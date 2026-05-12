# R dosresmeta cross-validation for dose-response reviews.
#
# Input JSON shape (matches tests/dose_response_fixtures/<name>.json):
#   { "review": "<name>",
#     "trials": [
#       { "studlab": "...", "arms": [
#         { "dose": 0, "events": ..., "n": ..., "is_reference": true },
#         { "dose": ..., "events": ..., "n": ..., "is_reference": false }
#       ]}, ...
#     ]}
#
# Output JSON: { review, engine: "R-dosresmeta", dosresmeta_version, k,
#                linear: {fit_ok, pooled_slope_log, pooled_slope_log_se, tau2},
#                rcs: {fit_ok, knots, spline_coefs, spline_coefs_cov, nonlinearity_wald_p}
#              }
#
# Usage: Rscript r_validate_doseresp.R <input.json> <output.json>
#
# Implementation notes:
#   dosresmeta 2.x with covariance="gl" requires:
#     (a) cases, n, type as data columns (type="ci" for cohort data),
#     (b) v: the diagonal GL variance 1/d_j + 1/d_0 - 1/n_j - 1/n_0,
#     (c) logrr: pre-computed log(rate_j/rate_ref) as a data column.
#   The package then constructs the full off-diagonal GL covariance from (a)+(b).

suppressPackageStartupMessages({
  library(dosresmeta)
  library(rms)
  library(jsonlite)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) stop("Usage: Rscript r_validate_doseresp.R <input.json> <output.json>")
input_path  <- args[1]
output_path <- args[2]

dat <- fromJSON(input_path, simplifyDataFrame = FALSE)
trials <- dat$trials

# Flatten to a single data.frame, pre-computing logrr and GL variance
rows <- list()
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
      studlab     = t$studlab,
      dose        = a$dose,
      events      = a$events,
      n           = a$n,
      type        = "ci",      # cohort incidence
      logrr       = logrr_val,
      v           = v_val,
      is_reference = is_ref,
      stringsAsFactors = FALSE
    )
  }
}
df <- do.call(rbind, rows)

# Linear pool
fit_lin <- tryCatch(
  dosresmeta(formula = logrr ~ dose,
             cases = events, n = n, type = type, v = v,
             data = df, id = studlab, method = "reml"),
  error = function(e) structure(list(), class = "fitError", .error_msg = conditionMessage(e))
)

# RCS-3 pool: knots at Harrell 25/50/75 of non-reference doses
# P1-1: Use unique non-reference doses for Harrell-percentile knot placement, aligning with
# the JS engine's rcsKnots() convention. Closer to Harrell's intent (percentiles of distinct
# covariate values) and eliminates the silent engine-vs-R knot divergence on datasets with
# dose-level repetition.
knots <- quantile(unique(df$dose[df$dose > 0]), c(0.25, 0.50, 0.75))
fit_rcs <- tryCatch(
  dosresmeta(formula = logrr ~ rcs(dose, knots),
             cases = events, n = n, type = type, v = v,
             data = df, id = studlab, method = "reml"),
  error = function(e) structure(list(), class = "fitError", .error_msg = conditionMessage(e))
)

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

# One-stage Poisson hierarchical (lme4::glmer with offset). Per-arm counts modelled
# with random study intercept; dose enters as a fixed effect on the log-rate scale.
# Dose is scaled by sd(dose[dose > 0]) to avoid the "very large eigenvalue" near-
# unidentifiability warning; coefficients are back-transformed to the original scale.
suppressPackageStartupMessages({ library(lme4) })

dose_sd_pos <- sd(df$dose[df$dose > 0])
df$dose_scaled <- df$dose / dose_sd_pos

fit_os <- tryCatch(
  glmer(events ~ dose_scaled + (1 | studlab), offset = log(n),
        family = poisson(link = "log"), data = df,
        control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e5))),
  error = function(e) structure(list(), class = "fitError", .error_msg = conditionMessage(e))
)

one_stage_block <- if (is.null(fit_os) || inherits(fit_os, "fitError")) {
  list(fit_ok = FALSE, error_msg = if (inherits(fit_os, "fitError")) attr(fit_os, ".error_msg") else "glmer fit returned NULL")
} else tryCatch({
  conv_ok <- is.null(fit_os@optinfo$conv$lme4$messages) ||
             length(fit_os@optinfo$conv$lme4$messages) == 0
  # Back-transform to original dose scale
  coef_sc  <- as.numeric(fixef(fit_os)["dose_scaled"])
  se_sc    <- as.numeric(sqrt(diag(vcov(fit_os))["dose_scaled"]))
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
writeLines(toJSON(out, auto_unbox = TRUE, pretty = TRUE, na = "null"), output_path)
cat("Wrote", output_path, "\n")
