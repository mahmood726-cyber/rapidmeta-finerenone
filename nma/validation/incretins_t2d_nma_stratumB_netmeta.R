## Incretin Class NMA in T2D — Stratum B (long-term CV-outcomes trials, ≥2 yr, HbA1c as secondary on heterogeneous background)
## Sensitivity analysis v1.3 (2026-04-21) — companion to Stratum A
## Scope: SUSTAIN-6 (Sema vs Pbo, 2 yr CV-outcome) and EXSCEL (Exenatide-ER vs Pbo, 3.2 yr CV-outcome)
## Network topology: 2-trial Pbo-star. Sema and Exenatide only connected via Placebo.
## Direct estimates = pairwise. Indirect Sema-vs-Exe through shared Pbo anchor.
suppressPackageStartupMessages({ library(netmeta); library(meta) })

trials <- data.frame(
  studlab = c("SUSTAIN-6","EXSCEL"),
  treat1  = c("Semaglutide","Exenatide"),
  treat2  = c("Placebo","Placebo"),
  TE      = c(-0.77,-0.53),
  seTE    = c(0.0408163265,0.0204081633),
  stringsAsFactors = FALSE
)
cat("=== Incretins T2D NMA Stratum B (long-term CV-outcomes, 2 trials) ===\n")
print(trials)
cat("\n")

## With only 2 trials REML cannot estimate tau^2 reliably.
## Report common-effect model as primary; random-effect with DerSimonian-Laird as sensitivity.
nma <- netmeta(TE=TE, seTE=seTE, treat1=treat1, treat2=treat2, studlab=studlab,
               data=trials, sm="MD", reference.group="Placebo",
               common=TRUE, random=TRUE, method.tau="DL", hakn=FALSE)

cat("\n=== Consistency model (Stratum B) ===\n")
print(summary(nma))
cat("\n=== Q heterogeneity / inconsistency (limited — no closed loops) ===\n")
cat("Q_total:", round(nma$Q, 3), "\n")
cat("Q_het  :", round(nma$Q.heterogeneity, 3), "\n")
cat("Q_inc  :", round(nma$Q.inconsistency, 3), "df", nma$df.Q.inconsistency, "\n")
cat("[note] Star network has no closed loops — design-by-treatment consistency test not defined.\n")

cat("\n=== P-scores (Stratum B) ===\n")
rk <- netrank(nma, small.values="desirable", common=FALSE, random=TRUE)
print(rk)

## MC ranking — small k but valid for reporting
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
cat("\n=== Rank-probability matrix (Stratum B, N=100k draws) ===\n")
print(round(rank_prob, 3))
cat("\n=== SUCRA (Stratum B) ===\n")
print(round(sort(sucra, decreasing=TRUE), 3))

results <- list(
  title = "Incretins T2D NMA Stratum B (long-term CV-outcomes, 2 trials)",
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
saveRDS(results, "incretins_t2d_nma_stratumB_netmeta_results.rds")
tryCatch({
  suppressPackageStartupMessages(library(jsonlite))
  writeLines(toJSON(lapply(results, function(x) if (is.matrix(x)) { m <- as.matrix(x); dimnames(m) <- NULL; m } else x), digits=6, auto_unbox=TRUE),
             "incretins_t2d_nma_stratumB_netmeta_results.json")
  cat("\n[wrote stratumB .rds + .json]\n")
}, error = function(e) cat("\n[JSON skipped:", conditionMessage(e), "]\n"))

cat("\n=== Key results (Stratum B) for peer-review bundle ===\n")
cat("TAU2:", round(nma$tau^2, 5), "\n")
cat("I2:", round(nma$I2 * 100, 2), "%\n")
for (tr in trts) {
  if (tr == "Placebo") next
  cat(sprintf("  %-24s MD %.3f (%.3f, %.3f)\n",
              tr,
              nma$TE.random[tr, "Placebo"],
              nma$lower.random[tr, "Placebo"],
              nma$upper.random[tr, "Placebo"]))
}
