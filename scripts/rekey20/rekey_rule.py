# -*- coding: utf-8 -*-
"""THE RULE. Stated once, applied mechanically to every topic.

  R1  SPLIT the title at the first CONDITION CONNECTIVE (" in ", " for ", " after ").
      Everything before it is the INTERVENTION SPAN; everything after it, truncated at
      the first terminator, is the CONDITION SPAN.
  R2  A token in the intervention span is a DRUG iff ChEMBL resolves it to a molecule
      with max_phase >= 1. The lexicon is the authority's, not mine.
  R3  A topic is DRUG-KEYED iff its intervention span holds exactly ONE drug.
  R4  RE-KEY: replace the drug with its class -- the molecule's USAN stem definition,
      split into phrases. Nothing else about the topic changes.

FAILURE STATES. Where the rule gives a clearly wrong answer for a topic, that is
RECORDED HERE AS A PROPERTY OF THE RULE. No topic is repaired by hand.

  F1_NO_CONDITION    title has no condition connective -- cannot be split
  F2_NO_DRUG         no drug in the intervention span (already class- or procedure-keyed)
  F3_MULTI_DRUG      two or more drugs (already a comparison- or class-shaped key)
  F4_NO_CLASS        the drug has no USAN stem -- the authority holds no class for it
  F5_MODALITY_CLASS  the stem names a MOLECULAR MODALITY, not a therapeutic class
  F6_CIRCULAR_CLASS  the class phrase contains the drug's own name -- re-keying is a no-op
"""
import re

COND_CONNECTIVES = (" in ", " for ", " after ")
COND_TERMINATORS = (":", ";", " -- ", " – ", ",", " versus ", " vs ", " against ",
                    " compared", " and ", "?")
COND_LEAD_STRIP = ("adults with ", "adult ", "patients with ", "people with ",
                   "participants with ", "children with ", "the ", "an ", "a ",
                   "chronic ", "acute ", "established ", "prevention of ")

STOP = set("""a an the of in for with and or to on at by from versus vs against alone
plus added its own each what is are was were be been effect effects patients people
adults adult children participants trial trials study studies review reviews placebo
usual care control inactive standard three four five six seven eight nine ten one two
across after before during between within than more less high low dose doses therapy
therapies treatment treatments group groups arm arms outcome outcomes primary secondary
""".split())

# Declared BEFORE the twenty were drawn. A general clinical-abbreviation table, not one
# fitted to the sample.
ABBREV = {
    "pah": "pulmonary arterial hypertension", "ph": "pulmonary hypertension",
    "af": "atrial fibrillation", "hf": "heart failure",
    "hfref": "heart failure reduced ejection fraction",
    "hfpef": "heart failure preserved ejection fraction",
    "vte": "venous thromboembolism", "acs": "acute coronary syndrome",
    "pci": "percutaneous coronary intervention", "cad": "coronary artery disease",
    "hofh": "homozygous familial hypercholesterolaemia",
    "hefh": "heterozygous familial hypercholesterolaemia",
    "ascvd": "atherosclerotic cardiovascular disease", "cvd": "cardiovascular disease",
    "ldl": "low density lipoprotein", "psvt": "paroxysmal supraventricular tachycardia",
    "svt": "supraventricular tachycardia", "hcm": "hypertrophic cardiomyopathy",
    "ohcm": "obstructive hypertrophic cardiomyopathy", "bp": "blood pressure",
    "mr": "mitral regurgitation", "attr": "transthyretin amyloid",
    "cm": "cardiomyopathy", "mi": "myocardial infarction",
}

# Symmetric spelling normalisation. Applied to BOTH sides, so it cannot bias either arm.
# British forms INSERT a vowel (haemoglobin > hemoglobin), so the rewrite drops the
# inserted vowel rather than swapping one for another.
_SPELL = ((r"ha?em", "hem"), (r"isch(a)?em", "ischem"), (r"a?emia", "emia"),
          (r"a?emic", "emic"), (r"o?edema", "edema"), (r"aemat", "emat"),
          (r"olaemia", "olemia"), (r"lipidaemia", "lipidemia"),
          (r"terolaemia", "terolemia"), (r"ae", "e"))


def norm(text):
    t = (text or "").lower()
    for pat, rep in _SPELL:
        t = re.sub(pat, rep, t)
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return " " + " ".join(_stem(w) for w in t.split()) + " "


def _stem(w):
    return w[:-1] if len(w) > 4 and w.endswith("s") and not w.endswith("ss") else w


def split_title(title):
    """-> (intervention_span, condition_span or None)"""
    low = " " + (title or "") + " "
    pos, conn = None, None
    for c in COND_CONNECTIVES:
        i = low.lower().find(c)
        if i >= 0 and (pos is None or i < pos):
            pos, conn = i, c
    if pos is None:
        return (title or "").strip(), None
    inter = low[:pos].strip()
    cond = low[pos + len(conn):]
    cut = len(cond)
    for t in COND_TERMINATORS:
        j = cond.lower().find(t)
        if j >= 0:
            cut = min(cut, j)
    cond = cond[:cut].strip()
    changed = True
    while changed:
        changed = False
        for lead in COND_LEAD_STRIP:
            if cond.lower().startswith(lead):
                cond, changed = cond[len(lead):].strip(), True
    return inter, (cond or None)


def condition_terms(cond_span):
    """content words of the condition, abbreviations expanded, stemmed."""
    out = []
    for w in re.sub(r"[^a-zA-Z0-9]+", " ", cond_span or "").lower().split():
        if w in ABBREV:
            out.extend(norm(ABBREV[w]).split())
        elif w not in STOP and len(w) > 2:
            out.append(_stem(re.sub(r"[^a-z0-9]", "", norm(w).strip())))
    seen, uniq = set(), []
    for w in out:
        if w and w not in seen:
            seen.add(w)
            uniq.append(w)
    return uniq


