# iv-iron-hf: independent recomputation of all four k=2 pools. Verbatim output.
#
# Four outcomes pool; two do not. The two that do not are NOT failures and each has its own
# distinct reason, already recorded on the object:
#
#   hierarchical_primary  WIN_RATIO, k=1 -- the FORM would prevent pooling even at k=2: it
#                         counts PAIRS of participants rather than participants or events, its
#                         direction of benefit is inverted relative to every other ratio here,
#                         and its interval is not at the level the others use.
#   six_min_walk_24w      MD, k=1 -- a DATA-AVAILABILITY limit, explicitly not a form limit:
#                         only one staged source prints an extractable between-arm difference.
#                         A mean difference in metres pools by generic inverse variance like
#                         any other, so this is recoverable with full texts.
#
# The four below share, within each pool, one measure, one estimand family and ONE UNIT OF
# ANALYSIS. Across pools the units differ -- event, hospitalisation, participant -- which is
# why they are four pools and not one.

library(metafor)

fit <- function(label, unit, nct, est, lo, hi) {
  yi  <- log(est)
  sei <- (log(hi) - log(lo)) / (2 * qnorm(0.975))
  cat("\n", strrep("=", 78), "\n", label, "\n  unit of analysis: ", unit, "\n",
      strrep("=", 78), "\n", sep = "")
  res <- rma(yi = yi, sei = sei, method = "REML", slab = nct)
  print(res)
  cat("\nBack-transformed:\n")
  print(predict(res, transf = exp))
  invisible(res)
}

cat(R.version.string, "\n")
cat("metafor", as.character(packageVersion("metafor")), "\n")

fit("hfh_cvd_recurrent -- recurrent HF hospitalisations WITH CV death, rate ratio",
    "event: each participant contributes every qualifying event",
    c("NCT02937454 AFFIRM-AHF", "NCT02642562 IRONMAN"),
    c(0.79, 0.82), c(0.62, 0.66), c(1.01, 1.02))

fit("hfh_cvd_first -- FIRST CV death or HF hospitalisation, hazard ratio",
    "participant: time to the first component event",
    c("NCT02937454 AFFIRM-AHF", "NCT03036462 FAIR-HF2"),
    c(0.80, 0.79), c(0.66, 0.63), c(0.98, 0.99))

fit("hfh_recurrent -- recurrent HF hospitalisations ALONE, no death component, rate ratio",
    "hospitalisation: each participant contributes every hospitalisation",
    c("NCT02937454 AFFIRM-AHF", "NCT03036462 FAIR-HF2"),
    c(0.74, 0.80), c(0.58, 0.60), c(0.94, 1.06))

fit("acm -- death from ANY cause, hazard ratio",
    "participant: time to death from any cause",
    c("NCT02937454 AFFIRM-AHF", "NCT01453608 CONFIRM-HF"),
    c(0.99, 0.89), c(0.75, 0.41), c(1.31, 1.93))

cat("\n", strrep("=", 78), "\n", sep = "")
cat("Four pools, four units of analysis. They are not alternatives and none supersedes\n")
cat("another: hfh_cvd_recurrent and hfh_recurrent differ by whether CV death is a\n")
cat("qualifying event, and hfh_cvd_first differs from both by counting participants\n")
cat("rather than events. A single 'HF hospitalisation' headline would collapse three\n")
cat("distinct quantities into one.\n")
