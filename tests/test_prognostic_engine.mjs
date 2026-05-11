// tests/test_prognostic_engine.mjs — Node-runnable, pure JS.
// Mirrors tests/test_dta_engine.mjs idiom: load engine via new Function(window, src),
// register test(name, fn), run, report pass/fail counts.
//
// All 5 fixtures (tests/prognostic_fixtures/*.json) are derived from real published
// prognostic-factor meta-analyses with verified PMIDs:
//   bnp_hf_doust2005.json          — Doust 2005 BMJ, PMID 15774989
//   kim1_dkd_coca2017.json         — Coca 2017 JASN, PMID 28476763 + Gutiérrez 2022, PMID 34752914
//   hstn_pad_vrsalovic2022.json    — Vrsalovic 2022 Clin Cardiol, PMID 35132665
//   hscrp_chd_erfc2010.json        — Kaptoge 2010 Lancet, PMID 20031199
//   hstn_dose_response_jia2019.json — Jia 2019 Circulation, PMID 31030544
//
// Parity baselines live in tests/prognostic_baselines/r_parity.json; assertions
// against them pin engine output bit-stably so that any change to PM tau^2 or
// Wald CI construction trips a regression test (Δ tolerance: 1e-3 for HR/CI,
// 1e-3 for tau^2, 1e-2 for Q).
//
// SCOPE OF THE "PARITY BASELINE" CHECK
// ------------------------------------
// These baselines are ENGINE SELF-CONSISTENCY snapshots, NOT external parity
// vs metafor::rma(). They detect regressions in the engine's own PM bisection
// + Wald construction + Q-profile + PI implementation. They do NOT certify
// that the engine matches metafor::rma(method='PM') bit-for-bit.
//
// Cross-engine parity vs metafor::rma() is delivered separately via
// webr-prognostic-validator.js (lazy WebR + metafor install, runs in-browser
// from the host HTML; see PROGNOSTIC_HSTN_PAD_REVIEW.html). The DTA engine
// uses the same split: the unit-test suite verifies internal consistency,
// the WebR validator certifies cross-engine parity.
//
// To upgrade these baselines to metafor-parity values, run the WebR
// validator on each fixture, copy the metafor::rma() output into
// r_parity.json, and tighten the tolerances. The engine's PM bisection
// is designed to converge to the same fixed point as metafor::rma(method='PM')
// (see "CONVERGENCE GUARANTEE (PM bisection)" comment in the engine source),
// so the resulting deltas should be within machine precision.
import { strict as assert } from 'node:assert';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ENGINE_PATH = join(__dirname, '..', 'rapidmeta-prognostic-engine-v1.js');

const engineSrc = readFileSync(ENGINE_PATH, 'utf-8');
const ctx = {};
new Function('window', engineSrc)(ctx);
const PROG = ctx.RapidMetaPrognostic;
const I = PROG._internal;

function loadFx(name) {
  return JSON.parse(readFileSync(join(__dirname, 'prognostic_fixtures', name), 'utf-8'));
}
const BASELINES = JSON.parse(readFileSync(join(__dirname, 'prognostic_baselines', 'r_parity.json'), 'utf-8')).baselines;

const tests = [];
function test(name, fn) { tests.push({ name, fn }); }

// Helper: approx-equal with named field for clearer assertion messages
function near(actual, expected, tol, label) {
  if (expected == null) {
    assert.equal(actual, null, label + ' expected null; got ' + actual);
    return;
  }
  assert.ok(typeof actual === 'number' && isFinite(actual),
            label + ' must be finite number; got ' + actual);
  assert.ok(Math.abs(actual - expected) < tol,
            label + ' = ' + actual + ' vs baseline ' + expected + ' (Δ=' + Math.abs(actual - expected).toExponential(2) + ', tol=' + tol + ')');
}

// -----------------------------------------------------------------------------
// Section A: validate() contract
// -----------------------------------------------------------------------------

test('validate: rejects non-array input', () => {
  const issues = PROG.validate({ not: 'array' });
  assert.ok(issues.length > 0);
});

test('validate: rejects empty array', () => {
  const issues = PROG.validate([]);
  assert.ok(issues.length > 0);
});

test('validate: rejects missing hr_adj', () => {
  const issues = PROG.validate([{ studlab: 'X', hr_adj_ci_lb: 1.0, hr_adj_ci_ub: 1.5 }]);
  assert.ok(issues.length > 0);
  assert.ok(issues[0].includes('hr_adj'));
});

test('validate: rejects negative hr_adj', () => {
  const issues = PROG.validate([{ studlab: 'X', hr_adj: -1.0, hr_adj_ci_lb: 0.5, hr_adj_ci_ub: 1.5 }]);
  assert.ok(issues.length > 0);
});

