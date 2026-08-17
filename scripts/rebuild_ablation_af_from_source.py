"""ABLATION_AF -- rebuild the four trial rows from source, and correct the withdrawal.

WHY THIS EXISTS
    The pool on this page was already WITHDRAWN, and the recorded reason was
    "3 of 4 contributing trials carry no outcome definition". Reading the four
    registry records shows the verdict is right and THE REASON IS WRONG: all four
    trials DO record a primary endpoint definition, and NO TWO OF THE FOUR ARE
    THE SAME.

        CASTLE-AF     all-cause mortality or worsening heart failure requiring
                      unplanned hospitalization
        CABANA        total mortality, disabling stroke, serious bleeding, or
                      cardiac arrest
        EAST-AFNET 4  cardiovascular death, stroke, and hospitalisation for
                      worsening heart failure or acute coronary syndrome
        RAFT-AF       all-cause mortality and heart failure events

    Absence of evidence was recorded where there was evidence of difference. The
    withdrawal stands on much stronger ground than the ground it was standing on,
    and a withdrawal needs the same evidentiary standard as a claim.

THREE FURTHER DEFECTS FOUND IN THE PER-TRIAL ROWS, which the withdrawal of the
POOL did nothing to address -- a reader still had four trial rows in front of them:

    1. EAST-AFNET 4's ARMS ARE SWAPPED. The object labels the arm with 249 events
       "Usual care" and gives it the role TREATMENT. The trial's own report says
       "a first-primary-outcome event occurred in 249 of the patients assigned to
       EARLY RHYTHM CONTROL ... and in 316 patients assigned to usual care". The
       label was taken from the registry's arm ORDER and the count from the
       publication's, and the two orders differ. Same family as RE-LY entered as
       dabigatran-versus-dabigatran.

    2. RAFT-AF's EVENT COUNTS ARE WRONG IN BOTH ARMS: 44 and 55 stored against 50
       and 64 posted by the registry and printed in the publication.

    3. EVERY VALUE IS AN ODDS RATIO DERIVED FROM 2x2 COUNTS, while all four
       trials report a TIME-TO-FIRST-EVENT HAZARD RATIO. An odds ratio on
       participants discards the time dimension, and on CASTLE-AF the two differ
       materially: derived OR 0.4956 against the trial's own HR 0.62.

WHAT THIS REBUILD DOES NOT DO
    - It does NOT restore the pool. Four different endpoints cannot be averaged,
      and this rebuild makes that harder to miss rather than easier.
    - It does NOT make this a source-built REVIEW. The protocol, search,
      screening, risk-of-bias and certainty layers are still absent and still
      recorded as absent; only the TRIAL DATA are now source-read. build_mode
      stays CONVERTED for exactly that reason -- flipping it would swap the
      absence vocabulary for one whose sentences are false of this page.
    - It does NOT establish that these four trials belong in one review at all.
      EAST-AFNET 4's intervention is early standardised rhythm control against
      usual care, which is a strategy mostly delivered with antiarrhythmic drugs.
      A review about ablation contains a trial whose intervention is not ablation,
      and that is recorded rather than resolved.
"""
from __future__ import annotations
import io, json, math, os, sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(REPO, "ssot", "ablation-af-review", "ablation-af-review.json")

Z95 = 1.959963984540054
Z96 = 2.053748910631823          # EAST-AFNET 4 printed a 96% interval, not 95%

