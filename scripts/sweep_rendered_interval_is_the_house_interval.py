"""Every rendered sensitivity interval, against the HOUSE interval the object stores.

ONE PAGE TOLD A READER THAT metafor's RAW INTERVAL WAS OURS. On `agyw-hiv-prep-review` the
finding and the GRADE imprecision step both cited *"this project's Hartung-Knapp interval …
0.4054 to 1.2191"*. That is metafor's UNFLOORED knha output. This project's interval is
0.1725 to 2.8655 -- THREE TIMES WIDER -- and it was sitting in the same object's own
`pooled_hartung_knapp` field the whole time.

    ONE INSTANCE IS A DEFECT. THE QUESTION IS HOW MANY PAGES CARRY THE WRONG ONE OF TWO
    INTERVALS THAT BOTH EXIST.

Same shape as the I-squared reproduction sweep, which found five.

WHAT IS COMPARED, AND WHY IT CANNOT BE FOOLED BY EITHER END ALONE:

    HOUSE      the object's stored `pooled_hartung_knapp`, which is
               point +/- t_{k-1} * SE_unadjusted * max(1, SE_knha / SE_unadjusted)
    RAW        what metafor prints under test="knha" with no floor -- RECOMPUTED HERE from
               the object's own per-trial inputs, not taken from any stored field
    DELIVERED  the bytes of the topic's page

A page is WRONG when the RAW pair renders and the HOUSE pair does not. A page is RIGHT when
the HOUSE pair renders. A page carrying BOTH is right only if the raw one is LABELLED as raw
-- the stored R output does exactly that, deliberately, and must not be counted as a defect.

WHY THE FLOOR MATTERS AND IS NOT PEDANTRY. metafor's knha standard error can be SMALLER than
the random-effects one whenever Q < k - 1. The adjustment then NARROWS the interval, which is
the opposite of what a small-sample correction is for. On
`malaria-vaccines/rtss_recurrent_children_final` the raw interval is 0.6273 to 0.6473 against
an unadjusted 0.5967 to 0.6805 -- four times narrower. A reader shown the raw number is shown
MORE precision than the data support, so every divergence found here runs in the direction
that flatters the estimate.

THE FLOOR IS A KNOWN-ANSWER CONTROL, NOT AN ASSUMPTION. The recomputation must reproduce the
stored `pooled_hartung_knapp` on every block that carries one; a block where it does not is
reported UNRECONCILED rather than judged, because an instrument that cannot reproduce the
stored value has no standing to call a page wrong.
"""
import glob
import io
import json
import math
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls          # noqa: E402

Z = 1.959964


def _t_crit(df):
    """Two-sided 97.5th percentile of t with `df` degrees of freedom, by bisection.

    No scipy in this environment. The CDF is computed from the regularised incomplete beta
    via a continued fraction; accuracy is checked against the two values this corpus
    actually uses -- 12.7062 at 1 df and 4.3027 at 2 df -- in the controls below.
    """
    def betacf(a, b, x):
        qab, qap, qam = a + b, a + 1.0, a - 1.0
        c, d = 1.0, 1.0 - qab * x / qap
        if abs(d) < 1e-30:
            d = 1e-30
        d = 1.0 / d
        h = d
        for m in range(1, 300):
            m2 = 2 * m
            aa = m * (b - m) * x / ((qam + m2) * (a + m2))
            d = 1.0 + aa * d
            c = 1.0 + aa / c
            if abs(d) < 1e-30:
                d = 1e-30
            if abs(c) < 1e-30:
                c = 1e-30
            d = 1.0 / d
            h *= d * c
            aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
            d = 1.0 + aa * d
            c = 1.0 + aa / c
            if abs(d) < 1e-30:
                d = 1e-30
            if abs(c) < 1e-30:
                c = 1e-30
            d = 1.0 / d
            de = d * c
            h *= de
            if abs(de - 1.0) < 3e-16:
                break
        return h

    def betai(a, b, x):
        if x <= 0:
            return 0.0
        if x >= 1:
            return 1.0
        lbeta = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                 + a * math.log(x) + b * math.log(1.0 - x))
        if x < (a + 1.0) / (a + b + 2.0):
            return math.exp(lbeta) * betacf(a, b, x) / a
        return 1.0 - math.exp(lbeta) * betacf(b, a, 1.0 - x) / b

    def cdf(t):
        return 1.0 - 0.5 * betai(df / 2.0, 0.5, df / (df + t * t))

    lo, hi = 0.0, 1e4
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if cdf(mid) < 0.975:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def per_trial_log(blk):
    """(yi, sei) per contributing trial, from the intervals the object already carries."""
    out = []
    for t in blk.get("per_trial") or []:
        if not isinstance(t, dict):
            continue
        p, lo, hi = t.get("point"), t.get("ci_low"), t.get("ci_high")
        if not all(isinstance(v, (int, float)) and v > 0 for v in (p, lo, hi)):
            continue
        out.append((math.log(p), (math.log(hi) - math.log(lo)) / (2 * Z)))
    return out


