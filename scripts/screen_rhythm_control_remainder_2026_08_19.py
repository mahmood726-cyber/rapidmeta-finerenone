"""SCREEN THE 551-TRIAL REMAINDER of `early-rhythm-control-af`.

WRITTEN FRESH, NOT DERIVED FROM THE SIBLING'S SCREENER, AND THE FIRST ATTEMPT WAS THE DERIVED
ONE. A sed-rename of `screen_ablation_medical_remainder` parses cleanly, runs, and produces a
full set of verdicts -- all of them answering the SIBLING'S question, because its rules ask
whether ABLATION is the contrast. That is one topic's criteria applied to another under a new
filename: the contamination class this repository has met six times, arriving through a copy
rather than through a module constant. Deleted and rewritten.

THE CRITERIA ARE DIFFERENT IN THE WAY THAT MATTERS.

    ablation-af-medical-therapy   the contrast is ABLATION, against medical therapy
    early-rhythm-control-af       the contrast is a RHYTHM-CONTROL STRATEGY, against rate
                                  control or usual care -- and the strategy may be delivered
                                  BY drugs, BY cardioversion, BY ablation, or by all three in
                                  one arm

So an antiarrhythmic-drug arm is the INTERVENTION here and would have been the COMPARATOR
there. A rate-control arm is the COMPARATOR here and would have been the comparator there too,
for a different reason. THE SAME ARM TEXT MEANS DIFFERENT THINGS TO THE TWO REVIEWS, which is
the whole reason they are two reviews.

IDENTITY IS BY ENUMERATED TERM SET OVER DECLARED NAMES, NEVER SUBSTRING OVER CLINICAL TEXT
(P14), and anything the rules cannot settle is NEEDS_ADJUDICATION -- never guessed, never
defaulted to EXCLUDED. The sibling's 621-trial run produced 130 of those and every one was
real; a screen that resolves everything has stopped distinguishing deciding from assuming.
"""
import io
import json
import os
import re
import sys

REPO = "F:/rapidmeta-ssot-shell"
sys.path.insert(0, REPO + "/ssot")
os.environ.setdefault(
    "RM_CTGOV_CACHE",
    "F:/claude-temp/claude/F--rapidmeta-ssot-shell/"
    "eb4d84e5-8a24-4c3b-afe2-34bd91c20bc7/scratchpad/.ctgov-raw-cache")

import ctgov_transport as X          # noqa: E402

CASCADE = os.path.join(REPO, "evidence", "2026-08-19-batch1", "ablation_split_cascade.json")
DEST = os.path.join(REPO, "evidence", "2026-08-19-batch1", "rhythm_control_screening.json")

E, ENP, ENR, EPNI, ADJ = ("EXCLUDED", "ELIGIBLE_NOT_POOLABLE", "ELIGIBLE_NO_RESULTS_YET",
                          "ELIGIBLE_POOLABLE_NOT_INCLUDED", "NEEDS_ADJUDICATION")

AF_TERMS = ("atrial fibrillation", "atrial flutter", "afib", "paroxysmal af", "persistent af",
            "arrhythmia")

# --- RHYTHM CONTROL, however delivered. The strategy words AND its components.
RHYTHM_TERMS = ("rhythm control", "rhythm-control", "early rhythm control",
                "early standardised rhythm control", "early standardized rhythm control",
                "sinus rhythm", "restoration of sinus rhythm", "cardioversion",
                "catheter ablation", "pulmonary vein isolation", "left atrial ablation",
                "radiofrequency ablation", "cryoballoon", "cryoablation",
                "pulsed field ablation", "pulsed-field ablation",
                "antiarrhythmic", "anti-arrhythmic", "amiodarone", "dronedarone",
                "flecainide", "propafenone", "sotalol", "dofetilide")
# --- RATE CONTROL is this review's COMPARATOR, not its intervention. Checked FIRST, because
# --- "rate control" and "rhythm control" differ by one word and the wrong one wins a
# --- substring race.
RATE_TERMS = ("rate control", "rate-control", "ventricular rate control", "pulse rate control",
              "digoxin", "diltiazem", "verapamil", "beta blocker", "beta-blocker",
              "metoprolol", "bisoprolol", "carvedilol", "atenolol")
# --- Conduction-system ablation is RATE control delivered by ablation. It contains ablation
# --- words, so it is checked BEFORE the rhythm family.
NODAL_TERMS = ("av node", "av-node", "avn ablation", "atrioventricular node",
               "atrioventricular nodal", "av junction", "atrioventricular junction",
               "av nodal", "avj ablation", "pace and ablate", "pace & ablate",
               "his bundle", "conduction system pacing")
USUAL_TERMS = ("usual care", "standard care", "standard medical", "conventional treatment",
               "conventional therapy", "best medical", "optimal medical", "standard of care",
               "guideline", "conservative")
NO_TREATMENT_TYPES = ("NO_INTERVENTION",)
MORTALITY_TERMS = ("all-cause mortality", "all cause mortality", "total mortality",
                   "death from any cause", "cardiovascular death", "cardiovascular mortality",
                   "mortality", "death")
