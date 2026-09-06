# -*- coding: utf-8 -*-
"""Every object that runs a search must publish how many records it never retrieved.

THE DEFECT, AND ITS FIRST DIAGNOSIS WAS WRONG. This gate originally refused sglt2-hf on the
grounds that `k_cascade.k_unscreened_remainder` was 0 while its sources summed to 1,402. That
accused the wrong field.

    `k_unscreened_remainder` is a SCREENING remainder -- candidates that ENTERED the cascade
    and went unscreened -- and it is CORRECT on both objects that publish one. sglt2-hf's 0
    is backed by "all 32 screened" and "all 10 screened". early-rhythm-control-af's 88 counts
    trials read by ONE seat, and one seat is not a screen.

    A GATE THAT ACCUSES A CORRECT FIELD IS THE DEFECT CLASS THIS REPOSITORY CATALOGUES, and
    this one did it in the very commit that introduced it.

THE REAL DEFECT WAS A MISSING NUMBER, NOT A WRONG ONE. sglt2-hf's PubMed search returned
1,452 records and retrieved 50. The other 1,402 never entered the cascade at all -- not in
`k0_surfaced`, not in the screening remainder, nowhere. NO OBJECT IN THE CORPUS PUBLISHED HOW
MANY RECORDS A SEARCH RETURNED AND NOBODY RETRIEVED. The page renders "unscreened remainder
0." and contains `1402` zero times, and both statements were true of what the object held.

WHAT THIS REFUSES
    1. an object with recorded sources and NO `search.retrieval_remainder` at all
    2. a published total that does not equal the sum of its per-source rows
    3. `state: PROVED` on an object that has a NOT_RECORDED source
    4. a source whose remainder is derivable from its own numbers and is still not written down

    AN ABSENCE MUST NOT BECOME A PROVEN ZERO. A SUM OVER A SILENT FIELD IS NOT A SMALLER SUM
    -- IT IS NOT A SUM. Rule 3 is the one that enforces it, and it needed a THIRD control,
    because a positive and a negative control both pass a gate that cannot tell the difference.

WHAT THIS DELIBERATELY DOES NOT TOUCH. `reconciliation.gap_stated_plainly` names all 45 of
sglt2-hf's 49 -> 4 SCREENING gap, trial by trial and route by route, and `k_unscreened_
remainder` is left exactly as it is on every object. A gate conflating retrieval with
screening would refuse the best-documented object in the corpus for being well documented.
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
    if isinstance(rem, str) and rem == "NOT_EXECUTED":
        return ("NOT_EXECUTED", None,
                "%s: declared and never searched" % name)
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
    """(verdict, retrieval_total, per_source_rows, reasons).

    CORRECTED 2026-09-04, and the correction is that this gate was naming the wrong field.

    Its first version refused an object because `k_cascade.k_unscreened_remainder` was 0 while
    the sources summed to 1,402. That reading was wrong. `k_unscreened_remainder` is a
    SCREENING remainder -- candidates that entered the cascade and went unscreened -- and it is
    CORRECT on both objects that publish one: sglt2-hf's 0 ("all 32 screened", "all 10
    screened") and early-rhythm-control-af's 88 (read by one seat, and one seat is not a
    screen).

        A GATE THAT ACCUSES A CORRECT FIELD IS THE DEFECT CLASS THIS REPOSITORY CATALOGUES.
        The defect was never a wrong aggregate. It was a MISSING one: no object published how
        many records a search returned and never retrieved.

    So this now checks `search.retrieval_remainder`, written by
    scripts/apply_retrieval_remainder_2026_09_04.py, and refuses:
        1. an object with recorded sources that publishes no retrieval remainder at all
        2. a published total that does not equal the sum of its per-source rows
        3. a PROVED state on an object that has a NOT_RECORDED source
        4. a source whose remainder is derivable and is still not written down
    """
    dbs = ((obj.get("search") or {}).get("databases")) or []
    rows = [per_source(db) for db in dbs if isinstance(db, dict)]
    if not rows:
        return "NO_SOURCES", None, rows, []

    block = (obj.get("search") or {}).get("retrieval_remainder")
    if not isinstance(block, dict):
        return ("REFUSED", None, rows,
                ["records %d source(s) and publishes NO retrieval remainder. How many records "
                 "a search returned and nobody retrieved is not stated anywhere." % len(rows)])

    reasons = []
    # FOUR STATES, because NOT_EXECUTED and NOT_RECORDED are different claims about the world.
    # A declared source that was never searched has NO remainder -- not zero. Reading it as
    # zero would let "we never searched PubMed" stand as "PubMed left nothing unexamined".
    silent = [r for r in rows if r[0] == "NOT_ASSESSABLE"]
    unexecuted = [r for r in rows if r[0] == "NOT_EXECUTED"]
    for state_, rem, detail in rows:
        if state_ == "COMPUTABLE":
            reasons.append("a source does not record its remainder -- %s" % detail)
        elif state_ == "INCONSISTENT":
            reasons.append("a source contradicts itself -- %s" % detail)

    state = block.get("state")
    total = block.get("total")
    summed = sum(r[1] for r in rows if isinstance(r[1], int))
    if silent:
        if state != "NOT_PROVABLE":
            reasons.append(
                "%d source(s) ran and do not state what they returned, so no total is "
                "provable, yet the block claims state=%r. A SUM OVER A SILENT FIELD IS NOT A "
                "SMALLER SUM -- IT IS NOT A SUM." % (len(silent), state))
        if isinstance(total, int):
            reasons.append(
                "a numeric total (%d) is published while %d source(s) are NOT_RECORDED. An "
                "absence must not become a proven zero." % (total, len(silent)))
    elif unexecuted:
        if state != "PROVED_FOR_EXECUTED_SOURCES":
            reasons.append(
                "%d declared source(s) were never executed, so a bare PROVED overstates the "
                "cover, yet the block claims state=%r" % (len(unexecuted), state))
        if not block.get("sources_not_executed"):
            reasons.append("declared sources were never executed and none is NAMED in "
                           "sources_not_executed")
        if isinstance(total, int) and total != summed:
            reasons.append("the published total is %d but the executed sources sum to %d"
                           % (total, summed))
    else:
        if state != "PROVED":
            reasons.append("every source states its remainder, so the total is provable, yet "
                           "the block claims state=%r" % state)
        elif total != summed:
            reasons.append("the published retrieval remainder is %r but the per-source rows "
                           "sum to %d" % (total, summed))

    return ("REFUSED" if reasons else "PROVED"), total, rows, reasons


def controls():
    """A proved retrieval remainder must pass; a missing one must fire.

    POSITIVE  the sglt2-hf SHAPE: sources recording 1,402 unretrieved and NO retrieval
              remainder block. It MUST be refused. A gate that cannot fire on the instance
              that motivated it has not been shown to do anything.
    NEGATIVE  the same sources WITH a correct PROVED block. It MUST NOT be refused -- the
              over-flagging direction, where the gate would punish an object for carrying
              exactly what it was asked to carry.
    THIRD     a silent source with a numeric total published anyway. MUST be refused: this is
              the absence-becomes-a-proven-zero case and neither of the first two catches it.
    """
    srcs = [{"database": "ctgov", "records_returned": 56, "total_count": 56,
             "records_not_retrieved": 0},
            {"database": "pubmed", "records_returned": 50, "total_count": 1452,
             "records_not_retrieved": 1402}]
    bad = {"search": {"databases": srcs}}
    good = {"search": {"databases": srcs, "retrieval_remainder": {
        "state": "PROVED", "total": 1402,
        "by_source": {"ctgov": 0, "pubmed": 1402}}}}
    silent = {"search": {"databases": [
        {"database": "ctgov", "records_returned": 56, "total_count": 56,
         "records_not_retrieved": 0},
        {"database": "pubmed", "records_not_retrieved": "NOT_RECORDED"}],
        "retrieval_remainder": {"state": "PROVED", "total": 0, "by_source": {}}}}
    return check(bad)[0], check(good)[0], check(silent)[0]


def load_baseline():
    if BASELINE.exists():
        return set(json.loads(BASELINE.read_text(encoding="utf-8")).get("apps", []))
    return None


def main(argv):
    pos, neg, silent = controls()
    require_controls(
        "gate_remainder_is_per_source",
        ("1402 unretrieved and NO retrieval remainder block", pos, "REFUSED"),
        ("the same sources WITH a correct PROVED block", neg, "REFUSED"),
    )
    # THE THIRD CONTROL, and it catches what neither of the first two can: a total
    # published over a source that never said what it returned.
    if silent != "REFUSED":
        raise SystemExit(
            "REFUSED: a numeric total published over a NOT_RECORDED source came back "
            "%r, not REFUSED. An absence must not become a proven zero, and this gate "
            "cannot currently tell. NO COUNT IS PRINTED." % silent)
    print("CONTROL (third) gate_remainder_is_per_source: numeric total over a "
          "NOT_RECORDED source -> %r, expected 'REFUSED'" % silent)

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
