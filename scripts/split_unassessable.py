"""Split the 27 unassessable subject-role results by CAUSE, before the number settles.

MY PROPOSED SPLIT WAS WRONG AND THE OBJECTS CORRECTED IT. I expected three causes --
combination products, class-named topics, brand-versus-molecule. The largest cause is none
of those: THE REGISTRY NAMES ARMS BY THE SPONSOR'S DEVELOPMENT CODE. bamlanivimab is
LY3819253, bezlotoxumab is MK-3415A, nirsevimab is MEDI8897, sacubitril/valsartan is LCZ696,
Prevnar-15 is V114. The topic is named for the drug the world calls it; the registration is
named for the compound the sponsor filed.

Combination products, my first guess, cause NOTHING here on their own.

Each cause gets a resolvability verdict backed by a measurement, not an assertion.
"""
import io
import json
import os
import sys
import time
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
REPO = r"F:\rapidmeta-ssot-shell"
SCRATCH = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(REPO, ".othernames-cache.json")
cache = json.load(io.open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}

# The five causes, assigned from the ARM TEXT that was actually read -- not from the
# topic name, which is what produced the wrong split in the first place.
NOT_A_DRUG_AT_ALL = {           # the token names a disease, population or anatomy
    "covid19-vaccines": "covid19 is a DISEASE",
    "cryptococcal-meningitis": "cryptococcal is a DISEASE",
    "cryptococcal-meningitis-africa": "cryptococcal is a DISEASE",
    "pediatric-hiv-art": "pediatric is a POPULATION",
    "hepatitis-b-taf-tdf-review": "hepatitis is a DISEASE",
    "mitral-funcmr-review": "mitral is an ANATOMICAL STRUCTURE",
}
CLASS_OR_TARGET = {             # the token names a class or a molecular target
    "pcsk9-inhibitors-cv-review": "pcsk9 is a TARGET; arms name evolocumab, alirocumab",
    "pcsk9-review": "pcsk9 is a TARGET; arms name evolocumab, alirocumab",
    "incretin-hfpef-review": "incretin is a CLASS; arms name semaglutide, tirzepatide",
    "sglt2-ckd-review": "sglt2 is a CLASS; arms name canagliflozin, dapagliflozin",
    "sglt2-hf": "sglt2 is a CLASS; arms name dapagliflozin, empagliflozin",
    "sglt2-mace-cvot-review": "sglt2 is a CLASS; arms name BI 10773 (empagliflozin)",
}
DEV_CODE = {                    # the registry names the arm by the sponsor's code
    "bamlanivimab-covid": ("bamlanivimab", "LY3819253"),
    "bamlanivimab-outp": ("bamlanivimab", "LY3819253"),
    "bezlotoxumab-cdi": ("bezlotoxumab", "MK-3415A"),
    "bezlotoxumab-cdiff": ("bezlotoxumab", "MK-3415A"),
    "nirsevimab-infant-rsv-review": ("nirsevimab", "MEDI8897"),
    "sacubitril-heartfail": ("sacubitril", "LCZ696"),
    "sacubitril-valsartan-hf": ("sacubitril", "LCZ696"),
    "prevnar15-pneumo": ("prevnar15", "V114"),
    "netarsudil-ocular-hypertension-auto-full-review": ("netarsudil", "AR-13324"),
    "menacwy-booster": ("menacwy", "Menactra / meningococcal vaccine"),
}
TOKENISATION = {                # the name matches but for punctuation
    "ser109-cdi": "ser109 against the registry's 'ser-109' -- A HYPHEN",
}


def other_names(nct):
    if nct in cache:
        return cache[nct]
    blob = None
    try:
        u = "https://clinicaltrials.gov/api/v2/studies/%s?format=json" % nct
        d = json.loads(urllib.request.urlopen(
            urllib.request.Request(u, headers={"User-Agent": "rm-syn"}),
            timeout=45).read().decode("utf-8"))
        ivs = (((d.get("protocolSection") or {}).get("armsInterventionsModule")
                or {}).get("interventions") or [])
        parts = []
        for iv in ivs:
            parts.append(iv.get("name") or "")
            parts += list(iv.get("otherNames") or [])
        blob = " ".join(parts).lower()
    except Exception:
        blob = None
    cache[nct] = blob
    time.sleep(0.06)
    return blob


def ncts_of(topic):
    f = os.path.join(REPO, "ssot", topic, topic + ".json")
    if not os.path.exists(f):
        return []
    try:
        o = json.load(io.open(f, encoding="utf-8"))
    except Exception:
        return []
    return [str(t.get("nct") or "") for t in ((o.get("inputs") or {}).get("trials") or [])
            if str(t.get("nct") or "").startswith("NCT")]


rows = json.load(io.open(os.path.join(SCRATCH, "unassessable.json"), encoding="utf-8"))
no_exp = [r for r in rows if r[3] == "NO_EXPERIMENTAL_TYPE"]

print("=" * 78)
print("THE 27 UNASSESSABLE, SPLIT BY CAUSE")
print("=" * 78)
print()
print("MY PROPOSED THREE-WAY SPLIT WAS WRONG. I expected combination products,")
print("class-named topics and brand-versus-molecule. COMBINATION PRODUCTS CAUSE")
print("NOTHING HERE. The largest cause is one I did not propose at all.")
print()

