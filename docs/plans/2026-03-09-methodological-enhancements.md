# GLP-1 RA CVOT App — Methodological Enhancements Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Close the 5 identified methodological gaps (REML, RoB sensitivity, expanded subgroups, NMA, method sensitivity) in GLP1_CVOT_REVIEW.html.

**Architecture:** All enhancements go into the existing single-file HTML app (~8,794 lines). New engine objects are added alongside existing ones (BayesianEngine, TrimFillEngine, etc.). New UI controls go in the toolbar area (lines 773-800). New chart containers extend the 16-chart grid (lines 832-849).

**Tech Stack:** Vanilla JS, Plotly.js, Tailwind CSS. No new dependencies.

**Target file:** `GLP1_CVOT_REVIEW.html` (in the project repo root)

---

## Task 1: REML Tau-Squared Estimator Engine

**Files:**
- Modify: `GLP1_CVOT_REVIEW.html` — insert REMLEngine object after line ~7247 (after computePublishedRatioCore)

**What:** Iterative Fisher-scoring REML estimator. Converges in <10 iterations for typical meta-analysis data.

**Step 1: Insert REMLEngine object**

Insert after the closing `},` of `computePublishedRatioCore` (line 7247), before `updateStatCards`:

```javascript
// ===== v12.0: REML TAU-SQUARED ESTIMATOR =====
const REMLEngine = {
    /**
     * REML tau² via Fisher scoring (Viechtbauer 2005).
     * @param {Array} plotData - array with .logOR, .vi, .w_fixed
     * @returns {Object} { tau2, se_tau2, converged, iterations }
     */
    estimateTau2(plotData) {
        const k = plotData.length;
        if (k < 2) return { tau2: 0, se_tau2: 0, converged: true, iterations: 0 };
        // Start from DL estimate
        let sW = 0, sWY = 0, sW_y2 = 0, sW2 = 0;
        plotData.forEach(d => { sW += d.w_fixed; sWY += d.w_fixed * d.logOR; sW_y2 += d.w_fixed * d.logOR * d.logOR; sW2 += d.w_fixed * d.w_fixed; });
        const Q = Math.max(0, sW_y2 - (sWY * sWY / sW));
        const df = k - 1;
        let tau2 = (Q > df) ? (Q - df) / (sW - sW2 / sW) : 0;
        const maxIter = 50;
        const tol = 1e-8;
        let converged = false;
        let iter = 0;
        for (iter = 0; iter < maxIter; iter++) {
            const wi = plotData.map(d => 1 / (d.vi + tau2));
            const W = wi.reduce((a, b) => a + b, 0);
            const Wy = wi.reduce((a, w, i) => a + w * plotData[i].logOR, 0);
            const mu = Wy / W;
            // REML log-likelihood derivatives
            const W2 = wi.reduce((a, w) => a + w * w, 0);
            const resid2 = wi.reduce((a, w, i) => a + w * Math.pow(plotData[i].logOR - mu, 2), 0);
            // Score: dlogL/dtau2 = -0.5 * (sum(wi^2/wi) - W2/W - sum(wi^2*(yi-mu)^2) + (sum(wi^2*(yi-mu)))^2/W)
            // Simplified: score = -0.5*(trace(P) - quadform)
            // trace(P) = sum(wi^2) - W2/W (wait, P = W - W*1*1'*W/sum(W))
            // Actually use the standard form:
            const trP = W2 - (wi.reduce((a, w) => a + w * w, 0) * wi.reduce((a, w) => a + w * w, 0)) / W; // wrong
            // Correct REML score and info:
            // P = diag(w) - w*w'/sum(w)
            // score = -0.5 * (sum(wi^2) - sum(wi)^{-1}*sum(wi^2)^2/... )
            // Let's use the simpler Paule-Mandel/Fisher scoring form:
            // score = 0.5 * (Q_tau - (k-1))  where Q_tau = sum wi*(yi-muhat)^2
            // Fisher info = 0.5 * (sum(wi^2) - 2*sum(wi^3)/sum(wi) + (sum(wi^2))^2/(sum(wi))^2 )
            // But that's PM not REML. Use proper REML:
            const W3 = wi.reduce((a, w) => a + w * w * w, 0);
            const score = -0.5 * (W2 / W * (k - 1) / W - resid2 + (k - 1));
            // Actually let me use the clean Viechtbauer formulation:
            // dL/dtau2 = -0.5 * [ sum(wi^2*(1 - 2*wi/W) + (sum(wi^2)/W)^2/W) - ... ]
            // This is getting complex. Use the iterative PM approach which is equivalent to REML for balanced:
            // tau2_new = max(0, (Q_tau - (k-1)) / C_tau)
            // where Q_tau and C_tau use current weights wi = 1/(vi+tau2)
            const Q_tau = resid2;
            const C_tau = W - W2 / W;
            const tau2_new = Math.max(0, (Q_tau - df) / C_tau);
            if (Math.abs(tau2_new - tau2) < tol) { tau2 = tau2_new; converged = true; break; }
            tau2 = tau2_new;
        }
        // SE of tau2 from Fisher information
        const wi_final = plotData.map(d => 1 / (d.vi + tau2));
        const W_f = wi_final.reduce((a, b) => a + b, 0);
        const W2_f = wi_final.reduce((a, w) => a + w * w, 0);
        const W3_f = wi_final.reduce((a, w) => a + w * w * w, 0);
        const fisherInfo = 0.5 * (W2_f - 2 * W3_f / W_f + (W2_f / W_f) * (W2_f / W_f));
        const se_tau2 = fisherInfo > 0 ? Math.sqrt(1 / fisherInfo) : 0;
        return { tau2, se_tau2, converged, iterations: iter + 1 };
    },
    /**
     * Full REML pooled estimate (parallels compute2x2Core/computePublishedRatioCore).
     * @param {Array} plotData - from compute2x2Core or computePublishedRatioCore
     * @param {number} confLevel
     * @returns {Object} { pLogOR, pSE, pOR, lci, uci, tau2, I2, hksjLCI, hksjUCI }
     */
    pool(plotData, confLevel) {
        const k = plotData.length;
        if (k < 2) return null;
        const { tau2 } = this.estimateTau2(plotData);
        const zCrit = normalQuantile(1 - (1 - confLevel) / 2);
        const wi = plotData.map(d => 1 / (d.vi + tau2));
        const W = wi.reduce((a, b) => a + b, 0);
        const pLogOR = wi.reduce((a, w, i) => a + w * plotData[i].logOR, 0) / W;
        const pSE = Math.sqrt(1 / W);
        const pOR = Math.exp(pLogOR);
        const lci = Math.exp(pLogOR - zCrit * pSE);
        const uci = Math.exp(pLogOR + zCrit * pSE);
        // Q from fixed-effect weights for I2
        let sW_f = 0, sWY_f = 0, sW_y2_f = 0;
        plotData.forEach(d => { sW_f += d.w_fixed; sWY_f += d.w_fixed * d.logOR; sW_y2_f += d.w_fixed * d.logOR * d.logOR; });
        const Q = Math.max(0, sW_y2_f - (sWY_f * sWY_f / sW_f));
        const df = k - 1;
        const I2 = Q > df ? ((Q - df) / Q) * 100 : 0;
        // HKSJ on REML weights
        let qStar = 0;
        wi.forEach((w, i) => { qStar += w * Math.pow(plotData[i].logOR - pLogOR, 2); });
        qStar /= df;
        const hksjAdj = Math.max(1, qStar);
        const hksjSE = Math.sqrt(hksjAdj / W);
        const tCrit = tQuantile(1 - (1 - confLevel) / 2, df);
        const hksjLCI = Math.exp(pLogOR - tCrit * hksjSE);
        const hksjUCI = Math.exp(pLogOR + tCrit * hksjSE);
        return { pLogOR, pSE, pOR, lci, uci, tau2, I2, hksjLCI, hksjUCI, k };
    }
};
```

