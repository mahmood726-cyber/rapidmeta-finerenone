"""cangrelor-pci-review: render the disagreement where a reader meets the estimate.

WE ARE NOT WITHHOLDING A REFUSAL; WE ARE WITHHOLDING A DISAGREEMENT. A reader meeting
0.9646 (0.8132 to 1.1442) is currently told this composite is compatible with no benefit,
with NO INDICATION that a larger prespecified patient-level analysis of the same programme
returned 0.81 (0.71 to 0.92) -- which excludes no difference. That is the withholding
failure inverted, and it is fixed here by the same mechanism as the referrals: a
POOL_FINDINGS_ key that the projector renders IMMEDIATELY AFTER the estimate sentence.

WHAT THE TRIAL-SET INVESTIGATION ESTABLISHED, KEYED BY REGISTRATION ID.

Three possibilities were named: the third trial is in the object and excluded, in the object
and unpooled, or never surfaced by the search. IT IS THE FIRST, AND THE EXCLUSION IS
DOCUMENTED AND PRINCIPLED.

    NCT01156571 (CHAMPION PHOENIX) IS ON THIS OBJECT. It is excluded from the corrected
    composite for a stated, checkable reason: it registers a FOUR-component composite,
    adding STENT THROMBOSIS to the same three, and its counts are recorded so the exclusion
    can be checked -- 257/5470 against 322/5469.

    NOT a search failure. NOT an oversight. The object declined to pool a differing
    estimand -- WHICH IS THE DISCIPLINE CLASS 76 SAYS WE LACK, CORRECTLY APPLIED HERE.

AND THE TWO SYMPTOMS SHARE ONE CAUSE, WHICH WAS THE QUESTION ASKED. The declared primary
carries no pooled estimate because this page was WITHDRAWN for a data-integrity error:
numerators from ALL-CAUSE MORTALITY were carried against the primary composite's
denominators, on all three trials. The primary was nulled by that withdrawal; the corrected
composite was then rebuilt from the two trials whose registered primary matches word for
word. ONE CAUSE, TWO SYMPTOMS -- confirmed, not assumed.

SO WHY DO THE NUMBERS STILL DISAGREE? Steg et al. had PATIENT-LEVEL DATA and could
construct the three-component composite for PHOENIX; from aggregates we cannot, because
PHOENIX only REGISTERS the four-component version. THE DISAGREEMENT IS EXPLAINED BY DATA
ACCESS, NOT BY AN ERROR ON EITHER SIDE -- and their answer is the better one, because
patient-level data let them include a trial we honestly cannot.

THAT CORRECTS MY OWN EARLIER FRAMING. The first comparison block said "a dropped trial is
the likeliest cause" and put the k difference first. The trial was not dropped; it was
excluded with a reason, and reporting it as a drop implied a carelessness that the object's
own record refutes. The comparison block is amended here rather than left standing.

NO STORED NUMBER IS CHANGED.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import atomic_write

TOPIC = "cangrelor-pci-review"
TODAY = "2026-08-20"
STAMP = TODAY.replace("-", "_")
OBJ = os.path.join(REPO, "ssot", TOPIC, TOPIC + ".json")


def main():
    dry = "--apply" not in sys.argv
    obj = json.load(io.open(OBJ, encoding="utf-8"))
    blk = ((obj.get("results") or {}).get("by_outcome") or {}).get(
        "corrected_composite_3component")
    if not isinstance(blk, dict):
        sys.exit("REFUSED: corrected_composite_3component is not on this object.")
    p = blk.get("pooled") or {}
    if p.get("point") is None:
        sys.exit("REFUSED: no pooled point to attach a finding to.")

    blk["POOL_FINDINGS_%s" % STAMP] = {
        "a_a_published_patient_level_analysis_disagrees_with_this_estimate": (
            "THIS ESTIMATE IS COMPATIBLE WITH NO BENEFIT AND A LARGER PRESPECIFIED ANALYSIS "
            "IS NOT. This pool: %s (%s to %s) on 2 trials, from published aggregate counts. "
            "Steg et al., Lancet 2013 (PMID 24011551), a PRESPECIFIED POOLED ANALYSIS OF "
            "PATIENT-LEVEL DATA from ALL THREE CHAMPION trials, 24,910 patients: the same "
            "three-component composite -- all-cause death, myocardial infarction or "
            "ischaemia-driven revascularisation at 48 hours -- returns ODDS RATIO 0.81 "
            "(0.71 to 0.92). THEIR INTERVAL EXCLUDES NO DIFFERENCE AND THIS ONE DOES NOT."
            % (p.get("point"), p.get("ci_low"), p.get("ci_high"))),
        "b_why_the_two_differ_and_it_is_not_an_error_on_either_side": (
            "THE THIRD TRIAL. CHAMPION PHOENIX (NCT01156571) is on this object and is "
            "EXCLUDED from this pool with a stated reason: it registers a FOUR-component "
            "composite, adding stent thrombosis to the same three, and its counts are "
            "recorded here so the exclusion is checkable -- 257/5470 against 322/5469. "
            "Steg et al. had PATIENT-LEVEL DATA and could rebuild the three-component "
            "composite for PHOENIX; FROM PUBLISHED AGGREGATES THAT CANNOT BE DONE. The "
            "difference is one of DATA ACCESS, not of care."),
        "c_which_estimate_a_reader_should_prefer": (
            "THEIRS. A prespecified patient-level analysis of three trials is stronger "
            "evidence than an aggregate-data pool of two, and it includes a trial this "
            "object cannot include honestly. This pool is reported because it is what the "
            "registered aggregate data support; IT IS NOT OFFERED AS THE BETTER ANSWER."),
        "d_what_remains_unresolved": (
            "Whether this object should carry a three-component pool at all, given that the "
            "quantity is recoverable only with patient-level data that this review does not "
            "have. That is a content decision and has not been made."),
    }

    pc = obj.get("published_comparison") or {}
    if isinstance(pc, dict) and pc.get("reviews"):
        pc["CORRECTION_%s" % STAMP] = (
            "AN EARLIER SENTENCE IN THIS BLOCK SAID 'a dropped trial is the likeliest "
            "cause' AND PUT THE k DIFFERENCE FIRST. THE TRIAL WAS NOT DROPPED. NCT01156571 "
            "is on this object and is excluded from the corrected composite for a stated, "
            "checkable reason -- it registers a four-component composite. Calling it a drop "
            "implied a carelessness the object's own record refutes, and the correction is "
            "recorded here rather than made silently.")

    obj.setdefault("display_change_announced", []).append({
        "date": TODAY,
        "change": ("the disagreement with the published patient-level analysis now RENDERS "
                   "beside the estimate"),
        "values_moved": "NONE",
        "what_changed": (
            "A reader meeting 0.9646 (0.8132-1.1442) is now told that Steg 2013 returned "
            "0.81 (0.71-0.92) on all three trials at patient level, why the two differ, and "
            "which to prefer."),
        "why": ("Withholding a disagreement is the withholding failure inverted. The "
                "referral mechanism already existed; this uses it."),
    })

    print("cangrelor: POOL_FINDINGS attached to corrected_composite_3component")
    print("  ESTABLISHED: NCT01156571 is ON the object and EXCLUDED with a stated reason")
    print("  -> not a search failure, not an oversight; a documented estimand exclusion")
    print("  ONE CAUSE, TWO SYMPTOMS: the withdrawal for mismatched numerators nulled the")
    print("  primary AND forced the corrected composite onto the two matching trials.")
    if dry:
        print("DRY RUN -- pass --apply to write")
        return
    atomic_write.write_json(OBJ, obj, indent=1)
    print("wrote %s" % OBJ)


if __name__ == "__main__":
    main()