TRIALS = {
 "NCT00643188": {
  "name": "CASTLE-AF",
  "pmid": "29385358",
  "design": "randomised, open-label; catheter ablation against medical therapy in "
            "heart failure with an implanted defibrillator",
  "endpoint": "All-cause mortality or worsening heart failure requiring unplanned "
              "hospitalization",
  "endpoint_source": "registry",
  "endpoint_quote_extra": "The primary end point was a composite of death from any "
                          "cause or hospitalization for worsening heart failure.",
  "arms": [("Catheter ablation", "treatment", 51, 179),
           ("Medical therapy (rate or rhythm control)", "control", 82, 184)],
  "effect": (0.62, 0.43, 0.87, 95),
  "effect_quote": "the primary composite end point occurred in significantly fewer "
                  "patients in the ablation group than in the medical-therapy group "
                  "(51 patients [28.5%] vs. 82 patients [44.6%]; hazard ratio, 0.62; "
                  "95% confidence interval [CI], 0.43 to 0.87; P=0.007)",
  "effect_source": "publication",
  "effect_source_url": "https://pubmed.ncbi.nlm.nih.gov/29385358/",
  "registry_results": "This trial's registry record posts NO results section, so "
                      "its effect is read from the publication and there is no "
                      "second surface to check it against.",
  "was": "the object stored a DERIVED odds ratio of 0.4956 (0.3206 to 0.7663) from "
         "these same counts. The counts were right; the measure was ours, not the "
         "trial's, and 0.4956 against 0.62 is not a rounding difference.",
 },
 "NCT00911508": {
  "name": "CABANA",
  "pmid": None,
  "pmid_absent_because": "No PMID is recorded here because none was read. The "
      "registry record supplies this trial's endpoint, both arms' counts and its "
      "own Cox analysis, so nothing on this row depends on a publication, and "
      "filling in a plausible identifier would be exactly the guess this project "
      "refuses elsewhere.",
  "design": "randomised, open-label; left atrial ablation against rate or rhythm "
            "control drug therapy",
  "endpoint": "Number of Participants With Composite of Total Mortality, Disabling "
              "Stroke, Serious Bleeding, or Cardiac Arrest in Patients Warranting "
              "Therapy for AF.",
  "endpoint_source": "registry",
  "endpoint_quote_extra": "Death was defined as all-cause mortality, disabling "
      "stroke (including intracranial bleeding) as an irreversible physical "
      "limitation defined by a Rankin Stroke Scale >=2, and serious bleeding as "
      "bleeding accompanied by hemodynamic compromise that required surgical "
      "intervention or a transfusion of >=3 units of blood.",
  "arms": [("Left Atrial Ablation", "treatment", 89, 1108),
           ("Rate or Rhythm Control Therapy", "control", 101, 1096)],
  "effect": (0.86, 0.65, 1.15, 95),
  "effect_quote": "Cox Proportional Hazard 0.86, 95% CI 0.65 to 1.15",
  "effect_source": "registry",
  "effect_source_url": "https://clinicaltrials.gov/study/NCT00911508",
  "registry_results": "The registry posts this trial's primary outcome with both "
                      "arms' counts and its own Cox analysis.",
  "was": "the object stored a DERIVED odds ratio of 0.8604 (0.6387 to 1.1592). Its "
         "point estimate agrees with the trial's hazard ratio to two decimals BY "
         "COINCIDENCE and its interval does not -- 0.639 to 1.159 against 0.65 to "
         "1.15. Agreement of a point estimate is not agreement of an estimand.",
 },
 "NCT01288352": {
  "name": "EAST-AFNET 4",
  "pmid": "32865375",
  "design": "randomised, open-label; early standardised RHYTHM CONTROL -- "
            "antiarrhythmic drugs or ablation -- against usual care",
  "endpoint": "A composite of cardiovascular death, stroke and hospitalization due "
              "to worsening of heart failure or due to acute coronary syndrome.",
  "endpoint_source": "registry",
  "endpoint_quote_extra": "The 1st co-primary outcome parameter is defined as the "
      "time to the first occurrence of a composite of cardiovascular death, stroke "
      "/ transient ischemic attack (TIA), and hospitalization due to worsening of "
      "heart failure or due to acute coronary syndrome.",
  "arms": [("Early standardised rhythm control", "treatment", 249, 1395),
           ("Usual care", "control", 316, 1394)],
  "effect": (0.79, 0.66, 0.94, 96),
  "effect_quote": "A first-primary-outcome event occurred in 249 of the patients "
      "assigned to early rhythm control (3.9 per 100 person-years) and in 316 "
      "patients assigned to usual care (5.0 per 100 person-years) (hazard ratio, "
      "0.79; 96% confidence interval, 0.66 to 0.94; P = 0.005)",
  "effect_source": "publication",
  "effect_source_url": "https://pubmed.ncbi.nlm.nih.gov/32865375/",
  "registry_results": "This trial's registry record posts NO results section.",
  "was": "THE ARMS WERE SWAPPED. The object labelled the 249-event arm 'Usual care' "
         "and gave it the role TREATMENT; the trial's own sentence assigns those "
         "249 events to EARLY RHYTHM CONTROL. The label came from the registry's "
         "arm order and the count from the publication's, and the two differ. The "
         "derived odds ratio 0.7412 was unaffected in magnitude, which is why "
         "nothing caught it: the numbers were consistent and the labels were not. "
         "The interval was also computed at 95% where the trial printed 96%.",
  "not_an_ablation_trial": "THIS TRIAL'S INTERVENTION IS NOT ABLATION. It is early "
      "standardised rhythm control against usual care -- a strategy arm in which "
      "most patients received antiarrhythmic drugs. It sits in a review about "
      "ablation, and that is recorded here rather than quietly resolved: a review "
      "whose title names a comparison its trials do not all make is the "
      "DOAC-versus-warfarin defect, and this object should be re-scoped or this "
      "trial removed by a human decision, not by this script.",
 },
 "NCT01420393": {
  "name": "RAFT-AF",
  "pmid": "35313733",
  "design": "randomised, open-label; ablation-based rhythm control against rate "
            "control in heart failure with high-burden atrial fibrillation",
  "endpoint": "Composite of All-cause Mortality and Heart Failure Events",
  "endpoint_source": "registry",
  "endpoint_quote_extra": "Heart failure event defined as an admission to a "
      "healthcare facility for > 24 hours or clinically significant worsening heart "
      "failure leading to an intervention (defined as treatment in an emergency "
      "department, a same-day access clinic, or an infusion centre) or unscheduled "
      "visits to a healthcare provider for administration of an intravenous "
      "diuretic ... and an increase in chronic heart failure therapy",
  "arms": [("Ablation-based rhythm control", "treatment", 50, 214),
           ("Rate control", "control", 64, 197)],
  "effect": (0.71, 0.49, 1.03, 95),
  "effect_quote": "The primary outcome occurred in 50 (23.4%) patients in the "
                  "rhythm-control group and 64 (32.5%) patients in the rate-control "
                  "group (hazard ratio, 0.71 [95% CI, 0.49-1.03])",
  "effect_source": "publication",
  "effect_source_url": "https://pubmed.ncbi.nlm.nih.gov/35313733/",
  "registry_results": "The registry posts this trial's primary outcome with both "
                      "arms' counts -- 50 of 214 and 64 of 197 -- and no analysis. "
                      "The counts are therefore confirmed on TWO surfaces.",
  "was": "THE EVENT COUNTS WERE WRONG IN BOTH ARMS: 44 and 55 stored, against 50 "
         "and 64 posted by the registry and printed in the publication. The derived "
         "odds ratio 0.6682 was computed from the wrong numbers; the odds ratio the "
         "true counts give is 0.6336, and the trial's own hazard ratio is 0.71.",
 },
}

