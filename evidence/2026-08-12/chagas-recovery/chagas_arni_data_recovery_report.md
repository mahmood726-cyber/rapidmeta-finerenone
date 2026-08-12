# Chagas cardiomyopathy ARNI (sacubitril/valsartan) — data recovery report

**Prepared:** 12 August 2026 (overnight run)
**Revised:** 12 August 2026 — JAMA **main text** and **Supplement 3** (`joi250086supp3`, 26 pp.) both obtained and extracted in full.
**Scope:** trial-level outcome data for ARNI vs ACEi in HFrEF due to chronic Chagas cardiomyopathy.
**Standalone document.** Nothing written to `F:\rapidmeta-finerenone`.

---

## 0. Correction to the previous version of this report — read this first

The earlier version of this report recorded the PARACHUTE-HF all-cause mortality HR as `not_computed_reason` and described the JAMA article as needing "institutional access". **Both statements were wrong, and the error was mine.**

- **The article is open access.** It was never paywalled.
- What actually happened is that my fetch tooling was blocked — jamanetwork.com returned a Cloudflare "Validate User" interstitial and PMC returned a Google reCAPTCHA challenge. Those are **bot-mitigation blocks on my retrieval path**, not access restrictions on the source.
- **A tool-access failure is not a data absence.** Recording one as the other is a substantive error: it converts "I could not reach this" into "this does not exist", which is exactly the kind of false negative this whole exercise was meant to eliminate. Every instance of that framing has been removed from this document.
- **The all-cause mortality HR was in main-text Table 2 the entire time**: **HR 0.98 (95% CI 0.77–1.25), P = .88.** It was never in the supplement, and it was never missing.

Two claims from the earlier version that were also wrong, now corrected below:

- I flagged the −41.1% / −1.5% NT-proBNP figures from the Cardiology Trials appraisal as a likely erroneous outlier and told you to use −30.6% / −5.5%. **The appraisal was correct.** Both pairs are real and both are in Table 2: −30.6% / −5.5% are the **medians**, −41.1 / −1.5 are the **means** (SD 72.8 and 66.3). I was right about which to use as the median and wrong to call the other an error.
- I inferred Supplement 3's likely contents from JAMA convention. The inference on *label* was right; the inference that it would hold the mortality HR, the subgroup forest plot and the KM curves was **wrong on two of three**. See §9.

---

## 1. Headline finding

The data was never unavailable. It sits across four open layers, and the two richest — the JAMA main text and Supplement 3 — were reachable by any human with a browser the whole time.

Three trials, not one: **PARACHUTE-HF** (NCT04023227, n=922), **ANSWER-HF** (NCT04853758, n=190), and the **PARADIGM-HF Chagas subgroup** (n=113).

**No digitisation was required anywhere.** Every value in both supplement eFigures is a printed text label; eTable 8 is a table of printed numbers, not a forest plot. The only genuine digitisation target left is main-text Figure 2 C/D/E (KM curves), and only if you want pseudo-IPD.

---

## 2. Identifier resolution (all by live lookup, none from recall)

| Item | Identifier | How resolved | Confirmed record |
|---|---|---|---|
| PARACHUTE-HF registry | **NCT04023227** | ClinicalTrials.gov API search | Novartis, n=922, COMPLETED, `hasResults: true` |
| PARACHUTE-HF primary paper | **PMID 41335448** · DOI `10.1001/jama.2025.19808` · **PMC12676478** | PubMed E-utilities, re-confirmed | JAMA 2026;335(1):49–59. Lopes RD et al. Abstract names NCT04023227 |
| — JAMA article ID | **2842283** | `pii` field on the PubMed record | matches the article URL |
| — Supplement 3 file | **`joi250086supp3`** | supplied by Mahmood; header confirms | "Supplemental Online Content … JAMA. Published online December 3, 2025. doi:10.1001/jama.2025.19808". 26 pp. Author of file properties: Lucas Petri Damiani |
| — Correction notice | article corrected **22 Jan 2026** (coauthor affiliation only) | main text | no data affected |
| PARACHUTE-HF design paper | **PMID 39111953** · DOI `10.1016/j.jchf.2024.05.021` | PubMed | JACC Heart Fail 2024;12(8):1473–1486 |
| PARACHUTE-HF baseline paper | **PMID 40916703** · DOI `10.1002/ejhf.70026` | PubMed | Eur J Heart Fail 2025;27(12):2879–2886 |
| PARACHUTE-HF appraisal | **PMID 41910669** · DOI `10.1007/s10741-026-10617-3` · PMC13035569 | PubMed | Heart Fail Rev 2026;31(1) |
| ANSWER-HF registry | **NCT04853758** | ClinicalTrials.gov API | n=200 target, `hasResults: false` |
| ANSWER-HF primary paper | **PMID 41396086** · DOI `10.1016/j.jacc.2025.10.053` | PubMed | J Am Coll Cardiol 2025;87(10):1220–1232 |
| PARADIGM-HF Chagas subgroup | **PMID 30298996** · DOI `10.1002/ehf2.12355` | DOI resolved live; PMID from publisher `citation_pmid` | ESC Heart Fail 2018;5(6):1069–1071. Open access CC BY-NC |
| PARADIGM-HF parent NCT | **not resolved** | registry search did not return it in-session | **Left blank deliberately.** Resolve live before use |
| Meta-analysis A | **PMID 41941460** · DOI `10.1097/CRD.0000000000001270` | PubMed | Cardiol Rev, 6 Apr 2026, n=1225 |
| Meta-analysis B | **PMID 41923142** · DOI `10.1097/CRD.0000000000001242` | PubMed | Cardiol Rev, 2 Apr 2026, n=1225 |

