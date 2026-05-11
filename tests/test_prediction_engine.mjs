// tests/test_prediction_engine.mjs — Node-runnable, pure JS
// Targets the rapidmeta-prediction-engine-v1.js engine.
//
// Run: node tests/test_prediction_engine.mjs
//
// Mirrors tests/test_dta_engine.mjs in structure: load the engine source into
// a sandboxed `window` context, then exercise the public + _internal API.
import { strict as assert } from 'node:assert';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ENGINE_PATH = join(__dirname, '..', 'rapidmeta-prediction-engine-v1.js');

const engineSrc = readFileSync(ENGINE_PATH, 'utf-8');
const ctx = {};
new Function('window', engineSrc)(ctx);
const PRED = ctx.RapidMetaPrediction;

const tests = [];
function test(name, fn) { tests.push({ name, fn }); }

// ───── Validation ─────
test('validate: rejects empty array', () => {
  const issues = PRED.validate([]);
  assert.ok(issues.length > 0);
});

test('validate: rejects non-array', () => {
  const issues = PRED.validate('not-an-array');
  assert.ok(issues.length > 0);
});

test('validate: accepts well-formed cohort with C + n_events/n_nonevents', () => {
  const issues = PRED.validate([{
    studlab: 'PCE-MESA', C: 0.74, n_events: 120, n_nonevents: 4500, cohort_type: 'external'
  }]);
  assert.deepEqual(issues, []);
});

test('validate: rejects C > 1', () => {
  const issues = PRED.validate([{ studlab: 'bad', C: 1.05, n_events: 10, n_nonevents: 100 }]);
  assert.ok(issues.length > 0 && issues[0].includes('C must be in'));
});

test('validate: warns on C < 0.5 (worse than chance)', () => {
  const issues = PRED.validate([{ studlab: 'bad', C: 0.42, n_events: 10, n_nonevents: 100 }]);
  assert.ok(issues.some(s => /worse than chance|verify direction/.test(s)));
});

test('validate: rejects missing C_se with no n_events/n_nonevents', () => {
  const issues = PRED.validate([{ studlab: 'no-se', C: 0.75 }]);
  assert.ok(issues.some(s => /n_events/.test(s)));
});

test('validate: rejects negative C_se', () => {
  const issues = PRED.validate([{ studlab: 'neg', C: 0.75, C_se: -0.01 }]);
  assert.ok(issues.some(s => /C_se must be > 0/.test(s)));
});

test('validate: rejects non-finite calib_slope', () => {
  const issues = PRED.validate([{
    studlab: 'x', C: 0.75, C_se: 0.02, calib_slope: 'oops', calib_slope_se: 0.1
  }]);
  assert.ok(issues.some(s => /calib_slope must be a finite/.test(s)));
});

test('validate: rejects OE without SE info', () => {
  const issues = PRED.validate([{
    studlab: 'x', C: 0.75, C_se: 0.02, OE: 1.1
  }]);
  assert.ok(issues.some(s => /OE provided but missing/.test(s)));
});

test('validate: rejects Brier outside [0,1]', () => {
  const issues = PRED.validate([{
    studlab: 'x', C: 0.75, C_se: 0.02, brier: 1.5
  }]);
  assert.ok(issues.some(s => /brier must be in/.test(s)));
});

// ───── Numeric primitives ─────
test('logit/invLogit round-trip', () => {
  const ps = [0.1, 0.3, 0.5, 0.7, 0.9, 0.99];
  for (const p of ps) {
    assert.ok(Math.abs(PRED._internal.invLogit(PRED._internal.logit(p)) - p) < 1e-12);
  }
});

test('Hanley-McNeil variance: AUC=0.80 n=100/100 matches hand calc', () => {
  // Hand: Q1=0.6667, Q2=0.7111; num=0.16 + 99*(0.6667-0.64) + 99*(0.7111-0.64)
  //       = 0.16 + 2.6433 + 7.0389 = 9.8422; var = 9.8422/10000 ≈ 0.000984
  const v = PRED._internal.hanleyMcNeilVar(0.80, 100, 100);
  assert.ok(Math.abs(v - 0.000984) < 5e-5, 'got ' + v);
});

test('Hanley-McNeil variance: rejects negative inputs', () => {
  assert.ok(!isFinite(PRED._internal.hanleyMcNeilVar(0.8, -10, 100)) ||
            isNaN(PRED._internal.hanleyMcNeilVar(0.8, -10, 100)));
});

