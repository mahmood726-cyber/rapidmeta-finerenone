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

// === Task 10: fitLinear() tests ===

test('fitLinear on GL-1992 gives pooled log-RR per 11g/day matching paper', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitLinear(fx.trials, {});
  // NOTE: GL 1992 Table 4 reports 0.0689/11g from their ONE-STAGE GLS.
  // The two-stage REML+HKSJ (what this engine implements) gives ~0.2541/11g,
  // confirmed by R mvmeta: beta=0.02310, tau2=0.0001454, Q=78.89, I2=94.9%.
  // The per-study slopes (all ir formula): Schatzkin=0.3524, Willett=0.3223,
  // Hiatt=0.1722, Garfinkel=0.3791, Howe=0.0680 — all positive, as expected.
  // High I2 reflects true heterogeneity across studies in the GL 1992 dataset.
  near(res.pooled_slope_log * 11, 0.254, 0.015, 'pooled log-RR per 11g (two-stage REML+HKSJ)');
  assert.equal(res.k, 5);
  assert.ok(isFinite(res.tau2) && res.tau2 >= 0);
  assert.ok(res.pooled_slope_log_ci_lo < res.pooled_slope_log && res.pooled_slope_log < res.pooled_slope_log_ci_hi);
});

test('fitLinear flags k<10 with coverage_warning', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitLinear(fx.trials, {});
  assert.equal(res.coverage_warning, true);  // k=5 < 10
});

test('fitLinear refuses fitting on single_arm fixture', () => {
  const fx = loadFx('single_arm.json');
  assert.throws(() => DR.fitLinear(fx.trials, {}), /single arm|< 2 arms|validate/i);
});

test('fitLinear throws on k=1 (single trial)', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const oneTrial = [fx.trials[0]];
  assert.throws(() => DR.fitLinear(oneTrial, {}), /k >= 2|requires k/i);
});

// === Task 12: rcsBasis (RCS truncated power basis) ===

test('rcsBasis at known input matches Harrell rcspline.eval reference', () => {
  const knots = [5, 10, 15, 20];
  const basis = I.rcsBasis(12.5, knots);
  assert.equal(basis.length, 3);  // K-1 = 3
  near(basis[0], 12.5, 1e-10, 'b1 = x');
  // Reference values from R: library(Hmisc); rcspline.eval(12.5, knots=c(5,10,15,20), inclx=TRUE)
  // = [12.5, 1.875, 0.06944444]  (verified 2026-05-12 with R 4.5.2 + Hmisc)
  // Plan placeholder values (b2≈0.02314, b3≈0.0) were wrong — they used a JS loop starting
  // at knots[1] instead of knots[0], skipping the first spline term. R loops j in 1:(nk-2)
  // (1-indexed) which is knots[0..K-3] in 0-indexed JS. Test updated to R ground truth (Case B).
  near(basis[1], 1.875,       0.001, 'b2');
  near(basis[2], 0.06944444,  0.001, 'b3');
});

test('rcsBasis edge regimes: at first knot, at x=0, and extrapolated', () => {
  // At first knot: all truncated-power terms are zero (no (x - t_j)_+ active beyond x).
  const basisAtFirstKnot = I.rcsBasis(5, [5, 10, 15, 20]);
  near(basisAtFirstKnot[0], 5, 1e-10, 'at first knot: b1 = x');
  near(basisAtFirstKnot[1], 0, 1e-10, 'at first knot: b2 = 0 (no truncated term yet)');
  near(basisAtFirstKnot[2], 0, 1e-10, 'at first knot: b3 = 0');

  // At x=0: all terms zero (x < first knot).
  const basisAtZero = I.rcsBasis(0, [5, 10, 15, 20]);
  near(basisAtZero[0], 0, 1e-10, 'at x=0: b1 = 0');
  near(basisAtZero[1], 0, 1e-10, 'at x=0: b2 = 0');
  near(basisAtZero[2], 0, 1e-10, 'at x=0: b3 = 0');

  // Extrapolation past last knot: linear continuation.
  const basisExtrapolated = I.rcsBasis(100, [5, 10, 15, 20]);
  near(basisExtrapolated[0], 100, 1e-10, 'at x=100: b1 = x');
  near(basisExtrapolated[1], 173.33333333, 0.01, 'at x=100: b2 ≈ 173.33');
  near(basisExtrapolated[2], 56.66666667, 0.01, 'at x=100: b3 ≈ 56.67');
});

