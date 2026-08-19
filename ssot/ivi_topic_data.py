"""Per-topic build data for `iv-iron-hf`, KEYED TO THE TOPIC AND HELD IN ITS OWN MODULE.

WHY ITS OWN FILE. Five separate cross-topic contamination routes were found on 2026-08-19, and
the fifth was the subtlest: bempedoic's literal counts sat BELOW `**spec["k_cascade"]` inside
the same dict literal, so they overrode it and two topics rebuilt with identical numbers. A
module constant shared between topics is one edit away from being written onto the wrong page.
Data that belongs to one topic lives in one file named after that topic.

EVERY FIGURE HERE WAS EXECUTED ON 2026-08-19 AND IS RECORDED AS RETURNED, INCLUDING THE MISS.
"""

# --------------------------------------------------------------------------------------
# SEARCH -- executed, recorded verbatim, including the query that failed to find its own
# included trials. A search that missed something is evidence about the search.
# --------------------------------------------------------------------------------------
IVI_SEARCH = {
    "executed_by": "lane 1 (Claude, Anthropic family)",
    "databases": [
        {"database": "ClinicalTrials.gov API v2 -- QUERY 1, NARROWER, AND IT MISSED TWO "
                     "INCLUDED TRIALS",
         "tool": "https://clinicaltrials.gov/api/v2/studies (raw, curl)",
         "query_as_executed": (
             "query.cond=\"chronic heart failure\"; query.intr=\"ferric carboxymaltose OR iron "
             "sucrose OR ferric derisomaltose OR iron isomaltoside\"; "
             "filter.advanced=AREA[StudyType]INTERVENTIONAL; pageSize=100; countTotal=true"),
         "date_executed": "2026-08-19", "http_status": 200,
         "records_returned": 16, "total_reported": 16,
         "DEFECT_FOUND": (
             "This query surfaced only 3 of this object's 5 OWN INCLUDED TRIALS. It missed "
             "AFFIRM-AHF (NCT02937454), whose registered condition is 'Iron Deficiency; Heart "
             "Failure', and HEART-FID (NCT03037931), registered as 'Heart Failure; "
             "Iron-deficiency'. NEITHER CARRIES THE WORD 'CHRONIC'. This is the same defect "
             "shape that dropped DELIVER from the sglt2-hf query: a condition term one word "
             "narrower than the registry's own wording silently loses included trials. It is "
             "recorded rather than replaced, because a search's misses are the only available "
             "evidence about its recall."),
        },
        {"database": "ClinicalTrials.gov API v2 -- QUERY 2, BROADER, FULL RECALL ON THE "
                     "INCLUDED SET",
         "tool": "https://clinicaltrials.gov/api/v2/studies (raw, curl)",
         "query_as_executed": (
             "query.cond=\"heart failure\"; query.intr=\"ferric carboxymaltose OR iron sucrose "
             "OR ferric derisomaltose OR iron isomaltoside OR intravenous iron\"; "
             "filter.advanced=AREA[StudyType]INTERVENTIONAL; pageSize=200; countTotal=true"),
         "date_executed": "2026-08-19", "http_status": 200,
         "records_returned": 47, "total_reported": 47,
         "recall_on_included_set": "5/5",
        },
    ],
    "why_raw_and_not_the_mcp_client": (
        "Arm TYPES exist only in the raw v2 payload; the flattened MCP payload drops them, and "
        "a role reader handed a flattened payload cannot tell 'no experimental arm' from 'the "
        "field is absent'. ssot/ctgov_transport.require_raw_v2() RAISES rather than returning "
        "a verdict for exactly this reason."),
    "count_reconciliation_against_the_earlier_run": (
        "An earlier execution tonight recorded k0=40 with roles 30/4/4/2. THIS run returns "
        "k0=47 with 34/6/5/2. THE DIFFERENCE IS THE QUERY, NOT THE REGISTRY: query 2 above "
        "adds the term 'intravenous iron' to the intervention list, which surfaces seven "
        "further interventional records. Both numbers are correct for their own query. The "
        "earlier figure is superseded HERE AND NAMED rather than silently overwritten, because "
        "a count that changes without an explanation is indistinguishable from a count that "
        "was wrong."),
}

