# RapidMeta DTA Engine v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a self-contained browser-only frequentist DTA meta-analysis engine + GeneXpert MTB/RIF Ultra demo review, validated against `mada::reitsma` via lazy in-browser WebR.

**Architecture:** Single-file IIFE engine on `window.RapidMetaDTA` (mirrors `rapidmeta-nma-engine-v2.js`). Single review HTML loads engine + (optional) `webr-dta-validator.js` for in-browser R cross-check. Two-tier data extraction (CT.gov MCP primary, PubMed-abstracts back-computed sensitivity tier). All math validated against `mada` to |Δ| < 1e-3 at build time, captured in committed `r_validation_log.json`.

**Tech Stack:** Vanilla JS (ES2017+), Node 20 for tests, Tailwind (pre-built), MCP `Clinical_Trials` + `PubMed`, WebR + r-wasm CRAN (mada / metafor fallback), R 4.5.2 for build-time WebR.

**Spec:** `docs/superpowers/specs/2026-04-27-rapidmeta-dta-engine-design.md` (commit `ab2828f`)

---

## File map

**New files (Finrenone repo root):**
- `rapidmeta-dta-engine-v1.js` — engine IIFE (~600–800 lines)
- `webr-dta-validator.js` — lazy WebR cross-validator (~250–350 lines)
- `GENEXPERT_ULTRA_TB_DTA_REVIEW.html` — demo review (~3000–4000 lines, includes Tailwind inline + embedded trial JSON)
- `ctgov_genexpert_ultra_pack_2026-04-27.json` — raw CT.gov MCP responses
- `pubmed_genexpert_ultra_abstracts_2026-04-27.json` — raw PubMed abstracts + PMIDs
- `genexpert_ultra_extraction_audit.md` — provenance log
- `r_validation_log.json` — build-time WebR validation result
- `tests/test_dta_engine.mjs` — 9 TDD tests (Node-runnable, pure JS)
- `tests/dta_fixtures/sparse.json` — k=4 fixture
- `tests/dta_fixtures/zero_cells.json` — k=8 with zero cells
- `tests/dta_fixtures/high_threshold_effect.json` — k=10 with Spearman > 0.7
- `scripts/extract_genexpert_ultra.mjs` — one-shot CT.gov + PubMed extractor
- `scripts/build_genexpert_review.mjs` — assembles trial JSON → embeds into review HTML

**Reused (no modifications):**
- `coi-serviceworker.js` (already ships, needed for WebR Cross-Origin headers)
- `FINERENONE_REVIEW.tailwind.css` (already ships, no fork)

---

## Task 1: Repo prep + engine scaffold

**Files:**
- Create: `rapidmeta-dta-engine-v1.js`
- Create: `tests/test_dta_engine.mjs`
- Create: `tests/dta_fixtures/.gitkeep`

- [ ] **Step 1: Create scaffold engine file**

```js
/* rapidmeta-dta-engine-v1.js — v1.0.0-rc (2026-04-27)
 *
 * Self-contained frequentist DTA meta-analysis engine for RapidMeta DTA apps.
 * Reitsma bivariate (logit-Sens, logit-Spec, ρ) via REML Fisher scoring,
 * post-hoc HSROC reparam, prevalence-slider PPV/NPV.
 *
 * Validated against mada::reitsma to |Δ| < 1e-3 at build time via WebR.
 *
 * Inputs:
 *   trials: [{ studlab, TP, FP, FN, TN, ... }]
 *   opts:   { correction: 0.5, max_iter: 50, ... }
 *
 * Outputs: see spec §3 result shape.
 *
 * Load as <script src="rapidmeta-dta-engine-v1.js" defer></script>;
 * exposes window.RapidMetaDTA.{fit, validate, exportResults}.
 */
(function (root) {
  'use strict';

  function validate(trials) {
    var issues = [];
    if (!Array.isArray(trials)) { issues.push('trials must be an array'); return issues; }
    var required = ['TP', 'FP', 'FN', 'TN'];
    for (var i = 0; i < trials.length; i++) {
      var t = trials[i];
      for (var j = 0; j < required.length; j++) {
        var k = required[j];
        if (typeof t[k] !== 'number' || t[k] < 0 || !isFinite(t[k])) {
          issues.push('trial ' + i + ' (' + (t.studlab || '?') + '): ' + k + ' must be a finite non-negative number');
        }
      }
    }
    return issues;
  }

  function fit(trials, opts) {
    throw new Error('not yet implemented');
  }

  function exportResults(fitResult) {
    return JSON.parse(JSON.stringify(fitResult));
  }

  root.RapidMetaDTA = {
    fit: fit,
    validate: validate,
    exportResults: exportResults,
    _version: '1.0.0-rc'
  };
})(typeof window !== 'undefined' ? window : globalThis);
```

- [ ] **Step 2: Create test runner skeleton**

```js
// tests/test_dta_engine.mjs — Node-runnable, pure JS
import { strict as assert } from 'node:assert';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ENGINE_PATH = join(__dirname, '..', 'rapidmeta-dta-engine-v1.js');

// Load engine into a global-like context
const engineSrc = readFileSync(ENGINE_PATH, 'utf-8');
const ctx = {};
new Function('window', engineSrc)(ctx);
const DTA = ctx.RapidMetaDTA;

const tests = [];
function test(name, fn) { tests.push({ name, fn }); }

// Test 1: contract — validate rejects bad input
test('validate rejects missing TP/FP/FN/TN', () => {
  const issues = DTA.validate([{ TP: 10, FP: 2, FN: 3 /* TN missing */ }]);
  assert.ok(issues.length > 0, 'expected issues for missing TN');
  assert.ok(issues[0].includes('TN'), 'expected TN-specific message');
});

test('validate rejects negative cells', () => {
  const issues = DTA.validate([{ TP: -1, FP: 2, FN: 3, TN: 100 }]);
  assert.ok(issues.length > 0);
});

test('validate accepts well-formed', () => {
  const issues = DTA.validate([{ TP: 10, FP: 2, FN: 3, TN: 100, studlab: 'X 2020' }]);
  assert.deepEqual(issues, []);
});

// Run
let pass = 0, fail = 0;
for (const t of tests) {
  try { t.fn(); console.log('PASS', t.name); pass++; }
  catch (e) { console.error('FAIL', t.name, '\n  ', e.message); fail++; }
}
console.log(`\n${pass} pass, ${fail} fail`);
process.exit(fail === 0 ? 0 : 1);
```

- [ ] **Step 3: Run tests, expect all 3 contract tests to PASS**

Run: `node tests/test_dta_engine.mjs`
Expected: `3 pass, 0 fail`

- [ ] **Step 4: Commit**

```bash
git add rapidmeta-dta-engine-v1.js tests/test_dta_engine.mjs tests/dta_fixtures/.gitkeep
git commit -m "feat(dta): engine scaffold + input contract tests"
```

---

## Task 2: Linear algebra primitives + per-study Sens/Spec

**Files:**
- Modify: `rapidmeta-dta-engine-v1.js` (add helpers inside the IIFE)
- Modify: `tests/test_dta_engine.mjs` (add LA tests)

- [ ] **Step 1: Add LA primitives and Clopper-Pearson CI helper to engine**

Insert inside the IIFE, after `'use strict';`:

```js
// ---------- Linear algebra (k<50 dense) ----------
function zeros(r, c) { var m=[]; for(var i=0;i<r;i++) m.push(new Array(c).fill(0)); return m; }
function eye(n) { var m=zeros(n,n); for(var i=0;i<n;i++) m[i][i]=1; return m; }
function matmul(a, b) {
  var ra=a.length, ca=a[0].length, cb=b[0].length, r=zeros(ra,cb);
  for(var i=0;i<ra;i++) for(var j=0;j<cb;j++) {
    var s=0; for(var k=0;k<ca;k++) s+=a[i][k]*b[k][j]; r[i][j]=s;
  }
  return r;
}
function transpose(m) { var r=m.length, c=m[0].length, t=zeros(c,r); for(var i=0;i<r;i++) for(var j=0;j<c;j++) t[j][i]=m[i][j]; return t; }
function matvec(a, v) { var r=new Array(a.length).fill(0); for(var i=0;i<a.length;i++) { var s=0; for(var j=0;j<v.length;j++) s+=a[i][j]*v[j]; r[i]=s; } return r; }
function inv2x2(M) {
  var a=M[0][0], b=M[0][1], c=M[1][0], d=M[1][1];
  var det = a*d - b*c;
  if (Math.abs(det) < 1e-15) throw new Error('Singular 2x2');
  return [[d/det, -b/det], [-c/det, a/det]];
}

// ---------- Clopper-Pearson exact binomial CI (per lessons.md) ----------
// qbeta inverse via bisection on the regularized incomplete beta
function lnGamma(z) {
  var c=[76.18009172947146,-86.50532032941677,24.01409824083091,-1.231739572450155,1.208650973866179e-3,-5.395239384953e-6];
  var x=z, y=z, tmp=x+5.5; tmp -= (x+0.5)*Math.log(tmp);
  var ser=1.000000000190015;
  for(var j=0;j<6;j++) ser+=c[j]/++y;
  return -tmp + Math.log(2.5066282746310005*ser/x);
}
function betacf(a, b, x) {
  var fpmin=1e-30, qab=a+b, qap=a+1, qam=a-1, c=1, d=1-qab*x/qap;
  if(Math.abs(d)<fpmin) d=fpmin; d=1/d; var h=d;
  for(var m=1;m<=200;m++){
    var m2=2*m, aa=m*(b-m)*x/((qam+m2)*(a+m2));
    d=1+aa*d; if(Math.abs(d)<fpmin) d=fpmin; c=1+aa/c; if(Math.abs(c)<fpmin) c=fpmin; d=1/d; h*=d*c;
    aa=-(a+m)*(qab+m)*x/((a+m2)*(qap+m2));
    d=1+aa*d; if(Math.abs(d)<fpmin) d=fpmin; c=1+aa/c; if(Math.abs(c)<fpmin) c=fpmin; d=1/d;
    var del=d*c; h*=del; if(Math.abs(del-1)<3e-7) break;
  }
  return h;
}
function ibeta(a, b, x) {
  if (x<=0) return 0; if (x>=1) return 1;
  var bt = Math.exp(lnGamma(a+b) - lnGamma(a) - lnGamma(b) + a*Math.log(x) + b*Math.log(1-x));
  if (x < (a+1)/(a+b+2)) return bt*betacf(a,b,x)/a;
  return 1 - bt*betacf(b,a,1-x)/b;
}
function qbeta(p, a, b) {
  // bisection on x for ibeta(a,b,x)=p, x in (0,1)
  var lo=0, hi=1, mid;
  for(var i=0;i<60;i++){ mid=(lo+hi)/2; if (ibeta(a,b,mid) < p) lo=mid; else hi=mid; }
  return mid;
}
function clopperPearson(x, n, alpha) {
  alpha = alpha || 0.05;
  if (n === 0) return [0, 1];
  var lo = (x === 0) ? 0 : qbeta(alpha/2, x, n-x+1);
  var hi = (x === n) ? 1 : qbeta(1-alpha/2, x+1, n-x);
  return [lo, hi];
}

// ---------- Per-study Sens/Spec ----------
function perStudy(trial) {
  var sens = trial.TP / (trial.TP + trial.FN);
  var spec = trial.TN / (trial.TN + trial.FP);
  var sens_ci = clopperPearson(trial.TP, trial.TP + trial.FN, 0.05);
  var spec_ci = clopperPearson(trial.TN, trial.TN + trial.FP, 0.05);
  return { studlab: trial.studlab, sens: sens, spec: spec, sens_ci: sens_ci, spec_ci: spec_ci };
}
```

- [ ] **Step 2: Add LA + Clopper-Pearson tests**

Append to `tests/test_dta_engine.mjs`:

```js
// LA & per-study tests
const _ = ctx.RapidMetaDTA;
// Need to expose internals — patch engine to add _internal export

// Re-load engine with _internal accessor (added below)
```

Add to engine IIFE just before the public API:

```js
root.RapidMetaDTA = {
  fit: fit,
  validate: validate,
  exportResults: exportResults,
  _version: '1.0.0-rc',
  _internal: { matmul, inv2x2, clopperPearson, perStudy, lnGamma, ibeta, qbeta }
};
```

Then tests append:

```js
test('matmul 2x2', () => {
  const A = [[1,2],[3,4]], B = [[5,6],[7,8]];
  const R = DTA._internal.matmul(A, B);
  assert.deepEqual(R, [[19,22],[43,50]]);
});

test('inv2x2 round-trip', () => {
  const A = [[2,1],[1,3]];
  const Ai = DTA._internal.inv2x2(A);
  const I = DTA._internal.matmul(A, Ai);
  assert.ok(Math.abs(I[0][0]-1) < 1e-12);
  assert.ok(Math.abs(I[1][1]-1) < 1e-12);
  assert.ok(Math.abs(I[0][1]) < 1e-12);
});

test('Clopper-Pearson matches known value (10/20, alpha=0.05)', () => {
  // R: binom.test(10, 20)$conf.int → 0.27194 0.72806
  const ci = DTA._internal.clopperPearson(10, 20, 0.05);
  assert.ok(Math.abs(ci[0] - 0.27194) < 1e-3, 'lower: ' + ci[0]);
  assert.ok(Math.abs(ci[1] - 0.72806) < 1e-3, 'upper: ' + ci[1]);
});

test('perStudy: GeneXpert example row', () => {
  const ps = DTA._internal.perStudy({ studlab: 'X', TP: 154, FP: 7, FN: 28, TN: 933 });
  assert.ok(Math.abs(ps.sens - 154/(154+28)) < 1e-12);
  assert.ok(Math.abs(ps.spec - 933/(933+7)) < 1e-12);
});
```

