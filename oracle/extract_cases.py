# -*- coding: utf-8 -*-
"""Extract every pooled estimate we serve, as cases for the external oracle.

The oracle is R/metafor. This file does NOT compute anything statistical -- it only
lifts the per-trial inputs and the stored answer, so R can recompute independently.
A check that recomputed the estimate in Python would be a second implementation by
the same author reading the same fields, which verifies nothing.

METHOD IS CARRIED PER CASE AND MUST BE PINNED DOWNSTREAM. An estimate computed with
Hartung-Knapp compared against one computed without is TWO DIFFERENT QUANTITIES and
the difference reads as a real effect. Where the object does not state the method,
the case is marked METHOD_UNSTATED and is NOT compared -- it is reported as
uncomparable rather than silently compared under an assumption.

CONTROL VALUES ARE EXPORTED FROM THE DATA. Nothing here is typed by hand.
"""
import glob
import io
import json
import math
import os

SHELL = r"F:\rapidmeta-ssot-shell"
Z = 1.959964


def se_from_ci(lo, hi, log_scale):
    try:
        lo, hi = float(lo), float(hi)
    except (TypeError, ValueError):
        return None
    if lo <= 0 or hi <= 0:
        return None
    if log_scale:
        return (math.log(hi) - math.log(lo)) / (2 * Z)
    return (hi - lo) / (2 * Z)


def stated_method(res):
    """Read the method off the object. Never assume one."""
    for k in ("method", "pooling_method", "model"):
        v = res.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    p = res.get("pooled") or {}
    for k in ("method", "model", "estimator"):
        v = p.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    het = res.get("heterogeneity") or {}
    v = het.get("tau2_method") or het.get("method")
    return v.strip() if isinstance(v, str) and v.strip() else None


def hksj_flag(res):
    p = res.get("pooled") or {}
    for src in (res, p, res.get("heterogeneity") or {}):
        for k in ("hksj", "knha", "hartung_knapp"):
            if k in src:
                return bool(src[k])
    return None


def main():
    cases, skipped = [], []
    for f in sorted(glob.glob(os.path.join(SHELL, "ssot", "*", "*.json"))):
        topic = os.path.basename(os.path.dirname(f))
        try:
            o = json.load(io.open(f, encoding="utf-8"))
        except Exception as e:
            skipped.append((topic, "UNREADABLE", repr(e)[:50]))
            continue
        if not isinstance(o, dict):
            continue
        res = o.get("results")
        by = res.get("by_outcome") if isinstance(res, dict) else None
        if not isinstance(by, dict):
            continue
        for oid, r in by.items():
            if not isinstance(r, dict):
                continue
            pooled = r.get("pooled")
            if not isinstance(pooled, dict) or pooled.get("point") is None:
                continue
            per = r.get("per_trial") or []
            if not isinstance(per, list) or len(per) < 2:
                skipped.append((topic, oid, "NO_PER_TRIAL(k=%s)" % r.get("k")))
                continue
            measure = str(pooled.get("measure") or "").upper().replace(" ", "_")
            # RATIO measures MUST be pooled on the log scale and back-transformed.
            # The first version of this list omitted RATE_RATIO, so iv-iron-hf was
            # handed raw ratios and metafor -- correctly -- pooled them on the
            # natural scale. That produced a 2.24e-03 "disagreement" on a flagship
            # page that was entirely MY defect, and it is the exact failure this
            # project's own rule warns about: natural scale + random effects is a
            # Simpson trap. An UNKNOWN measure is now UNCOMPARABLE, never assumed.
            RATIO = {"RR", "OR", "HR", "IRR", "RATE_RATIO", "RISK_RATIO",
                     "ODDS_RATIO", "HAZARD_RATIO", "INCIDENCE_RATE_RATIO"}
            DIFF = {"MD", "MEAN_DIFFERENCE", "SMD", "RD", "RISK_DIFFERENCE"}
            if measure in RATIO:
                log_scale = True
            elif measure in DIFF:
                log_scale = False
            else:
                skipped.append((topic, oid, "MEASURE_UNKNOWN(%r) -- UNCOMPARABLE,"
                                            " not assumed" % measure))
                continue
            yi, sei, ids = [], [], []
            bad = False
            for t in per:
                if not isinstance(t, dict):
                    bad = True
                    break
                pt = t.get("point")
                s = se_from_ci(t.get("ci_low"), t.get("ci_high"), log_scale)
                if pt is None or s is None or s <= 0:
                    bad = True
                    break
                try:
                    y = math.log(float(pt)) if log_scale else float(pt)
                except (TypeError, ValueError):
                    bad = True
                    break
                yi.append(y)
                sei.append(s)
                ids.append(str(t.get("trial") or t.get("id") or t.get("name") or "?"))
            if bad or len(yi) < 2:
                skipped.append((topic, oid, "PER_TRIAL_UNUSABLE"))
                continue
            het = r.get("heterogeneity") or {}
            cases.append({
                "topic": topic, "outcome": oid, "measure": measure,
                "log_scale": log_scale, "k": len(yi),
                "yi": yi, "sei": sei, "trials": ids,
                "stored_point": pooled.get("point"),
                "stored_ci_low": pooled.get("ci_low"),
                "stored_ci_high": pooled.get("ci_high"),
                "stored_tau2": het.get("tau2"),
                "stored_i2": het.get("i2"),
                "stated_method": stated_method(r),
                "stated_hksj": hksj_flag(r),
            })
    out = {"n_cases": len(cases), "n_skipped": len(skipped),
           "cases": cases, "skipped": skipped[:200]}
    json.dump(out, io.open("cases.json", "w", encoding="utf-8"), indent=1)
    unstated = sum(1 for c in cases if not c["stated_method"])
    print("pooled estimates extracted : %d" % len(cases))
    print("skipped (named, not hidden): %d" % len(skipped))
    print("METHOD_UNSTATED            : %d  <- reported uncomparable, never assumed"
          % unstated)
    from collections import Counter
    print("measures:", dict(Counter(c["measure"] for c in cases)))
    print("k range :", min(c["k"] for c in cases), "-", max(c["k"] for c in cases))


if __name__ == "__main__":
    main()
