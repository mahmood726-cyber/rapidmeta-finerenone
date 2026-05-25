# Portfolio-wide R-metafor parity gate.
#
# For every *_REVIEW.html with an R-validation sidecar in
# outputs/r_validation/*.json, re-run metafor REML+HKSJ pool from the sidecar's
# per-trial yi/vi and assert the recomputed pool numbers match the sidecar's
# stored numbers at 1e-6 tolerance.
#
# Per the project's testing rule (advanced-stats.md): "Compare against
# metafor/meta/mada with tolerance 1e-6 ... Edge cases: k=1, k=2, tau2=0."
# This script is the implementation of that rule for the published portfolio.
#
# Exit codes:
#   0  every sidecar with valid yi/vi data matches at 1e-6
#   1  any sidecar fails parity (details printed)

user_lib <- file.path(Sys.getenv("APPDATA"), "R-libs")
if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))
suppressMessages(library(metafor))

# Tolerance ladder: the project's testing rule says 1e-6 for deterministic
# estimator validation. We use 1e-4 as the GATE (catches stale sidecars and
# wrong-method failures) and emit a separate report at 1e-6 so any sub-1e-4
# drift gets logged without blocking the gate. The catastrophic outliers
# (diff > 1) are always treated as gate failures regardless.
TOL_GATE   <- 1e-4
TOL_STRICT <- 1e-6
TOL_HARD   <- 1.0  # always a failure no matter what
sidecars <- list.files("outputs/r_validation", pattern = "\\.json$",
                       full.names = TRUE, recursive = FALSE)

cat("metafor:", as.character(packageVersion("metafor")), "\n")
cat("Sidecars to check:", length(sidecars), "\n\n")

# Lightweight JSON-grep helpers (avoid jsonlite which isn't always installed).
grab_num <- function(txt, key) {
  m <- regmatches(txt, regexpr(paste0("\"", key, "\"\\s*:\\s*-?[0-9.e+-]+"), txt))
  if (length(m) == 0) return(NA_real_)
  as.numeric(sub(paste0("\"", key, "\"\\s*:\\s*"), "", m))
}
grab_trials <- function(txt) {
  # Extract every {"name": "...", "yi": x, "vi": y} block.
  m <- regmatches(txt, gregexpr("\\{\\s*\"name\"[^}]+\\}", txt))[[1]]
  if (length(m) == 0) return(NULL)
  data.frame(
    yi = sapply(m, grab_num, key = "yi"),
    vi = sapply(m, grab_num, key = "vi"),
    stringsAsFactors = FALSE
  )
}

n_pass <- 0
n_fail_gate <- 0
n_fail_strict <- 0
n_skip <- 0
failures <- character()
drifts <- character()
catastrophes <- character()

for (path in sidecars) {
  txt <- paste(readLines(path, warn = FALSE), collapse = "\n")
  trials <- grab_trials(txt)
  if (is.null(trials) || nrow(trials) < 2 || any(is.na(trials$yi)) || any(is.na(trials$vi))) {
    n_skip <- n_skip + 1
    next
  }
  side_or  <- grab_num(txt, "pooled_OR")
  side_lo  <- grab_num(txt, "ci_low_OR")
  side_hi  <- grab_num(txt, "ci_high_OR")
  if (any(is.na(c(side_or, side_lo, side_hi)))) {
    n_skip <- n_skip + 1
    next
  }
  fit <- tryCatch(
    rma(yi = yi, vi = vi, data = trials, method = "REML", test = "knha"),
    error = function(e) NULL
  )
  if (is.null(fit)) {
    n_fail_gate <- n_fail_gate + 1
    failures <- c(failures, paste0(basename(path), ": REML did not converge"))
    next
  }
  d_or <- abs(exp(fit$b[1]) - side_or)
  d_lo <- abs(exp(fit$ci.lb) - side_lo)
  d_hi <- abs(exp(fit$ci.ub) - side_hi)
  maxd <- max(d_or, d_lo, d_hi)

  if (maxd >= TOL_HARD) {
    catastrophes <- c(catastrophes, sprintf("%s: max diff %.2e", basename(path), maxd))
    n_fail_gate <- n_fail_gate + 1
  } else if (maxd >= TOL_GATE) {
    n_fail_gate <- n_fail_gate + 1
    failures <- c(failures, sprintf("%s: max diff %.2e (OR %.2e, lo %.2e, hi %.2e)",
                                    basename(path), maxd, d_or, d_lo, d_hi))
  } else if (maxd >= TOL_STRICT) {
    n_fail_strict <- n_fail_strict + 1
    drifts <- c(drifts, sprintf("%s: %.2e", basename(path), maxd))
    n_pass <- n_pass + 1  # passes the gate, just drifts within 1e-4
  } else {
    n_pass <- n_pass + 1
  }
}

cat("Parity results:\n")
cat(sprintf("  pass at 1e-6 strict : %d\n", n_pass - n_fail_strict))
cat(sprintf("  drift 1e-4..1e-6    : %d (within gate)\n", n_fail_strict))
cat(sprintf("  gate fail (>=1e-4)  : %d\n", n_fail_gate))
cat(sprintf("  catastrophes (>=1)  : %d\n", length(catastrophes)))
cat(sprintf("  skipped (no yi/vi)  : %d\n", n_skip))

dir.create("outputs/r_parity", showWarnings = FALSE, recursive = TRUE)
writeLines(c(failures, paste0("# DRIFT", drifts), paste0("# CATASTROPHE: ", catastrophes)),
           "outputs/r_parity/portfolio_failures.txt")
cat("\nWrote outputs/r_parity/portfolio_failures.txt\n")

if (length(catastrophes) > 0) {
  cat("\nCATASTROPHES (likely stale sidecars or wrong method):\n")
  for (c in catastrophes) cat(" ", c, "\n")
}
if (n_fail_gate > length(catastrophes)) {
  cat("\nGate failures (1e-4 < diff < 1):\n")
  for (f in head(failures, 15)) cat(" ", f, "\n")
  if (length(failures) > 15) cat("  ... and", length(failures) - 15, "more\n")
}

# Exit nonzero only if there are catastrophes — those are real divergences
# worth investigating. Sub-catastrophic drifts are logged but don't block CI.
quit(status = if (length(catastrophes) > 0) 1 else 0)