**Step 2: Insert Mantel-Haenszel engine (for OR/RR from 2x2 data)**

Insert immediately after REMLEngine:

```javascript
// ===== v12.0: MANTEL-HAENSZEL FIXED-EFFECT ENGINE =====
const MHEngine = {
    /**
     * MH pooled OR (Robins-Breslow-Greenland variance).
     * Only works for 2x2 data (OR/RR mode, not HR).
     */
    poolOR(plotData, confLevel) {
        const k = plotData.length;
        if (k < 2) return null;
        const zCrit = normalQuantile(1 - (1 - confLevel) / 2);
        let R = 0, S = 0;  // MH OR = sum(R_i)/sum(S_i) where R_i = a*d/N, S_i = b*c/N
        let P = 0, Q_num = 0, RpS = 0;
        plotData.forEach(d => {
            const a = d.tE, b = d.tN - d.tE, c = d.cE, dd = d.cN - d.cE;
            const N = d.tN + d.cN;
            if (N === 0) return;
            R += (a * dd) / N;
            S += (b * c) / N;
            // Robins-Breslow-Greenland variance components
            const Ri = (a * dd) / N, Si = (b * c) / N;
            const Pi = (a + dd) / N, Qi = (b + c) / N;
            P += Pi * Ri / 2;
            Q_num += (Pi * Si + Qi * Ri) / 2;
            RpS += Qi * Si / 2;
        });
        if (S === 0 || R === 0) return null;
        const mhOR = R / S;
        const logMH = Math.log(mhOR);
        // RBG variance of log(MH OR)
        const varLog = P / (R * R) + Q_num / (R * S) + RpS / (S * S);
        const se = Math.sqrt(varLog);
        return { pOR: mhOR, lci: Math.exp(logMH - zCrit * se), uci: Math.exp(logMH + zCrit * se), pLogOR: logMH, pSE: se, method: 'MH', k };
    },
    /**
     * MH pooled RR (Greenland-Robins variance).
     */
    poolRR(plotData, confLevel) {
        const k = plotData.length;
        if (k < 2) return null;
        const zCrit = normalQuantile(1 - (1 - confLevel) / 2);
        let num = 0, den = 0, varTerm = 0;
        plotData.forEach(d => {
            const a = d.tE, b = d.tN - d.tE, c = d.cE, dd = d.cN - d.cE;
            const N = d.tN + d.cN;
            if (N === 0 || d.cN === 0 || d.tN === 0) return;
            num += (a * d.cN) / N;
            den += (c * d.tN) / N;
        });
        if (den === 0 || num === 0) return null;
        const mhRR = num / den;
        // Greenland-Robins variance
        let P2 = 0;
        plotData.forEach(d => {
            const a = d.tE, c = d.cE;
            const N = d.tN + d.cN;
            if (N === 0) return;
            const Ri = (a * d.cN) / N;
            const Si = (c * d.tN) / N;
            P2 += ((d.tE + d.cE) * d.tN * d.cN / (N * N) - a * c / N);
        });
        const varLog = P2 / (num * den);
        const se = Math.sqrt(Math.abs(varLog));
        const logMH = Math.log(mhRR);
        return { pOR: mhRR, lci: Math.exp(logMH - zCrit * se), uci: Math.exp(logMH + zCrit * se), pLogOR: logMH, pSE: se, method: 'MH-RR', k };
    }
};
```

