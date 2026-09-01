# Does metafor converge where our fixed-point iteration does not?
#
# Our corrected REML is a naive fixed-point iteration. metafor uses Fisher
# scoring with step-halving, which converges on inputs where a plain fixed
# point oscillates. So this is not a re-run of the same computation: it is a
# different algorithm for the same estimand, which is the only kind of check
# that can settle whether our capped values are wrong or merely slow.

suppressMessages(library(metafor))
suppressMessages(library(jsonlite))

inp <- file.path("tests", "fixtures", "nonconverged_oracle_inputs.json")
out <- file.path("tests", "fixtures", "nonconverged_oracle_r_output.json")

items <- fromJSON(inp, simplifyDataFrame = FALSE)

res <- lapply(items, function(it) {
  yi <- as.numeric(it$yi)
  vi <- as.numeric(it$vi)
  fit <- try(rma(yi = yi, vi = vi, method = "REML"), silent = TRUE)
  if (inherits(fit, "try-error")) {
    return(list(id = it$id, ok = FALSE, tau2 = NA, python_tau2 = it$python_tau2))
  }
  list(id = it$id, ok = TRUE,
       tau2 = as.numeric(fit$tau2),
       estimate = as.numeric(fit$beta[1]),
       python_tau2 = it$python_tau2,
       metafor_converged = TRUE)
})

write(toJSON(res, auto_unbox = TRUE, digits = 17), out)
cat("wrote", out, "\n\n")
cat(sprintf("%-44s %16s %16s %10s\n", "id", "metafor tau2", "python tau2", "rel diff"))
for (r in res) {
  if (isTRUE(r$ok)) {
    rel <- abs(r$tau2 - r$python_tau2) / max(abs(r$tau2), 1e-12)
    cat(sprintf("%-44s %16.8g %16.8g %10.2e\n",
                sub("^nonconv:", "", r$id), r$tau2, r$python_tau2, rel))
  } else {
    cat(sprintf("%-44s %16s %16.8g %10s\n",
                sub("^nonconv:", "", r$id), "FIT FAILED", r$python_tau2, "-"))
  }
}
