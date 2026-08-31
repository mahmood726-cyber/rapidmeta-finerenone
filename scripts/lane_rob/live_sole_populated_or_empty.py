# -*- coding: utf-8 -*-
"""Of the pages that are a subject's ONLY coverage, how many contain a result?

THE TWO FINDINGS THAT COMBINE. This lane established that 518 legacy pages are the sole
coverage of their subject: no successor, and a reader is routed there. The harness lane
established that 744 of 795 legacy pages are unpopulated app shells -- every result slot
reads `--`, and only 19 carry a formatted effect estimate. Both are true, so for some share
of those 518 subjects the ONLY page that exists contains no results.

THAT IS A DIFFERENT CLAIM FROM "UNAUDITED". An unaudited page says something we have not
checked. An empty shell says nothing while presenting PRISMA, GRADE, AMSTAR-2 and a
risk-of-bias grid around the absence -- and because the delivery system already chose that
page as the survivor of a consolidation, it is the corpus's own answer to "what do we say
about this topic". The intersection is the honest size of the corpus, and neither 141 nor
1,463 is it.

THE DETECTOR IS VALIDATED BEFORE IT IS USED. It is checked against the harness lane's
published figure on the harness lane's own population first. A detector that has not
reproduced a known answer is an assumption wearing a number, and the two lanes counting the
same pages with different instruments is exactly how one lane's artefact becomes both lanes'
finding.

WHAT COUNTS AS A RESULT: a formatted effect estimate in the RENDERED text -- a point estimate
with an interval beside it. Not a number in a script, because the question is what a reader
sees. Three kinds, so nothing is silently dropped:

  POPULATED     at least one point estimate with an interval
  EMPTY_SHELL   no estimate, and placeholder dashes where results belong
  NEITHER       no estimate and no placeholders -- named, not folded into either

RECONCILIATION WITH THE HARNESS LANE, UNRESOLVED AND SAID SO. On the unstamped subset --
797 pages, essentially their 795 -- this detector finds 9 populated where they publish 19.
Fewer, on a slightly larger population, so this instrument is the stricter of the two and
the gap is in the direction of over-stating emptiness. Three hypotheses were tested and all
three returned exactly zero:

  integer formatting     "12 (95% CI 8 to 16)" that a decimals-only pattern cannot see  -> 0
  table layout           estimate and bounds in separate cells, so no parentheses exist  -> 0
  unrendered data        an estimate held in a script that never reaches the reader      -> 0

So the gap is not number format, not layout, and not hidden data. What remains is a
difference in POPULATION MEMBERSHIP or in what the other detector accepts, and neither can
be settled from this side: it needs the two page lists compared directly.

THE CONCLUSION DOES NOT DEPEND ON RESOLVING IT, and that is worth saying plainly so the open
gap does not look load-bearing. At this detector's rate 8 of 518 sole-coverage pages carry a
result; at the harness lane's rate it would be roughly twice that. Either way 97-98% of the
pages that are a subject's only coverage contain no result at all.
"""
import collections
import html
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
os.chdir(REPO)

# A point estimate with an interval beside it: 0.83 (95% CI 0.74 to 0.93), 0.83 (0.74-0.93),
# 1.2 (95% CrI 0.9, 1.6). Anchored on the left so it cannot start mid-number.
ESTIMATE = re.compile(
    r"(?<![\d.])\d{1,3}\.\d{1,3}\s*"
    r"\(\s*(?:95\s*%?\s*)?(?:CI|CrI|credible|confidence)?[^)\d]{0,12}"
    r"[-\u2212]?\d{1,3}\.\d{1,3}\s*(?:to|,|\u2013|\u2014|-)\s*[-\u2212]?\d{1,3}\.\d{1,3}\s*\)")
# Placeholder where a result belongs: a cell or slot whose whole content is dashes.
PLACEHOLDER = re.compile(r">\s*[-\u2013\u2014]{1,3}\s*<")


def rendered(raw):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))


