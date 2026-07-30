# Independent validation of nma_fit.py against R netmeta.
# House rule: compare to metafor/meta/netmeta, tolerance 1e-6 for deterministic
# estimators. tau^2 estimators differ by method, so we compare the FIXED-effect
# fit exactly (no tau^2 involved) and report the RE fit for eyeball agreement.

suppressMessages(library(netmeta))
suppressMessages(library(jsonlite))

net <- fromJSON("preflight/network.json", simplifyDataFrame = FALSE)

rows <- do.call(rbind, lapply(net$trials, function(t) {
  do.call(rbind, lapply(t$arms, function(a) {
    data.frame(studlab = t$id, treat = a$node,
               event = a$recurrence,                 # P8a "observed"
               n = a$recurrence + a$recurrence_free,
               stringsAsFactors = FALSE)
  }))
}))

cat("arm-level data (event = recurrence by 180 d, evaluable denominator)\n")
print(rows)

p <- pairwise(treat = treat, event = event, n = n, studlab = studlab,
              data = rows, sm = "OR")

nm <- netmeta(p, reference.group = "no_hypnozoiticidal",
              common = TRUE, random = TRUE)

cat("\n=== netmeta FIXED effect: log-OR vs no_hypnozoiticidal ===\n")
print(round(nm$TE.common[, "no_hypnozoiticidal"], 10))
cat("\n=== netmeta FIXED effect SE ===\n")
print(round(nm$seTE.common[, "no_hypnozoiticidal"], 10))

cat("\n=== netmeta RANDOM effects: OR vs no_hypnozoiticidal ===\n")
print(round(exp(nm$TE.random[, "no_hypnozoiticidal"]), 6))

cat("\n=== heterogeneity ===\n")
cat("tau2 (netmeta, DL-type) =", round(nm$tau2, 6), "\n")
cat("Q =", round(nm$Q, 6), " df =", nm$df.Q, " p =", round(nm$pval.Q, 6), "\n")
cat("I2 =", round(nm$I2 * 100, 4), "%\n")

cat("\n=== decomposition of Q (within vs between design) ===\n")
print(decomp.design(nm)$Q.decomp)

cat("\n=== per-trial TQ_300 vs PQ_14d_low_3.5 (direct) ===\n")
d <- p[(p$treat1 == "TQ_300" & p$treat2 == "PQ_14d_low_3.5") |
       (p$treat2 == "TQ_300" & p$treat1 == "PQ_14d_low_3.5"), ]
for (i in seq_len(nrow(d))) {
  te <- if (d$treat1[i] == "TQ_300") d$TE[i] else -d$TE[i]
  cat(sprintf("  %-18s OR = %.4f\n", d$studlab[i], exp(te)))
}

cat("\n=== netsplit: direct vs indirect (inconsistency) ===\n")
ns <- netsplit(nm)
print(ns, digits = 4)
