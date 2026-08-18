"""Reusable: pool binary outcomes read from ClinicalTrials.gov posted results.

WRITTEN ON THE THIRD OCCURRENCE, NOT FORECAST. The same log-risk-ratio + REML + Hartung-
Knapp code was written by hand for gepotidacin/lefamulin, then again for cabotegravir. A
third hand-written copy is where a pattern is paid for anyway, so it becomes a function.

WHAT IT SAVES, MEASURED RATHER THAN CLAIMED: ~40 lines of arithmetic per topic and, more
importantly, the four places that arithmetic can silently go wrong -- the SE formula, the
REML iteration, the Hartung-Knapp variance-inflation FLOOR (without which HK can NARROW
the interval below the unadjusted one, the documented HKSJ trap), and the t critical value
at k-1 degrees of freedom rather than a normal quantile.

WHAT IT DOES NOT DO, deliberately: it does not decide whether a topic is poolable. That is
a reading of four limbs against the registrations and it is not automatable. This function
is reached only AFTER that reading. It is arithmetic, not judgement.
"""
from __future__ import annotations
import math

Z = 1.959963985
# qt(0.975, df) for the small k this corpus actually produces
T_CRIT = {1: 12.7062047, 2: 4.3026527, 3: 3.1824463, 4: 2.7764451, 5: 2.5705818,
          6: 2.4469119, 7: 2.3646243, 8: 2.3060041, 9: 2.2621572}


def reml(y, v, iters: int = 500):
    """REML tau-squared, the Handbook 6.5 section 10.10.4.4 default."""
    w = [1.0 / x for x in v]
    sw = sum(w)
    mu = sum(a * b for a, b in zip(w, y)) / sw
    q = sum(a * (b - mu) ** 2 for a, b in zip(w, y))
    c = sw - sum(x * x for x in w) / sw
    t2 = max(0.0, (q - (len(y) - 1)) / c) if c > 0 else 0.0
    for _ in range(iters):
        w = [1.0 / (vi + t2) for vi in v]
        sw = sum(w)
        mu = sum(a * b for a, b in zip(w, y)) / sw
        num = sum((wi ** 2) * ((yi - mu) ** 2 - vi) for wi, yi, vi in zip(w, y, v))
        num += sum(x * x for x in w) / sw
        den = sum(x ** 2 for x in w)
        new = max(0.0, num / den) if den else 0.0
        if abs(new - t2) < 1e-14:
            t2 = new
            break
        t2 = new
    w = [1.0 / (vi + t2) for vi in v]
    sw = sum(w)
    return sum(a * b for a, b in zip(w, y)) / sw, math.sqrt(1.0 / sw), t2, q, w