---

## 3. Source tiers

| Tier | Meaning |
|---|---|
| **T1-MAIN** | Primary publication **main text** — JAMA 2026;335(1):49–59, Table 2 unless otherwise stated |
| **T1-SUPP** | Primary publication **Supplement 3** — `joi250086supp3`, 26 pp., © 2025 AMA, cited by eTable/eFigure number and page |
| **T1-ABS** | Structured abstract of the primary publication |
| **T2-REG** | ClinicalTrials.gov posted results, NCT04023227 |
| **T3-CONF** | ESC press release / ACC news / TCTMD conference report |
| **T4-HTA** | Regulator or HTA document — searched, none exists (§9) |
| **T5-SEC** | Secondary literature: appraisals, mini-reviews, meta-analyses |
| **T6-DIG** | Digitised from figure geometry — **not used anywhere** |

---

## 4. PARACHUTE-HF — design and conduct

**SV** = sacubitril/valsartan, target 200 mg BID (n=462). **ENA** = enalapril, target 10 mg BID (n=460).

| Cell | Value | Tier | Pointer | Read/dig |
|---|---|---|---|---|
| Design | open-label, blinded endpoint adjudication, ITT | T1-MAIN | main text | read |
| Sites / countries | 83 sites; Brazil, Argentina, Colombia, Mexico | T1-MAIN | main text | read |
| Enrolment window | 10 Dec 2019 – 13 Sep 2023 | T1-MAIN/T1-ABS | main text; abstract | read |
| Randomised SV / ENA | 462 / 460 | T1-MAIN, T2-REG | Table 2; CTG `STARTED` | read |
| Median (IQR) follow-up | 25.2 (18.4–33.2) months | T1-MAIN | main text | read |
| Loss to follow-up | none | T1-MAIN | main text | read |
| Withdrew consent, SV / ENA | 2 / 8 | T1-MAIN, T2-REG | main text; CTG `dropWithdraws` | read |
| Mean (SD) age | 64.2 (10.8) y | T1-ABS, T2-REG | abstract; CTG baseline | read |
| Female | 387 (42.0%) | T1-ABS, T2-REG | abstract; CTG baseline | read |
| Mean LVEF | 29.8% | T3-CONF, T5-SEC | ESC PR; EJHF baseline paper | read |
| Median baseline NT-proBNP, SV / ENA | 1801.0 (Q1–Q3 921.5–3685.8), n=460 / 1679.0 (812.0–3220.0), n=457 | **T1-SUPP** | **eTable 5, p. 16** | read |
| Prior HF hospitalisation | 44.4% | T3-CONF | ESC PR | read |
| Completed / not completed, SV | 333 / 129 | T2-REG | CTG participant flow | read |
| Completed / not completed, ENA | 318 / 142 | T2-REG | CTG participant flow | read |
| **Superiority rule (prespecified)** | required **both** win ratio > 1 **and** HR point estimate < 1.0 for CV death **and** for HF hospitalisation | T1-MAIN | main text; also in JACC HF design paper | read |
| Events at stop | 324 actual vs 302 protocol target | T5-SEC / design paper | Heart Fail Rev appraisal; CTG detailed description | read |

### 4.1 Drug exposure and adherence — **new, all T1-SUPP**

| Cell | SV | ENA | Pointer | Read/dig |
|---|---|---|---|---|
| Received ≥1 dose | 462/462 (100.0%) | 460/460 (100.0%) | eTable 2, p. 12 | read |
| Total months on study medication, median (Q1,Q3) | 24.2 (17.2, 32.5) | 20.8 (8.6, 30.2) | eTable 2, p. 12 | read |
| % of total follow-up on drug, mean (SD) | 91.2 (21.6) | 80.8 (32.5) | eTable 2, p. 12 | read |
| **Study drug permanent discontinuation** | **21/462 (4.5%)** | **49/460 (10.7%)** | eTable 2, p. 12 | read |
| — reason: adverse events | 7/21 (33.3%) | 15/49 (30.6%) | eTable 2, p. 12 | read |
| — reason: physician decision | 2/21 (9.5%) | 8/49 (16.3%) | eTable 2, p. 12 | read |
| — reason: subject/guardian decision | 10/21 (47.6%) | 17/49 (34.7%) | eTable 2, p. 12 | read |
| — reason: interruption of visits before EOS | 2/21 (9.5%) | 9/49 (18.4%) | eTable 2, p. 12 | read |
| **At target dose (Level 3) at week 12** | **270/447 (60.4%)** | **271/441 (61.5%)** | **eFigure 1, p. 24**, W12 bars | read (printed label) |