test('logitCSE delta-method: AUC=0.8 SE=0.03 → logit SE ≈ 0.1875', () => {
  // SE(logit C) = SE(C) / (C*(1-C)) = 0.03 / (0.8*0.2) = 0.1875
  const seLogit = PRED._internal.logitCSE(0.8, 0.03);
  assert.ok(Math.abs(seLogit - 0.1875) < 1e-6);
});

test('oeLogVar: 50 observed in 500 total ≈ (1-0.1)/50 = 0.018', () => {
  const v = PRED._internal.oeLogVar(50, 500);
  assert.ok(Math.abs(v - 0.018) < 1e-9);
});

test('oeLogVar: falls back to 1/O when n_total missing', () => {
  const v = PRED._internal.oeLogVar(40);
  assert.ok(Math.abs(v - 1/40) < 1e-12);
});

test('tinv: matches known t-quantiles', () => {
  const t10 = PRED._internal.tinv(0.975, 10);
  const t30 = PRED._internal.tinv(0.975, 30);
  const t100 = PRED._internal.tinv(0.975, 100);
  assert.ok(Math.abs(t10 - 2.228) < 1e-2, 't10='+t10);
  assert.ok(Math.abs(t30 - 2.042) < 1e-2, 't30='+t30);
  assert.ok(Math.abs(t100 - 1.984) < 1e-2, 't100='+t100);
});

test('qchisq: matches known chi-square quantiles', () => {
  // qchisq(0.95, 1) ≈ 3.841; qchisq(0.95, 5) ≈ 11.07
  assert.ok(Math.abs(PRED._internal.qchisq(0.95, 1) - 3.841) < 1e-2);
  assert.ok(Math.abs(PRED._internal.qchisq(0.95, 5) - 11.07) < 0.1);
});

test('chi2UpperP: q=3.841 df=1 ≈ 0.05', () => {
  const p = PRED._internal.chi2UpperP(3.841, 1);
  assert.ok(Math.abs(p - 0.05) < 1e-2, 'p=' + p);
});

// ───── Pooling: Paule-Mandel REML ─────
test('paule_mandel: homogeneous data → tau² ≈ 0', () => {
  // 5 cohorts at logitC = 1.0 with equal variance
  const yi = [1.0, 1.0, 1.0, 1.0, 1.0];
  const vi = [0.04, 0.04, 0.04, 0.04, 0.04];
  const pm = PRED._internal.paule_mandel(yi, vi);
  assert.ok(pm.tau2 < 1e-4, 'tau2=' + pm.tau2);
  assert.ok(Math.abs(pm.mu - 1.0) < 1e-9);
});

test('paule_mandel: heterogeneous data → tau² > 0', () => {
  // 5 cohorts with spread > sampling
  const yi = [0.5, 0.7, 1.0, 1.3, 1.5];
  const vi = [0.02, 0.02, 0.02, 0.02, 0.02];
  const pm = PRED._internal.paule_mandel(yi, vi);
  assert.ok(pm.tau2 > 0.05, 'tau2=' + pm.tau2);
  assert.ok(pm.mu > 0.9 && pm.mu < 1.1, 'mu=' + pm.mu);
});

test('paule_mandel: pooled mean matches inverse-variance weighted mean at tau²=0', () => {
  const yi = [1.0, 1.0, 1.0];
  const vi = [0.01, 0.02, 0.04];
  const pm = PRED._internal.paule_mandel(yi, vi);
  const wExp = vi.map(v => 1/v);
  const sumW = wExp.reduce((a,b)=>a+b, 0);
  const muExp = yi.reduce((s, y, i) => s + wExp[i]*y, 0) / sumW;
  assert.ok(Math.abs(pm.mu - muExp) < 1e-3);
});

test('hksjCI: Q < df → floor = 1 (no inflation)', () => {
  const pm = PRED._internal.paule_mandel([1.0, 1.0, 1.0, 1.0, 1.0],
                                          [0.04, 0.04, 0.04, 0.04, 0.04]);
  const hk = PRED._internal.hksjCI(pm, 0.05);
  assert.ok(Math.abs(hk.hksj_factor - 1) < 1e-9, 'factor=' + hk.hksj_factor);
});

