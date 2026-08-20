"""Pages publishing a pooled estimate for an outcome whose own object declines to stand behind it.

THE SHAPE, AND IT IS DIFFERENT FROM EVERY OTHER DEFECT FOUND TONIGHT. Every other one was an
instrument or a projector saying something WRONG. This one is a CORRECT OBJECT, CORRECT
FIELDS, A CORRECT REFUSAL -- AND NO CONSUMER OBLIGED TO READ THEM.

`sglt2-mace-cvot-review` is the worked case. Its outcome `name` begins "Multiple
trial-declared outcomes:" and concatenates FOUR different registered titles separated by
pipes. `estimand_established` is FALSE. `estimand_id_means` says "not recorded on the page
this object was extracted from". `pool_uniformity.effect_measure` says "NOT ESTABLISHED".
Every one of those fields is honest and correct, and the page published 0.9074 (0.831 to
0.9908) anyway.

    A DECLARATION NOBODY IS REQUIRED TO CONSULT IS DOCUMENTATION, AND DOCUMENTATION HAS
    FAILED AS A CONTROL EVERY TIME THIS PROJECT HAS TESTED IT.

That is the same law arriving in the DATA layer rather than in the code layer. The heredoc
rule was breached nine times by an author who had read it; `estimand_established: false` is
breached by a renderer that was never told to ask.

WHAT THIS COUNTS. For every outcome block that publishes a pooled point (not null, not
withdrawn), the state of `estimand_established`:

    TRUE   established: every contributing trial read and shown to measure the same quantity
    FALSE  CHECKED AND FAILED -- the object states the trials do NOT measure one quantity
    NULL   never checked. `estimand_established_means` on these objects says explicitly that
           an ABSENT assertion and a NEGATIVE one are different states and null is not a pass

FALSE is the sharp population: the object has looked and said no, and the page publishes.
NULL is larger and softer -- nobody asked. Reported separately and never summed, because
summing them would make an unasked question look like a failed one.

THIS FILE RECOMMENDS AND DOES NOT ACT. Whether the remedy is a build-time refusal or a
disclosure on the page is a published-number decision. The count is what that decision
should be made on.
"""
import io
import json
import os
import sys
import glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls


def published_blocks(obj):
    out = []
    for name, blk in ((obj.get("results") or {}).get("by_outcome") or {}).items():
        if not isinstance(blk, dict):
            continue
        p = blk.get("pooled")
        if not isinstance(p, dict):
            continue
        if p.get("point") is None or p.get("withdrawn"):
            continue
        out.append((name, blk, p))
    return out


def main():
    # CONSTRUCTED CONTROLS. The positive is the sglt2-mace shape; the negative is the same
    # block with the flag TRUE, which must not be counted.
    bad = {"results": {"by_outcome": {"primary": {
        "pooled": {"point": 0.9074}, "estimand_established": False}}}}
    good = {"results": {"by_outcome": {"primary": {
        "pooled": {"point": 0.9074}, "estimand_established": True}}}}
    require_controls(
        "audit_published_over_unestablished_estimand",
        positive=("a published point over estimand_established FALSE -- the sglt2-mace shape",
                  any(b.get("estimand_established") is False
                      for _n, b, _p in published_blocks(bad)), True),
        negative=("the same block with the flag TRUE",
                  any(b.get("estimand_established") is False
                      for _n, b, _p in published_blocks(good)), True))

    false_hits, null_hits, true_hits, absent = [], [], [], []
    topics = 0
    for path in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        topic = os.path.basename(os.path.dirname(path))
        if os.path.basename(path) != topic + ".json":
            continue
        try:
            obj = json.load(io.open(path, encoding="utf-8"))
        except Exception:
            continue
        topics += 1
        for name, blk, p in published_blocks(obj):
            flag = blk.get("estimand_established", "__missing__")
            row = (topic, name, p.get("point"), p.get("measure"),
                   str(blk.get("estimand_id_means") or "")[:70])
            if flag is False:
                false_hits.append(row)
            elif flag is None:
                null_hits.append(row)
            elif flag == "__missing__":
                absent.append(row)
            else:
                true_hits.append(row)

    total = len(false_hits) + len(null_hits) + len(true_hits) + len(absent)
    print("")
    print("OBJECTS READ: %d.  POOLED ESTIMATES PUBLISHED (point set, not withdrawn): %d"
          % (topics, total))
    print("")
    print("    estimand_established TRUE      %3d   established and published" % len(true_hits))
    print("    estimand_established FALSE     %3d   THE OBJECT LOOKED AND SAID NO"
          % len(false_hits))
    print("    estimand_established NULL      %3d   never checked" % len(null_hits))
    print("    the field is ABSENT            %3d   the question was never posed" % len(absent))
    print("")
    print("NEVER SUMMED. A question nobody asked and a question answered NO are different")
    print("states, and the objects' own `estimand_established_means` says so.")

    print("")
    print("PUBLISHED OVER A FALSE FLAG -- the object has looked and said the trials do NOT")
    print("measure one quantity, and a reader meets the number anyway:")
    for topic, name, point, measure, means in false_hits:
        print("    %-40s %-28s %s %s" % (topic, name, measure or "?", point))
        if means:
            print("        estimand_id_means: %s" % means)
    if not false_hits:
        print("    none")

    print("")
    print("PUBLISHED OVER A NULL FLAG -- nobody asked (%d):" % len(null_hits))
    for topic, name, point, measure, _m in null_hits[:20]:
        print("    %-40s %-28s %s %s" % (topic, name, measure or "?", point))
    if len(null_hits) > 20:
        print("    ... +%d more" % (len(null_hits) - 20))

    print("")
    print("RECOMMENDATION, NOT AN ACTION. Whether the remedy is a build-time REFUSAL or a")
    print("DISCLOSURE beside the number is a published-number decision and belongs to")
    print("Mahmood. The count above is what that decision should be made on.")


if __name__ == "__main__":
    main()
