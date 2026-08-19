#!/usr/bin/env python3
"""A FILE NAMED `*_gate.py` MUST BE ABLE TO FAIL. The name is a promise; this keeps it.

FOUND BY A CORPUS SWEEP, 2026-08-19. Four files named `*_gate.py` --
internal_consistency_gate, arm_role_gate, metric_consistency_gate, subject_role_gate -- had NO
reachable non-zero exit. They could only ever pass.

AND THEY WERE NOT BROKEN. Reading them settled it: each self-describes as advisory --
"TRIAGE, NOT A VERDICT", "A flag means READ THE TRIAL". They were correctly-designed triage
tools wearing the wrong name. The defect was the NAME, not the behaviour, and wiring them to
block would have contradicted their own stated contract. All four are now `*_triage.py`.

    A GATE THAT CANNOT FAIL IS NOT A DEFECT WHILE NOTHING RUNS IT. IT IS A TRAP FOR WHOEVER
    WIRES IT IN NEXT, who will reasonably assume a thing called a gate can block.

That is why this is a lint and not a one-off cleanup: the four files were fixed by renaming, but
nothing stopped the fifth from being written tomorrow. The convention only holds if it is
mechanical.

THE RULE: a module whose filename ends `_gate.py` must contain a REACHABLE non-zero exit --
`sys.exit(1)`, `sys.exit(2)`, `return 1` from main, `raise SystemExit(...)` with a message, or
an explicit non-zero exit code. A module that merely PRINTS failures is a report, and reports
are named `_triage.py`, `_check.py`, `_census.py` or anything else.

WHAT IT DOES NOT CHECK, named rather than implied: reachability is judged SYNTACTICALLY -- the
statement exists in the file. It does not prove any input can actually reach it. A gate with
`if False: sys.exit(1)` passes this lint and cannot fail in practice. Proving reachability is
the known-answer test (scripts/known_answer_gate.py), which is a different instrument; this one
only enforces that the promise is present in the source at all.
"""
import ast
import io
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", "__pycache__", "node_modules", "figs", "sources"}

# A VERB PREFIX PUTS 'gate' IN THE OBJECT POSITION, NOT THE SUBJECT. `add_f1000_gate.py` and
# `extend_alignment_gate.py` are one-off scripts that MODIFY a gate; `test_build_gate.py` is a
# TEST OF a gate. None of them claims to be one, so none owes a failing exit.
#
# This is exactly the move that turns a guard into a formality, so the exclusions are COUNTED
# AND NAMED on every run. If that list starts growing, it is being used as a hiding place --
# and the fix then is to rename the file, not to extend this tuple.
ACTS_ON_A_GATE = ("test_", "add_", "extend_", "fix_", "make_", "regenerate_")


def _returns_nonzero(tree, fname):
    """Does the module-level function `fname` ever return a non-zero constant?

    THE IDIOM THAT DEFEATED THE FIRST VERSION OF THIS LINT. `sys.exit(main())` is the standard
    gate shape, so a non-constant argument was treated as 'can fail'. But all four files that
    motivated this lint end exactly that way with a `main()` whose only return is 0 -- so the
    first version WOULD HAVE MISSED THE FOUR FILES IT WAS WRITTEN FOR. Caught by testing it
    against them rather than against an invented probe, which is the whole standard here.

    Resolved conservatively: if the named function cannot be found, or returns something this
    cannot evaluate (a variable, a call), the answer is True -- unproven is not the same as
    proven-safe, and a lint should not manufacture a failure it cannot demonstrate.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == fname:
            saw_unknown = False
            for r in ast.walk(node):
                if isinstance(r, ast.Return) and r.value is not None:
                    if isinstance(r.value, ast.Constant) and isinstance(r.value.value, int):
                        if r.value.value != 0:
                            return True
                    else:
                        saw_unknown = True
            return saw_unknown
    return True                       # function not found: do not claim it cannot fail


def has_failing_exit(tree):
    """True if the module contains a non-zero exit / SystemExit / `return 1`."""
    for node in ast.walk(tree):
        # sys.exit(1) / exit(2) / sys.exit(main())  -- the last is a real gate idiom
        if isinstance(node, ast.Call):
            fn = node.func
            name = getattr(fn, "attr", None) or getattr(fn, "id", None)
            if name in ("exit", "_exit"):
                if not node.args:
                    continue                       # exit() with no code == exit(0)
                a = node.args[0]
                if isinstance(a, ast.Constant) and isinstance(a.value, int):
                    if a.value != 0:
                        return True
                elif isinstance(a, ast.Call) and getattr(a.func, "id", None):
                    # sys.exit(main()) -- resolve main() rather than assume it can fail
                    if _returns_nonzero(tree, a.func.id):
                        return True
                else:
                    return True                    # sys.exit(<expr>) we cannot resolve
        if isinstance(node, ast.Raise):
            exc = node.exc
            nm = getattr(getattr(exc, "func", None), "id", None) or getattr(exc, "id", None)
            if nm == "SystemExit":
                return True
        # `return 1` (or any non-zero int) from a function
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, int) and node.value.value != 0:
                return True
    return False


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    bad, checked, unparsable, excluded = [], 0, [], []
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in files:
            if not fn.endswith("_gate.py"):
                continue
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, REPO)
            if fn.startswith(ACTS_ON_A_GATE):
                excluded.append(rel)
                continue
            try:
                tree = ast.parse(io.open(p, encoding="utf-8", errors="replace").read())
            except (SyntaxError, OSError) as e:
                unparsable.append((rel, str(e)[:60]))   # reported, never skipped
                continue
            checked += 1
            if not has_failing_exit(tree):
                bad.append(rel)

    for rel in bad:
        print("%s" % rel)
        print("      named a GATE but contains no reachable non-zero exit: it can only pass.")
    for rel, err in unparsable:
        print("%s  UNPARSABLE (%s) -- reported, not skipped" % (rel, err))
    print()
    if excluded:
        print("excluded -- a VERB prefix puts 'gate' in the object position, so the file acts")
        print("ON a gate rather than being one. Counted and named every run:")
        for rel in excluded:
            print("   %s" % rel)
        print()
    print("files named *_gate.py   %d checked, %d unparsable, %d excluded by verb prefix"
          % (checked, len(unparsable), len(excluded)))
    print("cannot ever fail        %d" % len(bad))
    print()
    print("NOT CHECKED: reachability is syntactic. `if False: sys.exit(1)` passes this lint.")
    print("Proving a gate CAN fire on a real input is the known-answer test, a different")
    print("instrument (scripts/known_answer_gate.py).")
    if bad or unparsable:
        print()
        print("REFUSED: %d file(s) named *_gate.py cannot fail." % len(bad)
              if bad else "REFUSED: unparsable file(s) named *_gate.py.")
        print("FIX: give it a reachable non-zero exit, or rename it -- a report is *_triage.py,")
        print("     *_check.py, *_census.py. The name is a promise about what the file can do.")
        return 1
    print()
    print("every file named a gate can fail.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
