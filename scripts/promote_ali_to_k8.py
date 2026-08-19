#!/usr/bin/env python3
"""Promote alirocumab-lipid to k=8: the two recovered trials become part of the review.

WHY PROMOTION AND NOT A FOOTNOTE. Both trials meet this review's own criteria and register its
estimand word for word. There is no criterion under which they belong outside it.

    LEAVING THEM OUT BECAUSE INCLUDING THEM RESTATES A HEADLINE IS THE WITHHOLDING DIRECTION,
    AND WITHHOLDING A CORRECT ESTIMATE DESTROYS A TRUE FINDING WHILE PUBLISHING THE
    DESTRUCTION AS CAUTION.

We would not accept that reasoning from a published synthesis we were auditing.

EVERYTHING THAT MAKES THE CHANGE ATTRIBUTABLE IS KEPT: old and new side by side, the estimator
held constant at the object's declared DerSimonian-Laird so the delta belongs to the trials and
nothing else, and REML reported separately rather than switched.

Also repaired here, because both were found while doing this and both are defects of the same
family -- a stored block asserting something the object contradicts:

  r_output   said "k=1. No meta-analysis was performed" on an object that pools six trials.
             That is why P6 refused with a reason that was not true. Replaced with the VERBATIM
             output of ssot/ali_repool.R.
  k_history_note / interpretation_caveat
             carried UNSUBSTITUTED TEMPLATE TOKENS -- "I-squared is {res...i2} per cent".
             Substituted with the real values.
"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBJ = os.path.join(ROOT, "ssot", "alirocumab-lipid", "alirocumab-lipid.json")
ROUT = os.path.join(
    "F:/claude-temp/claude/F--rapidmeta-ssot-shell/"
    "eb4d84e5-8a24-4c3b-afe2-34bd91c20bc7/scratchpad", "ali_repool_out.txt")

NEW_TRIALS = [
    {"id": "NCT02289963", "nct": "NCT02289963",
     "name": "Alirocumab versus placebo on top of lipid-modifying therapy",
     "enrolled": 199, "comparator_type": "placebo",
     "comparator_type_basis": "armsInterventionsModule.armGroups -- the control arm gives "
                              "placebo plus the same lipid-modifying therapy as the "
                              "alirocumab arm, so LMT is background and the contrast is "
                              "alirocumab vs placebo",
     "registration_read_utc": "2026-08-19",
     "recovered_by": "screening of the 81-trial remainder, 2026-08-19"},
    {"id": "NCT02585778", "nct": "NCT02585778",
     "name": "Alirocumab versus placebo in insulin-treated diabetes (ODYSSEY DM-INSULIN)",
     "enrolled": 517, "comparator_type": "placebo",
     "comparator_type_basis": "armsInterventionsModule.armGroups -- placebo plus background "
                              "LMT and antihyperglycaemic therapy in the control arm",
     "registration_read_utc": "2026-08-19",
     "recovered_by": "screening of the 81-trial remainder, 2026-08-19"},
]

NEW_PER_TRIAL = [
    {"trial_id": "NCT02289963", "nct": "NCT02289963", "measure": "MD",
     "point": -63.40, "se": 4.172, "ci_low": -71.58, "ci_high": -55.22, "ci_level": 95,
     "estimand_id": "ldlc_pct_change_wk24-estimand",
     "derivation": "READ from the trial's own posted results: LS means placebo 6.3 (SE 2.9), "
                   "alirocumab -57.1 (SE 3.0). MD = -57.1 - 6.3; SE = sqrt(3.0^2 + 2.9^2). "
                   "Neither figure computed from another cell."},
    {"trial_id": "NCT02585778", "nct": "NCT02585778", "measure": "MD",
     "point": -48.83, "se": 2.507, "ci_low": -53.74, "ci_high": -43.92, "ci_level": 95,
     "estimand_id": "ldlc_pct_change_wk24-estimand",
     "derivation": "ASSEMBLED, and labelled so. This trial POSTS NO SINGLE OVERALL ESTIMATE: "
                   "ODYSSEY DM-INSULIN reports its primary separately for T1DM (alirocumab "
                   "-51.8 SE 3.7, n=49; placebo -3.9 SE 5.3, n=25) and T2DM (alirocumab -48.2 "
                   "SE 1.6, n=287; placebo 0.8 SE 2.2, n=142). Stratum contrasts T1DM -47.90 "
                   "(SE 6.464) and T2DM -49.00 (SE 2.720) were combined by FIXED-EFFECT "
                   "inverse variance, because the strata are DISJOINT participants from ONE "
                   "randomisation (Handbook 6.5 s23.3, combining groups). Fixed-effect and "
                   "not random: this is one trial, not two."},
]


def main():
    with io.open(OBJ, encoding="utf-8") as fh:
        obj = json.load(fh)
    b = obj["results"]["by_outcome"]["ldlc_pct_change_wk24"]

    have = {t.get("nct") for t in obj["inputs"]["trials"]}
    for t in NEW_TRIALS:
        if t["nct"] not in have:
            obj["inputs"]["trials"].append(t)
    pt_have = {t.get("nct") for t in b["per_trial"]}
    for t in NEW_PER_TRIAL:
        if t["nct"] not in pt_have:
            b["per_trial"].append(t)

    # The supersede CHAIN, not a single slot: 5 -> 6 -> 8. Each restatement keeps the one
    # before it, because a headline that changes twice with only the latest recorded is
    # indistinguishable from a headline that was always this.
    chain = b.get("supersede_chain") or []
    if b.get("superseded"):
        chain.append(dict(b["superseded"], stage="k=5, before an earlier trial was added"))
    chain.append({"stage": "k=6, before the 2026-08-19 recovery", "k": 6,
                  "estimator": "DerSimonian-Laird", "point": -54.66,
                  "ci_low": -60.75, "ci_high": -48.56, "tau2": 47.42, "i2": 87.9,
                  "reproduced_exactly_before_change": True})
    b["supersede_chain"] = chain
    b["superseded"] = chain[-1]

    b["k"] = 8
    b["pooled"] = {"measure": "MD", "point": -54.82, "ci_low": -60.23, "ci_high": -49.42,
                   "ci_level": 95}
    b["heterogeneity"] = dict(b.get("heterogeneity") or {},
                              tau2=50.04, i2=88.0, q=58.42, df=7)
    b["heterogeneity_status"] = "high"

    b["k_history_note"] = (
        "This object pooled 5 trials and recorded -52.58 (-60.61 to -44.56); then 6 trials, "
        "-54.66 (-60.75 to -48.56); and now 8, -54.82 (-60.23 to -49.42). The k=6 pool was "
        "RECOMPUTED FROM THE OBJECT'S OWN PER-TRIAL ESTIMATES BEFORE ANYTHING WAS ADDED and "
        "reproduced exactly, so the arithmetic was never in question -- the completeness was.")

    b["interpretation_caveat"] = (
        "Between-trial variation is high: I-squared is 88.0 per cent and tau-squared 50.04. "
        "The trials differ in background statin therapy, in population, and in dose regimen, "
        "so the pooled figure summarises a range of settings rather than estimating one common "
        "effect. Heterogeneity was already high at k=6 (I-squared 87.9) and the recovery did "
        "not create it.")

    b["restated_2026_08_19"] = {
        "from": {"k": 6, "point": -54.66, "ci_low": -60.75, "ci_high": -48.56},
        "to": {"k": 8, "point": -54.82, "ci_low": -60.23, "ci_high": -49.42},
        "added": ["NCT02289963", "NCT02585778"],
        "participants_added": 716,
        "why": (
            "Both trials meet this review's stated criteria and register its estimand word for "
            "word. THERE IS NO CRITERION UNDER WHICH THEY BELONG OUTSIDE IT. They were found "
            "by screening this topic's own 81-trial remainder -- which means the gap was in "
            "our completeness, not in the registry."),
        "what_changed": (
            "716 PARTICIPANTS ADDED, THE ESTIMATE MOVED BY 0.16 PERCENTAGE POINTS, THE "
            "INTERVAL NARROWED FROM 12.19 TO 10.81 POINTS WIDE, AND THE CONCLUSION IS "
            "UNCHANGED. A search that finds missing trials and confirms the answer is the "
            "search working. It also means this review's published number was right for "
            "reasons partly independent of our having found all the evidence, which is worth "
            "knowing about ourselves."),
        "attributability": (
            "The estimator is held CONSTANT at the object's declared DerSimonian-Laird, so the "
            "delta belongs to the two trials and nothing else."),
    }

    b["estimator_note"] = (
        "INHERITED AND OPEN, NOT ENDORSED. This object declares DerSimonian-Laird, which is "
        "biased for k<10. That was already questionable at k=6 and remains so at k=8. REML on "
        "the same eight trials gives -54.72 (-60.62 to -48.82) with tau2 61.44 and I-squared "
        "90.0, and a prediction interval of -71.18 to -38.26. It is reported BESIDE the DL "
        "figure rather than substituted for it, because changing the estimator and the trial "
        "set in one step would make neither change attributable. A reader should treat the "
        "estimator choice as open.")

    with io.open(ROUT, encoding="utf-8", errors="replace") as fh:
        verbatim = fh.read()
    b["r_output"] = {
        "state": "PRESENT",
        "environment": "R 4.6.0 / metafor 5.0.1",
        "script": "ssot/ali_repool.R",
        "run_utc": "2026-08-19",
        "verbatim": verbatim,
        "replaced_a_false_block": (
            "The previous r_output read 'k=1. No meta-analysis was performed, so there is NO "
            "model call to quote' -- on an object that pooled SIX trials and stored a pooled "
            "estimate. P6 therefore refused with a reason that was not true. A block asserting "
            "something the object itself contradicts is the same family as a verdict hardcoded "
            "so it can only report one outcome."),
    }

    with io.open(OBJ, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(obj, indent=1, ensure_ascii=False) + "\n")
    print("k=%d  trials=%d  per_trial=%d  chain=%d"
          % (b["k"], len(obj["inputs"]["trials"]), len(b["per_trial"]),
             len(b["supersede_chain"])))


if __name__ == "__main__":
    main()
