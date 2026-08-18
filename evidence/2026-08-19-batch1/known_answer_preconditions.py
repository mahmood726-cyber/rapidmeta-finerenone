"""Known-answer test for the seven preconditions AND for the five detectors that gate them.

Run BEFORE any verdict from these seven is trusted. Two parts, and part A matters as much as
part B: the four defective assessors of 2026-08-18 were all caught mechanically and NONE of
them by review, so a detector that has not been shown to REJECT is not evidence of anything.

PART A -- each detector is handed the exact defect it was written to catch, and must refuse.
PART B -- each precondition is handed an instance whose answer is already known.

Every PART B case pins an answer that was got WRONG once, by this project, in a way that
mattered:
  * `arms: []` scored FAIL -- "no data" reported as "the data is wrong".
  * `{"role": ""}` counted as a non-matching value rather than an unreadable field (agy D1).
  * `Placebo Q2W` vs `Placebo` scored as different comparators.
  * a 2x2 factorial rejected outright by an arm-count test (AUGUSTUS NCT02415400).
"""
import sys

sys.path.insert(0, "F:/rapidmeta-ssot-shell/ssot")

from assessment import FAIL, NOT_ASSESSABLE, PASS
from assessor_registry import AssessorRejected, Registry, UnitMismatch

import preconditions as P

fails = []


def check(name, got, expected):
    ok = got == expected
    if not ok:
        fails.append(f"{name}: got {got!r} expected {expected!r}")
    print(f"[{'ok ' if ok else 'MISS'}] {name}: {got}")
    return ok


def rejects(name, thunk, exc=AssessorRejected):
    try:
        thunk()
    except exc as e:
        print(f"[ok ] {name}: REFUSED -- {str(e)[:95]}")
        return True
    except Exception as e:                                   # noqa: BLE001
        fails.append(f"{name}: wrong exception {type(e).__name__}: {e}")
        print(f"[MISS] {name}: wrong exception {type(e).__name__}")
        return False
    fails.append(f"{name}: did NOT refuse")
    print(f"[MISS] {name}: did NOT refuse -- the detector is not a detector")
    return False


print("=" * 78)
print("PART A -- the detectors must REJECT. A check that can only pass is not a check.")
print("=" * 78)

# DETECTOR 1: two assessors over one path set (the `subject_role` defect).
r1 = Registry()
r1.register("first", lambda o: (PASS, "x"), ["screening.eligibility"])
rejects("D1 duplicate path set",
        lambda: r1.register("second", lambda o: (PASS, "y"), ["screening.eligibility"]))

# DETECTOR 2: normalise-then-compare without text_match (the `comparator` defect).
def _raw_text_equality(obj):
    labels = [str(a).lower() for a in obj.get("arms", [])]
    return (PASS, "x") if len(set(labels)) == 1 else (FAIL, "y")

rejects("D2 raw text equality",
        lambda: Registry().register("bad_text", _raw_text_equality, ["arms"]))

# DETECTOR 5: declared unit is not the unit iterated (the grand-total-vs-per-tab error).
def _wrong_unit(obj):
    return (PASS, f"{len([x for x in obj.get('outcomes', [])])}")

rejects("D5 unit mismatch",
        lambda: Registry().register("bad_unit", _wrong_unit, ["outcomes"],
                                    unit="trial", unit_source="trials"),
        UnitMismatch)

# THE PRECONDITION GATE: no named Handbook section -> does not register.
rejects("gate: unnamed authority",
        lambda: P.register_precondition("nameless", ["some.path"], handbook_section=""))

# DETECTOR 3 is exercised in PART B via a polymorphic field; DETECTOR 4 runs after the sweep.

print()
print("=" * 78)
print("PART B -- each precondition against an instance whose answer is already known.")
print("=" * 78)

# --- 1. population_stated ---------------------------------------------------------------
check("1 population: stated",
      P.population_stated({"question": "Does tafamidis reduce mortality in ATTR-CM?"})[0], PASS)
check("1 population: DECLARED absent -> FAIL",
      P.population_stated({"question": "not recorded on the page this object was built from"})[0],
      FAIL)
