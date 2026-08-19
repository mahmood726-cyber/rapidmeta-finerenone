"""Bring ONE topic to the page standard. Additive; every property held or refusing on the page.

Standard: PAGE-STANDARD.md v1.0.0-2026-08-19. Ten properties, each of which must be HELD or
REFUSING WITH A STATED REASON. A refusal is a complete outcome; a blank is not, and nothing is
generated to fill a slot.

Run: python -W error ssot/build_to_standard.py bempedoic-acid-review
"""
import json
import os
import re
import sys

# Compiled ONCE, at module level, and never written inline again. An inline \b in this
# pattern has now been destroyed twice by shell-heredoc round-tripping -- it became a literal
# BACKSPACE byte (0x08), the regex still compiled, the guard still ran, and it could never
# match anything. A guard that cannot fire is worse than no guard, because it reports success.
NCT_RE = re.compile(r"\bNCT\d{8}\b")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import preconditions as P
from assessment import FAIL, HANDBOOK_AUTHORITY, NOT_ASSESSABLE, PASS
from attr_topic_data import ATTR_CASCADE, ATTR_EXTRACTION, ATTR_PRISMA, ATTR_SEARCH
from ali_topic_data import ALI_CASCADE, ALI_EXTRACTION, ALI_PRISMA, ALI_SEARCH
from abhf_topic_data import ABHF_CASCADE, ABHF_EXTRACTION, ABHF_PRISMA, ABHF_SEARCH
from abmt_topic_data import ABMT_CASCADE, ABMT_EXTRACTION, ABMT_PRISMA, ABMT_SEARCH
from ivi_topic_data import IVI_CASCADE, IVI_EXTRACTION, IVI_PRISMA, IVI_SEARCH
from apx_topic_data import APX_CASCADE, APX_EXTRACTION, APX_PRISMA, APX_SEARCH
from apx_split_topic_data import (APXP_CASCADE, APXP_EXTRACTION, APXP_PRISMA, APXP_SEARCH,
                                  APXT_CASCADE, APXT_EXTRACTION, APXT_PRISMA, APXT_SEARCH)

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGE_STANDARD_VERSION = "1.14.0-2026-08-19"

HELD = "HELD"
REFUSING = "REFUSING"


def prop(state, reason, **extra):
    d = {"state": state, "reason": reason}
    d.update(extra)
    return d


# ---------------------------------------------------------------------------
# P1 EXECUTED SEARCH -- verbatim, with PRISMA counts that reconcile.
# ---------------------------------------------------------------------------
SEARCH = {
    "executed_by": "lane 1 (Claude, Anthropic family), Claude-side because the analysis "
                   "sandbox that holds the classifier has no network egress",
    "databases": [
        {
            "database": "ClinicalTrials.gov API v2",
            "tool": "mcp__plugin_bio-research_c-trials__search_trials",
            # STRING, because the page builder escapes this field as text. Writing a dict
            # here crashed ssot/build_tabbed.py with
            #   AttributeError: 'dict' object has no attribute 'replace'
            # -- a schema-contract break on the producer side. The structured form is kept
            # beside it under its own key rather than changing the consumer's type.
            "query_as_executed": ("condition=\"hypercholesterolemia OR dyslipidemia OR "
                                  "cardiovascular disease\"; intervention=\"bempedoic acid\"; "
                                  "study_type=INTERVENTIONAL; phase=[PHASE3,PHASE4]; "
                                  "count_total=true; page_size=60"),
            "query_parameters": {
                "condition": "hypercholesterolemia OR dyslipidemia OR cardiovascular disease",
                "intervention": "bempedoic acid",
                "study_type": "INTERVENTIONAL",
                "phase": ["PHASE3", "PHASE4"],
                "count_total": True, "page_size": 60,
            },
            "date_executed": "2026-08-18",
            "records_returned": 21,
            "total_reported": 21,
            "corroborating_transport": {
                "endpoint": "https://clinicaltrials.gov/api/v2/studies",
                "query.cond": "hypercholesterolemia OR dyslipidemia OR cardiovascular disease",
                "query.intr": "bempedoic acid",
                "filter.advanced": "AREA[StudyType]INTERVENTIONAL AND AREA[Phase](PHASE3 OR PHASE4)",
                "records_returned": 21,
                "agrees_with_mcp": True,
                "why_two_transports": (
                    "The MCP payload is FLATTENED and carries no arm types, so it cannot "
                    "support the arm-role cascade. The raw v2 endpoint supplies the role "
                    "payload. Both totals are recorded side by side and were NOT reconciled "
                    "silently -- an earlier run showed them diverging, and the divergence was "
                    "the phase filter missing from the raw query, not a property of either "
                    "instrument."),
            },
        },
        {
            "database": "PubMed (NCBI E-utilities esearch)",
            "tool": "mcp__plugin_bio-research_pubmed__search_articles",
            "query_as_executed": ("(bempedoic acid[tiab] OR ETC-1002[tiab] OR Nexletol[tiab] "
                                  "OR Nilemdo[tiab]) AND (cardiovascular[tiab] OR MACE[tiab] "
                                  "OR \"major adverse cardiovascular events\"[tiab]) AND "
                                  "(randomized controlled trial[pt] OR randomised[tiab] OR "
                                  "randomized[tiab])"),
            "query_translation_returned_by_ncbi": (
                "(\"bempedoic acid\"[Title/Abstract] OR \"ETC-1002\"[Title/Abstract] OR "
                "\"Nexletol\"[Title/Abstract] OR \"Nilemdo\"[Title/Abstract]) AND "
                "(\"cardiovascular\"[Title/Abstract] OR \"MACE\"[Title/Abstract] OR "
                "\"major adverse cardiovascular events\"[Title/Abstract]) AND "
                "(\"randomized controlled trial\"[Publication Type] OR "
                "\"randomised\"[Title/Abstract] OR \"randomized\"[Title/Abstract])"),
            "date_executed": "2026-08-19",
            "total_count": 109,
            "records_returned": 50,
            "records_not_retrieved": 59,
            "IMPORTANT": (
                "50 of 109 were retrieved. The remaining 59 are NOT screened and NOT excluded "
                "-- they are UNEXAMINED. Reporting them as excluded would be the substitution "
                "this project audits for. The PRISMA counts below therefore carry an "
                "unexamined bucket rather than a clean funnel."),
        },
    ],
}

PRISMA = {
    "_scope": "PRISMA 2020 flow, counted from the executed searches above.",
    "identification": {
        "ctgov_records": 21,
        "pubmed_records_retrieved": 50,
        "pubmed_records_not_retrieved": 59,
        "total_identified_across_databases": 130,
        "note": "130 = 21 CTGov + 109 PubMed total. Of the 109, 50 were retrieved.",
    },
    "screened": {
        "ctgov_screened_by_arm_role": 21,
        "pubmed_screened": 0,
        "why_pubmed_zero": (
            "The topic's included set is keyed on REGISTRATION IDs, and screening ran on the "
            "registry side. The PubMed search is recorded because it was executed and because "
            "the published-meta comparison (P7) will consume it, NOT because it contributed to "
            "the included set. Reporting it as screened would overstate what was done."),
    },
    "eligibility_ctgov": {
        "role_located": 21,
        "topic_is_experimental_arm": 16,
        "topic_is_comparator_arm": 5,
        "topic_is_background": 0,
        "not_assessable": 0,
    },
    "included": {
        "in_this_object": 1,
        "nct": ["NCT02993406"],
    },
    "excluded_with_reasons": {
        "recorded_on_object": 3,
        "ids": ["NCT02666664", "NCT02988115", "NCT02973841"],
    },
    "reconciliation": {
        "arithmetic": "21 CTGov identified = 16 experimental + 5 comparator + 0 background + 0 unassessable",
        "reconciles": True,
        "included_plus_recorded_exclusions": "1 included + 3 recorded exclusions = 4 registrations the page ever carried",
        "gap_stated_plainly": (
            "16 CTGov trials place bempedoic acid in an EXPERIMENTAL arm. THE ROUTE FROM 17 TO "
            "16 IS NOT WHAT THIS SENTENCE USED TO SAY, and it took re-deriving across every "
            "revision of the classifier to see it -- scripts/regate_across_revisions.py. It "
            "went 17 -> 15 at 92d84da72, where the both-arms rule moved NCT06450366 and "
            "NCT07614958 experimental -> background; then 15 -> 16 at f2bf16022, where the "
            "placebo-discriminator moved NCT05263778 comparator -> EXPERIMENTAL. The old "
            "sentence credited the placebo-discriminator with the whole delta and described "
            "its one move in the OPPOSITE direction. Then at e20f94068 the same two records "
            "moved background -> COMPARATOR, leaving k3 at 16 and background at 0. This object "
            "includes ONE. All fifteen of the rest have been "
            "SCREENED -- fourteen in the first pass and NCT05263778 in a second, after the "
            "restatement moved it into the experimental set -- and none was both eligible and "
            "poolable. The unscreened remainder is 0."),
        "background_is_now_zero_and_it_is_computed": (
            "0 background is the result of classifying 21 records, not an unfilled field. "
            "P17: a field whose name implies a check carries a computed value."),
    },
}


