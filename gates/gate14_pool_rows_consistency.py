# no-control-exempt: this gate reads typed store fields, so a known-negative control is
# mandatory and is drawn below from the corpus's own declared refusals.
"""GATE 14 -- a published result needs rows behind it, or a declared refusal (class S1).

Q4 WAS REPORTED HERE AND NO LONGER IS. `count_matches_rows` won that class on a cross-run of
both lanes' plant sets (7/7 positives against 1/7); the declared-refusal exclusion this side
contributed was merged into it. Reporting Q4 from two modules would double-count the class and
is exactly the merge-by-file failure the ruling forbids.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402
import pool_rows_consistency as PRC                                         # noqa: E402

# NO CORPUS NAMED POSITIVE: S1's corpus baseline is a MEASURED ZERO -- every one of the 96
# row-less blocks declares a refusal. Registering a corpus case that does not exist would make
# this gate VACUOUS on every run, which is worse than saying so. The proof that the leg can
# fire at all is the real-file plant in plant_pool_rows, and the fixture pair S1a/S1b in the
# registry; both are exercised on every build.


def main(argv):
    gate = H.Gate("14 A RESULT NEEDS ROWS",
                  "a block publishing a result with no rows and no declared refusal",
                  needs_coverage=True)
    gate.requires_control()
    repo = H.repo_root()
    paths, path_kinds = H.topic_objects(repo)

    total = {"outcome_blocks": 0, "blocks_stating_k": 0, "blocks_with_rows": 0,
             "declared_refusals": 0}
    n_s1 = 0
    negatives = fp = 0

    for p in paths:
        topic = H.topic_id(p)
        try:
            obj = H.load(p)
        except Exception as exc:
            gate.broken("%s did not parse (%r)" % (topic, exc))
            continue
        rows, seen = PRC.scan(obj, topic)
        for k in total:
            total[k] += seen[k]
        flagged = {r["outcome"] for r in rows}

        # KNOWN-NEGATIVE CONTROL: the corpus's declared refusals. A refusal states k and
        # carries no rows ON PURPOSE. It is the model answer for this class and must never
        # be accused -- a detector that fires here would push authors to delete the refusal.
        for oid, block in ((obj.get("results") or {}).get("by_outcome") or {}).items():
            if not isinstance(block, dict):
                continue
            refused, _ = PRC.is_refusal(block)
            if refused and not (block.get("per_trial") or []):
                negatives += 1
                if oid in flagged:
                    fp += 1

        for r in rows:
            n_s1 += 1
            gate.finding("S1-RESULT-PUBLISHED-WITH-NO-ROWS",
                             "%s/%s: %s" % (topic, r["outcome"], r["detail"]),
                             numerator=0, denominator=r["k"] if r["k"] else "?")

    gate.control(negatives, fp)
    gate.kinds({
        "topic objects examined": len(paths),
        "  (other json under ssot/<t>/, not examined)":
            path_kinds.get("other json under ssot/<t>/", 0),
        "outcome blocks": total["outcome_blocks"],
        "  stating a k": total["blocks_stating_k"],
        "  carrying at least one row": total["blocks_with_rows"],
        "  DECLARED REFUSALS (a third kind, neither data nor defect)":
            total["declared_refusals"],
        "S1 findings": n_s1,
    })
    gate.coverage(total["outcome_blocks"], total["outcome_blocks"],
                  "outcome blocks in the store",
                  blind_to=("nothing in the STORE layer -- every block is parsed. This gate is "
                            "blind to the SERVED layer entirely: a page may render an outcome "
                            "the store refuses, and no leg of this gate reads a rendered page. "
                            "S1's zero is a statement about 175 store blocks and about NO "
                            "pages."))
    gate.note("S1 baseline is a MEASURED zero, not an unrun check: plant_pool_rows.py plants "
              "a result with no rows into a real object and this gate reports it, then the "
              "object is restored byte-identical.")
    return gate.report(denominator="%d outcome blocks over %d topic objects"
                                   % (total["outcome_blocks"], len(paths)))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
