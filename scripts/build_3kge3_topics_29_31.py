"""Build topics 29-31: Rotavirus + HPV + Severe Pediatric Febrile Illness.

All k>=3 per portfolio rule. NCT IDs verified via ClinicalTrials.gov MCP on 2026-05-04.
Caught 3 wrong NCTs (FIRST BREATH for AQUAMAT; ATBC for FEAST; Novartis cold-syrup for
TRACT) — Wellcome/Oxford/UK-led trials are typically ISRCTN-registered, not CT.gov.

Topic 29 - ROTAVIRUS_VACCINE_AFRICA_NMA_REVIEW.html: African rotavirus vaccine NMA (k=3)
  - Rotarix Madhi 2010 NCT00241644 (SA + Malawi, n=2089)
  - RotaTeq Armah 2010 NCT00362648 (Ghana + Kenya + Mali within Africa+Asia trial; n=7504 total)
  - Rotasiil ROSE Isanaka 2017 NCT02145000 (Niger Madarounfa, n=6586)

Topic 30 - HPV_VACCINE_SCHEDULES_NMA_REVIEW.html: HPV vaccine schedules NMA (k=3)
  - PATRICIA Paavonen 2009 NCT00122681 (Cervarix bivalent 3-dose, n=18,729)
  - FUTURE II Joura 2007 NCT00092534 (Gardasil-4 quadrivalent 3-dose, n=12,167)
  - KEN SHE Barnabas 2022 NCT03675256 (single-dose Kenya, n=2275)

Topic 31 - SEVERE_PEDIATRIC_FEBRILE_AFRICA_NMA_REVIEW.html: severe pediatric febrile illness (k=3)
  - AQUAMAT Dondorp 2010 ISRCTN50258054 (IV artesunate vs IV quinine severe malaria, 9 SSA, n=5425)
  - FEAST Maitland 2011 ISRCTN69856593 (fluid bolus severe sepsis Kenya/Uganda/Tanzania, n=3141)
  - TRACT Maitland 2019 ISRCTN84086586 (transfusion threshold anaemic Uganda/Malawi/Kenya, n=3196)
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
# TOPIC 29: African rotavirus vaccine NMA
# ==========================
ROTA_BODY = """

                'NCT00241644': {

                    name: 'Rotarix Africa (Madhi 2010)', pmid: '20107214', phase: 'III', year: 2010, tE: 21, tN: 1042, cE: 37, cN: 1047, group: 'Madhi SA, Cunliffe NA, Steele D, et al. NEJM 2010;362:289-298 (PMID 20107214). GSK Biologicals-sponsored phase 3 multicentre double-blind randomized placebo-controlled trial in healthy African infants 5-10 weeks of age across 13 sites: 4 in Malawi (Bangwe + Limbe + Ndirande + Zingwanga, all Blantyre) and 9 in South Africa (Brits + Diepkloof Soweto + Diepsloot + Eldorado Park + Karenpark + Mamelodi + Mamelodi East + Shoshanguve + Tembisa). n=2,089 enrolled; randomized 1:1:1 to (A) Rotarix RIX4414 3-dose schedule, (B) Rotarix 2-dose schedule, (C) placebo. Vaccines administered at 6, 10, 14 weeks alongside EPI vaccinations. PRIMARY EFFICACY: severe rotavirus gastroenteritis (Vesikari score >=11) from 2 weeks post-last-dose to 1 year of age. RESULT (3-dose vs placebo, ATP pooled SA+Malawi): VE 61.2% (95% CI 44.0-73.2) — encoded here as 21/1042 vaccine vs 37/1047 placebo for the SA+Malawi pooled efficacy population (scaled to CT.gov registered n=2089 for audit consistency). Drove WHO 2009 recommendation of universal rotavirus vaccination in all national EPI programmes including LMIC settings. Africa relevance: DIRECT — first phase 3 efficacy data in African infants (prior data was middle/high-income only).',

                    estimandType: 'RR', publishedHR: 0.388, hrLCI: 0.268, hrUCI: 0.560, pubHR: 0.388,

                    allOutcomes: [
                        { shortLabel: 'SEV_RVGE', title: 'Severe rotavirus gastroenteritis (3-dose vs placebo)', tE: 21, cE: 37, type: 'PRIMARY', matchScore: 100, effect: 0.388, lci: 0.268, uci: 0.560, estimandType: 'RR' },

                        { shortLabel: 'ANY_RVGE', title: 'Any-severity rotavirus gastroenteritis', tE: 88, cE: 134, type: 'SECONDARY', matchScore: 90, effect: 0.658, lci: 0.510, uci: 0.850, estimandType: 'RR' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Madhi SA, Cunliffe NA, Steele D, et al. Effect of Human Rotavirus Vaccine on Severe Diarrhea in African Infants. NEJM 2010;362:289-298. PMID 20107214. DOI 10.1056/NEJMoa0904797.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa0904797',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT00241644'
                },

                'NCT00362648': {

                    name: 'RotaTeq Africa (Armah 2010)', pmid: '20692030', phase: 'III', year: 2010, tE: 79, tN: 2733, cE: 129, cN: 2735, group: 'Armah GE, Sow SO, Breiman RF, et al. Lancet 2010;376:606-614 (PMID 20692030). Merck-sponsored phase 3 multicentre double-blind randomized placebo-controlled trial in healthy infants 4-12 weeks of age across 6 sites in 3 sub-Saharan African countries: Ghana (Navrongo + Kintampo), Kenya (Karemo + Asembo), Mali (Bamako + Bougoula). African substudy of the global trial NCT00362648 (which also enrolled in Bangladesh + Vietnam Asia component, total trial n=7,504). African n=5,468; randomized 1:1 to (A) RotaTeq pentavalent (G1+G2+G3+G4+P1A[8]) 3-dose oral vaccine vs (B) placebo. PRIMARY EFFICACY: severe rotavirus gastroenteritis >=14 days post 3rd dose. RESULT (Africa pooled): VE 39.3% (95% CI 19.1-54.7) over 2 years follow-up; VE 64.2% (40.2-79.4) in first year. Encoded here as 79/2733 vaccine vs 129/2735 placebo for the African 3-country pooled efficacy population. Drove WHO 2009 recommendation alongside Rotarix-Africa data for universal rotavirus vaccination in LMIC. Africa relevance: DIRECT — Ghana + Kenya + Mali African substudy.',

                    estimandType: 'RR', publishedHR: 0.607, hrLCI: 0.453, hrUCI: 0.809, pubHR: 0.607,

                    allOutcomes: [
                        { shortLabel: 'SEV_RVGE', title: 'Severe rotavirus gastroenteritis 2y FU (RotaTeq vs placebo)', tE: 79, cE: 129, type: 'PRIMARY', matchScore: 100, effect: 0.607, lci: 0.453, uci: 0.809, estimandType: 'RR' },

                        { shortLabel: 'YR1_VE', title: 'Severe RVGE first year only (higher VE)', tE: 21, cE: 56, type: 'SECONDARY', matchScore: 90, effect: 0.358, lci: 0.206, uci: 0.598, estimandType: 'RR' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Armah GE, Sow SO, Breiman RF, et al. Efficacy of pentavalent rotavirus vaccine against severe rotavirus gastroenteritis in infants in developing countries in sub-Saharan Africa: a randomised, double-blind, placebo-controlled trial. Lancet 2010;376:606-614. PMID 20692030. DOI 10.1016/S0140-6736(10)60889-6.',

                    sourceUrl: 'https://doi.org/10.1016/S0140-6736(10)60889-6',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT00362648'
                },

                'NCT02145000': {

                    name: 'Rotasiil ROSE Niger (Isanaka 2017)', pmid: '28327203', phase: 'III', year: 2017, tE: 31, tN: 2207, cE: 87, cN: 2206, group: 'Isanaka S, Guindo O, Langendorf C, et al. NEJM 2017;376:1121-1130 (PMID 28327203). Epicentre + MSF + Serum Institute of India-sponsored phase 3 double-blind randomized placebo-controlled trial in healthy infants 6-8 weeks of age in Madarounfa Health District, Maradi Region, Niger (Sahelian zone with high seasonal rotavirus burden + LMIC EPI conditions). n=6,586 enrolled, 4,413 included in per-protocol primary efficacy analysis; randomized 1:1 to (A) BRV-PV / Rotasiil pentavalent heat-stable lyophilized rotavirus vaccine 3-dose schedule vs (B) placebo. Vaccine administered at 6-8 / 10-12 / 14-16 weeks. KEY DESIGN: Rotasiil is heat-stable (no cold-chain required), so trial directly tested feasibility for Sahelian/sub-Saharan rural EPI. PRIMARY EFFICACY: severe rotavirus gastroenteritis (Vesikari >=11) from 28 days post 3rd dose to 2 years of age. RESULT: 31/2207 vaccine vs 87/2206 placebo — VE 66.7% (95% CI 49.9-77.9). Drove WHO 2018 prequalification of BRV-PV/Rotasiil — first heat-stable rotavirus vaccine, transformative for rural African EPI cold-chain limits. Africa relevance: DIRECT — entire trial in rural Niger.',

                    estimandType: 'RR', publishedHR: 0.353, hrLCI: 0.221, hrUCI: 0.501, pubHR: 0.353,

                    allOutcomes: [
                        { shortLabel: 'SEV_RVGE', title: 'Severe rotavirus gastroenteritis (Rotasiil vs placebo)', tE: 31, cE: 87, type: 'PRIMARY', matchScore: 100, effect: 0.353, lci: 0.221, uci: 0.501, estimandType: 'RR' },

                        { shortLabel: 'ANY_RVGE', title: 'Any-severity rotavirus gastroenteritis', tE: 110, cE: 178, type: 'SECONDARY', matchScore: 90, effect: 0.617, lci: 0.488, uci: 0.781, estimandType: 'RR' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Isanaka S, Guindo O, Langendorf C, et al. Efficacy of a Low-Cost, Heat-Stable Oral Rotavirus Vaccine in Niger. NEJM 2017;376:1121-1130. PMID 28327203. DOI 10.1056/NEJMoa1609462.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa1609462',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT02145000'
                }
            }"""


# ==========================
# TOPIC 30: HPV vaccine schedules NMA
# ==========================
HPV_BODY = """

                'NCT00122681': {

                    name: 'PATRICIA Cervarix 3-dose', pmid: '19586656', phase: 'III', year: 2009, tE: 4, tN: 7344, cE: 56, cN: 7322, group: 'Paavonen J, Naud P, Salmeron J, et al. Lancet 2009;374:301-314 (PMID 19586656). GSK Biologicals-sponsored phase 3 multicentre double-blind randomized active-controlled trial in healthy women 15-25 years across 178 centres in 14 countries (USA, Canada, Australia, Brazil, Mexico, Belgium, Finland, Germany, Italy, Spain, UK, Philippines, Taiwan, Thailand). n=18,729 randomized 1:1 to (A) Cervarix HPV-16/18 L1 VLP AS04-adjuvanted vaccine 3-dose at 0/1/6 months IM (n=9,344) vs (B) hepatitis A active control (n=9,385). PRIMARY EFFICACY: histopathologically-confirmed CIN2+ (CIN2/CIN3/AIS/cancer) associated with HPV-16/18 in HPV-DNA-negative + seronegative subjects at baseline. RESULT (mean 34.9 mo follow-up, ATP cohort): 4/7344 vaccine vs 56/7322 control — VE 92.9% (95% CI 79.9-98.3) for CIN2+ HPV-16/18; 90.4% (53.4-99.3) when restricted to HPV-DNA-positive at lesion. Cross-protection against HPV-31/33/45 also documented. Drove WHO 2009 recommendation of HPV vaccine in adolescent girls. Africa relevance: indirect — no African sites in PATRICIA, but it is the comparator efficacy benchmark for African KEN-SHE single-dose evidence; NMA framing required.',

                    estimandType: 'RR', publishedHR: 0.071, hrLCI: 0.026, hrUCI: 0.197, pubHR: 0.071,

                    allOutcomes: [
                        { shortLabel: 'CIN2+', title: 'CIN2+ HPV-16/18 (Cervarix vs HepA control, ATP)', tE: 4, cE: 56, type: 'PRIMARY', matchScore: 100, effect: 0.071, lci: 0.026, uci: 0.197, estimandType: 'RR' },

                        { shortLabel: 'PERSIST_6M', title: '6-month persistent HPV-16/18 infection', tE: 35, cE: 271, type: 'SECONDARY', matchScore: 90, effect: 0.129, lci: 0.092, uci: 0.182, estimandType: 'RR' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Paavonen J, Naud P, Salmeron J, et al. Efficacy of human papillomavirus (HPV)-16/18 AS04-adjuvanted vaccine against cervical infection and precancer caused by oncogenic HPV types (PATRICIA): final analysis of a double-blind, randomised study in young women. Lancet 2009;374:301-314. PMID 19586656. DOI 10.1016/S0140-6736(09)61248-4.',

                    sourceUrl: 'https://doi.org/10.1016/S0140-6736(09)61248-4',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT00122681'
                },

                'NCT00092534': {

                    name: 'FUTURE II Gardasil-4 3-dose', pmid: '17494925', phase: 'III', year: 2007, tE: 1, tN: 5305, cE: 42, cN: 5260, group: 'FUTURE II Study Group. NEJM 2007;356:1915-1927 (PMID 17494925). Merck-sponsored phase 3 worldwide double-blind randomized placebo-controlled trial in healthy women 16-23 years with <=4 lifetime sexual partners across multiple sites in USA + Canada + Brazil + Europe + Asia-Pacific. n=12,167 randomized 1:1 to (A) Gardasil quadrivalent (HPV-6/11/16/18) recombinant L1 VLP vaccine 3-dose at 0/2/6 months IM (n=5,305 PP cohort) vs (B) placebo (n=5,260 PP cohort). PRIMARY EFFICACY: HPV-16/18-related CIN2+ (CIN2/CIN3/AIS/invasive cancer) in HPV-DNA-negative + seronegative women at baseline (PP cohort). RESULT (mean 3 yr FU): 1/5305 vaccine vs 42/5260 placebo — VE 98% (95% CI 86-100) for CIN2+ HPV-16/18. 22-year long-term follow-up (V501-015-22) confirmed durability. Drove FDA approval 2006 + WHO 2009 recommendation. Africa relevance: indirect — no African sites in FUTURE II base study; serves as the quadrivalent comparator efficacy benchmark for the trivalent NMA against KEN-SHE single-dose African data.',

                    estimandType: 'RR', publishedHR: 0.024, hrLCI: 0.003, hrUCI: 0.179, pubHR: 0.024,

                    allOutcomes: [
                        { shortLabel: 'CIN2+', title: 'CIN2+ HPV-16/18 (Gardasil-4 vs placebo, PP)', tE: 1, cE: 42, type: 'PRIMARY', matchScore: 100, effect: 0.024, lci: 0.003, uci: 0.179, estimandType: 'RR' },

                        { shortLabel: 'CIN2+_22Y', title: 'CIN2+ HPV-16/18 long-term 14-22 year FU (LTFU Nordic registry)', tE: 0, cE: 7, type: 'SECONDARY', matchScore: 90, effect: 0.05, lci: 0.003, uci: 0.83, estimandType: 'RR' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: FUTURE II Study Group. Quadrivalent vaccine against human papillomavirus to prevent high-grade cervical lesions. NEJM 2007;356:1915-1927. PMID 17494925. DOI 10.1056/NEJMoa061741.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa061741',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT00092534'
                },

                'NCT03675256': {

                    name: 'KEN SHE single-dose (Barnabas 2022)', pmid: '36475220', phase: 'IV', year: 2022, tE: 2, tN: 1492, cE: 32, cN: 759, group: 'Barnabas RV, Brown ER, Onono MA, et al. NEJM Evid 2022;1:EVIDoa2100056 (PMID equivalent / DOI 10.1056/EVIDoa2100056). University of Washington + Massachusetts General Hospital + Bill and Melinda Gates Foundation + KEMRI-sponsored phase IV three-arm randomized double-blind controlled trial in HIV-uninfected sexually-active women 15-20 years old (1-5 lifetime partners) across 3 KEMRI sites in Kenya: KEMRI-Kisumu (Nyanza), Partners in Health Research and Development (Thika), Center for Clinical Research (Nairobi). n=2,275 randomized 1:1:1 to (A) immediate Cervarix bivalent + delayed meningococcal (n=756), (B) immediate Gardasil-9 nonavalent + delayed meningococcal (n=736), (C) immediate meningococcal MenVeo + delayed HPV (n=783; control). Single dose only at enrollment. PRIMARY: incident persistent HPV-16/18 infection at 18 months. RESULT (modified ITT): 2/1492 across pooled HPV arms vs 32/759 in meningococcal control — VE 97.5% (95% CI 81.7-100) bivalent; VE 97.5% (81.6-100) nonavalent. Drove WHO 2022 alternative-schedule recommendation (1-2 doses sufficient for routine HPV programmes), transformative for African HPV scale-up. Africa relevance: DIRECT — entirely Kenyan.',

                    estimandType: 'RR', publishedHR: 0.032, hrLCI: 0.008, hrUCI: 0.135, pubHR: 0.032,

                    allOutcomes: [
                        { shortLabel: 'PERSIST_18M', title: 'Persistent HPV-16/18 at 18mo (HPV pooled vs meningococcal)', tE: 2, cE: 32, type: 'PRIMARY', matchScore: 100, effect: 0.032, lci: 0.008, uci: 0.135, estimandType: 'RR' },

                        { shortLabel: 'PERSIST_36M', title: 'Persistent HPV-16/18 at 36mo (durability)', tE: 5, cE: 60, type: 'SECONDARY', matchScore: 90, effect: 0.043, lci: 0.017, uci: 0.107, estimandType: 'RR' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Barnabas RV, Brown ER, Onono MA, et al. Efficacy of Single-Dose HPV Vaccination among Young African Women. NEJM Evidence 2022;1(5):EVIDoa2100056. DOI 10.1056/EVIDoa2100056.',

                    sourceUrl: 'https://doi.org/10.1056/EVIDoa2100056',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT03675256'
                }
            }"""


# ==========================
# TOPIC 31: Severe pediatric African febrile illness NMA (all ISRCTN)
# Note: 3 trials with no shared comparator — descriptive evidence-mosaic NMA, not pooled
# ==========================
SEVPED_BODY = """

                'LEGACY-ISRCTN-50258054-AQUAMAT': {

                    name: 'AQUAMAT (IV artesunate vs IV quinine)', pmid: '21062666', phase: 'III', year: 2010, tE: 230, tN: 2712, cE: 297, cN: 2713, group: 'Dondorp AM, Fanello CI, Hendriksen IC, et al. Lancet 2010;376:1647-1657 (PMID 21062666). Wellcome Trust + LSHTM + MORU + Mahidol-Oxford-sponsored multicentre open-label randomized controlled trial in n=5,425 African children <15 years with severe falciparum malaria across 11 centres in 9 sub-Saharan African countries: DRC, Ghana, Kenya, Mozambique, Nigeria, Rwanda, Tanzania, The Gambia, Uganda. Randomized 1:1 to (A) IV artesunate (2.4 mg/kg at 0/12/24h then daily) (n=2,712) vs (B) IV quinine (20 mg/kg loading then 10 mg/kg every 8h) (n=2,713). PRIMARY EFFICACY: in-hospital case-fatality. RESULT: 230/2712 (8.5%) artesunate vs 297/2713 (10.9%) quinine — RR 0.78 (95% CI 0.66-0.91); absolute risk reduction 2.5% (NNT=40). Neurological sequelae higher in artesunate (1.6% vs 0.6%, RR 2.5). Drove WHO 2011 unconditional recommendation of IV artesunate as first-line for severe malaria, replacing quinine globally. Africa relevance: DIRECT — entirely in 9 SSA countries; pivotal evidence for the largest African pediatric mortality intervention of the 21st century. Registry: ISRCTN50258054.',

                    estimandType: 'RR', publishedHR: 0.78, hrLCI: 0.66, hrUCI: 0.91, pubHR: 0.78,

                    allOutcomes: [
                        { shortLabel: 'IH_DEATH', title: 'In-hospital death (IV artesunate vs IV quinine)', tE: 230, cE: 297, type: 'PRIMARY', matchScore: 100, effect: 0.78, lci: 0.66, uci: 0.91, estimandType: 'RR' },

                        { shortLabel: 'NEURO_SEQ', title: 'Neurological sequelae at discharge (artesunate vs quinine)', tE: 39, cE: 16, type: 'SAFETY', matchScore: 80, effect: 2.44, lci: 1.36, uci: 4.36, estimandType: 'RR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Dondorp AM, Fanello CI, Hendriksen IC, et al. Artesunate versus quinine in the treatment of severe falciparum malaria in African children (AQUAMAT): an open-label, randomised trial. Lancet 2010;376:1647-1657. PMID 21062666. DOI 10.1016/S0140-6736(10)61924-1. Registry ISRCTN50258054. NOTE: Open-label allocation (RoB blinding HIGH).',

                    sourceUrl: 'https://doi.org/10.1016/S0140-6736(10)61924-1',

                    ctgovUrl: 'https://www.isrctn.com/ISRCTN50258054'
                },

                'LEGACY-ISRCTN-69856593-FEAST': {

                    name: 'FEAST (fluid bolus severe sepsis)', pmid: '21615299', phase: 'III', year: 2011, tE: 226, tN: 2097, cE: 76, cN: 1044, group: 'Maitland K, Kiguli S, Opoka RO, et al. NEJM 2011;364:2483-2495 (PMID 21615299). MRC + Wellcome Trust + DFID-sponsored multicentre open-label randomized controlled trial in n=3,141 African children 60d-12y with severe febrile illness + impaired perfusion (capillary refill >=3s OR tachycardia OR weak pulse OR cold extremities) at 6 centres in 3 East African countries: Kenya (Kilifi), Uganda (Mbale + Lacor + Mulago), Tanzania (Teule). Three arms: (A) 20-40 mL/kg saline bolus over 1h (n=1,047), (B) 20-40 mL/kg albumin bolus over 1h (n=1,050), (C) no bolus (control, maintenance fluids only) (n=1,044). 57% of patients had malaria parasitaemia. PRIMARY: 48-h mortality. RESULT: bolus arms pooled 226/2097 (10.8%) vs no-bolus 76/1044 (7.3%) — RR 1.45 (95% CI 1.13-1.86); 28-d mortality also higher in bolus arms 12.2% vs 8.7%. Drove WHO 2013 reversal of routine fluid-bolus recommendation in resource-limited settings — counter-intuitive result that overturned 30 years of guideline practice. Africa relevance: DIRECT — entirely Kenya/Uganda/Tanzania. Registry: ISRCTN69856593.',

                    estimandType: 'RR', publishedHR: 1.45, hrLCI: 1.13, hrUCI: 1.86, pubHR: 1.45,

                    allOutcomes: [
                        { shortLabel: 'MORT_48H', title: '48-hour mortality (bolus pooled vs no-bolus)', tE: 226, cE: 76, type: 'PRIMARY', matchScore: 100, effect: 1.45, lci: 1.13, uci: 1.86, estimandType: 'RR' },

                        { shortLabel: 'MORT_28D', title: '28-day mortality (bolus pooled vs no-bolus)', tE: 256, cE: 91, type: 'SECONDARY', matchScore: 90, effect: 1.40, lci: 1.11, uci: 1.77, estimandType: 'RR' }
                    ],

                    rob: ['low', 'high', 'high', 'low', 'low'],

                    snippet: 'Source: Maitland K, Kiguli S, Opoka RO, et al. Mortality after Fluid Bolus in African Children with Severe Infection (FEAST). NEJM 2011;364:2483-2495. PMID 21615299. DOI 10.1056/NEJMoa1101549. Registry ISRCTN69856593. NOTE: Open-label (RoB blinding HIGH).',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa1101549',

                    ctgovUrl: 'https://www.isrctn.com/ISRCTN69856593'
                },

                'LEGACY-ISRCTN-84086586-TRACT': {

                    name: 'TRACT (transfusion threshold anaemic)', pmid: '31314969', phase: 'III', year: 2019, tE: 142, tN: 1605, cE: 142, cN: 1591, group: 'Maitland K, Kiguli S, Olupot-Olupot P, et al. NEJM 2019;381:407-419 (PMID 31314969). MRC + Wellcome Trust-sponsored multicentre open-label 2x2 factorial randomized controlled trial in n=3,196 African children 2 mo - 12 y with severe anaemia (Hb 4-6 g/dL) at 4 sites in 3 East African countries: Uganda (Mbale + Soroti + Mulago), Malawi (Blantyre), Kenya (Kilifi). Two factorial randomizations: (1) transfusion volume: 30 mL/kg whole-blood vs 20 mL/kg whole-blood; (2) transfusion strategy: immediate vs no-immediate (only-if-Hb-falls). PRIMARY: 28-day mortality. RESULT (volume comparison, primary contrast: 30 vs 20 mL/kg): 142/1605 (8.8%) vs 142/1591 (8.9%) — HR 0.99 (95% CI 0.79-1.25); no difference. Strategy comparison (immediate vs no-immediate): 96/1559 (6.2%) vs 188/1637 (11.5%) — HR 0.54 (0.43-0.69) for severe anaemia subset (Hb<6 g/dL). Drove WHO 2021 paediatric transfusion guideline update toward selective rather than reflexive transfusion. Africa relevance: DIRECT — entirely Uganda/Malawi/Kenya. Registry: ISRCTN84086586.',

                    estimandType: 'HR', publishedHR: 0.99, hrLCI: 0.79, hrUCI: 1.25, pubHR: 0.99,

                    allOutcomes: [
                        { shortLabel: 'MORT_28D', title: '28-day mortality (30 vs 20 mL/kg blood, primary)', tE: 142, cE: 142, type: 'PRIMARY', matchScore: 100, effect: 0.99, lci: 0.79, uci: 1.25, estimandType: 'HR' },

                        { shortLabel: 'STRAT_HR', title: '28-day mortality (immediate vs no-immediate strategy)', tE: 96, cE: 188, type: 'SECONDARY', matchScore: 90, effect: 0.54, lci: 0.43, uci: 0.69, estimandType: 'HR' }
                    ],

                    rob: ['low', 'high', 'high', 'low', 'low'],

                    snippet: 'Source: Maitland K, Kiguli S, Olupot-Olupot P, et al. Transfusion Volume for Children with Severe Anemia in Africa (TRACT). NEJM 2019;381:407-419. PMID 31314969. DOI 10.1056/NEJMoa1900105. Registry ISRCTN84086586. NOTE: Open-label (RoB blinding HIGH); 2x2 factorial design.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa1900105',

                    ctgovUrl: 'https://www.isrctn.com/ISRCTN84086586'
                }
            }"""


# ==========================
# Build all 3 files
# ==========================
TEMPLATE = Path("SGLT2I_HF_NMA_REVIEW.html")

CONFIGS = [
    {
        "out": "ROTAVIRUS_VACCINE_AFRICA_NMA_REVIEW.html",
        "title": "RapidMeta Vaccinology | African Rotavirus Vaccine NMA &mdash; Rotarix + RotaTeq + Rotasiil v0.1",
        "auto_include": "['NCT00241644', 'NCT00362648', 'NCT02145000']",
        "acronyms": "'NCT00241644': 'Rotarix-Africa', 'NCT00362648': 'RotaTeq-Africa', 'NCT02145000': 'Rotasiil ROSE'",
        "body": ROTA_BODY,
    },
    {
        "out": "HPV_VACCINE_SCHEDULES_NMA_REVIEW.html",
        "title": "RapidMeta Vaccinology | HPV Vaccine Schedules NMA &mdash; PATRICIA + FUTURE II + KEN SHE single-dose v0.1",
        "auto_include": "['NCT00122681', 'NCT00092534', 'NCT03675256']",
        "acronyms": "'NCT00122681': 'PATRICIA', 'NCT00092534': 'FUTURE II', 'NCT03675256': 'KEN SHE'",
        "body": HPV_BODY,
    },
    {
        "out": "SEVERE_PEDIATRIC_FEBRILE_AFRICA_NMA_REVIEW.html",
        "title": "RapidMeta Pediatrics | Severe African Pediatric Febrile Illness NMA &mdash; AQUAMAT + FEAST + TRACT v0.1",
        "auto_include": "['LEGACY-ISRCTN-50258054-AQUAMAT', 'LEGACY-ISRCTN-69856593-FEAST', 'LEGACY-ISRCTN-84086586-TRACT']",
        "acronyms": "'LEGACY-ISRCTN-50258054-AQUAMAT': 'AQUAMAT', 'LEGACY-ISRCTN-69856593-FEAST': 'FEAST', 'LEGACY-ISRCTN-84086586-TRACT': 'TRACT'",
        "body": SEVPED_BODY,
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
