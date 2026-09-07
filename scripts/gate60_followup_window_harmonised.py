# -*- coding: utf-8 -*-
"""Gate 60 -- follow-up windows must be harmonised before pooling cumulative counts.

The time horizon is part of the estimand. ROTAVIRUS pooled cumulative counts from Rotarix (through age 1),
RotaTeq (median 527d ~21mo) and RotaSIIL (~9.8mo) as one quantity -- and that manufactured I2 57.6% where
the harmonised first-year ratios are I2 0%. Fires on an object whose per-trial follow-up windows span a
ratio > 1.5x while the pool is cumulative counts and harmonisation is not declared.

Controls: SYNTHETIC positive (12/21/9.8mo, not declared) fires; SYNTHETIC negative (declared harmonised) silent.
"""
from __future__ import annotations
import io, json, os, glob, sys


def _months(t):
    try:
        return float(t.get("follow_up_months")) if isinstance(t, dict) and t.get("follow_up_months") is not None else None
    except Exception:
        return None


def _detect(obj):
    hits = []
    for oid, o in ((obj.get("results") or {}).get("by_outcome") or {}).items():
        if not isinstance(o, dict):
            continue
        fw = o.get("follow_up_window") or {}
        if fw.get("harmonised") is True:
            continue
        months = [m for m in (_months(t) for t in (o.get("per_trial") or [])) if m]
        if len(months) >= 2 and (max(months) / min(months)) > 1.5:
            hits.append((oid, "follow-up spans %.1f-%.1fmo (%.1fx) pooled as cumulative counts, harmonisation not declared"
                         % (min(months), max(months), max(months) / min(months))))
    return hits


_POS = {"results": {"by_outcome": {"primary": {"per_trial": [
        {"follow_up_months": 12}, {"follow_up_months": 21}, {"follow_up_months": 9.8}]}}}}
_NEG = {"results": {"by_outcome": {"primary": {"follow_up_window": {"harmonised": True, "window": "first year"},
        "per_trial": [{"follow_up_months": 12}, {"follow_up_months": 12}]}}}}


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
    print("GATE 60 -- follow-up windows must be harmonised before pooling cumulative counts")
    print("  CONTROL positive (12/21/9.8mo) fires: %s (must be True)" % pos)
    print("  CONTROL negative (harmonised) silent: %s (must be True)" % neg)
    if not (pos and neg):
        print("  *** CONTROLS FAILED ***"); raise SystemExit(1)
    hits = scan()
    print("  findings: %d" % len(hits))
    for a, o, w in hits[:20]:
        print("   %-40s %-22s %s" % (a, o[:22], w))
    raise SystemExit(0)
