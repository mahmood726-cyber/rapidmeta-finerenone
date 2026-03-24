# GLP-1 RA CVOT Review — Phase 3: Research Frontier Analytics

**Date**: 2026-03-10
**File**: `C:\Users\user\Downloads\Finrenone\GLP1_CVOT_REVIEW.html`
**Goal**: Add 25 new analytical panels (Panels 28-52) implementing research-frontier statistical methods, CT.gov transparency mining, and novel visualizations — all validated against R packages with deterministic hashes.

## Competitive Edge After Phase 3

Phase 2 delivered 27 panels including NMA, Fragility, TSA, Dose-Response, Safety Forest Plots, TruthCert, Time-to-Benefit. Phase 3 adds methods no published GLP-1 RA meta-analysis has attempted.

## Section 1: Advanced NMA (Panels 28-29)

### Panel 28: Component NMA (Rücker-Schwarzer 2020)
- Decomposes GLP-1 RA class effect into additive pharmacological components
- Design matrix W: rows = trials, columns = components (GLP-1R binding, weight loss, glucose lowering, anti-inflammatory)
- WLS on log-HR scale: β = (W'VW)^{-1} W'Vy where V = diag(1/SE²)
- Component HRs with 95% CI via delta method
- Visualization: stacked bar showing component contribution per molecule
- Limitation disclosure: ecological inference (trial-level, not patient-level)

### Panel 29: Riley Multivariate MA (Riley 2009)
- Joint model for correlated outcomes: CV death, MI, stroke (MACE components)
- Within-study correlations from 2×2 tables (Olkin-Gleser)
- Between-study correlation via unstructured Σ (DL-type estimator)
- Borrowing strength: trials missing one outcome still contribute
- Output: joint HR per outcome + correlation matrix + forest plot with correlated CIs
- R validation: mvmeta::mvmeta()

## Section 2: Publication Bias Arsenal (Panels 30-36)

### Panel 30: Mathur-VanderWeele Worst-Case Bound (2020)
- Pool only non-affirmative trials (those whose CI includes null or goes wrong direction)
- Compute η sensitivity parameter: minimum bias factor to nullify the result
- If pooled non-affirmative estimate still significant → extremely robust
- Display: forest plot of affirmative vs non-affirmative + η gauge

### Panel 31: PET-PEESE (Stanley & Doucouliagos 2014)
- PET: meta-regression of effect on SE → intercept = bias-corrected estimate
- PEESE: meta-regression on SE² (if PET significant)
- Conditional estimator: use PET if PET p>0.05, else PEESE
- Funnel plot overlay with PET/PEESE regression lines
- R validation: metafor::rma(yi, sei, mods=~sei)

### Panel 32: Z-Curve (Bartoš & Schimmack 2022)
- Convert all trial z-scores to absolute values
- EM mixture model: K=3 components (null, small, large effect)
- Expected Replication Rate (ERR): mean power of significant studies
- Expected Discovery Rate (EDR): overall proportion of true effects
- File-drawer ratio: (EDR - observed discovery rate) / observed discovery rate
- Visualization: z-score histogram with fitted mixture density + ERR/EDR annotations
- R validation: zcurve::zcurve()

### Panel 33: Vevea-Hedges Weight Function (1995)
- Step-function model: publication probability changes at p-value thresholds
- Default cut-points: [0.005, 0.01, 0.025, 0.05, 0.10, 0.25, 0.50, 1.0]
- Severity variants: moderate (gradual decline) and severe (sharp cliff at 0.05)
- Likelihood ratio test vs unadjusted model
- Adjusted pooled estimate + CI
- R validation: weightr::weightfunct()

### Panel 34: WAAP-WLS (Stanley 2017)
- Weighted Average of Adequately Powered trials
- Compute per-trial power for detecting the pooled effect
- Include only trials with power ≥ 80%
- If <2 adequately powered → fall back to unrestricted WLS
- Display: forest plot highlighting adequate-power trials in green
- Interpretation: "bias-corrected estimate from only well-powered trials"

### Panel 35: Sunset Funnel Plot (Kossmeier 2020) — STANDARD TIER
- Standard funnel plot with power contours
- Regions: powered (green), underpowered (amber), twilight (red)
- Trials landing in "sunset" zone = underpowered for the pooled effect
- Interactive: hover shows trial name, effect, SE, power

### Panel 36: E-Values (VanderWeele & Ding 2017) — STANDARD TIER
- Per-trial E-value: minimum unmeasured confounding strength to explain away the result
- E-value = HR + sqrt(HR × (HR-1)) for HR < 1 (protective)
- E-value for CI bound: applied to the CI limit closest to null
- Display: table with E-value per trial + E-value for pooled estimate
- Interpretation guide: "An E-value of 2.5 means an unmeasured confounder would need to be associated with both treatment and outcome by a factor of 2.5 each"

## Section 3: Influence Diagnostics (Panels 37-41)

### Panel 37: Cook's Distance + DFBETAS (Viechtbauer & Cheung 2010)
- Cook's D: combined measure of leverage + residual
- DFBETAS: change in pooled estimate when trial i removed, standardized
- Hat values (leverage): h_i from weight matrix
- Threshold: Cook's D > 4/k or DFBETAS > 2/√k
- Visualization: bar chart of Cook's D per trial, flagged outliers in red
- R validation: metafor::influence(rma.obj)

### Panel 38: Baujat Plot (2002)
- X-axis: contribution to overall heterogeneity (Q_i)
- Y-axis: influence on pooled result (|Δ̂_i|)
- Quadrant interpretation: top-right = influential + heterogeneous (problematic)
- Interactive: click trial point for details

### Panel 39: GOSH Plot (Olkin et al. 2012)
- All 2^k subset meta-analyses (k=10 → 1,024 subsets, feasible)
- Each point: pooled estimate vs I² for that subset
- Density/cluster visualization reveals hidden subgroup structure
- K-means clustering (k=2,3) to identify natural groupings
- R validation: metafor::gosh(rma.obj)

### Panel 40: Forward Search (Petropoulou et al. 2021)
- Start with most homogeneous pair of trials
- Iteratively add trial that least increases heterogeneity
- Track pooled estimate, I², tau² at each step
- Outliers = trials that cause sudden jumps when added
- Visualization: step plot of estimate + I² across iterations

### Panel 41: Credibility Ceiling (Salanti & Ioannidis 2009) — Influence version
- Assume minimum variance floor c per trial (credibility ceiling)
- Sweep c from 0% to 50%
- At each c, recompute pooled estimate with inflated variances
- If conclusion reverses at low c → fragile to residual bias
- Visualization: pooled HR vs ceiling level, with significance threshold line

## Section 4: CT.gov Evidence Delta & Transparency (Panels 42-43)

### Panel 42: CT.gov Evidence Delta — 6 modules
Fetched live from ClinicalTrials.gov API via MCP tools.

**Module 1: Results Coverage**
- Per-trial: does CT.gov record have structured results posted?
- Time from completion to results posting (days)
- Missing results = transparency flag
- Traffic light: green (results posted <1yr), amber (posted >1yr), red (no results)

**Module 2: Protocol/SAP Presence**
- Check protocolSection for uploaded protocol document
- Check if Statistical Analysis Plan is referenced
- Flag trials without protocol = higher risk of outcome switching

**Module 3: Record History Drift**
- Compare first posted date vs last update date
- Count number of amendments
- Flag primary outcome changes (COMPare methodology, Goldacre 2019)
- Endpoint switching detection: compare primaryOutcome at registration vs results

**Module 4: Registry ↔ Abstract Mismatch**
- Compare CT.gov primary endpoint text vs PubMed abstract primary endpoint
- Flag discrepancies in: sample size, primary outcome definition, follow-up duration
- Severity scoring: minor (wording), moderate (different threshold), major (different endpoint)

**Module 5: Reporting Lag**
- Days from primary completion to first results submission
- Days from completion to first publication (PubMed date)
- Flag excessive lag (>365 days from completion to results)

**Module 6: Ghost Inventory**
- Search CT.gov for GLP-1 RA cardiovascular trials that completed but never published
- Known candidates: CONFIDENCE (NCT05254002), FINE-ONE (NCT05901831)
- Per ghost: NCT ID, sponsor, enrollment, completion date, days since completion
- No auto-classification as "ghost" — surfaced with UNVERIFIED flag, requires user attestation

**Evidence Delta Composite Score**: 0-100 per trial (weighted: results 25%, protocol 15%, drift 20%, mismatch 20%, lag 10%, ghost 10%)

### Panel 43: Evidence Gap Matrix — STANDARD TIER
- Rows: outcomes (MACE, CV death, MI, stroke, ACM, HHF, renal)
- Columns: populations (T2DM high CV risk, obesity + CVD, CKD, HFrEF, HFpEF)
- Cells: number of trials + total N providing data for that combination
- Color: green (≥3 trials, N>5000), amber (1-2 trials), red (0 trials)
- Identifies where evidence is thin → future trial priorities

### Validation Framework
- **Deterministic hashes**: SHA-256 of input data + parameters → stored in validation manifest
- **Locked oracle tolerances**: ±0.01 for HRs, ±0.5% for I², ±1 for event counts
- **R parity**: Generated R code reproduces JS results within tolerance
- **Manual review gate**: CT.gov Evidence Delta flags surfaced but never auto-classified
- **Confidence levels**: VALIDATED (R parity confirmed), DERIVED (from validated inputs), EXPLORATORY (novel method)

## Section 5: Decision Robustness (Panels 44-47)

### Panel 44: Multiverse Specification Curve (Voracek 2019; Patel 2019)
- 1,728 analytical specifications from crossing:
  - Model: DL, REML, PM, HKSJ (4)
  - Outcome: MACE, CV death, ACM (3)
  - Trials: all 10, exclude ELIXA, exclude SELECT, exclude both (4)
  - Effect: HR, log-HR (2)
  - Correction: none, HKSJ (2)
  - Knapp-Hartung: yes/no (2) — partially overlaps but distinct from HKSJ correction
  - Trim-fill: with/without (2)
- For each specification: pooled estimate + CI + significance (binary)
- Visualization: sorted effect sizes (top) + specification indicators (bottom matrix)
- Summary: % specifications significant, median effect across all specs
- Key insight: "Does the conclusion depend on analytical choices?"

### Panel 45: Threshold Analysis (Phillippo et al. 2019)
- Linear programming: what minimum data perturbation reverses the conclusion?
- Per-trial: how much would the log-HR need to change to flip pooled significance?
- Invariant threshold: the trial most "on the knife edge"
- Display: bar chart of thresholds per trial, sorted by fragility
- Complementary to Fragility Index (event-based vs effect-based)

### Panel 46: Conformal Prediction Intervals (Lei et al. 2018)
- Distribution-free prediction intervals with guaranteed finite-sample coverage
- No normality assumption (unlike standard PI)
- Jackknife+ conformal method: leave-one-out residuals → exact coverage
- Sweep alpha from 0.50 to 0.99, plot PI width vs coverage
- Compare with standard DerSimonian-Laird PI
- R validation: cfma::conformal.ma() if available, else manual implementation

### Panel 47: Credibility Ceiling (Robustness version)
- Same Salanti & Ioannidis 2009 method as Panel 41 but framed for decision robustness
- Focus question: "At what level of residual bias does the class benefit disappear?"
- Sweep c from 0% to 50%, plot pooled HR vs ceiling
- Mark the "tipping point" where HR crosses 1.0
- If tipping point > 20% → very robust conclusion

## Section 6: Frontier Visualizations (Panels 48-52)

### Panel 48: Galaxy Plot (Dong et al. 2020) — Expert
- Bivariate outcome space: x = CV death HR, y = MI HR
- Each molecule = point with confidence ellipse (from Riley correlation)
- Ellipse size reflects precision (inverse variance)
- Quadrant annotation: NW = CV death benefit only, NE = both benefit, etc.
- Interactive: hover shows molecule name, both HRs, correlation

### Panel 49: Kilim Plot (Seo et al. 2021) — STANDARD TIER
- Heatmap: rows = molecules, columns = outcomes
- Cell color = z-score (blue = strong benefit, white = null, red = harm)
- z = log(HR)/SE
- Overlay: significance markers (* p<0.05, ** p<0.01, *** p<0.001)
- Sortable by any column
- Named after Turkish kilim rugs — pattern reveals molecule profiles

### Panel 50: Radial SUCRA Plot (Seitidis et al. 2023) — STANDARD TIER
- Polar coordinates: angle = outcome, radius = P-score (from existing NMA)
- Each molecule = colored polygon connecting its P-scores
- Larger polygon area = better overall ranking
- Interactive: toggle molecules on/off to compare profiles
- Extends existing heatmap (Panel 23) with intuitive visual comparison

### Panel 51: E-Value Profile Plot — Expert
- X-axis: E-value magnitude (1.0 to 5.0)
- Y-axis: trial stacked by E-value
- Horizontal bars showing E-value for point estimate and CI bound
- Color gradient: green (robust, E>3) → red (fragile, E<1.5)
- Pooled E-value highlighted at top

### Panel 52: Fragility Quotient Dashboard — STANDARD TIER
- Extends existing Fragility Index (Panel 20) with:
  - FI/N ratio (Vukadinovic 2023 normalization)
  - Reverse Fragility Index: events to ADD to make non-significant result significant
  - Pooled Fragility Index: how many trial flips needed to reverse pooled conclusion
  - Visualization: bubble chart (x=FI, y=FI/N, size=N, color=significance)
  - Summary statistics: median FI, median FI/N, most fragile trial

## Section 7: Integration

### Panel Layout (Panels 28-52)

| # | Panel | Tier |
|---|-------|------|
| 28 | Component NMA | Expert |
| 29 | Riley Multivariate MA | Expert |
| 30 | Mathur-VanderWeele Worst-Case | Expert |
| 31 | PET-PEESE Regression | Expert |
| 32 | Z-Curve (EDR/ERR) | Expert |
| 33 | Vevea-Hedges Weight Function | Expert |
| 34 | WAAP-WLS | Expert |
| 35 | Sunset Funnel Plot | Standard |
| 36 | E-Values | Standard |
| 37 | Cook's D + DFBETAS | Expert |
| 38 | Baujat Plot | Expert |
| 39 | GOSH Plot | Expert |
| 40 | Forward Search | Expert |
| 41 | Credibility Ceiling (Influence) | Expert |
| 42 | CT.gov Evidence Delta | Standard |
| 43 | Evidence Gap Matrix | Standard |
| 44 | Multiverse Specification Curve | Expert |
| 45 | Threshold Analysis | Expert |
| 46 | Conformal Prediction Intervals | Expert |
| 47 | Credibility Ceiling (Robustness) | Expert |
| 48 | Galaxy Plot | Expert |
| 49 | Kilim Plot | Standard |
| 50 | Radial SUCRA | Standard |
| 51 | E-Value Profile Plot | Expert |
| 52 | Fragility Quotient Dashboard | Standard |

Standard tier (visible to all): Panels 35, 36, 42, 43, 49, 50, 52
Expert tier (behind toggle): Panels 28-34, 37-41, 44-48, 51

### Export Additions
- Component NMA weights CSV
- Riley multivariate pooled CSV
- Pub bias arsenal summary CSV
- Z-Curve metrics CSV
- Influence diagnostics CSV
- GOSH clusters CSV
- CT.gov Evidence Delta JSON
- Evidence Gap Matrix CSV
- Multiverse results CSV (1,728 rows)
- Threshold analysis CSV
- Conformal PI CSV
- Fragility quotient CSV
- Validation manifest JSON (SHA-256 hashes, tolerances, R parity, confidence levels)
- R script extended with netmeta, puninger, zcurve, vevea, threshold, conformal validation

### Arabic Translations
New terms for _arDict:
- Advanced NMA: component analysis, multivariate, joint model, correlation, design matrix
- Pub Bias Arsenal: worst-case bound, affirmative trial, selection model, weight function, replication rate, discovery rate, file drawer, adequately powered, E-value, unmeasured confounding, sunset
- Influence: Cook's distance, leverage, DFBETAS, Baujat, GOSH, forward search, credibility ceiling, outlier
- CT.gov Evidence Delta: results coverage, protocol drift, reporting lag, ghost trial, outcome switching, SAP, registry mismatch, structured AE
- Decision Robustness: multiverse, specification curve, threshold, conformal, prediction interval, robustness
- Frontier Viz: galaxy, kilim, radial, fragility quotient, reverse fragility

### R Cross-Validation Extension (~200 lines)
Generated R code validates against: netmeta::discomb(), mvmeta::mvmeta(), metafor::rma(mods=~sei), zcurve::zcurve(), weightr::weightfunct(), metafor::influence(), metafor::gosh(), cfma::conformal.ma(), nmathresh::nma_thresh()

### Code Estimate
| Section | Panels | Lines |
|---------|--------|-------|
| Advanced NMA | 28-29 | ~700 |
| Pub Bias Arsenal | 30-36 | ~1,200 |
| Influence Diagnostics | 37-41 | ~800 |
| CT.gov Evidence Delta + Gap Matrix | 42-43 | ~900 |
| Decision Robustness | 44-47 | ~800 |
| Frontier Visualizations | 48-52 | ~600 |
| Glue (exports, Arabic, R, validation, HTML) | — | ~500 |
| **Total** | **25 panels** | **~5,500 lines** |

### Data Requirements
All existing realData fields sufficient for Panels 28-41, 44-52. New data:
- Panel 42: Fetched live from CT.gov API
- Panel 43: Derived from existing outcome × population coverage
- Ghost inventory: CONFIDENCE NCT05254002, FINE-ONE NCT05901831 + any discovered

## Non-Goals
- No Bayesian MCMC (approximate posterior sufficient)
- No consistency testing (star network — impossible, disclosed)
- No tirzepatide (SURPASS-CVOT not yet reported)
- No full-text PDF extraction (OA abstracts only)
- No patient-level component NMA (trial-level ecological inference, disclosed)
- No auto-classification of ghost trials (manual review gate required)
