# -*- coding: utf-8 -*-
"""Second landing: the COMPARATOR read, the count tiers, and the estimand mismatch.

⭐ THIS PASS FOUND THAT TWO NUMBERS ON THE WINNING PAGE CANNOT BE TRACED TO ANY DOCUMENT THIS
PROJECT HOLDS, and that is the most useful thing it did.

The hand-built pilot page prints, at the tier it calls "prior synthesis":

    Gonorrhoea        RR 1.00 (0.87 to 1.15)      4588 women, 2 trials
    Trichomoniasis    RR 1.06 (0.92 to 1.23)      4588 women, 2 trials
    Serious adverse events, pooled  RR 1.12 (0.94 to 1.32)

The designated comparator has now been RETRIEVED and READ -- Cochrane CD007961.pub3,
PMID 33719075 / PMC8092571, ncbi_efetch, 10,857 rendered characters,
sha256 a61512f81de560a9... -- and it contains none of those three numbers. What it contains for
dapivirine is chlamydia RR 0.97 (0.89 to 1.07) and syphilis RR 1.70 (0.63 to 4.59), given
verbatim, plus a QUALITATIVE statement covering gonorrhoea and trichomoniasis with no figures.

⚠️ SO THE ROWS ARE RECORDED AT WHAT WE CAN SHOW, NOT AT WHAT THE PILOT PAGE ASSERTED. Chlamydia
and syphilis carry their quoted sentence. Gonorrhoea and trichomoniasis carry the qualitative
finding and say plainly that the numbers sit in the full review's data tables, which the PMC
deposit does not include. ⛔ The pilot's three figures are NOT copied forward. A number nobody
can resolve to a document is not evidence, however plausible it looks, and the fact that it
appeared on a page six judges preferred does not make it traceable.

⛔ AND THE PMC DEPOSIT OF A COCHRANE REVIEW IS AN ABSTRACT, NOT THE REVIEW. 10,857 rendered
characters is the front matter and plain-language summary. Recording this retrieval as "the
comparator, obtained" would be the same error as treating a publisher landing page as a trial
report -- so the object records WHAT PART of the comparator we hold.

---------------------------------------------------------------------------------------------
THE COUNT TIERS, which is the second thing this pass lands.

The object pools REGISTRY counts. The trials' own reports give different ones, because the
registry posts counts as SUBMITTED and the publication reports them after endpoint
ADJUDICATION -- the step that decides which seroconversions count. Those are not two readings
of one number, and until now the page recorded neither which it used nor why.

  ASPIRE       registry   71/1313 vs 97/1313      report  71/1313 vs 97/1316   [read at source]
  Ring Study   registry   82/1302 vs 61/650       report  77/1300 vs 56/650    [NOT read at source]

⛔ AND THE RING STUDY'S ADJUDICATED COUNTS ARE NOT PROMOTED TO A PRIMARY READ. Its primary
report is PMID 27959766, which has no PMC identifier; `multiroute_retrieve` tried
`europepmc_by_pmid` and got 404, and there was no `pmcid` or `doi` route to try. So the
adjudicated Ring Study figures stay at the external-review tier with the retrieval named. The
pilot page's own audit trail said this correctly -- "secondary tier -- primary report not held"
-- while `dapivirine_adjudicated_pool.py` claims in its docstring that every number in it was
read from the trial's own report. ⚠️ The page was right and the script's docstring was wrong.

---------------------------------------------------------------------------------------------
THE ESTIMAND MISMATCH, which is the third.

Both trials analysed HIV-1 acquisition as TIME TO EVENT, with censoring and unequal follow-up;
ASPIRE reports a median 1.6 years. A risk ratio over binary counts is a DIFFERENT QUANTITY. It
is what this object supports, and it must be labelled as such rather than presented as the
trials' own estimand. Until now that sentence existed only inside the integrity section -- where
the page describes what could be wrong with it -- and not in the review itself.
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)

OBJ = os.path.join("ssot", "agyw-hiv-prep-review", "agyw-hiv-prep-review.json")

ASPIRE_DOC = {
    "document_id": "PMC4993693", "what": "ASPIRE / MTN-020 primary report",
    "route": "ncbi_efetch (Europe PMC returned 503)", "retrieved_utc": "2026-08-30",
    "rendered_chars": 44179, "tier": "trial report",
    "sha256": "a6c75ad7e331aff7ff37a7792efa39d3631550600aeebe8c1b219457c4a03752"}

COCHRANE_DOC = {
    "document_id": "PMC8092571", "pmid": "33719075",
    "what": "Cochrane CD007961.pub3, 'Topical microbicides for preventing sexually transmitted "
            "infections' — THE DESIGNATED COMPARATOR",
    "route": "ncbi_efetch (Europe PMC returned 404)", "retrieved_utc": "2026-08-30",
    "rendered_chars": 10857, "tier": "prior-meta table (unverified)",
    "sha256_prefix": "a61512f81de560a9",
    "what_part_we_hold": "⚠️ ABSTRACT AND PLAIN-LANGUAGE SUMMARY ONLY. 10,857 rendered "
                         "characters is the PMC deposit's front matter, not the review. The "
                         "data tables, forest plots and per-outcome event counts are not in "
                         "what we hold, so any figure not quoted below is unread.",
    "its_search_date": "up to August 2020, quoted from its own abstract"}

RINGSTUDY_NOT_HELD = {
    "document_id": "PMID 27959766",
    "what": "The Ring Study primary report (Nel et al., 2016)",
    "state": "NOT_YET_FOUND",
    "routes_tried": "europepmc_by_pmid -> HTTP 404. The record carries no PMC identifier and no "
                    "DOI in what we hold, so no pmcid or doi route existed to try. A document "
                    "is recorded as unreachable only after every route has been tried and "
                    "named, and this is that record.",
    "attempted_utc": "2026-08-30"}

Q_CHLAMYDIA = ("In addition, dapivirine (RR 0.97, 95% CI 0.89 to 1.07), tenofovir (RR 0.90, "
               "95% CI 0.71 to 1.13) … may result in little to no difference in the risk of "
               "acquiring chlamydia infection (low-certainty evidence).")
Q_SYPHILIS = ("The evidence also suggests that dapivirine (RR 1.70, 95% CI 0.63 to 4.59), "
              "tenofovir (RR 1.27, 95% CI 0.58 to 2.78) … may have little or no effect on the "
              "risk of acquiring syphilis (low-certainty evidence).")
Q_OTHER_STI = ("The evidence also suggests that current topical microbicides may not have an "
               "effect on the risk of acquiring gonorrhoea, condyloma acuminatum, "
               "trichomoniasis, or human papillomavirus infection (low-certainty evidence).")
Q_HSV = ("Existing evidence suggests that cellulose sulphate … and PRO 2000 … may result in "
         "little to no difference in the risk of getting herpes simplex virus type 2 infection")
Q_AE_COMPARATOR = ("Microbicide use in the 12 trials, compared to placebo, did not lead to any "
                   "difference in adverse event rates.")
Q_ACCEPT = "No study reported on acceptability of the intervention."

NO_FIGURE = ("⚠️ NO FIGURE IS GIVEN HERE BECAUSE WE HOLD NONE. The comparator states this "
             "qualitatively in the part of it we hold; its per-outcome counts and intervals are "
             "in the data tables, and the PMC deposit is the abstract only. The pilot page "
             "printed a risk ratio for this outcome that does not appear in any document this "
             "project holds, and it is not carried forward.")

NEW_ROWS = [
    {"outcome": "Chlamydia", "treatment": "not stated in what we hold",
     "control": "not stated in what we hold", "effect": "RR 0.97 (0.89 to 1.07)",
     "trials": "2 trials, 4588 women", "tier": "prior-meta table (unverified)",
     "source": COCHRANE_DOC, "source_quote": Q_CHLAMYDIA,
     "why_the_primary_read_did_not_land":
         "This is the comparator's own pooled figure, quoted from its abstract. The underlying "
         "counts are in ASPIRE's Table S7 and the Ring Study's report, neither of which this "
         "retrieval obtained, so the number has not been reconciled against a primary read."},
    {"outcome": "Syphilis", "treatment": "not stated in what we hold",
     "control": "not stated in what we hold", "effect": "RR 1.70 (0.63 to 4.59)",
     "trials": "as reported by the comparator", "tier": "prior-meta table (unverified)",
     "source": COCHRANE_DOC, "source_quote": Q_SYPHILIS,
     "why_the_primary_read_did_not_land":
         "As above. ⚠️ AND THE INTERVAL SPANS 0.63 TO 4.59, so it supports no conclusion in "
         "either direction and must not be read as harm."},
    {"outcome": "Gonorrhoea", "treatment": "—", "control": "—",
     "effect": "the comparator reports no effect on the risk of acquiring gonorrhoea; " + NO_FIGURE,
     "trials": "—", "tier": "prior-meta table (unverified)",
     "source": COCHRANE_DOC, "source_quote": Q_OTHER_STI,
     "why_the_primary_read_did_not_land":
         "The comparator states this outcome qualitatively in the abstract we hold and gives no "
         "figure for it there; the counts are in data tables the PMC deposit does not include."},
    {"outcome": "Trichomoniasis", "treatment": "—", "control": "—",
     "effect": "the comparator reports no effect on the risk of acquiring trichomoniasis; "
               + NO_FIGURE,
     "trials": "—", "tier": "prior-meta table (unverified)",
     "source": COCHRANE_DOC, "source_quote": Q_OTHER_STI,
     "why_the_primary_read_did_not_land":
         "As for gonorrhoea: stated qualitatively, no figure in what we hold."},
    {"outcome": "Human papillomavirus and condyloma acuminatum", "treatment": "—",
     "control": "—",
     "effect": "the comparator reports no effect; no figure is given in what we hold",
     "trials": "—", "tier": "prior-meta table (unverified)",
     "source": COCHRANE_DOC, "source_quote": Q_OTHER_STI,
     "why_the_primary_read_did_not_land":
         "Stated qualitatively in the abstract; no figure in the deposit we hold."},
    {"outcome": "Herpes simplex virus type 2", "treatment": "—", "control": "—",
     "effect": "NOT MEASURABLE for this product — the comparator reports HSV-2 for cellulose "
               "sulphate, PRO 2000 and tenofovir, and reports none for dapivirine; ASPIRE's "
               "report does not carry an HSV outcome either",
     "trials": "—", "tier": "absent by design",
     "source": COCHRANE_DOC, "source_quote": Q_HSV},
    {"outcome": "Acceptability", "treatment": "—", "control": "—",
     "effect": "NOT REPORTED by any trial in the comparator's set — “%s”" % Q_ACCEPT,
     "trials": "—", "tier": "absent",
     "source": COCHRANE_DOC, "source_quote": Q_ACCEPT},
]

# The old placeholder rows this pass replaces, matched by outcome name.
SUPERSEDED = {"Incident sexually transmitted infections, overall",
              "Herpes simplex virus",
              "Acceptability and minor adverse events"}

COUNTS_BY_TIER = {
    "NCT01617096": {
        "_what": "The counts for this trial under each provenance tier, so a reader can see "
                 "which the pool used and what the alternative would give.",
        "designated": "registry results",
        "why_designated": "⚠️ NOT because it is the better number. The object's pooled estimate "
                          "was computed from the registry counts, and moving the designation "
                          "without recomputing the pool would leave the page's headline "
                          "disagreeing with its own inputs. The disagreement is shown instead.",
        "tiers": {
            "registry results": {
                "treatment_events": 71, "treatment_n": 1313,
                "control_events": 97, "control_n": 1313,
                "source": "ClinicalTrials.gov NCT01617096, results as submitted",
                "read_utc": "2026-08-18"},
            "trial report": {
                "treatment_events": 71, "treatment_n": 1313,
                "control_events": 97, "control_n": 1316,
                "source": ASPIRE_DOC,
                "source_quote": "Of 5516 women who underwent screening, 2629 were enrolled: "
                                "1313 in the dapivirine group and 1316 in the placebo group.",
                "read_utc": "2026-08-30"}},
        "what_differs": "The PLACEBO DENOMINATOR: 1313 in the registry, 1316 in the trial's own "
                        "report. The allocation was 1:1 and the realised split was not exactly "
                        "balanced. Three participants."},
    "NCT01539226": {
        "_what": "As above.",
        "designated": "registry results",
        "why_designated": "The adjudicated counts are held only at the external-review tier "
                          "(see `not_held`), so designating them would rest the headline on a "
                          "document this project has not read.",
        "tiers": {
            "registry results": {
                "treatment_events": 82, "treatment_n": 1302,
                "control_events": 61, "control_n": 650,
                "source": "ClinicalTrials.gov NCT01539226, results as submitted",
                "read_utc": "2026-08-18"},
            "external review citing the adjudicated publication": {
                "treatment_events": 77, "treatment_n": 1300,
                "control_events": 56, "control_n": 650,
                "source": "An external review citing this trial's adjudicated primary "
                          "publication. ⚠️ NOT read at source — see `not_held`.",
                "not_held": RINGSTUDY_NOT_HELD}},
        "what_differs": "FIVE EVENTS AND TWO PARTICIPANTS in the intervention arm, and five "
                        "events in the control arm. The registry posts counts as SUBMITTED; the "
                        "publication reports them after endpoint ADJUDICATION, which is the "
                        "step that decides which seroconversions count. Where the two disagree "
                        "the adjudicated figure is the trial's own final answer — which is why "
                        "the difference is shown rather than resolved silently."},
}

ESTIMAND_MISMATCH = {
    "pooled_quantity": "risk ratio over binary counts",
    "trials_analysed": "time to event, with censoring and unequal follow-up",
    "statement":
        "⚠️ THE QUANTITY POOLED HERE IS NOT THE QUANTITY THE TRIALS ANALYSED. Both trials "
        "analysed HIV-1 acquisition as TIME TO EVENT, with censoring and unequal follow-up; "
        "ASPIRE reports a median of 1.6 years per participant and a follow-up window of 12 to "
        "14 months on its registered primary outcome. What this review pools is a RISK RATIO "
        "over binary counts, because binary counts are what the object holds. That is a "
        "different quantity from the trials' own estimand: it weights a participant followed "
        "for two years the same as one followed for twelve months, and it will differ from a "
        "hazard ratio whenever follow-up differs between arms. It is reported because it is "
        "what the evidence here supports, and it is labelled rather than presented as though it "
        "were the trials' own analysis.",
    "source_quote": "ASPIRE, registered primary outcome time frame: “minimum of 12 months and a "
                    "maximum of 14 months per participant”. The Ring Study: “24 months”.",
    "what_would_fix_it": "Per-arm person-time or the trials' own hazard ratios with their "
                         "standard errors. Neither is in this object; neither has been "
                         "extracted; and no hazard ratio is derived here from counts, because "
                         "a hazard ratio derived from binary counts is a risk ratio wearing a "
                         "different name.",
}


def apply(path=OBJ, dry=False):
    c = json.load(io.open(path, encoding="utf-8"))
    changed = []
    prim = ((c.get("results") or {}).get("by_outcome") or {}).get("primary")
    if not isinstance(prim, dict):
        raise SystemExit("REFUSED: no primary outcome block in %s" % path)

    oo = prim.get("other_outcomes")
    if isinstance(oo, dict) and isinstance(oo.get("rows"), list):
        have = {r.get("outcome") for r in oo["rows"] if isinstance(r, dict)}
        kept = [r for r in oo["rows"]
                if isinstance(r, dict) and r.get("outcome") not in SUPERSEDED]
        dropped = len(oo["rows"]) - len(kept)
        added = [r for r in NEW_ROWS if r["outcome"] not in have or r["outcome"] in SUPERSEDED]
        added = [r for r in NEW_ROWS
                 if r["outcome"] not in {k.get("outcome") for k in kept}]
        if added or dropped:
            oo["rows"] = kept + added
            changed.append("other_outcomes: -%d superseded, +%d read from the comparator"
                           % (dropped, len(added)))

    trials = ((c.get("inputs") or {}).get("trials") or [])
    for t in trials:
        nct = t.get("nct") or t.get("trial_id")
        if nct in COUNTS_BY_TIER and "counts_by_tier" not in t:
            t["counts_by_tier"] = COUNTS_BY_TIER[nct]
            changed.append("counts_by_tier on %s" % nct)

    if "estimand_mismatch" not in prim:
        prim["estimand_mismatch"] = ESTIMAND_MISMATCH
        changed.append("estimand_mismatch on the primary outcome")

    print("")
    print("APPLY -- %s" % path)
    for ch in changed:
        print("   + %s" % ch)
    if not changed:
        print("   (nothing to do; this script is idempotent)")
        return 0
    if dry:
        print("   --dry: not written")
        return 0
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as fh:
        json.dump(c, fh, indent=1, ensure_ascii=False)
    size = os.path.getsize(tmp)
    if size < 10000:
        os.remove(tmp)
        raise SystemExit("REFUSED: the rewritten object is %d bytes. Nothing was replaced."
                         % size)
    json.load(io.open(tmp, encoding="utf-8"))
    os.replace(tmp, path)
    print("   written, %d bytes, reparsed OK" % size)
    return 0


if __name__ == "__main__":
    raise SystemExit(apply(dry="--dry" in sys.argv))