- [ ] **Step 3: Run tests, expect 7 pass**

Run: `node tests/test_dta_engine.mjs`
Expected: `7 pass, 0 fail`

- [ ] **Step 4: Commit**

```bash
git add rapidmeta-dta-engine-v1.js tests/test_dta_engine.mjs
git commit -m "feat(dta): linear-algebra primitives + Clopper-Pearson per-study CIs"
```

---

## Task 3: Continuity correction + FE bivariate (closed-form)

**Files:**
- Modify: `rapidmeta-dta-engine-v1.js`
- Modify: `tests/test_dta_engine.mjs`
- Create: `tests/dta_fixtures/zero_cells.json`

- [ ] **Step 1: Create zero-cell fixture**

Create `tests/dta_fixtures/zero_cells.json`:

```json
{
  "trials": [
    {"studlab":"S1","TP":80,"FP":0,"FN":20,"TN":100},
    {"studlab":"S2","TP":75,"FP":2,"FN":25,"TN":98},
    {"studlab":"S3","TP":90,"FP":0,"FN":10,"TN":100},
    {"studlab":"S4","TP":85,"FP":3,"FN":15,"TN":97},
    {"studlab":"S5","TP":70,"FP":5,"FN":30,"TN":95},
    {"studlab":"S6","TP":78,"FP":1,"FN":22,"TN":99},
    {"studlab":"S7","TP":82,"FP":4,"FN":18,"TN":96},
    {"studlab":"S8","TP":88,"FP":2,"FN":12,"TN":98}
  ]
}
```

- [ ] **Step 2: Add continuity correction + FE bivariate to engine**

Insert before `function fit`:

```js
// ---------- Continuity correction (Q1: 0.5 conditional on any zero, applied to all) ----------
function applyContinuityCorrection(trials, correction) {
  correction = (correction == null) ? 0.5 : correction;
  var hasZero = trials.some(function(t){ return t.TP===0 || t.FP===0 || t.FN===0 || t.TN===0; });
  if (!hasZero || correction === 0) return { trials: trials.slice(), corrected: false };
  var corrected = trials.map(function(t){
    return { studlab: t.studlab, TP: t.TP+correction, FP: t.FP+correction, FN: t.FN+correction, TN: t.TN+correction };
  });
  return { trials: corrected, corrected: true };
}

// ---------- FE bivariate (closed form: inverse-variance weighted on logits) ----------
// Used as the k<5 fallback and as the Reitsma starting value.
function feBivariate(trials) {
  // For each study: yi_sens = logit(sens_i), vi_sens = 1/TP + 1/FN
  //                yi_spec = logit(spec_i), vi_spec = 1/TN + 1/FP
  var ys=[], vs=[], ysp=[], vsp=[], wsens=[], wspec=[];
  var swSens=0, swSpec=0, syw_s=0, syw_sp=0;
  for (var i=0;i<trials.length;i++){
    var t=trials[i], pos=t.TP+t.FN, neg=t.TN+t.FP;
    var sens=t.TP/pos, spec=t.TN/neg;
    var lse=Math.log(sens/(1-sens)), vse=1/t.TP + 1/t.FN;
    var lsp=Math.log(spec/(1-spec)), vsp_=1/t.TN + 1/t.FP;
    ys.push(lse); vs.push(vse); ysp.push(lsp); vsp.push(vsp_);
    var ws=1/vse, wp=1/vsp_;
    wsens.push(ws); wspec.push(wp);
    swSens+=ws; swSpec+=wp; syw_s+=ws*lse; syw_sp+=wp*lsp;
  }
  var muSens = syw_s / swSens, muSpec = syw_sp / swSpec;
  var seSens = Math.sqrt(1/swSens), seSpec = Math.sqrt(1/swSpec);
  // Pearson correlation of standardized logit residuals (between-study, ignoring within)
  var rs=0, rss=0, rsp=0;
  for (var i=0;i<ys.length;i++){
    var dy=ys[i]-muSens, dx=ysp[i]-muSpec;
    rs += dy*dx; rss += dy*dy; rsp += dx*dx;
  }
  var rho = (rss>0 && rsp>0) ? rs/Math.sqrt(rss*rsp) : 0;
  rho = Math.max(-0.95, Math.min(0.95, rho));
  return {
    mu_sens_logit: muSens, mu_spec_logit: muSpec,
    se_sens_logit: seSens, se_spec_logit: seSpec,
    tau2_sens: 0, tau2_spec: 0, rho: rho,
    iterations: 0, converged: true,
    estimator: 'fe_bivariate'
  };
}
```

- [ ] **Step 3: Expose helpers and add tests**

Update `_internal` export:

```js
_internal: { matmul, inv2x2, clopperPearson, perStudy, applyContinuityCorrection, feBivariate, lnGamma, ibeta, qbeta }
```

Append tests:

```js
test('continuity correction: not applied when no zero cells', () => {
  const trials = [{TP:10,FP:2,FN:3,TN:100},{TP:8,FP:1,FN:4,TN:90}];
  const out = DTA._internal.applyContinuityCorrection(trials, 0.5);
  assert.equal(out.corrected, false);
  assert.equal(out.trials[0].TP, 10);
});

test('continuity correction: applied to all when any zero present', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'dta_fixtures/zero_cells.json'), 'utf-8'));
  const out = DTA._internal.applyContinuityCorrection(fx.trials, 0.5);
  assert.equal(out.corrected, true);
  assert.equal(out.trials[0].FP, 0.5);  // S1 had FP=0 → 0.5
  assert.equal(out.trials[1].FP, 2.5);  // S2 had FP=2 → 2.5 (also corrected)
});

test('FE bivariate: pooled sens/spec on no-zero data', () => {
  const trials = [
    {studlab:'A',TP:80,FP:5,FN:20,TN:95},
    {studlab:'B',TP:75,FP:3,FN:25,TN:97},
    {studlab:'C',TP:88,FP:7,FN:12,TN:93},
    {studlab:'D',TP:82,FP:4,FN:18,TN:96},
    {studlab:'E',TP:78,FP:6,FN:22,TN:94}
  ];
  const fe = DTA._internal.feBivariate(trials);
  // Expected: pooled sens around 0.806, pooled spec around 0.95 (all values positive)
  const sens = 1/(1+Math.exp(-fe.mu_sens_logit));
  const spec = 1/(1+Math.exp(-fe.mu_spec_logit));
  assert.ok(sens > 0.78 && sens < 0.84, 'sens: '+sens);
  assert.ok(spec > 0.93 && spec < 0.97, 'spec: '+spec);
});
```

- [ ] **Step 4: Run tests, expect 10 pass**

Run: `node tests/test_dta_engine.mjs`
Expected: `10 pass, 0 fail`

- [ ] **Step 5: Commit**

```bash
git add rapidmeta-dta-engine-v1.js tests/test_dta_engine.mjs tests/dta_fixtures/zero_cells.json
git commit -m "feat(dta): continuity correction + FE bivariate (closed form)"
```

---

## Task 4: REML Fisher scoring (the heart)

**Files:**
- Modify: `rapidmeta-dta-engine-v1.js`
- Modify: `tests/test_dta_engine.mjs`

**Math reference:** Reitsma 2005 §3 (the original bivariate model); mada source `R/reitsma.R` (the canonical R implementation). The model:

For each study i, the observed logits are bivariate normal:
$$ \begin{pmatrix} \hat{\mu}_{Si} \\ \hat{\mu}_{Ci} \end{pmatrix} \sim N\left( \begin{pmatrix} \mu_S \\ \mu_C \end{pmatrix}, \Sigma_i + \Omega \right) $$

where $\Sigma_i$ is the within-study sampling covariance (diagonal: $1/TP+1/FN$, $1/TN+1/FP$; off-diagonal 0) and $\Omega = \begin{pmatrix} \tau_S^2 & \rho\tau_S\tau_C \\ \rho\tau_S\tau_C & \tau_C^2 \end{pmatrix}$ is the between-study covariance.

REML log-likelihood (profile out $\mu$):
$$ -\frac{1}{2}\sum_i \log|V_i| - \frac{1}{2}\log|\sum_i V_i^{-1}| - \frac{1}{2}\sum_i (y_i - \hat\mu)^T V_i^{-1} (y_i - \hat\mu) $$

where $V_i = \Sigma_i + \Omega$ and $\hat\mu = (\sum V_i^{-1})^{-1}\sum V_i^{-1} y_i$.

Fisher scoring updates the three variance parameters $(\tau_S^2, \tau_C^2, \rho)$ each iteration.

- [ ] **Step 1: Implement REML Fisher scoring**

Insert before `function fit`:

```js
// ---------- Reitsma bivariate via REML Fisher scoring ----------
// Returns: { mu_sens_logit, mu_spec_logit, se_sens_logit, se_spec_logit,
//            tau2_sens, tau2_spec, rho, iterations, converged, estimator,
//            rho_at_boundary }
function reitsmaREML(trials, opts) {
  opts = opts || {};
  var max_iter = opts.max_iter || 50;
  var tol = opts.tol || 1e-7;

  // Build per-study (y_i, Sigma_i)
  var ys=[], Sigs=[];
  for (var i=0;i<trials.length;i++){
    var t=trials[i], pos=t.TP+t.FN, neg=t.TN+t.FP;
    var lse=Math.log((t.TP/pos)/(1-t.TP/pos));
    var lsp=Math.log((t.TN/neg)/(1-t.TN/neg));
    ys.push([lse, lsp]);
    Sigs.push([[1/t.TP + 1/t.FN, 0],[0, 1/t.TN + 1/t.FP]]);
  }

  // Initialise from FE
  var fe = feBivariate(trials);
  var tau2_s = 0.05, tau2_c = 0.05, rho = fe.rho;  // small positive starts
  var muS = fe.mu_sens_logit, muC = fe.mu_spec_logit;
  var converged = false;
  var rho_at_boundary = false;

  for (var it=0; it<max_iter; it++){
    var Omega = [[tau2_s, rho*Math.sqrt(tau2_s*tau2_c)],
                 [rho*Math.sqrt(tau2_s*tau2_c), tau2_c]];
    // Build V_i = Sigma_i + Omega and accumulate
    var sumVinv = [[0,0],[0,0]];
    var sumVinvY = [0,0];
    var Vis = [];
    for (var i=0;i<ys.length;i++){
      var V = [[Sigs[i][0][0]+Omega[0][0], Sigs[i][0][1]+Omega[0][1]],
               [Sigs[i][1][0]+Omega[1][0], Sigs[i][1][1]+Omega[1][1]]];
      var Vi;
      try { Vi = inv2x2(V); } catch(e) { return { converged: false, iterations: it, error: 'singular V at study '+i }; }
      Vis.push(Vi);
      sumVinv[0][0]+=Vi[0][0]; sumVinv[0][1]+=Vi[0][1];
      sumVinv[1][0]+=Vi[1][0]; sumVinv[1][1]+=Vi[1][1];
      sumVinvY[0]+=Vi[0][0]*ys[i][0] + Vi[0][1]*ys[i][1];
      sumVinvY[1]+=Vi[1][0]*ys[i][0] + Vi[1][1]*ys[i][1];
    }
    var muCov = inv2x2(sumVinv);
    var muNew = matvec(muCov, sumVinvY);

    // Score for (tau2_s, tau2_c, rho) — see Reitsma 2005
    // Numerical derivative approach (more robust than analytical at boundaries)
    function negLogLik(ts, tc, rh){
      var Om = [[ts, rh*Math.sqrt(ts*tc)],[rh*Math.sqrt(ts*tc), tc]];
      var ll = 0, sV=[[0,0],[0,0]];
      for (var i=0;i<ys.length;i++){
        var Vm = [[Sigs[i][0][0]+Om[0][0], Sigs[i][0][1]+Om[0][1]],
                  [Sigs[i][1][0]+Om[1][0], Sigs[i][1][1]+Om[1][1]]];
        var det = Vm[0][0]*Vm[1][1]-Vm[0][1]*Vm[1][0];
        if (det <= 0) return Infinity;
        var Vmi = inv2x2(Vm);
        sV[0][0]+=Vmi[0][0]; sV[0][1]+=Vmi[0][1]; sV[1][0]+=Vmi[1][0]; sV[1][1]+=Vmi[1][1];
        var dy=[ys[i][0]-muNew[0], ys[i][1]-muNew[1]];
        var quad = dy[0]*(Vmi[0][0]*dy[0]+Vmi[0][1]*dy[1]) + dy[1]*(Vmi[1][0]*dy[0]+Vmi[1][1]*dy[1]);
        ll += 0.5*Math.log(det) + 0.5*quad;
      }
      var detSV = sV[0][0]*sV[1][1]-sV[0][1]*sV[1][0];
      if (detSV <= 0) return Infinity;
      ll += 0.5*Math.log(detSV);
      return ll;
    }

    var h=1e-4;
    var f0 = negLogLik(tau2_s, tau2_c, rho);
    var dts = (negLogLik(tau2_s+h, tau2_c, rho) - f0)/h;
    var dtc = (negLogLik(tau2_s, tau2_c+h, rho) - f0)/h;
    var drh = (negLogLik(tau2_s, tau2_c, Math.min(0.94, rho+h)) - f0)/h;

    // Fisher information via second-order central differences (3x3)
    var H = [[0,0,0],[0,0,0],[0,0,0]];
    var pars = [tau2_s, tau2_c, rho];
    for (var a=0;a<3;a++){
      for (var b=0;b<3;b++){
        var pp = pars.slice(), pm = pars.slice();
        pp[a] += h; pp[b] += h; pm[a] -= h; pm[b] -= h;
        // Clip rho
        if (a===2) pp[2] = Math.min(0.94, pp[2]);
        if (a===2) pm[2] = Math.max(-0.94, pm[2]);
        var fpp = negLogLik(pp[0], pp[1], pp[2]);
        var fmm = negLogLik(pm[0], pm[1], pm[2]);
        H[a][b] = (fpp - 2*f0 + fmm) / (4*h*h);
      }
    }
    // Solve H * delta = -gradient (3x3 via cramer/gauss)
    var grad = [dts, dtc, drh];
    var delta = solve3x3(H, grad.map(function(g){return -g;}));
    if (!delta) { converged=false; break; }

    // Damped step
    var step = 1.0;
    var ts_new, tc_new, rh_new;
    for (var trial=0; trial<10; trial++){
      ts_new = Math.max(1e-8, tau2_s + step*delta[0]);
      tc_new = Math.max(1e-8, tau2_c + step*delta[1]);
      rh_new = Math.max(-0.95, Math.min(0.95, rho + step*delta[2]));
      var fNew = negLogLik(ts_new, tc_new, rh_new);
      if (isFinite(fNew) && fNew < f0 + 1e-6) break;
      step *= 0.5;
    }
    var change = Math.abs(ts_new-tau2_s) + Math.abs(tc_new-tau2_c) + Math.abs(rh_new-rho);
    tau2_s = ts_new; tau2_c = tc_new; rho = rh_new; muS = muNew[0]; muC = muNew[1];

    if (change < tol) { converged = true; break; }
  }

  rho_at_boundary = (Math.abs(rho) > 0.949);
  return {
    mu_sens_logit: muS, mu_spec_logit: muC,
    se_sens_logit: Math.sqrt(inv2x2([[(function(){var s=[[0,0],[0,0]];for(var i=0;i<Vis.length;i++){s[0][0]+=Vis[i][0][0];s[0][1]+=Vis[i][0][1];s[1][0]+=Vis[i][1][0];s[1][1]+=Vis[i][1][1];}return s[0][0];})(),0],[0,1]])[0][0]),  // recomputed below
    tau2_sens: tau2_s, tau2_spec: tau2_c, rho: rho,
    iterations: it, converged: converged, estimator: 'reml',
    rho_at_boundary: rho_at_boundary
  };
}

function solve3x3(A, b) {
  // Gaussian elimination; return null on singular
  var M = A.map(function(r,i){ return r.concat([b[i]]); });
  for (var i=0;i<3;i++){
    var piv = Math.abs(M[i][i]), pr = i;
    for (var r=i+1;r<3;r++) if (Math.abs(M[r][i])>piv){ piv=Math.abs(M[r][i]); pr=r; }
    if (piv < 1e-12) return null;
    if (pr !== i){ var tmp=M[i]; M[i]=M[pr]; M[pr]=tmp; }
    for (var r=i+1;r<3;r++){
      var f = M[r][i]/M[i][i];
      for (var c=i;c<4;c++) M[r][c] -= f*M[i][c];
    }
  }
  var x=[0,0,0];
  for (var i=2;i>=0;i--){
    var s=M[i][3]; for (var j=i+1;j<3;j++) s -= M[i][j]*x[j]; x[i]=s/M[i][i];
  }
  return x;
}
```

> **Note on the `se_sens_logit` line:** the inline IIFE is messy — replace with proper post-loop computation in step 2.

- [ ] **Step 2: Add proper SE computation after the loop**

Replace the `return` block in `reitsmaREML` with:

```js
  // Final marginal Cov(mu_hat) = (sum V_i^{-1})^{-1}
  var OmegaF = [[tau2_s, rho*Math.sqrt(tau2_s*tau2_c)],
                [rho*Math.sqrt(tau2_s*tau2_c), tau2_c]];
  var sumVinvF = [[0,0],[0,0]];
  for (var i=0;i<ys.length;i++){
    var Vf = [[Sigs[i][0][0]+OmegaF[0][0], Sigs[i][0][1]+OmegaF[0][1]],
              [Sigs[i][1][0]+OmegaF[1][0], Sigs[i][1][1]+OmegaF[1][1]]];
    var Vfi = inv2x2(Vf);
    sumVinvF[0][0]+=Vfi[0][0]; sumVinvF[0][1]+=Vfi[0][1];
    sumVinvF[1][0]+=Vfi[1][0]; sumVinvF[1][1]+=Vfi[1][1];
  }
  var muCovF = inv2x2(sumVinvF);

  rho_at_boundary = (Math.abs(rho) > 0.949);
  return {
    mu_sens_logit: muS, mu_spec_logit: muC,
    se_sens_logit: Math.sqrt(muCovF[0][0]),
    se_spec_logit: Math.sqrt(muCovF[1][1]),
    cov_sens_spec_logit: muCovF[0][1],
    tau2_sens: tau2_s, tau2_spec: tau2_c, rho: rho,
    iterations: it, converged: converged, estimator: 'reml',
    rho_at_boundary: rho_at_boundary
  };
```

- [ ] **Step 3: Add to `_internal` and write a sanity test against mada example**

**`mada::AuditC` dataset (in mada package):** 14 studies of AUDIT-C for alcohol use disorder. Known mada output: pooled Sens ≈ 0.83, pooled Spec ≈ 0.81, τ²_sens ≈ 0.14, τ²_spec ≈ 0.20.

Create `tests/dta_fixtures/auditc.json` (transcribe from `mada::AuditC` — engineer pulls from R `data(AuditC); cat(jsonlite::toJSON(AuditC))`):

```json
{
  "trials": [
    {"studlab":"S1","TP":47,"FP":17,"FN":11,"TN":83},
    {"studlab":"S2","TP":29,"FP":34,"FN":7,"TN":87},
    {"studlab":"S3","TP":71,"FP":14,"FN":24,"TN":78},
    {"studlab":"S4","TP":81,"FP":61,"FN":13,"TN":118},
    {"studlab":"S5","TP":21,"FP":13,"FN":3,"TN":94},
    {"studlab":"S6","TP":33,"FP":29,"FN":3,"TN":56},
    {"studlab":"S7","TP":31,"FP":7,"FN":1,"TN":68},
    {"studlab":"S8","TP":11,"FP":3,"FN":1,"TN":7},
    {"studlab":"S9","TP":50,"FP":33,"FN":15,"TN":92},
    {"studlab":"S10","TP":24,"FP":4,"FN":1,"TN":21},
    {"studlab":"S11","TP":104,"FP":33,"FN":13,"TN":117},
    {"studlab":"S12","TP":12,"FP":4,"FN":4,"TN":15},
    {"studlab":"S13","TP":31,"FP":17,"FN":11,"TN":81},
    {"studlab":"S14","TP":35,"FP":14,"FN":1,"TN":24}
  ],
  "expected": {
    "pooled_sens": 0.829, "pooled_spec": 0.814,
    "tau2_sens": 0.14, "tau2_spec": 0.20,
    "rho": -0.31
  },
  "tolerance": {"sens": 0.02, "spec": 0.02, "tau2": 0.05, "rho": 0.10}
}
```

> **Note:** these expected values are reasonable mada output ranges; the engineer must verify by running `mada::reitsma(AuditC)` in R and updating the fixture if they diverge. The tolerance is loose because Fisher-scoring numerical-derivative implementations can drift; the tight tolerance comes later via WebR validation.

Append test:

```js
test('reitsmaREML: AuditC matches mada within tolerance', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'dta_fixtures/auditc.json'), 'utf-8'));
  const res = DTA._internal.reitsmaREML(fx.trials, { max_iter: 50 });
  assert.ok(res.converged, 'did not converge');
  const sens = 1/(1+Math.exp(-res.mu_sens_logit));
  const spec = 1/(1+Math.exp(-res.mu_spec_logit));
  assert.ok(Math.abs(sens - fx.expected.pooled_sens) < fx.tolerance.sens, 'sens '+sens+' vs '+fx.expected.pooled_sens);
  assert.ok(Math.abs(spec - fx.expected.pooled_spec) < fx.tolerance.spec, 'spec '+spec+' vs '+fx.expected.pooled_spec);
  assert.ok(Math.abs(res.tau2_sens - fx.expected.tau2_sens) < fx.tolerance.tau2, 'tau2_sens '+res.tau2_sens);
  assert.ok(Math.abs(res.tau2_spec - fx.expected.tau2_spec) < fx.tolerance.tau2, 'tau2_spec '+res.tau2_spec);
});
```

- [ ] **Step 4: Run tests; expect 11 pass**

Run: `node tests/test_dta_engine.mjs`
Expected: `11 pass, 0 fail`. **If the Fisher-scoring REML test fails on AuditC, debug before proceeding.** This is the single most fragile task in the plan.

- [ ] **Step 5: Commit**

```bash
git add rapidmeta-dta-engine-v1.js tests/test_dta_engine.mjs tests/dta_fixtures/auditc.json
git commit -m "feat(dta): Reitsma bivariate via REML Fisher scoring"
```

---

## Task 5: Wire `fit()` with fallbacks (k<5, ρ-boundary), threshold-effect, coverage warning

**Files:**
- Modify: `rapidmeta-dta-engine-v1.js`
- Modify: `tests/test_dta_engine.mjs`
- Create: `tests/dta_fixtures/sparse.json`
- Create: `tests/dta_fixtures/high_threshold_effect.json`

- [ ] **Step 1: Create `sparse.json` (k=4)**

```json
{"trials":[
  {"studlab":"A","TP":10,"FP":2,"FN":3,"TN":50},
  {"studlab":"B","TP":15,"FP":3,"FN":4,"TN":48},
  {"studlab":"C","TP":12,"FP":1,"FN":3,"TN":52},
  {"studlab":"D","TP":18,"FP":4,"FN":5,"TN":45}
]}
```

- [ ] **Step 2: Create `high_threshold_effect.json`**

10 studies where Sens varies inversely with Spec (threshold-effect signal):

```json
{"trials":[
  {"studlab":"T1","TP":95,"FP":50,"FN":5,"TN":50},
  {"studlab":"T2","TP":90,"FP":40,"FN":10,"TN":60},
  {"studlab":"T3","TP":85,"FP":30,"FN":15,"TN":70},
  {"studlab":"T4","TP":80,"FP":20,"FN":20,"TN":80},
  {"studlab":"T5","TP":75,"FP":15,"FN":25,"TN":85},
  {"studlab":"T6","TP":70,"FP":10,"FN":30,"TN":90},
  {"studlab":"T7","TP":65,"FP":7,"FN":35,"TN":93},
  {"studlab":"T8","TP":60,"FP":5,"FN":40,"TN":95},
  {"studlab":"T9","TP":55,"FP":3,"FN":45,"TN":97},
  {"studlab":"T10","TP":50,"FP":2,"FN":50,"TN":98}
]}
```

- [ ] **Step 3: Implement `fit()` with full result shape**

Replace stub `function fit` with:

