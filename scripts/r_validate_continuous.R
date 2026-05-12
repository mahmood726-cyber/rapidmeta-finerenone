# R metafor cross-validation for continuous-outcome reviews (MD pool).
#
# Input JSON:
#   { "review": ..., "scale": "MD",
#     "trials": [ { "studlab": ..., "yi": <effect>, "vi": <variance> }, ... ] }
#
# Fits rma(yi, vi, method="REML", test="knha") and reports pool + CI + τ² + I².
#
# Usage: Rscript r_validate_continuous.R <input.json> <output.json>

suppressPackageStartupMessages({
  library(metafor)
  library(jsonlite)
})

# P0-1 fix: define `%||%` BEFORE first use. Survives R<4.4 (which lacks base
# `%||%`); on R≥4.4 this shadows the identical base operator harmlessly.
`%||%` <- function(a, b) if (is.null(a)) b else a

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) stop("Usage: Rscript r_validate_continuous.R <input.json> <output.json>")
input_path  <- args[1]
output_path <- args[2]

dat <- fromJSON(input_path)
trials <- dat$trials
# Filter out invalid rows
trials <- trials[is.finite(trials$yi) & is.finite(trials$vi) & trials$vi > 0, , drop = FALSE]
k <- nrow(trials)

if (k < 2) {
  writeLines(toJSON(list(review = dat$review, fit_ok = FALSE,
                         engine = "R-metafor-rma", k = k,
                         error = paste0("k=", k, " < 2")),
                    auto_unbox = TRUE), output_path)
  quit(status = 0)
}

fit <- tryCatch(
  rma(yi = trials$yi, vi = trials$vi, method = "REML", test = "knha"),
  error = function(e) NULL
)

if (is.null(fit)) {
  writeLines(toJSON(list(review = dat$review, fit_ok = FALSE, k = k,
                         engine = "R-metafor-rma",
                         error = "rma() failed"),
                    auto_unbox = TRUE), output_path)
  quit(status = 0)
}

# Prediction interval (Cochrane v6.5 t_{k-1} convention)
pi <- predict(fit)

out <- list(
  review = dat$review,
  engine = "R-metafor-rma",
  metafor_version = as.character(packageVersion("metafor")),
  scale = dat$scale %||% "MD",
  k = k,
  fit_ok = TRUE,
  pool = as.numeric(fit$b),
  se = as.numeric(fit$se),
  lci = as.numeric(fit$ci.lb),
  uci = as.numeric(fit$ci.ub),
  zval = as.numeric(fit$zval),
  pval = as.numeric(fit$pval),
  tau2 = as.numeric(fit$tau2),
  tau  = as.numeric(sqrt(fit$tau2)),
  I2 = as.numeric(fit$I2),
  H2 = as.numeric(fit$H2),
  Q  = as.numeric(fit$QE),
  Qp = as.numeric(fit$QEp),
  PI_lci = as.numeric(pi$pi.lb),
  PI_uci = as.numeric(pi$pi.ub)
)
writeLines(toJSON(out, auto_unbox = TRUE, pretty = TRUE, na = "null"), output_path)
cat("Wrote", output_path, "\n")
