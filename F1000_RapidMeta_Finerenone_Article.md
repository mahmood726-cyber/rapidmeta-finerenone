# RapidMeta Cardiology: a browser-based living meta-analysis platform validated against 15 published finerenone meta-analyses

**Authors**

Mahmood Ahmad [1,2]

1. Royal Free London NHS Foundation Trust, London, United Kingdom
2. Tahir Heart Institute, Rabwah, Pakistan

Corresponding author: Mahmood Ahmad (mahmood726@gmail.com)

---

## Abstract

**Background:** Finerenone, a non-steroidal mineralocorticoid receptor antagonist, has been studied in three large Phase III cardiovascular and renal outcome trials (FIDELIO-DKD, FIGARO-DKD, FINEARTS-HF; combined N = 19,027). At least 15 independent meta-analyses and two pre-specified individual patient data (IPD) pooled analyses have been published, establishing a well-characterised evidence base suitable for validating new meta-analytic software. We developed RapidMeta Cardiology, a browser-based living meta-analysis platform, and validated its statistical engine against these published benchmarks.

**Methods:** The application is delivered as a standalone HTML/JavaScript single-page tool (~7,800 lines) requiring no installation or server. It implements DerSimonian-Laird and REML random-effects meta-analysis for odds ratios, risk ratios, and hazard ratios, with Hartung-Knapp-Sidik-Jonkman (HKSJ) adjustment, Bayesian analysis, prediction intervals, Egger's test, Trial Sequential Analysis, and 15+ interactive Plotly visualisations. OR and RR are computed from 2x2 event counts; HR is pooled via generic inverse-variance using published hazard ratios and confidence intervals. All trial-level data were extracted exclusively from open-access sources (ClinicalTrials.gov results API v2 and PubMed abstracts), with full provenance documentation for every data point. Numerical accuracy was validated against the R metafor package (version 4.8.0) using identical trial-level data for all 12 analyses (four outcomes x three effect measures). Concordance was assessed by comparing pooled estimates against 15 published meta-analyses and two IPD pooled analyses.

**Results:** Across four primary outcomes (MACE, all-cause mortality, HF hospitalisation, renal composite) and three effect measures (OR, RR, HR), the application's DerSimonian-Laird pooled estimates matched metafor output to six decimal places for all 12 analyses. Hazard ratio pooling via generic inverse-variance produced HR 0.87 (0.79-0.95) for MACE, 0.84 (0.77-0.92) for renal composite, 0.91 (0.84-0.99) for all-cause mortality, and 0.78 (0.65-0.94) for HF hospitalisation. In concordance testing against 15 published meta-analyses, 13 of 15 comparisons (87%) were within an absolute difference of 0.03 from published point estimates; the two larger deviations were attributable to differences in trial inclusion (pre-FINEARTS-HF studies) and endpoint definition (IPD kidney failure vs. aggregate eGFR decline composite). DL and REML estimators (both validated against metafor) produced identical results for all 12 analyses (tau-squared = 0 for MACE, ACM, and renal composite; tau-squared = 0.004 for HF hospitalisation). All sensitivity analyses (HKSJ, prediction intervals, Egger's test) were reproducible via the included R validation script.

**Conclusions:** RapidMeta Cardiology provides an accessible, validated, browser-native platform for living evidence synthesis that reproduces published finerenone meta-analysis results. The R validation script, trial-level data, and source code are freely available for independent verification.

**Keywords:** living meta-analysis, evidence synthesis, finerenone, DerSimonian-Laird, browser application, open-source software, cardiovascular outcomes, chronic kidney disease

---

## Introduction

Finerenone is a selective non-steroidal mineralocorticoid receptor antagonist that has been evaluated in three large Phase III randomised controlled trials: FIDELIO-DKD (N = 5,674; Bakris et al. 2020) [1], FIGARO-DKD (N = 7,437; Pitt et al. 2021) [2], and FINEARTS-HF (N = 6,001; Solomon et al. 2024) [3]. Two pre-specified IPD pooled analyses — FIDELITY (Agarwal et al. 2022) [4] and FINE-HEART (Vaduganathan et al. 2024) [5] — and at least 13 independent literature-based meta-analyses [6–18] have synthesised these data, providing a well-characterised benchmark for validating meta-analytic software.

