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

WHERE `field_read` ACTUALLY COMES FROM, corrected 2026-09-04. NO LINE IN THIS FILE READS
ClinicalTrials.gov. `D` below is a hard-coded literal list; the `field_read` value on each row
was TYPED BY ITS AUTHOR, and until this correction it asserted a read this script never
performed. The reader's page renders that value in a cell headed "Field read", so a hand-typed
label there is not decoration -- it is a claim about provenance, made in the one place a reader
goes to check provenance.

    THE FIX TAKEN, AND WHY THAT ONE. The field is MADE HONEST rather than made real, on every
    row except the three that were re-read. Making it real would mean re-running this screen
    against a live registry, which rewrites 29 rows that are already served, from a script
    whose author-time reads are undated and unrecoverable -- a larger change than a provenance
    correction is authorised to make, and one this environment could not execute or verify in
    any case, because it has no network. So each row now carries `provenance` beside
    `field_read`, and `field_read` names the field the DECISION TURNS ON rather than a read.

    WHERE THE READ WAS MADE REAL: the three rows corrected on 2026-09-04 carry
    `registry_measured_2026_09_04` with the verbatim `measure` and `description` strings and
    the date they were read. Those rows can be checked without a network call. The other 26
    cannot, and now say so.

THE TITLE-WITHOUT-DESCRIPTION DEFECT, corrected 2026-09-04. Three rows below characterised a
trial's outcome from `outcomesModule.primaryOutcomes[].measure` -- the TITLE -- and never read
`description` on the same record. Two of them were false as a result, and the third was false
without matching either field. The registry TITLE of FAIR-HFpEF's primary is the two words
"exercise capacity"; its DESCRIPTION on the same record is "The difference of 6-minute walking
distance in meters from baseline to week 24 ...". EFFECT-HF, two rows away, is correctly
rejected on peak VO2 by reading exactly that field, so the field was available and was simply
not read. A test now fails on this class:
scripts/test_screen_reason_vs_registry_description.py.

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
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBJ = os.path.join(REPO, "ssot", "iv-iron-hf", "iv-iron-hf.json")

