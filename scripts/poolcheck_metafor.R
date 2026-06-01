ul <- path.expand("~/R/win-library"); .libPaths(c(ul, .libPaths()))
suppressPackageStartupMessages({library(metafor); library(jsonlite)})
dat <- fromJSON("outputs/poolcheck_input.json", simplifyVector=FALSE)
res <- list()
for (app in names(dat)) {
  d <- dat[[app]]
  yi <- as.numeric(unlist(d$yi)); si <- as.numeric(unlist(d$si))
  vi <- si^2
  out <- tryCatch({
    m <- rma(yi=yi, vi=vi, method="REML", test="knha")
    list(r_est=round(exp(as.numeric(m$b)),4), r_k=m$k, I2=round(m$I2,1))
  }, error=function(e) tryCatch({
    m <- rma(yi=yi, vi=vi, method="DL", test="knha")
    list(r_est=round(exp(as.numeric(m$b)),4), r_k=m$k, I2=round(m$I2,1))
  }, error=function(e2) list(r_est=NA, r_k=length(yi), I2=NA)))
  res[[app]] <- out
}
write_json(res, "outputs/poolcheck_R.json", auto_unbox=TRUE, na="null")
cat("R pooled", length(res), "apps\n")