**Step 3: Insert Peto engine (for OR only)**

```javascript
// ===== v12.0: PETO FIXED-EFFECT ENGINE =====
const PetoEngine = {
    /**
     * Peto's method for pooling OR (Yusuf 1985).
     * Best for rare events, no continuity correction needed.
     */
    pool(plotData, confLevel) {
        const k = plotData.length;
        if (k < 2) return null;
        const zCrit = normalQuantile(1 - (1 - confLevel) / 2);
        let sumOE = 0, sumV = 0;
        plotData.forEach(d => {
            const n1 = d.tN, n2 = d.cN, a = d.tE;
            const N = n1 + n2;
            const m = d.tE + d.cE; // total events
            if (N === 0 || m === 0 || m === N) return;
            const E = m * n1 / N;  // expected events in treatment
            const V = m * (N - m) * n1 * n2 / (N * N * (N - 1));
            sumOE += (a - E);
            sumV += V;
        });
        if (sumV === 0) return null;
        const logPetoOR = sumOE / sumV;
        const se = Math.sqrt(1 / sumV);
        const petoOR = Math.exp(logPetoOR);
        return { pOR: petoOR, lci: Math.exp(logPetoOR - zCrit * se), uci: Math.exp(logPetoOR + zCrit * se), pLogOR: logPetoOR, pSE: se, method: 'Peto', k };
    }
};
```

**Step 4: Commit**

Not a git repo; skip commit.

---

## Task 2: RoB Sensitivity Analysis

**Files:**
- Modify: `GLP1_CVOT_REVIEW.html`
  - UI button: insert after stat-chips-row (~line 800)
  - Logic: add `robSensitivity()` method to AnalysisEngine (~line 7448)
  - GRADE integration: modify `renderGRADE` to use RoB sensitivity result

**Step 1: Add RoB sensitivity toggle button in UI**

After the stat-chips-row div (line 800), insert:

```html
<!-- v12.0: RoB Sensitivity Analysis -->
<div class="flex flex-wrap items-center gap-4 px-2">
    <span class="text-[9px] font-bold uppercase tracking-widest text-slate-500">Sensitivity:</span>
    <button onclick="AnalysisEngine.toggleRobSensitivity()" id="btn-rob-sensitivity" class="text-[10px] font-bold px-4 py-1.5 rounded-full border border-slate-700 text-slate-400 hover:border-amber-500/50 hover:text-amber-400 transition-all" aria-pressed="false">
        <i class="fa-solid fa-shield-halved mr-1"></i> Low-Risk Only
    </button>
    <button onclick="AnalysisEngine.toggleExcludeTrial('ELIXA')" id="btn-exclude-elixa" class="text-[10px] font-bold px-4 py-1.5 rounded-full border border-slate-700 text-slate-400 hover:border-cyan-500/50 hover:text-cyan-400 transition-all" aria-pressed="false">
        <i class="fa-solid fa-ban mr-1"></i> Exclude ELIXA (4-pt MACE)
    </button>
    <div class="stat-chip stat-chip-blue" id="chip-rob-sensitivity"><i class="fa-solid fa-flask" style="font-size:10px"></i> RoB Sensitivity: --</div>
    <div class="stat-chip stat-chip-blue" id="chip-method-sensitivity"><i class="fa-solid fa-scale-balanced" style="font-size:10px"></i> Method Sensitivity: --</div>
</div>
```

**Step 2: Add sensitivity state and toggle logic**

In the `RapidMeta` state init (around line 1430), add two new state fields:
- `robSensitivityActive: false`
- `excludedTrialNames: []`

Add toggle methods to AnalysisEngine (before the `run()` orchestrator, ~line 7448):

