# Capture VERBATIM R output for every result this review reports.
#
# Why this is the validity layer and not decoration: a bare number on a page can
# only be checked against the object that produced it, and the object is ours. A
# quoted metafor call carries its own k, its own estimator, its own heterogeneity
# and its own package version, so a reader can see the provenance of the number
# without trusting us. It would have made last night's worst defect visible on
# sight -- a printed `k = 4` sitting under a leave-one-out panel drawn from three
# studies is obvious where a bare 0.839 is not.
#
# capture.output() on the print method, not a reconstruction: anything re-typed
# here would be exactly the re-typing this is meant to prevent.
suppressMessages(library(metafor))
suppressMessages(library(jsonlite))

a <- commandArgs(trailingOnly = TRUE)
dat <- fromJSON(a[1], simplifyDataFrame = FALSE)

yi   <- sapply(dat$trials, function(t) t$log_point)
sei  <- sapply(dat$trials, function(t) t$log_se)
slab <- sapply(dat$trials, function(t) t$id)
ai <- sapply(dat$counts, function(t) t$te); n1 <- sapply(dat$counts, function(t) t$tn)
ci <- sapply(dat$counts, function(t) t$ce); n2 <- sapply(dat$counts, function(t) t$cn)
cslab <- sapply(dat$counts, function(t) t$id)

env <- paste0(R.version.string, "; metafor ", as.character(packageVersion("metafor")))
grab <- function(expr) paste(capture.output(expr), collapse = "\n")

out <- list()

m <- rma(yi = yi, sei = sei, method = "REML", slab = slab, level = 95)
out[["primary_pooled"]] <- list(
  label = "Primary pooled hazard ratio, random-effects REML on the log scale",
  call  = 'rma(yi = log_hr, sei = log_se, method = "REML", level = 95)',
  output = grab(print(m)),
  back_transformed = grab(print(predict(m, transf = exp))),
  environment = env)

out[["prediction_interval"]] <- list(
  label = "Prediction interval for a future study",
  call = "predict(m, transf = exp)",
  output = grab(print(predict(m, transf = exp))), environment = env)

out[["tau2_ci"]] <- list(
  label = "Confidence interval for tau-squared, Q-profile",
  call = "confint(m)", output = grab(print(confint(m))), environment = env)

out[["eggers"]] <- list(
  label = "Egger's regression test for funnel asymmetry",
  call = 'regtest(m, model = "lm")',
  output = grab(print(regtest(m, model = "lm"))), environment = env)

out[["leave_one_out"]] <- list(
  label = "Leave-one-out refits",
  call = "leave1out(m)", output = grab(print(leave1out(m))), environment = env)

out[["cumulative"]] <- list(
  label = "Cumulative meta-analysis in year order",
  call = "cumul(m)", output = grab(print(cumul(m))), environment = env)

out[["influence"]] <- list(
  label = "Influence diagnostics",
  call = "influence(m)", output = grab(print(influence(m))), environment = env)

for (meas in c("RR", "OR", "RD")) {
  es <- escalc(measure = meas, ai = ai, n1i = n1, ci = ci, n2i = n2, slab = cslab)
  mm <- rma(es, method = "REML")
  out[[paste0("count_", tolower(meas))]] <- list(
    label = paste0("Count-based pool on the ", meas, " scale (secondary estimand)"),
    call = paste0('escalc(measure = "', meas,
                  '", ai, n1i, ci, n2i); rma(method = "REML")'),
    output = grab(print(mm)), environment = env)
}

for (est in c("REML", "DL", "PM")) {
  mm <- rma(yi = yi, sei = sei, method = est, slab = slab)
  mh <- rma(yi = yi, sei = sei, method = est, slab = slab, test = "knha")
  out[[paste0("estimator_", tolower(est))]] <- list(
    label = paste0("Between-study variance estimator ", est,
                   ", Wald and Hartung-Knapp intervals"),
    call = paste0('rma(yi, sei, method = "', est, '")  and  ... test = "knha"'),
    output = paste(grab(print(mm)), "", "## Hartung-Knapp-Sidik-Jonkman:", "",
                   grab(print(mh)), sep = "\n"),
    environment = env)
}

write(toJSON(out, auto_unbox = TRUE), a[2])
cat("captured", length(out), "verbatim R outputs\n")
