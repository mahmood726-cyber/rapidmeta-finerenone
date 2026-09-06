# -*- coding: utf-8 -*-
"""Scan the 155 served objects for a value that came in through a rule that could confuse a RATE
for a PROPORTION -- the stored-data form of the extractor bug where '3.9' (events per 100
patient-years) was almost read as '3.9%' of participants.

    A NUMBER'S SCALE DOES NOT TELL YOU ITS UNIT. A ratio near 1 can be a risk ratio (a
    proportion contrast) or a rate ratio (an incidence contrast, needing person-time); an
    arm value of 3.9 can be a percentage of people or a rate per 100 patient-years. The
    plausible-looking magnitude is the most dangerous kind of wrong, because nothing
    downstream flags it. Same family as reading denoms.counts and getting 48 wrong integers.

WHAT IT FLAGS (each a rate-treated-as-proportion, or its measure-level analogue):
  A. A POOL MIXING a rate-type measure (RATE_RATIO / IRR) with a risk-type measure (RR / OR /
     RISK_RATIO / ODDS_RATIO). Pooling a rate ratio with a risk ratio treats one as the other.
  B. A POOL MIXING a hazard ratio (HR) with a rate ratio (RATE_RATIO / IRR) -- softer: both are
     time-based but an HR (instantaneous hazard) is not an IRR (average rate); reported
     separately, not merged into A.
  C. AN ARM-LEVEL count with events > N, or a stored proportion/risk > 1 -- the impossible value
     a rate-as-proportion arithmetic error produces at the extreme.

THE INSTRUMENT CAN FIND A POSITIVE. _selftest plants one of each and asserts each is flagged; a
scan that can only return zero is not a measurement. A zero on the real corpus is reported only
because the planted positives were caught.
"""
from __future__ import annotations
import io, os, sys, json, glob, re

RATE = {"RATE_RATIO", "IRR"}
RISK = {"RR", "OR", "RISK_RATIO", "ODDS_RATIO"}
HR = {"HR", "HAZARD_RATIO"}


def _objs():
    out = []
    for p in glob.glob("ssot/*/*.json"):
        if "sources" in p:
            continue
        if os.path.basename(p)[:-5] == os.path.basename(os.path.dirname(p)):
            out.append(p)
    return sorted(out)


def _walk_arms(node, path, hits):
    """Flag arm-level impossibilities: events>N, or a proportion/risk field > 1."""
    if isinstance(node, dict):
        # events + n pair (any casing) in the same dict
        keys = {k.lower(): k for k in node}
        e = next((keys[k] for k in keys if k in ("events", "tE".lower(), "e", "affected", "subjects_affected")), None)
        n = next((keys[k] for k in keys if k in ("n", "at_risk", "subjects_at_risk", "denom", "tN".lower())), None)
        if e and n and isinstance(node[e], (int, float)) and isinstance(node[n], (int, float)) and node[n] > 0:
            if node[e] > node[n]:
                hits.append(("C_events_gt_N", path, "%s=%s > %s=%s" % (e, node[e], n, node[n])))
        for k, v in node.items():
            if k.lower() in ("proportion", "risk", "prop", "p_event") and isinstance(v, (int, float)) and v > 1:
                hits.append(("C_proportion_gt_1", path + "/" + k, str(v)))
            _walk_arms(v, path + "/" + k, hits)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _walk_arms(v, "%s[%d]" % (path, i), hits)


def scan_object(path, d):
    hits = []
    bo = (d.get("results") or {}).get("by_outcome") or {}
    for oid, o in bo.items():
        if not isinstance(o, dict):
            continue
        pt = o.get("per_trial") or []
        ms = {t.get("measure") for t in pt if isinstance(t, dict) and t.get("measure")}
        pooled = (o.get("pooled") or {}).get("measure")
        allm = set(ms) | ({pooled} if pooled else set())
        if (allm & RATE) and (allm & RISK):
            hits.append(("A_rate_mixed_with_risk", oid, sorted(allm)))
        elif (allm & HR) and (allm & RATE):
            hits.append(("B_hr_mixed_with_rate", oid, sorted(allm)))
    _walk_arms(d.get("results"), "results", hits)
    _walk_arms(d.get("extraction"), "extraction", hits)
    return hits


def run():
    rows = []
    for p in _objs():
        try:
            d = json.load(io.open(p, encoding="utf-8"))
        except Exception as ex:
            rows.append((os.path.basename(p), [("READ_ERROR", "", str(ex)[:60])]))
            continue
        h = scan_object(p, d)
        if h:
            rows.append((os.path.basename(p), h))
    return rows


def _selftest():
    planted_A = {"results": {"by_outcome": {"o1": {
        "per_trial": [{"measure": "IRR"}, {"measure": "RR"}], "pooled": {"measure": "RR"}}}}}
    planted_C = {"results": {"by_outcome": {}}, "extraction": {"arms": [{"events": 150, "n": 100}]}}
    hA = scan_object("plantA", planted_A)
    hC = scan_object("plantC", planted_C)
    okA = any(t[0] == "A_rate_mixed_with_risk" for t in hA)
    okC = any(t[0] == "C_events_gt_N" for t in hC)
    return okA, okC


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    okA, okC = _selftest()
    print("SELF-TEST (instrument can find a positive): mix A=%s  arm C=%s" % (okA, okC))
    if not (okA and okC):
        print("*** INSTRUMENT BROKEN -- it cannot find a planted positive; its zero means nothing ***")
        raise SystemExit(1)
    rows = run()
    n_obj = len(_objs())
    A = sum(1 for _, hs in rows for t in hs if t[0] == "A_rate_mixed_with_risk")
    B = sum(1 for _, hs in rows for t in hs if t[0] == "B_hr_mixed_with_rate")
    C = sum(1 for _, hs in rows for t in hs if t[0].startswith("C_"))
    print("\nSCANNED %d objects." % n_obj)
    print("  A  rate ratio pooled with/as a risk ratio (the defect): %d" % A)
    print("  B  hazard ratio pooled with a rate ratio (softer):       %d" % B)
    print("  C  arm-level events>N or proportion>1:                   %d" % C)
    if rows:
        print("\nDETAIL:")
        for name, hs in rows:
            for t in hs:
                print("  %-34s %-26s %s" % (name, t[0], t[1] if not isinstance(t[1], str) else t[1])
                      + ("  " + str(t[2]) if len(t) > 2 else ""))
    else:
        print("\nNo objects flagged. (Instrument proven above, so this zero is a measurement.)")
    raise SystemExit(0)
