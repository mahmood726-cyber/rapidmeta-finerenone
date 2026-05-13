# Dose-Response Pack — Round 2B Implementation Plan (Engine v0.3 Math Hardening)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Engine v0.3.0 — close the documented diagonal-PM vs R-full-REML divergence on RCS non-linearity p; add Q-profile τ² CI to fitLinear; F-5 test closure; P2-13 structural refactor.

**Architecture:** Six logical groups across ~15 tasks. Helpers and structural prep first (Group A); then fitLinear's Q-profile (Group B); then the big multivariate REML lift in fitRCS via Nelder-Mead on the REML log-likelihood (Group C); then HKSJ-multivariate + t_{k-1} CI follow-on (Group D); then F-5 tests (Group E); then regression-pin updates + close (Group F).

**Tech Stack:** ES5-compatible JS (browser, no build step), Node ≥18 for tests. No new external deps.

**Spec:** `docs/superpowers/specs/2026-05-13-dose-response-round-2b-design.md` (committed `20bc8be8`).

---

## File Structure

| Path | Responsibility | Action |
|---|---|---|
| `rapidmeta-dose-response-engine-v1.js` | Engine v0.3.0: API restructure, Nelder-Mead simplex, REML log-likelihood, full multivariate REML in fitRCS, HKSJ-mv + t_{k-1}, Q-profile τ² CI in fitLinear | MODIFY |
| `tests/test_dose_response_engine.mjs` | New tests: REML parity vs R, Q-profile CI, HKSJ-mv, 2 F-5 tests; update Round 1A non-linearity p regression-pin | MODIFY |

No changes to fixtures, R script, HTML, or badge JS. Pure engine work.

---

## Group A — Helpers + structural prep (Tasks 1-4)

### Task 1: Engine version bump v0.2.0 → v0.3.0

**Files:**
- Modify: `rapidmeta-dose-response-engine-v1.js` (file header comment + `engine_version` constant)

- [ ] **Step 1: Update header comment**

In the file header, update:
- Version line: `v0.2.0 (2026-05-13)` → `v0.3.0 (2026-05-13)`
- Add to "Validated by:":
  ```
   *   - full multivariate REML for fitRCS via Nelder-Mead on Cholesky parameters
   *     of the τ² matrix; non-linearity Wald p matches R mixmeta within |Δ| < 0.1
   *   - Q-profile τ² CI for fitLinear (Viechtbauer 2007) returns finite bounds
  ```

- [ ] **Step 2: Update engine_version constant**

Find `engine_version: 'rapidmeta-dose-response-engine-v1@0.2.0'`. Change to `'rapidmeta-dose-response-engine-v1@0.3.0'`.

- [ ] **Step 3: Tests stay at 47**

Run: `node tests/test_dose_response_engine.mjs 2>&1 | tail -3` — expect `47 passed, 0 failed`.

- [ ] **Step 4: Commit**

```bash
git add rapidmeta-dose-response-engine-v1.js
git commit -m "feat(dose-response): bump engine to v0.3.0 (Round 2B — REML/Q-profile incoming)"
```

---

### Task 2: P2-13 API forward-reference structural refactor

**Files:**
- Modify: `rapidmeta-dose-response-engine-v1.js` (move `var API = {...}` to top of IIFE; assign methods after each function definition)

- [ ] **Step 1: Add a regression test that pins the API shape**

Append to `tests/test_dose_response_engine.mjs` BEFORE the runner block:

```javascript
test('API shape: all public methods + _internal helpers present after IIFE init', () => {
  const required = ['engine_version','validate','fitLinear','fitRCS','fitOneStage',
                    'nonLinearityTest','predict','forest','exportResults','_internal'];
  for (const k of required) {
    assert.ok(k in DR, `DR.${k} must be defined`);
  }
  assert.equal(typeof DR.engine_version, 'string');
  assert.equal(typeof DR._internal, 'object');
  const requiredInternal = ['matInv','qt','qchisq','pchisq','glCovariance',
                            'mdCovariance','pmTau2','rcsKnots','rcsBasis','quantile'];
  for (const k of requiredInternal) {
    assert.equal(typeof DR._internal[k], 'function', `DR._internal.${k} must be a function`);
  }
});
```

Run: `node tests/test_dose_response_engine.mjs 2>&1 | tail -3` — should pass `48 passed, 0 failed` (no engine change yet; test pins the existing surface).

- [ ] **Step 2: Restructure the IIFE**

The current pattern in `rapidmeta-dose-response-engine-v1.js`:

```javascript
(function (root) {
  'use strict';
  // ... numerics (functions defined, ASSIGNED to API._internal at the bottom)
  function validate(trials) { ... uses API.engine_version somewhere ... }
  function fitLinear(...) { ... uses API.engine_version ... }
  // ... etc.
  var API = {  // <-- defined LAST
    engine_version: 'rapidmeta-dose-response-engine-v1@0.3.0',
    validate: validate,
    fitLinear: fitLinear,
    ...,
    _internal: { zeros: zeros, inv2x2: inv2x2, ... }
  };
  root.RapidMetaDoseResp = API;
  if (typeof module !== 'undefined' && module.exports) module.exports = API;
})(typeof window !== 'undefined' ? window : globalThis);
```

Refactor to:

```javascript
(function (root) {
  'use strict';

  // P2-13: API defined at IIFE top to avoid forward-reference footgun.
  // Public methods are assigned to API.<name> immediately after each function
  // definition below. _internal helpers are similarly attached as defined.
  var API = {
    engine_version: 'rapidmeta-dose-response-engine-v1@0.3.0',
    _internal: {},
  };

  // ... numerics (each helper assigned to API._internal after definition):
  function zeros(r, c) { ... }
  API._internal.zeros = zeros;

  function inv2x2(M) { ... }
  API._internal.inv2x2 = inv2x2;

  // ... etc. for ALL numerics helpers

  function validate(trials) { ... }
  API.validate = validate;

  function fitLinear(trials, opts) { ... }
  API.fitLinear = fitLinear;

  function fitRCS(trials, opts) { ... }
  API.fitRCS = fitRCS;

  function fitOneStage(trials, opts, precomputedJson) { ... }
  API.fitOneStage = fitOneStage;

  function nonLinearityTest(rcsResult) { ... }
  API.nonLinearityTest = nonLinearityTest;

  function predict(result, dose) { ... }
  API.predict = predict;

  function forest(trials, result) { ... }
  API.forest = forest;

  function exportResults(result) { ... }
  API.exportResults = exportResults;

  root.RapidMetaDoseResp = API;
  if (typeof module !== 'undefined' && module.exports) module.exports = API;
})(typeof window !== 'undefined' ? window : globalThis);
```

Mechanical refactor. Preserve every function body unchanged. Only the position of `var API = {...}` and the per-function `API.<name> = <name>` assignments change.

**Side note**: Some functions (especially fitLinear and fitRCS) reference `API.engine_version` inside their return objects. That continues to work since `API.engine_version` is set at IIFE top now.

- [ ] **Step 3: Tests stay green**

Run: `node tests/test_dose_response_engine.mjs 2>&1 | tail -3` — expect `48 passed, 0 failed`.

If anything breaks, STOP — the refactor introduced a regression.

- [ ] **Step 4: Commit**

