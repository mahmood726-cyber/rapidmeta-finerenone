# GLP-1 RA CVOT Phase 3: Research Frontier Analytics — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 25 new analytical panels (Panels 28-52) to `GLP1_CVOT_REVIEW.html` implementing research-frontier statistical methods, CT.gov transparency mining, and novel visualizations.

**Architecture:** All code goes into the single existing HTML file (`GLP1_CVOT_REVIEW.html`, currently 10,884 lines). Each panel follows the existing pattern: HTML container in the analysis grid (line ~919), JS render method on `AnalysisEngine`, computation logic either inline or in a dedicated engine object, render call wired into `AnalysisEngine.run()` (line ~8600). Plotly.js for interactive charts, Canvas for lightweight plots.

**Tech Stack:** Vanilla JS (no build tools), Plotly.js (already loaded), HTML/CSS with Tailwind (already loaded), ClinicalTrials.gov API v2 (for Panel 42).

**Spec:** `docs/superpowers/specs/2026-03-10-glp1-cvot-phase3-design.md`

---

## File Structure

Single file modified throughout:
- **Modify:** `C:\Users\user\Downloads\Finrenone\GLP1_CVOT_REVIEW.html`
  - CSS section: lines 15-326 (add new panel styles before `</style>`)
  - Panel HTML grid: line 919 (insert new `<div>` containers after Panel 27)
  - Arabic dictionary: lines 3344-4555 (append terms before closing `},`)
  - `AnalysisEngine.run()`: line ~8600 (add render calls after `renderTruthCert`)
  - Render methods: after line ~10000 (new `AnalysisEngine.render*` functions)
  - R code generation: lines 9104-9271 (extend `nmaSection` string)
  - Export functions: lines 10482-10535 (extend CSV/JSON data)
  - Before `</script>` at line 10882 (absolute boundary)

- **Test:** `C:\Users\user\Downloads\Finrenone\test_glp1_cvot.py` (extend existing Selenium suite)

## Insertion Strategy

All 25 new panels follow this 4-point insertion pattern:

1. **HTML** — Insert after line 919 (after Panel 27 TruthCert container, before the grid closing `</div>` at line 920)
2. **render call** — Insert after line 8600 (after `this.renderTruthCert(...)` in `AnalysisEngine.run()`)
3. **render method** — Insert before `</script>` (line 10882), grouped by subsystem
4. **Arabic** — Insert before line 4555 (before `_arDict` closing `},`)

**CRITICAL RULES** (from `.claude/rules/lessons.md` and `.claude/rules/html-apps.md`):
- Never write literal `</script>` inside JS — use `${'<'}/script>` in template literals
- `?? ... ||` mixing without parens is a SyntaxError — always wrap: `a ?? (b || c)`
- `|| fallback` drops valid zero — use `?? fallback` for numeric fields
- After structural HTML edits, verify div balance (count `<div[\s>]` vs `</div>`)
- `normalQuantile(0.975)` for published 95% CIs — never use user confLevel for published data
- Fragility Index modifies ONE arm only
- Escape all user-facing text with `escapeHtml()`

## Shared Utilities

Several panels share computation patterns. Define these utility functions ONCE (in a `Phase3Utils` object) before the individual panel render methods:

```javascript
const Phase3Utils = {
    // DL pooling on log-HR scale (reusable for subset analyses)
    dlPool(plotData) { ... },
    // Leave-one-out: returns array of {omitted, pOR, lci, uci, tau2, I2}
    leaveOneOut(plotData, confLevel) { ... },
    // Power calculation for a single trial
    trialPower(logHR, se, pooledLogHR) { ... },
    // E-value computation
    evalue(hr) { ... },
    // Formatted Plotly layout with theme detection
    plotlyLayout(title, xTitle, yTitle, extraOpts) { ... }
};
```

These are inserted at line ~10000, before the individual panel renderers.

---

## Chunk 1: Influence Diagnostics (Panels 37-41)

### Task 1: Shared Utilities + Cook's D + DFBETAS (Panel 37)

**Files:**
- Modify: `GLP1_CVOT_REVIEW.html:919` (HTML container)
- Modify: `GLP1_CVOT_REVIEW.html:8600` (render call)
- Modify: `GLP1_CVOT_REVIEW.html:~10000` (Phase3Utils + render method)

- [ ] **Step 1: Add HTML container for Panel 37**

Insert after line 919 (after Panel 27 TruthCert):
```html
<div class="col-span-1 md:col-span-2" data-tier="expert"><div class="chart-header mb-2 px-2"><h4 class="text-[10px] opacity-70 font-bold uppercase tracking-widest" data-translate>37. Cook's Distance & DFBETAS</h4></div><div id="plot-cooks-d" class="chart-container tc-panel-bg" style="height:450px;"></div></div>
```

- [ ] **Step 2: Add Phase3Utils object**

Insert before `</script>` (line 10882). Contains:
- `dlPool(plotData)` — DerSimonian-Laird pooling returning `{pLogOR, pSE, pOR, lci, uci, tau2, I2, Q, k}`
- `leaveOneOut(plotData, confLevel)` — LOO array
- `trialPower(logHR, se, pooledLogHR)` — `1 - normalCDF(1.96 - |pooledLogHR|/se)`
- `evalue(hr)` — `hr + Math.sqrt(hr * (hr - 1))` for HR > 1; for HR < 1: `1/hr + Math.sqrt((1/hr) * (1/hr - 1))`
- `plotlyLayout(title, xTitle, yTitle, opts)` — detects `document.body.classList.contains('light-mode')`, returns themed layout

