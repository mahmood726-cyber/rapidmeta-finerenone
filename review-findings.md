# Multi-Persona Review: PR #223 — Dose-Response Pack Round 1B

### Date: 2026-05-12
### Files reviewed
- `ALCOHOL_BC_DOSE_RESP_REVIEW.html` (new flagship, 321 lines)
- `vendor/r-validation-doseresp.js` (new badge UI, 120 lines)
- `rapidmeta-dose-response-engine-v1.js` (F-2 + F-3 + fit_ok propagation)
- `tests/test_dose_response_engine.mjs` (37 tests, 4 new this round)
- `scripts/r_validate_doseresp.R` (glmer one-stage block added)
- `scripts/r_validate_doseresp.py` (wrapper)
- `outputs/r_validation/doseresp/gl1992_alcohol_bc.json`

### Summary: **8 P0, 20 P1, 14 P2** (deduplicated across 5 personas)
### Personas: Statistical Methodologist · Security Auditor · UX/Accessibility · Software Engineer · Domain Expert

---

## P0 — Critical (must fix before merge)

> **P0 status:** 8/8 FIXED in commits d744d37c + 8c1c348d. P1/P2 remain open.

- **P0-1** [FIXED] [Software Engineer]: Wrong badge JS loaded. `vendor/r-validation-badge.js` is the legacy NMA-paradigm badge (auto-bootstraps; fires fetch for `outputs/r_validation/ALCOHOL_BC_DOSE_RESP.json` derived from filename — will 404 on every load and inject a "R validation skipped" panel). The dose-response badge is `vendor/r-validation-doseresp.js`. (file `ALCOHOL_BC_DOSE_RESP_REVIEW.html` line 148)
  - Fix: remove the `<script src="vendor/r-validation-badge.js" defer></script>` line.

- **P0-2** [FIXED] [Domain Expert]: Trial-summary table column header is **"Total person-years"** but Howe 1991 is a case-control reanalysis (per GL 1992 Table 1 footnote); its `n` values are person-counts, not person-years. The implied reference-arm rate of 25.3% is biologically impossible for breast-cancer incidence — immediate credibility flag for any epidemiologist. (file `ALCOHOL_BC_DOSE_RESP_REVIEW.html` line ~169)
  - Fix: change header to `"Total n (person-years or subjects)"` + footnote.

- **P0-3** [FIXED] [Domain Expert]: Plain-English summary states "≈ 1 drink/day" for 11 g/day. US standard drink = 14 g; 11 g ≈ 1 WHO/Australian standard drink. Audience may include US-trained readers who'll interpret this as wrong. (file `ALCOHOL_BC_DOSE_RESP_REVIEW.html` line ~222)
  - Fix: replace parenthetical with `(≈ 1 standard drink by WHO convention; US standard = 14 g)` or drop the drink-equivalence framing.

- **P0-4** [FIXED] [UX/Accessibility]: Missing `<meta name="viewport">` — WCAG 1.4.10 (Reflow) violation. Mobile renders at desktop width. (file `ALCOHOL_BC_DOSE_RESP_REVIEW.html` `<head>`)
  - Fix: add `<meta name="viewport" content="width=device-width, initial-scale=1">`.

- **P0-5** [FIXED] [UX/Accessibility]: Tab widget has no ARIA tablist semantics — WCAG 4.1.2 (Name, Role, Value) failure. Screen-reader users hear "4 buttons next to a div" with no indication of a tabbed interface, no active-tab signal, no panel relationship. (file `ALCOHOL_BC_DOSE_RESP_REVIEW.html` lines 54–59 and 61–86)
  - Fix: add `role="tablist"` to `<nav>`; `role="tab"` + `aria-selected` + `aria-controls` on each `<button>`; `role="tabpanel"` + `tabindex="0"` + `aria-labelledby` on each `<section>`. Update `showTab()` to toggle `aria-selected`.

- **P0-6** [FIXED] [UX/Accessibility]: No `aria-live` regions for dynamically-injected status/errors — WCAG 4.1.3 (Status Messages). Coverage warning + fetch-failure error banners are silent for screen-reader users. (file `ALCOHOL_BC_DOSE_RESP_REVIEW.html` lines 195, 282–283, 310–313)
  - Fix: wrap `#onestage-kpis`, `#r-parity-doseresp` (or a common parent) with `aria-live="polite" aria-atomic="true"` declared in static HTML.