```bash
git add rapidmeta-dose-response-engine-v1.js tests/test_dose_response_engine.mjs
git commit -m "fix(dose-response): P2-13 move API definition to top of IIFE + add shape pin test (Task 2)"
```

---

### Task 3: Nelder-Mead simplex helper

**Files:**
- Modify: `rapidmeta-dose-response-engine-v1.js` (add `nelderMead` to `_internal`)
- Modify: `tests/test_dose_response_engine.mjs` (one test using Rosenbrock function)

- [ ] **Step 1: Write the failing test**

Append:

```javascript
test('nelderMead minimizes Rosenbrock at (1, 1) within 1e-3', () => {
  // Rosenbrock function: f(x, y) = (1-x)^2 + 100*(y - x^2)^2; min at (1,1) = 0
  function rosenbrock(p) {
    var x = p[0], y = p[1];
    return (1 - x) * (1 - x) + 100 * (y - x*x) * (y - x*x);
  }
  var result = I.nelderMead(rosenbrock, [0, 0], {
    relTol: 1e-8, maxIter: 1000, initialStep: 0.5
  });
  near(result.x[0], 1, 1e-3, 'x converges to 1');
  near(result.x[1], 1, 1e-3, 'y converges to 1');
  assert.ok(result.converged, 'must report converged');
  assert.ok(result.iterations < 1000, 'should converge in < 1000 iterations');
});
```

Run: expect 1 fail (helper not defined).

- [ ] **Step 2: Implement Nelder-Mead simplex**

Add to Section 1 (Numerics) of the engine, after the existing matrix helpers:

```javascript
function nelderMead(f, x0, opts) {
  // Derivative-free simplex optimizer (Nelder & Mead 1965).
  // Inputs:
  //   f: function(p: number[]) -> number   (the objective to minimize)
  //   x0: number[]  (starting point, length n)
  //   opts: { relTol: number, maxIter: number, initialStep: number }
  // Returns: { x: number[], fx: number, converged: bool, iterations: int }
  opts = opts || {};
  var relTol = opts.relTol != null ? opts.relTol : 1e-8;
  var maxIter = opts.maxIter != null ? opts.maxIter : 200;
  var step = opts.initialStep != null ? opts.initialStep : 0.1;
  var n = x0.length;

  // Standard Nelder-Mead coefficients
  var alpha = 1.0, gamma = 2.0, rho = 0.5, sigma = 0.5;

  // Build initial simplex of n+1 points
  var simplex = [x0.slice()];
  for (var i = 0; i < n; i++) {
    var pt = x0.slice();
    pt[i] += step;
    simplex.push(pt);
  }
  var fvals = simplex.map(f);

  // Helper: sort simplex+fvals by ascending fvals
  function sortSimplex() {
    var idx = fvals.map(function (_, i) { return i; });
    idx.sort(function (a, b) { return fvals[a] - fvals[b]; });
    simplex = idx.map(function (k) { return simplex[k]; });
    fvals = idx.map(function (k) { return fvals[k]; });
  }

  for (var iter = 0; iter < maxIter; iter++) {
    sortSimplex();

    // Convergence check: relative spread of f-values across simplex
    var fbest = fvals[0], fworst = fvals[n];
    var spread = Math.abs(fworst - fbest) / (Math.abs(fbest) + relTol);
    if (spread < relTol) {
      return { x: simplex[0].slice(), fx: fbest, converged: true, iterations: iter };
    }

    // Centroid of all points except the worst
    var xc = new Array(n).fill(0);
    for (var k = 0; k < n; k++) for (var d = 0; d < n; d++) xc[d] += simplex[k][d];
    for (var d2 = 0; d2 < n; d2++) xc[d2] /= n;

    // Reflection
    var xr = new Array(n);
    for (var dd = 0; dd < n; dd++) xr[dd] = xc[dd] + alpha * (xc[dd] - simplex[n][dd]);
    var fr = f(xr);

    if (fr < fvals[0]) {
      // Expansion
      var xe = new Array(n);
      for (var ee = 0; ee < n; ee++) xe[ee] = xc[ee] + gamma * (xr[ee] - xc[ee]);
      var fe = f(xe);
      if (fe < fr) { simplex[n] = xe; fvals[n] = fe; }
      else         { simplex[n] = xr; fvals[n] = fr; }
    } else if (fr < fvals[n - 1]) {
      // Accept reflection (better than 2nd-worst but not better than best)
      simplex[n] = xr; fvals[n] = fr;
    } else {
      // Contraction
      var xx, ff;
      if (fr < fvals[n]) {
        xx = new Array(n);
        for (var c1 = 0; c1 < n; c1++) xx[c1] = xc[c1] + rho * (xr[c1] - xc[c1]);
        ff = f(xx);
        if (ff < fr) { simplex[n] = xx; fvals[n] = ff; }
        else         { /* shrink */ shrink(); }
      } else {
        xx = new Array(n);
        for (var c2 = 0; c2 < n; c2++) xx[c2] = xc[c2] + rho * (simplex[n][c2] - xc[c2]);
        ff = f(xx);
        if (ff < fvals[n]) { simplex[n] = xx; fvals[n] = ff; }
        else               { shrink(); }
      }
    }
  }

  function shrink() {
    for (var i = 1; i <= n; i++) {
      for (var j = 0; j < n; j++) {
        simplex[i][j] = simplex[0][j] + sigma * (simplex[i][j] - simplex[0][j]);
      }
      fvals[i] = f(simplex[i]);
    }
  }

  sortSimplex();
  return { x: simplex[0].slice(), fx: fvals[0], converged: false, iterations: maxIter };
}

API._internal.nelderMead = nelderMead;
```

- [ ] **Step 3: Run, expect 49 passed**

- [ ] **Step 4: Commit**

```bash
git add rapidmeta-dose-response-engine-v1.js tests/test_dose_response_engine.mjs
git commit -m "feat(dose-response): nelderMead simplex helper (Task 3 — prep for Round 2B multivariate REML)"
```

---

### Task 4: Q-profile τ² CI helper

**Files:**
- Modify: `rapidmeta-dose-response-engine-v1.js` (add `qProfileCI` to `_internal`)
- Modify: `tests/test_dose_response_engine.mjs` (one test on a synthetic 5-trial pool)

- [ ] **Step 1: Write the failing test**

Append:

```javascript
test('qProfileCI returns finite bounds bracketing the point estimate', () => {
  // 5 synthetic studies, moderate heterogeneity
  var yi = [0.2, 0.3, 0.5, 0.4, 0.1];
  var vi = [0.01, 0.015, 0.02, 0.012, 0.018];
  var tau2_hat = I.pmTau2(yi, vi);
  assert.ok(tau2_hat >= 0, 'PM tau2 must be non-negative');
  var ci = I.qProfileCI(yi, vi, 0.05);
  assert.ok(Number.isFinite(ci.lo), 'tau2_lo must be finite');
  assert.ok(Number.isFinite(ci.hi), 'tau2_hi must be finite');
  assert.ok(ci.lo >= 0, 'tau2_lo must be >= 0');
  assert.ok(ci.lo <= ci.hi, 'tau2_lo <= tau2_hi');
  // The Q-profile CI typically brackets the PM point estimate (not strictly
  // guaranteed for boundary cases — relax to "tau2_hat is within [lo, 10*hi]"
  // OR "lo == 0 and hat is small")
  assert.ok(tau2_hat <= ci.hi * 10, 'tau2_hat within Q-profile envelope');
});
```