WITHDRAWN_REASON = (
    "THE FOUR TRIALS MEASURE FOUR DIFFERENT THINGS, and the registry states all "
    "four. CASTLE-AF counts all-cause mortality or worsening heart failure "
    "requiring unplanned hospitalisation. CABANA counts total mortality, disabling "
    "stroke, serious bleeding or cardiac arrest. EAST-AFNET 4 counts cardiovascular "
    "death, stroke, and hospitalisation for worsening heart failure or acute "
    "coronary syndrome. RAFT-AF counts all-cause mortality and heart failure "
    "events, where an event includes an outpatient intravenous diuretic visit. NO "
    "TWO OF THE FOUR ARE THE SAME. An average over them is an average over four "
    "questions.")

WITHDRAWN_NOTE_CORRECTION = (
    "THE EARLIER WITHDRAWAL REASON WAS WRONG, AND IT WAS WRONG IN THE DIRECTION "
    "THAT MATTERS. It said '3 of 4 contributing trials carry no outcome "
    "definition'. All four DO carry one; they are on the registry and they were "
    "not read. Absence of evidence was recorded where there was evidence of "
    "difference. The verdict does not change -- the pool was not established and "
    "is not established now -- but the ground under it does, and a withdrawal "
    "needs the same evidentiary standard as a claim. This correction was found by "
    "reading the four registry records, which is the step that should have "
    "preceded the withdrawal rather than following it.")


def _logse(lo, hi, level):
    z = Z96 if level == 96 else Z95
    return (math.log(hi) - math.log(lo)) / (2 * z)


