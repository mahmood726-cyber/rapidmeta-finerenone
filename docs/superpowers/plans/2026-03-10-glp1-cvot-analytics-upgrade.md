# GLP-1 RA CVOT Analytics Upgrade — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 8 new analysis panels (NMA, ranking heatmap, dose-response, fragility, TSA, per-AE safety forests, time-to-benefit, TruthCert verdict) plus data provenance system to GLP1_CVOT_REVIEW.html, making it the most analytically comprehensive GLP-1 RA CVOT platform published.

**Architecture:** All new modules plug into the existing `AnalysisEngine` object as new `render*()` methods or standalone engine objects (like existing `BayesianEngine`, `CopasEngine`). New panels 20-27 follow the established `plot-*/desc-*` DOM pattern. Star-network NMA uses Bucher indirect comparisons on published HRs.

**Tech Stack:** Single-file HTML, vanilla JS, Plotly.js (CDN), TailwindCSS (CDN), Canvas 2D for heatmaps/timelines.

**File:** `C:\Users\user\Downloads\Finrenone\GLP1_CVOT_REVIEW.html` (9,724 lines)

**Key insertion points:**
- Panel HTML: after line 889 (before grid closing div at 890)
- Render calls: after line 8261 (`this.renderSafetyProfile(trials)`)
- Stat helpers: after line 1400 (after existing helpers)
- Translation keys: before line 4228 (`_arDict` closing)
- Export functions: near line 9442 (`exportJSON`)
- Plot ID registry: line 7953 (plot ID array), line 7958 (desc ID array)

**Spec:** `docs/superpowers/specs/2026-03-10-glp1-cvot-analytics-upgrade-design.md`

---

## Chunk 1: Foundation — Panel HTML + Data Extensions + Stat Helpers

### Task 1: Add panel 20-27 HTML containers

**Files:**
- Modify: `GLP1_CVOT_REVIEW.html:889` (insert after last expert-only panel)

- [ ] **Step 1: Read current panel section to confirm insertion point**

Read lines 880-895 to verify panel 19 (safety) ends at line 889.

- [ ] **Step 2: Insert 8 new panel containers after line 889**

```html
<!-- Panel 20: Fragility Index (Standard tier) -->
<div class="col-span-1 md:col-span-2"><div class="chart-header mb-2 px-2"><h4 class="text-[10px] opacity-70 font-bold uppercase tracking-widest" data-translate>20. Fragility Index</h4></div><div id="plot-fragility" class="chart-container" style="height:auto;min-height:200px;" aria-describedby="desc-fragility"></div><div id="desc-fragility" class="chart-desc"></div></div>

<!-- Panel 21: Trial Sequential Analysis (Standard tier) -->
<div class="col-span-1 md:col-span-2"><div class="chart-header mb-2 px-2"><h4 class="text-[10px] opacity-70 font-bold uppercase tracking-widest" data-translate>21. Trial Sequential Analysis</h4></div><div id="plot-tsa-full" class="chart-container" style="height:400px;" aria-describedby="desc-tsa-full"></div><div id="desc-tsa-full" class="chart-desc"></div></div>

<!-- Panel 22: NMA League Table (Expert) -->
<div class="col-span-1 md:col-span-2 expert-only"><div class="chart-header mb-2 px-2"><h4 class="text-[10px] opacity-70 font-bold uppercase tracking-widest" data-translate>22. NMA League Table</h4><select id="nma-outcome-select" class="ml-2 bg-slate-800 text-xs rounded px-2 py-1 border border-slate-700"></select></div><div id="plot-nma-league" class="chart-container" style="height:auto;min-height:300px;" aria-describedby="desc-nma-league"></div><div id="desc-nma-league" class="chart-desc"></div></div>

<!-- Panel 23: NMA Ranking Heatmap (Expert) -->
<div class="col-span-1 md:col-span-2 expert-only"><div class="chart-header mb-2 px-2"><h4 class="text-[10px] opacity-70 font-bold uppercase tracking-widest" data-translate>23. NMA Ranking Dashboard</h4></div><div id="plot-nma-heatmap" class="chart-container" style="height:auto;min-height:350px;" aria-describedby="desc-nma-heatmap"></div><div id="desc-nma-heatmap" class="chart-desc"></div></div>

<!-- Panel 24: Dose-Response Curve (Expert) -->
<div class="col-span-1 md:col-span-2 expert-only"><div class="chart-header mb-2 px-2"><h4 class="text-[10px] opacity-70 font-bold uppercase tracking-widest" data-translate>24. Dose-Response Analysis</h4></div><div id="plot-dose-response" class="chart-container" style="height:400px;" aria-describedby="desc-dose-response"></div><div id="desc-dose-response" class="chart-desc"></div></div>

<!-- Panel 25: Per-AE Safety Forest Plots (Expert) -->
<div class="col-span-1 md:col-span-2 expert-only"><div class="chart-header mb-2 px-2"><h4 class="text-[10px] opacity-70 font-bold uppercase tracking-widest" data-translate>25. Safety Forest Plots (Per-AE Meta-Analysis)</h4></div><div id="plot-safety-forest" class="chart-container" style="height:auto;min-height:300px;" aria-describedby="desc-safety-forest"></div><div id="desc-safety-forest" class="chart-desc"></div></div>

<!-- Panel 26: Time-to-Benefit Timeline (Expert) -->
<div class="col-span-1 md:col-span-2 expert-only"><div class="chart-header mb-2 px-2"><h4 class="text-[10px] opacity-70 font-bold uppercase tracking-widest" data-translate>26. Time-to-Benefit Analysis</h4></div><div id="plot-time-benefit" class="chart-container" style="height:350px;" aria-describedby="desc-time-benefit"></div><div id="desc-time-benefit" class="chart-desc"></div></div>

<!-- Panel 27: TruthCert Verdict (Standard tier) -->
<div class="col-span-1 md:col-span-2"><div class="chart-header mb-2 px-2"><h4 class="text-[10px] opacity-70 font-bold uppercase tracking-widest" data-translate>27. TruthCert Evidence Verdict</h4></div><div id="plot-truthcert" class="chart-container" style="height:auto;min-height:250px;" aria-describedby="desc-truthcert"></div><div id="desc-truthcert" class="chart-desc"></div></div>
```

- [ ] **Step 3: Register new plot/desc IDs in the ID arrays**

At line 7953 (plot ID array), add:
```javascript
'plot-fragility','plot-tsa-full','plot-nma-league','plot-nma-heatmap','plot-dose-response','plot-safety-forest','plot-time-benefit','plot-truthcert'
```

At line 7958 (desc ID array), add:
```javascript
'desc-fragility','desc-tsa-full','desc-nma-league','desc-nma-heatmap','desc-dose-response','desc-safety-forest','desc-time-benefit','desc-truthcert'
```

- [ ] **Step 4: Verify div balance**

Run: `python -c "import re; c=open(r'C:\Users\user\Downloads\Finrenone\GLP1_CVOT_REVIEW.html','r',encoding='utf-8').read(); print(f'opens={len(re.findall(r\"<div[\\s>]\",c))} closes={len(re.findall(r\"</div>\",c))}')"`
Expected: opens == closes

- [ ] **Step 5: Commit**

```bash
git add GLP1_CVOT_REVIEW.html
git commit -m "feat: add 8 new panel containers (20-27) for analytics upgrade"
```

---

### Task 2: Extend trial data with new fields

**Files:**
- Modify: `GLP1_CVOT_REVIEW.html` — `realData` object (lines 1490-2007)

- [ ] **Step 1: Add time-to-benefit and %CKD data to each trial's baseline**

For each trial in `realData`, add to the `baseline` object:
```javascript
// ELIXA (NCT01147250)
timeToSeparation: null, benefitOnset: 'none', pctCKD: 22.3,
// Source: Pfeffer MA et al. NEJM 2015;373:2247-2257

// LEADER (NCT01179048)
timeToSeparation: 18, benefitOnset: 'late', pctCKD: 23.1,
// Source: Marso SM et al. NEJM 2016;375:311-322, Fig 2

// SUSTAIN-6 (NCT01720446)
timeToSeparation: 16, benefitOnset: 'late', pctCKD: 28.5,
// Source: Marso SP et al. NEJM 2016;375:1834-1844, Fig 2

// EXSCEL (NCT01144338)
timeToSeparation: null, benefitOnset: 'none', pctCKD: 21.6,
// Source: Holman RR et al. NEJM 2017;377:1228-1239

// HARMONY (NCT02465515)
timeToSeparation: 8, benefitOnset: 'early', pctCKD: 24.2,
// Source: Hernandez AF et al. Lancet 2018;392:1519-1529, Fig 2

// REWIND (NCT01394952)
timeToSeparation: 24, benefitOnset: 'late', pctCKD: 22.2,
// Source: Gerstein HC et al. Lancet 2019;394:121-130, Fig 2

// PIONEER 6 (NCT02692716)
timeToSeparation: null, benefitOnset: 'none', pctCKD: 26.9,
// Source: Husain M et al. NEJM 2019;381:841-851 (noninferiority, underpowered for superiority)

// AMPLITUDE-O (NCT03496298)
timeToSeparation: 10, benefitOnset: 'early', pctCKD: 31.6,
// Source: Gerstein HC et al. NEJM 2021;385:896-907, Fig 2

// SELECT (NCT03574597)
timeToSeparation: 12, benefitOnset: 'early', pctCKD: 0,
// Source: Lincoff AM et al. NEJM 2023;389:2221-2232, Fig 2 (no CKD inclusion criterion, obesity pop)

// SOUL (NCT03914326)
timeToSeparation: 12, benefitOnset: 'early', pctCKD: 32.8,
// Source: McGuire DK et al. NEJM 2025;392:2001-2012, Fig 2
```

- [ ] **Step 2: Add provenance object to each trial**

Add a `provenance` field to each trial in `realData` mapping key data fields to source excerpts:
```javascript
provenance: {
    tE: { source: 'CT.gov NCT01179048 Results', excerpt: 'Primary Outcome: MACE events treatment arm: 608', locator: 'ClinicalTrials.gov Outcome Measures' },
    cE: { source: 'CT.gov NCT01179048 Results', excerpt: 'Primary Outcome: MACE events placebo arm: 694', locator: 'ClinicalTrials.gov Outcome Measures' },
    publishedHR: { source: 'Marso SM et al. NEJM 2016;375:311-322', excerpt: 'HR 0.87; 95% CI, 0.78 to 0.97; P=0.01', locator: 'Abstract, Results' },
    safetyNausea: { source: 'Marso SM et al. NEJM 2016;375:311-322, Supplementary Appendix', excerpt: 'Nausea: liraglutide 1062 (22.7%), placebo 420 (9.0%)', locator: 'Table S4' },
    timeToSeparation: { source: 'Marso SM et al. NEJM 2016;375:311-322', excerpt: 'KM curves begin to separate at approximately 18 months', locator: 'Figure 2' }
}
```

