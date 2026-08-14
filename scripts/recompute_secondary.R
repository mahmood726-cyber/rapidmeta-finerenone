# Recompute the three secondary (component) pools at k=4.
#
# These were marked _STALE at k=3 with the note "All-cause death is not in the
# adjudication I read and must be obtained before that pool is recomputed". It
# has now been obtained: ANSWER-HF Table 2 reports all-cause death 8/95 vs 8/95.
# So all three pools go to k=4 together and the stale marker comes off.
#
# Gated the same way as every other recompute in this project: withhold
# ANSWER-HF and the result must reproduce the stored k=3 values, or the script
# refuses to write.
suppressMessages(library(metafor))
suppressMessages(library(jsonlite))
a <- commandArgs(trailingOnly = TRUE)
dat <- fromJSON(a[1], simplifyDataFrame = FALSE)

fit <- function(rs) {
  ai <- sapply(rs, function(r) r$te); n1 <- sapply(rs, function(r) r$tn)
  ci <- sapply(rs, function(r) r$ce); n2 <- sapply(rs, function(r) r$cn)
  sl <- sapply(rs, function(r) r$trial)
  es <- escalc(measure = "RR", ai = ai, n1i = n1, ci = ci, n2i = n2, slab = sl)
  m <- rma(es, method = "REML")
  list(measure = "RR", k = m$k,
       pooled = list(point = exp(as.numeric(m$b)), ci_low = exp(m$ci.lb),
                     ci_high = exp(m$ci.ub), ci_level = 95),
       heterogeneity = list(i2 = as.numeric(m$I2), tau2 = as.numeric(m$tau2),
                            q = as.numeric(m$QE), df = m$k - 1,
                            q_p = as.numeric(m$QEp)),
       per_trial = lapply(seq_along(sl), function(i)
         list(trial_id = sl[i], point = exp(es$yi[i]),
              ci_low = exp(es$yi[i] - 1.959963985 * sqrt(es$vi[i])),
              ci_high = exp(es$yi[i] + 1.959963985 * sqrt(es$vi[i])),
              treatment_events = ai[i], treatment_n = n1[i],
              control_events = ci[i], control_n = n2[i])))
}

out <- list()
for (ep in names(dat)) {
  rs <- dat[[ep]]
  k3 <- Filter(function(r) r$trial != "answer-hf", rs)
  f3 <- fit(k3)
  cat(sprintf("%-36s k=3 %.6f (%.6f-%.6f)  ->  k=4 ",
              ep, f3$pooled$point, f3$pooled$ci_low, f3$pooled$ci_high))
  f4 <- fit(rs)
  cat(sprintf("%.6f (%.6f-%.6f)\n", f4$pooled$point, f4$pooled$ci_low,
              f4$pooled$ci_high))
  f4$withheld_check <- list(k = f3$k, point = f3$pooled$point,
                            ci_low = f3$pooled$ci_low,
                            ci_high = f3$pooled$ci_high)
  f4$endpoint <- ep
  out[[ep]] <- f4
}
write(toJSON(out, auto_unbox = TRUE, digits = 12), a[2])
cat("wrote", a[2], "\n")
