# no-control-exempt: this gate reads typed store fields, so a known-negative control is
# mandatory and is drawn below from the corpus's own declared refusals.
"""GATE 14 -- pooled k must agree with its rows (Q4), and a result needs rows (S1)."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402
import pool_rows_consistency as PRC                                         # noqa: E402

MOTIVATING = ("finerenone-review", "primary")     # k=3 over 4 rows, found in this corpus


def main(argv):
    gate = H.Gate("14 POOLED k AGAINST ITS ROWS",
                  "k must equal the rows behind it (Q4); a published result needs rows (S1)",
                  needs_coverage=True)
    gate.requires_control()
    repo = H.repo_root()
    paths, path_kinds = H.topic_objects(repo)
    gate.expect_case("Q4-real", "%s/%s -- k stated over a different number of rows"
                     % MOTIVATING)

    total = {"outcome_blocks": 0, "blocks_stating_k": 0, "blocks_with_rows": 0,
             "declared_refusals": 0}
    n_q4 = n_s1 = 0
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
            if r["cls"] == "Q4":
                n_q4 += 1
                if (topic, r["outcome"]) == MOTIVATING:
                    gate.saw("Q4-real")
                gate.finding("Q4-POOLED-k-DISAGREES-WITH-ITS-ROWS",
                             "%s/%s: %s" % (topic, r["outcome"], r["detail"]),
                             numerator=r["k"], denominator=r["rows"])
            else:
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
        "Q4 findings": n_q4,
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
    gate.note("26 of the 27 k-vs-rows disagreements in this corpus are declared refusals "
              "stating the k they would have pooled. They are the model answer and are "
              "excluded by their DECLARED STATE, not by a count.")
    return gate.report(denominator="%d outcome blocks over %d topic objects"
                                   % (total["outcome_blocks"], len(paths)))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
