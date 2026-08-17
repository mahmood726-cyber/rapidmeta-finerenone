"""THE STANDARD -- what "done" means, versioned, with a check for every property.

ADMISSION CRITERION -- THIS IS THE RULE THAT WILL DECAY FIRST
    NO PROPERTY ENTERS v(n+1) WITHOUT A CONSTRUCTIBLE FAILING INPUT AND A REAL
    DEFECT IT WOULD HAVE CAUGHT.

    The pressure to add an aspirational property with no check will arrive the
    moment someone wants this list to look complete. A property with no failing
    input is a wish; a list of wishes reads as a standard and enforces nothing.
    This is the same bar as detector promotion in gate_integrity, and the symmetry
    is not a coincidence -- it is the same mechanism: A CHECK THAT CANNOT FAIL
    REPORTS SUCCESS WITHOUT HAVING CHECKED.

THE BOUNDARY OF THIS WHOLE APPARATUS
    THE STANDARD DOES NOT MAKE A REVIEW CORRECT. IT MAKES A REVIEW CHECKABLE.

    Every property below is structural or provenance-related. Eleven of them
    cannot detect a correctly-formatted synthesis of the wrong trials: a page can
    satisfy all of them, carry perfect provenance, agree across every surface, and
    pool trials that never measured the same thing. Source verification is human
    work and nothing here stands in for it.

    Anyone who reads v1 compliance as correctness has made the same error as
    reading a green gate as a verified page -- and this project made that error
    five separate times in a single day.

WHY THIS IS VERSIONED RATHER THAN FIXED
    "ARNI standard" was out of date the moment we found the Word renderer gap:
    ARNI itself did not meet the standard we now hold. A bar that moves as we
    learn is correct -- each page should be better than the last -- but "better
    than the last one" is unauditable unless the bar is written down and stamped.

    So: each page records the STANDARD VERSION it was built to, in its build
    stamp. A page at v1 while the standard is v3 is HONESTLY LABELLED, not
    silently stale, and "bring cardiology to standard" becomes a countable backlog
    instead of a feeling.

    NO PAGE IS GRANDFATHERED. When the version increments, every earlier page is
    out of date BY DEFINITION, including the flagship. ARNI was stale and its Word
    manuscript was missing a section; being the reference implementation earns no
    exemption.

THE RATCHET APPLIES TO THE HARNESS TOO
    Every defect found on page N becomes a detector before page N+1 is built.
    That is the mechanism that makes each page better than the last rather than
    merely aspiring to. A property enters this manifest only WITH a check that can
    fail, and where a real past defect exists the check must be replayed against
    it -- see the promotion criterion in gate_integrity.

WHAT A FULL PASS DOES NOT ESTABLISH -- written in advance
    - NOT that the review is CORRECT. Every property here is structural or
      provenance-related. A page can satisfy all of them and pool the wrong trials.
    - NOT that the numbers are right. Source verification is human work and this
      cannot stand in for it.
    - NOT that the standard is COMPLETE. It is the current state of what we have
      learned, which is exactly why it carries a version rather than a claim.
"""
from __future__ import annotations
import json, os, re, sys, io

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ---------------------------------------------------------------- the standard
STANDARD_VERSION = 1
STANDARD_DATE = "2026-08-17"
# v1 is the FIRST time the standard has been written down. Everything built before
# it was built to no written standard at all, which is why the corpus run found
# 6 of 513 pages on the current build and 1 of 53 cardiology topics at the bar.

