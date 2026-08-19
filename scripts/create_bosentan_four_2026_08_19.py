#!/usr/bin/env python3
"""BUILD THE FOUR REVIEWS `bosentan-pah` WAS SPLIT INTO.

Decision and counts: `DECIDED-bosentan-pah-2026-08-19.md`. Every reading has eligible trials, so
every reading is a review -- the empty-question test was set in advance and did not fire.

THREE OF THE FOUR PUBLISH A REFUSAL AND ONE PUBLISHES k=1. That is the whole of what this drug's
registered evidence supports under any reading, and it is a finding about the registrations
rather than a gap in the work:

    A  monotherapy   4 eligible, 2 with results, NOT ONE registering a walk CHANGE or a
                     clinical-worsening outcome. Its anchor trial's registered primaries are
                     the two-word strings "exercise capacity" and "cardiac hemodynamics".
    B  combination   7 eligible, 1 with results. COMPASS-2's own morbidity/mortality result,
                     reported as one trial's result and not as a pool.
    C  not group 1   8 eligible, ZERO with results.
    D  children      2 eligible, both with results, measuring PK and ventilator weaning.

Run: python scripts/create_bosentan_four_2026_08_19.py
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import bos_topic_data as D                                              # noqa: E402

EV = os.path.join(REPO, "evidence", "2026-08-19-batch1")

PROTOCOL = {
    "prespecified": False, "permanently_refused": True,
    "why": ("A protocol specified before data collection is a HISTORICAL FACT ABOUT THE PAST "
            "and cannot be created retrospectively."),
    "what_was_actually_done": ("Eligibility criteria were derived POST HOC on 2026-08-19, when "
                               "`bosentan-pah` was split into four readings."),
    "authority_permitting_it": "MECIR R107, provided they are declared as such.",
    "forward_remedy": "For topics not yet built, register a protocol BEFORE the search.",
}
DUP = {
    "performed": False, "state": "OWED, AND RECORDED AS OWED RATHER THAN DESCRIBED",
    "what_is_owed": "independent duplicate screening by a second reader.",
    "what_was_NOT_done": ("No second model family read this screen. An agreement rate over one "
                          "reader is not an agreement rate."),
}
SIBS = ["bosentan-pah-monotherapy", "bosentan-pah-combination",
        "bosentan-ph-not-group1", "bosentan-pah-children"]


def rob(state_note):
    return {
        "tool": "RoB 2", "state": "NOT_ASSESSED_FOR_THIS_REVIEW",
        "why": ("No result-level RoB 2 assessment has been performed. RECORDED AS UNASSESSED, "
                "NEVER AS ABSENT OF BIAS: an unassessed domain is NOT_ASSESSABLE, not LOW. "
                + state_note),
        "what_would_close_it": "RoB 2 per RESULT for each contributing result.",
    }


def build(topic, title, question, provenance, search, prisma, cascade, extraction,
          eligibility, outcome, result, trials, wq, state, grade):
    o = {
        "app_id": topic, "schema_version": 2, "title": title, "question": question,
        "question_provenance": provenance, "built": "2026-08-19", "build_mode": "AUTHORED",
        "split_provenance": {
            "parent": "bosentan-pah",
            "why_split": ("The parent asked at least four questions under one title and its "
                          "two trials fell on opposite sides of the split -- COMPASS-2 "
                          "(combination) and FUTURE-2 (children, open-label, no control arm, "
                          "primary is growth). See DECIDED-bosentan-pah-2026-08-19.md. P21."),
            "siblings": [s for s in SIBS if s != topic],
            "precedence": D._PRECEDENCE,
        },
        "outcomes": [outcome], "withholding_question": wq,
        "inputs": {"trials": trials}, "config": {"confidence_level": 95},
        "results": {"by_outcome": {outcome["id"]: result}},
        "search": search, "prisma_flow": prisma, "k_cascade": cascade,
        "screening": {
            "search_note": ("Executed 2026-08-19. 57 registrations surfaced by ONE search over "
                            "the drug; the four readings are applied after it, by a stated "
                            "precedence."),
            "eligibility": eligibility,
            "eligibility_provenance": {
                "state": "DERIVED_POST_HOC", "predefined": False, "post_hoc": True,
                "derived": True,
                "predefined_is_false_because": "written 2026-08-19 when the topic was split.",
                "authority_it_satisfies": "MECIR R29/R30/R31.",
                "authority_it_does_NOT_establish": "MECIR C5/C7.",
                "precedence": D._PRECEDENCE,
                "adjudication": D._ADJUDICATION,
            },
            "duplicate_screening": DUP,
        },
        "screening_of_remainder": {"unscreened_remainder": 0,
                                   "adjudication": D._ADJUDICATION},
        "topic_state": state, "risk_of_bias": rob(""), "grade": grade,
        "protocol": PROTOCOL, "sources": {},
        "sources_note": ("Every number is traceable to a ClinicalTrials.gov v2 payload read on "
                         "2026-08-19. No journal article was read for any effect estimate."),
        "extraction": extraction,
    }
    d = os.path.join(REPO, "ssot", topic)
    os.makedirs(d, exist_ok=True)
    dest = os.path.join(d, "%s.json" % topic)
    if os.path.exists(dest) and "--recreate" not in sys.argv:
        raise SystemExit("REFUSED: %s exists. This script CREATES." % dest)
    if os.path.exists(dest):
        with io.open(dest, encoding="utf-8") as fh:
            if json.load(fh).get("build_stamp"):
                raise SystemExit("REFUSED: %s is stamped; MERGE instead." % dest)
    with io.open(dest, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(o, indent=1))
    return dest


def refusing_outcome(oid, name, definition):
    # `definition_note` is REQUIRED by the projector -- it renders it unconditionally beside the
    # definition. Discovered by the page build raising KeyError on all four objects at once,
    # which is the ordinary way this codebase's object contract gets found (see the memory note
    # on build_tabbed's unwritten type contracts).
    return {"id": oid, "name": name, "definition": definition,
            "definition_note": ("This reading registers no shared estimand. The definition "
                                "above names what a pooled outcome WOULD have been, and the "
                                "page reports why there is none rather than leaving the slot "
                                "blank."),
            "measure": "MD", "effect_scale": "natural", "type": "primary",
            "estimand": {"id": oid, "family": "not established", "model": "none"},
            "comparator": "placebo or an inactive control", "comparator_type": "placebo",
            "direction_of_benefit": "higher", "null_value": 0}


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    with io.open(os.path.join(EV, "bosentan_readings_estimand.json"), encoding="utf-8") as fh:
        est = json.load(fh)
    wrote = []

    def wq_for(key, answer):
        rows = est["by_reading"].get(key, [])
        return {
            "asked_on": "2026-08-19",
            "question": est["withholding_question"]["question"],
            "detected_structurally_not_by_keyword":
                est["withholding_question"]["detected_structurally_not_by_keyword"],
            "answer": answer,
            "per_trial": {r["nct"]: {
                "name": r["name"],
                "two_component": "%d rank(s) read; %s" % (
                    r["ranks_read"], "RESULTS POSTED" if r["has_results"] else "no results"),
                "three_component": "; ".join(
                    "[%s] %s" % (h["rank"], h["measure"][:80])
                    for h in (r["walk_change_at_ranks"] + r["worsening_at_ranks"]))
                    or "NO walk-change and NO clinical-worsening outcome at any rank"}
                for r in rows},
        }

    def trials_for(key):
        return [{"id": r["nct"], "nct": r["nct"], "name": r["name"][:60],
                 "enrolled": r["enrolment"], "arms": [],
                 "design": r["status"], "comparator_type": "placebo",
                 "comparator_type_basis": "read from the registration",
                 "by_outcome": {},
                 "registered_primaries": r["registered_primaries"],
                 "has_posted_results": r["has_results"],
                 "registration_read_utc": "2026-08-19",
                 "all_ranks_read_utc": "2026-08-19"}
                for r in est["by_reading"].get(key, [])]

    # ---- A -------------------------------------------------------------------------
    wrote.append(build(
        "bosentan-pah-monotherapy",
        ("Bosentan alone against an inactive control in pulmonary arterial hypertension: four "
         "eligible trials, and not one registering an endpoint this review could pool"),
        ("In adults with WHO group 1 pulmonary arterial hypertension, what is the effect of "
         "bosentan compared with placebo or no active pulmonary vasodilator on exercise "
         "capacity and on clinical worsening?"),
        ("One of the four readings `bosentan-pah` was split into on 2026-08-19. The parent's "
         "question was the OBJECT'S OWN VERDICT with a question mark appended."),
        D.BOSA_SEARCH, D.BOSA_PRISMA, D.BOSA_CASCADE, D.BOSA_EXTRACTION,
        ("POPULATION: adults with WHO group 1 pulmonary arterial hypertension. INTERVENTION: "
         "bosentan as the randomised intervention -- NOT named in an arm description as prior "
         "or background therapy, which is how two records entered other readings wrongly. "
         "COMPARATOR: placebo or no active pulmonary vasodilator; a trial in which a second "
         "PAH-specific drug is part of the contrast belongs to the COMBINATION reading. "
         "ESTIMAND, which governs POOLABILITY and not eligibility: a six-minute walk distance "
         "CHANGE, or a clinical-worsening / morbidity-mortality outcome, at ANY rank. "
         "Criteria are DERIVED POST HOC and say so."),
        refusing_outcome("exercise_or_worsening",
                         "Six-minute walk distance change, or clinical worsening",
                         "Neither endpoint is registered by any eligible trial in this reading."),
        {"k": 4, "estimand_id": "exercise_or_worsening", "model": "none",
         "estimator_used": "not applicable", "comparator_type": "placebo", "poolable": False,
         "poolable_reason": (
             "FOUR TRIALS ARE ELIGIBLE AND NONE REGISTERS AN ENDPOINT THIS REVIEW CAN POOL. "
             "Not one of the four registers a six-minute walk distance CHANGE or a "
             "clinical-worsening outcome at any rank. The two that have posted results "
             "register 'Total Exercise Time on the Exercise Echocardiogram' (n=5, TERMINATED) "
             "and 'Insulin Resistance Profile Change - Triglyceride:HDL Cholesterol Ratio' "
             "(n=2, TERMINATED). AND THE READING'S ANCHOR TRIAL REGISTERS NO MEASURABLE "
             "ENDPOINT AT ALL: EARLY (NCT00091715, n=185) declares the two-word primaries "
             "'exercise capacity' and 'cardiac hemodynamics' -- no measure, no timepoint, no "
             "direction -- and has posted no results. A REVIEW CANNOT POOL A CONSTRUCT."),
         "pooled": {"withdrawn": True, "point": None,
                    "withdrawn_because": "see poolable_reason"},
         "heterogeneity_status": "NOT_ASSESSABLE -- nothing was pooled",
         "and_the_weaker_limb_is_reported_too": (
             "TWO of the four name a walk-distance endpoint AT ALL, as a bare construct with "
             "no change term, timepoint or direction. THE GAP BETWEEN 0 AND 2 IS THE FINDING: "
             "registrations too thin to establish a shared estimand look identical to "
             "registrations that establish one until both limbs are counted. Treating a bare "
             "construct as a change endpoint would be inferring the analysis from the name."),
         "r_output": {"state": "ABSENT_AND_THAT_IS_THE_FINDING",
                      "_why_absent": "k=4 and nothing was pooled, so there is no model call.",
                      "what_would_hold_P6": "an estimand shared by two or more eligible trials."},
         },
        trials_for("A_monotherapy"),
        wq_for("A_monotherapy",
               "NO, AND FOR EVERY ONE OF THE FOUR. Asked at every registered rank before any "
               "pooling decision; not one eligible trial registers a walk CHANGE or a "
               "clinical-worsening outcome."),
        ("REPORTED AS A REFUSAL, WITH A ZERO REMAINDER. Four eligible trials, two with posted "
         "results, and no shared estimand anywhere. This review is complete in its screening "
         "and empty in its synthesis, and the difference matters."),
        {"approach": "GRADE", "by_outcome": {"exercise_or_worsening": {
            "rated": False,
            "why_not": ("Nothing was pooled, so there is no effect estimate whose certainty "
                        "could be rated. Rating it would be certainty about a number this "
                        "review did not produce.")}}}))

    # ---- B -------------------------------------------------------------------------
    wrote.append(build(
        "bosentan-pah-combination",
        ("Bosentan added to established pulmonary arterial hypertension therapy: one trial has "
         "reported, and its design is invisible in the registry's arm fields"),
        ("In adults with pulmonary arterial hypertension already receiving a PAH-specific "
         "therapy, what is the effect of adding bosentan, compared with continuing that "
         "therapy alone, on morbidity and mortality?"),
        ("One of the four readings `bosentan-pah` was split into on 2026-08-19."),
        D.BOSB_SEARCH, D.BOSB_PRISMA, D.BOSB_CASCADE, D.BOSB_EXTRACTION,
        ("POPULATION: adults with pulmonary arterial hypertension. INTERVENTION: bosentan added "
         "to, or combined with, another PAH-specific therapy as the randomised contrast. "
         "COMPARATOR: the background therapy alone. ESTIMAND, which governs POOLABILITY and "
         "not eligibility: a morbidity/mortality or clinical-worsening outcome, or a "
         "six-minute walk distance CHANGE, at ANY rank. "
         "AND THE DEFINING FEATURE OF THIS READING IS NOT A CODED FIELD. Background therapy is "
         "not a registered intervention, so a combination trial can declare exactly what a "
         "monotherapy trial declares. COMPASS-2's arms are `bosentan | placebo` and its "
         "interventions are `['bosentan','placebo']` -- identical in shape to EARLY's. The "
         "design is named only in the official title, and the assignment records that it rests "
         "on TEXT. Criteria are DERIVED POST HOC and say so."),
        {"id": "morbidity_mortality", "name": "Time to first morbidity or mortality event",
         "definition": ("Time to the first confirmed morbidity or mortality event, as each "
                        "trial registers it."),
         "definition_note": ("ONE trial in this reading has posted results, so this definition "
                             "describes COMPASS-2's registered primary and not a harmonised "
                             "estimand across several trials. Six eligible trials have "
                             "reported nothing, so whether they share it is unknown."),
         "measure": "HR", "effect_scale": "log", "type": "primary",
         "estimand": {"id": "morbidity_mortality", "family": "time-to-first-event",
                      "model": "none -- single trial"},
         "comparator": "background PAH therapy alone", "comparator_type": "placebo",
         "direction_of_benefit": "lower", "null_value": 1.0},
        {"k": 7, "estimand_id": "morbidity_mortality", "model": "none -- single trial",
         "estimator_used": "not applicable", "comparator_type": "placebo", "poolable": False,
         "poolable_reason": (
             "SEVEN TRIALS ARE ELIGIBLE AND ONE HAS REPORTED. COMPASS-2 (NCT00303459, n=334) "
             "is the only trial in this reading with posted results; its registered primary is "
             "'Time to First Confirmed Morbidity/Mortality Event up to the End of Treatment' "
             "and it also registers a Week-16 six-minute walk change at secondary rank. The "
             "other six -- 268 participants across five completed or unknown-status trials and "
             "110 in an ongoing sixth -- have posted nothing. k=1 IS A FLOOR AND NOT AN ANSWER, "
             "and this review reports one trial's result AS one trial's result rather than "
             "assembling a pool from a single row."),
         "pooled": {"withdrawn": True, "point": None,
                    "withdrawn_because": "k=1; there is nothing to combine"},
         "single_study_ref": {
             "trial": "COMPASS-2", "nct": "NCT00303459", "enrolled": 334,
             "registered_primary": "Time to First Confirmed Morbidity/Mortality Event up to "
                                   "the End of Treatment",
             "what_this_is": ("ONE TRIAL'S RESULT, REPORTED AS ONE TRIAL'S RESULT. The effect "
                              "estimate itself is NOT extracted onto this object: the posted "
                              "results were not read cell by cell in this pass, and stating a "
                              "hazard ratio here without that reading would be a number with "
                              "no provenance. WHAT IS OWED IS NAMED RATHER THAN GUESSED.")},
         "heterogeneity_status": "NOT_ASSESSABLE -- k = 1",
         "and_the_add_on_design_is_invisible_in_the_arms": (
             "THE ONE DISTINCTION THIS READING TURNS ON IS PRECISELY THE ONE THE REGISTRY DOES "
             "NOT ENCODE. Background therapy is not a registered intervention, so COMPASS-2 -- "
             "a combination trial -- declares exactly what EARLY, a monotherapy trial, "
             "declares: `armGroups: bosentan | placebo`, `interventions: ['bosentan', "
             "'placebo']`. Read from the arms alone the two are indistinguishable, and "
             "COMPASS-2 was first assigned to the MONOTHERAPY reading. A reader will assume "
             "monotherapy versus combination is a coded fact. IT IS NOT."),
         "r_output": {"state": "ABSENT_AND_THAT_IS_THE_FINDING",
                      "_why_absent": "k=1; nothing was pooled.",
                      "what_would_hold_P6": "a second reporting trial in this reading."},
         },
        trials_for("B_add_on"),
        wq_for("B_add_on",
               "YES FOR FOUR OF THE SEVEN, AND ONLY ONE HAS REPORTED. Four register a "
               "clinical-worsening outcome and three a walk change; six have posted no "
               "results, so the shared estimand exists on paper and not in data."),
        ("REPORTED AT k=1, WITH A ZERO REMAINDER AND SIX ELIGIBLE TRIALS THAT HAVE NEVER "
         "REPORTED. This review is not complete and its face says so."),
        {"approach": "GRADE", "by_outcome": {"morbidity_mortality": {
            "rated": False,
            "why_not": ("k=1 and no pooled estimate. GRADE rates the certainty of a body of "
                        "evidence; one trial's result is reported here as one trial's result "
                        "and its own report is where its certainty is judged.")}}}))

    # ---- C -------------------------------------------------------------------------
    wrote.append(build(
        "bosentan-ph-not-group1",
        ("Bosentan in pulmonary hypertension that is not WHO group 1: eight eligible trials and "
         "not one posted result"),
        ("In adults with pulmonary hypertension due to chronic thromboembolic disease, lung "
         "disease, left heart disease, sickle cell disease or sarcoidosis, what is the effect "
         "of bosentan compared with placebo or usual care on exercise capacity and on clinical "
         "worsening?"),
        ("One of the four readings `bosentan-pah` was split into on 2026-08-19. It exists "
         "because a CTEPH trial is not a PAH trial whatever its comparator, and the parent "
         "object held neither."),
        D.BOSC_SEARCH, D.BOSC_PRISMA, D.BOSC_CASCADE, D.BOSC_EXTRACTION,
        ("POPULATION: adults with pulmonary hypertension that is NOT WHO group 1 -- chronic "
         "thromboembolic, lung-disease or hypoxia related, left-heart related, or associated "
         "with sickle cell disease or sarcoidosis. READ FROM THE CODED CONDITION, AND FROM THE "
         "TITLE WHERE THE CODED FIELD NAMES ONLY THE SYNDROME: ASSET-1 and ASSET-2 declare "
         "`conditions: ['Pulmonary Hypertension']` and are titled '...in Sickle Cell Disease "
         "(SCD) Patients', so reading the code alone put both into the WHO-group-1 reading. "
         "INTERVENTION: bosentan as the randomised intervention. COMPARATOR: placebo, usual "
         "care, or another active regimen. ESTIMAND, which governs POOLABILITY and not "
         "eligibility: a walk-distance CHANGE or a clinical-worsening outcome at ANY rank. "
         "Criteria are DERIVED POST HOC and say so."),
        refusing_outcome("exercise_or_worsening",
                         "Six-minute walk distance change, or clinical worsening",
                         "No eligible trial in this reading has posted any result."),
        {"k": 8, "estimand_id": "exercise_or_worsening", "model": "none",
         "estimator_used": "not applicable", "comparator_type": "placebo", "poolable": False,
         "poolable_reason": (
             "EIGHT TRIALS ARE ELIGIBLE AND NOT ONE HAS POSTED A RESULT. Sarcoidosis, "
             "interstitial lung disease, diastolic heart failure, sickle-cell disease twice, "
             "idiopathic pulmonary fibrosis, and a treatment-regimen comparison. Six of the "
             "eight register a walk-distance endpoint and three a clinical-worsening outcome, "
             "SO THE SHARED ESTIMAND EXISTS ON PAPER AND IN NO DATABASE. Two are TERMINATED at "
             "n=14 and n=12 and one was WITHDRAWN at n=0."),
         "pooled": {"withdrawn": True, "point": None,
                    "withdrawn_because": "see poolable_reason"},
         "heterogeneity_status": "NOT_ASSESSABLE -- nothing was pooled",
         "and_this_page_is_a_finding_and_not_a_gap": (
             "Under the remainder reading in PAGE-STANDARD.md, a body of eligible-but-"
             "unreported trials means the query is well aimed and THE FIELD IS STILL IN "
             "FLIGHT. Here it means something sharper: A WHOLE SET OF DISEASE AREAS IN WHICH "
             "THIS DRUG WAS TRIED AND NOTHING WAS EVER REPORTED. All eight are named on this "
             "page with their status and enrolment, because naming them is the result."),
         "r_output": {"state": "ABSENT_AND_THAT_IS_THE_FINDING",
                      "_why_absent": "no eligible trial has posted results.",
                      "what_would_hold_P6": "any one of the eight posting its results."},
         },
        trials_for("C_not_group1"),
        wq_for("C_not_group1",
               "YES ON PAPER FOR SIX OF THE EIGHT, AND IN NO DATABASE. Six register a "
               "walk-distance endpoint and three a clinical-worsening outcome; ZERO have "
               "posted results."),
        ("REPORTED AS A REFUSAL, WITH A ZERO REMAINDER AND EIGHT ELIGIBLE TRIALS THAT HAVE "
         "NEVER REPORTED. The screening is complete; the literature is not."),
        {"approach": "GRADE", "by_outcome": {"exercise_or_worsening": {
            "rated": False,
            "why_not": "No eligible trial has posted a result. There is no evidence to rate."}}}))

    # ---- D -------------------------------------------------------------------------
    wrote.append(build(
        "bosentan-pah-children",
        ("Bosentan in children with pulmonary hypertension: two trials have reported, and they "
         "measure different things"),
        ("In children with pulmonary arterial hypertension or persistent pulmonary hypertension "
         "of the newborn, what is the effect of bosentan compared with placebo or an "
         "alternative regimen on clinical outcomes?"),
        ("One of the four readings `bosentan-pah` was split into on 2026-08-19. The parent "
         "object held FUTURE-2, an open-label paediatric extension with no control arm whose "
         "registered primary is growth."),
        D.BOSD_SEARCH, D.BOSD_PRISMA, D.BOSD_CASCADE, D.BOSD_EXTRACTION,
        ("POPULATION: children. READ FROM THE ELIGIBILITY MODULE AND NOT FROM A MINIMUM AGE: a "
         "paediatric trial is one with NO ADULT STRATUM AT ALL, or a maximum age under 18. "
         "Assigning by `minimumAge < 18` pulled EARLY and COMPASS-2 -- adult trials admitting "
         "adolescents from 12 -- into this reading and out of their own. INTERVENTION: "
         "bosentan as the randomised intervention, and NOT named in an arm description as "
         "background therapy: NCT01824290 records 'All participants were taking endothelin "
         "receptor antagonist (ERA) (such as bosentan...)' on BOTH arms and is adjudicated out. "
         "COMPARATOR: placebo, an alternative regimen, or an alternative dosing schedule. "
         "ESTIMAND, which governs POOLABILITY and not eligibility: any clinical outcome shared "
         "by two or more trials. Criteria are DERIVED POST HOC and say so."),
        refusing_outcome("shared_clinical_outcome", "Any shared clinical outcome",
                         "The two reporting trials share none."),
        {"k": 2, "estimand_id": "shared_clinical_outcome", "model": "none",
         "estimator_used": "not applicable", "comparator_type": "placebo", "poolable": False,
         "poolable_reason": (
             "BOTH ELIGIBLE TRIALS HAVE POSTED RESULTS AND THEY MEASURE DIFFERENT THINGS. "
             "FUTURE-3 (NCT01223352, n=64) compares TWO DOSING REGIMENS and registers "
             "'Dose-corrected Daily Exposure [AUC(0-24c)] to Bosentan' -- a PHARMACOKINETIC "
             "endpoint. The PPHN trial (NCT01389856, n=23, TERMINATED) registers 'Percentage "
             "of Patients With Treatment Failure', 'Time to Complete Weaning From iNO' and "
             "'Time to Complete Weaning From Mechanical Ventilation'. Neither registers a "
             "walk-distance or clinical-worsening outcome and NO ESTIMAND IS SHARED. This is "
             "not a case of unreported data -- both reported, and there is still nothing to "
             "combine."),
         "pooled": {"withdrawn": True, "point": None,
                    "withdrawn_because": "see poolable_reason"},
         "heterogeneity_status": "NOT_ASSESSABLE -- nothing was pooled",
         "and_a_dosing_comparison_is_not_a_drug_comparison": (
             "FUTURE-3 randomises bosentan twice daily against bosentan three times daily. "
             "Every participant receives the drug; the contrast is the SCHEDULE. It is in "
             "scope by population and by intervention and it cannot contribute to a question "
             "about the effect of bosentan against anything else."),
         "r_output": {"state": "ABSENT_AND_THAT_IS_THE_FINDING",
                      "_why_absent": "k=2 and no shared estimand.",
                      "what_would_hold_P6": "an outcome both trials register."},
         },
        trials_for("D_children"),
        wq_for("D_children",
               "NO, AND DECISIVELY. Both trials have posted results and neither registers a "
               "walk change or a clinical-worsening outcome; their primaries are a "
               "pharmacokinetic exposure and ventilator weaning."),
        ("REPORTED AS A REFUSAL, WITH A ZERO REMAINDER. Both eligible trials reported and "
         "share no estimand -- which is a different and stronger statement than 'the data are "
         "not in'."),
        {"approach": "GRADE", "by_outcome": {"shared_clinical_outcome": {
            "rated": False,
            "why_not": "Nothing was pooled; there is no estimate whose certainty to rate."}}}))

    for w in wrote:
        print("wrote %s" % w)
    print("\nA refusal | B k=1 | C refusal | D refusal")
    return 0


if __name__ == "__main__":
    sys.exit(main())