Key formulas for Cook's D:
```javascript
// Hat values: h_i = w_i / sum(w_i) where w_i = 1/(vi + tau2)
// Standardized residual: r_i = (yi - pooled) / sqrt(vi + tau2)
// Cook's D_i = r_i^2 * h_i / ((1 - h_i)^2 * p) where p = 1
// DFBETAS_i = (pooled - pooled_{-i}) / SE_{pooled}
// Threshold: Cook's D > 4/k, |DFBETAS| > 2/sqrt(k)
```

- [ ] **Step 3: Add renderCooksD method**

```javascript
AnalysisEngine.renderCooksD = function(plotData, pLogOR, tau2) {
    // Compute hat values, residuals, Cook's D, DFBETAS per trial
    // Create Plotly grouped bar chart: trials on x-axis, Cook's D + |DFBETAS| as grouped bars
    // Red threshold lines at 4/k and 2/sqrt(k)
    // Flag outliers in red
};
```

- [ ] **Step 4: Wire render call in AnalysisEngine.run()**

After line 8600 (`this.renderTruthCert(...)`), add:
```javascript
// === PHASE 3 PANELS ===
this.renderCooksD(c.plotData, c.pLogOR, c.tau2);
```

- [ ] **Step 5: Verify — run Selenium test**

Run: `python test_glp1_cvot.py`
Expected: Panel 37 container found with content, zero JS errors.

---

### Task 2: Baujat Plot (Panel 38)

- [ ] **Step 1: Add HTML container**
```html
<div data-tier="expert"><div class="chart-header mb-2 px-2"><h4 class="text-[10px] opacity-70 font-bold uppercase tracking-widest" data-translate>38. Baujat Plot</h4></div><div id="plot-baujat" class="chart-container tc-panel-bg" style="height:400px;"></div></div>
```

- [ ] **Step 2: Add renderBaujat method**

Key computation:
```javascript
// Q_i contribution: Q_total - Q_{-i} (heterogeneity contribution)
// Influence_i: |pooled - pooled_{-i}| (effect on pooled result)
// Plotly scatter: x = Q_i, y = influence_i, text = trial name
// Quadrant lines at median Q_i and median influence
// Top-right quadrant = problematic (influential + heterogeneous)
```

- [ ] **Step 3: Wire render call + verify**

---

### Task 3: GOSH Plot (Panel 39)

- [ ] **Step 1: Add HTML container**
```html
<div data-tier="expert"><div class="chart-header mb-2 px-2"><h4 class="text-[10px] opacity-70 font-bold uppercase tracking-widest" data-translate>39. GOSH Plot</h4></div><div id="plot-gosh" class="chart-container tc-panel-bg" style="height:450px;"></div></div>
```

- [ ] **Step 2: Add renderGOSH method**

Key computation:
```javascript
// k=10 → 2^10 = 1024 subsets (feasible, no sampling needed)
// For each non-empty subset of size ≥2:
//   Run DL pooling → get pooledOR and I²
//   Store as point {or, i2, k_sub}
// Plotly scatter: x = pooledOR, y = I², opacity=0.3
// K-means clustering (k=2,3) using simple Lloyd's algorithm
// Color points by cluster assignment
```

IMPORTANT: k=10 means 1024 subsets. Use bitmask enumeration `for (let mask = 3; mask < (1 << k); mask++)` skipping subsets with fewer than 2 trials (`popcount(mask) >= 2`).

- [ ] **Step 3: Wire render call + verify**

---

### Task 4: Forward Search (Panel 40) + Credibility Ceiling (Panel 41)

- [ ] **Step 1: Add HTML containers for both panels**
```html
<div data-tier="expert"><div class="chart-header mb-2 px-2"><h4 class="text-[10px] opacity-70 font-bold uppercase tracking-widest" data-translate>40. Forward Search</h4></div><div id="plot-forward-search" class="chart-container tc-panel-bg" style="height:400px;"></div></div>
<div data-tier="expert"><div class="chart-header mb-2 px-2"><h4 class="text-[10px] opacity-70 font-bold uppercase tracking-widest" data-translate>41. Credibility Ceiling</h4></div><div id="plot-credibility-ceiling" class="chart-container tc-panel-bg" style="height:400px;"></div></div>
```

- [ ] **Step 2: Add renderForwardSearch method**

```javascript
// Start: find pair (i,j) with smallest Q when pooled together
// Iterate: add trial that least increases Q
// Track at each step: {step, addedTrial, pooledOR, I2, tau2}
// Plotly dual-axis: pooled OR (left axis) + I² (right axis) vs step
// Highlight jumps > 10% I² change as outlier markers
```

- [ ] **Step 3: Add renderCredibilityCeiling method**

