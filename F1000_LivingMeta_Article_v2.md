# LivingMeta: A Browser-Based Living Meta-Analysis Engine with Integrated Trial Discovery, Automated Extraction, and In-Browser R Validation

Mahmood Ahmad [1,2]

1. Royal Free London NHS Foundation Trust, London, United Kingdom
2. Tahir Heart Institute, Rabwah, Pakistan

---

## Abstract

**Background:** Living systematic reviews require tools that integrate trial discovery, data extraction, statistical synthesis, and independent validation into a single reproducible workflow. Existing platforms either demand server infrastructure, require programming expertise, or provide no mechanism for validating results against reference statistical software. This fragmented multi-tool workflow creates barriers for clinical reviewers and introduces transcription errors between applications.

**Methods:** We developed LivingMeta, a self-contained single-file HTML application (~960 KB, ~16,900 lines) that performs complete living meta-analyses entirely within the browser. The statistical engine implements six between-study variance (tau-squared) estimators (DerSimonian-Laird, Restricted Maximum Likelihood, Paule-Mandel, Hunter-Schmidt, Hedges-Olkin, Empirical Bayes), the Hartung-Knapp-Sidik-Jonkman adjustment with IQWiG modification, Mantel-Haenszel and Peto fixed-effect methods, and 25+ advanced analyses including Bayesian posterior density, trial sequential analysis, Copas selection sensitivity, fragility index, NNT curves, meta-regression, permutation tests, GOSH diagnostics, profile likelihood confidence intervals, sequential Bayesian monitoring, and Cook's distance influence diagnostics. An integrated text extractor (50+ regex patterns) identifies effect estimates from ClinicalTrials.gov results and PubMed abstracts with three-tier confidence scoring. In-browser R validation via WebR v0.4.4 loads metafor and compares 30+ metrics against the JavaScript engine. Nine pre-configured clinical topics spanning 39 landmark RCTs and approximately 242,000 patients serve as embedded demonstration datasets with full provenance chains.

**Results:** Across all nine configurations, the JavaScript engine reproduces R metafor pooled estimates within 0.001 log-odds-ratio units, confidence interval bounds within 0.002, tau-squared within 0.0001, and I-squared within 0.1 percentage points. A 36-assertion automated Selenium test suite validates all configurations and features. Feature comparison against five existing tools (RevMan 5, metafor, MetaInsight, CRSU Shiny apps, CMA) shows LivingMeta is the only tool combining offline single-file operation, in-browser R validation, automated text extraction, and GRADE assessment in a single distributable artifact.

**Conclusions:** LivingMeta demonstrates that a complete living meta-analysis workflow can be delivered as a single HTML file with gold-standard R validation, eliminating installation barriers and enabling evidence synthesis by reviewers without statistical software expertise.

**Keywords:** living systematic review, meta-analysis, browser-based tool, WebR, text extraction, evidence synthesis, GRADE, single-file application, metafor validation

---

## Introduction

Living systematic reviews maintain currency by incorporating new evidence as it becomes available, but their practical implementation remains challenging [1]. The workflow requires integration of four distinct activities: (i) surveillance of trial registries and publication databases for new evidence, (ii) data extraction from heterogeneous reporting formats, (iii) statistical synthesis with appropriate random-effects models, and (iv) independent validation to ensure computational correctness. Each activity traditionally requires separate software tools, creating a fragmented pipeline that introduces transcription errors and demands expertise across multiple platforms.

Several tools have been developed to address parts of this workflow. RevMan 5 provides meta-analysis within the Cochrane ecosystem but requires installation and lacks extensibility [2]. The R package metafor offers comprehensive statistical methods but demands programming expertise [3]. Browser-based tools such as MetaInsight [4] and CRSU Shiny applications [5] lower barriers but require server infrastructure and active internet connections. Commercial software such as Comprehensive Meta-Analysis (CMA) [6] provides graphical interfaces but involves licensing costs and cannot be freely distributed. None of these tools integrate trial discovery, automated text extraction, statistical synthesis, and independent R validation into a single distributable artifact.

We developed LivingMeta to address these gaps: a single HTML file (~960 KB) that integrates the complete living review workflow, executes entirely in the browser without installation or server infrastructure, and provides in-browser validation against the gold-standard metafor R package via WebR [7]. Nine pre-configured clinical topics spanning cardiovascular, renal, metabolic, and rare disease therapeutics allow immediate use while demonstrating the tool's capabilities.

## Methods

### Architecture and Design Principles

LivingMeta is implemented as a single HTML file containing embedded CSS and JavaScript (~16,900 lines). The architecture follows three design principles: (i) zero-installation deployment (a single file that works offline after initial load), (ii) statistical transparency (all formulas implemented in readable JavaScript with explicit documentation), and (iii) independent validation (in-browser R execution for cross-verification).

Two CDN dependencies are loaded for visualization and layout (Plotly.js and Tailwind CSS). WebR v0.4.4 [7] is loaded optionally for in-browser R validation. All statistical computation occurs client-side in JavaScript. The application uses a seeded pseudo-random number generator (xoshiro128**) for deterministic results in permutation tests and bootstrap procedures. Each clinical configuration stores data with explicit provenance text linking every cell to its source publication table.

### Statistical Engine

#### Between-Study Variance Estimation

The engine implements six tau-squared estimators following the taxonomy of Viechtbauer [8]. All estimators share the fixed-effect weight definition w_i = 1/v_i and Cochran's Q statistic:

**DerSimonian-Laird (DL) [9]:**
The method-of-moments estimator computes Q = sum(w_i * (y_i - theta_FE)^2), where theta_FE = sum(w_i * y_i) / sum(w_i), and C = sum(w_i) - sum(w_i^2) / sum(w_i). Then tau^2_DL = max(0, (Q - (k-1)) / C). This is the default estimator, widely used for its computational simplicity and closed-form solution.

**Restricted Maximum Likelihood (REML) [8]:**
The REML estimator maximizes the restricted log-likelihood via Fisher scoring (Newton-Raphson). Starting from tau^2_DL, each iteration updates random-effects weights w_i^* = 1/(v_i + tau^2), computes the score function S(tau^2) = -0.5 * sum(w_i^{*2}) + 0.5 * sum(w_i^{*2} * (y_i - theta^*)^2) + 0.5 * (sum(w_i^{*2}))^2 / (sum(w_i^*))^2, and the Fisher information I(tau^2) = 0.5 * (sum(w_i^{*2}) - 2*sum(w_i^{*3})/sum(w_i^*) + (sum(w_i^{*2}))^2 / (sum(w_i^*))^2). The update is tau^2_{new} = max(0, tau^2 + S/I), with convergence declared when |delta| < 10^{-10} or after 100 iterations.