# A COMPOSITE IS TWO CLINICAL EVENTS IN ONE ENDPOINT, NOT THE WORD "COMPOSITE".
#
# The first version looked for the literal token and for a handful of phrasings, and the
# known-answer check on this review's OWN included set caught it immediately: CASTLE-AF
# registers "All-cause mortality or worsening heart failure requiring unplanned
# hospitalization" -- unmistakably a composite, containing neither the word "composite" nor
# the contiguous string "or hospitalization" -- and the ESTIMAND limb FAILED.
#
#     A KEYWORD FOR THE NAME OF A THING IS NOT A TEST FOR THE THING. It failed toward
#     NOT-POOLABLE, the withholding direction, on a trial the review includes.
#
# So a composite is detected STRUCTURALLY: a mortality term together with at least one other
# clinical event term in the same endpoint. That is what a composite IS.
SECOND_EVENT_TERMS = ("hospitali", "heart failure", "stroke", "cardiac arrest", "bleeding",
                      "myocardial infarction", "transient ischemic", "transient ischaemic",
                      "cardiovascular event", "readmission", "transplant")
COMPOSITE_TERMS = ("composite", "time to first")
NO_RESULT_STATUSES = ("RECRUITING", "NOT_YET_RECRUITING", "ENROLLING_BY_INVITATION",
                      "ACTIVE_NOT_RECRUITING", "WITHDRAWN", "SUSPENDED", "UNKNOWN")


def hits(text, terms):
    t = " " + re.sub(r"\s+", " ", (text or "").lower()) + " "
    return [w for w in terms if w in t]


def arm_kind(arm):
    """RHYTHM / RATE / NODAL / USUAL / NONE / OTHER_DECLARED / UNREADABLE.

    ORDER MATTERS AND IS STATED. NODAL before RHYTHM, because AV-node ablation carries ablation
    words and is rate control. RATE before RHYTHM, because the two phrases differ by one word.
    """
    if str(arm.get("type") or "").upper() in NO_TREATMENT_TYPES:
        return "NONE"
    names = " ".join(str(n) for n in (arm.get("interventionNames") or []))
    label = str(arm.get("label") or "").strip()
    blob = label + " " + names
    if hits(blob, NODAL_TERMS):
        return "NODAL"
    if hits(blob, RATE_TERMS):
        return "RATE"
    if hits(blob, RHYTHM_TERMS):
        return "RHYTHM"
    if hits(blob, USUAL_TERMS):
        return "USUAL"
    if not names.strip():
        return "UNREADABLE"
    return "OTHER_DECLARED"


