"""Per-topic data for the TWO reviews `apixaban-vte` was split into.

THE DECISION, AND WHY IT IS THE SAME ONE AS ABLATION. `BLOCKED-apixaban-vte-2026-08-19.md`
asked Mahmood to choose between two questions -- apixaban for the TREATMENT of venous
thromboembolism (34 coded trials) and apixaban for its PREVENTION (33) -- and tabulated each by
which of the object's two trials it would DROP. Two legitimate questions with near-equal
evidence, and the axis of choice was how much to discard.

    P21: AN AMBIGUOUS QUESTION IS BUILT AS SEVERAL REVIEWS, NEVER CHOSEN BETWEEN. Choosing is
    a decision to withhold evidence from whichever reading loses, and a dropped trial leaves
    no trace in any object.

Both are built. Neither shares a block with the other.

AND THE SPLIT IS TAKEN FROM A CODED FIELD WHOSE UNRELIABILITY IS ON THE RECORD.
`designModule.designInfo.primaryPurpose` separates the two questions cleanly at corpus level
and IS NOT RELIABLE ROW BY ROW -- proven by one programme:

    ADVANCE-2  NCT00452530  knee replacement thromboprophylaxis  -> coded TREATMENT
    ADVANCE-3  NCT00423319  hip  replacement thromboprophylaxis  -> coded PREVENTION

One design, one sponsor, months apart, coded on opposite sides of the very split these two
reviews turn on. So the coded field decides which POOL a trial is counted in, and each trial's
own design decides whether it is INCLUDED -- stated here rather than discovered during
screening.
"""

# ==========================================================================================
# SHARED FACT, NOT A SHARED BLOCK: both reviews were surfaced by the same executed search,
# because it is one search over one drug. Their CASCADES and CRITERIA are separate.
# ==========================================================================================
_SEARCH_NOTE = (
    "Executed 2026-08-19 against ClinicalTrials.gov API v2, raw. "
    'query.cond="venous thromboembolism OR deep vein thrombosis OR pulmonary embolism"; '
    'query.intr="apixaban"; filter.advanced=AREA[StudyType]INTERVENTIONAL -- NO PHASE FILTER. '
    "82 records, returned == totalCount, nextPageToken null.")

_PHASE_FILTER_NOTE = (
    "THE FIRST QUERY CARRIED phase=[PHASE3,PHASE4] AND RETURNED 49 RECORDS WITHOUT NCT02366871 "
    "-- one of the parent object's own two trials -- because it is registered PHASE2. Recorded "
    "rather than replaced. The corpus-wide cost of that filter is measured at "
    "evidence/2026-08-19-batch1/phase_filter_recall_sweep.json, where apixaban-vte is one of "
    "two topics that lost an included trial to it. P23.")

# ------------------------------------------------------------------------------------------
# A -- TREATMENT
# ------------------------------------------------------------------------------------------
APXT_SEARCH = {
    "executed_by": "lane 1 (Claude, Anthropic family)",
    "databases": [
        {"database": "ClinicalTrials.gov API v2", "tool": "raw /studies",
         "query_as_executed": _SEARCH_NOTE, "date_executed": "2026-08-19",
         "http_status": 200, "records_returned": 82, "total_reported": 82,
         "recall_on_included_set": "1/1"},
        {"database": "ClinicalTrials.gov API v2 -- FIRST QUERY, RECORDED BECAUSE IT MISSED",
         "tool": "raw /studies",
         "query_as_executed": "same terms with filter.advanced=... AND AREA[Phase](PHASE3 OR "
                              "PHASE4)",
         "date_executed": "2026-08-19", "http_status": 200,
         "records_returned": 49, "total_reported": 49,
         "recall_on_included_set": "1/1 for THIS review, 1/2 for the parent",
         "what_it_cost": _PHASE_FILTER_NOTE},
        {"database": "PubMed (NCBI E-utilities esearch)", "tool": "esearch",
         "query_as_executed": "apixaban AND venous thromboembolism",
         "date_executed": "2026-08-19", "http_status": 200,
         "records_returned": 50, "total_reported": 439,
         "recall_on_included_set": "NOT MEASURED",
         "what_is_unexamined": "439 records matched and 50 were retrieved. THE OTHER 389 ARE "
                               "UNEXAMINED, NOT EXCLUDED, and recall against this review's "
                               "included set was never measured on this database -- so P23 "
                               "cannot hold on it and says so."},
    ],
    "pagination_verified": "returned == totalCount on both registry queries, totalCount read "
                           "from the FIRST page.",
}

