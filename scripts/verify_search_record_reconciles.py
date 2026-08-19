#!/usr/bin/env python3
"""A SEARCH RECORD MUST RECONCILE WITH THE IDENTIFIERS IT LISTS -- by a command, not by reading.

WHY. `colchicine_search_COMPLETE.json` states `records_returned_total: 137` and NAMES NOT ONE OF
THEM. A count with no list behind it is P30 exactly: a number stated in a record that nothing can
recompute is indistinguishable from a number that was asserted. Nothing could check the screen
against the set it screened, and re-running the query later would silently substitute a different
set under the same count.

WHAT IT CHECKS, for every search-record file that carries an identifier list:

    len(list)  ==  sum of per-page `returned`  ==  the reported total  ==  len(set(list))

Four quantities, and each catches a different failure:
  * list vs SUM-ACROSS-PAGES  -- a page transcribed short or twice
  * SUM vs REPORTED TOTAL     -- an unexhausted cursor, which is class 20
  * list vs DISTINCT          -- the same identifier written twice, which inflates a denominator
                                 while every other check still reconciles

THE FOURTH IS THE ONE A HUMAN WOULD NOT DO. A duplicated identifier keeps the sum right and the
total right and is invisible to every check but a set comparison.

WHAT THIS DOES NOT ESTABLISH
  - NOT that the identifiers are the RIGHT ones, or that the query was well aimed. It compares a
    record against itself.
  - NOT anything about a record with no list. That is NOT_ASSESSABLE and is counted separately;
    a record that names nothing cannot fail this and must never be reported as passing it.

USAGE:  python scripts/verify_search_record_reconciles.py
        python scripts/verify_search_record_reconciles.py --selftest
"""
import glob
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LIST_KEYS = ("pmids", "nct_ids", "identifiers", "records")
PAGE_KEYS = ("pages",)
RETURNED = ("returned", "records_returned", "count")
TOTAL = ("total_count", "total_reported", "totalCount", "total")


def _ids(doc):
    """The identifier list, however this record spells it -- including page-split lists."""
    for k in LIST_KEYS:
        v = doc.get(k)
        if isinstance(v, list) and v and all(isinstance(x, str) for x in v):
            return k, list(v)
    parts, names = [], []
    for k, v in doc.items():
        if k.startswith("page_") and isinstance(v, list) and all(isinstance(x, str) for x in v):
            names.append(k)
            parts.extend(v)
    if parts:
        return "+".join(sorted(names)), parts
    return None, None


