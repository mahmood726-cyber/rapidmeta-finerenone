"""Run the headline-reproducibility test over the 1,243-page corpus extract.

The extract uses a different shape from the SSOT objects: per-trial effects are
stored as an estimate and a VARIANCE on the analysis scale under
`canonical.trials[].effect`, and the page's own pooled result under
`canonical.result.reported` as logEffect/lci/uci. Both are exactly what the
reproduction test needs, so this adapts them and reuses the gate's arithmetic
rather than reimplementing it -- a second copy of a pooling routine is a second
thing to be wrong.

WHAT THIS ANSWERS THAT THE SSOT RUN COULD NOT. All 22 checkable SSOT objects
reproduce, and they must: they were CONVERTED FROM the pages, so an object's
pooled value is by construction the page's own computed pool. The mismatches found
by hand this session were CARD versus OBJECT. This run asks the independent
question -- does each PAGE's own displayed pool follow from that page's own
per-trial numbers?
"""
from __future__ import annotations
import glob
import io
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import headline_reproducible_gate as G  # noqa: E402

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = r"F:\E156\outputs\codex-corpus-scan\extract\full_run"


def adapt(doc):
    """canonical extract -> the object shape headline_reproducible_gate reads."""
    can = doc.get("canonical") or {}
    rep = ((can.get("result") or {}).get("reported")) or {}
    if not rep or rep.get("logEffect") is None:
        return None
    per = []
    for t in can.get("trials") or []:
        eff = t.get("effect") or {}
        est, var = eff.get("estimate"), eff.get("variance")
        if not isinstance(est, (int, float)) or not isinstance(var, (int, float)):
            continue
        if var <= 0:
            continue
        se = math.sqrt(var)
        # The gate reads point/ci_low/ci_high on the DISPLAY scale, so put these
        # back on it: the extract stores log-scale estimate and variance.
        per.append({"trial_id": (t.get("identity") or {}).get("id") or "?",
                    "point": math.exp(est),
                    "ci_low": math.exp(est - G.Z * se),
                    "ci_high": math.exp(est + G.Z * se)})
    if len(per) < 2:
        return None
    pooled = {"measure": rep.get("effect_measure") or can.get("result", {}).get("effect_measure") or "OR",
              "point": math.exp(rep["logEffect"])}
    if isinstance(rep.get("lci"), (int, float)) and isinstance(rep.get("uci"), (int, float)):
        pooled["ci_low"] = math.exp(rep["lci"])
        pooled["ci_high"] = math.exp(rep["uci"])
    return {"outcomes": [{"id": "o", "measure": "OR"}],
            "results": {"by_outcome": {"o": {"per_trial": per, "pooled": pooled}}}}


def main() -> int:
    paths = sorted(glob.glob(os.path.join(ROOT, "*.canonical.json")))
    if not paths:
        print("no corpus extract at %s -- NOT RUN, and not a pass." % ROOT)
        return 2
    tally = {}
    hits = []
    for p in paths:
        try:
            doc = json.load(open(p, encoding="utf-8", errors="replace"))
        except Exception:
            tally["UNREADABLE"] = tally.get("UNREADABLE", 0) + 1
            continue
        obj = adapt(doc)
        if obj is None:
            tally["NO_COMPARABLE_DATA"] = tally.get("NO_COMPARABLE_DATA", 0) + 1
            continue
        try:
            v, notes = G.check(obj)
        except Exception as ex:
            v, notes = "UNCHECKABLE", ["raised %s" % type(ex).__name__]
        tally[v] = tally.get(v, 0) + 1
        if v in ("NOT_REPRODUCED", "POINT_ONLY"):
            hits.append((os.path.basename(p).replace(".html.canonical.json", ""),
                         [n for n in notes if v in n]))

    print("CORPUS EXTRACT: %d page objects" % len(paths))
    for k in ("REPRODUCED", "POINT_ONLY", "NOT_REPRODUCED", "UNCHECKABLE", "SKIPPED",
              "NO_COMPARABLE_DATA", "UNREADABLE"):
        if tally.get(k):
            print("  %-20s %d" % (k, tally[k]))
    d = tally.get("REPRODUCED", 0) + tally.get("POINT_ONLY", 0) + tally.get("NOT_REPRODUCED", 0)
    if d:
        print("\n  ASKED AND ANSWERED on %d pages:" % d)
        print("    headline follows from the page's own per-trial numbers : %d (%.1f%%)"
              % (tally.get("REPRODUCED", 0), 100.0 * tally.get("REPRODUCED", 0) / d))
        print("    point follows, interval does not                       : %d (%.1f%%)"
              % (tally.get("POINT_ONLY", 0), 100.0 * tally.get("POINT_ONLY", 0) / d))
        print("    NO combination reproduces it                           : %d (%.1f%%)"
              % (tally.get("NOT_REPRODUCED", 0), 100.0 * tally.get("NOT_REPRODUCED", 0) / d))
    print("\n  NO_COMPARABLE_DATA and UNCHECKABLE are NOT passes and are excluded from "
          "that denominator. The percentages above describe the %d pages where the "
          "question could be asked, not the %d in the corpus." % (d, len(paths)))
    for name, notes in hits[:25]:
        print("\n  %s" % name)
        for n in notes:
            print("   " + n.strip()[:190])
    return 0


if __name__ == "__main__":
    sys.exit(main())
