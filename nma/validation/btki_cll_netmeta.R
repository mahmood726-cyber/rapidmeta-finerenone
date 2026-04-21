## BTKi-CLL NMA validation via netmeta (R 4.5.2, netmeta 3.2.0)
## Gold-standard comparator for the RapidMeta JS NMA engine.
## Run: Rscript btki_cll_netmeta.R > btki_cll_netmeta_results.txt

suppressPackageStartupMessages({
  library(netmeta)
  library(meta)
})

# Contrast-based data — log-HR + SE for each trial edge
# Derived from the 4 trials in the BTKi-CLL NMA protocol:
#   NCT02477696 ELEVATE-RR: Acalabrutinib vs Ibrutinib, HR 1.00 (0.81-1.24)
#   NCT02475681 ELEVATE-TN: Acalabrutinib vs Chemoimm, HR 0.21 (0.14-0.32)
#   NCT01722487 RESONATE-2: Ibrutinib vs Chemoimm,     HR 0.146 (0.098-0.218)
#   NCT03734016 ALPINE:     Zanubrutinib vs Ibrutinib, HR 0.65 (0.49-0.86)

logHR_SE <- function(hr, lci, uci) {
  list(TE = log(hr), seTE = (log(uci) - log(lci)) / 3.92)
}

trials <- data.frame(
  studlab  = c("ELEVATE-RR", "ELEVATE-TN", "RESONATE-2", "ALPINE"),
  treat1   = c("Acalabrutinib", "Acalabrutinib", "Ibrutinib",     "Zanubrutinib"),
  treat2   = c("Ibrutinib",     "Chemoimm",       "Chemoimm",      "Ibrutinib"),
  TE       = c(logHR_SE(1.00,0.81,1.24)$TE,
               logHR_SE(0.21,0.14,0.32)$TE,
               logHR_SE(0.146,0.098,0.218)$TE,
               logHR_SE(0.65,0.49,0.86)$TE),
  seTE     = c(logHR_SE(1.00,0.81,1.24)$seTE,
               logHR_SE(0.21,0.14,0.32)$seTE,
               logHR_SE(0.146,0.098,0.218)$seTE,
               logHR_SE(0.65,0.49,0.86)$seTE),
  stringsAsFactors = FALSE
)

cat("========================================\n")
cat("BTKi-CLL NMA — netmeta gold-standard fit\n")
cat("========================================\n\n")
cat("INPUT DATA:\n")
print(trials)
cat("\n")

# Fit NMA (contrast-based, random-effects; REML tau2; back-transformed to HR)
nma_fit <- netmeta(
  TE      = TE,
  seTE    = seTE,
  treat1  = treat1,
  treat2  = treat2,
  studlab = studlab,
  data    = trials,
  sm      = "HR",
  reference.group = "Chemoimm",
  common  = TRUE,
  random  = TRUE,
  details.chkmultiarm = TRUE,
  tol.multiarm = 0.001
)

cat("=== CONSISTENCY MODEL (random-effects) ===\n\n")
print(summary(nma_fit))
cat("\n")

cat("=== LEAGUE TABLE (random-effects, HR with 95% CI) ===\n\n")
league_re <- netleague(nma_fit, digits = 2, common = FALSE, random = TRUE)
print(league_re$random)
cat("\n")

cat("=== GLOBAL INCONSISTENCY (design-by-treatment interaction, Higgins 2012) ===\n\n")
decomp <- decomp.design(nma_fit)
print(decomp)
cat("\n")

cat("=== NODE-SPLITTING (Dias 2010, all comparisons with direct + indirect evidence) ===\n\n")
ns <- netsplit(nma_fit, common = FALSE, random = TRUE)
print(ns)
cat("\n")

cat("=== RANKING — P-scores (random-effects; lower-better for PFS HR) ===\n\n")
rk <- netrank(nma_fit, small.values = "desirable", common = FALSE, random = TRUE)
print(rk)
cat("\n")

# Full rank-probability matrix via resampling (1e5 draws)
set.seed(42)
n_draws <- 1e5
treatments <- nma_fit$trts
n_trt <- length(treatments)

# Multivariate normal draws from fitted posterior mean + vcov
mu <- c(0, nma_fit$TE.random[-which(treatments == "Chemoimm"), "Chemoimm"])
names(mu) <- c("Chemoimm", treatments[treatments != "Chemoimm"])
mu <- mu[treatments]  # reorder to match treatments vector

