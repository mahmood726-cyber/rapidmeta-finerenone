# Dose-Response Pack — Round 2B Design (Engine v0.3 Math Hardening)

**Status:** v0.1 spec (2026-05-13).

**Depends on:** Round 2A merged at `466afc50` on main (engine v0.2.0 with continuous-outcome + F-1).

**Series:** Round 2B of pack #4 — pure engine math hardening. No UI changes; no new fixtures. The headline closes the long-documented diagonal-PM-vs-R-full-REML divergence on RCS non-linearity p.

---

## 1. Purpose

Round 1A/1B/2A all shipped under the documented v0.1 engine approximation: `fitRCS` uses diagonal-PM-per-dimension τ² (each spline-basis coefficient gets its own independent Paule-Mandel τ²). R `mixmeta` / `dosresmeta` use full multivariate REML (joint τ² matrix). On the GL-1992 fixture this produces engine non-linearity Wald p ≈ 0.05 vs R ≈ 0.70 — a real ~14× divergence, surfaced in the R-parity badge's always-amber row, but a known v0.1 limitation.

Round 2B closes that gap (and four related items): full multivariate REML via Nelder-Mead on the REML log-likelihood; HKSJ-multivariate + `t_{k−1}` CI for fitRCS (follows naturally from the new τ² matrix); Q-profile τ² CI for fitLinear (currently `tau2_lo: null, tau2_hi: null`); F-5 test gap closure; P2-13 API forward-reference structural refactor.

After Round 2B, the R-parity badge's non-linearity-p row should turn GREEN on both GL-1992 and SGLT2i — engine and R agree on the documented R-validated math.

## 2. Inputs and outputs

**Inputs:**
- Existing engine `rapidmeta-dose-response-engine-v1.js` (v0.2.0)
- Existing test suite `tests/test_dose_response_engine.mjs` (47 tests)
- Existing fixtures and R-precomputed outputs (no changes)

**Outputs:**
- Updated engine v0.3.0
- ~5 new tests (~52 total)
- No fixture changes
- No HTML changes (existing flagships keep working; the R-parity badge re-computes the engine values at page-load time and will now show green on the non-linearity row)

## 3. Full multivariate REML for fitRCS

### 3.1 Why

Current `fitRCS` (engine v0.2.0) does per-dimension Paule-Mandel τ² independently:

```javascript
// Round 1A/1B/2A: diagonal-PM-per-dimension τ²
for (var d = 0; d < Kp; d++) {
  tau2_per_dim[d] = pmTau2(yi_d, vi_d);  // INDEPENDENT per dimension
}
```

This treats spline-basis dimensions as orthogonal, which they aren't. The Wald non-linearity statistic uses only diagonal elements of the (engine-implicit) τ² matrix, missing the off-diagonal covariance that R captures. Result: engine p ≈ 0.05 vs R p ≈ 0.70 on GL-1992.

### 3.2 What

Replace the per-dimension PM loop with a single REML optimization over the full τ² matrix (a `Kp × Kp` symmetric positive-semi-definite matrix where `Kp = K − 1` for `K` knots).

The REML log-likelihood for the multivariate model is:

```
ℓ(τ²) = −½ ∑_i log|V_i + τ²|  −  ½ ∑_i (y_i − Xβ)' (V_i + τ²)⁻¹ (y_i − Xβ)
        − ½ log|∑_i X'_i (V_i + τ²)⁻¹ X_i|
```

where `V_i` is the per-trial within-study covariance and `X_i` is the per-trial basis matrix. The β is profiled out (`β̂ = (∑ X'_i W_i X_i)⁻¹ ∑ X'_i W_i y_i` with `W_i = (V_i + τ²)⁻¹`).

We optimize over the lower-triangular Cholesky factor `L` of `τ² = LL'` to enforce positive-semi-definiteness implicitly. For `Kp = 2` (the GL-1992 + SGLT2i case with 3 knots) the optimization is over 3 scalars (`L[0][0], L[1][0], L[1][1]`).

### 3.3 How — Nelder-Mead simplex

A standard derivative-free simplex routine on the 3 (or `Kp*(Kp+1)/2`) Cholesky parameters:

1. Initialize the simplex at the current diagonal-PM values (warm-start; off-diagonals at zero).
2. Iterate Nelder-Mead with standard reflection/expansion/contraction coefficients (α=1, γ=2, ρ=0.5, σ=0.5).
3. Convergence: relative change in REML log-likelihood < 1e-6 OR max-iterations 200.
4. Recover `τ² = LL'` from the converged Cholesky factor.
5. Compute pooled β via `β̂ = (∑ X'_i W_i X_i)⁻¹ ∑ X'_i W_i y_i` and Cov(β̂) = `(∑ X'_i W_i X_i)⁻¹` evaluated at the converged τ².

Estimated size: ~60-80 lines of new JS (Nelder-Mead simplex + REML log-likelihood evaluator). Plus existing matrix primitives (matInv, etc.).

### 3.4 Public API

`fitRCS` return shape gains:

```js
rcs: {
  ...existing fields,
  tau2_matrix: <Kp×Kp matrix>,         // NEW: full multivariate τ²
  tau2_per_dim: [...],                  // retained for backward compat; now = diagonal of tau2_matrix
  reml_converged: <bool>,               // NEW
  reml_iterations: <int>,               // NEW
  reml_loglik: <number>,                // NEW
  // Wald non-linearity now uses the FULL τ² matrix + full cov(β̂),
  // matching R's t(β_nl) %*% solve(V_full_nl) %*% β_nl
  nonlinearity_wald_p: <number>,        // expected to match R within |Δ| < 0.1
}
```

`estimator` field changes from `'pm_diagonal_z'` to `'reml_hksj_multivariate'` (per §5 below). `ci_method` changes from `'z_1.96'` to `'hksj_t_km1'`.

### 3.5 Backward compatibility

- Existing tests that pin `nonlinearity_wald_p ≈ 0.05` on GL-1992 (Round 1A regression-pin test) must be UPDATED to expect the new R-matching value (~0.7).
- The Round 1B HTML's amber-by-design non-linearity-p note in the RCS tab is no longer accurate — the engine now matches R, so the amber row in the badge becomes GREEN automatically (the badge already uses dynamic threshold-vs-engine comparison; no HTML change required).
- The flagship's amber note text can be relaxed in a Round 2B-cleanup commit (optional; covered by the Round 2B P1 review cycle).

## 4. HKSJ-multivariate + t_{k−1} for fitRCS

With full multivariate REML, the multivariate HKSJ scaling factor is well-defined:

```
HKSJ_mv = max(1, Q_mv / (n − p))
```

where `Q_mv = ∑_i (y_i − Xβ)' (V_i + τ²)⁻¹ (y_i − Xβ)` is the multivariate Cochran Q, `n = ∑_i k_i` is total observations, and `p = Kp` is parameter count.

