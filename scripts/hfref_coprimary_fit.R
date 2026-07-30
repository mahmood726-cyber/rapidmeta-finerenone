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
#      Direction is measured as |ln RR| (distance from the null), never as
#      sign(rel_change_pct). BB is why: RR 0.996110 -> 1.359354 CROSSES RR=1, so
#      the sign test books a 79x move AWAY from the null as a move toward it.
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
cat(sprintf("%-14s %24s %24s %9s %8s %-14s\n","node","FULL RR (95% CI)",
            "QUARANTINED RR (95% CI)","d(RR)%","d|lnRR|","direction"))
nd <- list()
for (nm in sapply(FULL$nodes, function(x) x$node)) {
  b <- g(FULL,nm); a <- g(QUAR,nm)
  if (is.null(a)) {
    cat(sprintf("%-14s %24s %24s %9s\n", nm,
      sprintf("%.3f (%.3f-%.3f)",b$rr,b$lo,b$hi),"NODE LOST","--"))
    nd[[length(nd)+1]] <- list(node=nm, full=b, quarantined=NULL, node_lost=TRUE); next
  }
  d <- 100*(a$rr-b$rr)/b$rr
  # DIRECTION IS DISTANCE FROM THE NULL, NOT THE SIGN OF THE RR CHANGE.
  # sign(rel_change_pct) is only a valid direction test while RR stays on one
  # side of 1. BB does not: 0.996110 -> 1.359354 crosses to the HARM side, so a
  # +36.47% "rise" is a move 79x FURTHER from the null, not a move toward it.
  # Keying on |ln RR| is sign-agnostic and handles the crossing correctly.
  afl <- abs(log(b$rr)); aql <- abs(log(a$rr)); dabs <- aql - afl
  crosses <- (b$rr - 1) * (a$rr - 1) < 0
  dirn <- if (dabs > 0) "away_from_null" else
          if (dabs < 0) "toward_null" else "unchanged"
  cat(sprintf("%-14s %24s %24s %+8.2f%% %+8.4f %-14s%s\n", nm,
    sprintf("%.3f (%.3f-%.3f)",b$rr,b$lo,b$hi),
    sprintf("%.3f (%.3f-%.3f)",a$rr,a$lo,a$hi), d, dabs, dirn,
    if (crosses) "  CROSSES THE NULL" else ""))
  nd[[length(nd)+1]] <- list(node=nm, full=b, quarantined=a, rel_change_pct=d,
                             abs_log_rr_full=afl, abs_log_rr_quarantined=aql,
                             abs_log_rr_change=dabs, direction=dirn,
                             crosses_null=crosses,
                             fold_further_from_null=if (afl > 0) aql/afl else NA_real_,
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
# COUNT the direction rather than asserting it, and count it on the RIGHT
# quantity. Two successive errors are corrected here:
#
#   (i)  Earlier passes claimed "every retained treatment node falls". Never true.
#   (ii) The fix for (i) keyed direction on sign(rel_change_pct), which is only
#        valid while RR stays on one side of 1. BB does not: 0.996110 ->
#        1.359354 CROSSES to the harm side, so its +36.47% was booked as a move
#        TOWARD the null when it is in fact the LARGEST move AWAY from it
#        (|ln RR| 0.003898 -> 0.307010, ~79x further). That understated exactly
#        the unfavourable direction this flag exists to surface.
#
# Direction is therefore distance from the null, |ln RR|, which is sign-agnostic
# and handles null-crossing correctly. rel_change_pct is retained as a
# descriptive only; it never decides direction.
node_dabs   <- sapply(retained, function(x) x$abs_log_rr_change)
node_names  <- sapply(retained, function(x) x$node)
node_cross  <- sapply(retained, function(x) isTRUE(x$crosses_null))
n_node_away <- sum(node_dabs > 0)
n_node_tow  <- sum(node_dabs < 0)
n_node_flat <- sum(node_dabs == 0)
node_away_names <- node_names[node_dabs > 0]
node_tow_names  <- node_names[node_dabs < 0]
cross_names <- node_names[node_cross]
mk_worst <- function(idx) {
  if (!length(idx)) return(NULL)
  x <- retained[[idx]]
  list(node=x$node, rr_full=x$full$rr, rr_quarantined=x$quarantined$rr,
       abs_log_rr_full=x$abs_log_rr_full,
       abs_log_rr_quarantined=x$abs_log_rr_quarantined,
       abs_log_rr_change=x$abs_log_rr_change,
       fold_further_from_null=x$fold_further_from_null,
       rel_change_pct=x$rel_change_pct, crosses_null=x$crosses_null)
}
worst_away <- mk_worst(if (n_node_away) which.max(node_dabs) else integer(0))
worst_tow  <- mk_worst(if (n_node_tow)  which.min(node_dabs) else integer(0))
# Legacy alias kept so nothing silently reads a stale meaning: it now points at
# the genuine largest toward-null move, and BB is no longer in that set.
node_worst_up <- if (!is.null(worst_tow)) worst_tow$node else NA_character_

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
cat(sprintf("node distance from the null (|ln RR|): %d of %d move AWAY, %d move TOWARD\n",
  n_node_away, length(node_dabs), n_node_tow))
cat(sprintf("  toward-null nodes: %s\n",
  if (n_node_tow) paste(node_tow_names, collapse=", ") else "(none)"))
if (length(cross_names))
  cat(sprintf("  CROSSES THE NULL: %s\n", paste(cross_names, collapse=", ")))
cat("\nHONEST DIRECTION FLAG -- two parts, both true, neither favourable:\n")
cat(sprintf("  (1) POINT ESTIMATES mostly move AWAY from the null: %d of %d retained\n",
  n_node_away, length(node_dabs)))
cat(sprintf("      treatment nodes move FURTHER from RR=1 (median d|lnRR| %+.4f);\n",
  median(node_dabs)))
cat(sprintf("      only %d move toward it%s.\n", n_node_tow,
  if (n_node_tow) paste0(" (", paste(node_tow_names, collapse=", "), ")") else ""))
if (!is.null(worst_away))
  cat(sprintf("      Largest move AWAY: %s, RR %.6f -> %.6f (|lnRR| %.6f -> %.6f,\n      %.1fx further from the null)%s\n",
    worst_away$node, worst_away$rr_full, worst_away$rr_quarantined,
    worst_away$abs_log_rr_full, worst_away$abs_log_rr_quarantined,
    worst_away$fold_further_from_null,
    if (isTRUE(worst_away$crosses_null))
      " -- and it CROSSES THE NULL onto the HARM side." else "."))
cat("      Direction is measured as |ln RR|, NOT the sign of the RR change: a\n")
cat("      node crossing RR=1 rises in RR while moving FURTHER from the null.\n")
cat("      This is the direction the gate warned about. It must NOT be read as\n")
cat("      benefit, and it must not be softened.\n")
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
      "treatment nodes' POINT ESTIMATES FURTHER FROM THE NULL -- ", n_node_away,
      " of ", length(node_dabs), " move away (median d|lnRR| ",
      sprintf("%+.4f", median(node_dabs)), "), only ", n_node_tow, " move toward it",
      if (n_node_tow) paste0(" (", paste(node_tow_names, collapse=", "), ")") else "",
      ". ",
      if (!is.null(worst_away)) paste0(
        "The largest move away is ", worst_away$node, ", RR ",
        sprintf("%.6f", worst_away$rr_full), " -> ",
        sprintf("%.6f", worst_away$rr_quarantined), " (|lnRR| ",
        sprintf("%.6f", worst_away$abs_log_rr_full), " -> ",
        sprintf("%.6f", worst_away$abs_log_rr_quarantined), ", ",
        sprintf("%.1f", worst_away$fold_further_from_null),
        "x further from the null)",
        if (isTRUE(worst_away$crosses_null))
          ", and it CROSSES THE NULL onto the HARM side" else "", ". ") else "",
      "Direction is measured as distance from the null, |ln RR|, NOT the sign of ",
      "the RR change: a node that crosses RR=1 RISES in RR while moving FURTHER ",
      "from the null, and keying on the sign books that as a move toward the ",
      "null -- understating exactly the unfavourable direction this flag exists ",
      "to surface. That is the direction the ",
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
        direction_basis=paste0(
          "|ln RR| -- distance from the null. Sign-agnostic, so a node crossing ",
          "RR=1 is classified by how far it ends up from 1, not by whether RR ",
          "went up or down. rel_change_pct is carried per node as a DESCRIPTIVE ",
          "ONLY and never decides direction."),
        median_abs_log_rr_change=median(node_dabs),
        min_abs_log_rr_change=min(node_dabs),
        max_abs_log_rr_change=max(node_dabs),
        rel_change_pct_descriptive_only=list(
          median=median(node_rr_chg), min=min(node_rr_chg), max=max(node_rr_chg)),
        retained_nodes=length(node_dabs),
        moved_away_from_null=n_node_away, moved_toward_null=n_node_tow,
        unchanged=n_node_flat,
        nodes_moving_away_from_null=as.list(node_away_names),
        nodes_moving_toward_null=as.list(node_tow_names),
        nodes_crossing_null=as.list(cross_names),
        largest_move_away_from_null=worst_away,
        largest_move_toward_null=worst_tow,
        counted_not_asserted=paste0(
          "Two errors are corrected here, in order. (1) Earlier passes claimed ",
          "EVERY retained node moves away from the null; never true. (2) The fix ",
          "for (1) keyed direction on sign(rel_change_pct), which is only valid ",
          "while RR stays on one side of 1. BB does not: RR 0.996110 -> 1.359354 ",
          "CROSSES to the harm side, so its +36.47% was booked as a move TOWARD ",
          "the null when it is the LARGEST move AWAY from it (|ln RR| 0.003898 ",
          "-> 0.307010, ~79x further). That understated exactly the unfavourable ",
          "direction this flag exists to surface. Overstating the unfavourable ",
          "direction is misreporting; understating it is worse.")),
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
