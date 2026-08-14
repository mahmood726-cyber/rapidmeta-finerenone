# Recompute the count-based panels at k=4 with metafor.
#
# These were marked _STALE on the grounds that recomputing needed 2x2 counts I
# did not want to invent overnight. That was over-cautious and wrong: ANSWER-HF
# carries per-arm counts for this composite (12/95 against 8/95) in the object
# already, so the risk ratio, odds ratio, risk difference, L'Abbe and baseline
# risk are all computable at k=4. A panel that CAN be computed and is shown at
# the wrong k is a worse outcome than one honestly declared stale.
#
# The L'Abbe point matters for a second reason: it was rendering three points
# beside a four-trial forest, which is exactly the visible inconsistency the
# k gate exists to catch.
suppressMessages(library(metafor))
suppressMessages(library(jsonlite))

a <- commandArgs(trailingOnly = TRUE)
dat <- fromJSON(a[1], simplifyDataFrame = FALSE)
ai <- sapply(dat$trials, function(t) t$te)     # treatment events
n1 <- sapply(dat$trials, function(t) t$tn)
ci <- sapply(dat$trials, function(t) t$ce)     # control events
n2 <- sapply(dat$trials, function(t) t$cn)
slab <- sapply(dat$trials, function(t) t$id)

mk <- function(meas) {
  es <- escalc(measure = meas, ai = ai, n1i = n1, ci = ci, n2i = n2, slab = slab)
  m <- rma(es, method = "REML")
  back <- if (meas == "RD") identity else exp
  list(measure = meas, k = m$k,
       point = back(as.numeric(m$b)), ci_low = back(m$ci.lb),
       ci_high = back(m$ci.ub), tau2 = as.numeric(m$tau2),
       I2 = as.numeric(m$I2), Q = as.numeric(m$QE), Qdf = m$k - 1,
       Qp = as.numeric(m$QEp),
       per_trial = lapply(seq_along(slab), function(i)
         list(trial = slab[i], point = back(es$yi[i]),
              ci_low = back(es$yi[i] - 1.959963985 * sqrt(es$vi[i])),
              ci_high = back(es$yi[i] + 1.959963985 * sqrt(es$vi[i])))))
}

rr <- mk("RR"); or <- mk("OR"); rd <- mk("RD")

labbe <- lapply(seq_along(slab), function(i)
  list(trial = slab[i], control_risk = ci[i] / n2[i],
       treatment_risk = ai[i] / n1[i], n = n1[i] + n2[i]))
baseline <- lapply(seq_along(slab), function(i)
  list(trial = slab[i], control_events = ci[i], control_n = n2[i],
       control_risk = ci[i] / n2[i]))

# NNT across a range of assumed control risks, from the POOLED risk ratio.
rrp <- rr$point
cr <- seq(0.05, 0.60, by = 0.025)
nnt <- lapply(cr, function(p0) list(control_risk = p0,
                                    nnt = 1 / (p0 - p0 * rrp)))

write(toJSON(list(rr = rr, or = or, rd = rd, labbe = labbe,
                  baseline_risk = baseline, nnt_curve = nnt),
             auto_unbox = TRUE, digits = 12), a[2])
cat("k =", rr$k, " RR =", rr$point, "(", rr$ci_low, "-", rr$ci_high, ")\n")
cat("wrote", a[2], "\n")
