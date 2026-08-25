#!/usr/bin/env python3
"""HOW MUCH OF OUR GREEN IS MEANINGLESS. Two measurements, never one number.

    MEASURE 1 -- CAN IT FAIL AT ALL?  Does the module contain a REACHABLE non-zero exit?
    MEASURE 2 -- HAS IT EVER BEEN SHOWN TO FAIL?  Does anything in this repo plant a defect
                 into a real input and require this check to refuse it?

THESE ARE NOT THE SAME QUESTION AND THE SECOND IS THE HARD ONE. A check with a reachable
`sys.exit(1)` that nobody has ever watched fire is not a control; it is an assertion about
the future. `lint_gate_can_fail.py` already answers MEASURE 1 -- but only for filenames
ending `_gate.py`, so roughly forty `lint_*` and `check_*` modules sit outside it entirely.
This measures the whole population on both axes and reports its own scope.

WHY AST AND NOT REGEX. The defect class being measured here IS vocabulary-bound matching:
a gate resting on seven literal patterns missed a twenty-page defect phrased differently.
An instrument built from `grep sys.exit` would inherit exactly that failure -- it would miss
`raise SystemExit(2)`, `return 1` from a main() that is `sys.exit(main())`, and an exit
inside a helper -- and would count them as cannot-fail. So the exits are found by walking
the parse tree, and the modules that fail to parse are REPORTED, never scored.

THREE STATES, NEVER TWO, on both axes: yes / no / could-not-determine.

VALIDATED AGAINST KNOWN POSITIVES, and the run refuses if they do not hold -- a first run
is not information until something known proves the instrument. The known positives are
declared in KNOWN below with the reason each is known.
"""
import ast
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(REPO, "scripts")
sys.path.insert(0, SCRIPTS)

# The population. A module is a CHECK if its name says it checks something. Recorded here
# rather than in prose so the scope is auditable and arguable.
CHECK_NAME = re.compile(r"^(lint_|gate_|check_|verify_|audit_|prove_)|(_gate|_check|_guard)\.py$")

# Modules that exist to PROVE another check, not to check the corpus. They are the evidence
# for MEASURE 2 and are excluded from the population so they cannot inflate it.
PROVER_NAME = re.compile(r"^(plant_|prove_)|(_plant|_selftest)\.py$")

# KNOWN POSITIVES. Each is a fact established before this instrument existed. If the
# instrument disagrees with any of them it is wrong and says so instead of reporting.
KNOWN = [
    # (module, axis, expected, why it is known)
    ("lint_gate_can_fail.py", "can_fail", True,
     "it is wired into .githooks/pre-commit with `|| exit 1`, so it demonstrably blocks"),
    ("ssot_net_deletion_check.py", "can_fail", True,
     "first gate in the hook chain, `|| exit 1`"),
]


