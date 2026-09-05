#!/usr/bin/env python3
"""SEPARATE THE LABEL FROM THE INCLUSION: introduce ELIGIBLE_OUTCOME_UNAVAILABLE.

WHAT THIS DOES, AND THE ONE THING IT MUST NOT DO
------------------------------------------------
A row that reads EXCLUDED tells a reader the trial DID NOT QUALIFY. For a trial
that meets population, intervention, comparator and design and merely has no
extractable cell for a given endpoint, that is false, and it is false in the
direction that closes the question. ELIGIBLE_OUTCOME_UNAVAILABLE says the true
thing instead: it qualified, and we hold nothing from it for this endpoint. That
is checkable, and it invites the reader to go and find the number.

THIS SCRIPT CHANGES LABELS. IT CHANGES NO POOL. Nothing under `results`,
`inputs`, or any `pooled` block is written by this script; `assert_pooled_frozen`
below reads every `results.by_outcome[*].pooled` before and after and refuses to
write if a single point or bound moved. Re-including a trial is a DIFFERENT
decision that requires recomputation, review and a rebuild, and it is not taken
here.

WHY THE SET IS SMALLER THAN "EVERY ROW WHOSE AXIS SAYS OUTCOME"
---------------------------------------------------------------
279 rows across 4 objects carry an outcome-shaped exclusion axis. Only 17 of them
are relabelled, and the arithmetic for every exclusion is recorded in
`SKIPPED_WITH_REASON` and written onto the objects, because a silent skip is the
defect this exercise exists to remove.

  MIXED AXIS -- the row names an outcome axis AND population or comparator. The
  trial is not eligible, so the new verdict would be a false claim about it.
  (iv-iron-hf IRON-CRT; arni-hfref PARADISE-MI.)

  BIBLIOGRAPHIC RECORDS, NOT TRIAL DISPOSITIONS -- arni-hfref's 423-record
  title/abstract screen carries 131 exclusions on the OUTCOME axis. A TiAb record
  is a RECORD: most of these are sub-studies, association analyses and quality-of-
  life papers, and the review has never assessed them on P/I/C. Asserting they
  "meet population, intervention, comparator and design" would be an invention,
  not a relabelling.

  CHECK-ORDER ARTEFACTS -- bempedoic-acid-review's own
  `screening_of_remainder.restated_two_axis_2026_08_19` already establishes that
  of its 13 rows whose limb reads OUTCOME, ELEVEN also fail population or
  comparator: "the limb it REPORTED was determined by CHECK ORDER rather than by
  the trial". Two are genuinely eligible. Those two are relabelled; the other
  eleven get their limb CORRECTED to the axis that object already knows, which
  removes a contradiction between two of its own surfaces.

  MIS-ATTRIBUTED AXIS -- sotagliflozin-hf's SOTA-P-CARDIA row is filed under
  `outcome_not_this_review's`, but that object's eligibility says in terms that it
  "does NOT turn on which analysis a trial reported", and the row's own prose says
  the trial "is NOT part of the pivotal programme this object is scoped to". The
  ground is SCOPE. The row stays excluded and its axis is corrected to say so.

A REGRESSION THIS PASS FOUND AND REVERSES
------------------------------------------
`scripts/screen_ivi_remainder.py` is the generator of iv-iron-hf's 29-trial
remainder block. Its FAIR-HF row reads ELIGIBLE_NOT_POOLABLE and says so at
length: "ELIGIBLE AND NOT POOLED IS THE CORRECT READING -- recording a landmark
trial as 'excluded' would misstate why it is absent." The STORED object reads
EXCLUDED / OUTCOME. Exactly one of 29 rows diverges from its own generator, and
the object's own stored `tally` still counts 13 EXCLUDED against the 14 its rows
now contain -- mechanical confirmation that the row was flipped after the tally
was written, by hand, away from the script. Relabelling restores the generator's
reading.

USAGE
    python ssot/relabel_outcome_verdict_2026_09_04.py --check   # report, write nothing
    python ssot/relabel_outcome_verdict_2026_09_04.py --apply
Idempotent: applying twice is a no-op and reports zero changes.
"""
import argparse
import copy
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")
DATE = "2026-09-04"
VERDICT = "ELIGIBLE_OUTCOME_UNAVAILABLE"

VERDICT_MEANS = (
    "This trial meets this review's population, intervention, comparator and "
    "design criteria. It contributes no usable result to this outcome. That is a "
    "statement about what we hold, not about whether the trial qualified -- and it "
    "is deliberately NOT 'excluded', because 'excluded' tells a reader the trial "
    "did not qualify and closes a question this verdict leaves open."
)

