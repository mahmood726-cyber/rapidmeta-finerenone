#!/usr/bin/env python3
"""Repair attr-cm-review's r_output reason: the STATE was right, the REASON was false.

The block declared:

    state       ABSENT_AND_THAT_IS_THE_FINDING          <- CORRECT. Nothing was pooled.
    _why_absent "k=1. No meta-analysis was performed."  <- FALSE. The object declares k=2.

Same shape as alirocumab-lipid's, caught this time by scripts/lint_block_contradicts_object.py
IN THE VERY NEXT TOPIC BUILT -- which is the detector earning its place rather than being
argued for.

The refusal stands and is correct. What changes is its justification, which is what a reader
checks a verdict against.
"""
import io
import json
import os

OBJ = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "ssot", "attr-cm-review", "attr-cm-review.json")


def main():
    with io.open(OBJ, encoding="utf-8") as fh:
        obj = json.load(fh)
    b = obj["results"]["by_outcome"]["primary"]
    old = (b.get("r_output") or {}).get("_why_absent")
    b["r_output"] = {
        "state": "ABSENT_AND_THAT_IS_THE_FINDING",
        "_why_absent": (
            "k=2 AND NOTHING WAS POOLED -- and the reason is the estimand, not the evidence "
            "base. Both included trials register a HIERARCHICAL primary analysed by win ratio, "
            "and the two hierarchies are not the same hierarchy: ATTR-ACT (NCT01994889) "
            "combines all-cause mortality with CV-related hospitalisation frequency; "
            "ATTRibute-CM (NCT03860935) adds NT-proBNP change and 6-minute-walk change. A win "
            "ratio's estimand IS its hierarchy and cannot be recovered from a 2x2 table, so "
            "there is no model call to quote because NO MODEL WAS RUN, not because one failed. "
            "This is the correct state for two trials that do not share an estimand."),
        "k_at_time_of_writing": 2,
        "corrected_2026_08_19": {
            "previous_why_absent": old,
            "why_it_was_wrong": (
                "It said k=1 on an object that declares k=2. The STATE was correct -- nothing "
                "was pooled -- but the REASON was false, and a reason is what a reader checks "
                "the verdict against. P6 therefore refused with a justification that was "
                "fiction, exactly as it did on alirocumab-lipid."),
            "found_by": "scripts/lint_block_contradicts_object.py, on the next topic built "
                        "after the detector was written",
        },
    }
    with io.open(OBJ, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(obj, indent=1, ensure_ascii=False) + "\n")
    print("r_output reason corrected: k=1 -> k=2, with the estimand reason stated")


if __name__ == "__main__":
    main()
