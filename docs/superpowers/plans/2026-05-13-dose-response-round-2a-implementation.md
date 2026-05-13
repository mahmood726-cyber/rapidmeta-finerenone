# Dose-Response Pack — Round 2A Implementation Plan (SGLT2i + Engine v0.2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `SGLT2I_DOSE_RESP_REVIEW.html` (5-tab pooled-class SGLT2i flagship on HbA1c primary + hHF secondary) and the engine v0.2 extension (continuous-outcome branch + F-1 zero-cell continuity correction) that the flagship requires.

**Architecture:** Engine extensions land first (5 commits), then R-script continuous-mode dispatch (1 commit), then fixtures + R precompute (3 commits), then flagship HTML built tab-by-tab (5 commits), then pre-push gates + close (2 commits). ~16 commits across 5 logical groups. Each group has a clear validation gate.

**Tech Stack:** ES5-compatible JS (browser, no build step), Node ≥18 for tests, R 4.5.2 + `dosresmeta` 2.2.0 + `lme4` 1.1-37, Python 3.13. PubMed MCP server (already connected in this environment) for trial data lookup.

**Spec:** `docs/superpowers/specs/2026-05-13-dose-response-round-2a-design.md` (committed `bdc06769`, with math correction at §3.1 — continuous-mode covariance has the same shared-reference off-diagonal structure as binary GL).

---

## File Structure

| Path | Responsibility | Action |
|---|---|---|
| `rapidmeta-dose-response-engine-v1.js` | Engine v0.2.0: pool-level outcome dispatch, `mdCovariance` helper, continuous-branch in `fitLinear`/`fitRCS`, F-1 zero-cell correction | MODIFY |
| `tests/test_dose_response_engine.mjs` | New tests: pool-mode-dispatch, mdCovariance shape, continuous fitLinear parity, F-1 conditional, fitRCS continuous | MODIFY |
| `scripts/r_validate_doseresp.R` | Add continuous-mode dispatch (`dosresmeta type="md"` + `lme4::lmer` one-stage) | MODIFY |
| `tests/dose_response_fixtures/sglt2i_hba1c.json` | NEW — 4 trials, continuous HbA1c change | NEW |
| `tests/dose_response_fixtures/sglt2i_hhf.json` | NEW — 3 trials, binary hHF events (SOLOIST low-dose triggers F-1) | NEW |
| `outputs/r_validation/doseresp/sglt2i_hba1c.json` | R-precomputed continuous-mode output | NEW |
| `outputs/r_validation/doseresp/sglt2i_hhf.json` | R-precomputed binary-mode output | NEW |
| `SGLT2I_DOSE_RESP_REVIEW.html` | 5-tab flagship (HbA1c Linear/RCS/One-stage, hHF secondary, R-parity) | NEW |

**Pre-existing dependencies** (already merged at `2e96489a`):
- Engine v0.1.0 with binary `fitLinear`/`fitRCS`/`glCovariance`, F-2 + F-3 fixes, `fitOneStage` JSON reader, `predict` with `ci_method` honoring
- R-validator triplet `scripts/r_validate_doseresp.{R,py}` + `vendor/r-validation-doseresp.js` badge
- 37 tests passing

---

## Group A — Engine extensions (Tasks 1-7)

### Task 1: Engine version bump v0.1.0 → v0.2.0

**Files:**
- Modify: `rapidmeta-dose-response-engine-v1.js` (file header comment + `engine_version` constant)

- [ ] **Step 1: Update the header comment date and version**

Find the file header. Update the version line from `v0.1.0 (2026-05-12)` to `v0.2.0 (2026-05-13)`. Add a single line under "Validated by:":

```
 *   - continuous-outcome branch via mdCovariance + dosresmeta type='md' on
 *     SGLT2i HbA1c fixture (k=4 trials, validated against dosresmeta MD pool)
```

- [ ] **Step 2: Update `engine_version` constant**

Find `engine_version: 'rapidmeta-dose-response-engine-v1@0.1.0'`. Change to `'rapidmeta-dose-response-engine-v1@0.2.0'`.

- [ ] **Step 3: Run tests, verify pass-count unchanged**

Run: `cd C:/Projects/Finrenone/.claude/worktrees/<wt>/ && node tests/test_dose_response_engine.mjs 2>&1 | tail -3`
Expected: `37 passed, 0 failed`. The version-string change shouldn't break any test because no test pins the exact version (they use `typeof === 'string'`).

- [ ] **Step 4: Commit**

```bash
git add rapidmeta-dose-response-engine-v1.js
git commit -m "feat(dose-response): bump engine to v0.2.0 (Round 2A — continuous-outcome support incoming)"
```

---

### Task 2: validate() pool-level outcome-type dispatch rule

**Files:**
- Modify: `rapidmeta-dose-response-engine-v1.js` (extend `validate()`)
- Modify: `tests/test_dose_response_engine.mjs` (one new test)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_dose_response_engine.mjs` before the runner block:

```javascript
test('validate rejects mixed continuous + binary trials within one pool', () => {
  const mixed = [
    { studlab: 'A_binary', arms: [
      { dose: 0,  events: 10, n: 100, is_reference: true },
      { dose: 5,  events: 15, n: 100, is_reference: false },
    ]},
    { studlab: 'B_continuous', arms: [
      { dose: 0, mean: 0.0, sd: 0.5, n: 50, is_reference: true },
      { dose: 5, mean: -0.4, sd: 0.5, n: 50, is_reference: false },
    ]},
  ];
  const issues = DR.validate(mixed);
  assert.ok(issues.length > 0, 'should flag mixed-mode pool');
  assert.match(issues.join('|'), /mixed outcome types|mixed-mode/i,
    'message should mention mixed outcome types');
});
```

- [ ] **Step 2: Run, expect new test to FAIL**

Run: `node tests/test_dose_response_engine.mjs`
Expected: 37 prior pass + 1 new fail (validate doesn't yet check mixed-mode).

- [ ] **Step 3: Implement the pool-level dispatch rule**

In `rapidmeta-dose-response-engine-v1.js`, find the `validate(trials)` function. At the END of the function body, just before `return issues;`, insert:

```javascript
  // Round 2A: pool-level outcome-type homogeneity check. fitLinear/fitRCS dispatch
  // once on a single outcome type for the whole pool; mixed binary+continuous trials
  // in one fixture would silently mis-pool. validate enforces homogeneity.
  if (trials.length > 0 && issues.length === 0) {
    var seenTypes = {};
    for (var ti = 0; ti < trials.length; ti++) {
      var t = trials[ti];
      if (!Array.isArray(t.arms)) continue;
      for (var ai = 0; ai < t.arms.length; ai++) {
        var a = t.arms[ai];
        if (!a) continue;
        var hasE = isFinite(a.events) && isFinite(a.n);
        var hasC = isFinite(a.mean) && isFinite(a.sd);
        if (hasE) seenTypes['binary'] = true;
        if (hasC) seenTypes['continuous'] = true;
      }
    }
    var typeCount = Object.keys(seenTypes).length;
    if (typeCount > 1) {
      issues.push('mixed outcome types in pool — one fixture = one outcome type');
    }
  }
```

- [ ] **Step 4: Run tests, expect 38/0**

Run: `node tests/test_dose_response_engine.mjs 2>&1 | tail -3`
Expected: `38 passed, 0 failed`.

- [ ] **Step 5: Commit**

```bash
git add rapidmeta-dose-response-engine-v1.js tests/test_dose_response_engine.mjs
git commit -m "feat(dose-response): validate enforces pool-level outcome-type homogeneity (Task 2)"
```

---

### Task 3: `mdCovariance` helper — continuous-mode shared-reference covariance

**Files:**
- Modify: `rapidmeta-dose-response-engine-v1.js` (add helper, expose on `_internal`)
- Modify: `tests/test_dose_response_engine.mjs` (one new test)

- [ ] **Step 1: Write the failing test**

```javascript
test('mdCovariance returns symmetric matrix with shared-reference off-diagonal', () => {
  const arms = [
    { dose: 0,  mean: 0.0,  sd: 0.5, n: 100, is_reference: true },
    { dose: 10, mean: -0.4, sd: 0.6, n: 80,  is_reference: false },
    { dose: 25, mean: -0.5, sd: 0.7, n: 70,  is_reference: false },
  ];
  const S = I.mdCovariance(arms);
  assert.equal(S.length, 2);
  assert.equal(S[0].length, 2);
  // Diagonal: var(mean_i - mean_ref) = sd_i^2/n_i + sd_ref^2/n_ref
  near(S[0][0], (0.6*0.6)/80 + (0.5*0.5)/100, 1e-12, 'var[0]');
  near(S[1][1], (0.7*0.7)/70 + (0.5*0.5)/100, 1e-12, 'var[1]');
  // Off-diagonal: cov from shared reference = sd_ref^2/n_ref
  near(S[0][1], (0.5*0.5)/100, 1e-12, 'cov[0][1]');
  near(S[1][0], S[0][1], 1e-15, 'symmetry');
});
```

- [ ] **Step 2: Run, expect fail (helper not defined)**

- [ ] **Step 3: Implement `mdCovariance`**

Add to Section 2 of the engine (next to the existing `glCovariance`):

```javascript
function mdCovariance(arms) {
  // Continuous-outcome (mean difference) per-trial covariance.
  // Same shared-reference structure as glCovariance: every y_i = mean_i - mean_ref
  // shares the reference arm, so off-diagonal entries are sd_ref^2/n_ref.
  var ref = arms.find(function (a) { return a.is_reference; });
  if (!ref) throw new Error('mdCovariance: no reference arm');
  var contrasts = arms.filter(function (a) { return !a.is_reference; });
  var k = contrasts.length;
  var sdRefSq = ref.sd * ref.sd;
  var nRef = ref.n;
  var shared = sdRefSq / nRef;
  var S = [];
  for (var i = 0; i < k; i++) {
    S.push(new Array(k));
    for (var j = 0; j < k; j++) {
      if (i === j) {
        var c = contrasts[i];
        S[i][j] = (c.sd * c.sd) / c.n + shared;
      } else {
        S[i][j] = shared;
      }
    }
  }
  return S;
}

API._internal.mdCovariance = mdCovariance;
```

- [ ] **Step 4: Run tests, expect 39/0**

- [ ] **Step 5: Commit**

```bash
git add rapidmeta-dose-response-engine-v1.js tests/test_dose_response_engine.mjs
git commit -m "feat(dose-response): mdCovariance helper for continuous-outcome shared-reference covariance (Task 3)"
```

---

### Task 4: `fitLinear` continuous-outcome branch

**Files:**
- Modify: `rapidmeta-dose-response-engine-v1.js` (extend `fitLinear` per-trial loop with mode dispatch)
- Modify: `tests/test_dose_response_engine.mjs` (one new test with a synthetic continuous fixture)

- [ ] **Step 1: Write the failing test**

```javascript
test('fitLinear continuous-mode pools mean differences correctly', () => {
  // Synthetic continuous fixture: 2 trials with monotone dose-response on HbA1c
  const trials = [
    { studlab: 'A', arms: [
      { dose: 0,  mean: 0.0,  sd: 0.5, n: 100, is_reference: true },
      { dose: 10, mean: -0.4, sd: 0.5, n: 100, is_reference: false },
      { dose: 25, mean: -0.6, sd: 0.5, n: 100, is_reference: false },
    ]},
    { studlab: 'B', arms: [
      { dose: 0,  mean: 0.0,  sd: 0.4, n: 120, is_reference: true },
      { dose: 5,  mean: -0.3, sd: 0.4, n: 120, is_reference: false },
      { dose: 20, mean: -0.5, sd: 0.4, n: 120, is_reference: false },
    ]},
  ];
  const res = DR.fitLinear(trials, {});
  assert.equal(res.k, 2);
  // Pooled slope should be negative (dose increase -> mean decrease)
  assert.ok(res.pooled_slope_log < 0, 'continuous slope should be negative for protective effect');
  // PI bounds finite
  assert.ok(isFinite(res.pi_lo) && isFinite(res.pi_hi));
  // estimator label remains 'reml_hksj' (continuous-mode doesn't change pooling)
  assert.equal(res.estimator, 'reml_hksj');
  // Per-study slopes should both be negative
  assert.ok(res.per_study[0].slope_log < 0, 'study A slope negative');
  assert.ok(res.per_study[1].slope_log < 0, 'study B slope negative');
});
```

Note: we reuse the field name `pooled_slope_log` even for continuous outcomes (it's a misnomer for MD-on-identity-scale; the field name stays for backward compatibility and Round 1B HTML re-use). The slope is the per-unit-dose change in mean, not log-RR.

- [ ] **Step 2: Run, expect fail (current `fitLinear` hardcodes `Math.log(pi/p0)`)**

- [ ] **Step 3: Implement continuous dispatch**

In `rapidmeta-dose-response-engine-v1.js`, find `fitLinear(trials, opts)`. After the `validate()` call and before the per-trial loop, add the pool-level outcome-type detection:

```javascript
  // Round 2A: dispatch on outcome type at pool entry. validate() already enforces
  // pool-level homogeneity; safe to infer once from the first non-reference arm.
  var firstTrial = trials[0];
  var firstArm = firstTrial.arms.find(function (a) { return !a.is_reference; });
  var poolOutcomeType = (isFinite(firstArm.mean) && isFinite(firstArm.sd)) ? 'continuous' : 'binary';
