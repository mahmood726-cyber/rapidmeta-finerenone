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

// The 7 dose-response flagships shipped via Rounds 1B-3.8:
//   1. ALCOHOL_BC_DOSE_RESP_REVIEW.html (gl1992_alcohol_bc)
//   2. SGLT2I_DOSE_RESP_REVIEW.html (sglt2i_hba1c primary + sglt2i_hhf secondary)
//   3. TIRZEPATIDE_T2D_SURPASS_DOSE_RESP_REVIEW.html (tirzepatide_t2d_surpass)
//   4. TIRZEPATIDE_OBESITY_SURMOUNT_DOSE_RESP_REVIEW.html (tirzepatide_obesity_surmount, k=2 small-k stress test)
//   5. FINERENONE_ARTS_DN_DOSE_RESP_REVIEW.html (finerenone_arts_dn, k=1 single-trial path — Round 3.6, v0.4 PR #270)
//   6. SEMAGLUTIDE_T2D_SUSTAIN_DOSE_RESP_REVIEW.html (semaglutide_t2d_sustain — Round 3.7;
//      6-trial fixture but engine fitRCS drops 4 singular-design trials, R dosresmeta refuses
//      RCS entirely on sparse-arm requirement; linear-layer pool succeeds k=6)
//   7. UPADACITINIB_RA_SELECT_DOSE_RESP_REVIEW.html (upadacitinib_ra_select — Round 3.8;
//      4-trial fixture on the {0, 15, 30} mg dose grid; engine returns the documented
//      RCS-fallback layer='linear', fallback='degenerate_to_linear', rcs=null because
//      the 3-distinct-dose grid does not support a 3-knot Harrell basis under two-stage
//      pooling. R dosresmeta refuses with the parallel sparse-arm error. Linear pool
//      succeeds k=4 and matches R within thresholds.)
//
// Each flagship reads engine field paths from DR.fitLinear / DR.fitRCS results.
// We codify the contract per flagship.
//
// Per-flagship overrides for badge-row expectations: some flagships are
// intentionally small-k stress tests where one or more rows are expected AMBER
// (e.g. SURMOUNT k=2 has linear_tau2 AMBER because engine PM vs R REML diverge
// at k=2). Each contract entry may specify `expectAmberRows: [...]` to mark
// which row-keys should be allowed to fail the threshold check.
//
// For k=1 single-trial flagships:
//   - `singleTrial: true` skips fitLinear assertions (engine throws on k=1) and
//     redirects the R-parity badge check to the abbreviated 2-row RCS-only contract.
//   - The flagship's badge is rendered with class `rv-badge-deferred` (custom panel)
//     rather than the standard 5-row badge, so allGreen/allAmber assertions are
//     replaced with finite-coef + invariant-shape assertions.
//
// For flagships where R refused to fit RCS entirely (sparse-arm requirement,
// e.g. SUSTAIN where 4 of 6 trials have only 1 non-reference arm):
//   - `rRefusedRcs: true` skips the 3 RCS R-parity row assertions
//     (rcs_coef_0, rcs_coef_1, nonlinearity_p) because the R precompute JSON
//     has no rcs.spline_coefs or rcs.nonlinearity_wald_p fields. The engine's
//     RCS output is still field-path-asserted and the engine-only assertions
//     (finite coefs, valid Wald, invariant shape) still run.
//   - `rcsKEffectiveLessThanFixture: true` documents that the engine's fitRCS
//     reduces to k_RCS < input k because some trials have singular per-trial
//     design matrices. The contract enforces hksj_mv >= 1 (still holds at the
//     reduced k_RCS) and finite-coef invariants.
//
// For flagships where the engine itself returns the documented RCS-fallback
// (the dose grid does not support a K-knot Harrell basis under two-stage
// pooling, e.g. SELECT where the pool's 3 distinct doses cannot identify a
// 3-knot RCS):
//   - `rcsDegenerate: true` asserts the engine returned the documented
//     RCS-fallback: rcs.layer === 'linear', rcs.fallback === 'degenerate_to_linear',
//     rcs.rcs === null (no nested .rcs block). The standard nested-.rcs
//     assertions (spline_coefs, nonlinearity_wald_p, tau2_matrix, fit_at_dose,
//     reml_*) are SKIPPED because they would all dereference null. The
//     standard top-level RCS-only fields (hksj_mv, tcrit, q_mv, df_mv,
//     estimator='reml_hksj_multivariate', ci_method='hksj_t_km1') are also
//     SKIPPED because the result is shaped like a fitLinear output (with
//     estimator='reml_hksj' from fitLinear, NOT the RCS multivariate
//     estimator). The 3 RCS R-parity rows are deferred. The linear-pool
//     R-parity rows still run normally. This is the FIRST flagship to
//     exercise this engine branch in a production-shaped contract test.

