"""python -m nafis_harness [--baseline PATH] [--update-baseline]

Runs, in order:
  1. registry self-test  -- fire every detector against its own fixtures
  2. historical dataset  -- including the INVALID (dead-plate) cases
  3. baseline diff       -- regressions, improvements, and went-blind

Exit codes: 0 clean · 1 regression or went-blind · 2 registry unfit.
"""

from __future__ import annotations

import argparse
import os
import sys

from .baseline import (diff_baseline, diff_is_clean, load_baseline, run_dataset,
                       save_baseline)
from .dataset import historical_dataset
from .probes import build_registry

DEFAULT_BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "baseline.json")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="nafis_harness")
    ap.add_argument("--baseline", default=DEFAULT_BASELINE)
    ap.add_argument("--update-baseline", action="store_true")
    args = ap.parse_args(argv)

    reg = build_registry()

    print("=" * 72)
    print("1. REGISTRY SELF-TEST -- every detector against its own fixtures")
    print("=" * 72)
    st = reg.self_test()
    for cid, rep in st["checks"].items():
        mark = "ok " if rep["ok"] else "UNFIT"
        print(f"  [{mark}] {cid:34s} fired {len(rep['fired'])}  "
              f"silent {len(rep['silent'])}")
        for m in rep["misbehaved"]:
            print(f"          !! {m['fixture']}: expected {m['expected']}, "
                  f"got {m['got']} -- {m.get('reason','')}")
    print(f"\n  {st['n_checks']} detectors registered; "
          f"{'all fit' if st['ok'] else 'UNFIT: ' + ', '.join(st['unfit'])}")
    if not st["ok"]:
        print("\nREGISTRY UNFIT -- no results may be reported from it.")
        return 2

    print()
    print("=" * 72)
    print("2. HISTORICAL DATASET")
    print("=" * 72)
    ds = historical_dataset()
    rec = run_dataset(reg, ds)
    print(f"  {len(ds.cases)} cases | match {rec.counts['match']} | "
          f"mismatch {rec.counts['mismatch']} | unexpected-INVALID "
          f"{rec.counts['invalid']}")
    print(f"  discriminating: {rec.discriminating}")
    for cid, e in sorted(rec.results.items()):
        if e["status"] != "match":
            print(f"    !! {cid}: expected {e['expect']}, got {e['got']} "
                  f"-- {e['reason'][:110]}")
    for n in rec.notes:
        print(f"  NOTE: {n}")

    print()
    print("=" * 72)
    print("3. BASELINE DIFF")
    print("=" * 72)
    base = load_baseline(args.baseline)
    diff = diff_baseline(rec, base)
    if diff["first_run"]:
        print("  no baseline on disk -- this run becomes the baseline")
    else:
        for k in ("regressions", "went_blind", "improvements", "new_cases",
                  "dropped_cases"):
            print(f"  {k:14s} {len(diff[k])}")
        for r in diff["regressions"] + diff["went_blind"]:
            print(f"    !! {r['case']}: {r['from']} -> {r['to']} ({r['reason'][:90]})")

    if args.update_baseline or diff["first_run"]:
        save_baseline(rec, args.baseline)
        print(f"  baseline written to {args.baseline}")

    print()
    print("=" * 72)
    print("4. MUTATION MATRIX")
    print("=" * 72)
    mut_ok = True
    try:
        import os as _os, sys as _sys
        _sys.path.insert(0, _os.path.dirname(_os.path.dirname(
            _os.path.abspath(__file__))))
        from mutation_suite import (run_mutation_matrix, summarise, format_report,
                                    SURVIVED, ARMS)
        matrix = run_mutation_matrix()
        print(format_report(matrix))
        s = summarise(matrix)
        mut_ok = all(s["current"][a][SURVIVED] == 0 for a in ARMS)
    except Exception as exc:
        # A mutation suite that cannot run is not a passed mutation suite.
        print(f"  MUTATION SUITE UNAVAILABLE ({type(exc).__name__}: {exc})")
        print("  This is INVALID, not clean -- unit tests alone do not license a "
              "release.")
        mut_ok = False

    print()
    print("=" * 72)
    print("5. EXTERNAL ACCEPTANCE -- the benchmark lane's mutant set (authoritative)")
    print("=" * 72)
    ext_ok = True
    try:
        from test_external_acceptance import _run_external
        out = _run_external()
        for line in out.splitlines():
            if ("HEADLINE" in line or "/7" in line or "SURVIVED" in line) \
                    and "all mutants SURVIVED" not in line:
                print("  " + line.strip())
        ext_ok = "SURVIVED" not in out.replace(
            "baseline: validate_v2.py scored 0/7, all mutants SURVIVED", "")
    except Exception as exc:
        print(f"  EXTERNAL ACCEPTANCE UNAVAILABLE ({type(exc).__name__}: {exc})")
        print("  A skipped acceptance reads as a passed one. Scored NOT CLEAN.")
        ext_ok = False

    print()
    print("=" * 72)
    print("6. MISTAKE LEDGER -- would these be caught if they happened again?")
    print("=" * 72)
    try:
        from .ledger import summarise, unguarded_queue
        s = summarise()
        print(f"  rows: {s['rows']}  "
              f"(sourced: {s['tier_F']} file-backed, {s['tier_R']} operator-relayed)")
        print(f"  guard states: {s['by_guard_state']}")
        print()
        print(f"  CAUGHT TODAY BY SOMETHING THAT RUNS ON ITS OWN : "
              f"{s['caught_today_if_wired_only']:.1%}")
        print(f"  ...if the harness were invoked by the build     : "
              f"{s['caught_today_if_harness_invoked']:.1%}")
        print(f"  no mechanism at all                             : "
              f"{s['unguarded']:.1%}")
        print(f"  caught autonomously when they happened          : "
              f"{s['caught_autonomously_when_it_happened']:.1%}")
        print()
        print("  The gap between the first two figures is detectors that exist and")
        print("  nothing calls. They are AVAILABLE, not caught.")
        q = unguarded_queue()
        print(f"\n  UNGUARDED QUEUE ({len(q)}):")
        for r in q:
            print(f"    {r.id:6s} {r.guard_state:9s} {r.fix_scope:10s} "
                  f"{r.believed[:52]}")
    except Exception as exc:
        print(f"  LEDGER UNAVAILABLE ({type(exc).__name__}: {exc})")

    ok = (rec.counts["mismatch"] == 0 and rec.counts["invalid"] == 0
          and diff_is_clean(diff) and mut_ok and ext_ok)
    print()
    print("VERDICT:", "CLEAN" if ok else "NOT CLEAN")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
