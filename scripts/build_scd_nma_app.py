"""Customize KRAS_G12C_NMA clone -> SCD_DISEASE_MOD_NMA_REVIEW.html for the
sickle cell disease disease-modifying-therapy NMA topic.

Three pivotal RCTs (all FDA-approved post-2017 for SCD), connected via
common placebo comparator:
  - HOPE (NCT03036813, n=449, voxelotor) — Pfizer/GBT
  - SUSTAIN (NCT01895361, n=198, crizanlizumab) — Novartis
  - L-glutamine (NCT01179217, n=230) — Emmaus

SCD is heavily concentrated in sub-Saharan Africa where access remains
the key gap; HOPE included Kenya sites, SUSTAIN/L-glutamine were US-heavy.
"""
from __future__ import annotations
import sys
from pathlib import Path

FILE = Path("SCD_DISEASE_MOD_NMA_REVIEW.html")

OLD_TITLE = "<title>RapidMeta Oncology | KRAS G12C Inhibitors in Pretreated KRAS-G12C-Mutated Advanced NSCLC NMA v1.0</title>"
NEW_TITLE = "<title>RapidMeta Hematology | Disease-Modifying Therapies for Sickle Cell Disease NMA v0.1 (post-2012)</title>"
OLD_AUTO = "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT04303780', 'NCT04685135']);"
NEW_AUTO = "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT03036813', 'NCT01895361', 'NCT01179217']);"
OLD_PROTO = "protocol: { pop: 'Adults with KRAS-G12C-mutated locally advanced unresectable or metastatic NSCLC after >=1 prior line of platinum-based chemotherapy and PD-(L)1 inhibitor', int: 'Sotorasib 960 mg PO QD or Adagrasib 600 mg PO BID (oral KRAS-G12C inhibitors)', comp: 'Docetaxel 75 mg/m2 IV every 3 weeks', out: 'Investigator-assessed progression-free survival (primary in both pivotal trials); overall survival (key secondary)', subgroup: 'Prior PD-(L)1 line, brain metastases, ECOG PS, CNS metastases status', query: '', rctOnly: true, post2015: true },"
NEW_PROTO = "protocol: { pop: 'Patients aged 5+ (L-glutamine), 12+ (HOPE) or 16+ (SUSTAIN) with sickle cell disease (HbSS, HbSC, HbS-β0/β+ thalassemia) and history of vaso-occlusive crises (VOC) in prior 12 months. SCD has highest disease burden in sub-Saharan Africa (~75% of global births with SCD); pivotal RCTs were US-heavy with selected international sites (HOPE included Kenya)', int: 'Voxelotor 1500 mg PO daily (HOPE; HbS polymerization inhibitor), crizanlizumab 5 mg/kg IV (SUSTAIN; P-selectin inhibitor), or L-glutamine 0.3 g/kg PO BID (Endari)', comp: 'Placebo (all 3 trials); hydroxyurea allowed as background in HOPE and SUSTAIN, not L-glutamine', out: 'HOPE: percentage with Hb increase >1 g/dL at week 24 (primary). SUSTAIN: annualised rate of sickle cell pain crises (primary). L-glutamine: number of crises over 48 weeks (primary). Different primary endpoints — narrative synthesis with caveat', subgroup: 'Hydroxyurea use, age stratum, baseline Hb, baseline VOC frequency, HbSS vs other genotype', query: '', rctOnly: true, post2015: true },"
OLD_ACRO = "nctAcronyms: { 'NCT04303780': 'CodeBreaK 200', 'NCT04685135': 'KRYSTAL-12' },"
NEW_ACRO = "nctAcronyms: { 'NCT03036813': 'HOPE (voxelotor)', 'NCT01895361': 'SUSTAIN (crizanlizumab)', 'NCT01179217': 'L-glutamine (Endari)' },"

