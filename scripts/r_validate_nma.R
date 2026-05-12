# R netmeta cross-validation for binary-outcome NMA reviews.
#
# Input JSON:
#   { "review": ..., "treatments": [...], "scale": "OR"|"RR",
#     "comparisons": [
#       { "studlab": ..., "t1": ..., "t2": ..., "e1": ..., "n1": ..., "e2": ..., "n2": ... },
#       ...
#     ] }
#
# Fits netmeta on log-OR contrast scale, REML, fixed=FALSE, common=FALSE.
# Returns per-treatment vs reference effect, p-scores (SUCRA-like), τ², Q.
#
# Usage: Rscript r_validate_nma.R <input.json> <output.json>

suppressPackageStartupMessages({
  library(netmeta)
  library(jsonlite)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) stop("Usage: Rscript r_validate_nma.R <input.json> <output.json>")
input_path  <- args[1]
output_path <- args[2]

dat <- fromJSON(input_path)
cmp <- dat$comparisons
if (is.null(cmp) || nrow(cmp) < 2) {
  writeLines(toJSON(list(review = dat$review, fit_ok = FALSE,
                         engine = "R-netmeta", k_comparisons = nrow(cmp) %||% 0,
                         error = "<2 valid contrasts"),
                    auto_unbox = TRUE), output_path)
  quit(status = 0)
}

# Cast to int + filter invalid
for (col in c("e1","n1","e2","n2")) cmp[[col]] <- as.integer(cmp[[col]])
cmp <- cmp[is.finite(cmp$e1) & is.finite(cmp$n1) & is.finite(cmp$e2) & is.finite(cmp$n2) &
           cmp$n1 > 0 & cmp$n2 > 0 & cmp$e1 >= 0 & cmp$e2 >= 0 &
           cmp$e1 <= cmp$n1 & cmp$e2 <= cmp$n2, , drop = FALSE]
k <- nrow(cmp)

if (k < 2) {
  writeLines(toJSON(list(review = dat$review, fit_ok = FALSE,
                         engine = "R-netmeta", k_comparisons = k,
                         error = paste0("k_comparisons=", k, " < 2")),
                    auto_unbox = TRUE), output_path)
  quit(status = 0)
}

# Compute log-OR + SE per contrast (Haldane 0.5 cc for zero cells)
zero <- with(cmp, e1 == 0 | n1 - e1 == 0 | e2 == 0 | n2 - e2 == 0)
cmp$e1c <- cmp$e1 + ifelse(zero, 0.5, 0)
cmp$n1c <- cmp$n1 + ifelse(zero, 1, 0)
cmp$e2c <- cmp$e2 + ifelse(zero, 0.5, 0)
cmp$n2c <- cmp$n2 + ifelse(zero, 1, 0)
cmp$logOR <- with(cmp, log((e1c * (n2c - e2c)) / ((n1c - e1c) * e2c)))
cmp$seLogOR <- with(cmp, sqrt(1/e1c + 1/(n1c - e1c) + 1/e2c + 1/(n2c - e2c)))

# netmeta needs studlab uniqueness; if duplicates, suffix-number
if (anyDuplicated(cmp$studlab)) {
  cmp$studlab <- make.unique(cmp$studlab)
}

fit <- tryCatch(
  netmeta(TE = cmp$logOR, seTE = cmp$seLogOR, treat1 = cmp$t1, treat2 = cmp$t2,
          studlab = cmp$studlab, sm = "OR", common = FALSE, random = TRUE,
          reference.group = dat$reference %||% NULL),
  error = function(e) NULL
)

if (is.null(fit)) {
  writeLines(toJSON(list(review = dat$review, fit_ok = FALSE,
                         engine = "R-netmeta", k_comparisons = k,
                         error = "netmeta() failed — disconnected network or degenerate"),
                    auto_unbox = TRUE), output_path)
  quit(status = 0)
}

# Pull per-treatment vs reference RE estimates
ref <- fit$reference.group
trts <- fit$trts
re_pool <- list()
for (tr in trts) {
  if (identical(tr, ref)) next
  i <- which(trts == tr); j <- which(trts == ref)
  re_pool[[tr]] <- list(
    treatment = tr,
    reference = ref,
    logOR = as.numeric(fit$TE.random[i, j]),
    seLogOR = as.numeric(fit$seTE.random[i, j]),
    OR = exp(as.numeric(fit$TE.random[i, j])),
    lci = exp(as.numeric(fit$lower.random[i, j])),
    uci = exp(as.numeric(fit$upper.random[i, j]))
  )
}

# SUCRA-equivalent p-scores
ps <- tryCatch(netrank(fit, common = FALSE)$ranking.random, error = function(e) NULL)

out <- list(
  review = dat$review,
  engine = "R-netmeta",
  netmeta_version = as.character(packageVersion("netmeta")),
  k_comparisons = k,
  n_treatments = length(trts),
  reference = ref,
  fit_ok = TRUE,
  tau2 = as.numeric(fit$tau2),
  Q   = as.numeric(fit$Q),
  Qdf = as.numeric(fit$df.Q),
  Qp  = as.numeric(fit$pval.Q),
  I2  = as.numeric(fit$I2),
  treatments = as.list(trts),
  pooled = re_pool,
  pscores = if (!is.null(ps)) as.list(ps) else NULL
)
writeLines(toJSON(out, auto_unbox = TRUE, pretty = TRUE, na = "null"), output_path)
cat("Wrote", output_path, "\n")

`%||%` <- function(a, b) if (is.null(a)) b else a
