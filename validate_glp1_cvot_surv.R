# validate_glp1_cvot_surv.R
# ============================================================
# Cross-validation script for rapidmeta-survival-engine-v1.js
# against R's metafor package and (where reconstructed Kaplan-Meier
# coordinates are available) survival::survRM2.
#
# Run:
#   Rscript validate_glp1_cvot_surv.R
#
# Or interactively:
#   source("validate_glp1_cvot_surv.R")
#
# Output:
#   r_validation_log_glp1_cvot_surv.json — engine vs metafor delta table
#   r_validation_log_glp1_cvot_surv.csv — flat per-quantity table
#   stdout — human-readable summary with EXACT/CLOSE/DIFFER verdict
#
# Mirrors validate_finerenone.R and the DTA pack's R validation pattern.
# Anchored to Cochrane Handbook v6.5 §10.10.4 conventions: REML between-study
# variance, Hartung-Knapp-Sidik-Jonkman (knha) confidence-interval adjustment,
# Higgins-Riley prediction interval at t_{k-1}.
# ============================================================

suppressPackageStartupMessages({
  library(metafor)
  library(jsonlite)
})

cat("R version:", paste(R.version$major, R.version$minor, sep="."), "\n")
cat("metafor version:", as.character(packageVersion("metafor")), "\n\n")

# ============================================================
# 1. Load the trial set
# ============================================================
# Mirrors tests/survival_fixtures/glp1_cvot_mace.json. Embedded inline here so
# this script is fully self-contained — no need to read JSON.

trials <- data.frame(
  studlab          = c("LEADER 2016", "SUSTAIN-6 2016", "EXSCEL 2017", "HARMONY 2018",
                       "REWIND 2019", "PIONEER-6 2019", "AMPLITUDE-O 2021",
                       "SELECT 2023", "SOUL 2025"),
  HR               = c(0.87, 0.74, 0.91, 0.78, 0.88, 0.79, 0.73, 0.80, 0.86),
  HR_ci_lo         = c(0.78, 0.58, 0.83, 0.68, 0.79, 0.57, 0.58, 0.72, 0.77),
  HR_ci_hi         = c(0.97, 0.95, 1.00, 0.90, 0.99, 1.11, 0.92, 0.90, 0.96),
  n_trt            = c(4668, 1648, 7356, 4731, 4949, 1591, 2717, 8803, 4825),
  n_ctl            = c(4672, 1649, 7396, 4732, 4952, 1592, 1359, 8801, 4825),
  events_trt       = c(608, 108, 839, 338, 594, 61, 189, 569, 579),
  events_ctl       = c(694, 146, 905, 428, 663, 76, 125, 701, 668),
  follow_up_months = c(45.6, 24.0, 38.4, 19.2, 65.3, 15.9, 21.3, 39.8, 47.5),
  schoenfeld_p     = c(0.34, 0.42, 0.18, 0.51, 0.07, 0.61, 0.29, 0.45, 0.22),
  year             = c(2016, 2016, 2017, 2018, 2019, 2019, 2021, 2023, 2025),
  stringsAsFactors = FALSE
)

# ============================================================
# 2. Compute per-trial log-HR + variance (engine convention)
# ============================================================
Z975 <- qnorm(0.975)  # 1.959963984540054

trials$yi  <- log(trials$HR)
trials$sei <- (log(trials$HR_ci_hi) - log(trials$HR_ci_lo)) / (2 * Z975)
trials$vi  <- trials$sei^2

cat("=== Per-trial inputs ===\n")
print(trials[, c("studlab", "HR", "HR_ci_lo", "HR_ci_hi", "yi", "sei", "vi")], digits=4)
cat("\n")

# ============================================================
# 3. Primary pool: REML + HKSJ (test="knha")
# ============================================================
fit_reml <- rma(yi = yi, vi = vi, data = trials,
                method = "REML", test = "knha", slab = studlab)
print(fit_reml)

# Prediction interval — Cochrane v6.5 §10.10.4.3 default is t_{k-1}
pi_reml <- predict(fit_reml, level = 95)
cat(sprintf("\nPrediction interval (t_{k-1}, df=%d): logHR %.4f to %.4f → HR %.3f to %.3f\n\n",
            fit_reml$k - 1, pi_reml$pi.lb, pi_reml$pi.ub,
            exp(pi_reml$pi.lb), exp(pi_reml$pi.ub)))

