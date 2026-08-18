"""Per page, per tab: held with content / renders "Not held" / tab absent entirely.

WHY THIS EXISTS, AND IT IS A CORRECTION TO THE MEASURE ITSELF. `content_gate` asserts that
a pooled estimate's values appear in the served bytes; `verdict_gate` asserts the object's
own verdict text does. BOTH INSPECT ONE SLOT. Neither says anything about the other seven.

So "115 of 116, gated live" is true and means THE HEADLINE SLOT IS RIGHT ON 115 PAGES. It
does not mean 115 topics a reader can open and find populated -- which is exactly the
distinction delivery-is-not-audit was written to stop us losing, lost again one level up,
on the night we re-measured.

Mahmood opened sglt2-hf -- the flagship -- and found Paper Studio and Statistics both
reading "Not held in this object."

THE EMPTY TAB IS NOT THE FAILURE. The absent-state text says: a manuscript belongs to one
review, and none from another review is shown here -- this tab is empty of content rather
than filled with someone else's. THAT IS THE ARCHITECTURE WORKING AS DESIGNED. It refuses
instead of borrowing. THE FAILURE IS THAT OUR DELIVERY COUNTER NEVER ASKED.

Three states, from the markup the builder actually emits:
  HELD      the panel exists and carries content
  NOT HELD  the panel exists and carries an absent-state note -- an honest refusal
  ABSENT    no panel at all, which is the only one of the three that is silent

MEASURE ONLY. No manuscript is generated to fill a tab; restoring tabs needs Mahmood, and
conjuring content to satisfy a counter is the overreach direction.
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
TABS = [("protocol", "1 Protocol"), ("search", "2 Search"), ("screen", "3 Screening"),
        ("extract", "4 Extraction"), ("analysis", "5 Analysis"),
        ("report", "6 SciOutput"), ("paper", "7 Paper"), ("statistics", "8 Stats")]
PANEL = re.compile(r'<section class="panel" id="pn-([a-z]+)"', re.I)
HELD, NOTHELD, ABSENT = "H", "-", " "


ALT_PANEL = re.compile(r'class="tab-panel', re.I)


def states_for(html: str):
    """Segment the page into panels and classify each.

    RETURNS None WHEN THE MARKUP IS A DIFFERENT GENERATION, and that distinction was
    forced by the census getting it wrong on its first run. SOTATERCEPT_PAH_AUTO_2
    was reported as 0 of 8 tabs held. It holds SEVEN, in  markup
    from an older builder that this regex cannot see.

    A CENSUS THAT CANNOT READ A PAGE MUST SAY SO RATHER THAN SCORE IT ZERO -- reporting
    'no tabs' for 'markup I do not recognise' is the same error this whole week has been
    about, committed by the instrument built to measure it.
    """
    marks = [(m.group(1), m.start()) for m in PANEL.finditer(html)]
    if not marks:
        return "ALT" if ALT_PANEL.search(html) else None
    out = {}
    for i, (tid, start) in enumerate(marks):
        end = marks[i + 1][1] if i + 1 < len(marks) else len(html)
        seg = html[start:end]
        out[tid] = NOTHELD if 'class="absent-state"' in seg else HELD
    return out


def main() -> int:
    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"),
                           encoding="utf-8"))
    rows, missing, unreadable = [], [], []
    for page in sorted(pm):
        p = os.path.join(REPO, page)
        if not os.path.exists(p):
            missing.append(page)
            continue
        html = io.open(p, encoding="utf-8", errors="replace").read()
        st = states_for(html)
        if st == "ALT" or st is None:
            unreadable.append((page, "older tab-panel markup" if st == "ALT"
                               else "no recognised tab markup"))
            continue
        rows.append((page, [st.get(t, ABSENT) for t, _ in TABS]))

    print("=" * 100)
    print("TAB-OCCUPANCY CENSUS -- %d pages x %d tabs" % (len(rows), len(TABS)))
    print("H = held with content   - = renders 'Not held' (an honest refusal)   "
          "blank = tab absent")
    print("=" * 100)
    print("%-46s %s" % ("PAGE", " ".join("%-4s" % lbl.split()[0] for _, lbl in TABS)))
    print("%-46s %s" % ("", " ".join("%-4s" % lbl.split()[1][:4] for _, lbl in TABS)))
    print("-" * 100)
    for page, st in rows:
        print("%-46s %s" % (page[:45], "  ".join("%-2s" % s for s in st)))

    print()
    print("=" * 100)
    print("PER-TAB TOTALS across %d pages" % len(rows))
    print("%-16s %8s %10s %8s" % ("TAB", "HELD", "NOT HELD", "ABSENT"))
    print("-" * 46)
    tot = {}
    for i, (tid, lbl) in enumerate(TABS):
        h = sum(1 for _, st in rows if st[i] == HELD)
        n = sum(1 for _, st in rows if st[i] == NOTHELD)
        a = len(rows) - h - n
        tot[tid] = (h, n, a)
        print("%-16s %8d %10d %8d" % (lbl, h, n, a))

    print()
    full = sum(1 for _, st in rows if all(s == HELD for s in st))
    print("pages with ALL EIGHT tabs held : %d of %d" % (full, len(rows)))
    hist = {}
    for _, st in rows:
        hist[sum(1 for s in st if s == HELD)] = hist.get(
            sum(1 for s in st if s == HELD), 0) + 1
    print("distribution of tabs-held per page:")
    for k in sorted(hist, reverse=True):
        print("   %d/8 tabs held : %3d pages" % (k, hist[k]))
    if unreadable:
        print()
        print("NOT MEASURABLE BY THIS CENSUS: %d -- a DIFFERENT BUILDER GENERATION,"
              % len(unreadable))
        print("not an empty page. Scored zero on the first run until the page was read.")
        for u, why in unreadable:
            print("   %-46s %s" % (u[:45], why))
    if missing:
        print()
        print("PAGE_MAP entries with no file on disk: %d" % len(missing))
        for m in missing:
            print("   %s" % m)
    print()
    print("=" * 100)
    print("THE DELIVERY NUMBER IS A VECTOR, NOT A SCALAR. One number for eight slots is")
    print("what let this hide: a gated headline says the headline slot is right, and")
    print("says nothing whatever about the other seven.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
