# REML random-effects refit for any object whose per-trial rows carry a point and interval.
#
# GENERALISED FROM ssot/fit_gepotidacin_lefamulin.R, which was written for two topics and
# then wanted for a third. Takes topic and outcome as arguments so the next one does not
# need a new file -- the hardcoded-list lesson, applied at the second edit rather than the
# fourth.
#
#   Rscript ssot/fit_from_per_trial.R <topic> <outcome>
#
# INPUTS ARE READ FROM THE OBJECT, NEVER TYPED. yi = log(point);
# sei = (log(ci_high) - log(ci_low)) / (2 * 1.959964), which is the same derivation the
# objects already record for their own per-trial effects. No count is invented.
#
# HARTUNG-KNAPP IS SHOWN BESIDE THE UNADJUSTED INTERVAL, NEVER INSTEAD OF IT, per the house
# rule: metafor's own knha statistic, and at small k the t critical value is what makes the
# interval honest rather than what makes it look bad.

suppressWarnings(suppressMessages(library(metafor)))
library(jsonlite)

args  <- commandArgs(trailingOnly = TRUE)
topic <- args[1]
outcome <- args[2]
# THE REPO IS DERIVED, NOT HARDCODED. This read "F:/rapidmeta-ssot-shell" -- an
# absolute path into ANOTHER lane's worktree, so the script silently fitted a
# different clone's object or failed outright depending on who ran it. Same class as
# the three scripts already recorded for defaulting into a foreign worktree.
# RMF_REPO overrides; otherwise the repo is the parent of this script's directory.
repo <- Sys.getenv("RMF_REPO")
if (!nzchar(repo)) {
  a <- commandArgs(trailingOnly = FALSE)
  f <- sub("^--file=", "", a[grep("^--file=", a)])
  repo <- if (length(f)) dirname(dirname(normalizePath(f[1]))) else getwd()
}

path <- file.path(repo, "ssot", topic, paste0(topic, ".json"))
obj  <- fromJSON(path, simplifyVector = FALSE)
blk  <- obj$results$by_outcome[[outcome]]
rows <- blk$per_trial

ids <- vapply(rows, function(r) as.character(r$trial_id), character(1))
pt  <- vapply(rows, function(r) as.numeric(r$point),      numeric(1))
lo  <- vapply(rows, function(r) as.numeric(r$ci_low),     numeric(1))
hi  <- vapply(rows, function(r) as.numeric(r$ci_high),    numeric(1))

# SCALE IS READ FROM THE MEASURE, NOT ASSUMED.
#
# This script log-transformed unconditionally. That is right for RR, OR, HR and IRR and
# WRONG for a MEAN DIFFERENCE: incretin-hfpef-review/kccq_css_change is MD 7.43 (5.09 to
# 9.77) KCCQ points, and log(7.43) estimates nothing. Running it anyway would have produced
# a number that looked like a fit and was not one -- and P46 limb 4 stores the output
# VERBATIM, so it would have shipped as our engine`s word.
# THE MEASURE IS NOT ALWAYS IN THE SAME PLACE. Some blocks carry it on `pooled$measure`
# and some on the block itself; cangrelor-pci-review/corrected_composite_3component has
# `measure: "RR"` at block level and NO measure inside `pooled`, so reading only the inner
# one gave character(0) and the scale test failed with "missing value where TRUE/FALSE
# needed". Both places, and a refusal if neither carries it -- never a default.
meas_raw <- blk$pooled$measure
if (is.null(meas_raw)) meas_raw <- blk$measure
if (is.null(meas_raw)) stop("REFUSED: no measure on the pooled block or the outcome block.")
meas <- toupper(as.character(meas_raw))
logscale <- meas %in% c("RR", "OR", "HR", "IRR", "RATE RATIO", "RISK RATIO", "ODDS RATIO")
if (!logscale && !(meas %in% c("MD", "SMD", "RD", "MEAN DIFFERENCE"))) {
  stop(sprintf(paste0("REFUSED: measure %s is neither a recognised ratio nor a recognised ",
                      "difference. Guessing the scale is how a mean difference gets logged."),
               meas))
}
bt <- if (logscale) exp else function(x) x

yi  <- if (logscale) log(pt) else pt
sei <- if (logscale) (log(hi) - log(lo)) / (2 * qnorm(0.975)) else (hi - lo) / (2 * qnorm(0.975))