# --------------------------------------------------------------------------------------
# PRISMA -- counted from the searches above, and it must reconcile arithmetically.
# --------------------------------------------------------------------------------------
IVI_PRISMA = {
    "_scope": "PRISMA 2020 flow, counted from the executed searches above.",
    "identification": {"ctgov_query1": 16, "ctgov_query2": 47,
                       "note": "Query 2 supersedes query 1 for coverage; both are recorded, "
                               "because query 1's miss is a finding about search recall."},
    # 43, not 47: FOUR records now have no readable role (was 2), and counting them among the
    # located ones is the arithmetic defect corrected corpus-wide on 2026-08-19.
    "eligibility_ctgov": {"role_located": 43, "topic_is_experimental_arm": 34,
                          "topic_is_comparator_arm": 6, "topic_is_background": 3,
                          "not_assessable": 4},
    "included": {"in_this_object": 5,
                 "nct": ["NCT01453608", "NCT02937454", "NCT02642562",
                         "NCT03037931", "NCT03036462"]},
    "reconciliation": {
        "arithmetic": ("47 identified = 34 experimental + 6 comparator + 3 background "
                       "+ 4 not_assessable; 43 of the 47 had a role located"),
        "reconciles": True,
        "unscreened_remainder": 0,
        "remainder_means": (
            "34 trials place intravenous iron in the randomised experimental arm; 5 are in this "
            "object; the other 29 were ALL SCREENED on 2026-08-19 and the remainder is now 0. "
            "Dispositions: 13 excluded, 6 eligible but not poolable, 10 eligible with no "
            "results yet. The third state is kept because a trial nobody has looked at is not "
            "a trial that was assessed and rejected -- and neither is one that has not reported."),
    },
}

IVI_CASCADE = {
    "k0_surfaced": 47,
    "k2_role_located": 43,
    "k3_experimental": 34,
    "k4_comparator": 6,
    "k5_background": 3,
    "kNA_not_assessable": 4,
    "k_included_in_object": 5,
    "k_unscreened_remainder": 0,
    "restated_2026_08_19_trailing_placebo": {
        "k2_was": 47, "k2_now": 43,
        "k5_was": 5, "k5_now": 3,
        "kNA_was": 2, "kNA_now": 4,
        "k3_unchanged": 34,
        "why_the_remainder_does_not_move": (
            "BOTH MOVERS WENT INTO NOT_ASSESSABLE, WHICH IS NOT A SCREENING QUEUE. k3 is "
            "unchanged at 34, so the 29-trial remainder and its dispositions stand exactly as "
            "screened. A restatement that changes k5 and kNA without touching k3 changes what "
            "the page CLAIMS TO HAVE READ, not what it screened -- and those are two different "
            "corrections that would be indistinguishable if only a total were reported."),
        "the_two_records": {
            "NCT00125996": "background -> NOT_ASSESSABLE: the registration declares NO "
                           "armGroups at all, so role cannot be read from an absent field.",
            "NCT00386126": "background -> NOT_ASSESSABLE: same, no armGroups.",
        },
        "this_is_the_law_being_applied_not_bent": (
            "'background_or_coadministered' asserts the drug was given in every arm. On a "
            "record with no arms declared, that assertion has no input. ABSENT INPUT IS "
            "NOT_ASSESSABLE, NEVER A VERDICT -- the same law the preconditions run on, "
            "reaching the classifier two commits later than it reached them."),
        "measured_how": (
            "Old classifier loaded from git at 7a08bcbe1; surfaced set re-executed from this "
            "object's own query and returned 47, identical to the stored k0, so none of the "
            "delta is registry drift. scripts/regate_cascade_2026_08_19.py."),
        "no_included_trial_changed_role": "Checked against this object's own five.",
    },
    "k_unscreened_remainder_note": (
        "Was 29; all 29 screened on 2026-08-19 (scripts/screen_ivi_remainder.py, dispositions "
        "on the object at screening_of_remainder.iv_iron_2026_08_19, each keyed to the "
        "criterion it turns on and the registry field that settles it)."),
    "remainder_dispositions": {
        "EXCLUDED": 13,
        "ELIGIBLE_NOT_POOLABLE": 6,
        "ELIGIBLE_NO_RESULTS_YET": 10,
        "what_this_says": (
            "SIXTEEN OF THE TWENTY-NINE ARE ELIGIBLE. Only 13 fail a stated criterion. The "
            "evidence base is not limited by eligibility -- it is limited by ESTIMAND MATCH "
            "and by trials that have not reported. Reporting all 29 as 'excluded' would have "
            "said the opposite, and would have been the withholding class again: eligible "
            "evidence recorded as though it had failed a test."),
        "largest_pending": (
            "ICONIC-HF (NCT06929806, n=1900, RECRUITING) registers cardiovascular death and "
            "hospitalisation for worsening heart failure -- THE SAME ESTIMAND AS THIS OBJECT'S "
            "HEADLINE POOL -- and will be the single largest contributor when it reports. "
            "INFERRCT (NCT05759078, n=1000) is the second."),
        "notable_eligible_not_poolable": (
            "FAIR-HF (NCT00520780, n=456) is the trial that established ferric carboxymaltose "
            "in heart failure. It meets P/I/C and its primary -- patient global assessment "
            "plus NYHA class -- is a registered functional primary a regulator relied on, so "
            "it PASSES the outcome criterion. It is not poolable because that is an ordinal "
            "patient-reported scale matching none of this object's six estimands. ELIGIBLE AND "
            "NOT POOLED is the correct reading; recording a landmark trial as 'excluded' would "
            "misstate why it is absent."),
    },
    "k3_corrected_from": (
        "The placebo-discriminator (ssot/topic_identity.locate, 2026-08-19) is load-bearing "
        "here: AFFIRM-AHF and HEART-FID type their IRON arm ACTIVE_COMPARATOR against a "
        "PLACEBO_COMPARATOR saline arm and declare NO arm typed EXPERIMENTAL AT ALL. Read "
        "literally, 2 of this object's 5 included trials would be scored 'comparator' and the "
        "evidence base would shrink silently -- the WITHHOLDING direction."),
}

