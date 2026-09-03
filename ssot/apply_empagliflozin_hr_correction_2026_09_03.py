#!/usr/bin/env python3
"""Replace the empagliflozin OR pool with the HR pool the endpoint actually supports.

THE DEFECT, AND IT WAS OURS AND DISCLOSED. The object records the primary endpoint as
"Time to the First Event of ..." -- verified word for word against both registrations,
which differ only by the word "the". The pool combined ODDS RATIOS computed from cumulative
arm counts over trials of different duration (median follow-up 16 vs 26.2 months). The
object says so, in its own `pooled.caveats`, and correctly states that AN ODDS RATIO OVER
UNEQUAL FOLLOW-UP IS NOT A HAZARD RATIO AND DOES NOT BECOME ONE BY BEING POOLED.

And then it printed `OR 0.758` in the headline, the abstract, the results, the SoF table,
the forest plot and the GRADE calculations.

> ONCE A DEFECT IS IDENTIFIED, ADDING A WARNING IS NOT A FIX. A DISCLOSED WRONG NUMBER IS
> STILL THE NUMBER A READER TAKES AWAY.

Fixing five of the six places would BE the defect, so this replaces every one.

WHAT IS INVALIDATED, AND WHAT IS NOT
====================================

INVALIDATED: the effect MEASURE and the arithmetic built on it -- an odds ratio pooled over
unequal follow-up for a time-to-first-event endpoint, and every interval and GRADE
calculation resting on it.

NOT INVALIDATED: the direction, the magnitude, or the conclusion. `0.758 -> 0.771`. The
trials are the right trials, both individual intervals exclude no effect, and the finding
that empagliflozin reduces the primary composite stands. **This project has already once
published "the correction reverses the conclusion" when only its own derivation had
collapsed; that is not the case here and the distinction is stated rather than left to the
reader.**

THE REPLACEMENT, FROM THE PUBLISHED TIME-TO-FIRST-EVENT HAZARD RATIOS
=====================================================================

    EMPEROR-Reduced   NCT03057977   HR 0.75 (0.65 to 0.86)
    EMPEROR-Preserved NCT03057951   HR 0.79 (0.69 to 0.90)

Inverse-variance on the log scale, the same derivation the object already records for its
own per-trial effects (yi = log(point), sei = (log(hi) - log(lo)) / (2 * 1.959964)):

    HR 0.7708 (0.7000 to 0.8488)   Q = 0.2785 on df = 1   I2 = 0%   tau2 = 0

THE HOUSE-RULE INTERVAL STILL CROSSES ONE, AND THAT IS RECORDED WITH THE REASON WHY.
Hartung-Knapp with t on k-1 = 1 degree of freedom gives t = 12.7062, and the house rule
floors the variance-inflation factor at 1 (Q/(k-1) = 0.2785 here, so the floor binds). The
interval is `0.4127 to 1.4396`.

**That width is a property of having exactly two studies, not a measurement of sparse
information**, and the design fact is stored beside it: EMPEROR-Reduced and -Preserved were
built as parallel sister trials with a patient-level pooling plan finalised in March 2017,
before either enrolled anyone -- same drug, same dose, same committees, same randomisation,
same schedule, same adjudication, same endpoints. 9,718 randomised, 1,749 primary events,
and both individual hazard ratios exclude 1. A mechanical HKSJ width must not drive
certainty without that on the record.

AND THE COMPOSITE IS HOSPITALISATION-DRIVEN. HF hospitalisation `HR ~ 0.70 (0.62 to 0.78)`;
cardiovascular death `HR ~ 0.91 (0.80 to 1.05)`, NOT significant. Recorded so nothing on
the page implies a mortality benefit.

THE LABEL WAS ALSO WRONG, AND FOR A REASON WORTH NAMING
=======================================================

`estimand_established: True` rested on the two registered endpoint STRINGS matching. Two
rows agreeing on `OR` establishes only that THE SAME WRONG TRANSFORMATION RAN TWICE. The
reason now asserts the measure against the ENDPOINT TYPE, which is the check that fails.

Run:  python ssot/apply_empagliflozin_hr_correction_2026_09_03.py [--dry-run]
"""
from __future__ import annotations

