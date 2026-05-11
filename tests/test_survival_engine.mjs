// tests/test_survival_engine.mjs — Node-runnable, pure JS
// Mirrors tests/test_dta_engine.mjs. Target: ≥35 tests beating DTA's 31-count.
import { strict as assert } from 'node:assert';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ENGINE_PATH = join(__dirname, '..', 'rapidmeta-survival-engine-v1.js');

const engineSrc = readFileSync(ENGINE_PATH, 'utf-8');
const ctx = {};
new Function('window', engineSrc)(ctx);
const SURV = ctx.RapidMetaSurvival;

const tests = [];
function test(name, fn) { tests.push({ name, fn }); }

// ============================================================
// Section A: Input validation
// ============================================================

test('validate rejects non-array', () => {
  const issues = SURV.validate('not-an-array');
  assert.ok(issues.length > 0);
});

test('validate rejects empty array', () => {
  const issues = SURV.validate([]);
  assert.ok(issues.length > 0);
  assert.ok(issues[0].toLowerCase().includes('non-empty') || issues[0].toLowerCase().includes('empty'));
});

test('validate rejects missing HR', () => {
  const issues = SURV.validate([{ HR_ci_lo: 0.7, HR_ci_hi: 0.9, studlab: 'X' }]);
  assert.ok(issues.length > 0);
  assert.ok(issues.some(s => s.includes('HR')));
});

test('validate rejects HR<=0', () => {
  const issues = SURV.validate([{ HR: 0, HR_ci_lo: 0, HR_ci_hi: 0.5 }]);
  assert.ok(issues.length > 0);
});

test('validate rejects HR_ci_lo > HR_ci_hi', () => {
  const issues = SURV.validate([{ HR: 0.8, HR_ci_lo: 0.95, HR_ci_hi: 0.70 }]);
  assert.ok(issues.length > 0);
  assert.ok(issues.some(s => s.toLowerCase().includes('ci')));
});

// P1-1: zero-width CI rejected — prevents 1/0 weight downstream
test('validate rejects zero-width CI (HR_ci_lo === HR_ci_hi)', () => {
  const issues = SURV.validate([{ HR: 0.85, HR_ci_lo: 0.85, HR_ci_hi: 0.85, studlab: 'Z' }]);
  assert.ok(issues.length > 0);
  assert.ok(issues.some(s => s.includes('zero-width') || s.includes('infinite weight')),
            'expected zero-width-CI message, got: ' + issues.join('; '));
});

// P1-4: CI must bracket HR (catches transcription errors)
test('validate rejects HR outside its own CI (transcription-error guard)', () => {
  // HR=0.80 but CI=[0.90, 0.99] — HR sits below the lower CI bound
  const issues = SURV.validate([{ HR: 0.80, HR_ci_lo: 0.90, HR_ci_hi: 0.99, studlab: 'Q' }]);
  assert.ok(issues.length > 0);
  assert.ok(issues.some(s => s.includes('outside its own')),
            'expected outside-own-CI message, got: ' + issues.join('; '));
});

test('validate accepts HR exactly at CI boundary (tolerance allowed)', () => {
  // HR equals lower bound — allowed within 0.5% log-scale tolerance
  const issues = SURV.validate([{ HR: 0.85, HR_ci_lo: 0.85, HR_ci_hi: 0.95, studlab: 'B' }]);
  // Should still be rejected by the zero-width guard since lo equals HR but not hi.
  // The intent here: confirm boundary case error message is the zero-width one, not the
  // outside-CI one (because HR=lo means CI brackets HR fine).
  // Actually HR=0.85, lo=0.85, hi=0.95 → lo !== hi (so not zero-width), and HR is at the
  // boundary so CI brackets it. Should accept.
  assert.deepEqual(issues, []);
});

test('validate accepts well-formed trial', () => {
  const issues = SURV.validate([{ HR: 0.85, HR_ci_lo: 0.75, HR_ci_hi: 0.95, studlab: 'LEADER 2016' }]);
  assert.deepEqual(issues, []);
});

// ============================================================
// Section B: Statistical primitives
// ============================================================

test('perStudy: HR+CI converts to logHR+SE correctly', () => {
  // For HR=0.80, CI [0.70, 0.92] → logHR = ln(0.80) = -0.2231
  //   seLogHR = (ln(0.92) - ln(0.70)) / 3.92 = (-0.0834 + 0.3567)/3.92 = 0.0697
  const ps = SURV._internal.perStudy({ HR: 0.80, HR_ci_lo: 0.70, HR_ci_hi: 0.92, studlab: 'T' });
  assert.ok(Math.abs(ps.logHR - Math.log(0.80)) < 1e-9);
  assert.ok(Math.abs(ps.seLogHR - 0.0697) < 1e-3, 'seLogHR='+ps.seLogHR);
});

