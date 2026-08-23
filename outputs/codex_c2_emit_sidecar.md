# emit_sidecar provenance enumeration

Repo root: `F:\rapidmeta-ssot-shell`.

This is enumeration only. I changed no file except this report.

## Search coverage

Literal `emit_sidecar` scan found the sites listed here. I separately checked
`outputs/r_validation`, `figs`, `outputs/figs`, `ctgov_history_raw`, and
`.ctgov-raw-cache`; none contained `emit_sidecar`. `docs/verification-lane`
had no hit when `.pytest_cache` was excluded; that cache directory itself is
unreadable (`Access is denied`) and is not source.

I also searched for `emit.*sidecar`, `sidecar.*emit`, and indirect-call
constructs (`do.call`, `match.fun`, `get`, `eval`, `source`, `paste0`,
`assign`, `call`) near `sidecar`/`emit`. I found no dynamically constructed
`emit_sidecar` call beyond the literal calls and documentation snippets below.

## Definitions

Primary provenance-enforcing definition:

- `scripts/regenerate_catastrophic_sidecars.R:25-26`
  `emit_sidecar <- function(path, label, trials, ncts = NULL, pmids = NULL,
  provenance = NULL)`

Semantics:

- `trials` is a data frame with `name`, `hr`, `lci`, `uci`.
- It computes `yi = log(hr)`, `sei`, `vi`, fits
  `metafor::rma(..., method = "REML", test = "knha")`, computes a
  `t_{k-1}` prediction interval, and writes JSON manually to `path`.
- `provenance` is used only for JSON field `regenerated_from`
  (`scripts/regenerate_catastrophic_sidecars.R:84`).
- It accepts any non-`NULL` value for which `nzchar(provenance)` is true;
  practically, a non-empty scalar string. It is not source-validated.
- If absent or empty, `scripts/regenerate_catastrophic_sidecars.R:34-39`
  calls `stop(...)` before fitting or writing.

Other same-named definitions, without provenance:

- `scripts/build_continuous_sidecar.py:219`
  `def emit_sidecar(page_path: Path, force=False) -> dict:`
- `scripts/build_binary_sidecar.py:349`
  `def emit_sidecar(page_path: Path, force=False) -> dict:`

## Executable call sites

### `scripts/regenerate_catastrophic_sidecars.R:112`

Call emits `outputs/r_validation/COPD_TRIPLE.json` if unblocked.

Provenance passed: no. It therefore refuses with `provenance = NULL`.

Values passed:

- IMPACT: `0.75 [0.70, 0.81]`, `NCT02164513`, PMID `29668352`.
- ETHOS: `0.76 [0.69, 0.83]`, `NCT02465567`, PMID `32579807`.
- KRONOS: `0.52 [0.40, 0.69]`, `NCT02497001`, PMID `30232048`.

Immediate source: hardcoded R data frame at
`scripts/regenerate_catastrophic_sidecars.R:115-123`.

Trace found: these effect triples match embedded page fields:

- `COPD_TRIPLE_REVIEW.html` `RapidMeta.realData.NCT02164513.publishedHR/hrLCI/hrUCI`.
- `COPD_TRIPLE_REVIEW.html` `RapidMeta.realData.NCT02465567.publishedHR/hrLCI/hrUCI`.
- `COPD_TRIPLE_REVIEW.html` `RapidMeta.realData.NCT02497001.publishedHR/hrLCI/hrUCI`.

The page has adjacent source snippets for Lipson 2018, Rabe 2020, and
Ferguson 2018. Note: the R call PMIDs differ from the page `pmid` field for
IMPACT and ETHOS; KRONOS matches.

### `scripts/regenerate_catastrophic_sidecars.R:130`

Call emits `outputs/r_validation/FGFR_INHIBITORS_SOLID.json` if unblocked.

Provenance passed: no. It therefore refuses with `provenance = NULL`.

Values passed:

- FIGHT-202 pemigatinib: `0.50 [0.40, 0.63]`.
- BGJ398 infigratinib: `0.45 [0.34, 0.60]`.
- BLC2001 erdafitinib: `0.55 [0.42, 0.72]`.

Immediate source: hardcoded R data frame at
`scripts/regenerate_catastrophic_sidecars.R:133-141`.

Trace found: the local comment says these are placeholder HRs reflecting
single-arm response benchmarks against historical control
(`scripts/regenerate_catastrophic_sidecars.R:135-137`). No `ncts` or `pmids`
are supplied. Corresponding page trial objects have
`publishedHR/hrLCI/hrUCI = null`.

Exact source: NOT ESTABLISHED.

### `scripts/regenerate_catastrophic_sidecars.R:147`

Call emits `outputs/r_validation/HPV_DOSE_REDUCTION.json` if unblocked.

Provenance passed: no. It therefore refuses with `provenance = NULL`.

Values passed:

- KEN-SHE: `0.025 [0.003, 0.183]`, `NCT03832621`.
- DoRIS: `0.030 [0.005, 0.180]`, `NCT02834637`.

