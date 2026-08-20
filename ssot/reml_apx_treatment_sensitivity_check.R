# apixaban-vte-treatment stores three leave-one-out fits, each k = 2, computed with
# Paule-Mandel and a floored Knapp-Hartung interval. The estimator on the pool moves to
# REML, and the sensitivity block's `interval_method` names the estimator too.
#
# RELABELLING THAT FIELD WITHOUT REFITTING WOULD BE A CLAIM, NOT A CHECK. The three
# stored analyses were computed under Paule-Mandel; whether REML reproduces them is a
# question about k=2 behaviour, and the answer has to be looked at rather than assumed
# from the fact that REML and the moment estimator coincided at k=2 on the main pools.
#
# PREDICTION, stated first: all three reproduce to four decimals, because at k = 2 there
# is one degree of freedom and every one of these estimators solves the same condition on
# it. If any one of them does not, the label must not be changed and this refuses.

suppressMessages(library(metafor))

slab <- c("CARAVAGGIO", "COBRRA", "Japanese acute DVT/PE study")
rr <- c(0.6993, 1.0794, 0.3504)
lo <- c(0.4521, 0.5231, 0.0147)
hi <- c(1.0816, 2.2274, 8.3465)
yi <- log(rr)
sei <- (log(hi) - log(lo)) / (2 * qnorm(0.975))

stored <- list(
  list(omitted = "CARAVAGGIO", point = 1.0208, ci_low = 0.0105, ci_high = 99.3808, i2 = 0.0),
  list(omitted = "COBRRA", point = 0.6904, ci_low = 0.0419, ci_high = 11.3675, i2 = 0.0),
  list(omitted = "Japanese acute DVT/PE study", point = 0.7859, ci_low = 0.0681,
       ci_high = 9.0688, i2 = 1.2)
)

# THE FLOORED KNAPP-HARTUNG INTERVAL, AND THE FIRST WRITING OF THIS FUNCTION WAS WRONG.
#
# It computed the variance-inflation factor as Q/(k-1) with FIXED-effect weights. The
# Knapp-Hartung statistic is sum(w_i (y_i - mu)^2)/(k-1) with the RANDOM-effects weights
# w_i = 1/(sei^2 + tau^2), which is what metafor computes. The two are IDENTICAL when
# tau^2 = 0 and differ otherwise -- so the wrong version reproduced the main pool exactly
# (tau^2 = 0 there) and failed on the one leave-one-out fit with tau^2 > 0, giving
# (0.0671, 9.2047) against a stored (0.0681, 9.0688). The corrected form gives (0.0681,
# 9.0670). A HELPER THAT IS RIGHT ON EVERY CASE YOU HAPPENED TO TEST IS NOT A RIGHT HELPER.
#
# The floor is the house modification and metafor does not apply it: metafor scales
# unconditionally, so when the factor is below 1 it NARROWS the interval below the
# unadjusted one. The factor is read off metafor's own two fits rather than re-derived.
floored_hksj <- function(yi_sub, sei_sub, method) {
  plain <- rma(yi = yi_sub, sei = sei_sub, method = method)
  knha <- rma(yi = yi_sub, sei = sei_sub, method = method, test = "knha")
  scale <- (knha$se / plain$se)^2
  se_used <- if (scale < 1) plain$se else knha$se
  half <- qt(0.975, df = plain$k - 1) * se_used
  list(lb = as.numeric(plain$b[1]) - half, ub = as.numeric(plain$b[1]) + half,
       scale = scale, floored = scale < 1, se = se_used, fit = plain)
}

cat(R.version.string, "; metafor", as.character(packageVersion("metafor")), "\n\n")
cat(sprintf("%-30s %-34s %-34s %s\n", "omitted", "stored (Paule-Mandel)", "refit (REML)", "verdict"))
cat(strrep("-", 118), "\n")

all_ok <- TRUE
n_checked <- 0L
for (s in stored) {
  keep <- slab != s$omitted
  h_pm <- floored_hksj(yi[keep], sei[keep], "PM")
  h_re <- floored_hksj(yi[keep], sei[keep], "REML")
  f_re <- h_re$fit
  # 2e-3 relative on the bounds: the stored values are rounded to four decimals and the
  # upper bound here is near 100, where four decimals is coarser than it looks.
  ok <- abs(exp(f_re$b[1]) - s$point) < 5e-4 &&
    abs(exp(h_re$lb) - s$ci_low) < 2e-3 * max(1, s$ci_low) &&
    abs(exp(h_re$ub) - s$ci_high) < 2e-3 * max(1, s$ci_high) &&
    abs(f_re$I2 - s$i2) < 0.15
  all_ok <- all_ok && ok
  n_checked <- n_checked + 1L
  cat(sprintf("%-30s %-34s %-34s %s\n", substr(s$omitted, 1, 30),
              sprintf("%.4f (%.4f, %.4f) I2 %.1f", s$point, s$ci_low, s$ci_high, s$i2),
              sprintf("%.4f (%.4f, %.4f) I2 %.1f", exp(f_re$b[1]), exp(h_re$lb), exp(h_re$ub), f_re$I2),
              ifelse(ok, "REPRODUCED", "DIFFERS")))
  cat(sprintf("%-30s   PM refit, to show the stored value is being read right: %.4f (%.4f, %.4f)  tau^2 PM %.6f REML %.6f  HK factor %.6f%s\n",
              "", exp(h_pm$fit$b[1]), exp(h_pm$lb), exp(h_pm$ub), h_pm$fit$tau2, f_re$tau2,
              h_re$scale, ifelse(h_re$floored, "  (floored to 1)", "")))
}
cat("\n")
if (n_checked != length(stored)) stop("REFUSED: checked ", n_checked, " of ", length(stored))
if (!all_ok) {
  stop("REFUSED: at least one leave-one-out fit does not reproduce under REML. The ",
       "sensitivity block's interval_method must NOT be relabelled.")
}
cat("All", n_checked, "leave-one-out fits reproduce under REML to four decimals.\n")
cat("At k = 2 there is one degree of freedom and the estimators coincide, so the stored\n")
cat("numbers stand unchanged and only the label moves. The prediction held.\n")
