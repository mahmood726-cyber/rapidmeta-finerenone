suppressMessages(library(metafor)); suppressMessages(library(jsonlite))
d <- fromJSON("rebuild_inputs.json", simplifyVector = FALSE)
cat("R:", R.version.string, "| metafor", as.character(packageVersion("metafor")), "\n\n")
for (x in d) {
  yi <- as.numeric(unlist(x$yi)); vi <- as.numeric(unlist(x$vi))
  f <- rma(yi = yi, vi = vi, method = "REML", test = "z")
  cat(sprintf("%-40s k=%d  metafor tau2 = %.7f   I2 = %.4f   Q = %.4f (df=%d)\n",
              x$file, length(yi), f$tau2, f$I2, f$QE, f$k - 1))
}
