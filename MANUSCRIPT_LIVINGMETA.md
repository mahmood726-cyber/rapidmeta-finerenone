# LivingMeta: A Single-File, Browser-Based Living Meta-Analysis Engine with Integrated Trial Discovery and In-Browser R Validation

## Abstract

**Background:** Living systematic reviews require tools that integrate trial discovery, data extraction, statistical synthesis, and validation into a reproducible workflow. Existing tools either require server infrastructure, demand programming expertise, or lack real-time validation against reference R packages.

**Methods:** We developed LivingMeta, a self-contained single-file HTML application (~550 KB) that performs complete living meta-analyses entirely in the browser. The tool implements six tau-squared estimators (DL, REML, PM, HS, HE, EB), Hartung-Knapp-Sidik-Jonkman adjustment, Mantel-Haenszel and Peto fixed-effect methods, and 15+ advanced analyses including Bayesian posterior density, trial sequential analysis, Copas selection sensitivity, fragility index, NNT curves, and meta-regression. An integrated text extractor (50+ regex patterns ported from a validated Python extraction pipeline) automatically identifies effect estimates (HR, OR, RR, IRR, MD, SMD, ARD, NNT) with confidence intervals from CT.gov results and PubMed abstracts. In-browser R validation via WebR loads metafor and compares 30+ metrics against the JavaScript engine. Nine pre-configured clinical topics spanning cardiovascular, renal, metabolic, and rare disease therapeutics (45 landmark RCTs, ~200,000 patients) are included as demonstration datasets.

**Results:** LivingMeta produces pooled effect estimates within 0.01 OR units of R metafor across all six tau-squared estimators. The text extractor achieves extraction from standard journal formats (HR with 95% CI, event counts, p-values) with plausibility validation and confidence scoring. The application requires no installation, server, or internet connection after initial load, and runs on any modern browser. A 36-assertion automated test suite validates all features across all nine clinical configurations.

**Conclusions:** LivingMeta demonstrates that a complete living meta-analysis workflow — from trial discovery through certified synthesis — can be delivered as a single distributable file with gold-standard R validation, making evidence synthesis accessible to reviewers without statistical software expertise.

**Keywords:** living systematic review, meta-analysis, browser-based, WebR, text extraction, evidence synthesis, single-file application

---

## Introduction

Living systematic reviews maintain currency by incorporating new evidence as it becomes available [1]. However, the tools supporting this workflow are fragmented: trial discovery requires registry searches (ClinicalTrials.gov, PubMed), data extraction demands manual abstraction or specialized software, statistical synthesis typically relies on R or Stata, and validation requires independent replication. This multi-tool workflow creates barriers for clinical reviewers who may lack programming expertise and introduces opportunities for transcription errors between tools.

Browser-based meta-analysis tools have emerged to lower these barriers [2,3], but most either require server infrastructure, lack comprehensive statistical methods, or provide no mechanism for independent validation of results. The gap between "accessible" and "rigorous" remains wide.

We developed LivingMeta to bridge this gap: a single HTML file that integrates the complete living review workflow — protocol definition, multi-source trial discovery, dual-reviewer screening, provenance-tracked extraction, comprehensive synthesis with 20+ statistical methods, GRADE certainty assessment, and in-browser R validation — all executable offline without installation.

## Methods

### Architecture

LivingMeta is implemented as a single HTML file (~550 KB) containing embedded CSS and JavaScript. No build tools, package managers, or server infrastructure are required. The application loads two CDN dependencies (Plotly.js for visualization, Tailwind CSS for layout) and optionally loads WebR (R compiled to WebAssembly) for in-browser validation. All statistical computation occurs client-side in JavaScript.

### Statistical Engine

The synthesis engine implements inverse-variance weighted random-effects meta-analysis with six tau-squared estimators: DerSimonian-Laird (DL) [4], Restricted Maximum Likelihood (REML) via Newton-Raphson iteration [5], Paule-Mandel (PM) via binary search, Hunter-Schmidt (HS), Hedges-Olkin (HE), and Empirical Bayes (EB). The Hartung-Knapp-Sidik-Jonkman (HKSJ) adjustment [6] uses the t-distribution with k-1 degrees of freedom and implements the IQWiG modification (wider of HKSJ and Wald CI). Fixed-effect methods include inverse-variance, Mantel-Haenszel [7], and Peto [8].

