# Recurrent VTE on apixaban-vte-treatment, refitted so the printed output can be QUOTED.
#
# WHY THIS EXISTS. The object stores a pooled risk ratio for recurrent VTE and stored no model
# output, so P46's fourth limb -- the model output quoted verbatim -- could not be met. A
# number a reader cannot check against the call that produced it is exactly what this project
# refuses elsewhere, and it was refusing it on its own page.
#
# INPUTS ARE THE PER-TRIAL EFFECTS ALREADY ON THE OBJECT, each derived from that trial's own
# arm-level event counts. Nothing is re-derived from counts here and no trial is added.
#
# THE FIRST REFIT WAS WRONG AND THAT IS WHY THE CHECK EXISTS. A plain REML/z fit reproduced
# the point (0.7763), Q (1.2575) and I^2 (0.00%) EXACTLY and returned an interval of
# 0.5356 to 1.1251 against a stored 0.3437 to 1.7532. Identical point and heterogeneity with
# a different interval means the INPUTS were right and the SPECIFICATION was wrong -- so the
# stored value was investigated, not overwritten.
#
# The interval this page serves is Knapp-Hartung with a FLOOR, and two rules govern it:
#   HKSJ df    -- use qt(alpha/2, k-1), never qnorm. With k = 3 that is t on 2 df = 4.3027.
#   HKSJ floor -- when Q < k-1 the Knapp-Hartung scaling SHRINKS the interval below the
#                 ordinary one, which is the wrong direction for a small-k adjustment. The
#                 scale factor is floored at max(1, Q/(k-1)). Here Q/(k-1) = 0.6288, so the
#                 floor binds: the scaling contributes nothing and the t critical value is
#                 what widens the interval.

library(metafor)

cat("R environment, quoted rather than asserted:\n")
cat(R.version.string, "\n")
cat("metafor", as.character(packageVersion("metafor")), "\n\n")

# label, RR, lower, upper -- read from inputs.trials[].by_outcome.recurrent_vte.effect
trials <- data.frame(
  slab = c("CARAVAGGIO", "COBRRA", "Japanese acute DVT/PE study"),
  rr   = c(0.6993, 1.0794, 0.3504),
  lo   = c(0.4521, 0.5231, 0.0147),
  hi   = c(1.0816, 2.2274, 8.3465),
  stringsAsFactors = FALSE
)

yi  <- log(trials$rr)
sei <- (log(trials$hi) - log(trials$lo)) / (2 * qnorm(0.975))

cat(strrep("=", 78), "\n")
cat("Recurrent VTE -- apixaban against its comparator, random-effects REML on the log scale\n")
cat(strrep("=", 78), "\n")
cat("trials:", paste(trials$slab, collapse = ", "), "\n\n")

res <- rma(yi = yi, sei = sei, method = "REML", slab = trials$slab)
print(res)

scale2 <- max(1, res$QE / (res$k - 1))
se_adj <- res$se * sqrt(scale2)
tcrit  <- qt(0.975, df = res$k - 1)
lo_adj <- res$b[1] - tcrit * se_adj
hi_adj <- res$b[1] + tcrit * se_adj

cat("\nKnapp-Hartung with the floor, which is the interval this page serves:\n")
cat(sprintf("  scale factor max(1, Q/(k-1)) = max(1, %.4f) = %.4f\n",
            res$QE / (res$k - 1), scale2))
cat(sprintf("  t(%d) = %.4f, against z = %.4f\n", res$k - 1, tcrit, qnorm(0.975)))
cat(sprintf("  RR %.4f (%.4f to %.4f)\n", exp(res$b[1]), exp(lo_adj), exp(hi_adj)))

cat("\nFor contrast, the ordinary REML/z interval, which this page does NOT serve:\n")
pred <- predict(res, transf = exp)
print(pred)

cat("\nPer-trial contributions, as weights:\n")
print(round(weights(res), 2))

cat("\nCHECK AGAINST THE VALUE THE PAGE SERVES:\n")
cat(sprintf("  refit  [HKSJ, floored]  RR %.4f (%.4f to %.4f)\n",
            exp(res$b[1]), exp(lo_adj), exp(hi_adj)))
cat(sprintf("  stored                  RR %.4f (%.4f to %.4f)\n", 0.7763, 0.3437, 1.7532))
cat(sprintf("  Q %.4f on %d df; stored Q 1.2575 on 2 df\n", res$QE, res$k - 1))
cat(sprintf("  I^2 %.2f%%; stored 0.00%%\n", res$I2))
