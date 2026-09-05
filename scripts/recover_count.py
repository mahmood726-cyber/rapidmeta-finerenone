#!/usr/bin/env python
"""Arithmetic recovery of an arm-level integer count from a posted proportion or
percentage and a denominator, with a ROUNDING-UNIQUENESS test.

This is the single highest-yield extraction rule measured to date: it recovered
730 of 1,009 arm-level values that the naive extractor left on the floor. It is
NOT a new method -- apixaban-vte-prophylaxis already carried it, by hand, before
today ("The registry posts 0.47% on 3184. Exactly one integer rounds to that at
the posted precision, so the count is determined: 15."). This generalises that
existing, validated practice.

THE RULE. A registry posts a proportion (or percentage) at some precision and a
denominator N. The true numerator is an integer k in [0, N]. Accept k ONLY where
exactly ONE integer, rounded at the posted precision, reproduces the posted value.
Where more than one integer qualifies, the value is AMBIGUOUS and is refused, not
guessed. Every accepted value is a DERIVATION and carries its admissible interval.

TWO TRAPS, both encoded and tested:
  1. READ THE UNIT. AMPLIFY posts "proportion of participants = 0.0226" -- a
     proportion, not a percentage. A percent rule returns NONE on all 93 of its
     values. kind='proportion' vs kind='percent' is an input, never assumed.
  2. PRECISION DRIVES YIELD. 4-dp proportions resolve uniquely 93/93; 2-dp
     percentages 177/188; 1-dp percentages only 467/693 with 84 ambiguous. So the
     precision is recorded, and a 1-dp value that does not resolve is refused, not
     forced.
"""
from __future__ import annotations


def _decimals(x) -> int:
    s = repr(float(x))
    return len(s.split(".", 1)[1]) if "." in s else 0


def admissible(posted, N, kind="proportion", precision=None):
    """Every integer k in [0, N] whose posted value at `precision` equals `posted`.

    kind='proportion' -> posted == round(k / N, precision)
    kind='percent'    -> posted == round(100 * k / N, precision)
    """
    if N is None or N <= 0:
        return []
    if precision is None:
        precision = _decimals(posted)
    scale = 100.0 if kind == "percent" else 1.0

    def val(k):
        return round(scale * k / N, precision)

    centre = (posted / scale) * N
    lo = max(0, int(centre) - 4)
    hi = min(N, int(centre) + 4)
    return [k for k in range(lo, hi + 1) if val(k) == posted]


def recover(posted, N, kind="proportion", precision=None):
    """(count, interval, status).

    status 'unique'    -> count is the sole integer; interval == [count, count].
    status 'ambiguous' -> >1 integer qualifies; count None; interval == [min, max].
    status 'none'      -> no integer reproduces the posted value; count None.
    A recovered value is a DERIVATION: store it with its interval and precision,
    never as a read count.
    """
    if precision is None:
        precision = _decimals(posted)
    ks = admissible(posted, N, kind, precision)
    if len(ks) == 1:
        return ks[0], [ks[0], ks[0]], "unique"
    if len(ks) > 1:
        return None, [min(ks), max(ks)], "ambiguous"
    return None, [], "none"


# ---------------------------------------------------------------------------
def _selftest():
    out = []

    def check(name, got, want):
        ok = got == want
        out.append((name, "OK" if ok else "*** FAIL ***", got, want))
        return ok

    held = True
    # apixaban, prior-practice cases -- each must resolve to the by-hand answer
    for pct, N, want in ((0.47, 3184, 15), (0.82, 2673, 22),
                         (0.69, 1596, 11), (0.60, 1501, 9)):
        c, iv, st = recover(pct, N, kind="percent", precision=2)
        held &= check("apixaban %.2f%% on %d -> %r" % (pct, N, want),
                      (c, st), (want, "unique"))

    # TRAP 1: read the unit. AMPLIFY's real posted value is 0.0226 on N=2609 (its
    # populationDescription reads "n/N: 59/2609"). As a PROPORTION it resolves to 59;
    # read as a PERCENT it resolves to nothing -- a percent rule discards all 93 values.
    c_prop, _, st_prop = recover(0.0226, 2609, kind="proportion", precision=4)
    held &= check("AMPLIFY 0.0226 on 2609 as PROPORTION -> 59",
                  (c_prop, st_prop), (59, "unique"))
    _, _, st_pct = recover(0.0226, 2609, kind="percent", precision=4)
    held &= check("AMPLIFY 0.0226 read as PERCENT does NOT resolve",
                  st_pct in ("none", "ambiguous"), True)

    # TRAP 2: precision. A coarse 1-dp percent on a large N is AMBIGUOUS and must
    # be refused, not forced to a single integer.
    _, iv, st_amb = recover(1.0, 10000, kind="percent", precision=1)
    held &= check("1-dp 1.0%% on 10000 is ambiguous (refused)", st_amb, "ambiguous")

    # a clean 2-dp percent stays unique
    _, _, st_u = recover(0.50, 2000, kind="percent", precision=2)
    held &= check("2-dp 0.50%% on 2000 resolves", st_u, "unique")

    return held, out


if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    ok, rows = _selftest()
    print("recover_count selftest")
    for name, verdict, got, want in rows:
        print("  %-52s %-12s got=%s want=%s" % (name, verdict, got, want))
    print("\n%s" % ("ALL PASS" if ok else "FAILURES ABOVE"))
    raise SystemExit(0 if ok else 1)