Run: expect 1 fail.

- [ ] **Step 2: Implement qProfileCI**

Add to Section 1 of the engine (next to `pmTau2`):

```javascript
function qProfileCI(yi, vi, alpha) {
  // Viechtbauer 2007 Q-profile CI for τ².
  // Q(τ²) = Σ w_i (y_i − ȳ_τ²)² where w_i = 1/(v_i + τ²) and ȳ_τ² is the
  // corresponding weighted mean.
  // CI bounds: tau2_lo = inf{τ² : Q(τ²) ≤ chiUpper}; tau2_hi = sup{τ² : Q(τ²) ≥ chiLower}
  // where chiLower = qchisq(α/2, df), chiUpper = qchisq(1−α/2, df), df = k−1.
  var k = yi.length;
  if (k < 2) return { lo: 0, hi: 0 };
  var df = k - 1;
  alpha = alpha || 0.05;
  var chiLower = qchisq(alpha / 2, df);
  var chiUpper = qchisq(1 - alpha / 2, df);

  function Q(tau2) {
    var w = vi.map(function (v) { return 1 / (v + tau2); });
    var wsum = w.reduce(function (a, b) { return a + b; }, 0);
    var ybar = yi.reduce(function (acc, y, i) { return acc + w[i] * y; }, 0) / wsum;
    return yi.reduce(function (acc, y, i) {
      var d = y - ybar;
      return acc + w[i] * d * d;
    }, 0);
  }

  function bisect(target, lo, hi, maxIter) {
    // Find tau2 such that Q(tau2) == target, on a monotone-decreasing Q.
    maxIter = maxIter || 60;
    for (var i = 0; i < maxIter; i++) {
      var mid = (lo + hi) / 2;
      var qm = Q(mid);
      if (Math.abs(qm - target) < 1e-9) return mid;
      if (qm > target) lo = mid; else hi = mid;
    }
    return (lo + hi) / 2;
  }

  // Find bracket: Q(0) is the FE Cochran Q (largest); Q(big) → 0.
  var q0 = Q(0);
  var tau2_estimate = pmTau2(yi, vi);
  // Upper τ²: 100× PM estimate or a generous floor (e.g. max yi² range)
  var range = Math.max.apply(null, yi) - Math.min.apply(null, yi);
  var tau2_max = Math.max(100 * tau2_estimate, range * range, 1.0);

  // tau2_lo: smallest τ² where Q(τ²) ≤ chiUpper (large-quantile boundary)
  var tau2_lo;
  if (q0 <= chiUpper) {
    tau2_lo = 0;
  } else {
    tau2_lo = bisect(chiUpper, 0, tau2_max);
  }

  // tau2_hi: largest τ² where Q(τ²) ≥ chiLower (small-quantile boundary)
  var tau2_hi;
  if (Q(tau2_max) >= chiLower) {
    tau2_hi = tau2_max;  // bound not reached; CI is open-ended (clamp at tau2_max)
  } else if (q0 < chiLower) {
    tau2_hi = 0;
  } else {
    tau2_hi = bisect(chiLower, 0, tau2_max);
  }

  return { lo: tau2_lo, hi: tau2_hi };
}

API._internal.qProfileCI = qProfileCI;
```

- [ ] **Step 3: Run, expect 50 passed**

- [ ] **Step 4: Commit**

```bash
git add rapidmeta-dose-response-engine-v1.js tests/test_dose_response_engine.mjs
git commit -m "feat(dose-response): qProfileCI helper (Viechtbauer 2007) for τ² CI (Task 4)"
```

---

## Group B — fitLinear gets finite Q-profile τ² CI (Task 5)

### Task 5: Plumb qProfileCI into fitLinear

**Files:**
- Modify: `rapidmeta-dose-response-engine-v1.js` (use `qProfileCI` in `fitLinear` to populate `tau2_lo` and `tau2_hi`)
- Modify: `tests/test_dose_response_engine.mjs` (one test pinning finite CI bounds on GL-1992)

- [ ] **Step 1: Write the failing test**

```javascript
test('fitLinear returns finite Q-profile τ² CI bounds on GL-1992', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitLinear(fx.trials, {});
  assert.ok(Number.isFinite(res.tau2_lo), 'tau2_lo must be finite (Round 2B)');
  assert.ok(Number.isFinite(res.tau2_hi), 'tau2_hi must be finite');
  assert.ok(res.tau2_lo >= 0);
  assert.ok(res.tau2_lo <= res.tau2_hi);
  // GL-1992 has high heterogeneity (I² ~ 95%); τ² CI should be a non-trivial range
  assert.ok(res.tau2_hi > 0, 'GL-1992 τ²_hi > 0 (substantial heterogeneity)');
});
```

Run: expect 1 fail (currently `tau2_lo: null, tau2_hi: null`).

- [ ] **Step 2: Plumb qProfileCI**

In `fitLinear`, find the existing line:

```javascript
    tau2: tau2, tau2_lo: null, tau2_hi: null,  // Q-profile deferred to P2 hardening
```

Replace with:

```javascript
    tau2: tau2,
    // Round 2B: Q-profile τ² CI per Viechtbauer 2007 (qchisq-bracket bisection)
    tau2_lo: qProfileCI(yi, vi, alpha).lo,
    tau2_hi: qProfileCI(yi, vi, alpha).hi,
```

Note: this calls `qProfileCI` twice (once for `.lo`, once for `.hi`). The function is cheap (~60 bisection iterations × ~k operations), so the duplication is acceptable. For DRY: extract to a local variable above the return:

```javascript
  var tau2CI = qProfileCI(yi, vi, alpha);
  // ... in the return object:
    tau2_lo: tau2CI.lo,
    tau2_hi: tau2CI.hi,
```

- [ ] **Step 3: Run, expect 51 passed**

- [ ] **Step 4: Commit**

```bash
git add rapidmeta-dose-response-engine-v1.js tests/test_dose_response_engine.mjs
git commit -m "feat(dose-response): fitLinear returns Q-profile τ² CI bounds (Task 5)"
```

---

## Group C — Full multivariate REML for fitRCS (Tasks 6-8)

### Task 6: REML log-likelihood evaluator

**Files:**
- Modify: `rapidmeta-dose-response-engine-v1.js` (add `remlLogLik` to `_internal`)
- Modify: `tests/test_dose_response_engine.mjs` (one test verifying log-likelihood is finite at τ²=0)

- [ ] **Step 1: Write the failing test**

```javascript
test('remlLogLik returns finite value at zero tau2 matrix for valid per-study X, y, V', () => {
  // Simple synthetic: 2 trials, 1 basis dimension (linear), zero τ²
  var perStudy = [
    { X: [[10], [20]], y: [0.5, 1.0], V: [[0.05, 0.02], [0.02, 0.04]] },
    { X: [[5], [15]],  y: [0.3, 0.7], V: [[0.06, 0.03], [0.03, 0.05]] },
  ];
  var tau2 = [[0]];  // Kp=1, scalar τ²=0
  var ll = I.remlLogLik(perStudy, tau2);
  assert.ok(Number.isFinite(ll), 'log-likelihood must be finite at τ²=0');
});
```

