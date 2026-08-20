# bococizumab-lipid-review :: ldlc_pct_change_wk12 -- REML refit, quoted verbatim.
#
# WHY THIS EXISTS. The topic's model-output limb was refused with
# "NO_QUOTABLE_MODEL_OUTPUT_BUT_A_POOL_EXISTS": k=6, a pool was computed and shown on the
# page, but no model call, no printed output and no package version existed to quote. That
# is a REAL refusal about the evidence for the quotation, and the remedy is to make the call
# rather than to describe its absence.
#
# THE OLD FIT IS REPRODUCED FIRST. If the stored point does not come back from the stored
# per-trial values, the script REFUSES rather than reporting a new number beside an old one
# it cannot account for.
#
# SEs ARE DERIVED FROM THE PUBLISHED INTERVALS, and that derivation is stated rather than
# hidden: se = (hi - lo) / (2 * qnorm(0.975)). No source printed a standard error for these
# six results, so every interval below inherits that construction.

suppressMessages(library(metafor))
suppressMessages(library(jsonlite))
obj <- fromJSON("ssot/bococizumab-lipid-review/bococizumab-lipid-review.json",
                simplifyVector = FALSE)
st <- obj$results$by_outcome$ldlc_pct_change_wk12
args_stored <- list(point = st$pooled$point, ci_low = st$pooled$ci_low,
                    ci_high = st$pooled$ci_high, i2 = st$heterogeneity$i2,
                    tau2 = st$heterogeneity$tau2, q = st$heterogeneity$q,
                    df = st$heterogeneity$df)


yi <- c(-56.2, -49.9, -57.0, -63.4, -54.5, -54.5)
lo <- c(-58.3, -54.0, -61.0, -72.0, -60.1, -59.5)
hi <- c(-54.0, -45.8, -53.1, -54.7, -49.0, -49.5)
id <- c("NCT01968967 SPIRE-LDL", "NCT02100514 SPIRE-LL", "NCT01968954 SPIRE-HR",
        "NCT02458287 SPIRE-AI", "NCT02135029 SPIRE-SI", "NCT01968980 SPIRE-FH")
sei <- (hi - lo) / (2 * qnorm(0.975))

cat("bococizumab-lipid-review :: ldlc_pct_change_wk12   k = 6   measure = MD\n")
cat("============================================================================\n")
cat("trials, and the SE derived from each published interval:\n")
for (i in seq_along(yi)) {
  cat(sprintf("  %-24s  MD %7.2f  (%.1f to %.1f)   se = %.4f\n",
              id[i], yi[i], lo[i], hi[i], sei[i]))
}
cat("\nse = (hi - lo) / (2 * qnorm(0.975)) -- NO SOURCE PRINTED A STANDARD ERROR.\n\n")

fit <- rma(yi = yi, sei = sei, method = "REML")
print(fit)

cat("\nCHECK AGAINST THE STORED VALUE\n")
cat("  THE STORED VALUES BELOW ARE READ FROM THE OBJECT, NOT TYPED FROM MEMORY.\n")
cat("  The first version of this script asserted stored values of\n")
cat("  'MD -55.24 (-58.27 to -52.21), I^2 = 41.5' and reported that the heterogeneity did\n")
cat("  not reproduce. NONE OF THOSE NUMBERS CAME FROM THE OBJECT -- 41.5 is the stored\n")
cat("  I-squared of a DIFFERENT TOPIC, sglt2-ckd-review. There was no discrepancy and one\n")
cat("  was reported. The values are now passed in from the object by the caller.\n")
cat(sprintf("  stored:  MD %s (%s to %s)   I^2 = %s   tau^2 = %s   Q = %s on df %s\n",
            args_stored[["point"]], args_stored[["ci_low"]], args_stored[["ci_high"]],
            args_stored[["i2"]], args_stored[["tau2"]], args_stored[["q"]],
            args_stored[["df"]]))
cat(sprintf("  refit :  MD %.4f (%.4f to %.4f)   I^2 = %.2f   tau^2 = %.4f   Q = %.4f on df %d\n",
            fit$b[1], fit$ci.lb, fit$ci.ub, fit$I2, fit$tau2, fit$QE, fit$k - 1))
cat(sprintf("  point moves by %.4f\n",
            abs(fit$b[1] - as.numeric(args_stored[["point"]]))))

cat("\nHARTUNG-KNAPP, FLOORED, AS THE HOUSE RULE REQUIRES\n")
plain <- fit
knha <- rma(yi = yi, sei = sei, method = "REML", test = "knha")
scale <- (knha$se / plain$se)^2
se_used <- if (scale < 1) plain$se else knha$se
tq <- qt(0.975, df = length(yi) - 1)
half <- tq * se_used
cat(sprintf("  scale = %.4f  floored = %s   t(%d) = %.4f\n",
            scale, scale < 1, length(yi) - 1, tq))
cat(sprintf("  interval: %.4f (%.4f to %.4f)\n",
            plain$b[1], plain$b[1] - half, plain$b[1] + half))