CIs use `t_{k−1}` (matching fitLinear's Cochrane v6.5 convention).

`fit_at_dose` grid CIs lift from `est ± 1.96 × se` to `est ± t_{k−1}(0.975) × √HKSJ_mv × se`.

## 5. Q-profile τ² CI for fitLinear

Currently `fitLinear` returns `tau2_lo: null, tau2_hi: null` (deferred to P2 per Round 1A spec).

Implement Viechtbauer 2007 Q-profile via `qchisq` bracket on the Q-distribution:

```
tau2_lo = inf{τ² : Q(τ²) ≤ qchisq(1 − α/2, df)}
tau2_hi = sup{τ² : Q(τ²) ≥ qchisq(α/2, df)}
```

where `Q(τ²) = ∑_i (y_i − ȳ_τ²)² / (v_i + τ²)` is the generalized Q statistic at a candidate τ², `ȳ_τ²` is the corresponding RE-pooled mean, and `df = k − 1`. Bracket via bisection on `[0, 100 * τ²_estimate]`.

Estimated size: ~30-40 lines new JS.

`fitLinear` return shape gains finite values for `tau2_lo` and `tau2_hi`.

## 6. F-5 test gap closure

Spec target ≥ 40 tests; current count is 47 but the spec-listed categories aren't all covered. Add:

1. **`validate-two-arm-no-ref`** — a trial with 2 arms but no `is_reference: true` should be flagged. Test: `validate([{arms:[{dose:0,events:10,n:100},{dose:5,events:15,n:100}]}])` returns issue matching `/no reference arm/i`.
2. **`fitLinear-k=2-HKSJ-floor-fires`** — with k=2 and small Q, HKSJ floor `max(1, Q/(k−1))` clamps to 1. Test: `fitLinear` on a k=2 fixture with homogeneous trials produces `hksj_qstar === 1` (floor fired).

The `validate-mismatched-outcome-type` test was added in Round 2A (Task 2); already covered.

## 7. P2-13 API forward-reference structural refactor

Currently:

```javascript
(function (root) {
  'use strict';
  // ... numerics ...
  function validate(trials) {
    // ... references API._internal indirectly via _internal.<fn> ...
  }
  function fitLinear(trials, opts) {
    // ... uses API.engine_version inside the return object ...
  }
  // ... more functions ...
  var API = {  // <-- defined AFTER all functions reference it
    engine_version: '...',
    validate: validate,
    fitLinear: fitLinear,
    ...
    _internal: { ... }
  };
  root.RapidMetaDoseResp = API;
})(typeof window !== 'undefined' ? window : globalThis);
```

This works via `var` hoisting (`API` is hoisted as undefined and only set later) but is a footgun: any function called during IIFE init would read `API.engine_version` as `undefined.engine_version` and throw.

Refactor to:

```javascript
(function (root) {
  'use strict';
  var API = {  // <-- defined FIRST
    engine_version: 'rapidmeta-dose-response-engine-v1@0.3.0',
    _internal: {},
  };
  // ... numerics ... (assigned to API._internal as each helper is defined)
  function validate(trials) { ... }
  API.validate = validate;
  function fitLinear(trials, opts) { ... }
  API.fitLinear = fitLinear;
  // ... etc. ...
  root.RapidMetaDoseResp = API;
})(typeof window !== 'undefined' ? window : globalThis);
```

Mechanical refactor. No semantic change. ~30 lines of structural reordering. The new `nelderMead` helper (§3.3) and `qProfileCI` helper (§5) are assigned to `_internal` immediately after each is defined.

## 8. Validation gate

- **Engine tests:** 47 → ~52
- **GL-1992 non-linearity Wald p:** engine within `|Δ| < 0.1` of R full-REML (~0.70). The Round 1A regression-pin test at p ≈ 0.05 is UPDATED.
- **SGLT2i HbA1c + hHF non-linearity Wald p:** similar parity gate (engine should now match R within `|Δ| < 0.15` — wider tolerance because SGLT2i has lower k).
- **fitLinear Q-profile τ² CI:** returns finite values for `tau2_lo` and `tau2_hi`; CI brackets the point estimate.
- **HKSJ-mv:** `fitRCS` `estimator` field is `'reml_hksj_multivariate'`; `ci_method` is `'hksj_t_km1'`.
- **GL-1992 linear pool:** still produces `pooled_slope_log * 11 ≈ 0.254` (regression guard — no math change in fitLinear except adding tau2 CI bounds).
- **SGLT2i regression:** both flagships still render; R-precompute outputs unchanged.

## 9. Pre-push gates

- Engine 52/52 tests passing
- Sentinel BLOCK = 0 on touched files
- R cross-check: run `python scripts/r_validate_doseresp.py --review gl1992_alcohol_bc` and verify the R precomputed values are unchanged (the engine evolved; R is the reference)

## 10. Out of scope (Round 2C)

- Automated Playwright browser test
- F-6 stale plan file structure doc fix
- P1-7 + P2-5 shared `vendor/r-validation-badge.js` `escapeHtml` (parallel-session ownership; check status before claiming)
- Cross-pack consistency sweep with prognostic / prediction / survival / DTA engines

## 11. Resolved decisions (2026-05-13 brainstorm)

| Question | Decision |
|---|---|
| Sub-round to start | Round 2B (engine math hardening) ahead of 2C (infra) |
| Multivariate REML approach | Nelder-Mead simplex on Cholesky parameters (vs Newton-Raphson with analytic gradient OR block-coordinate descent) |
| Parity target on non-linearity p | engine within |Δ| < 0.1 of R full-REML on GL-1992 |
| Q-profile τ² CI for fitLinear | Viechtbauer 2007 bisection on Q-distribution |
| HKSJ-mv + t_{k-1} for fitRCS | follows naturally from full REML; `ci_method` label changes |
| F-5 missing tests | add `validate-two-arm-no-ref` + `fitLinear-k=2-HKSJ-floor-fires` |
| P2-13 structural refactor | move API definition to top of IIFE; assign methods after each function |
| Engine version | v0.2.0 → v0.3.0 |
| Spec/plan paths | `docs/superpowers/specs/2026-05-13-dose-response-round-2b-design.md` + matching plan path |
