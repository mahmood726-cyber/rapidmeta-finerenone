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
    "included": {"in_this_object": 1, "nct": ["NCT02829957"]},
    "reconciliation": {
        "arithmetic": "82 identified = 54 experimental + 19 comparator + 7 background + 2 "
                      "not_assessable; 80 of the 82 had a role located",
        "reconciles": True,
        "unscreened_remainder": 71,
        "remainder_means": "73 trials place apixaban in the randomised contrast; 1 is in this "
                           "object; 71 are UNSCREENED and are carried as a number rather than "
                           "as a zero. THIS REVIEW IS NOT COMPLETE.",
    },
}

APXT_CASCADE = {
    "k0_surfaced": 82, "k2_role_located": 80, "k3_experimental": 54, "k4_comparator": 19,
    "k5_background": 7, "kNA_not_assessable": 2,
    "k_included_in_object": 1, "k_unscreened_remainder": 71,
    "reproduced_by": "scripts/regate_cascade_2026_08_19.py and the parent's recorded search.",
    "why_k_is_1_and_the_review_is_still_worth_building": (
        "The parent held TWO trials that fall on opposite sides of this split. This review "
        "keeps RAMBLE (NCT02829957) and the sibling keeps NCT02366871. NEITHER TRIAL IS "
        "DISCARDED -- that is the whole point of building both -- but k=1 here is a floor and "
        "not an answer: 34 of the 73 randomised-apixaban trials are coded TREATMENT and 15 of "
        "those are COMPLETED, five with n >= 1000. THE UNSCREENED REMAINDER IS WHERE THIS "
        "REVIEW'S EVIDENCE BASE ACTUALLY IS, and it is 71."),
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
    "included": {"in_this_object": 1, "nct": ["NCT02366871"]},
    "reconciliation": {
        "arithmetic": "82 identified = 54 experimental + 19 comparator + 7 background + 2 "
                      "not_assessable; 80 of the 82 had a role located",
        "reconciles": True, "unscreened_remainder": 71,
        "remainder_means": "71 UNSCREENED, carried as a number. THIS REVIEW IS NOT COMPLETE.",
    },
}

APXP_CASCADE = {
    "k0_surfaced": 82, "k2_role_located": 80, "k3_experimental": 54, "k4_comparator": 19,
    "k5_background": 7, "kNA_not_assessable": 2,
    "k_included_in_object": 1, "k_unscreened_remainder": 71,
    "reproduced_by": "scripts/regate_cascade_2026_08_19.py and the parent's recorded search.",
    "why_k_is_1_and_the_review_is_still_worth_building": (
        "33 of the 73 randomised-apixaban trials are coded PREVENTION and 17 are COMPLETED, "
        "four with n >= 1000 -- ADOPT (n=6758), ADVANCE-3 (n=5407), ADVANCE-1 (n=3608). NONE "
        "OF THEM IS IN THIS OBJECT. k=1 is a floor and the 71-trial remainder is where this "
        "review's evidence base is."),
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