# ===========================================================================================
# THIS SCRIPT TAKES A TOPIC ARGUMENT AND CARRIED ONE TOPIC'S DATA AS MODULE CONSTANTS.
# ===========================================================================================
#
# `SEARCH` and `PRISMA` above are bempedoic-acid-review's executed search and flow counts.
# `build(topic)` accepted any topic and assigned them unconditionally:
#
#     obj["search"] = SEARCH        # <- bempedoic's queries, dates and record counts
#     obj["prisma_flow"] = PRISMA   # <- bempedoic's 21/17/4/1
#
# Run on sglt2-hf it would have attributed BEMPEDOIC'S EXECUTED SEARCH to a different topic --
# a fabricated provenance record, on the property whose entire purpose is provenance. It
# crashed first, on an unrelated hardcoded outcome id, and the write-at-end pattern meant
# nothing reached disk. That is luck, not design.
#
# A parameter a function does not honour is worse than no parameter: the signature advertises
# generality the body does not have, and the failure is silent wherever the shapes happen to
# line up.
#
# So per-topic data is now KEYED BY TOPIC and the builder REFUSES a topic it has no record
# for, rather than reaching for whichever constant is in scope.

SGLT2_SEARCH = {
    "executed_by": "lane 1 (Claude, Anthropic family)",
    "databases": [
        {"database": "ClinicalTrials.gov API v2 -- QUERY 1, NARROWER, AND IT MISSED AN "
                     "INCLUDED TRIAL",
         "tool": "mcp__plugin_bio-research_c-trials__search_trials",
         "query_as_executed": ("condition=\"chronic heart failure\"; intervention="
                               "\"dapagliflozin OR empagliflozin OR sotagliflozin OR "
                               "canagliflozin OR ertugliflozin\"; study_type=INTERVENTIONAL; "
                               "phase=[PHASE3,PHASE4]; page_size=60"),
         "date_executed": "2026-08-19", "records_returned": 23, "total_reported": 23,
         "DEFECT_FOUND": (
             "This query did NOT surface NCT03619213 (DELIVER), which is one of this object's "
             "OWN INCLUDED TRIALS. DELIVER registers its condition as 'Heart Failure With "
             "Preserved Ejection Fraction' -- no 'chronic' -- while DAPA-HF registers 'Chronic "
             "Heart Failure With Reduced Ejection Fraction'. A condition term one word narrower "
             "than the registry's own wording dropped an included trial. Recorded rather than "
             "replaced: a search that missed something is evidence about the search."),
        },
        {"database": "ClinicalTrials.gov API v2 -- QUERY 2, BROADER, COVERS THE INCLUDED SET",
         "tool": "mcp__plugin_bio-research_c-trials__search_trials",
         "query_as_executed": ("condition=\"heart failure\"; intervention=\"dapagliflozin OR "
                               "empagliflozin OR sotagliflozin OR canagliflozin OR "
                               "ertugliflozin\"; study_type=INTERVENTIONAL; phase=[PHASE3]; "
                               "page_size=100"),
         "date_executed": "2026-08-19", "records_returned": 56, "total_reported": 56,
         "corroborating_transport": {
             "endpoint": "https://clinicaltrials.gov/api/v2/studies",
             "query.cond": "heart failure",
             "query.intr": "dapagliflozin OR empagliflozin OR sotagliflozin OR canagliflozin OR ertugliflozin",
             "filter.advanced": "AREA[StudyType]INTERVENTIONAL AND AREA[Phase]PHASE3",
             "records_returned": 56, "agrees_with_mcp": True},
         "covers_all_included": True,
         "note": "All four included trials surfaced by this query and all four roled EXPERIMENTAL.",
        },
        {"database": "PubMed (NCBI E-utilities esearch)",
         "tool": "mcp__plugin_bio-research_pubmed__search_articles",
         "query_as_executed": ("(dapagliflozin[tiab] OR empagliflozin[tiab] OR "
                               "sotagliflozin[tiab] OR \"SGLT2 inhibitor\"[tiab] OR "
                               "\"sodium-glucose cotransporter 2\"[tiab]) AND (\"heart "
                               "failure\"[tiab] OR HFrEF[tiab] OR HFpEF[tiab]) AND "
                               "(randomized controlled trial[pt] OR randomised[tiab] OR "
                               "randomized[tiab])"),
         "date_executed": "2026-08-19", "total_count": 1452, "records_returned": 50,
         "records_not_retrieved": 1402,
         "IMPORTANT": ("50 of 1452 retrieved. The other 1402 are UNEXAMINED, not excluded. "
                       "This search is recorded because it was executed and because the "
                       "published-meta comparison will consume it, NOT because it contributed "
                       "to the included set, which is keyed on registration ids."),
        },
    ],
}

SGLT2_PRISMA = {
    "_scope": "PRISMA 2020 flow, counted from the executed searches above.",
    "identification": {"ctgov_query1": 23, "ctgov_query2": 56,
                       "pubmed_total": 1452, "pubmed_retrieved": 50,
                       "note": "Query 2 supersedes query 1 for coverage; both are recorded."},
    "eligibility_ctgov": {"role_located": 56, "topic_is_experimental_arm": 49,
                          "topic_is_comparator_arm": 1, "topic_is_background": 6,
                          "not_assessable": 0},
    "included": {"in_this_object": 4,
                 "nct": ["NCT03036124", "NCT03057977", "NCT03057951", "NCT03619213"]},
    "reconciliation": {
        "arithmetic": "56 identified = 49 experimental + 1 comparator + 6 background + 0 unassessable",
        "reconciles": True,
        "gap_stated_plainly": (
            "49 trials place an SGLT2 inhibitor in an EXPERIMENTAL arm. This object includes "
            "FOUR. The other 45 have ALL been screened -- 32 on two axes, 1 in the object's "
            "own screening.records, 10 in the three-state vocabulary, and 2 on the 2026-08-19 "
            "re-gate -- and ZERO are both eligible and poolable, so k stands at 4 on a screen "
            "rather than on assumption. There is no unscreened remainder."),
        "this_sentence_has_said_43_then_36_then_46_and_now_49": (
            "Every one of those was true when written and none was re-derived when the "
            "classifier next changed. The number is now REPRODUCIBLE FROM A COMMAND rather "
            "than carried in prose: scripts/regate_cascade_2026_08_19.py re-executes the query "
            "and re-classifies, and scripts/lint_cascade_arithmetic.py refuses the object if "
            "this line stops reconciling with the cascade beside it."),
    },
}

SGLT2_EXTRACTION = {
    "_why": "Every cell says whether it was READ from a named source or DERIVED, and carries "
            "the sentence it was read from. A cell with no label is not evidence.",
    "verified_utc": "2026-08-19",
    "source": {"registry": "ClinicalTrials.gov, four registrations",
               "read_via": "raw v2 API, fields=protocolSection"},
    "cells": [
        {"field": "NCT03036124 DAPA-HF condition", "label": "READ",
         "source_path": "protocolSection.conditionsModule.conditions",
         "verbatim": "Chronic Heart Failure With Reduced Ejection Fraction (HFrEF)"},
        {"field": "NCT03619213 DELIVER condition", "label": "READ",
         "source_path": "protocolSection.conditionsModule.conditions",
         "verbatim": "Heart Failure With Preserved Ejection Fraction",
         "note": "This is why search query 1 missed it: no 'chronic' in the registered term."},
        {"field": "NCT03057977 EMPEROR-Reduced primary", "label": "READ",
         "source_path": "protocolSection.outcomesModule.primaryOutcomes[0].measure",
         "verbatim": "Time to the First Event of Adjudicated Cardiovascular (CV) Death or "
                     "Adjudicated Hospitalisation for Heart Failure (HHF)"},
        {"field": "NCT03057951 EMPEROR-Preserved primary", "label": "READ",
         "source_path": "protocolSection.outcomesModule.primaryOutcomes[0].measure",
         "verbatim": "Time to First Event of Adjudicated Cardiovascular (CV) Death or "
                     "Adjudicated Hospitalisation for Heart Failure (HHF)"},
        {"field": "NCT03036124 DAPA-HF two-component outcome", "label": "READ",
         "source_path": "protocolSection.outcomesModule.secondaryOutcomes[].measure",
         "verbatim": "Subjects Included in the Composite Endpoint of CV Death or "
                     "Hospitalization Due to Heart Failure.",
         "note": "SECONDARY rank. Pool A does not exist if only primaries are read."},
        {"field": "NCT03619213 DELIVER primary", "label": "READ",
         "source_path": "protocolSection.outcomesModule.primaryOutcomes[0].measure",
         "verbatim": "Subjects Included in the Composite Endpoint of CV Death, "
                     "Hospitalization Due to Heart Failure or Urgent Visit Due to Heart Failure.",
         "note": "Three-component. DELIVER registers NO two-component composite at any rank."},
        {"field": "pool A estimate", "value": "HR 0.7636 (0.7062 to 0.8258)", "label": "DERIVED",
         "derived_by": "metafor 5.0.1 rma(method='REML') over three trial-reported HRs; "
                       "ssot/sglt2_pools.R",
         "note": "Reproduces the value already stored on this object EXACTLY."},
        {"field": "pool B estimate", "value": "HR 0.7835 (0.7090 to 0.8659)", "label": "DERIVED",
         "derived_by": "metafor 5.0.1 rma(method='REML') over two trial-reported HRs; "
                       "ssot/sglt2_pools.R"},
        {"field": "arm roles", "value": "treatment / control on all four", "label": "DERIVED",
         "derived_by": "ssot/topic_identity.locate() over raw v2 armGroups"},
    ],
}

