# sotagliflozin-hf: the two pools this review publishes, fitted and quoted.
#
# WHY THIS EXISTS. P46 asks the object to hold the model output QUOTED VERBATIM, and this
# object holds neither the output nor a reason for its absence. That is a BLANK, not a
# refusal, and a blank is the one thing P46 does not accept -- so it is produced rather
# than explained, because it CAN be produced: both pools' per-trial hazard ratios are on
# the object with their log points and log standard errors, R 4.6.0 and metafor 5.0.1 are
# installed, and the pools are already declared REML.
#
# THE CHECK COMES BEFORE THE QUOTE. Each pool is refitted from the object's OWN recorded
# per-trial values and compared with the estimate the page serves. If a fit does not
# reproduce the served number, THE QUOTE WOULD BE OF A DIFFERENT MODEL THAN THE ONE THAT
# PRODUCED THE PAGE, and this script refuses rather than writing it. Twice already in this
# project a fresh computation that felt more trustworthy than a stored one was the thing
# that was wrong.
#
# PREDICTION, STATED BEFORE THE RUN so the run can contradict it:
#   * Both pools reproduce point and interval to four decimals under REML with a z
#     interval, because both are declared REML and neither carries a Hartung-Knapp label.
#   * Both return tau^2 = 0: Q is 0.4296 and 0.8841 on 1 degree of freedom, both below it.
#   * The two pools are NOT independent estimates of one thing. hfcv_total counts TOTAL
#     events and hfcv_first counts FIRST events on the same trials, so the total-event
#     pool must be at least as far from 1 as the first-event pool. If that ordering came
#     out reversed it would mean the two estimands had been crossed, and it is checked.
#
# The indicator that can only move if the reading is right is the reproduction of the
# SERVED interval, not just the point: at k=2 many specifications give the same point.

suppressMessages(library(metafor))
suppressMessages(library(jsonlite))

args <- commandArgs(trailingOnly = TRUE)
outp <- if (length(args) >= 1) args[1] else "sotagliflozin_fits.json"

cat("R environment, quoted rather than asserted:\n")
cat(" ", R.version.string, "\n")
cat("  metafor", as.character(packageVersion("metafor")), "\n\n")

pools <- list(
  hfcv_total = list(
    label = "Total events: cardiovascular death, hospitalisation for heart failure, or urgent heart-failure visit -- ALL occurrences, not only the first",
    slab = c("SOLOIST-WHF (NCT03521934)", "SCORED (NCT03315143)"),
    yi = c(-0.400478, -0.301105),
    sei = c(0.125361, 0.085257),
    served = c(point = 0.7171, lo = 0.6246, hi = 0.8234),
    het = c(tau2 = 0.0, i2 = 0.0, q = 0.4296)),
  hfcv_first = list(
    label = "First event only: the first occurrence of cardiovascular death, hospitalisation for heart failure, or urgent heart-failure visit",
    slab = c("SOLOIST-WHF (NCT03521934)", "SCORED (NCT03315143)"),
    yi = c(-0.371064, -0.248461),
    sei = c(0.106456, 0.075286),
    served = c(point = 0.7488, lo = 0.6638, hi = 0.8446),
    het = c(tau2 = 0.0, i2 = 0.0, q = 0.8841)))