Immediate source: hardcoded R data frame at
`scripts/regenerate_catastrophic_sidecars.R:150-158`.

Trace found:

- The local comment says vaccine efficacy was converted as `RR = 1 - VE`
  (`scripts/regenerate_catastrophic_sidecars.R:144-152`).
- `ssot/placeholder_provenance.py:64-71` says the inputs are not invented,
  but applying that transform to interval bounds is unsound.
- `HPV_DOSE_REDUCTION_REVIEW.html` does not contain `NCT03832621`.
- KEN-SHE's numeric triple matches
  `HPV_DOSE_REDUCTION_REVIEW.html`
  `RapidMeta.realData.NCT03675256.publishedHR/hrLCI/hrUCI`.
- DoRIS in the page is
  `RapidMeta.realData.NCT02834637.publishedHR/hrLCI/hrUCI = 1/0.96/1.04`,
  not `0.030/0.005/0.180`.

Exact source: partial only; complete sidecar source NOT ESTABLISHED.

### `scripts/regenerate_catastrophic_sidecars.R:162`

Call emits `outputs/r_validation/HEPATITIS_HCV_DAA.json` if unblocked.

Provenance passed: no. It therefore refuses with `provenance = NULL`.

Values passed:

- ASTRAL-1: `0.10 [0.03, 0.30]`.
- ASTRAL-3: `0.08 [0.02, 0.27]`.
- EXPEDITION-1: `0.05 [0.01, 0.20]`.

Immediate source: hardcoded R data frame at
`scripts/regenerate_catastrophic_sidecars.R:165-174`.

Trace found: comments say these are treatment-failure ORs approximated from
about 1 percent DAA failure versus about 5 to 10 percent comparator failure
(`scripts/regenerate_catastrophic_sidecars.R:160-170`).
`ssot/placeholder_provenance.py:57-63` says they were not read per trial.
The review page fields do not match these values.

Exact source: NOT ESTABLISHED.

### `scripts/regenerate_catastrophic_sidecars.R:178`

Call emits `outputs/r_validation/MDRTB_BPAL.json` if unblocked.

Provenance passed: no. It therefore refuses with `provenance = NULL`.

Values passed:

- Nix-TB single-arm BPaL: `0.30 [0.18, 0.50]`, PMID `31531947`.
- ZeNix BPaL Lzd 600 mg/26 wk: `0.25 [0.15, 0.42]`, PMID `35139273`.
- TB-PRACTECAL BPaLM vs SOC: `0.22 [0.12, 0.39]`, PMID `35384356`.

Immediate source: hardcoded R data frame at
`scripts/regenerate_catastrophic_sidecars.R:181-190`.

Trace found:

- The local comment says TB-PRACTECAL is a published unfavorable-outcome RR
  and the others are single-arm (`scripts/regenerate_catastrophic_sidecars.R:177-185`).
- `ssot/placeholder_provenance.py:72-78` says one input is published and the
  other two are assumed values for single-arm studies.
- The page confirms Nix-TB is `estimandType="PROPORTION"` with no comparator.
- The page has `RapidMeta.realData.NCT02589782` for TB-PRACTECAL with group
  text saying RR `0.23 [0.15, 0.36]`, not `0.22 [0.12, 0.39]`.

Exact source: NOT ESTABLISHED for the full sidecar.

### `scripts/build_continuous_sidecar.py:263`

Call: `r = emit_sidecar(p)`.

Provenance passed: no; this Python function does not accept provenance.

Emitted value: for each `HERE.glob("*_REVIEW.html")`, a continuous sidecar
under `outputs/r_validation/continuous/<PAGE_STEM>.json`, unless it already
exists or `k < 2`.

Source path: each review HTML's embedded
`realData.<NCT>.publishedHR`, `.hrLCI`, `.hrUCI`, `.estimandType`, `.name`,
and `.pmid`. The pooled value is computed in this script.

### `scripts/build_binary_sidecar.py:406`

Call: `r = emit_sidecar(p)`.

Provenance passed: no; this Python function does not accept provenance.

Emitted value: for each `HERE.glob("*_FULL_REVIEW.html")`, a binary sidecar
under `outputs/r_validation/<STEM>.json`, unless it already exists or `k < 2`.

Source path: each full review HTML's embedded
`realData.<NCT>.tE`, `.tN`, `.cE`, `.cN`, `.name`, and `.pmid`. The pooled
log OR is computed in this script.

### Test calls in `scripts/tests/test_idempotency_v2.py`

Continuous builder calls:

- `scripts/tests/test_idempotency_v2.py:230`: `r1 = mod.emit_sidecar(page)`.
- `scripts/tests/test_idempotency_v2.py:231`: `r2 = mod.emit_sidecar(page)`.
- `scripts/tests/test_idempotency_v2.py:236`: `mod.emit_sidecar(page, force=True)`.

