// tests/test_panel_improvements.mjs — Node-runnable, pure JS.
// Exercises the helpers exposed via __test__ on each vendor module after the
// 2026-05-10 panel-review fixes (DTA spearman, k<5 advisory, PI k<3,
// dose-response cross-class, Q-profile degenerate case, permutation seed).
import { strict as assert } from 'node:assert';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const VENDOR = join(__dirname, '..', 'vendor');

// Load a vendor IIFE module into a fresh sandbox object.
//
// The vendor IIFE wrapper is `(function (global) { ... })(typeof window !==
// 'undefined' ? window : this);`. The `global` IIFE parameter SHADOWS any
// outer name. To inject our sandbox we declare the outer parameter as
// `window` so that `typeof window !== 'undefined'` evaluates true inside
// the new-Function body, and the ternary then passes our sandbox into the
// IIFE.
function loadVendor(name) {
  const src = readFileSync(join(VENDOR, name), 'utf-8');
  const ctx = {};
  new Function('window', src)(ctx);
  return ctx;
}

const tests = [];
function test(name, fn) { tests.push({ name, fn }); }

// ---------- DTA: spearmanRho ----------
const dta = loadVendor('dta-bivariate.js');
const { spearmanRho, trialSensSpec, poolDLRE } = dta.DTABivariate.__test__;

test('spearmanRho: perfect ascending → ρ = 1', () => {
  assert.equal(spearmanRho([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]), 1);
});
test('spearmanRho: perfect descending → ρ = -1', () => {
  assert.equal(spearmanRho([1, 2, 3, 4, 5], [5, 4, 3, 2, 1]), -1);
});
test('spearmanRho: returns null for n < 3', () => {
  assert.equal(spearmanRho([1, 2], [1, 2]), null);
});
test('spearmanRho: handles ties via average rank', () => {
  // Ties in xs at value 2 — should still produce a valid correlation
  const r = spearmanRho([1, 2, 2, 3], [1, 2, 3, 4]);
  assert.ok(r !== null && r > 0.8, 'expected strong positive ρ with ties; got ' + r);
});

test('DTA threshold-effect: |ρ| > 0.6 detected on synthetic threshold-varying data', () => {
  // Construct 6 trials where Sens and (1−Spec) move together → high
  // Spearman ρ on logit(Se) vs logit(1−Sp); flags threshold heterogeneity.
  const trials = [
    { TP: 80, FN: 20, FP: 30, TN: 70 },   // Se=0.80, Sp=0.70
    { TP: 90, FN: 10, FP: 40, TN: 60 },   // Se=0.90, Sp=0.60
    { TP: 95, FN:  5, FP: 50, TN: 50 },   // Se=0.95, Sp=0.50
    { TP: 70, FN: 30, FP: 20, TN: 80 },   // Se=0.70, Sp=0.80
    { TP: 60, FN: 40, FP: 10, TN: 90 },   // Se=0.60, Sp=0.90
    { TP: 50, FN: 50, FP:  5, TN: 95 },   // Se=0.50, Sp=0.95
  ];
  const ss = trials.map(trialSensSpec);
  const xLogitSe = ss.map(s => s.logitSe);
  const xLogit1mSp = ss.map(s => Math.log((1 - s.Sp) / s.Sp));
  const r = spearmanRho(xLogitSe, xLogit1mSp);
  assert.ok(Math.abs(r) > 0.6, 'expected |ρ|>0.6 to flag threshold effect; got ' + r);
});

// ---------- DTA: small-k poolDLRE robustness (k=3 fallback) ----------
test('poolDLRE: produces valid pool for k=3', () => {
  const yi = [0.1, 0.2, 0.3];
  const vi = [0.04, 0.05, 0.06];
  const pool = poolDLRE(yi, vi);
  assert.ok(pool, 'pool should not be null for k=3');
  assert.equal(pool.k, 3);
  assert.ok(pool.tau2 >= 0, 'τ² must be non-negative');
  assert.ok(pool.ci_low < pool.mean && pool.mean < pool.ci_high, 'CI must bracket mean');
});

// ---------- DOSE-RESPONSE: cross-class drug-stem detection ----------
const dr = loadVendor('dose-response.js');
const { detectDrugStems } = dr.DoseResponse.__test__;