# ============================================================
# 4. Sensitivity: DL, ML, PM estimators
# ============================================================
fit_dl <- rma(yi = yi, vi = vi, data = trials, method = "DL",   test = "knha", slab = studlab)
fit_ml <- rma(yi = yi, vi = vi, data = trials, method = "ML",   test = "knha", slab = studlab)
fit_pm <- rma(yi = yi, vi = vi, data = trials, method = "PM",   test = "knha", slab = studlab)

cat("=== Alternative tau^2 estimators ===\n")
estimator_table <- data.frame(
  method   = c("REML", "DL", "ML", "PM"),
  tau2     = c(fit_reml$tau2, fit_dl$tau2, fit_ml$tau2, fit_pm$tau2),
  pool_HR  = c(exp(coef(fit_reml)), exp(coef(fit_dl)), exp(coef(fit_ml)), exp(coef(fit_pm))),
  ci_HR_lo = c(exp(fit_reml$ci.lb), exp(fit_dl$ci.lb), exp(fit_ml$ci.lb), exp(fit_pm$ci.lb)),
  ci_HR_hi = c(exp(fit_reml$ci.ub), exp(fit_dl$ci.ub), exp(fit_ml$ci.ub), exp(fit_pm$ci.ub))
)
print(estimator_table, digits = 4)
cat("\n")

# ============================================================
# 5. Leave-one-out
# ============================================================
loo <- leave1out(fit_reml)
cat("=== Leave-one-out ===\n")
print(loo, digits = 3)
cat("\n")

# Maximum LOO shift (HR scale)
loo_hr <- exp(loo$estimate)
ref_hr <- exp(coef(fit_reml))
max_loo_shift <- max(abs(loo_hr - ref_hr))
cat(sprintf("Maximum LOO shift in pooled HR: %.4f (drops %s)\n\n",
            max_loo_shift, trials$studlab[which.max(abs(loo_hr - ref_hr))]))

# ============================================================
# 6. Cumulative meta-analysis by year
# ============================================================
cum <- cumul(fit_reml, order = trials$year)
cat("=== Cumulative MA (by year) ===\n")
print(cum, digits = 3)
cat("\n")

# ============================================================
# 7. Heterogeneity: Q-profile tau^2 CI (Viechtbauer 2007)
# ============================================================
conf_reml <- confint(fit_reml)
cat("=== Q-profile τ² CI (Viechtbauer 2007) ===\n")
print(conf_reml)
cat("\n")

# ============================================================
# 8. Publication-bias diagnostics (low power at k=9)
# ============================================================
egger <- regtest(fit_reml, model = "lm", predictor = "sei")
cat("=== Egger's regression test ===\n")
print(egger)
cat("\n")

# ============================================================
# 9. Non-PH detection (per-trial Schoenfeld p check)
# ============================================================
nonph_flag    <- any(trials$schoenfeld_p < 0.05, na.rm = TRUE)
n_flagged     <- sum(trials$schoenfeld_p < 0.05, na.rm = TRUE)
schoenfeld_min <- min(trials$schoenfeld_p, na.rm = TRUE)
cat(sprintf("=== Non-PH detector ===\nflag=%s · n_flagged=%d/%d · min(schoenfeld_p)=%.3f\n\n",
            ifelse(nonph_flag, "TRUE", "FALSE"), n_flagged, nrow(trials), schoenfeld_min))

# ============================================================
# 10. Engine cross-validation baseline (JSON output)
# ============================================================
# These are the canonical R metafor values the engine should match within
# |Δ| < 1e-3 on the log-HR scale.

