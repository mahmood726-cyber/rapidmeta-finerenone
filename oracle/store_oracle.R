suppressMessages(library(metafor)); suppressMessages(library(jsonlite))
d <- fromJSON("store_cases.json", simplifyVector = FALSE)
cat("R:", R.version.string, "| metafor", as.character(packageVersion("metafor")), "\n")
for (c in d$cases) {
  yi <- as.numeric(unlist(c$yi)); sei <- as.numeric(unlist(c$sei))
  f <- rma(yi = yi, sei = sei, method = "REML", test = "z")
  cat("\n================================================================\n")
  cat(sprintf("%s / %s   k=%d  measure=%s\n", c$topic, c$outcome, length(yi), c$measure))
  cat(sprintf("STORE  tau2 = %s   point = %s (%s to %s)\n",
              c$store_tau2, c$store_point, c$store_ci_low, c$store_ci_high))
  cat(sprintf("ORACLE tau2 = %.7f  [method=%s test=%s]\n", f$tau2, f$method, f$test))
  cat("--- metafor VERBATIM ---\n")
  print(f)
}
