"""RECORD THE HONEST STATE of topic 2's cross-family adjudication: agy-complete, Codex partial.

THE DECISION AND ITS RULE. Codex cleared chunk 1 (44 trials) in ~10 minutes and then spent
~35 minutes on chunk 2 without clearing it, while agy completed all 8 chunks. That is
DEGRADATION, NOT VARIANCE, and the standing instruction is to give it one more chunk and then
report rather than block a topic indefinitely on a slowing seat.

    A SECOND READING IS WORTH HAVING AND IT IS NOT WORTH BLOCKING A TOPIC ON INDEFINITELY.

WHAT THIS RECORDS, AND WHAT IT REFUSES TO RECORD.

    44 of 352   DUAL-READ    -- both families answered; agreement is computed and reported
   308 of 352   SINGLE-READ  -- agy only. NOT ADJUDICATED, NOT SCORED, NOT DISPOSITIONED.

The 308 are not given agy's answer as a verdict. A trial one seat read is not a trial that was
decided, and an absent second reading is ABSENT rather than CONCURRING -- the same rule that
would have let a dead seat read as a unanimous one earlier tonight. Holding it makes the
visible progress look slower and is the only honest option.

THE THROUGHPUT FACT IS RECORDED BECAUSE IT IS OPERATIONAL, NOT INCIDENTAL. Two seats on
identical 44-trial packets: agy ~2 min/chunk, Codex ~10 min/chunk falling to >35. A 5x
throughput difference that then degraded further changes how a cross-family pass should be
planned:

    CHUNKING IS WHAT MADE THIS SURVIVABLE. It converted an all-or-nothing wait into an
    incremental read with per-chunk assertions, so chunk 1 gave a usable early result -- both
    rates, and the RHYTHM_BOTH_ARMS finding -- instead of nothing at all. A single 352-trial
    call to each seat would have produced one unusable timeout and no signal.

Every chunk that DID return passed `rc == 0` AND the >=44-answer count assertion, so nothing is
silently wrong with what was collected. The seat slowed; it did not corrupt.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(REPO, "evidence", "2026-08-19-batch1", "rhythm_adjudication_state.json")
ADJ = os.path.join(REPO, "evidence", "2026-08-19-batch1", "rhythm_adjudication.json")


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    a = json.load(io.open(ADJ, encoding="utf-8"))
    dual = a["n"]
    single = len(a["not_answered_by_both"])
    out = {
        "recorded_utc": "2026-08-19",
        "topic": "early-rhythm-control-af",
        "state": "AGY-COMPLETE, CODEX PARTIAL -- reported rather than blocked",
        "n_to_adjudicate": dual + single,
        "dual_read": dual,
        "single_read_NOT_adjudicated": single,
        "why_the_single_read_are_not_scored": (
            "A trial one seat read is not a trial that was decided. An absent second reading "
            "is ABSENT, not CONCURRING. Scoring agy's 308 answers alone would convert a "
            "missing check into apparent agreement -- the same substitution that would have "
            "let a dead seat read as a unanimous one."),
        "rates_over_the_dual_read_44_only": {
            "code_agreement_pct": a["code_agreement_rate_pct"],
            "disposition_agreement_pct": a["disposition_agreement_rate_pct"],
            "caveat": ("these are over 44 trials, not 352, and P34 applies: the gap between "
                       "the two rates measures THIS vocabulary's granularity and is not "
                       "comparable with the sibling topic's gap."),
        },
        "seat_throughput": {
            "packet": "44 trials per chunk, 8 chunks, identical to both seats",
            "agy": "~2 min/chunk, 8/8 complete",
            "codex": "~10 min for chunk 1, then >35 min on chunk 2 without clearing",
            "verdict": "DEGRADATION, NOT VARIANCE",
            "assertions_held": ("every chunk that returned passed rc == 0 AND the >=44-answer "
                                "count assertion. The seat slowed; it did not corrupt."),
            "what_made_it_survivable": (
                "CHUNKING. It converted an all-or-nothing wait into an incremental read with "
                "per-chunk assertions, so chunk 1 produced both rates and the "
                "RHYTHM_BOTH_ARMS finding instead of nothing. A single 352-trial call to each "
                "seat would have produced one unusable timeout and no signal."),
        },
        "consequence_for_the_topic": (
            "early-rhythm-control-af CANNOT be completed on this pass. Its remainder is 352 "
            "of which 44 are adjudicated and 308 are not, so k_unscreened_remainder is 308 "
            "and NOT zero. The object must say so on its face rather than reporting a "
            "remainder it has not screened."),
    }
    with io.open(DEST, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, indent=1))
    print("dual-read (both seats)        %4d" % dual)
    print("single-read, NOT adjudicated  %4d" % single)
    print("code agreement over the 44    %.1f%%" % a["code_agreement_rate_pct"])
    print("disposition agreement          %.1f%%" % a["disposition_agreement_rate_pct"])
    print("\nearly-rhythm-control-af remainder is 308, NOT zero.")
    print("wrote %s" % DEST)
    return 0


if __name__ == "__main__":
    sys.exit(main())