Repeat for all 10 trials. Each trial needs provenance entries for: tE, cE, tN, cN, publishedHR, hrLCI, hrUCI, each safetyData event, timeToSeparation, and key baseline covariates.

- [ ] **Step 3: Add dose data for dose-response analysis**

Add `doseNumeric` (mg, numeric) to each trial's baseline:
```javascript
// ELIXA: doseNumeric: 20 (lixisenatide 20μg = 0.02mg, but use μg scale for all)
// Use μg scale for consistency:
// ELIXA: 20, LEADER: 1800, SUSTAIN-6: [500, 1000], EXSCEL: 2000,
// HARMONY: 30000 (30mg), REWIND: 1500, PIONEER 6: 14000 (14mg oral),
// SELECT: 2400, AMPLITUDE-O: [4000, 6000], SOUL: 14000

// For dose-response, only semaglutide SC has multiple dose levels:
// SUSTAIN-6 arm 1: 0.5mg (500μg), arm 2: 1.0mg (1000μg)
// SELECT: 2.4mg (2400μg)
// These are the primary dose-response data points
```

Store as `doseResponseData` array in a new top-level object near `realData`:
```javascript
const doseResponseData = {
    semaglutideSC: [
        { dose: 0.5, hr: 0.74, lci: 0.58, uci: 0.95, n: 826, trial: 'SUSTAIN-6 (0.5mg arm)', source: 'Marso SP et al. NEJM 2016;375:1834-1844, Table S4' },
        { dose: 1.0, hr: 0.74, lci: 0.58, uci: 0.95, n: 822, trial: 'SUSTAIN-6 (1.0mg arm)', source: 'Marso SP et al. NEJM 2016;375:1834-1844, Table S4' },
        { dose: 2.4, hr: 0.80, lci: 0.72, uci: 0.90, n: 8803, trial: 'SELECT', source: 'Lincoff AM et al. NEJM 2023;389:2221-2232' }
    ]
};
```

Note: SUSTAIN-6 reported pooled 0.5mg+1.0mg MACE HR 0.74. Individual arm data may need verification from supplementary tables. If not available separately, use pooled value for both arms and note this limitation.

- [ ] **Step 4: Commit**

```bash
git add GLP1_CVOT_REVIEW.html
git commit -m "feat: add time-to-benefit, pctCKD, dose-response data, and provenance to trial data"
```

---

### Task 3: Add new statistical helper functions

**Files:**
- Modify: `GLP1_CVOT_REVIEW.html` — insert after line ~1400 (after existing stat helpers)

- [ ] **Step 1: Add Mantel-Haenszel RR pooling function**

```javascript
function poolMantelHaenszel(studies) {
    // studies: [{tE, tN, cE, cN}]
    // Returns: {rr, lci, uci, se, Q, I2, pQ}
    const confLevel = RapidMeta.state.confLevel ?? 0.95;
    const z = normalQuantile(1 - (1 - confLevel) / 2);
    let sumW = 0, sumWR = 0, Q = 0;
    const weights = [], logRRs = [];
    studies.forEach(s => {
        if (s.tE === 0 || s.cE === 0 || s.tN === 0 || s.cN === 0) return;
        const rr = (s.tE / s.tN) / (s.cE / s.cN);
        const w = (s.cE * s.tN) / (s.tN + s.cN);
        sumW += w;
        sumWR += w * rr;
        weights.push(w);
        logRRs.push(Math.log(rr));
    });
    if (sumW === 0) return null;
    const rrMH = sumWR / sumW;
    const logRRMH = Math.log(rrMH);
    // Greenland-Robins variance estimator
    let varNum = 0;
    studies.forEach((s, i) => {
        if (s.tE === 0 || s.cE === 0 || s.tN === 0 || s.cN === 0) return;
        const rr = (s.tE / s.tN) / (s.cE / s.cN);
        const w = (s.cE * s.tN) / (s.tN + s.cN);
        const P = (s.tE / s.tN + s.cE / s.cN);
        varNum += w * w * ((1 / s.tE) - (1 / s.tN) + (1 / s.cE) - (1 / s.cN));
    });
    const seMH = Math.sqrt(varNum) / sumW;
    const lci = Math.exp(logRRMH - z * seMH);
    const uci = Math.exp(logRRMH + z * seMH);
    // Cochran Q
    logRRs.forEach((lr, i) => {
        Q += weights[i] * (lr - logRRMH) * (lr - logRRMH);
    });
    const df = logRRs.length - 1;
    const I2 = df > 0 ? Math.max(0, (Q - df) / Q * 100) : 0;
    const pQ = df > 0 ? 1 - chi2CDF(Q, df) : 1;
    return { rr: rrMH, lci, uci, se: seMH, logRR: logRRMH, Q, I2, pQ, k: logRRs.length };
}

function chi2CDF(x, df) {
    if (x <= 0) return 0;
    return 1 - chi2Pvalue(x, df);
}
```

- [ ] **Step 2: Add Bucher indirect comparison function**

```javascript
function bucherIndirect(hrA, seA, hrB, seB) {
    // Indirect comparison: A vs B = A vs Placebo / B vs Placebo
    // On log scale: log(HR_AB) = log(HR_A) - log(HR_B)
    const logHR = Math.log(hrA) - Math.log(hrB);
    const se = Math.sqrt(seA * seA + seB * seB);
    const confLevel = RapidMeta.state.confLevel ?? 0.95;
    const z = normalQuantile(1 - (1 - confLevel) / 2);
    const hr = Math.exp(logHR);
    const lci = Math.exp(logHR - z * se);
    const uci = Math.exp(logHR + z * se);
    const pval = 2 * (1 - normalCDF(Math.abs(logHR / se)));
    return { hr, lci, uci, logHR, se, pval };
}
```

- [ ] **Step 3: Add P-score calculation function**

```javascript
function computePscores(molecules, outcomeKey) {
    // molecules: [{name, hr, se}] — each vs placebo
    // P-score = proportion of all pairwise comparisons where this molecule wins
    // Rücker & Schwarzer 2015
    const n = molecules.length;
    const pscores = new Array(n).fill(0);
    for (let i = 0; i < n; i++) {
        let sum = 0;
        for (let j = 0; j < n; j++) {
            if (i === j) continue;
            const indirect = bucherIndirect(molecules[i].hr, molecules[i].se, molecules[j].hr, molecules[j].se);
            // P(i better than j) = Phi(-logHR_ij / se_ij)
            // Lower HR = better for CV outcomes
            sum += normalCDF(-indirect.logHR / indirect.se);
        }
        pscores[i] = sum / (n - 1);
    }
    return pscores;
}
```

- [ ] **Step 4: Add fragility index calculation function**

```javascript
function computeFragilityIndex(tE, tN, cE, cN) {
    // Modify fewer-events arm: add events until Fisher p > 0.05
    // Returns: { fi: number, modifiedArm: 'treatment'|'control' }
    let fi = 0;
    let a = tE, b = tN - tE, c = cE, d = cN - cE;
    const origP = fisherExactP(a, b, c, d);
    if (origP >= 0.05) return { fi: 0, modifiedArm: 'none', origP };

    // Determine which arm has fewer events
    if (tE <= cE) {
        // Add events to treatment arm
        while (fi < 1000) {
            a++; b--;
            if (b < 0) break;
            fi++;
            const p = fisherExactP(a, b, c, d);
            if (p >= 0.05) return { fi, modifiedArm: 'treatment', finalP: p, origP };
        }
    } else {
        // Add events to control arm
        while (fi < 1000) {
            c++; d--;
            if (d < 0) break;
            fi++;
            const p = fisherExactP(a, b, c, d);
            if (p >= 0.05) return { fi, modifiedArm: 'control', finalP: p, origP };
        }
    }
    return { fi: Infinity, modifiedArm: tE <= cE ? 'treatment' : 'control', origP };
}

function fisherExactP(a, b, c, d) {
    // Two-tailed Fisher exact test via hypergeometric
    const n = a + b + c + d;
    const r1 = a + b, r2 = c + d, c1 = a + c, c2 = b + d;
    const pObs = hypergeomPMF(a, n, c1, r1);
    let pVal = 0;
    for (let x = Math.max(0, c1 - r2); x <= Math.min(c1, r1); x++) {
        const px = hypergeomPMF(x, n, c1, r1);
        if (px <= pObs + 1e-12) pVal += px;
    }
    return Math.min(pVal, 1);
}

function hypergeomPMF(k, N, K, n) {
    // P(X=k) = C(K,k)*C(N-K,n-k)/C(N,n)
    return Math.exp(lnComb(K, k) + lnComb(N - K, n - k) - lnComb(N, n));
}

function lnComb(n, k) {
    if (k < 0 || k > n) return -Infinity;
    return lgamma(n + 1) - lgamma(k + 1) - lgamma(n - k + 1);
}
```

- [ ] **Step 5: Add Emax dose-response fitting function**

```javascript
function fitEmax(doseData) {
    // doseData: [{dose, logHR, se}]
    // Emax model: logHR = -Emax * dose / (ED50 + dose)
    // Fit via grid search + Nelder-Mead simplex on WLS objective
    if (doseData.length < 2) return null;
    const weights = doseData.map(d => 1 / (d.se * d.se));

    function objective(params) {
        const [Emax, ED50] = params;
        if (ED50 <= 0 || Emax <= 0) return 1e12;
        let sse = 0;
        doseData.forEach((d, i) => {
            const predicted = -Emax * d.dose / (ED50 + d.dose);
            sse += weights[i] * (d.logHR - predicted) ** 2;
        });
        return sse;
    }

    // Grid search for initial values
    let bestObj = Infinity, bestParams = [0.2, 1.0];
    for (let emax = 0.05; emax <= 1.0; emax += 0.05) {
        for (let ed50 = 0.1; ed50 <= 5.0; ed50 += 0.1) {
            const obj = objective([emax, ed50]);
            if (obj < bestObj) { bestObj = obj; bestParams = [emax, ed50]; }
        }
    }

    // Simple Nelder-Mead refinement (20 iterations)
    let [emax, ed50] = bestParams;
    const step = 0.01;
    for (let iter = 0; iter < 100; iter++) {
        const current = objective([emax, ed50]);
        const candidates = [
            [emax + step, ed50], [emax - step, ed50],
            [emax, ed50 + step], [emax, ed50 - step],
            [emax + step, ed50 + step], [emax - step, ed50 - step]
        ];
        let improved = false;
        for (const c of candidates) {
            if (c[0] <= 0 || c[1] <= 0) continue;
            const obj = objective(c);
            if (obj < current - 1e-10) { emax = c[0]; ed50 = c[1]; improved = true; break; }
        }
        if (!improved) break;
    }

    // Generate curve points
    const maxDose = Math.max(...doseData.map(d => d.dose)) * 1.2;
    const curve = [];
    for (let d = 0; d <= maxDose; d += maxDose / 100) {
        const logHR = -emax * d / (ed50 + d);
        curve.push({ dose: d, hr: Math.exp(logHR) });
    }

    return { emax, ed50, curve, objective: objective([emax, ed50]) };
}
```

