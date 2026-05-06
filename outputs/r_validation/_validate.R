
suppressPackageStartupMessages({ library(metafor); library(jsonlite) })

args <- commandArgs(trailingOnly = TRUE)
csv_in <- args[1]
json_out <- args[2]

dat <- read.csv(csv_in, stringsAsFactors = FALSE)
k <- nrow(dat)

if (k < 2) {
  jsonlite::write_json(list(error = "k<2", k = k), json_out, auto_unbox = TRUE)
  quit(status = 0)
}

# escalc — log OR with continuity correction only when needed
es <- tryCatch(
  metafor::escalc(measure = "OR",
                  ai = tE, n1i = tN, ci = cE, n2i = cN,
                  data = dat, to = "only0", add = 0.5,
                  drop00 = FALSE),
  error = function(e) NULL
)
if (is.null(es) || all(is.na(es$yi))) {
  jsonlite::write_json(list(error = "escalc_failed", k = k), json_out, auto_unbox = TRUE)
  quit(status = 0)
}

# REML + HKSJ
res <- tryCatch(
  metafor::rma(yi = es$yi, vi = es$vi, method = "REML", test = "knha"),
  error = function(e) NULL
)
if (is.null(res)) {
  # Fallback DL if REML fails
  res <- tryCatch(
    metafor::rma(yi = es$yi, vi = es$vi, method = "DL", test = "knha"),
    error = function(e) NULL
  )
}
if (is.null(res)) {
  jsonlite::write_json(list(error = "rma_failed", k = k), json_out, auto_unbox = TRUE)
  quit(status = 0)
}

# HKSJ floor: max(1, Q/(k-1)) — metafor handles HKSJ but not the floor;
# we report whether floor would have applied.
Q <- as.numeric(res$QE)
df <- k - 1
phi <- max(1, Q / df)
hksj_floor_applied <- (Q < df)

# Prediction interval (Cochrane v6.5 t_{k-1}): pred() default in metafor uses k-2
# We compute t_{k-1} convention manually for repro alignment:
tau2 <- as.numeric(res$tau2)
se_b <- as.numeric(res$se)
b <- as.numeric(res$b)
tcrit <- qt(0.975, df = max(1, k - 1))
pi_se <- sqrt(tau2 + se_b^2)
PI_low <- b - tcrit * pi_se
PI_high <- b + tcrit * pi_se

# CI from rma (already HKSJ when test="knha")
ci_low <- as.numeric(res$ci.lb)
ci_high <- as.numeric(res$ci.ub)

out <- list(
  k = k,
  pooled_logOR = b,
  pooled_se = se_b,
  pooled_OR = exp(b),
  ci_low_OR = exp(ci_low),
  ci_high_OR = exp(ci_high),
  tau2 = tau2,
  I2 = as.numeric(res$I2),
  H2 = as.numeric(res$H2),
  Q = Q,
  Qdf = df,
  Qp = as.numeric(res$QEp),
  PI_low_OR = exp(PI_low),
  PI_high_OR = exp(PI_high),
  pi_df_convention = "t_{k-1}_Cochrane_v6.5",
  hksj_floor_applied = hksj_floor_applied,
  method = paste0(res$method, "+HKSJ"),
  trials = lapply(seq_len(k), function(i) list(
    name = dat$name[i],
    nct = dat$nct[i],
    tE = dat$tE[i], tN = dat$tN[i],
    cE = dat$cE[i], cN = dat$cN[i],
    yi = es$yi[i], vi = es$vi[i]
  ))
)
jsonlite::write_json(out, json_out, auto_unbox = TRUE, pretty = TRUE, digits = 6)