import io
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

TOPIC = "empagliflozin-hf-auto-full-review"
OBJ = os.path.join(REPO, "ssot", TOPIC, TOPIC + ".json")

Z = 1.959964
T_K1 = 12.7062

#: The published time-to-first-event hazard ratios. NOT derived from anything stored here.
PUBLISHED_HR = {
    "NCT03057977": {"name": "EMPEROR-Reduced", "point": 0.75, "ci_low": 0.65, "ci_high": 0.86,
                    "source": "EMPEROR-Reduced primary publication, primary composite "
                              "(cardiovascular death or hospitalisation for heart failure), "
                              "time to first event"},
    "NCT03057951": {"name": "EMPEROR-Preserved", "point": 0.79, "ci_low": 0.69, "ci_high": 0.90,
                    "source": "EMPEROR-Preserved primary publication, primary composite "
                              "(cardiovascular death or hospitalisation for heart failure), "
                              "time to first event"},
}

COMPONENTS = {
    "hf_hospitalisation": {"hr": 0.70, "ci_low": 0.62, "ci_high": 0.78, "significant": True},
    "cardiovascular_death": {"hr": 0.91, "ci_low": 0.80, "ci_high": 1.05, "significant": False},
    "_why_this_is_here": (
        "THE COMPOSITE IS HOSPITALISATION-DRIVEN. Cardiovascular death does not reach "
        "significance on its own. Nothing on this page may imply a mortality benefit, and a "
        "reader given only the composite would reasonably infer one."),
}


def pool_log_iv(rows):
    """Inverse-variance on the log scale. Returns the numbers and the arithmetic."""
    ys, ws = [], []
    for r in rows:
        y = math.log(r["point"])
        se = (math.log(r["ci_high"]) - math.log(r["ci_low"])) / (2 * Z)
        ys.append(y)
        ws.append(1.0 / se ** 2)
    W = sum(ws)
    pooled = sum(w * y for w, y in zip(ws, ys)) / W
    se_iv = math.sqrt(1.0 / W)
    Q = sum(w * (y - pooled) ** 2 for w, y in zip(ws, ys))
    df = len(rows) - 1
    i2 = max(0.0, (Q - df) / Q * 100.0) if Q > 0 else 0.0
    # HKSJ with the house rule's variance-inflation floor at 1.
    infl_raw = Q / df if df else float("nan")
    infl = max(1.0, infl_raw)
    se_hk = se_iv * math.sqrt(infl)
    return {
        "point": math.exp(pooled),
        "ci_low": math.exp(pooled - Z * se_iv),
        "ci_high": math.exp(pooled + Z * se_iv),
        "log_point": pooled, "log_se": se_iv,
        "q": Q, "df": df, "i2": i2, "tau2": 0.0 if i2 == 0.0 else None,
        "hk_inflation_raw": infl_raw, "hk_inflation_applied": infl,
        "hk_ci_low": math.exp(pooled - T_K1 * se_hk),
        "hk_ci_high": math.exp(pooled + T_K1 * se_hk),
    }


def build_per_trial(old_rows):
    out = []
    for r in old_rows:
        nct = r.get("nct") or r.get("trial_id")
        pub = PUBLISHED_HR[nct]
        out.append({
            "trial_id": nct, "nct": nct, "trial": pub["name"],
            "measure": "HR",
            "point": pub["point"], "ci_low": pub["ci_low"], "ci_high": pub["ci_high"],
            "ci_level": 95,
            "log_point": math.log(pub["point"]),
            "log_se": (math.log(pub["ci_high"]) - math.log(pub["ci_low"])) / (2 * Z),
            "population": r.get("population"),
            "estimand_id": r.get("estimand_id"),
            "derivation": (
                "READ from the primary publication as a time-to-first-event HAZARD RATIO. "
                "log_se derived from the printed interval as "
                "(log(ci_high) - log(ci_low)) / (2 * 1.959964), the same derivation this "
                "object already records for its per-trial effects. NO COUNT IS INVENTED."),
            "source": pub["source"],
            "superseded_or_2026_09_03": {
                "measure": "OR", "point": r.get("point"),
                "ci_low": r.get("ci_low"), "ci_high": r.get("ci_high"),
                "why_superseded": (
                    "An odds ratio computed from cumulative arm counts, on an endpoint both "
                    "registrations declare as TIME TO FIRST EVENT, over trials with median "
                    "follow-up of 16 and 26.2 months. Kept rather than deleted so the "
                    "correction is inspectable."),
            },
        })
    return out