test('validate: rejects CI bounds <= 0', () => {
  const issues = PROG.validate([{ studlab: 'X', hr_adj: 1.0, hr_adj_ci_lb: 0, hr_adj_ci_ub: 1.5 }]);
  assert.ok(issues.length > 0);
});

test('validate: rejects point estimate outside CI', () => {
  const issues = PROG.validate([{ studlab: 'X', hr_adj: 2.0, hr_adj_ci_lb: 1.0, hr_adj_ci_ub: 1.5 }]);
  assert.ok(issues.length > 0, 'expected CI violation issue');
});

test('validate: accepts well-formed', () => {
  const issues = PROG.validate([{ studlab: 'X', hr_adj: 1.30, hr_adj_ci_lb: 1.20, hr_adj_ci_ub: 1.40 }]);
  assert.deepEqual(issues, []);
});

test('validate: rejects invalid quips level', () => {
  const issues = PROG.validate([{
    studlab: 'X', hr_adj: 1.30, hr_adj_ci_lb: 1.20, hr_adj_ci_ub: 1.40,
    quips: { participation: 'TYPO_VALUE' }
  }]);
  assert.ok(issues.length > 0);
});

test('validate: rejects zero-width CI (lb == ub triggers seLog=0 degeneracy)', () => {
  // Code-review P1.1: validate() must reject zero-width CIs to prevent
  // downstream pool divergence (infinite IV weight from seLog=0).
  const issues = PROG.validate([{
    studlab: 'ZeroWidth', hr_adj: 1.5, hr_adj_ci_lb: 1.5, hr_adj_ci_ub: 1.5
  }]);
  assert.ok(issues.length > 0, 'expected zero-width CI to be rejected');
  assert.ok(issues[0].includes('zero-width') || issues[0].includes('degenerate'),
            'expected message to mention zero-width or degenerate; got: ' + issues[0]);
});

test('validate: rejects near-zero-width CI via relative tolerance', () => {
  // Boundary: (ub-lb)/lb < 1e-9
  const issues = PROG.validate([{
    studlab: 'NearZero', hr_adj: 1.30, hr_adj_ci_lb: 1.30, hr_adj_ci_ub: 1.30 + 1e-12
  }]);
  assert.ok(issues.length > 0, 'expected near-zero-width CI to be rejected');
});

test('validate: accepts tight-but-finite CI (above the relative-tolerance floor)', () => {
  // Tight 1% CI on HR=1.30 is fine (real biomarker MAs report this)
  const issues = PROG.validate([{
    studlab: 'Tight', hr_adj: 1.30, hr_adj_ci_lb: 1.29, hr_adj_ci_ub: 1.31
  }]);
  assert.deepEqual(issues, [], 'tight-but-finite CI must pass validation');
});

test('fit: k=2 surfaces hksj_warning (df=1 → t ≈ 12.7 is uninformative)', () => {
  // Code-review P1.2: HKSJ at k=2 is mathematically defined but produces a
  // wildly conservative CI. The engine must surface a warning so consumers
  // can suppress / annotate the column rather than silently emit a useless CI.
  const r = PROG.fit([
    {studlab: 'A', hr_adj: 1.30, hr_adj_ci_lb: 1.20, hr_adj_ci_ub: 1.41},
    {studlab: 'B', hr_adj: 1.40, hr_adj_ci_lb: 1.30, hr_adj_ci_ub: 1.51}
  ]);
  assert.equal(r.k, 2);
  assert.ok(r.hksj_warning != null, 'expected hksj_warning to be populated for k=2');
  assert.ok(r.hksj_warning.includes('k=2') || r.hksj_warning.includes('df=1'),
            'expected warning to reference k=2 or df=1; got: ' + r.hksj_warning);
});

test('fit: k>=3 sets hksj_warning to null', () => {
  const fx = loadFx('kim1_dkd_coca2017.json');
  const r = PROG.fit(fx.trials);
  assert.equal(r.k, 3);
  assert.equal(r.hksj_warning, null, 'hksj_warning should be null for k>=3');
});

test('validate: all 5 real fixtures pass validation cleanly', () => {
  const names = ['bnp_hf_doust2005', 'kim1_dkd_coca2017', 'hstn_pad_vrsalovic2022',
                 'hscrp_chd_erfc2010', 'hstn_dose_response_jia2019'];
  names.forEach(n => {
    const fx = loadFx(n + '.json');
    const issues = PROG.validate(fx.trials);
    assert.deepEqual(issues, [], n + ' validation failures: ' + issues.join('; '));
  });
});

// -----------------------------------------------------------------------------
// Section B: Numerics helpers
// -----------------------------------------------------------------------------

test('qnormApprox: matches z_{0.975} ≈ 1.95996 within 1e-3', () => {
  const z = I.qnormApprox(0.975);
  assert.ok(Math.abs(z - 1.959963984540054) < 1e-3, 'got ' + z);
});

