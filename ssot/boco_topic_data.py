"""Per-topic data for `bococizumab-lipid-review`. Shared with no other topic.

THE RE-ANALYSIS WAS NEVER WHAT WAS MISSING. The odds-ratio-from-counts was replaced on
2026-08-18 with the registry's own least-squares mean differences, and that stands. What the
object said about everything else is why this module exists:

    "search":      "not recorded on the page this object was built from"
    "screening":   "not recorded on the page this object was built from"
    "eligibility": "not recorded on the page this object was built from"

A REVIEW WITH A CORRECTED ESTIMATE AND NO SEARCH IS NOT A CORRECTED REVIEW. Its five trials
were the five somebody once put on a page; nothing established they were the five the question
has. Executed 2026-08-19; the sixth was found and the answer did not move.
"""

BOCO_SEARCH = {
    "executed_by": "lane 1 (Claude, Anthropic family), Claude-side because the analysis "
                   "sandbox that holds the classifier has no network egress",
    "databases": [
        {"database": "ClinicalTrials.gov API v2",
         "tool": "mcp__plugin_bio-research_c-trials__search_trials",
         "query_as_executed": ('intervention="bococizumab"; '
                               'study_type=INTERVENTIONAL; NO phase filter; '
                               'page_size=100; count_total=true'),
         "date_executed": "2026-08-19", "http_status": 200,
         "records_returned": 22, "total_reported": 22,
         "recall_on_included_set": "5/5",
         "pagination_verified": "next_page_token null and returned == totalCount, read from "
                                "the FIRST page."},
        {"database": "ClinicalTrials.gov API v2 -- SECOND QUERY, RECORDED BECAUSE IT DIFFERS",
         "tool": "mcp__plugin_bio-research_c-trials__search_trials",
         "query_as_executed": ('condition="hypercholesterolemia OR dyslipidemia OR '
                               'cardiovascular disease"; intervention="bococizumab"; '
                               'study_type=INTERVENTIONAL'),
         "date_executed": "2026-08-19", "http_status": 200,
         "records_returned": 21, "total_reported": 21,
         "recall_on_included_set": "5/5 -- IT MISSED NOTHING THIS REVIEW INCLUDES",
         "what_it_cost": (
             "ONE RECORD, AND THE INTERESTING PART IS WHICH. The condition-filtered query "
             "drops NCT02458209 (conditions: ['Healthy']) and KEEPS NCT00991159 (conditions: "
             "['Healthy']). TWO PFIZER PHASE-1 RECORDS WITH THE IDENTICAL CODED CONDITIONS "
             "FALL ON OPPOSITE SIDES OF A PARAMETER NAMED FOR THAT FIELD. The `condition` "
             "parameter is not a filter on `conditionsModule.conditions`; it matches "
             "elsewhere in the record too. Recorded, not relied on -- the unfiltered query is "
             "the one this review's cascade is counted from."),
         "and_no_query_missed_an_included_trial_here": (
             "SAID PLAINLY, BECAUSE THREE OTHER TOPICS IN THIS CORPUS LOST ONE TO THEIRS. "
             "sglt2-hf lost DELIVER and iv-iron-hf lost AFFIRM-AHF and HEART-FID to condition "
             "terms one word too narrow; apixaban-vte lost NCT02366871 to a phase filter. A "
             "clean recall is only worth reading if the misses are reported in the same "
             "voice, so it is reported here in that voice.")},
        {"database": "PubMed (NCBI E-utilities esearch)",
         "tool": "mcp__plugin_bio-research_pubmed__search_articles",
         "query_as_executed": "bococizumab",
         "query_translation": '"bococizumab"[Supplementary Concept] OR "bococizumab"[All Fields]',
         "date_executed": "2026-08-19", "http_status": 200,
         "records_returned": 50, "total_reported": 109,
         "recall_on_included_set": "NOT MEASURED",
         "what_is_unexamined": ("109 records matched and 50 were retrieved. THE OTHER 59 ARE "
                               "UNEXAMINED, NOT EXCLUDED, and recall against this review's "
                               "included set was never measured on this database -- so P23 "
                               "cannot hold on it and says so.")},
    ],
    "pagination_verified": "returned == totalCount on both registry queries, totalCount read "
                           "from the FIRST page.",
}

