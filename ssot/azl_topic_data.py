"""Per-topic data for `azilsartan-chlorthalidone-vs-olmesartan-hctz`. Shared with no other topic.

THIS TOPIC IS THE OPPOSITE SHAPE TO THE OTHERS BUILT ON 2026-08-19. Its question was already a
REAL QUESTION -- a named head-to-head, a named estimand, a named timepoint -- and its two trials
genuinely share both arms. Nothing had to be restated and no estimate had to be withdrawn.

What it had never had is any evidence that its two trials are the only two, and that is what
the executed search of 2026-08-19 supplies. THE ANSWER IS THAT THEY ARE, and the two further
head-to-heads the search found cannot contribute because both registered SAFETY endpoints only.
"""

AZL_SEARCH = {
    "executed_by": "lane 1 (Claude, Anthropic family), Claude-side because the analysis "
                   "sandbox that holds the classifier has no network egress",
    "databases": [
        {"database": "ClinicalTrials.gov API v2",
         "tool": "mcp__plugin_bio-research_c-trials__search_trials",
         "query_as_executed": ('intervention="azilsartan"; study_type=INTERVENTIONAL; '
                               'NO phase filter; page_size=100; count_total=true'),
         "date_executed": "2026-08-19", "http_status": 200,
         "records_returned": 57, "total_reported": 57,
         "recall_on_included_set": "2/2",
         "why_the_query_is_the_DRUG_and_not_the_CONTRAST": (
             "Searching for the contrast -- azilsartan AND chlorthalidone AND olmesartan -- "
             "would have surfaced only trials that already name all three, which is the set "
             "this review already holds. A query built from the included set cannot discover "
             "anything the included set does not already contain. The whole drug programme is "
             "surfaced and the CONTRAST is applied at SCREENING, where it is auditable."),
         "pagination_verified": "next_page_token null and returned == totalCount, from the "
                                "FIRST page."},
        {"database": "PubMed (NCBI E-utilities esearch)",
         "tool": "mcp__plugin_bio-research_pubmed__search_articles",
         "query_as_executed": "NOT EXECUTED FOR THIS TOPIC",
         "date_executed": "2026-08-19", "http_status": None,
         "records_returned": None, "total_reported": None,
         "recall_on_included_set": "NOT MEASURED",
         "what_is_unexamined": (
             "NO PUBMED SEARCH WAS RUN FOR THIS TOPIC. Recorded as an absence rather than "
             "omitted: the registry search is the only executed search behind this review, so "
             "any trial reported in the literature and never registered is outside what was "
             "looked at. P23 cannot hold on a database nobody queried, and this says so "
             "instead of leaving the row out.")},
    ],
    "pagination_verified": "returned == totalCount on the registry query, from the FIRST page.",
}

AZL_PRISMA = {
    "_scope": "PRISMA 2020 flow, counted from the executed search above.",
    "identification": {"ctgov": 57, "pubmed": None},
    "eligibility_ctgov": {
        "role_located": 57, "topic_is_experimental_arm": 45, "topic_is_comparator_arm": 4,
        "topic_is_background": 8, "not_assessable": 0,
        "note": ("Arm roles read by `ssot/topic_identity.locate()` over the raw v2 armGroups. "
                 "kNA = 0 is a COMPUTED zero over 57 classified records, not an empty field."),
    },
    "screening_of_the_candidate_pool": {
        "screened": 57, "excluded": 53, "eligible": 4,
        "excluded_on": {"POPULATION": 13, "INTERVENTION": 47, "COMPARATOR": 53,
                        "_note": "counted per FAILING LIMB; a record may fail more than one, "
                                 "so these do not sum to 53. COMPARATOR is 53 of 53 -- EVERY "
                                 "excluded record fails it, because only four registrations "
                                 "in the whole programme carry an olmesartan-plus-"
                                 "hydrochlorothiazide arm at all."},
        "eligible_split": {"INCLUDED": 2, "ELIGIBLE_NOT_POOLABLE": 2},
    },
    "included": {"in_this_object": 2, "contributing_to_the_pool": 2,
                 "nct": ["NCT00846365", "NCT01033071"]},
    "reconciliation": {
        "arithmetic": ("57 identified = 45 experimental + 4 comparator + 8 background + 0 "
                       "not-assessable; 57 screened = 53 excluded + 4 eligible"),
        "reconciles": True,
        "unscreened_remainder": 0,
        "remainder_means": ("ZERO. Every surfaced registration has a disposition, and the "
                            "review's included set is UNCHANGED at 2 -- which is a result of "
                            "the search rather than an assumption it started from."),
    },
}

