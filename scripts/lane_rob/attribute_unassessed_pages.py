# -*- coding: utf-8 -*-
"""What ARE the 1,369 pages no instrument can see? Establish, do not assess.

WHY. The certainty gate reports 88 attributable pages clean and 1,369 it cannot attribute to
a store at all. It refuses on those rather than passing them, which is honest, but "1,369
unknown" is the largest unmeasured population on the project and it is invisible precisely
because every instrument reports confidently on what remains. A population that size that no
tool can name is where the next external finding comes from.

THIS DOES NOT ASSESS THEM. It classifies them, so an invisible population becomes a bounded
one. Every count prints its numerator and its denominator, which is the house rule that
caught two broken guards tonight in opposite directions.

KINDS, chosen so every page lands in exactly one and none is silently dropped:

  HAS_STORE            a store exists for it; the gate simply could not attribute it
  RETIRED_TOMBSTONE    the page says it is retired or its estimate is withdrawn
  REDIRECT_STUB        a small page whose job is to point somewhere else
  INDEX_OR_TOOL        an index, dashboard, atlas or utility rather than a review
  NO_STORE_REVIEW      looks like a review, and no store answers to it
  UNREADABLE           could not be read
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

TOPIC_IN_PAGE = re.compile(rb"ssot/([a-z0-9][a-z0-9-]{2,})/")
TOMB = re.compile(rb"Retired review|This review has been retired|Estimate withdrawn", re.I)
REDIRECT = re.compile(rb'http-equiv="refresh"|rel="canonical"', re.I)
TOOLISH = re.compile(r"index|atlas|dashboard|pools|table|checklist|map|hub|tools?$", re.I)


def known_topics():
    out = set()
    for p in glob.glob("ssot/*/*.json"):
        t = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) == t + ".json":
            out.add(t)
    return out


def classify(page, raw, known):
    c = collections.Counter(m.group(1).decode("ascii", "ignore")
                            for m in TOPIC_IN_PAGE.finditer(raw))
    for name, _ in c.most_common():
        if name in known:
            return "HAS_STORE", name
    stem = os.path.basename(page)[:-5].lower().replace("_", "-")
    for cand in (stem, stem.replace("-review", ""), stem + "-review"):
        if cand in known:
            return "HAS_STORE", cand
    if len(raw) < 8000 and REDIRECT.search(raw):
        return "REDIRECT_STUB", None
    if TOMB.search(raw[:20000]):
        return "RETIRED_TOMBSTONE", None
    if TOOLISH.search(os.path.basename(page)[:-5]):
        return "INDEX_OR_TOOL", None
    return "NO_STORE_REVIEW", None


def main():
    known = known_topics()
    pages = sorted(glob.glob("*.html"))
    rows = []
    for p in pages:
        try:
            raw = open(p, "rb").read()
        except OSError:
            rows.append((p, "UNREADABLE", None, 0))
            continue
        kind, topic = classify(p, raw, known)
        rows.append((p, kind, topic, len(raw)))

    print("=" * 88)
    print("ATTRIBUTING THE PAGES NO INSTRUMENT COULD SEE")
    print("=" * 88)
    print("  stores on disk                              %4d" % len(known))
    print("  delivered pages                             %4d  == the denominator" % len(rows))
    print("")
    c = collections.Counter(k for _, k, _, _ in rows)
    for k, v in c.most_common():
        print("     %-24s %5d   %5.1f%%" % (k, v, 100.0 * v / len(rows)))
    print("     %-24s %5d   == the population" % ("sum", sum(c.values())))
    print("")
    attributable = c["HAS_STORE"]
    print("  ATTRIBUTABLE TO A STORE                     %4d" % attributable)
    print("  NOT ATTRIBUTABLE                            %4d" % (len(rows) - attributable))
    print("")
    med = {}
    for _, k, _, n in rows:
        med.setdefault(k, []).append(n)
    print("  median page size by kind, as a sanity check on the classification:")
    for k in sorted(med):
        v = sorted(med[k])
        print("     %-24s %5d pages   median %8d bytes" % (k, len(v), v[len(v) // 2]))
    print("")
    for k in ("NO_STORE_REVIEW", "INDEX_OR_TOOL"):
        ex = [p for p, kk, _, _ in rows if kk == k][:8]
        print("  examples, %s:" % k)
        for e in ex:
            print("     %s" % e)
    json.dump([{"page": p, "kind": k, "topic": t, "bytes": n} for p, k, t, n in rows],
              io.open(r"F:\claude-temp\pend\page_attribution.json", "w", encoding="utf-8"),
              indent=1)
    print("")
    print("  detail -> page_attribution.json")
    print("  ESTABLISHED, NOT ASSESSED: this says what these pages ARE, not whether they")
    print("  are correct. No page here has been judged.")


if __name__ == "__main__":
    main()
