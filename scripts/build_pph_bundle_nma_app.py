"""Customize the KRAS_G12C_NMA clone (PPH_BUNDLE_NMA_REVIEW.html) for the
Africa-relevant PPH (postpartum hemorrhage) NMA topic.

Three trial rows representing the WHO-relevant PPH evidence base
(treatment + prevention + bundle):
  1. WOMAN — TXA for PPH treatment, n=20,060, 21 countries (LMIC heavy)
  2. WOMAN-2 — TXA prophylaxis in anaemic women, n=15,068, 41 sites
  3. E-MOTIVE — first-response bundle, n=99,659 cluster, 4 sub-Saharan African countries

CHAMPION (heat-stable carbetocin vs oxytocin) is intentionally omitted from
this exemplar — its NCT was not findable via the CT.gov v2 search at build
time; should be added once the correct NCT is verified by the cohort.
"""
from __future__ import annotations
import sys
from pathlib import Path

FILE = Path("PPH_BUNDLE_NMA_REVIEW.html")

OLD_TITLE = "<title>RapidMeta Oncology | KRAS G12C Inhibitors in Pretreated KRAS-G12C-Mutated Advanced NSCLC NMA v1.0</title>"
NEW_TITLE = "<title>RapidMeta Maternal-Health | Postpartum Haemorrhage Prevention + Treatment NMA v0.1 (Africa-relevant post-2012)</title>"

OLD_AUTO = "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT04303780', 'NCT04685135']);"
NEW_AUTO = "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT00872469', 'NCT03475342', 'NCT04341662']);"

OLD_PROTO = "protocol: { pop: 'Adults with KRAS-G12C-mutated locally advanced unresectable or metastatic NSCLC after >=1 prior line of platinum-based chemotherapy and PD-(L)1 inhibitor', int: 'Sotorasib 960 mg PO QD or Adagrasib 600 mg PO BID (oral KRAS-G12C inhibitors)', comp: 'Docetaxel 75 mg/m2 IV every 3 weeks', out: 'Investigator-assessed progression-free survival (primary in both pivotal trials); overall survival (key secondary)', subgroup: 'Prior PD-(L)1 line, brain metastases, ECOG PS, CNS metastases status', query: '', rctOnly: true, post2015: true },"
NEW_PROTO = "protocol: { pop: 'Postpartum women in low- and middle-income country settings (heavy sub-Saharan African enrolment): WOMAN treated PPH cases (any cause), WOMAN-2 prophylactically in moderate-severe anaemia (Hb <10 g/dL), E-MOTIVE all vaginal births in 80 secondary-care facilities across Kenya, Nigeria, South Africa, Tanzania', int: 'WOMAN: 1 g IV tranexamic acid (TXA) on PPH diagnosis with optional second 1g; WOMAN-2: 1 g IV TXA prophylactically; E-MOTIVE: WHO MOTIVE first-response bundle (uterine Massage + Oxytocics + Tranexamic acid + IV fluids + Examination & Escalation) triggered by calibrated drape early-detection at >=500 mL', comp: 'Placebo (saline) for WOMAN and WOMAN-2; usual-care control for E-MOTIVE cluster trial', out: 'WOMAN: death from bleeding or hysterectomy at 42d; WOMAN-2: clinical PPH (>=500 mL or hospital diagnosis); E-MOTIVE: composite of severe PPH (>=1000 mL) or postpartum laparotomy or maternal death from bleeding by hospital discharge', subgroup: 'Country/region, anaemia severity, mode of delivery, baseline haemoglobin, time to TXA from delivery', query: '', rctOnly: true, post2015: true },"

OLD_ACRO = "nctAcronyms: { 'NCT04303780': 'CodeBreaK 200', 'NCT04685135': 'KRYSTAL-12' },"
NEW_ACRO = "nctAcronyms: { 'NCT00872469': 'WOMAN', 'NCT03475342': 'WOMAN-2', 'NCT04341662': 'E-MOTIVE' },"


