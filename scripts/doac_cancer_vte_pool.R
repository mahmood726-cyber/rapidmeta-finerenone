# R/metafor cross-validation of the DOAC-vs-LMWH cancer-associated-VTE pool.
# Companion to scripts/doac_cancer_vte_pool.py. Tolerance 1e-6 on the log scale.
suppressMessages(library(metafor))

z <- qnorm(0.975)

dat <- data.frame(
  study = c("HOKUSAI VTE-Cancer", "SELECT-D", "ADAM VTE", "CARAVAGGIO", "CASTA-DIVA"),
  hr    = c(0.71,  0.43,  0.099, 0.63,  0.75),
  lo    = c(0.476, 0.19,  0.013, 0.37,  0.21),
  hi    = c(1.059, 0.99,  0.780, 1.07,  2.66),
  stringsAsFactors = FALSE
)
dat$yi <- log(dat$hr)
dat$sei <- (log(dat$hi) - log(dat$lo)) / (2 * z)
dat$vi <- dat$sei^2

report <- function(d, tag) {
  fe <- rma(yi = d$yi, vi = d$vi, method = "FE")
  dl <- rma(yi = d$yi, vi = d$vi, method = "DL")
  hk <- rma(yi = d$yi, vi = d$vi, method = "DL", test = "knha")
  cat("\n==== ", tag, "  (k = ", nrow(d), ") ====\n", sep = "")
  cat(sprintf("FE    HR %.6f (%.6f - %.6f)\n", exp(fe$b), exp(fe$ci.lb), exp(fe$ci.ub)))
  cat(sprintf("DL    HR %.6f (%.6f - %.6f)  p = %.6f\n",
              exp(dl$b), exp(dl$ci.lb), exp(dl$ci.ub), dl$pval))
  cat(sprintf("HKSJ  HR %.6f (%.6f - %.6f)  p = %.6f\n",
              exp(hk$b), exp(hk$ci.lb), exp(hk$ci.ub), hk$pval))
  cat(sprintf("tau2 = %.8f   Q = %.6f (df %d, p = %.6f)   I2 = %.4f%%\n",
              dl$tau2, dl$QE, dl$k - 1, dl$QEp, dl$I2))
  # Prediction interval. The review's protocol specifies t_{k-1} (Cochrane Handbook v6.5),
  # which is what the app computes. metafor 5.0.1's predict() default is normal-based, so
  # both are printed and only the t_{k-1} line is the contract.
  pi <- predict(dl)
  tc <- qt(0.975, dl$k - 1)
  se_pi <- sqrt(dl$tau2 + dl$se^2)
  cat(sprintf("PI    %.6f - %.6f   [t_{k-1}, Cochrane v6.5 - CONTRACT]\n",
              exp(dl$b - tc * se_pi), exp(dl$b + tc * se_pi)))
  cat(sprintf("PI    %.6f - %.6f   [metafor %s predict() default, normal-based]\n",
              exp(pi$pi.lb), exp(pi$pi.ub), as.character(packageVersion("metafor"))))
  invisible(list(dl = dl, hk = hk))
}

report(dat[1:4, ], "Recurrent VTE - PRIMARY, cause-specific/Cox HR only")
report(dat, "Recurrent VTE - SENSITIVITY, + CASTA-DIVA subdistribution HR")
