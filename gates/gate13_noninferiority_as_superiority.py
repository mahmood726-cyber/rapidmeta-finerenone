# no-control-exempt: this gate DOES match store fields, so a known-negative control is
# mandatory and is supplied below from the corpus itself.
"""GATE 13 -- a non-inferiority trial pooled and read as a superiority test (class S3).

LINEAGE. Register A0d, found by an external reviewer reading a page: "A NON-INFERIORITY TRIAL
POOLED AS A SUPERIORITY TEST -- unadjusted RR read against 1, where the trial prespecified an
adjusted RD with a -10pp NI margin." Ranked #2 of the fourteen undefended classes on harm,
because it is one of only two that can make a reader act in the WRONG DIRECTION: "not
meaningfully worse" is rendered as "better", and the margin exists precisely to make that
reading wrong.

DIRECTION OF ERROR. This gate accuses our own pages. That is the direction our detectors are
measured to fail in (standing orders section 8, three independent measurements). So the
known-negative control is not optional here and the false-positive rate prints beside the
count on every run.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402
import noninferiority_pooling as NIP                                        # noqa: E402

# The REAL motivating case, named. If the traversal never reaches it, this gate is VACUOUS --
# three unrelated filters once hid an instrument's own motivating case and nothing said so.
MOTIVATING_TOPIC = "tigecycline-ciai"
MOTIVATING_OUTCOME = "cure_toc_me"


def main(argv):
    gate = H.Gate("13 NON-INFERIORITY POOLED AS SUPERIORITY",
                  "a trial registered as non-inferiority, pooled and read against the null",
                  needs_coverage=True)
    gate.requires_control()
    repo = H.repo_root()

    try:
        ni_set, ni_path = NIP.registrations(repo)
    except Exception as exc:
        gate.broken("the non-inferiority registry could not be read (%r). An empty registry "
                    "would make every page pass, which is the failure mode this refuses." % exc)
        gate.kinds({"unreadable": 1})
        return gate.report()
    if not ni_set:
        gate.broken("the non-inferiority registry is EMPTY. A join against nothing finds "
                    "nothing and would report a clean corpus.")

    paths, path_kinds = H.topic_objects(repo)
    gate.expect_case("S3-real", "%s/%s -- the register A0d case"
                     % (MOTIVATING_TOPIC, MOTIVATING_OUTCOME))

    total = {"outcome_blocks": 0, "blocks_with_per_trial": 0, "ni_rows_seen": 0}
    trials_seen, trials_ni = set(), set()
    findings, negatives, fp = [], 0, 0

    for p in paths:
        topic = H.topic_id(p)
        try:
            obj = H.load(p)
        except Exception as exc:
            gate.broken("%s did not parse (%r)" % (topic, exc))
            continue
        for t in (obj.get("inputs") or {}).get("trials") or []:
            if isinstance(t, dict) and t.get("nct"):
                trials_seen.add(t["nct"])
                if t["nct"] in ni_set:
                    trials_ni.add(t["nct"])

        rows, seen = NIP.scan(obj, ni_set, topic)
        for k in total:
            total[k] += seen[k]

        # KNOWN-NEGATIVE CONTROL, from the corpus: every pooled block holding NO
        # NI registration must not fire. These are real blocks we did not write for this test.
        by_outcome = ((obj.get("results") or {}).get("by_outcome") or {})
        flagged = {r["outcome"] for r in rows}
        for oid, block in by_outcome.items():
            if not isinstance(block, dict) or not (block.get("per_trial") or []):
                continue
            if any(r.get("nct") in ni_set for r in block["per_trial"] if isinstance(r, dict)):
                continue
            negatives += 1
            if oid in flagged:
                fp += 1

        for r in rows:
            if topic == MOTIVATING_TOPIC and r["outcome"] == MOTIVATING_OUTCOME:
                gate.saw("S3-real")
            findings.append(r)
            gate.finding("S3-NONINFERIORITY-READ-AS-SUPERIORITY",
                         "%s/%s: %s" % (topic, r["outcome"], r["detail"]),
                         numerator=len(r["ni_trials"]), denominator=r["rows"])

    gate.control(negatives, fp)
    gate.kinds({
        "topic objects examined": len(paths),
        "  (other json under ssot/<t>/, not examined)": path_kinds.get("other json under ssot/<t>/", 0),
        "outcome blocks": total["outcome_blocks"],
        "  of those, pooling any rows at all": total["blocks_with_per_trial"],
        "  of those, holding a known NI registration": len({(f["topic"], f["outcome"]) for f in findings}) + fp,
        "distinct trials in inputs": len(trials_seen),
        "  recognisable as non-inferiority (the registry's reach)": len(trials_ni),
    })
    gate.coverage(len(trials_ni), len(trials_seen), "trials whose non-inferiority status is knowable",
                  blind_to=("non-inferiority trials absent from %s (%d registrations). The corpus "
                            "demonstrably holds such trials: cryptococcal-meningitis records "
                            "non_inferiority_margin_pp for ACTA and AMBITION and NEITHER is in "
                            "the list, so this gate cannot see them."
                            % (os.path.relpath(ni_path, repo).replace(os.sep, "/"), len(ni_set))))
    gate.note("The join is on an EXTERNAL registry, not on inputs.trials[].design: that field "
              "is populated on 93 of 407 trials and is polluted -- its values include "
              "COMPLETED, TERMINATED and UNKNOWN, which are recruitment status, not design.")
    gate.note("A block recording a margin is NOT accused. cryptococcal-meningitis is the "
              "corpus's own model answer: it holds each trial's own estimand with its "
              "-10pp margin beside the pooled reading.")
    return gate.report(denominator="%d outcome blocks over %d topic objects"
                                   % (total["outcome_blocks"], len(paths)))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
