# -*- coding: utf-8 -*-
"""Measure BUILT pages against the declared tab list in ssot/page_format_v1.json.

⭐ THE POINT IS THE DENOMINATOR. On 2026-08-30 two lanes measured the same page and
reported "6 of 8" and "6 of 10". Neither had the page wrong; they were counting different
REQUIRED lists, because the required list existed only in messages. This reads the list from
a file and reports `present / declared`, so the ratio carries its own denominator.

⛔ MEASURED FROM THE BUILT BYTES. Panel ids and nav labels are read out of the shipped HTML,
never from the generator -- a generator states what was meant, and the whole class of defect
this repo keeps finding is the gap between that and what shipped.

⚠️ EXTRA TABS ARE REPORTED, NEVER NETTED. A page carrying a tab the standard does not name is
interesting and is not credit; adding it to the numerator would let a page satisfy the format
by carrying the wrong things.

Read-only. Usage:  python scripts/check_page_format.py [PAGE.html ...]
With no arguments it walks every page in ssot/PAGE_MAP.json.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))

PANEL_RE = re.compile(r'<section[^>]*id="([^"]+)"')
NAVLABEL_RE = re.compile(r">\s*(?:\d+\.\s*)?([A-Za-z][A-Za-z /&-]{2,40}?)\s*<")


def load_format():
    p = os.path.join(_ROOT, "ssot", "page_format_v1.json")
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def panels_of(html):
    """Panel ids actually present in the shipped bytes."""
    return [i for i in PANEL_RE.findall(html) if i.startswith("pn-")]


def navlabels_of(html):
    m = re.search(r'class="tabnav"[^>]*>(.{0,4000})', html, re.S)
    if not m:
        return []
    return [t.strip() for t in NAVLABEL_RE.findall(m.group(1)) if t.strip()]


TOMBSTONE_RE = re.compile(r"has been retired|Retired review|retired, answered at", re.I)


def is_tombstone(html):
    """A retired-review tombstone is a THIRD KIND OF PAGE -- not a review, not a defect.

    ⛔ SCORING ONE AGAINST THE REVIEW FORMAT IS A CATEGORY ERROR. The first run of this
    checker reported 14 pages at 0/8 required tabs, which reads as 14 broken pages. They are
    deliberate tombstones (~2.8 KB) that exist so a link to a retired review does not break,
    and they say so in their own text: "It is not a redirect: a reader who arrives here is
    told what happened rather than moved silently."

    Counting them as review pages would have put 14 fabricated failures into a corpus
    number. Before reporting any count, the KINDS of item in the population have to be
    enumerated -- reviews, tombstones, and whatever else -- not just the number.
    """
    return bool(TOMBSTONE_RE.search(html)) and len(html) < 20000


def check(path, fmt):
    with open(path, encoding="utf-8", errors="replace") as fh:
        html = fh.read()
    if is_tombstone(html):
        return None
    panels = set(panels_of(html))
    labels = navlabels_of(html)
    low = " | ".join(labels).lower()

    present, missing = [], []
    for t in fmt["required_tabs"]:
        hit = (t["panel_id_hint"] in panels) or (t["label"].lower() in low)
        (present if hit else missing).append(t["id"])

    extra_known = [e["id"] for e in fmt["observed_but_not_in_the_required_list"]
                   if e["panel_id_hint"] in panels]
    named = {t["panel_id_hint"] for t in fmt["required_tabs"]}
    named |= {e["panel_id_hint"] for e in fmt["observed_but_not_in_the_required_list"]}
    extra_unknown = sorted(panels - named)
    return present, missing, extra_known, extra_unknown, len(panels)


def main(argv):
    fmt = load_format()
    declared = len(fmt["required_tabs"])
    if argv:
        pages = argv
    else:
        pm = json.load(open(os.path.join(_ROOT, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
        pages = sorted(pm)
    print("DECLARED REQUIRED TABS: %d  (ssot/page_format_v1.json, status=%s)"
          % (declared, fmt.get("_status", "")[:40]))
    print("unit: REQUIRED PRESENT / REQUIRED DECLARED. Extras reported, never netted.\n")

    hist, rows, seen, tombstones = {}, [], 0, []
    for pg in pages:
        full = pg if os.path.isabs(pg) else os.path.join(_ROOT, pg)
        if not os.path.exists(full):
            continue
        seen += 1
        got = check(full, fmt)
        if got is None:
            tombstones.append(os.path.basename(pg))
            continue
        present, missing, ek, eu, npanels = got
        hist[len(present)] = hist.get(len(present), 0) + 1
        rows.append((os.path.basename(pg), len(present), missing, ek, eu))

    # ⭐ THE POPULATION, BY KIND -- never a bare total. A tombstone is not a review page and
    # not a defect; it is a third thing, and it must leave the denominator explicitly rather
    # than by being silently skipped.
    print("PAGE MAP ENTRIES  : %d" % len(pages))
    print("  files found     : %d" % seen)
    print("  RETIRED-REVIEW TOMBSTONES (excluded, not defects): %d" % len(tombstones))
    print("  REVIEW PAGES -- the real denominator             : %d\n" % len(rows))
    if tombstones:
        print("  tombstones: %s\n" % ", ".join(t[:34] for t in tombstones[:6])
              + ("    ... and %d more\n" % (len(tombstones) - 6) if len(tombstones) > 6 else ""))
    seen = len(rows)
    print("distribution of required-tabs-present:")
    for k in sorted(hist, reverse=True):
        print("   %d/%d required present : %3d pages" % (k, declared, hist[k]))

    worst = sorted(rows, key=lambda r: r[1])[:5]
    print("\nfewest required tabs:")
    for name, n, missing, ek, eu in worst:
        print("   %-52s %d/%d  missing=%s" % (name[:52], n, declared, ",".join(missing)))

    allmissing = {}
    for _, _, missing, _, _ in rows:
        for m in missing:
            allmissing[m] = allmissing.get(m, 0) + 1
    print("\nrequired tab MISSING, by tab:")
    for k, v in sorted(allmissing.items(), key=lambda kv: -kv[1]):
        print("   %-16s missing on %3d/%d pages" % (k, v, seen))

    extras = {}
    for _, _, _, ek, eu in rows:
        for e in list(ek) + list(eu):
            extras[e] = extras.get(e, 0) + 1
    print("\nEXTRA tabs present but not required (reported, not credited):")
    for k, v in sorted(extras.items(), key=lambda kv: -kv[1]):
        print("   %-16s on %3d pages" % (k, v))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