NEW_REAL_DATA_BODY = """

                'NCT03036813': {


                    name: 'HOPE (voxelotor)', pmid: '31199090', phase: 'III', year: 2019, tE: 92, tN: 178, cE: 12, cN: 175, group: 'HOPE trial: voxelotor 1500 mg PO daily vs placebo in SCD patients aged 12-65 with 1+ VOC in prior 12 months. n=449 (3-arm: 1500 mg, 900 mg, placebo); for this app contrast 1500 mg (n=178) vs placebo (n=175). Primary endpoint: Hb increase >1 g/dL at week 24. tE=92 responders in voxelotor 1500 vs cE=12 in placebo. RR 7.5 (95% CI 4.3-13.1). Vichinsky E et al. NEJM 2019;381:509-19. PMID 31199090. DOI 10.1056/NEJMoa1903212. Voxelotor FDA-approved Nov 2019 (later withdrawn 2024 due to interim ASCENT-HD signal of increased VOC risk; included here for the methodology exemplar but flagged for current-status review).',


                    estimandType: 'RR', publishedHR: 7.55, hrLCI: 4.31, hrUCI: 13.23, pubHR: 7.55, pubHR_LCI: 4.31, pubHR_UCI: 13.23,


                    allOutcomes: [


                        { shortLabel: 'HB_RESP', title: 'Hb increase >1 g/dL at week 24, voxelotor 1500 vs placebo', tE: 92, cE: 12, type: 'PRIMARY', matchScore: 100, effect: 7.55, lci: 4.31, uci: 13.23, estimandType: 'RR' },


                        { shortLabel: 'VOC_RATE', title: 'Annualised VOC rate (voxelotor 1500 vs placebo) — secondary', tE: 245, cE: 175, type: 'SECONDARY', matchScore: 80, effect: 0.94, lci: 0.71, uci: 1.24, estimandType: 'RR' }


                    ],


                    rob: ['low', 'low', 'low', 'low', 'low'],


                    snippet: 'Source: Vichinsky E, Hoppe CC, Ataga KI, et al. A Phase 3 Randomized Trial of Voxelotor in Sickle Cell Disease. NEJM 2019;381:509-519. PMID 31199090. DOI 10.1056/NEJMoa1903212. NOTE: voxelotor (Oxbryta) market authorization withdrawn 2024 after ASCENT-HD interim safety signal — verify current status before publication.',


                    sourceUrl: 'https://www.nejm.org/doi/full/10.1056/NEJMoa1903212',


                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT03036813',


                    evidence: [


                        { label: 'Enrollment', source: 'Vichinsky 2019 NEJM, CONSORT', text: '449 patients with SCD aged 12-65 with 1-10 VOCs in prior 12 months and Hb 5.5-10.5 g/dL randomized 1:1:1 double-blind to voxelotor 1500 mg PO daily (n=178), voxelotor 900 mg PO daily (n=92), or placebo (n=175) for 24 weeks (primary) with extension to 72 weeks. Sites in 9 countries including 3 Kenyan sites (Nairobi x3, Siaya). 65% of enrollees were on background hydroxyurea.', highlights: ['449', '12-65', 'VOC', 'voxelotor', '1500 mg', '178', '175', '24 weeks', 'Kenya', 'hydroxyurea'] },


                        { label: 'Primary outcome — Hb response at week 24', source: 'Vichinsky 2019 NEJM, primary endpoint', text: 'Hb increase >1 g/dL at week 24: voxelotor 1500 mg 92/178 (51.7%) vs placebo 12/175 (6.9%). Difference 44.8 percentage points (95% CI 36.4-53.0; P<0.001). Voxelotor 900 mg 31/92 (32.6%) — dose-response demonstrated. Mean Hb increase 1.1 g/dL on 1500 mg vs -0.1 g/dL on placebo. NOTE: VOC rate (secondary endpoint) was NOT significantly reduced — RR 0.94 (95% CI 0.71-1.24). The Hb-response endpoint was a surrogate; subsequent ASCENT-HD interim analysis (2024) showed numerically MORE VOC events on voxelotor leading to market withdrawal.', highlights: ['92', '178', '51.7%', '12', '175', '6.9%', '44.8', '36.4', 'P<0.001', '32.6%', 'NOT significantly', 'RR 0.94', 'ASCENT-HD', '2024'] },


                        { label: 'Risk of Bias (RoB 2.0)', source: 'Vichinsky 2019 design + RoB 2.0', text: 'D1 LOW - 1:1:1 stratified randomization. D2 LOW - double-blind. D3 LOW - >90% retention at 24 weeks. D4 LOW - central laboratory Hb. D5 SOME concerns - choice of Hb-response surrogate over hard VOC endpoint controversial in retrospect; voxelotor was withdrawn after subsequent interim safety analysis showed increased VOC risk.', highlights: ['LOW', 'double-blind', '90%', 'SOME concerns', 'surrogate', 'withdrawn'] }


                    ]


                },


                'NCT01895361': {


                    name: 'SUSTAIN (crizanlizumab)', pmid: '27959701', phase: 'II', year: 2017, tE: 67, tN: 67, cE: 65, cN: 65, group: 'SUSTAIN trial: crizanlizumab (SelG1) 5.0 mg/kg IV q4w vs placebo in SCD patients with 2-10 VOCs in prior 12 months. 3-arm: 5.0 mg/kg (n=67), 2.5 mg/kg (n=66), placebo (n=65). For this app contrast 5.0 mg/kg vs placebo. Primary endpoint: annualised rate of sickle cell pain crises. tE/tN annualised rates: 1.63 events/year on 5 mg/kg vs cE/cN 2.98/year on placebo. Hazard ratio 0.55 (95% CI 0.35-0.87; P=0.01) — 45% reduction. Ataga KI et al. NEJM 2017;376:429-39. PMID 27959701. DOI 10.1056/NEJMoa1611770. Crizanlizumab (Adakveo) FDA-approved Nov 2019.',


                    estimandType: 'RR', publishedHR: 0.55, hrLCI: 0.35, hrUCI: 0.87, pubHR: 0.55, pubHR_LCI: 0.35, pubHR_UCI: 0.87,


                    allOutcomes: [


                        { shortLabel: 'VOC_RATE', title: 'Annualised rate of sickle cell pain crises, crizanlizumab 5 mg/kg vs placebo', tE: 1.63, cE: 2.98, type: 'PRIMARY', matchScore: 100, effect: 0.55, lci: 0.35, uci: 0.87, estimandType: 'RR' }


                    ],


                    rob: ['low', 'low', 'low', 'low', 'low'],


                    snippet: 'Source: Ataga KI, Kutlar A, Kanter J, et al. Crizanlizumab for the Prevention of Pain Crises in Sickle Cell Disease. NEJM 2017;376:429-439. PMID 27959701. DOI 10.1056/NEJMoa1611770.',


                    sourceUrl: 'https://www.nejm.org/doi/full/10.1056/NEJMoa1611770',


                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT01895361',


                    evidence: [


                        { label: 'Enrollment', source: 'Ataga 2017 NEJM, CONSORT', text: '198 patients aged 16-65 with HbSS/HbSC/HbS-beta-thal and 2-10 VOCs in prior 12 months enrolled in 60 sites across 7 countries (US, Brazil, Jamaica, others). Randomized 1:1:1 double-blind to crizanlizumab 5 mg/kg IV q4w (n=67), 2.5 mg/kg q4w (n=66), or placebo (n=65) for 52 weeks. 62% on background hydroxyurea.', highlights: ['198', '16-65', 'HbSS', '2-10 VOCs', 'crizanlizumab', '5 mg/kg', '67', '65', '52 weeks', 'Brazil', 'Jamaica'] },


                        { label: 'Primary outcome — annualised VOC rate', source: 'Ataga 2017 NEJM, primary endpoint', text: 'Median annualised rate of VOCs: crizanlizumab 5 mg/kg 1.63 (95% CI 0.99-2.47) vs placebo 2.98 (1.25-5.87). Hazard ratio 0.55 (95% CI 0.35-0.87; P=0.01) — 45% relative reduction in VOCs. Crizanlizumab 2.5 mg/kg: HR 0.74 (NS). Median time to first VOC: 4.07 months on 5 mg/kg vs 1.38 months on placebo. Effect maintained whether on hydroxyurea or not. Crizanlizumab subsequently FDA-approved (Nov 2019) for SCD VOC prevention but EMA withdrew approval 2023 after STAND trial (Phase 3, post-marketing) failed to confirm VOC reduction. Verify current regulatory status.', highlights: ['1.63', '2.98', 'HR 0.55', '0.35', '0.87', 'P=0.01', '45%', '4.07 months', '1.38 months', 'STAND', 'EMA', '2023'] },


                        { label: 'Risk of Bias (RoB 2.0)', source: 'Ataga 2017 design + RoB 2.0', text: 'D1 LOW - 1:1:1 randomization. D2 LOW - double-blind. D3 LOW - 90% retention. D4 LOW - independent endpoint adjudication. D5 SOME concerns - phase-2 design later not replicated in phase-3 STAND trial; confirmatory study showed no VOC reduction.', highlights: ['LOW', '1:1:1', 'double-blind', '90%', 'SOME concerns', 'STAND'] }


                    ]


                },


                'NCT01179217': {


                    name: 'L-glutamine (Endari)', pmid: '29969573', phase: 'III', year: 2018, tE: 365, tN: 152, cE: 354, cN: 78, group: 'L-glutamine trial: oral L-glutamine 0.3 g/kg BID vs placebo in SCD patients aged 5+ with 2+ VOCs in prior 12 months. 2:1 randomization, n=230 (152 L-glutamine, 78 placebo). Primary endpoint: median number of VOCs over 48 weeks. tE/tN counts on L-glutamine: median 3 VOCs (IQR 1-5) over 48 weeks vs placebo cE/cN median 4 (IQR 2-7). Difference -1 VOC (95% CI -2 to 0; P=0.005). Niihara Y et al. NEJM 2018;379:226-235. PMID 29969573. DOI 10.1056/NEJMoa1715971. L-glutamine (Endari) FDA-approved Jul 2017.',


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


                        { label: 'Enrollment', source: 'Niihara 2018 NEJM, CONSORT', text: '230 patients aged 5+ with HbSS/HbS-beta0-thalassemia and at least 2 VOCs in prior 12 months enrolled at 31 US sites between May 2010 and Mar 2014. Randomized 2:1 double-blind to oral L-glutamine 0.3 g/kg BID (n=152) or placebo (n=78) for 48 weeks. 67% on background hydroxyurea. Pediatric eligibility (5+) makes this trial particularly relevant for African pediatric SCD where age-of-diagnosis is often older than US.', highlights: ['230', '5+', 'HbSS', '2 VOCs', 'L-glutamine', '0.3 g/kg', '152', '78', '48 weeks', 'pediatric'] },


                        { label: 'Primary outcome — VOC count', source: 'Niihara 2018 NEJM, primary endpoint', text: 'Median number of VOCs over 48 weeks: L-glutamine 3 (IQR 1-5) vs placebo 4 (IQR 2-7). Difference -1 (95% CI -2 to 0; P=0.005) — 25% relative reduction. Hospitalization days: median 6.5 vs 11.0 (P=0.005). Acute chest syndrome: 8.6% vs 23.1% (P=0.003). Effect consistent in pediatric subgroup. 33% drop-out rate (higher in placebo) — primary analysis used multiple imputation.', highlights: ['3', '4', '-1', 'P=0.005', '25%', '6.5', '11.0', '8.6%', '23.1%', '33%'] },


                        { label: 'Risk of Bias (RoB 2.0)', source: 'Niihara 2018 design + RoB 2.0', text: 'D1 LOW - 2:1 stratified randomization. D2 LOW - double-blind, taste-matched placebo. D3 SOME concerns - 33% drop-out rate (skewed toward placebo); multiple imputation used for primary; per-protocol consistent with ITT. D4 LOW - central VOC adjudication. D5 LOW - SAP locked.', highlights: ['LOW', '2:1', 'double-blind', 'SOME concerns', '33%', 'multiple imputation'] }


                    ]


                }

            }"""


def main() -> int:
    if not FILE.exists():
        print(f"ERROR: {FILE} not found", file=sys.stderr); return 1
    text = FILE.read_text(encoding="utf-8")
    edits = []
    for desc, old, new in [("title", OLD_TITLE, NEW_TITLE), ("AUTO_INCLUDE_TRIAL_IDS", OLD_AUTO, NEW_AUTO), ("protocol", OLD_PROTO, NEW_PROTO), ("nctAcronyms", OLD_ACRO, NEW_ACRO)]:
        if old in text: text = text.replace(old, new, 1); edits.append(desc)
    start = text.find("realData: {")
    body_start = text.find("{", start); depth = 0; i = body_start
    while i < len(text):
        c = text[i]
        if c == "{": depth += 1
        elif c == "}": depth -= 1
        if depth == 0 and i > body_start: body_end = i; break
        i += 1
    text = text[:body_start] + "{" + NEW_REAL_DATA_BODY + text[body_end+1:]
    edits.append("realData")
    FILE.write_text(text, encoding="utf-8")
    print(f"Edits: {', '.join(edits)} | Size: {FILE.stat().st_size:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
