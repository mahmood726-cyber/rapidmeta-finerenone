# Dump the numeric 2x2 per (review, study) from Pairwise70 .rda files.
#
# WHY SEPARATE FROM p70_dump_labels.R. The label dump answers "which trial is this row about".
# This answers "what does the row CLAIM about that trial" -- the numbers a recovery
# measurement has to reproduce from the registry. Keeping them apart means the join can be
# validated without touching the counts, and the counts can be re-extracted without redoing
# the join.
#
# One row per (Study, Analysis) that carries a complete dichotomous 2x2. Rows with continuous
# outcomes (means/SDs) or generic-inverse-variance rows are emitted with what they have and
# flagged, rather than dropped -- a row silently omitted here becomes a denominator error
# downstream.
#
# Usage:  Rscript p70_dump_counts.R <dir-of-rda> <out.json>

args <- commandArgs(trailingOnly = TRUE)
dir <- args[1]
out <- args[2]

num <- function(x) {
  if (is.null(x)) return(NA_real_)
  suppressWarnings(as.numeric(as.character(x)))
}
col <- function(d, nm) if (nm %in% names(d)) d[[nm]] else rep(NA, nrow(d))

files <- list.files(dir, pattern = "\\.rda$", full.names = TRUE)
recs <- list()

for (f in files) {
  e <- new.env()
  ok <- tryCatch({ load(f, envir = e); TRUE }, error = function(x) FALSE)
  if (!ok) next
  nm <- ls(e)
  if (length(nm) == 0) next
  d <- get(nm[1], envir = e)
  if (!is.data.frame(d) || !("Study" %in% names(d))) next

  doi <- if ("review_doi" %in% names(d)) as.character(d[["review_doi"]]) else NA
  doi <- doi[!is.na(doi) & nzchar(doi)]
  doi <- if (length(doi) > 0) doi[1] else NA

  st  <- as.character(col(d, "Study"))
  yr  <- as.character(col(d, "Study.year"))
  an  <- as.character(col(d, "Analysis.name"))
  ec  <- num(col(d, "Experimental.cases")); en <- num(col(d, "Experimental.N"))
  cc  <- num(col(d, "Control.cases"));      cn <- num(col(d, "Control.N"))
  em  <- num(col(d, "Experimental.mean"));  cm <- num(col(d, "Control.mean"))

  rows <- list()
  for (i in seq_len(nrow(d))) {
    if (is.na(st[i]) || !nzchar(st[i])) next
    dich <- !is.na(ec[i]) && !is.na(en[i]) && !is.na(cc[i]) && !is.na(cn[i])
    cont <- !is.na(em[i]) || !is.na(cm[i])
    rows[[length(rows) + 1]] <- list(
      study    = st[i],
      year     = if (is.na(yr[i])) NULL else yr[i],
      analysis = if (is.na(an[i])) NULL else an[i],
      kind     = if (dich) "dichotomous" else if (cont) "continuous" else "other",
      e_cases  = if (is.na(ec[i])) NULL else ec[i],
      e_n      = if (is.na(en[i])) NULL else en[i],
      c_cases  = if (is.na(cc[i])) NULL else cc[i],
      c_n      = if (is.na(cn[i])) NULL else cn[i]
    )
  }

  recs[[length(recs) + 1]] <- list(
    file = basename(f),
    review_doi = if (is.na(doi)) NULL else doi,
    n_rows = nrow(d),
    n_emitted = length(rows),
    rows = rows
  )
}

con <- file(out, open = "w", encoding = "UTF-8")
writeLines(jsonlite::toJSON(recs, auto_unbox = TRUE, null = "null"), con)
close(con)

emitted <- sum(vapply(recs, function(r) r$n_emitted, numeric(1)))
seen    <- sum(vapply(recs, function(r) r$n_rows, numeric(1)))
cat("reviews:", length(recs), " data rows seen:", seen, " rows emitted:", emitted, "\n")
cat("rows NOT emitted (no Study label):", seen - emitted, "\n")