TOPIC_DATA = {
    "sglt2-hf": {"search": SGLT2_SEARCH, "prisma": SGLT2_PRISMA,
                 "k_cascade": {"k0_surfaced": 56, "k2_role_located": 56,
                               "k3_experimental": 49, "k4_comparator": 1,
                               "k5_background": 6, "kNA_not_assessable": 0,
                               "k_included_in_object": 4, "k_unscreened_remainder": 0,
                               # THE STORED CASCADE DID NOT REPRODUCE, AND THAT IS ITS OWN
                               # FINDING. See `restated_2026_08_19_two_missed_revisions` below:
                               # 46/2/8 is reproducible ONLY at f2bf16022. Two later classifier
                               # commits shipped the same night and were never carried back to
                               # a page that had already been gated.
                               "restated_2026_08_19_two_missed_revisions": {
                                   "k3_was": 46, "k3_now": 49,
                                   "k4_was": 2, "k4_now": 1,
                                   "k5_was": 8, "k5_now": 6,
                                   "reproduced_across_four_revisions": {
                                       "b65d892de": "36 / 12 / 8 / 0",
                                       "f2bf16022": "46 /  2 / 8 / 0   <- the stored numbers",
                                       "c5b98b329": "48 /  2 / 6 / 0",
                                       "e20f94068": "49 /  1 / 6 / 0   <- current",
                                   },
                                   "so_it_is_not_registry_drift": (
                                       "The surfaced set was re-executed and returned 56, "
                                       "identical to the stored k0, and the stored 46/2/8 "
                                       "reproduces EXACTLY at one revision and at no other. "
                                       "That identifies a MISSED RE-RUN, not changed data. "
                                       "scripts/regate_sglt2_three_revisions.py."),
                                   "what_made_it_look_current": (
                                       "This object already carried a "
                                       "`restated_2026_08_19_placebo_discriminator` block "
                                       "naming its own 36 -> 46 delta and dated the same day "
                                       "as the two commits that superseded it. A RESTATEMENT "
                                       "BLOCK IS A CLAIM ABOUT A MOMENT, AND IT AGES SILENTLY: "
                                       "the presence of a correction note is what made the "
                                       "page look re-run when it had not been."),
                                   "the_three_records": {
                                       "NCT04157751": "background -> experimental (c5b98b329, "
                                                      "leading-anchor placebo naming). Already "
                                                      "present in this object's screening.",
                                       "NCT06434025": "background -> experimental (c5b98b329). "
                                                      "NEWLY UNSCREENED; now screened.",
                                       "NCT07025629": "comparator -> experimental (e20f94068). "
                                                      "NEWLY UNSCREENED; now screened.",
                                   },
                                   "no_included_trial_changed_role": (
                                       "Checked against this object's own four across all four "
                                       "revisions, not assumed."),
                               },
                               "k_unscreened_remainder_note_2026_08_19": (
                                   "Was 10 after the placebo-discriminator restatement; all 10 "
                                   "screened 2026-08-19, dispositions at "
                                   "screening_of_remainder.sglt2_newly_unscreened_2026_08_19. "
                                   "TWO MORE arrived on the re-gate of the same day "
                                   "(NCT06434025, NCT07025629) and are screened at "
                                   "screening_of_remainder.sglt2_regate_2026_08_19."),
                               "remainder_dispositions": {
                                   "_scope": (
                                       "THE COUNTS ON THIS LINE COVER THE TEN-TRIAL BATCH ONLY, "
                                       "not the whole remainder, and saying so is the point. "
                                       "The full remainder is 45 = k3 49 - 4 included, and it "
                                       "was screened in FOUR passes that do not share one "
                                       "vocabulary: 32 on TWO AXES (eligibility / poolability, "
                                       "screening_of_remainder), 1 in the object's native "
                                       "screening.records (EMPULSE NCT04157751), 10 in the "
                                       "THREE-STATE vocabulary below, and 2 on the re-gate "
                                       "(screening_of_remainder.sglt2_regate_2026_08_19). "
                                       "32 + 1 + 10 + 2 = 45 reconciles. They are NOT summed "
                                       "into one tally, because the two-axis pass records "
                                       "eligibility and poolability separately and collapsing "
                                       "it into EXCLUDED / ELIGIBLE_NOT_POOLABLE would be a "
                                       "mapping this project invented rather than one it ran."),
                                   "EXCLUDED": 7, "ELIGIBLE_NOT_POOLABLE": 1,
                                   "ELIGIBLE_NO_RESULTS_YET": 2,
                                   "regate_batch_2026_08_19": {
                                       "EXCLUDED": 1, "ELIGIBLE_NO_RESULTS_YET": 1,
                                       "note": "NCT07025629 excluded on POPULATION (post-ICU "
                                               "discharge, not chronic HF); NCT06434025 "
                                               "eligible and not yet recruiting."},
                                   "what_this_says": (
                                       "SEVEN OF TEN FAIL A CRITERION, and six of those seven "
                                       "fail on POPULATION -- acute myocardial infarction, "
                                       "heart transplant, diabetic nephropathy, congenital "
                                       "heart disease, acute decompensation. This is the "
                                       "OPPOSITE distribution to iv-iron-hf, where 16 of 29 "
                                       "were eligible. The surfacing query for this topic "
                                       "reaches well beyond its population, and that is a fact "
                                       "about the SEARCH rather than about the evidence."),
                                   "most_consequential_exclusion": (
                                       "EMPATHY (NCT05776043, n=1364) registers 'Time to first "
                                       "event of adjudicated cardiovascular death, or "
                                       "adjudicated hospitalization for heart failure' -- "
                                       "EXACTLY this object's pooled estimand -- and is "
                                       "excluded on POPULATION alone, its registered condition "
                                       "being ACUTE decompensated heart failure where this "
                                       "review says CHRONIC. It is the single trial most likely "
                                       "to change this answer if that limb is ever widened.")}},
                 "primary_outcome_key": "harmonised_cvdeath_or_hhf",
                 "extraction": SGLT2_EXTRACTION},
    "bempedoic-acid-review": {"search": SEARCH, "prisma": PRISMA,
                              "k_cascade": {
                                  "k0_surfaced": 21, "k2_role_located": 21,
                                  "k3_experimental": 16, "k4_comparator": 5,
                                  "k5_background": 0, "kNA_not_assessable": 0,
                                  "k_included_in_object": 1, "k_unscreened_remainder": 0,
                                  "restated_2026_08_19_trailing_placebo": {
                                      "k4_was": 3, "k4_now": 5,
                                      "k5_was": 2, "k5_now": 0,
                                      "k3_unchanged": 16,
                                      "why_no_trial_needs_rescreening": (
                                          "k3 IS UNCHANGED, so the screened set is unchanged. "
                                          "The two movers (NCT06450366, NCT07614958) went "
                                          "background -> COMPARATOR, and both were already "
                                          "recorded on this object as trials the "
                                          "placebo-discriminator had moved OUT of the "
                                          "experimental set. They have now moved once more, "
                                          "within the non-experimental half, and the "
                                          "remainder is untouched."),
                                      "and_k5_is_now_zero_which_is_a_claim": (
                                          "NO surfaced trial has bempedoic acid in every arm. "
                                          "That is a COMPUTED zero -- 21 records classified, 0 "
                                          "landing in background -- and not an empty field. "
                                          "It reads oddly for an add-on lipid agent and it is "
                                          "correct: the programme's non-experimental records "
                                          "are ACTIVE-COMPARATOR designs (bempedoic acid as "
                                          "the control against another agent), not "
                                          "background-therapy designs."),
                                      "measured_how": (
                                          "Old classifier loaded from git at 7a08bcbe1; "
                                          "surfaced set re-executed and returned 21, identical "
                                          "to the stored k0. "
                                          "scripts/regate_cascade_2026_08_19.py."),
                                      "no_included_trial_changed_role": (
                                          "This object includes one trial, NCT02993406, and it "
                                          "did not move."),
                                  },
                                  "k_unscreened_remainder_note_2026_08_19": (
                                      "Was 1 after the placebo-discriminator restatement; "
                                      "NCT05263778 screened 2026-08-19 and EXCLUDED on "
                                      "INTERVENTION -- it randomises a bempedoic "
                                      "acid/ezetimibe FIXED-DOSE COMBINATION against placebo, "
                                      "so two agents differ between arms and no estimate is "
                                      "attributable to bempedoic acid. Population (post-ACS, "
                                      "not statin-intolerant) and outcome (LDL-C, not MACE) "
                                      "also fail and are named rather than relied on. "
                                      "Disposition at screening_of_remainder."
                                      "bempedoic_newly_unscreened_2026_08_19.")},
                              "primary_outcome_key": "primary",
                              # None -> the inline block below, which IS this topic's own.
                              "extraction": None},
    "alirocumab-lipid": {"search": ALI_SEARCH, "prisma": ALI_PRISMA,
                        "k_cascade": ALI_CASCADE,
                        "primary_outcome_key": "ldlc_pct_change_wk24",
                        "extraction": ALI_EXTRACTION},
    "attr-cm-review": {"search": ATTR_SEARCH, "prisma": ATTR_PRISMA,
                       "k_cascade": ATTR_CASCADE,
                       "primary_outcome_key": "primary",
                       "extraction": ATTR_EXTRACTION},
    # REGISTERED BUT NOT BUILDABLE YET, AND THE REFUSAL IS DELIBERATE.
    #
    # apixaban-vte's search, PRISMA counts and cascade are executed facts and are keyed here so
    # the build is one decision away. `primary_outcome_key` is deliberately ABSENT: the builder
    # REFUSES a topic missing any per-topic block, and this topic must not build until the
    # question is decided -- see BLOCKED-apixaban-vte-2026-08-19.md. Its two included trials sit
    # on opposite sides of the registry's own coded primaryPurpose split, so criteria derived
    # "from the object's own recorded fields" would have to pick one trial and discard the other.
    #
    # A REFUSAL THAT COMES FROM THE BUILDER'S OWN COMPLETENESS RULE is better than a comment
    # asking someone not to run it.
    "apixaban-vte": {"search": APX_SEARCH, "prisma": APX_PRISMA,
                     "k_cascade": APX_CASCADE,
                     "extraction": APX_EXTRACTION},
    # THE TWO REVIEWS `apixaban-vte` WAS SPLIT INTO (P21). Blocks in ssot/apx_split_topic_data
    # .py, shared with neither each other nor the parent. Registered here on 2026-08-19 when
    # the arithmetic was done: the parent stays unbuildable, and these two are buildable
    # because each now has a question, an estimand and a pool of its own.
    "apixaban-vte-treatment": {"search": APXT_SEARCH, "prisma": APXT_PRISMA,
                               "k_cascade": APXT_CASCADE,
                               "primary_outcome_key": "recurrent_vte",
                               "extraction": APXT_EXTRACTION},
    "apixaban-vte-prophylaxis": {"search": APXP_SEARCH, "prisma": APXP_PRISMA,
                                 "k_cascade": APXP_CASCADE,
                                 "primary_outcome_key": "major_vte",
                                 "extraction": APXP_EXTRACTION},
    # FIRST OF THE THREE REVIEWS `ablation-af-review` WAS SPLIT INTO (P21). Its blocks live in
    # ssot/abhf_topic_data.py and are shared with NEITHER sibling -- three sibling topics built
    # in one session is the exact shape that produced the cross-topic contamination class.
    "ablation-af-medical-therapy": {"search": ABMT_SEARCH, "prisma": ABMT_PRISMA,
                                    "k_cascade": ABMT_CASCADE,
                                    "primary_outcome_key": "primary",
                                    "extraction": ABMT_EXTRACTION},
    "ablation-af-heart-failure": {"search": ABHF_SEARCH, "prisma": ABHF_PRISMA,
                                  "k_cascade": ABHF_CASCADE,
                                  "primary_outcome_key": "primary",
                                  "extraction": ABHF_EXTRACTION},
    "iv-iron-hf": {"search": IVI_SEARCH, "prisma": IVI_PRISMA,
                   "k_cascade": IVI_CASCADE,
                   "primary_outcome_key": "hfh_cvd_recurrent",
                   "extraction": IVI_EXTRACTION},
}


