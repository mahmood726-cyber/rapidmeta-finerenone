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
  error = function(e) NULL
)

# RCS-3 pool: knots at Harrell 25/50/75 of non-reference doses
knots <- quantile(df$dose[df$dose > 0], c(0.25, 0.50, 0.75))
fit_rcs <- tryCatch(
  dosresmeta(formula = logrr ~ rcs(dose, knots),
             cases = events, n = n, type = type, v = v,
             data = df, id = studlab, method = "reml"),
  error = function(e) NULL
)

# Wald non-linearity test on RCS fit
nl_p <- NA_real_
if (!is.null(fit_rcs)) {
  bv <- coef(fit_rcs)
  V  <- vcov(fit_rcs)
  if (length(bv) >= 2) {
    nl_coef <- bv[-1]
    nl_V    <- V[-1, -1, drop = FALSE]
    W <- t(nl_coef) %*% solve(nl_V) %*% nl_coef
    nl_p <- 1 - pchisq(as.numeric(W), df = length(nl_coef))
  }
}

out <- list(
  review = dat$review,
  engine = "R-dosresmeta",
  dosresmeta_version = as.character(packageVersion("dosresmeta")),
  k = length(trials),
  linear = if (is.null(fit_lin)) list(fit_ok = FALSE) else list(
    fit_ok = TRUE,
    pooled_slope_log    = as.numeric(coef(fit_lin)),
    pooled_slope_log_se = as.numeric(sqrt(vcov(fit_lin))),
    tau2 = if (!is.null(fit_lin$Psi)) as.numeric(fit_lin$Psi[1, 1]) else NA_real_
  ),
  rcs = if (is.null(fit_rcs)) list(fit_ok = FALSE) else list(
    fit_ok = TRUE,
    knots            = as.numeric(knots),
    spline_coefs     = as.numeric(coef(fit_rcs)),
    spline_coefs_cov = matrix(as.numeric(vcov(fit_rcs)), nrow = length(coef(fit_rcs))),
    nonlinearity_wald_p = nl_p
  )
)
writeLines(toJSON(out, auto_unbox = TRUE, pretty = TRUE, na = "null"), output_path)
cat("Wrote", output_path, "\n")
