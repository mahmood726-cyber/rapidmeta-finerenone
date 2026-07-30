###############################################################################
# hfref_quarantine_refit.R -- RE-FIT THE PRIMARY WITH CARMEN'S MORTALITY
#                             QUARANTINED, AND REPORT THE CONSEQUENCE
# =============================================================================
# WHY THIS EXISTS
#   outputs/HFREF_INTEGRITY_GATES_2026-07-30.md finding F2 established that
#   CARMEN's 14/14/14 all-cause death counts have NO located source: the
#   trial's primary endpoint is left-ventricular end-systolic volume index,
#   its abstract reports no deaths, and the settled fit script's own line 377
#   already annotates CARMEN "inadmissible (its primary reports LVESVI and no
#   deaths)". This script executes the disposition the audit deferred to a
#   human: it QUARANTINES that contribution (it does not silently delete it --
#   the violation is named in outputs/hfref_quarantine_ledger.json) and re-fits
#   the network without it, so the published estimates rest only on counts that
#   have a source.
#
# WHAT IS QUARANTINED, AND WHAT IS NOT
#   QUARANTINED : HF-021 CARMEN -- named violation
#                 "no death data in source; 14/14/14 unsourced; primary is LVESVI"
#   NOT quarantined (re-sourced during this pass, see the ledger):
#     HF-008 SPICE   -- primary LOCATED this pass: PMID 10740141 (Granger,
#                       Am Heart J 2000;139:609-17). Counts recover exactly.
#     HF-019 RESOLVD -- citation corrected to PMID 10653828; counts match the
#                       publication's body text.
#     HF-020 He 2015 -- per-arm N and deaths verified exactly from PMC5746969.
#     HF-038 QUEST   -- counts verified exactly from PMC11333273; the finding is
#                       a PRESENTATION issue (crude-2x2 significance vs the
#                       trial's own non-significant Cox analysis), not a count
#                       error, so it changes no input here.
#
# HOW IT AVOIDS TRANSCRIPTION RISK
#   Exactly the discipline of scripts/hfref_league_export.R: this script
#   evaluates lines 1..PREFIX_END of the settled fit -- everything up to and
#   including fit_cell(), and NOTHING from its RUN or EMIT sections -- so ARMS,
#   META, CELLS, select_trials(), mk_contrasts(), structure_of() and fit_cell()
#   are the settled definitions by construction. The settled script's emit step
#   cannot fire; running this never writes into F:/E156 and never modifies it.
#
# ANCHOR (hard gate)
#   The BEFORE fit must reproduce the settled primary exactly or this script
#   refuses to emit:
#     ACEI+BB+MRA  0.59333495     ACEI+BB  0.64459765     tau^2 0.02323609
#
# USAGE  (from the repository root)
#   Rscript scripts/hfref_quarantine_refit.R
#       -> writes outputs/hfref_quarantine_refit.json
###############################################################################

suppressMessages({
  library(netmeta)
  library(jsonlite)
})

SETTLED    <- "F:/E156/hfref_eightcell_fit.R"
PREFIX_END <- 587L
OUT        <- "outputs/hfref_quarantine_refit.json"
CELL_ID    <- "OURS-STRICT"
CAL_ID     <- "CAL-netfit-v1.3"

QUARANTINE <- c("HF-021")
QUARANTINE_REASON <- list(
  "HF-021" = list(
    trial = "CARMEN",
    violation = "no death data in source; 14/14/14 unsourced; primary is LVESVI",
    detail = paste0(
      "PMID 15115904 (Cardiovasc Drugs Ther 2004;18:57-66) confirms the three ",
      "arms exactly -- 'carvedilol (N = 191), enalapril (N = 190) or their ",
      "combination (N = 191)' -- but the trial's primary endpoint is the change ",
      "in left-ventricular end-systolic volume index and the publication ",
      "reports NO per-arm death counts. The ledger nonetheless carried an ",
      "identical 14 deaths in all three arms. The settled fit script's own ",
      "line 377 annotates CARMEN 'inadmissible (its primary reports LVESVI and ",
      "no deaths)'. Quarantined, not deleted: the arm rows remain on record ",
      "here and in outputs/hfref_quarantine_ledger.json.")))

fail <- function(...) { cat("FAIL: ", ..., "\n", sep = ""); quit(status = 1) }

###############################################################################
# 0. LOAD THE SETTLED DEFINITIONS (prefix only -- never RUN, never EMIT)
###############################################################################

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
# 1. FIT THE PRIMARY CELL, WITH AN ARBITRARY QUARANTINE SET
###############################################################################

