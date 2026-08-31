# -*- coding: utf-8 -*-
"""Record what the newly-answered signalling questions actually imply for
RoB 2 domain 3 -- which is more than the extraction block said, and in the
direction that flatters this review.

WHY THIS EXISTS. `registry_extraction_2026_08_30` recorded the domain
implication as a general "would need re-deriving". A prediction logged before
that extraction ran said, in terms:

    "I predict this does NOT change the domain judgement to LOW, because
     3.2-3.4 concern differential missingness and dependence on the true value,
     which the flow table alone cannot answer."

THAT REASONING IS WRONG, and this repo's own implementation says so.
`ssot/rob2_algorithm.py` d3() is RoB 2 Table 10 and its first row is:

    if _i(a, YPY):
        return LOW, 'Table 10 row 1: 3.1 = Y/PY -> Low'

3.2, 3.3 and 3.4 are reached ONLY when 3.1 is No, Probably no, or No
information. With 3.1 = YES the domain is LOW on row one and the remaining
three questions are never asked. The prediction reasoned from questions the
algorithm does not reach.

⭐ THE CORRECTION RUNS AGAINST US, WHICH IS WHY IT IS WRITTEN DOWN. The
implication is not "the domain might move"; it is that domain 3 becomes LOW for
both trials on the tool's own table, and domain 3 is one of the two domains the
GRADE risk-of-bias downgrade names by name. An author who has just gathered
evidence that improves his own rating is precisely the case the two-assessor
rule exists for, so the derivation is SHOWN and NOT APPLIED.
"""
import datetime
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OBJ = os.path.join(HERE, "agyw-hiv-prep-review", "agyw-hiv-prep-review.json")
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()


def main():
    import rob2_algorithm as R

    # Run the tool's own table rather than asserting what it would say.
    #
    # ⚠️ AND CODE THE RESPONSES FIRST. d3() takes the tool's CODED tokens
    # ('Y/PY', 'N/PN', 'NI'), not raw answers. The first version of this script
    # passed the literal string "Y" -- `_i("Y", "Y/PY")` is False -- and every
    # branch fell through to UNDERIVABLE. It printed `None` for BOTH cases
    # while the prose beside it asserted the domain moves to LOW, so the object
    # briefly carried a derivation that contradicted its own conclusion. The
    # module exports `code()` for exactly this and it was not used.
    def _q(**kw):
        return {k.replace("_", "."): R.code(v) for k, v in kw.items()}

    d3_yes, why_yes = R.d3(_q(**{"3_1": "YES", "3_2": "NI",
                                 "3_3": "NI", "3_4": "NI"}))
    d3_ni, why_ni = R.d3(_q(**{"3_1": "NI", "3_2": "NI",
                               "3_3": "NI", "3_4": "NI"}))

    # The conclusion is READ OFF the derivation, never asserted beside it.
    assert d3_yes == R.LOW, (
        "the tool's Table 10 did not return LOW for 3.1 = Y/PY; it returned "
        "%r (%s). The prose in this script asserts LOW and must not ship if "
        "the algorithm disagrees." % (d3_yes, why_yes))

    obj = json.load(open(OBJ, encoding="utf-8"))
    blk = obj["registry_extraction_2026_08_30"]["what_the_posted_results_ANSWER_in_RoB_2"]

    blk["D3_DERIVED_FROM_THE_TOOLS_OWN_TABLE_2026_08_30"] = {
        "derived_with": ("ssot/rob2_algorithm.py d3(), which implements RoB 2 "
                         "Table 10. EXECUTED, not quoted."),
        "before_this_evidence": {
            "answers": {"3.1": "NI", "3.2": "NI", "3.3": "NI", "3.4": "NI"},
            "domain": d3_ni if d3_ni else "UNDERIVABLE",
            "underivable_means": (
                "Table 10 defines no row when 3.2 is No information: every row "
                "requires 3.2 in {Y/PY, N/PN}. With nothing answered the "
                "domain is not LOW, not HIGH and not SOME CONCERNS -- it is "
                "UNDERIVABLE, which this project records as a data gap rather "
                "than resolving to a letter."),
            "table_row": why_ni,
        },
        "with_3.1_answered_YES": {
            "answers": {"3.1": "Y", "3.2": "NI", "3.3": "NI", "3.4": "NI"},
            "domain": d3_yes,
            "table_row": why_yes,
            "applies_to": "BOTH trials -- 3.1 is YES for both.",
        },
        "⚠️_A_PREDICTION_THIS_CONTRADICTS": (
            "A prediction logged before the extraction ran said the flow data "
            "would NOT move the domain, \"because 3.2-3.4 concern "
            "differential missingness and dependence on the true value, which "
            "the flow table alone cannot answer\". Table 10 never reaches "
            "3.2-3.4 when 3.1 is YES. The reasoning was wrong and the "
            "consequence is the opposite of what was predicted: the domain "
            "moves to LOW, on the tool's first row, for both trials. Scored "
            "in evidence/2026-08-30-dapivirine-ahead/PREDICTIONS_SCORED.md."),
        "⛔_DERIVED_AND_NOT_APPLIED": {
            "what_is_NOT_done": (
                "No stored domain judgement is changed. No overall "
                "risk-of-bias rating is changed. No GRADE certainty is "
                "changed."),
            "why": (
                "This moves the rating in the direction that flatters this "
                "review, and it was found by the person who gathered the "
                "evidence. That is the exact case the standing two-assessor "
                "process exists for -- see `risk_of_bias.ONE_ASSESSOR_ONLY` "
                "and `risk_of_bias.SECOND_ASSESSOR_2026_08_21`. A derivation "
                "shown is a proposal; a derivation applied by its own author "
                "is a review rating itself up."),
            "what_would_close_it": (
                "A second assessor, from a different model family, answering "
                "3.1 independently from the same posted results, and the "
                "disagreement rate recorded whether or not they agree."),
            "and_the_GRADE_step_that_depends_on_it": (
                "The risk-of-bias downgrade's stated reason is \"D2 and D3 are "
                "NO_INFORMATION and on a PrEP trial those are the adherence "
                "and attrition domains -- the ones that decide whether an "
                "intention-to-treat ring effect reflects the drug or its "
                "use\". If D3 becomes LOW that reason is half retired, and the "
                "downgrade would need re-deriving rather than merely "
                "re-labelling. NOT DONE HERE, for the same reason."),
        },
        "what_this_does_NOT_touch": (
            "D1 on NCT01539226, which stands at SOME CONCERNS on signalling "
            "question 1.2 -- the allocation-concealment mechanism, which "
            "neither registration, neither set of posted results and neither "
            "published paper reports. That remains the one open question, and "
            "it is unaffected by anything here."),
        "recorded_utc": NOW,
    }

    tmp = OBJ + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False)
    os.replace(tmp, OBJ)

    print("WROTE D3_DERIVED_FROM_THE_TOOLS_OWN_TABLE_2026_08_30")
    print("  all NI              -> %s   (%s)" % (d3_ni, why_ni))
    print("  3.1 = YES           -> %s   (%s)" % (d3_yes, why_yes))
    print("  applied?            NO -- derived and routed to the second assessor")


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    main()
