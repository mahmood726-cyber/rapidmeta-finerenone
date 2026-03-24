# Finerenone v12.0 — Robustness, Provenance & Submission Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enhance FINERENONE_REVIEW.html from v11.0 to v12.0 with sensitivity analysis, influence diagnostics, per-number provenance, and submission-quality exports.

**Architecture:** All code lives in one file (`FINERENONE_REVIEW.html`, currently ~10,600 lines). New engines follow the existing pattern: `const EngineName = { run(...) { ... }, renderPlot(...) { ... } };`. New engines are inserted between `DataSealEngine` (~line 7600) and `AnalysisEngine` (~line 7609). New HTML plot divs are added to the analysis tab grid. The regression test (`finerenone_full_regression.py`) and goldens JSON are extended for each new feature.

**Tech Stack:** Vanilla JS (ES2020), Plotly.js 2.27.0, Tailwind CSS, Playwright CLI for regression tests.

**Spec:** `docs/superpowers/specs/2026-03-12-finerenone-v12-robustness-provenance-submission-design.md`

---

## Chunk 1: Tier C — Analysis Robustness

### Task 1: SensitivityEngine — Core Logic (C1)

**Files:**
- Modify: `FINERENONE_REVIEW.html` (insert between DataSealEngine ~line 7600 and AnalysisEngine ~line 7609)

- [ ] **Step 1: Add SensitivityEngine object skeleton**

Insert after `DataSealEngine` closing brace (line ~7600), before `// Shared Plotly configuration`:

```javascript
// ===== v12.0: SENSITIVITY ANALYSIS PANEL (Chart #17) =====
const SensitivityEngine = {
    // pOR here means pooled exponentiated effect (exp(logOR) in OR mode, exp(logHR) in HR mode)
    run(plotData, pLogOR, pSE, tau2, zCrit, confLevel, pOR, lci, uci) {
        const k = plotData.length;
        const emMode = RapidMeta.resolveEffectMeasure().effective;
        const useHR = (emMode === 'HR');
        const scenarios = [];

        // Scenario 1: FE vs RE (inverse-variance FE in both OR and HR modes)
        const feResult = this._fePool(plotData, zCrit, confLevel);
        scenarios.push(this._classify('FE (IV)', feResult.or, feResult.lci, feResult.uci, feResult.pValue, k, pOR, lci, uci));

        // Scenario 2: Exclude high-RoB
        const lowRobData = plotData.filter(d => !d.rob || !d.rob.includes('high'));
        if (lowRobData.length >= 1 && lowRobData.length < k) {
            const robResult = this._dlPool(lowRobData, zCrit, confLevel);
            scenarios.push(this._classify('Excl. High-RoB', robResult.or, robResult.lci, robResult.uci, robResult.pValue, lowRobData.length, pOR, lci, uci));
        } else {
            scenarios.push({ label: 'Excl. High-RoB', or: null, lci: null, uci: null, pValue: null, k: lowRobData.length, concordance: 'grey', note: lowRobData.length === k ? 'No high-RoB trials' : 'All trials high-RoB' });
        }

        // Scenario 3: Peto OR (OR mode only, requires 2x2 tables)
        if (!useHR) {
            const hasRare = plotData.some(d => (d.ter != null && d.ter < 0.05) || (d.cer != null && d.cer < 0.05));
            if (hasRare) {
                const petoResult = this._petoPool(plotData, zCrit);
                scenarios.push(this._classify('Peto OR', petoResult.or, petoResult.lci, petoResult.uci, petoResult.pValue, k, pOR, lci, uci));
            } else {
                scenarios.push({ label: 'Peto OR', or: null, lci: null, uci: null, pValue: null, k, concordance: 'grey', note: 'N/A \u2014 no rare-event studies' });
            }
        } else {
            scenarios.push({ label: 'Peto OR', or: null, lci: null, uci: null, pValue: null, k, concordance: 'grey', note: 'N/A \u2014 Peto requires event counts' });
        }

        // Scenario 4: REML + HKSJ (surface existing computation)
        const remlResult = this._remlHksjPool(plotData, confLevel);
        scenarios.push(this._classify('REML+HKSJ', remlResult.or, remlResult.lci, remlResult.uci, remlResult.pValue, k, pOR, lci, uci));

        // Scenario 5: Randomization p
        const randP = this._randomizationP(plotData, pLogOR, useHR);
        scenarios.push({
            label: 'Randomization p',
            or: pOR, lci, uci,
            pValue: randP,
            k,
            concordance: Math.abs(randP - (this._asymptP(pLogOR, pSE))) < 0.01 ? 'green' : (Math.abs(randP - this._asymptP(pLogOR, pSE)) < 0.05 ? 'amber' : 'red'),
            note: `p-rand=${randP.toFixed(3)} vs p-asymp=${this._asymptP(pLogOR, pSE).toFixed(3)}`
        });

        // Verdict
        const concordant = scenarios.filter(s => s.concordance === 'green').length;
        const total = scenarios.filter(s => s.concordance !== 'grey').length;

        return { scenarios, concordant, total };
    },

    _asymptP(logOR, se) {
        const z = Math.abs(logOR / se);
        return 2 * (1 - normalCDF(z));
    },

    _fePool(plotData, zCrit, confLevel) {
        let sw = 0, swy = 0;
        plotData.forEach(d => { sw += d.w_fixed; swy += d.w_fixed * d.logOR; });
        const est = swy / sw;
        const se = Math.sqrt(1 / sw);
        const or = Math.exp(est);
        const lo = Math.exp(est - zCrit * se);
        const hi = Math.exp(est + zCrit * se);
        const z = Math.abs(est / se);
        return { or, lci: lo, uci: hi, pValue: 2 * (1 - normalCDF(z)) };
    },

    _dlPool(data, zCrit, confLevel) {
        let sW = 0, sWY = 0, sW_y2 = 0, sW2 = 0;
        data.forEach(d => { sW += d.w_fixed; sWY += d.w_fixed * d.logOR; sW_y2 += d.w_fixed * d.logOR * d.logOR; sW2 += d.w_fixed * d.w_fixed; });
        const Q = Math.max(0, sW_y2 - sWY * sWY / sW);
        const df = data.length - 1;
        const tau2 = df > 0 && Q > df ? (Q - df) / (sW - sW2 / sW) : 0;
        let swR = 0, swRY = 0;
        data.forEach(d => { const wr = 1 / (d.vi + tau2); swR += wr; swRY += wr * d.logOR; });
        const est = swR > 0 ? swRY / swR : 0;
        const se = swR > 0 ? Math.sqrt(1 / swR) : 1;
        const or = Math.exp(est);
        const lo = Math.exp(est - zCrit * se);
        const hi = Math.exp(est + zCrit * se);
        const z = Math.abs(est / se);
        return { or, lci: lo, uci: hi, pValue: 2 * (1 - normalCDF(z)) };
    },

    _petoPool(plotData, zCrit) {
        let sumOE = 0, sumV = 0;
        plotData.forEach(d => {
            const a_i = d.tE + d.cE;
            const n_i = d.tN + d.cN;
            const E_i = d.tN * a_i / n_i;
            const V_i = d.tN * d.cN * a_i * (n_i - a_i) / (n_i * n_i * (n_i - 1));
            sumOE += d.tE - E_i;
            sumV += V_i;
        });
        if (sumV < 1e-15) return { or: 1, lci: 1, uci: 1, pValue: 1 };
        const logOR = sumOE / sumV;
        const se = 1 / Math.sqrt(sumV);
        const or = Math.exp(logOR);
        const z = Math.abs(logOR / se);
        return { or, lci: Math.exp(logOR - zCrit * se), uci: Math.exp(logOR + zCrit * se), pValue: 2 * (1 - normalCDF(z)) };
    },

    _remlHksjPool(plotData, confLevel) {
        const k = plotData.length;
        const yi = plotData.map(d => d.logOR);
        const vi = plotData.map(d => d.vi);
        // REML tau2 via Fisher scoring
        let tau2r = 0;
        let sW = 0, sWY = 0, sW_y2 = 0, sW2_init = 0;
        plotData.forEach(d => { sW += d.w_fixed; sWY += d.w_fixed * d.logOR; sW_y2 += d.w_fixed * d.logOR * d.logOR; sW2_init += d.w_fixed * d.w_fixed; });
        const Q0 = Math.max(0, sW_y2 - sWY * sWY / sW);
        const df0 = k - 1;
        tau2r = df0 > 0 && Q0 > df0 ? (Q0 - df0) / (sW - sW2_init / sW) : 0;
        for (let it = 0; it < 100; it++) {
            const w = vi.map(v => 1 / (v + tau2r));
            const _sW = w.reduce((a, b) => a + b, 0);
            const _mu = w.reduce((a, wi, i) => a + wi * yi[i], 0) / _sW;
            const _sW2 = w.reduce((a, wi) => a + wi * wi, 0);
            const _sW3 = w.reduce((a, wi) => a + wi * wi * wi, 0);
            const _trP = _sW - _sW2 / _sW;
            const _yP2y = w.reduce((a, wi, i) => a + wi * wi * Math.pow(yi[i] - _mu, 2), 0);
            const _trP2 = _sW2 - 2 * _sW3 / _sW + _sW2 * _sW2 / (_sW * _sW);
            if (_trP2 < 1e-15) break;
            const _delta = (_yP2y - _trP) / _trP2;
            const _new = Math.max(0, tau2r + _delta);
            if (Math.abs(_new - tau2r) < 1e-10) { tau2r = _new; break; }
            tau2r = _new;
        }
        // Pool with REML tau2
        let swR = 0, swRY = 0;
        plotData.forEach(d => { const wr = 1 / (d.vi + tau2r); swR += wr; swRY += wr * d.logOR; });
        const est = swRY / swR;
        const se = Math.sqrt(1 / swR);
        // HKSJ adjustment
        let qStar = 0;
        plotData.forEach(d => { const wr = 1 / (d.vi + tau2r); qStar += wr * Math.pow(d.logOR - est, 2); });
        qStar /= (k - 1);
        const hksjAdj = Math.max(1, qStar);
        const hksjSE = Math.sqrt(hksjAdj / swR);
        const tCrit = tQuantile(1 - (1 - confLevel) / 2, k - 1);
        const or = Math.exp(est);
        const lo = Math.exp(est - tCrit * hksjSE);
        const hi = Math.exp(est + tCrit * hksjSE);
        const tStat = Math.abs(est / hksjSE);
        // p-value from t-distribution (consistent with HKSJ using t-quantile for CI)
        // Use betaIncomplete for proper t-CDF: P(T > |t|) = I(df/(df+t^2), df/2, 1/2)
        const dfHK = k - 1;
        const tCDF = dfHK > 0 ? 0.5 * (1 + (1 - betaIncomplete(dfHK / (dfHK + tStat * tStat), dfHK / 2, 0.5)) * (tStat >= 0 ? 1 : -1)) : 0.5;
        const pVal = 2 * (1 - tCDF);
        return { or, lci: lo, uci: hi, pValue: pVal };
    },

    _randomizationP(plotData, observedLogOR, useHR) {
        // djb2 hash of concatenated study IDs for reproducible seed
        let hashSeed = 5381;
        plotData.forEach(d => {
            const id = d.id;
            for (let i = 0; i < id.length; i++) hashSeed = ((hashSeed << 5) + hashSeed + id.charCodeAt(i)) >>> 0;
        });
        // mulberry32 PRNG
        let _s = hashSeed;
        const rand = () => { _s |= 0; _s = _s + 0x6D2B79F5 | 0; let t = Math.imul(_s ^ _s >>> 15, 1 | _s); t ^= t + Math.imul(t ^ t >>> 7, 61 | t); return ((t ^ t >>> 14) >>> 0) / 4294967296; };
        const nPerm = 1000;
        let moreExtreme = 0;
        const absObs = Math.abs(observedLogOR);
        // Use FE pooling for permutation test (standard approach — Follmann & Proschan 1999)
        // FE is appropriate here because the null hypothesis is H0: theta=0 (no treatment effect),
        // and under the null, heterogeneity is zero by construction
        for (let p = 0; p < nPerm; p++) {
            let sW = 0, sWY = 0;
            plotData.forEach(d => {
                // Sign-flip: randomly negate each study's logOR (equivalent to label swap)
                // This works for both OR and HR modes since both store effects as logOR
                const sign = rand() < 0.5 ? 1 : -1;
                const permLogOR = sign * d.logOR;
                sW += d.w_fixed;
                sWY += d.w_fixed * permLogOR;
            });
            const permEst = sWY / sW;
            if (Math.abs(permEst) >= absObs) moreExtreme++;
        }
        return (moreExtreme + 1) / (nPerm + 1); // +1 for continuity
    },

    _classify(label, or, lci, uci, pValue, k, mainOR, mainLCI, mainUCI) {
        const mainSig = (mainLCI > 1 || mainUCI < 1);
        const mainDir = mainOR < 1 ? 'benefit' : 'harm';
        const thisSig = (lci > 1 || uci < 1);
        const thisDir = or < 1 ? 'benefit' : 'harm';
        let concordance;
        if (mainDir !== thisDir) concordance = 'red';
        else if (mainSig === thisSig) concordance = 'green';
        else concordance = 'amber';
        return { label, or, lci, uci, pValue, k, concordance };
    },

    renderChart(result) {
        const el = document.getElementById('plot-sensitivity');
        if (!el || !result) { if (el) { try { Plotly.purge(el); } catch(e) {} el.innerHTML = ''; } return; }
        const { scenarios } = result;
        const colors = { green: '#22c55e', amber: '#eab308', red: '#ef4444', grey: '#64748b' };
        const yLabels = scenarios.map(s => s.label);
        const xVals = scenarios.map(s => s.or != null ? Math.log(s.or) : null);
        const errVals = scenarios.map((s, i) => {
            if (s.or == null) return 0;
            return [Math.log(s.or) - Math.log(s.lci), Math.log(s.uci) - Math.log(s.or)];
        });
        const markerColors = scenarios.map(s => colors[s.concordance]);
        const trace = {
            x: xVals, y: yLabels, mode: 'markers', type: 'scatter',
            error_x: { type: 'data', symmetric: false, array: errVals.map(e => Array.isArray(e) ? e[1] : 0), arrayminus: errVals.map(e => Array.isArray(e) ? e[0] : 0), visible: true, color: '#94a3b8' },
            marker: { size: 12, color: markerColors, symbol: 'diamond' },
            hovertext: scenarios.map(s => s.note ?? `${s.label}: ${s.or?.toFixed(2) ?? 'N/A'}`),
            hoverinfo: 'text'
        };
        const nullLine = { x: [0, 0], y: [yLabels[0], yLabels[yLabels.length - 1]], mode: 'lines', line: { color: '#64748b', dash: 'dot', width: 1 }, showlegend: false };
        const lo = plotlyLayout('log(Effect)', 'Scenario', { showlegend: false });
        lo.yaxis.autorange = 'reversed';
        Plotly.newPlot('plot-sensitivity', [nullLine, trace], lo, PLOTLY_OPTS);

        // Verdict text
        const descEl = document.getElementById('desc-sensitivity');
        if (descEl) {
            const verdictItems = scenarios.filter(s => s.concordance !== 'grey');
            const concordant = verdictItems.filter(s => s.concordance === 'green').length;
            const txt = concordant === verdictItems.length
                ? `The pooled estimate is robust across all sensitivity analyses (${concordant}/${verdictItems.length} concordant).`
                : `Caution: ${verdictItems.length - concordant} sensitivity scenario(s) show attenuated or reversed results (${concordant}/${verdictItems.length} concordant).`;
            descEl.textContent = txt;
        }
    }
};
```

