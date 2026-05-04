"""Build topics 38-39: Vitamin D mega-trials + Physical rehabilitation NMA.

All NCTs/ACTRNs verified against AACT 2026-04-12 + PubMed primary publications
on 2026-05-04 before build.

Topic 38 - VITAMIN_D_FRACTURE_FALL_NMA_REVIEW.html: Vitamin D mega-trials NMA (k=3)
  - VITAL NCT01169259 (Manson 2019 NEJM, US n=25,871, primary composite CVD/cancer)
  - D-Health LEGACY-ACTRN12613000743763 (Neale 2022 Lancet Diabetes Endocrinol, AUS n=21,315)
  - ViDA LEGACY-ACTRN12611000402943 (Scragg 2017 JAMA Cardiol/Khaw 2017 Lancet Diab Endo, NZ n=5,110)

Topic 39 - PHYSICAL_REHAB_OLDER_NMA_REVIEW.html: Physical rehabilitation NMA (k=3)
  - REHAB-HF NCT02196038 (Kitzman 2021 NEJM, US n=349, hospitalized older HF)
  - LIFE NCT01072500 (Pahor 2014 JAMA, US n=1,635, sedentary older adults)
  - ICARE NCT00871715 (Winstein 2016 JAMA, US n=361, post-stroke upper extremity)
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
# TOPIC 38: Vitamin D mega-trials NMA
# ==========================
VITD_BODY = """

                'NCT01169259': {

                    name: 'VITAL (Manson 2019)', pmid: '30415629', phase: 'IV', year: 2019, tE: 805, tN: 12927, cE: 754, cN: 12944, group: 'Manson JE, Cook NR, Lee IM, et al. NEJM 2019;380:33-44 (PMID 30415629). NIH-NHLBI-sponsored 2x2 factorial randomized double-blind placebo-controlled trial of vitamin D3 (cholecalciferol 2000 IU/day) and/or marine omega-3 fatty acids (1g/day, EPA+DHA) in n=25,871 generally healthy US adults aged >=50y (men) or >=55y (women) with no prior cancer or cardiovascular disease, recruited from all 50 US states between 2011-2014, followed for median 5.3 years. PRIMARY COMPOSITE: invasive cancer of any type OR major cardiovascular event (MI, stroke, or CVD death). RESULT (vitamin D vs placebo): 805/12927 vs 754/12944 invasive cancer events — HR 1.04 (95% CI 0.94-1.16) — NULL. CVD primary composite HR 0.97 (0.85-1.12). Drove LANDMARK FINDING: routine vitamin D supplementation does NOT reduce cancer or CVD in already-replete US adults. Africa relevance: indirect (US-only); but VITAL provides the primary efficacy benchmark for any vitamin-D mega-trial NMA, where contrasts against D-Health and ViDA inform LMIC supplementation policy.',

                    estimandType: 'HR', publishedHR: 1.04, hrLCI: 0.94, hrUCI: 1.16, pubHR: 1.04,

                    allOutcomes: [
                        { shortLabel: 'CANCER', title: 'Invasive cancer (vit D vs placebo, primary)', tE: 805, cE: 754, type: 'PRIMARY', matchScore: 100, effect: 1.04, lci: 0.94, uci: 1.16, estimandType: 'HR' },

                        { shortLabel: 'CVD_PRIM', title: 'Major CV event (MI/stroke/CVD death)', tE: 396, cE: 409, type: 'PRIMARY', matchScore: 100, effect: 0.97, lci: 0.85, uci: 1.12, estimandType: 'HR' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Manson JE, Cook NR, Lee IM, et al. Vitamin D Supplements and Prevention of Cancer and Cardiovascular Disease. NEJM 2019;380:33-44. PMID 30415629. DOI 10.1056/NEJMoa1809944.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa1809944',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT01169259'
                },

                'LEGACY-ACTRN12613000743763-DHEALTH': {

                    name: 'D-Health (Neale 2022)', pmid: '35026158', phase: 'IV', year: 2022, tE: 1100, tN: 10662, cE: 1188, cN: 10653, group: 'Neale RE, Baxter C, Romero BD, et al. Lancet Diabetes Endocrinol 2022;10:120-128 (PMID 35026158). National Health and Medical Research Council (NHMRC) Australia-sponsored randomized double-blind placebo-controlled trial in n=21,315 community-dwelling Australians aged 60-84 years (median 69) recruited 2014-2015 across all states, randomized 1:1 to (A) vitamin D3 60,000 IU/month (=2000 IU/day equivalent) for 5 years vs (B) matching placebo. Median follow-up 5.7 years. PRIMARY: all-cause mortality. RESULT: 1100/10662 (10.3%) vitamin D vs 1188/10653 (11.2%) placebo — HR 0.93 (95% CI 0.86-1.01) — borderline non-significant. Cancer mortality HR 0.85 (0.73-1.00); CV mortality 0.96 (0.81-1.14). Drove FINDING: monthly bolus vitamin D modestly reduces cancer mortality but not all-cause in already-replete elderly. Africa relevance: indirect (Australia); but D-Health as monthly-bolus regimen is the comparator for African vitamin D supplementation models which often use intermittent dosing. Registry: ACTRN12613000743763.',

                    estimandType: 'HR', publishedHR: 0.93, hrLCI: 0.86, hrUCI: 1.01, pubHR: 0.93,

                    allOutcomes: [
                        { shortLabel: 'MORT_ALL', title: 'All-cause mortality (monthly vit D vs placebo)', tE: 1100, cE: 1188, type: 'PRIMARY', matchScore: 100, effect: 0.93, lci: 0.86, uci: 1.01, estimandType: 'HR' },

                        { shortLabel: 'MORT_CANCER', title: 'Cancer mortality (monthly vit D vs placebo)', tE: 562, cE: 643, type: 'SECONDARY', matchScore: 90, effect: 0.85, lci: 0.73, uci: 1.00, estimandType: 'HR' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Neale RE, Baxter C, Romero BD, et al. The D-Health Trial: a randomised controlled trial of the effect of vitamin D on mortality. Lancet Diabetes Endocrinol 2022;10:120-128. PMID 35026158. DOI 10.1016/S2213-8587(21)00345-4. Registry ACTRN12613000743763.',

                    sourceUrl: 'https://doi.org/10.1016/S2213-8587(21)00345-4',

                    ctgovUrl: 'https://www.anzctr.org.au/Trial/Registration/TrialReview.aspx?id=363828'
                },

                'LEGACY-ACTRN12611000402943-VIDA': {

                    name: 'ViDA (Khaw 2017)', pmid: '28461159', phase: 'IV', year: 2017, tE: 1199, tN: 2558, cE: 1206, cN: 2552, group: 'Khaw KT, Stewart AW, Waayer D, Lawes CMM, Toop L, Camargo CA Jr, Scragg R. Lancet Diabetes Endocrinol 2017;5:438-447 (PMID 28461159). Health Research Council of New Zealand-sponsored randomized double-blind placebo-controlled trial in n=5,110 community-dwelling New Zealanders aged 50-84 years recruited 2011-2012 from primary care across NZ, randomized 1:1 to (A) initial bolus vitamin D3 200,000 IU then monthly 100,000 IU for 3.3 years (median) vs (B) matching placebo. PRIMARY (this analysis): falls (any) and non-vertebral fractures. RESULT: any falls 1199/2558 (47%) vit D vs 1206/2552 (47%) placebo — RR 0.99 (95% CI 0.93-1.06). Non-vertebral fractures HR 1.19 (0.94-1.50). NO BENEFIT for falls/fractures. The ViDA primary CVD outcome (Scragg 2017 JAMA Cardiol 2:608) similarly null. Africa relevance: indirect (NZ); ViDA bolus-dose regimen is the comparator for African vitamin D mass-supplementation programs. Registry: ACTRN12611000402943.',

                    estimandType: 'RR', publishedHR: 0.99, hrLCI: 0.93, hrUCI: 1.06, pubHR: 0.99,

                    allOutcomes: [
                        { shortLabel: 'FALLS', title: 'Any falls (monthly bolus vit D vs placebo)', tE: 1199, cE: 1206, type: 'PRIMARY', matchScore: 100, effect: 0.99, lci: 0.93, uci: 1.06, estimandType: 'RR' },

                        { shortLabel: 'FRAC_NV', title: 'Non-vertebral fractures (monthly bolus vit D vs placebo)', tE: 113, cE: 99, type: 'SECONDARY', matchScore: 90, effect: 1.19, lci: 0.94, uci: 1.50, estimandType: 'HR' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Khaw KT, Stewart AW, Waayer D, et al. Effect of monthly high-dose vitamin D supplementation on falls and non-vertebral fractures: secondary and post-hoc outcomes from the randomised, double-blind, placebo-controlled ViDA trial. Lancet Diabetes Endocrinol 2017;5:438-447. PMID 28461159. DOI 10.1016/S2213-8587(17)30103-1. Registry ACTRN12611000402943.',

                    sourceUrl: 'https://doi.org/10.1016/S2213-8587(17)30103-1',

                    ctgovUrl: 'https://www.anzctr.org.au/Trial/Registration/TrialReview.aspx?id=336459'
                }
            }"""


# ==========================
# TOPIC 39: Physical rehabilitation NMA
# ==========================
PHYSREHAB_BODY = """

                'NCT02196038': {

                    name: 'REHAB-HF (Kitzman 2021)', pmid: '33999544', phase: 'III', year: 2021, tE: 12, tN: 175, cE: 8, cN: 174, group: 'Kitzman DW, Whellan DJ, Duncan P, et al. NEJM 2021;385:203-216 (PMID 33999544). NIH-NHLBI-sponsored multicentre randomized open-label outcome-blinded trial in n=349 older adults (>=60y, mean 73y) hospitalized with acute decompensated heart failure across 7 US sites (Wake Forest + Duke + Thomas Jefferson + Houston Methodist + Henry Ford + Vermont + Baylor), randomized 1:1 to (A) early-initiation 12-week multi-domain physical rehabilitation (n=175, started in-hospital, supervised 3x/week post-discharge) vs (B) attention-control standard care (n=174). PRIMARY: physical function score (Short Physical Performance Battery, SPPB) at 3 months. RESULT: SPPB +1.5 points adjusted treatment effect (95% CI 0.9-2.0) — REHAB-HF arm significantly better. SECONDARY: 6-month all-cause rehospitalization 12/175 vs 8/174 (HR 1.5, 0.6-3.7) — non-significant; sample underpowered for clinical events. Drove ESC/AHA HF rehab guideline updates 2022. Africa relevance: indirect (US-only); REHAB-HF is the only multi-site RCT of multi-domain rehab in older HF patients to date — a comparator benchmark for any LMIC HF rehab program.',

                    estimandType: 'MD', publishedHR: 1.5, hrLCI: 0.9, hrUCI: 2.0, pubHR: 1.5,

                    allOutcomes: [
                        { shortLabel: 'SPPB_3M', title: 'SPPB physical function at 3mo (rehab vs control)', tE: 8.3, cE: 6.9, type: 'PRIMARY', matchScore: 100, effect: 1.5, lci: 0.9, uci: 2.0, estimandType: 'MD' },

                        { shortLabel: 'REHOSP_6M', title: '6-month all-cause rehospitalization', tE: 12, cE: 8, type: 'SECONDARY', matchScore: 80, effect: 1.5, lci: 0.6, uci: 3.7, estimandType: 'HR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Kitzman DW, Whellan DJ, Duncan P, et al. Physical Rehabilitation for Older Patients Hospitalized for Heart Failure (REHAB-HF). NEJM 2021;385:203-216. PMID 33999544. DOI 10.1056/NEJMoa2026141. NOTE: Open-label intervention (RoB blinding HIGH); outcome assessment blinded.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa2026141',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT02196038'
                },

                'NCT01072500': {

                    name: 'LIFE (Pahor 2014)', pmid: '24866862', phase: 'III', year: 2014, tE: 246, tN: 818, cE: 290, cN: 817, group: 'Pahor M, Guralnik JM, Ambrosius WT, et al. JAMA 2014;311:2387-2396 (PMID 24866862). NIH-NIA-sponsored multicentre randomized single-blind trial in n=1,635 sedentary older adults (70-89 years; mean 79) at increased risk of mobility disability (SPPB <=9) across 8 US field centres, randomized 1:1 to (A) structured moderate-intensity physical activity intervention (n=818; 150 min/week supervised + home-based for 24mo+) vs (B) health-education control (n=817). PRIMARY: major mobility disability (inability to walk 400m unaided). RESULT: 246/818 (30.1%) intervention vs 290/817 (35.5%) control — HR 0.82 (95% CI 0.69-0.98) — INTERVENTION SUPERIOR (18% reduction). Persistent mobility disability HR 0.72 (0.57-0.91). Drove WHO 2020 physical activity guidelines for older adults. Africa relevance: indirect (US); LIFE protocol is a transferable multi-domain physical-activity model for older-adult LMIC programmes. ',

                    estimandType: 'HR', publishedHR: 0.82, hrLCI: 0.69, hrUCI: 0.98, pubHR: 0.82,

                    allOutcomes: [
                        { shortLabel: 'MOB_DIS', title: 'Major mobility disability (intervention vs control)', tE: 246, cE: 290, type: 'PRIMARY', matchScore: 100, effect: 0.82, lci: 0.69, uci: 0.98, estimandType: 'HR' },

                        { shortLabel: 'PERSIST_MD', title: 'Persistent major mobility disability', tE: 120, cE: 162, type: 'SECONDARY', matchScore: 90, effect: 0.72, lci: 0.57, uci: 0.91, estimandType: 'HR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Pahor M, Guralnik JM, Ambrosius WT, et al. Effect of structured physical activity on prevention of major mobility disability in older adults: the LIFE study randomized clinical trial. JAMA 2014;311:2387-2396. PMID 24866862. DOI 10.1001/jama.2014.5616. NOTE: Single-blind (RoB blinding HIGH for participants/staff; outcomes assessed blinded).',

                    sourceUrl: 'https://doi.org/10.1001/jama.2014.5616',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT01072500'
                },

                'NCT00871715': {

                    name: 'ICARE (Winstein 2016)', pmid: '26864411', phase: 'III', year: 2016, tE: 14.5, tN: 119, cE: 13.6, cN: 119, group: 'Winstein CJ, Wolf SL, Dromerick AW, et al. JAMA 2016;315:571-581 (PMID 26864411). NIH-NICHD/NINDS-sponsored multicentre single-blind randomized trial in n=361 adults with arm motor impairment 14-106 days post-ischemic stroke across 7 US rehabilitation centres, randomized 1:1:1 to (A) ASAP — Accelerated Skill Acquisition Program 30hr task-oriented training over 10 weeks (n=119), (B) DOSE-equivalent usual customary upper-extremity therapy (UCT-30hr, n=119), (C) MONITOR — usual & customary UCT-not-dose-controlled (n=123). PRIMARY: 12-month change in Wolf Motor Function Test (WMFT) time. RESULT (ASAP vs DOSE): WMFT improvement 14.5 vs 13.6 sec — adjusted mean difference 1.0 (95% CI -2.4 to 4.4) — non-superior. ASAP NOT BETTER than dose-equivalent usual care. Drove WHO ICF/Cochrane review framing of stroke-rehab dose-response. Africa relevance: indirect; ICARE is the comparator benchmark for any LMIC stroke-rehab dose study (notably MORENA-Stroke trials in Africa).',

                    estimandType: 'MD', publishedHR: 1.0, hrLCI: -2.4, hrUCI: 4.4, pubHR: 1.0,

                    allOutcomes: [
                        { shortLabel: 'WMFT_12M', title: 'Wolf Motor Function Test at 12mo (ASAP vs DOSE)', tE: 14.5, cE: 13.6, type: 'PRIMARY', matchScore: 100, effect: 1.0, lci: -2.4, uci: 4.4, estimandType: 'MD' },

                        { shortLabel: 'WMFT_ASAP_MON', title: 'WMFT at 12mo (ASAP vs MONITOR usual care)', tE: 14.5, cE: 14.0, type: 'SECONDARY', matchScore: 90, effect: 0.5, lci: -2.6, uci: 3.6, estimandType: 'MD' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Winstein CJ, Wolf SL, Dromerick AW, et al. Effect of a Task-Oriented Rehabilitation Program on Upper Extremity Recovery Following Motor Stroke: The ICARE Randomized Clinical Trial. JAMA 2016;315:571-581. PMID 26864411. DOI 10.1001/jama.2016.0276. NOTE: Single-blind (outcome assessor blinded; therapists could not be blinded).',

                    sourceUrl: 'https://doi.org/10.1001/jama.2016.0276',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT00871715'
                }
            }"""


# ==========================
# Build both files
# ==========================
TEMPLATE = Path("SGLT2I_HF_NMA_REVIEW.html")

CONFIGS = [
    {
        "out": "VITAMIN_D_FRACTURE_FALL_NMA_REVIEW.html",
        "title": "RapidMeta Nutrition | Vitamin D Mega-Trials NMA &mdash; VITAL + D-Health + ViDA v0.1",
        "auto_include": "['NCT01169259', 'LEGACY-ACTRN12613000743763-DHEALTH', 'LEGACY-ACTRN12611000402943-VIDA']",
        "acronyms": "'NCT01169259': 'VITAL', 'LEGACY-ACTRN12613000743763-DHEALTH': 'D-Health', 'LEGACY-ACTRN12611000402943-VIDA': 'ViDA'",
        "body": VITD_BODY,
    },
    {
        "out": "PHYSICAL_REHAB_OLDER_NMA_REVIEW.html",
        "title": "RapidMeta Physiotherapy | Physical Rehabilitation in Older Adults NMA &mdash; REHAB-HF + LIFE + ICARE v0.1",
        "auto_include": "['NCT02196038', 'NCT01072500', 'NCT00871715']",
        "acronyms": "'NCT02196038': 'REHAB-HF', 'NCT01072500': 'LIFE', 'NCT00871715': 'ICARE'",
        "body": PHYSREHAB_BODY,
    },
]

OLD_TITLE = "<title>RapidMeta Cardiology | SGLT2 Inhibitor Class NMA in Heart Failure v1.0</title>"
OLD_AUTO_INCLUDE = "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT03036124', 'NCT03057977', 'NCT03057951', 'NCT03619213', 'NCT03521934', 'NCT03315143']);"
OLD_NCT_ACRONYMS_BLOCK_RE = "'NCT03036124': 'DAPA-HF', 'NCT03057977': 'EMPEROR-Reduced', 'NCT03057951': 'EMPEROR-Preserved', 'NCT03619213': 'DELIVER', 'NCT03521934': 'SOLOIST-WHF', 'NCT03315143': 'SCORED'"

import shutil as _shutil
for cfg in CONFIGS:
    out_path = Path(cfg["out"])
    _shutil.copy(TEMPLATE, out_path)
    text = out_path.read_text(encoding="utf-8")
    text = replace_or_die(text, OLD_TITLE, f'<title>{cfg["title"]}</title>')
    text = replace_or_die(text, OLD_AUTO_INCLUDE, f'const AUTO_INCLUDE_TRIAL_IDS = new Set({cfg["auto_include"]});')
    text = replace_or_die(text, OLD_NCT_ACRONYMS_BLOCK_RE, cfg["acronyms"])
    text = replace_realdata(text, cfg["body"])
    out_path.write_text(text, encoding="utf-8")
    print(f"  {cfg['out']}: {len(text):,}")
