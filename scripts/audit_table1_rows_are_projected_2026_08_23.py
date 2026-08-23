"""Which Table 1 rows are PROJECTIONS and which are hardcoded constants. Enumerated by AST.

# no-control: a static classification of source, so the known answer is the source itself. The
# control that matters IS asserted: `Risk of bias method` must come back PROJECTED and `Study
# selection process` must come back CONSTANT -- both established by a person reading delivered
# MAVACAMTEN, where the first degrades honestly and the second asserts a procedure the same
# page refuses by name. If either lands wrong, this classifier is not reading what it claims.

THE FINDING THIS ANSWERS, AND IT IS THE INHERITANCE TRAP THIS PROJECT PREDICTED. Every page
carries a Table 1 on the Protocol tab whose procedural rows have NO SOURCE SUPERSCRIPT. On
MAVACAMTEN, rows assert procedures THE SAME PAGE REFUSES BY NAME:

    Table 1 says                                    the same page says
    "Two independent screeners of different model   "No screening log is recorded for this
     families ... with named human adjudication"     review"
    "all pre-specified before the search"           "Refused: the claim that the review
                                                     methods were prespecified"
    "GRADE, all five domains"                       "Refused: the certainty assessment -- no
                                                     GRADE record is held"

The identical strings appear on MALARIA_ACT and TIGECYCLINE_INFECTION. THE MECHANISM IS
CONFIRMED: ARNI holds the timestamps (protocol committed 11:27:47Z, first query attempted
12:19:18Z) and the named adjudication (2026-08-13T13:55:30Z) that make those sentences TRUE OF
ARNI. They were copied to every page as constants.

AND ONE ROW PROVES THE FIX IS AVAILABLE. `Risk of bias method` IS projected and degrades
honestly to "Not recorded -- no per-domain RoB-2 assessment exists yet". One projected, the
rest asserted, in the same table.

WHY AN AST AND NOT A READING. Seven rows were reported by a lane that read ONE page. That is
the known positive, not the population. A row is a PROJECTION when its value expression reads
the object -- `canon`, `sc`, `cfg`, or the escaper `p` -- and a CONSTANT when it is a literal,
whatever it says about procedure. The distinction is syntactic and is therefore not a matter of
anyone's opinion about how procedural a sentence sounds.
"""
from __future__ import annotations

import ast
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "ssot", "projectors2.py")
OUT = os.path.join(REPO, "outputs", "table1_row_classification_2026_08_23.json")

OBJECT_NAMES = {"canon", "sc", "cfg", "p", "obj", "res"}
# Words that make a literal an assertion ABOUT PROCEDURE rather than a label or a link.
PROCEDURAL = re.compile(
    r"(?i)\b(screener|screeners|adjudicat|pre-?specified|prespecified|GRADE|"
    r"independent|extracted|extraction items|funnel|egger|peters|random effects|"
    r"REML|HKSJ|leave-one-out|domains|title/abstract|full text)\b")


def value_reads_object(node):
    for n in ast.walk(node):
        if isinstance(n, ast.Name) and n.id in OBJECT_NAMES:
            return True
    return False


def literals_of(node):
    return " ".join(n.value for n in ast.walk(node)
                    if isinstance(n, ast.Constant) and isinstance(n.value, str))


def rows_of(func):
    for node in ast.walk(func):
        if not isinstance(node, ast.Assign):
            continue
        if not (len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "pairs"):
            continue
        for elt in node.value.elts:
            if isinstance(elt, ast.Tuple) and len(elt.elts) == 2:
                label = elt.elts[0]
                lab = label.value if isinstance(label, ast.Constant) else "<expr>"
                yield lab, elt.elts[1]


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    tree = ast.parse(io.open(SRC, encoding="utf-8").read())
    func = next((n for n in ast.walk(tree)
                 if isinstance(n, ast.FunctionDef) and n.name == "protocol_card"), None)
    if func is None:
        sys.exit("REFUSED: protocol_card not found in %s" % SRC)

    rows = []
    for lab, val in rows_of(func):
        projected = value_reads_object(val)
        text = literals_of(val)
        procedural = bool(PROCEDURAL.search(text))
        rows.append({"row": lab, "projected": projected,
                     "asserts_procedure": procedural,
                     "text": re.sub(r"\s+", " ", text)[:150]})

    # THE CONTROLS. POSITIVE from the live source, NEGATIVE from a fixture.
    #
    # The negative was `Study selection process` must classify CONSTANT -- true when this was
    # written and FALSE once the row was fixed to project. A control pointing at the defect the
    # work removes dies on success and then refuses forever; that is the fourth instance today.
    # So the negative is a fixture holding a constant row, which will classify CONSTANT
    # permanently, and the positive stays on the live source where a REGRESSION would show.
    by = {r["row"]: r for r in rows}
    errs = []
    if not by.get("Risk of bias method", {}).get("projected"):
        errs.append("`Risk of bias method` must classify PROJECTED -- it degrades honestly on "
                    "delivered MAVACAMTEN to 'Not recorded -- no per-domain RoB-2 assessment "
                    "exists yet'")
    fixture = ast.parse(
        'def f(canon, p):\n'
        '    pairs = [("Constant row", "Two independent screeners of different model '
        'families"), ("Projected row", p(canon["title"]))]\n')
    fx = {lab: value_reads_object(v)
          for lab, v in rows_of(fixture.body[0])}
    if fx.get("Constant row") is not False:
        errs.append("a fixture row whose value is a bare literal must classify CONSTANT")
    if fx.get("Projected row") is not True:
        errs.append("a fixture row reading `canon` must classify PROJECTED")
    if errs:
        sys.exit("REFUSED: the classifier disagrees with a case established by hand:\n   "
                 + "\n   ".join(errs))

    proj = [r for r in rows if r["projected"]]
    const = [r for r in rows if not r["projected"]]
    danger = [r for r in const if r["asserts_procedure"]]

    print("")
    print("TABLE 1 (protocol_card), %d rows" % len(rows))
    print("")
    print("   PROJECTED from the object          %3d" % len(proj))
    print("   CONSTANT                           %3d" % len(const))
    print("   CONSTANT *and* asserts a procedure %3d   <- these can be false on any page"
          % len(danger))
    print("")
    print("   %-32s %-10s %s" % ("row", "source", "asserts a procedure?"))
    for r in rows:
        print("   %-32s %-10s %s" % (r["row"][:32],
                                     "projected" if r["projected"] else "CONSTANT",
                                     "YES" if r["asserts_procedure"] else "-"))
    print("")
    print("THE ROWS THAT CAN BE FALSE, WITH WHAT THEY ASSERT:")
    for r in danger:
        print("   %-32s %s" % (r["row"][:32], r["text"][:96]))
    print("")
    print("A ROW IS A PROJECTION WHEN ITS VALUE READS THE OBJECT AND A CONSTANT WHEN IT IS A")
    print("LITERAL, whatever it says about procedure. That is syntactic, so it is not a matter")
    print("of anyone's opinion about how procedural a sentence sounds.")
    json.dump({"rows": rows, "projected": len(proj), "constant": len(const),
               "constant_procedural": len(danger)},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    print("")
    print("written: %s" % os.path.relpath(OUT, REPO))


if __name__ == "__main__":
    main()