> Dose levels: L1 = enalapril 2.5 mg BID / SV 50 mg BID; L2 = 5 mg BID / 100 mg BID; L3 = 10 mg BID / 200 mg BID.
> The 60.4% / 61.5% pair was previously carried at T5-SEC from the Cardiology Trials appraisal. Now **upgraded to T1-SUPP**, and the denominators are visible for the first time: **447 and 441**, not 462/460.

### 4.2 Background and concomitant therapy — **new, all T1-SUPP (eTable 3, p. 13)**

| Medication | SV baseline | ENA baseline | SV concomitant | ENA concomitant |
|---|---|---|---|---|
| ACE inhibitor | 225/462 (48.7%) | 233/460 (50.7%) | 18/462 (3.9%) | 29/460 (6.3%) |
| ARB | 147/462 (31.8%) | 141/460 (30.7%) | 22/462 (4.8%) | 62/460 (13.5%) |
| Beta-blocker | 419/462 (90.7%) | 420/460 (91.3%) | 424/462 (91.8%) | 429/460 (93.3%) |
| MRA | 337/462 (72.9%) | 341/460 (74.1%) | 365/462 (79.0%) | 364/460 (79.1%) |
| Loop / thiazide diuretic | 328/462 (71.0%) | 317/460 (68.9%) | 359/462 (77.7%) | 359/460 (78.0%) |
| Amiodarone | 148/462 (32.0%) | 141/460 (30.7%) | 181/462 (39.2%) | 171/460 (37.2%) |
| Aspirin | 70/462 (15.2%) | 76/460 (16.5%) | 82/462 (17.7%) | 90/460 (19.6%) |
| Anticoagulants | 210/462 (45.5%) | 205/460 (44.6%) | 241/462 (52.2%) | 244/460 (53.0%) |
| SGLT2 inhibitor | 21/462 (4.5%) | 37/460 (8.0%) | 47/462 (10.2%) | 60/460 (13.0%) |
| Ivabradine | 1/462 (0.2%) | 3/460 (0.7%) | 3/462 (0.6%) | 4/460 (0.9%) |
| Digoxin / digitalis | 1/462 (0.2%) | 2/460 (0.4%) | 3/462 (0.6%) | 6/460 (1.3%) |

> This resolves the vague conference-report statements ("roughly half on an ACE inhibitor, one-third on an ARB, SGLT2i 6.3%") into exact per-arm numerators and denominators. Note the **baseline SGLT2i imbalance: 4.5% SV vs 8.0% ENA**, which no secondary source mentioned.

---

## 5. PARACHUTE-HF — primary endpoint (hierarchical composite, win ratio)

| Cell | Value | Tier | Pointer | Read/dig |
|---|---|---|---|---|
| **Stratified unmatched win ratio** | **1.524 (95% CI 1.282–1.819), P < .001** | **T1-SUPP** | **eFigure 2, p. 26** final box; identical in eTable 4, p. 14. Rounded to 1.52 (1.28–1.82) in main text and abstract | read |
| **Unstratified win ratio** | **1.54 (95% CI 1.34–1.85)** | **T1-MAIN** | Table 2 | read |
| **Total matches** | **101,477** | **T1-SUPP** | **eFigure 2, p. 26** header box: "101,477 matches were made by pairing participants from each group within each stratum (country)"; confirmed eTable 4, p. 14 | read |
| Total wins, SV / ENA (unweighted) | 48,041 (47.3%) / 33,790 (33.3%); ties 19,646 (19.4%) | T1-SUPP | eTable 4, p. 14 overall row | read |
| Total **weighted** wins, SV / ENA | 111.3 / 73.0 | T1-SUPP | eFigure 2, p. 26; eTable 4, p. 14 | read |

### 5.1 Component-specific win ratios — **the single most valuable new finding**

**T1-SUPP, eFigure 2, p. 26.** All values printed as text labels; **read, not digitised.**

| Hierarchy layer | % of decisions | **Win ratio (95% CI)** | SV weighted wins | ENA weighted wins | Ties |
|---|---|---|---|---|---|
| 1. Death due to cardiovascular causes | 46.6% | **1.03 (0.78–1.35)** | 41.5 | 40.5 | 63,384 (62.5%) |
| 2. Hospitalisation due to heart failure | 17.4% | **1.11 (0.71–1.59)** | 17.6 | 16.0 | 49,184 (77.6%) |
| 3. NT-proBNP change at 12 weeks | 36.1% | **3.15 (2.42–4.27)** | 52.2 | 16.0 | 19,646 (39.9%) |
| **Overall** | — | **1.524 (1.282–1.819), p<0.001** | **111.3** | **73.0** | — |

> This quantifies precisely what every appraisal asserted qualitatively. The two clinical layers are essentially null (1.03 and 1.11, both CIs crossing 1); the biomarker layer is 3.15 with a CI nowhere near 1. The headline 1.52 is a weighted blend of two null clinical comparisons and one very large biomarker effect. **The percentage-of-decisions column is what makes this quantitative — the biomarker layer decided 36.1% of all decisions.**

### 5.2 Win ratio by country stratum — **new, T1-SUPP (eTable 4, p. 14)**

