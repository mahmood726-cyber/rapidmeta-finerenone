# Re-pool alirocumab-lipid: 6 trials -> 8, after screening recovered two eligible, poolable
# trials that were absent from the object. Old and new reported side by side.
#
# EVERY NUMBER READ FROM SOURCE, NEVER COMPUTED FROM ANOTHER CELL:
#   the six existing MDs and CIs come from results.by_outcome.ldlc_pct_change_wk24.per_trial
#   the two recovered come from each trial's OWN posted resultsSection (LS means + SEs),
#   fetched from the v2 API and keyed to the registration id.
#
# SEs for the six are DERIVED from the published CI: se = (hi - lo) / (2 * 1.959964). That is a
# derivation and is labelled one; the alternative is to invent a precision the object never
# recorded.

suppressMessages(library(metafor))

# ---- the six already in the object -------------------------------------------------------
nct <- c("NCT01507831","NCT01617655","NCT01623115","NCT01644175","NCT01709500","NCT02107898")
md  <- c(-61.9, -39.1, -57.9, -45.9, -51.4, -64.1)
lo  <- c(-64.3, -51.1, -63.3, -52.5, -58.1, -68.5)
hi  <- c(-59.4, -27.1, -52.6, -39.3, -44.8, -59.8)
se  <- (hi - lo) / (2 * qnorm(0.975))

# ---- the two recovered by screening ------------------------------------------------------
# NCT02289963: two arms, LS mean % change at week 24, ITT.
#   placebo     6.3 (SE 2.9)   alirocumab -57.1 (SE 3.0)
md_963 <- -57.1 - 6.3
se_963 <- sqrt(3.0^2 + 2.9^2)

# NCT02585778 (ODYSSEY DM-INSULIN): FOUR groups. The trial posts NO single overall estimate --
# it reports T1DM and T2DM strata separately, so a trial-level contrast has to be assembled.
#   T1DM  alirocumab -51.8 (SE 3.7) n=49   placebo -3.9 (SE 5.3) n=25
#   T2DM  alirocumab -48.2 (SE 1.6) n=287  placebo  0.8 (SE 2.2) n=142
# The two strata are DISJOINT sets of participants from one randomisation, so they are combined
# by fixed-effect inverse variance to recover the trial-level estimate (Handbook 6.5 s23.3,
# combining groups). Fixed-effect and not random: this is one trial, not two.
md_t1 <- -51.8 - (-3.9);  se_t1 <- sqrt(3.7^2 + 5.3^2)
md_t2 <- -48.2 - 0.8;     se_t2 <- sqrt(1.6^2 + 2.2^2)
w1 <- 1/se_t1^2; w2 <- 1/se_t2^2
md_778 <- (md_t1*w1 + md_t2*w2) / (w1 + w2)
se_778 <- sqrt(1/(w1 + w2))

cat("=== RECOVERED TRIAL CONTRASTS, from each trial's own posted results ===\n")
cat(sprintf("NCT02289963  MD %.2f  SE %.3f  (two arms, read directly)\n", md_963, se_963))
cat(sprintf("NCT02585778  T1DM MD %.2f SE %.3f | T2DM MD %.2f SE %.3f\n", md_t1, se_t1, md_t2, se_t2))
cat(sprintf("NCT02585778  MD %.2f  SE %.3f  (strata combined, fixed-effect IV)\n\n", md_778, se_778))

# ---- OLD pool: the six, with the estimator the object declares --------------------------
old_dl <- rma(yi = md, sei = se, method = "DL")
cat("=== OLD: k=6, DerSimonian-Laird (the estimator the object declares) ===\n")
print(summary(old_dl))

# ---- NEW pool: all eight, same estimator, so the change is attributable to the trials ----
nct8 <- c(nct, "NCT02289963", "NCT02585778")
md8  <- c(md, md_963, md_778)
se8  <- c(se, se_963, se_778)
new_dl <- rma(yi = md8, sei = se8, method = "DL")
cat("\n=== NEW: k=8, SAME estimator (DL), so the delta is the two trials and nothing else ===\n")
print(summary(new_dl))

# ---- and the estimator the statistics rules actually require ----------------------------
# DerSimonian-Laird is biased for k < 10; REML or Paule-Mandel is indicated. The object
# declares DL, so DL is used above FOR COMPARABILITY. Reported here as a SEPARATE finding
# rather than silently switched, because changing the estimator and the trial set in one step
# would make the movement unattributable.
new_reml <- rma(yi = md8, sei = se8, method = "REML")
cat("\n=== NEW: k=8, REML -- methodologically preferred at k<10, reported separately ===\n")
print(summary(new_reml))

pi_reml <- predict(new_reml)
cat(sprintf("\nREML prediction interval: %.2f to %.2f\n", pi_reml$pi.lb, pi_reml$pi.ub))

cat("\n=== SIDE BY SIDE ===\n")
cat(sprintf("OLD k=6  DL    MD %.2f  (%.2f to %.2f)  tau2 %.2f  I2 %.1f%%\n",
            old_dl$b, old_dl$ci.lb, old_dl$ci.ub, old_dl$tau2, old_dl$I2))
cat(sprintf("NEW k=8  DL    MD %.2f  (%.2f to %.2f)  tau2 %.2f  I2 %.1f%%\n",
            new_dl$b, new_dl$ci.lb, new_dl$ci.ub, new_dl$tau2, new_dl$I2))
cat(sprintf("NEW k=8  REML  MD %.2f  (%.2f to %.2f)  tau2 %.2f  I2 %.1f%%\n",
            new_reml$b, new_reml$ci.lb, new_reml$ci.ub, new_reml$tau2, new_reml$I2))
cat(sprintf("\nR %s / metafor %s\n", getRversion(), packageVersion("metafor")))
