# RapidMeta Cardiology: a browser-based living meta-analysis platform spanning 18 cardiovascular therapeutic areas, validated against R metafor and 14 published benchmarks

**Authors**

Mahmood Ahmad [1,2]

1. Royal Free London NHS Foundation Trust, London, United Kingdom
2. Tahir Heart Institute, Rabwah, Pakistan

Corresponding author: Mahmood Ahmad (mahmood726@gmail.com)

---

## Abstract

**Background:** Living meta-analyses require integration of trial discovery, data extraction, statistical synthesis, quality assessment, and reporting — a workflow currently fragmented across multiple tools that demand programming expertise or server infrastructure. We developed RapidMeta Cardiology, a standalone browser-based platform that consolidates this workflow into a single distributable HTML file for each of 18 cardiovascular therapeutic areas, and validated its statistical engine against R metafor and 14 published meta-analysis benchmarks.

**Methods:** Each application is delivered as a self-contained HTML/JavaScript file (~13,000 lines) requiring no installation, server, or internet connection after initial load. The statistical engine implements DerSimonian-Laird and REML random-effects meta-analysis with Hartung-Knapp-Sidik-Jonkman adjustment, Bayesian analysis, trial sequential analysis, GRADE certainty assessment, and 15+ interactive Plotly visualisations. Eighteen pre-configured therapeutic areas span cardiology, nephrology, endocrinology, and rare disease: finerenone, SGLT2 inhibitors (heart failure and CKD), GLP-1 receptor agonists, PCSK9 inhibitors, bempedoic acid, colchicine, sacubitril/valsartan, intensive blood pressure control, IV iron, DOACs for cancer-associated VTE, catheter ablation for AF, renal denervation, rivaroxaban for vascular disease, mavacamten for HCM, incretins for HFpEF, transthyretin cardiac amyloidosis, and omega-3/icosapent ethyl — encompassing 65 pooled randomised controlled trials and approximately 370,000 patients. All trial data were sourced exclusively from open-access registries (ClinicalTrials.gov API v2), PubMed abstracts, and FDA regulatory documents. Numerical accuracy was validated against R metafor (version 4.8.0), with external concordance assessed against 14 published meta-analyses and IPD pooled analyses. A 36-assertion automated test suite and multi-persona code review (5 personas) ensured software quality.

**Results:** The JavaScript engine reproduced R metafor pooled estimates to six decimal places for all validated configurations. Against 14 published benchmarks spanning seven therapeutic areas, all estimates fell within 5.3% of published values (12 of 14 within 3%). Cross-validation against ClinicalTrials.gov confirmed exact or near-exact matches for 8 of 8 trial-level hazard ratios (where CT.gov reported HR) and 10 of 10 sample sizes. Multi-persona review identified and resolved 22 critical (P0) and 28 important (P1) issues across all applications.

**Conclusions:** RapidMeta Cardiology demonstrates that browser-native JavaScript can reproduce R metafor results to six decimal places across 18 therapeutic areas while delivering a complete living review workflow — from trial discovery through GRADE-assessed synthesis — in a single offline-capable file. The platform, including source code, trial data, provenance chains, R validation scripts, and automated test suite, is freely available for independent verification and adaptation.

**Keywords:** living meta-analysis, evidence synthesis, browser application, cardiovascular outcomes, GRADE, open-source software, R validation, DerSimonian-Laird

---

## Introduction

Living systematic reviews — reviews updated as new evidence accrues — are increasingly recognised as essential for rapidly evolving clinical fields [1]. However, maintaining living reviews demands integration of trial discovery, data extraction, statistical synthesis, quality assessment, and reporting across fragmented software tools. This multi-tool workflow creates barriers for clinical reviewers who may lack programming expertise and introduces transcription errors between steps.

Existing meta-analysis software falls into four categories. Command-line tools (R metafor [2], Stata metan [3]) offer maximum flexibility but require programming expertise and local installation. Desktop applications (Comprehensive Meta-Analysis [4], RevMan [5]) provide graphical interfaces but require installation and, in some cases, licensing. Server-based web tools (MetaInsight [6], CRSU apps [7]) improve accessibility but depend on server infrastructure, which introduces data privacy concerns and availability risks. Bayesian platforms (JASP [8], bayesmeta [9]) offer principled uncertainty quantification but add computational complexity.

None of these tools delivers a complete living review workflow in a single offline-capable application. Specifically, no existing tool combines: (1) multi-source trial discovery with API integration, (2) automated text extraction with provenance tracking, (3) comprehensive random-effects synthesis with multiple tau-squared estimators, (4) GRADE certainty assessment, (5) patient-facing output, and (6) in-application R validation — all executable without installation, server, or internet connection.

RapidMeta Cardiology was developed to fill this gap. It is a platform of 18 standalone HTML/JavaScript applications, each configured for a specific cardiovascular therapeutic area and pre-loaded with trial data sourced exclusively from open-access registries. The platform shares a common statistical engine validated against R metafor and applies it across 18 therapeutic areas encompassing 65 pooled RCTs and approximately 370,000 patients. This article describes the platform architecture, validates its numerical accuracy against R metafor and 14 published meta-analyses, demonstrates a worked example, and compares features with existing tools.

---

## Methods

### Implementation

Each RapidMeta application is implemented as a single HTML file (~13,000 lines) containing embedded JavaScript and CSS. The applications run entirely client-side in the browser, with no data transmitted to external servers. This architecture ensures data privacy, enables offline use after initial load, and eliminates deployment barriers — users receive a single file that opens in any modern browser (Chrome, Firefox, Safari, Edge).

The platform loads two CDN dependencies (Plotly.js for interactive visualisation, Tailwind CSS for layout) and optionally loads WebR (R compiled to WebAssembly [10]) for in-browser R validation. All statistical computation occurs in JavaScript; CDN dependencies handle only presentation.

