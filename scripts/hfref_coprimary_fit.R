###############################################################################
# hfref_coprimary_fit.R -- the CO-PRIMARY re-fit.
#
# Supersedes scripts/hfref_quarantine_primary.R, which quarantined ONE of the
# three trials that meet the integrity rule and presented only the quarantined
# fit. Two corrections, both required by the cross-family gate:
#
#   1. SYMMETRIC QUARANTINE. The rule is "unverified per-arm all-cause deaths
#      AND identical across-arm counts". BOTH limbs are required, so verifying
#      the counts clears a trial even when they stay identical. Two trials in
#      the settled network now meet the rule:
#        HF-021 CARMEN       14/14/14, 572 pts
#        HF-025 Vizzardi 2014 8/8, 130 pts
#      See outputs/hfref_quarantine_ledger.json for the named violation and the
#      reinstatement condition attached to each.
#
#      HF-034 GALACTIC-HF (1078/1078, 8232 pts) was quarantined on 2026-07-30
#      and is REINSTATED here. Its counts are still identical across arms, but
#      they are no longer unverified: the ClinicalTrials.gov NCT02929329 posted
#      results carry per-arm ALL-CAUSE deaths as verbatim integers in the FDAAA
#      All-Cause Mortality table -- 1078/4112 placebo, 1078/4120 omecamtiv --
#      matching the extraction exactly in both arms, on the same denominators
#      the publication reports for its primary outcome. The identical count is a
#      genuine coincidence. Recovery evidence and the frame distinctions:
#        scripts/hfref_recover_galactic_allcause.py
#        outputs/hfref_galactic_allcause_recovery.json
#      Because GALACTIC-HF is the only trial supplying +Omecamtiv, reinstating
#      it RESTORES that node to the quarantined network (V 14 -> 15).
#
#   2. CO-PRIMARY, NOT REPLACEMENT. Both fits are emitted and both are carried
#      by the app. The FULL network is the conservative co-primary; the
#      quarantined network is a PROVENANCE SENSITIVITY, and must never be
#      presented as stronger evidence. The measured direction is two-sided and
#      the script reports both halves rather than the convenient one: most
#      retained nodes' POINT ESTIMATES move away from the null, but INTERVAL
#      significance FALLS (tau^2 rises, HKSJ df drops, CIs widen). Neither half
#      makes the quarantined fit stronger.
#
# Same discipline as the scripts it supersedes: evaluates lines 1..587 of the
# settled fit (up to and including fit_cell(), nothing from RUN or EMIT), so
# ARMS, META, CELLS, select_trials() and mk_contrasts() are the settled
# definitions. The settled script's emit cannot fire and F:/E156 is never
# written. F:/E156/hfref_eightcell_fit.R is READ-ONLY here.
#
# ANCHOR GATE: the FULL fit must reproduce the settled primary
#   ACEI+BB+MRA 0.59333495   ACEI+BB 0.64459765   tau^2 0.02323609
# or this script refuses to emit.
###############################################################################

suppressMessages({ library(netmeta); library(jsonlite) })

SETTLED <- "F:/E156/hfref_eightcell_fit.R"; PREFIX_END <- 587L
OUT      <- "outputs/hfref_coprimary_fit.json"
CELL_ID  <- "OURS-STRICT"
APP_CELLS <- c("OURS-STRICT","OURS-INCLUSIVE","OURS-STRICT-7b","OURS-STRICT-7c")

# The symmetric quarantine set. Every id here has a named violation and a
# reinstatement condition in outputs/hfref_quarantine_ledger.json.
QUARANTINE <- c("HF-021", "HF-025")
QV <- list(
  "HF-021" = "unverified per-arm all-cause deaths (14/14/14) identical across all three arms; primary endpoint is LVESVI and the source reports no deaths",
  "HF-025" = "unverified per-arm all-cause deaths (8/8) identical across both arms; the source reports only composite event-free survival")