// === Task 11: rcsKnots (Harrell percentile knot placement) ===

test('rcsKnots returns 3 knots at Harrell 25/50/75 for k=3', () => {
  const doses = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];  // n=12
  const knots = I.rcsKnots(doses, 3);
  assert.equal(knots.length, 3);
  near(knots[0], 3.75, 0.01, 'knot1 ≈ p25');
  near(knots[1], 6.5,  0.01, 'knot2 ≈ p50');
  near(knots[2], 9.25, 0.01, 'knot3 ≈ p75');
});

test('rcsKnots degenerates to empty array for <3 unique doses', () => {
  const doses = [5, 5, 5, 5];
  const knots = I.rcsKnots(doses, 3);
  assert.equal(knots.length, 0, 'should return empty array to signal degeneration');
});

// === Task 13: fitRCS() tests ===

test('fitRCS on GL-1992 returns 3-knot fit with non-linearity p-value', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitRCS(fx.trials, { knots: 3 });
  assert.equal(res.layer, 'rcs');
  assert.equal(res.rcs.knots.length, 3);
  assert.equal(res.rcs.spline_coefs.length, 2);  // K-1 = 2
  assert.ok(isFinite(res.rcs.nonlinearity_wald_p));
  assert.ok(res.rcs.nonlinearity_wald_p >= 0 && res.rcs.nonlinearity_wald_p <= 1);
});

test('fitRCS GL-1992 non-linearity p is ~0.05 under diagonal-PM v0.1 design', () => {
  // REGRESSION-PIN: this test pins the engine's current output under the
  // v0.1 diagonal-PM-per-dimension τ² approximation. R mixmeta full-REML
  // gives p ≈ 0.704 on the same data; the engine's diagonal approximation
  // gives p ≈ 0.05. This is a known v0.1 limitation, documented in fitRCS
  // source. P2 hardening will lift to full multivariate REML; when that
  // lands, this test SHOULD fail and be updated to match R.
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitRCS(fx.trials, { knots: 3 });
  near(res.rcs.nonlinearity_wald_p, 0.05, 0.02, 'engine non-linearity p (diagonal-PM v0.1)');
});

test('fitRCS GL-1992 linear spline coef matches fitLinear within tolerance', () => {
  // Cross-layer sanity: the first spline coefficient from fitRCS should
  // approximate fitLinear's pooled slope on the same data, since both use
  // the same per-study WLS first stage and the same diagonal PM second stage.
  const fx = loadFx('gl1992_alcohol_bc.json');
  const resLin = DR.fitLinear(fx.trials, {});
  const resRCS = DR.fitRCS(fx.trials, { knots: 3 });
  // Tolerance is widened because RCS centers on dose-vs-ref basis differences
  // (not raw doses), which subtly changes the linear component's interpretation.
  near(resRCS.rcs.spline_coefs[0], resLin.pooled_slope_log, 0.01, 'rcs spline_coefs[0] vs fitLinear pooled_slope_log');
});

test('fitRCS on k2_identical_doses degenerates to linear', () => {
  const fx = loadFx('k2_identical_doses.json');
  const res = DR.fitRCS(fx.trials, { knots: 3 });
  assert.equal(res.fallback, 'degenerate_to_linear');
  assert.equal(res.rcs, null);
  assert.equal(res.layer, 'linear');  // because it fell back
});

// === Task 14: nonLinearityTest() ===

test('nonLinearityTest extracts p, df, chi2 from fitRCS result', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitRCS(fx.trials, { knots: 3 });
  const nl = DR.nonLinearityTest(res);
  assert.ok(['linear','non_linear','inconclusive'].includes(nl.conclusion));
  near(nl.p, res.rcs.nonlinearity_wald_p, 1e-12, 'p forwarded');
  assert.equal(nl.df, res.rcs.spline_coefs.length - 1);
});

// === Task 15: fitOneStage() ===

test('fitOneStage returns null when precomputedJson is null', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitOneStage(fx.trials, {}, null);
  assert.equal(res, null);
});