# nct, verdict, criterion, field, reason  [, extra dict]
#
# `field` NAMES THE FIELD THE DECISION TURNS ON. It does NOT record a read performed here --
# see the provenance paragraph in the module docstring. Rows carrying an `extra` dict with
# `registry_measured_2026_09_04` DID have that read performed, on that date, and store the
# verbatim strings so the next reader need not take anyone's word for it.
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
 # ---------------------------------------------------------------------------------------
 # CORRECTED 2026-09-04. TITLE-WITHOUT-DESCRIPTION, worst variant: the retracted reason matched
 # NEITHER field. "cardiac function" appears nowhere on this record.
 #
 # RETRACTED TEXT, VERBATIM, NOT IN FORCE:
 #   "EFFICACY-HF. FCM vs normal saline; meets P/I/C. TERMINATED at n=35. Primary is exercise
 #    capacity and cardiac function -- a unit of analysis matching none of this object's six
 #    pools."
 # ---------------------------------------------------------------------------------------
 ("NCT00821717", "ELIGIBLE_NOT_POOLABLE",
  "POOLABILITY -- ESTIMAND MATCHES BUT NO EXTRACTABLE CELL WAS LOCATED",
  "outcomesModule.primaryOutcomes[].measure (.description is EMPTY on this record) + "
  "designModule.enrollmentInfo",
  "EFFICACY-HF. FCM vs normal saline; meets P/I/C. TERMINATED at n=35. ITS TWO REGISTERED "
  "CO-PRIMARIES ARE 'The distance covered in six-minute walk tests performed at 4, 12 and 24 "
  "weeks' AND 'NYHA class assessed at weeks 4, 12 and 24 after the start of study treatment'. "
  "The first IS this object's six_min_walk_24w quantity, in metres, at week 24. IT IS NOT "
  "POOLABLE HERE FOR A NARROWER REASON THAN THE ONE THIS ROW USED TO GIVE: no published report "
  "was located, so no between-arm difference with a dispersion term exists to extract. A PubMed "
  "search on 2026-09-04 returned nothing, which is a SEARCH RESULT AND NOT AN ESTABLISHED "
  "ABSENCE and is recorded as such. THE RETRACTED REASON SAID 'Primary is exercise capacity and "
  "cardiac function'. That matched no string on the record at either title or description "
  "level -- an outcome characterisation with no registry provenance at all, carried under a "
  "`field_read` naming outcomesModule.primaryOutcomes.",
  {"registry_measured_2026_09_04": {
    "source": "ClinicalTrials.gov API v2, read 2026-09-04",
    "url": "https://clinicaltrials.gov/study/NCT00821717",
    "outcomesModule.primaryOutcomes[0].measure":
      "The distance covered in six-minute walk tests performed at 4, 12 and 24 weeks",
    "outcomesModule.primaryOutcomes[0].description": None,
    "outcomesModule.primaryOutcomes[1].measure":
      "NYHA class assessed at weeks 4, 12 and 24 after the start of study treatment",
    "outcomesModule.primaryOutcomes[1].description": None,
    "note_on_the_empty_description":
      "this record carries NO description on either primary, so the title alone would have "
      "settled it correctly and the row still got it wrong. Reading the description is "
      "necessary and is not sufficient; reading SOMETHING is the floor."},
   "publication_search_2026_09_04": {
    "searched": "PubMed, on the registration identifier and the acronym with intervention and "
                "condition terms",
    "result": "0 records",
    "state": "CLAIMED ABSENCE -- NOT AN ESTABLISHED ONE"},
   "pooling_decision": {
    "state": "NOT POOLABLE AS THINGS STAND, on the absence of an extractable cell",
    "reopens_if": "a published or posted between-arm 6MWD difference with a dispersion term "
                  "is located"}}),
 # ---------------------------------------------------------------------------------------
 # CORRECTED 2026-09-04. TITLE-WITHOUT-DESCRIPTION: the retracted reason named no outcome at
 # all -- it asserted a mismatch under a `field_read` claiming a field it had not consulted.
 #
 # RETRACTED TEXT, VERBATIM, NOT IN FORCE:
 #   "PRACTICE-ASIA-HF. FCM vs placebo, n=50, COMPLETED. A pilot whose primary is not one of
 #    this object's estimands."
 # ---------------------------------------------------------------------------------------
 ("NCT01922479", "ELIGIBLE_POOLABLE_NOT_INCLUDED",
  "POOLABILITY -- SAME QUANTITY, DIFFERENT TIMEPOINT; POOLING DECISION OPEN",
  "outcomesModule.primaryOutcomes[0].measure AND .description",
  "PRACTICE-ASIA-HF. FCM against saline in Southeast Asians hospitalised with decompensated "
  "heart failure and iron deficiency, n=50, COMPLETED; meets P/I/C. ELIGIBLE. ITS REGISTERED "
  "PRIMARY IS 'Change in 6MWT distance over time' -- the CHANGE IN SIX-MINUTE WALK DISTANCE, "
  "this object's six_min_walk_24w quantity, IN METRES -- at 12 weeks rather than 24. The "
  "published report prints an extractable cell: adjusted mean difference 0.88 m (95% CI -30.2 "
  "to 32.0, P = 0.956). WHAT IS ACTUALLY IN QUESTION IS THE TIMEPOINT, which is a narrower and "
  "different question from the one the retracted reason answered; alirocumab-lipid's "
  "NCT01812707 row records a timepoint as its own ground ('ESTIMAND -- TIMEPOINT') rather than "
  "folding it into 'not our estimand', and that is the precedent followed here. POPULATION IS A "
  "SECOND OPEN QUESTION, NAMED RATHER THAN USED: randomisation was in hospital before discharge "
  "after decompensation, not in the ambulatory population CONFIRM-HF enrolled. THE POOLING "
  "DECISION IS OPEN AND IS RECORDED AS OPEN.",
  {"registry_measured_2026_09_04": {
    "source": "ClinicalTrials.gov API v2, read 2026-09-04",
    "url": "https://clinicaltrials.gov/study/NCT01922479",
    "outcomesModule.primaryOutcomes[0].measure": "Change in 6MWT distance over time",
    "outcomesModule.primaryOutcomes[0].timeFrame": "12 weeks",
    "outcomesModule.primaryOutcomes[0].description":
      "Assess the change in the patient's 6MWT distance over time, from baseline, at 4 weeks, "
      "and at 12 weeks."},
   "published_measured_2026_09_04": {
    "citation": "Yeo TJ, Yeo PSD, Hadi FA, et al. Single-dose intravenous iron in Southeast "
                "Asian heart failure patients: A pilot randomized placebo-controlled study "
                "(PRACTICE-ASIA-HF). ESC Heart Fail 2018;5(2):344-353.",
    "pmid": "29345426", "doi": "10.1002/ehf2.12250",
    "source": "PubMed record for PMID 29345426, read 2026-09-04",
    "effect": "adjusted mean difference between groups 0.88 m, 95% CI -30.2 to 32.0, P = 0.956",
    "randomised": 50, "extractable": True},
   "pooling_decision": {
    "state": "OPEN -- NOT TAKEN IN THIS ROW",
    "open_on": ["timepoint: 12 weeks against CONFIRM-HF's 24",
                "population: in-hospital post-decompensation against ambulatory"]}}),
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
 # ---------------------------------------------------------------------------------------
 # CORRECTED 2026-09-04. RIGHT ANSWER, UNCHECKED REASON -- and the clearest single argument in
 # this file for reading the description: the primary TITLE here is the same two words as
 # NCT03074591's, four rows below, and it means peak VO2 on this record and six-minute walk
 # distance on that one. Same title, opposite content, opposite disposition.
 #
 # RETRACTED TEXT, VERBATIM, NOT IN FORCE:
 #   "TERMINATED at n=6. Exercise capacity; no shared estimand."
 # ---------------------------------------------------------------------------------------
 ("NCT05816265", "ELIGIBLE_NOT_POOLABLE", "POOLABILITY",
  "outcomesModule.primaryOutcomes[].measure AND .description, plus "
  "secondaryOutcomes[].description; designModule.enrollmentInfo",
  "TERMINATED at n=6. ITS PRIMARY IS PEAK VO2, NOT WALK DISTANCE, AND THE DESCRIPTION IS WHAT "
  "SETTLES THAT: the primary's TITLE is the same two words as FAIR-HFpEF's -- 'Exercise "
  "Capacity' -- and its DESCRIPTION on this record reads 'Cardiopulmonary exercise testing will "
  "be administered to measure Peak V02.' Same title, opposite content, opposite disposition. "
  "THE OLD REASON REACHED THE RIGHT ANSWER WITHOUT CHECKING, and is corrected on that ground "
  "alone. A SECONDARY RANK IS NAMED RATHER THAN LEFT OUT: 'Objective Quality of Life measures' "
  "carries the description 'A 6-minute walk test will be administered to determine if the NYHA "
  "class has improved.' A 6MWT IS administered here, and it is visible ONLY in the description. "
  "It is not a walk-distance ENDPOINT: it is an instrument for grading NYHA class, at secondary "
  "rank, and the trial stopped at n=6, so there is no cell to extract for six_min_walk_24w and "
  "no prospect of one.",
  {"registry_measured_2026_09_04": {
    "source": "ClinicalTrials.gov API v2, read 2026-09-04",
    "url": "https://clinicaltrials.gov/study/NCT05816265",
    "primaryOutcomes[0].measure": "Exercise Capacity",
    "primaryOutcomes[0].description":
      "Cardiopulmonary exercise testing will be administered to measure Peak V02. During the "
      "exercise testing a special mouthpiece that can measure oxygen and carbon dioxide is used "
      "to measure peak oxygen uptake.",
    "primaryOutcomes[1].measure": "Patient subjective outcome measures",
    "secondaryOutcomes[0].measure": "Objective Quality of Life measures",
    "secondaryOutcomes[0].description":
      "A 6-minute walk test will be administered to determine if the NYHA class has improved.",
    "why_this_row_is_worth_the_space":
      "'Exercise Capacity' is peak VO2 here and six-minute walk distance on NCT03074591. The "
      "two rows sit four apart in this block, carry the same outcome title, and require "
      "opposite dispositions. That is the whole argument for reading the description, in one "
      "pair."}}),
 ("NCT01925703", "EXCLUDED", "INTERVENTION", "armsInterventionsModule.interventions",
  "Sodium ferric gluconate -- neither ferric carboxymaltose nor ferric derisomaltose. Primary "
  "is serum haemoglobin, a laboratory measure."),
 ("NCT05477498", "ELIGIBLE_NO_RESULTS_YET", "STATUS", "statusModule.overallStatus",
  "IRON-HFpEF, WITHDRAWN, enrolment 0."),
 ("NCT03380520", "EXCLUDED", "OUTCOME", "outcomesModule.primaryOutcomes",
  "IRON-CRT. Primary is change in left-ventricular ejection fraction -- an imaging surrogate, "
  "not a clinical event."),
 # ---------------------------------------------------------------------------------------
 # CORRECTED 2026-09-04. THE REPORTED INSTANCE OF TITLE-WITHOUT-DESCRIPTION, and the one that
 # cost the most: the registry TITLE of this primary really is the two words "exercise
 # capacity", and the DESCRIPTION on the same record says it is 6-minute walking distance to
 # week 24. Reading only the first kept a published 49 m result with an interval out of a pool
 # of one. EFFECT-HF, two rows above, is correctly rejected on peak VO2 by reading exactly the
 # field this row skipped.
 #
 # RETRACTED TEXT, VERBATIM, NOT IN FORCE:
 #   "FAIR-HFpEF, n=40, COMPLETED. FCM vs saline; meets P/I/C. Primary 'exercise capacity' is
 #    not one of this object's estimands."
 # ---------------------------------------------------------------------------------------
 ("NCT03074591", "ELIGIBLE_POOLABLE_NOT_INCLUDED",
  "POOLABILITY -- ESTIMAND MATCHES; POOLING DECISION OPEN AND NAMED AS OPEN",
  "outcomesModule.primaryOutcomes[0].measure AND outcomesModule.primaryOutcomes[0].description "
  "-- BOTH, and reading BOTH is the correction",
  "FAIR-HFpEF. Ferric carboxymaltose against saline in HFpEF with iron deficiency; meets "
  "P/I/C. ELIGIBLE. ITS REGISTERED PRIMARY IS THE CHANGE IN SIX-MINUTE WALK DISTANCE FROM "
  "BASELINE TO WEEK 24, AND THAT IS THIS OBJECT'S six_min_walk_24w ESTIMAND -- the same "
  "quantity, the same unit (metres), the same timepoint, and the same quantity CONFIRM-HF "
  "contributes, which is the only trial presently in that pool. THE POOLING DECISION IS OPEN "
  "AND IS RECORDED AS OPEN: this row does NOT add the trial, because k for that estimand is a "
  "served result and moving it is a separate decision belonging to whoever owns the pool. WHAT "
  "A READER WEIGHING IT SHOULD KNOW FIRST: the trial was STOPPED EARLY for slow recruitment "
  "after 39 of a planned 200 patients had been randomised (median age 80, 62% women) -- small, "
  "imprecise, and subject to the biases of stopping early, which is a real reason to weight it "
  "differently and is stated here rather than left to be discovered. A NOTE ON n: the registry "
  "records enrolment 40 and the publication reports 39 randomised; the retracted row's 'n=40' "
  "came from the registry and was not itself the defect.",
  {"registry_measured_2026_09_04": {
    "source": "ClinicalTrials.gov API v2, read 2026-09-04",
    "url": "https://clinicaltrials.gov/study/NCT03074591",
    "outcomesModule.primaryOutcomes[0].measure": "exercise capacity",
    "outcomesModule.primaryOutcomes[0].timeFrame": "24 weeks",
    "outcomesModule.primaryOutcomes[0].description":
      "The difference of 6-minute walking distance in meters from baseline to week 24 in "
      "symptomatic patients with HFpEF with documented ID compared to the control group.",
    "statusModule.overallStatus": "COMPLETED",
    "designModule.enrollmentInfo.count": 40},
   "published_measured_2026_09_04": {
    "citation": "von Haehling S, Doehner W, Evertz R, et al. Ferric carboxymaltose and exercise "
                "capacity in heart failure with preserved ejection fraction and iron "
                "deficiency: the FAIR-HFpEF trial. Eur Heart J 2024;45(37):3789-3800.",
    "pmid": "39185895", "doi": "10.1093/eurheartj/ehae479",
    "source": "PubMed record for PMID 39185895, read 2026-09-04",
    "effect": "least square mean difference 49 m, 95% CI 5 to 93, P = 0.029",
    "randomised": 39, "planned": 200,
    "stopped_early": "stopped because of slow recruitment after 39 patients had been included",
    "extractable": True},
   "pooling_decision": {
    "state": "OPEN -- NOT TAKEN IN THIS ROW",
    "why_open": "adding this trial takes k for six_min_walk_24w from 1 to 2 and turns a "
                "single-trial result presented as such into a two-trial meta-analysis",
    "what_this_row_must_not_be_read_as": "authority to pool. It is authority to stop saying "
                                         "the trial measures something else."}}),
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
 # ---------------------------------------------------------------------------------------
 # RETRACTED 2026-09-04, AND THE RETRACTED TEXT IS KEPT BELOW RATHER THAN DELETED.
 #
 # THIS SCRIPT ASSERTED ELIGIBLE_NOT_POOLABLE / POOLABILITY FOR FAIR-HF AND CALLED THAT
 # ASSERTION "THE CORRECT READING". IT IS WITHDRAWN. The object's EXCLUDED / OUTCOME is
 # adopted instead. What settled it, measured rather than argued:
 #
 #   1. THE READER SEES `EXCLUDED`, AND HAS SINCE BEFORE THIS SCRIPT'S READING EXISTED.
 #      IV_IRON_HF_REVIEW.html (sha256 9da59bad0237...db88e7f0) renders FAIR-HF in three
 #      places and all three say excluded: the screening card at #screen-fair-hf-nct00520780
 #      ("This review's decision: excluded."), the aggregate line
 #      ("EXCLUDED 14, ELIGIBLE NOT POOLABLE 5, ELIGIBLE NO RESULTS YET 10"), and
 #      k_cascade.remainder_dispositions.notable_excluded_on_outcome. THE READING BELOW
 #      APPEARS ZERO TIMES ON THE SERVED PAGE. It was never published.
 #
 #   2. THE OBJECT'S ROW IS THE AUDITED ONE. screening.records[0] carries a source tier
 #      (primary_oa), a source URL, criteria_failed=["outcome_not_this_review's"] and
 #      not_poolable_even_if_eligible=[] -- the two axes recorded SEPARATELY, which is the
 #      discipline this script's own docstring demands, applied and reaching the opposite
 #      verdict. That row also records its own correction history: an earlier version said
 #      the trial can contribute to none of this review's estimands, "WHICH IS FALSE AND WAS
 #      THE MOST SUBSTANTIVE THING A GATE LEG FOUND IN THIS OBJECT". The row has been
 #      through review. The line below has not.
 #
 #   3. THE SUBSTANTIVE POINT. The retracted text claims PGA + NYHA is "a registered
 #      functional primary a regulator relied on", so FAIR-HF passes O and fails only
 #      poolability. The object holds that FAIR-HF designates NO clinical-event endpoint and
 #      that PGA/NYHA is not the regulator-relied functional primary this review's O
 #      criterion means. That is a disposition about what the trial DESIGNATED, and it is
 #      the eligibility axis, not the poolability axis. On that reading the axes were not
 #      collapsed; the criterion was simply read the other way.
 #
 # THE RETRACTED CLAIM'S ONE DURABLE POINT IS PRESERVED, because it is right and the new
 # reason carries it: FAIR-HF is absent for a NARROW reason -- the staged abstract prints no
 # extractable between-arm difference for walk distance -- not because it measured nothing
 # this review wants. "Excluded" must not be read as "assessed and found worthless".
 #
 # RETRACTED TEXT, VERBATIM, NOT IN FORCE:
 #   ("NCT00520780", "ELIGIBLE_NOT_POOLABLE", "POOLABILITY", "outcomesModule.primaryOutcomes",
 #    "FAIR-HF, n=456, COMPLETED -- the trial that established FCM in heart failure. FCM vs
 #     normal saline; meets P/I/C, and its primary (patient global assessment plus NYHA
 #     class) is a registered functional primary a regulator relied on, so it PASSES the
 #     outcome criterion. It is not poolable: PGA/NYHA is an ordinal patient-reported scale,
 #     matching none of this object's six estimands. ELIGIBLE AND NOT POOLED IS THE CORRECT
 #     READING -- recording a landmark trial as 'excluded' would misstate why it is absent.")
 # ---------------------------------------------------------------------------------------
 ("NCT00520780", "EXCLUDED", "OUTCOME", "outcomesModule.primaryOutcomes",
  "FAIR-HF, n=456, COMPLETED -- the trial that established FCM in heart failure. FCM vs normal "
  "saline; meets P/I/C, but its registered primaries are patient global assessment plus NYHA "
  "class and it designates no clinical-event endpoint. This review holds a walk-distance "
  "estimand and the trial reports improvement on that test, but the staged abstract prints no "
  "between-arm difference, dispersion term or interval for walk distance, so there is no "
  "extractable cell for that estimand. EXCLUDED ON OUTCOME is the correct reading. THE ABSENCE "
  "IS NARROW AND MUST BE READ AS SUCH: it is a limit on what the staged source PRINTS, not a "
  "finding that a landmark trial measured nothing this review wants."),
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

