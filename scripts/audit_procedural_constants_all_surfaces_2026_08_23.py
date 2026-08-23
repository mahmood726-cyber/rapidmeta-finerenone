"""Every surface that asserts a PROCEDURE from a literal rather than from a field.

# no-control: static classification of source. The control is asserted and is the same pair
# used by the Table 1 audit: `protocol_card` must come back carrying procedural constants, and
# a function known to project -- `extraction_provenance_table`, which builds one row per
# extracted value from the object -- must NOT. If either lands wrong the scan is not reading.

TABLE 1 WAS NOT COVERED BY `lint_method_claim_has_a_field`, WHICH GUARDS THE MANUSCRIPT. So the
question is not "is Table 1 fixed" but "what else was never covered". That is
`every_referring_surface` for the sixth time, and this instance PUBLISHES FALSE METHOD CLAIMS
rather than mis-rendering something.

WHAT COUNTS AS A FINDING HERE. A string literal that asserts a procedure was carried out --
screeners, adjudication, prespecification, GRADE domains, funnel/Egger/Peters, an estimator
choice -- inside a function that emits reader-facing markup, where the surrounding expression
does NOT read the object. A literal that names a tab, labels a column, or explains a method in
general terms is not a claim that the procedure was performed HERE.

THE DISTINCTION THAT MATTERS, AND IT IS THE ONE THE CORPUS ALREADY DEMONSTRATES: on delivered
MAVACAMTEN, `Risk of bias method` reads "Not recorded -- no per-domain RoB-2 assessment exists
yet" because it projects, while `Study selection process` asserts two independent screeners on
a page whose own text says no screening log is recorded. Same table, same page, one honest.
"""
from __future__ import annotations

import ast
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = [os.path.join(REPO, "ssot", "projectors.py"),
           os.path.join(REPO, "ssot", "projectors2.py"),
           os.path.join(REPO, "ssot", "build_tabbed.py")]
OUT = os.path.join(REPO, "outputs", "procedural_constants_2026_08_23.json")

OBJECT_NAMES = {"canon", "sc", "cfg", "obj", "res", "blk", "t", "trial", "o"}

# Assertions that a procedure WAS CARRIED OUT. Deliberately narrow: each phrase names an act.
PROCEDURAL = re.compile(
    r"(?i)("
    r"two independent screener|independent screeners|named human adjudication|"
    r"cross-family|title/abstract then full text|"
    r"pre-?specified before the search|all pre-?specified|were pre-?specified|"
    r"GRADE, all five domains|all five domains|"
    r"funnel, egger and peters|each reported as a computed value|"
    r"random effects on the log scale|REML headline|HKSJ reported alongside|"
    r"leave-one-out and an estimator comparison|"
    r"per-arm event counts, and the published effect"
    r")")

# Markup emission -- a literal only reaches a reader from a function that renders it.
#
# THE FIRST VERSION LOOKED ONLY AT THE FUNCTION'S OWN LITERALS AND MISSED `protocol_card`, the
# function this audit exists for: it returns `kv_card(...)`, so the markup lives in the CALLEE
# and the caller holds only the sentences. The hand-classified control caught it, which is what
# the control is for -- a scan that cannot see the known instance cannot report an absence.
EMITS = re.compile(r"<(?:div|table|tr|td|th|p|section|h[1-6]|li|span)\b")
# Functions that hand their content to a renderer rather than emitting tags themselves.
RENDER_CALLS = re.compile(r"\b(kv_card|fig|card|_card|section|rows_svg|add_table|s\.add)\s*\(")


def emits_markup(fn, body):
    if EMITS.search(body):
        return True
    seg = ast.dump(fn)
    return bool(RENDER_CALLS.search(seg)) or fn.name.endswith(
        ("_card", "_table", "_section", "_panel"))


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    findings = []
    per_func = {}
    for src in SOURCES:
        if not os.path.isfile(src):
            continue
        text = io.open(src, encoding="utf-8").read()
        tree = ast.parse(text)
        rel = os.path.relpath(src, REPO).replace("\\", "/")
        for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
            lits = [n for n in ast.walk(fn)
                    if isinstance(n, ast.Constant) and isinstance(n.value, str)]
            body = " ".join(n.value for n in lits)
            if not emits_markup(fn, body):
                continue                      # not a markup-emitting function
            hits = []
            for n in lits:
                m = PROCEDURAL.search(n.value)
                if m:
                    hits.append((n.lineno, re.sub(r"\s+", " ", n.value)[:110], m.group(1)))
            if hits:
                per_func[rel + "::" + fn.name] = len(hits)
                for line, snippet, phrase in hits:
                    findings.append({"file": rel, "function": fn.name, "line": line,
                                     "phrase": phrase, "text": snippet})

    # CONTROLS, AND THE POSITIVE IS A FIXTURE RATHER THAN THE LIVE SOURCE.
    #
    # It was keyed to `protocol_card` carrying procedural constants -- true when this scan was
    # written and FALSE the moment the seven rows were fixed. A control pointing at the defect
    # the work removes dies on success and then refuses forever. Third instance of that today,
    # after the field-name lint's control and the seam gate's.
    #
    # The fixture is the row as it stood before the fix, so the scan is proven against the
    # exact text it was built to find, permanently.
    fixture = (
        'def _fixture_card(canon, p):\n'
        '    return kv_card("t", [("Study selection process", "Two independent screeners of '
        'different model families, title/abstract then full text, with named human '
        'adjudication")])\n')
    ftree = ast.parse(fixture)
    ffn = ftree.body[0]
    flits = [n for n in ast.walk(ffn)
             if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    fbody = " ".join(n.value for n in flits)
    errs = []
    if not emits_markup(ffn, fbody):
        errs.append("the fixture card is not recognised as emitting markup -- it returns "
                    "kv_card(...), which is exactly how protocol_card was missed")
    if not any(PROCEDURAL.search(n.value) for n in flits):
        errs.append("the fixture's known procedural sentence is not detected")
    funcs = {k.split("::")[1] for k in per_func}
    if "extraction_provenance_table" in funcs:
        errs.append("extraction_provenance_table must NOT be flagged -- it builds one row per "
                    "extracted value from the object")
    if errs:
        sys.exit("REFUSED: the scan disagrees with a case established by hand:\n   "
                 + "\n   ".join(errs))

    print("")
    print("PROCEDURAL ASSERTIONS FROM LITERALS, across %d projector module(s)" % len(SOURCES))
    print("")
    print("   functions carrying at least one     %3d" % len(per_func))
    print("   total assertions                    %3d" % len(findings))
    print("")
    for k, v in sorted(per_func.items(), key=lambda kv: -kv[1]):
        print("   %-56s %3d" % (k[:56], v))
    print("")
    print("EVERY ONE, WITH THE PHRASE THAT MAKES IT A CLAIM:")
    for f in findings:
        print("   %s::%s:%d" % (f["file"].split("/")[-1], f["function"], f["line"]))
        print("        [%s]  %s" % (f["phrase"], f["text"][:92]))
    print("")
    print("A LITERAL THAT NAMES A TAB OR LABELS A COLUMN IS NOT A CLAIM THAT A PROCEDURE WAS")
    print("PERFORMED HERE. Each of the above says an act was carried out, on every page that")
    print("renders it, whatever the object holds.")
    json.dump({"findings": findings, "per_function": per_func},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    print("")
    print("written: %s" % os.path.relpath(OUT, REPO))


if __name__ == "__main__":
    main()
