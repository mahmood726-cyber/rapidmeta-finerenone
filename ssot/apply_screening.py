"""Write the screening result onto the object. Additive; corrects one reason without deleting it.

The screen of the 16-trial unscreened remainder produced 0 INCLUDE / 16 EXCLUDE, so k stays
at 1 and P6 continues to refuse -- but it now refuses on a SCREENED basis, which is a
materially stronger statement than refusing on an unexamined one.

IT ALSO CONTRADICTED ONE OF THE OBJECT'S OWN RECORDED EXCLUSION REASONS, and that correction
is written beside the original rather than over it.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(os.path.dirname(ROOT), "evidence", "2026-08-19-batch1",
                    "bempedoic_screening.json")
TOPIC = "bempedoic-acid-review"


def walk(node, prefix=""):
    out = []
    if isinstance(node, dict):
        for k, v in node.items():
            out.append(f"{prefix}{k}")
            out.extend(walk(v, f"{prefix}{k}."))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            out.extend(walk(v, f"{prefix}[{i}]."))
    return out


with open(EVID, encoding="utf-8") as fh:
    scr = json.load(fh)
path = os.path.join(ROOT, TOPIC, f"{TOPIC}.json")
with open(path, "rb") as fh:
    original = fh.read()
obj = json.loads(original.decode("utf-8"))
before = set(walk(obj))

rows = scr["rows"]
by_limb = {}
for r in rows:
    if r["verdict"] == "EXCLUDE":
        by_limb.setdefault(r["failing_limb"], []).append(r["nct"])

obj["screening_of_remainder"] = {
    "screened_on": "2026-08-19",
    "n_screened": scr["n_screened"],
    "screened_against": (
        "screening.eligibility_provenance -- the DERIVED criteria block "
        "(predefined:false, post_hoc:true). This screen is the first test of whether a "
        "derived block can do the work criteria are for: admitting and excluding named "
        "trials with reasons. It could."),
    "result": {"include": scr["n_include"], "exclude": scr["n_exclude"],
               "not_assessable": scr["n_not_assessable"]},
    "k_after_screening": 1,
    "k_unchanged_because": (
        "None of the 16 met all four limbs. k stays at 1, and P6 therefore continues to "
        "refuse a pooled model -- but it now refuses on a SCREENED basis rather than an "
        "unexamined one, which is a different and stronger statement."),
    "exclusions_by_failing_limb": {k: {"n": len(v), "ncts": v} for k, v in sorted(by_limb.items())},
    "withholding_question": {
        "asked": "does this trial report, AT ANY RANK -- primary, secondary or other -- an "
                 "outcome matching what the included trial reports as its primary?",
        "why_asked_before_deciding_not_to_pool": (
            "Reading only registered PRIMARIES is how a poolable outcome one rank down goes "
            "unseen. Two of the three MACE-matching outcomes found here sit at SECONDARY "
            "rank and a primaries-only screen would have missed both."),
        "trials_with_a_mace_matching_outcome_at_some_rank": [
            {"nct": r["nct"], "hits": r["mace_at_any_rank"]}
            for r in rows if r.get("mace_at_any_rank")],
        "outcome_ranks_searched_total": sum(r.get("outcome_ranks_searched", 0) for r in rows),
    },
    "rows": rows,
    "evidence_file": "evidence/2026-08-19-batch1/bempedoic_screening.json",
}

# --- THE CORRECTION, written BESIDE the original and not over it ------------------------
for st in obj["eligible_but_not_contributing"]["studies"]:
    if st["id"] != "NCT02666664":
        continue
    st["why_not_contributing_CORRECTED_2026_08_19"] = {
        "the_recorded_reason_was_wrong": (
            "The recorded reason reads: 'its registered primaries are SAFETY outcomes -- "
            "treatment-emergent adverse events and events of special interest -- not "
            "cardiovascular events.' That is FACTUALLY WRONG. NCT02666664 registers THIRTEEN "
            "primary outcomes and the SECOND is 'Percentage of Participants With Adjudicated "
            "Major Adverse Cardiovascular Event'. It has a MACE primary."),
        "how_the_error_happened": (
            "The object stores `registered_primary_measure` as a SCALAR holding ONE of the "
            "trial's thirteen primaries -- the first, TEAEs -- and the exclusion reason was "
            "written by characterising all primaries from that single value. A scalar field "
            "standing for a list is how the other twelve became invisible."),
        "the_verdict_still_stands_but_on_a_different_limb": (
            "EXCLUDE is still correct. The failing limb is POPULATION, not OUTCOME: this is "
            "CLEAR Harmony, in high-cardiovascular-risk patients on maximally tolerated "
            "statin therapy, whereas the review's population limb is statin-intolerant "
            "patients."),
        "class": (
            "A correct verdict reached by broken reasoning. It passed every outcome-based "
            "check because the outcome -- exclusion -- was right. Only reading the REASON "
            "against the registry caught it, and only because the withholding question is "
            "asked at every rank rather than at the primary alone."),
        "found_by": "ssot/screen_remainder.py, 2026-08-19",
    }

# --- P1/P2 now have a screened remainder --------------------------------------------------
obj["k_cascade"]["k_unscreened_remainder"] = 0
obj["k_cascade"]["k_unscreened_remainder_note"] = (
    "Was 16. All 16 were screened on 2026-08-19 against the derived criteria block; 0 met "
    "all four limbs. See screening_of_remainder.")
obj["prisma_flow"]["reconciliation"]["gap_stated_plainly"] = (
    "17 CTGov trials place bempedoic acid in an EXPERIMENTAL arm. ONE is included. The other "
    "16 were SCREENED on 2026-08-19 against the stated criteria and all 16 were excluded with "
    "a reason keyed to its registration id: 13 on the OUTCOME limb, 2 on COMPARATOR, 1 on "
    "POPULATION. There is no longer an unscreened remainder.")
obj["prisma_flow"]["excluded_with_reasons"]["screened_remainder"] = {
    "n": scr["n_exclude"], "by_limb": {k: len(v) for k, v in sorted(by_limb.items())}}

# --- P6 refuses on a screened basis now ---------------------------------------------------
ro = obj["results"]["by_outcome"]["primary"]["r_output"]
ro["what_would_change_it"] = (
    "SUPERSEDED 2026-08-19. The 16-trial remainder named here has now been screened, and none "
    "of the 16 met all four limbs -- 13 report no MACE outcome at any registered rank, 2 "
    "declare no placebo arm, 1 is a different population. k remains 1 and this refusal is now "
    "made on a SCREENED basis. What would change it is a NEW trial, not a rescreen of these.")
ro["refusal_basis"] = "SCREENED"

after = set(walk(obj))
lost = before - after
if lost:
    with open(path, "wb") as fh:
        fh.write(original)
    raise SystemExit(f"ABORTED: would remove {sorted(lost)[:6]}. Restored.")

tmp = path + ".part"
with open(tmp, "w", encoding="utf-8", newline="") as fh:
    json.dump(obj, fh, indent=1, ensure_ascii=True)
    fh.write("\n")
os.replace(tmp, path)
print(f"screening written: {scr['n_include']} include / {scr['n_exclude']} exclude / "
      f"{scr['n_not_assessable']} not-assessable; k stays 1; unscreened remainder now 0")
print("NCT02666664 exclusion reason corrected beside the original (verdict unchanged)")