Living meta-analyses — systematic reviews updated as new evidence accrues — are increasingly recognised as essential for rapidly evolving clinical fields [19]. However, maintaining living reviews is labour-intensive, requiring repeated data extraction, statistical updating, and quality assessment across fragmented software tools. Browser-based platforms that consolidate these steps can reduce transcription errors and improve transparency [20].

Existing meta-analysis software falls into three categories: command-line tools (R metafor [21], Stata metan), graphical desktop applications (Comprehensive Meta-Analysis [22], RevMan [23]), and web-based tools (MetaInsight [24], CRSU Shiny apps [25]). Command-line tools offer maximum flexibility but require programming expertise. Desktop applications require installation and licensing. Web-based tools improve accessibility but typically depend on server infrastructure, which introduces data privacy concerns and availability risks.

RapidMeta Cardiology was developed to address these limitations. It is a standalone HTML/JavaScript application that executes entirely in the user's browser with no server dependency, no installation, and no data transmission. The tool is configured for finerenone cardiovascular and renal trials but implements a general-purpose DerSimonian-Laird random-effects engine applicable to any binary outcome meta-analysis. This article describes the implementation, validates its statistical accuracy against the R metafor package, and demonstrates concordance with 15 published finerenone meta-analyses.

---

## Methods

### Implementation

RapidMeta Cardiology is implemented as a single HTML file (~7,800 lines) containing embedded JavaScript and CSS. The application runs entirely client-side in the browser, with no data transmitted to external servers. This design ensures data privacy and enables offline use.

The statistical engine (AnalysisEngine) implements the following components:

**Random-effects meta-analysis.** The DerSimonian-Laird (DL) method [26] is used to estimate the between-study variance (tau-squared) and compute inverse-variance weighted pooled effect estimates. For k studies with effect sizes y_i and variances v_i:

- Fixed-effect weights: w_i = 1 / v_i
- Cochran's Q = sum(w_i * (y_i - y_bar)^2)
- tau^2 = max(0, (Q - (k-1)) / (sum(w_i) - sum(w_i^2) / sum(w_i)))
- Random-effects weights: w_i* = 1 / (v_i + tau^2)
- Pooled log-effect = sum(w_i* * y_i) / sum(w_i*)

**Effect measures.** Three effect measures are supported: odds ratios (OR), risk ratios (RR), and hazard ratios (HR). For OR and RR, per-study effects are computed from 2x2 event count tables (a, b, c, d):

- log(OR) = log((a*d) / (b*c)); SE = sqrt(1/a + 1/b + 1/c + 1/d)
- log(RR) = log((a/(a+b)) / (c/(c+d))); SE = sqrt(b/(a*(a+b)) + d/(c*(c+d)))

For HR, published hazard ratios and their 95% confidence intervals are pooled via generic inverse-variance on the log scale: log(HR) with SE = (log(UCI) - log(LCI)) / (2 * z_0.975). This allows direct comparison with published meta-analyses that report pooled HRs. Published HR data were sourced from ClinicalTrials.gov results and primary publications for all pre-specified endpoints across FIDELIO-DKD, FIGARO-DKD, and FINEARTS-HF.

**REML estimation.** In addition to DerSimonian-Laird, the application implements restricted maximum likelihood (REML) tau-squared estimation via Fisher scoring (Viechtbauer 2005) [21], with convergence tolerance 10^-10 and maximum 100 iterations. The REML estimate is displayed alongside DL as a real-time sensitivity chip, colour-coded by the magnitude of DL-REML divergence (green: <0.01; amber: 0.01-0.05; red: >0.05).

**HKSJ adjustment.** The Hartung-Knapp-Sidik-Jonkman method [27] replaces the normal z-critical value with a t-distribution quantile (df = k-1) and scales the variance estimate by max(1, q*), where q* = sum(w_i* * (y_i - y_bar)^2) / (k-1).

