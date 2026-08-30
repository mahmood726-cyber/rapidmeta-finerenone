# -*- coding: utf-8 -*-
"""Regulatory-review answers to RoB 2 signalling questions, as a PROVENANCE TIER.

WHY THIS EXISTS. Risk of bias is the domain that blocks a GRADE rating on 49 of the 54
live pooled results in this corpus, and 19 of those refuse because an assessor recorded
NO INFORMATION. The reason is not effort: the assessments were made from
ClinicalTrials.gov registration records, and a registration does not report the allocation
concealment mechanism, the analysis population, or how missing outcome data were handled.

Measured across four document classes for the same question, one protocol each:

    registry record             D1a NO   D1b NO   D2 NO   D3 NO
    journal publication  n=2    D1a NO   D1b NO   D2 NO   D3 YES
    FDA Medical Review   n=1    D1a YES  D1b NO   --      --
    FDA Statistical Rev  n=1    --       D1b NO   D2 YES  D3 YES
    FDA INTEGRATED REVIEW n=2   D1a YES  D1b YES  D2 YES  D3 YES

⭐ THE INTEGRATED REVIEW ANSWERS EVERY BLOCKED DOMAIN, AND IT IS FREE. FDA merged the
Medical and Statistical Reviews into one Integrated Review around 2019. An earlier
conclusion here -- "allocation concealment is unanswered by every source read" -- was
drawn entirely from a 2015-era application and was a claim about THAT ERA, not about FDA
reviews. ⚠️ ANY CLAIM ABOUT A DOCUMENT CLASS IS A CLAIM ABOUT A VERSION OF IT. Name the
version, or the claim is about whatever you happened to read.

    THE TWO TIERS, AND WHY THEY ARE IN THE SCHEMA RATHER THAN THE PROSE.

    STATED    the document says the thing. finerenone: "Randomization was managed
              centrally using an interactive voice and web response system."
    INFERRED  the document evidences the MECHANISM without stating the property.
              sotagliflozin: "stratum assignment between Interactive Response Technology
              (IRT) and eCRF occurred in more than 5% of patients" -- which shows an IRT
              was in use, inside a sentence about a stratification discrepancy.

⚠️ A DISTINCTION KEPT ONLY IN PROSE SURVIVES ONE REPORT AND DIES AT THE FIRST JOIN. So the
tier is a required field, it travels with every answer, and any derived verdict that rests
on an INFERRED answer says so in its own record. `rests_on_inferred_evidence` is not a
footnote; it is a field a later query can filter on.

WHAT THIS MODULE WILL NOT DO. It does not read PDFs and it does not decide anything. It is
a typed store plus a reader. The reading is done by an assessor against a named document,
and every answer carries the document, the section, a verbatim quote and the UTC it was
retrieved -- so a disagreement is settled against the bytes rather than by re-running.

MAPPING TO THE TOOL, from `rob2_algorithm` and nothing else:
    1.1  was the allocation sequence random
    1.2  was the allocation sequence CONCEALED until enrolment and assignment
    1.3  do baseline differences suggest a problem with randomisation
    2.6  was an appropriate analysis used to estimate the effect of ASSIGNMENT
    3.1  were outcome data available for all, or nearly all, participants
"""
from __future__ import annotations

STATED = "STATED"
INFERRED = "INFERRED"
TIERS = (STATED, INFERRED)

# The store lives under risk_of_bias so it travels with the assessment it supplements,
# and is dated so a later version of the same document is a different record.
STORE_KEY = "regulatory_evidence"

# Signalling questions this source class has been MEASURED to answer. Deliberately not
# "all of them": a question no document was probed for is absent, not answerable.
SUPPORTED_QUESTIONS = ("1.1", "1.2", "1.3",
                       "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7",
                       "3.1", "3.2", "3.3", "3.4",
                       "4.1", "4.2", "4.3", "4.4", "4.5")

# ⭐ WIDENED 2026-08-30, AND ONLY AFTER PROBING. The first version carried five questions
# and said so: "a question no document was probed for is absent, not answerable." D1
# completed from those five, but D2 needs 2.1-2.7 and D3 needs 3.1-3.4, so no OVERALL
# could be computed and the lift did not fire on a single real result. The remaining
# questions were then put to the same documents and answered -- both trials are double
# blind, which routes 2.3-2.5 to NA, and 2.7/3.2-3.4 route from the earlier answers.
# ⚠️ NA IS AN ANSWER, NOT A GAP. RoB 2 routes through NOT-APPLICABLE, and recording NA as
# NO_INFORMATION would have blocked the very domains the routing resolves.

