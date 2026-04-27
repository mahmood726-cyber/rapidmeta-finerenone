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

// Run
let pass = 0, fail = 0;
for (const t of tests) {
  try { t.fn(); console.log('PASS', t.name); pass++; }
  catch (e) { console.error('FAIL', t.name, '\n  ', e.message); fail++; }
}
console.log(`\n${pass} pass, ${fail} fail`);
process.exit(fail === 0 ? 0 : 1);
