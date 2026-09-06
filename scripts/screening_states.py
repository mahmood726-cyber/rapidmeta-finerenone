# -*- coding: utf-8 -*-
"""A screening gate has THREE outcomes, and this repository's had two.

THE DEFECT. `audit_nct` records six gates as booleans and a candidate is included only when
`all(gates.values())`. A False therefore means BOTH of these, indistinguishably:

    the data was consulted and it disagrees        -- a real exclusion
    the data needed to decide was never there      -- nothing was consulted at all

Gate D is the clearest case. It reads a PMID out of AACT study_references, fetches the
abstract from PubMed, and asks whether the drug or condition appears in it. It returns False
when the abstract disagrees. It ALSO returns False when no PMID was ever linked, and again
when a PMID was linked but PubMed was unreachable and no metadata came back. All three land
in the record as the same word, and the topic is written out NOT_VIABLE.

    A CANDIDATE NOBODY COULD CHECK IS NOT A CANDIDATE THAT FAILED. Counting it as one
    turns an unreachable network into evidence about a trial, and does so silently: the
    output looks exactly like a screen that ran and rejected things.

Gates E and F have the same shape. E asks for two arms and reads AACT baseline counts; a
trial with no baseline rows posted is recorded as not having two arms. F asks for a known
primary outcome and reads design_outcomes; a trial with no rows there is recorded as having
no known primary outcome. In both, "not posted" is being read as "not so".

WHAT THIS MODULE DOES. One function, `classify`, returns for every gate one of

    PASS         the data was consulted and the gate is satisfied
    EXCLUDE      the data was consulted and the gate is not satisfied
    UNDECIDABLE  the data needed to decide is absent, and is NAMED

and a candidate-level disposition of INCLUDED, EXCLUDED or UNDECIDABLE. Exclusion requires
at least one gate that actually EXCLUDES; a candidate that merely could not be assessed is
UNDECIDABLE, which is a third answer and not a soft no.

IT IS SHARED ON PURPOSE. `audit_nct` calls it and so does the measurement instrument, so the
counts reported about screening are produced by the code that screens. A measurement that
reimplemented these rules would be measuring its own opinion of them.

WHAT THIS DOES NOT CHANGE. The `gates` booleans and the VIABLE/NOT_VIABLE verdict are left
exactly as they were, so no topic changes status because of this file. The undecidables are
COUNTED and SERVED alongside, which is the point: you cannot decide what to do about 40%
of a pool being unassessable until the number exists.
"""
from __future__ import annotations

PASS = "PASS"
EXCLUDE = "EXCLUDE"
UNDECIDABLE = "UNDECIDABLE"

INCLUDED = "INCLUDED"
EXCLUDED = "EXCLUDED"

GATE_ORDER = ("A_aact_exists", "B_drug_in_intvs", "C_condition_in_aact",
              "D_pmid_topic_match", "E_two_arms", "F_primary_outcome_known")


def _state(ok, evidence_present, absent_reason):
    """PASS / EXCLUDE / UNDECIDABLE, stated as the property the evidence has.

    `evidence_present` is the positive claim -- the rows needed to decide were found --
    rather than a check for their absence, so a reader can see what was required rather
    than inferring it from what was missing.
    """
    if evidence_present:
        return (PASS, "") if ok else (EXCLUDE, "")
    return (UNDECIDABLE, absent_reason)