AZL_CASCADE = {
    "k0_surfaced": 57,
    "k2_role_located": 57,
    "k3_experimental": 45,
    "k4_comparator": 4,
    "k5_background": 8,
    "kNA_not_assessable": 0,
    "k_screened": 57,
    "k_excluded": 53,
    "k_eligible": 4,
    "k_eligible_not_poolable": 2,
    "k_included_in_object": 2,
    "k_pooled": 2,
    "k_unscreened_remainder": 0,
    "reproduced_by": "scripts/screen_azilsartan_2026_08_19.py.",
    "why_53_of_57_ARE_EXCLUDED_AND_THAT_IS_NOT_A_CRITICISM_OF_THE_QUERY": (
        "The query is the whole azilsartan programme and the review is ONE fixed-dose "
        "combination against ONE other. ALL 53 EXCLUSIONS FAIL ON COMPARATOR -- only four "
        "registrations in the entire programme carry an olmesartan-plus-hydrochlorothiazide "
        "arm, and the other fifty-three randomise azilsartan against valsartan, olmesartan "
        "alone, ramipril, candesartan, amlodipine, or placebo. All are perfectly good "
        "contrasts and none is this one. THE QUERY WAS DELIBERATELY BUILT FROM THE DRUG AND "
        "NOT FROM THE "
        "CONTRAST: a query built from the contrast could only have returned trials already "
        "naming all three agents, which is the set this review already held, and a search "
        "that can only confirm the included set is not a search."),
    "and_the_included_set_DID_NOT_CHANGE": (
        "k stays 2. THE THIRD DIRECTION AGAIN, on a second topic and by a different route: "
        "bococizumab's evidence base was checked and gained one trial; this one was checked "
        "and gained none. Before either search, neither review could tell a correct included "
        "set from an unexamined one."),
}

AZL_CRITERIA = {
    "state": "DERIVED_POST_HOC", "predefined": False, "post_hoc": True, "derived": True,
    "predefined_is_false_because": ("written 2026-08-19, when this review's search was "
                                    "executed for the first time."),
    "authority_it_satisfies": "MECIR R29/R30/R31.",
    "authority_it_does_NOT_establish": "MECIR C5/C7 -- criteria defined in advance.",
    "and_they_are_narrow_because_the_QUESTION_is": (
        "A review of ONE fixed-dose combination against ONE other has narrow criteria by "
        "construction, and narrowness is only a defect when it is derived BACKWARDS from the "
        "trials already present. Every limb below is auditable against a registry field, and "
        "the screen was run over the whole 57-record drug programme rather than over a "
        "shortlist."),
    "elements": [
        {"element": "POPULATION", "criterion": "adults with essential or primary hypertension",
         "auditable_against": "conditionsModule.conditions, against a declared term set",
         "settles_it": False,
         "why_it_does_not_settle_it_alone": (
             "A CONDITION THAT NAMES A STUDY OBJECTIVE IS NOT A STATEMENT ABOUT THE "
             "POPULATION. NCT01309828 declares `conditions: ['Safety']` while its title reads "
             "'...in Hypertensive Subjects With Moderate Renal Impairment', and it carries "
             "BOTH arms of this review's contrast. The field is neither absent nor negative; "
             "it is UNINFORMATIVE, and excluding on it asserts something the record nowhere "
             "says. Where every declared condition names an objective the coded field is "
             "NOT_ASSESSABLE for this limb and the verdict falls back to the TITLE -- and says "
             "on its face which it rests on. The fallback still excludes: NCT03652792 declares "
             "a bioequivalence objective and its title says 'in Chinese Healthy Volunteers'.")},
        {"element": "INTERVENTION",
         "criterion": "azilsartan medoxomil TOGETHER WITH chlorthalidone, as the randomised "
                      "intervention",
         "auditable_against": "armsInterventionsModule.armGroups -- label, description and "
                              "interventionNames", "settles_it": True,
         "evidence": ("Both agents must appear in the SAME arm. Azilsartan monotherapy is a "
                      "different intervention and azilsartan with amlodipine is another. "
                      "Matched against the declared synonym set including the Takeda "
                      "development codes TAK-491 and TAK-536, which name the drug in eight of "
                      "the fifty-seven surfaced records.")},
        {"element": "COMPARATOR",
         "criterion": "olmesartan medoxomil TOGETHER WITH hydrochlorothiazide",
         "auditable_against": "armsInterventionsModule.armGroups", "settles_it": True,
         "evidence": ("48 of the 53 exclusions fail here, and each names what it randomised "
                      "instead. The limb is independent of the intervention limb and is shown "
                      "to be: NCT00847626 randomises AZL-CLD against chlorthalidone alone and "
                      "fails COMPARATOR ONLY.")},
        {"element": "ESTIMAND (poolability, NOT eligibility)",
         "criterion": "change from baseline in clinic systolic blood pressure",
         "auditable_against": "outcomesModule, EVERY rank", "settles_it": True,
         "evidence": ("Detected STRUCTURALLY -- a blood-pressure term plus a change term -- at "
                      "every rank, never by the incumbents' registered phrase. THIS IS THE "
                      "LIMB THAT DECIDES THE TWO RECOVERED HEAD-TO-HEADS: NCT00996281 and "
                      "NCT01309828 share both arms and register NO blood-pressure change "
                      "outcome at any of their two and four ranks. Both are long-term "
                      "open-label SAFETY studies.")},
    ],
}

