###############################################################################
# hfref_league_export.R -- REGENERATE THE 105-PAIR LEAGUE TABLE
# =============================================================================
# WHY THIS EXISTS
#   The app's payload cited "hfref_league_export.R" as its provenance, and no
#   such file existed on disk. The settled fit script, F:/E156/
#   hfref_eightcell_fit.R, emits only the 15 node rows (each node vs Placebo) --
#   it never serialises the all-pairs league. So the 105 contrasts the page
#   displays had no runnable source. This script is that source.
#
# WHAT IT DOES
#   Re-executes the settled primary cell (OURS-STRICT) and derives every one of
#   the 105 pairwise contrasts, with the same HKSJ-corrected intervals the node
#   rows use, plus the direct-evidence count for each pair.
#
# HOW IT AVOIDS TRANSCRIPTION RISK
#   The arm-level counts, trial metadata, eligibility ladder, contrast
#   construction and cell coordinates are NOT retyped. This script evaluates
#   lines 1..PREFIX_END of the settled script -- everything up to and including
#   fit_cell(), and nothing from its RUN/EMIT sections -- so ARMS, META, CELLS,
#   select_trials() and mk_contrasts() are the settled definitions by
#   construction. The settled script's own emit step cannot fire, so running
#   this never writes into F:/E156.
#
# ANCHOR (hard gate; refuses to emit an unverified table)
#   ACEI+BB+MRA  0.59333495 (0.348-1.011)
#   ACEI+BB      0.64459765 (0.433-0.959)
#   tau^2        0.02323609
#
# USAGE  (from the repository root)
#   Rscript scripts/hfref_league_export.R
#       -> writes outputs/hfref_league_export.json
#   Rscript scripts/hfref_league_export.R --verify HFREF_NMA_AUTO_FULL_REVIEW.html
#       -> additionally re-derives the table and compares it, row by row,
#          against the one embedded in the app. Exits non-zero on any mismatch.
###############################################################################

suppressMessages({
  library(netmeta)
  library(jsonlite)
})

SETTLED    <- "F:/E156/hfref_eightcell_fit.R"
PREFIX_END <- 587L
OUT        <- "outputs/hfref_league_export.json"
CELL_ID    <- "OURS-STRICT"
TOL        <- 1e-8

args   <- commandArgs(trailingOnly = TRUE)
verify <- if ("--verify" %in% args) args[which(args == "--verify") + 1] else NA

fail <- function(...) { cat("FAIL: ", ..., "\n", sep = ""); quit(status = 1) }

if (!file.exists(SETTLED)) fail("settled fit script not found: ", SETTLED)
src <- readLines(SETTLED, warn = FALSE)
if (length(src) < PREFIX_END) fail("settled script shorter than PREFIX_END")
if (!grepl("^\\}$", src[PREFIX_END]))
  fail("PREFIX_END no longer closes fit_cell(); refusing to eval a partial prefix")
if (!any(grepl("8\\. RUN", src[(PREFIX_END + 1):min(length(src), PREFIX_END + 6)])))
  fail("section 8 (RUN) is not immediately after PREFIX_END; settled script moved")

invisible(capture.output(
  eval(parse(text = paste(src[1:PREFIX_END], collapse = "\n")), envir = globalenv())))

###############################################################################
# 1. RE-EXECUTE THE SETTLED PRIMARY CELL
###############################################################################

cl <- Filter(function(x) x$cell_id == CELL_ID, CELLS)
if (length(cl) != 1L) fail("cell ", CELL_ID, " not found in the settled CELLS list")
cl <- cl[[1]]
co <- cl$coords

ids <- select_trials(co)
d   <- ARMS[ARMS$id %in% ids, ]
cn  <- mk_contrasts(d, emperor = co$emperor)
st  <- structure_of(cn)

net <- netmeta(TE = TE, seTE = seTE, treat1 = treat1, treat2 = treat2,
               studlab = studlab, data = cn, sm = "RR",
               common = FALSE, random = TRUE, method.tau = "REML",
               reference.group = "Placebo", warn = FALSE,
               details.chkmultiarm = FALSE)