test('hksjCI: heterogeneous data → factor > 1', () => {
  const pm = PRED._internal.paule_mandel([0.5, 0.7, 1.0, 1.3, 1.5],
                                          [0.02, 0.02, 0.02, 0.02, 0.02]);
  const hk = PRED._internal.hksjCI(pm, 0.05);
  assert.ok(hk.hksj_factor > 1, 'factor=' + hk.hksj_factor);
});

test('predictionInterval: undefined for k=2 (df<2)', () => {
  const pm = PRED._internal.paule_mandel([1.0, 1.0], [0.04, 0.04]);
  const pi = PRED._internal.predictionInterval(pm, 0.05);
  assert.equal(pi.defined, false);
});

test('predictionInterval: defined and brackets pooled mean for k>=3', () => {
  const pm = PRED._internal.paule_mandel([0.8, 1.0, 1.2, 1.4],
                                          [0.04, 0.04, 0.04, 0.04]);
  const pi = PRED._internal.predictionInterval(pm, 0.05);
  assert.equal(pi.defined, true);
  assert.ok(pi.pi_lo < pm.mu && pm.mu < pi.pi_hi);
});

test('poolGeneric: single cohort → method=single_cohort_wald', () => {
  const r = PRED._internal.poolGeneric([1.0], [0.04]);
  assert.equal(r.k, 1);
  assert.equal(r.method, 'single_cohort_wald');
  assert.ok(isNaN(r.tau2));
});

// ───── fit() integration ─────
function demoCohorts() {
  // SCORE2-flavoured synthetic dataset: 5 external validation cohorts
  // C-statistic around 0.74-0.78, calibration intercept near 0, slope near 1, O/E near 1.
  return [
    { studlab: 'cohort_A', C: 0.74, C_se: 0.012,
      calib_int: -0.10, calib_int_se: 0.05,
      calib_slope: 0.92, calib_slope_se: 0.04,
      OE: 0.95, n_observed: 280, n_total: 4500,
      brier: 0.084, brier_se: 0.004,
      cohort_type: 'derivation',
      probast: { participants: 'low', predictors: 'low', outcome: 'low', analysis: 'low' } },
    { studlab: 'cohort_B', C: 0.76, C_se: 0.015,
      calib_int: 0.05, calib_int_se: 0.06,
      calib_slope: 1.04, calib_slope_se: 0.05,
      OE: 1.08, n_observed: 220, n_total: 3800,
      brier: 0.078, brier_se: 0.005,
      cohort_type: 'external',
      probast: { participants: 'low', predictors: 'low', outcome: 'low', analysis: 'unclear' } },
    { studlab: 'cohort_C', C: 0.78, C_se: 0.020,
      calib_int: -0.20, calib_int_se: 0.08,
      calib_slope: 0.88, calib_slope_se: 0.06,
      OE: 0.84, n_observed: 145, n_total: 2900,
      brier: 0.091, brier_se: 0.005,
      cohort_type: 'external',
      probast: { participants: 'high', predictors: 'low', outcome: 'low', analysis: 'low' } },
    { studlab: 'cohort_D', C: 0.72, C_se: 0.018,
      calib_int: 0.12, calib_int_se: 0.07,
      calib_slope: 1.10, calib_slope_se: 0.06,
      OE: 1.15, n_observed: 180, n_total: 3200,
      brier: 0.088, brier_se: 0.004,
      cohort_type: 'external',
      probast: { participants: 'low', predictors: 'unclear', outcome: 'low', analysis: 'low' } },
    { studlab: 'cohort_E', C: 0.75, C_se: 0.014,
      calib_int: -0.05, calib_int_se: 0.05,
      calib_slope: 0.95, calib_slope_se: 0.04,
      OE: 0.98, n_observed: 250, n_total: 4100,
      brier: 0.082, brier_se: 0.004,
      cohort_type: 'external',
      probast: { participants: 'low', predictors: 'low', outcome: 'unclear', analysis: 'low' } }
  ];
}

test('fit: returns expected top-level shape on 5-cohort demo', () => {
  const r = PRED.fit(demoCohorts());
  assert.equal(r.k, 5);
  assert.equal(r.k_C, 5);
  assert.ok(r.C_pool && r.C_pool.C_pool > 0.5 && r.C_pool.C_pool < 1.0);
  assert.ok(r.calib_int_pool && isFinite(r.calib_int_pool.mu));
  assert.ok(r.calib_slope_pool && isFinite(r.calib_slope_pool.mu));
  assert.ok(r.OE_pool && r.OE_pool.OE_pool > 0);
  assert.ok(r.brier_pool && isFinite(r.brier_pool.mu));
  assert.equal(r.engine_version, '1.0.0');
});

