# E156 Methods Note draft — Diagonal-PM → full multivariate REML

**Status:** draft for E156 workbook submission. NOT YET added to `C:/E156/rewrite-workbook.txt` — the workbook numbering / denominator convention is sensitive (see workbook header). Mahmood (or the student rewriter) decides the slot and ordinal.

**Authorship rule (per workbook):** MA must be middle-author only (data curation, software, methodology, supervision-of-tooling). Student rewriter is first author; faculty supervisor is last/senior author.

**Target journal:** ◆ Synthēsis (Methods Note section, 400-word ceiling).

**Format:** Exactly 7 sentences, ≤ 156 words, single paragraph. S1=Question, S2=Dataset, S3=Method, S4=Result, S5=Robustness, S6=Interpretation, S7=Boundary.

---

## Title (draft)

Diagonal-PM τ² approximation flips the qualitative RCS non-linearity verdict in two-stage dose-response meta-analysis: a three-cohort engine-vs-R audit.

## Body (135 words, 7 sentences)

Does diagonal-PM-per-dimension τ² approximation distort the Wald non-linearity p-value in restricted-cubic-spline dose-response meta-analysis versus full multivariate REML? Three published dose-response cohorts were re-analysed: alcohol/breast-cancer (Greenland-Longnecker 1992, k=8), tirzepatide T2D SURPASS (k=5), and SGLT2i HbA1c (k=3). Full multivariate REML maximises the log-likelihood over Cholesky parameters of the τ² matrix via Nelder-Mead simplex, validated against R mixmeta. Diagonal-PM produced non-linearity p ≈ 0.05 on alcohol/breast-cancer; full REML matched R at 0.7035 vs 0.704 (|Δ| = 0.0006), flipping the qualitative verdict from significant to no-evidence-of-non-linearity. The R-match replicated on tirzepatide (engine 0.0346 vs R 0.0364, |Δ| = 0.0018) and SGLT2i (engine 0.227 vs R 0.229, |Δ| = 0.002). Diagonal approximations can flip RCS inferential verdicts because off-diagonal between-study covariance carries the linear/non-linear correlation. Findings extend to two-stage IPD pools, both continuous and binary; not to one-stage hierarchical fits.

## Word count check

| Sentence | Role | Words |
|---|---|---|
| S1 | Question | 17 |
| S2 | Dataset | 18 |
| S3 | Method | 20 |
| S4 | Result | 27 |
| S5 | Robustness | 23 |
| S6 | Interpretation | 15 |
| S7 | Boundary | 15 |
| **Total** | | **135** |

Target: ≤ 156 words (E156 ceiling). Within budget (21-word headroom).

## Primary estimand

Wald non-linearity p (chi² on the (Kp − 1)-dim non-linear submatrix of the pooled spline-coef covariance, computed under full multivariate REML).

## Evidence base / code linkage

- Engine: `rapidmeta-dose-response-engine-v1.js@0.3.0` (commit `2b963653` on `main`, PR #246).
- Validation harness: `scripts/r_validate_doseresp.py` + `scripts/r_validate_doseresp.R` (R mixmeta + dosresmeta + lme4 against jsonlite at `digits=8`).
- Fixtures: `tests/dose_response_fixtures/{gl1992_alcohol_bc,tirzepatide_t2d_surpass,sglt2i_hba1c}.json`.
- Live flagships:
  - https://github.com/mahmood726-cyber/rapidmeta-finerenone/blob/main/ALCOHOL_BC_DOSE_RESP_REVIEW.html
  - https://github.com/mahmood726-cyber/rapidmeta-finerenone/blob/main/SGLT2I_DOSE_RESP_REVIEW.html
  - https://github.com/mahmood726-cyber/rapidmeta-finerenone/blob/main/TIRZEPATIDE_T2D_SURPASS_DOSE_RESP_REVIEW.html
- R-parity audit: `tests/test_flagship_field_paths.mjs` (96/96), `tests/test_flagship_playwright_smoke.py` (12/12).

## References (Vancouver, draft)

Up to 6 authors per ref then `et al.`; DOI without URL prefix.

1. Greenland S, Longnecker MP. Methods for trend estimation from summarized dose-response data, with applications to meta-analysis. Am J Epidemiol. 1992;135(11):1301-1309. doi:10.1093/oxfordjournals.aje.a116237
2. Crippa A, Discacciati A, Bottai M, Spiegelman D, Orsini N. One-stage dose-response meta-analysis for aggregated data. Stat Methods Med Res. 2019;28(5):1579-1596. doi:10.1177/0962280218773122
3. Jackson D, White IR, Riley RD. Quantifying the impact of between-study heterogeneity in multivariate meta-analyses. Stat Med. 2012;31(29):3805-3820. doi:10.1002/sim.5453
4. Viechtbauer W. Confidence intervals for the amount of heterogeneity in meta-analysis. Stat Med. 2007;26(1):37-52. doi:10.1002/sim.2514
5. Sidik K, Jonkman JN. A simple confidence interval for meta-analysis. Stat Med. 2002;21(21):3153-3159. doi:10.1002/sim.1262
6. Rosenstock J, Wysham C, Frías JP, Kaneko S, Lee CJ, Fernández Landó L, et al. Efficacy and safety of a novel dual GIP and GLP-1 receptor agonist tirzepatide in patients with type 2 diabetes (SURPASS-1): a double-blind, randomised, phase 3 trial. Lancet. 2021;398(10295):143-155. doi:10.1016/S0140-6736(21)01324-6

## Competing interests disclosure (draft, per workbook standard)

`Authors declare no competing financial or non-financial interests directly related to this work. MA acts as a methodology adviser for several open-source statistical engines including the dose-response engine described here; no royalties, consultancy fees, or equity arrangements pertain to the engine, the Finrenone repository, or the Synthēsis journal at the time of submission. The engine code, fixtures, R validation harness, and tests are all open source under MIT (see https://github.com/mahmood726-cyber/rapidmeta-finerenone).`

## AI disclosure (draft)

`Engine implementation, fixture extraction (AACT 2026-04-12), R-parity validation harness, flagship HTML scaffolding, and Playwright/Node test suites were produced by Anthropic Claude (Opus 4.7) under MA's supervision and code review. Manuscript paragraph composed by Claude from the engine logs; reviewed and finalized by [student rewriter] and [faculty supervisor].`

## Data availability

`All fixtures, R precomputed JSONs, engine source, flagship HTML, and Node/Python test suites are at https://github.com/mahmood726-cyber/rapidmeta-finerenone, MIT licensed. AACT snapshot date 2026-04-12 (publicly available at https://aact.ctti-clinicaltrials.org/snapshots).`
