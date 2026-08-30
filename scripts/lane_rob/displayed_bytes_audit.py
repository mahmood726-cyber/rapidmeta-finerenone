# -*- coding: utf-8 -*-
"""SWEEP: which checks read the bytes the reader sees, and which read something else.

⛔ THE CLASS, FOUND THE HARD WAY. currency_query asserted that a quotation contained the date it
was offered as evidence for. The assertion passed. The page still showed a quotation with no
date in it -- because the check ran on the sentence and the page rendered sentence[:300], with
the date at character 340.

⇒ A CHECK ON A VALUE THAT IS TRUNCATED, FORMATTED OR ROUNDED BEFORE DISPLAY IS A CHECK ON
SOMETHING THE READER NEVER SEES.

⚠️ And it happened on the THIRD attempt at a check written specifically to catch that defect.
Knowing the class does not defend against it, which is the argument for sweeping rather than
remembering.

WHAT THIS LOOKS FOR, structurally rather than by keyword: inside one function, a name that is
both (a) the subject of a check -- re.search/match/finditer, an `in` test, an assert -- and
(b) transformed on its way out, by a slice, a %-format, .format(), f-string or round().

⚠️ IT SURFACES CANDIDATES. Every flag is hand-read before it is counted; the fraction reported
to anyone is the hand-checked one. The absence-claim sweep earlier tonight reported 0 of 665 and
0 of 14 from a keyword rule that was wrong both times, and that is the standing reason this file
does not print a verdict of its own.
"""
import ast
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.dirname(os.path.dirname(HERE)))

CHECK_CALLS = {"search", "match", "finditer", "findall", "fullmatch", "startswith", "endswith"}
XFORM_CALLS = {"format", "round", "strftime", "join"}


class FuncScan(ast.NodeVisitor):
    def __init__(self):
        self.checked = set()
        self.transformed = set()

    # ---- (a) names that are the SUBJECT of a check
    def visit_Call(self, node):
        fn = node.func
        name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", None)
        if name in CHECK_CALLS:
            for a in node.args:
                self._names(a, self.checked)
            if isinstance(fn, ast.Attribute):
                self._names(fn.value, self.checked)
        if name in XFORM_CALLS:
            if isinstance(fn, ast.Attribute):
                self._names(fn.value, self.transformed)
            for a in node.args:
                self._names(a, self.transformed)
        self.generic_visit(node)

    def visit_Compare(self, node):
        for op in node.ops:
            if isinstance(op, (ast.In, ast.NotIn)):
                self._names(node.left, self.checked)
                for c in node.comparators:
                    self._names(c, self.checked)
        self.generic_visit(node)

    def visit_Assert(self, node):
        self._names(node.test, self.checked)
        self.generic_visit(node)

    # ---- (b) names TRANSFORMED on the way out
    def visit_Subscript(self, node):
        if isinstance(node.slice, ast.Slice):
            self._names(node.value, self.transformed)
        self.generic_visit(node)

    def visit_BinOp(self, node):
        if isinstance(node.op, ast.Mod):
            self._names(node.left, self.transformed)
            self._names(node.right, self.transformed)
        self.generic_visit(node)

    def visit_JoinedStr(self, node):
        for v in node.values:
            if isinstance(v, ast.FormattedValue):
                self._names(v.value, self.transformed)
        self.generic_visit(node)

    def _names(self, node, into):
        for n in ast.walk(node):
            if isinstance(n, ast.Name):
                into.add(n.id)
            elif isinstance(n, ast.Attribute):
                base = n
                while isinstance(base, ast.Attribute):
                    base = base.value
                if isinstance(base, ast.Name):
                    into.add(base.id)


def scan_file(path):
    try:
        tree = ast.parse(io.open(path, encoding="utf-8").read())
    except Exception as e:
        return [{"func": "<unparseable>", "why": "%s: %s" % (type(e).__name__, str(e)[:60])}]
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        s = FuncScan()
        for child in node.body:
            s.visit(child)
        both = sorted(s.checked & s.transformed)
        # `self`-ish and loop temporaries are noise; a one-letter name is almost never a payload
        both = [b for b in both if len(b) > 1 and b not in ("re", "os", "io", "sys", "json")]
        if both:
            out.append({"func": node.name, "line": node.lineno, "names": both})
    return out


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    targets = []
    for root in ("scripts/lane_rob", "ssot"):
        for dirpath, _d, names in os.walk(root):
            if "__pycache__" in dirpath:
                continue
            for n in names:
                if n.endswith(".py"):
                    targets.append(os.path.join(dirpath, n))
    targets.sort()
    rows = []
    for t in targets:
        for hit in scan_file(t):
            rows.append((t, hit))
    print("")
    print("DISPLAYED-BYTES SWEEP -- CANDIDATES, hand-read before counting")
    print("")
    print("  python files scanned                    %5d" % len(targets))
    print("  functions where a checked name is also  %5d" % len(rows))
    print("    transformed before output")
    print("")
    for t, h in rows:
        if "why" in h:
            print("  %-46s UNPARSEABLE %s" % (os.path.relpath(t), h["why"][:50]))
            continue
        print("  %-46s %s:%d" % (os.path.relpath(t), h["func"], h["line"]))
        print("        names: %s" % ", ".join(h["names"][:8]))
    print("")
    print("  ⚠️ A flag is not a defect. It says a name was checked and also sliced or formatted")
    print("     in the same function -- which is the SHAPE of the currency_query bug and is also")
    print("     what ordinary display code looks like. Read each before counting it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