WHY_RELABELLED = (
    "RELABELLED " + DATE + ". This row previously read as an EXCLUSION on an "
    "outcome ground. Cochrane Handbook 6.5 section 3.2.4 cautions against making "
    "ELIGIBILITY depend on which outcomes a study reported, because that admits "
    "selective-outcome-reporting bias, and this object cited 3.2.4 against itself "
    "while doing exactly that. The criterion is retained unchanged -- what changes "
    "is what it DECIDES: it decides whether a trial CONTRIBUTES TO A GIVEN "
    "OUTCOME, not whether the trial is eligible for the review. The exclusion "
    "reason is carried forward verbatim below rather than rewritten. NO POOL "
    "CHANGED: this trial was not in any pool before this relabelling and is not in "
    "one after it, and re-inclusion is a separate decision requiring recomputation."
)


# ---------------------------------------------------------------- the row sets
# Each entry: (object_id, json_path, expectations, evidence-for-eligibility).
# `pic_basis` is the honest provenance of the claim that P/I/C hold, and it is
# written onto the row. MEASURED = another surface of this same object states it
# in terms. INFERRED = this screen's convention is to name every failing axis it
# finds (it does so on other rows, e.g. "INTERVENTION+STATUS"), so a single named
# axis implies the others passed -- an inference from convention, not a reading.

IVI = "iv-iron-hf"
IVI_REM = ("screening_of_remainder", "iv_iron_2026_08_19", "trials")

IVI_RECORDS = [
    # (index, trial, pic_basis, what_it_does_report)
    (0, "FAIR-HF", "MEASURED",
     "Six-minute walk distance: its registry names exercise tolerance measured by "
     "the six-minute walk test among its key secondary efficacy objectives and its "
     "abstract reports a significant improvement on that test. This review holds a "
     "walk-distance estimand. What is missing is the CELL, not the endpoint: the "
     "staged abstract prints no between-arm difference, dispersion term or "
     "interval. A lane that obtains the full text could close this gap.",
     "This object's own remainder screen (NCT00520780) and its generator "
     "scripts/screen_ivi_remainder.py both state 'meets P/I/C' for this trial."),
    (1, "EFFECT-HF", "MEASURED",
     "Change in peak oxygen consumption at 24 weeks -- a continuous "
     "exercise-capacity endpoint. Not poolable with six_min_walk_24w: peak VO2 and "
     "six-minute walk distance are different quantities in different units.",
     "This object's remainder screen already records NCT01394562 as "
     "ELIGIBLE_NOT_POOLABLE: 'FCM vs standard of care -- the usual care half of the "
     "comparator criterion admits it, which is why that half is load-bearing.' The "
     "screening record said EXCLUDED for the same trial. The two surfaces "
     "contradicted each other and this relabelling resolves them onto the "
     "remainder screen's reading."),
    (4, "PRACTICE-ASIA-HF 2018", "MEASURED",
     "Not established here; the trial's own report is not staged. Graham 2023's "
     "Table 1 records no cardiovascular-mortality outcome for it.",
     "This object's remainder screen already records NCT01922479 as "
     "ELIGIBLE_NOT_POOLABLE: 'PRACTICE-ASIA-HF. FCM vs placebo, n=50, COMPLETED. A "
     "pilot whose primary is not one of this object's estimands.' Same "
     "two-surface contradiction as EFFECT-HF, resolved the same way."),
    (5, "Dhoot 2020", "INFERRED_FROM_PRIOR_SYNTHESIS_TABLE",
     "Not established here; the trial's own report is not staged.",
     "P/I/C rest on Graham 2023's characteristics table, NOT on the trial's own "
     "report, exactly as this row's own record_limitation already says. The "
     "eligibility claim in this verdict is therefore weaker than for the rows "
     "above, and that is stated rather than levelled up."),
]

IVI_REMAINDER = [
    # (nct, pic_basis, note)
    ("NCT00520780", "MEASURED",
     "Restores this row to what its own generator, scripts/screen_ivi_remainder.py, "
     "says: ELIGIBLE_NOT_POOLABLE, 'meets P/I/C', 'ELIGIBLE AND NOT POOLED IS THE "
     "CORRECT READING -- recording a landmark trial as excluded would misstate why "
     "it is absent.' The stored row read EXCLUDED / OUTCOME. It is the only one of "
     "29 rows that diverges from the script, and the block's own stored tally "
     "(EXCLUDED: 13) still counts the script's version rather than the 14 the "
     "stored rows contain."),
    ("NCT02737995", "INFERRED", "Skeletal-muscle metabolism, n=8."),
    ("NCT03871699", "INFERRED", "Intra-myocardial iron load by imaging, n=20."),
    ("NCT04945707", "INFERRED", "Mechanisms of exercise intolerance. FDI vs placebo, n=65."),
    ("NCT03218384", "INFERRED", "Post-exercise phosphocreatine recovery by 31P MRS."),
    ("NCT03991000", "INFERRED", "iCHF-2: LVEF and atrial-fibrillation burden. n=8, TERMINATED."),
    ("NCT01978028", "INFERRED", "Mitochondrial function. n=20, TERMINATED."),
    ("NCT01837082", "INFERRED", "iCHF: change in LVEF. n=18, TERMINATED."),
]