BOCO_PRISMA = {
    "_scope": "PRISMA 2020 flow, counted from the executed search above.",
    "identification": {"ctgov": 22, "pubmed_total": 109, "pubmed_retrieved": 50},
    "eligibility_ctgov": {
        "role_located": 21, "topic_is_experimental_arm": 18, "topic_is_comparator_arm": 0,
        "topic_is_background": 3, "not_assessable": 1,
        "note": ("Arm roles read by `ssot/topic_identity.locate()` over the raw v2 armGroups "
                 "with the declared synonym set. ZERO comparator is a COMPUTED zero over 22 "
                 "classified records, not an empty field: bococizumab was never marketed and "
                 "no trial uses it as the established control."),
    },
    "screening_of_the_candidate_pool": {
        "screened": 22, "excluded": 7, "eligible": 14, "not_assessable": 1,
        "excluded_on": {"POPULATION": 4, "COMPARATOR": 2, "INTERVENTION": 3,
                        "_note": "limbs are counted per FAILING LIMB and a record may fail "
                                 "more than one, so these do not sum to 7"},
        "eligible_split": {"INCLUDED": 5, "ELIGIBLE_POOLABLE_NOT_INCLUDED": 5,
                           "ELIGIBLE_NOT_POOLABLE": 3, "ELIGIBLE_NO_RESULTS_YET": 1},
    },
    "included": {"in_this_object": 6, "contributing_to_the_pool": 6,
                 "nct": ["NCT01968967", "NCT02100514", "NCT01968954", "NCT02458287",
                         "NCT02135029", "NCT01968980"]},
    "reconciliation": {
        "arithmetic": ("22 identified = 18 experimental + 0 comparator + 3 background + 1 "
                       "not-assessable; 21 of the 22 had a role located. 22 screened = 7 "
                       "excluded + 14 eligible + 1 not-assessable."),
        "reconciles": True,
        "unscreened_remainder": 0,
        "remainder_means": ("ZERO. Every surfaced registration has a disposition. What limits "
                            "this review is not unread records: it is FOUR DOSE-RANGING "
                            "TRIALS that are eligible, have posted LDL results, and cannot "
                            "contribute a single contrast."),
    },
}

BOCO_CASCADE = {
    "k0_surfaced": 22,
    "k2_role_located": 21,
    "k3_experimental": 18,
    "k4_comparator": 0,
    "k5_background": 3,
    "kNA_not_assessable": 1,
    "k_screened": 22,
    "k_excluded": 7,
    "k_eligible": 14,
    "k_eligible_poolable": 10,
    "k_eligible_not_poolable": 3,
    "k_eligible_no_results_yet": 1,
    "k_included_in_object": 6,
    "k_pooled": 6,
    "k_unscreened_remainder": 0,
    "reproduced_by": ("scripts/screen_bococizumab_2026_08_19.py and "
                      "scripts/repool_bococizumab_2026_08_19.py."),
    "why_k_went_5_to_6": (
        "SPIRE-FH (NCT01968980, n=370) was surfaced by this review's own search, passed its "
        "own criteria, registers the IDENTICAL primary at the IDENTICAL timepoint, posts a "
        "least-squares mean difference in its own `analyses` block -- and was not in the "
        "object, because this review had no executed search until 2026-08-19."),
    "and_FOUR_more_are_eligible_with_results_and_do_not_pool": (
        "NCT01342211, NCT01350141, NCT02055976 and NCT01592240. Each randomised DOSE. "
        "ELIGIBLE WITH RESULTS IS NOT POOLABLE, and the four are named on the page with their "
        "own numbers so the refusal costs something inspectable."),
}

