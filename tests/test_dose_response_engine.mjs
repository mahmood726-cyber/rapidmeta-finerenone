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

let pass = 0, fail = 0;
for (const { name, fn } of tests) {
  try { fn(); console.log(`✓ ${name}`); pass++; }
  catch (e) { console.error(`✗ ${name}\n  ${e.message}`); fail++; }
}
console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail === 0 ? 0 : 1);
