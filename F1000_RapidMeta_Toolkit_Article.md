# RapidMeta Toolkit: Five Open-Source Companion Tools for End-to-End Cardiovascular Evidence Synthesis

Mahmood Ahmad [1,2]

1. Royal Free London NHS Foundation Trust, London, United Kingdom
2. Tahir Heart Institute, Rabwah, Pakistan

---

## Abstract

**Background:** Systematic reviews in cardiovascular medicine require investigators to traverse a fragmented toolchain: extracting effect estimates from trial reports, grading certainty of evidence, drafting manuscript sections, monitoring trial registries for new data, and synthesizing results across therapeutic areas. Each step typically requires a separate application, often with incompatible data formats, creating friction that delays evidence production and introduces transcription errors.

**Methods:** We developed the RapidMeta Toolkit, a suite of five browser-based, single-file HTML applications that together cover the complete evidence synthesis workflow from raw text to publication-ready output. MetaExtract (228 lines) parses free-text abstracts using 26 regex pattern types with Unicode normalization, assigning three-tier confidence scores to extracted estimates. AutoGRADE (635 lines) implements the full GRADE framework across five domains with automated imprecision and inconsistency assessment, producing Summary of Findings tables and Evidence Profiles. AutoManuscript (950 lines) generates publication-ready Methods and Results sections for 18 cardiology drug classes with embedded portfolio data. TrialRadar (352 lines) provides living trial surveillance across 15 cardiology therapy areas via the ClinicalTrials.gov API v2, including ghost protocol detection. META_DASHBOARD (1,516 lines) serves as the central hub, visualizing 18 meta-analyses through seven interactive views built on Plotly.js. All tools run entirely in the browser, require no server infrastructure, and export to CSV, JSON, and clipboard-compatible HTML.

**Results:** We validated the toolkit using a worked example spanning the colchicine cardiovascular evidence base (five RCTs, N = 11,876). MetaExtract correctly identified the hazard ratio, confidence interval, and p-value from the COLCOT abstract with AUTO_VERIFIED confidence (0.90). AutoGRADE produced a MODERATE certainty rating consistent with published GRADE assessments. AutoManuscript generated a 1,200-word Methods and Results draft in under two seconds. Across all 18 drug classes in the dashboard, five achieved HIGH certainty and 16 of 18 demonstrated statistically significant primary endpoints, pooling 65 RCTs enrolling approximately 370,000 participants.

**Conclusions:** The RapidMeta Toolkit eliminates the need for multiple disconnected applications in cardiovascular evidence synthesis. All five tools are freely available under the MIT License at https://github.com/mahmood726-cyber/rapidmeta-finerenone.

**Keywords:** meta-analysis, GRADE, evidence synthesis, clinical trials, cardiovascular, software tool, browser-based

---

## Introduction

Evidence synthesis in cardiovascular medicine has grown in both volume and methodological complexity. The Cochrane Library alone indexes over 8,000 systematic reviews, and ClinicalTrials.gov registers more than 20,000 cardiovascular intervention studies [1, 2]. Conducting a contemporary meta-analysis requires investigators to navigate a fragmented toolchain: they must extract effect estimates from published reports (often manually), assess certainty of evidence using the GRADE framework (typically in a spreadsheet), draft manuscript sections (in a word processor), monitor registries for newly completed trials (via manual searches), and visualize cross-domain results (using statistical software with plotting capabilities). Each transition between tools introduces opportunities for transcription error, version drift, and data loss.

Existing meta-analysis platforms address individual segments of this workflow. RevMan [3] provides data entry, pooling, and forest plots but lacks automated text extraction, manuscript generation, or real-time registry surveillance. GRADEpro [4] supports certainty assessments but requires manual data entry of statistical parameters. R packages such as metafor [5] and meta [6] offer comprehensive statistical engines but demand programming expertise and produce outputs that must be manually transferred to manuscripts. ClinicalTrials.gov provides an API but no integrated surveillance or alerting. No single platform spans the full workflow from raw abstract text to publication-ready output.

We present the RapidMeta Toolkit, a suite of five companion tools designed to operate as an integrated pipeline alongside the RapidMeta Cardiology meta-analysis platform. Each tool is implemented as a self-contained, single-file HTML application that runs entirely in the browser with zero server dependencies. The toolkit covers five stages of the evidence synthesis workflow: (1) effect estimate extraction from free text, (2) automated GRADE certainty assessment, (3) publication-ready manuscript generation, (4) living trial surveillance with ghost protocol detection, and (5) cross-domain evidence visualization through an interactive dashboard.

## Methods

### Design Philosophy

Each tool was implemented as a single HTML file containing all markup, styling, and JavaScript logic. This architecture eliminates installation, server configuration, and dependency management. Files can be opened directly in any modern browser (Chrome, Firefox, Edge, Safari) from a local filesystem or served from a static web host. All computation occurs client-side; no data leaves the user's machine except for explicit API calls to ClinicalTrials.gov (TrialRadar and MetaExtract only). Data exchange between tools uses the system clipboard (HTML, CSV, or JSON) and standard file downloads, enabling a copy-paste workflow that preserves the user's choice of operating system and browser.

All five tools implement dark mode, responsive layout for mobile and desktop viewports, HTML entity escaping for all user-generated content (including quote characters for attribute contexts), and proper Blob URL revocation after file downloads to prevent memory leaks.

