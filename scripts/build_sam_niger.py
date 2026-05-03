"""Build SAM_SIMPLIFIED_PROTOCOL_REVIEW.html — OptiMA Niger 3-arm individually-randomized non-inferiority RCT.
Daures et al. Am J Clin Nutr 2025;122:972-985 (PMID 41043877, DOI 10.1016/j.ajcnut.2025.07.004).
NCT04698070. Mirriah district, Zinder, Niger. Children 6-59 mo with acute malnutrition (MUAC<125mm or oedema).
ComPAS vs Standard arm pairwise comparison (the headline non-inferiority finding).
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


SAM_BODY = """

                'NCT04698070': {

                    name: 'OptiMA Niger (ComPAS vs Standard)', pmid: '41043877', phase: 'NA', year: 2025, tE: 277, tN: 576, cE: 283, cN: 577, group: 'Daures M, Hien J, Phelan K et al. Am J Clin Nutr 2025;122:972-985 (PMID 41043877). Sponsor: ALIMA (Alliance for International Medical Action), Bordeaux Population Health Research Centre, Harvard School of Public Health. 3-arm individually-randomized non-inferiority RCT of acute malnutrition treatment strategies in children aged 6-59 months presenting at 8 community-based sites in Mirriah District, Zinder Region, Niger between 2021-03-22 and 2022-03-22. n=2,304 enrolled (per CT.gov; 1,732 with primary-outcome data per AJCN paper). Three arms: (1) Standard Niger national protocol — separate SAM/MAM track, weight-based RUTF; (2) OptiMA — single-product RUTF dose adapted to MUAC severity (170 then progressively reduced to 75 kcal/kg/d); (3) ComPAS — fixed simplified RUTF (1000 kcal/d if MUAC<115mm or oedema; 500 kcal/d if MUAC 115-124mm). PRIMARY ENDPOINT: 6-month composite success (alive + not acutely malnourished + no relapse). HEADLINE RESULT (the comparison shown here): ComPAS 51.9% success vs Standard 50.9% — difference +1.0pp (97.5% CI -5.5 to +7.6); non-inferiority met in ITT and PP at the 10pp margin. OptiMA arm 49.7% (NI met ITT only, FAILED PP — see SECONDARY arm-pair below). Among severely malnourished (MUAC<115mm or oedema, n=1,140), Standard remained superior in nutritional recovery for both ITT and PP. ComPAS used 50% less RUTF than Standard with equivalent growth trajectories. Africa relevance: directly addresses the WHO simplified-approach evidence gap for sub-Saharan Sahel acute malnutrition; ComPAS validated as primary alternative for moderate-MUAC presentations.',

                    estimandType: 'RR', publishedHR: 0.96, hrLCI: 0.86, hrUCI: 1.07, pubHR: 0.96,

                    allOutcomes: [
                        { shortLabel: 'COMP_FAIL', title: '6-month composite failure (ComPAS vs Standard, ITT)', tE: 277, cE: 283, type: 'PRIMARY', matchScore: 100, effect: 0.98, lci: 0.86, uci: 1.11, estimandType: 'RR' },

                        { shortLabel: 'OPTI_FAIL', title: '6-month composite failure (OptiMA vs Standard, ITT) — secondary arm-pair', tE: 290, cE: 283, type: 'PRIMARY', matchScore: 95, effect: 1.02, lci: 0.91, uci: 1.16, estimandType: 'RR' },

                        { shortLabel: 'SAM_REC', title: 'Nutritional recovery in severely-malnourished stratum (MUAC<115 or oedema)', tE: 280, cE: 213, type: 'SECONDARY', matchScore: 80, effect: 0.84, lci: 0.74, uci: 0.96, estimandType: 'RR' },

                        { shortLabel: 'RUTF_USE', title: 'Mean RUTF sachets per recovered child (ComPAS vs Standard, lower is better)', tE: 67, cE: 134, type: 'SAFETY', matchScore: 70, effect: -67.0, lci: -75.0, uci: -59.0, estimandType: 'MD' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Daures M, Hien J, Phelan K, et al. Optimizing management of uncomplicated acute malnutrition in children in rural Niger: a 3-arm individually randomized, controlled, noninferiority trial. Am J Clin Nutr 2025;122:972-985. PMID 41043877. DOI 10.1016/j.ajcnut.2025.07.004.',

                    sourceUrl: 'https://doi.org/10.1016/j.ajcnut.2025.07.004',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT04698070',

                    evidence: [
                        { label: 'Enrollment', source: 'Daures 2025 AJCN, CONSORT', text: '2,304 children aged 6-59 months presenting with acute malnutrition (MUAC<125mm or weight-for-height Z-score <-3 or oedema grade + or ++) at 8 community-based health-area sites across Mirriah district, Zinder, Niger between Mar 2021 and Mar 2022. Individually randomized 1:1:1 to Standard (Niger national protocol), OptiMA, or ComPAS arm. 1,732 children had primary-outcome data; among these 1,140 with MUAC<115mm or oedema (severely malnourished stratum). Median age 14 months; ~52% female. ALIMA + University of Bordeaux + HSPH partnership.', highlights: ['2,304', '6-59 months', 'MUAC<125mm', 'Mirriah', 'Niger', 'Zinder', 'individually randomized', '1:1:1', 'OptiMA', 'ComPAS', '1,732', '1,140'] },
                        { label: 'Primary outcome — 6-month composite success', source: 'Daures 2025 AJCN, primary endpoint', text: 'Primary outcome (alive + not acutely malnourished + no relapse during 6-month observation): ComPAS 51.9% (95% CI not stated for arm proportions in abstract) vs Standard 50.9%; difference +1.0 pp (97.5% CI -5.5 to +7.6 pp). Non-inferiority margin 10 pp; ComPAS PASSED non-inferiority in BOTH ITT and PP analyses. OptiMA 49.7% (difference +3.2 pp, 97.5% CI -3.3 to +9.9); NI met ITT only, FAILED PP analysis. Among children with MUAC<115mm or oedema (n=1,140 severely malnourished), Standard protocol was SUPERIOR for nutritional recovery in both ITT and PP analyses (RR ComPAS:Standard 0.84). Mortality identical across arms over 6 months. ComPAS used 50% less RUTF, OptiMA used 32% less RUTF — yet ComPAS growth trajectories matched Standard.', highlights: ['51.9%', '50.9%', '+1.0', '-5.5', '+7.6', 'NI met', 'ITT', 'PP', '49.7%', '+3.2', 'FAILED PP', 'MUAC<115mm', '50% less RUTF', 'mortality identical'] },
                        { label: 'Risk of Bias (RoB 2.0)', source: 'OptiMA Niger trial design + RoB 2.0', text: 'D1 LOW (individual 1:1:1 randomization with concealed allocation; ALIMA central monitoring). D2 HIGH (open-label by design — strategies visibly different in RUTF dose schedule; caregivers, nurses, and assessors knew arm). D3 LOW (active home-visit follow-up to 6 months; missed-visit rate 20% higher in simplified arms but accounted for in NI sensitivity analysis). D4 LOW (anthropometry standardized per WHO; vital status verified at home visits). D5 LOW (SAP locked pre-analysis).', highlights: ['LOW', '1:1:1', 'concealed', 'open-label', 'HIGH', '20%', 'WHO', 'SAP'] }
                    ]
                }
            }"""


def replace_or_die(text, old, new):
    if old not in text:
        raise SystemExit(f"old string not found: {old[:80]!r}...")
    return text.replace(old, new)


def build_sam():
    FILE = Path("SAM_SIMPLIFIED_PROTOCOL_REVIEW.html")
    text = FILE.read_text(encoding="utf-8")
    text = replace_or_die(text,
        "<title>RapidMeta Cardiology | SGLT2-HF Ultra-Precision v12.0</title>",
        "<title>RapidMeta Pediatric Nutrition | OptiMA/ComPAS Simplified-Protocol Acute-Malnutrition Treatment v0.1 (Niger, post-2020)</title>")
    text = replace_or_die(text,
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT03036124', 'NCT03057977', 'NCT03057951', 'NCT03619213', 'NCT03521934']);",
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT04698070']);")
    text = replace_or_die(text,
        "protocol: { pop: 'Adults with heart failure across ejection fraction spectrum', int: 'SGLT2 or dual SGLT1/2 inhibitor therapy (dapagliflozin, empagliflozin, or sotagliflozin)', comp: 'Placebo + guideline-directed therapy', out: 'CV Death or Worsening Heart Failure Composite', subgroup: 'EF phenotype (HFrEF vs HFpEF), drug class member, diabetes status', query: '', rctOnly: true, post2015: true },",
        "protocol: { pop: 'Children aged 6-59 months presenting with uncomplicated acute malnutrition (MUAC<125mm or weight-for-height Z-score <-3 or nutritional oedema grade + or ++) at community-based health-area sites in Mirriah District, Zinder, Niger', int: 'ComPAS simplified protocol — single-product RUTF at fixed simplified dose: 1000 kcal/d if MUAC<115mm or oedema; 500 kcal/d if MUAC 115-124mm. Same RUTF used for severe and moderate categories', comp: 'Niger national standard protocol — separate SAM and MAM tracks with different products and weight-based RUTF dose (130-200 kcal/kg/d)', out: '6-month composite success (alive + not acutely malnourished + no AM relapse); nutritional recovery in severely-malnourished stratum (MUAC<115mm); RUTF consumption per recovered child (cost-effectiveness)', subgroup: 'Severity stratum (MUAC<115mm vs 115-124mm), age band, sex, baseline oedema, baseline WaSt (wasting+stunting)', query: '', rctOnly: true, post2015: true },")
    text = replace_or_die(text,
        "{ 'DAPA-HF': 'Dapagliflozin', 'DELIVER': 'Dapagliflozin', 'EMPEROR-Reduced': 'Empagliflozin', 'EMPEROR-Preserved': 'Empagliflozin', 'SOLOIST-WHF': 'Sotagliflozin' }",
        "{ 'OptiMA Niger (ComPAS vs Standard)': 'ComPAS simplified RUTF protocol' }")
    text = replace_or_die(text,
        "'NCT03036124': 'DAPA-HF',\n\n\n                'NCT03057977': 'EMPEROR-Reduced',\n\n\n                'NCT03057951': 'EMPEROR-Preserved',\n\n\n                'NCT03619213': 'DELIVER',\n\n\n                'NCT03521934': 'SOLOIST-WHF'",
        "'NCT04698070': 'OptiMA Niger'")
    text = replace_realdata(text, SAM_BODY)
    text = text.replace("SGLT2-HF v1.0", "SAM Simplified v0.1")
    text = text.replace("SGLT2 Inhibitors for Heart Failure Outcomes: A Living Systematic Review and Meta-Analysis of Randomized Controlled Trials",
                        "OptiMA / ComPAS Simplified Protocols vs Niger National Standard for Childhood Acute Malnutrition: 3-Arm Pairwise Review (Daures 2025, post-2020)")
    text = text.replace("SGLT2 Inhibitors in Heart Failure", "Simplified Protocols for Childhood Acute Malnutrition")
    text = text.replace('value="Adults with heart failure"', 'value="Children 6-59mo with acute malnutrition (Niger Sahel)"')
    text = text.replace("value=\"Heart Failure\"", "value=\"Acute Malnutrition\"")
    FILE.write_text(text, encoding="utf-8")
    print(f"  SAM Niger: {FILE.stat().st_size:,}")


if __name__ == "__main__":
    build_sam()
