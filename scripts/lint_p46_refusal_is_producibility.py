#!/usr/bin/env python3
"""A P46 REFUSAL MUST BE ABOUT PRODUCIBILITY. A provenance note is not a refusal.

THE SHAPE THIS ENFORCES, and it is a new one. 34 objects carry:

    absent_from_source.rob2   "No risk-of-bias assessment was recoverable from the page."
    absent_from_source.grade  "No certainty rating was recoverable from the page."

Every one of those sentences is TRUE. Each is a statement about PROVENANCE -- what the
published page this object was converted from happened to contain. **It is about the wrong
thing.** Whether a risk-of-bias assessment CAN BE MADE is a fact about the trials, and those
objects hold their registrations in `inputs.trials`; RoB 2 per result is assessed from the
registrations, not from the source page, which is exactly what the unit does on `iv-iron-hf`
where a domain that cannot be judged is recorded NO_INFORMATION.

    A TRUE SENTENCE ANSWERING A QUESTION NOBODY ASKED, SITTING WHERE THE ANSWER TO THE REAL
    QUESTION SHOULD BE, IS WORSE THAN A FALSE ONE, BECAUSE IT SURVIVES SCRUTINY.

THE TEST IS STRUCTURAL, NOT A KEYWORD MATCH. Keyword rules over clinical prose are
known-broken here (P14) and a rule that fired on the word "recoverable" would be one. The
test instead is:

    A REASON TRUE OF **THIS** TOPIC CANNOT BE BYTE-IDENTICAL ACROSS MANY TOPICS.

Sharing is the evidence of templating, and it is what made these visible in the first place:
identical text on 34 objects. A refusal that names what was reached on this topic, what was
found insufficient, and what would have to be obtained, cannot collide with another topic's.

SCOPE. Only topics that PUBLISH A POOLED ESTIMATE are judged. A topic with no estimate has no
published number for a missing assessment to qualify, and is reported as OUT OF SCOPE rather
than as passing -- a topic with nothing to judge and a topic with something unjudged must not
look identical in a count.

MODE. Reporting by default. `--gate` exits non-zero when the number of templated refusals
RISES ABOVE THE RECORDED BASELINE, which is the ratchet this repo uses: the existing 34 are
the work item, and blocking every commit on them would only get the gate deleted.
"""
import argparse
import collections
import glob
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# MEASURED by running this script. Re-derive with:
#     python scripts/lint_p46_refusal_is_producibility.py
# and take the TEMPLATED count. Never type it.
#
# THIS CONSTANT HAS NOW BEEN WRONG TWICE, IN OPPOSITE WAYS, WITHIN AN HOUR -- which is the
# whole of registry class 37 demonstrated on itself:
#
#   136  typed from memory; never true of anything
#    19  measured, and correct FOR THE LINT AS IT THEN WAS -- it read reasons only from
#        `absent_from_source`
#    52  measured after the lint was widened to read an artefact's OWN block, where three
#        topics turned out to carry full refusals the narrow version had scored as SILENT
#
# THE JUMP FROM 19 TO 52 IS NOT 33 NEW TEMPLATES. Not one object changed. The INSTRUMENT got
# better at finding the reasons that were already there, and a baseline is measured against
# an instrument, not against the world. So a baseline must be re-derived whenever the thing
# that produces it changes -- otherwise the ratchet fires on its own improvement and the
# obvious fix is to delete the gate.
#
# It remains a BACKLOG, not a permission: it may fall and must not rise.
BASELINE_TEMPLATED = 50

ARTEFACTS = ("risk_of_bias", "grade", "published_comparison", "verbatim_output")


def has_artefact(obj, which):
    bo = ((obj.get("results") or {}).get("by_outcome") or {})
    pooled = {k for k, v in bo.items()
              if isinstance(v, dict) and (v.get("pooled") or {}).get("point") is not None}
    if which == "risk_of_bias":
        rob = obj.get("risk_of_bias") or {}
        return bool(rob.get("by_outcome") or rob.get("by_result"))
    if which == "grade":
        gb = (obj.get("grade") or {}).get("by_outcome") or {}
        return bool(pooled & set(gb)) if pooled else bool(gb)
    if which == "published_comparison":
        checks = (obj.get("published_comparison") or {}).get("checks")
        return isinstance(checks, list) and len(checks) > 0
    if which == "verbatim_output":
        return any(((v or {}).get("r_output") or {}).get("verbatim") for v in bo.values())
    raise ValueError(which)


# Fields an artefact's OWN block uses to carry a refusal. Found by reading the objects, not
# assumed: sglt2-hf's published_comparison states its state, why the denominator is absent,
# what is blocking it, and what was deliberately NOT done instead -- which is a complete P46
# refusal and a better one than most.
REASON_FIELDS = ("denominator_reason", "blocked_on", "explicitly_not_done", "state",
                 "reason", "why", "_why", "what_would_change_it", "access_limitation")

