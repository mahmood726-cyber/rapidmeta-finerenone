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
    # P0-3 fix: clamp to [0,1] (back-transforms can produce out-of-range
    # bounds for sparse-event proportions) AND enforce monotonicity
    # (Barendregt 2013 warns ipft.hm can give non-monotone CIs at small k).
    pool_est <- pmin(pmax(as.numeric(pool_est), 0), 1)
    pool_lci <- pmin(pmax(as.numeric(pool_lci), 0), 1)
    pool_uci <- pmin(pmax(as.numeric(pool_uci), 0), 1)
    if (pool_lci > pool_est) pool_lci <- pool_est
    if (pool_uci < pool_est) pool_uci <- pool_est
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

# P1-18 fix: Schwarzer 2019 rule for primary pool selection.
#   PFT primary when any p̂_i < 0.2 or > 0.8 AND τ̂² > 0.1
#   Logit primary otherwise.
proportions <- with(trials, e / n)
schwarzer_pft <- (any(proportions < 0.2 | proportions > 0.8) &&
                  !is.null(logit_pool) && logit_pool$tau2 > 0.1)
primary_method <- if (schwarzer_pft) "freeman_tukey" else "logit"

# P1-9 fix: HKSJ floor disclosure. metafor's test="knha" can produce CIs
# narrower than DL when Q < df; the Cochrane v6.5 / RevMan-2025 convention
# is to enforce max(1, Q/(k-1)). We report whether the floor would have
# been active (HKSJ inflation factor).
hksj_floor_applied <- FALSE
hksj_inflation <- NA_real_
if (!is.null(logit_pool) && !is.null(logit_pool$Q) && k >= 2) {
  q_over_df <- logit_pool$Q / max(1, k - 1)
  hksj_inflation <- max(1, q_over_df)
  hksj_floor_applied <- (q_over_df < 1)
}

out <- list(
  review = dat$review,
  engine = "R-metafor-rma",
  metafor_version = as.character(packageVersion("metafor")),
  k = k,
  fit_ok = !is.null(logit_pool),
  primary_method = primary_method,  # P1-18 Schwarzer choice
  schwarzer_rule = if (schwarzer_pft) "PFT primary (extreme proportions + tau2>0.1)" else "logit primary",
  hksj_floor_applied = hksj_floor_applied,  # P1-9 disclosure
  hksj_inflation_factor = hksj_inflation,
  logit_pool = logit_pool,
  freeman_tukey_pool = ft_pool
)
writeLines(toJSON(out, auto_unbox = TRUE, pretty = TRUE, na = "null"), output_path)
cat("Wrote", output_path, "\n")