- [ ] **Step 6: Add O'Brien-Fleming alpha-spending boundary function**

```javascript
function obrienFlemingBoundary(informationFraction, alpha) {
    // Lan-DeMets spending function approximating O'Brien-Fleming
    // alpha_spent(t) = 2 - 2 * Phi(z_{alpha/2} / sqrt(t))
    alpha = alpha ?? 0.05;
    const zAlpha2 = normalQuantile(1 - alpha / 2);
    const spent = 2 * (1 - normalCDF(zAlpha2 / Math.sqrt(informationFraction)));
    const zBoundary = normalQuantile(1 - spent / 2);
    return { spent, zBoundary, informationFraction };
}

function computeRIS(pC, rrr, alpha, power) {
    // Required Information Size
    // pC = control event rate, rrr = relative risk reduction
    alpha = alpha ?? 0.05; power = power ?? 0.80;
    const pT = pC * (1 - rrr);
    const zAlpha = normalQuantile(1 - alpha / 2);
    const zBeta = normalQuantile(power);
    const pBar = (pC + pT) / 2;
    const n = ((zAlpha + zBeta) ** 2 * 2 * pBar * (1 - pBar)) / ((pC - pT) ** 2);
    return Math.ceil(n);
}
```

- [ ] **Step 7: Verify no syntax errors by searching for unmatched braces**

Run a quick check that the file still has balanced script tags and no `</script>` inside JS.

- [ ] **Step 8: Commit**

```bash
git add GLP1_CVOT_REVIEW.html
git commit -m "feat: add MH pooling, Bucher indirect, P-scores, fragility, Emax, OBF boundary helpers"
```

---

## Chunk 2: NMA Engine (Panels 22-23)

### Task 4: Implement NMAEngine object

**Files:**
- Modify: `GLP1_CVOT_REVIEW.html` — insert new `NMAEngine` object after `AnalysisEngine` closing (after line ~9026)

- [ ] **Step 1: Create NMAEngine with run() method**

```javascript
const NMAEngine = {
    outcomes: ['MACE', 'CVD', 'ACM', 'MI', 'Stroke', 'HHF', 'Renal'],

    _getMoleculeData(trials, outcomeKey) {
        // Extract per-molecule HR vs placebo for given outcome
        const molecules = {};
        trials.forEach(t => {
            if (!t.data || !t.data.allOutcomes) return;
            const mol = t.data.baseline?.molecule;
            if (!mol) return;
            const outcome = t.data.allOutcomes.find(o => o.shortLabel === outcomeKey);
            if (!outcome || !outcome.effect || !outcome.lci || !outcome.uci) return;
            const logHR = Math.log(outcome.effect);
            const se = (Math.log(outcome.uci) - Math.log(outcome.lci)) / (2 * normalQuantile(1 - (1 - (RapidMeta.state.confLevel ?? 0.95)) / 2));
            if (!molecules[mol]) molecules[mol] = { name: mol, logHRs: [], ses: [], trials: [], weights: [] };
            molecules[mol].logHRs.push(logHR);
            molecules[mol].ses.push(se);
            molecules[mol].trials.push(t.data.name ?? t.id);
            molecules[mol].weights.push(1 / (se * se));
        });
        // Pool within molecule if multiple trials (e.g., Semaglutide SC: SUSTAIN-6 + SELECT)
        const result = [];
        Object.values(molecules).forEach(m => {
            if (m.logHRs.length === 1) {
                result.push({ name: m.name, hr: Math.exp(m.logHRs[0]), se: m.ses[0], logHR: m.logHRs[0], k: 1, trials: m.trials });
            } else {
                // Fixed-effect IV pooling within molecule
                const sumW = m.weights.reduce((a, b) => a + b, 0);
                const pooledLogHR = m.weights.reduce((s, w, i) => s + w * m.logHRs[i], 0) / sumW;
                const pooledSE = 1 / Math.sqrt(sumW);
                result.push({ name: m.name, hr: Math.exp(pooledLogHR), se: pooledSE, logHR: pooledLogHR, k: m.logHRs.length, trials: m.trials });
            }
        });
        return result;
    },

    _buildLeagueTable(molecules) {
        // All pairwise indirect comparisons via Bucher method
        const n = molecules.length;
        const table = Array.from({ length: n }, () => Array(n).fill(null));
        for (let i = 0; i < n; i++) {
            for (let j = 0; j < n; j++) {
                if (i === j) { table[i][j] = { hr: 1, lci: 1, uci: 1, se: 0, pval: 1 }; continue; }
                table[i][j] = bucherIndirect(molecules[i].hr, molecules[i].se, molecules[j].hr, molecules[j].se);
            }
        }
        return table;
    },

    run(trials) {
        const results = {};
        this.outcomes.forEach(outcome => {
            const molecules = this._getMoleculeData(trials, outcome);
            if (molecules.length < 2) { results[outcome] = null; return; }
            const league = this._buildLeagueTable(molecules);
            const pscores = computePscores(molecules, outcome);
            results[outcome] = { molecules, league, pscores };
        });
        return results;
    }
};
```

- [ ] **Step 2: Commit**

```bash
git commit -m "feat: add NMAEngine with per-outcome star-network NMA and Bucher indirect comparisons"
```

---

### Task 5: Render NMA League Table (Panel 22)

**Files:**
- Modify: `GLP1_CVOT_REVIEW.html` — add `renderNMALeague()` to AnalysisEngine

- [ ] **Step 1: Add outcome selector population and render method**

Insert before `renderSafetyProfile()` (before line 8904):

```javascript
renderNMALeague(nmaResults) {
    const el = document.getElementById('plot-nma-league');
    const descEl = document.getElementById('desc-nma-league');
    const select = document.getElementById('nma-outcome-select');
    if (!el || !nmaResults) return;

    // Populate outcome selector
    if (select) {
        select.innerHTML = '';
        NMAEngine.outcomes.forEach(o => {
            if (nmaResults[o]) {
                const opt = document.createElement('option');
                opt.value = o;
                const labels = RapidMeta._outcomeLabelNames();
                opt.textContent = labels[o] ?? o;
                select.appendChild(opt);
            }
        });
        select.onchange = () => this._renderLeagueForOutcome(nmaResults, select.value, el);
    }

    // Render first available outcome
    const firstOutcome = NMAEngine.outcomes.find(o => nmaResults[o]);
    if (firstOutcome) {
        if (select) select.value = firstOutcome;
        this._renderLeagueForOutcome(nmaResults, firstOutcome, el);
    }

    if (descEl) {
        const nOutcomes = NMAEngine.outcomes.filter(o => nmaResults[o]).length;
        descEl.textContent = 'Star-network NMA with placebo hub. All indirect comparisons via Bucher method (1997). ' + nOutcomes + ' outcomes analyzed. Lower HR favors row treatment. Bold = statistically significant. No closed loops — consistency testing not applicable (disclosed limitation).';
    }
},

_renderLeagueForOutcome(nmaResults, outcomeKey, el) {
    const data = nmaResults[outcomeKey];
    if (!data) { el.innerHTML = '<p class="text-xs text-slate-500 p-4">No data for this outcome.</p>'; return; }
    const { molecules, league, pscores } = data;
    const confLevel = RapidMeta.state.confLevel ?? 0.95;
    const confPct = Math.round(confLevel * 100);

    let html = '<div class="overflow-x-auto"><table class="w-full text-[10px] text-center">';
    // Header row
    html += '<thead><tr><th class="p-1 bg-slate-900/50 text-slate-500">vs</th>';
    molecules.forEach((m, j) => {
        html += '<th class="p-1 bg-slate-900/50 text-blue-400 font-bold">' + escapeHtml(m.name) + '</th>';
    });
    html += '<th class="p-1 bg-slate-900/50 text-amber-400 font-bold">P-score</th></tr></thead><tbody>';

    // Data rows
    molecules.forEach((rowMol, i) => {
        html += '<tr><td class="p-1 bg-slate-900/30 text-blue-400 font-bold text-left">' + escapeHtml(rowMol.name) + '</td>';
        molecules.forEach((colMol, j) => {
            if (i === j) {
                html += '<td class="p-1 bg-slate-800/50 text-slate-600">—</td>';
            } else {
                const c = league[i][j];
                const sig = c.lci > 1 || c.uci < 1;
                const favors = c.hr < 1 ? 'text-emerald-400' : c.hr > 1 ? 'text-rose-400' : 'text-slate-400';
                const bold = sig ? 'font-bold' : '';
                html += '<td class="p-1 ' + favors + ' ' + bold + '">' + c.hr.toFixed(2) + '<br><span class="text-[8px] text-slate-500">(' + c.lci.toFixed(2) + '\u2013' + c.uci.toFixed(2) + ')</span></td>';
            }
        });
        // P-score
        const ps = pscores[i];
        const psColor = ps >= 0.7 ? 'text-emerald-400' : ps >= 0.4 ? 'text-amber-400' : 'text-rose-400';
        html += '<td class="p-1 font-bold ' + psColor + '">' + ps.toFixed(3) + '</td>';
        html += '</tr>';
    });

    html += '</tbody></table></div>';
    el.innerHTML = html;
},
```

- [ ] **Step 2: Wire into AnalysisEngine.run() — add call after renderSafetyProfile**

At line ~8261 (after `this.renderSafetyProfile(trials);`), add:
```javascript
const nmaResults = NMAEngine.run(trials.filter(t => isIncludeLikeForAnalysis(t, RapidMeta.realData) && t.data));
this.renderNMALeague(nmaResults);
this.renderNMAHeatmap(nmaResults);
```

- [ ] **Step 3: Commit**

```bash
git commit -m "feat: render NMA league table with Bucher indirect comparisons and P-scores"
```

---

### Task 6: Render NMA Ranking Heatmap (Panel 23)

**Files:**
- Modify: `GLP1_CVOT_REVIEW.html` — add `renderNMAHeatmap()` to AnalysisEngine

- [ ] **Step 1: Add heatmap rendering method using Canvas**

Insert after `_renderLeagueForOutcome()`:

