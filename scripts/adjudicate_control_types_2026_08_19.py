"""FINAL 11 of the 621: 8 disputed control types + 3 inherited-ELIGIBLE that held.

ONE JUDGEMENT SETTLES SIX OF THE EIGHT, AND IT IS THE RULE THIS PROJECT ALREADY OWNS.

    A TREATMENT PRESENT IN EVERY ARM IS BACKGROUND, AND THE CONTRAST IS WHAT DIFFERS.

Six of the eight disputed trials share the shape `X + ablation` against `X`:
    DCCV + PVI            vs DCCV                       NCT03907982
    DCCV + PVI            vs DCCV + sham                NCT06096246
    LAA occlusion + PFA   vs LAA occlusion              NCT06334250
    LAA closure + PFA     vs LAA closure                NCT07453940
    cryoablation          vs placebo procedure          NCT04272762
    pulsed-field ablation vs sham procedure             NCT05717725, NCT07403760
The cardioversion, the appendage closure and the sham are in BOTH arms or are nothing at all.
THE ABLATION IS WHAT THE RANDOMISATION VARIES, so these are eligible -- and the two seats
disagreed because one read the control arm's CONTENT ("a procedure, so OTHER") and the other
read its ROLE ("no active treatment, so USUAL"). Both were reading truly; the question was
which of the two the criterion asks about, and it asks about the contrast.

AND A SHAM-CONTROLLED ABLATION TRIAL IS COUNTED AS ELIGIBLE, WHICH IS A STATED JUDGEMENT.
A sham arm receives no ablation and continues background medical management, so the contrast is
ablation against no ablation on common therapy -- the cleanest available form of this review's
question, not a departure from it. WHAT WOULD CHANGE IT: a reader who requires the comparator to
be an actively-managed drug strategy rather than an absence would exclude all four sham trials,
and can see here exactly which four they are.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(REPO, "evidence", "2026-08-19-batch1", "ablation_control_types.json")

ROWS = [
    # --- the six "X + ablation vs X" and sham designs
    ("NCT03907982", "ELIGIBLE_NOT_POOLABLE", "POOLABILITY", "ESTIMAND",
     "DCCV + PVI vs DCCV alone. CARDIOVERSION IS IN BOTH ARMS and is therefore background; the "
     "contrast is the pulmonary vein isolation. Eligible. COMPLETED with posted results, and "
     "its primary is RECURRENCE OF PERSISTENT AF; its secondaries list Death and hospital "
     "readmission SEPARATELY and never as a composite. No all-cause-mortality composite at any "
     "rank."),
    ("NCT04011800", "ELIGIBLE_NO_RESULTS_YET", "STATUS", "NO RESULTS POSTED",
     "PRAGUE-25: catheter ablation vs antiarrhythmic drugs with risk-factor modification. "
     "Eligible -- and the AAD component rests on the TITLE, because the control arm's coded "
     "name is only 'Combination Product: Risk Factor Modification'. Status UNKNOWN, "
     "hasResults=false. Its secondary composite is stroke / CARDIOVASCULAR death / heart-"
     "failure hospitalisation -- cardiovascular, not all-cause, so it is a near neighbour of "
     "this estimand and not this estimand."),
    ("NCT04272762", "ELIGIBLE_NO_RESULTS_YET", "STATUS", "NO RESULTS POSTED",
     "cryoablation vs a PLACEBO procedure. A sham-controlled ablation trial: eligible by the "
     "stated judgement above. COMPLETED but hasResults=false -- nothing to extract."),
    ("NCT05717725", "ELIGIBLE_NO_RESULTS_YET", "STATUS", "NO RESULTS POSTED",
     "pulsed-field ablation vs SHAM ablation. RECRUITING."),
    ("NCT06096246", "ELIGIBLE_NO_RESULTS_YET", "STATUS", "NO RESULTS POSTED",
     "DCCV + PVI vs DCCV + SHAM. Cardioversion in both arms; the contrast is the PVI against a "
     "sham. RECRUITING."),
    ("NCT06334250", "ELIGIBLE_NO_RESULTS_YET", "STATUS", "NO RESULTS POSTED",
     "left atrial appendage occlusion + pulsed-field ablation vs occlusion alone. THE OCCLUSION "
     "IS IN BOTH ARMS; the contrast is the ablation. WITHDRAWN -- it will never report, and "
     "that is recorded as a status rather than as an exclusion."),
    ("NCT07403760", "ELIGIBLE_NO_RESULTS_YET", "STATUS", "NO RESULTS POSTED",
     "catheter ablation vs SHAM control. RECRUITING."),
    ("NCT07453940", "ELIGIBLE_NO_RESULTS_YET", "STATUS", "NO RESULTS POSTED",
     "LAA closure + pulsed-field ablation vs LAA closure alone. Closure in both arms. "
     "ENROLLING_BY_INVITATION."),
    # --- the three inherited-ELIGIBLE that survived the corrected question
    ("NCT00116428", "ELIGIBLE_NOT_POOLABLE", "POOLABILITY", "ESTIMAND",
     "NAVISTAR THERMOCOOL catheter vs ANTIARRHYTHMIC DRUG -- the cleanest ablation-against-"
     "medical-therapy contrast in the whole remainder, and both seats agreed under both "
     "questions. COMPLETED with posted results. Its primaries are CHRONIC SUCCESS of the "
     "catheter and serious-adverse-event incidence: a device-effectiveness endpoint, not a "
     "clinical event composite."),
    ("NCT06166524", "ELIGIBLE_NO_RESULTS_YET", "STATUS", "NO RESULTS POSTED",
     "pulsed-field ablation vs a conservative arm in ASYMPTOMATIC non-paroxysmal AF. Status "
     "UNKNOWN, hasResults=false. Its primary is CHANGES IN VO2 MAX, so it will not contribute "
     "an effect estimate on this estimand when it does report -- stated so it is not mistaken "
     "for a trial that will change the answer."),
    # --- THE FIVE THAT FLIPPED FROM INHERITED-ELIGIBLE TO EXCLUDED.
    #
    # These were reported as "5 flipped to EXCLUDED" and were NOT WRITTEN TO ANY EVIDENCE FILE
    # until the consolidation refused: 616 of 621 had a verdict and these five had none. A
    # number stated in a report with no artefact behind it is exactly what the arithmetic gate
    # exists to catch, and it caught one written by the author of the gate.
    ("NCT01058980", "EXCLUDED", "ELIGIBILITY", "INTERVENTION",
     "both seats now say the ablation is in every arm or on both sides -- 'Additional ablation "
     "until elimination of dormant conduction' against 'No additional ablation' plus a registry "
     "group. The contrast is an ablation ENDPOINT strategy, not ablation against medical "
     "therapy."),
    ("NCT01503268", "EXCLUDED", "ELIGIBILITY", "COMPARATOR",
     "percutaneous ablation vs SURGICAL ablation vs DCCV, all with an implantable loop "
     "recorder. Both seats read the control as another procedure."),
    ("NCT02528604", "EXCLUDED", "ELIGIBILITY", "COMPARATOR",
     "both seats read the comparator as another procedure or device rather than medical "
     "therapy or usual care."),
    ("NCT03276169", "EXCLUDED", "ELIGIBILITY", "COMPARATOR",
     "both seats read the comparator as another procedure or device."),
    ("NCT03351816", "EXCLUDED", "ELIGIBILITY", "COMPARATOR",
     "both seats read the comparator as another procedure or device."),
    ("NCT07447297", "EXCLUDED", "ELIGIBILITY", "INTERVENTION",
     "'EARLY RHYTHM CONTROL' vs general control, where the intervention arm declares "
     "'Drug: early rhythm control group' AND 'Procedure: cardioversion, catheter ablation'. "
     "THE CONTRAST IS A STRATEGY COMBINING DRUGS, CARDIOVERSION AND ABLATION, so no estimate "
     "from it is attributable to ablation. THIS TRIAL BELONGS TO THE SIBLING REVIEW -- "
     "early-rhythm-control-af -- and its appearance here is the split doing exactly what it "
     "was decided for: a trial that is out of scope for one question is in scope for another, "
     "and neither review has to discard it."),
]


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    from collections import Counter
    print("final adjudications: %d" % len(ROWS))
    for k, v in Counter(v for _n, v, _a, _c, _w in ROWS).most_common():
        print("   %-28s %2d" % (k, v))
    print("\nSIX OF THE EIGHT DISPUTED TURN ON ONE RULE THIS PROJECT ALREADY OWNS:")
    print("   a treatment present in EVERY arm is background, and the contrast is what differs.")
    print("The two seats were reading the control arm's CONTENT against its ROLE. Both read")
    print("truly; the criterion asks about the contrast.")
    print("\nONE TRIAL GOES TO THE SIBLING REVIEW rather than being discarded -- NCT07447297,")
    print("an early-rhythm-control strategy. That is the split working as decided.")
    out = {"adjudicated_utc": "2026-08-19", "n": len(ROWS),
           "tally": dict(Counter(v for _n, v, _a, _c, _w in ROWS)),
           "sham_controlled_counted_eligible": {
               "trials": ["NCT04272762", "NCT05717725", "NCT06096246", "NCT07403760"],
               "judgement": ("a sham arm receives no ablation and continues background medical "
                             "management, so the contrast is ablation against no ablation on "
                             "common therapy -- the cleanest form of this review's question."),
               "what_would_change_it": ("a reader requiring an actively-managed drug comparator "
                                        "rather than an absence would exclude these four, and "
                                        "can see exactly which four they are.")},
           "trials": [{"nct": n, "verdict": v, "axis": a, "criterion": c, "why": w}
                      for n, v, a, c, w in ROWS]}
    with io.open(DEST, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, indent=1))
    print("\nwrote %s" % DEST)
    return 0


if __name__ == "__main__":
    sys.exit(main())
