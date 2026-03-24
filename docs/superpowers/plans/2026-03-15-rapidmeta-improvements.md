# RapidMeta 12-Feature Improvement Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 12 improvements to the RapidMeta cardiology app portfolio (11 HTML apps, ~120K total lines), starting with WebR in-browser validation and subgroup forest plots, then the remaining 10 features in sequence.

**Architecture:** Each app is a single-file HTML (9-13K lines) using a shared v12.0 template engine. Changes are implemented in FINERENONE_REVIEW.html first (reference app), validated with Selenium, then propagated to all siblings via an agent. LivingMeta.html already has WebR — port its pattern (lines 12664-13198 + UI lines 1659-1711).

**Tech Stack:** HTML/JS (single-file), Plotly.js (plots), WebR v0.4.4 (in-browser R), Selenium (testing), metafor R package (validation)

---

## Chunk 1: WebR In-Browser R Validation (Feature #2)

### Task 1: Add WebR UI to FINERENONE_REVIEW.html

**Files:**
- Modify: `FINERENONE_REVIEW.html` (analysis tab section, ~line 890)
- Reference: `LivingMeta.html:1659-1711` (WebR UI), `LivingMeta.html:586-612` (CSS)

- [ ] **Step 1: Add WebR CSS to FINERENONE style block**

After the existing `.prov-progress` CSS (~line 133), add:

```css
/* WebR validation */
.webr-card { background: rgba(6,95,70,0.08); border: 1px solid rgba(16,185,129,0.2); border-radius: 1.5rem; padding: 1.5rem; }
.webr-progress { height: 6px; border-radius: 999px; overflow: hidden; background: rgba(30,41,59,0.7); margin-top: 0.5rem; }
.webr-progress > span { display: block; height: 100%; background: linear-gradient(90deg, #10b981, #3b82f6); transition: width 0.4s; }
@keyframes webr-spin { to { transform: rotate(360deg); } }
.webr-spinner { animation: webr-spin 1s linear infinite; display: inline-block; }
.webr-badge { font-size: 9px; padding: 2px 8px; border-radius: 12px; font-weight: bold; text-transform: uppercase; }
.webr-badge-ready { background: #065f46; color: #6ee7b7; }
.webr-badge-loading { background: #78350f; color: #fcd34d; }
.webr-badge-error { background: #7f1d1d; color: #fca5a5; }
```

- [ ] **Step 2: Add WebR UI card to analysis tab**

In the analysis tab section (after the R code block, ~line 895), add:

```html
<div class="glass p-8 rounded-[30px] border border-emerald-500/20 bg-emerald-500/5">
    <div class="flex items-center justify-between mb-4">
        <h3 class="text-xs font-bold opacity-40 uppercase tracking-widest">WebR: Validate with R in Your Browser</h3>
        <span id="webrStatusBadge" class="webr-badge webr-badge-loading">Not loaded</span>
    </div>
    <p class="text-[10px] text-slate-500 mb-4">Runs metafor::rma() directly in your browser via WebAssembly. No server needed. First load installs R + metafor (~20-40s).</p>
    <button id="webrRunBtn" onclick="runWebRValidation()" class="bg-emerald-600 text-white px-6 py-2 rounded-xl text-xs font-bold uppercase tracking-widest hover:bg-emerald-500 transition-all">
        <i class="fa-solid fa-flask-vial mr-1"></i> Run R Validation
    </button>
    <div id="webrProgressContainer" class="hidden mt-4">
        <div class="flex items-center gap-2">
            <span class="webr-spinner text-emerald-400">&#9696;</span>
            <span id="webrProgressText" class="text-[10px] text-slate-400">Initializing R...</span>
        </div>
        <div class="webr-progress mt-2"><span id="webrProgressBar" style="width:0%"></span></div>
    </div>
    <div id="webrResults" class="mt-4"></div>
</div>
```

- [ ] **Step 3: Verify HTML renders without JS errors**

Run: `python -c "import sys,io,time;sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace');from selenium import webdriver;from selenium.webdriver.chrome.options import Options;o=Options();o.add_argument('--headless=new');o.add_argument('--no-sandbox');d=webdriver.Chrome(options=o);d.get('file:///C:/Users/user/Downloads/Finrenone/FINERENONE_REVIEW.html');time.sleep(4);print('webrRunBtn:',d.execute_script('return document.getElementById(\"webrRunBtn\")!=null'));d.quit()"`
Expected: `webrRunBtn: True`