Effect size calculators support log odds ratio (Woolf's method with 0.5 continuity correction), log risk ratio, and log hazard ratio (derived from published HR and CI). All critical values are computed from the user's confidence level parameter (not hardcoded).

Advanced analyses include: prediction intervals (t-distribution, df=k-2), Bayesian grid approximation with three-prior sensitivity analysis, trial sequential analysis with O'Brien-Fleming spending boundaries, Egger's regression test, Begg's rank correlation, trim-and-fill (L0 estimator with mid-rank for ties per Duval & Tweedie 2000), PET-PEESE conditional estimation, Copas selection sensitivity, fragility index (Walsh et al. 2014, fewer-event arm modification), Rosenthal and Orwin fail-safe N, NNT curves across baseline risk, leave-one-out influence diagnostics (Cook's D, hat values, DFBETAS), cumulative meta-analysis by year, sceptical p-value (Matthews 2018), and meta-regression (categorical Q-between and continuous WLS slope).

### Text Extractor

A JavaScript text extraction module (50+ regex patterns) was ported from a validated Python extraction pipeline (rct_data_extractor_v2, 83.6% accuracy on 1,290 OA PDFs). The extractor identifies hazard ratios, odds ratios, risk ratios, incidence rate ratios, mean differences, standardized mean differences, absolute risk differences, NNT/NNH, vaccine efficacy, and geometric mean ratios with their confidence intervals. Event count patterns extract 2x2 table data from "X/N vs Y/N" formats. P-values are automatically linked to the nearest preceding effect estimate.

Text normalization handles Unicode dashes, thin spaces, European decimal commas, OCR artifacts (Cl to CI correction), and 24 run-together medical term corrections (e.g., "hazardratio" to "hazard ratio"). Plausibility checks reject implausible values (HR outside 0.01-50, CI not containing the point estimate). Each extraction receives a confidence score and automation tier (AUTO_VERIFIED, SPOT_CHECK, NEEDS_REVIEW).

