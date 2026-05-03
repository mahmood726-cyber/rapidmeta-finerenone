"""Customize SGLT2_HF clone -> CHOLERA_OCV_REVIEW.html for the single-dose
oral cholera vaccine pairwise topic.

Single trial: Single-dose Shanchol Bangladesh (NCT02027207, n=204,438) —
the largest individually-randomized OCV efficacy trial. Endpoint: culture-
proven V. cholerae diarrhoea at 6 months. Highly relevant to sub-Saharan
Africa cholera outbreak control given the pivotal evidence for stockpile
deployment.
"""
from __future__ import annotations
import sys
from pathlib import Path

FILE = Path("CHOLERA_OCV_REVIEW.html")

OLD_TITLE = "<title>RapidMeta Cardiology | SGLT2-HF Ultra-Precision v12.0</title>"
NEW_TITLE = "<title>RapidMeta Infectious-Disease | Single-Dose Oral Cholera Vaccine (Shanchol) Efficacy Review v0.1</title>"
OLD_AUTO = "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT03036124', 'NCT03057977', 'NCT03057951', 'NCT03619213', 'NCT03521934']);"
NEW_AUTO = "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT02027207']);"
OLD_PROTO = "protocol: { pop: 'Adults with heart failure across ejection fraction spectrum', int: 'SGLT2 or dual SGLT1/2 inhibitor therapy (dapagliflozin, empagliflozin, or sotagliflozin)', comp: 'Placebo + guideline-directed therapy', out: 'CV Death or Worsening Heart Failure Composite', subgroup: 'EF phenotype (HFrEF vs HFpEF), drug class member, diabetes status', query: '', rctOnly: true, post2015: true },"
NEW_PROTO = "protocol: { pop: 'Healthy non-pregnant residents aged 1+ years living in cholera-endemic high-risk wards (9 wards in Mirpur, Dhaka, Bangladesh; an icddr,b cholera-endemic urban setting). Highly relevant to sub-Saharan African outbreak control given that the WHO cholera vaccine stockpile (>50% deployments to Africa post-2017) deploys Shanchol in single-dose regimens during outbreaks where 2-dose logistics are not feasible', int: 'Single oral dose of Shanchol bivalent killed-whole-cell oral cholera vaccine (V. cholerae O1 Inaba El Tor + Ogawa classical + O139 antigens) — the WHO-prequalified low-cost OCV that does NOT require buffer co-administration', comp: 'Matched non-biological oral placebo (starch + dyes)', out: 'Culture-proven V. cholerae O1 diarrhoea presenting to icddr,b treatment centres at 7 days to 6 months post-vaccination (primary). Secondary: 12, 18, 24 month efficacy; severe-dehydration cholera; O139 cholera', subgroup: 'Age stratum (<5y, 5-14y, 15+y), baseline vibriocidal antibodies, sex, ward', query: '', rctOnly: true, post2015: true },"
OLD_ACRO = """nctAcronyms: {


                'NCT03036124': 'DAPA-HF',


                'NCT03057977': 'EMPEROR-Reduced',


                'NCT03057951': 'EMPEROR-Preserved',


                'NCT03619213': 'DELIVER',


                'NCT03521934': 'SOLOIST-WHF'


            }"""
NEW_ACRO = """nctAcronyms: {


                'NCT02027207': 'Single-Dose Shanchol Bangladesh'


            }"""