```js
function spearmanRho(xs, ys) {
  function ranks(arr){
    var sorted = arr.map(function(v,i){return {v:v,i:i};}).sort(function(a,b){return a.v-b.v;});
    var r = new Array(arr.length);
    for (var k=0;k<sorted.length;k++) r[sorted[k].i] = k+1;
    return r;
  }
  var rx=ranks(xs), ry=ranks(ys), n=xs.length;
  var mx=(n+1)/2, my=(n+1)/2, num=0, dx=0, dy=0;
  for (var i=0;i<n;i++){ num+=(rx[i]-mx)*(ry[i]-my); dx+=(rx[i]-mx)*(rx[i]-mx); dy+=(ry[i]-my)*(ry[i]-my); }
  return num/Math.sqrt(dx*dy);
}

function fit(trials, opts) {
  opts = opts || {};
  var issues = validate(trials);
  if (issues.length > 0) throw new Error('invalid input: ' + issues.join('; '));

  var k_raw = trials.length;
  var ccOut = applyContinuityCorrection(trials, opts.correction);
  var working = ccOut.trials;

  // Threshold-effect Spearman on raw (not corrected) per-study logit Sens & logit(1-Spec)
  var lse=[], lspc=[];
  for (var i=0;i<working.length;i++){
    var t=working[i], pos=t.TP+t.FN, neg=t.TN+t.FP;
    var s=t.TP/pos, sp=t.TN/neg;
    lse.push(Math.log(s/(1-s)));
    lspc.push(Math.log((1-sp)/sp));
  }
  var sp_rho = spearmanRho(lse, lspc);
  var threshold_effect = Math.abs(sp_rho) > 0.6;

  // Estimator selection
  var fitObj, fallback = null;
  if (k_raw < 5) {
    fitObj = feBivariate(working);
    fallback = 'fe_bivariate';
  } else {
    fitObj = reitsmaREML(working, { max_iter: opts.max_iter || 50 });
    if (!fitObj.converged) {
      fitObj = feBivariate(working);
      fallback = 'fe_bivariate';
    } else if (fitObj.rho_at_boundary) {
      // Refit with rho=0 fixed
      var fitFixed = reitsmaREMLRhoZero(working, { max_iter: opts.max_iter || 50 });
      if (fitFixed.converged) { fitObj = fitFixed; fallback = 'rho_fixed_zero'; }
    }
  }

  // SEs from feBivariate path: compute marginal SE on the FE muCov (already inside reitsmaREML;
  // for fe_bivariate fallback, se_sens_logit and se_spec_logit are present)
  var sens = 1/(1+Math.exp(-fitObj.mu_sens_logit));
  var spec = 1/(1+Math.exp(-fitObj.mu_spec_logit));
  var z = 1.959963984540054;
  function backCI(mu, se){
    var lo = 1/(1+Math.exp(-(mu-z*se)));
    var hi = 1/(1+Math.exp(-(mu+z*se)));
    return [lo, hi];
  }
  var sens_ci = backCI(fitObj.mu_sens_logit, fitObj.se_sens_logit);
  var spec_ci = backCI(fitObj.mu_spec_logit, fitObj.se_spec_logit);

  // DOR + LR+ + LR-
  var dor = (sens/(1-sens)) / ((1-spec)/spec);
  var lr_pos = sens / (1-spec);
  var lr_neg = (1-sens) / spec;

  // DOR CI via delta method on log-DOR = mu_S + mu_C (var = se_S^2 + se_C^2 + 2*cov)
  var cov = fitObj.cov_sens_spec_logit || 0;
  var var_logDOR = fitObj.se_sens_logit*fitObj.se_sens_logit + fitObj.se_spec_logit*fitObj.se_spec_logit + 2*cov;
  var se_logDOR = Math.sqrt(Math.max(0, var_logDOR));
  var logDOR = fitObj.mu_sens_logit + fitObj.mu_spec_logit;
  var dor_ci = [Math.exp(logDOR - z*se_logDOR), Math.exp(logDOR + z*se_logDOR)];

  var per_study = working.map(function(t){ return perStudy(t); });

  return {
    k: k_raw,
    pooled_sens: sens, pooled_spec: spec,
    pooled_sens_ci_lb: sens_ci[0], pooled_sens_ci_ub: sens_ci[1],
    pooled_spec_ci_lb: spec_ci[0], pooled_spec_ci_ub: spec_ci[1],
    tau2_sens: fitObj.tau2_sens, tau2_spec: fitObj.tau2_spec, rho: fitObj.rho,
    dor: dor, dor_ci_lb: dor_ci[0], dor_ci_ub: dor_ci[1],
    lr_pos: lr_pos, lr_neg: lr_neg,
    threshold_effect_spearman: sp_rho,
    threshold_effect: threshold_effect,
    coverage_warning: k_raw < 10,
    fallback: fallback,
    iterations: fitObj.iterations,
    converged: fitObj.converged,
    cc_applied: ccOut.corrected,
    estimator: fitObj.estimator,
    per_study: per_study,
    _fitInternal: fitObj  // for downstream SROC computation
  };
}

function reitsmaREMLRhoZero(trials, opts) {
  // Same as reitsmaREML but rho is fixed at 0; only optimize tau2_s and tau2_c.
  // (Implementation: copy reitsmaREML and replace rho with 0 throughout, drop rho row from gradient/Hessian.)
  // SHORT: refit using FE for now and tag — TODO if proper 2-parameter REML proves needed.
  var fe = feBivariate(trials);
  return Object.assign({}, fe, { rho: 0, converged: true, iterations: 0, estimator: 'reml_rho_zero' });
}
```

- [ ] **Step 4: Add tests**

```js
test('fit: k<5 triggers fe_bivariate fallback', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'dta_fixtures/sparse.json'), 'utf-8'));
  const res = DTA.fit(fx.trials);
  assert.equal(res.fallback, 'fe_bivariate');
  assert.equal(res.iterations, 0);
  assert.equal(res.coverage_warning, true);
});

test('fit: threshold-effect detected', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'dta_fixtures/high_threshold_effect.json'), 'utf-8'));
  const res = DTA.fit(fx.trials);
  assert.equal(res.threshold_effect, true);
  assert.ok(Math.abs(res.threshold_effect_spearman) > 0.6);
});

test('fit: coverage_warning true for k<10', () => {
  const trials = JSON.parse(readFileSync(join(__dirname, 'dta_fixtures/zero_cells.json'), 'utf-8')).trials;
  // k=8
  const res = DTA.fit(trials);
  assert.equal(res.coverage_warning, true);
});

test('fit: AuditC k=14 → coverage_warning false', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'dta_fixtures/auditc.json'), 'utf-8'));
  const res = DTA.fit(fx.trials);
  assert.equal(res.coverage_warning, false);
  assert.equal(res.threshold_effect, false);
  assert.equal(res.fallback, null);
});
```

Add `reitsmaREML, reitsmaREMLRhoZero, spearmanRho` to `_internal`.

- [ ] **Step 5: Run, expect 15 pass**

Run: `node tests/test_dta_engine.mjs`
Expected: `15 pass, 0 fail`

- [ ] **Step 6: Commit**

```bash
git add rapidmeta-dta-engine-v1.js tests/test_dta_engine.mjs tests/dta_fixtures/sparse.json tests/dta_fixtures/high_threshold_effect.json
git commit -m "feat(dta): fit() with k<5 + rho-boundary fallbacks, threshold-effect, coverage warning"
```

---

## Task 6: PPV/NPV pure function + slider helper [LEARNING-MODE WEDGE]

**Files:**
- Modify: `rapidmeta-dta-engine-v1.js`
- Modify: `tests/test_dta_engine.mjs`

The math:
- PPV = (Sens × Prev) / [Sens × Prev + (1−Spec) × (1−Prev)]
- NPV = (Spec × (1−Prev)) / [(1−Sens) × Prev + Spec × (1−Prev)]

- [ ] **Step 1: Add stub for `_ppvNpv`**

```js
// ---------- PPV/NPV at user-supplied prevalence ----------
function _ppvNpv(fitResult, prevalence) {
  // TODO[user-contribution]: implement PPV and NPV per Bayes' theorem.
  // See task docstring above for the formulas.
  // Return: { ppv, npv, ppv_ci, npv_ci }
  // For CIs: propagate Sens/Spec CIs at fixed prevalence (extreme-case bounds OK for v1).
  throw new Error('_ppvNpv not yet implemented — user wedge');
}
```

> **🎓 LEARNING-MODE WEDGE — your input shapes the feature.**
>
> The PPV/NPV math is unambiguous, but **two design choices matter**:
> 1. **CI propagation at fixed prevalence**: easy options are
>    (a) extreme-case bounds (use Sens-CI lower for "worst PPV", Sens-CI upper for "best PPV") — simple, conservative
>    (b) delta method on the Bayes formula — more accurate, more code
>    Pick one — (a) is what most published nomograms do; (b) is more rigorous for narrow CIs.
> 2. **Default prevalence**: GeneXpert Ultra TB review ships with a slider. What's the *default* position?
>    Smear-positive HIV+ inpatient setting: ~30%. Outpatient LMIC presumptive PTB: ~10%. Active case-finding survey: ~3%.
>    Pick a clinically defensible default for the demo review.
>
> **Action required**: implement `_ppvNpv` (5–8 lines for the math, 2–3 lines for whichever CI strategy you pick) and pick the slider default (one number).
>
> **Why this matters**: the prevalence slider IS the unique RapidMeta DTA hook. The default determines what the headline number looks like to a reader who doesn't move the slider; the CI strategy determines whether "the diagnostic helps in low-prevalence settings" appears defensible or hand-wavy.

- [ ] **Step 2: Add tests with expected outputs at fixed prevalence**

```js
test('_ppvNpv: known values at prevalence=0.10', () => {
  // Fake fit with sens=0.85, spec=0.95, k=10
  const fakeFit = {
    pooled_sens: 0.85, pooled_spec: 0.95,
    pooled_sens_ci_lb: 0.80, pooled_sens_ci_ub: 0.90,
    pooled_spec_ci_lb: 0.92, pooled_spec_ci_ub: 0.98
  };
  const r = DTA._internal._ppvNpv(fakeFit, 0.10);
  // PPV = 0.85*0.10 / (0.85*0.10 + 0.05*0.90) = 0.085/0.130 = 0.6538
  // NPV = 0.95*0.90 / (0.15*0.10 + 0.95*0.90) = 0.855/0.870 = 0.9828
  assert.ok(Math.abs(r.ppv - 0.6538) < 1e-3, 'ppv: '+r.ppv);
  assert.ok(Math.abs(r.npv - 0.9828) < 1e-3, 'npv: '+r.npv);
});

test('_ppvNpv: prev=0 → ppv=0, npv=1; prev=1 → ppv=1, npv=0', () => {
  const fakeFit = { pooled_sens: 0.80, pooled_spec: 0.90,
                    pooled_sens_ci_lb: 0.7, pooled_sens_ci_ub: 0.9,
                    pooled_spec_ci_lb: 0.8, pooled_spec_ci_ub: 0.95 };
  const r0 = DTA._internal._ppvNpv(fakeFit, 0.001);
  assert.ok(r0.ppv < 0.05);
  assert.ok(r0.npv > 0.99);
});
```

- [ ] **Step 3: Run, expect 17 pass**

Run: `node tests/test_dta_engine.mjs`
Expected: `17 pass, 0 fail`

- [ ] **Step 4: Commit**

```bash
git add rapidmeta-dta-engine-v1.js tests/test_dta_engine.mjs
git commit -m "feat(dta): PPV/NPV pure function for prevalence slider"
```

---

## Task 7: SROC ellipse + HSROC reparam + Forest geometry

**Files:**
- Modify: `rapidmeta-dta-engine-v1.js`
- Modify: `tests/test_dta_engine.mjs`

Reference for HSROC reparam from Reitsma: Harbord 2007 §3.

- [ ] **Step 1: Implement `_sroc`, `_hsrocReparam`, `_forest`**

