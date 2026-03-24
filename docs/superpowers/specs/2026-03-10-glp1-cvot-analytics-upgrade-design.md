# GLP-1 RA CVOT Review — Analytical Depth Upgrade

**Date**: 2026-03-10
**File**: `C:\Users\user\Downloads\Finrenone\GLP1_CVOT_REVIEW.html`
**Goal**: Make this the most analytically comprehensive GLP-1 RA CVOT evidence synthesis platform, beating all published meta-analyses (including Galli JACC 2025, 99K patients) on analytical depth using 10 canonical CVOTs.

## Competitive Landscape

| Competitor | Trials | N | NMA | Dose-Resp | Fragility | TSA | Bayesian | TruthCert | Safety MA |
|-----------|--------|---|-----|-----------|-----------|-----|----------|-----------|----------|
| Kristensen 2019 | 7 | 56K | No | No | No | No | No | No | No |
| Sattar 2021 | 8 | 60K | No | No | No | No | No | No | No |
| Badve 2024 | 11 | 85K | No | No | No | No | No | No | No |
| Galli JACC 2025 | 21 | 99K | No | No | No | Yes* | No | No | Partial |
| **Ours** | **10** | **~85K** | **Yes** | **Yes** | **Yes** | **Yes** | **Yes** | **Yes** | **Yes** |

*Galli TSA is pre-SOUL.

## Scope

- **Trials**: 10 canonical CVOTs (ELIXA, LEADER, SUSTAIN-6, EXSCEL, HARMONY, REWIND, PIONEER 6, SELECT, AMPLITUDE-O, SOUL)
- **Data sources**: ClinicalTrials.gov structured results, PubMed abstracts, OpenAlex — open-access only
- **Audience**: Tiered — clinicians (standard view) + methodologists (expert panels)
- **Approach**: Deep analytics on canonical trials, not trial count inflation

## 13 New/Enhanced Features

### 1. Multi-Outcome NMA (NEW)
- Star network, placebo hub, 8 molecule nodes
- 7 separate NMA runs: MACE, CVD, ACM, MI, Stroke, HHF, Renal
- Bucher indirect comparison method (standard for star networks)
- Inverse-variance pooling on log-HR scale
- Per-molecule HR vs placebo + all pairwise indirect HRs + 95% CI
- P-scores per molecule per outcome (Rücker & Schwarzer 2015)
- Consistency cannot be tested (star network) — explicitly disclosed
- SELECT grouped with Semaglutide SC node, flagged as different dose/population

### 2. Unified Ranking Dashboard (NEW)
- Heatmap: rows=molecules, columns=outcomes, cells=P-score (green→red)
- Sortable by any outcome column
- Mean P-score row summary (overall best molecule ranking)
- Sparkline per molecule showing ranking profile across outcomes
- Never published for GLP-1 RA CV endpoints

### 3. Dose-Response for MACE (NEW)
- Primary model: Emax — `HR = 1 - Emax × dose / (ED50 + dose)`
- Sensitivity: Log-linear — `log(HR) = β₀ + β₁ × log(dose)`
- Weighted least squares on log-HR scale, weights = 1/SE²
- Confidence band via delta method
- Within-semaglutide SC: 3 dose levels (0.5mg SUSTAIN-6, 1.0mg SUSTAIN-6, 2.4mg SELECT)
- Cross-molecule potency-equivalent: exploratory, clearly labeled ecological inference
- Visualization: dose vs HR, Emax curve + CI, trial bubbles (size ∝ N), optimal dose annotation

### 4. Fragility Index (NEW)
- Per-trial: iteratively add events to fewer-events arm until Fisher exact p crosses 0.05
- Modify ONE arm only (standard Fragility Index method)
- Display: table with FI, FI/N ratio, color coding (green ≥5, amber 3-4, red ≤2)
- Pooled fragility: how many trials need to flip for pooled result to become non-significant
- First publication of FI for GLP-1 RA CVOTs

### 5. Trial Sequential Analysis (NEW)
- Required Information Size (RIS): control event rate, 15% RRR, alpha 0.05, power 0.80
- Information fraction: cumulative N / RIS
- O'Brien-Fleming alpha-spending boundaries (Lan-DeMets)
- Futility boundary
- Visualization: cumulative Z vs boundaries, chronological (ELIXA 2015 → SOUL 2025)
- Key output: "Has monitoring boundary been crossed?" — conclusiveness statement
- Updates existing cumulative Z-curve (section 4) with formal boundaries

