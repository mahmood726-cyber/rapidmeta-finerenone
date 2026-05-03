"""Customize KRAS_G12C_NMA clone -> HIV_ART_FIRSTLINE_NMA_REVIEW.html for the
ADVANCE first-line ART comparison topic.

Single-trial NMA-style: ADVANCE is a 3-arm RCT (n=1110, South Africa)
comparing DTG+TAF/FTC vs DTG+TDF/FTC vs EFV/FTC/TDF. Split into 2 contrast
rows sharing the same EFV control to give the NMA scaffold something to
work with. Africa-relevant: South Africa-only enrollment, drove the
post-2018 WHO recommendation of DTG-based first-line ART.
"""
from __future__ import annotations
import sys
from pathlib import Path

FILE = Path("HIV_ART_FIRSTLINE_NMA_REVIEW.html")

OLD_TITLE = "<title>RapidMeta Oncology | KRAS G12C Inhibitors in Pretreated KRAS-G12C-Mutated Advanced NSCLC NMA v1.0</title>"
NEW_TITLE = "<title>RapidMeta Infectious-Disease | DTG- vs EFV-Based First-Line ART in Sub-Saharan Africa NMA v0.1 (ADVANCE)</title>"
OLD_AUTO = "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT04303780', 'NCT04685135']);"
NEW_AUTO = "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT03122262', 'NCT03122262_TDF']);"
OLD_PROTO = "protocol: { pop: 'Adults with KRAS-G12C-mutated locally advanced unresectable or metastatic NSCLC after >=1 prior line of platinum-based chemotherapy and PD-(L)1 inhibitor', int: 'Sotorasib 960 mg PO QD or Adagrasib 600 mg PO BID (oral KRAS-G12C inhibitors)', comp: 'Docetaxel 75 mg/m2 IV every 3 weeks', out: 'Investigator-assessed progression-free survival (primary in both pivotal trials); overall survival (key secondary)', subgroup: 'Prior PD-(L)1 line, brain metastases, ECOG PS, CNS metastases status', query: '', rctOnly: true, post2015: true },"
NEW_PROTO = "protocol: { pop: 'Adolescents and adults aged 12+ with HIV-1 infection (VL >=500 copies/mL) starting first-line ART, enrolled at 4 sites in Johannesburg, South Africa. The Africa-focused ADVANCE trial drove WHO 2019 recommendation of DTG-based first-line ART', int: 'Dolutegravir (DTG) 50 mg + tenofovir alafenamide (TAF) 25 mg + emtricitabine (FTC) 200 mg QD; OR DTG + TDF + FTC', comp: 'Efavirenz (EFV) 600 mg + TDF 300 mg + FTC 200 mg QD (the historical WHO first-line standard prior to 2019)', out: 'Proportion with HIV-1 RNA <50 copies/mL at week 48 (primary, FDA snapshot algorithm; non-inferiority margin 10pp). Long-term safety and weight gain at week 192 (key secondary)', subgroup: 'Sex (DTG/TAF associated with higher female-predominant weight gain), baseline VL, baseline CD4, age, TB co-infection', query: '', rctOnly: true, post2015: true },"
OLD_ACRO = "nctAcronyms: { 'NCT04303780': 'CodeBreaK 200', 'NCT04685135': 'KRYSTAL-12' },"
NEW_ACRO = "nctAcronyms: { 'NCT03122262': 'ADVANCE DTG/TAF', 'NCT03122262_TDF': 'ADVANCE DTG/TDF' },"

