# Dose-Response Pack — Round 1B Implementation Plan (Flagship + Engine P1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `ALCOHOL_BC_DOSE_RESP_REVIEW.html` (4-tab teaching flagship on Greenland-Longnecker 1992 alcohol-breast-cancer canonical dataset), plus two engine P1 fixes (F-2 predict t-critical, F-3 forest RCS τ²) and an R-script extension that adds `lme4::glmer` one-stage Poisson hierarchical output.

**Architecture:** Two engine fixes land first as their own commits (preserves git history clarity and lets you verify the test suite stays green at 35/35 before any HTML work). Then the R script grows a one-stage block so Tab 3 has real data to display. Then the badge JS, then the HTML scaffold, then each tab is populated one at a time with a manual browser smoke after each.

**Tech Stack:** ES5-compatible JS (browser-only constraints, no build step), Node ≥18 for tests, R 4.5.2 + `dosresmeta` 2.x + `lme4` 1.x, Python 3.13 for the validator wrapper.

---

## File Structure

| Path | Responsibility | Action |
|---|---|---|
| `rapidmeta-dose-response-engine-v1.js` | Engine — F-2 + F-3 patches in `predict()` and `forest()` | MODIFY |
| `tests/test_dose_response_engine.mjs` | Two new regression tests pinning F-2 and F-3 behavior | MODIFY |
| `scripts/r_validate_doseresp.R` | Add `lme4::glmer` Poisson + offset one-stage block | MODIFY |
| `outputs/r_validation/doseresp/gl1992_alcohol_bc.json` | Regenerated to include `one_stage` block | REGENERATE |
| `vendor/r-validation-doseresp.js` | Badge UI mirroring `r-validation-dta.js` / `r-validation-continuous.js` | NEW |
| `ALCOHOL_BC_DOSE_RESP_REVIEW.html` | Flagship — 4 tabs, ~600-900 lines | NEW |

**Spec:** `docs/superpowers/specs/2026-05-12-dose-response-round-1b-design.md`

**Pre-existing dependencies** (already merged in main at `403765c1`):
- Engine: validate, fitLinear, fitRCS, fitOneStage, nonLinearityTest, predict, forest, exportResults — all functional
- R validator triplet: `scripts/r_validate_doseresp.{R,py}` + `outputs/r_validation/doseresp/gl1992_alcohol_bc.json`
- 33 Node-runnable tests passing

---

## Task 1: F-2 fix — `predict()` uses t_{k-1} for linear results

