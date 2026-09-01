# -*- coding: utf-8 -*-
"""Separate WHAT WAS MEASURED from WHAT WE DID TO IT, on finerenone-cv.

THE DEFECT. `results.by_outcome.cv_composite_first.estimand_id_means` read:

    "the pooled first-occurrence CV composite across the two pivotal DKD trials"

That is two claims in one string. "the first-occurrence CV composite" is the
ENDPOINT -- a property of the trials, true before we existed. "pooled across the
two pivotal DKD trials" is a statement about OUR ANALYSIS.

WHY IT MATTERS BEYOND TIDINESS. A blinding guard on a judging panel refused to
send this object, correctly: its allow-list emits the outcome definition, and the
definition contained our result phrasing -- so a judge blinded to our estimate
would have been told we had produced a pooled one anyway. The fix belongs in the
store, not in the guard. Weakening the guard that caught it would be the same
mistake as widening a baseline to make a gate pass.

⛔ THE WORDS ARE SPLIT, NOT REWRITTEN. Every word of both halves occurs in the
original string. They are NOT contiguous substrings and cannot be: the two claims
are interleaved -- "the POOLED first-occurrence CV composite ACROSS the two
pivotal DKD trials" -- so pulling either half out necessarily breaks contiguity.
No new claim is introduced, no meaning is changed, and nothing is composed -- if the separation required inventing a
phrase, that would be authoring content into a store and it is not permitted.

⛔ NOT VERIFIED HERE, AND NAMED RATHER THAN IMPLIED: the blinding guard's
allow-list lives in another lane's tooling and is not present in this repo, so
this script CANNOT confirm that moving the analysis half to a sibling key removes
it from what that guard emits. What it can confirm is that the two claims are no
longer fused in one field. Whether the sibling key is also emitted is a question
for whoever owns the allow-list.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(HERE, "finerenone-cv", "finerenone-cv.json")
OID = "cv_composite_first"
KEY = "estimand_id_means"

ENDPOINT = "the first-occurrence CV composite"
ANALYSIS = "pooled across the two pivotal DKD trials"
ORIGINAL = "the pooled first-occurrence CV composite across the two pivotal DKD trials"


def plant(out):
    """A fix needs its own plant, and this one has two halves to prove.

    1. The separation must be a SPLIT: every word of each half must come from
       the original string. A rewrite that reads better but introduces a word is
       authored content, and the test must fail on it.
    2. The endpoint half must NOT still contain the analysis wording, which is
       the entire defect. A "fix" that leaves `pooled` in the definition is the
       original bug with extra fields."""
    # ⛔ WORD MEMBERSHIP, NOT SUBSTRING, AND THE FIRST DRAFT TESTED SUBSTRING.
    # It refused this write, correctly by its own rule and wrongly in fact: the
    # two claims are INTERLEAVED in the original -- "the POOLED first-occurrence
    # CV composite ACROSS the two pivotal DKD trials" -- so pulling either half
    # out necessarily breaks contiguity. No honest separation of an interleaved
    # string can be a contiguous substring, so the test could only ever have
    # passed for a separation that was not one.
    #
    # The property actually meant is: every word of each half occurs in the
    # original. That still refuses an invented phrase, which is the whole point,
    # and it permits the split that is genuinely a split. The failure direction
    # was safe -- it refused to write -- and it was still a wrong test.
    ok = True
    out("  PLANT -- the separation must split words, never invent them")
    orig_words = set(ORIGINAL.lower().replace("-", " ").split())

    def all_words_from_original(s):
        return all(w in orig_words for w in s.lower().replace("-", " ").split())

    cases = [
        ("endpoint half uses only words from the original", ENDPOINT, True),
        ("analysis half uses only words from the original", ANALYSIS, True),
        ("a plausible REWRITE is refused",
         "the composite of CV death, MI, stroke or HHF", False),
        ("a single invented word is refused",
         "the first-occurrence CV composite endpoint", False),
    ]
    for what, half, want in cases:
        got = all_words_from_original(half)
        mark = "ok" if got == want else "*** WRONG ***"
        out("    %-46s words_from_original=%-5s expected=%-5s %s"
            % (what, got, want, mark))
        if got != want:
            ok = False
    leak = any(w in ENDPOINT.lower() for w in ("pooled", "pooling", "across the"))
    out("    %-46s leaks=%-5s expected=%-5s %s"
        % ("endpoint half carries no analysis wording", leak, False,
           "ok" if not leak else "*** WRONG ***"))
    if leak:
        ok = False
    return ok


def main():
    if "--plant" in sys.argv:
        return 0 if plant(print) else 1
    if not plant(print):
        print("REFUSED: the plant does not pass, so nothing is written.")
        return 3
    print("")
    with io.open(STORE, encoding="utf-8") as fh:
        canon = json.load(fh)
    rec = ((canon.get("results") or {}).get("by_outcome") or {}).get(OID)
    if not isinstance(rec, dict):
        print("REFUSED: %s not found in %s" % (OID, STORE))
        return 3
    current = rec.get(KEY)
    if current != ORIGINAL:
        print("REFUSED: the field does not hold the string this script was written")
        print("  for. Expected: %r" % ORIGINAL)
        print("  Found:    %r" % current)
        print("  Editing it blind would overwrite someone else's change.")
        return 3

    rec[KEY] = ENDPOINT
    rec[KEY + "_analysis_note"] = (
        "%s. Separated from the estimand on 2026-09-01: the estimand names WHAT "
        "WAS MEASURED, which is a property of the trials; how it was combined is "
        "a statement about this review's analysis and does not belong in the "
        "definition of the endpoint. Every word of both halves occurs in the "
        "single string this field previously held -- the words were split, not "
        # ⛔ NOT .capitalize(). It lowercases every character after the first,
        # so "the two pivotal DKD trials" became "dkd" -- an acronym silently
        # destroyed by a formatting call, inside a fix whose entire premise is
        # that the words are not rewritten. Only the first character is raised.
        "rewritten." % (ANALYSIS[:1].upper() + ANALYSIS[1:]))
    rec[KEY + "_separated_because"] = (
        "A blinding guard on a judging panel refused to send this object, "
        "correctly. Its allow-list emits the outcome definition, and the "
        "definition contained our result phrasing, so a judge blinded to our "
        "estimate would have been told we had produced a pooled one. The store "
        "was the defect; the guard was right.")

    with io.open(STORE, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(canon, ensure_ascii=False, indent=1) + "\n")
    print("  WROTE %s" % os.path.relpath(STORE, os.path.dirname(HERE)))
    print("    %s = %r" % (KEY, ENDPOINT))
    print("    %s_analysis_note carries the analysis half" % KEY)
    return 0


if __name__ == "__main__":
    sys.exit(main())