BOCO_CRITERIA = {
    "state": "DERIVED_POST_HOC", "predefined": False, "post_hoc": True, "derived": True,
    "predefined_is_false_because": ("written 2026-08-19, when this review's search was "
                                    "executed for the first time -- years after its included "
                                    "set existed on a page."),
    "authority_it_satisfies": "MECIR R29/R30/R31.",
    "authority_it_does_NOT_establish": "MECIR C5/C7 -- criteria defined in advance.",
    "elements": [
        {"element": "POPULATION",
         "criterion": "adults with a lipid disorder -- primary hyperlipidaemia, mixed "
                      "dyslipidaemia, hypercholesterolaemia, or heterozygous familial "
                      "hypercholesterolaemia",
         "auditable_against": "conditionsModule.conditions, against a declared term set",
         "settles_it": True,
         "evidence": "A record whose only condition is `Healthy` is not in this population, "
                     "and that limb removes the phase-1 pharmacology programme. A record "
                     "whose only condition is `Cardiovascular Disease` is not either -- that "
                     "is the SPIRE-1/SPIRE-2 outcomes programme, which asks a different "
                     "question with a different endpoint."},
        {"element": "INTERVENTION", "criterion": "bococizumab as the randomised intervention",
         "auditable_against": "armsInterventionsModule.armGroups via topic_identity.locate()",
         "settles_it": True,
         "evidence": "matched against the declared synonym set "
                     "topic_identity.TOPIC_SYNONYMS['bococizumab'], which carries the "
                     "DEVELOPMENT CODES `pf-04950615` and `rn316`. Eleven of the twenty-two "
                     "surfaced registrations name the drug by a code and not by its name, so "
                     "a screen matching 'bococizumab' would have found half of them."},
        {"element": "COMPARATOR",
         "criterion": "placebo, or an active lipid-lowering comparator",
         "auditable_against": "arm TYPE **or** what the arms RECEIVE -- either suffices",
         "settles_it": True,
         "evidence": "READ BOTH WAYS BECAUSE EACH IS BLIND TO A REAL DESIGN. By type alone, "
                     "NCT01592240 has no comparator -- both its arms are typed EXPERIMENTAL "
                     "with `Drug: PBO` inside each. By intervention name alone, NCT01243151 "
                     "has none either -- its placebo arm carries no intervention record. It "
                     "takes BOTH readings to fail, and NCT01435382 still fails: four arms, "
                     "all carrying PF-04950615, nothing else."},
        {"element": "ESTIMAND (poolability, NOT eligibility)",
         "criterion": "percent change from baseline in LDL-C at WEEK 12, as a mean difference",
         "auditable_against": "outcomesModule, EVERY rank", "settles_it": True,
         "evidence": "Detected STRUCTURALLY -- an LDL term plus a change term -- and never by "
                     "the registered phrase. Matching the five incumbents' wording would have "
                     "found the five that already agree and nothing else. THE TIMEPOINT IS "
                     "PART OF THE ESTIMAND: three of the four dose-ranging trials post Day 85 "
                     "or Day 113, and one posts 'Week 12 and 24' combined in a single "
                     "measure."},
    ],
    "and_a_dose_ranging_design_is_eligible_and_not_poolable": (
        "Stated here rather than discovered at the pooling step. A dose-ranging trial "
        "randomised DOSE; pooling one of its arms against placebo means choosing which arm, "
        "and no rule in this review chooses it. Inside NCT01342211 alone the effect runs from "
        "-2.30 to -49.11 percentage points -- a spread wider than the entire pool. THE CHOICE "
        "WOULD BE OURS AND IT WOULD LOOK LIKE THE TRIAL'S."),
}

