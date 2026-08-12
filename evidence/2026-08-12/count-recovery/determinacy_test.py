#!/usr/bin/env python3
"""Is a reconstruction actually determined? Test it; do not assume it.

The 2026-08-12 ruling permits reconstruction where the reported quantities
"mathematically determine the cells ... with no assumption". This script tests whether
that condition actually holds, rather than taking the presence of a percentage and a
denominator as proof that it does.

The test
--------
A published percentage p printed to d decimals is not a number, it is an interval:
    p in [p - 0.5*10^-d, p + 0.5*10^-d]
Given a group size n, the integer counts compatible with that interval are
    { k : 100k/n lies in the interval }
The reconstruction is DETERMINED only if that set has exactly one member. If it has
two or more, choosing one is an assumption, and the ruling forbids it.

Part 1 runs the test against a case where the true counts are known independently, so
the failure mode can be measured rather than argued about.
"""
from __future__ import annotations

import json
import math
import os
import sys


def compatible_counts(pct: float, n: int, decimals: int | None = None) -> list[int]:
    """Integers k whose 100k/n rounds to the printed percentage."""
    if decimals is None:
        s = f"{pct}"
        decimals = len(s.split(".")[1]) if "." in s else 0
    half = 0.5 * (10 ** -decimals)
    lo, hi = pct - half, pct + half
    kmin = max(0, math.floor(lo * n / 100.0) - 2)
    kmax = min(n, math.ceil(hi * n / 100.0) + 2)
    return [k for k in range(kmin, kmax + 1) if lo <= 100.0 * k / n <= hi]


def naive(pct: float, n: int) -> int:
    return round(n * pct / 100.0)


# ----------------------------------------------------------------------------
# Part 1 — a known-truth calibration set.
# Counts and percentages both READ from the FDA statistical/summary review for
# NDA 207620 (PARADIGM-HF), Tables 1-3. Because the true integers are printed
# alongside the percentages, this measures exactly how far a percentage-times-
# denominator reconstruction drifts from the truth.
# ----------------------------------------------------------------------------
FDA_PARADIGM = [
    # (label, true_count, printed_pct, denominator)
    ("composite, LCZ696",            914, 21.8, 4187),
    ("composite, enalapril",        1117, 26.5, 4212),
    ("all-cause death, LCZ696",      711, 17.0, 4187),
    ("all-cause death, enalapril",   835, 19.8, 4212),
    ("CV death (total), LCZ696",     558, 13.3, 4187),
    ("CV death (total), enalapril",  693, 16.5, 4212),
    ("HF hosp (total), LCZ696",      537, 12.8, 4187),
    ("HF hosp (total), enalapril",   658, 15.6, 4212),
    ("CV death (first event), LCZ696",   377,  9.0, 4187),
    ("CV death (first event), enalapril", 459, 10.9, 4212),
]


def part1():
    print("=" * 96)
    print("PART 1 — percentage x denominator, tested where the true count is known")
    print("  source: FDA NDA 207620 statistical/summary review, PARADIGM-HF Tables 1-3")
    print("=" * 96)
    print(f"{'quantity':34}{'true':>6}{'naive':>7}{'err':>5}{'compatible integers':>22}  verdict")
    print("-" * 96)
    errs, undet, wrong = [], 0, 0
    for label, true, pct, n in FDA_PARADIGM:
        nv = naive(pct, n)
        comp = compatible_counts(pct, n)
        err = nv - true
        errs.append(abs(err))
        det = len(comp) == 1
        if not det:
            undet += 1
        if err != 0:
            wrong += 1
        span = f"{comp[0]}-{comp[-1]} ({len(comp)})" if comp else "none"
        verdict = "DETERMINED" if det else "UNDERDETERMINED"
        if det and comp[0] != true:
            verdict += " and WRONG"
        print(f"{label:34}{true:6}{nv:7}{err:+5}{span:>22}  {verdict}")
    print()
    print(f"  naive reconstruction exact in {len(FDA_PARADIGM)-wrong} of {len(FDA_PARADIGM)}; "
          f"max error {max(errs)}")
    print(f"  rounding interval admits more than one integer in {undet} of {len(FDA_PARADIGM)}")
    print("""
  Reading. A percentage printed to one decimal against a denominator in the thousands
  does not pin the count. Eight of these ten reconstructions miss the true value, one
  by two. The two that hit are the ones where the denominator happens to make the
  interval narrow. Percentage-times-denominator is therefore NOT a determined
  reconstruction at this precision, which is why it stays forbidden -- and the
  determinacy has to be tested per cell, not assumed from the presence of a
  percentage and an n.""")


# ----------------------------------------------------------------------------
# Part 2 — apply the same test to the diagnostic-accuracy rows
# ----------------------------------------------------------------------------
FILES = ["covid_antigen_trials.json", "ddimer_pe_trials.json", "genexpert_ultra_trials.json",
         "mpmri_prostate_trials.json", "ptau217_ad_trials.json", "hsctn_nstemi_trials.json"]
DERIVED = ("back_comput", "back_compute", "relabel")


def printed_decimals(quote: str, value: float) -> int | None:
    """How many decimals was this statistic printed to in the stored quote?"""
    import re
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*%", quote or ""):
        v = float(m.group(1))
        if abs(v - value) <= 0.55:
            frac = m.group(1).split(".")
            return len(frac[1]) if len(frac) > 1 else 0
    return None