- **P0-7** [FIXED] [UX/Accessibility]: Coverage warning color `#d97706` on white = 2.9:1 contrast — fails WCAG 1.4.3 AA (need 4.5:1). (file `ALCOHOL_BC_DOSE_RESP_REVIEW.html` line 195)
  - Fix: darken to `#b45309` (≈ 6:1) or `#92400e` (≈ 9:1).

- **P0-8** [FIXED] [Software Engineer]: `RSCRIPT_EXE` hardcoded with no env-var/PATH fallback — diverges from the three-tier pattern (`os.environ.get → shutil.which → hardcoded`) used by every other R validator in this repo. Will fail on R upgrade (4.5.2 → 4.6.x). Listed as F-4 in Round 1B follow-ups but escalated to P0 here because it diverges from existing repo convention. (file `scripts/r_validate_doseresp.py` line 28)
  - Fix: `RSCRIPT_EXE = os.environ.get("RSCRIPT_EXE") or shutil.which("Rscript") or r"C:\Program Files\R\R-4.5.2\bin\Rscript.exe"`.

---

## P1 — Important (should fix this round or next)

- **P1-1** [Statistical Methodologist]: Knot placement diverges between JS and R. Engine `rcsKnots()` uses **unique** doses (gives [10, 20, 27]); R script uses **all arm-level rows** (gives [5, 15, 24]). Parity badge compares spline coefficients fit under different knots; happens to pass tolerance on GL-1992 but masks a real silent inconsistency. (engine line ~356; R script line ~79)
  - Fix: align — either change `rcsKnots` to accept the full (non-deduplicated) dose vector, OR change the R script to `quantile(unique(df$dose[df$dose > 0]), ...)`. Document the chosen convention.

- **P1-2** [Statistical Methodologist]: `fitRCS` has no post-loop guard on `perStudy.length`. If all per-study WLS fail (singular `XtSX`), `pmTau2([], [])` returns 0, `0/0 = NaN` propagates through pooled coefs silently. (engine line ~593–636)
  - Fix: `if (perStudy.length < 2) throw new Error('fitRCS: fewer than 2 studies survived covariance inversion');`

- **P1-3** [Statistical Methodologist]: `predict()` ignores `ci_method` field set by `fitOneStage` (which is `'z_1.96'`). If a caller passes a one-stage result, CIs are computed using `t_{k-1}` (e.g. 2.776 at k=5) — contradicts the result's own annotation. Currently latent (HTML reads CIs directly from JSON), but the function contract is misleading. (engine line ~762–768)
  - Fix: add `if (result.ci_method === 'z_1.96') { tcrit = 1.96; }` before the df/tcrit calculation.

- **P1-4** [Statistical Methodologist]: PI df convention (`k-1`, Cochrane v6.5) is documented in file header but NOT at the decision point. `advanced-stats.md` rule: "document which convention if computing locally." (engine line ~490)
  - Fix: one-line inline comment naming the convention + the IntHout/Higgins/Tudur Smith 2016 `k-2` alternative.

- **P1-5** [Security]: `e.message` from `fetch().catch()` interpolated raw into `innerHTML`. Browser-built TypeError is safe today, but the pattern is XSS-unsafe by construction. (file `ALCOHOL_BC_DOSE_RESP_REVIEW.html` lines 311–313)
  - Fix: use `textContent` or `escapeHtml(e.message)`.

- **P1-6** [Security]: Path traversal in `scripts/r_validate_doseresp.py` via `args.review` — value concatenated into `OUT_DIR / f"{args.review}.input.json"` with no validation. `--review ../../evil` would write outside `OUT_DIR`. (file `scripts/r_validate_doseresp.py` lines 38, 49, 50)
  - Fix: `if not re.fullmatch(r'[A-Za-z0-9_\-]+', args.review): sys.exit("ERROR: --review must be alphanumeric")` after `args.parse_args()`.

- **P1-7** [Security]: `vendor/r-validation-badge.js` (shared framework, **not** my badge) has unescaped innerHTML on `topic` and `data.error` / `data.method`. Partially obviated by P0-1 (removing the badge.js load) — but if any other review still uses badge.js, fix the framework. (file `vendor/r-validation-badge.js` lines 54–55, 69, 72, 134–136)
  - Fix: extract shared `escapeHtml()` into badge.js and wrap interpolations.

