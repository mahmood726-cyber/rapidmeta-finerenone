"""Build 2 more Africa-relevant post-2010 topic apps.

Topic 18 - PREGNANCY_IRON_FCM_REVIEW.html: Pasricha 2023 Lancet Malawi IV iron in pregnancy.
  Single-dose ferric carboxymaltose vs standard-of-care oral iron at 13-26 weeks gestation
  in malaria-endemic southern Malawi. n=862 (FCM 430, SOC 432). NEGATIVE primary outcome:
  no reduction in anemia at 36 weeks (PR 0.92, 95% CI 0.81-1.06; P=0.27). Birthweight identical.
  Trial registered with ANZCTR ACTRN12618001268235 (NOT CT.gov) → synthetic LEGACY-ANZCTR-12618001268235-FCM key.

Topic 19 - PREGNANCY_HIV_VESTED_REVIEW.html: Lockman 2021 Lancet HIV — IMPAACT 2010 / VESTED.
  3-arm phase 3 RCT. NCT03048422. n=643 across Botswana, South Africa (4 sites), Tanzania,
  Uganda, Zimbabwe (3 sites), India, Brazil (4 sites), Thailand (3 sites), USA (2 sites).
  Predominantly sub-Saharan Africa (~70%). Arms: DTG+FTC/TAF vs DTG+FTC/TDF vs EFV/FTC/TDF
  during pregnancy + postpartum. PRIMARY: maternal viral suppression at delivery + adverse
  pregnancy outcome composite + maternal grade ≥3 AE + infant grade ≥3 AE. Drove WHO 2021
  guideline preference for DTG-based ART in pregnancy.
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
# TOPIC 18: Pregnancy IV Iron Pasricha 2023 Malawi
# ==========================
IRON_BODY = """

                'LEGACY-ANZCTR-12618001268235-FCM': {

                    name: 'Pasricha 2023 Malawi (FCM vs oral iron)', pmid: '37088092', phase: 'III', year: 2023, tE: 179, tN: 341, cE: 189, cN: 333, group: 'Pasricha SR, Mwangi MN, Moya E, et al. Lancet 2023;401:1595-1609 (PMID 37088092). Open-label individually-randomized trial in 21 primary-care clinics across two southern regions of Malawi 2018-2021. Adults aged 18+ with singleton pregnancy 13-26 weeks gestation, capillary haemoglobin <10.0 g/dL, negative malaria RDT. Randomized 1:1 to (a) single-dose intravenous ferric carboxymaltose up to 1000 mg given once at enrolment in outpatient setting (n=430) vs (b) standard-of-care oral iron (60 mg elemental iron BID for 90 days, n=432). All received intermittent preventive malaria treatment. PRIMARY MATERNAL OUTCOME: anaemia at 36 weeks gestation (Hb<11.0 g/dL). NEGATIVE: 179/341 (52%) FCM vs 189/333 (57%) SOC; prevalence ratio 0.92 (95% CI 0.81 to 1.06; P=0.27). PRIMARY NEONATAL OUTCOME: birthweight not different (mean diff -3.1 g, 95% CI -75.0 to +68.9; P=0.93). SAFETY: no infusion-related serious adverse events; AE rates similar between arms. Africa relevance: pivotal evidence that single-dose IV ferric carboxymaltose is SAFE in malaria-endemic sub-Saharan African pregnancy but does NOT improve the primary anemia/birthweight outcomes vs WHO-standard oral iron — challenges the assumption that IV iron will be cost-effective for population-level anemia control in Malawi-type settings. Registered with ANZCTR (Australia New Zealand) as ACTRN12618001268235 (NOT on ClinicalTrials.gov); uses synthetic LEGACY-ANZCTR-12618001268235-FCM key in this dashboard.',

                    estimandType: 'RR', publishedHR: 0.92, hrLCI: 0.81, hrUCI: 1.06, pubHR: 0.92,

                    allOutcomes: [
                        { shortLabel: 'ANEMIA_36w', title: 'Anaemia (Hb<11.0 g/dL) at 36 weeks gestation, FCM vs SOC oral iron', tE: 179, cE: 189, type: 'PRIMARY', matchScore: 100, effect: 0.92, lci: 0.81, uci: 1.06, estimandType: 'RR' },

                        { shortLabel: 'ANEMIA_4w', title: 'Anaemia at 4 weeks post-treatment (secondary, FCM vs SOC)', tE: 0, cE: 0, type: 'SECONDARY', matchScore: 90, effect: 0.91, lci: 0.85, uci: 0.97, estimandType: 'RR' },

                        { shortLabel: 'BIRTHWT_MD', title: 'Mean birthweight difference (g, FCM vs SOC) — neonatal primary', tE: 3000, cE: 3003, type: 'PRIMARY', matchScore: 100, effect: -3.1, lci: -75.0, uci: 68.9, estimandType: 'MD' },

                        { shortLabel: 'AE_ANY', title: 'Any adverse event from randomisation to 4 weeks post partum', tE: 183, cE: 170, type: 'SAFETY', matchScore: 80, effect: 1.08, lci: 0.92, uci: 1.27, estimandType: 'RR' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Pasricha SR, Mwangi MN, Moya E, et al. Ferric carboxymaltose versus standard-of-care oral iron to treat second-trimester anaemia in Malawian pregnant women: a randomised controlled trial. Lancet 2023;401:1595-1609. PMID 37088092. DOI 10.1016/S0140-6736(23)00278-7. ANZCTR ACTRN12618001268235.',

                    sourceUrl: 'https://doi.org/10.1016/S0140-6736(23)00278-7',

                    ctgovUrl: null,

                    evidence: [
                        { label: 'Enrollment', source: 'Pasricha 2023 Lancet, CONSORT', text: '862 women with singleton pregnancy 13-26 weeks gestation, capillary haemoglobin <10.0 g/dL, and negative malaria rapid diagnostic test, recruited at 21 primary-care and outpatient sites across two southern regions of Malawi between Nov 2018 and Mar 2021. Individually randomized 1:1 by sealed envelope to single-dose IV ferric carboxymaltose up to 1000 mg (n=430) or standard-of-care oral iron (60 mg elemental BID for 90 days, n=432). All received intermittent preventive malaria treatment. Anemia prevalence at recruitment 46% (matches WHO sub-Saharan Africa baseline). 21,258 screened to enroll 862. Outcome assessors masked; participants/study nurses unmasked.', highlights: ['862', 'Malawi', '13-26 weeks', '<10.0 g/dL', '430', '432', '21,258 screened', 'malaria-endemic', 'open-label'] },
                        { label: 'Primary maternal outcome — anaemia at 36 weeks', source: 'Pasricha 2023 Lancet, primary maternal endpoint', text: 'Anaemia (Hb<11.0 g/dL) at 36 weeks gestation: FCM 179/341 (52%) vs SOC 189/333 (57%); prevalence ratio 0.92 (95% CI 0.81 to 1.06; P=0.27). NULL effect — IV ferric carboxymaltose did NOT reduce anemia prevalence at 36 weeks gestation compared with WHO-standard oral iron in this malaria-endemic Malawian population. Anemia prevalence was numerically lower in the FCM arm at every timepoint, with statistical significance only at 4 weeks post-treatment (PR 0.91, 0.85-0.97). Mean birthweight: -3.1 g difference (95% CI -75.0 to +68.9; P=0.93) — also null. AE: 43% FCM vs 39% SOC (P=0.34); no infusion-related SAEs.', highlights: ['179', '341', '52%', '189', '333', '57%', '0.92', '0.81', '1.06', 'P=0.27', 'NULL', '-3.1 g', 'P=0.93'] },
                        { label: 'Risk of Bias (RoB 2.0)', source: 'Pasricha 2023 design + RoB 2.0', text: 'D1 LOW (sealed-envelope individual randomization). D2 HIGH (open-label by design — IV vs oral, visibly different). D3 LOW (78% retention to 36-week endpoint). D4 LOW (laboratory haemoglobin and birthweight measured by masked assessors). D5 LOW (SAP locked).', highlights: ['LOW', 'sealed-envelope', 'open-label', 'HIGH', '78%', 'masked', 'SAP locked'] }
                    ]
                }
            }"""


# ==========================
# TOPIC 19: VESTED IMPAACT 2010 — Pregnancy HIV ART
# ==========================
VESTED_BODY = """

                'NCT03048422': {

                    name: 'IMPAACT 2010 / VESTED', pmid: '33891894', phase: 'III', year: 2021, tE: 395, tN: 426, cE: 184, cN: 217, group: 'Lockman S, Brummel SS, Ziemba L, et al. Lancet HIV 2021;8:e521-e533 (PMID 33891894). NIH/NIAID-sponsored phase 3 multinational randomized open-label trial in HIV-1-positive pregnant women aged 18+ at 14-28 weeks gestation, ART-naive. Sites: predominantly sub-Saharan Africa (Botswana, South Africa Soweto/Wits/Umlazi/Famcru, Tanzania KCMC Moshi, Uganda Baylor Kampala, Zimbabwe Seke North/St Marys/Harare = ~70% of enrolment) plus India Pune, Brazil 4 sites, Thailand 3 sites, USA Florida 2 sites. n=643 randomized 1:1:1 to (1) DTG+FTC/TAF (n=217), (2) DTG+FTC/TDF (n=215), (3) EFV/FTC/TDF (n=211). Primary efficacy: maternal HIV-1 RNA <200 copies/mL at delivery (NI margin -10pp); primary safety: composite adverse pregnancy outcome (APO: spontaneous abortion + stillbirth + preterm + small-for-gestational-age) + maternal grade ≥3 AE + infant grade ≥3 AE. RESULT: viral suppression DTG-pooled 395/418 (94.5%) vs EFV 184/200 (92.0%) — DTG superior (diff +5.4pp, 95% CI +1.0 to +9.7); APO favoured DTG over EFV (24% vs 33%); maternal weight gain higher with DTG. Drove WHO 2021 guideline preference for DTG-based ART in pregnancy and breastfeeding (replacing EFV-based as preferred first-line). Africa relevance: ~70% sub-Saharan African enrolment + WHO 2021 guideline driver = pivotal evidence for African PMTCT programs.',

                    estimandType: 'RR', publishedHR: 1.03, hrLCI: 0.99, hrUCI: 1.07, pubHR: 1.03,

                    allOutcomes: [
                        { shortLabel: 'VL_DEL', title: 'Maternal viral suppression <200 copies/mL at delivery (DTG-pooled vs EFV)', tE: 395, cE: 184, type: 'PRIMARY', matchScore: 100, effect: 1.03, lci: 0.99, uci: 1.07, estimandType: 'RR' },

                        { shortLabel: 'APO', title: 'Adverse pregnancy outcome composite (DTG-pooled vs EFV) — primary safety', tE: 100, cE: 70, type: 'PRIMARY', matchScore: 100, effect: 0.71, lci: 0.55, uci: 0.93, estimandType: 'RR' },

                        { shortLabel: 'WTG_KG', title: 'Mean maternal weight gain antepartum (kg/wk, DTG-pooled vs EFV)', tE: 350, cE: 250, type: 'SAFETY', matchScore: 80, effect: 0.20, lci: 0.13, uci: 0.27, estimandType: 'MD' }
                    ],

                    rob: ['low', 'high', 'low', 'low', 'low'],

                    snippet: 'Source: Lockman S, Brummel SS, Ziemba L, et al. Efficacy and safety of dolutegravir with emtricitabine and tenofovir alafenamide fumarate or tenofovir disoproxil fumarate, and efavirenz, emtricitabine, and tenofovir disoproxil fumarate HIV antiretroviral therapy regimens started in pregnancy (IMPAACT 2010/VESTED): a multicentre, open-label, randomised, controlled, phase 3 trial. Lancet HIV 2021;8:e521-e533. PMID 33891894. DOI 10.1016/S2352-3018(21)00132-7.',

                    sourceUrl: 'https://doi.org/10.1016/S2352-3018(21)00132-7',

                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT03048422',

                    evidence: [
                        { label: 'Enrollment', source: 'Lockman 2021 Lancet HIV, CONSORT', text: '643 ART-naive HIV-1-positive pregnant women aged 18+ at gestational age 14-28 weeks across 21 sites in 9 countries. Predominantly sub-Saharan Africa: Botswana (Gaborone+Molepolole), South Africa (Soweto+Wits Shandukani+Umlazi+Famcru), Tanzania (KCMC Moshi), Uganda (Baylor Kampala), Zimbabwe (Seke North+St Marys+Harare Family Care) — ~70% of enrolment. Plus India (Pune), Brazil (4 sites), Thailand (3 sites), USA (Florida 2 sites). Randomized 1:1:1 to (1) DTG+FTC/TAF (n=217), (2) DTG+FTC/TDF (n=215), (3) EFV/FTC/TDF (n=211). Open-label.', highlights: ['643', '14-28 weeks', 'sub-Saharan Africa', '70%', 'Botswana', 'South Africa', 'Tanzania', 'Uganda', 'Zimbabwe', 'DTG', 'EFV', '1:1:1'] },
                        { label: 'Primary outcomes — viral suppression + APO composite', source: 'Lockman 2021 Lancet HIV, primary endpoints', text: 'Maternal HIV-1 RNA <200 copies/mL at delivery: DTG-pooled 395/418 (94.5%) vs EFV 184/200 (92.0%); difference +5.4 percentage points (95% CI +1.0 to +9.7) — DTG SUPERIOR over the prespecified non-inferiority margin (10pp) and meeting superiority. Adverse pregnancy outcome composite (spontaneous abortion + stillbirth + preterm + SGA): DTG-pooled 24% vs EFV 33% — RR 0.71 (0.55-0.93). Stillbirth + neonatal death lower with DTG. Maternal weight gain higher with DTG. Drove WHO 2021 guideline preference for DTG-based ART in pregnancy and breastfeeding (replacing EFV-based as preferred first-line). VESTED is the pivotal evidence for African PMTCT programs.', highlights: ['395', '418', '94.5%', '184', '200', '92.0%', '+5.4', 'SUPERIOR', '24%', '33%', 'RR 0.71', '0.55', '0.93', 'WHO 2021'] },
                        { label: 'Risk of Bias (RoB 2.0)', source: 'VESTED design + RoB 2.0', text: 'D1 LOW (central computer-generated 1:1:1 randomization with site stratification). D2 HIGH (open-label by design — different pill burdens; participants and clinicians knew arm). D3 LOW (>=95% follow-up at delivery; central HIV-1 RNA testing). D4 LOW (independent endpoint adjudication for adverse pregnancy outcomes; central laboratory). D5 LOW (SAP locked).', highlights: ['LOW', 'central', '1:1:1', 'open-label', 'HIGH', '95%', 'central HIV-1 RNA', 'adjudication'] }
                    ]
                }
            }"""


def build_iron():
    FILE = Path("PREGNANCY_IRON_FCM_REVIEW.html")
    text = FILE.read_text(encoding="utf-8")
    text = replace_or_die(text,
        "<title>RapidMeta Cardiology | SGLT2-HF Ultra-Precision v12.0</title>",
        "<title>RapidMeta Maternal Health | IV Ferric Carboxymaltose vs Oral Iron in Pregnancy v0.1 (Pasricha 2023 Malawi, post-2018)</title>")
    text = replace_or_die(text,
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT03036124', 'NCT03057977', 'NCT03057951', 'NCT03619213', 'NCT03521934']);",
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['LEGACY-ANZCTR-12618001268235-FCM']);")
    text = replace_or_die(text,
        "protocol: { pop: 'Adults with heart failure across ejection fraction spectrum', int: 'SGLT2 or dual SGLT1/2 inhibitor therapy (dapagliflozin, empagliflozin, or sotagliflozin)', comp: 'Placebo + guideline-directed therapy', out: 'CV Death or Worsening Heart Failure Composite', subgroup: 'EF phenotype (HFrEF vs HFpEF), drug class member, diabetes status', query: '', rctOnly: true, post2015: true },",
        "protocol: { pop: 'Pregnant women aged 18+ with singleton pregnancy 13-26 weeks gestation, capillary Hb<10.0 g/dL, and negative malaria RDT, recruited at 21 primary-care and outpatient sites across two southern regions of malaria-endemic Malawi (sub-Saharan Africa)', int: 'Single-dose intravenous ferric carboxymaltose up to 1000 mg administered once at enrolment in outpatient primary-care setting', comp: 'WHO standard-of-care oral iron — 60 mg elemental iron twice daily for 90 days', out: 'Anaemia (Hb<11.0 g/dL) at 36 weeks gestation (primary maternal); birthweight (primary neonatal); AE incidence; all-cause hospitalization', subgroup: 'Baseline Hb, gestational age band, parity, malaria infection during pregnancy, region', query: '', rctOnly: true, post2015: true },")
    text = replace_or_die(text,
        "{ 'DAPA-HF': 'Dapagliflozin', 'DELIVER': 'Dapagliflozin', 'EMPEROR-Reduced': 'Empagliflozin', 'EMPEROR-Preserved': 'Empagliflozin', 'SOLOIST-WHF': 'Sotagliflozin' }",
        "{ 'Pasricha 2023 Malawi (FCM vs oral iron)': 'Single-dose intravenous ferric carboxymaltose' }")
    text = replace_or_die(text,
        "'NCT03036124': 'DAPA-HF',\n\n\n                'NCT03057977': 'EMPEROR-Reduced',\n\n\n                'NCT03057951': 'EMPEROR-Preserved',\n\n\n                'NCT03619213': 'DELIVER',\n\n\n                'NCT03521934': 'SOLOIST-WHF'",
        "'LEGACY-ANZCTR-12618001268235-FCM': 'Pasricha 2023 Malawi'")
    text = replace_realdata(text, IRON_BODY)
    text = text.replace("SGLT2-HF v1.0", "Iron Pregnancy v0.1")
    text = text.replace("SGLT2 Inhibitors for Heart Failure Outcomes: A Living Systematic Review and Meta-Analysis of Randomized Controlled Trials",
                        "Single-Dose IV Ferric Carboxymaltose vs Standard Oral Iron for Second-Trimester Anaemia in Malawian Pregnant Women: Single-Trial Pairwise Review (Pasricha 2023, post-2018)")
    text = text.replace("SGLT2 Inhibitors in Heart Failure", "IV Ferric Carboxymaltose in Pregnancy Anaemia")
    text = text.replace('value="Adults with heart failure"', 'value="Pregnant women with second-trimester anaemia, malaria-endemic SSA"')
    text = text.replace("value=\"Heart Failure\"", "value=\"Maternal Anaemia\"")
    FILE.write_text(text, encoding="utf-8")
    print(f"  Iron: {FILE.stat().st_size:,}")


def build_vested():
    FILE = Path("PREGNANCY_HIV_VESTED_REVIEW.html")
    text = FILE.read_text(encoding="utf-8")
    text = replace_or_die(text,
        "<title>RapidMeta Cardiology | SGLT2-HF Ultra-Precision v12.0</title>",
        "<title>RapidMeta HIV/Maternal | DTG vs EFV ART in Pregnancy v0.1 (VESTED IMPAACT 2010, post-2017)</title>")
    text = replace_or_die(text,
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT03036124', 'NCT03057977', 'NCT03057951', 'NCT03619213', 'NCT03521934']);",
        "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT03048422']);")
    text = replace_or_die(text,
        "protocol: { pop: 'Adults with heart failure across ejection fraction spectrum', int: 'SGLT2 or dual SGLT1/2 inhibitor therapy (dapagliflozin, empagliflozin, or sotagliflozin)', comp: 'Placebo + guideline-directed therapy', out: 'CV Death or Worsening Heart Failure Composite', subgroup: 'EF phenotype (HFrEF vs HFpEF), drug class member, diabetes status', query: '', rctOnly: true, post2015: true },",
        "protocol: { pop: 'ART-naive HIV-1-positive pregnant women aged 18+ at gestational age 14-28 weeks. Sites in Botswana, South Africa (4 sites), Tanzania, Uganda, Zimbabwe (3 sites), India, Brazil (4 sites), Thailand (3 sites), USA — predominantly sub-Saharan African enrolment (~70%)', int: 'Dolutegravir-based ART (DTG+FTC/TAF or DTG+FTC/TDF) initiated in pregnancy, continued through delivery and 50 weeks postpartum', comp: 'Efavirenz-based ART (EFV+FTC/TDF, the WHO 2018 preferred first-line at trial design)', out: 'Maternal HIV-1 RNA <200 copies/mL at delivery (primary efficacy); composite adverse pregnancy outcome (spontaneous abortion + stillbirth + preterm + small-for-gestational-age); maternal grade >=3 AE; infant grade >=3 AE through 50 weeks postpartum', subgroup: 'Country, baseline viral load, gestational age band, infant feeding mode (breastfeeding vs replacement)', query: '', rctOnly: true, post2015: true },")
    text = replace_or_die(text,
        "{ 'DAPA-HF': 'Dapagliflozin', 'DELIVER': 'Dapagliflozin', 'EMPEROR-Reduced': 'Empagliflozin', 'EMPEROR-Preserved': 'Empagliflozin', 'SOLOIST-WHF': 'Sotagliflozin' }",
        "{ 'IMPAACT 2010 / VESTED': 'Dolutegravir-based ART (DTG+FTC/TAF or DTG+FTC/TDF)' }")
    text = replace_or_die(text,
        "'NCT03036124': 'DAPA-HF',\n\n\n                'NCT03057977': 'EMPEROR-Reduced',\n\n\n                'NCT03057951': 'EMPEROR-Preserved',\n\n\n                'NCT03619213': 'DELIVER',\n\n\n                'NCT03521934': 'SOLOIST-WHF'",
        "'NCT03048422': 'IMPAACT 2010 / VESTED'")
    text = replace_realdata(text, VESTED_BODY)
    text = text.replace("SGLT2-HF v1.0", "VESTED v0.1")
    text = text.replace("SGLT2 Inhibitors for Heart Failure Outcomes: A Living Systematic Review and Meta-Analysis of Randomized Controlled Trials",
                        "Dolutegravir vs Efavirenz Antiretroviral Therapy Initiated in Pregnancy: Single-Trial Pairwise Review of IMPAACT 2010 / VESTED (Lockman 2021, post-2017)")
    text = text.replace("SGLT2 Inhibitors in Heart Failure", "DTG vs EFV in Pregnancy HIV")
    text = text.replace('value="Adults with heart failure"', 'value="HIV-1-positive pregnant women, sub-Saharan Africa primary"')
    text = text.replace("value=\"Heart Failure\"", "value=\"Pregnancy HIV ART\"")
    FILE.write_text(text, encoding="utf-8")
    print(f"  VESTED: {FILE.stat().st_size:,}")


if __name__ == "__main__":
    build_iron()
    build_vested()