**Files:**
- Modify: `rapidmeta-dose-response-engine-v1.js` (inside `predict()` function, the linear branch's return statement)
- Modify: `tests/test_dose_response_engine.mjs` (add one new test)

- [ ] **Step 1: Write the failing regression test**

Append to `tests/test_dose_response_engine.mjs` BEFORE the runner block (`let pass = 0, fail = 0;`):

```javascript
test('predict() linear CI uses t_{k-1} not raw z=1.96 (F-2 fix)', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitLinear(fx.trials, {});
  // For k=5, qt(0.975, 4) ≈ 2.776, NOT 1.96. CI half-width at dose=5 should be ~5*se*2.776.
  const p = DR.predict(res, 5);
  const halfWidth = p.ci_hi - p.est;
  const expected = 5 * res.pooled_slope_log_se * I.qt(0.975, res.pi_df);
  near(halfWidth, expected, 1e-10, 'predict CI half-width = dose * se * t_{k-1}');
  // Confirm it is NOT the 1.96-based value (sanity: the two are visibly different at k=5)
  const wrongValue = 5 * res.pooled_slope_log_se * 1.96;
  assert.ok(Math.abs(halfWidth - wrongValue) > 0.0001,
    `should not equal z=1.96 width; got ${halfWidth}, z-based was ${wrongValue}`);
});
```

- [ ] **Step 2: Run, expect this test to FAIL**

Run: `cd C:/Projects/Finrenone && node tests/test_dose_response_engine.mjs`

Expected: `34 passed, 1 failed` (the new test fails because the current `predict()` uses `1.96`).

- [ ] **Step 3: Apply the F-2 fix**

In `rapidmeta-dose-response-engine-v1.js`, find the `predict()` function. The linear branch currently looks like:

```javascript
  } else {
    est = dose * result.pooled_slope_log;
    se = Math.abs(dose) * result.pooled_slope_log_se;
    return { est: est, ci_lo: est - 1.96 * se, ci_hi: est + 1.96 * se, extrapolation_banner: banner };
  }
```

Replace with:

```javascript
  } else {
    est = dose * result.pooled_slope_log;
    se = Math.abs(dose) * result.pooled_slope_log_se;
    // F-2 fix: use t_{k-1} (matches fitLinear's own CI construction) instead of raw z=1.96.
    // Falls back to z=1.96 only when pi_df is missing (defensive) or non-positive (k=1 edge,
    // which fitLinear itself rejects via the k<2 guard).
    var df = result.pi_df != null ? result.pi_df : (result.k != null ? result.k - 1 : 0);
    var tcrit = df > 0 ? qt(0.975, df) : 1.96;
    return { est: est, ci_lo: est - tcrit * se, ci_hi: est + tcrit * se, extrapolation_banner: banner };
  }
```

The RCS branch (above this else) reads pre-computed CIs from `result.rcs.fit_at_dose` and stays unchanged — the RCS curve grid's CIs are built inside `fitRCS()` and that is a separate concern (already noted as a P2 hardening item in the Round 1A spec).

- [ ] **Step 4: Run, expect all tests pass**

Run: `cd C:/Projects/Finrenone && node tests/test_dose_response_engine.mjs`

Expected: `34 passed, 0 failed`. If any pre-existing test breaks, STOP — F-2 was not supposed to affect any test except the new one. Likely cause: a typo in the replacement.

- [ ] **Step 5: Commit**

```bash
cd /c/Projects/Finrenone && git add rapidmeta-dose-response-engine-v1.js tests/test_dose_response_engine.mjs && git commit -m "fix(dose-response): F-2 predict() uses t_{k-1} for linear CI (round 1B)"
```

---

## Task 2: F-3 fix — `forest()` uses RCS τ² from `tau2_per_dim[0]` when result is RCS

**Files:**
- Modify: `rapidmeta-dose-response-engine-v1.js` (inside `forest()` function, the τ² source line)
- Modify: `tests/test_dose_response_engine.mjs` (add one new test)

- [ ] **Step 1: Write the failing regression test**

Append to `tests/test_dose_response_engine.mjs` BEFORE the runner block:

```javascript
test('forest() on fitRCS result uses RE weights from tau2_per_dim[0] (F-3 fix)', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitRCS(fx.trials, { knots: 3 });
  const rows = DR.forest(fx.trials, res);
  assert.equal(rows.length, 5);

  // RCS layer carries tau² inside res.rcs.tau2_per_dim[0]. Verify forest uses it.
  // FE weights would be 1/vi (no tau² added). RE weights are 1/(vi + tau²_per_dim[0]).
  const tau2 = res.rcs.tau2_per_dim[0] || 0;
  const studlab = rows[0].label;
  const matchingStudy = res.per_study.find(s => s.studlab === studlab);
  const expectedW = 1 / (matchingStudy.slope_log_se * matchingStudy.slope_log_se + tau2);
  // Sum-normalised weights — we compute the expected weight_pct
  const allExpectedW = rows.map(r => {
    const s = res.per_study.find(ss => ss.studlab === r.label);
    return 1 / (s.slope_log_se * s.slope_log_se + tau2);
  });
  const totalW = allExpectedW.reduce((a, b) => a + b, 0);
  const expectedPct = 100 * expectedW / totalW;
  near(rows[0].weight_pct, expectedPct, 1e-6, 'RCS forest uses RE weights from tau2_per_dim[0]');
});
```

- [ ] **Step 2: Run, expect this test to FAIL**

Run: `cd C:/Projects/Finrenone && node tests/test_dose_response_engine.mjs`

Expected: `34 passed, 1 failed` (the new test fails because the current `forest()` reads `result.tau2 || 0`, which is `0` for RCS results since fitRCS doesn't set a root-level `tau2`).

- [ ] **Step 3: Apply the F-3 fix**

In `rapidmeta-dose-response-engine-v1.js`, find the `forest()` function. The τ² source line currently looks like:

```javascript
  // weights: 1 / (vi + tau2)
  var tau2 = result.tau2 || 0;
```

Replace with:

```javascript
  // weights: 1 / (vi + tau2).
  // F-3 fix: fitRCS results carry tau² inside result.rcs.tau2_per_dim (per-dimension);
  // use dim 0 (the linear component) for forest weighting. fitLinear / fitOneStage
  // results expose result.tau2 directly.
  var tau2;
  if (result.layer === 'rcs' && result.rcs && Array.isArray(result.rcs.tau2_per_dim)) {
    tau2 = result.rcs.tau2_per_dim[0] || 0;
  } else {
    tau2 = result.tau2 || 0;
  }
```

- [ ] **Step 4: Run, expect 35/0**

Run: `cd C:/Projects/Finrenone && node tests/test_dose_response_engine.mjs`

Expected: `35 passed, 0 failed`. The existing `forest returns per_study rows with weight_pct` test uses a fitLinear result, so it stays green. The new test pins the RCS path.

- [ ] **Step 5: Commit**

```bash
cd /c/Projects/Finrenone && git add rapidmeta-dose-response-engine-v1.js tests/test_dose_response_engine.mjs && git commit -m "fix(dose-response): F-3 forest() uses tau2_per_dim[0] for RCS results (round 1B)"
```

---

## Task 3: R script — add `lme4::glmer` Poisson one-stage block

**Files:**
- Modify: `scripts/r_validate_doseresp.R` (append one-stage section after RCS block)

- [ ] **Step 1: Verify `lme4` is installed in R 4.5.2**

Run:
```bash
"C:/Program Files/R/R-4.5.2/bin/Rscript.exe" -e "library(lme4); cat(as.character(packageVersion('lme4')))"
```

Expected: prints version like `1.1-35.x`. If `lme4` is missing, install:
```bash
"C:/Program Files/R/R-4.5.2/bin/Rscript.exe" -e "install.packages('lme4', repos='https://cloud.r-project.org')"
```

If install fails, STOP and report `BLOCKED`.

- [ ] **Step 2: Add the one-stage block to the R script**

Open `scripts/r_validate_doseresp.R`. Find the line that builds the output list (currently begins with `out <- list(` after the RCS Wald-test block). Just BEFORE that line, insert:

```r
# One-stage Poisson hierarchical (lme4::glmer with offset). Per-arm counts modelled
# with random study intercept; dose enters as a fixed effect on the log-rate scale.
suppressPackageStartupMessages({ library(lme4) })

fit_os <- tryCatch(
  glmer(events ~ dose + (1 | studlab), offset = log(n),
        family = poisson(link = "log"), data = df,
        control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e5))),
  error = function(e) NULL
)

one_stage_block <- if (is.null(fit_os)) list(fit_ok = FALSE) else {
  conv_ok <- is.null(fit_os@optinfo$conv$lme4$messages) ||
             length(fit_os@optinfo$conv$lme4$messages) == 0
  ci <- tryCatch(confint(fit_os, parm = "dose", method = "Wald"),
                 error = function(e) c(NA_real_, NA_real_))
  list(
    fit_ok = TRUE,
    lme4_version = as.character(packageVersion("lme4")),
    coef_dose = as.numeric(fixef(fit_os)["dose"]),
    coef_dose_se = as.numeric(sqrt(diag(vcov(fit_os))["dose"])),
    coef_dose_ci_lo = as.numeric(ci[1]),
    coef_dose_ci_hi = as.numeric(ci[2]),
    random_effects_var = as.numeric(VarCorr(fit_os)$studlab[1, 1]),
    converged = conv_ok
  )
}
```

Then find the existing `out <- list(...)` block and add `one_stage = one_stage_block,` as a new field inside the list (anywhere among the existing fields; placing it after `rcs = ...` is natural).

- [ ] **Step 3: Smoke-test the R script directly**

Run:
```bash
cd /c/Projects/Finrenone && python scripts/r_validate_doseresp.py --review gl1992_alcohol_bc
```

Expected output: `gl1992_alcohol_bc: OK — linear=True, rcs=True` (the script doesn't print `one_stage`, but it must succeed). If R errors, the wrapper exits non-zero and prints the R stderr. Capture and fix.

Then inspect the regenerated JSON:
```bash
cd /c/Projects/Finrenone && python -c "import json; d=json.load(open('outputs/r_validation/doseresp/gl1992_alcohol_bc.json')); print(json.dumps(d.get('one_stage', 'NOT FOUND'), indent=2))"
```

Expected: a JSON block with `fit_ok: true`, `converged: true`, `coef_dose` around `0.006` to `0.007` (per-gram log-RR; matches the linear pool magnitude since GL-1992 is approximately linear at this scale), `coef_dose_se` around `0.001`, `random_effects_var` non-negative.

If `converged: false` or the coefficient is wildly off (>0.05 per gram, or negative), STOP and report `DONE_WITH_CONCERNS` with the actual values.

- [ ] **Step 4: Commit the R script change**

```bash
cd /c/Projects/Finrenone && git add scripts/r_validate_doseresp.R && git commit -m "feat(dose-response): add lme4::glmer one-stage Poisson block (round 1B)"
```

---

## Task 4: Regenerate and commit the R-output JSON

**Files:**
- Modify (regenerate): `outputs/r_validation/doseresp/gl1992_alcohol_bc.json`

- [ ] **Step 1: Confirm the JSON was regenerated by Task 3**

Run:
```bash
cd /c/Projects/Finrenone && git diff --stat outputs/r_validation/doseresp/gl1992_alcohol_bc.json
```

Expected: a non-empty diff (the file changed from Task 3's R run).

If the file is unchanged (Task 3 didn't run the wrapper or the wrapper failed silently), re-run `python scripts/r_validate_doseresp.py --review gl1992_alcohol_bc`.

- [ ] **Step 2: Quick sanity check of the new JSON**

```bash
cd /c/Projects/Finrenone && python -c "
import json
d = json.load(open('outputs/r_validation/doseresp/gl1992_alcohol_bc.json'))
print('linear.fit_ok:', d.get('linear', {}).get('fit_ok'))
print('rcs.fit_ok:', d.get('rcs', {}).get('fit_ok'))
print('one_stage.fit_ok:', d.get('one_stage', {}).get('fit_ok'))
print('one_stage.converged:', d.get('one_stage', {}).get('converged'))
print('one_stage.coef_dose:', d.get('one_stage', {}).get('coef_dose'))
"
```

Expected:
```
linear.fit_ok: True
rcs.fit_ok: True
one_stage.fit_ok: True
one_stage.converged: True
one_stage.coef_dose: ~0.006 (a small positive float)
```

- [ ] **Step 3: Commit the regenerated JSON**

```bash
cd /c/Projects/Finrenone && git add outputs/r_validation/doseresp/gl1992_alcohol_bc.json && git commit -m "data(dose-response): regenerate GL-1992 R output with one_stage block"
```

---

## Task 5: Badge JS — `vendor/r-validation-doseresp.js`

**Files:**
- Create: `vendor/r-validation-doseresp.js`

- [ ] **Step 1: Read the reference patterns**

Open the two closest analogues in this repo:
- `vendor/r-validation-continuous.js` — paradigm closest to ours (continuous outcome, MD pool)
- `vendor/r-validation-dta.js` — most-recent badge, shipped 2026-05-12

Note the IIFE shape, the mount-point lookup, the threshold-based green/amber styling, and the structure of the side-by-side numbers table.

- [ ] **Step 2: Create the badge JS**

Create `vendor/r-validation-doseresp.js`:

```javascript
/* vendor/r-validation-doseresp.js — v0.1.0 (2026-05-12)
 *
 * Collapsible R-parity badge for the dose-response engine. Compares
 * window.RapidMetaDoseResp output against R dosresmeta + lme4::glmer
 * precomputed values loaded from outputs/r_validation/doseresp/<REVIEW>.json.
 *
 * Mount with: <div id="r-parity-doseresp" data-review="gl1992_alcohol_bc"></div>
 * Then call: RValidationDoseresp.render('r-parity-doseresp', engineResults, rResults);
 *
 * engineResults must include: { linear: <fitLinear-output>, rcs: <fitRCS-output>, one_stage: <fitOneStage-output> }
 * rResults is the parsed JSON from outputs/r_validation/doseresp/<REVIEW>.json.
 */
(function (root) {
  'use strict';

  // Threshold matrix per spec §6
  var THRESHOLDS = {
    linear_slope: 0.01,
    linear_tau2: 0.0001,
    rcs_coef_0: 0.01,
    rcs_coef_1: 0.01,
  };

  function fmt(x, dp) {
    if (x == null || !isFinite(x)) return 'n/a';
    return (+x).toFixed(dp == null ? 4 : dp);
  }

  function row(label, engineVal, rVal, threshold, opts) {
    opts = opts || {};
    var delta = (isFinite(engineVal) && isFinite(rVal)) ? Math.abs(engineVal - rVal) : null;
    var withinTol = (threshold != null && delta != null && delta < threshold);
    var status = opts.alwaysAmber ? 'amber' : (withinTol ? 'green' : 'amber');
    var note = opts.note || '';
    return (
      '<tr class="rv-row rv-row-' + status + '">' +
      '<td class="rv-label">' + label + '</td>' +
      '<td class="rv-engine">' + fmt(engineVal) + '</td>' +
      '<td class="rv-r">' + fmt(rVal) + '</td>' +
      '<td class="rv-delta">' + (delta != null ? fmt(delta) : 'n/a') + '</td>' +
      '<td class="rv-note">' + note + '</td>' +
      '</tr>'
    );
  }

  function render(mountId, engineResults, rResults) {
    var mount = document.getElementById(mountId);
    if (!mount) { console.warn('RValidationDoseresp: mount #' + mountId + ' not found'); return; }
    if (!engineResults || !rResults) {
      mount.innerHTML = '<div class="rv-banner rv-banner-error">Badge data unavailable</div>';
      return;
    }

    var eng = engineResults, r = rResults;

    var rows = [];
    rows.push(row(
      'Linear pooled log-slope',
      eng.linear && eng.linear.pooled_slope_log,
      r.linear && r.linear.pooled_slope_log,
      THRESHOLDS.linear_slope
    ));
    rows.push(row(
      'Linear τ²',
      eng.linear && eng.linear.tau2,
      r.linear && r.linear.tau2,
      THRESHOLDS.linear_tau2
    ));
    rows.push(row(
      'RCS spline_coefs[0] (linear component)',
      eng.rcs && eng.rcs.rcs && eng.rcs.rcs.spline_coefs && eng.rcs.rcs.spline_coefs[0],
      r.rcs && r.rcs.spline_coefs && r.rcs.spline_coefs[0],
      THRESHOLDS.rcs_coef_0
    ));
    rows.push(row(
      'RCS spline_coefs[1] (non-linear component)',
      eng.rcs && eng.rcs.rcs && eng.rcs.rcs.spline_coefs && eng.rcs.rcs.spline_coefs[1],
      r.rcs && r.rcs.spline_coefs && r.rcs.spline_coefs[1],
      THRESHOLDS.rcs_coef_1
    ));
    rows.push(row(
      'RCS non-linearity Wald p',
      eng.rcs && eng.rcs.rcs && eng.rcs.rcs.nonlinearity_wald_p,
      r.rcs && r.rcs.nonlinearity_wald_p,
      null,
      { alwaysAmber: true,
        note: 'Engine uses diagonal-PM v0.1; R uses full multivariate REML — documented design tradeoff' }
    ));

    var allGreen = rows.every(function (r) { return r.indexOf('rv-row-green') !== -1; });
    var headerStatus = allGreen ? 'green' : 'amber';

    var html = '' +
      '<div class="rv-badge rv-badge-' + headerStatus + '">' +
      '  <details open>' +
      '    <summary>R-parity badge — engine vs R (' + (r.dosresmeta_version ? 'dosresmeta ' + r.dosresmeta_version : 'R dosresmeta') + (r.one_stage && r.one_stage.lme4_version ? ', lme4 ' + r.one_stage.lme4_version : '') + ')</summary>' +
      '    <table class="rv-table">' +
      '      <thead><tr><th>Metric</th><th>Engine</th><th>R</th><th>|Δ|</th><th>Note</th></tr></thead>' +
      '      <tbody>' + rows.join('') + '</tbody>' +
      '    </table>' +
      '    <p class="rv-disclosure">Non-linearity p divergence is the documented v0.1 diagonal-PM approximation. P2 hardening will lift to full multivariate REML. See engine source comment in <code>fitRCS</code>.</p>' +
      '  </details>' +
      '</div>';

    mount.innerHTML = html;
  }

  root.RValidationDoseresp = { render: render, THRESHOLDS: THRESHOLDS };
})(typeof window !== 'undefined' ? window : globalThis);
```

- [ ] **Step 3: Headless smoke test from Node**

Run:
```bash
cd /c/Projects/Finrenone && node -e "
const fs = require('fs');

// Mock minimal DOM
global.document = {
  _elem: { innerHTML: '' },
  getElementById: function () { return this._elem; }
};
global.window = global;
global.console = console;

// Load engine + badge
new Function('window', fs.readFileSync('rapidmeta-dose-response-engine-v1.js','utf8'))(global);
new Function('window', fs.readFileSync('vendor/r-validation-doseresp.js','utf8'))(global);

const fx = JSON.parse(fs.readFileSync('tests/dose_response_fixtures/gl1992_alcohol_bc.json','utf8'));
const linRes = window.RapidMetaDoseResp.fitLinear(fx.trials, {});
const rcsRes = window.RapidMetaDoseResp.fitRCS(fx.trials, {knots:3});

const rResults = JSON.parse(fs.readFileSync('outputs/r_validation/doseresp/gl1992_alcohol_bc.json','utf8'));
const osRes = window.RapidMetaDoseResp.fitOneStage(fx.trials, {}, rResults);

window.RValidationDoseresp.render('r-parity-doseresp', { linear: linRes, rcs: rcsRes, one_stage: osRes }, rResults);

const html = global.document._elem.innerHTML;
console.log('badge html length:', html.length);
console.log('contains \"rv-badge\":', html.indexOf('rv-badge') !== -1);
console.log('contains 5 rows:', (html.match(/rv-row-/g) || []).length);
console.log('header status:', html.indexOf('rv-badge-amber') !== -1 ? 'amber' : 'green');
"
```

Expected:
```
badge html length: <something around 1500-3000>
contains "rv-badge": true
contains 5 rows: 5
header status: amber
```

(Header is amber because the non-linearity p row is always amber by design.)

- [ ] **Step 4: Commit**

```bash
cd /c/Projects/Finrenone && git add vendor/r-validation-doseresp.js && git commit -m "feat(dose-response): vendor/r-validation-doseresp.js badge UI (round 1B)"
```

---

## Task 6: HTML scaffold — `ALCOHOL_BC_DOSE_RESP_REVIEW.html` (header + tab navigation, no tab content yet)

**Files:**
- Create: `ALCOHOL_BC_DOSE_RESP_REVIEW.html`

- [ ] **Step 1: Read the convention pattern**

Open `PROGNOSTIC_HSTN_PAD_REVIEW.html` (around lines 1-200). Note:
- The `<!DOCTYPE html>` boilerplate
- The `<head>` block with `<style>` inline
- The collapsible methodology box
- The tab navigation idiom (hidden `<div class="tab-content">` panels + `<button onclick="showTab(...)">` triggers, OR `<details><summary>` if that's what the pack uses)

Look at how it wires up engine calls (inline `<script>` block at the bottom that calls `RapidMetaPrognostic.fit(...)` and then writes HTML into specific element IDs).

- [ ] **Step 2: Create the scaffold**

Create `ALCOHOL_BC_DOSE_RESP_REVIEW.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Alcohol intake and breast cancer incidence — dose-response meta-analysis</title>
<meta name="description" content="Pooled re-analysis of Greenland & Longnecker 1992 alcohol-breast-cancer dataset using two-stage GL linear + RCS + one-stage Poisson hierarchical, with R cross-validation badge.">
<style>
  body { font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; max-width: 1100px; margin: 1em auto; padding: 0 1em; color: #222; line-height: 1.5; }
  h1, h2, h3 { color: #1a3a5c; }
  details > summary { cursor: pointer; font-weight: 600; padding: 0.4em 0; }
  table { border-collapse: collapse; width: 100%; margin: 0.6em 0; }
  th, td { border: 1px solid #d0d0d0; padding: 0.4em 0.6em; text-align: left; }
  th { background: #f2f5f8; }
  .tab-nav { display: flex; gap: 0.5em; border-bottom: 2px solid #d0d0d0; margin: 1em 0 0.6em; }
  .tab-nav button { background: #f2f5f8; border: 1px solid #d0d0d0; border-bottom: none; padding: 0.6em 1.2em; cursor: pointer; font-size: 1em; }
  .tab-nav button.active { background: #1a3a5c; color: white; border-color: #1a3a5c; }
  .tab-content { display: none; padding: 1em 0; }
  .tab-content.active { display: block; }
  .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.8em; margin: 1em 0; }
  .kpi { background: #f8f9fb; border-left: 3px solid #1a3a5c; padding: 0.6em 0.8em; }
  .kpi-label { font-size: 0.85em; color: #555; }
  .kpi-value { font-size: 1.2em; font-weight: 600; color: #1a3a5c; }
  .rv-badge { border: 2px solid; border-radius: 4px; padding: 0.6em; margin: 1em 0; }
  .rv-badge-green { border-color: #2e8540; background: #f0f8f2; }
  .rv-badge-amber { border-color: #d97706; background: #fef8ec; }
  .rv-row-green td { background: #f0f8f2; }
  .rv-row-amber td { background: #fef8ec; }
  .rv-disclosure { font-size: 0.85em; color: #555; margin-top: 0.6em; }
  .footnote { font-size: 0.85em; color: #555; border-top: 1px solid #d0d0d0; padding-top: 1em; margin-top: 2em; }
</style>
</head>
<body>

<h1>Alcohol intake and breast cancer incidence — dose-response meta-analysis</h1>
<p>Pooled re-analysis of Greenland &amp; Longnecker 1992 worked example, <em>Am J Epidemiol</em> 135:1301-9 (<a href="https://pubmed.ncbi.nlm.nih.gov/1626547/" target="_blank">PMID 1626547</a>).</p>
<p><strong>Engine:</strong> <span id="engine-version">…</span> · <strong>Generated:</strong> <span id="gen-date">…</span></p>

<details>
  <summary>Methods (click to expand)</summary>
  <p>This review applies three dose-response meta-analysis fitters in parallel:</p>
  <ol>
    <li><strong>Two-stage Greenland-Longnecker linear pool</strong> — per-study log-linear slope via weighted least squares with the GL covariance correction, then REML+HKSJ pool. Prediction interval uses <em>t<sub>k−1</sub></em> df (Cochrane Handbook v6.5 §10.10.4.3). HKSJ floor <code>max(1, Q/(k−1))</code> per advanced-stats.md.</li>
    <li><strong>Two-stage GL + restricted cubic splines</strong> — 3 knots at Harrell percentiles (25/50/75 of unique non-reference doses); multivariate-RE pool with diagonal-PM τ² approximation; Wald joint non-linearity test.</li>
    <li><strong>One-stage Poisson hierarchical</strong> — <code>lme4::glmer(events ~ dose + (1 | studlab), offset = log(n), family = poisson)</code> computed by R, surfaced as a precomputed-display layer (no JS fitter).</li>
  </ol>
  <p>Engine validation: parity against R <code>dosresmeta::dosresmeta(method="reml")</code> on the linear component (|Δ| &lt; 0.01) and against <code>lme4::glmer</code> on one-stage (precomputed). Non-linearity Wald p diverges from R by design — see the R-parity tab.</p>
</details>

<details>
  <summary>Per-study trial summary (click to expand)</summary>
  <div id="trial-summary"></div>
</details>

<nav class="tab-nav">
  <button data-tab="linear" class="active" onclick="showTab('linear')">1. Linear (GL two-stage)</button>
  <button data-tab="rcs" onclick="showTab('rcs')">2. RCS (3 knots)</button>
  <button data-tab="onestage" onclick="showTab('onestage')">3. One-stage (Poisson glmer)</button>
  <button data-tab="parity" onclick="showTab('parity')">4. R-parity badge</button>
</nav>

<section id="tab-linear" class="tab-content active">
  <h2>Linear pool — two-stage Greenland-Longnecker</h2>
  <div id="linear-kpis"></div>
  <div id="linear-forest"></div>
  <div id="linear-curve"></div>
  <div id="linear-summary"></div>
</section>

<section id="tab-rcs" class="tab-content">
  <h2>RCS pool — 3 knots at Harrell percentiles</h2>
  <div id="rcs-kpis"></div>
  <div id="rcs-curve"></div>
  <div id="rcs-forest"></div>
  <div id="rcs-wald"></div>
</section>

<section id="tab-onestage" class="tab-content">
  <h2>One-stage Poisson hierarchical (lme4::glmer)</h2>
  <div id="onestage-kpis"></div>
  <div id="onestage-methods"></div>
</section>

<section id="tab-parity" class="tab-content">
  <h2>Engine vs R — parity badge</h2>
  <div id="r-parity-doseresp"></div>
</section>

<div class="footnote">
  <p><strong>Citation:</strong> Greenland S, Longnecker MP. Methods for trend estimation from summarized dose-response data, with applications to meta-analysis. <em>Am J Epidemiol</em>. 1992;135(11):1301-9. PMID 1626547.</p>
  <p><strong>Spec:</strong> <code>docs/superpowers/specs/2026-05-12-dose-response-round-1b-design.md</code> · <strong>Plan:</strong> <code>docs/superpowers/plans/2026-05-12-dose-response-round-1b-implementation.md</code></p>
</div>

<!-- Trial data: embedded JSON, parsed by engine + tab renderers -->
<script type="application/json" id="doseresp-trials">
</script>

<!-- Engine + badge -->
<script src="rapidmeta-dose-response-engine-v1.js" defer></script>
<script src="vendor/r-validation-badge.js" defer></script>
<script src="vendor/r-validation-doseresp.js" defer></script>

<!-- Page wiring -->
<script>
function showTab(name) {
  document.querySelectorAll('.tab-content').forEach(function (el) { el.classList.remove('active'); });
  document.querySelectorAll('.tab-nav button').forEach(function (el) { el.classList.remove('active'); });
  document.getElementById('tab-' + name).classList.add('active');
  document.querySelector('.tab-nav button[data-tab="' + name + '"]').classList.add('active');
}

window.addEventListener('DOMContentLoaded', function () {
  // Read embedded trial data (populated in Task 7)
  var trialsScript = document.getElementById('doseresp-trials');
  var trialsJson = trialsScript ? trialsScript.textContent.trim() : '';
  if (!trialsJson) { return; /* scaffold only; tabs populated by Tasks 7-10 */ }
  // Tabs 1-4 wiring is added in Tasks 7-10.
});
</script>

</body>
</html>
```

- [ ] **Step 3: Smoke test — open in a browser**

```bash
cd /c/Projects/Finrenone && python -c "import webbrowser, pathlib; webbrowser.open('file:///' + str(pathlib.Path('ALCOHOL_BC_DOSE_RESP_REVIEW.html').resolve()))"
```

Verify in the browser:
- Page loads, no console errors (open DevTools → Console)
- 4 tab buttons render
- Clicking each tab shows an empty section (no content yet — that's expected)
- Methodology and trial-summary disclosures expand

If anything is broken (e.g. a typo in a class name, or the script tags don't load), STOP and fix.

- [ ] **Step 4: Commit the scaffold**

```bash
cd /c/Projects/Finrenone && git add ALCOHOL_BC_DOSE_RESP_REVIEW.html && git commit -m "feat(dose-response): scaffold ALCOHOL_BC_DOSE_RESP_REVIEW.html (round 1B)"
```

---

## Task 7: Populate Tab 1 (Linear) + embed trial data

**Files:**
- Modify: `ALCOHOL_BC_DOSE_RESP_REVIEW.html` (embed GL-1992 trial JSON + Linear-tab rendering)

- [ ] **Step 1: Embed the GL-1992 trial JSON**

In the HTML, replace the empty `<script type="application/json" id="doseresp-trials"></script>` with the GL-1992 fixture's `trials` array, formatted compactly:

```html
<script type="application/json" id="doseresp-trials">
[
  {
    "studlab": "Schatzkin 1987", "pmid": "3658177",
    "arms": [
      {"dose": 0, "events": 165, "n": 41937, "is_reference": true},
      {"dose": 1.5, "events": 74, "n": 19089, "is_reference": false},
      {"dose": 5, "events": 90, "n": 16669, "is_reference": false},
      {"dose": 15, "events": 35, "n": 5928, "is_reference": false},
      {"dose": 24, "events": 23, "n": 2682, "is_reference": false}
    ]
  },
  {
    "studlab": "Willett 1987", "pmid": "3574409",
    "arms": [
      {"dose": 0, "events": 167, "n": 33155, "is_reference": true},
      {"dose": 1.5, "events": 152, "n": 31269, "is_reference": false},
      {"dose": 5, "events": 248, "n": 36321, "is_reference": false},
      {"dose": 15, "events": 89, "n": 11484, "is_reference": false},
      {"dose": 30, "events": 50, "n": 4140, "is_reference": false}
    ]
  },
  {
    "studlab": "Hiatt 1988", "pmid": "3375247",
    "arms": [
      {"dose": 0, "events": 53, "n": 26142, "is_reference": true},
      {"dose": 5, "events": 24, "n": 9402, "is_reference": false},
      {"dose": 20, "events": 18, "n": 6063, "is_reference": false},
      {"dose": 45, "events": 8, "n": 1971, "is_reference": false}
    ]
  },
  {
    "studlab": "Garfinkel 1988", "pmid": "3358415",
    "arms": [
      {"dose": 0, "events": 348, "n": 200195, "is_reference": true},
      {"dose": 5, "events": 250, "n": 150295, "is_reference": false},
      {"dose": 15, "events": 140, "n": 50855, "is_reference": false},
      {"dose": 30, "events": 85, "n": 17890, "is_reference": false}
    ]
  },
  {
    "studlab": "Howe 1991", "pmid": "1888691",
    "arms": [
      {"dose": 0, "events": 1281, "n": 5054, "is_reference": true},
      {"dose": 5, "events": 1004, "n": 3973, "is_reference": false},
      {"dose": 15, "events": 481, "n": 1573, "is_reference": false},
      {"dose": 45, "events": 269, "n": 837, "is_reference": false}
    ]
  }
]
</script>
```

- [ ] **Step 2: Add the Tab-1 wiring inside the `DOMContentLoaded` handler**

Replace the existing `DOMContentLoaded` handler with:

```javascript
window.addEventListener('DOMContentLoaded', function () {
  var trials = JSON.parse(document.getElementById('doseresp-trials').textContent);
  var DR = window.RapidMetaDoseResp;

  // Engine version + date
  document.getElementById('engine-version').textContent = DR.engine_version;
  document.getElementById('gen-date').textContent = new Date().toISOString().slice(0, 10);

  // Trial-summary table
  var summary = '<table><thead><tr><th>Study</th><th>PMID</th><th>Arms</th><th>Total events</th><th>Total person-years</th></tr></thead><tbody>';
  trials.forEach(function (t) {
    var totalE = t.arms.reduce(function (a, b) { return a + b.events; }, 0);
    var totalN = t.arms.reduce(function (a, b) { return a + b.n; }, 0);
    summary += '<tr><td>' + t.studlab + '</td>' +
               '<td><a href="https://pubmed.ncbi.nlm.nih.gov/' + t.pmid + '/" target="_blank">' + t.pmid + '</a></td>' +
               '<td>' + t.arms.length + '</td>' +
               '<td>' + totalE.toLocaleString() + '</td>' +
               '<td>' + totalN.toLocaleString() + '</td></tr>';
  });
  summary += '</tbody></table>';
  document.getElementById('trial-summary').innerHTML = summary;

  // === Tab 1: Linear ===
  var lin = DR.fitLinear(trials, {});
  var linHR = Math.exp(lin.pooled_slope_log * 11);
  var linHR_lo = Math.exp(lin.pooled_slope_log_ci_lo * 11);
  var linHR_hi = Math.exp(lin.pooled_slope_log_ci_hi * 11);

  document.getElementById('linear-kpis').innerHTML =
    '<div class="kpi-grid">' +
    '<div class="kpi"><div class="kpi-label">RR per 11 g/day</div><div class="kpi-value">' + linHR.toFixed(3) + '</div><div>95% CI ' + linHR_lo.toFixed(3) + '&ndash;' + linHR_hi.toFixed(3) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">log-RR per gram</div><div class="kpi-value">' + lin.pooled_slope_log.toFixed(5) + '</div><div>SE ' + lin.pooled_slope_log_se.toFixed(5) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">τ²</div><div class="kpi-value">' + lin.tau2.toFixed(5) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">I²</div><div class="kpi-value">' + lin.I2.toFixed(1) + '%</div><div>Q = ' + lin.Q.toFixed(2) + ' (df ' + lin.Q_df + ')</div></div>' +
    '<div class="kpi"><div class="kpi-label">PI (per 11 g/day, df=' + lin.pi_df + ')</div><div class="kpi-value">' + Math.exp(lin.pi_lo * 11).toFixed(3) + '&ndash;' + Math.exp(lin.pi_hi * 11).toFixed(3) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">k</div><div class="kpi-value">' + lin.k + '</div>' + (lin.coverage_warning ? '<div style="color:#d97706">coverage warning: k&lt;10</div>' : '') + '</div>' +
    '</div>';

  var forestRows = DR.forest(trials, lin);
  var fHtml = '<h3>Per-study forest (linear layer)</h3><table><thead><tr><th>Study</th><th>HR per gram</th><th>95% CI</th><th>Weight</th></tr></thead><tbody>';
  forestRows.forEach(function (r) {
    fHtml += '<tr><td>' + r.label + '</td>' +
             '<td>' + r.hr.toFixed(4) + '</td>' +
             '<td>' + r.hr_ci_lo.toFixed(4) + '&ndash;' + r.hr_ci_hi.toFixed(4) + '</td>' +
             '<td>' + r.weight_pct.toFixed(1) + '%</td></tr>';
  });
  fHtml += '</tbody></table>';
  document.getElementById('linear-forest').innerHTML = fHtml;

  // Linear curve: 20-point grid from 0 to 45 g/day
  var curveHtml = '<h3>Dose-response curve (95% CI via t<sub>' + lin.pi_df + '</sub>)</h3><table><thead><tr><th>Dose (g/day)</th><th>log-RR</th><th>RR</th><th>95% CI</th></tr></thead><tbody>';
  for (var i = 0; i < 20; i++) {
    var d = i * 45 / 19;
    var p = DR.predict(lin, d);
    curveHtml += '<tr><td>' + d.toFixed(2) + '</td>' +
                 '<td>' + p.est.toFixed(4) + '</td>' +
                 '<td>' + Math.exp(p.est).toFixed(4) + '</td>' +
                 '<td>' + Math.exp(p.ci_lo).toFixed(4) + '&ndash;' + Math.exp(p.ci_hi).toFixed(4) + '</td></tr>';
  }
  curveHtml += '</tbody></table>';
  document.getElementById('linear-curve').innerHTML = curveHtml;

  document.getElementById('linear-summary').innerHTML =
    '<p><strong>Plain-English summary:</strong> Each additional 11 g/day of alcohol (≈ 1 drink/day) is associated with a ' +
    ((linHR - 1) * 100).toFixed(1) + '% relative increase in breast-cancer incidence (RR = ' + linHR.toFixed(3) +
    ', 95% CI ' + linHR_lo.toFixed(3) + '–' + linHR_hi.toFixed(3) + '). ' +
    'Between-study heterogeneity is high (I² = ' + lin.I2.toFixed(0) + '%); the prediction interval is wider than the confidence interval and is the better summary of expected effect in a future similar study.</p>';

  // Tabs 2-4 populated in subsequent tasks.
});
```

- [ ] **Step 3: Open in browser; manual smoke**

```bash
cd /c/Projects/Finrenone && python -c "import webbrowser, pathlib; webbrowser.open('file:///' + str(pathlib.Path('ALCOHOL_BC_DOSE_RESP_REVIEW.html').resolve()))"
```

Verify in browser (Tab 1 = active by default):
- Engine version + generation date populate in the header
- Trial-summary table expands with 5 rows (Schatzkin, Willett, Hiatt, Garfinkel, Howe), correct totals
- Linear tab shows: 6 KPI cards (RR per 11g, log-RR per gram, τ², I²/Q, PI, k with coverage warning)
- Forest table shows 5 rows, weights sum to ~100% (eyeball check)
- Curve table shows 20 rows, dose 0 → 45, log-RR monotone increasing, CI brackets widen with dose
- Plain-English summary at the bottom is grammatically correct
- DevTools Console: no errors

If any value displays `NaN`, STOP — likely a missing field on the engine result; check Console for the offending field name.

- [ ] **Step 4: Commit**

```bash
cd /c/Projects/Finrenone && git add ALCOHOL_BC_DOSE_RESP_REVIEW.html && git commit -m "feat(dose-response): populate Linear tab + embed GL-1992 trial data"
```

---

## Task 8: Populate Tab 2 (RCS)

**Files:**
- Modify: `ALCOHOL_BC_DOSE_RESP_REVIEW.html` (add Tab-2 wiring inside the existing `DOMContentLoaded` handler, after the Tab 1 block)

- [ ] **Step 1: Add the Tab-2 wiring**

Just before the closing `});` of the `DOMContentLoaded` handler (where the comment "Tabs 2-4 populated in subsequent tasks." currently sits), add:

```javascript
  // === Tab 2: RCS ===
  var rcs = DR.fitRCS(trials, { knots: 3 });

  var rcsKpis = '<div class="kpi-grid">' +
    '<div class="kpi"><div class="kpi-label">Knots (g/day)</div><div class="kpi-value">' + rcs.rcs.knots.map(function (k) { return k.toFixed(1); }).join(', ') + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">spline_coefs[0] (linear)</div><div class="kpi-value">' + rcs.rcs.spline_coefs[0].toFixed(5) + '</div><div>SE ' + rcs.rcs.spline_coefs_se[0].toFixed(5) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">spline_coefs[1] (non-linear)</div><div class="kpi-value">' + rcs.rcs.spline_coefs[1].toFixed(5) + '</div><div>SE ' + rcs.rcs.spline_coefs_se[1].toFixed(5) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">Wald non-linearity p</div><div class="kpi-value">' + rcs.rcs.nonlinearity_wald_p.toFixed(4) + '</div><div>(diagonal-PM v0.1)</div></div>' +
    '<div class="kpi"><div class="kpi-label">τ² per dimension</div><div class="kpi-value">[' + rcs.rcs.tau2_per_dim.map(function (t) { return t.toExponential(2); }).join(', ') + ']</div></div>' +
    '</div>';
  document.getElementById('rcs-kpis').innerHTML = rcsKpis;

  // RCS curve: use fit_at_dose grid
  var curveHtml = '<h3>RCS dose-response curve</h3><table><thead><tr><th>Dose (g/day)</th><th>log-RR</th><th>RR</th><th>95% CI</th></tr></thead><tbody>';
  rcs.rcs.fit_at_dose.forEach(function (p) {
    curveHtml += '<tr><td>' + p.dose.toFixed(2) + '</td>' +
                 '<td>' + p.est.toFixed(4) + '</td>' +
                 '<td>' + Math.exp(p.est).toFixed(4) + '</td>' +
                 '<td>' + Math.exp(p.ci_lo).toFixed(4) + '&ndash;' + Math.exp(p.ci_hi).toFixed(4) + '</td></tr>';
  });
  curveHtml += '</tbody></table>';
  document.getElementById('rcs-curve').innerHTML = curveHtml;

  // RCS per-study forest (uses F-3 fix to read tau2_per_dim[0] for RE weights)
  var rcsForestRows = DR.forest(trials, rcs);
  var rfHtml = '<h3>Per-study forest (RCS linear-component slopes, RE-weighted)</h3><table><thead><tr><th>Study</th><th>HR per gram</th><th>95% CI</th><th>RE weight</th></tr></thead><tbody>';
  rcsForestRows.forEach(function (r) {
    rfHtml += '<tr><td>' + r.label + '</td>' +
              '<td>' + r.hr.toFixed(4) + '</td>' +
              '<td>' + r.hr_ci_lo.toFixed(4) + '&ndash;' + r.hr_ci_hi.toFixed(4) + '</td>' +
              '<td>' + r.weight_pct.toFixed(1) + '%</td></tr>';
  });
  rfHtml += '</tbody></table>';
  document.getElementById('rcs-forest').innerHTML = rfHtml;

  // Non-linearity Wald note (calls out the diagonal-PM v0.1 design tradeoff)
  document.getElementById('rcs-wald').innerHTML =
    '<div style="background:#fef8ec; border-left:3px solid #d97706; padding:0.8em; margin:1em 0;">' +
    '<strong>Wald non-linearity test (diagonal-PM v0.1):</strong> p = ' + rcs.rcs.nonlinearity_wald_p.toFixed(4) +
    ' (df = ' + (rcs.rcs.spline_coefs.length - 1) + '). ' +
    'Under the v0.1 diagonal-PM-per-dimension τ² approximation, the engine\'s non-linearity p will differ ' +
    'from R full multivariate REML (which gives p ≈ 0.7 on this dataset). See the R-parity tab for the ' +
    'side-by-side comparison. P2 hardening will lift to full multivariate REML and close this gap.</div>';
```

- [ ] **Step 2: Open in browser; manual smoke (Tab 2)**

Reload `ALCOHOL_BC_DOSE_RESP_REVIEW.html`. Click "2. RCS (3 knots)" tab.

Verify:
- 5 KPI cards (knots, two spline coefs, Wald p, τ² per-dim)
- Wald p ≈ 0.05 (matches the Round 1A regression pin)
- Knot values are 3 numbers between 5 and ~30 (Harrell 25/50/75 of unique non-zero doses)
- Curve table has 20 rows, dose 0 → 45
- Forest table has 5 rows; weights sum to ~100%
- Amber-bordered note at the bottom explains the diagonal-PM tradeoff
- DevTools Console: no errors

- [ ] **Step 3: Commit**

```bash
cd /c/Projects/Finrenone && git add ALCOHOL_BC_DOSE_RESP_REVIEW.html && git commit -m "feat(dose-response): populate RCS tab (round 1B)"
```

---

## Task 9: Populate Tab 3 (One-stage)

**Files:**
- Modify: `ALCOHOL_BC_DOSE_RESP_REVIEW.html` (load R JSON via `fetch()` + populate One-stage tab)

- [ ] **Step 1: Add R-JSON fetch + Tab-3 wiring**

Inside the `DOMContentLoaded` handler, just before the closing `});`, add:

```javascript
  // Load R-precomputed JSON for Tabs 3 and 4
  fetch('outputs/r_validation/doseresp/gl1992_alcohol_bc.json')
    .then(function (resp) {
      if (!resp.ok) throw new Error('R JSON not found: HTTP ' + resp.status);
      return resp.json();
    })
    .then(function (rRes) {
      // === Tab 3: One-stage ===
      var os = DR.fitOneStage(trials, {}, rRes);
      if (!os || !os.one_stage || os.one_stage.fit_ok === false) {
        document.getElementById('onestage-kpis').innerHTML =
          '<div class="rv-banner rv-banner-error">One-stage R output unavailable. Run <code>python scripts/r_validate_doseresp.py --review gl1992_alcohol_bc</code> to populate.</div>';
        return rRes;
      }
      var osCoef = os.one_stage.coef_dose;
      var osHR11 = Math.exp(osCoef * 11);
      document.getElementById('onestage-kpis').innerHTML =
        '<div class="kpi-grid">' +
        '<div class="kpi"><div class="kpi-label">coef_dose (per gram)</div><div class="kpi-value">' + osCoef.toFixed(5) + '</div><div>SE ' + os.one_stage.coef_dose_se.toFixed(5) + '</div></div>' +
        '<div class="kpi"><div class="kpi-label">RR per 11 g/day</div><div class="kpi-value">' + osHR11.toFixed(3) + '</div><div>95% CI ' + Math.exp(os.one_stage.coef_dose_ci_lo * 11).toFixed(3) + '&ndash;' + Math.exp(os.one_stage.coef_dose_ci_hi * 11).toFixed(3) + '</div></div>' +
        '<div class="kpi"><div class="kpi-label">Random-effects variance (studlab)</div><div class="kpi-value">' + os.one_stage.random_effects_var.toFixed(5) + '</div></div>' +
        '<div class="kpi"><div class="kpi-label">Converged</div><div class="kpi-value">' + (os.one_stage.converged ? 'Yes' : 'No') + '</div></div>' +
        '<div class="kpi"><div class="kpi-label">Solver</div><div class="kpi-value">lme4 ' + (os.one_stage.lme4_version || rRes.one_stage.lme4_version || 'unknown') + '</div></div>' +
        '</div>';
      document.getElementById('onestage-methods').innerHTML =
        '<p><strong>Methodology:</strong> One-stage Poisson hierarchical model fit by R using <code>lme4::glmer(events ~ dose + (1 | studlab), offset = log(n), family = poisson(link = "log"))</code> with the bobyqa optimizer. ' +
        'Per-arm event counts modelled on the log-rate scale; person-years (here approximated by <code>n</code>) enter as an offset. ' +
        'Random intercept per study captures between-study baseline-rate variation. ' +
        'The engine surfaces the precomputed R coefficients only — no JS-side fitter for one-stage, per spec §11.</p>';

      // === Tab 4: R-parity badge ===
      window.RValidationDoseresp.render('r-parity-doseresp',
        { linear: lin, rcs: rcs, one_stage: os },
        rRes);
      return rRes;
    })
    .catch(function (e) {
      console.error('[ALCOHOL_BC] failed to load R JSON:', e);
      document.getElementById('onestage-kpis').innerHTML =
        '<div style="color:#c00">One-stage tab unavailable: ' + e.message + '</div>';
      document.getElementById('r-parity-doseresp').innerHTML =
        '<div style="color:#c00">R-parity badge unavailable: ' + e.message + '</div>';
    });
```

- [ ] **Step 2: Browser smoke — but `fetch()` from `file://` won't work**

`file://` origins block `fetch()` in modern browsers. Two options for the smoke test:

**Option A — local HTTP server:**
```bash
cd /c/Projects/Finrenone && python -m http.server 8765 &
# In a separate terminal or after a sleep:
python -c "import webbrowser; webbrowser.open('http://localhost:8765/ALCOHOL_BC_DOSE_RESP_REVIEW.html')"
```

After verification, kill the server (`Ctrl-C` or `kill %1`).

**Option B — substitute fetch with inline embed:** if the R JSON is small (<10 KB), embed it as a second `<script type="application/json" id="r-precomputed">` block. Skipping the fetch entirely. For Round 1B the R JSON is ~1-2 KB so this is viable. Use this fallback if Option A is blocked. The wiring change: replace the `fetch(...)` chain with `var rRes = JSON.parse(document.getElementById('r-precomputed').textContent);` followed by the body of the `.then`.

**This task uses Option A** (HTTP server). If the executor cannot run a local server for any reason, they may fall back to Option B and note in the commit message.

- [ ] **Step 3: Verify Tab 3 in the browser**

Click "3. One-stage (Poisson glmer)" tab.

Verify:
- 5 KPI cards (coef_dose, RR per 11g, random-effects var, Converged Yes/No, Solver lme4 version)
- Coefficient ≈ 0.006 per gram (RR per 11g ≈ 1.07)
- Converged: Yes
- Random-effects variance ≥ 0 (small positive value)
- Methodology paragraph renders below KPIs
- DevTools Console: no errors

Click "4. R-parity badge" tab.

Verify:
- Collapsible badge panel appears, default-open
- 5 rows: linear slope, linear τ², RCS coef[0], RCS coef[1], non-linearity Wald p
- First 4 rows green (engine within tolerance of R); last row amber (designed)
- Header banner amber overall (because of the always-amber last row)
- Disclosure paragraph at the bottom explains the diagonal-PM tradeoff

- [ ] **Step 4: Commit**

```bash
cd /c/Projects/Finrenone && git add ALCOHOL_BC_DOSE_RESP_REVIEW.html && git commit -m "feat(dose-response): populate One-stage + R-parity tabs via fetch (round 1B)"
```

---

## Task 10: Final smoke + close Round 1B

**Files:**
- None changed in this task; verification only.

- [ ] **Step 1: Engine test suite green**

```bash
cd /c/Projects/Finrenone && node tests/test_dose_response_engine.mjs 2>&1 | tail -5
```

Expected: `35 passed, 0 failed`.

If anything is red, STOP — likely a regression introduced by F-2 or F-3.

- [ ] **Step 2: Browser end-to-end smoke (via HTTP server)**

```bash
cd /c/Projects/Finrenone && python -m http.server 8765 &
sleep 1 && python -c "import webbrowser; webbrowser.open('http://localhost:8765/ALCOHOL_BC_DOSE_RESP_REVIEW.html')"
```

Click through all 4 tabs in order. Verify for each:
- No console errors (open DevTools → Console)
- All numeric values render (no NaN, no undefined, no "n/a" where data exists)
- Tables and KPIs are visually well-aligned (no broken HTML)

Kill the HTTP server after verification.

- [ ] **Step 3: Sentinel scan**

```bash
cd /c/Projects/Finrenone && python -m sentinel scan --repo .
```

Expected: BLOCK=0 on touched files (`rapidmeta-dose-response-engine-v1.js`, `tests/test_dose_response_engine.mjs`, `scripts/r_validate_doseresp.R`, `outputs/r_validation/doseresp/gl1992_alcohol_bc.json`, `vendor/r-validation-doseresp.js`, `ALCOHOL_BC_DOSE_RESP_REVIEW.html`).

WARN entries on other (parallel-session) files are not this round's concern.

- [ ] **Step 4: Final close commit**

```bash
cd /c/Projects/Finrenone && git commit --allow-empty -m "$(cat <<'EOF'
close: Round 1B complete — dose-response pack flagship + engine P1 fixes

Deliverables:
- ALCOHOL_BC_DOSE_RESP_REVIEW.html — 4-tab flagship on GL-1992
- vendor/r-validation-doseresp.js — R-parity badge UI
- Engine F-2 fix (predict t_{k-1}) + F-3 fix (forest tau2 on RCS)
- R script glmer one-stage block + regenerated JSON
- 35 engine tests passing (33 from Round 1A + 2 new regression pins)
- Sentinel BLOCK=0

Deferred to Round 2:
- SGLT2I_DOSE_RESP_REVIEW.html (per-arm dose data sourcing)
- F-1 (zero-cell continuity correction) + F-4 (shutil.which Rscript)
- Full multivariate REML for fitRCS (P2 hardening)
- Q-profile tau^2 CI for fitLinear (P2 hardening)
- Automated Playwright browser test
EOF
)"
```

---

## Done conditions (Round 1B)

| Deliverable | Path | Verification |
|---|---|---|
| Engine F-2 fix | `rapidmeta-dose-response-engine-v1.js` | new t-critical test passes |
| Engine F-3 fix | `rapidmeta-dose-response-engine-v1.js` | new RCS-forest test passes |
| R script one-stage | `scripts/r_validate_doseresp.R` | output JSON has `one_stage.converged: true` |
| Regenerated R JSON | `outputs/r_validation/doseresp/gl1992_alcohol_bc.json` | one_stage block present |
| Badge JS | `vendor/r-validation-doseresp.js` | headless smoke renders 5 rows |
| Flagship HTML | `ALCOHOL_BC_DOSE_RESP_REVIEW.html` | all 4 tabs render in browser without console errors |
| Engine tests | `tests/test_dose_response_engine.mjs` | 35 / 35 passing |
| Sentinel | `STUCK_FAILURES.jsonl` | BLOCK=0 on touched files |
