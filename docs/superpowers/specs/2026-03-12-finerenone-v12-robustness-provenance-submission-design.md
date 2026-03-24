# Finerenone Review v12.0 — Robustness, Provenance & Submission Design

**Date**: 2026-03-12
**Target file**: `FINERENONE_REVIEW.html` (currently v11.0, ~10,600 lines)
**Constraints**: 3-source search (CT.gov, Europe PMC, OpenAlex) and record/abstract-only extraction are non-negotiable.

---

## Overview

Three-tier enhancement in priority order:

1. **Tier C — Analysis Robustness Suite**: Sensitivity panel, sequential monitoring, GRADE upgrades, influence diagnostics
2. **Tier D — Provenance & Automation**: Per-number verification, source transparency, endpoint auto-resolution, living pipeline hardening
3. **Tier A — Submission Artifacts**: PRISMA 2020 flow, publication-quality forest, GRADE evidence profile with absolute effects, reproducibility capsule

Implementation order: C → D → A (each tier builds on the previous).

---

## Tier C: Analysis Robustness Suite

### C1. Sensitivity Analysis Panel (Chart #17)

A dedicated "Robustness Dashboard" that runs 5 re-pooling scenarios automatically whenever the main analysis runs.

#### Scenarios

| # | Scenario | Logic | Display |
|---|----------|-------|---------|
| 1 | **FE vs RE** | Fixed-effect inverse-variance (no τ²) pooling. In both OR and HR modes, uses IV-FE on logOR/logHR. | Side-by-side estimate + CI; flag if direction or significance differs |
| 2 | **Exclude high-RoB** | Re-pool after dropping any trial with ≥1 "High" RoB domain. Trials without any RoB assessment are treated as "not high" (kept). | OR + CI + k; greyed if no high-RoB trials exist |
| 3 | **Peto OR** | Peto method for rare events. **OR mode only** — requires 2×2 tables. In HR mode, display "N/A — Peto requires event counts" | OR + CI; only shown when any arm has <5% events |
| 4 | **REML + HKSJ** | Already computed in v11 — surface as a named sensitivity row | Pull from existing REML chip values |
| 5 | **Randomization p** | **OR mode**: shuffle treatment/control labels within 2×2 tables. **HR mode**: randomly sign-flip each logHR (±1 with prob 0.5) — a randomization test under symmetry, not a classical label-permutation. Both: re-pool 1000×, seeded PRNG (mulberry32, seed = djb2 hash of concatenated study IDs). | p-rand alongside asymptotic p; flag if they diverge beyond 0.01 |

#### Display

Compact comparison table with traffic-light cells:
- Green: agrees with main result (same direction + significance)
- Amber: attenuated (same direction, significance changed)
- Red: reversed (direction flipped)

Below the table, auto-generated robustness verdict:
> "The pooled estimate is robust across all sensitivity analyses (5/5 concordant)."
> or "Caution: excluding high-RoB trials attenuates the effect to non-significance (3/5 concordant)."

#### Implementation

New object `SensitivityEngine`:
- `run(plotData, pLogOR, pSE, tau2, zCrit, confLevel, pOR, lci, uci)` → returns array of 5 scenario results
  - Note: `pOR` is the pooled exponentiated effect (exp(logOR) in OR mode, exp(logHR) in HR mode). The existing codebase aliases logHR as `logOR` throughout — all sensitivity scenarios use this aliasing transparently.
- Each result: `{ label, or, lci, uci, pValue, k, concordance: 'green'|'amber'|'red' }`
- Peto OR formula:
  - For each study i with 2×2 table (tE, tN, cE, cN):
    - Total events `a_i = tE + cE`, total N `n_i = tN + cN`
    - Expected events in treatment under null: `E_i = tN × a_i / n_i`
    - Hypergeometric variance: `V_i = tN × cN × a_i × (n_i - a_i) / (n_i² × (n_i - 1))`
    - Observed minus expected: `O_i - E_i = tE - E_i`
  - Pooled log-OR: `ln(OR_Peto) = Σ(O_i - E_i) / Σ(V_i)`
  - SE: `SE = 1 / sqrt(Σ(V_i))`
  - CI: `exp(ln(OR_Peto) ± z_alpha × SE)`
  - OR: `exp(ln(OR_Peto))`
  - p-value: `2 × (1 - Φ(|ln(OR_Peto)| / SE))`