cat(sprintf("cell=%s  trials=%d  contrasts=%d  nodes=%d  edges=%d  tau2=%.11f  I2=%.4f\n",
            CELL_ID, length(unique(cn$studlab)), nrow(cn), st$V, st$E,
            net$tau2, net$I2))

# HKSJ: variance inflation q = max(1, r'Wr/df) with the mandatory max(1,.)
# floor, and a t_df critical value. Without the floor HKSJ NARROWS the interval
# below the uncorrected one whenever Q < df.
w    <- 1 / (net$seTE^2 + net$tau2)
dfq  <- unname(net$df.Q)
qraw <- sum(w * (net$TE - net$TE.nma.random)^2) / dfq
q    <- max(1, qraw)
crit <- qt(0.975, dfq)
mult <- crit * sqrt(q)
cat(sprintf("HKSJ q_raw=%.11f q_used=%.11f df=%d t=%.11f multiplier=%.11f\n",
            qraw, q, dfq, crit, mult))

TEm <- net$TE.random
SEm <- net$seTE.random
trts <- sort(net$trts)

###############################################################################
# 2. DIRECT EVIDENCE PER UNORDERED PAIR
#    Counted as DISTINCT STUDIES, so a multi-arm trial (CARMEN) contributes
#    once to each of its edges rather than once per contrast row.
###############################################################################

pkey  <- function(a, b) paste(sort(c(a, b)), collapse = "|")
studs <- list()
for (i in seq_len(nrow(cn))) {
  k <- pkey(cn$treat1[i], cn$treat2[i])
  studs[[k]] <- unique(c(studs[[k]], cn$studlab[i]))
}
dk <- function(a, b) { s <- studs[[pkey(a, b)]]; if (is.null(s)) 0L else length(s) }

###############################################################################
# 3. ALL 105 PAIRS + THE 14 NODE ROWS
###############################################################################

rr <- function(a, b) unname(exp(TEm[a, b]))
lo <- function(a, b) unname(exp(TEm[a, b] - mult * SEm[a, b]))
hi <- function(a, b) unname(exp(TEm[a, b] + mult * SEm[a, b]))

league <- list()
for (i in 1:(length(trts) - 1)) for (j in (i + 1):length(trts)) {
  a <- trts[i]; b <- trts[j]
  league[[length(league) + 1]] <- list(
    t1 = a, t2 = b, rr = rr(a, b), lo = lo(a, b), hi = hi(a, b),
    se_log = unname(SEm[a, b]), direct_k = dk(a, b))
}
nodes <- lapply(setdiff(trts, "Placebo"), function(nd)
  list(node = nd, rr = rr(nd, "Placebo"),
       lo = lo(nd, "Placebo"), hi = hi(nd, "Placebo")))

n_pairs  <- length(league)
n_direct <- sum(sapply(league, function(p) p$direct_k > 0))
n_excl   <- sum(sapply(league, function(p) p$lo > 1 || p$hi < 1))
cat(sprintf("pairs=%d (expected %d)  with direct evidence=%d  indirect only=%d  CI excludes 1=%d\n",
            n_pairs, length(trts) * (length(trts) - 1) / 2, n_direct,
            n_pairs - n_direct, n_excl))
if (n_pairs != length(trts) * (length(trts) - 1) / 2)
  fail("pair count is not the complete set of unordered pairs")

###############################################################################
# 4. ANCHOR GATE
###############################################################################

g <- function(nm) Filter(function(x) x$node == nm, nodes)[[1]]
A <- g("ACEI+BB+MRA"); B <- g("ACEI+BB")
ok <- abs(A$rr - 0.59333495) < 1e-8 && abs(A$lo - 0.348) < 5e-4 && abs(A$hi - 1.011) < 5e-4 &&
      abs(B$rr - 0.64459765) < 1e-8 && abs(B$lo - 0.433) < 5e-4 && abs(B$hi - 0.959) < 5e-4 &&
      abs(net$tau2 - 0.02323609) < 1e-8
cat(sprintf("ANCHOR ACEI+BB+MRA %.8f (%.3f-%.3f)  ACEI+BB %.8f (%.3f-%.3f)  tau2 %.8f  %s\n",
            A$rr, A$lo, A$hi, B$rr, B$lo, B$hi, net$tau2, if (ok) "PASS" else "FAIL"))