```javascript
// Sweep ceiling c from 0.00 to 0.50 in steps of 0.005 (100 points)
// At each c: inflate each trial's variance: vi_new = vi + c²
// Re-run DL pooling with inflated variances
// Track {c, pooledOR, lci, uci, significant}
// Plotly line chart: x = c, y = pooled HR
// Add horizontal line at HR=1.0 (null)
// Mark tipping point where HR crosses 1.0
// Annotation: "Conclusion robust up to c = X%"
```

- [ ] **Step 4: Wire both render calls + verify**

- [ ] **Step 5: Run full Selenium suite, confirm 0 JS errors + all new panels have content**

---

## Chunk 2: Publication Bias Arsenal (Panels 30-36)

### Task 5: E-Values (Panel 36) + Sunset Funnel (Panel 35)

Starting with Standard-tier panels (visible to all users).

- [ ] **Step 1: Add HTML containers**
```html
<div><div class="chart-header mb-2 px-2"><h4 class="text-[10px] opacity-70 font-bold uppercase tracking-widest" data-translate>35. Sunset Funnel Plot</h4></div><div id="plot-sunset-funnel" class="chart-container tc-panel-bg" style="height:450px;"></div></div>
<div class="col-span-1 md:col-span-2"><div class="chart-header mb-2 px-2"><h4 class="text-[10px] opacity-70 font-bold uppercase tracking-widest" data-translate>36. E-Values</h4></div><div id="plot-evalues" class="chart-container tc-panel-bg" style="height:auto;min-height:200px;"></div></div>
```

- [ ] **Step 2: Add renderEValues method**

E-value formula (for HR < 1, i.e. protective):
```javascript
// Convert HR to RR-scale for E-value
// For point estimate: E = 1/HR + sqrt(1/HR * (1/HR - 1))
// For CI bound (closest to null): same formula applied to UCI
// Table: Trial | HR | 95% CI | E-value (point) | E-value (CI)
// Pooled E-value row at bottom
// Color: green (E > 3.0), amber (1.5-3.0), red (< 1.5)
```

- [ ] **Step 3: Add renderSunsetFunnel method**

```javascript
// Standard funnel: x = log(HR), y = SE
// Power contours at 33%, 66%, 80% power
// For each power level p, compute SE threshold:
//   se_threshold = |pooledLogHR| / (z_alpha + z_p)
//   where z_alpha = 1.96, z_p = normalQuantile(p)
// Regions: green (power > 80%), amber (33-80%), red (< 33%)
// Plotly scatter + filled area for power regions
```

- [ ] **Step 4: Wire render calls + verify**

---

### Task 6: Mathur-VanderWeele (Panel 30) + WAAP-WLS (Panel 34)

- [ ] **Step 1: Add HTML containers**

- [ ] **Step 2: Add renderMathurVW method**

```javascript
// Classify trials: affirmative if UCI < 1.0 (for protective HR)
//   i.e., entire CI below null → affirms the beneficial effect
// Non-affirmative: everything else (CI crosses null or HR > 1)
// Pool non-affirmative trials only via DL
// η (eta) sensitivity parameter:
//   η = exp(|pooledLogHR| + 1.96 * pooledSE) — bias factor to nullify
// Display: split forest plot (affirmative group | non-affirmative group | pooled non-affirmative diamond)
// η gauge: arc meter showing strength
```

- [ ] **Step 3: Add renderWAAPWLS method**

```javascript
// For each trial: compute power = trialPower(logHR_i, se_i, pooledLogHR)
// Adequately powered: power >= 0.80
// If count(adequate) >= 2: WLS on adequate-only trials
//   WLS weight = 1/se², pooled = sum(w*y)/sum(w), SE = 1/sqrt(sum(w))
// If count(adequate) < 2: fall back to unrestricted WLS
// Forest plot: adequate trials in green, underpowered in grey
// Annotation: "X/Y trials adequately powered"
```

- [ ] **Step 4: Wire render calls + verify**

---

### Task 7: PET-PEESE (Panel 31) + Vevea-Hedges (Panel 33) + Z-Curve (Panel 32)

- [ ] **Step 1: Add HTML containers for all three**

- [ ] **Step 2: Add renderPETPEESE method**

```javascript
// PET: meta-regression yi = β₀ + β₁*SEi + εi (WLS, weights=1/vi)
//   β₀ = bias-corrected estimate (intercept)
// PEESE: yi = β₀ + β₁*SEi² + εi
// Conditional: if PET p_β₁ > 0.05, use PET; else use PEESE
// Visualization: funnel plot with PET line + PEESE curve overlaid
// Annotation: "Selected estimator: PET/PEESE, β₀ = X [CI]"
```

- [ ] **Step 3: Add renderVeveaHedges method**

```javascript
// Weight function: w(p) = 1 for p < cutpoint, δ for p ≥ cutpoint
// Cut-points: [0.025, 0.05, 0.50, 1.0] (simplified from 8 to 4 for k=10)
// Moderate severity: δ = [1, 0.75, 0.50, 0.25]
// Severe: δ = [1, 0.25, 0.10, 0.05]
// Adjusted estimate via reweighted DL
// LR test: -2*(loglik_unadjusted - loglik_adjusted)
// Display: table with moderate + severe estimates, LR p-values
```

- [ ] **Step 4: Add renderZCurve method**

