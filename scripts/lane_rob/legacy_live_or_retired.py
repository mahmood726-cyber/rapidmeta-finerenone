# -*- coding: utf-8 -*-
"""Are the legacy pages LIVE or RETIRED? The one attribute only the store side can answer.

THE STATE THAT IS NOT ACTIONABLE. Served, reachable and unclassifiable is where these pages
sit today: no stamp, no store, no retirement notice. If they are live they are the majority
of the corpus and unaudited; if they are retired they should not be served. Nothing in the
delivered bytes distinguishes the two, which is why no served-side census can settle it.

WHAT THE STORE SIDE CAN DECIDE, and it is one question: does a CURRENT-GENERATION page or a
store already cover this page's subject? A legacy page whose subject has a modern successor
is a duplicate that outlived its replacement -- retiring it costs a reader nothing. A legacy
page with no successor is the ONLY coverage of that subject a reader can reach, and retiring
it removes the subject from the corpus.

SUBJECT, NOT FILENAME. The join is on drug-plus-condition recovered from the stem, because a
name is not an identity: ABATACEPT_PSA_AUTO_FULL_REVIEW, ABATACEPT_PSA_REVIEW and the store
`abatacept-psa` are one subject under three spellings, and joining on the filename would
report three unrelated pages.

FOUR KINDS, and every page lands in exactly one:

  SUPERSEDED        a store or current-generation page covers this subject. Retirement is
                    the safe state; a reader loses nothing.
  LIVE_SOLE         no successor, and a reader is routed here -- linked from the index or
                    pointed at by a redirect stub. This is the only coverage of its subject.
  ORPHAN_NO_ROUTE   no successor and nothing routes here. Reachable only by direct URL.
  AMBIGUOUS         the stem yields no usable subject key, so no join can be attempted.

THIS DOES NOT RETIRE ANYTHING. It assigns the attribute the served-side census cannot, so
the population stops being unactionable. Deciding what to serve is Mahmood's.
"""
import collections
import glob
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
os.chdir(REPO)

GEN_SUFFIX = re.compile(
    r"_(AUTO_FULL_REVIEW|AUTO_REVIEW|AUTO_2|FULL_REVIEW|REVIEW|SSOT|LIVING_MA|MA)$", re.I)
STORE_SUFFIX = re.compile(
    r"-(auto-full-review|auto-review|full-review|review|ssot|auto-2)$", re.I)
STUB_TARGET = re.compile(rb'(?:refresh[^>]*url=|canonical"\s+href=")([A-Za-z0-9_\-]+\.html)',
                         re.I)


def subject_key(page):
    """drug-plus-condition, generation stripped. None when nothing usable remains."""
    stem = os.path.basename(page)[:-5]
    prev = None
    while prev != stem:                      # _AUTO_2_REVIEW etc. carry two suffixes
        prev = stem
        stem = GEN_SUFFIX.sub("", stem)
    k = stem.lower().replace("_", "-").strip("-")
    k = re.sub(r"-(review|ma|living-ma)$", "", k)
    return k or None


