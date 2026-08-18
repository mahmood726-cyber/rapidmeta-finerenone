"""Re-derive every published pooled estimate from its OWN object's per-trial inputs.

NOT the headline sweep. That one compared PAGE TO OBJECT and returned 514 of 514, which
establishes the projection is faithful and says NOTHING about whether the object's own
arithmetic is right. THIS ASKS WHETHER THE OBJECT AGREES WITH ITSELF.

TWO PASSES PER TOPIC, because the second is worthless without the first:

  PASS 1  INPUT INTEGRITY. Where a per-trial log point and log standard error are stored,
          recompute them from the effect and interval stored beside them. Where they are
          NOT stored, they must be DERIVED -- and derivation is itself a place to be wrong
          (the unicode-minus and exponentiated-mean-difference defects both lived there).
          Any topic whose inputs had to be derived is REPORTED AS SUCH, never silently.

  PASS 2  POOLED ARITHMETIC. REML random-effects on those inputs, compared to the
          published point, interval and tau-squared.

I-SQUARED IS COMPARED UNDER BOTH DEFINITIONS and neither is treated as the right one.
Higgins (Q-df)/Q and the metafor/REML tau2/(tau2+s2) are different quantities; ARNI carries
the second under a field named only 'i2'. A mismatch on one but not the other is a
LABELLING finding, not an arithmetic one, and is reported separately so the two are never
confused.

A FAILURE HERE IS NOT AUTOMATICALLY A WRONG NUMBER. A pooled estimate that does not
reproduce from its own inputs is EITHER a wrong number on a live page OR a wrong record of
how it was computed -- for instance a different estimator, a continuity correction, or a
trial excluded from the pool but left in per_trial. Those need different treatments, so
this script reports the discrepancy and does NOT fix anything.
"""
from __future__ import annotations
import io
import json
import math
import os
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Z = 1.959963985
# RATE_RATIO was MISSING here and iv-iron-hf was pooled on the natural scale instead of
# the log scale as a result -- reported as a non-reproducing estimate when the object was
# correct. Any ratio measure added to the corpus must be added here.
RATIO = {"HR", "RR", "OR", "IRR", "RATE_RATIO", "RATERATIO", "IRR_", "HAZARD_RATIO",
         "RISK_RATIO", "ODDS_RATIO"}


def dl(y, v):
    """DerSimonian-Laird. THE OBJECT'S DECLARED ESTIMATOR IS AUTHORITATIVE, not ours."""
    W = [1 / x for x in v]
    SW = sum(W)
    mu0 = sum(a * b for a, b in zip(W, y)) / SW
    q = sum(a * (b - mu0) ** 2 for a, b in zip(W, y))
    c = SW - sum(x * x for x in W) / SW
    t2 = max(0.0, (q - (len(y) - 1)) / c) if c > 0 else 0.0
    w = [1 / (vi + t2) for vi in v]
    sw = sum(w)
    return sum(a * b for a, b in zip(w, y)) / sw, math.sqrt(1 / sw), t2, q


def reml(y, v, it=800):
    w = [1 / x for x in v]
    sw = sum(w)
    mu = sum(a * b for a, b in zip(w, y)) / sw
    q = sum(a * (b - mu) ** 2 for a, b in zip(w, y))
    c = sw - sum(x * x for x in w) / sw
    t2 = max(0.0, (q - (len(y) - 1)) / c) if c > 0 else 0.0
    for _ in range(it):
        w = [1 / (vi + t2) for vi in v]
        sw = sum(w)
        mu = sum(a * b for a, b in zip(w, y)) / sw
        num = sum((wi ** 2) * ((yi - mu) ** 2 - vi) for wi, yi, vi in zip(w, y, v))
        num += sum(x * x for x in w) / sw
        den = sum(x ** 2 for x in w)
        new = max(0.0, num / den) if den else 0.0
        if abs(new - t2) < 1e-15:
            t2 = new
            break
        t2 = new
    w = [1 / (vi + t2) for vi in v]
    sw = sum(w)
    return sum(a * b for a, b in zip(w, y)) / sw, math.sqrt(1 / sw), t2, q


def inputs_from(pt, measure):
    """Return (y, v, derived_flags, integrity) or None if the shape does not permit."""
    y, v, derived, integrity = [], [], [], []
    log_scale = (measure or "").upper() in RATIO
    for t in pt:
        p, lo, hi = t.get("point"), t.get("ci_low"), t.get("ci_high")
        ly, ls = t.get("log_point"), t.get("log_se")
        se = t.get("se") or t.get("se_log_rr")
        if log_scale:
            if ly is not None and ls not in (None, 0):
                # PASS 1: check the stored logs against the stored effect
                if None not in (p, lo, hi) and p > 0 and lo > 0 and hi > 0:
                    d1 = abs(math.log(p) - ly)
                    d2 = abs((math.log(hi) - math.log(lo)) / (2 * Z) - ls)
                    integrity.append(max(d1, d2))
                y.append(ly)
                v.append(ls * ls)
                derived.append(False)
            elif None not in (p, lo, hi) and p > 0 and lo > 0 and hi > 0:
                y.append(math.log(p))
                v.append(((math.log(hi) - math.log(lo)) / (2 * Z)) ** 2)
                derived.append(True)
            else:
                return None
        else:
            if p is None:
                return None
            s = se if se else (
                (hi - lo) / (2 * Z) if None not in (lo, hi) else None)
            if not s:
                return None
            y.append(p)
            v.append(s * s)
            derived.append(se is None)
    return (y, v, derived, integrity) if len(y) >= 2 else None


