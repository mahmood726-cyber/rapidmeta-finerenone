# -*- coding: utf-8 -*-
"""What ARE the 860 published review pages with no store? Name them. Assess nothing.

WHY THIS IS ABOVE D5. Every build, rebuild and coverage number this project has produced --
every lane's -- describes the 94 delivered pages that have an SSOT object. 860 full review
pages have none. They are 59% of what a reader can reach and 0% of what any instrument
measures, because every instrument starts from the stores.

THE TWO MYSTERIES ARE ONE POPULATION. The harness lane's "1,369 pages no instrument can
attribute" and this lane's split are the same set seen from two directions: 1,463 delivered
minus 94 with stores is exactly 1,369, decomposing as 860 store-less reviews, 501 redirect
stubs, 5 index or tool pages, 3 tombstones. One enumeration serves both.

SIGNALS READ, all cheap and all from the bytes:

  linked from index.html   is a reader routed here at all, or is it orphaned?
  build stamp              can it be rebuilt correctly, or is its generator unknown?
  filename generation      _AUTO_2 / _AUTO_FULL_REVIEW / _AUTO_REVIEW / plain _REVIEW
  superseded by a stub     does a redirect stub point AT this page, or does one replace it?

NAMING, NOT ASSESSING. Nothing here says a page is wrong. It says what kind of thing it is,
so a population that is invisible becomes a bounded one.
"""
import collections
import glob
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
os.chdir(REPO)

STAMP = re.compile(rb"Generator build")
REDIRECT_TARGET = re.compile(rb'(?:refresh[^>]*url=|canonical"\s+href=")([A-Z0-9_\-]+\.html)',
                             re.I)


def main():
    attrib = json.load(io.open(r"F:\claude-temp\pend\page_attribution.json",
                               encoding="utf-8"))
    storeless = [r["page"] for r in attrib if r["kind"] == "NO_STORE_REVIEW"]
    stubs = [r["page"] for r in attrib if r["kind"] == "REDIRECT_STUB"]

    # which pages does a redirect stub point AT? those are the survivors of a consolidation
    pointed_at = set()
    for s in stubs:
        try:
            b = open(s, "rb").read()
        except OSError:
            continue
        for m in REDIRECT_TARGET.finditer(b):
            pointed_at.add(m.group(1).decode("ascii", "ignore"))

    try:
        idx = open("index.html", "rb").read().decode("utf-8", "replace")
    except OSError:
        idx = ""
    linked = set(re.findall(r'href="([A-Za-z0-9_\-]+\.html)"', idx))

    rows = []
    for p in storeless:
        try:
            b = open(p, "rb").read()
        except OSError:
            continue
        gen = ("_AUTO_2" if "_AUTO_2" in p else
               "_AUTO_FULL_REVIEW" if "_AUTO_FULL_REVIEW" in p else
               "_AUTO_REVIEW" if "_AUTO_REVIEW" in p else
               "_SSOT" if "_SSOT" in p else "plain _REVIEW")
        rows.append({"page": p, "generation": gen,
                     "linked_from_index": p in linked,
                     "has_stamp": bool(STAMP.search(b)),
                     "is_redirect_target": p in pointed_at,
                     "bytes": len(b)})

    n = len(rows)
    print("=" * 90)
    print("THE 860: PUBLISHED REVIEW PAGES WITH NO STORE")
    print("=" * 90)
    print("  store-less review pages                     %4d  == the denominator" % n)
    print("  delivered pages overall                     %4d" % len(attrib))
    print("  redirect stubs (the benign 501)             %4d" % len(stubs))
    print("")
    print("  LINKED FROM index.html                      %4d   %5.1f%%"
          % (sum(1 for r in rows if r["linked_from_index"]),
             100.0 * sum(1 for r in rows if r["linked_from_index"]) / n))
    print("  ORPHANED (no index link)                    %4d   %5.1f%%"
          % (sum(1 for r in rows if not r["linked_from_index"]),
             100.0 * sum(1 for r in rows if not r["linked_from_index"]) / n))
    print("")
    print("  carries a build stamp (rebuildable)         %4d   %5.1f%%"
          % (sum(1 for r in rows if r["has_stamp"]),
             100.0 * sum(1 for r in rows if r["has_stamp"]) / n))
    print("  no stamp: generator unknown                 %4d   %5.1f%%"
          % (sum(1 for r in rows if not r["has_stamp"]),
             100.0 * sum(1 for r in rows if not r["has_stamp"]) / n))
    print("")
    print("  a redirect stub points AT it (a survivor)   %4d" %
          sum(1 for r in rows if r["is_redirect_target"]))
    print("")
    print("  BY GENERATION, from the filename:")
    for k, v in collections.Counter(r["generation"] for r in rows).most_common():
        sub = [r for r in rows if r["generation"] == k]
        print("     %-22s %4d   linked %4d   stamped %4d   median %8d bytes"
              % (k, v, sum(1 for r in sub if r["linked_from_index"]),
                 sum(1 for r in sub if r["has_stamp"]),
                 sorted(r["bytes"] for r in sub)[len(sub) // 2]))
    print("")
    print("  THE CROSS THAT MATTERS -- linked to a reader AND unrebuildable:")
    live_blind = [r for r in rows if r["linked_from_index"] and not r["has_stamp"]]
    print("     %4d pages a reader can reach that nothing can rebuild or check"
          % len(live_blind))
    for r in live_blind[:10]:
        print("       %s" % r["page"])
    json.dump(rows, io.open(r"F:\claude-temp\pend\storeless.json", "w", encoding="utf-8"),
              indent=1)
    print("")
    print("  detail -> storeless.json")
    print("  NAMED, NOT ASSESSED. Nothing here says a page is wrong.")


if __name__ == "__main__":
    main()