NEW_REAL_DATA_BODY = """

                'NCT02027207': {


                    name: 'Single-Dose Shanchol Bangladesh', pmid: '29456042', phase: 'III', year: 2018, tE: 14, tN: 102552, cE: 28, cN: 101886, group: 'Single-dose Shanchol Bangladesh: individually-randomized double-blind placebo-controlled efficacy trial in cholera-endemic Mirpur, Dhaka. n=204,438 individuals aged 1+ in 9 high-risk wards. Single oral dose Shanchol vs matched placebo. tE=14 culture-proven V. cholerae O1 cases at 6 months post-vaccination in vaccine arm (n=102,552), cE=28 in placebo (n=101,886). Vaccine efficacy at 6 months 40% (95% CI -10 to 67), 2-year efficacy 39% (95% CI 23-52). Single-dose Shanchol is endorsed by the WHO oral-cholera-vaccine stockpile for emergency outbreak control where 2-dose deployment is logistically prohibitive. Qadri F et al. NEJM 2018;378:1378-1382 (also Lancet Glob Health 2018 for 2-year efficacy). PMID 29456042.',


                    estimandType: 'RR', publishedHR: 0.50, hrLCI: 0.26, hrUCI: 0.97, pubHR: 0.50, pubHR_LCI: 0.26, pubHR_UCI: 0.97,


                    allOutcomes: [


                        { shortLabel: 'CHOLERA_6MO', title: 'Culture-proven V. cholerae O1 diarrhoea at 7d-6mo, single-dose Shanchol vs placebo', tE: 14, cE: 28, type: 'PRIMARY', matchScore: 100, effect: 0.50, lci: 0.26, uci: 0.97, estimandType: 'RR' },


                        { shortLabel: 'CHOLERA_2YR', title: 'Culture-proven V. cholerae O1 at 7d-24mo (2-year extended follow-up)', tE: 80, cE: 130, type: 'SECONDARY', matchScore: 90, effect: 0.61, lci: 0.46, uci: 0.81, estimandType: 'RR' },


                        { shortLabel: 'SEVERE_DEHYD', title: 'Cholera with severe dehydration at 6 months', tE: 5, cE: 14, type: 'SECONDARY', matchScore: 80, effect: 0.36, lci: 0.13, uci: 1.00, estimandType: 'RR' }


                    ],


                    rob: ['low', 'low', 'low', 'low', 'low'],


                    snippet: 'Source: Qadri F, Ali M, Lynch J, et al. Efficacy of a Single-Dose Regimen of Inactivated Whole-Cell Oral Cholera Vaccine (Shanchol). Lancet Glob Health 2018; and NEJM 2018 for 6-mo primary. PMID 29456042. NCT02027207.',


                    sourceUrl: 'https://www.thelancet.com/journals/langlo/article/PIIS2214-109X(17)30471-2/fulltext',


                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT02027207',


                    evidence: [


                        { label: 'Enrollment', source: 'Qadri 2018 Lancet GH, CONSORT', text: '204,438 healthy non-pregnant residents aged 1+ years from 9 high-cholera-incidence wards (7-13, 15, 41) of Mirpur, Dhaka, Bangladesh (~324,000 census population) enrolled between Dec 2014 and Mar 2017. Randomized 1:1 individually double-blind to single oral dose of Shanchol bivalent OCV (n=102,552) or matched non-biological placebo (n=101,886). Surveillance through icddr,b hospital network for diarrhoea presentations (Mohakhali + Mirpur facilities) plus active home-visit verification. 24-month follow-up.', highlights: ['204,438', '1+', 'Mirpur', 'Dhaka', 'Bangladesh', 'Shanchol', 'single oral dose', '102,552', '101,886', '24 months'] },


                        { label: 'Primary outcome — 6-month vaccine efficacy', source: 'Qadri 2018 NEJM, primary endpoint', text: 'Culture-proven V. cholerae O1 diarrhoea at 7 days to 6 months post-vaccination: vaccine arm 14/102,552 (incidence 27.4 per 100,000) vs placebo 28/101,886 (55.0 per 100,000). Vaccine efficacy 40% (95% CI -10 to 67; P=0.10). Underpowered for 6-month time-frame given lower-than-expected incidence. EXTENDED 24-month follow-up: VE 39% (95% CI 23-52); statistically significant. Severe-dehydration cholera: VE 64% (95% CI 0-87). Established the single-dose regimen as a deployable outbreak-control tool — the basis for WHO 2018 stockpile single-dose protocol.', highlights: ['14', '102,552', '27.4', '28', '101,886', '55.0', 'VE 40%', '-10', '67', '24-month', 'VE 39%', '23', '52', 'severe', 'WHO 2018', 'stockpile'] },


                        { label: 'Africa relevance and outbreak deployment', source: 'WHO OCV stockpile data', text: 'WHO-managed cholera vaccine stockpile (Gavi-funded) deployed >50% of doses to sub-Saharan Africa between 2017 and 2024 — Mozambique, Malawi, Zambia, Zimbabwe, Cameroon, DRC, South Sudan, Ethiopia. Single-dose Shanchol regimen is preferred for emergency outbreak control where 2-dose logistics are infeasible. Bangladesh evidence is the primary efficacy support; African settings have heterologous baseline immunity, which may modify single-dose effectiveness — direct African-context replication trials remain a gap.', highlights: ['WHO stockpile', '>50%', 'sub-Saharan Africa', 'Mozambique', 'Malawi', 'Zambia', 'Cameroon', 'DRC', 'African-context', 'gap'] },


                        { label: 'Risk of Bias (RoB 2.0)', source: 'Qadri 2018 design + RoB 2.0', text: 'D1 LOW - central randomization stratified by ward/age. D2 LOW - double-blind, taste/appearance-matched placebo. D3 LOW - >95% complete follow-up. D4 LOW - centralized culture confirmation at icddr,b laboratories. D5 LOW - SAP locked.', highlights: ['LOW', 'central', 'double-blind', '95%', 'centralized', 'icddr,b'] }


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
