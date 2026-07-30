#!/usr/bin/env python
"""Correct endpoint classification, denominators, missing harms and template
contamination in RIVAROXABAN_VASC_REVIEW.html.

Every replacement is fail-closed: the anchor must occur exactly `count` times or
the script aborts without writing. Run from the repo root.

Source of truth for each numeric change is recorded in PATCH_PROVENANCE below and
mirrored into the app's own provenance ledger.
"""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TARGET = Path("RIVAROXABAN_VASC_REVIEW.html")

PATCH_PROVENANCE = {
    "COMPASS": "NEJM 2017;377:1319-1330 (PMID 28844192) + CT.gov NCT01776424 results",
    "VOYAGER-PAD": "NEJM 2020;382:1994-2004 (PMID 32222135) + CT.gov NCT02504216 results",
    "COMMANDER HF": "NEJM 2018;379:1332-1342 (PMID 30146935) + CT.gov NCT01877915 results"
                    " + BMJ Open 2023;13:e068865 (PMID 37567750) post-hoc",
    "ATLAS ACS 2": "NEJM 2012;366:9-19 (PMID 22077192) + CT.gov NCT00809965 results",
}

PATCHES = []


def patch(name, old, new, count=1):
    PATCHES.append((name, old, new, count))


# ---------------------------------------------------------------------------
# 1. COMPASS - the only exactly-matched 3-point MACE. Counts ARE reported.
#    Add major bleeding (the essential counterbalance).
# ---------------------------------------------------------------------------
patch(
    "COMPASS outcomes",
    'allOutcomes:[{shortLabel:"MACE",title:"CV death, stroke, or MI",tE:379,cE:496,'
    'type:"PRIMARY",pubHR:.76,pubHR_LCI:.66,pubHR_UCI:.86},'
    '{shortLabel:"ACM",title:"All-cause mortality",tE:313,cE:378,type:"SECONDARY",'
    'pubHR:.82,pubHR_LCI:.71,pubHR_UCI:.96},'
    '{shortLabel:"Stroke",title:"Stroke",tE:83,cE:142,type:"SECONDARY",'
    'pubHR:.58,pubHR_LCI:.44,pubHR_UCI:.76}]',

    'allOutcomes:[{shortLabel:"PRIMARY_COMPOSITE",title:"CV death, stroke, or MI (3-point MACE)",'
    'endpointComponents:3,endpointExactMace:!0,countsReported:!0,'
    'endpointNote:"Registered primary composite = CV death + stroke + MI. This is the ONLY trial '
    'in this set whose primary endpoint is an exact 3-point MACE. Counts are explicitly reported '
    'in the NEJM primary paper and in the CT.gov results record - they are NOT derived or '
    'back-calculated.",'
    'tE:379,cE:496,type:"PRIMARY",pubHR:.76,pubHR_LCI:.66,pubHR_UCI:.86},'
    '{shortLabel:"ACM",title:"All-cause mortality",countsReported:!0,tE:313,cE:378,'
    'type:"SECONDARY",pubHR:.82,pubHR_LCI:.71,pubHR_UCI:.96},'
    '{shortLabel:"Stroke",title:"Stroke (any) - standalone secondary",countsReported:!0,'
    'endpointNote:"Reported as a standalone secondary outcome in COMPASS. VOYAGER-PAD and ATLAS '
    'ACS 2 report stroke only as a component of their primary composite (component counts not '
    'extracted here); COMMANDER HF reports ischaemic stroke as a post-hoc exploratory analysis.",'
    'tE:83,cE:142,type:"SECONDARY",pubHR:.58,pubHR_LCI:.44,pubHR_UCI:.76},'
    '{shortLabel:"MajorBleed",title:"Major bleeding (modified ISTH)",countsReported:!0,'
    'harmOutcome:!0,'
    'endpointNote:"Principal safety outcome. 288 (3.1%) vs 170 (1.9%); NEJM 2017 abstract and '
    'CT.gov results. Direction of benefit is INVERTED for this outcome - HR>1 favours the '
    'comparator.",'
    'tE:288,cE:170,type:"SAFETY",pubHR:1.7,pubHR_LCI:1.4,pubHR_UCI:2.05}]',
)