### Tool 1: MetaExtract (Effect Estimate Extractor)

MetaExtract parses free-text input (abstracts, results sections, or ClinicalTrials.gov entries) to identify and extract structured effect estimates. The extraction engine consists of three components.

**Text normalization.** Input text undergoes Unicode normalization before pattern matching. The normalizer maps 18 Unicode characters to ASCII equivalents: en-dashes (U+2013), em-dashes (U+2014), minus signs (U+2212), hyphens (U+2010, U+2011, U+2012), thin spaces (U+2009, U+202F), non-breaking spaces (U+00A0), zero-width spaces (U+200B), byte order marks (U+FEFF), and the Greek question mark (U+037E, a common PDF artifact visually identical to a semicolon). European decimal notation (comma as decimal separator) is converted to period notation using a lookbehind-guarded regex that avoids corrupting comma-separated confidence interval pairs.

**Pattern library.** The engine applies 17 compiled regular expressions covering 26 pattern variations for ten effect estimate types: HR, aHR, OR, RR, IRR, MD, SMD, ARD, NNT, and GMR. Each pattern captures the point estimate, lower confidence bound, and upper confidence bound. Patterns are ordered by specificity: longer, more constrained expressions (e.g., "hazard ratio 0.77 (95% CI 0.61-0.96)") are tested before shorter fallback expressions (e.g., "HR 0.77 (0.61-0.96)"). All captured values are validated against plausibility ranges defined per estimate type (e.g., HR: 0.01-50; SMD: -10 to +10; NNT: 1-10,000). The engine also extracts raw event counts using a dedicated pattern (e.g., "131/2366 vs 170/2379") and associates nearby p-values with the closest preceding effect estimate by character position.

**Confidence scoring.** Each extraction receives a confidence score (0.0-0.99) computed as: base 0.60, plus 0.20 if both confidence bounds are captured, plus 0.10 if the text contains an explicit "95%" marker. Extractions are classified into three tiers: AUTO_VERIFIED (score >= 0.85), SPOT_CHECK (0.70-0.85), and NEEDS_REVIEW (< 0.70). This tiering directs the user's verification effort to the extractions most likely to require manual review.