test('fit: pooled C bracket — pooled estimate within [0.72, 0.78]', () => {
  const r = PRED.fit(demoCohorts());
  assert.ok(r.C_pool.C_pool >= 0.72 && r.C_pool.C_pool <= 0.78,
            'C_pool=' + r.C_pool.C_pool);
});

test('fit: pooled C 95% CI brackets pooled point', () => {
  const r = PRED.fit(demoCohorts());
  assert.ok(r.C_pool.C_ci_lo < r.C_pool.C_pool);
  assert.ok(r.C_pool.C_pool < r.C_pool.C_ci_hi);
});

test('fit: pooled C prediction interval defined and at least as wide as CI', () => {
  const r = PRED.fit(demoCohorts());
  assert.equal(r.C_pool.pi_defined, true);
  const pi_w = r.C_pool.C_pi_hi - r.C_pool.C_pi_lo;
  const ci_w = r.C_pool.C_ci_hi - r.C_pool.C_ci_lo;
  assert.ok(pi_w >= ci_w * 0.99, 'PI ' + pi_w + ' should be >= CI ' + ci_w);
});

test('fit: O/E pool back-transforms correctly (around 1)', () => {
  const r = PRED.fit(demoCohorts());
  assert.ok(r.OE_pool.OE_pool > 0.7 && r.OE_pool.OE_pool < 1.3,
            'OE_pool=' + r.OE_pool.OE_pool);
});

test('fit: missing C_se falls back to Hanley-McNeil', () => {
  const r = PRED.fit([
    { studlab: 'a', C: 0.78, n_events: 150, n_nonevents: 2000, cohort_type: 'external' },
    { studlab: 'b', C: 0.75, n_events: 180, n_nonevents: 2200, cohort_type: 'external' },
    { studlab: 'c', C: 0.72, n_events: 90, n_nonevents: 1500, cohort_type: 'external' }
  ]);
  assert.ok(r.C_pool && isFinite(r.C_pool.C_pool));
  assert.ok(r.C_pool.C_pool > 0.7 && r.C_pool.C_pool < 0.8);
});

test('fit: single cohort returns method=single_cohort_wald, no τ²', () => {
  const r = PRED.fit([{
    studlab: 'solo', C: 0.78, C_se: 0.02, cohort_type: 'derivation'
  }]);
  assert.equal(r.k, 1);
  assert.equal(r.C_pool.method, 'single_cohort_wald');
  assert.ok(isNaN(r.C_pool.tau2));
});

test('fit: two cohorts pool but skip prediction interval', () => {
  const r = PRED.fit([
    { studlab: 'a', C: 0.75, C_se: 0.02, cohort_type: 'external' },
    { studlab: 'b', C: 0.78, C_se: 0.02, cohort_type: 'external' }
  ]);
  assert.equal(r.k, 2);
  assert.equal(r.C_pool.pi_defined, false);
});

test('fit: optional metrics skipped gracefully if not provided', () => {
  // Only C — no calibration, no O/E, no Brier
  const r = PRED.fit([
    { studlab: 'a', C: 0.78, C_se: 0.02 },
    { studlab: 'b', C: 0.75, C_se: 0.02 },
    { studlab: 'c', C: 0.72, C_se: 0.02 }
  ]);
  assert.equal(r.k_calib_int, 0);
  assert.equal(r.k_calib_slope, 0);
  assert.equal(r.k_OE, 0);
  assert.equal(r.k_brier, 0);
  assert.equal(r.calib_int_pool, null);
});

// ───── PROBAST summary ─────
test('PROBAST: all-low cohort → overall low', () => {
  const r = PRED.fit([
    { studlab: 'a', C: 0.75, C_se: 0.02,
      probast: { participants: 'low', predictors: 'low', outcome: 'low', analysis: 'low' } }
  ]);
  assert.equal(r.probast.per_cohort[0].overall, 'low');
  assert.equal(r.probast.overall.low, 1);
});

test('PROBAST: any-high → overall high', () => {
  const r = PRED.fit([
    { studlab: 'a', C: 0.75, C_se: 0.02,
      probast: { participants: 'low', predictors: 'low', outcome: 'low', analysis: 'high' } }
  ]);
  assert.equal(r.probast.per_cohort[0].overall, 'high');
});