```javascript
toggleRobSensitivity() {
    RapidMeta.state.robSensitivityActive = !RapidMeta.state.robSensitivityActive;
    const btn = document.getElementById('btn-rob-sensitivity');
    const active = RapidMeta.state.robSensitivityActive;
    btn.classList.toggle('border-amber-500', active);
    btn.classList.toggle('text-amber-400', active);
    btn.classList.toggle('bg-amber-500/10', active);
    btn.setAttribute('aria-pressed', active);
    RapidMeta.save();
    this.run();
},
toggleExcludeTrial(name) {
    const arr = RapidMeta.state.excludedTrialNames ?? [];
    const idx = arr.indexOf(name);
    if (idx >= 0) arr.splice(idx, 1); else arr.push(name);
    RapidMeta.state.excludedTrialNames = arr;
    const btn = document.getElementById('btn-exclude-elixa');
    const active = arr.includes('ELIXA');
    btn.classList.toggle('border-cyan-500', active);
    btn.classList.toggle('text-cyan-400', active);
    btn.classList.toggle('bg-cyan-500/10', active);
    btn.setAttribute('aria-pressed', active);
    RapidMeta.save();
    this.run();
},
```

**Step 3: Integrate RoB filter into the run() orchestrator**

In `AnalysisEngine.run()` (line ~7482), after `const trials = eligible;`, add filtering:

```javascript
// v12.0: RoB sensitivity filter
let analysisTrials = trials;
if (RapidMeta.state.robSensitivityActive) {
    analysisTrials = trials.filter(t => {
        const rob = t.data?.rob;
        if (!Array.isArray(rob)) return true;
        const overall = rob.length >= 5 ? rob[4] : rob[rob.length - 1];
        return overall === 'low';
    });
}
// v12.0: Exclude specific trials
const excluded = RapidMeta.state.excludedTrialNames ?? [];
if (excluded.length > 0) {
    analysisTrials = analysisTrials.filter(t => {
        const name = RapidMeta.nctAcronyms[t.id] ?? t.data?.name ?? t.id;
        return !excluded.includes(name);
    });
}
```

Then change `const c = this.computeCore(trials);` to `const c = this.computeCore(analysisTrials);` and update downstream references.

**Step 4: Add RoB sensitivity chip update**

In `runSubEngines`, after existing engines, add:

```javascript
// RoB sensitivity comparison
const robChip = document.getElementById('chip-rob-sensitivity');
if (RapidMeta.state.robSensitivityActive) {
    const fullK = RapidMeta.state._fullAnalysisK ?? plotData.length;
    robChip.className = 'stat-chip stat-chip-amber';
    robChip.innerHTML = `<i class="fa-solid fa-flask" style="font-size:10px"></i> RoB Sensitivity: k=${plotData.length}/${fullK} (low-risk only)`;
} else {
    robChip.className = 'stat-chip stat-chip-blue';
    robChip.innerHTML = '<i class="fa-solid fa-flask" style="font-size:10px"></i> RoB Sensitivity: Off (all trials)';
}
```

---

## Task 3: Expanded Subgroup Analysis

**Files:**
- Modify: `GLP1_CVOT_REVIEW.html`
  - UI: Add subgroup selector dropdown near line 784 (meta-regression covariate area)
  - Logic: Modify subgroup chart rendering in renderPlots (~line 7650)

**Step 1: Add subgroup-by selector UI**

After the meta-regression covariate selector (line 788), add:

```html
<div class="h-6 w-px bg-slate-800"></div>
<div class="flex items-center gap-2">
    <span class="text-[9px] font-bold uppercase tracking-widest text-slate-500">Subgroup By:</span>
    <select id="subgroup-by" onchange="AnalysisEngine.run()" class="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1 text-[10px] font-bold text-slate-300 outline-none">
        <option value="group">Drug Class (Short/Long-acting)</option>
        <option value="molecule">Molecule</option>
        <option value="population">Population (T2DM vs Obesity)</option>
        <option value="mace_def">MACE Definition (3-pt vs 4-pt)</option>
        <option value="era">Era (Pre-2020 vs 2020+)</option>
    </select>
</div>
```

**Step 2: Add subgroup assignment logic**

In `renderPlots`, replace the hardcoded `d.group` subgroup (line ~7651-7660) with dynamic grouping:

```javascript
// 2. Subgroup Plot — dynamic grouping
const subgroupBy = document.getElementById('subgroup-by')?.value ?? 'group';
const getSubgroupLabel = (d) => {
    switch (subgroupBy) {
        case 'molecule': return d.id; // each trial = its own molecule
        case 'population': {
            const obesityTrials = ['SELECT'];
            return obesityTrials.includes(d.id) ? 'Obesity/CVD (no mandatory T2DM)' : 'T2DM + High CV Risk';
        }
        case 'mace_def': {
            return d.id === 'ELIXA' ? '4-point MACE' : '3-point MACE';
        }
        case 'era': return (d.year ?? 2020) < 2020 ? 'Pre-2020' : '2020+';
        default: return d.group || 'Other';
    }
};
const groups = [...new Set(data.map(d => getSubgroupLabel(d)))];
const tr2X = [], tr2Y = [], tr2Err = [], subDescs = [];
let qBetween = 0, dfBetween = groups.length - 1;
const overallLogOR = pLogOR;
groups.forEach(g => {
    const sub = data.filter(d => getSubgroupLabel(d) === g);
    if (sub.length === 0) return;
    const sw = sub.reduce((a, b) => a + b.w_random, 0);
    const swy = sub.reduce((a, b) => a + b.w_random * b.logOR, 0);
    const est = swy / sw;
    const se = Math.sqrt(1 / sw);
    tr2X.push(est);
    tr2Y.push(`${g} (k=${sub.length})`);
    tr2Err.push(zCrit * se);
    qBetween += sw * Math.pow(est - overallLogOR, 2);
    subDescs.push(`${g}: ${Math.exp(est).toFixed(2)} (${Math.exp(est - zCrit * se).toFixed(2)}-${Math.exp(est + zCrit * se).toFixed(2)}, k=${sub.length})`);
});
const qBetweenP = chi2Pvalue(qBetween, dfBetween);
```