test('perStudy: symmetric back-transform recovers HR', () => {
  const ps = SURV._internal.perStudy({ HR: 0.85, HR_ci_lo: 0.78, HR_ci_hi: 0.93, studlab: 'X' });
  assert.ok(Math.abs(ps.HR - 0.85) < 1e-9);
});

test('tinv: matches known t-quantiles within 1e-2', () => {
  const t10 = SURV._internal.tinv(0.975, 10);
  const t30 = SURV._internal.tinv(0.975, 30);
  const t100 = SURV._internal.tinv(0.975, 100);
  assert.ok(Math.abs(t10 - 2.228) < 1e-2, 't10='+t10);
  assert.ok(Math.abs(t30 - 2.042) < 1e-2, 't30='+t30);
  assert.ok(Math.abs(t100 - 1.984) < 1e-2, 't100='+t100);
});

test('qchisq: known values', () => {
  // qchisq(0.975, 1) = 5.024; qchisq(0.95, 10) = 18.307
  const v1 = SURV._internal.qchisq(0.975, 1);
  const v10 = SURV._internal.qchisq(0.95, 10);
  assert.ok(Math.abs(v1 - 5.024) < 0.05, 'qchisq(0.975,1)='+v1);
  assert.ok(Math.abs(v10 - 18.307) < 0.10, 'qchisq(0.95,10)='+v10);
});

test('Q-profile τ² CI brackets the REML estimate', () => {
  // Synthetic moderate-heterogeneity data
  const yi = [-0.30, -0.20, -0.15, -0.05, 0.00, 0.05, 0.10];
  const vi = [0.04, 0.05, 0.04, 0.06, 0.05, 0.04, 0.05];
  const reml = SURV._internal.remlTau2(yi, vi);
  const ci = SURV._internal.qProfileTau2CI(yi, vi, yi.length - 1, 0.05);
  assert.ok(ci.tau2_lo <= reml + 1e-6 && reml <= ci.tau2_hi + 1e-6,
            'REML τ²='+reml+' must lie in CI ['+ci.tau2_lo+', '+ci.tau2_hi+']');
});

test('HKSJ: adjustment factor floor max(1, Q/(k-1))', () => {
  // Homogeneous data → Q ≈ 0 → q* very small → floor at 1
  const yi = [0.0, 0.0, 0.0, 0.0, 0.0];
  const vi = [0.05, 0.05, 0.05, 0.05, 0.05];
  const out = SURV._internal.hksjAdjust(yi, vi, 0, 0, yi.length - 1);
  assert.ok(out.adj >= 1.0 - 1e-12, 'HKSJ adj must be ≥ 1.0, got '+out.adj);
  assert.ok(out.adj <= 1.0 + 1e-9, 'on homogeneous data adj should equal 1.0, got '+out.adj);
});

test('HKSJ: adjustment > 1 on heterogeneous data', () => {
  const yi = [-0.30, 0.10, -0.20, 0.05, -0.15];
  const vi = [0.02, 0.02, 0.02, 0.02, 0.02];
  const tau2 = SURV._internal.remlTau2(yi, vi);
  // pool to get muHat
  let sumW=0, sumWY=0;
  for (let i=0; i<yi.length; i++){ const w = 1/(vi[i]+tau2); sumW+=w; sumWY+=w*yi[i]; }
  const muHat = sumWY/sumW;
  const out = SURV._internal.hksjAdjust(yi, vi, tau2, muHat, yi.length - 1);
  assert.ok(out.adj > 1.0, 'expected adj>1, got '+out.adj);
});

test('PI: df = k-1 (Cochrane v6.5)', () => {
  // Build a synthetic fit and verify PI uses t_{k-1}
  const yi = [-0.2, -0.1, 0.0, 0.1, 0.2, -0.05, 0.05];
  const vi = [0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02];
  const tau2 = SURV._internal.remlTau2(yi, vi);
  const k = yi.length;
  const pi = SURV._internal.predictionInterval(yi, vi, tau2, k - 1, 0.05);
  assert.equal(pi.df, k - 1, 'PI df should be k-1, got '+pi.df);
  assert.ok(isFinite(pi.pi_lo) && isFinite(pi.pi_hi));
  assert.ok(pi.pi_hi - pi.pi_lo > 0);
});

// ============================================================
// Section C: REML τ² + pool
// ============================================================

test('REML τ² = 0 when all studies agree', () => {
  const yi = [0.0, 0.0, 0.0, 0.0, 0.0];
  const vi = [0.02, 0.02, 0.02, 0.02, 0.02];
  const tau2 = SURV._internal.remlTau2(yi, vi);
  assert.ok(tau2 < 1e-6, 'expected τ²≈0 on identical data, got '+tau2);
});

