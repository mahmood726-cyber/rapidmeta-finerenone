r"""Summary-of-Findings counts: participants and studies, PER OUTCOME.

WHERE THE NUMBERS COME FROM, AND WHY IT MATTERS
    From the SAME CELLS THE EFFECT COMES FROM:

        inputs.trials[].by_outcome.<OUTCOME>.control.{events,n}
        inputs.trials[].by_outcome.<OUTCOME>.treatment.{events,n}

    n_participants = sum of BOTH arms' n over the trials contributing THAT
                     outcome
    n_studies      = how many trials that is

    Cochrane Handbook ch. 14 asks for the participants CONTRIBUTING TO THAT
    OUTCOME, not everything the page mentions. A page-wide identifier count
    answers a different question and would be larger -- ARNI's page carries
    93 distinct NCT ids and zero per-arm cells, so an id-based count there
    would report 93 studies for an outcome that has none.

THE FAILURE THIS REFUSES: A PARTIAL DENOMINATOR
    If five trials claim to contribute an outcome and three carry cells,
    summing the three gives a participant total SMALLER than the pool it
    describes -- and it renders, and it looks right. That is worse than a
    declared absence, because nothing downstream can tell it apart from a
    correct total.

    So every outcome is given a state:

      COMPLETE    every trial with a by_outcome entry for this outcome
                  carries both arms' events and n. Counts are emitted.
      INCOMPLETE  some do and some do not. NO counts are emitted; the two
                  numbers are named instead -- how many carry cells, out of
                  how many claim to contribute.
      ABSENT      no trial carries cells for this outcome. Nothing to sum.

    A count is emitted ONLY for COMPLETE. The other two states carry no
    number at all, by design.

CROSS-CHECK AGAINST THE OBJECT'S OWN k
    The outcome stores its own k. Where n_studies and k disagree the row
    says so rather than preferring either: a disagreement is a finding about
    the object, not something for this script to resolve silently.
"""
from __future__ import annotations
import argparse
import glob
import json
import os
import sys
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from absolute_effects import _dicts, _file_kind  # noqa: E402

STORE = os.path.join(ROOT, "ssot", "*", "*.json")


def arm_ok(block):
    """Both arms present with integer events and n."""
    if isinstance(block, dict) is False:
        return False
    c, t = block.get("control"), block.get("treatment")
    for arm in (c, t):
        if isinstance(arm, dict) is False:
            return False
        for key in ("events", "n"):
            v = arm.get(key)
            if isinstance(v, int) is False or isinstance(v, bool):
                return False
    return True


def counts_for(obj, outcome_name):
    """Return an OrderedDict describing this outcome's SoF counts."""
    inputs = obj.get("inputs")
    trials = inputs.get("trials") if isinstance(inputs, dict) else None
    claiming, complete, participants, per_trial = 0, 0, 0, []
    for t in _dicts(trials):
        bo = t.get("by_outcome")
        entry = bo.get(outcome_name) if isinstance(bo, dict) else None
        if isinstance(entry, dict) is False:
            continue
        claiming += 1                      # this trial claims the outcome
        if arm_ok(entry):
            complete += 1
            n = entry["control"]["n"] + entry["treatment"]["n"]
            participants += n
            per_trial.append(OrderedDict([
                ("trial", t.get("id") or t.get("nct") or "?"),
                ("control_n", entry["control"]["n"]),
                ("treatment_n", entry["treatment"]["n"]),
                ("participants", n)]))
    row = OrderedDict(outcome=outcome_name,
                      trials_claiming_this_outcome=claiming,
                      trials_carrying_both_arms=complete)
    if claiming == 0 or complete == 0:
        row["state"] = "ABSENT"
        row["note"] = ("no trial carries both arms' events and n for this "
                       "outcome, so there is nothing to sum. No count is "
                       "emitted.")
        return row
    if complete != claiming:
        row["state"] = "INCOMPLETE"
        row["note"] = ("%d of %d contributing trials carry both arms. Summing "
                       "only those would give a participant total SMALLER "
                       "than the pool it describes, which renders and looks "
                       "right. No count is emitted."
                       % (complete, claiming))
        return row
    row["state"] = "COMPLETE"
    row["n_participants"] = participants
    row["n_studies"] = complete
    row["per_trial"] = per_trial
    row["basis"] = ("both arms' n summed over the trials contributing this "
                    "outcome, from inputs.trials[].by_outcome.%s.{control,"
                    "treatment}.n -- the same cells the effect comes from"
                    % outcome_name)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-out", default=None)
    ap.add_argument("--only", nargs="*", default=[],
                    help="limit to these topic slugs")
    a = ap.parse_args()

    rows = []
    for path in sorted(glob.glob(STORE)):
        kind, obj = _file_kind(path)
        if kind != "live_with_outcomes":
            continue
        topic = os.path.basename(os.path.dirname(path))
        if a.only and topic not in a.only:
            continue
        bo = obj["results"]["by_outcome"]
        for name, entry in bo.items():
            if isinstance(entry, dict) is False:
                continue
            r = counts_for(obj, name)
            r["topic"] = topic
            k = entry.get("k")
            r["k_recorded_by_the_object"] = k
            if r["state"] == "COMPLETE" and isinstance(k, int) and k != r["n_studies"]:
                r["k_disagreement"] = (
                    "the object records k=%d but %d trials carry cells for "
                    "this outcome. Reported as a disagreement, not resolved "
                    "here." % (k, r["n_studies"]))
            rows.append(r)

    c = Counter(r["state"] for r in rows)
    print("SUMMARY-OF-FINDINGS COUNTS, per outcome")
    for k in ("COMPLETE", "INCOMPLETE", "ABSENT"):
        print("  %-12s %d" % (k, c.get(k, 0)))
    print("  identity: %d == %d outcome entries : %s"
          % (sum(c.values()), len(rows),
             "HOLDS" if sum(c.values()) == len(rows) else "FAILS"))
    print("")
    print("COMPLETE rows -- these carry counts")
    print("  %-34s %-26s %12s %8s" % ("topic", "outcome", "participants",
                                      "studies"))
    for r in rows:
        if r["state"] != "COMPLETE":
            continue
        flag = "  <- k disagrees" if "k_disagreement" in r else ""
        print("  %-34s %-26s %12d %8d%s"
              % (r["topic"][:34], r["outcome"][:26], r["n_participants"],
                 r["n_studies"], flag))
    print("")
    inc = [r for r in rows if r["state"] == "INCOMPLETE"]
    print("INCOMPLETE rows -- NAMED, and deliberately carrying NO count")
    for r in inc:
        print("  %-34s %-26s %d of %d contributors carry both arms"
              % (r["topic"][:34], r["outcome"][:26],
                 r["trials_carrying_both_arms"],
                 r["trials_claiming_this_outcome"]))
    if inc == []:
        print("  none")
    if a.json_out:
        json.dump(rows, open(a.json_out, "w", encoding="utf-8"), indent=1,
                  ensure_ascii=False)
        print("\nwrote %s" % a.json_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