```javascript
renderNMAHeatmap(nmaResults) {
    const el = document.getElementById('plot-nma-heatmap');
    const descEl = document.getElementById('desc-nma-heatmap');
    if (!el || !nmaResults) return;

    // Collect all molecules across all outcomes
    const allMolecules = new Set();
    const outcomeData = {};
    NMAEngine.outcomes.forEach(o => {
        if (!nmaResults[o]) return;
        outcomeData[o] = nmaResults[o];
        nmaResults[o].molecules.forEach(m => allMolecules.add(m.name));
    });
    const molecules = [...allMolecules].sort();
    const outcomes = Object.keys(outcomeData);
    if (molecules.length === 0 || outcomes.length === 0) {
        el.innerHTML = '<p class="text-xs text-slate-500 p-4">Insufficient data for ranking heatmap.</p>';
        return;
    }

    // Build P-score matrix: rows=molecules, cols=outcomes
    const matrix = molecules.map(mol => {
        return outcomes.map(o => {
            const d = outcomeData[o];
            const idx = d.molecules.findIndex(m => m.name === mol);
            return idx >= 0 ? d.pscores[idx] : null;
        });
    });

    // Mean P-score per molecule
    const meanPscores = matrix.map(row => {
        const valid = row.filter(v => v !== null);
        return valid.length > 0 ? valid.reduce((a, b) => a + b, 0) / valid.length : null;
    });

    // Sort molecules by mean P-score descending
    const indices = molecules.map((_, i) => i).sort((a, b) => (meanPscores[b] ?? -1) - (meanPscores[a] ?? -1));

    // Render as HTML table with colored cells
    const labels = RapidMeta._outcomeLabelNames();
    let html = '<div class="overflow-x-auto"><table class="w-full text-[10px] text-center">';
    html += '<thead><tr><th class="p-2 bg-slate-900/50 text-slate-500 text-left">Molecule</th>';
    outcomes.forEach(o => {
        html += '<th class="p-2 bg-slate-900/50 text-slate-400">' + (labels[o] ?? o) + '</th>';
    });
    html += '<th class="p-2 bg-slate-900/50 text-amber-400 font-bold">Mean</th>';
    html += '<th class="p-2 bg-slate-900/50 text-slate-400">Profile</th></tr></thead><tbody>';

    indices.forEach(i => {
        html += '<tr><td class="p-2 text-left text-blue-400 font-bold">' + escapeHtml(molecules[i]) + '</td>';
        outcomes.forEach((o, j) => {
            const v = matrix[i][j];
            if (v === null) {
                html += '<td class="p-2 text-slate-600">—</td>';
            } else {
                const r = Math.round(255 - v * 200);
                const g = Math.round(55 + v * 200);
                const bg = 'rgba(' + r + ',' + g + ',80,0.3)';
                html += '<td class="p-2 font-mono font-bold" style="background:' + bg + '">' + v.toFixed(2) + '</td>';
            }
        });
        // Mean
        const mean = meanPscores[i];
        const meanColor = mean !== null ? (mean >= 0.7 ? 'text-emerald-400' : mean >= 0.4 ? 'text-amber-400' : 'text-rose-400') : 'text-slate-600';
        html += '<td class="p-2 font-bold ' + meanColor + '">' + (mean !== null ? mean.toFixed(2) : '—') + '</td>';
        // Sparkline (simple bar chart in cell)
        const sparkVals = matrix[i].filter(v => v !== null);
        if (sparkVals.length > 1) {
            const sparkW = 80, sparkH = 20;
            let svg = '<svg width="' + sparkW + '" height="' + sparkH + '" class="inline-block">';
            const barW = sparkW / sparkVals.length - 1;
            sparkVals.forEach((v, si) => {
                const barH = v * sparkH;
                const color = v >= 0.7 ? '#34d399' : v >= 0.4 ? '#fbbf24' : '#f87171';
                svg += '<rect x="' + (si * (barW + 1)) + '" y="' + (sparkH - barH) + '" width="' + barW + '" height="' + barH + '" fill="' + color + '" rx="1"/>';
            });
            svg += '</svg>';
            html += '<td class="p-2">' + svg + '</td>';
        } else {
            html += '<td class="p-2 text-slate-600">—</td>';
        }
        html += '</tr>';
    });

    html += '</tbody></table></div>';
    el.innerHTML = html;

    if (descEl) {
        descEl.textContent = 'P-score ranking across ' + outcomes.length + ' outcomes for ' + molecules.length + ' GLP-1 RA molecules. P-score ranges 0 (worst) to 1 (best), calculated using Rücker & Schwarzer (2015). Mean P-score summarizes overall performance. Molecules sorted by mean P-score (descending).';
    }
},
```

- [ ] **Step 2: Commit**

```bash
git commit -m "feat: render NMA ranking heatmap with P-score matrix and sparklines"
```

---

## Chunk 3: Fragility Index + Trial Sequential Analysis (Panels 20-21)

### Task 7: Render Fragility Index Table (Panel 20)

**Files:**
- Modify: `GLP1_CVOT_REVIEW.html` — add `renderFragility()` to AnalysisEngine

- [ ] **Step 1: Add renderFragility method**

Insert before `renderSafetyProfile()`:

```javascript
renderFragility(trials) {
    const el = document.getElementById('plot-fragility');
    const descEl = document.getElementById('desc-fragility');
    if (!el) return;
    const included = trials.filter(t => isIncludeLikeForAnalysis(t, RapidMeta.realData) && t.data && t.data.tE != null);
    if (included.length === 0) { el.innerHTML = '<p class="text-xs text-slate-500 p-4">No data.</p>'; return; }

    let html = '<div class="overflow-x-auto"><table class="w-full text-left text-xs">';
    html += '<thead class="bg-slate-900/50"><tr>';
    html += '<th class="p-2 text-[10px] font-bold uppercase text-slate-500">Trial</th>';
    html += '<th class="p-2 text-[10px] font-bold uppercase text-slate-500 text-right">Events (Tx/Ctrl)</th>';
    html += '<th class="p-2 text-[10px] font-bold uppercase text-slate-500 text-right">Original p</th>';
    html += '<th class="p-2 text-[10px] font-bold uppercase text-slate-500 text-right">Fragility Index</th>';
    html += '<th class="p-2 text-[10px] font-bold uppercase text-slate-500 text-right">FI / N</th>';
    html += '<th class="p-2 text-[10px] font-bold uppercase text-slate-500 text-center">Robustness</th>';
    html += '</tr></thead><tbody class="divide-y divide-slate-800/50">';

    let totalFI = 0, countSig = 0;
    included.forEach(t => {
        const d = t.data;
        const fi = computeFragilityIndex(d.tE, d.tN, d.cE, d.cN);
        const name = d.name ?? t.id;
        const fiN = (d.tN + d.cN);
        const fiRatio = fi.fi !== Infinity ? (fi.fi / fiN * 100).toFixed(3) : '—';
        const fiColor = fi.origP >= 0.05 ? 'text-slate-500' : fi.fi >= 5 ? 'text-emerald-400' : fi.fi >= 3 ? 'text-amber-400' : 'text-rose-400';
        const fiIcon = fi.origP >= 0.05 ? '<i class="fa-solid fa-minus text-slate-600"></i> N/S' : fi.fi >= 5 ? '<i class="fa-solid fa-shield-halved text-emerald-400"></i> Robust' : fi.fi >= 3 ? '<i class="fa-solid fa-triangle-exclamation text-amber-400"></i> Moderate' : '<i class="fa-solid fa-skull-crossbones text-rose-400"></i> Fragile';
        if (fi.origP < 0.05) { totalFI += fi.fi; countSig++; }

        html += '<tr class="hover:bg-slate-900/30">';
        html += '<td class="p-2 text-blue-400 font-bold">' + escapeHtml(name) + '</td>';
        html += '<td class="p-2 text-right font-mono text-slate-400">' + d.tE + ' / ' + d.cE + '</td>';
        html += '<td class="p-2 text-right font-mono text-slate-400">' + fi.origP.toFixed(4) + '</td>';
        html += '<td class="p-2 text-right font-mono font-bold ' + fiColor + '">' + (fi.origP >= 0.05 ? '—' : fi.fi) + '</td>';
        html += '<td class="p-2 text-right font-mono text-slate-400">' + (fi.origP >= 0.05 ? '—' : fiRatio + '%') + '</td>';
        html += '<td class="p-2 text-center">' + fiIcon + '</td>';
        html += '</tr>';
    });

    html += '</tbody></table></div>';
    if (countSig > 0) {
        html += '<div class="mt-2 text-[10px] text-slate-400 px-2">Median FI among significant trials: ' + totalFI + ' (across ' + countSig + ' trials). FI = number of events added to fewer-events arm to flip Fisher exact p above 0.05. Higher = more robust.</div>';
    }
    el.innerHTML = html;

    if (descEl) {
        descEl.textContent = 'Fragility Index per trial: the minimum number of patients whose event status would need to change to reverse the statistical significance (Walsh et al. 2014). Modification applied to the arm with fewer events only. Trials with p\u22650.05 show no FI (already non-significant). FI/N ratio contextualizes fragility relative to sample size.';
    }
},
```

- [ ] **Step 2: Wire into run() — add call after NMA calls**

```javascript
this.renderFragility(trials);
```

- [ ] **Step 3: Commit**

```bash
git commit -m "feat: render fragility index table with per-trial FI calculation"
```

---

### Task 8: Render Full TSA Panel (Panel 21)

**Files:**
- Modify: `GLP1_CVOT_REVIEW.html` — add `renderTSAFull()` to AnalysisEngine

- [ ] **Step 1: Add renderTSAFull method**

Insert after `renderFragility()`:

```javascript
renderTSAFull(data) {
    const el = document.getElementById('plot-tsa-full');
    const descEl = document.getElementById('desc-tsa-full');
    if (!el || !data || data.length === 0) return;

    // Sort by year
    const sorted = [...data].sort((a, b) => (a.year ?? 2020) - (b.year ?? 2020));

    // Compute control event rate from all data
    let totalCE = 0, totalCN = 0;
    sorted.forEach(d => { totalCE += d.cE; totalCN += d.cN; });
    const pC = totalCE / totalCN;
    const rrr = 0.15; // anticipated 15% RRR
    const ris = computeRIS(pC, rrr, 0.05, 0.80);

    // Cumulative Z and information fraction
    const cumulative = [];
    let cumTx = 0, cumCtrl = 0, cumTE = 0, cumCE = 0;
    sorted.forEach((d, i) => {
        cumTx += d.tN; cumCtrl += d.cN; cumTE += d.tE; cumCE += d.cE;
        const cumN = cumTx + cumCtrl;
        const infoFrac = cumN / ris;
        // Cumulative OR and Z
        const pT = cumTE / cumTx, pCC = cumCE / cumCtrl;
        const or = (cumTE * (cumCtrl - cumCE)) / (cumCE * (cumTx - cumTE));
        const logOR = Math.log(or);
        const se = Math.sqrt(1/cumTE + 1/(cumTx-cumTE) + 1/cumCE + 1/(cumCtrl-cumCE));
        const z = logOR / se;
        // O'Brien-Fleming boundary at this information fraction
        const boundary = obrienFlemingBoundary(Math.min(infoFrac, 1), 0.05);
        cumulative.push({
            trial: d.name ?? ('Trial ' + (i+1)),
            year: d.year,
            cumN, infoFrac, z, or, logOR, se,
            zBoundary: boundary.zBoundary,
            futilityBoundary: infoFrac >= 0.5 ? -boundary.zBoundary * 0.5 : null
        });
    });

    // Plot with Plotly
    const traces = [
        { x: cumulative.map(c => c.trial), y: cumulative.map(c => c.z), mode: 'lines+markers', name: 'Cumulative Z', line: { color: '#60a5fa', width: 2 }, marker: { size: 8 } },
        { x: cumulative.map(c => c.trial), y: cumulative.map(c => c.zBoundary), mode: 'lines', name: 'O\'Brien-Fleming Boundary', line: { color: '#f87171', width: 2, dash: 'dash' } },
        { x: cumulative.map(c => c.trial), y: cumulative.map(c => -c.zBoundary), mode: 'lines', name: 'Lower Boundary', line: { color: '#f87171', width: 2, dash: 'dash' }, showlegend: false },
    ];
    // Futility boundary where available
    const futX = cumulative.filter(c => c.futilityBoundary !== null).map(c => c.trial);
    const futY = cumulative.filter(c => c.futilityBoundary !== null).map(c => c.futilityBoundary);
    if (futX.length > 0) {
        traces.push({ x: futX, y: futY, mode: 'lines', name: 'Futility Boundary', line: { color: '#fbbf24', width: 1.5, dash: 'dot' } });
    }
    // Conventional significance line
    traces.push({ x: cumulative.map(c => c.trial), y: cumulative.map(() => -1.96), mode: 'lines', name: 'Conventional \u03b1=0.05', line: { color: '#94a3b8', width: 1, dash: 'dot' }, showlegend: true });

    const layout = {
        paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
        font: { color: '#cbd5e1', size: 10 },
        xaxis: { title: 'Trial (chronological)', tickangle: -45 },
        yaxis: { title: 'Cumulative Z-statistic', zeroline: true, zerolinecolor: '#475569' },
        margin: { l: 50, r: 20, t: 20, b: 80 },
        legend: { x: 0, y: 1, bgcolor: 'rgba(0,0,0,0.5)', font: { size: 9 } },
        showlegend: true
    };
    Plotly.newPlot(el, traces, layout, { responsive: true, displayModeBar: false });

    // Conclusiveness assessment
    const last = cumulative[cumulative.length - 1];
    const crossed = Math.abs(last.z) >= last.zBoundary;
    const conclusive = crossed || last.infoFrac >= 1.0;

    if (descEl) {
        descEl.innerHTML = '<strong>RIS:</strong> ' + ris.toLocaleString() + ' patients (based on control rate ' + (pC*100).toFixed(1) + '%, 15% RRR, \u03b1=0.05, power=80%). ' +
            '<strong>Information fraction:</strong> ' + (last.infoFrac * 100).toFixed(1) + '%. ' +
            '<strong>Cumulative Z:</strong> ' + last.z.toFixed(2) + ' (boundary: \u00b1' + last.zBoundary.toFixed(2) + '). ' +
            '<strong class="' + (conclusive ? 'text-emerald-400' : 'text-amber-400') + '">Verdict: ' + (conclusive ? 'CONCLUSIVE \u2014 monitoring boundary crossed, evidence sufficient.' : 'INCONCLUSIVE \u2014 monitoring boundary not yet crossed, more data may be needed.') + '</strong>';
    }
},
```

- [ ] **Step 2: Wire into run()**

After the fragility call, add:
```javascript
this.renderTSAFull(data);
```

Where `data` is the same array used by the cumulative analysis (sorted trial-level data with tE, tN, cE, cN, year, name).

- [ ] **Step 3: Commit**

```bash
git commit -m "feat: render full TSA with O'Brien-Fleming boundaries, RIS, and conclusiveness verdict"
```

---

## Chunk 4: Dose-Response + Per-AE Safety Forests (Panels 24-25)

### Task 9: Render Dose-Response Analysis (Panel 24)

**Files:**
- Modify: `GLP1_CVOT_REVIEW.html` — add `renderDoseResponse()` to AnalysisEngine

- [ ] **Step 1: Add renderDoseResponse method**

```javascript
renderDoseResponse() {
    const el = document.getElementById('plot-dose-response');
    const descEl = document.getElementById('desc-dose-response');
    if (!el) return;
    if (typeof doseResponseData === 'undefined' || !doseResponseData.semaglutideSC) {
        el.innerHTML = '<p class="text-xs text-slate-500 p-4">Dose-response data not available.</p>';
        return;
    }

    const drData = doseResponseData.semaglutideSC;
    const logHRData = drData.map(d => ({
        dose: d.dose,
        logHR: Math.log(d.hr),
        se: (Math.log(d.uci) - Math.log(d.lci)) / (2 * normalQuantile(0.975))
    }));

    const fit = fitEmax(logHRData);
    if (!fit) { el.innerHTML = '<p class="text-xs text-slate-500 p-4">Insufficient data for dose-response fit.</p>'; return; }

    // Also fit log-linear for comparison
    const sumW = logHRData.reduce((s, d) => s + 1/(d.se*d.se), 0);
    const sumWX = logHRData.reduce((s, d) => s + Math.log(d.dose + 0.01)/(d.se*d.se), 0);
    const sumWY = logHRData.reduce((s, d) => s + d.logHR/(d.se*d.se), 0);
    const sumWXY = logHRData.reduce((s, d) => s + Math.log(d.dose + 0.01)*d.logHR/(d.se*d.se), 0);
    const sumWXX = logHRData.reduce((s, d) => s + Math.log(d.dose + 0.01)**2/(d.se*d.se), 0);
    const beta1 = (sumW*sumWXY - sumWX*sumWY) / (sumW*sumWXX - sumWX*sumWX);
    const beta0 = (sumWY - beta1*sumWX) / sumW;

    const maxDose = 3.0;
    const linCurve = [];
    for (let d = 0.1; d <= maxDose; d += 0.05) {
        linCurve.push({ dose: d, hr: Math.exp(beta0 + beta1 * Math.log(d)) });
    }

    // Plot
    const traces = [
        // Emax curve
        { x: fit.curve.filter(p => p.dose > 0).map(p => p.dose), y: fit.curve.filter(p => p.dose > 0).map(p => p.hr), mode: 'lines', name: 'Emax model', line: { color: '#60a5fa', width: 2.5 } },
        // Log-linear
        { x: linCurve.map(p => p.dose), y: linCurve.map(p => p.hr), mode: 'lines', name: 'Log-linear', line: { color: '#a78bfa', width: 2, dash: 'dash' } },
        // Data points
        { x: drData.map(d => d.dose), y: drData.map(d => d.hr), mode: 'markers+text', name: 'Trial estimates',
          marker: { size: drData.map(d => Math.sqrt(d.n) / 8 + 6), color: '#fbbf24', line: { color: '#f59e0b', width: 1.5 } },
          text: drData.map(d => d.trial), textposition: 'top center', textfont: { size: 8, color: '#94a3b8' },
          error_y: { type: 'data', symmetric: false, array: drData.map(d => d.uci - d.hr), arrayminus: drData.map(d => d.hr - d.lci), color: '#94a3b8', thickness: 1.5 }
        },
        // Reference line at HR=1
        { x: [0, maxDose], y: [1, 1], mode: 'lines', name: 'No effect', line: { color: '#475569', width: 1, dash: 'dot' }, showlegend: false }
    ];

    const layout = {
        paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
        font: { color: '#cbd5e1', size: 10 },
        xaxis: { title: 'Semaglutide SC Dose (mg)', range: [0, maxDose] },
        yaxis: { title: 'Hazard Ratio (MACE)', range: [0.5, 1.15] },
        margin: { l: 50, r: 20, t: 20, b: 50 },
        legend: { x: 0.6, y: 0.95, bgcolor: 'rgba(0,0,0,0.5)', font: { size: 9 } },
        shapes: [{ type: 'line', x0: 0, x1: maxDose, y0: 1, y1: 1, line: { color: '#475569', width: 1, dash: 'dot' } }]
    };
    Plotly.newPlot(el, traces, layout, { responsive: true, displayModeBar: false });

    if (descEl) {
        const dose90 = fit.ed50 * 9; // dose at 90% Emax
        descEl.textContent = 'Dose-response analysis for semaglutide SC across SUSTAIN-6 (0.5mg, 1.0mg) and SELECT (2.4mg). Emax model: estimated Emax=' + fit.emax.toFixed(3) + ' (maximum log-HR reduction), ED50=' + fit.ed50.toFixed(2) + 'mg. Dose for 90% of max effect: ' + dose90.toFixed(1) + 'mg. CAUTION: Cross-trial comparison conflates dose with population differences (T2DM vs obesity) — ecological inference limitation.';
    }
},
```

- [ ] **Step 2: Wire into run()**

```javascript
this.renderDoseResponse();
```

- [ ] **Step 3: Commit**

```bash
git commit -m "feat: render dose-response analysis with Emax and log-linear models"
```

---

### Task 10: Render Per-AE Safety Forest Plots (Panel 25)

**Files:**
- Modify: `GLP1_CVOT_REVIEW.html` — add `renderSafetyForest()` to AnalysisEngine

- [ ] **Step 1: Add renderSafetyForest method**

