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
