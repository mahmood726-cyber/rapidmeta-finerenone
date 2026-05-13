# Dose-Response Pack — Round 2A Design (SGLT2i Flagship + Engine Continuous Extension)

**Status:** v0.1 spec (2026-05-13).

**Depends on:** Round 1B merged at `2e96489a` on main (engine v0.1 with F-2/F-3/fit_ok propagation, R validator triplet with glmer one-stage, ALCOHOL_BC_DOSE_RESP_REVIEW.html flagship, vendor/r-validation-doseresp.js badge).

**Series:** Round 2A of pack #4. Round 1A shipped the engine + GL-1992 validation; Round 1B shipped the GL-1992 teaching flagship. Round 2A ships the originally-spec'd SGLT2i flagship + the engine continuous-outcome extension required for the primary HbA1c outcome.

---

## 1. Purpose

Demonstrate the dose-response engine on a real-world clinical exposure-response question: SGLT2 inhibitor dose vs glycemic and cardiovascular outcomes. SGLT2i CVOTs are overwhelmingly single-dose trials, so the credible multi-dose subset is small:

- **EMPA-REG OUTCOME** (Zinman 2015, PMID 26378978): empagliflozin 10 mg vs 25 mg vs placebo, ~7,000 patients
- **CANVAS Program** (Neal 2017, PMID 28605608): canagliflozin 100 mg vs 300 mg vs placebo, ~10,000 patients
- **SOLOIST-WHF** (Bhatt 2021, PMID 33196306): sotagliflozin 200 mg vs 400 mg vs placebo, ~1,200 HF patients
- **Wilding 2009 Phase 2 dose-ranging** (PMID 19196325): dapagliflozin 2.5 / 5 / 10 / 20 / 50 mg vs placebo, 12-week, ~390 patients (no CVD outcomes)

Pooled-class fixture with raw mg doses (class-equivalence assumption implicit and documented in the HTML methods disclosure). Primary outcome HbA1c reduction (continuous, all 4 trials, ~11 dose-arm data points). Secondary outcome hospitalization for HF (binary, 3 trials, exercises the F-1 zero-cell continuity correction because SOLOIST low-dose arm has zero hHF events in some strata).

Engine extension required: `fitLinear`/`fitRCS` are binary-only in v0.1 (line 422 hardcodes `Math.log(pi/p0)`); continuous-outcome branch must be added. F-1 zero-cell continuity correction must also land (P1 deferral from Round 1A → Round 1B, now blocking SGLT2i hHF).

## 2. Inputs and outputs

**Inputs:**
- `tests/dose_response_fixtures/sglt2i_hba1c.json` — NEW; 4 trials with `(dose, mean, sd, n)` arms, continuous outcome (HbA1c change from baseline)
- `tests/dose_response_fixtures/sglt2i_hhf.json` — NEW; 3 trials with `(dose, events, n)` arms, binary outcome
- `outputs/r_validation/doseresp/sglt2i_hba1c.json` — R-precomputed (dosresmeta MD + lme4 lmer one-stage)
- `outputs/r_validation/doseresp/sglt2i_hhf.json` — R-precomputed (dosresmeta IR + lme4 glmer one-stage)

**Outputs:**
- `SGLT2I_DOSE_RESP_REVIEW.html` — the 5-tab flagship
- Updated `rapidmeta-dose-response-engine-v1.js` (v0.2.0) with continuous-outcome branch + F-1
- Updated `scripts/r_validate_doseresp.R` with continuous-mode dispatch
- Updated `scripts/r_validate_doseresp.py` accepting both fixture names

## 3. Engine extensions

### 3.1 Continuous-outcome branch in fitLinear

Engine dispatches at pool entry on the fixture's outcome type. `validate()` enforces that all trials in the pool share the same outcome type (rejects mixed-mode within a single fixture); fitLinear/fitRCS then dispatch once based on the first non-reference arm of the first trial:

```js
// At fitLinear entry, after validate():
var firstArm = trials[0].arms.find(function (a) { return !a.is_reference; });
var outcomeType = (isFinite(firstArm.mean) && isFinite(firstArm.sd)) ? 'continuous' : 'binary';
// validate() has already rejected mixed-mode trials, so all per-trial loops below
// can rely on this single outcomeType for the entire pool.
```

`validate()` adds a new rule: enumerate the inferred outcome type per non-reference arm across all trials; if more than one distinct type is found, push an issue `'mixed outcome types in pool — one fixture = one outcome type'`.