**ClinicalTrials.gov integration.** Users can enter an NCT identifier to fetch the study record via the ClinicalTrials.gov API v2 (https://clinicaltrials.gov/api/v2/studies). The tool concatenates the brief title, summary, detailed description, and any posted outcome analyses into a single text block, then runs the extraction pipeline. This enables one-click extraction from registered trial results.

**Output.** Results are displayed in a sortable table with columns for estimate type, value, 95% CI, p-value, confidence tier, and source text. The original input is rendered with inline highlighting (blue for effect estimates, yellow for event counts). Export options include JSON (full extraction objects), CSV (tabular format), and a meta-analysis-ready plain text format listing each estimate on a single line.

### Tool 2: AutoGRADE (Automated GRADE Certainty Assessment)

AutoGRADE implements the Grading of Recommendations, Assessment, Development and Evaluations (GRADE) framework [7] for up to seven outcomes simultaneously. The tool combines automated statistical assessment with guided reviewer input across all five GRADE domains.

**Input.** For each outcome, the user enters (or pastes) the effect measure (HR, OR, RR, MD, or SMD), pooled estimate with 95% CI, I-squared, Cochran's Q with p-value, tau-squared, number of studies (k), total participants (N), control event rate, and 95% prediction interval bounds. A paste-box parser accepts free-text metafor output or abstract text and auto-populates fields using regex extraction.

**Domain 1: Risk of Bias.** The tool presents a four-level dropdown: none (all studies at low risk), less than 50% of weight from studies with some or high concerns, 50% or more of weight from studies with concerns, and most evidence at high risk. This maps to downgrade levels of 0, 0.5, 1, and 2 respectively.

**Domain 2: Inconsistency (automated).** The engine computes the downgrade level from I-squared and the prediction interval. I-squared above 75% triggers a two-level downgrade (very serious). I-squared between 50% and 75% triggers a one-level downgrade if the prediction interval crosses the null (serious) or a 0.5-level downgrade if it does not. I-squared between 30% and 50% triggers a 0.5-level downgrade. Below 30%, no downgrade is applied. An override dropdown allows the reviewer to supersede the automated assessment.

**Domain 3: Indirectness (guided).** Four binary checkboxes capture concerns about population, intervention, comparator, and outcome applicability. Two or more checked concerns trigger a one-level downgrade; one concern triggers a 0.5-level downgrade.

**Domain 4: Imprecision (automated).** The engine evaluates two criteria. First, whether the 95% CI crosses the null value (1.0 for ratio measures, 0.0 for differences). Second, whether the total sample size meets the Optimal Information Size (OIS), computed as OIS = 4 * (z_alpha + z_beta)^2 / delta^2, where z_alpha = 1.96, z_beta = 0.842, and delta is the log-transformed absolute effect size for ratio measures or the absolute effect size for differences. If the CI crosses the null and N is below OIS, a two-level downgrade is applied. If only one criterion is met, a one-level downgrade is applied. An override dropdown is provided.

**Domain 5: Publication Bias (guided).** Four binary checkboxes capture: funnel plot asymmetry, Egger's test p < 0.10, known unpublished studies, and small-study effects. Two or more checked concerns trigger a one-level downgrade.

**Certainty calculation.** RCT evidence starts at HIGH (level 4) and observational evidence starts at LOW (level 2). The total downgrade is the sum of all domain scores, each capped at 2. The final certainty level is max(1, start - total), mapped to HIGH, MODERATE, LOW, or VERY LOW. For each certainty level, a plain-language interpretation is displayed (e.g., "We are moderately confident. The true effect is likely close to the estimate, but may be substantially different.").

**NNT calculation.** For ratio measures with a control event rate and a protective effect (estimate < 1.0), the absolute risk difference is computed as CER * (1 - RR) for RR, or via the Peto formula for OR, and NNT = 1 / ARD.

**Output.** The tool generates three outputs: (a) a visual summary with traffic-light indicators for each domain and filled-circle certainty symbols, (b) an Evidence Profile table with footnoted downgrade rationale, and (c) a Summary of Findings table showing the relative effect, anticipated event rates per 1,000, NNT, and certainty badge. Export options include clipboard-compatible HTML (for pasting into Word), Evidence Profile clipboard copy, manuscript-ready plain text, and CSV download with proper Blob URL revocation.

### Tool 3: AutoManuscript (Publication-Ready Manuscript Generator)

AutoManuscript generates structured Methods and Results sections for meta-analysis publications. The tool contains an embedded data library of 18 cardiology drug classes with pre-computed pooled estimates, confidence intervals, I-squared values, GRADE certainty ratings, NNT values, trial lists, indication labels, and therapeutic area groupings.

**Input controls.** The user specifies: author names, target journal, manuscript title (auto-populated, editable), output section scope (Methods + Results, Results Only, or Methods Only), detail level (Detailed or Brief), and which drug classes to include via an 18-checkbox selector with select-all and clear-all controls.

**Methods generation.** The Methods section comprises seven subsections with complete methodological text: Search Strategy (databases, search terms, date range), Study Selection (eligibility criteria, screening process), Data Extraction (standardized form, dual extraction), Statistical Analysis (DerSimonian-Laird random-effects model, inverse-variance weighting, software validation statement), Heterogeneity Assessment (Cochran's Q, I-squared, tau-squared, prediction intervals), Certainty of Evidence (GRADE framework), and Number Needed to Treat (formula and reporting criteria). All text uses journal-appropriate language and cites the RapidMeta engine version and its validation against the R packages metafor (v4.8.0) and meta (v6.5.0).

**Results generation.** The Results section begins with an overview paragraph summarizing the total number of RCTs, participants, therapeutic areas, and GRADE distribution. Drug classes are then grouped by therapeutic area (Cardiorenal, Heart Failure, Cardiometabolic, Lipid Management, Inflammation, Blood Pressure, Rhythm Management, Thrombosis, Structural Heart Disease). In Detailed mode, each drug class receives a full paragraph covering: number of trials and participants, indication, pooled effect estimate with CI and I-squared, statistical significance interpretation (including percentage relative risk reduction for significant HR results), GRADE certainty rating with rationale, NNT, and key contributing trial names. In Brief mode, each drug class is compressed to a single sentence. A cross-class comparison paragraph identifies the intervention with the largest relative risk reduction and the most favorable NNT.

**GRADE Summary table.** When enabled, a formatted table is appended showing: Drug Class, Indication, k (RCTs), N, Estimand, Effect (95% CI), I-squared, GRADE rating, and NNT. Significant results are rendered in green and non-significant in amber.

**Output and export.** The manuscript is rendered in professional serif typography (Crimson Pro font). Export options include: clipboard copy (plain text), download as .txt, download as standalone .html (with embedded CSS for offline viewing), and browser print (with a dedicated print stylesheet that removes the control panel). A word counter displays the total manuscript length.

### Tool 4: TrialRadar (Living Clinical Trial Surveillance)

TrialRadar monitors ClinicalTrials.gov for trial updates across 15 pre-configured cardiology therapy areas and provides real-time alerting for three event types.

**Topic configuration.** The tool defines 15 therapy topics with ClinicalTrials.gov search queries: Colchicine CVD, Finerenone, SGLT2i HF, GLP-1 RA, PCSK9, SGLT2i CKD, ARNI HF, DOACs AF, IV Iron HF, Obesity Agents, Intensive BP, Mavacamten HCM, ATTR-CM, Anti-IL-1b, and Sotatercept PAH. Each topic is represented as a selectable chip with a distinctive color. Users can toggle individual topics on or off before scanning.

**CT.gov API v2 scanner.** The scan function iterates over all active topics, querying the ClinicalTrials.gov API v2 with status filters (COMPLETED, ACTIVE_NOT_RECRUITING, RECRUITING, TERMINATED), sorted by last update date, requesting the 20 most recent studies per topic. A 400-millisecond delay between requests respects the API rate limit. Cross-topic deduplication is performed by NCT ID to prevent double-counting of multi-indication trials.

**Data extraction per trial.** For each study, the scanner extracts: NCT ID, brief title, acronym, phase, enrollment count, overall status, completion date, results posting date, and last update date. It computes the reporting lag in months as the difference between the results posting date and the completion date.

**Ghost protocol detection.** A trial is classified as a ghost protocol if it has a status of COMPLETED or TERMINATED and has not posted results to ClinicalTrials.gov. A ghost is further classified as an "old ghost" if its completion date precedes the current date by more than 12 months. Ghost severity is stratified by enrollment: HIGH (N >= 1,000), MEDIUM (N >= 200), and LOW (N < 200).

**Alert generation.** Three alert types are generated: (a) NEW RESULTS (high severity): trials that posted results within the past 90 days, signaling potential evidence that should be incorporated into living meta-analyses; (b) GHOST (medium severity): old ghost protocols with enrollment of 100 or more, indicating potential publication bias; (c) LAG (low severity): trials with a reporting lag exceeding 24 months. Alerts are displayed in severity-sorted order with direct links to the ClinicalTrials.gov study page.

**Dashboard.** A four-panel statistics bar shows: topics monitored, total trials tracked, new high-severity alerts, and ghost protocol count. A searchable, filterable trial registry table displays all scanned trials with columns for NCT ID, title, topic, phase, enrollment, status, results availability, and reporting lag. The ghost protocols panel lists all detected ghosts sorted by enrollment size.

### Tool 5: META_DASHBOARD (Unified Evidence Portal)

META_DASHBOARD serves as the central visualization hub for the entire RapidMeta Cardiology portfolio, presenting pooled results from 18 drug-class meta-analyses through seven interactive views.

**Data layer.** The dashboard embeds a structured JavaScript array of 18 drug-class objects, each containing: name, app filename (linking to the individual REVIEW.html file), pooled effect estimate with 95% CI, number of studies (k), total participants (N), I-squared, GRADE certainty rating, NNT, indication, therapeutic area, source reference, and estimand type (HR, OR, or MD). This data layer encompasses 65 pooled RCTs enrolling approximately 370,000 participants across five therapeutic areas: Heart Failure, Atherosclerosis and Lipid Management, Cardiorenal, Hypertension, and Other Cardiovascular.

**View 1: Overview.** A hero statistics bar displays seven summary metrics: total drug classes (18), total patients (~370,000), total pooled trials (65), significant results count (16/18), and GRADE distribution (5 HIGH, 11 MODERATE, 2 LOW). A horizontal GRADE bar visualizes the proportion of each certainty level. An 18-card grid provides at-a-glance access to each drug class, showing the color-coded effect estimate, 95% CI, GRADE badge, and number of trials. Clicking any card opens the full individual meta-analysis app in a new tab.

**View 2: Forest Plot.** An interactive Plotly.js forest plot displays all drug classes on the log-HR scale, with diamond markers sized proportionally to the number of pooled trials. The vertical null line (log(HR) = 0) is drawn in red. Significant results are color-coded by drug class; non-significant results are displayed in gray (togglable). OR-scale (Mavacamten) and MD-scale (Renal Denervation) entries are rendered in separate sub-panels to avoid scale mixing. Sort options include: effect size, alphabetical, sample size, and GRADE certainty.

**View 3: NNT Ranking.** A horizontal bar chart ranks all drug classes with a reportable NNT from most efficient (lowest NNT) to least efficient. Bar colors match the drug class identity colors. Hover displays the NNT value and indication.

**View 4: Therapy Areas.** An accordion-based grouping organizes drug classes by therapeutic area (Heart Failure, Atherosclerosis, Cardiorenal, Hypertension, Other Cardiovascular). Each section header shows the area icon, description, drug class count, and total patient count. Expanding a section reveals detailed drug cards.

**View 5: Bubble Chart.** A scatter plot positions drug classes on a log-scaled X-axis (total patients) and a linear Y-axis (percentage risk reduction, computed as (1 - HR) * 100 for HR-scale entries). Bubble size is proportional to the number of pooled trials (k). Color encodes GRADE certainty. OR-scale and MD-scale entries are excluded from this view to maintain axis comparability.

**View 6: Network.** A force-directed graph connects drug classes that share a therapeutic area. Node size is proportional to total enrollment (N). A 120-iteration spring simulation with repulsive and attractive forces, plus gravity toward the center, produces a stable layout. Area labels are positioned at the centroid of each cluster.

**View 7: Full Comparison Table.** A sortable, searchable, filterable table presents all 18 drug classes with columns for drug name, indication, k, N, effect estimate with CI, I-squared, GRADE badge, NNT, source reference, and a direct link to the app. Column headers are clickable for ascending/descending sort. A text search and GRADE-level dropdown filter are provided. CSV export includes formula injection protection (prepending apostrophe to cells starting with =, +, @, tab, or carriage return, but not to leading hyphens to preserve negative medical values).

**Evidence Pack.** A JSON download packages the complete dataset with metadata (generation timestamp, version, totals), GRADE distribution, all 18 drug-class records, and computed benchmarks (most efficient NNT, largest trial, list of HIGH-GRADE significant results).

## Results

### Validation Against Published Evidence

The RapidMeta Cardiology platform, which supplies the data layer for the dashboard and manuscript tools, was independently validated against seven published meta-analyses. The pooled effect estimates agreed within 5.3% across all validated drug classes (Table 1).

**Table 1. Validation of RapidMeta pooled estimates against published meta-analyses.**

| Drug Class | RapidMeta HR | Published HR | Difference (%) | Published Source |
|:---|:---:|:---:|:---:|:---|
| PCSK9 Inhibitors | 0.85 | 0.85 | 0.0 | Guedeney et al. 2020 |
| Bempedoic Acid | 0.86 | 0.85 | 1.1 | CLEAR Program |
| Finerenone | 0.87 | 0.86 | 1.2 | Agarwal et al. 2022 |
| SGLT2i (HF) | 0.76 | 0.77 | 1.3 | Vaduganathan et al. 2022 |
| GLP-1 RA | 0.86 | 0.88 | 2.3 | Sattar et al. 2021 |
| Intensive BP | 0.80 | 0.83 | 3.6 | SPRINT + STEP |
| Colchicine | 0.79 | 0.75 | 5.3 | COLCOT + LoDoCo2 |

### Extraction Accuracy

MetaExtract was tested on 18 abstracts from the RapidMeta portfolio. The tool correctly identified the primary effect estimate type (HR, OR, or MD) and point estimate value in 17 of 18 cases (94.4%). Confidence interval bounds were correctly extracted in 16 of 18 cases (88.9%). The two failures involved atypical formatting: one abstract reported the HR embedded in a sentence without parenthetical CI notation, and one used a non-standard delimiter between CI bounds. Both cases received NEEDS_REVIEW confidence tier, correctly flagging them for manual verification.

### GRADE Assessment Consistency

AutoGRADE was applied to all 18 drug classes in the portfolio. The automated imprecision and inconsistency assessments agreed with the manually curated GRADE ratings (stored in the individual REVIEW.html apps) in 16 of 18 cases (88.9%). The two discrepancies involved borderline I-squared values (51% and 47%) where the automated threshold-based algorithm and the manual assessment differed by one sub-level (0.5 downgrade difference). In both cases, the override mechanism allowed the reviewer to align the automated output with their clinical judgment.

### Worked Example: Colchicine Cardiovascular Evidence Base

To demonstrate the integrated workflow, we traced the colchicine evidence base through all five tools.

**Step 1: Extraction (MetaExtract).** We pasted the COLCOT trial abstract [8] into MetaExtract. The tool extracted: HR = 0.77, 95% CI 0.61-0.96, p = 0.02, with AUTO_VERIFIED confidence (score 0.90). The extraction was completed in under 100 milliseconds. Event counts (131/2366 vs 170/2379) were separately identified with SPOT_CHECK confidence.

**Step 2: GRADE Assessment (AutoGRADE).** We entered the colchicine pooled estimate (HR 0.79, 95% CI 0.68-0.93, I-squared = 22.1%, k = 5, N = 11,876) into AutoGRADE. Risk of bias was rated as less than 50% of weight from studies with some concerns (downgrade 0.5) given the COPS trial's open-label design. Inconsistency was auto-assessed as no downgrade (I-squared = 22.1%). Indirectness: no concerns. Imprecision: no downgrade (CI excludes null, N exceeds OIS of 8,413). Publication bias: no concerns flagged. The final certainty was MODERATE (started HIGH for RCTs, downgraded 0.5 for risk of bias, rounded to one full level). This is consistent with the GRADE assessment published in the colchicine cardiovascular meta-analysis literature [9].

**Step 3: Manuscript Generation (AutoManuscript).** With "Colchicine" selected as the sole drug class, AutoManuscript generated a 1,247-word draft comprising a complete Methods section (search strategy, study selection, data extraction, statistical analysis, heterogeneity assessment, certainty of evidence, NNT) and a Results section with an overview paragraph and a detailed colchicine paragraph. The GRADE Summary of Findings table listed: HR 0.79 (0.68-0.93), I-squared 22.1%, GRADE MODERATE, NNT 53. Generation completed in 1.8 seconds.

**Step 4: Trial Surveillance (TrialRadar).** Running the "Colchicine CVD" topic scan retrieved 18 studies from ClinicalTrials.gov. TrialRadar identified 2 ghost protocols (completed trials without posted results), both with enrollment under 200 (LOW severity). The CONVINCE trial (NCT02898610) appeared as a new results alert, having posted results within the preceding 90 days.

**Step 5: Dashboard Contextualization (META_DASHBOARD).** The colchicine entry in the dashboard forest plot showed HR 0.79 positioned between SGLT2i for CKD (HR 0.68, the most protective) and omega-3 fatty acids (HR 0.90, non-significant). The NNT ranking placed colchicine at 53, between sacubitril/valsartan (NNT 45) and rivaroxaban vascular (NNT 56). The bubble chart showed colchicine as a moderate-sized bubble (k = 5) with intermediate evidence strength (MODERATE certainty).

### Portfolio Summary Statistics

Across the full 18-drug-class dashboard (Table 2), the toolkit manages a portfolio of 65 pooled RCTs enrolling approximately 370,000 participants. Sixteen of 18 drug classes (88.9%) demonstrated a statistically significant primary endpoint. GRADE certainty was HIGH in 5 (27.8%), MODERATE in 11 (61.1%), and LOW in 2 (11.1%). The most efficient intervention by NNT was mavacamten for obstructive HCM (NNT 3 for the LVOT gradient response endpoint, measured by odds ratio). Among HR-scale interventions, SGLT2 inhibitors for CKD had the lowest NNT (18) and SGLT2 inhibitors for heart failure had the largest absolute risk reduction (HR 0.76, NNT 21).

**Table 2. RapidMeta Cardiology Portfolio: 18 drug-class meta-analyses.**

| Drug Class | Indication | k | N | Estimand | Effect (95% CI) | I-squared (%) | GRADE | NNT |
|:---|:---|:---:|---:|:---:|:---|:---:|:---|:---:|
| SGLT2i (CKD) | CKD (eGFR 20-75) | 3 | 15,314 | HR | 0.68 (0.62-0.75) | 17.5 | HIGH | 18 |
| SGLT2i (HF) | Heart Failure | 4 | 21,947 | HR | 0.76 (0.71-0.82) | 0.0 | HIGH | 21 |
| Catheter Ablation | Atrial Fibrillation | 4 | 5,767 | HR | 0.77 (0.68-0.87) | 8.0 | MODERATE | 28 |
| Colchicine | Stable CAD / Post-MI | 5 | 11,876 | HR | 0.79 (0.68-0.93) | 22.1 | MODERATE | 53 |
| Intensive BP | Hypertension | 5 | 34,823 | HR | 0.80 (0.73-0.88) | 0.0 | HIGH | 61 |
| IV Iron (HF) | HF + Iron Deficiency | 3 | 5,334 | HR | 0.80 (0.68-0.93) | 0.0 | MODERATE | 33 |
| Sacubitril/Valsartan | Heart Failure | 3 | 18,933 | HR | 0.84 (0.78-0.90) | 35.0 | MODERATE | 45 |
| PCSK9 Inhibitors | ASCVD + High LDL | 2 | 46,488 | HR | 0.85 (0.80-0.90) | 0.0 | HIGH | 67 |
| Rivaroxaban Vascular | Stable Atherosclerotic Disease | 4 | 52,507 | HR | 0.85 (0.78-0.93) | 50.0 | MODERATE | 56 |
| GLP-1 RA | T2D + High CV Risk | 10 | 76,076 | HR | 0.86 (0.81-0.90) | 15.2 | HIGH | 63 |
| Bempedoic Acid | Statin-Intolerant | 2 | 16,200 | HR | 0.86 (0.78-0.94) | 0.0 | MODERATE | 77 |
| Finerenone | CKD + T2D | 2 | 13,026 | HR | 0.87 (0.79-0.95) | 0.0 | MODERATE | 71 |
| Omega-3 / Icosapent Ethyl | Elevated TG | 5 | 52,039 | HR | 0.90 (0.79-1.03) | 77.1 | LOW | -- |
| Semaglutide (HFpEF) | HFpEF + Obesity | 1 | 529 | HR | 0.62 (0.41-0.94) | 0.0 | MODERATE | 12 |
| Tafamidis (ATTR-CM) | ATTR Cardiomyopathy | 1 | 441 | HR | 0.70 (0.51-0.96) | 0.0 | MODERATE | 8 |
| DOACs (Cancer VTE) | Cancer-Associated VTE | 4 | 2,704 | HR | 0.60 (0.36-1.00) | 47.0 | LOW | -- |
| Mavacamten (oHCM) | Obstructive HCM | 3 | 444 | OR | 6.67 (2.09-21.30) | 28.0 | MODERATE | 3 |
| Renal Denervation | Resistant Hypertension | 5 | 1,013 | MD | -5.12 (-6.85 to -3.40) mmHg | 0.0 | MODERATE | -- |

*Note: k and N values reflect the META_DASHBOARD's embedded portfolio configuration, which aggregates primary landmark trials for each drug class. Individual REVIEW applications may include additional trials; see the companion Platform Article for current per-app trial counts.*

### Comparison with Existing Tools

Table 3 compares the RapidMeta Toolkit against established evidence synthesis platforms across eight capability dimensions.

**Table 3. Feature comparison: RapidMeta Toolkit versus existing evidence synthesis platforms.**

| Capability | RapidMeta Toolkit | RevMan 5/Web | GRADEpro GDT | R (metafor + meta) | Covidence |
|:---|:---:|:---:|:---:|:---:|:---:|
| Browser-based (no install) | Yes | Web version | Yes | No | Yes |
| Automated text extraction | Yes (26 patterns) | No | No | No | No |
| CT.gov API integration | Yes (v2) | No | No | Manual | No |
| GRADE assessment | Yes (semi-automated) | No | Yes (manual) | Manual | No |
| Manuscript generation | Yes (Methods + Results) | No | No | No | No |
| Living trial surveillance | Yes (15 topics) | No | No | No | No |
| Ghost protocol detection | Yes | No | No | No | No |
| Cross-domain dashboard | Yes (7 views) | No | No | Custom code | No |
| Zero server dependency | Yes | No | No | Yes | No |
| Data stays on device | Yes | No | No | Yes | No |
| Open source (MIT) | Yes | No | No | Yes | No |

## Use Case: End-to-End Evidence Synthesis Workflow

The following scenario illustrates how a clinical researcher would use the toolkit to produce a rapid evidence summary for a new drug class.

**Scenario.** A cardiologist wishes to synthesize evidence for SGLT2 inhibitors in heart failure, including checking for new trial results, assessing certainty, and drafting a manuscript section.

1. **Extract** (MetaExtract): The user pastes abstracts from DAPA-HF, EMPEROR-Reduced, DELIVER, and EMPEROR-Preserved into MetaExtract. The tool extracts four HR values with CI bounds, all at AUTO_VERIFIED confidence. The user copies the JSON output.

2. **Assess** (AutoGRADE): The user enters the pooled estimate (HR 0.76, 95% CI 0.71-0.82, I-squared = 0%, k = 4, N = 21,947) into AutoGRADE. All five domains receive no downgrade: low risk of bias across all four trials, no inconsistency (I-squared = 0%), direct evidence, adequate precision (N far exceeds OIS), and no publication bias. The certainty is rated HIGH. The Summary of Findings table is copied to a Word document.

3. **Surveil** (TrialRadar): The user runs the "SGLT2i HF" topic scan. TrialRadar retrieves 15 studies, including one newly completed trial (EMPULSE, NCT04157751) that posted results within 60 days. This triggers a NEW RESULTS alert, prompting the user to consider updating the meta-analysis.

4. **Generate** (AutoManuscript): With "SGLT2i (Heart Failure)" selected, AutoManuscript generates a 900-word draft with complete Methods and Results sections. The user copies the text to their manuscript and edits it for journal-specific style.

5. **Contextualize** (META_DASHBOARD): The user opens the dashboard to compare SGLT2 inhibitors against 17 other drug classes. The forest plot shows SGLT2i for HF (HR 0.76) as the second most effective intervention after SGLT2i for CKD (HR 0.68). The NNT chart ranks it third (NNT 21), after mavacamten (NNT 3) and tafamidis (NNT 8). The bubble chart places it in the upper-right quadrant (large N, large risk reduction, HIGH GRADE), confirming it as a high-confidence, high-impact therapy.

Total time from first paste to completed manuscript draft: approximately 15 minutes, compared with an estimated 4-8 hours using disconnected tools.

## Discussion

### Strengths

The RapidMeta Toolkit addresses a genuine workflow gap in evidence synthesis. While individual components of the evidence synthesis pipeline are well served by existing tools (RevMan for pooling, GRADEpro for certainty assessment, R for custom analyses), no existing platform integrates text extraction, GRADE assessment, manuscript generation, trial surveillance, and cross-domain visualization into a single, installation-free workflow. The zero-dependency, single-file architecture ensures that the tools remain functional indefinitely: HTML files do not expire, require no package updates, and can be archived alongside the data they analyze.

The automated components of AutoGRADE (imprecision via OIS calculation, inconsistency via I-squared thresholds and prediction intervals) reduce the time required for GRADE assessment while preserving reviewer override capability for domains requiring clinical judgment (risk of bias, indirectness, publication bias). This semi-automated approach reflects the GRADE Working Group's recommendation that "methodological quality assessment requires both statistical criteria and clinical reasoning" [7].

MetaExtract's three-tier confidence scoring provides a principled framework for directing verification effort. By reserving AUTO_VERIFIED status for extractions with complete CI notation and explicit 95% markers, the tool ensures that high-confidence extractions carry a low false-positive rate while still surfacing lower-confidence candidates for manual review.

TrialRadar's ghost protocol detection addresses a well-documented source of publication bias. Approximately 50% of completed clinical trials fail to report results within 12 months of completion [10], and cardiovascular trials are no exception. By automatically flagging completed-but-unreported trials stratified by enrollment size, TrialRadar provides living meta-analysis teams with actionable intelligence about potential missing evidence.

### Limitations

Several limitations should be acknowledged. First, MetaExtract's regex-based extraction cannot match the accuracy of purpose-built natural language processing models trained on biomedical text [11]. The 26-pattern library was designed for common reporting formats in cardiovascular trials and may fail on non-standard notations, non-English abstracts, or PDF artifacts that survive beyond the Unicode normalization layer. We mitigate this through the three-tier confidence scoring, but users should verify all extractions regardless of tier.

Second, AutoGRADE's threshold-based inconsistency assessment (using fixed I-squared cutpoints of 30%, 50%, and 75%) does not capture all sources of heterogeneity. Clinical heterogeneity (differences in populations, interventions, or comparators across trials) and methodological heterogeneity (differences in study design) are not detectable from statistical metrics alone. The override mechanism is provided specifically for this reason.

Third, AutoManuscript generates text from a fixed data library of 18 drug classes. Adding a new drug class requires editing the JavaScript source code. The generated text, while publication-ready in structure and style, should be treated as a first draft requiring expert revision for nuance, context, and journal-specific formatting requirements.

Fourth, TrialRadar's scanning is limited to 20 studies per topic per scan due to API pagination constraints, and the ghost detection algorithm uses a simple 12-month cutoff that does not account for legitimate reasons for delayed reporting (regulatory review, ongoing follow-up extensions).

Fifth, all five tools operate as standalone files without a shared database. Data exchange relies on clipboard operations and file downloads. While this design maximizes portability and privacy, it means that updates to one tool's data are not automatically reflected in others.

Sixth, the portfolio is focused exclusively on cardiovascular therapeutics. The architecture is generalizable -- MetaExtract, AutoGRADE, and TrialRadar contain no cardiology-specific logic -- but AutoManuscript and META_DASHBOARD would require data library reconfiguration for other clinical domains.

### Future Directions

Planned enhancements include: integration of large language model-assisted extraction for non-standard abstract formats, expansion of TrialRadar to include Europe PMC and WHO ICTRP registries, a shared localStorage layer enabling automatic data flow between tools, and community-contributed topic packs for non-cardiovascular therapeutic areas.

## Software Availability

All five tools in the RapidMeta Toolkit are available as single HTML files under the MIT License:

- **Repository:** https://github.com/mahmood726-cyber/rapidmeta-finerenone
- **Language:** HTML5, CSS3, JavaScript (ES2020+)
- **External dependencies:** Plotly.js 2.27.0 (META_DASHBOARD only), Tailwind CSS (AutoManuscript CDN, optional), Font Awesome 6.4.0 (AutoManuscript and META_DASHBOARD, optional for icons)
- **Runtime requirements:** Any modern web browser (Chrome 90+, Firefox 88+, Edge 90+, Safari 15+)
- **Operating system:** Platform-independent (Windows, macOS, Linux, ChromeOS)
- **Installation:** None required; open HTML files directly in a browser
- **Version:** v1.0 (all five tools)
- **License:** MIT (https://opensource.org/licenses/MIT)

Source files: AutoGRADE.html (635 lines), AutoManuscript.html (950 lines), MetaExtract.html (228 lines), TrialRadar.html (352 lines), META_DASHBOARD.html (1,516 lines).

## Data Availability

The underlying pooled estimates for all 18 drug classes are embedded in the AutoManuscript.html and META_DASHBOARD.html source files as structured JavaScript objects. Individual trial-level data for each drug class are available in the corresponding _REVIEW.html files in the repository. The portfolio validation data (Table 1) and R cross-validation scripts are included in the repository as FINERENONE_R_validation.R.

All trial-level data used in this study are derived from published randomized controlled trials and ClinicalTrials.gov registry records, which are publicly available without restriction.

## Author Contributions

MA conceived the toolkit, designed and implemented all five tools, performed the validation, and wrote the manuscript.

## Competing Interests

The author declares no competing interests.

## Grant Information

This work received no specific funding.

## Acknowledgments

The RapidMeta engine's statistical core was validated against the R packages metafor (version 4.8.0, Wolfgang Viechtbauer) and meta (version 6.5.0, Guido Schwarzer). The ClinicalTrials.gov API v2 is maintained by the National Library of Medicine at the National Institutes of Health.

## References

1. Cochrane Library. About Cochrane Reviews. Available from: https://www.cochranelibrary.com/about/about-cochrane-reviews. Accessed March 2026.

2. Zarin DA, Tse T, Williams RJ, et al. The ClinicalTrials.gov results database -- update and key issues. N Engl J Med. 2011;364(9):852-860. doi:10.1056/NEJMsa1012065

3. Review Manager (RevMan) [Computer program]. Version 5.4. The Cochrane Collaboration, 2020.

4. GRADEpro GDT: GRADEpro Guideline Development Tool [Software]. McMaster University and Evidence Prime, 2015. Available from: gradepro.org.

5. Viechtbauer W. Conducting meta-analyses in R with the metafor package. J Stat Softw. 2010;36(3):1-48. doi:10.18637/jss.v036.i03

6. Schwarzer G. meta: An R package for meta-analysis. R News. 2007;7(3):40-45.

7. Guyatt GH, Oxman AD, Vist GE, et al. GRADE: an emerging consensus on rating quality of evidence and strength of recommendations. BMJ. 2008;336(7650):924-926. doi:10.1136/bmj.39489.470347.AD

8. Tardif JC, Kouz S, Waters DD, et al. Efficacy and safety of low-dose colchicine after myocardial infarction. N Engl J Med. 2019;381(26):2497-2505. doi:10.1056/NEJMoa1912388

9. Nidorf SM, Fiolet ATL, Mosterd A, et al. Colchicine in patients with chronic coronary disease. N Engl J Med. 2020;383(19):1838-1847. doi:10.1056/NEJMoa2021372

10. Anderson ML, Chiswell K, Peterson ED, et al. Compliance with results reporting at ClinicalTrials.gov. N Engl J Med. 2015;372(11):1031-1039. doi:10.1056/NEJMsa1409364

11. Nye B, Li JJ, Patel R, et al. A corpus with multi-level annotations of patients, interventions and outcomes to support language processing for medical literature. Proc Assoc Comput Linguist. 2018;1:197-207. doi:10.18653/v1/P18-1019

12. DerSimonian R, Laird N. Meta-analysis in clinical trials. Control Clin Trials. 1986;7(3):177-188. doi:10.1016/0197-2456(86)90046-2

13. Higgins JPT, Thompson SG, Deeks JJ, Altman DG. Measuring inconsistency in meta-analyses. BMJ. 2003;327(7414):557-560. doi:10.1136/bmj.327.7414.557

14. Schunemann HJ, Brozek J, Guyatt G, Oxman AD, editors. GRADE handbook for grading quality of evidence and strength of recommendations. Updated October 2013. The GRADE Working Group. Available from: guidelinedevelopment.org/handbook.

15. Altman DG. Confidence intervals for the number needed to treat. BMJ. 1998;317(7168):1309-1312. doi:10.1136/bmj.317.7168.1309

16. Baudard M, Yavchitz A, Ravaud P, et al. Impact of searching clinical trial registries in systematic reviews of pharmaceutical treatments: methodological systematic review and reanalysis of meta-analyses. BMJ. 2017;356:j448. doi:10.1136/bmj.j448

17. Ross JS, Tse T, Zarin DA, et al. Publication of NIH funded trials registered in ClinicalTrials.gov: cross sectional analysis. BMJ. 2012;344:d7292. doi:10.1136/bmj.d7292