| Stratum | Win ratio (95% CI) | SV wins | Ties | ENA wins |
|---|---|---|---|---|
| Brazil | 1.367 (1.103–1.697) | 41,025 (47%) | 16,226 (18.6%) | 30,063 (34.4%) |
| Argentina | 1.893 (1.311–2.826) | 5,880 (48.6%) | 3,117 (25.8%) | 3,099 (25.6%) |
| Colombia | 1.796 (1.042–3.258) | 1,066 (55.1%) | 270 (14%) | 599 (31%) |
| Mexico | 2.521 (0.741–12.857) | 70 (53%) | 33 (25%) | 29 (22%) |

> Method note printed in eTable 4: win ratio uses country as stratum per **Dong et al. (2018)**; 95% CI from **10,000 bootstrap resamples**; weighted wins = wins × (1 / stratum size).

### 5.3 Sensitivity analyses — **new, T1-SUPP**

| Analysis | Win ratio (95% CI) | Pointer |
|---|---|---|
| Per-protocol set (N=450 SV, 447 ENA) | **1.509 (1.273–1.804)** | eTable 6, p. 17 |
| — Brazil | 1.342 (1.081–1.676) | eTable 6, p. 17 |
| — Argentina | 1.904 (1.323–2.806) | eTable 6, p. 17 |
| — Colombia | 1.793 (1.046–3.259) | eTable 6, p. 17 |
| — Mexico | 2.571 (0.680–15.005) | eTable 6, p. 17 |
| **Total death** as first hierarchy (instead of CV death) | **1.471 (1.241–1.752)** | eTable 7, p. 19 |
| — Brazil | 1.376 (1.112–1.705) | eTable 7, p. 19 |
| — Argentina | 1.689 (1.188–2.468) | eTable 7, p. 19 |
| — Colombia | 1.648 (0.961–2.957) | eTable 7, p. 19 |
| — Mexico | 1.744 (0.508–6.929) | eTable 7, p. 19 |

---

## 6. PARACHUTE-HF — clinical outcomes (main-text Table 2, tier-upgraded)

Every row below was previously held at T3-CONF (press release) or T5-SEC. **All now T1-MAIN.** Rates are per 100 patient-years.

| Outcome | SV | ENA | Effect estimate | Pointer |
|---|---|---|---|---|
| **Death from any cause** | **129 (27.9%), 12.9/100py** | **134 (29.1%), 13.5/100py** | **HR 0.98 (95% CI 0.77–1.25), P = .88**; adjusted absolute difference −1.1 (−6.9 to 4.7) | Table 2 |
| **CV death** | 110 (23.8%), 11.0/100py | 117 (25.4%), 11.7/100py | **HR 0.95 (0.73–1.23), P = .70** | Table 2 |
| **First HF hospitalisation** | 102 (22.1%), 11.0/100py | 111 (24.1%), 12.4/100py | **HR 0.92 (0.70–1.20), P = .52**; **subdistribution HR 0.74 (0.49–1.14), P = .17** (Fine–Gray, death as competing risk) | Table 2 |
| **Composite CV death or first HF hosp** | **155 (33.5%), 16.8/100py** | **169 (36.7%), 18.8/100py** | **HR 0.91 (0.73–1.13), P = .40** | Table 2 |
| Sudden death or resuscitated cardiac arrest | 46 (10.0%) | 39 (8.5%) | **HR 1.17 (0.76–1.80), P = .48** | Table 2 |
| ED visits for HF | 23 | 21 | **rate ratio 1.12 (0.48–2.58), P = .80** | Table 2 |
| Days alive and out of hospital at 1 y, mean (SD) | 339 (72), n=461 | 338 (71), n=455 | difference 1.1 (−8.2 to 10.4), P = .82 | Table 2 |
| Recurrent HF hosp + CV death (total events) | 289, 28.9/100py | 316, 31.7/100py | **rate ratio 0.90 (0.63–1.28), P = .56** | Table 2 |
| VF or sustained VT | 42 | 32 | not reported | T2-REG (CTG other outcome) |
| ATP or shock therapies | 17 | 13 | not reported | T2-REG (CTG other outcome) |

**Newly recovered that no prior source carried:** the composite event **counts** (155 / 169), all per-100-patient-year rates, the **Fine–Gray subdistribution HR** for HF hospitalisation, the sudden-death HR, and every P value.

### 6.1 NT-proBNP

| Cell | SV | ENA | Effect | Tier | Pointer |
|---|---|---|---|---|---|
| Week 12, median % change (IQR) | −30.6% (−54.3 to −0.9) | −5.5% (−31.9 to 37.5) | — | T1-MAIN, T1-ABS | Table 2; abstract |
| **Week 12, mean % change (SD)** | **−41.1 (72.8)** | **−1.5 (66.3)** | — | **T1-MAIN** | Table 2 |
| Week 12, n analysed | 417 | 401 | — | T1-MAIN | Table 2 |
| Week 12, median absolute (Q1,Q3) | 1236.0 (557.5, 2608.0) | 1700.0 (732.5, 3531.5) | — | T1-SUPP | eTable 5, p. 16 |
| Week 12, geometric mean (95% CI) | 1164.5 (1020.1–1329.4) | 1507.7 (1318.4–1724.2) | — | T1-SUPP | eTable 5, p. 16 |
| Week 12, geometric mean factor change | 0.62 (0.56–0.69) | 0.91 (0.82–1.01) | **GMR 0.68 (0.62–0.75), P < .001** | T1-MAIN + T1-SUPP | Table 2; eTable 5, p. 16 |
| Week 12, adjusted absolute difference | — | — | **−38.1 (−28.6 to −47.6)** | T1-MAIN | Table 2 |
| **Month 8, n analysed** | **231** | **220** | — | **T1-SUPP** | eTable 5, p. 16 |
| **Month 8, median absolute (Q1,Q3)** | **1139.0 (573.5, 2345.5)** | **1328.0 (586.0, 2549.8)** | — | **T1-SUPP** | eTable 5, p. 16 |
| **Month 8, geometric mean (95% CI)** | **1077.8 (913.2–1272.1)** | **1219.3 (1030.6–1442.6)** | — | **T1-SUPP** | eTable 5, p. 16 |
| **Month 8, geometric mean factor change** | **0.66 (0.55–0.79)** | **0.86 (0.72–1.03)** | **GMR 0.76 (0.66–0.88)** | **T1-SUPP** | eTable 5, p. 16 |