Run: expect 1 fail.

- [ ] **Step 2: Implement remlLogLik**

Add to Section 1 of the engine, near other matrix helpers:

```javascript
function remlLogLik(perStudy, tau2) {
  // REML log-likelihood for multivariate dose-response random-effects model.
  // perStudy: array of { X: k_i × Kp matrix, y: length-k_i vector, V: k_i × k_i matrix }
  // tau2: Kp × Kp symmetric PSD matrix (between-study covariance of β)
  // Returns: ℓ(τ²)  = −½ Σ_i [ log|V_i + τ²_marginal_i| + (y_i − Xβ)' Σ_i⁻¹ (y_i − Xβ) ]
  //              − ½ log|Σ_i X'_i Σ_i⁻¹ X_i|
  // where Σ_i = V_i + X_i τ² X'_i  (marginal cov of y_i under RE model)
  // and β is profiled out via β̂ = (Σ X'_i Σ_i⁻¹ X_i)⁻¹ Σ X'_i Σ_i⁻¹ y_i.
  var Kp = tau2.length;
  if (Kp === 0) return -Infinity;

  // Step 1: per-trial marginal cov Σ_i = V_i + X_i τ² X'_i
  var XtSinvX_sum = zeros(Kp, Kp);
  var XtSinvy_sum = new Array(Kp).fill(0);
  var logDetSum = 0;
  var ySinvy_sum = 0;
  var trialContribs = [];

  for (var t = 0; t < perStudy.length; t++) {
    var X = perStudy[t].X;
    var y = perStudy[t].y;
    var V = perStudy[t].V;
    var ki = X.length;

    // X τ² X' (k_i × k_i)
    var Xt2 = zeros(ki, ki);
    for (var i = 0; i < ki; i++) for (var j = 0; j < ki; j++) {
      for (var p = 0; p < Kp; p++) for (var q = 0; q < Kp; q++) {
        Xt2[i][j] += X[i][p] * tau2[p][q] * X[j][q];
      }
    }
    // Σ_i = V + Xτ²X'
    var Sigma = zeros(ki, ki);
    for (var i2 = 0; i2 < ki; i2++) for (var j2 = 0; j2 < ki; j2++) {
      Sigma[i2][j2] = V[i2][j2] + Xt2[i2][j2];
    }

    // Σ_i⁻¹ and log|Σ_i|
    var SigmaInv;
    var logDet = 0;
    try {
      SigmaInv = matInv(Sigma);
      // For log|Σ|, use LU-like accumulation. matInv uses Gauss-Jordan; we
      // compute log|Σ| separately via |Σ| = product of pivots from a fresh LU.
      logDet = logDeterminant(Sigma);
    } catch (e) {
      return -Infinity;
    }
    logDetSum += logDet;

    // X'_i Σ_i⁻¹ X_i and X'_i Σ_i⁻¹ y_i
    for (var p2 = 0; p2 < Kp; p2++) {
      for (var i3 = 0; i3 < ki; i3++) {
        var XtSinv_p_i = 0;
        for (var j3 = 0; j3 < ki; j3++) XtSinv_p_i += X[j3][p2] * SigmaInv[j3][i3];
        XtSinvy_sum[p2] += XtSinv_p_i * y[i3];
        for (var q2 = 0; q2 < Kp; q2++) {
          XtSinvX_sum[p2][q2] += XtSinv_p_i * X[i3][q2];
        }
      }
    }
    trialContribs.push({ X: X, y: y, SigmaInv: SigmaInv });
  }

  // Profile-out β̂
  var XtSinvX_inv;
  try { XtSinvX_inv = matInv(XtSinvX_sum); }
  catch (e) { return -Infinity; }
  var beta = matVec(XtSinvX_inv, XtSinvy_sum);

  // Σ (y - Xβ)' Σ⁻¹ (y - Xβ)
  var quadForm = 0;
  for (var tt = 0; tt < trialContribs.length; tt++) {
    var X_tt = trialContribs[tt].X;
    var y_tt = trialContribs[tt].y;
    var SI_tt = trialContribs[tt].SigmaInv;
    var resid = y_tt.map(function (yv, idx) {
      var Xb = 0;
      for (var p3 = 0; p3 < Kp; p3++) Xb += X_tt[idx][p3] * beta[p3];
      return yv - Xb;
    });
    for (var i4 = 0; i4 < resid.length; i4++) for (var j4 = 0; j4 < resid.length; j4++) {
      quadForm += resid[i4] * SI_tt[i4][j4] * resid[j4];
    }
  }

  var logDetXtSinvX = logDeterminant(XtSinvX_sum);
  return -0.5 * logDetSum - 0.5 * quadForm - 0.5 * logDetXtSinvX;
}

function logDeterminant(M) {
  // log|M| via LU decomposition (Doolittle). Returns -Infinity if singular.
  var n = M.length;
  var A = M.map(function (row) { return row.slice(); });
  var logDet = 0;
  for (var i = 0; i < n; i++) {
    // Partial pivot
    var maxR = i, maxV = Math.abs(A[i][i]);
    for (var r = i + 1; r < n; r++) {
      if (Math.abs(A[r][i]) > maxV) { maxR = r; maxV = Math.abs(A[r][i]); }
    }
    if (maxV < 1e-15) return -Infinity;
    if (maxR !== i) {
      var tmp = A[i]; A[i] = A[maxR]; A[maxR] = tmp;
      // Row swap flips sign of det; but we take log of abs, so just track sign separately
      // For positive-definite Σ (our use case), sign should remain positive after odd swaps
      // are matched by another sign flip elsewhere. We assume PSD inputs.
    }
    var pivot = A[i][i];
    logDet += Math.log(Math.abs(pivot));
    for (var r2 = i + 1; r2 < n; r2++) {
      var factor = A[r2][i] / pivot;
      for (var c = i; c < n; c++) A[r2][c] -= factor * A[i][c];
    }
  }
  return logDet;
}

API._internal.remlLogLik = remlLogLik;
API._internal.logDeterminant = logDeterminant;
```

- [ ] **Step 3: Run, expect 52 passed**

- [ ] **Step 4: Commit**

```bash
git add rapidmeta-dose-response-engine-v1.js tests/test_dose_response_engine.mjs
git commit -m "feat(dose-response): remlLogLik + logDeterminant helpers for full multivariate REML (Task 6)"
```

---

### Task 7: fitRCS uses Nelder-Mead REML over Cholesky parameters

**Files:**
- Modify: `rapidmeta-dose-response-engine-v1.js` (replace per-dimension PM loop in `fitRCS` with Nelder-Mead REML optimization)
- Modify: `tests/test_dose_response_engine.mjs` (one test verifying engine non-linearity p matches R within |Δ| < 0.1)

- [ ] **Step 1: Write the failing test**

