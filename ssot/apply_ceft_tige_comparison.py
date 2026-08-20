"""ceftaroline and tigecycline-ciai: the published comparison. P46 limb 3, closing both.

TIGECYCLINE IS THE STRONGEST DISAGREEMENT OF THE RUN, AND OUR OWN ADJUSTED INTERVAL SIDES
WITH THEM.

    Yu et al., Medicine 2019, PMID 31577763 -- "Carbapenems vs tigecycline for the treatment
    of complicated intra-abdominal infections: a Bayesian network meta-analysis". FIFTEEN
    STUDIES, 6,745 PARTICIPANTS, Markov chain Monte Carlo, random effects.

        published conclusion, quoted: "No differences in clinical and microbiological
        outcomes were observed between different carbapenems and TGC."

        this object: RR 0.9351 (0.8885 to 0.9842) on k = 3 -- AN INTERVAL THAT EXCLUDES NO
        DIFFERENCE, i.e. tigecycline INFERIOR on clinical cure.

    THEY FIND NO DIFFERENCE ACROSS FIFTEEN STUDIES; THIS OBJECT FINDS INFERIORITY ACROSS
    THREE. And this object's OWN Hartung-Knapp interval at k = 3 -- 0.8327 to 1.0501 on
    t = 4.3027 with 2 df -- INCLUDES no difference, which agrees with them and not with our
    unadjusted interval. The disagreement is therefore not merely with the literature: THE
    SMALL-SAMPLE CORRECTION THIS PROJECT ALREADY APPLIES POINTS THE SAME WAY.

    Their 15 studies against our 3 is also a k gap. WHICH TWELVE IS NOT ESTABLISHED -- the
    abstract names none and no included-study table was read -- so it is COUNTED AND NOT
    IDENTIFIED, per class 82.

CEFTAROLINE'S NEAREST COMPARISON IS A NETWORK ACROSS MANY AGENTS, not a pool of its trials.
Recorded as such rather than forced into a numeric comparison it cannot support.

NO STORED NUMBER IS CHANGED ON EITHER.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import atomic_write

TODAY = "2026-08-21"
STAMP = TODAY.replace("-", "_")

SPEC = {
    "tigecycline-ciai": {
        "outcome": "cure_toc_me",
        "query": ('(tigecycline[tiab]) AND ("intra-abdominal"[tiab] OR cIAI[tiab]) AND '
                  '(meta-analysis[pt] OR "systematic review"[pt] OR meta-analysis[tiab] OR '
                  '"pooled"[tiab])'),
        "denom": {"matched": 22, "retrieved": 22, "read": 22, "appraised": 1,
                  "flagged_by_title": 12, "not_returned_by_the_tool": 0},
        "review": {
            "pmid": "31577763", "year": 2019, "journal": "Medicine",
            "title": ("Carbapenems vs tigecycline for the treatment of complicated "
                      "intra-abdominal infections: A Bayesian network meta-analysis"),
            "trial_set": ["NOT NAMED -- fifteen studies, 6,745 participants"],
            "trial_set_basis": ("NOT READ. No included-study list in the abstract, so the "
                                "twelve studies this object does not carry are COUNTED AND "
                                "NOT IDENTIFIED."),
            "design": "Bayesian network meta-analysis, MCMC, random effects, six agents",
            "n_pooled": 6745,
            "outcome_pooled": ("clinical treatment success and microbiological treatment "
                               "success, plus adverse events and mortality"),
            "estimate_quoted": (
                "Quoted conclusion: 'No differences in clinical and microbiological outcomes "
                "were observed between different carbapenems and TGC.' On adverse events "
                "tigecycline was WORSE than imipenem/cilastatin: OR 1.53 (95% CrI 1.02 to "
                "2.41)."),
            "comparable_to_ours": True,
            "agreement": (
                "DISAGREES ON THE CONCLUSION. They find no difference in clinical outcome "
                "across fifteen studies; this object's unadjusted interval excludes no "
                "difference across three. NOTE THAT THIS OBJECT'S OWN HARTUNG-KNAPP "
                "INTERVAL, 0.8327 to 1.0501, AGREES WITH THEM."),
        },
        "finding": {
            "a_a_fifteen_study_network_finds_no_difference_where_this_pool_finds_inferiority": (
                "A PUBLISHED NETWORK META-ANALYSIS OF FIFTEEN STUDIES AND 6,745 PARTICIPANTS "
                "CONCLUDES: 'No differences in clinical and microbiological outcomes were "
                "observed between different carbapenems and TGC' (Yu et al., Medicine 2019, "
                "PMID 31577763). THIS POOL REPORTS RR 0.9351 (0.8885 to 0.9842) ON THREE "
                "TRIALS -- an interval that excludes no difference, read as tigecycline "
                "being inferior on clinical cure."),
            "b_and_our_own_small_sample_correction_agrees_with_them": (
                "THE INFERIORITY CONCLUSION DOES NOT SURVIVE THIS OBJECT'S OWN ADJUSTMENT. "
                "The Hartung-Knapp interval at k = 3 is 0.8327 to 1.0501 on t = 4.3027 with "
                "2 degrees of freedom, and it INCLUDES no difference. A reader taking "
                "inferiority from this page is reading the unadjusted interval only."),
            "c_the_evidence_base_here_is_weaker_than_the_interval_suggests": (
                "One contributing trial is OPEN-LABEL (NCT00136201 registers masking NONE) "
                "on an assessed clinical-response endpoint; one registers NO PRIMARY OUTCOME "
                "AT ALL (NCT00081744, open item O0a) so its result cannot be checked against "
                "anything; and the three define their primary in DIFFERENT ANALYSIS "
                "POPULATIONS. GRADE certainty is VERY LOW."),
            "d_what_is_not_established": (
                "WHICH twelve studies the network carries that this object does not. The "
                "abstract names none and no included-study table was read, so the gap is "
                "COUNTED AND NOT IDENTIFIED."),
        },
    },
    "ceftaroline-auto-full-review": {
        "outcome": "primary",
        "query": ('(ceftaroline[tiab]) AND (pneumonia[tiab] OR CABP[tiab] OR CAP[tiab]) AND '
                  '(meta-analysis[pt] OR "systematic review"[pt] OR meta-analysis[tiab] OR '
                  '"pooled"[tiab] OR FOCUS[tiab])'),
        "denom": {"matched": 42, "retrieved": 42, "read": 42, "appraised": 1,
                  "flagged_by_title": 18, "not_returned_by_the_tool": 0},
        "review": {
            "pmid": "34540732", "year": 2021,
            "journal": "(indexed 2021; journal not extracted)",
            "title": ("Comparing Several Treatments with Antibiotics for Community-Acquired "
                      "Pneumonia: A Systematic Review and Network Meta-Analysis"),
            "trial_set": ["NOT READ -- a network across many antibiotic regimens"],
            "trial_set_basis": ("NOT READ. Only the title and the opening of the abstract "
                                "were seen; the included-study list was not."),
            "design": "systematic review and NETWORK meta-analysis across antibiotic classes",
            "outcome_pooled": "NOT ESTABLISHED -- the outcome list was not read",
            "estimate_quoted": None,
            "comparable_to_ours": False,
            "why_not_comparable": (
                "A NETWORK ACROSS MANY AGENTS ANSWERS A DIFFERENT QUESTION from a "
                "three-trial pool of ceftaroline against ceftriaxone. No published pool of "
                "THESE THREE TRIALS was found in this screen."),
        },
        "finding": {
            "a_no_published_pool_of_these_three_trials_was_found": (
                "THIS SCREEN FOUND NO PUBLISHED SYNTHESIS POOLING THESE THREE TRIALS. The "
                "nearest relevant record is a NETWORK meta-analysis across many "
                "community-acquired pneumonia regimens (PMID 34540732), which answers a "
                "different question from a ceftaroline-versus-ceftriaxone pool. 42 records "
                "matched, 42 read, 18 flagged by title, ONE appraised; the rest were NOT "
                "READ, so absence here is absence FROM THIS SCREEN and not from the "
                "literature."),
            "b_the_pool_crosses_an_analysis_population_boundary": (
                "Two contributing trials register the primary in the MITTE population and "
                "one in the CE population. CE excludes protocol violators and indeterminate "
                "responses and systematically yields higher cure rates, so this ratio is "
                "assembled across quantities that are not the same quantity. GRADE "
                "indirectness is downgraded for it."),
            "c_the_conclusion_survives_the_small_sample_correction": (
                "Unlike tigecycline, ceftaroline's result holds under adjustment: the "
                "Hartung-Knapp interval at k = 3 is 1.0356 to 1.1787 on t = 4.3027 with 2 "
                "df, and it still excludes no difference. Recorded because the two topics "
                "separate on exactly this."),
        },
    },
}


def main():
    dry = "--apply" not in sys.argv
    for topic, spec in sorted(SPEC.items()):
        path = os.path.join(REPO, "ssot", topic, topic + ".json")
        obj = json.load(io.open(path, encoding="utf-8"))
        blk = ((obj.get("results") or {}).get("by_outcome") or {}).get(spec["outcome"])
        if not isinstance(blk, dict):
            sys.exit("REFUSED: %s has no `%s`." % (topic, spec["outcome"]))
        d = dict(spec["denom"])
        d["_house_form"] = (
            "matched / retrieved / read / appraised / not returned -- P53. %d flagged by "
            "title; ONE appraised against its abstract and the rest NOT READ."
            % d["flagged_by_title"])
        atomic_write.merge_not_overwrite(obj, "published_comparison", {
            "_why": "P46 limb 3.",
            "_how_identified": (
                "PubMed E-utilities, executed %s. Query, counts and per-record disposition "
                "in ssot/%s/appraisal/PUBLISHED_SYNTHESIS_SCREEN.json." % (TODAY, topic)),
            "denominator": d,
            "identity_basis": spec["review"]["trial_set_basis"],
            "reviews": [spec["review"]],
            "THE_FINDING_OF_THIS_COMPARISON_%s" % STAMP:
                " ".join(spec["finding"][k] for k in sorted(spec["finding"])),
        }, STAMP)

        prior = blk.get("POOL_FINDINGS_%s" % STAMP) or {}
        prior.update(spec["finding"])
        blk["POOL_FINDINGS_%s" % STAMP] = prior

        obj.setdefault("display_change_announced", []).append({
            "date": TODAY,
            "change": "published comparison added with a denominator (P46 limb 3)",
            "values_moved": "NONE",
            "what_changed": "%d matched / %d read / %d appraised"
                            % (d["matched"], d["read"], d["appraised"]),
            "why": "The limb was ABSENT.",
        })
        screen = os.path.join(REPO, "ssot", topic, "appraisal",
                              "PUBLISHED_SYNTHESIS_SCREEN.json")
        os.makedirs(os.path.dirname(screen), exist_ok=True)
        print("%-40s %d matched / %d read / %d appraised"
              % (topic, d["matched"], d["read"], d["appraised"]))
        if not dry:
            atomic_write.write_json(screen, {
                "executed_utc": TODAY,
                "source": "PubMed E-utilities esearch + esummary",
                "query_as_executed": spec["query"],
                "matched": d["matched"], "retrieved": d["retrieved"], "read": d["read"],
                "flagged_by_title": d["flagged_by_title"],
                "appraised": [spec["review"]["pmid"]],
                "not_returned_by_the_tool": 0,
                "_honesty": ("One record appraised against its abstract; every other "
                             "title-flagged record and every unflagged summary NOT READ. No "
                             "included-study table was read."),
            }, indent=1)
            atomic_write.write_json(path, obj, indent=1)
    if dry:
        print("DRY RUN -- pass --apply to write")


if __name__ == "__main__":
    main()