def pool_rr(rows, exp_label="experimental", comp_label="comparator"):
    """rows: (nct, label, e1, n1, e2, n2). Returns (per_trial, pooled_block).

    Applies a 0.5 continuity correction ONLY where a cell is zero -- house rule; an
    unconditional correction biases the ratio toward 1.
    """
    y, v, per = [], [], []
    for nct, lab, e1, n1, e2, n2 in rows:
        a, b = float(e1), float(e2)
        corrected = False
        if e1 == 0 or e2 == 0 or e1 == n1 or e2 == n2:
            a, b, corrected = a + 0.5, b + 0.5, True
        lrr = math.log((a / n1) / (b / n2))
        se = math.sqrt(1.0 / a - 1.0 / n1 + 1.0 / b - 1.0 / n2)
        y.append(lrr)
        v.append(se * se)
        rec = {"trial_id": nct, "nct": nct, "label": lab,
               "registry": "ClinicalTrials.gov",
               "source_url": "https://clinicaltrials.gov/study/%s" % nct,
               "read_utc": "2026-08-18",
               "provenance": "REGISTRY -- ClinicalTrials.gov posted results",
               "as_posted": {exp_label + "_events": e1, exp_label + "_n": n1,
                             comp_label + "_events": e2, comp_label + "_n": n2},
               "measure": "RR", "point": round(math.exp(lrr), 4),
               "ci_low": round(math.exp(lrr - Z * se), 4),
               "ci_high": round(math.exp(lrr + Z * se), 4),
               "se_log_rr": round(se, 6), "derived_here": True,
               "how": ("RR = (e1/n1)/(e2/n2); SE(log RR) = sqrt(1/e1 - 1/n1 + 1/e2 - "
                       "1/n2), Handbook 6.5 section 6.4.1. Counts read from the "
                       "registry; only the arithmetic is ours and the formula is shown.")}
        if corrected:
            rec["continuity_correction"] = (
                "0.5 ADDED TO BOTH EVENT COUNTS because a cell was zero or complete. "
                "Applied ONLY in that case: an unconditional correction biases the ratio "
                "toward the null. The corrected value is what the interval is built from; "
                "as_posted holds the uncorrected registry counts.")
        per.append(rec)

    k = len(y)
    mu, se, t2, q, w = reml(y, v)
    infl = max(1.0, sum(wi * (yi - mu) ** 2 for wi, yi in zip(w, y)) / (k - 1))
    se_hk = math.sqrt(infl / sum(w))
    tc = T_CRIT.get(k - 1, 1.96)
    i2 = max(0.0, (q - (k - 1)) / q * 100) if q > 0 else 0.0

    # the direction test -- TAXONOMY-PUBLISHED-SYNTHESIS-ERRORS.md standing rule
    excl = [r["ci_low"] > 1 or r["ci_high"] < 1 for r in per]
    same = len({r["point"] > 1 for r in per}) == 1
    # GATED ON HIGH I-SQUARED. The rule is "when I-squared is HIGH, check direction" --
    # firing it at low I-squared labels agreeing trials a "substantive disagreement" purely
    # because one interval is wide, which manufactures the doubt the rule exists to prevent.
    # This gate was added after the unconditional version mislabelled a k=3 pool at I2=0.
    if i2 < 50:
        kind = ("NOT APPLICABLE -- I-squared is %.1f%%, below the threshold at which the "
                "direction test is informative. The trials are consistent with a common "
                "effect and no heterogeneity caution is warranted. Applying one here would "
                "manufacture doubt the data do not support, which is the mirror failure of "
                "ignoring heterogeneity that matters." % i2)
    elif all(excl) and same:
        kind = ("PRECISION -- I-squared is %.1f%%, but every trial interval excludes 1 and "
                "all point the same way. The trials agree on WHETHER and disagree on HOW "
                "MUCH. The pooled DIRECTION may be reported; the MAGNITUDE is not "
                "established." % i2)
    else:
        kind = ("SUBSTANTIVE -- I-squared is %.1f%% AND the trial intervals do not all "
                "exclude 1, or do not all point the same way. The trials disagree on "
                "WHETHER. THE POOLED POINT IS A NUMBER AND NOT A CONCLUSION." % i2)

    return per, {
        "measure": "RR", "k": k, "model": "random-effects", "estimator": "REML",
        "pooled": {"point": round(math.exp(mu), 4),
                   "ci_low": round(math.exp(mu - Z * se), 4),
                   "ci_high": round(math.exp(mu + Z * se), 4), "ci_level": 95},
        "pooled_hartung_knapp": {
            "point": round(math.exp(mu), 4),
            "ci_low": round(math.exp(mu - tc * se_hk), 4),
            "ci_high": round(math.exp(mu + tc * se_hk), 4),
            "df": k - 1, "t_critical": tc,
            "variance_inflation_applied": round(infl, 4),
            "why_it_is_shown": (
                "Handbook 6.5 section 10.10.4.5 recommends Hartung-Knapp where k is small. "
                "Shown ALONGSIDE the unadjusted interval, not instead of it. A FLOOR OF 1 "
                "is applied to the variance-inflation factor so the adjustment can never "
                "NARROW the interval below the unadjusted one.")},
        "heterogeneity": {
            "tau2": round(t2, 6), "q": round(q, 4), "df": k - 1,
            "i2_percent": round(i2, 1),
            "DIRECTION_TEST": kind,
            "how_to_read_this_at_low_k": (
                "At k=2 or k=3 these statistics are weak evidence about consistency in "
                "EITHER direction. A low value means the estimates are CONSISTENT WITH a "
                "common effect, not that one is demonstrated.")},
        "per_trial": per,
    }
