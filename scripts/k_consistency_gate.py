"""Every derived panel must be computed at the same k as the headline it sits beside.

WHY THIS EXISTS, and it is not hypothetical. On 2026-08-13 ANSWER-HF entered the
ARNI pool and the headline became k=4. The entire `panels` block -- its own `fit`,
leave-one-out, cumulative, influence, Baujat, Galbraith, funnel, Egger, the
prediction interval and the tau-squared interval -- stayed at k=3, and so did
`count_panels`. The page therefore showed a four-trial forest plot directly above
a three-row leave-one-out, and a prediction interval computed from three trials
under a four-trial pooled estimate. Nothing failed. Every number was individually
correct; they were correct about different pools.

The interpretation moved too, which is what makes this severe rather than untidy:
at k=3 the pooled interval excluded no difference and at k=4 it does not. The
Discussion still said "the interval excludes the null" while the Conclusions of
the same manuscript said "consistent with no difference".

THE INVARIANT: for each outcome, every block that carries a k, or a row-per-trial
list, agrees with the number of contributing trials in `per_trial`. A block that
is deliberately behind must say so in a `_STALE` field -- then it is a stated
limitation rather than a silent disagreement.

Usage:  python scripts/k_consistency_gate.py <object.json> [more.json ...]
        python scripts/k_consistency_gate.py --selftest
"""
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Panels whose length must equal k (one row per contributing trial).
ROW_PER_TRIAL = ("leave_one_out", "cumulative", "influence", "baujat",
                 "galbraith", "funnel")


def check_outcome(oid, res):
    """Returns a list of problem strings. Empty means consistent."""
    bad = []
    per = res.get("per_trial") or []
    k = res.get("k") or len(per)
    if not k:
        return bad

    pan = res.get("panels") or {}
    stale = bool(pan.get("_STALE"))
    fit = pan.get("fit") or {}
    if fit.get("k") is not None and fit["k"] != k and not stale:
        bad.append("%s: panels.fit.k=%s but the outcome has k=%s"
                   % (oid, fit["k"], k))
    for name in ROW_PER_TRIAL:
        rows = pan.get(name)
        if isinstance(rows, list) and rows and len(rows) != k and not stale:
            bad.append("%s: panels.%s has %d rows for k=%s"
                       % (oid, name, len(rows), k))

    cp = res.get("count_panels") or {}
    cstale = bool(cp.get("_STALE"))
    for meas in ("rr", "or", "rd"):
        m = cp.get(meas)
        if isinstance(m, dict) and m.get("k") is not None and m["k"] != k \
                and not cstale:
            bad.append("%s: count_panels.%s.k=%s but the outcome has k=%s"
                       % (oid, meas, m["k"], k))

    # The pooled interval and the prose must agree about the null. This is the
    # part that changes a reader's conclusion rather than a figure's row count.
    p = res.get("pooled") or {}
    lo, hi = p.get("ci_low"), p.get("ci_high")
    null = 1.0
    if lo is not None and hi is not None:
        includes = lo <= null <= hi
        blob = json.dumps(res.get("_prose", "")) if res.get("_prose") else ""
        if includes and "excludes the null" in blob:
            bad.append("%s: pooled interval %s-%s contains the null but the "
                       "prose says it excludes it" % (oid, lo, hi))
    return bad


def check_object(path):
    d = json.load(open(path, encoding="utf-8"))
    bad = []
    for oid, res in ((d.get("results") or {}).get("by_outcome") or {}).items():
        bad += check_outcome(oid, res)
    # The manuscript is prose ABOUT the pool, so it is checked against the pool.
    ms = json.dumps(d.get("manuscript") or {}, ensure_ascii=False)
    for oid, res in ((d.get("results") or {}).get("by_outcome") or {}).items():
        p = res.get("pooled") or {}
        lo, hi = p.get("ci_low"), p.get("ci_high")
        if lo is not None and hi is not None and lo <= 1.0 <= hi \
                and "excludes the null" in ms:
            bad.append("%s: pooled interval %.4g-%.4g contains the null but the "
                       "manuscript says it excludes it" % (oid, lo, hi))
        break
    return bad


def selftest():
    """A gate that cannot fail is not a gate. These must all be CAUGHT."""
    cases = [
        ("panels stale at k=3 under a k=4 pool",
         {"results": {"by_outcome": {"o": {
             "k": 4, "per_trial": [1, 2, 3, 4],
             "pooled": {"ci_low": 0.7, "ci_high": 1.02},
             "panels": {"fit": {"k": 3},
                        "leave_one_out": [1, 2, 3]}}}}}, True),
        ("count_panels stale at k=3",
         {"results": {"by_outcome": {"o": {
             "k": 4, "per_trial": [1, 2, 3, 4],
             "pooled": {"ci_low": 0.7, "ci_high": 1.02},
             "count_panels": {"rr": {"k": 3}}}}}}, True),
        ("prose says excludes-null while the interval contains it",
         {"results": {"by_outcome": {"o": {
             "k": 2, "per_trial": [1, 2],
             "pooled": {"ci_low": 0.7, "ci_high": 1.02}, "panels": {}}}},
          "manuscript": {"d": "the interval excludes the null"}}, True),
        ("consistent object",
         {"results": {"by_outcome": {"o": {
             "k": 4, "per_trial": [1, 2, 3, 4],
             "pooled": {"ci_low": 0.7, "ci_high": 1.02},
             "panels": {"fit": {"k": 4}, "leave_one_out": [1, 2, 3, 4]}}}},
          "manuscript": {"d": "the interval contains the null"}}, False),
        ("stale but DECLARED -- a stated limitation, not a silent one",
         {"results": {"by_outcome": {"o": {
             "k": 4, "per_trial": [1, 2, 3, 4],
             "pooled": {"ci_low": 0.7, "ci_high": 1.02},
             "panels": {"_STALE": "computed at k=3, recorded",
                        "fit": {"k": 3}, "leave_one_out": [1, 2, 3]}}}}}, False),
    ]
    ok = True
    print("=== the gate must FAIL on a silent k mismatch, and PASS otherwise ===")
    import tempfile
    import os
    for name, obj, expect_fail in cases:
        fd, p = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        json.dump(obj, open(p, "w", encoding="utf-8"))
        got = bool(check_object(p))
        os.unlink(p)
        good = got == expect_fail
        ok &= good
        print("  %-52s %s expected=%s %s"
              % (name, "FAIL" if got else "PASS",
                 "FAIL" if expect_fail else "PASS",
                 "correct" if good else "WRONG"))
    print("\nk-consistency gate proved able to fail on every silent mismatch:", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(selftest())
    paths = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not paths:
        raise SystemExit("usage: k_consistency_gate.py <object.json> ...")
    problems = 0
    for p in paths:
        b = check_object(p)
        problems += len(b)
        print("%s: %s" % (p, "CONSISTENT" if not b else "%d PROBLEM(S)" % len(b)))
        for x in b:
            print("   -", x)
    raise SystemExit(1 if problems else 0)