- [ ] **Step 2: Add HTML div for sensitivity plot**

Find the analysis tab plot grid area. After the last existing plot div pair (RoB bar, chart #16), add:

```html
<!-- Chart 17: Sensitivity Panel -->
<div class="bg-slate-900/60 rounded-2xl p-6 border border-slate-800">
    <h3 class="text-xs font-bold uppercase text-slate-500 mb-3">Sensitivity Analysis</h3>
    <div id="plot-sensitivity" class="w-full h-64"></div>
    <p id="desc-sensitivity" class="text-[11px] text-slate-500 mt-3 leading-relaxed"></p>
</div>
```

- [ ] **Step 3: Wire into runSubEngines**

In `runSubEngines` (line ~7834), after the REML chip block, add:

```javascript
// Sensitivity Panel (v12.0)
const sensitivityResult = SensitivityEngine.run(plotData, pLogOR, pSE, tau2, zCrit, confLevel, pOR, c.lci, c.uci);
```

Return it from `runSubEngines` alongside existing results.

In `runAnalysis` (line ~8002), after `CopasEngine.renderPlot(...)`, add:

```javascript
SensitivityEngine.renderChart(sub.sensitivityResult);
```

- [ ] **Step 4: Add to renderEmptyAnalysis**

In `renderEmptyAnalysis` (line ~8109), add `'plot-sensitivity'` to `plotIds` array and `'desc-sensitivity'` to `descIds` array.

- [ ] **Step 5: Run regression tests**

Run: `cd /c/Users/user/Downloads/Finrenone && python finerenone_full_regression.py`
Expected: All existing tests pass (new chart is additive, doesn't break existing).

- [ ] **Step 6: Commit**

```bash
git add FINERENONE_REVIEW.html
git commit -m "feat(v12): add SensitivityEngine with 5 robustness scenarios (C1)"
```

---

### Task 2: TSA Enhancement — OBF + Futility + RIS (C2)

**Files:**
- Modify: `FINERENONE_REVIEW.html` (renderPlots TSA section ~line 8182)

- [ ] **Step 1: Enhance TSA chart with futility boundary and RIS marker**

Replace the TSA section (chart #4, ~lines 8182-8199) in `renderPlots`:

```javascript
// 4. TSA with O'Brien-Fleming boundary (discrete, Jennison & Turnbull 2000)
const tr4 = { x: tr4X, y: tr4Y, mode: 'lines+markers', type: 'scatter', marker: { color: '#ec4899' }, name: 'Cumulative Z' };
const totalInfo = (powerResult && powerResult.available && powerResult.ris > 0) ? powerResult.ris : Math.max(...tr4X) * 1.5;
// OBF boundary: z(t) = zCrit / sqrt(t), where t = info fraction
const bUpX = [], bUpY = [], bDnX = [], bDnY = [];
const fUpX = [], fUpY = [], fDnX = [], fDnY = []; // Futility
const nPts = 50;
for (let i = 1; i <= nPts; i++) {
    const infoSize = (i / nPts) * Math.max(totalInfo, Math.max(...tr4X));
    const t = Math.min(infoSize / totalInfo, 1);
    if (t > 0.01) {
        const boundary = zCrit / Math.sqrt(t);
        bUpX.push(infoSize); bUpY.push(Math.min(boundary, zCrit * 4));
        bDnX.push(infoSize); bDnY.push(Math.max(-boundary, -zCrit * 4));
        // Approximate futility: conditional power ~ 20% region
        const thetaAlt = Math.abs(pLogOR);
        const zFut = thetaAlt * Math.sqrt(t * totalInfo) - zCrit * Math.sqrt((1 - t) / t);
        if (t > 0.1) {
            fUpX.push(infoSize); fUpY.push(Math.max(0, Math.min(zFut, zCrit)));
            fDnX.push(infoSize); fDnY.push(Math.max(-zCrit, Math.min(0, -zFut)));
        }
    }
}
const bUp = { x: bUpX, y: bUpY, mode: 'lines', line: { color: '#ef4444', dash: 'dash', width: 1.5 }, name: 'OBF boundary' };
const bDn = { x: bDnX, y: bDnY, mode: 'lines', line: { color: '#ef4444', dash: 'dash', width: 1.5 }, showlegend: false };
const fUp = { x: fUpX, y: fUpY, mode: 'lines', line: { color: '#f59e0b', dash: 'dot', width: 1 }, name: 'Approx. futility' };
const fDn = { x: fDnX, y: fDnY, mode: 'lines', line: { color: '#f59e0b', dash: 'dot', width: 1 }, showlegend: false };
const flatUp = { x: [0, Math.max(...tr4X, totalInfo)], y: [zCrit, zCrit], mode: 'lines', line: { color: '#64748b', dash: 'dot', width: 1 }, name: 'Fixed \u00b1z' };
const flatDn = { x: [0, Math.max(...tr4X, totalInfo)], y: [-zCrit, -zCrit], mode: 'lines', line: { color: '#64748b', dash: 'dot', width: 1 }, showlegend: false };
// RIS vertical marker
const risLine = (powerResult && powerResult.available && powerResult.ris < Infinity)
    ? { x: [powerResult.ris, powerResult.ris], y: [-zCrit * 3, zCrit * 3], mode: 'lines', line: { color: '#22c55e', dash: 'dashdot', width: 1 }, name: 'RIS' }
    : null;
const tsaTraces = [tr4, bUp, bDn, fUp, fDn, flatUp, flatDn];
if (risLine) tsaTraces.push(risLine);
Plotly.newPlot('plot-tsa', tsaTraces, Object.assign(layout('Information Size (Weight)', 'Z-Score'), { showlegend: true, legend: { x: 0.55, y: 0.95, font: { size: 8 } } }), PLOTLY_OPTS);
```

- [ ] **Step 2: Add stopping classification chip**

After the TSA chart render, add a chip element update:

```javascript
// TSA stopping classification
const tsaChipEl = document.getElementById('chip-tsa-status');
if (tsaChipEl) {
    const lastZ = tr4Y[tr4Y.length - 1];
    const lastInfo = tr4X[tr4X.length - 1];
    const lastIF = totalInfo > 0 ? lastInfo / totalInfo : 0;
    const obfAtLast = lastIF > 0.01 ? zCrit / Math.sqrt(lastIF) : Infinity;
    // Compute futility boundary at current IF using conditional power formula
    const thetaAltChip = Math.abs(pLogOR);
    const zFutAtLast = lastIF > 0.1 ? thetaAltChip * Math.sqrt(lastIF * totalInfo) - zCrit * Math.sqrt((1 - lastIF) / lastIF) : Infinity;
    if (Math.abs(lastZ) > obfAtLast) {
        tsaChipEl.className = 'stat-chip stat-chip-green';
        tsaChipEl.innerHTML = '<i class="fa-solid fa-check-circle" style="font-size:10px"></i> TSA: Evidence sufficient \u2014 OBF boundary crossed';
    } else if (lastIF > 0.5 && Math.abs(lastZ) < Math.max(0, zFutAtLast)) {
        tsaChipEl.className = 'stat-chip stat-chip-amber';
        tsaChipEl.innerHTML = '<i class="fa-solid fa-hourglass-half" style="font-size:10px"></i> TSA: Futility \u2014 unlikely to reach significance';
    } else {
        tsaChipEl.className = 'stat-chip stat-chip-blue';
        tsaChipEl.innerHTML = `<i class="fa-solid fa-spinner" style="font-size:10px"></i> TSA: Accruing \u2014 ${(lastIF * 100).toFixed(0)}% of required information`;
    }
}
```

- [ ] **Step 3: Add TSA chip HTML element**

In the stat-chips row (search for `chip-ris`), add after it:

```html
<span id="chip-tsa-status" class="stat-chip stat-chip-blue"><i class="fa-solid fa-spinner" style="font-size:10px"></i> TSA: --</span>
```

- [ ] **Step 4: Update desc-tsa text generation**

Replace the existing `setDesc('desc-tsa', ...)` (line ~8335) to remove "Lan-DeMets" and reference OBF correctly:

```javascript
setDesc('desc-tsa', 'Cumulative Z = ' + lastZ.toFixed(2) + ', info fraction = ' + infoFrac + '%. ' + 'O\u2019Brien-Fleming boundary at current IF = \u00b1' + obfBound + ' (red dashed). Approximate futility region in amber. Fixed boundary \u00b1' + zCrit.toFixed(2) + ' (grey dotted). ' + (crossed ? 'The Z-curve has crossed the fixed boundary.' : 'The Z-curve has not crossed either boundary, suggesting additional evidence may be needed.'));
```

- [ ] **Step 5: Run regression tests**

Run: `cd /c/Users/user/Downloads/Finrenone && python finerenone_full_regression.py`
Expected: PASS (TSA chart is re-rendered but existing goldens only check plot existence, not content).

- [ ] **Step 6: Commit**

```bash
git add FINERENONE_REVIEW.html
git commit -m "feat(v12): enhance TSA with OBF futility boundary and RIS marker (C2)"
```

---

### Task 3: GRADE Upgrades (C3)

**Files:**
- Modify: `FINERENONE_REVIEW.html` (renderGRADE ~line 8364)

- [ ] **Step 1: Add upgrade logic after totalDown calculation**

After `const totalDown = ...` (line ~8431), before the certainty assignment, add:

```javascript
// v12.0: GRADE upgrades (only applicable when starting certainty <= LOW)
const startingLevel = RapidMeta.state.config?.startingLevel ?? 'HIGH';
const startOffset = { HIGH: 0, MODERATE: 1, LOW: 2, 'VERY LOW': 3 }[startingLevel] ?? 0;
let upgradeLevel = 0;
const upgradeReasons = [];
if (startingLevel !== 'HIGH') {
    // Large effect: OR < 0.50 or OR > 2.0 with p < 0.001
    const _wSum = data.reduce((a, d) => a + d.w_random, 0);
    const mainOR = Math.exp(data.reduce((a, d) => a + d.logOR * d.w_random, 0) / _wSum);
    const mainSE = Math.sqrt(1 / _wSum);
    const mainP = 2 * (1 - normalCDF(Math.abs(Math.log(mainOR) / mainSE)));
    if ((mainOR < 0.20 || mainOR > 5.0)) {
        upgradeLevel = 2; upgradeReasons.push('very large effect (OR ' + mainOR.toFixed(2) + ')');
    } else if ((mainOR < 0.50 || mainOR > 2.0) && mainP < 0.001) {
        upgradeLevel = 1; upgradeReasons.push('large effect (OR ' + mainOR.toFixed(2) + ', p < 0.001)');
    }
    // Dose-response not implemented for finerenone (single dose) — placeholder
}
// Net level: startOffset + totalDown - upgradeLevel, clamped to [0, 3]
const netLevel = Math.max(0, Math.min(3, startOffset + totalDown - upgradeLevel));
```

Then modify the certainty assignment to use `netLevel` (0=HIGH, 1=MOD, 2=LOW, 3=VLOW):

```javascript
const certaintyMap = ['HIGH', 'MODERATE', 'LOW', 'VERY LOW'];
const badgeMap = ['grade-high', 'grade-mod', 'grade-low', 'grade-vlow'];
let certainty = certaintyMap[netLevel];
let badge = badgeMap[netLevel];
```

- [ ] **Step 2: Add upgrade display text**

After `reasonText`, add upgrade display:

```javascript
const upgradeText = startingLevel === 'HIGH'
    ? 'No upgrade criteria applicable (RCT baseline).'
    : upgradeReasons.length > 0
        ? `Upgraded +${upgradeLevel} for ${upgradeReasons.join('; ')}.`
        : 'No upgrade criteria met.';
```

Include `upgradeText` in the GRADE panel innerHTML.

- [ ] **Step 3: Run regression tests**

Expected: PASS (GRADE display changes only text, RCT baseline means no functional change).

- [ ] **Step 4: Commit**

```bash
git add FINERENONE_REVIEW.html
git commit -m "feat(v12): add GRADE upgrade criteria for observational reviews (C3)"
```

---

### Task 4: InfluenceEngine — Diagnostics (C4)

**Files:**
- Modify: `FINERENONE_REVIEW.html` (insert after SensitivityEngine, before shared Plotly config)

- [ ] **Step 1: Add InfluenceEngine object**

Insert after `SensitivityEngine`:

```javascript
// ===== v12.0: INFLUENCE & OUTLIER DIAGNOSTICS (Chart #18) =====
const InfluenceEngine = {
    run(plotData, pLogOR, pSE, tau2) {
        const k = plotData.length;
        if (k < 3) return { available: false };
        const totalW = plotData.reduce((a, d) => a + 1 / (d.vi + tau2), 0);
        const sePooled = Math.sqrt(1 / totalW);

        const results = plotData.map((d, i) => {
            const subset = plotData.filter((_, j) => j !== i);
            // LOO DL pooling
            let sW = 0, sWY = 0, sW_y2 = 0, sW2 = 0;
            subset.forEach(s => { sW += s.w_fixed; sWY += s.w_fixed * s.logOR; sW_y2 += s.w_fixed * s.logOR * s.logOR; sW2 += s.w_fixed * s.w_fixed; });
            const Q = Math.max(0, sW_y2 - sWY * sWY / sW);
            const df = subset.length - 1;
            const tau2_loo = df > 0 && Q > df ? (Q - df) / (sW - sW2 / sW) : 0;
            let swR = 0, swRY = 0;
            subset.forEach(s => { const wr = 1 / (s.vi + tau2_loo); swR += wr; swRY += wr * s.logOR; });
            const thetaLoo = swR > 0 ? swRY / swR : 0;
            const seLoo = swR > 0 ? Math.sqrt(1 / swR) : 1;

            // Hat value (leverage)
            const wi = 1 / (d.vi + tau2);
            const hat = wi / totalW;

            // Externally studentized residual (Viechtbauer & Cheung 2010)
            const rstudent = (d.logOR - thetaLoo) / Math.sqrt(d.vi + tau2_loo);

            // Cook's distance (direct from LOO)
            const cookD = Math.pow(pLogOR - thetaLoo, 2) / (sePooled * sePooled);

            // DFBETAS
            const dfbetas = (pLogOR - thetaLoo) / sePooled;

            return { id: d.id, hat, rstudent, cookD, dfbetas };
        });

        // Thresholds
        const cookThresh = 4 / k;
        const hatThresh = 2 * 2 / k; // 2(p+1)/k where p=1
        const tBonf = k > 2 ? tQuantile(1 - 0.05 / (2 * k), k - 2) : Infinity; // Bonferroni t(alpha/2k, k-2)
        const dfbetasThresh = 1;

        // Flag influential outliers (cross 2+ thresholds)
        results.forEach(r => {
            let crosses = 0;
            if (r.cookD > cookThresh) crosses++;
            if (r.hat > hatThresh) crosses++;
            if (Math.abs(r.rstudent) > tBonf) crosses++;
            if (Math.abs(r.dfbetas) > dfbetasThresh) crosses++;
            r.influential = crosses >= 2;
        });

        return { available: true, results, thresholds: { cookThresh, hatThresh, tBonf, dfbetasThresh } };
    },

    renderChart(result) {
        const el = document.getElementById('plot-influence');
        if (!el || !result || !result.available) {
            if (el) { try { Plotly.purge(el); } catch(e) {} el.innerHTML = '<div class="h-full min-h-[180px] flex items-center justify-center text-xs text-slate-500">Influence diagnostics require k \u2265 3</div>'; }
            return;
        }
        const { results: r, thresholds: t } = result;
        const ids = r.map(d => d.id);

        // 2x2 subplot grid
        const cookTrace = { x: ids, y: r.map(d => d.cookD), type: 'bar', marker: { color: r.map(d => d.cookD > t.cookThresh ? '#ef4444' : '#3b82f6') }, name: "Cook's D", xaxis: 'x', yaxis: 'y' };
        const hatTrace = { x: ids, y: r.map(d => d.hat), type: 'bar', marker: { color: r.map(d => d.hat > t.hatThresh ? '#ef4444' : '#10b981') }, name: 'Hat', xaxis: 'x2', yaxis: 'y2' };
        const rstTrace = { x: ids, y: r.map(d => d.rstudent), type: 'bar', marker: { color: r.map(d => Math.abs(d.rstudent) > t.tBonf ? '#ef4444' : '#8b5cf6') }, name: 'rstudent', xaxis: 'x3', yaxis: 'y3' };
        const dfbTrace = { x: ids, y: r.map(d => d.dfbetas), type: 'bar', marker: { color: r.map(d => Math.abs(d.dfbetas) > t.dfbetasThresh ? '#ef4444' : '#f59e0b') }, name: 'DFBETAS', xaxis: 'x4', yaxis: 'y4' };

        const lo = {
            paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#94a3b8', size: 9 },
            margin: { t: 25, b: 30, l: 50, r: 10 },
            showlegend: false,
            grid: { rows: 2, columns: 2, pattern: 'independent', xgap: 0.1, ygap: 0.12 },
            xaxis: { showticklabels: false, gridcolor: '#1e293b' },
            yaxis: { title: "Cook's D", gridcolor: '#1e293b' },
            xaxis2: { showticklabels: false, gridcolor: '#1e293b' },
            yaxis2: { title: 'Hat', gridcolor: '#1e293b' },
            xaxis3: { gridcolor: '#1e293b' },
            yaxis3: { title: 'rstudent', gridcolor: '#1e293b' },
            xaxis4: { gridcolor: '#1e293b' },
            yaxis4: { title: 'DFBETAS', gridcolor: '#1e293b' },
            annotations: [
                { text: "Cook's Distance", x: 0.22, y: 1.05, xref: 'paper', yref: 'paper', showarrow: false, font: { size: 10 } },
                { text: 'Hat Values', x: 0.78, y: 1.05, xref: 'paper', yref: 'paper', showarrow: false, font: { size: 10 } },
                { text: 'Ext. Studentized', x: 0.22, y: 0.45, xref: 'paper', yref: 'paper', showarrow: false, font: { size: 10 } },
                { text: 'DFBETAS', x: 0.78, y: 0.45, xref: 'paper', yref: 'paper', showarrow: false, font: { size: 10 } }
            ]
        };

        Plotly.newPlot('plot-influence', [cookTrace, hatTrace, rstTrace, dfbTrace], lo, PLOTLY_OPTS);

        // Description text
        const descEl = document.getElementById('desc-influence');
        if (descEl) {
            const influential = r.filter(d => d.influential);
            const topCook = r.reduce((a, b) => a.cookD > b.cookD ? a : b);
            const topHat = r.reduce((a, b) => a.hat > b.hat ? a : b);
            if (influential.length > 0) {
                descEl.textContent = `${influential.map(d => d.id).join(', ')} ${influential.length === 1 ? 'exceeds' : 'exceed'} 2+ diagnostic thresholds \u2014 flagged as influential outlier(s). ${topHat.id} has the highest leverage (hat=${topHat.hat.toFixed(2)}).`;
            } else {
                descEl.textContent = `No studies exceed 2+ diagnostic thresholds. ${topHat.id} has the highest leverage (hat=${topHat.hat.toFixed(2)}) but residual is within bounds.`;
            }
        }
    }
};
```

- [ ] **Step 2: Add HTML div for influence plot**

After the sensitivity chart div (Task 1 Step 2), add:

```html
<!-- Chart 18: Influence Diagnostics -->
<div class="bg-slate-900/60 rounded-2xl p-6 border border-slate-800">
    <h3 class="text-xs font-bold uppercase text-slate-500 mb-3">Influence & Outlier Diagnostics</h3>
    <div id="plot-influence" class="w-full h-80"></div>
    <p id="desc-influence" class="text-[11px] text-slate-500 mt-3 leading-relaxed"></p>
</div>
```

- [ ] **Step 3: Wire into runSubEngines and runAnalysis**

In `runSubEngines`, add:

```javascript
// Influence Diagnostics (v12.0)
const influenceResult = InfluenceEngine.run(plotData, pLogOR, pSE, tau2);
```

Return it. In `runAnalysis` after `SensitivityEngine.renderChart(...)`:

```javascript
InfluenceEngine.renderChart(sub.influenceResult);
```

- [ ] **Step 4: Add to renderEmptyAnalysis**

Add `'plot-influence'` to `plotIds` array and `'desc-influence'` to `descIds` array.

- [ ] **Step 5: Run regression tests**

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add FINERENONE_REVIEW.html
git commit -m "feat(v12): add InfluenceEngine with Cook's D, hat, rstudent, DFBETAS (C4)"
```

---

## Chunk 2: Tier D — Provenance & Automation

### Task 5: Per-Number Provenance Layer (D1)

**Files:**
- Modify: `FINERENONE_REVIEW.html` (ExtractEngine section ~line 6001)

- [ ] **Step 1: Add provenance builder to ExtractEngine**

After `ExtractEngine`'s existing methods, add `_buildProvenance`:

```javascript
_buildProvenance(trial) {
    if (!trial.data || !trial.evidence) return;
    const prov = {};
    const fields = ['tE', 'tN', 'cE', 'cN', 'pubHR', 'pubHR_LCI', 'pubHR_UCI'];
    fields.forEach(field => {
        const val = trial.data[field];
        if (val == null) return;
        const valStr = String(val);
        // Search evidence panels for snippets containing this number
        let bestSnippet = null, bestSource = null, bestUrl = null, bestConf = 0, bestOffset = null;
        (trial.evidence ?? []).forEach(ev => {
            const texts = [ev.text, ev.fullText].filter(Boolean);
            texts.forEach(txt => {
                // Use word-boundary regex to avoid false positives (e.g., "520" in "2520")
                const re = new RegExp('\\b' + valStr.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b');
                const m = re.exec(txt);
                const idx = m ? m.index : -1;
                if (idx >= 0) {
                    const start = Math.max(0, idx - 40);
                    const end = Math.min(txt.length, idx + valStr.length + 40);
                    const snippet = '...' + txt.slice(start, end) + '...';
                    const conf = ev.source === 'CT.gov' ? 98 : ev.source === 'PubMed' ? 90 : 80;
                    if (conf > bestConf) {
                        bestSnippet = snippet;
                        bestSource = `${ev.source} ${trial.id}`;
                        bestUrl = ev.url ?? null;
                        bestConf = conf;
                        bestOffset = [idx, idx + valStr.length];
                    }
                }
            });
        });
        prov[field] = {
            snippet: bestSnippet,
            source: bestSource,
            sourceUrl: bestUrl,
            charOffset: bestOffset,
            confidence: bestConf || 0,
            verifiedBy: null,
            verifiedTs: null
        };
    });
    trial.data._provenance = prov;
},
```

- [ ] **Step 2: Call _buildProvenance after extraction**

In `ExtractEngine.confirmExtract()` or wherever trial data is committed, add:

```javascript
this._buildProvenance(trial);
```

Also call it for landmark/realData trials during `ensureCanonicalAnalysisSeed()`.

- [ ] **Step 3: Add provenance dot rendering to extraction cards**

In the extraction card cell rendering, after each value cell, add a coloured dot:

```javascript
// After rendering each cell value:
const provStatus = trial.data._provenance?.[field];
const dotColor = provStatus?.verifiedBy ? '#22c55e' : provStatus?.snippet ? '#eab308' : '#64748b';
const dotTitle = provStatus?.verifiedBy ? 'Verified' : provStatus?.snippet ? 'Auto-sourced' : 'No source';
// Append: <span class="prov-dot" style="background:${dotColor}" title="${dotTitle}" data-field="${field}" data-trial="${trial.id}"></span>
```

- [ ] **Step 4: Add provenance popover component**

Add CSS class `.prov-dot` and popover logic:

```css
.prov-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-left: 4px; cursor: pointer; vertical-align: middle; }
```

Click handler on `.prov-dot` opens a positioned popover:

```javascript
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('prov-dot')) {
        const field = e.target.dataset.field;
        const trialId = e.target.dataset.trial;
        const trial = RapidMeta.state.trials.find(t => t.id === trialId);
        const prov = trial?.data?._provenance?.[field];
        // Show/create popover with snippet, source, verify/flag buttons
        showProvenancePopover(e.target, prov, field, trialId);
    }
});
```

- [ ] **Step 5: Add verification progress bar**

In each extraction card header, add:

```javascript
const totalFields = Object.keys(trial.data._provenance ?? {}).length;
const verified = Object.values(trial.data._provenance ?? {}).filter(p => p.verifiedBy).length;
// Render: Provenance: ${verified}/${totalFields} verified
```

- [ ] **Step 6: Run regression tests**

Expected: PASS (provenance is additive metadata, doesn't affect analysis values).

- [ ] **Step 7: Commit**

```bash
git add FINERENONE_REVIEW.html
git commit -m "feat(v12): add per-number provenance layer with snippets and verification (D1)"
```

---

### Task 6: Source Verification Shortcuts (D2)

**Files:**
- Modify: `FINERENONE_REVIEW.html` (ScreenEngine ~line 4918)

- [ ] **Step 1: Add source badges and "View Record" to screening cards**

In `ScreenEngine.render()`, extend the card template to include:

```javascript
// Source badge row
const sources = trial.source ?? [];
const sourceBadges = ['CT.gov', 'PubMed', 'OpenAlex']
    .filter(s => (typeof sources === 'string' ? sources : '').includes(s) || (Array.isArray(sources) ? sources.includes(s) : false))
    .map(s => `<span class="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">${escapeHtml(s)}</span>`)
    .join(' ');
