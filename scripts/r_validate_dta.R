# R metafor / mada cross-validation for DTA reviews.
#
# Reads a JSON file with structure:
#   {
#     "review": "<REVIEW_STEM>",
#     "trials": [
#       { "studlab": "...", "TP": int, "FP": int, "FN": int, "TN": int },
#       ...
#     ]
#   }
#
# Fits the Reitsma bivariate model via mada::reitsma() and writes a JSON
# result with pooled Se, Sp, DOR, LR+, LR-, AUC + 95% CIs.
#
# Usage:
#   Rscript r_validate_dta.R <input.json> <output.json>

suppressPackageStartupMessages({
  library(mada)
  library(jsonlite)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) {
  stop("Usage: Rscript r_validate_dta.R <input.json> <output.json>")
}
input_path  <- args[1]
output_path <- args[2]

dat <- fromJSON(input_path)
trials <- dat$trials

# mada::reitsma handles zero cells via its built-in correction option.
# Pre-cast to integer so the input passes its checkdata() validator.
trials$TP <- as.integer(trials$TP)
trials$FP <- as.integer(trials$FP)
trials$FN <- as.integer(trials$FN)
trials$TN <- as.integer(trials$TN)
needs_cc <- with(trials, TP == 0 | FP == 0 | FN == 0 | TN == 0)

# Fit Reitsma bivariate model (mada applies +0.5 cc for zero cells internally).
fit <- tryCatch(
  reitsma(trials, TP = "TP", FP = "FP", FN = "FN", TN = "TN", correction.control = "all"),
  error = function(e) NULL
)

if (is.null(fit)) {
  out <- list(
    review = dat$review,
    engine = "R-mada-reitsma",
    mada_version = as.character(packageVersion("mada")),
    k = nrow(trials),
    fit_ok = FALSE,
    error = "reitsma() failed — likely k<4 or singular Hessian"
  )
} else {
  sm <- summary(fit)
  # Pull logit-scale point estimates + CIs from confint(fit). Row names
  # are "tsens.(Intercept)" and "tfpr.(Intercept)" (with covariates,
  # additional rows). summary()$coefficients carries the same rows plus
  # Estimate/SE/z/p columns.
  ci_logit  <- confint(fit)
  ci_tsens_row <- grep("^tsens", rownames(ci_logit), value = TRUE)[1]
  ci_tfpr_row  <- grep("^tfpr",  rownames(ci_logit), value = TRUE)[1]
  sm_coef <- summary(fit)$coefficients
  est_col <- if ("Estimate" %in% colnames(sm_coef)) "Estimate" else colnames(sm_coef)[1]
  tsens_logit <- as.numeric(sm_coef[ci_tsens_row, est_col])
  tfpr_logit  <- as.numeric(sm_coef[ci_tfpr_row,  est_col])
  # mada parameterizes on FPR = 1 - Sp; sign-flip for Sp
  inv_logit <- function(x) 1 / (1 + exp(-x))
  sens_pool <- as.numeric(inv_logit(tsens_logit))
  fpr_pool  <- as.numeric(inv_logit(tfpr_logit))
  spec_pool <- 1 - fpr_pool
  sens_lci  <- as.numeric(inv_logit(ci_logit[ci_tsens_row, 1]))
  sens_uci  <- as.numeric(inv_logit(ci_logit[ci_tsens_row, 2]))
  spec_lci  <- 1 - as.numeric(inv_logit(ci_logit[ci_tfpr_row, 2]))
  spec_uci  <- 1 - as.numeric(inv_logit(ci_logit[ci_tfpr_row, 1]))
  # Likelihood ratios + DOR from pooled point estimates
  lr_pos    <- sens_pool / (1 - spec_pool)
  lr_neg    <- (1 - sens_pool) / spec_pool
  dor       <- lr_pos / lr_neg
  # AUC of HSROC curve via summary
  auc_obj <- tryCatch(AUC(fit), error = function(e) NULL)
  auc_val <- if (!is.null(auc_obj)) as.numeric(auc_obj$AUC) else NA_real_

  out <- list(
    review = dat$review,
    engine = "R-mada-reitsma",
    mada_version = as.character(packageVersion("mada")),
    k = nrow(trials),
    fit_ok = TRUE,
    cc_applied = sum(needs_cc),
    sens_pool = sens_pool, sens_lci = sens_lci, sens_uci = sens_uci,
    spec_pool = spec_pool, spec_lci = spec_lci, spec_uci = spec_uci,
    lr_pos = lr_pos, lr_neg = lr_neg, dor = dor,
    auc = auc_val,
    tsens_logit = as.numeric(tsens_logit),
    tfpr_logit  = as.numeric(tfpr_logit)
  )
}

writeLines(toJSON(out, auto_unbox = TRUE, pretty = TRUE, na = "null"), output_path)
cat("Wrote", output_path, "\n")
