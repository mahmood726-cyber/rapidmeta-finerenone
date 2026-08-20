"""Every percentage in PAGE-STANDARD.md: does it name the instrument that produced it?

WHY. `10.9%` -- the projector's reproduction of ARNI -- was quoted for a week as evidence
that OBJECTS lack substance. Measured with the tokens resolved it is 26.2%, and part of the
gap was never about objects at all (class 72). A number in a standards document is quoted
BY people who did not derive it, which is exactly the number that needs to say where it
came from.

A percentage is PROVENANCED here if its own sentence names the artefact that produced it --
a script path, a commit hash, or a named delivered page. Not "measured 2026-08-20": a date
says when somebody looked, not what they ran, and a reader cannot re-run a date.

WARN, NOT BLOCK. Some of these are illustrative arithmetic inside an argument, where naming
an instrument would be noise. This says which are which so a human decides, and the count is
a reading list rather than a defect count.
"""
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls          # noqa: E402

DOC = os.path.join(REPO, "PAGE-STANDARD.md")
PCT = re.compile(r"\b\d[\d.]*\s?%")
# What counts as naming the thing that produced the number.
PROV = re.compile(r"`[\w/]+\.(?:py|R|json|html)`|scripts/[\w_]+\.py|ssot/[\w_]+\.py"
                  r"|\b[0-9a-f]{7,40}\b|[A-Z][A-Z0-9_]{3,}\.html", re.I)


def units(text, mode):
    """The span a reader has in front of them when they meet the number.

    TWO UNITS, AND THE CHOICE CHANGES THE ANSWER, SO BOTH ARE REPORTED. Splitting on table
    CELLS strands a percentage from an instrument named in the next cell of the same row --
    a reader reading that row can re-derive it, so counting it unprovenanced overstates.
    Splitting on ROWS is the reader's real unit in a table and the sentence is the reader's
    real unit in prose.

    A count that changes with an unstated unit is the denominator defect in another form,
    so the unit is named in the output beside every number.
    """
    if mode == "cell":
        parts = re.split(r"(?<=[.!?])\s+|\|", text)
    else:
        parts = []
        for line in text.split("\n"):
            parts.extend(re.split(r"(?<=[.!?])\s+", line) if "|" not in line else [line])
    return [p for p in parts if p.strip()]


def main():
    gate = "--gate" in sys.argv
    require_controls(
        "audit_standard_percentages_provenanced",
        positive=("a percentage whose sentence names a script is PROVENANCED",
                  bool(PROV.search("measured 41.5% by `scripts/foo.py`")), True),
        negative=("a percentage whose sentence names only a DATE is PROVENANCED",
                  bool(PROV.search("measured 41.5% on 2026-08-20")), True))

    if not os.path.exists(DOC):
        print("NOT_ASSESSABLE: %s is absent." % os.path.relpath(DOC, REPO))
        return 2
    text = io.open(DOC, encoding="utf-8").read()
    total = len(PCT.findall(text))
    print("")
    print("PERCENTAGES IN PAGE-STANDARD.md: %d" % total)

    results = {}
    for mode in ("cell", "row"):
        results[mode] = measure(text, mode, total)
    for mode in ("cell", "row"):
        p, b = results[mode]
        print("")
        print("UNIT = %s : provenanced %d of %d ; unprovenanced %d of %d"
              % (mode.upper(), len(p), total, len(b), total))
    bare = results["row"][1]
    prov = results["row"][0]
    print("")
    print("THE ROW UNIT IS THE REPORTED ONE -- it is what a reader has in front of them.")
    print("")
    print("UNPROVENANCED -- a reader cannot re-derive these from what they are reading:")
    for v, s in bare:
        print("   %-7s %s" % (v, s))
    return 0


def measure(text, mode, total):
    prov, bare = [], []
    seen = 0
    for s in units(text, mode):
        hits = PCT.findall(s)
        if not hits:
            continue
        seen += len(hits)
        target = prov if PROV.search(s) else bare
        for h in hits:
            target.append((h.strip(), " ".join(s.split())[:110]))

    # FLOOR. If the sentence splitter loses percentages, a small `bare` count would be a
    # clean answer over a narrowed population -- the defect this project keeps making.
    if seen != total:
        sys.exit("PROOF FAILED: the document contains %d percentage(s) and the splitter "
                 "accounted for %d. A reader that loses part of its own population cannot "
                 "report a shortfall." % (total, seen))

    return prov, bare


if __name__ == "__main__":
    sys.exit(main())