```

Then within the per-trial loop, REPLACE the current `var y = ...; var S = glCovariance(T.arms); var Sinv = matInv(S);` block with branched logic:

```javascript
    var y, S;
    if (poolOutcomeType === 'continuous') {
      y = contrasts.map(function (a) { return a.mean - ref.mean; });
      S = mdCovariance(T.arms);
    } else {
      y = contrasts.map(function (a) {
        var pi = a.events / a.n, p0 = ref.events / ref.n;
        return Math.log(pi / p0);
      });
      S = glCovariance(T.arms);
    }
    var Sinv = matInv(S);
```

The rest of the per-trial loop (WLS solve, `xSx`, `xSy`, `beta`, `seBeta`, `perStudy.push`) is unchanged — these operate on the abstract `x`, `y`, `S` regardless of mode.

The `max_observed_dose` computation at the bottom of `fitLinear` is also unchanged.

- [ ] **Step 4: Run tests, expect 40/0**

- [ ] **Step 5: Commit**

```bash
git add rapidmeta-dose-response-engine-v1.js tests/test_dose_response_engine.mjs
git commit -m "feat(dose-response): fitLinear continuous-outcome branch via mdCovariance (Task 4)"
```

---

### Task 5: F-1 zero-cell continuity correction in `fitLinear` (binary branch)

**Files:**
- Modify: `rapidmeta-dose-response-engine-v1.js` (binary branch of `fitLinear`'s per-trial loop)
- Modify: `tests/test_dose_response_engine.mjs` (two new tests)

- [ ] **Step 1: Write the failing tests**

```javascript
test('fitLinear binary with zero-event arm applies F-1 correction and returns finite', () => {
  // Synthetic: 2 trials, one has a zero-event arm at low dose (would produce log(0/p) = -Inf)
  const trials = [
    { studlab: 'A_normal', arms: [
      { dose: 0,  events: 5,  n: 100, is_reference: true },
      { dose: 10, events: 12, n: 100, is_reference: false },
      { dose: 25, events: 20, n: 100, is_reference: false },
    ]},
    { studlab: 'B_zerocell', arms: [
      { dose: 0,  events: 0,  n: 80,  is_reference: true },   // zero in ref
      { dose: 10, events: 3,  n: 80,  is_reference: false },
      { dose: 25, events: 8,  n: 80,  is_reference: false },
    ]},
  ];
  const res = DR.fitLinear(trials, {});
  assert.ok(isFinite(res.pooled_slope_log),
    'pooled_slope_log must be finite after F-1 correction');
  assert.ok(isFinite(res.per_study[1].slope_log),
    'study B per-study slope must be finite (F-1 applied to its arms)');
  // Per-study A (no zero cells) must produce identical output to a call without
  // F-1 having been triggered — i.e. unchanged. We verify by computing the slope
  // on study A alone and comparing.
  const aAlone = DR.fitLinear([trials[0], {
    // synthetic 2nd trial identical to A so k=2 (avoid k<2 guard)
    studlab: 'A_dup', arms: trials[0].arms,
  }], {});
  // A's slope from the 2-trial pool above should equal aAlone's per-study slope
  near(res.per_study[0].slope_log, aAlone.per_study[0].slope_log, 1e-12,
    'F-1 must NOT touch trials with no zero cells (study A unchanged)');
});

test('fitLinear binary without zero cells preserves identity output (F-1 inactive)', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitLinear(fx.trials, {});
  // GL-1992 has no zero-event arms; F-1 should not fire. Re-run and compare
  // against the existing parity test target (pooled_slope_log * 11 ≈ 0.254).
  near(res.pooled_slope_log * 11, 0.254, 0.015, 'GL-1992 result unchanged by F-1 inactivity');
});
```

- [ ] **Step 2: Run, expect the new "zero-event arm" test to FAIL (current engine produces NaN)**

- [ ] **Step 3: Implement F-1 in the binary branch**

In `rapidmeta-dose-response-engine-v1.js`, find the binary branch of `fitLinear` (the `} else { y = contrasts.map(...)` block). Replace the `y = contrasts.map(...)` line with the F-1-aware version:

```javascript
    } else {
      // F-1 zero-cell continuity correction (advanced-stats.md): add 0.5 to events
      // and 1.0 to n in BOTH ref and contrast arms ONLY when >=1 cell is zero in
      // this trial. Unconditional correction biases OR -> 1; conditional is the
      // consensus correction.
      var hasZeroCell = (ref.events === 0) ||
        contrasts.some(function (a) { return a.events === 0; });
      var refE, refN;
      if (hasZeroCell) {
        refE = ref.events + 0.5;
        refN = ref.n + 1.0;
      } else {
        refE = ref.events;
        refN = ref.n;
      }
      y = contrasts.map(function (a) {
        var aE = hasZeroCell ? a.events + 0.5 : a.events;
        var aN = hasZeroCell ? a.n + 1.0 : a.n;
        var pi = aE / aN, p0 = refE / refN;
        return Math.log(pi / p0);
      });
      // glCovariance needs the (potentially) corrected events/n too; pass a shallow
      // clone of arms with the corrected fields.
      if (hasZeroCell) {
        var armsCorr = T.arms.map(function (a) {
          if (a.is_reference) return { events: a.events + 0.5, n: a.n + 1.0, is_reference: true };
          return { events: a.events + 0.5, n: a.n + 1.0, is_reference: false };
        });
        S = glCovariance(armsCorr);
      } else {
        S = glCovariance(T.arms);
      }
    }
```

Note: `glCovariance` reads `events` and `n` directly from the arms; we pass the corrected versions when F-1 fires.

- [ ] **Step 4: Run tests, expect 42/0**

Run: `node tests/test_dose_response_engine.mjs 2>&1 | tail -3`
Expected: `42 passed, 0 failed`.

- [ ] **Step 5: Commit**

```bash
git add rapidmeta-dose-response-engine-v1.js tests/test_dose_response_engine.mjs
git commit -m "feat(dose-response): F-1 conditional zero-cell continuity correction in fitLinear (Task 5)"
```

---

### Task 6: `fitRCS` continuous-outcome branch + F-1

**Files:**
- Modify: `rapidmeta-dose-response-engine-v1.js` (extend `fitRCS` per-trial loop with same dispatch)
- Modify: `tests/test_dose_response_engine.mjs` (one new test)

- [ ] **Step 1: Write the failing test**

```javascript
test('fitRCS continuous-mode pools spline coefs on a 4-trial synthetic fixture', () => {
  const trials = [
    { studlab: 'T1', arms: [
      { dose: 0,  mean: 0.0,  sd: 0.5, n: 100, is_reference: true },
      { dose: 5,  mean: -0.3, sd: 0.5, n: 100, is_reference: false },
      { dose: 25, mean: -0.6, sd: 0.5, n: 100, is_reference: false },
    ]},
    { studlab: 'T2', arms: [
      { dose: 0,  mean: 0.0,  sd: 0.4, n: 120, is_reference: true },
      { dose: 10, mean: -0.4, sd: 0.4, n: 120, is_reference: false },
      { dose: 50, mean: -0.7, sd: 0.4, n: 120, is_reference: false },
    ]},
    { studlab: 'T3', arms: [
      { dose: 0,  mean: 0.0,  sd: 0.6, n: 80,  is_reference: true },
      { dose: 2.5,mean: -0.2, sd: 0.6, n: 80,  is_reference: false },
      { dose: 20, mean: -0.5, sd: 0.6, n: 80,  is_reference: false },
    ]},
    { studlab: 'T4', arms: [
      { dose: 0,  mean: 0.0,  sd: 0.5, n: 90,  is_reference: true },
      { dose: 15, mean: -0.45,sd: 0.5, n: 90,  is_reference: false },
      { dose: 40, mean: -0.65,sd: 0.5, n: 90,  is_reference: false },
    ]},
  ];
  const res = DR.fitRCS(trials, { knots: 3 });
  assert.equal(res.layer, 'rcs');
  assert.equal(res.rcs.knots.length, 3);
  assert.equal(res.rcs.spline_coefs.length, 2);
  assert.ok(isFinite(res.rcs.nonlinearity_wald_p));
  assert.ok(res.rcs.spline_coefs[0] < 0, 'linear-component coef should be negative');
});
```

- [ ] **Step 2: Run, expect fail.**

- [ ] **Step 3: Implement the dispatch in `fitRCS`**

In `rapidmeta-dose-response-engine-v1.js`, find `fitRCS(trials, opts)`. Apply the SAME pool-level dispatch as Task 4 and the SAME F-1 logic as Task 5. Specifically:

After `validate(trials)` and the k<2 guard, before the knot computation:

```javascript
  var firstTrial = trials[0];
  var firstArm = firstTrial.arms.find(function (a) { return !a.is_reference; });
  var poolOutcomeType = (isFinite(firstArm.mean) && isFinite(firstArm.sd)) ? 'continuous' : 'binary';
```

Within the per-trial loop, REPLACE the current `var y = ...; var S = glCovariance(T.arms);` block with:

```javascript
    var y, S;
    if (poolOutcomeType === 'continuous') {
      y = contrasts.map(function (a) { return a.mean - ref.mean; });
      S = mdCovariance(T.arms);
    } else {
      var hasZeroCell = (ref.events === 0) ||
        contrasts.some(function (a) { return a.events === 0; });
      var refE, refN;
      if (hasZeroCell) {
        refE = ref.events + 0.5;
        refN = ref.n + 1.0;
      } else {
        refE = ref.events;
        refN = ref.n;
      }
      y = contrasts.map(function (a) {
        var aE = hasZeroCell ? a.events + 0.5 : a.events;
        var aN = hasZeroCell ? a.n + 1.0 : a.n;
        var pi = aE / aN, p0 = refE / refN;
        return Math.log(pi / p0);
      });
      if (hasZeroCell) {
        var armsCorr = T.arms.map(function (a) {
          if (a.is_reference) return { events: a.events + 0.5, n: a.n + 1.0, is_reference: true };
          return { events: a.events + 0.5, n: a.n + 1.0, is_reference: false };
        });
        S = glCovariance(armsCorr);
      } else {
        S = glCovariance(T.arms);
      }
    }
```

The rest of the per-trial loop in `fitRCS` (basis-matrix construction via `rcsBasis`, WLS solve, V_i inversion) is unchanged. It operates on the abstract `y` and `S`.

- [ ] **Step 4: Run tests, expect 43/0**

- [ ] **Step 5: Commit**

```bash
git add rapidmeta-dose-response-engine-v1.js tests/test_dose_response_engine.mjs
git commit -m "feat(dose-response): fitRCS continuous-mode + F-1 zero-cell correction (Task 6)"
```

---

### Task 7: Group-A close — verify all engine extensions interoperate

**Files:** None (verification only)

- [ ] **Step 1: Run the full engine test suite**

Run: `node tests/test_dose_response_engine.mjs 2>&1 | tail -3`
Expected: `43 passed, 0 failed`.

- [ ] **Step 2: Spot-check GL-1992 still works (binary regression guard)**

Run the existing GL-1992 parity test alone via a Node one-liner:

```bash
cd C:/Projects/Finrenone/.claude/worktrees/<wt>/ && node -e "
const fs = require('fs');
const ctx = {};
new Function('window', fs.readFileSync('rapidmeta-dose-response-engine-v1.js','utf8'))(ctx);
const fx = JSON.parse(fs.readFileSync('tests/dose_response_fixtures/gl1992_alcohol_bc.json','utf8'));
const r = ctx.RapidMetaDoseResp.fitLinear(fx.trials, {});
console.log('GL-1992 pooled_slope_log*11:', (r.pooled_slope_log*11).toFixed(4));
console.log('expected ~0.254');
console.log('within tol:', Math.abs(r.pooled_slope_log*11 - 0.254) < 0.015);
"
```

Expected: prints `~0.254` and `within tol: true`. If false, the binary path regressed — STOP and report.

- [ ] **Step 3: No commit (verification only).**

Group A closes here. Engine v0.2.0 is ready to consume continuous and binary fixtures.

---

## Group B — R script continuous-mode dispatch (Task 8)

### Task 8: `r_validate_doseresp.R` — add continuous (`type="md"`) dispatch

**Files:**
- Modify: `scripts/r_validate_doseresp.R` (auto-detect input fixture's outcome type; dispatch to MD or IR mode)

- [ ] **Step 1: Verify `lme4` is still loadable** (already a dep from Round 1B):

```bash
"C:/Program Files/R/R-4.5.2/bin/Rscript.exe" -e "library(lme4); cat(as.character(packageVersion('lme4')))"
```

Expected: prints a version like `1.1-37`. If missing, install:

```bash
"C:/Program Files/R/R-4.5.2/bin/Rscript.exe" -e "install.packages('lme4', repos='https://cloud.r-project.org')"
```

- [ ] **Step 2: Modify the R script**

Open `scripts/r_validate_doseresp.R`. Find the section near the top where the input JSON is read and the data frame is flattened. The current script assumes binary (events + n). Add outcome-type detection right after the data frame is built:

```r
# Round 2A: detect outcome type from first non-reference arm of first trial.
# All arms in a single fixture must agree (validate enforces this on the JS side).
first_trial <- trials[[1]]
first_arm <- NULL
for (a in first_trial$arms) {
  if (!isTRUE(a$is_reference)) { first_arm <- a; break }
}
is_continuous <- !is.null(first_arm) &&
                 !is.null(first_arm$mean) && !is.null(first_arm$sd) &&
                 is.null(first_arm$events)
