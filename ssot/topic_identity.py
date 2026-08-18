"""Is the topic drug IN this trial, and in which role? Identity, never display text.

WHY THIS EXISTS. The search-side arm-role classifier matched the topic drug against arm
LABELS. NCT02789917 -- `APixaban vs. PhenpRocoumon: APPROACH-ACS-AF` -- labels its arms:

    EXPERIMENTAL       'Dual therapy (incl. NOAC)'    ['Other: Dual Therapy']
    ACTIVE_COMPARATOR  'Triple therapy (incl. VKA)'   ['Other: Triple Therapy']

"apixaban" appears nowhere except the title. The classifier scored it `not_eligible_other`
and the candidate SILENTLY DISAPPEARED from the reconciliation queue. That is the same
label-keying defect fixed object-side, still live on the search side -- and it failed in
the withholding direction, which has no guard.

TWO RULES, both learned the hard way.

1. THE ANSWER TO "I CANNOT FIND THE DRUG" IS NOT_ASSESSABLE, NEVER not_eligible.
   A trial we cannot classify was being reported as a trial we had excluded. That single
   substitution is the whole defect.

2. DRUG IDENTITY NEEDS A DECLARED SYNONYM SET, NOT A FUZZY MATCH. Registries name drugs by
   development code, brand and molecule interchangeably -- LY3819253 is bamlanivimab,
   MEDI8897 is nirsevimab, LCZ696 is sacubitril/valsartan, V114 is Prevnar-15. `otherNames`
   resolved only 3 of 10 in the identifier work, so it cannot be relied on. Every topic
   declares its own set here, enumerated and inspectable, and anything not on the list does
   not match. Same discipline as the estimand synonym map: enumerate what is safe, refuse
   what is not, never interpolate.
"""

EXPERIMENTAL = "experimental"
COMPARATOR = "comparator"
BACKGROUND = "background_or_coadministered"
NOT_ASSESSABLE = "not_assessable"
NOT_ELIGIBLE = "not_eligible_other"

# Declared per-topic identity sets. Molecule, brand, development code, and the regimen
# wording a registry may use INSTEAD of the drug name.
TOPIC_SYNONYMS = {
    "apixaban": ["apixaban", "eliquis", "bms-562247", "bms 562247",
                 # NCT02789917 names neither -- its arms say only this:
                 "noac", "doac", "dual therapy", "direct oral anticoagulant"],
    "catheter ablation": ["catheter ablation", "ablation", "pulmonary vein isolation", "pvi",
                          "cryoballoon", "radiofrequency ablation", "rfca", "wide area circumferential"],
    "alirocumab": ["alirocumab", "praluent", "sar236553", "sar 236553", "regn727", "regn 727"],
    "tafamidis OR acoramidis": ["tafamidis", "vyndaqel", "vyndamax", "fx-1006a", "fx 1006a",
                                "pf-06291826", "acoramidis", "ag10", "ag-10", "attruby"],
    "azilsartan": ["azilsartan", "edarbi", "edarbyclor", "tak-491", "tak 491",
                   "tak-536", "tak 536", "azilsartan medoxomil"],
    "bempedoic acid": ["bempedoic acid", "bempedoic", "nexletol", "nilemdo",
                       "etc-1002", "etc 1002", "esp15228"],
    "bococizumab": ["bococizumab", "pf-04950615", "pf 04950615", "rn316", "rn-316"],
    "bosentan": ["bosentan", "tracleer", "ro 47-0203", "ro47-0203"],
    # A CLASS TOPIC, ENUMERATED AS MOLECULES. The topic is "SGLT2 inhibitors", but searching
    # or matching on the class name is the error `lessons.md` records under CT.gov queries:
    # registries name the drug, not the class. So the class is expanded here into its members
    # plus their brands and development codes, and the class strings are ALSO listed because
    # a minority of records genuinely label an arm "SGLT2 inhibitor" with no molecule named --
    # in which case the arm is located but the molecule is not, and that is a real state.
    "sglt2 inhibitors": ["dapagliflozin", "forxiga", "farxiga", "bms-512148",
                         "empagliflozin", "jardiance", "bi 10773", "bi-10773",
                         "sotagliflozin", "zynquista", "inpefa", "lx4211", "lx-4211",
                         "canagliflozin", "invokana", "jnj-28431754",
                         "ertugliflozin", "steglatro", "pf-04971729", "mk-8835",
                         "sglt2 inhibitor", "sglt-2 inhibitor",
                         "sodium-glucose cotransporter 2", "sodium glucose cotransporter 2"],
}

