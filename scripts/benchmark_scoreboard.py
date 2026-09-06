# -*- coding: utf-8 -*-
"""The PER-OUTCOME scoreboard. Wraps the rigorous single-outcome reproducer
(reproduce_benchmark.py) into the full table the goal asks for: for every benchmark outcome,
k ours-vs-theirs, the disagreement set, the pooled estimate with the method named on BOTH sides,
and -- the point -- the loss ledger saying what we could not obtain and at which step.

    protocol -> search -> screen -> identify -> extract arms -> pool -> compare      (per outcome)

DESIGN CHOICES, each a standing lesson:
  * ONE data source. Every row reads the SAME AACT snapshot the death reproducer uses; no row
    mixes a live-API number with a snapshot number, which would make a source gap look like a
    data gap.
  * REUSE, NOT REBUILD. The death row calls reproduce_benchmark.extract_death verbatim -- its
    HEART-FID cross-check and anchor validation are the reason to trust it. A second lane already
    built that; this composes it instead of duplicating it.
  * MEASURE NAMED ON BOTH SIDES. Theirs is an IRR (needs person-time). Ours is an RR (events+n).
    They coincide only under balanced follow-up. Stated on every row, never elided.
  * NOT TUNED. A row we cannot extract honestly reports its k and names the blocking step. There
    is no branch here that raises a number by relaxing a rule. An honest k=1 with a named
    remainder beats a false k=4 with none.

WHAT IS WIRED NOW: all_cause_death (via the reproducer) and serious_adverse_events (AE-module
'serious' totals, which carry affected AND at-risk per arm directly). Every other outcome prints
theirs and the EXACT step blocking ours -- a work list, not a blank.
"""
from __future__ import annotations
import io, os, sys, math, json
from collections import defaultdict
sys.path.insert(0, "scripts")
import reproduce_benchmark as RB
import titled_outcome_extract as TOE

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# how each benchmark outcome is reached, and the honest block where it is not yet
OUTCOME_PLAN = {
    "all_cause_death":        ("wired", "reproduce_benchmark.extract_death (AE deaths / titled, HEART-FID checked)"),
    "serious_adverse_events": ("wired", "AE-module event_type='serious' totals (affected + at-risk per arm)"),
    "cv_death":               ("wired", "titled-outcome component class, arithmetic pct*N, denom class-title-first"),
    "mace":                   ("wired", "titled composite outcome (3-point), not summed from components"),
    "nonfatal_mi":            ("wired", "titled-outcome component class, arithmetic pct*N"),
    "nonfatal_stroke":        ("wired", "titled-outcome component class, arithmetic pct*N"),
    "hf_hospitalisation":     ("wired", "titled-outcome component class, arithmetic pct*N"),
    "neoplasm":               ("blocked", "AE-term (MedDRA organ-class) parsing not yet wired"),
    "infections":             ("blocked", "AE-term (MedDRA organ-class) parsing not yet wired"),
    "gi_disorders":           ("blocked", "AE-term (MedDRA organ-class) parsing not yet wired"),
    "acute_kidney_failure":   ("blocked", "AE-term (MedDRA organ-class) parsing not yet wired"),
    "pancreatitis":           ("blocked", "AE-term (MedDRA preferred-term) parsing not yet wired"),
    "gallbladder_disorders":  ("blocked", "AE-term (MedDRA preferred-term) parsing not yet wired"),
}

_T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306,
         9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131,
         16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086}


def _t975(df):
    return float("nan") if df <= 0 else _T975.get(df, 1.98 if df < 100 else 1.96)


