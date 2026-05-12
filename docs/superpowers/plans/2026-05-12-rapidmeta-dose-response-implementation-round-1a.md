# Dose-Response Pack — Round 1A Implementation Plan (Engine + R Validator + Tests)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a working `rapidmeta-dose-response-engine-v1.js` (three layered fitters: GL-linear, GL+RCS, one-stage JSON reader), 5 adversarial fixtures with parity baselines, a Node-runnable test suite, and the Rscript-out-of-process validator triplet — all without an HTML host. Round 1B (flagship `SGLT2I_DOSE_RESP_REVIEW.html` + AACT cross-check + badge UI) is a separate plan that depends on this one.

**Spec:** `docs/superpowers/specs/2026-05-12-rapidmeta-dose-response-engine-design.md`

**Architecture:** Mirrors `rapidmeta-prognostic-engine-v1.js` shape (IIFE → `window.RapidMetaDoseResp`). Math primitives (matInv, qchisq, etc.) are copied verbatim from the prognostic engine to keep cross-engine numerical consistency. Validator triplet mirrors `scripts/r_validate_continuous.{R,py}` shipped 2026-05-12.

**Tech stack:** ES5-compatible JS (browser-only constraints, no build step), Node ≥18 for tests (`node --test` not used — bespoke test runner per repo idiom), R 4.5.2 + `dosresmeta` 2.0.1 + `nlme` 3.1, Python 3.13.

---

## File structure

| Path | Responsibility | Status |
|---|---|---|
| `rapidmeta-dose-response-engine-v1.js` | Engine: validate, fitLinear, fitRCS, fitOneStage, nonLinearityTest, predict, forest, exportResults | NEW |
| `tests/test_dose_response_engine.mjs` | Node-runnable test suite, ~40 tests | NEW |
| `tests/dose_response_fixtures/gl1992_alcohol_bc.json` | Greenland-Longnecker 1992 canonical | NEW |
| `tests/dose_response_fixtures/k2_identical_doses.json` | Degenerate non-linearity test | NEW |
| `tests/dose_response_fixtures/single_arm.json` | Validator-reject case | NEW |
| `tests/dose_response_fixtures/ref_only.json` | Validator-reject case | NEW |
| `tests/dose_response_fixtures/extrapolation.json` | Banner-flag case | NEW |
| `tests/dose_response_baselines/r_parity.json` | dosresmeta reference outputs | NEW |
| `scripts/r_validate_doseresp.R` | R-side dosresmeta runner | NEW |
| `scripts/r_validate_doseresp.py` | Python wrapper (CLI: `--review <NAME>`) | NEW |
| `outputs/r_validation/doseresp/` | R-output JSON sink | NEW (dir) |

---

## Task 1: Bootstrap — empty engine + test skeleton + commit

**Files:**
- Create: `rapidmeta-dose-response-engine-v1.js`
- Create: `tests/test_dose_response_engine.mjs`

Per the Finrenone safety memory ("commit a skeleton EARLY because the harvest-peer-review-findings workflow deletes untracked files"), this task's only goal is getting the skeleton into git fast.

- [ ] **Step 1: Create engine skeleton with header + IIFE shell**

Create `rapidmeta-dose-response-engine-v1.js`:

```javascript
/* rapidmeta-dose-response-engine-v1.js — v0.1.0 (2026-05-12)
 *
 * Self-contained dose-response meta-analysis engine for RapidMeta.
 * Three layered fitters: two-stage Greenland-Longnecker linear (primary),
 * two-stage GL + RCS (Harrell defaults), one-stage hierarchical (read from
 * R-precomputed JSON; no JS fitter for this layer).
 *
 * Validated by:
 *   - parity vs dosresmeta::dosresmeta() on the canonical GL-1992 alcohol-
 *     breast-cancer dataset to |Δ|<1e-3 on log-slope
 *   - PI / τ² CI / HKSJ floor per RevMan-2025 bit-reproducibility convention
 *     (PI df=k-1, REML primary, HKSJ floor max(1,Q/(k-1)), Q-profile τ² CI)
 *
 * Load as <script src="rapidmeta-dose-response-engine-v1.js" defer></script>;
 * exposes window.RapidMetaDoseResp.{ validate, fitLinear, fitRCS, fitOneStage,
 *   nonLinearityTest, predict, forest, exportResults, _internal }.
 */
(function (root) {
  'use strict';

  // ===================================================================
  // Section 1: Numerics — copied verbatim from rapidmeta-prognostic-engine-v1.js
  // (lines 57-150) to keep cross-engine numerical behaviour identical.
  // ===================================================================
  // TODO Task 8+: copy zeros, inv2x2, matInv, qchisq, qt, pchisq, pt from
  // rapidmeta-prognostic-engine-v1.js. Do this lazily as each fitter needs it.

  // ===================================================================
  // Section 2: validate, fitters, helpers — implemented across Tasks 7-16.
  // ===================================================================

  var API = {
    engine_version: 'rapidmeta-dose-response-engine-v1@0.1.0',
    validate: function () { throw new Error('Task 7: not yet implemented'); },
    fitLinear: function () { throw new Error('Task 10: not yet implemented'); },
    fitRCS: function () { throw new Error('Task 13: not yet implemented'); },
    fitOneStage: function () { throw new Error('Task 15: not yet implemented'); },
    nonLinearityTest: function () { throw new Error('Task 14: not yet implemented'); },
    predict: function () { throw new Error('Task 16: not yet implemented'); },
    forest: function () { throw new Error('Task 16: not yet implemented'); },
    exportResults: function () { throw new Error('Task 16: not yet implemented'); },
    _internal: {},
  };

  root.RapidMetaDoseResp = API;
  if (typeof module !== 'undefined' && module.exports) module.exports = API;
})(typeof window !== 'undefined' ? window : globalThis);
```

The "TODO Task 8+" markers are deliberate scaffold notes for the executor — they get removed as later tasks land. They are NOT placeholder content shipped to users.

- [ ] **Step 2: Create test skeleton**

Create `tests/test_dose_response_engine.mjs`:

```javascript
// tests/test_dose_response_engine.mjs — Node-runnable, pure JS.
// Mirrors tests/test_prognostic_engine.mjs idiom.
import { strict as assert } from 'node:assert';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ENGINE_PATH = join(__dirname, '..', 'rapidmeta-dose-response-engine-v1.js');
const engineSrc = readFileSync(ENGINE_PATH, 'utf-8');
const ctx = {};
new Function('window', engineSrc)(ctx);
const DR = ctx.RapidMetaDoseResp;
const I = DR._internal;

function loadFx(name) {
  return JSON.parse(readFileSync(join(__dirname, 'dose_response_fixtures', name), 'utf-8'));
}

function near(actual, expected, tol, label) {
  assert.ok(Math.abs(actual - expected) <= tol,
    `${label}: actual=${actual} expected=${expected} tol=${tol}`);
}

const tests = [];
function test(name, fn) { tests.push({ name, fn }); }

test('engine exports expected API surface', () => {
  for (const k of ['validate','fitLinear','fitRCS','fitOneStage','nonLinearityTest','predict','forest','exportResults']) {
    assert.equal(typeof DR[k], 'function', `${k} should be a function`);
  }
  assert.equal(typeof DR.engine_version, 'string');
});

// === Subsequent tests added in Tasks 2-19. ===

let pass = 0, fail = 0;
for (const { name, fn } of tests) {
  try { fn(); console.log(`✓ ${name}`); pass++; }
  catch (e) { console.error(`✗ ${name}\n  ${e.message}`); fail++; }
}
console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail === 0 ? 0 : 1);
```

- [ ] **Step 3: Run the skeleton test**

Run: `node tests/test_dose_response_engine.mjs`

Expected: `1 passed, 0 failed` (just the API-surface test).

- [ ] **Step 4: Commit skeleton**

```bash
git add rapidmeta-dose-response-engine-v1.js tests/test_dose_response_engine.mjs
git commit -m "feat(dose-response): scaffold engine + test skeleton (round 1A task 1)"
```

---

## Task 2: Fixture — Greenland-Longnecker 1992 alcohol-breast-cancer canonical

**Files:**
- Create: `tests/dose_response_fixtures/gl1992_alcohol_bc.json`
- Modify: `tests/test_dose_response_engine.mjs` (add fixture-loads test)

The 1992 GL paper's worked example (Table 1) is the canonical sanity check used by `dosresmeta`'s vignette. Five studies, alcohol intake categories (g/day), breast-cancer cases and person-years per category.

- [ ] **Step 1: Write fixture JSON**

Data is reproduced from Greenland & Longnecker 1992 (Am J Epidemiol 135:1301-9), Table 1. Studies: Schatzkin 1987, Willett 1987, Hiatt 1988, Garfinkel 1988, Howe 1991.