# Rows this pass deliberately does NOT relabel, with the ground for each. Written
# onto the objects so the skip is countable rather than invisible.
SKIPPED_WITH_REASON = {
    IVI: [
        {"row": "screening.records[6] / screening_of_remainder[14]",
         "trial": "IRON-CRT 2021 (NCT03380520)",
         "kept_verdict": "EXCLUDED",
         "why": "MIXED AXIS. This trial fails POPULATION as well as the outcome "
                "axis -- screening.records[6] lists both. It is not eligible, so "
                "ELIGIBLE_OUTCOME_UNAVAILABLE would be a false claim about it. The "
                "remainder row named only OUTCOME and has been corrected to name "
                "both, which removes a disagreement between two of this object's "
                "own surfaces."}],
    "arni-hfref": [
        {"row": "screening.records[1]", "trial": "PARADISE-MI (NCT02924727)",
         "kept_verdict": "excluded",
         "why": "MIXED AXIS. Fails population (acute myocardial infarction, not "
                "chronic HFrEF) and comparator (ramipril, not enalapril) as well as "
                "outcome."},
        {"row": "screening.corpus[*] (TiAb stage)", "trial": "131 records",
         "kept_verdict": "exclude",
         "why": "NOT TRIAL-LEVEL DISPOSITIONS. These are title/abstract "
                "bibliographic records, and the great majority are sub-studies, "
                "association analyses and quality-of-life papers rather than "
                "independent trials. This review has assessed none of them on "
                "population, intervention or comparator, so no verdict asserting "
                "they meet those criteria can be written from what this object "
                "holds. 24 of them ARE registry records for standalone trials, and "
                "those are the countable, revisitable part of this gap: they are "
                "listed in `outcome_axis_gap_2026_09_04.registry_records_not_yet_"
                "reassessed` and a lane that assesses them on P/I/C could relabel "
                "them. THE GAP IS RECORDED RATHER THAN CLOSED BY ASSERTION."},
        {"row": "screening.corpus (FullText, PMID 29431251)",
         "trial": "PARADIGM-HF recurrent-events analysis",
         "kept_verdict": "exclude",
         "why": "NOT A SEPARATE TRIAL. A secondary analysis of a trial this review "
                "already includes. Relabelling it as an eligible trial would "
                "double-count the trial in the eligibility ledger."}],
}


def _get(node, path):
    for k in path:
        node = node[k]
    return node


def load(obj_id):
    p = os.path.join(SSOT, obj_id, obj_id + ".json")
    raw = open(p, encoding="utf-8").read()
    return p, raw, json.loads(raw)


def dump(path, raw, data):
    """Write with the byte-shape the file already had.

    Every canonical object in this store round-trips EXACTLY under
    indent=1/ensure_ascii=False, verified before this script was written. Writing
    with any other setting would reformat 500KB and bury the change.
    """
    out = json.dumps(data, indent=1, ensure_ascii=False)
    if raw.endswith("\n"):
        out += "\n"
    open(path, "w", encoding="utf-8", newline="").write(out)


def pooled_snapshot(data):
    """Every served pooled point and interval, keyed by outcome.

    This is the quantity the whole exercise promises not to move.
    """
    by = ((data.get("results") or {}).get("by_outcome") or {})
    snap = {}
    if isinstance(by, dict):
        items = by.items()
    else:
        items = ((str(i), v) for i, v in enumerate(by))
    for k, v in items:
        if isinstance(v, dict) and "pooled" in v:
            snap[k] = copy.deepcopy(v["pooled"])
    return snap


def assert_pooled_frozen(obj_id, before, after):
    if before != after:
        moved = [k for k in set(before) | set(after)
                 if before.get(k) != after.get(k)]
        raise SystemExit(
            "REFUSING TO WRITE %s: a pooled estimate moved under a RELABELLING "
            "migration, on outcome(s) %s. A relabelling that changes a number is "
            "not a relabelling." % (obj_id, ", ".join(sorted(moved))))


# --------------------------------------------------------------- row rewriting
def relabel_record(row, pic_basis, reports, evidence):
    """A screening.records row. Returns True if it changed."""
    if row.get("verdict") == VERDICT:
        return False
    row["verdict"] = VERDICT
    row["verdict_means"] = VERDICT_MEANS
    row["verdict_changed_" + DATE.replace("-", "_")] = {
        "from": "EXCLUDED (implied by criteria_failed; this row carried no "
                "verdict field, and the renderer read the presence of "
                "criteria_failed as an exclusion)",
        "to": VERDICT,
        "why": WHY_RELABELLED,
        "pool_effect": "NONE. This trial was in no pool before and is in none "
                       "after.",
    }
    # The old axis is RETRACTED IN PLACE, not deleted: it moves to a dated
    # superseded field and the live field is emptied, so the page cannot print
    # "eligible" over a list of failed criteria.
    row["criteria_failed_superseded_" + DATE.replace("-", "_")] = {
        "was": list(row.get("criteria_failed") or []),
        "why": "The outcome axis is retained as a CONTRIBUTION axis below. It is "
               "removed from criteria_failed because that field is what this "
               "review's own surfaces read as 'did not qualify'.",
    }
    row["criteria_failed"] = []
    row["contribution_axis"] = "OUTCOME"
    row["eligibility_axes_met"] = ["POPULATION", "INTERVENTION", "COMPARATOR", "DESIGN"]
    row["eligibility_basis"] = pic_basis
    row["eligibility_basis_evidence"] = evidence
    row["what_it_does_report"] = reports
    row["contributes_to_outcomes"] = []
    return True