BLOCK_FOR = {"risk_of_bias": "risk_of_bias", "grade": "grade",
             "published_comparison": "published_comparison", "verbatim_output": None}


def candidate_reasons(obj, which):
    """Every string this object offers as the reason that artefact is absent.

    IT LOOKED IN ONE PLACE AND REPORTED SILENCE FROM THE OTHER. The first version read only
    `absent_from_source`, so three topics whose `published_comparison` block carries a full
    refusal -- state, denominator_reason, blocked_on, and what was explicitly not done and
    why -- were counted as offering NO REASON AT ALL. The instrument was looking in one place
    and calling the rest of the object silent, which is the same shape as the probe that
    reported iv-iron-hf holds no quoted model output because it read one level too high.
    """
    out = []
    afs = obj.get("absent_from_source") or {}
    keys = {"risk_of_bias": ("rob2", "risk_of_bias", "rob"),
            "grade": ("grade", "certainty"),
            "published_comparison": ("published_comparison", "comparison"),
            "verbatim_output": ("r_output", "analysis", "statistics")}[which]
    for k in keys:
        v = afs.get(k)
        if isinstance(v, str) and v.strip():
            out.append(("absent_from_source.%s" % k, v.strip()))
    blk_name = BLOCK_FOR.get(which)
    blk = obj.get(blk_name) if blk_name else None
    if isinstance(blk, dict):
        for k in REASON_FIELDS:
            v = blk.get(k)
            if isinstance(v, str) and len(v.strip()) > 25:
                out.append(("%s.%s" % (blk_name, k), v.strip()))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true")
    args = ap.parse_args()
    os.chdir(REPO)

    objs = {}
    for op in sorted(glob.glob("ssot/*/*.json")):
        name = os.path.basename(op)[:-5]
        if os.path.basename(os.path.dirname(op)) != name:
            continue
        try:
            o = json.load(open(op, encoding="utf-8"))
        except Exception:
            continue
        if isinstance(o, dict) and "title" in o:
            objs[name] = o

    # how many DISTINCT topics use each reason string -- sharing is the evidence
    users = collections.defaultdict(set)
    for name, o in objs.items():
        for which in ARTEFACTS:
            for _path, text in candidate_reasons(o, which):
                users[text].add(name)

    in_scope, out_scope = [], []
    templated, specific, silent = [], [], []
    for name, o in sorted(objs.items()):
        bo = ((o.get("results") or {}).get("by_outcome") or {})
        pooled = any(isinstance(v, dict) and (v.get("pooled") or {}).get("point") is not None
                     for v in bo.values())
        if not pooled:
            out_scope.append(name)
            continue
        in_scope.append(name)
        for which in ARTEFACTS:
            if has_artefact(o, which):
                continue
            reasons = candidate_reasons(o, which)
            if not reasons:
                silent.append((name, which))
                continue
            for path, text in reasons:
                if len(users[text]) > 1:
                    templated.append((name, which, path, text, len(users[text])))
                else:
                    specific.append((name, which, path, text))

    print("objects                       : %d" % len(objs))
    print("IN SCOPE (publish an estimate): %d" % len(in_scope))
    print("OUT OF SCOPE (no estimate)    : %d  <-- NOT passing. A topic with nothing to judge"
          % len(out_scope))
    print("                                    and one with something unjudged are different.")
    print()
    print("MISSING ARTEFACT, reason offered but TEMPLATED (shared with other topics): %d"
          % len(templated))
    seen = set()
    for name, which, path, text, n in templated:
        if text in seen:
            continue
        seen.add(text)
        print("    %-26s %-20s used by %d topics" % (path, which, n))
        print("        %r" % text[:110])
    print()
    print("MISSING ARTEFACT, reason SPECIFIC to its topic (discharges the clause): %d"
          % len(specific))
    for name, which, path, text in specific[:8]:
        print("    %-28s %-20s %r" % (name[:28], which, text[:70]))
    print()
    print("MISSING ARTEFACT, NO reason offered at all: %d" % len(silent))
    by_art = collections.Counter(w for _n, w in silent)
    for w, n in sorted(by_art.items()):
        print("    %-22s %d topic(s)" % (w, n))
    print()
    print("A P46 refusal must name WHAT WAS REACHED and found insufficient, and WHAT WOULD")
    print("HAVE TO BE OBTAINED. 'Not recoverable from the source page' is a note about where")
    print("somebody looked first; it refuses nothing.")

    if args.gate:
        if len(templated) > BASELINE_TEMPLATED:
            print()
            print("REFUSED: templated P46 refusals rose to %d, above the recorded baseline of "
                  "%d. A provenance note may not be added where a refusal belongs."
                  % (len(templated), BASELINE_TEMPLATED))
            return 1
        print()
        print("GATE OK: %d templated refusal(s), baseline %d. The baseline is a BACKLOG, not "
              "a permission -- it may fall and must not rise."
              % (len(templated), BASELINE_TEMPLATED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