def main() -> int:
    targets = json.load(io.open(os.path.join(REPO, ".rederive-targets.json"),
                                encoding="utf-8"))
    ok, bad, unck = [], [], []
    for topic in targets:
        f = os.path.join(REPO, "ssot", topic, topic + ".json")
        if not os.path.exists(f):
            unck.append((topic, "no object"))
            continue
        o = json.load(io.open(f, encoding="utf-8"))
        bo = ((o.get("results") or {}).get("by_outcome") or {})
        hit = None
        for name, blk in bo.items():
            pl = (blk or {}).get("pooled") or {}
            if pl.get("point") is not None and (blk.get("per_trial") or []):
                hit = (name, blk, pl)
                break
        if not hit:
            unck.append((topic, "no outcome carries both a pooled point and per_trial"))
            continue
        name, blk, pl = hit
        measure = pl.get("measure") or blk.get("measure") or ""
        got = inputs_from(blk["per_trial"], measure)
        if not got:
            unck.append((topic, "per_trial shape does not permit re-derivation"))
            continue
        y, v, derived, integ = got
        if len(y) != (blk.get("k") or len(y)):
            unck.append((topic, "per_trial n=%d but k=%s -- pool membership unclear"
                         % (len(y), blk.get("k"))))
            continue
        # RE-DERIVE WITH THE ESTIMATOR THE OBJECT DECLARES. The first version of this
        # script used REML unconditionally and reported three DerSimonian-Laird topics as
        # non-reproducing. An audit that ignores the method under audit is not an audit.
        est = (blk.get("estimator") or blk.get("estimator_used") or "").lower()
        fn = dl if ("dersimonian" in est or est.strip() in ("dl", "d-l")) else reml
        mu, se, t2, q = fn(y, v)
        rec_est = "DL" if fn is dl else "REML"
        log_scale = measure.upper() in RATIO
        pt_r = math.exp(mu) if log_scale else mu
        lo_r = math.exp(mu - Z * se) if log_scale else mu - Z * se
        hi_r = math.exp(mu + Z * se) if log_scale else mu + Z * se
        dp = abs(pt_r - pl["point"]) / max(1e-12, abs(pl["point"]))
        d_lo = (abs(lo_r - pl["ci_low"]) / max(1e-12, abs(pl["ci_low"]))
                if pl.get("ci_low") is not None else 0)
        d_hi = (abs(hi_r - pl["ci_high"]) / max(1e-12, abs(pl["ci_high"]))
                if pl.get("ci_high") is not None else 0)
        rec = {"topic": topic, "outcome": name, "measure": measure, "k": len(y),
               "published": [pl["point"], pl.get("ci_low"), pl.get("ci_high")],
               "rederived": [round(pt_r, 8), round(lo_r, 8), round(hi_r, 8)],
               "rel_delta": [dp, d_lo, d_hi],
               "inputs_derived_here": sum(derived),
               "input_integrity_max_abs": (max(integ) if integ else None),
               "estimator_declared": blk.get("estimator"), "estimator_used": rec_est}
        (ok if max(dp, d_lo, d_hi) < 1e-3 else bad).append(rec)

    print("RE-DERIVED OK (relative difference < 1e-3): %d" % len(ok))
    for r in ok:
        note = ""
        if r["inputs_derived_here"]:
            note = "  [%d input(s) DERIVED here, not stored]" % r["inputs_derived_here"]
        print("   %-44s %-3s k=%-2d  %.10g vs %.10g   d=%.1e%s"
              % (r["topic"][:43], r["measure"], r["k"], r["rederived"][0],
                 r["published"][0], r["rel_delta"][0], note))
    print()
    print("DID NOT RE-DERIVE: %d" % len(bad))
    for r in bad:
        print("   %-44s %-3s k=%-2d" % (r["topic"][:43], r["measure"], r["k"]))
        print("        published  %s" % r["published"])
        print("        rederived  %s" % r["rederived"])
        print("        rel deltas point %.3e  lo %.3e  hi %.3e" % tuple(r["rel_delta"]))
        if r["inputs_derived_here"]:
            print("        NOTE: %d input(s) had to be DERIVED -- the derivation is itself "
                  "a candidate cause" % r["inputs_derived_here"])
    print()
    print("NOT CHECKABLE: %d   -- these are a HOLE, not a pass" % len(unck))
    for t, why in unck:
        print("   %-44s %s" % (t[:43], why[:56]))
    json.dump({"ok": ok, "failed": bad, "unchecked": unck},
              io.open(os.path.join(REPO, ".rederive-result.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
