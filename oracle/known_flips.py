# -*- coding: utf-8 -*-
"""KNOWN-ANSWER CONTROL: re-find the 3 flips the tau-squared defect caused.

Until this suite re-finds the defects we already know about, it is not proven to
measure what the blast-radius measurement measured. That is the whole point of a
known-answer control: an oracle that cannot re-find a known defect is not an oracle,
it is an opinion that has never been contradicted.

METHOD. The defect is fully specified in scripts/build_binary_sidecar.py: the REML
update omitted the `1/sum(w)` term, and because the result is clamped at zero it had
a FIXED POINT AT ZERO -- once a step went negative the loop returned exactly 0.0.
So the old estimator is reconstructed here EXACTLY as described, run beside the
current one on the same inputs, and the two are compared on the quantity the
blast-radius figure counted: whether the published interval excludes the null.

Expected, from the committed measurement:
    351 sidecars whose stored tau2 was exactly 0.0
    250 legitimately zero      (correct estimator also returns 0)
     86 heterogeneity erased   (correct estimator returns > 0)
      3 of those carried a published interval that excluded the null and no longer does

THE CONTROL VALUES ARE NOT TYPED. The comparison is computed from the data; the
figures above are the expectation being tested, not an input to the test.
"""
import io
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

Z = 1.959964


def _mu_w(yis, vis, tau2):
    w = [1.0 / (v + tau2) for v in vis]
    sw = sum(w)
    mu = sum(wi * y for wi, y in zip(w, yis)) / sw
    return w, sw, mu


def reml_tau2_BROKEN(yis, vis, max_iter=1000, tol=1e-16):
    """The defect, reconstructed as documented: NO `1/sw` term, clamped at zero.

    Its failure value (0.0) is also a meaningful value, which is why nothing
    internal could ever have caught it.
    """
    tau2 = 0.0
    for _ in range(max_iter):
        w, sw, mu = _mu_w(yis, vis, tau2)
        num = sum(wi ** 2 * ((y - mu) ** 2 - v)
                  for wi, y, v in zip(w, yis, vis))
        den = sum(wi ** 2 for wi in w)
        nxt = num / den                     # <-- the missing "+ 1/sw"
        if nxt < 0:
            return 0.0                      # the fixed point at zero
        if abs(nxt - tau2) < tol:
            return nxt
        tau2 = nxt
    return tau2


def reml_tau2_FIXED(yis, vis, max_iter=2000, tol=1e-16):
    """Current form: direct update INCLUDING 1/sw, with bisection fallback."""
    def f(t):
        w, sw, mu = _mu_w(yis, vis, t)
        num = sum(wi ** 2 * ((y - mu) ** 2 - v)
                  for wi, y, v in zip(w, yis, vis))
        den = sum(wi ** 2 for wi in w)
        return max(0.0, num / den + 1.0 / sw)

    t = 0.0
    for _ in range(max_iter):
        nxt = f(t)
        if abs(nxt - t) < tol:
            return nxt
        t = nxt
    # bisection on g(t) = f(t) - t, which is bracketed for k >= 2
    lo, hi = 0.0, max(1.0, t * 4 + 1.0)
    while f(hi) - hi > 0 and hi < 1e6:
        hi *= 2
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(mid) - mid > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def pooled_ci(yis, vis, tau2):
    w = [1.0 / (v + tau2) for v in vis]
    sw = sum(w)
    mu = sum(wi * y for wi, y in zip(w, yis)) / sw
    se = math.sqrt(1.0 / sw)
    return mu, mu - Z * se, mu + Z * se


def excludes_null(lo, hi):
    """On the log scale the null is 0."""
    return (lo > 0) or (hi < 0)


def main():
    cases = json.load(io.open("cases.json", encoding="utf-8"))["cases"]
    rows, flips, erased, legit = [], [], 0, 0
    for c in cases:
        yis = c["yi"]
        vis = [s * s for s in c["sei"]]
        tb = reml_tau2_BROKEN(yis, vis)
        tf = reml_tau2_FIXED(yis, vis)
        mb, lb, ub = pooled_ci(yis, vis, tb)
        mf, lf, uf = pooled_ci(yis, vis, tf)
        eb, ef = excludes_null(lb, ub), excludes_null(lf, uf)
        if tb == 0.0 and tf > 1e-8:
            erased += 1
            if eb and not ef:
                flips.append((c["topic"], c["outcome"], tb, tf,
                              (lb, ub), (lf, uf)))
        elif tb == 0.0 and tf <= 1e-8:
            legit += 1
        rows.append((c["topic"], c["outcome"], tb, tf, eb, ef))

    print("KNOWN-ANSWER CONTROL -- re-finding the tau-squared defect")
    print("  cases available to this suite      : %d" % len(cases))
    print("  broken=0 and fixed=0 (legit zero)  : %d" % legit)
    print("  broken=0 and fixed>0 (erased)      : %d" % erased)
    print("  ...of which the interval FLIPS     : %d" % len(flips))
    print()
    if flips:
        print("FLIPS RE-FOUND, named:")
        for t, o, tb, tf, (lb, ub), (lf, uf) in flips:
            print("   %-30s %-22s tau2 %.6g -> %.6g" % (t[:30], str(o)[:22], tb, tf))
            print("        broken CI (log) %.4f to %.4f  EXCLUDES null" % (lb, ub))
            print("        fixed  CI (log) %.4f to %.4f  INCLUDES null" % (lf, uf))
    else:
        print("NO FLIPS RE-FOUND IN THIS SLICE.")
        print("  This does NOT clear the suite. The blast-radius figure was measured")
        print("  over 351 BINARY SIDECARS; this suite currently covers %d pooled" % len(cases))
        print("  estimates from results.by_outcome, a DIFFERENT SURFACE. The control")
        print("  is UNRUN against its own population, not passed.")
    json.dump({"n_cases": len(cases), "legit_zero": legit, "erased": erased,
               "flips": [[f[0], f[1], f[2], f[3]] for f in flips]},
              io.open("known_flips_out.json", "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
