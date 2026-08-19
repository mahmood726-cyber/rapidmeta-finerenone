"""SCREEN THE 43-TRIAL REMAINDER of `ablation-af-heart-failure` to zero.

CRITERIA, DERIVED POST HOC AND SAYING SO. This topic is one of three that `ablation-af-review`
was split into, so its criteria were written when the split was decided -- after the included
set existed. `predefined: false`. Each element names the registry field that settles it.

  POPULATION    adults with atrial fibrillation AND heart failure or left-ventricular
                dysfunction.                          conditionsModule.conditions
  INTERVENTION  CATHETER-BASED ABLATION OF ATRIAL FIBRILLATION -- pulmonary vein isolation,
                radiofrequency or cryoballoon -- as the randomised intervention.
                                                      armsInterventionsModule.armGroups
  COMPARATOR    medical therapy: rate- or rhythm-control drugs, or conventional / usual /
                standard care.                        armsInterventionsModule.armGroups
  ESTIMAND      a time-to-first-event composite of all-cause mortality with heart-failure
                hospitalisation or heart-failure events, as a hazard ratio.
                                                      outcomesModule, EVERY rank

THE INTERVENTION LIMB CARRIES THE ONE JUDGEMENT IN THIS SCREEN, AND IT IS STATED RATHER THAN
BURIED. **AV-node / AV-junction ablation is NOT this review's intervention.** It ablates the
conduction system and requires a permanent pacemaker; it is a RATE-CONTROL strategy delivered
by ablation, and it does not restore sinus rhythm. Eight trials in this remainder turn on that
distinction, and every one of them says `ablation` in its arm labels -- which is exactly why
identity is taken from what the arm DOES and not from the word it contains. A reader who
disagrees with that boundary can see all eight named below and what including them would add.

THE WITHHOLDING QUESTION WAS ASKED AT EVERY REGISTERED RANK. `ELIGIBLE_NOT_POOLABLE` here
means the estimand appears at NO rank -- primary or secondary -- not merely that the primary
differs. Where a trial's primary is close, the secondaries were read too and are quoted.

FOUR TRIALS WERE CHECKED INDIVIDUALLY AGAINST THE LIVE REGISTRY FOR POSTED RESULTS, because
they were the only candidates for ELIGIBLE_POOLABLE_NOT_INCLUDED -- the cell that would oblige
this review to extract and re-pool. NONE has posted results (`hasResults: false`, no
`resultsSection`). So that cell is ZERO, and it is a COMPUTED zero: it is what four live
registry lookups returned, not a cell nobody filled.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASCADE = os.path.join(REPO, "evidence", "2026-08-19-batch1", "ablation_split_cascade.json")
DEST = os.path.join(REPO, "evidence", "2026-08-19-batch1", "ablation_hf_screening.json")

E, ENP, ENR, EPNI = ("EXCLUDED", "ELIGIBLE_NOT_POOLABLE",
                     "ELIGIBLE_NO_RESULTS_YET", "ELIGIBLE_POOLABLE_NOT_INCLUDED")

# Each row: (nct, verdict, axis, criterion, field_read, reason)
# `criterion` is the limb the verdict RESTS on. `reason` names every other failing limb too --
# a single reason drawn from an ordered sequence of tests is a fact about the sequence (P15).
ROWS = [
    ("NCT00292162", ENP, "POOLABILITY", "ESTIMAND", "outcomesModule",
     "ELIGIBLE: chronic heart failure + AF, radiofrequency ablation against a medical-therapy "
     "arm (ACE inhibitor, beta blocker, aldosterone antagonist). It HAS posted results. Its "
     "primaries are all LEFT VENTRICULAR EJECTION FRACTION by MRI (change, baseline, and at 6 "
     "months) and its secondaries are plasma BNP. No mortality or heart-failure-event outcome "
     "at ANY rank. n=41."),
    ("NCT00589303", E, "ELIGIBILITY", "INTERVENTION", "armsInterventionsModule.armGroups",
     "AV NODE ABLATION AND PACEMAKER against drug therapy. Rate control delivered by ablating "
     "the conduction system, not AF ablation. POPULATION holds (AF + heart failure) and "
     "COMPARATOR holds (rate and rhythm control drugs); the intervention limb is the one that "
     "fails. TERMINATED at n=27, which is NOT the stated ground."),
    ("NCT00652522", ENP, "POOLABILITY", "ESTIMAND", "outcomesModule",
     "ELIGIBLE: persistent AF + heart failure with an ICD; AF ablation added to ICD/CRT in one "
     "arm against ICD/CRT plus best medical treatment in the other, so the device is in BOTH "
     "arms and the randomised contrast is the ablation. Primary is LVEF by transthoracic "
     "echocardiography. n=202."),
    ("NCT00729911", ENP, "POOLABILITY", "ESTIMAND", "outcomesModule",
     "ELIGIBLE: AF ablation against amiodarone -- a rhythm-control drug, so a medical-therapy "
     "comparator -- in congestive heart failure. Primary is TIME TO RECURRENCE OF AF lasting "
     "longer than 15 seconds. An arrhythmia-recurrence endpoint, not a clinical composite. "
     "n=203."),
    ("NCT00839566", E, "ELIGIBILITY", "INTERVENTION", "armsInterventionsModule.armGroups",
     "AV ABLATION against rate control and a sinus-rhythm arm. Conduction-system ablation "
     "again. POPULATION holds. TERMINATED at n=12, not the stated ground."),
    ("NCT00878384", ENP, "POOLABILITY", "ESTIMAND", "outcomesModule",
     "ELIGIBLE: catheter ablation against medical rate control in AF + heart failure. Primary "
     "is PEAK OXYGEN CONSUMPTION at cardiopulmonary exercise testing -- a functional endpoint. "
     "n=52."),
    ("NCT01181414", E, "ELIGIBILITY", "INTERVENTION", "armsInterventionsModule.armGroups",
     "ATRIOVENTRICULAR JUNCTION ABLATION with radiofrequency against drug control of "
     "ventricular rate, in cardiac resynchronisation. Conduction-system ablation. POPULATION "
     "holds (chronic heart failure, dilated cardiomyopathy, AF)."),
    ("NCT01233648", E, "ELIGIBILITY", "POPULATION", "conditionsModule.conditions",
     "conditions = ['Atrial Fibrillation'] ONLY -- no heart failure or ventricular dysfunction "
     "is registered, and this review's population is AF WITH heart failure. INTERVENTION also "
     "fails: the comparison is rate control via CRT-D and AV-nodal ablation against rhythm "
     "control by 'pharmacologic, electrical or ablative therapies', so neither arm is catheter "
     "ablation of AF as such. Both limbs named; the population limb is the ground."),
    ("NCT01411371", ENP, "POOLABILITY", "ESTIMAND", "outcomesModule",
     "ELIGIBLE: catheter ablation of persistent AF against medical treatment alone, in AF + "
     "heart failure. Primary is DIFFERENCE IN EJECTION FRACTION between groups. Settled on the "
     "estimand, which the registry states, rather than on its UNKNOWN recruitment status, "
     "which it does not: an UNKNOWN status is a fact about the registrant's updating, not "
     "about whether the trial reported."),
    ("NCT01522898", E, "ELIGIBILITY", "INTERVENTION", "armsInterventionsModule.armGroups",
     "AV NODAL ABLATION against medical ventricular rate control, with resynchronisation. "
     "Conduction-system ablation. POPULATION holds (heart failure + AF) and the primary -- "
     "'All-cause mortality and non-fatal heart failure events' -- IS this review's estimand, "
     "which is why the intervention limb has to be stated plainly: this trial would pool, and "
     "it is not eligible."),
    ("NCT01639495", E, "ELIGIBILITY", "COMPARATOR", "armsInterventionsModule.armGroups",
     "SINGLE ARM -- one EXPERIMENTAL arm, a THERMOCOOL SMARTTOUCH catheter, and no control. "
     "POPULATION also fails: 'Drug Refractory Symptomatic Paroxysmal Atrial Fibrillation', no "
     "heart failure. Both named; the absence of any comparator is the ground."),
    ("NCT01877473", E, "ELIGIBILITY", "COMPARATOR", "armsInterventionsModule.armGroups",
     "ABLATION AGAINST ABLATION -- 'Reverse remodeling' against 'Standard ablation', both arms "
     "carrying Procedure: Ablation. A technique comparison, not ablation against medical "
     "therapy. POPULATION also fails (persistent AF, no heart failure). WITHDRAWN at n=0."),
    ("NCT02137187", E, "ELIGIBILITY", "INTERVENTION", "armsInterventionsModule.armGroups",
     "AV JUNCTION ABLATION with CRT against optimised drug therapy. Conduction-system "
     "ablation. POPULATION also fails: conditions = ['Permanent Atrial Fibrillation'] with no "
     "heart failure registered."),
    ("NCT02321085", ENP, "POOLABILITY", "ESTIMAND", "outcomesModule",
     "Primaries are improvement of LEFT VENTRICULAR FUNCTION and FUNCTIONAL CAPACITY by rhythm "
     "control. AND THE INTERVENTION LIMB CANNOT BE SETTLED FROM THE RECORD: both arms are "
     "'Procedure: Sinus Rhythm control' and 'Procedure: Pulse Rate control', which do not say "
     "whether the rhythm-control arm is delivered by ablation. Recorded as not-poolable on the "
     "estimand, which IS settled, with the unsettled limb named rather than guessed."),
    ("NCT02509754", ENP, "POOLABILITY", "ESTIMAND", "outcomesModule",
     "ELIGIBLE: AF catheter ablation against a rate-control arm in persistent AF with "
     "congestive heart failure due to LV systolic dysfunction. Primary is a composite of "
     "IMPROVEMENT IN LVEF -- a physiological composite, not a clinical event composite. n=180."),
    ("NCT02686749", ENP, "POOLABILITY", "ESTIMAND", "outcomesModule",
     "ELIGIBLE: catheter ablation against an FDA-approved antiarrhythmic drug in congestive "
     "heart failure with AF. Primary is 'First Hospitalization for Heart Failure, Recurrence "
     "of AF or ...' -- a composite that includes ARRHYTHMIA RECURRENCE, so it is not this "
     "review's mortality-and-heart-failure composite. TERMINATED at n=4 of its planned "
     "enrolment, named but not the ground."),
    ("NCT03062241", ENR, "STATUS", "NO RESULTS POSTED", "hasResults / resultsSection",
     "ELIGIBLE AND ITS ESTIMAND IS THE CLOSEST MATCH IN THE REMAINDER: cryoablation against a "
     "NO_INTERVENTION conventional-treatment arm in AF with severe heart failure, primary "
     "'Composite outcome of hospitalization due to heart failure worsening, mortality, use of "
     "mechanical left ventricle support and heart transplant'. CHECKED LIVE AGAINST THE "
     "REGISTRY: hasResults=false and no resultsSection. There is nothing to extract. n=330."),
    ("NCT03410966", E, "ELIGIBILITY", "COMPARATOR", "armsInterventionsModule.armGroups",
     "ONE ARM ONLY -- 'Intervention group', trans-catheter ablation, no control arm declared. "
     "POPULATION holds (AF + diastolic heart failure) and the primary is AF recurrence, so the "
     "estimand would fail too; the absent comparator is the ground."),
    ("NCT03573869", ENP, "POOLABILITY", "ESTIMAND", "outcomesModule",
     "ELIGIBLE: cryoballoon ablation against a NO_INTERVENTION standard-treatment arm in AF "
     "with systolic heart failure. Primary is TIME TO EXCEED AN AF BURDEN CUT-OFF OF 1% -- an "
     "arrhythmia-burden endpoint. n=404."),
    ("NCT04160000", ENR, "STATUS", "NO RESULTS POSTED", "hasResults / resultsSection",
     "ELIGIBLE, AND THE SINGLE TRIAL IN THIS REMAINDER MOST LIKELY TO CHANGE THE ANSWER. "
     "Catheter ablation against rate- or rhythm-control antiarrhythmic drugs in AF with "
     "diastolic heart failure, primary 'TIME TO COMPOSITE OF HEART FAILURE HOSPITALIZATIONS "
     "AND/OR CARDIOVASCULAR MORTALITY' -- a time-to-first-event composite of exactly this "
     "review's shape -- with all-cause mortality and cardiovascular hospitalisation among its "
     "secondaries. CHECKED LIVE: hasResults=false, no resultsSection. n=360, status UNKNOWN."),
    ("NCT04282850", ENP, "POOLABILITY", "ESTIMAND", "outcomesModule",
     "ELIGIBLE: pulmonary vein isolation against a NO_INTERVENTION medical-management arm in "
     "AF with heart failure and normal ejection fraction. Primary is CHANGE IN AF BURDEN. "
     "TERMINATED at n=13, named but not the ground."),
    ("NCT04327596", ENP, "POOLABILITY", "ESTIMAND", "outcomesModule",
     "ELIGIBLE: radiofrequency AF ablation against a NO_INTERVENTION conventional-treatment "
     "arm in HFpEF. Primary is RATE OF HEALTHCARE UTILISATION. TERMINATED at n=2."),
    ("NCT04342832", ENR, "STATUS", "NO RESULTS POSTED", "hasResults / resultsSection",
     "ELIGIBLE with a near-matching estimand: cryoballoon ablation against a NO_INTERVENTION "
     "standard-medical-care arm in AF with HFrEF, primary 'Composite of all-cause mortality, "
     "unplanned cardiovascular hospitalizations and stroke (time-to-event analysis)'. It "
     "includes STROKE and its hospitalisation limb is cardiovascular rather than "
     "heart-failure, so it is a near neighbour and not this estimand. CHECKED LIVE: "
     "hasResults=false. TERMINATED at n=64 having posted nothing."),
    ("NCT04649801", ENR, "STATUS", "NO RESULTS POSTED", "hasResults / resultsSection",
     "ELIGIBLE: AF ablation against a NO_INTERVENTION conventional arm in end-stage heart "
     "failure. COMPLETED at n=194 and CHECKED LIVE: hasResults=false, no resultsSection -- a "
     "completed trial that has posted nothing, which is a different state from one still "
     "running and is recorded as the same disposition for the same reason: there is nothing to "
     "extract. Its primary, 'Mortality or transplantation', is in any case not this review's "
     "composite -- named so the disposition does not rest on the posting alone."),
    ("NCT04664686", E, "ELIGIBILITY", "COMPARATOR", "armsInterventionsModule.armGroups",
     "AF CATHETER ABLATION AGAINST AV NODE ABLATION -- both arms are ablation, so the contrast "
     "is between two ablation strategies rather than against medical therapy. POPULATION holds "
     "(AF + heart failure)."),
    ("NCT05023590", E, "ELIGIBILITY", "COMPARATOR", "armsInterventionsModule.armGroups",
     "CRYO ABLATION AGAINST RADIOFREQUENCY ABLATION, both delivered during open-chest mitral "
     "valve surgery. A technique comparison. POPULATION also fails: AF with mitral valve "
     "failure, no heart failure registered."),
    ("NCT05434819", E, "ELIGIBILITY", "INTERVENTION", "armsInterventionsModule.armGroups",
     "SURGICAL AF ablation against no surgical ablation. This review's intervention is "
     "CATHETER-BASED ablation; a surgical maze performed during cardiac surgery is a different "
     "procedure with a different risk profile and a different population pathway. POPULATION "
     "holds (AF + heart failure) and the comparator is a genuine no-ablation arm, so the "
     "intervention limb alone decides it. RECRUITING, n=2000."),
    ("NCT05508256", ENR, "STATUS", "NOT YET REPORTED", "statusModule.overallStatus",
     "ELIGIBLE: CE-marked catheter ablation against a NO_INTERVENTION usual-medical-care arm "
     "in AF with HFpEF and HFmrEF, primary a composite of cardiovascular events. RECRUITING at "
     "n=1548 -- THE LARGEST UNREPORTED TRIAL IN THIS REMAINDER, and one of the two that will "
     "determine whether this question has an answer."),
    ("NCT05760833", E, "ELIGIBILITY", "COMPARATOR", "armsInterventionsModule.armGroups",
     "PULMONARY VEIN ISOLATION AGAINST ATRIOVENTRICULAR NODE ABLATION -- both arms ablation. "
     "WITHDRAWN at n=0."),
    ("NCT05827172", ENP, "POOLABILITY", "ESTIMAND", "outcomesModule",
     "ELIGIBLE: AF ablation against an OTHER-typed 'Medical therapy (rate or rhythm control)' "
     "arm in persistent AF with HFrEF. Primary is DIFFERENCE IN EJECTION FRACTION. n=96, "
     "COMPLETED."),
    ("NCT06125925", ENR, "STATUS", "NOT YET REPORTED", "statusModule.overallStatus",
     "ELIGIBLE with a matching estimand shape: radiofrequency catheter ablation against a "
     "medical-therapy arm in AF with HFpEF, primary a 'Composite endpoint of worsening heart "
     "failure requiring unplanned ...'. RECRUITING at n=436."),
    ("NCT06207383", E, "ELIGIBILITY", "COMPARATOR", "armsInterventionsModule.armGroups",
     "AF ABLATION AGAINST CONDUCTION SYSTEM PACING PLUS ATRIOVENTRICULAR NODAL ABLATION. The "
     "comparator arm is itself an ablation strategy. POPULATION holds."),
    ("NCT06299514", E, "ELIGIBILITY", "INTERVENTION", "armsInterventionsModule.armGroups",
     "'PACE AND ABLATE' -- pacemaker implantation with AV-node ablation -- against "
     "pharmacological therapy. Conduction-system ablation, so the intervention limb fails even "
     "though the comparator is exactly the medical therapy this review wants."),
    ("NCT06528262", E, "ELIGIBILITY", "INTERVENTION", "armsInterventionsModule.armGroups",
     "THE RANDOMISED CONTRAST IS A DRUG: enavogliflozin against placebo, given AFTER catheter "
     "ablation. Ablation is background, present in both arms, and the estimate would be "
     "attributable to the SGLT2 inhibitor. POPULATION also fails: conditions = ['Atrial "
     "Fibrillation'] with no heart failure."),
    ("NCT06740539", ENR, "STATUS", "NOT YET REPORTED", "statusModule.overallStatus",
     "ELIGIBLE: catheter ablation against a NO_INTERVENTION drug-control arm in HFpEF with AF, "
     "primary a composite of all-cause death or readmission. NOT_YET_RECRUITING at n=304."),
    ("NCT06833138", E, "ELIGIBILITY", "INTERVENTION", "armsInterventionsModule.armGroups",
     "PACEMAKER IMPLANTATION WITH ATRIOVENTRICULAR NODE ABLATION against a NO_INTERVENTION "
     "arm, in HFpEF with persistent AF. Conduction-system ablation. Its primary -- 'Time to "
     "the composite of all-cause mortality or hospitalization ...' -- IS this review's "
     "estimand, which again is why the intervention boundary is stated rather than assumed."),
    ("NCT07118488", E, "ELIGIBILITY", "COMPARATOR", "armsInterventionsModule.armGroups",
     "SINGLE ARM -- multitarget pulsed-field ablation, no control. POPULATION also fails: "
     "longstanding persistent AF with no heart failure registered."),
    ("NCT07238452", ENR, "STATUS", "NOT YET REPORTED", "statusModule.overallStatus",
     "ELIGIBLE: pulmonary vein isolation against optimal medical therapy (pharmacological rate "
     "control) in HFrEF with AF, primary 'Composite of cardiovascular mortality, stroke, and "
     "total number of ...'. NOT_YET_RECRUITING at n=1056."),
    ("NCT07254455", ENR, "STATUS", "NOT YET REPORTED", "statusModule.overallStatus",
     "ELIGIBLE: CASTLE-HFpEF -- catheter ablation against a NO_INTERVENTION standard-medical- "
     "therapy arm in AF with HFpEF, primary a composite of all-cause mortality, stroke or "
     "transient ischaemic attack. NOT_YET_RECRUITING at n=900. Named because it is the "
     "explicit HFpEF successor to one of this review's two included trials."),
    ("NCT07272902", ENR, "STATUS", "NOT YET REPORTED", "statusModule.overallStatus",
     "ELIGIBLE: catheter ablation against medical rate-control therapy in AF with HFmrEF and "
     "HFpEF. RECRUITING at n=84, and its primary is 'FEASIBILITY OF TRIAL CONDUCT' -- so it "
     "will not contribute an effect estimate when it does report. Settled on status, which is "
     "the uncontestable ground, with the estimand named so the reader is not left expecting a "
     "future contribution."),
    ("NCT07359872", E, "ELIGIBILITY", "INTERVENTION", "armsInterventionsModule.armGroups",
     "THE RANDOMISED CONTRAST IS A DRUG: relaxin against placebo, with 'standard of care "
     "(including ablation)' in BOTH arms and a crossover design. Ablation is background. "
     "POPULATION also fails: AF, arrhythmia, oxidative stress and stroke, no heart failure."),
    ("NCT07385417", ENR, "STATUS", "NOT YET REPORTED", "statusModule.overallStatus",
     "ELIGIBLE ON THE ARMS AND THE POPULATION LIMB IS FLAGGED RATHER THAN ASSUMED: AF ablation "
     "by electroporation against a NO_INTERVENTION 'best medical AF treatment' arm, and the "
     "trial's TITLE names heart failure while conditionsModule.conditions lists only ['Atrial "
     "Fibrillation (AF)']. THE CODED FIELD GOVERNS AND IT DOES NOT CARRY HEART FAILURE; the "
     "free text does. Recorded as eligible-not-yet-reported because status settles it either "
     "way, with the discrepancy stated so the verdict does not rest on the coded field alone. "
     "RECRUITING at n=200."),
    ("NCT07630454", E, "ELIGIBILITY", "INTERVENTION", "armsInterventionsModule.armGroups",
     "THE RANDOMISED CONTRAST IS A DRUG: tirzepatide plus lifestyle against lifestyle alone, "
     "after catheter ablation. Ablation is background in both arms."),
]


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    with io.open(CASCADE, encoding="utf-8") as fh:
        casc = json.load(fh)["ablation-af-heart-failure"]
    pool = sorted(set(casc["experimental_ids"] + casc["comparator_ids"]))
    included = set(casc["included"])
    remainder = [n for n in pool if n not in included]

    screened = {r[0] for r in ROWS}
    missing = [n for n in remainder if n not in screened]
    extra = sorted(screened - set(remainder))

    print("candidate pool (k3+k4)      %3d" % len(pool))
    print("included in this object     %3d" % len(included))
    print("remainder to screen         %3d" % len(remainder))
    print("rows written                %3d" % len(ROWS))
    if missing:
        print("\nREFUSED: %d remainder trial(s) have NO screening row: %s"
              % (len(missing), missing))
        print("An unscreened trial is not an excluded one, and a remainder reported as 0 while "
              "any\nrow is missing is the false-zero this project has already shipped twice.")
        return 1
    if extra:
        print("\nREFUSED: %d screening row(s) name a trial not in the remainder: %s"
              % (len(extra), extra))
        return 1

    tally = {}
    for _n, verdict, _a, _c, _f, _r in ROWS:
        tally[verdict] = tally.get(verdict, 0) + 1
    tally.setdefault(EPNI, 0)

    print("\nDISPOSITIONS")
    for k in (E, ENP, ENR, EPNI):
        print("   %-32s %3d" % (k, tally.get(k, 0)))
    print("   %-32s %3d" % ("total", sum(tally.values())))
    assert sum(tally.values()) == len(remainder)

    by_limb = {}
    for _n, verdict, _a, crit, _f, _r in ROWS:
        if verdict == E:
            by_limb[crit] = by_limb.get(crit, 0) + 1
    print("\nEXCLUSIONS BY THE LIMB THE VERDICT RESTS ON")
    for k, v in sorted(by_limb.items(), key=lambda kv: -kv[1]):
        print("   %-16s %3d" % (k, v))

    out = {
        "screened_utc": "2026-08-19",
        "topic": "ablation-af-heart-failure",
        "criteria_status": ("DERIVED POST HOC on 2026-08-19, when ablation-af-review was split "
                            "into three reviews. predefined: false."),
        "remainder": len(remainder),
        "tally": {k: tally.get(k, 0) for k in (E, ENP, ENR, EPNI)},
        "eligible_poolable_not_included_is_zero_because": (
            "FOUR trials were the only candidates for this cell -- NCT03062241, NCT04160000, "
            "NCT04342832 and NCT04649801, each eligible with a composite primary. All four "
            "were checked LIVE against the registry and NONE has posted results "
            "(hasResults=false, no resultsSection). The zero is what four lookups returned, "
            "not a cell nobody filled."),
        "exclusions_by_failing_limb": by_limb,
        "av_node_ablation_boundary": (
            "EIGHT exclusions turn on ONE judgement: AV-node / AV-junction ablation is not "
            "this review's intervention. It ablates the conduction system, requires a "
            "permanent pacemaker, and is rate control delivered by ablation rather than "
            "restoration of sinus rhythm. Every one of the eight says `ablation` in its arm "
            "labels, which is why identity is taken from what the arm DOES. Two of them -- "
            "NCT01522898 and NCT06833138 -- register EXACTLY this review's estimand, so the "
            "boundary is what excludes them and not the outcome. A reader who draws it "
            "elsewhere can see precisely what including them would add."),
        "trials": [{"nct": n, "verdict": v, "axis": a, "criterion": c,
                    "field_read": f, "reason": r} for n, v, a, c, f, r in ROWS],
    }
    with io.open(DEST, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, indent=1))
    print("\nremainder after screening: 0")
    print("wrote %s" % DEST)
    return 0


if __name__ == "__main__":
    sys.exit(main())
