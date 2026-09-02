"""UNORDERED ITERATION LINT -- a result decided by hash order is not a result.

THE CLASS. `min`, `max`, `next` and `[0]` applied to a `set`, a `glob` or an
`iterdir()` pick a winner out of an order nobody chose. Sets iterate in hash
order, which varies with PYTHONHASHSEED for str and bytes; directory listings
vary with the filesystem. The code runs, returns something plausible, and
returns something different on the next machine. Eight sites were measured
across three sweep scripts; two are fixed.

THE HISTORY OF THIS LINT, WHICH IS THE POINT OF IT

    The first version reported `0 of 1407` on a codebase containing the very
    line it had been written from. It matched the INLINE form --
    `next(iter(set(x)))` -- while the real code bound a variable first:

        cands = set(...)
        pick  = next(iter(cands))

    A regex over source text cannot see that, because the two lines are not
    adjacent and share no distinctive token. A ZERO FROM AN INSTRUMENT THAT
    CANNOT SEE THE SHAPE IT IS LOOKING FOR IS NOT A CLEAN RESULT; and a zero
    that arrives with a large, specific denominator -- 1407 -- reads as
    thoroughness, which is worse than no number at all.

    So this version parses to an AST and TRACKS THE BINDING within each function
    scope. Its self-test plants BOTH forms, and the variable-bound one is the
    one that matters, because it is the one that was missed.

    Its zero, wherever it appears, reads NOT OBSERVED and never SAFE.

WHAT COUNTS AS UNORDERED HERE

    set(...), frozenset(...), a `{...}` set literal, a set comprehension,
    glob.glob/iglob, Path.glob/rglob/iterdir, os.listdir, os.scandir, and
    set operations on those (| & - ^).

    A dict is NOT unordered. Python has guaranteed insertion order since 3.7,
    and flagging `next(iter(d))` would be a false warning. This is an exclusion
    made deliberately and stated so, not an oversight.

WHAT COUNTS AS ORDER-CONSUMING

    next(...), x[0], x[-1], list(x)[i], tuple(x)[i], and `min`/`max` WITH a
    `key=` argument -- where ties are broken by iteration order, so the answer
    depends on hash order even though the function looks total.

    `min(s)` / `max(s)` with NO key over comparable scalars is deterministic and
    is NOT flagged. That exclusion is counted and printed, so if it ever starts
    absorbing real sites the number will say so.

    `sorted(x)` fixes an order and is the fix, not the defect. Anything reached
    through `sorted()` is clean.

WHAT IT CANNOT SEE -- printed with every verdict

    * A binding that crosses a function boundary, a class attribute, a module
      global read in another function, or a value passed in as a parameter.
      Tracking is per-function-scope by design; anything wider needs types.
    * An unordered source this file does not name -- a third-party function
      returning a set, a `.keys()` on a dict that was itself built from a set.
    * Nondeterminism from anything other than iteration order.
    * Whether a flagged site actually MATTERS. Some picks are genuinely
      arbitrary-by-design; those want a comment and a `sorted()` anyway, because
      a reader cannot tell the two apart either.

USAGE

    python scripts/lint_unordered_iteration.py --selftest
    python scripts/lint_unordered_iteration.py --diff origin/main   # DEFAULT
    python scripts/lint_unordered_iteration.py --all
    python scripts/lint_unordered_iteration.py path/to/file.py ...

Exit code: +1 if any site was found in scope, +2 if any file could not be read
or parsed. A file that will not parse is NOT a file with no findings.
"""
from __future__ import annotations

import argparse
import ast
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

UNORDERED_CALLS = {
    "set", "frozenset",
    "glob", "iglob",           # glob.glob / glob.iglob
    "listdir", "scandir",      # os.listdir / os.scandir
    "iterdir", "rglob",        # Path.iterdir / Path.rglob; Path.glob shares "glob"
}
ORDER_FIXERS = {"sorted"}
SKIP_DIRS = {".git", "__pycache__", "node_modules", "figs", "sources",
             "archived", "retired", "removed", "delisted"}