cl <- Filter(function(x) x$cell_id == CELL_ID, CELLS)
if (length(cl) != 1L) fail("cell ", CELL_ID, " not found in the settled CELLS list")
cl <- cl[[1]]
co <- cl$coords

pkey <- function(a, b) paste(sort(c(a, b)), collapse = "|")

fit_primary <- function(drop_ids = character(0)) {
  ids <- setdiff(select_trials(co), drop_ids)
  d   <- ARMS[ARMS$id %in% ids, ]
  cn  <- mk_contrasts(d, emperor = co$emperor)
  st  <- structure_of(cn)

  net <- netmeta(TE = TE, seTE = seTE, treat1 = treat1, treat2 = treat2,
                 studlab = studlab, data = cn, sm = "RR",
                 common = FALSE, random = TRUE, method.tau = "REML",
                 reference.group = "Placebo", warn = FALSE,
                 details.chkmultiarm = FALSE)

  # HKSJ exactly as the settled fit applies it: variance inflation
  # q = max(1, r'Wr/df) -- the max(1,.) floor is mandatory, without it HKSJ
  # NARROWS the interval below the uncorrected one whenever Q < df -- and a
  # t_df critical value.
  w    <- 1 / (net$seTE^2 + net$tau2)
  dfq  <- unname(net$df.Q)
  qraw <- sum(w * (net$TE - net$TE.nma.random)^2) / dfq
  q    <- max(1, qraw)
  crit <- qt(0.975, dfq)
  mult <- crit * sqrt(q)

  TEm <- net$TE.random; SEm <- net$seTE.random
  trts <- sort(net$trts)

  studs <- list()
  for (i in seq_len(nrow(cn))) {
    k <- pkey(cn$treat1[i], cn$treat2[i])
    studs[[k]] <- unique(c(studs[[k]], cn$studlab[i]))
  }
  dk <- function(a, b) { s <- studs[[pkey(a, b)]]; if (is.null(s)) 0L else length(s) }

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

  # Placebo-ARB direct leg -- the edge SPICE alone supplies in this cell
  arb_leg <- cn[(cn$treat1 == "ARB" & cn$treat2 == "Placebo") |
                (cn$treat2 == "ARB" & cn$treat1 == "Placebo"), ]

  list(net = net, cn = cn, st = st, trts = trts, league = league, nodes = nodes,
       tau2 = unname(net$tau2), i2 = unname(net$I2),
       hksj = list(q = unname(q), q_raw = unname(qraw), df = dfq,
                   crit = unname(crit), multiplier = unname(mult)),
       trials = length(unique(cn$studlab)),
       trial_names = sort(unique(cn$studlab)),
       contrasts = nrow(cn),
       n_excl = sum(sapply(league, function(p) p$lo > 1 || p$hi < 1)),
       n_direct = sum(sapply(league, function(p) p$direct_k > 0)),
       placebo_arb = list(k = nrow(arb_leg),
                          events = if (nrow(arb_leg))
                            sum(arb_leg$event1 + arb_leg$event2) else 0),
       # the covariance the league is derived from, kept so the multiverse and
       # any downstream recomputation use the SAME matrix rather than a re-fit
       cov_random = unname(as.matrix(net$seTE.random)))
}

###############################################################################
# 2. BEFORE -- must reproduce the settled primary exactly
###############################################################################

cat("=== BEFORE: settled primary (OURS-STRICT, CARMEN included) ===\n")
B <- fit_primary(character(0))
gb <- function(f, nm) Filter(function(x) x$node == nm, f$nodes)[[1]]

A0 <- gb(B, "ACEI+BB+MRA"); B0 <- gb(B, "ACEI+BB")
anchor_ok <-
  abs(A0$rr - 0.59333495) < 1e-8 && abs(A0$lo - 0.348) < 5e-4 && abs(A0$hi - 1.011) < 5e-4 &&
  abs(B0$rr - 0.64459765) < 1e-8 && abs(B0$lo - 0.433) < 5e-4 && abs(B0$hi - 0.959) < 5e-4 &&
  abs(B$tau2 - 0.02323609) < 1e-8
cat(sprintf("  trials=%d contrasts=%d V=%d E=%d designs=%d cyclomatic=%d ICDF=%d\n",
            B$trials, B$contrasts, B$st$V, B$st$E, B$st$designs,
            B$st$cyclomatic, B$st$icdf))