cat(sprintf("Round 2A outcome dispatch: %s\n", if (is_continuous) "continuous (md)" else "binary (ir)"))
```

Then in the per-trial data-frame construction loop, populate the appropriate columns based on type:

```r
rows <- list()
for (t in trials) {
  for (a in t$arms) {
    rows[[length(rows) + 1]] <- if (is_continuous) {
      data.frame(
        studlab = t$studlab,
        dose = a$dose,
        mean = a$mean,
        sd = a$sd,
        n = a$n,
        is_reference = isTRUE(a$is_reference),
        stringsAsFactors = FALSE
      )
    } else {
      data.frame(
        studlab = t$studlab,
        dose = a$dose,
        events = a$events,
        n = a$n,
        is_reference = isTRUE(a$is_reference),
        stringsAsFactors = FALSE
      )
    }
  }
}
df <- do.call(rbind, rows)
```

Then branch the fitter calls:

```r
# Linear pool
if (is_continuous) {
  fit_lin <- tryCatch(
    dosresmeta(formula = mean ~ dose, type = "md", sd = sd, n = n,
               data = df, id = studlab, method = "reml"),
    error = function(e) structure(list(),
                                  class = "fitError",
                                  .error_msg = conditionMessage(e))
  )
} else {
  fit_lin <- tryCatch(
    dosresmeta(formula = logrr ~ dose, type = "ir",
               cases = events, n = n,
               data = df, id = studlab, method = "reml"),
    error = function(e) structure(list(),
                                  class = "fitError",
                                  .error_msg = conditionMessage(e))
  )
}
```

Same dispatch for `fit_rcs` (RCS branch — use `mean ~ rcs(dose, knots)` with `type="md"` when continuous).

Same dispatch for one-stage `fit_os`:

```r
if (is_continuous) {
  # Weighted lmer: weights = 1/(sd^2 / n) gives the inverse-variance weight per arm
  df$.w <- 1 / ((df$sd * df$sd) / df$n)
  # Dose rescaling for convergence (Round 1B precedent)
  dose_sd_pos <- sd(df$dose[df$dose > 0])
  df$dose_scaled <- df$dose / dose_sd_pos
  fit_os <- tryCatch(
    lmer(mean ~ dose_scaled + (1 | studlab), data = df, weights = df$.w,
         REML = TRUE,
         control = lmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e5))),
    error = function(e) structure(list(),
                                  class = "fitError",
                                  .error_msg = conditionMessage(e))
  )
  # Back-transform coef and se
  if (!is.null(fit_os) && !inherits(fit_os, "fitError")) {
    coef_sc <- as.numeric(fixef(fit_os)["dose_scaled"])
    se_sc <- as.numeric(sqrt(diag(vcov(fit_os))["dose_scaled"]))
    coef_orig <- coef_sc / dose_sd_pos
    se_orig <- se_sc / dose_sd_pos
    # Replace the existing one_stage_block builder to use these orig values
    # (the binary path's existing builder reads fixef("dose"); the continuous path
    # reads dose_scaled and back-transforms identically to Round 1B's glmer pattern)
  }
} else {
  # Existing binary path: glmer with offset(log(n)), dose scaling as before.
  # (Leave the existing block untouched.)
}
```

The output JSON shape is the same for both modes (`linear`, `rcs`, `one_stage` blocks). For continuous mode:
- `linear.pooled_slope_log` field is reused but represents the MD per unit dose (not log-RR).
- `rcs.spline_coefs` same shape.
- `one_stage.coef_dose` = back-transformed MD per unit dose.
- `coef_dose_on_scaled` + `dose_scale_sd` audit-trail fields preserved.

- [ ] **Step 3: Smoke-test on the existing GL-1992 binary fixture (must not break the binary path)**

```bash
cd /c/Projects/Finrenone/.claude/worktrees/<wt>/ && python scripts/r_validate_doseresp.py --review gl1992_alcohol_bc 2>&1 | tail -3
```

Expected: `gl1992_alcohol_bc: OK — linear=True, rcs=True`. The continuous-dispatch logic must take the `else` branch for this fixture.

- [ ] **Step 4: Commit**

```bash
git add scripts/r_validate_doseresp.R
git commit -m "feat(dose-response): R script continuous-mode dispatch via type='md' (Task 8)"
```

Note: a continuous-mode smoke test happens after Group C lands the new fixtures.

---

## Group C — Fixtures + R precompute (Tasks 9-11)

### Task 9: `tests/dose_response_fixtures/sglt2i_hba1c.json` — primary outcome fixture

**Files:**
- Create: `tests/dose_response_fixtures/sglt2i_hba1c.json`
- Modify: `tests/test_dose_response_engine.mjs` (one fixture-load test)

This fixture pools 4 SGLT2i trials' HbA1c change-from-baseline at the per-arm level. Three trials' values are well-established in the literature; SOLOIST-WHF reported HbA1c as a secondary outcome in supplementary materials.

**Trial data — sources and values:**

- **Wilding 2009** (PMID 19196325, *Diabetes Obes Metab*): 12-week Phase 2 dose-ranging trial of dapagliflozin. HbA1c change from baseline (Table 2 of the primary publication). Six arms.
- **EMPA-REG OUTCOME** (PMID 26378978, *N Engl J Med*): HbA1c change at 12 weeks (Figure 2 of the primary publication; pre-specified secondary endpoint). Three arms.
- **CANVAS Program** (PMID 28605608, *N Engl J Med*): HbA1c change pooled across CANVAS + CANVAS-R (primary endpoint of secondary outcomes set; reported in Supplement Table S6). Three arms.
- **SOLOIST-WHF** (PMID 33196306, *N Engl J Med*): primary endpoint was CV events; HbA1c change reported in Supplement Table S5. Three arms.

The data sourcing for SOLOIST-WHF requires the supplementary appendix. If extraction is blocked (e.g., paywall, no supplement access), the implementer should DROP SOLOIST-WHF from the HbA1c fixture and proceed with k=3 (Wilding + EMPA-REG + CANVAS) — annotate the omission in the fixture's top-level metadata. The plan accepts k=3 as a valid fallback.

- [ ] **Step 1: Look up Wilding 2009 values via PubMed MCP**

Use the available PubMed MCP tool to fetch the abstract and any available structured data:

Tool call: `mcp__claude_ai_PubMed__get_article_metadata` with PMID `19196325`. Confirm title, authors, year, journal.

Tool call: `mcp__claude_ai_PubMed__get_full_text_article` with PMID `19196325` if available. Extract Table 2 HbA1c change-from-baseline per arm. Expected approximate values (verify against returned data):
- Placebo: HbA1c change ≈ -0.18% (n≈54)
- Dapagliflozin 2.5 mg: ≈ -0.42% (n≈58)
- Dapagliflozin 5 mg: ≈ -0.55% (n≈58)
- Dapagliflozin 10 mg: ≈ -0.55% (n≈47)
- Dapagliflozin 20 mg: ≈ -0.56% (n≈59)
- Dapagliflozin 50 mg: ≈ -0.66% (n≈58)

SDs of the change are not always reported directly; if only SEM or 95% CI is given, back-compute SD = SEM × √n or SD = (CI_hi − CI_lo) × √n / 3.92. If only "mean (SE)" is given in the table, use `SD = SE × √n` per arm.

If the PubMed MCP can only return the abstract (not the full text), USE THE ABSTRACT VALUES and add `"data_source": "abstract — verify against published Table 2"` to the fixture's per-trial metadata. The implementer should note this gap in the commit message.

- [ ] **Step 2: Look up EMPA-REG values via PubMed MCP**

Tool: `mcp__claude_ai_PubMed__get_full_text_article` with PMID `26378978`. Extract Figure 2 / Supplement Table values:
- Placebo: HbA1c change ≈ -0.08% baseline-adjusted, n≈2,333
- Empagliflozin 10 mg: ≈ -0.54%, n≈2,345
- Empagliflozin 25 mg: ≈ -0.60%, n≈2,342

The full-text article will report these with the corresponding SDs/SEs. If the MCP returns only the abstract, mark `"data_source": "abstract"` per-arm and proceed.

- [ ] **Step 3: Look up CANVAS values via PubMed MCP**

Tool: `mcp__claude_ai_PubMed__get_full_text_article` with PMID `28605608`. Extract HbA1c change values:
- Placebo: ≈ -0.07%, n≈4,347 (pooled CANVAS + CANVAS-R placebo arms)
- Canagliflozin 100 mg: ≈ -0.58%, n≈2,886
- Canagliflozin 300 mg: ≈ -0.62%, n≈2,887

- [ ] **Step 4: Look up SOLOIST-WHF values via PubMed MCP**

Tool: `mcp__claude_ai_PubMed__get_full_text_article` with PMID `33196306`. HbA1c is a secondary outcome reported in Supplement Table S5 of SOLOIST-WHF. If extraction succeeds, three arms:
- Placebo: HbA1c change (extract value), n≈614
- Sotagliflozin 200 mg: HbA1c change (extract value), n≈308
- Sotagliflozin 400 mg: HbA1c change (extract value), n≈304

If extraction fails (no full text, no supplement access), **DROP SOLOIST-WHF from this fixture** and proceed with k=3.

- [ ] **Step 5: Compose the fixture JSON**

Create `tests/dose_response_fixtures/sglt2i_hba1c.json` with this exact shape (substitute extracted values for `MEAN_*`, `SD_*`, `N_*` placeholders):

```json
{
  "fixture_name": "sglt2i_hba1c",
  "source": "Pooled SGLT2i dose-response on HbA1c change from baseline; 4 trials (or 3 if SOLOIST-WHF supplement unavailable)",
  "outcome": "hba1c_change_from_baseline_percent",
  "outcome_type": "continuous",
  "dose_unit": "mg_per_day",
  "dose_assignment_method": "as-randomized per-trial dose; raw mg across 4 SGLT2i drugs",
  "class_equivalence_caveat": "Raw mg doses are not pharmacologically equivalent across drugs (empa, dapa, cana, sota). Cross-drug pooling assumes equipotent dose-response on the per-mg scale; methodologically debatable. See HTML methods disclosure.",
  "trials": [
    {
      "studlab": "Wilding 2009 (dapagliflozin Phase 2)",
      "pmid": "19196325",
      "drug": "dapagliflozin",
      "arms": [
        { "dose": 0,    "mean": MEAN_W0,  "sd": SD_W0,  "n": N_W0,  "is_reference": true },
        { "dose": 2.5,  "mean": MEAN_W2_5,"sd": SD_W2_5,"n": N_W2_5,"is_reference": false },
        { "dose": 5,    "mean": MEAN_W5,  "sd": SD_W5,  "n": N_W5,  "is_reference": false },
        { "dose": 10,   "mean": MEAN_W10, "sd": SD_W10, "n": N_W10, "is_reference": false },
        { "dose": 20,   "mean": MEAN_W20, "sd": SD_W20, "n": N_W20, "is_reference": false },
        { "dose": 50,   "mean": MEAN_W50, "sd": SD_W50, "n": N_W50, "is_reference": false }
      ]
    },
    {
      "studlab": "EMPA-REG OUTCOME 2015 (empagliflozin)",
      "pmid": "26378978",
      "drug": "empagliflozin",
      "arms": [
        { "dose": 0,  "mean": MEAN_E0,  "sd": SD_E0,  "n": N_E0,  "is_reference": true },
        { "dose": 10, "mean": MEAN_E10, "sd": SD_E10, "n": N_E10, "is_reference": false },
        { "dose": 25, "mean": MEAN_E25, "sd": SD_E25, "n": N_E25, "is_reference": false }
      ]
    },
    {
      "studlab": "CANVAS Program 2017 (canagliflozin)",
      "pmid": "28605608",
      "drug": "canagliflozin",
      "arms": [
        { "dose": 0,   "mean": MEAN_C0,   "sd": SD_C0,   "n": N_C0,   "is_reference": true },
        { "dose": 100, "mean": MEAN_C100, "sd": SD_C100, "n": N_C100, "is_reference": false },
        { "dose": 300, "mean": MEAN_C300, "sd": SD_C300, "n": N_C300, "is_reference": false }
      ]
    },
    {
      "studlab": "SOLOIST-WHF 2021 (sotagliflozin)",
      "pmid": "33196306",
      "drug": "sotagliflozin",
      "arms": [
        { "dose": 0,   "mean": MEAN_S0,   "sd": SD_S0,   "n": N_S0,   "is_reference": true },
        { "dose": 200, "mean": MEAN_S200, "sd": SD_S200, "n": N_S200, "is_reference": false },
        { "dose": 400, "mean": MEAN_S400, "sd": SD_S400, "n": N_S400, "is_reference": false }
      ]
    }
  ]
}
```

If SOLOIST-WHF is dropped per Step 4, OMIT its trial object entirely from the `trials` array.

- [ ] **Step 6: Add a fixture-load test**

Append to `tests/test_dose_response_engine.mjs`:

```javascript
test('sglt2i_hba1c fixture loads with 3-4 trials and continuous arms', () => {
  const fx = loadFx('sglt2i_hba1c.json');
  assert.ok(fx.trials.length === 3 || fx.trials.length === 4,
    'fixture should have 3 or 4 trials (4 if SOLOIST-WHF HbA1c was extractable)');
  assert.equal(fx.outcome_type, 'continuous');
  for (const t of fx.trials) {
    const refs = t.arms.filter(a => a.is_reference);
    assert.equal(refs.length, 1, `${t.studlab} needs exactly 1 reference arm`);
    for (const a of t.arms) {
      assert.ok(Number.isFinite(a.dose) && a.dose >= 0, `${t.studlab} arm dose must be finite >= 0`);
      assert.ok(Number.isFinite(a.mean), `${t.studlab} arm mean must be finite (continuous fixture)`);
      assert.ok(Number.isFinite(a.sd) && a.sd > 0, `${t.studlab} arm sd must be positive`);
      assert.ok(Number.isFinite(a.n) && a.n > 0, `${t.studlab} arm n must be positive`);
    }
  }
});
```

- [ ] **Step 7: Run tests, expect 44/0**

```bash
node tests/test_dose_response_engine.mjs 2>&1 | tail -3
```

- [ ] **Step 8: Commit**

```bash
git add tests/dose_response_fixtures/sglt2i_hba1c.json tests/test_dose_response_engine.mjs
git commit -m "test(dose-response): SGLT2i HbA1c continuous fixture (Wilding+EMPA-REG+CANVAS{+SOLOIST}) (Task 9)"
```

---

### Task 10: `tests/dose_response_fixtures/sglt2i_hhf.json` — secondary outcome fixture

**Files:**
- Create: `tests/dose_response_fixtures/sglt2i_hhf.json`
- Modify: `tests/test_dose_response_engine.mjs` (one fixture-load test + one F-1 trigger test)

hHF event counts per arm from EMPA-REG, CANVAS, SOLOIST-WHF primary publications. SOLOIST-WHF was a HF-population trial with hHF as part of the primary composite — event counts ARE reported in the primary publication's Table 2.

- [ ] **Step 1: Look up hHF event counts**

Use PubMed MCP for each PMID. Extract from primary publication tables:
- **EMPA-REG OUTCOME** (PMID 26378978): hHF events per arm (placebo, empa 10 mg, empa 25 mg)
- **CANVAS Program** (PMID 28605608): hHF events per arm (placebo, cana 100 mg, cana 300 mg)
- **SOLOIST-WHF** (PMID 33196306): hHF events per arm (placebo, sota 200 mg, sota 400 mg). SOLOIST is a HF-population trial — hHF events are dense and well-reported. The placebo arm has events; lower-dose arms may have 0 events in some strata (depends on follow-up time), which triggers F-1.

If SOLOIST low-dose arm has 0 events for hHF (which is the expected F-1 trigger), encode it as `"events": 0` in the fixture — do NOT pre-apply +0.5 here. F-1 fires inside the engine.

- [ ] **Step 2: Compose the fixture JSON**

```json
{
  "fixture_name": "sglt2i_hhf",
  "source": "Pooled SGLT2i dose-response on hospitalization for heart failure; 3 trials with within-trial multi-dose data",
  "outcome": "hospitalization_for_heart_failure",
  "outcome_type": "binary",
  "dose_unit": "mg_per_day",
  "dose_assignment_method": "as-randomized per-trial dose; raw mg across 3 SGLT2i drugs",
  "class_equivalence_caveat": "See sglt2i_hba1c.json — same caveat applies.",
  "f1_trigger_note": "SOLOIST-WHF low-dose arm may have 0 hHF events — engine F-1 conditional +0.5 correction will fire for that trial.",
  "trials": [
    {
      "studlab": "EMPA-REG OUTCOME 2015 (empagliflozin)",
      "pmid": "26378978",
      "drug": "empagliflozin",
      "arms": [
        { "dose": 0,  "events": EVT_E0,  "n": N_E0,  "is_reference": true },
        { "dose": 10, "events": EVT_E10, "n": N_E10, "is_reference": false },
        { "dose": 25, "events": EVT_E25, "n": N_E25, "is_reference": false }
      ]
    },
    {
      "studlab": "CANVAS Program 2017 (canagliflozin)",
      "pmid": "28605608",
      "drug": "canagliflozin",
      "arms": [
        { "dose": 0,   "events": EVT_C0,   "n": N_C0,   "is_reference": true },
        { "dose": 100, "events": EVT_C100, "n": N_C100, "is_reference": false },
        { "dose": 300, "events": EVT_C300, "n": N_C300, "is_reference": false }
      ]
    },
    {
      "studlab": "SOLOIST-WHF 2021 (sotagliflozin)",
      "pmid": "33196306",
      "drug": "sotagliflozin",
      "arms": [
        { "dose": 0,   "events": EVT_S0,   "n": N_S0,   "is_reference": true },
        { "dose": 200, "events": EVT_S200, "n": N_S200, "is_reference": false },
        { "dose": 400, "events": EVT_S400, "n": N_S400, "is_reference": false }
      ]
    }
  ]
}
```

- [ ] **Step 3: Add fixture-load test**

Append to `tests/test_dose_response_engine.mjs`:

```javascript
test('sglt2i_hhf fixture loads with 3 trials and binary arms', () => {
  const fx = loadFx('sglt2i_hhf.json');
  assert.equal(fx.trials.length, 3, 'sglt2i_hhf has 3 trials');
  assert.equal(fx.outcome_type, 'binary');
  for (const t of fx.trials) {
    const refs = t.arms.filter(a => a.is_reference);
    assert.equal(refs.length, 1);
    for (const a of t.arms) {
      assert.ok(Number.isFinite(a.events) && a.events >= 0, `${t.studlab} arm events finite >= 0`);
      assert.ok(Number.isFinite(a.n) && a.n > 0);
    }
  }
});

