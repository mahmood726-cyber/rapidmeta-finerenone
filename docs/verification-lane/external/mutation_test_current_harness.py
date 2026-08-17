"""Mutation test of the CURRENT nafis_harness (34 tests / 15 detectors) against the
seven semantic mutants recorded in verdict_covid19-vaccines.txt for validate_v2.py.

Every mutant is a reader-visible value that is CONTRADICTED BY A STAGED PAYLOAD.
Ground-truth values are quoted verbatim from the verdict artefact.

validate_v2.py scored 0/7 (all seven SURVIVED -- "VALIDATOR CLEAN -- 21/21").

The current harness is a library of pure functions over dicts, not a file validator,
so each mutant is re-expressed as a detector input. That re-expression is a choice,
and the choice turns out to BE the result -- so it is made three ways:

  ARM A -- referent keyed correctly by field. The best case: the caller has
           extracted the right quantity from the source and keyed it.
  ARM B -- referent supplied as a flat number-bag, i.e. exactly the encoding
           validate_v2.py used (`_REVIEW_NUMBERS = {float(x) for x in re.findall(...)}`).
           This is the historical failure mode, not a strawman.
  ARM C -- referent keyed correctly but OMITTING the mutated field. Tests whether
           a missing referent key is a silent skip.

Kill = FAIL (defect detected). Survive = PASS. INVALID = run void, not a pass.
"""
import sys, json
sys.path.insert(0, r"/sessions/funny-great-rubin/mnt/local_758bb69d-9d15-47f1-b3a5-8b96047daeef--outputs")

from nafis_harness import build_registry, Verdict

reg = build_registry()
fitness = reg.self_test()
assert fitness["ok"], fitness["unfit"]

# ---------------------------------------------------------------------------
# Ground truth, verbatim from the staged payloads as recorded in the verdict file
# ---------------------------------------------------------------------------
TRUTH = {
    "reference_efficacy_percent":    91.1,    # review: "VE 91.10 (83.80 to 95.10)"
    "reference_ci_low_percent":      83.8,    # same string
    "reference_ci_high_percent":     95.1,    # same string
    "registry_enrolment":            33758,   # NCT04530396.ctgov.json "count": 33758
    "dosed":                         39540,   # NCT04652102.ctgov.json "value": "39540"
    "reference_analysis_population":  18695,  # PMC9726273 cochrane "18,695"
}
# Every numeric token that appears anywhere in the staged Cochrane XML / registry.
# This is what a document-wide regex number-set looks like. 95.1 and 18696 are in
# here for different reasons: 95.1 because it is the CI bound, 18696 because a
# 6-digit-plus corpus of this size contains almost any small integer somewhere.
NUMBER_BAG = {91.1, 83.8, 95.1, 18695, 19866, 39540, 39680, 33758, 21977,
              48.2, 31.7, 60.9, 78.1, 64.8, 86.3, 25463, 38206, 40382, 18696,
              33759, 39541, 12851, 12211, 14964, 4902, 13465, 13458}

MUTANTS = [
    # (n, label, field, mutated_value, detector, extra)
    (1, "reference_efficacy_percent 91.1 -> 95.1 (CI bound substituted for point estimate)",
     "reference_efficacy_percent", 95.1, "CHK005"),
    (2, "reference_ci_low/high swapped (83.8 <-> 95.1)",
     "reference_ci_low_percent", 95.1, "CHK005"),
    (5, "registry_enrolment 33758 -> 33759",
     "registry_enrolment", 33759, "CHK005"),
    (6, "dosed 39540 -> 39541",
     "dosed", 39541, "CHK005"),
    (7, "reference_analysis_population 18695 -> 18696",
     "reference_analysis_population", 18696, "CHK005"),
]

def run_chk005(row, ref, name="PMC9726273 Cochrane SoF / NCT04530396 registry"):
    return reg.run("CHK005_EXTERNAL_REFERENT",
                   {"referent_name": name, "row": row, "external_referent": ref})

results = {"A": {}, "B": {}, "C": {}}

