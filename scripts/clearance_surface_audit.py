# -*- coding: utf-8 -*-
"""AUDIT THE WHOLE CLEARANCE SURFACE: every gate file the harness owns, across BOTH naming conventions
(gate*.py prefix AND *_gate.py suffix -- 108 files), classified by WHICH RUNNER reaches it.

"A check that has never executed is indistinguishable from a clean corpus." The first draft of this
tool globbed only gate*.py and reported "54 of 54, 0 never-run" -- a denominator that was HALF the
population (the *_gate.py suffix family, 54 more files with zero overlap, was invisible to it). That is
the exact "a scan reports where it LOOKED" error this project keeps finding, occurring inside the audit
meant to catch it. Fixed: the population is now every gate file under both conventions.

There are TWO clearance layers, and a gate in EITHER is consulted before a page is served:
  - PER-PAGE PROMOTION   run_end_to_end._discover_gates() -- runs at a single page's promotion
  - PUSH-TIME            the pre-push hook (its named gates) + gates/run_all.py (the CI suite)
plus gate8's UNCALLED_REPO_GATES.json, the ratcheted backlog of KNOWN-uncalled repo gates.

A file reached by NONE of those is a NEVER-RUN. We split those:
  DORMANT_GATE     never-run AND can actually fail (a real safety gate written and left inert)
  MISNAMED_HELPER  never-run AND cannot fail at all (named *_gate but is a script/helper, not a gate)

RATCHET: the current DORMANT_GATE set is frozen in scripts/baselines/never_runs_baseline.json,
OWED - NOT CLEARED. PASS means no NEW dormant gate joined the never-run set; it never means "clean".
Fail closed: a new *_gate.py that can fail and nothing runs FAILS this audit.
"""
from __future__ import annotations
import io, os, sys, ast, re, glob, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE = os.path.join(ROOT, "scripts", "baselines", "never_runs_baseline.json")


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


def _population():
    return sorted(set(os.path.basename(p) for p in (
        glob.glob(os.path.join(ROOT, "gates", "gate*.py")) +
        glob.glob(os.path.join(ROOT, "scripts", "gate*.py")) +
        glob.glob(os.path.join(ROOT, "gates", "*_gate.py")) +
        glob.glob(os.path.join(ROOT, "scripts", "*_gate.py")))))


def _path_of(name):
    for d in ("gates", "scripts"):
        p = os.path.join(ROOT, d, name)
        if os.path.exists(p):
            return p
    return None


def _can_fail(name):
    """True if the file has a reachable NON-zero exit / FAIL verdict -- i.e. it can actually block.
    Mirrors gate8's distinction between a gate and a same-named helper that only ever prints."""
    p = _path_of(name)
    if not p:
        return False
    src = io.open(p, encoding="utf-8", errors="replace").read()
    if "__main__" not in src:
        return False
    # a non-zero SystemExit, an exit of a computed value, or an H.Gate FAIL/BROKEN verdict path
    if re.search(r"sys\.exit\(\s*(?!0\s*\))", src) or re.search(r"raise\s+SystemExit\(\s*(?!0?\s*\))", src):
        return True
    if re.search(r"H\.(FAIL|BROKEN)\b|gate\.report\(|return\s+\d*\s*#?.*(FAIL|BROKEN)", src):
        return True
    if re.search(r"\bexit\(\s*1\b|\bsys\.exit\(\s*[a-zA-Z_]", src):
        return True
    return False


def _runners():
    # 1. per-page promotion clearance (gate*.py minus non-blocking minus kinds helper)
    nb = dict(_assign_literal(os.path.join(ROOT, "scripts", "run_end_to_end.py"), "CLEARANCE_NONBLOCKING"))
    clearance = {os.path.basename(p) for p in (
        glob.glob(os.path.join(ROOT, "gates", "gate*.py")) + glob.glob(os.path.join(ROOT, "scripts", "gate*.py")))
        if os.path.basename(p) not in nb and os.path.basename(p) != "gate_kinds.py"}
    # 2. CI suite
    ci = {m + ".py" for m, _w, _s in _assign_literal(os.path.join(ROOT, "gates", "run_all.py"), "GATES")}
    # 3. pre-push hook named gates (filenames referenced in the hook script)
    hook = io.open(os.path.join(ROOT, ".githooks", "pre-push"), encoding="utf-8", errors="replace").read()
    prepush = set(re.findall(r"([a-z_0-9]+_gate\.py)", hook))
    for m in re.findall(r"scripts/([a-z_0-9]+)\.py", hook):
        prepush.add(m + ".py")
    for grp in re.findall(r"for g in ([a-z_0-9 ]+); do", hook):
        for nm in grp.split():
            prepush.add(nm + ".py")
    # 4. gate8's known-uncalled ratchet registry (tracked, not silently ignored)
    reg = set()
    rp = os.path.join(ROOT, "gates", "UNCALLED_REPO_GATES.json")
    if os.path.exists(rp):
        def walk(o):
            if isinstance(o, str) and o.endswith(".py"):
                reg.add(os.path.basename(o))
            elif isinstance(o, list):
                [walk(x) for x in o]
            elif isinstance(o, dict):
                [walk(x) for x in o.values()]
        try:
            walk(json.load(io.open(rp, encoding="utf-8")))
        except Exception:
            pass
    return nb, clearance, ci, prepush, reg


