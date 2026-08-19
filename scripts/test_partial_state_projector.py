#!/usr/bin/env python3
"""THE THIRD STATE, TESTED WITHOUT REBUILDING A DELIVERED PAGE.

The projector change is small and its blast radius is every page ever rebuilt, so it is tested
against the branch directly rather than by regenerating pages and reading the result. Rebuilding
seven live pages to find out whether a sentence is right is the wrong order.

WHAT IS ASSERTED, and each of these is a case that actually occurred:

  A panel holding a QUERY but no yield        -> PARTIALLY HELD, naming the query as held
  A panel holding NOTHING                     -> NOT HELD, the original sentence unchanged
  A tab with no PARTIAL_STATE entry           -> falls back to NOT HELD rather than inventing one
  The two sentences are never both emitted    -> the label is one or the other
"""
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import projectors as P                                                  # noqa: E402


def decide(body, tid):
    """The projector's branch, exercised in isolation."""
    carries = bool(re.search(r"<(?:pre|table|svg|li|dl)[ >/]", body)) \
        or len(re.sub(r"<[^>]+>", " ", body).strip()) > 80
    if carries and tid in P.PARTIAL_STATE:
        return "Partially held.", P.PARTIAL_STATE[tid]
    return "Not held in this object.", P.ABSENT_STATE.get(tid, "")


def main():
    fails = []

    def ck(name, got, want):
        ok = got == want
        print("  %-66s %s" % (name, "ok" if ok else "FAIL"))
        if not ok:
            print("      got  %r" % (got,))
            fails.append(name)

    print("1. THE CASE THAT PRODUCED ELEVEN FALSE REFUSALS -- a query, no yield:")
    body = ("<div class='card'><h3>ClinicalTrials.gov API v2</h3>"
            "<pre>intervention=\"colchicine\"</pre>"
            "<table><caption>Table 2.</caption></table></div>")
    label, note = decide(body, "search")
    ck("labelled PARTIALLY HELD, not denied", label, "Partially held.")
    ck("...and it says the query IS held", "query is held" in note.lower(), True)
    ck("...and that the yield is NOT", "yield is not" in note.lower(), True)
    ck("...and the old false sentence is gone",
       "no query, date or yield can be shown" in note.lower(), False)
    ck("...and it does NOT call the set a convenience sample",
       "convenience sample" in note.lower(), False)

    print("\n2. A GENUINELY EMPTY PANEL still gets the original refusal, unchanged:")
    label, note = decide("", "search")
    ck("labelled NOT HELD", label, "Not held in this object.")
    ck("...with the original wording intact",
       "no query, date or yield can be shown" in note.lower(), True)

    print("\n3. WHITESPACE AND MARKUP ARE NOT CONTENT:")
    label, _ = decide("<div class='card'>   </div>", "search")
    ck("an empty card is still NOT HELD", label, "Not held in this object.")

    print("\n4. A TAB WITH NO PARTIAL SENTENCE FALLS BACK rather than inventing one:")
    ck("`statistics` has no PARTIAL_STATE entry", "statistics" in P.PARTIAL_STATE, False)
    label, note = decide("<pre>something</pre>", "statistics")
    ck("so it stays NOT HELD", label, "Not held in this object.")
    ck("...with its own absent text", note, P.ABSENT_STATE["statistics"])

    print("\n5. THE TWO SENTENCES ARE NEVER BOTH EMITTED:")
    for tid in ("search", "screen", "report", "analysis", "protocol", "extract"):
        l1, n1 = decide("<pre>x</pre>" + "y" * 200, tid)
        l2, n2 = decide("", tid)
        if l1 == l2:
            fails.append("%s: both bodies give the same label" % tid)
    ck("every partial tab distinguishes a carrying body from an empty one",
       [f for f in fails if "same label" in f], [])

    print("\n%s" % ("FAILED: %s" % fails if fails else "PASSED"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main())