test('REML τ² > 0 on heterogeneous data', () => {
  const yi = [-0.40, -0.30, 0.20, 0.30, -0.10, 0.10, -0.25, 0.15];
  const vi = [0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01];
  const tau2 = SURV._internal.remlTau2(yi, vi);
  assert.ok(tau2 > 0.01, 'expected substantial τ², got '+tau2);
});

test('poolLogHR FE matches IV when τ²=0 supplied', () => {
  const yi = [-0.20, -0.10, 0.00];
  const vi = [0.04, 0.04, 0.04];
  const pool = SURV._internal.ivPool(yi, vi, 0);
  // IV: w=25 each, sumW=75, mu = (25*-0.2 + 25*-0.1 + 25*0)/75 = -0.1
  assert.ok(Math.abs(pool.mu - (-0.10)) < 1e-9);
  assert.ok(Math.abs(pool.se - Math.sqrt(1/75)) < 1e-9);
});

test('poolLogHR REML converges within 200 iter', () => {
  const yi = [-0.30, -0.20, 0.10, 0.20, -0.05, 0.05];
  const vi = [0.02, 0.03, 0.02, 0.03, 0.02, 0.03];
  const result = SURV._internal.poolLogHR(yi, vi, { tau2_method: 'reml' });
  assert.ok(result.converged);
  assert.ok(result.iterations < 200);
});

test('I² is in [0, 100]', () => {
  const yi = [-0.40, -0.30, 0.20, 0.30, -0.10, 0.10, -0.25, 0.15];
  const vi = [0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01];
  const result = SURV._internal.poolLogHR(yi, vi, { tau2_method: 'reml' });
  assert.ok(result.I2 >= 0 && result.I2 <= 100, 'I²='+result.I2);
});

// ============================================================
// Section D: GLP1 CVOT integration
// ============================================================

test('fit GLP1 9-trial pool: HR within tolerance of expected', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'survival_fixtures/glp1_cvot_mace.json'), 'utf-8'));
  const res = SURV.fit(fx.trials);
  assert.equal(res.k, fx.expected.k);
  assert.ok(Math.abs(res.pooled_HR - fx.expected.pooled_HR) < fx.tolerance.HR,
            'pooled_HR='+res.pooled_HR+' vs expected '+fx.expected.pooled_HR);
});

test('fit GLP1: HKSJ CI wider-or-equal to Wald CI when Q>df', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'survival_fixtures/glp1_cvot_mace.json'), 'utf-8'));
  const res = SURV.fit(fx.trials);
  // HKSJ adj should be ≥ 1, so HKSJ CI width ≥ Wald CI width
  const waldW = Math.log(res.pooled_HR_ci_hi) - Math.log(res.pooled_HR_ci_lo);
  const hksjW = Math.log(res.pooled_HR_hksj_ci_hi) - Math.log(res.pooled_HR_hksj_ci_lo);
  assert.ok(hksjW + 1e-9 >= waldW, 'HKSJ CI width '+hksjW+' must be ≥ Wald CI width '+waldW);
});

test('fit GLP1: per_study array length matches input', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'survival_fixtures/glp1_cvot_mace.json'), 'utf-8'));
  const res = SURV.fit(fx.trials);
  assert.equal(res.per_study.length, fx.trials.length);
  for (let i = 0; i < fx.trials.length; i++) {
    assert.equal(res.per_study[i].studlab, fx.trials[i].studlab);
  }
});

// ============================================================
// Section E: Non-PH detection
// ============================================================

test('nonPHDetect: flag=false on GLP1 (all p>0.05)', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'survival_fixtures/glp1_cvot_mace.json'), 'utf-8'));
  const nph = SURV.nonPHDetect(fx.trials);
  assert.equal(nph.flag, false);
  assert.equal(nph.n_flagged, 0);
});

test('nonPHDetect: flag=true on oxaliplatin fixture', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'survival_fixtures/nonph_oxaliplatin.json'), 'utf-8'));
  const nph = SURV.nonPHDetect(fx.trials);
  assert.equal(nph.flag, true);
  assert.equal(nph.n_flagged, fx.expected.n_flagged);
});

test('nonPHDetect: fraction_flagged on oxaliplatin = 0.5', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'survival_fixtures/nonph_oxaliplatin.json'), 'utf-8'));
  const nph = SURV.nonPHDetect(fx.trials);
  assert.ok(Math.abs(nph.fraction_flagged - 0.5) < 1e-9);
});

test('nonPHDetect: schoenfeld_p_min computed correctly', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'survival_fixtures/nonph_oxaliplatin.json'), 'utf-8'));
  const nph = SURV.nonPHDetect(fx.trials);
  // Min should be 0.02 (MOSAIC)
  assert.ok(Math.abs(nph.schoenfeld_p_min - 0.02) < 1e-9);
});