test('fitLinear handles sglt2i_hhf — produces finite output (F-1 may fire on zero-event arms)', () => {
  const fx = loadFx('sglt2i_hhf.json');
  const res = DR.fitLinear(fx.trials, {});
  assert.ok(isFinite(res.pooled_slope_log), 'pooled_slope_log must be finite');
  assert.ok(isFinite(res.tau2));
  assert.equal(res.k, 3);
  assert.equal(res.coverage_warning, true, 'k=3 < 10 triggers coverage warning');
});
```

- [ ] **Step 4: Run tests, expect 46/0**

- [ ] **Step 5: Commit**

```bash
git add tests/dose_response_fixtures/sglt2i_hhf.json tests/test_dose_response_engine.mjs
git commit -m "test(dose-response): SGLT2i hHF binary fixture (Task 10)"
```

---

### Task 11: R precompute on both new fixtures

**Files:**
- Create (by R-script side effect): `outputs/r_validation/doseresp/sglt2i_hba1c.json`
- Create (by R-script side effect): `outputs/r_validation/doseresp/sglt2i_hhf.json`

- [ ] **Step 1: Run the Python wrapper on the HbA1c fixture**

```bash
cd /c/Projects/Finrenone/.claude/worktrees/<wt>/ && python scripts/r_validate_doseresp.py --review sglt2i_hba1c 2>&1 | tail -3
```

Expected: `sglt2i_hba1c: OK — linear=True, rcs=True` plus an additional line for one-stage success if visible.

Inspect the output:

```bash
python -c "
import json
d = json.load(open('outputs/r_validation/doseresp/sglt2i_hba1c.json'))
print('linear.fit_ok:', d.get('linear', {}).get('fit_ok'))
print('linear.pooled_slope_log:', d.get('linear', {}).get('pooled_slope_log'))
print('rcs.fit_ok:', d.get('rcs', {}).get('fit_ok'))
print('one_stage.fit_ok:', d.get('one_stage', {}).get('fit_ok'))
print('one_stage.converged:', d.get('one_stage', {}).get('converged'))
"
```

Expected:
- `linear.fit_ok: True`
- `linear.pooled_slope_log` is a small negative number (mean reduction in HbA1c per mg dose; should be ~-0.005 to -0.02 depending on extraction)
- `rcs.fit_ok: True`
- `one_stage.fit_ok: True`, `converged: True`

If `linear.pooled_slope_log` is positive (i.e. dose increases HbA1c, which would be wrong direction), STOP — likely a sign error in the fixture extraction (someone wrote +0.55 instead of -0.55).

- [ ] **Step 2: Run the Python wrapper on the hHF fixture**

```bash
python scripts/r_validate_doseresp.py --review sglt2i_hhf 2>&1 | tail -3
```

Expected: `sglt2i_hhf: OK — linear=True, rcs=True`. Binary mode (existing path) handles the zero-event arms — note that R's `dosresmeta` may or may not apply its own continuity correction; that's a separate question from the engine's F-1.

Inspect the output:

```bash
python -c "
import json
d = json.load(open('outputs/r_validation/doseresp/sglt2i_hhf.json'))
print('linear.pooled_slope_log:', d.get('linear', {}).get('pooled_slope_log'))
print('rcs.nonlinearity_wald_p:', d.get('rcs', {}).get('nonlinearity_wald_p'))
print('one_stage.coef_dose:', d.get('one_stage', {}).get('coef_dose'))
print('one_stage.converged:', d.get('one_stage', {}).get('converged'))
"
```

- [ ] **Step 3: Commit both JSON outputs + their .input.json siblings**

The `.input.json` files are gitignored per the Round 1B convention (`outputs/r_validation/**/*.input.json` in `.gitignore`). Only commit the actual `.json` outputs.

```bash
git add outputs/r_validation/doseresp/sglt2i_hba1c.json outputs/r_validation/doseresp/sglt2i_hhf.json
git commit -m "data(dose-response): R precompute outputs for SGLT2i HbA1c + hHF fixtures (Task 11)"
```

Group C closes. The engine, R script, fixtures, and R-precomputed outputs all interoperate.

---

## Group D — Flagship HTML (Tasks 12-17)

**Reference:** `ALCOHOL_BC_DOSE_RESP_REVIEW.html` (Round 1B final state at commit `82f5ce53`). The SGLT2i flagship reuses the entire `<style>` block, the `showTab()` + arrow-key navigation, ARIA tab semantics, `<main>` landmark, `aria-live` regions, CSP meta, focus-visible rings, captions, table-scroll wrappers, plain-English summary, and Round 1B's audit-cleanup ergonomics. Implementer should START by copying ALCOHOL_BC_DOSE_RESP_REVIEW.html as a template, then mutate the topic-specific content.

### Task 12: HTML scaffold (5 tabs, empty content, header furniture)

**Files:**
- Create: `SGLT2I_DOSE_RESP_REVIEW.html`

- [ ] **Step 1: Copy the Round 1B flagship as a template**

```bash
cd /c/Projects/Finrenone/.claude/worktrees/<wt>/ && cp ALCOHOL_BC_DOSE_RESP_REVIEW.html SGLT2I_DOSE_RESP_REVIEW.html
```

- [ ] **Step 2: Mutate the topic-specific content**

In the new file, change:

1. `<title>` from "Alcohol intake and breast cancer..." to "SGLT2 inhibitor dose vs HbA1c and hospitalization for heart failure — pooled dose-response meta-analysis"

2. `<meta name="description">` content to: "Pooled dose-response re-analysis of 4 SGLT2i trials (EMPA-REG OUTCOME, CANVAS, SOLOIST-WHF, Wilding 2009 dose-ranging). Primary outcome HbA1c (continuous); secondary hHF (binary). Class-equivalence assumption documented."

3. `<h1>` and subtitle: replace alcohol-BC text with SGLT2i text. Subtitle should link the 4 PMIDs (19196325, 26378978, 28605608, 33196306).

4. **Methodology disclosure (`<details>` block)** — replace the alcohol-BC methods text with this SGLT2i-specific content:

```html
<details>
  <summary>Methods (click to expand)</summary>
  <p>This review pools 4 SGLT2 inhibitor trials with within-trial multi-dose data:</p>
  <ol>
    <li><strong>EMPA-REG OUTCOME 2015</strong> (Zinman et al., <em>NEJM</em>): empagliflozin 10 mg vs 25 mg vs placebo; CV-outcomes trial in T2DM with CV disease.</li>
    <li><strong>CANVAS Program 2017</strong> (Neal et al., <em>NEJM</em>): canagliflozin 100 mg vs 300 mg vs placebo; pooled CANVAS + CANVAS-R analysis.</li>
    <li><strong>SOLOIST-WHF 2021</strong> (Bhatt et al., <em>NEJM</em>): sotagliflozin 200 mg vs 400 mg vs placebo; recently-hospitalized HF patients.</li>
    <li><strong>Wilding 2009</strong> (<em>Diabetes Obes Metab</em>): dapagliflozin 2.5/5/10/20/50 mg vs placebo; 12-week Phase 2 dose-ranging.</li>
  </ol>
  <p><strong>Class-equivalence caveat:</strong> Doses are pooled at the raw mg scale across 4 different drugs (empagliflozin, canagliflozin, sotagliflozin, dapagliflozin). The dose axis is therefore drug-dependent; 10 mg means very different things across drugs. The pool implicitly assumes equipotent dose-response on the per-mg scale, which is methodologically debatable. A %-of-max-dose harmonization or per-drug separate analysis would each be defensible alternatives; this flagship chose raw mg for pedagogical simplicity and to match the engine's input shape.</p>
  <p><strong>Limited evidence base:</strong> SGLT2i CVOTs are overwhelmingly single-dose. Only 4 trials contribute within-trial multi-dose data here. k = 3-4 (HbA1c) and k = 3 (hHF) trigger the engine's <code>coverage_warning</code>.</p>
  <p><strong>Statistical methods</strong> match the engine v0.2.0 conventions: two-stage Greenland-Longnecker linear pool with REML+HKSJ (HKSJ floor <code>max(1, Q/(k-1))</code>); restricted cubic splines with Harrell-default knots; Wald non-linearity test under diagonal-PM v0.1 (engine non-linearity p will diverge from R full-REML — see R-parity tab); one-stage hierarchical Poisson (hHF, binary, lme4::glmer) and weighted-linear (HbA1c, continuous, lme4::lmer) computed by R and surfaced from precomputed JSON. PI uses <em>t<sub>k-1</sub></em> df (Cochrane Handbook v6.5).</p>
  <p><strong>Continuous-outcome support:</strong> Engine v0.2.0 adds a continuous-outcome branch in <code>fitLinear</code>/<code>fitRCS</code> using a per-trial covariance matrix that mirrors the binary GL shared-reference structure (off-diagonal = sd<sub>ref</sub><sup>2</sup>/n<sub>ref</sub>; diagonal = sd<sub>i</sub><sup>2</sup>/n<sub>i</sub> + sd<sub>ref</sub><sup>2</sup>/n<sub>ref</sub>). Validated against R <code>dosresmeta(type="md")</code> in the R-parity badge tab.</p>
  <p><strong>F-1 zero-cell continuity correction:</strong> Engine v0.2.0 conditionally adds 0.5 to events and 1.0 to n in BOTH reference and contrast arms ONLY when ≥1 cell is zero (per <em>advanced-stats.md</em>: unconditional correction biases OR→1). Triggered on the hHF tab for SOLOIST-WHF's low-dose arm if it has 0 events.</p>
