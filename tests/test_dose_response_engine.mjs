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

let pass = 0, fail = 0;
for (const { name, fn } of tests) {
  try { fn(); console.log(`✓ ${name}`); pass++; }
  catch (e) { console.error(`✗ ${name}\n  ${e.message}`); fail++; }
}
console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail === 0 ? 0 : 1);