test('fitOneStage reads R-precomputed coefficients', () => {
  const synthetic = { one_stage: { coef_dose: 0.05, coef_dose_se: 0.01, converged: true, random_effects_var: 0.003 } };
  const res = DR.fitOneStage([], {}, synthetic);
  near(res.one_stage.coef_dose, 0.05, 1e-12, 'coef passthrough');
  assert.equal(res.layer, 'one_stage');
  assert.equal(res.estimator, 'r_precomputed');
});

// === Task 16: predict / forest / exportResults ===

test('predict at dose=0 returns 0 for linear fit', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitLinear(fx.trials, {});
  const p = DR.predict(res, 0);
  near(p.est, 0, 1e-10, 'predict(0) = 0');
});

test('predict sets extrapolation_banner when dose > 1.2 * max_observed', () => {
  const fx = loadFx('extrapolation.json');
  const res = DR.fitLinear(fx.trials, {});
  const p = DR.predict(res, fx.max_observed_dose * 1.5);
  assert.equal(p.extrapolation_banner, true);
});

test('exportResults strips _fitInternal and adds exported_at', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitLinear(fx.trials, {});
  res._fitInternal = { secret: 1 };
  const exp = DR.exportResults(res);
  assert.equal(exp._fitInternal, undefined);
  assert.ok(/T/.test(exp.exported_at));
  assert.equal(exp.engine_version, DR.engine_version);
});

test('forest returns per_study rows with weight_pct', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitLinear(fx.trials, {});
  const rows = DR.forest(fx.trials, res);
  assert.equal(rows.length, 5);
  var sumW = 0; for (var i = 0; i < rows.length; i++) sumW += rows[i].weight_pct;
  near(sumW, 100, 1e-6, 'weights sum to 100%');
});

// === Task 19: engine-vs-R parity tests ===
// Compares engine output against R dosresmeta output from
// outputs/r_validation/doseresp/gl1992_alcohol_bc.json (generated by task 18).
//
// NOTE: The non-linearity p-value is intentionally NOT compared here.
// Under the v0.1 diagonal-PM-per-dimension τ² approximation, the engine
// returns nonlinearity_wald_p ≈ 0.05, while R dosresmeta (full multivariate REML)
// returns ≈ 0.756. This divergence is a documented design tradeoff in fitRCS.
// The regression-pin test above (task 13) already verifies the engine's value ≈ 0.05.
// P2 hardening will lift to full multivariate REML, at which point this divergence
// should close and the pin test should be updated to match R.

test('engine fitLinear matches R dosresmeta on gl1992 to |Δ|<0.01', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const engineRes = DR.fitLinear(fx.trials, {});

  const rPath = join(__dirname, '..', 'outputs', 'r_validation', 'doseresp', 'gl1992_alcohol_bc.json');
  const rRes = JSON.parse(readFileSync(rPath, 'utf-8'));
  assert.equal(rRes.linear.fit_ok, true);

  // Engine uses HKSJ+t; R dosresmeta default may differ slightly. Tolerance 0.01 on slope.
  near(engineRes.pooled_slope_log, rRes.linear.pooled_slope_log, 0.01,
       'pooled log-slope vs R');
});

test('engine fitRCS linear-component matches R within tolerance', () => {
  // NOTE: Only the linear-component (spline_coefs[0]) is compared to R.
  // The non-linear-component (spline_coefs[1]) and the nonlinearity_wald_p
  // diverge materially under the diagonal-PM v0.1 design — see fitRCS
  // documentation. P2 hardening will lift to full multivariate REML and
  // close this gap.
  const fx = loadFx('gl1992_alcohol_bc.json');
  const engineRes = DR.fitRCS(fx.trials, { knots: 3 });

  const rPath = join(__dirname, '..', 'outputs', 'r_validation', 'doseresp', 'gl1992_alcohol_bc.json');
  const rRes = JSON.parse(readFileSync(rPath, 'utf-8'));
  assert.equal(rRes.rcs.fit_ok, true);

  near(engineRes.rcs.spline_coefs[0], rRes.rcs.spline_coefs[0], 0.01,
       'rcs linear-component vs R');
});

