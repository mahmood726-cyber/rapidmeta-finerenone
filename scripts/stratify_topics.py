"""What KIND is each topic? Enumerate the kinds before counting anything.

WHY THIS EXISTS. Three denominators were wrong tonight for one reason: the kinds of item
in the population were never enumerated, so a count of "topics" silently included things
that are not topics.

The worst instance nearly reached an anchored artefact. Fourteen directories under ssot/
are RETIRED TOMBSTONES -- topics merged into other topics on 2026-08-19, authorised, and
deliberately preserved rather than deleted. They were sitting in a work list of questions
to author. Authoring a review question for a retired topic and anchoring a protocol over
it would have fabricated a review that was deliberately retired, and reversed an
authorised decision, in a form that is timestamped and third-party attested.

What stopped it was the corpus protecting itself: each tombstone carries a field named
`a_tombstone_is_not_an_absence`, whose value explains that an auditor must be able to SEE
a merge rather than infer it from a gap. It was named as a SENTENCE rather than a flag,
which is why it was read rather than skipped.

THE STRATA ARE DERIVED FROM MACHINE-READABLE FIELDS, not from names or guesses:
    state == RETIRED            a tombstone. NEVER author a question for one.
    build_mode == verdict-only  built to record a verdict, not a pool. A review question
                                exists to define a search and a pool; these were never
                                going to pool, so they do not need one -- but they must
                                DECLARE what they are rather than leave a reader to infer
                                it from silence.
    everything else             a live review, which needs a question if it lacks one.

AND ONE SPLIT THAT MATTERS INSIDE verdict-only: a verdict-only topic that knows some
trials exist is a different thing from one that knows none. Those are named separately
rather than folded together.

WHAT A FULL RUN DOES NOT ESTABLISH
    - NOT that the live topics are correct, complete, or searched.
    - NOT that verdict-only is the right outcome for the topics carrying it. It reports
      the field; whether the verdict was justified is not a question a field can answer.
    - NOT that the strata are exhaustive of every distinction that matters. It reports
      the kind-bearing fields it found, and prints every distinct value so a reader can
      see what it had to work with.
"""
import io
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls  # noqa: E402

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")
NCT = re.compile(r"NCT\d{8}")

RETIRED = "RETIRED TOMBSTONE"
VERDICT_KNOWS_TRIALS = "VERDICT-ONLY, knows trials exist"
VERDICT_KNOWS_NONE = "VERDICT-ONLY, knows of no trials"
LIVE = "LIVE REVIEW"


def stratify():
    rows = []
    state_vals, mode_vals = Counter(), Counter()
    for topic in sorted(os.listdir(SSOT)):
        d = os.path.join(SSOT, topic)
        f = os.path.join(d, topic + ".json")
        if os.path.isdir(d) and os.path.isfile(f):
            obj = json.load(open(f, encoding="utf-8"))
            state = obj["state"] if "state" in obj else None
            mode = obj["build_mode"] if "build_mode" in obj else None
            state_vals[str(state)] += 1
            mode_vals[str(mode)] += 1
            trials = ((obj.get("inputs") or {}).get("trials") or [])
            ncts_anywhere = sorted(set(NCT.findall(json.dumps(obj))))
            if str(state).upper() == "RETIRED":
                kind = RETIRED
            elif str(mode) == "verdict-only":
                kind = VERDICT_KNOWS_TRIALS if ncts_anywhere else VERDICT_KNOWS_NONE
            else:
                kind = LIVE
            rows.append({"topic": topic, "kind": kind, "state": state,
                         "build_mode": mode, "n_trials": len(trials),
                         "n_ncts_anywhere": len(ncts_anywhere),
                         "absorbed_by": obj.get("absorbed_by")})
    return rows, state_vals, mode_vals


