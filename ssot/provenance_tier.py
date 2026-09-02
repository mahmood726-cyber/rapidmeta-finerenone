#!/usr/bin/env python3
"""WHERE DID THIS NUMBER COME FROM. A required field on every extracted value.

Measured 2026-08-26 across the 176 stored per-trial estimates carrying a point:

    journal cited              0   (0%)
    registry recorded         43   (24%)
    NOTHING RECORDED         133   (76%)

Three quarters of the numbers this review publishes do not say where they came from. So `k`
has not been measuring evidence; for most rows it has not been measuring anything stated. This
schema is the corpus's answer to that question for years, which is the argument for getting it
right rather than quick.

THE TIER IS NOT THE SOURCE. A source is "ClinicalTrials.gov" or "NEJM". A TIER says what kind
of artefact the number was read off, because that is what a reader needs in order to weight it:
a figure in a registry results table and a figure in a background citation are both "from
ClinicalTrials.gov" and are not remotely the same evidence.

    ⭐ WHENEVER A CHECK TESTS MEMBERSHIP, NAME THE PROPERTY YOU ACTUALLY WANT AND TEST THAT.

That rule was learned four times in one night, each time by an instrument that tested presence
in a container and reported it as the property the container was supposed to imply:

    `hasResults` was present            -> read as "results are available"   (false)
    a dict KEY held the NCT             -> read as "the row has no identifier" (false)
    a screening row existed             -> read as "the exclusion is auditable" (it was)
    a `study_references` row existed    -> read as "the trial is published"   (FALSE: two were
                                           BACKGROUND citations made BY the protocol, and one
                                           was a RESULT pair with 2016 and 2010 PMIDs on a
                                           trial registered in 2023)

`REGISTRY_REFERENCE_ROW` exists as its own tier for exactly that last case. It is not a
publication, it is a pointer that may or may not be to one, and it must never be silently
promoted to `JOURNAL_FULL_TEXT` by a script that merely found a PMID.
"""

import re

# ---------------------------------------------------------------------------
# THE TIERS, ordered strongest to weakest as EVIDENCE ABOUT THIS RESULT.
# Order is documented rather than implied, because someone will sort on it.
# ---------------------------------------------------------------------------
TIERS = {
    "REGISTRY_POSTED_RESULT": {
        "rank": 1,
        "what": "A value read from the trial's own posted results table on the registry "
                "(AACT `outcome_analyses` / `outcome_counts` / `outcome_measurements`, or the "
                "equivalent live record).",
        "why_it_ranks_here": "Deposited by the sponsor under a legal reporting duty, "
                             "structured, and not selected by an author writing a narrative.",
        "requires": ("registry", "accessed_utc", "table", "row_identifier"),
    },
    "JOURNAL_FULL_TEXT": {
        "rank": 2,
        "what": "A value read from the body or tables of the published report itself.",
        "why_it_ranks_here": "Peer reviewed and complete, but the presented analysis is the "
                             "one the authors chose to present.",
        "requires": ("pmid_or_doi", "accessed_utc", "locator"),
    },
    "JOURNAL_SUPPLEMENT": {
        "rank": 3,
        "what": "A value read from a supplementary appendix of the published report.",
        "why_it_ranks_here": "Same provenance as the full text, usually less scrutinised, and "
                             "frequently where the number a synthesis needs actually lives.",
        "requires": ("pmid_or_doi", "accessed_utc", "locator"),
    },
    "TRIAL_PROTOCOL": {
        "rank": 4,
        "what": "A value or definition read from the posted protocol.",
        "why_it_ranks_here": "Authoritative about INTENT and definitions; it is not a result "
                             "and must never be stored as one.",
        "requires": ("document_url", "accessed_utc", "version"),
    },
    "STATISTICAL_ANALYSIS_PLAN": {
        "rank": 5,
        "what": "A value or definition read from the posted SAP.",
        "why_it_ranks_here": "As above, and it is the artefact that settles whether an "
                             "analysis was pre-specified -- which domain 5 needs and this "
                             "corpus has never held for any trial.",
        "requires": ("document_url", "accessed_utc", "version"),
    },
    "JOURNAL_ABSTRACT": {
        "rank": 6,
        "what": "A value read from the abstract only, the full text not consulted.",
        "why_it_ranks_here": "A real source and a bounded one. It is where this corpus has "
                             "silently been for most of its estimates, and naming it is the "
                             "point: an abstract-sourced number is usable and must be "
                             "declared, not disguised as a full-text read.",
        "requires": ("pmid_or_doi", "accessed_utc"),
    },
    "PRIOR_SYNTHESIS": {
        "rank": 7,
        "what": "A value taken from someone else's meta-analysis or review rather than from "
                "the trial.",
        "why_it_ranks_here": "Second-hand. It carries the other review's extraction errors and "
                             "its selection decisions, and it can silently double-count.",
        "requires": ("pmid_or_doi", "accessed_utc", "which_trial_it_reports"),
    },
    "REGISTRY_REFERENCE_ROW": {
        "rank": 99,
        "what": "A citation listed on the registry record. NOT A RESULT AND NOT A PUBLICATION.",
        "why_it_ranks_here": "It is a pointer, and it is frequently a pointer to something "
                             "else entirely: measured on this corpus, `reference_type=BACKGROUND` "
                             "rows cite prior literature the PROTOCOL discussed, and even "
                             "`reference_type=RESULT` rows have been seen carrying PMIDs "
                             "predating the trial's registration by seven years. It may be "
                             "PROMOTED to JOURNAL_FULL_TEXT or JOURNAL_ABSTRACT only after the "
                             "cited paper has been opened and confirmed to report THIS trial.",
        "requires": ("registry", "reference_type", "pmid", "promoted_from_row_id"),
        "never_counts_as_evidence": True,
    },
    "DERIVED_HERE": {
        "rank": 0,
        "what": "A value this review COMPUTED from inputs of some other tier -- a risk ratio "
                "from two counts, a log SE from a printed interval, a mean difference from two "
                "arm means.",
        "why_it_ranks_here": "Rank 0 because it is not a tier of its own: it inherits the tier "
                             "of its INPUTS, which must be recorded alongside. A derived value "
                             "whose inputs are untiered is untiered.",
        "requires": ("formula", "inputs", "input_tiers"),
    },
    "COULD_NOT_DETERMINE": {
        "rank": 100,
        "what": "The value is stored and its origin is not established.",
        "why_it_ranks_here": "The honest state for the 133 estimates that currently record "
                             "nothing. It is not a failure to be hidden; it is the only "
                             "truthful label until someone traces the number, and it makes the "
                             "backlog countable.",
        "requires": (),
    },
}