# vcov on contrasts (use seTE.random for contrast vs reference)
se_contrast <- nma_fit$seTE.random[, "Chemoimm"]
# crude draw: independent normals on each contrast (approximation; netmeta's Cov is correlated)
# for rigorous draw use MASS::mvrnorm with nma_fit's TE.random matrix + seTE.random and correlation
draws <- matrix(0, nrow = n_draws, ncol = n_trt)
colnames(draws) <- treatments
for (i in seq_along(treatments)) {
  if (treatments[i] == "Chemoimm") next
  draws[, i] <- rnorm(n_draws, mu[treatments[i]], se_contrast[treatments[i]])
}

# Rank each draw (lower HR = better = rank 1 for PFS)
ranks <- t(apply(draws, 1, rank, ties.method = "random"))
colnames(ranks) <- treatments

# Rank-probability matrix
rank_prob <- matrix(0, nrow = n_trt, ncol = n_trt,
                    dimnames = list(treatments, paste0("rank_", seq_len(n_trt))))
for (i in seq_len(n_trt)) {
  for (r in seq_len(n_trt)) {
    rank_prob[i, r] <- mean(ranks[, i] == r)
  }
}

cat("=== FULL RANK-PROBABILITY MATRIX (N = 100,000 MC draws) ===\n")
cat("(rows = treatments; columns = rank positions; cell = P[this treatment gets this rank])\n\n")
print(round(rank_prob, 3))
cat("\n")

# SUCRA from rank_prob
sucra <- sapply(seq_len(n_trt), function(i) {
  cum_probs <- cumsum(rank_prob[i, -n_trt])
  mean(cum_probs)
})
names(sucra) <- treatments
cat("=== SUCRA (from MC rank-probability) ===\n\n")
print(round(sort(sucra, decreasing = TRUE), 3))
cat("\n")

# Save numerical outputs for JS cross-check
results <- list(
  treatments = treatments,
  te_random_vs_chemoimm = setNames(nma_fit$TE.random[, "Chemoimm"], treatments),
  se_random_vs_chemoimm = setNames(nma_fit$seTE.random[, "Chemoimm"], treatments),
  hr_random_vs_chemoimm = setNames(exp(nma_fit$TE.random[, "Chemoimm"]), treatments),
  hr_ci_lower = setNames(exp(nma_fit$lower.random[, "Chemoimm"]), treatments),
  hr_ci_upper = setNames(exp(nma_fit$upper.random[, "Chemoimm"]), treatments),
  tau2 = nma_fit$tau^2,
  I2 = nma_fit$I2,
  Q_total = nma_fit$Q,
  Q_heterogeneity = nma_fit$Q.heterogeneity,
  Q_inconsistency = nma_fit$Q.inconsistency,
  p_inconsistency = nma_fit$pval.Q.inconsistency,
  sucra = sucra,
  rank_prob = rank_prob,
  pscore_random = rk$ranking.random
)
saveRDS(results, "btki_cll_netmeta_results.rds")
# Also emit JSON for the peer-review bundle
tryCatch({
  suppressPackageStartupMessages(library(jsonlite))
  writeLines(toJSON(lapply(results, function(x) if (is.matrix(x)) { m <- as.matrix(x); dimnames(m) <- NULL; m } else x), digits = 6, auto_unbox = TRUE),
             "btki_cll_netmeta_results.json")
  cat("\n[wrote btki_cll_netmeta_results.rds + .json]\n")
}, error = function(e) cat("\n[JSON skipped:", conditionMessage(e), "]\n"))
cat("\n=== JSON-READABLE KEY RESULTS ===\n")
cat("TAU2:", round(nma_fit$tau^2, 5), "\n")
cat("I2 :", round(nma_fit$I2, 4), "\n")
cat("Q  :", round(nma_fit$Q, 4),
    " (p =", round(nma_fit$pval.Q, 4), ")\n")
cat("Q heterogeneity:", round(nma_fit$Q.heterogeneity, 4),
    " (df =", nma_fit$df.Q.heterogeneity, ")\n")
cat("Q inconsistency:", round(nma_fit$Q.inconsistency, 4),
    " (df =", nma_fit$df.Q.inconsistency,
    ", p =", round(nma_fit$pval.Q.inconsistency, 4), ")\n\n")

cat("Treatment effects vs Chemoimm (random-effects, HR, 95% CI):\n")
for (tr in treatments) {
  if (tr == "Chemoimm") next
  hr   <- exp(nma_fit$TE.random[tr, "Chemoimm"])
  lci  <- exp(nma_fit$lower.random[tr, "Chemoimm"])
  uci  <- exp(nma_fit$upper.random[tr, "Chemoimm"])
  cat(sprintf("  %-16s HR %.3f (%.3f, %.3f)\n", tr, hr, lci, uci))
}
cat("\nSUCRA:\n")
for (nm in names(sort(sucra, decreasing = TRUE))) {
  cat(sprintf("  %-16s %.3f\n", nm, sucra[nm]))
}
