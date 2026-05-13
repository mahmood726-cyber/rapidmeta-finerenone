# R dosresmeta cross-validation for dose-response reviews.
#
# Input JSON shape (matches tests/dose_response_fixtures/<name>.json):
#
#   Binary (events+n) fixture:
#   { "review": "<name>",
#     "trials": [
#       { "studlab": "...", "arms": [
#         { "dose": 0, "events": ..., "n": ..., "is_reference": true },
#         { "dose": ..., "events": ..., "n": ..., "is_reference": false }
#       ]}, ...
#     ]}
#
#   Continuous (mean+sd+n) fixture — Round 2A addition:
#   { "review": "<name>",
#     "trials": [
#       { "studlab": "...", "arms": [
#         { "dose": 0, "mean": ..., "sd": ..., "n": ..., "is_reference": true },
#         { "dose": ..., "mean": ..., "sd": ..., "n": ..., "is_reference": false }
#       ]}, ...
#     ]}
#
# Output JSON: { review, engine: "R-dosresmeta", dosresmeta_version, k,
#                linear: {fit_ok, pooled_slope_log, pooled_slope_log_se, tau2},
#                rcs: {fit_ok, knots, spline_coefs, spline_coefs_cov, nonlinearity_wald_p},
#                one_stage: {fit_ok, coef_dose, coef_dose_se, ...}
#              }
#
# Usage: Rscript r_validate_doseresp.R <input.json> <output.json>
#
# Mode detection (Round 2A, spec §4):
#   is_continuous = TRUE if the first arm of the first trial has a non-null "mean" field.
#   Binary mode: dosresmeta type="ir" (cohort incidence rates) + lme4::glmer Poisson.
#   Continuous mode: dosresmeta type="md" (mean differences) + lme4::lmer with IV weights.
#   Output JSON field semantics are documented in the spec:
#     "pooled_slope_log" / "coef_dose" represent log-RR per unit dose (binary) or
#     MD per unit dose (continuous). Named identically to allow a single parity harness.
#
# Implementation notes (binary path):
#   dosresmeta 2.x with covariance="gl" requires:
#     (a) cases, n, type as data columns (type="ci" for cohort data),
#     (b) v: the diagonal GL variance 1/d_j + 1/d_0 - 1/n_j - 1/n_0,
#     (c) logrr: pre-computed log(rate_j/rate_ref) as a data column.
#   The package then constructs the full off-diagonal GL covariance from (a)+(b).
#
# Implementation notes (continuous path, Round 2A):
#   dosresmeta covariance="md" (NOT type="md") expects:
#     (a) mean (outcome mean), sd (outcome SD), n (arm sample size) columns,
#     (b) a reference arm row per trial (dose=0) — same structure as binary.
#     (c) NO type argument (type is only for covariance="gl"/"h").
#   The package computes within-trial (k-1)×(k-1) covariance automatically from
#   the shared-reference variance formula: S[i,i]=sd_i^2/n_i + sd_ref^2/n_ref,
#   S[i,j]=sd_ref^2/n_ref for i≠j.  This matches the JS engine's mdCovariance().
#   One-stage: lmer(mean ~ dose_scaled + (1|studlab), weights=1/(sd^2/n)).
#   Dose-scaling by sd(non-reference doses) continues per Round 1B convergence
#   precedent; back-transform divides by dose_sd_pos.

