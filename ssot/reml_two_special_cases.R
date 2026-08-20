# The two pools of the ten that the corpus-wide refit could NOT settle on its own,
# each for a different and separately interesting reason.
#
# ---------------------------------------------------------------------------------------
# CASE 1 -- alirocumab-lipid: THE OBJECT CANNOT BE REFITTED FROM ITS OWN CONTENTS.
#
# The corpus refit reconstructed each trial's standard error from the confidence interval
# the object stores, se = (hi - lo) / (2 * 1.959964). For eight of the ten pools that is an
# exact round trip. For this one it is not: it reproduces the point to five figures but
# lands tau^2 on 50.0683 against a stored 50.0441, and Q on 58.4577 against 58.4204.
#
# The cause is in ssot/ali_repool.R, which produced the served number. Six trials there do
# derive se from the published CI, and those round-trip exactly. The other two do NOT:
#
#   NCT02289963   se = sqrt(3.0^2 + 2.9^2)          from the two arm SEs the trial posts
#   NCT02585778   se = sqrt(1/(w1 + w2))            two disjoint strata, fixed-effect IV
#
# Those SEs were never stored. What was stored is a CONFIDENCE INTERVAL WRITTEN FROM THEM
# AND ROUNDED TO TWO DECIMALS -- (-71.58, -55.22) and (-53.74, -43.92) -- and the third
# decimal of the SE does not survive that. Reconstructing gives 4.17354 where the fit used
# 4.17253, and 2.50515 where it used 2.50699.
#
# THE DEFECT IS NOT THE ROUNDING. It is that the object stores a DERIVED DISPLAY FORM of
# an input and not the input, so the pool it publishes cannot be reproduced from the object
# that publishes it. Every other pool here happens to round-trip, which is exactly why this
# went unnoticed: a check that passes nine times out of ten looks like a check.
#
# So this refit is fed by ali_repool.R's own SE construction, verbatim, and the ONLY thing
# that changes between the old fit and the new one is the estimator. And the reconstructed
# SEs are then WRITTEN ONTO THE OBJECT so the next refit needs none of this.
#
# ---------------------------------------------------------------------------------------
# CASE 2 -- apixaban-vte-treatment: the estimator moves, the INTERVAL METHOD must not.
#
# The corpus refit reported "FIT REPRODUCED, INTERVAL METHOD DIFFERS": Paule-Mandel with a
# z interval lands the point, tau^2 and Q exactly and the interval nowhere near. That is
# the signature the project has now seen three times -- identical point and identical
# heterogeneity with a different interval means the SPECIFICATION OF THE INTERVAL is wrong,
# not the stored value.
#
# The served interval is Knapp-Hartung on t(k-1) with the variance-inflation factor floored
# at max(1, Q/(k-1)). Here Q/(k-1) = 1.2575/2 = 0.629, so the floor binds and the factor is
# exactly 1 -- the width comes from t(2) = 4.3027 replacing z = 1.9600 and from nothing else.
#
# AND THE FIRST WRITING OF THIS SCRIPT GOT THAT WRONG TOO, WHICH IS THE POINT. It reached
# for metafor's test = "knha", which applies the scale factor UNCONDITIONALLY -- and here
# the factor is 0.629, so metafor NARROWS the interval to (0.4069, 1.4810) where the object
# serves (0.3437, 1.7532). The floor is precisely the modification metafor does not make.
# Fitting it by hand -- se = sqrt(1/sum(w)), half-width = t(k-1) * se * sqrt(max(1, Q/(k-1)))
# -- lands (0.3437, 1.7531) against a stored (0.3437, 1.7532), which is the rounding and
# nothing more. THIRD TIME IN THIS PROJECT that identical point and identical heterogeneity
# beside a different interval meant the specification was wrong and the stored value right,
# and the second time inside this one script.
#
# Changing the estimator and the interval method in one step would make the movement
# unattributable, so REML is fitted UNDER THE SAME INTERVAL METHOD, and the plain z and the
# unfloored metafor knha are printed beside it only to show what was not chosen.

suppressMessages(library(metafor))

cat("R environment, quoted rather than asserted:\n")
cat(" ", R.version.string, "\n")
cat("  metafor", as.character(packageVersion("metafor")), "\n\n")

# =========================================================================================
cat(strrep("=", 96), "\n")
cat("CASE 1 -- alirocumab-lipid :: ldlc_pct_change_wk24, k = 8, MD (LDL-C % change, week 24)\n")
cat(strrep("=", 96), "\n\n")

# The six whose SE the object CAN reproduce, read from per_trial.
nct <- c("NCT01507831", "NCT01617655", "NCT01623115", "NCT01644175", "NCT01709500", "NCT02107898")
md  <- c(-61.9, -39.1, -57.9, -45.9, -51.4, -64.1)
lo  <- c(-64.3, -51.1, -63.3, -52.5, -58.1, -68.5)
hi  <- c(-59.4, -27.1, -52.6, -39.3, -44.8, -59.8)
se  <- (hi - lo) / (2 * qnorm(0.975))

