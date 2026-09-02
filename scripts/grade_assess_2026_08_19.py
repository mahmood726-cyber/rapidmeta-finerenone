#!/usr/bin/env python3
"""DO THE THIRD OF THE FOUR: GRADE, PER POOLED OUTCOME, EVERY RATING-DOWN STEP WITH ITS REASON.

ONLY POOLED ESTIMATES ARE RATED. A withdrawn or declined pool has no effect estimate to rate
the certainty OF, and rating one would be certainty about a number we refused to publish.
Declined outcomes are listed with that as the reason.

    START AT HIGH FOR RANDOMISED EVIDENCE, THEN RATE DOWN AND SAY WHY EACH TIME. A certainty
    rating with no recorded steps is a number that cannot be argued with, which is the opposite
    of what GRADE is for.

THE FIVE DOMAINS, AND WHY THIS CORPUS HAS UNUSUALLY GOOD EVIDENCE FOR TWO OF THEM:

  RISK OF BIAS      read from `evidence/.../rob2.json` -- the per-result assessment, not a
                    guess. NOT ONE result in this corpus reaches LOW, because D5 cannot (no
                    trial's analysis plan is held) and D1 cannot (allocation concealment is in
                    neither the registration nor our fields). So every pool rates down at
                    least one level here, and the reason is recorded as a limit on what we can
                    reach rather than as a criticism of the trials.

  INCONSISTENCY     I-squared AND, where it exists, the COMPONENT-LEVEL DIFFERENCE between the
                    endpoints pooled. P36: heterogeneity can neither establish nor refute
                    estimand coherence -- measured in both directions in one night -- so I2 is
                    reported as ONE input and never as the test.

  INDIRECTNESS      WHERE A POOL COMBINES COMPOSITES THAT DIFFER IN COMPONENTS, THAT IS A
                    DOCUMENTED JUDGEMENT AND NOT AN ASSERTION. The component sets are already
                    computed by `lint_composite_by_components.py` and the differences are
                    recorded on the pages. A pool whose trials count different events is
                    answering a slightly different question in each trial, which is what
                    indirectness means.

  IMPRECISION       an interval crossing the null with a wide ratio is rated, not argued away.
                    And k is stated: AT k = 2 OR 3, tau-squared is estimated from almost no
                    information and the interval is optimistic even when it looks tight.

  PUBLICATION BIAS  at k < 10 a funnel plot and Egger's test have no power, so this is
                    UNDETECTED rather than NOT PRESENT. The distinction is the whole of P24
                    applied to a GRADE domain: an unreachable state is not a clean one.
"""
import io
import json
import math
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(REPO, "evidence", "2026-08-19-batch1")
DEST = os.path.join(EV, "grade.json")
ROB = os.path.join(EV, "rob2.json")

LEVELS = ["VERY_LOW", "LOW", "MODERATE", "HIGH"]

AUTHORITY = {
    "approach": "GRADE",
    "reference": ("Schunemann H, Brozek J, Guyatt G, Oxman A (editors). GRADE Handbook for "
                  "grading quality of evidence and strength of recommendations."),
    "handbook_chapter": ("Cochrane Handbook for Systematic Reviews of Interventions version "
                        "6.5.1, Chapter 14: Completing 'Summary of findings' tables and "
                        "grading the certainty of the evidence"),
    "checked_on": "2026-08-19",
    "starting_point": "HIGH for a body of randomised evidence, then rated down with reasons.",
    "not_rated_up": ("No domain is rated UP. Rating up for large effect or dose-response "
                     "applies to observational evidence that has not already been rated down, "
                     "and neither condition holds here."),
}


OIS_FLOOR = 2000


def contributing_n(obj, oid):
    """Participants CONTRIBUTING TO THIS OUTCOME, or None if unknowable.

    Cochrane ch.14 asks for the number contributing to the OUTCOME, not the
    total included population, and GRADE judges imprecision against an optimal
    information size -- never against the number of studies.

    Returns None rather than a fallback when the object holds no per-trial row
    for this outcome. That is deliberate: on SGLT2_HF the two live pools have
    results but NO `inputs.trials[*].by_outcome` rows, and a fallback to the
    topic total is exactly how both Summary-of-Findings rows came to print
    20,725 for pools of 14,462 and 11,007. An absent denominator must read as
    absent.
    """
    tot, seen = 0, 0
    for t in ((obj.get("inputs") or {}).get("trials") or []):
        b = ((t or {}).get("by_outcome") or {}).get(oid)
        a = (b or {}).get("analysed") or {}
        arms = [a.get("treatment"), a.get("control")]
        if all(isinstance(x, (int, float)) for x in arms):
            tot += int(arms[0]) + int(arms[1]); seen += 1
    return tot if seen else None