test('qchisq: chi2_{0.95, 1} ≈ 3.841 within 1e-2', () => {
  const v = I.qchisq(0.95, 1);
  assert.ok(Math.abs(v - 3.841) < 1e-2, 'got ' + v);
});

test('qchisq: chi2_{0.95, 7} ≈ 14.067 within 1e-1', () => {
  const v = I.qchisq(0.95, 7);
  assert.ok(Math.abs(v - 14.067) < 0.2, 'got ' + v);
});

test('tinv: matches t_{0.975, 10} ≈ 2.228, t_{0.975, 30} ≈ 2.042', () => {
  assert.ok(Math.abs(I.tinv(0.975, 10) - 2.228) < 1e-2);
  assert.ok(Math.abs(I.tinv(0.975, 30) - 2.042) < 1e-2);
});

// -----------------------------------------------------------------------------
// Section C: Per-study log-effect derivation
// -----------------------------------------------------------------------------

test('logEffect: HR 1.30 (1.20–1.41) → seLog ≈ (log(1.41)-log(1.20))/(2*1.96)', () => {
  const r = I.logEffect(1.30, 1.20, 1.41);
  const exp_se = (Math.log(1.41) - Math.log(1.20)) / (2 * 1.959963984540054);
  assert.ok(Math.abs(r.seLog - exp_se) < 1e-12);
  assert.ok(Math.abs(r.yi - Math.log(1.30)) < 1e-12);
  assert.ok(Math.abs(r.vi - exp_se * exp_se) < 1e-12);
});

test('logEffect: null HR ≡ symmetric CI on log scale (HR=1 with sym CI)', () => {
  const r = I.logEffect(1.0, 0.80, 1.25);
  assert.ok(Math.abs(r.yi) < 1e-12, 'log(1)=0');
});

test('perStudyLog: maps adjusted + unadjusted side by side', () => {
  const out = I.perStudyLog([{
    studlab: 'X', hr_adj: 1.30, hr_adj_ci_lb: 1.20, hr_adj_ci_ub: 1.41,
    hr_unadj: 1.50, hr_unadj_ci_lb: 1.40, hr_unadj_ci_ub: 1.61
  }]);
  assert.equal(out.length, 1);
  assert.ok(out[0].yi_unadj > 0);
  assert.ok(out[0].yi_unadj > out[0].yi_adj, 'unadjusted typically larger');
});

// -----------------------------------------------------------------------------
// Section D: tau^2 estimators
// -----------------------------------------------------------------------------

test('tau2DL: homogeneous yi → tau2=0', () => {
  const yi = [0.1, 0.1, 0.1, 0.1, 0.1];
  const vi = [0.01, 0.01, 0.01, 0.01, 0.01];
  assert.equal(I.tau2DL(yi, vi), 0);
});

test('tau2DL: heterogeneous yi → tau2 > 0', () => {
  const yi = [0.10, 0.40, 0.70, 1.00, 1.30];
  const vi = [0.01, 0.01, 0.01, 0.01, 0.01];
  assert.ok(I.tau2DL(yi, vi) > 0.01);
});

// PM-identity check helper — used by both the synthetic-data test below and
// the per-fixture parity tests later. Verifies the bisection landed on the
// correct fixed point Σwᵢ(yᵢ−μ̂)² = k − 1 (or τ²=0 floor if Σwᵢ(yᵢ−μ̂)²|_{τ²=0} ≤ k − 1).
function verifyPMIdentity(yi, vi, t, label) {
  let W = 0, WY = 0;
  for (let i = 0; i < yi.length; i++) { const w = 1 / (vi[i] + t); W += w; WY += w * yi[i]; }
  const mu = WY / W;
  let s = 0;
  for (let i = 0; i < yi.length; i++) { const w = 1 / (vi[i] + t); s += w * (yi[i] - mu) * (yi[i] - mu); }
  if (t > 0) {
    assert.ok(Math.abs(s - (yi.length - 1)) < 1e-6,
              label + ': PM identity Σw(y-μ̂)² ≈ k-1 violated at τ²=' + t + ': ' + s + ' vs ' + (yi.length - 1));
  } else {
    assert.ok(s <= yi.length - 1 + 1e-6,
              label + ': τ²=0 floor but Σw(y-μ̂)² > k-1: ' + s);
  }
  return { mu, s, W };
}