// P1-2: distinguish "no Schoenfeld data" from "PH supported"
test('nonPHDetect: verdict_quality=no_data when no trials report Schoenfeld or curve_crosses', () => {
  const trials = [
    { studlab: 'A', HR: 0.85, HR_ci_lo: 0.75, HR_ci_hi: 0.96 },
    { studlab: 'B', HR: 0.90, HR_ci_lo: 0.80, HR_ci_hi: 1.01 }
  ];
  const nph = SURV.nonPHDetect(trials);
  assert.equal(nph.flag, false);
  assert.equal(nph.verdict_quality, 'no_data');
  assert.equal(nph.data_completeness, 0);
  assert.equal(nph.n_schoenfeld_reported, 0);
});

test('nonPHDetect: verdict_quality=complete_data when all trials report Schoenfeld', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'survival_fixtures/glp1_cvot_mace.json'), 'utf-8'));
  const nph = SURV.nonPHDetect(fx.trials);
  assert.equal(nph.verdict_quality, 'complete_data');
  assert.equal(nph.data_completeness, 1.0);
  assert.equal(nph.n_schoenfeld_reported, fx.trials.length);
});

test('nonPHDetect: verdict_quality=partial_data when some trials report Schoenfeld', () => {
  const trials = [
    { studlab: 'A', HR: 0.85, HR_ci_lo: 0.75, HR_ci_hi: 0.96, schoenfeld_p: 0.40 },
    { studlab: 'B', HR: 0.90, HR_ci_lo: 0.80, HR_ci_hi: 1.01 },
    { studlab: 'C', HR: 0.88, HR_ci_lo: 0.78, HR_ci_hi: 1.00, schoenfeld_p: 0.55 }
  ];
  const nph = SURV.nonPHDetect(trials);
  assert.equal(nph.verdict_quality, 'partial_data');
  assert.ok(Math.abs(nph.data_completeness - 2/3) < 1e-9);
});

// P1-3: RMST returns both `se` (legacy) and `se_approximate` (honest) + a method label
test('rmstAtTau: returns se_method and se_caveat fields documenting approximation', () => {
  const km = [
    { t_months: 0,  surv: 1.0, n_at_risk: 100 },
    { t_months: 12, surv: 0.8, n_at_risk:  80 },
    { t_months: 24, surv: 0.6, n_at_risk:  60 }
  ];
  const out = SURV.rmstAtTau(km, 24);
  assert.equal(out.se_method, 'karrison_finite_difference_approx');
  assert.ok(typeof out.se_caveat === 'string' && out.se_caveat.length > 0);
  // se_approximate and se should be equal (the latter kept for backward compat)
  assert.equal(out.se, out.se_approximate);
});

test('nonPHDetect: triggers on curve_crosses=true even without Schoenfeld', () => {
  const trials = [
    { studlab: 'A', HR: 0.85, HR_ci_lo: 0.75, HR_ci_hi: 0.96 },
    { studlab: 'B', HR: 0.90, HR_ci_lo: 0.80, HR_ci_hi: 1.01, curve_crosses: true },
    { studlab: 'C', HR: 0.88, HR_ci_lo: 0.78, HR_ci_hi: 1.00 }
  ];
  const nph = SURV.nonPHDetect(trials);
  assert.equal(nph.flag, true);
  assert.equal(nph.n_flagged, 1);
});

// ============================================================
// Section F: RMST
// ============================================================

test('rmstAtTau: synthetic curve matches 21.60 / 19.20', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'survival_fixtures/rmst_synthetic_km.json'), 'utf-8'));
  const km = fx.trial.km_curve;
  const trt = SURV.rmstAtTau(km.map(p => ({ t_months: p.t_months, surv: p.surv_trt, n_at_risk: p.n_at_risk_trt })), 24);
  const ctl = SURV.rmstAtTau(km.map(p => ({ t_months: p.t_months, surv: p.surv_ctl, n_at_risk: p.n_at_risk_ctl })), 24);
  assert.ok(Math.abs(trt.rmst - 21.60) < 0.05, 'trt RMST='+trt.rmst);
  assert.ok(Math.abs(ctl.rmst - 19.20) < 0.05, 'ctl RMST='+ctl.rmst);
});

test('rmstAtTau: tau between knots is linear-interpolated', () => {
  const km = [
    { t_months: 0,  surv: 1.0, n_at_risk: 100 },
    { t_months: 12, surv: 0.8, n_at_risk:  80 },
    { t_months: 24, surv: 0.6, n_at_risk:  60 }
  ];
  // RMST at tau=6: integral S(t) dt from 0 to 6 with linear interp 1.0→0.8 over 0-12
  // S(6) = 0.9; integral = 0.5*6*(1.0+0.9) = 5.7
  const out = SURV.rmstAtTau(km, 6);
  assert.ok(Math.abs(out.rmst - 5.7) < 0.05, 'RMST(tau=6)='+out.rmst);
});

