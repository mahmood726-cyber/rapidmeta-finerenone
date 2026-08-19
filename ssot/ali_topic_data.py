"""Per-topic build data for `alirocumab-lipid`, KEYED TO THE TOPIC AND HELD IN ITS OWN MODULE.

Own file for the reason `ivi_topic_data.py` has one: five cross-topic contamination routes were
found on 2026-08-19, the subtlest being a shared literal overriding a spread inside one dict.
Data belonging to one topic lives in one file named after that topic.

EVERY FIGURE HERE WAS EXECUTED ON 2026-08-19 AND IS RECORDED AS RETURNED.
"""

ALI_SEARCH = {
    "executed_by": "lane 1 (Claude, Anthropic family)",
    "databases": [
        {"database": "ClinicalTrials.gov API v2 -- QUERY 1, NARROW (condition + drug)",
         "tool": "https://clinicaltrials.gov/api/v2/studies (raw, curl)",
         "query_as_executed": (
             "query.cond=\"hypercholesterolemia\"; query.intr=\"alirocumab\"; "
             "filter.advanced=AREA[StudyType]INTERVENTIONAL; pageSize=200; countTotal=true"),
         "date_executed": "2026-08-19", "http_status": 200,
         "records_returned": 54, "total_reported": 54,
         "recall_on_included_set": "6/6",
         "note": (
             "THE NARROW QUERY ACHIEVED FULL RECALL HERE, which is worth recording because on "
             "the two preceding topics it did not: sglt2-hf's narrow query dropped DELIVER and "
             "iv-iron-hf's dropped AFFIRM-AHF and HEART-FID, both because the registered "
             "condition lacked the word the query required. A narrow query is not reliably "
             "wrong -- it is reliably UNTESTED until its recall is measured against the "
             "object's own included set."),
        },
        {"database": "ClinicalTrials.gov API v2 -- QUERY 2, BROAD (intervention only)",
         "tool": "https://clinicaltrials.gov/api/v2/studies (raw, curl)",
         "query_as_executed": (
             "query.intr=\"alirocumab OR praluent OR SAR236553 OR REGN727\"; "
             "filter.advanced=AREA[StudyType]INTERVENTIONAL; pageSize=400; countTotal=true"),
         "date_executed": "2026-08-19", "http_status": 200,
         "records_returned": 99, "total_reported": 99,
         "recall_on_included_set": "6/6",
        },
    ],
    "pagination_verified": (
        "records_returned == total_reported on BOTH queries (54/54 and 99/99), so neither "
        "stopped at a page boundary. Checked explicitly rather than assumed: an outside critic "
        "named PAGINATION CURSOR ABANDONMENT -- a fetcher taking page 1 and stopping without "
        "raising -- as a class this project could neither rule out nor detect, and it sits at "
        "the surfacing stage where withholding leaves no trace in the object."),
    "why_raw_and_not_the_mcp_client": (
        "Arm TYPES and per-arm intervention lists exist only in the raw v2 payload. This topic "
        "is the reason that matters: its comparator can only be read from armGroups, because "
        "four of its candidate trials are DOUBLE-DUMMY designs where a placebo is present in "
        "both arms as the blinding device while the comparator is ezetimibe."),
}

ALI_PRISMA = {
    "_scope": "PRISMA 2020 flow, counted from the executed searches above.",
    "identification": {"ctgov_query1": 54, "ctgov_query2": 99,
                       "note": "Query 2 supersedes query 1 for coverage; both recorded."},
    "eligibility_ctgov": {"role_located": 99, "topic_is_experimental_arm": 87,
                          "topic_is_comparator_arm": 5, "topic_is_background": 6,
                          "not_assessable": 1},
    "included": {"in_this_object": 6,
                 "nct": ["NCT01507831", "NCT01617655", "NCT01623115",
                         "NCT01644175", "NCT01709500", "NCT02107898"]},
    "reconciliation": {
        "arithmetic": ("99 identified = 87 experimental + 5 comparator + 6 background "
                       "+ 1 not_assessable"),
        "reconciles": True,
        "unscreened_remainder": 0,
        "remainder_means": (
            "87 trials place alirocumab in the randomised experimental arm; 6 are in this "
            "object; the other 81 were ALL SCREENED on 2026-08-19 and the remainder is now 0. "
            "Dispositions: 33 excluded, 20 eligible but not poolable, 26 eligible with no "
            "results yet, and 2 ELIGIBLE AND POOLABLE AND NOT IN THIS OBJECT."),
    },
}