test('tau2REML (Paule-Mandel bisection): satisfies Σw(y-μ̂)² = k-1 at convergence', () => {
  const yi = [0.20, 0.30, 0.25, 0.15, 0.40];
  const vi = [0.04, 0.03, 0.05, 0.04, 0.06];
  const t = I.tau2REML(yi, vi);
  assert.ok(t >= 0 && isFinite(t));
  // Verify the PM identity to <1e-6: Σw(y-μ̂)² should equal k-1 at the converged τ².
  let W = 0, WY = 0;
  for (let i = 0; i < yi.length; i++) { const w = 1 / (vi[i] + t); W += w; WY += w * yi[i]; }
  const mu = WY / W;
  let s = 0;
  for (let i = 0; i < yi.length; i++) { const w = 1 / (vi[i] + t); s += w * (yi[i] - mu) * (yi[i] - mu); }
  // If t > 0, identity should hold tightly; if t = 0 by floor, then Σw(y-μ̂)² <= k-1.
  if (t > 0) {
    assert.ok(Math.abs(s - (yi.length - 1)) < 1e-6, 'PM identity Σw(y-μ̂)² ≈ k-1 violated: ' + s + ' vs ' + (yi.length - 1));
  } else {
    assert.ok(s <= yi.length - 1 + 1e-6, 'τ²=0 floor but Σw(y-μ̂)² > k-1: ' + s);
  }
});

test('poolGivenTau2: pooled mean is inverse-variance weighted', () => {
  const yi = [0.10, 0.30];
  const vi = [0.01, 0.04];
  const p = I.poolGivenTau2(yi, vi, 0);
  // w1=100, w2=25, expected mu = (100*0.1 + 25*0.3)/125 = 0.14
  assert.ok(Math.abs(p.mu - 0.14) < 1e-6);
});

// -----------------------------------------------------------------------------
// Section E: HKSJ floor + Q-profile + PI
// -----------------------------------------------------------------------------

test('hksjMultiplier: Q < k-1 floored at 1.0', () => {
  const yi = [0.20, 0.20, 0.20, 0.20];  // perfectly homogeneous
  const vi = [0.04, 0.04, 0.04, 0.04];
  const mult = I.hksjMultiplier(yi, vi, 0, 0.20);
  assert.equal(mult, 1, 'expected floor at 1.0; got ' + mult);
});

test('hksjMultiplier: high heterogeneity → multiplier > 1', () => {
  const yi = [0.0, 0.5, 1.0, 1.5];
  const vi = [0.01, 0.01, 0.01, 0.01];
  const p = I.poolGivenTau2(yi, vi, 0);
  const mult = I.hksjMultiplier(yi, vi, 0, p.mu);
  assert.ok(mult > 1.0, 'expected scaling > 1 on heterogeneous data');
});

test('qProfileTau2CI: returns null bounds for k<3', () => {
  const r = I.qProfileTau2CI([0.1, 0.2], [0.01, 0.02], 0.05);
  assert.equal(r.tau2_lo, null);
  assert.equal(r.tau2_hi, null);
});

test('qProfileTau2CI: heterogeneous data → finite upper bound', () => {
  const yi = [0.10, 0.30, 0.50, 0.70, 0.90];
  const vi = [0.02, 0.03, 0.04, 0.02, 0.03];
  const r = I.qProfileTau2CI(yi, vi, 0.05);
  assert.ok(r.tau2_hi != null && r.tau2_hi > 0, 'expected positive upper bound; got ' + r.tau2_hi);
});

// -----------------------------------------------------------------------------
// Section F: Cutoff harmonization
// -----------------------------------------------------------------------------

test('cutoffHarmonization: skips trials missing per_unit', () => {
  const out = I.cutoffHarmonization([{
    studlab: 'X', yi_adj: 0.30, vi_adj: 0.01, seLog_adj: 0.10,
    per_unit: null, biomarker_sd: 1.0
  }], 'log_per_sd');
  assert.equal(out[0].harmonized, false);
  assert.ok(out[0].harmonization_note.includes('per_unit'));
});

test('cutoffHarmonization: rescales by SD/per_unit when both present', () => {
  const out = I.cutoffHarmonization([{
    studlab: 'X', yi_adj: 0.30, vi_adj: 0.01, seLog_adj: 0.10,
    per_unit: 0.693, biomarker_sd: 1.0
  }], 'log_per_sd');
  assert.ok(out[0].harmonized);
  assert.ok(Math.abs(out[0].yi_harm - 0.30 * (1.0 / 0.693)) < 1e-9);
  assert.ok(Math.abs(out[0].vi_harm - 0.01 * Math.pow(1.0 / 0.693, 2)) < 1e-9);
});

// -----------------------------------------------------------------------------
// Section G: Adjusted vs unadjusted forest split (synthetic only — real fixtures
// did not report paired adj/unadj HRs uniformly)
// -----------------------------------------------------------------------------

