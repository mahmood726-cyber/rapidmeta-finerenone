###############################################################################
# hfref_quarantine_primary.R -- the PRIMARY-CELL half of the quarantine re-fit,
# split out so the headline before->after table is available without waiting on
# the multiverse pass (which re-fits 22 networks with netsplit and is slow).
#
# Same discipline as scripts/hfref_league_export.R and
# scripts/hfref_quarantine_refit.R: evaluates lines 1..587 of the settled fit
# (up to and including fit_cell(), nothing from RUN or EMIT), so ARMS, META,
# CELLS, select_trials() and mk_contrasts() are the settled definitions. The
# settled script's emit cannot fire and F:/E156 is never written.
#
# ANCHOR GATE: the BEFORE fit must reproduce the settled primary
#   ACEI+BB+MRA 0.59333495   ACEI+BB 0.64459765   tau^2 0.02323609
# or this script refuses to emit.
###############################################################################

suppressMessages({ library(netmeta); library(jsonlite) })

SETTLED <- "F:/E156/hfref_eightcell_fit.R"; PREFIX_END <- 587L
OUT      <- "outputs/hfref_quarantine_primary.json"
CELL_ID  <- "OURS-STRICT"
# every cell the app payload embeds a full league table for
APP_CELLS <- c("OURS-STRICT","OURS-INCLUSIVE","OURS-STRICT-7b","OURS-STRICT-7c")
QUARANTINE <- c("HF-021")   # CARMEN -- see outputs/hfref_quarantine_ledger.json

fail <- function(...) { cat("FAIL: ", ..., "\n", sep = ""); quit(status = 1) }

src <- readLines(SETTLED, warn = FALSE)
if (!grepl("^\\}$", src[PREFIX_END])) fail("PREFIX_END no longer closes fit_cell()")
if (!any(grepl("8\\. RUN", src[(PREFIX_END + 1):(PREFIX_END + 6)])))
  fail("section 8 (RUN) not immediately after PREFIX_END; settled script moved")
invisible(capture.output(
  eval(parse(text = paste(src[1:PREFIX_END], collapse = "\n")), envir = globalenv())))

pkey <- function(a, b) paste(sort(c(a, b)), collapse = "|")

fitp <- function(cl, drop_ids = character(0)) {
  co  <- cl$coords
  ids <- setdiff(select_trials(co), drop_ids)
  cn  <- mk_contrasts(ARMS[ARMS$id %in% ids, ], emperor = co$emperor)
  st  <- structure_of(cn)
  rnd <- (co$estimand != "fe")
  net <- netmeta(TE = TE, seTE = seTE, treat1 = treat1, treat2 = treat2,
                 studlab = studlab, data = cn, sm = "RR", common = !rnd,
                 random = rnd,
                 method.tau = if (co$estimand == "reml") "REML" else "DL",
                 reference.group = "Placebo",
                 warn = FALSE, details.chkmultiarm = FALSE)
  fitted <- if (rnd) net$TE.nma.random else net$TE.nma.common
  w <- 1 / (net$seTE^2 + (if (rnd) net$tau2 else 0)); dfq <- unname(net$df.Q)
  qraw <- sum(w * (net$TE - fitted)^2) / dfq
  q <- max(1, qraw); crit <- qt(0.975, dfq); mult <- crit * sqrt(q)
  TEm <- if (rnd) net$TE.random else net$TE.common
  SEm <- if (rnd) net$seTE.random else net$seTE.common
  trts <- sort(net$trts)
  studs <- list()
  for (i in seq_len(nrow(cn))) {
    k <- pkey(cn$treat1[i], cn$treat2[i])
    studs[[k]] <- unique(c(studs[[k]], cn$studlab[i]))
  }
  dk <- function(a, b) { s <- studs[[pkey(a, b)]]; if (is.null(s)) 0L else length(s) }
  rr <- function(a,b) unname(exp(TEm[a,b]))
  lo <- function(a,b) unname(exp(TEm[a,b] - mult*SEm[a,b]))
  hi <- function(a,b) unname(exp(TEm[a,b] + mult*SEm[a,b]))
  league <- list()
  for (i in 1:(length(trts)-1)) for (j in (i+1):length(trts)) {
    a <- trts[i]; b <- trts[j]
    league[[length(league)+1]] <- list(t1=a, t2=b, rr=rr(a,b), lo=lo(a,b),
      hi=hi(a,b), se_log=unname(SEm[a,b]), direct_k=dk(a,b))
  }
  nodes <- lapply(setdiff(trts, "Placebo"), function(nd)
    list(node=nd, rr=rr(nd,"Placebo"), lo=lo(nd,"Placebo"), hi=hi(nd,"Placebo")))
  arb <- cn[(cn$treat1=="ARB" & cn$treat2=="Placebo") |
            (cn$treat2=="ARB" & cn$treat1=="Placebo"), ]
  edge_k <- table(apply(cn[, c("treat1","treat2")], 1,
                        function(r) paste(sort(r), collapse=" vs ")))
  rk <- try(netrank(net, small.values = "desirable"), silent = TRUE)
  ps <- if (inherits(rk,"try-error")) NULL else {
    v <- if (rnd) rk$ranking.random else rk$ranking.common
    as.list(round(v[order(-v)], 4)) }
  list(st=st, trts=trts, league=league, nodes=nodes, pscore=ps,
       tau2=unname(if (rnd) net$tau2 else 0),
       i2=unname(net$I2),
       hksj=list(q=unname(q), q_raw=unname(qraw), df=dfq, crit=unname(crit),
                 multiplier=unname(mult)),
       trials=length(unique(cn$studlab)), trial_names=sort(unique(cn$studlab)),
       contrasts=nrow(cn),
       n_excl=sum(sapply(league, function(p) p$lo > 1 || p$hi < 1)),
       n_direct=sum(sapply(league, function(p) p$direct_k > 0)),
       placebo_arb=list(k=nrow(arb),
                        events=if (nrow(arb)) sum(arb$event1+arb$event2) else 0),
       edge_k=as.list(edge_k))
}

