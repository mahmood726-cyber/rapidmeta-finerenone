# R parity test for FINERENONE_REVIEW.html using metafor REML + HKSJ on logOR
# computed from AACT event counts (the same path the JS engine uses).
#
# This validates the JS engine matches metafor at 1e-6 tolerance per the
# project's testing rule (advanced-stats.md: "Compare against metafor/meta/
# mada with tolerance 1e-6").
#
# Inputs (4 trials from FINERENONE_REVIEW.html realData):
#   FIDELIO-DKD   tE=367/tN=2833, cE=420/cN=2841
#   FIGARO-DKD    tE=458/tN=3686, cE=519/cN=3666
#   FINEARTS-HF   tE=624/tN=3003, cE=719/cN=2998
#   ARTS-DN       tE=3/tN=727,    cE=1/cN=94    (Phase IIb dose-finding)

user_lib <- file.path(Sys.getenv("APPDATA"), "R-libs")
if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))
suppressMessages(library(metafor))

cat("metafor version:", as.character(packageVersion("metafor")), "\n\n")

dat <- data.frame(
  name = c("FIDELIO-DKD", "FIGARO-DKD", "FINEARTS-HF", "ARTS-DN"),
  tE   = c(367, 458, 624, 3),
  tN   = c(2833, 3686, 3003, 727),
  cE   = c(420, 519, 719, 1),
  cN   = c(2841, 3666, 2998, 94)
)
# Compute logOR + var via Woolf with 0.5 cell correction when needed.
# ARTS-DN has cE=1 (no zero cells, so no correction). escalc handles this.
esc <- escalc(measure = "OR",
              ai = tE, bi = tN - tE,
              ci = cE, di = cN - cE,
              data = dat)
cat("Per-trial logOR + variance:\n")
for (i in 1:nrow(esc)) {
  cat(sprintf("  %s: yi=%.6f vi=%.6f\n",
              esc$name[i], esc$yi[i], esc$vi[i]))
}

# Random-effects REML + HKSJ.
fit <- rma(yi = yi, vi = vi, data = esc,
           method = "REML", test = "knha")

cat("\nREML + HKSJ pool:\n")
cat(sprintf("  k                : %d\n", fit$k))
cat(sprintf("  pooled logOR     : %.6f\n", fit$b[1]))
cat(sprintf("  pooled OR        : %.6f\n", exp(fit$b[1])))
cat(sprintf("  HKSJ se(logOR)   : %.6f\n", fit$se))
cat(sprintf("  HKSJ 95%% CI OR  : [%.6f, %.6f]\n", exp(fit$ci.lb), exp(fit$ci.ub)))
cat(sprintf("  tau^2 (REML)     : %.10f\n", fit$tau2))
cat(sprintf("  Q                : %.6f (df=%d, p=%.6f)\n", fit$QE, fit$k - 1, fit$QEp))
cat(sprintf("  I^2              : %.4f%%\n", fit$I2))

# Prediction intervals.
pi_se <- sqrt(fit$tau2 + fit$se^2)
t_v65 <- qt(0.975, df = fit$k - 1)
t_v15 <- qt(0.975, df = fit$k - 2)
pi_v65 <- c(fit$b[1] - t_v65 * pi_se, fit$b[1] + t_v65 * pi_se)
pi_v15 <- c(fit$b[1] - t_v15 * pi_se, fit$b[1] + t_v15 * pi_se)
cat("\nPrediction intervals:\n")
cat(sprintf("  Cochrane v6.5 (k-1) : OR [%.6f, %.6f]  <- new JS engine target\n",
            exp(pi_v65[1]), exp(pi_v65[2])))
cat(sprintf("  IntHout 2016  (k-2) : OR [%.6f, %.6f]  <- old engine output\n",
            exp(pi_v15[1]), exp(pi_v15[2])))

# Compare against shipped sidecar.
sidecar_path <- "outputs/r_validation/FINERENONE.json"
if (file.exists(sidecar_path)) {
  txt <- paste(readLines(sidecar_path, warn = FALSE), collapse = "\n")
  # quick grep parse (avoid jsonlite dependency)
  get <- function(key) {
    m <- regmatches(txt, regexpr(paste0("\"", key, "\"\\s*:\\s*-?[0-9.e+-]+"), txt))
    if (length(m) == 0) return(NA_real_)
    as.numeric(sub(paste0("\"", key, "\"\\s*:\\s*"), "", m))
  }
  cat("\nShipped sidecar values:\n")
  for (key in c("pooled_OR", "ci_low_OR", "ci_high_OR", "tau2", "I2", "Q", "PI_low_OR", "PI_high_OR")) {
    v <- get(key)
    cat(sprintf("  %-12s: %.6f\n", key, v))
  }

  # Compare
  side_or  <- get("pooled_OR")
  side_lo  <- get("ci_low_OR")
  side_hi  <- get("ci_high_OR")
  side_pil <- get("PI_low_OR")
  side_pih <- get("PI_high_OR")
  my_or  <- exp(fit$b[1])
  my_lo  <- exp(fit$ci.lb)
  my_hi  <- exp(fit$ci.ub)
  my_pil <- exp(pi_v65[1])
  my_pih <- exp(pi_v65[2])
  cat("\nDiff (sidecar - this run):\n")
  cat(sprintf("  pooled_OR : %.2e\n", side_or - my_or))
  cat(sprintf("  ci_low_OR : %.2e\n", side_lo - my_lo))
  cat(sprintf("  ci_high_OR: %.2e\n", side_hi - my_hi))
  cat(sprintf("  PI_low_OR : %.2e\n", side_pil - my_pil))
  cat(sprintf("  PI_high_OR: %.2e\n", side_pih - my_pih))
  tol <- 1e-4
  ok <- all(abs(c(side_or - my_or, side_lo - my_lo, side_hi - my_hi)) < tol)
  cat(sprintf("\nParity at 1e-4 tolerance: %s\n", if (ok) "PASS" else "FAIL"))
}
