# -*- coding: utf-8 -*-
"""ClinicalTrials.gov POSTED RESULTS as risk-of-bias evidence.

⭐ THE REGISTRY POSTS COUNTS, NOT JUST IDENTIFIERS AND DATES. This project spent months
treating ClinicalTrials.gov as a metadata source -- NCT, title, phase, enrolment, dates --
and recorded NO_INFORMATION across three RoB 2 domains on the grounds that "a registration
does not report the concealment mechanism, the analysis population, or how missing outcome
data were handled". That sentence is true of the REGISTRATION and false of the RESULTS
SECTION, which is a different document at the same URL.

    participantFlowModule            -> D3. Started, completed, and every withdrawal
                                        reason, per arm.
    baselineCharacteristicsModule    -> D1 question 1.3. The arm-by-arm baseline table.
    outcomeMeasuresModule            -> D2 question 2.6. `populationDescription` states the
                                        analysis population for THAT outcome, in words.

⭐⭐ AND IT IS FREE-SOURCE BY CONSTRUCTION, WHICH IS WHY IT MATTERS MORE THAN THE FDA ROUTE.
No subscription, no publisher, no institutional login: a reader in Laos or Uganda can open
the same URL and see the same counts. The FDA Integrated Review answered these domains too,
but only for drugs approved in the United States. THIS WORKS FOR ANY REGISTERED TRIAL THAT
POSTED RESULTS, approved or not, which is a strictly larger set.

⚠️ FOUR STATES, AND THE FOURTH IS THE ONE THAT MATTERS.

    POSTED                    results exist and were read.
    NO_RESULTS_POSTED         the registration exists; no results section. A FACT ABOUT THE
                              SPONSOR'S REPORTING, and reportable as one.
    POSTED_DIFFERENT_OUTCOME  results exist but not for the outcome being synthesised. The
                              trial reported; it did not report THIS.
    NOT_ATTEMPTED             ⛔ WE DID NOT LOOK.

⛔ `NOT_ATTEMPTED` MUST NEVER RENDER AS AN ABSENCE OF EVIDENCE. It is a statement about this
review's reach, not about the trial, and the two are opposite in meaning: one says the
evidence does not exist, the other says we did not go and see. Collapsing them is the exact
failure that left the dapivirine result unrated for weeks -- a NO_INFORMATION drawn from a
document that could not answer, read as though the answer were unavailable anywhere.

⚠️ AND A CLAIM ABOUT A REGISTRY IS A CLAIM ABOUT A VERSION OF IT. Posted results are edited:
sponsors correct counts, add outcomes, and respond to QC review. Every figure taken from
here carries `retrieved_utc` and the record's own version stamps, so a later disagreement is
settled against a version rather than by re-fetching and hoping.
"""
from __future__ import annotations

POSTED = "POSTED"
NO_RESULTS_POSTED = "NO_RESULTS_POSTED"
POSTED_DIFFERENT_OUTCOME = "POSTED_DIFFERENT_OUTCOME"
NOT_ATTEMPTED = "NOT_ATTEMPTED"
STATES = (POSTED, NO_RESULTS_POSTED, POSTED_DIFFERENT_OUTCOME, NOT_ATTEMPTED)

STATE_MEANING = {
    POSTED: "Results are posted and were read at the stamped version.",
    NO_RESULTS_POSTED: ("No results section is posted. This is a fact about the sponsor's "
                        "reporting and is reportable as one; it is NOT a statement that the "
                        "trial produced no data."),
    POSTED_DIFFERENT_OUTCOME: ("Results are posted, but not for the outcome being "
                               "synthesised here. The trial reported; it did not report "
                               "this."),
    NOT_ATTEMPTED: ("⛔ WE DID NOT LOOK. A statement about this review's reach, not about "
                    "the trial. It must never be rendered, counted, or summarised as an "
                    "absence of evidence."),
}