# The state a value is in when nobody has said anything. Distinct from COULD_NOT_DETERMINE,
# which is a recorded finding that the origin could not be established.
UNSET = "NOT_YET_RECORDED"


# ===========================================================================================
# THE SOURCE HIERARCHY -- AND WHY `rank` ABOVE IS NOT IT
# ===========================================================================================
#
# `TIERS[t]["rank"]` puts REGISTRY_POSTED_RESULT at 1 and JOURNAL_FULL_TEXT at 2, and the
# reason it gives is real: a posted results table is deposited under a legal reporting duty
# and is not selected by an author writing a narrative. That is a good argument, and it is an
# argument about ONE QUESTION -- was this outcome declared, and reported at all. It is not an
# argument about what the effect on that outcome IS.
#
# Ranking both questions with one number conflated them, and the conflation cost real work:
#
#   * A fully published RCT was dropped from a topic because its registry entry carried
#     `hasResults=false`. Registry silence was read as "no results exist". It is not; it is
#     evidence about the REGISTRY. See `registry_silence_problems()` below.
#   * On the inclisiran topic the ORION-11 record holds THREE values for one endpoint --
#     -53.5 observed-case, -47.8 after washout, -49.9 the published imputation -- and the
#     registry's was taken because the registry outranked. Mixed with other trials'
#     published-imputation values that manufactured I2 = 74%. Harmonised to one variant the
#     same trials give tau2 = 0. The heterogeneity was a property of the EXTRACTION.
#
# So the hierarchy is split by the question being asked. For a VALUE the order is the one the
# reviews follow: PRIMARY PUBLICATION -> SUPPLEMENT / SAP / PROTOCOL -> REGISTRY. The registry
# keeps precedence on pre-specification, where its argument holds.
#
# `rank` above is deliberately left untouched. Nothing outside this module indexes it
# (measured), it is the documented ordering of the tier TABLE, and silently redefining a
# published number is the substitution class this project audits for. These functions are the
# operative order; the table is prose.

#: For "what is the effect on this outcome?" -- strongest first.
EFFECT_VALUE_ORDER = (
    "JOURNAL_FULL_TEXT",
    "JOURNAL_SUPPLEMENT",
    "STATISTICAL_ANALYSIS_PLAN",
    "TRIAL_PROTOCOL",
    "REGISTRY_POSTED_RESULT",
    "JOURNAL_ABSTRACT",
    "PRIOR_SYNTHESIS",
)

#: For "was this outcome pre-specified, and in what form?" -- strongest first. Here the
#: deposited-under-duty argument is the correct one and the registry keeps precedence.
PRESPECIFICATION_ORDER = (
    "STATISTICAL_ANALYSIS_PLAN",
    "TRIAL_PROTOCOL",
    "REGISTRY_POSTED_RESULT",
    "JOURNAL_FULL_TEXT",
    "JOURNAL_SUPPLEMENT",
    "JOURNAL_ABSTRACT",
)

QUESTIONS = {"effect_value": EFFECT_VALUE_ORDER,
             "prespecification": PRESPECIFICATION_ORDER}


def outranks(tier_a, tier_b, question="effect_value"):
    """Does `tier_a` outrank `tier_b` for this question?

    Raises on an unknown question rather than defaulting, because a silent default is how
    the two questions came to share one number in the first place.
    """
    if question not in QUESTIONS:
        raise ValueError("unknown question %r; the questions are %s -- a source hierarchy is "
                         "only meaningful relative to one" % (question, sorted(QUESTIONS)))
    order = QUESTIONS[question]
    if tier_a not in order or tier_b not in order:
        return False        # a tier outside the order (REGISTRY_REFERENCE_ROW) outranks nothing
    return order.index(tier_a) < order.index(tier_b)