def class_phrases(stem_def):
    """USAN stem definition -> match phrases. Each phrase contributes itself and, if it
    has 3+ words, its final two-word suffix -- Cochrane writes 'factor Xa inhibitors'
    where USAN writes 'blood coagulation factor XA inhibitors'."""
    if not stem_def:
        return []
    out = []
    # AMENDMENT 2 (before the scan, see RULE-AMENDMENT.md): split on parentheses too, and
    # drop a trailing "<exemplar> type" qualifier. USAN writes the class as
    # "beta-blockers (propranolol type)" and "thrombin inhibitors argatroban type"; the
    # exemplar is a naming convention, not part of the class name, and leaving it glued on
    # made the phrase unmatchable against every Cochrane title that uses the class.
    for part in re.split(r"[,:;()]| or ", stem_def):
        p = norm(part).strip()
        if not p:
            continue
        out.append(p)
        w = p.split()
        if len(w) >= 2 and w[-1] == "type":
            out.append(" ".join(w[:-2]) if len(w) > 2 else "")
        if len(w) >= 3:
            out.append(" ".join(w[-2:]))
    seen, uniq = set(), []
    for p in out:
        if p and p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq


def contains(hay_norm, term_norm):
    """whole-token-sequence containment in normalised space."""
    return (" " + term_norm.strip() + " ") in hay_norm


def class_terms_for_drug(drug_record):
    """THE ONE PLACE a drug becomes class terms. -> (phrases, failure_state or None).

    R4 plus its three refusals, in one function, so build_pool.py and scan.py cannot
    disagree about what the rule yields. They previously did: build_pool applied the
    F4/F5/F6 gating and froze the result, while scan read that frozen list -- so moving
    scan to compute live would have silently started scoring the modality classes the
    rule rejects. One source has to mean the WHOLE rule, not just the splitter.
    """
    d = drug_record or {}
    sd = d.get("usan_stem_definition")
    if not sd:
        return [], "F4_NO_CLASS"
    if d.get("class_is_modality"):
        return [], "F5_MODALITY_CLASS"
    ph = class_phrases(sd)
    dn = norm(d.get("pref_name") or "").strip()
    if dn and any(dn in p for p in ph):
        return [], "F6_CIRCULAR_CLASS"
    return ph, None


# ---------------------------------------------------------------------------
# RULE FINGERPRINT -- the structural fix for: AN INSTRUMENT CERTIFIED IN ONE
# CONFIGURATION AND RUN IN ANOTHER.
#
# WHAT WENT WRONG. Amendment 2 changed `class_phrases`. scan.py had TWO SOURCES for
# one rule: its controls called class_phrases() LIVE and got the amended splitter,
# while the twenty read class_phrases FROZEN into twenty.json at draw time, before
# the amendment. The positive control therefore certified a splitter the twenty
# never used -- so it was not measuring the twenty at all.
#
# WHY A HASH AND NOT A CONVENTION. "Remember to redraw after amending the rule" is a
# convention, and the next amendment breaks it silently. This makes the drift
# MECHANICALLY DETECTABLE: the fingerprint is the rule's OUTPUT over a fixed probe,
# so any change to norm(), class_phrases() or the probe changes it. An artefact
# records the fingerprint it was built under; a consumer recomputes it and REFUSES
# on mismatch rather than scoring stale terms.
#
# The probe is fixed here, beside the rule, and deliberately includes the exact
# shapes Amendment 2 was about -- a parenthetical qualifier and a trailing
# "<exemplar> type" -- so an un-propagated amendment cannot fingerprint identical.
FINGERPRINT_PROBE = (
    "beta-blockers (propranolol type)",
    "thrombin inhibitors argatroban type",
    "coronary vasodilators verapamil type",
    "endothelin receptor antagonists",
    "antithrombotics, blood coagulation factor XA inhibitors",
    "heparin derivatives and low molecular weight or depolymerized heparins",
    "enzyme inhibitors: antihyperlipidemics (HMG-CoA inhibitors)",
    "monoclonal antibodies: fully human",
    "warfarin analogs",
)


def rule_fingerprint():
    """sha256 over the rule's OUTPUT for a fixed probe. Changes iff the rule changes."""
    import hashlib
    h = hashlib.sha256()
    for s in FINGERPRINT_PROBE:
        h.update(s.encode("utf-8"))
        h.update(b"\x1f")
        h.update("|".join(class_phrases(s)).encode("utf-8"))
        h.update(b"\x1e")
        h.update(norm(s).encode("utf-8"))
        h.update(b"\x1d")
    return h.hexdigest()


def assert_fingerprint(recorded, artefact_path, gate):
    """REFUSE if an artefact was built under a different rule than the one now loaded.

    Refusal names the offending artefact first, the rule second, the gate third.
    """
    live = rule_fingerprint()
    if recorded is None:
        raise SystemExit(
            "%s\n  rule: the artefact records no rule_fingerprint, so there is no way to "
            "show it was built by the rule now loaded. An artefact whose provenance cannot "
            "be checked may not be scored\n  found by: %s" % (artefact_path, gate))
    if recorded != live:
        raise SystemExit(
            "%s\n  rule: built under rule_fingerprint %s, but the rule now loaded "
            "fingerprints %s. The artefact carries terms from a DIFFERENT version of the "
            "rule; scoring it would certify one configuration and measure another. "
            "Rebuild the artefact\n  found by: %s"
            % (artefact_path, recorded[:16], live[:16], gate))
    return live
