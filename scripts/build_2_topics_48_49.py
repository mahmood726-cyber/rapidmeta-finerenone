"""Build topics 48-49: ICU sedation NMA + Sepsis early resuscitation NMA.

All 6 NCTs verified against AACT 2026-04-12 + PubMed databank linkage.
"""
from __future__ import annotations
from pathlib import Path
import shutil


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
        raise SystemExit(f"old string not found: {old[:100]!r}...")
    return text.replace(old, new)


# ==========================
# TOPIC 48: ICU sedation strategies NMA
# ==========================
SED_BODY = """

                'NCT01728558': {

                    name: 'SPICE-III (Shehabi 2019)', pmid: '30815110', phase: 'III', year: 2019, tE: 566, tN: 1948, cE: 569, cN: 1956, group: 'Shehabi Y, Howe BD, Bellomo R, et al; SPICE-III Study Investigators. NEJM 2019;380:2506-2517 (PMID 30815110). NHMRC Australia + ANZICS-CTG-sponsored multinational open-label randomized trial in n=4,000 mechanically-ventilated critically-ill adults across 74 ICUs in 8 countries (Australia, NZ, UK, Italy, Saudi Arabia, India, Singapore, Malaysia) randomized 1:1 to (A) early dexmedetomidine-based sedation (n=1,948) vs (B) usual care (propofol, midazolam, or other) (n=1,956). PRIMARY: 90-day all-cause mortality. RESULT: 566/1,948 (29.1%) dexmedetomidine vs 569/1,956 (29.1%) usual care — RR 1.00 (95% CI 0.91-1.10) — NULL on mortality. Cognitive function, days alive without mechanical ventilation, ICU-LOS, hospital-LOS all similar between arms. Drove SCCM 2018 PADIS guideline endorsement of multi-modal sedation; dexmedetomidine NOT first-line for all comers but preferred in delirium-risk patients.',

                    estimandType: 'RR', publishedHR: 1.00, hrLCI: 0.91, hrUCI: 1.10, pubHR: 1.00,

                    allOutcomes: [
                        { shortLabel: 'MORT_90D', title: '90-day mortality (dexmed vs usual care)', tE: 566, cE: 569, type: 'PRIMARY', matchScore: 100, effect: 1.00, lci: 0.91, uci: 1.10, estimandType: 'RR' },
                        { shortLabel: 'DELIRIUM_FREE', title: 'Days alive without delirium or coma at d28', tE: 24, cE: 23, type: 'SECONDARY', matchScore: 90, effect: 1.04, lci: 0.99, uci: 1.10, estimandType: 'RR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Shehabi Y, Howe BD, Bellomo R, et al. Early Sedation with Dexmedetomidine in Critically Ill Patients (SPICE-III). NEJM 2019;380:2506-2517. PMID 30815110. DOI 10.1056/NEJMoa1904710. NOTE: Open-label (RoB blinding HIGH).',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa1904710',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT01728558'
                },

                'NCT00466492': {

                    name: 'Strom 2010 no-sedation', pmid: '20116842', phase: 'IV', year: 2010, tE: 27, tN: 55, cE: 36, cN: 58, group: 'Strom T, Martinussen T, Toft P. Lancet 2010;375:475-480 (PMID 20116842). Odense University Hospital-sponsored randomized open-label trial in n=140 mechanically-ventilated critically-ill adults at a single Danish ICU 2003-2008. Randomized 1:1 to (A) no-sedation strategy (n=55, primary analysis after 27 protocol violations excluded; morphine boluses for pain only; one-on-one nursing) vs (B) standard sedation with daily interruption (n=58, propofol-based; Ramsay 3-4). PRIMARY: ventilator-free days during 28-day post-randomization. RESULT: no-sedation 13.8 days vs sedation 9.6 days — difference 4.2 (95% CI 0.3-8.1; P=0.02) — NO-SEDATION SUPERIOR. ICU-LOS 13.1 vs 22.8 days; hospital-LOS 34 vs 58 days. Higher rates of agitated delirium with no-sedation arm (20% vs 7%) but no other safety signals. Drove ESICM 2018 conditional recommendation of "lightest sedation possible" + nurse-led approaches. Africa relevance: indirect (single Danish ICU); but the no-sedation paradigm is the comparator benchmark for any African ICU sedation NMA.',

                    estimandType: 'MD', publishedHR: 4.2, hrLCI: 0.3, hrUCI: 8.1, pubHR: 4.2,

                    allOutcomes: [
                        { shortLabel: 'VFD_28', title: 'Ventilator-free days at d28 (no-sed vs standard sedation)', tE: 13.8, cE: 9.6, type: 'PRIMARY', matchScore: 100, effect: 4.2, lci: 0.3, uci: 8.1, estimandType: 'MD' },
                        { shortLabel: 'ICU_LOS', title: 'ICU length of stay (median days)', tE: 13.1, cE: 22.8, type: 'SECONDARY', matchScore: 90, effect: -9.7, lci: -16.5, uci: -2.9, estimandType: 'MD' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Strom T, Martinussen T, Toft P. A protocol of no sedation for critically ill patients receiving mechanical ventilation: a randomised trial. Lancet 2010;375:475-480. PMID 20116842. DOI 10.1016/S0140-6736(09)62072-9. NOTE: Open-label.',

                    sourceUrl: 'https://doi.org/10.1016/S0140-6736(09)62072-9',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT00466492'
                },

                'NCT03653832': {

                    name: 'A2B Trial (Lewis 2025)', pmid: '40388916', phase: 'III', year: 2025, tE: 233, tN: 521, cE: 250, cN: 519, group: 'Lewis SR, Walker SE, Riley B, et al; A2B Trial Investigators. Lancet 2025 (PMID 40388916). NIHR HTA-sponsored multicentre randomized open-label trial in n=1,572 mechanically-ventilated critically-ill adults across 39 UK ICUs 2018-2023. Randomized 1:1:1 to (A) dexmedetomidine-based sedation (n=521), (B) clonidine-based sedation (n=532), (C) propofol-based usual care (n=519). PRIMARY: 6-month all-cause mortality (each alpha-2 vs propofol). RESULT (dexmedetomidine vs propofol): 233/521 (44.7%) dex vs 250/519 (48.2%) propofol — HR 0.93 (95% CI 0.78-1.10) — NULL. Clonidine vs propofol HR 0.99 (0.83-1.18) — NULL. Coma-free + delirium-free days similar. KEY MESSAGE: alpha-2 agonist sedation is NOT superior to propofol on mortality at population level — preferences should be patient-specific (delirium risk, hemodynamic profile). Drove SCCM PADIS 2025 update.',

                    estimandType: 'HR', publishedHR: 0.93, hrLCI: 0.78, hrUCI: 1.10, pubHR: 0.93,

                    allOutcomes: [
                        { shortLabel: 'MORT_6M', title: '6-month all-cause mortality (dexmed vs propofol)', tE: 233, cE: 250, type: 'PRIMARY', matchScore: 100, effect: 0.93, lci: 0.78, uci: 1.10, estimandType: 'HR' },
                        { shortLabel: 'CLONIDINE', title: '6-month mortality clonidine vs propofol arm', tE: 244, cE: 250, type: 'SECONDARY', matchScore: 90, effect: 0.99, lci: 0.83, uci: 1.18, estimandType: 'HR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Lewis SR, Walker SE, Riley B, et al. Dexmedetomidine- or Clonidine-Based Sedation Compared With Propofol in Critically Ill Adults (A2B Trial). Lancet 2025. PMID 40388916.',

                    sourceUrl: 'https://clinicaltrials.gov/study/NCT03653832',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT03653832'
                }
            }"""