ALI_CASCADE = {
    "k0_surfaced": 99,
    "k2_role_located": 99,
    "k3_experimental": 87,
    "k4_comparator": 5,
    "k5_background": 6,
    "kNA_not_assessable": 1,
    "k_included_in_object": 6,
    "k_unscreened_remainder": 0,
    "k3_corrected_from": (
        "k3 was 74 and background 18 before the placebo-name fix of 2026-08-19. The ODYSSEY "
        "registrations name the placebo arm's intervention 'Placebo (for alirocumab)', so a "
        "substring match reported the drug in BOTH arms and locate() returned "
        "background_or_coadministered on FIVE OF THIS OBJECT'S SIX INCLUDED TRIALS. A PLACEBO "
        "FOR X IS NOT X. Fixed by anchoring: a placebo declares itself at the START of its own "
        "name. 8.4% of intervention records to hand name the drug their placebo substitutes "
        "for, so this was an industry-wide convention rather than one registry's data entry."),
    "remainder_dispositions": {
        "EXCLUDED": 33,
        "ELIGIBLE_NOT_POOLABLE": 20,
        "ELIGIBLE_NO_RESULTS_YET": 26,
        "ELIGIBLE_POOLABLE_NOT_INCLUDED": 2,
        "what_this_says": (
            "READ BY THE REMAINDER-DIAGNOSIS RULE (PAGE-STANDARD, 'Reading the remainder'): 33 "
            "of 81 fail a criterion, 20 are eligible with a different estimand, and 26 have not "
            "reported. This is the FRAGMENTED-EVIDENCE shape rather than the too-broad-query "
            "shape -- most exclusions are comparator failures (active-comparator and "
            "double-dummy designs), not population failures, so the query is well aimed at a "
            "drug programme that simply ran many non-placebo contrasts."),
        "the_two_that_matter": (
            "NCT02585778 (n=517) and NCT02289963 (n=199) both register 'Percent Change From "
            "Baseline in Calculated LDL-C at Week 24 - Intent-to-treat' -- WORD FOR WORD THIS "
            "OBJECT'S ESTIMAND -- and both randomise alirocumab against placebo on background "
            "lipid-modifying therapy. NEITHER IS IN THIS OBJECT'S SIX. That is not a screening "
            "outcome; it is a gap in this review's own evidence base, and it is recorded as a "
            "named verdict rather than folded into a tally."),
    },
}

ALI_EXTRACTION = {
    "_why": "Every cell says whether it was READ from a named source or DERIVED, and carries "
            "the sentence it was read from. A cell with no label is not evidence.",
    "verified_utc": "2026-08-19",
    "source": {"registry": "ClinicalTrials.gov, six registrations",
               "read_via": "raw v2 API, fields=protocolSection"},
    "cells": [
        {"field": "estimand", "value": "ldlc_pct_change_wk24", "label": "READ",
         "source_path": "outcomes[0].id",
         "verbatim": "percent change from baseline in calculated LDL-C at week 24"},
        {"field": "population", "label": "READ",
         "source_path": "question",
         "verbatim": "In adults treated for hypercholesterolaemia, how much does alirocumab "
                     "change calculated LDL cholesterol from baseline to week 24 compared "
                     "with placebo?",
         "note": "This topic's question is a REAL question -- P, I, C and O are all present "
                 "and it names a timepoint. Recorded because the topic screened immediately "
                 "before it, ablation-af-review, carried one trial's registry outcome measure "
                 "truncated at 120 characters in this same field."},
        {"field": "comparator", "value": "placebo", "label": "DERIVED",
         "derived_by": "armsInterventionsModule.armGroups, per trial -- a control-arm drug "
                       "that is neither a placebo nor present in every arm. Read from the ARM "
                       "and never from the flat intervention list, because four candidate "
                       "trials are DOUBLE-DUMMY designs carrying a placebo in both arms while "
                       "the comparator is ezetimibe."},
        {"field": "arm roles", "value": "experimental on all six", "label": "DERIVED",
         "derived_by": "ssot/topic_identity.locate() over raw v2 armGroups, with the "
                       "anchored placebo-name rule; five of the six resolved as BACKGROUND "
                       "before that fix"},
        {"field": "unscreened remainder", "value": "0", "label": "DERIVED",
         "derived_by": "87 experimental-arm trials, minus the 6 in this object, minus the 81 "
                       "screened on 2026-08-19"},
    ],
}
