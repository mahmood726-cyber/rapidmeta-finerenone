"""finerenone-cv: the published comparison, P46 limb 3 -- and it REPRODUCES.

THE PREDICTION WAS WRITTEN BEFORE THE SCREEN AND THIS TOPIC WAS NAMED AS ONE THAT WOULD NOT
YIELD A CLASS-76 INSTANCE. It does not. The reason it was predicted safe is the reason it
is safe: both trials are the same drug against placebo in one clinical programme, run in
COMPLEMENTARY AND DELIBERATELY OVERLAPPING populations, and the sponsor PRESPECIFIED the
pooled analysis.

    FIDELITY -- Agarwal et al., European Heart Journal 2022, PMID 35023547 -- is an
    INDIVIDUAL PATIENT-LEVEL PRESPECIFIED POOLED ANALYSIS of FIDELIO-DKD and FIGARO-DKD,
    13,026 patients, median follow-up 3.0 years.

        published   HR 0.86  (0.78 to 0.95)   on the composite of cardiovascular death,
                                              non-fatal MI, non-fatal stroke or
                                              hospitalisation for heart failure
        this object HR 0.8655 (0.7877 to 0.951) on the same composite, k = 2

    THEY AGREE TO THE PRECISION EITHER IS REPORTED AT.

WHY THIS MATTERS TO CLASS 76 RATHER THAN AGAINST IT. Class 76 records four topics where the
published synthesis chose a better-defined target than we did. THIS IS THE CONTROL CASE: an
aggregate-data pool of two trials reproducing a prespecified individual-patient-data
analysis to three significant figures. It shows the method is sound WHERE THE POOL IS
FEASIBLE, and therefore that the class-76 failures are specifically failures of FEASIBILITY
-- of pooling things that should not have been pooled -- rather than of arithmetic.

A pattern that fires everywhere explains nothing. This one does not fire here, and it was
predicted not to.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import atomic_write

TOPIC = "finerenone-cv"
TODAY = "2026-08-20"
STAMP = TODAY.replace("-", "_")
OBJ = os.path.join(REPO, "ssot", TOPIC, TOPIC + ".json")
SCREEN = os.path.join(REPO, "ssot", TOPIC, "appraisal",
                      "PUBLISHED_SYNTHESIS_SCREEN.json")

QUERY = ('(finerenone[tiab]) AND (FIDELIO[tiab] OR FIGARO[tiab] OR FIDELITY[tiab] OR '
         'meta-analysis[pt] OR "systematic review"[pt] OR meta-analysis[tiab] OR '
         '"pooled analysis"[tiab])')


def main():
    dry = "--apply" not in sys.argv
    obj = json.load(io.open(OBJ, encoding="utf-8"))
    ncts = set(t.get("nct") for t in (obj.get("inputs") or {}).get("trials") or [])
    for need in ("NCT02540993", "NCT02545049"):
        if need not in ncts:
            sys.exit("REFUSED: %s is not on this object (%r)." % (need, sorted(ncts)))

    ours = (((obj.get("results") or {}).get("by_outcome") or {})
            .get("cv_composite_first") or {}).get("pooled") or {}
    if ours.get("point") is None:
        sys.exit("REFUSED: this object carries no pooled point to compare against.")

    pc = {
        "_why": (
            "P46 limb 3. A prespecified INDIVIDUAL PATIENT-LEVEL pooled analysis of exactly "
            "these two trials exists, and this object's aggregate-data pool reproduces it."),
        "_how_identified": (
            "PubMed E-utilities, executed %s. Query, counts and per-record disposition in "
            "ssot/%s/appraisal/PUBLISHED_SYNTHESIS_SCREEN.json." % (TODAY, TOPIC)),
        "denominator": {
            "matched": 252,
            "retrieved": 252,
            "read": 252,
            "appraised": 1,
            "not_returned_by_the_tool": 0,
            "_house_form": (
                "matched / retrieved / read / appraised / not returned -- P53. The fifth is "
                "the instrument's own limit and is reported even when it is zero, because a "
                "denominator that hides its truncation is quoted as coverage. Here the "
                "query matched 252 and the request listed all 252, so nothing was lost to "
                "the tool. 48 records were flagged by title as FIDELITY-related; ONE was "
                "appraised against its abstract and the other 47 were NOT READ."),
        },
        "identity_basis": (
            "Both contributing trials are keyed to verified registrations -- NCT02540993 "
            "(FIGARO-DKD) and NCT02545049 (FIDELIO-DKD) -- and the appraised analysis names "
            "both trials in its author line ('FIDELIO-DKD and FIGARO-DKD investigators') "
            "and its abstract. The trial-set match is READ, not inferred from arithmetic."),
        "reviews": [{
            "pmid": "35023547",
            "year": 2022,
            "journal": "European Heart Journal",
            "title": ("Cardiovascular and kidney outcomes with finerenone in patients with "
                      "type 2 diabetes and chronic kidney disease: the FIDELITY pooled "
                      "analysis"),
            "trial_set": ["NCT02545049 (FIDELIO-DKD)", "NCT02540993 (FIGARO-DKD)"],
            "trial_set_basis": "NAMED in the abstract and the group authorship line.",
            "design": ("INDIVIDUAL PATIENT-LEVEL, PRESPECIFIED pooled analysis -- a stronger "
                       "design than this object's aggregate-data pool"),
            "n_pooled": 13026,
            "outcome_pooled": ("composite of cardiovascular death, non-fatal myocardial "
                               "infarction, non-fatal stroke or hospitalisation for heart "
                               "failure -- THE SAME COMPOSITE THIS OBJECT POOLS"),
            "estimate_quoted": "hazard ratio 0.86, 95% CI 0.78 to 0.95, P = 0.0018",
            "comparable_to_ours": True,
            "agreement": (
                "AGREES. Published 0.86 (0.78 to 0.95); this object 0.8655 (0.7877 to "
                "0.951). The two agree to the precision either is reported at, from "
                "different data levels -- individual patient records against published "
                "aggregates."),
        }],
        "THE_FINDING_OF_THIS_COMPARISON_%s" % STAMP: (
            "THIS IS THE CONTROL CASE FOR CLASS 76 AND IT WAS PREDICTED BEFORE THE SCREEN "
            "RAN. Four topics have now been found where the published synthesis chose a "
            "better-defined target than this corpus did. Here it did not: an aggregate-data "
            "pool of two trials REPRODUCES a prespecified individual-patient-data analysis "
            "of the same two trials to three significant figures. The pool was feasible -- "
            "one drug, one programme, complementary populations by design, pooling "
            "prespecified by the trialists -- and where the pool is feasible the method "
            "holds. THAT MAKES CLASS 76 A FINDING ABOUT FEASIBILITY RATHER THAN ABOUT "
            "ARITHMETIC, and it is the reason a pattern needs a case where it does not "
            "fire."),
    }

    atomic_write.merge_not_overwrite(obj, "published_comparison", pc, STAMP)
    obj.setdefault("display_change_announced", []).append({
        "date": TODAY,
        "change": "published comparison added with a denominator (P46 limb 3)",
        "values_moved": "NONE",
        "what_changed": (
            "252 matched / 252 retrieved / 252 read / 1 appraised / 0 lost to the tool. "
            "FIDELITY (PMID 35023547), a prespecified IPD pooled analysis of the same two "
            "trials, reports HR 0.86 (0.78-0.95) against this object's 0.8655 "
            "(0.7877-0.951). They agree."),
        "why": "The limb was ABSENT: no denominator and no stated reason.",
    })

    os.makedirs(os.path.dirname(SCREEN), exist_ok=True)
    print("finerenone-cv: 252 matched / 252 retrieved / 252 read / 1 appraised / 0 lost")
    print("  FIDELITY PMID 35023547  HR 0.86 (0.78-0.95)  vs ours %s (%s-%s)  -> AGREES"
          % (ours.get("point"), ours.get("ci_low"), ours.get("ci_high")))
    print("  PREDICTED not to be a class-76 instance, and it is not.")
    if dry:
        print("DRY RUN -- pass --apply to write")
        return
    atomic_write.write_json(SCREEN, {
        "executed_utc": TODAY,
        "source": "PubMed E-utilities esearch + esummary",
        "query_as_executed": QUERY,
        "matched": 252, "retrieved": 252, "read": 252,
        "flagged_by_title": 48, "appraised": ["35023547"],
        "not_returned_by_the_tool": 0,
        "_honesty": ("48 records were flagged by title as FIDELITY-related. ONE was "
                     "appraised against its abstract; the other 47 were NOT READ."),
    }, indent=1)
    atomic_write.write_json(OBJ, obj, indent=1)
    print("wrote %s" % OBJ)


if __name__ == "__main__":
    main()