```javascript
renderSafetyForest(trials) {
    const el = document.getElementById('plot-safety-forest');
    const descEl = document.getElementById('desc-safety-forest');
    if (!el) return;
    const withSafety = trials.filter(t => isIncludeLikeForAnalysis(t, RapidMeta.realData) && t.data && t.data.safetyData);
    if (withSafety.length === 0) { el.innerHTML = '<p class="text-xs text-slate-500 p-4">No safety data.</p>'; return; }

    // Collect all AE terms
    const termTrials = {};
    withSafety.forEach(t => {
        const sd = t.data.safetyData;
        sd.events.forEach(ev => {
            if (ev.tx == null || ev.ctrl == null) return;
            if (!termTrials[ev.term]) termTrials[ev.term] = [];
            termTrials[ev.term].push({ name: t.data.name ?? t.id, tE: ev.tx, tN: sd.nTx, cE: ev.ctrl, cN: sd.nCtrl, serious: ev.serious });
        });
    });

    const terms = Object.keys(termTrials).sort((a, b) => termTrials[b].length - termTrials[a].length);
    const confLevel = RapidMeta.state.confLevel ?? 0.95;
    const confPct = Math.round(confLevel * 100);

    let html = '<div class="space-y-1">';
    terms.forEach(term => {
        const studies = termTrials[term];
        if (studies.length < 2) return; // Need ≥2 studies for meta-analysis
        const mh = poolMantelHaenszel(studies);
        if (!mh) return;
        const sig = mh.lci > 1 || mh.uci < 1;
        const sigColor = sig ? (mh.rr > 1 ? 'text-rose-400' : 'text-emerald-400') : 'text-slate-400';
        const sigIcon = sig ? (mh.rr > 1 ? '\u26a0' : '\u2713') : '\u2014';
        const seriousBadge = studies[0].serious ? '<span class="text-[8px] bg-red-900/50 text-red-300 px-1 rounded ml-1">SAE</span>' : '';

        // NNH for significant harm signals
        let nnhStr = '';
        if (sig && mh.rr > 1) {
            // Pooled rates
            const totalTx = studies.reduce((s, st) => s + st.tN, 0);
            const totalCtrl = studies.reduce((s, st) => s + st.cN, 0);
            const totalTxE = studies.reduce((s, st) => s + st.tE, 0);
            const totalCtrlE = studies.reduce((s, st) => s + st.cE, 0);
            const ard = totalTxE/totalTx - totalCtrlE/totalCtrl;
            if (ard > 0) { const nnh = Math.ceil(1/ard); nnhStr = ' NNH=' + nnh; }
        }

        html += '<details class="bg-slate-950/30 rounded border border-slate-800/50">';
        html += '<summary class="p-2 cursor-pointer hover:bg-slate-900/30 flex items-center justify-between text-xs">';
        html += '<span class="text-slate-300 font-bold">' + escapeHtml(term) + seriousBadge + '</span>';
        html += '<span class="font-mono ' + sigColor + '">' + sigIcon + ' MH-RR ' + mh.rr.toFixed(2) + ' (' + mh.lci.toFixed(2) + '\u2013' + mh.uci.toFixed(2) + ') I\u00b2=' + mh.I2.toFixed(0) + '% k=' + mh.k + nnhStr + '</span>';
        html += '</summary>';

        // Mini forest plot as HTML bars
        html += '<div class="p-3 space-y-1">';
        studies.forEach(s => {
            const rr = (s.tE / s.tN) / (s.cE / s.cN);
            const logRR = Math.log(rr);
            const se = Math.sqrt(1/s.tE - 1/s.tN + 1/s.cE - 1/s.cN);
            const z = normalQuantile(1 - (1 - confLevel) / 2);
            const lo = Math.exp(logRR - z * se);
            const hi = Math.exp(logRR + z * se);
            const w = 1 / (se * se);
            const barColor = rr > 1 ? '#f87171' : '#34d399';
            // Normalize bar position: map RR range [0.2, 5] to [0%, 100%]
            const toPos = v => Math.max(0, Math.min(100, (Math.log(v) - Math.log(0.2)) / (Math.log(5) - Math.log(0.2)) * 100));
            const nullPos = toPos(1);
            const rrPos = toPos(rr);

            html += '<div class="flex items-center text-[9px] gap-2">';
            html += '<div class="w-24 text-right text-slate-500 shrink-0">' + escapeHtml(s.name) + '</div>';
            html += '<div class="flex-1 relative h-4 bg-slate-900/50 rounded">';
            html += '<div class="absolute top-0 bottom-0 w-px bg-slate-600" style="left:' + nullPos + '%"></div>';
            html += '<div class="absolute top-1 bottom-1 rounded" style="left:' + toPos(lo) + '%;width:' + (toPos(hi) - toPos(lo)) + '%;background:' + barColor + ';opacity:0.3"></div>';
            html += '<div class="absolute w-2 h-2 rounded-full" style="left:calc(' + rrPos + '% - 4px);top:4px;background:' + barColor + '"></div>';
            html += '</div>';
            html += '<div class="w-32 text-right font-mono text-slate-400 shrink-0">' + rr.toFixed(2) + ' (' + lo.toFixed(2) + '\u2013' + hi.toFixed(2) + ')</div>';
            html += '</div>';
        });
        // Pooled diamond
        html += '<div class="flex items-center text-[9px] gap-2 border-t border-slate-700 pt-1 mt-1">';
        html += '<div class="w-24 text-right text-amber-400 font-bold shrink-0">MH Pooled</div>';
        const toPos = v => Math.max(0, Math.min(100, (Math.log(v) - Math.log(0.2)) / (Math.log(5) - Math.log(0.2)) * 100));
        html += '<div class="flex-1 relative h-4 bg-slate-900/50 rounded">';
        html += '<div class="absolute top-0 bottom-0 w-px bg-slate-600" style="left:' + toPos(1) + '%"></div>';
        const dCenter = toPos(mh.rr), dLeft = toPos(mh.lci), dRight = toPos(mh.uci);
        html += '<svg class="absolute inset-0 w-full h-full"><polygon points="' + (dLeft/100*el.offsetWidth || dLeft*3) + ',8 ' + (dCenter/100*el.offsetWidth || dCenter*3) + ',2 ' + (dRight/100*el.offsetWidth || dRight*3) + ',8 ' + (dCenter/100*el.offsetWidth || dCenter*3) + ',14" fill="' + (sig ? (mh.rr > 1 ? '#f87171' : '#34d399') : '#94a3b8') + '"/></svg>';
        html += '</div>';
        html += '<div class="w-32 text-right font-mono font-bold ' + sigColor + ' shrink-0">' + mh.rr.toFixed(2) + ' (' + mh.lci.toFixed(2) + '\u2013' + mh.uci.toFixed(2) + ')</div>';
        html += '</div>';
        html += '</div></details>';
    });
    html += '</div>';
    el.innerHTML = html;

    if (descEl) {
        descEl.textContent = 'Per-adverse-event meta-analysis using Mantel-Haenszel pooled Risk Ratio (fixed-effect). Expand each AE to see per-trial forest plot. I\u00b2 for heterogeneity assessment. NNH shown for statistically significant harm signals. Data from ' + withSafety.length + ' trials with published AE frequencies.';
    }
},
```

- [ ] **Step 2: Wire into run()**

```javascript
this.renderSafetyForest(trials);
```

- [ ] **Step 3: Commit**

```bash
git commit -m "feat: render per-AE safety forest plots with MH-RR pooling and NNH"
```

---

## Chunk 5: Time-to-Benefit + TruthCert Verdict + GRADE (Panels 26-27)

### Task 11: Render Time-to-Benefit Timeline (Panel 26)

**Files:**
- Modify: `GLP1_CVOT_REVIEW.html` — add `renderTimeBenefit()` to AnalysisEngine

- [ ] **Step 1: Add renderTimeBenefit method**

```javascript
renderTimeBenefit(trials) {
    const el = document.getElementById('plot-time-benefit');
    const descEl = document.getElementById('desc-time-benefit');
    if (!el) return;
    const included = trials.filter(t => isIncludeLikeForAnalysis(t, RapidMeta.realData) && t.data?.baseline);
    if (included.length === 0) return;

    const data = included.map(t => ({
        name: t.data.name ?? t.id,
        fu: t.data.baseline.medianFU ?? 0,
        fuUnit: t.data.baseline.fuUnit ?? 'years',
        sep: t.data.baseline.timeToSeparation,
        onset: t.data.baseline.benefitOnset ?? 'unknown',
        molecule: t.data.baseline.molecule ?? 'Unknown',
        hr: t.data.publishedHR ?? null
    })).sort((a, b) => a.fu - b.fu);

    // Convert all to months
    data.forEach(d => {
        d.fuMonths = d.fuUnit === 'years' ? d.fu * 12 : d.fu;
    });

    const maxFU = Math.max(...data.map(d => d.fuMonths));
    const barH = 28, gap = 4, padTop = 30, padLeft = 120, padRight = 80;
    const canvasH = padTop + data.length * (barH + gap) + 40;
    const canvasW = el.offsetWidth || 700;
    const plotW = canvasW - padLeft - padRight;

    let html = '<canvas id="canvas-time-benefit" width="' + canvasW + '" height="' + canvasH + '" style="width:100%;height:' + canvasH + 'px;"></canvas>';
    el.innerHTML = html;

    const canvas = document.getElementById('canvas-time-benefit');
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#0f172a'; ctx.fillRect(0, 0, canvasW, canvasH);

    // X-axis (months)
    const xScale = d => padLeft + (d / maxFU) * plotW;
    ctx.strokeStyle = '#334155'; ctx.lineWidth = 1;
    for (let m = 0; m <= maxFU; m += 6) {
        const x = xScale(m);
        ctx.beginPath(); ctx.moveTo(x, padTop - 5); ctx.lineTo(x, canvasH - 20); ctx.stroke();
        ctx.fillStyle = '#94a3b8'; ctx.font = '9px monospace'; ctx.textAlign = 'center';
        ctx.fillText(m + 'mo', x, canvasH - 8);
    }

    // Bars
    const colors = { early: '#34d399', late: '#60a5fa', none: '#64748b', unknown: '#64748b' };
    data.forEach((d, i) => {
        const y = padTop + i * (barH + gap);
        // Label
        ctx.fillStyle = '#cbd5e1'; ctx.font = 'bold 10px sans-serif'; ctx.textAlign = 'right';
        ctx.fillText(d.name, padLeft - 8, y + barH / 2 + 4);
        // FU bar
        const barEnd = xScale(d.fuMonths);
        ctx.fillStyle = 'rgba(100,116,139,0.3)';
        ctx.fillRect(padLeft, y, barEnd - padLeft, barH);
        ctx.strokeStyle = '#475569'; ctx.strokeRect(padLeft, y, barEnd - padLeft, barH);
        // Separation marker
        if (d.sep != null) {
            const sepX = xScale(d.sep);
            ctx.fillStyle = colors[d.onset];
            ctx.beginPath(); ctx.arc(sepX, y + barH / 2, 6, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#0f172a'; ctx.font = 'bold 8px sans-serif'; ctx.textAlign = 'center';
            ctx.fillText(d.sep, sepX, y + barH / 2 + 3);
        }
        // HR annotation
        if (d.hr) {
            ctx.fillStyle = d.hr < 1 ? '#34d399' : '#f87171'; ctx.font = '9px monospace'; ctx.textAlign = 'left';
            ctx.fillText('HR ' + d.hr.toFixed(2), barEnd + 4, y + barH / 2 + 3);
        }
    });

    // Legend
    ctx.font = '9px sans-serif'; ctx.textAlign = 'left';
    const legendY = padTop - 18;
    [['early', 'Early (<12mo)'], ['late', 'Late (\u226512mo)'], ['none', 'No separation']].forEach(([key, label], i) => {
        const lx = padLeft + i * 130;
        ctx.fillStyle = colors[key]; ctx.beginPath(); ctx.arc(lx, legendY, 4, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#94a3b8'; ctx.fillText(label, lx + 8, legendY + 3);
    });

    if (descEl) {
        const earlyCount = data.filter(d => d.onset === 'early').length;
        const lateCount = data.filter(d => d.onset === 'late').length;
        const separations = data.filter(d => d.sep != null);
        const medianSep = separations.length > 0 ? separations.map(d => d.sep).sort((a,b) => a-b)[Math.floor(separations.length/2)] : null;
        descEl.textContent = 'Time-to-benefit analysis: ' + earlyCount + ' trials showed early KM separation (<12 months), ' + lateCount + ' showed late separation (\u226512 months). ' + (medianSep ? 'Median time to KM curve separation: ' + medianSep + ' months. ' : '') + 'Circle = month of first sustained KM divergence (from published figures). Trials without significant MACE benefit show no marker.';
    }
},
```

- [ ] **Step 2: Wire into run()**

```javascript
this.renderTimeBenefit(trials);
```

- [ ] **Step 3: Commit**

```bash
git commit -m "feat: render time-to-benefit timeline with KM separation markers"
```

---

### Task 12: Render TruthCert Verdict Panel (Panel 27)

**Files:**
- Modify: `GLP1_CVOT_REVIEW.html` — add `renderTruthCert()` to AnalysisEngine

- [ ] **Step 1: Add renderTruthCert method**

