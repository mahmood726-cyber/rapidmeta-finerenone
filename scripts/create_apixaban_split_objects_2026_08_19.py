#!/usr/bin/env python3
"""BUILD THE TWO OBJECTS `apixaban-vte` WAS SPLIT INTO, EACH CARRYING WHAT THE OTHER LACKS.

The split itself was decided and recorded on 2026-08-19 (P21: an ambiguous question is built as
several reviews, never chosen between). Its per-topic search, PRISMA and cascade have been on
file at `ssot/apx_split_topic_data.py` since. WHAT WAS MISSING WAS THE ARITHMETIC, and on the
treatment side the arithmetic changed the answer twice over.

WHAT EACH OBJECT NOW SAYS THAT A FINISHED-LOOKING PAGE WOULD NOT.

TREATMENT
  * ELEVEN eligible poolable trials were recovered from a remainder this object did not hold.
    EIGHT have posted results. EIGHT report an outcome NAMED for recurrent VTE. THREE POOL.
    The fall from eight to three is not attrition; it is the difference between reading names
    and reading definitions, itemised trial by trial with every failing axis named.
  * The two largest trials in the field -- AMPLIFY (5,244 analysed) and AMPLIFY-EXT (2,482) --
    CONTRIBUTE TO NO POOL THIS REVIEW REPORTS, because neither posts a recurrent-VTE measure
    without a death term at any of its twenty-one and twenty-two registered ranks.
  * They DO share an estimand with each other, and are still not pooled: one randomises against
    enoxaparin/warfarin and the other against PLACEBO. That pool is computed and declined.
    ESTIMAND COHERENCE IS NECESSARY AND IT IS NOT SUFFICIENT.
  * A prediction was stated before the run and HELD: the estimand-COHERENT pool is the MORE
    heterogeneous one (I2 93.5% against 76.4%). Sixth measurement for P36 and the first in
    which coherence and heterogeneity point in opposite directions on the same page.

PROPHYLAXIS
  * The re-pool computed on 2026-08-19 is carried onto the object at last: four trials and
    13,570 participants on the estimand all four register at SECONDARY rank, replacing a page
    that reported ONE trial's SAFETY result as its answer.
  * Its DerSimonian-Laird estimator is recorded as OWED a correction, because its sibling built
    the same night uses Paule-Mandel at k=4 and a silent divergence between two pages built
    from one search is exactly the kind of thing that is never noticed again.

AND THE BOUNDARY CRITERION IS ON BOTH, which is the point of this script as much as the pools.
It decided which review sixteen trials belong to and it lived in an adjudication file. A rule
that decides inclusion and is published nowhere is not a criterion; it is a habit.

Run: python scripts/create_apixaban_split_objects_2026_08_19.py
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import apx_split_topic_data as D                                          # noqa: E402

EV = os.path.join(REPO, "evidence", "2026-08-19-batch1")
T_TOPIC = "apixaban-vte-treatment"
P_TOPIC = "apixaban-vte-prophylaxis"


def load(name):
    with io.open(os.path.join(EV, name), encoding="utf-8") as fh:
        return json.load(fh)


PROTOCOL = {
    "prespecified": False,
    "permanently_refused": True,
    "why": ("A protocol specified before data collection is a HISTORICAL FACT ABOUT THE PAST "
            "and cannot be created retrospectively. Writing one now and calling it "
            "prespecified would invalidate every other refusal on this page, because a reader "
            "who caught it would be right to disbelieve all of them."),
    "what_was_actually_done": ("Eligibility criteria were derived POST HOC when `apixaban-vte` "
                               "was split in two on 2026-08-19, after the parent object's "
                               "included set existed. The derivation is recorded element by "
                               "element in `screening.eligibility`, and the criterion that "
                               "separates this review from its sibling is stated in full at "
                               "`screening.boundary_criterion`."),
    "authority_permitting_it": ("MECIR R107 permits post-hoc eligibility criteria PROVIDED "
                                "THEY ARE DECLARED AS SUCH. They are declared, here and on the "
                                "page."),
    "forward_remedy": ("For topics not yet built, a protocol is to be written and registered "
                       "BEFORE the search is executed. It is never to be made true "
                       "retroactively for a built topic."),
}

DUPLICATE_SCREENING_OWED = {
    "performed": False,
    "state": "OWED, AND RECORDED AS OWED RATHER THAN DESCRIBED",
    "what_is_owed": ("Independent duplicate screening of the surfaced set by a second reader. "
                     "The mechanical screen and the sixteen-trial adjudication were performed "
                     "by ONE family (Claude), with the registry payload as the evidence."),
    "what_was_NOT_done": ("No second model family read this topic's screen. The 2026-08-19 "
                          "cross-family adjudications covered the ablation and rhythm topics; "
                          "this topic was not among them."),
    "why_it_is_not_reported_as_a_rate": ("An agreement rate over one reader is not an "
                                         "agreement rate. A seat that did not read is ABSENT, "
                                         "not concurring -- the rule that keeps 88 trials off "
                                         "`early-rhythm-control-af`'s adjudicated count."),
}


def rob2_for(pool_rows):
    """RoB 2 per RESULT for the three results that contribute to the reported pool.

    Every domain that cannot be judged from the registration and the posted results is
    NO_INFORMATION or SOME_CONCERNS, never LOW-by-default. The ceiling below is the same one
    stated on the seven pages built earlier tonight and it is a bound on OUR ACCESS.
    """
    return {
        "tool": "RoB 2 (Cochrane risk-of-bias tool for randomized trials)",
        "version": "22 August 2019 version, as reproduced in the Cochrane Handbook",
        "handbook": ("Higgins JPT, Savovic J, Page MJ, Elbers RG, Sterne JAC. Chapter 8: "
                     "Assessing risk of bias in a randomized trial. In: Cochrane Handbook for "
                     "Systematic Reviews of Interventions version 6.5.1"),
        "unit_of_assessment": ("A RESULT, not a study -- Handbook 8.2. Every judgement below "
                               "names the outcome it is about, and for two of the three that "
                               "outcome is a SECONDARY."),
        "default_rule": ("A domain that cannot be judged from the registration and the posted "
                         "results is NO_INFORMATION, never LOW. Low-by-default asserts a fact; "
                         "high-by-default invents a defect."),
        "ceiling": {
            "no_result_can_reach_LOW": True,
            "statement": ("NO RESULT IN THIS REVIEW CAN REACH LOW RISK OF BIAS ON THE EVIDENCE "
                          "WE CAN REACH, AND THAT IS A FACT ABOUT OUR ACCESS RATHER THAN ABOUT "
                          "THE TRIALS. D1 needs allocation concealment and baseline data, held "
                          "for none of them; D5 needs each trial's statistical analysis plan, "
                          "held for none of them. SOME CONCERNS IS THE CEILING, NOT A FINDING."),
            "what_would_change_it": ("Retrieving each trial's full published report and its "
                                     "statistical analysis plan or protocol."),
        },
        "and_one_domain_here_is_worse_than_the_ceiling": (
            "D5 is SOME CONCERNS for every result in this review and for TWO OF THE THREE it "
            "carries an extra reason that is OURS: the result used is a SECONDARY outcome that "
            "THIS REVIEW selected from among the trial's registered ranks. The selection was "
            "made by a stated rule -- the shared estimand, chosen before any result was read -- "
            "and it is still a selection, and it is named rather than left for a reader to "
            "notice."),
        "by_result": pool_rows,
    }


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    repool = load("apixaban_treatment_repool.json")
    estimand = load("apixaban_treatment_estimand.json")
    extraction = load("apixaban_treatment_extraction.json")
    adjud = load("apixaban_adjudication.json")
    screen = load("apixaban_split_screening.json")
    prop = load("apixaban_prophylaxis_repool.json")

    rep = repool["estimand_reported"]
    hks = rep["PM"]["hksj"]

    # ==================================================================================
    # A -- TREATMENT
    # ==================================================================================
    t_trials = []
    by_nct = {r["trial"]: r for r in rep["per_trial"]}
    NCT_OF = {"CARAVAGGIO": "NCT03045406", "COBRRA": "NCT03266783",
              "Japanese acute DVT/PE study": "NCT01780987"}
    for name, nct in NCT_OF.items():
        r = by_nct[name]
        s = repool["coherence_screen"][nct]
        t_trials.append({
            "id": nct, "nct": nct, "name": name,
            "arms": [
                {"label": "Apixaban", "role": "treatment",
                 "events": r["events_apixaban"], "participants": r["n_apixaban"]},
                {"label": s["comparator_class"], "role": "control",
                 "events": r["events_comparator"], "participants": r["n_comparator"]},
            ],
            "design": s["randomised"],
            "comparator_type": "active",
            "comparator_type_basis": ("Every trial in the pool this review reports randomises "
                                      "apixaban against ANOTHER ANTICOAGULANT. The trials that "
                                      "randomise against placebo are eligible and are reported "
                                      "separately, never averaged in."),
            "enrolled": r["n_apixaban"] + r["n_comparator"],
            "by_outcome": {"recurrent_vte": {
                "effect": {"measure": "RR", "point": r["rr"], "ci_low": r["ci_low"],
                           "ci_high": r["ci_high"], "ci_level": 95, "scale": "log",
                           "derived_from": "arm-level event counts posted by the trial",
                           "derivation_note": (
                               "The risk ratio and its interval are DERIVED from the arm-level "
                               "counts, which are READ. Neither the ratio nor the interval is "
                               "claimed to appear in any source."
                               + ("  A 0.5 continuity correction is applied to BOTH arms "
                                  "because one cell is zero; it is applied for that reason and "
                                  "for no other, an unconditional correction biasing the ratio "
                                  "toward the null."
                                  if r["continuity_corrected"] else ""))},
                "provenance": {
                    "tag": "MEASURED",
                    "source_id": nct,
                    "source": "ClinicalTrials.gov posted results, read 2026-08-19",
                    "source_outcome_title": rep["titles_read"][nct],
                    "source_quotes": [
                        rep["titles_read"][nct],
                        rep["sources_read"][nct],
                    ],
                    "quote_note": ("Two quotes: the endpoint TITLE as the registry posts it, "
                                   "and the arm-level counts as the registry posts them. The "
                                   "first says what was counted and the second says what "
                                   "happened, and this review exists partly because eight "
                                   "trials' titles agreed while what they counted did not."),
                },
                "analysed": {"treatment": r["n_apixaban"], "control": r["n_comparator"]},
                "outcome_definition": rep["titles_read"][nct],
                "outcome_definition_source": {
                    "source": "registry results section",
                    "source_field": "resultsSection.outcomeMeasuresModule.outcomeMeasures[]",
                    "source_url": "https://clinicaltrials.gov/study/%s" % nct,
                    "read_utc": "2026-08-19"},
                "counts_read_from": rep["sources_read"][nct],
                "endpoint_rank_in_its_own_trial": (
                    "PRIMARY" if nct == "NCT03045406" else "SECONDARY"),
                "source_tier": "registry_posted_results",
            }},
            "registration_read_utc": "2026-08-19",
            "all_ranks_read_utc": "2026-08-19",
        })

    # The trial the parent included, kept and named rather than dropped. A trial that fails
    # only at the POOLING step is a fact about this review's evidence base; dropping it would
    # erase the fact and leave k=3 looking like the whole of what was found.
    t_trials.append({
        "id": "NCT02829957", "nct": "NCT02829957", "name": "RAMBLE",
        "arms": [],
        "design": ("randomised, rivaroxaban against apixaban in heavy menstrual bleeding on "
                   "anticoagulation; BOTH arms typed ACTIVE_COMPARATOR, so apixaban is not "
                   "the declared intervention"),
        "comparator_type": "active",
        "comparator_type_basis": "rivaroxaban, another direct oral anticoagulant.",
        "enrolled": 19,
        "contributes_to_no_pool": {
            "state": "ELIGIBLE, NOT POOLABLE",
            "why": ("n=19, and its registered primary is a PICTORIAL MENSTRUAL BLOOD-LOSS "
                    "CHART (PBAC score). It is in scope by population and by intervention and "
                    "it reports nothing on this review's estimand at any rank."),
            "why_it_is_kept": ("It is the trial the parent object included on this side of the "
                               "split. Dropping it would make k=3 read as everything this "
                               "review found, and would erase the fact that the review's only "
                               "pre-existing trial cannot answer its own question."),
        },
        "by_outcome": {},
        "registration_read_utc": "2026-08-19",
        "all_ranks_read_utc": "2026-08-19",
    })

    t_obj = {
        "app_id": T_TOPIC,
        "schema_version": 2,
        "title": ("Apixaban for the treatment of venous thromboembolism: eight trials report "
                  "an outcome named for recurrent VTE, and three of them count the same thing"),
        "question": ("In adults with acute or recent venous thromboembolism, what is the "
                     "effect of apixaban compared with conventional anticoagulation, another "
                     "direct oral anticoagulant, or placebo on recurrent venous "
                     "thromboembolism and on bleeding?"),
        "question_provenance": (
            "One of the two readings `apixaban-vte` was split into on 2026-08-19. The parent's "
            "question was the OBJECT'S OWN VERDICT with a question mark appended -- 'NOT "
            "POOLABLE AS POSED...?' -- which no lint could see because the string appears in no "
            "registry record. Both readings are built; neither was chosen over the other."),
        "built": "2026-08-19",
        "build_mode": "AUTHORED",
        "split_provenance": {
            "parent": "apixaban-vte",
            "why_split": ("The parent asked one question of two evidence bases of almost equal "
                          "size -- 34 trials coded TREATMENT and 33 coded PREVENTION -- and "
                          "its two included trials fall on opposite sides. See "
                          "BLOCKED-apixaban-vte-2026-08-19.md. P21."),
            "siblings": [P_TOPIC],
            "shared_trials": {
                "with_" + P_TOPIC: [],
                "computed_over": ("this object's included NCT set intersected with the "
                                  "sibling's, both read from the objects rather than asserted"),
                "why_empty_is_a_result_and_not_a_blank": (
                    "The boundary criterion assigns every trial to exactly one of the two "
                    "reviews, so the intersection is EMPTY BY CONSTRUCTION and the emptiness "
                    "is computed rather than left as a bare `[]`. P17. The corpus-level "
                    "consequence is the good one: summing k across these two topics does NOT "
                    "double-count, which is the opposite of the ablation split's situation."),
            },
        },
        "outcomes": [{
            "id": "recurrent_vte",
            "name": ("Recurrent symptomatic venous thromboembolism -- nonfatal deep vein "
                     "thrombosis or nonfatal pulmonary embolism -- with NO death term"),
            "definition": rep["definition"],
            "restriction": rep["restriction"],
            "definition_note": (
                "THE DEATH TERM IS PART OF THE DEFINITION AND NOT A DETAIL. Five of the eleven "
                "trials register a primary composite carrying one, and they do not carry the "
                "SAME one: AMPLIFY counts VTE-related death, AMPLIFY-EXT counts ALL-CAUSE "
                "death. Same sponsor, same programme, sequential trials, names differing by a "
                "hyphenated suffix."),
            "measure": "RR", "effect_scale": "log", "type": "binary",
            "estimand": {"id": "recurrent_vte", "family": "binary risk",
                         "model": "random-effects, Paule-Mandel",
                         "unit_of_analysis": "participant, first recurrent event",
                         "case_definition": rep["definition"]},
            "comparator": "another anticoagulant",
            "comparator_type": "active",
            "direction_of_benefit": "lower", "null_value": 1.0,
        }],
        "withholding_question": {
            "asked_on": "2026-08-19",
            "question": estimand["withholding_question"]["question"],
            "answer": "YES AT EVERY RANK, AND THE ANSWER DOES NOT SETTLE POOLABILITY",
            "n_with_the_outcome_at_some_rank": 9,
            "n_of_those_with_posted_results": 8,
            "n_that_actually_pool": rep["k"],
            "what_asking_it_bought_and_what_it_did_not": (
                "IT BOUGHT THE REVIEW ITS ENTIRE POOL. All three contributing results were "
                "found by asking at every rank: two of the three are SECONDARY outcomes in "
                "trials whose registered PRIMARY is a bleeding endpoint, so a review reading "
                "primaries only would have reported that they contribute nothing. IT DID NOT "
                "BUY POOLABILITY: eight trials answered yes and five of the eight still do not "
                "pool, each for a named reason. The prophylaxis half of this pair ran the "
                "identical discipline and its poolable set went 3 -> 8. HERE IT WENT 8 -> 3. "
                "THE METHOD HAS NO DIRECTION -- asking is not a way of finding more trials, it "
                "is a way of finding out."),
            "per_trial_ranks_read": {t["nct"]: t.get("ranks_read")
                                     for t in estimand["trials_with_the_shared_outcome"]},
        },
        "inputs": {"trials": t_trials},
        "config": {"confidence_level": 95},
        "results": {"by_outcome": {"recurrent_vte": {
            "k": rep["k"],
            "estimand_id": "recurrent_vte",
            "model": "random-effects",
            "estimator": "Paule-Mandel",
            "estimator_used": "Paule-Mandel",
            "interval_method": hks["interval"],
            "comparator_type": "active",
            "poolable": True,
            "poolable_reason": (
                "Three trials randomise apixaban ITSELF against another anticoagulant for the "
                "acute event and post an arm-level count of recurrent symptomatic VTE with no "
                "death term. Their definitions were read and compared, not their names."),
            "pooled": {"measure": "RR", "point": hks["rr"], "ci_low": hks["ci_low"],
                       "ci_high": hks["ci_high"], "ci_level": 95, "scale": "log",
                       "withdrawn": False},
            "favours": "neither -- the interval spans the null",
            "per_trial": [
                {"trial_id": r["trial"], "nct": NCT_OF[r["trial"]], "measure": "RR",
                 "point": r["rr"], "ci_low": r["ci_low"], "ci_high": r["ci_high"],
                 "ci_level": 95,
                 "events_apixaban": r["events_apixaban"], "n_apixaban": r["n_apixaban"],
                 "events_comparator": r["events_comparator"],
                 "n_comparator": r["n_comparator"],
                 "continuity_corrected": r["continuity_corrected"],
                 "endpoint_rank_in_its_own_trial": (
                     "PRIMARY" if NCT_OF[r["trial"]] == "NCT03045406" else "SECONDARY"),
                 "outcome_definition": rep["titles_read"][NCT_OF[r["trial"]]]}
                for r in rep["per_trial"]],
            "heterogeneity": {"q": rep["q"], "df": rep["df"], "tau2": rep["PM"]["tau2"],
                              "i2": rep["i2_pct"],
                              "i2_definition": "Higgins (Q - df)/Q, clamped at 0",
                              "AND IT ESTABLISHES NOTHING ABOUT COHERENCE": (
                                  "I-SQUARED IS 0.0% ON THIS POOL AND THAT IS NOT WHY THE POOL "
                                  "IS REPORTED. The coherence judgement was made by reading "
                                  "three endpoint definitions and would be identical at any "
                                  "I-squared. On the same page, the pool this review DECLINES "
                                  "whose estimand IS shared comes out at 93.5% -- higher than "
                                  "the name-matched pool whose estimands agree on nothing. "
                                  "P36, measured in both directions on one topic.")},
            "heterogeneity_status": ("computed; tau-squared is 0 and at k=3 that is an "
                                     "estimate from almost no information, which is why the "
                                     "interval is Knapp-Hartung on 2 degrees of freedom rather "
                                     "than a normal one"),
            "estimator_note": repool["estimator_note"],
            "sensitivity": rep["leave_one_out"],
            "estimator_sensitivity": {
                "DerSimonian-Laird, Wald interval": {
                    "point": rep["DL"]["rr"], "ci_low": rep["DL"]["ci_low"],
                    "ci_high": rep["DL"]["ci_high"]},
                "Paule-Mandel, floored Knapp-Hartung t interval": {
                    "point": hks["rr"], "ci_low": hks["ci_low"], "ci_high": hks["ci_high"]},
                "note": ("THE SAME POINT ESTIMATE AND A MUCH NARROWER INTERVAL: %.4f to %.4f "
                         "against %.4f to %.4f. The difference is entirely the t multiplier on "
                         "2 degrees of freedom against 1.96, and it is the difference between "
                         "an interval that looks like an answer and one that admits k=3. The "
                         "wider one is reported."
                         % (rep["DL"]["ci_low"], rep["DL"]["ci_high"],
                            hks["ci_low"], hks["ci_high"])),
            },
            "the_pools_this_review_declines": {
                "_why_shown": ("SHOWN SO THE COST OF EACH REFUSAL IS INSPECTABLE, and labelled "
                               "so none can be mistaken for this review's answer."),
                "name_matched_k8": repool["estimand_declined_name_matched"],
                "estimand_shared_comparator_not_k2":
                    repool["estimand_declined_shared_but_comparator_not"],
                "each_trials_own_primary":
                    repool["estimand_declined_each_trials_own_primary"],
            },
            "coherence_screen": repool["coherence_screen"],
            "derivation_refused_with_its_arithmetic":
                repool["derivation_refused_with_its_arithmetic"],
            "the_duplicate_a_text_match_cannot_settle":
                repool["the_duplicate_a_text_match_cannot_settle"],
            "prediction_stated_before_the_run": repool["prediction"],
            "r_output": {
                "state": "NO_QUOTABLE_MODEL_OUTPUT_BUT_A_POOL_EXISTS",
                "_why_absent": ("No R session produced this pool. It was computed in Python by "
                                "scripts/repool_apixaban_treatment_2026_08_19.py, using the "
                                "same tau-squared implementation the corpus headline gate uses "
                                "to CHECK pools -- so the checker and the computer cannot "
                                "disagree on the arithmetic, only on the inputs. P6 requires "
                                "the absence of a quotable model call to be RECORDED, and it "
                                "is recorded rather than a call being invented."),
                "what_would_hold_P6": ("metafor::rma(measure='RR', method='PM', test='knha') "
                                       "over the three arm-level tables, with its printed "
                                       "output quoted verbatim."),
            },
        }}},
        "search": D.APXT_SEARCH,
        "prisma_flow": D.APXT_PRISMA,
        "k_cascade": D.APXT_CASCADE,
        "screening": {
            "search_note": ("Mechanical screen over the surfaced set on four limbs, then "
                            "adjudication of every UNSETTLED record."),
            "eligibility": (
                "POPULATION: adults with acute or recent venous thromboembolism being TREATED "
                "for it. INTERVENTION: apixaban as the randomised intervention -- the drug "
                "itself, not a class of which it is one member. COMPARATOR: conventional "
                "anticoagulation, another direct oral anticoagulant, or placebo. ESTIMAND, "
                "which governs POOLABILITY and not eligibility: recurrent venous "
                "thromboembolism, or major bleeding, at ANY registered rank. "
                "AND THE BOUNDARY WITH THE PROPHYLAXIS REVIEW: extended anticoagulation in "
                "patients who have ALREADY HAD a venous thromboembolism is TREATMENT and "
                "belongs here; primary prophylaxis in patients who have not is PREVENTION and "
                "belongs to the sibling. The discriminator is read from each trial's "
                "eligibility criteria, because the registry's coded `primaryPurpose` does not "
                "carry it and both conventions are used for both situations. Criteria are "
                "DERIVED POST HOC and say so."),
            "boundary_criterion": D.BOUNDARY_CRITERION,
            "eligibility_provenance": None,   # filled below, from this topic's own criteria
            "records": screen[T_TOPIC]["trials"] if isinstance(screen.get(T_TOPIC), dict)
                       else screen[T_TOPIC],
            "adjudication": adjud["topics"][T_TOPIC],
            "duplicate_screening": DUPLICATE_SCREENING_OWED,
        },
        "screening_of_remainder": {
            "recovered_eligible_poolable_not_included": 11,
            "of_those_with_posted_results": 8,
            "of_those_that_pool": rep["k"],
            "what_ELIGIBLE_POOLABLE_NOT_INCLUDED_means": (
                "A GAP IN OUR OWN EVIDENCE BASE, not a gap in the literature. Each of the "
                "eleven was surfaced by this review's own search, passed its own criteria, and "
                "was not in the object. The disposition exists to name that state rather than "
                "let it read as an exclusion."),
            "trials_with_results_and_no_recurrent_VTE_outcome_at_any_rank":
                repool["trials_with_results_and_no_such_outcome_at_any_rank"],
            "and_the_boundary_was_not_applied_to_all_of_them_until_now": (
                "The boundary criterion reached the SIXTEEN trials sent to adjudication. The "
                "NINE admitted by the mechanical screen were admitted on `primaryPurpose`, the "
                "coded field these criteria say does not settle the question, and were put to "
                "the boundary for the first time in this build. HI-PRO survived it against a "
                "stated prediction that it would not."),
            "unscreened_remainder": 0,
            "and_the_remainder_is_now_ZERO": (
                "It was 71 at the split. The whole of it has been screened, and the SHAPE of "
                "the disposition table is what a bare count could not say: 39 of the 48 "
                "exclusions fail on POPULATION, because they are thromboprophylaxis trials in "
                "patients who have never had a VTE. One search over one drug necessarily "
                "reaches across the boundary this pair of reviews is split on, and the trials "
                "this review excludes are the trials its sibling holds. That is a fact about "
                "splitting a drug topic in two, not a criticism of the query."),
            "what_limits_this_review_now": (
                "TWELVE eligible trials have posted no results, and EIGHT of the eleven "
                "eligible poolable trials post no arm-level count of the shared estimand. "
                "Neither limit is fixed by a better query."),
            "extraction_source": extraction.get("_source_note", "see `extraction` block"),
        },
        "topic_state": (
            "REPORTED, WITH A ZERO REMAINDER AND THREE OF EIGHT POOLING. Every one of the 73 "
            "candidate registrations has a disposition. The review is NOT complete and the "
            "reason has changed: 12 eligible trials have posted no results, and the two "
            "largest trials in the field post no measure this review can pool."),
        "risk_of_bias": rob2_for({
            "recurrent_vte": {
                "NCT03045406": {
                    "trial": "CARAVAGGIO",
                    "domains": {
                        "D1_randomisation": {"judgement": "SOME_CONCERNS", "evidence": [
                            "designInfo.allocation = RANDOMIZED",
                            "Allocation concealment and baseline balance are in neither the "
                            "registration nor the posted results."]},
                        "D2_deviations": {"judgement": "SOME_CONCERNS", "evidence": [
                            "designInfo.maskingInfo.masking = NONE. Participants and carers "
                            "knew the assignment; an open-label anticoagulant trial cannot "
                            "reach LOW here on the registration alone.",
                            "The trial describes itself as PROBE -- open, blinded end-point."]},
                        "D3_missing_outcome_data": {"judgement": "LOW", "evidence": [
                            "participant flow STARTED 585 + 585 = 1170; the recurrent-VTE "
                            "denominators are 576 and 579 = 1155, so 15 of 1170 (1.28%) are "
                            "not in the analysed set."]},
                        "D4_measurement": {"judgement": "LOW", "evidence": [
                            "blinded end-point adjudication, and the outcome is an objectively "
                            "confirmed thrombotic event."]},
                        "D5_selection_of_result": {"judgement": "SOME_CONCERNS", "evidence": [
                            "No statistical analysis plan is held, so D5 cannot reach LOW.",
                            "The result used is this trial's own registered PRIMARY, so no "
                            "selection among ranks was made by this review."]},
                    },
                    "overall": "SOME_CONCERNS"},
                "NCT03266783": {
                    "trial": "COBRRA",
                    "domains": {
                        "D1_randomisation": {"judgement": "SOME_CONCERNS", "evidence": [
                            "designInfo.allocation = RANDOMIZED; concealment not reported."]},
                        "D2_deviations": {"judgement": "SOME_CONCERNS", "evidence": [
                            "masking = NONE; a pragmatic PROBE trial of two oral drugs."]},
                        "D3_missing_outcome_data": {"judgement": "SOME_CONCERNS", "evidence": [
                            "STARTED 1370 + 1390 = 2760; the recurrent-VTE denominators are "
                            "1345 and 1355, WHICH EQUAL THE COMPLETED COUNTS EXACTLY. The "
                            "analysis of this outcome is on completers, not on all randomised "
                            "-- 60 of 2760 (2.17%) are absent from it, and the equality with "
                            "the completion milestone is what identifies it as a completer "
                            "analysis rather than an ITT one."]},
                        "D4_measurement": {"judgement": "LOW", "evidence": [
                            "the measure is titled `Adjudicated`, and the event is objective."]},
                        "D5_selection_of_result": {"judgement": "SOME_CONCERNS", "evidence": [
                            "No statistical analysis plan is held.",
                            "THE RESULT USED IS A SECONDARY OUTCOME, selected by THIS REVIEW "
                            "from among ten posted ranks. The rule that chose it -- the "
                            "estimand shared across the pool -- was fixed before any result "
                            "was read, and it is still a selection this review made."]},
                    },
                    "overall": "SOME_CONCERNS"},
                "NCT01780987": {
                    "trial": "Japanese acute DVT/PE study",
                    "domains": {
                        "D1_randomisation": {"judgement": "SOME_CONCERNS", "evidence": [
                            "designInfo.allocation = RANDOMIZED; concealment not reported; "
                            "n=80, at which size baseline imbalance is likely and unreported."]},
                        "D2_deviations": {"judgement": "SOME_CONCERNS", "evidence": [
                            "masking = NONE."]},
                        "D3_missing_outcome_data": {"judgement": "SOME_CONCERNS", "evidence": [
                            "STARTED 40 + 40; the recurrent-VTE denominators are 38 and 40. "
                            "Two participants are absent from one arm of a trial with ONE "
                            "event in total, so the missing data are of the same order as the "
                            "outcome."]},
                        "D4_measurement": {"judgement": "LOW", "evidence": [
                            "titled `Adjudicated`; objective event."]},
                        "D5_selection_of_result": {"judgement": "SOME_CONCERNS", "evidence": [
                            "No statistical analysis plan is held.",
                            "THE RESULT USED IS A SECONDARY OUTCOME; this trial's registered "
                            "primary is a bleeding endpoint."]},
                    },
                    "overall": "SOME_CONCERNS"},
            }}),
        "grade": {
            "approach": "GRADE",
            "reference": ("Schunemann H, Brozek J, Guyatt G, Oxman A (editors). GRADE Handbook "
                          "for grading quality of evidence and strength of recommendations."),
            "handbook_chapter": ("Cochrane Handbook for Systematic Reviews of Interventions "
                                 "version 6.5.1, Chapter 14"),
            "starting_point": "HIGH for a body of randomised evidence, then rated down.",
            "not_rated_up": "No domain is rated up.",
            "by_outcome": {"recurrent_vte": {
                "rated": True, "certainty": "VERY_LOW", "k": rep["k"], "i2": rep["i2_pct"],
                "estimate": {"point": hks["rr"], "ci_low": hks["ci_low"],
                             "ci_high": hks["ci_high"]},
                "started_at": "HIGH",
                "steps": [
                    {"domain": "risk_of_bias", "levels": -1, "from": "HIGH", "to": "MODERATE",
                     "reason": ("All three contributing results are SOME CONCERNS overall, and "
                                "all three are open-label. Two are secondary outcomes selected "
                                "by this review from among registered ranks.")},
                    {"domain": "inconsistency", "levels": 0, "from": "MODERATE",
                     "to": "MODERATE",
                     "reason": ("I-squared 0% over k=3: not rated down. A LOW I-SQUARED DOES "
                                "NOT SHOW THE TRIALS MEASURE THE SAME THING -- on this very "
                                "page the pool with the SHARED estimand comes out at 93.5%. "
                                "Coherence is handled under indirectness, where it belongs.")},
                    {"domain": "indirectness", "levels": -1, "from": "MODERATE", "to": "LOW",
                     "reason": ("The three comparators are NOT the same comparator: dalteparin, "
                                "rivaroxaban, and unfractionated heparin followed by warfarin. "
                                "The estimand is shared and the contrast is not, so the pooled "
                                "quantity is 'apixaban against whatever else was given', which "
                                "is one step from any question a reader has. Stated rather "
                                "than absorbed into heterogeneity.")},
                    {"domain": "imprecision", "levels": -1, "from": "LOW", "to": "VERY_LOW",
                     "reason": ("k=3, 3,933 participants, 61 events in total, and the "
                                "Knapp-Hartung interval runs 0.34 to 1.75 -- consistent with a "
                                "two-thirds reduction and with a three-quarters increase. This "
                                "is the honest width and it is why the review's answer is 'not "
                                "established' rather than 'no difference'.")},
                    {"domain": "publication_bias", "levels": 0, "from": "VERY_LOW",
                     "to": "VERY_LOW",
                     "reason": ("k=3. A funnel plot or Egger test at k=3 has no power and "
                                "would be theatre. NOT ASSESSED, and not counted as absent.")},
                ],
                "and_what_the_rating_is_NOT_about": (
                    "VERY LOW certainty here is not a claim that apixaban is ineffective in "
                    "acute VTE. It is a claim about WHAT THIS REVIEW CAN SHOW from three "
                    "trials on one shared estimand. The largest trials in the field are "
                    "excluded from this pool for a reason recorded on this page, and their "
                    "results are not smuggled into the certainty rating by implication."),
            }},
        },
        "protocol": PROTOCOL,
        "sources": {},
        "sources_note": ("Every number on this page is traceable to a ClinicalTrials.gov v2 "
                         "payload read on 2026-08-19 and quoted in the extraction table. No "
                         "journal article was read for any effect estimate; where a published "
                         "report would settle something the registry cannot, that is recorded "
                         "as unheld rather than inferred."),
        "extraction": D.APXT_EXTRACTION,
    }

    # ==================================================================================
    # B -- PROPHYLAXIS
    # ==================================================================================
    pr = prop["estimand_reported"]
    p_trials = []
    P_NCT = {"ADOPT": "NCT00457002", "ADVANCE-3": "NCT00423319",
             "ADVANCE-1": "NCT00371683", "ADVANCE-2": "NCT00452530"}
    for r in pr["per_trial"]:
        nct = P_NCT[r["trial"]]
        p_trials.append({
            "id": nct, "nct": nct, "name": r["trial"],
            "arms": [
                {"label": "Apixaban", "role": "treatment",
                 "events": r["events_apixaban"], "participants": r["n_apixaban"]},
                {"label": "Enoxaparin", "role": "control",
                 "events": r["events_enoxaparin"], "participants": r["n_enoxaparin"]},
            ],
            "design": "randomised thromboprophylaxis, apixaban against enoxaparin",
            "comparator_type": "active",
            "comparator_type_basis": "enoxaparin in all four.",
            "enrolled": r["n_apixaban"] + r["n_enoxaparin"],
            "by_outcome": {"major_vte": {
                "effect": {"measure": "RR", "point": r["rr"], "ci_low": r["ci_low"],
                           "ci_high": r["ci_high"], "ci_level": 95, "scale": "log",
                           "derived_from": "arm-level event counts",
                           "derivation_note": ("Events are the posted event RATE multiplied by "
                                               "the analysed denominator and rounded -- "
                                               "DERIVED, and labelled DERIVED, because these "
                                               "four trials post rates where the treatment "
                                               "review's three post counts.")},
                "provenance": {
                    "tag": "MEASURED",
                    "source_id": nct,
                    "source": "ClinicalTrials.gov posted results, read 2026-08-19",
                    "source_outcome_title": pr["titles_read"][nct],
                    "source_quotes": [
                        pr["titles_read"][nct],
                        ("Event counts are the posted event RATE multiplied by the analysed "
                         "denominator and rounded; the rate is what this trial posts."),
                    ],
                    "quote_note": ("The endpoint TITLE as the registry posts it, and a plain "
                                   "statement that the counts here are DERIVED from a posted "
                                   "rate rather than read as counts -- which is the one "
                                   "material difference between this pool and its sibling's."),
                },
                "analysed": {"treatment": r["n_apixaban"], "control": r["n_enoxaparin"]},
                "outcome_definition": pr["titles_read"][nct],
                "outcome_definition_source": {
                    "source": "registry results section",
                    "source_field": "resultsSection.outcomeMeasuresModule.outcomeMeasures[]",
                    "source_url": "https://clinicaltrials.gov/study/%s" % nct,
                    "read_utc": "2026-08-19"},
                "endpoint_rank_in_its_own_trial": "SECONDARY",
                "source_tier": "registry_posted_results",
            }},
            "registration_read_utc": "2026-08-19",
            "all_ranks_read_utc": "2026-08-19",
        })

    p_trials.append({
        "id": "NCT02366871", "nct": "NCT02366871", "name": "apixaban vs enoxaparin, pelvic "
                                                           "malignancy",
        "arms": [],
        "design": "randomised, apixaban against enoxaparin in suspected pelvic malignancy",
        "comparator_type": "active", "comparator_type_basis": "enoxaparin.",
        "enrolled": 400,
        "contributes_to_no_pool": {
            "state": "ELIGIBLE, NOT POOLABLE",
            "why": ("Its registered primaries are MAJOR BLEEDING and clinically relevant "
                    "non-major bleeding -- a SAFETY estimand. It reports nothing on this "
                    "review's efficacy estimand."),
            "why_it_is_kept": ("THIS WAS THIS REVIEW'S ENTIRE PREVIOUS EVIDENCE BASE. The page "
                               "reported its result as the review's answer, and it was never "
                               "an estimate of the review's question. Keeping it visible is "
                               "what makes that legible."),
        },
        "by_outcome": {},
        "registration_read_utc": "2026-08-19",
        "all_ranks_read_utc": "2026-08-19",
    })

    p_obj = {
        "app_id": P_TOPIC,
        "schema_version": 2,
        "title": ("Apixaban thromboprophylaxis: four trials, four different primary "
                  "composites, and one estimand all four register below the primary"),
        "question": ("In adults at risk of venous thromboembolism, what is the effect of "
                     "apixaban thromboprophylaxis compared with enoxaparin, another "
                     "anticoagulant, or no anticoagulation on symptomatic venous "
                     "thromboembolism and on bleeding?"),
        "question_provenance": (
            "The second of the two readings `apixaban-vte` was split into on 2026-08-19. See "
            "BLOCKED-apixaban-vte-2026-08-19.md. P21: neither reading was chosen over the "
            "other; both are built."),
        "built": "2026-08-19",
        "build_mode": "AUTHORED",
        "split_provenance": {
            "parent": "apixaban-vte",
            "why_split": "See the sibling. P21.",
            "siblings": [T_TOPIC],
            "shared_trials": {
                "with_" + T_TOPIC: [],
                "computed_over": "this object's included NCT set intersected with the sibling's",
                "why_empty_is_a_result_and_not_a_blank": (
                    "The boundary criterion assigns every trial to exactly one review, so the "
                    "intersection is empty BY CONSTRUCTION and is computed rather than left as "
                    "a bare `[]`. P17."),
            },
        },
        "outcomes": [{
            "id": "major_vte",
            "name": "Proximal DVT, non-fatal pulmonary embolism, or VTE-related death",
            "definition": pr["definition"],
            "definition_note": (
                "SECONDARY IN ALL FOUR TRIALS. Their four PRIMARY composites are four "
                "different things -- ADOPT counts VTE-related death, ADVANCE-1 counts "
                "ALL-CAUSE death -- and their primary event rates span 1.39% to 8.99% for one "
                "drug in one indication, which is a fact about what each counted and which "
                "surgery rather than about apixaban."),
            "measure": "RR", "effect_scale": "log", "type": "binary",
            "estimand": {"id": "major_vte", "family": "binary risk",
                         "model": "random-effects, DerSimonian-Laird",
                         "case_definition": pr["definition"]},
            "comparator": "enoxaparin", "comparator_type": "active",
            "direction_of_benefit": "lower", "null_value": 1.0,
        }],
        "withholding_question": {
            "asked_on": "2026-08-19",
            "question": ("does each trial report, AT ANY RANK -- primary, secondary or other "
                         "-- an outcome matching what the others report, before any decision "
                         "about which pools are possible?"),
            "answer": "YES, AND IT IS A SECONDARY IN ALL FOUR",
            "found": pr["found_by"],
            "what_asking_it_bought": (
                "THE WHOLE POOL. Every contributing result is below the primary; a review "
                "reading primaries only would have found four incompatible composites and "
                "reported no pool. The poolable set went from 3 to 8 candidates and settled at "
                "4 contributing trials and 13,570 participants. THE SIBLING REVIEW RAN THE "
                "IDENTICAL DISCIPLINE AND ITS POOLABLE SET FELL, 8 to 3. Asking is not a way "
                "of finding more trials."),
        },
        "inputs": {"trials": p_trials},
        "config": {"confidence_level": 95},
        "results": {"by_outcome": {"major_vte": {
            "k": pr["k"], "estimand_id": "major_vte",
            "model": "random-effects", "estimator": "DerSimonian-Laird",
            "estimator_used": "DerSimonian-Laird",
            "comparator_type": "active",
            "poolable": True,
            "poolable_reason": ("All four register the same composite -- proximal DVT, "
                                "non-fatal PE, or VTE-related death -- at SECONDARY rank, and "
                                "each title was read rather than matched by name."),
            "pooled": {"measure": "RR", "point": pr["rr"], "ci_low": pr["ci_low"],
                       "ci_high": pr["ci_high"], "ci_level": 95, "scale": "log",
                       "withdrawn": False},
            "favours": "neither -- the interval spans the null",
            "per_trial": [
                {"trial_id": r["trial"], "nct": P_NCT[r["trial"]], "measure": "RR",
                 "point": r["rr"], "ci_low": r["ci_low"], "ci_high": r["ci_high"],
                 "ci_level": 95, "events_apixaban": r["events_apixaban"],
                 "n_apixaban": r["n_apixaban"],
                 "events_comparator": r["events_enoxaparin"],
                 "n_comparator": r["n_enoxaparin"],
                 "endpoint_rank_in_its_own_trial": "SECONDARY",
                 "outcome_definition": pr["titles_read"][P_NCT[r["trial"]]]}
                for r in pr["per_trial"]],
            "heterogeneity": {"q": pr["q"], "df": pr["df"], "tau2": pr["tau2"],
                              "i2": pr["i2_pct"],
                              "i2_definition": "Higgins (Q - df)/Q, clamped at 0",
                              "AND IT CUTS BOTH WAYS": (
                                  "I-SQUARED IS 67.8% ON THE POOL THIS REVIEW REPORTS AND "
                                  "83.6% ON THE ONE IT DECLINES. The reported pool is the more "
                                  "consistent of the two AND THAT IS NOT WHY IT IS REPORTED: "
                                  "on the sibling topic, built the same night, the ordering is "
                                  "reversed -- the estimand-coherent pool is the MORE "
                                  "heterogeneous. P36.")},
            "heterogeneity_status": "computed",
            "estimator_note": (
                "THIS POOL IS OWED AN ESTIMATOR CORRECTION AND THE DEBT IS ON THE PAGE. It "
                "uses DerSimonian-Laird at k=4. The house rule refuses DerSimonian-Laird below "
                "k=10 because it under-estimates the between-study variance, and THE SIBLING "
                "REVIEW BUILT THE SAME NIGHT uses Paule-Mandel with a floored Knapp-Hartung "
                "interval at k=3. It is recorded rather than silently changed because "
                "recomputing it in the same pass that publishes this page would move a "
                "published estimate that has not been re-derived or re-checked -- and a "
                "divergence between two siblings built from one search is exactly the kind of "
                "thing nobody notices again. What would close it: re-run "
                "scripts/repool_apixaban_prophylaxis_2026_08_19.py with Paule-Mandel and a "
                "floored Knapp-Hartung interval, then promote the result through every derived "
                "block on this object (P19)."),
            "estimator_debt": {
                "state": "OWED A CORRECTION",
                "estimator_used": "DerSimonian-Laird", "k": pr["k"],
                "estimator_the_house_rule_requires_at_this_k": "Paule-Mandel or REML",
                "sibling_using_it": T_TOPIC,
                "what_would_close_it": ("re-run scripts/repool_apixaban_prophylaxis_2026_08_19"
                                        ".py with Paule-Mandel and a floored Knapp-Hartung "
                                        "interval, and promote through every derived block."),
            },
            "the_pool_this_review_declines": prop["estimand_declined"],
            "what_this_replaces": prop["what_this_replaces"],
            "and_the_primary_is_read_by_text_never_by_position":
                prop["and_the_primary_is_read_by_text_never_by_position"],
            "r_output": {
                "state": "NO_QUOTABLE_MODEL_OUTPUT_BUT_A_POOL_EXISTS",
                "_why_absent": ("Computed in Python by "
                                "scripts/repool_apixaban_prophylaxis_2026_08_19.py. No R "
                                "session produced it and none is quoted."),
                "what_would_hold_P6": "metafor::rma(measure='RR', method='PM', test='knha')",
            },
        }}},
        "search": D.APXP_SEARCH,
        "prisma_flow": D.APXP_PRISMA,
        "k_cascade": D.APXP_CASCADE,
        "screening": {
            "search_note": "Mechanical screen on four limbs, then adjudication of every "
                           "UNSETTLED record.",
            "eligibility": (
                "POPULATION: adults AT RISK of venous thromboembolism receiving "
                "thromboprophylaxis -- surgical, medically ill, or cancer-associated. "
                "INTERVENTION: apixaban thromboprophylaxis as the randomised intervention. "
                "COMPARATOR: enoxaparin or another anticoagulant, or placebo / no "
                "anticoagulation. ESTIMAND, which governs POOLABILITY and not eligibility: "
                "symptomatic venous thromboembolism, or major bleeding, at ANY registered "
                "rank. AND THE BOUNDARY WITH THE TREATMENT REVIEW: primary prophylaxis in "
                "patients who have NOT had a venous thromboembolism belongs here; extended "
                "anticoagulation in patients who have belongs to the sibling. The "
                "discriminator is read from each trial's eligibility criteria, because the "
                "registry's coded `primaryPurpose` does not carry it -- ADVANCE-2 is "
                "knee-replacement thromboprophylaxis coded TREATMENT, and it is admitted here. "
                "Criteria are DERIVED POST HOC and say so."),
            "boundary_criterion": D.BOUNDARY_CRITERION,
            "eligibility_provenance": None,   # filled below, from this topic's own criteria
            "records": screen[P_TOPIC]["trials"] if isinstance(screen.get(P_TOPIC), dict)
                       else screen[P_TOPIC],
            "adjudication": adjud["topics"][P_TOPIC],
            "duplicate_screening": DUPLICATE_SCREENING_OWED,
        },
        "screening_of_remainder": {
            "recovered_eligible_poolable_not_included": 5,
            "contributing_to_the_pool": 4,
            "what_ELIGIBLE_POOLABLE_NOT_INCLUDED_means": (
                "A GAP IN OUR OWN EVIDENCE BASE. ADOPT (n=6758), ADVANCE-3 (n=5407) and "
                "ADVANCE-1 (n=3608) were surfaced by this review's own search, passed its own "
                "criteria, and were not in the object. ADVANCE-2 was recovered by the boundary "
                "criterion against its own coded field."),
            "and_the_object_previously_reported_a_SAFETY_result": (
                "Its single included trial NCT02366871 is n=400 and its registered primaries "
                "are major bleeding and clinically relevant non-major bleeding. The previous "
                "figure was not an estimate of this review's efficacy question at all, which "
                "is why the change here IS NOT A DELTA and must not be presented as one."),
            "unscreened_remainder": 0,
            "and_the_remainder_is_now_ZERO": (
                "It was 71 at the split and the whole of it has been screened. The disposition "
                "table's dominant state is NOT exclusion: 22 of the 31 eligible trials have "
                "POSTED NO RESULTS. Under the reading in PAGE-STANDARD.md that means the query "
                "is well aimed and THE FIELD IS STILL IN FLIGHT, and the thing to do is name "
                "the largest pending trial rather than narrow the search. It is NCT06581965, "
                "n=10,078 -- larger than every trial in this pool combined."),
        },
        "topic_state": ("REPORTED, WITH A ZERO REMAINDER AND AN OPEN ESTIMATOR DEBT. Every one "
                        "of the 73 candidate registrations has a disposition. The review is "
                        "NOT complete: 22 of its 31 eligible trials have posted no results, "
                        "and its pool is computed with an estimator its own note says is the "
                        "wrong one at k=4."),
        "risk_of_bias": {
            "tool": "RoB 2 (Cochrane risk-of-bias tool for randomized trials)",
            "state": "NOT_ASSESSED_FOR_THIS_REVIEW",
            "why": ("The four contributing results were extracted and pooled on 2026-08-19 and "
                    "no result-level RoB 2 assessment was performed for any of them. THIS IS "
                    "RECORDED AS UNASSESSED AND NOT AS ABSENT OF BIAS: an unassessed domain is "
                    "NOT_ASSESSABLE, never LOW."),
            "consequence_carried_into_grade": ("GRADE rates this outcome down one level for "
                                               "risk of bias on the ground that it is "
                                               "unassessed, which is the same handling the "
                                               "corpus applied to sglt2-hf's harmonised pool."),
            "what_would_close_it": ("RoB 2 per RESULT for the shared secondary in each of "
                                    "NCT00457002, NCT00423319, NCT00371683 and NCT00452530."),
        },
        "grade": {
            "approach": "GRADE",
            "reference": ("Schunemann H, Brozek J, Guyatt G, Oxman A (editors). GRADE "
                          "Handbook."),
            "handbook_chapter": ("Cochrane Handbook for Systematic Reviews of Interventions "
                                 "version 6.5.1, Chapter 14"),
            "starting_point": "HIGH for a body of randomised evidence, then rated down.",
            "not_rated_up": "No domain is rated up.",
            "by_outcome": {"major_vte": {
                "rated": True, "certainty": "VERY_LOW", "k": pr["k"], "i2": pr["i2_pct"],
                "estimate": {"point": pr["rr"], "ci_low": pr["ci_low"],
                             "ci_high": pr["ci_high"]},
                "started_at": "HIGH",
                "steps": [
                    {"domain": "risk_of_bias", "levels": -1, "from": "HIGH", "to": "MODERATE",
                     "reason": ("No result-level RoB 2 assessment exists for this outcome, so "
                                "risk of bias is NOT ASSESSED rather than absent. Rated down "
                                "one level because unassessed is not low.")},
                    {"domain": "inconsistency", "levels": -1, "from": "MODERATE", "to": "LOW",
                     "reason": ("I-squared 67.8% over k=4, with per-trial risk ratios running "
                                "from 0.40 to 1.41 -- two intervals excluding the null in "
                                "OPPOSITE directions. Rated down, and note that this is "
                                "inconsistency of RESULT and says nothing either way about "
                                "whether the estimand is shared, which was established by "
                                "reading the four titles.")},
                    {"domain": "indirectness", "levels": 0, "from": "LOW", "to": "LOW",
                     "reason": ("One comparator (enoxaparin) in all four, and one endpoint "
                                "definition verified by reading each trial's registered text.")},
                    {"domain": "imprecision", "levels": -1, "from": "LOW", "to": "VERY_LOW",
                     "reason": ("The interval 0.4532 to 1.2309 spans a 55% reduction and a 23% "
                                "increase. k=4, and tau-squared estimated by DerSimonian-Laird "
                                "which the house rule says is biased low at this k -- so the "
                                "interval is if anything narrower than it should be.")},
                    {"domain": "publication_bias", "levels": 0, "from": "VERY_LOW",
                     "to": "VERY_LOW",
                     "reason": "k=4. NOT ASSESSED; not counted as absent."},
                ],
            }},
        },
        "protocol": PROTOCOL,
        "sources": {},
        "sources_note": ("Every number is traceable to a ClinicalTrials.gov v2 payload read on "
                         "2026-08-19."),
        "extraction": D.APXP_EXTRACTION,
    }

    # P3: the criteria provenance block is this topic's OWN criteria, keyed to the topic and
    # never a module constant -- it is the block that carries `predefined: false` on its face.
    t_obj["screening"]["eligibility_provenance"] = D.APXT_CRITERIA
    p_obj["screening"]["eligibility_provenance"] = D.APXP_CRITERIA

    # ------------------------------------------------------------------------------
    # P22: SHARING, COMPUTED AGAINST THE WHOLE CORPUS RATHER THAN AGAINST THE SIBLING.
    #
    # The obvious answer -- "the two split reviews share nothing, the boundary criterion
    # guarantees it" -- is TRUE AND IT IS NOT THE ANSWER TO THE QUESTION P22 ASKS. Both
    # trials are still in the PARENT object, which has not been retired, so each one is now
    # held by two objects and a corpus-level k obtained by summing double-counts them. That
    # is exactly the state P22 exists to make visible, and it is invisible if the check is
    # run against the sibling alone.
    # ------------------------------------------------------------------------------
    ssot_dir = os.path.join(REPO, "ssot")
    for topic, obj in ((T_TOPIC, t_obj), (P_TOPIC, p_obj)):
        mine = [t.get("nct") for t in obj["inputs"]["trials"] if t.get("nct")]
        found, checked = {}, 0
        for d in sorted(os.listdir(ssot_dir)):
            if d in (topic, T_TOPIC, P_TOPIC):
                continue
            p2 = os.path.join(ssot_dir, d, d + ".json")
            if not os.path.exists(p2):
                continue
            checked += 1
            try:
                with io.open(p2, encoding="utf-8") as fh:
                    o2 = json.load(fh)
            except (ValueError, OSError):
                continue
            their = {t.get("nct") for t in ((o2.get("inputs") or {}).get("trials") or [])}
            for n in mine:
                if n in their:
                    found.setdefault(n, []).append(d)
        obj["shared_with_other_topics"] = {
            "computed": True,
            "computed_against": ("every other topic object under ssot/ -- %d checked -- by "
                                 "reading each one's inputs.trials. Not asserted, and not "
                                 "limited to the sibling." % checked),
            "shared": {n: {"also_in": ts,
                           "why": ("This review was split out of `apixaban-vte` and the parent "
                                   "object still holds this trial. The sharing is a "
                                   "consequence of the split, not of two reviews independently "
                                   "including it."
                                   if ts == ["apixaban-vte"] else
                                   "held by another topic; recorded rather than left to a "
                                   "summed corpus k to hide.")}
                       for n, ts in sorted(found.items())},
            "summing_per_topic_k_double_counts": (
                "A CORPUS-LEVEL k OBTAINED BY SUMMING PER-TOPIC k DOUBLE-COUNTS. %d of this "
                "review's %d trials are also held elsewhere. The parent `apixaban-vte` is "
                "superseded by this split and has not been retired, so its trials are counted "
                "twice for as long as it stands." % (len(found), len(mine))),
            "and_the_split_ITSELF_shares_nothing": (
                "The two split reviews share NO trial with each other, by construction: the "
                "boundary criterion assigns every trial to exactly one of them. That is worth "
                "stating precisely because it is the answer to a DIFFERENT question from the "
                "one above, and reporting it in place of the parent overlap would have been a "
                "true sentence standing where a false impression was needed."),
        }

    # ------------------------------------------------------------------------------
    # SHARED TRIALS, COMPUTED. P17: a field whose name implies a check carries a computed
    # value and names what it was computed against. `[]` here is a RESULT.
    # ------------------------------------------------------------------------------
    t_ncts = set(D.APXT_PRISMA["included"]["nct"])
    p_ncts = set(D.APXP_PRISMA["included"]["nct"])
    shared = sorted(t_ncts & p_ncts)
    for obj, other in ((t_obj, P_TOPIC), (p_obj, T_TOPIC)):
        blk = obj["split_provenance"]["shared_trials"]
        blk["with_" + other] = shared
        blk["computed_over"] = (
            "the two objects' own included NCT sets: %d here against %d there, intersected. "
            "Not asserted." % (len(t_ncts), len(p_ncts)))
        if shared:
            blk["why_empty_is_a_result_and_not_a_blank"] = (
                "NOT EMPTY -- %s appear in both, and that must be recorded on both sides with "
                "the reason, or a corpus-level k obtained by summing double-counts them (P22)."
                % ", ".join(shared))

    wrote = []
    for topic, obj in ((T_TOPIC, t_obj), (P_TOPIC, p_obj)):
        d = os.path.join(REPO, "ssot", topic)
        os.makedirs(d, exist_ok=True)
        dest = os.path.join(d, "%s.json" % topic)
        if os.path.exists(dest):
            # This script CREATES objects. A wholesale write regresses every enrichment since
            # the last build -- the class `merge_rob_grade_into_objects_2026_08_19.py` refuses.
            # `--recreate` exists ONLY for the window before the first enrichment, and it is
            # gated on the object carrying no build stamp, which is the mark that
            # build_to_standard.py has touched it. Not on a flag alone, because a flag is a
            # promise and a build stamp is a fact.
            with io.open(dest, encoding="utf-8") as fh:
                existing = json.load(fh)
            if "--recreate" not in sys.argv:
                raise SystemExit(
                    "REFUSED: %s already exists and this script does not overwrite. Pass "
                    "--recreate only while the object is unstamped." % dest)
            if existing.get("build_stamp"):
                raise SystemExit(
                    "REFUSED: %s carries a build_stamp (%s), so it has been through "
                    "ssot/build_to_standard.py and may hold enrichment this script does not "
                    "reproduce. --recreate is not honoured. MERGE instead."
                    % (dest, existing["build_stamp"].get("page_standard_version")))
        with io.open(dest, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(obj, indent=1))
        wrote.append(dest)

    print("TREATMENT   k0 %d  ->  eligible poolable recovered 11  ->  with results 8  ->  "
          "POOLED %d" % (D.APXT_CASCADE["k0_surfaced"], rep["k"]))
    print("            RR %.4f (%.4f to %.4f)  PM tau2 %.5f  I2 %.1f%%  HKSJ t on %d df"
          % (hks["rr"], hks["ci_low"], hks["ci_high"], rep["PM"]["tau2"], rep["i2_pct"],
             hks["t_df"]))
    print("            declined: name-matched k=8 I2 %.1f%%;  AMPLIFY+AMPLIFY-EXT k=2 I2 %.1f%%"
          % (repool["estimand_declined_name_matched"]["i2_pct"],
             repool["estimand_declined_shared_but_comparator_not"]["i2_pct"]))
    print("PROPHYLAXIS k0 %d  ->  recovered 5  ->  POOLED %d"
          % (D.APXP_CASCADE["k0_surfaced"], pr["k"]))
    print("            RR %.4f (%.4f to %.4f)  I2 %.1f%%   [DL -- estimator debt recorded]"
          % (pr["rr"], pr["ci_low"], pr["ci_high"], pr["i2_pct"]))
    print("BOUNDARY CRITERION on BOTH objects at screening.boundary_criterion")
    for w in wrote:
        print("wrote %s" % w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