</details>
```

5. **Per-study trial summary** — leave the structure (collapsible `<details><div id="trial-summary"></div></details>`) but the JS that populates it will be replaced in subsequent tasks (Tasks 13/16) since SGLT2i has TWO fixtures (HbA1c and hHF) and the table needs to display data from both.

6. **Tab navigation** — change the 4 tabs to 5 and update labels:

```html
<nav class="tab-nav" role="tablist" aria-label="Analysis tabs">
  <button id="tab-btn-hba1c-linear" data-tab="hba1c-linear" class="active" role="tab" aria-selected="true" aria-controls="tab-hba1c-linear" tabindex="0" onclick="showTab('hba1c-linear')">1. HbA1c — Linear</button>
  <button id="tab-btn-hba1c-rcs" data-tab="hba1c-rcs" role="tab" aria-selected="false" aria-controls="tab-hba1c-rcs" tabindex="-1" onclick="showTab('hba1c-rcs')">2. HbA1c — RCS</button>
  <button id="tab-btn-hba1c-os" data-tab="hba1c-os" role="tab" aria-selected="false" aria-controls="tab-hba1c-os" tabindex="-1" onclick="showTab('hba1c-os')">3. HbA1c — One-stage</button>
  <button id="tab-btn-hhf" data-tab="hhf" role="tab" aria-selected="false" aria-controls="tab-hhf" tabindex="-1" onclick="showTab('hhf')">4. hHF — secondary</button>
  <button id="tab-btn-parity" data-tab="parity" role="tab" aria-selected="false" aria-controls="tab-parity" tabindex="-1" onclick="showTab('parity')">5. R-parity badge</button>
</nav>
```

7. **Tab content sections** — replace the 4 Round 1B sections with 5 new ones, all with empty placeholder divs (filled in subsequent tasks):

```html
<section id="tab-hba1c-linear" class="tab-content active" role="tabpanel" tabindex="0" aria-labelledby="tab-btn-hba1c-linear">
  <h2 tabindex="-1">HbA1c — Linear pool (two-stage GL, continuous outcome)</h2>
  <div id="hba1c-linear-kpis" aria-live="polite" aria-atomic="true"></div>
  <div id="hba1c-linear-forest"></div>
  <div id="hba1c-linear-curve"></div>
  <div id="hba1c-linear-summary"></div>
</section>

<section id="tab-hba1c-rcs" class="tab-content" role="tabpanel" tabindex="0" aria-labelledby="tab-btn-hba1c-rcs">
  <h2 tabindex="-1">HbA1c — RCS (3 knots, diagonal-PM v0.1)</h2>
  <div id="hba1c-rcs-kpis"></div>
  <div id="hba1c-rcs-curve"></div>
  <div id="hba1c-rcs-forest"></div>
  <div id="hba1c-rcs-wald"></div>
</section>

<section id="tab-hba1c-os" class="tab-content" role="tabpanel" tabindex="0" aria-labelledby="tab-btn-hba1c-os">
  <h2 tabindex="-1">HbA1c — One-stage hierarchical (R-precomputed lmer)</h2>
  <div id="hba1c-os-kpis" aria-live="polite" aria-atomic="true"></div>
  <div id="hba1c-os-methods"></div>
</section>

<section id="tab-hhf" class="tab-content" role="tabpanel" tabindex="0" aria-labelledby="tab-btn-hhf">
  <h2 tabindex="-1">hospitalization for heart failure — secondary (binary, F-1-exercise)</h2>
  <div id="hhf-kpis" aria-live="polite" aria-atomic="true"></div>
  <div id="hhf-f1-badge"></div>
  <div id="hhf-forest"></div>
  <div id="hhf-summary"></div>
</section>

<section id="tab-parity" class="tab-content" role="tabpanel" tabindex="0" aria-labelledby="tab-btn-parity">
  <h2 tabindex="-1">R-parity badges (engine vs R)</h2>
  <h3>HbA1c (continuous)</h3>
  <div id="r-parity-doseresp-hba1c" aria-live="polite" aria-atomic="true"></div>
  <h3>hHF (binary)</h3>
  <div id="r-parity-doseresp-hhf" aria-live="polite" aria-atomic="true"></div>
</section>
```

8. **Embedded trial JSON** — DELETE the existing `<script type="application/json" id="doseresp-trials">...gl1992 data...</script>` block. The SGLT2i flagship needs TWO JSON blocks (one per outcome). Replace with:

```html
<script type="application/json" id="doseresp-trials-hba1c">
[]
</script>
<script type="application/json" id="doseresp-trials-hhf">
[]
</script>
```

The `[]` content is populated in Tasks 13 and 16.

9. **Inline `<script>` block at the bottom** — the existing `showTab()` + `DOMContentLoaded` logic must be heavily revised. Strip the existing DOMContentLoaded body and leave a minimal stub:

```javascript
window.addEventListener('DOMContentLoaded', function () {
  if (!window.RapidMetaDoseResp || typeof window.RapidMetaDoseResp.engine_version !== 'string') {
    document.body.innerHTML = '<div style="color:#c00; padding:1em;"><strong>Engine failed to load.</strong> Check the browser console for errors.</div>';
    return;
  }
  // Tabs populated in subsequent tasks (13, 14, 15, 16, 17).
});
```

Keep the `showTab()` function and the arrow-key keydown handler from Round 1B intact (just update the button selectors to use the new tab IDs).

10. **Footer** — update citations to list the 4 SGLT2i trial PMIDs.

- [ ] **Step 3: Static-check the scaffold**

```bash
cd /c/Projects/Finrenone/.claude/worktrees/<wt>/ && python -c "
with open('SGLT2I_DOSE_RESP_REVIEW.html') as f: html = f.read()
checks = [
  ('<meta name=\"viewport\"', 'viewport'),
  ('Content-Security-Policy', 'CSP'),
  ('<main>', 'main landmark'),
  ('role=\"tablist\"', 'ARIA tablist'),
  ('aria-label=\"Analysis tabs\"', 'nav aria-label'),
  ('id=\"tab-hba1c-linear\"', 'tab section 1'),
  ('id=\"tab-hba1c-rcs\"', 'tab section 2'),
  ('id=\"tab-hba1c-os\"', 'tab section 3'),
  ('id=\"tab-hhf\"', 'tab section 4'),
  ('id=\"tab-parity\"', 'tab section 5'),
  ('id=\"doseresp-trials-hba1c\"', 'HbA1c JSON block'),
  ('id=\"doseresp-trials-hhf\"', 'hHF JSON block'),
  ('id=\"r-parity-doseresp-hba1c\"', 'HbA1c parity mount'),
  ('id=\"r-parity-doseresp-hhf\"', 'hHF parity mount'),
  ('class-equivalence', 'class-equivalence caveat'),
  ('keydown', 'arrow-key handler'),
]
missing = [name for kw, name in checks if kw not in html]
print('missing:', missing if missing else 'none')
print('button count:', html.count('data-tab='))
print('section count:', html.count('class=\"tab-content'))
"
```

Expected: `missing: none`, `button count: 5`, `section count: 5`.

- [ ] **Step 4: Commit**

```bash
git add SGLT2I_DOSE_RESP_REVIEW.html
git commit -m "feat(dose-response): scaffold SGLT2I_DOSE_RESP_REVIEW.html (5 tabs, ARIA, dual JSON blocks) (Task 12)"
```

---

### Task 13: Tab 1 — HbA1c Linear + embed HbA1c trial data

**Files:**
- Modify: `SGLT2I_DOSE_RESP_REVIEW.html`

- [ ] **Step 1: Embed HbA1c trial data**

Replace the empty `<script type="application/json" id="doseresp-trials-hba1c">[]</script>` with the contents of `tests/dose_response_fixtures/sglt2i_hba1c.json`'s `trials` array (paste the JSON array).

- [ ] **Step 2: Wire DOMContentLoaded for Tab 1**

Inside the `DOMContentLoaded` handler (between the engine-load guard and the `// Tabs populated...` comment), add:

```javascript
  var DR = window.RapidMetaDoseResp;

  // Read HbA1c trials
  var hba1cScript = document.getElementById('doseresp-trials-hba1c');
  var hba1cTrials;
  try {
    hba1cTrials = JSON.parse(hba1cScript.textContent);
  } catch (e) {
    document.getElementById('hba1c-linear-kpis').textContent = 'HbA1c trial data malformed: ' + e.message;
    return;
  }
  if (hba1cTrials.length === 0) {
    document.getElementById('hba1c-linear-kpis').textContent = 'No HbA1c trial data embedded.';
    return;
  }

  // Per-study trial summary (combine HbA1c + hHF arms; trial-summary populated in Task 16
  // when hHF trials are also embedded).

  // === Tab 1: HbA1c Linear ===
  var hba1cLin = DR.fitLinear(hba1cTrials, {});
  // Note: pooled_slope_log here is MD-per-mg-dose (continuous mode), not log-RR.
  var mdPer10mg = hba1cLin.pooled_slope_log * 10;
  var mdPer10mg_lo = hba1cLin.pooled_slope_log_ci_lo * 10;
  var mdPer10mg_hi = hba1cLin.pooled_slope_log_ci_hi * 10;

  document.getElementById('hba1c-linear-kpis').innerHTML =
    '<div class="kpi-grid">' +
    '<div class="kpi"><div class="kpi-label">HbA1c change per 10 mg dose</div><div class="kpi-value">' + mdPer10mg.toFixed(3) + '%</div><div>95% CI ' + mdPer10mg_lo.toFixed(3) + ' to ' + mdPer10mg_hi.toFixed(3) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">MD per mg dose</div><div class="kpi-value">' + hba1cLin.pooled_slope_log.toFixed(5) + '</div><div>SE ' + hba1cLin.pooled_slope_log_se.toFixed(5) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">τ²</div><div class="kpi-value">' + hba1cLin.tau2.toExponential(2) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">I²</div><div class="kpi-value">' + hba1cLin.I2.toFixed(1) + '%</div><div>Q = ' + hba1cLin.Q.toFixed(2) + ' (df ' + hba1cLin.Q_df + ')</div></div>' +
    '<div class="kpi"><div class="kpi-label">PI (per 10 mg, df=' + hba1cLin.pi_df + ')</div><div class="kpi-value">' + (hba1cLin.pi_lo*10).toFixed(3) + ' to ' + (hba1cLin.pi_hi*10).toFixed(3) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">k</div><div class="kpi-value">' + hba1cLin.k + '</div>' + (hba1cLin.coverage_warning ? '<div style="color:#92400e">coverage warning: k&lt;10</div>' : '') + '</div>' +
    '</div>';

  // Per-study forest
  var hba1cForestRows = DR.forest(hba1cTrials, hba1cLin);
  var hba1cFHtml = '<h3>Per-study forest (HbA1c, linear layer, RE-weighted)</h3><div class="table-scroll"><table><caption>Per-study HbA1c MD per mg dose with 95% CI</caption><thead><tr><th>Study</th><th>MD per mg</th><th>95% CI</th><th>Weight</th></tr></thead><tbody>';
  hba1cForestRows.forEach(function (r) {
    // For continuous mode, forest returns slope_log = MD per mg (no exp transform needed)
    hba1cFHtml += '<tr><td>' + r.label + '</td>' +
                  '<td>' + r.slope_log.toFixed(5) + '</td>' +
                  '<td>' + (r.slope_log - 1.96 * r.slope_log_se).toFixed(5) + ' to ' + (r.slope_log + 1.96 * r.slope_log_se).toFixed(5) + '</td>' +
                  '<td>' + r.weight_pct.toFixed(1) + '%</td></tr>';
  });
  hba1cFHtml += '</tbody></table></div>';
  document.getElementById('hba1c-linear-forest').innerHTML = hba1cFHtml;

  // Dose-response curve (20-point grid, 0 to max observed dose)
  var maxObs = hba1cLin.max_observed_dose;
  var hba1cCurveHtml = '<h3>Dose-response curve (95% CI via t<sub>' + hba1cLin.pi_df + '</sub>)</h3><div class="table-scroll"><table><caption>HbA1c MD per arm dose, 20-point grid 0 to ' + maxObs + ' mg</caption><thead><tr><th>Dose (mg)</th><th>MD (%)</th><th>95% CI</th></tr></thead><tbody>';
  for (var i = 0; i < 20; i++) {
    var d = i * maxObs / 19;
    var p = DR.predict(hba1cLin, d);
    hba1cCurveHtml += '<tr><td>' + d.toFixed(2) + '</td>' +
                     '<td>' + p.est.toFixed(4) + '</td>' +
                     '<td>' + p.ci_lo.toFixed(4) + ' to ' + p.ci_hi.toFixed(4) + '</td></tr>';
  }
  hba1cCurveHtml += '</tbody></table></div>';
  document.getElementById('hba1c-linear-curve').innerHTML = hba1cCurveHtml;

  // Plain-English summary
  document.getElementById('hba1c-linear-summary').innerHTML =
    '<p><strong>Plain-English summary:</strong> Each additional 10 mg of SGLT2 inhibitor (raw mg across 4 drugs at the pooled-class scale) is associated with a HbA1c reduction of approximately ' + Math.abs(mdPer10mg).toFixed(2) + ' percentage points (95% CI ' + Math.abs(mdPer10mg_hi).toFixed(2) + ' to ' + Math.abs(mdPer10mg_lo).toFixed(2) + '). The estimate combines 4 trials across 4 different SGLT2i drugs at the raw-mg dose scale; see Methods for the class-equivalence caveat.</p>' +
    '<p style="margin-top:0.6em; font-size:0.92em; color:#444;"><strong>Caveat:</strong> The raw-mg cross-drug pool assumes equipotent per-mg effects, which is methodologically debatable. Per-drug analyses or %-of-max-dose harmonization would be defensible alternatives.</p>';
```

- [ ] **Step 3: Static check + browser smoke (Node-side simulation)**

```bash
cd /c/Projects/Finrenone/.claude/worktrees/<wt>/ && node -e "
const fs = require('fs');
const ctx = {};
new Function('window', fs.readFileSync('rapidmeta-dose-response-engine-v1.js','utf8'))(ctx);
const html = fs.readFileSync('SGLT2I_DOSE_RESP_REVIEW.html','utf8');
const m = html.match(/<script type=\"application\\/json\" id=\"doseresp-trials-hba1c\">([\\s\\S]*?)<\\/script>/);
const trials = JSON.parse(m[1].trim());
console.log('trials embedded:', trials.length);
const res = ctx.RapidMetaDoseResp.fitLinear(trials, {});
console.log('pooled_slope_log:', res.pooled_slope_log.toFixed(5));
console.log('per 10 mg:', (res.pooled_slope_log * 10).toFixed(3));
console.log('coverage_warning:', res.coverage_warning);
console.log('k:', res.k);
"
```

Expected: `trials embedded: 3` or `4`, `pooled_slope_log` is a small negative number, `coverage_warning: true`, `k: 3` or `4`.

If `pooled_slope_log` is positive, the fixture has sign-error and the curve will show the wrong direction.

- [ ] **Step 4: Commit**

```bash
git add SGLT2I_DOSE_RESP_REVIEW.html
git commit -m "feat(dose-response): populate Tab 1 HbA1c Linear + embed HbA1c fixture (Task 13)"
```

---

### Task 14: Tab 2 — HbA1c RCS

**Files:**
- Modify: `SGLT2I_DOSE_RESP_REVIEW.html`

- [ ] **Step 1: Add Tab-2 wiring**

After the Tab 1 block inside `DOMContentLoaded`, add:

```javascript
  // === Tab 2: HbA1c RCS ===
  var hba1cRcs = DR.fitRCS(hba1cTrials, { knots: 3 });

  document.getElementById('hba1c-rcs-kpis').innerHTML =
    '<div class="kpi-grid">' +
    '<div class="kpi"><div class="kpi-label">Knots (mg)</div><div class="kpi-value">' + hba1cRcs.rcs.knots.map(function (k) { return k.toFixed(1); }).join(', ') + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">spline_coefs[0] (linear)</div><div class="kpi-value">' + hba1cRcs.rcs.spline_coefs[0].toFixed(5) + '</div><div>SE ' + hba1cRcs.rcs.spline_coefs_se[0].toFixed(5) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">spline_coefs[1] (non-linear)</div><div class="kpi-value">' + hba1cRcs.rcs.spline_coefs[1].toFixed(5) + '</div><div>SE ' + hba1cRcs.rcs.spline_coefs_se[1].toFixed(5) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">Wald non-linearity p</div><div class="kpi-value">' + hba1cRcs.rcs.nonlinearity_wald_p.toFixed(4) + '</div><div>(diagonal-PM v0.1)</div></div>' +
    '<div class="kpi"><div class="kpi-label">τ² per dim</div><div class="kpi-value">[' + hba1cRcs.rcs.tau2_per_dim.map(function (t) { return t.toExponential(2); }).join(', ') + ']</div></div>' +
    '</div>';

  // RCS curve via fit_at_dose grid
  var rcsCurveHtml = '<h3>RCS dose-response curve (HbA1c)</h3><div class="table-scroll"><table><caption>RCS dose-response curve via 20-point fit_at_dose grid</caption><thead><tr><th>Dose (mg)</th><th>MD (%)</th><th>95% CI</th></tr></thead><tbody>';
  hba1cRcs.rcs.fit_at_dose.forEach(function (p) {
    rcsCurveHtml += '<tr><td>' + p.dose.toFixed(2) + '</td>' +
                    '<td>' + p.est.toFixed(4) + '</td>' +
                    '<td>' + p.ci_lo.toFixed(4) + ' to ' + p.ci_hi.toFixed(4) + '</td></tr>';
  });
  rcsCurveHtml += '</tbody></table></div>';
  document.getElementById('hba1c-rcs-curve').innerHTML = rcsCurveHtml;

  // RCS per-study forest (F-3 RE-weighted via tau2_per_dim[0])
  var rcsForestRows = DR.forest(hba1cTrials, hba1cRcs);
  var rfHtml = '<h3>Per-study forest (RCS linear-component, RE-weighted)</h3><div class="table-scroll"><table><caption>Per-study HbA1c MD per mg (linear-component slope), RE-weighted via tau2_per_dim[0]</caption><thead><tr><th>Study</th><th>MD per mg</th><th>95% CI</th><th>RE weight</th></tr></thead><tbody>';
  rcsForestRows.forEach(function (r) {
    rfHtml += '<tr><td>' + r.label + '</td>' +
              '<td>' + r.slope_log.toFixed(5) + '</td>' +
              '<td>' + (r.slope_log - 1.96 * r.slope_log_se).toFixed(5) + ' to ' + (r.slope_log + 1.96 * r.slope_log_se).toFixed(5) + '</td>' +
              '<td>' + r.weight_pct.toFixed(1) + '%</td></tr>';
  });
  rfHtml += '</tbody></table></div>';
  document.getElementById('hba1c-rcs-forest').innerHTML = rfHtml;

  // Wald note (amber)
  document.getElementById('hba1c-rcs-wald').innerHTML =
    '<div class="rv-badge rv-badge-amber">' +
    '<strong>Wald non-linearity test (diagonal-PM v0.1):</strong> p = ' + hba1cRcs.rcs.nonlinearity_wald_p.toFixed(4) +
    ' (df = ' + (hba1cRcs.rcs.spline_coefs.length - 1) + '). ' +
    'Under the v0.1 diagonal-PM-per-dimension τ² approximation, the engine\'s non-linearity p will differ ' +
    'from R full multivariate REML. See the R-parity tab for the side-by-side comparison. P2 hardening (Round 2B) ' +
    'will lift to full multivariate REML and close this gap.</div>';
```

- [ ] **Step 2: Browser smoke (static check + Node)**

```bash
node -e "
const fs = require('fs');
const ctx = {};
new Function('window', fs.readFileSync('rapidmeta-dose-response-engine-v1.js','utf8'))(ctx);
const html = fs.readFileSync('SGLT2I_DOSE_RESP_REVIEW.html','utf8');
const m = html.match(/<script type=\"application\\/json\" id=\"doseresp-trials-hba1c\">([\\s\\S]*?)<\\/script>/);
const trials = JSON.parse(m[1].trim());
const r = ctx.RapidMetaDoseResp.fitRCS(trials, {knots:3});
console.log('knots:', r.rcs.knots.map(k => k.toFixed(2)).join(', '));
console.log('wald p:', r.rcs.nonlinearity_wald_p.toFixed(4));
console.log('fit_at_dose len:', r.rcs.fit_at_dose.length);
"
```

Expected: 3 knot values, wald p in [0,1], fit_at_dose length 20.

- [ ] **Step 3: Commit**

```bash
git add SGLT2I_DOSE_RESP_REVIEW.html
git commit -m "feat(dose-response): populate Tab 2 HbA1c RCS (Task 14)"
```

---

### Task 15: Tab 3 — HbA1c One-stage (R-precomputed display)