g <- function(f, nm) { x <- Filter(function(z) z$node == nm, f$nodes)
                       if (!length(x)) NULL else x[[1]] }

PC <- Filter(function(x) x$cell_id == CELL_ID, CELLS)[[1]]
B <- fitp(PC, character(0))
A0 <- g(B,"ACEI+BB+MRA"); B0 <- g(B,"ACEI+BB")
anchor_ok <- abs(A0$rr-0.59333495)<1e-8 && abs(B0$rr-0.64459765)<1e-8 &&
             abs(B$tau2-0.02323609)<1e-8
cat("=== BEFORE (settled primary, CARMEN in) ===\n")
cat(sprintf("trials=%d contrasts=%d V=%d E=%d designs=%d cyclomatic=%d ICDF=%d internal_loops=%d\n",
  B$trials,B$contrasts,B$st$V,B$st$E,B$st$designs,B$st$cyclomatic,B$st$icdf,
  B$st$multiarm_internal_loops))
cat(sprintf("tau2=%.8f I2=%.4f HKSJ q=%.6f q_raw=%.6f df=%d mult=%.6f\n",
  B$tau2,B$i2,B$hksj$q,B$hksj$q_raw,B$hksj$df,B$hksj$multiplier))
cat(sprintf("ANCHOR %s : ACEI+BB+MRA %.8f  ACEI+BB %.8f  tau2 %.8f\n",
  if (anchor_ok) "PASS" else "FAIL", A0$rr, B0$rr, B$tau2))
if (!anchor_ok) fail("BEFORE does not reproduce the settled primary")

A <- fitp(PC, QUARANTINE)
cat("\n=== AFTER (CARMEN quarantined) ===\n")
cat(sprintf("trials=%d contrasts=%d V=%d E=%d designs=%d cyclomatic=%d ICDF=%d internal_loops=%d\n",
  A$trials,A$contrasts,A$st$V,A$st$E,A$st$designs,A$st$cyclomatic,A$st$icdf,
  A$st$multiarm_internal_loops))
cat(sprintf("tau2=%.8f I2=%.4f HKSJ q=%.6f q_raw=%.6f df=%d mult=%.6f\n",
  A$tau2,A$i2,A$hksj$q,A$hksj$q_raw,A$hksj$df,A$hksj$multiplier))