> **The month-8 timepoint is entirely new.** The Heart Failure Reviews appraisal specifically criticised the trial for measuring NT-proBNP only at 12 weeks and called the longer-term trajectory "unknown". It was not unknown — eTable 5 reports month 8, where the ratio attenuates from 0.68 to 0.76 on a much reduced sample (231/220 vs 417/401). That attenuation-on-attrition is worth a sentence in any write-up.
>
> Model note printed in eTable 5: factor change from a linear regression of log(NT-proBNP) adjusted for country and baseline value; geometric means adjusted for country.

---

## 7. PARACHUTE-HF — subgroups (eTable 8, pp. 20–21) — **complete, all printed values, none digitised**

The main text states results "were consistent across all prespecified subgroups (eTable 8 in Supplement 3)". eTable 8 is a **table**, not a forest plot. **No interaction p-values are printed anywhere in it** — that is a genuine reporting gap, not a retrieval failure.

| Subgroup | N | SV wins | Ties | ENA wins | Win ratio (95% CI) |
|---|---|---|---|---|---|
| **Sex** — Male | 535 | 15,812 | 5,698 | 11,120 | 1.540 (1.227–1.934) |
| **Sex** — Female | 387 | 8,813 | 4,061 | 5,827 | 1.571 (1.187–2.094) |
| **Age** — <65 y | 438 | 11,306 | 4,112 | 8,016 | 1.437 (1.118–1.856) |
| **Age** — ≥65 y | 484 | 12,759 | 5,858 | 8,729 | 1.609 (1.263–2.090) |
| **Race** — Caucasian | 502 | 13,632 | 6,751 | 10,143 | 1.413 (1.125–1.797) |
| **Race** — Black | 140 | 2,274 | 599 | 1,957 | 1.160 (0.764–1.803) |
| **Race** — Indigenous | 42 | 117 | 46 | 43 | 2.324 (0.996–5.044) |
| **Race** — Mixed ethnicity | 238 | 3,961 | 1,667 | 2,075 | 1.854 (1.300–2.679) |
| **NYHA** — I or II | 570 | 20,965 | 9,657 | 11,550 | 1.833 (1.470–2.316) |
| **NYHA** — III or IV | 352 | 5,596 | 1,777 | 5,598 | 1.184 (0.904–1.559) |
| **eGFR** — ≥60 | 590 | 16,565 | 8,415 | 11,193 | 1.577 (1.259–1.970) |
| **eGFR** — <60 | 332 | 8,507 | 2,602 | 6,315 | 1.408 (1.075–1.892) |
| **Diabetes** — No | 784 | 34,796 | 14,150 | 23,693 | 1.562 (1.287–1.883) |
| **Diabetes** — Yes | 138 | 1,079 | 443 | 895 | 1.331 (0.838–2.090) |
| **SBP** — < median | 447 | 13,525 | 4,623 | 10,147 | 1.425 (1.119–1.817) |
| **SBP** — ≥ median | 475 | 10,587 | 5,586 | 7,234 | 1.519 (1.194–1.974) |
| **LVEF** — ≤35% | 668 | 26,507 | 8,849 | 19,605 | 1.464 (1.195–1.781) |
| **LVEF** — >35% | 254 | 3,213 | 2,165 | 1,837 | 1.834 (1.291–2.739) |
| **Atrial fibrillation** — No | 641 | 26,364 | 10,547 | 16,629 | 1.711 (1.368–2.097) |
| **Atrial fibrillation** — Yes | 281 | 3,486 | 1,505 | 3,024 | 1.229 (0.896–1.692) |
| **Hypertension** — No | 549 | 20,117 | 6,822 | 12,901 | 1.675 (1.344–2.108) |
| **Hypertension** — Yes | 373 | 6,074 | 3,389 | 5,001 | 1.340 (1.019–1.800) |
| **Prior ACEi/ARB** — No | 195 | 1,678 | 740 | 950 | 2.022 (1.391–3.043) |
| **Prior ACEi/ARB** — Yes | 727 | 32,649 | 12,940 | 23,635 | 1.428 (1.185–1.750) |
| **Prior MRA** — No | 244 | 3,252 | 1,475 | 2,489 | 1.411 (0.996–2.030) |
| **Prior MRA** — Yes | 678 | 26,288 | 10,404 | 17,746 | 1.586 (1.298–1.944) |
| **Prior SGLT2i** — No | 864 | 43,534 | 18,100 | 29,954 | 1.539 (1.288–1.854) |
| **Prior SGLT2i** — Yes | 58 | 111 | 34 | 144 | **0.928 (0.445–1.978)** |
| **Prior HF hosp within 1 y** — No | 642 | 25,707 | 12,008 | 16,093 | 1.684 (1.365–2.096) |
| **Prior HF hosp within 1 y** — Yes | 280 | 3,808 | 948 | 3,196 | 1.289 (0.964–1.740) |
| **Time since HF diagnosis** — ≤1 y | 391 | 7,675 | 3,680 | 4,964 | 1.738 (1.329–2.339) |
| **Time since HF diagnosis** — 1–5 y | 185 | 2,095 | 541 | 1,311 | 1.826 (1.249–2.760) |
| **Time since HF diagnosis** — ≥5 y | 346 | 7,751 | 3,292 | 6,221 | 1.238 (0.925–1.665) |
| **Randomisation date** — before 31 Dec 2021 | 271 | 3,315 | 971 | 3,117 | 1.174 (0.879–1.599) |
| **Randomisation date** — after 1 Jan 2022 | 651 | 27,160 | 11,859 | 17,182 | 1.651 (1.345–2.062) |