def _call_name(node):
    f = node.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return None


def _is_unordered_expr(node, bound):
    """Is this expression an unordered collection?"""
    if isinstance(node, (ast.SetComp, ast.Set)):
        return "a set literal or set comprehension"
    if isinstance(node, ast.Call):
        name = _call_name(node)
        if name in ORDER_FIXERS:
            return None
        if name in UNORDERED_CALLS:
            return "%s()" % name
        return None
    if isinstance(node, ast.Name):
        return bound.get(node.id)
    if isinstance(node, ast.BinOp) and isinstance(
            node.op, (ast.BitOr, ast.BitAnd, ast.Sub, ast.BitXor)):
        return (_is_unordered_expr(node.left, bound)
                or _is_unordered_expr(node.right, bound))
    return None


_FUNC = (ast.FunctionDef, ast.AsyncFunctionDef)


def _own_nodes(scope):
    """Every node belonging to THIS scope, not to a function nested inside it.

    `ast.walk` descends through nested function bodies, so walking the module
    and then walking each function visits every function body twice and reports
    every finding twice. A duplicated finding is not merely untidy: it doubles
    the number this lint reports, and the whole point of the file is that its
    numbers can be trusted.
    """
    out, stack = [], [scope]
    while stack:
        node = stack.pop()
        out.append(node)
        for child in ast.iter_child_nodes(node):
            if isinstance(child, _FUNC) and child is not scope:
                continue
            stack.append(child)
    return out


class _ScopeVisitor(ast.NodeVisitor):
    """One function (or module) scope: bind names, then judge the reads.

    TWO PASSES, AND THAT IS THE WHOLE FIX. A single pass in source order misses
    a use that precedes its assignment textually inside a loop, and -- more to
    the point -- a one-pass regex misses the binding entirely, which is what
    made the first version of this lint report zero on the file it came from.
    """

    def __init__(self, path, findings, stats, inherited=None):
        self.path, self.findings, self.stats = path, findings, stats
        self.bound = dict(inherited or {})

    def bind(self, nodes):
        for node in nodes:
            if isinstance(node, ast.Assign):
                why = _is_unordered_expr(node.value, self.bound)
                if why:
                    for t in node.targets:
                        if isinstance(t, ast.Name):
                            self.bound[t.id] = why
            elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
                if node.value is not None:
                    why = _is_unordered_expr(node.value, self.bound)
                    if why and isinstance(node.target, ast.Name):
                        self.bound[node.target.id] = why
            elif isinstance(node, ast.For):
                # `for p in glob.glob(...)` iterates an unordered sequence, but
                # the LOOP is not the defect -- taking one element out of it is.
                pass

    def judge(self, nodes):
        for node in nodes:
            if isinstance(node, ast.Call):
                name = _call_name(node)
                if name == "next" and node.args:
                    arg = node.args[0]
                    inner = (arg.args[0] if isinstance(arg, ast.Call)
                             and _call_name(arg) == "iter" and arg.args else arg)
                    why = _is_unordered_expr(inner, self.bound)
                    if why:
                        self._add(node, "next()", why)
                elif name in ("min", "max"):
                    if not node.keywords:
                        # min/max with no key over comparable scalars is total.
                        if node.args and _is_unordered_expr(node.args[0],
                                                            self.bound):
                            self.stats["excluded_total_minmax"] += 1
                        continue
                    if any(k.arg == "key" for k in node.keywords) and node.args:
                        why = _is_unordered_expr(node.args[0], self.bound)
                        if why:
                            self._add(node, "%s(..., key=...)" % name, why)
            elif isinstance(node, ast.Subscript):
                v = node.value
                inner = v
                if isinstance(v, ast.Call) and _call_name(v) in ("list", "tuple"):
                    inner = v.args[0] if v.args else None
                if inner is None:
                    continue
                why = _is_unordered_expr(inner, self.bound)
                if why:
                    self._add(node, "subscripting", why)

    def _add(self, node, op, why):
        self.findings.append({
            "file": self.path, "line": getattr(node, "lineno", 0),
            "op": op, "source": why})