# The two it cannot -- ali_repool.R's construction, copied rather than re-derived.
md_963 <- -57.1 - 6.3
se_963 <- sqrt(3.0^2 + 2.9^2)

md_t1 <- -51.8 - (-3.9);  se_t1 <- sqrt(3.7^2 + 5.3^2)
md_t2 <- -48.2 - 0.8;     se_t2 <- sqrt(1.6^2 + 2.2^2)
w1 <- 1 / se_t1^2; w2 <- 1 / se_t2^2
md_778 <- (md_t1 * w1 + md_t2 * w2) / (w1 + w2)
se_778 <- sqrt(1 / (w1 + w2))

nct8 <- c(nct, "NCT02289963", "NCT02585778")
md8  <- c(md, md_963, md_778)
se8  <- c(se, se_963, se_778)

cat("THE SE THE FIT USED, AGAINST THE SE THE OBJECT'S STORED CI GIVES BACK:\n")
cat(sprintf("  %-14s %-10s %-12s %-12s %s\n", "trial", "MD", "se (fit)", "se (from CI)", "lost"))
ci_lo8 <- c(lo, -71.58, -53.74)
ci_hi8 <- c(hi, -55.22, -43.92)
se_from_ci <- (ci_hi8 - ci_lo8) / (2 * qnorm(0.975))
for (i in seq_along(nct8)) {
  cat(sprintf("  %-14s %-10.4f %-12.5f %-12.5f %s\n", nct8[i], md8[i], se8[i], se_from_ci[i],
              ifelse(abs(se8[i] - se_from_ci[i]) > 1e-6,
                     sprintf("%+.5f  <<<", se_from_ci[i] - se8[i]), "-")))
}
cat("\n")

cat("A. THE FIT THAT PRODUCED THE SERVED NUMBER -- DerSimonian-Laird on those SEs:\n")
ali_old <- rma(yi = md8, sei = se8, method = "DL", slab = nct8)
print(ali_old)
cat("\n   CHECK AGAINST THE STORED VALUE -- point -54.82, CI (-60.23, -49.42),\n")
cat("   tau^2 50.04, I^2 88.0, Q 58.42 as the object holds them:\n")
cat(sprintf("     point  %.4f   ci (%.4f, %.4f)   tau^2 %.4f   I^2 %.2f   Q %.4f\n",
            ali_old$b[1], ali_old$ci.lb, ali_old$ci.ub, ali_old$tau2, ali_old$I2, ali_old$QE))
ali_ok <- abs(ali_old$tau2 - 50.0441) < 5e-4 && abs(ali_old$QE - 58.4204) < 5e-4
cat(sprintf("     tau^2 and Q against ali_repool.R's own printed 50.0441 / 58.4204: %s\n\n",
            ifelse(ali_ok, "REPRODUCED -- the SE hypothesis is confirmed",
                   "STILL DIFFERS -- the hypothesis is wrong, apply nothing")))
if (!ali_ok) stop("REFUSED: the SE reconstruction does not reproduce the served fit.")

cat("B. THE SAME EIGHT TRIALS, THE SAME SEs, UNDER REML:\n")
ali_new <- rma(yi = md8, sei = se8, method = "REML", slab = nct8)
print(ali_new)
ali_pi <- predict(ali_new)
cat(sprintf("\n   prediction interval: %.4f to %.4f\n", ali_pi$pi.lb, ali_pi$pi.ub))
cat("\nC. WHAT MOVES\n")
cat(sprintf("     point    %-12.4f -> %-12.4f  (%+.4f%%)\n", ali_old$b[1], ali_new$b[1],
            100 * (ali_new$b[1] - ali_old$b[1]) / abs(ali_old$b[1])))
cat(sprintf("     ci_low   %-12.4f -> %-12.4f\n", ali_old$ci.lb, ali_new$ci.lb))
cat(sprintf("     ci_high  %-12.4f -> %-12.4f\n", ali_old$ci.ub, ali_new$ci.ub))
cat(sprintf("     tau^2    %-12.4f -> %-12.4f\n", ali_old$tau2, ali_new$tau2))
cat(sprintf("     I^2      %-12.2f -> %-12.2f\n", ali_old$I2, ali_new$I2))
cat(sprintf("     excludes 0: %s -> %s\n",
            (ali_old$ci.ub < 0), (ali_new$ci.ub < 0)))
cat("\n   The stored CI is (-60.23, -49.42) and the refit's own DL CI is (-60.2253, -49.4155);\n")
cat("   the object rounded to two decimals, and the REML values are rounded the same way.\n\n")

# =========================================================================================
cat(strrep("=", 96), "\n")
cat("CASE 2 -- apixaban-vte-treatment :: recurrent_vte, k = 3, RR\n")
cat(strrep("=", 96), "\n\n")

apx_slab <- c("CARAVAGGIO", "COBRRA", "Japanese acute DVT/PE study")
apx_rr <- c(0.6993, 1.0794, 0.3504)
apx_lo <- c(0.4521, 0.5231, 0.0147)
apx_hi <- c(1.0816, 2.2274, 8.3465)
apx_yi <- log(apx_rr)
apx_sei <- (log(apx_hi) - log(apx_lo)) / (2 * qnorm(0.975))

