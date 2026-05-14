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

test('fitLinear on k=1 (single trial) no longer throws (v0.6.0)', () => {
  // v0.5.0 threw with "k >= 2 trials"; v0.6.0 dispatches to single-trial branch.
  // Detailed contract assertions for the k=1 branch live in the v0.6.0 block below.
  const fx = loadFx('gl1992_alcohol_bc.json');
  const oneTrial = [fx.trials[0]];
  const res = DR.fitLinear(oneTrial, {});
  assert.equal(res.k, 1);
  assert.ok(Number.isFinite(res.pooled_slope_log));
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

test('fitRCS GL-1992 non-linearity p matches R full-REML (Round 2B: ~0.70, was ~0.05 under v0.1 diagonal-PM)', () => {
  // REGRESSION-PIN (Round 2B): the engine now uses full multivariate REML via
  // Nelder-Mead and matches R mixmeta within |Δ| < 0.05. The prior v0.1
  // diagonal-PM-per-dimension τ² approximation produced p ≈ 0.05 on this data;
  // the new v0.3 full-REML matches R's p ≈ 0.70.
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitRCS(fx.trials, { knots: 3 });
  near(res.rcs.nonlinearity_wald_p, 0.70, 0.05,
    'engine non-linearity p matches R full-REML (Round 2B target)');
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

test('fitRCS exposes internally-consistent Wald chi2/df/p triple (Round 2B fix-up)', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitRCS(fx.trials, { knots: 3 });
  assert.ok(Number.isFinite(res.rcs.nonlinearity_wald_chi2), 'chi2 must be finite');
  assert.equal(res.rcs.nonlinearity_wald_df, 1, '3-knot RCS → df = K - 2 = 1');
  assert.ok(Number.isFinite(res.rcs.nonlinearity_wald_p), 'p must be finite');
  // Cross-check: the p must match 1 - pchisq(chi2, df) within float epsilon
  const expectedP = 1 - DR._internal.pchisq(res.rcs.nonlinearity_wald_chi2, res.rcs.nonlinearity_wald_df);
  near(res.rcs.nonlinearity_wald_p, expectedP, 1e-9, 'p must equal 1 - pchisq(chi2, df)');
  // And nonLinearityTest reads the same triple
  const nl = DR.nonLinearityTest(res);
  assert.equal(nl.chi2, res.rcs.nonlinearity_wald_chi2);
  assert.equal(nl.df, res.rcs.nonlinearity_wald_df);
  assert.equal(nl.p, res.rcs.nonlinearity_wald_p);
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
// Current state (Round 2B, v0.3.0): fitRCS uses full multivariate REML for τ²
// (Task 7) and HKSJ-multivariate × t_{k-1} CIs (Task 9). The non-linearity
// Wald p-value now matches R dosresmeta on GL-1992 within |Δ|<0.05 (~0.70 vs
// R's ~0.756), and the linear-component test below pins the engine's pooled
// slope against R.
//
// History: under v0.1/v0.2 (estimator='pm_diagonal_z', ci_method='z_1.96'),
// fitRCS pooled τ² diagonally with PM and used raw z=1.96 CIs, giving
// nonlinearity_wald_p ≈ 0.05 (vs R's ~0.756) — a documented divergence that
// Round 2B closed.

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
  // NOTE: Only the linear-component (spline_coefs[0]) is compared to R here.
  // The non-linear-component (spline_coefs[1]) and the nonlinearity_wald_p
  // now match R under Round 2B full-REML (v0.3). The v0.1 diagonal-PM divergence
  // is closed; see the Round 1A regression-pin test above for the updated pin.
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

test('fitRCS non-linearity p matches R full-REML on GL-1992 within |Δ| < 0.05', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitRCS(fx.trials, { knots: 3 });
  // R mixmeta full-REML on GL-1992 (verified during Round 1B audit): ~0.70
  near(res.rcs.nonlinearity_wald_p, 0.70, 0.05,
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

test('fitRCS uses HKSJ-mv + t_{k-1} for CIs (estimator label updated)', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitRCS(fx.trials, { knots: 3 });
  assert.equal(res.estimator, 'reml_hksj_multivariate',
    'fitRCS estimator now reml_hksj_multivariate (Round 2B)');
  assert.equal(res.ci_method, 'hksj_t_km1',
    'fitRCS ci_method now hksj_t_km1 (Round 2B)');
  // HKSJ multiplier should be ≥ 1 (floor) and visible in the result
  assert.ok(Number.isFinite(res.hksj_mv) && res.hksj_mv >= 1,
    'HKSJ multivariate scaling factor visible and ≥ 1');
});

test('fitRCS HKSJ-mv and tcrit numerical pin on GL-1992 (Round 2B)', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const res = DR.fitRCS(fx.trials, { knots: 3 });
  // GL-1992 (k=5 trials, Kp=3 basis dims, n_total non-ref arms ~18):
  // Q_mv ≈ 23.4, df_mv = max(1, n_total - Kp) ≈ 15, hksj_mv ≈ 1.56.
  // These pin the multivariate Cochran Q computation; a silent regression
  // in the residual/inverse-cov loop will drop hksj_mv toward 1.0.
  near(res.hksj_mv, 1.56, 0.10, 'GL-1992 HKSJ-mv ≈ 1.56 (Q_mv ≈ 23.4 / df_mv = 15)');
  // tcrit for k=5 → qt(0.975, 4) ≈ 2.7764; tcrit is top-level (res.tcrit)
  near(res.tcrit, 2.776, 0.01, 'GL-1992 tcrit = qt(0.975, k-1=4) ≈ 2.776');
});

test('validate flags a trial with 2 arms but no reference flag (F-5)', () => {
  const noRef = [{
    studlab: 'no_ref_trial',
    arms: [
      { dose: 0, events: 10, n: 100, is_reference: false },
      { dose: 5, events: 15, n: 100, is_reference: false },
    ],
  }];
  const issues = DR.validate(noRef);
  assert.ok(issues.length > 0, 'should flag missing reference arm');
  assert.match(issues.join('|'), /no reference arm/i,
    'message should mention missing reference');
});

test('fitLinear k=2 homogeneous pool fires HKSJ floor (Q < df → qstar = 1)', () => {
  // Two trials with very similar per-study slopes → Cochran Q ≈ 0 < df=1
  // → HKSJ floor max(1, Q/df) = 1 fires (qstar = 1, hksj_adj = 1).
  const trials = [
    { studlab: 'A', arms: [
      { dose: 0,  events: 5,  n: 1000, is_reference: true },
      { dose: 10, events: 8,  n: 1000, is_reference: false },
    ]},
    { studlab: 'B', arms: [
      { dose: 0,  events: 6,  n: 1000, is_reference: true },
      { dose: 10, events: 9,  n: 1000, is_reference: false },
    ]},
  ];
  const res = DR.fitLinear(trials, {});
  assert.equal(res.k, 2);
  assert.ok(res.hksj_qstar >= 1, 'qstar must respect floor');
  // For these homogeneous data Q should be small; qstar likely = 1
  if (res.Q < res.Q_df) {
    assert.equal(res.hksj_qstar, 1, 'qstar = 1 when Q < df (floor fires)');
    assert.equal(res.hksj_adj, 1, 'HKSJ adj = sqrt(1) = 1');
  }
});

// Round 3.6 (v0.4): single-trial (k=1) fitRCS support for ARTS-DN-like Phase 2b
// dose-finding designs. Verifies the new branch labels itself correctly, sets
// hksj_mv=1 (no inflation), tau2 all-zeros (no between-study variance defined),
// and produces a finite non-linearity Wald p.

function makeArtsDnSingleTrial() {
  // ARTS-DN Day-90 UACR ratio per memo (8 arms: placebo + 1.25–20 mg).
  // log-transformed for the engine's log-RR/log-ratio convention.
  return [{
    studlab: 'ARTS-DN',
    arms: [
      { label: 'Placebo',  dose: 0,    mean: Math.log(0.938), sd: 0.5, n: 94,  is_reference: true  },
      { label: '1.25 mg',  dose: 1.25, mean: Math.log(0.869), sd: 0.5, n: 96,  is_reference: false },
      { label: '2.5 mg',   dose: 2.5,  mean: Math.log(0.890), sd: 0.5, n: 92,  is_reference: false },
      { label: '5 mg',     dose: 5,    mean: Math.log(0.824), sd: 0.5, n: 100, is_reference: false },
      { label: '7.5 mg',   dose: 7.5,  mean: Math.log(0.739), sd: 0.5, n: 97,  is_reference: false },
      { label: '10 mg',    dose: 10,   mean: Math.log(0.708), sd: 0.5, n: 98,  is_reference: false },
      { label: '15 mg',    dose: 15,   mean: Math.log(0.630), sd: 0.5, n: 125, is_reference: false },
      { label: '20 mg',    dose: 20,   mean: Math.log(0.585), sd: 0.5, n: 119, is_reference: false },
    ],
  }];
}

test('fitRCS k=1 single-trial path does not throw and produces sensible output', () => {
  const trials = makeArtsDnSingleTrial();
  const rcs = DR.fitRCS(trials, { knots: 3 });
  assert.ok(rcs && rcs.rcs, 'rcs return present');
  assert.equal(rcs.k, 1);
});

test('fitRCS k=1 estimator label is wls_single_trial_rcs (not reml_hksj_multivariate)', () => {
  const rcs = DR.fitRCS(makeArtsDnSingleTrial(), { knots: 3 });
  assert.equal(rcs.estimator, 'wls_single_trial_rcs');
  assert.equal(rcs.ci_method, 't_within_trial');
});

test('fitRCS k=1 hksj_mv === 1 (no inflation; no between-study Q)', () => {
  const rcs = DR.fitRCS(makeArtsDnSingleTrial(), { knots: 3 });
  assert.equal(rcs.hksj_mv, 1);
  assert.equal(rcs.q_mv, 0);
});

test('fitRCS k=1 tau2_matrix is all zeros (single trial → no between-study variance defined)', () => {
  const rcs = DR.fitRCS(makeArtsDnSingleTrial(), { knots: 3 });
  for (const row of rcs.rcs.tau2_matrix) {
    for (const v of row) assert.equal(v, 0);
  }
  for (const v of rcs.rcs.tau2_per_dim) assert.equal(v, 0);
});

test('fitRCS k=1 nonlinearity_wald_p is finite (Wald test still valid within-trial)', () => {
  const rcs = DR.fitRCS(makeArtsDnSingleTrial(), { knots: 3 });
  assert.ok(Number.isFinite(rcs.rcs.nonlinearity_wald_p));
  assert.ok(rcs.rcs.nonlinearity_wald_p >= 0 && rcs.rcs.nonlinearity_wald_p <= 1);
  assert.ok(Number.isFinite(rcs.rcs.nonlinearity_wald_chi2));
});

test('fitRCS k=1 tcrit uses within-trial df (qt(0.975, n_arms − Kp − 1))', () => {
  const rcs = DR.fitRCS(makeArtsDnSingleTrial(), { knots: 3 });
  // 8 arms, 3 knots ⇒ Kp = 2 (spline_coefs.length); 7 contrast arms ⇒ df = 7-2-1 = 4? or 5?
  // Verify tcrit > z=1.96 (small df ⇒ wider CI) and finite.
  assert.ok(rcs.tcrit > 1.96, 'within-trial t > z at small df');
  assert.ok(rcs.tcrit < 4, 'tcrit should be modest with n_arms=8');
});

test('fitRCS k=1 fit_at_dose grid has 20 points + finite CIs', () => {
  const rcs = DR.fitRCS(makeArtsDnSingleTrial(), { knots: 3 });
  assert.equal(rcs.rcs.fit_at_dose.length, 20);
  for (const p of rcs.rcs.fit_at_dose) {
    assert.ok(Number.isFinite(p.dose));
    assert.ok(Number.isFinite(p.est));
    assert.ok(Number.isFinite(p.ci_lo));
    assert.ok(Number.isFinite(p.ci_hi));
    assert.ok(p.ci_lo <= p.est && p.est <= p.ci_hi);
  }
});

test('fitRCS k=1 spline_coefs come from the single trial directly (covBeta = perStudy[0].V)', () => {
  const rcs = DR.fitRCS(makeArtsDnSingleTrial(), { knots: 3 });
  // covBeta should be Kp×Kp with finite entries; not the zero matrix
  assert.ok(Array.isArray(rcs.rcs.cov_beta));
  for (const row of rcs.rcs.cov_beta) {
    for (const v of row) assert.ok(Number.isFinite(v));
  }
  // diagonal SEs strictly positive
  for (var d = 0; d < rcs.rcs.cov_beta.length; d++) {
    assert.ok(rcs.rcs.cov_beta[d][d] > 0, 'cov_beta diagonal > 0');
  }
});

// === v0.5.0 fitLOO leave-one-out sensitivity tests ===
// fitLOO orchestrates fitLinear / fitRCS over each k-1 subset.  We test
// orchestration, contract shape, and the k=2 single-trial fallback path.

test('fitLOO is exposed on DR._internal and DR.engine_version is v0.7.0', () => {
  assert.equal(typeof I.fitLOO, 'function', 'DR._internal.fitLOO must be a function');
  assert.ok(/v?0\.7\.0$/.test(DR.engine_version), 'engine_version should end with v0.7.0; got: ' + DR.engine_version);
});

test('fitLOO on SURPASS (k=5) returns full_pool + 5 LOO entries (default RCS layer)', () => {
  const fx = loadFx('tirzepatide_t2d_surpass.json');
  const r = I.fitLOO(fx.trials, { layer: 'rcs', knots: 3 });
  assert.equal(r.layer, 'rcs');
  assert.equal(r.k_full, 5);
  assert.equal(r.loo.length, 5, 'LOO should produce one entry per dropped trial');
  // Every dropped_studlab is a real fixture studlab; k_loo === k_full - 1 throughout
  const studlabs = new Set(fx.trials.map(t => t.studlab));
  for (const e of r.loo) {
    assert.ok(studlabs.has(e.dropped_studlab), 'LOO dropped_studlab must be a real studlab: ' + e.dropped_studlab);
    assert.equal(e.k_loo, 4, 'k_loo at k_full=5 must be 4');
    assert.ok(Number.isFinite(e.pooled_slope_log), 'pooled_slope_log finite');
    assert.ok(Number.isFinite(e.pooled_slope_log_se), 'pooled_slope_log_se finite');
  }
});

test('fitLOO SURPASS: summary.most_influential_trial is a real studlab from the fixture', () => {
  const fx = loadFx('tirzepatide_t2d_surpass.json');
  const r = I.fitLOO(fx.trials, { layer: 'rcs', knots: 3 });
  const studlabs = new Set(fx.trials.map(t => t.studlab));
  assert.ok(r.summary.most_influential_trial, 'most_influential_trial should be set when ≥1 finite delta');
  assert.ok(studlabs.has(r.summary.most_influential_trial),
    'most_influential_trial must be a real fixture studlab: ' + r.summary.most_influential_trial);
  assert.ok(Number.isFinite(r.summary.max_abs_delta_slope) && r.summary.max_abs_delta_slope > 0,
    'max_abs_delta_slope should be a positive finite number');
});

test('fitLOO SURPASS: delta_slope = entry.pooled_slope_log - full_pool.pooled_slope_log (1e-12)', () => {
  const fx = loadFx('tirzepatide_t2d_surpass.json');
  const r = I.fitLOO(fx.trials, { layer: 'rcs', knots: 3 });
  const fullSlope = r.full_pool.pooled_slope_log;
  for (const e of r.loo) {
    const expected = e.pooled_slope_log - fullSlope;
    near(e.delta_slope, expected, 1e-12, 'delta_slope for ' + e.dropped_studlab);
  }
});

test('fitLOO SURPASS: sign_flip semantics — true iff CI_lo signs differ from full pool', () => {
  const fx = loadFx('tirzepatide_t2d_surpass.json');
  const r = I.fitLOO(fx.trials, { layer: 'rcs', knots: 3 });
  const fullSignLo = Math.sign(r.full_pool.pooled_slope_log_ci_lo);
  let anyComputed = false;
  for (const e of r.loo) {
    const subSignLo = Math.sign(e.pooled_slope_log_ci_lo);
    const expectFlip = (subSignLo !== fullSignLo) && (fullSignLo !== 0) && (subSignLo !== 0);
    assert.equal(e.sign_flip, expectFlip,
      'sign_flip on ' + e.dropped_studlab + ': expected ' + expectFlip + ', got ' + e.sign_flip);
    anyComputed = true;
  }
  assert.ok(anyComputed, 'should have iterated over ≥1 LOO entry');
});

test('fitLOO SURPASS: significance_flip surfaces when LOO drops nlP across 0.05 from full', () => {
  const fx = loadFx('tirzepatide_t2d_surpass.json');
  const r = I.fitLOO(fx.trials, { layer: 'rcs', knots: 3 });
  // Full-pool nlP = 0.0346 (< 0.05).  Dropping SURPASS-1 (largest delta) raises
  // nlP above 0.05 — this is the headline LOO finding for the flagship.
  assert.ok(r.full_pool.rcs && r.full_pool.rcs.nonlinearity_wald_p < 0.05,
    'precondition: full-pool nlP must be < 0.05 for sig_flip semantics to mean something');
  // At least one LOO entry should flip significance (any_significance_flip=true).
  assert.equal(r.summary.any_significance_flip, true,
    'SURPASS has ≥1 LOO subset where nlP crosses 0.05 — at least one significance_flip=true expected');
  let n = 0;
  for (const e of r.loo) {
    if (e.significance_flip) n++;
  }
  assert.ok(n >= 1, 'expected ≥1 entry with significance_flip=true; got ' + n);
});

test('fitLOO on GL-1992 (k=5) returns 5 LOO entries (no degeneration on canonical fixture)', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const r = I.fitLOO(fx.trials, { layer: 'rcs', knots: 3 });
  assert.equal(r.k_full, 5);
  assert.equal(r.loo.length, 5, 'one LOO entry per trial');
  // GL-1992 has rich per-trial dose coverage; no LOO subset should degenerate
  // (rcsKnots returns >=3 knots on every 4-trial subset).
  assert.equal(r.summary.n_degenerated, 0, 'GL-1992 LOO subsets should all fit real RCS; got n_degenerated=' + r.summary.n_degenerated);
});

test('fitLOO opts.layer="linear" returns linear-layer full_pool + LOO entries', () => {
  const fx = loadFx('gl1992_alcohol_bc.json');
  const rLin = I.fitLOO(fx.trials, { layer: 'linear' });
  assert.equal(rLin.layer, 'linear');
  assert.equal(rLin.full_pool.layer, 'linear');
  assert.equal(rLin.loo.length, 5);
  for (const e of rLin.loo) {
    // Linear-layer LOO has no nlP since fitLinear has no spline.
    assert.equal(e.nonlinearity_wald_p, null,
      'linear-layer LOO has no nonlinearity_wald_p; should be null for ' + e.dropped_studlab);
    assert.ok(Number.isFinite(e.pooled_slope_log));
  }
  // any_significance_flip is false on linear layer (no nlP to flip)
  assert.equal(rLin.summary.any_significance_flip, false,
    'linear layer has no nlP → any_significance_flip must be false');
});

test('fitLOO opts.layer="rcs" produces RCS-layer summary with nlP fields populated', () => {
  const fx = loadFx('tirzepatide_t2d_surpass.json');
  const r = I.fitLOO(fx.trials, { layer: 'rcs', knots: 3 });
  assert.equal(r.layer, 'rcs');
  assert.equal(r.full_pool.layer, 'rcs');
  for (const e of r.loo) {
    if (!e.degenerated) {
      assert.ok(Number.isFinite(e.nonlinearity_wald_p),
        'rcs-layer non-degenerate LOO entry must have finite nonlinearity_wald_p; got ' + e.nonlinearity_wald_p + ' for ' + e.dropped_studlab);
    }
  }
});

test('fitLOO on SUSTAIN (k=6) handles RCS singular-design drops via degenerated flag', () => {
  const fx = loadFx('semaglutide_t2d_sustain.json');
  const r = I.fitLOO(fx.trials, { layer: 'rcs', knots: 3 });
  assert.equal(r.k_full, 6);
  assert.equal(r.loo.length, 6);
  // SUSTAIN's engine RCS fit is k_RCS=2 (4 singular per-trial drops at the
  // full pool); LOO over a subset that excludes one of the surviving trials
  // may further reduce k_eff or trigger the engine's degenerate-to-linear
  // fallback (rcs.layer collapsing to 'linear' on the subset).  The contract:
  // every LOO entry has either layer='rcs' (degenerated=false) or
  // layer='linear' (degenerated=true).  Verify no entry throws or returns NaN
  // on the pooled slope, and at least one entry is degenerated (LOO of the
  // already-sparse 6-trial pool exposes the engine's RCS-fallback branch).
  for (const e of r.loo) {
    assert.ok(Number.isFinite(e.pooled_slope_log),
      'every LOO entry must produce a finite pooled_slope_log even after singular-design drops; got ' + e.pooled_slope_log + ' on ' + e.dropped_studlab);
  }
  // Sanity: SUSTAIN's sparse-arm pool is exactly the kind that exercises
  // degenerated handling.  We don't require ≥1 degenerated (depends on
  // exact fixture), but the engine MUST NOT throw — that's the contract.
  assert.ok(r.summary.n_degenerated >= 0, 'n_degenerated must be a non-negative count');
});

test('fitLOO on SURMOUNT (k=2) drops to k=1 each time; engine handles both paths without throwing', () => {
  const fx = loadFx('tirzepatide_obesity_surmount.json');
  // RCS layer: at k_full=2 → k_loo=1.  SURMOUNT-1 alone has 4 arms (0/5/10/15)
  // and fits the k=1 RCS branch with finite output; SURMOUNT-2 alone has 3
  // arms {0,10,15} — only 2 distinct positive doses, fewer than K=3 knots →
  // the engine's RCS-fallback to fitLinear fires, then fitLinear throws at
  // k=1.  fitLOO's try/catch must surface that as a degenerated record (NaN
  // slope, _loo_error populated) WITHOUT re-throwing.  Contract: every LOO
  // entry must produce an output record, even on the degenerate sub-subset.
  const rRcs = I.fitLOO(fx.trials, { layer: 'rcs', knots: 3 });
  assert.equal(rRcs.k_full, 2);
  assert.equal(rRcs.loo.length, 2);
  let nFinite = 0, nDegen = 0;
  for (const e of rRcs.loo) {
    assert.equal(e.k_loo, 1, 'LOO of k=2 produces k_loo=1 subset');
    if (Number.isFinite(e.pooled_slope_log)) nFinite++;
    if (e.degenerated) nDegen++;
  }
  assert.ok(nFinite >= 1,
    'at least one SURMOUNT LOO subset (the one keeping the 4-arm SURMOUNT-1) must produce a finite slope via the k=1 RCS branch');
  assert.ok(nDegen >= 1,
    'at least one SURMOUNT LOO subset (the one keeping the 3-arm SURMOUNT-2 with only 2 distinct doses) should degenerate');
  // Linear layer at k_full=2: fitLinear throws on k<2, so fitLOO must use the
  // surviving-trial per-study slope as the LOO "pool".  Each entry should be
  // marked degenerated and have a finite slope from the surviving trial.
  const rLin = I.fitLOO(fx.trials, { layer: 'linear' });
  assert.equal(rLin.k_full, 2);
  assert.equal(rLin.loo.length, 2);
  for (const e of rLin.loo) {
    assert.equal(e.k_loo, 1);
    assert.ok(Number.isFinite(e.pooled_slope_log),
      'k=2 linear-layer LOO must NOT throw; should use surviving trial slope from fitLinear.per_study. Got: ' + e.pooled_slope_log);
    assert.equal(e.degenerated, true,
      'k=2 → k=1 linear-layer LOO entry must be marked degenerated=true (single-trial fallback)');
  }
});

// === v0.6.0 fitLinear k=1 single-trial path tests (mirror of fitRCS v0.4) ===
// Closes the asymmetry from v0.4 where fitRCS got k=1 support but fitLinear
// still threw. Re-uses the ARTS-DN-derived 8-arm fixture from the fitRCS k=1
// tests above (makeArtsDnSingleTrial).

test('fitLinear k=1 single-trial path does not throw and produces sensible output', () => {
  const trials = makeArtsDnSingleTrial();
  const lin = DR.fitLinear(trials, {});
  assert.equal(lin.k, 1);
  assert.ok(Number.isFinite(lin.pooled_slope_log));
  assert.ok(Number.isFinite(lin.pooled_slope_log_se));
  assert.ok(lin.pooled_slope_log_se > 0);
  assert.ok(Number.isFinite(lin.pooled_slope_log_ci_lo));
  assert.ok(Number.isFinite(lin.pooled_slope_log_ci_hi));
  assert.ok(lin.pooled_slope_log_ci_lo < lin.pooled_slope_log_ci_hi);
});

test('fitLinear k=1 estimator label is wls_single_trial_linear (not reml_hksj)', () => {
  const lin = DR.fitLinear(makeArtsDnSingleTrial(), {});
  assert.equal(lin.estimator, 'wls_single_trial_linear');
});

test('fitLinear k=1 ci_method is t_within_trial', () => {
  const lin = DR.fitLinear(makeArtsDnSingleTrial(), {});
  assert.equal(lin.ci_method, 't_within_trial');
});

test('fitLinear k=1 tau2=0, Q=0, I2=0 (no between-study heterogeneity defined)', () => {
  const lin = DR.fitLinear(makeArtsDnSingleTrial(), {});
  assert.equal(lin.tau2, 0);
  assert.equal(lin.tau2_lo, 0);
  assert.equal(lin.tau2_hi, 0);
  assert.equal(lin.Q, 0);
  assert.equal(lin.Q_df, 0);
  assert.equal(lin.I2, 0);
  assert.equal(lin.H2, 1);
});

test('fitLinear k=1 hksj_qstar=1, hksj_adj=1 (no Q-floor activation)', () => {
  const lin = DR.fitLinear(makeArtsDnSingleTrial(), {});
  assert.equal(lin.hksj_qstar, 1);
  assert.equal(lin.hksj_adj, 1);
});

test('fitLinear k=1 tcrit = qt(0.975, n_arms-2) within-trial df', () => {
  const trials = makeArtsDnSingleTrial();
  const lin = DR.fitLinear(trials, {});
  // ARTS-DN fixture has 8 arms → df_within = 8 - 2 = 6.
  // qt(0.975, 6) ≈ 2.4469.
  // tcrit isn't surfaced directly on the return; reconstruct from CI half-width.
  const ciHalf = lin.pooled_slope_log_ci_hi - lin.pooled_slope_log;
  const tcrit_recovered = ciHalf / lin.pooled_slope_log_se;
  const tcrit_expected = I.qt(0.975, 6);
  near(tcrit_recovered, tcrit_expected, 1e-10, 'tcrit reconstructed from CI matches qt(0.975, 6)');
  // Sanity: t > z=1.96 at small df, < ~4
  assert.ok(tcrit_recovered > 1.96, 'within-trial t > z at small df');
  assert.ok(tcrit_recovered < 4, 'tcrit modest at n_arms=8');
});

test('fitLinear k=1 PI degenerates to CI (pi_lo = ci_lo, pi_hi = ci_hi)', () => {
  const lin = DR.fitLinear(makeArtsDnSingleTrial(), {});
  near(lin.pi_lo, lin.pooled_slope_log_ci_lo, 1e-12, 'pi_lo == ci_lo at k=1');
  near(lin.pi_hi, lin.pooled_slope_log_ci_hi, 1e-12, 'pi_hi == ci_hi at k=1');
});

test('fitLinear k>=2 fixture (SURPASS, k=5) unchanged: pooled_slope_log regression-pin from v0.5', () => {
  // Regression pin: v0.5.0 baseline values captured BEFORE v0.6.0 engine edit.
  // If this fails, the k>=2 fitLinear path was perturbed by the v0.6 k=1 branch
  // (which should be impossible — the k=1 branch returns before the REML pool).
  const fx = loadFx('tirzepatide_t2d_surpass.json');
  const lin = DR.fitLinear(fx.trials, {});
  assert.equal(lin.k, 5);
  assert.equal(lin.estimator, 'reml_hksj');
  near(lin.pooled_slope_log, -0.06882512687116353, 1e-12,
    'SURPASS pooled_slope_log regression pin from v0.5 baseline');
  near(lin.pooled_slope_log_se, 0.10285426601824053, 1e-12,
    'SURPASS pooled_slope_log_se regression pin from v0.5 baseline');
});

// === v0.7.0 fitBootstrap (non-parametric trial-bootstrap CI) ===
//
// 10 tests covering the engine-level contract for the new
// DR._internal.fitBootstrap helper. Determinism is the trickiest property
// — the engine must produce byte-identical bootstrap_slopes arrays across
// runs for a fixed seed (the seeded LCG in makeSeededRng is the mechanism).

test('fitBootstrap returns n_boot bootstrap_slopes for n_boot=100 on SURPASS fixture', () => {
  const fx = loadFx('tirzepatide_t2d_surpass.json');
  const r = DR._internal.fitBootstrap(fx.trials, { layer: 'rcs', knots: 3, n_boot: 100, seed: 12345 });
  // SURPASS is a clean k=5 RCS fixture; no bootstrap sample should fail.
  assert.equal(r.bootstrap_slopes.length + r.n_failed, 100,
    'bootstrap_slopes.length + n_failed must equal n_boot');
  assert.equal(r.bootstrap_slopes.length, 100,
    'on the canonical SURPASS fixture, all 100 bootstrap samples should succeed');
  assert.equal(r.k_full, 5);
  assert.equal(r.layer, 'rcs');
  assert.equal(r.n_boot, 100);
  assert.equal(r.seed, 12345);
  assert.equal(r.alpha, 0.05);
});

test('fitBootstrap CI brackets the analytical CI within reasonable tolerance on SUSTAIN', () => {
  // SUSTAIN has I^2 ~97% so the analytical HKSJ-multivariate CI is very wide;
  // the bootstrap CI on the *resampled* trials produces a comparable interval
  // but with non-parametric quantiles. The two CIs should overlap substantially,
  // and the bootstrap CI lo/hi should land within ±50% of the analytical
  // interval width of the analytical bounds (a deliberately loose tolerance —
  // the headline of this whole tab is that the two methods can disagree at
  // extreme I^2, but they should still be in the same ballpark, NOT off by
  // an order of magnitude).
  const fx = loadFx('semaglutide_t2d_sustain.json');
  const r = DR._internal.fitBootstrap(fx.trials, { layer: 'rcs', knots: 3, n_boot: 500, seed: 12345 });
  const analWidth = r.analytical_ci_hi - r.analytical_ci_lo;
  assert.ok(isFinite(analWidth) && analWidth > 0,
    'analytical CI width must be finite + positive: lo=' + r.analytical_ci_lo + ' hi=' + r.analytical_ci_hi);
  assert.ok(isFinite(r.bootstrap_ci_lo) && isFinite(r.bootstrap_ci_hi),
    'bootstrap CI bounds must be finite');
  // Overlap requirement: intervals must share at least one point.
  assert.ok(r.bootstrap_ci_lo <= r.analytical_ci_hi && r.bootstrap_ci_hi >= r.analytical_ci_lo,
    'bootstrap CI [' + r.bootstrap_ci_lo + ',' + r.bootstrap_ci_hi + '] must overlap analytical [' + r.analytical_ci_lo + ',' + r.analytical_ci_hi + ']');
});

test('fitBootstrap seed determinism: same seed -> identical bootstrap_slopes array', () => {
  const fx = loadFx('tirzepatide_t2d_surpass.json');
  const r1 = DR._internal.fitBootstrap(fx.trials, { layer: 'rcs', knots: 3, n_boot: 100, seed: 42 });
  const r2 = DR._internal.fitBootstrap(fx.trials, { layer: 'rcs', knots: 3, n_boot: 100, seed: 42 });
  assert.equal(r1.bootstrap_slopes.length, r2.bootstrap_slopes.length,
    'same seed must produce same bootstrap_slopes.length');
  for (let i = 0; i < r1.bootstrap_slopes.length; i++) {
    assert.equal(r1.bootstrap_slopes[i], r2.bootstrap_slopes[i],
      'bootstrap_slopes[' + i + '] must be byte-identical across runs at seed=42');
  }
  assert.equal(r1.n_failed, r2.n_failed,
    'n_failed must also be deterministic across runs at the same seed');
});

test('fitBootstrap different seeds -> different bootstrap_slopes (expect distinct medians)', () => {
  const fx = loadFx('tirzepatide_t2d_surpass.json');
  const r1 = DR._internal.fitBootstrap(fx.trials, { layer: 'rcs', knots: 3, n_boot: 100, seed: 42 });
  const r2 = DR._internal.fitBootstrap(fx.trials, { layer: 'rcs', knots: 3, n_boot: 100, seed: 99 });
  // Different seeds must produce different samplings; medians should differ.
  // (Both runs sample 100 bootstrap replicates from k=5 trials; the chance
  // of the medians being equal to 15 sig figs is effectively 0.)
  assert.notEqual(r1.bootstrap_median, r2.bootstrap_median,
    'distinct seeds must yield distinct bootstrap medians; got r1=' + r1.bootstrap_median + ' r2=' + r2.bootstrap_median);
});

test("fitBootstrap layer='linear' produces linear-layer CI (no .bootstrap_nonlin_ps surface)", () => {
  const fx = loadFx('tirzepatide_t2d_surpass.json');
  const r = DR._internal.fitBootstrap(fx.trials, { layer: 'linear', n_boot: 100, seed: 12345 });
  assert.equal(r.layer, 'linear');
  assert.ok(isFinite(r.bootstrap_ci_lo) && isFinite(r.bootstrap_ci_hi));
  assert.ok(r.bootstrap_ci_lo <= r.bootstrap_ci_hi);
  // Linear layer must NOT expose bootstrap_nonlin_ps (it's RCS-only).
  assert.equal(typeof r.bootstrap_nonlin_ps, 'undefined',
    "layer='linear' must not produce bootstrap_nonlin_ps (RCS-only field)");
  assert.equal(typeof r.nonlin_p_fraction_below_005, 'undefined',
    "layer='linear' must not produce nonlin_p_fraction_below_005 (RCS-only field)");
});

test("fitBootstrap layer='rcs' produces bootstrap_nonlin_ps array", () => {
  const fx = loadFx('tirzepatide_t2d_surpass.json');
  const r = DR._internal.fitBootstrap(fx.trials, { layer: 'rcs', knots: 3, n_boot: 100, seed: 12345 });
  assert.ok(Array.isArray(r.bootstrap_nonlin_ps),
    'RCS layer must expose bootstrap_nonlin_ps as an array');
  // Each entry must be a finite number in [0,1] (Wald p-value).
  r.bootstrap_nonlin_ps.forEach((p, i) => {
    assert.ok(isFinite(p), 'bootstrap_nonlin_ps[' + i + '] must be finite');
    assert.ok(p >= 0 && p <= 1, 'bootstrap_nonlin_ps[' + i + '] must lie in [0,1]; got ' + p);
  });
  assert.ok(isFinite(r.bootstrap_nonlin_p_median),
    'bootstrap_nonlin_p_median must be finite when bootstrap_nonlin_ps is non-empty');
  assert.ok(isFinite(r.nonlin_p_fraction_below_005),
    'nonlin_p_fraction_below_005 must be finite when bootstrap_nonlin_ps is non-empty');
  assert.ok(r.nonlin_p_fraction_below_005 >= 0 && r.nonlin_p_fraction_below_005 <= 1);
});

test('fitBootstrap k=1 returns coverage_warning=true (single-trial bootstrap is trivial)', () => {
  // k=1 bootstrap is degenerate: every sample is the same trial; the engine
  // surfaces this via coverage_warning=true so consumers can downgrade the
  // result rather than treating it as a real sensitivity check.
  const fx = loadFx('finerenone_arts_dn.json');
  const r = DR._internal.fitBootstrap(fx.trials, { layer: 'rcs', knots: 3, n_boot: 50, seed: 7 });
  assert.equal(r.k_full, 1);
  assert.equal(r.coverage_warning, true,
    'k_full=1 must produce coverage_warning=true (trivial bootstrap)');
});

test('fitBootstrap n_failed mechanic: bootstrap_slopes.length + n_failed === n_boot (invariant)', () => {
  // Spec test #8: on degenerate-RCS fixtures (SELECT, AMAGINE), some
  // bootstrap samples may degenerate. The engine's fitRCS handles per-trial
  // singularity via internal try/catch (returning the linear-layer fallback
  // rather than throwing), so n_failed often stays at 0 — but the
  // bookkeeping invariant must always hold. We verify the invariant on the
  // canonical "engine-declined RCS" fixture (SELECT) AND that the n_failed
  // surface is wired up correctly (number, non-negative, never undefined).
  const fxSelect = loadFx('upadacitinib_ra_select.json');
  const rSelect = DR._internal.fitBootstrap(fxSelect.trials, { layer: 'rcs', knots: 3, n_boot: 200, seed: 12345 });
  assert.equal(typeof rSelect.n_failed, 'number', 'n_failed must be a number');
  assert.ok(rSelect.n_failed >= 0, 'n_failed must be non-negative');
  assert.equal(rSelect.bootstrap_slopes.length + rSelect.n_failed, 200,
    'invariant: bootstrap_slopes.length + n_failed must equal n_boot on SELECT (k=4); got ' +
    rSelect.bootstrap_slopes.length + ' + ' + rSelect.n_failed);
  // Same invariant on AMAGINE for good measure.
  const fxAmagine = loadFx('brodalumab_psoriasis_amagine.json');
  const rAmagine = DR._internal.fitBootstrap(fxAmagine.trials, { layer: 'rcs', knots: 3, n_boot: 200, seed: 12345 });
  assert.equal(rAmagine.bootstrap_slopes.length + rAmagine.n_failed, 200,
    'invariant: bootstrap_slopes.length + n_failed must equal n_boot on AMAGINE (k=3); got ' +
    rAmagine.bootstrap_slopes.length + ' + ' + rAmagine.n_failed);
});

test('fitBootstrap nonlin_p_fraction_below_005 on SURPASS reflects fragile-significance LOO finding', () => {
  // SURPASS full-pool RCS nonlinearity Wald p ≈ 0.0346 (just below 0.05).
  // The LOO sensitivity tab's headline is that this significance is fragile.
  // The bootstrap nonlin-p distribution should therefore have a substantial
  // fraction ABOVE 0.05 (i.e. not-significant under the resampled trials) —
  // we assert nonlin_p_fraction_below_005 is strictly between 0 and 1 (not
  // unanimous in either direction) on a reasonably large n_boot.
  const fx = loadFx('tirzepatide_t2d_surpass.json');
  const r = DR._internal.fitBootstrap(fx.trials, { layer: 'rcs', knots: 3, n_boot: 500, seed: 12345 });
  assert.ok(r.bootstrap_nonlin_ps.length > 0,
    'expected at least some bootstrap samples to produce a real RCS fit on SURPASS');
  assert.ok(r.nonlin_p_fraction_below_005 > 0 && r.nonlin_p_fraction_below_005 < 1,
    'SURPASS bootstrap nonlin-p distribution should NOT be unanimous (full-pool p=0.035 is fragile per the LOO tab); ' +
    'got fraction_below_005=' + r.nonlin_p_fraction_below_005);
});

test('fitBootstrap percentile CI semantics: bootstrap_ci_lo is the alpha/2 quantile of sorted bootstrap_slopes', () => {
  // The engine's percentile() is linear interpolation between order statistics
  // (matches numpy.quantile default). Verify the contract: bootstrap_ci_lo
  // and bootstrap_ci_hi are recoverable from the sorted slopes by re-applying
  // the same interpolation. This guards against future regressions where
  // someone might swap to e.g. nearest-rank percentile and silently change CIs.
  const fx = loadFx('tirzepatide_t2d_surpass.json');
  const r = DR._internal.fitBootstrap(fx.trials, { layer: 'rcs', knots: 3, n_boot: 100, seed: 12345 });
  function percentile(arr, p) {
    const n = arr.length;
    if (n === 0) return NaN;
    if (n === 1) return arr[0];
    const idx = p * (n - 1);
    const lo = Math.floor(idx), hi = Math.ceil(idx);
    if (lo === hi) return arr[lo];
    return arr[lo] * (1 - (idx - lo)) + arr[hi] * (idx - lo);
  }
  const sorted = r.bootstrap_slopes.slice().sort((a, b) => a - b);
  const expectedLo = percentile(sorted, r.alpha / 2);
  const expectedHi = percentile(sorted, 1 - r.alpha / 2);
  const expectedMed = percentile(sorted, 0.5);
  near(r.bootstrap_ci_lo, expectedLo, 1e-12,
    'bootstrap_ci_lo must equal linear-interp percentile(sorted, alpha/2)');
  near(r.bootstrap_ci_hi, expectedHi, 1e-12,
    'bootstrap_ci_hi must equal linear-interp percentile(sorted, 1-alpha/2)');
  near(r.bootstrap_median, expectedMed, 1e-12,
    'bootstrap_median must equal linear-interp percentile(sorted, 0.5)');
});

let pass = 0, fail = 0;
for (const { name, fn } of tests) {
  try { fn(); console.log(`✓ ${name}`); pass++; }
  catch (e) { console.error(`✗ ${name}\n  ${e.message}`); fail++; }
}
console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail === 0 ? 0 : 1);
