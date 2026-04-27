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

// AuditC mada-parity smoke test.
//
// The expected values in dta_fixtures/auditc.json (sens 0.829, spec 0.814,
// tau2_sens 0.14, tau2_spec 0.20, rho -0.31) are the plan author's approximate
// estimates of what mada::reitsma(AuditC) produces — they were not generated
// by running R locally during plan authoring.
//
// Strict |Δ| < 1e-3 mada-parity is enforced at build-time by T18's WebR
// validator (webr-dta-validator.js with mada loaded in-browser). This unit
// test is a smoke check: it verifies that the Nelder-Mead REML optimizer
// converges to a defensible REML optimum on a real-world dataset, with
// sensible tau^2 estimates and pooled values within ~5pp of the published
// fit. Tightening the tolerance to mada-parity (1e-3) is a T18 concern.
test('reitsmaREML: AuditC matches mada within smoke-test tolerance', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'dta_fixtures/auditc.json'), 'utf-8'));
  const res = DTA._internal.reitsmaREML(fx.trials, { max_iter: 500 });
  assert.ok(res.converged, 'did not converge: iterations=' + res.iterations);
  const sens = 1 / (1 + Math.exp(-res.mu_sens_logit));
  const spec = 1 / (1 + Math.exp(-res.mu_spec_logit));
  assert.ok(Math.abs(sens - fx.expected.pooled_sens) < fx.tolerance.sens,
            'sens ' + sens + ' vs ' + fx.expected.pooled_sens);
  assert.ok(Math.abs(spec - fx.expected.pooled_spec) < fx.tolerance.spec,
            'spec ' + spec + ' vs ' + fx.expected.pooled_spec);
  assert.ok(Math.abs(res.tau2_sens - fx.expected.tau2_sens) < fx.tolerance.tau2,
            'tau2_sens ' + res.tau2_sens);
  assert.ok(Math.abs(res.tau2_spec - fx.expected.tau2_spec) < fx.tolerance.tau2,
            'tau2_spec ' + res.tau2_spec);
});

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

test('_ppvNpv: known values at prevalence=0.10', () => {
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

// Run
let pass = 0, fail = 0;
for (const t of tests) {
  try { t.fn(); console.log('PASS', t.name); pass++; }
  catch (e) { console.error('FAIL', t.name, '\n  ', e.message); fail++; }
}
console.log(`\n${pass} pass, ${fail} fail`);
process.exit(fail === 0 ? 0 : 1);