check("1 population: silent -> NOT_ASSESSABLE",
      P.population_stated({})[0], NOT_ASSESSABLE)

# --- 2. arm_role_resolved ---------------------------------------------------------------
GOOD_TRIALS = {"inputs": {"trials": [
    {"nct": "NCT01994889", "arms": [{"role": "experimental"}, {"role": "placebo"}]}]}}
check("2 arm_role: roles readable",
      P.arm_role_resolved(GOOD_TRIALS)[0], PASS)
# THE 2026-08-18 BUG: `arms: []` was scored FAIL. It is absence, not a wrong role.
check("2 arm_role: arms:[] -> NOT_ASSESSABLE (was FAIL, the defect)",
      P.arm_role_resolved({"inputs": {"trials": [{"nct": "NCT1", "arms": []}]}})[0],
      NOT_ASSESSABLE)
# agy's D1 case: a blank role is an unreadable field, not the value "no role".
check("2 arm_role: {'role': ''} -> NOT_ASSESSABLE (agy D1)",
      P.arm_role_resolved(
          {"inputs": {"trials": [{"nct": "NCT2", "arms": [{"role": ""}]}]}})[0],
      NOT_ASSESSABLE)
check("2 arm_role: no inputs at all -> NOT_ASSESSABLE",
      P.arm_role_resolved({})[0], NOT_ASSESSABLE)

# --- 3. comparator_identified -----------------------------------------------------------
# THE COMPARATOR ARTIFACT: a schedule is not part of a comparator's identity.
check("3 comparator: 'Placebo Q2W' == 'Placebo' -> PASS (was FAIL, the defect)",
      P.comparator_identified({"outcomes": [{"id": "a", "comparator": "Placebo Q2W"},
                                            {"id": "b", "comparator": "Placebo"}]})[0], PASS)
# ...and normalisation must NOT collapse genuinely different comparators.
check("3 comparator: warfarin vs aspirin -> FAIL",
      P.comparator_identified({"outcomes": [{"id": "a", "comparator": "warfarin"},
                                            {"id": "b", "comparator": "aspirin"}]})[0], FAIL)
check("3 comparator: unnamed -> NOT_ASSESSABLE",
      P.comparator_identified({"outcomes": [{"id": "a"}]})[0], NOT_ASSESSABLE)

# --- 4. estimand_named ------------------------------------------------------------------
check("4 estimand: named",
      P.estimand_named({"outcomes": [{"id": "a", "estimand": "all-cause mortality"}]})[0], PASS)
check("4 estimand: definition only still names a quantity",
      P.estimand_named({"outcomes": [{"id": "a", "definition": "death from any cause"}]})[0],
      PASS)
check("4 estimand: silent -> NOT_ASSESSABLE",
      P.estimand_named({"outcomes": [{"id": "a"}]})[0], NOT_ASSESSABLE)

# --- 5. inclusion_criteria_auditable ----------------------------------------------------
check("5 auditable: DECLARED not recorded -> FAIL",
      P.inclusion_criteria_auditable(
          {"screening": {"eligibility": "not recorded on the page this object was built from"}})[0],
      FAIL)
check("5 auditable: no screening key -> NOT_ASSESSABLE",
      P.inclusion_criteria_auditable({})[0], NOT_ASSESSABLE)
check("5 auditable: real criteria -> PASS",
      P.inclusion_criteria_auditable(
          {"screening": {"eligibility": "Adults with wild-type or variant ATTR-CM, NYHA I-III"}})[0],
      PASS)

# --- 6. eligibility_met -----------------------------------------------------------------
# Always NOT_ASSESSABLE from JSON, and the three reasons must be DIFFERENT.
e_silent = P.eligibility_met({})
e_nosrc = P.eligibility_met({"screening": {"eligibility": "Adults with ATTR-CM"}})
e_src = P.eligibility_met({"screening": {"eligibility": "Adults with ATTR-CM"},
                           "sources": {"pmid": "30145929"}})