# Codes carried in from the identifier work. Kept here so the general lesson stays visible
# even for topics not in this batch: a registry may name ONLY the code.
KNOWN_DEVELOPMENT_CODES = {
    "ly3819253": "bamlanivimab",
    "medi8897": "nirsevimab",
    "lcz696": "sacubitril/valsartan",
    "v114": "pneumococcal 15-valent conjugate vaccine",
    "mk-0616": "enlicitide",
    "aln-ttrsc02": "vutrisiran",
    "alxn2060": "acoramidis",
}


def synonyms_for(topic_key):
    """Declared set for a topic. KeyError is deliberate -- an undeclared topic must not
    silently fall back to matching its own bare name."""
    return [s.lower() for s in TOPIC_SYNONYMS[topic_key]]


def _hay(*parts):
    return " ".join(str(p or "") for p in parts).lower()


def locate(study, syns):
    """WHAT EXACTLY WAS RANDOMISED? -- not "where does the topic drug appear".

    THE QUESTION WAS REFRAMED 2026-08-19 AND TWO DEFECTS DISSOLVED UNDER IT.

    Asked as "where does the drug appear", this function got both of these wrong:

      BOTH ARMS      EASi-HF randomises vicadrostat/empagliflozin against placebo/empagliflozin.
                     Empagliflozin appears in an EXPERIMENTAL arm, so it was scored
                     `experimental` -- but it is given to everyone and the randomised contrast
                     is vicadrostat. 7 of 43 trials on sglt2-hf, a 16% overcount in the ADDING
                     direction, on exactly the add-on designs that dominate modern cardiology.

      ONE ARM ONLY   NCT03794518 randomises "Pioglitazone Plus dapagliflozin" against placebo.
                     The drug appears in the experimental arm and IS part of the contrast --
                     but so is pioglitazone, absent from the control arm, so the estimate is
                     not attributable to the SGLT2 inhibitor.

    These look like opposite problems and are one question: **what is the difference between
    the arms?** A drug in both arms is background and is not that difference; a second active
    agent in one arm only is part of that difference and contaminates it. Both dissolve when
    the assessor asks what was randomised rather than where a name occurs.

    Reads the INTERVENTION LIST and the registration's own name records -- never the arm label
    alone, and never a placebo's DESCRIPTION (see the control-arm test below).

    Returns (role, evidence). Role is NOT_ASSESSABLE when the drug cannot be located in any
    eligible field, which is a different state from having been excluded.
    """
    ps = study.get("protocolSection") or {}
    ai = ps.get("armsInterventionsModule") or {}
    idm = ps.get("identificationModule") or {}
    arms = ai.get("armGroups") or []
    intrs = ai.get("interventions") or []

    # Eligible identity fields, in priority order.
    title_blob = _hay(idm.get("briefTitle"), idm.get("officialTitle"),
                      (idm.get("orgStudyIdInfo") or {}).get("id"))
    intr_index = {}
    for i in intrs:
        blob = _hay(i.get("name"), " ".join(i.get("otherNames") or []), i.get("description"))
        intr_index[str(i.get("name") or "")] = blob

    def matches(blob):
        return any(s in blob for s in syns)

    # 1. Which arms carry an intervention whose NAME/otherNames/description matches?
    hit_types, hit_ev = [], []
    for a in arms:
        arm_intr_blobs = [intr_index.get(str(n).split(":")[-1].strip(), "")
                          for n in (a.get("interventionNames") or [])]
        arm_intr_blobs += [intr_index.get(str(n), "") for n in (a.get("interventionNames") or [])]
        blob = _hay(a.get("description"), *arm_intr_blobs)
        if matches(blob):
            hit_types.append(str(a.get("type") or "").upper())
            hit_ev.append(f"arm {a.get('label')!r} via intervention record")

    # 2. Fall back to the arm label ONLY as corroboration, and say so.
    if not hit_types:
        for a in arms:
            if matches(_hay(a.get("label"))):
                hit_types.append(str(a.get("type") or "").upper())
                hit_ev.append(f"arm {a.get('label')!r} via LABEL (weak evidence)")

    if hit_types:
        # A DRUG IN **BOTH** ARMS IS BACKGROUND, NOT THE INTERVENTION.
        #
        # Found 2026-08-19 screening sglt2-hf's remainder. EASi-HF Preserved (NCT06424288) and
        # EASi-HF Reduced (NCT06935370) randomise:
        #     EXPERIMENTAL        vicadrostat/empagliflozin
        #     PLACEBO_COMPARATOR  placebo/empagliflozin
        # Empagliflozin is given to EVERYONE. The randomised contrast is VICADROSTAT. But
        # empagliflozin appears in an arm typed EXPERIMENTAL, so this function returned
        # `experimental` and both trials entered the cascade as SGLT2 trials.
        #
        # APPEARING IN THE EXPERIMENTAL ARM IS NOT THE SAME AS BEING THE RANDOMISED CONTRAST.
        # The BACKGROUND state already existed but was only reachable when the drug was tied to
        # NO arm; the commoner case -- tied to EVERY arm -- fell through to `experimental`.
        # That inflates k on exactly the modern add-on trials where the topic drug is standard
        # therapy in both groups, and it does so in the direction that ADDS trials.
        # THE CONTROL-ARM TEST READS INTERVENTION **NAMES**, NEVER DESCRIPTIONS.
        #
        # A first version tested the same blob used above, and broke the base case: DAPA-HF's
        # control arm carries `Drug: Placebo` whose DESCRIPTION reads "Placebo matching
        # dapagliflozin", so the drug name appears in the control arm's text and DAPA-HF was
        # reclassified as background. DELIVER likewise. The matching-placebo convention names
        # the active drug in every placebo description in the registry, so description text
        # cannot answer "is the drug in this arm".
        #
        # What separates the two cases cleanly is WHICH INTERVENTION IS ATTACHED TO THE ARM:
        #   DAPA-HF   control interventionNames = ['Drug: Placebo']        -> drug NOT in arm
        #   EASi-HF   control interventionNames = ['Drug: empagliflozin',
        #                                          'Drug: placebo']        -> drug IS in arm
        # So the control-arm hit requires an intervention whose NAME matches, attached to that
        # arm. Same discipline as everywhere else tonight: read the coded relation, not the prose.
        def _drug_named_in_arm(a):
            for n in (a.get("interventionNames") or []):
                nm = str(n).split(":", 1)[-1].strip().lower()
                if any(s in nm for s in syns):
                    return True
            return False

        ctrl_arms = [a for a in arms
                     if any(k in str(a.get("type") or "").upper()
                            for k in ("COMPARATOR", "PLACEBO", "SHAM", "NO_INTERVENTION"))]
        exp_hit = "EXPERIMENTAL" in hit_types
        ctrl_hit = any(_drug_named_in_arm(a) for a in ctrl_arms)
        if exp_hit and ctrl_hit:
            return BACKGROUND, (
                "present in BOTH an experimental and a control arm, so it is background "
                "therapy and NOT the randomised contrast; " + "; ".join(hit_ev[:2]))
        if exp_hit:
            return EXPERIMENTAL, "; ".join(hit_ev[:2])
        if any("COMPARATOR" in t for t in hit_types):
            return COMPARATOR, "; ".join(hit_ev[:2])
        return BACKGROUND, "; ".join(hit_ev[:2])

    # 3. Named in the intervention list but tied to no arm -> background.
    if any(matches(b) for b in intr_index.values()):
        return BACKGROUND, "named in interventions, tied to no arm"

    # 4. Named ONLY in the title/registration record. NCT02789917 is exactly this case.
    if matches(title_blob):
        if not arms:
            return NOT_ASSESSABLE, "named in the registration title; no armGroups to assign a role"
        types = [str(a.get("type") or "").upper() for a in arms]
        if "EXPERIMENTAL" in types:
            return (EXPERIMENTAL,
                    "named in the registration TITLE only; arms are labelled by regimen, "
                    "and the EXPERIMENTAL arm is taken as the topic arm")
        return NOT_ASSESSABLE, "named in the registration title; arm roles do not identify it"

    # 5. Genuinely not found anywhere eligible.
    return NOT_ASSESSABLE, ("topic drug not located in interventions, arms, or registration "
                            "title. NOT the same as excluded -- we could not classify it.")
