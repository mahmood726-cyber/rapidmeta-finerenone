"""A citation year must come from the article, not from a database's date field.

WHY THIS EXISTS, and it is the only regression a fix caused in this whole cycle.

ANSWER-HF was cited as JACC 2026;87(10):1220-1232. I "corrected" it to 2025 on
the strength of PubMed's `publication_date` field, which returned 2025-11-09.
That field returns the EPUB date for articles published ahead of issue. The
article's own citation line reads:

    (JACC. 2026;87:1220-1232)
    JACC VOL. 87, NO. 10, 2026 - MARCH 17, 2026:1220-1232

and PubMed's own citation string reads:

    J Am Coll Cardiol. 2026 Mar 17;87(10):1220-1232. Epub 2025 Nov 9.

So the object was right and the correction made it wrong. The same shape as every
other instrument failure in this run -- a source answering a different question
from the one asked -- except this time it was inside a correction, and it passed
every gate we had, because no gate checked a citation year against its source.

PARACHUTE-HF has the identical shape: JAMA vol 335 no 1 is a 2026 issue, and the
staged PMC header says "2025 Dec 3". Its 2026 was correct too.

THE INVARIANT: for any article whose Epub year differs from its issue year, the
recorded citation year is the ISSUE year, and the Epub date is recorded
separately rather than substituted. A DOI containing a year proves nothing --
DOIs are minted at acceptance.

Usage:  python citation_year_gate.py <object.json>
        python citation_year_gate.py --selftest
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from verdict import Verdict, PASS, FAIL, INVALID, summarise  # noqa: E402

# "J Am Coll Cardiol. 2026 Mar 17;87(10):1220-1232" -> issue year 2026
CITE = re.compile(r"(?P<year>(?:19|20)\d{2})\s*(?:[A-Z][a-z]{2}\s*\d{0,2})?\s*;"
                  r"\s*(?P<vol>\d{1,4})\s*\((?P<iss>[^)]{1,8})\)")
EPUB = re.compile(r"Epub\s+((?:19|20)\d{2})", re.I)


def check_trial(t, cites):
    nm = t.get("name") or t.get("id")
    yr = t.get("year")
    pmid = str(t.get("pmid") or "")
    c = (cites or {}).get(pmid) or {}
    cy = c.get("year")
    if yr is None and cy is None:
        return Verdict("%s has a citation year" % nm, FAIL,
                       detail="no year on the trial row or in its citation")
    if cy is not None and yr is not None and int(cy) != int(yr):
        return Verdict("%s year agrees across trial row and citation" % nm, FAIL,
                       detail="trial row says %s, citation block says %s"
                              % (yr, cy))
    epub = t.get("epub_date")
    if epub:
        ey = int(str(epub)[:4])
        if ey == int(yr):
            return Verdict("%s: epub year differs from issue year" % nm, FAIL,
                           detail="epub_date %s has the same year as the "
                                  "recorded citation year %s, so one of them is "
                                  "wrong -- an epub_date is only worth recording "
                                  "when it differs" % (epub, yr))
        if not t.get("citation_year_basis"):
            return Verdict("%s: epub-ahead-of-issue is declared" % nm, FAIL,
                           detail="epub_date %s differs from citation year %s "
                                  "but no citation_year_basis states which is "
                                  "which. This is the exact configuration that "
                                  "produced the only regression in this cycle."
                                  % (epub, yr))
        return Verdict("%s: epub %s, cited at issue year %s" % (nm, epub, yr),
                       PASS,
                       witness="basis recorded: %s"
                               % str(t["citation_year_basis"])[:110],
                       failure_would_be="the epub year substituted for the "
                                        "issue year, which is what a database "
                                        "publication-date field returns")
    return Verdict("%s cited at %s" % (nm, yr), PASS,
                   witness="trial row and citation block agree at %s; no "
                           "epub-ahead-of-issue recorded" % yr,
                   failure_would_be="row and citation disagreeing, or an epub "
                                    "year recorded as the citation year")


def check(d):
    trials = (d.get("inputs") or {}).get("trials") or []
    if not trials:
        return [Verdict("object has trials to check", INVALID,
                        detail="no inputs.trials")]
    return [check_trial(t, d.get("citations")) for t in trials]


def selftest():
    print("=== the citation-year gate ===")
    C = {"citations": {"1": {"year": 2026}}}

    def obj(**kw):
        t = {"name": "T", "id": "t", "pmid": "1"}
        t.update(kw)
        return dict(C, inputs={"trials": [t]})

    cases = [
        ("THE REGRESSION: epub year used as the citation year",
         dict(C, inputs={"trials": [{"name": "ANSWER-HF", "id": "a", "pmid": "1",
                                     "year": 2025, "epub_date": "2025-11-09"}]}),
         FAIL),
        ("epub ahead of issue, declared, cited at issue year",
         obj(year=2026, epub_date="2025-11-09",
             citation_year_basis="issue year from the article citation line"),
         PASS),
        ("epub ahead of issue but no basis recorded",
         obj(year=2026, epub_date="2025-11-09"), FAIL),
        ("NEGATIVE: an ordinary article with no epub split",
         dict({"citations": {"1": {"year": 2014}}},
              inputs={"trials": [{"name": "PARADIGM-HF", "id": "p", "pmid": "1",
                                  "year": 2014}]}), PASS),
        ("trial row and citation block disagree",
         obj(year=2021), FAIL),
        ("no trials at all -> INVALID, not PASS", {"inputs": {"trials": []}},
         INVALID),
    ]
    ok = True
    for name, dd, want in cases:
        vs = check(dd)
        got = (FAIL if any(v.state == FAIL for v in vs)
               else INVALID if any(v.state == INVALID for v in vs) else PASS)
        good = got == want
        ok &= good
        print("  %-56s %-8s expected=%-8s %s"
              % (name[:56], got, want, "correct" if good else "WRONG"))
    print("\ncitation-year gate correct on every case:", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(selftest())
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    raise SystemExit(summarise(check(d), "citation year:"))