cat(sprintf("  tau2=%.8f I2=%.4f  HKSJ q=%.6f df=%d mult=%.6f\n",
            B$tau2, B$i2, B$hksj$q, B$hksj$df, B$hksj$multiplier))
cat(sprintf("  ANCHOR ACEI+BB+MRA %.8f (%.3f-%.3f)  ACEI+BB %.8f (%.3f-%.3f)  tau2 %.8f  %s\n",
            A0$rr, A0$lo, A0$hi, B0$rr, B0$lo, B0$hi, B$tau2,
            if (anchor_ok) "PASS" else "FAIL"))
if (!anchor_ok)
  fail("BEFORE fit does not reproduce the settled primary -- refusing to report a delta ",
       "against an unverified baseline")

###############################################################################
# 3. AFTER -- CARMEN's mortality contribution quarantined
###############################################################################

cat("\n=== AFTER: CARMEN quarantined ===\n")
A <- fit_primary(QUARANTINE)
cat(sprintf("  trials=%d contrasts=%d V=%d E=%d designs=%d cyclomatic=%d ICDF=%d\n",
            A$trials, A$contrasts, A$st$V, A$st$E, A$st$designs,
            A$st$cyclomatic, A$st$icdf))
cat(sprintf("  tau2=%.8f I2=%.4f  HKSJ q=%.6f df=%d mult=%.6f\n",
            A$tau2, A$i2, A$hksj$q, A$hksj$df, A$hksj$multiplier))
cat(sprintf("  multi-arm internal loops: before=%d after=%d\n",
            B$st$multiarm_internal_loops, A$st$multiarm_internal_loops))
cat(sprintf("  nodes lost: %s\n",
            { L <- setdiff(B$trts, A$trts); if (length(L)) paste(L, collapse = ", ") else "(none)" }))

###############################################################################
# 4. BEFORE -> AFTER, NODE BY NODE
###############################################################################

cat("\n=== NODE vs Placebo: before -> after ===\n")
cat(sprintf("  %-14s %25s   %25s   %8s\n", "node", "BEFORE RR (95% CI)",
            "AFTER RR (95% CI)", "d(RR)%"))
node_delta <- list()
for (nm in sapply(B$nodes, function(x) x$node)) {
  b <- gb(B, nm)
  af <- Filter(function(x) x$node == nm, A$nodes)
  if (!length(af)) {
    cat(sprintf("  %-14s %25s   %25s   %8s\n", nm,
                sprintf("%.3f (%.3f-%.3f)", b$rr, b$lo, b$hi), "NODE LOST", "--"))
    node_delta[[length(node_delta) + 1]] <- list(
      node = nm, before = list(rr = b$rr, lo = b$lo, hi = b$hi),
      after = NULL, node_lost = TRUE)
    next
  }
  af <- af[[1]]
  d <- 100 * (af$rr - b$rr) / b$rr
  cat(sprintf("  %-14s %25s   %25s   %+7.2f%%\n", nm,
              sprintf("%.3f (%.3f-%.3f)", b$rr, b$lo, b$hi),
              sprintf("%.3f (%.3f-%.3f)", af$rr, af$lo, af$hi), d))
  node_delta[[length(node_delta) + 1]] <- list(
    node = nm, before = list(rr = b$rr, lo = b$lo, hi = b$hi),
    after = list(rr = af$rr, lo = af$lo, hi = af$hi),
    rel_change_pct = d, node_lost = FALSE)
}

cat(sprintf("\n  league pairs: before=%d after=%d | CI excludes 1: before=%d after=%d\n",
            length(B$league), length(A$league), B$n_excl, A$n_excl))
cat(sprintf("  Placebo-ARB direct leg: before k=%d/%d events, after k=%d/%d events\n",
            B$placebo_arb$k, B$placebo_arb$events, A$placebo_arb$k, A$placebo_arb$events))

###############################################################################
# 5. MULTIVERSE -- every cell re-fitted with the same quarantine.
#    The quarantine is a DATA-INTEGRITY disposition, not a coordinate choice,
#    so it applies to every cell regardless of whose review's coordinates the
#    cell encodes. The one exception is the CALIBRATION cell, which exists to
#    reproduce the frozen Python fit (netfit_hfref.py) -- that fit INCLUDED
#    CARMEN, so quarantining there would make the calibration check
#    meaningless. CAL is therefore left on the unquarantined data and is
#    reported as a reproducibility witness only, never as a claim.
###############################################################################

cat("\n=== MULTIVERSE: every cell, before -> after ===\n")
DROP_CARMEN <<- setdiff(sapply(CELLS, function(x) x$cell_id), CAL_ID)

