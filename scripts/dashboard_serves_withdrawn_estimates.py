#!/usr/bin/env python3
"""THE DASHBOARD SERVES ESTIMATES THE OBJECTS HAVE WITHDRAWN.

SURFACED BY THE CODEX SEAT (openai family) while it was running a different task, and VERIFIED
INDEPENDENTLY HERE before being recorded. A cross-family seat's finding is a lead, not a result.

THE CLASS THIS EXTENDS. Class 23 is "a page served an external benchmark where its own result
belongs", and it was measured over `index.html`'s 522 cards and closed at zero. THAT SWEEP
LOOKED AT ONE SURFACE.

    `dashboard.html` reads `outputs/portfolio_index.json` and renders a "Pooled OR (95% CI)"
    column. That file is a STALE SNAPSHOT. It carries a numeric `pooled_OR` for pages whose SSOT
    object has since WITHDRAWN its estimate -- and for pages that no longer exist as reviews at
    all, because they were retired into another topic hours ago.

A WITHDRAWAL IS THE STRONGEST STATEMENT A REVIEW IN THIS CORPUS CAN MAKE. It is what an object
says when its trials do not share an endpoint, when its comparator is wrong, or when its
headline could not be reproduced. Serving the withdrawn number anyway on an aggregate surface
undoes every one of those decisions at once, for a reader who never opens the page.

WHAT THIS DOES NOT CLAIM
  - NOT that the dashboard numbers were ever wrong when computed. They are a snapshot, and a
    snapshot is not a lie until it is served as current.
  - NOT that regenerating the snapshot is sufficient. A regenerated snapshot goes stale the next
    time an object is withdrawn; the durable fix is for the dashboard to read the objects, or
    for the snapshot to carry the object's own withdrawal state.
  - NOTHING about the 602 rows that are not in `PAGE_MAP.json`. They cannot be checked against
    any object and are counted separately -- never as clean.

USAGE:  python scripts/dashboard_serves_withdrawn_estimates.py
        python scripts/dashboard_serves_withdrawn_estimates.py --selftest
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import retirement as R                                       # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAP = os.path.join(REPO, "outputs", "portfolio_index.json")
PMAP = os.path.join(REPO, "ssot", "PAGE_MAP.json")
DEST = os.path.join(REPO, "evidence", "2026-08-19-batch1",
                    "dashboard_withdrawn_estimates.json")


def classify(page, val, pmap):
    """LIVE / WITHDRAWN / NO_POOL / RETIRED / UNMAPPED for one dashboard row."""
    if page not in pmap:
        return "UNMAPPED", None
    p = os.path.join(REPO, pmap[page].replace("/", os.sep))
    if not os.path.exists(p):
        return "OBJECT_MISSING", None
    try:
        with io.open(p, "r", encoding="utf-8") as fh:
            o = json.load(fh)
    except ValueError:
        return "OBJECT_UNREADABLE", None
    # A RETIRED TOPIC IS ITS OWN STATE. Serving a pooled estimate for a review that no longer
    # exists is worse than serving a stale one for a review that does.
    # RETIREMENT IS DECIDED BY `state` ALONE -- see scripts/retirement.py. This test read
    # `state == RETIRED **and** o.get("absorbed_by")`, which made the successor field a
    # PRECONDITION for seeing a tombstone at all. A topic retired by SPLIT records
    # `split_into`, so it was not recognised as retired and fell through to the live path.
    if R.is_retired(o):
        return "RETIRED", R.successor_label(o)
    res = (o.get("results") or {}).get("by_outcome") or {}
    live = any(isinstance(b, dict) and (b.get("pooled") or {}).get("point") is not None
               and not (b.get("pooled") or {}).get("withdrawn") for b in res.values())
    withdrawn = any(isinstance(b, dict) and (b.get("pooled") or {}).get("withdrawn")
                    for b in res.values())
    if live:
        return "LIVE", None
    if withdrawn:
        return "WITHDRAWN", None
    return "NO_POOL", None


def run():
    with io.open(SNAP, "r", encoding="utf-8") as fh:
        snap = json.load(fh)
    rows = snap if isinstance(snap, list) else (snap.get("rows") or snap.get("apps") or [])
    with io.open(PMAP, "r", encoding="utf-8") as fh:
        pmap = json.load(fh)

    tally, detail = {}, []
    numeric = 0
    for r in rows:
        if not isinstance(r, dict):
            continue
        val = r.get("pooled_OR")
        if not isinstance(val, (int, float)):
            continue
        numeric += 1
        page = r.get("file")
        state, extra = classify(page, val, pmap)
        tally[state] = tally.get(state, 0) + 1
        if state in ("WITHDRAWN", "NO_POOL", "RETIRED"):
            detail.append({"page": page, "pooled_OR": val, "object_state": state,
                           "absorbed_by": extra,
                           "ci": [r.get("ci_low"), r.get("ci_high")], "k": r.get("k")})

    served_wrongly = sum(tally.get(s, 0) for s in ("WITHDRAWN", "NO_POOL", "RETIRED"))
    out = {
        "computed_utc": "2026-08-19",
        "surfaced_by": ("the Codex seat (openai family), while running a different task. "
                        "VERIFIED INDEPENDENTLY HERE before being recorded -- a cross-family "
                        "seat's finding is a lead, not a result."),
        "surface": "dashboard.html, via outputs/portfolio_index.json",
        "rows_in_snapshot": len(rows),
        "rows_with_a_numeric_pooled_OR": numeric,
        "by_object_state": tally,
        "SERVED_WHERE_THE_OBJECT_DOES_NOT_SUPPORT_IT": served_wrongly,
        "what_each_state_means": {
            "WITHDRAWN": "the object has WITHDRAWN its estimate and the dashboard shows a number",
            "NO_POOL": "the object carries no pooled value at all",
            "RETIRED": "the topic no longer exists as a review -- it was absorbed into another",
            "LIVE": "the object has a live pooled estimate; the row may still be STALE and this "
                    "check does not compare the values",
            "UNMAPPED": "the row names a page with no SSOT object. NOT CHECKABLE, never clean -- "
                        "and it is the largest group by far, so any count here is a FLOOR",
        },
        "what_this_check_does_NOT_do": (
            "It does not compare the LIVE rows' numbers against their objects. A row classified "
            "LIVE may still be stale by value. This check answers only the sharper question: "
            "does the dashboard show a pooled estimate where the object says there is none?"),
        "detail": sorted(detail, key=lambda d: (d["object_state"], d["page"])),
    }
    with io.open(DEST, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, indent=1, ensure_ascii=False))

    print("DASHBOARD ROWS WITH A NUMERIC pooled_OR: %d of %d\n" % (numeric, len(rows)))
    for k in sorted(tally, key=lambda x: -tally[x]):
        print("   %-18s %4d" % (k, tally[k]))
    print("\n   SERVED WHERE THE OBJECT DOES NOT SUPPORT IT: %d" % served_wrongly)
    print("\n   the retired ones are the sharpest -- these reviews no longer exist:")
    for d in out["detail"]:
        if d["object_state"] == "RETIRED":
            print("      %-46s pooled_OR %-10s  absorbed by %s"
                  % (d["page"], d["pooled_OR"], d["absorbed_by"]))
    print("\nwrote %s" % os.path.relpath(DEST, REPO))
    return 1 if served_wrongly else 0


def selftest():
    fails = []

    def ck(name, got, want):
        ok = got == want
        print("  %-64s %s  %r" % (name, "ok" if ok else "FAIL", got))
        if not ok:
            fails.append(name)

    print("1. THE FIVE STATES ARE DISTINGUISHED, and none collapses into another:")
    pm = {"X.html": "ssot/nope/nope.json"}
    ck("a page with no object is UNMAPPED", classify("Q.html", 1.0, pm)[0], "UNMAPPED")
    ck("a mapped object that is missing on disk is its own state",
       classify("X.html", 1.0, pm)[0], "OBJECT_MISSING")

    print("\n2. AND ON REAL OBJECTS IN THIS REPOSITORY:")
    with io.open(PMAP, "r", encoding="utf-8") as fh:
        pmap = json.load(fh)
    ck("a retired topic classifies RETIRED",
       classify("OMECAMTIV_HF_AUTO_FULL_REVIEW.html", 1.0, pmap)[0], "RETIRED")
    ck("a withdrawn topic classifies WITHDRAWN",
       classify("COLCHICINE_CVD_REVIEW.html", 1.0, pmap)[0], "WITHDRAWN")
    ck("a live pool classifies LIVE",
       classify("SGLT2_HF_REVIEW.html", 1.0, pmap)[0], "LIVE")

    print("\n3. THE LIVE RUN -- and a zero here would mean the snapshot had no numbers at all:")
    rc = run()
    with io.open(DEST, "r", encoding="utf-8") as fh:
        out = json.load(fh)
    ck("the snapshot carries numeric pooled values to check",
       out["rows_with_a_numeric_pooled_OR"] > 0, True)
    ck("and the check returns non-zero while any is served wrongly",
       rc == (1 if out["SERVED_WHERE_THE_OBJECT_DOES_NOT_SUPPORT_IT"] else 0), True)

    print("\n%s" % ("SELFTEST FAILED: %s" % fails if fails else "SELFTEST PASSED"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(selftest() if "--selftest" in sys.argv else run())