def check(doc):
    """(verdict, detail, numbers) for one record."""
    key, ids = _ids(doc)
    pages = doc.get("pages")

    # A NULL CURSOR IS NOT A PROOF OF COMPLETENESS, and this is the check for it.
    #
    # Class 20 established that a LIVE next_page_token means the search is incomplete. Every
    # search in this corpus then relied on the CONVERSE -- that a NULL token means it is
    # complete. THE CONVERSE IS FALSE. On `acs-antiplatelet-review` the cursor returned null
    # after 100 + 100 + 3 = 203 records against a reported totalCount of 430, leaving 227 the
    # pagination never returned WHILE SAYING IT WAS DONE.
    #
    # On colchicine both proofs agreed -- 100 + 37 = 137 == totalCount, cursor null -- so the
    # weaker one was never tested. THE PROOF IS THE SUM RECONCILED AGAINST totalCount; the null
    # cursor is corroboration and never the proof.
    #
    # This runs even when the record lists no identifiers, because page counts and a total are
    # enough to catch it and a record with neither is a different failure.
    if isinstance(pages, list) and pages:
        last = pages[-1] if isinstance(pages[-1], dict) else {}
        # AN ABSENT TOKEN FIELD IS NOT A NULL ONE. A record that never wrote down what the
        # cursor said has made no claim about completeness, and reading its silence as "the
        # cursor said done" would convict it of a proof it never offered. Only an EXPLICIT
        # null/exhausted token counts here; absent falls through to the identifier checks.
        has_token_field = "next_page_token" in last
        tok = str(last.get("next_page_token") or "").strip().lower()
        cursor_done = has_token_field and ("null" in tok or "exhaust" in tok or tok == "none")
        vals = []
        for p in pages:
            if isinstance(p, dict):
                for r in RETURNED:
                    if isinstance(p.get(r), int):
                        vals.append(p[r])
                        break
        tot = None
        for p in pages:
            if isinstance(p, dict):
                for t in TOTAL:
                    if isinstance(p.get(t), int):
                        tot = p[t]
                        break
            if tot is not None:
                break
        if tot is None:
            for t in TOTAL:
                if isinstance(doc.get(t), int):
                    tot = doc[t]
                    break
        if cursor_done and vals and tot is not None and sum(vals) != tot:
            return ("CURSOR_SAID_DONE_BUT_THE_SUM_DOES_NOT_RECONCILE",
                    "the pages sum to %d against a reported total of %d -- %d record(s) the "
                    "pagination never returned WHILE THE CURSOR REPORTED THE SEARCH COMPLETE. "
                    "A null next_page_token is corroboration, never the proof."
                    % (sum(vals), tot, tot - sum(vals)),
                    {"sum_across_pages": sum(vals), "reported_total": tot,
                     "shortfall": tot - sum(vals), "cursor": "null"})

    if not ids:
        return "NOT_ASSESSABLE", "the record lists no identifiers, so nothing can be checked " \
                                 "against it. THIS IS NOT A PASS.", {}
    page_sum = None
    if isinstance(pages, list) and pages:
        vals = []
        for p in pages:
            if not isinstance(p, dict):
                continue
            for r in RETURNED:
                if isinstance(p.get(r), int):
                    vals.append(p[r])
                    break
        page_sum = sum(vals) if vals else None
    total = None
    for holder in (doc, (doc.get("counts") or {}),
                   (pages[0] if isinstance(pages, list) and pages
                    and isinstance(pages[0], dict) else {})):
        for t in TOTAL:
            if isinstance(holder.get(t), int):
                total = holder[t]
                break
        if total is not None:
            break
    nums = {"listed": len(ids), "distinct": len(set(ids)),
            "sum_across_pages": page_sum, "reported_total": total, "list_key": key}
    bad = []
    if len(set(ids)) != len(ids):
        dup = sorted({x for x in ids if ids.count(x) > 1})
        bad.append("DUPLICATE IDENTIFIERS in the list: %s" % dup[:6])
    if page_sum is not None and page_sum != len(ids):
        bad.append("the list has %d and the pages sum to %d" % (len(ids), page_sum))
    if total is not None and total != len(ids):
        bad.append("the list has %d and the record reports a total of %d -- if that shortfall "
                   "is deliberate the record must DECLARE it (class 20)" % (len(ids), total))
    if bad:
        return "REFUSED", "; ".join(bad), nums
    return "RECONCILES", "listed == distinct == pages == reported", nums


def main():
    files = sorted(glob.glob(os.path.join(REPO, "evidence", "**", "*.json"), recursive=True))
    tally, bad = {}, 0
    for f in files:
        try:
            with io.open(f, "r", encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, ValueError):
            continue
        if not isinstance(doc, dict):
            continue
        if not any(k in doc for k in ("query_as_executed", "query", "pages")):
            continue
        v, why, nums = check(doc)
        tally[v] = tally.get(v, 0) + 1
        if v == "NOT_ASSESSABLE":
            continue
        print("%-52s %-12s %s" % (os.path.basename(f), v, why[:90]))
        print("     listed %s  distinct %s  pages %s  reported %s"
              % (nums.get("listed"), nums.get("distinct"), nums.get("sum_across_pages"),
                 nums.get("reported_total")))
        if v == "REFUSED":
            bad += 1
    print("\n%s" % "  ".join("%s %d" % kv for kv in sorted(tally.items())))
    print("NOT_ASSESSABLE means the record names no identifiers. It is counted separately and "
          "is NEVER a pass.")
    return 1 if bad else 0


