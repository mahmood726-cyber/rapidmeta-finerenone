###############################################################################
# HFrEF GDMT NETWORK -- LEAGUE-TABLE BUNDLE EXPORT
# =============================================================================
# Written 2026-07-29.  Non-commercial evidence synthesis, RCT-only. PROTOTYPE.
#
# WHY THIS EXISTS
#   The settled fit lives in F:/E156/hfref_eightcell_fit.R and is NOT modified
#   by this script.  That script emits per-NODE estimates (each node vs
#   Placebo).  A league table needs every pairwise contrast, which requires the
#   covariance between basic parameters -- a quantity the settled script does
#   not serialise.  This sibling re-runs the settled fit and exports it.
#
# HOW IT AVOIDS TRANSCRIPTION RISK
#   The arm-level counts, the trial metadata, the eligibility ladder, the
#   contrast construction and the cell coordinates are NOT retyped here.  This
#   script evaluates lines 1..PREFIX_END of the settled script -- everything up
#   to and including fit_cell(), and nothing from its RUN/EMIT sections -- so
#   ARMS, META, CELLS, select_trials() and mk_contrasts() are the settled
#   definitions by construction.  If the settled script changes, this one
#   changes with it or fails the anchor.
#
# ANCHOR (hard gate; the script stops rather than emit an unverified bundle)
#   OURS-STRICT / all-cause mortality:
#     ACEI+BB+MRA  RR 0.59333495 (0.348-1.011)
#     ACEI+BB      RR 0.64459765 (0.433-0.959)
#     tau^2        0.02323609
#
# WRITES  (into this repository only -- never into F:/E156)
#   outputs/hfref_nma_bundle.json
###############################################################################

suppressMessages({
  library(netmeta)
  library(jsonlite)
})

SETTLED    <- "F:/E156/hfref_eightcell_fit.R"
PREFIX_END <- 587L   # last line of fit_cell(); section 8 (RUN) starts at 588
OUT        <- "outputs/hfref_nma_bundle.json"
PRIMARY    <- "OURS-STRICT"

if (!file.exists(SETTLED)) stop("settled fit script not found: ", SETTLED)

src <- readLines(SETTLED, warn = FALSE)
if (length(src) < PREFIX_END) stop("settled script is shorter than PREFIX_END")
if (!grepl("^\\}$", src[PREFIX_END]))
  stop("PREFIX_END no longer closes fit_cell(); refusing to eval a partial prefix")
if (!any(grepl("8\\. RUN", src[(PREFIX_END + 1):min(length(src), PREFIX_END + 6)])))
  stop("section 8 (RUN) is not immediately after PREFIX_END; settled script moved")

# Evaluate data + helpers only.  Nothing below fit_cell() runs, so the settled
# script's own emit step cannot fire and cannot write into F:/E156.
invisible(capture.output(
  eval(parse(text = paste(src[1:PREFIX_END], collapse = "\n")), envir = globalenv())
))

###############################################################################
# 1. RE-RUN THE PRIMARY CELL
#    Same coordinate read, same trial selection, same contrast construction and
#    the same HKSJ correction as fit_cell().  Duplicated here only because
#    fit_cell() returns summaries and discards the netmeta object we need.
###############################################################################

cl <- Filter(function(x) x$cell_id == PRIMARY, CELLS)
if (length(cl) != 1L) stop("cell ", PRIMARY, " not found in the settled CELLS list")
cl <- cl[[1]]
co <- cl$coords

ids <- select_trials(co)
if (cl$cell_id %in% DROP_CARMEN) ids <- setdiff(ids, "HF-021")
d   <- ARMS[ARMS$id %in% ids, ]
cn  <- mk_contrasts(d, emperor = co$emperor)
st  <- structure_of(cn)

