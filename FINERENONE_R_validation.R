#!/usr/bin/env Rscript

# FINERENONE_R_validation.R
# Self-contained R validation script for FINERENONE_REVIEW.html
# Harmonized endpoint scope refreshed 2026-03-06.
#
# Purpose:
# 1. Embed the exact trial-level counts used in the HTML app.
# 2. Reproduce the app's core random-effects calculations in base R.
# 3. Validate those R outputs against the stored reference baselines.
#
# Notes:
# - No external packages are required.
# - The implementation mirrors the HTML app's AnalysisEngine.computeCore().
# - Default matched CV pooling excludes FINEARTS-HF because its endpoint
#   definition does not match the CKD composite used in FIDELIO-DKD/FIGARO-DKD.
# - FIGARO-DKD all-cause hospitalization counts are evidence-only context and are
#   intentionally not pooled in the HF hospitalization analysis.

options(stringsAsFactors = FALSE, scipen = 999)

trial_data <- data.frame(
  trial = c(
    "FIDELIO-DKD", "FIDELIO-DKD", "FIDELIO-DKD", "FIDELIO-DKD",
    "FIGARO-DKD",  "FIGARO-DKD",  "FIGARO-DKD",  "FIGARO-DKD",
    "FINEARTS-HF", "FINEARTS-HF", "FINEARTS-HF"
  ),
  short_trial = c(
    "FIDELIO", "FIDELIO", "FIDELIO", "FIDELIO",
    "FIGARO",  "FIGARO",  "FIGARO",  "FIGARO",
    "FINEARTS", "FINEARTS", "FINEARTS"
  ),
  group = c(
    "CKD", "CKD", "CKD", "CKD",
    "CKD", "CKD", "CKD", "CKD",
    "Heart Failure", "Heart Failure", "Heart Failure"
  ),
  phase = c(
    "III", "III", "III", "III",
    "III", "III", "III", "III",
    "III", "III", "III"
  ),
  year = c(
    2020, 2020, 2020, 2020,
    2021, 2021, 2021, 2021,
    2024, 2024, 2024
  ),
  outcome = c(
    "MACE", "Renal40", "ACM", "ACH",
    "MACE", "Renal40", "ACM", "ACH",
    "HF_CV_First", "KidneyComp", "ACM"
  ),
  outcome_title = c(
    "CV Death, MI, Stroke, or HF Hospitalization",
    "Kidney Failure, >=40% eGFR Decline, or Renal Death",
    "All-Cause Mortality",
    "Hospitalization for Heart Failure",
    "CV Death, MI, Stroke, or HF Hospitalization",
    "Kidney Failure, >=40% eGFR Decline, or Renal Death",
    "All-Cause Mortality",
    "Hospitalization for Heart Failure",
    "First Worsening HF Event or CV Death",
    "Kidney Composite Outcome",
    "All-Cause Mortality"
  ),
  tE = c(367, 504, 219, 139, 458, 350, 333, 117, 624, 75, 491),
  tN = c(2833, 2833, 2833, 2833, 3686, 3686, 3686, 3686, 3003, 3003, 3003),
  cE = c(420, 600, 244, 162, 519, 395, 370, 163, 719, 55, 522),
  cN = c(2841, 2841, 2841, 2841, 3666, 3666, 3666, 3666, 2998, 2998, 2998),
  source = c(
    "Bakris GL et al. NEJM 2020;383:2219-2239, Table 2",
    "Bakris GL et al. NEJM 2020;383:2219-2239, primary kidney composite",
    "Harmonized app dataset from FIDELIO-DKD trial reporting / pooled mortality review",
    "FIDELIO-DKD heart-failure hospitalization count used in harmonized app dataset",
    "Pitt B et al. NEJM 2021;385:2252-2263, Table 2",
    "Pitt B et al. NEJM 2021;385:2252-2263, kidney composite reporting",
    "Regulatory / published summary table aligned to harmonized app dataset",
    "FIGARO-DKD heart-failure hospitalization count used in harmonized app dataset",
    "Solomon SD et al. NEJM 2024, Table 2",
    "Solomon SD et al. NEJM 2024, Table 2",
    "Solomon SD et al. NEJM 2024, Table 2"
  )
)

