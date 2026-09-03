# -*- coding: utf-8 -*-
"""A remainder of 0 must be PROVED from per-source arithmetic, with every source named.

THE DEFECT, MEASURED ON ssot/sglt2-hf/sglt2-hf.json AND ON THE PAGE IT SERVES.

    search.databases[0]  ClinicalTrials.gov q1   returned 23    total 23     not_retrieved ABSENT
    search.databases[1]  ClinicalTrials.gov q2   returned 56    total 56     not_retrieved ABSENT
    search.databases[2]  PubMed                  returned 50    total 1452   not_retrieved 1402
    k_cascade.k_unscreened_remainder                                                          0
    prisma_flow.reconciliation.arithmetic  "56 identified = 49 + 1 + 6 + 0"

The per-source record is HONEST -- it says in terms that "the other 1402 are UNEXAMINED, not
excluded". The AGGREGATE destroys it. The reconciliation balances the 56 that ClinicalTrials
returned and nothing else, and the single number it publishes is 0. SGLT2_HF_REVIEW.html then
renders "unscreened remainder 0." and contains 1452 once and 1402 ZERO TIMES.

    A ZERO THAT IS TRUE OF ONE CASCADE, SERVED AS THOUGH IT COVERED EVERY SOURCE. One number
    cannot be right for more than one cascade, and a reader has no way to see which cascade
    it belongs to.

AND THE TWO SILENCES. The ClinicalTrials rows have no remainder field at all. Their remainder
genuinely is zero -- returned equals total -- but the object does not SAY zero, it says
nothing, and an aggregate assembled from two silences and one honest 1402 came out 0. So this
gate demands the number be present, not merely correct: ABSENT and 0 are different claims,
and only one of them can be checked.

WHAT THIS REFUSES
    1. an aggregate remainder that does not equal the sum of the per-source remainders
    2. an aggregate remainder of 0 where any source has a non-zero remainder
    3. a source whose remainder can be computed (total and returned are both present) but
       which does not record it

WHAT THIS DELIBERATELY DOES NOT TOUCH -- and it is the behaviour we want, not a defect.
`reconciliation.gap_stated_plainly` names all 45 of the 49 -> 4 screening gap, trial by trial
and route by route. That is a SCREENING cascade, downstream of retrieval, and it is exactly
what a reader needs. This gate is about the RETRIEVAL remainder: how many records the
searches returned that nobody has looked at. A gate that conflated the two would refuse the
best-documented object in the corpus for being well documented.
"""
from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from instrument_controls import require_controls  # noqa: E402

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
PAGE_MAP = ROOT / "ssot" / "PAGE_MAP.json"

TOTAL_KEYS = ("total_count", "total_reported", "totalCount", "total")
RETURNED_KEYS = ("records_returned", "returned", "records_returned_total", "count")
REMAINDER_KEYS = ("records_not_retrieved", "not_retrieved", "unretrieved", "remainder")
AGGREGATE_KEYS = ("k_unscreened_remainder", "unscreened_remainder")

# The baseline of objects already carrying this defect. RATCHET, NOT RETROFIT: repairing one
# means editing a store object that serves a page, which needs the before/after page protocol
# and is not a rename. What this refuses is a NEW one.
BASELINE = ROOT / "scripts" / "baselines" / "remainder_per_source_baseline.json"


def _first(d, keys):
    for k in keys:
        if k in d and d[k] is not None:
            return k, d[k]
    return None, None