```javascript
// Convert each trial's log(HR)/SE to z-score
// Observed discovery rate: proportion with |z| > 1.96
// EM mixture with K=3 components: N(0,1) + N(0, σ₁²) + N(0, σ₂²)
//   σ₁ = 1.5, σ₂ = 3.0 (fixed component SDs for simplicity)
//   Initialize mixing proportions π = [0.33, 0.33, 0.34]
//   E-step: posterior assignment probabilities
//   M-step: update π
//   Iterate until convergence (|Δπ| < 1e-6, max 100 iterations)
// ERR: mean power of significant studies (|z| > 1.96)
//   power_i = 1 - normalCDF(1.96 - |μ_i|) where μ_i = posterior expected z
// EDR: overall proportion with true non-null effect (1 - π₁)
// File drawer ratio: (EDR - observed_discovery_rate) / observed_discovery_rate
// Visualization: z-score histogram + fitted mixture density curve + ERR/EDR annotations
```

- [ ] **Step 5: Wire all three render calls + verify**

- [ ] **Step 6: Run full Selenium suite — confirm all Panels 30-36 render with content, 0 JS errors**

---

## Chunk 3: Advanced NMA (Panels 28-29)

### Task 8: Component NMA (Panel 28)

- [ ] **Step 1: Add HTML container**
```html
<div class="col-span-1 md:col-span-2" data-tier="expert"><div class="chart-header mb-2 px-2"><h4 class="text-[10px] opacity-70 font-bold uppercase tracking-widest" data-translate>28. Component NMA</h4></div><div id="plot-component-nma" class="chart-container tc-panel-bg" style="height:450px;"></div></div>
```

- [ ] **Step 2: Add renderComponentNMA method**

Design matrix (4 components per molecule):
```javascript
// Components: [GLP1R_binding, weight_loss, glucose_lowering, anti_inflammatory]
// Weight matrix (molecule → component weights, 0-1 scale):
// lixisenatide:  [1.0, 0.2, 0.6, 0.3]  (short-acting, modest weight/inflammation)
// liraglutide:   [1.0, 0.5, 0.7, 0.6]
// semaglutide_SC:[1.0, 0.9, 0.8, 0.7]  (strongest weight loss)
// exenatide_ER:  [1.0, 0.4, 0.6, 0.4]
// albiglutide:   [1.0, 0.3, 0.5, 0.3]
// dulaglutide:   [1.0, 0.6, 0.7, 0.5]
// efpeglenatide: [1.0, 0.5, 0.6, 0.5]
// semaglutide_oral:[1.0, 0.7, 0.7, 0.6]
//
// WLS: β = (W'VW)⁻¹ W'Vy
// where y = vector of log(HR) per trial
//       V = diag(1/SE²)
//       W = design matrix (trial → component weights from molecule mapping)
// 4×4 matrix inversion via Cramer's rule or Gauss-Jordan
// Component HRs: exp(β_j) ± exp(β_j ± 1.96 * SE_βj)
// SE from diagonal of (W'VW)⁻¹
```

IMPORTANT: Label as EXPLORATORY — ecological inference, trial-level not patient-level.

- [ ] **Step 3: Visualization**

Plotly stacked bar chart: x = molecule, stacked segments = component contributions (proportional to β_j * W_ij). Hover shows component HR.

- [ ] **Step 4: Wire render call + verify**

---

### Task 9: Riley Multivariate MA (Panel 29)

- [ ] **Step 1: Add HTML container**

- [ ] **Step 2: Add renderRileyMV method**

```javascript
// Outcomes: CV death, MI, Stroke (3 MACE components)
// Per trial: extract HR + SE for each available outcome
// Missing outcomes: exclude from that trial's contribution
//
// Within-study correlation (Olkin-Gleser approximation):
//   For 2×2 data: corr(log(HR_j), log(HR_k)) ≈ shared_events / sqrt(total_j * total_k)
//   Default: 0.5 if 2×2 data unavailable
//
// Between-study heterogeneity: 3×3 Σ matrix (DL-type)
//   Diagonal: tau²_j from univariate DL for each outcome
//   Off-diagonal: tau²_jk estimated from method-of-moments
//
// GLS estimator:
//   Stack all outcomes: Y = [y₁₁, y₁₂, y₁₃, y₂₁, ...]
//   Block-diagonal Σ_within + Σ_between
//   pooled = (X'V⁻¹X)⁻¹ X'V⁻¹ Y
//   where X is the design matrix (identity per outcome block)
//
// Output: joint HR per outcome with borrowing-strength CIs
// Correlation matrix display (3×3 heatmap)
// Comparison row: univariate vs multivariate CIs (should be narrower)
```

- [ ] **Step 3: Wire render call + verify**

- [ ] **Step 4: Run full Selenium suite for Chunk 3**

---

## Chunk 4: Decision Robustness (Panels 44-47)

### Task 10: Multiverse Specification Curve (Panel 44)

- [ ] **Step 1: Add HTML container**
```html
<div class="col-span-1 md:col-span-2" data-tier="expert"><div class="chart-header mb-2 px-2"><h4 class="text-[10px] opacity-70 font-bold uppercase tracking-widest" data-translate>44. Multiverse Specification Curve</h4></div><div id="plot-multiverse" class="chart-container tc-panel-bg" style="height:600px;"></div></div>
```

