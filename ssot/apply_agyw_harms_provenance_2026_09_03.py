r"""AGYW: the SAE counts disagree with their own publication, and the page said WHY from the rates.

THE DEFECT IS NOT THE DISAGREEMENT. It is the sentence explaining it.

`harms_2026_08_30` reports serious adverse events of 116/1313 against 130/1316 in ASPIRE
and 41/1306 against 9/652 in the Ring Study, and then declines to pool them with this
reason:

    "THE TWO PLACEBO ARMS DIFFER SEVEN-FOLD ... A seven-fold difference in the CONTROL
     arm is a difference in what was counted and reported, not in what happened."

⛔ THAT IS A PROVENANCE CLAIM INFERRED FROM TWO RATES. Nothing was read to establish it.
   "What was counted" is a fact about documents and it is settled by reading documents; a
   ratio between two percentages cannot distinguish a reporting difference from a real
   one, however large it is. The conclusion may well be right. It was not EARNED, and a
   right conclusion resting on a false premise is the class this repository already
   carries as Class 97.

WHAT READING THE DOCUMENT ACTUALLY SHOWED, AND IT IS WORSE THAN THE PAGE THOUGHT.
ASPIRE's own primary report -- Baeten et al., N Engl J Med 2016, PMID 26900902, PMCID
PMC4993693, Table 2, staged in this object's own sources/ directory since 2026-08-30 --
reports ANY SERIOUS ADVERSE EVENT as 52 (4%) against 48 (4%). The page reports 116 against
130 from the registry. SAME TRIAL, SAME DENOMINATORS, A FACTOR OF 2.2 AND 2.7 APART.

And that breaks the page's own arithmetic: the "seven-fold" control-arm gap is 7.16x
registry-to-registry and 2.64x when ASPIRE's placebo arm is taken from ASPIRE's paper. The
number the reason was built on was itself one of the two disputed numbers.

WHAT IS ESTABLISHED, WHAT IS NOT, AND THE DIFFERENCE STATED IN THE OBJECT. The denominators
match exactly and the DEATHS match exactly -- 4 and 3 in both sources -- so this is not an
arm-mapping error and not a population mismatch, and those two were the likely culprits.
Why the SAE rows differ is NOT established by anything this lane read, and it is recorded
as UNRESOLVED with the document that would settle it named. It is not guessed a second time.
"""
from __future__ import annotations

import io
import json
import math
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
from atomic_write import write_json                                         # noqa: E402

TOPIC = "agyw-hiv-prep-review"
OBJ = os.path.join(REPO, "ssot", TOPIC, TOPIC + ".json")


def rr(e1, n1, e2, n2):
    p = (e1 / n1) / (e2 / n2)
    se = math.sqrt(1.0 / e1 - 1.0 / n1 + 1.0 / e2 - 1.0 / n2)
    return {"point": round(p, 4),
            "ci_low": round(math.exp(math.log(p) - 1.959964 * se), 4),
            "ci_high": round(math.exp(math.log(p) + 1.959964 * se), 4),
            "se_log_rr": round(se, 6)}