APXT_PRISMA = {
    "_scope": "PRISMA 2020 flow, counted from the executed search above.",
    "identification": {"ctgov": 82, "pubmed_total": 439, "pubmed_retrieved": 50},
    "eligibility_ctgov": {
        "role_located": 80, "topic_is_experimental_arm": 54, "topic_is_comparator_arm": 19,
        "topic_is_background": 7, "not_assessable": 2,
        "note": "80, not 82. The parent object recorded k2_role_located = 82 -- the SURFACED "
                "total -- while carrying kNA = 2, so the stage named 'role located' counted "
                "the two records whose role could NOT be read. Corrected here; the same "
                "defect was fixed on three other objects on 2026-08-19 and is now refused by "
                "scripts/lint_cascade_arithmetic.py.",
    },
    "screening_of_the_candidate_pool": {
        "screened": 72, "excluded": 48, "eligible": 25,
        "excluded_on": {"POPULATION": 39, "COMPARATOR": 9},
        "eligible_split": {"ELIGIBLE_POOLABLE": 11, "ELIGIBLE_NO_RESULTS_YET": 12,
                           "ELIGIBLE_NOT_POOLABLE": 2},
        "note": ("16 of the 72 were UNSETTLED at the mechanical screen and were adjudicated "
                 "one by one; their dispositions are at `screening.adjudication`."),
    },
    "included": {"in_this_object": 4, "contributing_to_the_pool": 3,
                 "nct": ["NCT02829957", "NCT03045406", "NCT03266783", "NCT01780987"]},
    "reconciliation": {
        "arithmetic": ("82 identified = 54 experimental + 19 comparator + 7 background + 2 "
                       "not_assessable; 80 of the 82 had a role located; 73 candidate pool = "
                       "48 excluded + 25 eligible"),
        "reconciles": True,
        "unscreened_remainder": 0,
        "remainder_means": ("ZERO. The 71 carried at the split have been screened to a "
                            "disposition table. THE REVIEW IS STILL NOT COMPLETE, and the "
                            "reason has changed: it is now 12 eligible trials that have posted "
                            "no results and 8 eligible poolable trials that post no arm-level "
                            "count of the shared estimand, not 71 records nobody has read."),
    },
}

APXT_CASCADE = {
    "k0_surfaced": 82, "k2_role_located": 80, "k3_experimental": 54, "k4_comparator": 19,
    "k5_background": 7, "kNA_not_assessable": 2,
    "k_candidate_pool": 73,
    "k_screened": 73,
    "k_excluded": 48,
    "k_eligible": 25,
    "k_eligible_no_results_yet": 12,
    "k_eligible_not_poolable": 2,
    "k_eligible_poolable": 11,
    "k_with_posted_results_reporting_a_recurrent_VTE_outcome": 8,
    "k_included_in_object": 4,
    "k_pooled": 3,
    "k_unscreened_remainder": 0,
    "reproduced_by": ("scripts/screen_apixaban_split_2026_08_19.py, "
                      "scripts/adjudicate_apixaban_split_2026_08_19.py and "
                      "scripts/repool_apixaban_treatment_2026_08_19.py."),
    "reconciliation": (
        "82 surfaced = 54 experimental + 19 comparator + 7 background + 2 not-assessable; 80 "
        "of the 82 had a role located. 73 place apixaban in the randomised contrast and are "
        "this review's candidate pool. 1 was in the parent object and 72 were screened, so "
        "k_screened = 73. 48 excluded + 25 eligible = 73. Of the 25 eligible, 12 have posted "
        "no results, 2 are eligible and not poolable, and 11 are eligible and poolable. "
        "REMAINDER ZERO."),
    "why_the_remainder_is_now_ZERO_and_was_71": (
        "It was 71 when the split was recorded and the whole remainder has since been screened "
        "-- 39 excluded and 16 sent to adjudication mechanically, the 16 adjudicated by hand. "
        "A REMAINDER IS NOT A QUEUE TO BE DRAINED; screening it is what turned 71 into a "
        "disposition table, and the shape of that table is the finding: 48 of 73 fail a "
        "criterion, and 39 of the 48 fail on POPULATION -- 30 at the mechanical screen and all "
        "9 of the adjudicated exclusions -- because they are thromboprophylaxis trials in "
        "patients who have never had a venous thromboembolism. The surfacing query reaches "
        "across the treatment/prevention boundary because ONE SEARCH OVER ONE DRUG NECESSARILY "
        "DOES; that is a fact about splitting a drug topic in two, not a criticism of the "
        "query, and the sibling review holds the trials this one excludes."),
    "why_k_included_is_4_and_k_pooled_is_3": (
        "The object holds RAMBLE (NCT02829957), which the parent included and which cannot "
        "contribute -- n=19, both arms typed ACTIVE_COMPARATOR, registered primary a pictorial "
        "menstrual blood-loss chart -- together with the three trials that pool. It is kept "
        "and named rather than dropped, because a trial that fails only at the POOLING step is "
        "a fact about this review's evidence base and dropping it would erase that fact. "
        "ELEVEN trials are eligible and poolable and only THREE contribute: the other eight "
        "post no arm-level count of the shared estimand, and each is named on the page."),
}

