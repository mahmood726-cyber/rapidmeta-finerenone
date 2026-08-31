# -*- coding: utf-8 -*-
"""PLANTS FOR THE TWO SEED GUARDS ADDED 2026-08-31. Every arm separately, each with a
clean sibling that must NOT fire.

The two guards are:
  G1  a term that is ENTIRELY schedule tokens is not a drug name  (`Q2W`, `QM`, `BID`)
  G2  a term appearing in BOTH a treatment and a control arm label is ROLE-AMBIGUOUS

⛔ A GUARD THAT ONLY EVER FIRES IS NOT A GUARD. Each plant below is paired with a sibling
that differs in exactly the thing the guard keys on, and the sibling must come out CLEAN.
Without the sibling, `strip everything in parentheses` and `flag every arm term` would both
pass every plant here.

⭐ AND EACH GUARD ALSO GETS A LIVE-CORPUS POSITIVE -- the real object that produced the
defect -- so the detector is proven on the corpus and not only on fixtures. A gate proven on
fixtures and never run on its corpus is this project's own recorded failure.
"""
import io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
from search_topic import (_strip_dose, _all_schedule, arm_role_conflicts,
                          intervention_terms, seed_role_state)

ROOT = "F:/rapidmeta-ssot-shell"
LIVE = os.path.join(ROOT, "ssot/evolocumab-mixed-dyslipidemia-auto-full-review/"
                          "evolocumab-mixed-dyslipidemia-auto-full-review.json")
CLEAN_LIVE = os.path.join(ROOT, "ssot/colchicine-cvd-review/colchicine-cvd-review.json")

results = []


def check(tag, ok, detail):
    results.append((tag, ok, detail))
    print("   %-52s %-4s %s" % (tag, "PASS" if ok else "FAIL", detail))


def obj(trials):
    return {"inputs": {"trials": trials}}


print("=== G1  SCHEDULE TOKENS -- plant and clean sibling ===")
got = _strip_dose("Atorvastatin (Q2W)")
check("G1 plant: 'Atorvastatin (Q2W)' loses the schedule",
      got == ["Atorvastatin"], "-> %r" % (got,))
got = _strip_dose("Evolocumab 420 mg QM")
check("G1 plant: 'Evolocumab 420 mg QM' -> the drug alone",
      got == ["Evolocumab"], "-> %r" % (got,))
# ⭐ THE SIBLING. If the guard were 'drop every parenthetical' both plants above would still
# pass and this would fail. It is the only assertion that separates the two rules.
got = _strip_dose("Metoprolol (extended release)")
check("G1 clean sibling: a NON-schedule parenthetical survives",
      "extended release" in got, "-> %r" % (got,))
got = _strip_dose("LCZ696 (sacubitril/valsartan) 200 mg twice daily")
check("G1 clean sibling: an alphanumeric drug code is untouched",
      "LCZ696" in got and "sacubitril/valsartan" in got, "-> %r" % (got,))
# ⚠️ `all([])` is True. Without the `bool(words) and` guard an empty term would classify as
# 'entirely schedule' and the branch would be dead for the case it exists to catch.
check("G1 vacuity: _all_schedule('') is False, not True",
      _all_schedule("") is False, "the all([]) trap, asserted rather than assumed")
check("G1 vacuity sibling: _all_schedule('Q2W') is True",
      _all_schedule("Q2W") is True, "the guard still fires on a real schedule token")

print("")
print("=== G2  ROLE AMBIGUITY -- plant and clean sibling ===")
plant = obj([{"id": "NCTPLANT", "arms": [
    {"role": "treatment", "label": "Atorvastatin (Q2W)"},
    {"role": "control", "label": "Evolocumab QM + Atorvastatin"}]}])
got = [c["term"] for c in arm_role_conflicts(plant)]
check("G2 plant: a term in BOTH roles is named",
      got == ["atorvastatin"], "-> %r" % (got,))
sib = obj([{"id": "NCTCLEAN", "arms": [
    {"role": "treatment", "label": "Evolocumab 420 mg QM"},
    {"role": "control", "label": "Placebo Q2W"}]}])
got = [c["term"] for c in arm_role_conflicts(sib)]
check("G2 clean sibling: correct roles produce NO conflict",
      got == [], "-> %r" % (got,))
