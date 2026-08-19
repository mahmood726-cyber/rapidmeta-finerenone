#!/usr/bin/env python3
"""Screen iv-iron-hf's 29-trial remainder on TWO AXES, kept separate throughout.

    AXIS 1  ELIGIBILITY -- does the trial meet this review's stated P/I/C/route/outcome?
    AXIS 2  POOLABILITY -- Handbook 6.5 section 10.9: does it estimate the SAME QUANTITY as one
            of this object's pools? A trial can be fully eligible and still not poolable,
            and collapsing the two axes is how eligible evidence gets discarded as if it
            had failed a criterion.

A THIRD STATE THAT IS NEITHER, and it is the largest group here: ELIGIBLE_NO_RESULTS_YET. A
trial that is recruiting, not yet recruiting, or withdrawn before enrolling has not been
assessed and rejected -- it has nothing to contribute yet. Recording it as 'excluded' would
overstate what this review has settled, in exactly the direction the withholding class runs.

EVERY DECISION NAMES THE CRITERION IT TURNS ON AND THE REGISTRY FIELD THAT SETTLES IT. A
screening decision with no named field is an opinion.

THE REVIEW'S CRITERIA, restated from screening.eligibility so each decision can be checked:
  P  adults with heart failure and iron deficiency
  I  INTRAVENOUS iron as ferric carboxymaltose or ferric derisomaltose
  C  placebo OR usual care
  O  a designated CLINICAL-EVENT endpoint, or a registered functional primary a regulator
     relies on
"""
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBJ = os.path.join(REPO, "ssot", "iv-iron-hf", "iv-iron-hf.json")

