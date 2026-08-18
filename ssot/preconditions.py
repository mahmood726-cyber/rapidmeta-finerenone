"""The seven preconditions a topic must satisfy before it may publish a pooled estimate.

=============================================================================
THESE SEVEN WERE AUTHORED IN THIS SESSION. THEY WERE NOT RECOVERED.
=============================================================================

`build_queue_v2.tsv` and the registered assessor set both went out with the discarded
working tree of 2026-08-18. `assessor_registry.Registry()` had ZERO registered assessors
when this session started. So the seven below are NEW, and that fact is recorded here
rather than in a commit message, deliberately.

WHY IT IS RECORDED. Authoring the standard you have been asked to measure against is this
project's own substitution class, aimed at the refusal list: if the author of the
preconditions is also the author of the refusals, then a topic's refusal is not evidence
about the topic. Naming the constraint in the artifact does not remove it. What it does is
let a later reader **disagree with the standard rather than with the results** -- the
verdicts below are reproducible from these seven definitions, so replacing a definition
replaces its verdicts mechanically, and no re-derivation of the corpus is needed.

Authorised 2026-08-19 under the standing instruction that the Handbook decides. Three
conditions were attached and all three are implemented here:

  1. Every precondition NAMES ITS HANDBOOK SECTION, and `HANDBOOK_AUTHORITY` stays
     FAIL-CLOSED until the cited edition is actually read. A precondition that cannot name
     its authority does not register (`register_precondition` raises).
  2. Every precondition registers through the FIVE DETECTORS in `assessor_registry`, and
     every one is known-answer tested before its output is trusted. The four defective
     assessors of 2026-08-18 were all caught mechanically and NONE of them by review.
  3. This notice.

=============================================================================
THE AUTHORITY IS NOT YET VERIFIED, AND THAT GATES PUBLICATION, NOT COMPUTATION.
=============================================================================

`assessment.HANDBOOK_AUTHORITY` carries `version=None, sections=None, verified_on=None`.
`handbook_authority_is_verified()` therefore returns False, and `verdict_is_publishable()`
below returns False with it.

The distinction matters and is deliberate:

  * The verdicts may be COMPUTED. They are reproducible facts about the objects.
  * No topic may be REFUSED ON HANDBOOK GROUNDS while the authority is unverified,
    because an unverified citation is not authority and must not be printed as one.

Section numbers below are cited as CLAIMED, from the sections named in the corpus's own
prior work (`FINDINGS-AUDIT-FIRST-VERDICTS-2026-08-18.md` cites MECIR Box 10.10.a C62 and
Handbook 6.5 s10.10.3). They are recorded so a reader can check them. They are NOT recorded
as verified, and `SECTION_VERIFIED_ON` is None for every one.
"""

from assessment import (FAIL, NOT_ASSESSABLE, PASS, handbook_authority_is_verified, judge,
                        read, read_scalar)
from assessor_registry import AssessorRejected, Registry, text_match

# Every citation below is CLAIMED, never verified. None of these has been read in the
# current edition during this session, so all of them stay fail-closed.
SECTION_VERIFIED_ON = None

REGISTRY = Registry()
_SECTIONS = {}
_UNITS = {}


def verdict_is_publishable():
    """Fail closed. A verdict resting on an unverified citation is not a Handbook verdict."""
    return handbook_authority_is_verified() and SECTION_VERIFIED_ON is not None


def register_precondition(name, reads, handbook_section, unit="object", unit_source="",
                          accepts=None):
    """Registration gate. Adds ONE requirement to the five detectors: name your authority."""
    if not handbook_section or not str(handbook_section).strip():
        raise AssessorRejected(
            f"{name}: names no Handbook section. A precondition that cannot say which rule "
            f"it enforces is an opinion, and it does not register.")

    def deco(fn):
        REGISTRY.register(name, fn, reads, accepts, unit, unit_source)
        _SECTIONS[name] = handbook_section
        _UNITS[name] = unit
        return fn
    return deco