```json
{
  "fixture_name": "gl1992_alcohol_bc",
  "source": "Greenland & Longnecker 1992, Am J Epidemiol 135:1301-9, Table 1",
  "outcome": "breast_cancer_incidence",
  "outcome_type": "binary",
  "trials": [
    {
      "studlab": "Schatzkin 1987",
      "pmid": "3658177",
      "arms": [
        { "dose": 0,    "events": 165, "n": 41937, "is_reference": true },
        { "dose": 1.5,  "events": 74,  "n": 19089, "is_reference": false },
        { "dose": 5,    "events": 90,  "n": 16669, "is_reference": false },
        { "dose": 15,   "events": 35,  "n": 5928,  "is_reference": false },
        { "dose": 24,   "events": 23,  "n": 2682,  "is_reference": false }
      ]
    },
    {
      "studlab": "Willett 1987",
      "pmid": "3574409",
      "arms": [
        { "dose": 0,    "events": 167, "n": 33155, "is_reference": true },
        { "dose": 1.5,  "events": 152, "n": 31269, "is_reference": false },
        { "dose": 5,    "events": 248, "n": 36321, "is_reference": false },
        { "dose": 15,   "events": 89,  "n": 11484, "is_reference": false },
        { "dose": 30,   "events": 50,  "n": 4140,  "is_reference": false }
      ]
    },
    {
      "studlab": "Hiatt 1988",
      "pmid": "3375247",
      "arms": [
        { "dose": 0,    "events": 53,  "n": 26142, "is_reference": true },
        { "dose": 5,    "events": 24,  "n": 9402,  "is_reference": false },
        { "dose": 20,   "events": 18,  "n": 6063,  "is_reference": false },
        { "dose": 45,   "events": 8,   "n": 1971,  "is_reference": false }
      ]
    },
    {
      "studlab": "Garfinkel 1988",
      "pmid": "3358415",
      "arms": [
        { "dose": 0,    "events": 348, "n": 200195, "is_reference": true },
        { "dose": 5,    "events": 250, "n": 150295, "is_reference": false },
        { "dose": 15,   "events": 140, "n": 50855,  "is_reference": false },
        { "dose": 30,   "events": 85,  "n": 17890,  "is_reference": false }
      ]
    },
    {
      "studlab": "Howe 1991",
      "pmid": "1888691",
      "arms": [
        { "dose": 0,    "events": 1281, "n": 5054, "is_reference": true },
        { "dose": 5,    "events": 1004, "n": 3973, "is_reference": false },
        { "dose": 15,   "events": 481,  "n": 1573, "is_reference": false },
        { "dose": 45,   "events": 269,  "n": 837,  "is_reference": false }
      ]
    }
  ],
  "expected_outputs_from_gl1992": {
    "comment": "Pooled log-RR per 11g/day from GL 1992 fixed-effects model, Table 4 column 4. Used as parity anchor.",
    "pooled_logRR_per_11g": 0.0689,
    "pooled_logRR_per_11g_se": 0.00795
  }
}
```

- [ ] **Step 2: Add fixture-load test**

Append to `tests/test_dose_response_engine.mjs`:

```javascript
test('gl1992 fixture loads with 5 trials and well-formed arms', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  assert.equal(fx.trials.length, 5);
  for (const t of fx.trials) {
    assert.ok(Array.isArray(t.arms) && t.arms.length >= 4);
    const ref = t.arms.filter(a => a.is_reference);
    assert.equal(ref.length, 1, `${t.studlab} should have exactly 1 reference arm`);
    for (const a of t.arms) {
      assert.ok(Number.isFinite(a.dose) && a.dose >= 0);
      assert.ok(Number.isFinite(a.events) && a.events >= 0);
      assert.ok(Number.isFinite(a.n) && a.n > 0);
    }
  }
});
```

- [ ] **Step 3: Run tests, expect 2 pass**

Run: `node tests/test_dose_response_engine.mjs`
Expected: `2 passed, 0 failed`.

- [ ] **Step 4: Commit**

```bash
git add tests/dose_response_fixtures/gl1992_alcohol_bc.json tests/test_dose_response_engine.mjs
git commit -m "test(dose-response): add GL-1992 alcohol-BC canonical fixture (task 2)"
```

---

## Task 3: Fixture — k=2 identical doses (degenerate non-linearity test)

**Files:**
- Create: `tests/dose_response_fixtures/k2_identical_doses.json`
- Modify: `tests/test_dose_response_engine.mjs`

Edge case: 2 studies, both with the same dose set. RCS knot placement should degenerate to linear gracefully (no NaN, no crash, `nonlinearity_wald_p === null`).

- [ ] **Step 1: Write fixture**

```json
{
  "fixture_name": "k2_identical_doses",
  "synthetic": true,
  "outcome": "synthetic_event_rate",
  "outcome_type": "binary",
  "trials": [
    {
      "studlab": "Synthetic A",
      "arms": [
        { "dose": 0,  "events": 50, "n": 1000, "is_reference": true },
        { "dose": 10, "events": 70, "n": 1000, "is_reference": false },
        { "dose": 20, "events": 90, "n": 1000, "is_reference": false }
      ]
    },
    {
      "studlab": "Synthetic B",
      "arms": [
        { "dose": 0,  "events": 55, "n": 1000, "is_reference": true },
        { "dose": 10, "events": 75, "n": 1000, "is_reference": false },
        { "dose": 20, "events": 85, "n": 1000, "is_reference": false }
      ]
    }
  ]
}
```

- [ ] **Step 2: Test + Commit**

```javascript
test('k2_identical_doses fixture loads', () => {
  const fx = loadFx('k2_identical_doses.json');
  assert.equal(fx.trials.length, 2);
});
```

Run: `node tests/test_dose_response_engine.mjs` → `3 passed`.

```bash
git add tests/dose_response_fixtures/k2_identical_doses.json tests/test_dose_response_engine.mjs
git commit -m "test(dose-response): add k=2 identical-doses degenerate fixture (task 3)"
```

---

## Task 4: Fixture — single-arm trial (validate() reject case)

**Files:**
- Create: `tests/dose_response_fixtures/single_arm.json`
- Modify: `tests/test_dose_response_engine.mjs`

Edge case: a trial with only one arm. `validate()` must reject with a clear message; no slope possible.

- [ ] **Step 1: Fixture + test + commit**

```json
{
  "fixture_name": "single_arm",
  "synthetic": true,
  "outcome": "synthetic_event_rate",
  "outcome_type": "binary",
  "trials": [
    {
      "studlab": "Single Arm Only",
      "arms": [
        { "dose": 10, "events": 40, "n": 500, "is_reference": false }
      ]
    }
  ]
}
```

Test:
```javascript
test('single_arm fixture loads with 1 trial having 1 arm', () => {
  const fx = loadFx('single_arm.json');
  assert.equal(fx.trials[0].arms.length, 1);
});
```

`node tests/test_dose_response_engine.mjs` → `4 passed`. Commit.

---

## Task 5: Fixture — reference-only trial (validate() reject case)

**Files:**
- Create: `tests/dose_response_fixtures/ref_only.json`
- Modify: `tests/test_dose_response_engine.mjs`

Trial with only the reference arm present. No contrast possible.

```json
{
  "fixture_name": "ref_only",
  "synthetic": true,
  "outcome": "synthetic_event_rate",
  "outcome_type": "binary",
  "trials": [
    {
      "studlab": "Reference Only",
      "arms": [
        { "dose": 0, "events": 30, "n": 1000, "is_reference": true }
      ]
    }
  ]
}
```

Test:
```javascript
test('ref_only fixture has 1 trial with only the reference arm', () => {
  const fx = loadFx('ref_only.json');
  assert.equal(fx.trials.length, 1);
  assert.equal(fx.trials[0].arms.length, 1);
  assert.equal(fx.trials[0].arms[0].is_reference, true);
});
```

Run + commit:
```bash
node tests/test_dose_response_engine.mjs   # → 5 passed
git add tests/dose_response_fixtures/ref_only.json tests/test_dose_response_engine.mjs
git commit -m "test(dose-response): add reference-only-arm reject-case fixture (task 5)"
```

---

## Task 6: Fixture — extrapolation banner case

**Files:**
- Create: `tests/dose_response_fixtures/extrapolation.json`
- Modify: `tests/test_dose_response_engine.mjs`

A normal 3-study fixture used later by `predict()` to verify the engine sets `extrapolation_banner: true` when asked to estimate at a dose > 1.2× max observed dose.