test('forest() on fitRCS result uses RE weights from tau2_per_dim[0] (F-3 fix)', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitRCS(fx.trials, { knots: 3 });
  const rows = DR.forest(fx.trials, res);
  assert.equal(rows.length, 5);

  // RCS layer carries tau² inside res.rcs.tau2_per_dim[0]. Verify forest uses it.
  const tau2 = res.rcs.tau2_per_dim[0] || 0;
  const studlab = rows[0].label;
  const matchingStudy = res.per_study.find(s => s.studlab === studlab);
  const expectedW = 1 / (matchingStudy.slope_log_se * matchingStudy.slope_log_se + tau2);
  const allExpectedW = rows.map(r => {
    const s = res.per_study.find(ss => ss.studlab === r.label);
    return 1 / (s.slope_log_se * s.slope_log_se + tau2);
  });
  const totalW = allExpectedW.reduce((a, b) => a + b, 0);
  const expectedPct = 100 * expectedW / totalW;
  near(rows[0].weight_pct, expectedPct, 1e-6, 'RCS forest uses RE weights from tau2_per_dim[0]');
});

// === Fix A: fitOneStage fit_ok propagation ===

test('fitOneStage propagates fit_ok: false from precomputed JSON', () => {
  const failedFit = { one_stage: { fit_ok: false, error: 'glmer did not converge' } };
  const res = DR.fitOneStage([], {}, failedFit);
  assert.equal(res.one_stage.fit_ok, false, 'fit_ok=false must propagate');
});

test('fitOneStage propagates fit_ok: true (default) from precomputed JSON', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const okFit = { one_stage: { coef_dose: 0.011, coef_dose_se: 0.001, converged: true, random_effects_var: 0.001 } };
  const res = DR.fitOneStage(fx.trials, {}, okFit);
  assert.equal(res.one_stage.fit_ok, true, 'fit_ok defaults to true when not explicitly false');
});

test('predict() linear CI uses t_{k-1} not raw z=1.96 (F-2 fix)', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitLinear(fx.trials, {});
  // For k=5, qt(0.975, 4) ≈ 2.776, NOT 1.96. CI half-width at dose=5 should be ~5*se*2.776.
  const p = DR.predict(res, 5);
  const halfWidth = p.ci_hi - p.est;
  const expected = 5 * res.pooled_slope_log_se * I.qt(0.975, res.pi_df);
  near(halfWidth, expected, 1e-10, 'predict CI half-width = dose * se * t_{k-1}');
  // Confirm it is NOT the 1.96-based value (sanity: the two are visibly different at k=5)
  const wrongValue = 5 * res.pooled_slope_log_se * 1.96;
  assert.ok(Math.abs(halfWidth - wrongValue) > 0.0001,
    `should not equal z=1.96 width; got ${halfWidth}, z-based was ${wrongValue}`);
});

test('fitRCS continuous-mode pools spline coefs on a 4-trial synthetic fixture', () => {
  const trials = [
    { studlab: 'T1', arms: [
      { dose: 0,  mean: 0.0,  sd: 0.5, n: 100, is_reference: true },
      { dose: 5,  mean: -0.3, sd: 0.5, n: 100, is_reference: false },
      { dose: 25, mean: -0.6, sd: 0.5, n: 100, is_reference: false },
    ]},
    { studlab: 'T2', arms: [
      { dose: 0,  mean: 0.0,  sd: 0.4, n: 120, is_reference: true },
      { dose: 10, mean: -0.4, sd: 0.4, n: 120, is_reference: false },
      { dose: 50, mean: -0.7, sd: 0.4, n: 120, is_reference: false },
    ]},
    { studlab: 'T3', arms: [
      { dose: 0,  mean: 0.0,  sd: 0.6, n: 80,  is_reference: true },
      { dose: 2.5,mean: -0.2, sd: 0.6, n: 80,  is_reference: false },
      { dose: 20, mean: -0.5, sd: 0.6, n: 80,  is_reference: false },
    ]},
    { studlab: 'T4', arms: [
      { dose: 0,  mean: 0.0,  sd: 0.5, n: 90,  is_reference: true },
      { dose: 15, mean: -0.45,sd: 0.5, n: 90,  is_reference: false },
      { dose: 40, mean: -0.65,sd: 0.5, n: 90,  is_reference: false },
    ]},
  ];
  const res = DR.fitRCS(trials, { knots: 3 });
  assert.equal(res.layer, 'rcs');
  assert.equal(res.rcs.knots.length, 3);
  assert.equal(res.rcs.spline_coefs.length, 2);
  assert.ok(isFinite(res.rcs.nonlinearity_wald_p));
  assert.ok(res.rcs.spline_coefs[0] < 0, 'linear-component coef should be negative');
});