// "View Record" button using _allSourceLinks
const links = ExtractEngine._allSourceLinks(trial.id + ' ' + (trial.source ?? ''));
const viewBtn = links.length > 0 ? links.map(l => `<a href="${escapeHtml(l.url)}" target="_blank" rel="noopener" class="text-[9px] text-blue-400 hover:underline">${escapeHtml(l.label)}</a>`).join(' ') : '';
```

- [ ] **Step 2: Add "Show Full Abstract" toggle**

```javascript
// Abstract toggle
const hasAbstract = trial.abstract && trial.abstract.length > 50;
const abstractToggle = hasAbstract
    ? `<button class="text-[9px] text-slate-500 hover:text-slate-300 mt-1" onclick="this.nextElementSibling.classList.toggle('hidden')">Show Full Abstract</button>
       <div class="hidden text-[10px] text-slate-500 mt-1 leading-relaxed max-h-32 overflow-y-auto">${escapeHtml(trial.abstract)}</div>`
    : '';
```

- [ ] **Step 3: Run regression tests**

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add FINERENONE_REVIEW.html
git commit -m "feat(v12): add source badges and record links to screening cards (D2)"
```

---

### Task 7: Endpoint Auto-Resolution Improvements (D3)

**Files:**
- Modify: `FINERENONE_REVIEW.html` (AutoExtractEngine ~line 5235)

