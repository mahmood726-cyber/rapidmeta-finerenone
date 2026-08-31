#!/usr/bin/env python3
"""STORE THE k=3 KCCQ POOL, WITH THE ESTIMAND AXIS RECORDED FOR THE FIRST TIME.

WHAT THIS ADDS, and why each part is not optional:

1. STEP-HFpEF DM as a contributing row. It was excluded because ClinicalTrials.gov holds no
   posted results for it -- AACT has ZERO outcome rows for NCT04916470 -- while its KCCQ
   result sits in the NEJM report. That rule is withdrawn: eligibility follows the review
   question, not whether a registry mirrors the paper.

2. A PROVENANCE TIER on every row, per `ssot/provenance_tier.py`. The corpus stored 313
   estimates and 0 declared a tier.

3. THE ESTIMAND AXIS, verbatim AND normalised, on every row. The object asserted
   `estimand_established: True` while containing ZERO occurrences of "treatment policy",
   "trial product", "efficacy estimand" or "on-treatment". It asserted sameness along an axis
   it never recorded.

    ⭐ BOTH FORMS ARE STORED AND NEITHER IS SUFFICIENT ALONE.

   The three trials label one strategy three ways: STEP-HFpEF and STEP-HFpEF DM say
   "treatment policy estimand", SUMMIT says "treatment-regimen estimand".
   `"treatment policy" == "treatment-regimen"` is FALSE and the correct answer is that they
   are THE SAME STRATEGY -- all randomised participants, effect regardless of adherence,
   intercurrent events included. So:
     * the VERBATIM label is stored, because a normalised strategy alone destroys the evidence
       a reader needs to check the normalisation;
     * the NORMALISED strategy is stored, because the verbatim label alone would make any
       future consistency check a string comparison -- the vocabulary-matching defect that has
       produced five false findings in this project in one night.
   What licenses the normalisation is STRUCTURAL, not lexical: each paper contrasts its
   headline figure against an explicitly on-treatment alternative OF ITS OWN
   (trial-product 8.8 and 8.6; efficacy 9.8). A paper that reports both a
   regardless-of-adherence figure and an on-treatment figure has told you which is which
   without needing to share anyone else's vocabulary.

4. THE COUNTERFACTUAL, stored as a number rather than a worry. Pooling each trial's OTHER
   estimand -- 8.8, 9.8, 8.6 -- gives about 9.0 against our 7.38. A 1.6-point shift, ~20%,
   with every individual number remaining quotable and correct. THAT is what estimand mixing
   costs, and it is invisible in the output.

5. THE k=2 GAP CLOSED IN THE SAME WRITE. The two pre-existing rows had no estimand recorded
   either. Fixing only the row I added would leave the defect I am documenting in the object I
   am documenting it in.

CORROBORATION. The estimand labels were established by TWO MODEL FAMILIES searching
independently -- Codex (GPT-5) and agy routed to Gemini 3.1 Pro (High), the routing confirmed
from CLI telemetry rather than from either model's testimony about itself. They agree on both
labels, both alternates and both alternate values. The STEP-HFpEF DM value itself was found by
ONE family plus a source URL and a verbatim quote, and is recorded as such rather than as
adjudicated.

NEVER NET-DELETE. Key paths are counted before and after and the write is refused on any loss.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
OBJ = os.path.join(REPO, "ssot", "incretin-hfpef-review", "incretin-hfpef-review.json")

from merge_rob_grade_into_objects_2026_08_19 import key_paths  # noqa: E402

STRATEGY = {
    "normalised": "REGARDLESS_OF_ADHERENCE",
    "means": ("All randomised participants, the effect estimated regardless of adherence, "
              "with intercurrent events included rather than censored. ICH E9(R1) calls this "
              "the treatment-policy strategy."),
    "why_these_three_are_the_same_strategy": (
        "They are NOT the same words. STEP-HFpEF and STEP-HFpEF DM print 'treatment policy "
        "estimand'; SUMMIT prints 'treatment-regimen estimand'. A string comparison of those "
        "labels returns FALSE and would be wrong. What establishes sameness is STRUCTURAL: "
        "each of the three papers reports, alongside its headline figure, an explicitly "
        "ON-TREATMENT alternative of its own -- trial-product 8.8 (STEP-HFpEF), efficacy 9.8 "
        "(SUMMIT), trial-product 8.6 (STEP-HFpEF DM). A report carrying both a "
        "regardless-of-adherence figure and an on-treatment figure identifies which is which "
        "without sharing anyone else's vocabulary."),
    "established_by": ("Two model families searching independently -- Codex (GPT-5) and agy "
                       "routed to Gemini 3.1 Pro (High). Routing confirmed from the agy CLI's "
                       "own telemetry line `Propagating selected model override to backend: "
                       "label=...`, NOT from either model's report about itself, which is "
                       "testimony whichever field is asked for."),
    "checked_utc": "2026-08-27",
}

ROWS = {
    "NCT04788511": {
        "estimand_verbatim": "treatment policy estimand",
        "on_treatment_alternative": {"label": "trial product estimand", "md_points": 8.8,
                                     "ci_low": 5.9, "ci_high": 11.7, "ci_level": 95},
        "url": "https://www.nejm.org/doi/full/10.1056/NEJMoa2306963",
        "verbatim": ("Analyses are based on the treatment policy estimand, reflect the full "
                     "analysis population, and are from the in-trial period."),
    },
    "NCT04847557": {
        "estimand_verbatim": "treatment-regimen estimand",
        "on_treatment_alternative": {"label": "efficacy (on-treatment) estimand",
                                     "md_points": 9.8, "ci_low": 7.1, "ci_high": 12.5,
                                     "ci_level": 95},
        "url": "https://www.nejm.org/doi/full/10.1056/NEJMoa2410027",
        "verbatim": "The treatment-regimen estimand is the change in the KCCQ-CSS at 52 weeks",
    },
    "NCT04916470": {
        "estimand_verbatim": "treatment policy estimand",
        "on_treatment_alternative": {"label": "trial product estimand", "md_points": 8.6,
                                     "ci_low": 5.6, "ci_high": 11.6, "ci_level": 95},
        "url": "https://www.nejm.org/doi/full/10.1056/NEJMoa2313917",
        "verbatim": "7.3 (4.1 to 10.4)",
    },
}

NEW_ROW = {
    "trial_id": "step-hfpef-dm", "nct": "NCT04916470", "measure": "MEAN_DIFFERENCE",
    "point": 7.3, "ci_low": 4.1, "ci_high": 10.4, "ci_level": 95,
    "estimand_id": "kccq_css_change",
    "population": ("Adults with obesity-related HFpEF AND type 2 diabetes. Full analysis "
                   "population, in-trial period, week 52."),
    "n_treatment": 310, "n_control": 306,
    "endpoint_rank_in_its_own_trial": "a DUAL PRIMARY (co-primary) endpoint of the trial",
    "derivation": ("the mean difference the source prints, stored as printed at the interval "
                   "level the source prints it at"),
}

POOL = {"measure": "MEAN_DIFFERENCE", "point": 7.3837, "ci_low": 5.5051, "ci_high": 9.2624,
        "ci_level": 95, "scale": "linear"}


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    with io.open(OBJ, encoding="utf-8") as fh:
        obj = json.load(fh)
    before = key_paths(obj)
    n_before = len(json.dumps(obj))

    blk = ((obj.get("results") or {}).get("by_outcome") or {}).get("kccq_css_change")
    if blk is None:
        print("REFUSED: kccq_css_change block absent")
        return 1
    rows = blk.get("per_trial") or []
    if any((r.get("nct") or "") == "NCT04916470" for r in rows):
        print("REFUSED: NCT04916470 already present; this script is not idempotent by design "
              "-- inspect before re-running.")
        return 1

    prev_pool = dict(blk.get("pooled") or {})
    prev_k = blk.get("k")

    rows.append(dict(NEW_ROW))
    blk["per_trial"] = rows

    for r in rows:
        n = r.get("nct")
        meta = ROWS.get(n)
        if not meta:
            continue
        r["estimand_axis"] = {
            "verbatim_label": meta["estimand_verbatim"],
            "normalised_strategy": STRATEGY["normalised"],
            "normalised_means": STRATEGY["means"],
            "why_normalisation_is_not_a_string_match":
                STRATEGY["why_these_three_are_the_same_strategy"],
            "the_papers_own_on_treatment_alternative": meta["on_treatment_alternative"],
            "verbatim_quote": meta["verbatim"],
            "url": meta["url"],
            "established_by": STRATEGY["established_by"],
            "checked_utc": STRATEGY["checked_utc"],
        }
        r["provenance"] = {
            "tier": "JOURNAL_FULL_TEXT",
            "pmid_or_doi": meta["url"].split("doi/full/")[-1],
            "accessed_utc": "2026-08-27",
            "locator": "headline KCCQ-CSS result, week 52",
            "corroboration": (
                "TWO FAMILIES on the estimand label (Codex GPT-5 and agy Gemini 3.1 Pro High, "
                "routing confirmed from CLI telemetry). ONE FAMILY on the NCT04916470 VALUE "
                "itself, plus a source URL and a verbatim quote. NOT adjudicated."
                if n == "NCT04916470" else
                "TWO FAMILIES agreeing on the estimand label, the alternate estimand and its "
                "value, searching independently."),
        }

    blk["k"] = 3
    # NEST-MERGE, NEVER REPLACE. The first version of this line was
    # `blk["pooled"] = dict(POOL)`, and the key-path guard refused it: it would have
    # destroyed 14 nested keys under `pooled`, among them `stands_because`, `caveats`,
    # `card_note` and the whole `replaces` block recording the withdrawn odds-ratio analysis.
    #
    #     I WROTE THE GUARD THAT CAUGHT THIS THIS MORNING, FOR THIS EXACT DEFECT, AND THEN
    #     COMMITTED THE DEFECT AGAIN SIX HOURS LATER IN NEW CODE.
    #
    # Which is the argument for the guard rather than for the lesson. A rule you have written
    # is not a rule you have applied.
    #
    # And the keys are not incidental: `stands_because` and `caveats` are where this object
    # ARGUED FOR k=2 -- "THE THIRD TRIAL IS MISSING FOR A PROVENANCE REASON, NOT A CLINICAL
    # ONE ... it is left out because its registry record has no results". That is the rule now
    # being withdrawn, stated in the object's own words. Deleting it would erase the evidence
    # that the exclusion was deliberate and reasoned, and leave the change looking like a
    # correction of an oversight rather than the reversal of a policy.
    for _k, _v in POOL.items():
        blk["pooled"][_k] = _v
    blk["pooled"]["superseded_k2_argument_2026_08_27"] = (
        "The `stands_because` and `caveats` text on this block argues for k=2 and is KEPT "
        "VERBATIM above. It is now superseded, not wrong: it says plainly that STEP-HFpEF DM "
        "'is left out because its registry record has no results, and that is a rule about "
        "where numbers may come from rather than a judgement about the trial', and it "
        "predicted the trial 'would very likely move this estimate very little'. Both were "
        "correct. The rule it obeyed has been withdrawn.")
    blk["pooled"]["interval_note_2026_08_27"] = (
        "The stored interval is the WALD interval, as at k=2. The k=2 caveat records that a "
        "Hartung-Knapp interval on ONE degree of freedom gave -7.74 to 22.60 and included no "
        "effect. At k=3 there are TWO degrees of freedom and that instability is much reduced, "
        "but the Hartung-Knapp interval has NOT been recomputed here and is not claimed. The "
        "k=3 pool is reported on the same basis as the k=2 pool it replaces, which is what "
        "makes the two comparable.")
    blk["pooled_superseded_2026_08_27"] = {
        "previous": prev_pool, "previous_k": prev_k,
        "why": ("STEP-HFpEF DM was excluded because ClinicalTrials.gov holds no posted "
                "results for it. AACT holds ZERO outcome rows for NCT04916470. Its KCCQ "
                "result is in the NEJM report. The registry-results rule is withdrawn: "
                "eligibility follows the review question."),
        "what_changed": ("The POINT barely moves, 7.43 -> 7.38. The INTERVAL narrows from "
                         "+/-2.34 to +/-1.88, a 20% reduction in width, because the added "
                         "trial carries 39% of the weight and agrees with the other two. "
                         "WHAT THE REGISTRY-ONLY RULE WAS COSTING WAS NOT A DIFFERENT "
                         "ANSWER. IT WAS A LESS CERTAIN ONE."),
        "computed_by": ("scripts/pool_incretin_hfpef_kccq_2026_08_27.py, which reproduces the "
                        "previous k=2 pool to four decimals before it is permitted to compute "
                        "k=3. REML random effects, tau2=0, Q=0.142, I2=0%. SE from each "
                        "printed interval at THAT interval's own level; the quantile table "
                        "REFUSES an unrecognised or absent level rather than defaulting to "
                        "1.96."),
        "derived_before_comparison": ("The k=3 value was computed BEFORE any published "
                                      "synthesis was consulted. Only then compared: published "
                                      "A 7.40 (4.90-9.90) differs by -0.016; published B 7.33 "
                                      "(5.84-8.82) by +0.054. Agreement to within 0.05 points "
                                      "is exactly the condition under which a number gets "
                                      "accepted instead of derived."),
    }
    blk["estimand_counterfactual_2026_08_27"] = {
        "if_each_trials_ON_TREATMENT_estimand_had_been_pooled_instead": [8.8, 9.8, 8.6],
        "approximate_pooled_value": 9.0,
        "shift_from_ours": "about +1.6 points, roughly 20%",
        "why_this_is_recorded": (
            "Every one of 8.8, 9.8 and 8.6 is quotable and correct as printed in its own "
            "paper. Pooling them would mix estimands across trials and move the answer by a "
            "fifth, and NOTHING IN THE OUTPUT WOULD SHOW IT. That is the magnitude of the "
            "error class, measured on our own data, having avoided it."),
    }
    blk["estimand_established_qualified_2026_08_27"] = (
        "READ THIS BESIDE `estimand_established`. Until today that flag asserted every "
        "contributing trial measures the same quantity, while this object contained ZERO "
        "occurrences of 'treatment policy', 'trial product', 'efficacy estimand' or "
        "'on-treatment'. It asserted sameness along an axis it did not record. It happened to "
        "be true; nothing in the object made it true, and nothing would have caught it had it "
        "been false. The axis is now recorded per row in `estimand_axis`.")

    after = key_paths(obj)
    lost = sorted(before - after)
    if lost:
        print("REFUSED: write would lose %d key path(s), e.g. %s"
              % (len(lost), ", ".join(lost[:5])))
        return 1
    with io.open(OBJ, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, indent=1))
    print("key paths %d -> %d (+%d), bytes +%d"
          % (len(before), len(after), len(after) - len(before),
             len(json.dumps(obj)) - n_before))
    print("k %s -> 3 ; pooled %s -> %s (%s, %s)"
          % (prev_k, prev_pool.get("point"), POOL["point"], POOL["ci_low"], POOL["ci_high"]))
    print("estimand_axis written on %d of %d rows"
          % (sum(1 for r in rows if "estimand_axis" in r), len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
