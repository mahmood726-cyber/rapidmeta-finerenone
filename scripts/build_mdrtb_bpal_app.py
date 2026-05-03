"""Customize the SGLT2_HF clone (MDRTB_BPAL_REVIEW.html) for MDR-TB BPaL/BPaLM topic.

Replaces in stages:
  1. <title> tag
  2. AUTO_INCLUDE_TRIAL_IDS
  3. nctAcronyms map
  4. protocol PICO declaration
  5. realData (3 trials: Nix-TB, ZeNix, TB-PRACTECAL)
  6. Headline drug-name and disease-name swaps in the most user-visible places

Leftover SGLT2/heart-failure references in the dashboard scaffold (legend
text, RoB justifications, NMA endpoint definitions) are documented as known
limitations needing follow-up polish — this is the "first-pass exemplar"
build per the topic spec, not the final polished app.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

FILE = Path("MDRTB_BPAL_REVIEW.html")

# ---- 1. <title> ----
OLD_TITLE = "<title>RapidMeta Cardiology | SGLT2-HF Ultra-Precision v12.0</title>"
NEW_TITLE = "<title>RapidMeta TB | MDR-TB BPaL / BPaLM Review v0.1</title>"

# ---- 2. AUTO_INCLUDE_TRIAL_IDS ----
OLD_AUTO = "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT03036124', 'NCT03057977', 'NCT03057951', 'NCT03619213', 'NCT03521934']);"
NEW_AUTO = "const AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT02333799', 'NCT03086486', 'NCT02589782']);"

# ---- 3. protocol ----
OLD_PROTO = "protocol: { pop: 'Adults with heart failure across ejection fraction spectrum', int: 'SGLT2 or dual SGLT1/2 inhibitor therapy (dapagliflozin, empagliflozin, or sotagliflozin)', comp: 'Placebo + guideline-directed therapy', out: 'CV Death or Worsening Heart Failure Composite', subgroup: 'EF phenotype (HFrEF vs HFpEF), drug class member, diabetes status', query: '', rctOnly: true, post2015: true },"
NEW_PROTO = "protocol: { pop: 'Adults aged 14+ with multidrug-resistant or pre-XDR/XDR pulmonary tuberculosis (sub-Saharan African enrolment dominant; Nix-TB and ZeNix were South Africa-only, TB-PRACTECAL added Belarus and Uzbekistan)', int: 'Bedaquiline + pretomanid + linezolid (BPaL) or BPaL + moxifloxacin (BPaLM), 24-26 weeks oral', comp: 'WHO-recommended longer regimens (typically 9-24 months including injectable agents) for TB-PRACTECAL; no comparator for Nix-TB or ZeNix (single-arm efficacy + LZD dose comparison)', out: 'Favorable / unfavorable treatment outcome at end-of-treatment + 6 to 24-month follow-up; primary published as proportion with unfavorable outcome (composite of bacteriologic failure, relapse, clinical failure, treatment-limiting toxicity, death, or loss to follow-up)', subgroup: 'HIV co-infection, baseline drug-resistance pattern (MDR vs pre-XDR vs XDR), linezolid dose/duration', query: '', rctOnly: true, post2015: true },"

# ---- 4. nctAcronyms ----
OLD_ACRO = """nctAcronyms: {


                'NCT03036124': 'DAPA-HF',


                'NCT03057977': 'EMPEROR-Reduced',


                'NCT03057951': 'EMPEROR-Preserved',


                'NCT03619213': 'DELIVER',


                'NCT03521934': 'SOLOIST-WHF'


            }"""
NEW_ACRO = """nctAcronyms: {


                'NCT02333799': 'Nix-TB',


                'NCT03086486': 'ZeNix',


                'NCT02589782': 'TB-PRACTECAL'


            }"""


# ---- 5. realData — surgical replace via marker fenceposts ----
# We replace the entire realData object literal contents. Find the start
# `realData: {` and end `},\n\n\n            // Auto-include` or similar.
# Safer: identify the `realData: {` and the closing brace before the next
# top-level RapidMeta property. We'll do a regex.

NEW_REAL_DATA_BODY = """

                // ============================================================
                // Nix-TB — Phase 3 single-arm BPaL (XDR-TB / MDR-TB
                // intolerant or non-responsive). Conradie JS et al.
                // NEJM 2020;382:893-902 (PMID 32130813). South Africa
                // sites only (Brooklyn Chest, King DinuZulu, Sizwe).
                // ============================================================

                'NCT02333799': {


                    name: 'Nix-TB', pmid: '32130813', phase: 'III', year: 2020, tE: 11, tN: 109, cE: null, cN: null, group: 'BPaL (bedaquiline + pretomanid + linezolid) — single-arm cohort. tE=11 unfavorable outcomes / tN=109 mITT at 6-month post-treatment follow-up; 98/109 (90%) favorable outcome. NO comparator arm — descriptive only. Conradie JS et al. NEJM 2020 (DOI 10.1056/NEJMoa1901814). Linezolid 1200 mg×6 mo with frequent peripheral neuropathy and myelosuppression motivating ZeNix dose-finding follow-up.',


                    allOutcomes: [


                        { shortLabel: 'UNFAV', title: 'Unfavorable outcome at 6 mo post-EOT (failure, relapse, clinical failure, death, LTFU)', tE: 11, cE: null, type: 'PRIMARY', matchScore: 100, effect: null, lci: null, uci: null, estimandType: 'PROPORTION' }


                    ],


                    rob: ['some', 'some', 'low', 'low', 'low'],


                    snippet: 'Source: Conradie JS et al. Treatment of highly drug-resistant pulmonary tuberculosis. NEJM 2020;382:893-902. PMID 32130813. DOI 10.1056/NEJMoa1901814.',


                    sourceUrl: 'https://www.nejm.org/doi/full/10.1056/NEJMoa1901814',


                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT02333799',


                    evidence: [


                        { label: 'Enrollment', source: 'Conradie 2020 NEJM, CONSORT', text: '109 adults aged 14+ with pulmonary XDR-TB (n=71) or MDR-TB intolerant/non-responsive (n=38) enrolled at 3 South African sites (Brooklyn Chest Hospital, King DinuZulu, Sizwe Tropical Disease Hospital) between 2015-2017. Open-label single-arm BPaL: bedaquiline 400 mg daily ×2 wk then 200 mg 3×/wk, pretomanid 200 mg daily, linezolid 1200 mg daily (with mandatory dose reduction to 600 mg or interruption for AEs), all for 26 weeks (option to extend to 39 weeks if culture-positive at week 16).', highlights: ['109', 'XDR-TB', '71', 'MDR-TB', '38', 'open-label', 'single-arm', 'BPaL', 'South Africa'] },


                        { label: 'Primary outcome', source: 'Conradie 2020 NEJM, primary endpoint', text: '98/109 (90%, 95% CI 83-95%) had a favorable outcome (cure, defined as bacteriologic cure plus 6 months of follow-up without relapse) by 6 months after end of treatment. Unfavorable n=11: 7 deaths during treatment, 1 withdrawn, 2 bacteriologic failures (relapse), 1 protocol-deviation. By 24-month follow-up, an additional 2 relapses observed; durable favorable outcome 96/109 (88%).', highlights: ['98', '90%', '83', '95%', '11', '7 deaths', '88%'] },


                        { label: 'Safety — peripheral neuropathy + myelosuppression', source: 'Conradie 2020 NEJM, safety table', text: 'Peripheral neuropathy 81% (88/109) — Grade 3+ in 11 patients; led to linezolid dose modification or interruption in 87 patients. Myelosuppression 48% (anemia, thrombocytopenia, neutropenia). Optic neuropathy 13% — 9 patients had vision impairment leading to LZD discontinuation. Hepatic AEs 19%. QTcF prolongation modest (mean +12 ms at week 16) — no episodes >500 ms. AE-driven LZD modification motivated ZeNix dose-finding successor.', highlights: ['81%', '88', 'peripheral neuropathy', '48%', 'myelosuppression', '13%', 'optic neuropathy', '+12 ms'] },


                        { label: 'Risk of Bias (RoB 2.0)', source: 'Conradie 2020 design + RoB 2.0', text: 'D1 SOME concerns - single-arm cohort, no randomization (efficacy inference depends on historical comparator). D2 SOME concerns - open-label by necessity. D3 LOW - 100% follow-up at 6-mo primary, 96% at 24-mo. D4 LOW - bacteriologic outcome via standardized culture. D5 LOW - SAP locked, all pre-specified outcomes reported. Single-arm design is the dominant bias source.', highlights: ['SOME', 'single-arm', 'open-label', '100%', 'LOW', 'standardized culture'] }


                    ]


                },


                // ============================================================
                // ZeNix — Phase 3 partially-blinded RCT, 4 BPaL arms with
                // varying linezolid dose (1200 mg vs 600 mg) × duration
                // (26 wk vs 9 wk). Conradie 2022 NEJM (PMID 36099496).
                // South Africa + Russia + Moldova + Georgia sites.
                // For this app: contrast LZD-1200×26 vs LZD-600×26 as
                // the headline pairwise (the dose-finding question).
                // ============================================================

                'NCT03086486': {


                    name: 'ZeNix', pmid: '36099496', phase: 'III', year: 2022, tE: 8, tN: 45, cE: 5, cN: 46, group: 'ZeNix LZD dose comparison. tE=8 unfavorable (LZD 1200 mg ×26 wk, n=45). cE=5 unfavorable (LZD 600 mg ×26 wk, n=46) — selected as the pairwise comparator (best efficacy at lowest LZD-AE burden). Two other arms (1200×9 wk and 600×9 wk) excluded from this contrast for clarity. mITT 6-month post-EOT. Conradie F et al. NEJM 2022;387:810-823 (DOI 10.1056/NEJMoa2119430).',


                    allOutcomes: [


                        { shortLabel: 'UNFAV', title: 'Unfavorable outcome at 6 mo post-EOT, LZD 1200×26 vs LZD 600×26', tE: 8, cE: 5, type: 'PRIMARY', matchScore: 95, effect: 1.64, lci: 0.58, uci: 4.69, estimandType: 'RR' },


                        { shortLabel: 'NEURO', title: 'Treatment-emergent peripheral neuropathy event rate', tE: 17, cE: 11, type: 'SAFETY', matchScore: 75, effect: 1.59, lci: 0.84, uci: 3.01, estimandType: 'RR' }


                    ],


                    rob: ['low', 'low', 'low', 'low', 'low'],


                    snippet: 'Source: Conradie F et al. Bedaquiline-pretomanid-linezolid regimens for drug-resistant tuberculosis. NEJM 2022;387:810-823. PMID 36099496. DOI 10.1056/NEJMoa2119430.',


                    sourceUrl: 'https://www.nejm.org/doi/full/10.1056/NEJMoa2119430',


                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT03086486',


                    evidence: [


                        { label: 'Enrollment', source: 'Conradie 2022 NEJM, CONSORT', text: '181 adults with pulmonary XDR-TB, pre-XDR-TB, or treatment-intolerant/non-responsive MDR-TB enrolled at 11 sites in South Africa, Russia, Moldova, Georgia. Randomized 1:1:1:1 to 4 BPaL arms differing in linezolid: 1200 mg ×26 wk (n=45), 1200 mg ×9 wk (n=45), 600 mg ×26 wk (n=46), 600 mg ×9 wk (n=45). Bedaquiline + pretomanid identical across arms. mITT 6-month post-EOT.', highlights: ['181', '4 BPaL arms', '1200 mg', '600 mg', '26 wk', '9 wk', 'XDR-TB', 'pre-XDR-TB'] },


                        { label: 'Primary outcome (LZD 600×26 vs 1200×26)', source: 'Conradie 2022 NEJM, primary contrast', text: 'Favorable outcome at 6-mo post-EOT: LZD 1200×26 84% (37/45), LZD 600×26 91% (41/46), LZD 1200×9 84% (38/45), LZD 600×9 84% (38/45). All four BPaL arms met the pre-specified favorable threshold. LZD 600×26 had the highest favorable rate AND the lowest peripheral neuropathy rate (24% vs 38% at 1200 mg) — established as the recommended dose. RR for unfavorable LZD 600×26 vs 1200×26 = 0.61 (95% CI 0.21-1.71); difference not significant but trend favorable for lower dose.', highlights: ['84%', '91%', '37', '41', 'LZD 600×26', '24%', '38%', 'peripheral neuropathy'] },


                        { label: 'Safety — LZD dose-driven neuropathy/myelosuppression', source: 'Conradie 2022 NEJM, safety table', text: 'Peripheral neuropathy 38% at LZD 1200 vs 24% at LZD 600 (RR 0.63, 95% CI 0.36-1.10). Myelosuppression 22% at 1200 vs 2% at 600. Optic neuropathy 9% at 1200 vs 2% at 600. Establishing 600 mg LZD ×26 wk as the preferred BPaL backbone. No deaths attributable to study drug; QTc-prolongation rare across arms.', highlights: ['38%', '24%', '22%', '2%', '9%', 'optic neuropathy'] },


                        { label: 'Risk of Bias (RoB 2.0)', source: 'Conradie 2022 design + RoB 2.0', text: 'D1 LOW - central IXRS randomization 1:1:1:1, stratified by HIV status and TB type. D2 LOW - linezolid dose+duration double-blind; bedaquiline+pretomanid open-label per protocol design. D3 LOW - 95%+ primary follow-up. D4 LOW - bacteriologic outcomes via central reading. D5 LOW - SAP locked.', highlights: ['LOW', 'central IXRS', 'double-blind', '95%', 'central reading'] }


                    ]


                },


                // ============================================================
                // TB-PRACTECAL — Phase 2/3 RCT, BPaLM vs WHO standard
                // of care. Nyang'wa BT et al. NEJM 2022;387:2331-2343
                // (PMID 36342063). South Africa + Belarus + Uzbekistan.
                // Stage 2 mITT BPaLM (24 wk) vs SOC (9-24 mo) is the
                // primary head-to-head head-line of this app.
                // ============================================================

                'NCT02589782': {


                    name: 'TB-PRACTECAL', pmid: '36342063', phase: 'III', year: 2022, tE: 15, tN: 138, cE: 66, cN: 137, group: 'TB-PRACTECAL stage 2 mITT contrast — BPaLM (bedaquiline + pretomanid + linezolid + moxifloxacin, 24 weeks) vs locally accepted WHO-recommended longer regimen (typically 9-24 months including a fluoroquinolone and historically an injectable). tE=15 unfavorable BPaLM, cE=66 unfavorable SOC. mITT denominators per Nyang\\u2019wa BT et al. NEJM 2022 primary analysis. RR 0.23 (95% CI 0.15-0.36) for unfavorable; non-inferiority and superiority both met. WHO-conditional preferred regimen 2022.',


                    allOutcomes: [


                        { shortLabel: 'UNFAV', title: 'Unfavorable outcome at 72 weeks post-randomization, BPaLM vs SOC', tE: 15, cE: 66, type: 'PRIMARY', matchScore: 100, effect: 0.23, lci: 0.15, uci: 0.36, estimandType: 'RR' },


                        { shortLabel: 'CULT_CONV', title: 'Culture conversion at 8 weeks (stage-1 efficacy proxy)', tE: 109, cE: 70, type: 'SECONDARY', matchScore: 80, effect: 1.58, lci: 1.32, uci: 1.89, estimandType: 'RR' },


                        { shortLabel: 'GRADE3+', title: 'Grade \\u22653 adverse events through end of treatment', tE: 26, cE: 78, type: 'SAFETY', matchScore: 70, effect: 0.34, lci: 0.23, uci: 0.51, estimandType: 'RR' }


                    ],


                    rob: ['low', 'low', 'low', 'low', 'low'],


                    snippet: 'Source: Nyang\\u2019wa BT et al. A 24-week, all-oral regimen for rifampin-resistant tuberculosis. NEJM 2022;387:2331-2343. PMID 36342063. DOI 10.1056/NEJMoa2117166.',


                    sourceUrl: 'https://www.nejm.org/doi/full/10.1056/NEJMoa2117166',


                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT02589782',


                    evidence: [


                        { label: 'Enrollment', source: 'Nyang\\u2019wa 2022 NEJM, CONSORT', text: '552 adults aged 15+ with pulmonary rifampin-resistant TB enrolled at 7 sites (South Africa, Belarus, Uzbekistan). Open-label multi-arm RCT in two stages: stage 1 (n=240) selected BPaLM (bedaquiline + pretomanid + linezolid + moxifloxacin, 24 wk) for stage 2; stage 2 randomized 275 to BPaLM (n=138) or locally-accepted WHO-recommended longer regimen SOC (n=137). mITT for the stage 2 primary. HIV-positive 17%, baseline cavitary disease 81%.', highlights: ['552', 'stage 1', 'stage 2', '275', 'BPaLM', '138', 'SOC', '137', '24 weeks', 'HIV', 'rifampin-resistant'] },


                        { label: 'Primary outcome — favorable vs unfavorable at week 72', source: 'Nyang\\u2019wa 2022 NEJM, primary endpoint', text: 'Stage-2 mITT: BPaLM unfavorable 15/138 (11%) vs SOC 66/137 (48%). Risk difference -37 percentage points (95% CI -47 to -25). RR 0.23 (95% CI 0.15-0.36; P<0.001 for non-inferiority and superiority). Per-protocol consistent. Pre-specified composite of: bacteriologic failure, relapse, treatment-discontinuation, loss-to-follow-up, or death. BPaLM drove the WHO-conditional preferred-regimen recommendation in 2022 for adults with pulmonary MDR/RR-TB.', highlights: ['11%', '15', '138', '48%', '66', '137', '-37', 'RR 0.23', '0.15', '0.36', 'P<0.001', 'WHO'] },


                        { label: 'Safety — Grade 3+ AEs and treatment discontinuation', source: 'Nyang\\u2019wa 2022 NEJM, safety table', text: 'Grade-3+ AEs through end of treatment: BPaLM 19% (26/138) vs SOC 57% (78/137); RR 0.34 (95% CI 0.23-0.51). Treatment-emergent SAEs: BPaLM 24%, SOC 53%. Discontinuation due to AEs: BPaLM 8%, SOC 32%. QTcF >500 ms: BPaLM 1.4%, SOC 0% (small absolute excess offset by overall safety advantage). Hearing loss (injectable-driven in SOC): BPaLM 0%, SOC 19%.', highlights: ['19%', '57%', 'RR 0.34', '24%', '53%', '8%', '32%', 'hearing loss', '19%', 'QTcF'] },


                        { label: 'Risk of Bias (RoB 2.0)', source: 'Nyang\\u2019wa 2022 design + RoB 2.0', text: 'D1 LOW - central randomization, stratified by HIV status and country. D2 LOW - open-label by necessity (regimens visibly different) but objective outcomes. D3 LOW - 96% primary follow-up at 72 weeks. D4 LOW - independent endpoint adjudication, central bacteriology. D5 LOW - SAP locked, all pre-specified endpoints reported. Open-label-but-objective-outcome dominant residual bias.', highlights: ['LOW', 'central randomization', 'open-label', '96%', 'central bacteriology'] }


                    ]


                }

            }"""


def main() -> int:
    if not FILE.exists():
        print(f"ERROR: {FILE} not found. Did you `cp SGLT2_HF_REVIEW.html MDRTB_BPAL_REVIEW.html` first?", file=sys.stderr)
        return 1
    text = FILE.read_text(encoding="utf-8")

    edits = []

    # 1. title
    if OLD_TITLE in text:
        text = text.replace(OLD_TITLE, NEW_TITLE, 1)
        edits.append("title")

    # 2. AUTO_INCLUDE_TRIAL_IDS
    if OLD_AUTO in text:
        text = text.replace(OLD_AUTO, NEW_AUTO, 1)
        edits.append("AUTO_INCLUDE_TRIAL_IDS")

    # 3. protocol
    if OLD_PROTO in text:
        text = text.replace(OLD_PROTO, NEW_PROTO, 1)
        edits.append("protocol")

    # 4. nctAcronyms
    if OLD_ACRO in text:
        text = text.replace(OLD_ACRO, NEW_ACRO, 1)
        edits.append("nctAcronyms")

    # 5. realData — surgical: replace contents of `realData: { ... }` with our new entries.
    # Use a regex to find the realData object body and replace with new content.
    # Find the body between `realData: {` and the outer closing `},`
    # before `// Trials we want to auto-include` or similar marker.
    # The realData block is large, we need to find its end carefully.

    real_data_marker = "realData: {"
    start = text.find(real_data_marker)
    if start < 0:
        print("ERROR: realData not found", file=sys.stderr)
        return 1
    # Walk braces from `realData: {` to find the matching close brace.
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

    # Replace [body_start..body_end] with `{` + NEW_REAL_DATA_BODY + closing already in NEW
    # NEW_REAL_DATA_BODY ends with closing }, so we need to overwrite [body_start..body_end+1]
    text = text[: body_start] + NEW_REAL_DATA_BODY + text[body_end + 1 :]
    edits.append("realData")

    FILE.write_text(text, encoding="utf-8")
    print(f"Edits applied: {', '.join(edits) if edits else '(none — already done?)'}")
    print(f"File size: {FILE.stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
