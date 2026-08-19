"""HAND ADJUDICATION of the 11 the corrected question still could not settle.

45 re-asked -> 36 agreed on disposition -> 9 real disagreements + 2 both-UNCLEAR = 11 read here
from armGroups. ALL ELEVEN ARE EXCLUDED.

AND READING THEM EXPOSED A GAP IN WHAT HAD ALREADY BEEN TREATED AS SETTLED.

    Under the OLD question, 62 of the 130 agreed -- and 16 of those agreed on A=YES, B=YES,
    which the old mapping read as ELIGIBLE. But an ADJUNCT trial with a NO_INTERVENTION control
    answers exactly that way: 'mental training vs no intervention, everyone having had an
    ablation' has an arm delivering ablation (YES) and an arm that is not itself an ablation
    (YES). THE OLD QUESTION CANNOT DISTINGUISH THAT FROM ABLATION-AGAINST-USUAL-CARE.

    So the 16 ELIGIBLE verdicts inherited from the old question are CONTAMINATED, and they are
    contaminated in the direction that ADMITS trials to the review. The other 46 old-question
    agreements were exclusions, where the same ambiguity produces the right disposition for the
    wrong reason -- tolerable in a screen, and recorded as such rather than silently relied on.

    A CORRECTION THAT STOPS AT THE CASES THAT LOOKED WRONG IS NOT A CORRECTION OF THE CLASS.
    The 16 are re-asked; they are not carried forward on the strength of an agreement reached
    under a question this run has just shown to be ambiguous.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(REPO, "evidence", "2026-08-19-batch1", "ablation_reask_hand.json")

ROWS = [
    ("NCT01649544", "EXCLUDED", "INTERVENTION",
     "EPICOR vs Amiodarone. Codex read this ELIGIBLE (ablation against a drug); agy read it "
     "SURGICAL and agy is right -- EPICOR is an epicardial ultrasound ablation system and the "
     "trial's own title says 'Surgical Ultrasound'. A surgical ablation against amiodarone is "
     "still not catheter ablation. THE ONLY CASE IN THE 11 WHERE THE ELIGIBLE READING WAS THE "
     "WRONG ONE, and it would have admitted a trial."),
    ("NCT01959425", "EXCLUDED", "INTERVENTION",
     "'Off OAT' vs 'On OAT' -- oral anticoagulation therapy after ablation. The ablation is in "
     "both arms; the contrast is anticoagulation. Codex ABLATION_IN_ALL right; agy refused."),
    ("NCT02238392", "EXCLUDED", "INTERVENTION",
     "Adenosine test vs AF termination as the PROCEDURAL ENDPOINT of a paroxysmal AF ablation. "
     "Both arms are ablated; what differs is when the operator stops. Codex right."),
    ("NCT02392338", "EXCLUDED", "INTERVENTION",
     "thoracoscopic ablation vs hybrid procedure. Both surgical. agy read it as ablation "
     "against 'other' and would have kept it in scope; codex CONTRAST_SURGICAL is right. NOTE "
     "the thoracoscopic arm is typed NO_INTERVENTION, which is a registrant's convention and "
     "not an absence of treatment."),
    ("NCT03268707", "EXCLUDED", "INTERVENTION",
     "telemetric smartphone application vs conventional follow-up after ablation."),
    ("NCT03389633", "EXCLUDED", "INTERVENTION",
     "cardiac rehabilitation vs none, for AF recurrence after ablation."),
    ("NCT03557034", "EXCLUDED", "INTERVENTION",
     "Kardia monitoring platform vs standard-of-care monitoring."),
    ("NCT03635034", "EXCLUDED", "INTERVENTION",
     "BLADDER CATHETER vs none during ablation procedures."),
    ("NCT04659213", "EXCLUDED", "INTERVENTION",
     "an oesophageal deviation catheter vs no intervention DURING radiofrequency ablation of "
     "AF. Codex read this CONTRAST_ABLATION -> ELIGIBLE; the ablation is in both arms and the "
     "contrast is the deviation device. agy's UNCLEAR was the safer answer and the "
     "conservative direction was the correct one here."),
    # --- the two both-UNCLEAR. In BOTH, the ARM DATA IS GENUINELY UNINFORMATIVE and the
    # --- verdict therefore rests on the TITLE. Which field it rests on is stated, per P11.
    ("NCT03026413", "EXCLUDED", "COMPARATOR",
     "BOTH ARMS DECLARE THE SAME INTERVENTION NAME -- 'Procedure: pulmonary vein antrum "
     "modification' in the experimental arm AND in the arm labelled 'Control arm'. The arm "
     "data cannot distinguish them and both seats were right to refuse. THE VERDICT RESTS ON "
     "THE TITLE, not on the coded arms: 'The Comparison Between the PVAM and CPVI' -- two "
     "ablation techniques against each other. Stated because a verdict resting on free text "
     "where the coded field is uninformative must say so."),
    ("NCT04240366", "EXCLUDED", "INTERVENTION",
     "arms declared as 'Procedure: Control intervention' and 'Procedure: Experimental "
     "intervention' -- literally uninformative, and both seats refused correctly. THE VERDICT "
     "RESTS ON THE TITLE: 'Additional Left Atrial Appendage Isolation During Balloon Ablation'. "
     "Both arms receive balloon ablation; the contrast is the additional LAA isolation."),
]

# The 16 ELIGIBLE verdicts inherited from the OLD question, which must not be carried forward.
CONTAMINATED_ELIGIBLE_NOTE = (
    "16 trials agreed A=YES B=YES under the OLD question and were mapped ELIGIBLE. An ADJUNCT "
    "trial with a NO_INTERVENTION control answers exactly that way, so the mapping cannot "
    "distinguish 'ablation against usual care' from 'something-else against nothing, in "
    "patients who all had an ablation'. They are re-asked, not inherited.")


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    from collections import Counter
    print("hand-adjudicated: %d" % len(ROWS))
    print("verdicts: %s" % Counter(v for _n, v, _l, _w in ROWS).most_common())
    print("by limb:  %s" % Counter(l for _n, _v, l, _w in ROWS).most_common())
    print("\nALL ELEVEN ARE EXCLUDED.")
    print("\nTWO verdicts rest on the TITLE because the coded arm data is uninformative --")
    print("NCT03026413 (both arms name the same procedure) and NCT04240366 ('Control")
    print("intervention' vs 'Experimental intervention'). Both seats refused on both, correctly.")
    print("\nONE case would have admitted a trial: NCT01649544, where codex read EPICOR as a")
    print("catheter ablation against amiodarone. It is a SURGICAL ultrasound ablation system.")
    out = {"adjudicated_utc": "2026-08-19", "n": len(ROWS), "all_excluded": True,
           "by_limb": dict(Counter(l for _n, _v, l, _w in ROWS)),
           "verdicts_resting_on_free_text": ["NCT03026413", "NCT04240366"],
           "contaminated_eligible_from_old_question": CONTAMINATED_ELIGIBLE_NOTE,
           "trials": [{"nct": n, "verdict": v, "limb": l, "why": w} for n, v, l, w in ROWS]}
    with io.open(DEST, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, indent=1))
    print("\nwrote %s" % DEST)
    return 0


if __name__ == "__main__":
    sys.exit(main())