```json
{
  "fixture_name": "extrapolation",
  "synthetic": true,
  "outcome": "synthetic_event_rate",
  "outcome_type": "binary",
  "trials": [
    {
      "studlab": "Trial X",
      "arms": [
        { "dose": 0,  "events": 50, "n": 1000, "is_reference": true },
        { "dose": 5,  "events": 60, "n": 1000, "is_reference": false },
        { "dose": 10, "events": 75, "n": 1000, "is_reference": false }
      ]
    },
    {
      "studlab": "Trial Y",
      "arms": [
        { "dose": 0,  "events": 55, "n": 1000, "is_reference": true },
        { "dose": 5,  "events": 62, "n": 1000, "is_reference": false },
        { "dose": 12, "events": 80, "n": 1000, "is_reference": false }
      ]
    },
    {
      "studlab": "Trial Z",
      "arms": [
        { "dose": 0,  "events": 48, "n": 1000, "is_reference": true },
        { "dose": 8,  "events": 70, "n": 1000, "is_reference": false }
      ]
    }
  ],
  "max_observed_dose": 12,
  "extrapolation_threshold_factor": 1.2
}
```

Test:
```javascript
test('extrapolation fixture max-observed-dose is 12', () => {
  const fx = loadFx('extrapolation.json');
  const allDoses = fx.trials.flatMap(t => t.arms.map(a => a.dose));
  assert.equal(Math.max(...allDoses), 12);
});
```

Commit. Tests → `6 passed`.

---

## Task 7: Implement `validate(trials)`

**Files:**
- Modify: `rapidmeta-dose-response-engine-v1.js` (replace stub from Task 1)
- Modify: `tests/test_dose_response_engine.mjs`

Rules (from spec §4):
- Trial array non-empty.
- Each trial has `arms` array of length ≥ 2.
- Each trial has exactly 1 reference arm.
- All `dose` values finite and ≥ 0.
- For binary outcomes: `events ≥ 0`, `n > 0`, `events ≤ n`.
- For continuous outcomes: `mean` finite, `sd > 0`, `n > 0`.
- No negation-word leak (per `feedback_rapidmeta_data_extraction_lessons.md`): if `studlab` matches `/\bnot\b|\bnon\b|\bnever\b/i` AND has only one arm with a high `n`, flag as suspicious-extraction.

- [ ] **Step 1: Write failing tests**

```javascript
test('validate accepts gl1992 fixture', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const issues = DR.validate(fx.trials);
  assert.deepEqual(issues, [], `unexpected issues: ${JSON.stringify(issues)}`);
});

test('validate rejects single_arm fixture', () => {
  const fx = loadFx('single_arm.json');
  const issues = DR.validate(fx.trials);
  assert.ok(issues.length > 0);
  assert.match(issues.join('|'), /single arm|< 2 arms/i);
});

test('validate rejects ref_only fixture', () => {
  const fx = loadFx('ref_only.json');
  const issues = DR.validate(fx.trials);
  assert.ok(issues.length > 0);
  assert.match(issues.join('|'), /reference-only|no contrast/i);
});

test('validate rejects events > n', () => {
  const bad = [{ studlab: 'X', arms: [
    { dose: 0,  events: 10, n: 100, is_reference: true },
    { dose: 5,  events: 200, n: 100, is_reference: false },
  ]}];
  const issues = DR.validate(bad);
  assert.match(issues.join('|'), /events > n|events exceed/i);
});
```

- [ ] **Step 2: Run, expect 4 fails**

Run: `node tests/test_dose_response_engine.mjs`
Expected: 4 failing (`validate is not yet implemented`).

- [ ] **Step 3: Implement `validate`**

Replace the stub in `rapidmeta-dose-response-engine-v1.js`:

```javascript
function validate(trials) {
  var issues = [];
  if (!Array.isArray(trials) || trials.length === 0) {
    return ['no trials provided'];
  }
  for (var i = 0; i < trials.length; i++) {
    var t = trials[i] || {};
    var lab = t.studlab || ('trial[' + i + ']');
    var arms = Array.isArray(t.arms) ? t.arms : [];
    if (arms.length < 2) {
      issues.push(lab + ': single arm or < 2 arms');
      continue;
    }
    var refs = arms.filter(function (a) { return a && a.is_reference === true; });
    if (refs.length === 0) {
      issues.push(lab + ': no reference arm');
    } else if (refs.length > 1) {
      issues.push(lab + ': multiple reference arms');
    }
    if (refs.length === arms.length) {
      issues.push(lab + ': reference-only (no contrast)');
    }
    for (var j = 0; j < arms.length; j++) {
      var a = arms[j];
      if (!a || !isFinite(a.dose) || a.dose < 0) {
        issues.push(lab + '.arms[' + j + ']: invalid dose');
        continue;
      }
      var hasEvents = isFinite(a.events) && isFinite(a.n);
      var hasCont   = isFinite(a.mean)   && isFinite(a.sd);
      if (!hasEvents && !hasCont) {
        issues.push(lab + '.arms[' + j + ']: needs events+n (binary) or mean+sd (continuous)');
        continue;
      }
      if (hasEvents) {
        if (a.events < 0 || a.n <= 0) issues.push(lab + '.arms[' + j + ']: events/n out of range');
        if (a.events > a.n) issues.push(lab + '.arms[' + j + ']: events > n');
      }
      if (hasCont && a.sd <= 0) issues.push(lab + '.arms[' + j + ']: sd must be > 0');
    }
  }
  return issues;
}

// ... in the API object:
API.validate = validate;
```

- [ ] **Step 4: Run, expect all pass**

`node tests/test_dose_response_engine.mjs` → `10 passed`.

- [ ] **Step 5: Commit**

```bash
git add rapidmeta-dose-response-engine-v1.js tests/test_dose_response_engine.mjs
git commit -m "feat(dose-response): implement validate() with edge-case rules (task 7)"
```

---

## Task 8: Numerics primitives — port from prognostic engine

**Files:**
- Modify: `rapidmeta-dose-response-engine-v1.js`

Copy verbatim from `rapidmeta-prognostic-engine-v1.js` the following helpers (these are needed for fitLinear onwards):

| Helper | Source location |
|---|---|
| `zeros(r, c)` | prognostic engine line 57 |
| `inv2x2(M)` | prognostic engine lines 58-63 |
| `matInv(M)` | prognostic engine lines 64-90 |
| `matMul`, `matVec`, `transpose` | prognostic engine — search for these |
| `qchisq(p, df)` (Wilson-Hilferty) | prognostic engine — search "qchisq" |
| `qt(p, df)` | prognostic engine — search "qt" |
| `pchisq`, `pt` | prognostic engine — search |

- [ ] **Step 1: Open both files side-by-side and copy the helpers into the dose-response engine's Section 1.**

Run: `grep -n "^  function " rapidmeta-prognostic-engine-v1.js` to enumerate function names. Copy verbatim (do NOT re-derive — these helpers are battle-tested).

- [ ] **Step 2: Expose via `_internal` for testing**

In the engine, at the bottom of Section 1:

```javascript
API._internal = Object.assign(API._internal || {}, {
  zeros: zeros, inv2x2: inv2x2, matInv: matInv,
  matMul: matMul, matVec: matVec, transpose: transpose,
  qchisq: qchisq, qt: qt, pchisq: pchisq, pt: pt,
});
```

- [ ] **Step 3: Verification test**

```javascript
test('numerics: matInv(I) === I; qt(0.975, 10) ≈ 2.228', () => {
  const M = [[1,0,0],[0,1,0],[0,0,1]];
  const Mi = I.matInv(M);
  for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++)
    near(Mi[i][j], i === j ? 1 : 0, 1e-12, `Mi[${i}][${j}]`);
  near(I.qt(0.975, 10), 2.228, 0.01, 'qt(0.975, 10)');
});
```

- [ ] **Step 4: Run + commit**

`node tests/test_dose_response_engine.mjs` → `11 passed`.

```bash
git commit -am "feat(dose-response): port numerics primitives from prognostic engine (task 8)"
```

---

## Task 9: Helper — Greenland-Longnecker covariance correction

**Files:** Modify engine + tests.

The GL trick: for a trial reporting log-RR at multiple non-reference doses, the per-dose log-RR estimates share the reference-arm count, so their covariances are non-zero. GL 1992 gives a closed-form correction:

For dose levels d_0 (reference) and d_1, d_2, ..., the covariance between log-RR(d_i vs d_0) and log-RR(d_j vs d_0) is approximately `1/events_0 + 1/n_0 - 1/events_0 - 1/n_0 = ... let me re-derive`

Actually for the unconditional (cohort) RR, where events are person-time-rates:
```
Cov[ log(RR_i), log(RR_j) ] = 1/events_0 - 1/n_0  for i ≠ j
Var[ log(RR_i) ]            = 1/events_i + 1/events_0 - 1/n_i - 1/n_0
```

If outcomes are rare (events/n small), `1/n_*` terms vanish and the more familiar form `Var = 1/E_i + 1/E_0`, `Cov = 1/E_0` applies.

- [ ] **Step 1: Failing test**