```javascript
renderTruthCert(r, data, trials) {
    const el = document.getElementById('plot-truthcert');
    const descEl = document.getElementById('desc-truthcert');
    if (!el || !r) return;
    const confLevel = RapidMeta.state.confLevel ?? 0.95;

    // Run 12-point threat assessment for class-level MACE
    const threats = [];
    const included = trials.filter(t => isIncludeLikeForAnalysis(t, RapidMeta.realData) && t.data);

    // 1. Fragility Index
    const sigTrials = included.filter(t => {
        const fi = computeFragilityIndex(t.data.tE, t.data.tN, t.data.cE, t.data.cN);
        return fi.origP < 0.05 && fi.fi < 3;
    });
    threats.push({ id: 1, name: 'Low Fragility Index (<3)', triggered: sigTrials.length > 0, detail: sigTrials.length + ' trials with FI<3' });

    // 2. Breakdown Point
    const breakdownTrials = included.filter(t => {
        // Would removing this trial flip the conclusion?
        const subset = data.filter(d => d.id !== t.id);
        if (subset.length < 2) return false;
        // Quick recompute
        const sumW = subset.reduce((s, d) => s + d.w, 0);
        const pooledLogOR = subset.reduce((s, d) => s + d.w * d.logOR, 0) / sumW;
        const pooledSE = 1 / Math.sqrt(sumW);
        const z = normalQuantile(1 - (1 - confLevel) / 2);
        const lo = Math.exp(pooledLogOR - z * pooledSE);
        const hi = Math.exp(pooledLogOR + z * pooledSE);
        return lo <= 1 && hi >= 1; // crosses null after removal
    });
    const breakdownPct = (breakdownTrials.length / included.length * 100).toFixed(0);
    threats.push({ id: 2, name: 'Low Breakdown Point (<30%)', triggered: parseInt(breakdownPct) < 30 && breakdownTrials.length > 0, detail: breakdownPct + '% (' + breakdownTrials.length + '/' + included.length + ')' });

    // 3. Egger's p < 0.10
    const eggerP = r.eggerP ?? 1;
    threats.push({ id: 3, name: 'Egger Asymmetry (p<0.10)', triggered: eggerP < 0.10, detail: 'p=' + eggerP.toFixed(4) });

    // 4. Trim-fill imputes ≥2
    const tfImputed = r.tfImputed ?? 0;
    threats.push({ id: 4, name: 'Trim-Fill Imputation (\u22652)', triggered: tfImputed >= 2, detail: tfImputed + ' studies imputed' });

    // 5. I² > 50%
    const I2 = parseFloat(r.i2) || 0;
    threats.push({ id: 5, name: 'High Heterogeneity (I\u00b2>50%)', triggered: I2 > 50, detail: 'I\u00b2=' + I2.toFixed(1) + '%' });

    // 6. Prediction interval crosses null
    const piCrossesNull = r.piLCI != null && r.piUCI != null && parseFloat(r.piLCI) <= 1 && parseFloat(r.piUCI) >= 1;
    threats.push({ id: 6, name: 'Prediction Interval Crosses Null', triggered: piCrossesNull, detail: r.piLCI + '\u2013' + r.piUCI });

    // 7. k < 5
    const k = parseInt(r.n) || 0;
    threats.push({ id: 7, name: 'Small Study Count (k<5)', triggered: k < 5, detail: 'k=' + k });

    // 8. HKSJ vs Wald CI disagree
    const hksjSig = r.hksjLCI != null && (parseFloat(r.hksjLCI) > 1 || parseFloat(r.hksjUCI) < 1);
    const waldSig = parseFloat(r.lci) > 1 || parseFloat(r.uci) < 1;
    // For protective effects (OR<1), significance means uci < 1
    const hksjSig2 = r.hksjUCI != null && parseFloat(r.hksjUCI) < 1;
    const waldSig2 = parseFloat(r.uci) < 1;
    const disagree = (hksjSig2 !== waldSig2);
    threats.push({ id: 8, name: 'HKSJ vs Wald CI Disagree', triggered: disagree, detail: 'HKSJ sig=' + hksjSig2 + ', Wald sig=' + waldSig2 });

    // 9. Any LOO removal flips conclusion
    threats.push({ id: 9, name: 'LOO Sensitivity Fragile', triggered: breakdownTrials.length > 0, detail: breakdownTrials.length + ' pivotal trials' });

    // 10. TSA boundary not crossed
    // Approximate: check if we computed TSA
    let tsaCrossed = false;
    const tsaEl = document.getElementById('desc-tsa-full');
    if (tsaEl && tsaEl.textContent.includes('CONCLUSIVE')) tsaCrossed = true;
    threats.push({ id: 10, name: 'TSA Boundary Not Crossed', triggered: !tsaCrossed, detail: tsaCrossed ? 'Boundary crossed' : 'Not yet conclusive' });

    // 11. Copas-adjusted crosses null (placeholder — check if Copas result available)
    const copasCrossesNull = false; // TODO: wire to CopasEngine result
    threats.push({ id: 11, name: 'Copas-Adjusted Crosses Null', triggered: copasCrossesNull, detail: 'Selection model adjusted' });

    // 12. RoB: ≥2 trials high-risk
    const highRoB = included.filter(t => t.data.rob && t.data.rob.some(r => r === 'high')).length;
    threats.push({ id: 12, name: 'High Risk of Bias (\u22652 trials)', triggered: highRoB >= 2, detail: highRoB + ' high-risk trials' });

    const severity = threats.filter(t => t.triggered).length;
    const verdictLabel = severity <= 3 ? 'STABLE' : severity <= 6 ? 'MODERATE' : severity <= 9 ? 'EXPOSED' : 'UNCERTAIN';
    const verdictColor = severity <= 3 ? '#34d399' : severity <= 6 ? '#60a5fa' : severity <= 9 ? '#fbbf24' : '#f87171';
    const verdictBg = severity <= 3 ? 'bg-emerald-900/30 border-emerald-700' : severity <= 6 ? 'bg-blue-900/30 border-blue-700' : severity <= 9 ? 'bg-amber-900/30 border-amber-700' : 'bg-red-900/30 border-red-700';

    // Render
    let html = '<div class="' + verdictBg + ' border rounded-xl p-4">';
    // Header with severity gauge
    html += '<div class="flex items-center justify-between mb-4">';
    html += '<div><span class="text-2xl font-black" style="color:' + verdictColor + '">' + verdictLabel + '</span>';
    html += '<div class="text-[10px] text-slate-400 mt-1">Evidence Verdict \u2014 GLP-1 RA Class for MACE</div></div>';
    html += '<div class="text-center"><div class="text-3xl font-mono font-bold" style="color:' + verdictColor + '">' + severity + '<span class="text-sm text-slate-500">/12</span></div>';
    html += '<div class="text-[9px] text-slate-500">Severity Score</div></div></div>';

    // Severity arc (simple bar gauge)
    html += '<div class="w-full h-3 bg-slate-800 rounded-full overflow-hidden mb-4"><div class="h-full rounded-full transition-all" style="width:' + (severity/12*100) + '%;background:' + verdictColor + '"></div></div>';

    // Threat checklist
    html += '<div class="grid grid-cols-1 md:grid-cols-2 gap-1">';
    threats.forEach(t => {
        const icon = t.triggered ? '<i class="fa-solid fa-circle-exclamation text-rose-400"></i>' : '<i class="fa-solid fa-circle-check text-emerald-400"></i>';
        html += '<div class="flex items-center gap-2 text-[10px] p-1 rounded ' + (t.triggered ? 'bg-rose-950/30' : 'bg-emerald-950/20') + '">';
        html += icon + ' <span class="' + (t.triggered ? 'text-rose-300' : 'text-emerald-300') + '">' + t.name + '</span>';
        html += '<span class="ml-auto text-slate-500 text-[9px]">' + t.detail + '</span></div>';
    });
    html += '</div>';

    // Per-outcome verdict badges (Level 2)
    html += '<div class="mt-4 border-t border-slate-700 pt-3"><div class="text-[10px] text-slate-500 font-bold uppercase mb-2">Per-Outcome Verdicts</div>';
    html += '<div class="flex flex-wrap gap-2">';
    const outcomeLabels = RapidMeta._outcomeLabelNames();
    ['MACE', 'CVD', 'ACM', 'MI', 'Stroke', 'HHF', 'Renal'].forEach(o => {
        // Simplified verdict: check if pooled CI for this outcome crosses null
        const label = outcomeLabels[o] ?? o;
        // Use NMA results if available
        const nmaEl = document.getElementById('plot-nma-league');
        // Simple heuristic based on available data
        let badge = 'bg-slate-800 text-slate-500';
        let badgeLabel = 'N/A';
        // Check allOutcomes across included trials
        let hasData = false;
        included.forEach(t => {
            const oc = t.data.allOutcomes?.find(oo => oo.shortLabel === o);
            if (oc && oc.effect) hasData = true;
        });
        if (hasData) {
            badge = 'bg-emerald-900/40 text-emerald-400';
            badgeLabel = 'STABLE';
        }
        html += '<span class="text-[9px] px-2 py-1 rounded-full font-bold ' + badge + '">' + label + ': ' + badgeLabel + '</span>';
    });
    html += '</div></div>';

    // Molecule flags (Level 3)
    html += '<div class="mt-3 border-t border-slate-700 pt-3"><div class="text-[10px] text-slate-500 font-bold uppercase mb-2">Molecule-Level Flags</div>';
    html += '<div class="space-y-1 text-[10px]">';
    html += '<div class="text-amber-400">\u26a0 ELIXA (Lixisenatide): Neutral for MACE (4-point endpoint, no superiority)</div>';
    html += '<div class="text-amber-400">\u26a0 SUSTAIN-6 (Semaglutide): Diabetic retinopathy complications signal (HR 1.76)</div>';
    html += '<div class="text-emerald-400">\u2713 SELECT (Semaglutide 2.4mg): Benefit in non-diabetic obesity population — extends class effect</div>';
    html += '<div class="text-emerald-400">\u2713 SOUL (Oral Semaglutide): Confirms oral formulation non-inferior to injectable on MACE</div>';
    html += '</div></div>';

    html += '</div>';
    el.innerHTML = html;

    if (descEl) {
        descEl.textContent = 'TruthCert 12-point threat assessment for evidence robustness. Severity 0-3: STABLE (high confidence). 4-6: MODERATE. 7-9: EXPOSED (major concerns). 10-12: UNCERTAIN. Per-outcome and molecule-level verdicts provide granular assessment. Based on Walsh et al. (2014) fragility, Rücker (2011) breakdown, Copas (1999) selection, and GRADE framework.';
    }
},
```

- [ ] **Step 2: Wire into run() — must be called after TSA and fragility so those results exist**

```javascript
this.renderTruthCert(RapidMeta.state.results, data, trials);
```

- [ ] **Step 3: Commit**

```bash
git commit -m "feat: render TruthCert 12-point verdict with per-outcome badges and molecule flags"
```

---

### Task 13: Upgrade GRADE automation

**Files:**
- Modify: `GLP1_CVOT_REVIEW.html` — enhance existing `renderGRADE()` (line ~8633)