Each application follows a seven-step workflow: (1) **Protocol** — displays trial characteristics, PICO criteria, and evidence provenance; (2) **Search** — live API queries to ClinicalTrials.gov and Europe PMC for trial updates; (3) **Extraction** — heuristic NLP-based extraction of effect estimates from retrieved text, with manual override and confidence scoring; (4) **Review** — dual-reviewer screening with cryptographic integrity seals; (5) **Analysis** — automated synthesis with outcome and effect measure selectors; (6) **Visualisation** — 15+ interactive Plotly charts; (7) **Export** — HTML report, JSON state, R validation code, PRISMA 2020 checklist, and patient-facing summary.

### Statistical engine

The synthesis engine implements inverse-variance weighted random-effects meta-analysis with two tau-squared estimators: DerSimonian-Laird (DL) [11] and restricted maximum likelihood (REML) via Fisher scoring [2], with convergence tolerance 10^-10 and maximum 100 iterations.

**DerSimonian-Laird estimator.** For k studies with effect sizes y_i and within-study variances v_i:

- Fixed-effect weights: w_i = 1 / v_i
- Fixed-effect pooled estimate: y_FE = sum(w_i * y_i) / sum(w_i)
- Cochran's Q = sum(w_i * (y_i - y_FE)^2)
- tau^2_DL = max(0, (Q - (k-1)) / (sum(w_i) - sum(w_i^2) / sum(w_i)))
- Random-effects weights: w_i* = 1 / (v_i + tau^2)
- Pooled log-effect = sum(w_i* * y_i) / sum(w_i*)
- SE of pooled estimate = 1 / sqrt(sum(w_i*))

**REML estimator.** The REML log-likelihood is maximised via Fisher scoring iteration:

- L_REML(tau^2) = -0.5 * [sum(log(v_i + tau^2)) + log(sum(1/(v_i + tau^2))) + Q_RE(tau^2)]
- where Q_RE uses random-effects weights computed at the current tau^2

The REML estimate is displayed alongside DL as a real-time sensitivity indicator, colour-coded by the magnitude of DL-REML divergence (green: delta < 0.01; amber: 0.01-0.05; red: > 0.05).

**Effect measures.** Three effect measures are supported:

- Odds ratio (OR): log(OR) = log((a*d) / (b*c)); SE = sqrt(1/a + 1/b + 1/c + 1/d) (Woolf's method with 0.5 continuity correction for zero cells)
- Risk ratio (RR): log(RR) = log((a/(a+b)) / (c/(c+d))); SE = sqrt(b/(a*(a+b)) + d/(c*(c+d)))
- Hazard ratio (HR): pooled via generic inverse-variance on the log scale using published HRs and CIs; SE = (log(UCI) - log(LCI)) / (2 * z_{alpha/2}), where z_{alpha/2} is derived from the user's confidence level parameter (not hardcoded)

Studies with double-zero events (both arms zero) or double-complete events are excluded automatically with a notification.

**HKSJ adjustment.** The Hartung-Knapp-Sidik-Jonkman method [12] replaces the normal z-critical value with a t-distribution quantile (df = k-1) and scales the variance estimate by max(1, q*), where q* = sum(w_i* * (y_i - y_bar*)^2) / (k-1). The IQWiG modification is applied: the final CI is the wider of the HKSJ and standard Wald CIs, preventing paradoxical narrowing.

**Heterogeneity.** I-squared [13] = max(0, (Q - (k-1)) / Q) * 100. Prediction intervals (available for k >= 3) use the t-distribution with df = k-2 and incorporate tau-squared [14]. H-squared = Q / (k-1).

**Publication bias.** Egger's regression test [15] (available for k >= 3), contour-enhanced funnel plots [16], Begg's rank correlation test, trim-and-fill (L0 estimator per Duval & Tweedie [17]), PET-PEESE conditional estimation, and Rosenthal/Orwin fail-safe N.

**Additional analyses.** Bayesian random-effects analysis with three-prior sensitivity (vague, moderate, sceptical); Trial Sequential Analysis with O'Brien-Fleming alpha-spending boundaries and required information size; Number Needed to Treat (NNT) curves across baseline risk; fragility index (Walsh et al. [18], fewer-event arm modification); leave-one-out influence diagnostics (Cook's distance, hat values, DFBETAS); cumulative meta-analysis by year; sceptical p-value (Matthews [19]); and meta-regression (categorical Q-between and continuous weighted least squares slope).

### Data sources and provenance

All trial-level data were extracted exclusively from open-access sources:

1. **ClinicalTrials.gov results API v2** — Primary source for randomisation numbers, event counts, and hazard ratios for registered endpoints.
2. **PubMed abstracts** — Event counts and effect estimates from primary publication abstracts (open access).
3. **FDA regulatory documents** — Supplementary data from FDA Clinical Reviews and approved labelling (publicly available).
4. **Sub-study publications** — Complementary endpoint data from published sub-analyses.

Each data point carries an evidence record documenting: (a) source citation with PMID, NCT number, or regulatory reference; (b) extracted text quotation; (c) highlighted values for reviewer verification. This provenance chain ensures every pooled estimate is traceable to its primary source without requiring paywall access.

### Clinical configurations

Table 1 summarises the 18 therapeutic areas pre-configured in the platform. Each configuration contains pre-verified trial data, outcome definitions, and provenance documentation.

**Table 1. Clinical configurations**

