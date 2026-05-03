"""Build 2 more topic apps:
- TB_DRUG_SUSCEPTIBLE_4MO_REVIEW.html: Study 31/A5349 (NCT02410772) — 4-month rifapentine-moxifloxacin vs 6-month standard for drug-susceptible pulmonary TB. Dorman 2021 NEJM.
- MENTAL_HEALTH_FRIENDSHIP_BENCH_REVIEW.html: Friendship Bench Zimbabwe (PACTR201410000876178) — lay-health-worker problem-solving therapy for common mental disorders. Chibanda 2016 JAMA. Uses synthetic LEGACY-PACTR-FRIENDSHIP-BENCH key.
"""
from __future__ import annotations
import sys
from pathlib import Path

def replace_realdata(text, new_body):
    start = text.find("realData: {")
    body_start = text.find("{", start)
    depth = 0; i = body_start
    while i < len(text):
        c = text[i]
        if c == "{": depth += 1
        elif c == "}": depth -= 1
        if depth == 0 and i > body_start: body_end = i; break
        i += 1
    return text[:body_start] + "{" + new_body + text[body_end+1:]


# ==========================
# TOPIC 13: TB drug-susceptible 4-month (clone SGLT2_HF)
# ==========================
TB_DS_BODY = """

                'NCT02410772': {

                    name: 'Study 31 / A5349 (4-month rifapentine-moxifloxacin)', pmid: '33951360', phase: 'III', year: 2021, tE: 49, tN: 791, cE: 39, cN: 768, group: 'TBTC Study 31 / ACTG A5349: 3-arm international RCT in adolescents and adults with drug-susceptible pulmonary TB. n=2,516 across 33 sites in 13 countries (sub-Saharan African enrolment ~50%: South Africa, Kenya, Malawi, Uganda, Zimbabwe, Vietnam, Brazil, others). Investigational arm 3 (2HPZM/2HPM, n=791): 2 months rifapentine + isoniazid + pyrazinamide + moxifloxacin then 2 months rifapentine + isoniazid + moxifloxacin (17 weeks total). Control (n=768): 2HRZE/4HR (26 weeks). Primary efficacy mITT: TB-disease-free survival at 12 months — non-inferior. Unfavorable (regimen-3 vs control): 49/791 (6.2%) vs 39/768 (5.1%); absolute difference 1.0 percentage points (95% CI -1.4 to 3.4), within prespecified 6.6 pp NI margin. Drove WHO 2022 conditional recommendation for the 4-month rifapentine-moxifloxacin regimen as alternative to 6-month standard. Dorman SE et al. NEJM 2021;384:1705-1718. PMID 33951360. DOI 10.1056/NEJMoa2033400.',

                    estimandType: 'RR', publishedHR: 1.22, hrLCI: 0.81, hrUCI: 1.84, pubHR: 1.22,

                    allOutcomes: [
                        { shortLabel: 'UNFAV', title: 'Unfavorable outcome at 12 months (mITT, regimen 3 vs control)', tE: 49, cE: 39, type: 'PRIMARY', matchScore: 100, effect: 1.22, lci: 0.81, uci: 1.84, estimandType: 'RR' },

                        { shortLabel: 'GR3_AE', title: 'Grade 3+ adverse events during treatment', tE: 152, cE: 119, type: 'SAFETY', matchScore: 80, effect: 1.24, lci: 0.99, uci: 1.55, estimandType: 'RR' }
                    ],

                    rob: ['low', 'some', 'low', 'low', 'low'],

                    snippet: 'Source: Dorman SE, Nahid P, Kurbatova EV, et al. Four-Month Rifapentine Regimens with or without Moxifloxacin for Tuberculosis. NEJM 2021;384:1705-1718. PMID 33951360.',

                    sourceUrl: 'https://www.nejm.org/doi/full/10.1056/NEJMoa2033400',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT02410772',

                    evidence: [
                        { label: 'Enrollment', source: 'Dorman 2021 NEJM, CONSORT', text: '2,516 participants aged 12+ with drug-susceptible pulmonary TB enrolled at 33 international sites between Jan 2016 and Jul 2018. Predominantly sub-Saharan African enrolment (South Africa, Kenya, Malawi, Uganda, Zimbabwe ~50% of total) plus US, Brazil, Haiti, India, Peru, Vietnam, Hong Kong, Thailand. Randomized 1:1:1 open-label to control 6-mo regimen (2HRZE/4HR), regimen 2 (2HPZE/2HP, 17 wk rifapentine substitution), or regimen 3 (2HPZM/2HPM, 17 wk rifapentine + moxifloxacin). 18% HIV-positive; 84% cavitary disease at baseline.', highlights: ['2,516', 'sub-Saharan Africa', 'South Africa', 'Kenya', 'Malawi', 'Uganda', 'Zimbabwe', '17 weeks', '6 months', '18% HIV', 'rifapentine'] },
                        { label: 'Primary outcome — 12-month TB-disease-free survival', source: 'Dorman 2021 NEJM, primary endpoint', text: 'mITT unfavorable outcome at 12 months: regimen 3 (rifapentine + moxifloxacin, 17 wk) 49/791 (6.2%) vs control 39/768 (5.1%) — absolute difference 1.0 pp (95% CI -1.4 to 3.4); non-inferiority margin 6.6 pp met. Regimen 2 (rifapentine alone, 17 wk) did NOT meet non-inferiority (10.5% unfavorable; difference 5.4 pp, 95% CI 2.6-8.2). Only the rifapentine-MOXIFLOXACIN combination achieved 4-month non-inferiority — drove WHO 2022 conditional recommendation as alternative to standard 6-month therapy.', highlights: ['49', '791', '6.2%', '39', '768', '5.1%', '1.0', '-1.4', '3.4', '6.6 pp', 'NI met', 'WHO 2022'] },
                        { label: 'Risk of Bias (RoB 2.0)', source: 'Dorman 2021 design + RoB 2.0', text: 'D1 LOW (central random allocation, 1:1:1). D2 SOME (open-label by design — different durations and pill burdens). D3 LOW (>=95% complete follow-up). D4 LOW (independent endpoint adjudication, central mycobacterial testing). D5 LOW (SAP locked).', highlights: ['LOW', 'central', '1:1:1', 'open-label', '95%', 'central'] }
                    ]
                }
            }"""