- [ ] **Step 2: Add renderMultiverse method**

```javascript
// Specification dimensions:
// model: ['DL', 'REML'] (2) — PM and HKSJ are CI corrections, not models
// outcome: ['MACE'] (1) — only MACE has enough trials for all combos
// trials: [all10, no_ELIXA, no_SELECT, no_both] (4)
// knappHartung: [false, true] (2)
// trimFill: [false, true] (2)
// Total: 2 × 1 × 4 × 2 × 2 = 32 specifications (not 1728 — reduced scope for k=10)
//
// Actually per spec: 4 models × 4 trial sets × 2 KH × 2 TF = 64 specs
// Using 4 models: DL, REML, DL+HKSJ, REML+HKSJ
//
// For each spec:
//   1. Filter trials
//   2. Run DL or REML pooling
//   3. Apply HKSJ correction if flagged
//   4. Apply trim-fill if flagged (shifts estimate)
//   5. Store: {spec_id, pooledHR, lci, uci, significant, model, trials, kh, tf}
//
// Sort by pooled HR
// Top panel: sorted effect sizes with CIs (Plotly scatter + error bars)
// Bottom panel: specification indicator matrix (binary cells showing which options active)
// Summary text: "X/Y (Z%) specifications significant at 95% CI"
```

- [ ] **Step 3: Wire render call + verify**

---

### Task 11: Threshold Analysis (Panel 45) + Conformal PI (Panel 46) + Credibility Ceiling Robustness (Panel 47)

- [ ] **Step 1: Add HTML containers for all three**

- [ ] **Step 2: Add renderThresholdAnalysis method**

```javascript
// Per trial i: find minimum Δ_i such that shifting log(HR_i) by Δ_i
//   reverses pooled significance
// Approach: binary search on Δ_i ∈ [-2, 2]
//   At each Δ_i: modify trial i's log(HR), re-pool, check if pooled p > 0.05
//   Precision: |Δ_i| to 0.001
// Display: horizontal bar chart sorted by |Δ_i| (most fragile trial first)
// Color: red if |Δ_i| < 0.1 (very fragile), amber < 0.3, green ≥ 0.3
```

- [ ] **Step 3: Add renderConformalPI method**

```javascript
// Jackknife+ conformal prediction interval
// For each trial i:
//   Compute LOO estimate μ_{-i} and LOO residual r_i = y_i - μ_{-i}
// For coverage level 1-α:
//   Sort |r_i| ascending
//   Conformal PI = pooled ± quantile(|r_i|, ceil((1-α)(k+1))/k)
// Sweep α from 0.01 to 0.50 (50 points)
// Compare with standard DL PI at each α
// Plotly dual line chart: PI width vs coverage for conformal (solid) vs DL (dashed)
```

- [ ] **Step 4: Add renderCredibilityCeilingRobust method**

Same algorithm as Panel 41 but framed differently:
```javascript
// Reuse credibility ceiling computation from Phase3Utils
// Focus on: "At what c does HR cross 1.0?"
// Display: clean single-panel with prominent tipping point callout
// If tipping point > 0.20 → "ROBUST" badge, else "FRAGILE"
```

- [ ] **Step 5: Wire all three render calls + verify**

---

## Chunk 5: CT.gov Evidence Delta (Panels 42-43)

### Task 12: Evidence Delta Data Collection

This task pre-computes CT.gov data for all 10 trials and stores it in `realData`.

- [ ] **Step 1: Add `evidenceDelta` field to each trial's realData**

For each of the 10 NCT IDs already in `realData`, add a `ctgovDelta` object:
```javascript
ctgovDelta: {
    hasResults: true/false,
    resultsPostedDate: 'YYYY-MM-DD' or null,
    completionDate: 'YYYY-MM-DD',
    firstPostedDate: 'YYYY-MM-DD',
    lastUpdateDate: 'YYYY-MM-DD',
    reportingLagDays: N,
    hasProtocol: true/false,
    hasSAP: true/false,
    primaryOutcomeRegistered: 'text',
    primaryOutcomePublished: 'text',
    amendmentCount: N,
    mismatchSeverity: 'none'|'minor'|'moderate'|'major',
    compositeScore: 0-100
}
```

Source these from ClinicalTrials.gov API during plan implementation. For the initial build, hard-code known values from the 10 canonical trials (all have published results, all are well-documented).

- [ ] **Step 2: Add ghost inventory data**

```javascript
// In realData, add a ghostTrials array:
RapidMeta.ghostTrials = [
    { nctId: 'NCT05254002', name: 'CONFIDENCE', sponsor: 'Novo Nordisk',
      enrollment: null, completionDate: null, status: 'Unknown',
      verified: false, userAttested: false },
    { nctId: 'NCT05901831', name: 'FINE-ONE', sponsor: 'Unknown',
      enrollment: null, completionDate: null, status: 'Unknown',
      verified: false, userAttested: false }
];
```

- [ ] **Step 3: Verify data loaded — check in Selenium that ctgovDelta exists on ≥8 trials**

---

### Task 13: Evidence Delta Panel (Panel 42) + Evidence Gap Matrix (Panel 43)