APXT_CRITERIA = {
    "state": "DERIVED_POST_HOC", "predefined": False, "post_hoc": True, "derived": True,
    "predefined_is_false_because": "written 2026-08-19 when apixaban-vte was split in two, "
                                   "after the parent's included set existed.",
    "authority_it_satisfies": "MECIR R29/R30/R31.",
    "authority_it_does_NOT_establish": "MECIR C5/C7 -- criteria defined in advance.",
    "elements": [
        {"element": "POPULATION",
         "criterion": "adults with acute or recent venous thromboembolism -- deep vein "
                      "thrombosis or pulmonary embolism -- being TREATED for it",
         "auditable_against": "conditionsModule.conditions + designModule.designInfo."
                              "primaryPurpose",
         "settles_it": False,
         "why_it_does_not_settle_it_alone": (
             "primaryPurpose is a REGISTRANT'S CODING and not a fact about the trial. "
             "ADVANCE-2 and ADVANCE-3 are one programme coded on opposite sides of it. The "
             "coded field decides which POOL a trial is counted in; the trial's own design "
             "decides whether it is INCLUDED, and where the two disagree the design wins and "
             "the disagreement is recorded.")},
        {"element": "INTERVENTION", "criterion": "apixaban as the randomised intervention",
         "auditable_against": "armsInterventionsModule.armGroups", "settles_it": True,
         "evidence": "matched against the declared synonym set "
                     "topic_identity.TOPIC_SYNONYMS['apixaban']. Placebo records naming the "
                     "drug -- `Apixaban-matching placebo`, `Apixaban Placebo` -- are NOT the "
                     "drug, which cost three pivotal trials before it was fixed."},
        {"element": "COMPARATOR",
         "criterion": "conventional anticoagulation (heparin/LMWH/vitamin-K antagonist), "
                      "another direct oral anticoagulant, or placebo",
         "auditable_against": "armsInterventionsModule.armGroups", "settles_it": True},
        {"element": "ESTIMAND (poolability, NOT eligibility)",
         "criterion": "recurrent venous thromboembolism, or major bleeding, as a risk ratio "
                      "or hazard ratio",
         "auditable_against": "outcomesModule, EVERY rank", "settles_it": True},
    ],
    "and_this_review_s_own_included_trial_barely_meets_them": (
        "RAMBLE (NCT02829957) is n=19, randomises rivaroxaban against apixaban with BOTH arms "
        "typed ACTIVE_COMPARATOR, and its registered primary is a PICTORIAL MENSTRUAL "
        "BLOOD-LOSS CHART. It is in scope by POPULATION and by INTERVENTION and it will not "
        "pool on this estimand. STATED HERE RATHER THAN DISCOVERED AT THE POOLING STEP, "
        "because a review whose only included trial cannot contribute to its own estimand is "
        "a review whose k=1 is not the number a reader should take away."),
}

# ------------------------------------------------------------------------------------------
# B -- PREVENTION
# ------------------------------------------------------------------------------------------
APXP_SEARCH = {
    "executed_by": "lane 1 (Claude, Anthropic family)",
    "databases": [
        {"database": "ClinicalTrials.gov API v2", "tool": "raw /studies",
         "query_as_executed": _SEARCH_NOTE, "date_executed": "2026-08-19",
         "http_status": 200, "records_returned": 82, "total_reported": 82,
         "recall_on_included_set": "1/1"},
        {"database": "ClinicalTrials.gov API v2 -- FIRST QUERY, RECORDED BECAUSE IT MISSED "
                     "THIS REVIEW'S ONLY TRIAL",
         "tool": "raw /studies",
         "query_as_executed": "same terms with filter.advanced=... AND AREA[Phase](PHASE3 OR "
                              "PHASE4)",
         "date_executed": "2026-08-19", "http_status": 200,
         "records_returned": 49, "total_reported": 49,
         "recall_on_included_set": "0/1 -- IT MISSED NCT02366871 ENTIRELY",
         "what_it_cost": _PHASE_FILTER_NOTE + " FOR THIS REVIEW THE COST WAS TOTAL: its only "
                         "included trial is the PHASE2 one the filter dropped, so the phase-"
                         "filtered search had ZERO recall on this review's evidence base."},
        {"database": "PubMed (NCBI E-utilities esearch)", "tool": "esearch",
         "query_as_executed": "apixaban AND venous thromboembolism",
         "date_executed": "2026-08-19", "http_status": 200,
         "records_returned": 50, "total_reported": 439,
         "recall_on_included_set": "NOT MEASURED",
         "what_is_unexamined": "389 records unexamined, not excluded."},
    ],
    "pagination_verified": "returned == totalCount on both registry queries, from the FIRST "
                           "page.",
}

APXP_PRISMA = {
    "_scope": "PRISMA 2020 flow, counted from the executed search above.",
    "identification": {"ctgov": 82, "pubmed_total": 439, "pubmed_retrieved": 50},
    "eligibility_ctgov": {
        "role_located": 80, "topic_is_experimental_arm": 54, "topic_is_comparator_arm": 19,
        "topic_is_background": 7, "not_assessable": 2,
        "note": "80, not 82 -- see the sibling's note; the parent counted its two "
                "NOT_ASSESSABLE records among the located ones.",
    },
    "screening_of_the_candidate_pool": {
        "screened": 72, "excluded": 42, "eligible": 31,
        "excluded_on": {"POPULATION": 33, "COMPARATOR": 6, "adjudicated_out": 3},
        "eligible_split": {"ELIGIBLE_POOLABLE": 5, "ELIGIBLE_NO_RESULTS_YET": 22,
                           "ELIGIBLE_NOT_POOLABLE": 4},
        "note": "15 of the 72 were UNSETTLED and were adjudicated one by one.",
    },
    "included": {"in_this_object": 5, "contributing_to_the_pool": 4,
                 "nct": ["NCT02366871", "NCT00457002", "NCT00423319", "NCT00371683",
                         "NCT00452530"]},
    "reconciliation": {
        "arithmetic": ("82 identified = 54 + 19 + 7 + 2; 80 role-located; 73 candidate pool = "
                       "42 excluded + 31 eligible"),
        "reconciles": True, "unscreened_remainder": 0,
        "remainder_means": ("ZERO. What limits this review now is that 22 of its 31 eligible "
                            "trials have posted no results."),
    },
}

