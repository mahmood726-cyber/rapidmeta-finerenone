"""Run every gate the git hooks invoke, collect ALL failures, stop at none.

WHY THIS EXISTS, AND WHAT ALREADY EXISTED.
    Two collect-all runners are already here and are good: gates/run_all.py (the 9
    executable-rule gates) and gates/run_repo_checks.py (the 24 wired repo checks). Both
    run every entry, report per check, and -- in run_repo_checks' case -- already separate
    a timeout from a refusal, which is the distinction most of this repository's worst
    hours have turned on.

    THE GAP IS NOT THOSE. It is `.githooks/pre-commit`, which invokes about forty-four
    gates as a shell `|| exit 1` chain. That chain REFUSES AT THE FIRST FAILING CHECK AND
    NEVER REACHES THE REST, so a person who fixes the named gate and re-runs learns only
    what check number two thinks. Every "the trunk is clear now" ever said from that chain
    was a statement about one check.

        A CHAIN THAT STOPS AT THE FIRST FAILURE IS THE SAME DEFECT AS A GATE THAT CAN ONLY
        PRINT ONE THING, ONE LEVEL UP.

    So the fix is WIRING for the 33 checks the two existing runners already cover, and
    CONSTRUCTION for the hook chain. This file is the construction half.

WHAT IT DOES NOT DO. It does not decide whether a red is a defect. That call needs the
output read. gates/WIRED_REPO_CHECKS.json::correction_2026_08_28 records what happens
otherwise: of 12 non-zero exits, 2 were harness error, 2 not assessable, 1 a control that
could not load, 1 broken code, and only 6 were real.

FIVE NAMED STATES, BECAUSE THREE OF THEM ARE NOT VERDICTS:
    ok            the check ran and was satisfied
    FAILED        the check ran and refused              <- the only one that is a finding
    INDETERMINATE it ran out of clock; it judged nothing
    NOT_RUN       its inputs are computed by the hook at run time and are not available
    MISSING       the hook names a script this tree does not carry

DEFECTS THIS RUNNER HAS ALREADY HAD, kept here because each is a house class and each
produced a red table with nothing real in it:
    1. It passed the SHELL TAIL of an invocation as argv (`--gate > "$_L" 2>&1`), so six
       checks exited 2 on an argparse error and read as six failing gates. The tell was
       uniformity -- same exit code, same 0.2s, across unrelated checks. Real failures are
       graded; harness failures are identical.
    2. It counted `check_ledger.py record ...` as a check. That is the hook's ledger
       WRITER, called when something else refuses.
    3. It matched only the inline `python "$R/scripts/x.py"` form. pre-push assigns its
       heavy gates first (DGATE="$REPO_ROOT/scripts/durable_artefact_gate.py") and runs
       `python "$DGATE"` -- so it covered 48 of 55 and reported it as everything. Reach
       read as coverage, inside the runner written to measure coverage.
    4. It ran gates with `$HARTS` passed through literally, producing "artefact not found:
       $HARTS". AN ARGUMENT THAT CANNOT BE EXPANDED IS NOT_RUN, NEVER FAILED.

Usage:  python gates/run_hook_chain.py [--json OUT] [--timeout N] [--selftest]
Exit 1 if any check FAILED. INDETERMINATE and NOT_RUN are reported and do not block,
because a check that could not run is not evidence of a defect -- nor of safety.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK_NAMES = ("pre-commit", "pre-push")

# Not gates. The hook calls these to WRITE a ledger row when something else refuses;
# running one standalone measures nothing and its argparse error is not a red.
NOT_A_GATE = (("scripts/check_ledger.py", "record"),)


def strip_shell(args):
    """argv stops where the shell begins.

    '2>' must be cut before '>', or `2>/dev/null` leaves a stray '2' that argparse
    rejects -- which is defect (1) above, arriving through the fix for defect (1).
    """
    for cut in ("2>", ">", "|", "&&", "||", ";"):
        i = args.find(cut)
        if i != -1:
            args = args[:i]
    return args.strip()


def invocations(hook_text):
    """Every gate a hook invokes, in order, read from the hook TEXT.

    Read from the text and never from a list kept here, so a gate added to the hook is a
    gate this runner covers. A runner carrying its own list drifts from the thing it
    claims to cover, and reports the drift as coverage.
    """
    found = []
    for m in re.finditer(r'python\s+"?\$\{?R\}?/(scripts/[A-Za-z0-9_]+\.py)"?([^\n|&]*)',
                         hook_text):
        found.append((m.group(1), m.group(2)))
    for m in re.finditer(
            r'python\s+"\$\(git rev-parse --show-toplevel\)/(scripts/[A-Za-z0-9_]+\.py)"([^\n|&]*)',
            hook_text):
        found.append((m.group(1), m.group(2)))
    varmap = {}
    for m in re.finditer(r'^\s*([A-Z_][A-Z0-9_]*)="\$(?:REPO_ROOT|R)/([^"]+)"', hook_text, re.M):
        varmap[m.group(1)] = m.group(2)
    for m in re.finditer(r'python\s+"\$\{?([A-Z_][A-Z0-9_]*)\}?"([^\n|&]*)', hook_text):
        rel = varmap.get(m.group(1))
        if rel:
            found.append((rel, m.group(2)))
    for m in re.finditer(r'for\s+g\s+in\s+([^;]+);\s*do', hook_text):
        for g in m.group(1).split():
            if g and not g.startswith("$"):
                found.append(("scripts/%s.py" % g, ""))
    seen, uniq = set(), []
    for rel, args in found:
        k = (rel, strip_shell(args))
        if k not in seen:
            seen.add(k)
            uniq.append(k)
    return uniq


def is_gate(rel, args):
    return not any(rel == r and args.startswith(a) for r, a in NOT_A_GATE)


def expand(args, root):
    """-> (argv_string, unresolved_variables). $REPO_ROOT is knowable here; $HOBJS and
    $HARTS are computed by the hook at run time and are not."""
    a = (args.replace('"$REPO_ROOT', '"' + root).replace("$REPO_ROOT", root)
             .replace('"$R/', '"' + root + "/")
             .replace("$(git rev-parse --show-toplevel)", root)).replace('"', "")
    return a, re.findall(r"\$[A-Za-z_][A-Za-z0-9_]*", a)


def run_one(rel, args, root, budget):
    full = os.path.join(root, rel.replace("/", os.sep))
    if not os.path.exists(full):
        return {"script": rel, "args": args, "state": "MISSING", "exit": None, "secs": 0.0,
                "tail": ["the hook names a script this tree does not carry"]}
    argstr, unresolved = expand(args, root)
    if unresolved:
        return {"script": rel, "args": args, "state": "NOT_RUN", "exit": None, "secs": 0.0,
                "tail": ["inputs computed by the hook at run time: %s"
                         % ", ".join(sorted(set(unresolved))),
                         "NOT a verdict about this check or about the corpus."]}
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable, full] + [a for a in argstr.split() if a],
                           cwd=root, capture_output=True, timeout=budget)
        rc = p.returncode
        blob = (p.stdout + p.stderr).decode("utf-8", "replace")
        state = "ok" if rc == 0 else "FAILED"
    except subprocess.TimeoutExpired:
        rc, blob, state = None, "timed out after %ds" % budget, "INDETERMINATE"
    lines = [l.rstrip() for l in blob.splitlines() if l.strip()]
    return {"script": rel, "args": args, "state": state, "exit": rc,
            "secs": round(time.time() - t0, 1), "tail": lines[-12:]}


def collect(root):
    targets, skipped = [], []
    for name in HOOK_NAMES:
        p = os.path.join(root, ".githooks", name)
        if not os.path.isfile(p):
            continue
        text = io.open(p, encoding="utf-8", errors="replace").read()
        for rel, args in invocations(text):
            (targets if is_gate(rel, args) else skipped).append((name, rel, args))
    return targets, skipped


def named_in_hooks(root):
    """The expected population, derived from the hook text INDEPENDENTLY of the runner's
    own list, so coverage is n_covered/n_expected and not n_covered/n_covered."""
    named = set()
    for name in HOOK_NAMES:
        p = os.path.join(root, ".githooks", name)
        if os.path.isfile(p):
            t = io.open(p, encoding="utf-8", errors="replace").read()
            named |= set(re.findall(r'(?:scripts|gates)/[A-Za-z0-9_]+\.py', t))
    return named


def selftest():
    """A planted chain: one check that must FAIL, one that must be ok, one absent.

    A runner that reports everything ok is indistinguishable from a runner that cannot
    report a failure, and this whole file exists because a chain reported one thing.
    """
    tmp = tempfile.mkdtemp(prefix="__control_hookchain_")
    ok = True
    try:
        os.makedirs(os.path.join(tmp, ".githooks"))
        os.makedirs(os.path.join(tmp, "scripts"))
        io.open(os.path.join(tmp, "scripts", "always_red.py"), "w",
                encoding="utf-8", newline="\n").write("import sys\nsys.exit(1)\n")
        io.open(os.path.join(tmp, "scripts", "always_green.py"), "w",
                encoding="utf-8", newline="\n").write("print('fine')\n")
        io.open(os.path.join(tmp, ".githooks", "pre-commit"), "w",
                encoding="utf-8", newline="\n").write(
                    '#!/bin/sh\n'
                    'python "$R/scripts/always_red.py" > "$_L" 2>&1 || exit 1\n'
                    'python "$R/scripts/always_green.py" || exit 1\n'
                    'python "$R/scripts/not_here_at_all.py" || exit 1\n')
        targets, _skipped = collect(tmp)
        got = {t[1]: run_one(t[1], t[2], tmp, 60)["state"] for t in targets}
        cases = [("a check that exits 1 is FAILED", got.get("scripts/always_red.py"), "FAILED"),
                 ("a check that exits 0 is ok", got.get("scripts/always_green.py"), "ok"),
                 ("a check the tree lacks is MISSING", got.get("scripts/not_here_at_all.py"),
                  "MISSING")]
        print("SELFTEST -- the chain must reach every check, not stop at the first")
        for label, actual, want in cases:
            good = actual == want
            ok &= good
            print("  %-48s -> %-8s want %-8s %s"
                  % (label, actual, want, "correct" if good else "WRONG"))
        # THE POINT OF THE FILE: the red is FIRST in the chain, and the two after it were
        # still reached. A `|| exit 1` chain returns one row here; this must return three.
        reached = len(got)
        good = reached == 3
        ok &= good
        print("  %-48s -> %-8s want %-8s %s"
              % ("all three reached despite the first failing", reached, 3,
                 "correct" if good else "WRONG -- it stopped early"))
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    print("-> SELFTEST PASS" if ok else "-> SELFTEST FAILED")
    return 0 if ok else 1


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", dest="out")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()

    targets, skipped = collect(REPO)
    named = named_in_hooks(REPO)
    invoked = {rel for _h, rel, _a in targets} | {rel for _h, rel, _a in skipped}

    print("HOOK CHAIN -- every gate .githooks/{pre-commit,pre-push} invokes, all of them")
    print("COVERAGE: %d distinct scripts invoked / %d named anywhere in the hook text"
          % (len(invoked), len(named)))
    for m in sorted(named - invoked):
        print("    named but NOT invoked (a comment or a remediation hint): %s" % m)
    for h, rel, args in skipped:
        print("    excluded, not a check: %-9s %s %s" % (h, rel, args))
    print()

    results = []
    for i, (hook, rel, args) in enumerate(targets, 1):
        r = run_one(rel, args, REPO, a.timeout)
        r["hook"] = hook
        results.append(r)
        print("  [%3d/%d] %-9s %-8s %-52s %5.1fs"
              % (i, len(targets), hook, r["state"], (rel + " " + args).strip()[:52], r["secs"]))
        sys.stdout.flush()

    failed = [r for r in results if r["state"] == "FAILED"]
    indet = [r for r in results if r["state"] == "INDETERMINATE"]
    notrun = [r for r in results if r["state"] == "NOT_RUN"]
    missing = [r for r in results if r["state"] == "MISSING"]

    print()
    print("-" * 78)
    print("  %d ok, %d FAILED, %d INDETERMINATE, %d NOT_RUN, %d MISSING"
          % (len(results) - len(failed) - len(indet) - len(notrun) - len(missing),
             len(failed), len(indet), len(notrun), len(missing)))
    for r in failed:
        print("  FAILED   %-52s exit=%s" % ((r["script"] + " " + r["args"]).strip()[:52],
                                            r["exit"]))
        for l in r["tail"][-3:]:
            print("             %s" % l[:110])
    for r in indet + notrun + missing:
        print("  %-13s %-52s %s" % (r["state"], (r["script"] + " " + r["args"]).strip()[:52],
                                    r["tail"][0][:70] if r["tail"] else ""))

    if a.out:
        io.open(a.out, "w", encoding="utf-8", newline="\n").write(json.dumps(
            {"repo": REPO, "coverage": {"invoked": sorted(invoked), "named": sorted(named)},
             "results": results}, indent=1))
        print("  wrote %s" % a.out)

    print()
    print("  A NON-ZERO EXIT IS NOT A DEFECT UNTIL ITS OUTPUT IS READ, and INDETERMINATE")
    print("  and NOT_RUN are not verdicts at all. Only FAILED blocks.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
