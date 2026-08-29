# no-control: this gate reads PYTHON SOURCE, not document prose. It decides by the AST rather
# than by matching text, so a known-negative control over prose would have nothing to be a
# control over. Stated rather than silently exempted.
r"""GATE 15 -- a regex escape inside a NON-RAW string literal.

WHY. Four backspace-escape bugs were found in check code on 2026-08-29 and THREE had made a
live check inert: it ran, matched nothing, and exited 0. That is the worst failure shape there
is, because the instrument reports GOOD NEWS, and nothing downstream ever re-tests a clean
sweep.

In a plain Python string the two characters backslash-b are U+0008 BACKSPACE, not a word
boundary. A pattern built from such a literal cannot match what its author meant, and it fails
SILENTLY.

THE BOUNDARY IS STRUCTURAL. This decides on the AST: a literal is raw or it is not, and the
parser knows which. No text to match, no threshold to tune.

THIS FILE IS ITS OWN HARDEST CASE, and that is recorded rather than hidden. Its first version
flagged its own token table -- the self-referential failure the standing orders warn about. A
second version fixed the bytes and thereby made its own probe inert, and the harness caught
THAT by refusing to report a named positive it had not reached. Both are the reason every
token below is either a raw literal or is built from chr(92): the class definition must not be
an instance of the class.
"""
from __future__ import annotations

import ast
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402

BS = chr(92)                       # a backslash, written so no escape can eat it

# DECLARED EXCLUSION, structural rather than a cut: these are the CLASS DEFINITION. Writing
# them RAW makes that true in the language, so they are excluded by the same raw-prefix rule
# that applies to every other file, with no special case for this one.
REGEXY = (r"\b", r"\d", r"\s", r"\w", r"\B", r"\D", r"\S", r"\W", r"\A", r"\Z")


def offending_literals(src, filename):
    """Every NON-RAW string literal whose SOURCE TEXT carries a regex escape.

    Reading the source segment rather than the parsed value is the whole point: by the time
    the value exists the escape has already become a control character and the evidence is
    gone.
    """
    out = []
    tree = ast.parse(src, filename)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        seg = ast.get_source_segment(src, node)
        if seg is None:
            continue
        prefix = seg[:2].lower()
        if prefix.startswith("r") or prefix.startswith("rb") or prefix.startswith("br"):
            continue
        for tok in REGEXY:
            if tok in seg:
                out.append((node.lineno, tok, seg.strip()[:110]))
                break
    return out


def main(argv):
    gate = H.Gate("15 REGEX ESCAPE IN A NON-RAW STRING",
                  "a check built from " + BS + "b in a plain string matches nothing, exits 0",
                  needs_coverage=True)
    repo = H.repo_root()
    gdir = os.path.join(repo, "gates")
    files = sorted(f for f in os.listdir(gdir) if f.endswith(".py"))

    # NAMED POSITIVE. Keyed to a fact established OUTSIDE this gate: the interpreter decides
    # that the two characters backslash-b in a plain literal are chr(8). If that assertion
    # ever fails, the premise of the whole gate is gone and it must not report a clean run.
    if (BS + "b").encode().decode("unicode_escape") != chr(8):
        gate.broken("the premise failed: backslash-b in a plain literal is not chr(8) here")
    gate.expect_case("synthetic", "a constructed non-raw literal carrying " + BS + "b")
    probe = ('x = "' + BS + 'bword"' + chr(10) +
             'y = r"' + BS + 'bword"' + chr(10))
    found = offending_literals(probe, "<probe>")
    if len(found) == 1 and found[0][1] == r"\b":
        gate.saw("synthetic")
    else:
        gate.broken("the AST walk did not see a constructed backslash-b literal, or wrongly "
                    "saw the raw one too: %r" % (found,))

    parsed = 0
    for f in files:
        p = os.path.join(gdir, f)
        try:
            src = io.open(p, encoding="utf-8").read()
            rows = offending_literals(src, f)
        except SyntaxError as exc:
            gate.broken("%s did not parse (%s)" % (f, exc))
            continue
        parsed += 1
        for lineno, tok, seg in rows:
            gate.finding("INERT-REGEX-ESCAPE-IN-PLAIN-STRING",
                         "gates/%s:%d carries %r in a NON-RAW literal: %s"
                         % (f, lineno, tok, seg), numerator=1, denominator=len(files))

    gate.kinds({"python files in gates/": len(files),
                "  parsed": parsed,
                "  unparseable (reported BROKEN, never skipped)": len(files) - parsed})
    gate.coverage(parsed, len(files), "python files in gates/",
                  blind_to=("any file that did not parse, and every check module OUTSIDE "
                            "gates/ -- scripts/ and the generator are not read here, so a "
                            "zero here says nothing about them."))
    return gate.report(denominator="%d files" % len(files))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
