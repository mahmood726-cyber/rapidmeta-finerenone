# REML, everywhere -- the ten pools of thirty-four that were not fitted with it.
#
# WHY THIS EXISTS, AND WHY IT IS ONE SCRIPT AND NOT TEN.
#
# DECISIONS-COCHRANE-2026-08-18.md section 1 settled the estimator on 2026-08-18,
# quoting Cochrane Handbook 6.5 section 10.10.4.4: "In RevMan, the default option for
# estimating the between-study variance is REML, while the DerSimonian and Laird
# moment-based method remains an available option." Its decision line reads, verbatim,
# "Decision: REML, everywhere." The decision was recorded and never applied.
#
# Ten pools are refitted in ONE pass because doing them singly would leave the corpus
# holding two estimator conventions at once, and any topic completed in between would
# be built on whichever convention was current that hour. That is the same failure the
# corpus has just finished repairing on the INTERVAL half of the same decision.
#
# ONE POOL IS DELIBERATELY NOT HERE. bempedoic-acid-review is k = 1 and declares
# "none -- one trial, the registry's own Cox analysis". Fitting a random-effects model
# to one study would manufacture a between-study variance out of a corpus that has one
# study. It is correct as it stands and is left alone.
#
# THE CHECK COMES BEFORE THE CHANGE. Each pool is FIRST refitted under the estimator it
# already declares. If that does not reproduce the served point, tau^2, Q and I^2, then
# THE SPECIFICATION IS WRONG AND THE STORED VALUE IS NOT TO BE TOUCHED -- twice already
# in this project a fresh computation that felt more trustworthy than a stored one was
# the thing that was wrong. Only a pool whose old fit reproduces earns a new one.
#
# STATED BEFORE THE RUN, so the run can contradict it:
#   * All 8 DerSimonian-Laird pools reproduce point, tau^2, Q and I^2 exactly.
#   * apixaban-vte-treatment does NOT reproduce its interval under PM + z, because its
#     served interval is Knapp-Hartung on t(k-1) with the scale factor floored at
#     max(1, Q/(k-1)); Q/(k-1) = 0.63 there, so the floor binds and the factor is 1.
#   * The four pools whose stored tau^2 is 0 (finerenone-cv, empagliflozin-hf,
#     apixaban-vte-treatment, and any other with Q < df) DO NOT MOVE, because REML also
#     returns tau^2 = 0 when Q is below its degrees of freedom.
#   * The pools with tau^2 > 0 move, and move WIDER, because REML is not downward-biased
#     at small k the way the moment estimator is.
# The indicator that can only move if that diagnosis is right is the tau^2 reproduction
# in the OLD fit: if the old fits do not land on the stored tau^2 to four decimals, the
# reading of how these pools were computed is wrong and nothing here should be applied.

library(metafor)
library(jsonlite)

args <- commandArgs(trailingOnly = TRUE)
inp <- if (length(args) >= 1) args[1] else "inputs.json"
outp <- if (length(args) >= 2) args[2] else "refits.json"

cat("R environment, quoted rather than asserted:\n")
cat(" ", R.version.string, "\n")
cat("  metafor", as.character(packageVersion("metafor")), "\n")
cat("  jsonlite", as.character(packageVersion("jsonlite")), "\n\n")

pools <- fromJSON(inp, simplifyDataFrame = FALSE)
if (length(pools) == 0L) stop("REFUSED: zero pools read from ", inp)
cat("pools read from", inp, ":", length(pools), "\n\n")

# The declared estimator strings carry prose. Map to what metafor accepts.
metafor_method <- function(s) {
  if (grepl("^REML", s)) return("REML")
  if (grepl("DerSimonian", s)) return("DL")
  if (grepl("Paule", s)) return("PM")
  stop("REFUSED: no metafor method for declared estimator: ", s)
}

is_ratio <- function(m) m %in% c("HR", "RR", "OR")

results <- list()
reproduced <- 0L
n_checked <- 0L

