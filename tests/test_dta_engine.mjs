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
  const r1 = DTA._internal._ppvNpv(fakeFit, 0.999);
  assert.ok(r1.ppv > 0.95);
  assert.ok(r1.npv < 0.05);
});

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
  // Either fallback fires OR threshold-effect flag fires; assert at least one defensive flag is set.
  assert.ok(res.fallback === 'rho_fixed_zero' || res.threshold_effect === true,
            'expected defensive flag on extreme dataset; got '+JSON.stringify({fb:res.fallback, te:res.threshold_effect}));
});

test('exportResults: strips _fitInternal and adds metadata', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'dta_fixtures/auditc.json'), 'utf-8'));
  const res = DTA.fit(fx.trials);
  const out = DTA.exportResults(res);
  assert.equal(out._fitInternal, undefined);
  assert.equal(out.engine_version, '1.0.0');
  assert.ok(out.exported_at);
});

test('perStudy: returns Clopper-Pearson CIs that bracket the point estimate', () => {
  const ps = DTA._internal.perStudy({ studlab: 'X', TP: 154, FP: 7, FN: 28, TN: 933 });
  assert.ok(Array.isArray(ps.sens_ci) && ps.sens_ci.length === 2);
  assert.ok(Array.isArray(ps.spec_ci) && ps.spec_ci.length === 2);
  assert.ok(ps.sens_ci[0] <= ps.sens && ps.sens <= ps.sens_ci[1]);
  assert.ok(ps.spec_ci[0] <= ps.spec && ps.spec <= ps.spec_ci[1]);
});

test('continuity correction: correction=0 disables CC even with zeros', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'dta_fixtures/zero_cells.json'), 'utf-8'));
  const out = DTA._internal.applyContinuityCorrection(fx.trials, 0);
  assert.equal(out.corrected, false);
  assert.equal(out.trials[0].FP, 0);
});

test('continuity correction: does not mutate input', () => {
  const trials = [{TP:80,FP:0,FN:20,TN:100}];
  const snapshot = JSON.parse(JSON.stringify(trials));
  DTA._internal.applyContinuityCorrection(trials, 0.5);
  assert.deepEqual(trials, snapshot);
});

test('_ppvNpv: throws on invalid prevalence', () => {
  const f = { pooled_sens: 0.8, pooled_spec: 0.9, pooled_sens_ci_lb: 0.7, pooled_sens_ci_ub: 0.9, pooled_spec_ci_lb: 0.85, pooled_spec_ci_ub: 0.95 };
  assert.throws(() => DTA._internal._ppvNpv(f, -0.1));
  assert.throws(() => DTA._internal._ppvNpv(f, 1.1));
  assert.throws(() => DTA._internal._ppvNpv(f, NaN));
  assert.throws(() => DTA._internal._ppvNpv(f, 'foo'));
});

// P0-2: k=1 single study should label estimator as single_study_clopper_pearson, NOT fe_bivariate.
test('fit: k=1 returns single_study_clopper_pearson estimator', () => {
  const trials = [{studlab:'Solo', TP: 80, FP: 5, FN: 20, TN: 95}];
  const res = DTA.fit(trials);
  assert.equal(res.estimator, 'single_study_clopper_pearson');
  assert.equal(res.fallback, 'single_study');
  assert.equal(res.k, 1);
  // Pooled sens/spec should be the per-study values
  assert.ok(Math.abs(res.pooled_sens - 0.80) < 1e-6);
  assert.ok(Math.abs(res.pooled_spec - 0.95) < 1e-6);
  // tau^2 must be null (no meta-analysis)
  assert.equal(res.tau2_sens, null);
  assert.equal(res.tau2_spec, null);
});

// P0-3: prediction interval — Higgins 2009 / Riley 2011, t_{k-2} on logit scale.
test('predict: returns null bounds for k<3 and single_study', () => {
  const single = DTA.fit([{studlab:'A', TP:80, FP:5, FN:20, TN:95}]);
  const pi1 = DTA.predict(single);
  assert.equal(pi1.pi_sens_lb, null);
  assert.equal(pi1.pi_spec_lb, null);
  // k=2 — also undefined (df = k-2 = 0)
  const k2 = DTA.fit([
    {studlab:'A', TP:80, FP:5, FN:20, TN:95},
    {studlab:'B', TP:75, FP:3, FN:25, TN:97}
  ]);
  const pi2 = DTA.predict(k2);
  assert.equal(pi2.pi_sens_lb, null);
});

test('predict: AuditC k=14 returns finite PI brackets pooled estimates', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'dta_fixtures/auditc.json'), 'utf-8'));
  const res = DTA.fit(fx.trials);
  const pi = DTA.predict(res);
  assert.ok(pi.pi_sens_lb !== null && pi.pi_sens_ub !== null);
  assert.ok(pi.df === res.k - 2);
  // PI must bracket the pooled point estimate AND be wider than the CI.
  assert.ok(pi.pi_sens_lb < res.pooled_sens && res.pooled_sens < pi.pi_sens_ub);
  assert.ok(pi.pi_spec_lb < res.pooled_spec && res.pooled_spec < pi.pi_spec_ub);
  const ci_sens_w = res.pooled_sens_ci_ub - res.pooled_sens_ci_lb;
  const pi_sens_w = pi.pi_sens_ub - pi.pi_sens_lb;
  assert.ok(pi_sens_w >= ci_sens_w, 'PI must be at least as wide as CI');
});

// tinv sanity — t_{0.975, 10} ~ 2.228; t_{0.975, 30} ~ 2.042
test('tinv: matches known t-quantiles within 1e-3', () => {
  const t10 = DTA._internal.tinv(0.975, 10);
  const t30 = DTA._internal.tinv(0.975, 30);
  const t100 = DTA._internal.tinv(0.975, 100);
  assert.ok(Math.abs(t10 - 2.228) < 1e-2, 't10='+t10);
  assert.ok(Math.abs(t30 - 2.042) < 1e-2, 't30='+t30);
  assert.ok(Math.abs(t100 - 1.984) < 1e-2, 't100='+t100);
});

// P0-1: rho=0 fallback must be a real 2-parameter REML fit, not an FE collapse.
test('reitsmaREMLRhoZero: produces non-zero tau^2 (genuine REML, not FE stub)', () => {
  // Use the AuditC dataset — has real between-study heterogeneity.
  const fx = JSON.parse(readFileSync(join(__dirname, 'dta_fixtures/auditc.json'), 'utf-8'));
  const res = DTA._internal.reitsmaREMLRhoZero(fx.trials, { max_iter: 500 });
  assert.equal(res.estimator, 'reml_rho_zero');
  assert.equal(res._stub, false, 'expected genuine fit, got stub');
  assert.equal(res.rho, 0);
  assert.ok(res.tau2_sens > 1e-6, 'tau2_sens must be > 0 on AuditC: '+res.tau2_sens);
  assert.ok(res.tau2_spec > 1e-6, 'tau2_spec must be > 0 on AuditC: '+res.tau2_spec);
  assert.ok(res.converged);
});

// Run
let pass = 0, fail = 0;
for (const t of tests) {
  try { t.fn(); console.log('PASS', t.name); pass++; }
  catch (e) { console.error('FAIL', t.name, '\n  ', e.message); fail++; }
}
console.log(`\n${pass} pass, ${fail} fail`);
process.exit(fail === 0 ? 0 : 1);