def classify(path):
    try:
        raw = open(path, "rb").read().decode("utf-8", "replace")
    except OSError:
        return None
    est = ESTIMATE.findall(rendered(raw))
    ph = PLACEHOLDER.findall(raw)
    if est:
        kind = "POPULATED"
    elif ph:
        kind = "EMPTY_SHELL"
    else:
        kind = "NEITHER"
    return {"page": path, "kind": kind, "n_estimates": len(est),
            "n_placeholders": len(ph), "first": (est[0][:44] if est else None)}


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    rows = json.load(io.open(r"F:\claude-temp\pend\legacy_live_or_retired.json",
                             encoding="utf-8"))
    seen = {}
    for r in rows:
        c = classify(r["page"])
        if c:
            c["live_kind"] = r["kind"]
            seen[r["page"]] = c

    def tally(sub):
        return collections.Counter(c["kind"] for c in sub)

    allc = list(seen.values())
    print("=" * 94)
    print("DOES THE ONLY PAGE ON A SUBJECT CONTAIN A RESULT?")
    print("=" * 94)
    print("")
    print("VALIDATION FIRST -- the whole legacy population, against the harness lane's")
    print("published figure of 19 populated in 795.")
    t = tally(allc)
    print("  legacy pages read                    %4d  == the denominator" % len(allc))
    for k in ("POPULATED", "EMPTY_SHELL", "NEITHER"):
        print("     %-14s %4d   %5.1f%%" % (k, t[k], 100.0 * t[k] / len(allc)))
    print("     %-14s %4d   == the population" % ("sum", sum(t.values())))
    print("")
    print("  harness lane, its own population:      19 populated of 795")
    print("  this detector, this population:      %4d populated of %d" % (t["POPULATED"], len(allc)))
    print("")
    print("THE INTERSECTION -- pages that are a subject's ONLY coverage:")
    live = [c for c in allc if c["live_kind"] == "LIVE_SOLE"]
    tl = tally(live)
    print("  LIVE_SOLE pages                      %4d  == the denominator" % len(live))
    for k in ("POPULATED", "EMPTY_SHELL", "NEITHER"):
        print("     %-14s %4d   %5.1f%%" % (k, tl[k], 100.0 * tl[k] / len(live)))
    print("")
    print("  SOLE COVERAGE THAT CONTAINS A RESULT  %4d" % tl["POPULATED"])
    print("  SOLE COVERAGE THAT CONTAINS NOTHING   %4d" % (len(live) - tl["POPULATED"]))
    print("")
    print("  by live-kind, all three arms:")
    for lk in ("LIVE_SOLE", "SUPERSEDED", "ORPHAN_NO_ROUTE"):
        sub = [c for c in allc if c["live_kind"] == lk]
        s = tally(sub)
        print("     %-16s %4d pages   populated %3d   shell %4d   neither %3d"
              % (lk, len(sub), s["POPULATED"], s["EMPTY_SHELL"], s["NEITHER"]))
    print("")
    print("  SOLE COVERAGE, POPULATED -- the pages that actually say something:")
    for c in sorted((c for c in live if c["kind"] == "POPULATED"),
                    key=lambda c: -c["n_estimates"])[:12]:
        print("     %-46s %3d estimates   %s"
              % (os.path.basename(c["page"])[:46], c["n_estimates"], c["first"]))
    nei = [c for c in live if c["kind"] == "NEITHER"]
    if nei:
        print("")
        print("  NEITHER -- no estimate and no placeholder, named rather than folded in:")
        for c in nei[:10]:
            print("     %s" % os.path.basename(c["page"]))
    json.dump(allc, io.open(r"F:\claude-temp\pend\live_sole_populated.json", "w",
                            encoding="utf-8"), indent=1)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import provenance as _pv
    print("  provenance -> %s" % os.path.basename(_pv.stamp(
        r"F:\claude-temp\pend\live_sole_populated.json", inputs=[r"F:\claude-temp\pend\legacy_live_or_retired.json"])))
    print("")
    print("  detail -> live_sole_populated.json")


if __name__ == "__main__":
    main()