def reachable_nonzero_exit(tree):
    """Any construct that can leave the process with a non-zero status.

    Deliberately broad: sys.exit(n>0), sys.exit(expr), exit(n), raise SystemExit(n or expr),
    and `return <nonzero-or-expr>` from a function named main (the `sys.exit(main())` idiom).
    An EXPRESSION argument counts, because `sys.exit(main())` and `sys.exit(rc)` are the two
    commonest shapes in this repo and both can be non-zero at run time.
    """
    found = []

    def arg_can_be_nonzero(node):
        if not node.args:
            return False                      # sys.exit() == 0
        a = node.args[0]
        if isinstance(a, ast.Constant):
            if a.value is None or a.value == 0:
                return False
            return True                       # non-zero literal, or a string (exit status 1)
        return True                           # an expression: cannot be shown to be zero

    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            name = getattr(f, "id", None) or getattr(f, "attr", None)
            if name == "exit" and arg_can_be_nonzero(n):
                found.append("exit()")
        if isinstance(n, ast.Raise) and n.exc is not None:
            e = n.exc
            if isinstance(e, ast.Call):
                nm = getattr(e.func, "id", None) or getattr(e.func, "attr", None)
                if nm == "SystemExit" and arg_can_be_nonzero(e):
                    found.append("raise SystemExit")
            elif getattr(e, "id", None) == "SystemExit":
                found.append("raise SystemExit")
        if isinstance(n, ast.FunctionDef) and n.name == "main":
            for m in ast.walk(n):
                if isinstance(m, ast.Return) and m.value is not None:
                    v = m.value
                    if isinstance(v, ast.Constant):
                        if v.value not in (None, 0, False):
                            found.append("main() returns nonzero")
                    else:
                        found.append("main() returns expr")
    return sorted(set(found))


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    names = sorted(f for f in os.listdir(SCRIPTS) if f.endswith(".py"))
    provers = [f for f in names if PROVER_NAME.search(f)]
    checks = [f for f in names if CHECK_NAME.search(f) and f not in provers]

    # MEASURE 2 evidence: text of every prover, plus the hook chain, plus any test_*.
    ev_files = list(provers) + [f for f in names if f.startswith("test_")]
    ev_text = {}
    for f in ev_files:
        try:
            with io.open(os.path.join(SCRIPTS, f), encoding="utf-8", errors="replace") as fh:
                ev_text[f] = fh.read()
        except OSError:
            pass
    hook = ""
    hp = os.path.join(REPO, ".githooks", "pre-commit")
    if os.path.exists(hp):
        with io.open(hp, encoding="utf-8", errors="replace") as fh:
            hook = fh.read()

    rows = []
    for f in checks:
        p = os.path.join(SCRIPTS, f)
        rec = {"module": f, "in_hook_chain": f in hook}
        try:
            with io.open(p, encoding="utf-8", errors="replace") as fh:
                src = fh.read()
            tree = ast.parse(src)
        except SyntaxError as exc:
            rec["can_fail"] = "COULD_NOT_DETERMINE"
            rec["why"] = "does not parse: %s" % exc
            rec["has_control"] = "COULD_NOT_DETERMINE"
            rows.append(rec)
            continue
        exits = reachable_nonzero_exit(tree)
        rec["can_fail"] = bool(exits)
        rec["exit_forms"] = exits
        stem = f[:-3]
        provers_naming = sorted(k for k, t in ev_text.items() if stem in t)
        # A module that plants a defect into ITSELF counts too -- some checks carry their own
        # known-positive fixture. Looked for by name, and reported as self rather than merged.
        self_control = bool(re.search(r"known[_ ]positive|plant|negative control", src, re.I))
        rec["provers"] = provers_naming
        rec["self_control_language"] = self_control
        rec["has_control"] = bool(provers_naming)
        rows.append(rec)

    # ---- THE REPO'S OWN CONTROL MECHANISM, and this instrument was caught by it.
    #
    # `lint_instrument_declares_a_control.py` sits in the hook chain at line 171 and refuses
    # any new corpus-wide instrument that reports findings without routing through
    # `instrument_controls.require_controls`. The first version of THIS file declared known
    # positives in its own private list and would have been refused -- an instrument built to
    # measure whether checks have controls, itself lacking one by the repo's own definition.
    # Recorded rather than quietly fixed, because it is the same shape as the finding.
    #
    # BOTH SIDES ARE DECLARED. The negative matters more here than the positive: the failure
    # mode of this instrument is OVER-reporting "no control", and a positive-only check
    # cannot see that.
    idx = {r["module"]: r for r in rows}
    try:
        from instrument_controls import require_controls
        require_controls(
            "measure_check_controls_2026_08_25",
            positive=("prove_our_gates_can_fail_2026_08_23.py plants a defect into "
                      "lint_control_chars.py's input and requires a non-zero exit, which is a "
                      "control by any definition -- established by reading that prover, not "
                      "by this logic",
                      idx.get("lint_control_chars.py", {}).get("has_control"), True),
            # THE OVER-FLAGGING DIRECTION IS "uncontrolled", so the negative must be a
            # module that genuinely IS controlled and must not come back otherwise. The
            # first version of this control had the polarity inverted -- it passed an
            # UNCONTROLLED module and asserted it must not be uncontrolled -- and
            # `require_controls` refused the whole run before printing a single count.
            # It was right to. The count that would have been printed was correct; the
            # control that vouched for it was not, and this file exists to say that
            # difference matters.
            negative=("lint_criteria_fingerprint.py is proven by its own dedicated prover "
                      "prove_criteria_fingerprint.py -- a correspondence established by "
                      "reading that prover, not by this logic. A controlled module must "
                      "NOT come back uncontrolled; that is this instrument's over-flagging "
                      "direction",
                      idx.get("lint_criteria_fingerprint.py", {}).get("has_control"), False))
    except ImportError:
        print("NOTE: instrument_controls not importable; inline known positives only.\n")
    bad = []
    for mod, axis, expect, why in KNOWN:
        r = idx.get(mod)
        if r is None:
            bad.append("%s absent from the population (%s)" % (mod, why))
        elif r.get(axis) != expect:
            bad.append("%s %s = %r, expected %r (%s)" % (mod, axis, r.get(axis), expect, why))
    print("KNOWN-POSITIVE VALIDATION")
    for mod, axis, expect, why in KNOWN:
        r = idx.get(mod)
        got = r.get(axis) if r else "ABSENT"
        print("   %-40s %-9s got %-6r expect %r" % (mod, axis, got, expect))
    if bad:
        print()
        print("REFUSED: the instrument contradicts a known fact, so its other numbers are "
              "not reportable:")
        for b in bad:
            print("   - %s" % b)
        return 1
    print("   all known positives hold.\n")

    n = len(rows)
    cant = [r for r in rows if r["can_fail"] is False]
    cnd = [r for r in rows if r["can_fail"] == "COULD_NOT_DETERMINE"]
    canfail = [r for r in rows if r["can_fail"] is True]
    nocontrol = [r for r in canfail if r["has_control"] is False]
    withctl = [r for r in canfail if r["has_control"] is True]
    hooked = [r for r in rows if r["in_hook_chain"]]
    hooked_nc = [r for r in hooked if r.get("has_control") is False]

    print("POPULATION: %d check modules in scripts/ (provers excluded: %d)" % (n, len(provers)))
    print()
    print("MEASURE 1 -- CAN IT FAIL AT ALL?   denominator %d" % n)
    print("   can fail                     %4d" % len(canfail))
    print("   CANNOT fail                  %4d" % len(cant))
    print("   could not determine          %4d" % len(cnd))
    print()
    print("MEASURE 2 -- HAS IT EVER BEEN SHOWN TO FAIL?   denominator %d (those that CAN fail)"
          % len(canfail))
    print("   a prover plants a defect and requires refusal   %4d" % len(withctl))
    print("   NO control anywhere                             %4d" % len(nocontrol))
    print()
    print("IN THE HOOK CHAIN (these actually block commits): %d" % len(hooked))
    print("   of those, with NO control                      %4d" % len(hooked_nc))
    print()
    if cant:
        print("MODULES THAT CANNOT FAIL:")
        for r in cant:
            print("   %-56s %s" % (r["module"], "IN HOOK CHAIN" if r["in_hook_chain"] else ""))
    if cnd:
        print("COULD NOT DETERMINE:")
        for r in cnd:
            print("   %-56s %s" % (r["module"], r.get("why", "")[:70]))
    print()
    print("CHECKS WITH A CONTROL (%d) -- the ones whose green means something:" % len(withctl))
    for r in withctl:
        print("   %-56s <- %s" % (r["module"], ", ".join(r["provers"])))

    dest = os.path.join(REPO, "outputs", "check_controls_2026_08_25.json")
    if not os.path.isdir(os.path.dirname(dest)):
        os.makedirs(os.path.dirname(dest))
    with io.open(dest, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "population": n, "provers_excluded": len(provers),
            "can_fail": len(canfail), "cannot_fail": len(cant), "cnd": len(cnd),
            "with_control": len(withctl), "no_control": len(nocontrol),
            "hook_chain": len(hooked), "hook_chain_no_control": len(hooked_nc),
            "rows": rows, "DONE": True}, indent=1))
    print("\nwrote %s" % dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