# ---------------------------------------------------------------------------
# 2. VOYAGER-PAD - FIVE-component limb/CV composite, not 3-point MACE.
#    All-cause mortality in the app (240/259, HR 0.93) does not match the
#    registry-reported ACM (321/297, HR 1.08) and is directionally inverted.
# ---------------------------------------------------------------------------
patch(
    "VOYAGER outcomes",
    'allOutcomes:[{shortLabel:"MACE",title:"MACE, ALI, or major amputation",tE:508,cE:584,'
    'type:"PRIMARY",pubHR:.85,pubHR_LCI:.76,pubHR_UCI:.96},'
    '{shortLabel:"ACM",title:"All-cause mortality",tE:240,cE:259,type:"SECONDARY",'
    'pubHR:.93,pubHR_LCI:.78,pubHR_UCI:1.1}]',

    'allOutcomes:[{shortLabel:"PRIMARY_COMPOSITE",'
    'title:"ALI, major amputation, MI, ischaemic stroke, or CV death (5-component limb/CV composite)",'
    'endpointComponents:5,endpointExactMace:!1,countsReported:!0,'
    'endpointNote:"NOT a 3-point MACE. The registered primary endpoint adds acute limb ischaemia '
    'and major amputation of vascular aetiology to MI/ischaemic stroke/CV death. Roughly a third '
    'of primary events are limb events, so this estimate is NOT interchangeable with a '
    'CV-death/MI/stroke estimate. Published percentages (17.3% vs 19.9%) are 3-year Kaplan-Meier '
    'estimates, not crude proportions.",'
    'tE:508,cE:584,type:"PRIMARY",pubHR:.85,pubHR_LCI:.76,pubHR_UCI:.96},'
    '{shortLabel:"ACM",title:"All-cause mortality",countsReported:!0,'
    'endpointNote:"CORRECTED 2026-07-30. The app previously held 240 vs 259 with HR 0.93 '
    '(0.78-1.10), i.e. a mortality BENEFIT. The registry-reported all-cause mortality '
    '(NCT02504216 results, efficacy cut-off 08-Sep-2019) is 321/3286 vs 297/3278, HR 1.08 '
    '(0.92-1.27) - deaths were numerically HIGHER on rivaroxaban. The prior values were '
    'unsourced and directionally inverted.",'
    'tE:321,cE:297,type:"SECONDARY",pubHR:1.08,pubHR_LCI:.92,pubHR_UCI:1.27},'
    '{shortLabel:"MajorBleed",title:"Major bleeding (ISTH) - safety population",'
    'countsReported:!0,harmOutcome:!0,nT:3256,nC:3248,'
    'endpointNote:"ISTH major bleeding 140/3256 vs 100/3248, HR 1.42 (1.10-1.84). Safety '
    'population differs from the ITT efficacy population (3286/3278). TIMI major bleeding, the '
    'principal safety outcome, was 62 vs 44, HR 1.43 (0.97-2.10). Direction of benefit is '
    'INVERTED for this outcome.",'
    'tE:140,cE:100,type:"SAFETY",pubHR:1.42,pubHR_LCI:1.1,pubHR_UCI:1.84}]',
)

# ---------------------------------------------------------------------------
# 3. COMMANDER HF - ALL-CAUSE-death composite, not CV-death MACE.
#    ACM CI was 0.87-1.12; published is 0.87-1.10.
# ---------------------------------------------------------------------------
patch(
    "COMMANDER outcomes",
    'allOutcomes:[{shortLabel:"MACE",title:"All-cause death, MI, or stroke",tE:null,cE:null,'
    'type:"PRIMARY",pubHR:.94,pubHR_LCI:.84,pubHR_UCI:1.05},'
    '{shortLabel:"ACM",title:"All-cause mortality",tE:null,cE:null,type:"SECONDARY",'
    'pubHR:.98,pubHR_LCI:.87,pubHR_UCI:1.12}]',

    'allOutcomes:[{shortLabel:"PRIMARY_COMPOSITE",'
    'title:"All-cause death, MI, or stroke (all-cause-death composite)",'
    'endpointComponents:3,endpointExactMace:!1,countsReported:!0,'
    'endpointNote:"NOT a CV-death MACE. The death component is death from ANY cause, which in a '
    'decompensated HFrEF population is dominated by non-cardiovascular and pump-failure deaths '
    'that a CV-death/MI/stroke endpoint would not count. A harmonised CV-death/MI/stroke '
    'composite exists only as a POST-HOC analysis and is not used as the primary input here. '
    'Comparator is placebo (no background aspirin requirement), not aspirin alone.",'
    'tE:626,cE:658,type:"PRIMARY",pubHR:.94,pubHR_LCI:.84,pubHR_UCI:1.05},'
    '{shortLabel:"ACM",title:"All-cause mortality",countsReported:!1,'
    'endpointNote:"CORRECTED 2026-07-30: upper CI was 1.12, published value is 1.10 (NEJM 2018 '
    'abstract: 21.8% vs 22.1%, HR 0.98, 95% CI 0.87-1.10). Event counts are not reported as '
    'integers in the primary publication and are left null rather than back-calculated from '
    'percentages.",'
    'tE:null,cE:null,type:"SECONDARY",pubHR:.98,pubHR_LCI:.87,pubHR_UCI:1.1},'
    '{shortLabel:"Stroke",title:"Ischaemic stroke (POST-HOC, exploratory)",countsReported:!1,'
    'postHoc:!0,'
    'endpointNote:"POST-HOC exploratory analysis, HR 0.66 (95% CI 0.47-0.95), reported in BMJ '
    'Open 2023;13:e068865 (PMID 37567750). Not a prespecified COMMANDER HF outcome; counts are '
    'not published as integers. Downgrade for indirectness/selective reporting before use.",'
    'tE:null,cE:null,type:"EXPLORATORY",pubHR:.66,pubHR_LCI:.47,pubHR_UCI:.95}]',
)

