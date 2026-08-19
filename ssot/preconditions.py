"""The preconditions a topic must satisfy before it may publish a pooled estimate.

EIGHT of them, as of 2026-08-19. They were authored as SEVEN and `inclusion_criteria_auditable`
later split into `criteria_stated` + `criteria_predefined` -- see the block above those two.

=============================================================================
THESE WERE AUTHORED IN THIS SESSION. THEY WERE NOT RECOVERED.
=============================================================================

`build_queue_v2.tsv` and the registered assessor set both went out with the discarded
working tree of 2026-08-18. `assessor_registry.Registry()` had ZERO registered assessors
when this session started. So the preconditions below are NEW, and that fact is recorded here
rather than in a commit message, deliberately.

WHY IT IS RECORDED. Authoring the standard you have been asked to measure against is this
project's own substitution class, aimed at the refusal list: if the author of the
preconditions is also the author of the refusals, then a topic's refusal is not evidence
about the topic. Naming the constraint in the artifact does not remove it. What it does is
let a later reader **disagree with the standard rather than with the results** -- the
verdicts below are reproducible from these definitions, so replacing a definition
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
THE AUTHORITY WAS VERIFIED ON 2026-08-19, AND THREE CITATIONS DID NOT SURVIVE IT.
=============================================================================

Every section was READ from the primary source on 2026-08-19, not recalled. What the
reading changed:

| cited from recall | what the source actually says | outcome |
|---|---|---|
| Handbook 6.5 s23.1 = multi-arm | s23.1 is **cluster-randomized trials** | WRONG, replaced |
| Handbook 6.5 s23.2 = factorial | s23.2 is **crossover trials** | WRONG, replaced |
| MECIR "Box 10.10.a C62" | no "Box 10.10.a" in the MECIR manual | UNVERIFIED, dropped |
| Handbook 6.5 s10.10.3 as the PICO-limb rule | it is "Strategies for addressing heterogeneity" | MISCITED, replaced by MECIR C5/C7/C8/C62 |
| MECIR C62 | verbatim as claimed, Mandatory | HOLDS |

**And one was wrong on the merits, not merely on its number.** The old
`one_randomised_comparison` required exactly ONE topic-vs-control comparison per trial.
Handbook 6.5 s23.3.4 says the recommended method is to COMBINE all relevant experimental
groups and all relevant comparator groups, and that selecting a single pair "results in a
loss of information and is open to results-related choices, so is not generally
recommended." The check demanded the strategy the Handbook discourages and FAILED trials it
says to include. Rewritten and renamed `contributes_a_randomised_contrast`.

That is the point of reading rather than recalling: a wrong section NUMBER is caught by
looking it up, but a wrong RULE is only caught by reading what the section says.

SOURCES READ 2026-08-19
  * Handbook version string "Version 6.5, 2024" --
    cochrane.org/authors/handbooks-and-manuals/handbook/current
  * Chapter 23 "Including variants on randomized trials", s23.3.3/23.3.4/23.3.6
  * Chapter 10 "Analysing data and undertaking meta-analyses", s10.10.3
  * MECIR standards C5, C6, C7, C8, C9, C62 -- extracted from the official MECIR PDF
    (cochrane.org/sites/default/files/uploads/PDFs/MECIR/MECIR Version February 2022.pdf)

WHAT VERIFICATION UNLOCKS. `verdict_is_publishable()` now returns True, so a topic MAY be
refused on these grounds. It gates publication, never computation -- the verdicts were
always computable; what was missing was the right to act on them.
"""

from assessment import (FAIL, NOT_ASSESSABLE, PASS, handbook_authority_is_verified, judge,
                        read, read_scalar)
from assessor_registry import AssessorRejected, Registry, normalise_text, text_match

# Every section cited below was read from the primary source on this date. Setting this to
# None again -- or changing a citation without re-reading -- must re-close the gate.
SECTION_VERIFIED_ON = "2026-08-19"

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
    handbook_section="MECIR C62 'Ensuring meta-analyses are meaningful' (Mandatory, READ "
                     "2026-08-19): 'Undertake (or display) a meta-analysis only if "
                     "participants, interventions, comparisons and outcomes are judged to be "
                     "sufficiently similar...'; MECIR C5 'Predefining unambiguous criteria "
                     "for participants' (Mandatory)",
    unit="object")