- [ ] **Step 1: Add ENDPOINT_BRIDGES lookup**

At the top of `AutoExtractEngine`, add:

```javascript
ENDPOINT_BRIDGES: {
    MACE: ['cardiovascular death, nonfatal myocardial infarction, nonfatal stroke', 'composite of cv death, mi, stroke', 'first mace event', 'major adverse cardiovascular event'],
    Renal40: ['sustained decrease in egfr of >= 40%', 'kidney failure, sustained egfr decline', 'composite renal endpoint', 'sustained 40% decline in egfr'],
    ACM: ['all-cause mortality', 'death from any cause', 'overall survival'],
    ACH: ['hospitalization for heart failure', 'hf hospitalization', 'heart failure event'],
    HF_CV_First: ['worsening heart failure event or cardiovascular death', 'composite of hf event or cv death'],
    KidneyComp: ['kidney composite', 'sustained egfr decline or kidney failure', 'renal composite'],
    Hyperkalemia: ['hyperkalemia', 'serum potassium > 5.5', 'potassium elevation']
},
```

- [ ] **Step 2: Add hierarchical matching in endpoint resolution**

Extend the existing outcome matching logic to use 3 tiers:

```javascript
_resolveEndpoint(measure, outcomeKey) {
    const text = String(measure).toLowerCase();
    // Tier 1: Exact keyword in primary outcome
    const directKeywords = { MACE: ['mace', 'cardiovascular composite'], Renal40: ['egfr', 'renal', 'kidney'], ACM: ['death', 'mortality'], ACH: ['heart failure', 'hf hospitalization'], Hyperkalemia: ['hyperkalemia', 'potassium'] };
    for (const [key, kws] of Object.entries(directKeywords)) {
        if (kws.some(kw => text.includes(kw))) return { match: key, tier: 1, confidence: 95 };
    }
    // Tier 2: Semantic bridge
    for (const [key, phrases] of Object.entries(this.ENDPOINT_BRIDGES)) {
        if (phrases.some(p => text.includes(p))) return { match: key, tier: 2, confidence: 87 };
    }
    // Tier 3: Ambiguous
    return { match: null, tier: 3, confidence: 0 };
},
```

- [ ] **Step 3: Add resolution audit trail to evidence panel**

When auto-resolved, add text to evidence panel:

```javascript
// In evidence panel generation:
if (resolution.tier <= 2) {
    ev.text += ` [Endpoint auto-matched: '${measure}' \u2192 ${resolution.match} (Tier ${resolution.tier}, confidence ${resolution.confidence}%)]`;
}
```

