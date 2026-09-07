# -*- coding: utf-8 -*-
"""Modified Hartung-Knapp-Sidik-Jonkman interval with an EXPLICIT variance-inflation floor.

The reviewer audit found SGLT2 serving a Wald interval while the abstract called it HKSJ, and
"modified HKSJ" alone is ambiguous: metafor's `test="knha"` applies NO floor, so at tau2=0 with
Q/(k-1)<1 its multiplier is <1 and it NARROWS the interval (0.733-0.817). The protocol's modified
HKSJ FLOORS the multiplier at 1 -- so only the quantile changes (z -> t_{k-1}) and the interval WIDENS
(0.695-0.862). Naming the floor, the quantile and the multiplier is the whole point; this module is the
one definition, with a locked fixture so it can never drift again.

DEFINITION (write this into the protocol verbatim):
  SE_pooled from the random-effects fit; multiplier q = max(1, Q/(k-1)) -- FLOORED at 1, never below;
  quantile t_{k-1} at 0.975; interval = exp( log(theta) +/- t_{k-1} * sqrt(q) * SE_pooled ).
"""
from __future__ import annotations
import io, math, sys

from statistics import NormalDist

# Exact two-sided 0.975 Student-t quantiles for df 1..30 (R qt(.975, df)); covers k up to 31.
# For a meta-analysis this is every realistic case; beyond df=30 the normal approximation is used.
_T975 = {
    1: 12.706205, 2: 4.302653, 3: 3.182446, 4: 2.776445, 5: 2.570582, 6: 2.446912,
    7: 2.364624, 8: 2.306004, 9: 2.262157, 10: 2.228139, 11: 2.200985, 12: 2.178813,
    13: 2.160369, 14: 2.144787, 15: 2.131450, 16: 2.119905, 17: 2.109816, 18: 2.100922,
    19: 2.093024, 20: 2.085963, 21: 2.079614, 22: 2.073873, 23: 2.068658, 24: 2.063899,
    25: 2.059539, 26: 2.055529, 27: 2.051831, 28: 2.048407, 29: 2.045230, 30: 2.042272,
}


def _t_quantile(df, p=0.975):
    if p != 0.975:
        raise ValueError("only the 0.975 quantile is tabulated (two-sided 95%% CI)")
    if df in _T975:
        return _T975[df]
    # df > 30: t is within ~1e-3 of z; the floor/quantile distinction that matters is at small k.
    return NormalDist().inv_cdf(p) * (1 + 1.0 / (4 * df))


def modified_hksj(log_theta, se_pooled, Q, k, level=0.975):
    """Return (lo, hi) on the RATIO scale for the floored modified HKSJ interval.

    log_theta : pooled effect on the log scale (e.g. log(0.7738))
    se_pooled : SE of the pooled effect from the RE fit (the fixed/Wald SE when tau2=0)
    Q, k      : Cochran's Q and the number of studies (df = k-1)
    """
    df = k - 1
    if df < 1:
        raise ValueError("modified HKSJ undefined for k<2")
    q = max(1.0, Q / df)                       # FLOOR at 1 -- the whole difference from metafor
    t = _t_quantile(df, level)
    half = t * math.sqrt(q) * se_pooled
    return math.exp(log_theta - half), math.exp(log_theta + half), {"q": q, "t": t, "df": df, "half_width_log": half}


def se_from_ci(point, lo, hi, z=1.959963985):
    """Recover the log-scale SE from a ratio-scale Wald CI."""
    return (math.log(hi) - math.log(lo)) / (2 * z)


def _selftest():
    ok, rows = True, []
    def chk(name, cond):
        nonlocal ok; ok &= bool(cond); rows.append((name, "OK" if cond else "*** FAIL ***"))

    # LOCKED FIXTURE: SGLT2 k=4 -- point 0.7738, Wald 0.7243-0.8268, Q=0.7698, k=4.
    # The reviewer's arithmetic: SE=0.0337797, t(3)=3.182446, half=0.1074958 -> 0.694917-0.861641.
    se = se_from_ci(0.7738, 0.7243, 0.8268)
    chk("SE recovered from SGLT2 Wald CI ~ 0.03378", abs(se - 0.0337797) < 5e-5)
    t3 = _t_quantile(3, 0.975)
    chk("t(3, .975) ~ 3.182446", abs(t3 - 3.182446) < 5e-4)
    lo, hi, info = modified_hksj(math.log(0.7738), se, Q=0.7698, k=4)
    chk("floor engaged: q = max(1, 0.7698/3) = 1", abs(info["q"] - 1.0) < 1e-9)
    chk("SGLT2 modified HKSJ lower ~ 0.6949", abs(lo - 0.694917) < 1e-3)
    chk("SGLT2 modified HKSJ upper ~ 0.8616", abs(hi - 0.861641) < 1e-3)
    # It must be WIDER than Wald (0.7243-0.8268) and than metafor's unfloored knha (0.7328-0.8171).
    chk("wider than Wald (floored HKSJ widens, not narrows)", lo < 0.7243 and hi > 0.8268)
    chk("wider than metafor unfloored knha (0.7328-0.8171)", lo < 0.7328 and hi > 0.8171)
    # A high-heterogeneity case where Q/(k-1) > 1: the floor does NOT engage (q>1), interval still valid.
    lo2, hi2, info2 = modified_hksj(math.log(0.80), 0.05, Q=20.0, k=5)
    chk("floor does not engage when Q/(k-1)>1 (q>1)", info2["q"] > 1.0)
    return ok, rows


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    ok, rows = _selftest()
    print("modified_hksj selftest (locked SGLT2 fixture: 0.6949-0.8616)")
    for n, v in rows:
        print("  %-56s %s" % (n, v))
    print("\n%s" % ("ALL PASS" if ok else "FAILURES ABOVE"))
    raise SystemExit(0 if ok else 1)
