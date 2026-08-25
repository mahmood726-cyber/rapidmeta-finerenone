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
        Two different cefepime combinations. "cefepime tazobactam" must match only the
        second -- the partners differ, tazobactam is not taniborbactam. A BARE "cefepime"
        specifies no partner and matches both, which is correct behaviour for that pattern
        and means CEFEPIME_TAZ's real defect is in TOPICS: it supplies the pattern
        "cefepime" for a topic whose drug is cefepime-tazobactam.

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


def _agents(name):
    """The active agents inside one intervention name, type prefix removed."""
    return [x for x in (p.strip() for p in _COMBO_JOIN.split(strip_type(name).lower())) if x]


def _pattern_agents(pattern):
    """Agents in a TOPIC PATTERN, which also uses a bare space as a combination separator.

    TOPICS writes combinations as "cefepime tazobactam" -- no slash, no plus. `_agents` reads
    that as ONE agent, so the conflict test returned False and the taniborbactam case, the
    original defect, passed. Patterns are therefore split on whitespace as well.

    This is safe only because `conflicting_combination` independently requires the TRIAL side
    to have two or more agents. A procedure pattern like "catheter ablation" does split into
    two tokens here, but it can only reach a conflict verdict against a trial that is itself a
    combination AND shares one of those tokens as a whole agent, which does not occur.
    """
    out = []
    for part in _agents(pattern):
        out.extend([w for w in part.split() if w])
    return out


def conflicting_combination(pattern, intervention_name):
    """True only where the pattern names a combination whose PARTNER differs from the trial's.

    THE FIRST VERSION OF THIS REJECTED ANY COMBINATION CONTAINING THE PATTERN, and it was
    built from one exemplar -- cefepime against "Cefepime/VNRX-5133". Run over the corpus it
    rejected 9 of the 12 combination cases WRONGLY, and each wrong rejection would have
    deleted real evidence:

        sacubitril    vs "Sacubitril/valsartan"      ARNI's own drug
        ceftolozane   vs "Ceftolozane/tazobactam"    ceftolozane is only marketed this way
        casirivimab   vs "casirivimab+imdevimab"     casirivimab is only given with imdevimab
        delamanid     vs "Delamanid + OBR"           OBR is background, delamanid is the drug
        apixaban      vs "Apixaban + Placebo"        a placebo of the other agent
        bosentan      vs "Duo-Therapy with Sildenafil"   on a page ABOUT combination therapy

    A combination containing the subject drug IS a trial of that drug. The drug is being
    given and the trial is measuring what it does.

    What is NOT a trial of the subject is a combination with a DIFFERENT PARTNER from the one
    the topic specifies. "cefepime tazobactam" against "Cefepime/VNRX-5133" is a conflict:
    both name a partner and the partners differ -- tazobactam is not taniborbactam. A bare
    "cefepime" specifies no partner and therefore conflicts with nothing.

    That distinction explains all twelve cases, where "any combination is a different drug"
    explained one.
    """
    pat_agents = _pattern_agents(pattern)
    if len(pat_agents) < 2:
        return False                      # no partner specified -- nothing to conflict with
    trial_agents = _agents(intervention_name)
    if len(trial_agents) < 2:
        return False
    shared = [a for a in pat_agents if any(norm(a) == norm(b) for b in trial_agents)]
    if not shared:
        return False                      # not the same drug family at all
    # Same head agent, different partner set -> a different combination.
    pat_rest = [a for a in pat_agents if not any(norm(a) == norm(s2) for s2 in shared)]
    trial_rest = [a for a in trial_agents if not any(norm(a) == norm(s2) for s2 in shared)]
    if not pat_rest or not trial_rest:
        return False
    return not any(norm(a) == norm(b) for a in pat_rest for b in trial_rest)


def matches_as_component(pattern, intervention_name):
    """The pattern appears inside a combination name (whether or not that is a problem)."""
    np_, ni = norm(pattern), norm(intervention_name)
    if not np_ or np_ == ni or np_ not in ni:
        return False
    return len(_agents(intervention_name)) > 1


# AN INTERVENTION NAMED AFTER THE DRUG IT MIMICS IS NOT THE DRUG.
#
# This is the single most dangerous thing in this module and it was missing. Registries name
# placebos after their target:
#
#     "Drug: Placebo (for alirocumab)"        NCT01507831
#     "Drug: Apixaban-matching placebo"       NCT00423319, a double-dummy design
#     "Biological: Bococizumab 150mg placebo" NCT02458287
#
# A substring match counts those as the drug being present. In a double-dummy trial the drug
# then appears in EVERY arm, and the background-therapy rule fires -- so the rule reported
# that alirocumab is background therapy in its own pivotal trials. Six pages were about to be
# escalated to "a wrong trial contributes to a published estimate", which would have been a
# false accusation of the most serious kind we have.
#
# Caught because 6 of 6 ALIROCUMAB trials coming back as background is not a finding, it is a
# statement about the instrument.
#
# WRITTEN BY BUILDING THE ESCAPE FROM A CHARACTER CODE, NOT TYPED THROUGH A HEREDOC.
# The first version of this line went in through a shell heredoc and its word-boundary
# escapes arrived as literal BACKSPACE BYTES -- r"<BS>placebo<BS>|..." -- which matches
# nothing. is_placebo_name then returned False for "Drug: Placebo (for alirocumab)", the
# placebo exclusion did nothing, and the six false accusations this was written to remove
# survived the fix meant to remove them. Invisible in an editor view; visible only to
# `cat -A`. This exact failure is in the operating rules as "never write a regex through a
# heredoc -- use the editor", and it still happened.
_PLACEBO_NAME = re.compile(
    r"\bplacebo\b|\bdummy\b|\bsham\b|matching placebo|placebo[- ]matching", re.I)


