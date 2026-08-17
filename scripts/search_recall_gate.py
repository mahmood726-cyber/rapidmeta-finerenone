"""SEARCH RECALL GATE -- does this search strategy retrieve the trials it includes?

WHY THIS EXISTS
    Building sotagliflozin's search record on 2026-08-16, a ClinicalTrials.gov
    query returned NCT06618976 and NCT05562063 -- and NEITHER was SOLOIST-WHF nor
    SCORED, the two trials the review actually pools. A registry search that
    misses both included trials is not a search strategy, and it would have been
    published as a screening log if the recall had not been checked.

    So: a search record is not credible until it has been shown to retrieve the
    studies the review says it included. This is the cheapest possible test of a
    search, it needs nothing but the record and the included set, and it can only
    be run by someone willing to see it fail.

PORTABILITY -- THIS APPLIES TO PUBLISHED REVIEWS, NOT ONLY TO OURS
    Re-run a published review's reported search strategy and ask whether it
    retrieves that review's own included studies. Mechanical, needs only the
    paper, and the expected failure rate on real reviews is worth measuring
    rather than assuming. Rated PORTABLE: the core takes (query results, included
    ids) and knows nothing about our HTML.

WHAT A FULL PASS DOES NOT ESTABLISH -- written in advance
    - NOT that the search is COMPLETE. Retrieving everything you included says
      nothing about what you failed to include; recall against your own set is a
      floor, not a ceiling. A search returning exactly your included studies and
      nothing else would pass here and be a terrible search.
    - NOT that screening was done well, or at all.
    - NOT that the query is the one that was actually run historically. It tests
      the query AS RECORDED against the set AS INCLUDED, today.
    - NOT that the databases searched are the right ones for the question.
"""
from __future__ import annotations
import json, sys, io, os

# Guarded: reassigning stdout AT IMPORT closes the caller's wrapper and the
# importer dies on "I/O operation on closed file" at its next print. Same trap
# already fixed in screen_harness; it was left in every sibling gate.
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def check(record, included_ncts, included_names, corpus_text):
    """-> (verdict, per-trial detail). A trial counts as retrieved if its
    registration id OR its trial name appears in what the search returned."""
    rows = []
    for nct, name in zip(included_ncts, included_names):
        by_id = bool(nct) and nct in corpus_text
        by_name = bool(name) and len(name) > 2 and name in corpus_text
        rows.append((name or "?", nct or "(no id)", by_id, by_name, by_id or by_name))
    missed = [r for r in rows if not r[4]]
    return ("FAIL" if missed else "PASS"), rows


def main():
    if sys.argv[1] == "--selftest":
        return selftest()
    rec = json.loads(open(sys.argv[1], encoding="utf-8", errors="replace").read())
    obj = json.loads(open(sys.argv[2], encoding="utf-8", errors="replace").read())
    corpus = open(sys.argv[3], encoding="utf-8", errors="replace").read() if len(sys.argv) > 3 else ""
    corpus += json.dumps(rec, ensure_ascii=False)
    trials = ((obj.get("inputs") or {}).get("trials")) or []
    v, rows = check(rec, [t.get("nct") for t in trials], [t.get("name") for t in trials], corpus)
    print("search recall: %d included trial(s)" % len(rows))
    for name, nct, bid, bnm, ok in rows:
        print("  %-16s %-14s by-id=%-5s by-name=%-5s %s"
              % (name[:16], nct, bid, bnm, "RETRIEVED" if ok else "MISSED"))
    print("-> %s" % v)
    return 0 if v == "PASS" else 1


def selftest() -> int:
    """Positive AND negative, from the real sotagliflozin run."""
    ok = True
    base = r"F:\claude-temp\searchrun"
    absts = os.path.join(base, "abstracts.txt")
    rec = os.path.join(base, "SEARCH_sotagliflozin.json")
    if not (os.path.exists(absts) and os.path.exists(rec)):
        print("  fixtures absent -- NOT PROVEN"); return 1
    corpus = open(absts, encoding="utf-8", errors="replace").read()
    r = json.loads(open(rec, encoding="utf-8", errors="replace").read())
    # NEGATIVE FIXTURE: the ctgov arm alone, which really did miss both trials.
    v_ct, rows_ct = check(r, ["NCT03521934", "NCT03315143"], ["SOLOIST-WHF", "SCORED"],
                          json.dumps(r["ctgov"], ensure_ascii=False))
    print("  ctgov arm alone (the real miss)      -> %-4s %s"
          % (v_ct, "correct" if v_ct == "FAIL" else "WRONG"))
    ok &= v_ct == "FAIL"
    # POSITIVE FIXTURE: pubmed abstracts, which do contain both.
    v_pm, rows_pm = check(r, ["NCT03521934", "NCT03315143"], ["SOLOIST-WHF", "SCORED"], corpus)
    print("  pubmed arm (both trials present)     -> %-4s %s"
          % (v_pm, "correct" if v_pm == "PASS" else "WRONG"))
    ok &= v_pm == "PASS"
    print("\nWHAT A FAILURE WOULD LOOK LIKE: the ctgov-only case passing, which is the "
          "exact strategy that missed SOLOIST and SCORED and would have shipped as a "
          "screening log.")
    print("-> SELFTEST PASS" if ok else "-> SELFTEST FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