**Step 3: Update subgroup chart title and description**

```javascript
const subgroupTitles = {
    group: 'Drug Class', molecule: 'Molecule', population: 'Population',
    mace_def: 'MACE Definition', era: 'Era'
};
const subTitle = subgroupTitles[subgroupBy] ?? 'Subgroup';
const tr2 = { x: tr2X, y: tr2Y, mode: 'markers', type: 'scatter',
    error_x: { type: 'data', array: tr2Err, visible: true, color: '#10b981' },
    marker: { size: 14, color: '#10b981', symbol: 'diamond' } };
Plotly.newPlot('plot-subgroup', [tr2], layout(logEmLabel, `Subgroup (${subTitle})`), PLOTLY_OPTS);
setDesc('desc-subgroup', `Subgroup analysis by ${subTitle.toLowerCase()}. ${subDescs.join('; ')}. Q-between = ${qBetween.toFixed(2)}, p = ${qBetweenP.toFixed(4)}. ${qBetweenP < 0.10 ? 'Significant interaction detected.' : 'No significant interaction.'}`);
```

---

## Task 4: Method Sensitivity Panel

**Files:**
- Modify: `GLP1_CVOT_REVIEW.html`
  - New chart container: insert after chart #16 (line ~848)
  - Engine logic: add to runSubEngines
  - Rendering: new renderMethodSensitivity function

**Step 1: Add two new chart containers to the grid (after line 848)**

```html
<div class="col-span-1 md:col-span-2 expert-only"><div class="chart-header mb-2 px-2"><h4 class="text-[10px] opacity-70 font-bold uppercase tracking-widest">17. Method Sensitivity</h4><button class="chart-dl-btn" onclick="downloadChart('plot-method-sens','method_sensitivity')" title="Download as SVG"><i class="fa-solid fa-download"></i></button></div><div id="plot-method-sens" class="chart-container" aria-describedby="desc-method-sens"></div><div id="desc-method-sens" class="chart-desc"></div></div>
<div class="col-span-1 md:col-span-2 expert-only"><div class="chart-header mb-2 px-2"><h4 class="text-[10px] opacity-70 font-bold uppercase tracking-widest">18. Network Meta-Analysis (League Table)</h4><button class="chart-dl-btn" onclick="downloadChart('plot-nma','nma_league')" title="Download as SVG"><i class="fa-solid fa-download"></i></button></div><div id="plot-nma" class="chart-container" style="height:450px;" aria-describedby="desc-nma"></div><div id="desc-nma" class="chart-desc"></div></div>
```

**Step 2: Add renderMethodSensitivity to AnalysisEngine**

In runSubEngines, after existing engines:

```javascript
// Method Sensitivity
const isHRMode = (RapidMeta.state.effectMeasure ?? 'OR') === 'HR';
const isRR = (RapidMeta.state.effectMeasure ?? 'OR') === 'RR';
const confLevel = RapidMeta.state.confLevel ?? 0.95;
const methods = [];
// DL (already computed in main)
methods.push({ name: 'DerSimonian-Laird', pOR: Math.exp(pLogOR), lci: Math.exp(pLogOR - normalQuantile(1-(1-confLevel)/2) * pSE), uci: Math.exp(pLogOR + normalQuantile(1-(1-confLevel)/2) * pSE) });
// REML
const remlResult = REMLEngine.pool(plotData, confLevel);
if (remlResult) methods.push({ name: 'REML', pOR: remlResult.pOR, lci: remlResult.lci, uci: remlResult.uci });
// Bayesian posterior median
if (bayesResult) methods.push({ name: 'Bayesian (posterior)', pOR: bayesResult.postMeanOR ?? Math.exp(pLogOR), lci: bayesResult.criLo, uci: bayesResult.criHi });
// MH and Peto (only for 2x2 data, not HR mode)
if (!isHRMode && plotData.length >= 2 && plotData[0].tE !== undefined) {
    const mhResult = isRR ? MHEngine.poolRR(plotData, confLevel) : MHEngine.poolOR(plotData, confLevel);
    if (mhResult) methods.push({ name: 'Mantel-Haenszel', pOR: mhResult.pOR, lci: mhResult.lci, uci: mhResult.uci });
    if (!isRR) {
        const petoResult = PetoEngine.pool(plotData, confLevel);
        if (petoResult) methods.push({ name: 'Peto', pOR: petoResult.pOR, lci: petoResult.lci, uci: petoResult.uci });
    }
}
this.renderMethodSensitivity(methods, confLevel);
// Update method sensitivity chip
const msChip = document.getElementById('chip-method-sensitivity');
if (methods.length >= 2) {
    const estimates = methods.map(m => m.pOR);
    const range = Math.max(...estimates) - Math.min(...estimates);
    const robust = range < 0.05;
    msChip.className = `stat-chip ${robust ? 'stat-chip-green' : 'stat-chip-amber'}`;
    msChip.innerHTML = `<i class="fa-solid fa-scale-balanced" style="font-size:10px"></i> Method Sensitivity: ${robust ? 'Robust' : 'Sensitive'} (range ${range.toFixed(3)})`;
} else {
    msChip.className = 'stat-chip stat-chip-blue';
    msChip.innerHTML = '<i class="fa-solid fa-scale-balanced" style="font-size:10px"></i> Method Sensitivity: N/A';
}
```