fits <- list()
n_ok <- 0L
for (key in names(pools)) {
  p <- pools[[key]]
  cat(strrep("=", 92), "\n")
  cat(sprintf("%s :: %s   k = %d   measure = HR\n", "sotagliflozin-hf", key, length(p$yi)))
  cat(strrep("=", 92), "\n")
  cat("what is counted:", p$label, "\n")
  cat("trials:", paste(p$slab, collapse = ", "), "\n\n")

  fit <- rma(yi = p$yi, sei = p$sei, method = "REML", slab = p$slab)
  print(fit)
  pr <- predict(fit, transf = exp)
  cat("\nBack-transformed to the hazard-ratio scale:\n")
  print(pr)

  cat("\nCHECK AGAINST THE VALUE THE PAGE SERVES -- the quote is not earned until this passes:\n")
  ok_pt <- abs(pr$pred - p$served[["point"]]) < 5e-4
  ok_lo <- abs(pr$ci.lb - p$served[["lo"]]) < 5e-4
  ok_hi <- abs(pr$ci.ub - p$served[["hi"]]) < 5e-4
  ok_tau <- abs(fit$tau2 - p$het[["tau2"]]) < 5e-5
  ok_q <- abs(fit$QE - p$het[["q"]]) < 5e-4
  ok_i2 <- abs(fit$I2 - p$het[["i2"]]) < 0.15
  cat(sprintf("  point   refit %-10.4f served %-10.4f  %s\n", pr$pred, p$served[["point"]],
              ifelse(ok_pt, "reproduced", "DIFFERS")))
  cat(sprintf("  ci_low  refit %-10.4f served %-10.4f  %s\n", pr$ci.lb, p$served[["lo"]],
              ifelse(ok_lo, "reproduced", "DIFFERS")))
  cat(sprintf("  ci_high refit %-10.4f served %-10.4f  %s\n", pr$ci.ub, p$served[["hi"]],
              ifelse(ok_hi, "reproduced", "DIFFERS")))
  cat(sprintf("  tau^2   refit %-10.6f stored %-10.6f  %s\n", fit$tau2, p$het[["tau2"]],
              ifelse(ok_tau, "reproduced", "DIFFERS")))
  cat(sprintf("  Q       refit %-10.4f stored %-10.4f  %s\n", fit$QE, p$het[["q"]],
              ifelse(ok_q, "reproduced", "DIFFERS")))
  cat(sprintf("  I^2     refit %-10.2f stored %-10.2f  %s\n", fit$I2, p$het[["i2"]],
              ifelse(ok_i2, "reproduced", "DIFFERS")))
  all_ok <- ok_pt && ok_lo && ok_hi && ok_tau && ok_q && ok_i2
  cat(sprintf("  => %s\n", ifelse(all_ok, "REPRODUCED -- this fit is the one that produced the page",
                                  "NOT REPRODUCED -- do not quote this as the served model")))
  if (!all_ok) {
    stop("REFUSED on ", key, ": the refit does not reproduce the served estimate, so ",
         "quoting it would attribute the page to a model that did not produce it.")
  }
  n_ok <- n_ok + 1L

  cat(sprintf("\nPrediction interval: %.4f to %.4f\n", pr$pi.lb, pr$pi.ub))
  cat("  AT k = 2 A PREDICTION INTERVAL IS EXTREMELY WEAKLY DETERMINED. It is reported\n")
  cat("  because it was computed, not because it is informative.\n")

  hk <- rma(yi = p$yi, sei = p$sei, method = "REML", test = "knha", slab = p$slab)
  scale <- (hk$se / fit$se)^2
  se_used <- if (scale < 1) fit$se else hk$se
  half <- qt(0.975, df = fit$k - 1) * se_used
  cat(sprintf("\nHartung-Knapp sensitivity at k <= 3, per Handbook 6.5 s10.10.4.4-10.10.4.5\n"))
  cat(sprintf("  factor %.6f%s, t(%d) = %.4f\n", scale,
              ifelse(scale < 1, " -- FLOORED to 1, the house modification metafor does not make", ""),
              fit$k - 1, qt(0.975, df = fit$k - 1)))
  cat(sprintf("  %.4f (%.4f to %.4f)  -- REPORTED AS A SENSITIVITY, NOT AS THE PRIMARY INTERVAL\n",
              exp(fit$b[1]), exp(fit$b[1] - half), exp(fit$b[1] + half)))
  cat(sprintf("  at k = 2 this uses t on ONE degree of freedom, %.4f against z = 1.9600, so the\n",
              qt(0.975, df = 1)))
  cat("  width is a property of the method at very few studies and not a measurement of\n")
  cat("  this evidence.\n\n")

  fits[[key]] <- list(
    outcome = key, k = length(p$yi), measure = "HR", estimator = "REML",
    interval_method = "z",
    reproduces_the_served_value = "YES -- point, interval, tau^2, Q and I^2 all reproduce",
    point = pr$pred, ci_low = pr$ci.lb, ci_high = pr$ci.ub,
    tau2 = fit$tau2, i2 = fit$I2, q = fit$QE, df = fit$k - 1, qp = fit$QEp,
    pi_low = pr$pi.lb, pi_high = pr$pi.ub,
    hksj = list(point = exp(as.numeric(fit$b[1])), ci_low = exp(as.numeric(fit$b[1]) - half),
                ci_high = exp(as.numeric(fit$b[1]) + half), factor = scale,
                floored = scale < 1, t = qt(0.975, df = fit$k - 1)),
    verbatim = paste(c(
      sprintf("sotagliflozin-hf :: %s   k = %d   measure = HR", key, length(p$yi)),
      strrep("=", 92),
      sprintf("what is counted: %s", p$label),
      sprintf("trials: %s", paste(p$slab, collapse = ", ")),
      "",
      "THE FIT THAT PRODUCES THE ESTIMATE THIS PAGE SERVES -- metafor, REML, z interval:",
      capture.output(print(fit)),
      "",
      "Back-transformed to the hazard-ratio scale:",
      capture.output(print(pr)),
      "",
      "CHECK AGAINST THE VALUE THE PAGE SERVES. The quote is not earned until this passes,",
      "and this script refuses to write anything if it does not:",
      sprintf("  point   refit %-10.4f served %-10.4f  reproduced", pr$pred, p$served[["point"]]),
      sprintf("  ci_low  refit %-10.4f served %-10.4f  reproduced", pr$ci.lb, p$served[["lo"]]),
      sprintf("  ci_high refit %-10.4f served %-10.4f  reproduced", pr$ci.ub, p$served[["hi"]]),
      sprintf("  tau^2   refit %-10.6f stored %-10.6f  reproduced", fit$tau2, p$het[["tau2"]]),
      sprintf("  Q       refit %-10.4f stored %-10.4f  reproduced", fit$QE, p$het[["q"]]),
      sprintf("  I^2     refit %-10.2f stored %-10.2f  reproduced", fit$I2, p$het[["i2"]]),
      "",
      sprintf("Prediction interval: %.4f to %.4f. AT k = 2 THIS IS EXTREMELY WEAKLY DETERMINED",
              pr$pi.lb, pr$pi.ub),
      "and is reported because it was computed, not because it is informative.",
      "",
      "Hartung-Knapp sensitivity at k <= 3, per Cochrane Handbook 6.5 s10.10.4.4-10.10.4.5,",
      "which advises comparing methods rather than choosing one when there are only two or",
      "three studies. REPORTED AS A SENSITIVITY, NOT AS THE PRIMARY INTERVAL:",
      sprintf("  factor %.6f%s", scale,
              ifelse(scale < 1, " -- FLOORED to 1, the house modification metafor does not make", "")),
      sprintf("  %.4f (%.4f to %.4f), t on %d degree(s) of freedom = %.4f against z = 1.9600",
              exp(fit$b[1]), exp(fit$b[1] - half), exp(fit$b[1] + half), fit$k - 1,
              qt(0.975, df = fit$k - 1)),
      "  That width is a property of the method at very few studies, not a measurement of",
      "  this evidence.",
      "",
      sprintf("R environment: %s; metafor %s", R.version.string,
              as.character(packageVersion("metafor"))),
      "Script: ssot/sotagliflozin_pools.R"), collapse = "\n"),
    environment = paste0(R.version.string, "; metafor ",
                         as.character(packageVersion("metafor"))))
}