APXP_CASCADE = {
    "k0_surfaced": 82, "k2_role_located": 80, "k3_experimental": 54, "k4_comparator": 19,
    "k5_background": 7, "kNA_not_assessable": 2,
    "k_candidate_pool": 73,
    "k_screened": 73,
    "k_excluded": 42,
    "k_eligible": 31,
    "k_eligible_no_results_yet": 22,
    "k_eligible_not_poolable": 4,
    "k_eligible_poolable": 5,
    "k_included_in_object": 5,
    "k_pooled": 4,
    "k_unscreened_remainder": 0,
    "reproduced_by": ("scripts/screen_apixaban_split_2026_08_19.py, "
                      "scripts/adjudicate_apixaban_split_2026_08_19.py and "
                      "scripts/repool_apixaban_prophylaxis_2026_08_19.py."),
    "reconciliation": (
        "82 surfaced = 54 + 19 + 7 + 2; 80 of the 82 had a role located. 73 are the candidate "
        "pool; 1 was in the parent object and 72 were screened. 42 excluded + 31 eligible = "
        "73. Of the 31 eligible, 22 have posted no results, 4 are eligible and not poolable, "
        "and 5 are eligible and poolable, of which 4 contribute. REMAINDER ZERO."),
    "why_the_remainder_is_now_ZERO_and_was_71": (
        "The whole remainder has been screened. 33 of this review's 39 mechanical exclusions "
        "fail on POPULATION -- they are treatment trials in patients who have already had a "
        "venous thromboembolism, which is exactly the population the sibling review holds."),
    "AND ITS DOMINANT DISPOSITION IS NOT EXCLUSION": (
        "TWENTY-TWO OF THE THIRTY-ONE ELIGIBLE TRIALS HAVE POSTED NO RESULTS -- more than "
        "twice this review's excluded-on-comparator count and more than four times the number "
        "that pool. Under the reading in PAGE-STANDARD.md, a remainder dominated by "
        "NOT-YET-REPORTED means the query is well aimed and THE FIELD IS STILL IN FLIGHT. The "
        "largest pending trial in either apixaban remainder is NCT06581965, n=10,078, "
        "individualised versus standard thrombosis prophylaxis -- larger than every trial in "
        "this pool combined. It is what will change this answer, and it is named for that "
        "reason."),
}

APXP_CRITERIA = {
    "state": "DERIVED_POST_HOC", "predefined": False, "post_hoc": True, "derived": True,
    "predefined_is_false_because": "written 2026-08-19 when apixaban-vte was split in two.",
    "authority_it_satisfies": "MECIR R29/R30/R31.",
    "authority_it_does_NOT_establish": "MECIR C5/C7.",
    "elements": [
        {"element": "POPULATION",
         "criterion": "adults AT RISK of venous thromboembolism receiving thromboprophylaxis "
                      "-- surgical, medically ill, or cancer-associated",
         "auditable_against": "conditionsModule.conditions + designModule.designInfo."
                              "primaryPurpose",
         "settles_it": False,
         "why_it_does_not_settle_it_alone": "the same ADVANCE-2 / ADVANCE-3 inversion. The "
                                            "coded field counts the pool; the design decides "
                                            "inclusion."},
        {"element": "INTERVENTION", "criterion": "apixaban thromboprophylaxis as the "
                                                 "randomised intervention",
         "auditable_against": "armsInterventionsModule.armGroups", "settles_it": True},
        {"element": "COMPARATOR",
         "criterion": "enoxaparin or another anticoagulant, or placebo / no anticoagulation",
         "auditable_against": "armsInterventionsModule.armGroups", "settles_it": True},
        {"element": "ESTIMAND (poolability, NOT eligibility)",
         "criterion": "symptomatic venous thromboembolism, or major bleeding, as a risk ratio",
         "auditable_against": "outcomesModule, EVERY rank", "settles_it": True},
    ],
    "and_this_review_s_own_included_trial": (
        "NCT02366871 is n=400, apixaban against enoxaparin in suspected pelvic malignancy, "
        "typed EXPERIMENTAL vs ACTIVE_COMPARATOR, and its registered primaries are MAJOR "
        "BLEEDING and clinically relevant non-major bleeding -- a SAFETY estimand. It is in "
        "scope and it does not report the efficacy estimand this review names, so k=1 here is "
        "also not the number to take away."),
}

