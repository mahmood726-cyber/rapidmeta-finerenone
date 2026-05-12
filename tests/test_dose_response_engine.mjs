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

test('k2_identical_doses fixture loads', () => {
  const fx = loadFx('k2_identical_doses.json');
  assert.equal(fx.trials.length, 2);
});

test('single_arm fixture loads with 1 trial having 1 arm', () => {
  const fx = loadFx('single_arm.json');
  assert.equal(fx.trials[0].arms.length, 1);
});

test('ref_only fixture has 1 trial with only the reference arm', () => {
  const fx = loadFx('ref_only.json');
  assert.equal(fx.trials.length, 1);
  assert.equal(fx.trials[0].arms.length, 1);
  assert.equal(fx.trials[0].arms[0].is_reference, true);
});

test('extrapolation fixture max-observed-dose is 12', () => {
  const fx = loadFx('extrapolation.json');
  const allDoses = fx.trials.flatMap(t => t.arms.map(a => a.dose));
  assert.equal(Math.max(...allDoses), 12);
});

let pass = 0, fail = 0;
for (const { name, fn } of tests) {
  try { fn(); console.log(`✓ ${name}`); pass++; }
  catch (e) { console.error(`✗ ${name}\n  ${e.message}`); fail++; }
}
console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail === 0 ? 0 : 1);