def per_source(db):
    """(state, remainder, detail) for one recorded database.

    States are named for what is KNOWN, not for what is missing: RECORDED when the object
    says its remainder, COMPUTABLE when total and returned are both present so the remainder
    follows by subtraction but is not written down, NOT_ASSESSABLE when neither is available.
    """
    tkey, total = _first(db, TOTAL_KEYS)
    rkey, returned = _first(db, RETURNED_KEYS)
    mkey, rem = _first(db, REMAINDER_KEYS)
    name = str(db.get("database") or db.get("tool") or "<unnamed source>")[:58]
    if isinstance(rem, int):
        if isinstance(total, int) and isinstance(returned, int) and total - returned != rem:
            return ("INCONSISTENT", rem,
                    "%s: records %s=%d but %s-%s = %d"
                    % (name, mkey, rem, tkey, rkey, total - returned))
        return ("RECORDED", rem, name)
    if isinstance(total, int) and isinstance(returned, int):
        return ("COMPUTABLE", total - returned,
                "%s: %s=%d and %s=%d give a remainder of %d, and the object does not record it"
                % (name, tkey, total, rkey, returned, total - returned))
    return ("NOT_ASSESSABLE", None,
            "%s: neither a remainder nor a total/returned pair" % name)


def check(obj):
    """(verdict, aggregate, per_source_rows, reasons)."""
    dbs = ((obj.get("search") or {}).get("databases")) or []
    rows = [per_source(db) for db in dbs if isinstance(db, dict)]

    agg_key, agg = None, None
    for holder in ("k_cascade", "prisma_flow"):
        blk = obj.get(holder)
        if isinstance(blk, dict):
            k, v = _first(blk, AGGREGATE_KEYS)
            if isinstance(v, int):
                agg_key, agg = "%s.%s" % (holder, k), v
                break
    if agg is None:
        return "NO_AGGREGATE", None, rows, []
    if not rows:
        return ("AGGREGATE_WITHOUT_SOURCES", agg, rows,
                ["an aggregate remainder of %d is published and NO source is recorded, so "
                 "it cannot be proved from anything" % agg])

    reasons = []
    known = [r for r in rows if r[1] is not None]
    unknown = [r for r in rows if r[1] is None]
    total_rem = sum(r[1] for r in known)

    for state, rem, detail in rows:
        if state == "COMPUTABLE":
            reasons.append("a source does not record its remainder -- %s" % detail)
        elif state == "INCONSISTENT":
            reasons.append("a source contradicts itself -- %s" % detail)
        elif state == "NOT_ASSESSABLE":
            reasons.append("a source cannot be assessed -- %s" % detail)

    if agg == 0 and total_rem > 0:
        reasons.insert(0, "%s is 0 while the sources sum to %d unexamined record(s). A zero "
                          "scoped to one cascade is being served as though it covered every "
                          "source." % (agg_key, total_rem))
    elif agg != total_rem and not unknown:
        reasons.insert(0, "%s is %d but the per-source remainders sum to %d"
                       % (agg_key, agg, total_rem))

    return ("REFUSED" if reasons else "PROVED"), agg, rows, reasons


def controls():
    """A proved zero must pass; the real defect must fire.

    POSITIVE  the sglt2-hf SHAPE, rebuilt synthetically: one source with 1402 unexamined and
              an aggregate of 0. It MUST be refused. A gate that cannot fire on the instance
              that motivated it has not been shown to do anything.
    NEGATIVE  every source records a remainder of 0 and the aggregate is 0. It MUST NOT be
              refused -- this is the over-flagging direction, where the gate would punish an
              object for being complete.
    """
    bad = {"search": {"databases": [
        {"database": "ctgov", "records_returned": 56, "total_count": 56,
         "records_not_retrieved": 0},
        {"database": "pubmed", "records_returned": 50, "total_count": 1452,
         "records_not_retrieved": 1402}]},
        "k_cascade": {"k_unscreened_remainder": 0}}
    good = {"search": {"databases": [
        {"database": "ctgov", "records_returned": 56, "total_count": 56,
         "records_not_retrieved": 0},
        {"database": "pubmed", "records_returned": 1452, "total_count": 1452,
         "records_not_retrieved": 0}]},
        "k_cascade": {"k_unscreened_remainder": 0}}
    return check(bad)[0], check(good)[0]


def load_baseline():
    if BASELINE.exists():
        return set(json.loads(BASELINE.read_text(encoding="utf-8")).get("apps", []))
    return None


