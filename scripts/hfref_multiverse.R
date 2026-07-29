###############################################################################
# HFrEF MULTIVERSE -- THE FOUR CELLS THIS REPOSITORY COMPUTES
# =============================================================================
# Emits the four cells whose estimates the app is allowed to display:
#   OURS-STRICT     7a  PRIMARY      (pre-specified)
#   OURS-INCLUSIVE  8   SENSITIVITY
#   OURS-STRICT-7b  7b  BRANCH       (X-10 executed)
#   OURS-STRICT-7c  7c  BRANCH       (X-10 executed, CARMEN dropped)
#
# The other six specifications in the eight-cell design are PUBLISHED reviews
# that this repository has NOT independently reproduced. PATH-2 (2026-07-28)
# downgraded them to illustrative. They are emitted here as coordinates and a
# withdrawal reason ONLY -- no estimate, no interval, no rank -- so the app can
# show what was specified without implying it was computed.
#
# Cells are fitted by calling the SETTLED fit_cell() itself, not a copy of it.
# Writes outputs/hfref_multiverse.json (this repository only).
###############################################################################

suppressMessages({
  library(netmeta)
  library(jsonlite)
})

SETTLED    <- "F:/E156/hfref_eightcell_fit.R"
PREFIX_END <- 587L
OUT        <- "outputs/hfref_multiverse.json"
COMPUTED   <- c("OURS-STRICT", "OURS-INCLUSIVE", "OURS-STRICT-7b", "OURS-STRICT-7c")

src <- readLines(SETTLED, warn = FALSE)
if (!grepl("^\\}$", src[PREFIX_END]))
  stop("PREFIX_END no longer closes fit_cell(); refusing to eval a partial prefix")
invisible(capture.output(
  eval(parse(text = paste(src[1:PREFIX_END], collapse = "\n")), envir = globalenv())))

# ---- the six withdrawn specifications ---------------------------------------
# Author coordinates are carried from the settled CELLS list; the reason is the
# PATH-2 downgrade. No estimate is attached, because none was reproduced.
WITHDRAWN_IDS <- c("T24-tang-2024", "B17-burnett-2017", "K18-komajda-2018",
                   "T21-tromp-2021", "DM22-demarzo-2022", "vE25-vanessen-2025")
WITHDRAWN_REASON <- paste0(
  "PUBLISHED SPECIFICATION -- NOT INDEPENDENTLY REPRODUCED. Downgraded to ",
  "illustrative by the PATH-2 pass (2026-07-28), which required every number ",
  "on the page to be our own re-fit, a figure quoted as its source reports it, ",
  "or an explicit 'not computed'. No estimate is displayed for this cell.")
WITHDRAWN_EXTRA <- list(
  "K18-komajda-2018"  = "Coordinate-identical to cell 5 (De Marzo 2022).",
  "DM22-demarzo-2022" = "Coordinate-identical to cell 3 (Komajda 2018).",
  "T21-tromp-2021"    = "Coordinate-identical to cell 6 (van Essen 2025).",
  "vE25-vanessen-2025" = paste0(
    "Coordinate-identical to cell 4 (Tromp 2021/22): the six unknown ",
    "coordinates were filled from Tromp, so this is the Tromp specification ",
    "under another name. Its fit is additionally UNRATIFIABLE from held data ",
    "(OWED-O) -- no family can witness it, because van Essen's own 89-trial ",
    "arm-level set is not held in this repository.")
)

REPORT <- c("ACEI", "ARB", "BB", "ACEI+BB", "ACEI+MRA", "ACEI+ARB",
            "ACEI+BB+ARB", "ACEI+BB+MRA", "ARNI+BB", "+SGLT2i",
            "+Omecamtiv", "+Vericiguat", "+Digitoxin", "+QLQX")

cells_out <- list()
anchor_seen <- FALSE