# ---------------------------------------------------------------------------
# 1. POPULATION -- the P limb.
# ---------------------------------------------------------------------------
@register_precondition(
    "population_stated",
    reads=["question", "title"],
    handbook_section="MECIR Box 10.10.a C62 (claimed); Handbook 6.5 s10.10.3 'participants' "
                     "limb -- a synthesis states the participants it is about",
    unit="object")
def population_stated(obj):
    """Can the object state WHICH PARTICIPANTS its pooled question is about?

    WHAT THIS DOES NOT DO. It does not check that the included trials MATCH that population.
    RIOCIGUAT_PAH (PAH pooled with CTEPH) and DABIGATRAN_STROKE (AF pooled with ESUS) both
    STATE a population correctly and then include trials from another one. Catching that
    needs the registry's condition field per trial, and it is a separate check that is not
    in these seven. This precondition is the weaker, prior question: is there a stated
    population to audit against at all. A PASS here is not a claim that the population is
    homogeneous.
    """
    r = read(obj, "question")
    if r.state in ("absent", "empty", "unreadable"):
        r = read(obj, "title")
    return judge(r, declared_absence_is_failure=True)


# ---------------------------------------------------------------------------
# 2. INTERVENTION -- the I limb, by arm ROLE and never by arm label.
# ---------------------------------------------------------------------------
@register_precondition(
    "arm_role_resolved",
    reads=["inputs.trials"],
    handbook_section="MECIR Box 10.10.a C62 (claimed); Handbook 6.5 s10.10.3 'interventions' "
                     "limb -- the intervention must be the one the review asks about",
    unit="trial", unit_source="trials")
def arm_role_resolved(obj):
    """Does EVERY included trial carry arms with a readable role?

    This is the object-side half of the defect `topic_identity.py` fixes search-side. A
    trial whose `arms` are absent or whose roles are blank is NOT_ASSESSABLE -- agy's
    `{"role": ""}` case, where counting a blank as a non-match turned missing data into a
    negative finding.
    """
    r = read(obj, "inputs.trials")
    if not r.readable:
        return judge(r)
    trials = r.value
    unreadable, roleless = [], []
    for t in trials:
        ar = read_scalar(t, "arms")
        if not ar.readable:
            unreadable.append(t.get("nct") or t.get("id") or "<unidentified>")
            continue
        for a in ar.value:
            rr = read_scalar(a, "role")
            if not rr.readable:
                roleless.append(t.get("nct") or t.get("id") or "<unidentified>")
                break
    if unreadable or roleless:
        return NOT_ASSESSABLE, (
            f"cannot assess: inputs.trials has {len(unreadable)} trial(s) with no readable "
            f"arms {unreadable[:4]} and {len(roleless)} with a blank arm role {roleless[:4]}. "
            f"Absent role data is not a wrong role.")
    return PASS, f"inputs.trials: all {len(trials)} trial(s) carry arms with a readable role"


# ---------------------------------------------------------------------------
# 3. COMPARATOR -- the C limb. Identity, after normalisation, never raw display text.
# ---------------------------------------------------------------------------
@register_precondition(
    "comparator_identified",
    reads=["outcomes.comparator", "outcomes.comparator_type"],
    handbook_section="MECIR Box 10.10.a C62 (claimed); Handbook 6.5 s10.10.3 'comparator' -- "
                     "one synthesis pools one contrast",
    unit="outcome", unit_source="outcomes")
def comparator_identified(obj):
    """Does every outcome name a comparator, and do they agree ACROSS outcomes?

    Routed through `text_match`, which is what keeps `Placebo Q2W` == `Placebo` (a schedule
    is not part of a comparator's identity) while keeping `warfarin` != `aspirin`. The
    2026-08-18 `comparator` assessor compared control-arm LABELS with string equality and
    scored those two placebos as different comparators.
    """
    r = read(obj, "outcomes")
    if not r.readable:
        return judge(r)
    outcomes = r.value
    named, missing = [], []
    for o in outcomes:
        cr = read_scalar(o, "comparator")
        if cr.readable:
            named.append(cr.value)
        else:
            missing.append(o.get("id") or o.get("name") or "<unnamed outcome>")
    if missing:
        return NOT_ASSESSABLE, (
            f"cannot assess: {len(missing)} of {len(outcomes)} outcome(s) carry no readable "
            f"comparator {missing[:4]}")
    first = named[0]
    disagreeing = [c for c in named[1:] if not text_match(first, c)]
    if disagreeing:
        return FAIL, (
            f"outcomes.comparator: {len(disagreeing) + 1} distinct comparators after "
            f"normalisation ({first!r} vs {disagreeing[:3]!r}). One synthesis pools one "
            f"contrast; the review must say which.")
    return PASS, f"outcomes.comparator: all {len(named)} outcome(s) name {first!r}"


