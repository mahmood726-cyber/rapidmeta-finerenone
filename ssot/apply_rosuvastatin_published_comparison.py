"""rosuvastatin-auto-full-review: the published comparison, P46 limb 3.

WHAT THIS REPLACES. The limb was ABSENT -- no denominator and no stated reason. P46 limb 3
requires a published comparison CARRYING A DENOMINATOR: not "we looked and found nothing",
but a search whose yield is counted so a reader can tell a thorough screen from a lucky one.

THE SEARCH, EXECUTED 2026-08-20, PubMed E-utilities:

    (rosuvastatin[tiab]) AND (meta-analysis[pt] OR "systematic review"[pt]
     OR meta-analysis[tiab] OR "pooled analysis"[tiab])
    AND (placebo[tiab] OR "primary prevention"[tiab])

    114 records matched. 114 summaries read. 8 appraised. 106 NOT appraised.

THE FINDING, AND IT IS AN ESTIMAND FINDING RATHER THAN A NUMERIC ONE.

Exactly one published synthesis pools THE SAME TWO TRIALS this object pools -- Joseph et
al., Cardiovascular Research 2022, PMID 33705531, an INDIVIDUAL PARTICIPANT DATA
meta-analysis of HOPE-3 and JUPITER across 30,507 participants. It is a stronger design
than this object's aggregate pool.

AND IT DELIBERATELY POOLS A SINGLE HARMONISED OUTCOME -- venous thromboembolism, HR 0.53
(0.37 to 0.75) on 139 events -- WHERE THIS OBJECT POOLS EACH TRIAL'S OWN DIFFERING PRIMARY.
This object's own question says so: "the outcome each trial registered as its primary,
which differ across the 2 trials here". So the two are NOT competing estimates of one
quantity and the difference between 0.656 and 0.53 is not a disagreement to reconcile.

    THE PUBLISHED SYNTHESIS SOLVED THE PROBLEM THIS POOL HAS BY CHOOSING ONE OUTCOME
    COMMON TO BOTH TRIALS. That is the comparison's finding, and it bears on this
    object's own pooled estimate rather than merely sitting beside it.

NO STORED NUMBER IS CHANGED HERE. Whether to re-pool on a harmonised outcome is a content
decision and belongs to Mahmood; this records what the literature did and why it differs.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import atomic_write

TOPIC = "rosuvastatin-auto-full-review"
TODAY = "2026-08-20"
STAMP = TODAY.replace("-", "_")
OBJ = os.path.join(REPO, "ssot", TOPIC, TOPIC + ".json")
SCREEN = os.path.join(REPO, "ssot", TOPIC, "appraisal",
                      "PUBLISHED_SYNTHESIS_SCREEN.json")

QUERY = ('(rosuvastatin[tiab]) AND (meta-analysis[pt] OR "systematic review"[pt] OR '
         'meta-analysis[tiab] OR "pooled analysis"[tiab]) AND (placebo[tiab] OR '
         '"primary prevention"[tiab])')

APPRAISED = [
    {
        "pmid": "33705531",
        "year": 2022,
        "journal": "Cardiovascular Research",
        "title": ("Rosuvastatin for the prevention of venous thromboembolism: a pooled "
                  "analysis of the HOPE-3 and JUPITER randomized controlled trials"),
        "trial_set": ["NCT00239681 (JUPITER)", "NCT00468923 (HOPE-3)"],
        "trial_set_basis": ("NAMED IN THE TITLE AND THE ABSTRACT. This is not inferred from "
                            "participant totals: both trials are named, and the abstract "
                            "states 30,507 participants over a mean 3.62 years."),
        "design": "INDIVIDUAL PARTICIPANT DATA meta-analysis -- a stronger design than ours",
        "outcome_pooled": ("venous thromboembolism -- deep vein thrombosis or pulmonary "
                           "embolism -- ONE OUTCOME HARMONISED ACROSS BOTH TRIALS"),
        "estimate_quoted": "hazard ratio 0.53, 95% CI 0.37 to 0.75, on 139 VTE events",
        "comparable_to_ours": False,
        "why_not_comparable": (
            "IT POOLS A DIFFERENT QUANTITY. This object pools each trial's OWN REGISTERED "
            "PRIMARY, and those primaries differ between JUPITER and HOPE-3 -- this "
            "object's question says so in its own words. Joseph et al. pool a single "
            "outcome defined identically in both trials. 0.656 and 0.53 are estimates of "
            "TWO DIFFERENT THINGS and the gap between them is not a discrepancy."),
    },
    {
        "pmid": "30716508",
        "year": 2019,
        "journal": "American Heart Journal",
        "title": ("Comparative effectiveness and safety of statins as a class and of "
                  "specific statins for primary prevention of cardiovascular disease: a "
                  "systematic review, meta-analysis, and network meta-analysis of "
                  "randomized trials with 94,283 participants"),
        "trial_set": ["NOT READ"],
        "trial_set_basis": (
            "NO INCLUDED-STUDY TABLE WAS READ. At 94,283 participants it is far larger than "
            "the two trials here and certainly contains them among many others, but WHICH "
            "trials it contains is not established from anything read, and it is recorded "
            "as unread rather than assumed."),
        "design": "systematic review, pairwise and network meta-analysis",
        "outcome_pooled": "NOT ESTABLISHED -- the abstract was read, the outcome list was not",
        "estimate_quoted": None,
        "comparable_to_ours": None,
        "why_not_comparable": (
            "NOT ASSESSABLE rather than not comparable. A class-level network meta-analysis "
            "of 94,283 participants answers a different question from a two-trial "
            "drug-versus-placebo pool, but that is an expectation and not a reading."),
    },
]


def main():
    dry = "--apply" not in sys.argv
    obj = json.load(io.open(OBJ, encoding="utf-8"))

    ncts = set(t.get("nct") for t in (obj.get("inputs") or {}).get("trials") or [])
    for need in ("NCT00239681", "NCT00468923"):
        if need not in ncts:
            sys.exit("REFUSED: %s is not on this object (%r). The comparison names trials "
                     "this object does not pool." % (need, sorted(ncts)))

    pc = {
        "_why": (
            "P46 limb 3. Exactly one published synthesis pools the same two trials, and it "
            "pools a DIFFERENT OUTCOME -- deliberately, by harmonising on one endpoint "
            "common to both. That is a finding about this object's own estimand, not a "
            "number to reconcile against."),
        "_how_identified": (
            "PubMed E-utilities, executed %s. Query, counts and the per-record disposition "
            "are in ssot/%s/appraisal/PUBLISHED_SYNTHESIS_SCREEN.json. %d records matched, "
            "%d summaries read, %d appraised, %d NOT APPRAISED. No included-study table was "
            "read for either appraised record: for PMID 33705531 the trial set is NAMED IN "
            "THE TITLE, and for PMID 30716508 the trial set is recorded as NOT READ."
            % (TODAY, TOPIC, 114, 114, 8, 106)),
        "denominator": {
            "records_matched": 114,
            "summaries_read": 114,
            "appraised": 8,
            "not_appraised": 106,
            "syntheses_pooling_this_exact_trial_set": 1,
            "_what_the_denominator_means": (
                "114 is what the query returned, not what exists. A different query returns "
                "a different denominator, which is why the query is stored beside the "
                "count. 106 records were screened out on title alone and were NOT READ."),
        },
        "identity_basis": (
            "Both contributing trials are keyed to a verified ClinicalTrials.gov "
            "registration -- NCT00239681 (JUPITER) and NCT00468923 (HOPE-3) -- and the one "
            "comparable synthesis NAMES BOTH IN ITS TITLE, so the trial-set match is read "
            "rather than inferred from participant arithmetic."),
        "reviews": APPRAISED,
        "THE_FINDING_OF_THIS_COMPARISON_%s" % STAMP: (
            "THE ONLY PUBLISHED SYNTHESIS OF THESE TWO TRIALS AVOIDED THE ESTIMAND PROBLEM "
            "THIS POOL HAS. Joseph et al. pooled individual participant data on ONE outcome "
            "defined identically in both trials. This object pools EACH TRIAL'S OWN "
            "REGISTERED PRIMARY, and those differ -- which this object's question already "
            "states. The comparison therefore does not adjudicate our number; it shows that "
            "the literature, given the same two trials, chose a different and more "
            "defensible target. WHETHER TO RE-POOL ON A HARMONISED OUTCOME IS A CONTENT "
            "DECISION AND IS NOT MADE HERE."),
    }

    atomic_write.merge_not_overwrite(obj, "published_comparison", pc, STAMP)

    obj.setdefault("display_change_announced", []).append({
        "date": TODAY,
        "change": "published comparison added with a denominator (P46 limb 3)",
        "values_moved": "NONE",
        "what_changed": (
            "114 records matched, 114 read, 8 appraised, 106 not appraised. One synthesis "
            "pools the same two trials (PMID 33705531, IPD, VTE, HR 0.53) and pools a "
            "different outcome from this object."),
        "why": "The limb was ABSENT: no denominator and no stated reason.",
    })

    os.makedirs(os.path.dirname(SCREEN), exist_ok=True)
    screen = {
        "executed_utc": TODAY,
        "source": "PubMed E-utilities esearch + esummary",
        "query_as_executed": QUERY,
        "records_matched": 114,
        "summaries_read": 114,
        "appraised": [r["pmid"] for r in APPRAISED],
        "screened_out_on_title_not_read": 106,
        "_honesty": (
            "8 records were flagged as candidates by title; 2 were appraised against their "
            "abstracts. The other 6 candidates and the 106 non-candidates were NOT READ."),
    }

    print("rosuvastatin: 114 matched / 114 read / 8 appraised / 106 not appraised")
    print("  PMID 33705531 pools BOTH trials, IPD, on VTE -- a different estimand from ours")
    if dry:
        print("DRY RUN -- pass --apply to write")
        return
    atomic_write.write_json(SCREEN, screen, indent=1)
    atomic_write.write_json(OBJ, obj, indent=1)
    print("wrote %s" % OBJ)
    print("wrote %s" % SCREEN)


if __name__ == "__main__":
    main()