- [ ] **Step 4: Run regression tests**

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add FINERENONE_REVIEW.html
git commit -m "feat(v12): add hierarchical endpoint matching with bridges (D3)"
```

---

### Task 8: Living Pipeline Hardening (D4)

**Files:**
- Modify: `FINERENONE_REVIEW.html` (SearchEngine ~line 4603, header area)

- [ ] **Step 1: Add stale detection banner**

After app initialization, add stale check:

```javascript
// In RapidMeta.init() or app load handler:
const lastSearch = RapidMeta.state.searchLog?.[RapidMeta.state.searchLog.length - 1]?.timestamp;
if (lastSearch) {
    const daysSince = Math.floor((Date.now() - new Date(lastSearch).getTime()) / 86400000);
    if (daysSince > 30) {
        const banner = document.getElementById('stale-banner');
        if (banner) {
            banner.classList.remove('hidden');
            banner.innerHTML = `<i class="fa-solid fa-triangle-exclamation mr-2"></i> Last acquisition: ${daysSince} days ago. New trials may have been published. <button onclick="RapidMeta.switchTab('search')" class="underline ml-2">Re-run now</button> <button onclick="this.closest('.stale-banner').classList.add('hidden')" class="ml-2 text-slate-400">\u2715</button>`;
        }
    }
}
```

- [ ] **Step 2: Add banner HTML element**

In the header area:

```html
<div id="stale-banner" class="hidden stale-banner bg-amber-900/50 border border-amber-700 text-amber-300 text-xs p-3 rounded-xl mb-4"></div>
```

- [ ] **Step 3: Add delta-on-re-acquisition in SearchEngine**

In `SearchEngine.search()`, after fetching new results, compare with stored:

```javascript
compareWithStored(newTrials, storedTrials) {
    const storedIds = new Set(storedTrials.map(t => t.id));
    const newIds = new Set(newTrials.map(t => t.id));
    const added = newTrials.filter(t => !storedIds.has(t.id));
    const removed = storedTrials.filter(t => !newIds.has(t.id));
    return { added, removed };
},
```

Mark new trials with `trial._delta = 'NEW'` badge. Mark disappeared with `trial._delta = 'WITHDRAWN'`.

- [ ] **Step 4: Render delta badges in screening cards**

```javascript
// In ScreenEngine card template:
const deltaBadge = trial._delta === 'NEW' ? '<span class="text-[9px] px-1.5 py-0.5 rounded bg-emerald-800 text-emerald-300 ml-1">NEW</span>' : trial._delta === 'WITHDRAWN' ? '<span class="text-[9px] px-1.5 py-0.5 rounded bg-red-800 text-red-300 ml-1">WITHDRAWN</span>' : '';
```

- [ ] **Step 5: Run regression tests**

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add FINERENONE_REVIEW.html
git commit -m "feat(v12): add stale detection and delta-on-re-acquisition (D4)"
```

---

## Chunk 3: Tier A — Submission Artifacts

### Task 9: PRISMA 2020 Flow Diagram (A1)

**Files:**
- Modify: `FINERENONE_REVIEW.html` (new PrismaEngine object + Report tab extension)

- [ ] **Step 1: Add PrismaEngine object**

Insert after `InfluenceEngine`:

```javascript
// ===== v12.0: PRISMA 2020 FLOW DIAGRAM =====
const PrismaEngine = {
    generate() {
        const s = RapidMeta.state;
        const searchLog = s.searchLog ?? [];
        const trials = s.trials ?? [];
        // Identification
        const ctgovN = searchLog.filter(l => l.source === 'registry').reduce((a, l) => a + (l.count ?? 0), 0);
        const pubmedN = searchLog.filter(l => l.source === 'pubmed').reduce((a, l) => a + (l.count ?? 0), 0);
        const oaN = searchLog.filter(l => l.source === 'openalex').reduce((a, l) => a + (l.count ?? 0), 0);
        const landmarkN = trials.filter(t => t.source === 'reference').length;
        const totalIdent = ctgovN + pubmedN + oaN + landmarkN;
        // Screening
        const afterDedup = trials.length;
        const dupRemoved = totalIdent - afterDedup;
        const excluded = trials.filter(t => t.status === 'exclude').length;
        const screened = afterDedup;
        // Included
        const included = trials.filter(t => t.status === 'include' && t.data).length;
        const pendingData = trials.filter(t => t.status === 'include' && !t.data).length;

        // Eligibility — excluded by reason
        const excludedPhaseII = trials.filter(t => t.status === 'exclude' && (t.data?.phase === 'II' || t.data?.phase === 'I')).length;
        const excludedZeroEvent = trials.filter(t => t.status === 'exclude' && t.data && t.data.tE === 0 && t.data.cE === 0).length;
        const excludedOther = excluded - excludedPhaseII - excludedZeroEvent;

        return { ctgovN, pubmedN, oaN, landmarkN, totalIdent, dupRemoved, afterDedup, screened, excluded, included, pendingData, excludedPhaseII, excludedZeroEvent, excludedOther };
    },

    renderSVG(data) {
        const w = 700, h = 580;
        const box = (x, y, bw, bh, text, count) => {
            return `<rect x="${x}" y="${y}" width="${bw}" height="${bh}" rx="4" fill="#1e293b" stroke="#334155" stroke-width="1.5"/>
                    <text x="${x + bw/2}" y="${y + bh/2 - 6}" text-anchor="middle" fill="#e2e8f0" font-size="11" font-family="system-ui">${escapeHtml(text)}</text>
                    <text x="${x + bw/2}" y="${y + bh/2 + 10}" text-anchor="middle" fill="#94a3b8" font-size="10" font-family="system-ui">(n=${count})</text>`;
        };
        const arrow = (x1, y1, x2, y2) => `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#64748b" stroke-width="1.5" marker-end="url(#arrowhead)"/>`;

        const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" class="w-full">
            <defs><marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#64748b"/></marker></defs>
            <!-- Identification -->
            <text x="10" y="30" fill="#94a3b8" font-size="12" font-weight="bold" font-family="system-ui">IDENTIFICATION</text>
            ${box(30, 45, 180, 50, 'CT.gov', data.ctgovN)}
            ${box(230, 45, 180, 50, 'Europe PMC', data.pubmedN)}
            ${box(430, 45, 180, 50, 'OpenAlex', data.oaN)}
            ${arrow(120, 95, 350, 120)}
            ${arrow(320, 95, 350, 120)}
            ${arrow(520, 95, 350, 120)}
            <!-- Dedup -->
            ${box(250, 120, 200, 45, 'After deduplication', data.afterDedup)}
            <text x="${w-30}" y="145" text-anchor="end" fill="#64748b" font-size="9" font-family="system-ui">Duplicates removed: ${data.dupRemoved}</text>
            ${arrow(350, 165, 350, 195)}
            <!-- Screening -->
            <text x="10" y="210" fill="#94a3b8" font-size="12" font-weight="bold" font-family="system-ui">SCREENING</text>
            ${box(250, 195, 200, 45, 'Records screened', data.screened)}
            ${box(500, 200, 150, 40, 'Excluded', data.excluded)}
            ${arrow(450, 217, 500, 220)}
            ${arrow(350, 240, 350, 275)}
            <!-- Eligibility -->
            <text x="10" y="290" fill="#94a3b8" font-size="12" font-weight="bold" font-family="system-ui">ELIGIBILITY</text>
            ${box(250, 295, 200, 45, 'Full-text assessed', data.screened - data.excluded)}
            ${box(500, 295, 160, 50, 'Excluded', data.excluded)}
            <text x="505" y="360" fill="#64748b" font-size="8" font-family="system-ui">Phase I/II: ${data.excludedPhaseII}</text>
            <text x="505" y="372" fill="#64748b" font-size="8" font-family="system-ui">Zero events: ${data.excludedZeroEvent}</text>
            <text x="505" y="384" fill="#64748b" font-size="8" font-family="system-ui">Other: ${data.excludedOther}</text>
            ${arrow(450, 317, 500, 320)}
            ${arrow(350, 340, 350, 375)}
            <!-- Included -->
            <text x="10" y="390" fill="#94a3b8" font-size="12" font-weight="bold" font-family="system-ui">INCLUDED</text>
            ${box(220, 395, 260, 50, 'Studies in quantitative synthesis', data.included)}
            ${data.pendingData > 0 ? `<text x="350" y="465" text-anchor="middle" fill="#f59e0b" font-size="9" font-family="system-ui">${data.pendingData} included but awaiting data</text>` : ''}
        </svg>`;
        return svg;
    },

    renderToElement(containerId) {
        const data = this.generate();
        const el = document.getElementById(containerId);
        if (el) el.innerHTML = this.renderSVG(data);
    },

    exportSVG() {
        const data = this.generate();
        const svg = this.renderSVG(data);
        const blob = new Blob([svg], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = 'prisma_2020_flow.svg';
        document.body.appendChild(a); a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    },

    exportPNG(dpi = 300) {
        const data = this.generate();
        const svg = this.renderSVG(data);
        const canvas = document.createElement('canvas');
        const scale = dpi / 96;
        canvas.width = 700 * scale; canvas.height = 500 * scale;
        const ctx = canvas.getContext('2d');
        ctx.scale(scale, scale);
        const img = new Image();
        const blob = new Blob([svg], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        img.onload = () => {
            ctx.drawImage(img, 0, 0);
            URL.revokeObjectURL(url);
            canvas.toBlob(pngBlob => {
                const pngUrl = URL.createObjectURL(pngBlob);
                const a = document.createElement('a');
                a.href = pngUrl; a.download = 'prisma_2020_flow.png';
                document.body.appendChild(a); a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(pngUrl);
            }, 'image/png');
        };
        img.src = url;
    }
};
```

- [ ] **Step 2: Add PRISMA section to Report tab**

In the Report tab HTML (search for `report-content`), add:

```html
<div class="mt-6">
    <h3 class="text-sm font-bold text-slate-300 mb-3">PRISMA 2020 Flow Diagram</h3>
    <div id="prisma-flow-container" class="bg-slate-950/50 rounded-xl p-4 border border-slate-800"></div>
    <div class="flex gap-2 mt-2">
        <button onclick="PrismaEngine.exportSVG()" class="text-[10px] px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700">Download SVG</button>
        <button onclick="PrismaEngine.exportPNG()" class="text-[10px] px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700">Download PNG (300 DPI)</button>
    </div>
</div>
```

- [ ] **Step 3: Call PrismaEngine in report generation**

In `ReportEngine.generate()`, add:

```javascript
PrismaEngine.renderToElement('prisma-flow-container');
```

