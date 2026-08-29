# no-control-exempt: this gate reads typed store fields and arithmetic, so a known-negative
# control is mandatory and is drawn below from every row it could have accused and did not.
"""GATE 16 -- the arms and the stored effect must point the same way (class A2)."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402
import arm_role_inversion as ARI                                            # noqa: E402


def main(argv):
    gate = H.Gate("16 ARM ROLE INVERSION",
                  "a stored effect whose direction contradicts the object's own arm counts",
                  needs_coverage=True)
    gate.requires_control()
    repo = H.repo_root()
    paths, path_kinds = H.topic_objects(repo)

    # NAMED POSITIVE. There is no known A2 instance in this corpus, so the case this gate was
    # built to find is SYNTHETIC and is exercised here, in the run, rather than in a transcript
    # somebody has to trust. If it is ever not reached, this gate is VACUOUS and says so.
    gate.expect_case("synthetic-inversion",
                     "a trial whose arms imply protection while the stored effect claims harm")
    probe = {"inputs": {"trials": [{"nct": "NCT-PROBE", "arms": [
        {"role": "treatment", "events": 10, "participants": 200},
        {"role": "control", "events": 40, "participants": 200}]}]},
        "results": {"by_outcome": {"primary": {"per_trial": [
            {"nct": "NCT-PROBE", "point": 4.0, "ci_low": 2.1, "ci_high": 7.6,
             "measure": "RR"}]}}}}
    probe_rows, probe_seen = ARI.scan(probe, "<probe>")
    if not probe_seen["rows_with_a_directional_claim"]:
        gate.broken("the probe never reached the directional test; the join or the count "
                    "parser has drifted and a zero here would be vacuous")
    elif len(probe_rows) == 1:
        gate.saw("synthetic-inversion")
    else:
        gate.broken("the probe row was not reported: %r" % (probe_rows,))

    total = {"per_trial_rows": 0, "rows_joined_to_arms": 0, "rows_with_usable_counts": 0,
             "rows_on_a_ratio_measure": 0, "rows_with_a_directional_claim": 0,
             "rows_refused_non_ratio_measure": 0}
    n = 0
    for p in paths:
        topic = H.topic_id(p)
        try:
            obj = H.load(p)
        except Exception as exc:
            gate.broken("%s did not parse (%r)" % (topic, exc))
            continue
        rows, seen = ARI.scan(obj, topic)
        for k in total:
            total[k] += seen[k]
        for r in rows:
            n += 1
            gate.finding("A2-ARM-ROLE-INVERSION",
                         "%s/%s: %s" % (topic, r["outcome"], r["detail"]),
                         numerator=1, denominator=seen["rows_with_a_directional_claim"])

    # KNOWN-NEGATIVE CONTROL: every row that reached the directional test and was NOT accused.
    # These are real stored estimates against real arm counts, none written for this test.
    negatives = total["rows_with_a_directional_claim"] - n
    if negatives > 0:
        gate.control(negatives, 0)
    else:
        gate.broken("no row reached the directional test, so there is no control set and a "
                    "zero would measure nothing")

    gate.kinds({
        "topic objects examined": len(paths),
        "  (other json under ssot/<t>/, not examined)":
            path_kinds.get("other json under ssot/<t>/", 0),
        "per_trial rows": total["per_trial_rows"],
        "  joined to a trial recording arms": total["rows_joined_to_arms"],
        "  whose arms yield a crude ratio": total["rows_with_usable_counts"],
        "  REFUSED -- measure is not a ratio (a difference has a different null)":
            total["rows_refused_non_ratio_measure"],
        "  on a ratio measure": total["rows_on_a_ratio_measure"],
        "  ALSO making a directional claim (own CI excludes the null)":
            total["rows_with_a_directional_claim"],
        "findings": n,
    })
    gate.coverage(total["rows_with_a_directional_claim"], total["per_trial_rows"],
                  "per_trial rows",
                  blind_to=("rows whose trial records no arms, whose arms omit events or "
                            "participants, whose roles do not resolve to exactly one "
                            "treatment and one control, that carry a zero event cell, or "
                            "whose own interval spans the null and so makes no directional "
                            "claim to contradict. An inversion in any of those is invisible "
                            "here and this gate's zero does not cover them."))
    gate.note("The test is a SIGN test against the object's own arm counts. It is deliberately "
              "silent on MAGNITUDE: a stored adjusted hazard ratio may legitimately differ "
              "from a crude count-derived ratio in size, and register A21 forbids substituting "
              "one for the other. Only a DIRECTION contradiction is reported.")
    return gate.report(denominator="%d per_trial rows over %d topic objects"
                                   % (total["per_trial_rows"], len(paths)))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