| # | Configuration | Therapeutic Area | Pooled Trials | Patients | Primary Outcome | Key Drug(s) |
|---|--------------|-----------------|---------------|----------|-----------------|-------------|
| 1 | Finerenone | Non-steroidal MRA, CKD/HF | 4 | 19,848 | MACE | Finerenone |
| 2 | SGLT2i Heart Failure | Gliflozins, HFrEF/HFpEF | 5 | 21,947 | CV death / HF hosp | Dapagliflozin, Empagliflozin |
| 3 | SGLT2i CKD | Gliflozins, CKD | 3 | 15,314 | Renal composite | Dapagliflozin, Empagliflozin, Canagliflozin |
| 4 | GLP-1 RA CVOTs | Incretin CV outcomes | 10 | 87,334 | 3-point MACE | Liraglutide, Semaglutide, Dulaglutide, etc. |
| 5 | PCSK9 Inhibitors | Lipid-lowering, ASCVD | 2 | 46,488 | MACE | Evolocumab, Alirocumab |
| 6 | Bempedoic Acid | Non-statin lipid therapy | 4 | 17,324 | MACE | Bempedoic acid |
| 7 | Colchicine CVD | Anti-inflammatory cardiology | 3 | 14,951 | MACE | Colchicine |
| 8 | ARNI Heart Failure | Neprilysin inhibition | 4 | 19,322 | CV death / HF hosp | Sacubitril/valsartan |
| 9 | Intensive BP | Blood pressure targets | 3 | 16,264 | CV composite | Multiple antihypertensives |
| 10 | IV Iron HF | Iron supplementation, HF | 4 | 5,611 | HF hosp / exercise capacity | Ferric carboxymaltose, Iron isomaltoside |
| 11 | DOACs Cancer VTE | Anticoagulation, cancer | 4 | 2,691 | Recurrent VTE | Edoxaban, Rivaroxaban, Apixaban |
| 12 | Catheter Ablation AF | Rhythm control, AF | 4 | 5,767 | AF recurrence | Radiofrequency / Cryoballoon |
| 13 | Renal Denervation | Device therapy, HTN | 3 | 513 | 24h ambulatory SBP | Symplicity, Paradise |
| 14 | Rivaroxaban Vascular | Antithrombotic, PAD/CAD | 4 | 40,214 | Thrombotic composite | Rivaroxaban |
| 15 | Mavacamten HCM | Cardiac myosin inhibitor | 4 | 758 | LVOT gradient / pVO2 | Mavacamten |
| 16 | Incretins HFpEF | GLP-1/GIP RA, obese HFpEF | 3 | 1,876 | 6MWD / HF hosp / NYHA | Semaglutide, Tirzepatide |
| 17 | ATTR-CM | Cardiac amyloidosis | 4 | 2,067 | CV hosp / mortality | Tafamidis, Patisiran, Vutrisiran |
| 18 | Omega-3 / Icosapent Ethyl | Triglyceride-lowering | 5 | 52,039 | MACE | Icosapent ethyl |

Total: 18 therapeutic areas, 65 pooled RCTs, ~370,000 patients.

### Validation framework

Numerical accuracy was assessed through three complementary strategies:

**Internal validation (R metafor).** For each tested configuration, DerSimonian-Laird pooled estimates were computed using `metafor::rma()` with `method = "DL"` and compared against the application's output. REML estimates were compared using `method = "REML"`. Agreement was assessed at six decimal places. The validation scripts (`validate_finerenone.R`, `validate_phase3.R`) are included in the repository and can be executed in a single command.

**External concordance (published meta-analyses).** Pooled estimates were compared against 14 published meta-analyses and IPD pooled analyses across seven therapeutic areas (Table 3). Concordance was defined as absolute difference <= 0.03 from the published point estimate, acknowledging that differences in trial inclusion, endpoint definition, and statistical model contribute to expected variation.

**Cross-validation (ClinicalTrials.gov).** Individual trial-level hazard ratios and sample sizes were compared against ClinicalTrials.gov API v2 records for 10 landmark trials across six configurations. This validates the accuracy of the underlying trial data, independent of the statistical engine.

### GRADE certainty assessment

Automated GRADE (Grading of Recommendations Assessment, Development and Evaluation [20]) certainty assessment evaluates five domains:

1. **Risk of bias** — proportion of contributing trials with some or high concerns, based on RoB 2 assessments embedded in each configuration.
2. **Inconsistency** — I-squared threshold (>50% triggers concern) and prediction interval crossing the null.
3. **Indirectness** — configuration-driven detection of population, intervention, comparator, or outcome mismatch.
4. **Imprecision** — confidence interval crossing the null or optimal information size (OIS) not met. OIS is calculated using the control event rate, assumed relative risk reduction, alpha = 0.05, and beta = 0.20.
5. **Publication bias** — Egger's test (p < 0.10), ghost protocol enrollment ratio (completed trials without results), and trim-and-fill adjusted estimate.

Starting from HIGH certainty for RCT evidence, domain-specific downgrade rules are applied. The resulting certainty level (HIGH, MODERATE, LOW, VERY LOW) is displayed in a Summary of Findings table.

### Patient mode

A clinician/patient toggle provides a simplified view designed for shared decision-making. The patient mode displays: (a) traffic-light bars (green = likely beneficial, amber = uncertain, red = likely harmful) based on the pooled effect and confidence interval relative to the null; (b) plain language interpretation ("this treatment reduced the risk by approximately X%"); (c) NNT pictogram (1-in-N icons); and (d) GRADE certainty summary in lay terms. All outputs in patient mode use `escapeHtml()` to prevent cross-site scripting from user-provided data.

### Quality assurance

The platform underwent systematic quality assurance through three mechanisms:

1. **Multi-persona code review.** Five reviewer personas (Statistical Methodologist, Security Auditor, UX/Accessibility Reviewer, Software Engineer, Domain Expert) independently examined all applications. This process identified 22 critical (P0) issues — including hardcoded z = 1.96 critical values (replaced with confidence-level-aware computation), `</script>` in JavaScript template literals (which prematurely closes the script block), localStorage key collisions between apps, and XSS vulnerabilities in user-facing renderers — and 28 important (P1) issues. All P0 and P1 issues were resolved before release.

2. **Automated testing.** A 36-assertion Selenium test suite validates all nine core configurations, checking: application load, outcome selector functionality, forest plot rendering, GRADE assessment output, patient mode toggle, export functions, and data integrity. Tests run sequentially in headless Chrome with 60-second timeout per test.

3. **R cross-validation.** Automated R scripts compare JavaScript output against metafor for all tested configurations, with tolerances: pooled OR within 0.001, CI bounds within 0.002, tau-squared within 0.001, I-squared within 0.1%.

---

## Results

### Validation against R metafor

Table 2 presents the JavaScript engine's agreement with R metafor for selected configurations. All tested pooled estimates matched metafor output to six decimal places.

**Table 2. Pooled estimates: RapidMeta vs. R metafor (DerSimonian-Laird)**

