# rapidmeta-survival-engine-v1 — Design

**Status:** v0.1 spec (2026-05-11). Owner: claude/kind-goodall-7448d3.

**Mirrors:** `rapidmeta-dta-engine-v1.js` API surface and `webr-dta-validator.js` validation pattern.

---

## 1. Purpose

Pool time-to-event meta-analyses where:
- Most trials publish `HR (CI)` only;
- Some trials raise non-PH concerns (Schoenfeld residuals significant, visible curve crossings);
- A subset have reconstructed IPD (e.g. from `KMcurve` sibling output) and can contribute RMST or interval-HR estimates.

The engine surfaces all three layers: pooled log-HR (primary), pooled RMST-difference at fixed τ\*, and pooled interval-HR (early vs late window). It flags non-PH explicitly rather than burying it under a single HR.

## 2. Input data shape

```js
trial = {
  studlab,                   // e.g. "EMPEROR-Preserved 2021"
  HR, HR_ci_lo, HR_ci_hi,    // primary; REQUIRED unless events given for derivation
  events_trt, n_trt,         // OPTIONAL; for events-derived log-HR via Peto when CI absent
  events_ctl, n_ctl,
  follow_up_months,          // OPTIONAL; weighting context, not pooling weight
  schoenfeld_p,              // OPTIONAL; if present, used by nonPHDetect
  curve_crosses,             // OPTIONAL boolean; visual non-PH flag from authors
  km_curve: [{t_months, surv_trt, surv_ctl, n_at_risk_trt, n_at_risk_ctl}],  // OPTIONAL; for RMST and interval-HR
  weight,                    // OPTIONAL; bypass IV weighting if caller pre-weights
}
```

## 3. Public API

Loaded as `<script src="rapidmeta-survival-engine-v1.js" defer></script>`. Exposes `window.RapidMetaSurvival`:

| Function | Purpose |
|---|---|
| `validate(trials)` | array of issue strings; `[]` if OK |
| `fit(trials, opts)` | primary entry; pools log-HR with REML+HKSJ; returns full result + `_fitInternal` |
| `exportResults(result)` | strips `_fitInternal`, adds `engine_version`+`exported_at` |
| `predict(result)` | Higgins-Riley PI on log-HR scale; `t_{k-2}` (Cochrane v6.5 §10.10.4.3) |
| `forest(trials, result)` | paired HR / RMST layout rows |
| `rmstAtTau(km_curve, tau)` | per-trial RMST at τ\* via trapezoid |
| `poolRMSTDiff(trials, tau, opts)` | pooled RMST-difference (REML+HKSJ) |
| `intervalHRPool(trials, breakpoints)` | per-window pooled HR + crossover diagnostic |
| `nonPHDetect(trials)` | aggregate non-PH flag with Schoenfeld-min, fraction-flagged |
| `nntForHR(HR, baseline_risk, tau_months)` | Altman 2002 NNT from HR conversion |
| `_internal` | helpers for testing |

## 4. Statistical methods

- **Log-HR pooling:** inverse-variance, REML τ² via Fisher scoring, HKSJ adjustment with floor `max(1, Q/(k-1))` per `advanced-stats.md`. PI df = `k-1` (Cochrane v6.5 default). NEVER use DL for k<10.
- **τ² CI:** Q-profile (Viechtbauer 2007) on the log-HR scale.
- **Non-PH detection:** `flag=true` iff any trial has `schoenfeld_p < 0.05` OR `curve_crosses === true`. Returns `n_trials_flagged` and `fraction_flagged`. Hard recommend to also pool RMST when flag fires.
- **RMST:** trapezoid integral of `S(t)` on the supplied KM curve to τ\* (months); SE via Greenwood-style finite-difference (Karrison 2018). RMST-difference pool: standard IV+REML on `rmst_diff` with `se` from delta method.
- **Interval HR:** Re-pool the log-HR estimates restricted to within-interval events (when interval-specific HRs published) OR derive from reconstructed-IPD via per-interval Cox-equivalent (events·log-HR) when `km_curve` supplied with `n_at_risk` ticks. v1.0 supports the published-interval-HR path; reconstructed-IPD path returns `null` if `km_curve` lacks at-risk ticks.
- **Royston-Parmar:** out of v1.0 scope as a fitting engine. The engine exposes `royston_parmar_panel(km_curve)` that returns the data needed for the panel to RENDER published RP coefficients when authors report them. No JS RP fitter — that's WebR territory.

## 5. Output shape

```js
{
  k,                                  // number of trials with usable HR
  pooled_logHR, pooled_HR,
  pooled_logHR_se,
  pooled_HR_ci_lo, pooled_HR_ci_hi,   // Wald 95% on log scale
  hksj_adj, hksj_qstar,               // HKSJ scaling factor and Q/(k-1)
  pooled_HR_hksj_ci_lo, pooled_HR_hksj_ci_hi,
  tau2, tau2_lo, tau2_hi,             // REML + Q-profile CI
  Q, Q_df, I2, H2,
  pi_HR_lo, pi_HR_hi, pi_df,
  nonph: { flag, n_flagged, fraction_flagged, schoenfeld_p_min },
  rmst: { pooled_diff, se, ci, tau_star, k, tau2 } | null,
  interval_hr: { intervals: [{label, t0, t1, HR, HR_ci_lo, HR_ci_hi, k}] } | null,
  per_study: [{studlab, logHR, seLogHR, HR, HR_ci}],
  coverage_warning,                   // k < 10
  fallback,                           // null | 'fixed_effect_k_lt_5' | 'single_study'
  estimator,                          // 'reml_hksj' | 'fixed_effect' | 'single_study'
  converged, iterations,
  _fitInternal: { ... }
}
```

## 6. Validation contract

R parity vs `metafor::rma(yi, vi, method="REML", test="knha")` at |Δ|<1e-3 on the log-HR scale via `webr-survival-validator.js`. Fallback to `metafor::rma(method="DL")` if REML fails. RMST parity vs `survRM2::rmst2` if available.

## 7. Tests

`tests/test_survival_engine.mjs` — target ≥35 tests covering validation, REML, HKSJ, PI, Q-profile, non-PH detection, RMST trapezoid, RMST pooling, interval-HR pooling, NNT-for-HR, exportResults, k=1/k=2 edge cases.

## 8. Out-of-scope (v1.x)

- JS-side Royston-Parmar fitting (WebR only)
- Reconstructed IPD from KM-curve digitisation (use `KMcurve` sibling)
- Frailty models (Aalen / shared frailty)
- Competing-risks Fine-Gray pooling
