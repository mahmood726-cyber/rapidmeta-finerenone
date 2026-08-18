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
    """Where does the topic drug appear? Reads the INTERVENTION LIST and the registration's
    own name records -- never the arm label alone.

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
        if "EXPERIMENTAL" in hit_types:
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