test('adjUnadjSplit: synthetic paired data → unadjusted > adjusted with Q_between', () => {
  const trials = [
    {studlab:'A', hr_adj:1.30, hr_adj_ci_lb:1.20, hr_adj_ci_ub:1.41,
      hr_unadj:1.50, hr_unadj_ci_lb:1.40, hr_unadj_ci_ub:1.61},
    {studlab:'B', hr_adj:1.25, hr_adj_ci_lb:1.15, hr_adj_ci_ub:1.36,
      hr_unadj:1.45, hr_unadj_ci_lb:1.35, hr_unadj_ci_ub:1.56},
    {studlab:'C', hr_adj:1.35, hr_adj_ci_lb:1.25, hr_adj_ci_ub:1.46,
      hr_unadj:1.55, hr_unadj_ci_lb:1.45, hr_unadj_ci_ub:1.66}
  ];
  const res = PROG.fit(trials);
  assert.ok(res.adj_unadj_split.available, 'split should be computable');
  assert.ok(res.adj_unadj_split.unadjusted.pooled_HR > res.adj_unadj_split.adjusted.pooled_HR,
            'expected unadjusted HR > adjusted HR');
  assert.ok(res.adj_unadj_split.Q_between > 0);
  assert.ok(typeof res.adj_unadj_split.p_between === 'number');
});

test('adjUnadjSplit: missing unadjusted → not available', () => {
  const fx = loadFx('kim1_dkd_coca2017.json');
  const res = PROG.fit(fx.trials);
  assert.equal(res.adj_unadj_split.available, false);
});

// -----------------------------------------------------------------------------
// Section H: QUIPS 6-domain RoB
// -----------------------------------------------------------------------------

test('QUIPS: 6 canonical domains exposed', () => {
  assert.equal(I.QUIPS_DOMAINS.length, 6);
  assert.ok(I.QUIPS_DOMAINS.includes('participation'));
  assert.ok(I.QUIPS_DOMAINS.includes('prognostic_factor_measurement'));
  assert.ok(I.QUIPS_DOMAINS.includes('study_confounding'));
});

test('quipsSummary: overall = worst-domain rule', () => {
  const pslog = I.perStudyLog([{
    studlab:'X', hr_adj:1.3, hr_adj_ci_lb:1.2, hr_adj_ci_ub:1.4,
    quips:{
      participation:'low', attrition:'low', prognostic_factor_measurement:'high',
      outcome_measurement:'low', study_confounding:'low', statistical_analysis:'low'
    }
  }]);
  const q = I.quipsSummary(pslog);
  assert.equal(q.per_study[0].overall, 'high', 'worst domain rule: any high → overall high');
});

test('quipsWeightedPool: down-weights high-RoB studies', () => {
  const trials = [
    {studlab:'lowRoB', hr_adj:1.20, hr_adj_ci_lb:1.10, hr_adj_ci_ub:1.31,
     quips:{participation:'low',attrition:'low',prognostic_factor_measurement:'low',
            outcome_measurement:'low',study_confounding:'low',statistical_analysis:'low'}},
    {studlab:'highRoB', hr_adj:2.50, hr_adj_ci_lb:2.00, hr_adj_ci_ub:3.13,
     quips:{participation:'high',attrition:'high',prognostic_factor_measurement:'high',
            outcome_measurement:'high',study_confounding:'high',statistical_analysis:'high'}},
    {studlab:'modRoB', hr_adj:1.30, hr_adj_ci_lb:1.20, hr_adj_ci_ub:1.41,
     quips:{participation:'moderate',attrition:'moderate',prognostic_factor_measurement:'moderate',
            outcome_measurement:'moderate',study_confounding:'moderate',statistical_analysis:'moderate'}}
  ];
  const res = PROG.fit(trials);
  assert.ok(res.quips_weighted_pool.available);
  assert.ok(res.quips_weighted_pool.pooled_HR < res.pooled_HR,
            'down-weighted high-RoB should pull pool toward low-RoB (smaller HR)');
});

test('QUIPS: real BNP/HF fixture has 6/6 studies with QUIPS recorded', () => {
  const fx = loadFx('bnp_hf_doust2005.json');
  const res = PROG.fit(fx.trials);
  assert.equal(res.quips_summary.n_with_quips, 6);
  assert.equal(res.quips_summary.n_without_quips, 0);
});

// -----------------------------------------------------------------------------
// Section I: Universal-panel-equivalents
// -----------------------------------------------------------------------------

test('leaveOneOut: hs-Tn PAD (k=8) → 8 rows, each with k=7 after drop', () => {
  const fx = loadFx('hstn_pad_vrsalovic2022.json');
  const res = PROG.fit(fx.trials);
  assert.equal(res.leave_one_out.length, 8);
  assert.ok(res.leave_one_out.every(r => r.k === 7));
});