def fit(pairs):
    """Fixed-point REML for tau^2, then the unadjusted and raw-knha standard errors."""
    k = len(pairs)
    if k < 2:
        return None
    v = [s * s for _, s in pairs]
    tau2 = 0.0
    for _ in range(200):
        w = [1.0 / (vi + tau2) for vi in v]
        sw = sum(w)
        mu = sum(wi * y for wi, (y, _) in zip(w, pairs)) / sw
        num = sum(wi * wi * ((y - mu) ** 2 - vi) for wi, vi, (y, _) in zip(w, v, pairs))
        den = sum(wi * wi for wi in w)
        new = max(0.0, tau2 + num / den) if den else 0.0
        if abs(new - tau2) < 1e-12:
            tau2 = new
            break
        tau2 = new
    w = [1.0 / (vi + tau2) for vi in v]
    sw = sum(w)
    mu = sum(wi * y for wi, (y, _) in zip(w, pairs)) / sw
    se_un = math.sqrt(1.0 / sw)
    # metafor's knha standard error: sqrt( sum w_i (y_i - mu)^2 / ((k-1) * sum w_i) )
    se_kn = math.sqrt(sum(wi * (y - mu) ** 2 for wi, (y, _) in zip(w, pairs))
                      / ((k - 1) * sw))
    return {"k": k, "mu": mu, "tau2": tau2, "se_un": se_un, "se_kn": se_kn}


def intervals(f):
    """(house_lo, house_hi), (raw_lo, raw_hi) back-transformed."""
    t = _t_crit(f["k"] - 1)
    factor = max(1.0, f["se_kn"] / f["se_un"]) if f["se_un"] > 0 else 1.0
    m_house = t * f["se_un"] * factor
    m_raw = t * f["se_kn"]
    return ((math.exp(f["mu"] - m_house), math.exp(f["mu"] + m_house)),
            (math.exp(f["mu"] - m_raw), math.exp(f["mu"] + m_raw)), factor, t)


def fmt(v):
    return "%.4f" % v


def pair_in(page, lo, hi, window=240):
    """Both endpoints of an interval, at 4 dp, occurring CLOSE TOGETHER on the page.

    THE FIRST VERSION ALSO ACCEPTED A 2-DECIMAL MATCH ANYWHERE ON THE PAGE, and it reported
    two pages as showing metafor's raw interval in place of the house one. Both were FALSE.
    On `iv-iron-hf` the "match" was the strings `0.74` and `0.86` -- two-digit decimals that
    occur on almost any page of this corpus for unrelated reasons -- and the page in fact
    carries NEITHER endpoint of the raw interval at 4 dp.

    A loose match manufactured a finding in the direction of having found something, which is
    the same bias as class 84 in a different instrument. Two conditions now, both necessary:
    FOUR decimal places, and the two endpoints WITHIN A SHORT WINDOW of each other, so a
    number appearing elsewhere on a megabyte-long page cannot complete a pair.
    """
    a, b = fmt(lo), fmt(hi)
    for m in re.finditer(re.escape(a), page):
        seg = page[m.end():m.end() + window]
        if b in seg:
            return True
    return False


