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
  library(metafor)
  library(jsonlite)
})

# P0-1 fix: define `%||%` BEFORE first use.
`%||%` <- function(a, b) if (is.null(a)) b else a

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

# P0-7 fix: cell-level Haldane 0.5 continuity correction via metafor::escalc
# (add=1/2, to="only0") — only zero cells get +0.5, not the whole 2x2. The
# yi/vi returned are the standard Woolf log-OR and its asymptotic variance.
es <- escalc(measure = "OR",
             ai = cmp$e1, n1i = cmp$n1,
             ci = cmp$e2, n2i = cmp$n2,
             slab = cmp$studlab,
             add = 1/2, to = "only0")
cmp$logOR   <- as.numeric(es$yi)
cmp$seLogOR <- sqrt(as.numeric(es$vi))
zero_count  <- sum(with(cmp, e1 == 0 | n1 - e1 == 0 | e2 == 0 | n2 - e2 == 0))

# P0-2 fix: do NOT make.unique() studlabs. netmeta detects multi-arm trials
# by repeated studlab and applies the tau²/2 shared-control covariance
# automatically. Fake-uniquing destroys that linkage.

# P0-9 fix: explicit connectivity check BEFORE attempting the fit.
nc <- tryCatch(
  netconnection(treat1 = cmp$t1, treat2 = cmp$t2, studlab = cmp$studlab),
  error = function(e) NULL
)
if (!is.null(nc) && nc$n.subnets > 1) {
  # Compose subnet summary
  subnet_sizes <- as.integer(table(nc$subnet))
  writeLines(toJSON(list(
    review = dat$review, fit_ok = FALSE,
    engine = "R-netmeta",
    netmeta_version = as.character(packageVersion("netmeta")),
    k_comparisons = k,
    connected = FALSE,
    n_subnets = as.integer(nc$n.subnets),
    subnet_sizes = subnet_sizes,
    error = paste0("Disconnected network: ", nc$n.subnets,
                    " sub-networks (sizes: ", paste(subnet_sizes, collapse = ", "), ")")
  ), auto_unbox = TRUE, pretty = TRUE), output_path)
  quit(status = 0)
}

fit <- tryCatch(
  netmeta(TE = cmp$logOR, seTE = cmp$seLogOR, treat1 = cmp$t1, treat2 = cmp$t2,
          studlab = cmp$studlab, sm = "OR", common = FALSE, random = TRUE,
          reference.group = dat$reference %||% NULL),
  error = function(e) list(caught_message = conditionMessage(e))
)

if (is.list(fit) && !is.null(fit$caught_message)) {
  writeLines(toJSON(list(
    review = dat$review, fit_ok = FALSE,
    engine = "R-netmeta",
    netmeta_version = as.character(packageVersion("netmeta")),
    k_comparisons = k,
    connected = TRUE,
    error = paste0("netmeta() error: ", fit$caught_message)
  ), auto_unbox = TRUE, pretty = TRUE), output_path)
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
  connected = TRUE,
  n_zero_cell_corrected = as.integer(zero_count),
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