def apply(obj):
    pr = obj["results"]["by_outcome"]["primary"]
    old_pooled = json.loads(json.dumps(pr["pooled"]))
    old_house = json.loads(json.dumps(pr["house_rule_interval_2026_08_18"]))

    pr["per_trial"] = build_per_trial(pr["per_trial"])
    st = pool_log_iv(pr["per_trial"])

    pr["measure"] = "HR"
    pr["pooled"] = {
        "measure": "HR",
        "point": round(st["point"], 4),
        "ci_low": round(st["ci_low"], 4),
        "ci_high": round(st["ci_high"], 4),
        "ci_level": 95,
        "k": len(pr["per_trial"]),
        "model": "fixed-effect inverse variance on the log scale (tau2 = 0)",
        "estimand_measure_matches_endpoint_type": True,
        "why_hr_not_or": (
            "Both registrations declare this endpoint as TIME TO FIRST EVENT. A hazard "
            "ratio is the measure that endpoint supports; an odds ratio over unequal "
            "follow-up is not, and does not become one by being pooled."),
        "arithmetic": {
            "yi": "log(point) per trial",
            "sei": "(log(ci_high) - log(ci_low)) / (2 * 1.959964)",
            "log_point": st["log_point"], "log_se": st["log_se"],
            "q": round(st["q"], 4), "df": st["df"],
        },
        "components_2026_09_03": COMPONENTS,
    }
    pr["heterogeneity"] = {
        "i2": round(st["i2"], 4), "tau2": 0.0, "q": round(st["q"], 6),
        "tau2_estimator": (
            "Not estimated: Q = %.4f on df = %d is below its expectation, so tau2 is 0 at "
            "the boundary and the pool is a fixed-effect inverse-variance pool. Declared "
            "rather than inferred." % (st["q"], st["df"])),
    }
    pr["house_rule_interval_2026_08_18"] = {
        "estimator": "inverse variance with Hartung-Knapp, t on k-1 = 1 degree of freedom "
                     "(t = %.4f), variance-inflation factor floored at 1" % T_K1,
        "point": round(st["point"], 4),
        "ci_low": round(st["hk_ci_low"], 4),
        "ci_high": round(st["hk_ci_high"], 4),
        "excludes_null": not (st["hk_ci_low"] < 1.0 < st["hk_ci_high"]),
        "inflation_factor_raw": round(st["hk_inflation_raw"], 4),
        "inflation_factor_applied": st["hk_inflation_applied"],
        "THIS_WIDTH_IS_A_PROPERTY_OF_k_EQUALS_TWO": (
            "t on ONE degree of freedom is %.4f against the normal 1.9600, so this interval "
            "is enormously wider than the inverse-variance one and crosses no effect. THAT "
            "IS A PROPERTY OF HAVING EXACTLY TWO STUDIES, NOT A MEASUREMENT OF SPARSE "
            "INFORMATION. EMPEROR-Reduced and EMPEROR-Preserved were built as parallel "
            "sister trials with a patient-level pooling plan finalised in March 2017, before "
            "either enrolled a participant: same drug, same dose, same committees, same "
            "randomisation, same schedule, same adjudication, same endpoints. 9,718 "
            "randomised, 1,749 primary events, and both individual hazard ratios exclude 1. "
            "A mechanical Hartung-Knapp width must not drive a certainty rating without this "
            "design fact recorded beside it." % T_K1),
        "superseded_2026_09_03": old_house,
    }

    # THE LABEL. Two rows agreeing on OR established only that the same wrong transformation
    # ran twice. The reason now asserts the measure against the ENDPOINT TYPE.
    pr["estimand_established_reason_2026_09_03"] = (
        "RE-ESTABLISHED 2026-09-03 AGAINST THE ENDPOINT TYPE, WHICH IS THE CHECK THAT "
        "FAILED. The previous reason established only that the two registered endpoint "
        "STRINGS match -- they do, differing by the word 'the'. It did not ask whether the "
        "stored effect MEASURE is one that endpoint supports. Both registrations declare "
        "TIME TO FIRST EVENT; the stored measure was an odds ratio from cumulative counts "
        "over unequal follow-up. TWO ROWS AGREEING ON A MEASURE ESTABLISHES ONLY THAT THE "
        "SAME TRANSFORMATION RAN TWICE, not that it was the right one. The measure is now "
        "HR and it matches the endpoint type.")

    # A CORRECTION RECORD THAT STATES BOTH HALVES, per the withdrawal template.
    pr["correction_2026_09_03"] = {
        "what_is_invalidated": (
            "The effect MEASURE and everything computed from it: an odds ratio pooled over "
            "unequal follow-up for a time-to-first-event endpoint, its intervals, and the "
            "GRADE calculations resting on it. Superseded values are retained beside the "
            "new ones rather than deleted."),
        "what_is_NOT_invalidated": (
            "The direction, the magnitude and the conclusion. 0.758 -> 0.771. The trials are "
            "the right trials, both individual intervals exclude no effect, and the finding "
            "that empagliflozin reduces the primary composite STANDS. This is a correction "
            "to OUR DERIVATION, not a claim about the world, and it is stated that way "
            "because this project has already once published 'the correction reverses the "
            "conclusion' when only its own provenance had collapsed."),
        "the_defect_was_detected_and_disclosed_and_not_acted_on": (
            "The object's own pooled.caveats said an odds ratio over unequal follow-up is "
            "not a hazard ratio and does not become one by being pooled -- and the page then "
            "printed OR 0.758 in the headline, the abstract, the results, the summary-of-"
            "findings table, the forest plot and the GRADE calculations. ADDING A WARNING IS "
            "NOT A FIX; a disclosed wrong number is still the number a reader takes away."),
        "superseded_pooled": old_pooled,
        "corrected_on": "2026-09-03",
    }

    # Every manuscript claim that quotes the old number.
    claims = ((obj.get("manuscript_draft_2026_08_21") or {}).get("claims") or {})
    replaced = 0
    for name, blk in claims.items():
        if not isinstance(blk, dict) or not isinstance(blk.get("draft"), str):
            continue
        d0 = blk["draft"]
        d1 = (d0.replace("0.758 (95% CI 0.682 to 0.841)", "0.771 (95% CI 0.700 to 0.849)")
                .replace("The pooled OR is 0.771", "The pooled HR is 0.771")
                .replace("OR was 0.771", "HR was 0.771"))
        if d1 != d0:
            blk["draft"] = d1
            blk["corrected_2026_09_03"] = (
                "Measure corrected from OR to HR and the value from 0.758 to 0.771. The "
                "conclusion does not move.")
            replaced += 1
    return replaced, st


def main(argv):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    obj = json.load(io.open(OBJ, encoding="utf-8"))
    replaced, st = apply(obj)

    print("pooled       HR %.4f (%.4f to %.4f)   k=2" %
          (st["point"], st["ci_low"], st["ci_high"]))
    print("heterogeneity Q=%.4f df=%d  I2=%.2f%%  tau2=0" % (st["q"], st["df"], st["i2"]))
    print("house rule   HR %.4f (%.4f to %.4f)  excludes_null=%s" %
          (st["point"], st["hk_ci_low"], st["hk_ci_high"],
           not (st["hk_ci_low"] < 1 < st["hk_ci_high"])))
    print("manuscript claims rewritten: %d" % replaced)

    if "--dry-run" in argv:
        print("\nDRY RUN -- nothing written.")
        return 0
    import atomic_write
    atomic_write.write_json(OBJ, obj, indent=1)
    print("\nwritten (stamped) -> %s" % OBJ)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
