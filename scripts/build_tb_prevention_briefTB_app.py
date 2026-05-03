"""Customize SGLT2_HF clone -> TB_PREVENTION_REVIEW.html for the BRIEF-TB
1HP-vs-9H latent TB prevention pairwise topic.

BRIEF-TB (NCT01404312, n=3000): 1 month rifapentine+isoniazid daily
(1HP) vs 9 months isoniazid daily (9H) in HIV-infected adults at risk
for active TB. Africa-heavy enrollment (Botswana, Kenya, Malawi,
South Africa, Zimbabwe). Drove WHO 2018 endorsement of 1HP for HIV+
populations in high-TB-burden settings.
"""
from __future__ import annotations
import sys
from pathlib import Path

FILE = Path("TB_PREVENTION_REVIEW.html")

OLD_TITLE = "<title>RapidMeta Cardiology | SGLT2-HF Ultra-Precision v12.0</title>"
NEW_TITLE = "<title>RapidMeta Infectious-Disease | 1HP vs 9H for Latent TB in HIV-Infected Adults v0.1 (BRIEF-TB, sub-Saharan Africa post-2012)</title>"
OLD_AUTO = "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT03036124', 'NCT03057977', 'NCT03057951', 'NCT03619213', 'NCT03521934']);"
NEW_AUTO = "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT01404312']);"
OLD_PROTO = "protocol: { pop: 'Adults with heart failure across ejection fraction spectrum', int: 'SGLT2 or dual SGLT1/2 inhibitor therapy (dapagliflozin, empagliflozin, or sotagliflozin)', comp: 'Placebo + guideline-directed therapy', out: 'CV Death or Worsening Heart Failure Composite', subgroup: 'EF phenotype (HFrEF vs HFpEF), drug class member, diabetes status', query: '', rctOnly: true, post2015: true },"
NEW_PROTO = "protocol: { pop: 'HIV-infected adults aged 13+ with latent TB infection (positive TST or IGRA, or living in high TB-burden area) and CD4 count permitting safe ART, enrolled at 45 sites including 5 sub-Saharan African countries (Botswana, Kenya, Malawi, South Africa, Zimbabwe — ~64% of trial enrollment)', int: '1HP: rifapentine 300 mg + isoniazid 300 mg daily for 28 days (4 weeks total)', comp: '9H: isoniazid 300 mg daily for 9 months (the historical WHO standard for HIV-positive LTBI)', out: 'Composite primary: first diagnosis of active TB, TB-related death, or death from unknown cause through 3-year follow-up. Non-inferiority margin 1.25 for hazard ratio', subgroup: 'CD4 stratum, country/TB-burden setting, IGRA-positive vs TST-positive, ART regimen', query: '', rctOnly: true, post2015: true },"
OLD_ACRO = """nctAcronyms: {


                'NCT03036124': 'DAPA-HF',


                'NCT03057977': 'EMPEROR-Reduced',


                'NCT03057951': 'EMPEROR-Preserved',


                'NCT03619213': 'DELIVER',


                'NCT03521934': 'SOLOIST-WHF'


            }"""
NEW_ACRO = """nctAcronyms: {


                'NCT01404312': 'BRIEF-TB / A5279'


            }"""

