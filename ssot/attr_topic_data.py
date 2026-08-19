"""Per-topic build data for `attr-cm-review`, KEYED TO THE TOPIC AND IN ITS OWN MODULE."""

ATTR_SEARCH = {
    "executed_by": "lane 1 (Claude, Anthropic family)",
    "databases": [
        {"database": "ClinicalTrials.gov API v2 -- intervention, all brands and codes",
         "tool": "https://clinicaltrials.gov/api/v2/studies (raw, curl)",
         "query_as_executed": (
             "query.intr=\"tafamidis OR acoramidis OR vyndaqel OR vyndamax OR attruby OR "
             "AG10\"; filter.advanced=AREA[StudyType]INTERVENTIONAL; pageSize=300; "
             "countTotal=true"),
         "date_executed": "2026-08-19", "http_status": 200,
         "records_returned": 55, "total_reported": 55,
         "recall_on_included_set": "2/2",
         "why_intervention_only": (
             "No condition filter. ATTR amyloidosis is registered under cardiomyopathy, "
             "polyneuropathy, and bare 'amyloidosis' interchangeably, and the two preceding "
             "topics both lost included trials to a condition term one word narrower than the "
             "registry's own. The population limb is applied at SCREENING, from "
             "conditionsModule, where it can be read per trial rather than guessed once."),
        },
    ],
    "pagination_verified": "records_returned == total_reported (55/55); no page boundary.",
}

ATTR_PRISMA = {
    "_scope": "PRISMA 2020 flow, counted from the executed search above.",
    "identification": {"ctgov": 55},
    "eligibility_ctgov": {"role_located": 55, "topic_is_experimental_arm": 48,
                          "topic_is_comparator_arm": 3, "topic_is_background": 1,
                          "not_assessable": 3},
    "included": {"in_this_object": 2, "nct": ["NCT01994889", "NCT03860935"]},
    "reconciliation": {
        "arithmetic": "55 identified = 48 experimental + 3 comparator + 1 background + 3 not_assessable",
        "reconciles": True,
        "unscreened_remainder": 0,
        "remainder_means": (
            "48 trials place tafamidis or acoramidis in the randomised experimental arm; 2 are "
            "in this object; the other 46 were ALL SCREENED on 2026-08-19. Dispositions: 31 "
            "excluded, 2 eligible but not poolable, 13 eligible with no results yet."),
    },
}

ATTR_CASCADE = {
    "k0_surfaced": 55, "k2_role_located": 55,
    "k3_experimental": 48, "k4_comparator": 3,
    "k5_background": 1, "kNA_not_assessable": 3,
    "k_included_in_object": 2, "k_unscreened_remainder": 0,
    "remainder_dispositions": {
        "EXCLUDED": 31, "ELIGIBLE_NOT_POOLABLE": 2, "ELIGIBLE_NO_RESULTS_YET": 13,
        "what_this_says": (
            "READ BY THE REMAINDER-DIAGNOSIS RULE: 31 of 46 fail a criterion, and the dominant "
            "ground is COMPARATOR -- only 6 of the 46 declare a placebo arm at all. This is a "
            "drug programme dominated by OPEN-LABEL EXTENSION and single-arm studies, so the "
            "query is well aimed and the randomised evidence is genuinely thin. Neither the "
            "too-broad-query shape nor the fragmented-estimand shape: a third reading, where "
            "the field itself has produced few controlled trials."),
        "no_poolable_candidates": (
            "ZERO trials in the remainder are eligible AND poolable -- unlike alirocumab-lipid, "
            "where screening recovered two. Stated explicitly because a zero here is a real "
            "result about this evidence base rather than an absence of effort."),
    },
    "why_k_included_is_2_and_stays_2": (
        "THE POOLING OBSTACLE IS THE ESTIMAND, NOT THE EVIDENCE BASE. Both included trials "
        "register HIERARCHICAL endpoints analysed by win ratio, and the two hierarchies are "
        "not the same hierarchy: ATTR-ACT combines all-cause mortality with CV-related "
        "hospitalisation frequency (2 tiers); ATTRibute-CM adds NT-proBNP change and "
        "6-minute-walk change (4 tiers). Verified from the registry 2026-08-19. A win ratio's "
        "estimand IS its hierarchy and cannot be recovered from a 2x2 table. TWO DIFFERENT "
        "HIERARCHIES ARE TWO ESTIMANDS, NOT HETEROGENEITY -- so k=2 is the count of included "
        "trials and NOT a pooled k."),
}

ATTR_EXTRACTION = {
    "_why": "Every cell says whether it was READ from a named source or DERIVED, and carries "
            "the sentence it was read from. A cell with no label is not evidence.",
    "verified_utc": "2026-08-19",
    "source": {"registry": "ClinicalTrials.gov, two registrations",
               "read_via": "raw v2 API, fields=protocolSection"},
    "cells": [
        {"field": "NCT01994889 ATTR-ACT primary", "label": "READ",
         "source_path": "protocolSection.outcomesModule.primaryOutcomes[0].measure",
         "verbatim": "Hierarchical Combination of All-Cause Mortality and Frequency of "
                     "Cardiovascular-Related Hospitalizations"},
        {"field": "NCT03860935 ATTRibute-CM primary", "label": "READ",
         "source_path": "protocolSection.outcomesModule.primaryOutcomes[0].measure",
         "verbatim": "A Hierarchical Combination of All-Cause Mortality, Cumulative Frequency "
                     "of CV-related Hospitalization, Change From Baseline in NT-proBNP and "
                     "Change From Baseline in 6-Minute Walk Distance"},
        {"field": "hierarchies differ", "value": "2 tiers vs 4 tiers", "label": "DERIVED",
         "derived_by": "comparison of the two verbatim primaries above. THE OBJECT STATED THIS "
                       "BEFORE ANY CHECK EXISTED; this cell records that the registry confirms "
                       "it rather than that a check discovered it."},
        {"field": "arm roles", "value": "experimental on both", "label": "DERIVED",
         "derived_by": "ssot/topic_identity.locate() over raw v2 armGroups"},
        {"field": "unscreened remainder", "value": "0", "label": "DERIVED",
         "derived_by": "48 experimental-arm trials, minus the 2 included, minus the 46 "
                       "screened on 2026-08-19"},
    ],
}
