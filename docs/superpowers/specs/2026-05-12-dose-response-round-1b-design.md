# Dose-Response Pack — Round 1B Design (Flagship HTML + Engine P1 Fixes)

**Status:** v0.1 spec (2026-05-12).

**Depends on:** Round 1A merged at `403765c1` (engine + R validator triplet + 33 tests).

**Mirrors:** `PROGNOSTIC_HSTN_PAD_REVIEW.html` and `PREDICTION_MODEL_KFRE_REVIEW.html` flagship convention (single-file, ~850 lines, hidden-div tab toggling, no tab library). Badge UI mirrors `vendor/r-validation-dta.js` and `vendor/r-validation-continuous.js` shipped 2026-05-12.

**Series:** Round 1B of pack #4. Round 1A shipped the engine + R validator + 33 tests + 5 fixtures. Round 1B ships the flagship HTML that consumes the engine and surfaces the R-parity badge.

---

## 1. Purpose

Demonstrate the dose-response engine on the Greenland-Longnecker 1992 alcohol-breast-cancer canonical dataset — the same fixture the engine is R-validated against. Single-outcome, multi-trial, multi-dose data with rich teaching value:

- Five real published studies (Schatzkin 1987, Willett 1987, Hiatt 1988, Garfinkel 1988, Howe 1991) all in the GL-1992 vignette.
- Multi-dose per study (3–5 doses) — the engine's required input shape.
- Pooled values cross-validated against R `dosresmeta::dosresmeta(method='reml')` and `lme4::glmer(family=poisson)`.
- High between-study heterogeneity (I² ≈ 95% on log-slope) — a teaching case for RE-vs-FE pool divergence.

Rationale for choosing GL-1992 over the original SGLT2i plan: most SGLT2i CVOTs are single-dose trials. A credible SGLT2i dose-response MA requires within-trial-multi-dose subsets (EMPA-REG OUTCOME, CANVAS, SOLOIST, Wilding 2009) or cross-drug equivalence assumptions, neither of which is methodologically clean for a v0.1 flagship. SGLT2i becomes Round 2 once the data sourcing is settled.

## 2. Inputs and outputs

**Inputs:**
- `tests/dose_response_fixtures/gl1992_alcohol_bc.json` — the Round 1A canonical fixture (5 trials × 4-5 arms each = 22 data rows total).
- `outputs/r_validation/doseresp/gl1992_alcohol_bc.json` — the Round 1A R-precomputed output (linear + RCS); Round 1B extends this with a `one_stage` block.

**Outputs:**
- `ALCOHOL_BC_DOSE_RESP_REVIEW.html` — the flagship.

## 3. HTML structure

Single-file HTML, ~600-900 lines, no external dependencies except CDN-loaded fonts (per repo convention; HTMLs are fully offline-capable except for fonts). Loaded scripts (all `defer`):
- `rapidmeta-dose-response-engine-v1.js`
- `vendor/r-validation-badge.js` (shared framework)
- `vendor/r-validation-doseresp.js` (NEW)
- Inline `<script type="application/json" id="doseresp-trials">…</script>` carrying the GL-1992 trial JSON

### 3.1 Header section (above tabs)

- Title: "Alcohol intake and breast cancer incidence — dose-response meta-analysis"
- Subtitle: "Pooled re-analysis of Greenland & Longnecker 1992 worked example, AJE 135:1301-9 (PMID 1626547)"
- Author block + date stamp (engine version + R version)
- Methodology note (collapsible): cites advanced-stats.md rules — REML+HKSJ, PI df=k-1 (Cochrane v6.5), HKSJ floor max(1, Q/(k-1)), τ² CI deferred to P2
- Per-study trial summary table (collapsible): 5 rows, columns `studlab | PMID | dose-arm count | total events | total person-years`

### 3.2 Tab 1 — Linear (default landing tab)

| Section | Content |
|---|---|
| Top KPIs | Pooled log-RR per gram (with CI), pooled RR per 11 g/day (back-transformed), τ², I², Q, PI bounds |
| Per-study forest | 5 rows (one per trial) — per-study slope_log + HR + CI + weight_pct (RE weights). Uses `forest()` post-F-3 fix. |
| Dose-response curve | 20-point grid from 0 to 45 g/day, est ± 95% CI band (uses `predict()` post-F-2 fix with t_{k-1}). Linear interpolation; no spline. |
| Summary text | Plain-English summary: "Pooled RR per 11g/day was {value} (95% CI {lo}-{hi})." |

### 3.3 Tab 2 — RCS

