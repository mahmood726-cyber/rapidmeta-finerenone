r"""The PICO surface of a topic, and the harm terms in it -- one definition, used by both
the measurement and the gate.

WHY THIS FILE IS SEPARATE. The measurement (scripts/measure_harms_gap.py) and the gate
(gates/gate21_pico_names_harm_unsynthesised.py) must decide "does this PICO name a harm"
the SAME way, or the gate polices a population the measurement never counted and the two
numbers drift apart while both look authoritative. Two conventions for one concept is the
defect gate 3 exists for.

WHAT A "PICO SURFACE" IS HERE -- named fields, not a guess:

    question                 the review's own stated question
    outcomes[].name          the outcome the review commits to reporting
    outcomes[].definition    and how it defines it
    screening.eligibility    which carries the ESTIMAND sentence on split reviews

Those four and no others. `protocol.what_was_actually_done`, `topic_state` and the prose
blocks are EXCLUDED: they describe what was done, not what the review undertook to
measure, and including them turns every page that discusses harms into a page that
promised them.

⛔ THE DETECTOR PRODUCES CANDIDATES, NOT VERDICTS. A term in the PICO surface can be
   (a) the review's own named outcome        -> the review undertook to report it
   (b) a component of a synthesised composite -> already inside the pooled outcome
   (c) the POPULATION                         -> "adults after intracerebral haemorrhage"
   (d) prose about what a TRIAL registered    -> a fact about a source, not an undertaking
Only (a) can be a harms-omission defect, and no regex separates (a) from (c) and (d).
Every candidate is therefore adjudicated by hand in gates/HARMS_PICO_ADJUDICATION.json
and the instruments REFUSE on a candidate with no adjudication row.

MEASURED DEFECTS IN THIS FILE'S OWN DETECTOR, kept because each was real:

 1. `h[ae]morrhag` CANNOT MATCH BRITISH "haemorrhage". The class `[ae]` matches exactly
    ONE of a/e; "haemorrhage" carries BOTH. It silently missed every British spelling in
    the corpus. Found on 2026-09-03 by reading a pre-registered recall sample, not by the
    detector. Correct form is `ha?emorrhag`.
 2. `myopath\w*` matched CARDIOMYOPATHY -- "Kansas City Cardiomyopathy Questionnaire" and
    "hypertrophic cardiomyopathy" -- turning two quality-of-life outcomes into harm
    candidates. `\b` anchoring fixes it; `\bneutropeni` still matches the POPULATION
    "neutropenic patients" and is left to adjudication rather than tuned away, because
    tuning a detector against the sample that measured it destroys the measurement.
"""
from __future__ import annotations

import re

# Terms that can NAME A HARM. Deliberately wider than the ones that turned out to matter:
# a candidate costs one adjudication row, a miss costs a defect that is never counted.
HARM_TERMS = (
    r"bleed\w*|ha?emorrhag\w*|adverse event\w*|serious adverse|\bSAEs?\b|\bAEs?\b"
    r"|safety|tolerabilit\w*|toxicit\w*|\bharms?\b|side.effect\w*"
    r"|discontinuation due to|withdrawal due to|treatment.emergent"
    r"|hypoglyca?emi\w*|hyperkala?emi\w*|ketoacidosis|\bamputation\w*|rhabdomyolysis"
    r"|\bmyopath\w*|\bneutropeni\w*|hepatotox\w*|nephrotox\w*|injection.site"
    r"|infusion.related|\bgout\b|cholelithiasis|serious infection\w*"
    r"|treatment.related|drug.related"
)
HARM_RX = re.compile(HARM_TERMS, re.I)

PICO_FIELDS = ("question", "outcomes", "screening.eligibility")


def pico_surface(obj):
    """-> {field_name: text}. The four named fields, flattened to three strings."""
    sc = obj.get("screening")
    outs = obj.get("outcomes") or []
    return {
        "question": str(obj.get("question") or ""),
        "outcomes": " | ".join(
            "%s :: %s" % (o.get("name", ""), o.get("definition", ""))
            for o in outs if isinstance(o, dict)),
        "screening.eligibility": (str(sc.get("eligibility", ""))
                                  if isinstance(sc, dict) else ""),
    }


def harm_mentions(obj):
    """-> [(field, matched_term, quoted_context)] over the PICO surface. CANDIDATES."""
    out = []
    for field, text in pico_surface(obj).items():
        for m in HARM_RX.finditer(text):
            out.append((field, m.group(0),
                        text[max(0, m.start() - 70):m.end() + 70].replace("\n", " ")))
    return out


def synthesised_outcome_ids(obj):
    """The outcome ids this object actually publishes a synthesis for."""
    return list(((obj.get("results") or {}).get("by_outcome") or {}).keys())