Provenance passed: no. Values come from hardcoded fixture HTML at
`scripts/tests/test_idempotency_v2.py:216-223`:

- `realData.NCT00000001.publishedHR/hrLCI/hrUCI/estimandType = 0.85/0.72/0.99/HR`.
- `realData.NCT00000002.publishedHR/hrLCI/hrUCI/estimandType = 0.78/0.65/0.93/HR`.

Binary builder calls:

- `scripts/tests/test_idempotency_v2.py:264`: `r1 = mod.emit_sidecar(page)`.
- `scripts/tests/test_idempotency_v2.py:265`: `r2 = mod.emit_sidecar(page)`.
- `scripts/tests/test_idempotency_v2.py:269`: `r3 = mod.emit_sidecar(page, force=True)`.
- `scripts/tests/test_idempotency_v2.py:271`: `r4 = mod.emit_sidecar(page, force=True)`.

Provenance passed: no. Values come from hardcoded fixture HTML at
`scripts/tests/test_idempotency_v2.py:249-256`:

- `realData.NCT00000001.tE/tN/cE/cN = 10/100/20/100`.
- `realData.NCT00000002.tE/tN/cE/cN = 5/50/8/50`.

## String and documentation mentions

These are not executable calls and emit no value:

- `scripts/regenerate_catastrophic_sidecars.R:36`: error-message string
  contains `emit_sidecar(%s)`.
- `scripts/tests/test_idempotency_v2.py:243`: test docstring contains
  `emit_sidecar()`.
- `scripts/instrument_controls.py:341`: docstring mentions `emit_sidecar()`.
- `scripts/instrument_controls.py:355`: docstring pseudo-call
  `emit_sidecar(..., provenance = NULL) -> stop() if provenance is missing`.
- `HANDOVER-2026-08-23.md:137`: mention of `emit_sidecar` requiring provenance.
- `HANDOVER-2026-08-23-WRITER-2.md:42`: mention of the five refusals.

I found no commented-out executable `emit_sidecar(...)` call.

## Blocked/refusing verdicts

Only the five R calls in `scripts/regenerate_catastrophic_sidecars.R` are
blocked by missing provenance.

| File:line | Sidecar | Verdict | Source |
|---|---|---|---|
| `scripts/regenerate_catastrophic_sidecars.R:112` | `COPD_TRIPLE` | PROVENANCE EXISTS AND CAN BE NAMED | `COPD_TRIPLE_REVIEW.html` `RapidMeta.realData.NCT02164513/NCT02465567/NCT02497001.publishedHR/hrLCI/hrUCI` |
| `scripts/regenerate_catastrophic_sidecars.R:130` | `FGFR_INHIBITORS_SOLID` | PROVENANCE DOES NOT EXIST | NOT ESTABLISHED; code says placeholders, page fields are null |
| `scripts/regenerate_catastrophic_sidecars.R:147` | `HPV_DOSE_REDUCTION` | COULD NOT DETERMINE | Partial only; KEN-SHE maps to `NCT03675256`, not the call's `NCT03832621`; DoRIS does not match page values |
| `scripts/regenerate_catastrophic_sidecars.R:162` | `HEPATITIS_HCV_DAA` | PROVENANCE DOES NOT EXIST | NOT ESTABLISHED; code says approximated from ranges, not read per trial |
| `scripts/regenerate_catastrophic_sidecars.R:178` | `MDRTB_BPAL` | PROVENANCE DOES NOT EXIST | NOT ESTABLISHED for full sidecar; two values are assumed and the comparative page value differs |

## Old on-disk outputs with the false default

These current files show what the old default emitted. They do not establish
that any blocked call should proceed.

- `outputs/r_validation/COPD_TRIPLE.json`: `pooled_OR=0.692750`,
  `ci_low_OR=0.429539`, `ci_high_OR=1.117251`,
  `regenerated_from="curated_publishedHR_via_metafor_5.0.1"`.
- `outputs/r_validation/FGFR_INHIBITORS_SOLID.json`: `pooled_OR=0.500065`,
  `ci_low_OR=0.396901`, `ci_high_OR=0.630043`,
  `regenerated_from="curated_publishedHR_via_metafor_5.0.1"`.
- `outputs/r_validation/HPV_DOSE_REDUCTION.json`: `pooled_OR=0.027729`,
  `ci_low_OR=0.008802`, `ci_high_OR=0.087352`,
  `regenerated_from="curated_publishedHR_via_metafor_5.0.1"`.
- `outputs/r_validation/HEPATITIS_HCV_DAA.json`: `pooled_OR=0.078183`,
  `ci_low_OR=0.033900`, `ci_high_OR=0.180310`,
  `regenerated_from="curated_publishedHR_via_metafor_5.0.1"`.
- `outputs/r_validation/MDRTB_BPAL.json`: `pooled_OR=0.258009`,
  `ci_low_OR=0.176350`, `ci_high_OR=0.377481`,
  `regenerated_from="curated_publishedHR_via_metafor_5.0.1"`.