def controls(rows):
    """Known answers, established independently of this code.

    POSITIVE -- bamlanivimab-outp is a retired tombstone. Established by reading its own
    `absorbed_by` and `a_tombstone_is_not_an_absence` fields, and by Mahmood's recorded
    authorisation of 2026-08-19, not by this classifier.

    NEGATIVE -- finerenone-cv must NOT be classified as retired. Over-classifying as
    retired is this instrument's dangerous direction: a live review wrongly marked a
    tombstone would be silently dropped from the authoring list and never searched, and
    nothing downstream would report the omission.
    """
    idx = {r["topic"]: r for r in rows}
    pos = idx.get("bamlanivimab-outp", {}).get("kind")
    neg = idx.get("finerenone-cv", {}).get("kind")
    require_controls(
        "stratify_topics",
        positive=("bamlanivimab-outp, retired and absorbed by bamlanivimab-covid "
                  "(established from its own tombstone fields, not by this code)",
                  pos, RETIRED),
        negative=("finerenone-cv classified as a retired tombstone", neg, RETIRED))


if __name__ == "__main__":
    rows, state_vals, mode_vals = stratify()
    controls(rows)

    print("KIND-BEARING FIELD VALUES, enumerated in full before any stratum is quoted\n")
    print("  `state`:")
    for k, v in state_vals.most_common():
        print("    %4d  %s" % (v, k))
    print("  `build_mode`:")
    for k, v in mode_vals.most_common():
        print("    %4d  %s" % (v, k))

    by = Counter(r["kind"] for r in rows)
    n = len(rows)
    print("\n" + "=" * 70)
    print("STRATA, DENOMINATOR %d DIRECTORIES UNDER ssot/\n" % n)
    for k in (RETIRED, VERDICT_KNOWS_TRIALS, VERDICT_KNOWS_NONE, LIVE):
        print("  %4d  %s" % (by[k], k))
    print("  ----")
    print("  %4d  total (sums: %s)" % (sum(by.values()),
                                       "yes" if sum(by.values()) == n else "NO"))

    print("\n  RETIRED -- never author a question for these:")
    for r in rows:
        if r["kind"] == RETIRED:
            print("      %-40s -> %s" % (r["topic"], r["absorbed_by"] or "<not stated>"))

    print("\n  VERDICT-ONLY that KNOWS TRIALS EXIST -- named separately because a")
    print("  verdict-only topic aware of trials is not the same as one aware of none:")
    for r in rows:
        if r["kind"] == VERDICT_KNOWS_TRIALS:
            print("      %-40s inputs.trials=%d  NCTs elsewhere=%d"
                  % (r["topic"], r["n_trials"], r["n_ncts_anywhere"]))

    print("\n  VERDICT-ONLY that KNOWS OF NO TRIALS:")
    for r in rows:
        if r["kind"] == VERDICT_KNOWS_NONE:
            print("      %-40s" % r["topic"])

    out = os.path.join(os.path.dirname(REPO), "strata.json")
    json.dump(rows, open(out, "w", encoding="utf-8"), indent=1)
    print("\nwrote " + out)

    # ------------------------------------------------------------------------------
    # EXIT CONTRACT. A file that returns a verdict must be able to refuse.
    #   0  every directory classified into exactly one stratum and the strata sum
    #   1  a topic could not be classified, or the strata do not sum to the population
    #   2  no directories found -- a NON-VERDICT, not a pass
    # ------------------------------------------------------------------------------
    if not rows:
        print("\nNO TOPIC STORES FOUND -- non-verdict, not a pass.")
        raise SystemExit(2)
    unclassified = [r for r in rows if r["kind"] not in
                    (RETIRED, VERDICT_KNOWS_TRIALS, VERDICT_KNOWS_NONE, LIVE)]
    if unclassified or sum(by.values()) != n:
        print("\nREFUSED: %d unclassified, strata sum %d against a population of %d."
              % (len(unclassified), sum(by.values()), n))
        raise SystemExit(1)
    print("\nAll %d directories classified into exactly one stratum." % n)
    raise SystemExit(0)
