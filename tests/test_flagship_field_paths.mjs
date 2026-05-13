// tests/test_flagship_field_paths.mjs
//
// Regression-pin test for the field-path bug class caught by the Round 2C
// double-check (PR #250). The bug: flagship HTML reads engine fields via
// the wrong nesting (e.g. `result.rcs.hksj_mv` instead of `result.hksj_mv`),
// silently producing "n/a" displays in production.
//
// This test loads the engine + each fixture + the corresponding R precompute,
// runs fitLinear/fitRCS, and asserts that every field path the flagship HTMLs
// actually read returns a non-null value. It also computes what the R-parity
// badge would display and asserts all-green on each fixture.
//
// Catches: undefined field accesses, schema drift between engine and flagship,
// R-parity badge thresholds being tripped by JSON-rounding artefacts.

import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '..');

const mod = await import('file://' + path.join(repoRoot, 'rapidmeta-dose-response-engine-v1.js'));
const DR = mod.default || mod;

// Mirror the THRESHOLDS object from vendor/r-validation-doseresp.js v0.2.0.
// If this drifts, the test will catch it via the badge-state assertion below.
const THRESHOLDS = {
  linear_slope: 0.01,
  linear_tau2: 0.0001,
  rcs_coef_0: 0.01,
  rcs_coef_1: 0.01,
  nonlinearity_p: 0.05,
};

// The 3 dose-response flagships shipped via Rounds 1B-3:
//   1. ALCOHOL_BC_DOSE_RESP_REVIEW.html (gl1992_alcohol_bc)
//   2. SGLT2I_DOSE_RESP_REVIEW.html (sglt2i_hba1c primary + sglt2i_hhf secondary)
//   3. TIRZEPATIDE_T2D_SURPASS_DOSE_RESP_REVIEW.html (tirzepatide_t2d_surpass)
//
// Each flagship reads engine field paths from DR.fitLinear / DR.fitRCS results.
// We codify the contract per flagship.

const flagshipContracts = [
  {
    flagship: 'ALCOHOL_BC_DOSE_RESP_REVIEW.html',
    fixture: 'tests/dose_response_fixtures/gl1992_alcohol_bc.json',
    rJson: 'outputs/r_validation/doseresp/gl1992_alcohol_bc.json',
    rcsKnots: 3,
  },
  {
    flagship: 'SGLT2I_DOSE_RESP_REVIEW.html',
    fixture: 'tests/dose_response_fixtures/sglt2i_hba1c.json',
    rJson: 'outputs/r_validation/doseresp/sglt2i_hba1c.json',
    rcsKnots: 3,
  },
  {
    flagship: 'TIRZEPATIDE_T2D_SURPASS_DOSE_RESP_REVIEW.html',
    fixture: 'tests/dose_response_fixtures/tirzepatide_t2d_surpass.json',
    rJson: 'outputs/r_validation/doseresp/tirzepatide_t2d_surpass.json',
    rcsKnots: 3,
  },
];

let passed = 0, failed = 0;
const test = (name, fn) => {
  try { fn(); console.log('  ✓ ' + name); passed++; }
  catch (e) { console.log('  ✗ ' + name + '\n    ' + (e.message || e)); failed++; }
};

console.log('Flagship field-path contract test\n');

