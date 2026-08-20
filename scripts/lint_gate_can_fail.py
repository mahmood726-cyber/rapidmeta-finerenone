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
import json
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


# WIDENED 2026-08-20 FROM A FILENAME TO A ROLE, and the reason is that the filename
# convention retired the rule as the codebase grew.
#
# This lint was written after four files named `*_gate.py` turned out to be triage tools
# that could only pass. EVERY INSTRUMENT WRITTEN SINCE HAS BEEN NAMED `lint_*` OR `audit_*`,
# so none of them was subject to it -- including eleven written last night. Nobody evaded
# the rule; THE RULE WAS SCOPED TO A NAME AND THE NAMES MOVED. A rule that narrows silently
# as the code grows is worse than no rule, because it keeps reporting a clean result over a
# shrinking population.
#
# THE SCOPE IS NOW THE ROLE: a file that RETURNS A VERDICT. `lint_`, `audit_`, `check_`,
# `verify_`, `prove_`, `*_gate.py`, `*_check.py`. Files that ACT on a gate keep their verb
# exclusion.
#
# AND A FILE THAT CANNOT FAIL IS NOT AUTOMATICALLY A DEFECT UNDER THE WIDER SCOPE. Some are
# TRIAGE by design -- `audit_path_resolvers.py` prints a reading list and says so in its own
# last line. Those are named in KNOWN_TRIAGE rather than being counted as breaches, and each
# entry states why, so "it is only a report" has to be written down rather than assumed.
VERDICT_PREFIX = ("lint_", "audit_", "check_", "verify_", "prove_")
VERDICT_SUFFIX = ("_gate.py", "_check.py")

# Instruments that report rather than refuse, BY DESIGN, each with the reason.
KNOWN_TRIAGE = {
    "audit_path_resolvers.py":
        "prints a reading list of resolver bodies -- 14 found, 12 unread. Its own closing "
        "line: 'this is not a clean bill and it is not a defect count; it is a reading "
        "list.' Blocking on a reading list would block every push until the list is read.",
    "audit_exclusion_by_absence.py":
        "the 1,300-guard population is a report; only the 125 inside a corpus-wide loop are "
        "gated, and that limb DOES exit non-zero under --gate.",
    "audit_class_mechanisation.py":
        "reports the mechanisation table; its --gate limb refuses when a class names a "
        "command that cannot fail.",
    "audit_standing_instructions.py":
        "reports which standing instructions are enforced, coincident or convention. There "
        "is nothing to refuse -- a convention is not a violation.",
}


def returns_a_verdict(fn):
    return (fn.startswith(VERDICT_PREFIX) or fn.endswith(VERDICT_SUFFIX)) \
        and fn.endswith(".py")


def _fails_through_controls(src):
    """require_controls() raises ControlFailed, which subclasses SystemExit.

    THE SAME BLINDNESS THE MECHANISATION AUDIT HAD. An AST search for sys.exit / raise
    SystemExit / return non-zero cannot see a file that fails ONLY through its declared
    controls, and it scored three such files as unable to fail -- two of which refuse a
    degenerate input on every run. A checker that cannot recognise the project's own
    failure idiom reports its own instruments as vacuous.
    """
    return "require_controls(" in src


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    bad, checked, unparsable, excluded, triage = [], 0, [], [], []
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in files:
            if not returns_a_verdict(fn):
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
            if has_failing_exit(tree):
                continue
            if _fails_through_controls(io.open(p, encoding="utf-8",
                                               errors="replace").read()):
                continue
            if fn in KNOWN_TRIAGE:
                triage.append((rel, KNOWN_TRIAGE[fn]))
                continue
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
    if triage:
        print("TRIAGE BY DESIGN -- reports rather than refuses, each with its reason:")
        for rel, why in triage:
            print("   %s" % rel)
            print("      %s" % why)
        print()
    print("files that RETURN A VERDICT   %d checked, %d unparsable, %d excluded by verb "
          "prefix, %d triage by design"
          % (checked, len(unparsable), len(excluded), len(triage)))
    print("cannot ever fail        %d" % len(bad))
    print()
    print("NOT CHECKED: reachability is syntactic. `if False: sys.exit(1)` passes this lint.")
    print("Proving a gate CAN fire on a real input is the known-answer test, a different")
    print("instrument (scripts/known_answer_gate.py).")
    if unparsable:
        print()
        print("REFUSED: unparsable file(s) that return a verdict.")
        return 1
    # RATCHET, BECAUSE THE WIDENING FOUND 45 AT ONCE.
    #
    # Scoped to `*_gate.py` this lint saw about ten files and reported zero. Scoped to
    # anything that RETURNS A VERDICT it sees 163 and finds 45 that cannot fail. THAT
    # DIFFERENCE IS WHAT THE FILENAME SCOPING WAS HIDING -- the rule had been retiring
    # itself for weeks, reporting clean over a population that kept shrinking as a share of
    # the code.
    #
    # Blocking on 45 would block every commit until they are all read, which is how a gate
    # gets bypassed rather than satisfied. They are baselined and THE COUNT MUST NOT RISE.
    # This is not a clearance: a baselined file still cannot fail, and each one is a report
    # wearing a verdict's name.
    ratchet_path = os.path.join(REPO, "scripts", "baselines", "gate_can_fail_baseline.json")
    present = sorted(r.replace("\\", "/") for r in bad)
    if not os.path.exists(ratchet_path):
        os.makedirs(os.path.dirname(ratchet_path), exist_ok=True)
        json.dump({
            "written": "2026-08-20",
            "why": ("The rule 'a file that returns a verdict must be able to fail' was "
                    "scoped to the filename *_gate.py and every instrument written since "
                    "was named lint_ or audit_, so the rule narrowed silently as the "
                    "codebase grew. Widening the scope surfaced 45 at once. NOT A "
                    "CLEARANCE -- each of these still cannot fail. THE COUNT MUST NOT RISE."),
            "cannot_fail": present,
        }, io.open(ratchet_path, "w", encoding="utf-8", newline=chr(10)), indent=1,
            ensure_ascii=False)
        print("wrote baseline with %d files that cannot fail" % len(present))
        return 0

    known = set(json.load(io.open(ratchet_path, encoding="utf-8")).get("cannot_fail") or [])
    new = sorted(set(present) - known)
    healed = sorted(known - set(present))
    if healed:
        print("%d baselined file(s) can now fail, or are gone." % len(healed))
    if new:
        print("REFUSED: %d NEW file(s) that return a verdict and cannot fail:" % len(new))
        for r in new:
            print("   %s" % r)
        return 1
    print("NO NEW FILE THAT CANNOT FAIL. The baseline of %d has not risen." % len(known))
    return 0


if __name__ == "__main__":
    sys.exit(main())
