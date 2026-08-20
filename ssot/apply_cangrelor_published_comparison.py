"""cangrelor-pci-review: the published comparison, P46 limb 3 -- and it DISAGREES.

MY PREDICTION WAS HALF WRONG AND THE WRONG HALF IS THE INTERESTING ONE.

Before this screen ran I predicted cangrelor-pci-review would NOT yield a class-76 instance
-- same drug, one programme -- and added that "a published pooled analysis of exactly those
trials is likely to exist and agree". IT EXISTS. IT DOES NOT AGREE.

    Steg et al., Lancet 2013, PMID 24011551 -- "Effect of cangrelor on periprocedural
    outcomes in percutaneous coronary interventions: a pooled analysis of patient-level
    data". PRESPECIFIED, PATIENT-LEVEL, ALL THREE CHAMPION TRIALS, 24,910 patients in the
    modified intention-to-treat population.

        published secondary triple composite   OR 0.81 (0.71 to 0.92), p = 0.0014
          -- all-cause death, myocardial infarction, or ischaemia-driven
             revascularisation at 48 h, across THREE trials

        this object, corrected_composite_3component
                                               0.9646 (0.8132 to 1.1442), k = 2

    THE PUBLISHED INTERVAL EXCLUDES NO DIFFERENCE AND OURS DOES NOT. Those are opposite
    readings of the same question, and the difference is not a rounding matter.

TWO THINGS ARE DIFFERENT AND ONLY ONE OF THEM IS ARGUABLE.

  1. THEY POOL THREE TRIALS AND THIS OBJECT POOLS TWO. k = 2 against k = 3, on a composite
     the published analysis reports across all three. A dropped trial is the first thing
     that would produce this gap and it is stated first.
  2. Patient-level against aggregate data. That difference alone does not usually move a
     point estimate from 0.81 to 0.96.

AND THIS OBJECT'S DECLARED PRIMARY CARRIES NO POOLED ESTIMATE AT ALL -- k = 3 with a null
point. So the outcome the review declares as primary is unpooled, while the outcome that
disagrees with the literature is a "corrected" three-component composite. This object's own
question already says the numbers it used "were not the ones they answered it with".

NOTHING IS RECONCILED HERE AND NO STORED NUMBER IS CHANGED. Which trial is missing, and
whether 0.9646 should stand, is a content decision. What this limb owes is the comparison
with its denominator, and the disagreement stated at full strength rather than softened.
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
SCREEN = os.path.join(REPO, "ssot", TOPIC, "appraisal",
                      "PUBLISHED_SYNTHESIS_SCREEN.json")

QUERY = ('(cangrelor[tiab]) AND (CHAMPION[tiab] OR meta-analysis[pt] OR "systematic '
         'review"[pt] OR meta-analysis[tiab] OR "pooled analysis"[tiab])')


def main():
    dry = "--apply" not in sys.argv
    obj = json.load(io.open(OBJ, encoding="utf-8"))
    ncts = set(t.get("nct") for t in (obj.get("inputs") or {}).get("trials") or [])
    for need in ("NCT00305162", "NCT00385138", "NCT01156571"):
        if need not in ncts:
            sys.exit("REFUSED: %s is not on this object (%r)." % (need, sorted(ncts)))

    byo = (obj.get("results") or {}).get("by_outcome") or {}
    ours = (byo.get("corrected_composite_3component") or {}).get("pooled") or {}
    if ours.get("point") is None:
        sys.exit("REFUSED: the 3-component composite carries no point to compare.")

    pc = {
        "_why": (
            "P46 limb 3. A prespecified PATIENT-LEVEL pooled analysis of all three CHAMPION "
            "trials exists and DISAGREES with this object on the three-component "
            "composite, in a direction that changes the conclusion."),
        "_how_identified": (
            "PubMed E-utilities, executed %s. Query, counts and per-record disposition in "
            "ssot/%s/appraisal/PUBLISHED_SYNTHESIS_SCREEN.json." % (TODAY, TOPIC)),
        "denominator": {
            "matched": 99,
            "retrieved": 99,
            "read": 99,
            "appraised": 1,
            "not_returned_by_the_tool": 0,
            "_house_form": (
                "matched / retrieved / read / appraised / not returned -- P53. The query "
                "matched 99 and listed all 99, so nothing was lost to the tool. 66 records "
                "were flagged by title; ONE was appraised against its abstract and 65 were "
                "NOT READ."),
        },
        "identity_basis": (
            "All three contributing trials are keyed to verified registrations on this "
            "object -- NCT00305162, NCT00385138, NCT01156571 -- and the appraised analysis "
            "NAMES ALL THREE (CHAMPION-PCI, CHAMPION-PLATFORM, CHAMPION-PHOENIX) in its "
            "abstract. The trial-set match is READ."),
        "reviews": [{
            "pmid": "24011551",
            "year": 2013,
            "journal": "Lancet",
            "title": ("Effect of cangrelor on periprocedural outcomes in percutaneous "
                      "coronary interventions: a pooled analysis of patient-level data"),
            "trial_set": ["CHAMPION-PCI", "CHAMPION-PLATFORM", "CHAMPION-PHOENIX"],
            "trial_set_basis": "ALL THREE NAMED in the abstract.",
            "design": "PRESPECIFIED pooled analysis of PATIENT-LEVEL data, k = 3",
            "n_pooled": 24910,
            "outcome_pooled": (
                "primary: death, myocardial infarction, ischaemia-driven revascularisation "
                "or stent thrombosis at 48 h. Secondary TRIPLE composite: all-cause death, "
                "myocardial infarction or ischaemia-driven revascularisation at 48 h."),
            "estimate_quoted": (
                "primary composite OR 0.81 (0.71 to 0.91), p = 0.0007; secondary triple "
                "composite OR 0.81 (0.71 to 0.92), p = 0.0014; stent thrombosis OR 0.59 "
                "(0.43 to 0.80)"),
            "comparable_to_ours": True,
            "agreement": (
                "DISAGREES. Their triple composite is OR 0.81 (0.71 to 0.92) on THREE "
                "trials; this object's corrected three-component composite is 0.9646 "
                "(0.8132 to 1.1442) on TWO. THE PUBLISHED INTERVAL EXCLUDES NO DIFFERENCE "
                "AND OURS DOES NOT -- opposite conclusions, not a rounding gap. The k "
                "difference is stated first because a dropped trial is the likeliest "
                "cause."),
        }],
        "THE_FINDING_OF_THIS_COMPARISON_%s" % STAMP: (
            "A MATERIAL DISAGREEMENT, AND IT IS NOT A CLASS-76 INSTANCE. Class 76 is about "
            "the published work choosing a better-defined target; here it chose the SAME "
            "target and got a different answer with MORE data. Steg 2013 pooled all three "
            "CHAMPION trials at patient level to OR 0.81 (0.71 to 0.92) on the triple "
            "composite; this object pools TWO to 0.9646 (0.8132 to 1.1442). One interval "
            "excludes no difference and the other does not. SEPARATELY, THIS OBJECT'S "
            "DECLARED PRIMARY OUTCOME CARRIES NO POOLED ESTIMATE AT ALL despite k = 3. "
            "Which trial is absent from the three-component pool, and whether 0.9646 "
            "should stand, is a content decision and is not made here."),
    }

    atomic_write.merge_not_overwrite(obj, "published_comparison", pc, STAMP)
    obj.setdefault("display_change_announced", []).append({
        "date": TODAY,
        "change": "published comparison added with a denominator (P46 limb 3)",
        "values_moved": "NONE",
        "what_changed": (
            "99 matched / 99 retrieved / 99 read / 1 appraised / 0 lost. Steg 2013 (PMID "
            "24011551), a prespecified patient-level pool of ALL THREE CHAMPION trials, "
            "reports OR 0.81 (0.71-0.92) on the triple composite against this object's "
            "0.9646 (0.8132-1.1442) on k=2. The intervals disagree on whether no "
            "difference is excluded."),
        "why": "The limb was ABSENT: no denominator and no stated reason.",
    })

    os.makedirs(os.path.dirname(SCREEN), exist_ok=True)
    print("cangrelor-pci: 99 matched / 99 retrieved / 99 read / 1 appraised / 0 lost")
    print("  Steg 2013 PMID 24011551  OR 0.81 (0.71-0.92) k=3  vs ours %s (%s-%s) k=2"
          % (ours.get("point"), ours.get("ci_low"), ours.get("ci_high")))
    print("  -> DISAGREES. Predicted 'not class-76' HELD; predicted 'likely to agree' WRONG.")
    if dry:
        print("DRY RUN -- pass --apply to write")
        return
    atomic_write.write_json(SCREEN, {
        "executed_utc": TODAY,
        "source": "PubMed E-utilities esearch + esummary",
        "query_as_executed": QUERY,
        "matched": 99, "retrieved": 99, "read": 99,
        "flagged_by_title": 66, "appraised": ["24011551"],
        "not_returned_by_the_tool": 0,
        "_honesty": ("66 records were flagged by title. ONE was appraised against its "
                     "abstract; the other 65 were NOT READ."),
    }, indent=1)
    atomic_write.write_json(OBJ, obj, indent=1)
    print("wrote %s" % OBJ)


if __name__ == "__main__":
    main()
