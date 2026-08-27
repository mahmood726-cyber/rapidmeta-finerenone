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


def page_map():
    """The AUTHORITATIVE page -> store map, which this classifier did not consult.

    The first version attributed a page by scanning its bytes for `ssot/<topic>/` and by
    matching its filename stem against store directory names. Both are inferences. The
    repository ships ssot/PAGE_MAP.json, which STATES the mapping, and 63 pages it maps to a
    store that exists on disk were classified here as legacy -- so a page with an object was
    reported as a page with none, and every downstream count inherited it.

    That is the same failure as every other denominator defect this week: the classifier
    reported where it looked. It looked at page bytes and filenames and not at the file whose
    entire purpose is to answer the question being asked.
    """
    import json as _json
    f = os.path.join("ssot", "PAGE_MAP.json")
    if not os.path.exists(f):
        return {}
    try:
        m = _json.load(io.open(f, encoding="utf-8"))
    except Exception:
        return {}
    out = {}
    for page, store in m.items():
        if not isinstance(store, str):
            continue
        if os.path.exists(store):                      # a map entry is not a store
            out[os.path.basename(page)] = os.path.basename(os.path.dirname(store))
    return out


SUFFIX = re.compile(
    r"[-_](auto[-_]full[-_]review|auto[-_]review|full[-_]review|review|ssot|auto[-_]2|"
    r"living[-_]ma|ma)$", re.I)


def norm(name):
    """Strip generation suffixes repeatedly, BOTH SIDES, then compare.

    The suffix blind spot has now produced two separate defects. It made the first subject
    join agree only 35.1% until the same suffix was stripped from page keys and store
    directory names alike; and it is why ANTIMALARIAL_ACT_SSOT, CRYPTOCOCCAL_MENINGITIS_SSOT
    and PREVNAR15_PNEUMO_SSOT -- all three populated -- were reported as having no object.
    Fixed once, here, rather than a third time somewhere else.
    """
    k = str(name).lower().replace("_", "-").strip("-")
    prev = None
    while prev != k:
        prev = k
        k = SUFFIX.sub("", k)
    return k


def classify(page, raw, known, mapped=None, nknown=None):
    # THE SHARED DEFINITION, AND IT IS THE OTHER LANE'S: a page has a canonical object when it
    # DECLARES that object's identity in its served bytes. That is evidence a reader receives,
    # not a directory convention either side happens to follow. My previous version made
    # PAGE_MAP the authority -- a claim ABOUT a page rather than a claim BY it -- and that is
    # exactly the 13 pages I called HAS_STORE that the served side calls a stub and the 14 it
    # calls current-generation-with-no-store. A map entry is a promise; the bytes are evidence.
    c = collections.Counter(m.group(1).decode("ascii", "ignore")
                            for m in TOPIC_IN_PAGE.finditer(raw))
    for name, _ in c.most_common():
        if name in known:
            return "HAS_STORE", name
    # SYMMETRIC SUFFIX STRIPPING on the page's OWN NAME, which is the page naming itself
    # rather than a third party asserting something about it, so it stays on this side of
    # the line the shared definition draws.
    # WHAT THE PAGE IS COMES BEFORE WHAT ITS NAME RESEMBLES. Putting the normalised-name
    # match ahead of these checks promoted 85 redirect stubs to HAS_STORE in one run: a stub
    # called X_AUTO_FULL_REVIEW.html normalises onto the store `x` and was declared an object
    # it merely points at. A stub is a pointer, and a pointer declares nothing -- which is the
    # shared definition doing real work rather than being restated.
    if len(raw) < 8000 and REDIRECT.search(raw):
        return "REDIRECT_STUB", None
    if TOMB.search(raw[:20000]):
        return "RETIRED_TOMBSTONE", None
    ns = norm(os.path.basename(page)[:-5])
    if nknown and ns in nknown:
        return "HAS_STORE", nknown[ns]
    # PAGE_MAP NAMES IT BUT THE BYTES DO NOT DECLARE IT. Its own kind, not promoted to
    # HAS_STORE: a reader receiving this page gets no provenance from it at all.
    if mapped and os.path.basename(page) in mapped:
        return "MAPPED_NOT_DECLARED", mapped[os.path.basename(page)]
    if TOOLISH.search(os.path.basename(page)[:-5]):
        return "INDEX_OR_TOOL", None
    return "NO_STORE_REVIEW", None


def main():
    known = known_topics()
    mapped = page_map()
    nknown = {}
    for t in known:                       # normalised store name -> real store name
        nknown.setdefault(norm(t), t)
    pages = sorted(glob.glob("*.html"))
    rows = []
    for p in pages:
        try:
            raw = open(p, "rb").read()
        except OSError:
            rows.append((p, "UNREADABLE", None, 0))
            continue
        kind, topic = classify(p, raw, known, mapped, nknown)
        rows.append((p, kind, topic, len(raw)))

    print("=" * 88)
    print("ATTRIBUTING THE PAGES NO INSTRUMENT COULD SEE")
    print("=" * 88)
    print("  stores on disk                              %4d" % len(known))
    print("  pages named by PAGE_MAP with a live store   %4d" % len(mapped))
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
    out = r"F:\claude-temp\pend\page_attribution.json"
    json.dump([{"page": p, "kind": k, "topic": t, "bytes": n} for p, k, t, n in rows],
              io.open(out, "w", encoding="utf-8"), indent=1)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import provenance as _pv
    side = _pv.stamp(out, inputs=["ssot/PAGE_MAP.json", "index.html"],
                     note="page attribution under the shared definition: a page has a "
                          "canonical object when its served bytes declare that object")
    print("  provenance -> %s" % os.path.basename(side))
    print("")
    print("  detail -> page_attribution.json")
    print("  ESTABLISHED, NOT ASSESSED: this says what these pages ARE, not whether they")
    print("  are correct. No page here has been judged.")


if __name__ == "__main__":
    main()