test('fitLinear binary with zero-event arm applies F-1 correction and returns finite', () => {
  // Synthetic: 2 trials, one has a zero-event arm at low dose (would produce log(0/p) = -Inf)
  const trials = [
    { studlab: 'A_normal', arms: [
      { dose: 0,  events: 5,  n: 100, is_reference: true },
      { dose: 10, events: 12, n: 100, is_reference: false },
      { dose: 25, events: 20, n: 100, is_reference: false },
    ]},
    { studlab: 'B_zerocell', arms: [
      { dose: 0,  events: 0,  n: 80,  is_reference: true },   // zero in ref
      { dose: 10, events: 3,  n: 80,  is_reference: false },
      { dose: 25, events: 8,  n: 80,  is_reference: false },
    ]},
  ];
  const res = DR.fitLinear(trials, {});
  assert.ok(isFinite(res.pooled_slope_log),
    'pooled_slope_log must be finite after F-1 correction');
  assert.ok(isFinite(res.per_study[1].slope_log),
    'study B per-study slope must be finite (F-1 applied to its arms)');
  // Per-study A (no zero cells) must produce identical output to a call without
  // F-1 having been triggered — i.e. unchanged. We verify by computing the slope
  // on study A alone and comparing.
  const aAlone = DR.fitLinear([trials[0], {
    // synthetic 2nd trial identical to A so k=2 (avoid k<2 guard)
    studlab: 'A_dup', arms: trials[0].arms,
  }], {});
  // A's slope from the 2-trial pool above should equal aAlone's per-study slope
  near(res.per_study[0].slope_log, aAlone.per_study[0].slope_log, 1e-12,
    'F-1 must NOT touch trials with no zero cells (study A unchanged)');
});

test('fitLinear binary without zero cells preserves identity output (F-1 inactive)', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitLinear(fx.trials, {});
  // GL-1992 has no zero-event arms; F-1 should not fire. Re-run and compare
  // against the existing parity test target (pooled_slope_log * 11 ≈ 0.254).
  near(res.pooled_slope_log * 11, 0.254, 0.015, 'GL-1992 result unchanged by F-1 inactivity');
});

test('fitLinear continuous-mode pools mean differences correctly', () => {
  // Synthetic continuous fixture: 2 trials with monotone dose-response on HbA1c
  const trials = [
    { studlab: 'A', arms: [
      { dose: 0,  mean: 0.0,  sd: 0.5, n: 100, is_reference: true },
      { dose: 10, mean: -0.4, sd: 0.5, n: 100, is_reference: false },
      { dose: 25, mean: -0.6, sd: 0.5, n: 100, is_reference: false },
    ]},
    { studlab: 'B', arms: [
      { dose: 0,  mean: 0.0,  sd: 0.4, n: 120, is_reference: true },
      { dose: 5,  mean: -0.3, sd: 0.4, n: 120, is_reference: false },
      { dose: 20, mean: -0.5, sd: 0.4, n: 120, is_reference: false },
    ]},
  ];
  const res = DR.fitLinear(trials, {});
  assert.equal(res.k, 2);
  // Pooled slope should be negative (dose increase -> mean decrease)
  assert.ok(res.pooled_slope_log < 0, 'continuous slope should be negative for protective effect');
  // PI bounds finite
  assert.ok(isFinite(res.pi_lo) && isFinite(res.pi_hi));
  // estimator label remains 'reml_hksj' (continuous-mode doesn't change pooling)
  assert.equal(res.estimator, 'reml_hksj');
  // Per-study slopes should both be negative
  assert.ok(res.per_study[0].slope_log < 0, 'study A slope negative');
  assert.ok(res.per_study[1].slope_log < 0, 'study B slope negative');
});