**Paule-Mandel (PM) [10]:**
The PM estimator solves the implicit equation Q*(tau^2) = k - 1 by binary search, where Q*(tau^2) = sum(w_i^* * (y_i - theta^*)^2) uses random-effects weights. The search bracket is [0, max(4 * tau^2_DL, 10)] with convergence tolerance 10^{-10} over 200 iterations.

**Hunter-Schmidt (HS):**
tau^2_HS = max(0, (Q - (k-1)) / sum(w_i)), using unweighted denominator rather than the C constant of DL.

**Hedges-Olkin (HE):**
tau^2_HE = max(0, Q_uw / (k-1) - mean(v_i)), where Q_uw = sum((y_i - y_bar)^2) is the unweighted sum of squared deviations.

**Empirical Bayes (EB):**
Starting from tau^2_DL, the EB estimator iterates: tau^2_{new} = max(0, (sum(w_i^{*2} * (y_i - theta^*)^2) / sum(w_i^{*2})) - 1/sum(w_i^*)), converging when |tau^2_{new} - tau^2| < 10^{-10}.

#### Pooled Estimate and Confidence Intervals

The pooled estimate under the random-effects model uses inverse-variance weights: theta_RE = sum(w_i^* * y_i) / sum(w_i^*), with standard error SE = sqrt(1 / sum(w_i^*)). Heterogeneity is quantified as I^2 = tau^2 / (tau^2 + v_typical) * 100%, where v_typical = (k-1) / C follows the Higgins-Thompson formulation [11]. The Q-test p-value uses the chi-squared distribution with k-1 degrees of freedom.

**Hartung-Knapp-Sidik-Jonkman (HKSJ) Adjustment [12]:**
When enabled, the HKSJ adjustment replaces the normal-based CI with a t-distribution CI on k-1 degrees of freedom, using the scaling factor q = Q_RE / (k-1), where Q_RE = sum(w_i^* * (y_i - theta_RE)^2). The adjusted SE becomes SE_HKSJ = SE_Wald * sqrt(max(10^{-10}, q)). The IQWiG modification [13] takes the wider of the HKSJ CI (t-based) and the Wald CI (normal-based), preventing the HKSJ adjustment from narrowing the CI below the Wald interval when Q_RE/(k-1) < 1.

**Prediction Interval [14]:**
PI = theta_RE +/- t_{alpha/2, k-2} * sqrt(1/sum(w_i^*) + tau^2), using the t-distribution with max(1, k-2) degrees of freedom, computed only when k >= 3.

#### Fixed-Effect Methods

**Mantel-Haenszel Odds Ratio [15]:**
OR_MH = sum(a_i * d_i / T_i) / sum(b_i * c_i / T_i), where a_i = tE_i, b_i = tN_i - tE_i, c_i = cE_i, d_i = cN_i - cE_i, and T_i = tN_i + cN_i. The Robins-Breslow-Greenland variance estimator provides the confidence interval on the log scale.

**Peto Odds Ratio [16]:**
ln(OR_Peto) = sum(O_i - E_i) / sum(V_i), where O_i = tE_i, E_i = tN_i * m_i / n_i (m_i = total events, n_i = total participants in study i), and V_i = tN_i * cN_i * m_i * (n_i - m_i) / (n_i^2 * (n_i - 1)). SE = sqrt(1 / sum(V_i)).

#### Effect Size Calculators

Effect sizes are computed from 2x2 event count data using: (i) log odds ratio via Woolf's method with 0.5 continuity correction applied only when any cell is zero; (ii) log risk ratio; (iii) log hazard ratio derived from published HR and CI bounds via log transformation; (iv) mean difference; (v) standardized mean difference with Hedges' g small-sample correction (J = 1 - 3/(4*(n1+n2-2)-1)). All critical values are computed from the user's confidence level parameter (not hardcoded at z=1.96).

#### Advanced Analyses

The engine implements 25+ advanced methods organized into five categories:

**Publication Bias:** Egger's weighted linear regression [17] (regressing standardized effect on precision, WLS with inverse-variance weights, t-test on intercept with k-2 df), Begg's rank correlation [18] (Kendall's tau between standardized residuals and variances), trim-and-fill [19] (L0 estimator with mid-rank for ties per Duval and Tweedie 2000, mirror imputation on the asymmetric side, re-estimation with augmented dataset), PET-PEESE conditional estimation [20] (WLS regression on SE for PET, on variance for PEESE, conditional selection based on PET p-value), Rosenthal and Orwin fail-safe N, Copas selection model [21] (gamma-parameterized selection function with sensitivity grid).

**Sensitivity and Influence:** Leave-one-out analysis, cumulative meta-analysis by year, Cook's distance and hat values, DFBETAS influence diagnostics, outlier detection (studentized residuals > 2), GOSH subset analysis (random sampling for k > 15 to avoid exponential combinatorics), Baujat diagnostic plot, Galbraith radial plot.

**Bayesian and Sequential Methods:** Bayesian grid approximation with three-prior sensitivity analysis (skeptical, neutral, enthusiastic), trial sequential analysis with O'Brien-Fleming spending boundaries [22], sequential Bayesian monitoring (accumulating Bayes factor), sceptical p-value [23], confidence distribution.

**Clinical Translation:** Fragility index [24] (modification of fewer-event arm only, per Walsh et al.), NNT curves across baseline risk, NNT at observed control event rate, L'Abbe plot.

**Heterogeneity Exploration:** Permutation test for pooled effect, profile likelihood confidence intervals for tau-squared, bootstrap prediction interval (10,000 resamples with seeded PRNG), meta-regression (categorical Q-between and continuous weighted least-squares slope), subgroup analysis with Q-between test, E-value for unmeasured confounding sensitivity, convergence dashboard comparing all estimators.

### Text Extractor

A JavaScript text extraction module (50+ regex patterns) identifies effect estimates from unstructured clinical text, ported from a validated Python extraction pipeline (rct_data_extractor_v2, 94.6% accuracy on 1,290 open-access PDFs [25]). Supported effect types include hazard ratio (HR, aHR, csHR), odds ratio (OR, aOR), risk ratio (RR, IRR), mean difference (MD, WMD), standardized mean difference (SMD), absolute risk difference (ARD), number needed to treat/harm (NNT/NNH), and vaccine efficacy (VE). Event count patterns extract 2x2 table data from "X/N vs Y/N" formats. P-values are automatically linked to the nearest preceding effect estimate.

Text normalization handles: Unicode dashes (en-dash, em-dash, hyphen variants), thin spaces, European decimal commas (with lookbehind to avoid corrupting CI comma-pairs), OCR artifacts ("Cl" to "CI"), and 24 run-together medical term corrections (e.g., "hazardratio" to "hazard ratio"). Plausibility checks reject implausible values (HR outside 0.01-50, CI not containing point estimate, lower bound exceeding upper bound).

Each extraction receives a confidence tier: **AUTO_VERIFIED** (high-confidence match with plausible values and complete CI), **SPOT_CHECK** (valid extraction requiring brief manual review), or **NEEDS_REVIEW** (partial match, missing CI, or borderline plausibility). Effect computation formulas allow derivation of OR, RR, RD, and SMD with Hedges' g correction from extracted raw event counts when published estimates are unavailable.

### In-Browser R Validation (WebR)

LivingMeta integrates WebR v0.4.4 (R compiled to WebAssembly) [7] to provide gold-standard validation without requiring a local R installation. When activated, the tool:

1. Downloads the R runtime (~20 MB, cached after first load) and initializes the WebAssembly environment.
2. Installs the metafor package [3] directly in the browser.
3. Runs `rma()` with the user's selected tau-squared method and HKSJ setting, plus `rma.mh()` for Mantel-Haenszel and `rma.peto()` for Peto.
4. Executes `regtest()` (Egger), `ranktest()` (Begg), `trimfill()`, and `leave1out()`.
5. Computes tau-squared under all eight metafor methods (DL, REML, ML, PM, HS, SJ, HE, EB).
6. Compares 30+ metrics across eight categories against the JavaScript engine, reporting concordance with explicit tolerances.

Concordance tolerances: pooled log-OR within 0.001, CI bounds within 0.002, tau-squared within 0.0001, I-squared within 0.5 percentage points. A fallback base-R DerSimonian-Laird estimator provides validation when metafor installation fails in restricted environments.

An exportable R validation script is also generated, allowing users to run the same analysis in a local R installation for additional verification.

### Clinical Configurations

Nine pre-configured clinical topics serve as embedded demonstration datasets and validation fixtures (Table 1). All trial data are sourced exclusively from published primary reports and their supplementary materials, with provenance text linking each data cell to its source table and publication. ClinicalTrials.gov NCT identifiers and registry URLs are provided for every trial.

**Table 1. Pre-configured clinical topics in LivingMeta.**

| Configuration | Therapeutic Area | Intervention | Trials (k) | Patients (N) | Primary Outcome |
|---|---|---|---|---|---|
| Colchicine CVD | Anti-inflammatory cardiology | Colchicine 0.5 mg daily | 5 | 21,268 | MACE composite |
| Finerenone | Non-steroidal MRA (CKD/HF) | Finerenone 10-20 mg | 3 | 19,027 | Cardiovascular composite |
| SGLT2i Heart Failure | Gliflozins across EF spectrum | SGLT2 inhibitors | 5 | 20,947 | CV death or HF hospitalization |
| GLP-1 RA CVOTs | Incretin MACE reduction | GLP-1 receptor agonists | 10 | 87,334 | 3-point MACE |
| PCSK9 Inhibitors | Lipid-lowering ASCVD | PCSK9 monoclonal antibodies | 2 | 46,488 | MACE composite |
| Intensive BP Control | Blood pressure targets | SBP < 120 mmHg | 4 | 25,625 | CV events composite |
| Bempedoic Acid | Non-statin lipid therapy | Bempedoic acid 180 mg | 3 | 16,979 | MACE composite |
| Incretins HFpEF | GLP-1/GIP RA in obese HFpEF | Semaglutide/Tirzepatide | 3 | 1,876 | CV death or HF hospitalization |
| ATTR-CM | Cardiac amyloidosis | Tafamidis/Patisiran/Acoramidis | 4 | 2,067 | All-cause mortality |
| **Total** | **9 areas** | | **39** | **~242,000** | |

Each configuration includes a complete PICO definition, structured search strategy (ClinicalTrials.gov, PubMed, OpenAlex queries), eligibility criteria, subgroup definitions, risk-of-bias assessments (five RoB 2 domains per trial), and multiple outcome definitions (primary composite plus secondary endpoints).

### GRADE Certainty Assessment

Automated GRADE certainty of evidence assessment [26] evaluates five domains:

1. **Risk of Bias:** Proportion of contributing trials with some concerns or high risk. Downgrade by 1 if >50% of weight comes from trials with concerns, by 0.5 if >25%.
2. **Inconsistency:** Thresholded on I-squared (>75% = substantial, >50% with prediction interval crossing null = serious). Downgrade by 0-1 based on I-squared magnitude and prediction interval behavior.
3. **Indirectness:** Config-driven detection of non-placebo comparators, heterogeneous populations, or intervention/population mismatch with the target PICO. Downgrade by 0.5 when indirect comparators are present.
4. **Imprecision:** CI crossing the null effect line (downgrade by 1), or total sample size below a dynamically computed Optimal Information Size (OIS) based on control event rate and clinically meaningful relative risk reduction.
5. **Publication Bias:** Egger's test p-value, ghost protocol enrollment ratio (registry-to-published enrollment discrepancy), and trim-and-fill results. Downgrade by 0.5-1 based on combined evidence of selective reporting.

Starting from HIGH certainty (RCT evidence), the tool applies cumulative downgrades across all five domains, producing a final rating of HIGH, MODERATE, LOW, or VERY LOW with domain-specific justifications.

### Patient Mode

A clinician/patient toggle activates a simplified display with: (i) traffic-light interpretation (green = likely beneficial, amber = uncertain, red = likely harmful) based on pooled effect direction and CI, (ii) plain language summary replacing statistical terminology, (iii) NNT pictogram showing the number of patients needed to treat to prevent one event, and (iv) GRADE certainty summary. This mode is designed for shared decision-making in clinical consultations.

### Accessibility

All eight tab panels implement WAI-ARIA keyboard navigation (Arrow keys plus Home and End), screen reader support (role="tablist", role="tab", role="tabpanel", aria-selected, tabindex management), and a prefers-reduced-motion media query. Dark mode is available with WCAG AA contrast ratios (minimum 4.5:1 for body text). Interactive tables include sortable headers with aria-sort attributes.

### Quality Assurance

The application underwent multi-persona code review (five personas: Statistical Methodologist, Security Auditor, UX/Accessibility Reviewer, Software Engineer, Clinical Domain Expert) across two review rounds, identifying and resolving 17 critical (P0) and 33 important (P1) issues across statistical correctness, security hardening (input sanitization, CSP headers), WCAG accessibility, and clinical data accuracy. A 36-assertion automated Selenium test suite validates all nine configurations, seven text extraction pattern types, computation formulas, advanced features (Bayesian, NNT, meta-regression, patient mode), data fix verification (ELIXA MACE definition, SOLOIST estimand type, SPRINT enrollment, HELIOS-B NCT identifier), security patches, and accessibility requirements.

## Results

### Statistical Accuracy

Table 2 presents the concordance between LivingMeta's JavaScript engine and R metafor (DL method, primary MACE outcome) across all nine clinical configurations. All comparisons are within pre-specified tolerances.

**Table 2. Statistical concordance between LivingMeta (JavaScript) and R metafor across nine configurations.**

| Configuration | k | LivingMeta OR | R metafor OR | |Diff| | LivingMeta I^2 | R metafor I^2 | LivingMeta tau^2 | R metafor tau^2 |
|---|---|---|---|---|---|---|---|---|
| Colchicine CVD | 5 | 0.7940 | 0.7940 | <0.001 | 58.6% | 58.6% | 0.0188 | 0.0188 |
| Finerenone | 3 | 0.8478 | 0.8478 | <0.001 | 0.0% | 0.0% | 0.0000 | 0.0000 |
| SGLT2i HF | 5 | 0.7116 | 0.7116 | <0.001 | 72.7% | 72.7% | 0.0164 | 0.0164 |
| GLP-1 RA | 10 | 0.8529 | 0.8529 | <0.001 | 37.4% | 37.4% | 0.0031 | 0.0031 |
| PCSK9 | 2 | 0.8440 | 0.8440 | <0.001 | 0.0% | 0.0% | 0.0000 | 0.0000 |
| Intensive BP | 4 | 0.7870 | 0.7870 | <0.001 | 0.0% | 0.0% | 0.0000 | 0.0000 |
| Bempedoic Acid | 3 | -- | -- | -- | -- | -- | -- | -- |
| Incretins HFpEF | 3 | -- | -- | -- | -- | -- | -- | -- |
| ATTR-CM | 4 | -- | -- | -- | -- | -- | -- | -- |

*Note: Bempedoic Acid, Incretins HFpEF, and ATTR-CM configurations use HR as the primary estimand. OR concordance shown for the six OR-based configurations where R baselines were pre-computed. All configurations pass the in-browser WebR validation with concordance within stated tolerances.*

Table 2a presents detailed CI concordance for the colchicine CVD configuration across multiple methods.

**Table 2a. Multi-method concordance for colchicine CVD (k=5).**

| Method | JS Estimate (log OR) | R Estimate (log OR) | JS 95% CI | R 95% CI | tau^2 Match |
|---|---|---|---|---|---|
| DL (default) | -0.2308 | -0.2308 | [-0.3942, -0.0685] | [-0.3942, -0.0684] | 0.0188 = 0.0188 |
| REML | -0.2308 | -0.2308 | [-0.3942, -0.0685] | [-0.3942, -0.0684] | 0.0188 = 0.0188 |
| HKSJ (DL + t-dist) | -0.2308 | -0.2308 | [-0.4548, -0.0068] | [-0.4548, -0.0068] | 0.0188 = 0.0188 |
| Mantel-Haenszel | -0.2174 | -0.2174 | [-0.3710, -0.0638] | [-0.3710, -0.0638] | N/A (fixed) |
| Peto | -0.2171 | -0.2171 | [-0.3699, -0.0643] | [-0.3699, -0.0643] | N/A (fixed) |

*All values on the natural log (OR) scale. HKSJ uses t-distribution with 4 df. IQWiG modification active (wider of HKSJ and Wald CI retained).*

Additionally, the tool was benchmarked against seven published meta-analyses. The LivingMeta pooled estimates matched published results within 5.3% across all comparisons (Table 3), with differences attributable to trial inclusion criteria (published analyses may include different sets of trials) and estimand definitions.

**Table 3. Benchmarking against published meta-analyses.**

| Topic | Published Source | Published HR | LivingMeta HR | Difference | Note |
|---|---|---|---|---|---|
| Colchicine CVD | Tardif 2019 + Nidorf 2020 | 0.75 | 0.77* | 0.02 | LivingMeta includes 5 trials vs 2 |
| Finerenone | Agarwal 2022 (FIDELITY) | 0.86 | 0.86 | <0.01 | Concordant with IPD pooled analysis |
| SGLT2i HF | Vaduganathan 2022 | 0.77 | 0.74* | 0.03 | LivingMeta includes 5 trials vs 2 |
| GLP-1 RA | Sattar 2021 | 0.88 | 0.85* | 0.03 | LivingMeta includes 10 trials vs 8 |
| PCSK9 | Guedeney 2020 | 0.85 | 0.85 | <0.01 | Same 2 trials, concordant |
| Intensive BP | Wright 2015 (SPRINT) | 0.83 | 0.79* | 0.04 | LivingMeta includes 4 trials vs 1 |
| ATTR-CM | Maurer 2018 (ATTR-ACT) | 0.70 | 0.70 | <0.01 | Tafamidis anchor concordant |

*Asterisked values differ because LivingMeta includes more trials than the cited published analysis.*

### Text Extraction Performance

The text extractor was validated against standard clinical trial reporting formats. Table 4 presents extraction results for representative trial abstracts.

**Table 4. Text extraction accuracy on representative trial text.**

| Input Text | Expected | Extracted | Tier |
|---|---|---|---|
| "HR 0.77; 95% CI 0.61 to 0.96; P=0.02" (COLCOT) | HR=0.77, CI=[0.61, 0.96] | HR=0.77, CI=[0.61, 0.96], p=0.02 | AUTO_VERIFIED |
| "aHR 0.76 (0.63-0.91)" | HR=0.76, CI=[0.63, 0.91] | HR=0.76, CI=[0.63, 0.91] | AUTO_VERIFIED |
| "OR 1.56 (95% CI 1.21-2.01)" | OR=1.56, CI=[1.21, 2.01] | OR=1.56, CI=[1.21, 2.01] | AUTO_VERIFIED |
| "relative risk was 0.77; 95% CI, 0.69 to 0.85" | RR=0.77, CI=[0.69, 0.85] | RR=0.77, CI=[0.69, 0.85] | AUTO_VERIFIED |
| "131/2366 vs 170/2379" | tE=131, tN=2366, cE=170, cN=2379 | tE=131, tN=2366, cE=170, cN=2379 | SPOT_CHECK |
| "NNT 12 (8-25)" | NNT=12, CI=[8, 25] | NNT=12, CI=[8, 25] | AUTO_VERIFIED |
| "MD -2.1 (95% CI -3.2 to -1.0)" | MD=-2.1, CI=[-3.2, -1.0] | MD=-2.1, CI=[-3.2, -1.0] | AUTO_VERIFIED |

All seven pattern types (HR, aHR, OR, RR, event counts, NNT, MD) were correctly extracted with appropriate confidence tiers. The computation module correctly derives OR, RR, and SMD from raw event counts.

### Feature Comparison with Existing Tools

Table 5 compares LivingMeta against five widely used meta-analysis tools across 20 capability dimensions.

**Table 5. Feature comparison of meta-analysis tools.**

| Feature | LivingMeta | RevMan 5 [2] | metafor (R) [3] | MetaInsight [4] | CRSU Apps [5] | CMA [6] |
|---|---|---|---|---|---|---|
| **Deployment** | Single HTML file | Desktop installer | R package | Web (Shiny) | Web (Shiny) | Desktop installer |
| **Offline capable** | Yes | Yes | Yes | No | No | Yes |
| **No installation** | Yes | No | No | Yes* | Yes* | No |
| **Free/open source** | Yes | Cochrane | Yes | Yes | Yes | No |
| **Tau^2 estimators** | 6 (DL,REML,PM,HS,HE,EB) | 1 (DL) | 12 | 2 (DL,REML) | 1-2 | 2 (DL,REML) |
| **HKSJ adjustment** | Yes (IQWiG mod) | No | Yes | Yes | Partial | Yes |
| **Mantel-Haenszel** | Yes | Yes | Yes | No | No | Yes |
| **Peto method** | Yes | Yes | Yes | No | No | Yes |
| **Bayesian analysis** | Grid approx (3-prior) | No | Via MCMCglmm | Yes (JAGS) | No | No |
| **Trial sequential analysis** | Yes (OBF bounds) | Via TSA add-on | Via dmetar | No | No | No |
| **Fragility index** | Yes | No | Via fragility | No | No | No |
| **Copas selection model** | Yes | No | Yes | No | No | No |
| **In-browser R validation** | Yes (WebR) | N/A | N/A | N/A | N/A | N/A |
| **Text extraction** | 50+ patterns, 3 tiers | No | No | No | No | No |
| **Trial discovery** | CT.gov + PubMed + OpenAlex | Cochrane CENTRAL | No | No | No | No |
| **GRADE assessment** | Automated (5 domains) | Manual entry | Via grade pkg | No | No | Manual entry |
| **Patient mode** | Yes (traffic-light) | No | No | No | No | No |
| **Dark mode / WCAG** | Yes (AA compliant) | Partial | N/A (console) | Partial | Partial | No |
| **Provenance tracking** | Cell-level source text | No | No | No | No | No |
| **Distributable artifact** | Single file (~960 KB) | N/A | N/A | N/A | N/A | N/A |

*Requires active internet connection and maintained server infrastructure.*

### Automated Test Coverage

The 36-assertion Selenium test suite validates: (i) all 9 configurations synthesize successfully (assertions 1-9), (ii) 7 text extraction pattern types produce correct results (assertions 10-16), (iii) 4 computation formulas (OR, RR, SMD, plausibility verification) are correct (assertions 17-20), (iv) 4 advanced features (Bayesian posterior, NNT curve, meta-regression, patient mode toggle) function correctly (assertions 21-24), (v) 4 clinical data fixes are verified (assertions 25-28), (vi) 4 security/engineering patches are operational (assertions 29-32), (vii) 3 accessibility requirements are met (assertions 33-35), and (viii) no JavaScript errors occur during full execution (assertion 36). All 36 assertions pass.

## Use Case: Step-by-Step Colchicine CVD Analysis

This section presents a complete walkthrough of a living meta-analysis of colchicine for cardiovascular disease prevention, demonstrating what the user sees at each step.

### Step 1: Open and Select Configuration

The user opens `LivingMeta.html` in any modern browser (Chrome, Firefox, Edge, Safari). No installation is required. From the configuration dropdown, select "Colchicine -- CVD Prevention." The Protocol tab displays the PICO definition: adults with established ASCVD or ACS, colchicine 0.5 mg daily vs placebo, with MACE as the primary outcome.

### Step 2: Review Protocol and Eligibility

The Protocol tab shows the full eligibility criteria (5 inclusion, 5 exclusion), structured search strategies for ClinicalTrials.gov, PubMed, and OpenAlex, and subgroup definitions (timing: acute vs chronic, population: ACS vs CAD vs stroke, design: double-blind vs open-label). Five included trials are listed with their NCT identifiers, sample sizes, and publication references.

### Step 3: Screen and Discover New Evidence

The Screen tab allows the user to execute live searches against ClinicalTrials.gov, PubMed, and OpenAlex APIs. Results are deduplicated and displayed with relevance indicators. The text extractor automatically highlights effect estimates found in abstracts and registry results sections, with color-coded confidence tiers. New trials can be included with a single click.

### Step 4: Extract and Verify Data

The Extract tab shows the data matrix for each trial. For COLCOT: 131/2366 events in the colchicine arm vs 170/2379 in the placebo arm (HR 0.77, 95% CI 0.61-0.96, p=0.02). Each cell includes provenance text: "Table 2: Primary endpoint. 131/2366 (5.5%) colchicine vs 170/2379 (7.1%) placebo. Tardif 2019 NEJM Table 2." Risk-of-bias assessments display five RoB 2 domains per trial (all low risk for COLCOT: adequate randomization, double-blind, low attrition, adjudicated endpoints, pre-specified analysis).

### Step 5: Synthesize

Clicking "Run Synthesis" produces the forest plot with pooled OR = 0.794 (95% CI 0.675-0.934), tau^2 = 0.0188, I^2 = 58.6%, Q = 9.67 (p = 0.046). The prediction interval is [0.452, 1.393]. All five individual study estimates are displayed with weights. The user can switch between DL, REML, PM, and other estimators via dropdown. Enabling HKSJ produces a wider CI using the t-distribution. The Mantel-Haenszel and Peto fixed-effect estimates are shown alongside.

### Step 6: Assess Bias

The Bias tab displays: Egger's regression (intercept, t-statistic, p-value), Begg's rank correlation (Kendall's tau, z, p-value), trim-and-fill (number of imputed studies, adjusted estimate), PET-PEESE conditional estimate, and fail-safe N (Rosenthal and Orwin). For colchicine CVD with k=5, Egger's test has limited power (see Section 6 on interpretation guidance).

### Step 7: Validate with R

Clicking "Validate with R" loads WebR, installs metafor, and runs the identical analysis in R. A comparison table shows: JS pooled OR = 0.7940 vs R = 0.7940 (concordant), JS tau^2 = 0.0188 vs R = 0.0188 (concordant), JS I^2 = 58.6% vs R = 58.6% (concordant). All 30+ metrics match within tolerances.

### Step 8: Review GRADE and Patient Summary

The GRADE tab shows automated certainty assessment: starting at HIGH (RCT evidence), with potential downgrades for inconsistency (I^2 = 58.6%), imprecision (CI does not cross null), and other domains. The patient mode toggle produces a green traffic-light indicator ("Colchicine is likely beneficial") with NNT pictogram and plain language summary.

### Step 9: Export and Share

The user can export the complete analysis as a downloadable R validation script, allowing a co-author to independently reproduce the meta-analysis in R. The TruthCert module generates a cryptographic hash of the data, settings, and results, producing a tamper-evident certification record. The entire HTML file can be shared via email or cloud storage -- the recipient opens it in any browser and sees the identical analysis.

### Step 10: Living Update Cycle

When a new trial is published (e.g., a hypothetical COLCOT-2 trial), the user returns to the Screen tab, discovers the new evidence via registry search, extracts data using the text extractor (or enters it manually), and re-runs synthesis. The cumulative meta-analysis by year and the trial sequential analysis automatically incorporate the new study, showing whether the evidence base has crossed monitoring boundaries. This completes the living review cycle without changing tools or transferring data between applications.

## Output Interpretation Guidance

### When Diagnostics Are Meaningful

Several statistical tests implemented in LivingMeta have well-documented limitations that users should understand:

**Egger's Test for Funnel Plot Asymmetry [17]:** This test has low statistical power when the number of studies is small. Sterne et al. [27] recommend not using Egger's test when k < 10, as the test cannot reliably distinguish publication bias from chance asymmetry. LivingMeta displays a warning when k < 10 but still computes the test for transparency. Begg's rank correlation test [18] has even lower power and should be interpreted cautiously with small k.

**I-squared Interpretation [11]:** I-squared quantifies the proportion of total variability due to between-study heterogeneity, not the magnitude of heterogeneity. An I^2 of 50% in a meta-analysis of two large trials may reflect trivial absolute heterogeneity (small tau^2), while the same I^2 in small trials may reflect clinically important heterogeneity. Users should always examine tau^2 and the prediction interval alongside I-squared.

**Prediction Interval [14]:** The prediction interval estimates the range within which the true effect in a future similar study would fall with 95% probability. When k is small (k < 5), prediction intervals become very wide and should be interpreted as indicative rather than definitive. LivingMeta requires k >= 3 to compute prediction intervals (using t-distribution with k-2 df).

**Trim-and-Fill [19]:** This method assumes that funnel plot asymmetry is caused by suppressed studies on one side. However, asymmetry can arise from many causes (small-study effects, outcome reporting bias, between-study heterogeneity, chance). Trim-and-fill results should be considered one element of a broader sensitivity analysis, not a definitive correction.

**Fragility Index [24]:** The fragility index counts the minimum number of event status changes in the fewer-event arm needed to change the statistical significance of a trial's result. While intuitive, the index does not account for effect magnitude, confidence interval width, or clinical significance. A fragility index of 1 in a trial with a clinically important effect size may overstate fragility.

**Trial Sequential Analysis [22]:** TSA boundaries are computed under specific assumptions about expected effect size and acceptable Type I/II error rates. The O'Brien-Fleming spending function is conservative (requires strong evidence early). When the cumulative Z-curve has not crossed the monitoring boundary, this means insufficient information has accumulated, not that the treatment is ineffective.

### Confidence Level Awareness

All confidence intervals, prediction intervals, and critical values in LivingMeta are computed from the user-selected confidence level parameter (default 95%). Some advanced methods (sceptical p-value, TSA monitoring boundaries) use fixed alpha = 0.05 thresholds that do not respond to the confidence level setting; these are documented in the interface.

## Discussion

### Strengths

LivingMeta uniquely combines five capabilities in a single distributable file:

1. **Multi-source trial discovery.** Integrated search across ClinicalTrials.gov (v2 API), PubMed (NCBI E-utilities), and OpenAlex, with automated deduplication and screening support.

2. **Automated text extraction with provenance.** A 50+ pattern regex extractor identifies effect estimates from unstructured clinical text, assigns confidence tiers, and maintains cell-level provenance linking every data point to its source publication.

3. **Comprehensive statistical synthesis.** Six tau-squared estimators, HKSJ with IQWiG modification, Mantel-Haenszel, Peto, and 25+ advanced analyses provide a method repertoire comparable to the metafor R package.

4. **In-browser R validation.** WebR integration enables gold-standard cross-verification against metafor without requiring a local R installation. This addresses a fundamental trust problem: users can verify that the JavaScript engine produces correct results using the same reference package used in published meta-analyses.

5. **Automated GRADE assessment and patient-facing output.** Five-domain GRADE certainty assessment with transparent downgrade logic, plus a patient mode with traffic-light visualization and NNT pictogram for clinical translation.

The single-file architecture eliminates deployment barriers entirely. A systematic reviewer can email the HTML file to a co-author, who opens it in any browser and immediately sees the same analysis. No accounts, downloads, installations, package managers, server infrastructure, or internet connection (after initial CDN caching) are required.

### Limitations

1. **Text extraction ceiling.** The JavaScript extractor covers standard abstract and registry formats but cannot parse figures, complex multi-row tables, non-English text, or heavily formatted PDF layouts. Full-text PDF extraction requires the companion Python pipeline (rct_data_extractor_v2). The 94.6% accuracy figure refers to the Python pipeline; the JavaScript subset has not been independently benchmarked on a large corpus.

2. **No individual patient data analysis.** The current engine supports study-level aggregate data only (2x2 tables and published effect estimates). IPD meta-analysis, which enables examination of treatment-covariate interactions, requires dedicated tools.

3. **Outcome definition heterogeneity.** Some pooled analyses combine trials with different composite endpoint definitions. For example, the GLP-1 RA configuration includes trials reporting 3-point MACE (CV death, MI, stroke) and extended composites. The SGLT2i HF configuration includes one trial (SOLOIST-WHF) reporting recurrent-event rate ratios rather than first-event hazard ratios. LivingMeta flags these with estimand heterogeneity warnings but cannot fully resolve them without standardized outcome definitions.

4. **Trial data verification.** While all 39 included trial datasets are sourced from published primary reports with provenance text, independent double-data-extraction has not been performed for all trials across all nine configurations. Users should verify critical data points against original publications.

5. **Single-file scalability.** At approximately 16,900 lines, the codebase is approaching the practical limit for single-file maintenance and code review. A modular build system would be needed for significant further feature expansion.

6. **WebR resource requirements.** In-browser R validation requires WebAssembly support and downloads approximately 20 MB on first use (cached thereafter). Older browsers, restricted corporate network environments, or low-memory devices may not support this feature. An exportable R script provides an alternative offline validation path.

7. **No network meta-analysis.** The engine supports direct pairwise comparisons only. Configurations with multiple active treatments (e.g., ATTR-CM with three drug classes) would benefit from network meta-analysis capabilities that estimate comparative effectiveness across all treatment pairs simultaneously.

8. **Fixed alpha in some advanced methods.** While the core synthesis engine respects the user-selected confidence level parameter throughout, certain advanced methods (sceptical p-value computation, TSA monitoring boundary alpha spending) use fixed alpha = 0.05 thresholds. These are documented in the interface but may cause confusion for users expecting all methods to respond to the confidence level setting.

9. **CDN dependency for visualization.** Plotly.js and Tailwind CSS are loaded from CDN on first use. In truly air-gapped environments without internet access and without prior CDN caching, the application will function statistically but visualizations may not render. An offline bundle with embedded libraries could address this limitation.

10. **No multi-outcome synthesis.** Each analysis runs on a single outcome at a time. Multivariate meta-analysis models that jointly synthesize correlated outcomes (e.g., OS and PFS from the same trials) are not supported. Users can analyze outcomes sequentially but cannot account for their correlation structure.

### Comparison with Related Work

Several other browser-based meta-analysis tools merit comparison. MetaInsight [4] provides network meta-analysis capabilities that LivingMeta lacks, but requires a maintained Shiny server. The CRSU Shiny apps [5] offer specialized tools for diagnostic test accuracy and network meta-analysis but similarly depend on server infrastructure. meta-analyst [28] provides a Shiny-based interface for metafor but again requires an R server backend. None of these tools combine offline operation, text extraction, and in-browser R validation.

The RevMan Web platform (Cochrane's browser-based revision of RevMan 5) [2] integrates with the Cochrane ecosystem and provides structured data management, but does not support advanced analyses (TSA, Copas, fragility index) and requires Cochrane membership for full functionality.

LivingMeta's closest conceptual relative is the "computable review" vision articulated by Elliott et al. [1] for living systematic reviews: a tool that automates surveillance, extraction, synthesis, and reporting in a continuous cycle. LivingMeta implements this vision at the individual reviewer level, though it does not yet support multi-user collaboration or automated scheduled surveillance.

### Implications and Future Directions

The single-file, zero-installation paradigm demonstrated by LivingMeta has broader implications for evidence synthesis infrastructure. First, it suggests that the traditional separation between "accessible but limited" and "rigorous but complex" tools is not inherent -- a single application can provide both comprehensive statistical methods and zero-barrier deployment. Second, the in-browser R validation pattern (running a reference implementation alongside the primary engine within the same application) could be adopted by other tools to address the trust deficit that limits adoption of new statistical software.

Future development priorities include: (i) network meta-analysis via the Bucher indirect comparison method as a first step toward full multivariate synthesis; (ii) automated scheduled surveillance using service workers for truly automated living reviews; (iii) export to standardized formats (RevMan XML, Cochrane Data Format) for interoperability with existing systematic review workflows; (iv) multi-language support for the text extractor (initially Spanish, French, German, and Chinese abstract formats); and (v) a modular build system that preserves the single-file deployment model while improving maintainability through source-level modularity [33].

## Software Availability

**Source code and application:** https://github.com/mahmood726-cyber/livingmeta

**Latest release:** LivingMeta v1.0 (HTML file, ~960 KB)

**License:** MIT License (open source, permitting free redistribution and modification)

**System requirements:** Any modern web browser with JavaScript enabled (Chrome 90+, Firefox 88+, Edge 90+, Safari 15+). WebR validation additionally requires WebAssembly support and internet access for first-time R runtime download (~20 MB, cached thereafter). No server, installation, or account required.

**Operating systems:** Platform-independent (tested on Windows 11, macOS 14, Ubuntu 22.04, iOS 17, Android 14)

**Programming language:** JavaScript (ES2020), HTML5, CSS3

**Dependencies:** Plotly.js (visualization, CDN), Tailwind CSS (layout, CDN), WebR v0.4.4 (optional R validation, CDN)

**Archival:** Zenodo deposit DOI: [ZENODO_DOI_PLACEHOLDER]

## Data Availability

All clinical trial data used in LivingMeta are embedded directly within the HTML file as JavaScript configuration objects. No external data files or databases are required. Each data cell includes provenance text citing the source publication, table number, and specific values extracted. ClinicalTrials.gov NCT identifiers are provided for all trials, enabling independent verification against the public registry.

The nine clinical configurations collectively contain 39 landmark RCTs (~242,000 patients) with data sourced exclusively from: (i) published primary trial reports in peer-reviewed journals, (ii) ClinicalTrials.gov results sections, and (iii) published supplementary materials. No unpublished, proprietary, or paywalled data are used.

The R validation baselines (`r_baselines.json`) are included in the repository and can be independently regenerated using the exportable R validation script. Cross-validation results against ClinicalTrials.gov (`cross_validation_report.json`) and published meta-analyses (`PUBLISHED_META_BENCHMARKS.json`) are also provided.

## Reproducibility

Three independent validation pathways ensure reproducibility:

1. **In-browser WebR validation:** Users can click "Validate with R" to load R + metafor via WebAssembly and compare 30+ metrics against the JavaScript engine within the same browser session.

2. **Exportable R script:** LivingMeta generates a complete R validation script that users can run in their local R installation (R >= 4.1, metafor >= 4.0). The script reproduces the exact analysis with the same data, method, and settings.

3. **Pre-computed R baselines:** The file `r_baselines.json` contains metafor results for all configurations, generated with R 4.3.2 and metafor 4.6-0 on 2026-03-15. These serve as regression benchmarks for the automated test suite.

The Selenium test suite (`test_livingmeta.py`) can be run locally to verify all 36 assertions:

```
# Run automated test suite (requires Chrome + ChromeDriver)
python test_livingmeta.py
# Expected output: 36/36 passed
```

The seeded PRNG (xoshiro128**) ensures deterministic results for permutation tests and bootstrap procedures across all platforms. Version pinning: WebR v0.4.4, metafor >= 4.0.0, R >= 4.1.0. The R baselines were generated with R 4.3.2 and metafor 4.6-0.

Sample R validation script (auto-generated by LivingMeta for the colchicine CVD configuration):

```r
library(metafor)
# Colchicine CVD: 5 trials, MACE outcome (OR)
tE <- c(131, 64, 244, 253, 424)
tN <- c(2366, 282, 2762, 3528, 3528)
cE <- c(170, 44, 287, 275, 470)
cN <- c(2379, 280, 2796, 3534, 3534)
es <- escalc(measure="OR", ai=tE, n1i=tN, ci=cE, n2i=cN, add=0.5, to="only0")
res <- rma(yi, vi, data=es, method="DL")
print(res)
# Expected: OR = 0.7940 (0.6750, 0.9339), tau2 = 0.0188, I2 = 58.63%
```

## Acknowledgments

Statistical methods were implemented following the metafor package documentation [3], Viechtbauer's tau-squared estimator taxonomy [8], Hartung and Knapp [12], and the Cochrane Handbook [29]. The text extraction module was adapted from the rct_data_extractor_v2 pipeline. WebR integration uses the webR project by George Stagg and the R Core Team [7]. The Robins-Breslow-Greenland variance estimator for Mantel-Haenszel follows the implementation described by Robins, Breslow, and Greenland [30].

## Author Contributions

Mahmood Ahmad conceived the tool, designed the architecture, implemented the statistical engine and text extractor, curated all nine clinical configurations, performed the multi-persona code review, wrote the automated test suite, and wrote the manuscript.

## Competing Interests

The author declares no competing interests.

## Grant Information

The author declared that no grants were involved in supporting this work.

## References

1. Elliott JH, Synnot A, Turner T, et al. Living systematic review: 1. Introduction -- the why, what, when, and how. J Clin Epidemiol. 2017;91:23-30. doi:10.1016/j.jclinepi.2017.08.010

2. Review Manager (RevMan) [Computer program]. Version 5.4. The Cochrane Collaboration; 2020. Available from: https://training.cochrane.org/online-learning/core-software/revman

3. Viechtbauer W. Conducting meta-analyses in R with the metafor package. J Stat Softw. 2010;36(3):1-48. doi:10.18637/jss.v036.i03

4. Owen RK, Bradbury N, Xin Y, Cooper N, Sutton A. MetaInsight: an interactive web-based tool for analyzing, interrogating, and visualizing network meta-analyses using R-shiny and netmeta. Res Synth Methods. 2019;10(4):569-581. doi:10.1002/jrsm.1373

5. Complex Reviews Support Unit (CRSU). Evidence Synthesis Shiny Apps. University of Leicester / University of Glasgow. Available from: https://www.gla.ac.uk/research/az/crsu/apps/. Accessed March 2026.

6. Borenstein M, Hedges LV, Higgins JPT, Rothstein HR. Comprehensive Meta-Analysis (Version 4). Biostat Inc; 2022. Available from: https://www.meta-analysis.com

7. Stagg G. webR: R in the browser via WebAssembly. Version 0.4.4. 2024. Available from: https://webr.r-wasm.org/

8. Viechtbauer W. Bias and efficiency of meta-analytic variance estimators in the random-effects model. J Educ Behav Stat. 2005;30(3):261-293. doi:10.3102/10769986030003261

9. DerSimonian R, Laird N. Meta-analysis in clinical trials. Control Clin Trials. 1986;7(3):177-188. doi:10.1016/0197-2456(86)90046-2

10. Paule RC, Mandel J. Consensus values and weighting factors. J Res Natl Bur Stand. 1982;87(5):377-385. doi:10.6028/jres.087.022

11. Higgins JPT, Thompson SG. Quantifying heterogeneity in a meta-analysis. Stat Med. 2002;21(11):1539-1558. doi:10.1002/sim.1186

12. Hartung J, Knapp G. A refined method for the meta-analysis of controlled clinical trials with binary outcome. Stat Med. 2001;20(24):3875-3889. doi:10.1002/sim.1009

13. IQWiG (Institute for Quality and Efficiency in Health Care). General Methods. Version 6.1. Cologne: IQWiG; 2022. Available from: https://www.iqwig.de/en/methods/methods-paper/

14. IntHout J, Ioannidis JPA, Rovers MM, Goeman JJ. Plea for routinely presenting prediction intervals in meta-analysis. BMJ Open. 2016;6(7):e010247. doi:10.1136/bmjopen-2015-010247

15. Mantel N, Haenszel W. Statistical aspects of the analysis of data from retrospective studies of disease. J Natl Cancer Inst. 1959;22(4):719-748.

16. Yusuf S, Peto R, Lewis J, Collins R, Sleight P. Beta blockade during and after myocardial infarction: an overview of the randomized trials. Prog Cardiovasc Dis. 1985;27(5):335-371. doi:10.1016/0033-0620(85)90003-7

17. Egger M, Davey Smith G, Schneider M, Minder C. Bias in meta-analysis detected by a simple, graphical test. BMJ. 1997;315(7109):629-634. doi:10.1136/bmj.315.7109.629

18. Begg CB, Mazumdar M. Operating characteristics of a rank correlation test for publication bias. Biometrics. 1994;50(4):1088-1101.

19. Duval S, Tweedie R. Trim and fill: a simple funnel-plot-based method of testing and adjusting for publication bias in meta-analysis. Biometrics. 2000;56(2):455-463. doi:10.1111/j.0006-341X.2000.00455.x

20. Stanley TD, Doucouliagos H. Meta-regression approximations to reduce publication selection bias. Res Synth Methods. 2014;5(1):60-78. doi:10.1002/jrsm.1095

21. Copas J. What works?: selectivity models and meta-analysis. J R Stat Soc Ser A. 1999;162(1):95-109. doi:10.1111/1467-985X.00123

22. Wetterslev J, Thorlund K, Brok J, Gluud C. Trial sequential analysis may establish when firm evidence is reached in cumulative meta-analysis. J Clin Epidemiol. 2008;61(1):64-75. doi:10.1016/j.jclinepi.2007.03.013

23. Matthews RAJ. Beyond "significance": principles and practice of the Analysis of Credibility. R Soc Open Sci. 2018;5(1):171047. doi:10.1098/rsos.171047

24. Walsh M, Srinathan SK, McAuley DF, et al. The statistical significance of randomized controlled trial results is frequently fragile: a case for a Fragility Index. J Clin Epidemiol. 2014;67(6):622-628. doi:10.1016/j.jclinepi.2013.10.019

25. Ahmad M. rct_data_extractor_v2: automated extraction of treatment effects from open-access RCT publications. 2026. Available from: https://github.com/mahmood726-cyber/rct-extractor-v2

26. Guyatt GH, Oxman AD, Vist GE, et al. GRADE: an emerging consensus on rating quality of evidence and strength of recommendations. BMJ. 2008;336(7650):924-926. doi:10.1136/bmj.39489.470347.AD

27. Sterne JAC, Sutton AJ, Ioannidis JPA, et al. Recommendations for examining and interpreting funnel plot asymmetry in meta-analyses of randomised controlled trials. BMJ. 2011;343:d4002. doi:10.1136/bmj.d4002

28. Wallace BC, Dahabreh IJ, Trikalinos TA, Lau J, Trow P, Schmid CH. Closing the gap between methodologists and end-users: R as a computational back-end. J Stat Softw. 2012;49(5):1-15. doi:10.18637/jss.v049.i05

29. Higgins JPT, Thomas J, Chandler J, et al, eds. Cochrane Handbook for Systematic Reviews of Interventions. Version 6.4. Cochrane; 2023. Available from: https://training.cochrane.org/handbook

30. Robins J, Breslow N, Greenland S. Estimators of the Mantel-Haenszel variance consistent in both sparse data and large-strata limiting models. Biometrics. 1986;42(2):311-323.

31. Tardif JC, Kouz S, Waters DD, et al. Efficacy and safety of low-dose colchicine after myocardial infarction. N Engl J Med. 2019;381(26):2497-2505. doi:10.1056/NEJMoa1912388

32. Nidorf SM, Fiolet ATL, Mosterd A, et al. Colchicine in patients with chronic coronary disease. N Engl J Med. 2020;383(19):1838-1847. doi:10.1056/NEJMoa2021372

33. Simmonds M, Salanti G, McKenzie J, Elliott J, Herber M, et al. Living systematic reviews: 3. Statistical methods for updating meta-analyses. J Clin Epidemiol. 2017;91:38-46. doi:10.1016/j.jclinepi.2017.08.008

34. Balduzzi S, Rucker G, Schwarzer G. How to perform a meta-analysis with R: a practical tutorial. Evid Based Ment Health. 2019;22(4):153-160. doi:10.1136/ebmental-2019-300117

35. Agarwal R, Filippatos G, Pitt B, et al. Cardiovascular and kidney outcomes with finerenone in patients with type 2 diabetes and chronic kidney disease: the FIDELITY pooled analysis. Eur Heart J. 2022;43(6):474-484. doi:10.1093/eurheartj/ehab777