**Files:**
- Modify: `SGLT2I_DOSE_RESP_REVIEW.html`

- [ ] **Step 1: Add fetch + Tab 3 wiring**

Append (still inside `DOMContentLoaded`):

```javascript
  // Load R-precomputed JSON for HbA1c (Tabs 3 + 5a) and hHF (Tabs 4-secondary + 5b).
  Promise.all([
    fetch('outputs/r_validation/doseresp/sglt2i_hba1c.json').then(function (r) {
      if (!r.ok) throw new Error('HbA1c R JSON: HTTP ' + r.status);
      return r.json();
    }),
    fetch('outputs/r_validation/doseresp/sglt2i_hhf.json').then(function (r) {
      if (!r.ok) throw new Error('hHF R JSON: HTTP ' + r.status);
      return r.json();
    })
  ]).then(function (results) {
    var rHba1c = results[0];
    var rHhf = results[1];

    // === Tab 3: HbA1c One-stage ===
    var hba1cOs = DR.fitOneStage(hba1cTrials, {}, rHba1c);
    if (!hba1cOs || !hba1cOs.one_stage || hba1cOs.one_stage.fit_ok === false) {
      document.getElementById('hba1c-os-kpis').innerHTML =
        '<div class="rv-banner rv-banner-error">One-stage R output unavailable. Run <code>python scripts/r_validate_doseresp.py --review sglt2i_hba1c</code> to populate.</div>';
    } else {
      var os = hba1cOs.one_stage;
      var osMd10 = os.coef_dose * 10;
      document.getElementById('hba1c-os-kpis').innerHTML =
        '<div class="kpi-grid">' +
        '<div class="kpi"><div class="kpi-label">MD per 10 mg dose (one-stage)</div><div class="kpi-value">' + osMd10.toFixed(3) + '%</div><div>95% CI ' + (os.coef_dose_ci_lo*10).toFixed(3) + ' to ' + (os.coef_dose_ci_hi*10).toFixed(3) + '</div></div>' +
        '<div class="kpi"><div class="kpi-label">coef_dose (per mg)</div><div class="kpi-value">' + os.coef_dose.toFixed(5) + '</div><div>SE ' + os.coef_dose_se.toFixed(5) + '</div></div>' +
        '<div class="kpi"><div class="kpi-label">Random-effects variance</div><div class="kpi-value">' + (os.random_effects_var != null ? os.random_effects_var.toFixed(5) : 'n/a') + '</div></div>' +
        '<div class="kpi"><div class="kpi-label">Converged</div><div class="kpi-value">' + (os.converged ? 'Yes' : 'No') + '</div></div>' +
        '<div class="kpi"><div class="kpi-label">Solver</div><div class="kpi-value">lme4 ' + (os.lme4_version || rHba1c.one_stage.lme4_version || 'unknown') + '</div></div>' +
        (os.dose_scale_sd != null ? '<div class="kpi"><div class="kpi-label">dose_scale_sd (audit)</div><div class="kpi-value">' + os.dose_scale_sd.toFixed(3) + '</div></div>' : '') +
        '</div>';
      document.getElementById('hba1c-os-methods').innerHTML =
        '<p><strong>Methodology:</strong> One-stage hierarchical model fit by R using <code>lme4::lmer(mean ~ dose + (1 | studlab), data = df, weights = 1/(sd^2/n), REML = TRUE)</code> with the bobyqa optimizer. Per-arm HbA1c change modelled on the original scale; per-arm precision weights (inverse-variance) reflect within-arm sampling uncertainty. Random study intercept captures between-study baseline-HbA1c variation. Dose rescaling by <code>sd(dose[dose > 0])</code> for convergence; coefficient back-transformed to per-mg scale.</p>' +
        '<p style="margin-top:0.6em; font-size:0.92em;"><strong>Why this differs from Tab 1:</strong> The one-stage estimate (MD per 10 mg) differs from the two-stage linear pool because the random study intercept absorbs between-study variation in baseline HbA1c, shifting the fixed-effect dose slope. Neither is wrong; they answer subtly different questions about the dose-response relationship.</p>';
    }

    // Tabs 4 + 5 populated in Tasks 16/17 — continue the chain
    // (placeholder: see Task 16's wiring for the hHF block)
  }).catch(function (e) {
    console.error('[SGLT2I] failed to load R JSON:', e);
    document.getElementById('hba1c-os-kpis').textContent = 'One-stage tab unavailable: ' + e.message;
    document.getElementById('r-parity-doseresp-hba1c').textContent = 'HbA1c R-parity unavailable: ' + e.message;
    document.getElementById('r-parity-doseresp-hhf').textContent = 'hHF R-parity unavailable: ' + e.message;
  });
```