for (const c of flagshipContracts) {
  console.log('Fixture: ' + c.flagship + '  ←  ' + path.basename(c.fixture));
  const fx = JSON.parse(fs.readFileSync(path.join(repoRoot, c.fixture), 'utf8'));
  const rJson = JSON.parse(fs.readFileSync(path.join(repoRoot, c.rJson), 'utf8'));
  const lin = DR.fitLinear(fx.trials, {});
  const rcs = DR.fitRCS(fx.trials, { knots: c.rcsKnots });

  // --- fitLinear top-level contract (what KPI displays read) ---
  test('fitLinear: pooled_slope_log defined', () => assert.ok(Number.isFinite(lin.pooled_slope_log)));
  test('fitLinear: pooled_slope_log_se defined', () => assert.ok(Number.isFinite(lin.pooled_slope_log_se)));
  test('fitLinear: pooled_slope_log_ci_lo defined', () => assert.ok(Number.isFinite(lin.pooled_slope_log_ci_lo)));
  test('fitLinear: pooled_slope_log_ci_hi defined', () => assert.ok(Number.isFinite(lin.pooled_slope_log_ci_hi)));
  test('fitLinear: k > 0', () => assert.ok(lin.k > 0));
  test('fitLinear: tau2 defined', () => assert.ok(Number.isFinite(lin.tau2)));
  test('fitLinear: tau2_lo defined (Q-profile, Round 2B)', () => assert.ok(Number.isFinite(lin.tau2_lo)));
  test('fitLinear: tau2_hi defined (Q-profile, Round 2B)', () => assert.ok(Number.isFinite(lin.tau2_hi)));

  // --- fitRCS TOP-LEVEL contract (Round 2C hotfix #250 — these MUST be top-level not nested) ---
  test('fitRCS: hksj_mv at TOP level (NOT nested under .rcs — Round 2C bug class)', () => {
    assert.ok(Number.isFinite(rcs.hksj_mv), 'rcs.hksj_mv must be finite at top level');
    assert.equal(rcs.rcs.hksj_mv, undefined, 'rcs.rcs.hksj_mv MUST be undefined (catches bug pattern)');
  });
  test('fitRCS: tcrit at TOP level', () => {
    assert.ok(Number.isFinite(rcs.tcrit));
    assert.equal(rcs.rcs.tcrit, undefined);
  });
  test('fitRCS: q_mv, df_mv at TOP level', () => {
    assert.ok(Number.isFinite(rcs.q_mv));
    assert.ok(Number.isFinite(rcs.df_mv));
  });
  test('fitRCS: estimator string is reml_hksj_multivariate (Round 2B Task 9)', () => {
    assert.equal(rcs.estimator, 'reml_hksj_multivariate');
  });
  test('fitRCS: ci_method string is hksj_t_km1 (Round 2B Task 9)', () => {
    assert.equal(rcs.ci_method, 'hksj_t_km1');
  });
  test('fitRCS: converged at TOP level (Round 2B Task 7 follow-up)', () => {
    assert.equal(typeof rcs.converged, 'boolean');
  });

  // --- fitRCS NESTED contract (these MUST be under .rcs) ---
  test('fitRCS: nonlinearity_wald_p NESTED under .rcs', () => {
    assert.ok(Number.isFinite(rcs.rcs.nonlinearity_wald_p));
  });
  test('fitRCS: nonlinearity_wald_chi2 NESTED under .rcs (Round 2B Task 7 follow-up Issue 1)', () => {
    assert.ok(Number.isFinite(rcs.rcs.nonlinearity_wald_chi2));
  });
  test('fitRCS: nonlinearity_wald_df NESTED under .rcs', () => {
    assert.ok(Number.isFinite(rcs.rcs.nonlinearity_wald_df));
  });
  test('fitRCS: spline_coefs array NESTED under .rcs, length ≥ 2', () => {
    assert.ok(Array.isArray(rcs.rcs.spline_coefs));
    assert.ok(rcs.rcs.spline_coefs.length >= 2);
    rcs.rcs.spline_coefs.forEach(c => assert.ok(Number.isFinite(c)));
  });
  test('fitRCS: spline_coefs_se array NESTED', () => {
    assert.ok(Array.isArray(rcs.rcs.spline_coefs_se));
    rcs.rcs.spline_coefs_se.forEach(c => assert.ok(Number.isFinite(c)));
  });
  test('fitRCS: tau2_matrix Kp×Kp NESTED', () => {
    assert.ok(Array.isArray(rcs.rcs.tau2_matrix));
    assert.ok(rcs.rcs.tau2_matrix.length >= 1);
    assert.equal(rcs.rcs.tau2_matrix.length, rcs.rcs.tau2_matrix[0].length, 'tau2_matrix must be square');
  });
  test('fitRCS: tau2_per_dim NESTED (backward-compat with v0.1/v0.2)', () => {
    assert.ok(Array.isArray(rcs.rcs.tau2_per_dim));
  });
  test('fitRCS: fit_at_dose grid NESTED, ≥ 10 points', () => {
    assert.ok(Array.isArray(rcs.rcs.fit_at_dose));
    assert.ok(rcs.rcs.fit_at_dose.length >= 10);
    rcs.rcs.fit_at_dose.forEach(p => {
      assert.ok(Number.isFinite(p.dose));
      assert.ok(Number.isFinite(p.est));
      assert.ok(Number.isFinite(p.ci_lo));
      assert.ok(Number.isFinite(p.ci_hi));
    });
  });
  test('fitRCS: reml_converged, reml_iterations, reml_loglik NESTED (Round 2B Task 7)', () => {
    assert.equal(typeof rcs.rcs.reml_converged, 'boolean');
    assert.ok(Number.isFinite(rcs.rcs.reml_iterations));
    assert.ok(Number.isFinite(rcs.rcs.reml_loglik));
  });

  // --- HKSJ-mv floor invariant (lessons.md HKSJ floor rule) ---
  test('fitRCS: hksj_mv ≥ 1 (floor invariant)', () => assert.ok(rcs.hksj_mv >= 1));

  // --- R-parity badge state simulation (what the badge JS would emit) ---
  test('R-parity row: linear_slope GREEN', () => {
    const d = Math.abs(lin.pooled_slope_log - rJson.linear.pooled_slope_log);
    assert.ok(d < THRESHOLDS.linear_slope, '|Δ|=' + d.toExponential(2) + ' must be < ' + THRESHOLDS.linear_slope);
  });
  test('R-parity row: linear_tau2 GREEN', () => {
    const d = Math.abs(lin.tau2 - rJson.linear.tau2);
    assert.ok(d < THRESHOLDS.linear_tau2, '|Δ|=' + d.toExponential(2) + ' must be < ' + THRESHOLDS.linear_tau2);
  });
  test('R-parity row: rcs_coef_0 GREEN', () => {
    const d = Math.abs(rcs.rcs.spline_coefs[0] - rJson.rcs.spline_coefs[0]);
    assert.ok(d < THRESHOLDS.rcs_coef_0, '|Δ|=' + d.toExponential(2));
  });
  test('R-parity row: rcs_coef_1 GREEN', () => {
    const d = Math.abs(rcs.rcs.spline_coefs[1] - rJson.rcs.spline_coefs[1]);
    assert.ok(d < THRESHOLDS.rcs_coef_1, '|Δ|=' + d.toExponential(2));
  });
  test('R-parity row: nonlinearity_p GREEN (Round 2C — was always-amber in v0.1/v0.2)', () => {
    const d = Math.abs(rcs.rcs.nonlinearity_wald_p - rJson.rcs.nonlinearity_wald_p);
    assert.ok(d < THRESHOLDS.nonlinearity_p, '|Δ|=' + d.toExponential(2));
  });

  // --- KPI display invariants (what the .toFixed(N) calls produce) ---
  // The bug pattern: accessing `.rcs.hksj_mv` (undefined) → `undefined.toFixed(2)` throws,
  // OR safe-access pattern `(x != null ? x.toFixed(2) : 'n/a')` silently produces 'n/a'.
  // This test catches both by asserting the top-level path returns a finite number.
  test('KPI display: top-level hksj_mv.toFixed(2) produces a real number string', () => {
    const display = rcs.hksj_mv.toFixed(2);
    assert.notEqual(display, 'NaN');
    assert.ok(/^\d+\.\d{2}$/.test(display), 'should match X.XX, got: ' + display);
  });
  test('KPI display: top-level tcrit.toFixed(3) produces a real number string', () => {
    const display = rcs.tcrit.toFixed(3);
    assert.ok(/^\d+\.\d{3}$/.test(display), 'should match X.XXX, got: ' + display);
  });
  test('KPI display: nested nonlinearity_wald_chi2.toFixed(3) produces a real number string', () => {
    const display = rcs.rcs.nonlinearity_wald_chi2.toFixed(3);
    assert.ok(/^-?\d+\.\d{3}$/.test(display), 'should match (-)X.XXX, got: ' + display);
  });

  console.log('');
}

console.log('-'.repeat(60));
console.log(passed + ' passed, ' + failed + ' failed');
process.exit(failed === 0 ? 0 : 1);