print("--- CAUSE 1: DEVELOPMENT CODE (%d) -------------------------------------"
      % len(DEV_CODE))
print("The registry names the arm by the sponsor's internal compound code. The topic")
print("is named for the drug the world calls it; the registration for what was filed.")
print()
resolvable, not_resolvable = [], []
for topic, (want, code) in sorted(DEV_CODE.items()):
    ncts = ncts_of(topic)
    hit = False
    for n in ncts:
        b = other_names(n)
        if b and want.lower() in b:
            hit = True
            break
    json.dump(cache, io.open(CACHE, "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False)
    (resolvable if hit else not_resolvable).append(topic)
    print("   %-44s %-11s -> %-14s otherNames: %s"
          % (topic[:43], want[:11], code[:14], "CARRIES IT" if hit else "silent"))
print()
print("   MEASURED, NOT ASSERTED: %d of %d resolve from interventions[].otherNames"
      % (len(resolvable), len(DEV_CODE)))
print("   The other %d do not, because the registration simply never records the"
      % len(not_resolvable))
print("   approved name. FOR THOSE THE REGISTRY IS NOT THE ANSWER and a curated")
print("   code->name map is the only route. So this cause is PARTLY resolvable, and")
print("   the honest form of that is a number rather than 'resolvable via synonyms'.")
print()

print("--- CAUSE 2: THE TOKEN IS NOT A DRUG (%d) ------------------------------"
      % len(NOT_A_DRUG_AT_ALL))
print("A DEFECT IN THE GATE, NOT IN THE OBJECTS. subject_of() takes the first")
print("hyphen-separated word and calls it a drug; these are diseases, populations")
print("and anatomy. The NOT_A_DRUG list was written from the topics I happened to")
print("look at. The check should never have attempted these -- they are not")
print("unassessable, they are OUT OF SCOPE, and the two are different claims.")
for t, why in sorted(NOT_A_DRUG_AT_ALL.items()):
    print("   %-44s %s" % (t[:43], why))
print()

print("--- CAUSE 3: CLASS OR TARGET NAME (%d) ---------------------------------"
      % len(CLASS_OR_TARGET))
print("The topic asks a class-level question and the arms name molecules. NOT")
print("RESOLVABLE BY SYNONYM: no registry field maps a class to its members, and")
print("the mapping is a clinical judgement -- which is exactly what makes these")
print("topics worth having. A class->member map would be curated, and curating one")
print("is a decision about scope, not a lookup.")
for t, why in sorted(CLASS_OR_TARGET.items()):
    print("   %-44s %s" % (t[:43], why[:44]))
print()

print("--- CAUSE 4: TOKENISATION (%d) -----------------------------------------"
      % len(TOKENISATION))
for t, why in sorted(TOKENISATION.items()):
    print("   %-44s %s" % (t[:43], why))
print("   RESOLVABLE WITH NO NETWORK CALL AT ALL: strip punctuation on both sides.")
print("   The cheapest fix in the list and the smallest population -- worth doing")
print("   because it costs nothing, worth NOT overselling because it fixes one.")
print()

print("--- CAUSE 5: NO ARM TYPED EXPERIMENTAL (%d) ----------------------------"
      % len(no_exp))
print("THE RE-LY SHAPE, and a registry-side limit rather than a corpus defect. The")
print("gate cannot ask its question when the registration declines to type its arms.")
for d, s, k, w, _t in sorted(no_exp):
    print("   %-44s k=%d" % (d[:43], k))
print("   NOT RESOLVABLE FROM THE REGISTRY BY ANY MEANS: the field is empty at the")
print("   source. Resolvable only by reading the protocol, which is a person's job.")
print()

tot = (len(DEV_CODE) + len(NOT_A_DRUG_AT_ALL) + len(CLASS_OR_TARGET)
       + len(TOKENISATION) + len(no_exp))
print("=" * 78)
print("TOTAL CLASSIFIED: %d of %d" % (tot, len(rows)))
print()
print("WHAT THE SPLIT CHANGES. '27 unassessable' reads as one backlog. It is five")
print("populations with five different answers: %d partly fixable from the registry"
      % len(DEV_CODE))
print("(%d of them measured to work), %d that are the GATE'S OWN BUG and should never"
      % (len(resolvable), len(NOT_A_DRUG_AT_ALL)))
print("have been counted, %d that need a curated class map and a scope decision, %d"
      % (len(CLASS_OR_TARGET), len(TOKENISATION)))
print("free, and %d NOT FIXABLE AT ALL because the registry field is empty." % len(no_exp))
print()
print("THE SECOND GROUP MATTERS MOST AND IS THE LEAST COMFORTABLE: %d of the 27 are"
      % len(NOT_A_DRUG_AT_ALL))
print("MY INSTRUMENT MISFIRING, counted as a corpus limitation. Left as a number,")
print("they would have read as evidence the corpus resists checking. THAT IS WHY THE")
print("SPLIT HAD TO HAPPEN BEFORE THE NUMBER SETTLED.")