Method note printed in eTable 8: "WR estimate considered country as stratum using Dong et al. (2018) statistic in each subgroup."

**Reading it:** "consistent across all prespecified subgroups" is defensible on overlapping CIs, but the spread is not trivial — NYHA I/II 1.833 vs NYHA III/IV 1.184; AF-no 1.711 vs AF-yes 1.229; pre-COVID 1.174 vs post-COVID 1.651; and prior-SGLT2i-yes is the only subgroup with a point estimate **below 1** (0.928), on n=58. Without interaction p-values none of this can be tested, and I am not going to compute them.

---

## 8. PARACHUTE-HF — safety

| Cell | SV | ENA | Effect | Tier | Pointer |
|---|---|---|---|---|---|
| Any adverse event | 331 (71.6%) | 348 (75.7%) | — | T1-MAIN | Table 2 |
| **Serious adverse events** | **211 (45.7%)** | **234 (50.9%)** | — | T1-MAIN | Table 2 |
| Discontinuation due to AE | 28 (6.1%) | 45 (9.8%) | — | T1-MAIN | Table 2 |
| Symptomatic hypotension | 146 (31.6%) | 126 (27.4%) | rate ratio 1.28 (0.96–1.70) | T1-MAIN | Table 2 |
| Kidney dysfunction | 101 (21.9%) | 92 (20.0%) | — | T1-MAIN | Table 2 |
| Hyperkalemia | 91 (19.7%) | 101 (22.0%) | — | T1-MAIN | Table 2 |
| Arrhythmia | 77 (16.7%) | 73 (15.9%) | — | T1-MAIN | Table 2 |
| Angioedema | 2 (0.4%) | 4 (0.9%) | — | T1-MAIN | Table 2 |
| Serious AEs (registry definition) | 169/462 | 183/460 | — | T2-REG | CTG `seriousNumAffected` — **disagrees with Table 2, see §11** |
| Other non-serious AEs (≥5% threshold) | 102/462 | 145/460 | — | T2-REG | CTG `otherNumAffected` |

### 8.1 AEs leading to study drug discontinuation, by MedDRA preferred term — **new, T1-SUPP (eTable 9, pp. 22–23)**

Most notable rows (SV / ENA):

| Term | SV | ENA |
|---|---|---|
| **Cough** | **0** | **20** |
| Cardiac failure acute | 2 | 3 |
| Acute kidney injury | 1 | 3 |
| Hypotension | 3 | 1 |
| Arrhythmic storm | 1 | 2 |
| Pruritus | 1 | 2 |
| Sudden death | 1 | 2 |
| Cardiac failure | 2 | 1 |
| Ventricular arrhythmia | 2 | 1 |
| Septic shock | 3 | 0 |
| Ventricular tachycardia | 3 | 0 |
| Cardiogenic shock | 2 | 0 |
| Orthostatic hypotension | 0 | 1 |

Plus 30+ singleton terms. **Cough (0 vs 20) is the dominant single driver of the discontinuation difference** — the classic ACE-inhibitor effect, and it accounts for most of the 6.1% vs 9.8% gap on its own.

> **Data-quality warning on eTable 9:** the published "Total" column is internally inconsistent — for every row where the SV count is >0, "Total" equals the Enalapril column rather than the sum (e.g. "Cardiac failure acute 2 | 3 | **3**"). Verified against the raw PDF text layer at word-coordinate level, so this is a genuine typesetting error in the published table, not an extraction artefact. **Use the two per-arm columns; ignore the Total column.** I have not corrected it by summation.

---

## 9. What Supplement 3 did and did not contain