# ---------------------------------------------------------------------------
# 4. OUTCOME -- the O limb, via the three-state estimand identity.
# ---------------------------------------------------------------------------
@register_precondition(
    "estimand_named",
    reads=["outcomes.estimand", "outcomes.definition"],
    handbook_section="MECIR Box 10.10.a C62 (claimed); Handbook 6.5 s10.10.3 'outcomes' -- "
                     "trials registering different quantities are not one estimand",
    unit="outcome", unit_source="outcomes")
def estimand_named(obj):
    """Does every outcome name the QUANTITY it estimates?

    UNDECIDABLE IS NOT FAIL, and that is the whole point of `estimand_identity`. The
    2026-08-18 estimand assessor reported 7 FAILs; 4 were unearned and became UNDECIDABLE
    once a discriminator had to be NAMED. This precondition therefore asks only the prior,
    decidable question -- is a quantity named at all -- and leaves SAME/DIFFERENT/UNDECIDABLE
    to `estimand_identity.compare`, which refuses rather than interpolates.
    """
    r = read(obj, "outcomes")
    if not r.readable:
        return judge(r)
    outcomes = r.value
    silent = []
    for o in outcomes:
        er = read_scalar(o, "estimand")
        dr = read_scalar(o, "definition")
        if not er.readable and not dr.readable:
            silent.append(o.get("id") or o.get("name") or "<unnamed outcome>")
    if silent:
        return NOT_ASSESSABLE, (
            f"cannot assess: {len(silent)} of {len(outcomes)} outcome(s) name neither an "
            f"estimand nor a definition {silent[:4]}")
    return PASS, f"outcomes.estimand: all {len(outcomes)} outcome(s) name a quantity"


# ---------------------------------------------------------------------------
# 5. AUDITABILITY -- can the included set be audited at all?
# ---------------------------------------------------------------------------
@register_precondition(
    "inclusion_criteria_auditable",
    reads=["screening.eligibility"],
    handbook_section="MECIR Box 10.10.a C62 (claimed); Handbook 6.5 s10.10.3 -- a review "
                     "states the criteria by which its included set was chosen",
    unit="object")
def inclusion_criteria_auditable(obj):
    """Can the OBJECT state the criteria its included set was chosen by?

    A declared "not recorded on the page this object was built from" is a readable, definite
    NO -- FAIL. No `screening` key at all is silence -- NOT_ASSESSABLE. These are different
    states and the 2026-08-18 split of this name from `eligibility_met` exists because one
    word was carrying both questions.
    """
    return judge(read(obj, "screening.eligibility"), declared_absence_is_failure=True)


# ---------------------------------------------------------------------------
# 6. ELIGIBILITY MET -- did the trials actually meet those criteria?
# ---------------------------------------------------------------------------
@register_precondition(
    "eligibility_met",
    reads=["screening.eligibility", "sources"],
    handbook_section="MECIR Box 10.10.a C62 (claimed); Handbook 6.5 s10.10.3 -- eligibility "
                     "is assessed against the full report, not a flattened record",
    unit="object")
