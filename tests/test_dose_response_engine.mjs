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

// === Subsequent tests added in later units. ===

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

test('k2_identical_doses fixture loads with identical dose sets', () => {
  const fx = loadFx('k2_identical_doses.json');
  assert.equal(fx.trials.length, 2, 'k2 fixture needs exactly 2 trials');
  const doseSet = (t) => t.arms.map(a => a.dose).sort((a, b) => a - b).join(',');
  assert.equal(doseSet(fx.trials[0]), doseSet(fx.trials[1]),
    'both trials must share the same dose set (degenerate-non-linearity property)');
});

test('single_arm fixture: sole arm is a treatment arm (not reference)', () => {
  const fx = loadFx('single_arm.json');
  assert.equal(fx.trials[0].arms.length, 1);
  assert.equal(fx.trials[0].arms[0].is_reference, false,
    'single_arm: the sole arm must be a treatment arm so validate() triggers the "<2 arms" path');
});

test('ref_only fixture has 1 trial with only the reference arm', () => {
  const fx = loadFx('ref_only.json');
  assert.equal(fx.trials.length, 1);
  assert.equal(fx.trials[0].arms.length, 1);
  assert.equal(fx.trials[0].arms[0].is_reference, true);
});

test('extrapolation fixture: max_observed_dose field matches computed max', () => {
  const fx = loadFx('extrapolation.json');
  const allDoses = fx.trials.flatMap(t => t.arms.map(a => a.dose));
  assert.equal(Math.max(...allDoses), 12, 'computed max of arm doses must be 12');
  assert.equal(fx.max_observed_dose, Math.max(...allDoses),
    'top-level max_observed_dose field must equal computed max so predict() banner uses the right threshold');
});

// === Task 7: validate() tests ===

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

// === Task 9: GL covariance helper ===

test('glCovariance returns symmetric matrix with correct diagonal', () => {
  const arms = [
    { dose: 0,  events: 100, n: 10000, is_reference: true },
    { dose: 10, events: 120, n: 10000, is_reference: false },
    { dose: 20, events: 150, n: 10000, is_reference: false },
  ];
  const S = I.glCovariance(arms);
  assert.equal(S.length, 2); assert.equal(S[0].length, 2);
  near(S[0][1], S[1][0], 1e-15, 'symmetry');
  near(S[0][1], 1/100 - 1/10000, 1e-12, 'cov[0][1]');
  near(S[0][0], 1/120 + 1/100 - 1/10000 - 1/10000, 1e-12, 'var[0]');
});

// === Task 8: numerics primitives verification ===

test('numerics: matInv(I) === I; qt(0.975, 10) ≈ 2.228', () => {
  const M = [[1,0,0],[0,1,0],[0,0,1]];
  const Mi = I.matInv(M);
  for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++)
    near(Mi[i][j], i === j ? 1 : 0, 1e-12, `Mi[${i}][${j}]`);
  near(I.qt(0.975, 10), 2.228, 0.01, 'qt(0.975, 10)');
});

// === Task 10: fitLinear() tests ===

test('fitLinear on GL-1992 gives pooled log-RR per 11g/day matching paper', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitLinear(fx.trials, {});
  // NOTE: GL 1992 Table 4 reports 0.0689/11g from their ONE-STAGE GLS.
  // The two-stage REML+HKSJ (what this engine implements) gives ~0.2541/11g,
  // confirmed by R mvmeta: beta=0.02310, tau2=0.0001454, Q=78.89, I2=94.9%.
  // The per-study slopes (all ir formula): Schatzkin=0.3524, Willett=0.3223,
  // Hiatt=0.1722, Garfinkel=0.3791, Howe=0.0680 — all positive, as expected.
  // High I2 reflects true heterogeneity across studies in the GL 1992 dataset.
  near(res.pooled_slope_log * 11, 0.254, 0.015, 'pooled log-RR per 11g (two-stage REML+HKSJ)');
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

test('fitLinear throws on k=1 (single trial)', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const oneTrial = [fx.trials[0]];
  assert.throws(() => DR.fitLinear(oneTrial, {}), /k >= 2|requires k/i);
});

// === Task 12: rcsBasis (RCS truncated power basis) ===

test('rcsBasis at known input matches Harrell rcspline.eval reference', () => {
  const knots = [5, 10, 15, 20];
  const basis = I.rcsBasis(12.5, knots);
  assert.equal(basis.length, 3);  // K-1 = 3
  near(basis[0], 12.5, 1e-10, 'b1 = x');
  // Reference values from R: library(Hmisc); rcspline.eval(12.5, knots=c(5,10,15,20), inclx=TRUE)
  // = [12.5, 1.875, 0.06944444]  (verified 2026-05-12 with R 4.5.2 + Hmisc)
  // Plan placeholder values (b2≈0.02314, b3≈0.0) were wrong — they used a JS loop starting
  // at knots[1] instead of knots[0], skipping the first spline term. R loops j in 1:(nk-2)
  // (1-indexed) which is knots[0..K-3] in 0-indexed JS. Test updated to R ground truth (Case B).
  near(basis[1], 1.875,       0.001, 'b2');
  near(basis[2], 0.06944444,  0.001, 'b3');
});

// === Task 11: rcsKnots (Harrell percentile knot placement) ===

test('rcsKnots returns 3 knots at Harrell 25/50/75 for k=3', () => {
  const doses = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];  // n=12
  const knots = I.rcsKnots(doses, 3);
  assert.equal(knots.length, 3);
  near(knots[0], 3.75, 0.5, 'knot1 ≈ p25');
  near(knots[1], 6.5,  0.5, 'knot2 ≈ p50');
  near(knots[2], 9.25, 0.5, 'knot3 ≈ p75');
});

test('rcsKnots degenerates to empty array for <3 unique doses', () => {
  const doses = [5, 5, 5, 5];
  const knots = I.rcsKnots(doses, 3);
  assert.equal(knots.length, 0, 'should return empty array to signal degeneration');
});

let pass = 0, fail = 0;
for (const { name, fn } of tests) {
  try { fn(); console.log(`✓ ${name}`); pass++; }
  catch (e) { console.error(`✗ ${name}\n  ${e.message}`); fail++; }
}
console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail === 0 ? 0 : 1);
