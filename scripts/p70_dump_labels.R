# Dump the study labels and review DOI from Pairwise70 .rda files.
#
# One row per (review, study). The label is what a third party actually receives to identify
# a trial: a Study string and a Study.year. Nothing else in the schema names the trial.
#
# Usage:  Rscript p70_dump_labels.R <dir-of-rda> <out.json>

args <- commandArgs(trailingOnly = TRUE)
dir <- args[1]
out <- args[2]

files <- list.files(dir, pattern = "\\.rda$", full.names = TRUE)
recs <- list()

for (f in files) {
  e <- new.env()
  ok <- tryCatch({ load(f, envir = e); TRUE }, error = function(x) FALSE)
  if (!ok) next
  nm <- ls(e)
  if (length(nm) == 0) next
  d <- get(nm[1], envir = e)
  if (!is.data.frame(d)) next

  doi <- if ("review_doi" %in% names(d)) unique(as.character(d[["review_doi"]])) else NA
  doi <- doi[!is.na(doi) & nzchar(doi)]
  doi <- if (length(doi) > 0) doi[1] else NA

  if (!("Study" %in% names(d))) next
  st <- as.character(d[["Study"]])
  yr <- if ("Study.year" %in% names(d)) as.character(d[["Study.year"]]) else rep(NA, length(st))

  keep <- !is.na(st) & nzchar(st)
  st <- st[keep]; yr <- yr[keep]
  # An explicit separator, not "", so ("AB","1") and ("A","B1") cannot collide into the
  # same dedup key. A pipe cannot occur in a Cochrane study label or a year.
  key <- paste(st, yr, sep = "|")
  dup <- !duplicated(key)
  st <- st[dup]; yr <- yr[dup]

  recs[[length(recs) + 1]] <- list(
    file = basename(f),
    review_doi = if (is.na(doi)) NULL else doi,
    n_rows = nrow(d),
    studies = lapply(seq_along(st), function(i) {
      list(study = st[i], year = if (is.na(yr[i])) NULL else yr[i])
    })
  )
}

con <- file(out, open = "w", encoding = "UTF-8")
writeLines(jsonlite::toJSON(recs, auto_unbox = TRUE, null = "null"), con)
close(con)
cat("wrote", length(recs), "review(s) to", out, "\n")
