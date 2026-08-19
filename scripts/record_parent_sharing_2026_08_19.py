"""RECORD THE SHARING P22 CAUGHT: the PARENT object still holds both of this review's trials.

The sharing block named the two SIBLING reviews -- which do not exist yet as objects -- and not
`ablation-af-review`, the parent this review was split out of, which DOES exist and still holds
all four of its original trials.

    P22 FIRED ON A REAL RELATIONSHIP AND ONE THAT WOULD HAVE BEEN EASY TO LEAVE OUT, because
    the parent is on its way to being retired and it is tempting to record the world as it is
    about to be rather than as it is.

A superseded object is still an object. While `ablation-af-review` exists, any corpus-level
count that sums per-topic k counts CASTLE-AF and RAFT-AF twice -- once here and once there --
and that is exactly the arithmetic P22 exists to keep honest.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPIC = "ablation-af-heart-failure"
OBJ = os.path.join(REPO, "ssot", TOPIC, TOPIC + ".json")

PARENT_NOTE = (
    "`ablation-af-review`, THE PARENT THIS REVIEW WAS SPLIT OUT OF. It still exists and still "
    "holds all four of its original trials, so while it does, a corpus-level count that sums "
    "per-topic k counts this trial twice. It is pending retirement once all three child "
    "reviews are built -- and 'pending retirement' is not 'gone'. Recorded because P22 "
    "computed it, not because it was remembered.")


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    with io.open(OBJ, encoding="utf-8") as fh:
        obj = json.load(fh)
    shared = obj["shared_with_other_topics"]["shared"]
    for nct in ("NCT00643188", "NCT01420393"):
        entry = shared[nct]
        if "ablation-af-review" in entry["also_in"]:
            print("%s already records the parent" % nct)
            continue
        entry["also_in"] = sorted(set(entry["also_in"]) | {"ablation-af-review"})
        entry["parent_object_note"] = PARENT_NOTE
        print("%s -> also_in now %s" % (nct, entry["also_in"]))
    obj["shared_with_other_topics"]["siblings_not_yet_built"] = (
        "TWO OF THE THREE TOPICS NAMED IN `also_in` DO NOT EXIST YET AS OBJECTS -- "
        "ablation-af-medical-therapy and early-rhythm-control-af are declared in "
        "DECIDED-ablation-af-review-2026-08-19.md and are not built. They are listed anyway, "
        "because the sharing is a property of the DECISION rather than of the build order, and "
        "because a list that grows as objects appear would let a reader mistake build order "
        "for evidence. P22's computed check sees only the objects that exist, so it currently "
        "confirms the parent and cannot yet confirm these two.")
    with io.open(OBJ, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, indent=1, ensure_ascii=True))
    print("wrote %s" % OBJ)
    return 0


if __name__ == "__main__":
    sys.exit(main())