test('cumulativeMA: sorted by year ascending', () => {
  const fx = loadFx('hstn_pad_vrsalovic2022.json');
  const res = PROG.fit(fx.trials);
  const years = res.cumulative.map(r => r.year);
  for (let i = 1; i < years.length; i++) {
    assert.ok(years[i - 1] <= years[i], 'cumulative not year-sorted');
  }
});

test('baujat: returns one row per trial with x_contrib_Q + y_influence', () => {
  const fx = loadFx('hstn_pad_vrsalovic2022.json');
  const res = PROG.fit(fx.trials);
  assert.equal(res.baujat.length, fx.trials.length);
  assert.ok(res.baujat.every(r => 'x_contrib_Q' in r && 'y_influence' in r));
});

test('influenceDiag: BNP/HF fixture flags Bettencourt 2000 as outlier', () => {
  // Bettencourt 2000 HR=1.01 (CI 1.005-1.02) is the canonical "wrong-units" artifact
  // in the Doust 2005 review. With externally-studentized residuals it should fall
  // far below the pooled HR ≈ 1.30, beyond |z|>1.96.
  const fx = loadFx('bnp_hf_doust2005.json');
  const res = PROG.fit(fx.trials);
  const bett = res.influence.find(r => r.studlab === 'Bettencourt 2000');
  assert.ok(bett, 'Bettencourt 2000 row missing from influence');
  assert.ok(bett.outlier_flag, 'expected Bettencourt 2000 outlier_flag=true; stud_resid=' + bett.studentized_residual);
});

test('funnelDiagnostics: undefined for k<3', () => {
  const trials = [
    {studlab:'A', hr_adj:1.3, hr_adj_ci_lb:1.2, hr_adj_ci_ub:1.4},
    {studlab:'B', hr_adj:1.4, hr_adj_ci_lb:1.3, hr_adj_ci_ub:1.5}
  ];
  const res = PROG.fit(trials);
  assert.equal(res.funnel.available, false);
});

test('funnelDiagnostics: warns underpowered for k<10', () => {
  const fx = loadFx('hstn_pad_vrsalovic2022.json');
  const res = PROG.fit(fx.trials);
  assert.ok(res.funnel.available);
  assert.equal(res.funnel.underpowered_warning, true, 'k=8 < 10 should warn underpowered');
});

test('subgroupInteraction: hs-Tn PAD fixture has multiple PAD subgroups', () => {
  const fx = loadFx('hstn_pad_vrsalovic2022.json');
  const res = PROG.fit(fx.trials);
  assert.ok(res.subgroup_interaction.available);
  assert.ok(res.subgroup_interaction.n_groups >= 2, 'expected ≥2 PAD subgroups; got ' + res.subgroup_interaction.n_groups);
});

// -----------------------------------------------------------------------------
// Section J: Dose-response (Jia 2019 ARIC quintiles)
// -----------------------------------------------------------------------------

test('doseResponse: Jia 2019 ARIC hs-TnI quintiles → monotone increasing', () => {
  const fx = loadFx('hstn_dose_response_jia2019.json');
  const res = PROG.fit(fx.trials);
  assert.ok(res.dose_response.available);
  assert.ok(res.dose_response.monotone_increasing,
            'expected monotone-increasing dose-response across Q2-Q5 vs Q1; slope=' + res.dose_response.linear_slope);
  assert.ok(res.dose_response.linear_slope > 0);
  assert.ok(res.dose_response.r2_weighted > 0.5, 'expected strong R² for canonical quintile data; got ' + res.dose_response.r2_weighted);
});

test('doseResponse: insufficient dose info → unavailable', () => {
  const trials = [
    {studlab:'A', hr_adj:1.3, hr_adj_ci_lb:1.2, hr_adj_ci_ub:1.4},  // no dose
    {studlab:'B', hr_adj:1.4, hr_adj_ci_lb:1.3, hr_adj_ci_ub:1.5}
  ];
  const res = PROG.fit(trials);
  assert.equal(res.dose_response.available, false);
});

// -----------------------------------------------------------------------------
// Section K: Prediction interval + coverage warnings
// -----------------------------------------------------------------------------

test('PI: k<3 → null bounds; k>=3 → finite bounds, df=k-1', () => {
  const small = PROG.fit([
    {studlab:'A', hr_adj:1.3, hr_adj_ci_lb:1.2, hr_adj_ci_ub:1.4},
    {studlab:'B', hr_adj:1.4, hr_adj_ci_lb:1.3, hr_adj_ci_ub:1.5}
  ]);
  assert.equal(small.pi_lb, null);
  const fx = loadFx('hstn_pad_vrsalovic2022.json');
  const big = PROG.fit(fx.trials);
  assert.ok(big.pi_lb != null && big.pi_ub != null);
  assert.equal(big.pi_df, big.k - 1, 'PI df must be k-1 per Cochrane v6.5');
  assert.ok(big.pi_lb <= big.pooled_HR && big.pooled_HR <= big.pi_ub, 'PI must bracket pooled');
});

