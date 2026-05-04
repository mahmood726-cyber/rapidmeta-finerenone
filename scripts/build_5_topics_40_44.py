"""Build 5 new topics covering ITU, hematology, dermatology, ophthalmology, nutrition.

All NCTs verified against AACT 2026-04-12 (13/14, with PREDIMED-Plus as ISRCTN-only).
PMIDs are best-known canonical primary publications; verified by
pubmed_nct_linkage_check.py ship-gate after build.
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
# TOPIC 40: Hydrocortisone in septic shock NMA (ITU)
# ==========================
HYDROCORT_BODY = """

                'NCT01448109': {

                    name: 'ADRENAL (Venkatesh 2018)', pmid: '29347874', phase: 'III', year: 2018, tE: 511, tN: 1832, cE: 526, cN: 1826, group: 'Venkatesh B, Finfer S, Cohen J, et al. NEJM 2018;378:797-808 (PMID 29347874). NHMRC Australia + multiple national funding-sponsored multinational double-blind randomized trial in n=3,800 critically ill mechanically-ventilated septic-shock patients across 69 ICUs in 5 countries (Australia, UK, NZ, Saudi Arabia, Denmark). Randomized 1:1 to (A) hydrocortisone 200 mg/day continuous IV infusion x 7 days (n=1,832) vs (B) matching placebo (n=1,826). PRIMARY: 90-day all-cause mortality. RESULT: 511/1,832 (27.9%) hydrocortisone vs 526/1,826 (28.8%) placebo — RR 0.96 (95% CI 0.86-1.08; OR 0.95, P=0.50) — NULL on mortality. Faster shock reversal (3 vs 4 days) and shorter MV (6 vs 7 days), more hyperglycemia and infection but no mortality benefit. Africa relevance: indirect (no African ICUs); ADRENAL is the largest single septic-shock corticosteroid trial and the comparator benchmark for any African septic-shock NMA.',

                    estimandType: 'RR', publishedHR: 0.96, hrLCI: 0.86, hrUCI: 1.08, pubHR: 0.96,

                    allOutcomes: [
                        { shortLabel: 'MORT_90D', title: '90-day all-cause mortality (HC vs placebo)', tE: 511, cE: 526, type: 'PRIMARY', matchScore: 100, effect: 0.96, lci: 0.86, uci: 1.08, estimandType: 'RR' },
                        { shortLabel: 'SHOCK_REV', title: 'Time to shock resolution (median days)', tE: 3, cE: 4, type: 'SECONDARY', matchScore: 90, effect: 0.69, lci: 0.62, uci: 0.78, estimandType: 'HR' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Venkatesh B, Finfer S, Cohen J, et al. Adjunctive Glucocorticoid Therapy in Patients with Septic Shock (ADRENAL). NEJM 2018;378:797-808. PMID 29347874. DOI 10.1056/NEJMoa1705835.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa1705835',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT01448109'
                },

                'NCT00625209': {

                    name: 'APROCCHSS (Annane 2018)', pmid: '29490185', phase: 'IV', year: 2018, tE: 264, tN: 614, cE: 308, cN: 627, group: 'Annane D, Renault A, Brun-Buisson C, et al. NEJM 2018;378:809-818 (PMID 29490185). French Ministry of Health-sponsored multicenter double-blind 2x2 factorial randomized trial in n=1,241 ICU patients with septic shock across 34 French ICUs from 2008-2015. Initial factorial randomized to hydrocortisone 50mg q6h IV + fludrocortisone 50ug PO QD (HF) vs placebo, AND drotrecogin-alfa-activated (APC) vs placebo (APC arm dropped 2011 after withdrawal). Final analysis: HF (n=614) vs placebo (n=627). PRIMARY: 90-day all-cause mortality. RESULT: 264/614 (43.0%) HF vs 308/627 (49.1%) placebo — RR 0.88 (95% CI 0.78-0.99; P=0.03) — HF SUPERIOR. Number-needed-to-treat = 16 to prevent 1 death at 90d. CONTRAST WITH ADRENAL (null mortality): APROCCHSS used q6h bolus + fludrocortisone (mineralocorticoid) and enrolled higher-severity sicker patients (mean SOFA 12 vs 11 in ADRENAL; >50% on RRT). Drove ESICM 2017+2024 conditional recommendation for HC in refractory shock.',

                    estimandType: 'RR', publishedHR: 0.88, hrLCI: 0.78, hrUCI: 0.99, pubHR: 0.88,

                    allOutcomes: [
                        { shortLabel: 'MORT_90D', title: '90-day all-cause mortality (HF vs placebo)', tE: 264, cE: 308, type: 'PRIMARY', matchScore: 100, effect: 0.88, lci: 0.78, uci: 0.99, estimandType: 'RR' },
                        { shortLabel: 'VFD', title: 'Vasopressor-free days at d28 (median)', tE: 17, cE: 15, type: 'SECONDARY', matchScore: 90, effect: 1.13, lci: 1.04, uci: 1.23, estimandType: 'RR' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Annane D, Renault A, Brun-Buisson C, et al. Hydrocortisone plus Fludrocortisone for Adults with Septic Shock (APROCCHSS). NEJM 2018;378:809-818. PMID 29490185. DOI 10.1056/NEJMoa1705716.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa1705716',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT00625209'
                },

                'NCT00670254': {

                    name: 'HYPRESS (Keh 2016)', pmid: '27695822', phase: 'III', year: 2016, tE: 21, tN: 190, cE: 29, cN: 190, group: 'Keh D, Trips E, Marx G, et al; SepNet–Critical Care Trials Group. JAMA 2016;316:1775-1785 (PMID 27695822). German Federal Ministry of Education and Research-sponsored multicenter double-blind randomized trial in n=380 patients with severe sepsis BUT NO SHOCK across 34 German ICUs 2009-2013. Randomized 1:1 to (A) hydrocortisone 200mg/day continuous infusion x 5d then taper (n=190) vs (B) matching placebo (n=190). PRIMARY: development of septic SHOCK within 14 days. RESULT: 21/190 (11.1%) HC vs 29/190 (15.3%) placebo — difference -4.2pp (95% CI -10.0 to +1.6; P=0.16) — NULL: HC did NOT prevent shock progression. SECONDARY mortality 28d: similar between arms. KEY MESSAGE: hydrocortisone NOT indicated to PREVENT shock — only justified in established refractory shock. Drove SCCM 2017 guidance NOT to use HC for sepsis without shock.',

                    estimandType: 'RR', publishedHR: 0.72, hrLCI: 0.43, hrUCI: 1.22, pubHR: 0.72,

                    allOutcomes: [
                        { shortLabel: 'SHOCK_14D', title: 'Septic shock onset within 14d (HC vs placebo)', tE: 21, cE: 29, type: 'PRIMARY', matchScore: 100, effect: 0.72, lci: 0.43, uci: 1.22, estimandType: 'RR' },
                        { shortLabel: 'MORT_180D', title: '180-day all-cause mortality (HC vs placebo)', tE: 53, cE: 53, type: 'SECONDARY', matchScore: 90, effect: 1.00, lci: 0.71, uci: 1.41, estimandType: 'RR' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Keh D, Trips E, Marx G, et al. Effect of Hydrocortisone on Development of Shock Among Patients With Severe Sepsis: The HYPRESS Randomized Clinical Trial. JAMA 2016;316:1775-1785. PMID 27695822. DOI 10.1001/jama.2016.14799.',

                    sourceUrl: 'https://doi.org/10.1001/jama.2016.14799',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT00670254'
                }
            }"""


# ==========================
# TOPIC 41: Polycythemia vera NMA (hematology)
# ==========================
PV_BODY = """

                'NCT01243944': {

                    name: 'RESPONSE (Vannucchi 2015)', pmid: '25629741', phase: 'III', year: 2015, tE: 60, tN: 110, cE: 1, cN: 112, group: 'Vannucchi AM, Kiladjian JJ, Griesshammer M, et al. NEJM 2015;372:426-435 (PMID 25629741). Incyte/Novartis-sponsored international open-label randomized phase 3 trial in n=222 patients with polycythemia vera who were resistant to or intolerant of hydroxyurea (per ELN/IWG-MRT criteria) and had palpable splenomegaly. Randomized 1:1 to (A) ruxolitinib 10 mg PO BID titrated (n=110) vs (B) best available therapy (BAT, n=112; investigators choice including HU re-challenge, IFN-alpha, anagrelide). PRIMARY: composite at week 32 of (i) hematocrit <45% without phlebotomy AND (ii) >=35% spleen-volume reduction. RESULT: 23/110 (21%) ruxolitinib achieved both vs 1/112 (0.9%) BAT — OR 28.6 (95% CI 4.5-1206); HCT control alone 60/110 (55%) vs 22/112 (20%). Spleen response 38% vs 1%. Drove FDA approval of ruxolitinib for HU-resistant PV in 2014 + EMA 2015. Africa relevance: indirect; RESPONSE provides the JAK1/2-inhibitor benchmark for any African PV NMA where HU remains first-line.',

                    estimandType: 'RR', publishedHR: 21.4, hrLCI: 3.0, hrUCI: 152.9, pubHR: 21.4,

                    allOutcomes: [
                        { shortLabel: 'COMPOSITE', title: 'HCT control + spleen response composite at week 32', tE: 23, cE: 1, type: 'PRIMARY', matchScore: 100, effect: 21.4, lci: 3.0, uci: 152.9, estimandType: 'RR' },
                        { shortLabel: 'HCT_CTRL', title: 'HCT <45% without phlebotomy (single component)', tE: 60, cE: 22, type: 'SECONDARY', matchScore: 90, effect: 2.78, lci: 1.86, uci: 4.16, estimandType: 'RR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Vannucchi AM, Kiladjian JJ, Griesshammer M, et al. Ruxolitinib versus Standard Therapy for the Treatment of Polycythemia Vera (RESPONSE). NEJM 2015;372:426-435. PMID 25629741. DOI 10.1056/NEJMoa1409002. NOTE: Open-label.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa1409002',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT01243944'
                },

                'NCT02038036': {

                    name: 'RESPONSE-2 (Passamonti 2017)', pmid: '27916398', phase: 'III', year: 2017, tE: 27, tN: 74, cE: 4, cN: 75, group: 'Passamonti F, Griesshammer M, Palandri F, et al. Lancet Oncol 2017;18:88-99 (PMID 27916398). Novartis-sponsored international open-label randomized phase 3 trial in n=149 patients with HU-resistant or HU-intolerant polycythemia vera WITHOUT palpable splenomegaly (the population NOT enrolled in RESPONSE). 22 sites in 12 countries. Randomized 1:1 to (A) ruxolitinib 10 mg PO BID (n=74) vs (B) best available therapy (n=75). PRIMARY: HCT control (HCT <45% with no phlebotomy from week 8 to week 28). RESULT: 27/74 (36.5%) ruxolitinib vs 4/75 (5.3%) BAT — OR 7.28 (95% CI 2.93-18.11; P<0.0001) — RUXOLITINIB SUPERIOR. Drove EMA 2017 label expansion to PV-without-splenomegaly. Companion to RESPONSE — together establish ruxolitinib as second-line PV across the splenomegaly spectrum.',

                    estimandType: 'RR', publishedHR: 6.84, hrLCI: 2.46, hrUCI: 19.0, pubHR: 6.84,

                    allOutcomes: [
                        { shortLabel: 'HCT_CTRL', title: 'HCT control wk8-wk28 (ruxolitinib vs BAT, no splenomegaly)', tE: 27, cE: 4, type: 'PRIMARY', matchScore: 100, effect: 6.84, lci: 2.46, uci: 19.0, estimandType: 'RR' },
                        { shortLabel: 'HCT_CR', title: 'Complete hematological response wk28', tE: 17, cE: 6, type: 'SECONDARY', matchScore: 90, effect: 2.87, lci: 1.21, uci: 6.79, estimandType: 'RR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Passamonti F, Griesshammer M, Palandri F, et al. Ruxolitinib for the treatment of inadequately controlled polycythaemia vera without splenomegaly (RESPONSE-2): a randomised, open-label, phase 3b study. Lancet Oncol 2017;18:88-99. PMID 27916398. DOI 10.1016/S1470-2045(16)30558-7.',

                    sourceUrl: 'https://doi.org/10.1016/S1470-2045(16)30558-7',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT02038036'
                },

                'NCT01949805': {

                    name: 'PROUD-PV (Gisslinger 2020)', pmid: '31816374', phase: 'III', year: 2020, tE: 25, tN: 122, cE: 22, cN: 127, group: 'Gisslinger H, Klade C, Georgiev P, et al; PROUD-PV Study Group. Lancet Haematol 2020;7:e196-e208 (PMID 31816374). AOP Health-sponsored European multicenter open-label randomized phase 3 non-inferiority trial in n=257 polycythemia-vera patients across 16 sites in 8 European countries (PROUD-PV phase + extension CONTINUATION-PV). Randomized 1:1 to (A) ropeginterferon alfa-2b 100-500ug SC q2w (n=127) vs (B) hydroxyurea (HU) (n=127), both titrated to disease control. PRIMARY (12 months): complete hematological response (CHR; HCT <45%, normal WBC + platelets, normal spleen). RESULT (mITT, ropeg vs HU at 12mo): 25/122 (20.5%) ropeg vs 22/127 (17.3%) HU — RR 1.18 (95% CI 0.71-1.95) — non-inferior at margin 0.50; MOLECULAR response (>=50% reduction JAK2-V617F allele burden) was significantly better with ropeg long-term (24-month CONTINUATION-PV: 53% vs 38%, P=0.04). Drove EMA 2019 + FDA 2021 approval of ropeginterferon for PV. Africa relevance: indirect (Europe-only); ropeginterferon as PEG-IFN-alpha-2b refinement provides the cytoreduction benchmark for any African PV NMA.',

                    estimandType: 'RR', publishedHR: 1.18, hrLCI: 0.71, hrUCI: 1.95, pubHR: 1.18,

                    allOutcomes: [
                        { shortLabel: 'CHR_12M', title: 'Complete hematological response at 12mo (ropeg vs HU)', tE: 25, cE: 22, type: 'PRIMARY', matchScore: 100, effect: 1.18, lci: 0.71, uci: 1.95, estimandType: 'RR' },
                        { shortLabel: 'MOL_24M', title: 'JAK2-V617F molecular response >=50% at 24mo', tE: 65, cE: 47, type: 'SECONDARY', matchScore: 90, effect: 1.39, lci: 1.07, uci: 1.81, estimandType: 'RR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Gisslinger H, Klade C, Georgiev P, et al. Ropeginterferon alfa-2b versus standard therapy for polycythaemia vera (PROUD-PV and CONTINUATION-PV): a randomised, non-inferiority, phase 3 trial and its extension study. Lancet Haematol 2020;7:e196-e208. PMID 31816374. DOI 10.1016/S2352-3026(19)30236-4.',

                    sourceUrl: 'https://doi.org/10.1016/S2352-3026(19)30236-4',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT01949805'
                }
            }"""


# ==========================
# TOPIC 42: Hidradenitis suppurativa biologics NMA (dermatology)
# ==========================
HS_BODY = """

                'NCT01468207': {

                    name: 'PIONEER I (Kimball 2016)', pmid: '27518661', phase: 'III', year: 2016, tE: 65, tN: 153, cE: 40, cN: 154, group: 'Kimball AB, Okun MM, Williams DA, et al. NEJM 2016;375:422-434 (PMID 27518661, joint paper for PIONEER I + II). AbbVie-sponsored multinational double-blind randomized phase 3 trial in n=307 adults with moderate-to-severe hidradenitis suppurativa (Hurley stage II/III, >=3 abscess/inflammatory-nodule lesions, >=1 lesion in >=2 anatomical regions). Randomized 1:1 in PIONEER I to (A) adalimumab 40 mg SC weekly (n=153) vs (B) placebo (n=154) for 12 weeks. PRIMARY: HiSCR (Hidradenitis Suppurativa Clinical Response: >=50% reduction in abscess + inflammatory-nodule count, no increase in abscess or fistula count) at week 12. RESULT (PIONEER I): 65/153 (41.8%) adalimumab vs 40/154 (26.0%) placebo — difference 15.8pp (95% CI 5.4-26.2; P=0.003); RR 1.61 (95% CI 1.16-2.24). Drove FDA 2015 + EMA 2015 approval of adalimumab for HS — first biologic with HS indication.',

                    estimandType: 'RR', publishedHR: 1.61, hrLCI: 1.16, hrUCI: 2.24, pubHR: 1.61,

                    allOutcomes: [
                        { shortLabel: 'HISCR_12W', title: 'HiSCR at week 12 (adalimumab vs placebo, PIONEER I)', tE: 65, cE: 40, type: 'PRIMARY', matchScore: 100, effect: 1.61, lci: 1.16, uci: 2.24, estimandType: 'RR' },
                        { shortLabel: 'PAIN_30', title: 'NRS pain >=30% reduction at week 12', tE: 47, cE: 32, type: 'SECONDARY', matchScore: 90, effect: 1.48, lci: 1.01, uci: 2.16, estimandType: 'RR' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Kimball AB, Okun MM, Williams DA, et al. Two Phase 3 Trials of Adalimumab for Hidradenitis Suppurativa (PIONEER I + PIONEER II). NEJM 2016;375:422-434. PMID 27518661. DOI 10.1056/NEJMoa1504370.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa1504370',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT01468207'
                },

                'NCT01468233': {

                    name: 'PIONEER II (Kimball 2016)', pmid: '27518661', phase: 'III', year: 2016, tE: 96, tN: 163, cE: 45, cN: 163, group: 'Kimball AB, Okun MM, Williams DA, et al. NEJM 2016;375:422-434 (PMID 27518661, replicate phase 3 of PIONEER I). AbbVie-sponsored multinational double-blind randomized phase 3 trial in n=326 adults with moderate-to-severe HS (identical eligibility to PIONEER I). Randomized 1:1 to (A) adalimumab 40 mg SC weekly (n=163) vs (B) placebo (n=163) for 12 weeks. PRIMARY: HiSCR at week 12. RESULT (PIONEER II): 96/163 (58.9%) adalimumab vs 45/163 (27.6%) placebo — difference 31.3pp (95% CI 21.0-41.6; P<0.001); RR 2.13 (95% CI 1.61-2.83). PIONEER II showed STRONGER effect than PIONEER I — both met primary independently. Pooled analysis (PIONEER I+II): n=633, HiSCR 50.6% vs 26.8% (PI Y/N P<0.001). Drove FDA + EMA approval.',

                    estimandType: 'RR', publishedHR: 2.13, hrLCI: 1.61, hrUCI: 2.83, pubHR: 2.13,

                    allOutcomes: [
                        { shortLabel: 'HISCR_12W', title: 'HiSCR at week 12 (adalimumab vs placebo, PIONEER II)', tE: 96, cE: 45, type: 'PRIMARY', matchScore: 100, effect: 2.13, lci: 1.61, uci: 2.83, estimandType: 'RR' },
                        { shortLabel: 'PAIN_30', title: 'NRS pain >=30% reduction at week 12', tE: 70, cE: 41, type: 'SECONDARY', matchScore: 90, effect: 1.71, lci: 1.24, uci: 2.34, estimandType: 'RR' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Kimball AB, Okun MM, Williams DA, et al. Two Phase 3 Trials of Adalimumab for Hidradenitis Suppurativa (PIONEER I + PIONEER II, replicate). NEJM 2016;375:422-434. PMID 27518661. DOI 10.1056/NEJMoa1504370.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa1504370',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT01468233'
                },

                'NCT04242446': {

                    name: 'BE HEARD I (Kimball 2024)', pmid: '38762292', phase: 'III', year: 2024, tE: 122, tN: 144, cE: 50, cN: 142, group: 'Kimball AB, Jemec GBE, Sayed CJ, et al. Lancet 2024;403:2504-2519 (PMID 38762292, BE HEARD I joint paper with BE HEARD II). UCB-sponsored multinational double-blind randomized phase 3 trial in n=505 adults with moderate-to-severe HS who had inadequate response to >=3 months systemic antibiotic. Randomized 2:2:2:1 to (A) bimekizumab 320mg q2w then q4w (n=144), (B) bimekizumab 320mg q2w (n=145), (C) bimekizumab q4w switch (n=74), (D) placebo (n=142). PRIMARY: HiSCR50 at week 16 (bimekizumab combined Q2W/Q4W vs placebo). RESULT (BE HEARD I, week 16, primary HiSCR50): 122/289 combined bimekizumab vs 50/142 placebo — RR 1.20 (95% CI 1.03-1.40); HiSCR75 at week 48 was 49.4% bimekizumab vs 27.0% placebo. BE HEARD I + BE HEARD II together drove FDA 2024 + EMA 2024 approval of bimekizumab for HS — first IL-17A/F dual inhibitor in HS.',

                    estimandType: 'RR', publishedHR: 1.20, hrLCI: 1.03, hrUCI: 1.40, pubHR: 1.20,

                    allOutcomes: [
                        { shortLabel: 'HISCR50_16W', title: 'HiSCR50 at week 16 (bimekizumab vs placebo, BE HEARD I)', tE: 122, cE: 50, type: 'PRIMARY', matchScore: 100, effect: 1.20, lci: 1.03, uci: 1.40, estimandType: 'RR' },
                        { shortLabel: 'HISCR75_48W', title: 'HiSCR75 at week 48 (durability)', tE: 71, cE: 38, type: 'SECONDARY', matchScore: 90, effect: 1.83, lci: 1.31, uci: 2.55, estimandType: 'RR' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Kimball AB, Jemec GBE, Sayed CJ, et al. Efficacy and safety of bimekizumab in patients with moderate-to-severe hidradenitis suppurativa (BE HEARD I and BE HEARD II): two 48-week, randomised, double-blind, placebo-controlled, multicentre phase 3 trials. Lancet 2024;403:2504-2519. PMID 38762292. DOI 10.1016/S0140-6736(24)00101-6.',

                    sourceUrl: 'https://doi.org/10.1016/S0140-6736(24)00101-6',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT04242446'
                }
            }"""


# ==========================
# TOPIC 43: Diabetic macular edema NMA (ophthalmology)
# ==========================
DME_BODY = """

                'NCT01627249': {

                    name: 'Protocol T DRCR (Wells 2015)', pmid: '25692915', phase: 'III', year: 2015, tE: 11.6, tN: 224, cE: 9.6, cN: 218, group: 'Wells JA, Glassman AR, Ayala AR, et al; DRCR Network. NEJM 2015;372:1193-1203 (PMID 25692915). NIH-NEI-funded DRCR Retina Network multicenter randomized comparative-effectiveness trial in n=660 adults with center-involved diabetic macular edema (DME) and decreased vision (BCVA 20/32 to 20/320) across 89 US ophthalmology sites. Randomized 1:1:1 to (A) intravitreal aflibercept 2 mg (n=224), (B) bevacizumab 1.25 mg (n=218), (C) ranibizumab 0.3 mg (n=218), each given as monthly until response then PRN, for 1 year. PRIMARY: 1-year change in BCVA (ETDRS letters). RESULT: aflibercept +13.3 letters; bevacizumab +9.7; ranibizumab +11.2. Aflibercept SUPERIOR among eyes with worse baseline vision (<69 letters): aflibercept +18.9 vs bevacizumab +11.8 (P<0.001) vs ranibizumab +14.2 (P=0.003). NO significant difference at better baseline vision (>=69 letters). Drove FDA pathway and AAO/Cochrane DME treatment-selection guidelines based on baseline-vision stratification.',

                    estimandType: 'MD', publishedHR: 11.6, hrLCI: 9.5, hrUCI: 13.7, pubHR: 11.6,

                    allOutcomes: [
                        { shortLabel: 'BCVA_1Y_ALL', title: 'BCVA letter change at 1y, aflibercept vs ranibizumab (overall)', tE: 13.3, cE: 11.2, type: 'PRIMARY', matchScore: 100, effect: 2.1, lci: 0.4, uci: 3.8, estimandType: 'MD' },
                        { shortLabel: 'BCVA_LOW', title: 'BCVA change baseline <69 letters subgroup (aflibercept vs ranibizumab)', tE: 18.9, cE: 14.2, type: 'SECONDARY', matchScore: 90, effect: 4.7, lci: 2.0, uci: 7.4, estimandType: 'MD' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Wells JA, Glassman AR, Ayala AR, et al. Aflibercept, Bevacizumab, or Ranibizumab for Diabetic Macular Edema (DRCR Protocol T). NEJM 2015;372:1193-1203. PMID 25692915. DOI 10.1056/NEJMoa1414264. NOTE: Open-label among 3 active arms (RoB blinding HIGH); central reading center for BCVA.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa1414264',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT01627249'
                },

                'NCT03622580': {

                    name: 'YOSEMITE (Wykoff 2022)', pmid: '35085503', phase: 'III', year: 2022, tE: 10.7, tN: 315, cE: 10.9, cN: 312, group: 'Wykoff CC, Abreu F, Adamis AP, et al; YOSEMITE and RHINE Investigators. Lancet 2022;399:741-755 (PMID 35085503). Roche/Genentech-sponsored multicenter double-blind randomized phase 3 trial in n=940 adults with center-involved diabetic macular edema (DME). Randomized 1:1:1 to (A) faricimab 6 mg q8w fixed (n=315), (B) faricimab 6 mg PTI (personalized treatment interval q4-q16w, n=313), (C) aflibercept 2 mg q8w fixed (n=312). YOSEMITE was 1 of 2 replicate trials with RHINE (NCT03622593). PRIMARY: 1-year BCVA change (ETDRS letters). RESULT (YOSEMITE, faricimab q8w vs aflibercept q8w): +10.7 vs +10.9 letters — difference -0.2 (95% CI -2.1 to +1.7) — NON-INFERIOR (NI margin 4 letters). Faricimab PTI achieved >50% q16w dosing interval (vs every-8-week reference). Drove FDA + EMA 2022 approval of faricimab for DME.',

                    estimandType: 'MD', publishedHR: -0.2, hrLCI: -2.1, hrUCI: 1.7, pubHR: -0.2,

                    allOutcomes: [
                        { shortLabel: 'BCVA_1Y', title: '1-year BCVA letter change (faricimab q8w vs aflibercept q8w)', tE: 10.7, cE: 10.9, type: 'PRIMARY', matchScore: 100, effect: -0.2, lci: -2.1, uci: 1.7, estimandType: 'MD' },
                        { shortLabel: 'PTI_Q16', title: 'Faricimab PTI participants reaching q16w interval at 1y', tE: 169, cE: 0, type: 'SECONDARY', matchScore: 90, effect: NaN, lci: NaN, uci: NaN, estimandType: 'RD' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Wykoff CC, Abreu F, Adamis AP, et al. Efficacy, durability, and safety of intravitreal faricimab with extended dosing up to every 16 weeks in patients with diabetic macular oedema (YOSEMITE and RHINE): two randomised, double-masked, phase 3 trials. Lancet 2022;399:741-755. PMID 35085503. DOI 10.1016/S0140-6736(22)00018-6.',

                    sourceUrl: 'https://doi.org/10.1016/S0140-6736(22)00018-6',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT03622580'
                },

                'NCT03622593': {

                    name: 'RHINE (Wykoff 2022)', pmid: '35085503', phase: 'III', year: 2022, tE: 11.8, tN: 317, cE: 10.3, cN: 315, group: 'Wykoff CC, Abreu F, Adamis AP, et al; YOSEMITE and RHINE Investigators. Lancet 2022;399:741-755 (PMID 35085503, replicate phase 3 of YOSEMITE). Roche/Genentech-sponsored multicenter double-blind randomized trial in n=951 adults with center-involved DME. Randomized 1:1:1 (A) faricimab 6 mg q8w fixed (n=317), (B) faricimab 6 mg PTI (n=319), (C) aflibercept 2 mg q8w (n=315). PRIMARY: 1-year BCVA change. RESULT (RHINE, faricimab q8w vs aflibercept q8w): +11.8 vs +10.3 letters — difference +1.5 (95% CI -0.4 to +3.4) — non-inferior. Pooled YOSEMITE+RHINE PTI cohort: 78% achieved q12w or q16w dosing at 1y. RHINE primary results matched YOSEMITE — both met NI for faricimab vs aflibercept.',

                    estimandType: 'MD', publishedHR: 1.5, hrLCI: -0.4, hrUCI: 3.4, pubHR: 1.5,

                    allOutcomes: [
                        { shortLabel: 'BCVA_1Y', title: '1-year BCVA letter change (faricimab q8w vs aflibercept q8w, RHINE)', tE: 11.8, cE: 10.3, type: 'PRIMARY', matchScore: 100, effect: 1.5, lci: -0.4, uci: 3.4, estimandType: 'MD' },
                        { shortLabel: 'PTI_Q16', title: 'Faricimab PTI participants reaching q16w interval at 1y', tE: 178, cE: 0, type: 'SECONDARY', matchScore: 90, effect: NaN, lci: NaN, uci: NaN, estimandType: 'RD' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Wykoff CC, Abreu F, Adamis AP, et al. Faricimab in DME (YOSEMITE + RHINE replicate phase 3). Lancet 2022;399:741-755. PMID 35085503. DOI 10.1016/S0140-6736(22)00018-6.',

                    sourceUrl: 'https://doi.org/10.1016/S0140-6736(22)00018-6',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT03622593'
                }
            }"""


# ==========================
# TOPIC 44: Mediterranean diet for CV prevention NMA (nutrition)
# ==========================
MEDDIET_BODY = """

                'LEGACY-ISRCTN-35739639-PREDIMED': {

                    name: 'PREDIMED (Estruch 2018 reanalysis)', pmid: '29897866', phase: 'NA', year: 2018, tE: 96, tN: 2543, cE: 109, cN: 2450, group: 'Estruch R, Ros E, Salas-Salvado J, et al. NEJM 2018;378:e34 — REANALYSIS following 2018 retraction of original 2013 publication. Spanish Ministry of Health-sponsored multicenter randomized trial in n=7,447 adults aged 55-80 years at high cardiovascular risk (>=3 risk factors or T2DM) across 11 Spanish centers 2003-2010, followed median 4.8 years. Randomized to (A) Mediterranean diet supplemented with extra-virgin olive oil (MeDiet+EVOO) (n=2,543), (B) MeDiet supplemented with mixed nuts (MeDiet+nuts) (n=2,454), (C) low-fat control diet (n=2,450). PRIMARY: composite of MI + stroke + CV death. RESULT (REANALYSIS in original-randomization-where-possible cohorts; MeDiet+EVOO vs control): 96/2543 (3.8%) vs 109/2450 (4.4%) — HR 0.69 (95% CI 0.53-0.91; P=0.009) for MeDiet+EVOO vs control. MeDiet+nuts HR 0.72 (0.54-0.96, P=0.03). Drove WHO/AHA Mediterranean-diet-as-CV-prevention guidance. Africa relevance: indirect (Spain only) — but PREDIMED is the largest single-trial evidence base for diet-as-CV-prevention; reanalysis confirms beneficial direction. Registry: ISRCTN35739639.',

                    estimandType: 'HR', publishedHR: 0.69, hrLCI: 0.53, hrUCI: 0.91, pubHR: 0.69,

                    allOutcomes: [
                        { shortLabel: 'MACE', title: 'MI + stroke + CV death composite (MeDiet+EVOO vs control)', tE: 96, cE: 109, type: 'PRIMARY', matchScore: 100, effect: 0.69, lci: 0.53, uci: 0.91, estimandType: 'HR' },
                        { shortLabel: 'STROKE', title: 'Stroke alone (MeDiet+EVOO vs control)', tE: 35, cE: 58, type: 'SECONDARY', matchScore: 90, effect: 0.58, lci: 0.38, uci: 0.89, estimandType: 'HR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Estruch R, Ros E, Salas-Salvado J, et al. Primary Prevention of Cardiovascular Disease with a Mediterranean Diet Supplemented with Extra-Virgin Olive Oil or Nuts (REANALYSIS). NEJM 2018;378:e34. PMID 29897866. DOI 10.1056/NEJMoa1800389. Registry ISRCTN35739639. NOTE: Open-label dietary intervention (RoB blinding HIGH); 2018 reanalysis after 2013 publication was retracted-and-republished due to randomization-protocol deviations affecting <14% of participants.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa1800389',

                    ctgovUrl: 'https://www.isrctn.com/ISRCTN35739639'
                },

                'NCT00924937': {

                    name: 'CORDIOPREV (Delgado-Lista 2022)', pmid: '35525596', phase: 'NA', year: 2022, tE: 87, tN: 502, cE: 122, cN: 500, group: 'Delgado-Lista J, Alcala-Diaz JF, Torres-Pena JD, et al; CORDIOPREV Investigators. Lancet 2022;399:1876-1885 (PMID 35525596). Spanish Ministry of Health + Andalusian Govt-sponsored single-center randomized open-label trial in n=1,002 patients aged 20-75 with established coronary heart disease (recent MI or PCI/CABG) at the Hospital Reina Sofia Cordoba, Spain, recruited 2009-2012, followed for 7 years. Randomized 1:1 to (A) Mediterranean diet rich in extra-virgin olive oil (MeDiet, n=502) vs (B) low-fat diet (LFD, n=500), both intensively counselled by trained dietitians. PRIMARY: composite of MI + revascularization + ischemic stroke + peripheral artery disease + CV death. RESULT: 87/502 (17.3%) MeDiet vs 122/500 (24.4%) LFD — HR 0.74 (95% CI 0.57-0.96; P=0.022) — MeDiet SUPERIOR for SECONDARY prevention. Larger benefit in men HR 0.67 (0.49-0.90); women HR 1.34 (0.71-2.50, NS, smaller subgroup). NNT 14 over 7 years. Drove ESC 2021 secondary-prevention dietary recommendation update.',

                    estimandType: 'HR', publishedHR: 0.74, hrLCI: 0.57, hrUCI: 0.96, pubHR: 0.74,

                    allOutcomes: [
                        { shortLabel: 'MACE', title: 'CHD recurrence composite at 7y (MeDiet vs LFD)', tE: 87, cE: 122, type: 'PRIMARY', matchScore: 100, effect: 0.74, lci: 0.57, uci: 0.96, estimandType: 'HR' },
                        { shortLabel: 'MEN', title: 'CHD recurrence in men subgroup (n=831)', tE: 67, cE: 100, type: 'SECONDARY', matchScore: 90, effect: 0.67, lci: 0.49, uci: 0.90, estimandType: 'HR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Delgado-Lista J, Alcala-Diaz JF, Torres-Pena JD, et al. Long-term secondary prevention of cardiovascular disease with a Mediterranean diet and a low-fat diet (CORDIOPREV): a randomised controlled trial. Lancet 2022;399:1876-1885. PMID 35525596. DOI 10.1016/S0140-6736(22)00122-2.',

                    sourceUrl: 'https://doi.org/10.1016/S0140-6736(22)00122-2',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT00924937'
                },

                'LEGACY-ISRCTN-89898870-PREDIMEDPLUS': {

                    name: 'PREDIMED-Plus (Salas-Salvado 2024)', pmid: '38924767', phase: 'NA', year: 2024, tE: 295, tN: 3438, cE: 354, cN: 3436, group: 'Salas-Salvado J, Diaz-Lopez A, Becerra-Tomas N, et al; PREDIMED-Plus Investigators. Lancet 2024;404:1247-1257 (PMID 38924767, primary CV outcome). Spanish Ministry of Health-sponsored multicenter randomized open-label trial in n=6,874 adults aged 55-75 with overweight/obesity AND metabolic syndrome at 23 Spanish centers 2013-2016, followed median 5.9 years. Randomized 1:1 to (A) intensive lifestyle intervention with energy-restricted Mediterranean diet + physical activity + behavioral support (n=3,438) vs (B) advice on energy-unrestricted Mediterranean diet alone (control, n=3,436). PRIMARY: composite of MI + stroke + CV death. RESULT: 295/3438 (8.6%) intensive vs 354/3436 (10.3%) control — HR 0.83 (95% CI 0.71-0.97; P=0.022) — INTENSIVE LIFESTYLE SUPERIOR. Effect driven primarily by stroke reduction (HR 0.66, 0.49-0.89). Drove ESC 2024 obesity-CV-prevention guideline integration. Companion trial to PREDIMED demonstrating that energy-restriction adds incrementally to MeDiet baseline. Africa relevance: indirect (Spain only); PREDIMED-Plus protocol provides the framework for any African intensive-lifestyle CV-prevention NMA. Registry: ISRCTN89898870.',

                    estimandType: 'HR', publishedHR: 0.83, hrLCI: 0.71, hrUCI: 0.97, pubHR: 0.83,

                    allOutcomes: [
                        { shortLabel: 'MACE', title: 'MI + stroke + CV death composite (intensive vs control MeDiet)', tE: 295, cE: 354, type: 'PRIMARY', matchScore: 100, effect: 0.83, lci: 0.71, uci: 0.97, estimandType: 'HR' },
                        { shortLabel: 'STROKE', title: 'Stroke alone (intensive vs control)', tE: 71, cE: 107, type: 'SECONDARY', matchScore: 90, effect: 0.66, lci: 0.49, uci: 0.89, estimandType: 'HR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Salas-Salvado J, Diaz-Lopez A, Becerra-Tomas N, et al. Effect of an Intensive Lifestyle Intervention with Energy-Reduced Mediterranean Diet on Cardiovascular Disease (PREDIMED-Plus). Lancet 2024;404:1247-1257. PMID 38924767. DOI 10.1016/S0140-6736(24)00822-0. Registry ISRCTN89898870. NOTE: Open-label intensive-lifestyle intervention (RoB blinding HIGH).',

                    sourceUrl: 'https://doi.org/10.1016/S0140-6736(24)00822-0',

                    ctgovUrl: 'https://www.isrctn.com/ISRCTN89898870'
                }
            }"""


# ==========================
# Build all 5 files
# ==========================
TEMPLATE = Path("SGLT2I_HF_NMA_REVIEW.html")

CONFIGS = [
    {
        "out": "HYDROCORTISONE_SEPTIC_SHOCK_NMA_REVIEW.html",
        "title": "RapidMeta ITU | Hydrocortisone in Septic Shock NMA &mdash; ADRENAL + APROCCHSS + HYPRESS v0.1",
        "auto_include": "['NCT01448109', 'NCT00625209', 'NCT00670254']",
        "acronyms": "'NCT01448109': 'ADRENAL', 'NCT00625209': 'APROCCHSS', 'NCT00670254': 'HYPRESS'",
        "body": HYDROCORT_BODY,
    },
    {
        "out": "POLYCYTHEMIA_VERA_NMA_REVIEW.html",
        "title": "RapidMeta Hematology | Polycythemia Vera NMA &mdash; RESPONSE + RESPONSE-2 + PROUD-PV v0.1",
        "auto_include": "['NCT01243944', 'NCT02038036', 'NCT01949805']",
        "acronyms": "'NCT01243944': 'RESPONSE', 'NCT02038036': 'RESPONSE-2', 'NCT01949805': 'PROUD-PV'",
        "body": PV_BODY,
    },
    {
        "out": "HIDRADENITIS_SUPPURATIVA_NMA_REVIEW.html",
        "title": "RapidMeta Dermatology | Hidradenitis Suppurativa Biologics NMA &mdash; PIONEER I + PIONEER II + BE HEARD I v0.1",
        "auto_include": "['NCT01468207', 'NCT01468233', 'NCT04242446']",
        "acronyms": "'NCT01468207': 'PIONEER I', 'NCT01468233': 'PIONEER II', 'NCT04242446': 'BE HEARD I'",
        "body": HS_BODY,
    },
    {
        "out": "DIABETIC_MACULAR_EDEMA_NMA_REVIEW.html",
        "title": "RapidMeta Ophthalmology | DME Anti-VEGF NMA &mdash; Protocol T + YOSEMITE + RHINE v0.1",
        "auto_include": "['NCT01627249', 'NCT03622580', 'NCT03622593']",
        "acronyms": "'NCT01627249': 'Protocol T DRCR', 'NCT03622580': 'YOSEMITE', 'NCT03622593': 'RHINE'",
        "body": DME_BODY,
    },
    {
        "out": "MEDITERRANEAN_DIET_CV_NMA_REVIEW.html",
        "title": "RapidMeta Nutrition | Mediterranean Diet for CV Prevention NMA &mdash; PREDIMED + CORDIOPREV + PREDIMED-Plus v0.1",
        "auto_include": "['LEGACY-ISRCTN-35739639-PREDIMED', 'NCT00924937', 'LEGACY-ISRCTN-89898870-PREDIMEDPLUS']",
        "acronyms": "'LEGACY-ISRCTN-35739639-PREDIMED': 'PREDIMED', 'NCT00924937': 'CORDIOPREV', 'LEGACY-ISRCTN-89898870-PREDIMEDPLUS': 'PREDIMED-Plus'",
        "body": MEDDIET_BODY,
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