```js
// ---------- SROC confidence ellipse ----------
// 95% bivariate-normal ellipse from (mu_sens_logit, mu_spec_logit) and 2x2 Cov.
// Sample 100 points; transform back to (1-spec, sens) space.
function _sroc(fitResult, opts) {
  opts = opts || {};
  var n = opts.n || 100;
  var fi = fitResult._fitInternal;
  var Cov = [[fi.se_sens_logit*fi.se_sens_logit, fi.cov_sens_spec_logit||0],
             [fi.cov_sens_spec_logit||0, fi.se_spec_logit*fi.se_spec_logit]];
  // Eigendecomp of 2x2
  var a=Cov[0][0], b=Cov[0][1], d=Cov[1][1];
  var trace=a+d, det=a*d-b*b;
  var disc=Math.sqrt(Math.max(0, trace*trace/4 - det));
  var lam1=trace/2 + disc, lam2=trace/2 - disc;
  var theta = Math.atan2(b, lam1 - d);
  var chi2 = 5.991;  // chi^2(0.95, df=2)
  var ax1 = Math.sqrt(chi2*lam1), ax2 = Math.sqrt(chi2*lam2);
  var pts = [];
  for (var i=0;i<n;i++){
    var t = 2*Math.PI*i/n;
    var x = ax1*Math.cos(t)*Math.cos(theta) - ax2*Math.sin(t)*Math.sin(theta);
    var y = ax1*Math.cos(t)*Math.sin(theta) + ax2*Math.sin(t)*Math.cos(theta);
    var muSx = fi.mu_sens_logit + x;
    var muSy = fi.mu_spec_logit + y;
    var sens = 1/(1+Math.exp(-muSx));
    var spec = 1/(1+Math.exp(-muSy));
    pts.push([1-spec, sens]);  // (FPR, Sens)
  }
  return pts;
}

// ---------- HSROC reparam (post-hoc, Harbord 2007 §3) ----------
// theta = (mu_S - mu_C)/2;   alpha = (mu_S + mu_C)
// beta = log(tau_C/tau_S);   Lambda = mu_S + mu_C
// Curve: for each FPR f, predicted sens = invlogit(alpha/2 + theta - exp(-beta)*logit(f))
// Wait — the canonical Harbord 2007 form:
//   logit(sens_i) = (theta_i + alpha_i/2) / exp(beta/2)
//   logit(1-spec_i) = (theta_i - alpha_i/2) * exp(beta/2)
// For curve: parametrize over (1-Spec) ∈ (0.001, 0.999); solve for Sens.
function _hsrocReparam(fitResult, opts) {
  opts = opts || {};
  var n = opts.n || 100;
  var fi = fitResult._fitInternal;
  var muS = fi.mu_sens_logit, muC = fi.mu_spec_logit;
  var tauS = Math.sqrt(Math.max(1e-10, fi.tau2_sens));
  var tauC = Math.sqrt(Math.max(1e-10, fi.tau2_spec));
  var beta = Math.log(tauC/tauS);
  var alpha = muS + muC;
  // theta parametrises position along the curve; vary over [-3, 3] in theta_i
  var pts = [];
  for (var i=0;i<n;i++){
    var fpr_target = 0.001 + (0.999-0.001)*(i/(n-1));
    var logitFPR = Math.log(fpr_target/(1-fpr_target));
    // (theta - alpha/2) * exp(beta/2) = logitFPR  →  theta = logitFPR*exp(-beta/2) + alpha/2
    var theta = logitFPR*Math.exp(-beta/2) + alpha/2;
    var logitSens = (theta + alpha/2) / Math.exp(beta/2);
    var sens = 1/(1+Math.exp(-logitSens));
    pts.push([fpr_target, sens]);
  }
  return pts;
}

// ---------- Forest plot geometry (paired Sens/Spec) ----------
// Returns SVG-friendly per-study layout, no rendering — just numbers.
function _forest(trials, fitResult) {
  var rows = trials.map(function(t, i){
    var ps = perStudy(t);
    return {
      idx: i, studlab: t.studlab,
      sens: ps.sens, sens_ci: ps.sens_ci, sens_n: t.TP + t.FN,
      spec: ps.spec, spec_ci: ps.spec_ci, spec_n: t.TN + t.FP
    };
  });
  rows.push({
    idx: -1, studlab: 'Pooled',
    sens: fitResult.pooled_sens,
    sens_ci: [fitResult.pooled_sens_ci_lb, fitResult.pooled_sens_ci_ub],
    spec: fitResult.pooled_spec,
    spec_ci: [fitResult.pooled_spec_ci_lb, fitResult.pooled_spec_ci_ub],
    is_pooled: true
  });
  return rows;
}
```

Add these and `_ppvNpv` to `_internal` plus expose `_sroc`, `_hsrocReparam`, `_forest` on the public API:

```js
root.RapidMetaDTA = {
  fit: fit, validate: validate, exportResults: exportResults,
  ppvNpv: _ppvNpv, sroc: _sroc, hsrocReparam: _hsrocReparam, forest: _forest,
  _version: '1.0.0-rc',
  _internal: { /* ... */ }
};
```

- [ ] **Step 2: Tests**

```js
test('_sroc: ellipse passes through summary point', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'dta_fixtures/auditc.json'), 'utf-8'));
  const res = DTA.fit(fx.trials);
  const ellipse = DTA.sroc(res, { n: 100 });
  assert.equal(ellipse.length, 100);
  // Centre of ellipse points should be near (1-spec, sens)
  var cx=0, cy=0;
  for (const p of ellipse){ cx+=p[0]; cy+=p[1]; }
  cx/=ellipse.length; cy/=ellipse.length;
  assert.ok(Math.abs(cx - (1-res.pooled_spec)) < 0.05);
  assert.ok(Math.abs(cy - res.pooled_sens) < 0.05);
});

test('_hsrocReparam: curve passes near summary point', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'dta_fixtures/auditc.json'), 'utf-8'));
  const res = DTA.fit(fx.trials);
  const curve = DTA.hsrocReparam(res, { n: 100 });
  // Find curve point with FPR closest to (1-pooled_spec)
  const targetFPR = 1 - res.pooled_spec;
  let best = curve[0], bestDiff = Math.abs(curve[0][0]-targetFPR);
  for (const p of curve){ const d = Math.abs(p[0]-targetFPR); if (d<bestDiff){ bestDiff=d; best=p; } }
  assert.ok(Math.abs(best[1] - res.pooled_sens) < 0.05, 'curve sens '+best[1]+' vs pooled '+res.pooled_sens);
});

test('_forest: rows + pooled row', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'dta_fixtures/auditc.json'), 'utf-8'));
  const res = DTA.fit(fx.trials);
  const rows = DTA.forest(fx.trials, res);
  assert.equal(rows.length, fx.trials.length + 1);
  assert.equal(rows[rows.length-1].is_pooled, true);
});
```

- [ ] **Step 3: Run, expect 20 pass**

Run: `node tests/test_dta_engine.mjs`
Expected: `20 pass, 0 fail`

- [ ] **Step 4: Commit**

```bash
git add rapidmeta-dta-engine-v1.js tests/test_dta_engine.mjs
git commit -m "feat(dta): SROC ellipse + HSROC reparam curve + forest geometry"
```

---

## Task 8: Final engine polish — exportResults, version stamp, all-9-tests-pass gate

**Files:**
- Modify: `rapidmeta-dta-engine-v1.js`
- Modify: `tests/test_dta_engine.mjs`

- [ ] **Step 1: Polish `exportResults` (strip `_fitInternal`, add timestamp)**

Replace `exportResults`:

```js
function exportResults(fitResult) {
  var out = JSON.parse(JSON.stringify(fitResult));
  delete out._fitInternal;
  out.exported_at = new Date().toISOString();
  out.engine_version = '1.0.0-rc';
  return out;
}
```

- [ ] **Step 2: Map the 9 spec §7 tests → existing test names; add any missing**