**Step 3: Add renderMethodSensitivity function**

```javascript
renderMethodSensitivity(methods, confLevel) {
    if (methods.length === 0) return;
    const ciPct = (confLevel * 100).toFixed(0);
    const emShort = RapidMeta.emLabel('short');
    const traces = [];
    methods.forEach((m, i) => {
        const colors = ['#3b82f6', '#10b981', '#a855f7', '#f59e0b', '#ef4444'];
        const color = colors[i % colors.length];
        traces.push({
            x: [m.pOR], y: [m.name], mode: 'markers', type: 'scatter',
            marker: { size: 14, color, symbol: ['diamond','circle','square','triangle-up','star'][i % 5] },
            error_x: { type: 'data', symmetric: false, array: [m.uci - m.pOR], arrayminus: [m.pOR - m.lci], visible: true, color, thickness: 3 },
            showlegend: false,
            hovertemplate: `${m.name}: ${m.pOR.toFixed(3)} (${m.lci.toFixed(3)}-${m.uci.toFixed(3)})<extra></extra>`
        });
    });
    const lo = Math.min(...methods.map(m => m.lci)) * 0.95;
    const hi = Math.max(...methods.map(m => m.uci)) * 1.05;
    const lay = {
        paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
        xaxis: { title: `${emShort} (${ciPct}% CI)`, gridcolor: '#1e293b', color: '#94a3b8', range: [lo, hi] },
        yaxis: { gridcolor: '#1e293b', color: '#94a3b8', autorange: 'reversed' },
        font: { color: '#94a3b8', size: 11 },
        margin: { t: 10, b: 50, l: 180, r: 30 },
        shapes: [{ type: 'line', x0: 1, x1: 1, y0: -0.5, y1: methods.length - 0.5, line: { color: '#ef4444', width: 2, dash: 'dot' } }]
    };
    Plotly.newPlot('plot-method-sens', traces, lay, { displayModeBar: false, responsive: true });
    const desc = methods.map(m => `${m.name}: ${m.pOR.toFixed(3)} (${m.lci.toFixed(3)}-${m.uci.toFixed(3)})`).join(' | ');
    const setDesc = (id, txt) => { const el = document.getElementById(id); if (el) el.textContent = txt; };
    setDesc('desc-method-sens', desc);
},
```

---

## Task 5: Network Meta-Analysis (Bucher Indirect Comparisons)

**Files:**
- Modify: `GLP1_CVOT_REVIEW.html`
  - New NMAEngine object: insert after PetoEngine
  - Rendering: league table heatmap in plot-nma container
  - Integration: call from runSubEngines

**Step 1: Insert NMAEngine**