# ---------------------------------------------------------------------------
# 4. ATLAS ACS 2 - wrong denominators (randomised vs mITT) and no counts.
#    5174/5176 are the RANDOMISED arm sizes; the 313/376 primary events belong
#    to the mITT analysis set of 5114/5113.
# ---------------------------------------------------------------------------
patch(
    "ATLAS header + outcomes",
    'name:"ATLAS ACS 2",pmid:"22077192",phase:"III",year:2012,tE:null,tN:5174,cE:null,cN:5176,'
    'group:"Recent ACS",publishedHR:.84,hrLCI:.72,hrUCI:.97,'
    'allOutcomes:[{shortLabel:"MACE",title:"CV death, MI, or stroke (2.5 mg arm)",tE:null,cE:null,'
    'type:"PRIMARY",pubHR:.84,pubHR_LCI:.72,pubHR_UCI:.97},'
    '{shortLabel:"ACM",title:"All-cause mortality",tE:null,cE:null,type:"SECONDARY",'
    'pubHR:.68,pubHR_LCI:.53,pubHR_UCI:.87}]',

    'name:"ATLAS ACS 2",pmid:"22077192",phase:"III",year:2012,tE:313,tN:5114,cE:376,cN:5113,'
    'group:"Recent ACS",publishedHR:.84,hrLCI:.72,hrUCI:.97,'
    'allOutcomes:[{shortLabel:"PRIMARY_COMPOSITE",'
    'title:"CV death, MI, or stroke (rivaroxaban 2.5 mg BID arm; mITT)",'
    'endpointComponents:3,endpointExactMace:!0,countsReported:!0,nT:5114,nC:5113,'
    'endpointNote:"CORRECTED 2026-07-30. Denominators were 5174/5176 - those are the RANDOMISED '
    'arm sizes; the 313 and 376 primary events belong to the mITT analysis set (5114 rivaroxaban '
    '2.5 mg BID vs 5113 placebo, CT.gov NCT00809965 results). Crude proportions are 6.1% vs 7.4%. '
    'The 9.1% and 10.7% figures previously shown are 2-year Kaplan-Meier estimates and must not '
    'be presented alongside these counts as if they were crude rates. Endpoint components match a '
    '3-point MACE, but the POPULATION (acute ACS within 7 days, on aspirin +/- thienopyridine) and '
    'the background therapy differ from the stable-ASCVD dual-pathway setting.",'
    'tE:313,cE:376,type:"PRIMARY",pubHR:.84,pubHR_LCI:.72,pubHR_UCI:.97},'
    '{shortLabel:"ACM",title:"All-cause mortality (2.5 mg BID arm)",countsReported:!1,'
    'endpointNote:"HR 0.68 (0.53-0.87); published rates 2.9% vs 4.5% are Kaplan-Meier estimates. '
    'Integer counts are not reported in the primary publication and are left null rather than '
    'back-calculated. This trial dominates any pooled all-cause-mortality estimate; the result '
    'should not be generalised across CAD/PAD/ACS/HF.",'
    'tE:null,cE:null,type:"SECONDARY",pubHR:.68,pubHR_LCI:.53,pubHR_UCI:.87},'
    '{shortLabel:"MajorBleed",title:"TIMI major bleeding not related to CABG (POOLED 2.5+5 mg)",'
    'countsReported:!1,harmOutcome:!0,pooledDoseArms:!0,'
    'endpointNote:"NEJM 2012 abstract reports 2.1% vs 0.6% (P<0.001) for rivaroxaban POOLED across '
    'the 2.5 mg and 5 mg arms, plus intracranial haemorrhage 0.6% vs 0.2% (P=0.009). A 2.5 mg-arm-'
    'specific hazard ratio was not extracted, so this entry is excluded from pooling and shown for '
    'context only. Bleeding was increased; fatal bleeding was not.",'
    'tE:null,cE:null,type:"SAFETY",excludeFromPooling:!0,pubHR:null,pubHR_LCI:null,pubHR_UCI:null}]',
)