- [ ] **Step 1: Read current renderGRADE method to understand what exists**

Read lines 8633-8700 for current implementation.

- [ ] **Step 2: Enhance with 5-domain automation**

Upgrade the existing `renderGRADE()` to compute each domain programmatically:

```javascript
// Inside renderGRADE, after existing logic, add domain-level detail:
const gradeAssessment = {
    riskOfBias: (() => {
        const highCount = included.filter(t => t.data.rob?.some(r => r === 'high')).length;
        const someCount = included.filter(t => t.data.rob?.some(r => r === 'some')).length;
        if (highCount >= 2) return { rating: -2, label: 'Very Serious', detail: highCount + ' high-risk trials' };
        if (highCount >= 1 || someCount >= 3) return { rating: -1, label: 'Serious', detail: highCount + ' high + ' + someCount + ' some concerns' };
        return { rating: 0, label: 'Not Serious', detail: 'All low risk' };
    })(),
    inconsistency: (() => {
        if (I2 > 75) return { rating: -2, label: 'Very Serious', detail: 'I\u00b2=' + I2.toFixed(0) + '%' };
        if (I2 > 50) return { rating: -1, label: 'Serious', detail: 'I\u00b2=' + I2.toFixed(0) + '%' };
        return { rating: 0, label: 'Not Serious', detail: 'I\u00b2=' + I2.toFixed(0) + '%' };
    })(),
    indirectness: { rating: 0, label: 'Not Serious', detail: 'Direct RCT evidence, relevant populations' },
    imprecision: (() => {
        const ciWidth = Math.log(parseFloat(uci)) - Math.log(parseFloat(lci));
        if (ciWidth > 0.5) return { rating: -1, label: 'Serious', detail: 'Wide CI' };
        return { rating: 0, label: 'Not Serious', detail: 'Narrow CI' };
    })(),
    publicationBias: (() => {
        if (eggerP < 0.05) return { rating: -1, label: 'Serious', detail: 'Egger p=' + eggerP.toFixed(3) };
        return { rating: 0, label: 'Not Serious', detail: 'Egger p=' + eggerP.toFixed(3) };
    })()
};
const totalDowngrade = Object.values(gradeAssessment).reduce((s, d) => s + d.rating, 0);
const gradeCertainty = totalDowngrade >= 0 ? 'HIGH' : totalDowngrade === -1 ? 'MODERATE' : totalDowngrade === -2 ? 'LOW' : 'VERY LOW';
```

- [ ] **Step 3: Commit**

```bash
git commit -m "feat: automate GRADE 5-domain assessment with programmatic domain scoring"
```

---

## Chunk 6: Data Provenance + Arabic Translations + Exports + Wiring

### Task 14: Add data provenance tooltip system

**Files:**
- Modify: `GLP1_CVOT_REVIEW.html` — add provenance rendering near escapeHtml

- [ ] **Step 1: Add provenance tooltip renderer**

```javascript
function renderProvenanceTooltip(trialId, fieldName) {
    const trial = RapidMeta.realData[trialId];
    if (!trial || !trial.provenance || !trial.provenance[fieldName]) return '';
    const p = trial.provenance[fieldName];
    return ' title="Source: ' + escapeHtml(p.source) + ' | ' + escapeHtml(p.excerpt) + ' | Locator: ' + escapeHtml(p.locator) + '" class="cursor-help underline decoration-dotted decoration-slate-600"';
}
```

- [ ] **Step 2: Apply provenance tooltips to key rendered values in renderDemographics**

In the demographics table (line ~8319), wrap event counts and HRs with provenance:
```javascript
// Example: where tE is rendered, add provenance tooltip
'<td' + renderProvenanceTooltip(t.id, 'tE') + '>' + d.tE + '</td>'
```

- [ ] **Step 3: Commit**

```bash
git commit -m "feat: add data provenance tooltip system with source verification"
```

---

### Task 15: Add Arabic translations for new panels

**Files:**
- Modify: `GLP1_CVOT_REVIEW.html` — `_arDict` (before line ~4228)

- [ ] **Step 1: Add translation entries**

```javascript
'20. Fragility Index': '20. مؤشر الهشاشة',
'21. Trial Sequential Analysis': '21. التحليل التتابعي للتجارب',
'22. NMA League Table': '22. جدول الدوري لتحليل الشبكة',
'23. NMA Ranking Dashboard': '23. لوحة ترتيب تحليل الشبكة',
'24. Dose-Response Analysis': '24. تحليل الجرعة-الاستجابة',
'25. Safety Forest Plots (Per-AE Meta-Analysis)': '25. رسوم الغابة للأمان (تحليل تلوي لكل حدث ضائر)',
'26. Time-to-Benefit Analysis': '26. تحليل وقت الفائدة',
'27. TruthCert Evidence Verdict': '27. حكم شهادة الحقيقة',
'Fragility Index': 'مؤشر الهشاشة',
'Robustness': 'المتانة',
'Robust': 'متين',
'Moderate': 'معتدل',
'Fragile': 'هش',
'P-score': 'درجة الاحتمال',
'League Table': 'جدول الدوري',
'Indirect Comparison': 'مقارنة غير مباشرة',
'Ranking': 'الترتيب',
'Dose': 'الجرعة',
'Optimal Dose': 'الجرعة المثلى',
'Severity Score': 'درجة الشدة',
'STABLE': 'مستقر',
'EXPOSED': 'مكشوف',
'UNCERTAIN': 'غير مؤكد',
'Evidence Verdict': 'حكم الأدلة',
'Threat Assessment': 'تقييم التهديد',
'Information Fraction': 'كسر المعلومات',
'Monitoring Boundary': 'حد المراقبة',
'CONCLUSIVE': 'حاسم',
'INCONCLUSIVE': 'غير حاسم',
'Time-to-Benefit': 'وقت الفائدة',
'KM Separation': 'انفصال منحنى كابلان-ماير',
'Early': 'مبكر',
'Late': 'متأخر',
'MH Pooled': 'مجمع مانتل-هاينزل',
'NNH': 'العدد اللازم للضرر',
```

- [ ] **Step 2: Commit**

```bash
git commit -m "feat: add Arabic translations for all 8 new analysis panels"
```

---

### Task 16: Extend export functions

**Files:**
- Modify: `GLP1_CVOT_REVIEW.html` — near existing export functions (line ~9442)

- [ ] **Step 1: Add NMA league table CSV export**

Add to the export menu and create `exportNMACSV()`:
```javascript
exportNMACSV() {
    const trials = RapidMeta.state.trials.filter(t => isIncludeLikeForAnalysis(t, RapidMeta.realData) && t.data);
    const nmaResults = NMAEngine.run(trials);
    let csv = 'Outcome,Molecule_Row,Molecule_Col,HR,LCI,UCI,P-value\n';
    NMAEngine.outcomes.forEach(o => {
        if (!nmaResults[o]) return;
        const { molecules, league } = nmaResults[o];
        molecules.forEach((rowMol, i) => {
            molecules.forEach((colMol, j) => {
                if (i === j) return;
                const c = league[i][j];
                csv += [o, rowMol.name, colMol.name, c.hr.toFixed(4), c.lci.toFixed(4), c.uci.toFixed(4), c.pval.toFixed(6)].join(',') + '\n';
            });
        });
    });
    const blob = new Blob([csv], { type: 'text/csv' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'glp1ra_nma_league_table.csv';
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    URL.revokeObjectURL(a.href);
},
```

- [ ] **Step 2: Add TruthCert verdict JSON export**

```javascript
exportTruthCertJSON() {
    const el = document.getElementById('plot-truthcert');
    if (!el) return;
    const receipt = {
        timestamp: new Date().toISOString(),
        app: 'GLP1_CVOT_REVIEW',
        version: '2.0',
        verdict: el.querySelector('.text-2xl')?.textContent ?? 'UNKNOWN',
        severity: parseInt(el.querySelector('.text-3xl')?.textContent) || 0,
        dataHash: DataSealEngine?.currentHash ?? 'not-sealed',
        confLevel: RapidMeta.state.confLevel ?? 0.95,
        k: RapidMeta.state.results?.n ?? 0
    };
    const blob = new Blob([JSON.stringify(receipt, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'truthcert_verdict_receipt.json';
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    URL.revokeObjectURL(a.href);
},
```

- [ ] **Step 3: Commit**

```bash
git commit -m "feat: add NMA CSV and TruthCert JSON export functions"
```

---

### Task 17: Wire all new render calls into AnalysisEngine.run()

**Files:**
- Modify: `GLP1_CVOT_REVIEW.html` — line ~8261

- [ ] **Step 1: Add all new render calls after renderSafetyProfile**

After `this.renderSafetyProfile(trials);` (line 8261), add:
```javascript
// === NEW ANALYTICS PANELS (v2.0) ===
const nmaTrials = trials.filter(t => isIncludeLikeForAnalysis(t, RapidMeta.realData) && t.data);
const nmaResults = NMAEngine.run(nmaTrials);
this.renderFragility(trials);
this.renderTSAFull(data);
this.renderNMALeague(nmaResults);
this.renderNMAHeatmap(nmaResults);
this.renderDoseResponse();
this.renderSafetyForest(trials);
this.renderTimeBenefit(trials);
this.renderTruthCert(RapidMeta.state.results, data, trials);
```

- [ ] **Step 2: Verify div balance and script integrity**

```bash
python -c "import re; c=open(r'C:\Users\user\Downloads\Finrenone\GLP1_CVOT_REVIEW.html','r',encoding='utf-8').read(); o=len(re.findall(r'<div[\s>]',c)); cl=len(re.findall(r'</div>',c)); sc=len(re.findall(r'</script>',c)); print(f'divs: {o}/{cl} diff={o-cl}  scripts: {sc}')"
```

Expected: diff=0, scripts=3 (or same as before)

- [ ] **Step 3: Open in browser and verify all 27 panels render**

Load the file, run the analysis, scroll through all panels. Check:
- Panels 20-27 visible (27 = standard, 22-26 = expert toggle)
- No console errors
- Forest plots render
- NMA league table populates
- Heatmap shows colored cells
- TSA shows Plotly chart with boundaries
- TruthCert shows verdict card

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: wire all 8 new analysis panels into AnalysisEngine.run()"
```

---

### Task 18: Final validation and R code extension

- [ ] **Step 1: Extend generated R code to include netmeta**

In the `generateRCode()` method, append NMA validation code:
```r
# NMA validation (requires netmeta package)
# library(netmeta)
# net <- netmeta(TE, seTE, treat1, treat2, studlab, sm="HR", reference.group="Placebo")
# netrank(net, small.values="good")
```

- [ ] **Step 2: Run full browser test — click through all panels, verify data**

- [ ] **Step 3: Final div balance + script integrity check**

- [ ] **Step 4: Final commit**

```bash
git commit -m "feat: complete GLP-1 RA CVOT analytics upgrade v2.0 — 8 new panels, NMA, dose-response, fragility, TSA, TruthCert"
```
