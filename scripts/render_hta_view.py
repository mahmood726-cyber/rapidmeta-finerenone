r"""Render the HTA view for one outcome, from data that already exists.

THIS IS A RENDER, NOT A BUILD. The absolute risk difference, the NNT, the
baseline and its source, and the per-trial spread are already computed by
absolute_effects_sidecar.py. They do not reach a reader. That is this
corpus's oldest defect -- the data exists and the rendering denies it -- and
the fix is to emit what is held, not to compose anything.

WHAT IS FORBIDDEN HERE, AND WHY
    NO MODEL-COMPOSED PROSE. Not one sentence on this view is written at
    runtime. Every string is a fixed template in this file, authored once,
    and every number is derived from cells the view also SHOWS. That is what
    keeps two standing claims true at the same time:

        "no model at runtime"           -- nothing here calls one
        "a reader can recompute this"   -- the 2x2 cells are printed beside
                                           every number derived from them

    A generated paragraph would kill both at once, which is why the LLM judge
    was deleted. If the data is absent the view DECLINES; an honest
    declination is the correct output and is scored under c4, never as a
    present-but-empty tab.

WHAT IS EMITTED, PER OUTCOME
    the 2x2 cells, per trial            so every number below is checkable
    baseline risk, with numerator,
      denominator and its SOURCE named
    the per-trial spread the pooled
      baseline hides
    pooled absolute risk difference
      and its interval
    NNT, with the Altman reading where
      the interval spans no difference
    the estimand AS PUBLISHED
    k
    WHAT IS NOT HELD                    named, never omitted
"""
from __future__ import annotations
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from absolute_effects_sidecar import (  # noqa: E402
    evaluate_sidecar, load_store,
)

W = 78


def rule(ch="-"):
    return ch * W


