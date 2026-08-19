#!/usr/bin/env python3
"""Record the alirocumab re-pool on the object: old and new side by side, with the reason.

A RECOVERY FOUND IN OUR OWN CORPUS GETS THE TREATMENT WE WOULD EXPECT OF ANYONE ELSE'S. Two
trials meeting this review's criteria and reporting its estimand word for word were absent from
a six-trial review. That is a defect in our work, not a screening outcome, so the old estimate
is not overwritten -- it is kept beside the new one with the reason for the change.
"""
import io
import json
import os

OBJ = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "ssot", "alirocumab-lipid", "alirocumab-lipid.json")

RECOVERED = [
    {"nct": "NCT02289963", "n": 199, "measure": "MD", "point": -63.40, "se": 4.172,
     "label": "READ",
     "source_path": "resultsSection.outcomeMeasuresModule.outcomeMeasures[0]",
     "verbatim": "Percent Change From Baseline in Calculated LDL-C at Week 24 - "
                 "Intent-to-Treat; LS means, placebo 6.3 (SE 2.9), alirocumab -57.1 (SE 3.0)",
     "derivation": "MD = -57.1 - 6.3; SE = sqrt(3.0^2 + 2.9^2). Both LS means and both SEs "
                   "read from the trial's OWN posted results, never computed from another "
                   "cell."},
    {"nct": "NCT02585778", "n": 517, "measure": "MD", "point": -48.83, "se": 2.507,
     "label": "READ + DERIVED",
     "source_path": "resultsSection.outcomeMeasuresModule.outcomeMeasures[0]",
     "verbatim": "T1DM alirocumab -51.8 (SE 3.7) n=49, placebo -3.9 (SE 5.3) n=25; "
                 "T2DM alirocumab -48.2 (SE 1.6) n=287, placebo 0.8 (SE 2.2) n=142",
     "derivation": "THIS TRIAL POSTS NO SINGLE OVERALL ESTIMATE. ODYSSEY DM-INSULIN reports "
                   "the primary outcome separately for T1DM and T2DM strata, so a trial-level "
                   "contrast had to be assembled: T1DM MD -47.90 (SE 6.464), T2DM MD -49.00 "
                   "(SE 2.720), combined by FIXED-EFFECT inverse variance because the strata "
                   "are disjoint participants from ONE randomisation (Handbook 6.5 s23.3, "
                   "combining groups). Fixed-effect and not random: this is one trial, not "
                   "two. The assembly is labelled DERIVED because it is."},
]

BLOCK = {
    "recovered_utc": "2026-08-19",
    "why": (
        "Screening this topic's 81-trial remainder found two trials that meet its stated "
        "criteria AND register its estimand word for word -- 'Percent Change From Baseline in "
        "Calculated LDL-C at Week 24' -- randomising alirocumab against placebo on background "
        "lipid-modifying therapy, and absent from the six-trial review. THAT IS A DEFECT IN "
        "THIS REVIEW'S OWN EVIDENCE BASE, not a screening outcome."),
    "recovered_trials": RECOVERED,
    "environment": "R 4.6.0 / metafor 5.0.1",
    "script": "ssot/ali_repool.R",
    "old_reproduced_exactly": (
        "BEFORE anything was added, the stored k=6 pool was recomputed from the object's own "
        "per-trial estimates: MD -54.66 (-60.75 to -48.56), tau2 47.42, I2 87.9%. IDENTICAL to "
        "the stored values. The object's arithmetic was right; what was missing was two trials."),
    "old": {"k": 6, "estimator": "DerSimonian-Laird", "measure": "MD", "point": -54.66,
            "ci_low": -60.75, "ci_high": -48.56, "tau2": 47.42, "i2": 87.9},
    "new": {"k": 8, "estimator": "DerSimonian-Laird", "measure": "MD", "point": -54.82,
            "ci_low": -60.23, "ci_high": -49.42, "tau2": 50.04, "i2": 88.0,
            "why_same_estimator": (
                "The estimator is held CONSTANT at the object's declared DerSimonian-Laird so "
                "the movement is attributable to the two trials AND NOTHING ELSE. Changing the "
                "estimator and the trial set in one step would make the delta unattributable.")},
    "new_reml": {"k": 8, "estimator": "REML", "measure": "MD", "point": -54.72,
                 "ci_low": -60.62, "ci_high": -48.82, "tau2": 61.44, "i2": 90.0,
                 "prediction_interval": [-71.18, -38.26],
                 "why_reported_separately": (
                     "DerSimonian-Laird is biased at k<10 and REML or Paule-Mandel is "
                     "indicated; this object declares DL and pooled 6 trials, so the estimator "
                     "choice was ALREADY questionable before the recovery. It is reported as a "
                     "SEPARATE finding rather than silently switched, for the same "
                     "attributability reason.")},
    "what_changed_and_what_did_not": (
        "ADDING TWO TRIALS AND 716 PARTICIPANTS MOVED THE POINT ESTIMATE BY 0.16 PERCENTAGE "
        "POINTS, from -54.66 to -54.82, and NARROWED the interval from 12.19 to 10.81 points "
        "wide. The conclusion is unchanged. That is the honest headline: the recovery CONFIRMS "
        "the estimate rather than overturning it, and a review going from six trials to eight "
        "on the same estimand is the search working, not a complication. Heterogeneity stays "
        "high (I2 88%) and was high before."),
    "not_done_and_named": (
        "The two recovered trials are recorded here with their extracted contrasts and the new "
        "pool, but are NOT yet added to inputs.trials or to results.by_outcome. Doing that "
        "restates the object's headline figure and its k, which is a change to what the page "
        "CLAIMS rather than to what this analysis SHOWS. Recorded as a completed recovery "
        "awaiting that promotion, rather than half-applied."),
}


def main():
    with io.open(OBJ, encoding="utf-8") as fh:
        obj = json.load(fh)
    before = set(obj.keys())
    obj["recovery_2026_08_19"] = BLOCK
    assert before <= set(obj.keys()), "ADDS only"
    with io.open(OBJ, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(obj, indent=1, ensure_ascii=False) + "\n")
    print("recorded: old k=6 MD %.2f -> new k=8 MD %.2f (delta %.2f)"
          % (BLOCK["old"]["point"], BLOCK["new"]["point"],
             BLOCK["new"]["point"] - BLOCK["old"]["point"]))


if __name__ == "__main__":
    main()
