###############################################################################
# HFrEF LEAGUE TABLE -- INDEPENDENT VERIFICATION
# =============================================================================
# The league table in outputs/hfref_league_table.json is built in Python from a
# serialised covariance matrix, via
#     Var(A-B) = Cov[A,A] + Cov[B,B] - 2*Cov[A,B].
# That is a derivation, and a derivation can be wrong in a way that still looks
# self-consistent.  This script re-fits the settled primary cell from scratch
# and compares EVERY published contrast against netmeta's own TE.random /
# seTE.random for that pair -- numbers the Python path never touches.
#
# Exits non-zero on any disagreement, on a missing table, or on a table whose
# contrast set does not match the fitted network.  A gate that cannot fail is
# not a gate.
#
# Run from the repository root:
#   Rscript scripts/hfref_league_verify.R
###############################################################################

suppressMessages({
  library(netmeta)
  library(jsonlite)
})

SETTLED    <- "F:/E156/hfref_eightcell_fit.R"
PREFIX_END <- 587L
TABLE      <- "outputs/hfref_league_table.json"
TOL        <- 1e-9

fail <- function(...) { cat("FAIL: ", ..., "\n", sep = ""); quit(status = 1) }

if (!file.exists(SETTLED)) fail("settled fit script not found: ", SETTLED)
if (!file.exists(TABLE))   fail("league table not found: ", TABLE)

src <- readLines(SETTLED, warn = FALSE)
if (!grepl("^\\}$", src[PREFIX_END])) fail("PREFIX_END no longer closes fit_cell()")
invisible(capture.output(
  eval(parse(text = paste(src[1:PREFIX_END], collapse = "\n")), envir = globalenv())))

cl <- Filter(function(x) x$cell_id == "OURS-STRICT", CELLS)
if (length(cl) != 1L) fail("OURS-STRICT not found in settled CELLS")
cl <- cl[[1]]; co <- cl$coords

d   <- ARMS[ARMS$id %in% select_trials(co), ]
cn  <- mk_contrasts(d, emperor = co$emperor)
net <- netmeta(TE = TE, seTE = seTE, treat1 = treat1, treat2 = treat2,
               studlab = studlab, data = cn, sm = "RR",
               common = FALSE, random = TRUE, method.tau = "REML",
               reference.group = "Placebo", warn = FALSE,
               details.chkmultiarm = FALSE)

# --- anchor first: a matching table built on a drifted fit is still wrong ----
anch <- list(list("ACEI+BB+MRA", 0.59333495), list("ACEI+BB", 0.64459765))
for (a in anch) {
  got <- unname(exp(net$TE.random[a[[1]], "Placebo"]))
  if (abs(got - a[[2]]) > 1e-8)
    fail(sprintf("anchor %s: expected %.8f, got %.8f", a[[1]], a[[2]], got))
}
if (abs(unname(net$tau2) - 0.02323609) > 1e-8)
  fail(sprintf("anchor tau2: expected 0.02323609, got %.8f", unname(net$tau2)))
cat("anchor: PASS (0.59333495 / 0.64459765 / tau2 0.02323609)\n")

# --- HKSJ, reconstructed independently of the bundle -------------------------
w    <- 1 / (net$seTE^2 + net$tau2)
dfq  <- unname(net$df.Q)
q    <- if (dfq > 0) max(1, sum(w * (net$TE - net$TE.nma.random)^2) / dfq) else 1
mult <- if (dfq > 0) qt(0.975, dfq) * sqrt(q) else qnorm(0.975) * sqrt(q)

lt <- fromJSON(TABLE, simplifyVector = FALSE)

# --- the table must describe THIS network, not a subset of it ----------------
trts    <- net$trts
expect  <- length(trts) * (length(trts) - 1) / 2
claimed <- lt$counts$estimable
if (length(lt$contrasts) != claimed)
  fail(sprintf("table claims %d estimable contrasts but carries %d rows",
               claimed, length(lt$contrasts)))
if (claimed + lt$counts$non_estimable != expect)
  fail(sprintf("estimable(%d) + non-estimable(%d) != %d unordered pairs of %d nodes",
               claimed, lt$counts$non_estimable, expect, length(trts)))
seen <- character(0)
for (c_ in lt$contrasts)
  seen <- c(seen, paste(sort(c(c_$treat1, c_$treat2)), collapse = "|"))
if (anyDuplicated(seen)) fail("table contains duplicate contrasts")
cat(sprintf("coverage: PASS (%d nodes, %d unordered pairs, %d estimable rows, no duplicates)\n",
            length(trts), expect, claimed))

# --- every row, against netmeta's own matrices -------------------------------
worst <- 0; worst_row <- ""
for (c_ in lt$contrasts) {
  a <- c_$treat1; b <- c_$treat2
  if (!(a %in% trts) || !(b %in% trts)) fail("unknown node in table: ", a, " / ", b)
  te <- unname(net$TE.random[a, b]); se <- unname(net$seTE.random[a, b])
  ref <- c(exp(te), exp(te - mult * se), exp(te + mult * se))
  got <- c(c_$rr, c_$lo, c_$hi)
  dev <- max(abs(ref - got) / ref)
  if (dev > worst) { worst <- dev; worst_row <- paste(a, "vs", b) }
}
cat(sprintf("contrasts: %d checked against netmeta TE.random/seTE.random, max rel dev %.3e (%s)\n",
            length(lt$contrasts), worst, worst_row))
if (worst > TOL)
  fail(sprintf("contrast deviation %.3e exceeds tolerance %.1e at %s", worst, TOL, worst_row))

cat("VERDICT: PASS -- every published contrast reproduces netmeta independently.\n")