---

### Task 2: Add WebR validation engine to FINERENONE

**Files:**
- Modify: `FINERENONE_REVIEW.html` (before `window.onload`, ~line 11880)
- Reference: `LivingMeta.html:12664-13198`

- [ ] **Step 1: Add runWebRValidation() function**

Before `window.onload`, add the WebR engine function. This is ported from LivingMeta with adaptations for the v12 template's data structure (uses `RapidMeta.state.results` instead of `AppState.results`):

```javascript
let webRInstance = null;
let webRLoading = false;

async function runWebRValidation() {
    const btn = document.getElementById('webrRunBtn');
    const prog = document.getElementById('webrProgressContainer');
    const progText = document.getElementById('webrProgressText');
    const progBar = document.getElementById('webrProgressBar');
    const badge = document.getElementById('webrStatusBadge');
    const resultsDiv = document.getElementById('webrResults');

    if (webRLoading) { showToast('WebR is already loading...'); return; }

    const r = RapidMeta.state.results;
    if (!r || !r.plotData) { showToast('Run analysis first.', 'warn'); return; }

    btn.disabled = true;
    prog.classList.remove('hidden');
    progText.textContent = 'Loading WebR runtime...';
    progBar.style.width = '10%';
    badge.className = 'webr-badge webr-badge-loading';
    badge.textContent = 'Loading...';

    try {
        if (!webRInstance) {
            webRLoading = true;
            progText.textContent = 'Downloading WebR v0.4.4 (~8MB)...';
            progBar.style.width = '20%';
            const { WebR } = await import('https://webr.r-wasm.org/v0.4.4/webr.mjs');
            webRInstance = new WebR();
            await webRInstance.init();
            progText.textContent = 'Installing metafor package...';
            progBar.style.width = '50%';
            try {
                await webRInstance.evalR('webr::install("metafor", quiet = TRUE)');
                await webRInstance.evalR('library(metafor)');
                badge.textContent = 'R metafor';
                badge.className = 'webr-badge webr-badge-ready';
            } catch(e) {
                badge.textContent = 'R (Base)';
                badge.className = 'webr-badge webr-badge-ready';
            }
            webRLoading = false;
        }

        progText.textContent = 'Running meta-analysis in R...';
        progBar.style.width = '70%';

        // Build R data from current analysis
        const data = r.plotData;
        const k = data.length;
        const confLevel = (RapidMeta.state.confLevel ?? 95) / 100;
        const effectSpec = RapidMeta.resolveEffectMeasure({ trials: RapidMeta.getAnalysisScopeDetails().analyzed });
        const isHR = effectSpec.effective === 'HR';

        const yiStr = data.map(d => d.logOR.toFixed(8)).join(',');
        const viStr = data.map(d => d.vi.toFixed(8)).join(',');
        const labStr = data.map(d => '"' + String(d.id).replace(/"/g, '') + '"').join(',');

        const rCode = `