if (!ok) fail("ANCHOR FAILED -- refusing to emit a league table off the settled fit")

###############################################################################
# 5. EMIT
###############################################################################

dir.create(dirname(OUT), showWarnings = FALSE, recursive = TRUE)
write(toJSON(list(
  schema = "hfref-league-export/v1",
  generated_by = "scripts/hfref_league_export.R",
  settled_source = SETTLED,
  settled_prefix_lines = PREFIX_END,
  engine = paste0("R ", getRversion(), " / netmeta ", packageVersion("netmeta")),
  cell_id = CELL_ID, coords = co,
  outcome = "all-cause mortality",
  trials = length(unique(cn$studlab)), contrasts_in_data = nrow(cn),
  nodes_in_network = st$V, estimable_pairs = n_pairs,
  tau2 = unname(net$tau2), i2 = unname(net$I2),
  hksj = list(q = unname(q), q_raw = unname(qraw), df = dfq, crit = unname(crit),
              multiplier = unname(mult)),
  structure = st,
  counts = list(estimable = n_pairs, with_direct = n_direct,
                indirect_only = n_pairs - n_direct, ci_excludes_null = n_excl),
  node_vs_placebo = nodes,
  league = league),
  auto_unbox = TRUE, digits = 11, null = "null", na = "null"), file = OUT)
cat("WROTE ", OUT, "\n", sep = "")

###############################################################################
# 6. OPTIONAL: VERIFY THE APP'S EMBEDDED TABLE AGAINST WHAT WE JUST COMPUTED
###############################################################################

if (!is.na(verify)) {
  cat("\n=== VERIFY against ", verify, " ===\n", sep = "")
  if (!file.exists(verify)) fail("app file not found: ", verify)
  html <- paste(readLines(verify, warn = FALSE), collapse = "\n")
  m <- regmatches(html, regexpr(
    '<script[^>]*id="hfref-fit-data"[^>]*>.*?</script>', html, perl = TRUE))
  if (!length(m)) fail("script#hfref-fit-data not found in the app")
  body <- sub('^<script[^>]*>', '', m); body <- sub('</script>$', '', body)
  F <- fromJSON(body, simplifyVector = FALSE)
  pc <- Filter(function(c_) c_$cell_id == CELL_ID, F$cells)
  if (length(pc) != 1L) fail("primary cell not found in the app payload")
  pc <- pc[[1]]

  if (length(pc$league) != n_pairs)
    fail(sprintf("app carries %d league rows, this script computes %d",
                 length(pc$league), n_pairs))

  mine <- list()
  for (p in league) mine[[pkey(p$t1, p$t2)]] <- p

  worst <- 0; worst_at <- ""; nchk <- 0; dkbad <- 0
  for (p in pc$league) {
    k <- pkey(p$t1, p$t2)
    s <- mine[[k]]
    if (is.null(s)) fail("app league row absent from this re-derivation: ", k)
    for (f in c("rr", "lo", "hi")) {
      dv <- abs(p[[f]] - s[[f]]) / max(abs(s[[f]]), 1e-30)
      if (dv > worst) { worst <- dv; worst_at <- paste0(k, ".", f) }
    }
    if (!identical(as.integer(p$direct_k), as.integer(s$direct_k))) dkbad <- dkbad + 1
    nchk <- nchk + 1
  }
  cat(sprintf("league   : %d rows compared, max rel dev %.3e (%s)\n", nchk, worst, worst_at))
  cat(sprintf("direct_k : %d row(s) disagree\n", dkbad))

  nworst <- 0
  for (p in pc$node_vs_placebo) {
    s <- Filter(function(x) x$node == p$node, nodes)[[1]]
    for (f in c("rr", "lo", "hi"))
      nworst <- max(nworst, abs(p[[f]] - s[[f]]) / max(abs(s[[f]]), 1e-30))
  }
  cat(sprintf("node rows: %d compared, max rel dev %.3e\n",
              length(pc$node_vs_placebo), nworst))

  if (worst > TOL || nworst > TOL || dkbad > 0)
    fail(sprintf("app table does NOT reproduce (league %.3e, nodes %.3e, direct_k mismatches %d)",
                 worst, nworst, dkbad))
  cat("VERDICT: PASS -- this script reproduces every row of the app's league table.\n")
}