suppressPackageStartupMessages({
  library(dosresmeta)
  library(rms)
  library(jsonlite)
  library(lme4)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) stop("Usage: Rscript r_validate_doseresp.R <input.json> <output.json>")
input_path  <- args[1]
output_path <- args[2]

dat <- fromJSON(input_path, simplifyDataFrame = FALSE)
trials <- dat$trials

# ── Mode detection (spec §4): continuous vs binary ────────────────────────────
# Use the first arm of the first trial as the probe. A fixture is continuous if
# the arm carries a non-null "mean" field; otherwise it is binary (events+n).
is_continuous <- !is.null(trials[[1]]$arms[[1]]$mean) &&
                 !is.null(trials[[1]]$arms[[1]]$sd)

# ── Flatten to data.frame ─────────────────────────────────────────────────────
rows <- list()

if (is_continuous) {
  # Continuous path (Round 2A): dosresmeta type="md"
  # Each row carries (studlab, dose, mean, sd, n, is_reference).
  # dosresmeta computes the within-trial shared-reference covariance from sd+n.
  for (t in trials) {
    for (a in t$arms) {
      is_ref <- isTRUE(a$is_reference)
      rows[[length(rows) + 1]] <- data.frame(
        studlab      = t$studlab,
        dose         = a$dose,
        mean         = a$mean,
        sd           = a$sd,
        n            = a$n,
        is_reference = is_ref,
        stringsAsFactors = FALSE
      )
    }
  }
} else {
  # Binary path (original): dosresmeta type="ir" cohort incidence
  # Pre-compute logrr and diagonal GL variance here; package uses both.
  for (t in trials) {
    ref_arm <- Filter(function(a) isTRUE(a$is_reference), t$arms)[[1]]
    d0 <- ref_arm$events
    n0 <- ref_arm$n
    log_rate_ref <- log(d0 / n0)

    for (a in t$arms) {
      is_ref <- isTRUE(a$is_reference)
      # log-RR vs. reference arm (0 for reference)
      logrr_val <- if (is_ref) 0 else log(a$events / a$n) - log_rate_ref
      # Diagonal GL variance: 1/d_j + 1/d_0 - 1/n_j - 1/n_0 (cohort formula)
      v_val <- if (is_ref) 0 else (1/a$events + 1/d0 - 1/a$n - 1/n0)

      rows[[length(rows) + 1]] <- data.frame(
        studlab      = t$studlab,
        dose         = a$dose,
        events       = a$events,
        n            = a$n,
        type         = "ci",      # cohort incidence
        logrr        = logrr_val,
        v            = v_val,
        is_reference = is_ref,
        stringsAsFactors = FALSE
      )
    }
  }
}

df <- do.call(rbind, rows)

# ── Linear pool ───────────────────────────────────────────────────────────────
# Dispatch on is_continuous (spec §4).
# Continuous: dosresmeta covariance="md" (Mean Differences) — slope is MD per unit dose.
#   The type argument is not used for covariance="md"; sd and n are required instead.
#   dosresmeta constructs the within-trial shared-reference covariance from sd+n
#   (identical to the JS engine's mdCovariance()).
# Binary:     dosresmeta type="ir" (cohort incidence rates) — slope is log-RR per unit dose.
fit_lin <- if (is_continuous) {
  tryCatch(
    dosresmeta(formula = mean ~ dose,
               covariance = "md", sd = sd, n = n,
               data = df, id = studlab, method = "reml"),
    error = function(e) structure(list(), class = "fitError", .error_msg = conditionMessage(e))
  )
} else {
  tryCatch(
    dosresmeta(formula = logrr ~ dose,
               cases = events, n = n, type = type, v = v,
               data = df, id = studlab, method = "reml"),
    error = function(e) structure(list(), class = "fitError", .error_msg = conditionMessage(e))
  )
}

# ── RCS-3 pool ────────────────────────────────────────────────────────────────
# P1-1: Use unique non-reference doses for Harrell-percentile knot placement, aligning with
# the JS engine's rcsKnots() convention. Closer to Harrell's intent (percentiles of distinct
# covariate values) and eliminates the silent engine-vs-R knot divergence on datasets with
# dose-level repetition.
# Dispatch on is_continuous (spec §4); formula changes but knot placement is identical.
# Continuous RCS uses covariance="md" to match the linear path.
knots <- quantile(unique(df$dose[df$dose > 0]), c(0.25, 0.50, 0.75))
fit_rcs <- if (is_continuous) {
  tryCatch(
    dosresmeta(formula = mean ~ rcs(dose, knots),
               covariance = "md", sd = sd, n = n,
               data = df, id = studlab, method = "reml"),
    error = function(e) structure(list(), class = "fitError", .error_msg = conditionMessage(e))
  )
} else {
  tryCatch(
    dosresmeta(formula = logrr ~ rcs(dose, knots),
               cases = events, n = n, type = type, v = v,
               data = df, id = studlab, method = "reml"),
    error = function(e) structure(list(), class = "fitError", .error_msg = conditionMessage(e))
  )
}

# Wald non-linearity test on RCS fit
nl_p <- NA_real_
if (!is.null(fit_rcs) && !inherits(fit_rcs, "fitError")) {
  bv <- coef(fit_rcs)
  V  <- vcov(fit_rcs)
  if (length(bv) >= 2) {
    nl_coef <- bv[-1]
    nl_V    <- V[-1, -1, drop = FALSE]
    W <- t(nl_coef) %*% solve(nl_V) %*% nl_coef
    nl_p <- 1 - pchisq(as.numeric(W), df = length(nl_coef))
  }
}

# ── One-stage hierarchical model (spec §4) ────────────────────────────────────
# Dose is scaled by sd(non-reference doses) to avoid near-unidentifiability warnings
# (Round 1B precedent). Coefficients are back-transformed to original dose scale.
# dose_scale_sd and coef_dose_on_scaled are persisted as audit-trail fields in both modes.
#
# Binary mode:   lme4::glmer — Poisson log-link with offset(log(n)).
# Continuous mode: lme4::lmer — Gaussian with inverse-variance weights 1/(sd²/n).
#   Weights are per-arm variances of the mean estimate; this matches the dosresmeta
#   MD covariance diagonal (sd_i²/n_i) used in the pooled fits above.

dose_sd_pos <- sd(df$dose[df$dose > 0])
df$dose_scaled <- df$dose / dose_sd_pos

fit_os <- if (is_continuous) {
  # Continuous one-stage: lmer with IV weights
  # Weight = 1 / (variance of the arm mean) = n / sd²
  # (Spec §4: df$.w = 1 / ((df$sd * df$sd) / df$n))
  df$.w <- df$n / (df$sd * df$sd)
  tryCatch(
    lmer(mean ~ dose_scaled + (1 | studlab), data = df, weights = df$.w,
         REML = TRUE,
         control = lmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e5))),
    error = function(e) structure(list(), class = "fitError", .error_msg = conditionMessage(e))
  )
} else {
  # Binary one-stage: glmer Poisson with offset (original path)
  tryCatch(
    glmer(events ~ dose_scaled + (1 | studlab), offset = log(n),
          family = poisson(link = "log"), data = df,
          control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e5))),
    error = function(e) structure(list(), class = "fitError", .error_msg = conditionMessage(e))
  )
}

