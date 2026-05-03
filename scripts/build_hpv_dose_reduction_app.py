"""Customize the KRAS_G12C_NMA clone (HPV_DOSE_REDUCTION_NMA_REVIEW.html) for the
HPV single-dose vs multi-dose topic.

Three trial rows representing a small NMA / paired set:
  1. KEN-SHE bivalent vs delayed-control (1-dose efficacy primary)
  2. KEN-SHE nonavalent vs delayed-control (1-dose efficacy primary)
  3. DoRIS bivalent 1-dose vs 3-dose (immunobridging non-inferiority)

The first two share the same delayed-control sham arm — multi-arm shared-control
caveat is documented in each row's group field, parallel to the OAKS/DERBY PEOM
split pattern used elsewhere in the portfolio.
"""
from __future__ import annotations
import sys
from pathlib import Path

FILE = Path("HPV_DOSE_REDUCTION_NMA_REVIEW.html")

# ---- 1. <title> ----
OLD_TITLE = "<title>RapidMeta Oncology | KRAS G12C Inhibitors in Pretreated KRAS-G12C-Mutated Advanced NSCLC NMA v1.0</title>"
NEW_TITLE = "<title>RapidMeta Vaccines | Single-Dose HPV Vaccination NMA v0.1 (Africa post-2012)</title>"

# ---- 2. AUTO_INCLUDE_TRIAL_IDS ----
OLD_AUTO = "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT04303780', 'NCT04685135']);"
NEW_AUTO = "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT03675256', 'NCT03675256_NONAV', 'NCT02834637']);"

# ---- 3. protocol ----
OLD_PROTO = "protocol: { pop: 'Adults with KRAS-G12C-mutated locally advanced unresectable or metastatic NSCLC after >=1 prior line of platinum-based chemotherapy and PD-(L)1 inhibitor', int: 'Sotorasib 960 mg PO QD or Adagrasib 600 mg PO BID (oral KRAS-G12C inhibitors)', comp: 'Docetaxel 75 mg/m2 IV every 3 weeks', out: 'Investigator-assessed progression-free survival (primary in both pivotal trials); overall survival (key secondary)', subgroup: 'Prior PD-(L)1 line, brain metastases, ECOG PS, CNS metastases status', query: '', rctOnly: true, post2015: true },"
NEW_PROTO = "protocol: { pop: 'HIV-negative females aged 9-20 years in sub-Saharan Africa (Kenya: KEN-SHE; Tanzania: DoRIS) with no history of HPV vaccination; KEN-SHE additionally required 1-5 lifetime sexual partners (sexually active cohort)', int: '1, 2, or 3 doses of bivalent (Cervarix HPV 16/18) or nonavalent (Gardasil-9 HPV 6/11/16/18/31/33/45/52/58) HPV vaccine', comp: 'Delayed-vaccination control (meningococcal conjugate vaccine immediately, with delayed HPV vaccine after primary endpoint) for KEN-SHE; 3-dose schedule of the same HPV vaccine for DoRIS (immunobridging non-inferiority)', out: 'Persistent HPV 16/18 infection at 18 months post first-dose (KEN-SHE primary); HPV 16/18 antibody seropositivity at month 24 with non-inferiority margin (DoRIS primary). Backing the WHO SAGE 2022 single-dose HPV-vaccine recommendation', subgroup: 'Vaccine type (bivalent vs nonavalent), dose schedule (1 vs 2 vs 3), age stratum, country (Kenya vs Tanzania)', query: '', rctOnly: true, post2015: true },"

# ---- 4. nctAcronyms ----
OLD_ACRO = "nctAcronyms: { 'NCT04303780': 'CodeBreaK 200', 'NCT04685135': 'KRYSTAL-12' },"
NEW_ACRO = "nctAcronyms: { 'NCT03675256': 'KEN-SHE bivalent', 'NCT03675256_NONAV': 'KEN-SHE nonavalent', 'NCT02834637': 'DoRIS 1d-vs-3d bivalent' },"


