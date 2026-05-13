# Dose-response engine pack

> Browser-native engine + flagship reviews for dose-response meta-analysis.
> Engine `rapidmeta-dose-response-engine-v1.js@v0.3.0` (top-level of this repo).
> Live on `main` as of commit `cfaead54` (CSP fix).

This subdirectory documents the dose-response *engine* and its 4 *flagship* HTML reviews. The engine is one of ~31 inlined analytic engines that ship with the broader RapidMeta Living Evidence Portfolio; the flagship reviews are full-page demonstrations of each engine layer on real datasets.

---

## Quick start

```bash
# Run engine test suite (Node, deterministic)
node tests/test_dose_response_engine.mjs            # 60 / 60

# Run flagship field-path contract test (Node, no browser)
node tests/test_flagship_field_paths.mjs            # 96 / 96 (32 per flagship × 3 flagships)

# Run real-browser smoke (Python, headless Chromium)
python tests/test_flagship_playwright_smoke.py      # 12 / 12 (4 per flagship × 3 flagships)

# Run R-vs-engine parity precompute for one fixture
python scripts/r_validate_doseresp.py --review gl1992_alcohol_bc
```

---

## Engine

### Public surface (engine v0.3.0)

```js
const DR = window.RapidMetaDoseResp;   // also: module.exports under Node

DR.engine_version;                      // 'rapidmeta-dose-response-engine-v1@0.3.0'
DR.validate(trials)                     // → string[] of issues
DR.fitLinear(trials, opts)              // → {pooled_slope_log, …, tau2_lo, tau2_hi (Q-profile), …}
DR.fitRCS(trials, opts)                 // → {pooled_slope_log family, rcs:{…}, hksj_mv, tcrit, …}
DR.fitOneStage(trials, opts, rJson)     // → {estimator:'r_precomputed', …}
DR.nonLinearityTest(rcsResult)          // → {chi2, df, p}  (reads from rcs.nonlinearity_wald_*)
DR.predict(result, dose)                // → {est, ci_lo, ci_hi}
DR.forest(trials, result)               // → forest plot data
DR.exportResults(result)                // → JSON-safe deep clone

DR._internal.nelderMead(f, x0, opts)       // derivative-free optimizer
DR._internal.qProfileCI(yi, vi, alpha)     // Viechtbauer 2007 τ² CI
DR._internal.remlLogLik(perStudy, tau2)    // REML log-likelihood evaluator
DR._internal.logDeterminant(M)             // log|M| via Doolittle LU
DR._internal.pmTau2(yi, vi)                // Paule-Mandel τ² (used by fitLinear)
DR._internal.glCovariance, mdCovariance    // per-trial cov (binary GL / continuous MD)
DR._internal.rcsKnots, rcsBasis            // 3-knot Harrell-default
DR._internal.matInv, matVec, …             // matrix helpers
DR._internal.qchisq, qt, pchisq, pt        // distribution helpers
```

### Return-shape contract (fitRCS)