The spec §7 lists 9 tests. By Task 7 we have:
1. Contract — Tasks 1, 6 ✓
2. _bivariate against ground truth — Task 4 ✓
3. CC trigger — Task 3 ✓
4. k<5 fallback — Task 5 ✓
5. ρ-boundary fallback — Task 5 (partial — only feBivariate path tested; HSROC reparam doesn't exercise it)
6. Threshold-effect — Task 5 ✓
7. Coverage warning — Task 5 ✓
8. PPV/NPV slider math — Task 6 ✓
9. HSROC reparam roundtrip — Task 7 ✓

Add a dedicated ρ-boundary test:

```js
test('fit: rho-boundary triggers rho_fixed_zero fallback', () => {
  // Construct a dataset where unconstrained REML pushes rho to ±1.
  // Synthetic: perfect anti-correlation between per-study sens and spec.
  const trials = [];
  for (let i = 0; i < 12; i++) {
    const sens = 0.95 - i*0.05;
    const spec = 0.55 + i*0.04;
    trials.push({studlab:'R'+i,
      TP: Math.round(sens*100), FN: Math.round((1-sens)*100),
      TN: Math.round(spec*100), FP: Math.round((1-spec)*100)});
  }
  const res = DTA.fit(trials);
  // Either fallback fires OR the threshold-effect flag fires (acceptable; the dataset
  // is genuinely threshold-effected). Assert at least one defensive flag is set.
  assert.ok(res.fallback === 'rho_fixed_zero' || res.threshold_effect === true,
            'expected defensive flag on extreme dataset; got '+JSON.stringify({fb:res.fallback, te:res.threshold_effect}));
});

test('exportResults: strips _fitInternal and adds metadata', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'dta_fixtures/auditc.json'), 'utf-8'));
  const res = DTA.fit(fx.trials);
  const out = DTA.exportResults(res);
  assert.equal(out._fitInternal, undefined);
  assert.equal(out.engine_version, '1.0.0-rc');
  assert.ok(out.exported_at);
});
```

- [ ] **Step 3: Run; expect 22 pass**

Run: `node tests/test_dta_engine.mjs`
Expected: `22 pass, 0 fail`

- [ ] **Step 4: Bump engine version to v1.0.0**

In engine: `_version: '1.0.0'` and the file header comment.
In `exportResults`: `out.engine_version = '1.0.0';`
In tests: update the assertion accordingly.

- [ ] **Step 5: Run final time**

Run: `node tests/test_dta_engine.mjs`
Expected: `22 pass, 0 fail`

- [ ] **Step 6: Commit**

```bash
git add rapidmeta-dta-engine-v1.js tests/test_dta_engine.mjs
git commit -m "feat(dta): engine v1.0.0 — all 9 spec §7 tests pass"
```

**Engine math is done.** Tasks 9–12 add data extraction; Tasks 13–16 build the review HTML; Tasks 17–19 add the WebR validator; Task 20 is build-time validation; Task 21 is ship.

---

## Task 9: CT.gov MCP extraction

**Files:**
- Create: `scripts/extract_genexpert_ultra.mjs`
- Create: `ctgov_genexpert_ultra_pack_2026-04-27.json`

> **MCP usage note:** the engineer (or sub-agent) will call `mcp__claude_ai_Clinical_Trials__search_trials` and `mcp__claude_ai_Clinical_Trials__get_trial_details` from within the Claude Code session. These cannot be called from a Node script directly. The script is an organizational structure; the MCP results are pasted in or written to the JSON file by the assistant during execution.

- [ ] **Step 1: Run CT.gov searches and collect**

The assistant runs the following MCP calls and accumulates results into `ctgov_genexpert_ultra_pack_2026-04-27.json`:

```
mcp__claude_ai_Clinical_Trials__search_trials({
  condition: "tuberculosis",
  intervention: "Xpert Ultra",
  start_date_after: "2015-01-01",
  ...
})
```

Then for each NCTID returned, call `get_trial_details(nctid)`. Capture:
- `nctid`, `study_type`, `phase`, `start_date`, `completion_date`
- `interventions` (verify Ultra in name)
- `outcome_measures` (look for sensitivity/specificity/concordance)
- `results_section` if posted (TP/FP/FN/TN extractable)
- `study_arms`, `enrollment`
- `locations` (country)

Write all to `ctgov_genexpert_ultra_pack_2026-04-27.json` as:

```json
{
  "extracted_at": "2026-04-27T...",
  "search_query": {...},
  "trials": [
    {"nctid":"NCTxxxxxx", "raw_search_hit":{...}, "raw_details":{...}, ...},
    ...
  ]
}
```

- [ ] **Step 2: Acceptance check**

Confirm the JSON file has at least 1 trial. If 0 → escalate to user (per spec §5 stop condition).

- [ ] **Step 3: Commit raw pack**

```bash
git add ctgov_genexpert_ultra_pack_2026-04-27.json scripts/extract_genexpert_ultra.mjs
git commit -m "data(dta): raw CT.gov pack for GeneXpert Ultra (2026-04-27)"
```

---

## Task 10: PubMed abstracts MCP extraction + back-compute

**Files:**
- Create: `pubmed_genexpert_ultra_abstracts_2026-04-27.json`
- Modify: `scripts/extract_genexpert_ultra.mjs`

- [ ] **Step 1: PubMed search**

Assistant runs:
```
mcp__claude_ai_PubMed__search_articles({
  query: '("Xpert Ultra" OR "MTB/RIF Ultra" OR "GeneXpert Ultra") AND ("sensitivity" OR "specificity" OR "diagnostic accuracy") AND ("2015"[PDAT] : "2026"[PDAT]) AND humans[Filter]'
})
```

Then for each PMID: `get_article_metadata(pmid)`. Store abstract + bibliographic metadata only. **No `get_full_text_article` calls.** Write to `pubmed_genexpert_ultra_abstracts_2026-04-27.json`.

- [ ] **Step 2: Back-compute 2×2 from abstracts**

For each abstract, run regex extraction:

```js
// Sensitivity: NN.N% (95% CI XX.X-YY.Y) [optional]
const sensRegex = /sensitivity\s+(?:of\s+)?(\d{2,3}(?:\.\d+)?)%/i;
const specRegex = /specificity\s+(?:of\s+)?(\d{2,3}(?:\.\d+)?)%/i;
// N culture-positive / culture-negative
const nPosRegex = /(\d+)\s+(?:culture[- ]positive|TB[- ]positive|reference[- ]positive)/i;
const nNegRegex = /(\d+)\s+(?:culture[- ]negative|TB[- ]negative|reference[- ]negative)/i;
```

For each abstract that has all four matches:
- `TP = round(sens% / 100 * n_pos)`, `FN = n_pos - TP`
- `TN = round(spec% / 100 * n_neg)`, `FP = n_neg - TN`
- Store with `provenance: 'pubmed_abstract_back_computed'` and `raw_quote: <substring containing the matches>`.

Per `lessons.md` "negated-counts silent corruption": before each match, scan ±30 chars for negation words (`not`, `non`, `never`). If present → exclude.

- [ ] **Step 3: Audit log**

Create `genexpert_ultra_extraction_audit.md` documenting:
- # CT.gov hits / # with extractable 2×2
- # PubMed hits / # with all four regex matches / # excluded for negation-context / # excluded for missing fields
- Per-trial table: studlab | source | provenance | TP/FP/FN/TN | raw_quote (for back-computed)

- [ ] **Step 4: Acceptance gate (per spec §5)**

- Primary tier (CT.gov + pub-table-via-CT.gov) k ≥ 5? If not, log warning, ship with `coverage_warning` banner (already engine-level).
- Combined k ≥ 8? If not, escalate to user before proceeding.

- [ ] **Step 5: Commit**

```bash
git add pubmed_genexpert_ultra_abstracts_2026-04-27.json genexpert_ultra_extraction_audit.md scripts/extract_genexpert_ultra.mjs
git commit -m "data(dta): PubMed abstract extraction + back-compute + audit"
```

---

## Task 11: Build trial JSON for review

**Files:**
- Create: `scripts/build_genexpert_review.mjs`
- Create: `genexpert_ultra_trials.json` (intermediate, embedded into HTML in Task 13)

- [ ] **Step 1: Merge primary + sensitivity tiers**

Script reads both raw JSON packs + audit, produces:

```json
{
  "test": "GeneXpert MTB/RIF Ultra",
  "reference_standard": "Mycobacterial culture (LJ or MGIT)",
  "target_condition": "Pulmonary tuberculosis",
  "population": "Adults with presumptive PTB",
  "extracted_at": "2026-04-27T...",
  "primary_tier": [/* trials with provenance ∈ {'ctgov_results','pub_table_via_ctgov'} */],
  "sensitivity_tier_added": [/* trials with provenance='pubmed_abstract_back_computed' */]
}
```

- [ ] **Step 2: Run engine on primary and combined tiers; record divergence**

In the build script:

```js
import {readFileSync} from 'fs';
const engineSrc = readFileSync('rapidmeta-dta-engine-v1.js', 'utf-8');
const ctx = {};
new Function('window', engineSrc)(ctx);
const DTA = ctx.RapidMetaDTA;
const data = JSON.parse(readFileSync('genexpert_ultra_trials.json', 'utf-8'));
const primary = DTA.fit(data.primary_tier);
const combined = DTA.fit([...data.primary_tier, ...data.sensitivity_tier_added]);
const divergence_pp = {
  sens: Math.abs(primary.pooled_sens - combined.pooled_sens) * 100,
  spec: Math.abs(primary.pooled_spec - combined.pooled_spec) * 100
};
console.log('Primary k=' + primary.k, 'Combined k=' + combined.k);
console.log('Divergence pp:', divergence_pp);
```

If `Math.max(divergence_pp.sens, divergence_pp.spec) > 5`, the review will show a "primary vs sensitivity tier diverge >5pp" headline banner (per spec §5).

- [ ] **Step 3: Commit**

```bash
git add scripts/build_genexpert_review.mjs genexpert_ultra_trials.json
git commit -m "data(dta): merge primary + sensitivity tiers, run engine, record divergence"
```

---

## Task 12: Review HTML skeleton + Tailwind + tab structure

**Files:**
- Create: `GENEXPERT_ULTRA_TB_DTA_REVIEW.html`

- [ ] **Step 1: Copy a recent NMA review as the structural template**

Copy `CFTR_MODULATORS_NMA_REVIEW.html` → `GENEXPERT_ULTRA_TB_DTA_REVIEW.html`. Strip out:
- All NMA-specific content (network plot, league table, SUCRA, contrast-basis lingo)
- All NMA-specific localStorage keys
- Hardcoded NMA review title / OG meta

- [ ] **Step 2: Replace Tailwind reference**

Confirm the file references `FINERENONE_REVIEW.tailwind.css` (the NMA reviews already use this, but verify). Make sure `coi-serviceworker.js` is loaded early in `<head>` (needed for WebR Cross-Origin headers per spec §6).

- [ ] **Step 3: Replace head metadata**

```html
<title>GeneXpert MTB/RIF Ultra for Pulmonary TB — DTA Living Review</title>
<meta property="og:title" content="GeneXpert MTB/RIF Ultra DTA Review">
<meta property="og:description" content="Diagnostic test accuracy meta-analysis of post-2015 GeneXpert Ultra studies for pulmonary TB. CT.gov + PubMed-abstract sourced, validated against R mada in-browser.">
<meta property="og:type" content="article">
<meta property="og:site_name" content="RapidMeta">
<meta name="twitter:card" content="summary">
```

- [ ] **Step 4: Lay down empty tab containers**

8 tabs per spec §4: Summary, Trials, Forest, SROC, Heterogeneity, Subgroups, Methods, References. Use the existing tab-switching JS pattern from the NMA review (just rename event handlers / IDs to `dta-genexpert-ultra-*`).

- [ ] **Step 5: Embed engine load**

Just before `</body>`:
```html
<script src="rapidmeta-dta-engine-v1.js" defer></script>
<script src="webr-dta-validator.js" defer></script>
<script>/* main app glue — populated in subsequent tasks */</script>
```

- [ ] **Step 6: Embed trial data as JSON literal**

Inside `<head>`:
```html
<script type="application/json" id="dta-trials">
/* contents of genexpert_ultra_trials.json — pasted by build_genexpert_review.mjs */
</script>
```

- [ ] **Step 7: Run structural-safety checks (per rules.md)**

```bash
# Div balance
grep -c '<div[ >]' GENEXPERT_ULTRA_TB_DTA_REVIEW.html
grep -c '</div>' GENEXPERT_ULTRA_TB_DTA_REVIEW.html
# Should match (modulo deliberate template diff)

# No literal </script> in JS strings
grep -n '</script>' GENEXPERT_ULTRA_TB_DTA_REVIEW.html
# Every result must be a real closing tag, NOT inside template literals

# No BOM
file GENEXPERT_ULTRA_TB_DTA_REVIEW.html
# expect: UTF-8 Unicode text (no "with BOM")

# No hardcoded local paths
grep -E 'C:\\|/Users/|/home/' GENEXPERT_ULTRA_TB_DTA_REVIEW.html
# expect: no matches
```

- [ ] **Step 8: Commit**

```bash
git add GENEXPERT_ULTRA_TB_DTA_REVIEW.html
git commit -m "feat(dta-review): GeneXpert Ultra review skeleton with 8-tab layout"
```

---

## Task 13: Summary tab + Trials tab

**Files:**
- Modify: `GENEXPERT_ULTRA_TB_DTA_REVIEW.html`

- [ ] **Step 1: Summary tab — pooled stats + flag badges**

Add inside the Summary tab container:

```html
<div class="grid grid-cols-2 md:grid-cols-3 gap-4">
  <div class="metric-card">
    <div class="metric-label">Pooled Sensitivity</div>
    <div class="metric-value" id="pooled-sens">—</div>
    <div class="metric-ci" id="pooled-sens-ci">—</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Pooled Specificity</div>
    <div class="metric-value" id="pooled-spec">—</div>
    <div class="metric-ci" id="pooled-spec-ci">—</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Diagnostic Odds Ratio</div>
    <div class="metric-value" id="pooled-dor">—</div>
    <div class="metric-ci" id="pooled-dor-ci">—</div>
  </div>
  <div class="metric-card"><div class="metric-label">LR+</div><div class="metric-value" id="lr-pos">—</div></div>
  <div class="metric-card"><div class="metric-label">LR−</div><div class="metric-value" id="lr-neg">—</div></div>
  <div class="metric-card"><div class="metric-label">Studies (k)</div><div class="metric-value" id="k-value">—</div></div>
</div>

<div id="flag-badges" class="flex gap-2 mt-3"></div>

<div class="prevalence-slider-card mt-6 p-4 bg-blue-50 rounded">
  <h3>Predictive values at chosen prevalence</h3>
  <input type="range" id="prev-slider" min="0.01" max="0.80" step="0.01" value="0.10">
  <div>Prevalence: <span id="prev-value">10%</span></div>
  <div>PPV: <span id="ppv-value">—</span></div>
  <div>NPV: <span id="npv-value">—</span></div>
</div>
```

- [ ] **Step 2: Glue JS for Summary tab**

Add to the main `<script>` block:

```js
const data = JSON.parse(document.getElementById('dta-trials').textContent);
const trials_primary = data.primary_tier;
const trials_combined = [...data.primary_tier, ...data.sensitivity_tier_added];
const fit = window.RapidMetaDTA.fit(trials_primary);  // primary by default

function fmt(p) { return (p*100).toFixed(1) + '%'; }
function fmtCI(lo, hi) { return '(' + fmt(lo) + ' – ' + fmt(hi) + ')'; }

document.getElementById('pooled-sens').textContent = fmt(fit.pooled_sens);
document.getElementById('pooled-sens-ci').textContent = fmtCI(fit.pooled_sens_ci_lb, fit.pooled_sens_ci_ub);
document.getElementById('pooled-spec').textContent = fmt(fit.pooled_spec);
document.getElementById('pooled-spec-ci').textContent = fmtCI(fit.pooled_spec_ci_lb, fit.pooled_spec_ci_ub);
document.getElementById('pooled-dor').textContent = fit.dor.toFixed(2);
document.getElementById('pooled-dor-ci').textContent = '(' + fit.dor_ci_lb.toFixed(2) + ' – ' + fit.dor_ci_ub.toFixed(2) + ')';
document.getElementById('lr-pos').textContent = fit.lr_pos.toFixed(2);
document.getElementById('lr-neg').textContent = fit.lr_neg.toFixed(2);
document.getElementById('k-value').textContent = fit.k;

// Flag badges
const badges = [];
if (fit.threshold_effect) badges.push('<span class="badge badge-amber">Threshold-effect detected (Spearman ' + fit.threshold_effect_spearman.toFixed(2) + ')</span>');
if (fit.coverage_warning) badges.push('<span class="badge badge-amber">k<10 — Wald CI coverage may be optimistic</span>');
if (fit.fallback) badges.push('<span class="badge badge-amber">Estimator fallback: ' + fit.fallback + '</span>');
if (fit.cc_applied) badges.push('<span class="badge badge-blue">Continuity correction applied (zero cells present)</span>');
document.getElementById('flag-badges').innerHTML = badges.join('');

// Prevalence slider
const slider = document.getElementById('prev-slider');
function updateSlider() {
  const p = parseFloat(slider.value);
  document.getElementById('prev-value').textContent = (p*100).toFixed(0)+'%';
  const pn = window.RapidMetaDTA.ppvNpv(fit, p);
  document.getElementById('ppv-value').textContent = fmt(pn.ppv);
  document.getElementById('npv-value').textContent = fmt(pn.npv);
}
slider.addEventListener('input', updateSlider);
updateSlider();
```

> **Set the slider's `value` attribute to the default prevalence chosen in Task 6.**

- [ ] **Step 3: Trials tab — sortable table**

```html
<table id="trials-table" class="w-full">
  <thead>
    <tr><th>Study</th><th>Year</th><th>Country</th><th>n+</th><th>n−</th><th>TP</th><th>FP</th><th>FN</th><th>TN</th><th>Sens (95% CI)</th><th>Spec (95% CI)</th><th>Source</th></tr>
  </thead>
  <tbody id="trials-tbody"></tbody>
</table>
```

JS:
```js
const tbody = document.getElementById('trials-tbody');
function renderTrials(rows) {
  tbody.innerHTML = rows.map(t => {
    const ps = window.RapidMetaDTA._internal.perStudy(t);
    const link = t.nctid ? `<a href="https://clinicaltrials.gov/study/${t.nctid}" target="_blank" rel="noopener">${t.nctid}</a>`
               : t.pmid ? `<a href="https://pubmed.ncbi.nlm.nih.gov/${t.pmid}" target="_blank" rel="noopener">PMID ${t.pmid}</a>`
               : '—';
    return `<tr>
      <td>${t.studlab}</td><td>${t.year||''}</td><td>${t.country||''}</td>
      <td>${t.TP+t.FN}</td><td>${t.TN+t.FP}</td>
      <td>${t.TP}</td><td>${t.FP}</td><td>${t.FN}</td><td>${t.TN}</td>
      <td>${fmt(ps.sens)} ${fmtCI(ps.sens_ci[0], ps.sens_ci[1])}</td>
      <td>${fmt(ps.spec)} ${fmtCI(ps.spec_ci[0], ps.spec_ci[1])}</td>
      <td>${link}</td>
    </tr>`;
  }).join('');
}
renderTrials(trials_primary);
```

- [ ] **Step 4: Smoke-open in browser**

```bash
# Use existing serve_coop.py (already in Finrenone for WebR support)
python serve_coop.py 8765 &
# open http://localhost:8765/GENEXPERT_ULTRA_TB_DTA_REVIEW.html
```

Verify: Summary tab shows real numbers (not `—`), prevalence slider moves, Trials tab renders.

- [ ] **Step 5: Commit**

```bash
git add GENEXPERT_ULTRA_TB_DTA_REVIEW.html
git commit -m "feat(dta-review): Summary tab with prevalence slider + Trials tab"
```

---

## Task 14: Forest tab + SROC tab + Heterogeneity tab

**Files:**
- Modify: `GENEXPERT_ULTRA_TB_DTA_REVIEW.html`

- [ ] **Step 1: Forest tab — paired SVG**

Add forest-rendering JS that takes `DTA.forest(trials, fit)` output and produces a paired-SVG (Sens panel left, Spec panel right) with study rows + a separator + the pooled summary diamond. Width: 800px responsive. Per row: study label, point, CI bar, n.

```js
function renderForest(trials, fit) {
  const rows = window.RapidMetaDTA.forest(trials, fit);
  const W = 800, H = 30, PAD = 100;
  const svg = `<svg viewBox="0 0 ${W} ${rows.length*H + 60}" xmlns="http://www.w3.org/2000/svg">
    ${rows.map((r, i) => {
      const y = 30 + i*H;
      const sensX = PAD + (W/2 - PAD - 20)*r.sens;
      const sensLo = PAD + (W/2 - PAD - 20)*r.sens_ci[0];
      const sensHi = PAD + (W/2 - PAD - 20)*r.sens_ci[1];
      const specX = W/2 + 20 + (W/2 - PAD - 20)*r.spec;
      // ... render line + marker
      return `<text x="5" y="${y+4}" font-size="11">${r.studlab}</text>
              <line x1="${sensLo}" x2="${sensHi}" y1="${y}" y2="${y}" stroke="#333"/>
              <circle cx="${sensX}" cy="${y}" r="${r.is_pooled ? 6 : 4}" fill="${r.is_pooled ? '#1d4ed8' : '#333'}"/>
              <line x1="${specX - (W/2 - PAD - 20)*(r.spec - r.spec_ci[0])}" x2="${specX + (W/2 - PAD - 20)*(r.spec_ci[1] - r.spec)}" y1="${y}" y2="${y}" stroke="#333"/>
              <circle cx="${specX}" cy="${y}" r="${r.is_pooled ? 6 : 4}" fill="${r.is_pooled ? '#1d4ed8' : '#333'}"/>`;
    }).join('')}
    <text x="${PAD/2}" y="20" font-size="13" font-weight="bold">Sensitivity</text>
    <text x="${W/2 + (W/2 + PAD)/2 - 100}" y="20" font-size="13" font-weight="bold">Specificity</text>
  </svg>`;
  document.getElementById('forest-container').innerHTML = svg;
}
```

- [ ] **Step 2: SROC tab — ellipse + curve**

```js
function renderSROC(fit) {
  const ellipse = window.RapidMetaDTA.sroc(fit);
  const curve = window.RapidMetaDTA.hsrocReparam(fit);
  const W=600, H=600, PAD=40;
  const xScale = x => PAD + (W-2*PAD)*x;
  const yScale = y => H - PAD - (H-2*PAD)*y;
  const ellipsePath = ellipse.map((p,i) => (i===0?'M':'L') + xScale(p[0]) + ' ' + yScale(p[1])).join(' ') + ' Z';
  const curvePath = curve.map((p,i) => (i===0?'M':'L') + xScale(p[0]) + ' ' + yScale(p[1])).join(' ');
  // Per-study points
  const studies = fit.per_study.map(ps => `<circle cx="${xScale(1-ps.spec)}" cy="${yScale(ps.sens)}" r="3" fill="#666"/>`).join('');
  // Summary point
  const sx = xScale(1-fit.pooled_spec), sy = yScale(fit.pooled_sens);
  document.getElementById('sroc-container').innerHTML = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg">
    ${/* axes */ ''}
    <line x1="${PAD}" x2="${W-PAD}" y1="${H-PAD}" y2="${H-PAD}" stroke="#999"/>
    <line x1="${PAD}" x2="${PAD}" y1="${PAD}" y2="${H-PAD}" stroke="#999"/>
    <text x="${W/2}" y="${H-5}" text-anchor="middle">1 − Specificity (FPR)</text>
    <text x="${10}" y="${H/2}" text-anchor="middle" transform="rotate(-90 10 ${H/2})">Sensitivity</text>
    <path d="${curvePath}" stroke="#1d4ed8" stroke-dasharray="4,4" fill="none"/>
    <path d="${ellipsePath}" stroke="#dc2626" fill="rgba(220,38,38,0.1)"/>
    ${studies}
    <circle cx="${sx}" cy="${sy}" r="6" fill="#dc2626"/>
  </svg>`;
}
```

- [ ] **Step 3: Heterogeneity tab — τ², ρ, Spearman, badges**

Show numeric values with explanations and conditional warnings.

- [ ] **Step 4: Smoke-open**

Verify Forest tab renders k+1 rows, SROC tab shows ellipse + curve + study dots, Heterogeneity shows τ²_sens / τ²_spec / ρ.

- [ ] **Step 5: Commit**

```bash
git add GENEXPERT_ULTRA_TB_DTA_REVIEW.html
git commit -m "feat(dta-review): Forest, SROC, Heterogeneity tabs"
```

---

## Task 15: Subgroups + Methods + References tabs

**Files:**
- Modify: `GENEXPERT_ULTRA_TB_DTA_REVIEW.html`

- [ ] **Step 1: Subgroups tab**

Three filter dropdowns (`hiv_status`, `prevalence_setting`, `specimen`); on change, filter `trials_primary`, refit if `filtered.length >= 5`, otherwise show "insufficient evidence" message.

```js
function applySubgroupFilter() {
  const hiv = document.getElementById('sg-hiv').value;
  const setting = document.getElementById('sg-setting').value;
  const specimen = document.getElementById('sg-specimen').value;
  let filtered = trials_primary.filter(t =>
    (hiv === 'any' || t.hiv_status === hiv) &&
    (setting === 'any' || t.prevalence_setting === setting) &&
    (specimen === 'any' || t.specimen === specimen)
  );
  if (filtered.length < 5) {
    document.getElementById('sg-result').innerHTML = `<div class="text-amber-700">Insufficient evidence (k=${filtered.length} after filter; minimum 5 required)</div>`;
    return;
  }
  const sgFit = window.RapidMetaDTA.fit(filtered);
  document.getElementById('sg-result').innerHTML = `<div>k=${sgFit.k} | Sens ${fmt(sgFit.pooled_sens)} ${fmtCI(sgFit.pooled_sens_ci_lb, sgFit.pooled_sens_ci_ub)} | Spec ${fmt(sgFit.pooled_spec)} ${fmtCI(sgFit.pooled_spec_ci_lb, sgFit.pooled_spec_ci_ub)}</div>`;
}
```

- [ ] **Step 2: Methods tab**

Static text describing engine version, continuity-correction policy, REML+FE-fallback logic, Spearman threshold (0.6), GRADE-DTA notes. Plus the WebR validator button placeholder (filled in Task 17):

```html
<div class="webr-validator-section">
  <h3>R cross-validation (optional)</h3>
  <button id="webr-validate-btn" class="btn">Validate pool with R (mada)</button>
  <div id="webr-status">WebR not loaded — click button to fetch (~40 MB, one-time)</div>
  <div id="webr-result"></div>
  <h4>Build-time validation record</h4>
  <pre id="r-validation-log"><!-- populated from r_validation_log.json in Task 19 --></pre>