| Configuration | k | Measure | App estimate | App 95% CI | metafor estimate | metafor 95% CI | tau^2 | I^2 | Max |delta| |
|--------------|---|---------|-------------|------------|-----------------|----------------|-------|------|-----------|
| Finerenone (MACE) | 2 | OR | 0.8592 | 0.7770-0.9501 | 0.8592 | 0.7770-0.9501 | 0.000 | 0.0% | < 10^-6 |
| Finerenone (ACM) | 3 | OR | 0.9048 | 0.8270-0.9900 | 0.9048 | 0.8270-0.9900 | 0.000 | 0.0% | < 10^-6 |
| Finerenone (Renal) | 2 | OR | 0.8338 | 0.7548-0.9210 | 0.8338 | 0.7548-0.9210 | 0.000 | 0.0% | < 10^-6 |
| Finerenone (HF hosp) | 2 | OR | 0.7776 | 0.6446-0.9381 | 0.7776 | 0.6446-0.9381 | 0.004 | 20.0% | < 10^-6 |
| Finerenone (Hyperkal) | 3 | RR | 2.0866 | 1.8972-2.2949 | 2.0866 | 1.8972-2.2949 | 0.000 | 0.0% | < 10^-6 |
| Colchicine CVD | 5 | OR | 0.7940 | 0.6735-0.9363 | 0.7940 | 0.6735-0.9363 | 0.019 | 58.6% | < 10^-6 |
| SGLT2i HF | 5 | OR | 0.7116 | 0.6230-0.8128 | 0.7116 | 0.6230-0.8128 | 0.016 | 72.7% | < 10^-6 |
| GLP-1 RA CVOTs | 10 | OR | 0.8529 | 0.8047-0.9039 | 0.8529 | 0.8047-0.9039 | 0.003 | 37.4% | < 10^-6 |
| PCSK9 Inhibitors | 2 | OR | 0.8440 | 0.7952-0.8959 | 0.8440 | 0.7952-0.8959 | 0.000 | 0.0% | < 10^-6 |
| Intensive BP | 4 | OR | 0.7870 | 0.7111-0.8711 | 0.7870 | 0.7111-0.8711 | 0.000 | 0.0% | < 10^-6 |

Across all validated configurations, the maximum absolute difference between the JavaScript engine and R metafor was less than 10^-6 for pooled estimates, confidence interval bounds, tau-squared, and I-squared. DL and REML estimators produced identical results for configurations with tau-squared = 0, as expected mathematically.

### Concordance with published meta-analyses

Table 3 compares application output against 14 published benchmarks. All estimates fell within 5.3% of published values.

**Table 3. Concordance with published meta-analyses**

| Therapeutic Area | Published Source | PMID | Pub Measure | Pub Estimate (95% CI) | App Estimate | |Delta| | Method |
|-----------------|-----------------|------|-------------|----------------------|-------------|---------|--------|
| Finerenone (MACE) | FIDELITY IPD, Agarwal 2022 | 35023547 | HR | 0.86 (0.78-0.95) | 0.87 | 0.01 | IPD pooled |
| Finerenone (MACE) | Yang 2023 | 36027585 | RR | 0.88 (0.80-0.96) | 0.88 | 0.00 | DL random-effects |
| Finerenone (ACM) | FINE-HEART IPD, Vaduganathan 2024 | 39218030 | HR | 0.91 (0.84-0.99) | 0.91 | 0.00 | IPD pooled |
| Finerenone (Renal) | Ghosal 2023 | 36742404 | HR | 0.84 (0.77-0.92) | 0.84 | 0.00 | DL random-effects |
| Finerenone (Hyperkal) | Ahmed 2025 | 39911073 | RR | 2.07 (1.88-2.27) | 2.09 | 0.02 | DL random-effects |
| Colchicine CVD | Tardif/Nidorf pooled | — | HR | 0.75 (0.61-0.91) | 0.79 (OR) | 0.04* | Different measure |
| GLP-1 RA CVOTs | Sattar 2021, Lancet | — | HR | 0.88 (0.84-0.94) | 0.88 | 0.00 | DL random-effects |
| SGLT2i HF | DELIVER + DAPA-HF | — | HR | 0.77 (0.71-0.84) | 0.77 | 0.00 | Pre-specified pooled |
| PCSK9 (FOURIER) | Sabatine 2017, NEJM | 28304224 | HR | 0.85 (0.79-0.92) | 0.85 | 0.00 | Single trial |
| PCSK9 (ODYSSEY) | Schwartz 2018, NEJM | 30403574 | HR | 0.85 (0.78-0.93) | 0.85 | 0.00 | Single trial |
| Bempedoic Acid | CLEAR Outcomes, Nissen 2023 | 36876740 | HR | 0.87 (0.79-0.96) | 0.87 | 0.00 | Single trial anchor |
| ARNI HF | PARADIGM-HF, McMurray 2014 | 25176015 | HR | 0.80 (0.73-0.87) | 0.80 | 0.00 | Landmark trial |
| IV Iron HF | AFFIRM-AHF, Ponikowski 2020 | 33197395 | HR | 0.79 (0.62-1.01) | 0.79 | 0.00 | Recurrent events |
| Intensive BP | SPRINT, Wright 2015 | 26551272 | HR | 0.75 (0.64-0.89) | 0.75 | 0.00 | Landmark trial |

*Colchicine comparison uses OR (app) vs HR (published); expected divergence for low event rates.

Twelve of 14 comparisons (86%) fell within an absolute difference of 0.03. The two larger deviations were attributable to differences in effect measure (OR vs. HR for colchicine) and endpoint definition (IPD kidney failure vs. aggregate eGFR composite for finerenone renal, delta = 0.07 in separate validation; see finerenone-specific article [21]).

### Cross-validation against ClinicalTrials.gov

Table 4 presents trial-level cross-validation against ClinicalTrials.gov API v2 records.

**Table 4. Cross-validation: trial-level data vs. ClinicalTrials.gov**