def is_placebo_name(name):
    return bool(_PLACEBO_NAME.search(strip_type(name)))


def _matches(pattern, name):
    """The pattern names this intervention: not a placebo of it, not a conflicting combo."""
    if is_placebo_name(name):
        return False
    if not norm(pattern) or norm(pattern) not in norm(name):
        return False
    return not conflicting_combination(pattern, name)

def studies_subject(drug_patterns, arm_groups):
    """(ok, reason) where ok is True, False, or NONE for undecidable.

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
        # THE CONFLICT CHECK MUST NOT REQUIRE SUBSTRING CONTAINMENT.
        #
        # A topic pattern writes a combination with a SPACE ("cefepime tazobactam"); the
        # registry writes it with a slash ("Cefepime/VNRX-5133"). Neither contains the other
        # as a substring, so gating the conflict test on `norm(p) in norm(n)` meant the
        # original defect -- the case this whole module exists for -- came back UNDECIDABLE.
        # `conflicting_combination` already decides on shared and differing AGENTS, so it is
        # asked directly.
        for _t, names in arms:
            for n in names:
                if is_placebo_name(n):
                    continue
                for p in pats:
                    if conflicting_combination(p, n):
                        return False, ("the topic names a different combination: %r"
                                       % strip_type(n))
        # NO ARM NAME MATCHES IS NOT "NOT STUDIED". It is "this method cannot tell".
        #
        # Arm names are PARAPHRASES. NCT00643188's experimental arm is
        # "Procedure: Radiofrequency ablation" and the topic pattern is "catheter ablation"
        # -- the same thing in different words. NCT01420393 names its arms by STRATEGY
        # ("Rhythm control") rather than by what is done. Drug arms carry brand names, code
        # names and formulations. A string match over arm names decides identity only when
        # the arm happens to name the drug the way the topic does.
        #
        # Returning False here produced 92 "not studied" verdicts on a 420-record corpus --
        # an implausible proportion, which is always a statement about the instrument. Each
        # one would have accused a page of naming a trial that does not study its subject,
        # on the evidence that two strings differ.
        #
        # This is the "unknown is not no" rule one level deeper, and it costs coverage
        # rather than correctness: the three failure modes this module CAN decide --
        # background in every arm, comparator-only, conflicting combination -- all require a
        # name match first, so they are unaffected.
        return None, ("no arm name matches the pattern, and arm names are paraphrases -- "
                      "this method cannot decide identity for this trial")

    # BACKGROUND. Present in EVERY arm, so it is not what was randomised. TWILIGHT.
    if len(hit_arms) == len(arms) and len(arms) > 1:
        return False, ("present in all %d arms, so it is background therapy and not the "
                       "randomised contrast" % len(arms))

    # ARM TYPE IS NOT RELIABLE for this. HOPE-3 (NCT00468923) registers its REAL
    # rosuvastatin arm as PLACEBO_COMPARATOR -- a 2x2 factorial labelled from the other
    # factor's point of view. Keying on the type accused rosuvastatin of appearing only in a
    # placebo arm of its own trial. `_matches` already excludes placebo-NAMED interventions,
    # which is the check that actually works, so a name that survived it is a real
    # administration of the drug whatever the arm is labelled.

    # HEAD-TO-HEAD. No arm is EXPERIMENTAL and the drug holds one of the active arms.
    # Requiring EXPERIMENTAL here would reject RAMBLE, PLATO's comparator side, and every
    # active-controlled trial registered without an experimental label.
    types = {t for t, _n in arms}
    if "EXPERIMENTAL" not in types:
        return True, "head-to-head: no experimental arm is declared and the drug holds an active arm"

    if any(arms[i][0] == "EXPERIMENTAL" for i in hit_arms):
        return True, "experimental arm"

    # COMPARATOR-ONLY IS NOT DECIDABLE FROM THE ARM TYPE LABEL, because the label lies.
    #
    #   NCT00423319  EXPERIMENTAL       Enoxaparin + Apixaban-matching placebo
    #                ACTIVE_COMPARATOR  Apixaban + Enoxaparin-matching placebo
    #   The title is "Study of an Investigational Drug for the Prevention of
    #   Thromboembolism" and the investigational drug is APIXABAN -- registered in the arm
    #   labelled ACTIVE_COMPARATOR.
    #
    #   NCT00468923  HOPE-3 registers its real rosuvastatin arm as PLACEBO_COMPARATOR,
    #   labelling a 2x2 factorial from the other factor's point of view.
    #
    # Two registrations, two different ways the label fails to say which drug is under test.
    # PLATO labels it correctly, so the field is right sometimes -- which is worse than
    # always wrong, because it invites exactly this kind of rule.
    #
    # So this returns UNDECIDABLE. It costs 16 verdicts and keeps the one class that needs no
    # label at all: a drug present in EVERY arm is background therapy whatever the arms are
    # called. Accusing a page on a field that is demonstrably unreliable is how a wrong number
    # gets onto a page and becomes the reader's problem.
    return None, ("the drug is in a non-experimental arm, but registry arm-type labels are "
                  "not reliable enough to call this -- see NCT00423319 and NCT00468923")
