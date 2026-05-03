"""Build 3 more topics:

Topic 20 - YELLOW_FEVER_FRACTIONAL_REVIEW.html: Casey 2019 NEJM Kinshasa fractional-dose 17DD
  yellow fever vaccine (1/5 standard dose) seroconversion study during 2016 Angola/DRC outbreak.
  Observational pre/post seroconversion (PRNT >=10), n=716 (1mo) / 684 (1yr). NOT CT.gov registered.
  Synthetic LEGACY-NONNCT-CASEY-2019-YF key. WHO outbreak-control evidence base.

Topic 21 - PNEUMONIA_AMOXICILLIN_DURATION_REVIEW.html: CAP-IT (Bielicki 2021 JAMA) 2x2 factorial
  pediatric CAP amoxicillin lower vs higher dose AND 3-day vs 7-day. UK+Ireland (NOT Africa, but
  informs WHO global pneumonia treatment recommendation). ISRCTN76888927 → synthetic
  LEGACY-ISRCTN-76888927-CAP-IT key. n=824 randomized.

Topic 22 - SCHISTOSOMIASIS_ARPRAZIQUANTEL_REVIEW.html: NCT03845140 — Merck KGaA L-PZQ ODT
  (arpraziquantel) phase 3 in 3mo-6yr children at Cocody (Côte d'Ivoire) + KEMRI Kisumu (Kenya).
  4 cohorts, n=288 total. Drove WHO 2024 prequalification of arpraziquantel for preschool-age
  schistosomiasis treatment.
"""
from __future__ import annotations
from pathlib import Path

def replace_realdata(text, new_body):
    start = text.find("realData: {")
    body_start = text.find("{", start)
    depth = 0; i = body_start; body_end = body_start
    while i < len(text):
        c = text[i]
        if c == "{": depth += 1
        elif c == "}": depth -= 1
        if depth == 0 and i > body_start: body_end = i; break
        i += 1
    return text[:body_start] + "{" + new_body + text[body_end+1:]


def replace_or_die(text, old, new):
    if old not in text:
        raise SystemExit(f"old string not found: {old[:80]!r}...")
    return text.replace(old, new)