PROPERTIES = [
    ("tabbed_build",
     "Eight-tab shell, no empty tab; absent sections render an honest state naming "
     "what is missing and why",
     "the flat pages were a different generation and read as unfinished"),
    ("estimate_preserved",
     "The displayed estimate equals the object's, digit for digit",
     "sig(x,3) silently rounded verified values during a REBUILD; 0.7171 became "
     "0.717 and the verified string appeared nowhere in the artefact"),
    ("card_matches_page",
     "The index card agrees with the page it points at",
     "ABLATION_AF served card HR 0.77 against page OR 0.7151 -- a public "
     "self-contradiction on a page reported as done"),
    ("extraction_table",
     "Extraction tab carries value, VERBATIM SOURCE SENTENCE, resolvable link, and "
     "read-versus-derived, per extracted value. ALL FOUR, OR THE PROPERTY IS NOT MET "
     "-- a table of values with no sentences is provenance theatre and FAILS, it "
     "does not partially pass",
     "a reader must be able to check us without reading the manuscript and without "
     "trusting us. ABLATION_AF and ALIROCUMAB both carry the table with ZERO verbatim "
     "quotes, and were nearly recorded as partial. The quote is the half that makes "
     "the table checkable: value plus link tells a reader WHERE to look, and only the "
     "sentence tells them WHAT WE READ, which is the thing they are checking. "
     "RELATEDLY, AND THE SAME BOUNDARY FROM THE OTHER SIDE: HAVING LINKS IS NOT BEING "
     "CHECKABLE. Trial-level provenance -- a resolvable link per included trial -- is "
     "widespread here, 27 of 31 sampled pages. Value-level provenance -- which NUMBER "
     "came from which SENTENCE -- exists on seven pages in 1450. A page can cite every "
     "trial correctly and still give a reader no way to check a single extracted "
     "number, and it will look fully sourced while doing it"),
    ("sections_in_both_surfaces",
     "Every section the object earns appears in BOTH the page and the manuscript",
     "the extraction table was missing from every Word manuscript ever produced and "
     "the alignment gate could not see it, because it compared only the intersection"),
    ("build_stamp",
     "Page states the generator commit AND standard version it was built to, and "
     "declares itself not reproducible if built from uncommitted code",
     "ARNI served a build predating a feature every neighbouring page had, and "
     "nothing detected it"),
    ("subject_match",
     "Every registration id on the page belongs to this page's own object",
     "four pages went live carrying ARNI's trials and manuscript"),
    ("arm_identity",
     "Intervention and control arms are distinguishable and are the claimed comparison",
     "DOAC_AF entered RE-LY as dabigatran-versus-dabigatran; HEPATITIS_B entered "
     "TAF-versus-TAF on a page titled TAF versus TDF"),
    ("poolable_or_withheld",
     "A pooled estimate is displayed only where the pool is established; otherwise "
     "withdrawn WITH ITS REASON",
     "of 522 judgeable topics, 141 cannot support a pooled estimate at all"),
    ("identity_by_registration",
     "Trials are keyed to registration id, never to a covering label",
     "PARACHUTE-HF was once read as ANSWER-HF because a label was accepted as identity"),
    ("no_synthesised_absence",
     "Absent fields state their absence and its correct reason; no plausible default "
     "is ever filled in",
     "a converted page explained its gap with an authored page's reason, which was "
     "false; and comparator_type would be right most of the time as 'placebo', which "
     "is exactly why guessing it is dangerous"),
    ("display_change_announced",
     "ANY change to a published display value is announced, INCLUDING when the "
     "underlying value is unchanged -- a re-rounding, a precision change, a unit or "
     "format change, all of it",
     "ARNI's card moved from HR 0.872 (0.746-1.02) to 0.8715 (0.7461-1.018) when the "
     "generator's precision went from three significant figures to four. Same number, "
     "0.87153524291, one more digit, and all three surfaces moved together -- so every "
     "internal consistency check passed and nothing would have said a word. But A "
     "READER WHO WROTE DOWN 0.872 AND NOW SEES 0.8715 HAS NO WAY TO KNOW WHICH OF THE "
     "TWO IS THE CORRECTION. Silence makes a refinement indistinguishable from a "
     "retraction, and the reader must assume the worse of the two. The obligation is "
     "to the reader's record, not to our own consistency; 'the value did not change' "
     "is precisely the case where nobody thinks to say anything"),
]

# Properties a page may not yet reach, but which must be TRUE OR DECLARED.
ASPIRATIONAL = [
    ("manuscript_own",
     "The review has a manuscript of its own, projected from its own object",
     "a hardcoded path put ARNI's manuscript on four unrelated pages"),
    ("r_output_verbatim",
     "Statistical output quoted verbatim from a second engine",
     "reproducibility validates the engine, not the inputs -- but it is still owed"),
    ("published_comparison",
     "Comparison with published syntheses, in both surfaces",
     "or an explicit statement that no synthesis reports this estimand"),
    ("search_and_screening",
     "Search record with recall precondition, screening log with a decision per "
     "record, PRISMA counts that close",
     "a search that misses the trials you already include is not a search strategy"),
    ("rob2_and_grade",
     "Risk-of-bias assessment and certainty rating, dated honestly",
     "an unverifiable domain is not a low-risk domain"),
]


def render():
    print("THE STANDARD  v%d  (%s)" % (STANDARD_VERSION, STANDARD_DATE))
    print("=" * 78)
    print("\nREQUIRED -- a page is not at standard without all of these:\n")
    for i, (k, what, why) in enumerate(PROPERTIES, 1):
        print("%2d. %-28s %s" % (i, k, what))
        print("    %s   because: %s" % (" " * 28, why))
    print("\nOWED -- true or explicitly declared absent, never silently missing:\n")
    for i, (k, what, why) in enumerate(ASPIRATIONAL, 1):
        print("%2d. %-28s %s" % (i, k, what))
        print("    %s   note: %s" % (" " * 28, why))
    print("\nEVERY property above entered this list WITH a check that can fail.")
    print("When a new defect is learned, the version increments and every earlier")
    print("page is out of date by definition -- the flagship included.")


if __name__ == "__main__":
    render()
