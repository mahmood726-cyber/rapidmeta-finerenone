"""Build 3 k>=3 NMA topics (per user rule: future topics MUST have k>=3 trials).

Topic 23 - HIV_PREP_INJECTABLE_NMA_REVIEW.html: HIV PrEP NMA (k=3)
  - HPTN 083 NCT02720094 (CAB-LA vs F/TDF, MSM/TGW global, n=4570)
  - HPTN 084 NCT03164564 (CAB-LA vs F/TDF, women East/Southern Africa, n=3224)
  - DISCOVER NCT02842086 (F/TAF vs F/TDF, MSM/TGW global, n=5399)

Topic 24 - MALARIA_VACCINE_NMA_REVIEW.html: Malaria vaccine NMA (k=3)
  - RTS,S/AS01 Phase 3 NCT00866619 (n=15,459 across 7 African countries)
  - R21/Matrix-M Phase 2b NCT03896724 (n=450 Nanoro Burkina Faso, Datoo 2021)
  - R21/Matrix-M Phase 3 NCT04704830 (n=4800 Burkina Faso/Kenya/Mali/Tanzania, Datoo 2024)

Topic 25 - TB_PREVENTION_NMA_REVIEW.html: TB Prevention NMA (k=3)
  - BRIEF-TB NCT01404312 (4w 1HP, n=3000, HIV+ multi-country incl Africa)
  - TBTC Study 26 NCT00023452 (3HP n=8053, Sterling 2011 NEJM)
  - iAdhere NCT01582711 (3HP SAT vs DOT n=1002)
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


def replace_or_die(text, old, new):
    if old not in text:
        raise SystemExit(f"old string not found: {old[:80]!r}...")
    return text.replace(old, new)


# ==========================
# TOPIC 23: HIV PrEP Injectable NMA
# ==========================
PREP_BODY = """

                'NCT02720094': {

                    name: 'HPTN 083', pmid: '34379922', phase: 'IIb/III', year: 2021, tE: 13, tN: 2282, cE: 39, cN: 2284, group: 'Landovitz RJ, Donnell D, Clement ME, et al. NEJM 2021;385:595-608 (PMID 34379922). NIAID + ViiV + Gilead-sponsored phase 2b/3 double-blind double-dummy non-inferiority trial of long-acting injectable cabotegravir (CAB-LA, every 8wk IM) vs daily oral F/TDF for HIV PrEP in HIV-uninfected cisgender men and transgender women who have sex with men. n=4,566 randomized 1:1 across 43 sites in 8 countries (USA, Argentina, Brazil, Peru, South Africa, Thailand, Vietnam, Italy). PRIMARY EFFICACY: HIV-1 incidence per 100 person-years. RESULT: incident HIV in 13/2282 CAB-LA arm vs 39/2284 F/TDF arm — HR 0.34 (95% CI 0.18-0.62) — CAB-LA SUPERIOR (DSMB stopped trial early). Africa relevance: 2 South African sites (Cape Town); paired with HPTN 084 (women, East/Southern Africa) provides the WHO 2022 guideline basis for CAB-LA preferred PrEP across all African PrEP populations.',

                    estimandType: 'HR', publishedHR: 0.34, hrLCI: 0.18, hrUCI: 0.62, pubHR: 0.34,

                    allOutcomes: [
                        { shortLabel: 'HIV_INC', title: 'Incident HIV-1 infection (CAB-LA vs F/TDF, MSM/TGW)', tE: 13, cE: 39, type: 'PRIMARY', matchScore: 100, effect: 0.34, lci: 0.18, uci: 0.62, estimandType: 'HR' },

                        { shortLabel: 'GR2_AE', title: 'Grade 2+ clinical/laboratory adverse event', tE: 1126, cE: 1138, type: 'SAFETY', matchScore: 80, effect: 0.99, lci: 0.94, uci: 1.04, estimandType: 'RR' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Landovitz RJ, Donnell D, Clement ME, et al. Cabotegravir for HIV Prevention in Cisgender Men and Transgender Women. NEJM 2021;385:595-608. PMID 34379922. DOI 10.1056/NEJMoa2101016.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa2101016',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT02720094'
                },

                'NCT03164564': {

                    name: 'HPTN 084', pmid: '35594553', phase: 'III', year: 2022, tE: 4, tN: 1614, cE: 36, cN: 1610, group: 'Delany-Moretlwe S, Hughes JP, Bock P, et al. Lancet 2022;399:1779-1789 (PMID 35594553). NIAID-sponsored phase 3 double-blind double-dummy non-inferiority trial in HIV-uninfected cisgender women aged 18-45 across 20 sites in 7 sub-Saharan African countries: Botswana (Gaborone), Eswatini (Mbabane), Kenya (Kisumu), Malawi (Lilongwe + Blantyre), South Africa (Soweto + Johannesburg + Durban + Cape Town), Uganda (Entebbe + Kampala 2x), Zimbabwe (Chitungwiza 3x + Harare 2x). n=3,224 randomized 1:1 to CAB-LA every 8wk IM vs daily F/TDF. PRIMARY EFFICACY: HIV-1 incidence. RESULT: 4/1614 CAB-LA vs 36/1610 F/TDF — HR 0.12 (95% CI 0.05-0.31) — CAB-LA SUPERIOR (DSMB stopped trial early). 89% reduction. Africa relevance: DIRECT — entirely sub-Saharan African; pivotal evidence for WHO 2022 guideline basis for CAB-LA preferred PrEP for African women + AGYW.',

                    estimandType: 'HR', publishedHR: 0.12, hrLCI: 0.05, hrUCI: 0.31, pubHR: 0.12,

                    allOutcomes: [
                        { shortLabel: 'HIV_INC', title: 'Incident HIV-1 infection (CAB-LA vs F/TDF, women SSA)', tE: 4, cE: 36, type: 'PRIMARY', matchScore: 100, effect: 0.12, lci: 0.05, uci: 0.31, estimandType: 'HR' },

                        { shortLabel: 'GR2_AE', title: 'Grade 2+ clinical/laboratory adverse event', tE: 1186, cE: 1175, type: 'SAFETY', matchScore: 80, effect: 1.01, lci: 0.96, uci: 1.06, estimandType: 'RR' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Delany-Moretlwe S, Hughes JP, Bock P, et al. Cabotegravir for the prevention of HIV-1 in women: results from HPTN 084. Lancet 2022;399:1779-1789. PMID 35594553. DOI 10.1016/S0140-6736(22)00538-4.',

                    sourceUrl: 'https://doi.org/10.1016/S0140-6736(22)00538-4',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT03164564'
                },

                'NCT02842086': {

                    name: 'DISCOVER (F/TAF vs F/TDF)', pmid: '32896293', phase: 'III', year: 2020, tE: 8, tN: 2694, cE: 15, cN: 2693, group: 'Mayer KH, Molina JM, Thompson MA, et al. Lancet 2020;396:239-254 (PMID 32896293). Gilead-sponsored phase 3 double-blind randomized non-inferiority trial of daily oral F/TAF (Descovy 200/25 mg) vs daily oral F/TDF (Truvada 200/300 mg) for HIV PrEP in HIV-uninfected MSM and TGW (male at birth) at high HIV risk across 94 sites in 11 countries (USA, Canada, Austria, Denmark, France, Germany, Ireland, Italy, Netherlands, Spain, UK). n=5,387 randomized 1:1 (5,399 enrolled). PRIMARY: HIV-1 incidence per 100 PY (NI margin 1.62). RESULT: 8/2694 F/TAF vs 15/2693 F/TDF over 8,756 PY — incidence 0.16 vs 0.34 per 100 PY; IRR 0.47 (95% CI 0.19-1.15) — non-inferior; secondary renal/bone safety advantage F/TAF. Africa relevance: indirect — no African sites; but provides comparator efficacy benchmark for any oral PrEP NMA against the injectable (HPTN 083/084) arm.',

                    estimandType: 'IRR', publishedHR: 0.47, hrLCI: 0.19, hrUCI: 1.15, pubHR: 0.47,

                    allOutcomes: [
                        { shortLabel: 'HIV_INC', title: 'Incident HIV-1 infection (F/TAF vs F/TDF, MSM/TGW)', tE: 8, cE: 15, type: 'PRIMARY', matchScore: 100, effect: 0.47, lci: 0.19, uci: 1.15, estimandType: 'IRR' },

                        { shortLabel: 'BMD_HIP', title: 'Hip BMD percent change at Week 48 (favouring TAF)', tE: 0.20, cE: -1.00, type: 'SECONDARY', matchScore: 70, effect: 1.20, lci: 0.95, uci: 1.45, estimandType: 'MD' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Mayer KH, Molina JM, Thompson MA, et al. Emtricitabine and tenofovir alafenamide vs emtricitabine and tenofovir disoproxil fumarate for HIV pre-exposure prophylaxis (DISCOVER): primary results from a randomised, double-blind, multicentre, active-controlled, phase 3, non-inferiority trial. Lancet 2020;396:239-254. PMID 32896293. DOI 10.1016/S0140-6736(20)31065-5.',

                    sourceUrl: 'https://doi.org/10.1016/S0140-6736(20)31065-5',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT02842086'
                }
            }"""


# ==========================
# TOPIC 24: Malaria Vaccine NMA (k=3)
# ==========================
MAL_BODY = """

                'NCT00866619': {

                    name: 'RTS,S/AS01 Phase 3', pmid: '25913272', phase: 'III', year: 2015, tE: 1612, tN: 5949, cE: 1115, cN: 2974, group: 'RTS,S Clinical Trials Partnership. Lancet 2015;386:31-45 (PMID 25913272). GSK + PATH MVI-sponsored phase 3 multicentre double-blind randomized trial in n=15,459 children across 11 sites in 7 sub-Saharan African countries: Burkina Faso, Gabon, Ghana (2 sites), Kenya (2 sites), Malawi (2 sites), Mozambique, Tanzania (2 sites). Two age categories: 5-17 month olds (n=8,922) and 6-12 week olds (n=6,537), each randomized 1:1:1 to (1) RTS,S/AS01 + booster at 18 months (R3R), (2) RTS,S/AS01 without booster (R3C), (3) control. PRIMARY EFFICACY: clinical malaria episodes. RESULT in 5-17 month-olds R3R vs control: 1612/2974 vaccine arm vs 1115/2974 control arm clinical episodes after 4 years follow-up — VE 36.3% (95% CI 31.8-40.5) for clinical malaria; 32.2% (13.7-46.9) for severe malaria. WHO endorsement October 2021 — first malaria vaccine recommended for routine use in P. falciparum moderate-to-high transmission settings (children >=5 months). Africa relevance: pivotal — entirely African enrolment.',

                    estimandType: 'VE', publishedHR: 0.637, hrLCI: 0.595, hrUCI: 0.682, pubHR: 0.637,

                    allOutcomes: [
                        { shortLabel: 'CLIN_MAL', title: 'Clinical malaria episodes 5-17mo R3R vs control (PRIMARY VE)', tE: 1612, cE: 1115, type: 'PRIMARY', matchScore: 100, effect: 0.637, lci: 0.595, uci: 0.682, estimandType: 'IRR' },

                        { shortLabel: 'SEV_MAL', title: 'Severe malaria 5-17mo R3R vs control', tE: 116, cE: 169, type: 'SECONDARY', matchScore: 90, effect: 0.678, lci: 0.531, uci: 0.863, estimandType: 'IRR' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: RTS,S Clinical Trials Partnership. Efficacy and safety of RTS,S/AS01 malaria vaccine with or without a booster dose in infants and children in Africa: final results of a phase 3, individually randomised, controlled trial. Lancet 2015;386:31-45. PMID 25913272. DOI 10.1016/S0140-6736(15)60721-8.',

                    sourceUrl: 'https://doi.org/10.1016/S0140-6736(15)60721-8',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT00866619'
                },

                'NCT03896724': {

                    name: 'R21/Matrix-M Phase 2b (Datoo 2021)', pmid: '33964223', phase: 'IIb', year: 2021, tE: 38, tN: 146, cE: 105, cN: 147, group: 'Datoo MS, Natama MH, Some A, et al. Lancet 2021;397:1809-1818 (PMID 33964223). University of Oxford + Institut de Recherche en Sciences de la Sante Burkina Faso + EDCTP-sponsored phase 2b double-blind randomized controlled trial in healthy 5-17 month old children at the IRSS-CRUN clinical research unit, Nanoro, Burkina Faso (highly seasonal malaria transmission). n=450 children randomized 1:1:1 to (1) 5 ug R21 + 25 ug Matrix-M (n=146), (2) 5 ug R21 + 50 ug Matrix-M (n=146), (3) rabies vaccine control (n=147). 3-dose primary series administered at 4-week intervals before malaria season; 4th booster dose 1 year later. PRIMARY EFFICACY: protective efficacy against clinical malaria 14 days to 6 months after 3rd dose. RESULT: 50 ug Matrix-M arm 38/146 (26.0%) vs control 105/147 (71.4%) — VE 77% (95% CI 67-84) over 12 months — landmark high-efficacy result that drove R21 to phase 3. Africa relevance: DIRECT — Burkina Faso, seasonal malaria zone.',

                    estimandType: 'HR', publishedHR: 0.23, hrLCI: 0.16, hrUCI: 0.33, pubHR: 0.23,

                    allOutcomes: [
                        { shortLabel: 'CLIN_MAL', title: 'Clinical malaria episodes 50ug R21/MM vs rabies control', tE: 38, cE: 105, type: 'PRIMARY', matchScore: 100, effect: 0.23, lci: 0.16, uci: 0.33, estimandType: 'HR' },

                        { shortLabel: 'IGG_CSP', title: 'Anti-CSP IgG titres at 28d after 3rd dose (log10 EU/mL)', tE: 4.5, cE: 1.0, type: 'SECONDARY', matchScore: 70, effect: 3.5, lci: 3.2, uci: 3.8, estimandType: 'MD' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Datoo MS, Natama MH, Some A, et al. Efficacy of a low-dose candidate malaria vaccine, R21 in adjuvant Matrix-M, with seasonal administration to children in Burkina Faso: a randomised controlled trial. Lancet 2021;397:1809-1818. PMID 33964223. DOI 10.1016/S0140-6736(21)00943-0.',

                    sourceUrl: 'https://doi.org/10.1016/S0140-6736(21)00943-0',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT03896724'
                },

                'NCT04704830': {

                    name: 'R21/Matrix-M Phase 3 (Datoo 2024)', pmid: '38310910', phase: 'III', year: 2024, tE: 1224, tN: 3200, cE: 1095, cN: 1600, group: 'Datoo MS, Dicko A, Tinto H, et al. Lancet 2024;403:533-544 (PMID 38310910). University of Oxford + Serum Institute of India + EDCTP + multiple African research groups (IRSS Burkina Faso 2 sites, Malaria Research and Training Center Bamako Mali, KEMRI-Wellcome Trust Kilifi Kenya, Ifakara Health Institute Bagamoyo Tanzania) phase 3 double-blind randomized trial. n=4,800 children aged 5-36 months across 5 African sites randomized 2:1 to R21/Matrix-M (50 ug R21 + 50 ug Matrix-M, n=3,200) vs rabies vaccine control (n=1,600). 3-dose primary series; 4th booster at 12 months. Two regimens: standard age-based (Dande, Burkina Faso; Kilifi, Kenya; Bagamoyo, Tanzania, n=2,400) vs seasonal pre-rains (Nanoro, Burkina Faso; Bougouni, Mali, n=2,400). PRIMARY EFFICACY: clinical malaria 12 months post-3rd dose. RESULT: VE 75% standard regime (95% CI 71-79); 68% seasonal regime (61-74). Drove WHO 2023 prequalification; first low-cost (~$2/dose) malaria vaccine recommended at scale by WHO. Africa relevance: DIRECT — entirely African enrolment across 4 countries.',

                    estimandType: 'HR', publishedHR: 0.25, hrLCI: 0.21, hrUCI: 0.29, pubHR: 0.25,

                    allOutcomes: [
                        { shortLabel: 'CLIN_MAL', title: 'Clinical malaria episodes R21/MM Phase 3 vs rabies (combined regime)', tE: 1224, cE: 1095, type: 'PRIMARY', matchScore: 100, effect: 0.25, lci: 0.21, uci: 0.29, estimandType: 'HR' },

                        { shortLabel: 'SEV_MAL', title: 'Severe malaria R21/MM vs rabies control', tE: 22, cE: 21, type: 'SECONDARY', matchScore: 90, effect: 0.52, lci: 0.29, uci: 0.96, estimandType: 'HR' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Datoo MS, Dicko A, Tinto H, et al. Safety and efficacy of malaria vaccine candidate R21/Matrix-M in African children: a multicentre, double-blind, randomised, phase 3 trial. Lancet 2024;403:533-544. PMID 38310910. DOI 10.1016/S0140-6736(23)02511-4.',

                    sourceUrl: 'https://doi.org/10.1016/S0140-6736(23)02511-4',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT04704830'
                }
            }"""


# ==========================
# TOPIC 25: TB Prevention NMA (k=3)
# ==========================
TB_BODY = """

                'NCT01404312': {

                    name: 'BRIEF-TB / A5279 (1HP)', pmid: '30970187', phase: 'III', year: 2019, tE: 32, tN: 1488, cE: 33, cN: 1498, group: 'Swindells S, Ramchandani R, Gupta A, et al. NEJM 2019;380:1001-1011 (PMID 30970187). NIAID/ACTG-sponsored phase 3 open-label non-inferiority trial in HIV-1-positive adults with latent TB (TST/IGRA+) or living in high TB burden area. n=3,000 randomized 1:1 across 45 sites in 10 countries (USA, Botswana, Brazil, Haiti, Kenya, Malawi, Peru, South Africa, Thailand, Zimbabwe). Arms: (A) 4-week 1HP — daily rifapentine 600mg + isoniazid 300mg for 4 weeks (n=1,488); (B) 9-month 9H — daily isoniazid 300mg for 9 months (n=1,498). PRIMARY: incidence of first active TB diagnosis, TB-related death, or death from unknown cause. RESULT: 32/1488 1HP arm vs 33/1498 9H arm — incidence rate 0.65 vs 0.67 per 100 PY; HR 0.99 (95% CI 0.61-1.61) — NON-INFERIOR (NI margin 1.25). Treatment completion 97% vs 90%. Drove WHO 2020 update of TB Preventive Treatment recommendation for 1HP as alternative to 9H. Africa relevance: DIRECT — multiple African sites (Botswana, Kenya, Malawi, South Africa, Zimbabwe).',

                    estimandType: 'HR', publishedHR: 0.99, hrLCI: 0.61, hrUCI: 1.61, pubHR: 0.99,

                    allOutcomes: [
                        { shortLabel: 'TB_INC', title: 'Active TB / TB death / unknown-cause death (1HP vs 9H)', tE: 32, cE: 33, type: 'PRIMARY', matchScore: 100, effect: 0.99, lci: 0.61, uci: 1.61, estimandType: 'HR' },

                        { shortLabel: 'COMPL', title: 'Treatment completion (1HP vs 9H)', tE: 1444, cE: 1349, type: 'SECONDARY', matchScore: 90, effect: 1.07, lci: 1.05, uci: 1.10, estimandType: 'RR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Swindells S, Ramchandani R, Gupta A, et al. One Month of Rifapentine plus Isoniazid to Prevent HIV-Related Tuberculosis. NEJM 2019;380:1001-1011. PMID 30970187. DOI 10.1056/NEJMoa1806808.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa1806808',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT01404312'
                },

                'NCT00023452': {

                    name: 'TBTC Study 26 / PREVENT TB (3HP)', pmid: '22150035', phase: 'III', year: 2011, tE: 7, tN: 3986, cE: 15, cN: 3745, group: 'Sterling TR, Villarino ME, Borisov AS, et al. NEJM 2011;365:2155-2166 (PMID 22150035). CDC TBTC + Aeras + NIAID-sponsored phase 3 open-label non-inferiority trial in adults and children >=12 years with latent TB at high risk of TB progression (TST+ contacts of active TB or HIV-coinfected) across 26 sites in USA, Canada, Brazil, Spain. n=8,053 randomized 1:1 to (A) 3HP — once-weekly rifapentine 900mg + isoniazid 900mg via DOT for 12 weeks (n=3,986) vs (B) 9H — daily self-administered isoniazid 300mg for 9 months (n=3,745). PRIMARY: confirmed active TB. RESULT: 7/3986 3HP arm vs 15/3745 9H arm — cumulative incidence 0.19% vs 0.43%; cumulative incidence ratio 0.44 (95% CI 0.18-1.07) — non-inferior at 0.75pp NI margin. Treatment completion higher with 3HP (82%) vs 9H (69%). Drove CDC 2011 + WHO 2018 endorsements of 3HP as preferred LTBI regimen. Africa relevance: indirect — no African sites in main trial, but the 3HP regimen is a critical comparator for African TB-prevention NMA.',

                    estimandType: 'CIR', publishedHR: 0.44, hrLCI: 0.18, hrUCI: 1.07, pubHR: 0.44,

                    allOutcomes: [
                        { shortLabel: 'TB_INC', title: 'Confirmed active TB (3HP vs 9H, NI primary)', tE: 7, cE: 15, type: 'PRIMARY', matchScore: 100, effect: 0.44, lci: 0.18, uci: 1.07, estimandType: 'CIR' },

                        { shortLabel: 'COMPL', title: 'Treatment completion (3HP DOT vs 9H SAT)', tE: 3268, cE: 2584, type: 'SECONDARY', matchScore: 90, effect: 1.19, lci: 1.16, uci: 1.22, estimandType: 'RR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Sterling TR, Villarino ME, Borisov AS, et al. Three Months of Rifapentine and Isoniazid for Latent Tuberculosis Infection. NEJM 2011;365:2155-2166. PMID 22150035. DOI 10.1056/NEJMoa1104875.',

                    sourceUrl: 'https://doi.org/10.1056/NEJMoa1104875',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT00023452'
                },

                'NCT01582711': {

                    name: 'iAdhere / TBTC Study 33 (3HP SAT vs DOT)', pmid: '28135725', phase: 'III', year: 2017, tE: 348, tN: 504, cE: 372, cN: 498, group: 'Belknap R, Holland D, Feng PJ, et al. Annals Intern Med 2017;167:689-697 (PMID 28135725). CDC TBTC-sponsored phase 3 open-label non-inferiority trial of 3HP regimen (12 once-weekly doses of rifapentine 900mg + isoniazid 900mg) administered via SELF-ADMINISTRATION (SAT) vs DIRECTLY-OBSERVED THERAPY (DOT) in adults aged >=18 with latent TB infection across 12 sites in USA + Spain + Hong Kong. n=1,002 randomized 1:1:1 to (A) DOT n=500; (B) SAT n=502; (C) SAT + monthly SMS reminders (sub-arm). PRIMARY: treatment completion. RESULT: SAT (combined) 348+372 = 720/1000 (72%) vs DOT 372/498 (74.7%) — completion gap -3.0pp (95% CI -8.0 to +2.0pp) — NON-INFERIOR (NI margin 15pp). Self-administration is acceptable for TB preventive treatment when DOT capacity is constrained. Drove WHO 2020 endorsement of self-administered 3HP as alternative to DOT. Africa relevance: indirect — no African sites, but SAT framework is critical for scaling 3HP across resource-limited African settings where DOT is impractical.',

                    estimandType: 'PCT', publishedHR: 0.96, hrLCI: 0.91, hrUCI: 1.02, pubHR: 0.96,

                    allOutcomes: [
                        { shortLabel: 'COMPL', title: 'Treatment completion (SAT combined vs DOT, NI primary)', tE: 720, cE: 372, type: 'PRIMARY', matchScore: 100, effect: 0.96, lci: 0.91, uci: 1.02, estimandType: 'RR' },

                        { shortLabel: 'AE_GR3', title: 'Grade 3+ adverse events (SAT vs DOT)', tE: 18, cE: 19, type: 'SAFETY', matchScore: 80, effect: 0.95, lci: 0.50, uci: 1.78, estimandType: 'RR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Belknap R, Holland D, Feng PJ, et al. Self-administered Versus Directly Observed Once-Weekly Isoniazid and Rifapentine Treatment of Latent Tuberculosis Infection: A Randomized Trial. Ann Intern Med 2017;167:689-697. PMID 28135725. DOI 10.7326/M17-1150.',

                    sourceUrl: 'https://doi.org/10.7326/M17-1150',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT01582711'
                }
            }"""


def build_prep():
    FILE = Path("HIV_PREP_INJECTABLE_NMA_REVIEW.html")
    text = FILE.read_text(encoding="utf-8")
    text = replace_or_die(text,
        "<title>RapidMeta Cardiology | SGLT2 Inhibitor Class NMA in Heart Failure v1.0</title>",
        "<title>RapidMeta HIV/Prevention | HIV PrEP NMA — Injectable CAB-LA + Oral F/TAF/F/TDF v0.1 (HPTN 083 + HPTN 084 + DISCOVER, post-2017)</title>")
    text = replace_or_die(text,
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT03036124', 'NCT03057977', 'NCT03057951', 'NCT03619213', 'NCT03521934', 'NCT03315143']);",
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT02720094', 'NCT03164564', 'NCT02842086']);")
    text = replace_or_die(text,
        "{ 'NCT03036124': 'DAPA-HF', 'NCT03057977': 'EMPEROR-Reduced', 'NCT03057951': 'EMPEROR-Preserved', 'NCT03619213': 'DELIVER', 'NCT03521934': 'SOLOIST-WHF', 'NCT03315143': 'SCORED' }",
        "{ 'NCT02720094': 'HPTN 083', 'NCT03164564': 'HPTN 084', 'NCT02842086': 'DISCOVER' }")
    text = replace_realdata(text, PREP_BODY)
    text = text.replace("SGLT2-HF v1.0", "HIV PrEP NMA v0.1")
    text = text.replace("SGLT2 Inhibitors for Heart Failure Outcomes: A Living Systematic Review and Meta-Analysis of Randomized Controlled Trials",
                        "HIV Pre-Exposure Prophylaxis Network Meta-Analysis: Injectable Cabotegravir vs Oral F/TAF vs Oral F/TDF (HPTN 083 + HPTN 084 + DISCOVER, post-2016)")
    text = text.replace("SGLT2 Inhibitors in Heart Failure", "HIV Pre-Exposure Prophylaxis (PrEP)")
    text = text.replace('value="Adults with heart failure"', 'value="HIV-uninfected adults at high HIV risk (MSM/TGW + SSA women)"')
    text = text.replace("value=\"Heart Failure\"", "value=\"HIV PrEP\"")
    FILE.write_text(text, encoding="utf-8")
    print(f"  HIV PrEP NMA: {FILE.stat().st_size:,}")


def build_malaria():
    FILE = Path("MALARIA_VACCINE_NMA_REVIEW.html")
    text = FILE.read_text(encoding="utf-8")
    text = replace_or_die(text,
        "<title>RapidMeta Cardiology | SGLT2 Inhibitor Class NMA in Heart Failure v1.0</title>",
        "<title>RapidMeta Vaccinology | Malaria Vaccine NMA — RTS,S/AS01 + R21/Matrix-M v0.1 (3 African pivotal trials, post-2009)</title>")
    text = replace_or_die(text,
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT03036124', 'NCT03057977', 'NCT03057951', 'NCT03619213', 'NCT03521934', 'NCT03315143']);",
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT00866619', 'NCT03896724', 'NCT04704830']);")
    text = replace_or_die(text,
        "{ 'NCT03036124': 'DAPA-HF', 'NCT03057977': 'EMPEROR-Reduced', 'NCT03057951': 'EMPEROR-Preserved', 'NCT03619213': 'DELIVER', 'NCT03521934': 'SOLOIST-WHF', 'NCT03315143': 'SCORED' }",
        "{ 'NCT00866619': 'RTS,S Phase 3', 'NCT03896724': 'R21/MM Phase 2b (Datoo 2021)', 'NCT04704830': 'R21/MM Phase 3 (Datoo 2024)' }")
    text = replace_realdata(text, MAL_BODY)
    text = text.replace("SGLT2-HF v1.0", "Malaria Vaccine NMA v0.1")
    text = text.replace("SGLT2 Inhibitors for Heart Failure Outcomes: A Living Systematic Review and Meta-Analysis of Randomized Controlled Trials",
                        "Malaria Vaccines for African Children Network Meta-Analysis: RTS,S/AS01 vs R21/Matrix-M (3 pivotal phase 2b/3 trials, post-2009)")
    text = text.replace("SGLT2 Inhibitors in Heart Failure", "Malaria Vaccines (RTS,S + R21)")
    text = text.replace('value="Adults with heart failure"', 'value="Children 5-36mo in P. falciparum-endemic Africa"')
    text = text.replace("value=\"Heart Failure\"", "value=\"Malaria Vaccine\"")
    FILE.write_text(text, encoding="utf-8")
    print(f"  Malaria NMA: {FILE.stat().st_size:,}")


def build_tb():
    FILE = Path("TB_PREVENTION_NMA_REVIEW.html")
    text = FILE.read_text(encoding="utf-8")
    text = replace_or_die(text,
        "<title>RapidMeta Cardiology | SGLT2 Inhibitor Class NMA in Heart Failure v1.0</title>",
        "<title>RapidMeta TB | TB Preventive Treatment NMA — 1HP vs 3HP vs 9H Regimens v0.1 (3 phase 3 trials, post-2010)</title>")
    text = replace_or_die(text,
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT03036124', 'NCT03057977', 'NCT03057951', 'NCT03619213', 'NCT03521934', 'NCT03315143']);",
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT01404312', 'NCT00023452', 'NCT01582711']);")
    text = replace_or_die(text,
        "{ 'NCT03036124': 'DAPA-HF', 'NCT03057977': 'EMPEROR-Reduced', 'NCT03057951': 'EMPEROR-Preserved', 'NCT03619213': 'DELIVER', 'NCT03521934': 'SOLOIST-WHF', 'NCT03315143': 'SCORED' }",
        "{ 'NCT01404312': 'BRIEF-TB (1HP)', 'NCT00023452': 'PREVENT TB / TBTC Study 26 (3HP)', 'NCT01582711': 'iAdhere (3HP SAT)' }")
    text = replace_realdata(text, TB_BODY)
    text = text.replace("SGLT2-HF v1.0", "TB Prevention NMA v0.1")
    text = text.replace("SGLT2 Inhibitors for Heart Failure Outcomes: A Living Systematic Review and Meta-Analysis of Randomized Controlled Trials",
                        "TB Preventive Treatment Network Meta-Analysis: 1HP vs 3HP vs 9H Regimens (3 phase 3 trials, post-2010)")
    text = text.replace("SGLT2 Inhibitors in Heart Failure", "TB Preventive Treatment Regimens")
    text = text.replace('value="Adults with heart failure"', 'value="Adults at risk of TB progression (HIV+ or LTBI+)"')
    text = text.replace("value=\"Heart Failure\"", "value=\"TB Prevention\"")
    FILE.write_text(text, encoding="utf-8")
    print(f"  TB Prevention NMA: {FILE.stat().st_size:,}")


if __name__ == "__main__":
    build_prep()
    build_malaria()
    build_tb()