def part2(corpus_dir):
    print("\n" + "=" * 96)
    print("PART 2 — determinacy of the diagnostic-accuracy reconstructions")
    print("=" * 96)
    rows = []
    for f in FILES:
        p = os.path.join(corpus_dir, f)
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        for tier, v in d.items():
            if isinstance(v, list) and v and isinstance(v[0], dict) and "TP" in v[0]:
                for r in v:
                    if any(m in str(r.get("provenance", "")).lower() for m in DERIVED):
                        rows.append((f, tier, r))

    print(f"{'study':44}{'sens':>7}{'dec':>4}{'TP opts':>9}{'spec':>7}{'dec':>4}{'TN opts':>9}  verdict")
    print("-" * 96)
    determined = partial = under = 0
    for f, tier, r in rows:
        tp, fp, fn, tn = r.get("TP"), r.get("FP"), r.get("FN"), r.get("TN")
        if None in (tp, fp, fn, tn):
            continue
        q = r.get("raw_quote") or ""
        n_dis, n_non = tp + fn, fp + tn
        sens, spec = 100.0 * tp / n_dis, 100.0 * tn / n_non
        ds, dp = printed_decimals(q, sens), printed_decimals(q, spec)
        tp_opts = compatible_counts(sens, n_dis, ds) if ds is not None else []
        tn_opts = compatible_counts(spec, n_non, dp) if dp is not None else []
        both_pinned = len(tp_opts) == 1 and len(tn_opts) == 1
        neither = ds is None and dp is None
        if both_pinned:
            determined += 1
            v = "DETERMINED"
        elif neither:
            under += 1
            v = "UNDERDETERMINED (stat not in quote)"
        elif len(tp_opts) == 1 or len(tn_opts) == 1:
            partial += 1
            v = "PARTIAL"
        else:
            under += 1
            v = "UNDERDETERMINED"
        print(f"{str(r.get('studlab'))[:43]:44}{sens:7.1f}{str(ds):>4}{len(tp_opts):9}"
              f"{spec:7.1f}{str(dp):>4}{len(tn_opts):9}  {v}")
    n = determined + partial + under
    print()
    print(f"  DETERMINED (both cells pinned to one integer) : {determined} of {n}")
    print(f"  PARTIAL    (one cell pinned, one not)         : {partial} of {n}")
    print(f"  UNDERDETERMINED                               : {under} of {n}")
    print("""
  Under the ruling, only the DETERMINED group may be reconstructed, and each such cell
  must store its inputs, its formula and a pointer per input so a reader can redo the
  arithmetic. The PARTIAL and UNDERDETERMINED groups stay `not_computed_reason`.""")


def part3(corpus_dir):
    """Both conditions must hold. Part 2 alone is not enough, and the gap matters.

    Part 2 asks whether the rounding interval pins a unique integer GIVEN the group
    sizes. It does not ask where those group sizes came from. Several rows pass Part 2
    on group sizes that were themselves assumed -- Palmqvist 2020 reports only N=301
    and the 138/163 split is an imputation, so the "pinned" TP is pinned conditional on
    a number nobody reported.

    A reconstruction is determined only if BOTH hold:
      (a) both group sizes appear in the source, and
      (b) the reported statistic's rounding interval admits exactly one integer.
    """
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from audit_dta_backcomputation import classify  # reuse the reported-quantity test

    rows = []
    for f in FILES:
        p = os.path.join(corpus_dir, f)
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        for tier, v in d.items():
            if isinstance(v, list) and v and isinstance(v[0], dict) and "TP" in v[0]:
                for r in v:
                    if any(m in str(r.get("provenance", "")).lower() for m in DERIVED):
                        rows.append(r)

    print("\n" + "=" * 96)
    print("PART 3 — both conditions: group sizes reported AND the interval pins the integer")
    print("=" * 96)
    print(f"{'study':44}{'(a) groups reported':>21}{'(b) interval pins':>19}   verdict")
    print("-" * 96)
    both = []
    for r in rows:
        tp, fp, fn, tn = r.get("TP"), r.get("FP"), r.get("FN"), r.get("TN")
        if None in (tp, fp, fn, tn):
            continue
        c = classify(r)
        a = c["status"] == "DETERMINED"
        q = r.get("raw_quote") or ""
        n_dis, n_non = tp + fn, fp + tn
        sens, spec = 100.0 * tp / n_dis, 100.0 * tn / n_non
        ds, dp = printed_decimals(q, sens), printed_decimals(q, spec)
        b = (ds is not None and len(compatible_counts(sens, n_dis, ds)) == 1 and
             dp is not None and len(compatible_counts(spec, n_non, dp)) == 1)
        if a and b:
            both.append(r.get("studlab"))
        print(f"{str(r.get('studlab'))[:43]:44}{('yes' if a else 'no'):>21}"
              f"{('yes' if b else 'no'):>19}   {'DETERMINED' if a and b else '-'}")
    print()
    print(f"  Determined on BOTH conditions: {len(both)} of {len(rows)} -> {both}")
    print(f"""
  So of the {len(rows)} reconstructions, {len(both)} may proceed under the ruling and
  {len(rows) - len(both)} may not. The gap between this and Part 2's count is the set of rows whose
  cells are pinned only because a group size was assumed -- pinned to an imputation is
  not determined.""")


if __name__ == "__main__":
    part1()
    part2(sys.argv[1] if len(sys.argv) > 1 else ".")
    part3(sys.argv[1] if len(sys.argv) > 1 else ".")