# ---------------------------------------------------------------------------
# 5. Evidence quotes: stop presenting KM rates and crude proportions as one thing
# ---------------------------------------------------------------------------
patch(
    "ATLAS evidence text",
    'text:"In the 2.5 mg rivaroxaban arm, the primary end point occurred in 313 (9.1%) vs 376 '
    '(10.7%) placebo (HR 0.84; 95% CI, 0.72 to 0.97; P=0.02).",'
    'highlights:["313","5174","376","5176","0.84"]',

    'text:"Rivaroxaban 2.5 mg BID vs placebo, mITT: 313/5114 vs 376/5113 primary events (crude '
    '6.1% vs 7.4%); HR 0.84 (95% CI 0.72-0.97; P=0.02). The 9.1% vs 10.7% figures quoted in the '
    'NEJM abstract are 2-year Kaplan-Meier estimates, NOT crude proportions of these counts. '
    'Randomised arm sizes were 5174 and 5176; the primary analysis set is 5114 and 5113.",'
    'highlights:["313","5114","376","5113","0.84","6.1%","7.4%"]',
)

patch(
    "VOYAGER evidence text",
    'text:"The primary end point occurred in 508 (15.5%) rivaroxaban+aspirin vs 584 (17.8%) '
    'placebo+aspirin (HR 0.85; 95% CI, 0.76 to 0.96; P=0.009).",'
    'highlights:["508","3286","584","3278","0.85"]',

    'text:"The primary efficacy outcome - a FIVE-component composite of acute limb ischaemia, '
    'major amputation for vascular causes, myocardial infarction, ischaemic stroke, or death from '
    'cardiovascular causes - occurred in 508/3286 rivaroxaban+aspirin vs 584/3278 placebo+aspirin; '
    '3-year Kaplan-Meier incidence 17.3% vs 19.9% (HR 0.85; 95% CI 0.76-0.96; P=0.009). The crude '
    'proportions (15.5% and 17.8%) are NOT the published rates.",'
    'highlights:["508","3286","584","3278","0.85","17.3%","19.9%"]',
)

patch(
    "COMMANDER evidence text",
    'evidence:[{label:"Primary MACE",source:null,'
    'text:"The primary outcome occurred in 626 (25.0%) rivaroxaban vs 658 (26.2%) placebo '
    'patients (HR 0.94; 95% CI, 0.84 to 1.05; P=0.27)."',

    'evidence:[{label:"Primary composite (ALL-CAUSE death, MI, or stroke)",'
    'source:"NEJM 2018; 379:1332-1342",'
    'text:"The primary outcome - a composite of death from ANY cause, myocardial infarction, or '
    'stroke - occurred in 626/2507 (25.0%) rivaroxaban vs 658/2515 (26.2%) placebo (HR 0.94; '
    '95% CI 0.84-1.05; P=0.27). This is not a cardiovascular-death MACE. Comparator is placebo, '
    'not aspirin alone."',
)

patch(
    "ATLAS evidence label/source",
    'evidence:[{label:"Primary MACE",source:null,text:"Rivaroxaban 2.5 mg BID vs placebo, mITT',
    'evidence:[{label:"Primary composite (CV death, MI, or stroke; 2.5 mg arm)",'
    'source:"NEJM 2012; 366:9-19 + CT.gov NCT00809965 results",'
    'text:"Rivaroxaban 2.5 mg BID vs placebo, mITT',
)