# ==========================
# TOPIC 14: Friendship Bench Mental Health (clone SGLT2_HF)
# ==========================
MENTAL_BODY = """

                'LEGACY-PACTR-FRIENDSHIP-BENCH': {

                    name: 'Friendship Bench Zimbabwe', pmid: '28027368', phase: 'NA', year: 2016, tE: 39, tN: 286, cE: 143, cN: 287, group: 'Friendship Bench cluster-RCT (Chibanda 2016 JAMA): 24 primary-care clinics in Harare, Zimbabwe randomized 1:1 to lay-health-worker problem-solving therapy ("Friendship Bench" 6-session intervention with optional peer-support extension) vs enhanced standard care. n=573 adults screening positive for common mental disorders on the locally-validated Shona Symptom Questionnaire (SSQ-14). Median age 33; 86% women; 42% HIV-positive (high HIV-mental-health comorbidity). Primary endpoint: continuous SSQ-14 score at 6 months. Adjusted mean difference -4.86 (95% CI -5.63 to -4.10; P<0.001) favoring intervention; ARR 0.21 (95% CI 0.15-0.29) for SSQ-14-positive. Secondary depression-symptoms endpoint (PHQ-9 cutpoint 11): 13.7% intervention vs 49.9% control (ARR 0.28). Established the cost-effectiveness of task-shifting mental health to lay health workers in low-resource African primary care. Subsequently scaled across multiple African countries (Kenya, Malawi, more). Trial registered with PACTR (Pan African Clinical Trials Registry) as PACTR201410000876178 — NOT registered on ClinicalTrials.gov; uses synthetic LEGACY-PACTR-FRIENDSHIP-BENCH key in this dashboard.',

                    estimandType: 'RR', publishedHR: 0.21, hrLCI: 0.15, hrUCI: 0.29, pubHR: 0.21,

                    allOutcomes: [
                        { shortLabel: 'SSQ_POS', title: 'Common mental disorder (SSQ-14 >=9) at 6 months, intervention vs control', tE: 39, cE: 143, type: 'PRIMARY', matchScore: 100, effect: 0.21, lci: 0.15, uci: 0.29, estimandType: 'RR' },

                        { shortLabel: 'PHQ9_POS', title: 'Depression (PHQ-9 >=11) at 6 months', tE: 39, cE: 143, type: 'SECONDARY', matchScore: 90, effect: 0.28, lci: 0.22, uci: 0.34, estimandType: 'RR' },

                        { shortLabel: 'SSQ_MD', title: 'Adjusted mean difference SSQ-14 score (continuous, 0-14)', tE: 3.81, cE: 8.90, type: 'SECONDARY', matchScore: 80, effect: -4.86, lci: -5.63, uci: -4.10, estimandType: 'MD' }
                    ],

                    rob: ['low', 'some', 'low', 'low', 'low'],

                    snippet: 'Source: Chibanda D, Weiss HA, Verhey R, et al. Effect of a Primary Care-Based Psychological Intervention on Symptoms of Common Mental Disorders in Zimbabwe (Friendship Bench): A Randomized Clinical Trial. JAMA 2016;316:2618-2626. PMID 28027368. DOI 10.1001/jama.2016.19102. PACTR201410000876178.',

                    sourceUrl: 'https://jamanetwork.com/journals/jama/fullarticle/2594719',

                    ctgovUrl: null,

                    evidence: [
                        { label: 'Enrollment', source: 'Chibanda 2016 JAMA, CONSORT', text: '24 primary-care clinics in Harare, Zimbabwe were randomized 1:1 (cluster) to Friendship Bench intervention (12 clinics) or enhanced usual care (12 clinics) between Sep 2014 and May 2015. Within clinics, 573 clinic attendees aged 18+ screening positive on the locally-validated Shona Symptom Questionnaire (SSQ-14, score >=9) were enrolled (286 intervention, 287 control). Median age 33 (IQR 27-41); 86.4% women; 41.7% HIV-positive (reflecting the high HIV-mental-health comorbidity in southern African primary care). 90.9% completed 6-month follow-up.', highlights: ['24 clinics', 'Harare', 'Zimbabwe', '573', '286', '287', '86.4%', 'women', '41.7%', 'HIV-positive', '90.9%'] },
                        { label: 'Primary outcome — SSQ-14 at 6 months', source: 'Chibanda 2016 JAMA, primary endpoint', text: 'SSQ-14 score at 6 months (continuous, 0-14, higher worse): intervention 3.81 (95% CI 3.28-4.34) vs control 8.90 (95% CI 8.33-9.47); adjusted mean difference -4.86 (95% CI -5.63 to -4.10; P<0.001). Common mental disorder (SSQ-14 >=9) at 6 months: intervention 39/286 (13.7%) vs control 143/287 (49.8%); adjusted RR 0.21 (95% CI 0.15-0.29). Depression (PHQ-9 >=11): 13.7% vs 49.9%; ARR 0.28 (0.22-0.34). Effect sizes are large for a behavioural-intervention primary-care trial. Lay-health-worker delivery (median 4 sessions completed) demonstrated feasibility for scale.', highlights: ['3.81', '8.90', '-4.86', '-5.63', '-4.10', 'P<0.001', '13.7%', '49.8%', 'RR 0.21', '0.15', '0.29'] },
                        { label: 'Risk of Bias (RoB 2.0)', source: 'Chibanda 2016 design + RoB 2.0', text: 'D1 LOW (cluster randomization with constrained allocation). D2 SOME (unblinded by design — psychotherapy intervention visibly different). D3 LOW (90.9% retention at 6 months, excellent for a primary-care psychiatric trial in Africa). D4 LOW (SSQ-14 self-administered with structured scoring; PHQ-9 standardized). D5 LOW.', highlights: ['LOW', 'cluster', 'unblinded', '90.9%', 'standardized'] }
                    ]
                }
            }"""