# Reinstated: quarantined 2026-07-30, cleared the same day by the registry route
# the ledger named as its reinstatement condition. Kept here (not deleted) so the
# quarantine record stays auditable -- see the ledger for the full disposition.
REINSTATED <- list("HF-034" = paste0(
  "GALACTIC-HF -- counts remain identical across arms (1078/1078) but are no ",
  "longer unverified. ClinicalTrials.gov NCT02929329 posted results state ",
  "per-arm ALL-CAUSE deaths as verbatim integers (1078/4112 placebo, ",
  "1078/4120 omecamtiv), matching the extraction exactly. The rule requires ",
  "unverified AND identical; only the second limb still holds, so the trial ",
  "is retained in BOTH co-primary fits and the +Omecamtiv node survives."))

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
  d   <- ARMS[ARMS$id %in% ids, ]
  cn  <- mk_contrasts(d, emperor = co$emperor)
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
       trial_ids=sort(ids),
       arm_rows=nrow(d),
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

# ---- co-primary (a): the FULL network, all trials retained -------------------
FULL <- fitp(PC, character(0))
A0 <- g(FULL,"ACEI+BB+MRA"); B0 <- g(FULL,"ACEI+BB")
anchor_ok <- abs(A0$rr-0.59333495)<1e-8 && abs(B0$rr-0.64459765)<1e-8 &&
             abs(FULL$tau2-0.02323609)<1e-8

cat("=== CO-PRIMARY (a): FULL NETWORK -- all trials retained ===\n")
cat(sprintf("trials=%d arm_rows=%d contrasts=%d V=%d E=%d designs=%d cyclomatic=%d ICDF=%d internal_loops=%d\n",
  FULL$trials,FULL$arm_rows,FULL$contrasts,FULL$st$V,FULL$st$E,FULL$st$designs,
  FULL$st$cyclomatic,FULL$st$icdf,FULL$st$multiarm_internal_loops))
cat(sprintf("tau2=%.8f I2=%.4f HKSJ q=%.6f df=%d mult=%.6f\n",
  FULL$tau2,FULL$i2,FULL$hksj$q,FULL$hksj$df,FULL$hksj$multiplier))
cat(sprintf("ANCHOR %s : ACEI+BB %.8f  ACEI+BB+MRA %.8f  tau2 %.8f\n",
  if (anchor_ok) "PASS" else "FAIL", B0$rr, A0$rr, FULL$tau2))
if (!anchor_ok) fail("FULL network does not reproduce the settled primary anchor")

# ---- co-primary (b): the integrity-quarantined network -----------------------
QUAR <- fitp(PC, QUARANTINE)
A1 <- g(QUAR,"ACEI+BB+MRA"); B1 <- g(QUAR,"ACEI+BB")
cat("\n=== CO-PRIMARY (b): INTEGRITY-QUARANTINED NETWORK ===\n")
cat(sprintf("quarantined: %s\n", paste(QUARANTINE, collapse=", ")))
cat(sprintf("trials=%d arm_rows=%d contrasts=%d V=%d E=%d designs=%d cyclomatic=%d ICDF=%d internal_loops=%d\n",
  QUAR$trials,QUAR$arm_rows,QUAR$contrasts,QUAR$st$V,QUAR$st$E,QUAR$st$designs,
  QUAR$st$cyclomatic,QUAR$st$icdf,QUAR$st$multiarm_internal_loops))
cat(sprintf("tau2=%.8f I2=%.4f HKSJ q=%.6f df=%d mult=%.6f\n",
  QUAR$tau2,QUAR$i2,QUAR$hksj$q,QUAR$hksj$df,QUAR$hksj$multiplier))
cat(sprintf("QUARANTINED ANCHOR: ACEI+BB %.8f  ACEI+BB+MRA %.8f\n", B1$rr, A1$rr))
cat(sprintf("arm rows %d -> %d | contrasts %d -> %d | trials %d -> %d\n",
  FULL$arm_rows, QUAR$arm_rows, FULL$contrasts, QUAR$contrasts,
  FULL$trials, QUAR$trials))
cat(sprintf("nodes lost: %s\n",
  { L <- setdiff(FULL$trts,QUAR$trts); if (length(L)) paste(L,collapse=", ") else "(none)" }))
cat(sprintf("edges lost: %s\n",
  { L <- setdiff(names(FULL$edge_k), names(QUAR$edge_k))
    if (length(L)) paste(L,collapse=", ") else "(none)" }))