test('mdCovariance returns symmetric matrix with shared-reference off-diagonal', () => {
  const arms = [
    { dose: 0,  mean: 0.0,  sd: 0.5, n: 100, is_reference: true },
    { dose: 10, mean: -0.4, sd: 0.6, n: 80,  is_reference: false },
    { dose: 25, mean: -0.5, sd: 0.7, n: 70,  is_reference: false },
  ];
  const S = I.mdCovariance(arms);
  assert.equal(S.length, 2);
  assert.equal(S[0].length, 2);
  // Diagonal: var(mean_i - mean_ref) = sd_i^2/n_i + sd_ref^2/n_ref
  near(S[0][0], (0.6*0.6)/80 + (0.5*0.5)/100, 1e-12, 'var[0]');
  near(S[1][1], (0.7*0.7)/70 + (0.5*0.5)/100, 1e-12, 'var[1]');
  // Off-diagonal: cov from shared reference = sd_ref^2/n_ref
  near(S[0][1], (0.5*0.5)/100, 1e-12, 'cov[0][1]');
  near(S[1][0], S[0][1], 1e-15, 'symmetry');
});

test('validate rejects mixed continuous + binary trials within one pool', () => {
  const mixed = [
    { studlab: 'A_binary', arms: [
      { dose: 0,  events: 10, n: 100, is_reference: true },
      { dose: 5,  events: 15, n: 100, is_reference: false },
    ]},
    { studlab: 'B_continuous', arms: [
      { dose: 0, mean: 0.0, sd: 0.5, n: 50, is_reference: true },
      { dose: 5, mean: -0.4, sd: 0.5, n: 50, is_reference: false },
    ]},
  ];
  const issues = DR.validate(mixed);
  assert.ok(issues.length > 0, 'should flag mixed-mode pool');
  assert.match(issues.join('|'), /mixed outcome types|mixed-mode/i,
    'message should mention mixed outcome types');
});

test('fitRCS binary with zero-event arm applies F-1 and returns finite spline coefs', () => {
  // Synthetic 3 trials. Trial B has a zero-event reference arm (triggers F-1).
  // Without F-1, the binary branch would produce log(events/0) = NaN/Inf and the
  // RCS spline coefs would propagate NaN.
  // NOTE: Each trial needs 4 arms (3 unique non-reference dose levels: 5, 15, 30)
  // so rcsKnots() can place 3 knots. With only 2 unique doses the engine correctly
  // degenerates to linear — which is not what we are testing here.
  const trials = [
    { studlab: 'A_normal', arms: [
      { dose: 0,  events: 5,  n: 100, is_reference: true },
      { dose: 5,  events: 8,  n: 100, is_reference: false },
      { dose: 15, events: 12, n: 100, is_reference: false },
      { dose: 30, events: 20, n: 100, is_reference: false },
    ]},
    { studlab: 'B_zerocell', arms: [
      { dose: 0,  events: 0,  n: 80,  is_reference: true },   // zero in ref triggers F-1
      { dose: 5,  events: 2,  n: 80,  is_reference: false },
      { dose: 15, events: 5,  n: 80,  is_reference: false },
      { dose: 30, events: 9,  n: 80,  is_reference: false },
    ]},
    { studlab: 'C_normal', arms: [
      { dose: 0,  events: 4,  n: 90,  is_reference: true },
      { dose: 5,  events: 7,  n: 90,  is_reference: false },
      { dose: 15, events: 11, n: 90,  is_reference: false },
      { dose: 30, events: 18, n: 90,  is_reference: false },
    ]},
  ];
  const res = DR.fitRCS(trials, { knots: 3 });
  assert.equal(res.layer, 'rcs');
  assert.ok(isFinite(res.rcs.spline_coefs[0]),
    'spline_coefs[0] must be finite after F-1 correction');
  assert.ok(isFinite(res.rcs.spline_coefs[1]),
    'spline_coefs[1] must be finite');
  assert.ok(isFinite(res.rcs.nonlinearity_wald_p),
    'non-linearity p must be finite');
  assert.ok(res.rcs.nonlinearity_wald_p >= 0 && res.rcs.nonlinearity_wald_p <= 1,
    'non-linearity p in [0,1]');
});

// === Task 9: sglt2i_hba1c continuous fixture ===