def harms_synthesis(obj):
    """-> (present, where). What in THIS object reports a harm quantity.

    Two places count, and both are read: an outcome in `results.by_outcome` whose own
    name/definition names a harm, and a top-level `harms*` block. Nothing else -- prose
    that discusses harms is not a synthesis of them.
    """
    where = []
    outs = {o.get("id"): o for o in (obj.get("outcomes") or []) if isinstance(o, dict)}
    for oid in synthesised_outcome_ids(obj):
        o = outs.get(oid) or {}
        blob = "%s %s %s" % (oid, o.get("name", ""), o.get("definition", ""))
        if HARM_RX.search(blob):
            where.append("results.by_outcome.%s" % oid)
    for key in obj:
        if re.match(r"^harms?(_|$)", key, re.I):
            where.append(key)
    return bool(where), where


FREEZE_DECISION_LIVES_IN_ONE_PLACE = (
    "⛔ `decide()` LIVES HERE AND NOT IN THE GATE. It was written inside gate 21 and the "
    "MEASUREMENT alongside it read the stored disposition instead -- so on 2026-09-03, "
    "minutes after both apixaban pages published their bleeding outcome, the gate "
    "correctly said 0 findings and the measurement still said 2. A file still said they "
    "were broken. THAT IS THE MIRROR OF THE DEFECT THE GATE'S OWN DOCSTRING WARNS "
    "AGAINST -- trusting a stored verdict over the object -- committed one module away "
    "by the person who wrote the warning. Two implementations of one decision is the "
    "defect gate 3 exists for, one layer up.")

# The dispositions under which the PICO actually UNDERTOOK to report a harm. The other
# three -- MENTION_IS_NOT_AN_OUTCOME, COMPONENT_OF_SYNTHESISED_COMPOSITE, and any future
# addition -- are not promises and are not policed here.
PROMISING = ("NAMED_AND_ABSENT", "NAMED_AND_SYNTHESISED", "NAMED_AND_REFUSED_WITH_REASON")

# Field names that carry a PUBLISHED refusal and its reason. Read as a pair: a refusal
# flag with no reason beside it is not a reasoned refusal, it is a blank.
REFUSAL_REASON_KEYS = ("withdrawn_reason", "why", "why_not_pooled", "poolable_reason",
                       "not_pooled", "not_pooled_either", "reason", "refusal_reason")

# ⛔ POLARITY, AND THE VALUE THAT MEANS REFUSED -- NOT THE PRESENCE OF THE KEY.
#
# The first draft of this gate tested `key in node`, so `poolable: True` -- a declaration
# that the efficacy outcome IS poolable, beside a `poolable_reason` explaining WHY it is
# -- counted as a refusal. Both apixaban pages then read as REFUSED_WITH_REASON and the
# gate reported ZERO findings where the measurement had found two. A GATE THAT READS AN
# AFFIRMATION AS ITS OPPOSITE FAILS SILENTLY AND IN THE FLATTERING DIRECTION.
#
# This is the repository's own inverted-guard class -- the signal that blocked the
# disclaimer and passed the assertion -- committed here by someone who had read that
# entry. A mention is not a claim, and a field is not a value.
REFUSAL_FLAG_KEYS = {"withdrawn": True, "poolable": False,
                     "permanently_refused": True, "refused": True}


def published_refusal(obj):
    """-> (bool, where). Does this object publish a refusal to report, WITH a reason?

    RE-DERIVED FROM THE OBJECT EVERY RUN, never read from the adjudication file. A gate
    that trusts a stored verdict cannot notice the day the object stops supporting it --
    it would pass a page whose refusal had been deleted, because a file still said the
    page had one.
    """
    found = []

    def visit(node, path):
        if isinstance(node, dict):
            flagged = any(node.get(k) is refusing
                          for k, refusing in REFUSAL_FLAG_KEYS.items() if k in node)
            reason = next((k for k in REFUSAL_REASON_KEYS
                           if isinstance(node.get(k), str) and len(node[k]) > 40), None)
            if flagged and reason:
                found.append("%s.%s" % (path, reason) if path else reason)
            for k, v in node.items():
                visit(v, "%s.%s" % (path, k) if path else k)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                visit(v, "%s[%d]" % (path, i))

    visit((obj.get("results") or {}).get("by_outcome") or {}, "results.by_outcome")
    return bool(found), found[:3]


def decide(obj, disposition):
    """The whole rule, in ONE place, shared by the gate, the measurement and the probes.

    The adjudication file supplies only what KIND OF MENTION this is -- a promise or not.
    Everything else is RE-DERIVED FROM THE OBJECT on every call, so a page that publishes
    its harm stops being a finding the moment it does, and a page that loses one starts
    being a finding the moment it does.

    -> one of:
        NOT_POLICED           the PICO names no harm, or the mention is not an undertaking
        REPORTED              a harm synthesis exists
        REFUSED_WITH_REASON   no synthesis, but a refusal carrying a reason is published
        PROMISED_NOT_REPORTED the finding
    """
    if disposition not in PROMISING:
        return "NOT_POLICED", []
    present, where = harms_synthesis(obj)
    if present:
        return "REPORTED", where
    refused, rwhere = published_refusal(obj)
    if refused:
        return "REFUSED_WITH_REASON", rwhere
    return "PROMISED_NOT_REPORTED", []
