"""Rebuild SCD_DISEASE_MOD_NMA_REVIEW.html removing withdrawn-drug rows.

Voxelotor (HOPE) — withdrawn 2024 after ASCENT-HD safety signal
Crizanlizumab (SUSTAIN) — EMA withdrew 2023 after STAND failed to confirm

Replaced with currently-active SCD therapies:
  - REACH (NCT01966731, n=635, hydroxyurea in 4 African countries) — kept African focus
  - CTX001/Casgevy (NCT03745287, n=63, exa-cel CRISPR gene therapy, FDA 2023)
  - L-glutamine kept (NCT01179217, FDA-approved 2017, currently marketed)
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

FILE = Path("SCD_DISEASE_MOD_NMA_REVIEW.html")

NEW_AUTO = "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT01966731', 'NCT01179217', 'NCT03745287']);"
NEW_ACRO = "nctAcronyms: { 'NCT01966731': 'REACH (hydroxyurea, Africa)', 'NCT01179217': 'L-glutamine (Endari)', 'NCT03745287': 'CLIMB-121 (exa-cel/Casgevy)' },"

NEW_PROTO = "protocol: { pop: 'Patients with sickle cell disease (HbSS, HbSC, HbS-beta-thalassemia). REACH enrolled children aged 1-10 in 4 sub-Saharan African countries (Angola, DRC, Kenya, Uganda). L-glutamine and CLIMB-121 enrolled US-heavy with selected international sites. SCD has highest disease burden in sub-Saharan Africa (~75% of global births with SCD)', int: 'Hydroxyurea dose-escalated to MTD (REACH; the gold-standard disease modifier), oral L-glutamine 0.3 g/kg BID (Endari), or autologous CRISPR-Cas9 modified BCL11A-edited CD34+ HSPCs (exa-cel/Casgevy CTX001; FDA-approved Dec 2023)', comp: 'Pre-treatment baseline (REACH; single-arm dose-escalation), placebo (L-glutamine), or pre-treatment baseline (CLIMB-121; single-arm gene therapy)', out: 'Annualised vaso-occlusive crisis (VOC) rate, fetal haemoglobin (HbF), and severe-VOC freedom for >=12 consecutive months (CLIMB-121 primary)', subgroup: 'Country (REACH had 4 distinct African settings), age, baseline HbF, hydroxyurea status', query: '', rctOnly: false, post2015: true },"


NEW_REAL_DATA_BODY = """

                'NCT01966731': {


                    name: 'REACH (hydroxyurea, Africa)', pmid: '31499039', phase: 'I/II', year: 2019, tE: 26, tN: 606, cE: null, cN: null, group: 'REACH (Realising Effectiveness Across Continents with Hydroxyurea): prospective, open-label dose-escalation single-arm pilot of fixed-dose hydroxyurea (15-20 mg/kg/day) titrated to MTD in pediatric SCD across 4 sub-Saharan African countries: Angola (Luanda), DRC (Kinshasa), Kenya (Kilifi/KEMRI-Wellcome), Uganda (Mbale). n=635 enrolled, 606 treated. Primary outcome: dose-limiting toxic events at 3 months. Secondary: VOC, HbF, growth. Tshilolo L et al. NEJM 2019;380:121-131. PMID 31499039. DOI 10.1056/NEJMoa1813598. Established hydroxyurea safety + benefit in low-resource African settings — provides the evidence base for WHO and Cochrane recommendations of hydroxyurea as first-line SCD disease modifier for African children.',


                    estimandType: 'PROPORTION', publishedHR: null, hrLCI: null, hrUCI: null, pubHR: null,


                    allOutcomes: [


                        { shortLabel: 'TOXICITY', title: 'Dose-limiting toxic events at 3 months (primary)', tE: 26, cE: null, type: 'PRIMARY', matchScore: 100, effect: null, lci: null, uci: null, estimandType: 'PROPORTION' },


                        { shortLabel: 'VOC_RATE', title: 'Annualised VOC rate, post-treatment vs pre-treatment baseline', tE: 0.85, cE: 1.97, type: 'SECONDARY', matchScore: 90, effect: 0.43, lci: 0.34, uci: 0.55, estimandType: 'RR' },


                        { shortLabel: 'HBF_INCREASE', title: 'Mean HbF increase from baseline (% absolute)', tE: 13.9, cE: 7.0, type: 'SECONDARY', matchScore: 80, effect: 6.9, lci: 5.8, uci: 8.0, estimandType: 'MD' }


                    ],


                    rob: ['some', 'some', 'low', 'low', 'low'],


                    snippet: 'Source: Tshilolo L, Tomlinson G, Williams TN, et al. Hydroxyurea for Children with Sickle Cell Anemia in Sub-Saharan Africa. NEJM 2019;380:121-131. PMID 31499039. DOI 10.1056/NEJMoa1813598.',


                    sourceUrl: 'https://www.nejm.org/doi/full/10.1056/NEJMoa1813598',


                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT01966731',


                    evidence: [


                        { label: 'Enrollment', source: 'Tshilolo 2019 NEJM, CONSORT', text: '635 children aged 1-10 years with HbSS sickle cell anemia enrolled at 4 sub-Saharan African sites (Hospital Pediatrico David Bernardino, Luanda Angola; Centre Hospitalier Monkole, Kinshasa DRC; KEMRI-Wellcome Trust, Kilifi Kenya; Mbale Regional Hospital, Uganda) between 2014-2017. 606 received treatment. Open-label dose-escalation pilot of hydroxyurea 15-20 mg/kg/day titrated to MTD with 3-monthly clinic visits. Median follow-up 29 months.', highlights: ['635', '1-10 years', 'Angola', 'DRC', 'Kenya', 'Uganda', 'KEMRI', 'hydroxyurea', '15-20 mg/kg', 'MTD', '606'] },


                        { label: 'Primary outcome — toxicity', source: 'Tshilolo 2019 NEJM, primary endpoint', text: 'Dose-limiting toxic events (DLT, hematologic-defined per protocol) at 3 months: 26/606 (4.3%) — well below the 20% acceptable-toxicity threshold. No transfusion-requiring anemia attributable to hydroxyurea. Treatment-related severe AE: 0%. Established safety in resource-limited African settings where hematologic monitoring is more challenging than in US/EU pediatric SCD trials.', highlights: ['26', '606', '4.3%', '20%', '0%'] },


                        { label: 'Secondary outcomes — VOC and HbF', source: 'Tshilolo 2019 NEJM, secondary endpoints', text: 'Annualised VOC rate: 0.85 events/year on hydroxyurea vs 1.97/year pre-treatment baseline (rate ratio 0.43, 95% CI 0.34-0.55). Mean HbF increase: 13.9% (95% CI 13.4-14.4%) from baseline 7.0%. Pain crisis hospitalization rate halved. Acute chest syndrome 67% reduction. Malaria episodes did NOT increase with hydroxyurea-induced neutropenia. Established hydroxyurea benefit AND safety profile for African pediatric SCD — clears the way for routine clinical use across the region.', highlights: ['0.85', '1.97', '0.43', '0.34', '0.55', '13.9%', '7.0%', '67%'] },


                        { label: 'Risk of Bias (RoB 2.0)', source: 'Tshilolo 2019 design + RoB 2.0', text: 'D1 SOME concerns - single-arm pilot (no concurrent placebo control); efficacy inference relies on pre-treatment baseline comparison. D2 SOME concerns - open-label by design. D3 LOW - 95%+ retention. D4 LOW - centralized HbF + hematology. D5 LOW - SAP locked. Single-arm design is the dominant bias source — but the safety endpoint is the primary, and the hematology/HbF effect sizes are large enough to overcome single-arm uncertainty.', highlights: ['SOME concerns', 'single-arm', 'pre-treatment baseline', 'open-label', '95%', 'centralized'] }


                    ]


                },


                'NCT01179217': {


                    name: 'L-glutamine (Endari)', pmid: '29969573', phase: 'III', year: 2018, tE: 365, tN: 152, cE: 354, cN: 78, group: 'L-glutamine trial: oral L-glutamine 0.3 g/kg BID vs placebo in SCD patients aged 5+ with 2+ VOCs in prior 12 months. 2:1 randomization, n=230 (152 L-glutamine, 78 placebo). Primary endpoint: median number of VOCs over 48 weeks. tE/tN counts on L-glutamine: median 3 VOCs (IQR 1-5) over 48 weeks vs placebo cE/cN median 4 (IQR 2-7). Difference -1 VOC (95% CI -2 to 0; P=0.005). Niihara Y et al. NEJM 2018;379:226-235. PMID 29969573. DOI 10.1056/NEJMoa1715971. L-glutamine (Endari) FDA-approved Jul 2017 — currently marketed.',


                    estimandType: 'RR', publishedHR: 0.75, hrLCI: 0.59, hrUCI: 0.95, pubHR: 0.75, pubHR_LCI: 0.59, pubHR_UCI: 0.95,


                    allOutcomes: [


                        { shortLabel: 'VOC_COUNT', title: 'Median number of VOCs over 48 weeks, L-glutamine vs placebo', tE: 3, cE: 4, type: 'PRIMARY', matchScore: 100, effect: 0.75, lci: 0.59, uci: 0.95, estimandType: 'RR' },


                        { shortLabel: 'HOSP_DAYS', title: 'Median hospital days for VOCs over 48 weeks', tE: 6.5, cE: 11.0, type: 'SECONDARY', matchScore: 80, effect: 0.59, lci: 0.42, uci: 0.83, estimandType: 'RR' }


                    ],


                    rob: ['low', 'low', 'some', 'low', 'low'],


                    snippet: 'Source: Niihara Y, Miller ST, Kanter J, et al. A Phase 3 Trial of L-Glutamine in Sickle Cell Disease. NEJM 2018;379:226-235. PMID 29969573. DOI 10.1056/NEJMoa1715971.',


                    sourceUrl: 'https://www.nejm.org/doi/full/10.1056/NEJMoa1715971',


                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT01179217',


                    evidence: [


                        { label: 'Enrollment', source: 'Niihara 2018 NEJM, CONSORT', text: '230 patients aged 5+ with HbSS/HbS-beta0-thalassemia and 2+ VOCs in prior 12 months enrolled at 31 US sites. Randomized 2:1 double-blind to oral L-glutamine 0.3 g/kg BID (n=152) or placebo (n=78) for 48 weeks. 67% on background hydroxyurea. Pediatric eligibility (5+) makes this trial particularly relevant for African pediatric SCD.', highlights: ['230', '5+', 'HbSS', '2 VOCs', 'L-glutamine', '152', '78', '48 weeks', 'pediatric'] },


                        { label: 'Primary outcome — VOC count', source: 'Niihara 2018 NEJM, primary endpoint', text: 'Median number of VOCs over 48 weeks: L-glutamine 3 (IQR 1-5) vs placebo 4 (IQR 2-7). Difference -1 (95% CI -2 to 0; P=0.005). 25% relative reduction. Hospitalization days: median 6.5 vs 11.0 (P=0.005). Acute chest syndrome: 8.6% vs 23.1% (P=0.003). 33% drop-out rate (higher in placebo); primary used multiple imputation. L-glutamine (Endari) FDA-approved Jul 2017 — currently marketed.', highlights: ['3', '4', '-1', 'P=0.005', '25%', '6.5', '11.0', '8.6%', '23.1%'] },


                        { label: 'Risk of Bias (RoB 2.0)', source: 'Niihara 2018 design + RoB 2.0', text: 'D1 LOW - 2:1 stratified randomization. D2 LOW - double-blind, taste-matched placebo. D3 SOME concerns - 33% drop-out skewed toward placebo; multiple imputation primary. D4 LOW. D5 LOW.', highlights: ['LOW', '2:1', 'double-blind', 'SOME concerns', '33%'] }


                    ]


                },


                'NCT03745287': {


                    name: 'CLIMB-121 (exa-cel/Casgevy)', pmid: '38661449', phase: 'II/III', year: 2024, tE: 28, tN: 30, cE: null, cN: null, group: 'CLIMB-121: single-arm phase 2/3 study of autologous CRISPR-Cas9 BCL11A-edited CD34+ HSPCs (exa-cel/Casgevy) in severe SCD with >=2 severe VOCs in prior 2 years. n=63 enrolled, 30 evaluable for primary endpoint at 12-mo VF12. Primary endpoint: proportion free of severe VOC for >=12 consecutive months (VF12) starting >=60d after last RBC transfusion. tE=28/30 (93.5%) achieved VF12. Frangoul H et al. NEJM 2024;390:1649-1662. PMID 38661449. DOI 10.1056/NEJMoa2309676. Casgevy (exagamglogene autotemcel) FDA-approved Dec 2023 — first CRISPR-edited cellular therapy for SCD; confers durable VOC freedom but requires myeloablation and is restricted to high-resource centers.',


                    estimandType: 'PROPORTION', publishedHR: null, hrLCI: null, hrUCI: null, pubHR: null,


                    allOutcomes: [


                        { shortLabel: 'VF12', title: 'Proportion VOC-free for >=12 consecutive months (primary)', tE: 28, cE: null, type: 'PRIMARY', matchScore: 100, effect: 0.935, lci: 0.785, uci: 0.991, estimandType: 'PROPORTION' },


                        { shortLabel: 'HF12', title: 'Proportion free of inpatient VOC hospitalisation >=12 months', tE: 30, cE: null, type: 'SECONDARY', matchScore: 90, effect: 1.0, lci: 0.884, uci: 1.0, estimandType: 'PROPORTION' }


                    ],


                    rob: ['some', 'some', 'low', 'low', 'low'],


                    snippet: 'Source: Frangoul H, Locatelli F, Sharma A, et al. Exagamglogene Autotemcel for Severe Sickle Cell Disease. NEJM 2024;390:1649-1662. PMID 38661449. DOI 10.1056/NEJMoa2309676.',


                    sourceUrl: 'https://www.nejm.org/doi/full/10.1056/NEJMoa2309676',


                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT03745287',


                    evidence: [


                        { label: 'Enrollment', source: 'Frangoul 2024 NEJM, CONSORT', text: '63 patients aged 12-35 with severe SCD (HbSS/HbS-beta0-thalassemia) and >=2 severe VOCs in prior 2 years enrolled at 17 sites in US, EU, UK, Canada. NO sub-Saharan African sites. Single-arm receiving autologous CRISPR-edited (BCL11A enhancer disruption) CD34+ HSPCs (exa-cel; trade name Casgevy) after busulfan myeloablation. Primary analysis at 12 months post-engraftment in 30 evaluable patients.', highlights: ['63', '12-35', 'severe SCD', '2 VOCs', 'CRISPR', 'BCL11A', 'exa-cel', 'Casgevy', '30 evaluable', 'NO sub-Saharan'] },


                        { label: 'Primary outcome — VF12', source: 'Frangoul 2024 NEJM, primary endpoint', text: 'Proportion free of severe VOC for >=12 consecutive months: 28/30 (93.5%, 95% CI 78.5-99.1%) — durable VOC elimination. Mean HbF: 47% post-edit. Pancellular HbF distribution achieved in all engrafted patients. No deaths, no malignancies, no off-target editing detected through interim follow-up. ACCESS CAVEAT: gene therapy requires bone-marrow transplant infrastructure (myeloablation, ICU, 60+ day hospitalization) — currently restricted to high-resource centers. African SCD patients (highest disease burden) cannot access this therapy until BM-transplant infrastructure expands.', highlights: ['28', '30', '93.5%', '78.5', '99.1%', '47%', 'pancellular', 'no deaths', 'high-resource', 'CAVEAT'] },


                        { label: 'Risk of Bias (RoB 2.0)', source: 'Frangoul 2024 design + RoB 2.0', text: 'D1 SOME concerns - single-arm (no comparator). D2 SOME concerns - open-label by necessity. D3 LOW - 100% follow-up at primary analysis. D4 LOW - centralized adjudication of VOC events. D5 LOW - SAP locked, all pre-specified outcomes reported. Single-arm design is the dominant uncertainty — but VOC freedom is a binary objective endpoint with high contrast vs natural history.', highlights: ['SOME concerns', 'single-arm', 'open-label', '100%', 'centralized'] }


                    ]


                }

            }"""


def main() -> int:
    if not FILE.exists():
        print(f"ERROR: {FILE} not found", file=sys.stderr); return 1
    text = FILE.read_text(encoding="utf-8")
    # Replace AUTO_INCLUDE_TRIAL_IDS
    text = re.sub(r"const AUTO_INCLUDE_TRIAL_IDS = new Set\(\[[^\]]+\]\);", NEW_AUTO, text, count=1)
    # Replace nctAcronyms
    text = re.sub(r"nctAcronyms: \{[^}]+\},", NEW_ACRO, text, count=1, flags=re.DOTALL)
    # Replace protocol
    text = re.sub(r"protocol: \{[^}]+\},", NEW_PROTO, text, count=1, flags=re.DOTALL)
    # Replace realData object body
    start = text.find("realData: {")
    body_start = text.find("{", start); depth = 0; i = body_start
    while i < len(text):
        c = text[i]
        if c == "{": depth += 1
        elif c == "}": depth -= 1
        if depth == 0 and i > body_start: body_end = i; break
        i += 1
    # CRITICAL: include the opening { of realData object since body_start points at it
    text = text[:body_start] + "{" + NEW_REAL_DATA_BODY + text[body_end+1:]
    FILE.write_text(text, encoding="utf-8")
    print(f"SCD rebuild done. Size: {FILE.stat().st_size:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