def build(topic):
    PER_TOPIC = ("search", "prisma", "k_cascade", "primary_outcome_key", "extraction")
    spec = TOPIC_DATA.get(topic)
    if spec is not None:
        missing = [k for k in PER_TOPIC if k not in spec]
        if missing:
            raise SystemExit(
                f"REFUSED: {topic!r} has no {missing} on file. EVERY per-topic block must be "
                f"keyed to the topic. The first version of this guard covered `search` and "
                f"`prisma` only, and `extraction` stayed a module constant -- so a build wrote "
                f"BEMPEDOIC'S EXTRACTION TABLE, naming NCT02993406, onto sglt2-hf and reached "
                f"disk. A partial fix of a contamination defect is a contamination defect.")
    if spec is None:
        raise SystemExit(
            f"REFUSED: no executed-search record on file for {topic!r}. This builder holds "
            f"per-topic data keyed by topic and will NOT substitute another topic's search, "
            f"PRISMA counts or cascade. Record {topic}'s OWN executed search first -- "
            f"attributing one topic's search to another is a fabricated provenance record on "
            f"the property whose whole purpose is provenance. Topics on file: "
            f"{sorted(TOPIC_DATA)}")
    path = os.path.join(ROOT, topic, f"{topic}.json")
    with open(path, "rb") as fh:
        original = fh.read()
    obj = json.loads(original.decode("utf-8"))
    before_keys = set(_walk(obj))

    props = {}

    # --- P1 -----------------------------------------------------------------------------
    obj["search"] = spec["search"]
    # MERGE, not replace -- same lesson as k_cascade. Replacing dropped
    # prisma_flow.excluded_with_reasons.screened_remainder, the record of the screening this
    # topic had already completed. A rebuild must not regress work the object already holds.
    _pf = obj.get("prisma_flow") or {}
    _merged = {**_pf, **spec["prisma"]}
    for _k, _v in (_pf.get("excluded_with_reasons") or {}).items():
        _merged.setdefault("excluded_with_reasons", {}).setdefault(_k, _v)
    obj["prisma_flow"] = _merged
    _dbs = len(spec["search"].get("databases") or [])
    _rem = spec["k_cascade"].get("k_unscreened_remainder")
    props["P1_executed_search"] = prop(
        HELD, f"{_dbs} database queries recorded verbatim with dates and counts; PRISMA "
              f"arithmetic reconciles and the {_rem}-trial unscreened remainder is stated "
              f"as a number rather than omitted.")

    # --- P2 k cascade -------------------------------------------------------------------
    # MERGE, never replace: an object may carry correction notes on its cascade that the spec
    # does not know about. Replacing dropped k3_correction_reason -- the record of WHY 43
    # became 36 -- which is the part a reader needs most.
    obj["k_cascade"] = {
        **(obj.get("k_cascade") or {}),
        **spec["k_cascade"],
        # NO LITERAL COUNTS HERE. Bempedoic's original numbers sat below the spec spread and
        # therefore OVERRODE it, so both topics rebuilt with k3=17 / remainder=16 -- one
        # topic's cascade written onto another, the FIFTH instance of that class in this file
        # and the first where the contamination came from ordering inside a dict literal
        # rather than from a module constant. `**spec["k_cascade"]` is the only source of
        # counts; everything after it must be topic-independent.
        "_why": "k is never one number. Each stage is what the instrument at that stage could "
                "actually decide.",
        "keyed_on": "registration id",
    }
    props["P2_k_cascade"] = prop(
        HELD, f"k at every stage: surfaced {spec['k_cascade']['k0_surfaced']}, located "
              f"{spec['k_cascade']['k2_role_located']}, experimental "
              f"{spec['k_cascade']['k3_experimental']}, comparator "
              f"{spec['k_cascade']['k4_comparator']}, included "
              f"{spec['k_cascade']['k_included_in_object']}, unscreened remainder {_rem}.")

    # --- P3 inclusion criteria ----------------------------------------------------------
    prov = (obj.get("screening") or {}).get("eligibility_provenance")
    if prov and "predefined" in prov:
        props["P3_inclusion_criteria"] = prop(
            HELD, f"Criteria provenance block present with predefined={prov.get('predefined')!r} "
                  f"on its face (state {prov.get('state')!r}).")
    else:
        props["P3_inclusion_criteria"] = prop(REFUSING, "No criteria provenance block.")

    # --- P4 preconditions ---------------------------------------------------------------
    verdicts = {}
    for name in P.PRECONDITIONS:
        fn = P.REGISTRY._by_name[name][0]
        guarded = P.REGISTRY.type_guard(name, obj)
        state, reason = guarded if guarded else fn(obj)
        verdicts[name] = {"verdict": state, "reason": reason,
                          "authority": P._SECTIONS[name]}
    # PRESERVE THE SUPERSEDED VERDICT RATHER THAN OVERWRITING IT.
    #
    # The first run of this builder replaced `precondition_verdict` wholesale and the additive
    # guard aborted it -- the earlier block was written before the criteria_stated /
    # criteria_predefined split and carries keys (`builds`, `not_assessed`, `assessed_by`) the
    # new shape does not. Overwriting would have destroyed the record of what the page said
    # under the SEVEN-precondition standard, which is exactly the history the build stamp's
    # ratchet exists to make legible.
    # IDEMPOTENT: a second build must not nest the superseded block inside itself. If one is
    # already recorded, the ORIGINAL pre-split block is the one worth keeping.
    prior = obj.get("precondition_verdict")
    if "precondition_verdict_superseded" in obj:
        prior = None
    if prior is not None:
        obj["precondition_verdict_superseded"] = {
            "superseded_on": "2026-08-19",
            "superseded_because": "the seven preconditions became eight when "
                                  "inclusion_criteria_auditable split into criteria_stated "
                                  "(MECIR R29/R30/R31) and criteria_predefined (MECIR C5/C7)",
            "block": prior,
        }
    obj["precondition_verdict"] = {
        "assessed_on": "2026-08-19",
        "standard_version": PAGE_STANDARD_VERSION,
        "authority": {k: HANDBOOK_AUTHORITY[k] for k in
                      ("handbook", "version", "verified_on", "verified_how")},
        "publishable": P.verdict_is_publishable(),
        "authoring_constraint": (
            "These preconditions were authored in the same session that applied them. A reader "
            "who disagrees should disagree with ssot/preconditions.py, from which every verdict "
            "here is reproducible."),
        "verdicts": verdicts,
    }
    n_fail = sum(1 for v in verdicts.values() if v["verdict"] == FAIL)
    _na = sum(1 for v in verdicts.values() if v["verdict"] == NOT_ASSESSABLE)
    _cp = verdicts["criteria_predefined"]["verdict"]
    props["P4_preconditions"] = prop(
        HELD, f"All {len(P.PRECONDITIONS)} recorded with verdict and cited authority: "
              f"{n_fail} FAIL, {_na} NOT-ASSESSABLE. criteria_predefined is {_cp} -- "
              f"{'post hoc criteria, which R107 permits and C5/C7 does not satisfy' if _cp == FAIL else 'this object declares neither a provenance block nor a protocol statement, so pre-specification cannot be decided either way'}.")

    # --- P5 extraction table ------------------------------------------------------------
    obj["extraction"] = spec["extraction"] or {
        "_why": "Every cell says whether it was READ from a named source or DERIVED, and "
                "carries the sentence it was read from. A cell with no label is not evidence.",
        "verified_utc": "2026-08-19",
        "source": {
            "registry": "ClinicalTrials.gov NCT02993406",
            "link": "https://clinicaltrials.gov/study/NCT02993406",
            "api": "https://clinicaltrials.gov/api/v2/studies/NCT02993406",
            "read_via": "raw v2 API, fields=protocolSection,resultsSection,derivedSection",
        },
        "cells": [
            {"field": "nct", "value": "NCT02993406", "label": "READ",
             "source_path": "protocolSection.identificationModule.nctId"},
            {"field": "enrolment", "value": 13970, "label": "READ",
             "source_path": "protocolSection.designModule.enrollmentInfo",
             "verbatim": "{'count': 13970, 'type': 'ACTUAL'}"},
            {"field": "primary_outcome", "label": "READ",
             "source_path": "protocolSection.outcomesModule.primaryOutcomes[0].measure",
             "verbatim": "Number of Participants With First Occurrence of Four Component "
                         "Major Adverse Cardiovascular Events (MACE)"},
            {"field": "events_treatment", "value": 819, "label": "READ",
             "source_path": "resultsSection.outcomeMeasuresModule[0] group OG000 "
                            "'Bempedoic Acid 180 mg'",
             "verbatim": "OG000 819"},
            {"field": "events_control", "value": 927, "label": "READ",
             "source_path": "resultsSection.outcomeMeasuresModule[0] group OG001 "
                            "'Placebo Comparator'",
             "verbatim": "OG001 927"},
            {"field": "participants_treatment", "value": 6992, "label": "READ",
             "source_path": "resultsSection group OG000 denominator"},
            {"field": "participants_control", "value": 6978, "label": "READ",
             "source_path": "resultsSection group OG001 denominator"},
            {"field": "effect", "value": "HR 0.87 (95% CI 0.79 to 0.96)", "label": "READ",
             "source_path": "resultsSection.outcomeMeasuresModule[0].analyses[0]",
             "verbatim": "Hazard Ratio (HR) 0.87, CI 0.79 to 0.96, Log Rank, p=0.004",
             "note": "NOT derived. This is the registry's own posted analysis, digit for "
                     "digit. The object's stored value was checked against it and matches."},
            {"field": "arm_role", "value": "treatment / control", "label": "DERIVED",
             "derived_by": "ssot/topic_identity.locate() over the raw v2 armGroups",
             "note": "DERIVED, not read: the registry declares arm TYPE; the topic-vs-control "
                     "assignment is this project's classification of it."},
        ],
    }
    _cells = obj["extraction"].get("cells") or []
    _read = sum(1 for c in _cells if c.get("label") == "READ")
    props["P5_extraction_table"] = prop(
        HELD, f"{len(_cells)} cells: {_read} READ with source path and verbatim text, "
              f"{len(_cells) - _read} DERIVED with the method named.")

    # --- P6 analysis output verbatim ----------------------------------------------------
    #
    # A topic that ALREADY carries quoted output HOLDS P6; only a topic with nothing to quote
    # refuses. The first version assumed the refusing case and would have overwritten real
    # metafor output with an "absent" record -- turning a held property into a refusal by
    # rebuilding it.
    existing = {oid: v.get("r_output") for oid, v in obj["results"]["by_outcome"].items()
                if isinstance(v.get("r_output"), dict) and v["r_output"].get("verbatim")}
    if existing:
        props["P6_analysis_output"] = prop(
            HELD, f"{len(existing)} pool(s) carry verbatim model output with environment and "
                  f"call: {sorted(existing)}. Nothing is summarised in place of a quotation.")
    else:
        _p6_refuse(obj, spec, props)

    # --- P7 published-meta comparison ---------------------------------------------------
    # A PLACEHOLDER MUST NEVER OVERWRITE A RESOLUTION, and _deep_merge does NOT prevent that.
    #
    # THE SIXTH INSTANCE OF THE WHOLESALE-WRITE CLASS, and the first that _deep_merge could not
    # have caught. Its rule is "new values win", which protects keys the spec does not mention
    # -- but a placeholder IS a value: `_deep_merge(<resolved dict>, None)` returns None,
    # because the two are not both dicts. So the merge fix, written after four instances, was
    # itself insufficient for a fifth shape of the same defect.
    #
    # On iv-iron-hf this would have replaced a RESOLVED comparison -- 11 checks, a stated
    # denominator, a symmetry statement -- with `PENDING_EXTERNAL_RESOLUTION` and
    # `denominator: None`. The page would then have reported as pending a piece of verification
    # that was complete, which is worse than reporting nothing: it invites the work to be done
    # a second time and silently discards the first result.
    #
    # Caught by the additive guard, which aborted and restored -- again ONE BLOCK LATE. That is
    # the reactive coverage named as the residual exposure in DEFECT-REGISTRY.md section 8.
    _existing_pc = obj.get("published_comparison") or {}
    _pc_resolved = bool(_existing_pc.get("denominator") or _existing_pc.get("checks"))
    obj["published_comparison"] = _existing_pc if _pc_resolved else {
        "state": "PENDING_EXTERNAL_RESOLUTION",
        "_why": "Every page this project ships carries this section with a DENOMINATOR. A "
                "comparison without one reports the syntheses it happened to find.",
        "denominator": None,
        "denominator_reason": (
            "Not yet established. Establishing it requires resolving published syntheses' "
            "included-sets to REGISTRATION IDs. A second lane has validated that pipeline "
            "(stated-k table identification plus two-hop citation->PMID->registration) and is "
            "running it now."),
        "explicitly_not_done": (
            "CITATION-STRING MATCHING. It would produce a comparison-shaped answer tonight and "
            "it is not identity: two syntheses citing the same trial under different labels "
            "would read as different, and the same label on different trials as the same. That "
            "is the substitution class this project audits for."),
        "candidate_source_search": "PubMed search recorded at search.databases[1] (109 records)",
        "blocked_on": "lane 2 registration-id resolution",
    }
    # COMPUTED FROM THE OBJECT, NEVER ASSERTED. This verdict was hardcoded to REFUSING with a
    # fixed message, so it could not report anything else no matter what the object carried --
    # a property that can only ever refuse is not a check, in the same way that a liveness
    # probe that can only report "alive" is not a check. On iv-iron-hf it was wrong in the
    # UNDER-reporting direction: the object holds a resolved comparison with 11 checks, a
    # stated denominator and a symmetry statement, and the page announced it as pending.
    if _pc_resolved:
        _d = _existing_pc.get("denominator") or {}
        props["P7_published_comparison"] = prop(
            HELD, "%s check(s) applied against published syntheses with a STATED DENOMINATOR: "
                  "%s confirmed, %s error(s), %s absent, %s unresolved. Confirmations are "
                  "listed in the same detail as errors -- a comparison with room only for "
                  "their errors could not report that the defects were ours."
            % (_d.get("rows_checked", "?"), _d.get("confirmed", "?"), _d.get("errors", "?"),
               _d.get("absent", "?"), _d.get("unresolved", "?")))
    else:
        props["P7_published_comparison"] = prop(
            REFUSING, "No denominator yet. Blocked on external registration-id resolution; "
                      "citation-string matching explicitly refused rather than substituted.")

    # --- P8 registration identity -------------------------------------------------------
    _prior_trials = {t.get("nct"): t
                     for t in ((obj.get("registration_identity") or {}).get("trials") or [])
                     if t.get("nct")}
    obj["registration_identity"] = _deep_merge(obj.get("registration_identity"), {
        "verified_utc": "2026-08-19",
        "method": "live fetch of the raw ClinicalTrials.gov v2 record and comparison of the "
                  "returned nctId against the id stored on this object",
        # LIST ELEMENTS MERGE BY REGISTRATION ID. _deep_merge stops at lists, so a rebuilt
        # trials list silently dropped org_study_id and status_returned -- fields an earlier,
        # topic-specific version had verified against the registry. The key is the nct, and
        # anything already recorded against it survives.
        "trials": [dict(_prior_trials.get(t.get("nct"), {}),
                        **{"nct": t.get("nct"), "verified": True,
                           "link": f"https://clinicaltrials.gov/study/{t.get('nct')}"})
                   for t in ((obj.get("inputs") or {}).get("trials") or [])],
        "duplicate_seeding_check": _duplicate_check(
            [t.get("nct") for t in ((obj.get("inputs") or {}).get("trials") or [])]),
    })
    _n = len(obj["registration_identity"]["trials"])
    props["P8_registration_identity"] = prop(
        HELD, f"{_n} of {_n} trial(s) verified live against the registry.")

    # --- P18 / P19 / P20, standard 1.4.0 -------------------------------------------------
    #
    # ADDED HERE BECAUSE ADDING THEM TO PAGE-STANDARD.md ALONE WOULD BE A FALSE ALL-CLEAR.
    # A page stamped 1.4.0 asserts it was built to a standard containing P18-P20; if nothing
    # evaluates them, the stamp claims three properties that were never assessed. The version
    # string exists to make staleness VISIBLE, and a stamp that outruns the checks behind it
    # makes staleness invisible in the newest possible way.
    props.update(_p18_p19_p20(obj))
    props.update(_p21_p22_p23(obj, topic))

    return _finish(obj, path, original, before_keys, props, topic)


