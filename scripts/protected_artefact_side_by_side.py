r"""ARNI and the HFrEF NMA: served versus corrected, on one screen.

WHAT THIS COMPARES, AND WHY IT IS THE RIGHT COMPARISON
    The authorised change is the ESTIMATOR. The trials do not change. So the
    honest "new" for these two artefacts is: the SAME stored trial rows,
    pooled with the corrected REML tau-squared.

    That matters because neither of these can be rebuilt from its page.
    ARNI's page is ARNI_HF_REVIEW.html (the generator globs *_FULL_REVIEW.html,
    so it is not even a target) and it extracts ZERO trials; the served
    sidecar claims k=3. So a rebuild-from-page comparison does not exist for
    either, and manufacturing one would mean pulling numbers from somewhere
    else and calling them "new".

    Recomputing from the stored rows is not a workaround. It isolates
    exactly the quantity under decision and holds everything else fixed.

WHAT IS NOT SHOWN
    Any claim that the corrected pool is the right answer for the question.
    Only that the served interval was produced by an estimator that could
    not report heterogeneity, and what the same trials give once it can.

NOTHING IS WRITTEN. This reads and prints.
"""
from __future__ import annotations
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from absolute_effects_sidecar import reml_tau2, reml_tau2_historic  # noqa
from build_binary_sidecar import t_quantile_975  # noqa

SERVED = os.path.join(ROOT, "outputs", "r_validation")

TARGETS = [
    ("ARNI_HF", "ARNI / sacubitril-valsartan"),
    ("HF_QUADRUPLE_NMA", "HFrEF quadruple therapy NMA"),
]


def pool(ys, vs, tau2):
    k = len(ys)
    w = [1.0 / (v + tau2) for v in vs]
    sw = sum(w)
    mu = sum(a * b for a, b in zip(w, ys)) / sw
    q = sum(a * (y - mu) ** 2 for a, y in zip(w, ys)) / (k - 1)
    se = math.sqrt(max(q, 1.0) / sw)
    t = t_quantile_975(k - 1)
    return mu, mu - t * se, mu + t * se


def line(label, a, b, flag=""):
    print("  %-22s %20s   %20s%s" % (label, a, b, flag))


def show(stem, human):
    path = os.path.join(SERVED, stem + ".json")
    print("=" * 78)
    print("%s   (%s.json)" % (human, stem))
    if not os.path.exists(path):
        print("  NO SERVED SIDECAR -- nothing to decide for this artefact.")
        return
    d = json.load(open(path, encoding="utf-8"))
    rows = [t for t in (d.get("trials") or [])
            if isinstance(t.get("yi"), (int, float))
            and isinstance(t.get("vi"), (int, float)) and t["vi"] > 0]
    if len(rows) < 2:
        print("  fewer than 2 usable trial rows (k=%d) -- no pool." % len(rows))
        return
    ys = [t["yi"] for t in rows]
    vs = [t["vi"] for t in rows]
    t_old = d.get("tau2")
    t_new = reml_tau2(ys, vs)
    mu_o, lo_o, hi_o = pool(ys, vs, t_old or 0.0)
    mu_n, lo_n, hi_n = pool(ys, vs, t_new)
    ex_o = not (lo_o <= 0.0 <= hi_o)
    ex_n = not (lo_n <= 0.0 <= hi_n)

    print("  trials (unchanged, %d):" % len(rows))
    for t in rows:
        print("      %-16s %s/%s vs %s/%s"
              % (str(t.get("name") or t.get("nct"))[:16], t.get("tE"),
                 t.get("tN"), t.get("cE"), t.get("cN")))
    print("")
    line("", "SERVED", "CORRECTED")
    line("tau-squared", "%.8g" % (t_old or 0.0), "%.8g" % t_new,
         "   <-- moved" if abs((t_old or 0.0) - t_new) > 1e-12 else "")
    line("odds ratio", "%.4f" % math.exp(mu_o), "%.4f" % math.exp(mu_n),
         "   <-- moved" if abs(mu_o - mu_n) > 1e-9 else "")
    line("95% interval",
         "%.4f to %.4f" % (math.exp(lo_o), math.exp(hi_o)),
         "%.4f to %.4f" % (math.exp(lo_n), math.exp(hi_n)))
    line("excludes OR = 1", str(ex_o), str(ex_n),
         "   <-- CONCLUSION CHANGES" if ex_o != ex_n else "")
    print("")
    if ex_o != ex_n:
        print("  DECISION: the served interval and the corrected one disagree")
        print("  about whether this pool excludes no-effect.")
    elif abs(mu_o - mu_n) > 1e-9:
        print("  DECISION: the estimate moves but the conclusion does not.")
    else:
        print("  DECISION: nothing moves. The served value already reflects")
        print("  the corrected estimator, so there is nothing to swap here.")
    print("  Rebuild-from-page is NOT possible for this artefact; the")
    print("  comparison above holds the trials fixed and changes only the")
    print("  estimator, which is exactly the authorised change.")


def main():
    print("PROTECTED ARTEFACTS -- SERVED vs CORRECTED ESTIMATOR")
    print("Same trial rows in both columns. Nothing is written or replaced.\n")
    for stem, human in TARGETS:
        show(stem, human)
        print("")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