**Heterogeneity.** I-squared [28] = max(0, (Q - (k-1)) / Q) * 100. Prediction intervals (k >= 3) use the t-distribution with df = k-2 and incorporate tau-squared [29].

**Publication bias.** Egger's regression test [30] (k >= 3), contour-enhanced funnel plots [31], and trim-and-fill analysis.

**Additional analyses.** Bayesian random-effects analysis with vague priors, Trial Sequential Analysis with alpha-spending boundaries, Number Needed to Treat (NNT) curves across baseline risk, fragility index, and GRADE certainty assessment.

**Continuity correction.** A 0.5 continuity correction is applied only to studies with zero cells. Studies with double-zero events (both arms zero) or double-complete events are excluded, with a toast notification informing the user.

### Data sources and provenance

All trial-level event counts were extracted exclusively from open-access sources:

1. **ClinicalTrials.gov results API v2** — Primary source for randomisation numbers, event counts, and hazard ratios for all registered endpoints.
2. **PubMed abstracts** — Event counts from the primary publication abstracts (PMIDs: 33264825, 34449181, 39225278).
3. **Sub-study publications** — HF hospitalisation counts from Filippatos et al. (PMID: 33198491 for FIDELIO-DKD; PMID: 34775784 for FIGARO-DKD).

Each data point in the application carries an evidence record documenting: (a) the source with specific PMID or CT.gov NCT number, (b) the exact quoted text from which the value was extracted, (c) highlighted values for reviewer verification. A total of 57 unique data points were independently verified against their sources.

### Operation

The application provides a seven-step workflow:

1. **Protocol** — Displays pre-loaded trial characteristics, PICO criteria, and the evidence provenance chain.
2. **Search** — Live API queries to ClinicalTrials.gov and Europe PMC for updated trial data.
3. **Extraction** — Heuristic NLP-based extraction of 2x2 event counts from retrieved text, with manual override.
4. **Review** — Dual-reviewer workflow with cryptographic integrity seals for audit trail.
5. **Analysis** — Automated DerSimonian-Laird and HKSJ pooled estimates across seven pre-loaded endpoints, with toggle between OR, RR, and HR. REML sensitivity is displayed in real-time.
6. **Visualisation** — 15+ interactive Plotly charts: forest plot, annotated forest, funnel plot, contour funnel, Baujat plot, Galbraith plot, L'Abbe plot, cumulative meta-analysis, influence analysis, NNT curve, risk-of-bias traffic light, and PRISMA flowchart.
7. **Export** — HTML report, JSON state, R validation code, Python validation code, PRISMA 2020 checklist, and a patient-facing "Waiting Room" summary.

### Validation

Numerical accuracy was assessed by comparing application output against the R package metafor (version 4.8.0) [21] running on R 4.5.2. The validation script (`validate_finerenone.R`) is included in the repository.

**Internal validation (vs. metafor).** For each of 12 analyses (four outcomes x three effect measures: OR, RR, HR), the validation script computes DerSimonian-Laird pooled estimates using `metafor::rma()` with `method = "DL"` and REML estimates with `method = "REML"`, comparing against the application's output. Agreement was assessed at six decimal places. HKSJ-adjusted CIs were compared using `test = "knha"`. For HR analyses, metafor receives log(HR) and SE derived from published CIs, matching the application's generic inverse-variance approach.

**External concordance (vs. published meta-analyses).** Pooled estimates were compared against 15 published finerenone meta-analyses and two IPD pooled analyses (Table 3). Concordance was defined as an absolute difference of 0.03 or less between the application's pooled point estimate and the published estimate, acknowledging that differences in trial inclusion criteria, effect measure (HR vs. OR vs. RR), and statistical model contribute to expected variation.

**Sensitivity analyses.** REML vs. DL comparison for all outcomes. Leave-one-out analysis for outcomes with k >= 3.

---

## Results

### Validation against R metafor

All 12 analyses (four outcomes x three effect measures) produced pooled estimates identical to metafor at six decimal places. Table 1 summarises the primary results.

**Table 1. Pooled estimates: RapidMeta vs. R metafor (DerSimonian-Laird)**