### 6. Bayesian Posterior (ENHANCE)
- Already exists with prior selection
- Add: MCMC trace-like visualization (approximated), posterior predictive check
- Informative prior: based on pre-LEADER era expectations
- Vague prior: N(0, 10²) on log-HR
- Weakly informative: N(0, 0.5²)

### 7. Per-AE Safety Forest Plots (NEW)
- Each AE term becomes its own mini meta-analysis
- Pooling: Mantel-Haenszel RR (preferred for rare events)
- Per-trial RR + CI as forest plot rows, pooled MH diamond
- Heterogeneity: I², tau², Cochran's Q per AE
- Expandable: click any row in safety summary → full forest plot
- NNH for significant signals
- Upgraded summary table: adds I², pooled MH-RR, NNH columns
- Includes SOUL (no competitor has this)

### 8. TruthCert Hierarchical Verdict (NEW)
**Level 1 — Class verdict** (GLP-1 RA class for MACE):
12-point threat assessment:
1. Fragility index < 3
2. Breakdown point < 30%
3. Egger's p < 0.10
4. Trim-fill imputes ≥2 studies
5. I² > 50%
6. Prediction interval crosses null
7. k < 5
8. HKSJ vs Wald CI disagree on significance
9. Any single trial removal flips conclusion
10. TSA boundary not crossed
11. Copas-adjusted estimate crosses null
12. RoB: ≥2 trials high-risk

Severity 0-12 → STABLE (0-3) / MODERATE (4-6) / EXPOSED (7-9) / UNCERTAIN (10-12)

**Level 2 — Per-outcome verdicts**: Same 12 checks for CVD, ACM, MI, Stroke, HHF, Renal.

**Level 3 — Molecule flags**: Qualitative flags where molecule diverges from class signal (ELIXA neutral, semaglutide retinopathy). Not full 12-point (k=1 too thin).

UI: severity gauge arc (0-12), threat checklist with pass/fail icons, per-outcome badge row, molecule flag list.

### 9. Time-to-Benefit Analysis (NEW)
- Data: `timeToSeparation` (months) and `benefitOnset` ('early'/'late') per trial
- Sourced from published KM curves and trial reports
- Visualization: horizontal timeline — trial bar from randomization to end, marker at KM separation
- Class summary: median time-to-benefit
- Novel insight: early vs late separators by molecule/population

### 10. Enhanced Meta-Regression (ENHANCE)
- 5 covariates: mean BMI, mean age, % established CVD, % CKD, median follow-up
- Bubble plot: x=covariate, y=log(HR), bubble size=weight, WLS regression line + CI
- R² and slope p-value
- Covariate dropdown selector
- Extends EHJ-CVP 2025 by adding %CKD and follow-up duration

### 11. GRADE Automation (ENHANCE)
- Automate all 5 domains per outcome:
  - Risk of bias: from RoB data (proportion low/some/high)
  - Inconsistency: I² thresholds (≤25% no, 25-50% serious, >50% very serious)
  - Indirectness: population match assessment
  - Imprecision: CI width relative to MCID, optimal information size
  - Publication bias: Egger's p threshold
- Output: GRADE table with up/down arrows, final certainty rating (HIGH/MOD/LOW/VERY LOW)

### 12. Cumulative MA (EXISTS)
- Already implemented, no changes needed
- Chronological ordering ELIXA→SOUL already present

### 13. R Cross-Validation Extension (ENHANCE)
- Extend generated R script to include `netmeta` code for NMA validation
- Add safety MH-RR validation against `metafor::rma.mh()`
- Add fragility index comparison

## Panel Layout

| # | Panel | Tier | Status |
|---|-------|------|--------|
| 1-19 | Existing panels | Mixed | No change |
| 20 | Fragility Index Table | Standard | NEW |
| 21 | Trial Sequential Analysis | Standard | NEW |
| 22 | NMA League Table | Expert | NEW |
| 23 | NMA Ranking Heatmap | Expert | NEW |
| 24 | Dose-Response Curve | Expert | NEW |
| 25 | Per-AE Safety Forest Plots | Expert | NEW |
| 26 | Time-to-Benefit Timeline | Expert | NEW |
| 27 | TruthCert Verdict Panel | Standard | NEW |

Standard tier panels (20, 21, 27) visible to all users — these are headline differentiators.
Expert tier panels (22-26) behind expert toggle.

## Data Requirements