# verdict, criterion, field, reason
D = [
 ("NCT02737995", "EXCLUDED", "OUTCOME", "outcomesModule.primaryOutcomes",
  "Skeletal-muscle metabolism. A mechanistic endpoint, neither a clinical event nor a "
  "regulator-relied functional primary. n=8."),
 ("NCT03871699", "EXCLUDED", "OUTCOME", "outcomesModule.primaryOutcomes",
  "Intra-myocardial iron load by imaging -- a mechanistic surrogate. n=20."),
 ("NCT00384657", "ELIGIBLE_NO_RESULTS_YET", "INTERVENTION+STATUS", "statusModule.overallStatus",
  "WITHDRAWN with enrolment 0, so it contributes no randomised contrast. Its intervention is "
  "iron SUCROSE, which also fails the FCM/FDI criterion -- but status settles it first and the "
  "weaker ground is not used."),
 ("NCT07643818", "ELIGIBLE_NO_RESULTS_YET", "STATUS", "statusModule.overallStatus",
  "ENROLLING_BY_INVITATION. Ferric derisomaltose vs placebo in HFpEF, n=150. Meets P/I/C; no "
  "results exist to assess."),
 ("NCT07686692", "ELIGIBLE_NO_RESULTS_YET", "STATUS", "statusModule.overallStatus",
  "NOT_YET_RECRUITING. Ferric derisomaltose vs placebo, n=300."),
 ("NCT03042130", "ELIGIBLE_NO_RESULTS_YET", "STATUS", "statusModule.overallStatus",
  "WITHDRAWN, enrolment 0."),
 ("NCT04945707", "EXCLUDED", "OUTCOME", "outcomesModule.primaryOutcomes",
  "Mechanisms of exercise intolerance -- mechanistic. FDI vs placebo, n=65."),
 ("NCT00821717", "ELIGIBLE_NOT_POOLABLE", "POOLABILITY", "outcomesModule.primaryOutcomes",
  "EFFICACY-HF. FCM vs normal saline; meets P/I/C. TERMINATED at n=35. Primary is exercise "
  "capacity and cardiac function -- a unit of analysis matching none of this object's six "
  "pools."),
 ("NCT01922479", "ELIGIBLE_NOT_POOLABLE", "POOLABILITY", "outcomesModule.primaryOutcomes",
  "PRACTICE-ASIA-HF. FCM vs placebo, n=50, COMPLETED. A pilot whose primary is not one of "
  "this object's estimands."),
 ("NCT05759078", "ELIGIBLE_NO_RESULTS_YET", "STATUS", "statusModule.overallStatus",
  "INFERRCT, n=1000, RECRUITING. Ferinject vs sodium chloride, primary is mortality and "
  "cardiovascular outcomes -- a CLINICAL-EVENT endpoint that WOULD be poolable. Nothing to "
  "pool yet. THE LARGEST PENDING CONTRIBUTOR IN THIS REMAINDER."),
 ("NCT01394562", "ELIGIBLE_NOT_POOLABLE", "POOLABILITY", "outcomesModule.primaryOutcomes",
  "EFFECT-HF, n=174, COMPLETED. FCM vs standard of care -- the 'usual care' half of the "
  "comparator criterion admits it, which is why that half is load-bearing. Primary is CHANGE "
  "IN PEAK VO2 (mL/kg/min). NOT poolable with six_min_walk_24w: peak VO2 and six-minute walk "
  "distance are different quantities in different units, and pooling them would be the "
  "unit-of-analysis defect this object was corrected for."),
 ("NCT05816265", "ELIGIBLE_NOT_POOLABLE", "POOLABILITY", "designModule.enrollmentInfo",
  "TERMINATED at n=6. Exercise capacity; no shared estimand."),
 ("NCT01925703", "EXCLUDED", "INTERVENTION", "armsInterventionsModule.interventions",
  "Sodium ferric gluconate -- neither ferric carboxymaltose nor ferric derisomaltose. Primary "
  "is serum haemoglobin, a laboratory measure."),
 ("NCT05477498", "ELIGIBLE_NO_RESULTS_YET", "STATUS", "statusModule.overallStatus",
  "IRON-HFpEF, WITHDRAWN, enrolment 0."),
 ("NCT03380520", "EXCLUDED", "OUTCOME", "outcomesModule.primaryOutcomes",
  "IRON-CRT. Primary is change in left-ventricular ejection fraction -- an imaging surrogate, "
  "not a clinical event."),
 ("NCT03074591", "ELIGIBLE_NOT_POOLABLE", "POOLABILITY", "outcomesModule.primaryOutcomes",
  "FAIR-HFpEF, n=40, COMPLETED. FCM vs saline; meets P/I/C. Primary 'exercise capacity' is "
  "not one of this object's estimands."),
 ("NCT03218384", "EXCLUDED", "OUTCOME", "outcomesModule.primaryOutcomes",
  "Post-exercise phosphocreatine recovery time by 31P MRS -- mechanistic."),
 ("NCT03991000", "EXCLUDED", "OUTCOME", "outcomesModule.primaryOutcomes",
  "iCHF-2. Primaries are LVEF and atrial-fibrillation burden -- surrogates. n=8, TERMINATED."),
 ("NCT03803111", "ELIGIBLE_NO_RESULTS_YET", "STATUS", "statusModule.overallStatus",
  "IronEx, WITHDRAWN, enrolment 0."),
 ("NCT05971732", "ELIGIBLE_NO_RESULTS_YET", "STATUS", "statusModule.overallStatus",
  "COREVIVE-HFrEF, n=146, status UNKNOWN so no results are posted. FDI vs placebo with a "
  "6-minute-walk primary -- the SAME UNIT as six_min_walk_24w, so it would be poolable if it "
  "reports. Recorded as pending rather than excluded precisely because it would contribute."),
 ("NCT00520780", "ELIGIBLE_NOT_POOLABLE", "POOLABILITY", "outcomesModule.primaryOutcomes",
  "FAIR-HF, n=456, COMPLETED -- the trial that established FCM in heart failure. FCM vs normal "
  "saline; meets P/I/C, and its primary (patient global assessment plus NYHA class) is a "
  "registered functional primary a regulator relied on, so it PASSES the outcome criterion. "
  "It is not poolable: PGA/NYHA is an ordinal patient-reported scale, matching none of this "
  "object's six estimands. ELIGIBLE AND NOT POOLED IS THE CORRECT READING -- recording a "
  "landmark trial as 'excluded' would misstate why it is absent."),
 ("NCT06703411", "EXCLUDED", "INTERVENTION", "armsInterventionsModule.interventions",
  "Iron sucrose -- fails the FCM/FDI criterion."),
 ("NCT07053475", "EXCLUDED", "COMPARATOR", "armsInterventionsModule.interventions",
  "IRONICA randomises ferric carboxymaltose against FERROUS SULFATE -- oral iron is an active "
  "comparator, not placebo or usual care. The contrast is route, not iron versus none."),
 ("NCT01978028", "EXCLUDED", "OUTCOME", "outcomesModule.primaryOutcomes",
  "Mitochondrial function -- mechanistic. n=20, TERMINATED."),
 ("NCT05991128", "ELIGIBLE_NO_RESULTS_YET", "STATUS", "statusModule.overallStatus",
  "COREVIVE-HFpEF, n=170, status UNKNOWN. FDI vs placebo, 6-minute-walk primary; same "
  "position as COREVIVE-HFrEF."),
 ("NCT05691257", "EXCLUDED", "INTERVENTION", "armsInterventionsModule.interventions",
  "Roxadustat, a HIF prolyl-hydroxylase inhibitor. Not intravenous iron at all."),
 ("NCT06929806", "ELIGIBLE_NO_RESULTS_YET", "STATUS", "statusModule.overallStatus",
  "ICONIC-HF, n=1900, RECRUITING. Ferric derisomaltose versus NO intravenous iron -- the "
  "'usual care' half of the comparator criterion admits it. Primary is cardiovascular deaths "
  "and hospitalisations for worsening heart failure: THE SAME ESTIMAND AS THIS OBJECT'S "
  "HEADLINE POOL. It will be the single largest contributor when it reports."),
 ("NCT04225728", "EXCLUDED", "INTERVENTION", "armsInterventionsModule.interventions",
  "ERADAL-HF uses iron sucrose IV and ferric polymaltose INTRAMUSCULARLY -- fails both the "
  "FCM/FDI criterion and, for one arm, the intravenous-route criterion."),
 ("NCT01837082", "EXCLUDED", "OUTCOME", "outcomesModule.primaryOutcomes",
  "iCHF. Primary is change in left-ventricular ejection fraction -- a surrogate. n=18, "
  "TERMINATED."),
]