- [ ] **Step 1: Add HTML containers**
```html
<div class="col-span-1 md:col-span-2"><div class="chart-header mb-2 px-2"><h4 class="text-[10px] opacity-70 font-bold uppercase tracking-widest" data-translate>42. CT.gov Evidence Delta</h4></div><div id="plot-evidence-delta" class="chart-container tc-panel-bg" style="height:auto;min-height:300px;"></div></div>
<div class="col-span-1 md:col-span-2"><div class="chart-header mb-2 px-2"><h4 class="text-[10px] opacity-70 font-bold uppercase tracking-widest" data-translate>43. Evidence Gap Matrix</h4></div><div id="plot-evidence-gap" class="chart-container tc-panel-bg" style="height:auto;min-height:250px;"></div></div>
```

- [ ] **Step 2: Add renderEvidenceDelta method**

```javascript
// Per trial: display 6-module scorecard
// Module 1 (Results): traffic light based on hasResults + reportingLagDays
// Module 2 (Protocol): green if hasProtocol && hasSAP, amber if one, red if neither
// Module 3 (Drift): amendmentCount display, flag if > 3
// Module 4 (Mismatch): severity badge (none/minor/moderate/major)
// Module 5 (Lag): days from completion to results, color-coded
// Module 6 (Ghost): count of ghost trials + UNVERIFIED badges
// Composite score bar per trial
// Render as HTML table (not Plotly — this is a data table)
```

- [ ] **Step 3: Add renderEvidenceGap method**

```javascript
// Rows: ['MACE', 'CV Death', 'MI', 'Stroke', 'ACM', 'HHF', 'Renal']
// Cols: ['T2DM High CV Risk', 'Obesity + CVD', 'CKD', 'HFrEF', 'HFpEF']
// Cell: count trials + sum(N) where that population × outcome combination has data
// From realData: map each trial's population characteristics to columns
// Color: green (≥3 trials), amber (1-2), red (0), cell text = "K trials, N=X"
// Render as HTML table with colored cells
```

- [ ] **Step 4: Wire render calls + verify**

---

## Chunk 6: Frontier Visualizations (Panels 48-52)

### Task 14: Kilim Plot (Panel 49) + Radial SUCRA (Panel 50) + Fragility Quotient (Panel 52)

Standard-tier panels first.

- [ ] **Step 1: Add HTML containers for all three**

- [ ] **Step 2: Add renderKilimPlot method**

```javascript
// Get per-molecule per-outcome data from NMAEngine results
// z_ij = log(HR_ij) / SE_ij
// Plotly heatmap: x = outcomes, y = molecules, z = z-scores
// Colorscale: blue (z < -2) → white (z = 0) → red (z > 2)
// Annotation overlay: significance stars (|z|>1.96: *, >2.58: **, >3.29: ***)
```

- [ ] **Step 3: Add renderRadialSUCRA method**

```javascript
// From existing NMAEngine P-scores (Panel 23 heatmap data)
// Polar coordinates: angle_j = j * 2π / numOutcomes
// For each molecule: polygon connecting P-scores at each angle
// Canvas rendering (lightweight) or Plotly polar chart
// Area = ranking quality (larger = better)
// Toggle buttons to show/hide individual molecules
```

- [ ] **Step 4: Add renderFragilityQuotient method**

```javascript
// Extends Panel 20 Fragility Index:
// FI/N ratio = FI / min(tN, cN)
// Reverse FI: for non-significant trials, events needed to MAKE significant
//   (reverse direction: add events to fewer-events arm until p < 0.05)
// Pooled FI: count of trials that need to flip for pooled result to flip
//   (already computed in Phase 2 as pooled fragility)
// Plotly bubble chart: x=FI, y=FI/N, size=N, color=significant(green)/not(grey)
// Summary: median FI, median FI/N, most fragile trial name
```

- [ ] **Step 5: Wire all three render calls + verify**

---

### Task 15: Galaxy Plot (Panel 48) + E-Value Profile (Panel 51)

- [ ] **Step 1: Add HTML containers**

- [ ] **Step 2: Add renderGalaxyPlot method**

```javascript
// Per molecule: get HR for CV death (x) and MI (y) from NMA results
// Plotly scatter: each molecule as a point
// Confidence ellipse per molecule (approximated):
//   Center = (logHR_CVD, logHR_MI)
//   Semi-axes from SE of each, correlation from Riley estimate (or 0.5 default)
//   Draw ellipse using parametric: x(t) = cx + a*cos(t)*cos(θ) - b*sin(t)*sin(θ)
// Quadrant annotation: NE="Both benefit", NW="CVD only", SE="MI only", SW="Neither"
// Reference lines at HR=1.0 for both axes
```

- [ ] **Step 3: Add renderEValueProfile method**

```javascript
// Reuse E-values computed in Panel 36
// Horizontal bar chart: trials sorted by E-value descending
// Each trial: two bars — E-value for point estimate (darker) + E-value for CI (lighter)
// Color gradient: green (E > 3) → amber (1.5-3) → red (< 1.5)
// Pooled E-value highlighted at top with different style
```

- [ ] **Step 4: Wire render calls + verify**

- [ ] **Step 5: Run full Selenium suite for all Panels 28-52**

---

## Chunk 7: Integration (Arabic, Exports, R Code, Validation)

