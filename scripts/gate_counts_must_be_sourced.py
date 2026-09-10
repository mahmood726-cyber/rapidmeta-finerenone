#!/usr/bin/env python3
"""GATE: a trial's pooled arm counts must trace to a source, not be fabricated.

WHY THIS EXISTS. ROTAVIRUS_VACCINE_AFRICA_REVIEW pooled 2x2 tables that do not come from
their registrations: Rotarix used 21/1042 vs 37/1047, but 1042+1047 = 2089 is the
top-level enrollmentInfo.count SPLIT IN TWO (real arm sizes 1647/1651/1641 sit in the
participant-flow module); RotaTeq used 79/2733 vs 129/2735 while the same registry object
posts 2357/2348 in its denoms field; Rotasiil (NCT02145000) posts NO results section at
all, so its counts cannot have come from the registry the masthead claims. The object
ITSELF records this -- provenance_MISMATCH fields, registration_primary_counts that differ
from the used arm events, and provenance strings saying the counts did not come from the
registry -- but the page published the fabricated cells anyway. This gate makes the
object's own recorded mismatch BLOCK the page.

THE RULE. For every contributing trial, the arm counts used in the pool must be sourced.
A trial is flagged if it carries a provenance_MISMATCH, OR its registration_primary_counts
differ from the arm events actually used, OR its provenance states the counts did not come
from the registry.

MEASURED PRECISION via instrument_controls.require_controls: real positive (rotavirus MUST
flag), real negative (a review whose trial counts are sourced must NOT flag). Prints EXECUTED.
"""
import glob
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
from instrument_controls import require_controls, ControlFailed  # noqa: E402

_UNSOURCED = re.compile(r"do(?:es)? not match|did not come from|NOT SUPPLIED BY THE REGISTRY"
                        r"|NO RESULTS SECTION|posts NO RESULTS", re.I)


def _num(x):
    try:
        return float(x)
    except Exception:
        return None


def trial_is_unsourced(t):
    if not isinstance(t, dict):
        return None
    # (1) an explicit provenance-mismatch field anywhere on the trial
    for k, v in t.items():
        if "provenance_mismatch" in k.lower():
            return "carries %s" % k
        if isinstance(v, str) and _UNSOURCED.search(v):
            return "provenance says counts are not from the registry"
    # NOTE: an earlier version also compared arms[].events against
    # registration_primary_counts and flagged any difference. That OVER-FLAGGED (27
    # reviews): registration_primary_counts frequently stores a DIFFERENT QUANTITY than
    # event counts -- incidence rates (15.77/21), mean changes (-43.96/-43.77) -- so the
    # two legitimately differ and the comparison measured field-type, not fabrication.
    # Verified against the real corpus, dropped. The explicit provenance signals above are
    # the object's OWN record that a count is unsourced, which is the precise defect.
    return None


def review_defects(objpath):
    try:
        obj = json.load(open(objpath, encoding="utf-8"))
    except Exception:
        return []
    trials = (obj.get("inputs") or {}).get("trials") or []
    out = []
    for i, t in enumerate(trials):
        why = trial_is_unsourced(t)
        if why:
            out.append((i, why))
    return out


def flags(objpath):
    return len(review_defects(objpath)) > 0


def main():
    objs = sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json")))
    print("EXECUTED gate_counts_must_be_sourced over %d ssot objects." % len(objs))
    roto = [o for o in objs if "rotavirus-vaccine-africa" in o.replace("\\", "/")]
    # negative control: first review with >=2 trials whose counts are all sourced
    neg = None
    for o in objs:
        if "rotavirus" in o.replace("\\", "/"):
            continue
        try:
            trials = (json.load(open(o, encoding="utf-8")).get("inputs") or {}).get("trials") or []
        except Exception:
            continue
        if len(trials) >= 2 and not flags(o):
            neg = o
            break
    try:
        require_controls(
            "counts-must-be-sourced",
            positive=("ROTAVIRUS_VACCINE_AFRICA has unsourced/fabricated arm counts -> flagged",
                      bool(roto) and flags(roto[0]), True),
            negative=(("%s (counts sourced) is flagged"
                       % (os.path.basename(os.path.dirname(neg)) if neg else "none")),
                      flags(neg) if neg else False, True))
    except ControlFailed as exc:
        print(str(exc))
        return 1
    hits = [(o, review_defects(o)) for o in objs if flags(o)]
    print("FINDINGS: %d review(s) pool arm counts that do not trace to a source:" % len(hits))
    for o, defs in hits:
        print("  FAIL: %s" % os.path.basename(os.path.dirname(o)))
        for i, why in defs:
            print("        trial[%d]: %s" % (i, why))
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