# ---------------------------------------------------------------------------
# 6. Outcome key rename fallout + honest key labels
# ---------------------------------------------------------------------------
patch(
    "benchmark + prose maps",
    'BENCHMARK_OUTCOME_MAP={default:"MACE",MACE:"MACE",ACH:"MACE",ACM:"MACE",Renal40:"MACE",'
    'Hyperkalemia:"MACE",HF_CV_First:"MACE",KidneyComp:"MACE",Renal57:"MACE"}',
    'BENCHMARK_OUTCOME_MAP={default:"MACE",PRIMARY_COMPOSITE:"MACE",ACM:"MACE"},'
    'OUTCOME_KEY_LABELS={PRIMARY_COMPOSITE:"Trial-specific PRIMARY composite (NOT harmonised - '
    'endpoints differ between trials)",ACM:"All-cause mortality",'
    'Stroke:"Stroke (definitions and reporting level differ between trials)",'
    'MajorBleed:"Major bleeding (HARM - higher is worse)"}',
)

patch(
    "outcome prose",
    'ocProse={default:"the matched cardiovascular composite endpoint across CKD trials",'
    'MACE:"the cardiovascular composite endpoint",'
    'HF_CV_First:"first worsening heart failure event or cardiovascular death",'
    'Renal40:"the renal composite endpoint (kidney failure, ≥40% eGFR decline, or renal death)",'
    'KidneyComp:"the trial-specific kidney composite endpoint",'
    'Renal57:"the renal composite endpoint (≥57% eGFR decline)",'
    'ACM:"all-cause mortality",ACH:"hospitalization for heart failure",'
    'Hyperkalemia:"hyperkalemia events"}',

    'ocProse={default:"each trial\'s own primary composite endpoint (these are NOT the same '
    'endpoint across trials)",'
    'PRIMARY_COMPOSITE:"each trial\'s own primary composite endpoint (these are NOT the same '
    'endpoint across trials)",'
    'ACM:"all-cause mortality",Stroke:"stroke",'
    'MajorBleed:"major bleeding (a harm outcome - a hazard ratio above 1 favours the comparator)"}',
)

patch(
    "outcomeLabel override",
    'outcomeLabel(key){const m=this._derivedOutcomeMap();',
    'outcomeLabel(key){if("undefined"!=typeof OUTCOME_KEY_LABELS&&OUTCOME_KEY_LABELS[String(key)])'
    'return OUTCOME_KEY_LABELS[String(key)];const m=this._derivedOutcomeMap();',
)

# ---------------------------------------------------------------------------
# 7. Finerenone-template contamination (rivaroxaban is a factor Xa inhibitor)
# ---------------------------------------------------------------------------
patch(
    "MRA narrative (generator)",
    'narrative=`Rivaroxaban (Low-Dose), a non-steroidal mineralocorticoid receptor antagonist, ',
    'narrative=`Rivaroxaban (Low-Dose), a direct oral factor Xa inhibitor, ',
)

patch(
    "MRA narrative (i18n key)",
    '"Rivaroxaban (Low-Dose), a non-steroidal mineralocorticoid receptor antagonist, demonstrated '
    'a statistically significant"',
    '"Rivaroxaban (Low-Dose), a direct oral factor Xa inhibitor, demonstrated a statistically '
    'significant"',
)

patch(
    "kidney-events plain language (generator)",
    '"Rivaroxaban (Low-Dose) reduced the risk of major heart and kidney events by about "',
    '"Rivaroxaban (Low-Dose) reduced the risk of the pooled primary composite endpoint by about "',
)

patch(
    "kidney-events plain language (i18n key)",
    '"Rivaroxaban (Low-Dose) reduced the risk of major heart and kidney events by about"',
    '"Rivaroxaban (Low-Dose) reduced the risk of the pooled primary composite endpoint by about"',
)

# ---------------------------------------------------------------------------
# 8. PRISMA: make the flow arithmetically consistent and stop claiming
#    full-text assessment the declared data boundary rules out.
# ---------------------------------------------------------------------------
patch(
    "PRISMA generate()",
    'excludedOther:excluded-excludedPhaseII-excludedZeroEvent}}',
    'excludedOther:excluded-excludedPhaseII-excludedZeroEvent,'
    'awaitingScreening:Math.max(0,afterDedup-excluded-included),'
    'assessedForEligibility:included,excludedAtEligibility:0,'
    'flowBalances:afterDedup===excluded+included+Math.max(0,afterDedup-excluded-included)}}',
)

patch(
    "PRISMA eligibility boxes",
    '${box(250,295,200,45,"Full-text assessed",data.screened-data.excluded)}',
    '${box(215,295,270,45,"Assessed for eligibility (registry + abstract level)",'
    'data.assessedForEligibility)}',
)