### Task 16: Arabic Translations

- [ ] **Step 1: Add all new panel titles to `_arDict`**

Insert before the closing `},` of `_arDict` (line ~4555):
```javascript
// Phase 3 panels
'28. Component NMA': '28. تحليل الشبكة المكوّن',
'29. Riley Multivariate MA': '29. التحليل التلوي متعدد المتغيرات (رايلي)',
'30. Mathur-VanderWeele Worst-Case': '30. حد أسوأ الحالات (ماثور-فاندرويل)',
'31. PET-PEESE Regression': '31. انحدار PET-PEESE',
'32. Z-Curve': '32. منحنى Z',
'33. Vevea-Hedges Weight Function': '33. دالة أوزان فيفيا-هيدجز',
'34. WAAP-WLS': '34. المتوسط المرجح للتجارب ذات القوة الكافية',
'35. Sunset Funnel Plot': '35. مخطط القمع الغروبي',
'36. E-Values': '36. قيم إي',
'37. Cook\'s Distance & DFBETAS': '37. مسافة كوك و DFBETAS',
'38. Baujat Plot': '38. مخطط بوجات',
'39. GOSH Plot': '39. مخطط GOSH',
'40. Forward Search': '40. البحث الأمامي',
'41. Credibility Ceiling': '41. سقف المصداقية',
'42. CT.gov Evidence Delta': '42. دلتا الأدلة من CT.gov',
'43. Evidence Gap Matrix': '43. مصفوفة فجوات الأدلة',
'44. Multiverse Specification Curve': '44. منحنى المواصفات المتعدد',
'45. Threshold Analysis': '45. تحليل العتبة',
'46. Conformal Prediction Intervals': '46. فواصل التنبؤ المتوافقة',
'47. Credibility Ceiling (Robustness)': '47. سقف المصداقية (المتانة)',
'48. Galaxy Plot': '48. مخطط المجرة',
'49. Kilim Plot': '49. مخطط الكليم',
'50. Radial SUCRA': '50. مخطط SUCRA الشعاعي',
'51. E-Value Profile': '51. ملف قيم إي',
'52. Fragility Quotient Dashboard': '52. لوحة حاصل الهشاشة',
```

Plus ~40 additional technical terms (component analysis, worst-case bound, replication rate, etc.) — see spec Section 7 for full list.

- [ ] **Step 2: Verify Arabic translation — run retranslate, check no missing keys**

---

### Task 17: Export Extensions

- [ ] **Step 1: Extend `exportCSV()` method**

Add new data sections to the CSV export (in `ReportEngine.exportCSV`):
```javascript
// After existing CSV data, append:
// --- Influence Diagnostics ---
// Trial, CooksD, DFBETAS, HatValue, Flagged
// --- Publication Bias Arsenal ---
// Method, Estimate, LCI, UCI, Interpretation
// --- E-Values ---
// Trial, HR, E_point, E_ci
// --- Fragility Quotient ---
// Trial, FI, FI_N, ReverseFI, Significant
```

- [ ] **Step 2: Extend `exportJSON()` method**

Add Phase 3 results to the JSON bundle:
```javascript
// Add to exported JSON:
// phase3: {
//   influence: { cooksD: [...], baujat: [...], gosh: {...} },
//   pubBias: { petPeese: {...}, zCurve: {...}, veveaHedges: {...}, mathurVW: {...} },
//   evidenceDelta: { perTrial: [...], ghosts: [...] },
//   multiverse: { specs: [...], summary: {...} },
//   validation: { sha256: '...', tolerances: {...}, confidenceLevel: 'VALIDATED' }
// }
```

- [ ] **Step 3: Add validation manifest to JSON export**

```javascript
// SHA-256 hash of input data (realData stringified)
// Oracle tolerances: { hr: 0.01, i2: 0.5, events: 1 }
// Per-panel confidence level: VALIDATED/DERIVED/EXPLORATORY
// Timestamp
```

- [ ] **Step 4: Verify exports — click export buttons in Selenium, check no errors**

---

### Task 18: R Code Extension

- [ ] **Step 1: Extend R code generation**

In `generateRCode()` method, append to `nmaSection`:
```r
# ═══════════════════════════════════════════════════════════════
# PHASE 3: INFLUENCE DIAGNOSTICS VALIDATION
# ═══════════════════════════════════════════════════════════════
library(metafor)
res <- rma(yi = log_hr, sei = se, method = "DL")
inf <- influence(res)
cat("Cook's D:", round(inf$cook.d, 4), "\n")
cat("DFBETAS:", round(inf$dfbs, 4), "\n")

# GOSH
gosh_res <- gosh(res)
cat("GOSH points:", nrow(gosh_res), "\n")

# ═══════════════════════════════════════════════════════════════
# PET-PEESE
# ═══════════════════════════════════════════════════════════════
pet <- rma(yi = log_hr, sei = se, mods = ~ se, method = "FE")
cat("PET intercept:", round(exp(coef(pet)[1]), 4), "\n")
peese <- rma(yi = log_hr, sei = se, mods = ~ I(se^2), method = "FE")
cat("PEESE intercept:", round(exp(coef(peese)[1]), 4), "\n")

# ═══════════════════════════════════════════════════════════════
# Z-CURVE (requires zcurve package)
# ═══════════════════════════════════════════════════════════════
library(zcurve)
z_scores <- log_hr / se
zc <- zcurve(z_scores)
cat("ERR:", round(zc$ERR, 4), "\n")
cat("EDR:", round(zc$EDR, 4), "\n")
```