cat("\n=== NODE vs Placebo: FULL -> QUARANTINED ===\n")
cat(sprintf("%-14s %24s %24s %9s\n","node","FULL RR (95% CI)","QUARANTINED RR (95% CI)","d(RR)%"))
nd <- list()
for (nm in sapply(FULL$nodes, function(x) x$node)) {
  b <- g(FULL,nm); a <- g(QUAR,nm)
  if (is.null(a)) {
    cat(sprintf("%-14s %24s %24s %9s\n", nm,
      sprintf("%.3f (%.3f-%.3f)",b$rr,b$lo,b$hi),"NODE LOST","--"))
    nd[[length(nd)+1]] <- list(node=nm, full=b, quarantined=NULL, node_lost=TRUE); next
  }
  d <- 100*(a$rr-b$rr)/b$rr
  cat(sprintf("%-14s %24s %24s %+8.2f%%\n", nm,
    sprintf("%.3f (%.3f-%.3f)",b$rr,b$lo,b$hi),
    sprintf("%.3f (%.3f-%.3f)",a$rr,a$lo,a$hi), d))
  nd[[length(nd)+1]] <- list(node=nm, full=b, quarantined=a, rel_change_pct=d,
                             node_lost=FALSE)
}
cat(sprintf("\nleague pairs %d -> %d | CI excludes 1: %d -> %d | with direct: %d -> %d\n",
  length(FULL$league),length(QUAR$league),FULL$n_excl,QUAR$n_excl,
  FULL$n_direct,QUAR$n_direct))
cat(sprintf("Placebo-ARB direct leg: k=%d/%d ev -> k=%d/%d ev\n",
  FULL$placebo_arb$k,FULL$placebo_arb$events,
  QUAR$placebo_arb$k,QUAR$placebo_arb$events))
# ---- like-for-like direction analysis on the pairs BOTH fits estimate --------
# The quarantined network loses whole league pairs when a node dies, so the raw
# CI-excludes-1 counts are not comparable. Restrict to the common pairs.
pk2 <- function(p) paste(p$t1, p$t2, sep = "|")
FL <- setNames(FULL$league, sapply(FULL$league, pk2))
QL <- setNames(QUAR$league, sapply(QUAR$league, pk2))
common <- intersect(names(FL), names(QL))
lostpairs <- setdiff(names(FL), names(QL))
exc  <- function(p) (p$lo > 1 || p$hi < 1)
f_ex <- sum(sapply(common, function(k) exc(FL[[k]])))
q_ex <- sum(sapply(common, function(k) exc(QL[[k]])))
gained  <- common[sapply(common, function(k) !exc(FL[[k]]) &&  exc(QL[[k]]))]
lost_sg <- common[sapply(common, function(k)  exc(FL[[k]]) && !exc(QL[[k]]))]
rr_chg  <- sapply(common, function(k) 100*(QL[[k]]$rr - FL[[k]]$rr)/FL[[k]]$rr)
wid_chg <- sapply(common, function(k)
  100*(((QL[[k]]$hi/QL[[k]]$lo)/(FL[[k]]$hi/FL[[k]]$lo)) - 1))
# node-level point-estimate move, retained nodes only
retained <- Filter(function(x) !x$node_lost, nd)
node_rr_chg <- sapply(retained, function(x) x$rel_change_pct)
# COUNT the direction rather than asserting it. Earlier passes of this script
# claimed "every retained treatment node falls"; that was never true -- the
# nodes supplied only by pendant edges off the quarantined trials move the other
# way, and BB moves sharply up when CARMEN's ACEI+BB vs BB edge is withheld.
# Overstating the unfavourable direction is still misreporting, so the flag now
# reports the split it actually measures.
n_node_down <- sum(node_rr_chg < 0); n_node_up <- sum(node_rr_chg > 0)
n_node_flat <- sum(node_rr_chg == 0)
node_up_names <- sapply(retained, function(x) x$node)[node_rr_chg > 0]
node_worst_up <- if (n_node_up) retained[[which.max(node_rr_chg)]]$node else NA_character_

cat("\n=== DIRECTION (like-for-like on the ", length(common),
    " pairs BOTH fits estimate) ===\n", sep="")
cat(sprintf("CI excludes 1: FULL %d -> QUARANTINED %d | gained %d, lost %d\n",
  f_ex, q_ex, length(gained), length(lost_sg)))