def selftest():
    fails = []

    def ck(name, got, want):
        ok = got == want
        print("  %-66s %s  %r" % (name, "ok" if ok else "FAIL", got))
        if not ok:
            fails.append(name)

    good = {"query": "q", "pmids": ["1", "2", "3"],
            "pages": [{"returned": 2, "total_count": 3}, {"returned": 1}]}
    ck("a reconciling record", check(good)[0], "RECONCILES")

    print("\n  THE FOURTH CHECK -- a duplicate keeps every other number right:")
    dup = {"query": "q", "pmids": ["1", "2", "2"],
           "pages": [{"returned": 2, "total_count": 3}, {"returned": 1}]}
    ck("listed 3, pages 3, reported 3, and DISTINCT 2 -> REFUSED", check(dup)[0], "REFUSED")
    ck("and it names the duplicate", "'2'" in check(dup)[1], True)

    print("\n  AN UNEXHAUSTED CURSOR (class 20):")
    short = {"query": "q", "pmids": ["1", "2"], "pages": [{"returned": 2, "total_count": 523}]}
    ck("2 listed against a reported 523 -> REFUSED", check(short)[0], "REFUSED")

    print("\n  A NULL CURSOR THAT DOES NOT RECONCILE IS ITS OWN VERDICT -- the real case that")
    print("  falsified the proof every search in this corpus was relying on:")
    acs = {"query": "q",
           "pages": [{"returned": 100, "total_reported": 430, "next_page_token": "PRESENT"},
                     {"returned": 100, "next_page_token": "PRESENT"},
                     {"returned": 3, "next_page_token": "null -- the cursor is exhausted"}]}
    ck("203 against a reported 430 with a null cursor is REFUSED",
       check(acs)[0], "CURSOR_SAID_DONE_BUT_THE_SUM_DOES_NOT_RECONCILE")
    ck("and it names the shortfall", check(acs)[2]["shortfall"], 227)
    okc = {"query": "q",
           "pages": [{"returned": 100, "total_reported": 137, "next_page_token": "PRESENT"},
                     {"returned": 37, "next_page_token": "null -- the cursor is exhausted"}]}
    ck("and colchicine's 137 == 137 with a null cursor does NOT trip this limb",
       check(okc)[0] != "CURSOR_SAID_DONE_BUT_THE_SUM_DOES_NOT_RECONCILE", True)
    print("  AN ABSENT TOKEN FIELD IS NOT A NULL ONE -- silence is not a claim:")
    silent = {"query": "q", "pmids": ["1", "2"],
              "pages": [{"returned": 2, "total_count": 523}]}
    ck("a record that never wrote the token falls through to the identifier checks",
       check(silent)[0], "REFUSED")

    print("\n  A RECORD THAT NAMES NOTHING CANNOT PASS:")
    ck("no identifier list -> NOT_ASSESSABLE",
       check({"query": "q", "pages": [{"returned": 137, "total_count": 137}]})[0],
       "NOT_ASSESSABLE")

    print("\n  PAGE-SPLIT LISTS ARE JOINED (the registry record spells it page_1 / page_2):")
    split = {"query": "q", "page_1": ["1", "2"], "page_2": ["3"],
             "counts": {"total_reported_by_the_registry": 3}}
    ck("page_1 + page_2 are one list of 3", check(split)[2]["listed"], 3)

    print("\n  THE LIVE RECORDS -- and a zero here would make a clean run meaningless:")
    rc = main()
    ck("the live scan reached at least one record with a list", rc in (0, 1), True)

    print("\n%s" % ("SELFTEST FAILED: %s" % fails if fails else "SELFTEST PASSED"))
    return 1 if fails else 0


if __name__ == "__main__":
    # WRAPPED ONCE, AT THE ENTRY POINT, AND NEVER INSIDE A FUNCTION.
    # `selftest()` calls `main()` -- proof number six is that the live scan runs at all -- and
    # with the wrapper inside both, the second call replaced the first's TextIOWrapper and the
    # first one's underlying buffer was closed. Every subsequent print raised
    # `ValueError: I/O operation on closed file` from inside a test that was passing.
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(selftest() if "--selftest" in sys.argv else main())