QUESTION_TEXT = {
    "2.1": "Were participants aware of their assigned intervention during the trial?",
    "2.2": ("Were carers and people delivering the interventions aware of participants' "
            "assigned intervention?"),
    "2.3": ("Were there deviations from the intended intervention that arose because of "
            "the trial context?"),
    "2.4": "Were these deviations likely to have affected the outcome?",
    "2.5": "Were these deviations from intended intervention balanced between groups?",
    "2.7": ("Was there potential for a substantial impact of the failure to analyse "
            "participants in the group to which they were randomized?"),
    "3.2": ("Is there evidence that the result was not biased by missing outcome data?"),
    "3.3": "Could missingness in the outcome depend on its true value?",
    "3.4": "Is it likely that missingness in the outcome depended on its true value?",
    "4.1": "Was the method of measuring the outcome inappropriate?",
    "4.2": ("Could measurement or ascertainment of the outcome have differed between "
            "intervention groups?"),
    "4.3": ("Were outcome assessors aware of the intervention received by study "
            "participants?"),
    "4.4": ("Could assessment of the outcome have been influenced by knowledge of the "
            "intervention received?"),
    "4.5": ("Is it likely that assessment of the outcome was influenced by knowledge of "
            "the intervention received?"),
    "1.1": "Was the allocation sequence random?",
    "1.2": ("Was the allocation sequence concealed until participants were enrolled and "
            "assigned to interventions?"),
    "1.3": ("Did baseline differences between intervention groups suggest a problem with "
            "the randomization process?"),
    "2.6": ("Was an appropriate analysis used to estimate the effect of assignment to "
            "intervention?"),
    "3.1": "Were data for this outcome available for all, or nearly all, participants?",
}

DOCUMENT_CLASSES = {
    "fda_integrated_review": ("FDA Integrated Review", 2019, "all four probed domains"),
    "fda_medical_review": ("FDA Medical Review", None, "D1a, D1c"),
    "fda_statistical_review": ("FDA Statistical Review", None, "D2, D3"),
    "ema_epar": ("EMA European Public Assessment Report", None, "not yet probed"),
}


def answer(question, response, tier, quote, document, section=None, url=None,
           retrieved_utc=None, document_class="fda_integrated_review"):
    """One typed answer. Refuses to build a malformed one rather than store it."""
    if question not in SUPPORTED_QUESTIONS:
        raise ValueError("signalling question %r is not one this source class has been "
                         "measured to answer: %s" % (question,
                                                     ", ".join(SUPPORTED_QUESTIONS)))
    if tier not in TIERS:
        raise ValueError("tier must be one of %s, not %r" % (TIERS, tier))
    # A quote is required for a SUBSTANTIVE answer and must not be for a routed one.
    # NA means the tool's own logic makes the question inapplicable given an earlier
    # answer, and NO_INFORMATION means the document is silent; neither has a sentence to
    # quote, and demanding one would push an assessor to stretch an unrelated span.
    routed = str(response).strip().upper() in ("NA", "NOT_APPLICABLE", "NO_INFORMATION")
    if not routed and (not quote or len(str(quote).split()) < 4):
        raise ValueError("an answer without a verbatim quote of at least four words is "
                         "not evidence; question %s" % question)
    if not document:
        raise ValueError("an answer must name the document it came from")
    return {"question": question,
            "question_text": QUESTION_TEXT[question],
            "response": response,
            "tier": tier,
            "quote": quote,
            "document": document,
            "document_class": document_class,
            "section": section,
            "url": url,
            "retrieved_utc": retrieved_utc}


def store(canon):
    rb = canon.get("risk_of_bias")
    rb = rb if isinstance(rb, dict) else {}
    s = rb.get(STORE_KEY)
    return s if isinstance(s, dict) else {}


def answers_for(canon, trial_id):
    """Every regulatory answer held for one trial, keyed by signalling question.

    ⚠️ TRIAL IDENTITY IS EXACT. A regulatory review covers an APPLICATION, which may
    include several trials; an answer recorded against the wrong trial would be a real
    finding attached to the wrong result. Keys are matched exactly, never by prefix.
    """
    per = store(canon).get("by_trial")
    per = per if isinstance(per, dict) else {}
    rec = per.get(str(trial_id))
    if not isinstance(rec, dict):
        return {}
    out = {}
    for q, a in rec.items():
        if isinstance(a, dict) and a.get("question") in SUPPORTED_QUESTIONS:
            out[a["question"]] = a
    return out


def responses_and_provenance(canon, trial_id):
    """({question: response}, provenance) for feeding `rob2_algorithm`.

    The provenance half is the point: it names which questions were answered from a
    regulatory document, at which tier, and whether ANY of them are INFERRED.
    """
    a = answers_for(canon, trial_id)
    responses = {q: v.get("response") for q, v in a.items()}
    inferred = sorted(q for q, v in a.items() if v.get("tier") == INFERRED)
    prov = {
        "questions_from_regulatory_review": sorted(a),
        "documents": sorted({v.get("document") for v in a.values() if v.get("document")}),
        "document_classes": sorted({v.get("document_class") for v in a.values()
                                    if v.get("document_class")}),
        "tiers": {q: v.get("tier") for q, v in a.items()},
        "inferred_questions": inferred,
        "rests_on_inferred_evidence": bool(inferred),
        "quotes": {q: v.get("quote") for q, v in a.items()},
    }
    if inferred:
        prov["inferred_means"] = (
            "At least one signalling question was answered from a document that EVIDENCES "
            "the mechanism without STATING the property -- for example a review that "
            "mentions an interactive response technology inside a sentence about a "
            "stratification discrepancy, which shows central randomisation was in use "
            "without saying allocation was concealed. It is weaker than a stated answer "
            "and is carried as a separate tier so the difference survives a join.")
    return responses, prov
