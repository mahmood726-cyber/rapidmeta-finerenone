suppressMessages({library(metafor); library(jsonlite)})
a <- commandArgs(TRUE)
d  <- fromJSON(a[1], simplifyVector = FALSE)
oid <- a[2]
pt <- d$results$by_outcome[[oid]]$per_trial
yi  <- sapply(pt, function(x) x$log_point)
sei <- sapply(pt, function(x) x$log_se)
nm  <- sapply(pt, function(x) x$trial_id)
yr  <- sapply(seq_along(pt), function(i){
  t <- d$inputs$trials[[i]]; if (is.null(t$year)) NA else t$year })

m <- rma(yi = yi, sei = sei, method = "REML")
out <- list()

out$fit <- list(k = m$k, point = exp(as.numeric(m$b)),
                ci_low = exp(m$ci.lb), ci_high = exp(m$ci.ub),
                log_point = as.numeric(m$b), log_se = m$se,
                tau2 = m$tau2, I2 = m$I2, H2 = m$H2,
                Q = m$QE, Qdf = m$k - 1, Qp = m$QEp)

# prediction interval
pr <- predict(m)
out$prediction <- list(pi_low = exp(pr$pi.lb), pi_high = exp(pr$pi.ub),
                       convention = "t_{k-1}, Cochrane Handbook v6.5")

# tau2 Q-profile CI
cf <- try(confint(m), silent = TRUE)
if (!inherits(cf, "try-error"))
  out$tau2_ci <- list(estimate = cf$random[1, 1],
                      ci_low = cf$random[1, 2], ci_high = cf$random[1, 3],
                      method = "Q-profile (Viechtbauer 2007)")

# leave-one-out
l1 <- leave1out(m)
out$leave_one_out <- lapply(seq_along(nm), function(i)
  list(omitted = nm[i], point = exp(l1$estimate[i]),
       ci_low = exp(l1$ci.lb[i]), ci_high = exp(l1$ci.ub[i]),
       I2 = l1$I2[i], Q = l1$Q[i]))

# influence diagnostics
inf <- influence(m)
out$influence <- lapply(seq_along(nm), function(i)
  list(trial = nm[i], rstudent = inf$inf$rstudent[i],
       dffits = inf$inf$dffits[i], cook_d = inf$inf$cook.d[i],
       hat = inf$inf$hat[i], weight = inf$inf$weight[i],
       influential = isTRUE(inf$is.infl[i])))

# baujat
pdf(NULL); bj <- baujat(m); invisible(dev.off())
out$baujat <- lapply(seq_along(nm), function(i)
  list(trial = nm[i], q_contribution = bj$x[i], pooled_influence = bj$y[i]))

# cumulative by year
ord <- order(yr)
cm <- cumul(m, order = ord)
out$cumulative <- lapply(seq_along(ord), function(i)
  list(through = nm[ord][i], year = yr[ord][i], k = i,
       point = exp(cm$estimate[i]), ci_low = exp(cm$ci.lb[i]),
       ci_high = exp(cm$ci.ub[i])))

# radial / Galbraith coordinates
out$galbraith <- lapply(seq_along(nm), function(i)
  list(trial = nm[i], precision = 1 / sei[i], z = yi[i] / sei[i]))

# funnel coordinates
out$funnel <- lapply(seq_along(nm), function(i)
  list(trial = nm[i], log_effect = yi[i], se = sei[i]))

# Egger / regtest -- run it, and record what it says at this k
rt <- try(regtest(m, model = "lm"), silent = TRUE)
if (inherits(rt, "try-error")) {
  out$egger <- list(estimable = FALSE, reason = "regtest failed at this k")
} else {
  out$egger <- list(estimable = TRUE, intercept = as.numeric(rt$est),
    se = as.numeric(rt$se), z = as.numeric(rt$zval), p = as.numeric(rt$pval),
    caution = paste("Run for completeness. With k =", m$k,
      "the test has almost no power and the Cochrane Handbook advises against",
      "interpreting it below about ten studies. Reported as a computed value,",
      "NOT as evidence about small-study effects."))
}

# Bayesian: grid over mu and tau (half-Cauchy(1) on tau, flat on mu)
mus  <- seq(min(yi) - 1.5, max(yi) + 1.5, length.out = 201)
taus <- seq(1e-4, 2, length.out = 201)
lg <- outer(mus, taus, Vectorize(function(mu, tau)
  sum(dnorm(yi, mu, sqrt(sei^2 + tau^2), log = TRUE)) +
    dcauchy(tau, 0, 1, log = TRUE) + log(2)))
w <- exp(lg - max(lg)); w <- w / sum(w)
pm <- rowSums(w)                       # marginal posterior of mu
cdf <- cumsum(pm)
q <- function(p) mus[which.min(abs(cdf - p))]
out$bayes <- list(
  method = paste("grid integration, 201x201, flat prior on the pooled log",
                 "effect and half-Cauchy(scale=1) on the between-study SD",
                 "(Gelman 2006)"),
  posterior_median = exp(q(0.5)), cri_low = exp(q(0.025)),
  cri_high = exp(q(0.975)),
  density = lapply(seq(1, length(mus), by = 4), function(i)
    list(x = exp(mus[i]), d = pm[i])))

cat(toJSON(out, auto_unbox = TRUE, digits = 10, na = "null"))