def screen(nct, doc):
    p = doc["protocolSection"]
    conds = " ; ".join((p.get("conditionsModule") or {}).get("conditions") or [])
    status = str((p.get("statusModule") or {}).get("overallStatus") or "")
    arms = (p.get("armsInterventionsModule") or {}).get("armGroups") or []
    om = p.get("outcomesModule") or {}
    ranks = [(o.get("measure") or "") for o in (om.get("primaryOutcomes") or [])]
    ranks += [(o.get("measure") or "") for o in (om.get("secondaryOutcomes") or [])]
    all_ranks = " ; ".join(ranks)

    limbs = {"POPULATION": "HOLDS" if hits(conds, AF_TERMS) else "FAILS"}
    kinds = [arm_kind(a) for a in arms]
    n_rhythm = kinds.count("RHYTHM")
    n_ctrl = kinds.count("RATE") + kinds.count("USUAL") + kinds.count("NONE")
    n_unread = kinds.count("UNREADABLE") + kinds.count("OTHER_DECLARED")
    n_nodal = kinds.count("NODAL")

    if len(arms) < 2:
        limbs["COMPARATOR"] = "UNSETTLED" if not arms else "FAILS"
        limbs["INTERVENTION"] = ("HOLDS" if n_rhythm else
                                 "UNSETTLED" if n_unread else "FAILS")
    else:
        if n_rhythm:
            limbs["INTERVENTION"] = "HOLDS"
        elif n_unread:
            limbs["INTERVENTION"] = "UNSETTLED"
        else:
            limbs["INTERVENTION"] = "FAILS"
        # A RHYTHM-CONTROL ARM ON BOTH SIDES IS A HEAD-TO-HEAD, NOT THIS REVIEW'S CONTRAST.
        # CABANA is exactly that: ablation against rate-OR-rhythm control. It is in the
        # included set on a judgement the criteria block carries, and other such trials are
        # sent to adjudication rather than decided here.
        if n_rhythm >= 2:
            limbs["COMPARATOR"] = "UNSETTLED"
        elif n_rhythm and n_ctrl:
            limbs["COMPARATOR"] = "HOLDS"
        elif n_unread:
            limbs["COMPARATOR"] = "UNSETTLED"
        elif n_rhythm and n_nodal:
            limbs["COMPARATOR"] = "HOLDS"
        else:
            limbs["COMPARATOR"] = "FAILS"

    has_mort = bool(hits(all_ranks, MORTALITY_TERMS))
    has_comp = bool(hits(all_ranks, COMPOSITE_TERMS)) or bool(
        hits(all_ranks, SECOND_EVENT_TERMS))
    limbs["ESTIMAND"] = "HOLDS" if (has_mort and has_comp) else (
        "UNSETTLED" if not all_ranks else "FAILS")

    failing = [k for k, v in limbs.items() if v == "FAILS" and k != "ESTIMAND"]
    unsettled = [k for k, v in limbs.items() if v == "UNSETTLED" and k != "ESTIMAND"]
    if failing:
        return (E, "ELIGIBILITY", failing[0], limbs, kinds, status, conds,
                "fails %s. ALL limbs: %s. arms: %s" % (", ".join(failing), limbs, kinds))
    if unsettled:
        return (ADJ, "ELIGIBILITY", unsettled[0], limbs, kinds, status, conds,
                "the rules cannot settle %s from declared fields. arms: %s"
                % (", ".join(unsettled), kinds))
    if "hasResults" not in doc:
        return (ADJ, "TRANSPORT", "hasResults ABSENT", limbs, kinds, status, conds,
                "eligible, and whether it posted results cannot be read from this payload")
    if status in NO_RESULT_STATUSES or not doc.get("hasResults"):
        return (ENR, "STATUS", "NO RESULTS POSTED", limbs, kinds, status, conds,
                "eligible; status %s, hasResults=%s" % (status, doc.get("hasResults")))
    if limbs["ESTIMAND"] != "HOLDS":
        return (ENP, "POOLABILITY", "ESTIMAND", limbs, kinds, status, conds,
                "eligible and reports results, but no mortality composite at ANY rank")
    return (EPNI, "POOLABILITY", "ESTIMAND MATCHES", limbs, kinds, status, conds,
            "ELIGIBLE, POOLABLE AND NOT IN THIS OBJECT -- must be extracted and re-pooled")


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    casc = json.load(io.open(CASCADE, encoding="utf-8"))["early-rhythm-control-af"]
    pool = sorted(set(casc["experimental_ids"] + casc["comparator_ids"]))
    included = set(casc["included"])
    remainder = [n for n in pool if n not in included]
    print("candidate pool %d, included %d, remainder %d"
          % (len(pool), len(included), len(remainder)))

    rows, tally, by_limb = [], {}, {}
    for i, nct in enumerate(remainder, 1):
        st, study, det = X.fetch_raw(nct, fields="protocolSection,hasResults")
        if st != X.OK:
            rows.append({"nct": nct, "verdict": ADJ, "axis": "TRANSPORT",
                         "criterion": "UNREACHABLE", "reason": "%s: %s" % (st, det)})
            tally[ADJ] = tally.get(ADJ, 0) + 1
            continue
        doc = X.require_raw_v2(study, nct)
        v, axis, crit, limbs, kinds, status, conds, reason = screen(nct, doc)
        rows.append({"nct": nct, "verdict": v, "axis": axis, "criterion": crit,
                     "limbs": limbs, "arm_kinds": kinds, "status": status,
                     "conditions": conds[:160],
                     "field_read": "armGroups + conditionsModule + outcomesModule (every "
                                   "rank) + statusModule",
                     "reason": reason})
        tally[v] = tally.get(v, 0) + 1
        if v == E:
            by_limb[crit] = by_limb.get(crit, 0) + 1
        if i % 150 == 0:
            print("   screened %d/%d" % (i, len(remainder)))

    print("\nDISPOSITIONS")
    for k in (E, ENP, ENR, EPNI, ADJ):
        print("   %-32s %4d" % (k, tally.get(k, 0)))
    print("   %-32s %4d" % ("total", sum(tally.values())))
    print("\nEXCLUSIONS BY THE LIMB THE VERDICT RESTS ON")
    for k, v in sorted(by_limb.items(), key=lambda kv: -kv[1]):
        print("   %-16s %4d" % (k, v))
    print("\nEVERY DISPOSITION REACHED AT LEAST ONCE? (P24)")
    for k in (E, ENP, ENR, EPNI, ADJ):
        print("   %-32s %s" % (k, "yes" if tally.get(k) else "NO -- reached zero times"))

    out = {"screened_utc": "2026-08-19", "topic": "early-rhythm-control-af",
           "remainder": len(remainder),
           "method": ("mechanical first pass over declared registry fields with enumerated "
                      "term sets; anything the rules cannot settle is NEEDS_ADJUDICATION"),
           "criteria_differ_from_the_sibling": (
               "the contrast here is a RHYTHM-CONTROL STRATEGY against rate control or usual "
               "care. An antiarrhythmic-drug arm is the INTERVENTION here and would be the "
               "COMPARATOR in ablation-af-medical-therapy. The same arm text means different "
               "things to the two reviews, which is why they are two reviews."),
           "tally": {k: tally.get(k, 0) for k in (E, ENP, ENR, EPNI, ADJ)},
           "exclusions_by_failing_limb": by_limb, "trials": rows}
    with io.open(DEST, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, indent=1))
    print("\nwrote %s" % DEST)
    print("\nNEEDS_ADJUDICATION %d -- NOT screened; the remainder is NOT zero until they are."
          % tally.get(ADJ, 0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