**For continuous (mean+sd arms):**
- `y = mean_i − mean_ref` per non-reference arm (simple difference of changes from baseline)
- `se² per arm = sd_i² / n_i + sd_ref² / n_ref` (delta-method variance of the difference)
- Per-trial covariance `S` is **diagonal** with `se²` on the diagonal (NO shared-denominator GL correction — continuous outcomes don't share a numerator/denominator the way binary RR does)
- WLS slope: `β_i = (x' S⁻¹ x)⁻¹ x' S⁻¹ y` — same formula as binary, just with the diagonal-S input
- Rest of pooling (PM τ², HKSJ floor, PI t_{k-1}) is identical

**Backward compatibility:** binary path unchanged. The `if (outcomeType === 'continuous') { ... } else { ... existing binary block ... }` branch.

### 3.2 Continuous-outcome branch in fitRCS

Same dispatch as fitLinear. The multivariate-RE pool of spline coefs works identically — only the per-study (X, y, S) construction differs. Diagonal-PM τ² approximation continues (documented Round 1B design tradeoff; deferred to Round 2B).

### 3.3 F-1 zero-cell continuity correction

In the per-trial loop of `fitLinear` and `fitRCS`, **before** computing `y` for the binary path:

```js
// F-1: conditional +0.5 continuity correction. ONLY applies if >=1 cell is zero
// across the reference + non-reference arms of this trial. Per advanced-stats.md:
// unconditional +0.5 biases OR -> 1; conditional is the consensus correction.
var hasZeroCell = (ref.events === 0) ||
  contrasts.some(function (a) { return a.events === 0; });
if (hasZeroCell) {
  refE = ref.events + 0.5;
  refN = ref.n + 1.0;  // matched correction to keep p_0 estimable
  contrasts.forEach(function (a) {
    a._adjEvents = a.events + 0.5;
    a._adjN = a.n + 1.0;
  });
} else {
  refE = ref.events; refN = ref.n;
  contrasts.forEach(function (a) {
    a._adjEvents = a.events; a._adjN = a.n;
  });
}
// Then use refE/refN/_adjEvents/_adjN throughout the y and S calculations.
```

**Tests:**
- `fitLinear handles continuous-outcome fixture (sglt2i_hba1c) and matches dosresmeta MD pool` (parity test on the new R output)
- `fitLinear with zero-event arm applies +0.5 correction and does not produce NaN` (regression test on a synthetic fixture)
- `fitLinear without zero cells does NOT apply correction (identity output preserved)`
- Engine test count grows from 37 to ~42.

### 3.4 Engine version bump

Bump `engine_version` from `'rapidmeta-dose-response-engine-v1@0.1.0'` to `'rapidmeta-dose-response-engine-v1@0.2.0'`. Document in source header.

## 4. R script extensions

`scripts/r_validate_doseresp.R` already handles binary (IR/Poisson) data. Add continuous-mode dispatch:

```r
# Detect continuous vs binary from the first arm shape
is_continuous <- !is.null(trials[[1]]$arms[[1]]$mean) && !is.null(trials[[1]]$arms[[1]]$sd)

if (is_continuous) {
  # Flatten to data.frame with mean, sd columns
  ...
  fit_lin <- dosresmeta(formula = mean ~ dose, type = "md", sd = sd, n = n,
                         data = df, id = studlab, method = "reml")
  ...
  # One-stage: lme4::lmer with weights
  fit_os <- lmer(mean ~ dose + (1 | studlab), data = df, weights = 1/(sd^2/n))
  # Extract coef, SE, CI, random_effects_var same as binary path
}
```

Continue dose-scaling for glmer/lmer convergence. The `dose_scale_sd` audit-trail field continues to be persisted.

## 5. Fixtures

### 5.1 `tests/dose_response_fixtures/sglt2i_hba1c.json`

```json
{
  "fixture_name": "sglt2i_hba1c",
  "source": "Pooled SGLT2i dose-response on HbA1c reduction; class-equivalence implicit; 4 trials",
  "outcome": "hba1c_reduction_percent",
  "outcome_type": "continuous",
  "dose_unit": "mg_per_day",
  "class_equivalence_caveat": "Raw mg doses are not pharmacologically equivalent across drugs (empa, dapa, cana, sota). Cross-drug pooling assumes equipotent dose-response on the per-mg scale; this is methodologically debatable.",
  "trials": [
    { "studlab": "EMPA-REG OUTCOME 2015 (empagliflozin)", "pmid": "26378978", "drug": "empagliflozin",
      "arms": [
        { "dose": 0,  "mean": <placebo HbA1c change>, "sd": <>, "n": <>, "is_reference": true },
        { "dose": 10, "mean": <empa10 HbA1c change>, "sd": <>, "n": <>, "is_reference": false },
        { "dose": 25, "mean": <empa25 HbA1c change>, "sd": <>, "n": <>, "is_reference": false }
      ]
    },
    { "studlab": "CANVAS 2017 (canagliflozin)", "pmid": "28605608", "drug": "canagliflozin",
      "arms": [ ... 3 arms ... ]
    },
    { "studlab": "SOLOIST-WHF 2021 (sotagliflozin)", "pmid": "33196306", "drug": "sotagliflozin",
      "arms": [ ... 3 arms ... ]
    },
    { "studlab": "Wilding 2009 (dapagliflozin Phase 2)", "pmid": "19196325", "drug": "dapagliflozin",
      "arms": [
        { "dose": 0,    "mean": <>, "sd": <>, "n": <>, "is_reference": true },
        { "dose": 2.5,  "mean": <>, "sd": <>, "n": <>, "is_reference": false },
        { "dose": 5,    "mean": <>, "sd": <>, "n": <>, "is_reference": false },
        { "dose": 10,   "mean": <>, "sd": <>, "n": <>, "is_reference": false },
        { "dose": 20,   "mean": <>, "sd": <>, "n": <>, "is_reference": false },
        { "dose": 50,   "mean": <>, "sd": <>, "n": <>, "is_reference": false }
      ]
    }
  ]
}
```

**Data sourcing:** exact values come from each trial's primary publication. Implementation phase will extract via PubMed full-text + supplementary appendices. PMID-verification gate per repo convention.

### 5.2 `tests/dose_response_fixtures/sglt2i_hhf.json`

3 trials × 3 arms, binary (events+n hHF). SOLOIST 200mg arm has zero hHF events in some strata — triggers F-1 conditional continuity correction.

```json
{
  "fixture_name": "sglt2i_hhf",
  "outcome": "hospitalization_for_heart_failure",
  "outcome_type": "binary",
  "trials": [
    { "studlab": "EMPA-REG OUTCOME 2015", "pmid": "26378978", "drug": "empagliflozin",
      "arms": [
        { "dose": 0, "events": <pbo_hhf>, "n": <pbo_n>, "is_reference": true },
        { "dose": 10, "events": <empa10_hhf>, "n": <empa10_n>, "is_reference": false },
        { "dose": 25, "events": <empa25_hhf>, "n": <empa25_n>, "is_reference": false }
      ]
    },
    { "studlab": "CANVAS 2017", ... }, 
    { "studlab": "SOLOIST-WHF 2021", ... }
  ]
}
```

## 6. HTML structure — `SGLT2I_DOSE_RESP_REVIEW.html`

Mirrors `ALCOHOL_BC_DOSE_RESP_REVIEW.html` shape from Round 1B (uses same `<style>` inline, same `showTab()` with ARIA, same `<main>` landmark, same `aria-live` regions). 5 tabs:

| Tab | Content |
|---|---|
| **1. HbA1c — Linear** | Primary outcome KPIs (slope log-units per mg, RR per 10mg back-transform unclear for continuous — instead show MD per 10mg), forest, dose-response curve with t_{k-1} CI |
| **2. HbA1c — RCS** | 3-knot RCS curve, Wald non-linearity p (diagonal-PM v0.1 — same amber note as GL-1992), spline coefs |
| **3. HbA1c — One-stage** | R-precomputed lme4 lmer output: coef_dose, SE, CI, random_effects_var, dose_scale_sd (per Round 1B audit-trail convention) |
| **4. hHF — secondary** | Single-pane: linear pool on binary hHF, k=3 forest, F-1 zero-cell badge (visible when correction fires), coverage_warning |
| **5. R-parity badge** | Mounts `vendor/r-validation-doseresp.js` (existing badge from Round 1B). Two badge instances: one for HbA1c result, one for hHF result. |

### 6.1 Header furniture

Same as ALCOHOL_BC_DOSE_RESP_REVIEW.html: title, subtitle, engine version, generation date, methodology disclosure (collapsible), per-trial summary table (collapsible).

**Critical methods disclosure** (in the collapsible):

> **Class-equivalence assumption:** This pool combines 4 SGLT2i trials at raw mg doses across 4 different drugs (empagliflozin, canagliflozin, sotagliflozin, dapagliflozin). The dose axis is therefore drug-dependent; 10 mg means very different things across drugs. The pool implicitly assumes equipotent dose-response on the per-mg scale, which is methodologically debatable. A %-of-max-dose harmonization or per-drug separate analysis would each be defensible alternatives; this pack chose raw mg for pedagogical simplicity and to match the engine's input shape.

> **Limited evidence base:** SGLT2i CVOTs are overwhelmingly single-dose; only 4 trials in this pool report within-trial multi-dose data. k = 4 (HbA1c) and k = 3 (hHF) both trigger the engine's `coverage_warning: k < 10` flag.

### 6.2 Footer

GL-1992-style citation for each trial, links to spec + plan + Round 2A follow-ups doc (created at round close).

## 7. R-parity badge thresholds

Reuse the thresholds from Round 1B for engine vs R comparison. For the **continuous outcome** path, R `dosresmeta(type="md")` returns coefficients on the same scale as the engine's continuous-mode output, so the same |Δ| < 0.01 threshold applies.

Non-linearity Wald p continues always-amber per the documented diagonal-PM design.

## 8. Tests

Engine: 37 → ~42 (continuous-mode tests + F-1 tests). Categories:
- `fitLinear continuous-mode on sglt2i_hba1c matches R dosresmeta MD pool to |Δ| < 0.01`
- `fitLinear binary with zero-event arm triggers F-1 and returns finite (no NaN)`
- `fitLinear binary without zero cells does NOT apply F-1 (identity preserved)`
- `fitRCS continuous-mode on sglt2i_hba1c returns finite spline coefs`
- `validate accepts both continuous and binary mixed across trials in a single fixture` (negative test: should REJECT mixed-mode within a single pool? — design decision: reject; one fixture = one outcome type)

Plus carry-over from Round 1B follow-up F-5: validate-mismatched-outcome-type, validate-two-arm-no-ref, fitLinear-k=2-HKSJ-floor-fires. Total target ≥40.

## 9. Pre-push gates

- `python scripts/r_validate_doseresp.py --review sglt2i_hba1c` returns OK with continuous output
- `python scripts/r_validate_doseresp.py --review sglt2i_hhf` returns OK with binary output
- `python scripts/aact_cross_check_v2.py --review SGLT2I_DOSE_RESP_REVIEW` returns OK (per the canonical repo gate)
- Sentinel BLOCK = 0 on touched files
- All PMIDs (26378978, 28605608, 33196306, 19196325) verified resolvable on PubMed
- Engine tests ~42/42 passing

## 10. Hardening cadence (5 rounds expected)

- **P0**: scaffold engine extension + F-1 + R script + fixtures + HTML + initial commits. ~15-20 commits.
- **P1**: multi-persona code review fixes (engine math, security, UX a11y, domain accuracy, software engineering).
- **P2**: parity tightening with R; address any non-linearity-p divergence beyond the documented design tradeoff.
- **Nits**: docs, citation accuracy, plain-English summary polish.
- **Round-2 convergence**: ensure SGLT2i flagship and Alcohol-BC flagship share badge UX patterns; both reference the same R-validator triplet.

## 11. Out-of-scope (Round 2A)

- **Full multivariate REML for fitRCS** — Round 2B (P2 hardening). SGLT2i ships with same diagonal-PM v0.1 as GL-1992.
- **Q-profile τ² CI for fitLinear** — Round 2B.
- **HKSJ-multivariate + t_{k-1} for fitRCS** — Round 2B.
- **Automated Playwright browser test** — Round 2C.
- **P2-13 API forward-reference structural refactor** — Round 2B.
- **Cross-drug equivalence harmonization (%-of-max-dose)** — alternative analysis, not v0.1.
- **Per-drug separate flagships** — alternative analysis, not v0.1.
- **Adding more SGLT2i outcomes** (MACE, CV death, eGFR slope, hyperkalemia) — sparse multi-dose data; defer.

## 12. Resolved decisions (2026-05-13 brainstorm)

| Question | Decision |
|---|---|
| Sub-round to brainstorm first | Round 2A (SGLT2i flagship) ahead of 2B (engine P2) and 2C (infra) |
| Fixture framing | Pooled class fixture with raw mg doses (class-equivalence implicit, disclosed in HTML) |
| Outcomes | Primary HbA1c (continuous, k=4) + secondary hHF (binary, k=3) |
| Engine continuous-outcome extension | Required; part of Round 2A scope (not split to a pre-round) |
| F-1 zero-cell continuity correction | Lands in Round 2A (becomes blocking for hHF) |
| Spec/plan paths | `docs/superpowers/specs/2026-05-13-dose-response-round-2a-design.md` + matching plan path |
| Engine version bump | v0.1.0 → v0.2.0 (continuous-outcome support is a real semver-minor addition) |