# ==========================================================================================
# THE BOUNDARY BETWEEN THESE TWO REVIEWS, STATED AS A CRITERION ON BOTH.
#
# It was applied on 2026-08-19 and it existed only inside an adjudication file. A criterion
# that decides which of two reviews a trial belongs to, and which is recorded nowhere either
# review states it, is a rule the reader cannot check and the next lane cannot apply.
#
#     "A RULE YOU HAVE WRITTEN IS NOT A RULE YOU HAVE APPLIED" -- and its other half, which
#     this block is: a rule you have applied is not a rule you have PUBLISHED.
#
# AND IT WAS NOT APPLIED EVERYWHERE IT SHOULD HAVE BEEN, WHICH IS WHY THIS IS NOT A TIDY-UP.
# The boundary reached the SIXTEEN trials that went to adjudication. The NINE that passed the
# mechanical screen were admitted on `primaryPurpose` -- the coded field these very criteria
# say does not settle the question -- and were never put to it. Two of the nine turned on it
# when they finally were, and one of the two moved.
# ==========================================================================================
BOUNDARY_CRITERION = {
    "criterion": ("EXTENDED ANTICOAGULATION IN PATIENTS WHO HAVE ALREADY HAD A VENOUS "
                  "THROMBOEMBOLISM IS TREATMENT. PRIMARY PROPHYLAXIS IN PATIENTS WHO HAVE NOT "
                  "IS PREVENTION."),
    "discriminator": ("whether the randomised population has already had the event, read from "
                      "`eligibilityModule.eligibilityCriteria` and "
                      "`descriptionModule.briefSummary`"),
    "why_not_the_coded_field": (
        "`designModule.designInfo.primaryPurpose` does not carry it, and BOTH registrant "
        "conventions are used for BOTH situations. ADVANCE-2 is knee-replacement "
        "thromboprophylaxis coded TREATMENT; APIDULCIS randomises extended anticoagulation "
        "after a first VTE and is coded PREVENTION. The coded field decides which POOL a trial "
        "is COUNTED in; the trial's own design decides which review INCLUDES it."),
    "authority_it_satisfies": ("MECIR R29/R30/R31 -- eligibility criteria stated and applied "
                               "consistently. The same authority the rest of both criteria "
                               "sets are written against, cited the same way."),
    "authority_it_does_NOT_establish": (
        "MECIR C5/C7. This boundary was written on 2026-08-19, after both reviews' included "
        "sets existed. `predefined: false`, like everything else in these criteria."),
    "predefined": False,
    "where_it_moved_a_trial": {
        "NCT03678506": "APIDULCIS -- coded PREVENTION, admitted to TREATMENT",
        "NCT00452530": "ADVANCE-2 -- coded TREATMENT, admitted to PREVENTION",
        "NCT03080883": "'preventing SECONDARY cancer-related VTE' -- secondary means after a "
                       "first event, so admitted to TREATMENT",
        "NCT05618808": "REGN9933 -- coded TREATMENT, the design is prophylaxis, EXCLUDED from "
                       "treatment",
    },
    "and_a_prediction_it_REFUTED": {
        "stated_before_the_check": True,
        "prediction": ("HI-PRO (NCT04168203) will FAIL this boundary and leave the treatment "
                       "review. Its registered arm is labelled `Extended Duration "
                       "Thromboprophylaxis`, its brief title says `to Prevent Recurrence`, and "
                       "it randomises against placebo -- every surface reads prophylaxis."),
        "indicator_chosen_because_it_could_only_move_one_way": (
            "P32: the test was its ELIGIBILITY TEXT, which states what was enrolled and cannot "
            "be true for both answers. A trial's own words about who may enter it settle "
            "whether the population has had the event; the arm label does not."),
        "outcome": "REFUTED, and the refutation is the finding.",
        "what_the_eligibility_actually_says": (
            "\"Objectively-confirmed provoked DVT and/or PE\" and \"Treated for at least 3 "
            "months with standard therapeutic anticoagulant therapy\". EVERY PARTICIPANT HAS "
            "ALREADY HAD THE EVENT. HI-PRO is extended treatment and it stays."),
        "the_general_form": (
            "THE ARM LABEL SAID PROPHYLAXIS AND THE POPULATION SAID TREATMENT. This is P33 on "
            "the other foot: P33 says a property is not the presence of its own name; this "
            "says a property is not ABSENT because another name is present. Four surfaces "
            "agreed with each other and disagreed with the eligibility criteria, and the "
            "eligibility criteria were right."),
    },
    "what_this_boundary_does_not_do": (
        "It does not make the two reviews clinically homogeneous. Extended anticoagulation "
        "after a completed course and treatment of the acute event are both TREATMENT under "
        "this criterion and they are different clinical questions with different comparators, "
        "which is why the treatment review pools within the acute stratum and states the "
        "extended trials separately rather than averaging across them."),
}

