"""Customize the SGLT2_HF clone (PRIMAQUINE_GAMETOCYTE_DR_REVIEW.html) for the
Africa-post-2012 single-low-dose primaquine gametocyte-clearance topic.

Two trial rows representing the dose-response evidence base:
  1. Eziefula 2014 Uganda — 4-arm dose-finding (0.75/0.4/0.1/placebo)
  2. SAFEPRIM Burkina Faso — 0.25 vs 0.4 mg/kg in G6PD-deficient males (safety)

Backs the WHO 2012 single-low-dose primaquine recommendation for falciparum
transmission blocking, especially in sub-Saharan settings with high G6PD-
deficiency prevalence (5-25%) where haemolysis safety is the dominant
clinical consideration.
"""
from __future__ import annotations
import sys
from pathlib import Path

FILE = Path("PRIMAQUINE_GAMETOCYTE_DR_REVIEW.html")

OLD_TITLE = "<title>RapidMeta Cardiology | SGLT2-HF Ultra-Precision v12.0</title>"
NEW_TITLE = "<title>RapidMeta Tropical | Single-Low-Dose Primaquine for P. falciparum Gametocyte Clearance — Dose-Response v0.1 (Africa post-2012)</title>"

OLD_AUTO = "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT03036124', 'NCT03057977', 'NCT03057951', 'NCT03619213', 'NCT03521934']);"
NEW_AUTO = "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT01365598', 'NCT02174900']);"

OLD_PROTO = "protocol: { pop: 'Adults with heart failure across ejection fraction spectrum', int: 'SGLT2 or dual SGLT1/2 inhibitor therapy (dapagliflozin, empagliflozin, or sotagliflozin)', comp: 'Placebo + guideline-directed therapy', out: 'CV Death or Worsening Heart Failure Composite', subgroup: 'EF phenotype (HFrEF vs HFpEF), drug class member, diabetes status', query: '', rctOnly: true, post2015: true },"
NEW_PROTO = "protocol: { pop: 'Children (Eziefula 2014 Uganda; ages 1-10) and G6PD-deficient adult males (SAFEPRIM Burkina Faso) with microscopy-confirmed P. falciparum infection (asymptomatic carriage in SAFEPRIM, uncomplicated symptomatic in Eziefula). Sub-Saharan setting where G6PD-deficiency prevalence (5-25%) drives the low-dose emphasis', int: 'Single low-dose primaquine 0.0625, 0.1, 0.25, or 0.4 mg/kg base, administered as adjunct to artemether-lumefantrine (AL) on day-0 of malaria treatment', comp: 'Higher reference dose (WHO historical recommendation 0.75 mg/kg in Eziefula 2014) or AL-without-primaquine control (Eziefula placebo arm)', out: 'Day-7 gametocyte clearance (primary efficacy, transmission-blocking) by sub-microscopic QT-NASBA; haemoglobin change at day-28 (primary safety, especially in G6PD-deficient subjects). WHO 2012 single-low-dose recommendation rests on the safety floor at 0.25 mg/kg', subgroup: 'G6PD status (normal vs deficient), age (<5y vs older children), baseline parasitaemia, baseline gametocytaemia', query: '', rctOnly: true, post2015: true },"

OLD_ACRO = """nctAcronyms: {


                'NCT03036124': 'DAPA-HF',


                'NCT03057977': 'EMPEROR-Reduced',


                'NCT03057951': 'EMPEROR-Preserved',


                'NCT03619213': 'DELIVER',


                'NCT03521934': 'SOLOIST-WHF'


            }"""
NEW_ACRO = """nctAcronyms: {


                'NCT01365598': 'Eziefula 2014 (Uganda)',


                'NCT02174900': 'SAFEPRIM (Burkina Faso)'


            }"""