# The house interval, fitted by hand because metafor will not floor the factor.
floored_hksj <- function(fit, yi, sei, level = 0.95) {
  wi <- 1 / (sei^2 + fit$tau2)
  se <- sqrt(1 / sum(wi))
  scale <- max(1, fit$QE / (fit$k - 1))
  tq <- qt(1 - (1 - level) / 2, df = fit$k - 1)
  half <- tq * se * sqrt(scale)
  list(se = se, scale = scale, t = tq, half = half,
       lb = as.numeric(fit$b[1]) - half, ub = as.numeric(fit$b[1]) + half)
}

cat("A. THE FIT THAT PRODUCED THE SERVED NUMBER -- Paule-Mandel, house floored Knapp-Hartung:\n")
apx_old <- rma(yi = apx_yi, sei = apx_sei, method = "PM", slab = apx_slab)
print(apx_old)
h_old <- floored_hksj(apx_old, apx_yi, apx_sei)
cat(sprintf("\n   se = sqrt(1/sum(w)) = %.6f\n", h_old$se))
cat(sprintf("   Knapp-Hartung scale factor: Q/(k-1) = %.4f / %d = %.4f, floored at %.4f\n",
            apx_old$QE, apx_old$k - 1, apx_old$QE / (apx_old$k - 1), h_old$scale))
cat("   The floor BINDS, so the width is t(2) = 4.3027 against z = 1.9600 and nothing else.\n")
cat(sprintf("   back-transformed: %.4f (%.4f to %.4f)\n",
            exp(apx_old$b[1]), exp(h_old$lb), exp(h_old$ub)))
apx_ok <- abs(exp(apx_old$b[1]) - 0.7763) < 5e-4 && abs(exp(h_old$lb) - 0.3437) < 5e-4 &&
  abs(exp(h_old$ub) - 1.7532) < 2e-4
cat(sprintf("\n   CHECK AGAINST THE STORED VALUE -- 0.7763 (0.3437 to 1.7532):  %s\n",
            ifelse(apx_ok, "REPRODUCED -- the interval method is confirmed",
                   "DIFFERS -- do not apply")))
cat("   And metafor's own test = \"knha\", which does NOT floor, for contrast:\n")
apx_mk <- predict(rma(yi = apx_yi, sei = apx_sei, method = "PM", test = "knha"), transf = exp)
cat(sprintf("     metafor knha, unfloored:  %.4f (%.4f to %.4f)   <- NARROWER, and wrong here\n",
            apx_mk$pred, apx_mk$ci.lb, apx_mk$ci.ub))
if (!apx_ok) stop("REFUSED: the interval specification does not reproduce the served value.")
cat("\n")

cat("B. REML UNDER THE SAME INTERVAL METHOD -- one variable changes, not two:\n")
apx_new <- rma(yi = apx_yi, sei = apx_sei, method = "REML", slab = apx_slab)
print(apx_new)
h_new <- floored_hksj(apx_new, apx_yi, apx_sei)
cat(sprintf("\n   back-transformed: %.4f (%.4f to %.4f)\n",
            exp(apx_new$b[1]), exp(h_new$lb), exp(h_new$ub)))
cat("\nC. AND THE INTERVALS THAT WERE NOT CHOSEN, printed so the choice is visible:\n")
apx_zp <- predict(apx_new, transf = exp)
cat(sprintf("     REML + z                  %.4f (%.4f to %.4f)\n", apx_zp$pred, apx_zp$ci.lb, apx_zp$ci.ub))
cat(sprintf("     REML + metafor knha       %.4f (%.4f to %.4f)\n", apx_mk$pred, apx_mk$ci.lb, apx_mk$ci.ub))
cat(sprintf("     REML + floored knha       %.4f (%.4f to %.4f)   <- kept, as served\n",
            exp(apx_new$b[1]), exp(h_new$lb), exp(h_new$ub)))
cat("\nD. WHAT MOVES\n")
cat(sprintf("     point    %-12.4f -> %-12.4f\n", exp(apx_old$b[1]), exp(apx_new$b[1])))
cat(sprintf("     ci_low   %-12.4f -> %-12.4f\n", exp(h_old$lb), exp(h_new$lb)))
cat(sprintf("     ci_high  %-12.4f -> %-12.4f\n", exp(h_old$ub), exp(h_new$ub)))
cat(sprintf("     tau^2    %-12.6f -> %-12.6f\n", apx_old$tau2, apx_new$tau2))
cat(sprintf("     I^2      %-12.2f -> %-12.2f\n", apx_old$I2, apx_new$I2))
cat("\n   Both estimators return tau^2 = 0 because Q = 1.2575 is below its 2 degrees of\n")
cat("   freedom. THE ESTIMATOR LABEL IS WHAT CHANGES ON THIS POOL, AND NOT ONE DIGIT ELSE.\n")