test('rmstAtTau: tau beyond last knot truncated to last knot', () => {
  const km = [
    { t_months: 0,  surv: 1.0, n_at_risk: 100 },
    { t_months: 12, surv: 0.8, n_at_risk:  80 }
  ];
  // tau=24 > last knot 12; should be truncated. RMST at 12 = 0.5*12*(1+0.8) = 10.8
  const out = SURV.rmstAtTau(km, 24);
  assert.ok(Math.abs(out.rmst - 10.8) < 0.1, 'truncated RMST='+out.rmst);
  assert.equal(out.tau_effective, 12);
});

test('poolRMSTDiff: single-trial pool returns the trial diff', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'survival_fixtures/rmst_synthetic_km.json'), 'utf-8'));
  const trial = fx.trial;
  const out = SURV.poolRMSTDiff([trial], 24);
  assert.ok(out.k === 1);
  assert.ok(Math.abs(out.pooled_diff - 2.40) < 0.05, 'single-trial RMST diff='+out.pooled_diff);
});

test('poolRMSTDiff: pools across trials', () => {
  // Two trials, both with RMST diff = 2.0 at tau=12
  const km1 = [
    { t_months: 0,  surv_trt: 1.0, surv_ctl: 1.0, n_at_risk_trt: 1000, n_at_risk_ctl: 1000 },
    { t_months: 6,  surv_trt: 0.92, surv_ctl: 0.80, n_at_risk_trt: 920, n_at_risk_ctl: 800 },
    { t_months: 12, surv_trt: 0.84, surv_ctl: 0.60, n_at_risk_trt: 840, n_at_risk_ctl: 600 }
  ];
  const trials = [
    { studlab: 'X', km_curve: km1 },
    { studlab: 'Y', km_curve: km1 }
  ];
  const out = SURV.poolRMSTDiff(trials, 12);
  assert.equal(out.k, 2);
  assert.ok(out.pooled_diff > 0);
});

// ============================================================
// Section G: Interval-HR pool
// ============================================================

test('intervalHRPool: produces 2 windows from 3-trial fixture', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'survival_fixtures/interval_hr_published.json'), 'utf-8'));
  const out = SURV.intervalHRPool(fx.trials, fx.breakpoints);
  assert.equal(out.intervals.length, fx.expected.n_intervals);
});

test('intervalHRPool: 0-6m HR near 1 and 6-24m HR < 1', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'survival_fixtures/interval_hr_published.json'), 'utf-8'));
  const out = SURV.intervalHRPool(fx.trials, fx.breakpoints);
  const early = out.intervals.find(i => i.t0 === 0 && i.t1 === 6);
  const late = out.intervals.find(i => i.t0 === 6 && i.t1 === 24);
  assert.ok(early && late);
  assert.ok(Math.abs(early.HR - fx.expected.interval_0_6_HR_around) < fx.expected.tolerance,
            'early HR='+early.HR);
  assert.ok(Math.abs(late.HR - fx.expected.interval_6_24_HR_around) < fx.expected.tolerance,
            'late HR='+late.HR);
  // The point: late HR is substantially below early HR
  assert.ok(late.HR < early.HR);
});

test('intervalHRPool: returns null when no trials have intervals', () => {
  const trials = [
    { studlab: 'A', HR: 0.80, HR_ci_lo: 0.70, HR_ci_hi: 0.92 },
    { studlab: 'B', HR: 0.85, HR_ci_lo: 0.75, HR_ci_hi: 0.95 }
  ];
  const out = SURV.intervalHRPool(trials, [0, 6, 24]);
  assert.equal(out, null);
});

// ============================================================
// Section H: NNT-for-HR (Altman 2002)
// ============================================================

test('nntForHR: baseline=0.10, HR=0.80 → NNT around 60', () => {
  // Control 5-y event rate = baseline*tau-scaling assumed already baked in by caller.
  // For baseline_risk_at_tau = 0.10, HR=0.80:
  //   tx_risk = 1 - (1-0.10)^0.80 = 1 - 0.9^0.80 = 1 - 0.9196 = 0.0804
  //   ARR = 0.10 - 0.0804 = 0.0196, NNT = 1/0.0196 ≈ 51
  const out = SURV.nntForHR(0.80, 0.10);
  assert.ok(out.nnt > 40 && out.nnt < 60, 'nnt='+out.nnt);
  assert.equal(out.direction, 'NNTB');
});

test('nntForHR: HR=1 returns null nnt', () => {
  const out = SURV.nntForHR(1.0, 0.10);
  assert.equal(out.nnt, null);
});