# =========================================================================================
# THE MIRROR HAD ALREADY DRIFTED, AND THAT DRIFT IS THE SAME FAILURE AS THE ONE THIS FILE WAS
# OPENED TO FIX -- a repair applied to one surface and not to the other.
#
# On 2026-09-04, BEFORE the title-without-description correction below, a separate pass
# relabelled eight rows on the OBJECT from EXCLUDED to ELIGIBLE_OUTCOME_UNAVAILABLE (Handbook
# 6.5 s3.2.4: eligibility must not depend on which outcomes a study reported) and corrected one
# criterion. THAT PASS DID NOT TOUCH THIS SCRIPT. So `D` above still held the pre-relabelling
# verdicts, and re-running main() would have silently REVERTED the relabelling on eight rows.
#
# The overlay below carries the object's state so the mirror stops being stale. It is kept
# SEPARATE from `D` rather than merged into it, so that what a later pass changed on the object
# without changing its generator stays visible instead of being absorbed.
_RELABEL_WHY = (
    "RELABELLED 2026-09-04. This row previously read as an EXCLUSION on an outcome ground. "
    "Cochrane Handbook 6.5 section 3.2.4 cautions against making ELIGIBILITY depend on which "
    "outcomes a study reported, because that admits selective-outcome-reporting bias, and this "
    "object cited 3.2.4 against itself while doing exactly that. The criterion is retained "
    "unchanged -- what changes is what it DECIDES: it decides whether a trial CONTRIBUTES TO A "
    "GIVEN OUTCOME, not whether the trial is eligible for the review. The exclusion reason is "
    "carried forward verbatim below rather than rewritten. NO POOL CHANGED: this trial was not "
    "in any pool before this relabelling and is not in one after it, and re-inclusion is a "
    "separate decision requiring recomputation.")