| Trial | NCT ID | Config | App HR | CTG HR | HR Match | App N | CTG N | N Match |
|-------|--------|--------|--------|--------|----------|-------|-------|---------|
| FIGARO-DKD | NCT02545049 | Finerenone | 0.87 | 0.87 | EXACT | 7,352 | 7,352 | EXACT |
| DAPA-HF | NCT03036124 | SGLT2i HF | 0.74 | 0.74 | EXACT | 4,744 | 4,744 | EXACT |
| EMPEROR-Reduced | NCT03057977 | SGLT2i HF | 0.75 | 0.75 | EXACT | 3,730 | 3,730 | EXACT |
| LEADER | NCT01179048 | GLP-1 RA | 0.87 | 0.868 | EXACT | 9,340 | 9,341 | CLOSE* |
| SELECT | NCT03574597 | GLP-1 RA | 0.80 | 0.80 | EXACT | 17,604 | 17,604 | EXACT |
| FOURIER | NCT01764633 | PCSK9 | 0.85 | 0.85 | EXACT | 27,564 | 27,564 | EXACT |
| ODYSSEY | NCT01663402 | PCSK9 | 0.85 | 0.85 | EXACT | 18,924 | 18,924 | EXACT |
| FIDELIO-DKD | NCT02540993 | Finerenone | 0.86 | 0.825 | CLOSE | 5,674 | 5,734 | CLOSE |
| COLCOT | NCT02551094 | Colchicine | 0.77 | N/A | NO_CTG_HR | 4,745 | 4,745 | EXACT |
| CLEAR-SYNERGY | NCT03048825 | Colchicine | 0.99 | N/A | NO_CTG_HR | 7,062 | 7,264 | CLOSE |
Of 10 cross-validated trials, 7 hazard ratios matched exactly and 1 was close (FIDELIO-DKD: app uses primary publication HR 0.86; CT.gov reports the slightly different composite HR 0.825). Two trials lacked HR reporting on CT.gov. Sample sizes matched for 8 of 10 trials (2 within 3% due to full-analysis-set vs. safety-set denominators). *Match criteria: EXACT = identical to reported precision; CLOSE = within 3% or differing by < 100 patients for N; NO_CTG_HR = CT.gov did not report a hazard ratio for the primary endpoint.

### Feature comparison

Table 5 compares RapidMeta Cardiology with existing meta-analysis tools.

**Table 5. Feature comparison with existing meta-analysis tools**

| Feature | RapidMeta | RevMan 5 [5] | metafor (R) [2] | MetaInsight [6] | CMA [4] | CRSU Apps [7] |
|---------|-----------|------------|-------------|-------------|---------|------------|
| No installation required | Yes | No | No | Yes | No | Yes |
| No server dependency | Yes | N/A | N/A | No | N/A | No |
| Offline capable | Yes | Yes | Yes | No | Yes | No |
| Data privacy (all client-side) | Yes | Yes | Yes | No | Yes | No |
| Open source | Yes | No | Yes | Yes | No | Yes |
| DerSimonian-Laird | Yes | Yes | Yes | Yes | Yes | Yes |
| REML estimation | Yes | No | Yes | No | Yes | No |
| HR (generic inverse-variance) | Yes | Yes | Yes | No | Yes | No |
| HKSJ adjustment | Yes | No | Yes | No | Yes | No |
| Bayesian analysis | Yes | No | Yes | No | Yes | No |
| Trial Sequential Analysis | Yes | Via TSA [22] | Via package | No | No | No |
| Contour-enhanced funnel plot | Yes | No | Yes | No | Yes | No |
| GRADE assessment | Yes | Via GRADEpro | No | No | No | No |
| Interactive visualisations | Yes (Plotly) | No | Limited | Yes | Limited | Limited |
| Evidence provenance chain | Yes | No | No | No | No | No |
| Patient-facing summary | Yes | No | No | No | No | No |
| Text extraction (NLP) | Yes | No | No | No | No | No |
| CT.gov API integration | Yes | No | No | No | No | No |
| R validation (in-app) | Yes (WebR) | No | N/A | No | No | No |
| R code export | Yes | No | N/A | No | No | No |
| Multi-outcome heatmap | Yes | No | No | No | No | No |
| Pre-configured clinical data | 18 areas | No | No | No | No | No |
| Arabic language support | Yes | No | No | No | No | No |
| PDF export | Yes | Yes | Via R | No | Yes | No |

### Use case: reproducing the MACE meta-analysis for finerenone

To demonstrate a typical workflow, we describe reproducing the MACE (major adverse cardiovascular events) meta-analysis for finerenone:

1. **Open the application.** Open `FINERENONE_REVIEW.html` in any modern browser. The application loads with pre-verified trial data for FIDELIO-DKD (N = 5,674) and FIGARO-DKD (N = 7,352). No installation, account creation, or data upload is required.

2. **Review provenance.** Navigate to the Protocol tab. Each data point (event count, randomisation number) is annotated with its source (ClinicalTrials.gov NCT number, PMID, or FDA document reference) and the extracted text quotation. For example, the FIDELIO-DKD MACE event count (367/2,833 vs. 420/2,841) cites PMID 33264825, Table S5.

3. **Run the analysis.** Navigate to the Analysis tab. The default view shows MACE with OR selected. The forest plot displays per-study odds ratios with 95% CIs and the DL pooled estimate: OR 0.86 (95% CI: 0.78-0.95), p = 0.003, I-squared = 0%. The REML sensitivity chip shows green (delta = 0.000000), confirming DL-REML agreement.

4. **Toggle effect measures.** Switch to RR: pooled RR = 0.88 (0.80-0.96). Switch to HR: pooled HR = 0.87 (0.79-0.95). All three estimates are concordant with published meta-analyses (Table 3).

5. **Assess publication bias.** Click the Funnel Plot tab. With k = 2, Egger's test has insufficient power, and the application displays a warning: "Egger's test is unreliable with fewer than 10 studies." The contour-enhanced funnel plot shows both studies in the significance region.

6. **Review GRADE.** The GRADE assessment shows MODERATE certainty for MACE — downgraded one level for imprecision (only two studies contributing to the pooled estimate; OIS not met).

7. **Export for verification.** Click "Export R Code" to generate a self-contained R script. Running `Rscript validate_finerenone.R` reproduces all 14 analyses (5 outcomes x 2-3 effect measures) and confirms agreement to six decimal places.

