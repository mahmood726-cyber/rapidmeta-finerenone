"""gepotidacin and lefamulin: the model output, quoted verbatim. P46 limb 4.

WHY A REFUSAL WOULD NOT HAVE DISCHARGED THIS LIMB. Both objects publish a pooled RR and
declare `model: random-effects, estimator_used: REML`, and neither carried quotable model
output. "No R output is stored" is a fact about OUR PIPELINE, not about the evidence -- so a
refusal citing it is PROVENANCE-SHAPED and P46's refinement exists to exclude exactly that.
The fit was run instead.

RUN 2026-08-21, R version 4.6.0 (2026-04-24 ucrt), metafor 5.0.1.
    CALL: rma(yi = yi, sei = sei, method = "REML")
    and the same fit with test = "knha".
    Script: ssot/fit_gepotidacin_lefamulin.R

INPUTS WERE READ FROM THE OBJECTS, NEVER TYPED. Each per-trial row carries a point estimate
and a 95% interval; the log point and the log standard error are DERIVED from the published
interval width. No count is invented and no interval is re-typed.

    gepotidacin  stored RR 1.2007 (0.9668 to 1.4912)
                 refit  RR 1.2007 (0.9667 to 1.4913)   REPRODUCES to 4 dp
    lefamulin    stored RR 0.9884 (0.9530 to 1.0250)
                 refit  RR 0.9884 (0.9531 to 1.0250)   REPRODUCES to 4 dp

AND THE FIT SAYS SOMETHING THE STORED VALUE DOES NOT, ON GEPOTIDACIN.

    tau^2 0.017239, Q 3.3879 on 1 df, p = 0.0657, I^2 70.48%

The two trials disagree: 1.0762 (0.9138 to 1.2676) against 1.3426 (1.1334 to 1.5904). One
interval includes no difference and the other excludes it, and the pooled interval crosses
1 while the larger trial's does not. AT k = 2 THAT I-SQUARED IS NOT EVIDENCE OF ANYTHING --
Q on ONE degree of freedom carries almost no information -- and that is a statement about
the evidence, which is two trials, rather than about our access to it.

    THE HARTUNG-KNAPP INTERVAL IS THE HONEST WIDTH AT THIS k: RR 1.2007 (0.2946 to 4.8937),
    on a t critical value of 12.7062 with 1 degree of freedom. It is shown BESIDE the
    unadjusted interval, never instead of it.

lefamulin's tau^2 is exactly 0 and Q is 0.7316 on 1 df (p = 0.3924): its two trials agree,
and its Hartung-Knapp interval is 0.8079 to 1.2093.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import atomic_write

TODAY = "2026-08-21"
STAMP = TODAY.replace("-", "_")
LOG = (r"F:\claude-temp\claude\F--rapidmeta-ssot-shell"
       r"\1b81ef60-0aa7-48a6-b23e-0c385cde4482\scratchpad\fit.log")

TOPICS = {
    "gepotidacin-urinary-tract-auto-full-review": "primary",
    "lefamulin-cabp-auto-full-review": "primary",
}


def section_for(text, topic):
    """The block of the run log belonging to one topic. Verbatim, not paraphrased."""
    parts = re.split(r"={60,}\n", text)
    for p in parts:
        if "TOPIC   %s" % topic in p:
            return p.rstrip()
    return None


def main():
    dry = "--apply" not in sys.argv
    if not os.path.exists(LOG):
        sys.exit("REFUSED: the run log %s is absent. Quoting model output that was not "
                 "captured would be re-typing it." % LOG)
    log = io.open(LOG, encoding="utf-8", errors="replace").read()
    header = log.split("=" * 60)[0].strip()

    for topic, oid in sorted(TOPICS.items()):
        path = os.path.join(REPO, "ssot", topic, topic + ".json")
        obj = json.load(io.open(path, encoding="utf-8"))
        blk = ((obj.get("results") or {}).get("by_outcome") or {}).get(oid)
        if not isinstance(blk, dict):
            sys.exit("REFUSED: %s has no `%s` block." % (topic, oid))
        body = section_for(log, topic)
        if not body:
            sys.exit("REFUSED: the run log carries no section for %s. A limb discharged by "
                     "an absent quotation is the defect this limb exists to close." % topic)
        stored = (blk.get("pooled") or {}).get("point")
        if stored is None:
            sys.exit("REFUSED: %s carries no pooled point to check the refit against." % topic)
        if ("AGREES WITH THE STORED POINT TO 4 dp: YES") not in body:
            sys.exit("REFUSED on %s: the refit does NOT reproduce the stored point. That is "
                     "a finding to report, not a limb to fill." % topic)

        blk["r_output"] = {
            "verbatim": body,
            "_what_this_is": (
                "The console output of the fit, captured as it was printed. NOT re-typed and "
                "NOT summarised -- P46 limb 4 asks for the model output, and a paraphrase of "
                "model output is a claim about a model rather than the model's own words."),
            "environment": header,
            "call": 'rma(yi = yi, sei = sei, method = "REML")  and the same fit with '
                    'test = "knha"',
            "script": "ssot/fit_gepotidacin_lefamulin.R",
            "run_utc": TODAY,
            "inputs_derivation": (
                "yi = log(point); sei = (log(ci_high) - log(ci_low)) / (2 * 1.959964). Read "
                "from this object's own per_trial rows. NO COUNT IS INVENTED and no interval "
                "is re-typed."),
            "reproduces_stored_point": True,
            "hartung_knapp_note": (
                "Shown BESIDE the unadjusted interval, never instead of it. At k = 2 the t "
                "critical value is 12.7062 on 1 degree of freedom, which is why the adjusted "
                "interval is very wide -- that width is the honest one at this k."),
            "what_k_equals_2_means": (
                "Two trials cannot inform a between-study variance. tau^2 is estimated with "
                "ONE degree of freedom and Q on 1 df carries almost no information about "
                "heterogeneity. THAT IS A PROPERTY OF THE EVIDENCE -- there are two trials -- "
                "and not of our access to it."),
        }

        obj.setdefault("display_change_announced", []).append({
            "date": TODAY,
            "change": "model output quoted verbatim (P46 limb 4)",
            "values_moved": "NONE",
            "what_changed": (
                "REML random-effects refit run in R 4.6.0 / metafor 5.0.1 from this object's "
                "own per-trial estimates; it reproduces the stored pooled point to 4 decimal "
                "places."),
            "why": ("The limb was ABSENT. 'No R output is stored' is a fact about our "
                    "pipeline, not about the evidence, so a refusal citing it is "
                    "provenance-shaped and does not discharge P46."),
        })
        print("%-44s r_output stored, %d chars, reproduces stored point"
              % (topic, len(body)))
        if not dry:
            atomic_write.write_json(path, obj, indent=1)
    if dry:
        print("DRY RUN -- pass --apply to write")


if __name__ == "__main__":
    main()