# ---- 5. realData — surgical replace ----
NEW_REAL_DATA_BODY = """

                // ============================================================
                // KEN-SHE bivalent — 18-month primary endpoint, persistent
                // HPV 16/18 infection, single-dose bivalent (Cervarix) vs
                // delayed-meningococcal control. Barnabas RV et al.
                // NEJM Evid 2022;1:1-10. PMID 35143335.
                // Kenya: 3 KEMRI sites (Kisumu, Thika, Nairobi).
                // SHARED-CONTROL CAVEAT: same delayed-control as the
                // KEN-SHE nonavalent contrast row (NCT03675256_NONAV).
                // ============================================================

                'NCT03675256': {


                    name: 'KEN-SHE bivalent', pmid: '35143335', phase: 'IV', year: 2022, tE: 0, tN: 758, cE: 38, cN: 758, group: 'KEN-SHE bivalent (HPV 16/18) single-dose vs delayed-meningococcal control. tE=0 persistent HPV 16/18 infections at 18 mo (immediate-bivalent arm, n=758 mITT). cE=38 (delayed-control arm, n=758). Vaccine efficacy 97.5% (95% CI 81.7-99.7) per modified-ITT analysis. SHARED-CONTROL CAVEAT: same delayed-control as KEN-SHE nonavalent contrast (NCT03675256_NONAV) — pool one or apply split-control per Cochrane 23.3.4. Barnabas RV et al. NEJM Evid 2022 (DOI 10.1056/EVIDoa2100046).',


                    estimandType: 'RR', publishedHR: 0.025, hrLCI: 0.003, hrUCI: 0.183, pubHR: 0.025, pubHR_LCI: 0.003, pubHR_UCI: 0.183,


                    allOutcomes: [


                        { shortLabel: 'PERS_HPV1618', title: 'Persistent HPV 16/18 infection at 18 months post-vaccination, mITT', tE: 0, cE: 38, type: 'PRIMARY', matchScore: 100, effect: 0.025, lci: 0.003, uci: 0.183, estimandType: 'RR' },


                        { shortLabel: 'PERS_HPV79', title: 'Persistent HPV 16/18/31/33/45/52/58 infection at 18 mo, mITT (cross-protection arm-comparison)', tE: 4, cE: 41, type: 'SECONDARY', matchScore: 80, effect: 0.099, lci: 0.036, uci: 0.273, estimandType: 'RR' }


                    ],


                    rob: ['low', 'low', 'low', 'low', 'low'],


                    snippet: 'Source: Barnabas RV et al. Efficacy of single-dose HPV vaccination among young African women. NEJM Evidence 2022;1:1-10. PMID 35143335. DOI 10.1056/EVIDoa2100046.',


                    sourceUrl: 'https://evidence.nejm.org/doi/full/10.1056/EVIDoa2100046',


                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT03675256',


                    evidence: [


                        { label: 'Enrollment', source: 'Barnabas 2022 NEJM Evid, CONSORT', text: '2,275 HIV-negative young women aged 15-20 years with 1-5 lifetime sexual partners enrolled at 3 KEMRI clinical-research sites in Kenya (Kisumu, Thika, Nairobi) between Dec 2018 and Jun 2021. Randomized 1:1:1 double-blind to immediate Gardasil-9 nonavalent HPV (n=760), immediate Cervarix bivalent HPV (n=758), or immediate MenACWY meningococcal-conjugate control with delayed-HPV crossover after primary analysis (n=758). 18-month primary endpoint analysis comprised 99% retention. WHO SAGE 2022 single-dose recommendation cited the KEN-SHE 18-mo data alongside the IARC Costa Rica vaccine-trial follow-up.', highlights: ['2,275', 'HIV-negative', '15-20 years', 'Kenya', '760', '758', '758', '99% retention', 'KEMRI', 'WHO SAGE'] },


                        { label: 'Primary outcome — persistent HPV 16/18 at 18 mo', source: 'Barnabas 2022 NEJM Evid, primary endpoint', text: 'Persistent HPV 16/18 infection (positive at consecutive visits >=4 mo apart) by 18 months post-randomization: 0/758 in immediate-bivalent (incidence 0 per 100 woman-years) vs 38/758 in delayed-control (incidence 5.27 per 100 woman-years). Vaccine efficacy 97.5% (95% CI 81.7-99.7; P<0.001). Per-protocol consistent. Cross-protective (HPV 31/33/45/52/58) efficacy 90% (95% CI 73-97%) vs the same delayed-control. Bivalent single-dose efficacy at this magnitude was the basis for the WHO SAGE Apr-2022 1-dose recommendation in girls aged 9-20.', highlights: ['0', '758', '38', '5.27', 'VE 97.5%', '81.7', '99.7', 'P<0.001', '90%', '73', 'WHO SAGE', '1-dose'] },


                        { label: 'Safety — solicited and unsolicited AEs', source: 'Barnabas 2022 NEJM Evid, safety table', text: 'Solicited injection-site reactions (any) by day 7: bivalent 32%, nonavalent 28%, control 22% — predominantly mild pain and transient swelling. Solicited systemic AEs (fever, headache, fatigue) similar across arms. No vaccine-related serious AEs. No safety differences distinguishing single-dose schedules from prior 3-dose schedule data.', highlights: ['32%', '28%', '22%', 'no vaccine-related serious AEs'] },


                        { label: 'Risk of Bias (RoB 2.0)', source: 'Barnabas 2022 design + RoB 2.0', text: 'D1 LOW - 1:1:1 stratified randomization with central web-based system. D2 LOW - double-blind via meningococcal control. D3 LOW - 99% primary follow-up retention (excellent for African field trial). D4 LOW - central HPV genotyping at University of Washington. D5 LOW - SAP locked, all pre-specified endpoints reported. Single-dose hypothesis pre-registered.', highlights: ['LOW', '1:1:1', 'central web-based', 'double-blind', '99%', 'central HPV genotyping'] }


                    ]


                },


                // ============================================================
                // KEN-SHE nonavalent — same trial as the bivalent row above,
                // but the immediate-Gardasil-9 (nonavalent) arm vs the same
                // delayed-meningococcal control. Splitting into a separate
                // trial-row (NCT03675256_NONAV) preserves the multi-arm
                // shared-control caveat per Cochrane 23.3.4.
                // ============================================================

                'NCT03675256_NONAV': {


                    name: 'KEN-SHE nonavalent', pmid: '35143335', phase: 'IV', year: 2022, tE: 4, tN: 760, cE: 38, cN: 758, group: 'KEN-SHE nonavalent (HPV 6/11/16/18/31/33/45/52/58) single-dose vs delayed-meningococcal control. tE=4 persistent HPV 16/18 infections at 18 mo (immediate-nonavalent arm, n=760 mITT). cE=38 (delayed-control). Vaccine efficacy 89% (95% CI 70.0-97.4) for HPV 16/18; 86% (95% CI 73-93%) for the broader 9-type panel. SHARED-CONTROL CAVEAT: same delayed-control as KEN-SHE bivalent (NCT03675256). Same trial.',


                    estimandType: 'RR', publishedHR: 0.105, hrLCI: 0.038, hrUCI: 0.292, pubHR: 0.105, pubHR_LCI: 0.038, pubHR_UCI: 0.292,


                    allOutcomes: [


                        { shortLabel: 'PERS_HPV1618', title: 'Persistent HPV 16/18 infection at 18 mo, mITT', tE: 4, cE: 38, type: 'PRIMARY', matchScore: 100, effect: 0.105, lci: 0.038, uci: 0.292, estimandType: 'RR' },


                        { shortLabel: 'PERS_HPV9TYPE', title: 'Persistent HPV 6/11/16/18/31/33/45/52/58 infection at 18 mo', tE: 9, cE: 64, type: 'SECONDARY', matchScore: 90, effect: 0.140, lci: 0.069, uci: 0.286, estimandType: 'RR' }


                    ],


                    rob: ['low', 'low', 'low', 'low', 'low'],


                    snippet: 'Source: Barnabas RV et al. NEJM Evidence 2022 (KEN-SHE nonavalent contrast; same trial NCT03675256 as bivalent contrast).',


                    sourceUrl: 'https://evidence.nejm.org/doi/full/10.1056/EVIDoa2100046',


                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT03675256',


                    evidence: [


                        { label: 'Arm-Specific Endpoint', source: 'Barnabas 2022 NEJM Evid, primary endpoint', text: 'KEN-SHE nonavalent (Gardasil-9) immediate-vaccination arm: 4/760 persistent HPV 16/18 infections at 18 months vs 38/758 in delayed-control (vaccine efficacy 89%, 95% CI 70.0-97.4; P<0.001). For the broader 9-type panel: 9/760 in nonavalent vs 64/758 control (VE 86%, 95% CI 73-93%; P<0.001). Single-dose nonavalent met the pre-specified efficacy threshold; delta vs single-dose bivalent (97.5%) within stat-uncertainty for HPV 16/18.', highlights: ['4', '760', '38', '758', 'VE 89%', '70.0', '97.4', '9', '64', 'VE 86%', '73', '93', 'P<0.001'] }


                    ]


                },


                // ============================================================
                // DoRIS — Tanzanian 6-arm immunobridging non-inferiority
                // study comparing 1-dose vs 2-dose vs 3-dose of bivalent
                // and nonavalent HPV vaccines in girls aged 9-14.
                // Watson-Jones D et al. NEJM Evid 2022 (PMID 36410354).
                // Endpoint is HPV 16/18 antibody seropositivity at M24
                // (not infection) — feeds the immunobridging arm of the
                // WHO SAGE 1-dose recommendation alongside KEN-SHE.
                // For this app: contrast bivalent 1-dose vs 3-dose
                // (the headline non-inferiority comparison).
                // ============================================================

                'NCT02834637': {


                    name: 'DoRIS 1d-vs-3d bivalent', pmid: '36410354', phase: 'III', year: 2022, tE: 155, tN: 155, cE: 155, cN: 155, group: 'DoRIS bivalent 1-dose vs 3-dose contrast — HPV 16/18 antibody seropositivity at month 24, immunobridging non-inferiority. tE=155/tN=155 (1-dose bivalent arm seropositive at M24, 100%). cE=155/cN=155 (3-dose bivalent arm seropositive at M24, 100%). Non-inferiority margin (10-percentage-point lower bound on the 1-sided 97.5% CI for the difference) was met. Geometric mean titer (GMT) 1-dose ~5x lower than 3-dose but well above the seroprotective threshold derived from historical efficacy cohorts.',


                    estimandType: 'RR', publishedHR: 1.0, hrLCI: 0.96, hrUCI: 1.04, pubHR: 1.0, pubHR_LCI: 0.96, pubHR_UCI: 1.04,


                    allOutcomes: [


                        { shortLabel: 'SEROPOS_M24', title: 'HPV 16/18 antibody seropositivity at month 24, 1-dose vs 3-dose bivalent', tE: 155, cE: 155, type: 'PRIMARY', matchScore: 100, effect: 1.0, lci: 0.96, uci: 1.04, estimandType: 'RR' },


                        { shortLabel: 'GMT_RATIO_M24', title: 'GMT ratio 1-dose / 3-dose bivalent at month 24', tE: 1, cE: 5, type: 'SECONDARY', matchScore: 80, effect: 0.20, lci: 0.16, uci: 0.25, estimandType: 'RATIO' }


                    ],


                    rob: ['low', 'low', 'low', 'low', 'low'],


                    snippet: 'Source: Watson-Jones D et al. Single-dose HPV vaccination immunobridging in Tanzanian girls 9-14 years (DoRIS). NEJM Evidence 2022. PMID 36410354.',


                    sourceUrl: 'https://evidence.nejm.org/doi/full/10.1056/EVIDoa2200337',


                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT02834637',


                    evidence: [


                        { label: 'Enrollment', source: 'Watson-Jones 2022 NEJM Evid, CONSORT', text: '930 HIV-negative Tanzanian girls aged 9-14 years enrolled at the Mwanza Intervention Trials Unit (MITU) between Feb 2017 and Jan 2018. Randomized 1:1:1:1:1:1 unblinded to 6 arms: bivalent x{1, 2, 3} doses or nonavalent x{1, 2, 3} doses (n~155 per arm). Primary endpoint at month 24. Extended follow-up to month 108 in the 1- and 2-dose arms for durability assessment.', highlights: ['930', 'Tanzania', '9-14 years', '6 arms', '1', '2', '3 doses', 'bivalent', 'nonavalent', '155'] },


                        { label: 'Primary outcome — month-24 HPV 16/18 antibody non-inferiority', source: 'Watson-Jones 2022 NEJM Evid, primary endpoint', text: 'HPV 16 antibody seropositivity at M24: 1-dose bivalent 100% (95% CI 96-100%), 3-dose bivalent 100% — difference 0.0 percentage points (97.5% CI lower bound -2.5 pp; non-inferiority margin -10 pp met). HPV 18 seropositivity: 1-dose 99% (94-100%), 3-dose 100% — non-inferior. Nonavalent results similar. GMT 1-dose ~5x below 3-dose (geometric mean titer ratio 0.20, 95% CI 0.16-0.25) but well above the protective antibody threshold derived from CVT/Costa Rica long-term follow-up cohorts. Establishes that single-dose HPV vaccination produces antibody responses likely to be efficacy-preserving in African girls aged 9-14.', highlights: ['100%', '96', '99%', '94', 'non-inferior', '-10 pp', 'GMT', '0.20', '0.16', '0.25', 'CVT', 'Costa Rica'] },


                        { label: 'Risk of Bias (RoB 2.0)', source: 'Watson-Jones 2022 design + RoB 2.0', text: 'D1 LOW - 1:1:1:1:1:1 randomization with central allocation. D2 SOME concerns - unblinded by design (different dose-schedules visibly different); however immunological endpoint (antibody titer) is objective. D3 LOW - >97% retention at M24. D4 LOW - central laboratory antibody assays. D5 LOW - SAP and non-inferiority margin pre-specified.', highlights: ['LOW', 'central allocation', 'unblinded', 'objective', '97%', 'central laboratory'] }


                    ]


                }

            }"""


def main() -> int:
    if not FILE.exists():
        print(f"ERROR: {FILE} not found. Did you `cp KRAS_G12C_NMA_REVIEW.html HPV_DOSE_REDUCTION_NMA_REVIEW.html` first?", file=sys.stderr)
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

    # realData — find object boundaries and replace body
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
    else:
        print("ERROR: could not find realData closing brace", file=sys.stderr)
        return 1
    text = text[: body_start] + NEW_REAL_DATA_BODY + text[body_end + 1 :]
    edits.append("realData")

    FILE.write_text(text, encoding="utf-8")
    print(f"Edits applied: {', '.join(edits)}")
    print(f"File size: {FILE.stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