def version_stamp(study, retrieved_utc):
    """What was read, and when it was posted. Both halves are needed.

    `retrieved_utc` alone dates OUR read; the registry's own dates say which VERSION we
    read. A figure carrying only the first cannot be checked by anyone else.
    """
    p = (study or {}).get("protocolSection") or {}
    st = p.get("statusModule") or {}
    def _d(k):
        v = st.get(k)
        return v.get("date") if isinstance(v, dict) else v
    return {"retrieved_utc": retrieved_utc,
            "results_first_posted": _d("resultsFirstPostDateStruct"),
            "last_update_posted": _d("lastUpdatePostDateStruct"),
            "source": "ClinicalTrials.gov API v2, resultsSection",
            "a_claim_about_a_registry_is_a_claim_about_a_version": (
                "Posted results are edited -- sponsors correct counts, add outcomes and "
                "answer QC review. These stamps say which version produced the figures "
                "beside them.")}


def classify(study, outcome_hint=None):
    """Which of the four states this trial is in, for this outcome."""
    if study is None:
        return NOT_ATTEMPTED, STATE_MEANING[NOT_ATTEMPTED]
    res = study.get("resultsSection")
    if not isinstance(res, dict) or not res:
        return NO_RESULTS_POSTED, STATE_MEANING[NO_RESULTS_POSTED]
    if outcome_hint:
        oms = (res.get("outcomeMeasuresModule") or {}).get("outcomeMeasures") or []
        hint = str(outcome_hint).lower()
        if oms and not any(hint in str(o.get("title") or "").lower() for o in oms):
            return POSTED_DIFFERENT_OUTCOME, STATE_MEANING[POSTED_DIFFERENT_OUTCOME]
    return POSTED, STATE_MEANING[POSTED]


def participant_flow(study):
    """Started / completed / withdrawal reasons per arm -> D3 evidence."""
    pf = ((study or {}).get("resultsSection") or {}).get("participantFlowModule") or {}
    groups = {g.get("id"): g.get("title") for g in (pf.get("groups") or [])}
    out = {"groups": groups, "milestones": {}, "withdrawals": {}}
    for per in pf.get("periods") or []:
        for m in per.get("milestones") or []:
            out["milestones"][m.get("type")] = {
                a.get("groupId"): a.get("numSubjects") for a in (m.get("achievements") or [])}
        for w in per.get("dropWithdraws") or []:
            out["withdrawals"][w.get("type")] = {
                a.get("groupId"): a.get("numSubjects") for a in (w.get("reasons") or [])}
    return out


def baseline_table(study):
    """The arm-by-arm baseline table -> D1 question 1.3.

    ⚠️ RETURNED AS DATA, NOT AS A JUDGEMENT. Whether baseline differences "suggest a problem
    with the randomisation process" is an assessor's call; this hands over the numbers that
    call is made on. Earlier this review refused 1.3 saying "the paper prints a table, and
    a table is not a sentence" -- which was honest about the instrument and wrong about the
    world: the table is machine-readable HERE, in a free source, arm by arm.
    """
    bl = ((study or {}).get("resultsSection") or {}).get("baselineCharacteristicsModule") or {}
    groups = {g.get("id"): g.get("title") for g in (bl.get("groups") or [])}
    rows = []
    for m in bl.get("measures") or []:
        for cl in m.get("classes") or []:
            for cat in cl.get("categories") or []:
                vals = {x.get("groupId"): x.get("value")
                        for x in (cat.get("measurements") or [])}
                if vals:
                    rows.append({"measure": m.get("title"),
                                 "category": cat.get("title") or cl.get("title") or "",
                                 "unit": m.get("unitOfMeasure"),
                                 "param": m.get("paramType"),
                                 "by_group": vals})
    return {"groups": groups, "population_description": bl.get("populationDescription"),
            "rows": rows}


def analysis_population(study, outcome_hint=None):
    """`populationDescription` for an outcome -> D2 question 2.6, in the sponsor's words."""
    oms = (((study or {}).get("resultsSection") or {})
           .get("outcomeMeasuresModule") or {}).get("outcomeMeasures") or []
    hint = str(outcome_hint or "").lower()
    out = []
    for o in oms:
        title = str(o.get("title") or "")
        if hint and hint not in title.lower():
            continue
        out.append({"outcome": title, "type": o.get("type"),
                    "population_description": o.get("populationDescription"),
                    "unit": o.get("unitOfMeasure")})
    return out