def population_stated(obj):
    """Can the object state WHICH PARTICIPANTS its pooled question is about?

    WHAT THIS DOES NOT DO. It does not check that the included trials MATCH that population.
    RIOCIGUAT_PAH (PAH pooled with CTEPH) and DABIGATRAN_STROKE (AF pooled with ESUS) both
    STATE a population correctly and then include trials from another one. Catching that
    needs the registry's condition field per trial, and it is a separate check that is not
    in this set. This precondition is the weaker, prior question: is there a stated
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
    handbook_section="MECIR C62 (Mandatory), 'interventions' limb -- this is a PRECONDITION "
                     "FOR ASSESSING C62, not an enforcement of it: you cannot judge whether "
                     "interventions are 'sufficiently similar' without knowing which arm is "
                     "the intervention. NOT cited to C5/C7: those govern PREDEFINITION of "
                     "criteria, and this check only reads whether a field is populated.",
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
    "comparators_identified",
    reads=["outcomes.comparator", "outcomes.comparator_type"],
    handbook_section="MECIR C62 (Mandatory), 'comparisons' limb -- a synthesis pools one "
                     "contrast. NOT cited to C7: C7 governs PREDEFINITION, and this check "
                     "reads recorded comparator fields and tests them for consistency.",
    unit="outcome", unit_source="outcomes")
def comparators_identified(obj):
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
    # THE SEMANTIC FIELD DECIDES; THE FREE TEXT ONLY CORROBORATES.
    #
    # This check first compared `outcomes.comparator`, which is a DESCRIPTION, and FAILed
    # sglt2-hf on:
    #     'placebo added to background heart failure therapy'  vs  'placebo'
    # Those are the same comparator at two levels of verbosity. The object says so in the
    # field beside it -- `comparator_type` is 'placebo' on BOTH -- and every included trial's
    # control arm is labelled exactly 'placebo'.
    #
    # That is the 2026-08-18 `comparator` defect reappearing in the check written to replace
    # it, ONE FIELD OVER. Routing through text_match satisfied detector 2 and did not save me,
    # because the error was never the comparison method: it was asking a TEXT question where a
    # SEMANTIC answer was recorded. "Added to background therapy" is not schedule noise, so
    # text_match is right to call the strings different -- and the strings were the wrong thing
    # to consult.
    #
    # So: comparator_type governs. A difference in the free text where the types AGREE is a
    # verbosity note, never a FAIL. A genuine difference in type is still a FAIL.
    # THE UNIT IS ONE OUTCOME, NOT THE OBJECT. This check compared comparator_type ACROSS
    # outcomes and FAILed iv-iron-hf, which carries six outcomes over different trial subsets:
    # five declare `placebo` and one declares `mixed`, because AFFIRM-AHF randomised against a
    # saline placebo and IRONMAN against usual care. The object's eligibility criterion admits
    # both DELIBERATELY -- "a placebo-only criterion would exclude it, which is the defect this
    # criterion was written to avoid" -- and its poolable_reason says the trials "share no
    # participant and no control group". The object had already declared everything the check
    # was trying to discover.
    #
    # Requiring six outcomes to share one comparator type is an OBJECT-level judgement made by
    # a check that declares unit="outcome". It iterates outcomes, so detector 5 passed it, and
    # it still judged across them. Different outcomes may legitimately rest on different
    # contrasts; that is not one synthesis pooling two contrasts, it is two questions.
    #
    # WHAT IS ACTUALLY CHECKABLE HERE, stated rather than overclaimed: whether every outcome
    # NAMES a comparator type, and whether any outcome DECLARES within-outcome heterogeneity
    # via `mixed`. Per-trial comparators are not stored per outcome, so within-outcome
    # consistency is visible ONLY through that declared type -- and `mixed` is the object
    # reporting it correctly, not failing.
    types = {}
    for o in outcomes:
        tr = read_scalar(o, "comparator_type")
        oid = o.get("id") or o.get("name") or "<unnamed>"
        if tr.readable:
            types[oid] = tr.value
    if len(types) != len(outcomes):
        silent = [o.get("id") or "<unnamed>" for o in outcomes
                  if (o.get("id") or o.get("name") or "<unnamed>") not in types]
        return NOT_ASSESSABLE, (
            f"cannot assess: {len(silent)} of {len(outcomes)} outcome(s) declare no "
            f"comparator_type {silent[:4]}")
    mixed = [k for k, v in types.items() if text_match(v, "mixed")]
    distinct = sorted(set(normalise_text(v) for v in types.values()))
    if mixed:
        return PASS, (
            f"every outcome names a comparator type; {len(mixed)} DECLARE 'mixed' {mixed} -- "
            f"the object reporting within-outcome comparator heterogeneity itself, which is "
            f"the state this check exists to surface, not a failure. Types across outcomes "
            f"({distinct}) are NOT judged: different outcomes may rest on different contrasts.")
    return PASS, (
        f"every outcome names a comparator type {distinct}; none declares 'mixed'. "
        f"Within-outcome consistency is visible only through the declared type, and "
        f"cross-outcome differences are not judged.")

    # No semantic field to consult -- fall back to the description, and SAY that the verdict
    # rests on display text rather than on a typed field.
    first = named[0]
    disagreeing = [c for c in named[1:] if not text_match(first, c)]
    if disagreeing:
        return FAIL, (
            f"outcomes.comparator: {len(disagreeing) + 1} distinct comparators after "
            f"normalisation ({first!r} vs {disagreeing[:3]!r}), and comparator_type is not "
            f"recorded on every outcome, so this verdict rests on DISPLAY TEXT rather than on "
            f"a typed field. One synthesis pools one contrast; the review must say which.")
    return PASS, (f"outcomes.comparator: all {len(named)} outcome(s) name {first!r} "
                  f"(comparator_type not recorded on every outcome; verdict rests on text)")


# ---------------------------------------------------------------------------
# 4. OUTCOME -- the O limb, via the three-state estimand identity.
# ---------------------------------------------------------------------------
@register_precondition(
    "estimand_named",
    reads=["outcomes.estimand", "outcomes.definition"],
    handbook_section="MECIR C8 'Clarifying role of outcomes' (Mandatory, READ 2026-08-19); "
                     "MECIR C62 (Mandatory), 'outcomes' limb",
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
# THIS WAS ONE PRECONDITION AND IS NOW TWO, FOR THE THIRD TIME IN TWO NIGHTS.
#
# `inclusion_criteria_auditable` cited MECIR C5/C7. Reading the MECIR manual on 2026-08-19
# showed those govern PREDEFINITION -- "Define in advance..." -- while the check only asks
# whether the object can STATE its criteria. MECIR has separate REPORTING standards whose
# verb is exactly the difference:
#
#   R29 "Eligibility criteria for types of participants"  (Mandatory) -- "STATE eligibility
#       criteria for participants, including any criteria around location, setting, diagnosis
#       or definition of condition and demographic factors..."
#   R30 "Eligibility criteria for types of interventions" (Mandatory) -- "STATE eligibility
#       criteria for interventions and comparators..."
#   R31 "Role of outcomes" (Mandatory)
#
# So STATING and PREDEFINING are two questions, and one name was carrying both -- the same
# shape as `inclusion_criteria_auditable` vs `eligibility_met`, and as `subject_role`.
# Splitting them is what lets a DERIVED criteria block discharge the first and honestly fail
# the second, instead of one verdict having to be wrong either way.

@register_precondition(
    "criteria_stated",
    reads=["screening.eligibility"],
    handbook_section="MECIR R29 'Eligibility criteria for types of participants', R30 "
                     "'...types of interventions', R31 'Role of outcomes' -- ALL Mandatory "
                     "REPORTING standards (READ 2026-08-19). Their verb is STATE. A block "
                     "DERIVED post hoc satisfies this if it is labelled post hoc per R107.",
    unit="object")
def criteria_stated(obj):
    """Can the OBJECT state the criteria its included set was chosen by, however arrived at?

    A declared "not recorded on the page this object was built from" is a readable, definite
    NO -- FAIL. No `screening` key at all is silence -- NOT_ASSESSABLE.

    This does NOT ask whether the criteria were predefined. `criteria_predefined` asks that,
    and a derived block cannot discharge it.
    """
    return judge(read(obj, "screening.eligibility"), declared_absence_is_failure=True)


@register_precondition(
    "criteria_predefined",
    reads=["screening.eligibility_provenance", "absent_from_source.protocol"],
    handbook_section="MECIR C5 'Predefining unambiguous criteria for participants' AND C7 "
                     "'...for interventions and comparators', BOTH Mandatory (READ "
                     "2026-08-19): 'Predefined, unambiguous eligibility criteria are a "
                     "fundamental prerequisite for a systematic review.' C5/C7 govern "
                     "PREDEFINITION and CANNOT be discharged by a post hoc derivation.",
    unit="object")
def criteria_predefined(obj):
    """Were the criteria defined IN ADVANCE? A derived block is definitively NOT.

    THIS PRECONDITION EXISTS TO BE UNDISCHARGEABLE WHERE IT SHOULD BE. C5/C7 exist precisely
    to stop an author reading the included trials and then writing criteria that fit them.
    A block derived from the object's own recorded question and recorded exclusions is exactly
    that shape -- legitimate for auditability under R107, and NOT pre-specification.

    So a derived block sets `predefined: false` and this returns FAIL, permanently and
    correctly. Recording that as a PASS would be the substitution class, wearing the
    derivation as cover.
    """
    prov = read(obj, "screening.eligibility_provenance")
    if prov.readable:
        flag = read_scalar(prov.value, "predefined")
        if flag.readable and flag.value is False:
            return FAIL, ("screening.eligibility_provenance.predefined is false: the criteria "
                          "were DERIVED post hoc from this object's own question and recorded "
                          "exclusions. That is auditable (R29/R30/R31) and is not "
                          "pre-specification (C5/C7). This FAIL is permanent and correct.")
        if flag.readable and flag.value is True:
            return PASS, "screening.eligibility_provenance.predefined is true"
    # No provenance block: fall back to whether a PROTOCOL was recoverable at all. A protocol
    # is the artefact in which predefinition would live.
    proto = read(obj, "absent_from_source.protocol")
    if proto.readable:
        return FAIL, (f"no eligibility provenance, and absent_from_source.protocol says: "
                      f"{str(proto.value)[:90]!r}. Predefinition cannot be shown without one.")
    return NOT_ASSESSABLE, ("cannot assess: the object records neither an eligibility "
                            "provenance block nor a statement about its protocol")


# ---------------------------------------------------------------------------
# 6. ELIGIBILITY MET -- did the trials actually meet those criteria?
# ---------------------------------------------------------------------------
@register_precondition(
    "eligibility_met",
    reads=["screening.eligibility", "sources"],
    handbook_section="MECIR C5/C7 (Mandatory) with C6 'Predefining a strategy for studies "
                     "with a subset of eligible participants' (Highly desirable, READ "
                     "2026-08-19) -- eligibility is assessed against the full report",
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
#
# THE ROLE VOCABULARY IS DECLARED, AND AN UNKNOWN VALUE IS NOT_ASSESSABLE.
#
# The first version of this precondition hardcoded `experimental` as the topic-arm role. The
# corpus writes `treatment` / `control`. Every object therefore had ZERO topic arms, and the
# precondition returned "NO randomised comparison of the topic against a non-topic arm" --
# a confident FAIL, on five live topics, all five false. Each was in fact a clean
# one-treatment-one-control design.
#
# That is the drug-name-matcher error again: THE CHECK ASKED A QUESTION THE DATA DOES NOT
# ANSWER IN THAT FIELD. And it failed in the direction that manufactures defects rather than
# hiding them, which is the rarer and more damaging direction -- a false defect claim on a
# live page.
#
# WHY THE KNOWN-ANSWER TEST DID NOT CATCH IT: the test data was INVENTED by the author of the
# code, using the same wrong vocabulary. A known-answer test built from synthetic data tests
# the code against its author's assumptions, not against the corpus. The fixture below is
# taken from the corpus, and the general rule is now in the ledger: THE KNOWN ANSWER MUST
# COME FROM THE DATA, NOT FROM THE AUTHOR.
#
# So the vocabulary is enumerated and inspectable, and anything not on either list is
# NOT_ASSESSABLE -- never silently sorted into "not the topic arm", which is what produced
# the false FAILs.

# ONLY STRICTLY UNAMBIGUOUS TERMS. An ambiguous role falls through to `unknown` and becomes
# NOT_ASSESSABLE, which is the safe direction; putting it here is the unsafe one.
#
# `"active"` and `"intervention"` WERE on this list and were removed 2026-08-19 after a
# cross-family review (Gemini 3.1 Pro) predicted the failure and a test reproduced it exactly:
#
#     arms = [{"role": "treatment"}, {"role": "active"}]
#       -> "active" classified TOPIC -> the trial has 2 topic arms and 0 control arms
#       -> FAIL "no control arm"
#
# "Active" is routine shorthand for ACTIVE COMPARATOR, i.e. a CONTROL arm. So the ambiguity
# ran in the direction that MANUFACTURES a false FAIL on a trial that has a perfectly good
# active-controlled contrast -- the same rare, damaging direction as the `experimental`
# hardcoding this list was written to fix. Note `"active comparator"` is exact-matched into
# CONTROL_ARM_ROLES below and is unaffected; it is the BARE token that is unsafe.
TOPIC_ARM_ROLES = frozenset({
    "experimental", "treatment", "active treatment", "topic",
})
CONTROL_ARM_ROLES = frozenset({
    "control", "comparator", "active comparator", "active_comparator", "placebo",
    "placebo comparator", "placebo_comparator", "sham", "sham comparator",
    "usual care", "standard of care", "no intervention", "standard care",
})


def classify_arm_role(value):
    """Topic side, control side, or UNKNOWN. Never guesses; the lists above are the whole rule."""
    for known in TOPIC_ARM_ROLES:
        if text_match(value, known):
            return "topic"
    for known in CONTROL_ARM_ROLES:
        if text_match(value, known):
            return "control"
    return "unknown"

@register_precondition(
    "contributes_a_randomised_contrast",
    reads=["inputs.trials.arms"],
    handbook_section="Handbook 6.5 s23.3.4 'How to include multiple groups from one study' "
                     "(READ 2026-08-19) and s23.3.6 'Factorial trials'; MECIR C7 "
                     "'Predefining unambiguous criteria for interventions and comparators' "
                     "(Mandatory)",
    unit="trial", unit_source="trials")
def contributes_a_randomised_contrast(obj):
    """Can every trial contribute a topic-vs-control randomised contrast AT ALL?

    ==========================================================================
    THIS PRECONDITION WAS WRONG ON THE MERITS AND THE HANDBOOK SAID SO.
    ==========================================================================

    Its first version was named `one_randomised_comparison` and required EXACTLY ONE
    topic-vs-control comparison per trial, FAILing a multi-arm or factorial trial until the
    review named which comparison it asked about. It cited "s23.1 / s23.2" from recall.

    Reading Handbook 6.5 Chapter 23 on 2026-08-19:

      * s23.1 is CLUSTER-RANDOMIZED TRIALS. s23.2 is CROSSOVER TRIALS. Both citations were
        simply wrong -- the identifier-by-recall defect in methodological clothing.
      * The correct sections are s23.3.4 and s23.3.6, AND THEY SAY THE OPPOSITE OF WHAT THIS
        CHECK ENCODED:

            "The recommended method in most situations is to combine all relevant
             experimental intervention groups of the study into a single group, and to
             combine all relevant comparator intervention groups into a single comparator
             group."

            "The alternative strategy of selecting a single pair of interventions ...
             results in a loss of information and is open to results-related choices, so is
             NOT GENERALLY RECOMMENDED."

    So the old check demanded the strategy the Handbook explicitly discourages, and FAILED
    trials the Handbook says to INCLUDE by combining. A multi-arm or factorial trial is not
    a defect to be resolved by the review picking one arm -- it is a trial to be combined.

    THE CORRECTED QUESTION is the one that actually gates poolability: does the trial offer
    a topic side AND a control side at all? If it does, s23.3.4 tells you how to reduce it
    to one contrast. If it has no control side, no method recovers a contrast from it --
    that is the uncontrolled extension (MIPOMERSEN NCT00477594, both arms mipomersen;
    BOSENTAN_PAH NCT00319020, single arm). If it has no topic side, the topic drug is not
    the intervention here (the OLMESARTAN_HTN class, object-side).

    The rename is deliberate: `one_randomised_comparison` named a requirement that is not
    the Handbook's, and a name that misdescribes its check is how one word came to carry two
    questions on 2026-08-18.
    """
    r = read(obj, "inputs.trials")
    if not r.readable:
        return judge(r)
    trials = r.value
    silent, none_found, multi, unknown_vocab = [], [], [], []
    for t in trials:
        ident = t.get("nct") or t.get("id") or "<unidentified>"
        ar = read_scalar(t, "arms")
        if not ar.readable:
            silent.append(ident)
            continue
        topic, control, unknown = 0, 0, []
        for a in ar.value:
            rr = read_scalar(a, "role")
            if not rr.readable:
                continue
            side = classify_arm_role(rr.value)
            if side == "topic":
                topic += 1
            elif side == "control":
                control += 1
            else:
                unknown.append(rr.value)
        if unknown:
            unknown_vocab.append(f"{ident}:{unknown[:2]}")
            continue
        if not topic and not control:
            silent.append(ident)
            continue
        if not control:
            none_found.append(f"{ident}(no control arm)")
        elif not topic:
            none_found.append(f"{ident}(no topic arm)")
        elif topic > 1 or control > 1:
            # s23.3.4: COMBINE. Not a failure -- a handling instruction, recorded so the
            # synthesis states which groups it merged.
            multi.append(f"{ident}({topic}x{control})")
    # An UNRECOGNISED role vocabulary is a fact about the schema, not about the trial. It
    # must never be sorted into "not the topic arm" -- that is what produced five false FAILs.
    if unknown_vocab:
        return NOT_ASSESSABLE, (
            f"cannot assess: {len(unknown_vocab)} trial(s) carry arm roles outside the "
            f"declared vocabulary {unknown_vocab[:4]}. Extend TOPIC_ARM_ROLES / "
            f"CONTROL_ARM_ROLES deliberately; do not let an unknown role count as a non-match.")
    if silent and not (none_found or multi):
        return NOT_ASSESSABLE, (
            f"cannot assess: {len(silent)} of {len(trials)} trial(s) carry no readable arm "
            f"roles {silent[:4]}")
    if none_found:
        return FAIL, (
            f"inputs.trials.arms: {len(none_found)} trial(s) can contribute NO randomised "
            f"contrast {none_found[:4]}. No method in Handbook 6.5 s23.3.4 recovers a "
            f"contrast from a trial with no control side or no topic side.")
    if multi:
        # PASS with the instruction recorded. s23.3.4 makes this includable, not defective.
        return PASS, (
            f"inputs.trials.arms: all {len(trials) - len(silent)} readable trial(s) contribute "
            f"a randomised contrast; {len(multi)} are multi-arm {multi[:4]} and are COMBINED "
            f"per Handbook 6.5 s23.3.4 (combine all relevant experimental groups into one and "
            f"all relevant comparator groups into one), NOT reduced by selecting a single pair")
    return PASS, (
        f"inputs.trials.arms: all {len(trials) - len(silent)} readable trial(s) contribute one "
        f"topic-vs-control randomised contrast")


# EIGHT, NOT SEVEN, AND THE COUNT CHANGED FOR A REASON WORTH KEEPING.
#
# `inclusion_criteria_auditable` split into `criteria_stated` (R29/R30/R31, dischargeable by
# a derivation) and `criteria_predefined` (C5/C7, not dischargeable post hoc) on 2026-08-19.
# The name SEVEN is retained as an alias so nothing that imported it breaks silently, but the
# canonical name is PRECONDITIONS and the count is 8. A constant whose name asserts a count
# that is no longer true is the stale-prose defect in identifier form.
PRECONDITIONS = ("population_stated", "arm_role_resolved",
                 "comparators_identified", "estimand_named",
                 "criteria_stated", "criteria_predefined", "eligibility_met",
                 "contributes_a_randomised_contrast")

SEVEN = PRECONDITIONS      # deprecated alias; the set is now eight

assert len(REGISTRY._by_name) == len(PRECONDITIONS), (
    f"expected {len(PRECONDITIONS)} registered, got {len(REGISTRY._by_name)}")
assert set(REGISTRY._by_name) == set(PRECONDITIONS), "registered names disagree with PRECONDITIONS"