- [ ] **Step 4: Run regression tests**

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add FINERENONE_REVIEW.html
git commit -m "feat(v12): add PRISMA 2020 flow diagram with SVG/PNG export (A1)"
```

---

### Task 10: Publication-Quality Forest Plot Export (A2)

**Files:**
- Modify: `FINERENONE_REVIEW.html` (new ForestExportEngine)

- [ ] **Step 1: Add ForestExportEngine**

```javascript
// ===== v12.0: PUBLICATION-QUALITY FOREST PLOT EXPORT =====
const ForestExportEngine = {
    buildSVG(plotData, pLogOR, pSE, tau2, zCrit, I2, confLevel, hksjLCI, hksjUCI, piLCI, piUCI) {
        const k = plotData.length;
        const emS = RapidMeta.emLabel('short');
        const pOR = Math.exp(pLogOR);
        const lci = Math.exp(pLogOR - zCrit * pSE);
        const uci = Math.exp(pLogOR + zCrit * pSE);
        const totalW = plotData.reduce((a, d) => a + 1 / (d.vi + tau2), 0);

        // Layout constants (in mm, converted to SVG units at 1mm = 3.78px)
        const mmToPx = 3.78;
        const W = 180 * mmToPx; // 180mm journal width
        const rowH = 18;
        const headerH = 30;
        const footerH = 60;
        const H = headerH + k * rowH + rowH + footerH; // +1 for pooled row

        // Column positions
        const colStudy = 10;
        const colPlotLeft = 220;
        const colPlotRight = 460;
        const colOR = 480;
        const colWeight = 590;

        // Scale for plot area
        const allVals = plotData.flatMap(d => [Math.exp(d.logOR - zCrit * d.se), Math.exp(d.logOR + zCrit * d.se)]).concat([lci, uci]);
        const minVal = Math.min(...allVals) * 0.8;
        const maxVal = Math.max(...allVals) * 1.2;
        const logMin = Math.log(minVal);
        const logMax = Math.log(maxVal);
        const xScale = (logVal) => colPlotLeft + (logVal - logMin) / (logMax - logMin) * (colPlotRight - colPlotLeft);

        let svgContent = '';
        // Header
        svgContent += `<text x="${colStudy}" y="15" font-size="9" font-weight="bold" fill="#1e293b" font-family="Georgia,serif">Study</text>`;
        svgContent += `<text x="${(colPlotLeft + colPlotRight) / 2}" y="15" text-anchor="middle" font-size="9" font-weight="bold" fill="#1e293b" font-family="Georgia,serif">${emS} (${Math.round(confLevel * 100)}% CI)</text>`;
        svgContent += `<text x="${colOR}" y="15" font-size="9" font-weight="bold" fill="#1e293b" font-family="Georgia,serif">${emS} [CI]</text>`;
        svgContent += `<text x="${colWeight}" y="15" font-size="9" font-weight="bold" fill="#1e293b" font-family="Georgia,serif">Weight</text>`;
        svgContent += `<line x1="${colStudy}" y1="${headerH - 5}" x2="${W - 10}" y2="${headerH - 5}" stroke="#1e293b" stroke-width="0.5"/>`;

        // Null line
        const nullX = xScale(0);
        svgContent += `<line x1="${nullX}" y1="${headerH}" x2="${nullX}" y2="${headerH + k * rowH + rowH}" stroke="#999" stroke-width="0.5" stroke-dasharray="3,3"/>`;

        // Study rows
        plotData.forEach((d, i) => {
            const y = headerH + i * rowH + rowH / 2;
            const or = Math.exp(d.logOR);
            const lo = Math.exp(d.logOR - zCrit * d.se);
            const hi = Math.exp(d.logOR + zCrit * d.se);
            const weight = ((1 / (d.vi + tau2)) / totalW * 100);
            const sqSize = Math.max(4, Math.min(12, weight / 5));

            // Whisker
            svgContent += `<line x1="${xScale(Math.log(lo))}" y1="${y}" x2="${xScale(Math.log(hi))}" y2="${y}" stroke="#1e293b" stroke-width="1"/>`;
            // Square (weighted)
            svgContent += `<rect x="${xScale(d.logOR) - sqSize / 2}" y="${y - sqSize / 2}" width="${sqSize}" height="${sqSize}" fill="#1e293b"/>`;
            // Labels
            svgContent += `<text x="${colStudy}" y="${y + 3}" font-size="8" fill="#1e293b" font-family="Georgia,serif">${escapeHtml(d.id)}</text>`;
            svgContent += `<text x="${colOR}" y="${y + 3}" font-size="8" fill="#1e293b" font-family="Georgia,serif">${or.toFixed(2)} [${lo.toFixed(2)}, ${hi.toFixed(2)}]</text>`;
            svgContent += `<text x="${colWeight}" y="${y + 3}" font-size="8" fill="#1e293b" font-family="Georgia,serif">${weight.toFixed(1)}%</text>`;
        });

        // Pooled diamond
        const pooledY = headerH + k * rowH + rowH / 2;
        const dLeft = xScale(Math.log(lci));
        const dRight = xScale(Math.log(uci));
        const dCenter = xScale(pLogOR);
        svgContent += `<polygon points="${dLeft},${pooledY} ${dCenter},${pooledY - 6} ${dRight},${pooledY} ${dCenter},${pooledY + 6}" fill="#ef4444" stroke="#ef4444" stroke-width="0.5"/>`;
        svgContent += `<text x="${colStudy}" y="${pooledY + 3}" font-size="8" font-weight="bold" fill="#1e293b" font-family="Georgia,serif">Pooled (RE)</text>`;
        svgContent += `<text x="${colOR}" y="${pooledY + 3}" font-size="8" font-weight="bold" fill="#1e293b" font-family="Georgia,serif">${pOR.toFixed(2)} [${lci.toFixed(2)}, ${uci.toFixed(2)}]</text>`;

        // Footer
        const footerY = headerH + (k + 1) * rowH + 15;
        svgContent += `<line x1="${colStudy}" y1="${footerY - 10}" x2="${W - 10}" y2="${footerY - 10}" stroke="#1e293b" stroke-width="0.5"/>`;
        svgContent += `<text x="${colStudy}" y="${footerY}" font-size="7" fill="#666" font-family="Georgia,serif">I\u00B2 = ${I2.toFixed(1)}%, \u03C4\u00B2 = ${tau2.toFixed(4)}, Q p = ${(RapidMeta.state.results?.qPvalue ?? '--')}</text>`;

        const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" style="background:white">${svgContent}</svg>`;
        return svg;
    },

    exportSVG(plotData, pLogOR, pSE, tau2, zCrit, I2, confLevel, hksjLCI, hksjUCI, piLCI, piUCI) {
        const svg = this.buildSVG(plotData, pLogOR, pSE, tau2, zCrit, I2, confLevel, hksjLCI, hksjUCI, piLCI, piUCI);
        const blob = new Blob([svg], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url; a.download = 'forest_plot.svg';
        document.body.appendChild(a); a.click(); document.body.removeChild(a); URL.revokeObjectURL(url);
    },

    exportPNG(plotData, pLogOR, pSE, tau2, zCrit, I2, confLevel, hksjLCI, hksjUCI, piLCI, piUCI, dpi = 300) {
        const svg = this.buildSVG(plotData, pLogOR, pSE, tau2, zCrit, I2, confLevel, hksjLCI, hksjUCI, piLCI, piUCI);
        const canvas = document.createElement('canvas');
        const scale = dpi / 96;
        // Parse SVG dimensions dynamically (match the buildSVG output)
        const k = plotData.length;
        const svgW = 180 * 3.78;
        const svgH = 30 + k * 18 + 18 + 60; // headerH + k*rowH + pooledRow + footerH
        canvas.width = Math.ceil(svgW * scale); canvas.height = Math.ceil(svgH * scale);
        const ctx = canvas.getContext('2d');
        ctx.scale(scale, scale);
        const img = new Image();
        const blob = new Blob([svg], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        img.onload = () => {
            ctx.fillStyle = 'white'; ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0); URL.revokeObjectURL(url);
            canvas.toBlob(pngBlob => {
                const pUrl = URL.createObjectURL(pngBlob);
                const a = document.createElement('a'); a.href = pUrl; a.download = 'forest_plot.png';
                document.body.appendChild(a); a.click(); document.body.removeChild(a); URL.revokeObjectURL(pUrl);
            }, 'image/png');
        };
        img.src = url;
    }
};
```

- [ ] **Step 2: Add export buttons to analysis tab**

Below the existing forest plot div, add:

```html
<div class="flex gap-2 mt-2">
    <button id="btn-forest-svg" class="text-[10px] px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700">Export Forest SVG</button>
    <button id="btn-forest-png" class="text-[10px] px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700">Export Forest PNG (300 DPI)</button>
</div>
```

Wire click handlers in `runAnalysis` after `renderPlots`:

```javascript
document.getElementById('btn-forest-svg')?.addEventListener('click', () => ForestExportEngine.exportSVG(c.plotData, c.pLogOR, c.pSE, c.tau2, c.zCrit, c.I2, c.confLevel, c.hksjLCI, c.hksjUCI, c.piLCI, c.piUCI));
document.getElementById('btn-forest-png')?.addEventListener('click', () => ForestExportEngine.exportPNG(c.plotData, c.pLogOR, c.pSE, c.tau2, c.zCrit, c.I2, c.confLevel, c.hksjLCI, c.hksjUCI, c.piLCI, c.piUCI));
```

- [ ] **Step 3: Run regression tests**

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add FINERENONE_REVIEW.html
git commit -m "feat(v12): add publication-quality forest plot SVG/PNG export (A2)"
```

---

### Task 11: GRADE Evidence Profile Table (A3)

**Files:**
- Modify: `FINERENONE_REVIEW.html` (new GradeProfileEngine)

- [ ] **Step 1: Add GradeProfileEngine**

```javascript
// ===== v12.0: GRADE EVIDENCE PROFILE TABLE =====
const GradeProfileEngine = {
    generateAll() {
        const outcomes = RapidMeta.getAvailableOutcomes();
        const rows = [];
        const savedOutcome = RapidMeta.state.selectedOutcome;
        outcomes.forEach(oc => {
            RapidMeta.setOutcome(oc.key);
            const trials = RapidMeta.getScopedIncludedTrials({ requireData: true });
            if (trials.length === 0) return;
            const c = AnalysisEngine.computeCore(trials);
            if (!c.plotData || c.plotData.length === 0) return;
            // Compute absolute effects via direct transformation
            const cer = c.plotData.reduce((a, d) => a + d.cer * (d.tN + d.cN), 0) / c.plotData.reduce((a, d) => a + d.tN + d.cN, 0);
            const orPt = c.pOR;
            const orLo = c.lci;
            const orHi = c.uci;
            const emS = RapidMeta.emLabel('short');
            let ierPt, ierLo, ierHi;
            if (emS === 'HR') {
                ierPt = 1 - Math.pow(1 - cer, orPt);
                ierLo = 1 - Math.pow(1 - cer, orHi); // bounds swap for HR
                ierHi = 1 - Math.pow(1 - cer, orLo);
            } else if (emS === 'RR') {
                ierPt = cer * orPt;
                ierLo = cer * orLo;
                ierHi = cer * orHi;
            } else {
                ierPt = cer * orPt / (1 - cer + cer * orPt);
                ierLo = cer * orLo / (1 - cer + cer * orLo);
                ierHi = cer * orHi / (1 - cer + cer * orHi);
            }
            const ardPt = Math.round((ierPt - cer) * 1000);
            const ardLo = Math.round((ierLo - cer) * 1000);
            const ardHi = Math.round((ierHi - cer) * 1000);
            rows.push({
                outcome: oc.label,
                k: c.k,
                certainty: this._getGradeCertainty(c),
                relativeEffect: `${emS} ${orPt.toFixed(2)} [${orLo.toFixed(2)}, ${orHi.toFixed(2)}]`,
                cerPer1000: Math.round(cer * 1000),
                ardPer1000: `${ardPt} (${ardLo} to ${ardHi})`,
                plain: this._plainLanguage(orPt, orLo, orHi, oc.label)
            });
        });
        // Restore original outcome
        if (savedOutcome) RapidMeta.setOutcome(savedOutcome);
        return rows;
    },

    _getGradeCertainty(c) {
        // Compute GRADE certainty independently (not from DOM) for multi-outcome iteration
        const k = c.k;
        const I2 = c.I2;
        const piLCI = c.piLCI;
        const piUCI = c.piUCI;
        const lci = c.lci;
        const uci = c.uci;
        const hksjLCI = c.hksjLCI;
        const hksjUCI = c.hksjUCI;
        let totalDown = 0;
        // RoB: simplified — check if any study has high rob
        const hasHighRoB = c.plotData.some(d => d.rob && d.rob.includes('high'));
        if (hasHighRoB) totalDown++;
        // Inconsistency
        const piCrossesNull = isFinite(piLCI) && isFinite(piUCI) && piLCI < 1 && piUCI > 1;
        if (I2 >= 50 || piCrossesNull) totalDown++;
        // Imprecision
        const _impLCI = Number.isFinite(hksjLCI) ? hksjLCI : lci;
        const _impUCI = Number.isFinite(hksjUCI) ? hksjUCI : uci;
        if ((_impLCI < 1 && _impUCI > 1) && (_impLCI < 0.80 || _impUCI > 1.25)) totalDown++;
        else if (Math.log(_impUCI) - Math.log(_impLCI) > 1.0) totalDown++;
        // Map
        const certaintyMap = ['HIGH', 'MODERATE', 'LOW', 'VERY LOW'];
        return certaintyMap[Math.min(totalDown, 3)];
    },

    _plainLanguage(or, lci, uci, outcome) {
        const ocLow = outcome.toLowerCase();
        if (lci < 1 && uci < 1) {
            const pct = Math.round((1 - or) * 100);
            return `Finerenone probably reduces ${ocLow} by about ${pct}%.`;
        } else if (lci > 1 && uci > 1) {
            const pct = Math.round((or - 1) * 100);
            return `Finerenone may increase ${ocLow} by about ${pct}%.`;
        }
        return `Finerenone may result in little to no difference in ${ocLow}.`;
    },

    renderTable(containerId) {
        const rows = this.generateAll();
        const el = document.getElementById(containerId);
        if (!el) return;
        const gradeSymbols = { HIGH: '\u2295\u2295\u2295\u2295', MODERATE: '\u2295\u2295\u2295\u2296', LOW: '\u2295\u2295\u2296\u2296', 'VERY LOW': '\u2295\u2296\u2296\u2296', NR: '--' };
        const html = `<table class="w-full text-[10px] border-collapse">
            <thead><tr class="bg-slate-800 text-slate-400">
                <th class="p-2 text-left">Outcome</th><th class="p-2">k</th><th class="p-2">Certainty</th>
                <th class="p-2">Relative effect</th><th class="p-2">Control risk/1000</th><th class="p-2">ARD/1000 (CI)</th>
                <th class="p-2 text-left">Plain language</th>
            </tr></thead>
            <tbody>${rows.map(r => `<tr class="border-b border-slate-800">
                <td class="p-2 text-slate-300">${escapeHtml(r.outcome)}</td>
                <td class="p-2 text-center">${r.k}</td>
                <td class="p-2 text-center">${r.certainty} ${gradeSymbols[r.certainty] ?? ''}</td>
                <td class="p-2 font-mono text-center">${escapeHtml(r.relativeEffect)}</td>
                <td class="p-2 text-center">${r.cerPer1000}</td>
                <td class="p-2 text-center font-mono">${r.ardPer1000}</td>
                <td class="p-2 text-slate-400 italic">${escapeHtml(r.plain)}</td>
            </tr>`).join('')}</tbody>
        </table>`;
        el.innerHTML = html;
    },

    exportCSV() {
        const rows = this.generateAll();
        const header = 'Outcome,k,Certainty,Relative Effect,Control Risk per 1000,ARD per 1000,Plain Language';
        const csv = [header, ...rows.map(r => `"${r.outcome}",${r.k},"${r.certainty}","${r.relativeEffect}",${r.cerPer1000},"${r.ardPer1000}","${r.plain}"`)].join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url; a.download = 'grade_evidence_profile.csv';
        document.body.appendChild(a); a.click(); document.body.removeChild(a); URL.revokeObjectURL(url);
    }
};
```

- [ ] **Step 2: Add GRADE profile section to Report tab**

```html
<div class="mt-6">
    <h3 class="text-sm font-bold text-slate-300 mb-3">GRADE Evidence Profile (Summary of Findings)</h3>
    <div id="grade-profile-container" class="overflow-x-auto"></div>
    <div class="flex gap-2 mt-2">
        <button onclick="GradeProfileEngine.renderTable('grade-profile-container')" class="text-[10px] px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700">Generate</button>
        <button onclick="GradeProfileEngine.exportCSV()" class="text-[10px] px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700">Export CSV</button>
    </div>
</div>
```

- [ ] **Step 3: Run regression tests**

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add FINERENONE_REVIEW.html
git commit -m "feat(v12): add GRADE evidence profile with absolute effects (A3)"
```

---

### Task 12: Reproducibility Capsule ZIP (A4) + Seal Extension + Audit Log (A5)

**Files:**
- Modify: `FINERENONE_REVIEW.html` (DataSealEngine extension + new CapsuleEngine + ZIP builder)

- [ ] **Step 1: Extend DataSealEngine to include HR and RoB**

In `DataSealEngine.computeSeal()` (line ~7577), extend canonical data:

```javascript
.map(t => ({
    name: RapidMeta.nctAcronyms[t.id] ?? t.data?.name,
    tE: t.data.tE, tN: t.data.tN, cE: t.data.cE, cN: t.data.cN,
    pubHR: t.data.pubHR ?? null,
    pubHR_LCI: t.data.pubHR_LCI ?? null,
    pubHR_UCI: t.data.pubHR_UCI ?? null,
    rob: t.data.rob ?? null
}));
```

- [ ] **Step 2: Add inline ZIP builder**

```javascript
// ===== v12.0: INLINE ZIP BUILDER (STORE method, no library) =====
const ZipBuilder = {
    _crc32Table: null,
    _initCRC() {
        if (this._crc32Table) return;
        this._crc32Table = new Uint32Array(256);
        for (let i = 0; i < 256; i++) {
            let c = i;
            for (let j = 0; j < 8; j++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
            this._crc32Table[i] = c;
        }
    },
    _crc32(data) {
        this._initCRC();
        let crc = 0xFFFFFFFF;
        for (let i = 0; i < data.length; i++) crc = this._crc32Table[(crc ^ data[i]) & 0xFF] ^ (crc >>> 8);
        return (crc ^ 0xFFFFFFFF) >>> 0;
    },
    build(files) {
        // files: [{name: string, content: string}]
        this._initCRC();
        const encoder = new TextEncoder();
        const entries = files.map(f => {
            const nameBytes = encoder.encode(f.name);
            const contentBytes = encoder.encode(f.content);
            const crc = this._crc32(contentBytes);
            return { name: f.name, nameBytes, contentBytes, crc };
        });
        // Calculate sizes
        let offset = 0;
        const localHeaders = [];
        entries.forEach(e => {
            const headerSize = 30 + e.nameBytes.length;
            localHeaders.push({ offset, headerSize });
            offset += headerSize + e.contentBytes.length;
        });
        const centralStart = offset;
        // Central directory
        let centralSize = 0;
        entries.forEach(e => { centralSize += 46 + e.nameBytes.length; });
        const totalSize = offset + centralSize + 22;
        const buf = new Uint8Array(totalSize);
        const view = new DataView(buf.buffer);
        // Write local file headers + content
        let pos = 0;
        entries.forEach((e, i) => {
            // Local file header
            view.setUint32(pos, 0x04034b50, true); pos += 4; // Signature
            view.setUint16(pos, 20, true); pos += 2; // Version needed
            view.setUint16(pos, 0, true); pos += 2; // Flags
            view.setUint16(pos, 0, true); pos += 2; // Compression (STORE)
            view.setUint16(pos, 0, true); pos += 2; // Mod time
            view.setUint16(pos, 0, true); pos += 2; // Mod date
            view.setUint32(pos, e.crc, true); pos += 4; // CRC-32
            view.setUint32(pos, e.contentBytes.length, true); pos += 4; // Compressed size
            view.setUint32(pos, e.contentBytes.length, true); pos += 4; // Uncompressed size
            view.setUint16(pos, e.nameBytes.length, true); pos += 2; // Filename length
            view.setUint16(pos, 0, true); pos += 2; // Extra field length
            buf.set(e.nameBytes, pos); pos += e.nameBytes.length;
            buf.set(e.contentBytes, pos); pos += e.contentBytes.length;
        });
        // Central directory
        entries.forEach((e, i) => {
            view.setUint32(pos, 0x02014b50, true); pos += 4; // Signature
            view.setUint16(pos, 20, true); pos += 2; // Version made by
            view.setUint16(pos, 20, true); pos += 2; // Version needed
            view.setUint16(pos, 0, true); pos += 2; // Flags
            view.setUint16(pos, 0, true); pos += 2; // Compression
            view.setUint16(pos, 0, true); pos += 2; // Mod time
            view.setUint16(pos, 0, true); pos += 2; // Mod date
            view.setUint32(pos, e.crc, true); pos += 4; // CRC-32
            view.setUint32(pos, e.contentBytes.length, true); pos += 4; // Compressed
            view.setUint32(pos, e.contentBytes.length, true); pos += 4; // Uncompressed
            view.setUint16(pos, e.nameBytes.length, true); pos += 2; // Filename len
            view.setUint16(pos, 0, true); pos += 2; // Extra field len
            view.setUint16(pos, 0, true); pos += 2; // Comment len
            view.setUint16(pos, 0, true); pos += 2; // Disk number
            view.setUint16(pos, 0, true); pos += 2; // Internal attrs
            view.setUint32(pos, 0, true); pos += 4; // External attrs
            view.setUint32(pos, localHeaders[i].offset, true); pos += 4; // Relative offset
            buf.set(e.nameBytes, pos); pos += e.nameBytes.length;
        });
        // End of central directory
        view.setUint32(pos, 0x06054b50, true); pos += 4;
        view.setUint16(pos, 0, true); pos += 2; // Disk number
        view.setUint16(pos, 0, true); pos += 2; // Start disk
        view.setUint16(pos, entries.length, true); pos += 2; // Entries on disk
        view.setUint16(pos, entries.length, true); pos += 2; // Total entries
        view.setUint32(pos, centralSize, true); pos += 4; // Central dir size
        view.setUint32(pos, centralStart, true); pos += 4; // Central dir offset
        view.setUint16(pos, 0, true); pos += 2; // Comment length
        return buf;
    }
};
```

- [ ] **Step 3: Add CapsuleEngine**

```javascript
// ===== v12.0: REPRODUCIBILITY CAPSULE =====
const CapsuleEngine = {
    async generate() {
        const included = RapidMeta.getScopedIncludedTrials({ requireData: true });
        const s = RapidMeta.state;
        const files = [];

        // data.csv
        const csvHeader = 'ID,Name,tE,tN,cE,cN,pubHR,Group,Phase,Year,RoB_D1,RoB_D2,RoB_D3,RoB_D4,RoB_D5';
        const csvRows = included.map(t => {
            const d = t.data;
            const rob = d.rob ?? ['','','','',''];
            return `${t.id},${d.name ?? ''},${d.tE},${d.tN},${d.cE},${d.cN},${d.pubHR ?? ''},${d.group ?? ''},${d.phase ?? ''},${d.year ?? ''},${rob[0]},${rob[1]},${rob[2]},${rob[3]},${rob[4]}`;
        });
        files.push({ name: 'data.csv', content: csvHeader + '\n' + csvRows.join('\n') });

        // validate_R.R (use existing R code generator)
        const rCode = document.getElementById('r-code-text')?.innerText ?? '# Run AnalysisEngine.generateRCode() first';
        files.push({ name: 'validate_R.R', content: rCode });

        // validate_python.py
        const pyScript = this._generatePython(included);
        files.push({ name: 'validate_python.py', content: pyScript });

        // provenance.json
        const provData = {};
        included.forEach(t => { if (t.data._provenance) provData[t.id] = t.data._provenance; });
        files.push({ name: 'provenance.json', content: JSON.stringify(provData, null, 2) });

        // grade_profile.csv (generate actual data via GradeProfileEngine)
        const gradeRows = GradeProfileEngine.generateAll();
        const gradeHeader = 'Outcome,k,Certainty,Relative Effect,Control Risk per 1000,ARD per 1000,Plain Language';
        const gradeCsv = [gradeHeader, ...gradeRows.map(r => `"${r.outcome}",${r.k},"${r.certainty}","${r.relativeEffect}",${r.cerPer1000},"${r.ardPer1000}","${r.plain}"`)].join('\n');
        files.push({ name: 'grade_profile.csv', content: gradeCsv });

        // audit_log.json
        files.push({ name: 'audit_log.json', content: JSON.stringify(s.updateLog ?? [], null, 2) });

        // config.json
        files.push({ name: 'config.json', content: JSON.stringify({ version: 'v12.0', confLevel: s.confLevel, effectMeasure: s.effectMeasure, outcome: s.selectedOutcome, searchQueries: s.protocol }, null, 2) });

        // seal.json
        const seal = await DataSealEngine.computeSeal();
        files.push({ name: 'seal.json', content: JSON.stringify({ sha256: seal, timestamp: new Date().toISOString(), dataFile: 'data.csv' }, null, 2) });

        // README.txt
        files.push({ name: 'README.txt', content: 'Finerenone v12.0 Reproducibility Capsule\n\nTo validate:\n1. R: source("validate_R.R") — requires metafor package\n2. Python: python validate_python.py — requires numpy\n\ndata.csv contains all included trial data.\nprovenance.json maps each number to its source snippet.\nseal.json contains SHA-256 hash of data.csv for integrity verification.' });

        return files;
    },

    _generatePython(included) {
        const cl = RapidMeta.state.confLevel ?? 0.95;
        const lines = [
            '"""Finerenone v12.0 - Python validation (numpy only, no scipy)"""',
            'import numpy as np',
            'import csv, json, math',
            '',
            '# Normal quantile via rational approximation (Abramowitz & Stegun 26.2.23)',
            'def qnorm(p):',
            '    if p <= 0 or p >= 1: return float("inf") if p >= 1 else float("-inf")',
            '    t = math.sqrt(-2 * math.log(min(p, 1-p)))',
            '    c0, c1, c2 = 2.515517, 0.802853, 0.010328',
            '    d1, d2, d3 = 1.432788, 0.189269, 0.001308',
            '    z = t - (c0 + c1*t + c2*t*t) / (1 + d1*t + d2*t*t + d3*t*t*t)',
            '    return z if p > 0.5 else -z',
            '',
            `conf_level = ${cl}`,
            'z = qnorm(1 - (1 - conf_level) / 2)',
            '',
            '# Load data',
            'data = []',
            'with open("data.csv") as f:',
            '    reader = csv.DictReader(f)',
            '    for row in reader: data.append(row)',
            '',
            '# DerSimonian-Laird pooling',
            'yi = []; vi = []',
            'for d in data:',
            '    tE, tN, cE, cN = int(d["tE"]), int(d["tN"]), int(d["cE"]), int(d["cN"])',
            '    adj = 0.5 if (tE == 0 or cE == 0 or tE == tN or cE == cN) else 0',
            '    a, b, c_, dd = tE+adj, tN-tE+adj, cE+adj, cN-cE+adj',
            '    logOR = np.log((a/b)/(c_/dd))',
            '    v = 1/a + 1/b + 1/c_ + 1/dd',
            '    yi.append(logOR); vi.append(v)',
            '',
            'yi = np.array(yi); vi = np.array(vi)',
            'w = 1/vi',
            'sW = w.sum(); sWY = (w*yi).sum()',
            'Q = (w * yi**2).sum() - sWY**2/sW',
            'k = len(yi); df = k - 1',
            'tau2 = max(0, (Q - df) / (sW - (w**2).sum()/sW)) if Q > df else 0',
            'wr = 1/(vi + tau2)',
            'est = (wr * yi).sum() / wr.sum()',
            'se = np.sqrt(1/wr.sum())',
            'I2 = max(0, (Q - df)/Q * 100) if Q > df else 0',
            'print(f"Pooled OR: {np.exp(est):.4f} [{np.exp(est-z*se):.4f}, {np.exp(est+z*se):.4f}]")',
            'print(f"tau2: {tau2:.6f}, I2: {I2:.1f}%, conf_level: {conf_level}")',
        ];
        return lines.join('\n');
    },

    async download() {
        const files = await this.generate();
        const zipData = ZipBuilder.build(files);
        const blob = new Blob([zipData], { type: 'application/zip' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url; a.download = 'finerenone_v12_capsule.zip';
        document.body.appendChild(a); a.click(); document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(url), 5000);
        showToast('Reproducibility capsule downloaded.');
    }
};
```

- [ ] **Step 4: Add capsule download button to Report/Export tab**

```html
<button onclick="CapsuleEngine.download()" class="text-[10px] px-4 py-2 rounded-lg bg-emerald-800 text-emerald-200 hover:bg-emerald-700">
    <i class="fa-solid fa-file-zipper mr-1"></i> Download Reproducibility Capsule (ZIP)
</button>
```

- [ ] **Step 5: Run regression tests**

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add FINERENONE_REVIEW.html
git commit -m "feat(v12): add reproducibility capsule with inline ZIP builder, extend seal (A4+A5)"
```

---

### Task 13: Update Regression Tests & Goldens

**Files:**
- Modify: `finerenone_full_regression.py`
- Modify: `finerenone_regression_goldens.json`

- [ ] **Step 1: Add new plot IDs to the golden outcome checks**

In `finerenone_regression_goldens.json`, add to each outcome's `plots`:

```json
"plot-sensitivity": true,
"plot-influence": true
```

(For outcomes with k < 3, `plot-influence` may be `false`.)

- [ ] **Step 2: Add sensitivity engine validation to regression test**

In `finerenone_full_regression.py`, after the outcome sweep, add:

```python
# Validate SensitivityEngine exists and runs
sens_check = playwright_eval("""
    const c = AnalysisEngine.computeCore(RapidMeta.getScopedIncludedTrials({requireData:true}));
    const r = SensitivityEngine.run(c.plotData, c.pLogOR, c.pSE, c.tau2, c.zCrit, c.confLevel, c.pOR, c.lci, c.uci);
    JSON.stringify({scenarios: r.scenarios.length, concordant: r.concordant, total: r.total});
""")
sens_data = json.loads(sens_check)
assert sens_data['scenarios'] == 5, f"Expected 5 sensitivity scenarios, got {sens_data['scenarios']}"
```

- [ ] **Step 3: Add influence engine validation**

```python
# Validate InfluenceEngine
inf_check = playwright_eval("""
    const c = AnalysisEngine.computeCore(RapidMeta.getScopedIncludedTrials({requireData:true}));
    const r = InfluenceEngine.run(c.plotData, c.pLogOR, c.pSE, c.tau2);
    JSON.stringify({available: r.available, count: r.available ? r.results.length : 0});
""")
inf_data = json.loads(inf_check)
# Should be available when k >= 3
```

- [ ] **Step 4: Add capsule generation test**

```python
# Validate CapsuleEngine (smoke test — generates files array)
cap_check = playwright_eval("""
    const files = await CapsuleEngine.generate();
    JSON.stringify({count: files.length, names: files.map(f=>f.name)});
""", timeout=30)
cap_data = json.loads(cap_check)
assert cap_data['count'] >= 8, f"Expected >=8 capsule files, got {cap_data['count']}"
```

- [ ] **Step 5: Run full regression suite**

Run: `cd /c/Users/user/Downloads/Finrenone && python finerenone_full_regression.py`
Expected: All tests PASS including new assertions.

- [ ] **Step 6: Commit**

```bash
git add finerenone_full_regression.py finerenone_regression_goldens.json
git commit -m "test(v12): extend regression tests for sensitivity, influence, capsule"
```

---

### Task 14: Final Version Bump & Integration Verification

**Files:**
- Modify: `FINERENONE_REVIEW.html` (version string, localStorage key)

- [ ] **Step 1: Update version string**

Search for `v11.0` in the title/header and update to `v12.0`. Update the localStorage key from `rapid_meta_finerenone_v11_0` to `rapid_meta_finerenone_v12_0`. Add migration logic:

```javascript
// Migration: v11 → v12
const oldData = localStorage.getItem('rapid_meta_finerenone_v11_0');
if (oldData && !localStorage.getItem('rapid_meta_finerenone_v12_0')) {
    localStorage.setItem('rapid_meta_finerenone_v12_0', oldData);
}
```

- [ ] **Step 2: Update goldens JSON localStorage key**

In `finerenone_regression_goldens.json`, update `local_storage_key` to `rapid_meta_finerenone_v12_0`.

- [ ] **Step 3: Div balance check**

Run: Count all `<div[\s>]` vs `</div>` in the final file. They must match.

```bash
cd /c/Users/user/Downloads/Finrenone
grep -cP '<div[\s>]' FINERENONE_REVIEW.html
grep -c '</div>' FINERENONE_REVIEW.html
```

- [ ] **Step 4: Script integrity check**

Verify no literal `</script>` inside `<script>` blocks:

```bash
# Should return 0 matches inside script blocks (only the closing tag itself)
```

- [ ] **Step 5: Run full regression suite one final time**

Run: `cd /c/Users/user/Downloads/Finrenone && python finerenone_full_regression.py`
Expected: ALL PASS.

- [ ] **Step 6: Final commit**

```bash
git add FINERENONE_REVIEW.html finerenone_full_regression.py finerenone_regression_goldens.json
git commit -m "chore(v12): version bump to v12.0, migration, div balance verified"
```

---

## Implementation Order Summary

| Task | Feature | Tier | Est. Lines Added |
|------|---------|------|-----------------|
| 1 | SensitivityEngine | C1 | ~200 |
| 2 | TSA Enhancement | C2 | ~40 |
| 3 | GRADE Upgrades | C3 | ~30 |
| 4 | InfluenceEngine | C4 | ~150 |
| 5 | Provenance Layer | D1 | ~120 |
| 6 | Source Shortcuts | D2 | ~40 |
| 7 | Endpoint Bridges | D3 | ~60 |
| 8 | Pipeline Hardening | D4 | ~50 |
| 9 | PRISMA Flow | A1 | ~120 |
| 10 | Forest Export | A2 | ~130 |
| 11 | GRADE Profile | A3 | ~100 |
| 12 | ZIP Capsule | A4+A5 | ~200 |
| 13 | Regression Tests | Test | ~50 |
| 14 | Version Bump | Infra | ~10 |
| **Total** | | | **~1,300** |

Final file size estimate: ~11,900 lines (from 10,600).