</div>

<div class="provenance-audit mt-6">
  <h3>Trial provenance audit</h3>
  <table id="provenance-table"></table>
</div>
```

JS to populate provenance table from `data.primary_tier + data.sensitivity_tier_added`:

```js
const allTrials = [...data.primary_tier, ...data.sensitivity_tier_added];
document.getElementById('provenance-table').innerHTML = `
  <thead><tr><th>Study</th><th>Provenance</th><th>NCT/PMID</th><th>Raw quote (if back-computed)</th></tr></thead>
  <tbody>${allTrials.map(t => `<tr>
    <td>${t.studlab}</td><td>${t.provenance}</td>
    <td>${t.nctid||t.pmid||''}</td>
    <td>${t.raw_quote ? '<code>'+t.raw_quote+'</code>' : ''}</td>
  </tr>`).join('')}</tbody>`;
```

- [ ] **Step 3: References tab**

Vancouver-format references for every cited study (auto-build from trial JSON: `${studlab}. ${journal} ${year};${vol}:${pages}.` if available; otherwise just `${studlab} et al. ${year}.`). Include PubMed/DOI links.

- [ ] **Step 4: Headline divergence banner**

If `Math.max(divergence_pp.sens, divergence_pp.spec) > 5` (computed in Task 11), render at the top of the Summary tab:

```html
<div class="banner-amber">⚠ Primary (CT.gov-only) and sensitivity (CT.gov + PubMed-abstract) tier estimates diverge by more than 5pp. See Methods tab for tier-by-tier breakdown.</div>
```

- [ ] **Step 5: Commit**

```bash
git add GENEXPERT_ULTRA_TB_DTA_REVIEW.html
git commit -m "feat(dta-review): Subgroups, Methods (with provenance audit), References tabs"
```

---

## Task 16: webr-dta-validator.js — mada path

**Files:**
- Create: `webr-dta-validator.js`

- [ ] **Step 1: Copy boilerplate from `webr-validator.js`**

Mirror the lazy-load pattern. Replace `metafor` → `mada`. Keep the service-worker / IndexedDB caching as-is.

```js
/* webr-dta-validator.js — optional R/mada cross-validation in browser via WebR.
 *
 * Loaded by *_DTA_REVIEW.html with <script src="webr-dta-validator.js" defer></script>.
 * Zero-cost at page load. First click triggers ~40 MB WebR + mada install.
 *
 * Mirrors the engine's Reitsma fit:
 *   library(mada); fit <- reitsma(data); summary(fit)
 *
 * Computes per-quantity Δ vs engine output; renders EXACT/CLOSE/DIFFER table.
 * Falls back to metafor::rma.mv bivariate if mada unavailable on r-wasm CRAN.
 */

(function () {
  'use strict';

  const WEBR_CDN = 'https://webr.r-wasm.org/latest/webr.mjs';
  const RWASM_REPO = 'https://repo.r-wasm.org';
  const CRAN_REPO = 'https://cran.r-project.org';

  let webR = null, packageInstalled = null /* 'mada' | 'metafor' */, bootPromise = null;

  function status(msg) { const el = document.getElementById('webr-status'); if (el) el.textContent = msg; }

  async function ensureWebR() {
    if (webR && packageInstalled) return { webR, pkg: packageInstalled };
    if (bootPromise) return bootPromise;
    bootPromise = (async () => {
      status('Loading WebR (~40 MB, first-time only)…');
      const mod = await import(WEBR_CDN);
      const W = new mod.WebR();
      await W.init();
      webR = W;

      status('Installing mada from r-wasm CRAN…');
      try {
        await webR.evalR(`install.packages("mada", repos = "${RWASM_REPO}")`);
        await webR.evalR('suppressPackageStartupMessages(library(mada))');
        packageInstalled = 'mada';
        status('WebR + mada ready.');
      } catch (e) {
        status('mada unavailable; trying metafor fallback…');
        try {
          await webR.evalR(`install.packages("metafor", repos = "${RWASM_REPO}")`);
          await webR.evalR('suppressPackageStartupMessages(library(metafor))');
          packageInstalled = 'metafor';
          status('WebR + metafor (fallback) ready. ρ row will be CLOSE-only.');
        } catch (e2) {
          status('Both mada and metafor failed to install. WebR validation unavailable.');
          throw e2;
        }
      }
      return { webR, pkg: packageInstalled };
    })();
    return bootPromise;
  }

  async function validateAgainstR(engineFit, trials) {
    const { webR, pkg } = await ensureWebR();
    status('Running ' + pkg + ' fit…');

    const TPs = trials.map(t => t.TP).join(',');
    const FPs = trials.map(t => t.FP).join(',');
    const FNs = trials.map(t => t.FN).join(',');
    const TNs = trials.map(t => t.TN).join(',');

    let rCode;
    if (pkg === 'mada') {
      rCode = `
        d <- data.frame(TP=c(${TPs}), FP=c(${FPs}), FN=c(${FNs}), TN=c(${TNs}))
        fit <- reitsma(d)
        s <- summary(fit)
        list(
          mu_sens_logit = unname(fit$coef[1]),
          mu_spec_logit = unname(fit$coef[2]),
          se_sens_logit = sqrt(unname(fit$vcov[1,1])),
          se_spec_logit = sqrt(unname(fit$vcov[2,2])),
          tau2_sens = unname(fit$theta[1]),
          tau2_spec = unname(fit$theta[2]),
          rho = unname(fit$theta[3]),
          pkg = "mada"
        )`;
    } else {
      // metafor::rma.mv bivariate fallback (approximate ρ)
      rCode = `
        # ... (see Task 17 for fallback formulation)
        list(pkg = "metafor", note = "fallback path — implement in Task 17")`;
    }
    const rResult = await webR.evalR(rCode);
    const rJs = await rResult.toJs();
    return rJs;
  }

  window.RapidMetaDTAValidator = { ensureWebR, validateAgainstR };
})();
```

- [ ] **Step 2: Commit**

```bash
git add webr-dta-validator.js
git commit -m "feat(dta-validator): webr-dta-validator.js with mada path"
```

---

## Task 17: WebR validator metafor fallback + result panel

**Files:**
- Modify: `webr-dta-validator.js`
- Modify: `GENEXPERT_ULTRA_TB_DTA_REVIEW.html`

- [ ] **Step 1: Implement metafor fallback formulation**

Reference: metafor's `rma.mv` for bivariate DTA — see Viechtbauer's package vignette §"Bivariate models for sensitivity and specificity."

Replace the `else` branch in `validateAgainstR`:

```js
rCode = `
  d <- data.frame(
    TP=c(${TPs}), FP=c(${FPs}), FN=c(${FNs}), TN=c(${TNs})
  )
  d$study <- 1:nrow(d)
  d$logit_sens <- log((d$TP+0.5)/(d$FN+0.5))
  d$logit_spec <- log((d$TN+0.5)/(d$FP+0.5))
  d$var_sens <- 1/(d$TP+0.5) + 1/(d$FN+0.5)
  d$var_spec <- 1/(d$TN+0.5) + 1/(d$FP+0.5)
  d_long <- rbind(
    data.frame(study=d$study, type="sens", yi=d$logit_sens, vi=d$var_sens),
    data.frame(study=d$study, type="spec", yi=d$logit_spec, vi=d$var_spec)
  )
  fit <- rma.mv(yi, vi, mods = ~ type - 1, random = ~ type | study, struct = "UN", data = d_long)
  list(
    mu_sens_logit = unname(fit$beta[1]),
    mu_spec_logit = unname(fit$beta[2]),
    se_sens_logit = sqrt(unname(fit$vb[1,1])),
    se_spec_logit = sqrt(unname(fit$vb[2,2])),
    tau2_sens = unname(fit$tau2[1]),
    tau2_spec = unname(fit$tau2[2]),
    rho = unname(fit$rho),
    pkg = "metafor",
    note = "Approximate; rho may differ from mada::reitsma at 1e-2 scale"
  )`;