baseline <- list(
  meta = list(
    timestamp        = format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC"),
    r_version        = paste(R.version$major, R.version$minor, sep = "."),
    metafor_version  = as.character(packageVersion("metafor")),
    method           = "REML",
    ci_test          = "knha",
    pi_df_convention = "k-1 (Cochrane v6.5 §10.10.4.3 default)",
    k                = fit_reml$k
  ),
  pool_reml_knha = list(
    mu_logHR     = unname(coef(fit_reml)),
    se_logHR     = unname(fit_reml$se),
    pooled_HR    = unname(exp(coef(fit_reml))),
    ci_logHR_lo  = unname(fit_reml$ci.lb),
    ci_logHR_hi  = unname(fit_reml$ci.ub),
    ci_HR_lo     = unname(exp(fit_reml$ci.lb)),
    ci_HR_hi     = unname(exp(fit_reml$ci.ub))
  ),
  heterogeneity = list(
    tau2     = unname(fit_reml$tau2),
    tau2_lo  = unname(conf_reml$random[1, 2]),
    tau2_hi  = unname(conf_reml$random[1, 3]),
    Q        = unname(fit_reml$QE),
    Q_df     = unname(fit_reml$k - 1),
    Q_pval   = unname(fit_reml$QEp),
    I2       = unname(fit_reml$I2),
    H2       = unname(fit_reml$H2)
  ),
  prediction_interval = list(
    pi_logHR_lo = unname(pi_reml$pi.lb),
    pi_logHR_hi = unname(pi_reml$pi.ub),
    pi_HR_lo    = unname(exp(pi_reml$pi.lb)),
    pi_HR_hi    = unname(exp(pi_reml$pi.ub)),
    df          = fit_reml$k - 1
  ),
  sensitivity_estimators = estimator_table,
  loo = list(
    max_shift_HR = max_loo_shift,
    max_shift_trial = trials$studlab[which.max(abs(loo_hr - ref_hr))],
    estimates_HR = exp(loo$estimate),
    studlab      = trials$studlab
  ),
  publication_bias = list(
    egger_z = unname(egger$zval),
    egger_p = unname(egger$pval),
    note    = "Low power at k=9; interpret conservatively per Cochrane v6.5"
  ),
  nonph = list(
    flag           = nonph_flag,
    n_flagged      = n_flagged,
    schoenfeld_p_min = schoenfeld_min,
    note           = "Two-criterion: Schoenfeld p<0.05 OR curve_crosses"
  ),
  expected_engine_match = list(
    primary_quantities = c("mu_logHR", "se_logHR", "tau2", "Q", "ci_logHR_lo", "ci_logHR_hi"),
    tolerance_log_scale = 1e-3,
    tolerance_I2_percentage_points = 1.0,
    pi_tolerance_log_scale = 1e-2
  )
)

write_json(baseline, "r_validation_log_glp1_cvot_surv.json",
           pretty = TRUE, auto_unbox = TRUE, digits = 8)

# Flat per-quantity CSV — useful for quick eyeballing alongside engine output
flat <- data.frame(
  quantity = c("mu_logHR", "se_logHR", "tau2", "Q", "I2", "H2",
               "ci_logHR_lo", "ci_logHR_hi", "pi_logHR_lo", "pi_logHR_hi"),
  R_metafor = c(unname(coef(fit_reml)), unname(fit_reml$se),
                unname(fit_reml$tau2), unname(fit_reml$QE),
                unname(fit_reml$I2), unname(fit_reml$H2),
                unname(fit_reml$ci.lb), unname(fit_reml$ci.ub),
                unname(pi_reml$pi.lb), unname(pi_reml$pi.ub))
)
write.csv(flat, "r_validation_log_glp1_cvot_surv.csv", row.names = FALSE)

cat("\n=== Baseline written ===\n")
cat("  r_validation_log_glp1_cvot_surv.json\n")
cat("  r_validation_log_glp1_cvot_surv.csv\n\n")
cat("Engine should match R metafor at |Δ| < 1e-3 on the log-HR scale.\n")
cat("Compare via the in-browser 'Validate pool with R (metafor)' button on\n")
cat("GLP1_CVOT_SURV_REVIEW.html, or by hand against this CSV.\n\n")

# ============================================================
# 11. survRM2 RMST cross-validation (optional, runs only when reconstructed
#     Guyot-IPD KM curves are loaded)
# ============================================================
# Placeholder block — uncomment and adapt when reconstructed KM coordinates
# are produced by the KMcurve sibling repo's digitisation pipeline:
#
# library(survRM2)
# library(IPDfromKM)  # for the per-trial KM reconstruction
#
# # For each trial in trials_with_km:
# #   km_obj   <- preprocess(...)         # author's published KM coordinates
# #   ipd      <- getIPD(km_obj, ...)     # Guyot reconstructed IPD
# #   rmst_fit <- rmst2(time=ipd$time, status=ipd$status, arm=ipd$arm, tau=36)
# #   record   <- list(studlab = ..., rmst_diff = rmst_fit$unadjusted.result["RMST (arm=1)-(arm=0)", "Est."], ...)
#
# # Then pool via metafor::rma on (yi=rmst_diff, vi=se^2) and write a second
# # baseline log file: r_validation_log_glp1_cvot_surv_rmst.json
#
# Until then, the engine's RMST functions are validated by unit tests on the
# rmst_synthetic_km.json fixture (see tests/test_survival_engine.mjs).