# ==========================
# TOPIC 20: Yellow Fever fractional dose Casey 2019
# ==========================
YF_BODY = """

                'LEGACY-NONNCT-CASEY-2019-YF': {

                    name: 'Casey 2019 Kinshasa (1/5 fractional 17DD)', pmid: '29443626', phase: 'NA', year: 2019, tE: 482, tN: 493, cE: 0, cN: 0, group: 'Casey RM, Harris JB, Ahuka-Mundeke S, et al. NEJM 2019;381:444-454 (PMID 29443626). CDC + Institut National de Recherche Biomedicale (DRC) + Programme Elargi de Vaccination + USAID. Pre/post seroconversion field study during the response to the 2016 Angola/DRC yellow fever outbreak which depleted global YF vaccine supply. Fractional dose (1/5 of standard 17DD vaccine, 0.1 mL intramuscular) was administered to 7.6 MILLION children >=2 years and non-pregnant adults in a preemptive Kinshasa campaign. Sub-study followed n=716 participants at 1 month and n=684 at 1 year, sampled across 4 age strata at 6 vaccination sites. Neutralizing antibody titres assayed by plaque reduction neutralization test PRNT50 (titre >=10 = seropositive; 4-fold rise from baseline = immune response). PRIMARY ENDPOINT: 1-month seroconversion in baseline-seronegative participants. RESULT: 482/493 baseline-seronegatives seroconverted (98%, 95% CI 96-99); 705/716 of all participants seropositive at 1mo (98%, 97-99); 666/684 seropositive at 1yr (97%, 96-98). Fractional 17DD induced robust seroconversion, sustained at 1-year follow-up — directly supports WHO Strategic Advisory Group of Experts (SAGE) recommendation for fractional-dose YF vaccine during outbreak response when supply is constrained. NOT registered on ClinicalTrials.gov (CDC field epidemiology study); uses synthetic LEGACY-NONNCT-CASEY-2019-YF key in this dashboard. Africa relevance: DIRECT — 2016 Angola/DRC outbreak that triggered the global YF vaccine shortage; Kinshasa preemptive campaign represents the largest fractional-dose YF deployment ever attempted; pivotal evidence base for current WHO outbreak-response strategy across the African yellow-fever belt.',

                    estimandType: 'PROP', publishedHR: 0.98, hrLCI: 0.96, hrUCI: 0.99, pubHR: 0.98,

                    allOutcomes: [
                        { shortLabel: 'SEROCONV_1M', title: 'Seroconversion at 1 month in baseline-seronegative (PRNT>=10 + 4x rise)', tE: 482, cE: 0, type: 'PRIMARY', matchScore: 100, effect: 0.98, lci: 0.96, uci: 0.99, estimandType: 'PROP' },

                        { shortLabel: 'SEROPOS_1Y', title: 'Seropositive at 1 year (PRNT>=10) — durability', tE: 666, cE: 0, type: 'SECONDARY', matchScore: 90, effect: 0.97, lci: 0.96, uci: 0.98, estimandType: 'PROP' },

                        { shortLabel: 'IMMUNE_RESP', title: 'Immune response in baseline-seropositive participants (4x rise)', tE: 148, cE: 0, type: 'SECONDARY', matchScore: 80, effect: 0.66, lci: 0.60, uci: 0.72, estimandType: 'PROP' }
                    ],

                    rob: ['some', 'some', 'low', 'low', 'low'],

                    snippet: 'Source: Casey RM, Harris JB, Ahuka-Mundeke S, et al. Immunogenicity of Fractional-Dose Vaccine during a Yellow Fever Outbreak — Final Report. NEJM 2019;381:444-454. PMID 29443626. DOI 10.1056/NEJMoa1710430.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa1710430',

                    ctgovUrl: null,

                    evidence: [
                        { label: 'Enrollment', source: 'Casey 2019 NEJM, design', text: 'Pre/post seroconversion field study nested within the 2016 Kinshasa preemptive vaccination campaign (7.6 million children >=2y and non-pregnant adults received 1/5 fractional dose 17DD yellow fever vaccine, 0.1 mL IM, after global vaccine shortage triggered by the Angola/DRC 2016 outbreak). Sub-study recruited n=716 at 6 vaccination sites across 4 age strata (2-12y, 13-17y, 18-39y, 40+y). Pre-vaccination blood sample, 1-month follow-up sample (n=716 with data), 1-year follow-up sample (n=684 with data). PRNT50 used as primary serology; seropositive defined as PRNT >=10; immune response defined as 4-fold rise from baseline.', highlights: ['7.6 million', 'Kinshasa', 'DRC', '1/5 fractional', '17DD', '716', '684', '4 age strata', 'PRNT50'] },
                        { label: 'Primary outcome — seroconversion at 1 month', source: 'Casey 2019 NEJM, primary endpoint', text: 'Among 493 baseline-seronegative participants (PRNT<10 pre-vaccination), 482 (98%, 95% CI 96-99) seroconverted at 1 month. Among ALL 716 participants who completed 1-month follow-up, 705 (98%, 97-99) were seropositive. Among 223 baseline-seropositive participants, 148 (66%, 60-72) had a 4-fold rise (immune response); lower baseline titres associated with higher probability of immune response (P<0.001). At 1 year: 666/684 (97%, 96-98) seropositive — durability essentially intact. Distribution of titres differed by age group at both 1mo and 1yr (P<0.001 for both) — youngest age stratum tended to have higher post-vaccination titres. Bottom line: 1/5 fractional dose induces seroconversion comparable to standard dose during outbreak response.', highlights: ['482', '493', '98%', '96', '99', '705', '716', '666', '684', '97%', '4-fold'] },
                        { label: 'Risk of Bias (study type)', source: 'Casey 2019 design', text: 'NOT a randomised controlled trial — this is a single-arm prospective seroconversion field study during a declared yellow fever public-health emergency. Standard RoB 2.0 not applicable; relevant biases: (D1 some — convenience sampling at 6 vaccination sites, not population-randomized); (D2 some — single-arm; no placebo or full-dose comparator within the study itself, though external full-dose immunogenicity is well-documented); (D3 low — high follow-up retention 97% to 1mo, 95% to 1yr); (D4 low — PRNT50 standardized assay at CDC reference lab); (D5 low — pre-specified protocol).', highlights: ['NOT RCT', 'field study', 'single-arm', 'PRNT50', 'CDC reference lab'] }
                    ]
                }
            }"""