cat(sprintf("nodes lost: %s\n",
  { L <- setdiff(B$trts,A$trts); if (length(L)) paste(L,collapse=", ") else "(none)" }))
cat(sprintf("edges lost: %s\n",
  { L <- setdiff(names(B$edge_k), names(A$edge_k))
    if (length(L)) paste(L,collapse=", ") else "(none)" }))

cat("\n=== NODE vs Placebo: BEFORE -> AFTER ===\n")
cat(sprintf("%-14s %24s %24s %9s\n","node","BEFORE RR (95% CI)","AFTER RR (95% CI)","d(RR)%"))
nd <- list()
for (nm in sapply(B$nodes, function(x) x$node)) {
  b <- g(B,nm); a <- g(A,nm)
  if (is.null(a)) {
    cat(sprintf("%-14s %24s %24s %9s\n", nm,
      sprintf("%.3f (%.3f-%.3f)",b$rr,b$lo,b$hi),"NODE LOST","--"))
    nd[[length(nd)+1]] <- list(node=nm, before=b, after=NULL, node_lost=TRUE); next
  }
  d <- 100*(a$rr-b$rr)/b$rr
  cat(sprintf("%-14s %24s %24s %+8.2f%%\n", nm,
    sprintf("%.3f (%.3f-%.3f)",b$rr,b$lo,b$hi),
    sprintf("%.3f (%.3f-%.3f)",a$rr,a$lo,a$hi), d))
  nd[[length(nd)+1]] <- list(node=nm, before=b, after=a, rel_change_pct=d, node_lost=FALSE)
}
cat(sprintf("\nleague pairs %d -> %d | CI excludes 1: %d -> %d | with direct: %d -> %d\n",
  length(B$league),length(A$league),B$n_excl,A$n_excl,B$n_direct,A$n_direct))
cat(sprintf("Placebo-ARB direct leg: k=%d/%d ev -> k=%d/%d ev\n",
  B$placebo_arb$k,B$placebo_arb$events,A$placebo_arb$k,A$placebo_arb$events))

pack <- function(f) list(trials=f$trials, trial_names=f$trial_names,
  contrasts=f$contrasts, tau2=f$tau2, i2=f$i2, hksj=f$hksj, structure=f$st,
  counts=list(estimable=length(f$league), with_direct=f$n_direct,
              indirect_only=length(f$league)-f$n_direct, ci_excludes_null=f$n_excl),
  placebo_arb_direct_leg=f$placebo_arb, edge_k=f$edge_k, pscore=f$pscore,
  node_vs_placebo=f$nodes, league=f$league)

dir.create(dirname(OUT), showWarnings=FALSE, recursive=TRUE)
write(toJSON(list(schema="hfref-quarantine-primary/v1",
  generated_by="scripts/hfref_quarantine_primary.R", date="2026-07-30",
  settled_source=SETTLED, settled_prefix_lines=PREFIX_END,
  engine=paste0("R ",getRversion()," / netmeta ",packageVersion("netmeta")),
  cell_id=CELL_ID, coords=PC$coords, outcome="all-cause mortality",
  quarantine=list(ids=QUARANTINE,
    violation="no death data in source; 14/14/14 unsourced; primary is LVESVI",
    ledger="outputs/hfref_quarantine_ledger.json"),
  anchor_before=list(acei_bb_mra=0.59333495, acei_bb=0.64459765,
                     tau2=0.02323609, reproduced=anchor_ok),
  before=pack(B), after=pack(A), node_delta=nd,
  app_cells=lapply(APP_CELLS, function(cid) {
    cc <- Filter(function(x) x$cell_id == cid, CELLS)[[1]]
    # 7c already drops CARMEN in the settled definition; its "before" here is a
    # synthetic CARMEN-included variant kept only so the columns line up.
    list(cell_id=cid, label=cc$label, tier=cc$tier, coords=cc$coords,
         settled_already_drops_carmen = cid %in% DROP_CARMEN,
         before=pack(fitp(cc, character(0))),
         after =pack(fitp(cc, QUARANTINE)))
  })),
  auto_unbox=TRUE, digits=11, null="null", na="null"), file=OUT)
cat("\nWROTE ", OUT, "\n", sep="")