def render(row, sidecar):
    """Return a list of lines. Pure formatting of derived values."""
    out = []
    out.append(rule("="))
    out.append("HTA VIEW -- %s" % row["sidecar"])
    out.append(rule("="))

    if row["state"] != "COMPUTABLE":
        # DECLINATION. Named, with the reason, and nothing invented.
        out.append("")
        out.append("THIS VIEW DECLINES.")
        out.append("")
        if row["state"] == "REFUSED_BY_STORE":
            out.append("  The store REFUSED this pool. Its reason, verbatim:")
            out.append("")
            for line in _wrap(str(row.get("store_reason_verbatim")), 72):
                out.append("      " + line)
            out.append("")
            out.append("  An absolute effect computed on a pool the store")
            out.append("  refused would be the same defect one layer up, so")
            out.append("  none is shown.")
        else:
            out.append("  Reason: %s" % str(row.get("reason", "")).split(":")[0])
            out.append("")
            for line in _wrap(str(row.get("reason", "")), 72):
                out.append("      " + line)
        out.append("")
        out.append("  Nothing is estimated to fill this space.")
        return out

    # ---- the cells, first, because everything below is derived from them
    out.append("")
    out.append("THE 2x2 CELLS THIS VIEW IS DERIVED FROM  (k = %d)" % row["k_used"])
    out.append("")
    out.append("  %-22s %10s %10s   %10s %10s"
               % ("trial", "treat ev", "treat n", "ctrl ev", "ctrl n"))
    cells = [t for t in (sidecar.get("trials") or [])
             if all(x in t for x in ("tE", "tN", "cE", "cN"))]
    for t in cells:
        out.append("  %-22s %10s %10s   %10s %10s"
                   % (str(t.get("name") or t.get("nct"))[:22],
                      t["tE"], t["tN"], t["cE"], t["cN"]))
    tot_ce = sum(t["cE"] for t in cells)
    tot_cn = sum(t["cN"] for t in cells)
    out.append("  %-22s %10s %10s   %10d %10d" % ("TOTAL", "", "", tot_ce, tot_cn))

    # ---- baseline, with its source
    out.append("")
    out.append("BASELINE RISK")
    out.append("  value          %.6f   =  %d / %d"
               % (row["baseline_value"], tot_ce, tot_cn))
    out.append("  source         control arms of the trials above")
    sp = row.get("baseline_spread") or {}
    if sp:
        out.append("  per-trial      %.4f to %.4f  (%.1f-fold)"
                   % (sp["min"], sp["max"], sp["fold"] or float("nan")))
        out.append("                 the pooled figure hides this spread; the")
        out.append("                 same effect at the extremes of that range")
        out.append("                 is a different absolute number")

    # ---- the effect
    out.append("")
    out.append("ABSOLUTE EFFECT")
    p = row.get("pooled_rd") or {}
    out.append("  risk difference        %+.6f   (%+.2f per 1000)"
               % (row["risk_difference"], row["risk_difference_per_1000"]))
    if p.get("ci_low") is not None:
        out.append("  95%% interval           %+.6f to %+.6f"
                   % (p["ci_low"], p["ci_high"]))
    out.append("  direction              %s" % row["direction"])
    out.append("  method                 %s" % p.get("interval_basis", ""))
    if p.get("tau2") is not None:
        out.append("  tau-squared            %.8g" % p["tau2"])

    # ---- NNT
    out.append("")
    out.append("NUMBER NEEDED TO TREAT")
    out.append("  NNT                    %.1f" % row["nnt_magnitude"])
    kind = row.get("nnt_ci_kind")
    ci = row.get("nnt_ci") or {}
    if kind == "FINITE":
        out.append("  95%% interval           %.1f to %.1f"
                   % (ci["low"], ci["high"]))
    elif kind == "SPANS_NO_DIFFERENCE":
        out.append("  95% interval           NOT A FINITE RANGE")
        out.append("                         %.1f (fewer events) to infinity,"
                   % ci["nnt_fewer_events_bound"])
        out.append("                         and back from %.1f (more events)"
                   % ci["nnt_more_events_bound"])
        out.append("                         Altman 1998: the risk-difference")
        out.append("                         interval includes zero, so a")
        out.append("                         finite NNT range would be a")
        out.append("                         fabrication")
    else:
        out.append("  95%% interval           %s" % kind)

    # ---- polarity
    out.append("")
    out.append("READING")
    if row.get("event_polarity") == "KNOWN":
        out.append("  event is               %s" % row.get("event_is"))
        for line in _wrap(str(row.get("event_polarity_source")), 56):
            out.append("  %-22s %s" % ("", line))
    else:
        out.append("  event polarity         UNKNOWN")
        out.append("                         Nothing held here establishes")
        out.append("                         whether an event of this outcome")
        out.append("                         is good or bad, so this NNT must")
        out.append("                         not be read as benefit or harm.")
        out.append("                         The magnitude and the arithmetic")
        out.append("                         direction stand; the clinical")
        out.append("                         reading does not.")

    # ---- what is not held
    out.append("")
    out.append("WHAT IS NOT HELD")
    missing = []
    if row.get("event_polarity") != "KNOWN":
        missing.append("event polarity -- no `favours` for a matched outcome")
    if row.get("store_adjudication") == "NO_STORE_ADJUDICATION":
        missing.append("a store ruling -- no store object exists for this "
                       "page, and silence is not permission")
    if row.get("store_adjudication") == "NAME_MATCH_WITHOUT_TRIAL_OVERLAP":
        missing.append("a store ruling -- the same-named store object pools "
                       "different trials")
    if row.get("store_adjudication") == "IDENTITY_UNVERIFIABLE":
        missing.append("a store ruling -- no shared trial registration proves "
                       "the same-named object describes this evidence")
    if row.get("baseline_spread") in (None, {}):
        missing.append("a per-trial baseline spread")
    missing.append("uncertainty in the baseline -- the interval above holds "
                   "the baseline FIXED and transforms only the relative "
                   "measure, so it understates total uncertainty")
    for m in missing:
        for i, line in enumerate(_wrap(m, 70)):
            out.append("  %s %s" % ("-" if i == 0 else " ", line))
    out.append("")
    out.append(rule())
    out.append("Every number above is derived from the cells printed at the")
    out.append("top. No sentence here was composed at runtime.")
    return out


def _wrap(text, width):
    words = str(text).split()
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines or [""]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stem", help="sidecar stem, e.g. SGLT2_HF")
    a = ap.parse_args()
    path = os.path.join(ROOT, "outputs", "r_validation", a.stem + ".json")
    if os.path.exists(path) is False:
        print("no such sidecar: %s" % path)
        return 2
    store, dropped = load_store()
    row = evaluate_sidecar(path, store)
    sidecar = json.load(open(path, encoding="utf-8"))
    for line in render(row, sidecar):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