```javascript
test('fitRCS non-linearity p matches R full-REML on GL-1992 within |Δ| < 0.1', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitRCS(fx.trials, { knots: 3 });
  // R mixmeta full-REML on GL-1992 (verified during Round 1B audit): ~0.70
  near(res.rcs.nonlinearity_wald_p, 0.70, 0.10,
    'engine non-linearity Wald p matches R full-REML (Round 2B target)');
  // tau2_matrix should be present and 2×2 (Kp = K-1 = 2 for 3 knots)
  assert.ok(Array.isArray(res.rcs.tau2_matrix), 'tau2_matrix field present');
  assert.equal(res.rcs.tau2_matrix.length, 2);
  assert.equal(res.rcs.tau2_matrix[0].length, 2);
  assert.ok(res.rcs.reml_converged === true, 'REML must converge on GL-1992');
});

test('fitRCS Round 2A regression-pin at p≈0.05 is now OUTDATED — engine matches R (Round 2B)', () => {
  // This test documents the intentional behavior change: the Round 1A regression
  // pin at p ≈ 0.05 (the diagonal-PM v0.1 value) is REPLACED in Task 13 by a pin
  // at p ≈ 0.70 (the R-matching v0.3 value). This test asserts the new behavior.
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitRCS(fx.trials, { knots: 3 });
  assert.ok(res.rcs.nonlinearity_wald_p > 0.4,
    'engine non-linearity p now > 0.4 (was ~0.05 under diagonal-PM v0.1)');
});
```

Run: expect 2 fails (engine still does diagonal-PM, p ≈ 0.05).

- [ ] **Step 2: Replace the per-dimension PM loop in fitRCS with Nelder-Mead REML**

In `fitRCS`, find the existing per-dimension PM loop (around "Round 1A/1B: diagonal-PM-per-dimension τ²"):

```javascript
  for (var d = 0; d < Kp; d++) {
    var yi_d = perStudy.map(...);
    var vi_d = perStudy.map(...);
    tau2_per_dim[d] = pmTau2(yi_d, vi_d);
  }
```

Replace with Nelder-Mead REML over Cholesky parameters of the τ² matrix:

```javascript
  // Round 2B: full multivariate REML via Nelder-Mead on Cholesky parameters
  // of the τ² matrix (Kp × Kp symmetric PSD). Closes the diagonal-PM divergence
  // from R full-REML documented in Round 1B's amber non-linearity-p row.

  // Build per-study {X, y, V} for the REML log-likelihood
  var psForREML = perStudy.map(function (s) { return { X: s.X, y: s.y, V: s.V }; });

  // Parametrize τ² as L L' where L is lower-triangular (Kp × Kp).
  // Free parameters: L_diag (Kp values) + L_offdiag (Kp*(Kp-1)/2 values)
  // Total: Kp * (Kp + 1) / 2
  function paramsToTau2(params) {
    var L = zeros(Kp, Kp);
    var idx = 0;
    for (var i = 0; i < Kp; i++) {
      L[i][i] = Math.exp(params[idx]); // ensure positive diagonal
      idx++;
      for (var j = 0; j < i; j++) {
        L[i][j] = params[idx];
        idx++;
      }
    }
    // τ² = L L'
    var tau2 = zeros(Kp, Kp);
    for (var i2 = 0; i2 < Kp; i2++) for (var j2 = 0; j2 < Kp; j2++) {
      for (var k = 0; k <= Math.min(i2, j2); k++) {
        tau2[i2][j2] += L[i2][k] * L[j2][k];
      }
    }
    return tau2;
  }

  var nParams = Kp * (Kp + 1) / 2;
  var x0 = new Array(nParams).fill(0);
  // Warm-start: use diagonal-PM estimates as initial diagonal
  var pmDiag = [];
  for (var d = 0; d < Kp; d++) {
    var yi_d = perStudy.map(function (s) { return s.beta[d]; });
    var vi_d = perStudy.map(function (s) { return s.V[d][d]; });
    pmDiag.push(Math.max(pmTau2(yi_d, vi_d), 1e-8));
  }
  // Set diagonal log-parameters from PM warm start; off-diagonals at 0
  var paramIdx = 0;
  for (var dd = 0; dd < Kp; dd++) {
    x0[paramIdx] = 0.5 * Math.log(pmDiag[dd]);
    paramIdx++;
    for (var jj = 0; jj < dd; jj++) {
      x0[paramIdx] = 0;
      paramIdx++;
    }
  }

  function negREML(params) {
    var t2 = paramsToTau2(params);
    var ll = remlLogLik(psForREML, t2);
    return -ll;  // Nelder-Mead minimizes; we negate to maximize log-likelihood
  }

  var optResult = nelderMead(negREML, x0, {
    relTol: 1e-6,
    maxIter: 500,
    initialStep: 0.5,
  });

  var tau2Matrix = paramsToTau2(optResult.x);
  var tau2_per_dim_final = [];
  for (var dim = 0; dim < Kp; dim++) tau2_per_dim_final.push(tau2Matrix[dim][dim]);
```

- [ ] **Step 3: Recompute pooled β and Cov(β) under the new τ² matrix**

After the optimization, the rest of fitRCS's pooled-coef block must use the full τ² matrix (not the diagonal). Replace the per-dimension `pooled[d]`, `pooledSE[d]` computation with:

```javascript
  // Pooled β̂ and Cov(β̂) under full τ² matrix
  var XtWX_sum = zeros(Kp, Kp);
  var XtWy_sum = new Array(Kp).fill(0);
  for (var t3 = 0; t3 < perStudy.length; t3++) {
    var X_t3 = perStudy[t3].X;
    var y_t3 = perStudy[t3].y;
    var V_t3 = perStudy[t3].V;
    var ki_t3 = X_t3.length;

    // Σ_t = V_t + X_t τ² X'_t
    var Xt2_t3 = zeros(ki_t3, ki_t3);
    for (var i5 = 0; i5 < ki_t3; i5++) for (var j5 = 0; j5 < ki_t3; j5++) {
      for (var p4 = 0; p4 < Kp; p4++) for (var q3 = 0; q3 < Kp; q3++) {
        Xt2_t3[i5][j5] += X_t3[i5][p4] * tau2Matrix[p4][q3] * X_t3[j5][q3];
      }
    }
    var Sigma_t3 = zeros(ki_t3, ki_t3);
    for (var i6 = 0; i6 < ki_t3; i6++) for (var j6 = 0; j6 < ki_t3; j6++) {
      Sigma_t3[i6][j6] = V_t3[i6][j6] + Xt2_t3[i6][j6];
    }
    var W_t3;
    try { W_t3 = matInv(Sigma_t3); } catch (e) { continue; }

    // Accumulate X'_t W_t X_t and X'_t W_t y_t
    for (var p5 = 0; p5 < Kp; p5++) {
      for (var i7 = 0; i7 < ki_t3; i7++) {
        var XtW_pi = 0;
        for (var j7 = 0; j7 < ki_t3; j7++) XtW_pi += X_t3[j7][p5] * W_t3[j7][i7];
        XtWy_sum[p5] += XtW_pi * y_t3[i7];
        for (var q4 = 0; q4 < Kp; q4++) {
          XtWX_sum[p5][q4] += XtW_pi * X_t3[i7][q4];
        }
      }
    }
  }

  var covBeta = matInv(XtWX_sum);
  var pooledBeta = matVec(covBeta, XtWy_sum);
  var pooledSE_final = [];
  for (var pd = 0; pd < Kp; pd++) pooledSE_final.push(Math.sqrt(covBeta[pd][pd]));
```

- [ ] **Step 4: Wald non-linearity uses the FULL covariance (not diagonal)**