- **P1-8** [UX/Accessibility]: No `<main>` landmark. Screen-reader landmark navigation lands on `<nav>` only. (file `ALCOHOL_BC_DOSE_RESP_REVIEW.html` line 32)
  - Fix: wrap `<h1>` through footnote `<div>` in `<main>`.

- **P1-9** [UX/Accessibility]: No arrow-key navigation between tabs. WAI-ARIA Tabs pattern requires `ArrowLeft`/`ArrowRight` + roving tabindex. Currently all 4 buttons are in tab order; user must press Tab 4 times to pass the strip. (file `ALCOHOL_BC_DOSE_RESP_REVIEW.html` lines 54–59 + `showTab()`)
  - Fix: implement roving tabindex + arrow-key handler in `showTab()`/`keydown`.

- **P1-10** [UX/Accessibility]: Tables lack `<caption>` elements. Screen readers announce "table" with no context — 5+ tables per panel makes orientation hard. (HTML multiple lines; badge JS line 109)
  - Fix: add `<caption>` as first child of each `<table>`.

- **P1-11** [UX/Accessibility]: Numeric tables overflow at 320px viewport — WCAG 1.4.10. (HTML lines 199–207, 210–219, 241–248, 253–260)
  - Fix: add `.table-scroll { overflow-x: auto; }` wrapper class and use it around each rendered table.

- **P1-12** [UX/Accessibility]: Tab switching doesn't move focus. Keyboard user activates a tab and lands on the button, then must Tab through dozens of non-focusable KPI divs to reach content. (HTML `showTab()` line 153–158)
  - Fix: after panel becomes visible, `document.getElementById('tab-' + name).querySelector('h2')?.focus()` (add `tabindex="-1"` to each `<h2>`).

- **P1-13** [Software Engineer]: `matvec` (lowercase) is dead code in the engine — defined at line 57 but never called or exported. Round 1A cleanup was supposed to remove it; persists. (engine line 57–60)
  - Fix: delete the dead function.

- **P1-14** [Software Engineer]: R `tryCatch` blocks discard error messages (`error = function(e) NULL`). On glmer/dosresmeta failure, output JSON shows only `fit_ok: false` with zero diagnostic. (R script lines 71–76, 80–85, 109–114)
  - Fix: capture `conditionMessage(e)` into `error_msg` field in each block.

- **P1-15** [Software Engineer]: `DOMContentLoaded` handler has no guard against `window.RapidMetaDoseResp` being undefined. If engine script fails to load, `DR.engine_version` throws and all 4 tabs render blank silently. `JSON.parse` on embedded trial JSON also has no try/catch. (HTML lines 161–165)
  - Fix: early guard with visible error banner if `DR` is undefined; wrap JSON.parse in try/catch.

- **P1-16** [Software Engineer]: `forest(trials, result)` accepts `trials` but never uses it; operates entirely on `result.per_study`. Misrepresents data dependencies. (engine line 771; all 3 call sites)
  - Fix: drop `trials` from signature OR add `/* trials reserved for future per-arm weight override */` comment.

- **P1-17** [Software Engineer]: Python wrapper exit codes (2–5) undocumented in module docstring. CI consumers can't distinguish failure modes without reading source. (file `scripts/r_validate_doseresp.py` lines 1–13)
  - Fix: add `Exit codes:` section to docstring.

- **P1-18** [Domain Expert]: Howe 1991 case-control-reanalysed-as-cohort design is silently mixed with 4 true cohorts. GL 1992 documents this explicitly in Table 1 footnote; the HTML methods collapsible doesn't. (HTML line ~135 / line ~297–300)
  - Fix: add a footnote/methods sentence explaining the design difference and that the Poisson hierarchical model treats all studies uniformly per GL 1992's choice.

- **P1-19** [Domain Expert]: RE pool gives RR ≈ 1.289 per 11 g/day — ~4× the FE estimate from the source paper and ~3× modern best-evidence (Smith-Warner 1998, Allen 2009: ~7–10% per 10 g/day). Plain-English summary presents 1.289 without caveats. Teaching audience will misinterpret. (HTML line ~222)
  - Fix: append note: "this is a methodology paper's worked example, not best-evidence; modern estimates are ~7–10% per 10 g/day; high RE value reflects extreme I² (≈ 95%) driven by Howe 1991."

- **P1-20** [Domain Expert]: Dose values in fixture are GL 1992's **assigned midpoints** (per Table 1) — not category boundaries. Not documented anywhere. (fixture JSON; HTML methods collapsible)
  - Fix: add `dose_assignment_method` field to fixture; one sentence in methods.