yi <- c(${yiStr})
vi <- c(${viStr})
labs <- c(${labStr})
res <- rma(yi, vi, method="DL", level=${confLevel * 100})
list(
  est = as.numeric(res$beta),
  se = as.numeric(res$se),
  ci_lb = as.numeric(res$ci.lb),
  ci_ub = as.numeric(res$ci.ub),
  tau2 = as.numeric(res$tau2),
  I2 = as.numeric(res$I2),
  QE = as.numeric(res$QE),
  k = as.numeric(res$k)
)`;

        const rResult = await webRInstance.evalR(rCode);
        const rObj = await rResult.toJs();

        // Extract R results
        const rEst = rObj.values[0].values[0];
        const rSE = rObj.values[1].values[0];
        const rLCI = rObj.values[2].values[0];
        const rUCI = rObj.values[3].values[0];
        const rTau2 = rObj.values[4].values[0];
        const rI2 = rObj.values[5].values[0];
        const rQ = rObj.values[6].values[0];

        progBar.style.width = '90%';
        progText.textContent = 'Comparing results...';

        // JS results from app
        const jsEst = r.pLogOR ?? Math.log(parseFloat(r.or) || 1);
        const jsLCI = Math.log(parseFloat(r.lci) || 1);
        const jsUCI = Math.log(parseFloat(r.uci) || 1);
        const jsTau2 = parseFloat(r.tau2) || 0;
        const jsI2 = parseFloat(r.i2) || 0;

        // Compare with tolerances
        const tol = { est: 0.01, ci: 0.02, tau2: 0.001, i2: 1.0, q: 0.1 };
        const rows = [
            { label: isHR ? 'log(HR)' : 'log(OR)', js: jsEst, r: rEst, t: tol.est },
            { label: isHR ? 'HR' : 'OR', js: Math.exp(jsEst), r: Math.exp(rEst), t: tol.est },
            { label: 'CI lower', js: Math.exp(jsLCI), r: Math.exp(rLCI), t: tol.ci },
            { label: 'CI upper', js: Math.exp(jsUCI), r: Math.exp(rUCI), t: tol.ci },
            { label: 'tau2', js: jsTau2, r: rTau2, t: tol.tau2 },
            { label: 'I2 (%)', js: jsI2, r: rI2, t: tol.i2 },
        ];

        const matchCount = rows.filter(row => Math.abs(row.js - row.r) <= row.t).length;
        const allMatch = matchCount === rows.length;

        resultsDiv.innerHTML = '<div class="text-[10px] font-bold uppercase tracking-widest mb-3 ' + (allMatch ? 'text-emerald-400' : 'text-amber-400') + '">' +
            '<i class="fa-solid ' + (allMatch ? 'fa-circle-check' : 'fa-triangle-exclamation') + ' mr-1"></i>' +
            matchCount + '/' + rows.length + ' metrics match R metafor (DL, k=' + k + ')</div>' +
            '<table class="w-full text-[10px]"><thead><tr class="text-slate-500 uppercase"><th class="text-left p-1">Metric</th><th class="text-right p-1">App (JS)</th><th class="text-right p-1">R metafor</th><th class="text-right p-1">Diff</th><th class="text-center p-1">Match</th></tr></thead><tbody>' +
            rows.map(row => {
                const diff = Math.abs(row.js - row.r);
                const ok = diff <= row.t;
                return '<tr class="border-t border-slate-800/30"><td class="p-1 text-slate-300 font-mono">' + escapeHtml(row.label) + '</td>' +
                    '<td class="p-1 text-right font-mono text-slate-300">' + row.js.toFixed(4) + '</td>' +
                    '<td class="p-1 text-right font-mono text-emerald-400">' + row.r.toFixed(4) + '</td>' +
                    '<td class="p-1 text-right font-mono ' + (ok ? 'text-slate-500' : 'text-red-400') + '">' + diff.toFixed(5) + '</td>' +
                    '<td class="p-1 text-center">' + (ok ? '<i class="fa-solid fa-check text-emerald-400"></i>' : '<i class="fa-solid fa-xmark text-red-400"></i>') + '</td></tr>';
            }).join('') + '</tbody></table>';

        progBar.style.width = '100%';
        progText.textContent = 'Validation complete.';
        setTimeout(() => prog.classList.add('hidden'), 2000);

        addAuditEntry('WebR validation: ' + matchCount + '/' + rows.length + ' match (DL, k=' + k + ', ' + (isHR ? 'HR' : 'OR') + ')');

    } catch(e) {
        badge.textContent = 'Error';
        badge.className = 'webr-badge webr-badge-error';
        progText.textContent = 'Error: ' + e.message;
        resultsDiv.innerHTML = '<div class="text-xs text-red-400"><i class="fa-solid fa-circle-xmark mr-1"></i>' + escapeHtml(e.message) + '</div>';
        webRLoading = false;
    } finally {
        btn.disabled = false;
    }
}
```

- [ ] **Step 2: Run existing test suite to verify no regressions**

Run: `cd C:/Users/user/Downloads/Finrenone && python test_livingmeta.py`
Expected: `36/36 passed`

- [ ] **Step 3: Write WebR-specific Selenium test**

Create `test_webr_finerenone.py`:

```python
"""Test WebR validation button exists and JS engine is intact."""
import sys, io, os, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def test_webr_ui():
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-gpu')
    opts.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
    d = webdriver.Chrome(options=opts)
    results = []

    try:
        d.get('file:///' + os.path.abspath('FINERENONE_REVIEW.html').replace(os.sep, '/'))
        time.sleep(5)

        # WebR UI exists
        results.append(('webrRunBtn exists', d.execute_script('return document.getElementById("webrRunBtn") != null')))
        results.append(('webrStatusBadge exists', d.execute_script('return document.getElementById("webrStatusBadge") != null')))
        results.append(('runWebRValidation fn exists', d.execute_script('return typeof runWebRValidation === "function"')))

        # Analysis still works
        d.execute_script('RapidMeta.switchTab("analysis")')
        time.sleep(3)
        r = d.execute_script('return RapidMeta.state.results?.k')
        results.append(('synthesis produces k>=2', isinstance(r, (int, float)) and r >= 2))

        # No JS errors
        logs = d.get_log('browser')
        severe = [l for l in logs if l['level'] == 'SEVERE' and 'favicon' not in l.get('message', '').lower()
                  and 'PubMed' not in l.get('message', '') and 'CT.gov' not in l.get('message', '')]
        results.append(('No JS errors', len(severe) == 0))
        for e in severe[:3]:
            print(f'  JS ERROR: {e["message"][:120]}')

    finally:
        d.quit()

    passed = sum(1 for _, v in results if v)
    for name, val in results:
        print(f'  [{"OK" if val else "FAIL"}] {name}')
    print(f'\n{passed}/{len(results)} passed')
    return passed == len(results)

if __name__ == '__main__':
    sys.exit(0 if test_webr_ui() else 1)
```

- [ ] **Step 4: Run WebR UI test**

Run: `cd C:/Users/user/Downloads/Finrenone && python test_webr_finerenone.py`
Expected: `5/5 passed`

- [ ] **Step 5: Commit**

```bash
git add FINERENONE_REVIEW.html test_webr_finerenone.py
git commit -m "feat: add WebR in-browser R validation to FINERENONE"
```

---

### Task 3: Propagate WebR to all sibling apps

**Files:**
- Modify: All 7 sibling v12 apps (BEMPEDOIC, COLCHICINE, GLP1, INTENSIVE_BP, LIPID_HUB, PCSK9, SGLT2)
- Skip: ATTR_CM (stub), INCRETIN_HFpEF (different architecture), LivingMeta (already has WebR)

- [ ] **Step 1: Use propagation agent to add WebR CSS + UI + JS to all 7 apps**

Dispatch agent with instructions to:
1. Add WebR CSS block (same for all apps)
2. Add WebR UI card in analysis section (same HTML for all)
3. Add `runWebRValidation()` function before `window.onload` (same JS for all)
4. Verify no duplicate `runWebRValidation` definitions

- [ ] **Step 2: Run full test suite**

Run: `cd C:/Users/user/Downloads/Finrenone && python test_livingmeta.py`
Expected: `36/36 passed`

- [ ] **Step 3: Spot-check 3 apps for WebR button**

Run quick Selenium check on BEMPEDOIC, GLP1, SGLT2 to verify `webrRunBtn` exists.

- [ ] **Step 4: Commit**

```bash
git add *.html
git commit -m "feat: propagate WebR validation to all v12 apps"
```

---

## Chunk 2: Subgroup Forest Plots by Drug Class (Feature #5)

### Task 4: Verify and enhance group data in all apps

**Files:**
- Modify: Trial data sections in each app's `realData` object

- [ ] **Step 1: Audit existing group fields per app**

For each app, grep for `group:` in the realData section and verify meaningful categorization exists:
- FINERENONE: CKD, Heart Failure (OK)
- BEMPEDOIC: Check if group exists (likely single class)
- COLCHICINE: Post-MI, Stable CAD (from COLCOT vs LoDoCo2)
- GLP1: Oral, Injectable, Tirzepatide (drug-level subgroups)
- INTENSIVE_BP: Check (SPRINT vs ACCORD vs STEP)
- LIPID_HUB: Pure EPA, EPA+DHA (from trial drugClass field)
- PCSK9: Evolocumab, Alirocumab (agent-level)
- SGLT2: Dapagliflozin, Empagliflozin, Canagliflozin, Sotagliflozin

- [ ] **Step 2: Add missing group labels to trial data**

For each app where group is missing or too generic, add meaningful subgroup labels. Use `drugClass` if available, otherwise categorize by mechanism/agent.

- [ ] **Step 3: Verify subgroup plot already renders**

Run FINERENONE synthesis and check if `plot-subgroup` div gets populated.

- [ ] **Step 4: Commit**

```bash
git add *.html
git commit -m "feat: add drug class subgroup labels to all trial data"
```

---

### Task 5: Enhance subgroup forest plot with interaction test

**Files:**
- Modify: `FINERENONE_REVIEW.html` (subgroup plot section, ~line 9397)

