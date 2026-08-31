# Compute the REML tau-squared oracle with metafor.
#
# This file exists so that no oracle value in this repository is typed by a
# person. It reads tests/fixtures/metafor_oracle_inputs.json, runs
# metafor::rma on each item, and writes the results back as JSON. The Python
# side then builds the fixture from THIS output.
#
# Nothing here is allowed to know what answer is expected.

suppressMessages(library(metafor))
suppressMessages(library(jsonlite))

# Run from the repository root. Paths are relative to it deliberately, so
# this script has no knowledge of any machine's directory layout.
inp_path <- file.path("tests", "fixtures", "metafor_oracle_inputs.json")
out_path <- file.path("tests", "fixtures", "metafor_oracle_r_output.json")

items <- fromJSON(inp_path, simplifyDataFrame = FALSE)

res <- lapply(items, function(it) {
  yi <- as.numeric(it$yi)
  vi <- as.numeric(it$vi)
  fit <- rma(yi = yi, vi = vi, method = "REML")
  list(
    id = it$id,
    k = length(yi),
    tau2 = as.numeric(fit$tau2),
    estimate = as.numeric(fit$beta[1]),
    se = as.numeric(fit$se),
    metafor_version = as.character(packageVersion("metafor")),
    r_version = R.version.string
  )
})

write(toJSON(res, auto_unbox = TRUE, digits = 17), out_path)
cat("wrote", out_path, "with", length(res), "oracle values\n")
for (r in res) {
  cat(sprintf("  %-46s k=%-3d tau2=%.17g\n", r$id, r$k, r$tau2))
}