| Section | Content |
|---|---|
| Top KPIs | Knot locations (3 doses), spline_coefs[0] + spline_coefs[1], Wald non-linearity p (~0.05 under diagonal-PM) |
| RCS curve | 20-point grid; smooth curve through knot locations; 95% CI band per `fit_at_dose` |
| Per-study forest (RCS layer) | 5 rows; slope_log = spline_coefs[0]-equivalent per study; RE-weighted (post-F-3 fix) |
| Non-linearity test | Boxed: "Wald non-linearity test under diagonal-PM v0.1: chi² = {W}, df = {df}, p = {p}. Note: R full-REML gives p ≈ 0.70 on the same data; this is the documented diagonal-PM tradeoff. See R-parity tab." |

### 3.4 Tab 3 — One-stage hierarchical

Reads `outputs/r_validation/doseresp/gl1992_alcohol_bc.json` → `one_stage` block (added in this round to the R script).

| Section | Content |
|---|---|
| Top KPIs | coef_dose, coef_dose_se, 95% CI, random_effects_var, converged flag, glmer version |
| Per-study slopes | Not available from glmer fit; show "see R one_stage output" note |
| Methodology disclosure | "One-stage Poisson hierarchical model (lme4::glmer with offset(log(n))) fit by R; engine surfaces precomputed R output. No JS fitter — see engine spec §4 and §11." |

### 3.5 Tab 4 — R-parity badge

Embedded via `vendor/r-validation-doseresp.js` mounting on a designated div.

| Section | Content |
|---|---|
| Badge header | Green for linear-component parity, amber for documented non-linearity divergence |
| Side-by-side numbers | Engine value vs R value vs delta, for: pooled_slope_log, tau² (linear), spline_coefs[0], spline_coefs[1], nonlinearity_wald_p |
| Documented divergence note | Calls out the diagonal-PM-vs-full-REML divergence on non-linearity p as a known v0.1 design tradeoff |
| Engineering metadata | dosresmeta version, lme4 version, R version |

### 3.6 Footer

- Links to spec, plan, follow-ups doc
- Citation: Greenland S, Longnecker MP. Methods for trend estimation from summarized dose-response data, with applications to meta-analysis. Am J Epidemiol. 1992;135:1301-9. PMID 1626547.
- Engine version + Round 1B SHA

## 4. Engine P1 fixes (F-2, F-3)

Applied as two separate commits BEFORE the HTML work begins.

### 4.1 F-2 — `predict()` uses `t_{k-1}` for linear

Current code (engine line ~745):
```javascript
return { est: est, ci_lo: est - 1.96 * se, ci_hi: est + 1.96 * se, extrapolation_banner: banner };
```

New code:
```javascript
var df = result.pi_df != null ? result.pi_df : (result.k - 1);
var tcrit = df > 0 ? qt(0.975, df) : 1.96;
return { est: est, ci_lo: est - tcrit * se, ci_hi: est + tcrit * se, extrapolation_banner: banner };
```

For RCS results the grid already carries CIs; no change to that branch.

**Test impact:** existing `predict at dose=0 returns 0` and `predict extrapolation_banner` tests both still pass (neither pins CI width). Add a new test pinning the t-critical: `near(predict(lin, 5).ci_hi - predict(lin, 5).est, 5 * lin.pooled_slope_log_se * qt(0.975, lin.pi_df), 1e-10)`.

### 4.2 F-3 — `forest()` uses correct τ² for RCS

Current code (engine line ~775):
```javascript
var tau2 = result.tau2 || 0;
```

New code:
```javascript
var tau2;
if (result.layer === 'rcs' && result.rcs && Array.isArray(result.rcs.tau2_per_dim)) {
  tau2 = result.rcs.tau2_per_dim[0] || 0;
} else {
  tau2 = result.tau2 || 0;
}
```

**Test impact:** existing `forest returns per_study rows with weight_pct` test uses fitLinear result — still passes. Add a new test pinning RCS forest behavior: `forest on fitRCS result uses RE weights from tau2_per_dim[0]`.

## 5. R script extension — one-stage glmer

Append to `scripts/r_validate_doseresp.R` after the existing RCS block:

```r
# One-stage Poisson hierarchical (lme4::glmer)
suppressPackageStartupMessages({ library(lme4) })

fit_os <- tryCatch(
  glmer(events ~ dose + (1 | studlab), offset = log(n),
        family = poisson(link = "log"), data = df,
        control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e5))),
  error = function(e) NULL,
  warning = function(w) NULL  # silence convergence warnings; we capture converged flag below
)

out$one_stage <- if (is.null(fit_os)) list(fit_ok = FALSE) else {
  conv_ok <- is.null(fit_os@optinfo$conv$lme4$messages) || length(fit_os@optinfo$conv$lme4$messages) == 0
  ci <- tryCatch(confint(fit_os, parm = "dose", method = "Wald"), error = function(e) c(NA, NA))
  list(
    fit_ok = TRUE,
    lme4_version = as.character(packageVersion("lme4")),
    coef_dose = as.numeric(fixef(fit_os)["dose"]),
    coef_dose_se = as.numeric(sqrt(diag(vcov(fit_os))["dose"])),
    coef_dose_ci_lo = as.numeric(ci[1]),
    coef_dose_ci_hi = as.numeric(ci[2]),
    random_effects_var = as.numeric(VarCorr(fit_os)$studlab[1, 1]),
    converged = conv_ok
  )
}
```