def relabel_remainder(row, pic_basis, note):
    if row.get("verdict") == VERDICT:
        return False
    row["verdict_changed_" + DATE.replace("-", "_")] = {
        "from": row.get("verdict"), "to": VERDICT, "why": WHY_RELABELLED,
        "note": note,
        "pool_effect": "NONE.",
    }
    row["verdict"] = VERDICT
    row["criterion_superseded_" + DATE.replace("-", "_")] = row.get("criterion")
    row["criterion"] = ""
    row["contribution_axis"] = "OUTCOME"
    row["eligibility_basis"] = pic_basis
    row["contributes_to_outcomes"] = []
    return True


# ------------------------------------------------------------------- iv-iron-hf
def migrate_iv_iron(check):
    path, raw, d = load(IVI)
    before = pooled_snapshot(d)
    changed = []

    recs = d["screening"]["records"]
    for idx, trial, basis, reports, evidence in IVI_RECORDS:
        row = recs[idx]
        assert row["trial"] == trial, "row %d is %r, expected %r" % (
            idx, row.get("trial"), trial)
        if relabel_record(row, basis, reports, evidence):
            changed.append("screening.records[%d] %s" % (idx, trial))

    # The mirror array. `screening.excluded` restates the same dispositions and
    # would otherwise contradict the records it mirrors. The contradicting-
    # surfaces gate exempts a DECLARED, DATED supersession, which is what this is.
    relabelled_trials = {t for _, t, _, _, _ in IVI_RECORDS}
    for e in d["screening"]["excluded"]:
        name = e.get("reason", "").split(" -- ")[0]
        if name in relabelled_trials and not e.get("superseded_" + DATE.replace("-", "_")):
            e["superseded_" + DATE.replace("-", "_")] = {
                "was": e["reason"],
                "now": "%s -- %s" % (name, VERDICT),
                "why": WHY_RELABELLED,
                "where_the_live_row_is": "screening.records",
            }
            e["reason"] = "%s -- %s (was: %s)" % (name, VERDICT, e["reason"])
            changed.append("screening.excluded[%s]" % name)

    trials = _get(d, IVI_REM)
    byn = {t["nct"]: t for t in trials}
    for nct, basis, note in IVI_REMAINDER:
        if relabel_remainder(byn[nct], basis, note):
            changed.append("screening_of_remainder %s" % nct)

    # IRON-CRT: not relabelled, but its remainder row named one axis while
    # screening.records[6] names two. Correct the row to agree with the object.
    icrt = byn["NCT03380520"]
    key = "criterion_corrected_" + DATE.replace("-", "_")
    if key not in icrt:
        icrt[key] = {
            "was": icrt["criterion"],
            "why": "screening.records[6] records this trial (IRON-CRT 2021) as "
                   "failing POPULATION as well as the outcome axis. This row named "
                   "only OUTCOME, so the two surfaces disagreed about why the same "
                   "trial is out. It stays EXCLUDED -- it is the population ground "
                   "that keeps it out, and that ground survives the "
                   + VERDICT + " decomposition entirely.",
        }
        icrt["criterion"] = "POPULATION+OUTCOME"
        changed.append("screening_of_remainder NCT03380520 (axis corrected, still EXCLUDED)")

    # The stored tally is recomputed from the rows it claims to count. It was
    # already wrong before this pass: it said EXCLUDED 13 while the rows held 14.
    blk = _get(d, IVI_REM[:-1])
    tally = {}
    for t in trials:
        tally[t["verdict"]] = tally.get(t["verdict"], 0) + 1
    if blk.get("tally") != tally:
        blk["tally_superseded_" + DATE.replace("-", "_")] = {
            "was": blk.get("tally"),
            "why": "Recomputed from the rows. The stored value disagreed with the "
                   "stored rows BEFORE this pass -- it counted 13 EXCLUDED against "
                   "14 rows -- which is how the hand-edit of the FAIR-HF row away "
                   "from its generator was detected.",
        }
        blk["tally"] = tally
        changed.append("screening_of_remainder tally recomputed -> %s" % tally)

    # The eligibility declaration. RETRACTED IN PLACE, with the date and the
    # reason, and the original kept verbatim beside it.
    sc = d["screening"]
    ekey = "eligibility_superseded_" + DATE.replace("-", "_")
    if ekey not in sc:
        sc[ekey] = {
            "was": sc["eligibility"],
            "retracted_utc": DATE,
            "why": "The passage stated that ELIGIBILITY turns on outcome as well as "
                   "on population, intervention, comparator and route. That is the "
                   "practice Cochrane Handbook 6.5 section 3.2.4 cautions against, "
                   "and this object cited 3.2.4 against itself while doing it. The "
                   "criterion itself is not withdrawn and is not weakened: what is "
                   "withdrawn is the claim about what it DECIDES. It decides "
                   "CONTRIBUTION TO A GIVEN OUTCOME. Eleven named trials that this "
                   "review had recorded as excluded are eligible and are now "
                   "recorded as " + VERDICT + ". No trial entered a pool as a "
                   "result and no pooled estimate moved.",
        }
        sc["eligibility"] = sc["eligibility"].replace(
            "ELIGIBILITY turns on population, intervention, comparator, route and "
            "outcome.",
            "ELIGIBILITY turns on population, intervention, comparator and route. "
            "[RESTATED " + DATE + ": this sentence read 'ELIGIBILITY turns on "
            "population, intervention, comparator, route and outcome' and the "
            "outcome clause is RETRACTED, not deleted -- the original stands "
            "verbatim under eligibility_superseded_" + DATE.replace("-", "_") + ". "
            "The outcome criterion below is UNCHANGED and is still applied; what "
            "changes is what it decides. It decides whether a trial CONTRIBUTES TO "
            "A GIVEN OUTCOME, not whether the trial is eligible for this review. "
            "Handbook 6.5 section 3.2.4 cautions against letting eligibility depend "
            "on which outcomes a study reported, because that admits selective-"
            "outcome-reporting bias; this object cited 3.2.4 against itself and now "
            "conforms to it. A trial that meets population, intervention, "
            "comparator and route and has no extractable cell for an endpoint is "
            "recorded as " + VERDICT + " and not as excluded.]")
        changed.append("screening.eligibility restated (retraction in place)")

    # The Handbook conformance passage, on the four outcomes that carry it. The
    # 3.2.4 SELF-CITATION IS KEPT WORD FOR WORD -- it is the most honest sentence
    # on the page and the only thing that made this defect findable.
    old_admission = (
        "Section 3.2.4 is cited for the caution it gives AGAINST making eligibility "
        "depend on which outcomes a study reported, AND because this review must be "
        "honest that it applies an outcome criterion at eligibility anyway: most of "
        "its screened-out records fail on that axis.")
    new_admission = (
        "Section 3.2.4 is cited for the caution it gives AGAINST making eligibility "
        "depend on which outcomes a study reported, AND because this review DID "
        "apply an outcome criterion at eligibility and said so here rather than "
        "hiding it. [RESTATED " + DATE + ": the sentence that followed read 'AND "
        "because this review must be honest that it applies an outcome criterion at "
        "eligibility anyway: most of its screened-out records fail on that axis.' "
        "It is retracted, not deleted -- the original stands verbatim under the "
        "dated superseded field on this outcome. The criterion is unchanged and "
        "still applied; it now decides CONTRIBUTION TO A GIVEN OUTCOME rather than "
        "eligibility, and the eleven trials it had removed from the review are "
        "recorded as " + VERDICT + ": eligible, and holding nothing this review can "
        "extract for the endpoint in question. NO POOL CHANGED. The self-citation "
        "above is kept word for word, because a review that cites the section it is "
        "breaking is the only kind that can be caught doing it.]")
    # The SAME passage names FAIR-HF three sentences later and says it is "out on
    # the clinical-event criterion". After the relabelling it is not out; it is in,
    # and holding nothing extractable. Leaving this sentence would put a fresh
    # contradiction two paragraphs below a retraction that exists to remove one.
    old_faihf = (
        "What this review DOES do, and an earlier version of this passage denied "
        "it, is exclude a trial that designates an endpoint this review holds but "
        "publishes no extractable estimate of it: the screened trial with a "
        "registered walk-distance secondary is out on the clinical-event criterion "
        "while the review carries a walk-distance estimand. That is a stricter rule "
        "than 3.2.4 requires, it is the review's own, and it is declared here rather "
        "than dressed as the Handbook's.")
    new_fairhf = (
        "What this review DID do, and two earlier versions of this passage first "
        "denied and then declared, is EXCLUDE a trial that designates an endpoint "
        "this review holds but publishes no extractable estimate of it: the screened "
        "trial with a registered walk-distance secondary was out on the clinical-"
        "event criterion while the review carries a walk-distance estimand. "
        "[RESTATED " + DATE + ": that sentence stood in the present tense and read "
        "'What this review DOES do ... is exclude a trial ... is out on the "
        "clinical-event criterion ... That is a stricter rule than 3.2.4 requires, "
        "it is the review's own, and it is declared here rather than dressed as the "
        "Handbook's.' It is retracted, not deleted; the original stands verbatim "
        "under the dated superseded field on this outcome. THAT TRIAL IS FAIR-HF AND "
        "IT IS NO LONGER EXCLUDED. It is recorded as " + VERDICT + ": it meets "
        "population, intervention, comparator and route, and the staged abstract "
        "prints no between-arm difference, dispersion term or interval for the walk "
        "distance, so there is no cell to extract. The stricter-than-3.2.4 rule is "
        "WITHDRAWN as a rule of ELIGIBILITY and retained as a rule of CONTRIBUTION, "
        "which is what it always did. Nothing entered the walk-distance pool and its "
        "estimate is unchanged.]")
    for oid, res in d["results"]["by_outcome"].items():
        hb = res.get("handbook") or {}
        conf = hb.get("conformance")
        skey = "conformance_superseded_" + DATE.replace("-", "_")
        if isinstance(conf, str) and old_faihf in conf and old_admission not in conf:
            # A conformance string carrying the FAIR-HF sentence but not the
            # eligibility admission. Two ways to arrive here: an outcome that never
            # carried the admission, or one where a first pass restated the
            # admission and this sentence was added to the script afterwards. In
            # the second case the superseded record ALREADY HOLDS THE TRUE
            # ORIGINAL and must not be overwritten with the half-edited string.
            if skey not in hb:
                hb[skey] = {
                    "was": conf, "retracted_utc": DATE,
                    "why": "Said FAIR-HF is out on the clinical-event criterion. It "
                           "is not out; it is " + VERDICT + ".",
                }
            hb["conformance"] = conf.replace(old_faihf, new_fairhf)
            changed.append("results.by_outcome[%s].handbook.conformance "
                           "(FAIR-HF sentence) restated" % oid)
            continue
        if isinstance(conf, str) and old_admission in conf:
            # `was` is the TRUE original, captured before either replacement. A
            # supersession record that stores a half-edited string is worse than
            # none: it looks like provenance and is not.
            hb[skey] = {
                "was": conf, "retracted_utc": DATE,
                "why": "Stated that this review applies an outcome criterion AT "
                       "ELIGIBILITY, and said three sentences later that FAIR-HF is "
                       "out on the clinical-event criterion. It applies the criterion "
                       "at CONTRIBUTION, and FAIR-HF is not out. Both retracted in "
                       "place; the Handbook 3.2.4 self-citation is preserved.",
            }
            hb["conformance"] = (conf.replace(old_admission, new_admission)
                                     .replace(old_faihf, new_fairhf))
            changed.append("results.by_outcome[%s].handbook.conformance restated" % oid)

    # DISTINCT TRIALS, NOT DISTINCT ROWS. FAIR-HF is relabelled on two surfaces --
    # screening.records under its trial name and the remainder screen under
    # NCT00520780 -- and a naive union of the two identifier spaces counts it
    # twice. The first version of this block reported 12 for what is 11 trials,
    # which is the same class of error as counting a mirror row as a second
    # exclusion.
    same_trial = {"NCT00520780": "FAIR-HF"}
    relabelled_names = sorted({t for _, t, _, _, _ in IVI_RECORDS}
                              | {same_trial.get(n, n) for n, _, _ in IVI_REMAINDER})
    ident_note = (
        "FAIR-HF appears on two surfaces of this object -- screening.records by "
        "name, screening_of_remainder by NCT00520780. It is ONE trial and is counted "
        "once here. 14 ROWS were relabelled across the corpus; 11 TRIALS were, and "
        "all 11 are in this object.")
    gapkey = "outcome_axis_gap_" + DATE.replace("-", "_")
    _ex = d.get(gapkey)
    if isinstance(_ex, dict) and _ex.get("n_trials_relabelled") != len(relabelled_names):
        _ex["n_trials_relabelled_superseded_" + DATE.replace("-", "_")] = {
            "was": _ex.get("n_trials_relabelled"),
            "why": "Counted ROWS across two identifier spaces rather than TRIALS. "
                   "FAIR-HF was counted twice.",
        }
        changed.append("%s: trial count corrected %s -> %d"
                       % (gapkey, _ex.get("n_trials_relabelled"), len(relabelled_names)))
        _ex["trials_relabelled"] = relabelled_names
        _ex["n_trials_relabelled"] = len(relabelled_names)
        _ex["identifier_note"] = ident_note
    if gapkey not in d:
        d[gapkey] = {
            "identifier_note": ident_note,
            "what_this_is": "The decomposition of 'excluded on an outcome ground' "
                            "into ELIGIBLE + OUTCOME-UNAVAILABLE, made countable. "
                            "Each trial below is one the review qualified and holds "
                            "nothing from for the endpoint named. That is a gap a "
                            "reader can go and close, which is the point of not "
                            "calling it an exclusion.",
            "trials_relabelled": relabelled_names,
            "n_trials_relabelled": len(relabelled_names),
            "pool_effect": "NONE. Every pooled point and interval in "
                           "results.by_outcome is byte-identical before and after, "
                           "enforced by assert_pooled_frozen in the migration and "
                           "by tests/test_relabel_pooled_invariance.py.",
            "what_this_does_not_do": "It does not re-include any trial. Re-inclusion "
                                     "changes results and needs extraction, "
                                     "recomputation, review and a rebuild. This "
                                     "makes that decision measurable per trial "
                                     "instead of architectural.",
            "not_relabelled": SKIPPED_WITH_REASON[IVI],
        }
        changed.append(gapkey)

    after = pooled_snapshot(d)
    assert_pooled_frozen(IVI, before, after)
    if changed and not check:
        dump(path, raw, d)
    return changed