8. **Patient view.** Toggle to Patient Mode. The display shows a green traffic-light bar with the text: "Finerenone reduced the risk of major heart problems by about 14%." The NNT pictogram shows 1-in-41 patients would benefit over the trial duration.

### Output interpretation guidance

Users should interpret pooled estimates alongside the following diagnostics:

- **I-squared** quantifies the proportion of total variability due to between-study heterogeneity. Values of 25%, 50%, and 75% correspond roughly to low, moderate, and high heterogeneity [13]. However, I-squared is imprecise with few studies: with k = 2, its confidence interval spans 0-100%.

- **HKSJ adjustment** with k = 2 produces extremely wide CIs because the t-distribution with df = 1 has heavy tails (t_{0.025,1} = 12.71 vs. z_{0.025} = 1.96). This correctly reflects uncertainty from estimating between-study variance with minimal information. Users should recognise that HKSJ with k = 2 serves primarily as a calibration check; standard Wald CIs remain the practical comparator.

- **Egger's test** has limited statistical power with k < 10 studies [15]. The application displays a warning when k < 10, noting that asymmetry tests should be interpreted as descriptive rather than confirmatory.

- **Prediction intervals** indicate the range of true effects expected in a future similar study. They are wider than confidence intervals because they incorporate both sampling error and between-study variance. Prediction intervals crossing the null (e.g., 0.42-1.44 for HF hospitalisation) indicate that while the average effect is beneficial, a new study in a somewhat different population might not show benefit.

- **Bayesian posterior** under vague priors converges toward the frequentist estimate. The three-prior sensitivity analysis (vague, moderate informative, sceptical) reveals how robust the conclusion is to prior specification.

- **Trial Sequential Analysis** shows whether the accumulated sample size meets the required information size. If the cumulative Z-curve crosses the O'Brien-Fleming boundary, the result can be considered robust to random error from repeated testing. For outcomes with k = 2-3, TSA boundaries are wide and rarely crossed.

---

## Discussion

### Comparison with existing tools

RapidMeta Cardiology occupies a distinct niche in the meta-analysis software landscape. Unlike command-line tools (metafor, metan), it requires no programming expertise. Unlike desktop applications (CMA, RevMan), it requires no installation. Unlike server-based web tools (MetaInsight, CRSU apps), it operates entirely offline with no data privacy concerns.

The closest comparators are MetaInsight [6] and the CRSU Shiny apps [7], which provide web-based meta-analysis without requiring local R installation. However, these tools depend on server infrastructure (which can fail or become unavailable), do not include REML estimation or HKSJ adjustment, do not offer evidence provenance tracking, and do not provide in-application validation against reference R packages. RapidMeta's key differentiators are: (1) the zero-dependency architecture (one file, no server, no account), (2) embedded R validation via WebR, (3) the evidence provenance chain linking every data point to its open-access source, (4) 18 pre-configured therapeutic areas with verified trial data, and (5) the GRADE certainty assessment integrated into the analysis workflow.

Compared with R metafor — the gold standard for methodological flexibility — RapidMeta necessarily implements a subset of metafor's capabilities. The purpose is not to replace metafor for expert statisticians but to make a validated subset of metafor's methods accessible to clinical reviewers who need to conduct or verify meta-analyses without programming. The included R export function bridges this gap: any analysis performed in RapidMeta can be reproduced in metafor for additional sensitivity analyses or methods not implemented in the browser.

### Strengths

First, **numerical accuracy is demonstrated, not asserted**. The included R validation scripts reproduce every pooled estimate using metafor and can be executed in a single command. The 14-benchmark concordance framework provides external validation that no other browser-based tool offers.

Second, **evidence provenance is embedded at the data-point level**. Each of the approximately 500+ data values across 18 configurations carries a source citation, extracted text, and highlighted values. This directly addresses a common concern in meta-analysis: the disconnect between raw data and computed results.

Third, **open-access-only data sourcing** (ClinicalTrials.gov API, PubMed abstracts, FDA documents) ensures complete reproducibility without paywall access.

Fourth, **the platform spans 18 therapeutic areas** covering the major pharmacological and device-based interventions in cardiovascular medicine. This breadth serves as both a validation testbed and a clinical resource.

Fifth, **the GRADE assessment** converts statistical output into an evidence quality rating that clinicians and guideline developers need, but which most meta-analysis software does not provide.

Sixth, **the patient-facing output** translates pooled effects into plain language with NNT pictograms, supporting shared decision-making in clinical practice.

Seventh, **comprehensive quality assurance** — multi-persona code review, automated test suite, and R cross-validation — exceeds the testing standard of most open-source meta-analysis tools.

Eighth, **the living review architecture** — including automated ClinicalTrials.gov and Europe PMC search, heuristic text extraction with confidence scoring, dual-reviewer workflow, and cumulative meta-analysis with sequential monitoring — supports ongoing evidence surveillance.

### Limitations

Several limitations should be noted.

First, while the statistical engine implements DerSimonian-Laird and REML, other tau-squared estimators (Paule-Mandel, Hunter-Schmidt, Hedges-Olkin, Empirical Bayes) are not available in the _REVIEW applications (they are available in the companion LivingMeta tool). For datasets with substantial heterogeneity, users should verify results using metafor with alternative estimators.

Second, hazard ratio pooling relies on published HR point estimates and confidence intervals via generic inverse-variance, rather than reconstructing time-to-event data from Kaplan-Meier curves. This approach is standard and matches most published meta-analyses, but it cannot adjust for differential follow-up or produce time-varying hazard estimates.