# --------------------------------------------------------------------------------------
# EXTRACTION -- every cell READ from the raw payload with its source path, or DERIVED with
# the derivation named. A cell with no label is not evidence.
# --------------------------------------------------------------------------------------
IVI_EXTRACTION = {
    "_why": "Every cell says whether it was READ from a named source or DERIVED, and carries "
            "the sentence it was read from. A cell with no label is not evidence.",
    "verified_utc": "2026-08-19",
    "source": {"registry": "ClinicalTrials.gov, five registrations",
               "read_via": "raw v2 API, fields=protocolSection"},
    "cells": [
        {"field": "NCT01453608 CONFIRM-HF condition", "label": "READ",
         "source_path": "protocolSection.conditionsModule.conditions",
         "verbatim": "Iron Deficiency; Chronic Heart Failure"},
        {"field": "NCT01453608 CONFIRM-HF primary", "label": "READ",
         "source_path": "protocolSection.outcomesModule.primaryOutcomes[].measure",
         "verbatim": "Change in six minute walk test from baseline to week 24",
         "note": "THE UNIT OF ANALYSIS IS METRES. It is not poolable with an event count, and "
                 "is reported as its own estimand rather than harmonised into the composite."},
        {"field": "NCT02937454 AFFIRM-AHF condition", "label": "READ",
         "source_path": "protocolSection.conditionsModule.conditions",
         "verbatim": "Iron Deficiency; Heart Failure",
         "note": "No 'chronic': this is why search query 1 missed it."},
        {"field": "NCT02937454 AFFIRM-AHF primary", "label": "READ",
         "source_path": "protocolSection.outcomesModule.primaryOutcomes[].measure",
         "verbatim": "HF Hospitalizations and CV Death"},
        {"field": "NCT02642562 IRONMAN condition", "label": "READ",
         "source_path": "protocolSection.conditionsModule.conditions",
         "verbatim": "Chronic Heart Failure; Iron Deficiency; Left Ventricular Systolic "
                     "Dysfunction"},
        {"field": "NCT02642562 IRONMAN primary", "label": "READ",
         "source_path": "protocolSection.outcomesModule.primaryOutcomes[].measure",
         "verbatim": "CV mortality or hospitalisation for worsening heart failure (analysis "
                     "will include first and recurrent events)",
         "note": "RECURRENT events -- the unit is the EVENT, not the participant."},
        {"field": "NCT03037931 HEART-FID condition", "label": "READ",
         "source_path": "protocolSection.conditionsModule.conditions",
         "verbatim": "Heart Failure; Iron-deficiency",
         "note": "No 'chronic': this is why search query 1 missed it."},
        {"field": "NCT03037931 HEART-FID primary", "label": "READ",
         "source_path": "protocolSection.outcomesModule.primaryOutcomes[].measure",
         "verbatim": "Number of Deaths; Number of Hospitalizations for Heart Failure; Change "
                     "in 6MWT (Six Minute Walk Test)",
         "note": "A HIERARCHICAL composite whose unit is a PAIR OF PARTICIPANTS (win ratio). "
                 "Not the same estimand as a time-to-first hazard ratio, and not pooled with "
                 "one."},
        {"field": "NCT03036462 FAIR-HF2 condition", "label": "READ",
         "source_path": "protocolSection.conditionsModule.conditions",
         "verbatim": "Systolic Heart Failure; Iron Deficiency"},
        {"field": "NCT03036462 FAIR-HF2 primary", "label": "READ",
         "source_path": "protocolSection.outcomesModule.primaryOutcomes[].measure",
         "verbatim": "Time-to-first event of CV death or HF hospitalisation; Rate of total "
                     "(first and recurrent) events",
         "note": "Registers BOTH units. That is why this object pools first-event and "
                 "recurrent-event estimands separately rather than choosing one."},
        {"field": "arm roles", "value": "experimental on all five", "label": "DERIVED",
         "derived_by": "ssot/topic_identity.locate() over raw v2 armGroups, with the "
                       "placebo-discriminator; 2 of the 5 declare no EXPERIMENTAL-typed arm"},
        {"field": "unscreened remainder", "value": "29", "label": "DERIVED",
         "derived_by": "34 experimental-arm trials from query 2, minus the 5 in this object"},
    ],
}