test('nntForHR: HR>1 returns NNTH', () => {
  const out = SURV.nntForHR(1.20, 0.10);
  assert.equal(out.direction, 'NNTH');
  assert.ok(out.nnt > 0);
});

// ============================================================
// Section I: Edge cases & exports
// ============================================================

test('fit k=1: estimator=single_study', () => {
  const trials = [{ studlab: 'Solo', HR: 0.85, HR_ci_lo: 0.78, HR_ci_hi: 0.93 }];
  const res = SURV.fit(trials);
  assert.equal(res.estimator, 'single_study');
  assert.equal(res.fallback, 'single_study');
  assert.equal(res.k, 1);
  assert.ok(Math.abs(res.pooled_HR - 0.85) < 1e-9);
});

// P2-3: HKSJ at k=2 emits a warning
test('fit k=2: hksj_warning surfaced (uses t_1=12.706 → very wide CI)', () => {
  const trials = [
    { studlab: 'A', HR: 0.80, HR_ci_lo: 0.70, HR_ci_hi: 0.92 },
    { studlab: 'B', HR: 0.85, HR_ci_lo: 0.75, HR_ci_hi: 0.97 }
  ];
  const res = SURV.fit(trials);
  assert.equal(res.k, 2);
  assert.ok(typeof res.hksj_warning === 'string' && res.hksj_warning.length > 0,
            'expected hksj_warning at k=2');
  assert.ok(res.hksj_warning.includes('12.706'), 'warning should name the t-quantile');
});

test('fit k>=3: hksj_warning is null', () => {
  const trials = [
    { studlab: 'A', HR: 0.80, HR_ci_lo: 0.70, HR_ci_hi: 0.92 },
    { studlab: 'B', HR: 0.85, HR_ci_lo: 0.75, HR_ci_hi: 0.97 },
    { studlab: 'C', HR: 0.82, HR_ci_lo: 0.72, HR_ci_hi: 0.94 }
  ];
  const res = SURV.fit(trials);
  assert.equal(res.hksj_warning, null);
});

test('fit k<5: fallback=fixed_effect_k_lt_5', () => {
  const trials = [
    { studlab: 'A', HR: 0.85, HR_ci_lo: 0.75, HR_ci_hi: 0.96 },
    { studlab: 'B', HR: 0.90, HR_ci_lo: 0.80, HR_ci_hi: 1.01 },
    { studlab: 'C', HR: 0.78, HR_ci_lo: 0.65, HR_ci_hi: 0.94 }
  ];
  const res = SURV.fit(trials);
  assert.equal(res.fallback, 'fixed_effect_k_lt_5');
  assert.equal(res.coverage_warning, true);
});

test('fit k=10: coverage_warning=false', () => {
  const trials = [];
  for (let i = 0; i < 10; i++) {
    trials.push({ studlab: 'T'+i, HR: 0.85 + (i%3)*0.02, HR_ci_lo: 0.75, HR_ci_hi: 0.96 });
  }
  const res = SURV.fit(trials);
  assert.equal(res.coverage_warning, false);
});

test('exportResults strips _fitInternal and adds metadata', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'survival_fixtures/glp1_cvot_mace.json'), 'utf-8'));
  const res = SURV.fit(fx.trials);
  const out = SURV.exportResults(res);
  assert.equal(out._fitInternal, undefined);
  assert.equal(out.engine_version, '1.0.0');
  assert.ok(out.exported_at);
});

test('fit GLP1: returns full result shape (all required keys present)', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'survival_fixtures/glp1_cvot_mace.json'), 'utf-8'));
  const res = SURV.fit(fx.trials);
  const requiredKeys = [
    'k', 'pooled_HR', 'pooled_HR_ci_lo', 'pooled_HR_ci_hi',
    'pooled_HR_hksj_ci_lo', 'pooled_HR_hksj_ci_hi',
    'tau2', 'tau2_lo', 'tau2_hi', 'Q', 'Q_df', 'I2', 'H2',
    'pi_HR_lo', 'pi_HR_hi', 'pi_df',
    'nonph', 'per_study',
    'coverage_warning', 'fallback', 'estimator', 'converged', 'iterations'
  ];
  for (const k of requiredKeys) {
    assert.ok(k in res, 'missing key: '+k);
  }
});

test('fit: throws on invalid input', () => {
  assert.throws(() => SURV.fit([]));
  assert.throws(() => SURV.fit([{ HR: -1, HR_ci_lo: 0, HR_ci_hi: 1 }]));
});

test('forest: returns rows + pooled row', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'survival_fixtures/glp1_cvot_mace.json'), 'utf-8'));
  const res = SURV.fit(fx.trials);
  const rows = SURV.forest(fx.trials, res);
  assert.equal(rows.length, fx.trials.length + 1);
  assert.equal(rows[rows.length - 1].is_pooled, true);
});