All data already exists in `realData` or can be derived:
- NMA: uses existing `publishedHR`, `hrLCI`, `hrUCI` per outcome
- Dose-response: uses existing `baseline.dose` + published HRs
- Fragility: uses existing `tE`, `tN`, `cE`, `cN`
- TSA: uses existing event counts + sample sizes
- Safety: uses existing `safetyData` blocks (all 10 trials populated)
- Time-to-benefit: NEW data field — `timeToSeparation` added to `baseline` (from publications)
- Meta-regression: uses existing `baseline` covariates (BMI, age, %CVD, FU)
  - NEW: add `pctCKD` to `baseline` for applicable trials

## Export Additions

- NMA league table CSV
- P-score ranking table CSV
- Fragility index table CSV
- TruthCert verdict receipt JSON (hash-sealed)
- Safety forest plot data CSV
- R script extended with `netmeta` NMA validation code

## Arabic Translations

All new panel headers and key terms added to `_arDict`:
- NMA terminology (league table, P-score, ranking, indirect comparison)
- Fragility (fragility index, breakdown point)
- TSA (information fraction, monitoring boundary, conclusive)
- TruthCert (verdict, threat, severity, stable/moderate/exposed/uncertain)
- Safety (forest plot terms already partially present)
- Time-to-benefit (separation, early, late)
- Dose-response (optimal dose, saturation)

## Estimated New Code

~2,500-3,000 lines of JS:
- NMA engine (Bucher + P-scores + league table + heatmap): ~800 lines
- Fragility index + TSA: ~400 lines
- Dose-response (Emax + log-linear + plot): ~300 lines
- Safety forest plots (per-AE MH meta-analysis): ~400 lines
- TruthCert verdict (12-point + hierarchy + UI): ~400 lines
- Time-to-benefit (data + timeline renderer): ~200 lines
- GRADE automation: ~200 lines
- Glue/UI (panel HTML, dropdowns, translations, exports): ~200 lines

## Data Provenance & Verification (Critical Requirement)

Every data point must be user-verifiable from the source record excerpts presented in the app.

### Principle: No Naked Numbers
- Every number in the analysis must trace back to a viewable source excerpt (abstract text, CT.gov results record, or OpenAlex metadata)
- The user must be able to click/expand any data point and see the original text it was extracted from

### Evidence Panels (existing, extended)
Each trial already has an `evidence[]` array with labeled panels (Enrollment, Endpoints, RoB, etc.). These are extended to cover ALL data points used in the new analyses:
- **Efficacy evidence**: For each outcome HR/event count, show the exact abstract sentence or CT.gov results field it came from, with the relevant numbers highlighted
- **Safety evidence**: For each AE count, show the source table reference and the exact text/numbers
- **Baseline covariates**: For BMI, age, %CVD, %CKD, follow-up — show the abstract excerpt
- **Dose data**: Show the CT.gov intervention description confirming the dose

### Verification UI
- **Data Audit Mode**: A toggle (accessible from the extraction tab) that overlays source citations on every number in the analysis
- **Per-cell provenance**: In the NMA league table, safety table, fragility table — hovering any number shows a tooltip with the source excerpt and locator (e.g., "NEJM 375:311-322, Table 2, Row 3")
- **Abstract viewer**: Each trial has a viewable abstract panel (fetched from PubMed/OpenAlex) with the extracted numbers highlighted in-situ
- **CT.gov record viewer**: Each trial shows key fields from the CT.gov structured results (primary outcome, enrollment, arms) with extracted values highlighted
- **Mismatch flagging**: If a user spots a discrepancy, they can flag it — the flag is stored in state and surfaced in the TruthCert verdict as a data quality concern

### Source Hierarchy
1. **CT.gov structured results** (highest confidence) — machine-readable, timestamped
2. **PubMed abstract** (high confidence) — peer-reviewed, but summary-level
3. **OpenAlex metadata** (moderate) — bibliographic, cross-referenced
4. **Manual entry** (requires user attestation) — flagged as UNCERTIFIED in TruthCert

### Implementation
- Extend each trial's `realData` entry with `provenance` object mapping each data field to its source excerpt and locator
- Abstract text stored in `evidence[]` panels (already partially present)
- New `renderProvenanceTooltip(trialId, fieldName)` function for hover verification
- Data Audit Mode adds `data-provenance` attributes to all rendered numbers
- ~300 additional lines of JS + provenance data in `realData`

## Non-Goals

- No Bayesian MCMC (approximate posterior sufficient)
- No consistency testing (star network — impossible, disclosed)
- No molecule-level safety classifier (k too thin, qualitative flags instead)
- No tirzepatide (SURPASS-CVOT not yet reported)
- No full-text PDF extraction (OA abstracts only)
- No dose-response for individual AE terms (insufficient granularity)