**Full contents** (26 pp.): enrolling centres and investigators (pp. 3–5), Executive/Steering committees, coordinating centre, DSMB, CEC committee, Novartis team (pp. 5–6), follow-up schedule (p. 8), eTable 1 participants per site (pp. 9–11), eTable 2 adherence (p. 12), eTable 3 medications (p. 13), eTable 4 win ratio by strata (pp. 14–15), eTable 5 NT-proBNP at 12 wk and 8 mo (p. 16), eTable 6 per-protocol sensitivity (pp. 17–18), eTable 7 total-death-first sensitivity (p. 19), eTable 8 subgroups (pp. 20–21), eTable 9 AE discontinuations (pp. 22–23), eFigure 1 treatment level per visit (pp. 24–25), eFigure 2 win-ratio weighted wins (p. 26).

**DID contain (new):** component-specific win ratios with CIs (eFigure 2); complete subgroup table (eTable 8); NT-proBNP at month 8 (eTable 5); per-protocol and total-death sensitivity win ratios (eTables 6, 7); per-country win ratios (eTable 4); per-arm baseline and concomitant medications (eTable 3); adherence and discontinuation reasons (eTable 2); AE-discontinuation terms (eTable 9); per-visit dosing with denominators (eFigure 1).

**DID NOT contain:**
- **Any hazard ratio.** The string "hazard" appears **zero times** in all 26 pages (verified by full-text grep). The all-cause mortality HR was in **main-text Table 2**, not here.
- **Kaplan–Meier curves.** Only two eFigures exist: a stacked bar chart (eFigure 1) and a win-ratio flow diagram (eFigure 2). **KM curves are main-text Figure 2 C, D, E** — Mahmood confirmed this from the article. Any pseudo-IPD reconstruction needs the article figure, not supp3.
- **Subgroup interaction p-values.** Not printed in eTable 8 or anywhere else.
- **Country-level randomisation totals.** eTable 1 is per-site with no totals row; I have not summed it.

**My prior inference, scored:** label "Supplement 3 = eTables/eFigures" — correct. Contents prediction — correct on the subgroup analysis, **wrong on the mortality HR and wrong on the KM curves**, both of which are main text.

---

## 10. Layers searched and what each returned

| Layer | Result |
|---|---|
| PubMed abstract | **Hit** — win ratio, event counts + %, NT-proBNP medians/IQRs |
| **Primary publication main text** | **Hit, and the decisive layer.** Table 2 carries every HR, every P value, per-100py rates, the Fine–Gray subdistribution HR, the unstratified win ratio, and the full safety panel. My earlier failure to reach it was a **tooling block, not an access restriction** |
| **Primary publication Supplement 3** | **Hit** — see §9 |
| PMC / Europe PMC | Fetch blocked by reCAPTCHA on my path. Article itself is open |
| ClinicalTrials.gov posted results | **Hit** — participant flow, baseline, 13 outcome tables, AE module |
| FDA statistical reviews | **Nothing** Chagas-specific; Entresto's approval predates these trials |
| EMA EPARs | **Nothing** Chagas-specific |
| NICE / CADTH–CDA / PBAC / IQWiG / SMC | **Nothing.** Only NICE TA388 (general HFrEF, 2016). No Chagas-indication HTA exists — Entresto is already licensed for HFrEF irrespective of aetiology, so no assessment was ever triggered. **A real negative** |
| CONITEC (Brazil) / IETS (Colombia) | **Nothing** located |
| Prior meta-analyses | **Hit** — two 2026 Cardiology in Review meta-analyses, n=1225 each |
| Conference press / news | **Hit** — ESC PR carried HRs before I had the main text |
| Independent appraisals | **Hit**, with two errors of their own (§11) |
| Figure digitisation | **Not required anywhere** |

---

## 11. Disagreements between sources — findings, not nuisances

| # | Conflict | Values | Resolution |
|---|---|---|---|
| 1 | **Pairwise comparisons** | **212,520** (Cardiology Trials appraisal) vs **101,477** (eFigure 2, p. 26) | **The appraisal is wrong.** Its author computed 462 × 460 = 212,520 and built a whole explainer paragraph on it. The actual analysis matches **within country strata**, giving 101,477. Use 101,477. This is a substantive error in a widely-read secondary source |
| 2 | **NT-proBNP % change at wk 12** | −30.6 / −5.5 vs −41.1 / −1.5 | **Both correct, and my earlier call was wrong.** −30.6 / −5.5 are **medians (IQR)**; −41.1 (SD 72.8) / −1.5 (SD 66.3) are **means (SD)**. Both are in Table 2. I previously flagged the second pair as a likely error — it was not |
| 3 | **Serious adverse events** | **211 (45.7%) / 234 (50.9%)** (Table 2) vs **169 / 183** (CTG `seriousNumAffected`) | **Genuine registry-vs-paper disagreement**, almost certainly a definitional/window difference (CTG AE window = first dose to end of treatment + 30 days, max 55 months). Not reconcilable from the public record. **Prefer Table 2** for a paper-based synthesis; note the registry figure if you use CTG as your source |
| 4 | **Discontinuation due to AE** | **28 (6.1%) / 45 (9.8%)** (Table 2) vs **21 (4.5%) / 49 (10.7%)** permanent study-drug discontinuation of which AE-caused **7/21 and 15/49** (eTable 2, p. 12) | Three different quantities with three different definitions. **Use Table 2's 28/45** for "discontinuation due to AE". eTable 2's 21/49 is *permanent study-drug discontinuation from any cause other than death*. Not reconcilable by arithmetic and not attempted |
| 5 | **NT-proBNP analysable n at week 12** | **417 / 401** (Table 2) vs **419 / 403** (eTable 5, p. 16 **and** CTG posted results) | **Unexplained 2-patient discrepancy between the paper's own main text and its own supplement.** The supplement and the registry agree with each other against the main text. Flagged; not resolved |
| 6 | **Sudden death direction** | 46 (10.0%) SV vs 39 (8.5%) ENA, **HR 1.17 (0.76–1.80)** | Not a conflict, but worth noting: this is the one outcome where the point estimate **favours enalapril**. No secondary source mentioned it |
| 7 | Number of sites | 83 (main text) vs "more than 80" (ESC/ACC/TCTMD) vs 79 facility records (CTG) vs "around 100" planned (design paper) | **Use 83.** Registry undercounts; design-paper figure was a plan |
| 8 | Events at trial stop | 324 actual vs 302 protocol target | Both correct — actual vs planned |
| 9 | Baseline median NT-proBNP | 1730 pg/mL (EJHF baseline paper) vs 1740 "at screening" (Cardiology Trials) vs **1801.0 SV / 1679.0 ENA** (eTable 5) | Different populations/timepoints: 1730 is the pooled baseline; eTable 5 gives per-arm baseline. **Use eTable 5 for per-arm work** |