- Peto OR trigger condition: Compute arm-level event rates for ALL included studies. Show the Peto OR row when **any** study has event rate < 5% in either arm (i.e., `tE/tN < 0.05` or `cE/cN < 0.05`). Otherwise, display "N/A — no rare-event studies" in greyed text.
- Permutation: shuffle treatment/control labels within each trial's 2×2 table, re-pool 1000×, compute p as fraction of permuted estimates more extreme than observed

New Plotly chart in `#plot-sensitivity` div.

### C2. Sequential / TSA Monitoring (Enhancement of Chart #4)

Enhances the **existing Z-curve plot** (Chart #4, `#plot-tsa`) with formal monitoring boundaries. Chart #3 (`#plot-cumulative`) remains unchanged as the effect-size cumulative plot. The existing TSA code at ~line 8182 already draws a basic OBF boundary — C2 replaces that with a more complete implementation and adds futility + RIS.

**Note**: The existing code comment at line 8182 says "Lan-DeMets O'Brien-Fleming" — this should be updated to "O'Brien-Fleming (discrete)" during implementation to match the actual formula used.

#### Overlays on Z-curve (Chart #4)

1. **O'Brien-Fleming (OBF) boundary** — discrete OBF approximation (not Lan-DeMets alpha-spending). Uses the simple closed-form: `z_boundary(j) = z_{alpha/2} / sqrt(IF_j)`. This is the classic OBF formula per Jennison & Turnbull (2000), not the continuous alpha-spending approximation.
2. **RIS horizontal marker** — showing total required information accrued
3. **Futility region** — simplified futility marker (not a full conditional-power boundary). This is a conservative indicator, not a formal beta-spending futility boundary.
4. **Stopping classification chip** — below the plot

#### Formulas

- Info fraction at step j: `IF_j = Σ(1/vi, i=1..j) / RIS`
- OBF boundary at step j: `z_boundary = z_{alpha/2} / sqrt(IF_j)` (discrete OBF, NOT Lan-DeMets spending function)
- Futility region: `z_futility = theta_alt × sqrt(IF_j × RIS) - z_{alpha/2} × sqrt((1 - IF_j) / IF_j)` where theta_alt = observed pooled effect. This approximates conditional power under the alternative. When cumulative Z falls below this line at IF > 50%, futility is indicated. Labeled as "approximate futility region" in the UI to distinguish from formal beta-spending boundaries.
- RIS from PowerEngine (already computed)

#### Stopping classification

| State | Condition | Label |
|-------|-----------|-------|
| SUFFICIENT | Cumulative Z crossed OBF boundary | "Evidence sufficient — monitoring boundary crossed at k=N" |
| FUTILE | Cumulative Z inside futility boundary at IF > 50% | "Futility — unlikely to reach significance with continued accrual" |
| ACCRUING | Neither boundary crossed | "Accruing — N% of required information reached" |

#### Implementation

Extend `renderPlots()` cumulative section. Add boundary traces to the Plotly chart. Add chip element below plot.

### C3. GRADE Upgrades

Currently GRADE only downgrades from HIGH. Add 3 upgrade paths per GRADE handbook (Schunemann 2013).

#### Upgrade criteria

| Criterion | Detection | Effect |
|-----------|-----------|--------|
| **Large effect** | OR < 0.50 or OR > 2.0 with p < 0.001 | +1 level |
| **Very large effect** | OR < 0.20 or OR > 5.0 | +2 levels (replaces +1) |
| **Dose-response gradient** | Meta-regression slope on dose/duration significant at p < 0.05 | +1 level |

#### Constraints

- Upgrades only apply when starting certainty ≤ LOW (per GRADE guidance, RCT baseline = HIGH, so upgrades won't fire for RCTs)
- The logic must be present for methodological completeness and reuse on observational data reviews
- Display: extra line in GRADE panel: "No upgrade criteria applicable (RCT baseline)." or "Upgraded +1 for large effect magnitude."
- **Starting level**: Currently hardcoded at HIGH (RCTs). A new `startingLevel` config field (values: `'HIGH'`, `'LOW'`) will be added to `CONFIG_LIBRARY` entries. The finerenone config sets `startingLevel: 'HIGH'`. Future configs for observational data can set `'LOW'` to activate upgrades. Until a config sets `'LOW'`, upgrade logic is evaluated but produces no effect — this is intentional (methodological completeness).

#### Implementation

Extend `renderGRADE()`. Add `upgradeLevel` computation after `totalDown`. Read `startingLevel` from config (default `'HIGH'`). Apply upgrades conditionally: `if (startingLevel !== 'HIGH') { ... }`.

### C4. Influence Diagnostics (Chart #18)

New chart: "Influence & Outlier Diagnostics" — 2×2 Plotly subplot grid.

#### Sub-panels

| Panel | Metric | X-axis | Threshold |
|-------|--------|--------|-----------|
| **Cook's distance** | Overall influence | Cook's D | 4/k |
| **Hat values** | Leverage | h_i = w_i / Σw | 2(p+1)/k where p=1 |
| **Ext. studentized residuals** | Outlier detection | rstudent_i | ±t(α/(2k), k-2) Bonferroni |
| **DFBETAS** | Estimate shift per study | DFBETAS_i | ±1 |

#### Formulas

All leverage the existing LOO infrastructure (already re-pools with each study removed):

```
hat_i = w_i / Σw                                                    [leverage]
r_i = (y_i - θ_pooled) / sqrt(v_i + τ²)                           [standardized residual]
rstudent_i = (θ_pooled - θ_(-i)) / SE(θ_pooled - θ_(-i))          [externally studentized]
    where SE(θ_pooled - θ_(-i)) = sqrt(SE_pooled² + SE_(-i)² - 2×cov)
    In practice for RE meta-analysis (Viechtbauer & Cheung 2010):
    rstudent_i = (y_i - θ_(-i)) / sqrt(v_i + τ²_(-i))
Cook_i = (θ_pooled - θ_(-i))² / (SE_pooled² × p)                  [p=1 parameter]
    Note: the regression simplification Cook_i = rstudent_i² × hat_i / (1 - hat_i) is
    approximate in RE meta-analysis (hat matrix is not idempotent). Use the direct LOO
    formula above for implementation.
DFBETAS_i = (θ_pooled - θ_(-i)) / SE_pooled                       [estimate shift in SE units]
```

Note: `rstudent_i` and `DFBETAS_i` differ in their denominators: rstudent uses the leave-one-out SE of the residual, while DFBETAS uses the SE of the full pooled estimate. They are NOT redundant.

Where `θ_(-i)` and `SE_(-i)` come from leave-one-out estimates already computed.

#### Summary text

Auto-generated: "No studies exceed Cook's D threshold. FIDELIO-DKD has the highest leverage (hat=0.42) but residual is within bounds."

If any study crosses ≥2 thresholds, flag as influential outlier with amber highlight.

#### Implementation

New object `InfluenceEngine`:
- `run(plotData, pLogOR, pSE, tau2, looResults)` → returns per-study diagnostics
- New Plotly subplot in `#plot-influence` div

#### Empty-state handling

`renderEmptyAnalysis()` must be updated to include both new plot divs (`#plot-sensitivity`, `#plot-influence`). Each gets cleared/hidden when there are no included trials, consistent with existing empty-state handling for plots #1-#16. The implementation adds these IDs to the existing array of plot containers that `renderEmptyAnalysis()` iterates over.

---

## Tier D: Provenance & Automation

### D1. Per-Number Provenance Layer

Every extracted numeric value becomes a traceable claim with source evidence.

#### Data model

Each trial's `data` object gains a `_provenance` map (underscore-prefixed to distinguish from analysis fields):

```javascript
// Trial object structure (existing):
// trial.data = { tE: 520, tN: 2152, cE: 600, cN: 2152, pubHR: null, ... }
// trial.evidence = [{ text: "...", source: "CT.gov", ... }]

// NEW: added alongside existing fields (does NOT replace or restructure them):
trial.data._provenance = {
  tE: {
    snippet: "...finerenone group: 520 of 2152 patients (24.2%)...",
    source: "CT.gov NCT02540993 resultsModule",
    sourceUrl: "https://clinicaltrials.gov/study/NCT02540993",
    charOffset: [34, 37],     // position of "520" within snippet
    confidence: 98,
    verifiedBy: null,          // reviewer ID when verified
    verifiedTs: null           // ISO timestamp
  },
  tN: { ... },
  cE: { ... },
  cN: { ... },
  pubHR:  { ... },            // if HR mode
  hrLCI:  { ... },
  hrUCI:  { ... }
};
// The actual values remain at trial.data.tE, trial.data.tN, etc. (unchanged)
// _provenance is metadata ABOUT the values, never used in computation
```

**Compatibility**: The `_provenance` map is purely additive. All existing code that reads `trial.data.tE` etc. continues to work unchanged. The underscore prefix signals "metadata" and avoids collision with any current or future data field names. Code that serializes trial data (JSON export, localStorage) will automatically include `_provenance` without modification. **Important**: Any code that iterates over `Object.keys(trial.data)` (e.g., CSV export) must skip underscore-prefixed keys to avoid `[object Object]` cells.

#### Provenance population

- **Landmark trials** (`realData`): Pre-populated from existing evidence panel text at confidence 100
- **Auto-extracted trials**: Extraction pipeline parses evidence panels to find the specific snippet containing each number. Uses regex matching against `ev.text` and `ev.fullText`. If a number appears in multiple panels, picks highest confidence. If no matching snippet, grey status.

#### UI — extraction card cells

Each 2×2 cell gets:
- **Coloured dot** inline: green (human-verified), amber (auto-extracted with source), grey (no source trace)
- **Click handler** → opens a **popover** (lightweight, not modal) showing:
  - Source snippet with the exact number highlighted in yellow
  - Source label (e.g., "CT.gov NCT02540993 — Results Module")
  - "Open Record" button → opens source page in new tab
  - "Verify" button → stamps reviewer ID + timestamp, turns dot green
  - "Flag" button → marks red, adds to reconciliation queue

#### Verification progress bar

Compact bar at top of each extract card:

```
Provenance: ████████░░ 6/8 verified  [2 pending]
```

When all values verified, card header gets a green seal icon.

#### Implementation

- Extend `ExtractEngine` with `_buildProvenance(trial, evidencePanels)` method
- New `ProvenancePopover` component (positioned absolutely, dismissed on outside click)
- Verification state persisted in `trial.data._provenance[field].verifiedBy/verifiedTs`
- CSS classes: `.prov-verified` (green), `.prov-sourced` (amber), `.prov-unsourced` (grey), `.prov-flagged` (red)

### D2. Source Verification Shortcuts

#### Screening cards

- **"View Record" link** on every screening card → opens CT.gov/PubMed using `_allSourceLinks`
- **Source badge row**: `[CT.gov] [PubMed] [OpenAlex]` showing which sources found this trial
- **"Show Full Abstract" toggle** — reveals complete PubMed abstract inline (already stored in `trial.abstract`)

#### Implementation

Extend `ScreenEngine.render()` card template. Add badge rendering from `trial.source` metadata.

### D3. Endpoint Auto-Resolution Improvements

Reduce reviewer burden by improving automatic endpoint matching.

#### Hierarchical matching (3 tiers)

| Tier | Logic | Auto-resolve? |
|------|-------|---------------|
| **Exact** | CT.gov `primaryOutcome.measure` contains target keyword AND type = PRIMARY | Yes, confidence 95+ |
| **Semantic bridge** | Outcome maps through equivalence table (e.g., "CV death, MI, stroke" → MACE) | Yes if confidence > 85, else flag |
| **Ambiguous** | Multiple candidates within 12 points, or no candidate above 65 | No — require reviewer adjudication |

#### Equivalence bridge table

Hardcoded lookup of ~20 common endpoint phrasings mapped to the 8 outcome keys:

```javascript
const ENDPOINT_BRIDGES = {
  MACE: [
    'cardiovascular death, nonfatal myocardial infarction, nonfatal stroke',
    'composite of cv death, mi, stroke',
    'first mace event',
    'major adverse cardiovascular event'
  ],
  Renal40: [
    'sustained decrease in egfr of >= 40%',
    'kidney failure, sustained egfr decline',
    'composite renal endpoint'
  ],
  ACM: ['all-cause mortality', 'death from any cause', 'overall survival'],
  ACH: ['hospitalization for heart failure', 'hf hospitalization', 'heart failure event'],
  // ... etc for all 8 outcome keys
};
```

#### Resolution audit trail

When endpoint is auto-resolved, evidence panel explicitly states:
> "Endpoint auto-matched: 'Composite of CV death, nonfatal MI, nonfatal stroke, HF hospitalization' → MACE (Tier 1: exact keyword, confidence 97%)."

Reviewer can override via existing adjudication flow.

### D4. Living Pipeline Hardening

#### Auto-stale detection

On app load, derive last search date from `searchLog[searchLog.length - 1].timestamp` (existing state). If >30 days, show amber banner:
> "Last acquisition: 47 days ago. New trials may have been published. [Re-run now]"

#### Delta-on-re-acquisition

When acquisition runs again, compare new trial list against stored list:

| Delta type | Display |
|------------|---------|
| **New trials** | "NEW" badge in screening, auto-scored but not auto-included |
| **Disappeared trials** | Warning badge (e.g., status changed to WITHDRAWN) |
| **Metadata changed** | "UPDATED" badge with diff of what changed (title, status, results posting date) |

#### Acquisition log enrichment

Extend search log to record:
- Per-source hit list (which NCT IDs from which source)
- Dedup trace (which records merged and why)
- New-vs-known breakdown

Answers: "When was this trial first discovered? By which source? Has its record changed since?"

#### Implementation

- `SearchEngine.compareWithStored(newTrials, storedTrials)` → returns `{ added, removed, changed }`
- Delta badges rendered in screening card template
- Banner component in header area, dismissible

---

## Tier A: Submission Artifacts

### A1. PRISMA 2020 Flow Diagram (Full 4-panel SVG)

Standard PRISMA 2020 layout rendered as SVG:

| Panel | Content | Source |
|-------|---------|--------|
| **Identification** | Records from databases (CT.gov: n, PubMed: n, OpenAlex: n) + landmark DB | `searchLog` counts |
| **Screening** | After dedup → screened → excluded with per-reason counts | `trials` statuses |
| **Eligibility** | Assessed → excluded (Phase II, no events, wrong comparator) | Phase-2 + zero-event filters |
| **Included** | k studies in quantitative synthesis, with per-outcome breakdown | `getScopedIncludedTrials()` |

SVG rendering with boxes, arrows, counts. Exportable as PNG (300 DPI, via shared `<canvas>` rasterization helper used by both PRISMA and Forest export) / SVG.

#### PRISMA checklist CSV enhancement

Every cell populated with actual content or specific section reference (not "See app tab X"). Map all 27 items to concrete text from protocol, analysis, and report.

### A2. Publication-Quality Forest Plot Export

Static SVG rendering separate from interactive Plotly plot.

#### Specifications

- **Width**: 180mm (standard journal column)
- **Height**: scales with k
- **Font**: serif (Times/Georgia), 8-9pt
- **Colour**: black/grey (print-safe), optional colour toggle
- **Left side**: study labels (acronym, year)
- **Center**: forest plot with squares (sized by weight), whiskers (CI), diamond (pooled)
- **Right columns**: Events/Total (Tx), Events/Total (Ctrl), OR [95% CI], Weight %
- **Below**: I², τ², Q p-value, HKSJ CI (dashed diamond outline), PI (thin extended line)
- **Export**: "Download SVG" + "Download PNG (300 DPI)" buttons

#### Implementation

New `ForestExportEngine` object. Builds SVG DOM elements directly. Uses `<canvas>` for PNG rasterization at 300 DPI.

### A3. GRADE Evidence Profile Table

Formal GRADE evidence profile (Summary of Findings) per Cochrane/GRADEpro format.

#### Columns

| Column | Content |
|--------|---------|
| Outcome | Endpoint name + follow-up duration |
| No. of studies (k) | From analysis |
| Certainty | HIGH/MOD/LOW/VLOW with GRADE symbols |
| Relative effect (95% CI) | OR/RR/HR [CI] |
| Anticipated absolute effects per 1,000 | Control risk → intervention risk, with CI |
| Plain language summary | "Finerenone probably reduces..." |

#### Absolute effect computation

- CER = weighted average of control arm event rates (weighted by study sample size)
- IER_OR = `CER × OR / (1 - CER + CER × OR)` (applying OR to baseline risk)
- IER_RR = `CER × RR`
- ARD = `IER - CER`, expressed per 1,000 patients
- CI on absolute effect — **use direct transformation** (preserves asymmetry, preferred over delta method):
  - For OR:
    - `IER(OR) = CER × OR / (1 - CER + CER × OR)`
    - `ARD_point = (IER(OR_point) - CER) × 1000`
    - `ARD_LCI = (IER(OR_LCI) - CER) × 1000`
    - `ARD_UCI = (IER(OR_UCI) - CER) × 1000`
  - For RR:
    - `IER(RR) = CER × RR`
    - `ARD = (CER × RR - CER) × 1000`, CI bounds via `IER(RR_LCI)`, `IER(RR_UCI)`
  - For HR (from published HRs, assuming proportional hazards):
    - `IER(HR) = 1 - (1 - CER)^HR` (exponential survival approximation)
    - `ARD = (IER(HR_point) - CER) × 1000`
    - CI: `ARD_LCI = (1 - (1-CER)^HR_UCI - CER) × 1000`, `ARD_UCI = (1 - (1-CER)^HR_LCI - CER) × 1000` (bounds swap because HR < 1 maps to lower absolute risk)
    - Note: this differs from `CER × HR` (which conflates risk ratios with hazard ratios). The `(1-CER)^HR` formula is correct for converting hazard ratios to absolute risk changes.
  - Note: delta method derivative `dIER/d(logOR) = CER × (1-CER) × exp(logOR) / (1-CER+CER×exp(logOR))²` is available for computing a symmetric SE if needed for other purposes, but the CI in the evidence profile table uses the direct transformation above.

#### Multi-outcome generation

Loops through all 8 outcomes in the selector, runs pooling for each, generates one row per outcome.

#### Export formats

- CSV (for supplementary tables)
- HTML fragment (copy-paste into manuscripts)
- Formatted display in Report tab

### A4. Reproducibility Capsule (ZIP)

Downloadable ZIP containing all artifacts for independent replication.

#### Contents

| File | Content |
|------|---------|
| `data.csv` | All included trials: ID, name, tE, tN, cE, cN, pubHR, group, phase, year, RoB D1-D5 |
| `validate_R.R` | Auto-generated R script (metafor) — already exists |
| `validate_python.py` | Auto-generated Python script (numpy only, no meta-analysis library dependency) — implements DL tau², IV-weighted pooling, HKSJ CI, and PI from scratch (~80 lines). Replicates the same analyses as the R script but serves users without R installed. |
| `provenance.json` | Per-number provenance map with source snippets and verification status |
| `prisma_checklist.csv` | Completed PRISMA 2020 checklist |
| `grade_profile.csv` | GRADE evidence profile for all outcomes |
| `audit_log.json` | Full audit trail (all entries, not just recent 12) |
| `config.json` | App version, confidence level, effect measure, outcome scope, search queries |
| `seal.json` | SHA-256 data seal + timestamp + reviewer IDs + hash of data.csv. Seal computation must include pubHR/hrLCI/hrUCI and RoB assessments (existing `DataSealEngine.computeSeal()` at line ~7577 only hashes name/tE/tN/cE/cN — must be extended). |
| `README.txt` | Instructions for running R/Python validation |

#### ZIP generation

**Inline minimal ZIP builder** (~150-200 lines, no external library). The ZIP format for uncompressed (STORE method) files is straightforward:
- Local file headers (30 bytes + filename) + raw file content per entry
- Central directory (46 bytes + filename per entry)
- End-of-central-directory record (22 bytes)

This avoids any CDN dependency and works within the existing CSP (no `script-src` changes needed). All files in the capsule are text (CSV, JSON, R, Python, TXT), so STORE (no compression) is acceptable — typical capsule size is 50-200 KB uncompressed.

The builder follows the pattern already used in the app's other export functions (SVG export, CSV export): construct content in memory, create a Blob, generate a download link via `URL.createObjectURL()`, trigger click, then `URL.revokeObjectURL()`.

No external library (JSZip etc.) is loaded. No CSP changes required.

#### Seal verification

`seal.json` includes SHA-256 hash of `data.csv` contents. Anyone can verify CSV wasn't modified post-export by re-hashing and comparing.

### A5. Audit Log Upgrade

- **Uncapped storage** — store all entries (typical: 50-200, trivial for localStorage)
- **Categorised view** — filter by: screening, extraction, RoB, analysis, reviewer actions
- **Export** — included in reproducibility capsule as `audit_log.json`
- **Seal coverage expanded** — hash includes RoB assessments, not just 2×2 counts

---

## Chart Slot Summary

| Slot | Name | Status |
|------|------|--------|
| #1 | Forest Plot | Existing |
| #2 | Subgroup | Existing |
| #3 | Cumulative (effect size) | Existing (unchanged) |
| #4 | TSA Z-curve + OBF/futility | Enhanced (C2) |
| #5 | Leave-One-Out | Existing |
| #6 | L'Abbe | Existing |
| #7 | Galbraith | Existing |
| #8 | NNT | Existing |
| #9 | Funnel (contour-enhanced) | Existing |
| #10 | Baujat | Existing |
| #11 | Bayesian Posterior | Existing |
| #12 | Meta-Regression | Existing |
| #13 | Copas Sensitivity | Existing |
| #14 | Power / Conditional | Existing |
| #15 | Egger Regression | Existing |
| #16 | RoB Summary | Existing |
| #17 | **Sensitivity Panel** | New (C1) |
| #18 | **Influence Diagnostics** | New (C4) |

---

## Non-Goals

- No full-text PDF extraction (constraint)
- No additional search sources beyond CT.gov, Europe PMC, OpenAlex (constraint)
- No network meta-analysis (single intervention)
- No Bayesian model averaging (current grid approximation is sufficient)
- No automated manuscript generation (out of scope)

---

## Success Criteria

1. All existing 0-failure regression tests continue to pass
2. Sensitivity panel produces concordant results with R metafor on the 3 landmark trials
3. Every landmark trial number has provenance with snippet; auto-extracted numbers target ≥90% provenance coverage (grey status for unmatched)
4. PRISMA flow diagram matches manual counts
5. Forest SVG export passes visual inspection against R metafor forest plot
6. Reproducibility ZIP's R script, when run, reproduces the app's pooled estimates within tolerance 0.005
7. GRADE evidence profile absolute effects match manual computation within 1 per 1,000