# --------------------------------------------------------- bempedoic-acid-review
def migrate_bempedoic(check):
    obj_id = "bempedoic-acid-review"
    path, raw, d = load(obj_id)
    before = pooled_snapshot(d)
    changed = []
    sor = d["screening_of_remainder"]
    # This object ALREADY holds the two-axis truth per trial. Read it; do not
    # re-derive it.
    restated = {r["nct"]: r for r in sor["restated_two_axis_2026_08_19"]["rows"]}
    for row in sor["rows"]:
        nct = row["nct"]
        rst = restated.get(nct)
        if not rst or row.get("failing_limb") != "OUTCOME":
            continue
        if rst["eligibility"] == "ELIGIBLE":
            if row.get("verdict") == VERDICT:
                continue
            row["verdict_changed_" + DATE.replace("-", "_")] = {
                "from": row.get("verdict"), "to": VERDICT, "why": WHY_RELABELLED,
                "pool_effect": "NONE. k stays 1, as this block already records.",
            }
            row["verdict"] = VERDICT
            row["failing_limb_superseded_" + DATE.replace("-", "_")] = "OUTCOME"
            row["failing_limb"] = ""
            row["contribution_axis"] = "OUTCOME"
            row["eligibility_basis"] = "MEASURED"
            row["eligibility_basis_evidence"] = (
                "screening_of_remainder.restated_two_axis_2026_08_19 records this "
                "registration as ELIGIBLE with eligibility_axis null, and "
                "NOT_POOLABLE_QUANTITY on the second axis.")
            row["what_it_does_report"] = row.get("reason", "")
            row["contributes_to_outcomes"] = []
            changed.append("rows[%s] -> %s" % (nct, VERDICT))
        else:
            # Not eligible on another axis. The limb this row prints is a
            # check-order artefact and the object already says which axis is real.
            key = "failing_limb_corrected_" + DATE.replace("-", "_")
            if key in row:
                continue
            row[key] = {
                "was": "OUTCOME", "now": rst["eligibility_axis"],
                "why": "restated_two_axis_2026_08_19 establishes that this trial "
                       "also fails " + str(rst["eligibility_axis"]) + ", and that "
                       "the OUTCOME limb this row printed 'was determined by CHECK "
                       "ORDER rather than by the trial'. The verdict is unchanged: "
                       "this trial is not eligible and is not a candidate for "
                       + VERDICT + ". Only the attributed axis changes, so that the "
                       "row and the restatement stop disagreeing.",
            }
            row["failing_limb"] = rst["eligibility_axis"]
            changed.append("rows[%s] limb OUTCOME -> %s (still EXCLUDE)"
                           % (nct, rst["eligibility_axis"]))

    # The by-limb summary is recomputed from the rows it summarises.
    if changed:
        buckets = {}
        for row in sor["rows"]:
            limb = row.get("failing_limb") or (
                "OUTCOME_UNAVAILABLE" if row.get("verdict") == VERDICT else "UNSTATED")
            b = buckets.setdefault(limb, {"n": 0, "ncts": []})
            b["n"] += 1
            b["ncts"].append(row["nct"])
        key = "exclusions_by_failing_limb_superseded_" + DATE.replace("-", "_")
        if key not in sor:
            sor[key] = {"was": sor.get("exclusions_by_failing_limb"),
                        "why": "Recomputed from the rows after the "
                               "check-order artefacts were corrected and two "
                               "eligible trials were relabelled " + VERDICT + ". "
                               "The OUTCOME bucket held 13; eleven of those belong "
                               "to POPULATION or COMPARATOR and two are not "
                               "exclusions at all."}
        sor["exclusions_by_failing_limb"] = buckets
        sor["k_unchanged_" + DATE.replace("-", "_")] = (
            "k stays 1. Two trials moved from EXCLUDE to " + VERDICT + ", which "
            "says they are eligible and contribute nothing extractable -- not that "
            "they contribute. Nothing entered a pool.")
        changed.append("exclusions_by_failing_limb recomputed")

    after = pooled_snapshot(d)
    assert_pooled_frozen(obj_id, before, after)
    if changed and not check:
        dump(path, raw, d)
    return changed