# A second sibling: the same two drugs, roles NOT overlapping. If the detector keyed on
# 'two drugs are present' rather than on 'one drug is in both roles', this would fire.
sib2 = obj([{"id": "NCT2", "arms": [
    {"role": "treatment", "label": "Evolocumab 420 mg"},
    {"role": "control", "label": "Atorvastatin 80 mg"}]}])
got = [c["term"] for c in arm_role_conflicts(sib2)]
check("G2 clean sibling: two drugs, one role each, still clean",
      got == [], "-> %r" % (got,))

print("")
print("=== G3  PLACEBO-LABELLED CONTROLS -- plant and clean sibling ===")
# ⛔ THIS ARM EXISTS BECAUSE A LIVE-CORPUS PLANT FAILED AND THE DETECTOR WAS RIGHT.
# My assertion said colchicine-cvd-review must be clean; it returned
# ['colchicine','stent','synergy']. `colchicine placebo` is a CONTROL LABEL THAT NAMES THE
# DRUG -- excludable. `SYNERGY Stent` is in both arms because it really is in both arms --
# not excludable, and correctly still reported. Two innocent causes, only one mechanical.
pl = obj([{"id": "NCTPL", "arms": [
    {"role": "treatment", "label": "colchicine"},
    {"role": "control", "label": "colchicine placebo"}]}])
got = [c["term"] for c in arm_role_conflicts(pl)]
check("G3 plant: a placebo control naming the drug is NOT a conflict",
      got == [], "-> %r" % (got,))
nopl = obj([{"id": "NCTNOPL", "arms": [
    {"role": "treatment", "label": "colchicine"},
    {"role": "control", "label": "colchicine low dose"}]}])
got = [c["term"] for c in arm_role_conflicts(nopl)]
check("G3 clean sibling: a NON-placebo control naming the drug IS a conflict",
      got == ["colchicine"], "-> %r  -- the exclusion keys on the placebo marker, not on "
                             "the drug appearing twice" % (got,))

print("")
print("=== LIVE-CORPUS POSITIVES -- the detector run on the corpus, not only on fixtures ===")
o = json.load(io.open(LIVE, encoding="utf-8"))
state, conflicts, terms = seed_role_state(o)
got = [c["term"] for c in conflicts]
check("LIVE evolocumab-mixed: state is SEED_LEADS_WITH_CONFLICT",
      state == "SEED_LEADS_WITH_CONFLICT",
      "-> %s, conflicts %r, seed %r" % (state, got, terms))
check("LIVE evolocumab-mixed: BOTH drugs are conflicted, not just atorvastatin",
      got == ["atorvastatin", "evolocumab"],
      "-> %r  -- across two trials evolocumab is treatment in one and control in the "
      "other. My plant asserted only 'atorvastatin'; the detector was right and the "
      "assertion was wrong" % (got,))
check("LIVE evolocumab-mixed: 'Q2W' is gone from the seed",
      "Q2W" not in terms, "seed is now %r" % (terms,))
o2 = json.load(io.open(CLEAN_LIVE, encoding="utf-8"))
state2, conflicts2, terms2 = seed_role_state(o2)
got2 = [c["term"] for c in conflicts2]
check("LIVE colchicine-cvd-review: the placebo control is excluded",
      "colchicine" not in got2, "-> %r" % (got2,))
check("LIVE colchicine-cvd-review: a REAL co-intervention is still reported",
      got2 == ["stent", "synergy"],
      "-> %r  -- 'SYNERGY Stent' is genuinely in both arms of NCT03048825. Reported, "
      "not repaired" % (got2,))
check("LIVE colchicine-cvd-review: state is SEED_ROLE_OK",
      state2 == "SEED_ROLE_OK",
      "-> %s  -- the seed leads with 'colchicine', its own titular drug, so the conflict "
      "did not choose the seed" % state2)

print("")
n_ok = sum(1 for _, ok, _ in results if ok)
print("PLANTS: %d/%d" % (n_ok, len(results)))
if n_ok != len(results):
    print("FAILED: %s" % ", ".join(t for t, ok, _ in results if not ok))
    sys.exit(1)