def build_tb_ds():
    FILE = Path("TB_DRUG_SUSCEPTIBLE_4MO_REVIEW.html")
    text = FILE.read_text(encoding="utf-8")
    text = text.replace(
        "<title>RapidMeta Cardiology | SGLT2-HF Ultra-Precision v12.0</title>",
        "<title>RapidMeta Infectious-Disease | 4-Month Rifapentine-Moxifloxacin for Drug-Susceptible TB v0.1 (Study 31)</title>")
    text = text.replace(
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT03036124', 'NCT03057977', 'NCT03057951', 'NCT03619213', 'NCT03521934']);",
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT02410772']);")
    text = text.replace(
        "protocol: { pop: 'Adults with heart failure across ejection fraction spectrum', int: 'SGLT2 or dual SGLT1/2 inhibitor therapy (dapagliflozin, empagliflozin, or sotagliflozin)', comp: 'Placebo + guideline-directed therapy', out: 'CV Death or Worsening Heart Failure Composite', subgroup: 'EF phenotype (HFrEF vs HFpEF), drug class member, diabetes status', query: '', rctOnly: true, post2015: true },",
        "protocol: { pop: 'Adolescents and adults aged 12+ with newly-diagnosed previously-untreated drug-susceptible pulmonary tuberculosis. Sub-Saharan African enrolment ~50% (S Africa, Kenya, Malawi, Uganda, Zimbabwe; plus US, Brazil, India, Peru, Vietnam, Thailand)', int: 'Investigational regimen 3: 2 months rifapentine + isoniazid + pyrazinamide + moxifloxacin then 2 months rifapentine + isoniazid + moxifloxacin (17 weeks total)', comp: 'Standard 6-month regimen 2HRZE/4HR (8 weeks rifampin/isoniazid/pyrazinamide/ethambutol then 18 weeks rifampin/isoniazid)', out: 'TB-disease-free survival at 12 months (mITT and assessable populations); proportion with grade 3+ adverse events during treatment', subgroup: 'HIV co-infection, baseline cavitary disease, sex, country/TB burden setting', query: '', rctOnly: true, post2015: true },")
    text = text.replace(
        "{ 'DAPA-HF': 'Dapagliflozin', 'DELIVER': 'Dapagliflozin', 'EMPEROR-Reduced': 'Empagliflozin', 'EMPEROR-Preserved': 'Empagliflozin', 'SOLOIST-WHF': 'Sotagliflozin' }",
        "{ 'Study 31 / A5349 (4-month rifapentine-moxifloxacin)': '4-month rifapentine-moxifloxacin' }")
    text = text.replace("'NCT03036124': 'DAPA-HF',\n\n\n                'NCT03057977': 'EMPEROR-Reduced',\n\n\n                'NCT03057951': 'EMPEROR-Preserved',\n\n\n                'NCT03619213': 'DELIVER',\n\n\n                'NCT03521934': 'SOLOIST-WHF'", "'NCT02410772': 'Study 31 / A5349 (4-month rifapentine-moxifloxacin)'")
    text = replace_realdata(text, TB_DS_BODY)
    # Quick scaffold cleanup
    text = text.replace("SGLT2-HF v1.0", "TB-DS 4mo v0.1")
    text = text.replace("SGLT2 Inhibitors for Heart Failure Outcomes: A Living Systematic Review and Meta-Analysis of Randomized Controlled Trials",
                        "Four-Month Rifapentine-Moxifloxacin for Drug-Susceptible Pulmonary TB: Single-Trial Pairwise Review (Study 31, post-2016)")
    text = text.replace("SGLT2 Inhibitors in Heart Failure", "4-Month Rifapentine-Moxifloxacin for DS-TB")
    text = text.replace('value="Adults with heart failure"', 'value="Adolescents/adults with drug-susceptible pulmonary TB"')
    text = text.replace("value=\"Heart Failure\"", "value=\"TB\"")
    FILE.write_text(text, encoding="utf-8")
    print(f"  TB-DS: {FILE.stat().st_size:,}")


def build_mental():
    FILE = Path("MENTAL_HEALTH_FRIENDSHIP_BENCH_REVIEW.html")
    text = FILE.read_text(encoding="utf-8")
    text = text.replace(
        "<title>RapidMeta Cardiology | SGLT2-HF Ultra-Precision v12.0</title>",
        "<title>RapidMeta Mental-Health | Friendship Bench Lay-Health-Worker Therapy for Common Mental Disorders v0.1 (Zimbabwe, post-2014)</title>")
    text = text.replace(
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT03036124', 'NCT03057977', 'NCT03057951', 'NCT03619213', 'NCT03521934']);",
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['LEGACY-PACTR-FRIENDSHIP-BENCH']);")
    text = text.replace(
        "protocol: { pop: 'Adults with heart failure across ejection fraction spectrum', int: 'SGLT2 or dual SGLT1/2 inhibitor therapy (dapagliflozin, empagliflozin, or sotagliflozin)', comp: 'Placebo + guideline-directed therapy', out: 'CV Death or Worsening Heart Failure Composite', subgroup: 'EF phenotype (HFrEF vs HFpEF), drug class member, diabetes status', query: '', rctOnly: true, post2015: true },",
        "protocol: { pop: 'Adults aged 18+ attending Harare primary-care clinics, screening positive for common mental disorders on the locally-validated Shona Symptom Questionnaire (SSQ-14 >=9). 86% women; 42% HIV-positive — reflects high HIV-mental-health comorbidity in southern Africa', int: 'Friendship Bench 6-session lay-health-worker problem-solving therapy with optional 6-session peer-support extension; delivered on a wooden bench at the clinic by trained \\u2018grandmother\\u2019 community workers', comp: 'Enhanced usual care (psychoeducation + clinic referral pathway)', out: 'SSQ-14 continuous score at 6 months (primary); proportion with PHQ-9 >=11 depression at 6 months (secondary)', subgroup: 'HIV status, baseline severity, age, prior mental-health contact', query: '', rctOnly: true, post2015: true },")
    text = text.replace(
        "{ 'DAPA-HF': 'Dapagliflozin', 'DELIVER': 'Dapagliflozin', 'EMPEROR-Reduced': 'Empagliflozin', 'EMPEROR-Preserved': 'Empagliflozin', 'SOLOIST-WHF': 'Sotagliflozin' }",
        "{ 'Friendship Bench Zimbabwe': 'Friendship Bench (lay-HW problem-solving therapy)' }")
    text = text.replace("'NCT03036124': 'DAPA-HF',\n\n\n                'NCT03057977': 'EMPEROR-Reduced',\n\n\n                'NCT03057951': 'EMPEROR-Preserved',\n\n\n                'NCT03619213': 'DELIVER',\n\n\n                'NCT03521934': 'SOLOIST-WHF'", "'LEGACY-PACTR-FRIENDSHIP-BENCH': 'Friendship Bench Zimbabwe'")
    text = replace_realdata(text, MENTAL_BODY)
    text = text.replace("SGLT2-HF v1.0", "Mental Health v0.1")
    text = text.replace("SGLT2 Inhibitors for Heart Failure Outcomes: A Living Systematic Review and Meta-Analysis of Randomized Controlled Trials",
                        "Friendship Bench Lay-Health-Worker Problem-Solving Therapy for Common Mental Disorders in Sub-Saharan African Primary Care: Single-Trial Review (Zimbabwe, post-2014)")
    text = text.replace("SGLT2 Inhibitors in Heart Failure", "Friendship Bench Mental-Health Intervention")
    text = text.replace('value="Adults with heart failure"', 'value="Adults with common mental disorders in primary care, sub-Saharan Africa"')
    text = text.replace("value=\"Heart Failure\"", "value=\"Mental Health\"")
    FILE.write_text(text, encoding="utf-8")
    print(f"  Mental: {FILE.stat().st_size:,}")


if __name__ == "__main__":
    build_tb_ds()
    build_mental()
