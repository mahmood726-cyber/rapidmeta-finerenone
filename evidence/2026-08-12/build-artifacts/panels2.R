suppressMessages({library(metafor); library(jsonlite)})
a <- commandArgs(TRUE)
d <- fromJSON(a[1], simplifyVector = FALSE); oid <- a[2]
tr <- d$inputs$trials
nm <- sapply(tr, function(t) t$id)
ai <- sapply(tr, function(t) t$by_outcome[[oid]]$treatment$events)
n1 <- sapply(tr, function(t) t$by_outcome[[oid]]$treatment$n)
ci <- sapply(tr, function(t) t$by_outcome[[oid]]$control$events)
n2 <- sapply(tr, function(t) t$by_outcome[[oid]]$control$n)
bi <- n1 - ai; di <- n2 - ci
out <- list()

fit <- function(meas, method = "REML") {
  es <- escalc(measure = meas, ai = ai, bi = bi, ci = ci, di = di)
  m  <- rma(es, method = method)
  list(m = m, es = es)
}

for (meas in c("RR", "OR", "RD")) {
  f <- fit(meas)
  m <- f$m
  bt <- if (meas == "RD") identity else exp
  out[[tolower(meas)]] <- list(
    measure = meas, k = m$k,
    point = as.numeric(bt(m$b)), ci_low = bt(m$ci.lb), ci_high = bt(m$ci.ub),
    tau2 = m$tau2, I2 = m$I2, Q = m$QE, Qdf = m$k - 1, Qp = m$QEp,
    per_trial = lapply(seq_along(nm), function(i) {
      yi <- f$es$yi[i]; vi <- f$es$vi[i]
      list(trial = nm[i], point = as.numeric(bt(yi)),
           ci_low = as.numeric(bt(yi - 1.96 * sqrt(vi))),
           ci_high = as.numeric(bt(yi + 1.96 * sqrt(vi))))
    }))
}

# baseline risk and L'Abbe coordinates -- read straight off the 2x2
out$labbe <- lapply(seq_along(nm), function(i)
  list(trial = nm[i], control_risk = ci[i] / n2[i],
       treatment_risk = ai[i] / n1[i], n = n1[i] + n2[i]))
out$baseline_risk <- lapply(seq_along(nm), function(i)
  list(trial = nm[i], control_events = ci[i], control_n = n2[i],
       control_risk = ci[i] / n2[i]))

# risk difference table + NNT (from the pooled RD only, never from a ratio)
rd <- out$rd
out$nnt <- list(
  pooled_rd = rd$point, rd_ci_low = rd$ci_low, rd_ci_high = rd$ci_high,
  nnt = if (rd$ci_low < 0 && rd$ci_high > 0) NA else abs(1 / rd$point),
  nnt_low = if (rd$ci_low < 0 && rd$ci_high > 0) NA else abs(1 / rd$ci_high),
  nnt_high = if (rd$ci_low < 0 && rd$ci_high > 0) NA else abs(1 / rd$ci_low),
  undefined_because = if (rd$ci_low < 0 && rd$ci_high > 0)
    paste("The pooled risk-difference interval crosses zero, so the number",
          "needed to treat is not defined: the same interval would give a",
          "number needed to treat and a number needed to harm. Nothing is",
          "printed in its place.") else NULL)

# NNT curve across plausible control risks, from the pooled RR
rr <- out$rr$point
out$nnt_curve <- lapply(seq(0.05, 0.60, by = 0.025), function(cr)
  list(control_risk = cr, nnt = 1 / abs(cr - cr * rr)))

# Peters' test -- the recommended small-study test for binary outcomes
es <- escalc(measure = "OR", ai = ai, bi = bi, ci = ci, di = di)
pt <- try(regtest(rma(es, method = "REML"), model = "lm",
                  predictor = "ni"), silent = TRUE)
out$peters <- if (inherits(pt, "try-error"))
  list(estimable = FALSE) else
  list(estimable = TRUE, intercept = as.numeric(pt$est),
       z = as.numeric(pt$zval), p = as.numeric(pt$pval),
       note = paste("Peters 2006 regresses the log odds ratio on the inverse",
                    "of total sample size, which the Cochrane Handbook v6.5",
                    "section 13.3.5 recommends for binary outcomes in place of",
                    "Egger, whose test is biased on the odds-ratio scale. With",
                    "k =", length(ai), "it still has almost no power and is",
                    "reported as a computed value, not as evidence."))

# Benford first-digit screen over the event counts as READ
digs <- as.integer(substr(as.character(c(ai, ci)), 1, 1))
obs <- sapply(1:9, function(x) sum(digs == x))
exp9 <- log10(1 + 1 / (1:9)) * length(digs)
out$benford <- list(
  n_counts = length(digs),
  observed = as.list(obs), expected = as.list(round(exp9, 4)),
  note = paste("First-digit screen over the", length(digs), "event counts as",
               "read. With this few integers the comparison is descriptive",
               "only -- Benford's law is a large-sample regularity and no",
               "test statistic is computed here."))

cat(toJSON(out, auto_unbox = TRUE, digits = 10, na = "null"))
