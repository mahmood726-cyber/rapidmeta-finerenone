#!/usr/bin/env python3
"""EVERY SEARCH WHOSE COMPLETENESS RESTED ON A NULL CURSOR, RE-CHECKED AGAINST ITS OWN TOTAL.

WHY. DEFECT-REGISTRY class 20 established that a LIVE `next_page_token` means a search is
incomplete. Every search recorded since then relied on the CONVERSE -- that a NULL token means
it is COMPLETE -- and the converse was never tested, because on `colchicine-cvd-review` both
proofs agreed: 100 + 37 = 137 == totalCount, cursor null.

    ON `acs-antiplatelet-review` THEY DISAGREED. 100 + 100 + 3 = 203 records with the cursor
    NULL, against a reported totalCount of 430. **227 records the pagination never returned,
    while the cursor said it was done.**

    THE PROOF IS THE SUM RECONCILED AGAINST totalCount. THE NULL CURSOR IS CORROBORATION.

So every search row in this corpus has to be asked which evidence it actually rests on, and any
that rests on the cursor ALONE is unproven -- not wrong, UNPROVEN -- and every topic built on
one is affected until it is re-checked.

THE FOUR STATES, and they are never summed
    RECONCILES              returned == total. The proof holds regardless of the cursor.
    SHORTFALL_DECLARED      returned < total AND the row says so. Legitimate (class 20).
    SHORTFALL_UNDECLARED    returned < total and the row does not say so. A DEFECT.
    CURSOR_ONLY             the row's completeness evidence is a null/absent cursor and it
                            states NO total to reconcile against. **UNPROVEN, never clean.**

WHAT THIS CANNOT DO
    It cannot re-run the searches. It reads what each row SAYS about itself. A row claiming
    `returned == total` where neither number is true passes here and this file says so.

USAGE:  python scripts/audit_null_cursor_evidence.py
        python scripts/audit_null_cursor_evidence.py --selftest
"""
import glob
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(REPO, "evidence", "2026-08-19-batch1", "null_cursor_evidence_audit.json")

# THE VOCABULARY IS NOT ONE VOCABULARY, and assuming it was produced five false
# NOT_ASSESSABLEs on the first run -- which is class 25 again: a lookup that does not find the
# field is indistinguishable from a field that is not there. `arni-hfref` spells them
# `hit_count` and `records_retrieved`; two colchicine records nest theirs one level down under
# `counts` and `PAGINATION_SHORTFALL_DECLARED`. None of those was a corpus gap; all five were
# this file failing to look.
RET = ("records_returned", "returned", "records_returned_total", "count",
       "records_retrieved", "total_listed_here")
TOT = ("total_reported", "total_count", "totalCount", "total", "hit_count",
       "total_reported_by_pubmed", "total_reported_by_the_registry",
       "total_count_reported_by_pubmed")
DECL = ("unexamined", "not excluded", "shortfall", "declared", "the other")

RECONCILES = "RECONCILES"
DECLARED = "SHORTFALL_DECLARED"
UNDECLARED = "SHORTFALL_UNDECLARED"
CURSOR_ONLY = "CURSOR_ONLY_UNPROVEN"
NOT_EXECUTED = "NOT_EXECUTED"
NA = "NOT_ASSESSABLE"


def _num(d, keys):
    """The first integer under any of `keys`, looking ONE LEVEL DOWN as well as at the top.

    Nested because real records put them there: `colchicine_surfaced_137.json` keeps its totals
    under `counts`, and the 100-of-523 PubMed record under `PAGINATION_SHORTFALL_DECLARED`. A
    top-level-only lookup reported both as stating no counts at all.
    """
    for k in keys:
        v = d.get(k)
        if isinstance(v, int) and not isinstance(v, bool):
            return v
    for v in d.values():
        if isinstance(v, dict):
            for k in keys:
                x = v.get(k)
                if isinstance(x, int) and not isinstance(x, bool):
                    return x
    # A `pages` list carries per-page counts; the row's returned total is their sum and its
    # total is whichever page stated one.
    pages = d.get("pages")
    if isinstance(pages, list) and pages:
        vals = [p[k] for p in pages if isinstance(p, dict)
                for k in keys if isinstance(p.get(k), int) and not isinstance(p.get(k), bool)]
        if vals:
            return sum(vals) if keys is RET else vals[0]
    return None


def classify_row(row):
    """(state, detail) for one database row of a search block."""
    blob = json.dumps(row, ensure_ascii=False).lower()
    tool = str(row.get("tool") or "")
    if "not executed" in tool.lower() or "NOT EXECUTED" in str(row.get("query_as_executed") or ""):
        return NOT_EXECUTED, "the row records that this database was not searched"
    ret, tot = _num(row, RET), _num(row, TOT)
    if ret is None and tot is None:
        # A NOT_ASSESSABLE THAT DOES NOT SAY WHAT IT LOOKED FOR IS NOT REFUTABLE, and this file
        # produced five of them on its first run that were all its own failure to look. The
        # remedy is the one that works on every form of this class: report the denominator.
        return NA, ("the row states neither a returned count nor a total under any key this "
                    "audit knows. KEYS PRESENT: %s. Looked for returned in %s and total in %s."
                    % (sorted(row.keys())[:14], list(RET), list(TOT)))
    if tot is None:
        # THE CASE THIS FILE EXISTS FOR. No total to reconcile against, so whatever the row says
        # about its cursor, its completeness is unproven.
        return CURSOR_ONLY, ("the row states returned=%s and NO TOTAL. Its completeness rests "
                             "on the cursor alone, which is corroboration and not a proof."
                             % ret)
    if ret is None:
        return NA, "the row states a total and no returned count"
    if ret == tot:
        return RECONCILES, "returned %d == total %d" % (ret, tot)
    if any(d in blob for d in DECL):
        return DECLARED, ("returned %d of %d and the row DECLARES the shortfall of %d"
                          % (ret, tot, tot - ret))
    return UNDECLARED, ("returned %d of %d and the row does NOT declare the shortfall of %d"
                        % (ret, tot, tot - ret))