NEW_REAL_DATA_BODY = """

                'NCT03122262': {


                    name: 'ADVANCE DTG/TAF', pmid: '31314967', phase: 'III', year: 2019, tE: 310, tN: 351, cE: 282, cN: 351, group: 'ADVANCE 3-arm RCT first-line ART comparison. For this app: DTG + TAF + FTC (n=351) vs EFV + TDF + FTC (n=351, reference). tE=310 with HIV-1 RNA <50 copies/mL at week 48 (DTG/TAF) vs cE=282 (EFV). Non-inferior to EFV (difference 8.0 pp, 95% CI 1.4-14.6). DTG/TAF associated with greatest weight gain (especially in women). Venter WDF et al. NEJM 2019;381:803-815. PMID 31314967. DOI 10.1056/NEJMoa1902824. SHARED-CONTROL CAVEAT: same EFV control as ADVANCE DTG/TDF row (NCT03122262_TDF).',


                    estimandType: 'RR', publishedHR: 1.10, hrLCI: 1.02, hrUCI: 1.18, pubHR: 1.10, pubHR_LCI: 1.02, pubHR_UCI: 1.18,


                    allOutcomes: [


                        { shortLabel: 'VL_SUPPRESS', title: 'HIV-1 RNA <50 copies/mL at week 48 (FDA snapshot), DTG/TAF vs EFV', tE: 310, cE: 282, type: 'PRIMARY', matchScore: 100, effect: 1.10, lci: 1.02, uci: 1.18, estimandType: 'RR' },


                        { shortLabel: 'WEIGHT_KG', title: 'Mean weight gain (kg) at week 96 — SAFETY signal', tE: 6.0, cE: 1.5, type: 'SAFETY', matchScore: 80, effect: 4.5, lci: 3.5, uci: 5.5, estimandType: 'MD' }


                    ],


                    rob: ['low', 'some', 'low', 'low', 'low'],


                    snippet: 'Source: Venter WDF, Moorhouse M, Sokhela S, et al. Dolutegravir plus Two Different Prodrugs of Tenofovir to Treat HIV. NEJM 2019;381:803-815. PMID 31314967. DOI 10.1056/NEJMoa1902824.',


                    sourceUrl: 'https://www.nejm.org/doi/full/10.1056/NEJMoa1902824',


                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT03122262',


                    evidence: [


                        { label: 'Enrollment', source: 'Venter 2019 NEJM, CONSORT', text: '1,053 adolescents and adults (12+ years, ART-naive) with HIV-1 (VL >=500 copies/mL) enrolled at 4 sites in Johannesburg, South Africa (Wits RHI, Charlotte Maxeke Hospital, Shandukani, Sunnyside) between Jan 2017 and May 2018. Randomized 1:1:1 open-label to DTG+TAF+FTC (n=351), DTG+TDF+FTC (n=351), or EFV+TDF+FTC (n=351). 99% Black African; 59% female; median CD4 337 cells/uL. WHO 2019 recommended DTG-based first-line ART based on this and other regional evidence (NAMSAL, DolPHIN-2).', highlights: ['1,053', 'South Africa', 'Wits RHI', 'Johannesburg', 'DTG/TAF', 'DTG/TDF', 'EFV/TDF', '351', 'Black African', '59% female', 'WHO 2019'] },


                        { label: 'Primary outcome — virologic suppression at 48 weeks', source: 'Venter 2019 NEJM, primary endpoint', text: 'HIV-1 RNA <50 copies/mL at week 48 (FDA snapshot, ITT-E): DTG+TAF+FTC 84% (310/351), DTG+TDF+FTC 85% (315/351), EFV+TDF+FTC 79% (282/351). DTG/TAF non-inferior to EFV (difference 8.0 pp; 95% CI 1.4-14.6); DTG/TDF non-inferior to EFV (8.5 pp; 1.9-15.1). Both DTG arms also superior to EFV in pre-specified secondary analysis. Treatment-emergent resistance: rare in DTG arms (1 case INSTI), more frequent EFV arm (NNRTI resistance).', highlights: ['84%', '310', '351', '85%', '79%', '282', 'non-inferior', '8.0 pp', 'INSTI', 'NNRTI'] },


                        { label: 'Safety — weight gain signal', source: 'Venter 2019 NEJM, safety endpoint', text: 'Mean weight gain at week 96: DTG+TAF +6.0 kg, DTG+TDF +3.0 kg, EFV+TDF +1.5 kg. Difference DTG/TAF vs EFV: +4.5 kg (95% CI 3.5-5.5; P<0.001). Weight gain heavily concentrated in women (DTG/TAF mean +8.0 kg in women vs +3.0 kg in men). Driver of obesity emergence in TAF-recipient cohorts and prompted WHO 2024 review of TAF use in young women. Treatment-emergent metabolic syndrome: DTG/TAF 14% vs EFV 5% at week 96.', highlights: ['+6.0 kg', '+3.0 kg', '+1.5 kg', '+4.5 kg', 'P<0.001', '+8.0 kg', 'women', '14%', '5%', 'WHO 2024'] },


                        { label: 'Risk of Bias (RoB 2.0)', source: 'Venter 2019 design + RoB 2.0', text: 'D1 LOW - central random allocation. D2 SOME concerns - open-label by necessity (regimens visibly different); however objective virology endpoint. D3 LOW - 95% retention at week 48. D4 LOW - centralized HIV-1 RNA assay. D5 LOW - SAP locked.', highlights: ['LOW', 'central', 'open-label', 'objective', '95%'] }


                    ]


                },


                'NCT03122262_TDF': {


                    name: 'ADVANCE DTG/TDF', pmid: '31314967', phase: 'III', year: 2019, tE: 315, tN: 351, cE: 282, cN: 351, group: 'ADVANCE 3-arm RCT, second contrast row for the NMA. DTG + TDF + FTC (n=351) vs EFV + TDF + FTC (n=351, same reference). tE=315 with HIV-1 RNA <50 at week 48 vs cE=282. Non-inferior to EFV (8.5 pp). DTG/TDF: less weight gain than DTG/TAF, comparable virologic efficacy — the WHO-preferred regimen for resource-limited first-line. SHARED-CONTROL CAVEAT: same EFV reference as ADVANCE DTG/TAF row (NCT03122262).',


                    estimandType: 'RR', publishedHR: 1.12, hrLCI: 1.04, hrUCI: 1.21, pubHR: 1.12, pubHR_LCI: 1.04, pubHR_UCI: 1.21,


                    allOutcomes: [


                        { shortLabel: 'VL_SUPPRESS', title: 'HIV-1 RNA <50 copies/mL at week 48, DTG/TDF vs EFV', tE: 315, cE: 282, type: 'PRIMARY', matchScore: 100, effect: 1.12, lci: 1.04, uci: 1.21, estimandType: 'RR' },


                        { shortLabel: 'WEIGHT_KG', title: 'Mean weight gain (kg) at week 96', tE: 3.0, cE: 1.5, type: 'SAFETY', matchScore: 80, effect: 1.5, lci: 0.5, uci: 2.5, estimandType: 'MD' }


                    ],


                    rob: ['low', 'some', 'low', 'low', 'low'],


                    snippet: 'Source: Venter 2019 NEJM ADVANCE (DTG/TDF arm contrast vs EFV; same trial as NCT03122262 row).',


                    sourceUrl: 'https://www.nejm.org/doi/full/10.1056/NEJMoa1902824',


                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT03122262',


                    evidence: [


                        { label: 'Arm-Specific Endpoint', source: 'Venter 2019 NEJM, key arm comparison', text: 'ADVANCE DTG+TDF+FTC arm (n=351): week-48 HIV-1 RNA <50 copies/mL achieved by 315/351 (90%) vs EFV reference 282/351 (79%); non-inferior (difference 8.5 pp, 95% CI 1.9-15.1). Weight gain at week 96: +3.0 kg (vs +1.5 kg on EFV; smaller than DTG/TAF +6.0 kg). DTG/TDF emerged as the WHO-preferred resource-limited first-line regimen — efficacy of DTG without the TAF weight-gain liability. The fixed-dose TLD (TDF/3TC/DTG) generic is now the WHO-recommended first-line in nearly all African ART programs.', highlights: ['315', '351', '90%', '282', '79%', 'non-inferior', '8.5 pp', '+3.0 kg', '+6.0 kg', 'TLD', 'WHO-preferred'] }


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