for (cid in COMPUTED) {
  cl <- Filter(function(x) x$cell_id == cid, CELLS)
  if (length(cl) != 1L) stop("cell not found in settled CELLS: ", cid)
  cl <- cl[[1]]
  r  <- fit_cell(cl)
  if (!isTRUE(r$computed))
    stop("cell ", cid, " did not compute: ", r$not_computed_reason)

  nodes <- Filter(function(n) isTRUE(n$present) && n$node %in% REPORT, r$nodes)
  nodes <- lapply(nodes, function(n)
    list(node = n$node, rr = n$rr, lo = n$lo, hi = n$hi))

  cat(sprintf("%-16s trials=%2d contrasts=%2d nodes=%2d tau2=%.8f I2=%.1f%%\n",
              cid, r$trials$n, r$contrasts, length(nodes), r$tau2, 100 * r$i2))

  if (cid == "OURS-STRICT") {
    g <- function(nm) Filter(function(n) n$node == nm, nodes)[[1]]
    a <- g("ACEI+BB+MRA"); b <- g("ACEI+BB")
    ok <- abs(a$rr - 0.59333495) < 1e-8 && abs(a$lo - 0.348) < 5e-4 &&
          abs(a$hi - 1.011) < 5e-4 &&
          abs(b$rr - 0.64459765) < 1e-8 && abs(b$lo - 0.433) < 5e-4 &&
          abs(b$hi - 0.959) < 5e-4 && abs(r$tau2 - 0.02323609) < 1e-8
    cat(sprintf("  ANCHOR ACEI+BB+MRA %.8f (%.3f-%.3f)  ACEI+BB %.8f (%.3f-%.3f)  tau2 %.8f  %s\n",
                a$rr, a$lo, a$hi, b$rr, b$lo, b$hi, r$tau2,
                if (ok) "PASS" else "FAIL"))
    if (!ok) stop("ANCHOR FAILED in the primary cell -- no multiverse written.")
    anchor_seen <- TRUE
  }

  cells_out[[length(cells_out) + 1]] <- list(
    cell_id = cl$cell_id, label = cl$label, tier = cl$tier,
    repro_label = cl$repro_label, scale = cl$scale, note = cl$note,
    computed = TRUE, coords = cl$coords,
    trials = r$trials$n, contrasts = r$contrasts,
    trial_names = r$trials$names,
    tau2 = r$tau2, i2 = r$i2,
    structure = list(nodes = r$structure$V, edges = r$structure$E,
                     designs = r$structure$designs, icdf = r$structure$icdf),
    nodes = unname(nodes))
}
if (!anchor_seen) stop("primary cell was never fitted -- refusing to emit")

for (wid in WITHDRAWN_IDS) {
  cl <- Filter(function(x) x$cell_id == wid, CELLS)
  if (length(cl) != 1L) stop("withdrawn cell not found in settled CELLS: ", wid)
  cl <- cl[[1]]
  cells_out[[length(cells_out) + 1]] <- list(
    cell_id = cl$cell_id, label = cl$label, tier = cl$tier,
    repro_label = cl$repro_label, scale = cl$scale,
    computed = FALSE,
    withdrawn = TRUE,
    withdrawn_reason = WITHDRAWN_REASON,
    withdrawn_extra = if (!is.null(WITHDRAWN_EXTRA[[wid]])) WITHDRAWN_EXTRA[[wid]] else NULL,
    review = cl$review,
    coords = cl$coords,
    nodes = list())
  cat(sprintf("%-20s WITHDRAWN (coordinates only, no estimate)\n", wid))
}

dir.create(dirname(OUT), showWarnings = FALSE, recursive = TRUE)
write(toJSON(list(
  schema = "hfref-multiverse/v1",
  generated_by = "scripts/hfref_multiverse.R",
  settled_source = SETTLED,
  engine = paste0("R ", getRversion(), " / netmeta ", packageVersion("netmeta")),
  outcome = "all-cause mortality",
  design = list(
    total_specifications = length(cells_out),
    computed = length(COMPUTED),
    withdrawn = length(WITHDRAWN_IDS),
    withdrawal_basis = WITHDRAWN_REASON),
  cells = unname(cells_out)),
  auto_unbox = TRUE, digits = 10, null = "null", na = "null"), file = OUT)
cat("WROTE ", OUT, "  (", length(COMPUTED), " computed + ",
    length(WITHDRAWN_IDS), " withdrawn)\n", sep = "")