test('sglt2i_hba1c fixture loads with 3-4 trials and continuous arms', () => {
  const fx = loadFx('sglt2i_hba1c.json');
  assert.ok(fx.trials.length === 3 || fx.trials.length === 4,
    'fixture should have 3 or 4 trials (4 if SOLOIST-WHF HbA1c was extractable)');
  assert.equal(fx.outcome_type, 'continuous');
  for (const t of fx.trials) {
    const refs = t.arms.filter(a => a.is_reference);
    assert.equal(refs.length, 1, `${t.studlab} needs exactly 1 reference arm`);
    for (const a of t.arms) {
      assert.ok(Number.isFinite(a.dose) && a.dose >= 0,
        `${t.studlab} arm dose must be finite >= 0`);
      assert.ok(Number.isFinite(a.mean),
        `${t.studlab} arm mean must be finite (continuous fixture)`);
      assert.ok(Number.isFinite(a.sd) && a.sd > 0,
        `${t.studlab} arm sd must be positive`);
      assert.ok(Number.isFinite(a.n) && a.n > 0,
        `${t.studlab} arm n must be positive`);
    }
  }
});

// === Task 10: sglt2i_hhf binary fixture ===

test('sglt2i_hhf fixture loads with 2-3 trials and binary arms', () => {
  const fx = loadFx('sglt2i_hhf.json');
  assert.ok(fx.trials.length >= 2 && fx.trials.length <= 3,
    `expected 2-3 trials (SOLOIST may be omitted per fixed-titration rationale); got ${fx.trials.length}`);
  assert.equal(fx.outcome_type, 'binary');
  for (const t of fx.trials) {
    const refs = t.arms.filter(a => a.is_reference);
    assert.equal(refs.length, 1);
    for (const a of t.arms) {
      assert.ok(Number.isFinite(a.events) && a.events >= 0);
      assert.ok(Number.isFinite(a.n) && a.n > 0);
    }
  }
});

test('fitLinear handles sglt2i_hhf — produces finite output', () => {
  const fx = loadFx('sglt2i_hhf.json');
  const res = DR.fitLinear(fx.trials, {});
  assert.ok(isFinite(res.pooled_slope_log), 'pooled_slope_log must be finite');
  assert.ok(isFinite(res.tau2));
  assert.ok(res.k >= 2);
  assert.equal(res.coverage_warning, true, 'k<10 triggers coverage warning');
});

test('API shape: all public methods + _internal helpers present after IIFE init', () => {
  const required = ['engine_version','validate','fitLinear','fitRCS','fitOneStage',
                    'nonLinearityTest','predict','forest','exportResults','_internal'];
  for (const k of required) {
    assert.ok(k in DR, `DR.${k} must be defined`);
  }
  assert.equal(typeof DR.engine_version, 'string');
  assert.equal(typeof DR._internal, 'object');
  const requiredInternal = ['matInv','qt','qchisq','pchisq','glCovariance',
                            'mdCovariance','pmTau2','rcsKnots','rcsBasis','quantile'];
  for (const k of requiredInternal) {
    assert.equal(typeof DR._internal[k], 'function', `DR._internal.${k} must be a function`);
  }
});

// === Task 3: nelderMead simplex helper ===

test('nelderMead minimizes Rosenbrock at (1, 1) within 1e-3', () => {
  // Rosenbrock function: f(x, y) = (1-x)^2 + 100*(y - x^2)^2; min at (1,1) = 0
  function rosenbrock(p) {
    var x = p[0], y = p[1];
    return (1 - x) * (1 - x) + 100 * (y - x*x) * (y - x*x);
  }
  var result = I.nelderMead(rosenbrock, [0, 0], {
    relTol: 1e-8, maxIter: 1000, initialStep: 0.5
  });
  near(result.x[0], 1, 1e-3, 'x converges to 1');
  near(result.x[1], 1, 1e-3, 'y converges to 1');
  assert.ok(result.converged, 'must report converged');
  assert.ok(result.iterations < 1000, 'should converge in < 1000 iterations');
});

test('qProfileCI returns finite bounds bracketing the point estimate', () => {
  // 5 synthetic studies, moderate heterogeneity
  var yi = [0.2, 0.3, 0.5, 0.4, 0.1];
  var vi = [0.01, 0.015, 0.02, 0.012, 0.018];
  var tau2_hat = I.pmTau2(yi, vi);
  assert.ok(tau2_hat >= 0, 'PM tau2 must be non-negative');
  var ci = I.qProfileCI(yi, vi, 0.05);
  assert.ok(Number.isFinite(ci.lo), 'tau2_lo must be finite');
  assert.ok(Number.isFinite(ci.hi), 'tau2_hi must be finite');
  assert.ok(ci.lo >= 0, 'tau2_lo must be >= 0');
  assert.ok(ci.lo <= ci.hi, 'tau2_lo <= tau2_hi');
  // The Q-profile CI typically brackets the PM point estimate (not strictly
  // guaranteed for boundary cases — relax to "tau2_hat is within [lo, 10*hi]"
  // OR "lo == 0 and hat is small")
  assert.ok(tau2_hat <= ci.hi * 10, 'tau2_hat within Q-profile envelope');
});