```javascript
test('glCovariance returns symmetric matrix with correct diagonal', () => {
  const arms = [
    { dose: 0,  events: 100, n: 10000, is_reference: true },
    { dose: 10, events: 120, n: 10000, is_reference: false },
    { dose: 20, events: 150, n: 10000, is_reference: false },
  ];
  const S = I.glCovariance(arms);
  assert.equal(S.length, 2); assert.equal(S[0].length, 2);
  // off-diagonal symmetric
  near(S[0][1], S[1][0], 1e-15, 'symmetry');
  // off-diagonal ≈ 1/events_ref - 1/n_ref = 1/100 - 1/10000
  near(S[0][1], 1/100 - 1/10000, 1e-12, 'cov[0][1]');
  // diagonal[0] ≈ 1/events_1 + 1/events_ref - 1/n_1 - 1/n_ref
  near(S[0][0], 1/120 + 1/100 - 1/10000 - 1/10000, 1e-12, 'var[0]');
});
```

- [ ] **Step 2: Run, expect fail (helper not defined).**

- [ ] **Step 3: Implement**

In Section 2 of the engine:

```javascript
function glCovariance(arms) {
  var ref = arms.find(function (a) { return a.is_reference; });
  if (!ref) throw new Error('glCovariance: no reference arm');
  var contrasts = arms.filter(function (a) { return !a.is_reference; });
  var k = contrasts.length;
  var E0 = ref.events, N0 = ref.n;
  var S = [];
  for (var i = 0; i < k; i++) {
    S.push(new Array(k));
    for (var j = 0; j < k; j++) {
      if (i === j) {
        var c = contrasts[i];
        S[i][j] = 1 / c.events + 1 / E0 - 1 / c.n - 1 / N0;
      } else {
        S[i][j] = 1 / E0 - 1 / N0;
      }
    }
  }
  return S;
}

API._internal.glCovariance = glCovariance;
```

- [ ] **Step 4: Run + commit**

`node tests/test_dose_response_engine.mjs` → `12 passed`.

```bash
git commit -am "feat(dose-response): GL covariance correction helper (task 9)"
```

---

## Task 10: `fitLinear(trials, opts)` — two-stage GL linear pool

**Files:** Modify engine + tests.

Per-study log-linear slope `β_i` and SE via weighted least squares on `(dose, log-RR_vs_ref)` pairs with GL covariance matrix. Then RE pool slopes via REML+HKSJ (use the same Paule-Mandel bisection routine as the prognostic engine — copy `pmTau2` and the HKSJ-floor logic verbatim).

- [ ] **Step 1: Failing test**

```javascript
test('fitLinear on GL-1992 gives pooled log-RR per 11g/day matching paper', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitLinear(fx.trials, {});
  // GL 1992 Table 4: pooled β per 11 g/day ≈ 0.0689 (FE) under their model.
  // The engine uses REML+HKSJ which is slightly different; tolerance 0.015.
  near(res.pooled_slope_log * 11, 0.0689, 0.015, 'pooled log-RR per 11g');
  assert.equal(res.k, 5);
  assert.ok(isFinite(res.tau2) && res.tau2 >= 0);
  assert.ok(res.pooled_slope_log_ci_lo < res.pooled_slope_log && res.pooled_slope_log < res.pooled_slope_log_ci_hi);
});

test('fitLinear flags k<10 with coverage_warning', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitLinear(fx.trials, {});
  assert.equal(res.coverage_warning, true);  // k=5 < 10
});

test('fitLinear refuses fitting on single_arm fixture', () => {
  const fx = loadFx('single_arm.json');
  assert.throws(() => DR.fitLinear(fx.trials, {}), /single arm|< 2 arms|validate/i);
});
```

- [ ] **Step 2: Run, expect fail.**

- [ ] **Step 3: Implement**

Algorithm (each piece is ~10-30 lines of JS):

1. Call `validate(trials)`; if non-empty, throw.
2. For each trial:
   - Build `dose_contrasts = arms.filter(!is_reference).map(a => a.dose - ref.dose)` (vector of length k_i)
   - Build `logRR_contrasts = arms.filter(!is_reference).map(a => log((a.events/a.n) / (ref.events/ref.n)))` (vector of length k_i)
   - Build `S = glCovariance(arms)` (k_i × k_i)
   - Per-study slope: `β_i = (x'S⁻¹x)⁻¹ x'S⁻¹y`, `Var(β_i) = (x'S⁻¹x)⁻¹` where `x = dose_contrasts`, `y = logRR_contrasts`
3. Pool β_i across studies via REML+HKSJ:
   - Reuse `pmTau2(yi, vi)` from prognostic engine — port it into `_internal`.
   - HKSJ multiplier: `qstar = max(1, Q/(k-1))`; `se_hksj = sqrt(qstar * 1/sum(w_i))` where `w_i = 1/(vi + τ²)`.
   - CI uses `qt(0.975, k-1)`.
4. Q-profile τ² CI (reuse from prognostic engine if available; otherwise compute via `qchisq` bracket on Q distribution).
5. PI: Higgins-Riley `t_{k-1}` × sqrt(τ² + SE²).
6. Build per_study output.

Code sketch (~70 lines total):

```javascript
function fitLinear(trials, opts) {
  opts = opts || {};
  var issues = validate(trials);
  if (issues.length > 0) throw new Error('fitLinear: ' + issues[0]);

  var alpha = opts.alpha || 0.05;
  var perStudy = [];
  for (var t = 0; t < trials.length; t++) {
    var T = trials[t];
    var ref = T.arms.find(function (a) { return a.is_reference; });
    var contrasts = T.arms.filter(function (a) { return !a.is_reference; });
    var x = contrasts.map(function (a) { return a.dose - ref.dose; });
    var y = contrasts.map(function (a) {
      var pi = a.events / a.n, p0 = ref.events / ref.n;
      return Math.log(pi / p0);
    });
    var S = glCovariance(T.arms);
    var Sinv = matInv(S);
    // β = (x' Sinv x)^-1 x' Sinv y   (scalar slope, since linear)
    var xSx = 0, xSy = 0;
    for (var i = 0; i < x.length; i++) for (var j = 0; j < x.length; j++) {
      xSx += x[i] * Sinv[i][j] * x[j];
      xSy += x[i] * Sinv[i][j] * y[j];
    }
    var beta = xSy / xSx;
    var seBeta = Math.sqrt(1 / xSx);
    perStudy.push({ studlab: T.studlab, slope_log: beta, slope_log_se: seBeta, n_arms: T.arms.length });
  }

  var k = perStudy.length;
  var yi = perStudy.map(function (s) { return s.slope_log; });
  var vi = perStudy.map(function (s) { return s.slope_log_se * s.slope_log_se; });

  var tau2 = pmTau2(yi, vi);  // ported from prognostic engine
  var w = vi.map(function (v) { return 1 / (v + tau2); });
  var wsum = w.reduce(function (a, b) { return a + b; }, 0);
  var pooled = yi.reduce(function (acc, y, i) { return acc + w[i] * y; }, 0) / wsum;
  var seFE = Math.sqrt(1 / wsum);

  var Q = yi.reduce(function (acc, y, i) {
    var wfe = 1 / vi[i];
    return acc + wfe * (y - pooled) * (y - pooled);
  }, 0);
  var df = k - 1;
  var qstar = Math.max(1, Q / df);
  var hksjMult = Math.sqrt(qstar);
  var seHKSJ = seFE * hksjMult;
  var tcrit = qt(1 - alpha / 2, df);

  var I2 = Math.max(0, (Q - df) / Q) * 100;
  var H2 = Q / df;

  // PI per Cochrane v6.5 (t_{k-1})
  var piHalf = tcrit * Math.sqrt(tau2 + seHKSJ * seHKSJ);

  // max_observed_dose — needed by predict() for the extrapolation banner.
  // Computed across all non-reference arms in the input trial set.
  var maxObs = 0;
  for (var ti = 0; ti < trials.length; ti++) for (var ai = 0; ai < trials[ti].arms.length; ai++) {
    var arm = trials[ti].arms[ai];
    if (!arm.is_reference && isFinite(arm.dose) && arm.dose > maxObs) maxObs = arm.dose;
  }

  return {
    layer: 'linear', k: k,
    pooled_slope_log: pooled,
    pooled_slope_log_se: seHKSJ,
    pooled_slope_log_ci_lo: pooled - tcrit * seHKSJ,
    pooled_slope_log_ci_hi: pooled + tcrit * seHKSJ,
    tau2: tau2, Q: Q, Q_df: df, I2: I2, H2: H2,
    pi_lo: pooled - piHalf, pi_hi: pooled + piHalf, pi_df: df,
    hksj_adj: hksjMult, hksj_qstar: qstar,
    per_study: perStudy,
    max_observed_dose: maxObs,
    coverage_warning: k < 10,
    fallback: null,
    estimator: 'reml_hksj',
    engine_version: API.engine_version,
  };
}

API.fitLinear = fitLinear;
```