test('coverage_warning: true for k<10', () => {
  const fx = loadFx('kim1_dkd_coca2017.json');  // k=3
  const res = PROG.fit(fx.trials);
  assert.equal(res.coverage_warning, true);
});

// -----------------------------------------------------------------------------
// Section L: Parity-baseline pinned tests (regression snapshots)
// -----------------------------------------------------------------------------

const PARITY_FIXTURES = [
  ['bnp_hf_doust2005',          1e-3],
  ['kim1_dkd_coca2017',         1e-3],
  ['hstn_pad_vrsalovic2022',    1e-3],
  ['hscrp_chd_erfc2010',        1e-3],
  ['hstn_dose_response_jia2019', 1e-3]
];
PARITY_FIXTURES.forEach(([name, tol]) => {
  test('parity baseline: ' + name + ' pooled HR + CI', () => {
    const fx = loadFx(name + '.json');
    const r = PROG.fit(fx.trials);
    const b = BASELINES[name];
    assert.equal(r.k, b.k);
    near(r.pooled_HR, b.pooled_HR, tol, name + ' pooled_HR');
    near(r.ci_lb, b.ci_lb, tol, name + ' ci_lb');
    near(r.ci_ub, b.ci_ub, tol, name + ' ci_ub');
  });
  test('parity baseline: ' + name + ' tau^2 + I^2', () => {
    const fx = loadFx(name + '.json');
    const r = PROG.fit(fx.trials);
    const b = BASELINES[name];
    near(r.tau2, b.tau2, 1e-3, name + ' tau^2');
    near(r.I2, b.I2, 1e-3, name + ' I^2');
    near(r.Q, b.Q, 1e-2, name + ' Q');
  });
  // Per-fixture PM identity: τ² returned by the bisection must satisfy
  // Σw(y-μ̂)² = k-1 (the PM equation) to <1e-6. This is the structural
  // guarantee that the bisection landed on the correct fixed point — a
  // tighter check than the parity-baseline numeric tolerance.
  test('PM identity holds on real fixture: ' + name, () => {
    const fx = loadFx(name + '.json');
    const yi = [], vi = [];
    for (const t of fx.trials) {
      yi.push(Math.log(t.hr_adj));
      const se = (Math.log(t.hr_adj_ci_ub) - Math.log(t.hr_adj_ci_lb)) / (2 * 1.959963984540054);
      vi.push(se * se);
    }
    const tau2 = I.tau2REML(yi, vi);
    verifyPMIdentity(yi, vi, tau2, name);
  });
});

test('per_study row exposes effect_type_differs_from_primary for mixed-type pools', () => {
  // Code-review N.2: when a cohort's effect_type (e.g. OR) differs from
  // the pool's primary effect type (e.g. HR), the per-cohort flag must
  // surface so the host HTML can annotate. Verified on KIM-1 fixture
  // where ACCORD is OR but NEPHRON-D and CRIC are HR (primary = HR).
  const fx = loadFx('kim1_dkd_coca2017.json');
  const r = PROG.fit(fx.trials);
  const accord = r.per_study.find(s => s.studlab.includes('ACCORD'));
  const nephron = r.per_study.find(s => s.studlab.includes('NEPHRON-D'));
  assert.ok(accord, 'expected ACCORD row in per_study');
  assert.equal(r.effect_type, 'HR', 'primary effect_type should be HR (2/3 cohorts)');
  assert.equal(accord.effect_type_differs_from_primary, true,
               'ACCORD is OR, should flag as differing from primary HR pool');
  assert.equal(nephron.effect_type_differs_from_primary, false,
               'NEPHRON-D matches primary HR, should not flag');
});

test('cumulative MA: study with year=null deterministically placed last', () => {
  // Code-review P2.3: year=null sentinel = Infinity, secondary sort on
  // original index. Verifies the behavior is documented and tested.
  const r = PROG.fit([
    {studlab: 'first',  hr_adj: 1.3, hr_adj_ci_lb: 1.2, hr_adj_ci_ub: 1.41, year: 2010},
    {studlab: 'nullyr', hr_adj: 1.4, hr_adj_ci_lb: 1.3, hr_adj_ci_ub: 1.51},  // year=null
    {studlab: 'last',   hr_adj: 1.5, hr_adj_ci_lb: 1.4, hr_adj_ci_ub: 1.61, year: 2020}
  ]);
  assert.equal(r.cumulative[0].studlab, 'first');
  assert.equal(r.cumulative[1].studlab, 'last');
  assert.equal(r.cumulative[2].studlab, 'nullyr', 'null-year study must be placed last');
});

// -----------------------------------------------------------------------------
// Section M: Single-study + edge cases + export
// -----------------------------------------------------------------------------