reference_results <- list(
  MACE_OR = list(
    outcome = "MACE",
    measure = "OR",
    label = "Matched CKD CV composite (default scope / MACE)",
    expected = list(
      or = 0.859229,
      lci = 0.777026,
      uci = 0.950129,
      tau2 = 0.000000,
      I2 = 0.0000,
      hksjLCI = 0.447693,
      hksjUCI = 1.649066,
      k = 2,
      trials = "FIDELIO,FIGARO"
    )
  ),
  MACE_RR = list(
    outcome = "MACE",
    measure = "RR",
    label = "Matched CKD CV composite (risk ratio sensitivity)",
    expected = list(
      or = 0.877051,
      lci = 0.803981,
      uci = 0.956761,
      tau2 = 0.000000,
      I2 = 0.0000,
      hksjLCI = 0.499009,
      hksjUCI = 1.541492,
      k = 2,
      trials = "FIDELIO,FIGARO"
    )
  ),
  Renal40_OR = list(
    outcome = "Renal40",
    measure = "OR",
    label = "Kidney composite >=40% eGFR decline / kidney failure / renal death",
    expected = list(
      or = 0.833777,
      lci = 0.754784,
      uci = 0.921037,
      tau2 = 0.000000,
      I2 = 0.0000,
      k = 2,
      trials = "FIDELIO,FIGARO"
    )
  ),
  ACM_OR = list(
    outcome = "ACM",
    measure = "OR",
    label = "All-cause mortality",
    expected = list(
      or = 0.904840,
      lci = 0.827012,
      uci = 0.989992,
      tau2 = 0.000000,
      I2 = 0.0000,
      hksjLCI = 0.742719,
      hksjUCI = 1.102349,
      piLCI = 0.505070,
      piUCI = 1.621036,
      eggerP = 0.490604,
      k = 3,
      trials = "FIDELIO,FIGARO,FINEARTS"
    )
  ),
  ACH_OR = list(
    outcome = "ACH",
    measure = "OR",
    label = "Hospitalization for heart failure",
    expected = list(
      or = 0.777627,
      lci = 0.644603,
      uci = 0.938102,
      tau2 = 0.003663,
      I2 = 19.9718,
      hksjLCI = 0.230438,
      hksjUCI = 2.624149,
      k = 2,
      trials = "FIDELIO,FIGARO"
    )
  )
)

extra_analyses <- list(
  HF_CV_First_OR = list(
    outcome = "HF_CV_First",
    measure = "OR",
    label = "FINEARTS-HF first worsening HF event or CV death"
  ),
  KidneyComp_OR = list(
    outcome = "KidneyComp",
    measure = "OR",
    label = "FINEARTS-HF trial-specific kidney composite"
  )
)

select_outcome_data <- function(outcome_key) {
  dat <- trial_data[trial_data$outcome == outcome_key, , drop = FALSE]
  if (nrow(dat) == 0) {
    stop(sprintf("No embedded rows found for outcome '%s'.", outcome_key))
  }
  dat
}