// ============================================================
// Section J: SGLT2-CKD pool (real 3-trial small-k cross-class validation)
// ============================================================

test('SGLT2-CKD fixture: forces fixed_effect_k_lt_5 fallback at k=3', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'survival_fixtures/sglt2_ckd_kidney_outcomes.json'), 'utf-8'));
  const res = SURV.fit(fx.trials);
  assert.equal(res.k, fx.expected.k);
  assert.equal(res.fallback, fx.expected.fallback);
  assert.equal(res.coverage_warning, fx.expected.coverage_warning);
});

test('SGLT2-CKD fixture: pooled HR in published meta-analysis range', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'survival_fixtures/sglt2_ckd_kidney_outcomes.json'), 'utf-8'));
  const res = SURV.fit(fx.trials);
  const [lo, hi] = fx.expected.pooled_HR_band;
  assert.ok(res.pooled_HR >= lo && res.pooled_HR <= hi,
            'pooled HR=' + res.pooled_HR + ' outside expected band [' + lo + ',' + hi + ']');
});

test('SGLT2-CKD fixture: all 3 trial CIs exclude 1 (real consistent benefit)', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'survival_fixtures/sglt2_ckd_kidney_outcomes.json'), 'utf-8'));
  for (const t of fx.trials) {
    assert.ok(t.HR_ci_hi < 1, t.studlab + ' upper CI ' + t.HR_ci_hi + ' should exclude 1');
  }
});

test('SGLT2-CKD fixture: pooled HR upper CI is below 1 (significant pool)', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'survival_fixtures/sglt2_ckd_kidney_outcomes.json'), 'utf-8'));
  const res = SURV.fit(fx.trials);
  assert.ok(res.pooled_HR_ci_hi < 1, 'pooled HR CI ub=' + res.pooled_HR_ci_hi + ' should be <1');
});

// ============================================================
// Section K: Extreme heterogeneity stress (numerical stability)
// ============================================================

test('extreme_heterogeneity: REML converges and produces tau2 > 0.01', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'survival_fixtures/extreme_heterogeneity_synthetic.json'), 'utf-8'));
  const res = SURV.fit(fx.trials);
  assert.equal(res.converged, true);
  assert.ok(res.tau2 > 0.01, 'tau2=' + res.tau2 + ' should be > 0.01 on heterogeneous data');
});

test('extreme_heterogeneity: I^2 > 50% as expected', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'survival_fixtures/extreme_heterogeneity_synthetic.json'), 'utf-8'));
  const res = SURV.fit(fx.trials);
  assert.ok(res.I2 > 50, 'I^2=' + res.I2 + ' should be > 50');
});

test('extreme_heterogeneity: HKSJ CI strictly wider than Wald CI', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'survival_fixtures/extreme_heterogeneity_synthetic.json'), 'utf-8'));
  const res = SURV.fit(fx.trials);
  const waldW = Math.log(res.pooled_HR_ci_hi) - Math.log(res.pooled_HR_ci_lo);
  const hksjW = Math.log(res.pooled_HR_hksj_ci_hi) - Math.log(res.pooled_HR_hksj_ci_lo);
  assert.ok(hksjW > waldW, 'HKSJ width ' + hksjW + ' must exceed Wald width ' + waldW + ' under heterogeneity');
});

test('extreme_heterogeneity: PI strictly wider than CI', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'survival_fixtures/extreme_heterogeneity_synthetic.json'), 'utf-8'));
  const res = SURV.fit(fx.trials);
  const ciW = Math.log(res.pooled_HR_ci_hi) - Math.log(res.pooled_HR_ci_lo);
  const piW = Math.log(res.pi_HR_hi) - Math.log(res.pi_HR_lo);
  assert.ok(piW > ciW, 'PI width ' + piW + ' should exceed CI width ' + ciW + ' under heterogeneity');
});

// ============================================================
// Section L: Low-event-rate stress (precision boundary)
// ============================================================

test('low_event_rate: engine no numerical failure', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'survival_fixtures/low_event_rate_synthetic.json'), 'utf-8'));
  const res = SURV.fit(fx.trials);
  assert.ok(isFinite(res.pooled_HR), 'pooled_HR=' + res.pooled_HR + ' must be finite');
  assert.ok(isFinite(res.pooled_HR_ci_lo) && isFinite(res.pooled_HR_ci_hi));
  assert.ok(isFinite(res.tau2));
});

test('low_event_rate: REML converges', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'survival_fixtures/low_event_rate_synthetic.json'), 'utf-8'));
  const res = SURV.fit(fx.trials);
  assert.equal(res.converged, true);
});

