# rapidmeta-dose-response-engine-v1 — Design

**Status:** v0.1 spec (2026-05-12).

**Mirrors:** `rapidmeta-dta-engine-v1.js` API surface and the 2026-05-12 DTA Rscript-out-of-process validator triplet (`scripts/r_validate_dta.{R,py}` + `vendor/r-validation-dta.js`).

**Series:** Pack #4 in the methodological topic-pack series (prognostic → prediction → survival → dose-response). Pack #5 candidate: DTA engine (existing DTA reviews currently have no dedicated engine).

---

## 1. Purpose

Pool aggregate-data dose-response meta-analyses where:

- Trials publish per-arm dose, event count, and N (binary outcomes) or per-arm dose with continuous outcome (e.g. eGFR slope);
- The exposure-response relationship is suspected to be non-linear (plateau, J-shape) — which is the actual SGLT2i story across CVOTs;
- The MA should expose monotonic-linear, non-linear-spline, and one-stage-hierarchical answers side-by-side rather than committing to a single model.

The engine surfaces three layered models with a UI toggle: two-stage Greenland-Longnecker linear (primary), two-stage GL + restricted cubic splines (RCS, non-linear), and one-stage hierarchical mixed model. Each layer is R-validated against `dosresmeta` (linear, RCS) or `nlme::lme` / `lme4::glmer` (one-stage) via the Rscript-out-of-process pattern.

## 2. Input data shape

```js
trial = {
  studlab,                  // e.g. "EMPEROR-Preserved 2021"
  pmid, nct,
  outcome,                  // 'hHF' | 'CV_death' | 'eGFR_slope' | 'hyperkalemia'
  outcome_type,             // 'binary' (events) | 'continuous' (mean+sd)
  arms: [
    {
      dose,                       // numeric, in canonical unit (mg/day for SGLT2i)
      events,                     // binary only
      n,                          // total in arm
      time_at_risk,               // optional; person-years for offset in one-stage Poisson
      mean,                       // continuous only
      sd,                         // continuous only
      is_reference,               // boolean; exactly one arm per trial
    }, ...
  ],
}
```

## 3. Public API

Loaded as `<script src="rapidmeta-dose-response-engine-v1.js" defer></script>`. Exposes `window.RapidMetaDoseResp`:

| Function | Purpose |
|---|---|
| `validate(trials)` | array of issue strings; `[]` if OK |
| `fitLinear(trials, opts)` | two-stage GL linear; pooled log-slope + τ² + Q-profile CI |
| `fitRCS(trials, opts)` | two-stage GL + RCS (3 or 4 knots); pooled spline coefs + Wald non-linearity test |
| `fitOneStage(trials, opts)` | one-stage hierarchical mixed model |
| `nonLinearityTest(rcsResult)` | Wald joint test (H0: all non-linear coefs = 0) |
| `predict(result, dose)` | per-dose effect estimate + 95% CI (used to draw the curve) |
| `forest(trials, result)` | per-study slope or RCS-coef rows |
| `exportResults(result)` | strips internals; adds `engine_version`+`exported_at` |
| `_internal` | helpers for testing |

## 4. Statistical methods

- **Two-stage GL linear:** per-study log-linear slope from (dose, event, N) triples; Greenland-Longnecker correlation correction for shared-reference covariance; pooled via REML+HKSJ with floor `max(1, Q/(k-1))` per `advanced-stats.md`.
- **Two-stage GL + RCS:** knots placed at standard percentiles (3 knots at 25/50/75; 4 knots at 5/35/65/95 per Harrell defaults); per-study spline-coef vector via GL applied per spline-basis column; multivariate-RE pool; Wald joint non-linearity test.
- **One-stage hierarchical:** mixed model across all study-dose rows with random study slopes/intercepts. For binary outcomes uses `glmer` Poisson approximation with `offset(log(time_at_risk))`; for continuous outcomes uses `lme` with identity link.
- **τ² CI:** Q-profile (Viechtbauer 2007) on the log-linear-slope scale (linear layer); joint multivariate equivalent for RCS.
- **PI:** Higgins-Riley with `t_{k-1}` df (Cochrane v6.5 §10.10.4.3 default).
- **Continuity correction:** add 0.5 ONLY if ≥1 cell is zero in a binary trial (per `advanced-stats.md`); never unconditional.
- **Estimator floor:** NEVER use DL for k<10. REML primary; PM fallback. HKSJ always on.

## 5. Output shape

```js
{
  layer,                              // 'linear' | 'rcs' | 'one_stage'
  k,                                  // trials with usable arms after validate()
  pooled_slope_log,                   // linear-layer primary
  pooled_slope_log_se,
  pooled_slope_log_ci_lo, pooled_slope_log_ci_hi,
  rcs: {
    knots,                            // [dose_q1, dose_q2, ...]
    spline_coefs,                     // length(knots)-1 vector
    spline_coefs_cov,                 // covariance matrix
    nonlinearity_wald_p,              // joint Wald test
    fit_at_dose: [{dose, est, ci_lo, ci_hi}]   // curve points for plotting
  } | null,
  one_stage: {
    coef_dose, coef_dose_se,
    random_effects_var,
    converged, n_iterations
  } | null,
  tau2, tau2_lo, tau2_hi,             // REML + Q-profile
  Q, Q_df, I2, H2,
  pi_lo, pi_hi, pi_df,
  hksj_adj, hksj_qstar,
  per_study: [{studlab, slope_log, slope_log_se, n_arms}],
  coverage_warning,                   // k < 10
  fallback,                           // null | 'fixed_effect_k_lt_5' | 'single_study'
  estimator,                          // 'reml_hksj' | 'pm_hksj' | 'fixed_effect'
  converged, iterations,
  _fitInternal,
}
```

