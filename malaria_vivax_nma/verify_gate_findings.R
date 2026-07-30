# Independent re-derivation of the cross-family gate's F1/F2/F3 claims.
# The gate's arithmetic is not taken on trust; every number is recomputed here.

suppressMessages(library(netmeta)); suppressMessages(library(meta))
suppressMessages(library(jsonlite))

net <- fromJSON("preflight/network.json", simplifyDataFrame = FALSE)
rows <- do.call(rbind, lapply(net$trials, function(t)
  do.call(rbind, lapply(t$arms, function(a)
    data.frame(studlab = t$id, treat = a$node, event = a$recurrence,
               n = a$recurrence + a$recurrence_free, stringsAsFactors = FALSE)))))

p  <- pairwise(treat = treat, event = event, n = n, studlab = studlab,
               data = rows, sm = "OR")
nm <- netmeta(p, reference.group = "no_hypnozoiticidal", common = TRUE, random = TRUE)

cat("########## F1  which trials share a DESIGN (node-set geometry)?\n")
for (t in net$trials) {
  nodes <- sort(sapply(t$arms, function(a) a$node))
  cat(sprintf("  %-18s design = {%s}\n", t$id, paste(nodes, collapse = ", ")))
}

cat("\n--- FULL network Q decomposition ---\n")
print(decomp.design(nm)$Q.decomp)
cat("\n--- per-design residual Q (which design drives BETWEEN?) ---\n")
print(decomp.design(nm)$Q.detach)

cat("\n########## F1b  ROBUST CORE: does the split reverse?\n")
core <- rows[rows$treat %in% c("no_hypnozoiticidal", "PQ_14d_low_3.5", "TQ_300"), ]
keep <- names(which(table(core$studlab) >= 2))
core <- core[core$studlab %in% keep, ]
pc <- pairwise(treat = treat, event = event, n = n, studlab = studlab,
               data = core, sm = "OR")
nmc <- netmeta(pc, reference.group = "no_hypnozoiticidal", common = TRUE, random = TRUE)
print(decomp.design(nmc)$Q.decomp)

cat("\n########## F2  focal-edge PAIRWISE heterogeneity (TQ_300 vs PQ_14d_low_3.5)\n")
d <- p[(p$treat1 == "TQ_300" & p$treat2 == "PQ_14d_low_3.5") |
       (p$treat2 == "TQ_300" & p$treat1 == "PQ_14d_low_3.5"), ]
te <- ifelse(d$treat1 == "TQ_300", d$TE, -d$TE)
m <- metagen(TE = te, seTE = d$seTE, studlab = d$studlab, sm = "OR",
             method.tau = "REML", common = FALSE, random = TRUE)
cat(sprintf("  k = %d\n  Q = %.4f  df = %d  p = %.6f\n  I2 = %.2f%%\n",
            m$k, m$Q, m$df.Q, m$pval.Q, m$I2 * 100))
cat(sprintf("  network-wide I2 (for contrast) = %.2f%%\n", nm$I2 * 100))

cat("\n########## F3  edge-specific Paule-Mandel vs common-tau2 NMA\n")
mpm <- metagen(TE = te, seTE = d$seTE, studlab = d$studlab, sm = "OR",
               method.tau = "PM", common = FALSE, random = TRUE)
cat(sprintf("  Paule-Mandel  tau2 = %.4f  OR = %.4f  (%.4f, %.4f)\n",
            mpm$tau2, exp(mpm$TE.random), exp(mpm$lower.random), exp(mpm$upper.random)))
cat(sprintf("  REML          tau2 = %.4f  OR = %.4f  (%.4f, %.4f)\n",
            m$tau2, exp(m$TE.random), exp(m$lower.random), exp(m$upper.random)))
i <- which(rownames(nm$TE.random) == "TQ_300")
j <- which(colnames(nm$TE.random) == "PQ_14d_low_3.5")
cat(sprintf("  NMA common-tau2      OR = %.4f  (%.4f, %.4f)\n",
            exp(nm$TE.random[i, j]), exp(nm$lower.random[i, j]), exp(nm$upper.random[i, j])))

cat("\n########## F4  randomised vs evaluable denominators\n")
tot_r <- sum(sapply(net$trials, function(t) t$n))
tot_e <- sum(rows$n)
cat(sprintf("  randomised = %d   evaluable = %d   conditioned away = %d (%.2f%%)\n",
            tot_r, tot_e, tot_r - tot_e, 100 * (tot_r - tot_e) / tot_r))
for (t in net$trials) {
  ev <- sum(sapply(t$arms, function(a) a$recurrence + a$recurrence_free))
  cat(sprintf("    %-18s randomised %4d  evaluable %4d\n", t$id, t$n, ev))
}