def main(argv):
    pos, neg = controls()
    require_controls(
        "gate_remainder_is_per_source",
        ("synthetic object, 1402 unexamined and an aggregate of 0", pos, "REFUSED"),
        ("synthetic object, every source records 0 and the aggregate is 0", neg, "REFUSED"),
    )

    pm = json.loads(PAGE_MAP.read_text(encoding="utf-8"))
    offenders, proved, no_agg, seen = [], [], [], 0
    for page, rel in sorted(pm.items()):
        p = ROOT / rel
        if not p.exists():
            continue
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        seen += 1
        verdict, agg, rows, reasons = check(obj)
        app = obj.get("app_id") or Path(rel).stem
        if verdict == "REFUSED":
            offenders.append((app, page, agg, rows, reasons))
        elif verdict == "PROVED":
            proved.append(app)
        else:
            no_agg.append(app)

    print("OBJECTS READ                       %d of %d PAGE_MAP entries" % (seen, len(pm)))
    print("  publish an aggregate remainder   %d" % (len(offenders) + len(proved)))
    print("    PROVED from per-source rows    %d" % len(proved))
    print("    REFUSED                        %d" % len(offenders))
    print("  publish none                     %d  -- NOT the same as a remainder of zero"
          % len(no_agg))

    if not (offenders or proved):
        print("")
        print("NOT_ASSESSABLE: no object in PAGE_MAP publishes an aggregate remainder at all, "
              "so this gate reached none of the cases it was built for. That is a broken "
              "instrument, not a clean corpus.")
        return 2

    baseline = load_baseline()
    if baseline is None:
        print("")
        print("NO BASELINE FILE. Nothing can be called NEW without one, so this run reports "
              "and does not refuse. Write one with --write-baseline.")
        for app, page, agg, rows, reasons in offenders:
            print("  %-26s aggregate=%s" % (app, agg))
            for r in reasons:
                print("      %s" % r)
        return 0

    new = [o for o in offenders if o[0] not in baseline]
    still = [o for o in offenders if o[0] in baseline]
    print("  baselined and still offending    %d  -- OWED, not cleared by being listed"
          % len(still))
    for app, page, agg, rows, reasons in offenders:
        mark = "NEW" if app not in baseline else "owed"
        print("")
        print("  [%s] %-24s %s   aggregate=%s" % (mark, app, page, agg))
        for state, rem, detail in rows:
            print("        %-14s remainder=%-6s %s" % (state, rem, detail[:74]))
        for r in reasons:
            print("      -> %s" % r)

    if new:
        print("")
        print("REFUSED: %d object(s) newly publish a remainder that is not proved from their "
              "own per-source arithmetic." % len(new))
        return 1
    print("")
    print("NO OBJECT NEWLY PUBLISHES AN UNPROVED REMAINDER.")
    return 0


if __name__ == "__main__":
    if "--write-baseline" in sys.argv:
        pm = json.loads(PAGE_MAP.read_text(encoding="utf-8"))
        bad = []
        for page, rel in sorted(pm.items()):
            p = ROOT / rel
            if not p.exists():
                continue
            try:
                obj = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if check(obj)[0] == "REFUSED":
                bad.append(obj.get("app_id") or Path(rel).stem)
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps({
            "_what": "objects publishing an aggregate remainder not proved per source",
            "_owed": ("NOT absolved by being listed. Repairing one means editing a store "
                      "object that serves a page, which needs the before/after page "
                      "protocol -- it is not a rename."),
            "_generated_by": "scripts/gate_remainder_is_per_source_2026_09_04.py "
                             "--write-baseline",
            "count": len(bad), "apps": sorted(set(bad))}, indent=2) + "\n",
            encoding="utf-8")
        print("wrote %s with %d app(s)" % (BASELINE, len(set(bad))))
        sys.exit(0)
    sys.exit(main(sys.argv))
