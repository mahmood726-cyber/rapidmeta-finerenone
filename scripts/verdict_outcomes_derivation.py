"""Derive `outcomes` for VERDICT-ONLY objects from their own registered primaries.

WHY THESE SIX WERE REFUSED. `schema_patch_for_generator.py` derives an `outcomes` entry
from a pooled block's recorded outcome name. A verdict-only object has no pooled outcome:
it records WHY NO POOL EXISTS, not what was pooled. The patcher refused rather than
authoring a generic name, which was correct -- a string written to satisfy a generator
would have rendered on a published page as though it came from the registrations.

THE LEGITIMATE SOURCE IS ALREADY ON THE OBJECT. Each verdict-only object carries
`inputs.trials[].registered_primaries` -- the primary outcome measures READ FROM EACH
REGISTRATION on a stated date. An `outcomes` entry naming "each trial's own registered
primary outcome" is a DERIVATION FROM THAT, not an authoring.

DERIVED IS NOT ENOUGH; IT MUST BE TRACEABLE. "Derived from recorded content" is what makes
it legitimate. "Here is exactly what it was derived from" is what makes it CHECKABLE, and
those are different properties. So the derived entry names the registrations it came from,
per trial, with the read date -- a reader can go from the rendered page to
`inputs.trials[].registered_primaries` and from there to the registry itself.

AND IT REFUSES, for the same reason the patcher did. Some closures were reached on IDENTITY
or COMPARATOR grounds before endpoints were read, so `registered_primaries` may be absent.
Where it is, this refuses rather than falling back to a generic phrase. The refusal list is
a legitimate output; it has been twice today.
"""
from __future__ import annotations
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from rebuild_guard import guard_write  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def derive(path):
    o = json.load(io.open(path, encoding="utf-8"))
    if "outcomes" in o:
        return None, "already has outcomes"
    trials = ((o.get("inputs") or {}).get("trials") or [])
    if not trials:
        return None, "REFUSED: no inputs.trials to derive from"

    per = []
    for t in trials:
        prims = t.get("registered_primaries")
        if prims:
            per.append({"nct": t.get("nct") or t.get("trial_id"),
                        "registered_primaries": prims,
                        "read_utc": t.get("read_utc"),
                        "source_url": t.get("source_url")})
    if not per:
        return None, ("REFUSED: no trial carries registered_primaries. This closure was "
                      "reached before endpoints were read, so there is nothing recorded "
                      "to derive an outcome from. Authoring one would invent content.")

    bo = (o.get("results") or {}).get("by_outcome") or {}
    oid = "primary" if "primary" in bo else (list(bo)[0] if bo else "primary")
    o["outcomes"] = [{
        "id": oid, "type": "primary",
        "name": "each trial's own registered primary outcome",
        "definition": ("This topic publishes no pooled estimate. Each contributing trial "
                       "registered its own primary outcome, and those are recorded per "
                       "trial rather than reduced to a common quantity -- which is the "
                       "reason no pool is displayed."),
        "definition_note": ("DERIVED from inputs.trials[].registered_primaries, which were "
                            "read from each registration on the dates recorded there. Not "
                            "authored: every phrase above describes the structure of the "
                            "record, and the substance is the per-trial list below."),
        "derived_from": {
            "field": "inputs.trials[].registered_primaries",
            "trials": per,
            "how_to_check": ("Each entry names its registration and the date it was read. "
                             "A reader can go from this page to that NCT on "
                             "ClinicalTrials.gov and compare. THE DERIVATION IS TRACEABLE, "
                             "not merely sourced."),
        },
    }]
    o["verdict_outcomes_derivation_2026_08_18"] = (
        "The generator requires `outcomes`; this object had none because it records why no "
        "pool exists rather than what was pooled. The entry was DERIVED from this object's "
        "own registered_primaries and NAMES WHAT IT WAS DERIVED FROM. Objects whose "
        "closures predate endpoint reading were REFUSED rather than given a generic name.")
    guard_write(path, json.dumps(o, ensure_ascii=False, indent=1))
    return len(per), None


def main() -> int:
    ok, refused = 0, []
    for t in sys.argv[1:]:
        p = os.path.join(REPO, "ssot", t, t + ".json")
        if not os.path.exists(p):
            refused.append((t, "no object"))
            continue
        n, err = derive(p)
        if err:
            refused.append((t, err))
        else:
            ok += 1
            print("  %-44s derived from %d trial(s)" % (t[:43], n))
    print()
    print("derived: %d   refused: %d" % (ok, len(refused)))
    for t, why in refused:
        print("   REFUSED %-38s %s" % (t[:37], why[:74]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
