"""Build 2 more topic apps:
- HEPATITIS_B_TAF_TDF_REVIEW.html: TAF vs TDF pooled (GS-US-320-0108 NCT01940341 HBeAg-, GS-US-320-0110 NCT01940471 HBeAg+).
  Buti 2016 + Chan 2016 Lancet Gastroenterol Hepatol. Africa burden 6.1% prevalence (highest globally).
- EBOLA_VACCINE_REVIEW.html: rVSVΔG-ZEBOV STRIVE Sierra Leone (NCT02378753, n=8651) +
  Henao-Restrepo 2017 Guinea ring (PACTR201503001057193, synthetic LEGACY-PACTR-EBOLA-CI-RING key).
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


# ==========================
# TOPIC 15: Hepatitis B TAF vs TDF (pooled 2 trials)
# ==========================
HBV_BODY = """

                'NCT01940341': {

                    name: 'GS-US-320-0108 (TAF vs TDF, HBeAg-negative)', pmid: '27916343', phase: 'III', year: 2016, tE: 268, tN: 285, cE: 130, cN: 140, group: 'Buti M et al. Lancet Gastroenterology and Hepatology 2016;1:196-206. Phase 3 multicentre randomized double-blind active-controlled non-inferiority trial. Adults aged 18+ with HBeAg-negative chronic hepatitis B (HBV DNA >=20,000 IU/mL, ALT >ULN). Randomized 2:1 to TAF 25mg QD (n=285) vs TDF 300mg QD (n=140). Primary endpoint: HBV DNA <29 IU/mL at Week 48 (FDA snapshot). Result: TAF 268/285 (94.0%) vs TDF 130/140 (92.9%); difference 1.1pp (95% CI -3.5 to 5.7), non-inferior at -10pp margin. Renal/bone safety advantages: smaller declines in eGFR-CG and hip/spine BMD with TAF. Drove EMA/FDA TAF approval Nov 2016. Africa relevance: HBV prevalence 6.1% across sub-Saharan Africa (highest WHO region) — Buti+Chan trials are the pivotal evidence supporting WHO 2024 guideline recommendation for TAF as preferred NA in low-bone-mineral-density and renal-impairment populations.',

                    estimandType: 'RR', publishedHR: 1.01, hrLCI: 0.96, hrUCI: 1.07, pubHR: 1.01,

                    allOutcomes: [
                        { shortLabel: 'HBV_VR', title: 'HBV DNA <29 IU/mL at Week 48 (FDA snapshot)', tE: 268, cE: 130, type: 'PRIMARY', matchScore: 100, effect: 1.01, lci: 0.96, uci: 1.07, estimandType: 'RR' },

                        { shortLabel: 'ALT_NORM', title: 'ALT normalization at Week 48 (AASLD criteria)', tE: 232, cE: 102, type: 'SECONDARY', matchScore: 90, effect: 1.12, lci: 1.01, uci: 1.24, estimandType: 'RR' },

                        { shortLabel: 'EGFR_CHG', title: 'Mean change in eGFR-CG at Week 48 (mL/min)', tE: -1.8, cE: -4.8, type: 'SAFETY', matchScore: 80, effect: 3.0, lci: 1.0, uci: 5.0, estimandType: 'MD' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Buti M, Gane E, Seto WK, et al. Tenofovir alafenamide versus tenofovir disoproxil fumarate for the treatment of patients with HBeAg-negative chronic hepatitis B virus infection: a randomised, double-blind, phase 3, non-inferiority trial. Lancet Gastroenterol Hepatol 2016;1:196-206. PMID 27916343.',

                    sourceUrl: 'https://www.thelancet.com/journals/langas/article/PIIS2468-1253(16)30107-8/abstract',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT01940341'
                },

                'NCT01940471': {

                    name: 'GS-US-320-0110 (TAF vs TDF, HBeAg-positive)', pmid: '27989565', phase: 'III', year: 2016, tE: 371, tN: 581, cE: 195, cN: 292, group: 'Chan HLY et al. Lancet Gastroenterology and Hepatology 2016;1:185-195 (and Agarwal 2018 J Hepatol 2-year follow-up). Phase 3 multicentre randomized double-blind active-controlled non-inferiority trial. Adults aged 18+ with HBeAg-positive chronic hepatitis B (HBV DNA >=20,000 IU/mL, ALT >ULN). Randomized 2:1 to TAF 25mg QD (n=581) vs TDF 300mg QD (n=292). Primary endpoint: HBV DNA <29 IU/mL at Week 48. Result: TAF 371/581 (63.9%) vs TDF 195/292 (66.8%); difference -2.9pp (95% CI -9.0 to 3.2), non-inferior at -10pp margin. Renal/bone safety advantages preserved. Buti+Chan together = 1,298-patient pivotal pooled evidence base. Africa relevance: HBeAg-positive disease is more common in younger sub-Saharan African populations infected vertically; TAF preferred for bone/kidney-spared long-term suppression in adolescents and pregnant women.',

                    estimandType: 'RR', publishedHR: 0.96, hrLCI: 0.87, hrUCI: 1.05, pubHR: 0.96,

                    allOutcomes: [
                        { shortLabel: 'HBV_VR', title: 'HBV DNA <29 IU/mL at Week 48 (FDA snapshot)', tE: 371, cE: 195, type: 'PRIMARY', matchScore: 100, effect: 0.96, lci: 0.87, uci: 1.05, estimandType: 'RR' },

                        { shortLabel: 'HBEAG_LOSS', title: 'HBeAg loss at Week 48', tE: 81, cE: 35, type: 'SECONDARY', matchScore: 90, effect: 1.16, lci: 0.81, uci: 1.66, estimandType: 'RR' },

                        { shortLabel: 'EGFR_CHG', title: 'Mean change in eGFR-CG at Week 48 (mL/min)', tE: -0.6, cE: -5.4, type: 'SAFETY', matchScore: 80, effect: 4.8, lci: 3.4, uci: 6.2, estimandType: 'MD' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Chan HLY, Fung S, Seto WK, et al. Tenofovir alafenamide versus tenofovir disoproxil fumarate for the treatment of HBeAg-positive chronic hepatitis B virus infection: a randomised, double-blind, phase 3, non-inferiority trial. Lancet Gastroenterol Hepatol 2016;1:185-195. PMID 27989565.',

                    sourceUrl: 'https://www.thelancet.com/journals/langas/article/PIIS2468-1253(16)30024-3/abstract',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT01940471'
                }
            }"""


# ==========================
# TOPIC 16: Ebola Vaccine rVSV-ZEBOV (STRIVE + Guinea Ring)
# ==========================
EBOLA_BODY = """

                'NCT02378753': {

                    name: 'STRIVE Sierra Leone (rVSV\\u0394G-ZEBOV)', pmid: '29929129', phase: 'II/III', year: 2018, tE: 0, tN: 4341, cE: 0, cN: 4310, group: 'Widdowson MA, Schrag SJ, Carter RJ, et al. Implementing an Ebola Vaccine Study in Sierra Leone. CID 2018;67(Suppl 1):S98-S106 (and Samai 2018, Carter 2018 sub-papers). STRIVE = Sierra Leone Trial to Introduce a Vaccine against Ebola. CDC + University of Sierra Leone + MoH-Sanitation + eHealth Africa. Open-label individually-randomized phase 2/3 trial in healthcare workers and frontline workers (Ebola care, holding/treatment, surveillance, ambulance, burial, swab teams) at high occupational Ebola exposure risk during the 2014-2016 West African outbreak. n=8,651 enrolled Apr 2015 - Aug 2015 across 5 districts (Western Area Urban/Rural, Bombali, Port Loko, Tonkolili). Randomized 1:1 to immediate (within 7 days, n=4,341) vs deferred (18-24 weeks later, n=4,310) single-dose intramuscular rVSV\\u0394G-ZEBOV (Merck V920, BPSC-1001). PRIMARY EFFICACY ENDPOINT: laboratory-confirmed Ebola during randomized 18-24 week period. RESULT: 0/4,341 cases in immediate vs 0/4,310 in deferred — no efficacy estimate possible because the West African outbreak waned during the trial (no community transmission by trial midpoint). Safety endpoint: SAEs over 6 months not different between arms. Drove WHO prequalification of Ervebo (rVSV-ZEBOV) Nov 2019; first FDA-approved Ebola vaccine Dec 2019. Africa relevance: this trial is the SIERRA LEONE arm of the global rVSV-ZEBOV evidence base — the WHO/Médecins Sans Frontières Guinea ring trial (Henao-Restrepo 2017) provides the efficacy estimate (100% protection within 10 days post-vaccination); STRIVE provides healthcare-worker safety/feasibility evidence in the most affected country.',

                    estimandType: 'RR', publishedHR: 1.0, hrLCI: 0.0, hrUCI: 0.0, pubHR: 1.0,

                    allOutcomes: [
                        { shortLabel: 'EBV_LAB', title: 'Laboratory-confirmed Ebola at >21d post-vaccination (immediate vs deferred)', tE: 0, cE: 0, type: 'PRIMARY', matchScore: 100, effect: 1.0, lci: 0.0, uci: 0.0, estimandType: 'RR' },

                        { shortLabel: 'SAE_6M', title: 'Serious adverse event at 6 months post-vaccination', tE: 161, cE: 154, type: 'SAFETY', matchScore: 80, effect: 1.04, lci: 0.84, uci: 1.29, estimandType: 'RR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Widdowson MA, Schrag SJ, Carter RJ, et al. Implementing an Ebola Vaccine Study in Sierra Leone. Clin Infect Dis 2018;67(Suppl 1):S98-S106. PMID 29929129. DOI 10.1093/cid/ciy243.',

                    sourceUrl: 'https://academic.oup.com/cid/article/67/suppl_1/S98/5025887',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT02378753',

                    evidence: [
                        { label: 'Enrollment', source: 'Widdowson 2018 CID, CONSORT', text: '8,651 healthcare workers and frontline workers (Ebola care/holding/treatment, surveillance teams, ambulance teams, burial workers, swab teams) at high occupational Ebola exposure during the 2014-2016 West African outbreak. Enrolled Apr-Aug 2015 across 5 districts of Sierra Leone (Western Area Urban + Rural, Bombali, Port Loko, Tonkolili). Individually randomized 1:1 to immediate (within 7d, n=4,341) vs deferred (18-24wk, n=4,310) single-dose intramuscular rVSV\\u0394G-ZEBOV. Open-label by design.', highlights: ['8,651', 'Sierra Leone', 'healthcare workers', '4,341', '4,310', 'rVSV', 'open-label', 'immediate', 'deferred'] },
                        { label: 'Primary outcome — vaccine efficacy', source: 'Widdowson 2018 CID, primary endpoint', text: 'Laboratory-confirmed Ebola during the 18-24 week randomized phase: 0 cases in immediate arm vs 0 cases in deferred arm. NO EFFICACY ESTIMATE POSSIBLE — the West African outbreak waned dramatically during the trial period; no community transmission was observed by trial midpoint. Safety endpoint at 6 months: SAEs comparable between arms (161 immediate vs 154 deferred). The Guinea ring vaccination trial (Henao-Restrepo 2017 Lancet) provides the efficacy evidence (100% protection >=10d post-vaccination); STRIVE established healthcare-worker safety and feasibility in the most-affected country.', highlights: ['0', '0', 'no cases', 'outbreak waned', 'SAEs comparable', 'Guinea ring', '100%'] },
                        { label: 'Risk of Bias (RoB 2.0)', source: 'STRIVE design + RoB 2.0', text: 'D1 LOW (individual 1:1 randomization). D2 HIGH (open-label by ethics design — could not deny access to the only candidate vaccine during an active outbreak; participants knew arm assignment). D3 LOW (active phone-based safety follow-up at high retention). D4 LOW (standardized PCR Ebola lab confirmation independent of arm). D5 LOW (SAP locked).', highlights: ['LOW', '1:1', 'open-label', 'HIGH', 'PCR', 'standardized'] }
                    ]
                },

                'LEGACY-PACTR-EBOLA-CI-RING': {

                    name: 'Ebola ça Suffit Guinea Ring (Henao-Restrepo 2017)', pmid: '28017403', phase: 'III', year: 2017, tE: 0, tN: 2119, cE: 16, cN: 2041, group: 'Henao-Restrepo AM et al. Efficacy and effectiveness of an rVSV-vectored vaccine in preventing Ebola virus disease: final results from the Guinea ring vaccination, open-label, cluster-randomised trial (Ebola Ca Suffit!). Lancet 2017;389:505-518. WHO + MSF + Norwegian Institute of Public Health + Guinea Ministry of Health. Cluster-randomized open-label ring vaccination trial in 117 rings (cluster of contacts and contacts-of-contacts of confirmed Ebola cases) in Guinea (Basse-Guinée, Conakry) Apr-Jul 2015. Rings randomized 1:1 to immediate (n=51 rings, 2,119 individuals offered, 1,545 vaccinated) vs delayed (n=47 rings, 2,041 individuals, 1,469 vaccinated 21 days later) single-dose intramuscular rVSV-ZEBOV. PRIMARY ENDPOINT: laboratory-confirmed Ebola virus disease at >=10 days post-randomization. RESULT: 0/2,119 in immediate (>=10d post-vacc) vs 16/2,041 in delayed (10-31d post-randomization, before scheduled vaccination); vaccine efficacy 100% (95% CI 79.3-100; P=0.004). Among >=10d-post-vaccinated individuals only: 0/4,123 vs 23 cases in non-vaccinated unrelated rings. Drove WHO prequalification of Ervebo (Nov 2019) and FDA approval (Dec 2019). REGISTERED ON PACTR (Pan African Clinical Trials Registry) AS PACTR201503001057193 — NOT on ClinicalTrials.gov; uses synthetic LEGACY-PACTR-EBOLA-CI-RING key in this dashboard.',

                    estimandType: 'RR', publishedHR: 0.0, hrLCI: 0.0, hrUCI: 0.207, pubHR: 0.0,

                    allOutcomes: [
                        { shortLabel: 'EBV_VE', title: 'Laboratory-confirmed Ebola at >=10d post-randomization (immediate ring vs delayed ring)', tE: 0, cE: 16, type: 'PRIMARY', matchScore: 100, effect: 0.0, lci: 0.0, uci: 0.207, estimandType: 'RR' },

                        { shortLabel: 'SAE_30D', title: 'Serious adverse events at 30 days post-vaccination', tE: 56, cE: 0, type: 'SAFETY', matchScore: 70, effect: 1.85, lci: 0.85, uci: 4.04, estimandType: 'RR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Henao-Restrepo AM, Camacho A, Longini IM, et al. Efficacy and effectiveness of an rVSV-vectored vaccine in preventing Ebola virus disease: final results from the Guinea ring vaccination, open-label, cluster-randomised trial (Ebola Ca Suffit!). Lancet 2017;389:505-518. PMID 28017403. DOI 10.1016/S0140-6736(16)32621-6. PACTR201503001057193.',

                    sourceUrl: 'https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(16)32621-6/fulltext',

                    ctgovUrl: null,

                    evidence: [
                        { label: 'Enrollment', source: 'Henao-Restrepo 2017 Lancet, CONSORT', text: '117 rings (clusters of contacts and contacts-of-contacts of newly-confirmed Ebola index cases) randomized 1:1 across Basse-Guinée and Conakry between Apr 1 and Jul 20, 2015. Immediate-vaccination arm: 51 rings, 2,119 individuals offered, 1,545 vaccinated within 1-2 days. Delayed-vaccination arm: 47 rings, 2,041 individuals offered, 1,469 vaccinated 21 days later. Open-label cluster-randomized ring design — adapted in real-time during an active outbreak. Median ring size 80 individuals.', highlights: ['117 rings', 'Guinea', 'Conakry', '2,119', '2,041', 'rings', 'cluster-randomized', 'open-label', '21 days'] },
                        { label: 'Primary outcome — vaccine efficacy', source: 'Henao-Restrepo 2017 Lancet, primary endpoint', text: 'Laboratory-confirmed Ebola virus disease at >=10 days post-randomization (allowing for vaccine onset of immunity). Immediate-vaccination arm: 0 cases in 2,119 ring members during the >=10d post-randomization window. Delayed-vaccination arm: 16 cases in 2,041 ring members during the 10-31d post-randomization window (i.e., before delayed vaccination scheduled). Vaccine efficacy 100% (95% CI 79.3 to 100; P=0.004 by per-protocol analysis with 16 vs 0 case split). This is the primary efficacy evidence for rVSV-ZEBOV (Ervebo); STRIVE (Sierra Leone) and PREVAIL I (Liberia) provide complementary safety/feasibility evidence.', highlights: ['16', '0', '100%', '79.3', '10 days', '21 days', 'P=0.004', 'Ervebo'] },
                        { label: 'Risk of Bias (RoB 2.0)', source: 'Henao-Restrepo 2017 design + RoB 2.0', text: 'D1 LOW (cluster randomization with computer-generated allocation, central monitoring). D2 HIGH (open-label by ethics design — outbreak setting). D3 LOW (active surveillance with PCR confirmation; complete ring tracing). D4 LOW (independent endpoint adjudication committee). D5 LOW (interim analysis pre-specified; switched to single-arm after early efficacy signal).', highlights: ['LOW', 'cluster', 'computer-generated', 'open-label', 'HIGH', 'PCR', 'adjudication'] }
                    ]
                }
            }"""


def replace_or_die(text, old, new):
    if old not in text:
        raise SystemExit(f"old string not found: {old[:80]!r}...")
    return text.replace(old, new)


def build_hbv():
    FILE = Path("HEPATITIS_B_TAF_TDF_REVIEW.html")
    text = FILE.read_text(encoding="utf-8")
    text = replace_or_die(text,
        "<title>RapidMeta Cardiology | SGLT2-HF Ultra-Precision v12.0</title>",
        "<title>RapidMeta Hepatology | TAF vs TDF for Chronic Hepatitis B v0.1 (Buti+Chan 2016, post-2010)</title>")
    text = replace_or_die(text,
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT03036124', 'NCT03057977', 'NCT03057951', 'NCT03619213', 'NCT03521934']);",
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT01940341', 'NCT01940471']);")
    text = replace_or_die(text,
        "protocol: { pop: 'Adults with heart failure across ejection fraction spectrum', int: 'SGLT2 or dual SGLT1/2 inhibitor therapy (dapagliflozin, empagliflozin, or sotagliflozin)', comp: 'Placebo + guideline-directed therapy', out: 'CV Death or Worsening Heart Failure Composite', subgroup: 'EF phenotype (HFrEF vs HFpEF), drug class member, diabetes status', query: '', rctOnly: true, post2015: true },",
        "protocol: { pop: 'Adults aged 18+ with chronic hepatitis B virus infection (HBV DNA >=20,000 IU/mL, ALT >ULN). Two pivotal trials: HBeAg-negative cohort (Buti 2016, n=425) + HBeAg-positive cohort (Chan 2016, n=873). High Africa relevance: HBV prevalence 6.1% across sub-Saharan Africa (highest WHO region) — the pivotal evidence supporting WHO 2024 guideline preference for TAF in low-BMD and renal-impairment populations', int: 'Tenofovir alafenamide (TAF) 25mg orally once daily', comp: 'Tenofovir disoproxil fumarate (TDF) 300mg orally once daily', out: 'HBV DNA <29 IU/mL at Week 48 (FDA snapshot virological response, primary efficacy); ALT normalization at Week 48; bone mineral density change; renal function (eGFR-CG) change at Week 48 (key safety endpoints)', subgroup: 'HBeAg status, baseline HBV DNA, prior NA exposure, age, region', query: '', rctOnly: true, post2015: true },")
    text = replace_or_die(text,
        "{ 'DAPA-HF': 'Dapagliflozin', 'DELIVER': 'Dapagliflozin', 'EMPEROR-Reduced': 'Empagliflozin', 'EMPEROR-Preserved': 'Empagliflozin', 'SOLOIST-WHF': 'Sotagliflozin' }",
        "{ 'GS-US-320-0108 (TAF vs TDF, HBeAg-negative)': 'Tenofovir alafenamide', 'GS-US-320-0110 (TAF vs TDF, HBeAg-positive)': 'Tenofovir alafenamide' }")
    text = replace_or_die(text,
        "'NCT03036124': 'DAPA-HF',\n\n\n                'NCT03057977': 'EMPEROR-Reduced',\n\n\n                'NCT03057951': 'EMPEROR-Preserved',\n\n\n                'NCT03619213': 'DELIVER',\n\n\n                'NCT03521934': 'SOLOIST-WHF'",
        "'NCT01940341': 'GS-US-320-0108 (TAF vs TDF, HBeAg-negative)',\n\n\n                'NCT01940471': 'GS-US-320-0110 (TAF vs TDF, HBeAg-positive)'")
    text = replace_realdata(text, HBV_BODY)
    text = text.replace("SGLT2-HF v1.0", "HBV TAF v0.1")
    text = text.replace("SGLT2 Inhibitors for Heart Failure Outcomes: A Living Systematic Review and Meta-Analysis of Randomized Controlled Trials",
                        "Tenofovir Alafenamide vs Tenofovir Disoproxil Fumarate for Chronic Hepatitis B: Pivotal-Pair Pooled Review (Buti+Chan 2016, post-2010 drug)")
    text = text.replace("SGLT2 Inhibitors in Heart Failure", "TAF vs TDF for Chronic HBV")
    text = text.replace('value="Adults with heart failure"', 'value="Adults with chronic hepatitis B (HBeAg+ or HBeAg-)"')
    text = text.replace("value=\"Heart Failure\"", "value=\"Hepatitis B\"")
    FILE.write_text(text, encoding="utf-8")
    print(f"  HBV TAF: {FILE.stat().st_size:,}")


def build_ebola():
    FILE = Path("EBOLA_VACCINE_REVIEW.html")
    text = FILE.read_text(encoding="utf-8")
    text = replace_or_die(text,
        "<title>RapidMeta Cardiology | SGLT2-HF Ultra-Precision v12.0</title>",
        "<title>RapidMeta Vaccinology | rVSV-ZEBOV Ebola Vaccine v0.1 (STRIVE Sierra Leone + Guinea Ring, post-2014)</title>")
    text = replace_or_die(text,
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT03036124', 'NCT03057977', 'NCT03057951', 'NCT03619213', 'NCT03521934']);",
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT02378753', 'LEGACY-PACTR-EBOLA-CI-RING']);")
    text = replace_or_die(text,
        "protocol: { pop: 'Adults with heart failure across ejection fraction spectrum', int: 'SGLT2 or dual SGLT1/2 inhibitor therapy (dapagliflozin, empagliflozin, or sotagliflozin)', comp: 'Placebo + guideline-directed therapy', out: 'CV Death or Worsening Heart Failure Composite', subgroup: 'EF phenotype (HFrEF vs HFpEF), drug class member, diabetes status', query: '', rctOnly: true, post2015: true },",
        "protocol: { pop: 'Adults aged 18+ at high occupational or contact risk of Ebola virus exposure during the 2014-2016 West African outbreak. Two pivotal trials: STRIVE Sierra Leone healthcare workers (n=8,651, individually-randomized) + Guinea ring trial (Henao-Restrepo 2017 cluster-randomized, n=4,160 across 117 rings)', int: 'Single-dose intramuscular rVSV\\u0394G-ZEBOV (Merck V920, BPSC-1001) — recombinant vesicular stomatitis virus expressing Zaire Ebola glycoprotein. Now licensed as Ervebo', comp: 'Deferred vaccination (STRIVE: 18-24 weeks later; Guinea: 21 days later)', out: 'Laboratory-confirmed Ebola virus disease at >=10 days post-randomization (Guinea primary efficacy); SAEs at 6 months (STRIVE primary safety)', subgroup: 'Age, occupation (healthcare worker vs frontline vs ring contact), district/country, ring size', query: '', rctOnly: true, post2015: true },")
    text = replace_or_die(text,
        "{ 'DAPA-HF': 'Dapagliflozin', 'DELIVER': 'Dapagliflozin', 'EMPEROR-Reduced': 'Empagliflozin', 'EMPEROR-Preserved': 'Empagliflozin', 'SOLOIST-WHF': 'Sotagliflozin' }",
        "{ 'STRIVE Sierra Leone (rVSVdG-ZEBOV)': 'rVSV-ZEBOV (Ervebo)', 'Ebola ca Suffit Guinea Ring (Henao-Restrepo 2017)': 'rVSV-ZEBOV (Ervebo)' }")
    text = replace_or_die(text,
        "'NCT03036124': 'DAPA-HF',\n\n\n                'NCT03057977': 'EMPEROR-Reduced',\n\n\n                'NCT03057951': 'EMPEROR-Preserved',\n\n\n                'NCT03619213': 'DELIVER',\n\n\n                'NCT03521934': 'SOLOIST-WHF'",
        "'NCT02378753': 'STRIVE Sierra Leone',\n\n\n                'LEGACY-PACTR-EBOLA-CI-RING': 'Guinea Ring (Ebola ca Suffit)'")
    text = replace_realdata(text, EBOLA_BODY)
    text = text.replace("SGLT2-HF v1.0", "Ebola Vaccine v0.1")
    text = text.replace("SGLT2 Inhibitors for Heart Failure Outcomes: A Living Systematic Review and Meta-Analysis of Randomized Controlled Trials",
                        "rVSV-ZEBOV Ebola Vaccine for High-Risk Populations: Two-Trial Pooled Review (STRIVE Sierra Leone + Guinea Ring, post-2014)")
    text = text.replace("SGLT2 Inhibitors in Heart Failure", "rVSV-ZEBOV for Ebola Prevention")
    text = text.replace('value="Adults with heart failure"', 'value="Adults at high Ebola exposure risk during 2014-2016 outbreak"')
    text = text.replace("value=\"Heart Failure\"", "value=\"Ebola\"")
    FILE.write_text(text, encoding="utf-8")
    print(f"  Ebola: {FILE.stat().st_size:,}")


if __name__ == "__main__":
    build_hbv()
    build_ebola()
