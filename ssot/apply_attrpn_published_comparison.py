"""attr-pn-review: the published comparison, P46 limb 3 -- and the obstacle it names.

THE LIMB IS HELD AND THE POOL IS REFERRED, AND THOSE ARE TWO DIFFERENT STATEMENTS.

P46 limb 3 asks whether this object CARRIES a published comparison with a denominator. It
now does. What that comparison SAYS is that the pool this object publishes rests on a
contrast the literature assessed and rejected as infeasible.

    Samjoo et al., Current Medical Research and Opinion 2020, PMID 32011182 -- "The impact
    of clinical heterogeneity on conducting network meta-analyses in transthyretin
    amyloidosis with polyneuropathy" -- SET OUT TO POOL THESE TREATMENTS, ASSESSED
    FEASIBILITY FIRST, AND CONCLUDED:

        "An NMA of ATTR-PN treatments was not feasible, given the observed cross-trial
         heterogeneity."

    And named the obstacle:

        "clear differences in eligibility criteria between trials were accompanied by
         imbalances in baseline population characteristics considered to be plausible
         effect modifiers, such as disease stage and previous treatment. Of the outcomes
         assessed, only quality of life and adverse events were similarly reported in all
         trials. NEUROPATHY OUTCOMES WERE NOT EVALUATED CONSISTENTLY BETWEEN TRIALS."

THIS OBJECT POOLS A NEUROPATHY OUTCOME -- mNIS+7 -- ACROSS THREE DIFFERENT DRUGS: patisiran
(APOLLO), vutrisiran (HELIOS-A) and eplontersen (NEURO-TTRansform), to a mean difference of
-25.11. The published feasibility assessment says that neuropathy outcomes are the ones NOT
consistently evaluated, and that the cross-trial heterogeneity defeats the comparison.

    THE OBSTACLE IS IN THE EVIDENCE, NOT IN OUR ACCESS TO IT. Nothing further we read
    resolves it: it is a property of how the trials were designed and reported. That makes
    this an EVIDENCE-SHAPED referral rather than a provenance-shaped one, and it is a
    finished state under the standard rather than a gap to be filled.

NO STORED NUMBER IS CHANGED. Whether to withdraw -25.11 is a content decision.

FOURTH INSTANCE OF ONE PATTERN, and the most direct. Given the same or overlapping trials,
published work has now four times chosen a more defensible target than this corpus did: the
ATTR network that refused to pool across drugs, the rosuvastatin IPD analysis that
harmonised the outcome, the SGLT2 CVOT review that declined to pool across populations, and
this feasibility assessment that declined the network entirely.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import atomic_write

TOPIC = "attr-pn-review"
TODAY = "2026-08-20"
STAMP = TODAY.replace("-", "_")
OBJ = os.path.join(REPO, "ssot", TOPIC, TOPIC + ".json")
SCREEN = os.path.join(REPO, "ssot", TOPIC, "appraisal",
                      "PUBLISHED_SYNTHESIS_SCREEN.json")

QUERY = ('(patisiran[tiab] OR vutrisiran[tiab] OR eplontersen[tiab] OR "hereditary '
         'transthyretin"[tiab] OR hATTR[tiab]) AND (polyneuropathy[tiab] OR '
         'neuropathy[tiab]) AND (meta-analysis[pt] OR "systematic review"[pt] OR '
         'meta-analysis[tiab] OR "indirect comparison"[tiab] OR "network meta"[tiab])')

APPRAISED = [
    {
        "pmid": "32011182",
        "year": 2020,
        "journal": "Current Medical Research and Opinion",
        "title": ("The impact of clinical heterogeneity on conducting network "
                  "meta-analyses in transthyretin amyloidosis with polyneuropathy"),
        "trial_set": ["APOLLO (patisiran) -- ALSO POOLED BY THIS OBJECT, NCT01960348",
                      "NEURO-TTR (inotersen) -- not on this object",
                      "Fx-005 (tafamidis) -- not on this object"],
        "trial_set_basis": "All three pivotal trials are NAMED in the abstract.",
        "design": "feasibility assessment for a Bayesian network meta-analysis",
        "outcome_pooled": "NONE -- the network was assessed and NOT performed",
        "estimate_quoted": (
            "no estimate. Quoted conclusion: 'An NMA of ATTR-PN treatments was not "
            "feasible, given the observed cross-trial heterogeneity.'"),
        "comparable_to_ours": False,
        "why_not_comparable": (
            "IT DECLINES THE COMPARISON THIS OBJECT MAKES. It shares one trial with us "
            "(APOLLO) and assesses the same drug-versus-drug question. Quoted: 'Of the "
            "outcomes assessed, only quality of life and adverse events were similarly "
            "reported in all trials. Neuropathy outcomes were not evaluated consistently "
            "between trials.' THIS OBJECT POOLS A NEUROPATHY OUTCOME."),
    },
    {
        "pmid": "39286810",
        "year": 2024,
        "journal": "Frontiers in Neurology",
        "title": ("Assessing the effectiveness and safety of Patisiran and Vutrisiran in "
                  "ATTRv amyloidosis with polyneuropathy: a systematic review"),
        "trial_set": ["NOT READ -- ten studies, 756 patients; membership not established"],
        "trial_set_basis": (
            "NO INCLUDED-STUDY TABLE WAS READ. It covers patisiran and vutrisiran, which "
            "are two of this object's three drugs, so it very likely contains APOLLO and "
            "HELIOS-A -- but WHICH ten studies is not established from anything read."),
        "design": "systematic review WITHOUT a pooled estimate across the drugs",
        "outcome_pooled": (
            "NONE POOLED ACROSS DRUGS. It reports that both 'consistently demonstrated "
            "significant improvements' in neuropathy, quality of life and cardiac "
            "function, narratively."),
        "estimate_quoted": None,
        "comparable_to_ours": False,
        "why_not_comparable": (
            "It reviews two of our three drugs and STILL DOES NOT POOL THEM against each "
            "other. A narrative synthesis where this object publishes a mean difference."),
    },
]


def main():
    dry = "--apply" not in sys.argv
    obj = json.load(io.open(OBJ, encoding="utf-8"))
    ncts = set(t.get("nct") for t in (obj.get("inputs") or {}).get("trials") or [])
    if "NCT01960348" not in ncts:
        sys.exit("REFUSED: APOLLO (NCT01960348) is not on this object (%r)." % sorted(ncts))

    pc = {
        "_why": (
            "P46 limb 3. The comparison is HELD and what it says is that a published "
            "feasibility assessment declined the very network this object pools."),
        "_how_identified": (
            "PubMed E-utilities, executed %s. Query, counts and per-record disposition in "
            "ssot/%s/appraisal/PUBLISHED_SYNTHESIS_SCREEN.json. 21 records matched, 21 "
            "summaries read, 2 appraised against their abstracts, 19 NOT APPRAISED. No "
            "included-study table was read for either." % (TODAY, TOPIC)),
        "denominator": {
            "records_matched": 21,
            "summaries_read": 21,
            "appraised": 2,
            "not_appraised": 19,
            "syntheses_pooling_our_exact_trial_set": 0,
            "_what_the_denominator_means": (
                "21 is what this query returned. NO published synthesis pools this object's "
                "three trials together; the closest relevant record ASSESSED such a pool "
                "and rejected it."),
        },
        "identity_basis": (
            "APOLLO is keyed to NCT01960348 on this object and is NAMED in the appraised "
            "feasibility assessment, so the overlap is read rather than inferred. The other "
            "two trials on this object -- HELIOS-A NCT03759379 and NEURO-TTRansform "
            "NCT04136184 -- are NOT in that assessment's trial set, which predates them."),
        "reviews": APPRAISED,
        "THE_FINDING_OF_THIS_COMPARISON_%s" % STAMP: (
            "THE COMPARISON IS HELD; THE POOL IS REFERRED ON AN OBSTACLE IN THE EVIDENCE. "
            "Samjoo et al. 2020 set out to network-meta-analyse ATTR-PN treatments, "
            "assessed feasibility, and concluded that 'An NMA of ATTR-PN treatments was not "
            "feasible, given the observed cross-trial heterogeneity' -- naming that "
            "'neuropathy outcomes were not evaluated consistently between trials'. THIS "
            "OBJECT POOLS mNIS+7, A NEUROPATHY OUTCOME, ACROSS THREE DIFFERENT DRUGS TO "
            "-25.11. The obstacle is a property of how the trials were designed and "
            "reported, so NOTHING FURTHER WE READ RESOLVES IT: this is an evidence-shaped "
            "referral and a finished state, not a gap awaiting more reading. Whether to "
            "withdraw the estimate is a content decision and is not made here."),
    }

    atomic_write.merge_not_overwrite(obj, "published_comparison", pc, STAMP)
    obj.setdefault("display_change_announced", []).append({
        "date": TODAY,
        "change": "published comparison added with a denominator (P46 limb 3)",
        "values_moved": "NONE",
        "what_changed": (
            "21 matched, 21 read, 2 appraised. NO published synthesis pools these three "
            "trials; PMID 32011182 assessed such a network and found it NOT FEASIBLE on "
            "cross-trial heterogeneity, naming neuropathy outcomes specifically."),
        "why": "The limb was ABSENT: no denominator and no stated reason.",
    })

    os.makedirs(os.path.dirname(SCREEN), exist_ok=True)
    atomic_write.write_json(SCREEN, {
        "executed_utc": TODAY,
        "source": "PubMed E-utilities esearch + esummary",
        "query_as_executed": QUERY,
        "records_matched": 21,
        "summaries_read": 21,
        "appraised": ["32011182", "39286810"],
        "not_appraised": 19,
        "_honesty": ("Two records were appraised against their abstracts. The other 19 were "
                     "read as TITLES ONLY and are recorded as not appraised."),
    }, indent=1) if not dry else None

    print("attr-pn: 21 matched / 21 read / 2 appraised / 19 not appraised")
    print("  PMID 32011182: an NMA of these treatments was assessed and found NOT FEASIBLE")
    print("  -> comparison limb HELD; the POOL is referred on an EVIDENCE-shaped obstacle")
    if dry:
        print("DRY RUN -- pass --apply to write")
        return
    atomic_write.write_json(OBJ, obj, indent=1)
    print("wrote %s" % OBJ)


if __name__ == "__main__":
    main()
