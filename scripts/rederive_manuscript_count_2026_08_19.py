#!/usr/bin/env python3
"""Re-derive "37 of 43 cardiology topics have no manuscript" against the DELIVERED page.

P18: A RESTATED QUANTITY IS REPRODUCIBLE BY A COMMAND. This is that command. Run it and
the number is re-derived from the pages on disk; nothing here is quoted from a document.

    python scripts/rederive_manuscript_count_2026_08_19.py

WHAT WAS WRONG WITH THE ORIGINAL FIGURE. `evidence/2026-08-19-batch1/completeness_audit.json`
records one page per topic and counts its paper panel. For three topics **the same object is
served by TWO delivered pages, and the two disagree about whether the review has a manuscript**:

    topic                          audited page                     other delivered page
    alirocumab-lipid               ALIROCUMAB_LIPID_AUTO_FULL  328   ALIROCUMAB_LIPID_SSOT      6706
    azilsartan-chlorthalidone-..   AZILSARTAN_HTN_AUTO_FULL    356   AZILSARTAN_CLD_VS_OLM      6366
    bococizumab-lipid-review       BOCOCIZUMAB_LIPID_AUTO_FULL 336   BOCOCIZUMAB_LIPID          8430

In each case the audit read the page WITHOUT the manuscript, and the page WITH it is the one
`scripts/verify_delivered_bytes.py` tracks as this topic's delivered artefact. So the topic has
a paper and the audit recorded that it has none.

    THE AUDIT WAS NOT WRONG ABOUT THE PAGE IT READ. It was wrong that there is one page.

THE TIE IS BROKEN BY verify_delivered_bytes.PAGES, not by a heuristic and not by picking the
larger number -- that dict is the repo's own declaration of which artefact is delivered for a
topic, and choosing the bigger paper would be choosing the answer we prefer.

A topic with two candidate pages and NO entry in that dict stays NOT_ASSESSABLE and is named.
It is never counted as having a manuscript and never counted as lacking one.
"""
import glob
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))

AUDIT = "evidence/2026-08-19-batch1/completeness_audit.json"
# The audit's own rows separate at ~350 (a refusing banner) against ~6,300 (a projected
# manuscript). Any threshold in that gap gives the same answer; it is stated, not tuned.
PAPER_FLOOR = 1500


def delivered_pages():
    """The repo's own topic -> delivered page declaration."""
    import verify_delivered_bytes as V
    return dict(V.PAGES)


def paper_chars(path):
    b = open(path, "rb").read().decode("utf-8", "replace")
    i = b.find('id="pn-paper"')
    j = b.find("<!--end-paper-->")
    if i < 0 or j <= i:
        return None
    return len(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", b[i:j])).strip())


def main():
    os.chdir(REPO)
    rows = json.load(open(AUDIT, encoding="utf-8"))["rows"]
    declared = delivered_pages()

    titles = {}
    for op in sorted(glob.glob("ssot/*/*.json")):
        try:
            o = json.load(open(op, encoding="utf-8"))
        except Exception:
            continue
        if isinstance(o, dict) and isinstance(o.get("title"), str):
            titles[os.path.basename(op)[:-5]] = o["title"]

    tabbed = [f for f in sorted(glob.glob("*.html"))
              if b'id="pn-search"' in open(f, "rb").read()]

    had, lacked, na, corrected = [], [], [], []
    for r in rows:
        topic, audited, audited_chars = r["topic"], str(r["page"]), r["paper_chars"]
        title = titles.get(topic)
        hits = []
        if title:
            esc = title.replace("&", "&amp;").replace("'", "&#x27;")
            for f in tabbed:
                b = open(f, "rb").read().decode("utf-8", "replace")
                if title in b or esc in b:
                    hits.append(f)
        if not hits:
            page = audited if os.path.exists(audited) else None
        elif len(hits) == 1:
            page = hits[0]
        else:
            page = declared.get(topic)
            if page is None or not os.path.exists(page):
                na.append((topic, "%d delivered pages match its title and none is declared "
                                  "in verify_delivered_bytes.PAGES" % len(hits)))
                continue
        if page is None:
            na.append((topic, "no delivered page located"))
            continue
        n = paper_chars(page)
        if n is None:
            na.append((topic, "no pn-paper panel in %s" % page))
            continue
        (had if n >= PAPER_FLOOR else lacked).append((topic, page, n))
        if page != audited and (audited_chars < PAPER_FLOOR <= n):
            corrected.append((topic, audited, audited_chars, page, n))

    print("ORIGINAL FIGURE  (completeness_audit.json): 6 with a manuscript, 37 without")
    print("PAPER_FLOOR                               : %d chars" % PAPER_FLOOR)
    print()
    print("RE-DERIVED against the page each topic actually delivers:")
    print("  WITH a manuscript   : %d" % len(had))
    print("  WITHOUT             : %d" % len(lacked))
    print("  NOT_ASSESSABLE      : %d" % len(na))
    print("  --------------------------")
    print("  rows                : %d" % len(rows))
    print()
    print("CORRECTED -- audited as having no paper, delivered page has one: %d"
          % len(corrected))
    for topic, ap, ac, np_, nc in corrected:
        print("  %-44s %s %d  ->  %s %d" % (topic[:44], ap[:38], ac, np_[:34], nc))
    print()
    print("NOT_ASSESSABLE, named rather than counted either way:")
    for topic, why in na:
        print("  %-44s %s" % (topic[:44], why))
    print()
    print("SCOPE: the 43 cardiology rows in the audit. Says nothing about infectious")
    print("       disease or about the 539 objectless pages.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