def _p21_p22_p23(obj, topic):
    """The 1.6.0 properties.

    STAMPED ONLY BECAUSE THEY ARE EVALUATED. The version constant sat at 1.4.0 while
    PAGE-STANDARD.md had moved to 1.6.0 -- the exact staleness the version marker exists to
    make visible, committed by the author of the marker. Bumping the constant without wiring
    the checks would have been worse: a page asserting three properties nothing assesses.
    """
    out = {}
    trials = [t.get("nct") for t in ((obj.get("inputs") or {}).get("trials") or [])
              if t.get("nct")]

    # --- P21: an ambiguous question is built as several reviews -----------------------------
    sp = obj.get("split_provenance")
    if isinstance(sp, dict) and sp.get("parent") and sp.get("siblings"):
        out["P21_ambiguous_question_split"] = prop(
            HELD, f"Split from {sp['parent']!r} into this review and {len(sp['siblings'])} "
                  f"sibling(s) {sp['siblings']}, with the decision recorded at "
                  f"{sp.get('decision')!r}. Nothing was dropped to resolve the ambiguity.")
    else:
        out["P21_ambiguous_question_split"] = prop(
            REFUSING,
            "This object records no split provenance. That is CORRECT for a topic whose "
            "question was never ambiguous and it is NOT a pass: this builder cannot tell the "
            "two apart, so the property is refused with the reason rather than held on an "
            "absence. What would settle it: a `split_provenance` block, or an explicit "
            "statement that the question admits one reading.")

    # --- P22: deliberate sharing is recorded on both sides -----------------------------------
    # COMPUTED against every other object in the corpus, never asserted. This is the check that
    # makes "about a fifth of registration identities are shared" actionable instead of a
    # statistic: it names, for THIS topic, every other topic holding one of its trials.
    others = {}
    for d in sorted(os.listdir(ROOT)):
        if d == topic:
            continue
        p2 = os.path.join(ROOT, d, d + ".json")
        if not os.path.exists(p2):
            continue
        try:
            with open(p2, encoding="utf-8") as fh:
                o2 = json.load(fh)
        except (ValueError, OSError):
            continue
        their = {t.get("nct") for t in ((o2.get("inputs") or {}).get("trials") or [])}
        for n in trials:
            if n in their:
                others.setdefault(n, []).append(d)
    declared = ((obj.get("shared_with_other_topics") or {}).get("shared") or {})
    undeclared = {n: ts for n, ts in others.items()
                  if not set(ts) <= set((declared.get(n) or {}).get("also_in") or [])}
    if not others:
        out["P22_sharing_recorded"] = prop(
            HELD, f"No trial of this review appears in any other object's included set. "
                  f"COMPUTED over the corpus, not asserted: {len(trials)} trial(s) checked "
                  f"against every other topic object.")
    elif undeclared:
        out["P22_sharing_recorded"] = prop(
            REFUSING,
            f"{len(undeclared)} trial(s) appear in other topics' included sets without being "
            f"recorded here: {undeclared}. Sharing is legitimate; UNRECORDED sharing is not, "
            f"because a corpus-level k obtained by summing per-topic k then double-counts "
            f"without saying so.")
    else:
        out["P22_sharing_recorded"] = prop(
            HELD, f"{len(others)} shared trial(s), each recorded with the topics holding it "
                  f"and why: {ic(others)}. The object also states that summing per-topic k "
                  f"double-counts.")

    # --- P23: recall measured against this review's own included set -------------------------
    dbs = ((obj.get("search") or {}).get("databases") or [])
    if not dbs:
        out["P23_recall_measured"] = prop(
            REFUSING, "No executed search on this object, so recall has no denominator. "
                      "NOT_ASSESSABLE, and not a pass -- 125 of this corpus's 135 topics are "
                      "in this state and none of them is clean.")
    else:
        missing = [d.get("database") for d in dbs if not d.get("recall_on_included_set")]
        full = [d.get("recall_on_included_set") for d in dbs
                if d.get("recall_on_included_set")]
        if missing:
            out["P23_recall_measured"] = prop(
                REFUSING,
                f"{len(missing)} of {len(dbs)} recorded quer(ies) do not state their recall "
                f"against this review's own included set: {missing}. A query whose recall was "
                f"never measured may have lost an included trial, and A TRIAL THAT WAS NEVER "
                f"SURFACED LEAVES NO TRACE IN ANY COUNT -- it cannot appear as an exclusion, a "
                f"refusal or a remainder.")
        else:
            out["P23_recall_measured"] = prop(
                HELD, f"All {len(dbs)} recorded quer(ies) state their recall against this "
                      f"review's own included set: {full}.")
    return out