# ------------------------------------------------------------- sotagliflozin-hf
def migrate_sotagliflozin(check):
    """No relabelling. One MIS-ATTRIBUTED AXIS corrected.

    The row is filed under `outcome_not_this_review's`. The object's eligibility
    says eligibility "does NOT turn on which analysis a trial reported", and the
    row's own prose says the trial "is NOT part of the pivotal programme this
    object is scoped to". The ground is SCOPE, and the row stays excluded.
    """
    obj_id = "sotagliflozin-hf"
    path, raw, d = load(obj_id)
    before = pooled_snapshot(d)
    changed = []
    row = d["screening"]["records"][0]
    assert row["trial"] == "SOTA-P-CARDIA", row.get("trial")
    key = "criteria_failed_corrected_" + DATE.replace("-", "_")
    if key not in row:
        row[key] = {
            "was": list(row.get("criteria_failed") or []),
            "now": ["scope_not_this_review's"],
            "why": "NOT a case for " + VERDICT + ", and the row's own prose already "
                   "said so: 'It is NOT excluded for reporting the wrong outcome in "
                   "the sense section 3.2.4 warns against.' This object's "
                   "eligibility turns on a phase 3 randomised trial of sotagliflozin "
                   "against placebo IN THE PIVOTAL CARDIOVASCULAR OUTCOME PROGRAMME, "
                   "and states in terms that it 'does NOT turn on which analysis a "
                   "trial reported'. This trial is an investigator-sponsored "
                   "mechanistic study outside that programme. The ground is SCOPE, "
                   "which is a population/design limb, and the axis label was the "
                   "only thing wrong. It stays excluded.",
            "corrected_utc": DATE,
        }
        row["criteria_failed"] = ["scope_not_this_review's"]
        changed.append("screening.records[0] SOTA-P-CARDIA axis outcome -> scope")
        for e in d["screening"]["excluded"]:
            if e.get("reason", "").startswith("SOTA-P-CARDIA"):
                e["superseded_" + DATE.replace("-", "_")] = {
                    "was": e["reason"],
                    "why": "Axis corrected from outcome to scope; see "
                           "screening.records[0]. The verdict is unchanged.",
                }
                e["reason"] = "SOTA-P-CARDIA -- scope_not_this_review's"
                changed.append("screening.excluded[SOTA-P-CARDIA] axis corrected")
    after = pooled_snapshot(d)
    assert_pooled_frozen(obj_id, before, after)
    if changed and not check:
        dump(path, raw, d)
    return changed


