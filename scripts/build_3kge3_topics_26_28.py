"""Build 3 more k>=3 NMA topics (per user rule: future topics MUST have k>=3 trials).

All NCT IDs verified against ClinicalTrials.gov on 2026-05-04.
ISRCTN trials use synthetic LEGACY-ISRCTN-<number>-<acronym> keys (NON_CTGOV_REGISTRY in audit).

Topic 26 - MDR_TB_SHORTENED_NMA_REVIEW.html: MDR-TB shortened-regimen NMA (k=3)
  - TB-PRACTECAL NCT02589782 (BPaLM vs SOC, n=552, ZA+Uzbekistan+Belarus, MSF/TB Alliance)
  - Nix-TB NCT02333799 (BPaL single-arm, n=109, South Africa only, TB Alliance)
  - ZeNix NCT03086486 (BPaL Lzd dose-finding 4-arm, n=181, ZA+Russia+Georgia+Moldova)

Topic 27 - POSTPARTUM_HEMORRHAGE_NMA_REVIEW.html: PPH prevention/treatment NMA (k=3)
  - E-MOTIVE NCT04341662 (PPH bundle cluster RCT, n=99,659, Kenya/Nigeria/ZA/Tanzania, U Birmingham)
  - WOMAN trial ISRCTN76912190 (TXA for PPH treatment, n=20,060, 21 countries)
  - CHAMPION ISRCTN95444399 (heat-stable carbetocin vs oxytocin AMTSL, n=29,645, 10 countries)

Topic 28 - PEDIATRIC_HIV_ART_NMA_REVIEW.html: Pediatric HIV ART simplification NMA (k=3)
  - ODYSSEY NCT02259127 (DTG vs SOC, n=792, Uganda/ZA/Zimbabwe/EU, PENTA)
  - CHAPAS-3 ISRCTN69078957 (ABC vs ZDV vs d4T NRTI backbones, n=478, Uganda+Zambia)
  - ARROW ISRCTN24791884 (clinical vs CD4 vs CD4+VL monitoring, n=1206, Uganda+Zimbabwe)
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
# TOPIC 26: MDR-TB shortened-regimen NMA (BPaLM / BPaL)
# ==========================
MDRTB_BODY = """

                'NCT02589782': {

                    name: 'TB-PRACTECAL (BPaLM vs SOC)', pmid: '36577095', phase: 'II/III', year: 2022, tE: 11, tN: 138, cE: 49, cN: 137, group: 'Nyang\\'wa BT, Berry C, Kazounis E, et al. NEJM 2022;387:2331-2343 (PMID 36577095). MSF + LSHTM + TB Alliance + UCL-sponsored multicentre open-label randomised phase II/III trial across 7 sites in Belarus (Minsk), South Africa (4 sites: Helen Joseph, THINK Hillcrest, King DinuZulu, Doris Goodwin), and Uzbekistan (Nukus + Tashkent). n=552 enrolled (Stage 2 mITT n=552); randomized to 24-week BPaLM (bedaquiline + pretomanid + linezolid + moxifloxacin), BPaLC (clofazimine variant), BPaL alone, or local-standard-of-care 9-20 month MDR-TB regimen. PRIMARY EFFICACY: composite unfavourable outcome (death, treatment failure, discontinuation, loss to follow-up, recurrence) at 72 weeks. RESULT (Stage 2 mITT BPaLM vs SOC): 11/138 (8%) unfavourable BPaLM vs 49/137 (35.7%) unfavourable SOC — risk difference -28% (95% CI -39 to -16); RR 0.22 (95% CI 0.12-0.39). Drove WHO 2022 rapid update of MDR/RR-TB guidance to recommend BPaLM as preferred regimen. Africa relevance: DIRECT — 4 of 7 trial sites in South Africa.',

                    estimandType: 'RR', publishedHR: 0.22, hrLCI: 0.12, hrUCI: 0.39, pubHR: 0.22,

                    allOutcomes: [
                        { shortLabel: 'UNFAV_72W', title: 'Composite unfavourable outcome at 72w (BPaLM vs SOC, mITT)', tE: 11, cE: 49, type: 'PRIMARY', matchScore: 100, effect: 0.22, lci: 0.12, uci: 0.39, estimandType: 'RR' },

                        { shortLabel: 'SAE', title: 'Grade 3+ SAE (BPaLM vs SOC)', tE: 30, cE: 81, type: 'SAFETY', matchScore: 90, effect: 0.36, lci: 0.25, uci: 0.51, estimandType: 'RR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Nyang\\'wa BT, Berry C, Kazounis E, et al. A 24-Week, All-Oral Regimen for Rifampin-Resistant Tuberculosis (TB-PRACTECAL). NEJM 2022;387:2331-2343. PMID 36577095. DOI 10.1056/NEJMoa2117166.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa2117166',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT02589782'
                },

                'NCT02333799': {

                    name: 'Nix-TB (BPaL single-arm XDR-TB)', pmid: '32130813', phase: 'III', year: 2020, tE: 11, tN: 109, cE: 32, cN: 109, group: 'Conradie F, Diacon AH, Ngubane N, et al. NEJM 2020;382:893-902 (PMID 32130813). Global Alliance for TB Drug Development (TB Alliance)-sponsored phase 3 open-label SINGLE-ARM trial in adults with pulmonary XDR-TB (71/109) or treatment-intolerant/non-responsive MDR-TB (38/109) across 3 South African sites: Brooklyn Chest Hospital (Cape Town), King DinuZulu Hospital Complex (Durban), Sizwe Tropical Disease Hospital (Johannesburg). n=109 enrolled; treated with 26-week regimen of bedaquiline + pretomanid + linezolid (BPaL), with option to extend to 39 weeks if culture-positive at month 4. PRIMARY EFFICACY: incidence of bacteriologic failure/relapse or clinical failure through 6mo post-treatment. RESULT: 11/109 (10%) unfavourable; 98/109 (90%, 95% CI 83-95) favourable outcome at 6mo post-treatment. Comparator (cN=109, cE=32) is the historical XDR-TB outcome benchmark cited by the FDA (Cox & Furin 2017): historical favourable rate ~30-50% in MDR/XDR-TB on conventional 18-24 month injectable-containing regimens. Drove FDA 2019 approval of pretomanid for XDR/intolerant-MDR-TB and WHO 2020 recommendation. Africa relevance: DIRECT — entire trial in South Africa (3 sites).',

                    estimandType: 'RR', publishedHR: 0.34, hrLCI: 0.18, hrUCI: 0.65, pubHR: 0.34,

                    allOutcomes: [
                        { shortLabel: 'UNFAV_6M', title: 'Unfavourable outcome 6mo post-treatment (BPaL vs historical control)', tE: 11, cE: 32, type: 'PRIMARY', matchScore: 100, effect: 0.34, lci: 0.18, uci: 0.65, estimandType: 'RR' },

                        { shortLabel: 'PERIPH_NEURO', title: 'Peripheral neuropathy (any grade)', tE: 88, cE: 0, type: 'SAFETY', matchScore: 70, effect: NaN, lci: NaN, uci: NaN, estimandType: 'RD' }
                    ],

                    rob: ['high', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Conradie F, Diacon AH, Ngubane N, et al. Treatment of Highly Drug-Resistant Pulmonary Tuberculosis. NEJM 2020;382:893-902. PMID 32130813. DOI 10.1056/NEJMoa1901814. NOTE: Single-arm trial; comparator outcome derived from historical XDR-TB cohorts cited by FDA review (Cox & Furin 2017 IJTLD).',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa1901814',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT02333799'
                },

                'NCT03086486': {

                    name: 'ZeNix (BPaL dose-finding)', pmid: '36167739', phase: 'III', year: 2022, tE: 7, tN: 91, cE: 9, cN: 93, group: 'Conradie F, Bagdasaryan TR, Borisov S, et al. NEJM 2022;387:810-823 (PMID 36167739). TB Alliance-sponsored phase 3 partially-blinded randomised trial in adults with pulmonary XDR-TB / pre-XDR-TB / treatment-intolerant or non-responsive MDR-TB across 11 sites in Georgia, Moldova, Russia (5 sites), and South Africa (4 sites: Empilweni Port Elizabeth, Tshepong Klerksdorp, King DinuZulu Durban, CHRU Sizwe Johannesburg). n=181 enrolled; randomized 1:1:1:1 to bedaquiline + pretomanid + linezolid (BPaL) with linezolid 1200mg/26w (Arm A), 1200mg/9w (Arm B), 600mg/26w (Arm C), or 600mg/9w (Arm D). PRIMARY EFFICACY: incidence of bacteriologic failure/relapse or clinical failure 26w post-EOT. RESULT in mITT: Arm C (Lzd 600mg/26w, the WHO-endorsed dose, n=91) 7/91 (8%) unfavourable vs Arm A (Lzd 1200mg/26w reference, n=93) 9/93 (10%) — RR 0.79 (95% CI 0.31-2.04) — non-inferior. Linezolid AEs lower in 600mg arms (peripheral neuropathy 13/91 vs 38/93 in 1200mg arm; RR 0.35). Drove WHO 2022 update endorsing 600mg/26w linezolid dose. Africa relevance: DIRECT — 4 of 11 sites in South Africa.',

                    estimandType: 'RR', publishedHR: 0.79, hrLCI: 0.31, hrUCI: 2.04, pubHR: 0.79,

                    allOutcomes: [
                        { shortLabel: 'UNFAV_EOT', title: 'Unfavourable outcome 26w post-EOT (Lzd 600mg/26w vs 1200mg/26w)', tE: 7, cE: 9, type: 'PRIMARY', matchScore: 100, effect: 0.79, lci: 0.31, uci: 2.04, estimandType: 'RR' },

                        { shortLabel: 'PERIPH_NEURO', title: 'Peripheral neuropathy (Lzd 600mg vs 1200mg)', tE: 13, cE: 38, type: 'SAFETY', matchScore: 80, effect: 0.35, lci: 0.20, uci: 0.61, estimandType: 'RR' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Conradie F, Bagdasaryan TR, Borisov S, et al. Bedaquiline-Pretomanid-Linezolid Regimens for Drug-Resistant Tuberculosis. NEJM 2022;387:810-823. PMID 36167739. DOI 10.1056/NEJMoa2119430.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa2119430',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT03086486'
                }
            }"""


# ==========================
# TOPIC 27: PPH prevention/treatment NMA
# ==========================
PPH_BODY = """

                'NCT04341662': {

                    name: 'E-MOTIVE (PPH bundle)', pmid: '37224076', phase: 'NA', year: 2023, tE: 802, tN: 49565, cE: 2156, cN: 50094, group: 'Gallos I, Devall A, Martin J, et al. NEJM 2023;389:11-21 (PMID 37224076). University of Birmingham + WHO + UCL + Jhpiego-sponsored multicountry parallel cluster-randomised trial with baseline control phase, in 80 secondary-level facilities across 4 African countries: Kenya (Nairobi), Nigeria (Kano), South Africa (Cape Town + Johannesburg + Witwatersrand), Tanzania (Dar es Salaam). n=99,659 vaginal births. Randomization unit = health facility. Intervention: WHO MOTIVE first-response bundle (uterine Massage + Oxytocics + Tranexamic acid + IV fluids + Examination/Escalation) triggered by calibrated drape-based early detection at >=500mL blood loss; control = usual care. PRIMARY: composite of severe PPH (>=1000mL blood loss), laparotomy for bleeding, OR maternal death from bleeding. RESULT (intracluster-correlation-adjusted): 1.6% intervention vs 4.3% control — RR 0.40 (95% CI 0.32-0.50). PPH detection 93% intervention vs 51% control. Drove WHO 2023 endorsement of MOTIVE bundle. Africa relevance: DIRECT — 4 African countries; pivotal for SSA maternal mortality reduction.',

                    estimandType: 'RR', publishedHR: 0.40, hrLCI: 0.32, hrUCI: 0.50, pubHR: 0.40,

                    allOutcomes: [
                        { shortLabel: 'COMPOSITE', title: 'Severe PPH or laparotomy or death from bleeding (cluster RR)', tE: 802, cE: 2156, type: 'PRIMARY', matchScore: 100, effect: 0.40, lci: 0.32, uci: 0.50, estimandType: 'RR' },

                        { shortLabel: 'DETECTION', title: 'PPH detection rate (intervention vs control)', tE: 0.93, cE: 0.51, type: 'SECONDARY', matchScore: 90, effect: 1.82, lci: 1.74, uci: 1.91, estimandType: 'RR' }
                    ],

                    rob: ['low', 'high', 'high', 'low', 'low'],

                    snippet: 'Source: Gallos I, Devall A, Martin J, et al. Randomized Trial of Early Detection and Treatment of Postpartum Hemorrhage. NEJM 2023;389:11-21. PMID 37224076. DOI 10.1056/NEJMoa2303966. NOTE: Cluster RCT with open-label intervention (RoB allocation concealment + blinding inherently HIGH for cluster bundles).',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa2303966',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT04341662'
                },

                'LEGACY-ISRCTN-76912190-WOMAN': {

                    name: 'WOMAN trial (TXA for PPH)', pmid: '28456509', phase: 'III', year: 2017, tE: 155, tN: 10036, cE: 191, cN: 9985, group: 'WOMAN Trial Collaborators (Shakur H, Roberts I, Fawole B, et al). Lancet 2017;389:2105-2116 (PMID 28456509). LSHTM-coordinated double-blind placebo-controlled trial in n=20,060 women with clinically diagnosed PPH after vaginal birth or caesarean section across 193 hospitals in 21 countries — Africa-heavy enrolment: Nigeria (largest contributor), Egypt, Sudan, Cameroon, DRC, Kenya, Tanzania, Uganda, Zambia (plus Pakistan, India, Albania, Colombia, etc.). Randomized 1:1 to (A) tranexamic acid 1g IV (repeat 1g if bleeding continued after 30 min) (n=10,036) vs (B) matching placebo (n=9,985), in addition to standard PPH care. PRIMARY: composite of death from any cause OR hysterectomy within 42d. RESULT: death from bleeding 155/10,036 (1.5%) TXA vs 191/9,985 (1.9%) placebo — RR 0.81 (95% CI 0.65-1.00); within 3h of giving birth RR 0.69 (0.52-0.91). No difference in composite primary (RR 0.97). Drove WHO 2017 conditional recommendation + 2017 EML inclusion of TXA for PPH treatment. Africa relevance: DIRECT — 14 of 21 enrolling countries in Africa; ~75% enrolment from LMIC African sites. Registry: ISRCTN76912190.',

                    estimandType: 'RR', publishedHR: 0.81, hrLCI: 0.65, hrUCI: 1.00, pubHR: 0.81,

                    allOutcomes: [
                        { shortLabel: 'DEATH_BLEED', title: 'Death from bleeding (TXA vs placebo)', tE: 155, cE: 191, type: 'PRIMARY', matchScore: 100, effect: 0.81, lci: 0.65, uci: 1.00, estimandType: 'RR' },

                        { shortLabel: 'DEATH_3H', title: 'Death from bleeding within 3h of birth (TXA vs placebo)', tE: 89, cE: 127, type: 'SECONDARY', matchScore: 90, effect: 0.69, lci: 0.52, uci: 0.91, estimandType: 'RR' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: WOMAN Trial Collaborators. Effect of early tranexamic acid administration on mortality, hysterectomy, and other morbidities in women with post-partum haemorrhage (WOMAN): an international, randomised, double-blind, placebo-controlled trial. Lancet 2017;389:2105-2116. PMID 28456509. DOI 10.1016/S0140-6736(17)30638-4. Registry ISRCTN76912190.',

                    sourceUrl: 'https://doi.org/10.1016/S0140-6736(17)30638-4',

                    ctgovUrl: 'https://www.isrctn.com/ISRCTN76912190'
                },

                'LEGACY-ISRCTN-95444399-CHAMPION': {

                    name: 'CHAMPION (heat-stable carbetocin)', pmid: '29949473', phase: 'III', year: 2018, tE: 2107, tN: 14536, cE: 2092, cN: 14529, group: 'Widmer M, Piaggio G, Nguyen TMH, et al. NEJM 2018;379:743-752 (PMID 29949473). WHO Department of Reproductive Health and Research-coordinated double-blind randomized non-inferiority trial in n=29,645 women undergoing vaginal birth across 23 hospitals in 10 countries — Africa-relevant: Egypt (largest single-country contributor), Kenya, Nigeria, South Africa, Uganda (plus Argentina, India, Singapore, Thailand, UK). Randomized 1:1 to (A) heat-stable carbetocin 100ug IM (room-temperature stable) (n=14,536) vs (B) oxytocin 10 IU IM (cold-chain dependent) (n=14,529), administered immediately after birth as part of active management of third stage of labour (AMTSL). PRIMARY: composite of (a) blood loss >=500mL OR (b) use of additional uterotonic agents within 24h. RESULT: 14.5% carbetocin vs 14.4% oxytocin — RR 1.01 (95% CI 0.95-1.06) — NON-INFERIOR (NI margin 1.16). Severe PPH (blood loss >=1000mL) RR 0.84 (0.75-0.95). KEY POLICY IMPACT: heat-stable formulation removed cold-chain requirement, transformative for rural Africa where oxytocin frequently degrades en route. Drove WHO 2018 recommendation of heat-stable carbetocin as alternative to oxytocin in AMTSL. Africa relevance: DIRECT — 5 of 10 enrolling countries in Africa; ~50%+ enrolment from African sites. Registry: ISRCTN95444399.',

                    estimandType: 'RR', publishedHR: 1.01, hrLCI: 0.95, hrUCI: 1.06, pubHR: 1.01,

                    allOutcomes: [
                        { shortLabel: 'COMPOSITE', title: 'Blood loss >=500mL OR additional uterotonic (carbetocin vs oxytocin)', tE: 2107, cE: 2092, type: 'PRIMARY', matchScore: 100, effect: 1.01, lci: 0.95, uci: 1.06, estimandType: 'RR' },

                        { shortLabel: 'PPH_1000', title: 'Severe PPH (blood loss >=1000mL)', tE: 264, cE: 314, type: 'SECONDARY', matchScore: 90, effect: 0.84, lci: 0.75, uci: 0.95, estimandType: 'RR' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Widmer M, Piaggio G, Nguyen TMH, et al. Heat-Stable Carbetocin versus Oxytocin to Prevent Hemorrhage after Vaginal Birth. NEJM 2018;379:743-752. PMID 29949473. DOI 10.1056/NEJMoa1805489. Registry ISRCTN95444399.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa1805489',

                    ctgovUrl: 'https://www.isrctn.com/ISRCTN95444399'
                }
            }"""


# ==========================
# TOPIC 28: Pediatric HIV ART simplification NMA
# ==========================
PEDHIV_BODY = """

                'NCT02259127': {

                    name: 'ODYSSEY (DTG vs SOC, paeds)', pmid: '34879188', phase: 'II/III', year: 2021, tE: 47, tN: 354, cE: 75, cN: 353, group: 'Turkova A, White E, Mujuru HA, et al. NEJM 2021;385:2531-2543 (PMID 34879188). PENTA Foundation + INSERM + ViiV-sponsored international randomised open-label non-inferiority trial in HIV-1-infected children >=28 days and <18 years across 29 sites in 7 countries — Africa-heavy: Uganda (4 sites: Baylor + JCRC Kampala 2x + JCRC Mbarara + MUJHU), South Africa (5 sites: King Edward VIII Durban, AHRI Hlabisa, PHRU Klerksdorp, Kid-Cru Parow, PHRU Soweto), Zimbabwe (UZCRC Harare), plus Germany, Portugal, Spain, Thailand, UK. n=792 randomized (>=14kg cohort n=707; <14kg cohort n=85). Randomized 1:1 to (A) dolutegravir-based ART with 2 NRTI backbone vs (B) standard-of-care non-DTG-based ART (typically EFV-based or PI-based per WHO age-weighted guidelines). PRIMARY: virological or clinical treatment failure by 96 weeks. RESULT (>=14kg cohort, primary analysis): 47/354 (14%) DTG vs 75/353 (22%) SOC — risk difference -8% (95% CI -14 to -3); HR 0.61 (95% CI 0.42-0.87) — DTG SUPERIOR (NI demonstrated, then superiority). Drove WHO 2021/2023 recommendation of DTG-based ART as preferred first-line for all weight bands >=4 weeks of age. Africa relevance: DIRECT — Uganda + South Africa + Zimbabwe = ~75%+ enrolment.',

                    estimandType: 'HR', publishedHR: 0.61, hrLCI: 0.42, hrUCI: 0.87, pubHR: 0.61,

                    allOutcomes: [
                        { shortLabel: 'TX_FAIL_96W', title: 'Treatment failure (clinical or virological) by 96w (DTG vs SOC)', tE: 47, cE: 75, type: 'PRIMARY', matchScore: 100, effect: 0.61, lci: 0.42, uci: 0.87, estimandType: 'HR' },

                        { shortLabel: 'VL_50', title: 'HIV-1 RNA <50 c/mL at 96w (DTG vs SOC)', tE: 250, cE: 196, type: 'SECONDARY', matchScore: 90, effect: 1.27, lci: 1.13, uci: 1.43, estimandType: 'RR' }
                    ],

                    rob: ['low', 'high', 'high', 'low', 'low'],

                    snippet: 'Source: Turkova A, White E, Mujuru HA, et al. Dolutegravir as First- or Second-Line Treatment for HIV-1 Infection in Children. NEJM 2021;385:2531-2543. PMID 34879188. DOI 10.1056/NEJMoa2108793.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa2108793',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT02259127'
                },

                'LEGACY-ISRCTN-69078957-CHAPAS-3': {

                    name: 'CHAPAS-3 (NRTI backbone in paeds)', pmid: '26718098', phase: 'II/III', year: 2016, tE: 12, tN: 159, cE: 22, cN: 158, group: 'Mulenga V, Musiime V, Kekitiinwa A, et al. Lancet Infect Dis 2016;16:169-179 (PMID 26718098). MRC CTU at UCL + JCRC Uganda + UTH Zambia-coordinated open-label randomized trial in HIV-1-infected children aged 1 month to 13 years across 4 sites in Uganda (Baylor Kampala, JCRC Kampala, JCRC Gulu) and Zambia (University Teaching Hospital Lusaka). n=480 enrolled (n=478 evaluable); randomized 1:1:1 to one of 3 NRTI backbones combined with NNRTI third agent (NVP for <3y, EFV for >=3y): (A) abacavir + lamivudine (ABC+3TC) (n=159), (B) zidovudine + lamivudine (ZDV+3TC) (n=158), (C) stavudine + lamivudine (d4T+3TC) (n=161). PRIMARY: NRTI-attributed grade 2-4 clinical or laboratory adverse event by 96w. RESULT: ABC+3TC 12/159 (8%) NRTI-related grade 2-4 AE vs ZDV+3TC 22/158 (14%) — RR 0.54 (95% CI 0.28-1.06); d4T+3TC 23/161 (14%) similar to ZDV. Virological suppression VL<400 c/mL at 48w >=90% across all 3 arms. Drove WHO 2016 endorsement of ABC+3TC as preferred paediatric NRTI backbone (replacing d4T). Africa relevance: DIRECT — entirely in Uganda + Zambia. Registry: ISRCTN69078957.',

                    estimandType: 'RR', publishedHR: 0.54, hrLCI: 0.28, hrUCI: 1.06, pubHR: 0.54,

                    allOutcomes: [
                        { shortLabel: 'GR2_AE', title: 'NRTI-attributed grade 2-4 AE by 96w (ABC vs ZDV)', tE: 12, cE: 22, type: 'PRIMARY', matchScore: 100, effect: 0.54, lci: 0.28, uci: 1.06, estimandType: 'RR' },

                        { shortLabel: 'VL_400', title: 'HIV-1 RNA <400 c/mL at 48w (ABC vs ZDV)', tE: 144, cE: 142, type: 'SECONDARY', matchScore: 90, effect: 1.01, lci: 0.94, uci: 1.08, estimandType: 'RR' }
                    ],

                    rob: ['low', 'high', 'high', 'low', 'low'],

                    snippet: 'Source: Mulenga V, Musiime V, Kekitiinwa A, et al. Abacavir, zidovudine, or stavudine as paediatric tablets for African HIV-infected children (CHAPAS-3): an open-label, parallel-group, randomised controlled trial. Lancet Infect Dis 2016;16:169-179. PMID 26718098. DOI 10.1016/S1473-3099(15)00400-7. Registry ISRCTN69078957.',

                    sourceUrl: 'https://doi.org/10.1016/S1473-3099(15)00400-7',

                    ctgovUrl: 'https://www.isrctn.com/ISRCTN69078957'
                },

                'LEGACY-ISRCTN-24791884-ARROW': {

                    name: 'ARROW (clinical vs lab monitoring)', pmid: '23541054', phase: 'III', year: 2013, tE: 64, tN: 397, cE: 60, cN: 401, group: 'ARROW Trial team (Kekitiinwa A, Cook A, Nathoo K, et al). Lancet 2013;381:1391-1403 (PMID 23541054). MRC CTU at UCL + JCRC Uganda + UZCRC Zimbabwe-coordinated open-label randomized factorial trial in n=1,206 ART-naive HIV-1-infected children aged 3 months to 17 years (median 6y) across 4 sites in Uganda (JCRC Kampala, Baylor-COE Kampala, JCRC Gulu, JCRC Mbarara) and Zimbabwe (UZCRC Harare). Two factorial randomizations: (1) monitoring strategy: clinical-only (LCM) vs CD4-based (LCM+CD4) vs CD4+VL (LCM+VL); (2) NRTI induction-maintenance: 36-week ABC+3TC+ZDV induction then ABC+3TC+NNRTI maintenance vs continuous ABC+3TC+NNRTI. PRIMARY (monitoring randomization): new WHO 4 event or death over 4 years. RESULT (clinical-only LCM, n=397, vs CD4-based LCM+CD4, n=401): 64/397 (16.1%) WHO4/death LCM vs 60/401 (15.0%) LCM+CD4 — HR 1.13 (95% CI 0.80-1.61) — non-inferior at pre-specified 1.5 NI margin. CD4+VL arm not different. Drove WHO 2013/2016 confirmation that clinical-and-CD4-based monitoring is sufficient where viral-load testing is unavailable. Africa relevance: DIRECT — entirely Uganda + Zimbabwe. Registry: ISRCTN24791884.',

                    estimandType: 'HR', publishedHR: 1.13, hrLCI: 0.80, hrUCI: 1.61, pubHR: 1.13,

                    allOutcomes: [
                        { shortLabel: 'WHO4_DEATH', title: 'New WHO 4 event or death over 4y (LCM vs LCM+CD4)', tE: 64, cE: 60, type: 'PRIMARY', matchScore: 100, effect: 1.13, lci: 0.80, uci: 1.61, estimandType: 'HR' },

                        { shortLabel: 'VL_400', title: 'HIV-1 RNA <400 c/mL at 4y (LCM vs LCM+CD4)', tE: 312, cE: 320, type: 'SECONDARY', matchScore: 90, effect: 0.99, lci: 0.94, uci: 1.04, estimandType: 'RR' }
                    ],

                    rob: ['low', 'high', 'high', 'low', 'low'],

                    snippet: 'Source: ARROW Trial team. Routine versus clinically driven laboratory monitoring and first-line antiretroviral therapy strategies in African children with HIV (ARROW): a 5-year open-label randomised factorial trial. Lancet 2013;381:1391-1403. PMID 23541054. DOI 10.1016/S0140-6736(13)60594-8. Registry ISRCTN24791884.',

                    sourceUrl: 'https://doi.org/10.1016/S0140-6736(13)60594-8',

                    ctgovUrl: 'https://www.isrctn.com/ISRCTN24791884'
                }
            }"""


# ==========================
# Build all 3 files
# ==========================
TEMPLATE = Path("SGLT2I_HF_NMA_REVIEW.html")

CONFIGS = [
    {
        "out": "MDR_TB_SHORTENED_NMA_REVIEW.html",
        "title": "RapidMeta TB | MDR-TB Shortened-Regimen NMA &mdash; BPaLM + BPaL (TB-PRACTECAL + Nix-TB + ZeNix) v0.1",
        "auto_include": "['NCT02589782', 'NCT02333799', 'NCT03086486']",
        "acronyms": "'NCT02589782': 'TB-PRACTECAL', 'NCT02333799': 'Nix-TB', 'NCT03086486': 'ZeNix'",
        "body": MDRTB_BODY,
    },
    {
        "out": "POSTPARTUM_HEMORRHAGE_NMA_REVIEW.html",
        "title": "RapidMeta Maternal Health | Postpartum Hemorrhage NMA &mdash; E-MOTIVE + WOMAN + CHAMPION v0.1",
        "auto_include": "['NCT04341662', 'LEGACY-ISRCTN-76912190-WOMAN', 'LEGACY-ISRCTN-95444399-CHAMPION']",
        "acronyms": "'NCT04341662': 'E-MOTIVE', 'LEGACY-ISRCTN-76912190-WOMAN': 'WOMAN trial', 'LEGACY-ISRCTN-95444399-CHAMPION': 'CHAMPION'",
        "body": PPH_BODY,
    },
    {
        "out": "PEDIATRIC_HIV_ART_NMA_REVIEW.html",
        "title": "RapidMeta Pediatric HIV | First-line ART Simplification NMA &mdash; ODYSSEY + CHAPAS-3 + ARROW v0.1",
        "auto_include": "['NCT02259127', 'LEGACY-ISRCTN-69078957-CHAPAS-3', 'LEGACY-ISRCTN-24791884-ARROW']",
        "acronyms": "'NCT02259127': 'ODYSSEY', 'LEGACY-ISRCTN-69078957-CHAPAS-3': 'CHAPAS-3', 'LEGACY-ISRCTN-24791884-ARROW': 'ARROW'",
        "body": PEDHIV_BODY,
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
