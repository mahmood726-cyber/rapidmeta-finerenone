"""A refusal added to a collection whose other members have a different shape.

> **A refusal that breaks the contract of the collection it joins is not a refusal, it is a
> different crash wearing a polite sentence.**

THE INSTANCE. `cangrelor-pci-review` killed the page build FOUR times. Three were bare
`next()` over a generator. THE FOURTH WAS THE FIX FOR THE THIRD: the refusal was appended to
`parts` as a bare string, and `projectors.tabbed_body` does `d.get(k)` over every member --
`AttributeError: 'str' object has no attribute 'get'`. The page died on the sentence written
to stop it dying.

WHY THIS IS A HAZARD FOR THIS PROJECT SPECIFICALLY. **Refusing is our default remedy.**
Refusals were added tonight to projectors, to validators, to gates and to prose, and every
one of them is a NEW VALUE ENTERING A STRUCTURE WHOSE OTHER MEMBERS ALREADY HAVE A SHAPE. The
remedy is the risk, and it is the only place tonight where that is true.

WHAT THIS CHECKS. Per function, a list built by `.append()` that receives BOTH a dict literal
and a non-dict value. That is the exact shape of the cangrelor defect: `parts.append({...})`
in the normal path, `parts.append("<div ...>")` in the refusal path, and a consumer that
assumes the first.

WHAT IT CANNOT SEE, said rather than implied: a heterogeneous list is sometimes correct, and
a consumer that handles both shapes is fine -- `build_tabbed` explicitly does
`if isinstance(d, str)` for one such case. The output is CANDIDATES with their file:line, so
the judgement is made against a list rather than against the last traceback.
"""
import io
import os
import sys
import ast
import glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls

SCOPE = ("ssot/build_tabbed.py", "ssot/build_app_v2.py", "ssot/paper_projector.py",
         "ssot/projectors.py", "ssot/projectors2.py", "ssot/validate_v2.py",
         "ssot/assessment.py", "ssot/preconditions.py")

REFUSAL_MARK = ("absent-state", "Refused", "Not rendered", "NOT_ASSESSABLE", "refus")


def _kind(node):
    if isinstance(node, ast.Dict):
        return "dict"
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return "str"
    if isinstance(node, ast.JoinedStr):
        return "str"
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
        return "str" if _kind(node.left) == "str" else "?"
    if isinstance(node, ast.Tuple):
        return "tuple"
    if isinstance(node, ast.List):
        return "list"
    return "?"


def mixed_appends(src):
    """-> [(func, target, [(line, kind, is_refusal, snippet)])] where kinds disagree."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    lines = src.split("\n")
    out = []
    def own_nodes(scope):
        """Nodes in this scope, NOT descending into nested functions.

        THE FIRST VERSION USED ast.walk AND MERGED EVERY FUNCTION'S LOCALS AT MODULE LEVEL.
        Two different functions each with a local list of the same NAME came back as one
        collection holding strings and a tuple, and the ONLY candidate it reported was that
        artefact. A scope-blind walk over a scoped language is not a measurement.
        """
        stack = list(ast.iter_child_nodes(scope))
        while stack:
            n = stack.pop()
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            yield n
            stack.extend(ast.iter_child_nodes(n))

    scopes = [tree] + [n for n in ast.walk(tree)
                       if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    for fn in scopes:
        by_target = {}
        for node in own_nodes(fn):
            if not isinstance(node, ast.Call):
                continue
            f = node.func
            if not (isinstance(f, ast.Attribute) and f.attr == "append"
                    and isinstance(f.value, ast.Name) and node.args):
                continue
            target = f.value.id
            arg = node.args[0]
            ln = getattr(node, "lineno", 0)
            snippet = lines[ln - 1].strip()[:88] if ln else ""
            seg = ast.get_source_segment(src, arg) or ""
            is_ref = any(m in seg for m in REFUSAL_MARK)
            by_target.setdefault(target, []).append((ln, _kind(arg), is_ref, snippet))
        for target, calls in by_target.items():
            kinds = set(k for _l, k, _r, _s in calls if k != "?")
            if len(kinds) > 1 and any(r for _l, _k, r, _s in calls):
                name = getattr(fn, "name", "<module>")
                out.append((name, target, sorted(calls)))
    return out


def main():
    fixture = (
        "def build(canon):\n"
        "    parts = []\n"
        "    for oid in canon['x']:\n"
        "        if oid is None:\n"
        "            parts.append(\"<div class='absent-state'>Refused: no declaration</div>\")\n"
        "            continue\n"
        "        parts.append({'name': 1, 'trials': 2})\n"
        "    return parts\n")
    clean = (
        "def build(canon):\n"
        "    parts = []\n"
        "    for oid in canon['x']:\n"
        "        if oid is None:\n"
        "            parts.append({'name': 'x', 'trials': "
        "\"<div class='absent-state'>Refused</div>\"})\n"
        "            continue\n"
        "        parts.append({'name': 1, 'trials': 2})\n"
        "    return parts\n")
    require_controls(
        "lint_refusal_breaks_its_collection",
        positive=("the cangrelor shape -- a refusal appended as a bare string beside dicts",
                  bool(mixed_appends(fixture)), True),
        negative=("the same refusal appended in the dict shape its neighbours use",
                  bool(mixed_appends(clean)), True))

    print("")
    hits, unparsed = [], []
    for rel in SCOPE:
        path = os.path.join(REPO, rel)
        if not os.path.exists(path):
            unparsed.append((rel, "not on disk"))
            continue
        res = mixed_appends(io.open(path, encoding="utf-8", errors="replace").read())
        if res is None:
            unparsed.append((rel, "does not parse"))
            continue
        for name, target, calls in res:
            hits.append((rel, name, target, calls))

    print("REFUSALS ENTERING A COLLECTION OF A DIFFERENT SHAPE: %d candidate(s)" % len(hits))
    print("UNPARSED (reported, not skipped): %d" % len(unparsed))
    for rel, why in unparsed:
        print("    %s -- %s" % (rel, why))
    print("")
    for rel, name, target, calls in hits:
        print("    %s :: %s() -> `%s`" % (rel, name, target))
        for ln, kind, is_ref, snippet in calls:
            print("        line %-5d %-6s %s %s" % (ln, kind,
                                                    "REFUSAL" if is_ref else "       ",
                                                    snippet))
    if not hits:
        print("    none. Every refusal added in these files enters its collection in the")
        print("    shape its neighbours already use.")
    print("")
    print("CANDIDATES, NOT DEFECTS. A heterogeneous list is sometimes correct and a consumer")
    print("that handles both shapes is fine -- build_tabbed does `if isinstance(d, str)` for")
    print("exactly one such case. What this gives is the population and its file:line.")


if __name__ == "__main__":
    main()
