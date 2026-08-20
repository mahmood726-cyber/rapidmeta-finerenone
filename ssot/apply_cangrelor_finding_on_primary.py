"""cangrelor-pci-review: put the finding where it RENDERS, and correct what it says.

TWO THINGS WERE WRONG WITH MY FIRST ATTEMPT AND BOTH ARE RECORDED RATHER THAN PATCHED.

1. IT WAS ATTACHED TO A BLOCK THE MANUSCRIPT NEVER RENDERS. `corrected_composite_3component`
   is NOT DECLARED in this object's `outcomes`, so the projector skips it: measured, ZERO
   projection paragraphs carry 0.9646. The finding existed for us and not for the reader --
   registry class 65, committed while fixing class 65. Declaring the outcome would make it
   render and is a CONTENT change the builder does not make, so the finding moves to the
   `primary` block, which is declared and does render.

2. THE PREMISE WAS WRONG. I reported that a reader meets 0.96 "with no indication that a
   larger prespecified analysis found 0.81". THE PAGE ALREADY SAYS 0.81. Its withdrawal
   note reads: "The card published OR 0.81 (0.71 to 0.91), which EXCLUDES it. The page
   reported a significant benefit where the trials' own primary outcome does not support
   it." The disagreement was disclosed; what was missing was WHOSE 0.81 it is.

AND THAT IS THE ACTUAL FINDING, WHICH IS SHARPER THAN THE ONE I WENT LOOKING FOR.

    THE OBJECT TREATS 0.81 (0.71 TO 0.91) AS THE WITHDRAWN CARD'S ERROR.
    STEG ET AL., LANCET 2013, PMID 24011551 -- A PRESPECIFIED PATIENT-LEVEL POOLED ANALYSIS
    OF ALL THREE CHAMPION TRIALS, 24,910 PATIENTS -- REPORTS THE PRIMARY COMPOSITE AS
    OR 0.81 (0.71 TO 0.91).

    THE SAME NUMBER, TO THE SECOND DECIMAL, WITH THE SAME INTERVAL.

So the withdrawn card's headline value APPEARS TO HAVE BEEN CORRECT, and what was wrong
with it was its PROVENANCE: the object records that the card's own stored numerators came
from all-cause mortality while its denominators came from the primary composite, on all
three trials. A right answer standing on counts that do not produce it.

    THAT IS A DIFFERENT DEFECT FROM THE ONE THE WITHDRAWAL NAMES, AND IT POINTS THE OTHER
    WAY. The withdrawal says the page claimed a benefit the trials do not support. The
    literature says the benefit is real and the page simply could not show its work.

NOTHING IS RESOLVED HERE AND NO STORED NUMBER IS CHANGED. Whether the withdrawal note
should be restated is a content decision, and it is exactly the kind that must not be made
by the process that discovered it.
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
    byo = (obj.get("results") or {}).get("by_outcome") or {}
    blk = byo.get("primary")
    if not isinstance(blk, dict):
        sys.exit("REFUSED: no `primary` block on this object.")
    declared = [d.get("id") for d in (obj.get("outcomes") or []) if isinstance(d, dict)]
    if "primary" not in declared:
        sys.exit("REFUSED: `primary` is not declared in `outcomes`, so this would not "
                 "render either. Declared: %r" % declared)

    blk["POOL_FINDINGS_%s" % STAMP] = {
        "a_the_withdrawn_value_matches_a_published_patient_level_analysis": (
            "THE 0.81 THIS PAGE RECORDS AS THE WITHDRAWN CARD'S FIGURE IS ALSO THE "
            "PUBLISHED ONE. Steg et al., Lancet 2013 (PMID 24011551) -- a PRESPECIFIED "
            "pooled analysis of PATIENT-LEVEL data from all three CHAMPION trials, 24,910 "
            "patients -- reports the primary composite at OR 0.81 (0.71 to 0.91). The "
            "withdrawal note on this outcome records that the card published OR 0.81 (0.71 "
            "to 0.91). THE SAME VALUE AND THE SAME INTERVAL."),
        "b_what_that_changes_and_what_it_does_not": (
            "IT DOES NOT UNDO THE WITHDRAWAL. This object establishes that the card's own "
            "stored numerators were ALL-CAUSE MORTALITY counts set against the primary "
            "composite's denominators, on all three trials, and that is a real data "
            "defect. WHAT IT CHANGES IS THE READING: the card's headline value appears to "
            "have been RIGHT while the counts beneath it could not produce it. A correct "
            "number standing on the wrong arithmetic is a PROVENANCE failure, not an "
            "accuracy one, and the withdrawal note currently reads as though the benefit "
            "itself were unsupported."),
        "c_what_this_object_can_and_cannot_pool": (
            "From published aggregates this review can pool only CHAMPION-PCI and "
            "CHAMPION-PLATFORM on the three-component composite, because CHAMPION PHOENIX "
            "(NCT01156571) REGISTERS A FOUR-COMPONENT composite adding stent thrombosis -- "
            "its counts are recorded here, 257/5470 against 322/5469, so the exclusion is "
            "checkable. Steg et al. had patient-level data and could rebuild the "
            "three-component quantity for PHOENIX; THAT IS NOT RECOVERABLE FROM "
            "AGGREGATES. The two-trial pool is 0.965 (0.813 to 1.14) and CROSSES NO "
            "DIFFERENCE where theirs does not."),
        "d_which_a_reader_should_prefer_and_what_is_unresolved": (
            "PREFER THE PUBLISHED ANALYSIS. Three trials at patient level, prespecified, "
            "beats two trials of aggregate counts. UNRESOLVED, AND NOT DECIDED HERE: "
            "whether this outcome's withdrawal note should be restated now that the "
            "withdrawn figure is corroborated by the literature. That is a content "
            "decision about a published number and belongs to the author."),
    }

    obj.setdefault("display_change_announced", []).append({
        "date": TODAY,
        "change": ("the published patient-level comparison now renders on the PRIMARY "
                   "outcome, where the withdrawal note a reader actually sees lives"),
        "values_moved": "NONE",
        "what_changed": (
            "Steg 2013 reports the primary composite at OR 0.81 (0.71-0.91) across all "
            "three CHAMPION trials at patient level -- the same value this object records "
            "as the withdrawn card's figure."),
        "why": ("The finding was first attached to `corrected_composite_3component`, which "
                "is NOT declared in `outcomes` and therefore never renders: 0 projection "
                "paragraphs carried it. A finding on a block the reader never sees is the "
                "defect it was written to fix."),
    })

    print("cangrelor: POOL_FINDINGS attached to `primary` (declared, and it renders)")
    print("  FINDING: the withdrawn card's 0.81 (0.71-0.91) EQUALS Steg 2013's primary")
    print("  composite across all three trials at patient level. Same value, same interval.")
    if dry:
        print("DRY RUN -- pass --apply to write")
        return
    atomic_write.write_json(OBJ, obj, indent=1)
    print("wrote %s" % OBJ)


if __name__ == "__main__":
    main()