def best_source(tiers, question="effect_value"):
    """The strongest of `tiers` for this question, or None if none of them are ranked."""
    order = QUESTIONS[question]
    ranked = [t for t in tiers if t in order]
    return min(ranked, key=order.index) if ranked else None


# ===========================================================================================
# REGISTRY SILENCE IS NOT ABSENCE
# ===========================================================================================
#
# `hasResults=false` is a fact about ClinicalTrials.gov. Reading it as "this trial has no
# results" is the membership error this module's header already names, and it is the one that
# removes published trials from reviews. A disposition resting on it must say which
# NON-REGISTRY source was checked and came back empty.

#: Fields whose presence shows a non-registry source was actually consulted.
NON_REGISTRY_EVIDENCE = ("pmid", "doi", "publication_checked", "full_text_checked",
                         "supplement_checked", "search_for_publication")

_REGISTRY_SILENCE = re.compile(r"hasResults\s*=\s*false|no resultsSection", re.I)
_ABSENCE_WORDS = re.compile(
    r"no results (exist|are available|were published)|has no results|"
    r"there is nothing to extract|is not published", re.I)


def registry_silence_problems(disposition):
    """Problems with a disposition that reads registry silence as absence of results.

    `disposition` carries at least a `reason` string, and optionally the fields recording
    what else was checked. Returns [] when the disposition is sound -- including the common
    and CORRECT case where it cites registry silence and does not convert it into absence.
    """
    blob = "%s %s" % (disposition.get("reason") or "", disposition.get("field_read") or "")
    if not _REGISTRY_SILENCE.search(blob):
        return []
    if not _ABSENCE_WORDS.search(blob):
        return []
    if [f for f in NON_REGISTRY_EVIDENCE if disposition.get(f)]:
        return []
    return ["This disposition reads registry silence as an absence of RESULTS and records no "
            "non-registry source that was checked. `hasResults=false` is evidence about the "
            "registry. Record which of %s was consulted, or state what was actually observed: "
            "the registry has posted nothing." % (", ".join(NON_REGISTRY_EVIDENCE),)]


def validate(record):
    """Return a list of problems with a value's provenance block. Empty list means valid.

    THREE STATES, NEVER TWO. `NOT_YET_RECORDED` (nobody looked), `COULD_NOT_DETERMINE`
    (someone looked and failed), and a real tier. Collapsing the first two would turn the
    backlog invisible, which is how 133 untraced numbers came to look like a corpus with
    provenance.
    """
    p = record.get("provenance")
    if p is None:
        return ["no `provenance` block"]
    if isinstance(p, str):
        # THE CORPUS ALREADY USES THIS KEY, AS A SENTENCE. 43 estimates carry strings like
        # "REGISTRY -- ClinicalTrials.gov posted results". That is real information and it is
        # NOT a tier: it names a source in prose, with no accessed date, no locator, and no
        # way for a reader to tell a posted results table from a background citation.
        #
        # It gets its own state rather than being crashed on, silently accepted, or promoted.
        # Promoting it would be the exact defect this schema exists to prevent -- a string
        # containing the word "registry" is not evidence that the number came from a posted
        # results table, and 43 rows would have been upgraded on a substring match.
        return ["`provenance` is a legacy STRING (%r). It names a source in prose and "
                "declares no tier. Migrate it to a tier block; do NOT infer the tier from "
                "the words in the string." % p[:60]]
    if not isinstance(p, dict):
        return ["`provenance` is a %s; expected a block with a `tier`" % type(p).__name__]
    tier = p.get("tier")
    if tier is None:
        return ["`provenance.tier` absent"]
    if tier == UNSET:
        return []
    if tier not in TIERS:
        return ["unknown tier %r -- tiers are a closed set; add it to TIERS with a rank and a "
                "reason rather than inventing one at a call site" % tier]
    spec = TIERS[tier]
    missing = [f for f in spec["requires"] if not str(p.get(f) or "").strip()]
    out = ["tier %s requires %r and it is empty" % (tier, f) for f in missing]
    if tier == "DERIVED_HERE":
        its = p.get("input_tiers") or []
        if not isinstance(its, (list, tuple)) or not its:
            out.append("DERIVED_HERE must list `input_tiers`; a derived value whose inputs are "
                       "untiered is itself untiered")
        else:
            bad = [t for t in its if t not in TIERS or t in ("DERIVED_HERE",)]
            if bad:
                out.append("DERIVED_HERE `input_tiers` contains %r, which is not a source tier"
                           % bad)
    if spec.get("never_counts_as_evidence") and record.get("point") is not None:
        out.append("tier %s carries a stored `point`. A registry reference row is a POINTER, "
                   "not a result -- open the cited paper, confirm it reports THIS trial, and "
                   "record the tier of what you actually read." % tier)
    return out
