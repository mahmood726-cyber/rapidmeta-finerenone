"""Does a trial STUDY the drug a topic is about? The three judgements, importable and tested.

Extracted from `scripts/add_topic_autodiscover.py` on 2026-08-25 so it can be tested without
an AACT snapshot. That script reads AACT at import time, so nothing inside it could be
exercised on a machine without one -- which is this machine, and which is why the matcher
defect survived a corpus-wide sweep of its own output.

THE DEFECT THIS EXISTS TO PREVENT. A sweep of 139 delivered pages found 29 carrying a trial
that does not study the page's subject: 42 trial records, 18 ABSENT, 23 COMPARATOR, 1
BACKGROUND. The matcher's rule was `pattern in " | ".join(all_intervention_names)`. That
single substring test cannot make three distinctions, and each one produced real mismatches:

  COMBINATION   "cefepime" is inside "cefepime/VNRX-5133" (taniborbactam) and inside
                "amoxicillin-clavulanate" for "amoxicillin". A combination is a DIFFERENT
                DRUG from its components, not a member of them.

  COMPARATOR    AACT's interventions table lists EVERY arm. RAMBLE is "Rivaroxaban vs
                Apixaban"; an apixaban topic matches it, and apixaban is the control.

  BACKGROUND    TWILIGHT gives ticagrelor to EVERY participant and randomises aspirin on top.
                A P2Y12 topic matches it, and the trial answers an aspirin question.

UNKNOWN IS NOT NO. Where arm roles are unavailable the answer is that the role could not be
determined, and the caller must not read that as "not experimental". Reading unknown as no
would silently drop real trials -- the opposite failure, and the worse one, because a missing
trial leaves no trace on the page while a wrong one at least looks odd to a reader.
"""
import re

_WS = re.compile(r"[^a-z0-9]+")

# What separates two active agents inside one intervention name. The lookaround on the
# hyphen keeps "VNRX-5133" and "AAI-101" whole -- a code name is one agent, not two.
_COMBO_JOIN = re.compile(r"[/+]|\s+(?:plus|and|with)\s+|(?<=[a-z])-(?=[a-z])")


def norm(s):
    return _WS.sub(" ", (s or "").lower()).strip()


def is_combination_of(pattern, intervention_name):
    """True where the intervention is a COMBINATION that merely CONTAINS the pattern.

    "cefepime"            vs "cefepime/VNRX-5133"        -> True   different drug
    "cefepime tazobactam" vs "cefepime/VNRX-5133"        -> False  pattern names a combo too
    "amoxicillin"         vs "amoxicillin-clavulanate"   -> True
    "apixaban"            vs "apixaban"                  -> False  plain match
    """
    np_, ni = norm(pattern), norm(intervention_name)
    if not np_ or np_ == ni or np_ not in ni:
        return False
    parts = [x for x in (p.strip() for p in _COMBO_JOIN.split(intervention_name.lower())) if x]
    if len(parts) < 2:
        return False
    if len([x for x in (p.strip() for p in _COMBO_JOIN.split(pattern.lower())) if x]) > 1:
        return False
    return any(norm(x) == np_ for x in parts)


def studies_subject(drug_patterns, all_interventions, experimental_interventions=None):
    """(ok, reason).

    all_interventions          every intervention name on the trial, any arm.
    experimental_interventions names in EXPERIMENTAL arms, or None where roles are unknown.
    """
    pats = [p for p in (drug_patterns or []) if norm(p)]
    known_roles = experimental_interventions is not None
    pool = experimental_interventions if known_roles else all_interventions

    for p in pats:
        for nm in (pool or []):
            if norm(p) in norm(nm) and not is_combination_of(p, nm):
                return True, "experimental intervention %r" % nm

    # It did not match where it counts. Say WHICH of the three reasons applies, because the
    # three call for different remedies -- rematch, drop the arm, or withdraw the claim.
    for p in pats:
        for nm in (all_interventions or []):
            if norm(p) in norm(nm):
                if is_combination_of(p, nm):
                    return False, "matches only as a component of the combination %r" % nm
                if known_roles:
                    return False, "matches only outside the experimental arm (%r)" % nm
                return False, "matches %r but arm roles are unknown" % nm
    return False, "no intervention matches the drug pattern"