def main():
    if not os.path.exists(P):
        print("no object at %s -- NOT RUN" % P, file=sys.stderr)
        return 2
    d = json.loads(open(P, encoding="utf-8").read())
    trials = ((d.get("inputs") or {}).get("trials")) or []
    by_nct = {t.get("nct"): t for t in trials if t.get("nct")}
    if set(by_nct) != set(TRIALS):
        print("trial set mismatch: object has %s, this rebuild describes %s"
              % (sorted(by_nct), sorted(TRIALS)), file=sys.stderr)
        return 1

    for nct, spec in TRIALS.items():
        t = by_nct[nct]
        t["name"] = spec["name"]
        t["design"] = spec["design"]
        if spec.get("pmid"):
            t["pmid"] = spec["pmid"]
        elif spec.get("pmid_absent_because"):
            t["pmid_absent_because"] = spec["pmid_absent_because"]
        t["comparator_type"] = "active"
        t["comparator_type_basis"] = (
            "Every trial in this object randomises against an ACTIVE strategy -- "
            "medical therapy, drug therapy, usual care or rate control -- and none "
            "against placebo. Read from each registry record's arm types, where no "
            "arm is typed PLACEBO_COMPARATOR.")
        t["arms"] = [{"label": lab, "role": role, "events": ev, "participants": n}
                     for lab, role, ev, n in spec["arms"]]
        t["enrolled"] = sum(n for _, _, _, n in spec["arms"])
        if spec.get("not_an_ablation_trial"):
            t["subject_scope_flag"] = spec["not_an_ablation_trial"]

        pt, lo, hi, lvl = spec["effect"]
        bo = t["by_outcome"]["primary"]
        bo["effect"] = {
            "measure": "HR",
            "point": pt, "ci_low": lo, "ci_high": hi, "ci_level": lvl,
            "scale": "log",
            "log_point": round(math.log(pt), 6),
            "log_se": round(_logse(lo, hi, lvl), 6),
            "derived_from": "published_hazard_ratio",
            "derivation_note":
                "The hazard ratio and its interval are stored as the source prints "
                "them, at the level the source prints them at. The log point and "
                "log standard error are DERIVED here, the standard error from the "
                "width of the printed interval using the multiplier belonging to "
                "that interval's own level -- 1.96 at 95 per cent and 2.054 at the "
                "96 per cent EAST-AFNET 4 printed -- and neither is claimed to "
                "appear in any source.",
        }
        bo["outcome_definition"] = spec["endpoint"]
        bo["outcome_definition_source"] = {
            "source": spec["endpoint_source"],
            "source_field": "protocolSection.outcomesModule.primaryOutcomes[0]",
            "source_url": "https://clinicaltrials.gov/study/%s" % nct,
            "read_utc": "2026-08-17",
        }
        bo["source_tier"] = ("registry" if spec["effect_source"] == "registry"
                             else "primary_oa")
        bo["source_url"] = spec["effect_source_url"]
        bo["registry_results_status"] = spec["registry_results"]
        bo["analysed"] = {"treatment": spec["arms"][0][3],
                          "control": spec["arms"][1][3]}
        bo["provenance"] = {
            "tag": "MEASURED",
            "source_id": nct,
            "source_quotes": [spec["endpoint"], spec["endpoint_quote_extra"],
                              spec["effect_quote"]],
            "quote_note":
                "Three quotes: the endpoint TITLE as the registry states it, the "
                "registry's or the report's fuller DEFINITION of what those events "
                "are, and the RESULT sentence carrying the number stored. The first "
                "two say what was counted and the third says what happened, and "
                "this object exists partly because those were once confused.",
        }
        bo["corrected_2026_08_17"] = spec["was"]

    res = d["results"]["by_outcome"]["primary"]
    res["pooled"]["withdrawn_reason"] = WITHDRAWN_REASON
    res["pooled"]["withdrawn_reason_correction"] = WITHDRAWN_NOTE_CORRECTION
    res["poolable"] = False
    res["poolable_reason"] = WITHDRAWN_REASON
    res["per_trial"] = [
        {"trial_id": TRIALS[n]["name"], "nct": n, "measure": "HR",
         "point": TRIALS[n]["effect"][0], "ci_low": TRIALS[n]["effect"][1],
         "ci_high": TRIALS[n]["effect"][2], "ci_level": TRIALS[n]["effect"][3],
         "estimand_id": "each trial's OWN primary composite -- FOUR DIFFERENT ONES",
         "endpoint_rank_in_its_own_trial": "PRIMARY",
         "derivation": "the hazard ratio the source prints, stored on the log scale "
                       "with the standard error its printed interval implies at that "
                       "interval's own level"}
        for n in TRIALS]
    res["display_change_announced"] = {
        "when": "2026-08-17",
        "what": "EVERY PER-TRIAL VALUE ON THIS PAGE HAS CHANGED, and the measure has "
                "changed with it. The four rows previously showed ODDS RATIOS "
                "derived by us from 2x2 counts -- 0.4956, 0.8604, 0.7412 and 0.6682. "
                "They now show each trial's OWN reported HAZARD RATIO: 0.62 "
                "(0.43-0.87), 0.86 (0.65-1.15), 0.79 (0.66-0.94 at 96%) and 0.71 "
                "(0.49-1.03).",
        "why": "An odds ratio on participants is not the time-to-first-event hazard "
               "ratio any of these trials reports, and on CASTLE-AF the two differ "
               "materially -- 0.4956 against 0.62. Two of the rows were also wrong "
               "on their own terms: RAFT-AF's event counts were 44 and 55 against a "
               "true 50 and 64, and EAST-AFNET 4's arm labels were swapped so the "
               "page named USUAL CARE as the intervention arm.",
        "for_a_reader_who_wrote_the_old_numbers_down": "None of the four old values "
               "is a correction of an arithmetic slip. They were correct arithmetic "
               "on a quantity none of these trials reports, computed in two cases "
               "from wrong or mislabelled inputs. Use the new ones.",
    }
    with open(P, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("rebuilt %d trial rows from source; pool remains WITHDRAWN with a "
          "corrected reason" % len(TRIALS))
    for n, s in TRIALS.items():
        print("  %-14s %s HR %.2f (%.2f-%.2f) at %d%%"
              % (s["name"], n, s["effect"][0], s["effect"][1], s["effect"][2],
                 s["effect"][3]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
