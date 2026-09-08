# -*- coding: utf-8 -*-
"""AUDIT THE WHOLE CLEARANCE SURFACE: every gate the harness owns, classified by WHERE it runs.

"A check that has never executed is indistinguishable from a clean corpus." This enumerates every
gate FILE on disk and classifies each into exactly one of four buckets, then reports n of N with the
NEVER-RUNS named individually -- never a bare rate.

  CONSULTED_BY_CLEARANCE  discovered and run at a page's promotion (run_end_to_end._discover_gates)
  NON_BLOCKING            a page/suite gate deliberately excluded from a single page's clearance,
                          registered with a STATED REASON (run_end_to_end.CLEARANCE_NONBLOCKING)
  CI_ONLY                 registered in the CI suite (gates/run_all.py GATES) but NOT consulted at
                          clearance -- runs nightly, never blocks a single promotion
  NEVER_RUNS              a file named like a gate that NO runner invokes: not clearance-discovered,
                          not registered non-blocking, not in the CI suite. This is the hole.

Fail closed: exit 1 if any NEVER_RUNS gate exists (a gate nothing runs is a false sense of coverage).
The four buckets are a partition -- every gate file lands in exactly one, and the tool asserts it.
"""
from __future__ import annotations
import io, os, sys, ast, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _assign_literal(modpath, name):
    """Read a module-level `name = <literal>` WITHOUT executing the module (several app modules
    reassign sys.stdout at import and would close this tool's stdout -- the trap in lessons.md)."""
    tree = ast.parse(io.open(modpath, encoding="utf-8").read())
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == name:
                    return ast.literal_eval(node.value)
    raise KeyError("%s not found in %s" % (name, modpath))


def _assert_mirrors_live_discovery(local_clearance):
    """Prove the local reimplementation equals run_end_to_end._discover_gates(). Run in a subprocess
    so that module's import-time sys.stdout reassignment cannot close THIS tool's stdout."""
    import subprocess, json
    code = ("import sys,os,json; sys.path.insert(0,os.path.join(%r,'scripts'));"
            "import run_end_to_end as e;"
            "print(json.dumps(sorted(os.path.basename(p) for p in e._discover_gates())))" % ROOT)
    p = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, timeout=60)
    line = [l for l in p.stdout.decode("utf-8", "replace").splitlines() if l.startswith("[")]
    if not line:
        raise SystemExit("MIRROR CHECK BROKEN: could not read live _discover_gates() (%s)"
                         % p.stderr.decode("utf-8", "replace")[:200])
    live = set(json.loads(line[-1]))
    if live != local_clearance:
        raise SystemExit("MIRROR DRIFT: audit's clearance set != live _discover_gates(). "
                         "only-in-live=%s only-in-audit=%s" % (sorted(live - local_clearance),
                                                               sorted(local_clearance - live)))


def audit():
    # 1. every gate file on disk (the population)
    disk = sorted(set(glob.glob(os.path.join(ROOT, "gates", "gate*.py"))) |
                  set(glob.glob(os.path.join(ROOT, "scripts", "gate*.py"))))
    disk_names = {os.path.basename(p) for p in disk}

    # 2. clearance's non-blocking registry, read from the live source (not a copy of it here)
    nonblocking = dict(_assign_literal(os.path.join(ROOT, "scripts", "run_end_to_end.py"),
                                       "CLEARANCE_NONBLOCKING"))
    # clearance DISCOVERS every gate file minus the registered non-blocking minus the kinds helper.
    # Reimplemented locally (importing run_end_to_end would run its stdout-reassign) then PROVEN equal
    # to the live _discover_gates() in an isolated subprocess -- a mirror that is not checked drifts.
    clearance = {n for n in disk_names if n not in nonblocking and n != "gate_kinds.py"}
    _assert_mirrors_live_discovery(clearance)

    # 3. what the CI suite registers (gates/run_all.py GATES -> module names -> filenames)
    gates_list = _assign_literal(os.path.join(ROOT, "gates", "run_all.py"), "GATES")
    ci = {mod + ".py" for mod, _what, _speed in gates_list}

    buckets = {"CONSULTED_BY_CLEARANCE": [], "NON_BLOCKING": [], "CI_ONLY": [], "NEVER_RUNS": []}
    for name in sorted(disk_names):
        if name in clearance:
            buckets["CONSULTED_BY_CLEARANCE"].append(name)
        elif name in nonblocking:
            buckets["NON_BLOCKING"].append((name, nonblocking[name]))
        elif name in ci:
            buckets["CI_ONLY"].append(name)
        else:
            buckets["NEVER_RUNS"].append(name)
    return disk_names, buckets, ci, clearance


def main():
    disk, buckets, ci, clearance = audit()
    N = len(disk)
    n_clear = len(buckets["CONSULTED_BY_CLEARANCE"])
    n_nb = len(buckets["NON_BLOCKING"])
    n_ci = len(buckets["CI_ONLY"])
    n_never = len(buckets["NEVER_RUNS"])
    print("CLEARANCE SURFACE AUDIT -- %d gate files on disk" % N)
    print("=" * 74)
    print("  CONSULTED_BY_CLEARANCE : %d" % n_clear)
    print("  NON_BLOCKING (reasoned): %d" % n_nb)
    print("  CI_ONLY                : %d" % n_ci)
    print("  NEVER_RUNS             : %d" % n_never)
    # partition assertion: the four buckets must sum to N with no overlap
    covered = n_clear + n_nb + n_ci + n_never
    print("  -- partition check: %d + %d + %d + %d = %d %s N=%d" %
          (n_clear, n_nb, n_ci, n_never, covered, "==" if covered == N else "!=", N))

    print("\n[NON_BLOCKING] deliberately outside a single page's clearance, with reason:")
    for name, reason in buckets["NON_BLOCKING"]:
        print("     - %-46s %s" % (name, reason))

    if buckets["CI_ONLY"]:
        print("\n[CI_ONLY] runs nightly, does NOT block a single promotion:")
        for name in buckets["CI_ONLY"]:
            print("     - %s" % name)

    print("\n[NEVER_RUNS] named like a gate, invoked by NOTHING -- %d:" % n_never)
    for name in buckets["NEVER_RUNS"]:
        print("     *** %s" % name)
    if not buckets["NEVER_RUNS"]:
        print("     (none -- every gate file is consulted, registered non-blocking, or in CI)")

    ok = (covered == N) and (n_never == 0)
    print("\n>>> %d of %d gate files run somewhere; %d NEVER-RUN. %s <<<" %
          (N - n_never, N, n_never, "PASS" if ok else "FAIL"))
    return 0 if ok else 1


def as_json():
    disk, buckets, ci, clearance = audit()
    return {
        "n_total": len(disk),
        "n_consulted": len(buckets["CONSULTED_BY_CLEARANCE"]),
        "n_non_blocking": len(buckets["NON_BLOCKING"]),
        "n_ci_only": len(buckets["CI_ONLY"]),
        "n_never_runs": len(buckets["NEVER_RUNS"]),
        "consulted": buckets["CONSULTED_BY_CLEARANCE"],
        "non_blocking": [{"gate": n, "reason": r} for n, r in buckets["NON_BLOCKING"]],
        "ci_only": buckets["CI_ONLY"],
        "never_runs": buckets["NEVER_RUNS"],
    }


if __name__ == "__main__":
    if "--json" in sys.argv:
        import json
        print(json.dumps(as_json(), indent=1))
        sys.exit(0)
    sys.exit(main())