# ==========================================================================================
# THE DIRECTION PAIR -- the one block these two reviews DO share, and the only one.
#
# Everything else here is deliberately kept apart, because three sibling topics built in one
# session is the shape that produced the cross-topic contamination class. This is the
# exception, and it is an exception for a reason that is the opposite of an oversight: THE
# FACT IS ABOUT THE PAIR. Neither half means anything alone.
#
#     apixaban-vte-prophylaxis   poolable set  3 -> 8   the question RECOVERED a pool
#     apixaban-vte-treatment     poolable set  8 -> 3   the question DISSOLVED one
#
# One search, one drug, one night, one discipline, opposite answers.
#
# WHY THIS MATTERS MORE THAN EITHER RESULT. A project that publishes only its recoveries has
# no defence against the obvious reading -- that it asks until it gets the answer it wants.
# Every previous instance of the withholding question in this corpus went the same way:
# sglt2-hf recovered a pool, apixaban prophylaxis recovered a pool. A check that has only ever
# returned the convenient answer is indistinguishable from no check at all.
#
#     THIS IS THE REFUTATION, AND IT AROSE ON ITS OWN. It was not sought, it was not designed,
#     and it cost the treatment review the two largest trials in its field. That is what makes
#     it evidence that the question is a question.
#
# So each object carries BOTH numbers, `scripts/lint_withholding_direction_paired.py` refuses
# an object that states one without the other, and the projector renders them as a table.
# ==========================================================================================
def _direction_pair(topic):
    """The pair, oriented to whichever review is asking. Keyed by topic, never a constant."""
    T = {"topic": "apixaban-vte-treatment", "moved": "8 -> 3",
         "direction": "DOWN -- the question DISSOLVED a pool",
         "detail": ("Eight trials with posted results report an outcome named for recurrent "
                    "VTE. Reading what each one COUNTS leaves three. The two largest trials "
                    "in the field, AMPLIFY and AMPLIFY-EXT, post no recurrent-VTE measure "
                    "without a death term at any registered rank.")}
    P = {"topic": "apixaban-vte-prophylaxis", "moved": "3 -> 8",
         "direction": "UP -- the question RECOVERED a pool",
         "detail": ("Four trials register four different primary composites and would not "
                    "pool. All four also register proximal DVT, non-fatal PE, or VTE-related "
                    "death, at SECONDARY rank in every one. Four trials and 13,570 "
                    "participants, available only because someone asked below the primary.")}
    mine, theirs = (T, P) if topic == "apixaban-vte-treatment" else (P, T)
    return {
        **mine,
        "counter_instance": theirs,
        "why_both_are_stated_together": (
            "THE SAME QUESTION, ASKED THE SAME WAY, ON THE SAME DRUG, ON THE SAME NIGHT, MOVED "
            "ONE REVIEW'S POOLABLE SET UP AND THE OTHER'S DOWN. Every earlier instance in this "
            "corpus recovered a pool, and a check that has only ever returned the convenient "
            "answer cannot be told apart from no check at all. This pair is the refutation, "
            "and it arose on its own rather than being sought: it cost the treatment review "
            "the two largest trials in its field. Asking the withholding question is not a way "
            "of finding more trials. It is a way of finding out."),
        "what_it_does_not_establish": (
            "NOT that either pool is correct -- both were judged by reading endpoint "
            "definitions, and that judgement stands or falls on its own. NOT that the "
            "direction is unpredictable in general; two instances are two instances. What it "
            "establishes is narrow and it is the thing that was missing: THE PROCEDURE HAS NO "
            "BUILT-IN DIRECTION, demonstrated rather than asserted."),
    }