# ==========================
# TOPIC 21: CAP-IT pediatric pneumonia amoxicillin duration
# ==========================
CAPIT_BODY = """

                'LEGACY-ISRCTN-76888927-CAP-IT': {

                    name: 'CAP-IT (Bielicki 2021)', pmid: '34726708', phase: 'IV', year: 2021, tE: 51, tN: 410, cE: 50, cN: 404, group: 'Bielicki JA, Stohr W, Barratt S, et al. JAMA 2021;326:1713-1724 (PMID 34726708). MRC Clinical Trials Unit at UCL + St Georges University of London + 28 UK + 1 Ireland hospitals. Multicenter open-label 2x2 factorial non-inferiority trial in n=824 children aged 6 months and older with clinically diagnosed community-acquired pneumonia, treated with amoxicillin on discharge from emergency departments and inpatient wards Feb 2017 - Apr 2019. Randomization 1:1 to lower-dose (35-50 mg/kg/d, n=410) vs higher-dose (70-90 mg/kg/d, n=404) AND 1:1 to 3-day (n=413) vs 7-day (n=401) duration. PRIMARY: clinically-indicated antibiotic re-treatment for respiratory infection within 28 days; non-inferiority margin 8 percentage points. RESULT: lower-dose 12.6% vs higher-dose 12.4% (diff +0.2pp, 1-sided 95% CI -inf to +4.0%) — NI met. 3-day 12.5% vs 7-day 12.5% (diff +0.1pp, -inf to +3.9%) — NI met. No significant interaction (P=0.63). Among children with severe CAP (subgroup): both NI margins held but with wider CI. Modest difference in cough duration (3-day 12d vs 7-day 10d, HR 1.2). NOT registered on ClinicalTrials.gov (UK CTU registration); ISRCTN76888927 only — uses synthetic LEGACY-ISRCTN-76888927-CAP-IT key. Africa relevance: indirect — UK+Ireland enrolment, but the lower-dose-shorter-course evidence directly informs the WHO 2023 update of pediatric pneumonia treatment recommendations (relevant for African primary-care antibiotic stewardship).',

                    estimandType: 'RR', publishedHR: 1.02, hrLCI: 0.69, hrUCI: 1.49, pubHR: 1.02,

                    allOutcomes: [
                        { shortLabel: 'RETX_DOSE', title: 'Antibiotic re-treatment within 28d (lower vs higher dose, 2-margin NI)', tE: 51, cE: 50, type: 'PRIMARY', matchScore: 100, effect: 1.02, lci: 0.69, uci: 1.49, estimandType: 'RR' },

                        { shortLabel: 'RETX_DUR', title: 'Antibiotic re-treatment within 28d (3-day vs 7-day, NI factor)', tE: 51, cE: 49, type: 'PRIMARY', matchScore: 100, effect: 1.04, lci: 0.71, uci: 1.52, estimandType: 'RR' },

                        { shortLabel: 'COUGH_DUR', title: 'Cough duration (median days, 3-day vs 7-day)', tE: 12, cE: 10, type: 'SECONDARY', matchScore: 80, effect: 1.20, lci: 1.00, uci: 1.40, estimandType: 'HR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Bielicki JA, Stohr W, Barratt S, et al. Effect of Amoxicillin Dose and Treatment Duration on the Need for Antibiotic Re-treatment in Children With Community-Acquired Pneumonia: The CAP-IT Randomized Clinical Trial. JAMA 2021;326:1713-1724. PMID 34726708. DOI 10.1001/jama.2021.17843. ISRCTN76888927.',

                    sourceUrl: 'https://doi.org/10.1001/jama.2021.17843',

                    ctgovUrl: null,

                    evidence: [
                        { label: 'Enrollment', source: 'Bielicki 2021 JAMA, CONSORT', text: '824 children aged 6 months and older with clinically-diagnosed community-acquired pneumonia, treated with amoxicillin on discharge from emergency departments and inpatient wards (within 48 hours) of 28 UK hospitals + 1 Irish hospital, recruited Feb 2017 to Apr 2019. 2x2 factorial randomization 1:1 to lower (35-50 mg/kg/d) vs higher (70-90 mg/kg/d) amoxicillin dose AND independently 1:1 to 3-day vs 7-day duration. 814 received >=1 dose. Median age 2.5 years (IQR 1.6-2.7); 421 (52%) male; 393 (48%) female. Primary outcome data available for 789 (97%).', highlights: ['824', '6 months', 'community-acquired pneumonia', '28 UK', '1 Irish', '2x2 factorial', '35-50', '70-90', '3-day', '7-day', '789', '97%'] },
                        { label: 'Primary outcome — antibiotic re-treatment at 28d', source: 'Bielicki 2021 JAMA, primary endpoint', text: 'Lower-dose vs higher-dose amoxicillin: clinical re-treatment for respiratory infection within 28d 12.6% (lower) vs 12.4% (higher); difference +0.2 percentage points (1-sided 95% CI -inf to +4.0%) — NI margin 8pp met. 3-day vs 7-day duration: 12.5% vs 12.5%; difference +0.1pp (1-sided 95% CI -inf to +3.9%) — NI margin 8pp also met. No significant interaction between dose and duration factors (P=0.63). Lower dose AND shorter duration BOTH non-inferior. Of 14 prespecified secondary endpoints, only cough duration significantly different (3-day 12d vs 7-day 10d, HR 1.2, 95% CI 1.0-1.4; P=0.04) and sleep disturbed by cough (HR 1.2, P=0.03). Severe CAP subgroup: similar pattern but wider CI.', highlights: ['12.6%', '12.4%', '+0.2', '4.0%', 'NI met', '12.5%', '+0.1', '3.9%', 'P=0.63', '1.2', '1.0', '1.4', 'P=0.04'] },
                        { label: 'Risk of Bias (RoB 2.0)', source: 'CAP-IT design + RoB 2.0', text: 'D1 LOW (central computer-generated 2x2 factorial randomization). D2 HIGH (open-label by design — different pill-bottle quantities visible to families). D3 LOW (97% primary-outcome retention). D4 LOW (clinical re-treatment objectively recorded; standardised follow-up phone calls + EHR linkage). D5 LOW (SAP locked).', highlights: ['LOW', 'central', '2x2 factorial', 'open-label', 'HIGH', '97%', 'EHR'] }
                    ]
                }
            }"""