def pool_rr_reml_hksj(cells):
    """RR by log-RR, REML tau2, HKSJ on t_{k-1}; 0.5 continuity only where a contrast has a zero
    cell; k=1 -> single-trial Wald. Method string returned so it is never confused with theirs."""
    ys, vs = [], []
    for c in cells:
        tE, cE = c["tE"], c["cE"]
        a, b, d, e = tE, c["tN"] - tE, cE, c["cN"] - cE
        if 0 in (a, b, d, e):
            a, b, d, e = a + .5, b + .5, d + .5, e + .5
        ys.append(math.log((a / (a + b)) / (d / (d + e))))
        vs.append(1./a - 1./(a + b) + 1./d - 1./(d + e))
    k = len(ys)
    if k == 0:
        return None
    if k == 1:
        se = math.sqrt(vs[0])
        return {"k": 1, "rr": math.exp(ys[0]), "lo": math.exp(ys[0]-1.96*se),
                "hi": math.exp(ys[0]+1.96*se), "tau2": None, "method": "RR, Wald (k=1, no pooling)"}
    tau2 = 0.0
    for _ in range(200):
        w = [1./(v+tau2) for v in vs]; sw = sum(w)
        mu = sum(wi*yi for wi, yi in zip(w, ys))/sw
        new = max(0., sum(wi*wi*((yi-mu)**2 - vi) for wi, yi, vi in zip(w, ys, vs))/sum(wi*wi for wi in w) + 1./sw)
        if abs(new-tau2) < 1e-10:
            tau2 = new; break
        tau2 = new
    w = [1./(v+tau2) for v in vs]; sw = sum(w)
    mu = sum(wi*yi for wi, yi in zip(w, ys))/sw
    q = max(1.0, sum(wi*(yi-mu)**2 for wi, yi in zip(w, ys))/(k-1))
    se = math.sqrt(q/sw); t = _t975(k-1)
    return {"k": k, "rr": math.exp(mu), "lo": math.exp(mu-t*se), "hi": math.exp(mu+t*se),
            "tau2": tau2, "method": "RR, REML tau2, HKSJ t_{k-1}"}


def _side(nct, code, rgroup):
    t = (rgroup.get(nct, {}).get(code) or "").lower()
    if any(g in t for g in RB.GLP1):
        return "TRT"
    if any(c in t for c in RB.CTRL):
        return "CTRL"
    return "?"


def extract_sae(nct, rgroup, totals):
    """SAE 2x2 from AE-module 'serious' totals: subjects_affected and subjects_at_risk per arm,
    summed by side. Returns {tE,tN,cE,cN} or None (no serious totals, or a side unresolved)."""
    aff, at = defaultdict(int), defaultdict(int)
    seen = False
    for et, code, a, risk in totals.get(nct, []):
        if et != "serious":
            continue
        s = _side(nct, code, rgroup)
        av, rv = RB._num(a), RB._num(risk)
        if av is None or rv is None:
            continue
        aff[s] += av; at[s] += rv; seen = True
    if not seen or not all(k in aff and k in at for k in ("TRT", "CTRL")):
        return None
    return {"tE": aff["TRT"], "tN": at["TRT"], "cE": aff["CTRL"], "cN": at["CTRL"]}


