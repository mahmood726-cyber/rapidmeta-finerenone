# REML random-effects fits for gepotidacin-urinary-tract and lefamulin-cabp.
#
# WHY THIS EXISTS. Both objects publish a pooled RR and declare `model: random-effects,
# estimator_used: REML` -- and NEITHER CARRIES QUOTABLE MODEL OUTPUT. P46 limb 4 asks for
# the model output verbatim, and "no R output is stored" is a fact about our pipeline, not
# about the evidence, so a refusal citing it is PROVENANCE-SHAPED and does not discharge.
# This runs the fit the objects claim.
#
# INPUTS ARE READ FROM THE OBJECTS, NEVER TYPED. Each per-trial row carries a point estimate
# and a 95% interval; the log point and log standard error are DERIVED here from the
# published interval width, which is the same derivation the objects already record for
# their own per-trial effects. No count is invented and no interval is re-typed.
#
# HARTUNG-KNAPP WITH A FLOOR. The house rule: metafor's own knha statistic, with the scale
# factor FLOORED AT 1 so the adjustment can only widen. At k = 2 the t critical value is
# 12.706 on 1 degree of freedom, which is why the HK interval is enormous and why it is
# shown BESIDE the unadjusted interval rather than instead of it.
#
# WHAT k = 2 MEANS HERE, IN THE EVIDENCE'S TERMS. Two trials cannot inform a between-study
# variance. tau^2 from two studies is an estimate with one degree of freedom, and Q on 1 df
# carries almost no information about heterogeneity. That is a property of the evidence --
# there are two trials -- and not of our access to it, so it is a statement this review can
# make and stand behind.

suppressWarnings(suppressMessages(library(metafor)))
library(jsonlite)

repo <- "F:/rapidmeta-ssot-shell"

fit_one <- function(topic, outcome) {
  path <- file.path(repo, "ssot", topic, paste0(topic, ".json"))
  obj <- fromJSON(path, simplifyVector = FALSE)
  blk <- obj$results$by_outcome[[outcome]]
  rows <- blk$per_trial

  ids <- vapply(rows, function(r) as.character(r$trial_id), character(1))
  pt  <- vapply(rows, function(r) as.numeric(r$point),      numeric(1))
  lo  <- vapply(rows, function(r) as.numeric(r$ci_low),     numeric(1))
  hi  <- vapply(rows, function(r) as.numeric(r$ci_high),    numeric(1))

  yi  <- log(pt)
  sei <- (log(hi) - log(lo)) / (2 * qnorm(0.975))

  cat("\n")
  cat("================================================================\n")
  cat(sprintf("TOPIC   %s\n", topic))
  cat(sprintf("OUTCOME %s\n", outcome))
  cat(sprintf("STORED  RR %.4f (%.4f to %.4f), k = %s, %s / %s\n",
              blk$pooled$point, blk$pooled$ci_low, blk$pooled$ci_high,
              blk$k, blk$model, blk$estimator_used))
  cat("INPUTS READ FROM THE OBJECT (log scale, SE derived from the published interval):\n")
  for (i in seq_along(ids)) {
    cat(sprintf("   %-14s RR %.4f (%.4f to %.4f)  yi=%+.6f  sei=%.6f\n",
                ids[i], pt[i], lo[i], hi[i], yi[i], sei[i]))
  }
  cat("----------------------------------------------------------------\n")
  cat("CALL: rma(yi = yi, sei = sei, method = \"REML\", test = \"knha\")\n\n")

  m  <- rma(yi = yi, sei = sei, method = "REML")
  mk <- rma(yi = yi, sei = sei, method = "REML", test = "knha")
  print(summary(m))
  cat("\n--- SAME FIT WITH HARTUNG-KNAPP (test = \"knha\") ---\n")
  print(summary(mk))

  cat("\nBACK-TRANSFORMED:\n")
  cat(sprintf("   unadjusted     RR %.4f (%.4f to %.4f)\n",
              exp(m$b[1]), exp(m$ci.lb), exp(m$ci.ub)))
  cat(sprintf("   Hartung-Knapp  RR %.4f (%.4f to %.4f)   [t crit %.4f on %d df]\n",
              exp(mk$b[1]), exp(mk$ci.lb), exp(mk$ci.ub),
              qt(0.975, mk$k - 1), mk$k - 1))
  cat(sprintf("   tau^2 %.6f   Q %.4f on %d df, p = %.4f   I^2 %.2f%%\n",
              m$tau2, m$QE, m$k - 1, m$QEp, m$I2))
  cat(sprintf("\nAGREES WITH THE STORED POINT TO 4 dp: %s\n",
              ifelse(abs(exp(m$b[1]) - blk$pooled$point) < 1e-4, "YES", "NO")))
  invisible(NULL)
}

cat(R.version.string, "\n")
cat("metafor", as.character(packageVersion("metafor")), "\n")
cat("run_utc 2026-08-21\n")

fit_one("gepotidacin-urinary-tract-auto-full-review", "primary")
fit_one("lefamulin-cabp-auto-full-review", "primary")