def scan_source(src, path, findings, stats):
    tree = ast.parse(src)
    # Module scope first, so a function that closes over a module-level binding
    # still sees it; then each function on its own nodes, so nothing is judged
    # twice.
    module_nodes = _own_nodes(tree)
    top = _ScopeVisitor(path, findings, stats)
    top.bind(module_nodes)
    top.judge(module_nodes)
    for node in ast.walk(tree):
        if isinstance(node, _FUNC):
            own = _own_nodes(node)
            v = _ScopeVisitor(path, findings, stats, inherited=top.bound)
            v.bind(own)
            v.judge(own)
    return findings


def scan_file(path, repo, findings, stats, unreadable):
    rel = os.path.relpath(path, repo).replace(os.sep, "/")
    try:
        with open(path, "rb") as fh:
            src = fh.read().decode("utf-8", "replace")
    except Exception as exc:
        unreadable.append((rel, "unreadable: %s" % exc))
        return
    try:
        scan_source(src, rel, findings, stats)
    except SyntaxError as exc:
        # A FILE THAT WILL NOT PARSE IS NOT A FILE WITH NO FINDINGS.
        unreadable.append((rel, "does not parse: %s" % exc))


# --------------------------------------------------------------------------
# scope

def diff_files(base, repo):
    r = subprocess.run(["git", "diff", "--name-only", "%s...HEAD" % base,
                        "--", "*.py"], cwd=repo, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        return None, (r.stderr or "").strip()[:200]
    out = []
    for n in r.stdout.split("\n"):
        n = n.strip()
        p = os.path.join(repo, n.replace("/", os.sep))
        if n and os.path.exists(p):
            out.append(p)
    return out, None


def all_files(repo):
    out = []
    for root, dirs, names in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for n in names:
            if n.endswith(".py"):
                out.append(os.path.join(root, n))
    return sorted(out)


# --------------------------------------------------------------------------

def report(findings, unreadable, n_files, scope_note, stats, wall, cpu,
           not_reached):
    by_file = {}
    for f in findings:
        by_file.setdefault(f["file"], []).append(f)
    for path in sorted(by_file):
        print("\n%s" % path)
        for f in sorted(by_file[path], key=lambda x: x["line"]):
            print("  line %-5d %s over %s"
                  % (f["line"], f["op"], f["source"]))
    for rel, why in unreadable:
        print("\nNOT_OBSERVED  %s -- %s" % (rel, why))

    print("\n" + "-" * 74)
    print("COVERAGE   %d file(s) parsed of %d %s"
          % (n_files - len(unreadable), n_files, scope_note))
    print("           %d site(s) found in %d file(s)" % (len(findings),
                                                         len(by_file)))
    if unreadable:
        print("           %d file(s) could NOT be parsed and were therefore not "
              "checked at all" % len(unreadable))
    print("EXCLUDED   %d bare min()/max() over an unordered collection with no "
          "key=." % stats["excluded_total_minmax"])
    print("           Those are total over comparable scalars and deterministic. "
          "The count is")
    print("           printed so that if this exclusion ever starts absorbing "
          "real sites, the")
    print("           number says so.")
    print("BLIND TO   a binding that crosses a function boundary, a class "
          "attribute, a module")
    print("           global, or a parameter; an unordered source not named in "
          "this file;")
    print("           nondeterminism from anything but iteration order; whether "
          "a flagged pick")
    print("           actually matters.")
    if not findings:
        print("VERDICT    NOT OBSERVED -- no site was found in the files "
              "examined. This is NOT")
        print("           a statement that the tree is free of the class. The "
              "first version of")
        print("           this lint reported 0 of 1407 on a codebase containing "
              "the line it was")
        print("           written from.")
    if not_reached:
        print("           NOT REACHED: %d file(s)" % len(not_reached))
    print("COST       %.2fs wall, %.2fs CPU" % (wall, cpu))
    return (1 if findings else 0) + (2 if (unreadable or not_reached) else 0)


# --------------------------------------------------------------------------
# self-test -- BOTH forms, and the variable-bound one is the one that matters

_PLANTED = '''
import glob, os
from pathlib import Path

def inline_form(x):
    return next(iter(set(x)))                 # 6: the form v1 could see

def variable_bound_form(x):
    cands = set(x)                            # THE FORM v1 MISSED
    pick = next(iter(cands))                  # 10
    return pick

def bound_through_a_glob(root):
    files = glob.glob(root + "/*.json")       # 14
    return files[0]                           # 15

def bound_through_iterdir(root):
    entries = Path(root).iterdir()
    first = list(entries)[0]                  # 19
    return first

def keyed_min_over_a_set(x):
    s = {a for a in x}
    return min(s, key=len)                    # 24

def set_algebra(a, b):
    both = set(a) | set(b)
    return sorted(both)[0]                    # 28 -- CLEAN, sorted fixes it

def bare_min_is_total(x):
    return min(set(x))                        # 31 -- CLEAN, and counted

def a_dict_is_ordered(d):
    return next(iter(d))                      # 34 -- CLEAN, dicts keep order

def os_listdir(root):
    names = os.listdir(root)
    return names[0]                           # 38
'''

_FIXED = '''
import glob, os
from pathlib import Path

def inline_form(x):
    return sorted(set(x))[0]

def variable_bound_form(x):
    cands = sorted(set(x))
    return cands[0]

def bound_through_a_glob(root):
    files = sorted(glob.glob(root + "/*.json"))
    return files[0]

def bound_through_iterdir(root):
    entries = sorted(Path(root).iterdir())
    return entries[0]

def keyed_min_over_a_set(x):
    s = sorted({a for a in x})
    return min(s, key=len)
'''


def selftest():
    ok = True
    print("=== the plant must fire before the fix is allowed to pass ===")

    findings, stats = [], {"excluded_total_minmax": 0}
    scan_source(_PLANTED, "__control_planted.py", findings, stats)
    lines = sorted(f["line"] for f in findings)
    want = [6, 10, 15, 19, 24, 38]
    good = lines == want
    ok = ok and good
    print("  %-8s planted sites fired at lines %s (expected %s)"
          % ("correct" if good else "WRONG", lines, want))

    # THE ONE THAT MATTERS: the variable-bound form, which v1 could not see.
    bound_hit = any(f["line"] == 10 for f in findings)
    ok = ok and bound_hit
    print("  %-8s the VARIABLE-BOUND form at line 10 -- the shape the first "
          "version of this lint reported zero on"
          % ("correct" if bound_hit else "WRONG"))

    clean = [ln for ln in (28, 31, 34) if ln in lines]
    good = not clean
    ok = ok and good
    print("  %-8s sorted(), a bare min(), and a dict are NOT flagged "
          "(false positives at %s)" % ("correct" if good else "WRONG", clean))

    good = stats["excluded_total_minmax"] == 1
    ok = ok and good
    print("  %-8s the bare min() exclusion is COUNTED (%d), not silent"
          % ("correct" if good else "WRONG", stats["excluded_total_minmax"]))

    findings2, stats2 = [], {"excluded_total_minmax": 0}
    scan_source(_FIXED, "__control_fixed.py", findings2, stats2)
    good = not findings2
    ok = ok and good
    print("  %-8s the same file with every site sorted(): %d finding(s)"
          % ("correct" if good else "WRONG", len(findings2)))

    # An unparseable file must NOT read as clean.
    unread = []
    import tempfile
    fd, p = tempfile.mkstemp(suffix=".py")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write("def broken(:\n")
    try:
        scan_file(p, os.path.dirname(p), [], {"excluded_total_minmax": 0},
                  unread)
        good = len(unread) == 1
        ok = ok and good
        print("  %-8s a file that does not parse is reported, not counted clean"
              % ("correct" if good else "WRONG"))
    finally:
        os.unlink(p)

    print("\nself-test %s" % ("PASSED" if ok else "FAILED"))
    return 0 if ok else 1


# --------------------------------------------------------------------------

def run_controls():
    """Both controls, before any count is printed.

    THE CONTROLS ARE SYNTHETIC ON PURPOSE. A control anchored to a live corpus
    item retires itself the moment the defect is fixed: it then either fails and
    looks like a regression, or passes for the wrong reason. These are
    constructed, pinned in this file, and cannot drift. The negative side is not
    optional -- over-flagging is this gate's failure mode, and a false finding
    discredits the true ones.
    """
    from instrument_controls import require_controls

    planted, stats_p = [], {"excluded_total_minmax": 0}
    scan_source(_PLANTED, "__control_planted.py", planted, stats_p)
    fixed, stats_f = [], {"excluded_total_minmax": 0}
    scan_source(_FIXED, "__control_fixed.py", fixed, stats_f)
    require_controls(
        "lint_unordered_iteration",
        positive=("a synthetic module carrying the VARIABLE-BOUND form the "
                  "first version of this lint reported zero on",
                  sorted(f["line"] for f in planted), [6, 10, 15, 19, 24, 38]),
        # require_controls REFUSES WHEN actual == forbidden, so the forbidden
        # value is the one the clean module must never produce. Passing the
        # count with 0 as "must not be" says the opposite, and this control
        # caught that miswiring on its first real run -- which is the whole
        # argument for the negative side.
        negative=("the same module with every site routed through sorted()",
                  "flagged %d site(s)" % len(fixed) if fixed else "clean",
                  "flagged"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--diff", metavar="BASE")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--timeout-seconds", type=float, default=180.0)
    ap.add_argument("--json", metavar="PATH")
    a = ap.parse_args(argv)

    if a.selftest:
        return selftest()

    # NOTHING IS PRINTED BEFORE THE CONTROLS HOLD.
    run_controls()

    repo = os.path.abspath(a.repo)
    not_reached = []
    if a.files:
        paths = [os.path.abspath(p) for p in a.files]
        scope_note = "file(s) named on the command line"
    elif a.all:
        paths = all_files(repo)
        scope_note = "Python file(s) in the tree"
    else:
        base = a.diff or "origin/main"
        paths, err = diff_files(base, repo)
        if paths is None:
            print("INVALID: cannot compute the diff against %s: %s" % (base, err))
            print("A lint that cannot establish its own scope reports that, "
                  "rather than checking nothing and calling it clean.")
            return 2
        scope_note = "Python file(s) changed against %s" % base

    t0, c0 = time.time(), time.process_time()
    deadline = t0 + a.timeout_seconds
    findings, unreadable = [], []
    stats = {"excluded_total_minmax": 0}
    for i, p in enumerate(paths):
        if time.time() > deadline:
            not_reached = paths[i:]
            print("TIMED_OUT after %.1fs: %d file(s) were not reached."
                  % (a.timeout_seconds, len(not_reached)))
            break
        scan_file(p, repo, findings, stats, unreadable)
    wall, cpu = time.time() - t0, time.process_time() - c0

    rc = report(findings, unreadable, len(paths), scope_note, stats, wall, cpu,
                not_reached)
    if a.json:
        import json as _json
        with open(a.json, "w", encoding="utf-8") as fh:
            _json.dump({"findings": findings, "unreadable": unreadable,
                        "scope": scope_note, "n_files": len(paths),
                        "excluded_total_minmax":
                            stats["excluded_total_minmax"],
                        "not_reached": [os.path.basename(p)
                                        for p in not_reached],
                        "wall_seconds": wall, "cpu_seconds": cpu}, fh, indent=1)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