for n, label, fld, bad, _det in MUTANTS:
    row = dict(TRUTH); row[fld] = bad
    if n == 2:  # the swap mutates two fields at once
        row["reference_ci_low_percent"] = 95.1
        row["reference_ci_high_percent"] = 83.8

    # ARM A -- correctly keyed referent
    results["A"][n] = (label, run_chk005(row, dict(TRUTH)))

    # ARM B -- flat number-bag referent (the validate_v2 encoding).
    # A bag has no field keys, so the only honest encoding is: for each row field,
    # assert only that its value appears somewhere in the bag.
    bag_ref = {k: (v if v in NUMBER_BAG else None) for k, v in row.items()}
    results["B"][n] = (label, run_chk005(row, bag_ref, "review-wide number set"))

    # ARM C -- correctly keyed referent, mutated field omitted
    partial = {k: v for k, v in TRUTH.items() if k != fld}
    if n == 2:
        partial.pop("reference_ci_high_percent", None)
    results["C"][n] = (label, run_chk005(row, partial))

# ---------------------------------------------------------------------------
# Mutants 3 and 4 -- identity. CHK006.
# ---------------------------------------------------------------------------
ident = {}
ident[3] = ("pmid 33545094 -> 99999999", reg.run("CHK006_IDENTITY_KEY", {
    "claimed_name": "Sputnik-V-phase3", "registration_id": "99999999",
    "source_document": "PMID33545094.pubmed.xml",
    "source_document_ids": ["33545094"],
    "registry_acronym": "Sputnik-V-phase3"}))
ident[4] = ("nct NCT04530396 -> NCT00000000", reg.run("CHK006_IDENTITY_KEY", {
    "claimed_name": "Sputnik-V-phase3", "registration_id": "NCT00000000",
    "source_document": "NCT04530396.ctgov.json",
    "source_document_ids": ["NCT04530396"],
    "registry_acronym": "Sputnik-V-phase3"}))
# and the off-by-one enrolment through CHK006's own enrolment path, for contrast
ident["5b"] = ("registry_enrolment 33758 -> 33759 via CHK006 enrolment-vs-weight",
    reg.run("CHK006_IDENTITY_KEY", {
        "claimed_name": "Sputnik-V-phase3", "registration_id": "NCT04530396",
        "source_document": "NCT04530396.ctgov.json",
        "source_document_ids": ["NCT04530396"],
        "registry_acronym": "Sputnik-V-phase3",
        "registry_enrolment": 33759, "row_weight": 33758}))

# ---------------------------------------------------------------------------
def verdict_of(r): return r.verdict.value
def killed(r):     return r.verdict is Verdict.FAIL

print("=" * 78)
print("MUTATION TEST -- current nafis_harness (34 tests / 15 detectors)")
print("baseline: validate_v2.py scored 0/7, all mutants SURVIVED")
print("=" * 78)

for arm, title in [("A", "ARM A -- external referent keyed correctly by field"),
                   ("B", "ARM B -- external referent as a flat number-bag (the validate_v2 encoding)"),
                   ("C", "ARM C -- referent keyed correctly but omitting the mutated field")]:
    print(f"\n{title}")
    print("-" * 78)
    k = 0
    for n in sorted(results[arm]):
        label, r = results[arm][n]
        v = verdict_of(r)
        mark = "KILLED " if killed(r) else ("SURVIVED" if v == "PASS" else "VOID    ")
        k += killed(r)
        print(f"  M{n}  [{mark}] {v:8s} {label[:60]}")
        if v != "FAIL":
            print(f"          reason: {r.reason[:150]}")
    print(f"  --> CHK005 mutants killed: {k}/{len(results[arm])}")

print("\nIDENTITY MUTANTS -- CHK006_IDENTITY_KEY")
print("-" * 78)
ik = 0
for n in [3, 4, "5b"]:
    label, r = ident[n]
    v = verdict_of(r)
    mark = "KILLED " if killed(r) else ("SURVIVED" if v == "PASS" else "VOID    ")
    if n in (3, 4): ik += killed(r)
    print(f"  M{n}  [{mark}] {v:8s} {label[:60]}")
    if v != "FAIL":
        print(f"          reason: {r.reason[:200]}")
print(f"  --> identity mutants killed: {ik}/2")

print("\n" + "=" * 78)
totalA = sum(killed(r) for _, r in results["A"].values()) + ik
totalB = sum(killed(r) for _, r in results["B"].values()) + ik
totalC = sum(killed(r) for _, r in results["C"].values()) + ik
print(f"HEADLINE  ARM A (referent keyed correctly):   {totalA}/7")
print(f"          ARM B (referent as number-bag):     {totalB}/7")
print(f"          ARM C (referent key omitted):       {totalC}/7")
print(f"          validate_v2.py baseline:            0/7")
print("=" * 78)
