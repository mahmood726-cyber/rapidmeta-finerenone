## SGLT2i-HF NMA — Stratum A (HF-primary trials only, k=4)
## Sensitivity analysis restricting to trials enrolling chronic HFrEF or HFpEF/HFmrEF
## Excludes SOLOIST-WHF (acute post-hospitalisation T2D+HF) and SCORED (T2D+CKD+CV-risk, HF as secondary)
suppressPackageStartupMessages({ library(netmeta); library(meta) })

logHR_SE <- function(hr, lci, uci) {
  list(TE = log(hr), seTE = (log(uci) - log(lci)) / 3.92)
}

trials <- data.frame(
  studlab = c("DAPA-HF","EMPEROR-Reduced","EMPEROR-Preserved","DELIVER"),
  treat1  = c("Dapagliflozin","Empagliflozin","Empagliflozin","Dapagliflozin"),
  treat2  = c("Placebo","Placebo","Placebo","Placebo"),
  TE      = c(log(0.74), log(0.75), log(0.79), log(0.82)),
  seTE    = c((log(0.85)-log(0.65))/3.92, (log(0.86)-log(0.65))/3.92,
              (log(0.90)-log(0.69))/3.92, (log(0.92)-log(0.73))/3.92),
  stringsAsFactors = FALSE
)
cat("=== SGLT2i-HF NMA Stratum A (4 HF-primary trials) ===\n")
print(trials)
cat("\n")

nma <- netmeta(TE=TE, seTE=seTE, treat1=treat1, treat2=treat2, studlab=studlab,
               data=trials, sm="HR", reference.group="Placebo",
               common=TRUE, random=TRUE, method.tau="REML", hakn=TRUE)

cat("\n=== Consistency model (Stratum A) ===\n")
print(summary(nma))
cat("\n=== Design-by-treatment inconsistency ===\n")
cat("Q_inc:", round(nma$Q.inconsistency, 3), "df", nma$df.Q.inconsistency, "\n")
cat("[note] Star network — no closed loops, consistency test not defined.\n")

cat("\n=== P-scores (Stratum A) ===\n")
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
cat("\n=== Rank-probability matrix (Stratum A) ===\n")
print(round(rank_prob, 3))
cat("\n=== SUCRA (Stratum A) ===\n")
print(round(sort(sucra, decreasing=TRUE), 3))

results <- list(
  title = "SGLT2i-HF NMA Stratum A (HF-primary, k=4)",
  treatments = trts,
  hr_random_vs_placebo = setNames(exp(nma$TE.random[, "Placebo"]), trts),
  hr_ci_lower = setNames(exp(nma$lower.random[, "Placebo"]), trts),
  hr_ci_upper = setNames(exp(nma$upper.random[, "Placebo"]), trts),
  tau2 = nma$tau^2, I2 = nma$I2,
  Q_total = nma$Q, Q_het = nma$Q.heterogeneity, Q_inc = nma$Q.inconsistency,
  p_inc = nma$pval.Q.inconsistency,
  sucra = sucra, pscore_random = rk$ranking.random,
  rank_prob = rank_prob
)
saveRDS(results, "sglt2i_hf_nma_stratumA_netmeta_results.rds")
tryCatch({
  suppressPackageStartupMessages(library(jsonlite))
  writeLines(toJSON(lapply(results, function(x) if (is.matrix(x)) { m <- as.matrix(x); dimnames(m) <- NULL; m } else x), digits=6, auto_unbox=TRUE),
             "sglt2i_hf_nma_stratumA_netmeta_results.json")
  cat("\n[wrote stratumA .rds + .json]\n")
}, error = function(e) cat("\n[JSON skipped:", conditionMessage(e), "]\n"))

cat("\n=== Key results (Stratum A) ===\n")
cat("TAU2:", round(nma$tau^2, 5), "\n")
cat("I2:", round(nma$I2 * 100, 2), "%\n")
for (tr in trts) {
  if (tr == "Placebo") next
  cat(sprintf("  %-20s HR %.3f (%.3f, %.3f)\n",
              tr,
              exp(nma$TE.random[tr, "Placebo"]),
              exp(nma$lower.random[tr, "Placebo"]),
              exp(nma$upper.random[tr, "Placebo"])))
}