test('PROBAST: per-domain tally counts correct', () => {
  const r = PRED.fit(demoCohorts());
  assert.equal(r.probast.domains.participants.low, 4);
  assert.equal(r.probast.domains.participants.high, 1);
  assert.equal(r.probast.domains.predictors.unclear, 1);
});

test('PROBAST: cohort with no probast field → unclear', () => {
  const r = PRED.fit([{ studlab: 'a', C: 0.75, C_se: 0.02 }]);
  assert.equal(r.probast.per_cohort[0].overall, 'unclear');
});

// ───── dev vs external split ─────
test('dev_vs_external: splits 1 derivation + 4 external', () => {
  const r = PRED.fit(demoCohorts());
  assert.ok(r.dev_vs_external);
  assert.ok(r.dev_vs_external.derivation && r.dev_vs_external.derivation.k === 1);
  assert.ok(r.dev_vs_external.external && r.dev_vs_external.external.k === 4);
});

test('dev_vs_external: external-only pool produces finite C', () => {
  const r = PRED.fit(demoCohorts());
  assert.ok(r.dev_vs_external.external.C_pool > 0.5);
  assert.ok(r.dev_vs_external.external.C_pool < 1.0);
});

test('dev_vs_external: Q_between is finite (or null when one bucket has k<1)', () => {
  const r = PRED.fit(demoCohorts());
  // 1 dev + 4 ext should produce finite Q_between
  assert.ok(r.dev_vs_external.Q_between == null ||
            isFinite(r.dev_vs_external.Q_between));
});

// ───── Forest layout ─────
test('forest: discrimination rows = k + 1 pooled', () => {
  const r = PRED.fit(demoCohorts());
  const f = PRED.forest(r);
  assert.equal(f.discrimination.length, 6);
  assert.equal(f.discrimination[5].is_pooled, true);
});

test('forest: O/E rows back-transformed (point > 0)', () => {
  const r = PRED.fit(demoCohorts());
  const f = PRED.forest(r);
  f.OE.forEach(row => assert.ok(row.point > 0, 'OE point=' + row.point));
});

test('forest: pooled row carries τ² and I²', () => {
  const r = PRED.fit(demoCohorts());
  const f = PRED.forest(r);
  const pooled = f.discrimination[f.discrimination.length - 1];
  assert.ok(typeof pooled.tau2 === 'number');
  assert.ok(typeof pooled.I2 === 'number');
});

// ───── Export ─────
test('exportResults: deep clone with exported_at timestamp', () => {
  const r = PRED.fit(demoCohorts());
  const exp = PRED.exportResults(r);
  assert.ok(exp.exported_at);
  assert.ok(/^\d{4}-\d{2}-\d{2}T/.test(exp.exported_at));
  assert.equal(exp.k, r.k);
  // Mutating export must not affect original
  exp.k = 999;
  assert.equal(r.k, 5);
});

// ───── R / metafor cross-check baselines ─────
// Three frozen baseline cases in tests/prediction_fixtures/r_metafor_baselines.json.
// Cases 1 and 2 are hand-verifiable closed-form values; case 3 is a real-data
// regression baseline (6 published KFRE external-validation cohorts).
const R_BASE = JSON.parse(readFileSync(join(__dirname, 'prediction_fixtures/r_metafor_baselines.json'), 'utf-8'));

test('R-baseline case 1 (homogeneous): τ²=0, μ=1, hand-derived CI', () => {
  const c = R_BASE.case_1_homogeneous_closed_form;
  const pm = PRED._internal.paule_mandel(c.input.yi, c.input.vi);
  const hk = PRED._internal.hksjCI(pm, c.input.alpha);
  const exp = c.expected, tol = c.tolerance;
  assert.ok(Math.abs(pm.tau2 - exp.tau2) < tol, 'tau2 ' + pm.tau2);
  assert.ok(Math.abs(pm.mu - exp.mu) < tol, 'mu ' + pm.mu);
  assert.ok(Math.abs(pm.se_mu - exp.se_mu) < tol, 'se_mu ' + pm.se_mu);
  assert.ok(Math.abs(hk.hksj_factor - exp.hksj_factor) < tol, 'hksj ' + hk.hksj_factor);
  assert.ok(Math.abs(hk.t - exp.t_crit_0975_df2) < 1e-3, 't ' + hk.t);
  assert.ok(Math.abs(hk.ci_lo - exp.ci_lo) < 1e-6, 'ci_lo ' + hk.ci_lo);
  assert.ok(Math.abs(hk.ci_hi - exp.ci_hi) < 1e-6, 'ci_hi ' + hk.ci_hi);
});

