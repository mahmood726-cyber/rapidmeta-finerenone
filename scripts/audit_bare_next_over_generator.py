"""Every `next(<genexp>)` with no default, found by AST rather than by grep.

WHY AST AND NOT GREP, STATED FIRST BECAUSE IT IS THE POINT. `cangrelor-pci-review` killed
three separate page builds on the same idiom, and the population was measured wrong TWICE:

    grep 'next(o for o in canon["outcomes"]'      -> 10 sites
    ...and the third crash was at a site written  -> next(x for x in canon["outcomes"] ...)

The loop variable was renamed and the string match missed it. A GREP FOR AN IDIOM IS A
STRING MATCH ON A HABIT; THE HABIT VARIES AND THE IDIOM DOES NOT. `next(genexp)` with no
default is a shape, and a shape is exactly what an AST walk finds.

WHAT IT FINDS. `Call(func=Name('next'), args=[GeneratorExp])` with len(args) == 1 -- no
default. That call raises StopIteration when the generator is empty, and StopIteration
carries no message: the traceback names neither the object, nor the key that was missing,
nor the collection that was searched. Three tracebacks in a row on cangrelor said only
`StopIteration`.

NOT ALL OF THEM ARE DEFECTS, and the file says so rather than counting them as such. A
`next(genexp)` over a collection the code has just built, or immediately inside a
try/except StopIteration, is fine. What the sweep gives is the POPULATION and the file:line
of each, so the judgement is made against a list rather than against a memory of where the
last traceback pointed.

AND THE FIX IS NOT A DEFAULT EVERYWHERE. `next(genexp, None)` on a lookup that should never
fail converts a loud defect into a silent one -- registry class 62, the same trade as
`.get(k, default)` masking a present-but-null key. On cangrelor the crash was the LUCKY
symptom: the block it could not find carries a live pooled point of 0.9646 that has never
appeared on the delivered page. Renderers should refuse ON THE PAGE; validators should
raise a NAMED error. Both are visible; a bare default is neither.
"""
import io
import os
import re
import sys
import ast
import glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls

# The paths that build or check a delivered page. A bare next() elsewhere is out of scope
# for this sweep and the scope is stated rather than implied.
RENDER_AND_VALIDATE = ("ssot/build_tabbed.py", "ssot/build_app_v2.py",
                       "ssot/projectors.py", "ssot/projectors2.py",
                       "ssot/paper_projector.py", "ssot/validate_v2.py",
                       "ssot/build_to_standard.py", "ssot/assessment.py",
                       "ssot/preconditions.py")


def bare_next_sites(src, rel):
    """-> [(line, snippet, guarded)] for next(<genexp>) with no default."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    lines = src.split("\n")
    out = []
    # Which line ranges sit inside a `try:` that catches StopIteration?
    protected = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            catches = False
            for h in node.handlers:
                names = []
                if isinstance(h.type, ast.Name):
                    names = [h.type.id]
                elif isinstance(h.type, ast.Tuple):
                    names = [n.id for n in h.type.elts if isinstance(n, ast.Name)]
                elif h.type is None:
                    names = ["BaseException"]
                if any(n in ("StopIteration", "Exception", "BaseException")
                       for n in names):
                    catches = True
            if catches:
                for st in node.body:
                    lo = getattr(st, "lineno", 0)
                    hi = getattr(st, "end_lineno", lo)
                    protected.update(range(lo, hi + 1))

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not (isinstance(node.func, ast.Name) and node.func.id == "next"):
            continue
        if len(node.args) != 1:
            continue                       # a default was given
        if not isinstance(node.args[0], ast.GeneratorExp):
            continue                       # next(iterator) is a different thing
        ln = getattr(node, "lineno", 0)
        out.append((ln, lines[ln - 1].strip()[:96] if ln else "",
                    ln in protected))
    return out


def _all_genexp_next(src):
    """Every next(<genexp>), default or not -- the denominator for the zero."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return 0
    n = 0
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "next" and node.args
                and isinstance(node.args[0], ast.GeneratorExp)):
            n += 1
    return n


def main():
    # CONSTRUCTED CONTROLS -- the positive is the exact shape that killed three builds,
    # with the loop variable RENAMED, because a rename is what defeated the grep.
    bad = "o = next(x for x in canon['outcomes'] if x['id'] == oid)\n"
    good = "o = next((x for x in canon['outcomes'] if x['id'] == oid), None)\n"
    require_controls(
        "audit_bare_next_over_generator",
        positive=("a bare next() over a genexp with the loop variable renamed -- the shape "
                  "the grep missed", bool(bare_next_sites(bad, "fixture")), True),
        negative=("the same call with a default supplied",
                  bool(bare_next_sites(good, "fixture")), True))

    print("")
    total, unguarded, unparsed = 0, [], []
    seen_any = [0]
    for rel in RENDER_AND_VALIDATE:
        path = os.path.join(REPO, rel)
        if not os.path.exists(path):
            unparsed.append((rel, "not on disk"))
            continue
        src = io.open(path, encoding="utf-8", errors="replace").read()
        sites = bare_next_sites(src, rel)
        if sites is None:
            unparsed.append((rel, "does not parse"))
            continue
        seen_any[0] += _all_genexp_next(src)
        for ln, snippet, prot in sites:
            total += 1
            if not prot:
                unguarded.append((rel, ln, snippet))

    print("RENDER AND VALIDATE PATHS SWEPT: %d file(s), %d unparsed (reported, not skipped)"
          % (len(RENDER_AND_VALIDATE) - len(unparsed), len(unparsed)))
    for rel, why in unparsed:
        print("    %s -- %s" % (rel, why))
    print("")
    # CLASS 52: A ZERO HAS TWO READINGS. This one states its denominator, so "none found"
    # cannot be confused with "the search could not match". The detector proved it can
    # match on its positive control; this line proves it saw the population.
    print("next(<genexp>) calls seen in these files: %d" % seen_any[0])
    print("BARE next(<genexp>) WITH NO DEFAULT: %d" % total)
    if total == 0 and seen_any[0] > 0:
        print("    -> LOOKED AND FOUND NONE. %d such calls exist and every one supplies a"
              % seen_any[0])
        print("       default, so this zero is a measurement rather than a failure to "
              "match.")
    elif total == 0:
        print("    -> NOT_ASSESSABLE: no next(<genexp>) call of any kind was seen. The "
              "search cannot match.")
    print("of those, NOT inside a try that catches StopIteration: %d" % len(unguarded))
    print("")
    print("MEASURED BY SHAPE. The grep that preceded this found 10 by matching")
    print("`next(o for o in canon[\"outcomes\"]` and missed a site written with `x` as the")
    print("loop variable -- which is the one that killed the third build.")
    print("")
    for rel, ln, snippet in unguarded:
        print("    %s:%d" % (rel, ln))
        print("        %s" % snippet)

    print("")
    print("NOT ALL OF THESE ARE DEFECTS. A next() over a collection the code has just built")
    print("cannot be empty. What this gives is the POPULATION and its file:line, so the")
    print("judgement is made against a list rather than against wherever the last traceback")
    print("happened to point.")


if __name__ == "__main__":
    main()