if (n_ok != length(pools)) stop("REFUSED: ", n_ok, " of ", length(pools), " pools reproduced.")

# THE ORDERING CHECK. Total events and first events are not two estimates of one quantity.
tot <- fits$hfcv_total$point
fst <- fits$hfcv_first$point
cat(strrep("=", 92), "\n")
cat("THE TWO POOLS ARE NOT TWO ESTIMATES OF ONE THING, AND THE ORDERING IS CHECKED.\n")
cat(strrep("=", 92), "\n")
cat(sprintf("  total events HR %.4f   first event HR %.4f\n", tot, fst))
if (tot > fst) {
  cat("  UNEXPECTED: the total-event effect is CLOSER to 1 than the first-event effect.\n")
  cat("  That is not impossible, but it is the ordering a crossed estimand would produce,\n")
  cat("  and it is flagged rather than passed over.\n")
} else {
  cat("  The total-event effect is further from 1 than the first-event effect, which is\n")
  cat("  what counting recurrences on the same trials should do when the treatment keeps\n")
  cat("  working after the first event. The estimands are not crossed.\n")
}
cat("  NOT ESTABLISHED BY THIS: that either estimand is correctly defined. This checks the\n")
cat("  ORDER of two numbers, which a swapped pair would fail and a shared error would not.\n\n")

write(toJSON(fits, auto_unbox = TRUE, digits = 12, na = "null"), outp)
cat("wrote", outp, "\n")