def main():
    # THE WRAPPER IS INSTALLED HERE, NOT AT MODULE LEVEL. A module-level
    # `sys.stdout = TextIOWrapper(sys.stdout.buffer, ...)` closes the caller's stdout the
    # moment this module is IMPORTED -- which it now is, because subject_key() is the join
    # predicate and any check of the join has to import it. That is exactly how a control
    # run of this script's own accuracy died a moment ago.
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    attrib = json.load(io.open(r"F:\claude-temp\pend\page_attribution.json",
                               encoding="utf-8"))
    by_kind = collections.defaultdict(list)
    for r in attrib:
        by_kind[r["kind"]].append(r["page"])

    stores = set()
    for p in glob.glob("ssot/*/*.json"):
        t = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) == t + ".json":
            stores.add(t)

    # SUCCESSOR SUBJECTS: every subject a store covers, plus every subject a page WITH a
    # store covers. Both arms, because a store whose page is named differently still means
    # the subject is currently maintained.
    # BOTH SPELLINGS OF EVERY STORE. Store directories retain the generation suffix
    # (`bococizumab-lipid-review`, `meropenem-auto-full-review`) while a page key strips it,
    # so the raw directory name joins with almost nothing. Normalising the store name the
    # same way makes the two sides comparable: measured on the 94 pages whose store is
    # known, the key agrees with the normalised store name 92 times (97.9%), and the two
    # genuine divergences are ARNI_HF_REVIEW -> arni-hfref and ROTAVIRUS_VACCINE_AUTO_FULL
    # -> rotavirus-vaccine-africa-review.
    successor = set(stores) | {STORE_SUFFIX.sub("", t) for t in stores}
    for p in by_kind["HAS_STORE"]:
        k = subject_key(p)
        if k:
            successor.add(k)

    # WHAT EACH REDIRECT STUB POINTS AT. A stub aiming at a legacy page is the delivery
    # system having already chosen that page as the survivor of a consolidation.
    pointed_at = set()
    for s in by_kind["REDIRECT_STUB"]:
        try:
            b = open(s, "rb").read()
        except OSError:
            continue
        for m in STUB_TARGET.finditer(b):
            pointed_at.add(m.group(1).decode("ascii", "ignore"))

    try:
        idx = open("index.html", "rb").read().decode("utf-8", "replace")
    except OSError:
        idx = ""
    linked = set(re.findall(r'href="([A-Za-z0-9_\-]+\.html)"', idx))

    legacy = by_kind["NO_STORE_REVIEW"]
    rows = []
    for p in legacy:
        k = subject_key(p)
        routed = (p in linked) or (p in pointed_at)
        if k is None:
            kind = "AMBIGUOUS"
        elif k in successor:
            kind = "SUPERSEDED"
        elif routed:
            kind = "LIVE_SOLE"
        else:
            kind = "ORPHAN_NO_ROUTE"
        rows.append({"page": p, "subject": k, "kind": kind,
                     "linked_from_index": p in linked,
                     "pointed_at_by_stub": p in pointed_at})

    n = len(rows)
    print("=" * 92)
    print("LEGACY PAGES: LIVE OR RETIRED -- the attribute the served side cannot assign")
    print("=" * 92)
    print("  stores on disk                                %4d" % len(stores))
    print("  successor SUBJECTS (store or current-gen page) %3d" % len(successor))
    print("  legacy pages, no store                        %4d  == the denominator" % n)
    print("")
    c = collections.Counter(r["kind"] for r in rows)
    for k in ("SUPERSEDED", "LIVE_SOLE", "ORPHAN_NO_ROUTE", "AMBIGUOUS"):
        print("     %-18s %4d   %5.1f%%" % (k, c[k], 100.0 * c[k] / n))
    print("     %-18s %4d   == the population" % ("sum", sum(c.values())))
    print("")
    print("  RETIRING IS SAFE FOR                          %4d  (a successor exists)"
          % c["SUPERSEDED"])
    print("  RETIRING REMOVES THE SUBJECT FOR              %4d  (sole coverage, routed)"
          % c["LIVE_SOLE"])
    print("  reachable only by direct URL                  %4d" % c["ORPHAN_NO_ROUTE"])
    print("")
    live = [r for r in rows if r["kind"] == "LIVE_SOLE"]
    print("  of the sole-coverage pages: %d linked from the index, %d pointed at by a stub"
          % (sum(1 for r in live if r["linked_from_index"]),
             sum(1 for r in live if r["pointed_at_by_stub"])))
    print("")
    print("  SOLE COVERAGE, first 14 by subject -- retiring any of these deletes a topic:")
    for r in sorted(live, key=lambda r: r["subject"])[:14]:
        print("     %-34s %s" % (r["subject"][:34], os.path.basename(r["page"])))
    print("")
    print("  SUPERSEDED, first 8 -- a successor already covers the subject:")
    for r in sorted((r for r in rows if r["kind"] == "SUPERSEDED"),
                    key=lambda r: r["subject"])[:8]:
        print("     %-34s %s" % (r["subject"][:34], os.path.basename(r["page"])))
    if c["AMBIGUOUS"]:
        print("")
        print("  NO SUBJECT KEY -- named, not guessed:")
        for r in (r for r in rows if r["kind"] == "AMBIGUOUS"):
            print("     %s" % r["page"])
    json.dump(rows, io.open(r"F:\claude-temp\pend\legacy_live_or_retired.json", "w",
                            encoding="utf-8"), indent=1)
    print("")
    print("  detail -> legacy_live_or_retired.json")
    print("  NOTHING RETIRED HERE. This assigns the attribute; the decision is Mahmood's.")


if __name__ == "__main__":
    main()
