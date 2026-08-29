"""S3 -- a non-inferiority trial pooled and read as a superiority test.

THE REAL DEFECT THIS CAME FROM. Register A0d: "A NON-INFERIORITY TRIAL POOLED AS A
SUPERIORITY TEST -- unadjusted RR read against 1, where the trial prespecified an adjusted RD
with a -10pp NI margin." The register adds the part that decides this module's shape:
"We may hold no margin field at all => the corpus CANNOT EXPRESS what those trials concluded."

WHY THE BOUNDARY IS STRUCTURAL AND NOT NUMERIC. There is no threshold here to tune. The
question is whether a typed container -- one `results.by_outcome.<id>` block -- simultaneously
(a) pools a trial that is registered as non-inferiority, (b) states a conclusion read against
the null, and (c) records no margin anywhere inside that same block. The enclosing block IS
the boundary. Nothing to fit to one page.

WHY THE JOIN IS ON A REGISTRY AND NOT ON `design`. `inputs.trials[].design` is populated on
93 of 407 trials AND IS POLLUTED: its observed values include "COMPLETED", "TERMINATED" and
"UNKNOWN", which are recruitment STATUS, not design. A join on that field would measure the
field's adoption and its contamination, not non-inferiority. `out/blind-review/
noninferiority_trials.json` is an external list of 46 registrations -- an answer established
outside this code, which is what a positive control requires.

WHAT THIS CANNOT SEE, STATED RATHER THAN DISCOVERED LATER. Its entire authority is those 46
registrations. A non-inferiority trial absent from that list is invisible here BY
CONSTRUCTION, and the corpus demonstrably contains such trials: `cryptococcal-meningitis`
records `non_inferiority_margin_pp` for ACTA and AMBITION, neither of which the list holds.
That is reach, not coverage, and `coverage_fraction()` publishes it every run.
"""
from __future__ import annotations

import json
import os

MARGIN_TOKENS = ("margin", "noninferior", "non_inferior", "non-inferior")


def registrations(repo):
    """The external NI registry. Returns (set, path). Absence is BROKEN, never an empty pass."""
    p = os.path.join(repo, "out", "blind-review", "noninferiority_trials.json")
    with open(p, "r", encoding="utf-8") as fh:
        return set(json.load(fh)), p


def _walk(x, path=""):
    yield path, x
    if isinstance(x, dict):
        for k, v in x.items():
            for r in _walk(v, path + "." + str(k)):
                yield r
    elif isinstance(x, list):
        for i, v in enumerate(x):
            for r in _walk(v, path + "[" + str(i) + "]"):
                yield r


def margin_recorded(block):
    """Is a non-inferiority margin recorded ANYWHERE inside this outcome block?

    A key whose value is None does NOT count. A field that exists and is empty records
    nothing, and crediting it would convert a missing margin into a satisfied one -- the
    softer-claim substitution the standing orders forbid.
    """
    for _, node in _walk(block):
        if isinstance(node, dict):
            for k, v in node.items():
                lk = k.lower()
                if any(tok in lk for tok in MARGIN_TOKENS) and v is not None:
                    return True, k
    return False, None


def states_a_conclusion(block):
    """Does this block read its pool against the null?

    `favours` naming a side, or a pooled estimate being present, is a conclusion a reader
    takes as a superiority answer. A block that refuses to pool AND names no side states
    nothing and is not accused.
    """
    fav = block.get("favours")
    if isinstance(fav, str) and fav.strip():
        return True, "favours=%r" % fav[:60]
    pooled = block.get("pooled")
    if isinstance(pooled, dict) and pooled:
        return True, "pooled block present"
    return False, None


def scan(obj, ni_set, topic="fixture"):
    """Rows for every outcome block that pools an NI registration and reads it against a null.

    Returns (rows, seen) where `seen` counts what was actually inspected, so a caller can tell
    "looked and found nothing" from "never reached anything".
    """
    rows = []
    seen = {"outcome_blocks": 0, "blocks_with_per_trial": 0, "ni_rows_seen": 0}
    by_outcome = ((obj.get("results") or {}).get("by_outcome") or {})
    for oid, block in by_outcome.items():
        if not isinstance(block, dict):
            continue
        seen["outcome_blocks"] += 1
        per_trial = block.get("per_trial") or []
        if not per_trial:
            continue
        seen["blocks_with_per_trial"] += 1
        ni_here = [r.get("nct") for r in per_trial
                   if isinstance(r, dict) and r.get("nct") in ni_set]
        if not ni_here:
            continue
        seen["ni_rows_seen"] += len(ni_here)
        has_margin, mkey = margin_recorded(block)
        if has_margin:
            continue
        concludes, why = states_a_conclusion(block)
        if not concludes:
            continue
        rows.append({
            "topic": topic, "outcome": oid, "k": block.get("k"),
            "rows": len(per_trial), "ni_trials": ni_here,
            "poolable": block.get("poolable"),
            "conclusion": why,
            "detail": ("outcome %r pools %d non-inferiority registration(s) %s and %s, with no "
                       "margin recorded anywhere in the block. The trial's own question was "
                       "'not worse by more than delta'; the block answers 'better or worse "
                       "than null'." % (oid, len(ni_here), ni_here, why)),
        })
    return rows, seen