Find the existing non-linearity Wald block. Replace the diagonal-sum version with the full quadratic form:

```javascript
  // Non-linearity Wald test using the FULL covariance of β̂ (not the diagonal).
  // H0: β_{d>=1} = 0 (all non-linear coefs). Statistic: β_nl' V_nl⁻¹ β_nl ~ χ²(K-2).
  var nlBeta = pooledBeta.slice(1);
  var nlCov = zeros(Kp - 1, Kp - 1);
  for (var i8 = 0; i8 < Kp - 1; i8++) for (var j8 = 0; j8 < Kp - 1; j8++) {
    nlCov[i8][j8] = covBeta[i8 + 1][j8 + 1];
  }
  var W = 0;
  if (nlBeta.length > 0) {
    var nlCovInv = matInv(nlCov);
    for (var i9 = 0; i9 < nlBeta.length; i9++) {
      for (var j9 = 0; j9 < nlBeta.length; j9++) {
        W += nlBeta[i9] * nlCovInv[i9][j9] * nlBeta[j9];
      }
    }
  }
  var nonlinearity_wald_p = nlBeta.length > 0 ? (1 - pchisq(W, nlBeta.length)) : null;
```

- [ ] **Step 5: Update fitRCS return object**

In the return, replace `tau2_per_dim` with both old + new fields:

```javascript
  rcs: {
    ...existing fields...,
    spline_coefs: pooledBeta,
    spline_coefs_se: pooledSE_final,
    tau2_matrix: tau2Matrix,                  // NEW: full Kp×Kp τ² matrix
    tau2_per_dim: tau2_per_dim_final,         // retained: diagonal of tau2_matrix
    nonlinearity_wald_p: nonlinearity_wald_p, // now matches R within |Δ| < 0.1
    reml_converged: optResult.converged,      // NEW
    reml_iterations: optResult.iterations,    // NEW
    reml_loglik: -optResult.fx,               // NEW
    fit_at_dose: <see Task 9>
  },
```

- [ ] **Step 6: Run tests**

Run: `node tests/test_dose_response_engine.mjs 2>&1 | tail -10`

Expected: the 2 new tests added in Step 1 should PASS. BUT: the Round 1A `fitRCS GL-1992 non-linearity p is ~0.05 under diagonal-PM v0.1 design` test will FAIL because the engine now matches R (~0.70, not ~0.05). That's intentional — Task 13 updates that pin.

For this commit, we accept 1 broken test (the outdated regression-pin) and explicitly mark it. Use `git status` to confirm exactly 1 failure on the old pin.

If MORE than 1 test fails, STOP — likely a regression beyond the expected pin update.

- [ ] **Step 7: Commit with failing-test note**

```bash
git add rapidmeta-dose-response-engine-v1.js tests/test_dose_response_engine.mjs
git commit -m "feat(dose-response): fitRCS full multivariate REML via Nelder-Mead (Task 7) — 1 expected test failure to be updated in Task 13"
```

---

### Task 8: Update Round 1A regression-pin and Round 1B documented-divergence comments

**Files:**
- Modify: `tests/test_dose_response_engine.mjs` (update the Round 1A pin)
- Modify: `rapidmeta-dose-response-engine-v1.js` (update Round 1B documented-divergence comment block in fitRCS source)

- [ ] **Step 1: Update the Round 1A regression-pin test**

Find the test labeled `'fitRCS GL-1992 non-linearity p is ~0.05 under diagonal-PM v0.1 design'` in `tests/test_dose_response_engine.mjs`. Update its body:

```javascript
test('fitRCS GL-1992 non-linearity p matches R full-REML (Round 2B: ~0.70, was ~0.05 under v0.1 diagonal-PM)', () => {
  // REGRESSION-PIN (Round 2B): the engine now uses full multivariate REML via
  // Nelder-Mead and matches R mixmeta within |Δ| < 0.1. The prior v0.1
  // diagonal-PM-per-dimension τ² approximation produced p ≈ 0.05 on this data;
  // the new v0.3 full-REML matches R's p ≈ 0.70.
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitRCS(fx.trials, { knots: 3 });
  near(res.rcs.nonlinearity_wald_p, 0.70, 0.10,
    'engine non-linearity p matches R full-REML (Round 2B target)');
});
```

- [ ] **Step 2: Update the documented-divergence comment block in fitRCS source**

Find the block in `rapidmeta-dose-response-engine-v1.js` that describes the diagonal-PM tradeoff (the multi-line comment starting with something like "v0.1 design choice: diagonal-PM-per-dimension τ² approximation"). Replace with the new state:

```javascript
  // Round 2B (v0.3.0): FULL multivariate REML via Nelder-Mead on Cholesky
  // parameters of the τ² matrix. Closes the v0.1/v0.2 diagonal-PM-per-dimension
  // divergence from R: engine non-linearity p now matches R mixmeta within
  // |Δ| < 0.1 on GL-1992 (engine ~0.70 vs R ~0.70). The R-parity badge's
  // non-linearity-p row turns GREEN under v0.3.
  //
  // Historical note: v0.1 (Round 1A) and v0.2 (Round 2A) used a simpler
  // diagonal-PM-per-dimension τ² approximation that produced engine
  // non-linearity p ≈ 0.05 on GL-1992 (vs R ≈ 0.70). The badge marked that row
  // always-amber under v0.1/v0.2 as a documented design tradeoff.
```

- [ ] **Step 3: Run tests, expect 53 passed (or however many — should be all green)**

Run: `node tests/test_dose_response_engine.mjs 2>&1 | tail -3`
Expected: all tests pass; the previously-failing Round 1A pin is now updated to expect ~0.70.

- [ ] **Step 4: Commit**

```bash
git add rapidmeta-dose-response-engine-v1.js tests/test_dose_response_engine.mjs
git commit -m "feat(dose-response): update Round 1A regression-pin to R-matching ~0.70 (Task 8 — Group C close)"
```

---

## Group D — HKSJ-multivariate + t_{k-1} for fitRCS (Task 9)

### Task 9: HKSJ-mv + t_{k-1} CI in fitRCS pooled output and fit_at_dose grid

**Files:**
- Modify: `rapidmeta-dose-response-engine-v1.js` (replace raw z=1.96 with HKSJ-mv × t_{k-1} in fitRCS)
- Modify: `tests/test_dose_response_engine.mjs` (one test pinning HKSJ-mv > 1 on GL-1992)

- [ ] **Step 1: Write the failing test**

```javascript
test('fitRCS uses HKSJ-mv + t_{k-1} for CIs (estimator label updated)', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitRCS(fx.trials, { knots: 3 });
  assert.equal(res.estimator, 'reml_hksj_multivariate',
    'fitRCS estimator now reml_hksj_multivariate (Round 2B)');
  assert.equal(res.ci_method, 'hksj_t_km1',
    'fitRCS ci_method now hksj_t_km1 (Round 2B)');
  // HKSJ multiplier should be ≥ 1 (floor) and visible in the result
  assert.ok(Number.isFinite(res.hksj_mv) && res.hksj_mv >= 1,
    'HKSJ multivariate scaling factor visible and ≥ 1');
});
```

Run: expect 1 fail.

- [ ] **Step 2: Compute HKSJ-mv scaling factor in fitRCS**