cat(sprintf("point-estimate RR change: median %+.2f%% (min %+.2f%%, max %+.2f%%)\n",
  median(rr_chg), min(rr_chg), max(rr_chg)))
cat(sprintf("CI-width ratio change:    median %+.2f%% (min %+.2f%%, max %+.2f%%)\n",
  median(wid_chg), min(wid_chg), max(wid_chg)))
cat(sprintf("league pairs dropped entirely: %d%s\n", length(lostpairs),
  if (length(lostpairs)) " (all involve a lost node)" else
    " -- every league pair the full fit estimates is still estimable"))
cat("\nHONEST DIRECTION FLAG -- two parts, both true, neither favourable:\n")
cat(sprintf("  (1) POINT ESTIMATES mostly move AWAY from the null: %d of %d retained\n",
  n_node_down, length(node_rr_chg)))
cat(sprintf("      treatment nodes fall (median %+.2f%%); %d rise%s. This is the\n",
  median(node_rr_chg), n_node_up,
  if (n_node_up) paste0(" (largest ", node_worst_up, " ",
                        sprintf("%+.2f%%", max(node_rr_chg)), ")") else ""))
cat("      direction the gate warned about and it is real for the majority of\n")
cat("      nodes. It must NOT be read as benefit.\n")
cat(sprintf("  (2) INTERVAL significance FALLS: %d -> %d of the common pairs exclude 1.\n",
  f_ex, q_ex))
cat(sprintf("      tau2 rises %+.1f%%, I2 %.1f%% -> %.1f%%, HKSJ df %d -> %d, so CIs\n",
  100*(QUAR$tau2/FULL$tau2 - 1), 100*FULL$i2, 100*QUAR$i2,
  FULL$hksj$df, QUAR$hksj$df))
cat(sprintf("      widen (median %+.2f%%). %d pairs gain significance; %d lose it.\n",
  median(wid_chg), length(gained), length(lost_sg)))
cat("The quarantined fit is a PROVENANCE SENSITIVITY, not stronger evidence.\n")
cat("The FULL network is the conservative co-primary. Both must be displayed.\n")

pack <- function(f) list(trials=f$trials, trial_names=f$trial_names,
  trial_ids=f$trial_ids, arm_rows=f$arm_rows,
  contrasts=f$contrasts, tau2=f$tau2, i2=f$i2, hksj=f$hksj, structure=f$st,
  counts=list(estimable=length(f$league), with_direct=f$n_direct,
              indirect_only=length(f$league)-f$n_direct, ci_excludes_null=f$n_excl),
  placebo_arb_direct_leg=f$placebo_arb, edge_k=f$edge_k, pscore=f$pscore,
  node_vs_placebo=f$nodes, league=f$league)