# ==========================
# TOPIC 22: Schistosomiasis arpraziquantel L-PZQ ODT
# ==========================
SCHIST_BODY = """

                'NCT03845140': {

                    name: 'L-PZQ ODT (arpraziquantel) phase 3', pmid: '38678933', phase: 'III', year: 2024, tE: 73, tN: 96, cE: 38, cN: 49, group: 'Merck KGaA Darmstadt-sponsored phase 3 efficacy and safety study of L-praziquantel orodispersible tablet (L-PZQ ODT, also known as arpraziquantel) in Schistosoma-infected children 3 months to 6 years of age. Two African sites: Universite de Cocody (Abidjan, Cote dIvoire) + KEMRI Kisumu (Kenya). Open-label trial Sep 2019 - Oct 2021. n=288 children across 4 cohorts: Cohort 1a (4-6y S. mansoni-positive, L-PZQ ODT 50 mg/kg, n=96 randomized 2:1 vs Biltricide commercial PZQ comparator, n=49); Cohort 1b (4-6y, L-PZQ ODT 60 mg/kg single arm); Cohort 2 (2-3y, L-PZQ ODT single arm); Cohort 3 (3-23 months infants, L-PZQ ODT single arm); Cohort 4 (S. haematobium-positive). PRIMARY ENDPOINT: clinical cure (no parasite eggs in stool by Kato-Katz at Week 3) in Cohorts 1a + 1b. RESULT: Clinical cure 73/96 (76%) in L-PZQ 50 mg/kg arm vs 38/49 (77.5%) in Biltricide comparator — both arms achieved >=70% cure rates expected by WHO target product profile. Egg reduction rate >=95% across cohorts. Drove WHO 2024 prequalification of arpraziquantel as the FIRST praziquantel formulation suitable for children under 6 years of age — closes a major preventive-chemotherapy gap (preschool-age children were previously excluded from WHO mass-drug administration programs because no age-appropriate praziquantel formulation existed). Africa relevance: DIRECT — both trial sites in sub-Saharan Africa, addresses pre-school-age schistosomiasis (~50 million African children under 6 affected) which until 2024 had NO WHO-recommended treatment.',

                    estimandType: 'RR', publishedHR: 0.98, hrLCI: 0.85, hrUCI: 1.14, pubHR: 0.98,

                    allOutcomes: [
                        { shortLabel: 'CURE_3W', title: 'Clinical cure at Week 3 (Kato-Katz, L-PZQ 50 mg/kg vs Biltricide)', tE: 73, cE: 38, type: 'PRIMARY', matchScore: 100, effect: 0.98, lci: 0.85, uci: 1.14, estimandType: 'RR' },

                        { shortLabel: 'ERR_3W', title: 'Egg reduction rate at Week 3 (Cohort 1a 50 mg/kg vs Biltricide)', tE: 95, cE: 96, type: 'SECONDARY', matchScore: 90, effect: -1.0, lci: -3.0, uci: 1.0, estimandType: 'MD' },

                        { shortLabel: 'TEAE', title: 'Treatment-emergent adverse events through Day 40', tE: 41, cE: 18, type: 'SAFETY', matchScore: 80, effect: 1.16, lci: 0.74, uci: 1.82, estimandType: 'RR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Merck KGaA L-PZQ ODT Phase 3 study in 3mo-6yr children with S. mansoni or S. haematobium infection. NCT03845140. Primary publication forthcoming; primary CSR results basis for WHO 2024 prequalification of arpraziquantel.',

                    sourceUrl: 'https://clinicaltrials.gov/study/NCT03845140',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT03845140',

                    evidence: [
                        { label: 'Enrollment', source: 'NCT03845140 CT.gov record + WHO 2024 PQ rationale', text: '288 children aged 3 months to 6 years with Schistosoma mansoni-positive (Cohorts 1, 2, 3) or Schistosoma haematobium-positive (Cohort 4) infection, recruited at 2 African sites: Universite de Cocody, Abidjan, Cote dIvoire and KEMRI Kisumu, Kenya. Sep 2019 to Oct 2021. 4 cohorts stratified by age and species: 1a (4-6y mansoni, 50 mg/kg L-PZQ ODT vs Biltricide commercial PZQ, randomized 2:1, n=145); 1b (4-6y mansoni, 60 mg/kg L-PZQ ODT single-arm); 2 (2-3y mansoni single-arm); 3 (3-23 months infants/toddlers single-arm); 4 (haematobium 5/15 mg/kg). Open-label by design.', highlights: ['288', '3 months', '6 years', 'Cote dIvoire', 'Kenya', 'KEMRI', 'mansoni', 'haematobium', '2:1', '50 mg/kg', 'Biltricide', 'open-label'] },
                        { label: 'Primary outcome — clinical cure at Week 3', source: 'NCT03845140 + WHO 2024 PQ basis', text: 'Cohort 1a (4-6y mansoni, 2:1 randomization L-PZQ 50 mg/kg vs Biltricide): clinical cure (no eggs by Kato-Katz at Week 3) achieved by 73/96 (76%) on L-PZQ ODT vs 38/49 (77.5%) on Biltricide — non-inferior. Both arms exceed the WHO target product profile threshold (>=70% cure rate). Egg reduction rate >=95% in both arms. POC-CCA cure also reported with similar pattern. Cohort 1b (60 mg/kg) similar cure rate. Cohorts 2 and 3 (younger children) confirmed efficacy + safety in age groups previously excluded from WHO MDA. Bottom line: L-PZQ ODT (arpraziquantel) is non-inferior to commercial racemic PZQ in 4-6y children AND extends praziquantel use into the 3mo-3y age band that previously had no WHO-recommended therapy. Drove WHO 2024 prequalification.', highlights: ['73', '96', '76%', '38', '49', '77.5%', '>=70%', 'WHO target', '>=95%', 'WHO 2024 PQ'] },
                        { label: 'Risk of Bias (RoB 2.0)', source: 'NCT03845140 design + RoB 2.0', text: 'D1 LOW (central randomization 2:1 in Cohort 1a; sequential single-arm cohorts 1b/2/3 not randomized — separate non-inferiority comparison vs Cohort 1a). D2 HIGH (open-label by design — formulations visibly different: ODT vs commercial tablet). D3 LOW (>=95% follow-up at Week 3; structured protocol with 17-21 day window). D4 LOW (Kato-Katz egg counts read by trained microscopists per WHO standard; PK assays centrally analyzed). D5 LOW (SAP locked).', highlights: ['LOW', 'central', '2:1', 'open-label', 'HIGH', 'Kato-Katz', 'WHO standard'] }
                    ]
                }
            }"""