---

## 12. Estimand caveat — important for the meta-analysis

**Do not pool the PARACHUTE-HF win ratio with HR-based composites.** The primary endpoint is a **hierarchical win ratio**, not a time-to-event effect measure; it has no common estimand with a Cox HR and no valid variance for pooling alongside one. The same applies to ANSWER-HF's win ratio of 1.80.

For a pooled time-to-event synthesis, use the **HRs from main-text Table 2**:
- All-cause death **0.98 (0.77–1.25)**
- CV death **0.95 (0.73–1.23)**
- First HF hospitalisation **0.92 (0.70–1.20)** — or the Fine–Gray subdistribution HR **0.74 (0.49–1.14)** if you are modelling the competing risk, but pick one and be consistent
- Composite **0.91 (0.73–1.13)**

Also note the prespecified superiority rule: the trial required **both** a win ratio > 1 **and** HR point estimates < 1.0 for CV death and HF hospitalisation. Both HR conditions were met on point estimates (0.95, 0.92) while neither was statistically significant — so "positive" here is a composite-rule verdict, not a demonstrated clinical-outcome benefit.

---

## 13. Still unrecovered

| Item | Status | Next step |
|---|---|---|
| **Subgroup interaction p-values** | **Not reported by the authors.** eTable 8 prints none; the main text asserts consistency without testing it | Request from authors, or treat consistency as an untested claim |
| **Kaplan–Meier pseudo-IPD** | Curves exist as **main-text Figure 2 C, D, E** — not extracted | Digitise Figure 2 C/D/E with the numbers-at-risk table; Guyot algorithm |
| **Country-level randomisation totals** | eTable 1 is per-site only, no totals row | Sum eTable 1 manually if needed — I have not, per the read-don't-compute rule |
| **PARACHUTE-HF non-serious AE per-term table (registry version)** | CTG API response truncated at ~85.6k chars before `otherEvents` | Re-fetch CTG with `fields=AdverseEventsModule` alone, or use AACT |
| **ANSWER-HF per-arm n and event counts** | Not in the JACC abstract; registry has no posted results | JACC full text |
| **PARADIGM-HF Chagas subgroup component CIs** | Only in the 2018 forest plot image | Digitise `eschf_5_6_1069_gra-0001`; composite HR 0.63 (0.31–1.28) already recovered as text |
| **PARADIGM-HF parent NCT** | Not resolved by live lookup | Resolve live; do not fill from recall |
| **Serious-AE definitional gap (Table 2 vs CTG)** | Unresolvable from public documents | Would need the CSR |

---

*Every value in this document was read verbatim from the source named in its row. No cell was summed, averaged, or back-derived. Where a published table is internally inconsistent (eTable 9 Total column) or two primary sources disagree (NT-proBNP n; serious AEs), the disagreement is reported rather than resolved by computation. All identifiers were resolved by live lookup.*

**Attribution:** bibliographic records and abstracts retrieved from PubMed. DOIs: [10.1001/jama.2025.19808](https://doi.org/10.1001/jama.2025.19808) · [10.1007/s10741-026-10617-3](https://doi.org/10.1007/s10741-026-10617-3) · [10.1016/j.jacc.2025.10.053](https://doi.org/10.1016/j.jacc.2025.10.053) · [10.1007/s10741-026-10614-6](https://doi.org/10.1007/s10741-026-10614-6) · [10.1002/ejhf.70026](https://doi.org/10.1002/ejhf.70026) · [10.1016/j.jchf.2024.05.021](https://doi.org/10.1016/j.jchf.2024.05.021) · [10.1002/ehf2.12355](https://doi.org/10.1002/ehf2.12355) · [10.1097/CRD.0000000000001270](https://doi.org/10.1097/CRD.0000000000001270) · [10.1097/CRD.0000000000001242](https://doi.org/10.1097/CRD.0000000000001242)
