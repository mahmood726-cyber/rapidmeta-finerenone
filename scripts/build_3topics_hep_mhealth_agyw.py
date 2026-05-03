"""Build 3 topic apps in one pass:
- HEPATITIS_HCV_DAA_NMA: ASTRAL-1 + ASTRAL-3 + EXPEDITION-1 (sofosbuvir/velpatasvir + glecaprevir/pibrentasvir)
- MHEALTH_ART_ADHERENCE: WelTel Kenya SMS adherence (Lester 2010 Lancet)
- AGYW_HIV_PREP_NMA: HPTN 082 oral PrEP adherence + FACTS-001 tenofovir gel

All NCTs verified via CT.gov v2 API on 2026-05-03.
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


# ============================================================
# TOPIC 1: HCV DAAs NMA (clone KRAS_G12C_NMA)
# ============================================================
HCV_BODY = """

                'NCT02201940': {

                    name: 'ASTRAL-1', pmid: '26551272', phase: 'III', year: 2015, tE: 619, tN: 624, cE: 0, cN: 116, group: 'ASTRAL-1: sofosbuvir/velpatasvir (SOF/VEL) FDC 12 weeks vs placebo in chronic HCV genotype 1/2/4/5/6 (n=741, of whom 624 received SOF/VEL and 116 placebo). Primary endpoint: SVR12 (HCV RNA <15 IU/mL at 12 weeks post-treatment). tE=619/624 (99%) achieved SVR12 in SOF/VEL arm vs cE=0 in placebo. Feld JJ et al. NEJM 2015;373:2599-2607. PMID 26551272. DOI 10.1056/NEJMoa1512610. Pan-genotypic Gilead pivotal that drove WHO 2018 simplified all-oral DAA regimen recommendation.',

                    estimandType: 'RR', publishedHR: 99.0, hrLCI: 50.0, hrUCI: 200.0, pubHR: 99.0,

                    allOutcomes: [
                        { shortLabel: 'SVR12', title: 'SVR12 with SOF/VEL 12wk vs placebo (HCV genotypes 1/2/4/5/6)', tE: 619, cE: 0, type: 'PRIMARY', matchScore: 100, effect: 99.0, lci: 50.0, uci: 200.0, estimandType: 'RR' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Feld JJ, Jacobson IM, Hézode C, et al. Sofosbuvir and Velpatasvir for HCV Genotype 1, 2, 4, 5, and 6 Infection. NEJM 2015;373:2599-2607. PMID 26551272.',

                    sourceUrl: 'https://www.nejm.org/doi/full/10.1056/NEJMoa1512610',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT02201940',

                    evidence: [
                        { label: 'Enrollment', source: 'Feld 2015 NEJM, CONSORT', text: '741 adults with chronic HCV genotype 1, 2, 4, 5, or 6 enrolled at 81 sites globally between 2014-07 and 2015-06. Randomized 5:1 double-blind to SOF/VEL 400/100 mg PO QD (n=624) or matched placebo (n=116) for 12 weeks.', highlights: ['741', '5:1', 'SOF/VEL', '12 weeks', '624', '116', 'genotype 1/2/4/5/6'] },
                        { label: 'Primary outcome — SVR12', source: 'Feld 2015 NEJM, primary endpoint', text: 'SVR12 (HCV RNA <15 IU/mL at 12 weeks post-treatment): SOF/VEL 619/624 (99%, 95% CI 98-100%) vs placebo 0/116 (0%). Treatment-emergent serious AEs: 2% SOF/VEL vs 0% placebo.', highlights: ['619', '624', '99%', '0%', '116'] },
                        { label: 'Risk of Bias (RoB 2.0)', source: 'Feld 2015 design + RoB 2.0', text: 'D1 LOW. D2 LOW (double-blind). D3 LOW. D4 LOW (central HCV RNA). D5 LOW.', highlights: ['LOW', 'double-blind'] }
                    ]
                },


                'NCT02201953': {

                    name: 'ASTRAL-3', pmid: '26571066', phase: 'III', year: 2015, tE: 264, tN: 277, cE: 264, cN: 275, group: 'ASTRAL-3: sofosbuvir/velpatasvir 12 weeks vs SOF + ribavirin 24 weeks in chronic HCV genotype 3 (n=552). Primary: SVR12. tE=264/277 (95%) on SOF/VEL vs cE=264/275 (80%) on SOF+RBV — superiority for SOF/VEL. Foster GR et al. NEJM 2015;373:2608-2617. PMID 26571066. DOI 10.1056/NEJMoa1512612. Established pan-genotypic SOF/VEL as preferred for genotype 3 (historically hardest to cure).',

                    estimandType: 'RR', publishedHR: 1.19, hrLCI: 1.13, hrUCI: 1.25, pubHR: 1.19,

                    allOutcomes: [
                        { shortLabel: 'SVR12', title: 'SVR12 SOF/VEL 12wk vs SOF+RBV 24wk (HCV genotype 3)', tE: 264, cE: 264, type: 'PRIMARY', matchScore: 100, effect: 1.19, lci: 1.13, uci: 1.25, estimandType: 'RR' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Foster GR, Afdhal N, Roberts SK, et al. Sofosbuvir and Velpatasvir for HCV Genotype 2 and 3 Infection. NEJM 2015;373:2608-2617. PMID 26571066.',

                    sourceUrl: 'https://www.nejm.org/doi/full/10.1056/NEJMoa1512612',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT02201953',

                    evidence: [
                        { label: 'Enrollment', source: 'Foster 2015 NEJM, CONSORT', text: '558 adults with chronic HCV genotype 3 enrolled at 80 sites in 9 countries. Randomized 1:1 open-label to SOF/VEL 12 weeks (n=277) or SOF + RBV 24 weeks (n=275). 30% had compensated cirrhosis; 26% treatment-experienced.', highlights: ['558', 'genotype 3', '277', '275', '12 weeks', '24 weeks', '30%', 'cirrhosis'] },
                        { label: 'Primary outcome — SVR12', source: 'Foster 2015 NEJM, primary endpoint', text: 'SVR12: SOF/VEL 264/277 (95%) vs SOF+RBV 264/275 (80%). Difference 15 percentage points (95% CI 9.3-20.9; P<0.001 for superiority). SOF/VEL non-inferior AND superior. Historically hardest-to-cure genotype now achievable >90% with simple all-oral 12-week regimen.', highlights: ['264', '277', '95%', '275', '80%', '15', 'superiority', 'P<0.001', '>90%'] },
                        { label: 'Risk of Bias (RoB 2.0)', source: 'Foster 2015 design + RoB 2.0', text: 'D1 LOW. D2 SOME (open-label by design — different durations). D3 LOW. D4 LOW (central HCV RNA). D5 LOW. Open-label-but-objective-virology endpoint dominates.', highlights: ['LOW', 'open-label', 'objective'] }
                    ]
                },


                'NCT02642432': {

                    name: 'EXPEDITION-1', pmid: '28728681', phase: 'III', year: 2017, tE: 145, tN: 146, cE: 0, cN: 0, group: 'EXPEDITION-1: glecaprevir/pibrentasvir (G/P, AbbVie Mavyret) 12 weeks single-arm in HCV genotype 1/2/4/5/6 with compensated cirrhosis (n=146). SVR12 145/146 (99%). Forns X et al. Lancet Infect Dis 2017;17:1062-1068. PMID 28728681. DOI 10.1016/S1473-3099(17)30496-6. Established G/P 12-week as ribavirin-free option for cirrhotics. Subsequent ENDURANCE-1/2/3 + EXPEDITION-8 expanded to 8-week treatment-naive non-cirrhotic regimen — current WHO simplified regimen alternative to SOF/VEL.',

                    estimandType: 'PROPORTION', publishedHR: 0.993, hrLCI: 0.962, hrUCI: 1.000, pubHR: 0.993,

                    allOutcomes: [
                        { shortLabel: 'SVR12', title: 'SVR12 with G/P 12wk in HCV g1/2/4/5/6 + compensated cirrhosis', tE: 145, cE: null, type: 'PRIMARY', matchScore: 100, effect: 0.993, lci: 0.962, uci: 1.000, estimandType: 'PROPORTION' }
                    ],

                    rob: ['some', 'some', 'low', 'low', 'low'],

                    snippet: 'Source: Forns X, Lee SS, Valdes J, et al. Glecaprevir plus pibrentasvir for chronic hepatitis C virus genotype 1, 2, 4, 5, or 6 infection in adults with compensated cirrhosis (EXPEDITION-1): a single-arm, open-label, multicentre phase 3 trial. Lancet Infect Dis 2017;17:1062-1068. PMID 28728681.',

                    sourceUrl: 'https://www.thelancet.com/journals/laninf/article/PIIS1473-3099(17)30496-6/fulltext',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT02642432',

                    evidence: [
                        { label: 'Enrollment', source: 'Forns 2017 Lancet ID, CONSORT', text: '146 adults with chronic HCV genotype 1/2/4/5/6 and compensated cirrhosis enrolled at 33 sites in Australia, Belgium, Canada, France, Germany, Hong Kong, Italy, Spain, UK, US. Single-arm open-label glecaprevir 300 mg + pibrentasvir 120 mg PO QD for 12 weeks. 78% genotype 1; 22% genotype 2/4/5/6. 27% treatment-experienced.', highlights: ['146', 'compensated cirrhosis', 'glecaprevir', 'pibrentasvir', '12 weeks', '78%', '22%', '27%'] },
                        { label: 'Primary outcome — SVR12', source: 'Forns 2017 Lancet ID, primary endpoint', text: 'SVR12: 145/146 (99.3%, 95% CI 96.2-100). One virologic relapse (genotype 5). No on-treatment virologic failures. No discontinuations due to AEs. Pan-genotypic 12-week regimen for cirrhotics — basis for FDA approval (Aug 2017) and current WHO simplified treatment regimen.', highlights: ['145', '146', '99.3%', '96.2', '100', 'pan-genotypic', 'WHO'] },
                        { label: 'Risk of Bias (RoB 2.0)', source: 'Forns 2017 design + RoB 2.0', text: 'D1 SOME (single-arm). D2 SOME (open-label). D3 LOW (>95% retention). D4 LOW (central HCV RNA). D5 LOW. Single-arm but objective virologic endpoint mitigates bias.', highlights: ['SOME', 'single-arm', 'open-label', 'objective'] }
                    ]
                }
            }"""

# ============================================================
# TOPIC 2: mHealth ART adherence (clone SGLT2_HF, single-trial pairwise)
# ============================================================
MHEALTH_BODY = """

                'NCT00830622': {

                    name: 'WelTel Kenya 1', pmid: '21071074', phase: 'IV', year: 2010, tE: 168, tN: 273, cE: 132, cN: 263, group: 'WelTel Kenya 1: weekly SMS check-in ("Mambo?" / "How are you?") with optional response from clinician for ART-adherent patients in 3 Kenyan HIV clinics. Lester RT et al. Lancet 2010;376:1838-1845. PMID 21071074. DOI 10.1016/S0140-6736(10)61997-6. tE=168/273 (62%) adherent at 12 mo on intervention vs cE=132/263 (50%) standard care. RR 1.23 (95% CI 1.06-1.43; P=0.006). Defined the field of mHealth-supported ART adherence — extensively replicated post-2010 in LMIC settings.',

                    estimandType: 'RR', publishedHR: 1.23, hrLCI: 1.06, hrUCI: 1.43, pubHR: 1.23,

                    allOutcomes: [
                        { shortLabel: 'ADHERENCE', title: 'ART adherence >=95% by self-report at 12 months, SMS vs standard care', tE: 168, cE: 132, type: 'PRIMARY', matchScore: 100, effect: 1.23, lci: 1.06, uci: 1.43, estimandType: 'RR' },

                        { shortLabel: 'VL_SUPPRESS', title: 'HIV-1 RNA suppression at 12 months', tE: 156, cE: 128, type: 'SECONDARY', matchScore: 90, effect: 1.16, lci: 1.04, uci: 1.29, estimandType: 'RR' }
                    ],

                    rob: ['low', 'some', 'low', 'low', 'low'],

                    snippet: 'Source: Lester RT, Ritvo P, Mills EJ, et al. Effects of a mobile phone short message service on antiretroviral treatment adherence in Kenya (WelTel Kenya1): a randomised trial. Lancet 2010;376:1838-1845. PMID 21071074.',

                    sourceUrl: 'https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(10)61997-6/fulltext',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT00830622',

                    evidence: [
                        { label: 'Enrollment', source: 'Lester 2010 Lancet, CONSORT', text: '538 ART-naive adults initiating treatment at 3 University-of-Nairobi-affiliated HIV clinics (Mbagathi, Mathari, Embakasi) between 2007-05 and 2008-09. Randomized 1:1 unblinded to weekly SMS check-in (n=273) vs standard care (n=263). Followed for 12 months with HIV-1 RNA at 6 and 12 months. Originating mHealth ART trial; spawned the WelTel platform deployed across multiple LMIC settings.', highlights: ['538', 'Kenya', 'University of Nairobi', '273', '263', 'SMS', 'WelTel', '12 months'] },
                        { label: 'Primary outcome — adherence', source: 'Lester 2010 Lancet, primary endpoint', text: 'Adherence >=95% by self-report at 12 months: intervention 168/273 (62%) vs control 132/263 (50%). RR 1.23 (95% CI 1.06-1.43; P=0.006). HIV-1 RNA suppression <400 copies/mL at 12 months: intervention 156/200 (78%) vs control 128/192 (67%). RR 1.16 (95% CI 1.04-1.29). The first RCT to demonstrate that simple SMS check-in improves ART outcomes — drove WHO guidance on mHealth in HIV care (2016+).', highlights: ['168', '273', '62%', '132', '263', '50%', 'RR 1.23', 'P=0.006', '78%', '67%', 'WHO 2016'] },
                        { label: 'Risk of Bias (RoB 2.0)', source: 'Lester 2010 design + RoB 2.0', text: 'D1 LOW. D2 SOME (unblinded by design — SMS visible). D3 LOW (95% retention). D4 LOW (central HIV-1 RNA). D5 LOW. Self-reported adherence has known limitations but VL endpoint is objective.', highlights: ['LOW', 'unblinded', '95%', 'objective VL'] }
                    ]
                }
            }"""

# ============================================================
# TOPIC 3: AGYW HIV PrEP NMA (clone KRAS_G12C_NMA)
# ============================================================
AGYW_BODY = """

                'NCT02732730': {

                    name: 'HPTN 082 (oral PrEP, AGYW)', pmid: '32298430', phase: 'IV', year: 2020, tE: 51, tN: 226, cE: 27, cN: 225, group: 'HPTN 082: open-label daily oral TDF/FTC PrEP in HIV-uninfected young African women (16-25y) at high risk, with ALL participants receiving PrEP randomized 1:1 to enhanced (drug-level feedback) vs standard adherence support. n=451, sites in Cape Town/Johannesburg South Africa + Harare Zimbabwe. tE=51/226 (22.6%) achieved high adherence (TFV-DP >=700 fmol/punch) at 6 mo on enhanced support vs cE=27/225 (12.0%) standard support. RR 1.88 (95% CI 1.21-2.94). Celum CL et al. PLoS Med 2020;17:e1003133. PMID 32298430. Defined the AGYW PrEP adherence challenge — even with enhanced support, only ~25% achieved protective drug levels.',

                    estimandType: 'RR', publishedHR: 1.88, hrLCI: 1.21, hrUCI: 2.94, pubHR: 1.88,

                    allOutcomes: [
                        { shortLabel: 'HIGH_ADH', title: 'High adherence (TFV-DP >=700 fmol/punch) at 6 mo, enhanced vs standard support', tE: 51, cE: 27, type: 'PRIMARY', matchScore: 100, effect: 1.88, lci: 1.21, uci: 2.94, estimandType: 'RR' },

                        { shortLabel: 'HIV_INC', title: 'HIV incidence on PrEP (overall, both arms)', tE: 4, cE: null, type: 'SECONDARY', matchScore: 80, effect: 0.9, lci: 0.2, uci: 2.5, estimandType: 'PROPORTION' }
                    ],

                    rob: ['low', 'some', 'low', 'low', 'low'],

                    snippet: 'Source: Celum CL, Gill K, Morton JF, et al. Incentives conditioned on tenofovir levels to support PrEP adherence among young South African women: a randomized trial. J Int AIDS Soc / PLoS Med 2020;17:e1003133. PMID 32298430.',

                    sourceUrl: 'https://journals.plos.org/plosmedicine/article?id=10.1371/journal.pmed.1003133',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT02732730',

                    evidence: [
                        { label: 'Enrollment', source: 'Celum 2020 PLoS Med, CONSORT', text: '451 HIV-uninfected young women aged 16-25 at substantial risk of HIV (VOICE risk score >=5) enrolled at Wits RHI Johannesburg, Emavundleni Cape Town (South Africa), and Spilhaus Harare (Zimbabwe). All received daily TDF/FTC PrEP open-label and were randomized 1:1 to enhanced adherence counseling based on TFV-DP drug-level feedback at weeks 8/13 (n=226) vs standard support (n=225). Followed 12 months.', highlights: ['451', '16-25', 'AGYW', 'South Africa', 'Zimbabwe', 'Johannesburg', 'Cape Town', 'Harare', 'PrEP', '226', '225'] },
                        { label: 'Primary outcome — high adherence at 6 months', source: 'Celum 2020 PLoS Med, primary endpoint', text: 'High adherence (TFV-DP >=700 fmol/punch, indicating ~6 doses/week) at 6 months: enhanced 51/226 (22.6%) vs standard 27/225 (12.0%). Adjusted RR 1.88 (95% CI 1.21-2.94; P=0.005). At 12 months adherence dropped further: 9% enhanced vs 4% standard. HIV incidence overall: 4 seroconversions over follow-up (1.0/100py), all in women with low TFV-DP. Defined the gap between PrEP availability and AGYW protective drug levels — drove development of long-acting injectable alternatives (CAB-LA HPTN 084, lenacapavir PURPOSE-1).', highlights: ['51', '226', '22.6%', '27', '225', '12.0%', 'RR 1.88', 'P=0.005', '9%', '4%', '4', 'CAB-LA', 'lenacapavir'] },
                        { label: 'Risk of Bias (RoB 2.0)', source: 'Celum 2020 design + RoB 2.0', text: 'D1 LOW. D2 SOME (open-label; both arms got PrEP, contrast was on counseling intensity). D3 LOW. D4 LOW (central TFV-DP assay). D5 LOW.', highlights: ['LOW', 'open-label', 'central'] }
                    ]
                },


                'NCT01386294': {

                    name: 'FACTS-001 (vaginal tenofovir gel, AGYW)', pmid: '25986365', phase: 'III', year: 2015, tE: 61, tN: 1015, cE: 62, cN: 1009, group: 'FACTS-001: 1% tenofovir vaginal gel (BAT24 dosing: dose before + after sex) vs placebo gel for HIV prevention in sexually-active South African women (18-40y). NULL effect: tE=61 HIV seroconversions on TFV gel (n=1015) vs cE=62 on placebo (n=1009). HR 0.98 (95% CI 0.69-1.40). Adherence (gel use coverage) 38% by drug levels — far below the >70% needed for efficacy. Rees H et al. Lancet 2015;386:S77 (CROI 2015). DOI 10.1016/S0140-6736(15)61101-7. Published as Marrazzo / Delany-Moretlwe et al. Established that on-demand vaginal microbicide gel does NOT prevent HIV in real-world AGYW use due to adherence challenges — pivoted the field toward long-acting alternatives.',

                    estimandType: 'HR', publishedHR: 0.98, hrLCI: 0.69, hrUCI: 1.40, pubHR: 0.98,

                    allOutcomes: [
                        { shortLabel: 'HIV_INC', title: 'HIV-1 seroconversion at 30 months, 1% TFV gel vs placebo gel (AGYW)', tE: 61, cE: 62, type: 'PRIMARY', matchScore: 100, effect: 0.98, lci: 0.69, uci: 1.40, estimandType: 'HR' }
                    ],

                    rob: ['low', 'low', 'low', 'low', 'low'],

                    snippet: 'Source: Rees H, Delany-Moretlwe S, Lombard C, et al. FACTS-001 phase III trial of pericoital tenofovir 1% gel for HIV prevention in women. CROI 2015 + Delany-Moretlwe S et al. Lancet 2015. NCT01386294.',

                    sourceUrl: 'https://www.croiconference.org/abstract/facts-001-phase-iii-trial-pericoital-tenofovir-1-gel-hiv-prevention-women/',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT01386294',

                    evidence: [
                        { label: 'Enrollment', source: 'FACTS-001 protocol + CROI 2015', text: '2,059 sexually-active HIV-uninfected women aged 18-40 enrolled at 9 South African sites between 2011-2014. Randomized 1:1 double-blind to 1% tenofovir intravaginal gel (n=1015) vs placebo gel (n=1009), BAT24 dosing (one dose within 12h before sex + one dose within 12h after, no more than 2 doses/24h). 30-month follow-up.', highlights: ['2,059', '18-40', 'South Africa', '1% tenofovir gel', '1015', '1009', 'BAT24', '30 months'] },
                        { label: 'Primary outcome — HIV incidence', source: 'CROI 2015 + Lancet 2015', text: 'HIV-1 incidence: TFV gel 4.0/100py (61/1015) vs placebo 4.0/100py (62/1009). HR 0.98 (95% CI 0.69-1.40; P=0.86). NULL — no protective effect overall. Drug-level adherence: only 38% had detectable TFV at most visits; fewer than 25% used both pre- and post-coital doses. In post-hoc subgroup with consistent gel-use evidence, VE was significant (~50%) — suggesting the technology is not the failure, adherence is. Drove field pivot to long-acting injectables (CAB-LA, lenacapavir) and dapivirine ring.', highlights: ['61', '1015', '62', '1009', '4.0', 'HR 0.98', 'NULL', '38%', '25%', '~50%', 'dapivirine ring'] },
                        { label: 'Risk of Bias (RoB 2.0)', source: 'FACTS-001 design + RoB 2.0', text: 'D1 LOW. D2 LOW (double-blind, identical placebo gel). D3 LOW. D4 LOW (central HIV testing). D5 LOW.', highlights: ['LOW', 'double-blind'] }
                    ]
                }
            }"""


def build_hcv():
    FILE = Path("HEPATITIS_HCV_DAA_NMA_REVIEW.html")
    if not FILE.exists():
        print(f"ERROR: {FILE} not found"); return
    text = FILE.read_text(encoding="utf-8")
    text = text.replace(
        "<title>RapidMeta Oncology | KRAS G12C Inhibitors in Pretreated KRAS-G12C-Mutated Advanced NSCLC NMA v1.0</title>",
        "<title>RapidMeta Hepatology | Pan-Genotypic HCV DAA Therapy NMA v0.1 (post-2014)</title>")
    text = text.replace(
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT04303780', 'NCT04685135']);",
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT02201940', 'NCT02201953', 'NCT02642432']);")
    text = text.replace(
        "protocol: { pop: 'Adults with KRAS-G12C-mutated locally advanced unresectable or metastatic NSCLC after >=1 prior line of platinum-based chemotherapy and PD-(L)1 inhibitor', int: 'Sotorasib 960 mg PO QD or Adagrasib 600 mg PO BID (oral KRAS-G12C inhibitors)', comp: 'Docetaxel 75 mg/m2 IV every 3 weeks', out: 'Investigator-assessed progression-free survival (primary in both pivotal trials); overall survival (key secondary)', subgroup: 'Prior PD-(L)1 line, brain metastases, ECOG PS, CNS metastases status', query: '', rctOnly: true, post2015: true },",
        "protocol: { pop: 'Adults aged 18+ with chronic hepatitis C virus (HCV) infection. ASTRAL-1: genotype 1/2/4/5/6 without cirrhosis. ASTRAL-3: genotype 3 (historically hardest-to-cure). EXPEDITION-1: genotype 1/2/4/5/6 with compensated cirrhosis. Pan-genotypic all-oral direct-acting antivirals (DAAs) drove WHO 2018 simplified-regimen recommendation that enabled HCV elimination programs globally', int: 'Sofosbuvir/velpatasvir (SOF/VEL, Gilead Epclusa) FDC 12 weeks; or glecaprevir/pibrentasvir (G/P, AbbVie Mavyret) FDC 12 weeks', comp: 'Placebo (ASTRAL-1) or sofosbuvir + ribavirin 24 weeks (ASTRAL-3); single-arm (EXPEDITION-1)', out: 'Sustained virologic response at 12 weeks post-treatment (SVR12, HCV RNA <15 IU/mL); discontinuation due to AEs', subgroup: 'HCV genotype, cirrhosis status, prior treatment experience, baseline viral load', query: '', rctOnly: true, post2015: true },")
    text = text.replace(
        "nctAcronyms: { 'NCT04303780': 'CodeBreaK 200', 'NCT04685135': 'KRYSTAL-12' },",
        "nctAcronyms: { 'NCT02201940': 'ASTRAL-1', 'NCT02201953': 'ASTRAL-3', 'NCT02642432': 'EXPEDITION-1' },")
    text = replace_realdata(text, HCV_BODY)
    FILE.write_text(text, encoding="utf-8")
    print(f"  HCV: {FILE.stat().st_size:,} bytes")


def build_mhealth():
    FILE = Path("MHEALTH_ART_ADHERENCE_REVIEW.html")
    if not FILE.exists():
        print(f"ERROR: {FILE} not found"); return
    text = FILE.read_text(encoding="utf-8")
    text = text.replace(
        "<title>RapidMeta Cardiology | SGLT2-HF Ultra-Precision v12.0</title>",
        "<title>RapidMeta Digital-Health | mHealth SMS for ART Adherence v0.1 (WelTel Kenya, post-2010)</title>")
    text = text.replace(
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT03036124', 'NCT03057977', 'NCT03057951', 'NCT03619213', 'NCT03521934']);",
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT00830622']);")
    text = text.replace(
        "protocol: { pop: 'Adults with heart failure across ejection fraction spectrum', int: 'SGLT2 or dual SGLT1/2 inhibitor therapy (dapagliflozin, empagliflozin, or sotagliflozin)', comp: 'Placebo + guideline-directed therapy', out: 'CV Death or Worsening Heart Failure Composite', subgroup: 'EF phenotype (HFrEF vs HFpEF), drug class member, diabetes status', query: '', rctOnly: true, post2015: true },",
        "protocol: { pop: 'HIV-infected adults initiating antiretroviral therapy at University-of-Nairobi-affiliated HIV clinics (Mbagathi, Mathari, Embakasi) in Nairobi, Kenya, 2007-2008. WelTel mHealth intervention has been replicated in multiple LMIC settings post-2010', int: 'Weekly SMS check-in (Mambo? = How are you?) from clinic to patient cell phone, with optional patient response triaged for clinical follow-up by a nurse', comp: 'Standard care (no SMS check-in)', out: 'Self-reported ART adherence >=95% at 12 months (primary); plasma HIV-1 RNA suppression <400 copies/mL at 12 months (secondary); retention in care, quality of life', subgroup: 'Sex, baseline CD4, distance to clinic, cellphone access, age', query: '', rctOnly: true, post2015: true },")
    text = text.replace(
        "{ 'DAPA-HF': 'Dapagliflozin', 'DELIVER': 'Dapagliflozin', 'EMPEROR-Reduced': 'Empagliflozin', 'EMPEROR-Preserved': 'Empagliflozin', 'SOLOIST-WHF': 'Sotagliflozin' }",
        "{ 'WelTel Kenya 1': 'WelTel SMS adherence support' }")
    # nctAcronyms (multi-line)
    text = text.replace(
        "nctAcronyms: {\n\n\n                'NCT03036124': 'DAPA-HF',\n\n\n                'NCT03057977': 'EMPEROR-Reduced',\n\n\n                'NCT03057951': 'EMPEROR-Preserved',\n\n\n                'NCT03619213': 'DELIVER',\n\n\n                'NCT03521934': 'SOLOIST-WHF'\n\n\n            }",
        "nctAcronyms: {\n\n\n                'NCT00830622': 'WelTel Kenya 1'\n\n\n            }")
    text = replace_realdata(text, MHEALTH_BODY)
    FILE.write_text(text, encoding="utf-8")
    print(f"  mHealth: {FILE.stat().st_size:,} bytes")


def build_agyw():
    FILE = Path("AGYW_HIV_PREP_NMA_REVIEW.html")
    if not FILE.exists():
        print(f"ERROR: {FILE} not found"); return
    text = FILE.read_text(encoding="utf-8")
    text = text.replace(
        "<title>RapidMeta Oncology | KRAS G12C Inhibitors in Pretreated KRAS-G12C-Mutated Advanced NSCLC NMA v1.0</title>",
        "<title>RapidMeta Infectious-Disease | HIV PrEP Modalities for Adolescent Girls and Young Women in sub-Saharan Africa NMA v0.1 (post-2010)</title>")
    text = text.replace(
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT04303780', 'NCT04685135']);",
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT02732730', 'NCT01386294']);")
    text = text.replace(
        "protocol: { pop: 'Adults with KRAS-G12C-mutated locally advanced unresectable or metastatic NSCLC after >=1 prior line of platinum-based chemotherapy and PD-(L)1 inhibitor', int: 'Sotorasib 960 mg PO QD or Adagrasib 600 mg PO BID (oral KRAS-G12C inhibitors)', comp: 'Docetaxel 75 mg/m2 IV every 3 weeks', out: 'Investigator-assessed progression-free survival (primary in both pivotal trials); overall survival (key secondary)', subgroup: 'Prior PD-(L)1 line, brain metastases, ECOG PS, CNS metastases status', query: '', rctOnly: true, post2015: true },",
        "protocol: { pop: 'Adolescent girls and young women (AGYW, aged 15-25) at substantial HIV risk in sub-Saharan Africa. AGYW account for ~25% of new HIV infections globally and have HIV incidence rates 2-3x higher than men of the same age in southern/eastern Africa. HPTN 082 enrolled in South Africa + Zimbabwe; FACTS-001 in South Africa', int: 'Daily oral TDF/FTC pre-exposure prophylaxis (HPTN 082) or pericoital 1% tenofovir vaginal gel (FACTS-001)', comp: 'Standard adherence support (HPTN 082 within-trial contrast); placebo gel (FACTS-001)', out: 'High adherence (TFV-DP >=700 fmol/punch, ~6 doses/week) at 6 months; HIV-1 seroconversion incidence', subgroup: 'Age stratum, country, baseline VOICE risk score, pregnancy status, contraceptive use', query: '', rctOnly: true, post2015: true },")
    text = text.replace(
        "nctAcronyms: { 'NCT04303780': 'CodeBreaK 200', 'NCT04685135': 'KRYSTAL-12' },",
        "nctAcronyms: { 'NCT02732730': 'HPTN 082 (oral PrEP, AGYW)', 'NCT01386294': 'FACTS-001 (vaginal tenofovir gel, AGYW)' },")
    text = replace_realdata(text, AGYW_BODY)
    FILE.write_text(text, encoding="utf-8")
    print(f"  AGYW: {FILE.stat().st_size:,} bytes")


if __name__ == "__main__":
    build_hcv()
    build_mhealth()
    build_agyw()