Effect computation formulas (OR, RR, RD, MD, SMD with Hedges' g correction) allow derivation of effect sizes from extracted raw data when published estimates are unavailable.

### In-Browser R Validation (WebR)

LivingMeta integrates WebR v0.4.4 (R compiled to WebAssembly) [9] to provide gold-standard validation. When activated, the tool installs the metafor package [10] directly in the browser and runs `rma()` with the user's selected tau-squared method and HKSJ setting. The validation compares 30+ metrics across eight categories: pooled estimate and CI, tau-squared (all six estimators), I-squared, Q-statistic, prediction interval, Mantel-Haenszel, Peto, Egger/Begg bias tests, trim-and-fill, and leave-one-out estimates. Tolerances follow established benchmarks: OR within 0.01, CI within 0.02, tau-squared within 0.001, I-squared within 1%.

A fallback base-R DerSimonian-Laird estimator provides validation when metafor installation fails.

### Clinical Configurations

Nine pre-configured clinical topics serve as demonstration datasets and validation fixtures:

| Configuration | Therapeutic Area | Trials | Patients |
|--------------|-----------------|--------|----------|
| Colchicine CVD | Anti-inflammatory cardiology | 5 | 21,268 |
| Finerenone | Non-steroidal MRA (CKD/HF) | 3 | 19,027 |
| SGLT2i Heart Failure | Gliflozins across EF spectrum | 5 | 20,947 |
| GLP-1 RA CVOTs | Incretin CVD outcomes | 10 | 87,334 |
| PCSK9 Inhibitors | Lipid-lowering ASCVD | 2 | 46,488 |
| Intensive BP Control | Blood pressure targets | 4 | 25,625 |
| Bempedoic Acid | Non-statin lipid therapy | 3 | 16,979 |
| Incretins HFpEF | GLP-1/GIP RA in obese HFpEF | 3 | 1,876 |
| ATTR-CM | Cardiac amyloidosis (3 drug classes) | 4 | 2,067 |

All trial data are sourced from published primary reports with provenance text linking each cell to its source table and publication.

### GRADE Assessment

Automated GRADE certainty of evidence assessment evaluates five domains: risk of bias (proportion of contributing trials with some/high concerns), inconsistency (I-squared threshold and prediction interval crossing null), indirectness (config-driven population/intervention mismatch detection), imprecision (CI crossing null or optimal information size not met), and publication bias (Egger test, ghost protocol enrollment ratio, trim-and-fill). Starting from HIGH certainty for RCT evidence, the tool applies domain-specific downgrade rules.

### Patient Mode

A clinician/patient toggle provides a simplified traffic-light view (green = likely beneficial, amber = uncertain, red = likely harmful) with plain language interpretation, NNT pictogram, and GRADE certainty summary, designed for shared decision-making.

### Quality Assurance

The application underwent multi-persona code review (5 personas: Statistical Methodologist, Security Auditor, UX/Accessibility Reviewer, Software Engineer, Domain Expert) identifying and resolving 17 critical (P0) and 33 important (P1) issues across statistical correctness, security hardening, WCAG accessibility, and clinical data accuracy. A 36-assertion automated Selenium test suite validates all configurations, features, and data fixes.

## Results

### Statistical Accuracy

The JavaScript engine matches R metafor within stated tolerances across all tested configurations. For the colchicine CVD configuration (k=5, default DL):

| Metric | LivingMeta (JS) | R metafor | |Diff| |
|--------|-----------------|-----------|--------|
| Pooled OR | 0.7940 | 0.7940 | <0.001 |
| 95% CI Lower | 0.6735 | 0.6735 | <0.001 |
| 95% CI Upper | 0.9363 | 0.9363 | <0.001 |
| tau-squared | 0.0268 | 0.0268 | <0.001 |
| I-squared | 50.2% | 50.2% | <0.1% |

### Text Extraction

The extractor correctly identifies effect estimates from standard journal abstract formats. Testing against real trial text (COLCOT abstract: "HR 0.77; 95% CI 0.61 to 0.96; P=0.02") produces: effectType=HR, value=0.77, ciLo=0.61, ciHi=0.96, pValue=0.02, tier=AUTO_VERIFIED.

### Accessibility

All eight tab panels are keyboard-navigable (ArrowLeft/Right/Home/End), screen reader accessible (ARIA roles, tabindex management), and support a prefers-reduced-motion media query. Dark mode maintains WCAG AA contrast ratios (4.5:1 minimum for body text).

## Discussion

### Strengths

LivingMeta uniquely combines five capabilities in a single distributable file: (1) multi-source trial discovery (CT.gov, PubMed, OpenAlex), (2) automated text extraction with provenance, (3) comprehensive statistical synthesis (20+ methods), (4) in-browser R validation without installation, and (5) GRADE certainty assessment with patient-facing output. The single-file architecture eliminates deployment barriers — reviewers receive one HTML file that works offline.

### Limitations

1. **Text extraction ceiling.** The JavaScript extractor covers ~70% of standard abstract formats but cannot parse figures, complex tables, or non-English text. Full-text PDF extraction requires the companion Python pipeline.

2. **No IPD analysis.** The current engine supports study-level aggregate data only. Individual patient data meta-analysis requires dedicated tools.

3. **Outcome definition heterogeneity.** Some pooled analyses combine trials with different composite endpoint definitions (e.g., 3-point vs 4-point MACE in the GLP-1 config, first-event HR vs recurrent-event rate ratio in the SGLT2 config). LivingMeta flags these with estimand heterogeneity warnings but cannot fully resolve them without standardized outcome definitions.

4. **Trial data verification.** While all included trial data are sourced from published primary reports, independent double-data-extraction has not been performed for all 45 trials across all 9 configurations.

5. **Single-file scalability.** At 11,000+ lines, the codebase approaches the practical limit for single-file maintenance. A modular build system (as implemented in the companion IPD-Meta-Pro application) would be needed for further feature expansion.

6. **WebR availability.** In-browser R validation requires WebAssembly support and a ~20 MB download on first use. Older browsers or restricted network environments may not support this feature. A downloadable R script provides an alternative validation path.

7. **No network meta-analysis.** Direct pairwise comparisons only. The ATTR-CM configuration (3 drug classes) would benefit from network meta-analysis capabilities.

8. **Confidence level scope.** While the core synthesis engine respects the confidence level parameter, some advanced methods (sceptical p-value, TSA boundaries) use fixed alpha=0.05 thresholds.

## Data Availability

The complete source code, test suite, and clinical configurations are available at https://github.com/mahmood726-cyber/livingmeta. The application can be used directly by opening the HTML file in any modern browser. No installation, server, or account is required.

## Acknowledgments

Statistical methods implemented following Viechtbauer (2010) [10], Hartung & Knapp (2001) [6], and Cochrane Handbook for Systematic Reviews of Interventions [11]. Text extraction patterns adapted from the rct_data_extractor_v2 pipeline. WebR integration uses the webR project by George Stagg and the R Core Team [9].

## Author Contributions

[AUTHOR_PLACEHOLDER] conceived the tool, designed the architecture, curated clinical configurations, and wrote the manuscript.

## Competing Interests

The authors declare no competing interests.

## Funding

No external funding was received for this work.

## References

1. Elliott JH, Synnot A, Turner T, et al. Living systematic review: 1. Introduction-the why, what, when, and how. J Clin Epidemiol. 2017;91:23-30.
2. Wallace BC, Dahabreh IJ, Trikalinos TA, Lau J, Trow P, Schmid CH. Closing the gap between methodologists and end-users: R as a computational back-end. J Stat Softw. 2012;49(5):1-15.
3. Balduzzi S, Rucker G, Schwarzer G. How to perform a meta-analysis with R: a practical tutorial. Evid Based Ment Health. 2019;22(4):153-160.
4. DerSimonian R, Laird N. Meta-analysis in clinical trials. Control Clin Trials. 1986;7(3):177-188.
5. Viechtbauer W. Bias and efficiency of meta-analytic variance estimators in the random-effects model. J Educ Behav Stat. 2005;30(3):261-293.
6. Hartung J, Knapp G. A refined method for the meta-analysis of controlled clinical trials with binary outcome. Stat Med. 2001;20(24):3875-3889.
7. Mantel N, Haenszel W. Statistical aspects of the analysis of data from retrospective studies of disease. J Natl Cancer Inst. 1959;22(4):719-748.
8. Yusuf S, Peto R, Lewis J, Collins R, Sleight P. Beta blockade during and after myocardial infarction: an overview of the randomized trials. Prog Cardiovasc Dis. 1985;27(5):335-371.
9. Stagg G. WebR: R in the browser via WebAssembly. https://webr.r-wasm.org/. Accessed 2026.
10. Viechtbauer W. Conducting meta-analyses in R with the metafor package. J Stat Softw. 2010;36(3):1-48.
11. Higgins JPT, Thomas J, Chandler J, et al, eds. Cochrane Handbook for Systematic Reviews of Interventions. Version 6.4. Cochrane; 2023.
12. Walsh M, Srinathan SK, McAuley DF, et al. The statistical significance of randomized controlled trial results is frequently fragile: a case for a Fragility Index. J Clin Epidemiol. 2014;67(6):622-628.
13. Matthews RAJ. Beyond "significance": principles and practice of the Analysis of Credibility. R Soc Open Sci. 2018;5(1):171047.
14. Tardif JC, Kouz S, Waters DD, et al. Efficacy and safety of low-dose colchicine after myocardial infarction. N Engl J Med. 2019;381(26):2497-2505.
15. Nidorf SM, Fiolet ATL, Mosterd A, et al. Colchicine in patients with chronic coronary disease. N Engl J Med. 2020;383(19):1838-1847.
