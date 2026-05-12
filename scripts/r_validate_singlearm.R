# R metafor cross-validation for single-arm proportion meta-analyses.
#
# Input JSON:
#   {
#     "review": "<REVIEW_STEM>",
#     "trials": [
#       { "studlab": "...", "e": <events>, "n": <total> },
#       ...
#     ]
#   }
#
# Fits two random-effects pools:
#   1. Logit transform (rma measure="PLO"), back-transformed (transf.ilogit)
#   2. Freeman-Tukey double-arcsine (rma measure="PFT"), back-transformed
#      (transf.ipft.hm)
#
# Uses REML estimator + HKSJ-Knapp correction for both.
#
# Usage: Rscript r_validate_singlearm.R <input.json> <output.json>

suppressPackageStartupMessages({
  library(metafor)
  library(jsonlite)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) stop("Usage: Rscript r_validate_singlearm.R <input.json> <output.json>")
input_path  <- args[1]
output_path <- args[2]

dat <- fromJSON(input_path)
trials <- dat$trials

# Cast to integer and basic sanity
trials$e <- as.integer(trials$e)
trials$n <- as.integer(trials$n)
trials   <- trials[trials$n > 0 & trials$e >= 0 & trials$e <= trials$n, , drop = FALSE]

k <- nrow(trials)
if (k < 2) {
  writeLines(toJSON(list(review = dat$review, fit_ok = FALSE,
                         error = paste0("k=", k, " < 2"),
                         engine = "R-metafor-rma", k = k),
                    auto_unbox = TRUE), output_path)
  quit(status = 0)
}

fit_pool <- function(measure, transf_fn = NULL) {
  esc <- tryCatch(
    escalc(measure = measure, xi = trials$e, ni = trials$n, slab = trials$studlab),
    error = function(e) NULL
  )
  if (is.null(esc)) return(NULL)
  m <- tryCatch(
    rma(yi, vi, data = esc, method = "REML", test = "knha"),
    error = function(e) NULL
  )
  if (is.null(m)) return(NULL)
  est_logit <- as.numeric(m$b)
  lci_logit <- as.numeric(m$ci.lb)
  uci_logit <- as.numeric(m$ci.ub)
  if (!is.null(transf_fn)) {
    if (identical(transf_fn, transf.ipft.hm)) {
      # metafor signature: transf.ipft.hm(xi, targs=list(ni=...))
      pool_est <- transf.ipft.hm(est_logit, targs = list(ni = trials$n))
      pool_lci <- transf.ipft.hm(lci_logit, targs = list(ni = trials$n))
      pool_uci <- transf.ipft.hm(uci_logit, targs = list(ni = trials$n))
    } else {
      pool_est <- transf_fn(est_logit)
      pool_lci <- transf_fn(lci_logit)
      pool_uci <- transf_fn(uci_logit)
    }
  } else {
    pool_est <- est_logit; pool_lci <- lci_logit; pool_uci <- uci_logit
  }
  list(
    pool = as.numeric(pool_est), lci = as.numeric(pool_lci), uci = as.numeric(pool_uci),
    tau2 = as.numeric(m$tau2), I2 = as.numeric(m$I2), Q = as.numeric(m$QE),
    Qp  = as.numeric(m$QEp),  H2 = as.numeric(m$H2),
    se_pool = as.numeric(m$se), k = m$k.eff
  )
}

logit_pool <- fit_pool("PLO", transf.ilogit)
ft_pool    <- fit_pool("PFT", transf.ipft.hm)

out <- list(
  review = dat$review,
  engine = "R-metafor-rma",
  metafor_version = as.character(packageVersion("metafor")),
  k = k,
  fit_ok = !is.null(logit_pool),
  logit_pool = logit_pool,
  freeman_tukey_pool = ft_pool
)
writeLines(toJSON(out, auto_unbox = TRUE, pretty = TRUE, na = "null"), output_path)
cat("Wrote", output_path, "\n")
