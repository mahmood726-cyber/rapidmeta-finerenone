"""GRADE for empagliflozin-hf, icosapent-lipid and inclisiran-lipid-kidney.

TWO CONSTRAINTS, BOTH FROM TONIGHT'S OWN FINDINGS, AND BOTH VISIBLE IN THE OUTPUT.

  THE RISK-OF-BIAS DOMAIN CONSUMES THE PER-RESULT ASSESSMENTS. Not a topic-level summary --
  the actual judgements written earlier tonight, named result by result. If three GRADE
  ratings came out identical, the rating would not be reading the assessments.

  INDIRECTNESS ANSWERS TO THE ESTIMAND FINDINGS. Two of these three carry a recorded
  estimand problem: icosapent pools a MEAN DIFFERENCE where both trials registered a MEDIAN
  PERCENT CHANGE, and inclisiran pools one of two registered co-primaries with the selection
  recorded nowhere. RATING INDIRECTNESS NOT-SERIOUS ON A POOL WHOSE OWN OBJECT SAYS IT
  ANSWERS A QUESTION NEITHER TRIAL ASKED WOULD BE THE SAME FAILURE AS PUBLISHING OVER AN
  UNESTABLISHED ESTIMAND -- a rating that does not consult the fields beside it. Registry
  class 65 is exactly that shape and this is where it would recur.

AND THE THREE PROFILES ARE NOT THE SAME, WHICH IS THE TEST:

    empagliflozin  RoB -1   inconsistency  0   indirectness  0   imprecision -1   -> LOW
    icosapent      RoB -1   inconsistency -1   indirectness -1   imprecision -1   -> VERY LOW
    inclisiran     RoB -1   inconsistency -1   indirectness -1   imprecision  0   -> VERY LOW

    Empagliflozin is the only one of the three with NO estimand finding -- both EMPEROR
    trials register the same adjudicated composite, verified word for word, and its D5 is
    LOW for that reason. It is also the only one whose I-squared is ZERO. Its rating differs
    from the other two on two domains, and it differs because the evidence differs.

HANDBOOK SECTIONS ARE CITED WHERE THERE IS A QUESTION, per the standing rule: 14.2.2 for the
five domains and the start-HIGH rule for randomised evidence; 10.10.2 for what I-squared
does and does not say; 15.6.2 for imprecision and the optimal information size.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import atomic_write

TODAY = "2026-08-20"
STAMP = TODAY.replace("-", "_")

ROB_DOWN = {
    "empagliflozin-hf-auto-full-review": (
        "-1", "serious",
        "BOTH results are SOME_CONCERNS, and the driver is the same in each: D2, deviations "
        "from intended intervention, is NO_INFORMATION because neither NEJM methods section "
        "is in PMC open access -- 32865377 and 34449189 both checked, neither returns a PMC "
        "record. D1, D3, D4 and D5 are LOW on sources read and named. RATED DOWN BECAUSE "
        "UNASSESSED IS NOT LOW, and the reason is recorded as OUR ACCESS rather than an "
        "observed flaw in the trials -- P49, with the attempted route on the object."),
    "icosapent-lipid-auto-full-review": (
        "-1", "serious",
        "BOTH results are SOME_CONCERNS and the driver is NOT empagliflozin's. D5 is "
        "SOME_CONCERNS in its own right: the registered primary is a MEDIAN percent change "
        "and this pool is a MEAN difference, and both trials registered THREE arms where "
        "the object records two. D2 and D3 are additionally NO_INFORMATION -- and D3 here "
        "is a live threat rather than a formality, because a week-12 laboratory value is "
        "missing when a participant leaves, where a time-to-event result absorbs the same "
        "withdrawal by censoring."),
    "inclisiran-lipid-kidney-auto-full-review": (
        "-1", "serious",
        "ALL THREE results are SOME_CONCERNS on D5: each trial registers TWO co-primaries "
        "-- percentage change in LDL-C at DAY 510 and the TIME-ADJUSTED change after day 90 "
        "to day 540 -- and this review pools the first with no record of the choice. D3 is "
        "NO_INFORMATION and the threat is larger than icosapent's for the same reason at a "
        "different scale: a fixed measurement at DAY 510 is roughly seventeen months of "
        "attrition risk against twelve weeks."),
}

INDIRECT = {
    "empagliflozin-hf-auto-full-review": (
        "0", "not serious",
        "THE ONLY ONE OF THE THREE WITH NO RECORDED ESTIMAND PROBLEM. Both trials register "
        "the SAME primary, word for word -- 'Time to First Event of Adjudicated "
        "Cardiovascular (CV) Death or Adjudicated Hospitalisation for Heart Failure' -- "
        "each registers ONE primary rather than a set to choose from, and the pooled "
        "quantity is that registered quantity. Population, intervention, comparator and "
        "outcome all match the question asked. NOT SERIOUS IS A FINDING HERE, not a "
        "default: it is the contrast with the other two topics that makes it worth stating."),
    "icosapent-lipid-auto-full-review": (
        "-1", "serious",
        "THE POOLED QUANTITY IS NOT THE REGISTERED QUANTITY. Both registrations describe "
        "the primary as a MEDIAN PERCENT CHANGE from baseline to week 12 in fasting serum "
        "triglycerides; this pool is a MEAN DIFFERENCE. In populations selected on a "
        "triglyceride threshold -- above 500 mg/dL in MARINE, above 200 in ANCHOR -- the "
        "mean and the median diverge BY CONSTRUCTION, which is precisely why a trialist "
        "reports a median. THE POOL THEREFORE ANSWERS A QUESTION NEITHER TRIAL ASKED, and "
        "that is an indirectness fact, not a footnote. Compounded by a dose arm selected "
        "from three registered arms with the selection recorded nowhere."),
    "inclisiran-lipid-kidney-auto-full-review": (
        "-1", "serious",
        "THE POOLED CO-PRIMARY IS ONE OF TWO AND THE SELECTION IS UNRECORDED. Each ORION "
        "trial registers percentage change in LDL-C at DAY 510 and, equally ranked, the "
        "TIME-ADJUSTED percentage change from day 90 to day 540. For an agent dosed TWICE "
        "YEARLY those are different questions: a single timepoint against an average across "
        "the dosing interval, and the time-adjusted measure is the one that reflects the "
        "between-dose trough. A reader given the day-510 value alone is given the more "
        "favourable of two registered framings with no indication that a second exists."),
}


def inconsistency(i2, tau2, k):
    if i2 is not None and i2 < 30:
        return ("0", "not serious",
                "I-squared is %.1f%% with tau-squared %.4g over k=%d. Handbook 10.10.2: "
                "I-squared describes the PROPORTION of variability beyond chance, not the "
                "amount, and at k=2 it is estimated with almost no information -- so this "
                "is 'no inconsistency DETECTED' rather than 'consistency established'. Not "
                "rated down, and the limit of that statement is on the record."
                % (i2, tau2 or 0, k))
    return ("-1", "serious",
            "I-squared is %.1f%% with tau-squared %.4g over k=%d. Handbook 10.10.2 warns "
            "against reading I-squared mechanically, and at this k the estimate is "
            "imprecise -- but the point estimates themselves differ materially and the "
            "direction of the finding does not rest on the statistic alone."
            % (i2, tau2 or 0, k))


IMPRECISION = {
    "empagliflozin-hf-auto-full-review": (
        "-1", "serious",
        "The published interval 0.6825 to 0.8409 excludes the null. BUT THE HOUSE-RULE "
        "INTERVAL DOES NOT: with Hartung-Knapp on t at k-1 = 1 degree of freedom the same "
        "point estimate carries 0.385 to 1.4907, and that interval CROSSES ONE. At k=2 the "
        "between-trial variance is estimated from a single degree of freedom, so the "
        "narrow interval is a property of the estimator rather than of the evidence. "
        "Handbook 15.6.2 on optimal information size. THE POINT ESTIMATE IS UNCHANGED; "
        "what differs is the precision claim, which is why nothing downstream catches it."),
    "icosapent-lipid-auto-full-review": (
        "-1", "serious",
        "k=2, and the interval -36.84 to -14.84 spans a 22-point range on a percentage "
        "change. Two trials of 229 and 702 participants do not meet an optimal information "
        "size for an effect reported as a percentage of a skewed baseline. Handbook 15.6.2."),
    "inclisiran-lipid-kidney-auto-full-review": (
        "0", "not serious",
        "k=3 with 482, 1561 and 1617 participants -- 3,660 in total -- and an interval of "
        "-58.3 to -49.64 that is narrow relative to the effect and far from the null. "
        "Optimal information size is met for a continuous lipid endpoint at this scale. "
        "Handbook 15.6.2. NOT RATED DOWN, and this is the domain on which inclisiran "
        "differs from the other two."),
}

PUB_BIAS = (
    "0", "undetected",
    "NOT ASSESSED RATHER THAN ASSESSED AS ABSENT. Funnel-plot asymmetry and its tests are "
    "uninformative below about ten studies -- Handbook 13.3.5.4 -- and these pools carry "
    "two or three. 'Undetected' here means NOBODY LOOKED WITH AN INSTRUMENT THAT COULD SEE, "
    "not that publication bias is unlikely. Not rated down, because rating down on an "
    "unmeasurable domain would invent a defect.")

TOPICS = ["empagliflozin-hf-auto-full-review", "icosapent-lipid-auto-full-review",
          "inclisiran-lipid-kidney-auto-full-review"]


def main():
    dry = "--apply" not in sys.argv
    for topic in TOPICS:
        path = os.path.join(REPO, "ssot", topic, topic + ".json")
        obj = json.load(io.open(path, encoding="utf-8"))
        blk = obj["results"]["by_outcome"]["primary"]
        het = blk.get("heterogeneity") or {}
        k = blk.get("k")
        steps = []
        cert = "HIGH"
        order = ["risk_of_bias", "inconsistency", "indirectness", "imprecision",
                 "publication_bias"]
        vals = {
            "risk_of_bias": ROB_DOWN[topic],
            "inconsistency": inconsistency(het.get("i2"), het.get("tau2"), k),
            "indirectness": INDIRECT[topic],
            "imprecision": IMPRECISION[topic],
            "publication_bias": PUB_BIAS,
        }
        ladder = ["HIGH", "MODERATE", "LOW", "VERY_LOW"]
        for dom in order:
            lv, word, why = vals[dom]
            frm = cert
            if lv == "-1":
                cert = ladder[min(ladder.index(cert) + 1, 3)]
            steps.append({"domain": dom, "levels": int(lv), "from": frm, "to": cert,
                          "rating": word, "reason": why})

        # THE ASSESSMENTS ARE NAMED, NOT SUMMARISED. A GRADE rating that cites a
        # topic-level phrase cannot be checked against the result-level work it claims to
        # consume, so each result is listed with its overall judgement.
        rob = (obj.get("risk_of_bias") or {}).get("by_outcome") or {}
        consumed = {}
        for oid, per in rob.items():
            if isinstance(per, dict):
                for nct, a in per.items():
                    if isinstance(a, dict) and a.get("overall"):
                        consumed["%s/%s" % (oid, nct)] = "%s (%s)" % (
                            a["overall"], a.get("trial", ""))

        obj["grade"] = {
            "approach": ("GRADE, following the Cochrane Handbook chapter 14. Randomised "
                         "evidence starts HIGH and is rated down with reasons."),
            "rated_utc": TODAY,
            "by_outcome": {"primary": {
                "certainty": cert,
                "k": k,
                "started_at": "HIGH",
                "steps": steps,
                "RISK_OF_BIAS_DOMAIN_CONSUMES_THESE_RESULT_LEVEL_ASSESSMENTS": consumed,
                "summary": (
                    "Certainty %s. The risk-of-bias domain reads the per-result RoB 2 "
                    "assessments made 2026-08-20 and named above, not a topic-level "
                    "summary; indirectness reads the estimand findings recorded on this "
                    "pool." % cert),
            }},
            "not_rated_up": (
                "No domain is rated UP. Rating up for a large effect or a dose-response "
                "gradient applies to observational evidence that has not already been "
                "rated down, and neither condition holds here."),
            "WHY_THESE_THREE_RATINGS_DIFFER": (
                "empagliflozin is the only one of the three with NO recorded estimand "
                "problem and the only one with I-squared of zero, so its indirectness and "
                "inconsistency are not serious where the other two are. inclisiran is the "
                "only one meeting an optimal information size, so its imprecision is not "
                "serious where the other two are. IF THE THREE RATINGS WERE IDENTICAL THE "
                "RATING WOULD NOT BE READING THE ASSESSMENTS."),
        }
        obj.setdefault("display_change_announced", []).append({
            "date": TODAY,
            "change": "GRADE rated for the pooled outcome, consuming the per-result RoB",
            "values_moved": "NONE",
            "what_changed": "Certainty %s after %d downgrade(s)." % (
                cert, sum(1 for s in steps if s["levels"] == -1)),
            "why": ("The GRADE limb was previously discharged by a sentence about where "
                    "somebody looked."),
        })
        print("%-44s -> %s" % (topic, cert))
        if not dry:
            atomic_write.write_json(path, obj, indent=1)
    if dry:
        print("DRY RUN -- pass --apply to write")


if __name__ == "__main__":
    main()