rnd <- (co$estimand != "fe")
net <- netmeta(TE = TE, seTE = seTE, treat1 = treat1, treat2 = treat2,
               studlab = studlab, data = cn, sm = "RR",
               common = !rnd, random = rnd,
               method.tau = if (co$estimand == "reml") "REML" else "DL",
               reference.group = "Placebo", warn = FALSE,
               details.chkmultiarm = FALSE)

TEm <- if (rnd) net$TE.random else net$TE.common
SEm <- if (rnd) net$seTE.random else net$seTE.common

# HKSJ exactly as the settled script applies it: variance inflation by
# q = max(1, r'Wr/df) with the max(1,.) floor, and a t_df critical value.
hk <- list(applied = FALSE, q = 1, df = unname(net$df.Q), crit = qnorm(0.975))
if (isTRUE(co$hksj)) {
  fitted <- if (rnd) net$TE.nma.random else net$TE.nma.common
  w      <- 1 / (net$seTE^2 + (if (rnd) net$tau2 else 0))
  dfq    <- unname(net$df.Q)
  q      <- if (dfq > 0) max(1, sum(w * (net$TE - fitted)^2) / dfq) else 1
  hk <- list(applied = TRUE, q = unname(q), df = dfq,
             crit = if (dfq > 0) qt(0.975, dfq) else qnorm(0.975))
}
ci_mult <- hk$crit * sqrt(hk$q)

###############################################################################
# 2. ANCHOR GATE -- fail closed
###############################################################################

node_rr <- function(nd) unname(exp(TEm[nd, "Placebo"]))
node_lo <- function(nd) unname(exp(TEm[nd, "Placebo"] - ci_mult * SEm[nd, "Placebo"]))
node_hi <- function(nd) unname(exp(TEm[nd, "Placebo"] + ci_mult * SEm[nd, "Placebo"]))

anchor <- list(
  list(node = "ACEI+BB+MRA", rr = 0.59333495, lo = 0.348, hi = 1.011),
  list(node = "ACEI+BB",     rr = 0.64459765, lo = 0.433, hi = 0.959)
)
anchor_rows <- list(); anchor_ok <- TRUE
for (a in anchor) {
  got <- c(node_rr(a$node), node_lo(a$node), node_hi(a$node))
  ok  <- abs(got[1] - a$rr) < 1e-8 &&
         abs(got[2] - a$lo) < 5e-4 &&
         abs(got[3] - a$hi) < 5e-4
  anchor_ok <- anchor_ok && ok
  anchor_rows[[length(anchor_rows) + 1]] <- list(
    node = a$node, expected = c(a$rr, a$lo, a$hi), observed = got, pass = ok)
  cat(sprintf("ANCHOR %-12s expected %.8f (%.3f-%.3f)  observed %.8f (%.3f-%.3f)  %s\n",
              a$node, a$rr, a$lo, a$hi, got[1], got[2], got[3],
              if (ok) "PASS" else "FAIL"))
}
tau2 <- unname(if (rnd) net$tau2 else 0)
tau2_ok <- abs(tau2 - 0.02323609) < 1e-8
anchor_ok <- anchor_ok && tau2_ok
cat(sprintf("ANCHOR %-12s expected %.8f              observed %.8f              %s\n",
            "tau2", 0.02323609, tau2, if (tau2_ok) "PASS" else "FAIL"))
if (!anchor_ok)
  stop("ANCHOR FAILED -- the primary cell no longer reproduces the settled fit. ",
       "No bundle written.")
cat("ANCHOR: all rows PASS\n")

###############################################################################
# 3. BASIC-PARAMETER COVARIANCE
#    netmeta's Cov.random is indexed over ALL pairwise comparisons ("A:B").
#    The basic parameters are the 14 rows "<node>:Placebo".  Extracting that
#    submatrix gives Cov[A,A], Cov[B,B], Cov[A,B] so any contrast variance is
#    Var(A-B) = Cov[A,A] + Cov[B,B] - 2*Cov[A,B].
#    The full comparison-level diagonal is exported alongside it purely as an
#    independent cross-check: for every pair, the formula above must reproduce
#    the diagonal entry netmeta already holds for that comparison.
###############################################################################

