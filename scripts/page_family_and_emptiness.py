"""Classify every page by FAMILY first, then by whether it is an empty template.

WHY FAMILY FIRST. A first attempt counted decimal values in static markup and reported
936 of 944 pages empty -- 99.2%. IT WAS NOT REPORTED, because two flagged pages had
completely different shapes and the heuristic binned them identically. Checking them showed
why: they are DIFFERENT PAGE FAMILIES, not the same family in different states.

  V2 SHELL   `<tbody id="...">` slots, literal `>--<` value cells, and the marker
             "No searches recorded yet. Run an acquisition from the Search tab".
             GEPOTIDACIN_URINARY_TRACT_AUTO_FULL_REVIEW.html -- LIVE-VERIFIED EMPTY on
             2026-08-18 by rendering, not by regex.
  V1 SHELL   none of those; carries `id="extract-pooled-result"`.
             ABLATION_AF_REVIEW.html -- the NEGATIVE CONTROL.

FOUNDING FIXTURES, and they are live-verified rather than assumed: GEPOTIDACIN and
CEFTAROLINE were both fetched from the published site and both render `--` in every value
field. ABLATION_AF_REVIEW is the negative control for the other family.

WHAT "EMPTY" MEANS HERE, stated because the word did the damage last time: a V2-shell page
is empty when its value cells hold the literal placeholder and its table bodies hold no
rows. THAT IS A STATEMENT ABOUT THE SHELL, NOT ABOUT WHETHER A READER SEES NUMBERS -- a
page could in principle be filled by JavaScript at load. The two live checks are what rule
that out for the V2 family, and they cover two pages, not the family.

THIS IS A TRIAGE. A V1 page reporting "not empty" has NOT been shown to contain correct
values, or any values -- only that it does not carry the V2 empty markers.
"""
from __future__ import annotations
import io
import json
import os
import re
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NO_SEARCH = re.compile(r"No searches recorded yet")
PLACEHOLDER = re.compile(r">\s*--\s*<")
TBODY_SLOT = re.compile(rb"<tbody[^>]*id=\"([^\"]+)\"")
V1_MARK = re.compile(r'id="extract-pooled-result"')
ROW_IN = re.compile(r"<tr[\s>]")
# a single colspan row saying "No ..." is how the V2 shell RENDERS EMPTINESS
EMPTY_STATE_ROW = re.compile(r"colspan=\"\d+\"[^>]*>\s*No\s", re.I)


def classify(html: str):
    v2 = bool(NO_SEARCH.search(html)) or len(PLACEHOLDER.findall(html)) >= 10
    v1 = bool(V1_MARK.search(html))
    if v2:
        fam = "V2_SHELL"
    elif v1:
        fam = "V1_SHELL"
    else:
        fam = "OTHER"
    ph = len(PLACEHOLDER.findall(html))
    slots = TBODY_SLOT.findall(html.encode("utf-8", "replace"))
    # rows inside the named tbody slots -- a filled V2 page would carry them
    # COUNT ONLY DATA ROWS. The V2 shell fills an empty table with a single
    # colspan row reading "No data ..." -- that is an EMPTINESS MARKER, and the
    # first version counted it as content, which made the detector disagree with
    # two live-verified empty fixtures. The fixture gate caught it.
    rows = 0
    for m in re.finditer(r"<tbody[^>]*id=\"[^\"]+\"[^>]*>(.*?)</tbody>", html, re.S):
        for tr in re.finditer(r"<tr[\s>].*?</tr>", m.group(1), re.S):
            if EMPTY_STATE_ROW.search(tr.group(0)):
                continue
            rows += 1
    empty = None
    if fam == "V2_SHELL":
        empty = (ph >= 10 and rows == 0)
    return fam, {"placeholder_cells": ph, "tbody_slots": len(slots),
                 "rows_in_slots": rows, "empty": empty}


def main() -> int:
    pm = set(json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"),
                               encoding="utf-8")))
    fams, empties, mapped_empty = {}, [], 0
    pages = [f for f in sorted(os.listdir(REPO))
             if f.endswith(".html") and os.path.getsize(os.path.join(REPO, f)) > 10000]
    for p in pages:
        html = io.open(os.path.join(REPO, p), encoding="utf-8", errors="replace").read()
        fam, d = classify(html)
        fams[fam] = fams.get(fam, 0) + 1
        if d["empty"]:
            empties.append(p)
            if p in pm:
                mapped_empty += 1

    print("pages over 10KB: %d" % len(pages))
    print()
    print("=== FAMILY")
    for k, v in sorted(fams.items(), key=lambda x: -x[1]):
        print("    %-12s %4d" % (k, v))
    print()
    print("=== EMPTY, within V2_SHELL only")
    print("    V2 pages:            %d" % fams.get("V2_SHELL", 0))
    print("    of those, EMPTY:     %d" % len(empties))
    print("    empty AND mapped to an object: %d" % mapped_empty)
    print()
    print("    EMPTINESS IS NOT ASSESSED FOR V1_SHELL OR OTHER. Those families carry")
    print("    neither the placeholder cells nor the slot tables this detects, so the")
    print("    question is not answered for them and is NOT a pass.")
    print()
    # fixture check -- the detector must agree with what was verified live
    fx = [("GEPOTIDACIN_URINARY_TRACT_AUTO_FULL_REVIEW.html", "V2_SHELL", True),
          ("CEFTAROLINE_AUTO_FULL_REVIEW.html", "V2_SHELL", True),
          ("ABLATION_AF_REVIEW.html", "V1_SHELL", None)]
    print("=== FIXTURES (two live-verified empty, one negative control)")
    ok = True
    for name, want_fam, want_empty in fx:
        fp = os.path.join(REPO, name)
        if not os.path.exists(fp):
            print("    MISSING %s" % name)
            ok = False
            continue
        fam, d = classify(io.open(fp, encoding="utf-8", errors="replace").read())
        good = (fam == want_fam and d["empty"] is want_empty)
        ok &= good
        print("    %-48s %-9s empty=%-5s %s"
              % (name[:47], fam, d["empty"], "ok" if good else "MISMATCH"))
    json.dump(empties, io.open(os.path.join(REPO, ".empty-v2-pages.json"), "w",
                               encoding="utf-8"), indent=1)
    print()
    print("detector agrees with the live-verified fixtures." if ok else
          "DETECTOR DISAGREES WITH A FIXTURE -- do not use its numbers.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