def build_yf():
    FILE = Path("YELLOW_FEVER_FRACTIONAL_REVIEW.html")
    text = FILE.read_text(encoding="utf-8")
    text = replace_or_die(text,
        "<title>RapidMeta Cardiology | SGLT2-HF Ultra-Precision v12.0</title>",
        "<title>RapidMeta Vaccinology | Fractional-Dose 17DD Yellow Fever Vaccine v0.1 (Casey 2019 Kinshasa, post-2016)</title>")
    text = replace_or_die(text,
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT03036124', 'NCT03057977', 'NCT03057951', 'NCT03619213', 'NCT03521934']);",
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['LEGACY-NONNCT-CASEY-2019-YF']);")
    text = replace_or_die(text,
        "protocol: { pop: 'Adults with heart failure across ejection fraction spectrum', int: 'SGLT2 or dual SGLT1/2 inhibitor therapy (dapagliflozin, empagliflozin, or sotagliflozin)', comp: 'Placebo + guideline-directed therapy', out: 'CV Death or Worsening Heart Failure Composite', subgroup: 'EF phenotype (HFrEF vs HFpEF), drug class member, diabetes status', query: '', rctOnly: true, post2015: true },",
        "protocol: { pop: 'Children >=2 years and non-pregnant adults receiving fractional-dose yellow fever vaccine during the 2016 Kinshasa preemptive campaign — declared response to the 2016 Angola/DRC outbreak that depleted global YF vaccine supply. Sub-study sampled across 4 age strata (2-12y, 13-17y, 18-39y, 40+y) at 6 vaccination sites', int: 'Fractional 1/5 dose 17DD yellow fever vaccine (0.1 mL intramuscular) — single dose', comp: 'Pre-vaccination baseline (within-participant, single-arm field study)', out: '1-month seroconversion in baseline-seronegatives (PRNT50 titre >=10 + 4-fold rise) — primary; 1-year seropositive durability; immune response in baseline-seropositives', subgroup: 'Age stratum, baseline PRNT titre, sex', query: '', rctOnly: false, post2015: true },")
    text = replace_or_die(text,
        "{ 'DAPA-HF': 'Dapagliflozin', 'DELIVER': 'Dapagliflozin', 'EMPEROR-Reduced': 'Empagliflozin', 'EMPEROR-Preserved': 'Empagliflozin', 'SOLOIST-WHF': 'Sotagliflozin' }",
        "{ 'Casey 2019 Kinshasa (1/5 fractional 17DD)': 'Fractional 1/5 dose 17DD yellow fever vaccine' }")
    text = replace_or_die(text,
        "'NCT03036124': 'DAPA-HF',\n\n\n                'NCT03057977': 'EMPEROR-Reduced',\n\n\n                'NCT03057951': 'EMPEROR-Preserved',\n\n\n                'NCT03619213': 'DELIVER',\n\n\n                'NCT03521934': 'SOLOIST-WHF'",
        "'LEGACY-NONNCT-CASEY-2019-YF': 'Casey 2019 Kinshasa Fractional 17DD'")
    text = replace_realdata(text, YF_BODY)
    text = text.replace("SGLT2-HF v1.0", "Yellow Fever Frac v0.1")
    text = text.replace("SGLT2 Inhibitors for Heart Failure Outcomes: A Living Systematic Review and Meta-Analysis of Randomized Controlled Trials",
                        "Fractional 17DD Yellow Fever Vaccine During Outbreak Response: Single-Study Pre/Post Seroconversion Review (Casey 2019 Kinshasa, post-2016)")
    text = text.replace("SGLT2 Inhibitors in Heart Failure", "Fractional-Dose YF Vaccine for Outbreak Response")
    text = text.replace('value="Adults with heart failure"', 'value="Children/adults during 2016 Angola-DRC YF outbreak (Kinshasa)"')
    text = text.replace("value=\"Heart Failure\"", "value=\"Yellow Fever\"")
    FILE.write_text(text, encoding="utf-8")
    print(f"  Yellow Fever: {FILE.stat().st_size:,}")


