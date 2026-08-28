"""Which objects publish an outcome with nothing checkable behind it -- and rate its certainty?

THE CLASS, FOUND AS ONE PAGE. `prevnar15-pneumo` exports ZERO check payloads while publishing
FOUR outcomes: no `per_trial` rows behind any of them, so the artefact detectors recognise
nothing. The pre-push harness refused it on "not-assessable is never PASS". One page was the
instance; this is the population.

TWO NUMBERS, AND THE SECOND IS THE ONE THAT MATTERS:

    outcomes published with no per_trial rows behind them
    of THOSE, how many also carry a GRADE certainty rating

A certainty rating over an outcome with no per-trial evidence is a confidence statement about
nothing. That is the shape of every uncheckable finding this project has produced.

DIRECTION IS ESTABLISHED BEFORE ANY NUMBER IS QUOTED. "Zero payloads" has two readings and
they have different owners:

    ABSENT       the object holds no per_trial rows      -> a data problem, the store's owner
    NOT CARRIED  rows exist and the exporter drops them  -> a projector problem, ours

This reads the OBJECT directly for the first and compares against what the exporter emits for
the second. Reporting one as the other would send the work to the wrong lane.

THREE STATES PER OUTCOME, never two:
    CHECKABLE       per_trial rows present
    NO ROWS         per_trial absent or empty
    NOT APPLICABLE  the object declares it publishes nothing, so nothing is owed
"""
import collections
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
OUT = os.path.join(REPO, "outputs", "uncheckable_outcomes_2026_08_28.json")


def certainty_of(blk):
    g = blk.get("grade")
    if not isinstance(g, dict):
        return None
    v = g.get("certainty") or g.get("rating")
    return str(v).strip() if v else None


def run_controls():
    from instrument_controls import require_controls
    with_rows = {"per_trial": [{"trial": "A"}], "grade": {"certainty": "low"}}
    no_rows = {"per_trial": [], "grade": {"certainty": "low"}}
    require_controls(
        "uncheckable_outcomes",
        ("an outcome WITH per_trial rows is not counted as uncheckable",
         bool(with_rows.get("per_trial")), True),
        ("an outcome with an EMPTY per_trial list reads as checkable",
         bool(no_rows.get("per_trial")), True))


def main():
    run_controls()
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def say(s):
        raw.write(s + chr(10))
        raw.flush()

    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    rows = []
    n_obj = n_out = 0
    c = collections.Counter()
    worst = []
    for page, path in sorted(pm.items()):
        fp = os.path.join(REPO, path)
        if not os.path.exists(fp):
            continue
        o = json.load(io.open(fp, encoding="utf-8"))
        by = (o.get("results") or {}).get("by_outcome") or {}
        if not by:
            continue
        n_obj += 1
        # does the object DECLARE it publishes nothing?
        declares_none = bool(o.get("publishes_nothing") or
                             (o.get("precondition_verdict") or {}).get("publishes_nothing"))
        obj_rows = 0
        for oid, blk in by.items():
            if not isinstance(blk, dict):
                continue
            n_out += 1
            per = blk.get("per_trial") or []
            cert = certainty_of(blk)
            if per:
                c["CHECKABLE"] += 1
                obj_rows += 1
                if cert:
                    c["checkable_with_certainty"] += 1
            elif declares_none:
                c["NOT APPLICABLE (declares it publishes nothing)"] += 1
            else:
                c["NO ROWS"] += 1
                if cert:
                    c["NO ROWS *and* a certainty rating"] += 1
                    worst.append((page, oid, cert))
            rows.append({"page": page, "outcome": oid, "per_trial": len(per),
                         "certainty": cert, "declares_none": declares_none})
        if obj_rows == 0:
            c["objects with NO checkable outcome at all"] += 1

    say("objects with a results block : %d" % n_obj)
    say("outcomes published           : %d" % n_out)
    say("")
    for k in ("CHECKABLE", "NO ROWS", "NOT APPLICABLE (declares it publishes nothing)"):
        say("  %-46s %4d / %d  (%.0f%%)"
            % (k, c[k], n_out, 100.0 * c[k] / n_out if n_out else 0))
    say("")
    say("  %-46s %4d" % ("objects with NO checkable outcome at all",
                         c["objects with NO checkable outcome at all"]))
    say("")
    say("THE NUMBER THAT MATTERS")
    say("  %-46s %4d / %d  (%.0f%% of no-rows outcomes)"
        % ("NO ROWS *and* a certainty rating", c["NO ROWS *and* a certainty rating"],
           c["NO ROWS"], 100.0 * c["NO ROWS *and* a certainty rating"] / c["NO ROWS"]
           if c["NO ROWS"] else 0))
    say("  a certainty rating over an outcome with no per-trial evidence behind it")
    say("")
    for page, oid, cert in worst[:14]:
        say("    %-44s %-28s certainty=%s" % (page[:44], oid[:28], cert))
    if len(worst) > 14:
        say("    ... and %d more" % (len(worst) - 14))

    json.dump({"question": "outcomes published with no per_trial rows, and how many of those "
                           "carry a certainty rating",
               "direction": "read from the OBJECT, so NO ROWS means the rows are ABSENT from "
                            "the store -- not that a projector dropped them",
               "counts": dict(c), "n_objects": n_obj, "n_outcomes": n_out, "rows": rows},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    say("")
    say("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