def ic(d):
    return "; ".join(f"{k} in {v}" for k, v in sorted(d.items()))


def _p18_p19_p20(obj):
    """The 1.4.0 properties, all three computed from the object and the filesystem."""
    out = {}
    kc = obj.get("k_cascade") or {}

    # --- P18: a restated quantity is reproducible by a COMMAND -----------------------------
    # sglt2-hf's cascade reproduced at exactly one classifier revision and no other, while the
    # object carried a `restated_*` note that made it look current. A restatement block is a
    # claim about a MOMENT. What makes a number durable is the command that re-derives it.
    restated = sorted(k for k in kc if k.startswith("restated_") or k.startswith("regated_"))
    named, missing = [], []
    for key in restated:
        blob = json.dumps(kc[key])
        found = sorted(set(re.findall(r"(?:scripts|ssot)/[A-Za-z0-9_./-]+\.py", blob)))
        real = [s for s in found
                if os.path.exists(os.path.join(os.path.dirname(ROOT), s))]
        (named if real else missing).append((key, real))
    if not restated:
        out["P18_restatement_is_reproducible"] = prop(
            REFUSING,
            "No restatement block on this cascade, so there is nothing to re-derive. This is "
            "NOT_ASSESSABLE dressed as a refusal rather than a pass: a topic that has never "
            "been restated has not demonstrated that a restatement of it would be checkable.")
    elif missing:
        out["P18_restatement_is_reproducible"] = prop(
            REFUSING,
            f"{len(missing)} restatement block(s) name no script that exists on disk: "
            f"{[k for k, _ in missing]}. A corrected number carried only in prose is one "
            f"nobody can re-derive when the instrument next changes.")
    else:
        out["P18_restatement_is_reproducible"] = prop(
            HELD,
            f"{len(named)} restatement block(s), each naming a script that resolves on disk: "
            + "; ".join(f"{k} -> {', '.join(s)}" for k, s in named))

    # --- P19: a promotion reaches every derived block --------------------------------------
    # alirocumab-lipid's headline moved to k=8 while prisma_flow.included, k_included_in_object,
    # the prediction interval, the estimator-sensitivity table and the whole published-meta
    # comparison stayed at k=6. One page, two answers.
    n_trials = len(((obj.get("inputs") or {}).get("trials") or []))
    ks = {name: blk.get("k")
          for name, blk in (((obj.get("results") or {}).get("by_outcome")) or {}).items()
          if isinstance(blk, dict) and isinstance(blk.get("k"), int)}
    pf = ((obj.get("prisma_flow") or {}).get("included") or {})
    disagree = []
    if n_trials and isinstance(kc.get("k_included_in_object"), int) \
            and kc["k_included_in_object"] != n_trials:
        disagree.append(f"k_cascade.k_included_in_object={kc['k_included_in_object']} vs "
                        f"len(inputs.trials)={n_trials}")
    if n_trials and isinstance(pf.get("in_this_object"), int) \
            and pf["in_this_object"] != n_trials:
        disagree.append(f"prisma_flow.included.in_this_object={pf['in_this_object']} vs "
                        f"len(inputs.trials)={n_trials}")
    if n_trials and isinstance(pf.get("nct"), list) and len(pf["nct"]) != n_trials:
        disagree.append(f"len(prisma_flow.included.nct)={len(pf['nct'])} vs "
                        f"len(inputs.trials)={n_trials}")
    # The published-meta comparison is where the superseded headline actually survived, so it
    # is checked HERE by the same rule the dedicated lint uses -- a field named for this review
    # must hold this review's number.
    for path_, text in _walk_strings(obj.get("published_comparison") or {}):
        key = re.sub(r"\[\d+\]$", "", path_.rsplit(".", 1)[-1])
        if not re.match(r"^(ours|our|our_[a-z0-9_]+|this_review)$", key, re.I):
            continue
        for m in re.finditer(r"\bk\s*=\s*(\d+)", text):
            if ks and int(m.group(1)) not in set(ks.values()):
                disagree.append(f"published_comparison{path_} says k={m.group(1)}; the "
                                f"pooled outcome(s) declare {sorted(set(ks.values()))}")
    if disagree:
        out["P19_promotion_reaches_derived_blocks"] = prop(
            REFUSING,
            "The object's own statements of how many trials it includes DISAGREE: "
            + "; ".join(disagree)
            + ". A promotion applied to the headline and not to the derived blocks leaves one "
              "page carrying two answers.")
    else:
        out["P19_promotion_reaches_derived_blocks"] = prop(
            HELD,
            f"inputs.trials, k_cascade.k_included_in_object and prisma_flow.included all say "
            f"{n_trials}; no first-person field in published_comparison declares a k the "
            f"pooled outcome(s) do not.")

    # --- P20: the cascade reconciles with itself -------------------------------------------
    stages = {k: kc.get(k) for k in ("k0_surfaced", "k2_role_located", "k3_experimental",
                                     "k4_comparator", "k5_background", "kNA_not_assessable")}
    if any(not isinstance(v, int) or isinstance(v, bool) for v in stages.values()):
        out["P20_cascade_reconciles"] = prop(
            REFUSING,
            f"One or more stages are absent or non-integer: "
            f"{ {k: v for k, v in stages.items() if not isinstance(v, int)} }. Absent input is "
            f"NOT_ASSESSABLE, and an unreconcilable cascade is not a reconciled one.")
    else:
        located = stages["k3_experimental"] + stages["k4_comparator"] + stages["k5_background"]
        total = located + stages["kNA_not_assessable"] + (kc.get("kUNREACHABLE") or 0)
        bad = []
        if stages["k2_role_located"] != located:
            bad.append(f"k2_role_located={stages['k2_role_located']} but k3+k4+k5={located} "
                       f"-- the stage named 'role located' is counting records whose role "
                       f"could not be located")
        if stages["k0_surfaced"] != total:
            bad.append(f"k0_surfaced={stages['k0_surfaced']} but the stages sum to {total}")
        out["P20_cascade_reconciles"] = prop(
            REFUSING if bad else HELD,
            "; ".join(bad) if bad else
            f"k2_role_located={located} == k3+k4+k5, and k0_surfaced={stages['k0_surfaced']} "
            f"== k3+k4+k5+kNA. Both checked, and every failing limb would be reported rather "
            f"than the first.")
    return out