compute_meta <- function(dat, measure = "OR", conf_level = 0.95) {
  if (!measure %in% c("OR", "RR")) {
    stop("measure must be 'OR' or 'RR'")
  }

  dat <- dat[!(dat$tE == 0 & dat$cE == 0), , drop = FALSE]
  dat <- dat[!(dat$tE == dat$tN & dat$cE == dat$cN), , drop = FALSE]
  if (nrow(dat) == 0) {
    stop("No analyzable studies after filtering all-zero or all-event rows.")
  }

  has_zero <- dat$tE == 0 | dat$cE == 0 | dat$tE == dat$tN | dat$cE == dat$cN
  adj <- ifelse(has_zero, 0.5, 0)

  a <- dat$tE + adj
  b <- dat$tN - dat$tE + adj
  c <- dat$cE + adj
  d <- dat$cN - dat$cE + adj

  if (measure == "RR") {
    yi <- log((a / (a + b)) / (c / (c + d)))
    vi <- b / (a * (a + b)) + d / (c * (c + d))
  } else {
    yi <- log((a / b) / (c / d))
    vi <- 1 / a + 1 / b + 1 / c + 1 / d
  }

  se <- sqrt(vi)
  w_fixed <- 1 / vi
  sW <- sum(w_fixed)
  sWY <- sum(w_fixed * yi)
  sW_y2 <- sum(w_fixed * yi * yi)
  sW2 <- sum(w_fixed^2)

  Q <- max(0, sW_y2 - (sWY^2 / sW))
  k <- length(yi)
  df <- k - 1
  I2 <- if (Q > df) ((Q - df) / Q) * 100 else 0
  tau2 <- if (Q > df) (Q - df) / (sW - (sW2 / sW)) else 0

  w_random <- 1 / (vi + tau2)
  sWR <- sum(w_random)
  pooled_log <- sum(w_random * yi) / sWR
  pooled_se <- sqrt(1 / sWR)

  z_crit <- qnorm(1 - (1 - conf_level) / 2)
  pooled_effect <- exp(pooled_log)
  lci <- exp(pooled_log - z_crit * pooled_se)
  uci <- exp(pooled_log + z_crit * pooled_se)

  hksjLCI <- NA_real_
  hksjUCI <- NA_real_
  if (k >= 2) {
    q_star <- sum(w_random * (yi - pooled_log)^2) / df
    hksj_adj <- max(1, q_star)
    hksj_se <- sqrt(hksj_adj / sWR)
    t_crit_hksj <- qt(1 - (1 - conf_level) / 2, df = df)
    hksjLCI <- exp(pooled_log - t_crit_hksj * hksj_se)
    hksjUCI <- exp(pooled_log + t_crit_hksj * hksj_se)
  }

  piLCI <- NA_real_
  piUCI <- NA_real_
  if (k >= 3) {
    pi_se <- sqrt(tau2 + pooled_se^2)
    t_crit_pi <- qt(1 - (1 - conf_level) / 2, df = k - 2)
    piLCI <- exp(pooled_log - t_crit_pi * pi_se)
    piUCI <- exp(pooled_log + t_crit_pi * pi_se)
  }

  qPvalue <- if (df >= 1) pchisq(Q, df = df, lower.tail = FALSE) else NA_real_

  egger_intercept <- NA_real_
  eggerP <- NA_real_
  if (k >= 3) {
    eX <- 1 / se
    eY <- yi / se
    x_mean <- mean(eX)
    y_mean <- mean(eY)
    sxy <- sum((eX - x_mean) * (eY - y_mean))
    sxx <- sum((eX - x_mean)^2)
    slope <- sxy / sxx
    intercept <- y_mean - slope * x_mean
    residuals <- eY - intercept - slope * eX
    mse <- sum(residuals^2) / (k - 2)
    se_intercept <- sqrt(mse * (1 / k + x_mean^2 / sxx))
    t_stat <- intercept / se_intercept
    egger_intercept <- intercept
    eggerP <- 2 * pt(abs(t_stat), df = k - 2, lower.tail = FALSE)
  }

  list(
    k = k,
    trials = paste(dat$short_trial, collapse = ","),
    outcome = unique(dat$outcome),
    measure = measure,
    pooled = pooled_effect,
    lci = lci,
    uci = uci,
    tau2 = tau2,
    I2 = I2,
    hksjLCI = hksjLCI,
    hksjUCI = hksjUCI,
    piLCI = piLCI,
    piUCI = piUCI,
    qPvalue = qPvalue,
    eggerIntercept = egger_intercept,
    eggerP = eggerP,
    totalN = sum(dat$tN + dat$cN),
    study_level = data.frame(
      trial = dat$trial,
      outcome = dat$outcome,
      tE = dat$tE,
      tN = dat$tN,
      cE = dat$cE,
      cN = dat$cN,
      yi = yi,
      vi = vi,
      se = se,
      w_fixed = w_fixed,
      w_random = w_random,
      stringsAsFactors = FALSE
    )
  )
}

metric_row <- function(metric, observed, expected, digits = 6) {
  comparable <- !(is.na(observed) || is.null(expected) || is.na(expected))
  abs_diff <- if (comparable) abs(observed - expected) else NA_real_
  pass <- if (comparable) identical(round(observed, digits), round(expected, digits)) else NA
  data.frame(
    metric = metric,
    observed = if (is.na(observed)) NA_real_ else observed,
    expected = if (is.null(expected)) NA_real_ else expected,
    digits = digits,
    abs_diff = abs_diff,
    pass = pass,
    stringsAsFactors = FALSE
  )
}