COV <- if (rnd) net$Cov.random else net$Cov.common
if (is.null(COV)) stop("netmeta returned no covariance matrix")
cov_nm <- rownames(COV)

trts  <- net$trts
basic <- setdiff(trts, "Placebo")

# comparison labels in Cov are "t1:t2"; find the one matching an unordered pair
find_cmp <- function(a, b) {
  i <- match(paste0(a, ":", b), cov_nm)
  if (!is.na(i)) return(list(idx = i, sign = 1))
  i <- match(paste0(b, ":", a), cov_nm)
  if (!is.na(i)) return(list(idx = i, sign = -1))
  NULL
}

bp_idx <- integer(0); bp_sgn <- numeric(0); bp_nm <- character(0)
for (t in basic) {
  f <- find_cmp(t, "Placebo")
  if (is.null(f)) stop("no covariance entry for basic parameter ", t, " vs Placebo")
  bp_idx <- c(bp_idx, f$idx); bp_sgn <- c(bp_sgn, f$sign); bp_nm <- c(bp_nm, t)
}
# orient every basic parameter as <node> vs Placebo
S  <- diag(bp_sgn, nrow = length(bp_sgn))
CB <- S %*% COV[bp_idx, bp_idx, drop = FALSE] %*% S
dimnames(CB) <- list(bp_nm, bp_nm)

bp_te <- sapply(bp_nm, function(t) unname(TEm[t, "Placebo"]))

# ---- cross-check: formula variance vs netmeta's own comparison diagonal ----
maxdev <- 0; ncheck <- 0
for (i in seq_along(bp_nm)) for (j in seq_along(bp_nm)) {
  if (j <= i) next
  f <- find_cmp(bp_nm[i], bp_nm[j]); if (is.null(f)) next
  v_formula <- CB[i, i] + CB[j, j] - 2 * CB[i, j]
  v_netmeta <- COV[f$idx, f$idx]
  if (!is.finite(v_netmeta) || v_netmeta <= 0) next
  maxdev <- max(maxdev, abs(v_formula - v_netmeta) / v_netmeta); ncheck <- ncheck + 1
}
cat(sprintf("COV CROSS-CHECK: %d comparisons, max relative deviation %.3e\n",
            ncheck, maxdev))
cov_check_pass <- (ncheck > 0 && maxdev < 1e-8)
if (!cov_check_pass)
  stop("covariance cross-check FAILED (n=", ncheck, ", maxdev=", maxdev,
       ") -- the basic-parameter submatrix does not reproduce netmeta's own ",
       "comparison variances. No bundle written.")

###############################################################################
# 4. ARM-LEVEL TRIAL TABLE
#    Straight from the settled ARMS/META objects, restricted to the trials the
#    primary cell actually admits.  One row per ARM (trial x node), carrying the
#    node assignment and the events/N that produced the contrast.
###############################################################################

arm_rows <- list()
for (i in seq_len(nrow(d))) {
  mrow <- META[META$id == d$id[i], ]
  arm_rows[[length(arm_rows) + 1]] <- list(
    id      = d$id[i],
    trial   = d$trial[i],
    node    = d$treat[i],
    events  = as.integer(d$event[i]),
    n       = as.integer(d$n[i]),
    ef_ceiling = if (nrow(mrow) && !is.na(mrow$efceil[1])) unname(mrow$efceil[1]) else NULL,
    population = if (nrow(mrow)) as.character(mrow$pop[1]) else NULL)
}

contrast_rows <- lapply(seq_len(nrow(cn)), function(i) list(
  id = cn$id[i], trial = cn$studlab[i],
  treat1 = cn$treat1[i], treat2 = cn$treat2[i],
  TE = cn$TE[i], seTE = cn$seTE[i],
  event1 = as.integer(cn$event1[i]), n1 = as.integer(cn$n1[i]),
  event2 = as.integer(cn$event2[i]), n2 = as.integer(cn$n2[i])))