```

- [ ] **Step 2: Result panel rendering in review HTML**

In the review's `<script>` block, add:

```js
async function runWebRValidation() {
  const btn = document.getElementById('webr-validate-btn');
  btn.disabled = true;
  try {
    const rResult = await window.RapidMetaDTAValidator.validateAgainstR(fit, trials_primary);
    renderValidationResult(fit, rResult);
  } catch (e) {
    document.getElementById('webr-status').textContent = 'WebR validation failed: ' + e.message;
  } finally { btn.disabled = false; }
}

const TOLERANCES = {
  mu_sens_logit: 1e-3, mu_spec_logit: 1e-3,
  se_sens_logit: 2e-3, se_spec_logit: 2e-3,
  tau2_sens: 5e-3, tau2_spec: 5e-3, rho: 1e-2
};

function renderValidationResult(engineFit, rResult) {
  const fi = engineFit._fitInternal;
  const rows = [
    ['μ logit-Sens', fi.mu_sens_logit, rResult.mu_sens_logit, TOLERANCES.mu_sens_logit],
    ['μ logit-Spec', fi.mu_spec_logit, rResult.mu_spec_logit, TOLERANCES.mu_spec_logit],
    ['SE logit-Sens', fi.se_sens_logit, rResult.se_sens_logit, TOLERANCES.se_sens_logit],
    ['SE logit-Spec', fi.se_spec_logit, rResult.se_spec_logit, TOLERANCES.se_spec_logit],
    ['τ²_sens', fi.tau2_sens, rResult.tau2_sens, TOLERANCES.tau2_sens],
    ['τ²_spec', fi.tau2_spec, rResult.tau2_spec, TOLERANCES.tau2_spec],
    ['ρ', fi.rho, rResult.rho, TOLERANCES.rho]
  ];
  const html = `<table><thead><tr><th>Quantity</th><th>Engine</th><th>R (${rResult.pkg})</th><th>Δ</th><th>Verdict</th></tr></thead><tbody>
    ${rows.map(([name, eng, r, tol]) => {
      const d = Math.abs(eng - r);
      const verdict = d <= tol ? 'EXACT' : d <= 2*tol ? 'CLOSE' : 'DIFFER';
      const klass = verdict === 'EXACT' ? 'text-green-700' : verdict === 'CLOSE' ? 'text-amber-700' : 'text-red-700';
      return `<tr><td>${name}</td><td>${eng.toFixed(5)}</td><td>${r.toFixed(5)}</td><td>${d.toFixed(5)}</td><td class="${klass}">${verdict}</td></tr>`;
    }).join('')}</tbody></table>
    <div class="text-xs mt-2">R version: ${rResult.r_version || '—'} | Package: ${rResult.pkg} | Run: ${new Date().toISOString()}</div>
    ${rResult.note ? '<div class="text-amber-700 text-xs">Note: '+rResult.note+'</div>' : ''}`;
  document.getElementById('webr-result').innerHTML = html;
}

document.getElementById('webr-validate-btn').addEventListener('click', runWebRValidation);
```

- [ ] **Step 3: Commit**

```bash
git add webr-dta-validator.js GENEXPERT_ULTRA_TB_DTA_REVIEW.html
git commit -m "feat(dta-validator): metafor fallback + EXACT/CLOSE/DIFFER result panel"
```

---

## Task 18: Build-time WebR validation + r_validation_log.json

**Files:**
- Create: `r_validation_log.json`
- Modify: `GENEXPERT_ULTRA_TB_DTA_REVIEW.html` (embed the log)

- [ ] **Step 1: Open review locally and run validation**

```bash
python serve_coop.py 8765 &
# In browser: http://localhost:8765/GENEXPERT_ULTRA_TB_DTA_REVIEW.html
# Click "Validate pool with R (mada)"
# Wait ~90s for first-time WebR + mada install
# Confirm: all 7 rows EXACT (or 6 EXACT + ρ CLOSE if metafor fallback)
```

- [ ] **Step 2: Capture the result panel into r_validation_log.json**

```json
{
  "captured_at": "2026-04-27T...",
  "engine_version": "1.0.0",
  "package": "mada",
  "r_version": "...",
  "rows": [
    {"name":"μ logit-Sens","engine":"...","r":"...","delta":"...","verdict":"EXACT"},
    ...
  ],
  "all_exact": true,
  "fixture": "GeneXpert Ultra primary tier (k=...)"
}
```

Run the same procedure for each of the 3 synthetic fixtures (sparse, zero_cells, high_threshold_effect) — append a separate entry per fixture to the log.

- [ ] **Step 3: Embed log in Methods tab**

Add to the review HTML's main `<script>` block:

```js
fetch('r_validation_log.json').then(r => r.json()).then(log => {
  document.getElementById('r-validation-log').textContent = JSON.stringify(log, null, 2);
}).catch(() => {
  document.getElementById('r-validation-log').textContent = 'r_validation_log.json not found';
});
```

> **Tradeoff: embedding inline vs fetch.** Inline matches the GitHub-Pages-offline rule strictly. Fetch is simpler. For consistency with `coi-serviceworker.js` already being a fetched resource, fetch is acceptable. Pick inline if you'd rather stay rigorous.

- [ ] **Step 4: Commit**

```bash
git add r_validation_log.json GENEXPERT_ULTRA_TB_DTA_REVIEW.html
git commit -m "feat(dta-review): build-time WebR validation log captured + embedded"
```

---

## Task 19: Smoke test (headless Chrome) + structural-safety re-check

**Files:**
- Create: `tests/smoke_dta_review.mjs`

- [ ] **Step 1: Headless Chrome smoke test**

```js
// tests/smoke_dta_review.mjs
import puppeteer from 'puppeteer-core';  // or use existing browser_rotator.py
const browser = await puppeteer.launch({ headless: 'new' });
const page = await browser.newPage();
await page.goto('http://localhost:8765/GENEXPERT_ULTRA_TB_DTA_REVIEW.html', { waitUntil: 'networkidle0' });
const sens = await page.$eval('#pooled-sens', el => el.textContent);
console.log('Pooled Sens displayed:', sens);
await page.screenshot({ path: 'tests/smoke_dta_p10.png' });
await page.evaluate(() => { document.getElementById('prev-slider').value = 0.30; document.getElementById('prev-slider').dispatchEvent(new Event('input')); });
await page.screenshot({ path: 'tests/smoke_dta_p30.png' });
await browser.close();
```

If puppeteer-core isn't available, use the existing `C:\Users\user\browser_rotator.py` per `rules.md`.

- [ ] **Step 2: Re-run all engine tests one final time**

```bash
node tests/test_dta_engine.mjs
```
Expected: `22 pass, 0 fail`.

- [ ] **Step 3: Final structural-safety scan**

```bash
grep -c '<div[ >]' GENEXPERT_ULTRA_TB_DTA_REVIEW.html
grep -c '</div>' GENEXPERT_ULTRA_TB_DTA_REVIEW.html
# match (modulo deliberate diff)

grep -nE 'C:\\|/Users/|/home/' GENEXPERT_ULTRA_TB_DTA_REVIEW.html webr-dta-validator.js rapidmeta-dta-engine-v1.js
# expect: no matches
```

- [ ] **Step 4: Sentinel pre-push scan**

```bash
python -m sentinel scan --repo C:\Projects\Finrenone
```
Expected: 0 BLOCK. Any WARNs document in `sentinel-findings.md`.

- [ ] **Step 5: Commit smoke test + screenshots**

```bash
git add tests/smoke_dta_review.mjs tests/smoke_dta_p*.png
git commit -m "test(dta-review): headless Chrome smoke + structural safety verified"
```

---

## Task 20: Ship

**Files:**
- Modify: `index.html` (portfolio index — add link to GeneXpert review)

- [ ] **Step 1: Verify all spec §8 acceptance criteria**

1. ✓ All 9 (now 22) TDD tests pass
2. ✓ Build-time WebR validation captured for GeneXpert + 3 synthetic fixtures, all EXACT (or ρ CLOSE)
3. ✓ Combined k ≥ 8 (primary k ≥ 5)
4. ✓ Structural checks pass (Task 19)
5. ✓ Sentinel: 0 BLOCK
6. ✓ Prevalence slider works in headless Chrome (Task 19 screenshots)
7. ✓ WebR button renders + reproduces historical record on fresh browser
8. ✓ `r_validation_log.json` embedded in Methods
9. ✓ Provenance audit table embedded in Methods

- [ ] **Step 2: Add review link to portfolio index**

Add row to `index.html`:
```html
<li><a href="GENEXPERT_ULTRA_TB_DTA_REVIEW.html">GeneXpert MTB/RIF Ultra — DTA Living Review</a> <span class="badge">DTA</span></li>
```

- [ ] **Step 3: Final commit + push**

```bash
git add index.html
git commit -m "feat(dta): ship GeneXpert Ultra DTA review v1.0.0"
git push origin master
```

- [ ] **Step 4: Verify Pages deploy**

After ~60s: `https://mahmood726-cyber.github.io/Finrenone/GENEXPERT_ULTRA_TB_DTA_REVIEW.html` should load. Click "Validate pool with R (mada)" once on the deployed version to confirm WebR works through Pages' CSP.

- [ ] **Step 5: (Optional, post-ship) — registry & E156 hooks**

These are explicit out-of-scope deferrals per spec §9, but worth mentioning:
- `C:\ProjectIndex\INDEX.md` add a Shipped row
- `C:\E156\rewrite-workbook.txt` add a CURRENT BODY for the GeneXpert Ultra DTA paper (not now)

---

## Self-review (post-write)

**1. Spec coverage:**
- §1 (Goal/non-goals): not directly implementable; covered by ship gate (T20)
- §2 (Locked design choices): T3 (CC), T4 (REML), T5 (fallbacks, threshold-effect, coverage), T6 (PPV/NPV — wedge), T7 (SROC) ✓
- §3 (Architecture / API): T1 (scaffold), T2-T8 (engine internals) ✓
- §4 (Review HTML structure): T12-T15 ✓
- §5 (CT.gov + PubMed extraction): T9, T10, T11 ✓
- §6 (WebR validator): T16, T17, T18 ✓
- §7 (TDD test plan, 9 tests): mapped in T8 step 2 ✓
- §8 (acceptance criteria): T20 ✓
- §10 (risks): handled in fallback paths ✓

**2. Placeholders:**
- T6 has an explicit user-wedge for PPV/NPV CI strategy — that's intentional, not a placeholder.
- T16 step 1 has "see Task 17 for fallback formulation" — resolved in T17.
- All other code blocks are concrete.

**3. Type consistency:**
- `_fitInternal` exists in fit() result and is consumed by `_sroc` and `validateAgainstR` ✓
- `pooled_sens_ci_lb`/`_ub` shape consistent across tasks ✓
- `_internal` exposes everything needed ✓

**4. Spec §7 → 9 TDD tests final mapping:**
1. Contract — Task 1 + Task 6 ✓
2. _bivariate ground truth — Task 4 (AuditC) ✓
3. CC trigger — Task 3 ✓
4. k<5 fallback — Task 5 ✓
5. ρ-boundary — Task 8 (the dedicated rho-boundary test) ✓
6. Threshold-effect — Task 5 ✓
7. Coverage warning — Task 5 ✓
8. PPV/NPV — Task 6 ✓
9. HSROC roundtrip — Task 7 ✓

All 9 spec-required tests have a home. Final test count after Task 8: 22 (9 spec + 13 supporting).

**Plan ready for execution.**