- [ ] **Step 1: Add Q_between p-value and interaction test to subgroup plot**

Below the subgroup plot, add a text summary:
```javascript
// After subgroup plot render
const qBetweenText = groups.length > 1
    ? 'Test for subgroup differences: Q_between = ' + qBetween.toFixed(2) +
      ', df = ' + (groups.length - 1) + ', p = ' + chi2CDF(qBetween, groups.length - 1).toFixed(4)
    : 'Single subgroup — no interaction test.';
setDesc('desc-subgroup', qBetweenText);
```

- [ ] **Step 2: Add pooled diamond per subgroup on forest plot**

Modify the subgroup trace to show pooled diamond per group alongside the main forest plot, with group headers separating studies.

- [ ] **Step 3: Run test suite**

Run: `cd C:/Users/user/Downloads/Finrenone && python test_livingmeta.py`
Expected: `36/36 passed`

- [ ] **Step 4: Commit**

```bash
git add FINERENONE_REVIEW.html
git commit -m "feat: enhance subgroup plot with Q_between interaction test"
```

---

### Task 6: Propagate subgroup improvements to siblings

- [ ] **Step 1: Propagate via agent to all 7 sibling apps**
- [ ] **Step 2: Run full test suite**
- [ ] **Step 3: Commit**

---

## Chunk 3: Remaining Features (#1, #3, #4, #6-#12)

### Task 7: Feature #1 — Live CT.gov Monitoring

Add a "Check for Updates" button that re-queries CT.gov for the app's drug, compares against included trials, and shows new/updated trials since last search. Port `compareWithStored()` (already exists) to a user-facing alert panel.

### Task 8: Feature #3 — PRISMA 2020 Flow Diagram

Generate a downloadable SVG PRISMA 2020 flow from the app's screening counts. Use inline SVG (no external dependencies). Render in the Report tab.

### Task 9: Feature #4 — Fix BEMPEDOIC Default Outcome

Investigate why BEMPEDOIC defaults to OR=1.14 instead of HR=0.87. Fix the default outcome/measure mapping.

### Task 10: Feature #6 — Network Meta-Analysis

Port ATTR_CM's NMA engine (indirect comparisons, SUCRA rankings) to apps with multiple drug classes (GLP1, SGLT2, PCSK9).

### Task 11: Feature #7 — Unified Sensitivity Dashboard

Create a one-click "Robustness Check" panel showing leave-one-out, influence diagnostics, trim-and-fill, and Copas on a single view.

### Task 12: Feature #8 — Patient-Facing Mode

Port LivingMeta's patient mode (traffic-light summary, plain language, NNT visualization) to all v12 apps.

### Task 13: Feature #9 — PDF Report Generation

Add a "Download PDF" button that uses browser print-to-PDF with a clean print stylesheet. Include forest plot, funnel, GRADE table, PRISMA flow.

### Task 14: Feature #10 — Multi-Outcome Dashboard

Add a heatmap view showing all outcomes simultaneously (MACE, mortality, renal, HF) across all trials.

### Task 15: Feature #11 — Bayesian Model Averaging

Add BMA across DL/REML/PM estimators with model weights and posterior model probabilities.

### Task 16: Feature #12 — Cross-App Meta-Dashboard

New standalone HTML file that loads synthesis results from all 10 apps and renders a comparative view (ranked NNT table, indirect comparisons).

---

## Execution Order

| Priority | Feature | Task | Effort | Dependencies |
|----------|---------|------|--------|-------------|
| 1 | WebR Validation | Tasks 1-3 | 2h | None |
| 2 | Subgroup Plots | Tasks 4-6 | 2h | None |
| 3 | Fix BEMPEDOIC | Task 9 | 30m | None |
| 4 | Live CT.gov Monitor | Task 7 | 1h | None |
| 5 | PRISMA Flow | Task 8 | 1h | None |
| 6 | Patient Mode | Task 12 | 2h | None |
| 7 | Sensitivity Dashboard | Task 11 | 2h | None |
| 8 | NMA | Task 10 | 3h | Subgroup data |
| 9 | PDF Report | Task 13 | 2h | PRISMA Flow |
| 10 | Multi-Outcome Dashboard | Task 14 | 3h | None |
| 11 | BMA | Task 15 | 2h | WebR |
| 12 | Cross-App Dashboard | Task 16 | 4h | All others |
