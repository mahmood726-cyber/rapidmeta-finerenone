# -*- coding: utf-8 -*-
"""Gate 59 -- the served effect scale must match what the trials estimate.

Vaccine efficacy is 1-RR, 1-IRR or 1-HR -- NEVER 1-OR. ROTAVIRUS_VACCINE_AFRICA converted cumulative
counts to ODDS RATIOS, discarded person-time, and served 1-OR as "~51% efficacy". That is a
methodological error, not a display choice. This detector fires on an object whose outcome declares an
efficacy/VE interpretation (or trial_native_effect risk/rate/hazard) while the served measure is OR.

Controls: SYNTHETIC positive (VE from OR) fires; SYNTHETIC negative (VE from RR) silent.
"""
from __future__ import annotations
import io, json, os, glob, re, sys

_VE = re.compile(r"vaccine efficac|1\s*[-−]\s*OR|efficacy.*odds|% efficacy", re.I)
_OK_MEASURE = {"risk": {"RR", "log_RR", "RD"}, "rate": {"IRR", "log_IRR"}, "hazard": {"HR", "log_HR"}}


def _detect(obj):
    hits = []
    for oid, o in ((obj.get("results") or {}).get("by_outcome") or {}).items():
        if not isinstance(o, dict):
            continue
        meas = str((o.get("pooled") or {}).get("measure") or o.get("measure") or "")
        nat = o.get("trial_native_effect")
        blob = json.dumps(o)
        looks_ve = bool(_VE.search(blob)) or (nat in _OK_MEASURE)
        is_or = meas.upper() in ("OR", "LOG_OR")
        if looks_ve and is_or:
            hits.append((oid, "efficacy/rate outcome served as %s -- VE is 1-RR/1-IRR/1-HR, not 1-OR" % meas))
    return hits


_POS = {"results": {"by_outcome": {"primary": {"trial_native_effect": "risk",
        "pooled": {"measure": "OR", "point": 0.49}, "note": "reported as ~51% vaccine efficacy (1-OR)"}}}}
_NEG = {"results": {"by_outcome": {"primary": {"trial_native_effect": "risk",
        "pooled": {"measure": "RR", "point": 0.386}, "note": "vaccine efficacy 61.4% = 1-RR"}}}}


def scan(objs_dir="ssot"):
    out = []
    for p in glob.glob(os.path.join(objs_dir, "*", "*.json")):
        if os.path.basename(p)[:-5] != os.path.basename(os.path.dirname(p)):
            continue
        try:
            d = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        for oid, why in _detect(d):
            out.append((os.path.basename(p)[:-5], oid, why))
    return out


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    pos = bool(_detect(_POS)); neg = not _detect(_NEG)
    print("GATE 59 -- effect scale must match the trials' estimand (VE is not 1-OR)")
    print("  CONTROL positive (VE from OR) fires:  %s (must be True)" % pos)
    print("  CONTROL negative (VE from RR) silent: %s (must be True)" % neg)
    if not (pos and neg):
        print("  *** CONTROLS FAILED ***"); raise SystemExit(1)
    hits = scan()
    print("  findings: %d" % len(hits))
    for a, o, w in hits[:20]:
        print("   %-40s %-22s %s" % (a, o[:22], w))
    raise SystemExit(0)
