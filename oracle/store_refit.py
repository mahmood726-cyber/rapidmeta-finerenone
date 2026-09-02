# -*- coding: utf-8 -*-
"""Refit the SERVED surface: tau2 in ssot/<topic>/<topic>.json, not the sidecars.

build_tabbed.py reads the STORE. ssot/ contains zero references to r_validation, so
the page builder cannot read a sidecar. The 747 sidecars are orphans; results.by_outcome
is what reaches a reader. An oracle validates whatever population you point it at and
says nothing about whether that population is the one that matters -- mine was pointed
at both, and only half of it was aimed at the served bytes.

This refits the store's own per-trial rows against metafor. Until it returns, the tau2
on these pages is UNVALIDATED -- not wrong, UNVALIDATED.
"""
import io
import json
import math
import os

SHELL = r"F:\rapidmeta-ssot-shell"
Z = 1.959964
TARGETS = [
    ("apixaban-vte-prophylaxis", "major_vte"),
    ("apixaban-vte-treatment", "recurrent_vte"),
    ("bococizumab-lipid-review", "ldlc_pct_change_wk12"),
    ("azilsartan-chlorthalidone-vs-olmesartan-hctz", "sbp_change_wk8"),
]
RATIO = {"RR", "OR", "HR", "IRR", "RATE_RATIO", "RISK_RATIO",
         "ODDS_RATIO", "HAZARD_RATIO", "INCIDENCE_RATE_RATIO"}
DIFF = {"MD", "MEAN_DIFFERENCE", "SMD", "RD", "RISK_DIFFERENCE",
        "PERCENT_CHANGE", "MEAN_CHANGE"}

cases, notes = [], []
for topic, oid in TARGETS:
    p = os.path.join(SHELL, "ssot", topic, topic + ".json")
    if not os.path.exists(p):
        notes.append((topic, oid, "STORE_NOT_FOUND")); continue
    o = json.load(io.open(p, encoding="utf-8"))
    by = ((o.get("results") or {}).get("by_outcome") or {})
    r = by.get(oid)
    if not isinstance(r, dict):
        notes.append((topic, oid, "OUTCOME_ABSENT (present: %s)"
                      % ", ".join(sorted(by)[:6]))); continue
    pooled = r.get("pooled") or {}
    het = r.get("heterogeneity") or {}
    per = r.get("per_trial") or []
    measure = str(pooled.get("measure") or "").upper().replace(" ", "_")
    if measure in RATIO:
        log_scale = True
    elif measure in DIFF:
        log_scale = False
    else:
        notes.append((topic, oid, "MEASURE_UNKNOWN(%r) -- UNCOMPARABLE" % measure)); continue
    yi, sei = [], []
    ok = True
    for t in per:
        if not isinstance(t, dict):
            ok = False; break
        pt, lo, hi = t.get("point"), t.get("ci_low"), t.get("ci_high")
        try:
            lo, hi = float(lo), float(hi)
            if log_scale:
                if lo <= 0 or hi <= 0 or float(pt) <= 0:
                    ok = False; break
                yi.append(math.log(float(pt))); sei.append((math.log(hi) - math.log(lo)) / (2 * Z))
            else:
                yi.append(float(pt)); sei.append((hi - lo) / (2 * Z))
        except (TypeError, ValueError):
            ok = False; break
    if not ok or len(yi) < 2:
        notes.append((topic, oid, "PER_TRIAL_UNUSABLE (k=%s, rows=%d) -- UNVALIDATED"
                      % (r.get("k"), len(per)))); continue
    cases.append({"topic": topic, "outcome": oid, "measure": measure,
                  "log_scale": log_scale, "k": len(yi), "yi": yi, "sei": sei,
                  "store_tau2": het.get("tau2"), "store_point": pooled.get("point"),
                  "store_ci_low": pooled.get("ci_low"), "store_ci_high": pooled.get("ci_high")})

json.dump({"cases": cases}, io.open("store_cases.json", "w", encoding="utf-8"), indent=1)
print("STORE REFIT CASES (the SERVED surface)")
for c in cases:
    print("  %-28s %-22s k=%d measure=%-16s store_tau2=%s"
          % (c["topic"][:28], c["outcome"][:22], c["k"], c["measure"], c["store_tau2"]))
print()
if notes:
    print("NOT REFITTABLE -- reported as UNVALIDATED, never as clean:")
    for t, o, why in notes:
        print("  %-28s %-22s %s" % (t[:28], str(o)[:22], why))