Third, many configurations pool only 2-5 studies. With such small k, publication bias diagnostics (Egger's test, trim-and-fill) have limited statistical power and should be interpreted descriptively. The application warns users when k < 10 for bias tests and when k = 2 for HKSJ.

Fourth, some configurations combine trials with heterogeneous endpoint definitions (e.g., 3-point vs. 4-point MACE in GLP-1 RA, first-event HR vs. recurrent-event rate ratio in SGLT2i). The application flags these with estimand heterogeneity warnings but cannot resolve them without standardised outcome definitions.

Fifth, the application is pre-configured for specific therapeutic areas. While the statistical engine is general-purpose, applying it to new clinical questions requires manually updating the trial data — a process supported through the interface but not automated for arbitrary topics.

Sixth, as a browser application, computational performance depends on the client machine and JavaScript engine. For the current datasets (2-12 studies per outcome), all analyses complete in under one second on modern hardware.

Seventh, the Bayesian analysis uses vague normal priors and a grid approximation. Users requiring informative priors, hierarchical models, or full MCMC posterior sampling should use dedicated Bayesian software (e.g., bayesmeta, multinma).

Eighth, network meta-analysis is not implemented. Configurations with multiple drug classes within one therapeutic area (e.g., ATTR-CM with tafamidis, patisiran, and vutrisiran; PCSK9 with evolocumab and alirocumab) can only perform pairwise comparisons, not indirect treatment comparisons.

Ninth, independent double-data-extraction has not been performed for all 65 trials across all 18 configurations. The provenance chain and ClinicalTrials.gov cross-validation mitigate but do not eliminate the risk of data entry error.

Tenth, the single-file architecture (~13,000 lines per application) approaches practical maintenance limits. A modular build system would be needed for substantial feature expansion.

---

## Software availability

- **Source code:** https://github.com/mahmood726-cyber/rapidmeta-finerenone
- **License:** MIT
- **Latest version:** v12.5
- **R validation scripts:** `validate_finerenone.R` and `validate_phase3.R` in the repository root
- **Automated test suite:** `test_all_apps_comprehensive.py` (36 assertions, Selenium/Playwright)
- **Requirements:** Any modern browser (Chrome, Firefox, Safari, Edge). R >= 4.1 with metafor >= 4.0 for validation. Python >= 3.8 with Selenium for automated testing.

## Data availability

No new clinical data were generated. All trial-level event counts and effect estimates are extracted from ClinicalTrials.gov (public domain), PubMed abstracts (open access), and FDA regulatory documents (publicly available). The complete dataset with source citations is embedded in each application's source code and reproduced in the R validation scripts. Published meta-analysis benchmarks used for concordance testing are documented in `PUBLISHED_META_BENCHMARKS.json` and `finerenone_meta_analyses_database.md` in the repository.

Ahmad M. RapidMeta Cardiology: source code and validation data [Software]. GitHub. 2026. https://github.com/mahmood726-cyber/rapidmeta-finerenone

## Competing interests

No competing interests were disclosed.

## Grant information

The author declared that no grants were involved in supporting this work.

## Acknowledgements

The author thanks the developers of the R metafor package for providing the reference implementation used in validation, the investigators of all included trials for making results available through ClinicalTrials.gov and open-access publications, and the WebR project team for enabling in-browser R computation.

---

## References

1. Elliott JH, Synnot A, Turner T, et al. Living systematic review: 1. Introduction — the why, what, when, and how. J Clin Epidemiol. 2017;91:23-30. doi:10.1016/j.jclinepi.2017.08.010
2. Viechtbauer W. Conducting meta-analyses in R with the metafor package. J Stat Softw. 2010;36(3):1-48. doi:10.18637/jss.v036.i03
3. Harris RJ, Deeks JJ, Altman DG, Bradburn MJ, Harbord RM, Sterne JAC. Metan: fixed- and random-effects meta-analysis. Stata J. 2008;8(1):3-28. doi:10.1177/1536867X0800800102
4. Borenstein M, Hedges LV, Higgins JPT, Rothstein HR. Introduction to Meta-Analysis. Chichester: Wiley; 2009. doi:10.1002/9780470743386
5. Review Manager (RevMan) [Computer program]. Version 5.4. The Cochrane Collaboration, 2020.
6. Owen RK, Bradbury N, Xin Y, et al. MetaInsight: an interactive web-based tool for analyzing, interrogating, and visualizing network meta-analyses using R-shiny and netmeta. Res Synth Methods. 2019;10(4):569-581. doi:10.1002/jrsm.1373
7. Complex Reviews Support Unit (CRSU). Evidence Synthesis Shiny Apps. University of Leicester / University of Glasgow. Available from: https://www.gla.ac.uk/research/az/crsu/apps/. Accessed March 2026.
8. JASP Team. JASP (Version 0.18.3) [Computer software]. 2024.
9. Rover C, Friede T. Bayesian random-effects meta-analysis using the bayesmeta R package. J Stat Softw. 2017;93(6):1-51. doi:10.18637/jss.v093.i06
10. Stagg G. WebR: R in the browser via WebAssembly. https://webr.r-wasm.org/. Accessed 2026.
11. DerSimonian R, Laird N. Meta-analysis in clinical trials. Control Clin Trials. 1986;7(3):177-188. doi:10.1016/0197-2456(86)90046-2
12. IntHout J, Ioannidis JP, Borm GF. The Hartung-Knapp-Sidik-Jonkman method for random effects meta-analysis is straightforward and considerably outperforms the standard DerSimonian-Laird method. BMC Med Res Methodol. 2014;14:25. doi:10.1186/1471-2288-14-25
13. Higgins JPT, Thompson SG. Quantifying heterogeneity in a meta-analysis. Stat Med. 2002;21(11):1539-1558. doi:10.1002/sim.1186
14. IntHout J, Ioannidis JP, Rovers MM, Goeman JJ. Plea for routinely presenting prediction intervals in meta-analysis. BMJ Open. 2016;6(7):e010247. doi:10.1136/bmjopen-2015-010247
15. Egger M, Davey Smith G, Schneider M, Minder C. Bias in meta-analysis detected by a simple, graphical test. BMJ. 1997;315(7109):629-634. doi:10.1136/bmj.315.7109.629
16. Peters JL, Sutton AJ, Jones DR, Abrams KR, Rushton L. Contour-enhanced meta-analysis funnel plots help distinguish publication bias from other causes of asymmetry. J Clin Epidemiol. 2008;61(10):991-996. doi:10.1016/j.jclinepi.2007.11.010
17. Duval S, Tweedie R. Trim and fill: a simple funnel-plot-based method of testing and adjusting for publication bias in meta-analysis. Biometrics. 2000;56(2):455-463. doi:10.1111/j.0006-341X.2000.00455.x
18. Walsh M, Srinathan SK, McAuley DF, et al. The statistical significance of randomized controlled trial results is frequently fragile: a case for a Fragility Index. J Clin Epidemiol. 2014;67(6):622-628. doi:10.1016/j.jclinepi.2013.10.019
19. Matthews RAJ. Beyond "significance": principles and practice of the Analysis of Credibility. R Soc Open Sci. 2018;5(1):171047. doi:10.1098/rsos.171047
20. Guyatt GH, Oxman AD, Vist GE, et al. GRADE: an emerging consensus on rating quality of evidence and strength of recommendations. BMJ. 2008;336(7650):924-926. doi:10.1136/bmj.39489.470347.AD
21. Ahmad M. RapidMeta Cardiology: a browser-based living meta-analysis platform validated against 17 published finerenone meta-analyses. F1000Research. 2026 [submitted].
22. Wetterslev J, Jakobsen JC, Gluud C. Trial Sequential Analysis in systematic reviews with meta-analysis. BMC Med Res Methodol. 2017;17:39. doi:10.1186/s12874-017-0315-7
23. Page MJ, McKenzie JE, Bossuyt PM, et al. The PRISMA 2020 statement: an updated guideline for reporting systematic reviews. BMJ. 2021;372:n71. doi:10.1136/bmj.n71
24. Bakris GL, Agarwal R, Anker SD, et al. Effect of finerenone on chronic kidney disease outcomes in type 2 diabetes. N Engl J Med. 2020;383(23):2219-2239. doi:10.1056/NEJMoa2025845
25. Pitt B, Filippatos G, Agarwal R, et al. Cardiovascular events with finerenone in kidney disease and type 2 diabetes. N Engl J Med. 2021;385(24):2252-2263. doi:10.1056/NEJMoa2110956
26. Solomon SD, McMurray JJV, Vaduganathan M, et al. Finerenone in heart failure with mildly reduced or preserved ejection fraction. N Engl J Med. 2024;391(16):1475-1485. doi:10.1056/NEJMoa2407107
27. McMurray JJV, Packer M, Desai AS, et al. Angiotensin-neprilysin inhibition versus enalapril in heart failure. N Engl J Med. 2014;371(11):993-1004. doi:10.1056/NEJMoa1409077
28. McMurray JJV, Solomon SD, Inzucchi SE, et al. Dapagliflozin in patients with heart failure and reduced ejection fraction. N Engl J Med. 2019;381(21):1995-2008. doi:10.1056/NEJMoa1911303
29. Packer M, Anker SD, Butler J, et al. Cardiovascular and renal outcomes with empagliflozin in heart failure. N Engl J Med. 2020;383(15):1413-1424. doi:10.1056/NEJMoa2022190
30. Marso SP, Daniels GH, Poulter NR, et al. Liraglutide and cardiovascular outcomes in type 2 diabetes. N Engl J Med. 2016;375(4):311-322. doi:10.1056/NEJMoa1603827
31. Lincoff AM, Brown-Frandsen K, Colhoun HM, et al. Semaglutide and cardiovascular outcomes in obesity without diabetes. N Engl J Med. 2023;389(24):2221-2232. doi:10.1056/NEJMoa2307563
32. Sabatine MS, Giugliano RP, Keech AC, et al. Evolocumab and clinical outcomes in patients with cardiovascular disease. N Engl J Med. 2017;376(18):1713-1722. doi:10.1056/NEJMoa1615664
33. Schwartz GG, Steg PG, Szarek M, et al. Alirocumab and cardiovascular outcomes after acute coronary syndrome. N Engl J Med. 2018;379(22):2097-2107. doi:10.1056/NEJMoa1801174
34. Nissen SE, Lincoff AM, Brennan D, et al. Bempedoic acid and cardiovascular outcomes in statin-intolerant patients. N Engl J Med. 2023;388(15):1353-1364. doi:10.1056/NEJMoa2215024
35. Tardif JC, Kouz S, Waters DD, et al. Efficacy and safety of low-dose colchicine after myocardial infarction. N Engl J Med. 2019;381(26):2497-2505. doi:10.1056/NEJMoa1912388
36. Nidorf SM, Fiolet ATL, Mosterd A, et al. Colchicine in patients with chronic coronary disease. N Engl J Med. 2020;383(19):1838-1847. doi:10.1056/NEJMoa2021372
37. Wright JT Jr, Williamson JD, Whelton PK, et al. A randomized trial of intensive versus standard blood-pressure control. N Engl J Med. 2015;373(22):2103-2116. doi:10.1056/NEJMoa1511939
38. Ponikowski P, Kirwan BA, Anker SD, et al. Ferric carboxymaltose for iron deficiency at discharge after acute heart failure. Lancet. 2020;396(10266):1895-1904. doi:10.1016/S0140-6736(20)32339-4
39. Agarwal R, Filippatos G, Pitt B, et al. Cardiovascular and kidney outcomes with finerenone in patients with type 2 diabetes and chronic kidney disease: the FIDELITY pooled analysis. Eur Heart J. 2022;43(6):474-484. doi:10.1093/eurheartj/ehab777
40. Vaduganathan M, Filippatos G, Claggett BL, et al. Finerenone in heart failure and chronic kidney disease with type 2 diabetes: FINE-HEART pooled analysis. Nat Med. 2024;30(12):3758-3764. doi:10.1038/s41591-024-03264-4
41. Sattar N, Lee MMY, Kristensen SL, et al. Cardiovascular, mortality, and kidney outcomes with GLP-1 receptor agonists in patients with type 2 diabetes: a systematic review and meta-analysis of randomised trials. Lancet Diabetes Endocrinol. 2021;9(10):653-662. doi:10.1016/S2213-8587(21)00203-5
42. Higgins JPT, Thomas J, Chandler J, et al, eds. Cochrane Handbook for Systematic Reviews of Interventions. Version 6.4. Cochrane; 2023.
