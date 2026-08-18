"""A row marked for exclusion must be HONOURED or the build must REFUSE.

THE FOUNDING CASE, and it is the sharpest defect found in this corpus. `finerenone-review`
carried a per-trial row with `trial_id: "NULLED:NCT01874431"` and `point: 0.385` -- a
continuous albuminuria ratio inside a pool of event odds. Re-derived:

    k=4 INCLUDING it   0.8470425219   <-- MATCHES THE PUBLISHED VALUE TO TEN DECIMAL PLACES
    k=3 dropping it    0.8478182774

SOMEONE MADE AN EXCLUSION DECISION AND IT NEVER TOOK EFFECT. That is worse than a defaulted
field: a default is at least silent about its intent. THIS ONE RECORDS THE INTENT AND
CONTRADICTS IT -- the object says "excluded" and the arithmetic says otherwise, and the
page published the arithmetic.

Same family as every seam defect this week -- a marker the consumer does not read is not an
exclusion, exactly as a field the consumer cannot find is not provenance and a shape it
cannot read is not data. THE INTENT LIVES IN ONE PLACE AND THE BEHAVIOUR IN ANOTHER.

WHY MECHANICAL AND NOT PROSE. One row corpus-wide today. But the marker convention will be
used again -- it is the obvious thing to reach for when excluding a trial without deleting
its record -- and NOTHING ENFORCES IT. Prose has failed on every class-3 rule this week;
the four mechanical guards have each held.

THE RULE: if any per_trial row carries a marker prefix, that row must be ABSENT from the
computation. This checks the only thing it can check statically -- that a marked row is not
counted in `k` -- and REFUSES when it is. Honouring it properly is the pooling step's job;
this makes the failure loud instead of silent.

NOT A SUBSTITUTE FOR DELETION. A marked row is kept deliberately: the record of an
exclusion is evidence. What must not survive is its CONTRIBUTION.
"""
from __future__ import annotations
import io
import json
import os
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKERS = ("NULLED:", "EXCLUDED:", "WITHDRAWN:", "REMOVED:", "VOID:", "SUPERSEDED:")


def main() -> int:
    bad, seen = [], 0
    ss = os.path.join(REPO, "ssot")
    for d in sorted(os.listdir(ss)):
        f = os.path.join(ss, d, d + ".json")
        if not os.path.exists(f):
            continue
        try:
            o = json.load(io.open(f, encoding="utf-8"))
        except Exception:
            continue
        for name, blk in ((o.get("results") or {}).get("by_outcome") or {}).items():
            if not isinstance(blk, dict):
                continue
            rows = [t for t in (blk.get("per_trial") or []) if isinstance(t, dict)]
            marked = [t for t in rows
                      if any(str(t.get("trial_id", "")).startswith(m) for m in MARKERS)]
            if not marked:
                continue
            seen += len(marked)
            k = blk.get("k")
            unmarked = len(rows) - len(marked)
            if isinstance(k, int) and k != unmarked:
                bad.append((d, name, k, unmarked, len(marked),
                            [t.get("trial_id") for t in marked]))

    print("marked rows found: %d" % seen)
    print("BLOCKS WHERE A MARKED ROW IS STILL COUNTED: %d" % len(bad))
    for d, name, k, un, nm, ids in bad:
        print()
        print("  %s :: %s" % (d, name))
        print("     k=%d but only %d unmarked rows -- %d marked row(s) are in the count"
              % (k, un, nm))
        print("     %s" % ", ".join(str(i) for i in ids))
    if bad:
        print()
        print("REFUSED. A MARKER THE CONSUMER DOES NOT READ IS NOT AN EXCLUSION. The row is")
        print("kept deliberately -- an exclusion record is evidence -- but its CONTRIBUTION")
        print("must not survive. Either drop it from the computation or remove the marker")
        print("and say why it belongs.")
        return 1
    print("every marked row is excluded from its block's count.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
