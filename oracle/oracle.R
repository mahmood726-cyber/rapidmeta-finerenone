# External oracle: R / metafor recomputes every pooled estimate independently.
#
# THE PIN IS READ BACK FROM THE FIT, NEVER FROM THE CALL. `fit$method` and
# `fit$test` are what metafor actually used; the arguments we passed are only what
# we asked for. Configuration is not evidence about a run -- the same rule the
# model-pinning guard enforces, applied to the statistics engine.
#
# METHOD MATCHING: an estimate computed WITH Hartung-Knapp and one computed
# WITHOUT are two different quantities. Each case is fitted under BOTH and both are
# emitted, so the comparison downstream can pick the matching one rather than
# silently comparing across methods.
#
# Output is verbatim: the printed metafor summary is captured per case and stored,
# so no number in the report is paraphrased out of R.

suppressMessages(library(metafor))
suppressMessages(library(jsonlite))

args <- commandArgs(trailingOnly = TRUE)
infile  <- if (length(args) >= 1) args[1] else "cases.json"
outfile <- if (length(args) >= 2) args[2] else "oracle_out.json"

dat <- fromJSON(infile, simplifyVector = FALSE)
cases <- dat$cases
res <- vector("list", length(cases))

cat(sprintf("R: %s | metafor %s | cases %d\n",
            R.version.string, as.character(packageVersion("metafor")),
            length(cases)))

for (i in seq_along(cases)) {
  cs <- cases[[i]]
  yi  <- as.numeric(unlist(cs$yi))
  sei <- as.numeric(unlist(cs$sei))
  rec <- list(topic = cs$topic, outcome = cs$outcome, k = length(yi),
              measure = cs$measure, log_scale = cs$log_scale)

  fit_one <- function(knha) {
    tryCatch({
      f <- rma(yi = yi, sei = sei, method = "REML", test = if (knha) "knha" else "z")
      pr <- paste(capture.output(print(f)), collapse = "\n")
      list(
        ok = TRUE,
        # THE PIN, READ BACK FROM THE FIT OBJECT ITSELF
        method_used = as.character(f$method),
        test_used   = as.character(f$test),
        knha_used   = isTRUE(f$test == "knha"),
        b = as.numeric(f$b)[1], se = as.numeric(f$se)[1],
        ci_lb = as.numeric(f$ci.lb)[1], ci_ub = as.numeric(f$ci.ub)[1],
        tau2 = as.numeric(f$tau2)[1], I2 = as.numeric(f$I2)[1],
        QE = as.numeric(f$QE)[1], QEp = as.numeric(f$QEp)[1],
        verbatim = pr)
    }, error = function(e) list(ok = FALSE, error = conditionMessage(e)))
  }

  rec$z    <- fit_one(FALSE)
  rec$knha <- fit_one(TRUE)
  res[[i]] <- rec
  if (i %% 25 == 0) cat(sprintf("  ...%d/%d\n", i, length(cases)))
}

write(toJSON(list(
  r_version = R.version.string,
  metafor_version = as.character(packageVersion("metafor")),
  n = length(res), results = res), auto_unbox = TRUE, digits = 12, null = "null"),
  file = outfile)
cat(sprintf("wrote %s\n", outfile))