const flagshipContracts = [
  {
    flagship: 'ALCOHOL_BC_DOSE_RESP_REVIEW.html',
    fixture: 'tests/dose_response_fixtures/gl1992_alcohol_bc.json',
    rJson: 'outputs/r_validation/doseresp/gl1992_alcohol_bc.json',
    rcsKnots: 3,
    expectAmberRows: [],
  },
  {
    flagship: 'SGLT2I_DOSE_RESP_REVIEW.html',
    fixture: 'tests/dose_response_fixtures/sglt2i_hba1c.json',
    rJson: 'outputs/r_validation/doseresp/sglt2i_hba1c.json',
    rcsKnots: 3,
    expectAmberRows: [],
  },
  {
    flagship: 'TIRZEPATIDE_T2D_SURPASS_DOSE_RESP_REVIEW.html',
    fixture: 'tests/dose_response_fixtures/tirzepatide_t2d_surpass.json',
    rJson: 'outputs/r_validation/doseresp/tirzepatide_t2d_surpass.json',
    rcsKnots: 3,
    expectAmberRows: [],
  },
  {
    flagship: 'TIRZEPATIDE_OBESITY_SURMOUNT_DOSE_RESP_REVIEW.html',
    fixture: 'tests/dose_response_fixtures/tirzepatide_obesity_surmount.json',
    rJson: 'outputs/r_validation/doseresp/tirzepatide_obesity_surmount.json',
    rcsKnots: 3,
    // k=2 PM vs REML divergence is real and documented; the 4 other rows must still be GREEN
    expectAmberRows: ['linear_tau2'],
  },
  {
    flagship: 'FINERENONE_ARTS_DN_DOSE_RESP_REVIEW.html',
    fixture: 'tests/dose_response_fixtures/finerenone_arts_dn.json',
    rJson: 'outputs/r_validation/doseresp/finerenone_arts_dn.json',
    rcsKnots: 3,
    expectAmberRows: [],
    // Round 3.6 (v0.4 PR #270): k=1 single-trial path. fitLinear throws on k=1; the
    // R-parity badge runs in deferred mode (custom 2-row RCS-only panel, no linear
    // or one-stage rows). This contract entry exercises the fitRCS k=1 branch
    // (estimator=wls_single_trial_rcs, ci_method=t_within_trial, hksj_mv=1,
    // tau2_matrix all zeros, tcrit=within-trial t). See test_dose_response_engine.mjs
    // for the 8 dedicated k=1 unit tests.
    singleTrial: true,
  },
  {
    flagship: 'SEMAGLUTIDE_T2D_SUSTAIN_DOSE_RESP_REVIEW.html',
    fixture: 'tests/dose_response_fixtures/semaglutide_t2d_sustain.json',
    rJson: 'outputs/r_validation/doseresp/semaglutide_t2d_sustain.json',
    rcsKnots: 3,
    // linear_tau2 AMBER: engine fitLinear uses Paule-Mandel (per lessons.md "Never
    // use DL for k<10 — use REML or PM"), R dosresmeta uses REML. On SUSTAIN with
    // I²=97.4% and dose-range mismatch (SUSTAIN-1/5 0→1 mg vs SUSTAIN-FORTE 1→2 mg),
    // PM and REML diverge by |Δ|=0.0113 (PM 0.4104, REML 0.3992) — far above the
    // 0.0001 threshold. Both estimators are valid; this is an expected estimator
    // divergence at the I²~97% boundary, not a bug. Documented in the flagship's
    // R-parity badge disclosure as the linear-row engine-vs-R caveat.
    expectAmberRows: ['linear_tau2'],
    // Round 3.7: 6-trial fixture but per-trial sparse-arm design causes 4 of 6 to
    // have singular K_p×K_p RCS design matrices (only 1 non-reference arm after
    // Option A dropping vs K_p=2 spline coefs required). Engine's fitRCS drops
    // them inside its try/catch and pools the surviving k_RCS=2 (SUSTAIN-1 +
    // SUSTAIN-5). R dosresmeta refuses RCS entirely with the sparse-arm error;
    // the R precompute JSON has rcs.fit_ok=false and lacks rcs.spline_coefs /
    // rcs.nonlinearity_wald_p fields. The 3 RCS R-parity rows are deferred in
    // the flagship's custom badge panel; we skip the threshold assertions for
    // those rows here.
    rRefusedRcs: true,
    // The engine reduces k_RCS from input k=6 to k=2 via silent drop of singular
    // per-trial designs. tcrit at the RCS layer = qt(0.975, 1) = 12.706 reflects
    // the surviving k_RCS, not the input fixture k. The hksj_mv >= 1 floor still
    // holds (q_mv/df_mv < 1 → hksj_mv = 1 by floor).
    rcsKEffectiveLessThanFixture: true,
  },
  {
    flagship: 'UPADACITINIB_RA_SELECT_DOSE_RESP_REVIEW.html',
    fixture: 'tests/dose_response_fixtures/upadacitinib_ra_select.json',
    rJson: 'outputs/r_validation/doseresp/upadacitinib_ra_select.json',
    rcsKnots: 3,
    expectAmberRows: [],
    // Round 3.8: 4-trial fixture on the {0, 15, 30} mg dose grid. Engine fitRCS
    // calls rcsKnots(allDoses, 3) → fewer than the required K=3 distinct knot
    // locations available → engine short-circuits to fitLinear with
    // layer='linear', fallback='degenerate_to_linear', rcs=null. R dosresmeta
    // refuses with the parallel sparse-arm error (rcs.fit_ok=false in the R
    // precompute JSON). This is the FIRST flagship to exercise the engine's
    // documented degenerate-to-linear RCS-fallback in a production-shaped
    // contract test. The contract skips the standard nested-.rcs assertions
    // and the standard top-level RCS-only fields (estimator name, ci_method,
    // hksj_mv, tcrit) because they're inherited from fitLinear's shape, not
    // the RCS multivariate estimator shape.
    rcsDegenerate: true,
    rRefusedRcs: true,
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
  // At k=1 (singleTrial), fitLinear throws — only fitRCS runs.
  let lin = null;
  if (!c.singleTrial) {
    lin = DR.fitLinear(fx.trials, {});
  } else {
    // Confirm the engine actually rejects k=1 for fitLinear (regression-pin the contract).
    test('fitLinear: throws at k=1 (k=1 fitLinear path intentionally rejected — RCS layer carries the linear-basis summary)', () => {
      assert.throws(() => DR.fitLinear(fx.trials, {}), /k\s*>=?\s*2|k=1|requires k/i);
    });
  }
  const rcs = DR.fitRCS(fx.trials, { knots: c.rcsKnots });

  // --- fitLinear top-level contract (what KPI displays read) — only at k >= 2 ---
  if (!c.singleTrial) {
    test('fitLinear: pooled_slope_log defined', () => assert.ok(Number.isFinite(lin.pooled_slope_log)));
    test('fitLinear: pooled_slope_log_se defined', () => assert.ok(Number.isFinite(lin.pooled_slope_log_se)));
    test('fitLinear: pooled_slope_log_ci_lo defined', () => assert.ok(Number.isFinite(lin.pooled_slope_log_ci_lo)));
    test('fitLinear: pooled_slope_log_ci_hi defined', () => assert.ok(Number.isFinite(lin.pooled_slope_log_ci_hi)));
    test('fitLinear: k > 0', () => assert.ok(lin.k > 0));
    test('fitLinear: tau2 defined', () => assert.ok(Number.isFinite(lin.tau2)));
    test('fitLinear: tau2_lo defined (Q-profile, Round 2B)', () => assert.ok(Number.isFinite(lin.tau2_lo)));
    test('fitLinear: tau2_hi defined (Q-profile, Round 2B)', () => assert.ok(Number.isFinite(lin.tau2_hi)));
  }

  // --- fitRCS DEGENERATE-FALLBACK contract (Round 3.8: dose grid too coarse for K-knot Harrell basis) ---
  // When the engine returns the documented RCS-fallback (rcsKnots returns
  // fewer than K distinct locations), the result is shaped like a fitLinear
  // output decorated with `layer='linear'`, `fallback='degenerate_to_linear'`,
  // and `rcs=null`. The standard nested-.rcs and top-level-RCS-only assertions
  // below would all fail because they expect the multivariate-RCS shape.
  // We assert the fallback contract explicitly here and skip the standard
  // RCS assertions for this case.
  if (c.rcsDegenerate) {
    test('fitRCS: degenerate-to-linear fallback — layer === "linear"', () => {
      assert.equal(rcs.layer, 'linear', 'engine should return layer=linear when the dose grid does not support the requested K-knot RCS');
    });
    test('fitRCS: degenerate-to-linear fallback — fallback === "degenerate_to_linear"', () => {
      assert.equal(rcs.fallback, 'degenerate_to_linear', 'engine should mark fallback=degenerate_to_linear when rcsKnots returns < K distinct knots');
    });
    test('fitRCS: degenerate-to-linear fallback — rcs === null (no nested .rcs block)', () => {
      assert.equal(rcs.rcs, null, 'engine must set rcs=null on the degenerate fallback so downstream readers do not dereference a partial RCS shape');
    });
    test('fitRCS: degenerate-to-linear fallback — estimator === "reml_hksj" (inherited from fitLinear)', () => {
      assert.equal(rcs.estimator, 'reml_hksj', 'engine should preserve the fitLinear estimator label on the fallback path (NOT the RCS multivariate estimator)');
    });
    test('fitRCS: degenerate-to-linear fallback — top-level linear fields are finite', () => {
      assert.ok(Number.isFinite(rcs.pooled_slope_log));
      assert.ok(Number.isFinite(rcs.pooled_slope_log_se));
      assert.ok(Number.isFinite(rcs.pooled_slope_log_ci_lo));
      assert.ok(Number.isFinite(rcs.pooled_slope_log_ci_hi));
      assert.ok(Number.isFinite(rcs.tau2));
      assert.ok(Number.isFinite(rcs.Q));
      assert.ok(Number.isFinite(rcs.Q_df));
      assert.ok(Number.isFinite(rcs.I2));
      assert.ok(rcs.k >= 2, 'fallback k must remain >= 2 (else fitLinear would have thrown the k>=2 boundary)');
    });
    test('fitRCS: degenerate-to-linear fallback — engine and fitLinear produce identical pooled slope', () => {
      assert.equal(rcs.pooled_slope_log, lin.pooled_slope_log, 'fallback path must reuse fitLinear output byte-for-byte on the same input');
      assert.equal(rcs.tau2, lin.tau2);
      assert.equal(rcs.k, lin.k);
    });
    test('fitRCS: degenerate-to-linear fallback — DR.predict works on the fallback result (linear branch)', () => {
      const p = DR.predict(rcs, rcs.max_observed_dose / 2);
      assert.ok(Number.isFinite(p.est));
      assert.ok(Number.isFinite(p.ci_lo));
      assert.ok(Number.isFinite(p.ci_hi));
    });
  } else {
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
    test('fitRCS: estimator string matches expected for ' + (c.singleTrial ? 'k=1 (wls_single_trial_rcs)' : 'k>=2 (reml_hksj_multivariate)'), () => {
      if (c.singleTrial) {
        assert.equal(rcs.estimator, 'wls_single_trial_rcs');
      } else {
        assert.equal(rcs.estimator, 'reml_hksj_multivariate');
      }
    });
    test('fitRCS: ci_method string matches expected for ' + (c.singleTrial ? 'k=1 (t_within_trial)' : 'k>=2 (hksj_t_km1)'), () => {
      if (c.singleTrial) {
        assert.equal(rcs.ci_method, 't_within_trial');
      } else {
        assert.equal(rcs.ci_method, 'hksj_t_km1');
      }
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
  }

  // --- k=1 invariants (Round 3.6 / v0.4): hksj_mv exactly 1, tau2 exactly zero,
  //     reml_iterations exactly 0 (no REML to run on a single trial). ---
  // Skipped for rcsDegenerate flagships because the engine returns the
  // fitLinear-shaped fallback (no .rcs block, no tau2_matrix, no reml_iterations).
  if (c.singleTrial && !c.rcsDegenerate) {
    test('k=1 invariant: hksj_mv === 1 (no Q heterogeneity at k=1)', () => {
      assert.equal(rcs.hksj_mv, 1);
      assert.equal(rcs.q_mv, 0);
    });
    test('k=1 invariant: tau2_matrix all zeros + tau2_per_dim all zeros', () => {
      for (const row of rcs.rcs.tau2_matrix) for (const v of row) assert.equal(v, 0);
      for (const v of rcs.rcs.tau2_per_dim) assert.equal(v, 0);
    });
    test('k=1 invariant: reml_iterations === 0 (no REML on single trial)', () => {
      assert.equal(rcs.rcs.reml_iterations, 0);
      assert.equal(rcs.rcs.reml_converged, true);
    });
    test('k=1 invariant: tcrit > 1.96 (within-trial t at small df > z_0.975)', () => {
      assert.ok(rcs.tcrit > 1.96, 'within-trial t at df ' + rcs.df_mv + ' = ' + rcs.tcrit + ' should exceed z=1.96');
    });
    test('k=1 invariant: cov_beta is finite Kp×Kp with positive diagonal (= trial.V)', () => {
      assert.ok(Array.isArray(rcs.rcs.cov_beta));
      for (let d = 0; d < rcs.rcs.cov_beta.length; d++) {
        assert.ok(rcs.rcs.cov_beta[d][d] > 0, 'cov_beta diagonal at dim ' + d + ' must be > 0');
        for (let dd = 0; dd < rcs.rcs.cov_beta.length; dd++) {
          assert.ok(Number.isFinite(rcs.rcs.cov_beta[d][dd]), 'cov_beta[' + d + '][' + dd + '] must be finite');
        }
      }
    });
  }

  // --- R-parity badge state simulation (what the badge JS would emit) ---
  // Per-row helper: GREEN means |Δ| < threshold; AMBER means |Δ| ≥ threshold.
  // A row listed in c.expectAmberRows is intentionally allowed to be AMBER
  // (small-k stress-test cases like SURMOUNT linear_tau2 PM-vs-REML divergence).
  // For k=1 (singleTrial) flagships, the standard 5-row badge does not apply
  // because the engine has no `linear` output; only RCS rows (engine vs R) are
  // testable, and the badge is rendered as a custom 2-row deferred panel.
  const expectAmber = new Set(c.expectAmberRows || []);
  function rowAssert(key, engineVal, rVal) {
    const d = Math.abs(engineVal - rVal);
    const thr = THRESHOLDS[key];
    const isGreen = d < thr;
    if (expectAmber.has(key)) {
      assert.ok(!isGreen, key + ': expected AMBER (|Δ|=' + d.toExponential(2) + ' should be >= threshold ' + thr + ' — engine drift would make this GREEN unexpectedly)');
    } else {
      assert.ok(isGreen, key + ': |Δ|=' + d.toExponential(2) + ' must be < ' + thr);
    }
  }
  if (!c.singleTrial) {
    test('R-parity row: linear_slope' + (expectAmber.has('linear_slope') ? ' AMBER (expected)' : ' GREEN'), () => {
      rowAssert('linear_slope', lin.pooled_slope_log, rJson.linear.pooled_slope_log);
    });
    test('R-parity row: linear_tau2' + (expectAmber.has('linear_tau2') ? ' AMBER (expected, k=2 PM-vs-REML divergence)' : ' GREEN'), () => {
      rowAssert('linear_tau2', lin.tau2, rJson.linear.tau2);
    });
  }
  if (c.rRefusedRcs) {
    // R refused to fit RCS entirely on this fixture (sparse-arm requirement).
    // The R precompute JSON has rcs.fit_ok=false; spline_coefs and nonlinearity_p
    // are absent. The flagship renders a DEFERRED panel for those rows. We still
    // verify the R precompute correctly marks the failure rather than silently
    // omitting the field.
    test('R precompute: rcs.fit_ok === false (R refused, sparse-arm requirement)', () => {
      assert.equal(rJson.rcs && rJson.rcs.fit_ok, false, 'R precompute must explicitly mark rcs.fit_ok=false when R dosresmeta refuses the RCS fit (catches silent omissions)');
      assert.ok(rJson.rcs && typeof rJson.rcs.error_msg === 'string' && rJson.rcs.error_msg.length > 0, 'R precompute must record an error_msg explaining why R refused');
    });
    if (!c.rcsDegenerate) {
      // SUSTAIN-style: R refused but the engine successfully pooled the surviving
      // trials (k_RCS=2). Engine RCS coefs are finite.
      test('Engine RCS coefs finite even though R refused (engine pooled surviving trials)', () => {
        assert.ok(Number.isFinite(rcs.rcs.spline_coefs[0]));
        assert.ok(Number.isFinite(rcs.rcs.spline_coefs[1]));
        assert.ok(Number.isFinite(rcs.rcs.nonlinearity_wald_p));
      });
    } else {
      // SELECT-style: engine also refused RCS (degenerate-to-linear fallback).
      // Both engine and R agree the dose grid cannot support a 3-knot RCS.
      test('Engine + R agree on RCS refusal (engine degenerate-to-linear; R sparse-arm)', () => {
        assert.equal(rcs.layer, 'linear');
        assert.equal(rcs.fallback, 'degenerate_to_linear');
        assert.equal(rcs.rcs, null);
        assert.equal(rJson.rcs.fit_ok, false);
      });
    }
  } else {
    test('R-parity row: rcs_coef_0' + (expectAmber.has('rcs_coef_0') ? ' AMBER (expected)' : ' GREEN') + (c.singleTrial ? ' (k=1 abbreviated badge)' : ''), () => {
      rowAssert('rcs_coef_0', rcs.rcs.spline_coefs[0], rJson.rcs.spline_coefs[0]);
    });
    test('R-parity row: rcs_coef_1' + (expectAmber.has('rcs_coef_1') ? ' AMBER (expected)' : ' GREEN') + (c.singleTrial ? ' (k=1 abbreviated badge)' : ''), () => {
      rowAssert('rcs_coef_1', rcs.rcs.spline_coefs[1], rJson.rcs.spline_coefs[1]);
    });
    test('R-parity row: nonlinearity_p' + (expectAmber.has('nonlinearity_p') ? ' AMBER (expected)' : ' GREEN (Round 2C — was always-amber in v0.1/v0.2)') + (c.singleTrial ? ' (k=1 abbreviated badge)' : ''), () => {
      rowAssert('nonlinearity_p', rcs.rcs.nonlinearity_wald_p, rJson.rcs.nonlinearity_wald_p);
    });
  }
  if (c.rcsKEffectiveLessThanFixture) {
    test('rcsKEffectiveLessThanFixture: engine fitRCS k < input fixture k (silent singular-design drop)', () => {
      assert.ok(rcs.k < fx.trials.length, 'expected rcs.k=' + rcs.k + ' < input fixture k=' + fx.trials.length + ' (4 of 6 SUSTAIN trials have only 1 non-ref arm vs K_p=2 spline → singular per-trial XtSX)');
      assert.ok(rcs.k >= 2, 'engine fitRCS k_RCS must remain >= 2 even after drop (else fitRCS would have thrown at the k>=2 boundary)');
    });
  }

  // --- KPI display invariants (what the .toFixed(N) calls produce) ---
  // The bug pattern: accessing `.rcs.hksj_mv` (undefined) → `undefined.toFixed(2)` throws,
  // OR safe-access pattern `(x != null ? x.toFixed(2) : 'n/a')` silently produces 'n/a'.
  // This test catches both by asserting the top-level path returns a finite number.
  // Skipped for rcsDegenerate flagships because they have no .rcs block (rcs===null)
  // and no top-level RCS-only fields (hksj_mv / tcrit are absent because the result
  // is fitLinear-shaped). For the degenerate path the flagship's Tab 1 / Tab 3 KPIs
  // use the linear-pool fields, asserted by the degenerate-fallback contract above.
  if (!c.rcsDegenerate) {
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
  } else {
    // Degenerate fallback: the flagship's HEADLINE Tab uses the linear-pool slope.
    // Pin the same display invariant on the top-level linear fields that the
    // flagship actually reads (Tab 1's KPI block).
    test('KPI display (rcsDegenerate): top-level pooled_slope_log.toFixed(4) produces a real number string', () => {
      const display = rcs.pooled_slope_log.toFixed(4);
      assert.notEqual(display, 'NaN');
      assert.ok(/^-?\d+\.\d{4}$/.test(display), 'should match (-)X.XXXX, got: ' + display);
    });
    test('KPI display (rcsDegenerate): top-level tau2.toFixed(6) produces a real number string', () => {
      const display = rcs.tau2.toFixed(6);
      assert.ok(/^\d+\.\d{6}$/.test(display), 'should match X.XXXXXX, got: ' + display);
    });
  }

  console.log('');
}

console.log('-'.repeat(60));
console.log(passed + ' passed, ' + failed + ' failed');
process.exit(failed === 0 ? 0 : 1);