BOCO_EXTRACTION = {
    "_why": "Every cell says whether it was READ from a named source or DERIVED, and carries "
            "the sentence it was read from. A cell with no label is not evidence.",
    "verified_utc": "2026-08-19",
    "source": {"registry": "ClinicalTrials.gov, 22 surfaced registrations; the ten with an "
                           "LDL percent-change outcome read in full",
               "read_via": "raw v2 API, fields=protocolSection,hasResults,resultsSection"},
    "cells": [
        {"field": "NCT01968980 SPIRE-FH registered primary", "label": "READ",
         "source_path": "protocolSection.outcomesModule.primaryOutcomes[0].measure",
         "verbatim": "Percent Change From Baseline in Low Density Lipoprotein Cholesterol "
                     "(LDL-C) at Week 12",
         "note": "The IDENTICAL endpoint at the IDENTICAL timepoint as all five incumbents."},
        {"field": "NCT01968980 SPIRE-FH effect", "label": "READ",
         "source_path": "resultsSection.outcomeMeasuresModule.outcomeMeasures[0].analyses[0]",
         "verbatim": "Least square (LS) mean difference = -54.5, 95% CI -59.5 to -49.5, "
                     "MMRM, p<0.001",
         "note": "Same provenance as every value already in the pool. NOTHING IS DERIVED."},
        {"field": "NCT01342211 dose contrasts", "label": "READ",
         "source_path": "resultsSection.outcomeMeasuresModule.outcomeMeasures[0].analyses[]",
         "verbatim": "LS Mean Difference -5.63, -2.30, -37.72, -49.11 for 0.25, 1.0, 3.0 and "
                     "6.0 mg/kg against one placebo, at Day 85",
         "note": "FOUR CONTRASTS FROM ONE TRIAL, spanning more than the whole pool. This one "
                 "cell is why a dose-ranging trial is not one contrast."},
        {"field": "NCT02055976 dose contrasts", "label": "READ",
         "source_path": "resultsSection.outcomeMeasuresModule.outcomeMeasures[0..1].analyses[]",
         "verbatim": "Adjusted Mean Difference -49.838 to -71.534 across six dose/route arms "
                     "against TWO separate placebos, at Day 85 AND Day 113",
         "note": "TWO co-primary timepoints, neither of them Week 12."},
        {"field": "NCT01592240 percent-change rank", "label": "READ",
         "source_path": "protocolSection.outcomesModule",
         "verbatim": "PRIMARY: 'Change From Baseline in Low-density Lipoprotein Cholesterol "
                     "(LDL-C) at Week 12'; SECONDARY: 'Percent Change From Baseline in Low "
                     "Density Lipoprotein Cholesterol (LDL-C) at Week 12 and 24'",
         "note": "Its PRIMARY is ABSOLUTE change. The percent change exists only at secondary "
                 "rank and only as a COMBINED two-timepoint measure, so there is no Week-12 "
                 "percent-change contrast to take."},
        {"field": "NCT02135029 SPIRE-SI arm role", "label": "READ",
         "source_path": "protocolSection.armsInterventionsModule.armGroups[].type",
         "verbatim": "EXPERIMENTAL 'Bococizumab'; ACTIVE_COMPARATOR 'Atorvastatin'; "
                     "PLACEBO_COMPARATOR 'Placebo'",
         "note": "THE TRIAL THAT CAUGHT DEFECT CLASS 19. Screened with the topic NAME instead "
                 "of the synonym LIST, its atorvastatin arm 'contained bococizumab' on the "
                 "strength of its letters and this included trial was excluded."},
        {"field": "NCT02458287 SPIRE-AI control records", "label": "READ",
         "source_path": "protocolSection.armsInterventionsModule.interventions[].name",
         "verbatim": "Bococizumab 150mg placebo; Bococizumab 75mg placebo",
         "note": "The TRAILING-placebo convention. A comparator limb testing whether a "
                 "synonym is a substring of the name calls these records the drug."},
        {"field": "arm roles across the surfaced set", "value": "18 / 0 / 3 / 1",
         "label": "DERIVED",
         "derived_by": "ssot/topic_identity.locate() over raw v2 armGroups with the declared "
                       "synonym set and both placebo discriminators"},
        {"field": "trials with an LDL percent-change outcome at ANY rank", "value": "10 of 22",
         "label": "DERIVED",
         "derived_by": "structural detection -- an LDL term plus a change term -- over every "
                       "registered rank, scripts/screen_bococizumab_2026_08_19.py"},
        {"field": "pooled mean difference", "value": "-55.2406 (-57.9243 to -52.5569), k=6",
         "label": "DERIVED",
         "derived_by": "scripts/repool_bococizumab_2026_08_19.py, REML inverse-variance over "
                       "six READ least-squares mean differences",
         "note": "Standard errors are DERIVED from each printed 95% interval; the point "
                 "estimates and intervals themselves are READ."},
    ],
}