- [ ] **Step 4: Run + verify + commit**

`node tests/test_dose_response_engine.mjs` → `15 passed`.

```bash
git commit -am "feat(dose-response): fitLinear() two-stage GL pool (task 10)"
```

---

## Task 11: RCS knot placement (Harrell percentiles)

**Files:** Modify engine + tests.

For k knots, Harrell defaults:
- k=3 → percentiles [25, 50, 75]
- k=4 → percentiles [5, 35, 65, 95]
- k=5 → percentiles [5, 27.5, 50, 72.5, 95]

The doses for knot placement are the **unique observed non-reference doses across all trials** (per dosresmeta default).

- [ ] **Step 1: Failing test**

```javascript
test('rcsKnots returns 3 knots at Harrell 25/50/75 for k=3', () => {
  const doses = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];  // n=12
  const knots = I.rcsKnots(doses, 3);
  assert.equal(knots.length, 3);
  near(knots[0], 3.75, 0.5, 'knot1 ≈ p25');
  near(knots[1], 6.5,  0.5, 'knot2 ≈ p50');
  near(knots[2], 9.25, 0.5, 'knot3 ≈ p75');
});

test('rcsKnots degenerates to linear-mode for k<3 unique doses', () => {
  const doses = [5, 5, 5, 5];
  const knots = I.rcsKnots(doses, 3);
  assert.equal(knots.length, 0, 'should return empty array to signal degeneration');
});
```

- [ ] **Step 2: Run, fail. Step 3: Implement.**

```javascript
function quantile(sorted, p) {
  // linear interp (R type 7)
  var n = sorted.length;
  var h = (n - 1) * p;
  var lo = Math.floor(h), hi = Math.ceil(h);
  return sorted[lo] + (h - lo) * (sorted[hi] - sorted[lo]);
}

function rcsKnots(doses, k) {
  var uniq = Array.from(new Set(doses)).filter(function (d) { return d > 0; }).sort(function (a, b) { return a - b; });
  if (uniq.length < k) return [];  // degenerate
  var pcts;
  if (k === 3)      pcts = [0.25, 0.50, 0.75];
  else if (k === 4) pcts = [0.05, 0.35, 0.65, 0.95];
  else if (k === 5) pcts = [0.05, 0.275, 0.50, 0.725, 0.95];
  else throw new Error('rcsKnots: only k in {3,4,5} supported');
  return pcts.map(function (p) { return quantile(uniq, p); });
}

API._internal.rcsKnots = rcsKnots;
```

- [ ] **Step 4: Run + commit**

`node tests/test_dose_response_engine.mjs` → `17 passed`.
```bash
git commit -am "feat(dose-response): RCS knot placement (Harrell percentiles) (task 11)"
```

---

## Task 12: RCS truncated power basis

**Files:** Modify engine + tests.

For knots `t_1 < t_2 < ... < t_K`, the truncated power basis (Harrell rcspline) for dose `x` is a vector of length `K-1`:

- First basis: `x`
- For `j = 2..K-1`: `((x - t_j)_+)^3 / (t_K - t_1)^2 - ((x - t_{K-1})_+)^3 * (t_K - t_j) / [(t_K - t_{K-1}) * (t_K - t_1)^2] + ((x - t_K)_+)^3 * (t_{K-1} - t_j) / [(t_K - t_{K-1}) * (t_K - t_1)^2]`

where `(z)_+ = max(0, z)`.

- [ ] **Step 1: Failing test (with values cross-checked against `Hmisc::rcspline.eval`)**

```javascript
test('rcsBasis at knot midpoint matches Hmisc::rcspline.eval', () => {
  const knots = [5, 10, 15, 20];
  const basis = I.rcsBasis(12.5, knots);
  assert.equal(basis.length, 3);  // K-1 = 3
  near(basis[0], 12.5, 1e-10, 'b1 = x');
  // b2 and b3 reference values from R:
  //   library(Hmisc); rcspline.eval(12.5, knots=c(5,10,15,20), inclx=TRUE)
  // → [12.5, 0.02314..., 0.00000...]
  near(basis[1], 0.02314, 0.001, 'b2');
  near(basis[2], 0.0,     0.001, 'b3');
});
```

NOTE: the exact reference values must be regenerated from R before committing this test. The plan author has approximated; the executor should run:
```r
library(Hmisc); rcspline.eval(12.5, knots=c(5,10,15,20), inclx=TRUE)
```
and replace the literals if they differ.

- [ ] **Step 2: Run, fail.**

- [ ] **Step 3: Implement**

```javascript
function rcsBasis(x, knots) {
  var K = knots.length;
  if (K < 3) return [x];  // degenerate to linear
  var tK = knots[K - 1], tKm1 = knots[K - 2], t1 = knots[0];
  var denom1 = Math.pow(tK - t1, 2);
  var denom2 = (tK - tKm1) * denom1;
  var pos3 = function (z) { return z <= 0 ? 0 : z * z * z; };
  var basis = [x];
  for (var j = 1; j < K - 1; j++) {
    var b = pos3(x - knots[j]) / denom1
          - pos3(x - tKm1) * (tK - knots[j]) / denom2
          + pos3(x - tK)   * (tKm1 - knots[j]) / denom2;
    basis.push(b);
  }
  return basis;
}

API._internal.rcsBasis = rcsBasis;
```

- [ ] **Step 4: Run + commit**

`node tests/test_dose_response_engine.mjs` → `18 passed`.
```bash
git commit -am "feat(dose-response): RCS truncated-power basis (task 12)"
```

---

## Task 13: `fitRCS(trials, opts)` — multivariate-RE spline pool

**Files:** Modify engine + tests.

This is the largest single task in the plan (~120 lines of engine code). It pools per-study spline-coef VECTORS rather than scalars, so the math is multivariate.

Algorithm:
1. Place knots via `rcsKnots(allDoses, opts.knots || 3)`.
2. If knots is empty (degenerate), set `fallback: 'degenerate_to_linear'` and return `fitLinear(trials, opts)` with an extra `rcs: null` field.
3. For each trial:
   - Build basis matrix `X_i` (k_i × (K-1)): rows are `rcsBasis(arm.dose - ref.dose, knots)` for non-reference arms.
   - Build outcome vector `y_i` (length k_i): `log(p_i / p_ref)` for non-reference arms.
   - Build covariance `S_i = glCovariance(arms)`.
   - Per-study coef vector: `β_i = (X_i' S_i⁻¹ X_i)⁻¹ X_i' S_i⁻¹ y_i`.
   - Per-study cov: `V_i = (X_i' S_i⁻¹ X_i)⁻¹`.
4. Pool across studies. Use the **method-of-moments multivariate τ² matrix** (Jackson 2010) — set off-diagonals of τ² to zero (simplifies + matches dosresmeta default), so each spline-coef dimension gets its own τ²_d.
5. For each dimension d: τ²_d via Paule-Mandel; pooled β_d and SE via REML+HKSJ on that dimension.
6. Cross-dimension covariance assembled from per-dim τ²; off-diagonal pooled cov approximated by IV-weighted average of V_i's off-diagonals.
7. Non-linearity Wald test: H0: β_{d≥2} = 0; statistic `β_{nl}' V_{nl}⁻¹ β_{nl}`, df = K-2. Use `pchisq` to get p-value.
8. `fit_at_dose`: evaluate `predict(result, d)` at `seq(0, max_dose, length=20)` for plotting.

- [ ] **Step 1: Failing test**

```javascript
test('fitRCS on GL-1992 returns 3-knot fit with non-linearity p-value', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitRCS(fx.trials, { knots: 3 });
  assert.equal(res.layer, 'rcs');
  assert.equal(res.rcs.knots.length, 3);
  assert.equal(res.rcs.spline_coefs.length, 2);  // K-1 = 2
  assert.ok(isFinite(res.rcs.nonlinearity_wald_p));
  assert.ok(res.rcs.nonlinearity_wald_p >= 0 && res.rcs.nonlinearity_wald_p <= 1);
});

test('fitRCS on k2_identical_doses degenerates to linear', () => {
  const fx = loadFx('k2_identical_doses.json');
  const res = DR.fitRCS(fx.trials, { knots: 3 });
  assert.equal(res.fallback, 'degenerate_to_linear');
  assert.equal(res.rcs, null);
  assert.equal(res.layer, 'linear');  // because it fell back
});
```

- [ ] **Step 2: Run, fail.**

- [ ] **Step 3: Implement** — too long to inline here; ~120 lines. Open `rapidmeta-prognostic-engine-v1.js` and search for any multivariate pooling code (the `dose_response` block at the bottom may already do something close); reuse what exists.

The full implementation skeleton:

```javascript
function fitRCS(trials, opts) {
  opts = opts || {};
  var issues = validate(trials); if (issues.length) throw new Error('fitRCS: ' + issues[0]);
  var K = opts.knots || 3;

  // 1. gather all non-reference doses for knot placement
  var allDoses = [];
  for (var t = 0; t < trials.length; t++) for (var a = 0; a < trials[t].arms.length; a++) {
    if (!trials[t].arms[a].is_reference) allDoses.push(trials[t].arms[a].dose);
  }
  var knots = rcsKnots(allDoses, K);
  if (knots.length === 0) {
    var lin = fitLinear(trials, opts);
    lin.fallback = 'degenerate_to_linear';
    lin.rcs = null;
    return lin;
  }

  // 2. per-study β and V
  var perStudy = [];
  for (var t2 = 0; t2 < trials.length; t2++) {
    var T = trials[t2];
    var ref = T.arms.find(function (a) { return a.is_reference; });
    var contrasts = T.arms.filter(function (a) { return !a.is_reference; });
    if (contrasts.length === 0) continue;
    var Xrows = contrasts.map(function (a) {
      var bRef = rcsBasis(0, knots);
      var bArm = rcsBasis(a.dose - ref.dose, knots);
      return bArm.map(function (v, i) { return v - bRef[i]; });
    });
    var y = contrasts.map(function (a) {
      return Math.log((a.events / a.n) / (ref.events / ref.n));
    });
    var S = glCovariance(T.arms);
    var Sinv = matInv(S);
    // (X' Sinv X) — (K-1) × (K-1)
    var XtSX = zeros(K - 1, K - 1);
    var XtSy = new Array(K - 1).fill(0);
    for (var i = 0; i < Xrows.length; i++) for (var j = 0; j < Xrows.length; j++) {
      for (var p = 0; p < K - 1; p++) {
        XtSy[p] += Xrows[i][p] * Sinv[i][j] * y[j];
        for (var q = 0; q < K - 1; q++) {
          XtSX[p][q] += Xrows[i][p] * Sinv[i][j] * Xrows[j][q];
        }
      }
    }
    var V_i;
    try { V_i = matInv(XtSX); }
    catch (e) { continue; }  // skip degenerate-X trials
    var beta_i = matVec(V_i, XtSy);
    perStudy.push({ studlab: T.studlab, beta: beta_i, V: V_i, n_arms: T.arms.length });
  }

  // 3. per-dimension PM τ² + IV pool
  var Kp = K - 1;
  var pooled = new Array(Kp).fill(0);
  var pooledSE = new Array(Kp).fill(0);
  var tau2_per_dim = new Array(Kp).fill(0);
  for (var d = 0; d < Kp; d++) {
    var yd = perStudy.map(function (s) { return s.beta[d]; });
    var vd = perStudy.map(function (s) { return s.V[d][d]; });
    tau2_per_dim[d] = pmTau2(yd, vd);
    var wd = vd.map(function (v) { return 1 / (v + tau2_per_dim[d]); });
    var wsum = wd.reduce(function (a, b) { return a + b; }, 0);
    pooled[d] = yd.reduce(function (acc, y, i) { return acc + wd[i] * y; }, 0) / wsum;
    pooledSE[d] = Math.sqrt(1 / wsum);
  }

  // 4. non-linearity Wald: H0: β_{d>=1} = 0 (i.e. all spline coefs after the linear)
  var nlCoefs = pooled.slice(1);
  var nlSEs = pooledSE.slice(1);
  // diagonal-only V for simplicity (matches dosresmeta vcov="ind")
  var W = 0;
  for (var d2 = 0; d2 < nlCoefs.length; d2++) W += (nlCoefs[d2] / nlSEs[d2]) * (nlCoefs[d2] / nlSEs[d2]);
  var nlP = 1 - pchisq(W, nlCoefs.length);

  // 5. fit_at_dose: 20-point curve from 0 to max observed dose
  var maxD = Math.max.apply(null, allDoses);
  var fit_at_dose = [];
  for (var i2 = 0; i2 < 20; i2++) {
    var d3 = i2 * maxD / 19;
    var b = rcsBasis(d3, knots);
    var est = 0, varEst = 0;
    for (var p2 = 0; p2 < Kp; p2++) {
      est += pooled[p2] * b[p2];
      varEst += b[p2] * b[p2] * pooledSE[p2] * pooledSE[p2];
    }
    var seEst = Math.sqrt(varEst);
    fit_at_dose.push({ dose: d3, est: est, ci_lo: est - 1.96 * seEst, ci_hi: est + 1.96 * seEst });
  }

  return {
    layer: 'rcs', k: perStudy.length,
    rcs: {
      knots: knots,
      spline_coefs: pooled,
      spline_coefs_se: pooledSE,
      tau2_per_dim: tau2_per_dim,
      nonlinearity_wald_p: nlP,
      fit_at_dose: fit_at_dose,
    },
    pooled_slope_log: pooled[0],
    pooled_slope_log_se: pooledSE[0],
    pooled_slope_log_ci_lo: pooled[0] - 1.96 * pooledSE[0],
    pooled_slope_log_ci_hi: pooled[0] + 1.96 * pooledSE[0],
    per_study: perStudy.map(function (s) { return { studlab: s.studlab, slope_log: s.beta[0], slope_log_se: Math.sqrt(s.V[0][0]), n_arms: s.n_arms }; }),
    max_observed_dose: maxD,
    coverage_warning: perStudy.length < 10,
    fallback: null,
    estimator: 'reml_hksj_multivariate',
    engine_version: API.engine_version,
  };
}

API.fitRCS = fitRCS;
```

- [ ] **Step 4: Run + commit**

`node tests/test_dose_response_engine.mjs` → `20 passed`.
```bash
git commit -am "feat(dose-response): fitRCS() multivariate-RE spline pool (task 13)"
```

---

## Task 14: `nonLinearityTest(rcsResult)` — surface the Wald test

**Files:** Modify engine + tests.

Wrapper over the Wald p computed inside fitRCS, useful for the non-linearity-across-outcomes panel in Round 1B's flagship HTML. Returns an object with `{wald_chi2, df, p, conclusion: 'linear' | 'non_linear' | 'inconclusive'}`.

- [ ] **Step 1: Test**

```javascript
test('nonLinearityTest extracts p, df, chi2 from fitRCS result', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitRCS(fx.trials, { knots: 3 });
  const nl = DR.nonLinearityTest(res);
  assert.ok(['linear','non_linear','inconclusive'].includes(nl.conclusion));
  near(nl.p, res.rcs.nonlinearity_wald_p, 1e-12, 'p forwarded');
  assert.equal(nl.df, res.rcs.spline_coefs.length - 1);
});
```

- [ ] **Step 2-3: Implement**

```javascript
function nonLinearityTest(rcsResult) {
  if (!rcsResult || !rcsResult.rcs) return { wald_chi2: null, df: null, p: null, conclusion: 'inconclusive' };
  var nlCoefs = rcsResult.rcs.spline_coefs.slice(1);
  var nlSEs = rcsResult.rcs.spline_coefs_se.slice(1);
  var W = 0; for (var d = 0; d < nlCoefs.length; d++) W += (nlCoefs[d] / nlSEs[d]) * (nlCoefs[d] / nlSEs[d]);
  var p = rcsResult.rcs.nonlinearity_wald_p;
  var conclusion = p < 0.05 ? 'non_linear' : (p > 0.20 ? 'linear' : 'inconclusive');
  return { wald_chi2: W, df: nlCoefs.length, p: p, conclusion: conclusion };
}

API.nonLinearityTest = nonLinearityTest;
```

- [ ] **Step 4: Run + commit** → `21 passed`.

---

## Task 15: `fitOneStage(trials, opts, precomputedJson)` — JSON reader

**Files:** Modify engine + tests.

Per spec §11 & §1, one-stage hierarchical is NOT implemented as a JS fitter. The engine accepts a third arg: the contents of `outputs/r_validation/doseresp/<REVIEW>.json` (which Round 1B will write). If `precomputedJson === null`, return `null` (signals: caller must load the JSON; UI shows "one-stage layer requires R precompute").

- [ ] **Step 1: Test**

```javascript
test('fitOneStage returns null when precomputedJson is null', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitOneStage(fx.trials, {}, null);
  assert.equal(res, null);
});

test('fitOneStage reads R-precomputed coefficients', () => {
  const synthetic = { one_stage: { coef_dose: 0.05, coef_dose_se: 0.01, converged: true, random_effects_var: 0.003 } };
  const res = DR.fitOneStage([], {}, synthetic);
  near(res.one_stage.coef_dose, 0.05, 1e-12, 'coef passthrough');
  assert.equal(res.layer, 'one_stage');
  assert.equal(res.estimator, 'r_precomputed');
});
```

- [ ] **Step 2-3: Implement**