# ------------------------------------------------------------------------------------------
# EXTRACTION -- separate per review, sharing no block, per the contamination rule at the top.
# ------------------------------------------------------------------------------------------
APXT_EXTRACTION = {
    "_why": "Every cell says whether it was READ from a named source or DERIVED, and carries "
            "the sentence it was read from. A cell with no label is not evidence.",
    "verified_utc": "2026-08-19",
    "source": {"registry": "ClinicalTrials.gov; the eleven recoverable registrations read in "
                           "full, and the eight with posted results read again for "
                           "resultsSection.outcomeMeasuresModule",
               "read_via": "raw v2 API, fields=protocolSection,hasResults,resultsSection"},
    "cells": [
        {"field": "NCT03045406 CARAVAGGIO recurrent VTE", "label": "READ",
         "source_path": "resultsSection.outcomeMeasuresModule.outcomeMeasures[0]",
         "verbatim": "Recurrent Venous Thromboembolism -- OG000 Apixaban 32 of 576, "
                     "OG001 Dalteparin 46 of 579",
         "note": "PRIMARY rank. Posted as COUNT_OF_PARTICIPANTS, so the counts are read and "
                 "not derived from a percentage."},
        {"field": "NCT03266783 COBRRA recurrent VTE", "label": "READ",
         "source_path": "resultsSection.outcomeMeasuresModule.outcomeMeasures[3]",
         "verbatim": "Number of Participants With Adjudicated Recurrent Venous Thromboembolism "
                     "(VTE) Events -- OG000 Apixaban Group 15 of 1345, OG001 Rivaroxaban Group "
                     "14 of 1355",
         "note": "SECONDARY rank. Its registered PRIMARY is clinically relevant bleeding, so "
                 "a review reading primaries only would have recorded this trial as reporting "
                 "no efficacy outcome at all."},
        {"field": "NCT01780987 recurrent VTE", "label": "READ",
         "source_path": "resultsSection.outcomeMeasuresModule.outcomeMeasures[1]",
         "verbatim": "Number of Participants With Adjudicated Recurrent Symptomatic Venous "
                     "Thromboembolism (VTE) -- OG000 Apixaban 0 of 38, OG001 UFH/Warfarin "
                     "1 of 40",
         "note": "SECONDARY rank; registered primary is bleeding. A zero cell, and the only "
                 "row in this pool that takes the 0.5 continuity correction."},
        {"field": "NCT00643201 AMPLIFY primary composite", "label": "READ",
         "source_path": "resultsSection.outcomeMeasuresModule.outcomeMeasures[0]."
                        "populationDescription",
         "verbatim": "All randomized participants with a non-missing primary endpoint (n/N: "
                     "59/2609; 71/2635, in apixaban, enoxaparin/warfarin, respectively)",
         "note": "COUNTS READ FROM THE TRIAL'S OWN POPULATION DESCRIPTION, not derived from "
                 "the posted proportion 0.0226 / 0.0269. The two agree; the read one is used."},
        {"field": "NCT00643201 AMPLIFY -- recurrent VTE with no death term", "label": "READ",
         "source_path": "resultsSection.outcomeMeasuresModule.outcomeMeasures[].title, all 21",
         "verbatim": "ABSENT. Every one of AMPLIFY's twenty-one posted outcome measures that "
                     "names recurrent VTE carries a death term.",
         "note": "A NEGATIVE CLAIM, COMPUTED OVER ALL TWENTY-ONE RANKS AND NOT ASSERTED (P17). "
                 "This one absence is why the largest trial in this review contributes to no "
                 "pool it reports."},
        {"field": "NCT00633893 AMPLIFY-EXT primary, WITH imputation", "label": "READ",
         "source_path": "resultsSection.outcomeMeasuresModule.outcomeMeasures[0]."
                        "populationDescription",
         "verbatim": "(n) number of events=32, 34, 96 in apixaban 2.5 mg, 5 mg, and placebo "
                     "arms, respectively; number of events imputed=13, 20, 19",
         "note": "THE SAME REGISTERED ENDPOINT IS POSTED TWICE, typed PRIMARY both times, "
                 "differing only in the trailing 'With Imputation' / 'Without Imputation'."},
        {"field": "NCT00633893 AMPLIFY-EXT primary, WITHOUT imputation", "label": "READ",
         "source_path": "resultsSection.outcomeMeasuresModule.outcomeMeasures[2]."
                        "populationDescription",
         "verbatim": "(n) number of events = 19, 14, 77 in apixaban 2.5 mg, 5 mg, and placebo "
                     "arms, respectively. All events were counted; no events were imputed.",
         "note": "Both cells are carried BECAUSE they differ: 32 against 19 on the same arm "
                 "under the same registered name. A text match returns both, and choosing "
                 "between them by position is P35 one level down."},
        {"field": "NCT04168203 HI-PRO recurrent VTE", "label": "READ",
         "source_path": "resultsSection.outcomeMeasuresModule.outcomeMeasures[0]",
         "verbatim": "Frequency of Symptomatic, Recurrent VTE ... OG000 Extended Duration "
                     "Thromboprophylaxis 4 of 300, OG001 Control 30 of 300"},
        {"field": "NCT04168203 HI-PRO eligibility", "label": "READ",
         "source_path": "protocolSection.eligibilityModule.eligibilityCriteria",
         "verbatim": "Objectively-confirmed provoked DVT and/or PE; Treated for at least 3 "
                     "months with standard therapeutic anticoagulant therapy",
         "note": "THE CELL THAT REFUTED A STATED PREDICTION. Its arm is labelled "
                 "`Extended Duration Thromboprophylaxis`; its population has already had the "
                 "event, so it is treatment."},
        {"field": "NCT02744092 CANVAS randomised arm", "label": "READ",
         "source_path": "protocolSection.armsInterventionsModule.armGroups[0].description",
         "verbatim": "There are four FDA-approved DOAC drugs that may be used for this study: "
                     "Rivaroxaban, Apixaban, Edoxaban, or Dabigatran.",
         "note": "WHAT WAS RANDOMISED IS A CLASS. Apixaban appears in the intervention list "
                 "and is not the randomised intervention, so the posted 6.1% vs 8.8% is a "
                 "DOAC-class effect."},
        {"field": "NCT03196349 COVET registered primaries", "label": "READ",
         "source_path": "resultsSection.outcomeMeasuresModule.outcomeMeasures[0..1].title",
         "verbatim": "Number of Subjects With Clinically Relevant Bleeding Events; Number of "
                     "Subjects With Recurrent Venous Thromboembolism (VTE)",
         "note": "TWO co-primaries, one a harm and one a benefit, in one trial."},
        {"field": "distinct primary component sets across the eleven", "value": "5",
         "label": "DERIVED",
         "derived_by": "scripts/estimand_apixaban_treatment_2026_08_19.py over every "
                       "registered primary, decomposed into components structurally (P33)",
         "note": "{bleeding} 4, {vte} 3, {vte, VTE-related death} 2, {dvt, pe} 1, "
                 "{vte, all-cause death} 1."},
        {"field": "AMPLIFY components summed against its posted composite",
         "value": "61 vs 59 and 76 vs 71", "label": "DERIVED",
         "derived_by": "nonfatal DVT 22/35 + nonfatal PE 27/25 + VTE-related death 12/16, "
                       "against the posted composite 59/71",
         "note": "THE ARITHMETIC THAT REFUSES THE DERIVATION. Reconstructing the missing "
                 "estimand from its components would manufacture 2 events in the apixaban arm "
                 "and 5 in the comparator -- biased toward the drug."},
        {"field": "trials in the pool this review reports", "value": "3 of 8 with results",
         "label": "DERIVED",
         "derived_by": "scripts/repool_apixaban_treatment_2026_08_19.py, coherence screen"},
    ],
}

