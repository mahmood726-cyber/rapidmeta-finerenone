"""A check whose expected value is TYPED rather than READ from the artefact.

THE INSTANCE. `ssot/boco_refit.R` printed a CHECK line asserting the object's stored values
were "MD -55.24 (-58.27 to -52.21), I^2 = 41.5" and reported that the heterogeneity did not
reproduce. NONE OF THOSE NUMBERS CAME FROM THE OBJECT. They were typed into the script, and
41.5 is the stored I-squared of a DIFFERENT TOPIC. **There was no discrepancy and one was
reported**, to a reader who relayed it onward and built three instructions on it.

    A CHECK LINE MUST READ ITS EXPECTED VALUES FROM THE ARTEFACT, NEVER ACCEPT TYPED ONES.

A typed expected value is not a check. It is two assertions -- the computed one and the
remembered one -- compared against each other, and when they disagree the script cannot say
which is wrong. It is the same class as an identifier written from recall and as a
fabricated provenance constant: A NUMBER IN SOURCE THAT CLAIMS TO DESCRIBE A FILE.

WHAT THIS FINDS. In `.py` and `.R` under `ssot/` and `scripts/`: a line that reports or
compares a "stored", "expected", "published" or "prior" value where that value is a NUMERIC
LITERAL rather than an expression reading the artefact. Reported as candidates -- a literal
in a CONSTRUCTED FIXTURE is correct and is exactly what class 58 requires, so the judgement
is made against a list.
"""
import io
import os
import re
import sys
import glob

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls

# NARROWED AFTER ITS FIRST RUN, WHICH MATCHED PROSE. The first pattern found any line
# with a claim word near a number, so it flagged docstring sentences -- "was 2.2%",
# "was Colombel Gut 2009" -- and reported them as typed expected values. A sweep that
# cannot tell a sentence from a check is measuring English, not code.
#
# The line must BE a check: it prints, asserts or compares. Prose does not.
IS_A_CHECK = re.compile(r"\bcat\(|\bprint\(|\bsprintf\(|\bassert\b|[=!]=|\bstopifnot\(")
# "stored: ... -55.24" / "expected 41.5" -- a claim about an artefact's contents carrying a
# bare decimal. Integers are excluded: a count in a check line is usually a length, and
# including them buried the signal.
CLAIM = re.compile(
    r"(?i)\b(stored|expected|published|prior|baseline|should\s+be)\b"
    r"[^\n]{0,40}?(-?\d+\.\d+)")
# A read: the line pulls from an object, a dict, a file or a parsed structure.
READS = re.compile(
    r"\.get\(|\[[\"'][\w.]+[\"']\]|json\.load|fromJSON|read\(|obj\b|blk\b|canon\b|"
    r"args_stored|%s|%\(|\{\}|format\(|sprintf\(.*%[sdf]")
FIXTURE = re.compile(r"(?i)fixture|control|graft|proof|self.?test|example|_bad|_good")


def scan(path):
    src = io.open(path, encoding="utf-8", errors="replace").read()
    hits = []
    for i, line in enumerate(src.split("\n")):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if not IS_A_CHECK.search(s):
            continue
        m = CLAIM.search(s)
        if not m:
            continue
        if READS.search(s):
            continue                     # the value comes from the artefact
        if FIXTURE.search(s):
            continue                     # a constructed fixture is meant to be literal
        hits.append((i + 1, s[:96]))
    return hits


def main():
    bad = 'cat(sprintf("  stored:  MD -55.24 (-58.27 to -52.21)   I^2 = 41.5\\n"))'
    good = ('cat(sprintf("  stored:  MD %s   I^2 = %s\\n", '
            'args_stored[["point"]], args_stored[["i2"]]))')
    tmp_bad = os.path.join(REPO, "outputs", "_evl_bad.R")
    tmp_good = os.path.join(REPO, "outputs", "_evl_good.R")
    os.makedirs(os.path.dirname(tmp_bad), exist_ok=True)
    io.open(tmp_bad, "w", encoding="utf-8", newline=chr(10)).write(bad + chr(10))
    io.open(tmp_good, "w", encoding="utf-8", newline=chr(10)).write(good + chr(10))
    try:
        require_controls(
            "lint_expected_value_is_a_literal",
            positive=("the boco_refit check line as it was written -- a typed stored value",
                      bool(scan(tmp_bad)), True),
            negative=("the same line reading its stored values from the object",
                      bool(scan(tmp_good)), True))
    finally:
        for p in (tmp_bad, tmp_good):
            if os.path.exists(p):
                os.remove(p)

    paths = sorted(glob.glob(os.path.join(REPO, "ssot", "*.py"))
                   + glob.glob(os.path.join(REPO, "ssot", "*.R"))
                   + glob.glob(os.path.join(REPO, "scripts", "*.py"))
                   + glob.glob(os.path.join(REPO, "scripts", "*.R")))
    total = 0
    print("")
    for p in paths:
        rel = os.path.relpath(p, REPO).replace("\\", "/")
        if rel.endswith("lint_expected_value_is_a_literal.py"):
            continue
        for ln, s in scan(p):
            total += 1
            print("    %s:%d" % (rel, ln))
            print("        %s" % s)
    print("")
    print("TYPED EXPECTED VALUES: %d candidate(s) across %d file(s)" % (total, len(paths)))
    print("")
    print("CANDIDATES, NOT DEFECTS. A literal inside a CONSTRUCTED FIXTURE is correct and is")
    print("what registry class 58 requires -- lines matching fixture, control, graft or")
    print("proof are excluded for that reason. What is a defect is a line that claims to")
    print("describe what an artefact CONTAINS while carrying a number nobody read from it.")


if __name__ == "__main__":
    main()
