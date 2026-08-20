# Does every stored I-squared reproduce from the values the object stores?
#
# WHY. bococizumab-lipid-review stores heterogeneity.i2 = 41.5 and a REML refit of its own
# six per-trial values gives 56.66. THE POINT ESTIMATE REPRODUCED TO 0.0006 AND THE
# DISPERSION DID NOT. That is the second case tonight where the point survives a refit and
# the precision or dispersion claim does not -- the first being the house-rule
# Hartung-Knapp interval, where a k=2 pool's interval crossed the null under t on one
# degree of freedom while the point never moved.
#
# AND THE REASON IT SURVIVES IS STRUCTURAL: EVERY CHECK THIS PROJECT HAS TESTS THE POINT.
# The regression check reads the rendered estimate; the displayable-precision lint reads the
# point; the invariance check compares numbers as a multiset. A dispersion claim that
# diverges leaves the point untouched, so nothing fires.
#
# Refits every pool with a stored I-squared using metafor REML on the values the object
# itself stores, and reports divergence. NOT A CORRECTION -- a measurement.

suppressMessages(library(metafor))
suppressMessages(library(jsonlite))

args <- commandArgs(trailingOnly = TRUE)
d <- fromJSON(args[1], simplifyVector = FALSE)
rows <- d$rows

cat(sprintf("%-44s %-30s %3s %8s %8s %9s\n",
            "topic", "outcome", "k", "storedI2", "refitI2", "delta"))
cat(strrep("-", 108), "\n")

n_div <- 0
n_ok <- 0
n_fail <- 0
for (r in rows) {
  yi <- as.numeric(unlist(r$yi))
  sei <- as.numeric(unlist(r$sei))
  stored <- as.numeric(r$stored_i2)
  fit <- try(rma(yi = yi, sei = sei, method = "REML"), silent = TRUE)
  if (inherits(fit, "try-error")) {
    n_fail <- n_fail + 1
    cat(sprintf("%-44s %-30s %3d %8.1f %8s %9s\n",
                substr(r$topic, 1, 44), substr(r$oid, 1, 30), length(yi), stored,
                "FIT FAILED", ""))
    next
  }
  refit <- fit$I2
  delta <- abs(refit - stored)
  # A tenth of a percentage point is rounding. Anything above one point is a different
  # number, not a different rounding.
  if (delta > 1.0) {
    n_div <- n_div + 1
    flag <- "  <== DIVERGES"
  } else {
    n_ok <- n_ok + 1
    flag <- ""
  }
  cat(sprintf("%-44s %-30s %3d %8.1f %8.1f %9.1f%s\n",
              substr(r$topic, 1, 44), substr(r$oid, 1, 30), length(yi),
              stored, refit, delta, flag))
}

cat("\n")
cat(sprintf("POOLS REFITTED            %d\n", n_ok + n_div + n_fail))
cat(sprintf("  stored I2 reproduces    %d   (within 1.0 percentage point)\n", n_ok))
cat(sprintf("  stored I2 DIVERGES      %d\n", n_div))
cat(sprintf("  refit failed            %d   reported, not skipped\n", n_fail))
cat("\n")
cat("THE POPULATION IS EVERY POOL CARRYING A STORED I-SQUARED WHOSE PER-TRIAL VALUES ARE\n")
cat("SUFFICIENT TO REFIT. A pool without both is not counted as agreeing -- it is not in\n")
cat("the denominator at all, and the extraction step reports how many those were.\n")
cat("\n")
cat("REML IS THE COMPARISON ESTIMATOR BECAUSE IT IS THE HOUSE RULE -- DECISIONS-COCHRANE-\n")
cat("2026-08-18 section 1, Handbook 6.5 section 10.10.4.4. A pool fitted under\n")
cat("DerSimonian-Laird will diverge here BY DESIGN, and that is a finding about which\n")
cat("estimator produced the stored number, not proof that the stored number was wrong.\n")