APXP_EXTRACTION = {
    "_why": "Every cell says whether it was READ from a named source or DERIVED, and carries "
            "the sentence it was read from. A cell with no label is not evidence.",
    "verified_utc": "2026-08-19",
    "source": {"registry": "ClinicalTrials.gov; the five recoverable registrations plus this "
                           "review's own included trial, read in full",
               "read_via": "raw v2 API, fields=protocolSection,hasResults,resultsSection"},
    "cells": [
        {"field": "NCT00457002 ADOPT shared secondary", "label": "READ",
         "source_path": "resultsSection.outcomeMeasuresModule.outcomeMeasures[].title",
         "verbatim": "Incidence of Adjudicated Proximal DVT, Non-Fatal PE or VTE-Related Death",
         "note": "SECONDARY rank in all four contributing trials -- the estimand the "
                 "withholding question recovered."},
        {"field": "NCT00423319 ADVANCE-3 shared secondary", "label": "READ",
         "source_path": "resultsSection.outcomeMeasuresModule.outcomeMeasures[].title",
         "verbatim": "Rate of Composite of Adjudicated Proximal DVT, Nonfatal PE, "
                     "VTE-related death"},
        {"field": "NCT00371683 ADVANCE-1 shared secondary", "label": "READ",
         "source_path": "resultsSection.outcomeMeasuresModule.outcomeMeasures[].title",
         "verbatim": "Event Rate for Participants With Proximal DVT/Non-Fatal PE/VTE-Related "
                     "Death"},
        {"field": "NCT00452530 ADVANCE-2 shared secondary", "label": "READ",
         "source_path": "resultsSection.outcomeMeasuresModule.outcomeMeasures[].title",
         "verbatim": "Rate of Adjudicated Proximal DVT, Nonfatal PE, and VTE-related death",
         "note": "AND FOR THIS TRIAL IT IS ELEMENT ZERO, while for its three companions "
                 "element zero is the PRIMARY. Reading by position would have pooled one "
                 "trial's secondary against three trials' primaries with nothing malformed "
                 "anywhere. P35."},
        {"field": "NCT00452530 ADVANCE-2 primary purpose", "label": "READ",
         "source_path": "protocolSection.designModule.designInfo.primaryPurpose",
         "verbatim": "TREATMENT",
         "note": "Knee-replacement thromboprophylaxis coded TREATMENT. Admitted HERE by the "
                 "boundary criterion, against its own coded field."},
        {"field": "NCT02366871 registered primaries", "label": "READ",
         "source_path": "protocolSection.outcomesModule.primaryOutcomes[].measure",
         "verbatim": "Number of Participants With Incidence of Major Bleeding; Number of "
                     "Participants With Incidence of Clinically Relevant Non Major Bleeding "
                     "Events",
         "note": "This review's ONLY previously included trial, n=400, and its registered "
                 "primary is a SAFETY endpoint -- so the figure this review used to report "
                 "was not an estimate of its own efficacy question."},
        {"field": "the four primary composites, decomposed", "value": "4 distinct component "
                                                                      "sets", "label": "DERIVED",
         "derived_by": "each trial's registered primary read in full and decomposed "
                       "structurally",
         "note": "ADOPT counts VTE-related death; ADVANCE-1 counts ALL-CAUSE death; primary "
                 "event rates span 1.39% to 8.99% across one drug for one indication."},
        {"field": "pooled RR on the shared secondary", "value": "0.7469 (0.4532 to 1.2309)",
         "label": "DERIVED",
         "derived_by": "scripts/repool_apixaban_prophylaxis_2026_08_19.py, "
                       "DerSimonian-Laird on log RR",
         "note": "THE ESTIMATOR IS OWED A CORRECTION. DerSimonian-Laird is biased at k<10 and "
                 "this pool is k=4. The treatment half of this pair, built the same night, "
                 "uses Paule-Mandel with a Knapp-Hartung interval. Recorded as a debt on this "
                 "page rather than left as a silent divergence between two siblings."},
    ],
}
