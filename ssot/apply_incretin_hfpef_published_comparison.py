"""incretin-hfpef-review: the published comparison, P46 limb 3 -- and MY PREDICTION WAS WRONG.

I NAMED THIS TOPIC, BEFORE THE SCREEN, AS ONE OF FOUR THAT WOULD YIELD A CLASS-76 INSTANCE.
The reasoning was that it pools TWO DIFFERENT DRUGS -- semaglutide in STEP-HFpEF DM and
tirzepatide in SUMMIT -- and that published work would decline that mix or define it better.

IT DID NOT. The published synthesis pools the SAME MIX AND MORE OF IT.

    Musa & Musa, BMC Cardiovascular Disorders 2026, PMID 41906074 -- "GLP-1 and dual
    GIP/GLP-1 agonists in obese patients with HFpEF: a systematic review and meta-analysis
    of RCTs". FOUR TRIALS, n = 4,149, registered CRD420251237462.

        published  first heart-failure hospitalisation   HR 0.52 (0.33 to 0.82), 2 trials
        published  KCCQ clinical summary score           +7.4 (4.9 to 9.9)
        this object  primary                             k = 2, NO POOLED POINT AT ALL
        this object  kccq_css_change                     MD 7.43 (5.0895 to 9.7704), k = 1

AND THE FINDING RUNS THE OPPOSITE WAY FROM CLASS 76. On the outcome this object DECLARES AS
PRIMARY it publishes no pooled estimate; the published synthesis pooled that outcome across
two trials and got HR 0.52 (0.33 to 0.82). THEY POOLED WHERE WE DECLINED, on the same drug
mix, having judged it poolable in a registered protocol.

On KCCQ the two agree closely -- 7.4 (4.9 to 9.9) against 7.43 (5.09 to 9.77) -- but THEIRS
IS A POOL AND OURS IS A SINGLE TRIAL (k = 1), so the agreement is not a reproduction and is
not claimed as one.

WHAT THIS DOES TO THE PREDICTION. Three of the twelve are now done. finerenone-cv was
predicted safe and reproduced. cangrelor-pci-review was predicted safe and DISAGREED
materially, so half that prediction failed. This one was predicted to be a class-76 instance
AND IS NOT. A prediction written down and then contradicted is worth more than one that was
never testable, and the running score is recorded rather than the successes alone.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import atomic_write

TOPIC = "incretin-hfpef-review"
TODAY = "2026-08-20"
STAMP = TODAY.replace("-", "_")
OBJ = os.path.join(REPO, "ssot", TOPIC, TOPIC + ".json")
SCREEN = os.path.join(REPO, "ssot", TOPIC, "appraisal",
                      "PUBLISHED_SYNTHESIS_SCREEN.json")

QUERY = ('((semaglutide[tiab] OR tirzepatide[tiab] OR "GLP-1"[tiab] OR incretin[tiab]) AND '
         '(HFpEF[tiab] OR "preserved ejection fraction"[tiab])) AND (meta-analysis[pt] OR '
         '"systematic review"[pt] OR meta-analysis[tiab] OR "pooled"[tiab])')


def main():
    dry = "--apply" not in sys.argv
    obj = json.load(io.open(OBJ, encoding="utf-8"))
    ncts = set(t.get("nct") for t in (obj.get("inputs") or {}).get("trials") or [])
    for need in ("NCT04916470", "NCT04847557"):
        if need not in ncts:
            sys.exit("REFUSED: %s is not on this object (%r)." % (need, sorted(ncts)))

    pc = {
        "_why": (
            "P46 limb 3. The published synthesis pools the SAME drug mix this object pools, "
            "across MORE trials, and pools the outcome this object declares primary and "
            "leaves unpooled."),
        "_how_identified": (
            "PubMed E-utilities, executed %s. Query, counts and per-record disposition in "
            "ssot/%s/appraisal/PUBLISHED_SYNTHESIS_SCREEN.json." % (TODAY, TOPIC)),
        "denominator": {
            "matched": 51,
            "retrieved": 51,
            "read": 51,
            "appraised": 1,
            "not_returned_by_the_tool": 0,
            "_house_form": (
                "matched / retrieved / read / appraised / not returned -- P53. The query "
                "matched 51 and listed all 51, so nothing was lost to the tool. 36 records "
                "were flagged by title; ONE was appraised against its abstract and 35 were "
                "NOT READ."),
        },
        "identity_basis": (
            "This object's two trials are keyed to NCT04916470 (STEP-HFpEF DM, semaglutide) "
            "and NCT04847557 (SUMMIT, tirzepatide). The appraised review does NOT name its "
            "four trials in the abstract, so THE OVERLAP IS INFERRED from its eligibility "
            "criteria -- HFpEF with obesity, GLP-1 or GLP-1/GIP agonist -- and from its "
            "KCCQ estimate, and that inference is stated rather than presented as read."),
        "reviews": [{
            "pmid": "41906074",
            "year": 2026,
            "journal": "BMC Cardiovascular Disorders",
            "title": ("GLP-1 and dual GIP/GLP-1 agonists in obese patients with HFpEF: a "
                      "systematic review and meta-analysis of RCTs"),
            "trial_set": ["NOT NAMED IN THE ABSTRACT -- four trials, n = 4,149"],
            "trial_set_basis": (
                "INFERRED, NOT READ. No included-study table was read. Overlap with this "
                "object's two trials is likely on eligibility grounds but is not "
                "established."),
            "design": "systematic review and meta-analysis, prospectively registered "
                      "(CRD420251237462)",
            "n_pooled": 4149,
            "outcome_pooled": (
                "primary: first heart-failure hospitalisation. Secondary: KCCQ clinical "
                "summary score, six-minute walk distance, weight, all-cause mortality."),
            "estimate_quoted": (
                "first HF hospitalisation HR 0.52 (0.33 to 0.82) from two contributing "
                "trials; KCCQ +7.4 (4.9 to 9.9); 6MWD +17.6 m (10.7 to 24.5); weight -9.6% "
                "(-11.3 to -8.0); all-cause mortality HR 0.90 (0.67 to 1.22), which the "
                "authors call inconclusive rather than null"),
            "comparable_to_ours": True,
            "agreement": (
                "PARTIAL, AND THE INTERESTING PART IS WHERE WE ARE SILENT. On KCCQ, 7.4 "
                "(4.9 to 9.9) against this object's 7.43 (5.09 to 9.77) -- but THEIRS IS A "
                "POOL AND OURS IS k = 1, so this is not a reproduction. On the outcome this "
                "object declares PRIMARY it publishes NO POOLED ESTIMATE, while they pooled "
                "it to HR 0.52 (0.33 to 0.82)."),
        }],
        "THE_FINDING_OF_THIS_COMPARISON_%s" % STAMP: (
            "THEY POOLED WHERE WE DECLINED, WHICH IS THE OPPOSITE OF CLASS 76. This topic "
            "was NAMED IN ADVANCE as a predicted class-76 instance on the grounds that it "
            "pools two different drugs -- semaglutide and tirzepatide. The published "
            "synthesis pools that same class mix ACROSS MORE TRIALS, in a prospectively "
            "registered review, and pools the first-heart-failure-hospitalisation outcome "
            "that this object declares primary and leaves unpooled. THE PREDICTION WAS "
            "WRONG AND IS RECORDED AS WRONG. Whether this object should pool its primary is "
            "a content decision and is not made here."),
    }

    atomic_write.merge_not_overwrite(obj, "published_comparison", pc, STAMP)
    obj.setdefault("display_change_announced", []).append({
        "date": TODAY,
        "change": "published comparison added with a denominator (P46 limb 3)",
        "values_moved": "NONE",
        "what_changed": (
            "51 matched / 51 retrieved / 51 read / 1 appraised / 0 lost. PMID 41906074 "
            "pools the same GLP-1 + GIP/GLP-1 mix across four trials and pools first HF "
            "hospitalisation to HR 0.52 (0.33-0.82) -- the outcome this object declares "
            "primary and does not pool."),
        "why": "The limb was ABSENT: no denominator and no stated reason.",
    })

    os.makedirs(os.path.dirname(SCREEN), exist_ok=True)
    print("incretin-hfpef: 51 matched / 51 retrieved / 51 read / 1 appraised / 0 lost")
    print("  PMID 41906074 pools the SAME drug mix across 4 trials; pools our primary")
    print("  -> PREDICTION WRONG: this is NOT a class-76 instance.")
    if dry:
        print("DRY RUN -- pass --apply to write")
        return
    atomic_write.write_json(SCREEN, {
        "executed_utc": TODAY,
        "source": "PubMed E-utilities esearch + esummary",
        "query_as_executed": QUERY,
        "matched": 51, "retrieved": 51, "read": 51,
        "flagged_by_title": 36, "appraised": ["41906074"],
        "not_returned_by_the_tool": 0,
        "_honesty": ("36 records were flagged by title. ONE was appraised against its "
                     "abstract; the other 35 were NOT READ. No included-study table was "
                     "read, so the trial-set overlap is INFERRED."),
    }, indent=1)
    atomic_write.write_json(OBJ, obj, indent=1)
    print("wrote %s" % OBJ)


if __name__ == "__main__":
    main()