def collect():
    rows = []
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        try:
            with io.open(p, "r", encoding="utf-8") as fh:
                o = json.load(fh)
        except (OSError, ValueError):
            continue
        if str(o.get("state") or "").upper() == "RETIRED":
            continue
        s = o.get("search") or {}
        for db in (s.get("databases") or []):
            if not isinstance(db, dict):
                continue
            st, why = classify_row(db)
            rows.append({"where": "object", "topic": o.get("app_id"),
                         "database": db.get("database"), "state": st, "why": why,
                         "built_page": True})
    for p in sorted(glob.glob(os.path.join(REPO, "evidence", "**", "*.json"), recursive=True)):
        try:
            with io.open(p, "r", encoding="utf-8") as fh:
                d = json.load(fh)
        except (OSError, ValueError):
            continue
        if not isinstance(d, dict) or "query_as_executed" not in d:
            continue
        st, why = classify_row(d)
        rows.append({"where": "evidence", "topic": d.get("topic"),
                     "database": d.get("database"),
                     "file": os.path.relpath(p, REPO), "state": st, "why": why,
                     "built_page": False})
    return rows


def run():
    rows = collect()
    tally = {}
    for r in rows:
        tally[r["state"]] = tally.get(r["state"], 0) + 1
    unproven = [r for r in rows if r["state"] == CURSOR_ONLY]
    bad = [r for r in rows if r["state"] == UNDECLARED]
    affected = sorted({r["topic"] for r in unproven + bad if r.get("built_page")})

    out = {
        "audited_utc": "2026-08-19",
        "why": ("Class 20 established that a LIVE cursor means incomplete. Every search since "
                "relied on the CONVERSE -- that a NULL cursor means complete -- and it was "
                "never tested because on colchicine both proofs agreed. On acs-antiplatelet "
                "they disagreed: 203 returned with a null cursor against a reported 430."),
        "the_proof_that_holds": ("the sum across pages reconciled against totalCount. The null "
                                 "cursor is corroboration and never the proof."),
        "rows_examined": len(rows),
        "by_state": tally,
        "UNPROVEN_rows": len(unproven),
        "UNDECLARED_shortfalls": len(bad),
        "TOPICS_WITH_A_BUILT_PAGE_RESTING_ON_AN_UNPROVEN_ROW": affected,
        "what_this_cannot_do": ("It cannot re-run the searches. It reads what each row SAYS "
                                "about itself; a row whose stated numbers are both untrue "
                                "passes here."),
        "rows": rows,
    }
    with io.open(DEST, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, indent=1, ensure_ascii=False))

    print("SEARCH ROWS EXAMINED: %d\n" % len(rows))
    for k in sorted(tally, key=lambda x: -tally[x]):
        print("   %-24s %3d" % (k, tally[k]))
    print("\n   UNPROVEN (cursor-only, no total to reconcile): %d" % len(unproven))
    for r in unproven:
        print("      %-42s %-38s %s" % (r.get("topic"), str(r.get("database"))[:38],
                                        "BUILT PAGE" if r.get("built_page") else "evidence only"))
    print("\n   UNDECLARED SHORTFALLS: %d" % len(bad))
    for r in bad:
        print("      %-42s %s" % (r.get("topic"), r["why"]))
    print("\n   TOPICS WITH A BUILT PAGE RESTING ON AN UNPROVEN ROW: %d" % len(affected))
    for t in affected:
        print("      %s" % t)
    print("\nwrote %s" % os.path.relpath(DEST, REPO))
    return 1 if (bad or affected) else 0


def selftest():
    fails = []

    def ck(name, got, want):
        ok = got == want
        print("  %-66s %s  %r" % (name, "ok" if ok else "FAIL", got))
        if not ok:
            fails.append(name)

    print("1. THE FOUR STATES, and none collapses into another:")
    ck("returned == total reconciles",
       classify_row({"records_returned": 137, "total_reported": 137})[0], RECONCILES)
    ck("a declared shortfall is legitimate",
       classify_row({"records_returned": 50, "total_reported": 439,
                     "what_is_unexamined": "THE OTHER 389 ARE UNEXAMINED, NOT EXCLUDED"})[0],
       DECLARED)
    ck("an undeclared shortfall is a defect",
       classify_row({"records_returned": 50, "total_reported": 439})[0], UNDECLARED)
    ck("a row with NO total is CURSOR_ONLY, never clean",
       classify_row({"records_returned": 57,
                     "pagination_verified": "next_page_token null"})[0], CURSOR_ONLY)

    print("\n2. AND A NOT-EXECUTED DATABASE IS ITS OWN STATE, never a shortfall:")
    ck("a row saying NOT EXECUTED",
       classify_row({"tool": "NOT EXECUTED", "records_returned": None})[0], NOT_EXECUTED)

    print("\n3. A ROW STATING NEITHER NUMBER IS NOT_ASSESSABLE:")
    ck("no counts at all", classify_row({"database": "PubMed"})[0], NA)

    print("\n4. THE LIVE CORPUS -- a zero here would make the audit meaningless:")
    rows = collect()
    ck("search rows were found to classify", len(rows) > 20, True)
    run()

    print("\n%s" % ("SELFTEST FAILED: %s" % fails if fails else "SELFTEST PASSED"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(selftest() if "--selftest" in sys.argv else run())