Two surfaces — **top-level** vs **nested under `.rcs`**. Confusing them is the bug class caught by Round 2C hotfix (PR #250) and now codified in `tests/test_flagship_field_paths.mjs`.

| Top-level (correct access) | Nested under `.rcs` (correct access) |
|---|---|
| `result.hksj_mv` | `result.rcs.nonlinearity_wald_p` |
| `result.tcrit` | `result.rcs.nonlinearity_wald_chi2` |
| `result.q_mv`, `df_mv` | `result.rcs.nonlinearity_wald_df` |
| `result.estimator` ('reml_hksj_multivariate') | `result.rcs.spline_coefs`, `spline_coefs_se` |
| `result.ci_method` ('hksj_t_km1') | `result.rcs.tau2_matrix` (Kp × Kp) |
| `result.converged`, `iterations` | `result.rcs.tau2_per_dim` (diagonal) |
| `result.pooled_slope_log` family | `result.rcs.fit_at_dose` (20-point grid) |
| | `result.rcs.reml_converged`, `reml_iterations`, `reml_loglik` |
| | `result.rcs.cov_beta` |

Writing `result.rcs.hksj_mv` returns `undefined` and the safe-access display pattern `(x != null ? x.toFixed(2) : 'n/a')` silently produces `"HKSJ-mv = n/a"`. The contract test catches it.

### Statistical conventions

| Topic | Decision | Reference |
|---|---|---|
| τ² for fitLinear | Paule-Mandel (PM) | lessons.md "Never use DL for k<10 — use REML or PM" |
| τ² for fitRCS | Full multivariate REML via Nelder-Mead on Cholesky parameters | Round 2B (PR #246) |
| CI for fitLinear | HKSJ floor `max(1, Q/(k−1))`, then z=1.96 | engine v0.2 |
| CI for fitRCS | HKSJ-multivariate `max(1, Q_mv/(n_total − Kp))` × √-inflated SE × `t_{k−1}` | Round 2B Task 9 |
| τ² CI for fitLinear | Q-profile per Viechtbauer 2007 (bisection) | Round 2B Task 5 |
| RCS knot placement | Harrell-default percentile knots on unique non-reference doses | Round 1A |
| Zero-cell continuity | Conditional +0.5 events + 1.0 n on BOTH arms IF any cell is zero (binary only) | engine v0.2 (Round 2A) |
| Continuous covariance | Shared-reference: `Cov(y_i, y_j) = sd_ref²/n_ref` off-diagonal | engine v0.2 (Round 2A) |
| Prediction interval df | `t_{k−1}` per Cochrane Handbook v6.5 | engine v0.1 |

### Engine version history

| Version | Round | Headline change |
|---|---|---|
| v0.1.0 | 1A (binary GL fixture) | Initial engine + GL-1992 alcohol/BC fixture; diagonal-PM τ² approximation for fitRCS |
| v0.2.0 | 2A | Continuous-outcome branch (per-trial cov, conditional zero-cell), SGLT2i HbA1c + hHF fixtures |
| v0.3.0 | 2B | **Full multivariate REML for fitRCS** via Nelder-Mead on Cholesky parameters; HKSJ-multivariate + t_{k−1} CIs; Q-profile τ² CI for fitLinear; F-5 test gap closure; P2-13 IIFE refactor |

The v0.2 → v0.3 lift closed the diagonal-PM divergence to R mixmeta:

| Fixture | engine non-lin p (v0.2) | engine non-lin p (v0.3) | R mixmeta | \|Δ\| |
|---|---|---|---|---|
| GL-1992 alcohol/BC (k=8) | 0.05 | **0.7035** | 0.7069 | 0.0034 |
| SGLT2i HbA1c (k=3) | (not estimable) | **0.2271** | 0.2293 | 0.0022 |
| Tirzepatide SURPASS (k=5) | (not built yet) | **0.0346** | 0.0364 | 0.0018 |

---

## Flagships

3 flagships on `main` as of `cfaead54`:

| Flagship | Fixture | Therapeutic area | k | Outcome | Headline |
|---|---|---|---|---|---|
| `ALCOHOL_BC_DOSE_RESP_REVIEW.html` | `gl1992_alcohol_bc.json` | Alcohol → breast cancer | 8 cohort studies | log-RR | No evidence of non-linearity (p = 0.70, full REML) |
| `SGLT2I_DOSE_RESP_REVIEW.html` | `sglt2i_hba1c.json` + `sglt2i_hhf.json` | T2D CV trials (HbA1c + hHF) | 3 + 2 | MD% / log-RR | Borderline non-linearity (p = 0.23 HbA1c, p = 0.04 hHF binary) |
| `TIRZEPATIDE_T2D_SURPASS_DOSE_RESP_REVIEW.html` | `tirzepatide_t2d_surpass.json` | T2D HbA1c (5 SURPASS RCTs) | 5 | MD HbA1c % | Significant saturation after ~5 mg (p = 0.035) |

A 4th flagship (Round 3.5, `TIRZEPATIDE_OBESITY_SURMOUNT_DOSE_RESP_REVIEW.html`) is in flight as of this writing — k=2 stress test (SURMOUNT-1 + SURMOUNT-2 weight loss).

### Flagship anatomy (post-CSP fix)

Every flagship has:

- `<NAME>.html` — the page skeleton, JSON data blocks, CSS, ARIA tabs, badge mounts
- `<NAME>.js` — the per-page logic (engine boot, fetch calls, KPI renders, badge mount). **External sibling file, never inline.** CSP `script-src 'self'` blocks inline scripts; the per-page logic must live in a `'self'`-loaded file.

This convention was introduced in PR #257 after the Playwright test caught that all 3 flagships had been broken in real browsers since Round 2A (commit `bb2ec9e4`, May 12-13) — every prior verification was Node-side simulation or HTTP-200 smoke; nobody actually opened them in a browser. Don't repeat that.

### Adding a new flagship

1. Build fixture JSON in `tests/dose_response_fixtures/<name>.json` (schema: match an existing fixture; agent-extracted from AACT is safe with the per-arm contract documented in fixture `_comment`).
2. Build abstracts JSON (optional) in `fixtures/dose_response/<name>_abstracts.json`.
3. Run R precompute: `python scripts/r_validate_doseresp.py --review <name>` → writes `outputs/r_validation/doseresp/<name>.json`.
4. Clone an existing flagship pair (`.html` + `.js`) as template; adapt names, JSON paths, copy.
5. Add the new flagship to BOTH test files:
   - `tests/test_flagship_field_paths.mjs` — `flagshipContracts` array
   - `tests/test_flagship_playwright_smoke.py` — `FLAGSHIPS` array
6. Verify: `node tests/test_flagship_field_paths.mjs` and `python tests/test_flagship_playwright_smoke.py` must both pass.
7. PR.

---

## Testing strategy

Three orthogonal test layers — DO NOT skip any when shipping a change to the engine, badge JS, or any flagship.

### Layer 1: Engine unit tests (Node)
`node tests/test_dose_response_engine.mjs` — 60 deterministic tests covering numerics (Nelder-Mead Rosenbrock, Q-profile bisection, REML log-likelihood, log-determinant, pmTau2), fits on the 4 fixtures, F-5 edge cases (validate + HKSJ floor at k=2), Round 1A/2A/2B regression pins. **Always green before PR.**

### Layer 2: Flagship field-path contract (Node, no browser)
`node tests/test_flagship_field_paths.mjs` — 32 assertions per flagship. Codifies the engine-API surface each flagship reads. **Catches the Round 2C hotfix bug class** (top-level vs nested field-path access). Also simulates the R-parity badge state per fixture.

### Layer 3: Real-browser smoke (Python Playwright headless Chromium)
`python tests/test_flagship_playwright_smoke.py` — 4 assertions per flagship. Launches a real browser, navigates to each flagship, asserts: (a) no console/page JS errors, (b) no `HKSJ-mv = n/a` user-facing displays, (c) R-parity badge renders with GREEN class, (d) engine_version span populated with `0.3.0`. **Catches CSP / inline-script / async-render-race bugs that pure Node tests miss.**

### Layer 4: R cross-validation (optional, run on fixture changes)
`python scripts/r_validate_doseresp.py --review <name>` — regenerates the R precompute JSON via metafor + dosresmeta + lme4 at `jsonlite::toJSON(digits=8)` (the digits=8 precision fix shipped in Round 3.1; default `digits=4` produces τ²-rounding false-positive ambers). Compare against engine via the badge's threshold matrix.

### Why all four matter
Each layer catches a different bug class. The CSP regression went undetected for weeks because Layers 1+2 don't open a browser; the field-path bug stayed under the radar of Layer 1; the Round 3.1 τ²-rounding false-positive stayed under the radar of everything except a manual reviewer's deep dive.

---

## R cross-validation harness

`scripts/r_validate_doseresp.py` (Python wrapper) → `scripts/r_validate_doseresp.R` (R worker).

R packages used: `metafor` (linear pool — REML default), `dosresmeta` (RCS — `type="ir"` binary, `covariance="md"` continuous), `lme4::lmer` (continuous one-stage), `lme4::glmer` (binary one-stage with Poisson + offset, dose rescaled by sd to avoid near-unidentifiability).

Output JSON shape:
```json
{
  "linear": {"pooled_slope_log": …, "tau2": …, …},
  "rcs": {"spline_coefs": […], "nonlinearity_wald_p": …, "fit_at_dose": [{dose, est, ci_lo, ci_hi}, …]},
  "one_stage": {"slope": …, "lme4_version": …, "converged": …}
}
```

Numeric precision: `jsonlite::toJSON(..., digits=8)` (Round 3.1 fix; default 4 rounded R's τ²=0.001644 to 0.0016 which then tripped the badge's 0.0001 threshold).

### R-parity badge tolerances (per row)

`vendor/r-validation-doseresp.js` v0.2.0:

```js
var THRESHOLDS = {
  linear_slope: 0.01,
  linear_tau2: 0.0001,
  rcs_coef_0: 0.01,
  rcs_coef_1: 0.01,
  nonlinearity_p: 0.05,
};
```

Round 2C (PR #247) replaced the always-amber `nonlinearity_p` row with the threshold-driven `0.05` after the engine v0.3.0 closed the diagonal-PM divergence to R mixmeta.

### Known threshold-vs-estimator-divergence cases

At small k (k=2), PM (engine fitLinear) and REML (R metafor) τ² estimates diverge by enough to trip the `linear_tau2: 0.0001` threshold — expected, not a bug. The SURMOUNT obesity flagship (Round 3.5, k=2) displays this AMBER row by design as a documented small-k estimator artefact.

---

## Lessons captured by this pack (cross-referenced in `lessons.md`)

| Bug class | Pack incident | Mitigation |
|---|---|---|
| Diagonal-PM divergence from R mixmeta on RCS non-linearity p | Round 1A/2A always-amber row | Round 2B full-REML lift |
| `result.rcs.hksj_mv` undefined (top-level vs nested) | Round 2C field-path bug, PR #250 hotfix | `tests/test_flagship_field_paths.mjs` codifies contract |
| jsonlite `digits=4` rounds τ² and trips badge threshold | Round 3 SURPASS τ² parity row went amber | Round 3.1 `digits=8` in shared R script |
| CSP `script-src 'self'` + inline scripts | All 3 flagships broken in real browsers from Round 2A onward | PR #257 extracts to sibling `.js` + Playwright test |
| HKSJ floor at k=2 (Q < df → qstar = 1) | F-5 test gap | Round 2B Task 11 explicit test |
| Reference arm semantics in active-comparator trials | SURPASS-2/3/4 dropped comparator per Option A in agent extraction spec | Documented in fixture `data_provenance` |
| PM-vs-REML τ² divergence at k=2 | Round 3.5 SURMOUNT obesity | Surfaced as documented AMBER row, not hidden |
| AACT estimand variation (treatment-regimen vs efficacy) | SURPASS-2/5 (TR estimand) vs SURMOUNT-1/2 (efficacy estimand) | Each fixture's `data_provenance` documents which AACT primary was extracted |

---

## Source map

```
rapidmeta-dose-response-engine-v1.js              ~1500 lines, v0.3.0 (Round 2B)
vendor/r-validation-doseresp.js                   ~130 lines, v0.2.0 (Round 2C)

ALCOHOL_BC_DOSE_RESP_REVIEW.html  + .js
SGLT2I_DOSE_RESP_REVIEW.html      + .js
TIRZEPATIDE_T2D_SURPASS_DOSE_RESP_REVIEW.html  + .js
(TIRZEPATIDE_OBESITY_SURMOUNT_DOSE_RESP_REVIEW.html + .js — Round 3.5, in flight)

tests/dose_response_fixtures/
  gl1992_alcohol_bc.json
  sglt2i_hba1c.json
  sglt2i_hhf.json
  tirzepatide_t2d_surpass.json
  tirzepatide_obesity_surmount.json

fixtures/dose_response/
  tirzepatide_t2d_surpass_abstracts.json
  tirzepatide_obesity_surmount_abstracts.json

outputs/r_validation/doseresp/
  gl1992_alcohol_bc.json
  sglt2i_hba1c.json
  sglt2i_hhf.json
  tirzepatide_t2d_surpass.json
  tirzepatide_obesity_surmount.json

scripts/
  r_validate_doseresp.py
  r_validate_doseresp.R

tests/
  test_dose_response_engine.mjs              (60 unit tests)
  test_flagship_field_paths.mjs              (96 contract assertions)
  test_flagship_playwright_smoke.py          (12 browser assertions)

docs/
  E156_diagonal_pm_to_reml_close_draft.md    (Methods Note draft for Synthēsis)
  dose_response/README.md                    (this file)
  superpowers/specs/                         (per-round design docs)
  superpowers/plans/                         (per-round implementation plans)
```

---

## Open work / known limitations

- **fitRCS structural refactor** (Round 2C reviewer recommendation, deferred): the fitRCS function is ~350 lines after Round 2B's additions. Candidates for extraction to `_internal`: the REML optimization block, the pooled-β re-derivation, the fit_at_dose grid construction. Risk: high regression surface. Mitigation: the field-path contract test + engine unit tests provide a tight safety net.
- **One-stage convergence at k=2** (Round 3 SURPASS, Round 3.5 SURMOUNT): R lme4 reports boundary-singular RE variance; fixed-effect coefs still reliable but the UI surfaces an amber convergence note.
- **Estimand uniformity across fixtures**: SURPASS uses treatment-regimen estimand; SURMOUNT uses efficacy estimand. Both are FDA-acceptable AACT primaries. Documented per-fixture; not normalized.
- **HKSJ-multivariate at k=2 produces tcrit ≈ 12.7** (t_{1, 0.975}). CIs are honestly very wide — flagship copy emphasizes "do not report as a real-world meta-analytic estimate" for the SURMOUNT k=2 case.

---

## Provenance

Maintained by Anthropic Claude (Opus 4.7) under Mahmood Ahmad's supervision. AACT snapshots cited per fixture (`2026-04-12`). PubMed primary publications verified via PubMed MCP at extraction time; no PMIDs guessed.