def run(out_dir=None):
    bench = json.load(open(os.path.join(REPO, "benchmarks", "GALLI_2025_GLP1_JACC.json"), encoding="utf-8"))
    bid = bench["benchmark_id"]
    theirs_per = {o["outcome"]: o for o in bench["THEIR_PER_OUTCOME_k_IS_NOT_21"]["per_outcome"]}
    theirs_est = {o["outcome"]: o for o in bench["their_outcomes"]}
    ncts = RB.BENCHMARK_NCTS.get(bid, {})
    aact = RB.resolve_aact()
    if not aact:
        return {"state": "NOT_RUN", "why": "no AACT snapshot (set AACT_ROOT/AACT_DIR). Absent source is not a zero."}
    intv, rgroup, totals, om = RB.load_maps(aact, list(ncts.values()))
    toe = TOE.load_tables(aact, list(ncts.values()))
    EFFICACY = ("cv_death", "mace", "nonfatal_mi", "nonfatal_stroke", "hf_hospitalisation")

    resolvable = {n: c for n, c in ncts.items() if c}
    unresolved = [n for n, c in ncts.items() if not c]

    rows = []
    for outcome, their in theirs_per.items():
        plan, how = OUTCOME_PLAN.get(outcome, ("blocked", "no plan"))
        their_k = their["k"]
        their_crude = ((their["events_glp1"]/their["n_glp1"]) / (their["events_ctrl"]/their["n_ctrl"])
                       if all(their.get(k) for k in ("events_glp1", "n_glp1", "events_ctrl", "n_ctrl")) else None)
        est = theirs_est.get(outcome)
        if plan != "wired":
            rows.append({"outcome": outcome, "their_k": their_k, "our_k": 0,
                         "their_irr": est["irr"] if est else None, "their_crude": their_crude,
                         "our": None, "how": how, "blocked_at": how,
                         "loss": {"blocked": "ALL %d -- %s" % (their_k, how)},
                         "disagreement": {"theirs_only": "not enumerated (extraction blocked)"}})
            continue
        cells, used, nodata = [], [], []
        for name, nct in sorted(resolvable.items()):
            if outcome == "all_cause_death":
                trt, ctrl, note = RB.extract_death(nct, rgroup, totals, om)
                cell = ({"tE": trt[0], "tN": trt[1], "cE": ctrl[0], "cN": ctrl[1]}
                        if trt and ctrl else None)
            elif outcome == "serious_adverse_events":
                cell = extract_sae(nct, rgroup, totals); note = "AE serious totals"
            elif outcome in EFFICACY:
                res = TOE.extract_titled(nct, outcome, toe)
                cell = res if "tE" in res else None
                note = res.get("status", "ok") if cell is None else res.get("event_route", "ok")
            else:
                cell = None; note = "no extractor"
            if cell:
                cell["trial"] = name; cell["nct"] = nct
                cells.append(cell); used.append(name)
            else:
                nodata.append(name)
        pooled = pool_rr_reml_hksj(cells) if cells else None
        # crude across our populated set, for a like-for-like line against their crude
        dt = sum(c["tE"] for c in cells); nt = sum(c["tN"] for c in cells)
        dc = sum(c["cE"] for c in cells); nc = sum(c["cN"] for c in cells)
        our_crude = (dt/nt)/(dc/nc) if (nt and nc and dc) else None
        rows.append({"outcome": outcome, "their_k": their_k, "our_k": len(cells),
                     "their_irr": est["irr"] if est else None, "their_crude": their_crude,
                     "our": pooled, "our_crude": our_crude, "how": how,
                     "our_trials": used,
                     "disagreement": {"theirs_has_ours_lacks": their_k - len(cells),
                                      "ours_could_not_populate": nodata,
                                      "unresolved_ncts": unresolved},
                     "loss": {"no_usable_data": nodata, "unresolved_ncts": unresolved},
                     "cells": cells})
    result = {"benchmark": bid, "aact": aact, "identified_resolvable": len(resolvable),
              "unresolved": unresolved,
              "measure_note": "THEIRS = IRR (person-time). OURS = RR (events+n). Equal only under "
                              "balanced arm follow-up; the estimate comparison is indicative.",
              "rows": rows}
    if out_dir:
        from pathlib import Path
        import time
        p = Path(out_dir); p.mkdir(parents=True, exist_ok=True)
        f = p / ("scoreboard_galli_%s.json" % time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
        io.open(f, "w", encoding="utf-8", newline="\n").write(json.dumps(result, indent=1, ensure_ascii=False))
        result["_written_to"] = str(f)
    return result


def _our(o):
    if not o:
        return "%-30s" % "(blocked)"
    return "RR %.3f [%.3f, %.3f] %s" % (o["rr"], o["lo"], o["hi"],
                                        "" if o.get("tau2") in (None,) else "t2=%.3f" % o["tau2"])


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    r = run(out_dir=("evidence/acquisition" if "--write" in sys.argv else None))
    if r.get("state") == "NOT_RUN":
        print("NOT_RUN:", r["why"]); raise SystemExit(0)
    print("PER-OUTCOME SCOREBOARD -- %s" % r["benchmark"])
    print("AACT: %s | identified/resolvable: %d | unresolved NCTs: %s"
          % (r["aact"], r["identified_resolvable"], ", ".join(r["unresolved"]) or "none"))
    print("MEASURE: %s\n" % r["measure_note"])
    print("  %-24s %5s %5s  %-22s %-34s" % ("outcome", "theirK", "ourK", "theirs", "ours (method named)"))
    print("  " + "-" * 96)
    for row in r["rows"]:
        theirs = "IRR %.2f (crude %.3f)" % (row["their_irr"], row["their_crude"]) if row["their_irr"] else "-"
        print("  %-24s %5s %5s  %-22s %-34s" % (row["outcome"], row["their_k"], row["our_k"], theirs, _our(row["our"])))
    print("\n  LOSS LEDGER (what we could not obtain, and at which step):")
    for row in r["rows"]:
        if row["our_k"] == 0:
            print("   %-24s BLOCKED: %s" % (row["outcome"], row["how"]))
        else:
            d = row["disagreement"]
            print("   %-24s ours k=%d of their %d; could not populate %d (%s); unresolved NCTs %d"
                  % (row["outcome"], row["our_k"], row["their_k"], len(d["ours_could_not_populate"]),
                     ", ".join(d["ours_could_not_populate"]) or "none", len(d["unresolved_ncts"])))
    if r.get("_written_to"):
        print("\n  written:", r["_written_to"])