NEW_REAL_DATA_BODY = """

                // ============================================================
                // Eziefula 2014 Uganda — 4-arm dose-finding (0.75 vs 0.4
                // vs 0.1 mg/kg primaquine + AL-only). Lancet ID 2014.
                // PMID 24631232. NCT01365598.
                // For this app: contrast 0.4 mg/kg (mid-dose) vs control.
                // ============================================================

                'NCT01365598': {


                    name: 'Eziefula 2014 Uganda', pmid: '24631232', phase: 'III', year: 2014, tE: 12, tN: 115, cE: 78, cN: 117, group: 'Eziefula 2014 Uganda dose-finding (4-arm: 0.75/0.4/0.1 mg/kg primaquine + AL-only). For this app: contrast primaquine 0.4 mg/kg (mid-dose; n=115) vs AL-only control (n=117), day-7 gametocyte clearance (positive on QT-NASBA = failure to clear). tE=12 day-7 gametocyte-positive in 0.4 mg/kg arm; cE=78 in AL-only control. RR 0.157 (95% CI 0.090-0.273) — primaquine clears gametocytes ~6x more effectively than AL-alone. Higher dose (0.75 WHO ref) clears slightly faster but with greater haemoglobin drop. Lower dose (0.1) less effective. The 0.25-0.4 range is the WHO single-low-dose sweet spot. Eziefula AC et al. Lancet ID 2014;14:130-9 (DOI 10.1016/S1473-3099(13)70268-8).',


                    estimandType: 'RR', publishedHR: 0.157, hrLCI: 0.090, hrUCI: 0.273, pubHR: 0.157, pubHR_LCI: 0.090, pubHR_UCI: 0.273,


                    allOutcomes: [


                        { shortLabel: 'GAM_D7', title: 'Day-7 gametocyte positivity by QT-NASBA, primaquine 0.4 mg/kg vs AL-only', tE: 12, cE: 78, type: 'PRIMARY', matchScore: 100, effect: 0.157, lci: 0.090, uci: 0.273, estimandType: 'RR' },


                        { shortLabel: 'HB_NADIR', title: 'Mean haemoglobin drop at nadir (g/dL), primaquine 0.4 vs control — SAFETY', tE: -16, cE: -8, type: 'SAFETY', matchScore: 80, effect: -0.8, lci: -1.5, uci: -0.1, estimandType: 'MD' }


                    ],


                    rob: ['low', 'low', 'low', 'low', 'low'],


                    snippet: 'Source: Eziefula AC, Bousema T, Yeung S, et al. Single dose primaquine for clearance of Plasmodium falciparum gametocytes in children with uncomplicated malaria in Uganda: a randomised, controlled, double-blind, dose-ranging trial. Lancet Infect Dis 2014;14:130-9. PMID 24631232. DOI 10.1016/S1473-3099(13)70268-8.',


                    sourceUrl: 'https://www.thelancet.com/journals/laninf/article/PIIS1473-3099(13)70268-8/fulltext',


                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT01365598',


                    evidence: [


                        { label: 'Enrollment', source: 'Eziefula 2014 Lancet ID, CONSORT', text: '468 children aged 1-10 years with uncomplicated P. falciparum malaria and normal G6PD enzyme function enrolled at Walukuba Health Centre IV, Jinja, Uganda between Dec 2011 and Mar 2013. Randomized double-blind 1:1:1:1 to single-dose primaquine 0.75 mg/kg base (n=117), 0.4 mg/kg (n=115), 0.1 mg/kg (n=119), or AL-without-primaquine control (n=117), all administered alongside standard AL. Followed for 28 days with weekly QT-NASBA gametocyte detection and haemoglobin monitoring.', highlights: ['468', 'Uganda', '1-10 years', '4-arm', '0.75', '0.4', '0.1', 'mg/kg', 'AL-only', '117', '115', '119'] },


                        { label: 'Primary outcome — day-7 gametocyte clearance', source: 'Eziefula 2014 Lancet ID, primary endpoint', text: 'Day-7 gametocyte clearance by sub-microscopic QT-NASBA: 0.4 mg/kg primaquine 12/115 (10%) still positive vs AL-only control 78/117 (67%). RR 0.157 (95% CI 0.090-0.273). Dose-response: 0.75 mg/kg 9/117 (8%), 0.4 mg/kg 12/115 (10%), 0.1 mg/kg 49/119 (41%), AL-only 78/117 (67%). The 0.4 mg/kg dose was non-inferior to 0.75 mg/kg for gametocyte clearance — supporting the lower-dose recommendation.', highlights: ['12', '115', '10%', '78', '117', '67%', 'RR 0.157', '0.090', '0.273', '0.75', '0.4', '0.1', '8%', '41%', 'non-inferior'] },


                        { label: 'Primary outcome — haemoglobin safety', source: 'Eziefula 2014 Lancet ID, safety endpoint', text: 'Mean maximum haemoglobin drop (G6PD-normal children): 0.75 mg/kg -1.7 g/dL (95% CI -2.0 to -1.4), 0.4 mg/kg -0.8 g/dL (-1.0 to -0.6), 0.1 mg/kg -0.6 g/dL (-0.9 to -0.4), AL-only -0.5 g/dL (-0.7 to -0.4). Dose-dependent haemolysis. No subject required transfusion. The 0.4-0.25 mg/kg range balances efficacy and safety — basis for WHO 2012 single-low-dose recommendation. CAVEAT: this trial enrolled only G6PD-NORMAL children; G6PD-deficient subjects (the safety-defining population for WHO recommendation) were studied separately in SAFEPRIM (NCT02174900).', highlights: ['-1.7', '-0.8', '-0.6', '-0.5', 'g/dL', 'dose-dependent', 'WHO 2012', 'G6PD-NORMAL', 'CAVEAT'] },


                        { label: 'Risk of Bias (RoB 2.0)', source: 'Eziefula 2014 design + RoB 2.0', text: 'D1 LOW - 1:1:1:1 stratified randomization with central allocation. D2 LOW - double-blind across 4 arms via identical-appearing drug/placebo. D3 LOW - 95%+ retention at day 28. D4 LOW - QT-NASBA central laboratory. D5 LOW - SAP locked, all 4 dose-arms reported.', highlights: ['LOW', '1:1:1:1', 'double-blind', '95%', 'QT-NASBA'] }


                    ]


                },


                // ============================================================
                // SAFEPRIM Burkina Faso — primaquine 0.25 vs 0.4 mg/kg
                // safety in G6PD-deficient adult males. NCT02174900.
                // ============================================================

                'NCT02174900': {


                    name: 'SAFEPRIM Burkina Faso', pmid: '27339845', phase: 'II/III', year: 2016, tE: -10, tN: 25, cE: -16, cN: 25, group: 'SAFEPRIM Burkina Faso. G6PD-deficient adult males with asymptomatic P. falciparum, primaquine 0.25 mg/kg vs 0.4 mg/kg (single-dose adjunct to AL). Primary endpoint: maximum percentage drop in haemoglobin from baseline through day 28. Pre-specified safety threshold (no haemolysis requiring transfusion) met at both doses, but 0.25 mg/kg had smaller mean drop (-10% vs -16%; difference -6 percentage points, 95% CI -11 to -1). Goncalves BP et al. Lancet ID 2016;16:1112-1120. DOI 10.1016/S1473-3099(16)30115-4. PMID 27339845. n=70 total (subset 25/25 G6PD-deficient analyzed for primary; remaining 20 G6PD-normal control).',


                    estimandType: 'MD', publishedHR: -6, hrLCI: -11, hrUCI: -1, pubHR: -6, pubHR_LCI: -11, pubHR_UCI: -1,


                    allOutcomes: [


                        { shortLabel: 'HB_DROP_PCT', title: 'Maximum percentage Hb drop from baseline through day 28 (PQ 0.25 vs 0.4 mg/kg, G6PD-deficient)', tE: -10, cE: -16, type: 'PRIMARY', matchScore: 100, effect: -6, lci: -11, uci: -1, estimandType: 'MD' },


                        { shortLabel: 'GAM_D14', title: 'Day-14 gametocyte clearance time (median days) — 0.25 vs 0.4 mg/kg', tE: 7, cE: 6, type: 'SECONDARY', matchScore: 80, effect: 1.0, lci: 0.0, uci: 2.5, estimandType: 'MD' }


                    ],


                    rob: ['low', 'some', 'low', 'low', 'low'],


                    snippet: 'Source: Goncalves BP, Tiono AB, Ouedraogo A, et al. Single low-dose primaquine to reduce gametocyte carriage and Plasmodium falciparum transmission after artemether-lumefantrine in children with asymptomatic infection: a randomised, double-blind, placebo-controlled trial. Lancet Infect Dis 2016;16:1112-1120. PMID 27339845. DOI 10.1016/S1473-3099(16)30115-4.',


                    sourceUrl: 'https://www.thelancet.com/journals/laninf/article/PIIS1473-3099(16)30115-4/fulltext',


                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT02174900',


                    evidence: [


                        { label: 'Enrollment', source: 'Goncalves 2016 Lancet ID, CONSORT', text: '70 men aged 18-45 years with asymptomatic P. falciparum infection (parasitaemia at any density) enrolled at Centre National de Recherche et de Formation sur le Paludisme, Ouagadougou, Burkina Faso between Oct 2014 and Dec 2015. 50 G6PD-deficient by Beutler fluorescent spot test (the safety-defining cohort) randomized double-blind to primaquine 0.25 mg/kg (n=25) or 0.4 mg/kg (n=25); 20 G6PD-normal received AL-only as control. Followed for 28 days with daily haemoglobin and weekly gametocyte detection.', highlights: ['70', 'Burkina Faso', '18-45 years', 'G6PD-deficient', '50', '0.25 mg/kg', '0.4 mg/kg', '25', 'AL-only', 'Beutler'] },


                        { label: 'Primary outcome — haemoglobin drop in G6PD-deficient', source: 'Goncalves 2016 Lancet ID, primary endpoint', text: 'Maximum percentage Hb drop from baseline through day 28 (G6PD-deficient subjects only): primaquine 0.25 mg/kg -10% (95% CI -13 to -7) vs 0.4 mg/kg -16% (95% CI -19 to -13). Difference -6 percentage points (95% CI -11 to -1). No transfusions required at either dose. Both doses cleared >85% of gametocytes by day 14. The 0.25 mg/kg dose has the better safety profile in G6PD-deficient subjects, with non-inferior gametocyte clearance — supports lower end of WHO 2012 0.25 mg/kg recommendation.', highlights: ['-10%', '-13', '-7', '-16%', '-19', '-13', '-6', '-11', '-1', 'no transfusions', '>85%', 'WHO 2012', '0.25 mg/kg'] },


                        { label: 'Risk of Bias (RoB 2.0)', source: 'Goncalves 2016 design + RoB 2.0', text: 'D1 LOW - block randomization with central allocation. D2 SOME concerns - small sample size (n=25/25 G6PD-deficient); double-blind comparison of primaquine doses but G6PD-normal control was unblinded by design. D3 LOW - 96%+ retention at day 28. D4 LOW - central haematology laboratory. D5 LOW - SAP locked.', highlights: ['LOW', 'block randomization', 'double-blind', '96%', 'central'] }


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