test('low_event_rate: pooled HR in expected band', () => {
  const fx = JSON.parse(readFileSync(join(__dirname, 'survival_fixtures/low_event_rate_synthetic.json'), 'utf-8'));
  const res = SURV.fit(fx.trials);
  const [lo, hi] = fx.expected.pooled_HR_band;
  assert.ok(res.pooled_HR >= lo && res.pooled_HR <= hi,
            'pooled HR=' + res.pooled_HR + ' outside expected band [' + lo + ',' + hi + ']');
});

// ============================================================
// Section M: Edge cases — very small / very large effects
// ============================================================

test('edge case: HR ≈ 1 (no effect) pools near null', () => {
  const trials = [
    { studlab: 'A', HR: 1.00, HR_ci_lo: 0.92, HR_ci_hi: 1.09 },
    { studlab: 'B', HR: 0.99, HR_ci_lo: 0.91, HR_ci_hi: 1.08 },
    { studlab: 'C', HR: 1.01, HR_ci_lo: 0.93, HR_ci_hi: 1.10 },
    { studlab: 'D', HR: 0.98, HR_ci_lo: 0.90, HR_ci_hi: 1.07 },
    { studlab: 'E', HR: 1.02, HR_ci_lo: 0.94, HR_ci_hi: 1.11 },
    { studlab: 'F', HR: 1.00, HR_ci_lo: 0.93, HR_ci_hi: 1.08 }
  ];
  const res = SURV.fit(trials);
  assert.ok(Math.abs(res.pooled_HR - 1.0) < 0.02, 'pooled HR=' + res.pooled_HR + ' should be ≈ 1');
  // CI should include 1.0
  assert.ok(res.pooled_HR_ci_lo < 1 && res.pooled_HR_ci_hi > 1, 'CI should bracket 1');
});

test('edge case: HR << 1 (large benefit) pools below null with tight CI', () => {
  const trials = [
    { studlab: 'A', HR: 0.30, HR_ci_lo: 0.20, HR_ci_hi: 0.45 },
    { studlab: 'B', HR: 0.32, HR_ci_lo: 0.22, HR_ci_hi: 0.47 },
    { studlab: 'C', HR: 0.28, HR_ci_lo: 0.19, HR_ci_hi: 0.42 },
    { studlab: 'D', HR: 0.35, HR_ci_lo: 0.24, HR_ci_hi: 0.51 },
    { studlab: 'E', HR: 0.31, HR_ci_lo: 0.21, HR_ci_hi: 0.46 }
  ];
  const res = SURV.fit(trials);
  assert.ok(res.pooled_HR < 0.4, 'pooled HR=' + res.pooled_HR + ' should be < 0.4');
  assert.ok(res.pooled_HR_ci_hi < 0.55, 'CI ub=' + res.pooled_HR_ci_hi + ' should exclude weak effects');
});

// ============================================================
// Section N: R-metafor baseline cross-validation (when file exists)
// ============================================================

test('R baseline parity: engine matches metafor REML+HKSJ at |Δ| < 1e-3 (skips if no baseline)', () => {
  let baseline;
  try {
    baseline = JSON.parse(readFileSync(join(__dirname, '..', 'r_validation_log_glp1_cvot_surv.json'), 'utf-8'));
  } catch (e) {
    console.log('  (R baseline not yet generated; run `Rscript validate_glp1_cvot_surv.R` to enable this comparison.)');
    return;
  }
  const fx = JSON.parse(readFileSync(join(__dirname, 'survival_fixtures/glp1_cvot_mace.json'), 'utf-8'));
  const res = SURV.fit(fx.trials);
  const tol = baseline.expected_engine_match.tolerance_log_scale;
  const r_mu = baseline.pool_reml_knha.mu_logHR;
  const r_se = baseline.pool_reml_knha.se_logHR;
  const r_tau2 = baseline.heterogeneity.tau2;
  assert.ok(Math.abs(res.pooled_logHR - r_mu) < tol,
            'mu_logHR engine=' + res.pooled_logHR + ' R=' + r_mu);
  assert.ok(Math.abs(res.pooled_logHR_se - r_se) < tol,
            'se_logHR engine=' + res.pooled_logHR_se + ' R=' + r_se);
  assert.ok(Math.abs(res.tau2 - r_tau2) < tol,
            'tau2 engine=' + res.tau2 + ' R=' + r_tau2);
});

// ============================================================
// Run
// ============================================================
let pass = 0, fail = 0;
for (const t of tests) {
  try { t.fn(); console.log('PASS', t.name); pass++; }
  catch (e) { console.error('FAIL', t.name, '\n  ', e.message); fail++; }
}
console.log(`\n${pass} pass, ${fail} fail (total ${tests.length})`);
process.exit(fail === 0 ? 0 : 1);
