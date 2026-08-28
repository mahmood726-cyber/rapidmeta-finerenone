"""ONE authoritative reason for not pooling, and one function that reads it.

THE CONCEPT IS STORED UNDER SEVEN NAMES.

    on the outcome        not_poolable_reason        poolable_reason
    on outcome.pooled     withdrawn_reason           withdrawn_because
                          absent_reason              withdrawn_note      card_note
    elsewhere             handbook.conformance (a string, 224 occurrences)

THREE SURFACES ALREADY DISAGREE ABOUT PRECEDENCE, and each implemented its own:

    ssot/build_app_v2.py:1230      not_poolable_reason, then poolable_reason
    ssot/validate_v2.py:1007       requires not_poolable_reason
    outputs/_baseline_projector.py prefers withdrawn_reason in one documented case and
                                   poolable_reason in another, in a 30-line comment

That comment is the problem in miniature: the precedence is REASONED ABOUT IN PROSE, in one
file, and the two other readers never saw it. Two objects examined on 2026-08-28 carry only
`not_poolable_reason` and `poolable_reason` -- neither of which is in `field_aliases.py`'s
`withdrawal_reason` tuple, so the alias map that exists to stop exactly this did not cover the
two spellings actually in use.

WHAT IS DECLARED HERE, AND WHAT IS NOT.

DECLARED: one precedence, `AUTHORITATIVE`, derived from the only precedence anyone actually
implemented (build_app_v2's), and one reader, `not_pooled_reason()`. Every surface goes
through it. The rest become read-through aliases.

NOT DECLARED: a rename. `poolable_reason` populates 152 objects and `not_poolable_reason` 7;
unifying the data is 155 objects and it is Mahmood's decision, as `field_aliases.py` already
records for the other seven concepts. Making the READER single decides nothing and stops the
divergence being invisible.

THE NOTES ARE A DIFFERENT CONCEPT AND ARE NOT ALIASES. `withdrawn_note` and `card_note` are
elaborations that travel BESIDE the reason -- a note saying what a withdrawal does not
establish is not a competing answer to "why was this not pooled". Treating them as aliases
would manufacture 26 divergences that are not divergences. Kinds before counts.
"""
from __future__ import annotations

import re

# precedence, strongest first. The FIRST one holding a substantive value is what a reader gets.
AUTHORITATIVE = "not_poolable_reason"
ALIASES = ("not_poolable_reason", "poolable_reason", "withdrawn_reason", "absent_reason",
           "withdrawn_because")

# beside the reason, never instead of it
ANNOTATIONS = ("withdrawn_note", "card_note")

# a value that defers to another spelling rather than competing with it
_XREF = re.compile(r"\bsee\s+(%s)\b|\b(?:as per|same as|refer to|cf\.?)\s+(%s)\b"
                   % ("|".join(ALIASES), "|".join(ALIASES)), re.I)
_XREF_BARE = re.compile(r"^\s*(see|as per|per|cf\.?|same as|refer to)\b.{0,60}$", re.I)


def is_cross_reference(text):
    """"see poolable_reason" is the corpus pointing AT the authority, not contradicting it."""
    if not isinstance(text, str):
        return False
    return bool(_XREF.search(text) or _XREF_BARE.match(text.strip()))


def _sources(outcome):
    pooled = outcome.get("pooled") if isinstance(outcome.get("pooled"), dict) else {}
    return outcome, pooled


def spellings_present(outcome):
    """{spelling: value} for every alias holding a substantive value, in precedence order."""
    found = {}
    if not isinstance(outcome, dict):
        return found
    for name in ALIASES:
        for src in _sources(outcome):
            v = src.get(name)
            if isinstance(v, str) and v.strip():
                found.setdefault(name, v.strip())
    return found


def not_pooled_reason(outcome, default=None):
    """THE reader. Returns (value, spelling_it_came_from). Never guesses precedence locally."""
    found = spellings_present(outcome)
    for name in ALIASES:
        if name in found:
            return found[name], name
    return default, None


def annotations(outcome):
    out = {}
    if not isinstance(outcome, dict):
        return out
    for name in ANNOTATIONS:
        for src in _sources(outcome):
            v = src.get(name)
            if isinstance(v, str) and v.strip():
                out.setdefault(name, v.strip())
    return out


def _norm(s):
    return re.sub(r"\W+", " ", s.lower()).strip()


def divergence(outcome):
    """Classify what the several spellings on one outcome are doing.

    Returns (kind, {spelling: value}). Kinds, in the order they are tested:
        'none'            one spelling or none
        'cross-reference' the extra spelling points at another spelling
        'identical'       same text under two names
        'subset'          one is contained in the other -- a summary, not a contradiction
        'DIVERGENT'       two substantive answers that are not the same answer
    """
    found = spellings_present(outcome)
    if len(found) <= 1:
        return "none", found
    substantive = {k: v for k, v in found.items() if not is_cross_reference(v)}
    if len(substantive) <= 1:
        return "cross-reference", found
    norms = {k: _norm(v) for k, v in substantive.items()}
    uniq = set(norms.values())
    if len(uniq) == 1:
        return "identical", substantive
    ordered = sorted(uniq, key=len)
    if all(ordered[0] in u for u in ordered[1:]):
        return "subset", substantive
    return "DIVERGENT", substantive
