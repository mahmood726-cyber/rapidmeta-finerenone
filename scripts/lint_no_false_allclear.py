#!/usr/bin/env python3
"""ABSENCE MUST NOT BE COERCED INTO ZERO. The difference here is 3 topics versus 135.

THE MEASUREMENT THAT MAKES THIS BINDING, 2026-08-19: of 135 topic objects, 3 carry a
`k_cascade`. 132 have never had k counted at all. The corpus reports 0 topics with a nonzero
unscreened remainder -- true, and read alone the most misleading number this project could
publish.

    A CORPUS OF 135 TOPICS REPORTING "0 UNSCREENED REMAINDER" IS NOT A CLEAN BACKLOG.
    IT IS 132 TOPICS THAT WERE NEVER ASKED THE QUESTION.

Three states, and they are not two:

    remainder: 0        counted, and nothing is left        -> may enter an all-clear
    REMAINDER_ABSENT    a cascade exists, no remainder key   -> UNKNOWN
    NO_CASCADE          k was never counted at all           -> UNKNOWN

The census that found this kept them distinct and so reported the truth. Any summary that adds
them produces a FALSE ALL-CLEAR over 132 topics.

THE MECHANICAL SIGNATURE, which is why this is lintable rather than a policy: the coercion is
almost always written as a DEFAULT ON A READ.

    obj.get("k_unscreened_remainder", 0)      # absent -> 0.  THE BUG.
    (cascade or {}).get("k_unscreened_remainder") or 0    # absent -> 0.  THE BUG.
    obj.get("k_unscreened_remainder")         # absent -> None. Correct: unknown stays unknown.

`sum(...)`, `all(... == 0)`, and `not any(...)` over a field that may be absent have the same
effect, and are flagged when the field is one of the census fields.

WHAT THIS DOES NOT CHECK, named rather than implied: it cannot tell whether a HUMAN-WRITTEN
sentence in a markdown report sums the two states. It checks code. A prose summary claiming the
corpus is clear remains a human responsibility, and the registry's headline section is where
that claim is bound.

    PROVEN BY GRAFT 2026-08-20: scripts/prove_never_fired_by_graft.py constructs an
    input this check must refuse, inside a temp tree so it is the only corpus the check
    can see, and requires a non-zero exit. Before that this check had never fired on
    any real run -- CAPABLE OF FAILING, CONDITION NOT YET OBSERVED, which is a
    legitimate state and a different one from vacuous.
"""
import ast
import io
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", "__pycache__", "node_modules", "figs", "sources"}
SKIP_TOKEN = "lint:absence-is-not-zero"

# Fields where ABSENT and ZERO mean different things, and conflating them overstates completion.
CENSUS_FIELDS = {
    "k_unscreened_remainder",
    "k0_surfaced", "k2_role_located", "k3_experimental",
    "k4_comparator", "k5_background", "kNA_not_assessable",
    "k_included_in_object",
}


def scan(tree, src_lines):
    out = []

    def line_ok(node):
        i = node.lineno - 1
        return 0 <= i < len(src_lines) and SKIP_TOKEN not in src_lines[i]

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if getattr(fn, "attr", None) != "get" or len(node.args) < 2:
            continue
        key = node.args[0]
        default = node.args[1]
        if not (isinstance(key, ast.Constant) and key.value in CENSUS_FIELDS):
            continue
        if isinstance(default, ast.Constant) and default.value == 0:
            if line_ok(node):
                out.append((node.lineno, key.value,
                            "`.get(%r, 0)` turns ABSENT into ZERO" % key.value))
    # `<get(...)> or 0` -- same coercion, different spelling
    for node in ast.walk(tree):
        if not isinstance(node, ast.BoolOp) or not isinstance(node.op, ast.Or):
            continue
        vals = node.values
        if len(vals) != 2:
            continue
        left, right = vals
        if not (isinstance(right, ast.Constant) and right.value == 0):
            continue
        for sub in ast.walk(left):
            if (isinstance(sub, ast.Call) and getattr(sub.func, "attr", None) == "get"
                    and sub.args and isinstance(sub.args[0], ast.Constant)
                    and sub.args[0].value in CENSUS_FIELDS):
                if line_ok(node):
                    out.append((node.lineno, sub.args[0].value,
                                "`... or 0` turns ABSENT into ZERO"))
                break
    return out


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    hits, scanned = [], 0
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in files:
            if not fn.endswith(".py"):
                continue
            p = os.path.join(root, fn)
            try:
                src = io.open(p, encoding="utf-8", errors="replace").read()
                tree = ast.parse(src)
            except (SyntaxError, OSError):
                continue
            scanned += 1
            for lineno, field, why in scan(tree, src.split("\n")):
                hits.append((os.path.relpath(p, REPO), lineno, field, why))

    for rel, lineno, field, why in hits:
        print("%s:%d  %s" % (rel, lineno, why))
        print("      ABSENT means k was never counted. ZERO means it was counted and is clear.")
    print()
    print("python files scanned            %d" % scanned)
    print("census fields guarded           %d" % len(CENSUS_FIELDS))
    print("absence-coerced-to-zero sites   %d" % len(hits))
    if hits:
        print()
        print("REFUSED: %d site(s) turn an uncounted topic into a clear one." % len(hits))
        print("FIX: read it without a default and handle None explicitly -- NO_CASCADE and")
        print("     REMAINDER_ABSENT are UNKNOWN, not zero, and must not enter an all-clear.")
        print("Deliberate exception: # lint:absence-is-not-zero on the line.")
        return 1
    print()
    print("no code turns an uncounted topic into a clear one.")
    print("NOT CHECKED: prose. A human sentence claiming the corpus is clear is bound by the")
    print("HEADLINE section of DEFECT-REGISTRY.md, not by this lint.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