## 6. Validation contract — DTA pattern, NOT webR

Three artifacts mirroring the 2026-05-12 DTA validator triplet exactly:

```
scripts/r_validate_doseresp.R      R 4.5.2 + dosresmeta + nlme (+ lme4 for one-stage binary)
scripts/r_validate_doseresp.py     Python wrapper; CLI: --review <REVIEW_NAME>
                                   Extracts <script type="application/json" id="doseresp-trials">,
                                   emits CSV, calls Rscript, writes JSON to:
outputs/r_validation/doseresp/<REVIEW>.json
vendor/r-validation-doseresp.js    Collapsible R-parity badge panel for flagship HTML
```

Badge logic (parallels DTA):

- **Green** if pooled linear log-slope |Δ| < 1pp, RCS coef joint L2-norm |Δ| < 2pp, non-linearity Wald p |Δ| < 5pp.
- **Amber** with explicit per-component deltas printed otherwise.

No webR. No in-browser R load. R runs out-of-process at build time; JSON is checked in.

## 7. Flagship HTML — `SGLT2I_DOSE_RESP_REVIEW.html`

5 tabs:

1. **hHF** (binary) — primary outcome
2. **CV death** (binary)
3. **eGFR slope** (continuous, mL/min/1.73 m²/yr)
4. **Hyperkalemia** (binary; J-shape candidate; teaches harm-curve)
5. **Non-linearity across outcomes** — side-by-side Wald p-values for each outcome's RCS fit

Each outcome tab shows: per-study forest, three-layer toggle (linear / RCS / one-stage), pooled-estimate panel, R-parity badge (from `vendor/r-validation-doseresp.js`), AACT cross-check note.

## 8. Tests — `tests/test_dose_response_engine.mjs`

Target ≥40 tests covering:

- `validate()` rejects: single-arm study, reference-only study, negative events, mismatched outcome_type, all-identical-doses, missing reference flag.
- `fitLinear()` — k=1/k=2 edge; Greenland-Longnecker correlation parity with `dosresmeta` to 1e-6 on Greenland & Longnecker's 1992 alcohol-breast-cancer canonical dataset; HKSJ floor honoured.
- `fitRCS()` — Harrell-percentile knot placement; Wald non-linearity p matches `dosresmeta` on canonical fixture; degenerates to linear when knots collapse.
- `fitOneStage()` — `lme` convergence on continuous; `glmer` convergence on binary; flags non-convergence cleanly without poisoning the layer-toggle UI.
- `exportResults()` / `predict()` / `forest()` shape contracts.
- **5 adversarial fixtures**: (a) k=2 with identical doses, (b) single-arm, (c) reference-only, (d) extrapolation beyond max observed dose (engine returns banner-flag), (e) Greenland-Longnecker 1992 canonical sanity check.

## 9. Hardening cadence — 5 rounds, mirrors prior packs

1. **P0** — scaffold engine + flagship HTML + R validator triplet + 5 adversarial fixtures; PMID/citation hygiene; AACT cross-check passes for all 4 outcome trial sets.
2. **P1** — engine numerical fixes (Brent convergence guarantee, RCS knot fallback when doses degenerate, conditional zero-cell correction).
3. **P2** — Wald-parity with `dosresmeta` to 1e-6; q-profile τ² CI; heterogeneity-fragility flag (matches prediction-pack P2).
4. **Nits** — Greenland-Longnecker 1992 reference documented inline; JSDoc on public API; HTML polish.
5. **Round-2** — flagship HTML convergence with the DTA badge UX; cross-pack consistency check across all 4 methodological packs.

## 10. Pre-push gates

- `python scripts/aact_cross_check_v2.py --review SGLT2I_DOSE_RESP_REVIEW` returns OK.
- **AACT caveat**: per-arm dose isn't in AACT's stock tables. Extraction may fall back to `detailed_descriptions` + `design_groups` joins. Flagged as P0 risk; resolve early in round 1.
- Sentinel BLOCK = 0 on the touched files; no new `P0-hardcoded-local-path` regressions.
- All adversarial fixtures green; R-parity all green across 4 outcomes.
- `DECISIONS.md` clean (no new `UNKNOWN` semgrep entries introduced by this pack).

## 11. Out-of-scope (v1.x)

- WebR / in-browser R fitting (DTA pattern is out-of-process; no need).
- Bayesian dose-response (e.g. JAGS hierarchical) — deferred to a future pack.
- IPD dose-response (one-stage with full IPD per arm) — current input shape is aggregate per-arm only.
- Time-varying / cumulative-dose exposure — single-dose-per-arm only.
- Network dose-response (NMA across multiple drugs at multiple doses) — single drug only.

## 12. Resolved decisions (this session, 2026-05-12)

| Question | Decision |
|---|---|
| Pack flavour | Dose-response MA (not "more drug HTMLs") |
| Flagship topic | SGLT2i dose vs HF/CKD outcomes |
| Engine scope | All three layers (linear, RCS, one-stage), UI toggle |
| Outcomes | hHF + CV death + eGFR slope + hyperkalemia + non-linearity panel |
| Validation | Rscript-out-of-process (DTA pattern); no webR |
| Hardening | Full 5-round cadence matching prior packs |
| Spec location | `docs/superpowers/specs/2026-05-12-rapidmeta-dose-response-engine-design.md` |