- [ ] **Step 2: Verify R code text includes new sections — check in Selenium**

---

### Task 19: CSS + Light Mode + Final Polish

- [ ] **Step 1: Add CSS for new panels**

Before `</style>` (line 326), add:
```css
/* Phase 3 panel backgrounds */
.light-mode #plot-cooks-d, .light-mode #plot-baujat, .light-mode #plot-gosh,
.light-mode #plot-forward-search, .light-mode #plot-credibility-ceiling,
.light-mode #plot-sunset-funnel, .light-mode #plot-evalues,
.light-mode #plot-mathur-vw, .light-mode #plot-waap-wls,
.light-mode #plot-pet-peese, .light-mode #plot-vevea-hedges,
.light-mode #plot-zcurve, .light-mode #plot-component-nma,
.light-mode #plot-riley-mv, .light-mode #plot-multiverse,
.light-mode #plot-threshold, .light-mode #plot-conformal-pi,
.light-mode #plot-credibility-robust, .light-mode #plot-galaxy,
.light-mode #plot-kilim, .light-mode #plot-radial-sucra,
.light-mode #plot-evalue-profile, .light-mode #plot-fragility-quotient,
.light-mode #plot-evidence-delta, .light-mode #plot-evidence-gap {
    background: #fff; border-color: #e2e8f0; color: #1e293b;
}
```

- [ ] **Step 2: Verify div balance**

Run: `grep -c '<div[\s>]' GLP1_CVOT_REVIEW.html` and `grep -c '</div>' GLP1_CVOT_REVIEW.html`
Expected: counts match exactly.

- [ ] **Step 3: Verify script integrity**

Run: Search for literal `</script>` inside script blocks.
Expected: 0 matches (only `${'<'}/script>` allowed).

- [ ] **Step 4: Run complete Selenium test suite**

Run: `python test_glp1_cvot.py`
Expected: All panels render, 0 JS errors, all data validations pass.

- [ ] **Step 5: Extend Selenium test for Phase 3 panels**

Add test assertions for all 25 new panel containers:
```python
phase3_panels = [
    "plot-cooks-d", "plot-baujat", "plot-gosh", "plot-forward-search",
    "plot-credibility-ceiling", "plot-sunset-funnel", "plot-evalues",
    "plot-mathur-vw", "plot-waap-wls", "plot-pet-peese", "plot-vevea-hedges",
    "plot-zcurve", "plot-component-nma", "plot-riley-mv", "plot-multiverse",
    "plot-threshold", "plot-conformal-pi", "plot-credibility-robust",
    "plot-galaxy", "plot-kilim", "plot-radial-sucra", "plot-evalue-profile",
    "plot-fragility-quotient", "plot-evidence-delta", "plot-evidence-gap"
]
for panel_id in phase3_panels:
    content = driver.execute_script(f"""
        var el = document.getElementById('{panel_id}');
        return el ? {{ found: true, len: el.innerHTML.trim().length }} : {{ found: false }};
    """)
    log_result(f"Panel {panel_id}", content.get('found') and content.get('len', 0) > 50)
```

- [ ] **Step 6: Final validation — run extended test suite**

Run: `python test_glp1_cvot.py`
Expected: ALL tests pass including 25 new panel assertions.

---

## Execution Order & Dependencies

```
Task 1-4 (Influence Diagnostics) → independent, start here
Task 5-7 (Pub Bias Arsenal) → independent, can parallel with Task 1-4
Task 8-9 (Advanced NMA) → depends on NMAEngine (already exists)
Task 10-11 (Decision Robustness) → depends on Phase3Utils from Task 1
Task 12-13 (CT.gov Evidence Delta) → independent of others
Task 14-15 (Frontier Viz) → depends on NMA results (Task 8-9) and E-Values (Task 5)
Task 16 (Arabic) → after all panel titles finalized
Task 17 (Exports) → after all computation methods exist
Task 18 (R Code) → after all methods finalized
Task 19 (CSS + Polish) → LAST — after all panels inserted
```

**Parallelizable pairs:**
- Tasks 1-4 + Tasks 12-13 (no shared code)
- Tasks 5-7 + Tasks 8-9 (independent subsystems)

**Sequential requirements:**
- Task 1 (Phase3Utils) must complete before Tasks 10-11
- Tasks 8-9 must complete before Tasks 14-15 (Galaxy/Kilim need NMA data)
- Tasks 16-19 are all final-pass integration

---

## Testing Strategy

After each task:
1. Run `python test_glp1_cvot.py` — check 0 JS errors
2. Verify new panel container has content (innerHTML.length > 50)
3. Verify div balance hasn't broken

After all tasks:
1. Full Selenium suite with Phase 3 panel assertions
2. Manual browser inspection of all 52 panels
3. Light mode toggle test
4. Arabic translation toggle test
5. Export buttons produce valid CSV/JSON
6. R code text includes all validation sections