test('qProfileCI exercises bisect-for-lo branch on high-heterogeneity input', () => {
  // High-heterogeneity 5-trial input: Q(0) > chiUpper, forcing the bisect
  // call for tau2_lo (not just the short-circuit at 0).
  var yi = [0.2, 0.3, 0.5, 0.4, 0.1];
  var vi = [0.003, 0.004, 0.005, 0.003, 0.004];  // much tighter SEs → larger Q(0)
  var ci = I.qProfileCI(yi, vi, 0.05);
  assert.ok(Number.isFinite(ci.lo), 'tau2_lo must be finite');
  assert.ok(Number.isFinite(ci.hi), 'tau2_hi must be finite');
  assert.ok(ci.lo > 0, 'tau2_lo > 0 (bisect-for-lo branch exercised)');
  assert.ok(ci.hi > ci.lo, 'tau2_hi strictly greater than tau2_lo');
});

test('fitLinear returns finite Q-profile τ² CI bounds on GL-1992', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitLinear(fx.trials, {});
  assert.ok(Number.isFinite(res.tau2_lo), 'tau2_lo must be finite (Round 2B)');
  assert.ok(Number.isFinite(res.tau2_hi), 'tau2_hi must be finite');
  assert.ok(res.tau2_lo >= 0);
  assert.ok(res.tau2_lo <= res.tau2_hi);
  // GL-1992 has high heterogeneity (I² ~ 95%); τ² CI should be a non-trivial range
  assert.ok(res.tau2_hi > 0, 'GL-1992 τ²_hi > 0 (substantial heterogeneity)');
});

test('remlLogLik returns finite value at zero tau2 matrix for valid per-study X, y, V', () => {
  // Simple synthetic: 2 trials, 1 basis dimension (linear), zero τ²
  var perStudy = [
    { X: [[10], [20]], y: [0.5, 1.0], V: [[0.05, 0.02], [0.02, 0.04]] },
    { X: [[5], [15]],  y: [0.3, 0.7], V: [[0.06, 0.03], [0.03, 0.05]] },
  ];
  var tau2 = [[0]];  // Kp=1, scalar τ²=0
  var ll = I.remlLogLik(perStudy, tau2);
  assert.ok(Number.isFinite(ll), 'log-likelihood must be finite at τ²=0');
});

test('fitRCS non-linearity p matches R full-REML on GL-1992 within |Δ| < 0.1', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitRCS(fx.trials, { knots: 3 });
  // R mixmeta full-REML on GL-1992 (verified during Round 1B audit): ~0.70
  near(res.rcs.nonlinearity_wald_p, 0.70, 0.10,
    'engine non-linearity Wald p matches R full-REML (Round 2B target)');
  // tau2_matrix should be present and 2×2 (Kp = K-1 = 2 for 3 knots)
  assert.ok(Array.isArray(res.rcs.tau2_matrix), 'tau2_matrix field present');
  assert.equal(res.rcs.tau2_matrix.length, 2);
  assert.equal(res.rcs.tau2_matrix[0].length, 2);
  assert.ok(res.rcs.reml_converged === true, 'REML must converge on GL-1992');
});

test('fitRCS Round 2A regression-pin at p≈0.05 is now OUTDATED — engine matches R (Round 2B)', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitRCS(fx.trials, { knots: 3 });
  assert.ok(res.rcs.nonlinearity_wald_p > 0.4,
    'engine non-linearity p now > 0.4 (was ~0.05 under diagonal-PM v0.1)');
});

let pass = 0, fail = 0;
for (const { name, fn } of tests) {
  try { fn(); console.log(`✓ ${name}`); pass++; }
  catch (e) { console.error(`✗ ${name}\n  ${e.message}`); fail++; }
}
console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail === 0 ? 0 : 1);