def eligibility_met(obj):
    """Did THIS topic's trials meet the stated criteria?

    READS TWO PATHS, AND THAT IS THE POINT. `inclusion_criteria_auditable` reads only the
    criteria. This reads the criteria AND the evidence that a full text was available to
    assess them against. Declaring one path would make this a byte-identical duplicate of
    precondition 5 -- which is exactly what `subject_role` was on 2026-08-18, and detector 1
    would reject it.

    It is NOT_ASSESSABLE from JSON alone even when criteria ARE stated, because inclusion
    logic is conditional clinical prose ("exclude if X unless Y within 30 days") that a
    flattened record drops. It never degrades into an auditability check.
    """
    cr = read(obj, "screening.eligibility")
    if not cr.readable:
        return NOT_ASSESSABLE, (
            f"cannot assess: criteria are not stated ({cr.detail}), so whether any trial met "
            f"them cannot be decided")
    sr = read(obj, "sources")
    if not sr.readable:
        return NOT_ASSESSABLE, (
            f"cannot assess: criteria are stated, but {sr.detail} -- no full text was "
            f"available this pass, and inclusion logic is conditional prose")
    return NOT_ASSESSABLE, (
        "cannot assess: criteria are stated and sources are present, but no full text was "
        "READ this pass. This precondition never infers from the auditability check.")


# ---------------------------------------------------------------------------
# 7. DESIGN -- exactly one randomised comparison the review asks about.
# ---------------------------------------------------------------------------
@register_precondition(
    "one_randomised_comparison",
    reads=["inputs.trials.arms"],
    handbook_section="Handbook 6.5 s23.1 (claimed) variants on randomised trials -- more "
                     "than two intervention groups; s23.2 (claimed) factorial trials: take "
                     "ONE randomised comparison at a time",
    unit="trial", unit_source="trials")
def one_randomised_comparison(obj):
    """Does every trial offer exactly one topic-vs-control randomised comparison?

    NOT AN ARM-COUNT TEST. AUGUSTUS (NCT02415400) is an open-label 2x2 factorial and
    APPRAISE (NCT00313300) is multi-arm dose-ranging; an arm-count test rejects both and the
    Handbook does not. More than one candidate comparison is a DECISION THE REVIEW OWES ITS
    READER, not an ineligible trial -- so it is a FAIL that NAMES the candidates, and the
    review records which one it asks about.

    An uncontrolled extension (MIPOMERSEN NCT00477594, both arms mipomersen; BOSENTAN_PAH
    NCT00319020, single arm) yields ZERO comparisons and is a different FAIL.
    """
    r = read(obj, "inputs.trials")
    if not r.readable:
        return judge(r)
    trials = r.value
    silent, none_found, multi = [], [], []
    for t in trials:
        ident = t.get("nct") or t.get("id") or "<unidentified>"
        ar = read_scalar(t, "arms")
        if not ar.readable:
            silent.append(ident)
            continue
        roles = []
        for a in ar.value:
            rr = read_scalar(a, "role")
            if rr.readable:
                roles.append(rr.value)
        if not roles:
            silent.append(ident)
            continue
        topic = [x for x in roles if text_match(x, "experimental")]
        control = [x for x in roles if not text_match(x, "experimental")]
        n = len(topic) * len(control)
        if n < 1:
            none_found.append(ident)
        elif n > 1:
            multi.append(f"{ident}({n})")
    if silent and not (none_found or multi):
        return NOT_ASSESSABLE, (
            f"cannot assess: {len(silent)} of {len(trials)} trial(s) carry no readable arm "
            f"roles {silent[:4]}")
    if none_found:
        return FAIL, (
            f"inputs.trials.arms: {len(none_found)} trial(s) offer NO randomised comparison "
            f"of the topic against a non-topic arm {none_found[:4]} -- an uncontrolled "
            f"extension cannot contribute a contrast")
    if multi:
        return FAIL, (
            f"inputs.trials.arms: {len(multi)} trial(s) offer more than one candidate "
            f"randomised comparison {multi[:4]}. Not ineligible -- the review must name which "
            f"comparison it asks about (factorial / dose-ranging designs)")
    return PASS, (
        f"inputs.trials.arms: all {len(trials) - len(silent)} readable trial(s) offer exactly "
        f"one topic-vs-control randomised comparison")


SEVEN = ("population_stated", "arm_role_resolved", "comparator_identified", "estimand_named",
         "inclusion_criteria_auditable", "eligibility_met", "one_randomised_comparison")

assert len(REGISTRY._by_name) == 7, f"expected 7 registered, got {len(REGISTRY._by_name)}"
assert set(REGISTRY._by_name) == set(SEVEN), "registered names disagree with SEVEN"