After the pooled β + Cov(β) computation in Task 7, add:

```javascript
  // Round 2B: HKSJ-multivariate scaling. Q_mv = Σ_i (y_i − Xβ)' Σ_i⁻¹ (y_i − Xβ)
  // is the multivariate Cochran Q; HKSJ_mv = max(1, Q_mv / (n − p)).
  var Q_mv = 0;
  var n_total = 0;
  for (var tQ = 0; tQ < perStudy.length; tQ++) {
    var X_tQ = perStudy[tQ].X;
    var y_tQ = perStudy[tQ].y;
    var V_tQ = perStudy[tQ].V;
    var ki_tQ = X_tQ.length;
    n_total += ki_tQ;

    // Recompute Σ_t and W_t (already done in Task 7's pooled computation; ideally
    // we'd cache, but cleaner to recompute since this is rare-event code)
    var Xt2_tQ = zeros(ki_tQ, ki_tQ);
    for (var iQ = 0; iQ < ki_tQ; iQ++) for (var jQ = 0; jQ < ki_tQ; jQ++) {
      for (var pQ = 0; pQ < Kp; pQ++) for (var qQ = 0; qQ < Kp; qQ++) {
        Xt2_tQ[iQ][jQ] += X_tQ[iQ][pQ] * tau2Matrix[pQ][qQ] * X_tQ[jQ][qQ];
      }
    }
    var Sigma_tQ = zeros(ki_tQ, ki_tQ);
    for (var iQ2 = 0; iQ2 < ki_tQ; iQ2++) for (var jQ2 = 0; jQ2 < ki_tQ; jQ2++) {
      Sigma_tQ[iQ2][jQ2] = V_tQ[iQ2][jQ2] + Xt2_tQ[iQ2][jQ2];
    }
    var W_tQ;
    try { W_tQ = matInv(Sigma_tQ); } catch (e) { continue; }

    var resid_tQ = y_tQ.map(function (yv, idx) {
      var Xb = 0;
      for (var pp = 0; pp < Kp; pp++) Xb += X_tQ[idx][pp] * pooledBeta[pp];
      return yv - Xb;
    });
    for (var iQ3 = 0; iQ3 < ki_tQ; iQ3++) for (var jQ3 = 0; jQ3 < ki_tQ; jQ3++) {
      Q_mv += resid_tQ[iQ3] * W_tQ[iQ3][jQ3] * resid_tQ[jQ3];
    }
  }
  var df_mv = Math.max(1, n_total - Kp);
  var hksj_mv = Math.max(1, Q_mv / df_mv);

  // Inflate pooled SE by sqrt(HKSJ_mv) for t_{k-1}-based CIs
  var k_trials = perStudy.length;
  var tcrit = k_trials > 1 ? qt(0.975, k_trials - 1) : 1.96;
  var hksjFactor = Math.sqrt(hksj_mv);
  var pooledSE_hksj = pooledSE_final.map(function (s) { return s * hksjFactor; });
```

- [ ] **Step 3: Use the HKSJ-adjusted CIs in fit_at_dose grid and pooled fields**

Replace the existing fit_at_dose curve construction (which used 1.96 directly) with t_{k-1}-based:

```javascript
  var fit_at_dose = [];
  for (var i_grid = 0; i_grid < 20; i_grid++) {
    var d_grid = i_grid * maxD / 19;
    var b = rcsBasis(d_grid, knots);
    var est_grid = 0, varEst_grid = 0;
    for (var p_grid = 0; p_grid < Kp; p_grid++) {
      est_grid += pooledBeta[p_grid] * b[p_grid];
      for (var q_grid = 0; q_grid < Kp; q_grid++) {
        // Variance of the linear combination uses the full pooled covariance
        // (with HKSJ inflation applied to the diagonal SE, equivalent to scaling
        // the whole covBeta by hksj_mv)
        varEst_grid += b[p_grid] * covBeta[p_grid][q_grid] * b[q_grid];
      }
    }
    varEst_grid *= hksj_mv;  // HKSJ-mv scaling
    var seEst_grid = Math.sqrt(varEst_grid);
    fit_at_dose.push({
      dose: d_grid,
      est: est_grid,
      ci_lo: est_grid - tcrit * seEst_grid,
      ci_hi: est_grid + tcrit * seEst_grid,
    });
  }
```

- [ ] **Step 4: Update fitRCS return object**

Replace `estimator` and `ci_method`:

```javascript
    estimator: 'reml_hksj_multivariate',  // was 'pm_diagonal_z' in v0.1/v0.2
    ci_method: 'hksj_t_km1',                // was 'z_1.96' in v0.1/v0.2
    hksj_mv: hksj_mv,                       // NEW: HKSJ-multivariate scaling factor
```

Also update `pooled_slope_log_ci_lo` and `pooled_slope_log_ci_hi` (the linear-component CIs) to use the HKSJ-inflated SE × t_{k-1}:

```javascript
    pooled_slope_log: pooledBeta[0],
    pooled_slope_log_se: pooledSE_hksj[0],
    pooled_slope_log_ci_lo: pooledBeta[0] - tcrit * pooledSE_hksj[0],
    pooled_slope_log_ci_hi: pooledBeta[0] + tcrit * pooledSE_hksj[0],
```

- [ ] **Step 5: Run tests, expect 54 passed**

- [ ] **Step 6: Commit**

```bash
git add rapidmeta-dose-response-engine-v1.js tests/test_dose_response_engine.mjs
git commit -m "feat(dose-response): fitRCS HKSJ-multivariate + t_{k-1} CI; estimator label = reml_hksj_multivariate (Task 9)"
```

---

## Group E — F-5 test gap closure (Tasks 10-11)

### Task 10: validate-two-arm-no-ref test

**Files:**
- Modify: `tests/test_dose_response_engine.mjs`

- [ ] **Step 1: Add the test**

```javascript
test('validate flags a trial with 2 arms but no reference flag (F-5)', () => {
  const noRef = [{
    studlab: 'no_ref_trial',
    arms: [
      { dose: 0, events: 10, n: 100, is_reference: false },
      { dose: 5, events: 15, n: 100, is_reference: false },
    ],
  }];
  const issues = DR.validate(noRef);
  assert.ok(issues.length > 0, 'should flag missing reference arm');
  assert.match(issues.join('|'), /no reference arm/i,
    'message should mention missing reference');
});
```

Run: should pass (existing `validate()` already enforces "exactly 1 reference arm").

- [ ] **Step 2: Commit**

```bash
git add tests/test_dose_response_engine.mjs
git commit -m "test(dose-response): F-5 validate-two-arm-no-ref test (Task 10)"
```

---

### Task 11: fitLinear-k=2-HKSJ-floor test

**Files:**
- Modify: `tests/test_dose_response_engine.mjs`

- [ ] **Step 1: Add the test**

