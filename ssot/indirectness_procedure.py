# -*- coding: utf-8 -*-
"""GRADE indirectness as a stated procedure, not a judgement made once in prose.

⭐ WHY THIS IS NOW THE HIGHEST-VALUE THING. Across 157 pooled results this engine can
evaluate, ONE carries a certainty letter and 156 refuse. The largest single cause is this
domain: 53 results refuse on indirectness, more than risk of bias (46). Retrieval is no
longer the bottleneck -- ClinicalTrials.gov posted results answered 40 of 47 blocked
risk-of-bias trials -- and no registry can answer indirectness, because IT IS A REASONING
STEP AND NOT A LOOKUP.

The reasoning exists correctly on exactly one topic. It was done for dapivirine, adjudicated
unanimously across three model families, and it is prose. This module is that reasoning
made repeatable.

THE PROCEDURE, from Cochrane Handbook 14.2.2 domain (3):

    "a review may find randomized trials that meet eligibility criteria but address a
     RESTRICTED VERSION of the main review question in terms of population ... the evidence
     may be regarded as indirect in relation to THE BROADER QUESTION OF INTEREST."

Five axes are compared -- population, intervention, comparator, outcome, setting -- and each
is rated:

    DIRECT       the trials' value is the question's value.
    RESTRICTED   the trials cover a PROPER SUBSET of what the question asks about. This is
                 the Handbook's "restricted version" and it is the common case: age bands,
                 single regions, single health systems.
    SUBSTITUTED  the trials use a DIFFERENT value -- a surrogate outcome, a comparator the
                 question did not name. Not a subset; a substitution.

⭐⭐ AND THE DECISIVE TEST IS NOT SIMILARITY, IT IS ANTICIPATED EFFECTS. The Handbook's own
criterion in the same paragraph is "differences in ANTICIPATED EFFECTS in the group of
primary interest". A restriction matters when the effect is expected to differ outside the
studied range -- and a trial that reports an EFFECT MODIFIER INSIDE its own range has
supplied evidence that it does. ASPIRE reported efficacy of 61% at age 25 or above against
10% below it, P = 0.02 for interaction: that is not an extrapolation worry, it is a measured
one. Where such a modifier is recorded, this procedure treats a restriction on that same
axis as confirmed rather than suspected.

⛔ THREE RULES THIS PROCEDURE ENFORCES, EACH FROM A MISTAKE MADE ON DAPIVIRINE TODAY:

 1. RESTRICTION IS JUDGED AGAINST THE QUESTION AS ASKED. Narrowing the question to escape a
    downgrade is the same defect as removing the downgrade. Rescoping is an editorial act
    that must change the title and question a reader meets -- never a note beside a letter.

 2. BURDEN-RELEVANCE IS A PRIORITISATION ARGUMENT, NOT A DIRECTNESS ONE. "The trials ran
    where the burden is" is a reason they were the right trials to RUN. Handbook domain (3)
    never mentions disease burden. An earlier rating here cleared this domain on exactly
    that conflation and did not survive review.

 3. AN INDIRECTNESS RATING PRODUCED FROM AN UNSTATED QUESTION IS WORTHLESS. If the question's
    PICO is not declared in a comparable form, this REFUSES and names the missing field. It
    does NOT parse the question sentence, and it does NOT infer the question from the trials
    -- inferring the question from the evidence returns DIRECT by construction, which is the
    most dangerous answer this domain can give. This corpus came within one turn of letting a
    DIRECTORY SLUG govern a certainty rating; the refusal is what stops that.
"""
from __future__ import annotations

DIRECT = "DIRECT"
RESTRICTED = "RESTRICTED"
SUBSTITUTED = "SUBSTITUTED"
AXES = ("population", "intervention", "comparator", "outcome", "setting")

REFUSED = "REFUSED"
NO_DOWNGRADE = "NO_DOWNGRADE"
DOWNGRADE = "DOWNGRADE"

HANDBOOK = ("Cochrane Handbook 6.5.1 ch 14 s14.2.2, domain (3) indirectness: trials that "
            "address a RESTRICTED VERSION of the main review question, judged by "
            "differences in ANTICIPATED EFFECTS in the group of primary interest.")

# The declared question PICO. Deliberately a REQUIRED, SEPARATE structure: a prose question
# is not comparable axis by axis, and parsing one into axes would be this module inventing
# the question it is meant to be checking against.
PICO_KEY = "question_pico"
REQUIRED_AXES = ("population", "intervention", "comparator", "outcome")


def question_pico(canon, oid=None):
    """The DECLARED question PICO, or None. Never parsed out of the question sentence."""
    res = (((canon.get("results") or {}).get("by_outcome") or {}).get(oid or "") or {})
    for holder in (res, canon):
        p = holder.get(PICO_KEY)
        if isinstance(p, dict) and any(p.get(a) for a in REQUIRED_AXES):
            return p
    return None


def missing_axes(pico):
    return [a for a in REQUIRED_AXES if not (pico or {}).get(a)]


def _norm(s):
    return " ".join(str(s or "").split()).strip().lower()