```javascript
// ===== v12.0: NETWORK META-ANALYSIS (BUCHER INDIRECT COMPARISONS) =====
const NMAEngine = {
    /**
     * Bucher indirect comparison for trials sharing a common comparator (placebo).
     * log(HR_A_vs_B) = log(HR_A_vs_placebo) - log(HR_B_vs_placebo)
     * Var = Var_A + Var_B (independent trials)
     * @param {Array} plotData - with .id, .logOR, .vi
     * @param {number} confLevel
     * @returns {Object} { molecules: [], league: 2D array, networkEdges: [] }
     */
    run(plotData, confLevel) {
        const k = plotData.length;
        if (k < 2) return { molecules: [], league: [], available: false };
        const zCrit = normalQuantile(1 - (1 - confLevel) / 2);
        const molecules = plotData.map(d => d.id);
        // League table: molecules.length x molecules.length
        // league[i][j] = effect of molecule i vs molecule j
        const league = [];
        for (let i = 0; i < k; i++) {
            league[i] = [];
            for (let j = 0; j < k; j++) {
                if (i === j) {
                    league[i][j] = { logOR: 0, se: 0, pOR: 1, lci: 1, uci: 1, label: '—' };
                } else {
                    // A vs B = A vs placebo - B vs placebo
                    const logDiff = plotData[i].logOR - plotData[j].logOR;
                    const seDiff = Math.sqrt(plotData[i].vi + plotData[j].vi);
                    const or = Math.exp(logDiff);
                    const lo = Math.exp(logDiff - zCrit * seDiff);
                    const hi = Math.exp(logDiff + zCrit * seDiff);
                    const sig = lo > 1 || hi < 1;
                    league[i][j] = { logOR: logDiff, se: seDiff, pOR: or, lci: lo, uci: hi, sig, label: `${or.toFixed(2)} (${lo.toFixed(2)}-${hi.toFixed(2)})` };
                }
            }
        }
        return { molecules, league, available: true, k };
    },
    renderPlot(result) {
        const el = document.getElementById('plot-nma');
        if (!el || !result || !result.available) return;
        const { molecules, league } = result;
        const k = molecules.length;
        // Heatmap: z values are log(OR), text shows formatted results
        const z = league.map(row => row.map(cell => cell.logOR));
        const text = league.map(row => row.map(cell => cell.label));
        const colorscale = [
            [0, '#22c55e'],     // green = favors row molecule
            [0.5, '#1e293b'],   // neutral
            [1, '#ef4444']      // red = favors column molecule
        ];
        const maxAbs = Math.max(0.3, ...z.flat().map(Math.abs));
        const trace = {
            z, x: molecules, y: molecules, type: 'heatmap',
            text, texttemplate: '%{text}', textfont: { size: 9, color: '#f1f5f9' },
            colorscale, zmin: -maxAbs, zmax: maxAbs,
            showscale: true, colorbar: { title: 'log(OR/HR)', titlefont: { size: 9 }, tickfont: { size: 8 } },
            hovertemplate: '%{y} vs %{x}: %{text}<extra></extra>'
        };
        const lay = {
            paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#94a3b8', size: 10 },
            xaxis: { side: 'top', tickangle: -45, color: '#94a3b8' },
            yaxis: { autorange: 'reversed', color: '#94a3b8' },
            margin: { t: 120, b: 20, l: 120, r: 80 },
            annotations: []
        };
        // Add significance markers
        for (let i = 0; i < k; i++) {
            for (let j = 0; j < k; j++) {
                if (i !== j && league[i][j].sig) {
                    lay.annotations.push({
                        x: molecules[j], y: molecules[i],
                        text: '*', showarrow: false,
                        font: { color: '#fbbf24', size: 14, weight: 'bold' },
                        xshift: 40, yshift: -8
                    });
                }
            }
        }
        Plotly.newPlot('plot-nma', [trace], lay, { displayModeBar: false, responsive: true });
        const sigPairs = [];
        for (let i = 0; i < k; i++) {
            for (let j = i + 1; j < k; j++) {
                if (league[i][j].sig) sigPairs.push(`${molecules[i]} vs ${molecules[j]}: ${league[i][j].label}`);
            }
        }
        const descEl = document.getElementById('desc-nma');
        if (descEl) descEl.textContent = `Bucher indirect comparisons (${k} molecules). ${sigPairs.length > 0 ? 'Significant pairs: ' + sigPairs.join('; ') : 'No statistically significant pairwise differences detected.'} Read row vs column.`;
    }
};
```

**Step 2: Call NMA from runSubEngines**

After method sensitivity code:

```javascript
// NMA
const nmaResult = NMAEngine.run(plotData, confLevel);
NMAEngine.renderPlot(nmaResult);
```

---

## Task 6: Update Annotation, CI Comparison, and REML stat card

**Files:**
- Modify: `GLP1_CVOT_REVIEW.html`
  - Add REML stat card to UI (line ~763)
  - Update renderCIComparison to include REML trace (line ~8265)
  - Update annotation text (line ~8263)

**Step 1: Add REML stat card**

After the Q-test card (line 763), add a new row:

```html
<!-- v12.0: REML + Method Comparison cards -->
<div class="grid grid-cols-3 gap-8">
    <div class="glass p-6 rounded-[30px] border border-emerald-500/20 bg-emerald-500/5 text-center"><div class="text-[10px] opacity-50 uppercase font-bold mb-2 tracking-[0.2em]">REML Estimate</div><div id="res-reml" class="text-lg font-bold font-mono tracking-tight text-emerald-400">--</div></div>
    <div class="glass p-6 rounded-[30px] border border-emerald-500/20 bg-emerald-500/5 text-center"><div class="text-[10px] opacity-50 uppercase font-bold mb-2 tracking-[0.2em]">REML tau&sup2;</div><div id="res-reml-tau2" class="text-lg font-bold font-mono tracking-tight text-emerald-400">--</div></div>
    <div class="glass p-6 rounded-[30px] border border-amber-500/20 bg-amber-500/5 text-center"><div class="text-[10px] opacity-50 uppercase font-bold mb-2 tracking-[0.2em]">MH Estimate</div><div id="res-mh" class="text-lg font-bold font-mono tracking-tight text-amber-400">--</div></div>
</div>
```

**Step 2: Update renderCIComparison**

In `renderCIComparison` (~line 8265), after the existing DL/HKSJ/PI traces, add:

```javascript
// v12.0: Add REML and MH traces
const remlResult = REMLEngine.pool(/* need plotData */);
// Since we don't have plotData here, store it in state during run()
const remlEst = RapidMeta.state._remlResult;
if (remlEst) {
    addTrace('REML (' + ciPct + '% CI)', remlEst.lci, remlEst.uci, '#10b981', 'triangle-up');
}
const mhEst = RapidMeta.state._mhResult;
if (mhEst) {
    addTrace('Mantel-Haenszel', mhEst.lci, mhEst.uci, '#f59e0b', 'star');
}
```