patch(
    "PRISMA eligibility excluded box",
    '${box(500,295,160,50,"Excluded",data.excluded)}\\n\\n\\n                    '
    '<text x="505" y="360" fill="#64748b" font-size="8" font-family="system-ui">'
    'Phase I/II: ${data.excludedPhaseII}</text>',
    '${box(500,295,160,50,"Excluded at eligibility",data.excludedAtEligibility)}'
    '\\n\\n\\n                    <text x="505" y="360" fill="#64748b" font-size="8" '
    'font-family="system-ui">Not recorded separately</text>',
)

patch(
    "PRISMA screening excluded label + awaiting box",
    '${box(500,200,150,40,"Excluded",data.excluded)}',
    '${box(500,196,150,40,"Excluded at screening",data.excluded)}\\n\\n\\n                    '
    '${box(30,196,180,40,"Awaiting screening decision",data.awaitingScreening)}\\n\\n\\n'
    '                    <text x="120" y="252" text-anchor="middle" fill="#f59e0b" font-size="8" '
    'font-family="system-ui">not yet adjudicated</text>',
)

patch(
    "PRISMA footer balance note",
    '${data.pendingData>0?`<text x="350" y="465" text-anchor="middle" fill="#f59e0b" '
    'font-size="9" font-family="system-ui">${data.pendingData} included but awaiting data</text>`:""}',

    '${data.pendingData>0?`<text x="350" y="462" text-anchor="middle" fill="#f59e0b" '
    'font-size="9" font-family="system-ui">${data.pendingData} included but awaiting data</text>`:""}'
    '\\n\\n\\n                    <text x="350" y="492" text-anchor="middle" fill="#94a3b8" '
    'font-size="9" font-family="system-ui">Balance: ${data.screened} screened = ${data.excluded} '
    'excluded + ${data.awaitingScreening} awaiting + ${data.assessedForEligibility} assessed'
    '</text>\\n\\n\\n                    <text x="350" y="508" text-anchor="middle" fill="#f59e0b" '
    'font-size="8" font-family="system-ui">No full-text eligibility stage was performed: '
    'extraction is limited to registry records and abstracts.</text>'
    '\\n\\n\\n                    <text x="350" y="522" text-anchor="middle" fill="#f59e0b" '
    'font-size="8" font-family="system-ui">The 4 analysed trials entered as a preloaded landmark '
    'reference set, not reproducibly from the database searches.</text>',
)

# ---------------------------------------------------------------------------
# 9. Protocol / registration claim + version reconciliation
# ---------------------------------------------------------------------------
patch(
    "PROSPERO-equivalence claim",
    'Per ICMJE 2023, GitHub commit hash + timestamp constitutes a verifiable pre-registration '
    'record',
    'This is a RETROSPECTIVE public protocol pack. A GitHub commit hash and timestamp are a '
    'tamper-evident record of when a document was published, which is genuine transparency - but '
    'it is NOT prospective registration and is NOT equivalent to PROSPERO. This review is not '
    'registered',
)

# Version strings disagreed: document title said v12.5, every internal/export
# string said v12.0, and the Arabic locale said 11.0. Unify on v12.5.
patch(
    "version strings",
    'v12.0',
    'v12.5',
    count=None,  # replace all occurrences
)

patch(
    "version string (ar locale)",
    '"Precision v12.5":"الدقة الإصدار 11.0"',
    '"Precision v12.5":"الدقة الإصدار 12.5"',
)


def main():
    if not TARGET.exists():
        print(f"FAIL: {TARGET} not found (run from repo root)")
        return 1

    src = TARGET.read_text(encoding="utf-8")
    original = src
    applied = []

    for name, old, new, count in PATCHES:
        found = src.count(old)
        if count is None:
            if found == 0:
                print(f"FAIL [{name}]: anchor not found")
                return 1
            src = src.replace(old, new)
            applied.append(f"{name} (x{found})")
            continue
        if found != count:
            print(f"FAIL [{name}]: expected {count} occurrence(s), found {found}")
            print(f"  anchor head: {old[:120]}...")
            return 1
        src = src.replace(old, new, count)
        applied.append(name)

    if src == original:
        print("FAIL: no changes produced")
        return 1

    TARGET.write_text(src, encoding="utf-8", newline="\n")
    print(f"OK: {len(applied)} patch groups applied to {TARGET}")
    for a in applied:
        print(f"  - {a}")
    print("\nProvenance:")
    for k, v in PATCH_PROVENANCE.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