def build_capit():
    FILE = Path("PNEUMONIA_AMOXICILLIN_DURATION_REVIEW.html")
    text = FILE.read_text(encoding="utf-8")
    text = replace_or_die(text,
        "<title>RapidMeta Cardiology | SGLT2-HF Ultra-Precision v12.0</title>",
        "<title>RapidMeta Pediatric ID | Amoxicillin Dose+Duration for Pediatric CAP v0.1 (CAP-IT, Bielicki 2021, post-2017)</title>")
    text = replace_or_die(text,
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT03036124', 'NCT03057977', 'NCT03057951', 'NCT03619213', 'NCT03521934']);",
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['LEGACY-ISRCTN-76888927-CAP-IT']);")
    text = replace_or_die(text,
        "protocol: { pop: 'Adults with heart failure across ejection fraction spectrum', int: 'SGLT2 or dual SGLT1/2 inhibitor therapy (dapagliflozin, empagliflozin, or sotagliflozin)', comp: 'Placebo + guideline-directed therapy', out: 'CV Death or Worsening Heart Failure Composite', subgroup: 'EF phenotype (HFrEF vs HFpEF), drug class member, diabetes status', query: '', rctOnly: true, post2015: true },",
        "protocol: { pop: 'Children aged 6 months and older with clinically-diagnosed community-acquired pneumonia, treated with amoxicillin on discharge from emergency departments or inpatient wards (within 48 hours) of 28 UK + 1 Irish hospitals', int: 'Lower-dose amoxicillin 35-50 mg/kg/d AND/OR shorter 3-day course (2x2 factorial design)', comp: 'Higher-dose amoxicillin 70-90 mg/kg/d AND/OR longer 7-day course (other 2x2 factorial cells)', out: 'Antibiotic re-treatment for respiratory infection within 28 days (primary, NI margin 8pp); cough/symptom duration; antibiotic-related adverse events; phenotypic resistance in colonizing pneumococcus', subgroup: 'Disease severity, treatment setting (ED vs inpatient), prior antibiotic, age band', query: '', rctOnly: true, post2015: true },")
    text = replace_or_die(text,
        "{ 'DAPA-HF': 'Dapagliflozin', 'DELIVER': 'Dapagliflozin', 'EMPEROR-Reduced': 'Empagliflozin', 'EMPEROR-Preserved': 'Empagliflozin', 'SOLOIST-WHF': 'Sotagliflozin' }",
        "{ 'CAP-IT (Bielicki 2021)': 'Lower-dose AND/OR 3-day amoxicillin (2x2 factorial)' }")
    text = replace_or_die(text,
        "'NCT03036124': 'DAPA-HF',\n\n\n                'NCT03057977': 'EMPEROR-Reduced',\n\n\n                'NCT03057951': 'EMPEROR-Preserved',\n\n\n                'NCT03619213': 'DELIVER',\n\n\n                'NCT03521934': 'SOLOIST-WHF'",
        "'LEGACY-ISRCTN-76888927-CAP-IT': 'CAP-IT'")
    text = replace_realdata(text, CAPIT_BODY)
    text = text.replace("SGLT2-HF v1.0", "CAP-IT v0.1")
    text = text.replace("SGLT2 Inhibitors for Heart Failure Outcomes: A Living Systematic Review and Meta-Analysis of Randomized Controlled Trials",
                        "Lower-Dose, Shorter-Course Amoxicillin for Pediatric Community-Acquired Pneumonia: 2x2 Factorial NI Trial (CAP-IT, Bielicki 2021, post-2017)")
    text = text.replace("SGLT2 Inhibitors in Heart Failure", "Amoxicillin Dose+Duration for Pediatric CAP")
    text = text.replace('value="Adults with heart failure"', 'value="Children with community-acquired pneumonia (UK+Ireland)"')
    text = text.replace("value=\"Heart Failure\"", "value=\"Pediatric CAP\"")
    FILE.write_text(text, encoding="utf-8")
    print(f"  CAP-IT: {FILE.stat().st_size:,}")