dir.create(dirname(OUT), showWarnings=FALSE, recursive=TRUE)
write(toJSON(list(schema="hfref-coprimary-fit/v1",
  generated_by="scripts/hfref_coprimary_fit.R", date="2026-07-30",
  supersedes="scripts/hfref_quarantine_primary.R (single-trial quarantine, quarantined fit presented alone)",
  settled_source=SETTLED, settled_prefix_lines=PREFIX_END,
  settled_source_mode="READ-ONLY; prefix evaluated, RUN/EMIT never reached",
  engine=paste0("R ",getRversion()," / netmeta ",packageVersion("netmeta")),
  cell_id=CELL_ID, coords=PC$coords, outcome="all-cause mortality",
  presentation=list(
    mode="CO-PRIMARY",
    conservative_coprimary="full",
    sensitivity="quarantined",
    direction_flag=paste0(
      "Removing these unverified identical-count trials moves MOST retained ",
      "treatment nodes' POINT ESTIMATES away from the null -- ", n_node_down,
      " of ", length(node_rr_chg), " fall (median ",
      sprintf("%+.2f%%", median(node_rr_chg)), "), ", n_node_up, " rise",
      if (n_node_up) paste0(" (largest ", node_worst_up, " ",
                            sprintf("%+.2f%%", max(node_rr_chg)), ")") else "",
      ". That is the direction the ",
      "gate warned about and it is real for the majority of nodes: it must not ",
      "be read as benefit. But ",
      "INTERVAL significance FALLS, not rises -- on the ", length(common),
      " pairs both fits estimate, CI-excludes-1 goes ", f_ex, " -> ", q_ex,
      " (", length(gained), " gain, ", length(lost_sg), " lose), because tau2 rises ",
      sprintf("%+.1f%%", 100*(QUAR$tau2/FULL$tau2 - 1)), ", I2 goes ",
      sprintf("%.1f%% -> %.1f%%", 100*FULL$i2, 100*QUAR$i2),
      ", HKSJ df falls ", FULL$hksj$df, " -> ", QUAR$hksj$df,
      " and CIs widen (median ", sprintf("%+.2f%%", median(wid_chg)), "). ",
      "Neither reading makes the quarantined fit stronger evidence. It is a ",
      "PROVENANCE SENSITIVITY. The full-network fit is the conservative ",
      "co-primary and must be shown alongside it."),
    direction_detail=list(
      common_pairs=length(common),
      pairs_dropped_with_lost_node=length(lostpairs),
      ci_excludes_null_common=list(full=f_ex, quarantined=q_ex),
      gained_significance=as.list(gained),
      lost_significance=as.list(lost_sg),
      node_point_estimate_pct_change=list(
        median=median(node_rr_chg), min=min(node_rr_chg), max=max(node_rr_chg),
        retained_nodes=length(node_rr_chg),
        moved_away_from_null=n_node_down, moved_toward_null=n_node_up,
        unchanged=n_node_flat,
        nodes_moving_toward_null=as.list(node_up_names),
        largest_move_toward_null=list(node=node_worst_up, pct=max(node_rr_chg)),
        counted_not_asserted=paste0(
          "Earlier passes of this script claimed EVERY retained node moves away ",
          "from the null. That was never true and is now measured instead: the ",
          "nodes supplied only by pendant edges are unaffected in the other ",
          "direction, and BB moves sharply toward/past the null when CARMEN's ",
          "ACEI+BB vs BB edge is withheld. Overstating the unfavourable ",
          "direction is still misreporting.")),
      pair_ci_width_pct_change=list(
        median=median(wid_chg), min=min(wid_chg), max=max(wid_chg)),
      note=paste0(
        "Two earlier passes are superseded. (1) The single-trial (CARMEN-only) ",
        "re-fit reported CI-excludes-1 rising 12 -> 17; that rise was an ",
        "artefact of an ASYMMETRIC quarantine. (2) The three-trial symmetric ",
        "pass (CARMEN + GALACTIC-HF + Vizzardi 2014) lost the +Omecamtiv node ",
        "outright and reported 12 -> 9 on 91 common pairs. GALACTIC-HF has ",
        "since been REINSTATED on verified registry counts, so the quarantine ",
        "set is CARMEN + Vizzardi 2014 and +Omecamtiv is restored. Compare the ",
        "current figures above against that history, not against either ",
        "superseded pass."))),
  quarantine=list(ids=QUARANTINE, rule=paste0(
      "unverified per-arm all-cause deaths AND identical across-arm counts"),
    violations=QV,
    reinstated=REINSTATED,
    reinstated_ids=as.list(names(REINSTATED)),
    ledger="outputs/hfref_quarantine_ledger.json"),
  anchor=list(
    full=list(acei_bb=B0$rr, acei_bb_mra=A0$rr, tau2=FULL$tau2,
              expected_acei_bb=0.64459765, expected_acei_bb_mra=0.59333495,
              expected_tau2=0.02323609, reproduced=anchor_ok),
    quarantined=list(acei_bb=B1$rr, acei_bb_mra=A1$rr, tau2=QUAR$tau2)),
  full=pack(FULL), quarantined=pack(QUAR), node_delta=nd,
  app_cells=lapply(APP_CELLS, function(cid) {
    cc <- Filter(function(x) x$cell_id == cid, CELLS)[[1]]
    # 7c already drops CARMEN in the settled definition; its "full" here is a
    # synthetic CARMEN-included variant kept only so the columns line up.
    list(cell_id=cid, label=cc$label, tier=cc$tier, coords=cc$coords,
         settled_already_drops_carmen = cid %in% DROP_CARMEN,
         full=pack(fitp(cc, character(0))),
         quarantined=pack(fitp(cc, QUARANTINE)))
  })),
  auto_unbox=TRUE, digits=11, null="null", na="null"), file=OUT)
cat("\nWROTE ", OUT, "\n", sep="")