# ------------------------------------------------------------------- arni-hfref
def migrate_arni(check):
    """No row is relabelled. The gap is RECORDED instead, with its arithmetic.

    This object holds the largest concentration of outcome-axis exclusions in the
    corpus -- 132 -- and none of them can honestly carry a verdict that asserts
    the record meets population, intervention and comparator, because this review
    has not assessed them on those axes. Writing the verdict anyway would trade a
    silent selection for a confident falsehood. The 24 registry records are named
    so the gap is a work item rather than a shrug.
    """
    obj_id = "arni-hfref"
    path, raw, d = load(obj_id)
    before = pooled_snapshot(d)
    changed = []
    corpus = d["screening"]["corpus"]
    outcome_rows = [r for r in corpus
                    if r.get("decision") == "exclude" and r.get("axis_failed") == "OUTCOME"]
    registry = sorted(r["record_id"] for r in outcome_rows if r.get("source") == "CTGov")
    gapkey = "outcome_axis_gap_" + DATE.replace("-", "_")
    if gapkey not in d:
        d[gapkey] = {
            "what_this_is": "A dated record of where the ELIGIBLE_OUTCOME_UNAVAILABLE "
                            "decomposition was NOT applied in this object, and why. "
                            "Counted, not asserted.",
            "n_rows_excluded_on_the_outcome_axis": len(outcome_rows),
            "n_relabelled": 0,
            "why_none": "The outcome-axis exclusions here are TITLE/ABSTRACT "
                        "bibliographic records, not trial-level eligibility "
                        "dispositions. This review has not assessed them on "
                        "population, intervention or comparator, so a verdict "
                        "asserting they meet those criteria cannot be written from "
                        "what this object holds. The honest move is to record the "
                        "gap and its size.",
            "registry_records_not_yet_reassessed": registry,
            "n_registry_records": len(registry),
            "what_would_close_it": "Assess these " + str(len(registry)) + " "
                                   "registrations on population, intervention and "
                                   "comparator against screening.eligibility. Each "
                                   "that passes all three becomes "
                                   + VERDICT + "; each that fails one stays "
                                   "excluded on the axis it fails. Neither outcome "
                                   "changes any pool.",
            "not_relabelled": SKIPPED_WITH_REASON["arni-hfref"],
            "pool_effect": "NONE. This block writes no row and touches no result.",
        }
        changed.append(gapkey)
    after = pooled_snapshot(d)
    assert_pooled_frozen(obj_id, before, after)
    if changed and not check:
        dump(path, raw, d)
    return changed


MIGRATIONS = [
    (IVI, migrate_iv_iron),
    ("bempedoic-acid-review", migrate_bempedoic),
    ("sotagliflozin-hf", migrate_sotagliflozin),
    ("arni-hfref", migrate_arni),
]


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="report, write nothing")
    g.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    total = 0
    for obj_id, fn in MIGRATIONS:
        rows = fn(a.check)
        total += len(rows)
        print("== %s: %d change(s)%s" % (obj_id, len(rows),
                                         "" if rows else "  (already migrated)"))
        for r in rows:
            print("   -", r)
    print("\n%s: %d change(s) across %d objects."
          % ("WOULD APPLY" if a.check else "APPLIED", total, len(MIGRATIONS)))
    print("Pooled estimates: verified frozen on every object before writing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