def classify(nct, topic, aact_rows, intvs, conds, pmids, pubmed_meta,
             baseline_rows, design_outcome_rows, match_blob, drug_syns, cond_syns):
    """Per-gate states and one candidate-level disposition.

    Returns {"states": {gate: (state, reason)}, "disposition": ..., "reasons": [...]}.
    Every argument is the data as the pipeline holds it; nothing is fetched here, so this
    function is decidable offline and its answer depends only on what it was handed.
    """
    states = {}

    # A -- the registration itself. Its absence is not undecidable: the pipeline is asking
    # about a trial it cannot find in the snapshot it just scanned, which is a real answer.
    states["A_aact_exists"] = (PASS, "") if aact_rows else (EXCLUDE, "no AACT study row")
    if not aact_rows:
        return {"states": states, "disposition": EXCLUDED,
                "reasons": ["A_aact_exists: no AACT study row"]}

    # B and C -- intervention and condition text. Present by construction for anything the
    # matcher returned, but an empty blob is an absence and is named as one.
    intv_text = " | ".join(intvs)
    cond_text = " | ".join(conds)
    states["B_drug_in_intvs"] = _state(
        match_blob(topic["drug_patterns"], intv_text, token_subset=False, synmap=drug_syns),
        bool(intv_text.strip()), "no intervention text in AACT")
    states["C_condition_in_aact"] = _state(
        match_blob(topic["condition_patterns"], cond_text, token_subset=True,
                   synmap=cond_syns),
        bool(cond_text.strip()), "no condition text in AACT")

    # D -- THE GATE THIS MODULE EXISTS FOR. Three outcomes where there were two.
    primary_pmid = pmids[0] if pmids else None
    if not primary_pmid:
        states["D_pmid_topic_match"] = (
            UNDECIDABLE, "no PMID linked in AACT study_references -- the publication was "
                         "never identified, so its text was never read")
    elif primary_pmid not in pubmed_meta:
        states["D_pmid_topic_match"] = (
            UNDECIDABLE, "PMID %s is linked but no PubMed metadata was retrieved -- the "
                         "abstract was never fetched, so it was never checked" % primary_pmid)
    else:
        m = pubmed_meta[primary_pmid]
        blob = ((m.get("title") or "") + " " + (m.get("abstract") or "")).lower()
        if blob.strip():
            hit = (any(p in blob for p in topic["drug_patterns"])
                   or any(p in blob for p in topic["condition_patterns"]))
            states["D_pmid_topic_match"] = (PASS, "") if hit else (
                EXCLUDE, "PMID %s title/abstract mentions neither the drug nor the "
                         "condition pattern" % primary_pmid)
        else:
            states["D_pmid_topic_match"] = (
                UNDECIDABLE, "PMID %s returned an empty title and abstract" % primary_pmid)

    # E -- arm count from posted baseline rows. "Not posted" is not "not randomised".
    bg = {b["ctgov_group_code"]: int(b["count"]) for b in baseline_rows
          if (b.get("scope") or "").lower() == "overall"
          and (b.get("units") or "") == "Participants"
          and (b.get("count") or "").isdigit()}
    total_n = sum(bg.values())
    per_arm = {k: v for k, v in bg.items() if v * 2 != total_n}
    states["E_two_arms"] = _state(
        len(per_arm) >= 2, bool(bg),
        "no overall participant baseline counts posted -- the arm structure is unreported, "
        "not single-armed")

    # F -- primary outcome from design_outcomes. Same shape as E.
    primary_outs = [o for o in design_outcome_rows
                    if (o.get("outcome_type") or "").lower() == "primary"]
    states["F_primary_outcome_known"] = _state(
        bool(primary_outs), bool(design_outcome_rows),
        "no design_outcomes rows at all -- the outcome set is unreported, not absent")

    # THE DISPOSITION. An exclusion requires a gate that actually EXCLUDED. A candidate with
    # no exclusions but at least one undecidable gate is UNDECIDABLE: it has not passed
    # screening and it has not failed it, and collapsing that into either is the defect.
    excluded = [g for g in GATE_ORDER if states.get(g, (PASS, ""))[0] == EXCLUDE]
    undecided = [g for g in GATE_ORDER if states.get(g, (PASS, ""))[0] == UNDECIDABLE]
    if excluded:
        disposition = EXCLUDED
    elif undecided:
        disposition = UNDECIDABLE
    else:
        disposition = INCLUDED
    reasons = ["%s: %s" % (g, states[g][1] or "gate not satisfied")
               for g in excluded + undecided]
    return {"states": states, "disposition": disposition, "reasons": reasons}


def tally(dispositions):
    """Counts by disposition, with every state present as a key even at zero.

    A key missing from a tally reads as nothing to report. A zero that is present reads as
    looked and found none, and those are different claims.
    """
    out = {INCLUDED: 0, EXCLUDED: 0, UNDECIDABLE: 0}
    for d in dispositions:
        out[d] = out.get(d, 0) + 1
    return out