AZL_EXTRACTION = {
    "_why": "Every cell says whether it was READ from a named source or DERIVED, and carries "
            "the sentence it was read from. A cell with no label is not evidence.",
    "verified_utc": "2026-08-19",
    "source": {"registry": "ClinicalTrials.gov, 57 surfaced registrations; the four sharing "
                           "both arms read in full",
               "read_via": "raw v2 API, fields=protocolSection,hasResults,resultsSection"},
    "cells": [
        {"field": "NCT00846365 arms", "label": "READ",
         "source_path": "protocolSection.armsInterventionsModule.armGroups[].interventionNames",
         "verbatim": "Azilsartan medoxomil and chlorthalidone; Olmesartan "
                     "medoxomil-hydrochlorothiazide",
         "note": "Both halves of this review's contrast, in one trial."},
        {"field": "NCT01033071 arms", "label": "READ",
         "source_path": "protocolSection.armsInterventionsModule.armGroups[].interventionNames",
         "verbatim": "Azilsartan medoxomil and chlorthalidone; Olmesartan medoxomil and "
                     "hydrochlorothiazide"},
        {"field": "NCT01309828 registered condition", "label": "READ",
         "source_path": "protocolSection.conditionsModule.conditions",
         "verbatim": "Safety",
         "note": "A STUDY OBJECTIVE IN THE FIELD MEANT FOR THE DISEASE. Its title names "
                 "hypertensive subjects and it carries both arms of this contrast; excluding "
                 "on this field would have asserted something the record nowhere says."},
        {"field": "NCT01309828 registered ranks", "label": "READ",
         "source_path": "protocolSection.outcomesModule",
         "verbatim": "4 registered outcomes, NONE of them a blood-pressure change",
         "note": "The estimand limb, not the population limb, is what keeps it out of the "
                 "pool -- and that is a different statement about the trial."},
        {"field": "NCT00996281 registered ranks", "label": "READ",
         "source_path": "protocolSection.outcomesModule",
         "verbatim": "2 registered outcomes, NEITHER a blood-pressure change",
         "note": "n=837, open-label, long-term safety and tolerability. It shares both arms "
                 "with the two included trials and reports nothing this review can pool."},
        {"field": "NCT00847626 comparator", "label": "READ",
         "source_path": "protocolSection.armsInterventionsModule.armGroups[]",
         "verbatim": "Azilsartan medoxomil and chlorthalidone; Chlorthalidone; Azilsartan "
                     "medoxomil",
         "note": "The right INTERVENTION and the wrong COMPARATOR. It fails one limb only, "
                 "which is what shows the two limbs are independent tests rather than one "
                 "test written twice."},
        {"field": "arm roles across the surfaced set", "value": "45 / 4 / 8 / 0",
         "label": "DERIVED",
         "derived_by": "ssot/topic_identity.locate() over raw v2 armGroups with the declared "
                       "synonym set"},
        {"field": "exclusions by failing limb", "value": "COMPARATOR 53, INTERVENTION 47, "
                                                         "POPULATION 13",
         "label": "DERIVED",
         "derived_by": "scripts/screen_azilsartan_2026_08_19.py; counted per limb, and a "
                       "record failing two limbs is counted in both",
         "note": "COMPARATOR is 53 OF 53 -- every excluded record fails it. That is a fact "
                 "about a NARROW QUESTION asked of a WHOLE DRUG PROGRAMME, not a criticism of "
                 "the query. THESE THREE NUMBERS WERE FIRST WRITTEN AS 48 / 30 / 13 FROM "
                 "RECOLLECTION AND WERE WRONG; they are now read from the screening file, "
                 "which is what `k` fields are for."},
    ],
}