def audit():
    disk = _population()
    nb, clearance, ci, prepush, reg = _runners()
    reached = clearance | ci | prepush | reg
    buckets = {"PER_PAGE_CLEARANCE": [], "PUSH_TIME": [], "NON_BLOCKING": [],
               "GATE8_BACKLOG": [], "DORMANT_GATE": [], "MISNAMED_HELPER": []}
    for name in disk:
        if name in clearance:
            buckets["PER_PAGE_CLEARANCE"].append(name)
        elif name in ci or name in prepush:
            buckets["PUSH_TIME"].append(name)
        elif name in nb:
            buckets["NON_BLOCKING"].append((name, nb[name]))
        elif name in reg:
            buckets["GATE8_BACKLOG"].append(name)
        elif _can_fail(name):
            buckets["DORMANT_GATE"].append(name)
        else:
            buckets["MISNAMED_HELPER"].append(name)
    return disk, buckets


def _baseline():
    if os.path.exists(BASELINE):
        try:
            return set(json.load(io.open(BASELINE, encoding="utf-8")).get("dormant_gates", []))
        except Exception:
            return set()
    return set()


def as_json():
    disk, b = audit()
    return {
        "n_total": len(disk),
        "n_per_page_clearance": len(b["PER_PAGE_CLEARANCE"]),
        "n_push_time": len(b["PUSH_TIME"]),
        "n_non_blocking": len(b["NON_BLOCKING"]),
        "n_gate8_backlog": len(b["GATE8_BACKLOG"]),
        "n_dormant_gate": len(b["DORMANT_GATE"]),
        "n_misnamed_helper": len(b["MISNAMED_HELPER"]),
        "non_blocking": [{"gate": n, "reason": r} for n, r in b["NON_BLOCKING"]],
        "dormant_gates": b["DORMANT_GATE"],
        "misnamed_helpers": b["MISNAMED_HELPER"],
    }


def main():
    disk, b = audit()
    N = len(disk)
    counts = {k: len(v) for k, v in b.items()}
    reached = counts["PER_PAGE_CLEARANCE"] + counts["PUSH_TIME"] + counts["NON_BLOCKING"] + counts["GATE8_BACKLOG"]
    print("CLEARANCE SURFACE AUDIT -- %d gate files (gate*.py AND *_gate.py)" % N)
    print("=" * 74)
    print("  PER_PAGE_CLEARANCE : %d  (run_end_to_end discovers + consults at promotion)" % counts["PER_PAGE_CLEARANCE"])
    print("  PUSH_TIME          : %d  (pre-push hook named gates + gates/run_all.py CI)" % counts["PUSH_TIME"])
    print("  NON_BLOCKING       : %d  (registered, reasoned -- below)" % counts["NON_BLOCKING"])
    print("  GATE8_BACKLOG      : %d  (known-uncalled, ratcheted in UNCALLED_REPO_GATES.json)" % counts["GATE8_BACKLOG"])
    print("  DORMANT_GATE       : %d  (CAN fail, reached by NOTHING -- the real never-runs)" % counts["DORMANT_GATE"])
    print("  MISNAMED_HELPER    : %d  (named *_gate but cannot fail -- not a gate)" % counts["MISNAMED_HELPER"])
    print("  -- partition: %d + ... = %d %s N=%d" % (reached, reached + counts["DORMANT_GATE"] + counts["MISNAMED_HELPER"],
          "==" if reached + counts["DORMANT_GATE"] + counts["MISNAMED_HELPER"] == N else "!=", N))

    print("\n[NON_BLOCKING] deliberately outside per-page clearance, with reason:")
    for name, reason in b["NON_BLOCKING"]:
        print("     - %-46s %s" % (name, reason))

    print("\n[DORMANT_GATE] a gate that CAN fail and NOTHING runs -- named:")
    for name in b["DORMANT_GATE"]:
        print("     *** %s" % name)
    if not b["DORMANT_GATE"]:
        print("     (none)")
    print("\n[MISNAMED_HELPER] named like a gate but cannot fail (not a gate, naming noise):")
    for name in b["MISNAMED_HELPER"]:
        print("     - %s" % name)

    base = _baseline()
    new_dormant = sorted(set(b["DORMANT_GATE"]) - base)
    print("\nRATCHET: baseline dormant=%d, now=%d, NEW=%d" % (len(base), counts["DORMANT_GATE"], len(new_dormant)))
    if new_dormant:
        print("  *** NEW dormant gate(s) since the freeze -- wire a caller or register the reason:")
        for n in new_dormant:
            print("      -> %s" % n)
    ok = not new_dormant
    print("\n>>> %d of %d reached by a runner; %d dormant (baseline %d, new %d). %s <<<" %
          (reached, N, counts["DORMANT_GATE"], len(base), len(new_dormant), "PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    if "--json" in sys.argv:
        print(json.dumps(as_json(), indent=1)); sys.exit(0)
    if "--freeze" in sys.argv:
        _disk, b = audit()
        os.makedirs(os.path.dirname(BASELINE), exist_ok=True)
        json.dump({"dormant_gates": b["DORMANT_GATE"],
                   "note": "OWED - NOT CLEARED. Frozen dormant gates (can fail, nothing runs them). "
                           "PASS = no NEW dormant gate; wire a caller to clear one."},
                  io.open(BASELINE, "w", encoding="utf-8"), indent=1)
        print("froze %d dormant gates to %s" % (len(b["DORMANT_GATE"]), BASELINE)); sys.exit(0)
    sys.exit(main())