one_stage_block <- if (is.null(fit_os) || inherits(fit_os, "fitError")) {
  list(fit_ok = FALSE,
       error_msg = if (inherits(fit_os, "fitError")) attr(fit_os, ".error_msg")
                   else paste0(if (is_continuous) "lmer" else "glmer", " fit returned NULL"))
} else tryCatch({
  if (is_continuous) {
    # lmer convergence check — same slot path as glmer
    conv_ok <- is.null(fit_os@optinfo$conv$lme4$messages) ||
               length(fit_os@optinfo$conv$lme4$messages) == 0
    # Back-transform to original dose scale
    coef_sc   <- as.numeric(fixef(fit_os)["dose_scaled"])
    se_sc     <- as.numeric(sqrt(diag(vcov(fit_os))["dose_scaled"]))
    coef_orig <- coef_sc / dose_sd_pos
    se_orig   <- se_sc  / dose_sd_pos
    ci_lo_orig <- coef_orig - 1.96 * se_orig
    ci_hi_orig <- coef_orig + 1.96 * se_orig
    list(
      fit_ok = TRUE,
      lme4_version = as.character(packageVersion("lme4")),
      dose_scale_sd = dose_sd_pos,
      coef_dose_on_scaled = as.numeric(coef_sc),
      coef_dose = coef_orig,
      coef_dose_se = se_orig,
      coef_dose_ci_lo = ci_lo_orig,
      coef_dose_ci_hi = ci_hi_orig,
      random_effects_var = as.numeric(VarCorr(fit_os)$studlab[1, 1]),
      converged = conv_ok
    )
  } else {
    # Binary glmer path (original, unchanged)
    conv_ok <- is.null(fit_os@optinfo$conv$lme4$messages) ||
               length(fit_os@optinfo$conv$lme4$messages) == 0
    # Back-transform to original dose scale
    coef_sc   <- as.numeric(fixef(fit_os)["dose_scaled"])
    se_sc     <- as.numeric(sqrt(diag(vcov(fit_os))["dose_scaled"]))
    coef_orig <- coef_sc  / dose_sd_pos
    se_orig   <- se_sc    / dose_sd_pos
    ci_lo_orig <- coef_orig - 1.96 * se_orig
    ci_hi_orig <- coef_orig + 1.96 * se_orig
    list(
      fit_ok = TRUE,
      lme4_version = as.character(packageVersion("lme4")),
      dose_scale_sd = dose_sd_pos,
      coef_dose_on_scaled = as.numeric(coef_sc),
      coef_dose = coef_orig,
      coef_dose_se = se_orig,
      coef_dose_ci_lo = ci_lo_orig,
      coef_dose_ci_hi = ci_hi_orig,
      random_effects_var = as.numeric(VarCorr(fit_os)$studlab[1, 1]),
      converged = conv_ok
    )
  }
}, error = function(e) list(fit_ok = FALSE, error_msg = paste0("post-fit failure: ", conditionMessage(e))))

