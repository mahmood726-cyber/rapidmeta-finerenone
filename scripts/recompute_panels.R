# Recompute the ARNI analysis panels at k=4 with the SAME toolchain the object's
# _provenance already names (metafor 5.0.1, R 4.6.0, REML on the log scale).
#
# The panels block -- including its own `fit` -- was still the k=3 analysis while
# the headline pooled result is k=4. Every number below is metafor's, not a
# hand-derivation: leave1out(), cumul(), influence(), regtest(), predict() and
# confint() are called directly so the panels agree with the pool by construction.
#
# THE VALIDATION THAT MAKES THIS TRUSTWORTHY: the recomputed k=4 fit is compared
# against the pooled result ALREADY STORED in the object. If they disagree, this
# script refuses to write. A pipeline that cannot reproduce the number the object
# already holds has no business producing the nine panels derived from it.
suppressMessages(library(metafor))
suppressMessages(library(jsonlite))

a <- commandArgs(trailingOnly = TRUE)
dat <- fromJSON(a[1], simplifyDataFrame = FALSE)

yi <- sapply(dat$trials, function(t) t$log_point)
sei <- sapply(dat$trials, function(t) t$log_se)
slab <- sapply(dat$trials, function(t) t$id)
yr <- sapply(dat$trials, function(t) t$year)

m <- rma(yi = yi, sei = sei, method = "REML", slab = slab, level = 95)

# ---- gate: does this reproduce the pool the object already stores? -----------
got <- c(exp(as.numeric(m$b)), exp(m$ci.lb), exp(m$ci.ub),
         as.numeric(m$tau2), as.numeric(m$I2), as.numeric(m$QE))
want <- c(dat$expect$point, dat$expect$ci_low, dat$expect$ci_high,
          dat$expect$tau2, dat$expect$i2, dat$expect$q)
dif <- abs(got - want)
tol <- pmax(1e-4, abs(want) * 1e-4)
cat("fit reproduction check\n")
for (i in seq_along(got)) {
  cat(sprintf("  %-10s got=%.8f want=%.8f diff=%.2e %s\n",
              c("point","ci_low","ci_high","tau2","I2","Q")[i],
              got[i], want[i], dif[i], ifelse(dif[i] <= tol[i], "OK", "MISMATCH")))
}
if (any(dif > tol)) {
  stop("REFUSED: recomputed k=4 fit does not reproduce the stored pooled result")
}

r3 <- function(x) as.numeric(x)

fit <- list(k = m$k, point = exp(as.numeric(m$b)), ci_low = exp(m$ci.lb),
            ci_high = exp(m$ci.ub), log_point = as.numeric(m$b),
            log_se = as.numeric(m$se), tau2 = as.numeric(m$tau2),
            I2 = as.numeric(m$I2), H2 = as.numeric(m$H2),
            Q = as.numeric(m$QE), Qdf = m$k - 1, Qp = as.numeric(m$QEp))

l1 <- leave1out(m)
loo <- lapply(seq_along(slab), function(i)
  list(omitted = slab[i], point = exp(l1$estimate[i]), ci_low = exp(l1$ci.lb[i]),
       ci_high = exp(l1$ci.ub[i]), I2 = r3(l1$I2[i]), Q = r3(l1$Q[i])))

o <- order(yr, slab)
cm <- cumul(rma(yi = yi[o], sei = sei[o], method = "REML", slab = slab[o]))
cum <- lapply(seq_along(o), function(i)
  list(through = slab[o][i], year = yr[o][i], k = i, point = exp(cm$estimate[i]),
       ci_low = exp(cm$ci.lb[i]), ci_high = exp(cm$ci.ub[i])))

inf <- influence(m)
infl <- lapply(seq_along(slab), function(i)
  list(trial = slab[i], rstudent = r3(inf$inf$rstudent[i]),
       dffits = r3(inf$inf$dffits[i]), cook_d = r3(inf$inf$cook.d[i]),
       hat = r3(inf$inf$hat[i]), weight = r3(inf$inf$weight[i]),
       influential = isTRUE(as.logical(inf$is.infl[i]))))

# metafor's own baujat(), not a hand-derivation from QE.del. The x axis is each
# study's contribution to overall heterogeneity and the y its influence on the
# pooled estimate; deriving those by subtraction invites a sign or scaling error
# that would look plausible on a scatter plot and be wrong.
bjd <- baujat(m, plot = FALSE)
bj <- lapply(seq_along(slab), function(i)
  list(trial = slab[i], q_contribution = r3(bjd$x[i]), pooled_influence = r3(bjd$y[i])))

zi <- yi / sei
gal <- lapply(seq_along(slab), function(i)
  list(trial = slab[i], precision = 1 / sei[i], z = zi[i]))

fun <- lapply(seq_along(slab), function(i)
  list(trial = slab[i], log_effect = yi[i], se = sei[i]))

eg <- tryCatch({
  rt <- regtest(m, model = "lm")
  # rt$se is absent on this call in metafor 5.x, so the stored object carried
  # `"se": []` -- an empty list where a standard error belongs, which renders as
  # nothing and reads as "not applicable" rather than "we failed to read it".
  # Recovered from the fitted model's own coefficient table.
  sefit <- tryCatch(as.numeric(coef(summary(rt$fit))[2, 2]), error = function(e) NA_real_)
  if (is.na(sefit) && is.finite(rt$zval) && rt$zval != 0)
    sefit <- abs(as.numeric(rt$est) / as.numeric(rt$zval))
  list(estimable = TRUE, intercept = as.numeric(rt$est), se = sefit,
       z = as.numeric(rt$zval), p = as.numeric(rt$pval))
}, error = function(e) list(estimable = FALSE, why = conditionMessage(e)))

pr <- predict(m)
pred <- list(pi_low = exp(pr$pi.lb), pi_high = exp(pr$pi.ub))
tc <- tryCatch({
  ci <- confint(m)
  list(estimate = as.numeric(m$tau2), ci_low = ci$random[1, 2], ci_high = ci$random[1, 3])
}, error = function(e) NULL)

write(toJSON(list(fit = fit, leave_one_out = loo, cumulative = cum,
                  influence = infl, baujat = bj, galbraith = gal, funnel = fun,
                  egger = eg, prediction = pred, tau2_ci = tc),
             auto_unbox = TRUE, digits = 12, null = "null"), a[2])
cat("wrote", a[2], "\n")