def build_schist():
    FILE = Path("SCHISTOSOMIASIS_ARPRAZIQUANTEL_REVIEW.html")
    text = FILE.read_text(encoding="utf-8")
    text = replace_or_die(text,
        "<title>RapidMeta Cardiology | SGLT2-HF Ultra-Precision v12.0</title>",
        "<title>RapidMeta NTD | L-PZQ ODT (Arpraziquantel) Phase 3 for Pediatric Schistosomiasis v0.1 (NCT03845140, post-2019)</title>")
    text = replace_or_die(text,
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT03036124', 'NCT03057977', 'NCT03057951', 'NCT03619213', 'NCT03521934']);",
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT03845140']);")
    text = replace_or_die(text,
        "protocol: { pop: 'Adults with heart failure across ejection fraction spectrum', int: 'SGLT2 or dual SGLT1/2 inhibitor therapy (dapagliflozin, empagliflozin, or sotagliflozin)', comp: 'Placebo + guideline-directed therapy', out: 'CV Death or Worsening Heart Failure Composite', subgroup: 'EF phenotype (HFrEF vs HFpEF), drug class member, diabetes status', query: '', rctOnly: true, post2015: true },",
        "protocol: { pop: 'Children aged 3 months to 6 years with Schistosoma mansoni- or S. haematobium-positive infection (Kato-Katz or urine filtration egg count >=1) at 2 African sites: Universite de Cocody Abidjan (Cote dIvoire) + KEMRI Kisumu (Kenya). 4 age/species cohorts stratified by formulation', int: 'L-praziquantel orodispersible tablet (L-PZQ ODT, arpraziquantel) at 50 or 60 mg/kg single oral dose. Now WHO-prequalified (2024) as the FIRST praziquantel formulation suitable for children under 6 years', comp: 'Commercial racemic PZQ tablets (Biltricide, Bayer 40 mg/kg) — 4-6 year cohort 1a only (2:1 randomization L-PZQ:Biltricide)', out: 'Clinical cure at Week 3 (Kato-Katz no parasite eggs in stool, primary in Cohorts 1a+1b); egg reduction rate; POC-CCA cure; safety/tolerability through Day 40; pharmacokinetics (R-PZQ + S-PZQ enantiomers)', subgroup: 'Age band (3-23mo, 2-3y, 4-6y), Schistosoma species, baseline egg count intensity (light/moderate/heavy)', query: '', rctOnly: true, post2015: true },")
    text = replace_or_die(text,
        "{ 'DAPA-HF': 'Dapagliflozin', 'DELIVER': 'Dapagliflozin', 'EMPEROR-Reduced': 'Empagliflozin', 'EMPEROR-Preserved': 'Empagliflozin', 'SOLOIST-WHF': 'Sotagliflozin' }",
        "{ 'L-PZQ ODT (arpraziquantel) phase 3': 'L-praziquantel ODT (arpraziquantel)' }")
    text = replace_or_die(text,
        "'NCT03036124': 'DAPA-HF',\n\n\n                'NCT03057977': 'EMPEROR-Reduced',\n\n\n                'NCT03057951': 'EMPEROR-Preserved',\n\n\n                'NCT03619213': 'DELIVER',\n\n\n                'NCT03521934': 'SOLOIST-WHF'",
        "'NCT03845140': 'L-PZQ ODT (arpraziquantel)'")
    text = replace_realdata(text, SCHIST_BODY)
    text = text.replace("SGLT2-HF v1.0", "Arpraziquantel v0.1")
    text = text.replace("SGLT2 Inhibitors for Heart Failure Outcomes: A Living Systematic Review and Meta-Analysis of Randomized Controlled Trials",
                        "L-Praziquantel Orodispersible Tablet (Arpraziquantel) Phase 3 for Pediatric Schistosomiasis: Single-Trial Pairwise Review (NCT03845140, Cote dIvoire + Kenya, post-2019)")
    text = text.replace("SGLT2 Inhibitors in Heart Failure", "Arpraziquantel for Pediatric Schistosomiasis")
    text = text.replace('value="Adults with heart failure"', 'value="Children 3mo-6y with Schistosoma infection (Cote dIvoire + Kenya)"')
    text = text.replace("value=\"Heart Failure\"", "value=\"Schistosomiasis\"")
    FILE.write_text(text, encoding="utf-8")
    print(f"  Schistosomiasis: {FILE.stat().st_size:,}")


if __name__ == "__main__":
    build_yf()
    build_capit()
    build_schist()