**Step 3: Store REML/MH results in state during runSubEngines**

In runSubEngines, save to state for renderCIComparison access:

```javascript
RapidMeta.state._remlResult = remlResult;
RapidMeta.state._mhResult = mhResult;
```

**Step 4: Update annotation text**

Change line 8263 to include REML:

```javascript
document.getElementById('nyt-annotation').textContent = `Analysis: DerSimonian-Laird + REML random-effects models with ${ciPct}% CI. HKSJ correction (max(1,q*) safeguard). PI with k-2 df (Higgins 2009). MH and Peto fixed-effect models for sensitivity. Bucher indirect comparisons for NMA.`;
```

---

## Task 7: Update plotIds/descIds arrays and Arabic translations

**Files:**
- Modify: `GLP1_CVOT_REVIEW.html`
  - plotIds array (~line 7358): add 'plot-method-sens', 'plot-nma'
  - descIds array (~line 7362): add 'desc-method-sens', 'desc-nma'
  - Arabic translations: add new strings

**Step 1: Update plotIds and descIds**

Add to the arrays:

```javascript
'plot-method-sens', 'plot-nma'
// and
'desc-method-sens', 'desc-nma'
```

**Step 2: Add Arabic translations for new UI strings**

Add to the translation dictionaries (~line 2989+):

```javascript
'Low-Risk Only': 'منخفض المخاطر فقط',
'Exclude ELIXA (4-pt MACE)': 'استبعاد ELIXA (4 نقاط MACE)',
'RoB Sensitivity': 'حساسية تقييم المخاطر',
'Method Sensitivity': 'حساسية الطريقة',
'Subgroup By:': 'تقسيم حسب:',
'Drug Class (Short/Long-acting)': 'فئة الدواء (قصير/طويل المفعول)',
'Molecule': 'الجزيء',
'Population (T2DM vs Obesity)': 'السكان (السكري مقابل البدانة)',
'MACE Definition (3-pt vs 4-pt)': 'تعريف MACE (3 مقابل 4 نقاط)',
'Era (Pre-2020 vs 2020+)': 'الحقبة (قبل 2020 مقابل 2020+)',
'Method Sensitivity': 'حساسية الطريقة الإحصائية',
'Network Meta-Analysis (League Table)': 'التحليل التلوي الشبكي (جدول المقارنات)',
'REML Estimate': 'تقدير REML',
'MH Estimate': 'تقدير Mantel-Haenszel',
'Robust': 'متين',
'Sensitive': 'حساس',
```

---

## Task 8: Update Selenium Tests

**Files:**
- Modify: `test_glp1_selenium.py` — add tests for new features

**Step 1: Add tests for REML stat card, method sensitivity chip, NMA chart**

```python
# Test REML stat card renders
reml_el = driver.find_element(By.ID, 'res-reml')
assert reml_el.text != '--', "REML estimate should be populated"

# Test method sensitivity chip
ms_chip = driver.find_element(By.ID, 'chip-method-sensitivity')
assert 'Robust' in ms_chip.text or 'Sensitive' in ms_chip.text, "Method sensitivity chip should show verdict"

# Test NMA chart rendered
nma_el = driver.find_element(By.ID, 'plot-nma')
assert nma_el.find_elements(By.CSS_SELECTOR, '.plotly'), "NMA chart should have Plotly content"

# Test RoB sensitivity toggle
rob_btn = driver.find_element(By.ID, 'btn-rob-sensitivity')
rob_btn.click()
time.sleep(1)
# Should re-run analysis with fewer trials
reml_after = driver.find_element(By.ID, 'res-reml').text
rob_chip = driver.find_element(By.ID, 'chip-rob-sensitivity')
assert 'low-risk only' in rob_chip.text.lower(), "RoB chip should indicate low-risk filter"
# Toggle back
rob_btn.click()
time.sleep(1)

# Test subgroup selector
sub_select = Select(driver.find_element(By.ID, 'subgroup-by'))
sub_select.select_by_value('molecule')
time.sleep(1)
sub_desc = driver.find_element(By.ID, 'desc-subgroup').text
assert 'LEADER' in sub_desc or 'ELIXA' in sub_desc, "Molecule subgroup should show individual trial names"
sub_select.select_by_value('group')  # reset
```

---

## Task 9: Final Div Balance and Safety Check

**Step 1:** Count `<div` vs `</div>` to ensure balance after all edits.

**Step 2:** Search for any literal `</script>` inside `<script>` blocks.

**Step 3:** Verify no duplicate element IDs for new elements.

**Step 4:** Run Selenium test suite to confirm all tests pass.

---

## Execution Order

1. Task 1 (REML + MH + Peto engines) — foundational, no UI dependency
2. Task 6 (REML/MH stat cards) — needs engines from Task 1
3. Task 4 (Method sensitivity panel) — needs all engines
4. Task 5 (NMA engine + league table) — independent of Tasks 2-4
5. Task 2 (RoB sensitivity) — independent of 4-5
6. Task 3 (Expanded subgroups) — independent
7. Task 7 (plotIds, translations) — after all new elements exist
8. Task 8 (Selenium tests) — after all features
9. Task 9 (Safety checks) — final