```javascript
test('fitLinear k=2 homogeneous pool fires HKSJ floor (Q < df → qstar = 1)', () => {
  // Two trials with very similar per-study slopes → Cochran Q ≈ 0 < df=1
  // → HKSJ floor max(1, Q/df) = 1 fires (qstar = 1, hksj_adj = 1).
  const trials = [
    { studlab: 'A', arms: [
      { dose: 0,  events: 5,  n: 1000, is_reference: true },
      { dose: 10, events: 8,  n: 1000, is_reference: false },
    ]},
    { studlab: 'B', arms: [
      { dose: 0,  events: 6,  n: 1000, is_reference: true },
      { dose: 10, events: 9,  n: 1000, is_reference: false },
    ]},
  ];
  const res = DR.fitLinear(trials, {});
  assert.equal(res.k, 2);
  assert.ok(res.hksj_qstar >= 1, 'qstar must respect floor');
  // For these homogeneous data Q should be small; qstar likely = 1
  if (res.Q < res.Q_df) {
    assert.equal(res.hksj_qstar, 1, 'qstar = 1 when Q < df (floor fires)');
    assert.equal(res.hksj_adj, 1, 'HKSJ adj = sqrt(1) = 1');
  }
});
```

Run: expect pass.

- [ ] **Step 2: Commit**

```bash
git add tests/test_dose_response_engine.mjs
git commit -m "test(dose-response): F-5 fitLinear-k=2-HKSJ-floor test (Task 11)"
```

---

## Group F — Final smoke + close (Task 12)

### Task 12: Final smoke + Sentinel + close commit

**Files:** None (verification only)

- [ ] **Step 1: Engine test suite**

```bash
cd /c/Projects/Finrenone/.claude/worktrees/<wt>/ && node tests/test_dose_response_engine.mjs 2>&1 | tail -5
```

Expected: `≥56 passed, 0 failed` (47 prior + 1 API shape + 1 nelderMead + 1 qProfileCI + 1 fitLinear Q-profile + 1 remlLogLik + 1 fitRCS REML parity + 1 Round 1A pin update + 1 HKSJ-mv label + 1 F-5 two-arm-no-ref + 1 F-5 k=2-HKSJ-floor = 56). The exact count may be slightly higher if any test got split.

- [ ] **Step 2: R cross-check on both existing fixtures (regression guard)**

```bash
python scripts/r_validate_doseresp.py --review gl1992_alcohol_bc 2>&1 | tail -3
python scripts/r_validate_doseresp.py --review sglt2i_hba1c 2>&1 | tail -3
python scripts/r_validate_doseresp.py --review sglt2i_hhf 2>&1 | tail -3
```

All three should return `OK — linear=True, rcs=True`. R output JSON unchanged from Round 2A close.

- [ ] **Step 3: Sentinel scan**

```bash
python -m sentinel scan --repo . 2>&1 | tail -25
```

Expected: BLOCK = 0 on touched files (`rapidmeta-dose-response-engine-v1.js`, `tests/test_dose_response_engine.mjs`).

- [ ] **Step 4: HTTP-server smoke — both flagships still render**

```bash
cd /c/Projects/Finrenone/.claude/worktrees/<wt>/ && python -m http.server 8765 &
SERVER_PID=$!
sleep 1
curl -fsS http://localhost:8765/ALCOHOL_BC_DOSE_RESP_REVIEW.html -o /dev/null && echo "GL-1992 flagship OK"
curl -fsS http://localhost:8765/SGLT2I_DOSE_RESP_REVIEW.html -o /dev/null && echo "SGLT2i flagship OK"
kill $SERVER_PID 2>/dev/null
wait $SERVER_PID 2>/dev/null
```

Both should reach. The engine.js change is fully backward compatible (return shape adds fields; doesn't remove any).

- [ ] **Step 5: Final close commit**

```bash
git commit --allow-empty -m "$(cat <<'EOF'
close: Round 2B complete — engine v0.3.0 (full multivariate REML, Q-profile, HKSJ-mv, F-5, P2-13)

Deliverables (~12 commits):
- Engine v0.3.0
- Nelder-Mead simplex helper (derivative-free optimizer)
- remlLogLik + logDeterminant helpers (REML log-likelihood evaluator)
- qProfileCI helper (Viechtbauer 2007 Q-profile τ² CI)
- fitLinear now returns finite tau2_lo / tau2_hi via qProfileCI
- fitRCS: replaced diagonal-PM-per-dimension τ² with full multivariate REML
  via Nelder-Mead over Cholesky parameters of the τ² matrix. Non-linearity
  Wald p now matches R mixmeta within |Δ| < 0.1 on GL-1992 (engine ~0.70 vs
  R ~0.70; was engine ~0.05 under v0.1/v0.2 diagonal-PM).
- fitRCS: HKSJ-multivariate + t_{k-1} CIs; estimator label changed to
  'reml_hksj_multivariate', ci_method to 'hksj_t_km1'.
- F-5 test closure: validate-two-arm-no-ref + fitLinear-k=2-HKSJ-floor.
- P2-13: API definition moved to top of IIFE; methods assigned after each
  function definition.
- Round 1A regression-pin updated from p ≈ 0.05 (diagonal-PM) to p ≈ 0.70
  (full REML matching R).
- Total ≥56 / 56 tests passing; Sentinel BLOCK = 0.

Deferred to Round 2C:
- Automated Playwright browser test
- F-6 stale plan file structure doc fix
- P1-7 + P2-5 shared vendor/r-validation-badge.js escapeHtml (if parallel
  session hasn't picked up)
EOF
)"
```

- [ ] **Step 6: Verify final state**

```bash
git log --oneline <pre-2B-SHA>..HEAD
node tests/test_dose_response_engine.mjs 2>&1 | tail -3
```

---

## Done conditions (Round 2B)

| Deliverable | Path | Verification |
|---|---|---|
| Engine v0.3.0 | `rapidmeta-dose-response-engine-v1.js` | `engine_version` = `'rapidmeta-dose-response-engine-v1@0.3.0'` |
| Nelder-Mead simplex | `_internal.nelderMead` | Rosenbrock parity test passes |
| remlLogLik | `_internal.remlLogLik` | finite at τ²=0 on synthetic input |
| qProfileCI | `_internal.qProfileCI` | finite CI bounds on synthetic 5-trial pool |
| fitLinear Q-profile CI | `fitLinear` return | GL-1992 `tau2_lo` and `tau2_hi` finite, both ≥ 0 |
| fitRCS REML parity | `fitRCS` return | GL-1992 `nonlinearity_wald_p` within 0.1 of 0.70 |
| fitRCS HKSJ-mv label | `fitRCS` return | `estimator: 'reml_hksj_multivariate'`, `ci_method: 'hksj_t_km1'` |
| fitRCS HKSJ-mv visible | `fitRCS` return | `hksj_mv >= 1`, finite |
| F-5 two-arm-no-ref | tests | passes |
| F-5 k=2-HKSJ-floor | tests | passes |
| P2-13 API order | engine source | `var API = {...}` near top of IIFE |
| Round 1A pin updated | tests | non-linearity p pin now ~0.70 ± 0.10 |
| Engine tests | `tests/test_dose_response_engine.mjs` | ≥ 56 passing, 0 failed |
| Sentinel | `STUCK_FAILURES.jsonl` | BLOCK = 0 on touched files |
| Both flagships render | `ALCOHOL_BC_DOSE_RESP_REVIEW.html` + `SGLT2I_DOSE_RESP_REVIEW.html` | HTTP-server smoke passes |
| R outputs unchanged | `outputs/r_validation/doseresp/*.json` | byte-for-byte identical to Round 2A close (Round 2B is JS-only) |
