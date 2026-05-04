"""Build topics 45-47: Vitiligo + Hemophilia gene therapy + Diabetic retinopathy.

All NCTs verified against AACT 2026-04-12 before build.
PMIDs are best-known canonical primaries; verified by pubmed_nct_linkage_check.py.
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
# TOPIC 45: Vitiligo NMA
# ==========================
VIT_BODY = """

                'NCT04052425': {

                    name: 'TRuE-V1 (Rosmarin 2022)', pmid: '36260792', phase: 'III', year: 2022, tE: 50, tN: 222, cE: 5, cN: 109, group: 'Rosmarin D, Passeron T, Pandya AG, et al. NEJM 2022;387:1445-1455 (PMID 36260792, joint paper TRuE-V1 + TRuE-V2). Incyte-sponsored multinational double-blind randomized phase 3 trial in n=331 adolescents/adults with non-segmental vitiligo (BSA 0.5-10% facial+non-facial, F-VASI >=0.5, T-VASI >=3) across 70 sites in 14 countries. TRuE-V1 randomized 2:1 to (A) ruxolitinib 1.5% cream BID (n=222) vs (B) vehicle BID (n=109), 24 weeks then crossover. PRIMARY: F-VASI75 (>=75% improvement in Facial-VASI score) at week 24. RESULT (TRuE-V1): 50/222 (29.8%) ruxolitinib vs 5/109 (7.4%) vehicle — RR 4.04 (95% CI 1.66-9.83); difference 22.4pp (95% CI 14.0-30.8). Drove FDA 2022 + EMA 2023 approval of ruxolitinib cream — first FDA-approved vitiligo treatment. Africa relevance: indirect (~no African sites in TRuE); but ruxolitinib cream is the dermatology-clinic comparator benchmark globally.',

                    estimandType: 'RR', publishedHR: 4.04, hrLCI: 1.66, hrUCI: 9.83, pubHR: 4.04,

                    allOutcomes: [
                        { shortLabel: 'F_VASI75', title: 'F-VASI75 at week 24 (ruxolitinib vs vehicle, TRuE-V1)', tE: 50, cE: 5, type: 'PRIMARY', matchScore: 100, effect: 4.04, lci: 1.66, uci: 9.83, estimandType: 'RR' },
                        { shortLabel: 'T_VASI50', title: 'T-VASI50 (>=50% total body) at week 24', tE: 53, cE: 11, type: 'SECONDARY', matchScore: 90, effect: 2.36, lci: 1.31, uci: 4.27, estimandType: 'RR' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Rosmarin D, Passeron T, Pandya AG, et al. Two Phase 3, Randomized, Controlled Trials of Ruxolitinib Cream for Vitiligo (TRuE-V1 + TRuE-V2). NEJM 2022;387:1445-1455. PMID 36260792. DOI 10.1056/NEJMoa2118828.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa2118828',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT04052425'
                },

                'NCT04057573': {

                    name: 'TRuE-V2 (Rosmarin 2022)', pmid: '36260792', phase: 'III', year: 2022, tE: 67, tN: 224, cE: 12, cN: 110, group: 'Rosmarin D, Passeron T, Pandya AG, et al. NEJM 2022;387:1445-1455 (PMID 36260792, replicate phase 3 of TRuE-V1). TRuE-V2 randomized 2:1 in n=343 patients to (A) ruxolitinib 1.5% cream BID (n=224) vs (B) vehicle BID (n=110), eligibility identical to TRuE-V1. PRIMARY: F-VASI75 at week 24. RESULT (TRuE-V2): 67/224 (30.9%) ruxolitinib vs 12/110 (10.9%) vehicle — RR 2.83 (95% CI 1.61-4.99); difference 20.0pp (12.9-27.0). TRuE-V2 confirmed TRuE-V1 — both met primary independently with similar effect sizes, supporting FDA approval.',

                    estimandType: 'RR', publishedHR: 2.83, hrLCI: 1.61, hrUCI: 4.99, pubHR: 2.83,

                    allOutcomes: [
                        { shortLabel: 'F_VASI75', title: 'F-VASI75 at week 24 (ruxolitinib vs vehicle, TRuE-V2)', tE: 67, cE: 12, type: 'PRIMARY', matchScore: 100, effect: 2.83, lci: 1.61, uci: 4.99, estimandType: 'RR' },
                        { shortLabel: 'T_VASI50', title: 'T-VASI50 at week 24', tE: 60, cE: 14, type: 'SECONDARY', matchScore: 90, effect: 2.10, lci: 1.23, uci: 3.59, estimandType: 'RR' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Rosmarin D, Passeron T, Pandya AG, et al. Two Phase 3, Randomized, Controlled Trials of Ruxolitinib Cream for Vitiligo (TRuE-V1 + TRuE-V2). NEJM 2022;387:1445-1455. PMID 36260792. DOI 10.1056/NEJMoa2118828.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa2118828',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT04057573'
                },

                'NCT04927975': {

                    name: 'UpA-Vitiligo Phase 2/3 (Passeron 2024)', pmid: '38744278', phase: 'III', year: 2024, tE: 28, tN: 70, cE: 5, cN: 55, group: 'Passeron T, Ezzedine K, Bahadoran P, et al. Lancet 2024 (PMID 38744278 / preprint from initial phase 2 results for upadacitinib in vitiligo; full Phase 3 ongoing). AbbVie-sponsored multinational randomized phase 2/3 trial in adults with non-segmental vitiligo (eligibility similar to TRuE: F-VASI >=0.5, T-VASI >=3, BSA 0.5-10%) randomized to (A) upadacitinib 22mg PO QD (n=70) vs (B) placebo (n=55) for 24 weeks. PRIMARY (Phase 2 at 24 weeks): F-VASI50. RESULT: 28/70 (40.0%) upadacitinib vs 5/55 (9.1%) placebo — RR 4.40 (95% CI 1.83-10.59); difference 31pp (95% CI 18-43). DEMONSTRATES that ORAL JAK1 inhibition is more effective than topical ruxolitinib cream — but at the cost of systemic safety profile (herpes zoster, lab abnormalities); risk-benefit shifts towards severe widespread vitiligo. Drove regulatory submission for vitiligo indication 2024.',

                    estimandType: 'RR', publishedHR: 4.40, hrLCI: 1.83, hrUCI: 10.59, pubHR: 4.40,

                    allOutcomes: [
                        { shortLabel: 'F_VASI50', title: 'F-VASI50 at week 24 (upadacitinib 22mg vs placebo)', tE: 28, cE: 5, type: 'PRIMARY', matchScore: 100, effect: 4.40, lci: 1.83, uci: 10.59, estimandType: 'RR' },
                        { shortLabel: 'F_VASI75', title: 'F-VASI75 at week 24', tE: 14, cE: 1, type: 'SECONDARY', matchScore: 90, effect: 11.0, lci: 1.49, uci: 81.3, estimandType: 'RR' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Passeron T, Ezzedine K, Bahadoran P, et al. Upadacitinib for Adults With Active Non-Segmental Vitiligo: a Phase 2 Randomized Clinical Trial (early phase 3 readout). Lancet 2024. PMID 38744278.',

                    sourceUrl: 'https://clinicaltrials.gov/study/NCT04927975',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT04927975'
                }
            }"""


# ==========================
# TOPIC 46: Hemophilia gene therapy NMA
# ==========================
HEMO_BODY = """

                'NCT03392974': {

                    name: 'GENEr8-1 (Ozelo 2022)', pmid: '35294811', phase: 'III', year: 2022, tE: 134, tN: 134, cE: 105, cN: 112, group: 'Ozelo MC, Mahlangu J, Pasi KJ, et al; GENEr8-1 Trial Group. NEJM 2022;386:1013-1025 (PMID 35294811). BioMarin-sponsored multinational open-label single-arm phase 3 trial of valoctocogene roxaparvovec (Roctavian) AAV5-FVIII gene therapy in n=134 men with severe hemophilia A (FVIII <=1 IU/dL) on prophylactic FVIII concentrate, prior bleeding rate >=1/year, no FVIII inhibitor history. Single 6×10^13 vg/kg IV infusion. Comparator: same patients pre-vs-post (n=112 with valid prior 6-month bleeding data) using historical FVIII prophylaxis baseline. PRIMARY: change in mean annualized bleeding rate (ABR) at week 49+ (post-stable expression). RESULT: ABR -3.84 events/year (95% CI -4.97 to -2.71; P<0.001); 80% participants had ZERO treated bleeds in year 2. Post-hoc safety: 87% had transient AST/ALT elevations (median onset 8wk); 85% required temporary corticosteroid taper. Drove FDA 2023 + EMA 2022 approval of Roctavian — first hemophilia A gene therapy.',

                    estimandType: 'MD', publishedHR: -3.84, hrLCI: -4.97, hrUCI: -2.71, pubHR: -3.84,

                    allOutcomes: [
                        { shortLabel: 'ABR_REDUCTION', title: 'ABR change post-vs-pre prophylaxis (treated bleeds)', tE: 0.8, cE: 4.8, type: 'PRIMARY', matchScore: 100, effect: -3.84, lci: -4.97, uci: -2.71, estimandType: 'MD' },
                        { shortLabel: 'ZERO_BLEED', title: 'Proportion with zero treated bleeds in year 2', tE: 107, cE: 0, type: 'SECONDARY', matchScore: 90, effect: NaN, lci: NaN, uci: NaN, estimandType: 'RD' }
                    ],

                    rob: ['high', 'high', 'high', 'low', 'low'],

                    snippet: 'Source: Ozelo MC, Mahlangu J, Pasi KJ, et al. Valoctocogene Roxaparvovec Gene Therapy for Hemophilia A (GENEr8-1). NEJM 2022;386:1013-1025. PMID 35294811. DOI 10.1056/NEJMoa2113708. NOTE: Open-label single-arm pre-vs-post (RoB blinding HIGH; allocation N/A). Comparator is historical control within-participant.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa2113708',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT03392974'
                },

                'NCT03569891': {

                    name: 'HOPE-B (Pipe 2023)', pmid: '36812434', phase: 'III', year: 2023, tE: 54, tN: 54, cE: 45, cN: 52, group: 'Pipe SW, Leebeek FWG, Recht M, et al; HOPE-B Investigators. NEJM 2023;388:706-718 (PMID 36812434). uniQure/CSL Behring-sponsored multinational open-label single-arm phase 3 trial of etranacogene dezaparvovec (Hemgenix) AAV5-FIX-Padua gene therapy in n=54 men with severe-to-moderately-severe hemophilia B (FIX <=2 IU/dL) on prophylactic FIX concentrate, prior bleeding rate >=4/year. Single 2×10^13 gc/kg IV infusion. PRIMARY (within-participant): change in mean ABR from 6-month lead-in baseline (FIX prophylaxis) to months 7-18 post-infusion. RESULT: ABR baseline 4.19 vs post-infusion 1.51 — RR 0.36 (95% CI 0.20-0.64; P<0.001); FIX activity rose to mean 39 IU/dL by month 18 (vs 0-2 IU/dL baseline). Drove FDA 2022 (PRV approval) + EMA 2023 approval of etranacogene — first hemophilia B gene therapy at $3.5M list price. NCT03569891 includes participants with detectable AAV5 neutralizing antibodies (53/54 — practical for real-world).',

                    estimandType: 'RR', publishedHR: 0.36, hrLCI: 0.20, hrUCI: 0.64, pubHR: 0.36,

                    allOutcomes: [
                        { shortLabel: 'ABR_REDUCTION', title: 'ABR change post-vs-pre prophylaxis (etranacogene)', tE: 1.51, cE: 4.19, type: 'PRIMARY', matchScore: 100, effect: 0.36, lci: 0.20, uci: 0.64, estimandType: 'RR' },
                        { shortLabel: 'FIX_RISE', title: 'Mean FIX activity at month 18 (IU/dL)', tE: 39, cE: 1, type: 'SECONDARY', matchScore: 90, effect: NaN, lci: NaN, uci: NaN, estimandType: 'MD' }
                    ],

                    rob: ['high', 'high', 'high', 'low', 'low'],

                    snippet: 'Source: Pipe SW, Leebeek FWG, Recht M, et al. Gene Therapy with Etranacogene Dezaparvovec for Hemophilia B (HOPE-B). NEJM 2023;388:706-718. PMID 36812434. DOI 10.1056/NEJMoa2211644. NOTE: Open-label single-arm pre-vs-post (RoB blinding HIGH).',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa2211644',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT03569891'
                },

                'NCT04370054': {

                    name: 'AFFINE (giroctocogene fitelparvovec, 2024)', pmid: '39504078', phase: 'III', year: 2024, tE: 84, tN: 84, cE: 60, cN: 73, group: 'Pfizer-sponsored multinational open-label single-arm phase 3 trial of giroctocogene fitelparvovec (PF-07055480, AAV6-FVIII) gene therapy in n=84 adult men with severe hemophilia A (FVIII <=1 IU/dL) on prophylactic FVIII concentrate. Single 3×10^13 vg/kg IV infusion. PRIMARY: change in ABR (post-vs-pre prophylactic baseline). RESULT (12-month interim, ASH 2023 + Lancet 2024 PMID 39504078): mean ABR 0.6 post-infusion vs 4.7 pre (RR 0.13, 95% CI 0.06-0.27); 84% achieved zero treated bleeds at 1 year; mean FVIII activity 22.1 IU/dL by week 15 declining to 11.2 IU/dL by week 78. Differs from GENEr8-1 in (a) AAV6 vs AAV5 capsid, (b) lower vg/kg dose, (c) more durable expression. Drove regulatory submission to FDA + EMA 2024.',

                    estimandType: 'RR', publishedHR: 0.13, hrLCI: 0.06, hrUCI: 0.27, pubHR: 0.13,

                    allOutcomes: [
                        { shortLabel: 'ABR_REDUCTION', title: 'ABR change post-vs-pre prophylaxis (giroctocogene)', tE: 0.6, cE: 4.7, type: 'PRIMARY', matchScore: 100, effect: 0.13, lci: 0.06, uci: 0.27, estimandType: 'RR' },
                        { shortLabel: 'ZERO_BLEED', title: 'Zero treated bleeds at 1y', tE: 71, cE: 0, type: 'SECONDARY', matchScore: 90, effect: NaN, lci: NaN, uci: NaN, estimandType: 'RD' }
                    ],

                    rob: ['high', 'high', 'high', 'low', 'low'],

                    snippet: 'Source: Mahlangu J, Pipe SW, Recht M, et al. Giroctocogene fitelparvovec gene therapy in moderately severe to severe hemophilia A: 12-month interim results from the AFFINE phase 3 trial. Lancet 2024 (Nov). PMID 39504078. DOI 10.1016/S0140-6736(24)02143-X. NOTE: Open-label single-arm.',

                    sourceUrl: 'https://doi.org/10.1016/S0140-6736(24)02143-X',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT04370054'
                }
            }"""


# ==========================
# TOPIC 47: Diabetic retinopathy NMA
# ==========================
DR_BODY = """

                'NCT01489189': {

                    name: 'Protocol S DRCR (Gross 2015)', pmid: '26565927', phase: 'III', year: 2015, tE: 6, tN: 191, cE: 8, cN: 203, group: 'Gross JG, Glassman AR, Jampol LM, et al; DRCR Network. JAMA 2015;314:2137-2146 (PMID 26565927). NIH-NEI-funded DRCR Retina Network multicenter randomized comparative-effectiveness trial in n=394 adults (305 patients with 394 eyes) with proliferative diabetic retinopathy (PDR) at 55 US sites. Randomized 1:1 to (A) intravitreal ranibizumab 0.5 mg as needed PRN (n=191 eyes) vs (B) panretinal photocoagulation (PRP) (n=203 eyes), each given for 2 years. PRIMARY: 2-year mean change in BCVA letter score, non-inferiority margin -5 letters. RESULT: ranibizumab +2.8 letters vs PRP +0.2 letters — difference +2.2 letters (95% CI -0.5 to +5.0) — NON-INFERIOR. Severe vision-threatening DME requiring vitrectomy 6/191 (3.1%) ranibizumab vs 8/203 (3.9%) PRP. KEY: ranibizumab equally effective for PDR with FEWER peripheral visual field loss + fewer adverse vitrectomy events. Drove AAO PPP-2017 and ICO 2017 update accepting anti-VEGF as alternative to PRP. 5-year extension Sun 2018 confirmed durability. Africa relevance: indirect (US-only); Protocol S is the global comparator for any African PDR-treatment NMA.',

                    estimandType: 'MD', publishedHR: 2.2, hrLCI: -0.5, hrUCI: 5.0, pubHR: 2.2,

                    allOutcomes: [
                        { shortLabel: 'BCVA_2Y', title: '2-year BCVA letter change (ranibizumab vs PRP)', tE: 2.8, cE: 0.2, type: 'PRIMARY', matchScore: 100, effect: 2.6, lci: 0.1, uci: 5.1, estimandType: 'MD' },
                        { shortLabel: 'VITRECT', title: 'Vitrectomy for severe vision-threatening DME', tE: 6, cE: 8, type: 'SAFETY', matchScore: 90, effect: 0.80, lci: 0.28, uci: 2.27, estimandType: 'RR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Gross JG, Glassman AR, Jampol LM, et al. Panretinal Photocoagulation vs Intravitreous Ranibizumab for Proliferative Diabetic Retinopathy: A Randomized Clinical Trial (DRCR Protocol S). JAMA 2015;314:2137-2146. PMID 26565927. DOI 10.1001/jama.2015.15217. NOTE: Open-label among 2 active arms (RoB blinding HIGH); central reading center.',

                    sourceUrl: 'https://doi.org/10.1001/jama.2015.15217',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT01489189'
                },

                'NCT02718326': {

                    name: 'PANORAMA (Brown 2021)', pmid: '33890860', phase: 'III', year: 2021, tE: 79, tN: 269, cE: 16, cN: 133, group: 'Brown DM, Wykoff CC, Boyer D, et al; PANORAMA Investigators. Ophthalmology 2021;128:1573-1583 (PMID 33890860). Regeneron/Bayer-sponsored multinational double-blind randomized phase 3 trial in n=402 adults with moderately severe to severe NPDR (DR Severity Scale 47-53) WITHOUT DME, across 87 US/Europe/Asia sites. Randomized 1:1:1 to (A) aflibercept 2mg q16w (after 5 monthly + 1 8-week loading) (n=135), (B) aflibercept 2mg q8-16w PRN (n=134), (C) sham (n=133). PRIMARY: proportion improving >=2 steps on DRSS at week 52. RESULT (combined aflibercept arms vs sham at week 100): 79/269 (29.4%) >=2-step improvement vs 16/133 (12.0%) sham — RR 2.44 (95% CI 1.49-4.01); proliferative DR development 3.0% aflibercept vs 19.5% sham (RR 0.15). Drove FDA 2019 + EMA 2020 approval of aflibercept for non-proliferative DR.',

                    estimandType: 'RR', publishedHR: 2.44, hrLCI: 1.49, hrUCI: 4.01, pubHR: 2.44,

                    allOutcomes: [
                        { shortLabel: 'DRSS_2STEP', title: '>=2-step DRSS improvement at wk100 (aflibercept vs sham)', tE: 79, cE: 16, type: 'PRIMARY', matchScore: 100, effect: 2.44, lci: 1.49, uci: 4.01, estimandType: 'RR' },
                        { shortLabel: 'PDR_DEV', title: 'Proliferative DR development at wk100', tE: 8, cE: 26, type: 'SAFETY', matchScore: 90, effect: 0.15, lci: 0.07, uci: 0.34, estimandType: 'RR' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Brown DM, Wykoff CC, Boyer D, et al. Evaluation of Intravitreal Aflibercept for the Treatment of Severe Nonproliferative Diabetic Retinopathy: Results From the PANORAMA Randomized Clinical Trial. Ophthalmology 2021;128:1573-1583. PMID 33890860. DOI 10.1016/j.ophtha.2021.04.024.',

                    sourceUrl: 'https://doi.org/10.1016/j.ophtha.2021.04.024',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT02718326'
                },

                'NCT02634333': {

                    name: 'Protocol W DRCR (Maturi 2021)', pmid: '34727134', phase: 'III', year: 2021, tE: 41, tN: 200, cE: 75, cN: 199, group: 'Maturi RK, Glassman AR, Josic K, et al; DRCR Retina Network. JAMA 2021;326:1880-1888 (PMID 34727134). NIH-NEI-funded DRCR multicenter randomized clinical trial in n=399 adults (328 patients) with moderate to severe NPDR (DRSS 43-53) WITHOUT center-involved DME, across 64 US sites. Randomized 1:1 by-eye to (A) intravitreal aflibercept 2 mg q16w after loading (n=200 eyes) vs (B) sham injection (n=199 eyes), for 4 years. PRIMARY: development of vision-threatening complications (CI-DME with vision loss OR PDR) by 4 years. RESULT: 41/200 (20.5%) aflibercept vs 75/199 (37.7%) sham — RR 0.54 (95% CI 0.39-0.75; P<0.001); ABSOLUTE risk reduction 17.2pp; NNT = 6 over 4 years. PRIMARY visual function preserved similarly between arms (mean BCVA decline -1.3 vs -2.4 letters, NS). FINDING: aflibercept REDUCES vision-threatening complications but does NOT improve mean visual acuity at 4 years — favours treatment in eyes at higher risk. Drove ICO 2024 + AAO 2024 PDR-prevention guideline updates.',

                    estimandType: 'RR', publishedHR: 0.54, hrLCI: 0.39, hrUCI: 0.75, pubHR: 0.54,

                    allOutcomes: [
                        { shortLabel: 'COMP_4Y', title: 'CI-DME with vision loss OR PDR by 4y (aflibercept vs sham)', tE: 41, cE: 75, type: 'PRIMARY', matchScore: 100, effect: 0.54, lci: 0.39, uci: 0.75, estimandType: 'RR' },
                        { shortLabel: 'BCVA_4Y', title: '4-year BCVA letter change (NS)', tE: -1.3, cE: -2.4, type: 'SECONDARY', matchScore: 90, effect: 1.1, lci: -1.5, uci: 3.7, estimandType: 'MD' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Maturi RK, Glassman AR, Josic K, et al. Effect of Intravitreous Anti-Vascular Endothelial Growth Factor vs Sham Treatment for Prevention of Vision-Threatening Complications of Diabetic Retinopathy: The Protocol W Randomized Clinical Trial (DRCR Network). JAMA 2021;326:1880-1888. PMID 34727134. DOI 10.1001/jama.2021.20488.',

                    sourceUrl: 'https://doi.org/10.1001/jama.2021.20488',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT02634333'
                }
            }"""


# ==========================
# Build all 3 files
# ==========================
TEMPLATE = Path("SGLT2I_HF_NMA_REVIEW.html")

CONFIGS = [
    {
        "out": "VITILIGO_NMA_REVIEW.html",
        "title": "RapidMeta Dermatology | Vitiligo NMA &mdash; TRuE-V1 + TRuE-V2 + UpA-Vitiligo v0.1",
        "auto_include": "['NCT04052425', 'NCT04057573', 'NCT04927975']",
        "acronyms": "'NCT04052425': 'TRuE-V1', 'NCT04057573': 'TRuE-V2', 'NCT04927975': 'UpA-Vitiligo'",
        "body": VIT_BODY,
    },
    {
        "out": "HEMOPHILIA_GENE_THERAPY_NMA_REVIEW.html",
        "title": "RapidMeta Hematology | Hemophilia Gene Therapy NMA &mdash; GENEr8-1 + HOPE-B + AFFINE v0.1",
        "auto_include": "['NCT03392974', 'NCT03569891', 'NCT04370054']",
        "acronyms": "'NCT03392974': 'GENEr8-1', 'NCT03569891': 'HOPE-B', 'NCT04370054': 'AFFINE'",
        "body": HEMO_BODY,
    },
    {
        "out": "DIABETIC_RETINOPATHY_NMA_REVIEW.html",
        "title": "RapidMeta Ophthalmology | Diabetic Retinopathy NMA &mdash; Protocol S + PANORAMA + Protocol W v0.1",
        "auto_include": "['NCT01489189', 'NCT02718326', 'NCT02634333']",
        "acronyms": "'NCT01489189': 'Protocol S DRCR', 'NCT02718326': 'PANORAMA', 'NCT02634333': 'Protocol W DRCR'",
        "body": DR_BODY,
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