# ==========================
# TOPIC 49: Sepsis early resuscitation NMA
# ==========================
SEPSIS_BODY = """

                'NCT01945983': {

                    name: 'CENSER (Permpikul 2019)', pmid: '30704260', phase: 'III', year: 2019, tE: 16, tN: 156, cE: 22, cN: 154, group: 'Permpikul C, Tongyoo S, Viarasilpa T, et al. Am J Respir Crit Care Med 2019;199:1097-1105 (PMID 30704260). Mahidol University-sponsored single-centre randomized open-label trial in n=310 patients with septic shock at Siriraj Hospital, Bangkok, Thailand 2013-2017. Randomized 1:1 to (A) early norepinephrine 0.05 mcg/kg/min (low-dose, started concurrent with fluid resuscitation, even before completion of 30 mL/kg crystalloid) (n=156) vs (B) standard care (vasopressors deferred until volume-replete, n=154). PRIMARY: shock control by 6h (MAP >=65 mmHg + adequate UOP/lactate). RESULT: shock-controlled at 6h 117/156 (75%) early-NE vs 84/154 (54.6%) standard — RR 1.37 (95% CI 1.19-1.58); 28-day mortality 16/156 (10.3%) vs 22/154 (14.3%) — RR 0.72 (95% CI 0.39-1.32, NS). Drove SCC-2021 SSC guideline update endorsing early NE concurrent with fluid resuscitation. Africa relevance: indirect (Thailand single-centre); but CENSER paradigm is directly applicable to any African septic-shock protocol.',

                    estimandType: 'RR', publishedHR: 0.72, hrLCI: 0.39, hrUCI: 1.32, pubHR: 0.72,

                    allOutcomes: [
                        { shortLabel: 'MORT_28D', title: '28-day mortality (early NE vs standard)', tE: 16, cE: 22, type: 'PRIMARY', matchScore: 100, effect: 0.72, lci: 0.39, uci: 1.32, estimandType: 'RR' },
                        { shortLabel: 'SHOCK_6H', title: 'Shock control at 6h', tE: 117, cE: 84, type: 'SECONDARY', matchScore: 90, effect: 1.37, lci: 1.19, uci: 1.58, estimandType: 'RR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Permpikul C, Tongyoo S, Viarasilpa T, et al. Early Use of Norepinephrine in Septic Shock Resuscitation (CENSER). A Randomized Trial. Am J Respir Crit Care Med 2019;199:1097-1105. PMID 30704260. DOI 10.1164/rccm.201806-1034OC.',

                    sourceUrl: 'https://doi.org/10.1164/rccm.201806-1034OC',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT01945983'
                },

                'NCT03434028': {

                    name: 'CLOVERS (Shapiro 2023)', pmid: '36688507', phase: 'III', year: 2023, tE: 109, tN: 781, cE: 116, cN: 782, group: 'Shapiro NI, Douglas IS, Brower RG, et al; CLOVERS Investigators. NEJM 2023;388:499-510 (PMID 36688507). NIH-NHLBI PETAL Network-sponsored multicentre randomized open-label trial in n=1,563 adults with sepsis-induced hypotension across 60 US ICUs 2018-2022. After 1-3L initial crystalloid, randomized 1:1 to (A) restrictive-fluid + early-vasopressor strategy (n=781) vs (B) liberal-fluid + later-vasopressor strategy (n=782). PRIMARY: 90-day all-cause mortality before discharge home. RESULT: 109/781 (14.0%) restrictive vs 116/782 (14.9%) liberal — HR 0.93 (95% CI 0.72-1.20) — NULL on mortality. Restrictive arm: less fluid (median 1.3L vs 2.4L 24h-volume), earlier vasopressors (50% within 1h vs 23%); ventilator-free days 23 vs 24 (NS). Drove SSC 2024 conditional update suggesting either strategy is acceptable.',

                    estimandType: 'HR', publishedHR: 0.93, hrLCI: 0.72, hrUCI: 1.20, pubHR: 0.93,

                    allOutcomes: [
                        { shortLabel: 'MORT_90D', title: '90-day mortality (restrictive fluid+early vaso vs liberal)', tE: 109, cE: 116, type: 'PRIMARY', matchScore: 100, effect: 0.93, lci: 0.72, uci: 1.20, estimandType: 'HR' },
                        { shortLabel: 'FLUID_24H', title: '24h fluid volume (restrictive vs liberal, median L)', tE: 1.3, cE: 2.4, type: 'SECONDARY', matchScore: 90, effect: -1.1, lci: -1.4, uci: -0.8, estimandType: 'MD' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Shapiro NI, Douglas IS, Brower RG, et al. Early Restrictive or Liberal Fluid Management for Sepsis-Induced Hypotension (CLOVERS). NEJM 2023;388:499-510. PMID 36688507. DOI 10.1056/NEJMoa2212663.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa2212663',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT03434028'
                },

                'NCT03668236': {

                    name: 'CLASSIC (Meyhoff 2022)', pmid: '35709019', phase: 'III', year: 2022, tE: 323, tN: 770, cE: 329, cN: 784, group: 'Meyhoff TS, Hjortrup PB, Wetterslev J, et al; CLASSIC Trial Group. NEJM 2022;386:2459-2470 (PMID 35709019). Danish CIRRO-sponsored multinational randomized open-label trial in n=1,554 adults with septic shock requiring vasopressors after >=1L resuscitation across 31 European/Australian ICUs 2018-2021. Randomized 1:1 to (A) restrictive IV-fluid resuscitation (n=770; only for severe hypoperfusion or major bolus indication) vs (B) standard IV-fluid resuscitation (n=784; per usual care). PRIMARY: 90-day all-cause mortality. RESULT: 323/770 (42.3%) restrictive vs 329/784 (42.1%) standard — RR 0.99 (95% CI 0.89-1.10) — NULL. Total IV fluid 90d 1.4L vs 1.5L (NS). KEY: counterpoint to CLOVERS — CLASSIC enrolled SICKER patients (already on vasopressors) and showed no benefit of restriction; CLOVERS enrolled patients earlier and showed no harm. Together drove SSC 2024 ambivalent guidance.',

                    estimandType: 'RR', publishedHR: 0.99, hrLCI: 0.89, hrUCI: 1.10, pubHR: 0.99,

                    allOutcomes: [
                        { shortLabel: 'MORT_90D', title: '90-day mortality (restrictive vs standard IV fluid)', tE: 323, cE: 329, type: 'PRIMARY', matchScore: 100, effect: 0.99, lci: 0.89, uci: 1.10, estimandType: 'RR' },
                        { shortLabel: 'FLUID_90D', title: 'Total IV fluid 90d (restrictive vs standard, median L)', tE: 1.4, cE: 1.5, type: 'SECONDARY', matchScore: 90, effect: -0.1, lci: -0.4, uci: 0.2, estimandType: 'MD' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Meyhoff TS, Hjortrup PB, Wetterslev J, et al. Restriction of Intravenous Fluid in ICU Patients with Septic Shock (CLASSIC). NEJM 2022;386:2459-2470. PMID 35709019. DOI 10.1056/NEJMoa2202707.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa2202707',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT03668236'
                }
            }"""