BLOCK = {
    "screened_utc": "2026-08-19",
    "screened_against": "screening.eligibility, restated in scripts/screen_ivi_remainder.py",
    "axes_kept_separate": (
        "ELIGIBILITY (P/I/C/route/outcome) and POOLABILITY (Handbook 6.5 s10.9) are recorded "
        "as SEPARATE verdicts. A trial can be fully eligible and not poolable, and collapsing "
        "the two is how eligible evidence gets discarded as though it had failed a criterion."),
    "third_state_why": (
        "ELIGIBLE_NO_RESULTS_YET is neither. A trial recruiting, not yet recruiting, or "
        "withdrawn before enrolling has NOT been assessed and rejected. Calling it 'excluded' "
        "would overstate what this review has settled, in the same direction the withholding "
        "class runs."),
    "trials": [{"nct": n, "verdict": v, "criterion": c, "field_read": f, "reason": r}
               for n, v, c, f, r in D],
}


def main():
    with io.open(OBJ, encoding="utf-8") as fh:
        obj = json.load(fh)
    from collections import Counter
    tally = Counter(x["verdict"] for x in BLOCK["trials"])
    BLOCK["tally"] = dict(tally)
    assert len(BLOCK["trials"]) == 29, "the remainder is 29"
    scr = obj.setdefault("screening_of_remainder", {})
    before = set(scr.keys())
    scr["iv_iron_2026_08_19"] = BLOCK
    assert before <= set(scr.keys()), "ADDS only"
    with io.open(OBJ, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(obj, indent=1, ensure_ascii=False) + "\n")
    for k, v in sorted(tally.items()):
        print("  %-26s %d" % (k, v))
    print("  %-26s %d" % ("TOTAL", sum(tally.values())))


if __name__ == "__main__":
    main()