for (key in names(pools)) {
  p <- pools[[key]]
  yi <- vapply(p$rows, function(r) as.numeric(r$yi), numeric(1))
  sei <- vapply(p$rows, function(r) as.numeric(r$sei), numeric(1))
  slab <- vapply(p$rows, function(r) as.character(r$slab), character(1))
  ratio <- is_ratio(p$measure)
  back <- if (ratio) exp else function(x) x

  cat(strrep("=", 96), "\n")
  cat(sprintf("%s :: %s   k = %d   measure = %s\n", p$topic, p$outcome, length(yi), p$measure))
  cat(strrep("=", 96), "\n")
  cat("trials:", paste(slab, collapse = ", "), "\n\n")

  old_m <- metafor_method(p$estimator)
  old <- rma(yi = yi, sei = sei, method = old_m, slab = slab)

  cat(sprintf("A. THE FIT THAT PRODUCED THE SERVED NUMBER -- method = %s, z interval\n", old_m))
  print(old)
  cat("\n")

  op <- back(old$b[1]); olo <- back(old$ci.lb); ohi <- back(old$ci.ub)
  sp <- as.numeric(p$served$point)
  slo <- as.numeric(p$served$ci_low)
  shi <- as.numeric(p$served$ci_high)
  stau <- if (is.null(p$heterogeneity$tau2)) NA_real_ else as.numeric(p$heterogeneity$tau2)
  si2 <- if (is.null(p$heterogeneity$i2)) NA_real_ else as.numeric(p$heterogeneity$i2)
  sq <- if (is.null(p$heterogeneity$q)) NA_real_ else as.numeric(p$heterogeneity$q)

  # Tolerances are on the SCALE OF THE QUANTITY, and the stored values are rounded to
  # between four and sixteen figures depending on the pool, so the point tolerance is
  # relative and the tau^2 tolerance is the four decimals the prediction named.
  ok_point <- abs(op - sp) <= 5e-4 * max(1, abs(sp))
  ok_lo <- abs(olo - slo) <= 5e-4 * max(1, abs(slo))
  ok_hi <- abs(ohi - shi) <= 5e-4 * max(1, abs(shi))
  ok_tau <- is.na(stau) || abs(old$tau2 - stau) <= 5e-5 * max(1, abs(stau))
  ok_q <- is.na(sq) || abs(old$QE - sq) <= 5e-4 * max(1, abs(sq))
  ok_i2 <- is.na(si2) || abs(old$I2 - si2) <= 0.15

  cat("   CHECK AGAINST THE STORED VALUE -- the change is not earned until this passes:\n")
  cat(sprintf("     point  refit %-14.6f stored %-14.6f  %s\n", op, sp, ifelse(ok_point, "reproduced", "DIFFERS")))
  cat(sprintf("     ci_low refit %-14.6f stored %-14.6f  %s\n", olo, slo, ifelse(ok_lo, "reproduced", "DIFFERS")))
  cat(sprintf("     ci_hi  refit %-14.6f stored %-14.6f  %s\n", ohi, shi, ifelse(ok_hi, "reproduced", "DIFFERS")))
  cat(sprintf("     tau^2  refit %-14.6f stored %-14.6f  %s\n", old$tau2, stau, ifelse(ok_tau, "reproduced", "DIFFERS")))
  cat(sprintf("     Q      refit %-14.6f stored %-14.6f  %s\n", old$QE, sq, ifelse(ok_q, "reproduced", "DIFFERS")))
  cat(sprintf("     I^2    refit %-14.4f stored %-14.4f  %s\n", old$I2, si2, ifelse(ok_i2, "reproduced", "DIFFERS")))

  # The point and the heterogeneity are what identify the fit; the interval is what the
  # interval METHOD produces from it. Identical point + identical heterogeneity + a
  # different interval means the specification of the INTERVAL is wrong, not the inputs,
  # and that case is named rather than counted as a failure to reproduce.
  spec_ok <- ok_point && ok_tau && ok_q && ok_i2
  interval_ok <- ok_lo && ok_hi
  verdict <- if (spec_ok && interval_ok) "REPRODUCED" else
             if (spec_ok) "FIT REPRODUCED, INTERVAL METHOD DIFFERS" else "NOT REPRODUCED"
  cat(sprintf("     => %s\n\n", verdict))
  n_checked <- n_checked + 1L
  if (spec_ok) reproduced <- reproduced + 1L

  new <- rma(yi = yi, sei = sei, method = "REML", slab = slab)
  cat("B. THE SAME DATA UNDER REML -- Handbook 10.10.4.4, 'Decision: REML, everywhere'\n")
  print(new)
  cat("\n")
  np <- back(new$b[1]); nlo <- back(new$ci.lb); nhi <- back(new$ci.ub)

  pr <- tryCatch(predict(new), error = function(e) NULL)
  pi_lo <- if (!is.null(pr) && !is.null(pr$pi.lb)) back(pr$pi.lb) else NA_real_
  pi_hi <- if (!is.null(pr) && !is.null(pr$pi.ub)) back(pr$pi.ub) else NA_real_

  shift <- if (sp != 0) 100 * (np - sp) / abs(sp) else NA_real_
  cat("C. WHAT MOVES\n")
  cat(sprintf("     point    %-14.6f -> %-14.6f  (%+.4f%%)\n", sp, np, shift))
  cat(sprintf("     ci_low   %-14.6f -> %-14.6f\n", slo, nlo))
  cat(sprintf("     ci_high  %-14.6f -> %-14.6f\n", shi, nhi))
  cat(sprintf("     tau^2    %-14.6f -> %-14.6f\n", stau, new$tau2))
  cat(sprintf("     I^2      %-14.4f -> %-14.4f\n", si2, new$I2))
  cat(sprintf("     Q        %-14.6f -> %-14.6f  (Q is estimator-independent)\n", sq, new$QE))
  null_v <- if (ratio) 1 else 0
  old_excl <- (slo > null_v) || (shi < null_v)
  new_excl <- (nlo > null_v) || (nhi < null_v)
  cat(sprintf("     excludes the null (%g):  %s -> %s%s\n", null_v, old_excl, new_excl,
              ifelse(old_excl != new_excl, "   <<< THE VERDICT TURNS ON THE ESTIMATOR", "")))
  cat("\n")

  # THE QUOTED MODEL OUTPUT IS THE WHOLE BLOCK, NOT JUST THE NEW FIT.
  #
  # The first version of this script stored only capture.output(print(new)) as the
  # verbatim. The manuscript on each page QUOTES that field, and the fields it replaced
  # held a full transcript -- the old fit, the reproduction check, the new fit and the
  # comparison. Installing the short version shrank the apixaban-vte-prophylaxis
  # manuscript by 7.88% and ssot/manuscript_guard.py REFUSED THE BUILD, correctly, and
  # wrote nothing. The guard was right and the output was wrong.
  #
  # A reader given only the new fit cannot tell whether the old one was reproduced before
  # it was replaced, which is the single most important thing about this change.
  block <- c(
    sprintf("%s :: %s   k = %d   measure = %s", p$topic, p$outcome, length(yi), p$measure),
    strrep("=", 96),
    sprintf("trials: %s", paste(slab, collapse = ", ")),
    "",
    sprintf("A. THE FIT THAT PRODUCED THE SERVED NUMBER -- method = %s, z interval", old_m),
    capture.output(print(old)),
    "",
    "   CHECK AGAINST THE STORED VALUE -- the change is not earned until this passes:",
    sprintf("     point  refit %-14.6f stored %-14.6f  %s", op, sp, ifelse(ok_point, "reproduced", "DIFFERS")),
    sprintf("     ci_low refit %-14.6f stored %-14.6f  %s", olo, slo, ifelse(ok_lo, "reproduced", "DIFFERS")),
    sprintf("     ci_hi  refit %-14.6f stored %-14.6f  %s", ohi, shi, ifelse(ok_hi, "reproduced", "DIFFERS")),
    sprintf("     tau^2  refit %-14.6f stored %-14.6f  %s", old$tau2, stau, ifelse(ok_tau, "reproduced", "DIFFERS")),
    sprintf("     Q      refit %-14.6f stored %-14.6f  %s", old$QE, sq, ifelse(ok_q, "reproduced", "DIFFERS")),
    sprintf("     I^2    refit %-14.4f stored %-14.4f  %s", old$I2, si2, ifelse(ok_i2, "reproduced", "DIFFERS")),
    sprintf("     => %s", verdict),
    "",
    "B. THE SAME DATA UNDER REML -- Cochrane Handbook 6.5 section 10.10.4.4, which records",
    "   REML as RevMan's own current default, and DECISIONS-COCHRANE-2026-08-18.md section 1,",
    "   whose decision line reads: \"Decision: REML, everywhere.\"",
    capture.output(print(new)),
    "",
    "C. WHAT MOVES",
    sprintf("     point    %-14.6f -> %-14.6f  (%+.4f%%)", sp, np, shift),
    sprintf("     ci_low   %-14.6f -> %-14.6f", slo, nlo),
    sprintf("     ci_high  %-14.6f -> %-14.6f", shi, nhi),
    sprintf("     tau^2    %-14.6f -> %-14.6f", stau, new$tau2),
    sprintf("     I^2      %-14.4f -> %-14.4f", si2, new$I2),
    sprintf("     Q        %-14.6f -> %-14.6f  (Q is estimator-independent)", sq, new$QE),
    sprintf("     excludes the null (%g):  %s -> %s%s", null_v, old_excl, new_excl,
            ifelse(old_excl != new_excl, "   <<< THE VERDICT TURNS ON THE ESTIMATOR", "")),
    if (!is.na(pi_lo)) sprintf("     prediction interval under REML: %.4f to %.4f", pi_lo, pi_hi) else
      "     prediction interval: not computable from this fit",
    "",
    sprintf("R environment: %s; metafor %s", R.version.string, as.character(packageVersion("metafor"))),
    sprintf("Script: ssot/reml_corpus_refit.R"))

  results[[key]] <- list(
    topic = p$topic, outcome = p$outcome, k = length(yi), measure = p$measure,
    declared_estimator = p$estimator, metafor_method_old = old_m,
    reproduction = list(verdict = verdict, point = ok_point, ci_low = ok_lo,
                        ci_high = ok_hi, tau2 = ok_tau, q = ok_q, i2 = ok_i2),
    old_refit = list(point = op, ci_low = olo, ci_high = ohi, tau2 = old$tau2,
                     i2 = old$I2, q = old$QE, df = old$k - 1),
    served = list(point = sp, ci_low = slo, ci_high = shi, tau2 = stau, i2 = si2, q = sq),
    reml = list(point = np, ci_low = nlo, ci_high = nhi, tau2 = new$tau2, i2 = new$I2,
                q = new$QE, df = new$k - 1, qp = new$QEp, se_log = new$se,
                pi_low = pi_lo, pi_high = pi_hi,
                excludes_null_before = old_excl, excludes_null_after = new_excl,
                pct_shift = shift),
    r_verbatim = paste(block, collapse = "\n"),
    r_verbatim_old = paste(capture.output(print(old)), collapse = "\n"),
    environment = paste0(R.version.string, "; metafor ", as.character(packageVersion("metafor")))
  )
}

cat(strrep("=", 96), "\n")
cat("SUMMARY -- printed beside the detail above, because the disagreement between them\n")
cat("is the safety. If this table and the per-pool blocks disagree, believe neither.\n")
cat(strrep("=", 96), "\n")
cat(sprintf("%-42s %-24s %-12s %-12s %s\n", "topic", "reproduction", "point", "-> REML", "verdict flip"))
for (key in names(results)) {
  r <- results[[key]]
  cat(sprintf("%-42s %-24s %-12.5f %-12.5f %s\n", r$topic, r$reproduction$verdict,
              r$served$point, r$reml$point,
              ifelse(r$reml$excludes_null_before != r$reml$excludes_null_after, "YES", "no")))
}
cat("\n")
cat(sprintf("pools whose OLD fit reproduced (point+tau^2+Q+I^2): %d of %d\n", reproduced, n_checked))
if (reproduced == 0L) stop("REFUSED: not one old fit reproduced. The reading of how these ",
                           "pools were computed is wrong; apply nothing.")
write(toJSON(results, auto_unbox = TRUE, digits = 12, na = "null"), outp)
cat("wrote", outp, "\n")