test('R-baseline case 2 (heterogeneous k=3): PM=DL=0.24, Q=50, I²=96%', () => {
  const c = R_BASE.case_2_heterogeneous_three_cohort;
  const pm = PRED._internal.paule_mandel(c.input.yi, c.input.vi);
  const hk = PRED._internal.hksjCI(pm, c.input.alpha);
  const exp = c.expected_pm_reml;
  assert.ok(Math.abs(pm.tau2 - exp.tau2) < c.tolerance_tau2, 'tau2 ' + pm.tau2);
  assert.ok(Math.abs(pm.mu - exp.mu) < c.tolerance_mu, 'mu ' + pm.mu);
  assert.ok(Math.abs(pm.se_mu - exp.se_mu) < c.tolerance_se_mu, 'se_mu ' + pm.se_mu);
  assert.ok(Math.abs(pm.Q - exp.Q) < 1e-9, 'Q ' + pm.Q);
  const I2 = pm.Q > pm.df ? Math.max(0, (pm.Q - pm.df)/pm.Q) * 100 : 0;
  assert.ok(Math.abs(I2 - exp.I2) < 1e-6, 'I2 ' + I2);
  assert.ok(Math.abs(hk.hksj_factor - exp.hksj_factor) < 1e-9, 'hksj ' + hk.hksj_factor);
  assert.ok(Math.abs(hk.ci_lo - exp.ci_lo_logit_scale) < 1e-3, 'ci_lo ' + hk.ci_lo);
});

test('R-baseline case 3 (real KFRE 6-cohort): frozen logit-C pool', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'prediction_fixtures/kfre_5y_external_validations.json'), 'utf-8'));
  const cohorts = fx.cohorts.map(c => ({
    studlab: c.studlab, C: c.C, C_se: c.C_se,
    cohort_type: c.cohort_type, probast: c.probast
  }));
  const r = PRED.fit(cohorts);
  const exp = R_BASE.case_3_kfre_real_data_6_cohort.expected_engine_output;
  const tol = R_BASE.case_3_kfre_real_data_6_cohort.tolerance;
  assert.equal(r.C_pool.k, exp.k);
  assert.ok(Math.abs(r.C_pool.mu - exp.logit_C_mu) < tol, 'logit_C_mu ' + r.C_pool.mu);
  assert.ok(Math.abs(r.C_pool.se_mu - exp.logit_C_se) < tol, 'logit_C_se ' + r.C_pool.se_mu);
  assert.ok(Math.abs(r.C_pool.C_pool - exp.C_pool) < tol, 'C_pool ' + r.C_pool.C_pool);
  assert.ok(Math.abs(r.C_pool.tau2 - exp.tau2_logit) < tol, 'tau2 ' + r.C_pool.tau2);
  assert.ok(Math.abs(r.C_pool.I2 - exp.I2_pct) < tol * 100, 'I2 ' + r.C_pool.I2);
  assert.ok(Math.abs(r.C_pool.Q - exp.Q) < tol * 100, 'Q ' + r.C_pool.Q);
  assert.ok(Math.abs(r.C_pool.hksj_factor - exp.hksj_factor) < tol * 10, 'hksj ' + r.C_pool.hksj_factor);
  assert.ok(Math.abs(r.C_pool.C_pi_lo - exp.C_pi_lo) < tol, 'C_pi_lo ' + r.C_pool.C_pi_lo);
  assert.ok(Math.abs(r.C_pool.C_pi_hi - exp.C_pi_hi) < tol, 'C_pi_hi ' + r.C_pool.C_pi_hi);
});

test('R-baseline case 3: PROBAST overall rollup matches frozen baseline', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'prediction_fixtures/kfre_5y_external_validations.json'), 'utf-8'));
  const cohorts = fx.cohorts.map(c => ({
    studlab: c.studlab, C: c.C, C_se: c.C_se,
    cohort_type: c.cohort_type, probast: c.probast
  }));
  const r = PRED.fit(cohorts);
  const exp = R_BASE.case_3_kfre_real_data_6_cohort.expected_probast_overall;
  assert.equal(r.probast.overall.low, exp.low);
  assert.equal(r.probast.overall.high, exp.high);
  assert.equal(r.probast.overall.unclear, exp.unclear);
});