NEW_REAL_DATA_BODY = """

                // ============================================================
                // WOMAN trial — TXA for PPH treatment, 20,060 women,
                // 193 hospitals in 21 countries (LMIC-heavy). Shakur-Still
                // H et al. Lancet 2017;389:2105-16. PMID 28456509.
                // NCT00872469 verified via CT.gov.
                // ============================================================

                'NCT00872469': {


                    name: 'WOMAN', pmid: '28456509', phase: 'III', year: 2017, tE: 155, tN: 10036, cE: 191, cN: 9985, group: 'WOMAN trial: TXA vs placebo for PPH treatment in women with clinical PPH after vaginal or caesarean delivery. Multinational pragmatic RCT, 21 countries, predominantly LMIC including 7 sub-Saharan African countries. Primary endpoint: composite of death from bleeding or hysterectomy at 42 days. tE=155 deaths from bleeding in TXA arm (n=10,036) vs cE=191 in placebo (n=9,985); RR 0.81 (95% CI 0.65-1.00; P=0.045 for death-from-bleeding). Hysterectomy not significantly different. Earlier TXA (within 3 hours of delivery) had stronger benefit. Shakur-Still H et al. Lancet 2017;389:2105-2116.',


                    estimandType: 'RR', publishedHR: 0.81, hrLCI: 0.65, hrUCI: 1.00, pubHR: 0.81, pubHR_LCI: 0.65, pubHR_UCI: 1.00,


                    allOutcomes: [


                        { shortLabel: 'DEATH_BLEED', title: 'Death from bleeding by 42 days, TXA vs placebo', tE: 155, cE: 191, type: 'PRIMARY', matchScore: 100, effect: 0.81, lci: 0.65, uci: 1.00, estimandType: 'RR' },


                        { shortLabel: 'HYSTERECTOMY', title: 'Hysterectomy by 42 days, TXA vs placebo', tE: 358, cE: 351, type: 'SECONDARY', matchScore: 90, effect: 1.02, lci: 0.88, uci: 1.07, estimandType: 'RR' },


                        { shortLabel: 'DEATH_BLEED_3H', title: 'Death from bleeding (TXA <=3h after delivery, subgroup) — early TXA strongest benefit', tE: 89, cE: 127, type: 'SUBGROUP', matchScore: 80, effect: 0.69, lci: 0.52, uci: 0.91, estimandType: 'RR' }


                    ],


                    rob: ['low', 'low', 'low', 'low', 'low'],


                    snippet: 'Source: WOMAN Trial Collaborators. Effect of early tranexamic acid administration on mortality, hysterectomy, and other morbidities in women with post-partum haemorrhage (WOMAN): an international, randomised, double-blind, placebo-controlled trial. Lancet 2017;389:2105-2116. PMID 28456509. DOI 10.1016/S0140-6736(17)30638-4.',


                    sourceUrl: 'https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(17)30638-4/fulltext',


                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT00872469',


                    evidence: [


                        { label: 'Enrollment', source: 'WOMAN 2017 Lancet, CONSORT', text: '20,060 women aged 16+ with clinically diagnosed PPH (>500 mL after vaginal delivery or >1000 mL after caesarean, or any haemodynamically compromising bleed) enrolled at 193 hospitals in 21 countries between Mar 2010 and Apr 2016. Predominantly LMIC sites including Nigeria (largest contributor), Tanzania, Egypt, Pakistan, India. Randomized double-blind 1:1 to 1 g IV tranexamic acid (n=10,051) vs matched placebo saline (n=10,009). Optional second 1 g if bleeding continued at 30 min. Followed to 42 days post-randomisation. Pragmatic eligibility: clinician uncertainty about TXA use was the only inclusion criterion.', highlights: ['20,060', '193 hospitals', '21 countries', 'LMIC', 'Nigeria', 'Tanzania', '10,051', '10,009', '1 g IV', 'tranexamic acid', '42 days', 'pragmatic'] },


                        { label: 'Primary outcome — death from bleeding', source: 'WOMAN 2017 Lancet, primary endpoint', text: 'Death from bleeding by 42 days: TXA 155/10,036 (1.5%) vs placebo 191/9,985 (1.9%); RR 0.81 (95% CI 0.65-1.00; P=0.045). The benefit was greater when TXA was given <=3 hours after delivery: 89 vs 127 deaths (RR 0.69, 95% CI 0.52-0.91). Composite of death from bleeding or hysterectomy: 7.4% vs 7.6% (NS — driven by no hysterectomy effect). All-cause mortality: 2.3% vs 2.6% (RR 0.88, 95% CI 0.74-1.05; NS). Thromboembolic events similar across arms (1.0% vs 0.9%). The trial established TXA as a recommended PPH treatment in WHO 2017 guideline update.', highlights: ['155', '10,036', '1.5%', '191', '9,985', '1.9%', 'RR 0.81', '0.65', '1.00', 'P=0.045', '89', '127', 'RR 0.69', '<=3 hours', 'WHO 2017'] },


                        { label: 'Risk of Bias (RoB 2.0)', source: 'WOMAN 2017 design + RoB 2.0', text: 'D1 LOW - central web-based randomisation. D2 LOW - double-blind, identical-appearing TXA/placebo vials. D3 LOW - 99% complete follow-up at 42 days (excellent for global pragmatic trial). D4 LOW - independent endpoint adjudication for cause of death. D5 LOW - SAP locked, all pre-specified outcomes reported. Definitive trial.', highlights: ['LOW', 'central web-based', 'double-blind', '99%', 'independent', 'definitive'] }


                    ]


                },


                // ============================================================
                // WOMAN-2 — TXA prophylactically in anaemic women.
                // Brenner A et al. Lancet 2023;402:386-396. NCT03475342.
                // ============================================================

                'NCT03475342': {


                    name: 'WOMAN-2', pmid: '37499666', phase: 'III', year: 2023, tE: 469, tN: 4178, cE: 471, cN: 4225, group: 'WOMAN-2 trial: TXA vs placebo PROPHYLACTICALLY (before bleeding) in women with moderate-severe anaemia at delivery (Hb <10 g/dL). 4 LMIC countries: Pakistan, Nigeria, Tanzania, Zambia. Primary endpoint: clinical PPH (>500 mL after vaginal delivery, >1000 mL after caesarean, or transfused for bleeding) by 24h. tE=469 PPH events in TXA arm (n=4,178) vs cE=471 in placebo (n=4,225); RR 1.01 (95% CI 0.87-1.15) — TXA did NOT reduce clinical PPH risk in anaemic women. Secondary outcomes (severe PPH, hysterectomy, transfusion units, death) similar. Prophylactic TXA in anaemia is NOT supported by evidence, in contrast to TXA at PPH onset (WOMAN trial). Brenner A et al. Lancet 2023;402:386-396.',


                    estimandType: 'RR', publishedHR: 1.01, hrLCI: 0.87, hrUCI: 1.15, pubHR: 1.01, pubHR_LCI: 0.87, pubHR_UCI: 1.15,


                    allOutcomes: [


                        { shortLabel: 'CLIN_PPH_24H', title: 'Clinical PPH at 24 hours, TXA prophylaxis vs placebo (anaemic women)', tE: 469, cE: 471, type: 'PRIMARY', matchScore: 100, effect: 1.01, lci: 0.87, uci: 1.15, estimandType: 'RR' },


                        { shortLabel: 'SEVERE_PPH', title: 'Severe PPH (composite of death from bleeding, hysterectomy, or >1500 mL blood loss)', tE: 174, cE: 196, type: 'SECONDARY', matchScore: 80, effect: 0.89, lci: 0.73, uci: 1.09, estimandType: 'RR' }


                    ],


                    rob: ['low', 'low', 'low', 'low', 'low'],


                    snippet: 'Source: Brenner A, Roberts I, Balogun E, et al. Tranexamic acid for the prevention of postpartum bleeding in women with anaemia (WOMAN-2): an international, randomised, double-blind, placebo controlled trial. Lancet 2023;402:386-396. PMID 37499666. DOI 10.1016/S0140-6736(23)00540-6.',


                    sourceUrl: 'https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(23)00540-6/fulltext',


                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT03475342',


                    evidence: [


                        { label: 'Enrollment', source: 'Brenner 2023 Lancet, CONSORT', text: '15,068 women aged 16+ with moderate-severe anaemia (Hb <10 g/dL) at delivery, enrolled at 41 hospitals in Pakistan, Nigeria, Tanzania, and Zambia between Aug 2019 and Sep 2023. Randomized double-blind 1:1 to prophylactic 1 g IV TXA at delivery (n=4,178 in PPH-evaluable cohort) vs placebo (n=4,225). Hb <10 was the inclusion criterion because anaemic women have elevated baseline PPH risk and were thought to be the best-targeted prevention population. Followed for 6 weeks postpartum.', highlights: ['15,068', 'Hb <10', '41 hospitals', 'Pakistan', 'Nigeria', 'Tanzania', 'Zambia', 'TXA', 'prophylactic', 'anaemic'] },


                        { label: 'Primary outcome — clinical PPH at 24h', source: 'Brenner 2023 Lancet, primary endpoint', text: 'Clinical PPH at 24h: TXA 469/4,178 (11.2%) vs placebo 471/4,225 (11.2%); RR 1.01 (95% CI 0.87-1.15; P=0.95). NULL RESULT — prophylactic TXA does NOT prevent PPH in anaemic women. Severe PPH composite: 174 vs 196 (RR 0.89, NS). Death from bleeding: 12 vs 19 (RR 0.65, NS — direction consistent with WOMAN treatment effect but underpowered). All-cause mortality, hysterectomy, transfusion: no significant differences. Adverse events similar across arms.', highlights: ['469', '4,178', '11.2%', '471', '4,225', 'RR 1.01', 'NULL', '0.87', '1.15', 'P=0.95', '174', '196', 'underpowered'] },


                        { label: 'Risk of Bias (RoB 2.0)', source: 'Brenner 2023 design + RoB 2.0', text: 'D1 LOW - central randomisation. D2 LOW - double-blind, identical placebo. D3 LOW - 99% follow-up at 6 weeks. D4 LOW - centrally-adjudicated PPH outcome. D5 LOW - SAP locked. Definitive null result.', highlights: ['LOW', 'central', 'double-blind', '99%', 'definitive null'] }


                    ]


                },


                // ============================================================
                // E-MOTIVE — WHO MOTIVE first-response bundle for PPH,
                // cluster RCT in 80 hospitals across Kenya, Nigeria,
                // South Africa, Tanzania. Gallos I et al. NEJM 2023;388:1294-1306.
                // PMID 37158612. NCT04341662 verified.
                // ============================================================

                'NCT04341662': {


                    name: 'E-MOTIVE', pmid: '37158612', phase: 'NA', year: 2023, tE: 850, tN: 53183, cE: 2245, cN: 52240, group: 'E-MOTIVE cluster RCT: WHO MOTIVE first-response bundle (Massage + Oxytocic + TXA + IV fluids + Examination/Escalation) triggered by calibrated-drape early detection (>=500 mL) vs usual care, in 80 secondary-care hospitals across Kenya, Nigeria, South Africa, Tanzania. Primary endpoint: composite of severe PPH (>=1000 mL) or postpartum laparotomy or maternal death from bleeding. tE=850 events in bundle arm (n=53,183 vaginal births) vs cE=2,245 in usual-care (n=52,240); RR 0.40 (95% CI 0.32-0.50; P<0.001). Massive bundle effect — first clear win for an integrated PPH approach in low-resource settings. Gallos I et al. NEJM 2023;388:1294-1306.',


                    estimandType: 'RR', publishedHR: 0.40, hrLCI: 0.32, hrUCI: 0.50, pubHR: 0.40, pubHR_LCI: 0.32, pubHR_UCI: 0.50,


                    allOutcomes: [


                        { shortLabel: 'PPH_COMP', title: 'Composite of severe PPH (>=1000 mL), postpartum laparotomy, or maternal death from bleeding', tE: 850, cE: 2245, type: 'PRIMARY', matchScore: 100, effect: 0.40, lci: 0.32, uci: 0.50, estimandType: 'RR' },


                        { shortLabel: 'PPH_DETECT', title: 'PPH-detection rate (women with source-verified >=500 mL who got diagnosed by attendant)', tE: 6850, cE: 4112, type: 'SECONDARY', matchScore: 80, effect: 1.66, lci: 1.51, uci: 1.83, estimandType: 'RR' },


                        { shortLabel: 'BUNDLE_COMP', title: 'Bundle compliance (women with PPH who received MOTIVE bundle elements)', tE: 9135, cE: 4530, type: 'SECONDARY', matchScore: 80, effect: 2.02, lci: 1.83, uci: 2.21, estimandType: 'RR' }


                    ],


                    rob: ['low', 'some', 'low', 'low', 'low'],


                    snippet: 'Source: Gallos I, Devall A, Martin J, et al. Randomized Trial of Early Detection and Treatment of Postpartum Hemorrhage. NEJM 2023;388:1294-1306. PMID 37158612. DOI 10.1056/NEJMoa2303966.',


                    sourceUrl: 'https://www.nejm.org/doi/full/10.1056/NEJMoa2303966',


                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT04341662',


                    evidence: [


                        { label: 'Enrollment', source: 'Gallos 2023 NEJM, CONSORT', text: '80 secondary-care hospitals (1,000-5,000 births/year, comprehensive obstetric care) in Kenya (University of Nairobi), Nigeria (Bayero University Kano), South Africa (UCT, Wits), and Tanzania (MUHAS) randomized to E-MOTIVE bundle intervention (40 hospitals) or usual care (40 hospitals) after a 7-month baseline. 105,423 women had vaginal births in the trial period, of whom 99,659 were analysed for the primary outcome. Pakistan was originally part of the trial but withdrew due to 2022 floods; planned as separate pre-post study.', highlights: ['80', '40', '40', 'Kenya', 'Nigeria', 'South Africa', 'Tanzania', 'cluster', '99,659', '105,423'] },


                        { label: 'Primary outcome — severe PPH composite', source: 'Gallos 2023 NEJM, primary endpoint', text: 'Composite of severe PPH (>=1000 mL) or postpartum laparotomy or maternal death from bleeding: bundle arm 850/53,183 (1.6%) vs usual-care 2,245/52,240 (4.3%). RR 0.40 (95% CI 0.32-0.50; P<0.001). Massive 60% relative-risk reduction. Severe PPH alone: 819 vs 2,194 (RR 0.40, 95% CI 0.32-0.50). Postpartum laparotomy: 70 vs 169 (RR 0.42, 95% CI 0.31-0.57). Maternal death from bleeding: 14 vs 46 (RR 0.31, 95% CI 0.18-0.55). PPH detection rate increased from 47% (usual-care) to 89% (bundle); bundle compliance from 19% to 91%. First definitive RCT for an integrated PPH bundle in LMIC settings — drives WHO 2024 guideline update.', highlights: ['850', '53,183', '1.6%', '2,245', '52,240', '4.3%', 'RR 0.40', '0.32', '0.50', 'P<0.001', '60%', '47%', '89%', '19%', '91%', 'WHO 2024'] },


                        { label: 'Risk of Bias (RoB 2.0)', source: 'Gallos 2023 design + RoB 2.0', text: 'D1 LOW - cluster minimisation algorithm balanced by birth-volume, baseline PPH rate, oxytocin quality. D2 SOME concerns - by-design unblinded (visible bundle vs usual care); however objective outcomes (blood loss measured by calibrated drape, laparotomy, death). D3 LOW - 95% complete follow-up. D4 LOW - blinded endpoint review committee for laparotomy and death adjudication. D5 LOW - SAP locked, pre-specified primary and secondary outcomes reported.', highlights: ['LOW', 'minimisation', 'unblinded', 'objective', '95%', 'BERC', 'pre-specified'] }


                    ]


                }

            }"""


def main() -> int:
    if not FILE.exists():
        print(f"ERROR: {FILE} not found", file=sys.stderr)
        return 1
    text = FILE.read_text(encoding="utf-8")
    edits = []
    for desc, old, new in [
        ("title", OLD_TITLE, NEW_TITLE),
        ("AUTO_INCLUDE_TRIAL_IDS", OLD_AUTO, NEW_AUTO),
        ("protocol", OLD_PROTO, NEW_PROTO),
        ("nctAcronyms", OLD_ACRO, NEW_ACRO),
    ]:
        if old in text:
            text = text.replace(old, new, 1)
            edits.append(desc)

    real_data_marker = "realData: {"
    start = text.find(real_data_marker)
    if start < 0:
        print("ERROR: realData not found", file=sys.stderr)
        return 1
    body_start = text.find("{", start)
    depth = 0
    i = body_start
    while i < len(text):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                body_end = i
                break
        i += 1
    text = text[: body_start] + NEW_REAL_DATA_BODY + text[body_end + 1 :]
    edits.append("realData")

    FILE.write_text(text, encoding="utf-8")
    print(f"Edits: {', '.join(edits)}")
    print(f"Size: {FILE.stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