def _relabelled(note, basis="INFERRED"):
    return {"verdict": "ELIGIBLE_OUTCOME_UNAVAILABLE", "criterion": "",
            "verdict_changed_2026_09_04": {"from": "EXCLUDED",
                                           "to": "ELIGIBLE_OUTCOME_UNAVAILABLE",
                                           "why": _RELABEL_WHY, "note": note,
                                           "pool_effect": "NONE."},
            "criterion_superseded_2026_09_04": "OUTCOME",
            "contribution_axis": "OUTCOME",
            "eligibility_basis": basis,
            "contributes_to_outcomes": []}


CORRECTIONS_2026_09_04 = {
 "NCT03074591": {"correction_2026_09_04": {
   "what_was_wrong": "the stated reason, not the verdict alone",
   "false_text_verbatim": "Primary 'exercise capacity' is not one of this object's estimands.",
   "why_it_was_wrong": "it read outcomesModule.primaryOutcomes[].measure (the TITLE) and never "
                       "the `description` on the same record",
   "class": "TITLE-WITHOUT-DESCRIPTION"}},
 "NCT01922479": {"correction_2026_09_04": {
   "what_was_wrong": "the stated reason",
   "false_text_verbatim": "A pilot whose primary is not one of this object's estimands.",
   "why_it_was_wrong": "the registered primary IS a change in six-minute walk distance, at both "
                       "title and description level; the row named no outcome and checked "
                       "neither field",
   "class": "TITLE-WITHOUT-DESCRIPTION (here: NEITHER-FIELD-READ)"}},
 "NCT05816265": {"correction_2026_09_04": {
   "what_was_wrong": "the stated reason, not the disposition",
   "false_text_verbatim": "Exercise capacity; no shared estimand.",
   "why_it_was_wrong": "'no shared estimand' was asserted flatly from a title, and a 6-minute "
                       "walk test IS administered at secondary rank -- visible only in a "
                       "description the row never read. The disposition survives on the primary "
                       "and on n=6.",
   "disposition_effect": "NONE. Still ELIGIBLE_NOT_POOLABLE.",
   "class": "TITLE-WITHOUT-DESCRIPTION (right answer, unchecked reason)"}},
 "NCT00821717": {"correction_2026_09_04": {
   "what_was_wrong": "the stated reason",
   "false_text_verbatim": "Primary is exercise capacity and cardiac function -- a unit of "
                          "analysis matching none of this object's six pools.",
   "why_it_was_wrong": "the registered co-primary is six-minute walk distance at week 24, which "
                       "is one of this object's six",
   "class": "TITLE-WITHOUT-DESCRIPTION (here: NEITHER-FIELD-READ)"}},
}


