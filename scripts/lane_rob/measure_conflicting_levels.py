# -*- coding: utf-8 -*-
"""Every surface that states a certainty level, and where they disagree.

WHY THIS IS A RE-MEASUREMENT. An earlier pass reported ZERO conflicting levels against
"23 of 33 present-versus-absent". That pass compared TWO surfaces -- the Summary of Findings
against the certainty column -- and was silent on every other. The surface that was actually
lying was the visual abstract's FIGURE TEXT, which is where a different level was printing.
Reach reported as coverage, inside a verification step.

CONSUMERS ENUMERATED BY SEARCHING FOR READS OF THE FIELD, NOT BY RECALLING WHERE IT APPEARS.
`grep -rn certainty ssot/*.py` filtered to actual reads turns up ten, of which these render:

  1 GRADE card            projectors2.grade_section          "Certainty: X"
  2 figure text           projectors.visual_abstract_svg     "GRADE certainty: X."
  3 draft bullet          build_tabbed li("Certainty", ...)  "GRADE certainty: X."
  4 insertable chip       build_tabbed snips                 "GRADE certainty: X"
  5 certainty table       paper_projector add_table          a Certainty column cell
  6 Summary of Findings   build_tabbed                       a Certainty column cell
  7 abstract results lead paper_projector _live_certainty    "certainty of the evidence was X"
  8 abstract outcome list paper_projector                    "carry a rating: ... X"
  9 docx                  make_docx                          "Overall certainty: X"
 10 authored F1000 prose  add_f1000_fields                   "[[certainty]]" token

Of those, 1, 5, 6, 8 route through grade_authority.resolve(); 2 did not until today; 3, 4 use
the resolved cell; 7 reads `grade.by_outcome[*].certainty` RAW; 9 is not a web page; 10 is
authored text on ARNI carrying a substitution token.

WHAT COUNTS AS A CONFLICT. Not "a level appears twice". Two distinct LEVELS on one page for
one outcome, or a level on one surface while another withholds it. Both are a reader meeting
two different answers to the same question on the same page.

READ-ONLY.
"""
import collections
import glob
import html
import io
import json
import os
import re
import sys

# GUARDED. A module-level stdout reassignment closes the CALLER's stdout the moment
# this file is imported, and every script here is now importable -- three separate
# checks of this lane's own output died that way before it was fixed at the source.
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace", line_buffering=True)
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
os.chdir(REPO)

LV = r"(very low|low|moderate|high)"
SURFACES = [
    ("GRADE card", re.compile(r"(?<!GRADE )Certainty:\s*" + LV + r"\b", re.I)),
    ("figure text / draft bullet / chip", re.compile(r"GRADE certainty:\s*" + LV + r"\b", re.I)),
    ("abstract results lead", re.compile(r"certainty of the evidence was\s*" + LV + r"\b", re.I)),
    ("abstract outcome list", re.compile(r"carry a rating[^.]{0,400}?\b" + LV.upper() + r"\b")),
    ("overall certainty line", re.compile(r"Overall certainty:\s*" + LV + r"\b", re.I)),
    ("derivation string", re.compile(r"total\s*-?\d+\s*->\s*" + LV + r"\b", re.I)),
]
WITHHELD = re.compile(r"Certainty:\s*Pending|PENDING, not rated|not rated\b", re.I)


def rendered(raw):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))


rows = []
for page in sorted(glob.glob("*.html")):
    try:
        raw = open(page, "rb").read().decode("utf-8", "replace")
    except OSError:
        continue
    t = rendered(raw)
    found = {}
    for name, pat in SURFACES:
        hits = {m.group(1).lower() for m in pat.finditer(t)}
        if hits:
            found[name] = sorted(hits)
    withheld = bool(WITHHELD.search(t))
    if not found and not withheld:
        continue
    levels = sorted({v for vs in found.values() for v in vs})
    rows.append({"page": page, "surfaces": found, "levels": levels,
                 "withheld_somewhere": withheld,
                 "conflict_distinct_levels": len(levels) > 1,
                 "conflict_level_vs_withheld": bool(found) and withheld})

print("=" * 94)
print("CONFLICTING CERTAINTY LEVELS, ACROSS EVERY RENDERING SURFACE")
print("=" * 94)
print("  pages stating or withholding a certainty       %4d  == the denominator" % len(rows))
print("  pages stating a level on >=1 surface           %4d"
      % sum(1 for r in rows if r["surfaces"]))
print("")
d = [r for r in rows if r["conflict_distinct_levels"]]
w = [r for r in rows if r["conflict_level_vs_withheld"]]
print("  TWO OR MORE DISTINCT LEVELS on one page        %4d" % len(d))
print("  A LEVEL ON ONE SURFACE, WITHHELD ON ANOTHER    %4d" % len(w))
print("")
print("  surfaces actually observed carrying a level, and on how many pages:")
c = collections.Counter(s for r in rows for s in r["surfaces"])
for k, v in c.most_common():
    print("     %-40s %4d" % (k, v))
print("")
if d:
    print("  PAGES SHOWING TWO OR MORE DISTINCT LEVELS:")
    for r in d[:20]:
        print("     %-40s %s" % (r["page"][:40], ", ".join(r["levels"])))
        for s, vs in r["surfaces"].items():
            print("         %-38s %s" % (s, ", ".join(vs)))
if w:
    print("")
    print("  PAGES WITH A LEVEL ON ONE SURFACE AND WITHHELD ON ANOTHER:")
    for r in w[:20]:
        print("     %-40s levels %s" % (r["page"][:40], ", ".join(r["levels"])))
        for s, vs in r["surfaces"].items():
            print("         %-38s %s" % (s, ", ".join(vs)))
json.dump(rows, io.open(r"F:\claude-temp\pend\conflict_levels.json", "w",
                        encoding="utf-8"), indent=1)
print("")
print("  detail -> conflict_levels.json")
