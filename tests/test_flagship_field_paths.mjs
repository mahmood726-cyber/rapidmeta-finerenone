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

// The 9 dose-response flagships shipped via Rounds 1B-3.10:
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
//   8. BRODALUMAB_PSORIASIS_AMAGINE_DOSE_RESP_REVIEW.html (brodalumab_psoriasis_amagine —
//      Round 3.9; 3-trial binary PASI 75 fixture on the {0, 140, 210} mg dose grid.
//      Engine returns the documented RCS-fallback (layer='linear',
//      fallback='degenerate_to_linear', rcs=null) because only 2 distinct positive doses
//      (140, 210) exist across the pool — fewer than the K=3 required Harrell-knot
//      locations. UNLIKE SUSTAIN/SELECT, R dosresmeta DOES fit RCS on this fixture
//      because each trial has 2 non-reference arms (R's sparse-per-trial-arm guard
//      does not fire). R places all 3 percentile knots inside the 140–210 mg interval
//      (knots [157.5, 175, 192.5], spline_coefs [0.01763, -0.01875]); R rcs.fit_ok=true
//      with nonlinearity_wald_p ≈ 1.64e-13. This is the FIRST flagship where engine
//      DECLINES and R FITS — a new contract combination (rcsDegenerate: true +
//      rRefusedRcs: false + new rEngineDisagreesOnRcs: true assertion on R rcs.fit_ok===true).
//      Linear pool succeeds k=3 and matches R within thresholds.)
//   9. ERENUMAB_MIGRAINE_PHASE3_DOSE_RESP_REVIEW.html (erenumab_migraine_phase3 —
//      Round 3.10; 3-trial Δ MMD continuous fixture on the {0, 70, 140} mg dose
//      grid with sparse per-trial coverage (STRIVE 0/70/140, ARISE 0/70 only,
//      LIBERTY 0/140 only). Engine returns the documented RCS-fallback
//      (layer='linear', fallback='degenerate_to_linear', rcs=null) because only
//      2 distinct positive doses exist across the pool — fewer than the K=3
//      required Harrell-knot locations. R dosresmeta refuses with the parallel
//      sparse-arm error (ARISE/LIBERTY each have 1 non-reference arm vs K_p=2
//      required). SAME contract pattern as SELECT (Round 3.8): rcsDegenerate +
//      rRefusedRcs, distinct from AMAGINE (Round 3.9) where engine declined but
//      R fit RCS. Linear pool succeeds k=3 with τ² ≈ 0 (Q=0.34 < df=2 means
//      HKSJ floor activates at 1.0); engine slope -0.01313 vs R slope -0.01312,
//      |Δ| ≈ 1e-5 — far inside threshold.)
//  10. ANIFROLUMAB_SLE_PHASE23_DOSE_RESP_REVIEW.html (anifrolumab_sle_phase23 —
//      Round 3.11; 3-trial BICLA Week 52 binary fixture on the {0, 150, 300, 1000} mg
//      dose grid with sparse per-trial coverage (MUSE 0/300/1000, TULIP-1 0/150/300,
//      TULIP-2 0/300 only). The pool has 3 distinct POSITIVE doses (150, 300, 1000) —
//      sufficient for the 3-knot Harrell basis. The engine produces a REAL 3-knot
//      RCS fit at k_RCS=2 (TULIP-2 silently dropped for singular per-trial design;
//      MUSE and TULIP-1 surviving). Engine knots [225, 300, 650] mg span the actual
//      active-dose range with meaningful gaps (NOT collapsed inside a tiny interval
//      like AMAGINE's R fit). R dosresmeta refuses with the parallel sparse-per-
//      trial-arm error (TULIP-2 has only 1 non-reference arm vs K_p=2 required);
//      the R precompute records rcs.fit_ok=false. NEW contract combination
//      (rRefusedRcs: true + engineFitsRcsRRefuses: true) — the OPPOSITE of AMAGINE
//      (Round 3.9, rcsDegenerate + rEngineDisagreesOnRcs: engine refused / R fit
//      with degenerate knots). This is the FIRST flagship since SUSTAIN where the
//      engine produces a real RCS fit and the FIRST EVER where engine fits with
//      informative knots while R refuses. The engineFitsRcsRRefuses flag asserts
//      the engine knots are NOT degenerate (every knot strictly between the min
//      and max positive dose with no two knots collinear). rcsKEffectiveLessThanFixture
//      also fires (engine k_RCS=2 < input k=3 due to TULIP-2 silent drop). Linear
//      pool succeeds k=3 with engine slope 0.00077 vs R slope 0.00081 (|Δ|≈4e-5,
//      far inside the 0.01 threshold) and engine τ²=3.90e-7 vs R τ²=3.67e-7
//      (|Δ|≈2e-8, far inside the 0.0001 threshold) — both linear rows GREEN.)
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
  {
    flagship: 'BRODALUMAB_PSORIASIS_AMAGINE_DOSE_RESP_REVIEW.html',
    fixture: 'tests/dose_response_fixtures/brodalumab_psoriasis_amagine.json',
    rJson: 'outputs/r_validation/doseresp/brodalumab_psoriasis_amagine.json',
    rcsKnots: 3,
    expectAmberRows: [],
    // Round 3.9: 3-trial binary PASI 75 fixture on the {0, 140, 210} mg dose grid.
    // Engine fitRCS sees only 2 distinct POSITIVE doses (140, 210) — rcsKnots
    // returns < K=3 distinct knot locations → engine short-circuits to
    // fitLinear with layer='linear', fallback='degenerate_to_linear', rcs=null
    // (same engine-side behavior as SELECT in Round 3.8). The standard nested-.rcs
    // assertions and the standard top-level RCS-only fields are SKIPPED via the
    // rcsDegenerate flag.
    rcsDegenerate: true,
    // Round 3.9 is the FIRST flagship where engine declines and R FITS RCS.
    // R's sparse-per-trial-arm guard does not fire (each AMAGINE trial has 2
    // non-reference arms after Option A → 2 >= K_p=2 required). R proceeds to
    // fit a 3-knot RCS with percentile knots all jammed inside the 140–210 mg
    // interval (knots [157.5, 175, 192.5]). The R precompute JSON therefore has
    // rcs.fit_ok = TRUE with spline_coefs and nonlinearity_wald_p populated —
    // the OPPOSITE of SUSTAIN/SELECT where rcs.fit_ok = false. We explicitly
    // do NOT set rRefusedRcs here; instead we add a dedicated
    // rEngineDisagreesOnRcs flag that asserts r.rcs.fit_ok === true plus
    // the knot-degeneracy invariant (all knots inside the [min_pos, max_pos]
    // range of the original dose grid — i.e. knots fit on percentile placeholders,
    // not on real interior dose levels).
    rEngineDisagreesOnRcs: true,
  },
  {
    flagship: 'ERENUMAB_MIGRAINE_PHASE3_DOSE_RESP_REVIEW.html',
    fixture: 'tests/dose_response_fixtures/erenumab_migraine_phase3.json',
    rJson: 'outputs/r_validation/doseresp/erenumab_migraine_phase3.json',
    rcsKnots: 3,
    expectAmberRows: [],
    // Round 3.10: 3-trial Δ MMD continuous fixture on the {0, 70, 140} mg dose
    // grid with sparse per-trial coverage. STRIVE alone has both 70 mg and
    // 140 mg arms; ARISE has only 70 mg, LIBERTY has only 140 mg. The pool has
    // only 2 distinct POSITIVE doses (70, 140). Engine fitRCS calls
    // rcsKnots(allDoses, 3) → fewer than the required K=3 distinct knot
    // locations → engine short-circuits to fitLinear with
    // layer='linear', fallback='degenerate_to_linear', rcs=null.
    // R dosresmeta refuses with the parallel sparse-arm error (ARISE/LIBERTY
    // each have only 1 non-reference arm vs K_p=2 required); the R precompute
    // JSON has rcs.fit_ok=false. SAME contract pattern as SELECT (Round 3.8):
    // both rcsDegenerate (engine refused) and rRefusedRcs (R refused) flags.
    // Distinct from AMAGINE (Round 3.9) which used rcsDegenerate +
    // rEngineDisagreesOnRcs (engine refused but R fit RCS). This is the
    // SECOND flagship to exercise the SELECT-pattern combination
    // (rcsDegenerate + rRefusedRcs) — engine and R agree to refuse.
    rcsDegenerate: true,
    rRefusedRcs: true,
  },
  {
    flagship: 'ANIFROLUMAB_SLE_PHASE23_DOSE_RESP_REVIEW.html',
    fixture: 'tests/dose_response_fixtures/anifrolumab_sle_phase23.json',
    rJson: 'outputs/r_validation/doseresp/anifrolumab_sle_phase23.json',
    rcsKnots: 3,
    expectAmberRows: [],
    // Round 3.11: 3-trial BICLA Wk 52 binary fixture on the {0, 150, 300, 1000} mg
    // dose grid with sparse per-trial coverage (MUSE 0/300/1000, TULIP-1 0/150/300,
    // TULIP-2 0/300 only). UNLIKE the prior 4 degeneracy flagships, the pool has
    // 3 distinct POSITIVE doses {150, 300, 1000} — sufficient for the 3-knot
    // Harrell basis. Engine fitRCS PROCEEDS (does NOT short-circuit to
    // degenerate-to-linear): rcsKnots(allDoses, 3) returns 3 distinct knot
    // locations [225, 300, 650] mg. The per-trial 2×2 spline-coef regression
    // succeeds for MUSE and TULIP-1 (both have 2 non-reference arms ≥ K_p=2);
    // TULIP-2's per-trial XtSX is singular (only 1 non-reference arm), so the
    // engine silently drops TULIP-2 and pools k_RCS=2 (rcsKEffectiveLessThanFixture
    // fires). Full multivariate REML converges in ~32 iterations, HKSJ-mv floor
    // activates at 1.0, tcrit=12.706 at df=1.
    //
    // R dosresmeta refuses the ENTIRE RCS pool with the sparse-per-trial-arm
    // error (TULIP-2 fails the K_p=2 requirement). The R precompute JSON has
    // rcs.fit_ok=false; spline_coefs and nonlinearity_wald_p are absent.
    //
    // NEW contract combination (rRefusedRcs + engineFitsRcsRRefuses) — the
    // OPPOSITE of AMAGINE Round 3.9 (rcsDegenerate + rEngineDisagreesOnRcs).
    // SUSTAIN Round 3.7 had the same combination (rRefusedRcs + engine
    // pooled surviving) but with k_RCS=2 dropping 4 of 6 trials; here only
    // 1 of 3 trials is dropped. The engineFitsRcsRRefuses flag asserts the
    // KNOT-INFORMATIVENESS invariant: not all knots collapsed inside a small
    // interval (the AMAGINE failure mode), but distributed across the actual
    // dose range. We verify this by asserting that the spread of engine knots
    // (max-min) exceeds the min-knot-spacing of the program-wide unique
    // positive-dose set — a structural check that the engine's percentile
    // placement actually used real dose levels.
    rRefusedRcs: true,
    engineFitsRcsRRefuses: true,
    // Engine drops TULIP-2 (only 1 non-ref arm vs K_p=2) → k_RCS=2 from input k=3.
    rcsKEffectiveLessThanFixture: true,
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
      // SUSTAIN-style / ANIFROLUMAB-style: R refused but the engine successfully
      // pooled the surviving trials (k_RCS=2). Engine RCS coefs are finite.
      test('Engine RCS coefs finite even though R refused (engine pooled surviving trials)', () => {
        assert.ok(Number.isFinite(rcs.rcs.spline_coefs[0]));
        assert.ok(Number.isFinite(rcs.rcs.spline_coefs[1]));
        assert.ok(Number.isFinite(rcs.rcs.nonlinearity_wald_p));
      });
      if (c.engineFitsRcsRRefuses) {
        // Round 3.11 (ANIFROLUMAB): engine FIT a real RCS with INFORMATIVE knots
        // (NOT collapsed inside a tiny dose-grid gap like AMAGINE's R fit). The
        // pool has ≥ 3 distinct positive doses, so rcsKnots returns 3 distinct
        // knot locations spanning the actual dose range. Assert the engine
        // knot-informativeness invariant: every knot strictly inside the
        // (min_positive_dose, max_positive_dose) range AND the knot spread
        // (max-knot − min-knot) must exceed at least one full inter-dose gap
        // of the program's unique positive-dose set (otherwise the knots are
        // degenerate-collapsed like AMAGINE).
        test('engineFitsRcsRRefuses: engine knots are INFORMATIVE (distributed across actual dose range, not collapsed)', () => {
          assert.equal(rcs.layer, 'rcs', 'engine layer must be rcs (full fit), not the degenerate-to-linear fallback');
          assert.equal(rcs.rcs == null, false, 'engine must produce a non-null rcs block when it fits');
          assert.ok(Array.isArray(rcs.rcs.knots) && rcs.rcs.knots.length === 3, 'engine must report 3 RCS knots');

          // Compute the program-wide unique positive-dose set.
          var positiveDoses = [];
          fx.trials.forEach(function (t) {
            t.arms.forEach(function (a) { if (a.dose > 0) positiveDoses.push(a.dose); });
          });
          var uniquePos = Array.from(new Set(positiveDoses)).sort(function (a, b) { return a - b; });
          assert.ok(uniquePos.length >= 3, 'engineFitsRcsRRefuses contract requires >= 3 distinct positive doses across the pool; this fixture has ' + uniquePos.length);
          var minPos = uniquePos[0];
          var maxPos = uniquePos[uniquePos.length - 1];

          // Each knot must be strictly inside (0, maxPos] — knots can be at or
          // below the smallest active dose if that's where the 10th percentile
          // lands; we assert > 0 (reference dose) and <= maxPos (no extrapolation
          // beyond the program's maximum dose).
          rcs.rcs.knots.forEach(function (k, i) {
            assert.ok(k > 0, 'engine knot[' + i + '] = ' + k + ' must be > 0 (reference dose excluded from knot percentile basis)');
            assert.ok(k <= maxPos, 'engine knot[' + i + '] = ' + k + ' must be <= max positive dose ' + maxPos);
          });

          // Knot spread > min inter-dose gap — catches the AMAGINE failure mode
          // (all 3 knots collapsed inside one 70 mg gap). Compute the smallest
          // gap between consecutive UNIQUE positive doses; the knot spread
          // (max_knot − min_knot) must be at least one such gap.
          var minInterDoseGap = Infinity;
          for (var i = 1; i < uniquePos.length; i++) {
            var g = uniquePos[i] - uniquePos[i - 1];
            if (g < minInterDoseGap) minInterDoseGap = g;
          }
          var knotSpread = Math.max.apply(null, rcs.rcs.knots) - Math.min.apply(null, rcs.rcs.knots);
          assert.ok(knotSpread >= minInterDoseGap,
            'engine knot spread (' + knotSpread + ') must be >= the smallest inter-dose gap in the pool (' + minInterDoseGap + '); otherwise knots are collapsed inside a single gap like the AMAGINE Round 3.9 failure mode');

          // Distinct positive-dose count must be >= 3 (the engine's cross-trial
          // knot-count check would have short-circuited otherwise; this is the
          // structural condition that lets the engine fit when AMAGINE could not).
          assert.ok(uniquePos.length >= 3,
            'engineFitsRcsRRefuses requires >= 3 distinct positive doses; this fixture has ' + uniquePos.length + ' (the ANIFROLUMAB-vs-AMAGINE distinguishing characteristic)');
        });
      }
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
  } else if (c.rEngineDisagreesOnRcs) {
    // Round 3.9 (AMAGINE brodalumab): engine DECLINED via degenerate-to-linear
    // fallback, but R DID fit RCS — the new flagship-shape combination. Assert:
    //  (1) engine returned the degenerate-to-linear fallback (rcs.layer='linear',
    //      rcs.fallback='degenerate_to_linear', rcs.rcs=null);
    //  (2) R rcs.fit_ok === true (the OPPOSITE of the rRefusedRcs case);
    //  (3) R reports spline_coefs and a nonlinearity_wald_p that are FINITE NUMBERS;
    //  (4) the knot-degeneracy invariant: every R knot location lies STRICTLY
    //      inside (min_positive_dose, max_positive_dose) — i.e. all knots are on
    //      percentile placeholders inside the 140–210 mg gap, not on real dose
    //      observations. This is what distinguishes the AMAGINE case from a
    //      "real" RCS fit where knots would land on or near the 10th / 50th /
    //      90th percentiles of the unique dose vector.
    test('R precompute: rcs.fit_ok === true (R fit RCS even though engine declined)', () => {
      assert.equal(rJson.rcs && rJson.rcs.fit_ok, true,
        'R precompute must mark rcs.fit_ok=true when R dosresmeta proceeds to fit RCS — this is the Round 3.9 distinguishing characteristic vs SUSTAIN/SELECT (both rRefusedRcs)');
      assert.ok(Array.isArray(rJson.rcs.spline_coefs) && rJson.rcs.spline_coefs.length >= 2,
        'R precompute must record spline_coefs[] with length >= 2 when fit_ok=true');
      assert.ok(Number.isFinite(rJson.rcs.spline_coefs[0]) && Number.isFinite(rJson.rcs.spline_coefs[1]),
        'R precompute spline_coefs[0] and spline_coefs[1] must be finite numbers');
      assert.ok(Number.isFinite(rJson.rcs.nonlinearity_wald_p),
        'R precompute must record a finite nonlinearity_wald_p when fit_ok=true');
    });
    test('Engine + R DISAGREE on RCS — engine degenerate-to-linear, R fit with knots inside dose-grid gap', () => {
      assert.equal(rcs.layer, 'linear');
      assert.equal(rcs.fallback, 'degenerate_to_linear');
      assert.equal(rcs.rcs, null);
      assert.equal(rJson.rcs.fit_ok, true, 'R must report fit_ok=true on this AMAGINE-style fixture');
      // Knot-degeneracy invariant: compute the positive-dose range from the
      // fixture's per-arm dose values and assert every R knot is strictly inside.
      const positiveDoses = [];
      fx.trials.forEach(t => t.arms.forEach(a => { if (a.dose > 0) positiveDoses.push(a.dose); }));
      const minPos = Math.min(...positiveDoses);
      const maxPos = Math.max(...positiveDoses);
      assert.ok(Array.isArray(rJson.rcs.knots) && rJson.rcs.knots.length === 3,
        'R must report 3 RCS knots');
      rJson.rcs.knots.forEach((k, i) => {
        assert.ok(k > minPos && k < maxPos,
          'R knot[' + i + '] = ' + k + ' must lie strictly INSIDE (min_pos=' + minPos + ', max_pos=' + maxPos + '); the knot-degeneracy invariant — R fit knots inside a gap where there are no interior data points');
      });
      // Sanity: distinct positive doses must be < 3 (the cross-trial constraint
      // the engine actually checks). Without this, the engine would have proceeded.
      const distinctPos = new Set(positiveDoses);
      assert.ok(distinctPos.size < 3,
        'Engine declined because distinct positive doses (' + distinctPos.size + ') < K=3; the test fixture must satisfy this invariant for the engine-declined branch to fire');
    });
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

// === v0.5.0 SURPASS LOO-tab contract (engine v0.5 demonstrator) ===
// The SURPASS flagship reads DR._internal.fitLOO from the loaded engine and
// renders a 5-tab page with the LOO sensitivity tab in slot 3.  These
// assertions pin the engine-vs-flagship contract for the new tab so a
// future engine refactor that renames or moves fitLOO breaks the test
// (matching the pattern of the Round 2C field-path regression).
console.log('SURPASS LOO-tab contract (engine v0.5.0 — DR._internal.fitLOO)');

test('engine v0.5: DR.engine_version label is @0.5.0', () => {
  assert.ok(/@0\.5\.0$/.test(DR.engine_version),
    'engine_version label should end with @0.5.0; got ' + DR.engine_version);
});

test('engine v0.5: DR._internal.fitLOO is a function', () => {
  assert.equal(typeof DR._internal.fitLOO, 'function',
    'DR._internal.fitLOO must be a function on the engine v0.5.0 API');
});

test('SURPASS LOO: fitLOO(SURPASS, layer=rcs, knots=3) returns full_pool + 5 LOO entries', () => {
  const fx = JSON.parse(fs.readFileSync(path.join(repoRoot, 'tests/dose_response_fixtures/tirzepatide_t2d_surpass.json'), 'utf8'));
  const r = DR._internal.fitLOO(fx.trials, { layer: 'rcs', knots: 3 });
  assert.equal(r.layer, 'rcs');
  assert.equal(r.k_full, 5);
  assert.equal(r.loo.length, 5);
  assert.equal(r.full_pool.layer, 'rcs');
  assert.ok(Number.isFinite(r.full_pool.rcs.nonlinearity_wald_p),
    'full_pool.rcs.nonlinearity_wald_p must be finite (the SURPASS headline finding the LOO tab supports)');
});

test('SURPASS LOO-tab KPI fields populate without "n/a" — most_influential_trial, max_abs_delta_slope, full nlP', () => {
  const fx = JSON.parse(fs.readFileSync(path.join(repoRoot, 'tests/dose_response_fixtures/tirzepatide_t2d_surpass.json'), 'utf8'));
  const r = DR._internal.fitLOO(fx.trials, { layer: 'rcs', knots: 3 });
  // KPI bar reads: full-pool nlP, most_influential_trial, max_abs_delta_slope.
  // Each must produce a non-empty display string.
  const fullNlP = r.full_pool.rcs.nonlinearity_wald_p;
  assert.ok(Number.isFinite(fullNlP), 'full-pool nlP must be finite');
  assert.ok(/^\d+\.\d{4}$/.test(fullNlP.toFixed(4)), 'fullNlP.toFixed(4) display: ' + fullNlP.toFixed(4));

  assert.ok(r.summary.most_influential_trial,
    'summary.most_influential_trial must be set (non-null/empty) so the KPI does not display "n/a"');
  assert.equal(typeof r.summary.most_influential_trial, 'string');

  assert.ok(Number.isFinite(r.summary.max_abs_delta_slope),
    'summary.max_abs_delta_slope must be finite (KPI displays via .toFixed(5))');
  assert.ok(/^\d+\.\d{5}$/.test(r.summary.max_abs_delta_slope.toFixed(5)),
    'max_abs_delta_slope.toFixed(5) display: ' + r.summary.max_abs_delta_slope.toFixed(5));

  // any_significance_flip / any_sign_flip — booleans (KPI displays YES/No).
  assert.equal(typeof r.summary.any_significance_flip, 'boolean');
  assert.equal(typeof r.summary.any_sign_flip, 'boolean');
  assert.equal(typeof r.summary.n_degenerated, 'number');
});

test('SURPASS LOO-tab per-row contract: every LOO entry has all displayed fields finite', () => {
  const fx = JSON.parse(fs.readFileSync(path.join(repoRoot, 'tests/dose_response_fixtures/tirzepatide_t2d_surpass.json'), 'utf8'));
  const r = DR._internal.fitLOO(fx.trials, { layer: 'rcs', knots: 3 });
  // The flagship's LOO table renders one row per entry; each row reads:
  // dropped_studlab, k_loo, pooled_slope_log, pooled_slope_log_ci_lo/hi,
  // nonlinearity_wald_p, delta_slope, sign_flip, significance_flip, degenerated.
  // The on-page render gates each numeric on Number.isFinite, so we only
  // need the engine to populate the right shape (NOT to guarantee every
  // value is finite on a hypothetical future degenerate subset).  But for
  // the canonical SURPASS k=5 fixture, every numeric SHOULD be finite.
  r.loo.forEach(e => {
    assert.ok(typeof e.dropped_studlab === 'string' && e.dropped_studlab.length > 0);
    assert.equal(e.k_loo, 4, 'SURPASS LOO k_loo === 4 for every entry (k_full=5)');
    assert.ok(Number.isFinite(e.pooled_slope_log));
    assert.ok(Number.isFinite(e.pooled_slope_log_se));
    assert.ok(Number.isFinite(e.pooled_slope_log_ci_lo));
    assert.ok(Number.isFinite(e.pooled_slope_log_ci_hi));
    assert.ok(Number.isFinite(e.nonlinearity_wald_p),
      'SURPASS canonical fixture: every LOO subset fits real RCS; nlP must be finite');
    assert.ok(Number.isFinite(e.delta_slope));
    assert.equal(typeof e.sign_flip, 'boolean');
    assert.equal(typeof e.significance_flip, 'boolean');
    assert.equal(typeof e.degenerated, 'boolean');
  });
});

// === v0.5.0 LOO-tab rollout (9 additional flagships) ===
// Each flagship asserts: (a) DOM mount ids the page expects exist in the .html
// source (we read the static HTML and grep for the documented ids), (b) the
// engine's fitLOO call on the fixture returns the documented shape, (c) the
// summary fields the KPI bar reads are populated (no n/a in displayable slots).
// For ARTS-DN (k=1) we assert the EXPLANATORY PANEL contract: HTML mounts
// exist, but DR._internal.fitLOO is NOT called by the flagship; instead the
// flagship renders an explanatory note.
console.log('LOO-tab rollout contract (9 additional flagships)');

function readFlagshipHtml(name) {
  return fs.readFileSync(path.join(repoRoot, name), 'utf8');
}

const looRollout = [
  {
    name: 'ALCOHOL_BC',
    html: 'ALCOHOL_BC_DOSE_RESP_REVIEW.html',
    fixture: 'tests/dose_response_fixtures/gl1992_alcohol_bc.json',
    layer: 'rcs',
    knots: 3,
    mountIds: ['loo-kpis', 'loo-headline', 'loo-table', 'loo-deltabar', 'loo-methods'],
    tabButtonId: 'tab-btn-loo',
    tabPanelId: 'tab-loo',
    expectedKFull: 5,
    expectedKLoo: 4,
    everyNlPFinite: true,
    expectedMostInfluential: 'Howe',  // substring match
  },
  {
    name: 'SGLT2I (HbA1c block)',
    html: 'SGLT2I_DOSE_RESP_REVIEW.html',
    fixture: 'tests/dose_response_fixtures/sglt2i_hba1c.json',
    layer: 'rcs',
    knots: 3,
    mountIds: ['hba1c-loo-kpis', 'hba1c-loo-headline', 'hba1c-loo-table', 'hhf-loo-kpis', 'hhf-loo-headline', 'hhf-loo-table', 'loo-methods'],
    tabButtonId: 'tab-btn-loo',
    tabPanelId: 'tab-loo',
    expectedKFull: 3,
    expectedKLoo: 2,
    everyNlPFinite: true,
    expectedMostInfluential: 'EMPA-REG',
  },
  {
    name: 'SGLT2I (hHF block — secondary)',
    html: 'SGLT2I_DOSE_RESP_REVIEW.html',
    fixture: 'tests/dose_response_fixtures/sglt2i_hhf.json',
    layer: 'linear',
    skipHtmlAssertions: true,  // SGLT2I HTML already asserted above
    expectedKFull: 2,
    expectedKLoo: 1,
    everyNlPFinite: false,  // linear layer at k=2 → all subsets are k=1 single-trial fallback, no RCS, nlP=null
    expectAllDegenerated: true,
    expectedMostInfluential: 'CANVAS',
  },
  {
    name: 'TIRZEPATIDE_OBESITY_SURMOUNT',
    html: 'TIRZEPATIDE_OBESITY_SURMOUNT_DOSE_RESP_REVIEW.html',
    fixture: 'tests/dose_response_fixtures/tirzepatide_obesity_surmount.json',
    layer: 'rcs',
    knots: 3,
    mountIds: ['wt-loo-kpis', 'wt-loo-headline', 'wt-loo-table', 'wt-loo-deltabar', 'wt-loo-methods'],
    tabButtonId: 'tab-btn-wt-loo',
    tabPanelId: 'tab-wt-loo',
    expectedKFull: 2,
    expectedKLoo: 1,
    everyNlPFinite: false,  // some LOO subsets are k=1 with sparse arms → degenerated, nlP=null
    expectedMostInfluential: 'SURMOUNT-2',
  },
  {
    name: 'FINERENONE_ARTS_DN (k=1, explanatory panel)',
    html: 'FINERENONE_ARTS_DN_DOSE_RESP_REVIEW.html',
    explanatoryPanelOnly: true,
    fixture: 'tests/dose_response_fixtures/finerenone_arts_dn.json',
    mountIds: ['loo-kpis', 'loo-headline', 'loo-methods'],
    tabButtonId: 'tab-btn-loo',
    tabPanelId: 'tab-loo',
    expectedKFull: 1,
    expectedExplanatoryPhrase: 'LOO sensitivity not applicable at k=1',
  },
  {
    name: 'SEMAGLUTIDE_T2D_SUSTAIN',
    html: 'SEMAGLUTIDE_T2D_SUSTAIN_DOSE_RESP_REVIEW.html',
    fixture: 'tests/dose_response_fixtures/semaglutide_t2d_sustain.json',
    layer: 'rcs',
    knots: 3,
    mountIds: ['hba1c-loo-kpis', 'hba1c-loo-headline', 'hba1c-loo-table', 'hba1c-loo-deltabar', 'hba1c-loo-methods'],
    tabButtonId: 'tab-btn-hba1c-loo',
    tabPanelId: 'tab-hba1c-loo',
    expectedKFull: 6,
    expectedKLoo: 5,
    everyNlPFinite: false,  // SUSTAIN-FORTE drop → k_RCS degeneration on remaining 5
    expectedMostInfluential: 'SUSTAIN-FORTE',
  },
  {
    name: 'UPADACITINIB_RA_SELECT',
    html: 'UPADACITINIB_RA_SELECT_DOSE_RESP_REVIEW.html',
    fixture: 'tests/dose_response_fixtures/upadacitinib_ra_select.json',
    layer: 'linear',
    mountIds: ['das28-loo-kpis', 'das28-loo-headline', 'das28-loo-table', 'das28-loo-deltabar', 'das28-loo-methods'],
    tabButtonId: 'tab-btn-das28-loo',
    tabPanelId: 'tab-das28-loo',
    expectedKFull: 4,
    expectedKLoo: 3,
    everyNlPFinite: false,  // linear layer; nlP=null for all LOO entries
    expectedMostInfluential: 'SELECT-EARLY',
  },
  {
    name: 'BRODALUMAB_PSORIASIS_AMAGINE',
    html: 'BRODALUMAB_PSORIASIS_AMAGINE_DOSE_RESP_REVIEW.html',
    fixture: 'tests/dose_response_fixtures/brodalumab_psoriasis_amagine.json',
    layer: 'linear',
    mountIds: ['pasi-loo-kpis', 'pasi-loo-headline', 'pasi-loo-table', 'pasi-loo-deltabar', 'pasi-loo-methods'],
    tabButtonId: 'tab-btn-pasi-loo',
    tabPanelId: 'tab-pasi-loo',
    expectedKFull: 3,
    expectedKLoo: 2,
    everyNlPFinite: false,
    expectedMostInfluential: 'AMAGINE-3',
  },
  {
    name: 'ERENUMAB_MIGRAINE_PHASE3',
    html: 'ERENUMAB_MIGRAINE_PHASE3_DOSE_RESP_REVIEW.html',
    fixture: 'tests/dose_response_fixtures/erenumab_migraine_phase3.json',
    layer: 'linear',
    mountIds: ['mmd-loo-kpis', 'mmd-loo-headline', 'mmd-loo-table', 'mmd-loo-deltabar', 'mmd-loo-methods'],
    tabButtonId: 'tab-btn-mmd-loo',
    tabPanelId: 'tab-mmd-loo',
    expectedKFull: 3,
    expectedKLoo: 2,
    everyNlPFinite: false,
    expectedMostInfluential: 'LIBERTY',
  },
  {
    name: 'ANIFROLUMAB_SLE_PHASE23',
    html: 'ANIFROLUMAB_SLE_PHASE23_DOSE_RESP_REVIEW.html',
    fixture: 'tests/dose_response_fixtures/anifrolumab_sle_phase23.json',
    layer: 'rcs',
    knots: 3,
    mountIds: ['bicla-loo-kpis', 'bicla-loo-headline', 'bicla-loo-table', 'bicla-loo-deltabar', 'bicla-loo-methods'],
    tabButtonId: 'tab-btn-bicla-loo',
    tabPanelId: 'tab-bicla-loo',
    expectedKFull: 3,
    expectedKLoo: 2,
    everyNlPFinite: false,  // 2/3 LOO subsets are single-trial RCS path, nlP=null
    expectedMostInfluential: 'TULIP-1',
  },
];

for (const c of looRollout) {
  console.log('LOO rollout: ' + c.name);
  if (!c.skipHtmlAssertions) {
    const html = readFlagshipHtml(c.html);
    test(c.name + ': LOO tab button #' + c.tabButtonId + ' present in HTML', () => {
      assert.ok(html.includes('id="' + c.tabButtonId + '"'),
        'flagship HTML must contain the LOO tab button id ' + c.tabButtonId);
    });
    test(c.name + ': LOO tab panel #' + c.tabPanelId + ' present in HTML', () => {
      assert.ok(html.includes('id="' + c.tabPanelId + '"'),
        'flagship HTML must contain the LOO tab panel id ' + c.tabPanelId);
    });
    c.mountIds.forEach(id => {
      test(c.name + ': mount #' + id + ' present in HTML', () => {
        assert.ok(html.includes('id="' + id + '"'),
          'flagship HTML must contain the LOO mount id ' + id);
      });
    });
  }

  if (c.explanatoryPanelOnly) {
    // ARTS-DN k=1 case: assert the HTML contains the explanatory phrase the
    // flagship JS renders rather than calling fitLOO.
    test(c.name + ': flagship JS contains the documented k=1 explanatory phrase', () => {
      const js = fs.readFileSync(path.join(repoRoot, c.html.replace('.html', '.js')), 'utf8');
      assert.ok(js.includes(c.expectedExplanatoryPhrase),
        'flagship JS must render the documented explanatory phrase: ' + c.expectedExplanatoryPhrase);
      // And the JS must NOT actually invoke DR._internal.fitLOO at k=1.
      // We strip string literals AND // line comments before scanning so that
      // references inside the methodology copy and inline comments
      // ("<code>DR._internal.fitLOO(...)</code>", "// Render an explanatory
      // panel rather than calling DR._internal.fitLOO") do not count as
      // invocations.
      const stripped = js
        .replace(/'(?:\\.|[^'\\])*'/g, "''")     // single-quoted strings
        .replace(/"(?:\\.|[^"\\])*"/g, '""')     // double-quoted strings
        .replace(/`(?:\\.|[^`\\])*`/g, '``')     // template literals
        .replace(/\/\/[^\n]*/g, '')              // // line comments
        .replace(/\/\*[\s\S]*?\*\//g, '');       // /* block comments */
      assert.ok(!/DR\._internal\.fitLOO\s*\(/.test(stripped),
        'flagship JS must NOT invoke DR._internal.fitLOO at k=1 (would return empty); only string-literal and comment references in the explanatory copy are allowed');
    });
    continue;
  }

  // Engine-side contract: fitLOO call must succeed and produce the documented shape.
  const fx = JSON.parse(fs.readFileSync(path.join(repoRoot, c.fixture), 'utf8'));
  let r;
  try {
    r = DR._internal.fitLOO(fx.trials, c.layer === 'rcs' ? { layer: 'rcs', knots: c.knots } : { layer: 'linear' });
  } catch (e) {
    test(c.name + ': fitLOO call should not throw (got: ' + e.message + ')', () => { throw e; });
    continue;
  }

  test(c.name + ': fitLOO returns layer=' + c.layer + ', k_full=' + c.expectedKFull + ', loo.length=' + c.expectedKFull, () => {
    assert.equal(r.layer, c.layer);
    assert.equal(r.k_full, c.expectedKFull);
    assert.equal(r.loo.length, c.expectedKFull);
  });

  test(c.name + ': summary fields populate (most_influential_trial, max_abs_delta_slope, booleans)', () => {
    assert.ok(typeof r.summary.most_influential_trial === 'string' && r.summary.most_influential_trial.length > 0,
      'summary.most_influential_trial must be a non-empty string so KPI does not display n/a');
    assert.ok(Number.isFinite(r.summary.max_abs_delta_slope),
      'summary.max_abs_delta_slope must be finite (KPI displays via .toFixed(5))');
    assert.equal(typeof r.summary.any_significance_flip, 'boolean');
    assert.equal(typeof r.summary.any_sign_flip, 'boolean');
    assert.equal(typeof r.summary.n_degenerated, 'number');
  });

  test(c.name + ': summary.most_influential_trial matches expected (' + c.expectedMostInfluential + ')', () => {
    assert.ok(String(r.summary.most_influential_trial).includes(c.expectedMostInfluential),
      'expected most_influential_trial to include "' + c.expectedMostInfluential + '"; got: ' + r.summary.most_influential_trial);
  });

  test(c.name + ': per-row k_loo === ' + c.expectedKLoo + ' for every entry', () => {
    r.loo.forEach(e => assert.equal(e.k_loo, c.expectedKLoo,
      'expected k_loo=' + c.expectedKLoo + ' for entry dropping ' + e.dropped_studlab + '; got ' + e.k_loo));
  });

  test(c.name + ': per-row shape contract (dropped_studlab, slope, CI, delta, booleans)', () => {
    r.loo.forEach(e => {
      assert.ok(typeof e.dropped_studlab === 'string' && e.dropped_studlab.length > 0);
      assert.equal(typeof e.sign_flip, 'boolean');
      assert.equal(typeof e.significance_flip, 'boolean');
      assert.equal(typeof e.degenerated, 'boolean');
      // pooled_slope_log can be NaN on degenerated subsets (e.g. SURMOUNT-1 LOO).
      // The flagship's row render checks Number.isFinite; we only require the
      // field to be a number (finite OR NaN).
      assert.equal(typeof e.pooled_slope_log, 'number');
    });
  });

  if (c.everyNlPFinite) {
    test(c.name + ': every LOO entry has finite nonlinearity_wald_p (no degenerations on this fixture)', () => {
      r.loo.forEach(e => {
        assert.ok(Number.isFinite(e.nonlinearity_wald_p),
          'expected finite nlP for entry dropping ' + e.dropped_studlab + '; got ' + e.nonlinearity_wald_p);
      });
    });
  }

  if (c.expectAllDegenerated) {
    test(c.name + ': all LOO subsets are degenerated (k_full=2 linear layer → each LOO is k=1)', () => {
      assert.equal(r.summary.n_degenerated, r.loo.length,
        'expected all ' + r.loo.length + ' LOO entries to be degenerated; got ' + r.summary.n_degenerated);
    });
  }

  console.log('');
}

console.log('-'.repeat(60));
console.log(passed + ' passed, ' + failed + ' failed');
process.exit(failed === 0 ? 0 : 1);