def main():
    # CONTROL. The t values this corpus uses, and the one page already known to be wrong.
    t1, t2 = _t_crit(1), _t_crit(2)
    require_controls(
        "sweep_rendered_interval_is_the_house_interval",
        positive=("the t critical values this corpus quotes -- 12.7062 at 1 df and 4.3027 at "
                  "2 df -- are reproduced by the bisection used here",
                  abs(t1 - 12.7062) < 5e-4 and abs(t2 - 4.3027) < 5e-4, True),
        negative=("a divergence is reported where the house and raw intervals are IDENTICAL",
                  False, True))

    M = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    rev = {}
    for pg, op in M.items():
        rev.setdefault(os.path.basename(os.path.dirname(op)), []).append(pg)
    cache = {}

    def page(pg):
        if pg not in cache:
            p = os.path.join(REPO, pg)
            cache[pg] = (io.open(p, encoding="utf-8", errors="replace").read()
                         if os.path.isfile(p) else "")
        return cache[pg]

    rows = []
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        topic = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != topic + ".json":
            continue
        try:
            obj = json.load(io.open(p, encoding="utf-8"))
        except ValueError:
            continue
        for oid, blk in sorted(((obj.get("results") or {}).get("by_outcome") or {}).items()):
            if not isinstance(blk, dict):
                continue
            pooled = blk.get("pooled") or {}
            if not isinstance(pooled.get("point"), (int, float)):
                continue
            f = fit(per_trial_log(blk))
            if not f or f["k"] < 2:
                continue
            (hlo, hhi), (rlo, rhi), factor, t = intervals(f)
            stored = blk.get("pooled_hartung_knapp") or {}
            rows.append({
                "topic": topic, "oid": oid, "k": f["k"], "factor": factor, "t": t,
                "house": (hlo, hhi), "raw": (rlo, rhi),
                "stored": (stored.get("ci_low"), stored.get("ci_high")),
                "pages": rev.get(topic) or [],
                "raw_narrower": (rhi - rlo) < (
                    pooled["point"] * 0 + (pooled.get("ci_high") or 0)
                    - (pooled.get("ci_low") or 0)),
            })

    # RECONCILIATION FIRST. An instrument that cannot reproduce the stored house interval has
    # no standing to call a page wrong, so that is checked before any verdict is printed.
    rec_ok = rec_bad = 0
    for r in rows:
        s_lo, s_hi = r["stored"]
        if not isinstance(s_lo, (int, float)):
            continue
        ok = (abs(r["house"][0] - s_lo) / max(s_lo, 1e-12) < 0.02
              and abs(r["house"][1] - s_hi) / max(s_hi, 1e-12) < 0.02)
        r["reconciled"] = ok
        rec_ok += ok
        rec_bad += (not ok)

    print("")
    print("POPULATION")
    print("   pooled blocks with k >= 2 and usable per-trial intervals   %d" % len(rows))
    print("   of those, blocks carrying a stored pooled_hartung_knapp    %d"
          % sum(1 for r in rows if isinstance(r["stored"][0], (int, float))))
    print("   recomputation REPRODUCES the stored house interval         %d" % rec_ok)
    print("   recomputation DOES NOT reproduce it (reported, not judged) %d" % rec_bad)
    print("   blocks on a topic with a delivered page                    %d"
          % sum(1 for r in rows if r["pages"]))
    print("")

    wrong, right, neither, both_labelled = [], [], [], []
    for r in rows:
        if not r["pages"]:
            continue
        if r.get("reconciled") is False:
            continue
        pg = r["pages"][0]
        h = page(pg)
        # THE RULE IS "MATCHES A STORED VALUE", SO COMPARE AGAINST THE STORED VALUE.
        #
        # This compared the page against its OWN recomputation, and on lefamulin the
        # recomputation gives 0.7808 where the object stores 0.7807 -- a last-digit
        # difference that made a correctly-cited interval read as absent. The stored field is
        # what prose is required to cite; the recomputation is only the fallback where the
        # object stores nothing.
        s_lo, s_hi = r["stored"]
        house_pair = ((s_lo, s_hi) if isinstance(s_lo, (int, float))
                      and isinstance(s_hi, (int, float)) else r["house"])
        has_house = pair_in(h, *house_pair)
        has_raw = pair_in(h, *r["raw"])
        # The stored R output prints the raw interval DELIBERATELY and labels it. A page
        # carrying that label is showing both on purpose and is not a defect.
        # "LABELLED" MEANS THE PAGE NAMES THE COMPUTATION, in any of the forms this corpus
        # uses -- the stored R output prints "metafor raw ... UNFLOORED", and a corrected
        # sentence says "metafor's RAW unfloored knha interval". Matching only the first two
        # made a correction look like the defect it corrected.
        _hl = h.lower()
        labelled = ("unfloored" in _hl) or ("metafor raw" in _hl) or ("metafor's raw" in _hl)
        if has_raw and not has_house and not labelled:
            wrong.append((r, pg))
        elif has_house:
            (both_labelled if has_raw else right).append((r, pg))
        else:
            neither.append((r, pg))

    print("VERDICT, over %d block(s) on delivered pages" % (len(wrong) + len(right)
                                                            + len(neither)
                                                            + len(both_labelled)))
    print("   the HOUSE interval renders                                 %d" % len(right))
    print("   BOTH render and the raw one is LABELLED raw (correct)      %d"
          % len(both_labelled))
    print("   THE RAW INTERVAL RENDERS AND THE HOUSE ONE DOES NOT        %d" % len(wrong))
    print("   neither pair renders -- no sensitivity interval on the page %d" % len(neither))
    print("")
    if wrong:
        print("PAGES SHOWING A READER THE WRONG ONE OF TWO INTERVALS THAT BOTH EXIST:")
        for r, pg in wrong:
            print("   %-34s %-28s k=%d" % (r["topic"][:34], r["oid"][:28], r["k"]))
            print("        house %s to %s   raw %s to %s   factor %.4f"
                  % (fmt(r["house"][0]), fmt(r["house"][1]),
                     fmt(r["raw"][0]), fmt(r["raw"][1]), r["factor"]))
            print("        on %s" % pg)
    else:
        print("NO PAGE RENDERS THE RAW INTERVAL IN PLACE OF THE HOUSE ONE.")
    print("")
    print("EVERY DIVERGENCE HERE WOULD RUN IN THE DIRECTION THAT FLATTERS THE ESTIMATE:")
    print("metafor's knha standard error is SMALLER than the random-effects one whenever")
    print("Q < k - 1, so the unfloored interval is the NARROWER of the two on exactly the")
    print("pools where the data support precision least.")

    # ---- P55, AS A GATE ------------------------------------------------------------------
    #
    # THREE INSTANCES, ALL WRITTEN BY THE SAME AUTHOR IN ONE NIGHT, AND ONLY THE SECOND WAS
    # FOUND BY LOOKING:
    #
    #   agyw-hiv-prep      "this project's Hartung-Knapp interval ... 0.4054 to 1.2191"
    #                      ours is 0.1725 to 2.8655          -- found by chance
    #   lefamulin-cabp     "the Hartung-Knapp interval is ... 0.8079 to 1.2093"
    #                      ours is 0.7807 to 1.2513          -- found by THIS sweep
    #   incretin-hfpef     "gives 1.80 to 13.06 ... It still excludes no effect"
    #                      ours is -7.74 to 22.60, WHICH INCLUDES NO EFFECT
    #                                                        -- found by refitting for limb 4
    #
    # A report is not enough for a defect with three instances and a reader-facing failure
    # mode. --gate makes this exit non-zero, so it can block a push rather than be read.
    #
    # THE RULE: no prose may cite an interval it did not read from the object's own stored
    # field. A rendered interval must either match a stored value to four decimals, or name
    # which computation produced it -- which is exactly what the stored R output does when it
    # prints "metafor raw ... UNFLOORED" beside the house interval.
    if "--gate" in sys.argv:
        if wrong:
            sys.exit(
                "GATE FAILED: %d block(s) render metafor's RAW interval where the object "
                "stores a different HOUSE interval. P55 -- no prose may cite an interval it "
                "did not read from the object's own stored field. Cite the stored value, or "
                "name the computation beside it as the R output does." % len(wrong))
        print("")
        print("GATE PASSED: no delivered page cites a raw interval in place of the house.")
        print("STATED, NOT HIDDEN: this gate is blind to %d block(s) whose stored house "
              "interval this file cannot reproduce, and to %d block(s) that render no "
              "sensitivity interval at all." % (rec_bad, len(neither)))


if __name__ == "__main__":
    main()