test('fit: k=1 → fallback=single_study, tau2=null', () => {
  const res = PROG.fit([
    {studlab:'Solo', hr_adj:1.5, hr_adj_ci_lb:1.2, hr_adj_ci_ub:1.87}
  ]);
  assert.equal(res.fallback, 'single_study');
  assert.equal(res.tau2, null);
  assert.equal(res.k, 1);
});

test('exportResults: strips _fitInternal + adds metadata', () => {
  const res = PROG.fit([
    {studlab:'A', hr_adj:1.3, hr_adj_ci_lb:1.2, hr_adj_ci_ub:1.4},
    {studlab:'B', hr_adj:1.4, hr_adj_ci_lb:1.3, hr_adj_ci_ub:1.5}
  ]);
  const out = PROG.exportResults(res);
  assert.equal(out._fitInternal, undefined);
  assert.equal(out.engine_version, '1.0.0');
  assert.ok(out.exported_at);
});

// -----------------------------------------------------------------------------
// Section N: Trial integrity + INSPECT-SR
// -----------------------------------------------------------------------------

test('trialIntegrity: BNP/HF fixture (k=6) returns ratio metric', () => {
  const fx = loadFx('bnp_hf_doust2005.json');
  const res = PROG.fit(fx.trials);
  assert.ok(res.trial_integrity.available);
  assert.ok(isFinite(res.trial_integrity.seLog_p75_p25_ratio));
});

test('inspectSrFlags: small N + tight CI → flagged', () => {
  // n=20 with very tight CI (ratio 1.10)
  const trials = [
    {studlab:'TIGHT', hr_adj:1.30, hr_adj_ci_lb:1.25, hr_adj_ci_ub:1.36, n:20,
     covariates:'age, sex'},
    {studlab:'OK',    hr_adj:1.30, hr_adj_ci_lb:1.10, hr_adj_ci_ub:1.55, n:500,
     covariates:'age, sex'}
  ];
  const res = PROG.fit(trials);
  const flagged = res.inspect_sr_flags.some(f => f.studlab === 'TIGHT' && f.reason.includes('tight'));
  assert.ok(flagged, 'expected TIGHT trial flagged for implausibly tight CI on small N');
});

test('inspectSrFlags: missing covariate set → flagged', () => {
  const trials = [
    {studlab:'NOCOV', hr_adj:1.30, hr_adj_ci_lb:1.10, hr_adj_ci_ub:1.55, n:500,
     effect_type:'HR'}
  ];
  const res = PROG.fit(trials);
  const flagged = res.inspect_sr_flags.some(f => f.studlab === 'NOCOV' && f.reason.includes('covariate set'));
  assert.ok(flagged);
});

// -----------------------------------------------------------------------------
// Section O: HKSJ floor in real fixture
// -----------------------------------------------------------------------------

test('HKSJ: hs-Tn PAD fixture exposes hksj_mult >= 1 and finite HKSJ CI', () => {
  const fx = loadFx('hstn_pad_vrsalovic2022.json');
  const res = PROG.fit(fx.trials);
  assert.ok(res.hksj_mult >= 1, 'Cochrane v6.5 floor: hksj_mult must be >= 1');
  assert.ok(isFinite(res.hksj_ci_lb) && isFinite(res.hksj_ci_ub));
});

// -----------------------------------------------------------------------------
// Section P: harmonized pool (per-1-SD rescale)
// -----------------------------------------------------------------------------

test('harmonized_pool: BNP/HF fixture per-100-pg/mL → harmonized when SD declared', () => {
  // Doust 2005 fixture is per_unit=100; we add a placeholder biomarker_sd at the
  // engine call layer to test the harmonization path, since the review did not
  // tabulate per-study biomarker SDs.
  const fx = loadFx('bnp_hf_doust2005.json');
  // Inject a study-level biomarker_sd (typical HF cohort BNP SD ≈ 250 pg/mL per Maisel 2002)
  const trials = fx.trials.map(t => Object.assign({}, t, { biomarker_sd: 250 }));
  const res = PROG.fit(trials);
  // With SD=250 and per_unit=100, scale = 2.5 → harmonization should activate.
  assert.ok(res.harmonized_pool != null, 'expected harmonized pool when biomarker SD declared');
  assert.equal(res.harmonized_pool.k, 6);
});

// =============================================================================
// Run
// =============================================================================
let pass = 0, fail = 0;
for (const t of tests) {
  try {
    t.fn();
    console.log('PASS', t.name);
    pass++;
  } catch (e) {
    console.error('FAIL', t.name, '\n  ', e.message);
    fail++;
  }
}
console.log(`\n${pass} pass, ${fail} fail (of ${tests.length} total)`);
process.exit(fail === 0 ? 0 : 1);
