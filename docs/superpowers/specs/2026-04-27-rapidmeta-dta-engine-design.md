# RapidMeta DTA Engine v1 — Design Spec

**Date:** 2026-04-27
**Author:** mahmood789 + Claude (Opus 4.7, learning mode)
**Status:** Brainstorm-locked, awaiting user review before writing-plans

## 1. Goal & non-goals

**Goal.** Add diagnostic test accuracy (DTA) capability to the RapidMeta single-file-HTML pattern. Deliver a self-contained browser-only frequentist DTA meta-analysis engine plus a single demo review (GeneXpert MTB/RIF Ultra for pulmonary TB), modelled on the existing `rapidmeta-nma-engine-v2.js` + `*_NMA_REVIEW.html` pattern in `C:\Projects\Finrenone\`.

**Non-goals (MVP).**
- Other DTA topics (mpMRI prostate, hs-cTn, AI-CADe colonoscopy, SARS-CoV-2 antigen, etc.) — clone-and-stamp later, after this engine ships and is R-validated.
- Bayesian DTA (Rutter-Gatsonis HSROC fitted directly via MCMC) — out of scope; we do post-hoc HSROC reparam from the frequentist Reitsma fit only.
- IPD or threshold-meta-analysis (mada::SROC threshold curves with study-specific thresholds).
- PROSPERO-grade systematic-review tooling (PRISMA-DTA flow, QUADAS-2 dashboard) — review HTML will display QUADAS-2 entries already in trial JSON, but not collect them.
- Live API calls from the deployed page. CT.gov and PubMed pulls happen once during the build; results are baked into the review HTML.
- Full-text PubMed extraction. Abstracts only.

## 2. Locked design choices (from brainstorming round 1)

| # | Choice | Decision |
|---|---|---|
| 1 | Continuity correction | 0.5 conditional on any zero cell, applied to all studies (matches `mada::reitsma`) |
| 2 | Random-effects estimator | REML via Fisher scoring; if k<5 OR fails to converge in 50 iters → fall back to fixed-effect bivariate, set `result.fallback = 'fe_bivariate'` |
| 3 | SROC plot | Reitsma 95% confidence ellipse + post-hoc HSROC curve, both rendered |
| 4 | CI method | Wald on logits, back-transformed; if k<10 set `result.coverage_warning = true` |
| 5 | Primary review tab content | Pooled Sens/Spec + CI, DOR, LR+/LR−, **prevalence-slider PPV/NPV** (the unique DTA hook) |

Plus four cross-cutting invariants from `advanced-stats.md`:
- ρ ∈ [−0.95, 0.95]; if Fisher scoring hits boundary, fix ρ = 0 and flag
- Spearman corr(logit Se, logit(1−Sp)) > 0.6 → set `result.threshold_effect = true`; primary tab routes to SROC-headline mode
- Per-study Sens/Spec CIs use Clopper-Pearson exact (per `lessons.md`)
- Validation tolerance |Δ| < 1e-3 against `mada::reitsma` on logit-scale point estimates

## 3. Architecture

**Approach: mirror the NMA engine pattern exactly.**

- One engine file: `rapidmeta-dta-engine-v1.js` (math + SVG renderers + slider helper, single IIFE on `window.RapidMetaDTA`)
- One review file: `GENEXPERT_ULTRA_TB_DTA_REVIEW.html` (loads engine via `<script src defer>`, embeds trial data as a JSON literal)
- One WebR validator: `webr-dta-validator.js` (mirror of existing `webr-validator.js` lazy-load pattern; loads `mada` in-browser via WASM only when user clicks "Validate with R")
- Tailwind: reuse existing `FINERENONE_REVIEW.tailwind.css`, no new CSS asset
- All localStorage keys prefixed `dta-genexpert-ultra-`; export filenames variant-specific (`genexpert_ultra_results.csv`)

### Engine API

```
window.RapidMetaDTA = {
  fit(trials, opts)          // primary entry; returns full result object
  validate(trials)           // input contract check; returns issues[]
  exportResults(fit)         // JSON for download / R-validation handoff
  // Exposed for testing:
  _bivariate(trials, opts)   // Reitsma REML via Fisher scoring
  _hsrocReparam(fit)         // post-hoc HSROC curve coords
  _sroc(fit, opts)           // ellipse + curve geometry
  _forest(trials, fit)       // paired Sens/Spec forest geometry
  _ppvNpv(fit, prevalence)   // pure function for slider
}
```

### Result object shape

```
{
  k: int,
  pooled_sens, pooled_spec,
  pooled_sens_ci_lb, pooled_sens_ci_ub,
  pooled_spec_ci_lb, pooled_spec_ci_ub,
  tau2_sens, tau2_spec, rho,
  dor, dor_ci_lb, dor_ci_ub,
  lr_pos, lr_neg,
  threshold_effect_spearman,    // numeric
  threshold_effect: bool,        // true if |spearman| > 0.6
  coverage_warning: bool,        // true if k < 10
  fallback: null | 'fe_bivariate' | 'rho_fixed_zero',
  iterations: int,
  converged: bool,
  sroc_ellipse: [[x,y], ...],   // 100-point SVG path
  hsroc_curve:  [[fpr, sens], ...],  // 100-point post-hoc HSROC
  per_study: [{studlab, sens, spec, sens_ci, spec_ci, weight}, ...]
}
```

## 4. Review HTML structure

**File:** `GENEXPERT_ULTRA_TB_DTA_REVIEW.html`

### Trial data contract (embedded JSON, superset of engine inputs)

```js
{
  test: "GeneXpert MTB/RIF Ultra",
  reference_standard: "Mycobacterial culture (LJ or MGIT)",
  target_condition: "Pulmonary tuberculosis",
  population: "Adults with presumptive PTB",
  trials: [
    {
      studlab, year, country, design,
      nctid, pmid, ref_doi,
      TP, FP, FN, TN,
      prevalence_setting, hiv_status, specimen,
      provenance,        // 'ctgov_results' | 'pub_table_via_ctgov' |
                         // 'pubmed_abstract_back_computed'
      raw_quote          // verbatim source string for back-computed rows
    },
    ...
  ]
}
```

### Tabs

1. **Summary** — pooled Sens/Spec + CI, DOR, LR+/LR−, prevalence slider → live PPV/NPV; flag badges (threshold-effect / coverage / fallback) prominently
2. **Trials** — sortable table; per-study Sens/Spec with Clopper-Pearson CIs; NCT + PubMed links
3. **Forest** — paired Sens/Spec forest (Reitsma standard), SVG, k-row layout
4. **SROC** — confidence ellipse + HSROC curve, study points sized by total N
5. **Heterogeneity** — τ²_sens, τ²_spec, ρ, I²; threshold-effect Spearman ρ; coverage-warning panel
6. **Subgroups** — filter on `hiv_status`, `prevalence_setting`, `specimen` → re-run engine on filtered subset
7. **Methods** — engine version, continuity-correction policy, GRADE-DTA notes, **"Validate pool with R (mada)" button** (lazy-loads WebR on click), build-time `r_validation_log.json` rendered as a static reference table, on-click result panel populated below the button when the user runs validation
8. **References** — Vancouver, with PubMed/DOI links

### Single-file safety invariants (per `rules.md`)

- No literal `</script>` inside template literals (use `${'<'}/script>`)
- localStorage keys all prefixed `dta-genexpert-ultra-`
- Export filenames variant-specific
- No external CDN — Tailwind pre-built and inlined; engine is the only `<script src>`
- Div balance check after every edit
- No BOM, no hardcoded local paths

## 5. Data extraction (CT.gov + PubMed abstracts)

### Source 1: CT.gov via MCP `search_trials`

Filters: condition `"tuberculosis"` OR `"pulmonary tuberculosis"`; intervention `"Xpert Ultra"` OR `"MTB/RIF Ultra"` OR `"GeneXpert Ultra"`; start_date ≥ 2015-01-01; status: any. Per-trial deep-dive via `get_trial_details` to extract reference standard, 2×2 counts, specimen, HIV cohort, country, prevalence setting.

### Source 2: PubMed abstracts via MCP `search_articles`

Query: `("Xpert Ultra" OR "MTB/RIF Ultra" OR "GeneXpert Ultra") AND ("sensitivity" OR "specificity" OR "diagnostic accuracy") AND ("2015"[PDAT] : "2026"[PDAT]) AND humans[Filter]`. `get_article_metadata` for each → abstract only. **No `get_full_text_article` calls.**

### Abstract-only extraction logic

1. Regex-extract Sens/Spec percentages plus N split by reference-standard result
2. Back-compute 2×2: `TP = round(Sens% × N_pos)`, `FN = N_pos − TP`, `TN = round(Spec% × N_neg)`, `FP = N_neg − TN`
3. If any of the four cannot be derived → exclude, log `excluded_abstract_insufficient`
4. Mark provenance as `pubmed_abstract_back_computed`; store verbatim `raw_quote`

### Two-tier analysis

- **Primary** = `ctgov_results` + `pub_table_via_ctgov` only
- **Sensitivity** = primary + `pubmed_abstract_back_computed`
- Both pooled estimates shown side-by-side in Methods/Heterogeneity tab; if they diverge >5pp on Sens or Spec → flag in headline banner

### Acceptance gate

- Primary tier: k ≥ 5; if 5 ≤ k < 10 → `coverage_warning: true` + banner
- Combined: k ≥ 8
- If primary k < 5 → ship with banner; if combined k < 5 → stop, re-scope topic

### Files added to git

- `ctgov_genexpert_ultra_pack_2026-04-27.json` — raw MCP CT.gov responses
- `pubmed_genexpert_ultra_abstracts_2026-04-27.json` — raw abstracts + PMIDs
- `genexpert_ultra_extraction_audit.md` — per-trial provenance, raw quotes, exclusion reasons
- `GENEXPERT_ULTRA_TB_DTA_REVIEW.html` — final review with hardcoded trial JSON

## 6. R-validation: in-browser WebR, lazy-loaded, optional

R-validation is **optional and lazy** — it never runs at page load and never adds to the engine's hot path. It mirrors the existing `webr-validator.js` pattern that the rest of the RapidMeta portfolio uses for metafor cross-validation, swapping `metafor` for `mada`.

**File:** `webr-dta-validator.js` (new, parallel to existing `webr-validator.js`)

### User-facing behaviour

- The Methods tab shows a **"Validate pool with R (mada)"** button plus a single status line. No WebR fetch happens until clicked.
- First click: ~40 MB WebR WASM download + ~60–90 s `mada` install. Cached in service worker / IndexedDB for subsequent clicks (matches existing pattern).
- Result panel renders inline below the button: per-quantity Δ table, EXACT / CLOSE / DIFFER flag, R version + mada version + timestamp.
- No file downloads, no Rscript, no developer-machine R required at any point — anyone reading the published page can re-validate.

### Tolerances (locked, unchanged from original spec)

| Quantity | \|Δ\| tolerance | Verdict |
|---|---|---|
| Pooled logit-Sens, logit-Spec | 1e-3 | EXACT |
| Pooled Sens, Spec (back-transformed) | 1e-3 | EXACT |
| Pooled Sens/Spec 95% CI bounds | 2e-3 | EXACT |
| τ²_sens, τ²_spec | 5e-3 | EXACT |
| ρ | 1e-2 | EXACT |
| DOR (relative) | 1e-3 | EXACT |
| HSROC curve at 50 sampled FPR points (logit-Sens) | 2e-3 | EXACT |

CLOSE = within 2× tolerance; DIFFER = beyond 2×, treated as red banner.

### WebR boot sequence

```
ensureWebR()
  ├─ import(WEBR_CDN)  (https://webr.r-wasm.org/latest/webr.mjs)
  ├─ new WebR(); await webR.init();
  ├─ install.packages("mada", repos = "https://repo.r-wasm.org")
  ├─ library(mada)  (suppressPackageStartupMessages)
  └─ if mada not on r-wasm repo at install time:
       ├─ try install via "https://cran.r-project.org" CDN through webr
       └─ if still failing → status: "mada unavailable on WebR repo;
            falling back to metafor::rma.mv bivariate fit"
            (fallback uses metafor's bivariate REML for sens/spec; ρ
             estimate is approximate, tolerance row for ρ becomes CLOSE
             not EXACT — explicitly flagged in result panel)
```

### Fixtures shipped in `tests/dta_fixtures/` (unchanged)

1. `sparse.json` — k=4, triggers `fe_bivariate` fallback
2. `zero_cells.json` — k=8 with two FP=0 studies, triggers continuity correction
3. `high_threshold_effect.json` — k=10 with Spearman > 0.7, triggers SROC-headline mode
4. The actual GeneXpert Ultra dataset

### Failure response (revised for lazy/optional model)

- Engine ship is **not gated** on WebR validation passing — engine ships once the 9 JS TDD tests pass (§7) and the manual one-time WebR validation that the developer ran during build is recorded in the audit log.
- WebR validation result is recorded in `r_validation_log.json` (committed to repo, embedded in Methods tab as a static historical record) at build time. End-users clicking the button get a fresh result on demand; if their fresh result diverges from the recorded one → console warning, no page failure.
- WebR fails to boot in the user's browser (offline, blocked, unsupported) → status panel shows "WebR unavailable in this browser; engine output is still validated against the build-time R run recorded below" and renders the historical record.
- WebR boots but `mada` install fails → fall back to metafor as above; flag the ρ row as CLOSE-only.

### Build-time validation (one-time, by developer)

Before committing the review HTML, the developer:
1. Opens the review locally
2. Clicks "Validate with R" once
3. Confirms all rows EXACT (or CLOSE on ρ if metafor fallback)
4. Saves the result panel content into `r_validation_log.json`
5. Re-renders the Methods tab to embed that JSON

This is the analogue of the original "Run validate_dta_engine.R once at end of TDD" step, just done in-browser instead of via Rscript.

### Cross-Origin headers

WebR requires `Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Embedder-Policy: require-corp`. The repo already ships `coi-serviceworker.js` for the existing webr-validator pattern; the DTA review reuses it via `<script src="coi-serviceworker.js"></script>` early in `<head>`. No new infrastructure needed.

## 7. Test plan (TDD-first)

`tests/test_dta_engine.mjs` (Node-runnable, pure JS, no browser):

1. **Contract tests** — `validate(trials)` rejects missing TP/FP/FN/TN; rejects negative cells; accepts well-formed
2. **`_bivariate` against synthetic ground truth** — three published mada example datasets (Cochrane DTA Ch.10) with hand-derived expected pooled Sens/Spec to 1e-3
3. **Continuity-correction trigger** — zero-cell fixture; assert correction applied to all rows iff any zero present, not applied otherwise
4. **k<5 fallback** — `sparse.json`; assert `result.fallback === 'fe_bivariate'`, assert no Fisher-scoring iterations attempted
5. **ρ-boundary fallback** — fixture forcing ρ → 1; assert `result.fallback === 'rho_fixed_zero'`
6. **Threshold-effect detection** — `high_threshold_effect.json`; assert `result.threshold_effect === true`
7. **Coverage warning** — k=7 fixture; assert `result.coverage_warning === true`
8. **PPV/NPV slider math** — pure function `_ppvNpv(fit, p)`; assert PPV/NPV correct at p ∈ {0.01, 0.10, 0.30, 0.50}
9. **HSROC reparam roundtrip** — fit Reitsma, reparametrise to HSROC, sample 50 points; assert curve passes through summary point ±1e-3

Build-time WebR validation (per §6) runs only after all 9 JS tests pass.

## 8. Acceptance criteria for MVP ship

1. All 9 TDD tests pass
2. **Build-time WebR validation** (developer clicks button once locally): every tolerance row EXACT (or CLOSE on ρ if metafor fallback) for the GeneXpert dataset and all 3 synthetic fixtures; result captured in `r_validation_log.json`
3. CT.gov + PubMed extraction yields combined k ≥ 8 (primary k ≥ 5)
4. Review HTML structural checks pass: div balance, no literal `</script>` in JS strings, no BOM, no hardcoded local paths, no unpopulated placeholders
5. Sentinel pre-push hook: 0 BLOCK; any WARN documented in `sentinel-findings.md`
6. Prevalence slider works in headless Chrome smoke test (one screenshot at p=0.05, p=0.30)
7. **WebR validator button renders in Methods tab** + clicking it on a fresh browser successfully boots WebR + mada (or metafor fallback) and reproduces the historical record within tolerance
8. `r_validation_log.json` (build-time record) embedded in Methods tab
9. Provenance audit table embedded in Methods tab

## 9. Out of scope (explicit deferrals)

- Cloning to other DTA topics (mpMRI, hs-cTn, etc.) — separate effort after MVP ships
- E156 micro-paper (`rewrite-workbook.txt` entry) — write only after MVP is on Pages and R-validated
- GitHub Pages deploy — assumed yes after MVP ships, but not part of this spec's acceptance criteria
- INDEX.md / restart-manifest.json registry updates — handle in the ship checklist, not here
- Subgroup re-fitting on the `Subgroups` tab uses the same engine; no new math; if a subgroup has k<5 → display "insufficient evidence", do not re-fit

## 10. Risks & mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| CT.gov MCP returns <5 hits for Ultra | medium | PubMed-abstract sensitivity tier rescues; if combined < 5, re-scope per §5 acceptance gate |
| `mada` REML diverges on a subgroup → tolerance breach | low-medium | k<5 fallback to FE bivariate; ρ-boundary fallback to ρ=0; both validated separately |
| Abstract regex extraction is wrong → silent corruption (per `lessons.md` "negated-counts" lesson) | medium | Every back-computed row stores `raw_quote`; primary analysis excludes the abstract tier; sensitivity tier is clearly labeled |
| Tailwind class drift between this and other reviews | low | Reuse existing `FINERENONE_REVIEW.tailwind.css` directly, no fork |
| HSROC reparam numerical drift on flat tau² | low | Tolerance is 2e-3 not 1e-3 on HSROC; documented in §6 |
| `mada` not on r-wasm CRAN repo | medium | Fallback to metafor::rma.mv bivariate at WebR runtime; ρ row degrades to CLOSE; flagged in result panel |
| WebR ~40 MB first-click download blocked by user network / corporate proxy | medium-low | Validator is optional; engine output stands on its own; static `r_validation_log.json` embedded in page provides build-time record even when WebR is unreachable |
| WebR validator drift between build-time record and on-demand re-run (e.g., mada version bump on r-wasm) | low | On-demand result panel shows both columns: "build-time record" vs "fresh"; mismatch triggers console warning, not page failure |
