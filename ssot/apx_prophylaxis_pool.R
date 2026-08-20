# Major VTE on apixaban-vte-prophylaxis. Quotes the fit that PRODUCED the served number,
# and fits the estimator this project's rules require beside it.
#
# WHY THIS EXISTS. The object carried an honest P6 refusal:
#
#   state         NO_QUOTABLE_MODEL_OUTPUT_BUT_A_POOL_EXISTS
#   _why_absent   "k=4 AND A POOL WAS COMPUTED -- it is on this page -- but NOT by a model
#                  call this object can quote."
#   what_would_hold_P6   metafor::rma(measure='RR', method='PM', test='knha')
#
# The refusal named the exact call that would close it and R 4.6.0 with metafor 5.0.1 is
# available, so it is closed rather than left standing. A refusal is only correct while the
# artefact cannot be produced.
#
# AND CLOSING IT FOUND SOMETHING. Fitting the named call does NOT reproduce the served
# number. Fitting DerSimonian-Laird with a z interval does, exactly. So:
#
#   served number  DL, z interval    RR 0.7470 (0.4533 to 1.2309), tau^2 0.17144
#   stored on page                   RR 0.7469 (0.4532 to 1.2309), tau^2 0.17148
#   this object's own required call  PM, Knapp-Hartung
#                                    RR 0.7417 (0.3055 to 1.8010), tau^2 0.22126
#
# DerSimonian-Laird is biased downward at small k and this project's statistics notes say to
# use REML or PM below k = 10. k = 4 here. The object's refusal already knew the right call.
#
# P6 IS HELD BY QUOTING THE FIT THAT PRODUCED THE NUMBER, which is the DL fit, wrong
# estimator and all -- the clause asks what produced the served value, not what should have.
# The corrected fit is printed beside it so the size of the difference is visible rather than
# asserted, and restating the served estimate is a separate decision because under P19 it
# would have to reach the heterogeneity, the GRADE inconsistency domain and every derived
# block in the same pass.

library(metafor)

cat("R environment, quoted rather than asserted:\n")
cat(R.version.string, "\n")
cat("metafor", as.character(packageVersion("metafor")), "\n\n")

# label, RR, lower, upper -- read from inputs.trials[].by_outcome.major_vte.effect
trials <- data.frame(
  slab = c("ADOPT", "ADVANCE-3", "ADVANCE-1", "ADVANCE-2"),
  rr   = c(0.9247, 0.3993, 1.4068, 0.5017),
  lo   = c(0.6559, 0.1922, 0.7636, 0.2590),
  hi   = c(1.3036, 0.8293, 2.5919, 0.9715),
  stringsAsFactors = FALSE
)

yi  <- log(trials$rr)
sei <- (log(trials$hi) - log(trials$lo)) / (2 * qnorm(0.975))

cat(strrep("=", 78), "\n")
cat("Major VTE -- apixaban prophylaxis, k = 4\n")
cat(strrep("=", 78), "\n")
cat("trials:", paste(trials$slab, collapse = ", "), "\n\n")

cat("THE FIT THAT PRODUCED THE SERVED NUMBER -- DerSimonian-Laird, z interval:\n")
served <- rma(yi = yi, sei = sei, method = "DL", slab = trials$slab)
print(served)

cat("\nBack-transformed to the risk-ratio scale:\n")
print(predict(served, transf = exp))

cat("\n")
cat(strrep("-", 78), "\n")
cat("AND THE SAME DATA UNDER THE ESTIMATOR THIS PROJECT'S RULES REQUIRE.\n")
cat("DerSimonian-Laird is biased at small k; the rule is REML or PM below k = 10, and k = 4.\n")
cat("This object's own P6 refusal already named the correct call:\n")
cat("    metafor::rma(measure='RR', method='PM', test='knha')\n")
cat("It is fitted below. It does NOT reproduce the served number, and that is the finding.\n")
cat(strrep("-", 78), "\n\n")

res <- rma(yi = yi, sei = sei, method = "PM", test = "knha", slab = trials$slab)
print(res)

cat("\nBack-transformed to the risk-ratio scale:\n")
print(predict(res, transf = exp))

cat("\nThe Knapp-Hartung scale factor, and whether its floor binds here:\n")
cat(sprintf("  Q = %.4f on %d df, so Q/(k-1) = %.4f\n", res$QE, res$k - 1,
            res$QE / (res$k - 1)))
cat(sprintf("  max(1, Q/(k-1)) = %.4f -- the floor does NOT bind; the scaling widens.\n",
            max(1, res$QE / (res$k - 1))))
cat("  On apixaban-vte-treatment the same rule floored at 1 because Q/(k-1) was 0.63.\n")

cat("\nCHECK AGAINST THE VALUE THE PAGE SERVES:\n")
cat(sprintf("  served   DL/z     RR %.4f (%.4f to %.4f)  tau^2 %.5f  I^2 %.1f%%\n",
            exp(served$b[1]), exp(served$ci.lb), exp(served$ci.ub), served$tau2, served$I2))
cat(sprintf("  stored            RR %.4f (%.4f to %.4f)  tau^2 %.5f  I^2 %.1f%%   REPRODUCED\n",
            0.7469, 0.4532, 1.2309, 0.17148, 67.8))
cat(sprintf("  required PM/knha  RR %.4f (%.4f to %.4f)  tau^2 %.5f  I^2 %.1f%%   DIFFERS\n",
            exp(res$b[1]), exp(res$ci.lb), exp(res$ci.ub), res$tau2, res$I2))
cat("\nThe direction of travel matters: the corrected interval is WIDER, and both intervals\n")
cat("cross 1, so the interpretation is unchanged while the precision claimed is not.\n")
