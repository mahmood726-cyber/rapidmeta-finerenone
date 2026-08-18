"""Bring ONE topic to the page standard. Additive; every property held or refusing on the page.

Standard: PAGE-STANDARD.md v1.0.0-2026-08-19. Ten properties, each of which must be HELD or
REFUSING WITH A STATED REASON. A refusal is a complete outcome; a blank is not, and nothing is
generated to fill a slot.

Run: python -W error ssot/build_to_standard.py bempedoic-acid-review
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import preconditions as P
from assessment import FAIL, HANDBOOK_AUTHORITY, NOT_ASSESSABLE, PASS

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGE_STANDARD_VERSION = "1.0.0-2026-08-19"

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
        "topic_is_experimental_arm": 17,
        "topic_is_comparator_arm": 4,
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
        "arithmetic": "21 CTGov identified = 17 experimental + 4 comparator + 0 background + 0 unassessable",
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

TOPIC_DATA = {
    "bempedoic-acid-review": {"search": SEARCH, "prisma": PRISMA,
                              "k_cascade": {
                                  "k0_surfaced": 21, "k2_role_located": 21,
                                  "k3_experimental": 17, "k4_comparator": 4,
                                  "k5_background": 0, "kNA_not_assessable": 0,
                                  "k_included_in_object": 1, "k_unscreened_remainder": 16},
                              "primary_outcome_key": "primary"},
}


def build(topic):
    spec = TOPIC_DATA.get(topic)
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
    obj["prisma_flow"] = spec["prisma"]
    props["P1_executed_search"] = prop(
        HELD, "Two databases, queries verbatim with dates and counts; PRISMA arithmetic "
              "reconciles and the 16-trial unscreened remainder is stated as a number.")

    # --- P2 k cascade -------------------------------------------------------------------
    obj["k_cascade"] = {
        "_why": "k is never one number. Each stage is what the instrument at that stage could "
                "actually decide.",
        "k0_surfaced": 21, "k2_role_located": 21, "k3_experimental": 17,
        "k4_comparator": 4, "k5_background": 0, "kNA_not_assessable": 0,
        "k_included_in_object": 1,
        "k_unscreened_remainder": 16,
        "keyed_on": "registration id",
        "source": "evidence/2026-08-19-batch1/cascade.json",
    }
    props["P2_k_cascade"] = prop(HELD, "Seven stages recorded, plus the unscreened remainder.")

    # --- P3 inclusion criteria ----------------------------------------------------------
    prov = (obj.get("screening") or {}).get("eligibility_provenance")
    if prov and prov.get("predefined") is False:
        props["P3_inclusion_criteria"] = prop(
            HELD, "Derived block present with predefined:false and post_hoc:true on its face, "
                  "each element naming its source field; authorised by MECIR R107.")
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
    props["P4_preconditions"] = prop(
        HELD, f"All {len(P.PRECONDITIONS)} recorded with verdict and cited authority "
              f"({n_fail} FAIL). criteria_predefined FAILs permanently: the criteria are post "
              f"hoc, which R107 permits and C5/C7 does not satisfy.")

    # --- P5 extraction table ------------------------------------------------------------
    obj["extraction"] = {
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
    props["P5_extraction_table"] = prop(
        HELD, "9 cells, 8 READ with source path and verbatim text, 1 DERIVED with its method "
              "named; all against a resolvable registry link.")

    # --- P6 analysis output verbatim ----------------------------------------------------
    outcome = obj["results"]["by_outcome"][spec["primary_outcome_key"]]
    outcome["r_output"] = {
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
            "Screening the 16-trial unscreened remainder. If any of them share this estimand "
            "and comparator, k rises above 1 and a pooled model becomes both possible and "
            "required -- at which point this field must carry the quoted call."),
    }
    props["P6_analysis_output"] = prop(
        REFUSING, "No quotable model output exists because k=1 and nothing was pooled. The "
                  "absence is recorded as a finding with its cause and its trigger, and the "
                  "registry's own analysis is quoted verbatim in its place.")

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
    obj["registration_identity"] = {
        "verified_utc": "2026-08-19",
        "method": "live fetch of the raw ClinicalTrials.gov v2 record and comparison of the "
                  "returned nctId against the id stored on this object",
        "trials": [{"nct": "NCT02993406", "verified": True, "status_returned": "COMPLETED",
                    "org_study_id": "1002-043",
                    "link": "https://clinicaltrials.gov/study/NCT02993406"}],
        "duplicate_seeding_check": {
            "shared_with_other_topics": False,
            "checked_against": "evidence/2026-08-19-corpus/reconcile.json (51 shared ids "
                               "corpus-wide); NCT02993406 is not among them",
        },
    }
    props["P8_registration_identity"] = prop(
        HELD, "1 of 1 trial verified live against the registry; not among the 51 "
              "corpus-wide shared registration ids.")

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

    # --- additive assertion, MOVE-AWARE AND THE MOVE IS VERIFIED --------------------------
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
    moves = {"precondition_verdict": "precondition_verdict_superseded.block"}
    after_keys = set(_walk(obj))
    lost = before_keys - after_keys
    unexplained = set()
    for k in lost:
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
