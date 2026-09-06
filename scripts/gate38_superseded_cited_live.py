# -*- coding: utf-8 -*-
"""Gate 38 -- a superseded analysis value cited LIVE in a downstream judgement.

After an estimand/input migration (counts->published-HR on empagliflozin; observed-case->
ITT-imputed on inclisiran), the object correctly marks the old pieces `*_superseded_*`. The
defect is when a DOWNSTREAM judgement (GRADE, interpretation, heterogeneity narrative) still
cites the DEAD value instead of the live one -- a judgement computed from the corpse.

REFINED, on Mahmood's instruction, to require DIFFERENT INPUT PROVENANCE, not merely >=2 Q:
  * flag ONLY numbers that live in a `*superseded*/DEPRECATED/legacy` field AND reappear in a
    LIVE downstream judgement field, AND are NOT the current pooled/heterogeneity value.
  * this is why arni-hfref (nine Q across HR/OR/RD/RR, ALL live multi-scale sensitivity of one
    pool) does NOT fire -- none of its values is a superseded number resurfacing downstream.

    A DETECTOR THAT CANNOT TELL CORRUPTION FROM LEGITIMATE VARIATION CONVERTS THE BEST PAGES
    INTO FINDINGS. arni showing the most Q *because it does the most sensitivity analysis* is
    exactly the false positive this refinement removes.

Controls: empagliflozin MUST fire (0.368949, dead-OR Q in GRADE); arni-hfref MUST NOT.
"""
from __future__ import annotations
import io, re, json, os, glob, sys

NUM = re.compile(r"\d+\.\d{3,}")
LIVE_JUDGEMENT = ("grade", "interpretation_caveat", "heterogeneity", "heterogeneity_status")


def _nums(s):
    return set(NUM.findall(s))


def _detect_in_object(d):
    """Return the list of (outcome_id, sorted_cited_numbers) for one object dict."""
    out = []
    for oid, o in ((d.get("results") or {}).get("by_outcome") or {}).items():
        if not isinstance(o, dict):
            continue
        sup, live = set(), ""
        for k, v in o.items():
            vs = json.dumps(v)
            if "supersed" in k.lower() or "DEPRECATED" in k or "legacy" in k.lower():
                sup |= _nums(vs)
            elif k in LIVE_JUDGEMENT:
                live += " " + vs
        livepool = _nums(json.dumps(o.get("pooled") or {})) | _nums(json.dumps(o.get("heterogeneity") or {}))
        cited = (sup & _nums(live)) - livepool
        if cited:
            out.append((oid, sorted(cited)))
    return out


def scan(objs_dir="ssot"):
    objs = [p for p in glob.glob(os.path.join(objs_dir, "*", "*.json"))
            if "sources" not in p and os.path.basename(p)[:-5] == os.path.basename(os.path.dirname(p))]
    hits = []
    for p in objs:
        aid = os.path.basename(p)[:-5]
        try:
            d = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        for oid, cited in _detect_in_object(d):
            hits.append((aid, oid, cited))
    return hits


# SYNTHETIC positive control -- pinned in code, so it cannot self-retire when a real page is fixed.
# (empagliflozin was the live control; fixing its real defect on 2026-09-06 retired it. A control
# anchored to a mutable artefact stops being a control the moment the defect is fixed.)
_SYNTHETIC_POSITIVE = {"results": {"by_outcome": {"primary": {
    "pooled": {"point": 0.77},
    "or_analysis_superseded_2026_08_20": {"q": 0.368949, "note": "dead odds-ratio pool"},
    "grade": "heterogeneity was negligible (Q = 0.368949), so we did not rate down for inconsistency",
}}}}


def controls():
    pos = bool(_detect_in_object(_SYNTHETIC_POSITIVE))                 # synthetic: must fire
    neg = "arni-hfref" not in {h[0] for h in scan()}                   # real good page: must not fire
    return pos, neg


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    pos, neg = controls()
    print("GATE 38 -- superseded value cited live in a downstream judgement")
    print("  CONTROL (positive, SYNTHETIC) fires:   %s (must be True)" % pos)
    print("  CONTROL (negative) arni-hfref silent:  %s (must be True)" % neg)
    if not (pos and neg):
        print("  *** CONTROLS FAILED -- detector not trustworthy ***")
        raise SystemExit(1)
    hits = scan()
    print("  findings: %d objects" % len({h[0] for h in hits}))
    for aid, oid, c in hits:
        print("   %-40s %-22s superseded-cited=%s" % (aid, oid[:22], c))
    raise SystemExit(0)