out <- list(
  review = dat$review,
  engine = "R-dosresmeta",
  dosresmeta_version = as.character(packageVersion("dosresmeta")),
  k = length(trials),
  linear = if (is.null(fit_lin)) {
    list(fit_ok = FALSE, error_msg = "fit not attempted")
  } else if (inherits(fit_lin, "fitError")) {
    list(fit_ok = FALSE, error_msg = attr(fit_lin, ".error_msg"))
  } else {
    list(
      fit_ok = TRUE,
      pooled_slope_log    = as.numeric(coef(fit_lin)),
      pooled_slope_log_se = as.numeric(sqrt(vcov(fit_lin))),
      tau2 = if (!is.null(fit_lin$Psi)) as.numeric(fit_lin$Psi[1, 1]) else NA_real_
    )
  },
  rcs = if (is.null(fit_rcs)) {
    list(fit_ok = FALSE, error_msg = "fit not attempted")
  } else if (inherits(fit_rcs, "fitError")) {
    list(fit_ok = FALSE, error_msg = attr(fit_rcs, ".error_msg"))
  } else {
    list(
      fit_ok = TRUE,
      knots            = as.numeric(knots),
      spline_coefs     = as.numeric(coef(fit_rcs)),
      spline_coefs_cov = matrix(as.numeric(vcov(fit_rcs)), nrow = length(coef(fit_rcs))),
      nonlinearity_wald_p = nl_p
    )
  },
  one_stage = one_stage_block
)
## Round 3.1 (2026-05-13): digits=8 prevents τ²-parity false-positive amber
## rows in the badge. jsonlite::toJSON defaults to digits=4, which rounded
## tirzepatide's τ²=0.001644 down to 0.0016 (|Δ| 0.000129 > 0.0001 threshold;
## true |Δ| was 0.000086, well inside). 8 sig figs match metafor/dosresmeta
## report-level precision.
writeLines(toJSON(out, auto_unbox = TRUE, pretty = TRUE, na = "null", digits = 8), output_path)
cat("Wrote", output_path, "\n")