test('Real-cohort fixture: consistency with Tangri 2016 IPDMA pooled 5y C', () => {
  // The IPDMA reported pooled 5y C = 0.88 (95% CI 0.86-0.90) across 31 cohorts.
  // Our 6-cohort sub-pool produces a point estimate close to this (0.87) — sanity check.
  const fx = JSON.parse(readFileSync(join(__dirname, 'prediction_fixtures/kfre_5y_external_validations.json'), 'utf-8'));
  const cohorts = fx.cohorts.map(c => ({ studlab: c.studlab, C: c.C, C_se: c.C_se }));
  const r = PRED.fit(cohorts);
  const ipdma_pooled = fx._meta.anchor_metaanalysis.pooled_C_5y;
  // Pooled C should be within 0.05 of the IPDMA pooled value (IPDMA uses different pooling
  // and a different mix of cohorts, so this is a sanity bound not bit-reproducibility).
  assert.ok(Math.abs(r.C_pool.C_pool - ipdma_pooled) < 0.05,
    'pooled C ' + r.C_pool.C_pool + ' vs IPDMA ' + ipdma_pooled);
});

// ───── Edge cases: stress paths through the engine ─────
test('Edge: Hanley-McNeil derivation path matches user-provided SE when both available', () => {
  // If a cohort provides BOTH C_se and n_events/n_nonevents, the engine should prefer C_se.
  // Demonstrate that the discrimination row uses the user-provided SE by constructing a
  // case where the two would diverge sharply.
  const c = { studlab: 'x', C: 0.80, C_se: 0.025, n_events: 100, n_nonevents: 100 };
  const d = PRED._internal.perCohortDiscrimination(c);
  // delta-method SE on logit: 0.025 / (0.8*0.2) = 0.15625
  assert.ok(Math.abs(d.logitC_se - 0.15625) < 1e-6, 'used user SE: ' + d.logitC_se);
});

test('Edge: C very close to 1 (clamp to 1 - 1e-6) does not blow up', () => {
  const c = { studlab: 'extreme', C: 0.9999, C_se: 0.001 };
  const d = PRED._internal.perCohortDiscrimination(c);
  assert.ok(isFinite(d.logitC), 'logitC ' + d.logitC);
  assert.ok(isFinite(d.logitC_se), 'se ' + d.logitC_se);
  assert.ok(d.C_ci_hi <= 1.0, 'CI upper clamped to 1: ' + d.C_ci_hi);
});

test('Edge: calibration slope outside (0.5, 2.0) is still pooled (no implicit clamp)', () => {
  // Some real cohorts report severe miscalibration (slope ~ 0.5 or ~ 2.0).
  // The engine should pool faithfully — clamping is a presentation-layer concern.
  const r = PRED.fit([
    { studlab: 'a', C: 0.75, C_se: 0.02, calib_slope: 0.50, calib_slope_se: 0.10 },
    { studlab: 'b', C: 0.75, C_se: 0.02, calib_slope: 1.95, calib_slope_se: 0.12 },
    { studlab: 'c', C: 0.75, C_se: 0.02, calib_slope: 1.00, calib_slope_se: 0.08 }
  ]);
  assert.ok(isFinite(r.calib_slope_pool.mu));
  assert.equal(r.calib_slope_pool.k, 3);
  // High heterogeneity expected — τ² should be substantial
  assert.ok(r.calib_slope_pool.tau2 > 0.05, 'tau2 ' + r.calib_slope_pool.tau2);
});

test('Edge: near-zero calibration intercept survives REML iteration', () => {
  // Two cohorts at α≈0 should pool to α≈0 with tau²≈0.
  const r = PRED.fit([
    { studlab: 'a', C: 0.75, C_se: 0.02, calib_int: 0.001, calib_int_se: 0.05 },
    { studlab: 'b', C: 0.75, C_se: 0.02, calib_int: -0.001, calib_int_se: 0.05 },
    { studlab: 'c', C: 0.75, C_se: 0.02, calib_int: 0.000, calib_int_se: 0.05 }
  ]);
  assert.ok(Math.abs(r.calib_int_pool.mu) < 0.01, 'mu ' + r.calib_int_pool.mu);
  assert.ok(r.calib_int_pool.tau2 < 0.01, 'tau2 ' + r.calib_int_pool.tau2);
});

