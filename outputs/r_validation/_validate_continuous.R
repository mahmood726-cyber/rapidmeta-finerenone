
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

# Generic precomputed-yi/vi pool: yi = mean difference, vi = se^2
dat$vi <- dat$se ^ 2
res <- tryCatch(
  metafor::rma(yi = dat$md, vi = dat$vi, method = "REML", test = "knha"),
  error = function(e) NULL
)
if (is.null(res)) {
  res <- tryCatch(
    metafor::rma(yi = dat$md, vi = dat$vi, method = "DL", test = "knha"),
    error = function(e) NULL
  )
}
if (is.null(res)) {
  jsonlite::write_json(list(error = "rma_failed", k = k), json_out, auto_unbox = TRUE)
  quit(status = 0)
}

# HKSJ floor flag
Q <- as.numeric(res$QE); df <- k - 1
hksj_floor_applied <- (Q < df)

# PI: t_{k-1} convention
tau2 <- as.numeric(res$tau2)
se_b <- as.numeric(res$se)
b <- as.numeric(res$b)
tcrit <- qt(0.975, df = max(1, k - 1))
pi_se <- sqrt(tau2 + se_b^2)
PI_low <- b - tcrit * pi_se
PI_high <- b + tcrit * pi_se

ci_low <- as.numeric(res$ci.lb)
ci_high <- as.numeric(res$ci.ub)

out <- list(
  k = k,
  effect_type = "MD",
  pooled_MD = b,
  pooled_se = se_b,
  ci_low_MD = ci_low,
  ci_high_MD = ci_high,
  tau2 = tau2,
  I2 = as.numeric(res$I2),
  H2 = as.numeric(res$H2),
  Q = Q, Qdf = df, Qp = as.numeric(res$QEp),
  PI_low_MD = PI_low,
  PI_high_MD = PI_high,
  pi_df_convention = "t_{k-1}_Cochrane_v6.5",
  hksj_floor_applied = hksj_floor_applied,
  method = paste0(res$method, "+HKSJ+continuous"),
  trials = lapply(seq_len(k), function(i) list(
    name = dat$name[i], nct = dat$nct[i],
    md = dat$md[i], se = dat$se[i]
  ))
)
jsonlite::write_json(out, json_out, auto_unbox = TRUE, pretty = TRUE, digits = 6)