test('detectDrugStems: 3 distinct stems → cross-class', () => {
  const stems = detectDrugStems([
    'Infliximab 5 mg/kg',
    'Adalimumab 80 mg',
    'Golimumab 100 mg',
  ]);
  assert.equal(stems.size, 3);
});
test('detectDrugStems: same drug at different doses → 1 stem (single-drug, valid)', () => {
  const stems = detectDrugStems([
    'Tofacitinib 5 mg',
    'Tofacitinib 10 mg',
    'Tofacitinib 15 mg',
  ]);
  assert.equal(stems.size, 1);
});
test('detectDrugStems: short/empty stems are skipped', () => {
  const stems = detectDrugStems(['', 'A', 'AB', 'Drug 5mg']);
  // 'A', 'AB' below 4-char threshold; only 'drug' counts
  assert.equal(stems.size, 1);
});

// ---------- Q-PROFILE: degenerate case ----------
const qp = loadVendor('tau2-qprofile.js');
const { qProfileCI } = qp.Tau2QProfile;

test('qProfileCI: homogeneous data (Q ≤ χ²_lo) → null bounds via Viechtbauer convention', () => {
  // 5 perfectly homogeneous studies — Q ≈ 0, far below χ²_{0.025, 4}
  const pts = [0.5, 0.5, 0.5, 0.5, 0.5].map((y, i) => ({ yi: y, vi: 0.04 }));
  const ci = qProfileCI(pts, 0.05);
  assert.ok(ci, 'must return an object');
  // Per Viechtbauer 2007, when Q ≤ χ²_lo the lower & upper bounds are null
  // (the conditional return path at line 102) — both null is the correct
  // signal that the data carry no information about τ².
  assert.equal(ci.tau2_hat, 0);
  assert.equal(ci.tau2_L, null);
  assert.equal(ci.tau2_U, null);
});

test('qProfileCI: heterogeneous data → finite τ² CI bounds', () => {
  // Spread effects with realistic between-study variance
  const pts = [0.10, 0.30, 0.50, 0.70, 0.90, 1.10, 1.30].map((y, i) => ({
    yi: y, vi: [0.02, 0.03, 0.04, 0.02, 0.03, 0.04, 0.02][i],
  }));
  const ci = qProfileCI(pts, 0.05);
  assert.ok(ci, 'must return an object');
  assert.ok(ci.tau2_hat > 0, 'τ̂² should be > 0 for heterogeneous data; got ' + ci.tau2_hat);
  assert.ok(ci.tau2_U != null && ci.tau2_U > 0, 'upper bound should be > 0; got ' + ci.tau2_U);
  // Lower bound may be 0 (Q-profile floors at 0) — just require it's < upper
  assert.ok(ci.tau2_L != null && ci.tau2_L <= ci.tau2_U, 'lower ≤ upper');
});

test('qProfileCI: returns null for k < 3', () => {
  const pts = [{ yi: 0.1, vi: 0.04 }, { yi: 0.2, vi: 0.05 }];
  assert.equal(qProfileCI(pts, 0.05), null);
});

// ---------- PERMUTATION: seed reproducibility ----------
const perm = loadVendor('meta-regression-permutation.js');
const { rng, permute } = perm.MetaRegPermutation.__test__;

test('rng: same seed → same first 5 draws (Mulberry32 reproducibility)', () => {
  const r1 = rng(12345);
  const r2 = rng(12345);
  for (let i = 0; i < 5; i++) {
    assert.equal(r1(), r2(), 'draw ' + i + ' must match');
  }
});
test('rng: different seeds → different sequences', () => {
  const r1 = rng(12345);
  const r2 = rng(54321);
  assert.notEqual(r1(), r2(), 'first draw should differ across seeds');
});
test('permute: same seed produces same permutation', () => {
  const arr = [10, 20, 30, 40, 50];
  const p1 = permute(arr, rng(7));
  const p2 = permute(arr, rng(7));
  assert.deepEqual(p1, p2);
  // Verify it's actually permuted (not the input order — Mulberry32 with seed 7
  // is virtually certain to permute n=5 to a non-identity ordering)
  assert.notDeepEqual(p1, arr);
});

// ---------- RUN ----------
let pass = 0, fail = 0;
for (const t of tests) {
  try {
    t.fn();
    console.log('  ✓ ' + t.name);
    pass++;
  } catch (e) {
    console.log('  ✗ ' + t.name);
    console.log('    ' + e.message);
    fail++;
  }
}
console.log('\n' + pass + ' passed, ' + fail + ' failed');
process.exit(fail === 0 ? 0 : 1);
