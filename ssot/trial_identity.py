"""Does a trial STUDY the drug a topic is about? Decided from registered ARM STRUCTURE.

Extracted from `scripts/add_topic_autodiscover.py` on 2026-08-25 so it can be tested without
an AACT snapshot — that script reads AACT at import time, and this machine has none, which is
why a matcher defect survived a corpus-wide sweep of its own output.

THE DEFECT. A sweep of 139 delivered pages found 29 carrying a trial that does not study the
page's subject: 42 trial records. The matcher's rule was `pattern in " | ".join(names)` over
every intervention on the trial. One substring test, three judgements it cannot make.

REGISTRY INTERVENTIONS DESCRIBE WHAT WAS GIVEN, NOT WHICH ARM WAS EXPERIMENTAL. That single
sentence is why the first version of this module was wrong, and the rules below are built
from the arm structure of five real registrations rather than from what a drug list implies.

  NCT02270242  TWILIGHT      ACTIVE_COMPARATOR  Aspirin + Ticagrelor
                             PLACEBO_COMPARATOR Placebo + Ticagrelor
        Ticagrelor is in BOTH arms. The randomised contrast is aspirin against placebo, so
        a P2Y12 topic that matches this trial has matched an aspirin question. The tell is
        not an arm TYPE -- it is that the drug appears in EVERY arm.

  NCT02829957  RAMBLE        ACTIVE_COMPARATOR  Rivaroxaban
                             ACTIVE_COMPARATOR  Apixaban
        NEITHER arm is EXPERIMENTAL. A rule requiring an EXPERIMENTAL arm would reject this
        and every other head-to-head trial -- silently dropping real evidence, which is the
        worse failure because a missing trial leaves no trace on the page. Apixaban IS
        studied here. (RAMBLE still does not belong on an apixaban VTE page, because it
        measures menstrual blood loss -- but that is an OUTCOME judgement, not an identity
        one, and this module must not pretend to make it.)

  NCT03840148                EXPERIMENTAL       Cefepime/VNRX-5133 (taniborbactam)
  NCT03630081                EXPERIMENTAL       WCK 4282 (FEP-TAZ) 4 g
        Two different cefepime combinations. A bare "cefepime" pattern matches both and
        should match neither; "cefepime tazobactam" should match only the second, and only
        because WCK 4282 is carried as a synonym.

  NCT00391872  PLATO         EXPERIMENTAL       Ticagrelor
                             ACTIVE_COMPARATOR  Clopidogrel
        The ordinary case, which must keep passing.

UNKNOWN IS NOT NO. Where arm structure is unavailable the answer is that the role could not
be determined. Reading that as "not experimental" would drop real trials.
"""
import re

_WS = re.compile(r"[^a-z0-9]+")

# What separates two active agents inside one intervention name. The lookaround on the
# hyphen keeps "VNRX-5133" and "AAI-101" whole: a code name is one agent, not two.
_COMBO_JOIN = re.compile(r"[/+]|\s+(?:plus|and|with)\s+|(?<=[a-z])-(?=[a-z])")

# Arms that are not a treatment being studied.
_INERT_ARM = {"PLACEBO_COMPARATOR", "NO_INTERVENTION", "SHAM_COMPARATOR"}


# ClinicalTrials.gov prefixes each interventionName with its TYPE: "Drug: Apixaban",
# "Biological: ...", "Procedure: ...". The first version of the combination test compared
# "drug: cefepime" against "cefepime" and never matched, so a bare "cefepime" pattern was
# accepted against "Drug: Cefepime/VNRX-5133" -- the exact case the test exists to catch,
# passing because of a five-character prefix.
_TYPE_PREFIX = re.compile(
    r"^\s*(drug|biological|device|procedure|behavioral|dietary supplement|"
    r"radiation|genetic|combination product|diagnostic test|other)\s*:\s*", re.I)


def strip_type(name):
    return _TYPE_PREFIX.sub("", str(name or "")).strip()


def norm(s):
    return _WS.sub(" ", strip_type(s).lower()).strip()


def is_combination_of(pattern, intervention_name):
    """True where the intervention is a COMBINATION that merely CONTAINS the pattern.

    "cefepime"            vs "Cefepime/VNRX-5133"        -> True   a different drug
    "cefepime tazobactam" vs "Cefepime/VNRX-5133"        -> False  pattern names a combo too
    "amoxicillin"         vs "amoxicillin-clavulanate"   -> True
    "apixaban"            vs "Apixaban"                  -> False  plain match
    """
    np_, ni = norm(pattern), norm(intervention_name)
    if not np_ or np_ == ni or np_ not in ni:
        return False
    parts = [x for x in (p.strip() for p in
             _COMBO_JOIN.split(strip_type(intervention_name).lower())) if x]
    if len(parts) < 2:
        return False
    if len([x for x in (p.strip() for p in _COMBO_JOIN.split(pattern.lower())) if x]) > 1:
        return False
    return any(norm(x) == np_ for x in parts)


def _matches(pattern, name):
    return bool(norm(pattern)) and norm(pattern) in norm(name) \
        and not is_combination_of(pattern, name)


def studies_subject(drug_patterns, arm_groups):
    """(ok, reason).

    arm_groups -- [{"type": "EXPERIMENTAL", "interventionNames": [...]}, ...] exactly as
                  ClinicalTrials.gov API v2 returns under
                  protocolSection.armsInterventionsModule.armGroups.
                  None or [] means the arm structure is unknown.
    """
    pats = [p for p in (drug_patterns or []) if norm(p)]
    if not pats:
        return False, "no drug pattern supplied"
    if not arm_groups:
        return True, "arm structure unknown -- not judged, and NOT read as a rejection"

    arms = []
    for a in arm_groups:
        if not isinstance(a, dict):
            continue
        names = [str(n) for n in (a.get("interventionNames") or [])]
        arms.append(((a.get("type") or "").upper(), names))
    if not arms:
        return True, "arm structure unknown -- not judged, and NOT read as a rejection"

    hit_arms = [i for i, (_t, names) in enumerate(arms)
                if any(_matches(p, n) for p in pats for n in names)]

    if not hit_arms:
        for _t, names in arms:
            for n in names:
                for p in pats:
                    if norm(p) and norm(p) in norm(n) and is_combination_of(p, n):
                        return False, "matches only as a component of the combination %r" % n
        return False, "no arm's intervention matches the drug pattern"

    # BACKGROUND. Present in EVERY arm, so it is not what was randomised. TWILIGHT.
    if len(hit_arms) == len(arms) and len(arms) > 1:
        return False, ("present in all %d arms, so it is background therapy and not the "
                       "randomised contrast" % len(arms))

    # The drug is only in placebo/no-intervention/sham arms.
    if all(arms[i][0] in _INERT_ARM for i in hit_arms):
        return False, "appears only in a placebo or no-intervention arm"

    # HEAD-TO-HEAD. No arm is EXPERIMENTAL and the drug holds one of the active arms.
    # Requiring EXPERIMENTAL here would reject RAMBLE, PLATO's comparator side, and every
    # active-controlled trial registered without an experimental label.
    types = {t for t, _n in arms}
    if "EXPERIMENTAL" not in types:
        return True, "head-to-head: no experimental arm is declared and the drug holds an active arm"

    if any(arms[i][0] == "EXPERIMENTAL" for i in hit_arms):
        return True, "experimental arm"

    return False, ("appears only in the comparator arm while a different intervention holds "
                   "the experimental arm")
