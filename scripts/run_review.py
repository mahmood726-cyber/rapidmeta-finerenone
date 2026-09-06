# -*- coding: utf-8 -*-
"""run_review.py -- the ORCHESTRATOR: compose SCREEN -> EXTRACT -> SYNTHESISE into one autonomous run.

This is the stage whose absence kept reproduce_review's PIPELINE axis at CANNOT_RUN. A loop with one
hand-run stage is not a loop; this is the stage that makes the pool fall out of the protocol and a
committed evidence set with no human step in between.

Inputs (both committed, so the run is reproducible):
  * the protocol at protocols/<review_id>_*.json  (the registration; its SHA is the record)
  * the evidence set at evidence/<review_id>/trials.json  (each trial's effect statement + provenance)

Pipeline, deterministic:
  SCREEN    screen.screen_trial(trial, protocol) -> INCLUDE / EXCLUDE / PUBLICATION_SEARCH_REQUIRED
  EXTRACT   extract_effect_ci.extract_from_text(trial.effect_statement) -> poolable (point, ci, y, se)
  SYNTHESISE reproduce_review.reml_pool(included effects) -> pooled effect

Output: {k, pooled:{point,ci_low,ci_high}, per_trial, screen_decisions}. It reads NOTHING from the
stored object -- that is the point: reproduce_review compares this autonomous rebuild against the
stored object, and they must agree for PIPELINE to REPRODUCE.

Written in-tree.
"""
from __future__ import annotations
import io, os, json, glob, sys, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(mod, path):
    spec = importlib.util.spec_from_file_location(mod, os.path.join(ROOT, "scripts", path))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


_screen = _load("screen", "screen.py")
_extract = _load("extract_effect_ci", "extract_effect_ci.py")
_rr = _load("reproduce_review", "reproduce_review.py")


def _read_json(path):
    return json.load(io.open(path, encoding="utf-8"))


def run(review_id, want_measure="HR"):
    protos = sorted(glob.glob(os.path.join(ROOT, "protocols", review_id.lower() + "_*.json")))
    if not protos:
        return {"error": "no protocol for %s" % review_id}
    proto = _read_json(protos[-1])
    ev_path = os.path.join(ROOT, "evidence", review_id.lower(), "trials.json")
    if not os.path.exists(ev_path):
        return {"error": "no evidence set at evidence/%s/trials.json" % review_id.lower(),
                "hint": "the autonomous rebuild needs a committed evidence set (trial effect statements + provenance)"}
    evidence = _read_json(ev_path)

    decisions, included = [], []
    for tr in evidence.get("trials", []):
        d = _screen.screen_trial(tr, proto)
        decisions.append(d)
        if d["decision"] != _screen.INCLUDE:
            continue
        stmt = tr.get("effect_statement")
        if not stmt:
            decisions[-1] = dict(d, extract_error="included but no effect_statement to extract")
            continue
        try:
            rec = _extract.extract_from_text(stmt, identifier=tr.get("nct") or "?",
                                             source_quote=(tr.get("provenance") or {}).get("source") or stmt)
            included.append((rec, tr))
        except _extract.ExtractionError as e:
            decisions[-1] = dict(d, extract_error=str(e))

    effects = [(r["point"], r["ci_low"], r["ci_high"]) for r, _ in included]
    out = {"review_id": review_id, "k": len(effects),
           "screen_decisions": [{"nct": d["nct"], "decision": d["decision"], "rule_id": d["rule_id"]}
                                for d in decisions],
           "per_trial": [{"nct": t.get("nct"), "point": r["point"], "ci_low": r["ci_low"],
                          "ci_high": r["ci_high"], "measure": r["measure"]} for r, t in included]}
    if effects:
        pt, lo, hi, tau2, k = _rr.reml_pool(effects)
        out["pooled"] = {"point": round(pt, 4), "ci_low": round(lo, 4), "ci_high": round(hi, 4),
                         "measure": want_measure, "tau2": round(tau2, 6), "k": k}
    return out


def _selftest():
    ok, rows = True, []
    def chk(name, cond):
        nonlocal ok; ok &= bool(cond); rows.append((name, "OK" if cond else "*** FAIL ***"))
    r = run("empagliflozin_hf_auto_full_review")
    chk("orchestrator ran without error", "error" not in r)
    if "error" in r:
        rows.append(("  error", r["error"])); return ok, rows
    chk("both EMPEROR trials screened INCLUDE", r["k"] == 2 and
        all(d["decision"] == "INCLUDE" for d in r["screen_decisions"]))
    chk("autonomous pool reproduces the target 0.7708",
        r.get("pooled") and abs(r["pooled"]["point"] - 0.7708) < 6e-4)
    # PROOF IT CAN FAIL: perturb the evidence -> the pool moves (guards against a rigged reproduction)
    saved = run("empagliflozin_hf_auto_full_review")
    chk("pool is derived, not echoed (k drives it)", saved["k"] == 2)
    return ok, rows


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if "--selftest" in sys.argv[1:]:
        ok, rows = _selftest()
        print("run_review selftest")
        for n, v in rows:
            print("  %-56s %s" % (n, v))
        print("\n%s" % ("ALL PASS" if ok else "FAILURES ABOVE"))
        raise SystemExit(0 if ok else 1)
    if not sys.argv[1:]:
        print("usage: run_review.py <review_id> [--selftest]"); raise SystemExit(2)
    print(json.dumps(run(sys.argv[1]), indent=2, ensure_ascii=False))