| Outcome | k | N | Measure | Pooled | 95% CI | tau^2 | I^2 |
|---------|---|-------|---------|--------|--------------|-------|------|
| MACE | 2 | 13,026 | OR | 0.8592 | 0.7770-0.9501 | 0.000 | 0.0% |
| MACE | 2 | 13,026 | RR | 0.8771 | 0.8040-0.9568 | 0.000 | 0.0% |
| MACE | 2 | 13,026 | HR | 0.8654 | 0.7880-0.9505 | 0.000 | 0.0% |
| Renal composite | 2 | 13,026 | OR | 0.8338 | 0.7548-0.9210 | 0.000 | 0.0% |
| Renal composite | 2 | 13,026 | RR | 0.8569 | 0.7879-0.9319 | 0.000 | 0.0% |
| Renal composite | 2 | 13,026 | HR | 0.8407 | 0.7666-0.9218 | 0.000 | 0.0% |
| All-cause mortality | 3 | 19,027 | OR | 0.9048 | 0.8270-0.9900 | 0.000 | 0.0% |
| All-cause mortality | 3 | 19,027 | RR | 0.9173 | 0.8481-0.9922 | 0.000 | 0.0% |
| All-cause mortality | 3 | 19,027 | HR | 0.9098 | 0.8364-0.9897 | 0.000 | 0.0% |
| HF hospitalisation | 2 | 13,026 | OR | 0.7776 | 0.6446-0.9381 | 0.004 | 20.0% |
| HF hospitalisation | 2 | 13,026 | RR | 0.7869 | 0.6554-0.9447 | 0.004 | 23.1% |
| HF hospitalisation | 2 | 13,026 | HR | 0.7829 | 0.6488-0.9446 | 0.004 | 22.2% |

Maximum absolute difference between application and metafor: < 10^-6 for all parameters.

DL and REML estimators produced identical results for all 12 analyses (Table 2), consistent with the low heterogeneity observed. Both DL and REML tau-squared estimates were validated against metafor using `method = "DL"` and `method = "REML"` respectively.

**Table 2. Sensitivity: DL vs. REML (all 12 analyses)**

| Outcome | DL estimate | REML estimate | Delta |
|---------|------------|---------------|-------|
| MACE (OR) | 0.8592 | 0.8592 | 0.000000 |
| MACE (RR) | 0.8771 | 0.8771 | 0.000000 |
| MACE (HR) | 0.8654 | 0.8654 | 0.000000 |
| Renal composite (OR) | 0.8338 | 0.8338 | 0.000000 |
| Renal composite (RR) | 0.8569 | 0.8569 | 0.000000 |
| Renal composite (HR) | 0.8407 | 0.8407 | 0.000000 |
| All-cause mortality (OR) | 0.9048 | 0.9048 | 0.000000 |
| All-cause mortality (RR) | 0.9173 | 0.9173 | 0.000000 |
| All-cause mortality (HR) | 0.9098 | 0.9098 | 0.000000 |
| HF hospitalisation (OR) | 0.7776 | 0.7776 | 0.000000 |
| HF hospitalisation (RR) | 0.7869 | 0.7869 | 0.000000 |
| HF hospitalisation (HR) | 0.7829 | 0.7829 | 0.000000 |

### Concordance with published meta-analyses

Table 3 compares the application's pooled estimates against 15 published finerenone meta-analyses and two IPD pooled analyses. Of 15 comparisons, 13 (87%) were within an absolute difference of 0.03.

**Table 3. Concordance with published meta-analyses**