- [ ] **Step 2: HTTP-server smoke** (file:// blocks fetch)

```bash
cd /c/Projects/Finrenone/.claude/worktrees/<wt>/ && python -m http.server 8765 &
sleep 1
curl -fsS http://localhost:8765/SGLT2I_DOSE_RESP_REVIEW.html -o /dev/null && echo "page reachable: YES"
curl -fsS http://localhost:8765/outputs/r_validation/doseresp/sglt2i_hba1c.json | head -c 200
kill %1
```

- [ ] **Step 3: Commit**

```bash
git add SGLT2I_DOSE_RESP_REVIEW.html
git commit -m "feat(dose-response): populate Tab 3 HbA1c One-stage via fetch (Task 15)"
```

---

### Task 16: Tab 4 — hHF secondary + embed hHF trial data

**Files:**
- Modify: `SGLT2I_DOSE_RESP_REVIEW.html`

- [ ] **Step 1: Embed hHF trial data**

Replace the empty `<script type="application/json" id="doseresp-trials-hhf">[]</script>` with `tests/dose_response_fixtures/sglt2i_hhf.json`'s `trials` array.

- [ ] **Step 2: Add Tab 4 wiring** — inside the `Promise.all().then` callback (right after the Tab 3 block), add:

```javascript
    // Read hHF trials
    var hhfScript = document.getElementById('doseresp-trials-hhf');
    var hhfTrials;
    try {
      hhfTrials = JSON.parse(hhfScript.textContent);
    } catch (e) {
      document.getElementById('hhf-kpis').textContent = 'hHF trial data malformed: ' + e.message;
      return;
    }

    // === Tab 4: hHF secondary (binary, k=3) ===
    var hhfLin = DR.fitLinear(hhfTrials, {});

    // Detect whether F-1 fired on any trial (zero-event arm)
    var f1Triggered = hhfTrials.some(function (t) {
      var ref = t.arms.find(function (a) { return a.is_reference; });
      return (ref && ref.events === 0) || t.arms.some(function (a) { return !a.is_reference && a.events === 0; });
    });

    var hhfRR10 = Math.exp(hhfLin.pooled_slope_log * 10);
    var hhfRR10_lo = Math.exp(hhfLin.pooled_slope_log_ci_lo * 10);
    var hhfRR10_hi = Math.exp(hhfLin.pooled_slope_log_ci_hi * 10);

    document.getElementById('hhf-kpis').innerHTML =
      '<div class="kpi-grid">' +
      '<div class="kpi"><div class="kpi-label">RR per 10 mg dose</div><div class="kpi-value">' + hhfRR10.toFixed(3) + '</div><div>95% CI ' + hhfRR10_lo.toFixed(3) + ' to ' + hhfRR10_hi.toFixed(3) + '</div></div>' +
      '<div class="kpi"><div class="kpi-label">log-RR per mg</div><div class="kpi-value">' + hhfLin.pooled_slope_log.toFixed(5) + '</div><div>SE ' + hhfLin.pooled_slope_log_se.toFixed(5) + '</div></div>' +
      '<div class="kpi"><div class="kpi-label">τ²</div><div class="kpi-value">' + hhfLin.tau2.toExponential(2) + '</div></div>' +
      '<div class="kpi"><div class="kpi-label">I²</div><div class="kpi-value">' + hhfLin.I2.toFixed(1) + '%</div></div>' +
      '<div class="kpi"><div class="kpi-label">k</div><div class="kpi-value">' + hhfLin.k + '</div>' + (hhfLin.coverage_warning ? '<div style="color:#92400e">coverage warning: k&lt;10</div>' : '') + '</div>' +
      '</div>';

    document.getElementById('hhf-f1-badge').innerHTML = f1Triggered ?
      '<div class="rv-badge rv-badge-amber"><strong>F-1 zero-cell continuity correction:</strong> at least one trial has a zero-event arm; the engine applied +0.5 to events and +1.0 to n in BOTH reference and contrast arms of the affected trial(s). This is the conditional correction (only fires when ≥1 cell is zero) per advanced-stats.md. Without this correction the affected trial would produce log(0/p) = -Infinity and the pool would silently return NaN.</div>' :
      '<div class="rv-badge rv-badge-green"><strong>F-1 not triggered:</strong> all trials have ≥1 event in every arm. F-1 conditional correction is wired but inactive on this dataset.</div>';

    var hhfForestRows = DR.forest(hhfTrials, hhfLin);
    var hhfFHtml = '<h3>Per-study forest (hHF, linear layer, RE-weighted)</h3><div class="table-scroll"><table><caption>Per-study hHF RR per mg dose with 95% CI</caption><thead><tr><th>Study</th><th>RR per mg</th><th>95% CI</th><th>Weight</th></tr></thead><tbody>';
    hhfForestRows.forEach(function (r) {
      hhfFHtml += '<tr><td>' + r.label + '</td>' +
                  '<td>' + r.hr.toFixed(4) + '</td>' +
                  '<td>' + r.hr_ci_lo.toFixed(4) + ' to ' + r.hr_ci_hi.toFixed(4) + '</td>' +
                  '<td>' + r.weight_pct.toFixed(1) + '%</td></tr>';
    });
    hhfFHtml += '</tbody></table></div>';
    document.getElementById('hhf-forest').innerHTML = hhfFHtml;

    document.getElementById('hhf-summary').innerHTML =
      '<p><strong>Plain-English summary:</strong> Across the 3 SGLT2i trials with within-trial multi-dose hHF data, each additional 10 mg of drug is associated with a relative-risk of ' + hhfRR10.toFixed(3) + ' for hHF (95% CI ' + hhfRR10_lo.toFixed(3) + ' to ' + hhfRR10_hi.toFixed(3) + '). The estimate combines empagliflozin, canagliflozin, and sotagliflozin at the raw-mg dose scale — same class-equivalence caveat as the HbA1c tab. k=3 < 10 triggers coverage warning.</p>';
```

- [ ] **Step 3: Browser smoke**

Same HTTP-server pattern as Task 15. Click Tab 4; verify F-1 badge shows correct state; verify k=3 + coverage warning fires; verify forest renders 3 rows summing to ~100%.

- [ ] **Step 4: Commit**

```bash
git add SGLT2I_DOSE_RESP_REVIEW.html
git commit -m "feat(dose-response): populate Tab 4 hHF secondary + embed hHF fixture + F-1 badge visibility (Task 16)"
```

---

### Task 17: Tab 5 — Two R-parity badges (HbA1c + hHF)

**Files:**
- Modify: `SGLT2I_DOSE_RESP_REVIEW.html`

- [ ] **Step 1: Add the two badge mounts** — inside the same `Promise.all().then` callback (after Tab 4 block):

```javascript
    // === Tab 5: R-parity badges ===
    window.RValidationDoseresp.render('r-parity-doseresp-hba1c',
      { linear: hba1cLin, rcs: hba1cRcs, one_stage: hba1cOs },
      rHba1c);
    window.RValidationDoseresp.render('r-parity-doseresp-hhf',
      { linear: hhfLin, one_stage: DR.fitOneStage(hhfTrials, {}, rHhf) },
      rHhf);
```

The badge JS from Round 1B handles the case where some result fields are missing (it returns "n/a" via `fmt()`). For hHF we only have linear (no RCS — could add but we didn't compute it in Tab 4); the badge will gracefully degrade.

OPTIONAL extension: if you want hHF RCS in the parity badge, compute `var hhfRcs = DR.fitRCS(hhfTrials, {knots: 3});` after `hhfLin` in Task 16 (k=3 is borderline for 3-knot RCS — may degenerate). Skip for v0.1 simplicity.

- [ ] **Step 2: Per-study trial summary** — now that both fixtures are loaded, populate the trial-summary div from Task 12. Add after the engine-load guard and before the Tab 1 block:

```javascript
  // Per-study trial summary: combine HbA1c + hHF trials, de-duplicate by studlab + pmid
  var allTrials = {};
  hba1cTrials.forEach(function (t) {
    allTrials[t.pmid] = { studlab: t.studlab, pmid: t.pmid, drug: t.drug, hba1c_arms: t.arms.length, hhf_arms: 0 };
  });
  // hhfTrials is loaded inside the fetch().then; we'll populate the trial-summary
  // table from inside the .then() callback after both fixtures are read.
```

Actually, since `hhfTrials` is loaded after the fetch, move the trial-summary HTML build INSIDE the `.then()` callback, after `hhfTrials` is parsed:

```javascript
    // Populate trial-summary table (uses both HbA1c and hHF fixtures)
    var summary = '<div class="table-scroll"><table><caption>Per-study summary across HbA1c + hHF outcomes</caption><thead><tr><th>Study</th><th>Drug</th><th>PMID</th><th>HbA1c arms</th><th>hHF arms</th></tr></thead><tbody>';
    var pmidSet = {};
    hba1cTrials.forEach(function (t) { pmidSet[t.pmid] = { studlab: t.studlab, drug: t.drug, hba1c: t.arms.length, hhf: 0 }; });
    hhfTrials.forEach(function (t) {
      if (pmidSet[t.pmid]) { pmidSet[t.pmid].hhf = t.arms.length; }
      else { pmidSet[t.pmid] = { studlab: t.studlab, drug: t.drug, hba1c: 0, hhf: t.arms.length }; }
    });
    Object.keys(pmidSet).forEach(function (pmid) {
      var s = pmidSet[pmid];
      summary += '<tr><td>' + s.studlab + '</td>' +
                 '<td>' + s.drug + '</td>' +
                 '<td><a href="https://pubmed.ncbi.nlm.nih.gov/' + pmid + '/" target="_blank" rel="noopener noreferrer">' + pmid + '</a></td>' +
                 '<td>' + s.hba1c + '</td>' +
                 '<td>' + s.hhf + '</td></tr>';
    });
    summary += '</tbody></table></div>';
    document.getElementById('trial-summary').innerHTML = summary;
```

- [ ] **Step 3: Final HTTP-server smoke — verify all 5 tabs render**

```bash
cd /c/Projects/Finrenone/.claude/worktrees/<wt>/ && python -m http.server 8765 &
sleep 1
curl -fsS http://localhost:8765/SGLT2I_DOSE_RESP_REVIEW.html -o /tmp/page.html && echo "page OK"
kill %1
```

The implementer should also (if interactive) open the page in a browser via http://localhost:8765/SGLT2I_DOSE_RESP_REVIEW.html, click through all 5 tabs, and verify no console errors. From a non-interactive subagent context, the static check + Node simulations from prior tasks are sufficient.

- [ ] **Step 4: Commit**

```bash
git add SGLT2I_DOSE_RESP_REVIEW.html
git commit -m "feat(dose-response): populate Tab 5 R-parity (2 mounts) + trial-summary table (Task 17)"
```

Group D closes — all 5 tabs wired.

---

## Group E — Pre-push gates + close (Tasks 18-19)

### Task 18: AACT cross-check on SGLT2i trials

**Files:** None (verification only); may produce `outputs/` audit artifacts depending on script.

The canonical Finrenone gate per `feedback_aact_cross_check_gate.md`: before pushing a review HTML, run AACT cross-check to verify the NCT IDs and trial metadata against the AACT 2026-04-12 snapshot. SGLT2i trials have NCT IDs:

- EMPA-REG OUTCOME → NCT01131676
- CANVAS → NCT01032629; CANVAS-R → NCT01989754
- SOLOIST-WHF → NCT03521934
- Wilding 2009 → NCT00263276 (registered separately as the Phase 2 dose-ranging)

- [ ] **Step 1: Add NCT IDs to the fixtures**

Both `sglt2i_hba1c.json` and `sglt2i_hhf.json` should have a `nct` field per trial. If they don't, add it now:

```bash
cd /c/Projects/Finrenone/.claude/worktrees/<wt>/ && python -c "
import json
for fix in ['sglt2i_hba1c', 'sglt2i_hhf']:
    path = f'tests/dose_response_fixtures/{fix}.json'
    with open(path) as f: d = json.load(f)
    print(f'=== {fix} ===')
    for t in d['trials']:
        print(f\"  {t['studlab']:50s} pmid={t['pmid']} nct={t.get('nct', 'MISSING')}\")
"
```

If any `nct` is `MISSING`, append the corresponding NCT ID to that trial's metadata and re-commit the fixtures.

- [ ] **Step 2: Run AACT cross-check (if the script supports per-review mode)**

```bash
cd /c/Projects/Finrenone/.claude/worktrees/<wt>/ && python scripts/aact_cross_check_v2.py --review SGLT2I_DOSE_RESP_REVIEW 2>&1 | tail -20
```

If the script's `--review <NAME>` mode requires special configuration for SGLT2i (e.g. a registered NCT list per review), and the script reports "review not found" or similar, this is an expected gap — the script was authored for the Finrenone NMA review family, not the dose-response pack. In that case:
- Capture the script's actual output
- Verify NCT IDs manually via PubMed (which the prior steps already did)
- Document the AACT-check limitation as a Round 2A follow-up: "AACT cross-check via `scripts/aact_cross_check_v2.py` does not (yet) recognize the dose-response review family — manually verified NCT IDs against AACT 2026-04-12 snapshot via raw query"

If the script DOES recognize the review and reports issues (e.g. country mismatches, drug-name mismatches), fix the fixture metadata.

- [ ] **Step 3: Commit any fixture metadata fixes**

```bash
git add tests/dose_response_fixtures/sglt2i_hba1c.json tests/dose_response_fixtures/sglt2i_hhf.json
git commit -m "fix(dose-response): add NCT IDs + AACT cross-check fixups for SGLT2i fixtures (Task 18)"
```

If no changes needed (NCTs already present, AACT clean), skip the commit and proceed.

---

### Task 19: Final smoke + Sentinel + close commit

**Files:** None (verification only); empty close commit at the end.

- [ ] **Step 1: Final engine test run**

```bash
cd /c/Projects/Finrenone/.claude/worktrees/<wt>/ && node tests/test_dose_response_engine.mjs 2>&1 | tail -5
```

Expected: `46 passed, 0 failed` (37 pre-Round-2A + ~9 new = ~46). The exact count may vary if synthetic-test counts differ from the plan estimates — the floor is "must be ≥46 and all green".

- [ ] **Step 2: Python wrapper smoke for both new fixtures**

```bash
python scripts/r_validate_doseresp.py --review sglt2i_hba1c 2>&1 | tail -3
python scripts/r_validate_doseresp.py --review sglt2i_hhf 2>&1 | tail -3
python scripts/r_validate_doseresp.py --review gl1992_alcohol_bc 2>&1 | tail -3
```

All three expected: `OK — linear=True, rcs=True`. The GL-1992 smoke is the binary-regression guard — must still pass after the R-script continuous dispatch was added.

- [ ] **Step 3: Sentinel scan**

```bash
cd /c/Projects/Finrenone/.claude/worktrees/<wt>/ && python -m sentinel scan --repo . 2>&1 | tail -20
```

Expected: BLOCK = 0 on Round 2A touched files (`rapidmeta-dose-response-engine-v1.js`, `tests/test_dose_response_engine.mjs`, `scripts/r_validate_doseresp.R`, `tests/dose_response_fixtures/sglt2i_*.json`, `outputs/r_validation/doseresp/sglt2i_*.json`, `SGLT2I_DOSE_RESP_REVIEW.html`).

WARN entries on pre-existing files (the parallel session's audit work, GL-1992 flagship, badge JS, etc.) are not this round's concern.

If a BLOCK fires on a Round 2A file, STOP and surface it.

- [ ] **Step 4: Browser end-to-end smoke (HTTP-server)**

```bash
cd /c/Projects/Finrenone/.claude/worktrees/<wt>/ && python -m http.server 8765 &
sleep 1
curl -fsS -o /tmp/page.html http://localhost:8765/SGLT2I_DOSE_RESP_REVIEW.html && echo "page OK"
curl -fsS -o /tmp/h.json http://localhost:8765/outputs/r_validation/doseresp/sglt2i_hba1c.json && echo "HbA1c JSON OK"
curl -fsS -o /tmp/f.json http://localhost:8765/outputs/r_validation/doseresp/sglt2i_hhf.json && echo "hHF JSON OK"
python -c "
with open('/tmp/page.html') as f: html = f.read()
print('page bytes:', len(html))
print('has 5 tab buttons:', html.count('data-tab=\"hba1c-linear\"') == 1 and html.count('data-tab=\"hhf\"') == 1)
print('has trial JSON embedded (HbA1c):', 'doseresp-trials-hba1c' in html)
print('has trial JSON embedded (hHF):', 'doseresp-trials-hhf' in html)
print('has class-equivalence caveat:', 'class-equivalence' in html)
print('has F-1 badge:', 'F-1 zero-cell' in html or 'F-1 not triggered' in html)
"
kill %1
```

Expected: all 3 curls succeed, page bytes > 10000, all structural checks pass.

- [ ] **Step 5: Final close commit**

```bash
git commit --allow-empty -m "$(cat <<'EOF'
close: Round 2A complete — SGLT2i flagship + engine v0.2.0 continuous-outcome support

Deliverables (~18 commits across Groups A-E):
- Engine v0.2.0: continuous-outcome branch in fitLinear/fitRCS, F-1 conditional
  zero-cell continuity correction, validate pool-level outcome-type homogeneity,
  mdCovariance helper.
- R script: continuous-mode dispatch (dosresmeta type='md' + lme4::lmer one-stage)
  with dose rescaling for convergence; binary path preserved.
- 2 new fixtures: sglt2i_hba1c (continuous, k=3-4 trials), sglt2i_hhf (binary,
  k=3 trials with SOLOIST-WHF zero-event arm exercising F-1).
- 2 new R-precomputed outputs: outputs/r_validation/doseresp/sglt2i_*.json.
- SGLT2I_DOSE_RESP_REVIEW.html — 5-tab flagship (HbA1c Linear / HbA1c RCS /
  HbA1c One-stage / hHF secondary / R-parity badge x2).
- ~9 new engine tests; total ~46 / 46 passing.
- Sentinel BLOCK = 0 on touched files.

Deferred to Round 2B:
- Full multivariate REML for fitRCS (closes diagonal-PM non-linearity p divergence)
- Q-profile tau^2 CI for fitLinear
- HKSJ-multivariate + t_{k-1} for fitRCS
- F-5 test gap closure (3 missing tests for ≥40 target — Round 2A may already exceed)
- P2-13 API forward-reference structural refactor

Deferred to Round 2C:
- Automated Playwright browser test
- F-6 stale plan file structure doc fix
- P1-7 + P2-5 shared vendor/r-validation-badge.js escapeHtml (if parallel session
  hasn't picked up)
EOF
)"
```

- [ ] **Step 6: Verify final state**

```bash
git log --oneline <pre-round-2A-SHA>..HEAD | head -25
node tests/test_dose_response_engine.mjs 2>&1 | tail -3
```

Expected: ~18 commits on the branch ending with the close commit; tests 46/0.

---

## Done conditions (Round 2A)

| Deliverable | Path | Verification |
|---|---|---|
| Engine v0.2.0 | `rapidmeta-dose-response-engine-v1.js` | `engine_version` = `'rapidmeta-dose-response-engine-v1@0.2.0'`; continuous-mode fitLinear/fitRCS tests pass; F-1 fires conditionally |
| Pool-mode dispatch | validate() rejects mixed binary+continuous | regression test pins behavior |
| HbA1c fixture | `tests/dose_response_fixtures/sglt2i_hba1c.json` | 3-4 trials, continuous arms, PMIDs verified |
| hHF fixture | `tests/dose_response_fixtures/sglt2i_hhf.json` | 3 trials, binary arms, SOLOIST zero-cell preserved |
| R script | `scripts/r_validate_doseresp.R` | continuous + binary smoke OK on both modes |
| R precompute HbA1c | `outputs/r_validation/doseresp/sglt2i_hba1c.json` | `linear.fit_ok=true`, `one_stage.converged=true` |
| R precompute hHF | `outputs/r_validation/doseresp/sglt2i_hhf.json` | `linear.fit_ok=true`, `one_stage.converged=true` |
| Flagship HTML | `SGLT2I_DOSE_RESP_REVIEW.html` | 5 tabs render; all PMIDs link; F-1 badge visibility correct |
| Engine tests | `tests/test_dose_response_engine.mjs` | ≥ 46 passing, 0 failed |
| Sentinel | `STUCK_FAILURES.jsonl` | BLOCK = 0 on touched files |
| Engine version bump | `engine_version` string | `@0.2.0` |
| Continuous-outcome parity | engine vs R `dosresmeta(type="md")` | linear pooled_slope_log within |Δ| < 0.01 (parity test in Task 7's manual verification or a dedicated test if added) |