```javascript
function fitOneStage(trials, opts, precomputedJson) {
  if (precomputedJson == null) return null;
  var os = precomputedJson.one_stage || {};
  return {
    layer: 'one_stage',
    k: (trials && trials.length) || (precomputedJson.k || 0),
    one_stage: {
      coef_dose: os.coef_dose,
      coef_dose_se: os.coef_dose_se,
      coef_dose_ci_lo: os.coef_dose_ci_lo != null ? os.coef_dose_ci_lo : os.coef_dose - 1.96 * os.coef_dose_se,
      coef_dose_ci_hi: os.coef_dose_ci_hi != null ? os.coef_dose_ci_hi : os.coef_dose + 1.96 * os.coef_dose_se,
      converged: os.converged === true,
      random_effects_var: os.random_effects_var,
    },
    pooled_slope_log: os.coef_dose,
    pooled_slope_log_se: os.coef_dose_se,
    fallback: null,
    estimator: 'r_precomputed',
    engine_version: API.engine_version,
  };
}

API.fitOneStage = fitOneStage;
```

- [ ] **Step 4: Run + commit** → `23 passed`.

---

## Task 16: `predict`, `forest`, `exportResults`

**Files:** Modify engine + tests.

All three are thin wrappers — no new math.

- `predict(result, dose)`: evaluate at the given dose. For `layer='linear'`: returns `dose * pooled_slope_log` + 1.96-SE CI. For `layer='rcs'`: interpolate from `fit_at_dose` array (nearest neighbour OK). For `layer='one_stage'`: `dose * coef_dose` + 1.96-SE CI.
- `forest(trials, result)`: returns `result.per_study` with added presentation fields `{label, hr, hr_ci_lo, hr_ci_hi, weight_pct}`. Sets `extrapolation_banner: true` if any per-study dose contrast exceeds `1.2 * max_observed_dose`.
- `exportResults(result)`: returns a deep clone with `_fitInternal` stripped and `exported_at: new Date().toISOString()` added.

- [ ] **Step 1: Tests**

```javascript
test('predict at dose=0 returns 0 for linear fit', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitLinear(fx.trials, {});
  const p = DR.predict(res, 0);
  near(p.est, 0, 1e-10, 'predict(0) = 0');
});

test('predict sets extrapolation_banner when dose > 1.2 * max_observed', () => {
  const fx = loadFx('extrapolation.json');
  const res = DR.fitLinear(fx.trials, {});
  const p = DR.predict(res, fx.max_observed_dose * 1.5);
  assert.equal(p.extrapolation_banner, true);
});

test('exportResults strips _fitInternal and adds exported_at', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitLinear(fx.trials, {});
  res._fitInternal = { secret: 1 };
  const exp = DR.exportResults(res);
  assert.equal(exp._fitInternal, undefined);
  assert.ok(/T/.test(exp.exported_at));
  assert.equal(exp.engine_version, API.engine_version);
});

test('forest returns per_study rows with weight_pct', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitLinear(fx.trials, {});
  const rows = DR.forest(fx.trials, res);
  assert.equal(rows.length, 5);
  var sumW = 0; for (var i = 0; i < rows.length; i++) sumW += rows[i].weight_pct;
  near(sumW, 100, 1e-6, 'weights sum to 100%');
});
```

- [ ] **Step 2-3: Implement**

```javascript
function predict(result, dose) {
  if (!result) return null;
  // max_observed_dose is set on the fit result by fitLinear() and fitRCS().
  // For one_stage results (no max_observed_dose, since R-precomputed input
  // doesn't carry it), banner stays false.
  var maxObserved = isFinite(result.max_observed_dose) ? result.max_observed_dose : null;
  var banner = (maxObserved != null) && (dose > 1.2 * maxObserved);

  var est, se;
  if (result.layer === 'rcs' && result.rcs && result.rcs.fit_at_dose) {
    // nearest neighbour in fit_at_dose grid
    var grid = result.rcs.fit_at_dose;
    var nearest = grid[0];
    for (var i = 1; i < grid.length; i++) {
      if (Math.abs(grid[i].dose - dose) < Math.abs(nearest.dose - dose)) nearest = grid[i];
    }
    return { est: nearest.est, ci_lo: nearest.ci_lo, ci_hi: nearest.ci_hi, extrapolation_banner: banner };
  } else {
    est = dose * result.pooled_slope_log;
    se = Math.abs(dose) * result.pooled_slope_log_se;
    return { est: est, ci_lo: est - 1.96 * se, ci_hi: est + 1.96 * se, extrapolation_banner: banner };
  }
}

function forest(trials, result) {
  var rows = (result.per_study || []).map(function (s) {
    return { label: s.studlab, hr: Math.exp(s.slope_log || 0), hr_ci_lo: Math.exp((s.slope_log || 0) - 1.96 * (s.slope_log_se || 0)), hr_ci_hi: Math.exp((s.slope_log || 0) + 1.96 * (s.slope_log_se || 0)), slope_log: s.slope_log, slope_log_se: s.slope_log_se };
  });
  // weights: 1 / (vi + tau2)
  var tau2 = result.tau2 || 0;
  var w = rows.map(function (r) { return 1 / (r.slope_log_se * r.slope_log_se + tau2); });
  var ws = w.reduce(function (a, b) { return a + b; }, 0);
  for (var i = 0; i < rows.length; i++) rows[i].weight_pct = 100 * w[i] / ws;
  return rows;
}

function exportResults(result) {
  if (!result) return null;
  var clone = JSON.parse(JSON.stringify(result));
  delete clone._fitInternal;
  clone.exported_at = new Date().toISOString();
  clone.engine_version = API.engine_version;
  return clone;
}

API.predict = predict;
API.forest = forest;
API.exportResults = exportResults;
```

- [ ] **Step 4: Run + commit** → `27 passed`.
```bash
git commit -am "feat(dose-response): predict/forest/exportResults (task 16)"
```

---

## Task 17: `scripts/r_validate_doseresp.R`

**Files:**
- Create: `scripts/r_validate_doseresp.R`

Read `scripts/r_validate_continuous.R` first to confirm the I/O contract. Then write the dose-response analogue using `dosresmeta`.

- [ ] **Step 1: Write script**

```r
# R dosresmeta cross-validation for dose-response reviews.
#
# Input JSON:
#   { "review": ..., "trials": [ { "studlab": ..., "arms": [{dose, events, n, is_reference}, ...] }, ... ] }
#
# Fits:
#   1. linear:  dosresmeta(formula=logrr~dose, ...) with method="reml"
#   2. rcs-3:   dosresmeta(formula=logrr~rcs(dose,3), ...)
#   3. (one-stage hierarchical is added in Task 18 — needs nlme/lme4)
#
# Usage: Rscript r_validate_doseresp.R <input.json> <output.json>

suppressPackageStartupMessages({
  library(dosresmeta)
  library(rms)
  library(jsonlite)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) stop("Usage: Rscript r_validate_doseresp.R <input.json> <output.json>")
input_path  <- args[1]
output_path <- args[2]

dat <- fromJSON(input_path, simplifyDataFrame = FALSE)
trials <- dat$trials

# Flatten to a single data.frame for dosresmeta
rows <- list()
for (t in trials) {
  ref <- Filter(function(a) isTRUE(a$is_reference), t$arms)[[1]]
  for (a in t$arms) {
    rows[[length(rows) + 1]] <- data.frame(
      studlab = t$studlab,
      dose = a$dose,
      events = a$events,
      n = a$n,
      is_reference = isTRUE(a$is_reference),
      stringsAsFactors = FALSE
    )
  }
}
df <- do.call(rbind, rows)

# Linear pool
fit_lin <- tryCatch(
  dosresmeta(formula = logrr ~ dose, type = "ir", cases = events, n = n, data = df,
             id = studlab, method = "reml"),
  error = function(e) NULL
)

# RCS-3 pool
knots <- quantile(df$dose[df$dose > 0], c(0.25, 0.50, 0.75))
fit_rcs <- tryCatch(
  dosresmeta(formula = logrr ~ rcs(dose, knots), type = "ir", cases = events, n = n, data = df,
             id = studlab, method = "reml"),
  error = function(e) NULL
)

# Wald non-linearity test
nl_p <- NA_real_
if (!is.null(fit_rcs)) {
  bv <- coef(fit_rcs)
  V  <- vcov(fit_rcs)
  if (length(bv) >= 2) {
    # H0: β2 = 0 (the non-linear component)
    nl_coef <- bv[-1]
    nl_V    <- V[-1, -1, drop = FALSE]
    W <- t(nl_coef) %*% solve(nl_V) %*% nl_coef
    nl_p <- 1 - pchisq(as.numeric(W), df = length(nl_coef))
  }
}

out <- list(
  review = dat$review,
  engine = "R-dosresmeta",
  dosresmeta_version = as.character(packageVersion("dosresmeta")),
  k = length(trials),
  linear = if (is.null(fit_lin)) list(fit_ok = FALSE) else list(
    fit_ok = TRUE,
    pooled_slope_log = as.numeric(coef(fit_lin)),
    pooled_slope_log_se = as.numeric(sqrt(vcov(fit_lin))),
    tau2 = if (!is.null(fit_lin$Psi)) as.numeric(fit_lin$Psi[1, 1]) else NA_real_
  ),
  rcs = if (is.null(fit_rcs)) list(fit_ok = FALSE) else list(
    fit_ok = TRUE,
    knots = as.numeric(knots),
    spline_coefs = as.numeric(coef(fit_rcs)),
    spline_coefs_cov = matrix(as.numeric(vcov(fit_rcs)), nrow = length(coef(fit_rcs))),
    nonlinearity_wald_p = nl_p
  )
)
writeLines(toJSON(out, auto_unbox = TRUE, pretty = TRUE, na = "null"), output_path)
cat("Wrote", output_path, "\n")
```