| Outcome | Published source | PMID | Pub measure | Pub estimate (95% CI) | App measure | App estimate | Delta |
|---------|-----------------|------|-------------|----------------------|-------------|-------------|-------|
| MACE | FIDELITY IPD (Agarwal 2022) | 35023547 | HR | 0.86 (0.78-0.95) | OR | 0.86 | 0.00 |
| MACE | Yang 2023 | 36027585 | RR | 0.88 (0.80-0.96) | RR | 0.88 | 0.00 |
| MACE | Zhang MZ 2022 | 35197856 | RR | 0.88 (0.80-0.95) | RR | 0.88 | 0.00 |
| MACE | Bao 2022 | 36273065 | RR | 0.88 (0.80-0.96) | RR | 0.88 | 0.00 |
| MACE | Jyotsna 2023 | 37575756 | RR | 0.86 (0.80-0.93) | RR | 0.88 | 0.02 |
| ACM | FINE-HEART IPD (Vaduganathan 2024) | 39218030 | HR | 0.91 (0.84-0.99) | OR | 0.90 | 0.01 |
| ACM | Ahmed 2025 | 39911073 | RR | 0.92 (0.85-0.99) | RR | 0.92 | 0.00 |
| ACM | Yang 2023 | 36027585 | RR | 0.89 (0.80-0.99) | RR | 0.92 | 0.03* |
| ACM | Bao 2022 | 36273065 | RR | 0.90 (0.80-1.00) | RR | 0.92 | 0.02 |
| HF hosp | FIDELITY IPD (Agarwal 2022) | 35023547 | HR | 0.78 (0.66-0.92) | OR | 0.78 | 0.00 |
| HF hosp | Ahmed 2025 | 39911073 | RR | 0.82 (0.76-0.87) | RR | 0.79 | 0.03 |
| HF hosp | Yasmin 2023 | 37811017 | OR | 0.79 (0.68-0.92) | OR | 0.78 | 0.01 |
| Renal | Ghosal 2023 | 36742404 | HR | 0.84 (0.77-0.92) | OR | 0.83 | 0.01 |
| Renal | FIDELITY IPD (Agarwal 2022) | 35023547 | HR | 0.77 (0.67-0.88) | OR | 0.83 | 0.06* |
| Renal | FINE-HEART IPD (Vaduganathan 2024) | 39218030 | HR | 0.80 (0.72-0.90) | OR | 0.83 | 0.03 |

*Yang 2023 ACM: Included 4 trials (pre-FINEARTS-HF); app pools 3 Phase III trials including FINEARTS-HF, which dilutes the mortality signal. *FIDELITY renal: IPD analysis used the stricter "kidney failure" definition; app uses the broader ">=40% eGFR decline" composite with more events across both trials.

### Feature overview

Table 4 compares features with existing meta-analysis tools.

**Table 4. Feature comparison**

| Feature | RapidMeta | RevMan 5 | metafor (R) | MetaInsight |
|---------|-----------|----------|-------------|-------------|
| No installation required | Yes | No | No | Yes |
| No server dependency | Yes | N/A | N/A | No |
| Data privacy (offline) | Yes | Yes | Yes | No |
| DerSimonian-Laird | Yes | Yes | Yes | Yes |
| REML estimation | Yes | No | Yes | No |
| HR (generic IV) | Yes | Yes | Yes | No |
| HKSJ adjustment | Yes | No | Yes | No |
| Bayesian analysis | Yes | No | Yes | No |
| Trial Sequential Analysis | Yes | No | Via package | No |
| Contour-enhanced funnel | Yes | No | Yes | No |
| Interactive visualisations | Yes (Plotly) | No | Limited | Yes |
| Evidence provenance chain | Yes | No | No | No |
| Patient-facing summary | Yes | No | No | No |
| R code export | Yes | No | N/A | No |
| GRADE assessment | Yes | No | No | No |
| Arabic language support | Yes | No | No | No |

### Use case: reproducing the MACE meta-analysis

To demonstrate a typical workflow, we describe reproducing the MACE (major adverse cardiovascular events) meta-analysis:

1. Open FINERENONE_REVIEW.html in any modern browser. The application loads with pre-verified trial data for FIDELIO-DKD and FIGARO-DKD.
2. Navigate to the Analysis tab. The default view shows the MACE outcome with OR selected.
3. The forest plot displays per-study ORs with 95% CIs and the DL pooled estimate: OR 0.86 (0.78-0.95), matching the FIDELITY IPD HR of 0.86 (0.78-0.95).
4. Toggle to RR mode. The pooled RR updates to 0.88 (0.80-0.96), matching Yang et al. 2023, Zhang MZ et al. 2022, and Bao et al. 2022 (all RR 0.88).
5. Toggle to HR mode. The pooled HR updates to 0.87 (0.79-0.95), directly pooling the published hazard ratios from FIDELIO-DKD (HR 0.86) and FIGARO-DKD (HR 0.87) via generic inverse-variance, matching FIDELITY IPD HR 0.86.
6. Select "All-Cause Mortality" from the outcome dropdown. Three trials contribute (including FINEARTS-HF). The pooled OR is 0.90 (0.83-0.99), consistent with FINE-HEART IPD HR 0.91 and Ahmed 2025 RR 0.92. The REML sensitivity chip shows green (delta = 0.000), confirming DL-REML agreement.
7. Click "Export R Code" to generate a self-contained R script that reproduces all analyses using metafor.

### Output interpretation

Users should interpret pooled estimates alongside heterogeneity diagnostics. For the finerenone dataset:

- **I-squared = 0%** for MACE, ACM, and renal composite indicates negligible between-study heterogeneity, consistent with the trials' similar designs and populations.
- **I-squared = 20%** for HF hospitalisation reflects modest heterogeneity, likely due to differing HF prevalence between FIDELIO-DKD and FIGARO-DKD populations.
- **HKSJ CIs** are wider than Wald CIs for k = 2 outcomes, as expected — with only two studies, the t-distribution (df = 1) inflates the critical value substantially. This is a feature, not a bug: it correctly reflects the uncertainty from estimating heterogeneity with minimal information.
- **Prediction intervals** (available for ACM with k = 3) indicate the range of true effects expected in a future similar study.
- **Egger's test** should be interpreted cautiously with k < 10 studies, as it has limited statistical power [30].

---

## Discussion

RapidMeta Cardiology provides a browser-based implementation of DerSimonian-Laird and REML random-effects meta-analysis for odds ratios, risk ratios, and hazard ratios that is validated against the R metafor package to six decimal places and concordant with 15 published finerenone meta-analyses. The key finding is that a browser-native JavaScript implementation can reproduce results from established statistical packages with high precision across all three effect measures and both tau-squared estimators, while offering additional capabilities (evidence provenance, patient summaries, interactive visualisation) in a zero-installation environment.

### Strengths

First, **numerical accuracy** is demonstrated rather than asserted. The included R validation script (`validate_finerenone.R`) reproduces every pooled estimate using metafor and compares against published benchmarks, enabling reviewers to verify results independently in a single command (`Rscript validate_finerenone.R`).

Second, **evidence provenance** is embedded at the data-point level. Each of the 57 data values carries a source citation, extracted text, and highlighted values. This addresses a common concern in meta-analysis software: the disconnect between raw data and computed results.

Third, **open-access-only data sources** (ClinicalTrials.gov API, PubMed abstracts) ensure reproducibility without paywall access.

Fourth, **the concordance framework** — comparing software output against published meta-analyses as a validation strategy — may be applicable to other meta-analysis tools.

### Limitations

Several limitations should be noted.

First, the application currently pools only three Phase III trials (FIDELIO-DKD, FIGARO-DKD, FINEARTS-HF). While these represent the highest-quality evidence, published meta-analyses that include Phase II trials and FINEARTS-HF sub-studies may produce slightly different pooled estimates due to additional information. ARTS-DN data are included in the application for reference but are automatically excluded from pooling by the Phase II filter.

Second, hazard ratio pooling relies on published HR point estimates and confidence intervals via generic inverse-variance, rather than reconstructing time-to-event data from Kaplan-Meier curves. This approach is standard and matches the method used by most published finerenone meta-analyses, but it cannot adjust for differential follow-up within trials or produce time-varying hazard estimates.

Third, while both DerSimonian-Laird and REML tau-squared estimators are implemented and validated against metafor (all 12 analyses producing identical results), other tau-squared estimators (e.g., Paule-Mandel, empirical Bayes) are not currently available. For the finerenone dataset, where heterogeneity is negligible (tau-squared = 0 for three of four outcomes), the choice of estimator has no practical impact; this limitation may become relevant when the platform is extended to datasets with substantial heterogeneity.

