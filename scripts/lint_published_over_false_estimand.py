"""A NEW pooled estimate published over `estimand_established: false` is refused.

THE PART OF THE RECOMMENDATION THAT NEEDS NO DECISION. Whether the two estimates currently
in this state should be withdrawn, disclosed or left is a published-number decision and
belongs to Mahmood. Whether a THIRD should be able to appear without anyone noticing is not
a decision, and this refuses it.

THE STATE IT GUARDS. `estimand_established: false` means the object HAS CHECKED and found
that the contributing trials do NOT measure one quantity. It is not "unknown" -- null is
unknown, and the objects' own `estimand_established_means` insists on the difference:
"AN ABSENT ASSERTION AND A NEGATIVE ONE ARE DIFFERENT STATES and null is not a pass". So
this gate keys on FALSE ONLY. Keying it on "not TRUE" would refuse 25 of the 34 published
estimates in this corpus, which is an outage rather than a fix, and would refuse them for a
question nobody asked rather than one answered no.

THE TWO KNOWN INSTANCES ARE GRANDFATHERED BY NAME, NOT SILENTLY:

    rosuvastatin-auto-full-review / primary        OR 0.6561
    sglt2-mace-cvot-review / primary               OR 0.9074

Both were REFERRED on 2026-08-20 for exactly this, with the reason written onto the object.
They are in the baseline so that the gate blocks nothing today and catches the third. A
baseline is not a clearance: each of these is a live estimate a reader meets while the
object beside it declines to stand behind it.

THE POSITIVE CONTROL IS CONSTRUCTED, NOT ONE OF THE TWO LIVE PAGES -- registry class 58. A
control that says "the corpus currently contains this defect" stops asserting anything the
day the corpus is clean, and these two are EXPECTED to be fixed.
"""
import io
import json
import os
import sys
import glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls

BASELINE = os.path.join(REPO, "scripts", "baselines",
                        "published_over_false_estimand_baseline.json")


def offenders(obj, topic):
    """-> [(topic, outcome, measure, point)] publishing over a FALSE flag."""
    out = []
    for name, blk in ((obj.get("results") or {}).get("by_outcome") or {}).items():
        if not isinstance(blk, dict):
            continue
        if blk.get("estimand_established") is not False:
            continue                      # NULL and ABSENT are different states
        p = blk.get("pooled")
        if not isinstance(p, dict):
            continue
        if p.get("point") is None or p.get("withdrawn"):
            continue
        out.append((topic, name, p.get("measure"), p.get("point")))
    return out


def scan():
    hits = []
    for path in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        topic = os.path.basename(os.path.dirname(path))
        if os.path.basename(path) != topic + ".json":
            continue
        try:
            obj = json.load(io.open(path, encoding="utf-8"))
        except Exception:
            continue
        hits.extend(offenders(obj, topic))
    return hits


def main():
    gate = "--gate" in sys.argv

    fixture_bad = {"results": {"by_outcome": {"primary": {
        "estimand_established": False,
        "pooled": {"point": 0.77, "measure": "HR"}}}}}
    fixture_null = {"results": {"by_outcome": {"primary": {
        "estimand_established": None,
        "pooled": {"point": 0.77, "measure": "HR"}}}}}
    require_controls(
        "lint_published_over_false_estimand",
        positive=("a constructed block publishing a point over a FALSE flag",
                  bool(offenders(fixture_bad, "fixture")), True),
        negative=("the same block with the flag NULL -- an unasked question, not a "
                  "failed check", bool(offenders(fixture_null, "fixture")), True))

    hits = scan()
    keys = sorted("%s/%s" % (t, n) for t, n, _m, _p in hits)
    print("")
    print("POOLED ESTIMATES PUBLISHED OVER estimand_established FALSE: %d" % len(hits))
    for topic, name, measure, point in sorted(hits):
        print("    %-42s %-24s %s %s" % (topic, name, measure or "?", point))

    if not os.path.exists(BASELINE):
        os.makedirs(os.path.dirname(BASELINE), exist_ok=True)
        json.dump({
            "written": "2026-08-20",
            "NOT_A_CLEARANCE": (
                "Each entry is a LIVE estimate a reader meets while the object beside it "
                "declines to stand behind it. Both were REFERRED on 2026-08-20 with the "
                "reason written onto the object. They are grandfathered BY NAME so the "
                "gate blocks nothing today and catches the third. Whether to withdraw, "
                "disclose or leave them is a published-number decision and is Mahmood's."),
            "grandfathered": keys,
        }, io.open(BASELINE, "w", encoding="utf-8", newline=chr(10)), indent=1,
            ensure_ascii=False)
        print("")
        print("wrote baseline with %d grandfathered instance(s)" % len(keys))
        return 0

    known = set(json.load(io.open(BASELINE, encoding="utf-8")).get("grandfathered") or [])
    new = sorted(set(keys) - known)
    healed = sorted(known - set(keys))
    print("")
    if healed:
        print("%d grandfathered instance(s) are gone -- the estimate was withdrawn, the "
              "flag became true, or the block was removed: %s"
              % (len(healed), ", ".join(healed)))
    if new:
        print("REFUSED: %d NEW pooled estimate(s) published over a FALSE estimand flag:"
              % len(new))
        for k in new:
            print("    %s" % k)
        print("")
        print("`estimand_established: false` means the OBJECT HAS CHECKED and found the")
        print("trials do not measure one quantity. Publishing a pooled point over it puts a")
        print("number in front of a reader that the object itself declines to stand behind.")
        print("Either establish the estimand, or withdraw the pool with its reason, or")
        print("refer it and add it to the baseline with that reason recorded.")
        if gate:
            return 1
    else:
        print("NO NEW INSTANCE. The baseline of %d has not risen." % len(known))
    return 0


if __name__ == "__main__":
    sys.exit(main())