OBJECT_STATE_2026_09_04 = {
 "NCT02737995": _relabelled("Skeletal-muscle metabolism, n=8."),
 "NCT03871699": _relabelled("Intra-myocardial iron load by imaging, n=20."),
 "NCT04945707": _relabelled("Mechanisms of exercise intolerance. FDI vs placebo, n=65."),
 "NCT03218384": _relabelled("Post-exercise phosphocreatine recovery by 31P MRS."),
 "NCT03991000": _relabelled("iCHF-2: LVEF and atrial-fibrillation burden. n=8, TERMINATED."),
 "NCT01978028": _relabelled("Mitochondrial function. n=20, TERMINATED."),
 "NCT01837082": _relabelled("iCHF: change in LVEF. n=18, TERMINATED."),
 "NCT00520780": dict(_relabelled(
    "Restores this row to what its own generator, scripts/screen_ivi_remainder.py, says: "
    "ELIGIBLE_NOT_POOLABLE, 'meets P/I/C', 'ELIGIBLE AND NOT POOLED IS THE CORRECT READING -- "
    "recording a landmark trial as excluded would misstate why it is absent.' The stored row "
    "read EXCLUDED / OUTCOME. It is the only one of 29 rows that diverges from the script, and "
    "the block's own stored tally (EXCLUDED: 13) still counts the script's version rather than "
    "the 14 the stored rows contain.", basis="MEASURED"),
   reason=(
    "FAIR-HF, n=456, COMPLETED -- the trial that established FCM in heart failure. FCM vs normal "
    "saline; meets P/I/C, but its registered primaries are patient global assessment plus NYHA "
    "class and it designates no clinical-event endpoint. This review holds a walk-distance "
    "estimand and the trial reports improvement on that test, but the staged abstract prints no "
    "between-arm difference, dispersion term or interval for walk distance, so there is no "
    "extractable cell for that estimand. EXCLUDED ON OUTCOME is the correct reading.")),
 "NCT03380520": {"criterion": "POPULATION+OUTCOME",
                 "criterion_corrected_2026_09_04": {
                   "was": "OUTCOME",
                   "why": "screening.records[6] records this trial (IRON-CRT 2021) as failing "
                          "POPULATION as well as the outcome axis. This row named only OUTCOME, "
                          "so the two surfaces disagreed about why the same trial is out. It "
                          "stays EXCLUDED -- it is the population ground that keeps it out, and "
                          "that ground survives the ELIGIBLE_OUTCOME_UNAVAILABLE decomposition "
                          "entirely."}},
}
# =========================================================================================

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
    "field_read_provenance_2026_09_04": (
        "READ THIS BEFORE TRUSTING ANY `field_read` VALUE IN THIS BLOCK. No line in "
        "scripts/screen_ivi_remainder.py reads ClinicalTrials.gov. `D` is a hard-coded literal "
        "list and each `field_read` value was TYPED BY ITS AUTHOR, not returned by a read. The "
        "reader's page renders it in a cell headed 'Field read', so a hand-typed label there is "
        "a claim about provenance made in the one place a reader goes to check provenance. "
        "WHAT `field_read` MEANS HERE, AS OF THIS CORRECTION: the field the DECISION TURNS ON. "
        "It does not assert that this script performed a read. "
        "WHERE A READ WAS ACTUALLY PERFORMED: the three rows carrying "
        "`registry_measured_2026_09_04` were re-read from the ClinicalTrials.gov v2 API on "
        "2026-09-04 and store the verbatim `measure` and `description` strings, so they can be "
        "checked without a network call. The other 26 rows were not re-read and now say so "
        "rather than implying otherwise. "
        "WHY THE FIELD WAS MADE HONEST RATHER THAN THE READ MADE REAL: making the read real "
        "means re-running this screen live, which rewrites 29 already-served rows from a script "
        "whose author-time reads are undated and unrecoverable. That is a larger change than a "
        "provenance correction is authorised to make, and this environment has no network, so "
        "it could be neither executed nor verified here."),
    "title_without_description_sweep_2026_09_04": {
        "defect": (
            "a screening reason that characterises a trial's outcome from "
            "outcomesModule.primaryOutcomes[].measure -- the TITLE -- without reading "
            "`description` on the same record. The registry title of FAIR-HFpEF's primary is "
            "the two words 'exercise capacity'; the description on the same record is 'The "
            "difference of 6-minute walking distance in meters from baseline to week 24 ...'."),
        "why_it_is_a_class_and_not_an_incident": (
            "this object had ALREADY self-corrected this exact defect on the sibling trial "
            "FAIR-HF -- see screening.records[0], 'an earlier version of this row went further "
            "and said it can contribute to NONE of this review's estimands, which is false' -- "
            "and never swept it to FAIR-HFpEF nine rows away in this block, nor to EFFICACY-HF "
            "and PRACTICE-ASIA-HF in the same block. A repair applied to the reported instance "
            "and not to the class is how the second, third and fourth instances survived."),
        "swept": "every screening/eligibility row across ssot/*/*.json and scripts/screen_*.py "
                 "whose stated reason turns on a registered outcome, on 2026-09-04",
        "population_N": 158,
        "population_N_means": "rows, across 15 files, whose stated disposition rests on what the "
                              "trial's registered outcome IS",
        "of_which_rest_on_a_TITLE": 106,
        "contradicted_by_their_own_record": 5,
        "contradicted_in_this_object": ["NCT03074591", "NCT01922479", "NCT00821717"],
        "contradicted_elsewhere": ["NCT02524106 in bococizumab-lipid-review",
                                   "NCT04649801 in ablation-af-heart-failure"],
        "test": "scripts/test_screen_reason_vs_registry_description.py -- fixture-backed, no "
                "network at test time",
        "what_the_sweep_does_NOT_establish": (
            "that the remaining 101 title-resting rows are right. It establishes that their own "
            "registry descriptions do not contradict them. A row can rest on a title, agree "
            "with its description, and still be wrong about the review's estimand.")},
    "mirror_drift_2026_09_04": (
        "OBJECT_STATE_2026_09_04 above carries nine rows that a separate same-day pass changed "
        "on ssot/iv-iron-hf/iv-iron-hf.json WITHOUT changing this generator. Until that overlay "
        "was added, re-running main() would have reverted the relabelling of eight rows from "
        "ELIGIBLE_OUTCOME_UNAVAILABLE back to EXCLUDED. A generator that no longer produces its "
        "own object is not a mirror, and a stale mirror is a loaded gun: it looks authoritative "
        "and it undoes work when fired."),
    "trials": [dict(dict(dict({"nct": n, "verdict": v, "criterion": c, "field_read": f,
                               "reason": r}, **(x[0] if x else {})),
                         **CORRECTIONS_2026_09_04.get(n, {})),
                    **OBJECT_STATE_2026_09_04.get(n, {}))
               for n, v, c, f, r, *x in D],
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

    # -----------------------------------------------------------------------------------
    # REFUSE TO SILENTLY REVERT A ROW THE OBJECT HOLDS AND THIS TABLE DOES NOT.
    #
    # `scr["iv_iron_2026_08_19"] = BLOCK` is a whole-block replacement, and the ADDS-only
    # assertion below only ever checked that no KEY disappeared -- it says nothing about the
    # contents of the key it overwrites. That is how this defect survived: on some date after
    # 2026-08-19 the FAIR-HF row on the object was changed to EXCLUDED / OUTCOME by a direct
    # edit, this script kept its own ELIGIBLE_NOT_POOLABLE reading, and a re-run would have
    # reverted the object to the script's reading WITHOUT PRINTING ANYTHING. The stale tally
    # was the only visible trace, and it was visible only to someone counting by hand.
    #
    # THE SCRIPT IS NOT THE SOURCE OF THE OBJECT AND MUST NOT ASSUME IT IS. Measured
    # 2026-09-04 across the corpus: of 20 NCT-bearing screening row-blocks on the ssot topic
    # objects, only 9 have any .py file in the repo containing all of their trial ids at all,
    # covering 167 of 1068 rows. The objects are hand-authored more often than they are
    # generated. A build script that overwrites one without looking is a revert waiting for a
    # re-run.
    #
    # So: compare first, refuse on divergence, and make the operator say which reading wins.
    # -----------------------------------------------------------------------------------
    existing = scr.get("iv_iron_2026_08_19")
    if isinstance(existing, dict) and isinstance(existing.get("trials"), list):
        on_object = {r.get("nct"): r for r in existing["trials"] if isinstance(r, dict)}
        drift = []
        for row in BLOCK["trials"]:
            cur = on_object.get(row["nct"])
            if cur is None:
                drift.append((row["nct"], "ABSENT FROM THE OBJECT", "", ""))
                continue
            for field in ("verdict", "criterion", "field_read", "reason"):
                if cur.get(field) != row[field]:
                    drift.append((row["nct"], field, cur.get(field), row[field]))
        extra = [n for n in on_object if n not in {r["nct"] for r in BLOCK["trials"]}]
        for n in extra:
            drift.append((n, "ON THE OBJECT, NOT IN THIS TABLE", "", ""))
        if drift and os.environ.get("OVERWRITE_SCREENING") != "iv_iron_2026_08_19":
            print("REFUSED: the object's screening rows DIFFER from this script's table, and")
            print("overwriting would revert them silently. %d difference(s):" % len(drift))
            for nct, field, was, now in drift:
                print("  %s  %s" % (nct, field))
                if was or now:
                    print("      ON THE OBJECT : %s" % (str(was)[:300],))
                    print("      THIS SCRIPT   : %s" % (str(now)[:300],))
            print()
            print("DECIDE WHICH READING IS RIGHT, IN WRITING, BEFORE EITHER IS OVERWRITTEN.")
            print("  the object is right  -> correct the table in this file and RETRACT the")
            print("                          losing text in place; do not delete it")
            print("  this script is right -> re-run with")
            print("                          OVERWRITE_SCREENING=iv_iron_2026_08_19")
            print("and record on the object WHY, because a reader who saw the old reading is")
            print("owed the retraction, not just the new value.")
            return 1

    scr["iv_iron_2026_08_19"] = BLOCK
    assert before <= set(scr.keys()), "ADDS only"
    with io.open(OBJ, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(obj, indent=1, ensure_ascii=False) + "\n")
    for k, v in sorted(tally.items()):
        print("  %-26s %d" % (k, v))
    print("  %-26s %d" % ("TOTAL", sum(tally.values())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