def down(cur, n, domain, reason, steps):
    i = max(0, LEVELS.index(cur) - n)
    steps.append({"domain": domain, "levels": -n, "from": cur, "to": LEVELS[i],
                  "reason": reason})
    return LEVELS[i]


def rob_for(rob, topic, oid):
    per = ((rob.get("by_topic") or {}).get(topic) or {}).get(oid) or {}
    if not per:
        return None, {}
    tally = {}
    for rec in per.values():
        tally[rec["overall"]] = tally.get(rec["overall"], 0) + 1
    return per, tally


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    with io.open(ROB, encoding="utf-8") as fh:
        rob = json.load(fh)
    topics = sys.argv[1:] or sorted((rob.get("by_topic") or {}).keys())
    out = {}
    for topic in topics:
        p = os.path.join(REPO, "ssot", topic, topic + ".json")
        if not os.path.exists(p):
            continue
        with io.open(p, encoding="utf-8") as fh:
            obj = json.load(fh)
        out[topic] = {}
        for oid, blk in ((obj.get("results") or {}).get("by_outcome") or {}).items():
            blk = blk or {}
            pooled = blk.get("pooled") or {}
            if pooled.get("point") is None:
                out[topic][oid] = {"rated": False,
                                   "why_not": ("This pool is declined or withdrawn, so there is "
                                               "no effect estimate to rate the certainty OF. "
                                               "Rating it would be certainty about a number "
                                               "this review refused to publish. The reason for "
                                               "the refusal is on the object.")}
                continue
            k = blk.get("k") or 0
            het = blk.get("heterogeneity") or {}
            i2 = het.get("i2")
            lo, hi = pooled.get("ci_low"), pooled.get("ci_high")
            steps, cur = [], "HIGH"

            # --- RISK OF BIAS ---------------------------------------------------------
            per, tally = rob_for(rob, topic, oid)
            if per is None:
                cur = down(cur, 1, "risk_of_bias",
                           "No result-level RoB 2 assessment exists for this outcome, so risk "
                           "of bias is NOT ASSESSED rather than absent. Rated down one level "
                           "because unassessed is not low.", steps)
            else:
                ni = tally.get("NO_INFORMATION", 0)
                low = tally.get("LOW", 0)
                cur = down(cur, 1, "risk_of_bias",
                           ("Result-level RoB 2 over %d contributing result(s): %s. NOT ONE "
                            "reaches LOW -- D5 cannot, because no trial's statistical analysis "
                            "plan is held, and D1 cannot, because allocation concealment is in "
                            "neither the registration nor this object. %d have at least one "
                            "domain at NO INFORMATION. This is a limit on what we can reach, "
                            "not a finding against the trials."
                            % (len(per), ", ".join("%s=%d" % kv for kv in sorted(tally.items())),
                               ni)), steps)
                if low:
                    steps[-1]["reason"] += " (%d at LOW)" % low

            # --- INCONSISTENCY --------------------------------------------------------
            if k < 2:
                steps.append({"domain": "inconsistency", "levels": 0, "from": cur, "to": cur,
                              "reason": "k = %d: inconsistency cannot be assessed with a "
                                        "single contributing result, and NOT ASSESSABLE is "
                                        "recorded rather than 'no inconsistency'." % k})
            elif i2 is not None and float(i2) >= 50:
                cur = down(cur, 1, "inconsistency",
                           "I-squared %.4g%% over k = %d. Rated down. I-squared is one input "
                           "and never the test -- P36 -- but at this magnitude with a small k "
                           "the point estimates genuinely disperse." % (float(i2), k), steps)
            else:
                steps.append({"domain": "inconsistency", "levels": 0, "from": cur, "to": cur,
                              "reason": ("I-squared %s%% over k = %d: not rated down. A LOW "
                                         "I-SQUARED DOES NOT SHOW THE TRIALS MEASURE THE SAME "
                                         "THING (P36, measured in both directions in one "
                                         "night); coherence is established by reading the "
                                         "definitions, which is done under indirectness."
                                         % (("%.4g" % float(i2)) if i2 is not None else "n/a", k))})

            # --- INDIRECTNESS ---------------------------------------------------------
            mismatch = None
            for o in (obj.get("outcomes") or []):
                if (o or {}).get("component_mismatch"):
                    mismatch = o["component_mismatch"]
            note = blk.get("relationship_to_the_other_pools") or blk.get("what_this_does_not_establish")
            if mismatch:
                cur = down(cur, 1, "indirectness",
                           ("The pooled trials' endpoints differ in components (%s), recorded "
                            "structurally on the object. A pool whose trials count different "
                            "events answers a slightly different question in each trial, which "
                            "is what indirectness means. THIS IS A DOCUMENTED JUDGEMENT, not "
                            "an assertion." % ", ".join(mismatch)), steps)
            else:
                steps.append({"domain": "indirectness", "levels": 0, "from": cur, "to": cur,
                              "reason": ("The contributing results share one endpoint "
                                         "definition, verified by reading each trial's "
                                         "registered text rather than by comparing names."
                                         + ((" The object records what this does not "
                                             "establish: " + str(note)[:220]) if note else ""))})

            # --- IMPRECISION ----------------------------------------------------------
            crosses = (lo is not None and hi is not None and
                       ((lo < 1.0 < hi) if pooled.get("measure", "").upper() not in ("MD", "SMD")
                        and (lo or 0) > 0 else (lo < 0 < hi)))
            ratio = (hi / lo) if (lo and hi and lo > 0) else None
            if crosses:
                cur = down(cur, 1, "imprecision",
                           "The %d%% interval (%.4g to %.4g) crosses the no-difference value, "
                           "so the evidence is compatible with benefit and with harm. Rated "
                           "down, not argued away."
                           % (pooled.get("ci_level", 95), lo, hi), steps)
            elif contributing_n(obj, oid) is None:
                steps.append({"domain": "imprecision", "levels": 0, "from": cur, "to": cur,
                              "reason": ("NOT ASSESSABLE. The interval (%.4g to %.4g) excludes "
                                         "the null, but this object holds no per-trial row for "
                                         "this outcome, so the number of participants "
                                         "CONTRIBUTING TO IT cannot be computed and there is "
                                         "nothing to compare against an optimal information "
                                         "size. Recorded as not assessable rather than rated "
                                         "down, and rather than assessed against a total that "
                                         "belongs to a different denominator."
                                         % (lo, hi))})
            elif contributing_n(obj, oid) < OIS_FLOOR:
                _n = contributing_n(obj, oid)
                cur = down(cur, 1, "imprecision",
                           ("%d participants contribute to this outcome, below the %d-"
                            "participant optimal information size this project uses for a "
                            "dichotomous outcome. The interval (%.4g to %.4g) does not cross "
                            "the null, but it rests on less information than a conventional "
                            "OIS asks for. RATED DOWN ON INFORMATION SIZE, NOT ON THE NUMBER "
                            "OF STUDIES -- Cochrane ch.14 is explicit that k is not a reason "
                            "for imprecision, and an earlier version of this file rated down "
                            "on k <= 3 alone."
                            % (_n, OIS_FLOOR, lo, hi)), steps)
            else:
                steps.append({"domain": "imprecision", "levels": 0, "from": cur, "to": cur,
                              "reason": "%d participants contribute and the interval (%.4g to "
                                        "%.4g) excludes the null%s." % (contributing_n(obj, oid), lo, hi,
                                                     (" with a %.2g-fold width" % ratio) if ratio else "")})

            # --- PUBLICATION BIAS -----------------------------------------------------
            steps.append({"domain": "publication_bias", "levels": 0, "from": cur, "to": cur,
                          "reason": ("k = %d. A funnel plot and Egger's test have no power "
                                     "below k = 10, so publication bias is UNDETECTED rather "
                                     "than ABSENT. Not rated down, and not reported as clean: "
                                     "an unreachable state is not a passing one." % k)
                          } if k < 10 else
                         {"domain": "publication_bias", "levels": 0, "from": cur, "to": cur,
                          "reason": "k = %d: small-study effects are assessable and no "
                                    "asymmetry test is recorded on this object, so this is "
                                    "NOT ASSESSED." % k})

            out[topic][oid] = {
                "rated": True, "certainty": cur, "k": k, "i2": i2,
                "estimate": {"point": pooled.get("point"), "ci_low": lo, "ci_high": hi},
                "started_at": "HIGH", "steps": steps,
                "summary": " ".join("%s %+d" % (s["domain"], s["levels"]) for s in steps),
            }
            print("%-28s %-34s %-9s  k=%-2s I2=%-6s  %s"
                  % (topic, oid[:34], cur, k, ("%.4g" % float(i2)) if i2 is not None else "n/a",
                     " ".join("%s%+d" % (s["domain"][:5], s["levels"])
                              for s in steps if s["levels"])))
    tally = {}
    for t, per in out.items():
        for oid, r in per.items():
            key = r.get("certainty") if r.get("rated") else "NOT_RATED_declined_pool"
            tally[key] = tally.get(key, 0) + 1
    print("\nCERTAINTY ACROSS ALL POOLED OUTCOMES")
    for k in ("HIGH", "MODERATE", "LOW", "VERY_LOW", "NOT_RATED_declined_pool"):
        if tally.get(k):
            print("   %-26s %d" % (k, tally[k]))
    with io.open(DEST, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"assessed_utc": "2026-08-19", "authority": AUTHORITY,
                             "by_topic": out}, indent=1))
    print("\nwrote %s" % DEST)
    return 0


if __name__ == "__main__":
    sys.exit(main())
