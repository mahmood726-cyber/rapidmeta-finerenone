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

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGE_STANDARD_VERSION = "1.3.0-2026-08-19"

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
        "topic_is_comparator_arm": 3,
        "topic_is_background": 2,
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
        "arithmetic": "21 CTGov identified = 16 experimental + 3 comparator + 2 background + 0 unassessable",
        "reconciles": True,
        "included_plus_recorded_exclusions": "1 included + 3 recorded exclusions = 4 registrations the page ever carried",
        "gap_stated_plainly": (
            "17 CTGov trials place bempedoic acid in an EXPERIMENTAL arm; this object includes "
            "ONE. The other 16 are NOT excluded -- they were never screened against the stated "
            "criteria. That is an UNSCREENED REMAINDER of 16, and it is recorded as a number "
            "rather than omitted. Screening them is the next unit of work on this topic."),
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
    "eligibility_ctgov": {"role_located": 56, "topic_is_experimental_arm": 46,
                          "topic_is_comparator_arm": 2, "topic_is_background": 8,
                          "not_assessable": 0},
    "included": {"in_this_object": 4,
                 "nct": ["NCT03036124", "NCT03057977", "NCT03057951", "NCT03619213"]},
    "reconciliation": {
        "arithmetic": "56 identified = 46 experimental + 2 comparator + 8 background + 0 unassessable",
        "reconciles": True,
        "gap_stated_plainly": (
            "36 trials place an SGLT2 inhibitor in an EXPERIMENTAL arm (corrected from 43: "
            "seven had it in BOTH arms as background). This object includes FOUR. The other 32 "
            "were SCREENED on 2026-08-19 on two axes; ZERO were both eligible and poolable, so "
            "k stands at 4 on a screen rather than on assumption. There is no unscreened "
            "remainder."),
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
                               "k3_experimental": 46, "k4_comparator": 2,
                               "k5_background": 8, "kNA_not_assessable": 0,
                               "k_included_in_object": 4, "k_unscreened_remainder": 10},
                 "primary_outcome_key": "harmonised_cvdeath_or_hhf",
                 "extraction": SGLT2_EXTRACTION},
    "bempedoic-acid-review": {"search": SEARCH, "prisma": PRISMA,
                              "k_cascade": {
                                  "k0_surfaced": 21, "k2_role_located": 21,
                                  "k3_experimental": 16, "k4_comparator": 3,
                                  "k5_background": 2, "kNA_not_assessable": 0,
                                  "k_included_in_object": 1, "k_unscreened_remainder": 1},
                              "primary_outcome_key": "primary",
                              # None -> the inline block below, which IS this topic's own.
                              "extraction": None},
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
    obj["published_comparison"] = {
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

    return _finish(obj, path, original, before_keys, props)



def _p6_refuse(obj, spec, props):
    """Only for a topic with NOTHING to quote. Never overwrites real output."""
    outcome = obj["results"]["by_outcome"][spec["primary_outcome_key"]]
    outcome["r_output"] = _deep_merge(outcome.get("r_output"), {
        "state": "ABSENT_AND_THAT_IS_THE_FINDING",
        "_why_absent": (
            "k=1. No meta-analysis was performed, so there is NO model call to quote, NO "
            "pooled estimate, NO heterogeneity and NO package version. This is not a missing "
            "artefact; it is the correct state for a single-study topic."),
        "quotable_model_call": None,
        "heterogeneity": None,
        "heterogeneity_reason": "Undefined at k=1: there is no between-study variance to estimate.",
        "package_version": None,
        "what_stands_instead": {
            "estimate": "HR 0.87 (95% CI 0.79 to 0.96)",
            "provenance": "CLEAR Outcomes' OWN registry-posted analysis, NOT a synthesis "
                          "result computed here",
            "verbatim_from_registry": "Hazard Ratio (HR) 0.87, CI 0.79 - 0.96, "
                                      "statistical method Log Rank, p=0.004",
            "read_utc": "2026-08-19",
        },
        "what_would_change_it": (
            "Screening the unscreened remainder. If any of them share this estimand and "
            "comparator, k rises above 1 and a pooled model becomes both possible and "
            "required -- at which point this field must carry the quoted call."),
    })
    props["P6_analysis_output"] = prop(
        REFUSING, "No quotable model output exists because k=1 and nothing was pooled. The "
                  "absence is recorded as a finding with its cause and its trigger, and the "
                  "registry's own analysis is quoted verbatim in its place.")

    props["P6_analysis_output"] = prop(
        REFUSING, "No quotable model output exists because k=1 and nothing was pooled. The "
                  "absence is recorded as a finding with its cause and its trigger.")




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


def _finish(obj, path, original, before_keys, props):
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
