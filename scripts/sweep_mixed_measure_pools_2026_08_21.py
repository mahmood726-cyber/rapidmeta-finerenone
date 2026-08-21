"""Every pool whose contributing entries do not share one measure type.

THE GATE FOUND ONE AND THE GATE ONLY LOOKS AT WHAT IS PUSHED. `malaria-vaccines`'
`exploratory_recurrent_rate` groups a HAZARD RATIO with an INCIDENCE RATE RATIO, and
CHK018_MIXED_POOLING caught it the moment the topic was mapped. Nothing was looking at the
topics already delivered.

A hazard ratio and an incidence rate ratio are not the same quantity. One is a ratio of
instantaneous rates under a proportional-hazards assumption over follow-up; the other is a
ratio of counts per person-time. Averaging them produces a number with no estimand.

THREE GRADES, REPORTED SEPARATELY, because they are not equally wrong:

    MIXED RATIO/DIFFERENCE   a ratio measure pooled with a difference measure. There is no
                             scale on which these are the same quantity.
    MIXED RATIO TYPES        HR with IRR, OR with RR, and so on. Each answers a different
                             question over a different denominator.
    MIXED DIFFERENCE TYPES   MD with SMD, which differ by whether the scale is standardised.

AND WHETHER IT REACHES A READER IS REPORTED BESIDE IT. A mixed pool that displays a pooled
point is a wrong number on a page. One that displays nothing is a defect in the object that a
reader cannot currently meet -- still worth fixing, and not the same severity.
"""
import glob
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RATIO = {"OR", "RR", "HR", "IRR", "RATIO", "RRR", "SHR"}
DIFF = {"MD", "SMD", "RD"}


def measures_in(blk):
    """Every measure type the entries of this pool carry, as the object records them."""
    out = {}
    for t in ((blk or {}).get("per_trial") or []):
        if not isinstance(t, dict):
            continue
        m = t.get("measure") or t.get("effect_measure")
        if isinstance(m, str) and m.strip():
            out.setdefault(m.strip().upper(), []).append(
                str(t.get("trial_id") or t.get("nct") or "?"))
    return out


def grade(kinds):
    r = [k for k in kinds if k in RATIO]
    d = [k for k in kinds if k in DIFF]
    if r and d:
        return "MIXED RATIO/DIFFERENCE"
    if len(r) > 1:
        return "MIXED RATIO TYPES"
    if len(d) > 1:
        return "MIXED DIFFERENCE TYPES"
    return None


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    pools = seen = 0
    found = []
    for path in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        topic = os.path.basename(os.path.dirname(path))
        if os.path.basename(path) != topic + ".json":
            continue
        try:
            obj = json.load(io.open(path, encoding="utf-8"))
        except ValueError:
            continue
        by = (obj.get("results") or {}).get("by_outcome") or {}
        if not isinstance(by, dict) or not by:
            continue
        seen += 1
        for oid, blk in by.items():
            if not isinstance(blk, dict):
                continue
            kinds = measures_in(blk)
            if not kinds:
                continue
            pools += 1
            g = grade(kinds)
            if not g:
                continue
            pt = ((blk.get("pooled") or {}) if isinstance(blk.get("pooled"), dict) else {})
            found.append({
                "topic": topic, "outcome": oid, "grade": g,
                "measures": {k: v for k, v in sorted(kinds.items())},
                "displays_a_pooled_point": pt.get("point") is not None,
                "pooled_measure_declared": blk.get("measure") or pt.get("measure"),
            })

    # A SWEEP THAT CANNOT FAIL IS NOT A SWEEP. The known answer is the one the gate found.
    known = [f for f in found
             if f["topic"] == "malaria-vaccines" and f["outcome"] == "exploratory_recurrent_rate"]
    if not known:
        sys.exit("PROOF FAILED: the floor case is missing. CHK018_MIXED_POOLING found "
                 "malaria-vaccines/exploratory_recurrent_rate pooling HR with IRR; a sweep "
                 "for mixed-measure pools that does not find it is not reading what the "
                 "gate reads.")

    print("")
    print("POOLS WHOSE ENTRIES DECLARE A MEASURE: %d, across %d topic(s) with results."
          % (pools, seen))
    print("MIXED: %d" % len(found))
    print("")
    reaches = [f for f in found if f["displays_a_pooled_point"]]
    print("REACHING A READER AS A POOLED NUMBER: %d" % len(reaches))
    print("IN THE OBJECT ONLY, NOTHING DISPLAYED:  %d" % (len(found) - len(reaches)))
    print("")
    for f in sorted(found, key=lambda x: (not x["displays_a_pooled_point"], x["topic"])):
        print("%-34s %-28s %s%s"
              % (f["topic"][:34], f["outcome"][:28], f["grade"],
                 "   *** DISPLAYS A POOLED POINT ***" if f["displays_a_pooled_point"] else ""))
        for m, ids in f["measures"].items():
            print("      %-6s %s" % (m, ", ".join(ids[:5])))
        if f["pooled_measure_declared"]:
            print("      pool declares itself: %s" % f["pooled_measure_declared"])
    print("")
    print("FLOOR: the case CHK018_MIXED_POOLING found is in this list, so the sweep reads "
          "what the gate reads.")


if __name__ == "__main__":
    main()