mv <- list()
for (c_ in CELLS) {
  before <- fit_cell(within(c_, { cell_id <- paste0(cell_id, "__nodrop") }))
  # the __nodrop suffix keeps it out of DROP_CARMEN, giving the pre-quarantine fit
  after  <- fit_cell(c_)
  gnode <- function(r, nm) {
    if (!isTRUE(r$computed)) return(NULL)
    x <- Filter(function(z) isTRUE(z$present) && z$node == nm, r$nodes)
    if (!length(x)) NULL else x[[1]]
  }
  bb <- gnode(before, "ACEI+BB"); aa <- gnode(after, "ACEI+BB")
  bm <- gnode(before, "ACEI+BB+MRA"); am <- gnode(after, "ACEI+BB+MRA")
  cat(sprintf("  %-22s trials %3d->%3d  ICDF %d->%d  ACEI+BB %s->%s  ACEI+BB+MRA %s->%s\n",
              c_$cell_id,
              if (isTRUE(before$computed)) before$trials$n else -1L,
              if (isTRUE(after$computed))  after$trials$n  else -1L,
              if (isTRUE(before$computed)) before$structure$icdf else -1L,
              if (isTRUE(after$computed))  after$structure$icdf  else -1L,
              if (is.null(bb)) "--" else sprintf("%.3f", bb$rr),
              if (is.null(aa)) "--" else sprintf("%.3f", aa$rr),
              if (is.null(bm)) "--" else sprintf("%.3f", bm$rr),
              if (is.null(am)) "--" else sprintf("%.3f", am$rr)))
  mv[[length(mv) + 1]] <- list(
    cell_id = c_$cell_id, label = c_$label, tier = c_$tier,
    quarantine_applied = !(c_$cell_id %in% CAL_ID),
    before = list(computed = isTRUE(before$computed),
                  trials = if (isTRUE(before$computed)) before$trials$n else NULL,
                  icdf = if (isTRUE(before$computed)) before$structure$icdf else NULL,
                  tau2 = if (isTRUE(before$computed)) before$tau2 else NULL,
                  acei_bb = if (is.null(bb)) NULL else bb,
                  acei_bb_mra = if (is.null(bm)) NULL else bm),
    after = list(computed = isTRUE(after$computed),
                 trials = if (isTRUE(after$computed)) after$trials$n else NULL,
                 icdf = if (isTRUE(after$computed)) after$structure$icdf else NULL,
                 tau2 = if (isTRUE(after$computed)) after$tau2 else NULL,
                 acei_bb = if (is.null(aa)) NULL else aa,
                 acei_bb_mra = if (is.null(am)) NULL else am))
}

###############################################################################
# 6. EMIT
###############################################################################

pack <- function(f) list(
  trials = f$trials, trial_names = f$trial_names, contrasts = f$contrasts,
  tau2 = f$tau2, i2 = f$i2, hksj = f$hksj, structure = f$st,
  counts = list(estimable = length(f$league), with_direct = f$n_direct,
                indirect_only = length(f$league) - f$n_direct,
                ci_excludes_null = f$n_excl),
  placebo_arb_direct_leg = f$placebo_arb,
  node_vs_placebo = f$nodes, league = f$league)

dir.create(dirname(OUT), showWarnings = FALSE, recursive = TRUE)
write(toJSON(list(
  schema = "hfref-quarantine-refit/v1",
  generated_by = "scripts/hfref_quarantine_refit.R",
  date = "2026-07-30",
  settled_source = SETTLED, settled_prefix_lines = PREFIX_END,
  engine = paste0("R ", getRversion(), " / netmeta ", packageVersion("netmeta")),
  cell_id = CELL_ID, coords = co, outcome = "all-cause mortality",
  quarantine = list(
    ids = QUARANTINE,
    reasons = QUARANTINE_REASON,
    principle = paste0(
      "Quarantine, never silent deletion. Every removed contribution carries a ",
      "NAMED violation and its arm rows stay on record in ",
      "outputs/hfref_quarantine_ledger.json.")),
  anchor_before = list(
    acei_bb_mra = 0.59333495, acei_bb = 0.64459765, tau2 = 0.02323609,
    reproduced = anchor_ok),
  before = pack(B), after = pack(A),
  node_delta = node_delta,
  multiverse = mv),
  auto_unbox = TRUE, digits = 11, null = "null", na = "null"), file = OUT)
cat("\nWROTE ", OUT, "\n", sep = "")
