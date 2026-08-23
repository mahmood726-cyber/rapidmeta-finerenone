"""Triage the identifiers pages HOLD but never show. The repairability picture the first pass could not see.

# no-control: a lookup, not a detector. The known answer per identifier is the registry's own
# response. The control that matters is asserted and identical to the first pass: NCT03914728
# must come back not-found, and the run refuses otherwise -- with the addition that
# ABALOPARATIDE's held NCT01343004 (the ACTIVE trial, read by hand) must come back FOUND, so
# the run cannot report absence without first demonstrating it can see a presence.

WHY A SECOND PASS EXISTS AT ALL. The first triage read only what a reader meets and put 630 of
745 legacy pages in "no identifier". That is the right answer to the question it asked. But 480
of those 630 HOLD identifiers and per-arm counts in their payload -- 1,556 distinct identifiers
across the bucket -- and those are checkable. Whether they resolve decides something the first
pass could not:

    a page holding an identifier that RESOLVES and matches      is a projection away from
                                                                repaired; the review exists
    a page holding one that DOES NOT EXIST                      is not repairable, and the
                                                                invisible provenance was
                                                                hiding that fact
    a page holding a DONOR                                      is the dangerous class, and
                                                                it has been invisible to
                                                                every reader and every check
                                                                so far

THE THIRD LINE IS THE REASON THIS RUN MATTERS. A donor identifier that is never displayed
cannot be caught by a reader, cannot be caught by a reader-facing probe, and passes an
existence check. It is the least visible defect in the corpus and the most serious.

NOTHING HERE RECLASSIFIES THE FIRST TRIAGE. Its counts stand: 630 pages show a reader no
identifier, and that is true whatever the payload holds. This reports a SECOND property of the
same pages, and both are true at once -- the shape that has read as a disagreement four times
tonight.
"""
from __future__ import annotations

import collections
import io
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import triage_legacy_registrations_2026_08_23 as T          # noqa: E402
import audit_no_identifier_pages_hold_data_2026_08_23 as H   # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HELD = os.path.join(REPO, "outputs", "no_identifier_data_state_2026_08_23.json")
OUT = os.path.join(REPO, "outputs", "held_identifier_triage_2026_08_23.json")

CONTROL_PRESENT = "NCT01343004"     # ACTIVE, held by ABALOPARATIDE_OSTEO, read by hand


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if not os.path.isfile(HELD):
        sys.exit("REFUSED: %s missing -- run the held-data audit first."
                 % os.path.relpath(HELD, REPO))
    held = json.load(io.open(HELD, encoding="utf-8"))
    names = sorted(set(held["by_bucket"].get("provenance_lost", [])
                       + held["by_bucket"].get("ids_no_data", [])))
    cache = T.load(T.CACHE, {})

    for nct, expect, why in ((T.CONTROL_ABSENT, False, "hand-confirmed NOT to resolve"),
                             (CONTROL_PRESENT, True,
                              "the ACTIVE trial, held by ABALOPARATIDE, read by hand")):
        r = T.query(nct, cache)
        print("CONTROL %s -> found=%r  (%s)" % (nct, r.get("found"), why))
        if r.get("found") is not expect:
            T.save(T.CACHE, cache)
            sys.exit("REFUSED: control %s came back %r, expected %r. A run that cannot see a "
                     "known presence must not report an absence." % (nct, r.get("found"), expect))
    T.save(T.CACHE, cache)

    per, allids = {}, set()
    for n in names:
        s = H.state_of(os.path.join(REPO, n))
        per[n] = s["ids"]
        allids.update(s["ids"])
    todo = sorted(i for i in allids if i not in cache)
    print("")
    print("%d page(s) hold %d distinct identifier(s); %d not yet queried"
          % (len(names), len(allids), len(todo)))
    for k, nct in enumerate(todo, 1):
        T.query(nct, cache)
        if k % 100 == 0:
            T.save(T.CACHE, cache)
            print("   %d/%d" % (k, len(todo)))
        time.sleep(0.1)
    T.save(T.CACHE, cache)

    b = collections.Counter()
    byb = collections.defaultdict(list)
    detail = {}
    for n in names:
        ids = per[n]
        terms = T.page_terms(n)
        found = [i for i in ids if cache.get(i, {}).get("found") is True]
        absent = [i for i in ids if cache.get(i, {}).get("found") is False]
        err = [i for i in ids if cache.get(i, {}).get("found") is None]
        if err or not ids:
            k = "needs_human"
            detail[n] = "%d identifier(s) unqueryable" % len(err) if err else "no held ids"
        elif absent and not found:
            k = "no_registration"
            detail[n] = "none of %d held id(s) resolve: %s" % (len(ids), ", ".join(absent[:5]))
        else:
            v = [T.describes(cache[i], terms) for i in found]
            mism = [i for i, d in zip(found, v) if d is False]
            if mism:
                k = "donor"
                detail[n] = "held id resolves to another subject: " + ", ".join(
                    "%s=%s" % (i, (cache[i].get("title") or "")[:60]) for i in mism[:2])
            elif all(d is True for d in v) and not absent:
                k = "repairable"
                detail[n] = "all %d held id(s) resolve and match" % len(found)
            else:
                k = "needs_human"
                detail[n] = ("%d resolve, %d absent, %d undecidable"
                             % (len(found), len(absent), sum(1 for d in v if d is None)))
        b[k] += 1
        byb[k].append(n)

    tot = len(names)
    print("")
    print("HELD-IDENTIFIER TRIAGE -- %d pages that show a reader nothing but hold ids" % tot)
    print("")
    for k, lab in (("repairable", "held ids resolve and match the topic"),
                   ("no_registration", "held ids do not exist"),
                   ("donor", "held id resolves to a DIFFERENT trial"),
                   ("needs_human", "not placeable")):
        print("   %-46s %5d   %5.1f%%" % (lab, b[k], 100.0 * b[k] / max(1, tot)))
    s = sum(b.values())
    print("   %-46s %5d   == the set" % ("sum", s))
    if s != tot:
        sys.exit("REFUSED: does not close -- %d pages, %d placed." % (tot, s))
    if byb["donor"]:
        print("")
        print("   DONORS HELD BUT NEVER SHOWN -- invisible to a reader and to every")
        print("   reader-facing check, by name:")
        for n in byb["donor"][:20]:
            print("      %-46s %s" % (n[:46], detail[n][:80]))
    T.save(OUT, {"total": tot, "buckets": {k: v for k, v in byb.items()},
                 "detail": detail, "ids": sorted(allids)})
    print("")
    print("The first triage's 630 stands: those pages show a reader no identifier. This is a")
    print("second property of the same pages and both are true at once.")


if __name__ == "__main__":
    main()
