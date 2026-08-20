"""inclisiran-lipid-kidney: risk of bias per result, and the third silent selection.

ESTABLISHED FROM ALL THREE REGISTRATIONS, ClinicalTrials.gov API v2, 2026-08-20:

    ORION-9   NCT03397121  n=482    RANDOMIZED  masking DOUBLE [participant, care provider]
                                    arms: Inclisiran | Placebo
    ORION-10  NCT03399370  n=1561   RANDOMIZED  masking DOUBLE [participant, care provider]
                                    arms: Inclisiran | Saline Solution
    ORION-11  NCT03400800  n=1617   RANDOMIZED  masking DOUBLE [participant, care provider]
                                    arms: Inclisiran | Saline Solution

    EACH REGISTERS TWO CO-PRIMARIES:
        1. Percentage Change in LDL-C From Baseline to Day 510
        2. Time-adjusted Percentage Change in LDL-C From Baseline After Day 90 and up to
           Day 540

THIS REVIEW POOLS THE FIRST AND RECORDS NO REASON FOR THE CHOICE -- registry class 66, third
instance in one night, after DECLARE-TIMI 58's dropped co-primary and icosapent's dose arm
selected from three. Three registries, three sponsors, three endpoints, one mechanism.

THE COMPARATOR WORDING IS A FACT, NOT A LABELLING SLIP. ORION-10 and ORION-11 register
"Saline Solution" where ORION-9 registers "Placebo". For a subcutaneous agent a saline
injection IS the sham, so this supports rather than undermines participant masking, and it
is recorded rather than smoothed into a single word.

AND THE MASKING IS DOUBLE, NOT QUADRUPLE. Participant and care provider are masked; the
OUTCOMES ASSESSOR IS NOT among the masked roles on any of the three. For a subjective
outcome that would carry D4; it does not here, and the reason is the endpoint rather than
the design -- see D4 below.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import atomic_write

TOPIC = "inclisiran-lipid-kidney-auto-full-review"
TODAY = "2026-08-20"
OBJ = os.path.join(REPO, "ssot", TOPIC, TOPIC + ".json")

TRIALS = {
    "NCT03397121": ("ORION-9", 482, "Placebo"),
    "NCT03399370": ("ORION-10", 1561, "Saline Solution"),
    "NCT03400800": ("ORION-11", 1617, "Saline Solution"),
}

D1 = {
    "judgement": "LOW",
    "basis": "REGISTRATION DESIGN MODULE, READ",
    "reason": ("allocation: RANDOMIZED is recorded on the design module of all three "
               "registrations, and masking is recorded as DOUBLE."),
    "what_is_NOT_established": (
        "The concealment MECHANISM is not on the registry, and the published reports were "
        "not read. LOW is scored on the recorded allocation, not on a mechanism nobody "
        "here has seen."),
}

D2 = {
    "judgement": "NO_INFORMATION",
    "basis": "NOT ESTABLISHED -- THE REGISTRY DOES NOT CARRY THE FIELD",
    "reason": (
        "Analysis population and handling of deviations are not on the registration. This "
        "is the same shape as icosapent and NOT the same as empagliflozin, where the "
        "methods section exists and is paywalled. The exit is the ORION reports -- Raal "
        "2020 for ORION-9 and Ray 2020 for ORION-10 and ORION-11 -- and neither was read."),
}

D3 = {
    "judgement": "NO_INFORMATION",
    "basis": "NOT ESTABLISHED -- AND THE FOLLOW-UP LENGTH IS WHY IT MATTERS MORE HERE",
    "reason": (
        "The result is a FIXED-TIMEPOINT measurement at DAY 510 -- roughly seventeen "
        "months. A participant who leaves before day 510 has no value at all, and over "
        "seventeen months more of them will. That is a materially larger attrition risk "
        "than icosapent's twelve weeks, on the same kind of endpoint, and neither "
        "registration states how many day-510 values were missing or how they were "
        "handled. THE DOMAIN IS THE SAME, THE MAGNITUDE OF THE THREAT IS NOT."),
}

D4 = {
    "judgement": "LOW",
    "basis": "REGISTRATION DESIGN MODULE AND THE ENDPOINT'S NATURE",
    "reason": (
        "LDL-C is an automated laboratory assay. THE OUTCOMES ASSESSOR IS NOT AMONG THE "
        "MASKED ROLES on any of the three registrations -- masking is DOUBLE, participant "
        "and care provider -- so for a subjective outcome this would not be LOW. It is LOW "
        "because an unmasked assessor has nothing to decide about an automated lipid "
        "value. THE JUDGEMENT RESTS ON THE ENDPOINT, NOT ON THE MASKING, and that is "
        "stated so the next reader does not carry it to a subjective outcome from the same "
        "trials."),
}

D5 = {
    "judgement": "SOME_CONCERNS",
    "basis": "REGISTRATION COMPARED WITH WHAT THIS OBJECT POOLS",
    "reason": (
        "Each trial registers TWO CO-PRIMARIES -- percentage change in LDL-C at day 510, "
        "and the TIME-ADJUSTED percentage change after day 90 up to day 540. This review "
        "pools the first and records no reason. The two are not interchangeable: a single "
        "timepoint at day 510 and a time-adjusted average over a 450-day window answer "
        "different questions about a drug dosed twice yearly, and the second is the one "
        "that reflects the between-dose trough. NOT HIGH: nothing read shows the choice "
        "was made after seeing the data, and asserting that would be the accusing-"
        "direction error."),
}


def main():
    dry = "--apply" not in sys.argv
    obj = json.load(io.open(OBJ, encoding="utf-8"))
    ncts = set(t.get("nct") for t in (obj.get("inputs") or {}).get("trials") or [])
    for nct in TRIALS:
        if nct not in ncts:
            sys.exit("REFUSED: %s is not on this object (%r)." % (nct, sorted(ncts)))

    by_outcome = {"primary": {}}
    for nct, (name, n, comparator) in TRIALS.items():
        by_outcome["primary"][nct] = {
            "nct": nct,
            "trial": name,
            "registered_enrolment": n,
            "registered_comparator": comparator,
            "registered_masking": ("DOUBLE -- participant and care provider; THE OUTCOMES "
                                   "ASSESSOR IS NOT LISTED"),
            "result_assessed": ("percentage change in LDL-C from baseline to DAY 510 -- a "
                                "fixed-timepoint laboratory measurement, and ONE OF TWO "
                                "REGISTERED CO-PRIMARIES"),
            "domains": {
                "D1_randomisation_process": D1,
                "D2_deviations_from_intended_intervention": D2,
                "D3_missing_outcome_data": D3,
                "D4_measurement_of_the_outcome": D4,
                "D5_selection_of_the_reported_result": D5,
            },
            "overall": "SOME_CONCERNS",
            "overall_reason": (
                "D5 SOME_CONCERNS on an unrecorded selection between two registered "
                "co-primaries; D2 and D3 NO_INFORMATION. Overall cannot be LOW while a "
                "domain is SOME_CONCERNS, and cannot be judged further while two are "
                "unread."),
        }

    _rob = {
        "tool": "RoB 2 (Cochrane risk-of-bias tool for randomized trials)",
        "assessed_utc": TODAY,
        "assessed_per": "RESULT, not trial -- Handbook 8.2",
        "by_outcome": by_outcome,
        "sources_read": [
            "ClinicalTrials.gov API v2 NCT03397121 -- ORION-9, n=482, RANDOMIZED, DOUBLE "
            "[participant, care provider], arms Inclisiran | Placebo, TWO co-primaries",
            "ClinicalTrials.gov API v2 NCT03399370 -- ORION-10, n=1561, same design, arms "
            "Inclisiran | Saline Solution, TWO co-primaries",
            "ClinicalTrials.gov API v2 NCT03400800 -- ORION-11, n=1617, same design, arms "
            "Inclisiran | Saline Solution, TWO co-primaries",
        ],
        "sources_NOT_read": (
            "The ORION publications. D2 and D3 are the domains that depend on them."),
        "ceiling": {"statement": "A domain that cannot be judged from the sources READ is NO_INFORMATION, never LOW. Low-by-default asserts a fact; high-by-default invents a defect. Overall is capped at SOME_CONCERNS wherever a domain is NO_INFORMATION.", "shape_note": "A DICT, NOT A STRING. paper_projector does ceil.get('statement'), so a bare string here raises AttributeError and the ENTIRE MANUSCRIPT VANISHES -- 17,012 chars and 27 sections down to a 318-char projector-failed banner."},
        "WHY_THIS_PROFILE_DIFFERS_FROM_ITS_SIBLINGS": (
            "Against empagliflozin: that result is an adjudicated time-to-event composite, "
            "so D3 is LOW because censoring absorbs withdrawal and D4 is LOW because a "
            "blinded committee adjudicates. Against icosapent: the same fixed-timepoint "
            "laboratory shape, but at DAY 510 rather than week 12, so the D3 threat is "
            "materially larger for the same reasoning. D5 is SOME_CONCERNS here for a "
            "DIFFERENT reason than icosapent's -- there a dose arm was selected from "
            "three, here a co-primary was selected from two."),
        "supersedes": (
            "'no risk-of-bias assessment was recoverable from the page this object was "
            "extracted from' -- a sentence about where somebody looked."),
    }
    atomic_write.merge_not_overwrite(obj, "risk_of_bias", _rob,
                                     TODAY.replace("-", "_"))

    blk = obj["results"]["by_outcome"]["primary"]
    blk["POOL_FINDINGS_%s" % TODAY.replace("-", "_")] = {
        "a_two_co_primaries_were_registered_and_one_is_pooled": (
            "ALL THREE TRIALS REGISTER TWO CO-PRIMARY OUTCOMES: percentage change in LDL-C "
            "from baseline to DAY 510, and the TIME-ADJUSTED percentage change after day 90 "
            "up to day 540. This pool uses the first. THE SELECTION IS RECORDED NOWHERE. "
            "The two answer different questions about a drug given twice a year -- a single "
            "timepoint against an average across the dosing interval -- and a review that "
            "selects among registered options without recording the selection has made an "
            "analytic decision that cannot be audited from its own output. The estimate is "
            "not changed here: choosing the other co-primary is a content decision."),
    }

    obj.setdefault("display_change_announced", []).append({
        "date": TODAY,
        "change": "risk of bias assessed per result for all three contributing results",
        "values_moved": "NONE",
        "what_changed": (
            "All three registrations read. D1 and D4 LOW, D2 and D3 NO_INFORMATION, D5 "
            "SOME_CONCERNS because each trial registers two co-primaries and this review "
            "pools one without recording the choice."),
        "why": ("The risk-of-bias limb was previously discharged by a sentence about where "
                "somebody looked."),
    })

    print("inclisiran: 3 results assessed; D5 SOME_CONCERNS (two co-primaries, one pooled)")
    if dry:
        print("DRY RUN -- pass --apply to write")
        return
    atomic_write.write_json(OBJ, obj, indent=1)
    print("wrote %s" % OBJ)


if __name__ == "__main__":
    main()