def key_paths(o, p=""):
    out = set()
    if isinstance(o, dict):
        for k, v in o.items():
            out.add(p + "." + k)
            out |= key_paths(v, p + "." + k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            out |= key_paths(v, p + "[%d]" % i)
    return out


BLOCK = {
    "_what": (
        "THE SERIOUS-ADVERSE-EVENT COUNTS ON THIS PAGE DO NOT MATCH THE COUNTS IN THE "
        "TRIALS' OWN PRIMARY REPORTS, and until 2026-09-03 the page explained the "
        "discrepancy from the rates rather than from the documents. This block records "
        "both sources side by side, states what reading the documents DID establish, and "
        "records the rest as UNRESOLVED."),
    "_the_rule_this_closes": (
        "⛔ NEVER INFER PROVENANCE STATISTICALLY. 'A difference in what was counted rather "
        "than in what happened' is a claim about documents. A ratio between two "
        "percentages cannot distinguish a reporting difference from a real one, at any "
        "size. Establish it from the sources or record it as unresolved."),
    "ASPIRE_NCT01617096": {
        "registry": {
            "source": "ClinicalTrials.gov NCT01617096 resultsSection.adverseEventsModule",
            "read_utc": "2026-09-03",
            "eventGroups_time_frame_as_posted": "24 Months",
            "frequency_threshold_as_posted": 2,
            "dapivirine": {"serious": 116, "n": 1313, "deaths": 4},
            "placebo": {"serious": 130, "n": 1316, "deaths": 3},
            "rr_serious": rr(116, 1313, 130, 1316),
        },
        "publication": {
            "source": ("Baeten JM et al. Use of a Vaginal Ring Containing Dapivirine for "
                       "HIV-1 Prevention in Women. N Engl J Med 2016. PMID 26900902, "
                       "PMCID PMC4993693, doi 10.1056/NEJMoa1506110, TABLE 2."),
            "staged_at": "ssot/agyw-hiv-prep-review/sources/ASPIRE_PMC4993693.extract.txt",
            "read_utc": "2026-09-03",
            "table_2_verbatim_rows": {
                "primary safety end point": {"dapivirine": 180, "placebo": 186},
                "any serious adverse event": {"dapivirine": 52, "placebo": 48},
                "death": {"dapivirine": 4, "placebo": 3},
                "any grade 4 event": {"dapivirine": 22, "placebo": 23},
                "any grade 3 event": {"dapivirine": 151, "placebo": 162},
                "any grade 2 event assessed as related": {"dapivirine": 7, "placebo": 9},
            },
            "n": {"dapivirine": 1313, "placebo": 1316},
            "primary_safety_end_point_definition_verbatim": (
                "a composite of any serious adverse event, any grade 3 or 4 adverse "
                "event, and any grade 2 adverse event that was assessed by the trial "
                "clinicians as being related to dapivirine"),
            "rr_serious": rr(52, 1313, 48, 1316),
        },
        "⛔_they_disagree": (
            "SERIOUS ADVERSE EVENTS: registry 116 and 130; publication 52 and 48. Same "
            "trial, same denominators, a factor of 2.2 in one arm and 2.7 in the other. "
            "The relative risks are 0.8943 (0.7047 to 1.1351) from the registry and "
            "1.0858 (0.7390 to 1.5954) from the paper -- both intervals include 1, so "
            "nothing about the safety reading turns on it, and the DISCREPANCY ITSELF is "
            "the finding."),
        "✓_what_reading_the_documents_ESTABLISHED": [
            "THE DENOMINATORS ARE IDENTICAL in both sources: 1313 and 1316.",
            "THE DEATHS ARE IDENTICAL in both sources: 4 and 3.",
            "Therefore this is NOT an arm-mapping error and NOT a population mismatch -- "
            "the two candidates that would have mattered most, and the two that a rate "
            "comparison could never have ruled out.",
        ],
        "⛔_UNRESOLVED": (
            "WHICH PARTICIPANTS THE REGISTRY'S 116 AND 130 COUNT. Neither document states "
            "it. The registry posts a time frame of '24 Months' and a frequency threshold "
            "of 2; the paper's Table 2 gives no period for its own rows in the text this "
            "lane read. NOTHING HERE ESTABLISHES THE REASON AND THIS OBJECT DOES NOT "
            "GUESS IT A SECOND TIME."),
        "what_would_resolve_it": (
            "Summing the registry's own MedDRA serious-event table BY PARTICIPANT and "
            "comparing that total with Table 2, or reading the MTN-020 clinical study "
            "report. Either is a document. Neither is a ratio."),
        "an_observation_that_is_NOT_an_explanation": (
            "The registry's serious counts fall BETWEEN the paper's serious-adverse-event "
            "row and its broader primary-safety composite, in both arms: 52 < 116 < 180 "
            "and 48 < 130 < 186. ⛔ THAT IS AN ORDERING, NOT A REASON. It is recorded "
            "because it is where a reader should look first, and it is labelled so that "
            "it cannot be quoted as the answer."),
    },
    "RING_STUDY_NCT01539226": {
        "registry": {
            "source": "ClinicalTrials.gov NCT01539226 resultsSection.adverseEventsModule",
            "read_utc": "2026-09-03",
            "dapivirine": {"serious": 41, "n": 1306, "deaths": 2},
            "placebo": {"serious": 9, "n": 652, "deaths": 3},
            "arm_keying": (
                "Keyed from the eventGroup TITLE. EG000 on this registration is PLACEBO, "
                "which is the OPPOSITE of its OG000. Confirmed again on 2026-09-03: "
                "EG000 title 'Placebo Vaginal Ring', EG001 title 'Dapivirine Vaginal "
                "Ring'."),
            "rr_serious": rr(41, 1306, 9, 652),
        },
        "publication": {
            "⛔_NOT_READ_BY_THIS_LANE": (
                "The review request that opened this work states the Ring Study "
                "publication reports 38 against 6. THAT NUMBER IS NOT REPRODUCED HERE "
                "AND IS NOT RECORDED AS A FINDING, because this lane holds only an "
                "STI-scoped excerpt of Nel et al. and did not read its adverse-event "
                "table. A number this object has not read is a number it must not print."),
            "source_if_it_is_read": (
                "Nel A et al. Safety and Efficacy of a Dapivirine Vaginal Ring for HIV "
                "Prevention in Women. N Engl J Med 2016;375:2133-2143. PMID 27959766, "
                "doi 10.1056/NEJMoa1602046. This object's own "
                "sources/RING_STUDY_NEJMoa1602046.sti_excerpt.txt records the retrieval "
                "route -- a Europe PMC Free PDF -- and the sha256 of the PDF, so the read "
                "is a task and not a search."),
        },
    },
    "⛔_THE_PAGES_OWN_REASON_FOR_NOT_POOLING_IS_WITHDRAWN": {
        "what_it_said": (
            "'THE TWO PLACEBO ARMS DIFFER SEVEN-FOLD ... A seven-fold difference in the "
            "CONTROL arm is a difference in what was counted and reported, not in what "
            "happened.'"),
        "why_it_is_withdrawn": (
            "TWO REASONS, AND THE SECOND IS THE SERIOUS ONE. (1) It infers provenance "
            "from rates, which no ratio can establish. (2) THE SEVEN-FOLD FIGURE IS "
            "ITSELF BUILT ON ONE OF THE TWO DISPUTED NUMBERS: it is 7.16x comparing "
            "registry against registry (9/652 = 1.380% against 130/1316 = 9.878%) and "
            "2.64x when ASPIRE's placebo arm is taken from ASPIRE's own paper (48/1316 = "
            "3.647%). The premise moved by a factor of nearly three the moment the "
            "document was read."),
        "the_decision_not_to_pool_STANDS_on_a_different_reason": (
            "THE ASPIRE INPUT IS NOT ESTABLISHED. Two sources give 116 and 52 for the "
            "same arm over the same denominator and nothing read here says which counts "
            "what. A pool whose largest contributing arm is uncertain by a factor of 2.2 "
            "is not a pool. This reason is checkable from the two documents cited above; "
            "the withdrawn one was checkable from nothing."),
        "and_it_is_still_not_a_safety_verdict": (
            "⚠️ The Ring Study's registry serious-event relative risk of 2.2743 (1.1122 "
            "to 4.6506) excludes 1. It is NOT reported as a harm signal, and the reason "
            "is NOT a rate comparison: it is that the companion trial's counts for the "
            "same outcome are in dispute with its own publication, so the set these two "
            "belong to is not yet established. It is shown because hiding an inconvenient "
            "interval is worse than showing one that needs explaining."),
    },
    "_supersedes": (
        "harms_2026_08_30.serious_adverse_events.⛔_NOT_POOLED.why and "
        "harms_2026_08_30.serious_adverse_events.⛔_NOT_POOLED.and_this_is_not_a_safety_"
        "verdict. Those fields are LEFT IN PLACE and not deleted: the record of what the "
        "page said is part of the correction, and removing it would launder the error. "
        "This block states that they are withdrawn and why."),
}


def main():
    with io.open(OBJ, encoding="utf-8") as fh:
        obj = json.load(fh)
    before = key_paths(obj)

    prior = obj.get("harms_2026_08_30") or {}
    sae = (prior.get("serious_adverse_events") or {}).get("⛔_NOT_POOLED") or {}
    if "SEVEN-FOLD" not in str(sae.get("why", "")):
        print("REFUSING: the field this correction supersedes does not carry the text it "
              "was written against. The page changed underneath; re-read before writing.")
        return 1

    obj["harms_provenance_2026_09_03"] = BLOCK
    # A POINTER AT THE WITHDRAWAL, PLACED WHERE THE WITHDRAWN TEXT IS. A correction the
    # reader only meets if they scroll to a different block is a correction that has not
    # been made -- the withdrawn sentence still reads as the page's reason where it sits.
    sae["⛔_THIS_REASON_IS_WITHDRAWN_2026_09_03"] = (
        "The sentence above infers provenance from two rates, and its seven-fold figure "
        "is computed from a registry count that DISAGREES WITH ITS OWN PUBLICATION "
        "(ASPIRE: registry 130, paper 48). Against the paper the gap is 2.64x, not 7.16x. "
        "See harms_provenance_2026_09_03. THE DECISION NOT TO POOL STANDS; THIS REASON "
        "FOR IT DOES NOT.")

    after = key_paths(obj)
    lost = sorted(before - after)
    if lost:
        print("REFUSED: write would lose %d key path(s): %s" % (len(lost), ", ".join(lost[:5])))
        return 1
    write_json(OBJ, obj)
    print("%s" % TOPIC)
    print("   + harms_provenance_2026_09_03")
    print("   + withdrawal pointer placed ON the withdrawn field")
    print("   ASPIRE serious AEs  registry 116/1313 vs 130/1316  RR %s"
          % BLOCK["ASPIRE_NCT01617096"]["registry"]["rr_serious"]["point"])
    print("                    publication  52/1313 vs  48/1316  RR %s"
          % BLOCK["ASPIRE_NCT01617096"]["publication"]["rr_serious"]["point"])
    print("   deaths 4 vs 3 in BOTH sources; denominators identical in BOTH")
    print("   the seven-fold control-arm claim: 7.16x registry-to-registry, 2.64x against"
          " the paper")
    print("   key paths %d -> %d (+%d)" % (len(before), len(after), len(after) - len(before)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