The output JSON gains a top-level `one_stage` block:
```json
{
  "review": "gl1992_alcohol_bc",
  "engine": "R-dosresmeta",
  ...
  "linear": {...},
  "rcs": {...},
  "one_stage": {
    "fit_ok": true,
    "lme4_version": "1.1-35",
    "coef_dose": 0.0064,
    "coef_dose_se": 0.0012,
    "coef_dose_ci_lo": 0.0040,
    "coef_dose_ci_hi": 0.0088,
    "random_effects_var": 0.0009,
    "converged": true
  }
}
```

## 6. Badge JS — `vendor/r-validation-doseresp.js`

Mirrors the structure of `vendor/r-validation-dta.js` and `vendor/r-validation-continuous.js`. Mounts on `<div id="r-parity-doseresp"></div>` in the flagship HTML.

Public API (window global):
```javascript
window.RValidationDoseresp = {
  render: function (mountId, engineResults, rResults) { ... }
}
```

Threshold matrix:

| Metric | Green if | Amber otherwise |
|---|---|---|
| Linear pooled_slope_log | `|Δ| < 0.01` | always show delta |
| Linear tau² | `|Δ| < 0.0001` | always show delta |
| RCS spline_coefs[0] | `|Δ| < 0.01` | always show delta |
| RCS spline_coefs[1] | `|Δ| < 0.01` | always show delta |
| Non-linearity Wald p | ALWAYS AMBER with documented note (diagonal-PM v0.1 design tradeoff) | n/a |

The amber row for non-linearity p is not a defect — it is the design point of the badge for this engine version.

## 7. Tests

- Engine: 33 tests + 2 new (F-2 t-critical pin, F-3 RCS forest pin) = **35 tests** target. Existing tests must stay green after F-2/F-3.
- R script: smoke test confirms `one_stage.fit_ok: true` and `converged: true`.
- HTML: manual browser smoke (open file; click each tab; check console for errors; verify badge mount populates). No automated Playwright test in this round.

## 8. Pre-push gates

- Engine tests: 35 / 35 passing.
- Sentinel BLOCK = 0 on all new/modified files.
- AACT cross-check: **N/A** — GL-1992 cohort studies are observational, not registered on CT.gov. The repo's AACT gate (`scripts/aact_cross_check_v2.py`) is for interventional-trial reviews and does not apply.
- PMID verification: all 5 trial PMIDs (3658177, 3574409, 3375247, 3358415, 1888691) plus the methodology paper (1626547) verified resolvable on PubMed during implementation (round-1B P0 task).
- HTML manual smoke test: each tab renders; badge populates; no console errors in Chrome.

## 9. Hardening cadence

Round 1B is the P0 round for the flagship. Subsequent rounds:
- Round 1B-1 (P1): code review fixes from any review the user dispatches.
- Round 1B-2 (P2): cross-pack badge UX consistency with the DTA flagship (matches the round-2 step from prior packs).

## 10. Out-of-scope (Round 1B)

- SGLT2i flagship — Round 2 of the pack, requires per-arm dose data sourcing (likely from EMPA-REG, CANVAS, SOLOIST, Wilding 2009).
- AACT cross-check integration — N/A for GL-1992 (observational).
- F-1 (zero-cell continuity correction) — doesn't bite GL-1992; deferred to Round 2.
- F-4 (`shutil.which` for Rscript path) — doesn't affect HTML; deferred to Round 2.
- Full multivariate REML in fitRCS — P2 hardening (separate round).
- Q-profile τ² CI in fitLinear — P2 hardening.
- Automated Playwright browser test — Round 1B-2 candidate.

## 11. Resolved decisions (2026-05-12 brainstorm)

| Question | Decision |
|---|---|
| Flagship topic | GL-1992 alcohol-breast-cancer (the engine's R-validated canonical dataset) |
| Original SGLT2i plan | Deferred to Round 2 (per-arm dose data sourcing required) |
| Tab structure | 4 tabs: Linear, RCS, One-stage, R-parity |
| Engine P1 fixes scope | F-2 + F-3 (the two that affect display); F-1 + F-4 deferred |
| One-stage source | Add `lme4::glmer` Poisson + offset to R script |
| HTML filename | `ALCOHOL_BC_DOSE_RESP_REVIEW.html` |
| Commit split | F-2 and F-3 as separate commits BEFORE HTML work (cleaner history) |
| AACT gate | N/A (observational data; AACT is for interventional trials) |
