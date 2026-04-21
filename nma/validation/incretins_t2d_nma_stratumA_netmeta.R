## Incretin Class NMA in T2D — Stratum A (short-term glycaemic efficacy, 26–52 wk, conventional or single-/basal-insulin-background trials)
## v1.4 (2026-04-21) — expanded with SURPASS-3, SURPASS-4, SURPASS-5, SURPASS-6 (Tirzepatide precision closures)
## Stratum A definition unchanged: ≤56 wk follow-up, HbA1c as primary endpoint, conventional diabetes-outcome trials.
## Background therapy: drug-naive or single-oral-layer (metformin ± one other) or basal-insulin (SURPASS-4/-5/-6). The basal-insulin SURPASS trials declared as moderate transitivity concern.
suppressPackageStartupMessages({ library(netmeta); library(meta) })

trials <- data.frame(
  studlab = c("SURPASS-1","SURPASS-2","SURPASS-3","SURPASS-4","SURPASS-5","SURPASS-6","SUSTAIN-1","SUSTAIN-2","SUSTAIN-3","SUSTAIN-7","LEAD-6","AWARD-6","LEAD-2","PIONEER-4","PIONEER-3"),
  treat1  = c("Tirzepatide","Tirzepatide","Tirzepatide","Tirzepatide","Tirzepatide","Tirzepatide","Semaglutide","Semaglutide","Semaglutide","Semaglutide","Liraglutide","Dulaglutide","Liraglutide","OralSemaglutide","OralSemaglutide"),
  treat2  = c("Placebo","Semaglutide","InsulinDegludec","InsulinGlargine","Placebo","InsulinLispro","Placebo","Sitagliptin","Exenatide","Dulaglutide","Exenatide","Liraglutide","Placebo","Liraglutide","Sitagliptin"),
  TE      = c(-2.11,-0.45,-1.04,-1.15,-2.50,-0.92,-1.55,-1.10,-0.62,-0.31,-0.33,-0.06,-1.10,-0.10,-0.50),
  seTE    = c(0.1198979592,0.0612244898,0.0663265306,0.0586734694,0.0943877551,0.0637755102,0.0943877551,0.0510204082,0.0918367347,0.0561224490,0.0739795918,0.0663265306,0.1020408163,0.0510204082,0.0510204082),
  stringsAsFactors = FALSE
)
cat("=== Incretins T2D NMA Stratum A v1.4 (15 trials, adds SURPASS-3/-4/-5/-6) ===\n")
print(trials)
cat("\n")

nma <- netmeta(TE=TE, seTE=seTE, treat1=treat1, treat2=treat2, studlab=studlab,
               data=trials, sm="MD", reference.group="Placebo",
               common=TRUE, random=TRUE, method.tau="REML", hakn=TRUE)

cat("\n=== Consistency model (Stratum A v1.4) ===\n")
print(summary(nma))
cat("\n=== Design-by-treatment inconsistency ===\n")
print(decomp.design(nma))
cat("\n=== Node-splitting ===\n")
print(netsplit(nma, common=FALSE, random=TRUE))
cat("\n=== P-scores ===\n")
rk <- netrank(nma, small.values="desirable", common=FALSE, random=TRUE)
print(rk)

set.seed(42)
suppressPackageStartupMessages(library(MASS))
n_draws <- 1e5
trts <- nma$trts
n_trt <- length(trts)
non_ref <- trts[trts != "Placebo"]
mu <- nma$TE.random[non_ref, "Placebo"]
if (!is.null(nma$Cov.random)) {
  cov_full <- nma$Cov.random
  idx_ref <- which(trts == "Placebo")
  Sigma <- matrix(0, nrow=length(non_ref), ncol=length(non_ref),
                  dimnames=list(non_ref, non_ref))
  for (a in seq_along(non_ref)) for (b in seq_along(non_ref)) {
    ia <- which(trts == non_ref[a]); ib <- which(trts == non_ref[b])
    Sigma[a, b] <- cov_full[ia, ib] - cov_full[ia, idx_ref] -
                   cov_full[idx_ref, ib] + cov_full[idx_ref, idx_ref]
  }
} else {
  Sigma <- diag(nma$seTE.random[non_ref, "Placebo"]^2)
}
draws_nonref <- mvrnorm(n_draws, mu, Sigma)
draws <- matrix(0, nrow=n_draws, ncol=n_trt); colnames(draws) <- trts
for (i in seq_along(non_ref)) draws[, non_ref[i]] <- draws_nonref[, i]
ranks <- t(apply(draws, 1, rank, ties.method="random"))
colnames(ranks) <- trts
rank_prob <- matrix(0, nrow=n_trt, ncol=n_trt,
                    dimnames=list(trts, paste0("rank_", seq_len(n_trt))))
for (i in seq_len(n_trt)) for (r in seq_len(n_trt)) rank_prob[i, r] <- mean(ranks[, i] == r)
sucra <- sapply(seq_len(n_trt), function(i) mean(cumsum(rank_prob[i, -n_trt])))
names(sucra) <- trts
cat("\n=== Rank-probability matrix (Stratum A v1.4, N=100k draws) ===\n")
print(round(rank_prob, 3))
cat("\n=== SUCRA (Stratum A v1.4) ===\n")
print(round(sort(sucra, decreasing=TRUE), 3))

results <- list(
  title = "Incretins T2D NMA Stratum A v1.4 (15 trials)",
  treatments = trts,
  te_random_vs_ref = setNames(nma$TE.random[, "Placebo"], trts),
  se_random_vs_ref = setNames(nma$seTE.random[, "Placebo"], trts),
  md_random_vs_placebo = setNames(nma$TE.random[, "Placebo"], trts),
  md_ci_lower = setNames(nma$lower.random[, "Placebo"], trts),
  md_ci_upper = setNames(nma$upper.random[, "Placebo"], trts),
  tau2 = nma$tau^2,
  I2 = nma$I2,
  Q_total = nma$Q,
  Q_heterogeneity = nma$Q.heterogeneity,
  Q_inconsistency = nma$Q.inconsistency,
  p_inconsistency = nma$pval.Q.inconsistency,
  sucra = sucra,
  pscore_random = rk$ranking.random,
  rank_prob = rank_prob
)
saveRDS(results, "incretins_t2d_nma_stratumA_netmeta_results.rds")
tryCatch({
  suppressPackageStartupMessages(library(jsonlite))
  writeLines(toJSON(lapply(results, function(x) if (is.matrix(x)) { m <- as.matrix(x); dimnames(m) <- NULL; m } else x), digits=6, auto_unbox=TRUE),
             "incretins_t2d_nma_stratumA_netmeta_results.json")
  cat("\n[wrote stratumA v1.4 .rds + .json]\n")
}, error = function(e) cat("\n[JSON skipped:", conditionMessage(e), "]\n"))

cat("\n=== Key results (Stratum A v1.4) for peer-review bundle ===\n")
cat("TAU2:", round(nma$tau^2, 5), "\n")
cat("I2:", round(nma$I2 * 100, 2), "%\n")
cat("Q inc:", round(nma$Q.inconsistency, 3), "df", nma$df.Q.inconsistency, "p", round(nma$pval.Q.inconsistency, 4), "\n")
for (tr in trts) {
  if (tr == "Placebo") next
  cat(sprintf("  %-24s MD %.3f (%.3f, %.3f)\n",
              tr,
              nma$TE.random[tr, "Placebo"],
              nma$lower.random[tr, "Placebo"],
              nma$upper.random[tr, "Placebo"]))
}