check("6 eligibility: criteria silent", e_silent[0], NOT_ASSESSABLE)
check("6 eligibility: criteria stated, no sources", e_nosrc[0], NOT_ASSESSABLE)
check("6 eligibility: criteria + sources, no full text read", e_src[0], NOT_ASSESSABLE)
check("6 eligibility: three DISTINCT reasons, not one repeated",
      len({e_silent[1], e_nosrc[1], e_src[1]}), 3)
# It must NOT be a byte-identical copy of precondition 5 -- that was `subject_role`.
check("6 eligibility: differs from precondition 5 on the same input",
      P.eligibility_met({"screening": {"eligibility": "Adults with ATTR-CM"}})[0]
      != P.inclusion_criteria_auditable({"screening": {"eligibility": "Adults with ATTR-CM"}})[0],
      True)

# --- 7. one_randomised_comparison -------------------------------------------------------
check("7 design: 1 exp vs 1 control -> PASS",
      P.one_randomised_comparison(GOOD_TRIALS)[0], PASS)
# AUGUSTUS-shaped 2x2 factorial: 2 topic x 2 control = 4 candidates. NOT ineligible.
AUGUSTUS = {"inputs": {"trials": [{"nct": "NCT02415400", "arms": [
    {"role": "experimental"}, {"role": "experimental"},
    {"role": "active_comparator"}, {"role": "placebo"}]}]}}
aug = P.one_randomised_comparison(AUGUSTUS)
check("7 design: 2x2 factorial -> FAIL naming candidates (NOT rejected as ineligible)",
      aug[0], FAIL)
check("7 design: the factorial reason NAMES the trial and the count",
      "NCT02415400(4)" in aug[1], True)
# An uncontrolled extension: all arms are the drug. Zero comparisons -- a different FAIL.
ext = P.one_randomised_comparison(
    {"inputs": {"trials": [{"nct": "NCT00477594",
                            "arms": [{"role": "experimental"}, {"role": "experimental"}]}]}})
check("7 design: uncontrolled extension -> FAIL", ext[0], FAIL)
check("7 design: extension reason is DIFFERENT from the factorial reason",
      ext[1] != aug[1], True)
check("7 design: blank roles -> NOT_ASSESSABLE",
      P.one_randomised_comparison(
          {"inputs": {"trials": [{"nct": "NCT3", "arms": [{"role": ""}]}]}})[0], NOT_ASSESSABLE)

# --- DETECTOR 4: no two of the seven may be byte-identical across a real object set ------
print()
print("=" * 78)
print("DETECTOR 4 -- two assessors byte-identical across every object is a duplicate check.")
print("=" * 78)
PROBES = {
    "stated_and_complete": {
        "question": "Does tafamidis reduce mortality in ATTR-CM?",
        "screening": {"eligibility": "Adults with wild-type or variant ATTR-CM"},
        "sources": {"pmid": "30145929"},
        "outcomes": [{"id": "primary", "comparator": "Placebo", "estimand": "all-cause mortality"}],
        "inputs": {"trials": [{"nct": "NCT01994889",
                               "arms": [{"role": "experimental"}, {"role": "placebo"}]}]}},
    "declared_absent": {
        "question": "not recorded",
        "screening": {"eligibility": "not recorded on the page this object was built from"},
        "outcomes": [{"id": "primary", "comparator": "warfarin"},
                     {"id": "second", "comparator": "aspirin"}],
        "inputs": {"trials": [{"nct": "NCT1", "arms": []}]}},
    "silent": {},
}
results, alarms = P.REGISTRY.run(PROBES)
for a in alarms:
    fails.append(f"D4 alarm: {a}")
    print(f"[MISS] {a}")
if not alarms:
    print(f"[ok ] no two of the seven agree across all {len(PROBES)} probe objects")

print()
print("=" * 78)
check("AUTHORITY stays fail-closed", P.verdict_is_publishable(), False)
print("=" * 78)
if fails:
    print(f"FAILURES ({len(fails)}):")
    for f in fails:
        print(f"  - {f}")
else:
    print("ALL KNOWN ANSWERS REPRODUCED. Detectors reject; preconditions agree with what we knew.")
sys.exit(1 if fails else 0)
