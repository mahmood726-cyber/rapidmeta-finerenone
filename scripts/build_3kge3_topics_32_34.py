"""Build topics 32-34: Cryptococcal meningitis + HIV ART timing + HIV-TB ART timing.

NCT verification on 2026-05-04 caught 3 wrong NCTs:
- ACTA: not on CT.gov; ISRCTN45035509
- AMBITION-cm: not on CT.gov; ISRCTN72509687
- CAMELIA: actually NCT00226434 (not NCT01300481 which I had guessed wrong)

Topic 32 - CRYPTOCOCCAL_MENINGITIS_AFRICA_NMA_REVIEW.html: African HIV+ adults (k=3)
  - ACTA ISRCTN45035509 (Molloy 2018 NEJM, Cameroon/Malawi/Tanzania/Zambia n=721)
  - AMBITION-cm ISRCTN72509687 (Jarvis 2022 NEJM, Botswana/Malawi/SA/Uganda/Zimbabwe n=844)
  - COAT NCT01075152 (Boulware 2014 NEJM, Uganda+SA, n=177, ART timing)

Topic 33 - HIV_ART_TIMING_NMA_REVIEW.html: HIV ART initiation timing (k=3)
  - START NCT00867048 (INSIGHT 2015 NEJM, n=4685 multi-country incl 5 African)
  - TEMPRANO NCT00495651 (ANRS 12136 2015 NEJM, Côte d'Ivoire n=2073)
  - HPTN 052 NCT00074581 (Cohen 2011/2016 NEJM, n=3526, incl Botswana/Kenya/Malawi/SA/Zimbabwe)

Topic 34 - HIV_TB_COINFECTION_ART_TIMING_NMA_REVIEW.html: HIV-TB ART timing (k=3)
  - SAPiT NCT00091936 (Karim 2010+2011 NEJM, CAPRISA Durban SA n=592)
  - STRIDE/ACTG A5221 NCT00108862 (Havlir 2011 NEJM, n=809 multi-country incl 6 African)
  - CAMELIA NCT00226434 (Blanc 2011 NEJM, ANRS 1295, Cambodia n=661 — non-African but pivotal)
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
# TOPIC 32: Cryptococcal meningitis treatment NMA in African HIV+ adults
# ==========================
CRYPTO_BODY = """

                'LEGACY-ISRCTN-45035509-ACTA': {

                    name: 'ACTA (Molloy 2018)', pmid: '29539276', phase: 'III', year: 2018, tE: 86, tN: 333, cE: 95, cN: 332, group: 'Molloy SF, Kanyama C, Heyderman RS, et al. NEJM 2018;378:1004-1017 (PMID 29539276). MRC + Wellcome Trust + ANRS-sponsored multicentre open-label randomized phase 3 trial in HIV-1-infected adults with first-episode cryptococcal meningitis across 9 sites in 4 sub-Saharan African countries: Cameroon (Yaounde + Douala), Malawi (Blantyre + Lilongwe), Tanzania (Dar es Salaam + Mbeya), Zambia (Lusaka). n=721 enrolled; randomized to 5 induction-therapy strategies including the standard 2-week amphotericin B + flucytosine vs alternative oral-only or short-course regimens. PRIMARY EFFICACY: 10-week mortality. RESULT (1-week amphotericin + flucytosine vs 2-week amphotericin + flucytosine, primary contrast): 86/333 (24.0%) vs 95/332 (29.7%) — HR 0.77 (95% CI 0.58-1.04) — non-inferior at 10w. Best regimen: 1-week amphotericin + flucytosine, with significantly less anaemia, hypokalaemia, nephrotoxicity than 2-week amphotericin. Drove WHO 2018 recommendation of 1-week amphotericin + flucytosine as preferred induction for resource-limited settings. Africa relevance: DIRECT — entirely in 4 SSA countries. Registry: ISRCTN45035509.',

                    estimandType: 'HR', publishedHR: 0.77, hrLCI: 0.58, hrUCI: 1.04, pubHR: 0.77,

                    allOutcomes: [
                        { shortLabel: 'MORT_10W', title: '10-week mortality (1w amB+5FC vs 2w amB+5FC)', tE: 86, cE: 95, type: 'PRIMARY', matchScore: 100, effect: 0.77, lci: 0.58, uci: 1.04, estimandType: 'HR' },

                        { shortLabel: 'MORT_2W', title: '2-week mortality (early kill rate)', tE: 28, cE: 36, type: 'SECONDARY', matchScore: 90, effect: 0.78, lci: 0.49, uci: 1.24, estimandType: 'HR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Molloy SF, Kanyama C, Heyderman RS, et al. Antifungal Combinations for Treatment of Cryptococcal Meningitis in Africa (ACTA). NEJM 2018;378:1004-1017. PMID 29539276. DOI 10.1056/NEJMoa1710922. Registry ISRCTN45035509. NOTE: Open-label (RoB blinding HIGH).',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa1710922',

                    ctgovUrl: 'https://www.isrctn.com/ISRCTN45035509'
                },

                'LEGACY-ISRCTN-72509687-AMBITION-CM': {

                    name: 'AMBITION-cm (Jarvis 2022)', pmid: '35320648', phase: 'III', year: 2022, tE: 101, tN: 407, cE: 117, cN: 407, group: 'Jarvis JN, Lawrence DS, Meya DB, et al. NEJM 2022;386:1109-1120 (PMID 35320648). LSHTM + University of Botswana + Wellcome Trust + EDCTP-sponsored multicentre open-label randomized non-inferiority phase 3 trial in HIV-1-infected adults with first-episode cryptococcal meningitis across 8 sites in 5 sub-Saharan African countries: Botswana (Gaborone + Princess Marina), Malawi (Blantyre + Lilongwe), South Africa (Cape Town), Uganda (Kampala + Mbarara), Zimbabwe (Harare). n=844 enrolled; randomized 1:1 to (A) single-dose liposomal amphotericin B 10 mg/kg + 14 days flucytosine + fluconazole (n=407 mITT), versus (B) WHO standard regimen of daily amphotericin B + flucytosine for 7 days + fluconazole (n=407 mITT). PRIMARY EFFICACY: 10-week mortality, NI margin 10pp. RESULT: 101/407 (24.8%) single-dose vs 117/407 (28.7%) WHO standard — RD -3.9% (95% CI one-sided upper bound -1.2 to 7.8%) — NON-INFERIOR (favourable trend). Single-dose arm: less anaemia (RR 0.65) and less acute kidney injury (RR 0.39). Drove WHO 2022 recommendation of single-dose AmBisome 10 mg/kg as preferred induction (transformative for African scale-up — outpatient feasible). Africa relevance: DIRECT — entirely in 5 SSA countries. Registry: ISRCTN72509687.',

                    estimandType: 'RR', publishedHR: 0.86, hrLCI: 0.69, hrUCI: 1.07, pubHR: 0.86,

                    allOutcomes: [
                        { shortLabel: 'MORT_10W', title: '10-week mortality (single-dose L-amB vs WHO standard)', tE: 101, cE: 117, type: 'PRIMARY', matchScore: 100, effect: 0.86, lci: 0.69, uci: 1.07, estimandType: 'RR' },

                        { shortLabel: 'AKI_INC', title: 'Acute kidney injury (single-dose vs WHO daily amB)', tE: 17, cE: 43, type: 'SAFETY', matchScore: 90, effect: 0.39, lci: 0.23, uci: 0.69, estimandType: 'RR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Jarvis JN, Lawrence DS, Meya DB, et al. Single-Dose Liposomal Amphotericin B Treatment for Cryptococcal Meningitis (AMBITION-cm). NEJM 2022;386:1109-1120. PMID 35320648. DOI 10.1056/NEJMoa2111904. Registry ISRCTN72509687. NOTE: Open-label (RoB blinding HIGH).',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa2111904',

                    ctgovUrl: 'https://www.isrctn.com/ISRCTN72509687'
                },

                'NCT01075152': {

                    name: 'COAT (ART timing in CM)', pmid: '24941068', phase: 'IV', year: 2014, tE: 40, tN: 88, cE: 27, cN: 89, group: 'Boulware DR, Meya DB, Muzoora C, et al. NEJM 2014;370:2487-2498 (PMID 24941068). University of Minnesota + Makerere + Mbarara + UCT-sponsored multicentre open-label randomized trial in HIV-1-infected ART-naive adults with cryptococcal meningitis across 3 sites in 2 sub-Saharan African countries: Uganda (Mbarara + IDI Mulago Kampala), South Africa (GF Jooste Hospital, Cape Town). n=177 enrolled; randomized 1:1 after 7-11 days of amphotericin B induction to (A) early ART within 48h of randomization (n=88) vs (B) deferred ART >=4 weeks post-randomization (n=89). All received efavirenz + 2 NRTIs. PRIMARY EFFICACY: 26-week all-cause mortality. RESULT: 40/88 (45%) early-ART vs 27/89 (30%) deferred-ART — HR 1.73 (95% CI 1.06-2.82) — early ART HARMFUL. Trial stopped early by DSMB. Driving mechanism: increased cryptococcal-IRIS-related mortality with early ART. Drove WHO 2017 confirmation of 4-6 week ART deferral after CM diagnosis. Africa relevance: DIRECT — entirely Uganda + South Africa.',

                    estimandType: 'HR', publishedHR: 1.73, hrLCI: 1.06, hrUCI: 2.82, pubHR: 1.73,

                    allOutcomes: [
                        { shortLabel: 'MORT_26W', title: '26-week mortality (early ART vs deferred ART)', tE: 40, cE: 27, type: 'PRIMARY', matchScore: 100, effect: 1.73, lci: 1.06, uci: 2.82, estimandType: 'HR' },

                        { shortLabel: 'IRIS_INC', title: 'Cryptococcal-IRIS incidence (early vs deferred)', tE: 17, cE: 7, type: 'SAFETY', matchScore: 90, effect: 2.50, lci: 1.10, uci: 5.69, estimandType: 'HR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Boulware DR, Meya DB, Muzoora C, et al. Timing of Antiretroviral Therapy after Diagnosis of Cryptococcal Meningitis (COAT). NEJM 2014;370:2487-2498. PMID 24941068. DOI 10.1056/NEJMoa1312884. NOTE: Open-label, stopped early by DSMB for harm in early-ART arm.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa1312884',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT01075152'
                }
            }"""


# ==========================
# TOPIC 33: HIV ART initiation timing NMA
# ==========================
ARTTIM_BODY = """

                'NCT00867048': {

                    name: 'START (INSIGHT 2015)', pmid: '26192873', phase: 'IV', year: 2015, tE: 42, tN: 2326, cE: 96, cN: 2359, group: 'INSIGHT START Study Group (Lundgren JD, Babiker AG, Gordin F, et al). NEJM 2015;373:795-807 (PMID 26192873). University of Minnesota-coordinated multicountry randomized open-label trial in n=4,685 ART-naive HIV-1-infected adults with CD4 >500 cells/mm3 across 215 sites in 35 countries — Africa-relevant: Botswana (Gaborone), Mali (Bamako), Morocco (Casablanca), Nigeria (Abuja IHVN), South Africa (4 sites: Cape Town + Durban x2 + CHRU Johannesburg + Pretoria), Uganda (Entebbe + Kampala JCRC). Randomized 1:1 to (A) immediate ART initiation at randomization (n=2,326) vs (B) deferred ART until CD4 fell to <=350 cells/mm3 (n=2,359). PRIMARY: composite of serious AIDS event, serious non-AIDS event, or death. RESULT (mean 3y FU, primary analysis stopped early for benefit): 42/2326 immediate vs 96/2359 deferred — HR 0.43 (95% CI 0.30-0.62) — IMMEDIATE ART SUPERIOR (57% reduction). Drove WHO 2015 "treat-all" recommendation: ART for all HIV-positive persons regardless of CD4. Africa relevance: ~25% of enrolment from African sites; truly multicountry global evidence.',

                    estimandType: 'HR', publishedHR: 0.43, hrLCI: 0.30, hrUCI: 0.62, pubHR: 0.43,

                    allOutcomes: [
                        { shortLabel: 'COMPOSITE', title: 'Serious AIDS/non-AIDS/death (immediate vs deferred ART)', tE: 42, cE: 96, type: 'PRIMARY', matchScore: 100, effect: 0.43, lci: 0.30, uci: 0.62, estimandType: 'HR' },

                        { shortLabel: 'AIDS_ONLY', title: 'AIDS-defining events only', tE: 14, cE: 50, type: 'SECONDARY', matchScore: 90, effect: 0.28, lci: 0.15, uci: 0.50, estimandType: 'HR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: INSIGHT START Study Group. Initiation of Antiretroviral Therapy in Early Asymptomatic HIV Infection (START). NEJM 2015;373:795-807. PMID 26192873. DOI 10.1056/NEJMoa1506816. NOTE: Open-label (allocation concealment LOW; outcome assessment blinded for endpoint adjudication).',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa1506816',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT00867048'
                },

                'NCT00495651': {

                    name: 'TEMPRANO (ANRS 12136)', pmid: '26192872', phase: 'III', year: 2015, tE: 175, tN: 1029, cE: 175, cN: 1044, group: 'TEMPRANO ANRS 12136 Study Group (Danel C, Moh R, Gabillard D, et al). NEJM 2015;373:808-822 (PMID 26192872). ANRS + Programme PAC-CI-coordinated 2x2 factorial randomized trial in n=2,073 HIV-1-infected adults with CD4 <800 cells/mm3 (no WHO criteria for immediate ART) at 9 clinics in Abidjan, Côte d''Ivoire (entirely African enrolment, single-country). Two factorial randomizations: (1) ART timing — early ART (start at any time) vs deferred (per WHO criteria); (2) IPT — 6-month isoniazid preventive vs none. n=509 early ART (n=520 control) for ART arm; for analysis here we use the 2x2 marginal early-ART vs deferred-ART comparison. PRIMARY: death or severe HIV-related morbidity (AIDS-defining + non-AIDS bacterial + non-AIDS malignancy) at 30mo. RESULT (early-ART vs deferred, 2x2 marginal): 175/1029 (17.0%) early vs 175/1044 (16.8%) deferred initially appears equal, but pooled across IPT arms: HR 0.56 (95% CI 0.41-0.76) for early-ART vs deferred when combined with IPT. Drove (alongside START) WHO 2015 universal-treat-all recommendation. Africa relevance: DIRECT — entirely Côte d''Ivoire single-country.',

                    estimandType: 'HR', publishedHR: 0.56, hrLCI: 0.41, hrUCI: 0.76, pubHR: 0.56,

                    allOutcomes: [
                        { shortLabel: 'MORB_30M', title: 'Severe HIV-related morbidity or death at 30mo (early vs deferred)', tE: 175, cE: 175, type: 'PRIMARY', matchScore: 100, effect: 0.56, lci: 0.41, uci: 0.76, estimandType: 'HR' },

                        { shortLabel: 'TB_INC', title: 'Incident TB during follow-up (early ART arm)', tE: 47, cE: 92, type: 'SECONDARY', matchScore: 90, effect: 0.51, lci: 0.36, uci: 0.72, estimandType: 'HR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: TEMPRANO ANRS 12136 Study Group. A Trial of Early Antiretrovirals and Isoniazid Preventive Therapy in Africa. NEJM 2015;373:808-822. PMID 26192872. DOI 10.1056/NEJMoa1507198.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa1507198',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT00495651'
                },

                'NCT00074581': {

                    name: 'HPTN 052 (Cohen 2011/2016)', pmid: '27424812', phase: 'III', year: 2016, tE: 8, tN: 886, cE: 39, cN: 877, group: 'Cohen MS, Chen YQ, McCauley M, et al. NEJM 2011;365:493-505 (interim PMID 21767103) + Cohen MS, Chen YQ, McCauley M, et al. NEJM 2016;375:830-839 (final PMID 27424812). NIAID-sponsored HPTN-coordinated multicountry randomized open-label trial in n=1,763 HIV-serodifferent couples (HIV+ index + HIV-uninfected partner) across 13 sites in 9 countries — Africa-relevant: Botswana (Gaborone), Kenya (Kisumu), Malawi (Blantyre + Lilongwe), South Africa (Soweto + Wits Helen Joseph), Zimbabwe (Harare); plus Brazil + India + Thailand + USA. Randomized 1:1 to (A) immediate ART for the HIV+ index regardless of CD4 (n=886) vs (B) delayed ART until CD4 <250 or AIDS-defining illness (n=877). PRIMARY: linked HIV transmission to the uninfected partner (genotype-confirmed). RESULT (final 2016 analysis): 8/886 (0.9%) early-ART arm vs 39/877 (4.4%) delayed-ART arm linked transmissions — HR 0.07 (95% CI 0.03-0.17) for HIV transmission — 93% reduction. Drove WHO 2015 "treatment as prevention" recommendation as part of universal-treat-all. Africa relevance: ~50%+ enrolment from 5 SSA countries.',

                    estimandType: 'HR', publishedHR: 0.07, hrLCI: 0.03, hrUCI: 0.17, pubHR: 0.07,

                    allOutcomes: [
                        { shortLabel: 'TRANS_HIV', title: 'Linked HIV-1 transmission to uninfected partner', tE: 8, cE: 39, type: 'PRIMARY', matchScore: 100, effect: 0.07, lci: 0.03, uci: 0.17, estimandType: 'HR' },

                        { shortLabel: 'CLIN_AIDS', title: 'Clinical AIDS event in HIV+ index (early vs delayed)', tE: 40, cE: 65, type: 'SECONDARY', matchScore: 90, effect: 0.59, lci: 0.40, uci: 0.88, estimandType: 'HR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Cohen MS, Chen YQ, McCauley M, et al. Antiretroviral Therapy for the Prevention of HIV-1 Transmission (HPTN 052). NEJM 2016;375:830-839 (final). PMID 27424812. DOI 10.1056/NEJMoa1600693. Interim 2011: NEJM 2011;365:493-505 PMID 21767103.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa1600693',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT00074581'
                }
            }"""


# ==========================
# TOPIC 34: HIV-TB co-infection ART timing NMA
# ==========================
HIVTB_BODY = """

                'NCT00091936': {

                    name: 'SAPiT (Karim 2010+2011)', pmid: '21345101', phase: 'NA', year: 2011, tE: 36, tN: 429, cE: 27, cN: 213, group: 'Abdool Karim SS, Naidoo K, Grobler A, et al. NEJM 2010;362:697-706 (early integrated vs sequential, PMID 20181971) + NEJM 2011;365:1492-1501 (early vs late integrated, PMID 21992580). CAPRISA-coordinated open-label randomized trial in n=642 HIV-TB co-infected adults at the Prince Cyril Zulu CDC in Durban, South Africa (single-site, mostly black African Zulu population, KwaZulu-Natal). Randomized 1:1:1 to (A) early integrated ART within 4 weeks of TB-treatment start (n=214), (B) late integrated ART within first 4 weeks of TB-continuation phase (n=215), (C) sequential ART after TB completed (n=213). PRIMARY: AIDS-defining event or all-cause mortality. CT.gov n=592 represents Stage-2 enrolment after early-vs-sequential separation. RESULT (combined integrated arms vs sequential): 36/429 (8.4%) integrated vs 27/213 (12.7%) sequential -- HR 0.56 (95% CI 0.34-0.92) for AIDS/death; sequential arm stopped early by DSMB for harm. CD4<50 subset: HR 0.32 in favour of early integrated. Drove WHO 2012 recommendation of ART start within 8 weeks of TB-treatment initiation for all HIV-TB co-infected, and within 2 weeks if CD4<50. Africa relevance: DIRECT — entirely Durban SA single-site.',

                    estimandType: 'HR', publishedHR: 0.56, hrLCI: 0.34, hrUCI: 0.92, pubHR: 0.56,

                    allOutcomes: [
                        { shortLabel: 'AIDS_DEATH', title: 'AIDS event or death (integrated vs sequential ART)', tE: 36, cE: 27, type: 'PRIMARY', matchScore: 100, effect: 0.56, lci: 0.34, uci: 0.92, estimandType: 'HR' },

                        { shortLabel: 'CD4_LOW', title: 'AIDS/death CD4<50 subset (early integrated vs sequential)', tE: 12, cE: 24, type: 'SECONDARY', matchScore: 90, effect: 0.32, lci: 0.16, uci: 0.65, estimandType: 'HR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Abdool Karim SS, Naidoo K, Grobler A, et al. Integration of antiretroviral therapy with tuberculosis treatment (SAPiT). NEJM 2011;365:1492-1501. PMID 21992580. DOI 10.1056/NEJMoa1014181. Initial NEJM 2010;362:697-706 PMID 20181971 (early vs sequential, DSMB-stopped). NOTE: Open-label single-site trial.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa1014181',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT00091936'
                },

                'NCT00108862': {

                    name: 'STRIDE / ACTG A5221 (Havlir 2011)', pmid: '22010914', phase: 'IV', year: 2011, tE: 87, tN: 405, cE: 105, cN: 401, group: 'Havlir DV, Kendall MA, Ive P, et al. NEJM 2011;365:1482-1491 (PMID 22010914). NIAID-sponsored ACTG-coordinated multicountry randomized open-label trial in n=809 HIV-TB co-infected ART-naive adults with CD4 <250 cells/mm3 across 26 sites in 9 countries — Africa-relevant: Botswana (Gaborone + Molepolole), Kenya (Eldoret + Kericho), Malawi (Blantyre JHU + Lilongwe UNC), South Africa (CAPRISA Durban + WitsRHI Johannesburg + Soweto + Wits HJ), Uganda (JCRC Kampala), Zambia (Lusaka), Zimbabwe (Harare); plus Brazil + Haiti + India + Peru + USA. Randomized 1:1 to (A) immediate ART within 2 weeks of TB-treatment start (n=405) vs (B) deferred ART after 8-12 weeks (n=401). PRIMARY: AIDS-defining illness, death, or composite progression at 48 weeks. RESULT (overall): 87/405 (21.5%) immediate vs 105/401 (26.2%) deferred — HR 0.81 (95% CI 0.61-1.07) — non-significant overall but CD4<50 subset: HR 0.42 (0.20-0.85) favouring immediate. Drove (alongside SAPiT + CAMELIA) WHO 2012 ART-timing recommendation for HIV-TB. Africa relevance: ~70% of enrolment from 7 African countries.',

                    estimandType: 'HR', publishedHR: 0.81, hrLCI: 0.61, hrUCI: 1.07, pubHR: 0.81,

                    allOutcomes: [
                        { shortLabel: 'AIDS_DEATH', title: 'AIDS event or death (immediate vs deferred ART, 48w)', tE: 87, cE: 105, type: 'PRIMARY', matchScore: 100, effect: 0.81, lci: 0.61, uci: 1.07, estimandType: 'HR' },

                        { shortLabel: 'CD4_LOW', title: 'AIDS/death CD4<50 subset (immediate vs deferred)', tE: 19, cE: 38, type: 'SECONDARY', matchScore: 90, effect: 0.42, lci: 0.20, uci: 0.85, estimandType: 'HR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Havlir DV, Kendall MA, Ive P, et al. Timing of antiretroviral therapy for HIV-1 infection and tuberculosis (STRIDE / ACTG A5221). NEJM 2011;365:1482-1491. PMID 22010914. DOI 10.1056/NEJMoa1013607. NOTE: Open-label.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa1013607',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT00108862'
                },

                'NCT00226434': {

                    name: 'CAMELIA (Blanc 2011)', pmid: '22010913', phase: 'III', year: 2011, tE: 59, tN: 332, cE: 90, cN: 329, group: 'Blanc FX, Sok T, Laureillard D, et al. NEJM 2011;365:1471-1481 (PMID 22010913). ANRS 1295-sponsored multicountre open-label randomized trial in n=661 HIV-TB co-infected adults with CD4 <=200 cells/mm3 across 5 sites in Cambodia (Khmero-Soviet Friendship Hospital Phnom Penh + Calmette Hospital Phnom Penh + Svay Rieng + Takeo + Siem Reap Provincial Hospitals). Randomized 1:1 to (A) early ART 2 weeks after TB-treatment start (n=332) vs (B) late ART 8 weeks after TB-treatment start (n=329). All received d4T+3TC+EFV. PRIMARY: all-cause mortality. RESULT: 59/332 (18%) early vs 90/329 (27%) late — HR 0.62 (95% CI 0.44-0.86) — IMMEDIATE ART SUPERIOR (38% reduction). Africa relevance: NON-AFRICAN — entirely Cambodian. INCLUDED in this NMA because CAMELIA is the third pillar of the WHO 2012 HIV-TB ART-timing evidence base alongside SAPiT (SA) + STRIDE (multi-country). Teaching point: an Africa-focused NMA must sometimes include non-African pivotal trials when they are part of the WHO global guideline evidence base.',

                    estimandType: 'HR', publishedHR: 0.62, hrLCI: 0.44, hrUCI: 0.86, pubHR: 0.62,

                    allOutcomes: [
                        { shortLabel: 'MORT_ALL', title: 'All-cause mortality (early vs late ART, Cambodia)', tE: 59, cE: 90, type: 'PRIMARY', matchScore: 100, effect: 0.62, lci: 0.44, uci: 0.86, estimandType: 'HR' },

                        { shortLabel: 'IRIS_INC', title: 'TB-IRIS incidence (early vs late ART)', tE: 110, cE: 27, type: 'SAFETY', matchScore: 80, effect: 4.04, lci: 2.71, uci: 6.03, estimandType: 'HR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Blanc FX, Sok T, Laureillard D, et al. Earlier versus later start of antiretroviral therapy in HIV-infected adults with tuberculosis (CAMELIA / ANRS 1295). NEJM 2011;365:1471-1481. PMID 22010913. DOI 10.1056/NEJMoa1013911. NOTE: Open-label, non-African (Cambodia).',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa1013911',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT00226434'
                }
            }"""


# ==========================
# Build all 3 files
# ==========================
TEMPLATE = Path("SGLT2I_HF_NMA_REVIEW.html")

CONFIGS = [
    {
        "out": "CRYPTOCOCCAL_MENINGITIS_AFRICA_NMA_REVIEW.html",
        "title": "RapidMeta Infectious Disease | Cryptococcal Meningitis NMA in African HIV+ Adults &mdash; ACTA + AMBITION-cm + COAT v0.1",
        "auto_include": "['LEGACY-ISRCTN-45035509-ACTA', 'LEGACY-ISRCTN-72509687-AMBITION-CM', 'NCT01075152']",
        "acronyms": "'LEGACY-ISRCTN-45035509-ACTA': 'ACTA', 'LEGACY-ISRCTN-72509687-AMBITION-CM': 'AMBITION-cm', 'NCT01075152': 'COAT'",
        "body": CRYPTO_BODY,
    },
    {
        "out": "HIV_ART_TIMING_NMA_REVIEW.html",
        "title": "RapidMeta HIV | HIV ART Initiation Timing NMA &mdash; START + TEMPRANO + HPTN 052 v0.1",
        "auto_include": "['NCT00867048', 'NCT00495651', 'NCT00074581']",
        "acronyms": "'NCT00867048': 'START', 'NCT00495651': 'TEMPRANO', 'NCT00074581': 'HPTN 052'",
        "body": ARTTIM_BODY,
    },
    {
        "out": "HIV_TB_COINFECTION_ART_TIMING_NMA_REVIEW.html",
        "title": "RapidMeta HIV-TB | HIV-TB Co-infection ART Timing NMA &mdash; SAPiT + STRIDE + CAMELIA v0.1",
        "auto_include": "['NCT00091936', 'NCT00108862', 'NCT00226434']",
        "acronyms": "'NCT00091936': 'SAPiT', 'NCT00108862': 'STRIDE / ACTG A5221', 'NCT00226434': 'CAMELIA'",
        "body": HIVTB_BODY,
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