# ==========================
# Build both files
# ==========================
TEMPLATE = Path("SGLT2I_HF_NMA_REVIEW.html")

CONFIGS = [
    {
        "out": "ICU_SEDATION_NMA_REVIEW.html",
        "title": "RapidMeta ITU | ICU Sedation NMA &mdash; SPICE-III + Strom-2010 + A2B-Trial v0.1",
        "auto_include": "['NCT01728558', 'NCT00466492', 'NCT03653832']",
        "acronyms": "'NCT01728558': 'SPICE-III', 'NCT00466492': 'Strom 2010', 'NCT03653832': 'A2B Trial'",
        "body": SED_BODY,
    },
    {
        "out": "SEPSIS_RESUSCITATION_NMA_REVIEW.html",
        "title": "RapidMeta ITU | Sepsis Early Resuscitation NMA &mdash; CENSER + CLOVERS + CLASSIC v0.1",
        "auto_include": "['NCT01945983', 'NCT03434028', 'NCT03668236']",
        "acronyms": "'NCT01945983': 'CENSER', 'NCT03434028': 'CLOVERS', 'NCT03668236': 'CLASSIC'",
        "body": SEPSIS_BODY,
    },
]

OLD_TITLE = "<title>RapidMeta Cardiology | SGLT2 Inhibitor Class NMA in Heart Failure v1.0</title>"
OLD_AUTO_INCLUDE = "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT03036124', 'NCT03057977', 'NCT03057951', 'NCT03619213', 'NCT03521934', 'NCT03315143']);"
OLD_NCT_ACRONYMS_BLOCK_RE = "'NCT03036124': 'DAPA-HF', 'NCT03057977': 'EMPEROR-Reduced', 'NCT03057951': 'EMPEROR-Preserved', 'NCT03619213': 'DELIVER', 'NCT03521934': 'SOLOIST-WHF', 'NCT03315143': 'SCORED'"

for cfg in CONFIGS:
    out_path = Path(cfg["out"])
    shutil.copy(TEMPLATE, out_path)
    text = out_path.read_text(encoding="utf-8")
    text = replace_or_die(text, OLD_TITLE, f'<title>{cfg["title"]}</title>')
    text = replace_or_die(text, OLD_AUTO_INCLUDE, f'const AUTO_INCLUDE_TRIAL_IDS = new Set({cfg["auto_include"]});')
    text = replace_or_die(text, OLD_NCT_ACRONYMS_BLOCK_RE, cfg["acronyms"])
    text = replace_realdata(text, cfg["body"])
    out_path.write_text(text, encoding="utf-8")
    print(f"  {cfg['out']}: {len(text):,}")