NEW_REAL_DATA_BODY = """

                'NCT01404312': {


                    name: 'BRIEF-TB / A5279', pmid: '30855125', phase: 'III', year: 2019, tE: 32, tN: 1488, cE: 33, cN: 1498, group: 'BRIEF-TB (ACTG A5279) trial: 1HP (rifapentine + isoniazid 1 month) vs 9H (isoniazid 9 months) in HIV-positive adults at risk of active TB. tE=32 incident TB events (or TB-related death/unknown-cause death) on 1HP arm (n=1488) vs cE=33 on 9H arm (n=1498). Composite incidence rate 0.65 vs 0.67 per 100 person-years; HR 0.97 (95% CI 0.59-1.61). Non-inferiority margin 1.25 met. Treatment completion: 1HP 97% vs 9H 90% (P<0.001) — major adherence advantage. Swindells S et al. NEJM 2019;380:1001-1011. PMID 30855125. DOI 10.1056/NEJMoa1806808. WHO 2018 endorsed 1HP for HIV-positive LTBI based on these results.',


                    estimandType: 'HR', publishedHR: 0.97, hrLCI: 0.59, hrUCI: 1.61, pubHR: 0.97, pubHR_LCI: 0.59, pubHR_UCI: 1.61,


                    allOutcomes: [


                        { shortLabel: 'TB_COMP', title: 'First diagnosis of active TB, TB-related death, or unknown-cause death (composite primary)', tE: 32, cE: 33, type: 'PRIMARY', matchScore: 100, effect: 0.97, lci: 0.59, uci: 1.61, estimandType: 'HR' },


                        { shortLabel: 'COMPLETION', title: 'Treatment completion rate', tE: 1444, cE: 1348, type: 'SECONDARY', matchScore: 90, effect: 1.07, lci: 1.05, uci: 1.10, estimandType: 'RR' },


                        { shortLabel: 'GR3_AE', title: 'Grade 3+ adverse event during treatment', tE: 89, cE: 105, type: 'SAFETY', matchScore: 80, effect: 0.85, lci: 0.65, uci: 1.13, estimandType: 'RR' }


                    ],


                    rob: ['low', 'some', 'low', 'low', 'low'],


                    snippet: 'Source: Swindells S, Ramchandani R, Gupta A, et al. One Month of Rifapentine plus Isoniazid to Prevent HIV-Related Tuberculosis. NEJM 2019;380:1001-1011. PMID 30855125. DOI 10.1056/NEJMoa1806808.',


                    sourceUrl: 'https://www.nejm.org/doi/full/10.1056/NEJMoa1806808',


                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT01404312',


                    evidence: [


                        { label: 'Enrollment', source: 'Swindells 2019 NEJM, CONSORT', text: '3,000 HIV-positive adults aged 13+ with TST/IGRA-positive LTBI or living in a high TB-burden area enrolled at 45 sites in 10 countries. Sub-Saharan African enrollment dominated: Botswana, Kenya, Malawi, South Africa, Zimbabwe (~64% of total). Other sites: US, Brazil, Haiti, Peru, Thailand. Randomized 1:1 open-label to 1HP (n=1488) or 9H (n=1498). Median CD4 470 cells/uL; 50% on ART at baseline. Followed for median 3.3 years.', highlights: ['3,000', 'HIV-positive', '45 sites', 'Botswana', 'Kenya', 'Malawi', 'South Africa', 'Zimbabwe', '64%', '1488', '1498', '3.3 years'] },


                        { label: 'Primary outcome — TB events at 3-year follow-up', source: 'Swindells 2019 NEJM, primary endpoint', text: 'Composite primary (incident TB, TB-related death, or unknown-cause death): 1HP 32/1488 (incidence 0.65 per 100 person-years) vs 9H 33/1498 (0.67/100py). HR 0.97 (95% CI 0.59-1.61). Non-inferiority margin (HR 1.25) met. Treatment completion: 1HP 97% vs 9H 90% (P<0.001). Grade 3+ AEs during treatment: 1HP 6% vs 9H 7% (NS). 1-month all-oral regimen with comparable efficacy and superior adherence — drove WHO 2018 endorsement and is now a preferred LTBI regimen for HIV-positive populations in high-burden settings.', highlights: ['32', '1488', '0.65', '33', '1498', '0.67', 'HR 0.97', '0.59', '1.61', '97%', '90%', 'P<0.001', '6%', '7%', 'WHO 2018'] },


                        { label: 'Risk of Bias (RoB 2.0)', source: 'Swindells 2019 design + RoB 2.0', text: 'D1 LOW - central random allocation, stratified by site and ART status. D2 SOME concerns - open-label by necessity (different pill burdens); however hard endpoint (active TB, death) is objective. D3 LOW - >95% complete follow-up at 3 years (excellent for global multi-country trial). D4 LOW - centralized TB endpoint adjudication. D5 LOW - SAP locked.', highlights: ['LOW', 'central', 'stratified', 'open-label', 'objective', '95%', 'centralized'] }


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
    text = text[:body_start] + NEW_REAL_DATA_BODY + text[body_end+1:]
    edits.append("realData")
    FILE.write_text(text, encoding="utf-8")
    print(f"Edits: {', '.join(edits)} | Size: {FILE.stat().st_size:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