test('Edge: HM derivation for tiny n_events (stress)', () => {
  // n_events = 5 should still produce a finite (large) variance.
  const v = PRED._internal.hanleyMcNeilVar(0.75, 5, 50);
  assert.ok(isFinite(v), 'v ' + v);
  assert.ok(v > 0);
  // With only 5 events the variance should be much larger than for 50 events
  const v50 = PRED._internal.hanleyMcNeilVar(0.75, 50, 50);
  assert.ok(v > v50 * 2, 'small-n var > 2× large-n: ' + v + ' vs ' + v50);
});

test('Edge: HM derivation rejects n=0 cleanly (returns NaN)', () => {
  const v = PRED._internal.hanleyMcNeilVar(0.75, 0, 100);
  assert.ok(isNaN(v) || !isFinite(v), 'expected NaN/Inf, got ' + v);
});

test('Edge: O/E with n_observed=0 returns NaN variance (does not divide by zero)', () => {
  const v = PRED._internal.oeLogVar(0, 1000);
  assert.ok(isNaN(v) || !isFinite(v), 'expected NaN/Inf, got ' + v);
});

test('Edge: chi2UpperP boundary q=0 → p=1', () => {
  assert.equal(PRED._internal.chi2UpperP(0, 5), 1);
  assert.equal(PRED._internal.chi2UpperP(-1, 5), 1);
});

test('Edge: tinv at p=0.999 df=5 returns finite large value', () => {
  const t = PRED._internal.tinv(0.999, 5);
  assert.ok(isFinite(t) && t > 5 && t < 10, 't ' + t);
});

test('Edge: exportResults survives null pool fields (optional metrics)', () => {
  const r = PRED.fit([
    { studlab: 'a', C: 0.75, C_se: 0.02 },
    { studlab: 'b', C: 0.75, C_se: 0.02 },
    { studlab: 'c', C: 0.75, C_se: 0.02 }
  ]);
  const exp = PRED.exportResults(r);
  assert.equal(exp.calib_int_pool, null);
  assert.equal(exp.OE_pool, null);
  assert.equal(exp.brier_pool, null);
  // C_pool still present
  assert.ok(exp.C_pool && isFinite(exp.C_pool.C_pool));
});

test('Edge: forest layout omits rows with skip flag', () => {
  // When per_cohort_rows[i].calib_int_row is null (no calibration data), the forest
  // for calibration intercept should skip that cohort but include cohorts that have it.
  const r = PRED.fit([
    { studlab: 'a', C: 0.75, C_se: 0.02, calib_int: 0.0, calib_int_se: 0.05 },
    { studlab: 'b', C: 0.75, C_se: 0.02 /* no calib_int */ },
    { studlab: 'c', C: 0.75, C_se: 0.02, calib_int: 0.1, calib_int_se: 0.05 }
  ]);
  const f = PRED.forest(r);
  // Discrimination: all 3 cohorts + pooled = 4 rows
  assert.equal(f.discrimination.length, 4);
  // Calibration intercept: only cohorts a and c + pooled = 3 rows
  assert.equal(f.calib_int.length, 3);
});

test('Edge: paule_mandel converges within 100 iterations on the KFRE data', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'prediction_fixtures/kfre_5y_external_validations.json'), 'utf-8'));
  // Compute logit-C / vi inputs by hand and run PM directly
  const yi = [], vi = [];
  fx.cohorts.forEach(c => {
    const logitC = Math.log(c.C / (1 - c.C));
    const se_logit = c.C_se / (c.C * (1 - c.C));
    yi.push(logitC); vi.push(se_logit * se_logit);
  });
  const pm = PRED._internal.paule_mandel(yi, vi);
  assert.ok(pm.converged, 'iter=' + pm.iter);
  assert.ok(pm.iter < 100, 'converged in ' + pm.iter + ' iterations');
});

// ───── Run ─────
let pass = 0, fail = 0;
for (const t of tests) {
  try { t.fn(); console.log('PASS', t.name); pass++; }
  catch (e) { console.error('FAIL', t.name, '\n  ', e.message); fail++; }
}
console.log(`\n${pass} pass, ${fail} fail (total ${tests.length})`);
process.exit(fail === 0 ? 0 : 1);
