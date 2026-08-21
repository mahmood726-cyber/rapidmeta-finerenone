"""Limb 4 for the three topics that needed only a refit -- and a third raw-vs-house instance.

    cangrelor-pci-review / corrected_composite_3component   RR  k=2
    rotavirus-vaccine-africa-review / primary               OR  k=3
    incretin-hfpef-review / kccq_css_change                 MD  k=2

ALL THREE REPRODUCE THE STORED POINT TO FOUR DECIMAL PLACES.

TWO OF THE THREE CARRY A READER-FACING FINDING, AND ONE OF THOSE IS A CORRECTION.

ONE -- INCRETIN, AND THIS IS THE THIRD INSTANCE OF THE RAW-VERSUS-HOUSE CONFUSION AND THE
FIRST THAT CHANGES A CONCLUSION.

    the object's stored caveat, verbatim:
        "At two studies a Hartung-Knapp interval uses a t-distribution on ONE degree of
        freedom and gives 1.80 to 13.06 -- far wider, and arguably the honest interval at
        this k. IT STILL EXCLUDES NO EFFECT."

    1.80 to 13.06 IS metafor's RAW UNFLOORED knha interval. THIS PROJECT'S INTERVAL IS
    -7.7429 to 22.6028, and IT INCLUDES NO EFFECT.

The raw factor here is 0.3708 -- the knha standard error is a THIRD of the random-effects
one -- so the unfloored adjustment NARROWS the interval, which is the exact instability the
house floor exists to prevent. The page told a reader that the adjusted interval was wider
AND still excluded no effect; the adjusted interval this project actually computes is wider
still and does not.

    THE STORED POINT ESTIMATE, MD 7.43 (5.09 to 9.77), IS NOT CHANGED. What changes is a
    sentence about what the sensitivity analysis showed, which said the opposite of what it
    shows.

TWO -- ROTAVIRUS, WHERE THE ADJUSTED INTERVAL CROSSES THE NULL AT k = 3.

    unadjusted   OR 0.4941 (0.3466 to 0.7045)   EXCLUDES no effect
    house HK     OR 0.4941 (0.2268 to 1.0764)   INCLUDES it, on t = 4.3027 with 2 df

Same shape as tigecycline-ciai, and at k = 3 rather than k = 2 -- so it is not the
"almost nothing survives" case. tau-squared is 0.0557 with I-squared 56.97%, which is real
spread across three trials rather than the zero-heterogeneity case.

THREE -- CANGRELOR, WHERE THE TWO INTERVALS AGREE and there is nothing to disclose. Recorded
because a run that finds nothing is evidence too: house and raw are both 0.3190 to 2.9171,
the stored `pooled_hartung_knapp` is 0.3190 to 2.9172, and the corpus sweep's earlier
"UNRECONCILED" verdict on this block was the SWEEP's Python REML approximation being loose,
not the object being wrong. The R fit settles it.

AND THE SCRIPT HAD TO BE GENERALISED TWICE TO GET HERE, both times against a real defect:
it log-transformed unconditionally, which is wrong for incretin's MEAN DIFFERENCE and would
have produced "unadjusted 1685.7331 (162.3105 to 17507.7801)" as our engine's word; and it
read the measure only from `pooled$measure`, which cangrelor's block does not carry.
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
FITS = os.path.join(REPO, "evidence", "refits_2026_08_21")

SPEC = {
    "cangrelor-pci-review": {
        "outcome": "corrected_composite_3component",
        "measure": "RR",
        "findings": None,
        "note": ("HOUSE AND RAW AGREE HERE: both 0.3190 to 2.9171, and the stored "
                 "pooled_hartung_knapp is 0.3190 to 2.9172. Nothing to disclose, recorded "
                 "because a run that finds nothing is evidence too."),
    },
    "rotavirus-vaccine-africa-review": {
        "outcome": "primary",
        "measure": "OR",
        "findings": {
            "a_the_adjusted_interval_crosses_no_effect_at_k_equals_3": (
                "READ THIS BESIDE THE ESTIMATE. The unadjusted interval is OR 0.4941 (0.3466 "
                "to 0.7045) and EXCLUDES no effect. THIS PROJECT'S HARTUNG-KNAPP INTERVAL AT "
                "k = 3 IS 0.2268 TO 1.0764, on t = 4.3027 with 2 degrees of freedom, AND IT "
                "INCLUDES NO EFFECT. The house rule already requires the adjusted interval to "
                "be shown beside the unadjusted one where k is small; on this pool the two "
                "disagree about the conclusion."),
            "b_and_this_is_not_the_almost_nothing_survives_case": (
                "STATED SO THE CAUTION IS NOT DISCOUNTED. At k = 2 the t critical value is "
                "12.7062 and almost no effect survives the adjustment, so a crossing there is "
                "weak evidence. HERE k = 3 AND t IS 4.3027, which is a far less demanding "
                "test. There is also real spread: tau-squared 0.0557, Q 4.7195 on 2 df, "
                "I-squared 56.97%. The crossing is driven by disagreement between the trials, "
                "not by the correction being brutal at tiny k."),
            "c_what_has_and_has_not_been_done": (
                "THE STORED ESTIMATE IS NOT CHANGED. Withdrawing or restating a published "
                "number is a content decision. What has been done is to put the adjusted "
                "interval where a reader meets the number."),
        },
        "note": None,
    },
    "incretin-hfpef-review": {
        "outcome": "kccq_css_change",
        "measure": "MD",
        "findings": {
            "a_the_sensitivity_interval_this_page_quoted_was_not_this_project_s": (
                "CORRECTION, AND IT REVERSES WHAT THIS PAGE SAID ABOUT ITS OWN SENSITIVITY "
                "ANALYSIS. The caveat on this pool stated that the Hartung-Knapp interval "
                "'gives 1.80 to 13.06 -- far wider, and arguably the honest interval at this "
                "k. It still excludes no effect.' THE FIGURES 1.80 TO 13.06 ARE metafor's RAW "
                "UNFLOORED knha OUTPUT. THIS PROJECT'S INTERVAL IS -7.7429 TO 22.6028, AND IT "
                "INCLUDES NO EFFECT."),
            "b_why_the_raw_interval_is_the_wrong_one_here_specifically": (
                "The raw variance-inflation factor on this pool is 0.3708 -- metafor's "
                "Hartung-Knapp standard error is barely a THIRD of the random-effects one -- "
                "so the unfloored adjustment NARROWS the interval instead of widening it. "
                "That is the exact instability this project's floor exists to prevent, and it "
                "is why the raw figures looked reassuringly wide next to the Wald interval "
                "while being the product of a correction pointing the wrong way."),
            "c_what_is_and_is_not_changed": (
                "THE POINT ESTIMATE AND ITS WALD INTERVAL ARE UNCHANGED: MD 7.43 (5.09 to "
                "9.77) points on the KCCQ clinical summary score, k = 2, 1,094 participants. "
                "What changes is a sentence about what the sensitivity analysis showed, which "
                "said the opposite of what it shows. A seven-point KCCQ difference remains a "
                "symptom benefit and this page still estimates nothing about death or "
                "hospitalisation."),
        },
        "note": None,
        "caveat_repair": {
            "find": ("At two studies a Hartung-Knapp interval uses a t-distribution on ONE "
                     "degree of freedom and gives 1.80 to 13.06 -- far wider, and arguably "
                     "the honest interval at this k. It still excludes no effect."),
            "replace": (
                "At two studies a Hartung-Knapp interval uses a t-distribution on ONE degree "
                "of freedom. THIS PROJECT'S INTERVAL IS -7.74 TO 22.60 AND IT INCLUDES NO "
                "EFFECT. An earlier version of this sentence gave 1.80 to 13.06 and said the "
                "interval still excluded no effect; those figures are metafor's RAW UNFLOORED "
                "knha output, not this project's, and the conclusion drawn from them was "
                "wrong. The raw inflation factor here is 0.3708, so the unfloored adjustment "
                "NARROWS rather than widens -- the instability the house floor exists to "
                "prevent."),
        },
    },
}


def main():
    dry = "--apply" not in sys.argv
    for topic, spec in sorted(SPEC.items()):
        path = os.path.join(REPO, "ssot", topic, topic + ".json")
        obj = json.load(io.open(path, encoding="utf-8"))
        oid = spec["outcome"]
        blk = ((obj.get("results") or {}).get("by_outcome") or {}).get(oid)
        if not isinstance(blk, dict):
            sys.exit("REFUSED: %s has no `%s`." % (topic, oid))

        fit = os.path.join(FITS, "%s__%s.txt" % (topic, oid))
        if not os.path.exists(fit):
            sys.exit("REFUSED: no stored R output at %s." % fit)
        text = io.open(fit, encoding="utf-8").read()
        for required in ("AGREES WITH THE STORED POINT TO 4 dp: YES",
                         "HOUSE INTERVAL, inflation factor floored at 1"):
            if required not in text:
                sys.exit("REFUSED: the stored fit for %s/%s does not carry %r."
                         % (topic, oid, required))
        scale = "natural" if spec["measure"] in ("MD", "SMD", "RD") else "log"
        if ("(%s scale," % scale) not in text:
            sys.exit("REFUSED: the fit for %s/%s was not run on the %s scale, which is the "
                     "scale its measure %s requires. A mean difference fitted on the log "
                     "scale produces a number that looks like a fit and is not one."
                     % (topic, oid, scale, spec["measure"]))

        blk["r_output"] = {
            "state": "PRESENT",
            "what_it_is": ("The random-effects fit of THIS BLOCK'S OWN per-trial estimates, "
                           "quoted as the software printed it."),
            "script": "ssot/fit_from_per_trial.R",
            "call": "Rscript ssot/fit_from_per_trial.R %s %s" % (topic, oid),
            "environment": "R 4.6.0 with metafor 5.0.1",
            "run_utc": TODAY,
            "scale": scale,
            "scale_note": (
                "READ FROM THE MEASURE, NOT ASSUMED. This measure is %s, so the fit is on the "
                "%s scale. The script log-transformed unconditionally until 2026-08-21, which "
                "is right for RR/OR/HR/IRR and WRONG for a mean difference -- on this corpus "
                "it would have printed 'unadjusted 1685.7331 (162.3105 to 17507.7801)' for a "
                "7.43-point KCCQ difference, and limb 4 stores that output VERBATIM."
                % (spec["measure"], scale)),
            "interval_method": (
                "REML with the unadjusted Wald interval, and the same fit under Hartung-Knapp "
                "beside it. THE HOUSE INTERVAL FLOORS THE VARIANCE-INFLATION FACTOR AT "
                "max(1, SE_knha / SE_unadjusted); metafor's raw unfloored value is printed "
                "separately and flagged where it is narrower than the unadjusted interval."),
            "reproduction_of_the_previous_value": (
                "REPRODUCES THE POINT ESTIMATE THIS PAGE DELIVERS TO FOUR DECIMAL PLACES."),
            "verbatim": text,
            "stored_at": "evidence/refits_2026_08_21/%s__%s.txt" % (topic, oid),
        }
        if spec.get("note"):
            blk["r_output"]["nothing_to_disclose"] = spec["note"]

        if spec.get("findings"):
            prior = blk.get("POOL_FINDINGS_%s" % STAMP) or {}
            prior.update(spec["findings"])
            blk["POOL_FINDINGS_%s" % STAMP] = prior

        moved = "NONE"
        if spec.get("caveat_repair"):
            cr = spec["caveat_repair"]
            cav = (blk.get("pooled") or {}).get("caveats")
            if not isinstance(cav, str) or cr["find"] not in cav:
                sys.exit("REFUSED: %s's caveat is not the text this repair was written "
                         "against. Repairing a sentence that has since changed would "
                         "overwrite somebody else's edit." % topic)
            blk["pooled"]["caveats"] = cav.replace(cr["find"], cr["replace"])
            moved = ("NONE -- the point estimate and its Wald interval are untouched; a "
                     "SENTENCE about the sensitivity analysis is corrected")

        obj.setdefault("display_change_announced", []).append({
            "date": TODAY,
            "change": "the model output for `%s` is stored verbatim (P46 limb 4)" % oid,
            "values_moved": moved,
            "what_changed": ("a REML refit on the %s scale reproducing the stored point to 4 "
                             "dp%s" % (scale,
                                       "; and the sensitivity interval quoted for this pool "
                                       "was metafor's RAW value, not this project's"
                                       if spec.get("caveat_repair") else "")),
            "why": "The limb was ABSENT." if not spec.get("caveat_repair") else
                   ("The limb was ABSENT, and storing it revealed that this page's own "
                    "statement about its sensitivity analysis was drawn from the unfloored "
                    "interval and reached the opposite conclusion."),
        })
        print("%-34s %-32s %s scale, reproduces%s"
              % (topic[:34], oid[:32], scale,
                 ", FINDING RENDERED" if spec.get("findings") else ""))
        if not dry:
            atomic_write.write_json(path, obj, indent=1)
    if dry:
        print("DRY RUN -- pass --apply to write")


if __name__ == "__main__":
    main()