---

## P2 — Minor (polish; queue for Round 2)

- **P2-1** [Statistical Methodologist]: `dose_scale_sd` (glmer convergence-aid factor) is in JSON but not propagated into `fitOneStage` return or displayed in HTML. (file `r_validate_doseresp.R` line 129; HTML line ~290)
- **P2-2** [Statistical Methodologist]: Wald non-linearity comment doesn't explain that the marginal-sum form is a consequence of diagonal-PM independence assumption. (engine line ~626–636)
- **P2-3** [Statistical Methodologist]: R `glmer` block lacks `tryCatch` around `vcov()`/`VarCorr()` — a post-fit failure crashes the script. (R script lines 116–138)
- **P2-4** [Security]: No `Content-Security-Policy` meta tag. (HTML `<head>`)
- **P2-5** [Security]: `vendor/r-validation-badge.js` localStorage key `'r-validation-badge-expanded'` is unnamespaced — cross-page collision risk. (badge.js line 35)
- **P2-6** [UX/Accessibility]: Inline `style="background:#fef8ec;..."` on the amber notes — won't render correctly in Windows High Contrast Mode (forced-colors strips backgrounds). (HTML line 265)
- **P2-7** [UX/Accessibility]: No explicit `:focus-visible` ring on tab buttons. (HTML `<style>`)
- **P2-8** [UX/Accessibility]: `<nav>` has no `aria-label`. (HTML line 54)
- **P2-9** [Software Engineer]: `fitOneStage(trials, opts, precomputedJson)` — `opts` is accepted but never read. (engine line 716)
- **P2-10** [Software Engineer]: Section banner order is `2 → 2b → 2a → 2c` (non-sequential). (engine lines 257, 338, 402, 525)
- **P2-11** [Software Engineer]: `allGreen` detection scans HTML strings for `rv-row-green` — fragile if CSS class renames. (badge JS line 101)
- **P2-12** [Software Engineer]: `forest()` uses raw `z=1.96` for per-study CIs while pooled CI uses `t_{k-1}` (F-2 fix). Asymmetry not commented. (engine lines 777–778)
- **P2-13** [Software Engineer]: `API` referenced inside `fit*` function bodies before it's defined — works via hoisting but is a latent footgun. (engine lines 520, 684, 737, 807 vs 811)
- **P2-14** [Domain Expert]: Fixture `outcome_type: "binary"` is clinically inaccurate for cohort person-years data — should be `"cohort_incidence_rate"` or `"ci"` (matching dosresmeta terminology). (fixture JSON line 6)
- **P2-15** [Domain Expert]: Tabs 1 vs 3 show RR 1.289 vs 1.129 — 14% point-estimate gap with no comparative explanation. Teaching opportunity missed. (HTML line ~287–300)

---

## Things multiple personas independently APPROVED (no need to re-check)

- F-2 fix correctness — predict() linear branch uses `qt(0.975, df)` with proper fallback chain (Stat + Eng)
- F-3 fix correctness — forest() reads `tau2_per_dim[0]` for RCS layer; non-tautological test (Stat + Eng)
- `escapeHtml()` in `r-validation-doseresp.js` — present and applied to both R-version strings (Security + Eng)
- `target="_blank" rel="noopener noreferrer"` on all outbound PMID links (Security + UX)
- `subprocess.run()` list form, no `shell=True` (Security)
- `<html lang="en">` present, table semantics intact, native `<button>` for tabs (UX)
- GL-1992 citation accuracy: PMID 1626547, AJE 135(11):1301-9, 1992 — verified (Domain)
- All 5 trial PMIDs verified resolvable (Domain)
- `glCovariance` formula matches GL-1992 exactly; HKSJ floor `max(1, Q/(k-1))` correctly applied (Stat)
- `rcsBasis` matches `Hmisc::rcspline.eval(norm=2, inclx=TRUE)` to 4 decimal places (Stat)

---

## False positives checked against `lessons.md` and `advanced-stats.md`

None of the findings duplicate known false-positive patterns from the agent-output-grading lessons. Specifically NOT flagged:
- DOR formula (not applicable)
- Clopper-Pearson alpha/2 (not applicable)
- HKSJ floor (verified correct)
- Continuity correction (correctly deferred to Round 2 F-1)
- ES5 `var` style in engine (intentional for browser-only constraints)
- Inline HTML/JS/CSS in flagship (required for offline-capable single-file)