cat(R.version.string, "\n")
cat("metafor", as.character(packageVersion("metafor")), "\n")
cat("run_utc 2026-08-21\n")
cat("\n================================================================\n")
cat(sprintf("TOPIC   %s\n", topic))
cat(sprintf("OUTCOME %s\n", outcome))
cat(sprintf("STORED  %s %.4f (%.4f to %.4f), k = %s, %s / %s\n",
            blk$pooled$measure, blk$pooled$point, blk$pooled$ci_low, blk$pooled$ci_high,
            blk$k, blk$model, blk$estimator_used))
cat(sprintf("INPUTS READ FROM THE OBJECT (%s scale, SE derived from the published interval):
",
            if (logscale) "log" else "natural"))
for (i in seq_along(ids)) {
  cat(sprintf("   %-16s %.4f (%.4f to %.4f)  yi=%+.6f  sei=%.6f\n",
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
cat(sprintf("   unadjusted     %.4f (%.4f to %.4f)\n",
            bt(m$b[1]), bt(m$ci.lb), bt(m$ci.ub)))
# BOTH HARTUNG-KNAPP INTERVALS, AND THE FLOORED ONE IS THE HOUSE INTERVAL.
#
# metafor's raw knha can NARROW the interval below the unadjusted one whenever Q < k - 1,
# because the variance-inflation factor sqrt(Q/(k-1)) is then less than 1. This project's
# house rule FLOORS that factor at 1 -- the recognised modification for exactly this
# instability -- so an adjustment can never manufacture precision it did not earn.
#
# THIS SCRIPT PRINTED ONLY THE RAW INTERVAL, and its output is stored VERBATIM as P46 limb 4.
# On malaria-vaccines / rtss_recurrent_children_final, Q = 0.0013 against 1 df and the raw
# knha interval is 0.6273 to 0.6473 where the UNADJUSTED interval is 0.5967 to 0.6805 --
# four times narrower. A reader meeting the stored output would have met, quoted as our own
# model output, an interval this project's own rule forbids.
# THE FACTOR IS THE SE RATIO, NOT sqrt(Q/(k-1)).
#
# The first version of this block used sqrt(Q / (k - 1)) as the inflation factor. That is
# the textbook expression, and it DOES NOT REPRODUCE WHAT THIS CORPUS STORES. On
# cab-prep-hiv-review it gives 1.7910 where the object stores `variance_inflation_applied:
# 1.0`, and the resulting interval was 0.0000 to 50888.9 against the stored 0.0002 to
# 211.7767 -- because metafor has already absorbed the adjustment into its knha standard
# error, so multiplying again DOUBLE-COUNTS it.
#
# The factor this project actually applies is max(1, SE_knha / SE_unadjusted). It reproduces
# every stored value checked: agyw 0.3918 -> floored to 1, cab 1.0000, and both malaria
# pools floored to 1. Caught by comparing the computed interval against what the objects
# already held, which is the only reason a wrong formula did not reach a page as limb 4.
se_un <- m$se
raw_f <- mk$se / m$se
infl  <- max(1, raw_f)
tcrit <- qt(0.975, m$k - 1)
cat(sprintf("   Hartung-Knapp  %.4f (%.4f to %.4f)   [t crit %.4f on %d df]  <- HOUSE INTERVAL, inflation factor floored at 1 (raw %.4f)\n",
            bt(m$b[1]), bt(m$b[1] - tcrit * se_un * infl),
            bt(m$b[1] + tcrit * se_un * infl), tcrit, m$k - 1, raw_f))
cat(sprintf("   metafor raw    %.4f (%.4f to %.4f)   [test=knha, UNFLOORED]%s\n",
            bt(mk$b[1]), bt(mk$ci.lb), bt(mk$ci.ub),
            ifelse((bt(mk$ci.ub) - bt(mk$ci.lb)) < (bt(m$ci.ub) - bt(m$ci.lb)),
                   "  *** NARROWER THAN UNADJUSTED -- NOT USED; this is what the floor prevents ***",
                   "")))
cat(sprintf("   tau^2 %.6f   Q %.4f on %d df, p = %.4f   I^2 %.2f%%\n",
            m$tau2, m$QE, m$k - 1, m$QEp, m$I2))
cat(sprintf("\nAGREES WITH THE STORED POINT TO 4 dp: %s\n",
            ifelse(abs(bt(m$b[1]) - blk$pooled$point) < 1e-4, "YES", "NO")))