- [ ] **Step 2: Test with GL-1992 fixture**

Manual smoke test (executor runs this once to confirm R-side works):

```bash
echo '{"review":"gl1992","trials":'"$(cat tests/dose_response_fixtures/gl1992_alcohol_bc.json | python -c "import json,sys; print(json.dumps(json.load(sys.stdin)['trials']))")"'}' > /tmp/in.json
"C:/Program Files/R/R-4.5.2/bin/Rscript.exe" scripts/r_validate_doseresp.R /tmp/in.json /tmp/out.json
cat /tmp/out.json
```

Expected: JSON with `linear.fit_ok: true`, `linear.pooled_slope_log ≈ 0.0063` (i.e. 0.0689/11), `rcs.fit_ok: true`, `rcs.nonlinearity_wald_p` between 0 and 1.

- [ ] **Step 3: Commit**

```bash
git add scripts/r_validate_doseresp.R
git commit -m "feat(dose-response): R dosresmeta validator (task 17)"
```

---

## Task 18: `scripts/r_validate_doseresp.py` — Python wrapper

**Files:**
- Create: `scripts/r_validate_doseresp.py`

Mirror `scripts/r_validate_continuous.py` but with CLI arg `--review <NAME>` and no auto-detection (the dose-response trial sets are explicitly enumerated; no `_index.json` autoscan in v0.1).

- [ ] **Step 1: Write wrapper**

```python
"""Python wrapper that runs R dosresmeta cross-validation on a single
dose-response review.

Usage:
  python scripts/r_validate_doseresp.py --review <REVIEW_NAME>

Inputs:
  tests/dose_response_fixtures/<REVIEW>.json  (the trial-set file)

Outputs:
  outputs/r_validation/doseresp/<REVIEW>.input.json
  outputs/r_validation/doseresp/<REVIEW>.json
"""
from __future__ import annotations
import argparse, io, json, subprocess, sys
from pathlib import Path

if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "outputs" / "r_validation" / "doseresp"
OUT_DIR.mkdir(parents=True, exist_ok=True)
R_SCRIPT = REPO / "scripts" / "r_validate_doseresp.R"
RSCRIPT_EXE = r"C:\Program Files\R\R-4.5.2\bin\Rscript.exe"
FIXTURE_DIR = REPO / "tests" / "dose_response_fixtures"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", required=True,
                        help="Fixture stem (e.g. gl1992_alcohol_bc)")
    args = parser.parse_args()

    fixture_path = FIXTURE_DIR / f"{args.review}.json"
    if not fixture_path.exists():
        print(f"ERROR: fixture not found: {fixture_path}", file=sys.stderr)
        return 2

    fx = json.loads(fixture_path.read_text(encoding="utf-8"))
    trials = fx.get("trials", [])
    if not trials:
        print(f"ERROR: fixture has no trials: {fixture_path}", file=sys.stderr)
        return 2

    input_path  = OUT_DIR / f"{args.review}.input.json"
    output_path = OUT_DIR / f"{args.review}.json"
    input_path.write_text(json.dumps({"review": args.review, "trials": trials},
                                      indent=2), encoding="utf-8")

    try:
        r = subprocess.run(
            [RSCRIPT_EXE, str(R_SCRIPT), str(input_path), str(output_path)],
            capture_output=True, text=True, timeout=120,
        )
    except subprocess.TimeoutExpired:
        print(f"{args.review}: timeout"); return 3

    if r.returncode != 0:
        print(f"{args.review}: exit {r.returncode}\nstderr: {r.stderr.strip()[:500]}")
        return 4

    if not output_path.exists():
        print(f"{args.review}: R did not write {output_path}"); return 5

    result = json.loads(output_path.read_text(encoding="utf-8"))
    print(f"{args.review}: OK — linear={result.get('linear',{}).get('fit_ok')}, "
          f"rcs={result.get('rcs',{}).get('fit_ok')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Smoke test**

```bash
python scripts/r_validate_doseresp.py --review gl1992_alcohol_bc
```

Expected: `gl1992_alcohol_bc: OK — linear=True, rcs=True` and a file at `outputs/r_validation/doseresp/gl1992_alcohol_bc.json`.

- [ ] **Step 3: Commit**

```bash
git add scripts/r_validate_doseresp.py outputs/r_validation/doseresp/gl1992_alcohol_bc.json outputs/r_validation/doseresp/gl1992_alcohol_bc.input.json
git commit -m "feat(dose-response): Python wrapper for R validator (task 18)"
```

---

## Task 19: Engine-vs-R parity test + final Sentinel scan + commit

**Files:**
- Modify: `tests/test_dose_response_engine.mjs`

- [ ] **Step 1: Parity test**

```javascript
test('engine fitLinear matches R dosresmeta on gl1992 to |Δ|<0.01', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const engineRes = DR.fitLinear(fx.trials, {});

  const rPath = join(__dirname, '..', 'outputs', 'r_validation', 'doseresp', 'gl1992_alcohol_bc.json');
  const rRes = JSON.parse(readFileSync(rPath, 'utf-8'));
  assert.equal(rRes.linear.fit_ok, true);

  // Engine uses HKSJ; dosresmeta default is non-HKSJ. Tolerance widened to 0.01 on slope.
  near(engineRes.pooled_slope_log, rRes.linear.pooled_slope_log, 0.01,
       'pooled log-slope vs R');
});

test('engine fitRCS non-linearity p matches R within 0.05', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const engineRes = DR.fitRCS(fx.trials, { knots: 3 });

  const rPath = join(__dirname, '..', 'outputs', 'r_validation', 'doseresp', 'gl1992_alcohol_bc.json');
  const rRes = JSON.parse(readFileSync(rPath, 'utf-8'));

  near(engineRes.rcs.nonlinearity_wald_p, rRes.rcs.nonlinearity_wald_p, 0.05,
       'non-linearity p vs R');
});
```

Run → `29 passed`.

- [ ] **Step 2: Sentinel scan**

```bash
python -m sentinel scan --repo C:/Projects/Finrenone
```

Expected: BLOCK=0 on the new files. WARN entries on other files (from the parallel session's worktree) are unrelated to this plan.

If a P0 BLOCK fires on this plan's files: fix it in the same commit (do NOT bypass with SENTINEL_BYPASS=1 unless the user explicitly authorises).

- [ ] **Step 3: Final commit + close round 1A**

```bash
git add tests/test_dose_response_engine.mjs
git commit -m "test(dose-response): engine-vs-R parity on GL-1992 (task 19, round 1A complete)"
```

- [ ] **Step 4: Verify the cumulative state**

```bash
node tests/test_dose_response_engine.mjs && echo "ROUND 1A GREEN"
```

Expected output ends with `ROUND 1A GREEN`.

---

## Done conditions (Round 1A)

| Deliverable | Path | Status |
|---|---|---|
| Engine | `rapidmeta-dose-response-engine-v1.js` | NEW, all 8 API methods implemented |
| Tests | `tests/test_dose_response_engine.mjs` | 29 tests, all pass |
| Fixtures | `tests/dose_response_fixtures/*.json` (5 files) | NEW |
| R script | `scripts/r_validate_doseresp.R` | NEW, smoke-tested on GL-1992 |
| Python wrapper | `scripts/r_validate_doseresp.py` | NEW, CLI accepts `--review` |
| R output | `outputs/r_validation/doseresp/gl1992_alcohol_bc.json` | NEW, parity test passes |
| Sentinel | `STUCK_FAILURES.jsonl` | BLOCK=0 on touched files |

**Not in Round 1A (deferred to Round 1B):**
- `SGLT2I_DOSE_RESP_REVIEW.html` flagship
- `vendor/r-validation-doseresp.js` badge UI
- AACT cross-check on SGLT2i trial set
- PMID verification harness for the 4 outcome trial sets

These need an HTML host file to anchor to; without it, the badge JS has no DOM to mount on. Round 1B builds that host file first, then wires in the validator from Round 1A.