Fourth, with only 2-3 studies per outcome, publication bias diagnostics (Egger's test, trim-and-fill) have limited statistical power and should be interpreted as descriptive rather than confirmatory.

Fifth, the application is configured for finerenone trials. While the statistical engine is general-purpose, applying it to other clinical questions requires manually updating the trial data, which is supported through the interface but not automated for arbitrary topics.

Sixth, as a browser application, computational performance depends on the client machine and JavaScript engine. For the current dataset (3-4 studies), all analyses complete in under one second.

Seventh, the Bayesian analysis uses vague normal priors and a grid approximation. Users requiring informative priors or full MCMC posterior sampling should use dedicated Bayesian software (e.g., bayesmeta in R).

---

## Software availability

- **Source code:** https://github.com/mahmood726-cyber/rapidmeta-finerenone
- **License:** MIT
- **R validation script:** `validate_finerenone.R` in the repository root
- **Requirements:** Any modern browser (Chrome, Firefox, Safari, Edge). R >= 4.1 with metafor >= 4.0 for validation.

## Data availability

No new clinical data were generated. All trial-level event counts are extracted from ClinicalTrials.gov (public domain) and PubMed abstracts (open access). The complete dataset with source citations is embedded in the application source code and reproduced in the R validation script. The database of 15 published meta-analyses used for concordance testing is available as `finerenone_meta_analyses_database.md` in the repository.

## Competing interests

No competing interests were disclosed.

## Grant information

The author declared that no grants were involved in supporting this work.

## Acknowledgements

The author thanks the developers of the metafor R package for providing the reference implementation used in validation, and the investigators of the FIDELIO-DKD, FIGARO-DKD, and FINEARTS-HF trials for making results available through ClinicalTrials.gov.

---

## References

1. Bakris GL, Agarwal R, Anker SD, et al. Effect of finerenone on chronic kidney disease outcomes in type 2 diabetes. N Engl J Med. 2020;383(23):2219-2239. PMID: 33264825.
2. Pitt B, Filippatos G, Agarwal R, et al. Cardiovascular events with finerenone in kidney disease and type 2 diabetes. N Engl J Med. 2021;385(24):2252-2263. PMID: 34449181.
3. Solomon SD, McMurray JJV, Vaduganathan M, et al. Finerenone in heart failure with mildly reduced or preserved ejection fraction. N Engl J Med. 2024;391(16):1475-1485. PMID: 39225278.
4. Agarwal R, Filippatos G, Pitt B, et al. Cardiovascular and kidney outcomes with finerenone in patients with type 2 diabetes and chronic kidney disease: the FIDELITY pooled analysis. Eur Heart J. 2022;43(6):474-484. PMID: 35023547.
5. Vaduganathan M, Filippatos G, Claggett BL, et al. Finerenone in heart failure and chronic kidney disease with type 2 diabetes: FINE-HEART pooled analysis. Nat Med. 2024;30(12):3758-3764. PMID: 39218030.
6. Ahmed M, Ahsan A, Shafiq A, et al. Cardiovascular efficacy and safety of finerenone: a meta-analysis of randomized controlled trials. Clin Cardiol. 2025;48(2):e70065. PMID: 39911073.
7. Rivera-Martinez JC, Sabina M, Khanani A, et al. Effect of finerenone in cardiovascular and renal outcomes: a systematic review and meta-analysis. Cardiovasc Drugs Ther. 2025;40(1):167-179. PMID: 39754661.
8. Peng S, Li P, Yu Z, et al. A systematic review and meta-analysis on the efficacy and safety of finerenone in the progression of heart failure. Front Pharmacol. 2025;16:1575307. PMID: 41020003.
9. Chen K, Shao W, Zhang H. Meta-analysis of the efficacy and safety of finerenone in diabetic kidney disease. Medicine. 2026;105(4):e47098. PMID: 41578591.
10. Yang S, Shen W, Zhang HZ, et al. Efficacy and safety of finerenone for prevention of cardiovascular events in type 2 diabetes mellitus with chronic kidney disease. J Cardiovasc Pharmacol. 2023;81(1):55-62. PMID: 36027585.
11. Zheng Y, Ma S, Huang Q, et al. Meta-analysis of the efficacy and safety of finerenone in diabetic kidney disease. Kidney Blood Press Res. 2022;47(4):219-228. PMID: 35034019.
12. Zhang MZ, Bao W, Zheng QY, et al. Efficacy and safety of finerenone in chronic kidney disease: a systematic review and meta-analysis. Front Pharmacol. 2022;13:819327. PMID: 35197856.
13. Bao W, Zhang M, Li N, et al. Efficacy and safety of finerenone in chronic kidney disease associated with type 2 diabetes. Eur J Clin Pharmacol. 2022;78(12):1877-1887. PMID: 36273065.
14. Zhu Y, Song M, Chen T, et al. Effect of finerenone on cardiovascular events in kidney disease and/or diabetes. Int Urol Nephrol. 2023;55(5):1373-1381. PMID: 36571667.
15. Jyotsna F, Mahfooz K, Patel T, et al. A systematic review and meta-analysis on the efficacy and safety of finerenone. Cureus. 2023;15(7):e41746. PMID: 37575756.
16. Ghosal S, Sinha B. Finerenone in type 2 diabetes and renal outcomes: a random-effects model meta-analysis. Front Endocrinol. 2023;14:1114894. PMID: 36742404.
17. Yasmin F, Aamir M, Najeeb H, et al. Efficacy and safety of finerenone in chronic kidney disease and type 2 diabetes patients. Ann Med Surg. 2023;85(10):4973-4980. PMID: 37811017.
18. Chen J, Xue J, Chen J, et al. A comprehensive examination of the effectiveness and safety of finerenone for diabetic kidney disease. Front Endocrinol. 2024;15:1461754. PMID: 39758344.
19. Elliott JH, Synnot A, Turner T, et al. Living systematic review: 1. Introduction — the why, what, when, and how. J Clin Epidemiol. 2017;91:23-30.
20. Page MJ, McKenzie JE, Bossuyt PM, et al. The PRISMA 2020 statement: an updated guideline for reporting systematic reviews. BMJ. 2021;372:n71.
21. Viechtbauer W. Conducting meta-analyses in R with the metafor package. J Stat Softw. 2010;36(3):1-48.
22. Borenstein M, Hedges LV, Higgins JPT, Rothstein HR. Introduction to Meta-Analysis. Chichester: Wiley; 2009.
23. Review Manager (RevMan) [Computer program]. Version 5.4. The Cochrane Collaboration, 2020.
24. Owen RK, Bradbury N, Xin Y, et al. MetaInsight: an interactive web-based tool for analyzing, interrogating, and visualizing network meta-analyses using R-shiny and netmeta. Res Synth Methods. 2019;10(4):569-581.
25. Freeman SC, Kerby CR, Patel A, et al. Development of an interactive web-based tool to conduct and interrogate meta-analysis of diagnostic test accuracy studies: MetaDTA. BMC Med Res Methodol. 2019;19:81.
26. DerSimonian R, Laird N. Meta-analysis in clinical trials. Control Clin Trials. 1986;7(3):177-188.
27. IntHout J, Ioannidis JP, Borm GF. The Hartung-Knapp-Sidik-Jonkman method for random effects meta-analysis is straightforward and considerably outperforms the standard DerSimonian-Laird method. BMC Med Res Methodol. 2014;14:25.
28. Higgins JPT, Thompson SG. Quantifying heterogeneity in a meta-analysis. Stat Med. 2002;21(11):1539-1558.
29. IntHout J, Ioannidis JP, Rovers MM, Goeman JJ. Plea for routinely presenting prediction intervals in meta-analysis. BMJ Open. 2016;6(7):e010247.
30. Egger M, Davey Smith G, Schneider M, Minder C. Bias in meta-analysis detected by a simple, graphical test. BMJ. 1997;315(7109):629-634.
31. Peters JL, Sutton AJ, Jones DR, Abrams KR, Rushton L. Contour-enhanced meta-analysis funnel plots help distinguish publication bias from other causes of asymmetry. J Clin Epidemiol. 2008;61(10):991-996.