# trials the primary cell EXCLUDES, with the coordinate that evicted them
excluded <- list()
for (i in seq_len(nrow(META))) {
  if (META$id[i] %in% ids) next
  r <- META[i, ]
  # a trial may fail more than one coordinate; report every one that applies
  # rather than the first, so no exclusion looks narrower than it is
  why <- character(0)
  if (isTRUE(r$dupe))
    why <- c(why, "dupes=once (protocol paper of a pooled report)")
  if (!is.na(r$efceil) && r$efceil > 40)
    why <- c(why, sprintf("ef=le40 (EF ceiling %g%% > 40%%)", r$efceil))
  if (r$pop != "chronic")
    why <- c(why, sprintf("pop=chronic (population is %s)", r$pop))
  if (r$drop_at != "never" && ELIG_ORDER[[r$drop_at]] <= ELIG_ORDER[[co$elig]])
    why <- c(why, sprintf("elig=%s (evicted at %s)", co$elig, r$drop_at))
  if (!length(why)) why <- "unclassified"
  nm <- unique(ARMS$trial[ARMS$id == r$id])
  excluded[[length(excluded) + 1]] <- list(id = r$id, trial = nm[1],
                                           reasons = unname(why),
                                           reason = paste(why, collapse = "; "))
}

###############################################################################
# 5. EMIT
###############################################################################

dir.create(dirname(OUT), showWarnings = FALSE, recursive = TRUE)

bundle <- list(
  schema  = "hfref-nma-bundle/v1",
  generated_by = "scripts/hfref_league_bundle.R",
  settled_source = SETTLED,
  settled_prefix_lines = PREFIX_END,
  engine  = paste0("R ", getRversion(), " / netmeta ", packageVersion("netmeta")),
  cell    = list(cell_id = cl$cell_id, label = cl$label, tier = cl$tier,
                 coords = co, scale = cl$scale),
  outcome = "all-cause mortality",
  anchor  = list(pass = anchor_ok, rows = unname(anchor_rows),
                 tau2 = list(expected = 0.02323609, observed = tau2, pass = tau2_ok)),
  model   = list(estimand = co$estimand, tau2 = tau2, i2 = unname(net$I2),
                 df_Q = unname(net$df.Q), Q = unname(net$Q),
                 hksj = hk, ci_multiplier = ci_mult,
                 reference = "Placebo"),
  structure = st,
  treatments = trts,
  basic_parameters = list(
    reference = "Placebo",
    order = bp_nm,
    log_rr = unname(bp_te),
    note = paste0("log-RR of each node vs Placebo. Var(A-B) = Cov[A,A] + ",
                  "Cov[B,B] - 2*Cov[A,B]; multiply sqrt(Var) by ci_multiplier ",
                  "for the 95% interval."),
    cov = unname(lapply(seq_len(nrow(CB)), function(i) unname(CB[i, ])))),
  covariance_cross_check = list(
    comparisons_checked = ncheck, max_rel_dev = maxdev, pass = cov_check_pass,
    note = paste0("Independent check that the basic-parameter submatrix ",
                  "reproduces netmeta's own comparison-level variances.")),
  trials = list(
    n_included = length(unique(cn$studlab)),
    included_ids = sort(unique(ids)),
    included_names = sort(unique(cn$studlab)),
    n_arms = length(arm_rows),
    arms = unname(arm_rows),
    contrasts = unname(contrast_rows),
    excluded = unname(excluded))
)

write(toJSON(bundle, auto_unbox = TRUE, digits = 12, null = "null", na = "null"),
      file = OUT)
cat("WROTE ", OUT, "\n", sep = "")
cat(sprintf("  trials=%d  arms=%d  contrasts=%d  nodes=%d  basic params=%d\n",
            bundle$trials$n_included, length(arm_rows), nrow(cn),
            length(trts), length(bp_nm)))
