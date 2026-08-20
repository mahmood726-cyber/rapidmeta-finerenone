"""Can a recovery, rollback or cleanup path in this pipeline raise?

A RECOVERY PATH ONLY EXECUTES WHEN SOMETHING HAS ALREADY FAILED. So a failure inside it
lands on a system that is already in a bad state, and it is the LEAST EXERCISED CODE IN THE
REPOSITORY -- it runs on the rare branch, usually unattended, usually with nobody reading.

THE INSTANCE. `rebuild_paper_corpus_2026_08_20.py` restored a page with

    shutil.move(backup, page)

and the backup was not there. FileNotFoundError, and THE WHOLE BATCH DIED WITH IT, taking
the remaining pages down. The page it was trying to protect was left as the new build with
nothing saying so.

WHAT COUNTS AS A RECOVERY PATH HERE. A statement that restores, removes, renames back or
cleans up, sitting in one of:

    an `except` block                 -- runs because something already raised
    a `finally` block                 -- runs on the way out, including the failing way
    a branch whose name says failure  -- `if not ok`, `if failed`, `rollback`, `restore`

AND THE TEST IS NOT "does it have a try". It is whether the recovery statement ITSELF can
raise: `os.remove` on a path that may be gone, `shutil.move` onto an existing target,
`os.rename` across devices, `json.load` on a file that may be empty -- the last of which is
exactly how a zero-byte object crashed a checker earlier tonight instead of being reported.

REPORTED AS CANDIDATES. Static analysis cannot know whether a path exists at the moment the
line runs; naming a call that CAN raise is not the same as proving it will. The instance
above is the one confirmed by having happened.
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

# Calls that raise on a missing / existing / unreadable target.
RISKY = {
    "remove": "raises if the path is already gone",
    "unlink": "raises if the path is already gone",
    "rename": "raises if the target exists (Windows) or across devices",
    "move": "raises if the source is gone; copies then unlinks if the target exists",
    "copyfile": "raises if the source is gone",
    "copy": "raises if the source is gone",
    "copy2": "raises if the source is gone",
    "rmtree": "raises on a missing tree unless ignore_errors",
    "load": "raises on an empty or malformed file -- the zero-byte object case",
    "loads": "raises on an empty or malformed string",
    "replace": "raises if the source is gone",
    "getmtime": "raises if the path is gone",
    "getsize": "raises if the path is gone",
}

# THE TEST SOURCE, NOT THE STATEMENT. ast.get_source_segment(node.test) returns "not ok",
# WITHOUT the leading "if" -- so the first version of this pattern required a word that is
# never present in the string it is matched against, and the detector found NOTHING at all.
# Caught by its own positive control on the very first run, which is the whole argument for
# having one: a sweep that silently matches nothing is indistinguishable from a clean repo.
FAILURE_BRANCH = re.compile(
    r"\bnot\s+(ok|ran|built|success|valid|written|wrote)\b|\brollback\b|\brestore\b|"
    r"\bcleanup\b|\bon_error\b|\bfailed\b|\babort", re.I)


def guarded(call_node, src_lines):
    """Is this call defended -- ignore_errors, missing_ok, or its own try?"""
    ln = getattr(call_node, "lineno", 0)
    seg = " ".join(src_lines[max(0, ln - 2):ln + 1])
    return ("ignore_errors" in seg or "missing_ok" in seg
            or "os.path.exists" in seg or "try:" in seg)


def scan(path):
    src = io.open(path, encoding="utf-8", errors="replace").read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    lines = src.split("\n")
    hits = []

    class V(ast.NodeVisitor):
        def __init__(self):
            self.context = []

        def _walk_body(self, body, label):
            self.context.append(label)
            for st in body:
                self.visit(st)
            self.context.pop()

        def visit_Try(self, node):
            self._walk_body(node.body, label="try")
            for h in node.handlers:
                self._walk_body(h.body, label="except")
            self._walk_body(node.finalbody, label="finally")
            self._walk_body(node.orelse, label="else")

        def visit_If(self, node):
            test = ast.get_source_segment(src, node.test) or ""
            label = "failure-branch" if FAILURE_BRANCH.search(test) else "if"
            self._walk_body(node.body, label)
            self._walk_body(node.orelse, label="else")

        def visit_Call(self, node):
            name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
            if name in RISKY and any(c in ("except", "finally", "failure-branch")
                                     for c in self.context):
                ln = getattr(node, "lineno", 0)
                if not guarded(node, lines):
                    ctx = next(c for c in reversed(self.context)
                               if c in ("except", "finally", "failure-branch"))
                    hits.append((ln, ctx, name, RISKY[name],
                                 lines[ln - 1].strip()[:88] if ln else ""))
            self.generic_visit(node)

    V().visit(tree)
    return hits


def main():
    # CONSTRUCTED CONTROLS. The positive is the exact shape that killed the batch; the
    # negative is the same call with the existence check that makes it safe.
    import tempfile
    import shutil as _sh
    d = tempfile.mkdtemp(prefix="recov_ctl_")
    try:
        bad = os.path.join(d, "bad.py")
        good = os.path.join(d, "good.py")
        io.open(bad, "w", encoding="utf-8", newline=chr(10)).write(chr(10).join([
            "import shutil",
            "def f(ok, backup, page):",
            "    if not ok:",
            "        shutil.move(backup, page)",
        ]))
        io.open(good, "w", encoding="utf-8", newline=chr(10)).write(chr(10).join([
            "import os, shutil",
            "def f(ok, backup, page):",
            "    if not ok:",
            "        if os.path.exists(backup):",
            "            shutil.move(backup, page)",
        ]))
        require_controls(
            "audit_recovery_paths_can_raise",
            positive=("shutil.move in an unguarded failure branch -- the shape that killed "
                      "the batch", bool(scan(bad)), True),
            negative=("the same call behind an existence check", bool(scan(good)), True))
    finally:
        _sh.rmtree(d, ignore_errors=True)

    print("")
    found, unparsed = [], []
    for path in sorted(glob.glob(os.path.join(REPO, "ssot", "*.py"))
                       + glob.glob(os.path.join(REPO, "scripts", "*.py"))):
        rel = os.path.relpath(path, REPO).replace("\\", "/")
        if rel.endswith("audit_recovery_paths_can_raise.py"):
            continue
        hits = scan(path)
        if hits is None:
            unparsed.append(rel)
            continue
        for ln, ctx, name, why, snippet in hits:
            found.append((rel, ln, ctx, name, why, snippet))

    print("RECOVERY / CLEANUP STATEMENTS THAT CAN RAISE: %d" % len(found))
    print("UNPARSED (reported, not skipped): %d" % len(unparsed))
    print("")
    print("CANDIDATES. Static analysis cannot know whether the path exists when the line")
    print("runs. The confirmed instance is the one that already happened.")
    print("")
    for rel, ln, ctx, name, why, snippet in found:
        print("    %s:%d  [%s]  %s -- %s" % (rel, ln, ctx, name, why))
        print("        %s" % snippet)


if __name__ == "__main__":
    main()