def compare_axis(axis, asked, observed):
    """One axis: DIRECT, RESTRICTED or SUBSTITUTED, with the values that decided it.

    ⚠️ `asked` and `observed` are DECLARED values on both sides. This does no string
    cleverness: a declared question value of "women" against trials declaring "women aged
    18-45" is a restriction because the question says so and the trials say so, not because
    a matcher noticed a substring. Where either side is absent the axis is NOT_STATED and
    the caller refuses -- it is never quietly treated as agreement.
    """
    a, o = _norm(asked), _norm(observed)
    if not a or not o:
        return {"axis": axis, "verdict": None, "asked": asked, "observed": observed,
                "why": "NOT STATED on %s side" % ("the question" if not a else "the trials")}
    if a == o:
        return {"axis": axis, "verdict": DIRECT, "asked": asked, "observed": observed,
                "why": "The trials' value is the question's value."}
    if a in o or o in a:
        return {"axis": axis, "verdict": RESTRICTED, "asked": asked, "observed": observed,
                "why": ("The trials cover a proper subset of what the question asks about "
                        "-- the Handbook's 'restricted version of the main review "
                        "question'.")}
    return {"axis": axis, "verdict": SUBSTITUTED, "asked": asked, "observed": observed,
            "why": ("The trials use a DIFFERENT value, not a narrower one. A substitution "
                    "is a stronger objection than a restriction: a surrogate outcome or an "
                    "unasked comparator does not answer a narrower version of the "
                    "question, it answers a different question.")}


def anticipated_effects(canon, oid):
    """Is an effect MODIFIER recorded inside the studied range, and on which axis?

    ⭐ THIS IS WHAT SEPARATES A MEASURED CONCERN FROM AN EXTRAPOLATION WORRY, and it is a
    QUERYABLE FACT wherever a subgroup or interaction is stored. A restriction on an axis
    that a contributing trial has itself shown to modify the effect is confirmed, not
    suspected.
    """
    res = (((canon.get("results") or {}).get("by_outcome") or {}).get(oid) or {})
    out = []
    for key in ("effect_modifiers", "subgroups", "interactions"):
        v = res.get(key)
        if isinstance(v, list):
            for m in v:
                if isinstance(m, dict) and m.get("axis"):
                    out.append(m)
    return out


def rate(canon, oid, trial_pico, modifiers=None):
    """The indirectness rating for one pooled result, or a refusal naming what is missing.

    trial_pico -- {axis: declared value} for the CONTRIBUTING TRIALS, from their registry
                  records. Supplied by the caller so this module never fetches, and so the
                  values it judged are stored beside the verdict.
    """
    q = question_pico(canon, oid)
    if not q:
        return {"state": REFUSED, "levels": 0, "handbook": HANDBOOK,
                "reason": (
                    "NO DECLARED QUESTION PICO. This review states its question as prose "
                    "only, and prose cannot be compared axis by axis. Indirectness asks "
                    "whether the trials address a RESTRICTED VERSION of the question -- "
                    "which requires knowing what the question's population, intervention, "
                    "comparator and outcome ARE, as declared rather than as inferred. "
                    "⇒ THIS IS AN OBJECT DEFECT, NOT A RATING. Declare `%s` with the four "
                    "required axes." % PICO_KEY),
                "missing": [PICO_KEY]}
    gaps = missing_axes(q)
    if gaps:
        return {"state": REFUSED, "levels": 0, "handbook": HANDBOOK,
                "reason": ("The declared question PICO is incomplete: %s not stated. An "
                           "axis nobody declared cannot be compared, and treating it as "
                           "agreement would manufacture directness."
                           % ", ".join(gaps)),
                "missing": ["%s.%s" % (PICO_KEY, g) for g in gaps]}
    comps, unstated = [], []
    for axis in AXES:
        c = compare_axis(axis, q.get(axis), (trial_pico or {}).get(axis))
        if c["verdict"] is None:
            if axis in REQUIRED_AXES:
                unstated.append(c)
            continue
        comps.append(c)
    if unstated:
        return {"state": REFUSED, "levels": 0, "handbook": HANDBOOK, "comparisons": comps,
                "reason": ("Required axes could not be compared: %s. Refused rather than "
                           "rated on the remainder -- a rating assembled from the axes that "
                           "happened to be stated would carry a confidence the comparison "
                           "does not have."
                           % "; ".join("%s (%s)" % (c["axis"], c["why"]) for c in unstated)),
                "missing": [c["axis"] for c in unstated]}

    mods = {m.get("axis") for m in (modifiers or []) if isinstance(m, dict)}
    bad = [c for c in comps if c["verdict"] in (RESTRICTED, SUBSTITUTED)]
    confirmed = [c for c in bad if c["axis"] in mods]
    if not bad:
        return {"state": NO_DOWNGRADE, "levels": 0, "handbook": HANDBOOK,
                "comparisons": comps,
                "reason": ("Every axis the question declares is matched by the contributing "
                           "trials. No restriction and no substitution.")}
    levels = 1
    why = ("%d of %d axes are not direct: %s. Handbook domain (3): trials addressing a "
           "restricted version of the main review question are indirect in relation to the "
           "broader question of interest."
           % (len(bad), len(comps), ", ".join("%s %s" % (c["axis"], c["verdict"])
                                              for c in bad)))
    if confirmed:
        why += (" ⭐ AND THE CONCERN IS MEASURED RATHER THAN ANTICIPATED on %s: a "
                "contributing trial reports an effect modifier on that axis INSIDE its own "
                "studied range, which is evidence that transfer beyond it is unsupported."
                % ", ".join(sorted(c["axis"] for c in confirmed)))
    return {"state": DOWNGRADE, "levels": levels, "handbook": HANDBOOK,
            "comparisons": comps, "modifier_confirmed_axes": sorted(mods & {c["axis"] for c in bad}),
            "reason": why,
            "why_not_two_levels": (
                "Two levels requires the trials not to address the question at all. A "
                "RESTRICTED version is still a version of it; if the evidence were that far "
                "from the question, the error would be in eligibility rather than in this "
                "domain.")}