validate_analysis <- function(spec_name, spec) {
  dat <- select_outcome_data(spec$outcome)
  res <- compute_meta(dat, measure = spec$measure)
  exp <- spec$expected

  rows <- list(
    metric_row("pooled_effect", res$pooled, exp$or, digits = 6),
    metric_row("lci", res$lci, exp$lci, digits = 6),
    metric_row("uci", res$uci, exp$uci, digits = 6),
    metric_row("tau2", res$tau2, exp$tau2, digits = 6),
    metric_row("I2", res$I2, exp$I2, digits = 4),
    metric_row("hksjLCI", res$hksjLCI, exp$hksjLCI, digits = 6),
    metric_row("hksjUCI", res$hksjUCI, exp$hksjUCI, digits = 6),
    metric_row("piLCI", res$piLCI, exp$piLCI, digits = 6),
    metric_row("piUCI", res$piUCI, exp$piUCI, digits = 6),
    metric_row("eggerP", res$eggerP, exp$eggerP, digits = 6),
    metric_row("k", res$k, exp$k, digits = 0)
  )
  check_table <- do.call(rbind, rows)

  trials_pass <- identical(res$trials, exp$trials)
  all_metric_pass <- all(check_table$pass[!is.na(check_table$pass)])
  overall_pass <- all_metric_pass && trials_pass

  list(
    name = spec_name,
    label = spec$label,
    result = res,
    checks = check_table,
    trials_expected = exp$trials,
    trials_pass = trials_pass,
    overall_pass = overall_pass
  )
}

render_result_block <- function(x) {
  cat("\n============================================================\n")
  cat(sprintf("%s\n", x$name))
  cat(sprintf("Scope: %s\n", x$label))
  cat(sprintf("Trials: %s\n", x$result$trials))
  cat(sprintf("Measure: %s\n", x$result$measure))
  cat(sprintf("Pooled effect: %.6f (%.6f to %.6f)\n", x$result$pooled, x$result$lci, x$result$uci))
  cat(sprintf("Tau^2: %.6f | I^2: %.4f | k: %d\n", x$result$tau2, x$result$I2, x$result$k))
  if (!is.na(x$result$hksjLCI)) {
    cat(sprintf("HKSJ CI: %.6f to %.6f\n", x$result$hksjLCI, x$result$hksjUCI))
  }
  if (!is.na(x$result$piLCI)) {
    cat(sprintf("Prediction interval: %.6f to %.6f\n", x$result$piLCI, x$result$piUCI))
  }
  if (!is.na(x$result$eggerP)) {
    cat(sprintf("Egger p-value: %.6f\n", x$result$eggerP))
  }
  cat(sprintf("Reference trial scope: %s | Match: %s\n", x$trials_expected, if (x$trials_pass) "PASS" else "FAIL"))
  print(x$checks, row.names = FALSE, right = FALSE)
  cat(sprintf("Overall status: %s\n", if (x$overall_pass) "PASS" else "FAIL"))
}

render_extra_analysis <- function(spec_name, spec) {
  dat <- select_outcome_data(spec$outcome)
  res <- compute_meta(dat, measure = spec$measure)
  cat("\n------------------------------------------------------------\n")
  cat(sprintf("%s\n", spec_name))
  cat(sprintf("Scope: %s\n", spec$label))
  cat(sprintf("Trials: %s\n", res$trials))
  cat(sprintf("Measure: %s\n", res$measure))
  cat(sprintf("Pooled effect: %.6f (%.6f to %.6f)\n", res$pooled, res$lci, res$uci))
  cat(sprintf("Tau^2: %.6f | I^2: %.4f | k: %d\n", res$tau2, res$I2, res$k))
}

cat("FINERENONE Self-Contained R Validation\n")
cat("Embedded dataset rows:", nrow(trial_data), "\n")
cat("Validation date:", format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z"), "\n")
cat("\nEmbedded trial rows used by this script:\n")
print(
  trial_data[, c("trial", "outcome", "tE", "tN", "cE", "cN", "source")],
  row.names = FALSE,
  right = FALSE
)

validation_results <- lapply(names(reference_results), function(nm) {
  validate_analysis(nm, reference_results[[nm]])
})
names(validation_results) <- names(reference_results)

for (res in validation_results) {
  render_result_block(res)
}

all_pass <- all(vapply(validation_results, function(x) x$overall_pass, logical(1)))

cat("\nAdditional non-reference endpoint outputs embedded in the dataset:\n")
for (nm in names(extra_analyses)) {
  render_extra_analysis(nm, extra_analyses[[nm]])
}

cat("\n============================================================\n")
if (all_pass) {
  cat("Validation summary: PASS\n")
  cat("All harmonized reference checks matched the stored HTML baselines.\n")
} else {
  cat("Validation summary: FAIL\n")
  cat("At least one reference check did not match the stored HTML baseline.\n")
  quit(status = 1)
}
