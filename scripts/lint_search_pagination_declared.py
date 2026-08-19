#!/usr/bin/env python3
"""E10, CURSOR ABANDONMENT: a search that returned fewer records than it reported must SAY SO.

THE INSTANCE THAT CLOSED THIS CLASS, 2026-08-19, on `colchicine-cvd-review`:

    page 1   returned 100   total_reported 137   next_page_token PRESENT

Building on that page would have produced a complete-looking cascade over 100 records, screened
its remainder to zero, and been MISSING THE LARGEST TRIAL IN ITS OWN INCLUDED SET -- CLEAR
SYNERGY (NCT03048825, n=7264) is on page 2 only.

    recall on page 1 alone   2/3
    recall on the complete search   3/3

NOTHING ABOUT THE PARTIAL PAGE WOULD HAVE LOOKED WRONG. 100 records is a plausible surfaced set,
the arithmetic reconciles with itself, and `k_unscreened_remainder: 0` prints happily over a
search that is 27 per cent short. The error runs in the direction that makes a review look
FINISHED, which is the withholding direction arriving at the search stage.

SAME CLASS AS THE PHASE FILTER, DIFFERENT ROUTE. `apixaban-vte` lost NCT02366871 -- one of its
own two included trials -- to `phase=[PHASE3,PHASE4]`, and P23 requires that miss to be RECORDED
RATHER THAN REPLACED. A query parameter and an unexhausted cursor remove trials the same way.
Only the parameter had a guard; this is the cursor's.

WHAT IT CHECKS. For every database row in every object's `search.databases`: if
`records_returned < total_reported`, the row must DECLARE the shortfall. A declared shortfall is
a legitimate and common state -- `apixaban-vte-treatment`'s PubMed row reads

    "439 records matched and 50 were retrieved. THE OTHER 389 ARE UNEXAMINED, NOT EXCLUDED"

-- and that row PASSES. An undeclared shortfall is the defect: a search silently treated as
whole.

WHAT IT DOES NOT CHECK, so a clean run is not read as more than it is:
  - NOT whether the declared numbers are TRUE. It compares an object's own two fields.
  - NOT whether the unexamined records matter. `apixaban`'s 389 unexamined PubMed records are
    declared and unexamined and might contain anything.
  - NOT rows where `total_reported` is absent -- those are NOT_ASSESSABLE, never a pass, and
    they are counted and printed separately.

USAGE:  python scripts/lint_search_pagination_declared.py
        python scripts/lint_search_pagination_declared.py --selftest
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")

# A shortfall is DECLARED when the row says, in its own words, that records were not examined.
# Matched against the whole row so the declaration may sit in any field the author chose --
# `what_is_unexamined`, `what_it_cost`, a note, or the query string itself.
DECLARED = re.compile(
    r"unexamined|not\s+examined|not\s+excluded|were\s+retrieved|were\s+not\s+fetched|"
    r"cursor|next_page_token|page\s*2|incomplete|shortfall|remaining\s+\d+\s+are",
    re.I)


def rows():
    """[(topic, index, row)] over every declared database row in every object."""
    out = []
    for d in sorted(os.listdir(SSOT)):
        p = os.path.join(SSOT, d, d + ".json")
        if not os.path.exists(p):
            continue
        try:
            with io.open(p, encoding="utf-8") as fh:
                o = json.load(fh)
        except (ValueError, OSError):
            continue
        for i, r in enumerate((o.get("search") or {}).get("databases") or []):
            if isinstance(r, dict):
                out.append((d, i, r))
    return out


def scan():
    """(undeclared, declared, not_assessable) over every database row in the corpus."""
    undeclared, declared, na = [], [], []
    for topic, i, r in rows():
        got, tot = r.get("records_returned"), r.get("total_reported")
        if not isinstance(got, int) or not isinstance(tot, int):
            na.append((topic, i, r.get("database", "?")))
            continue
        if got >= tot:
            continue
        blob = json.dumps(r)
        (declared if DECLARED.search(blob) else undeclared).append(
            (topic, i, r.get("database", "?"), got, tot))
    return undeclared, declared, na


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    undeclared, declared, na = scan()
    print("database rows scanned                 %d" % len(rows()))
    print("shortfall DECLARED (legitimate)       %d" % len(declared))
    for t, _i, db, got, tot in declared:
        print("   %-44s %-52s %d of %d" % (t, db[:52], got, tot))
    print("rows with no comparable counts        %d   NOT_ASSESSABLE, never a pass" % len(na))
    print("shortfall UNDECLARED                  %d" % len(undeclared))
    for t, _i, db, got, tot in undeclared:
        print("   %-44s %-52s %d of %d" % (t, db[:52], got, tot))
    if undeclared:
        print("\nREFUSED: a search returned fewer records than it reported and does not say so. "
              "A partial surfaced set treated as whole produces a cascade that reconciles with "
              "itself and is missing trials -- in the direction that makes a review look "
              "finished.")
        return 1
    print("\nevery search row that returned fewer records than it reported declares the "
          "shortfall.")
    print("NOT CHECKED: whether the declared numbers are TRUE, or whether the unexamined "
          "records matter. This compares two fields an object states about itself.")
    return 0


def selftest():
    """P16 four ways, and the firing case is the one that really happened."""
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    fails = []

    def check(name, got, want):
        ok = got == want
        print("  %-62s %s  %r" % (name, "ok" if ok else "FAIL", got))
        if not ok:
            fails.append(name)

    # THE STATE THAT REALLY OCCURRED, reconstructed from the recorded page-1 numbers.
    real = {"database": "ClinicalTrials.gov API v2", "records_returned": 100,
            "total_reported": 137, "query_as_executed": "intervention=colchicine..."}
    check("the colchicine page-1 row is UNDECLARED and fires",
          bool(DECLARED.search(json.dumps(real))), False)

    # THE DECLARED SHORTFALL THAT MUST PASS -- apixaban's PubMed row, quoted from the object.
    ok_row = {"database": "PubMed", "records_returned": 50, "total_reported": 439,
              "what_is_unexamined": ("439 records matched and 50 were retrieved. THE OTHER 389 "
                                     "ARE UNEXAMINED, NOT EXCLUDED")}
    check("a DECLARED shortfall passes", bool(DECLARED.search(json.dumps(ok_row))), True)

    # A complete row is not a shortfall at all.
    full = {"database": "x", "records_returned": 57, "total_reported": 57}
    check("a complete row is not a shortfall", full["records_returned"] >= full["total_reported"],
          True)

    # And it must not fire on the live corpus, or nobody can wire it.
    undeclared, declared, na = scan()
    check("the live corpus has NO undeclared shortfall", undeclared, [])
    check("and there ARE declared shortfalls to find -- a scan finding none proves nothing",
          len(declared) > 0, True)

    print("\n%s" % ("ALL FOUR PROOFS HELD" if not fails else "FAILED: %s" % fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
