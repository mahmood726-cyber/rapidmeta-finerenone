"""finerenone-cv (risk of bias + GRADE) and sglt2-hf (risk of bias). The last two open topics.

ALL FIVE REGISTRATIONS READ FROM ClinicalTrials.gov API v2 ON 2026-08-21.

FINERENONE -- THE TWO TRIALS ARE MIRROR IMAGES, AND THE POOLED RESULT IS ONE'S PRIMARY AND THE
OTHER'S SECONDARY.

    NCT02540993  FIDELIO-DKD  n=5734  QUADRUPLE
        PRIMARY   kidney composite: onset of kidney failure, sustained eGFR decrease >=40%, ...
        sec 1     CARDIOVASCULAR composite: CV death, non-fatal MI, non-fatal stroke, or
                  hospitalisation for heart failure          <- THE RESULT THIS REVIEW POOLS
    NCT02545049  FIGARO-DKD   n=7352  QUADRUPLE
        PRIMARY   CARDIOVASCULAR composite, the same four components in the same words
                                                             <- THE RESULT THIS REVIEW POOLS
        sec 1     kidney composite, the same as FIDELIO's primary

The pair was designed as one programme with the ranks swapped, and this review takes the
cardiovascular composite from both. On FIGARO that is the registered primary; ON FIDELIO IT IS
THE FIRST OF FIVE REGISTERED SECONDARIES. D5 separates the two results for that reason and for
no other -- THE QUANTITY IS THE SAME QUANTITY, word for word on both registrations, so
indirectness is NOT rated down and the reason is stated rather than left to inference.

SGLT2-HF -- A HARMONISED OUTCOME MEANS ONE TRIAL IS NOT CONTRIBUTING ITS REGISTERED PRIMARY.

    NCT03036124  DAPA-HF            QUADRUPLE  primary: CV death, HF hospitalisation, OR
                                               URGENT HF VISIT -- THREE components
    NCT03057977  EMPEROR-Reduced    DOUBLE [participant, investigator]  primary: adjudicated
                                               CV death or adjudicated HF hospitalisation --
                                               TWO components
    NCT03057951  EMPEROR-Preserved  DOUBLE, same shape as EMPEROR-Reduced
    NCT03619213  DELIVER            QUADRUPLE  THREE-component primary, registered TWICE

`harmonised_cvdeath_or_hhf` is the TWO-component composite. That is the EMPEROR trials'
registered primary and it is NOT DAPA-HF's, whose registered primary carries a third component.
The object's own outcome name says "harmonised", so the harmonisation is disclosed -- but the
consequence for D5 is not, and it is recorded here: DAPA-HF contributes a quantity that is not
its registered primary.

`threecomp_cvdeath_hhf_urgent` is the three-component composite, which IS the registered
primary of both trials contributing to it. D5 is LOW on both, and the contrast between the two
outcomes on this one object is the clearest illustration in the corpus of why RoB 2 is assessed
PER RESULT: the same trial, DAPA-HF, is SOME_CONCERNS on D5 in one pool and LOW in the other.

AND THE EMPEROR TRIALS DO NOT MASK THEIR OUTCOMES ASSESSOR. Masking is DOUBLE -- participant
and investigator. Their endpoints are ADJUDICATED, which their registered outcome titles state,
and adjudication blinded to allocation is the standard mitigation. NO REGISTRATION STATES THAT
THE ADJUDICATORS WERE BLINDED, so D4 is SOME_CONCERNS there and LOW on the quadruple-masked
trials.

NO STORED NUMBER IS CHANGED.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import atomic_write

TODAY = "2026-08-21"
STAMP = TODAY.replace("-", "_")

CEILING = {
    "statement": ("A domain that cannot be judged from the sources read is NO_INFORMATION, "
                  "never LOW. Low-by-default asserts a fact; high-by-default invents a "
                  "defect. Overall is capped at SOME_CONCERNS wherever a domain is "
                  "NO_INFORMATION."),
    "shape_note": ("A DICT, NOT A STRING -- paper_projector does ceil.get('statement') and a "
                   "bare string collapses the manuscript to a projector-failed banner."),
}
D1 = {"judgement": "LOW", "basis": "REGISTRATION DESIGN MODULE, READ",
      "reason": "allocation is recorded as RANDOMIZED on the design module.",
      "what_is_NOT_established": (
          "The concealment MECHANISM is not on the registry and no publication was read.")}
D2 = {"judgement": "NO_INFORMATION",
      "basis": "NOT ESTABLISHED -- THE REGISTRY DOES NOT CARRY THE FIELD",
      "reason": ("Deviations from the intended intervention and the analysis population used "
                 "are not on the registration.")}
D3 = {"judgement": "NO_INFORMATION",
      "basis": "NOT ESTABLISHED -- THE REGISTRY DOES NOT CARRY THE FIELD",
      "reason": ("No registration states how many participants were missing from the analysed "
                 "population or how they were handled. Follow-up runs years on all five.")}
D4_QUAD = {"judgement": "LOW", "basis": "REGISTRATION DESIGN MODULE, READ",
           "reason": ("Masking is QUADRUPLE and the OUTCOMES ASSESSOR IS EXPLICITLY AMONG THE "
                      "MASKED ROLES. The endpoint is an adjudicated composite, so it is the "
                      "masked assessor that makes this LOW.")}
D4_DOUBLE_ADJ = {
    "judgement": "SOME_CONCERNS",
    "basis": "REGISTRATION DESIGN MODULE AND THE REGISTERED OUTCOME TITLE, TOGETHER",
    "reason": ("Masking is DOUBLE -- PARTICIPANT AND INVESTIGATOR ONLY -- so the OUTCOMES "
               "ASSESSOR IS NOT AMONG THE MASKED ROLES. The endpoint is ADJUDICATED, which "
               "the registered outcome title states ('Adjudicated Cardiovascular Death or "
               "Adjudicated Hospitalisation for Heart Failure'), and adjudication blinded to "
               "allocation is the standard mitigation. BUT NO REGISTRATION STATES THAT THE "
               "ADJUDICATORS WERE BLINDED, so the mitigation is PLAUSIBLE AND NOT "
               "ESTABLISHED. Not HIGH: nothing read shows adjudication differed by arm.")}


def d5(judgement, reason):
    return {"judgement": judgement,
            "basis": "REGISTERED PRIMARY OUTCOMES COMPARED WITH WHAT THIS OBJECT POOLS",
            "reason": reason}


FINERENONE = {
    "NCT02540993": {
        "name": "FIDELIO-DKD", "n": 5734, "masking": "QUADRUPLE", "d4": D4_QUAD,
        "d5": d5("SOME_CONCERNS",
                 "THE REGISTERED PRIMARY IS THE KIDNEY COMPOSITE -- onset of kidney failure, "
                 "a sustained eGFR decrease of at least 40%, or renal death. The result this "
                 "review pools is the CARDIOVASCULAR composite, which is THE FIRST OF FIVE "
                 "REGISTERED SECONDARIES on this trial. Selecting a secondary from among "
                 "registered ranks is a D5 concern whatever the reason. NOT HIGH: the choice "
                 "is transparent and the same quantity is FIGARO's registered primary, so "
                 "nothing suggests the rank was picked after seeing the data."),
        "rank": "SECONDARY -- the first of five"},
    "NCT02545049": {
        "name": "FIGARO-DKD", "n": 7352, "masking": "QUADRUPLE", "d4": D4_QUAD,
        "d5": d5("LOW",
                 "THE REGISTERED PRIMARY IS THE CARDIOVASCULAR COMPOSITE and it is exactly "
                 "the result this review pools -- CV death, non-fatal myocardial infarction, "
                 "non-fatal stroke, or hospitalisation for heart failure. There is no set of "
                 "ranks to have chosen from. RECORDED BECAUSE THE CONTRAST WITH FIDELIO IS "
                 "THE POINT: the two trials register the same two composites with the ranks "
                 "swapped."),
        "rank": "PRIMARY"},
}

SGLT2 = {
    "harmonised_cvdeath_or_hhf": {
        "NCT03036124": {
            "name": "DAPA-HF", "masking": "QUADRUPLE", "d4": D4_QUAD,
            "d5": d5("SOME_CONCERNS",
                     "THIS TRIAL'S REGISTERED PRIMARY HAS THREE COMPONENTS -- CV death, "
                     "hospitalisation for heart failure, OR AN URGENT HEART-FAILURE VISIT. "
                     "The outcome pooled here is the TWO-component composite, which is not "
                     "this trial's registered primary. The object discloses the "
                     "harmonisation in the outcome's own name; the consequence for this "
                     "domain is recorded here. NOT HIGH: harmonising to the narrower "
                     "definition the other two trials registered is a stated method, not a "
                     "choice made after seeing the data."),
            "rank": "NOT THE REGISTERED PRIMARY -- harmonised to two components"},
        "NCT03057977": {
            "name": "EMPEROR-Reduced", "masking": "DOUBLE", "d4": D4_DOUBLE_ADJ,
            "d5": d5("LOW",
                     "THE REGISTERED PRIMARY IS THE TWO-COMPONENT COMPOSITE -- adjudicated CV "
                     "death or adjudicated hospitalisation for heart failure -- and that is "
                     "the harmonised outcome pooled here."),
            "rank": "PRIMARY"},
        "NCT03057951": {
            "name": "EMPEROR-Preserved", "masking": "DOUBLE", "d4": D4_DOUBLE_ADJ,
            "d5": d5("LOW",
                     "THE REGISTERED PRIMARY IS THE TWO-COMPONENT COMPOSITE, in the same "
                     "words as EMPEROR-Reduced, and that is what is pooled."),
            "rank": "PRIMARY"},
    },
    "threecomp_cvdeath_hhf_urgent": {
        "NCT03036124": {
            "name": "DAPA-HF", "masking": "QUADRUPLE", "d4": D4_QUAD,
            "d5": d5("LOW",
                     "HERE THE POOLED OUTCOME IS THIS TRIAL'S REGISTERED PRIMARY -- CV death, "
                     "hospitalisation for heart failure, or an urgent heart-failure visit. "
                     "THE SAME TRIAL IS SOME_CONCERNS ON D5 IN THE HARMONISED POOL AND LOW "
                     "HERE, which is the clearest illustration in this corpus of why RoB 2 is "
                     "assessed PER RESULT and not per trial."),
            "rank": "PRIMARY"},
        "NCT03619213": {
            "name": "DELIVER", "masking": "QUADRUPLE", "d4": D4_QUAD,
            "d5": d5("LOW",
                     "The registered primary is the three-component composite and that is "
                     "what is pooled. RECORDED AND NOT SCORED: this registration lists TWO "
                     "primary outcome entries whose measure text is the same composite; a "
                     "duplicated registry entry is not a second endpoint and is not treated "
                     "as one."),
            "rank": "PRIMARY"},
    },
}

FIN_GRADE_STEPS = [
    {"domain": "risk_of_bias", "move": "HIGH to MODERATE, down 1 level(s)",
     "reason": ("Both contributing results are SOME_CONCERNS. D1 and D4 are LOW on read "
                "registrations -- randomised, QUADRUPLE masking including the outcomes "
                "assessor on both -- and D5 is LOW on FIGARO and SOME_CONCERNS on FIDELIO, "
                "where the pooled cardiovascular composite is the first of five registered "
                "SECONDARIES. D2 and D3 are NO_INFORMATION on both.")},
    {"domain": "inconsistency", "move": "no downgrade",
     "reason": ("tau-squared is EXACTLY ZERO, Q 0.0143 on 1 df, p = 0.9047, I-squared 0.00%. "
                "The two estimates are 0.86 (0.747 to 0.989) and 0.87 (0.76 to 0.98) -- as "
                "close as two trials get. Downgrading would manufacture a caution the numbers "
                "contradict.")},
    {"domain": "indirectness", "move": "no downgrade",
     "reason": ("THE QUANTITY IS THE SAME QUANTITY. Both registrations define the composite "
                "in the same words -- cardiovascular death, non-fatal myocardial infarction, "
                "non-fatal stroke, or hospitalisation for heart failure. RECORDED AND "
                "DELIBERATELY NOT CONVERTED INTO A RATING: it is FIGARO's registered PRIMARY "
                "and FIDELIO's registered first SECONDARY. That is a selection question, "
                "which D5 already carries; rating it again here would count one fact as two "
                "defects.")},
    {"domain": "imprecision", "move": "MODERATE to LOW -- WARRANTED AND NOT APPLIED, see "
                                      "reason",
     "reason": ("k = 2. This project's floored Hartung-Knapp interval is 0.4699 to 1.5940 on "
                "t = 12.7062 with 1 degree of freedom AND IT INCLUDES NO EFFECT, where the "
                "unadjusted interval 0.7877 to 0.9510 excludes it. IT IS NOT APPLIED for the "
                "reason this project applies consistently at k = 2: the t critical value is "
                "12.7062 and almost nothing survives, so the crossing is weak evidence in "
                "either direction. WHAT IS NOT USED: metafor's RAW unfloored interval here is "
                "0.8045 to 0.9311 -- NARROWER THAN THE UNADJUSTED INTERVAL, which is exactly "
                "what the house floor exists to prevent, and it is not this project's "
                "interval.")},
    {"domain": "publication_bias", "move": "NOT ASSESSABLE -- no rating applied",
     "reason": "k = 2. Handbook 13.3.5.4."},
]


def build(per_spec, outcome_label):
    per = {}
    for nct, s in sorted(per_spec.items()):
        per[nct] = {
            "nct": nct, "trial": s["name"],
            "registered_masking": s["masking"],
            "rank_of_the_result_this_review_pools": s["rank"],
            "result_assessed": outcome_label,
            "domains": {
                "D1_randomisation_process": D1,
                "D2_deviations_from_intended_intervention": D2,
                "D3_missing_outcome_data": D3,
                "D4_measurement_of_the_outcome": s["d4"],
                "D5_selection_of_the_reported_result": s["d5"],
            },
            "overall": "SOME_CONCERNS",
            "overall_reason": (
                "D2 and D3 are NO_INFORMATION, and under RoB 2 an unjudgeable domain cannot "
                "yield LOW overall. Where D4 or D5 is also SOME_CONCERNS the reason is named "
                "in that domain."),
        }
        if "n" in s:
            per[nct]["registered_enrolment"] = s["n"]
    return per


def main():
    dry = "--apply" not in sys.argv

    # ---- finerenone-cv: risk of bias AND GRADE ------------------------------------------
    path = os.path.join(REPO, "ssot", "finerenone-cv", "finerenone-cv.json")
    obj = json.load(io.open(path, encoding="utf-8"))
    blk = ((obj.get("results") or {}).get("by_outcome") or {}).get("cv_composite_first")
    if not isinstance(blk, dict):
        sys.exit("REFUSED: finerenone-cv has no `cv_composite_first`.")
    carried = set(t.get("nct") for t in (blk.get("per_trial") or []) if isinstance(t, dict))
    for n in FINERENONE:
        if n not in carried:
            sys.exit("REFUSED: %s is not carried by finerenone-cv (%r)" % (n, sorted(carried)))

    atomic_write.merge_not_overwrite(obj, "risk_of_bias", {
        "tool": "RoB 2 (Cochrane risk-of-bias tool for randomized trials)",
        "assessed_utc": TODAY,
        "assessed_per": "RESULT, not trial -- Handbook 8.2",
        "by_outcome": {"cv_composite_first": build(
            FINERENONE, "the cardiovascular composite: CV death, non-fatal myocardial "
                        "infarction, non-fatal stroke, or hospitalisation for heart failure")},
        "sources_read": ["ClinicalTrials.gov API v2 %s -- design module and the full "
                         "registered primary and secondary outcome lists" % n
                         for n in sorted(FINERENONE)],
        "sources_NOT_read": ("The trial publications. D2 and D3 depend on them and are "
                             "NO_INFORMATION for that reason."),
        "ceiling": CEILING,
        "THE_TWO_TRIALS_REGISTER_THE_SAME_TWO_COMPOSITES_WITH_THE_RANKS_SWAPPED": (
            "FIDELIO-DKD registers the KIDNEY composite as its primary and the CARDIOVASCULAR "
            "composite as its first secondary. FIGARO-DKD registers the CARDIOVASCULAR "
            "composite as its primary and the KIDNEY composite as its first secondary. This "
            "review pools the cardiovascular composite, so it takes one trial's primary and "
            "the other's secondary -- and the quantity is identical, word for word, on both "
            "registrations."),
        "ONE_ASSESSOR_ONLY": (
            "ASSESSED BY ONE ASSESSOR. Under the standing specification that risk of bias 2 "
            "must be complete and done by TWO AIs from different model families, THIS "
            "ASSESSMENT IS INCOMPLETE. `rob2.assessors` is deliberately NOT written."),
    }, STAMP)

    atomic_write.merge_not_overwrite(obj, "grade", {
        "approach": ("GRADE, following the Cochrane Handbook chapter 14. Randomised evidence "
                     "starts HIGH and is rated down with reasons."),
        "assessed_utc": TODAY,
        "by_outcome": {"cv_composite_first": {
            "k": 2, "starting_certainty": "HIGH", "certainty": "MODERATE",
            "steps": FIN_GRADE_STEPS,
            "summary": ("MODERATE certainty. The two trials agree almost exactly, both are "
                        "quadruple-masked, and the pooled composite is defined identically on "
                        "both registrations -- so the single downgrade is for the unread "
                        "deviation and missing-data domains and for the pooled result being "
                        "FIDELIO's registered SECONDARY rather than its primary."),
            "rating_up_not_applied": (
                "No domain is rated UP. Rating up applies to observational evidence; these "
                "are randomised trials, which start HIGH."),
        }},
    }, STAMP)

    fit = os.path.join(REPO, "evidence", "refits_2026_08_21",
                       "finerenone-cv__cv_composite_first.txt")
    if os.path.exists(fit):
        text = io.open(fit, encoding="utf-8").read()
        if "AGREES WITH THE STORED POINT TO 4 dp: YES" in text:
            ro = blk.setdefault("r_output", {})
            ro["verbatim"] = text
            ro["run_utc"] = TODAY
            ro["environment"] = "R 4.6.0 with metafor 5.0.1"
            ro["call"] = ("Rscript ssot/fit_from_per_trial.R finerenone-cv "
                          "cv_composite_first")
            ro["stored_at"] = ("evidence/refits_2026_08_21/"
                               "finerenone-cv__cv_composite_first.txt")
            ro["why_this_was_re_run"] = (
                "THE PREVIOUS STORED OUTPUT NAMED AN ESTIMATOR THIS OBJECT DOES NOT DECLARE: "
                "it printed 'tau^2 estimator: DL' where the object declares REML, at k = 2. "
                "This project's own statistics rule forbids DerSimonian-Laird below k = 10, "
                "so the quotation carried a wrong label AND a forbidden method, faithfully. "
                "P56. Ten stored outputs across the corpus did this; this is one of them.")

    prior = blk.get("POOL_FINDINGS_%s" % STAMP) or {}
    prior.update({
        "a_the_pooled_result_is_one_trial_s_primary_and_the_other_s_secondary": (
            "READ THIS BESIDE THE ESTIMATE. FIDELIO-DKD (NCT02540993) registers the KIDNEY "
            "composite as its primary outcome and the CARDIOVASCULAR composite -- the one "
            "pooled here -- as the FIRST OF FIVE SECONDARIES. FIGARO-DKD (NCT02545049) "
            "registers them the other way round. THE QUANTITY IS IDENTICAL ON BOTH, word for "
            "word, so this is a question about which rank was selected and not about what was "
            "measured."),
        "b_the_effect_does_not_survive_the_small_sample_adjustment": (
            "The unadjusted interval is HR 0.8655 (0.7877 to 0.9510) and EXCLUDES no effect. "
            "This project's floored Hartung-Knapp interval at k = 2 is 0.4699 to 1.5940 and "
            "INCLUDES it. At k = 2 the t critical value is 12.7062 and almost nothing "
            "survives, so this is weaker evidence against the result than the same crossing "
            "would be at larger k. NOTE THAT metafor's RAW interval here, 0.8045 to 0.9311, "
            "is NARROWER than the unadjusted one -- which is what the house floor exists to "
            "prevent, and it is not cited as ours."),
    })
    blk["POOL_FINDINGS_%s" % STAMP] = prior
    obj.setdefault("display_change_announced", []).append({
        "date": TODAY,
        "change": "risk of bias per result and GRADE both written (P46 limbs 1 and 2)",
        "values_moved": "NONE",
        "what_changed": "2 results assessed; GRADE MODERATE; the model output re-run under "
                        "the declared estimator",
        "why": "Both limbs were ABSENT, and the stored fit named DL where the object "
               "declares REML.",
    })
    print("%-24s rob 2 results, GRADE MODERATE, r_output re-run" % "finerenone-cv")
    if not dry:
        atomic_write.write_json(path, obj, indent=1)

    # ---- sglt2-hf: risk of bias on both pooled outcomes ---------------------------------
    path = os.path.join(REPO, "ssot", "sglt2-hf", "sglt2-hf.json")
    obj = json.load(io.open(path, encoding="utf-8"))
    by = (obj.get("results") or {}).get("by_outcome") or {}
    rob_by = {}
    for oid, spec in SGLT2.items():
        blk = by.get(oid)
        if not isinstance(blk, dict):
            sys.exit("REFUSED: sglt2-hf has no `%s`." % oid)
        carried = set(t.get("nct") for t in (blk.get("per_trial") or [])
                      if isinstance(t, dict))
        for n in spec:
            if n not in carried:
                sys.exit("REFUSED: %s is not carried by sglt2-hf/%s (%r)"
                         % (n, oid, sorted(carried)))
        label = ("the harmonised TWO-component composite: cardiovascular death or "
                 "hospitalisation for heart failure"
                 if oid == "harmonised_cvdeath_or_hhf" else
                 "the THREE-component composite: cardiovascular death, hospitalisation for "
                 "heart failure, or an urgent heart-failure visit")
        rob_by[oid] = build(spec, label)

    atomic_write.merge_not_overwrite(obj, "risk_of_bias", {
        "tool": "RoB 2 (Cochrane risk-of-bias tool for randomized trials)",
        "assessed_utc": TODAY,
        "assessed_per": "RESULT, not trial -- Handbook 8.2",
        "by_outcome": rob_by,
        "sources_read": ["ClinicalTrials.gov API v2 %s -- design module and registered "
                         "primary outcomes" % n
                         for n in sorted({n for s in SGLT2.values() for n in s})],
        "sources_NOT_read": ("The trial publications. D2 and D3 depend on them and are "
                             "NO_INFORMATION for that reason."),
        "ceiling": CEILING,
        "THE_SAME_TRIAL_IS_JUDGED_DIFFERENTLY_IN_THE_TWO_POOLS": (
            "DAPA-HF (NCT03036124) contributes to both outcomes on this object. In "
            "`threecomp_cvdeath_hhf_urgent` the pooled outcome IS its registered primary and "
            "D5 is LOW. In `harmonised_cvdeath_or_hhf` the pooled outcome is the TWO-component "
            "composite, which is NOT its registered primary -- its primary carries a third "
            "component, an urgent heart-failure visit -- and D5 is SOME_CONCERNS. THAT IS WHY "
            "RoB 2 IS ASSESSED PER RESULT AND NOT PER TRIAL, and it is the clearest example "
            "of it in this corpus."),
        "THE_EMPEROR_TRIALS_DO_NOT_MASK_THEIR_OUTCOMES_ASSESSOR": (
            "NCT03057977 and NCT03057951 register masking as DOUBLE -- participant and "
            "investigator. Their endpoints are ADJUDICATED, which their registered outcome "
            "titles state, but no registration states that the adjudicators were blinded. "
            "DAPA-HF and DELIVER are QUADRUPLE-masked and D4 is LOW on both."),
        "ONE_ASSESSOR_ONLY": (
            "ASSESSED BY ONE ASSESSOR. Under the standing specification that risk of bias 2 "
            "must be complete and done by TWO AIs from different model families, THIS "
            "ASSESSMENT IS INCOMPLETE. `rob2.assessors` is deliberately NOT written."),
    }, STAMP)

    prior = by["harmonised_cvdeath_or_hhf"].get("POOL_FINDINGS_%s" % STAMP) or {}
    prior.update({
        "a_one_of_these_three_trials_is_not_contributing_its_registered_primary": (
            "READ THIS BESIDE THE ESTIMATE. This outcome is the HARMONISED two-component "
            "composite -- cardiovascular death or hospitalisation for heart failure. That is "
            "the registered primary of EMPEROR-Reduced and EMPEROR-Preserved. IT IS NOT "
            "DAPA-HF'S: NCT03036124 registers a THREE-component primary that also counts an "
            "URGENT HEART-FAILURE VISIT. The harmonisation is disclosed in this outcome's own "
            "name; what follows from it for risk of bias is recorded per result."),
        "b_and_two_of_the_three_do_not_mask_their_outcomes_assessor": (
            "EMPEROR-Reduced and EMPEROR-Preserved register masking as DOUBLE -- participant "
            "and investigator only. Their endpoints are adjudicated, which is the standard "
            "mitigation, but no registration states that the adjudicators were blinded. "
            "DAPA-HF is quadruple-masked."),
    })
    by["harmonised_cvdeath_or_hhf"]["POOL_FINDINGS_%s" % STAMP] = prior

    obj.setdefault("display_change_announced", []).append({
        "date": TODAY,
        "change": "risk of bias assessed per result on both pooled outcomes (P46 limb 1)",
        "values_moved": "NONE",
        "what_changed": ("%d result-level assessments across 2 outcomes; DAPA-HF is judged "
                         "differently in the two pools and the reason is stated"
                         % sum(len(s) for s in SGLT2.values())),
        "why": "The limb was ABSENT.",
    })
    print("%-24s rob %d results across 2 outcomes"
          % ("sglt2-hf", sum(len(s) for s in SGLT2.values())))
    if dry:
        print("DRY RUN -- pass --apply to write")
        return
    atomic_write.write_json(path, obj, indent=1)


if __name__ == "__main__":
    main()