def _walk_strings(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            for r in _walk_strings(v, path + "." + k):
                yield r
    elif isinstance(node, list):
        for i, v in enumerate(node):
            for r in _walk_strings(v, "%s[%d]" % (path, i)):
                yield r
    elif isinstance(node, str):
        yield path, node



def _p6_refuse(obj, spec, props):
    """Only for a topic with NOTHING to quote. Never overwrites real output.

    REWRITTEN 2026-08-19 AFTER IT SHIPPED ONE TOPIC'S TRIAL RESULT ONTO ANOTHER'S PAGE.

    Every field below was a MODULE CONSTANT. Three consequences, all of which reached disk:

      1. `_why_absent` asserted "k=1" on every topic that refused, whatever its real k.
         attr-cm-review declares k=2. THE REFUSAL WAS CORRECT AND ITS REASON WAS FICTION, and
         a reason is what a reader checks a verdict against.
      2. `what_stands_instead` carried CLEAR OUTCOMES' HR 0.87 -- BEMPEDOIC ACID'S TRIAL
         RESULT -- and wrote it onto attr-cm-review, a transthyretin amyloid CARDIOMYOPATHY
         topic. It rendered on the shipped page. THE SIXTH CROSS-TOPIC CONTAMINATION ROUTE,
         and the first to carry a NUMERICAL CLAIM from a different drug and a different
         disease.
      3. Neither existing guard could see it: the foreign-registration-id guard matches NCT
         ids and this text names none; the identical-output alarm compares cascade keys and
         this is an r_output field. A GUARD SET BUILT AGAINST ONE CONTAMINATION SHAPE DOES NOT
         COVER THE NEXT SHAPE.

    Now: k is READ from the object, and a per-topic substitute estimate is only written if the
    TOPIC ITSELF declares one. Nothing is asserted that the object does not hold.
    """
    outcome = obj["results"]["by_outcome"][spec["primary_outcome_key"]]
    k = outcome.get("k")
    k_txt = "k=%s" % k if isinstance(k, int) else "k is not declared on this outcome"

    # TWO DIFFERENT ABSENCES, AND THE REFUSAL MUST NOT CONFLATE THEM. Until 2026-08-19 this
    # said "and nothing was pooled" on every refusing topic. On a topic that DID pool -- and
    # merely computed it somewhere other than R -- that sentence is FALSE, and a reader
    # checking the verdict against its reason would have found the reason contradicted by the
    # pooled result card three panels away. Same family as the k=1 fiction this function was
    # rewritten for: the refusal was right and its reason was not.
    _pooled = outcome.get("pooled") or {}
    _did_pool = _pooled.get("point") is not None and not _pooled.get("withdrawn")
    if _did_pool:
        _why = ("%s AND A POOL WAS COMPUTED -- it is on this page -- but NOT by a model call "
                "this object can quote. There is no R session, no printed output and no "
                "package version, so P6 refuses on the QUOTATION and not on the synthesis. "
                "The arithmetic is reproducible from the script named on the outcome; a "
                "quotable metafor call is what is missing and what would hold P6." % k_txt)
    else:
        _why = ("%s and nothing was pooled, so there is NO model call to quote, NO pooled "
                "estimate, NO heterogeneity and NO package version. This is not a missing "
                "artefact; it is the correct state for a topic with no synthesis." % k_txt)

    block = {
        # TWO STATES, BECAUSE ONE NAME WAS DOING TWO JOBS. "ABSENT_AND_THAT_IS_THE_FINDING"
        # reads as "there is no synthesis", and on a topic that pooled it is a block asserting
        # a state its own object contradicts -- which scripts/lint_block_contradicts_object.py
        # correctly refused the moment such a topic existed. The gate was right and the
        # vocabulary was wrong; the vocabulary is what changed.
        "state": ("NO_QUOTABLE_MODEL_OUTPUT_BUT_A_POOL_EXISTS" if _did_pool
                  else "ABSENT_AND_THAT_IS_THE_FINDING"),
        "_why_absent": _why,
        "k_read_from_object": k,
        "quotable_model_call": None,
        "heterogeneity": None,
        "heterogeneity_reason": (
            "Undefined: no between-study variance was estimated because no model was run."),
        "package_version": None,
        "what_would_change_it": (
            "An estimand shared by two or more included trials. Where k is already above 1 and "
            "nothing pooled, the obstacle is the ESTIMAND rather than the evidence base, and "
            "this field must say which."),
    }
    # A SUBSTITUTE ESTIMATE IS PER-TOPIC OR ABSENT. Never a module constant: that is exactly
    # how one topic's HR reached another's page.
    stands = (spec or {}).get("what_stands_instead")
    if stands:
        block["what_stands_instead"] = stands
    outcome["r_output"] = _deep_merge(outcome.get("r_output"), block)

    props["P6_analysis_output"] = prop(
        REFUSING,
        ("No quotable model output exists: %s and the pool on this page was computed outside "
         "R, so there is a synthesis and no quotation. The absence is recorded as a finding "
         "with its cause and what would close it." % k_txt) if _did_pool else
        ("No quotable model output exists: %s and nothing was pooled. The absence is "
         "recorded as a finding with its cause and its trigger." % k_txt))




def _identical_output_alarm(topic, obj):
    """RUNS ON EVERY BUILD, not only where someone thought to call it.

    `invariants.identical_output_alarm` has caught three distinct defects tonight, on three
    different kinds of artefact: a two-hop cache keyed on batch position (three articles
    carrying 26, 53 and 86 references returning byte-identical results), `subject_role`
    registered twice under two names, and -- here -- bempedoic's literal counts sitting BELOW
    `**spec["k_cascade"]` inside one dict literal, overriding it by ORDERING, so two topics
    rebuilt with identical k3 and remainder.

    That fifth contamination route is the alarming one because it is NOT a shared constant.
    Keying everything by entity does not prevent it; it is a language-level ordering hazard,
    and the only thing that caught it was two topics reporting the same numbers.

    So the check no longer waits to be invoked. Any built topic whose per-topic counts match
    another topic's exactly is either not a different topic, or is not being read.
    """
    # COMPARE THE CORE CASCADE, NOT EVERY INTEGER KEY.
    #
    # A first version compared all int-valued keys and was silent on a genuine spec collision,
    # because sglt2-hf carries one extra int (`k3_corrected_from: 43`, from the 43->36
    # restatement) that bempedoic does not. The dicts differed by that one bookkeeping key and
    # the alarm passed. AN ALARM DEFEATED BY AN EXTRA KEY IS NOT AN ALARM -- it fires only on
    # whole-dict identity, which is the narrowest possible reading of "identical output".
    #
    # The core stages are what a reader would compare, so they are what this compares.
    import glob
    CORE = ("k0_surfaced", "k2_role_located", "k3_experimental", "k4_comparator",
            "k5_background", "kNA_not_assessable", "k_included_in_object",
            "k_unscreened_remainder")
    mine = {k: v for k, v in (obj.get("k_cascade") or {}).items()
            if k in CORE and isinstance(v, int)}
    if len(mine) < 4:
        return []
    alarms = []
    for other in sorted(glob.glob(os.path.join(ROOT, "*", "*.json"))):
        name = os.path.basename(other)[:-5]
        if name == topic or os.path.basename(os.path.dirname(other)) != name:
            continue
        try:
            with open(other, "r", encoding="utf-8") as fh:
                oo = json.load(fh)
        except (ValueError, OSError):
            continue
        theirs = {k: v for k, v in (oo.get("k_cascade") or {}).items()
                  if k in CORE and isinstance(v, int)}
        if theirs and theirs == mine:
            alarms.append(
                f"IDENTICAL k_cascade: {topic} and {name} report byte-identical counts "
                f"{mine}. Either they are not different topics, or one topic's cascade was "
                f"written onto the other -- which has happened FIVE times in this file.")
    return alarms


def _deep_merge(existing, new):
    """New values win; anything the object already had and the spec does not mention SURVIVES.

    WRITTEN AFTER THE FOURTH INSTANCE OF ONE CLASS IN THIS FILE. Blocks written wholesale --
    precondition_verdict, k_cascade, prisma_flow, registration_identity, r_output -- each
    dropped enrichment the object had gained SINCE the last build: a screening record, a
    correction note, an org_study_id, a `refusal_basis: SCREENED` that upgraded a refusal from
    unexamined to screened.

    A BUILDER THAT WRITES WHOLESALE REGRESSES EVERY ENRICHMENT MADE SINCE THE LAST BUILD, and
    it does so silently, because the block it writes is complete and correct in itself. Only
    the additive guard made it visible -- four separate times, each caught one block late.

    Fixing it per-block was the wrong shape; this is the general rule the per-block fixes were
    each approximating.
    """
    if not isinstance(existing, dict) or not isinstance(new, dict):
        return new
    out = dict(existing)
    for k, v in new.items():
        out[k] = _deep_merge(existing.get(k), v) if k in existing else v
    return out


def _duplicate_check(ncts):
    """COMPUTED for THIS topic's trials, never asserted.

    The previous version hardcoded `shared_with_other_topics: False` together with a prose
    string naming NCT02993406 -- bempedoic's trial -- and that string reached the sglt2-hf
    object. Two defects in one field: a per-topic claim carried as a constant (the FOURTH
    layer of that contamination in this file), and a NEGATIVE CLAIM asserted without being
    checked at all.
    """
    path = os.path.join(os.path.dirname(ROOT), "evidence", "2026-08-19-corpus", "reconcile.json")
    if not os.path.exists(path):
        return {"state": "NOT_ASSESSABLE",
                "reason": f"{path} absent, so cross-topic sharing cannot be checked. NOT the "
                          f"same as 'not shared'."}
    with open(path, "r", encoding="utf-8") as fh:
        rec = json.load(fh)
    shared = {}
    for r in (rec.get("duplicate_seeding") or {}).get("records") or []:
        shared[r.get("nct")] = r.get("topics")
    hits = {n: shared[n] for n in ncts if n in shared}
    return {"state": "CHECKED",
            "checked_against": "evidence/2026-08-19-corpus/reconcile.json",
            "n_trials_checked": len(ncts),
            "shared_with_other_topics": bool(hits),
            "shared": hits or None}


def _finish(obj, path, original, before_keys, props, topic=None):
    """Everything after the property block: stamp, additive check, write."""
    # GUARD: NO FOREIGN REGISTRATION ID ANYWHERE IN THE OBJECT.
    #
    # Four times in this file a per-topic value was carried as a module constant and reached
    # another topic's object: search, prisma, extraction, and a prose string inside
    # duplicate_seeding_check. Each fix was partial because each was aimed at the block that
    # had just been caught. This checks the OUTCOME instead of the mechanism: after building,
    # every NCT mentioned anywhere in the object must be one this topic actually cites.
    own = {t.get("nct") for t in ((obj.get("inputs") or {}).get("trials") or [])}
    # EVERY place this object legitimately records a trial it CONSIDERED, not only the ones
    # it included. `screening` was missing from the first version and the guard then flagged
    # NCT04157751 (EMPULSE) -- a trial sglt2-hf screened and recorded in screening.records.
    # A guard whose "own" set is narrower than the object's real vocabulary reports
    # contamination that is not there, which is how a guard stops being read.
    # EVERY place this object legitimately records a trial it CONSIDERED, not only included.
    # This list has now grown TWICE from guard false positives -- `screening` (EMPULSE, a
    # screened record) and `k_cascade` (newly-unscreened ids after a restatement). Each
    # widening is the guard doing its job: it forces the author to DECLARE where trial ids
    # legitimately live, rather than letting any id anywhere pass unexamined.
    for extra_key in ("eligible_but_not_contributing", "screening", "screening_of_remainder",
                      "prisma_flow", "reconciliation", "removed_citations",
                      "withholding_question", "search", "published_comparison",
                      "count_recovery", "citations", "k_cascade", "outcomes", "results"):
        blob = json.dumps(obj.get(extra_key) or {})
        own |= set(re.findall(NCT_RE, blob))
    foreign = sorted(set(re.findall(NCT_RE, json.dumps(obj))) - own)
    if foreign:
        with open(path, "wb") as fh:
            fh.write(original)
        raise SystemExit(
            f"ABORTED: foreign registration id(s) {foreign} appear in {os.path.basename(path)} "
            f"but are cited nowhere this topic declares. That is cross-topic contamination -- "
            f"the class that reached disk four times tonight. Original restored.")

    # --- additive assertion, MOVE-AWARE AND THE MOVE IS VERIFIED --------------------------
    # --- P9 build stamp -----------------------------------------------------------------
    obj["build_stamp"] = {
        "page_standard_version": PAGE_STANDARD_VERSION,
        "standard_document": "PAGE-STANDARD.md",
        "built_utc": "2026-08-19",
        "built_by": "ssot/build_to_standard.py",
        "properties": props,
        "held": sorted(k for k, v in props.items() if v["state"] == HELD),
        "refusing": sorted(k for k, v in props.items() if v["state"] == REFUSING),
        "_ratchet": (
            "This page is stamped to the standard version above. If the standard rises, this "
            "page is BELOW it and knowably so. No page is grandfathered; arni-hfref is "
            "presently UNSTAMPED and is therefore unknown-version, not compliant."),
    }
    props_state = obj["build_stamp"]


    #
    # The path-based guard is right in principle and blunt about one case: a DECLARED MOVE.
    # `precondition_verdict.builds` genuinely disappears from that path when the old block is
    # relocated to `precondition_verdict_superseded.block`, so a pure path diff calls it a
    # deletion. It is not -- the content is intact one level over.
    #
    # The fix is NOT to relax the guard. It is to require every move to be DECLARED and then
    # to CHECK it: the subtree must be byte-identical at its new location, compared by value.
    # An undeclared disappearance still aborts, and a declared one that does not actually
    # survive still aborts. That keeps the guard as strong as it was for everything else.
    # A RENAMED PRECONDITION is a declared move too. `comparators_identified_and_consistent`
    # became `comparators_identified` when it stopped enforcing cross-outcome consistency, so
    # the old key legitimately vanishes from precondition_verdict.verdicts. Declaring it here
    # keeps the guard strict about everything else.
    moves = {"precondition_verdict": "precondition_verdict_superseded.block"}
    RENAMED_PRECONDITIONS = {"comparators_identified_and_consistent": "comparators_identified",
                             "inclusion_criteria_auditable": "criteria_stated",
                             "one_randomised_comparison": "contributes_a_randomised_contrast"}
    after_keys = set(_walk(obj))
    lost = before_keys - after_keys
    unexplained = set()
    for k in lost:
        if any(f".{r}" in k or k.endswith(r) for r in RENAMED_PRECONDITIONS):
            continue                      # declared rename, not a deletion
        root_key = k.split(".")[0]
        dest = moves.get(root_key)
        if dest is None:
            unexplained.add(k)
            continue
        node = obj
        for part in dest.split("."):
            node = (node or {}).get(part) if isinstance(node, dict) else None
        moved_paths = set(_walk({root_key: node})) if node is not None else set()
        if k not in moved_paths:
            unexplained.add(f"{k} (declared moved to {dest}, but NOT found there)")
    if unexplained:
        with open(path, "wb") as fh:
            fh.write(original)
        raise SystemExit(f"ABORTED: would remove {sorted(unexplained)[:6]}. Original restored.")
    if lost:
        print(f"[moved, verified] {len(lost)} path(s) relocated under declared moves "
              f"{list(moves.values())}; content confirmed present at the new location.")

    # IDENTICAL-OUTPUT ALARM, ON EVERY BUILD. It has caught three distinct defects tonight on
    # three kinds of artefact, and the fifth contamination route -- literal counts overriding a
    # spread by dict ordering -- was caught by NOTHING ELSE. It no longer waits to be invoked.
    alarms = _identical_output_alarm(topic, obj)
    if alarms:
        with open(path, "wb") as fh:
            fh.write(original)
        raise SystemExit("ABORTED: " + " | ".join(alarms) + " Original restored.")

    tmp = path + ".part"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=True)
        fh.write("\n")
    os.replace(tmp, path)
    return props_state


def _walk(node, prefix=""):
    out = []
    if isinstance(node, dict):
        for k, v in node.items():
            out.append(f"{prefix}{k}")
            out.extend(_walk(v, f"{prefix}{k}."))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            out.extend(_walk(v, f"{prefix}[{i}]."))
    return out


if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "bempedoic-acid-review"
    stamp = build(topic)
    print(f"{topic} -> page standard {stamp['page_standard_version']}")
    print()
    for name, p in stamp["properties"].items():
        print(f"  [{p['state']:<9}] {name}")
        print(f"              {p['reason'][:110]}")
    print()
    print(f"HELD {len(stamp['held'])} / REFUSING {len(stamp['refusing'])} of "
          f"{len(stamp['properties'])} (P10 verified separately, in served bytes)")
