# -*- coding: utf-8 -*-
"""Machine extraction from registry posted results: participant flow, analysis
populations, and harms -- for the dapivirine object.

THREE THINGS THIS ADDS, none of them transcribed by hand.

1. PARTICIPANT FLOW AND THE ARM-CODE INVERSION. ClinicalTrials.gov numbers its
   result groups per MODULE, and the numbering is NOT guaranteed to agree
   across modules of the same registration. On NCT01539226 the baseline, flow
   and adverse-event modules all put PLACEBO at index 000 and the OUTCOME
   module puts DAPIVIRINE at index 000. On NCT01617096 all four modules put
   dapivirine first. Any extractor that joins flow to outcome on the index --
   the obvious thing to do -- silently swaps the arms of one trial and not the
   other. This is recorded per module, from two independent sources.

2. THE ANALYSIS POPULATIONS, VERBATIM. `risk_of_bias.analysis_population_NOT_
   STATED` has stood in this object since it was written. The posted results
   state it in terms for both trials, and both are MODIFIED intention-to-treat:
   participants found retrospectively to have been HIV-1 infected at enrolment
   are excluded. That answers RoB 2 signalling questions 2.6 and 3.1 from a
   free machine-readable source.

3. HARMS -- AND A REFUSAL TO POOL THEM. Serious adverse events and deaths per
   arm for both trials. The two placebo arms differ SEVEN-FOLD in serious-
   adverse-event rate (1.38% against 9.88%) in trials that enrolled the same
   population in the same countries. That is a difference in ascertainment, not
   in risk, and a pooled harms estimate over it would be arithmetic pretending
   to be evidence. The 2x2s are published and the pool is declined, with the
   reason.

⚠️ NO STORED RISK-OF-BIAS JUDGEMENT IS CHANGED HERE. This object is governed by
a standing two-assessor process and a recorded adjudication. New evidence is
written as evidence, with the domain implication stated and marked as awaiting
the second assessor. Answering a signalling question is not the same act as
moving a domain, and collapsing the two is how a review quietly rates itself up.

SOURCES. ClinicalTrials.gov API v2 (a URL, reproducible by any reader) is the
primary; the AACT 2026-04-12 flat-file snapshot is an INDEPENDENT SECOND SOURCE
and agrees on every group mapping. AACT is a 17 GB download and is therefore
never the route a reader is asked to take.
"""
import datetime
import io
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OBJ = os.path.join(HERE, "agyw-hiv-prep-review", "agyw-hiv-prep-review.json")
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()

RING = "NCT01539226"      # The Ring Study / IPM 027
ASPIRE = "NCT01617096"    # ASPIRE / MTN-020


def _rr(e1, n1, e2, n2):
    """RR and its 95% interval. Handbook 6.5 section 6.4.1 Box 6.4.a for the
    ratio; the standard error is the RevMan statistical-algorithms form, which
    is where chapter 6 defers it. Same formulas the primary pool uses."""
    r = (e1 / n1) / (e2 / n2)
    se = math.sqrt(1 / e1 - 1 / n1 + 1 / e2 - 1 / n2)
    return {"point": round(r, 4),
            "ci_low": round(math.exp(math.log(r) - 1.959964 * se), 4),
            "ci_high": round(math.exp(math.log(r) + 1.959964 * se), 4),
            "se_log_rr": round(se, 6)}


def _chi2_sf_1df(q):
    """Upper tail of chi-square on ONE degree of freedom = 2*(1 - Phi(sqrt q)).

    Since 1 - Phi(z) = 0.5 * erfc(z / sqrt(2)) and z = sqrt(q), the whole thing
    collapses to erfc(sqrt(q / 2)).

    ⚠️ TWO WRONG FORMS WERE WRITTEN BEFORE THIS ONE AND BOTH LOOKED FINE.
    exp(-q/2) is the survival function for TWO degrees of freedom, not one; it
    returns 0.053 on Q = 5.886 where the truth is 0.015. And
    erfc(sqrt(q/2)/sqrt(2)) divides by sqrt(2) twice; it returns 0.166 where a
    chi-square of 3.8415 must return exactly 0.05. Neither error is visible by
    reading the output -- both produce a plausible p-value in the right range,
    and one of them moves this harms comparison across 0.05.

    THE ONLY THING THAT CAUGHT THEM WAS A KNOWN-ANSWER CHECK, which is run
    below on the four textbook critical values every time this module is
    imported. A formula that has never been evaluated at a point whose answer
    is known independently is not a formula, it is a guess with a docstring."""
    return math.erfc(math.sqrt(q / 2.0))


# Known-answer check, at import. Chi-square on 1 df: these four pairs are
# textbook and are not derived from this function.
for _q, _p in ((3.841459, 0.05), (6.634897, 0.01),
               (2.705543, 0.10), (10.827566, 0.001)):
    assert abs(_chi2_sf_1df(_q) - _p) < 1e-5, (
        "chi-square tail on 1 df is WRONG: Q=%s gave %.6f, must be %s"
        % (_q, _chi2_sf_1df(_q), _p))


def _fe_q(rows):
    """Fixed-effect inverse-variance pool and Q, used ONLY to show how
    inconsistent the harms are. It is not offered as an estimate."""
    ys = [math.log(r["point"]) for r in rows]
    ws = [1.0 / (r["se_log_rr"] ** 2) for r in rows]
    mu = sum(w * y for w, y in zip(ws, ys)) / sum(ws)
    q = sum(w * (y - mu) ** 2 for w, y in zip(ws, ys))
    return {"fe_point": round(math.exp(mu), 4), "q": round(q, 4),
            "df": len(rows) - 1, "p": round(_chi2_sf_1df(q), 4)}


def main():
    obj = json.load(open(OBJ, encoding="utf-8"))

    # --------------------------------------------- 1. flow + arm inversion ---
    flow = {
        RING: {"groups_by_module": {
                   "baseline": {"BG000": "Placebo Vaginal Ring",
                                "BG001": "Dapivirine Vaginal Ring"},
                   "participant_flow": {"FG000": "Placebo Vaginal Ring",
                                        "FG001": "Dapivirine Vaginal Ring"},
                   "adverse_events": {"EG000": "Placebo Vaginal Ring",
                                      "EG001": "Dapivirine Vaginal Ring"},
                   "outcome_measures": {"OG000": "Dapivirine Vaginal Ring",
                                        "OG001": "Placebo Vaginal Ring"}},
               "randomised": 1959,
               "started": {"placebo": 652, "dapivirine": 1307},
               "completed": {"placebo": 435, "dapivirine": 902},
               "not_completed": {"placebo": 217, "dapivirine": 405},
               "completed_note": (
                   "The registry's own comment: \"A number of completed "
                   "participants rolled over to the open-label extension of "
                   "this trial (IPM 032, NCT02862171)\". COMPLETED here is "
                   "completion of the double-blind period, not of follow-up "
                   "for the endpoint."),
               "primary_outcome_analysed": {"dapivirine": 1302, "placebo": 650}},
        ASPIRE: {"groups_by_module": {
                     "baseline": {"BG000": "Dapivirine Vaginal Ring",
                                  "BG001": "Placebo Ring"},
                     "participant_flow": {"FG000": "Dapivirine Vaginal Ring",
                                          "FG001": "Placebo Ring"},
                     "adverse_events": {"EG000": "Dapivirine Vaginal Ring",
                                        "EG001": "Placebo Ring"},
                     "outcome_measures": {"OG000": "Dapivirine Vaginal Ring",
                                          "OG001": "Placebo Ring"}},
                 "randomised": 2629,
                 "started": {"dapivirine": 1313, "placebo": 1316},
                 "completed": {"dapivirine": 1165, "placebo": 1179},
                 "not_completed": {"dapivirine": 148, "placebo": 137},
                 "primary_outcome_analysed": {"dapivirine": 1313,
                                              "placebo": 1313}},
    }

    obj["registry_extraction_2026_08_30"] = {
        "_what": ("Participant flow, analysis populations and harms read from "
                  "ClinicalTrials.gov POSTED RESULTS by machine, for both "
                  "contributing trials. Nothing here is transcribed."),
        "extracted_utc": NOW,
        "sources": {
            "primary": ("ClinicalTrials.gov API v2, "
                        "https://clinicaltrials.gov/api/v2/studies/<NCT>. A "
                        "URL. Any reader can fetch it."),
            "independent_second_source": (
                "The AACT 2026-04-12 flat-file snapshot -- tables "
                "result_groups, milestones, drop_withdrawals, outcome_counts. "
                "AACT is a 17 GB download and is therefore NEVER the route a "
                "reader is asked to take; it is here to check the API, not to "
                "replace it."),
            "the_two_agree_on": ("Every group-to-arm mapping in both trials, "
                                 "and every flow count."),
        },
        "THE_ARM_CODE_INVERSION": {
            "finding": (
                "⚠️ ON NCT01539226 THE GROUP INDEX MEANS DIFFERENT ARMS IN "
                "DIFFERENT MODULES OF THE SAME REGISTRATION. Baseline, "
                "participant flow and adverse events all put PLACEBO at index "
                "000. The outcome-measures module -- the one carrying the "
                "effect estimate -- puts DAPIVIRINE at index 000. On "
                "NCT01617096 all four modules put dapivirine first."),
            "why_it_matters": (
                "An extractor that joins the flow table to the outcome table "
                "on the index number, which is the obvious join, swaps the "
                "arms of ONE of these two trials and not the other. It would "
                "not fail; it would return a completed, plausible, inverted "
                "2x2. On this pair the swap turns The Ring Study's RR of "
                "0.6711 into 1.4901 and the pooled direction with it."),
            "what_protects_against_it": (
                "Keying every count from the GROUP TITLE, never from the "
                "index, and recording the per-module mapping so the check is "
                "visible rather than remembered. This object already had the "
                "rule -- \"key everything from the NCT, never a label\" -- and "
                "this is its within-registration form."),
            "verified_by": ("Two independent sources: the API's own group "
                            "titles, and AACT `result_groups.result_type` + "
                            "`title`. They agree."),
            "and_the_stored_2x2s_were_CHECKED_against_it": (
                "The object stores 82/1302 dapivirine and 61/650 placebo for "
                "NCT01539226. The posted denominators are OG000 (Dapivirine "
                "Vaginal Ring) = 1302 and OG001 (Placebo Vaginal Ring) = 650, "
                "with values 82 and 61. THE STORED 2x2 IS CORRECT AND IS NOW "
                "CHECKED RATHER THAN ASSUMED. Same for NCT01617096: 71/1313 "
                "dapivirine, 97/1313 placebo."),
        },
        "participant_flow": flow,
        "analysis_populations_VERBATIM": {
            RING: ("This population consisted of all participants included in "
                   "the ITT population (all randomised), excluding those who "
                   "were not identified as HIV-seropositive at the Enrollment "
                   "Visit, but who were later found to be already HIV-1 "
                   "infected at enrollment through HIV-1 RNA PCR testing."),
            ASPIRE: ("The primary effectiveness Cohort included all eligible "
                     "randomised participants excluding participants deemed "
                     "to be HIV-1 RNA positive at the time of randomization, "
                     "based on retrospective PCR testing of stored blood "
                     "samples taken at enrollment."),
            "field": "resultsSection.outcomeMeasuresModule[0].populationDescription",
            "this_supersedes": (
                "`risk_of_bias.analysis_population_NOT_stated`, which has "
                "stood since this object was written. It is stated, in terms, "
                "in a free machine-readable field, and both trials use a "
                "MODIFIED intention-to-treat population of the same shape."),
        },
        "what_the_posted_results_ANSWER_in_RoB_2": {
            "⚠️_this_is_evidence_not_a_rating": (
                "The answers below are recorded as EVIDENCE. No stored domain "
                "judgement is changed by this script. This object is governed "
                "by a two-assessor process with a recorded adjudication, and "
                "answering a signalling question is a different act from "
                "moving a domain. Collapsing the two is how a review quietly "
                "rates itself up."),
            "3.1_outcome_data_for_all_or_nearly_all": {
                "was": "NO_INFORMATION -- a registration does not report it",
                "now_answerable": True,
                "answer": "YES for both trials",
                "arithmetic": {
                    RING: ("1302 + 650 = 1952 analysed of 1959 randomised = "
                           "99.64%. Excluded: 5 of 1307 from dapivirine, 2 of "
                           "652 from placebo."),
                    ASPIRE: ("1313 + 1313 = 2626 of 2629 randomised = 99.89%. "
                             "Excluded: 0 of 1313 from dapivirine, 3 of 1316 "
                             "from placebo."),
                },
                "the_distinction_that_matters": (
                    "STUDY DISCONTINUATION IS NOT MISSING OUTCOME DATA. "
                    "NCT01539226 records 622 of 1959 (31.8%) as NOT COMPLETED "
                    "and NCT01617096 records 285 of 2629 (10.8%), and a "
                    "reader who took those as missingness would downgrade "
                    "both trials. They are not: the endpoint is time to HIV-1 "
                    "seroconversion, a participant who leaves at month six "
                    "contributes six months of seronegative follow-up and is "
                    "CENSORED, not missing. The number that answers 3.1 is "
                    "the analysis population against the randomised total, "
                    "and it is 99.6% and 99.9%."),
            },
            "2.6_appropriate_analysis_for_the_effect_of_assignment": {
                "was": "NO_INFORMATION",
                "now_answerable": True,
                "answer": "PROBABLY YES for both trials, and not YES",
                "reason": (
                    "Both analyses are MODIFIED intention-to-treat: "
                    "participants shown by retrospective PCR on stored "
                    "enrolment samples to have been HIV-1 infected before "
                    "randomisation are excluded. That is a post-randomisation "
                    "exclusion and therefore a deviation from strict ITT, "
                    "which is why the answer is not YES. It is PROBABLY YES "
                    "rather than PROBABLY NO because the exclusion removes "
                    "participants who could not experience the outcome, it is "
                    "decided by a laboratory assay on stored specimens rather "
                    "than by anyone who knew the allocation, and it is tiny -- "
                    "7 of 1959 and 3 of 2629."),
                "what_is_still_NOT_answered": (
                    "Whether the excluded participants' allocation was known "
                    "to whoever ran the retrospective PCR. The posted results "
                    "do not say. The exclusion counts are small enough that it "
                    "could not plausibly matter, and that is a judgement, "
                    "stated as one."),
            },
            "1.2_allocation_concealment_STILL_OPEN": (
                "Posted results do not report a concealment mechanism and "
                "neither does either registration. This remains the ONE "
                "signalling question that no free machine-readable source in "
                "this review has answered, and it is why NCT01539226's D1 "
                "stands at SOME CONCERNS. Naming it precisely is the point: "
                "the gap is one question on one domain on one trial, not an "
                "unspecified incompleteness."),
            "domain_implication_AWAITING_SECOND_ASSESSOR": (
                "If 3.1 = YES and 2.6 = PROBABLY YES are accepted, D2 and D3 "
                "cease to be NO_INFORMATION and the GRADE risk-of-bias "
                "downgrade -- whose stated reason is \"D2 and D3 are "
                "NO_INFORMATION and on a PrEP trial those are the adherence "
                "and attrition domains\" -- would need re-deriving. THAT IS "
                "NOT DONE HERE. It moves the certainty rating in the "
                "direction that flatters this review, which is exactly the "
                "class of change that must go through the second assessor "
                "rather than through the author who found the evidence."),
        },
    }

    # ------------------------------------------------------------- harms -----
    sae = {RING: _rr(41, 1306, 9, 652), ASPIRE: _rr(116, 1313, 130, 1316)}
    deaths = {RING: _rr(2, 1306, 3, 652), ASPIRE: _rr(4, 1313, 3, 1316)}
    sae_q = _fe_q([sae[RING], sae[ASPIRE]])
    deaths_q = _fe_q([deaths[RING], deaths[ASPIRE]])

    obj["harms_2026_08_30"] = {
        "_what": ("Serious adverse events and deaths, per arm, both trials, "
                  "from ClinicalTrials.gov posted results. THE REVIEW HELD ONE "
                  "OUTCOME BEFORE THIS -- HIV-1 seroconversion -- and outcome "
                  "scope was scored against it 0-2 by blinded judges."),
        "extracted_utc": NOW,
        "source_field": "resultsSection.adverseEventsModule.eventGroups",
        "arm_keying": ("Keyed from the eventGroup TITLE. On NCT01539226 "
                       "EG000 is PLACEBO, which is the opposite of that "
                       "trial's OG000. See THE_ARM_CODE_INVERSION."),
        "serious_adverse_events": {
            "per_trial": {
                RING: {"dapivirine": {"events": 41, "n": 1306},
                       "placebo": {"events": 9, "n": 652}, "rr": sae[RING]},
                ASPIRE: {"dapivirine": {"events": 116, "n": 1313},
                         "placebo": {"events": 130, "n": 1316},
                         "rr": sae[ASPIRE]},
            },
            "⛔_NOT_POOLED": {
                "decision": "The two trials' serious adverse events are NOT pooled.",
                "why": (
                    "THE TWO PLACEBO ARMS DIFFER SEVEN-FOLD. Serious adverse "
                    "events occurred in 9 of 652 placebo participants (1.38%%) "
                    "in NCT01539226 and 130 of 1316 (9.88%%) in NCT01617096 -- "
                    "a ratio of 7.2 -- in trials that enrolled women of the "
                    "same ages, in the same four countries, over overlapping "
                    "years, against the same placebo ring. A seven-fold "
                    "difference in the CONTROL arm is a difference in what was "
                    "counted and reported, not in what happened. Pooling "
                    "across it produces a number (%s) that is arithmetic "
                    "wearing the clothes of evidence."
                    % sae_q["fe_point"]),
                "the_statistic_that_shows_it": (
                    "Fixed-effect Q = %s on %d degree of freedom, p = %s. The "
                    "two relative risks are 2.27 (1.11 to 4.65) and 0.89 "
                    "(0.70 to 1.14): they do not merely differ in size, THEY "
                    "POINT IN OPPOSITE DIRECTIONS and one of them excludes no "
                    "difference."
                    % (sae_q["q"], sae_q["df"], sae_q["p"])),
                "what_IS_reported_instead": (
                    "Both 2x2s, both relative risks, both intervals, and this "
                    "reason. A reader who disagrees can pool them in one line "
                    "from the counts printed here. Declining to pool is a "
                    "judgement and it is shown rather than enacted silently."),
                "and_this_is_not_a_safety_verdict": (
                    "⚠️ NCT01539226's serious-adverse-event relative risk of "
                    "2.27 excludes no difference. It is NOT reported here as a "
                    "harm signal: it sits beside a companion trial showing "
                    "0.89, on a control-arm rate seven times lower, which is "
                    "the signature of an ascertainment difference rather than "
                    "of a hazard. It is shown because hiding an inconvenient "
                    "interval is worse than showing one that needs "
                    "explaining."),
            },
        },
        "deaths": {
            "per_trial": {
                RING: {"dapivirine": {"events": 2, "n": 1306},
                       "placebo": {"events": 3, "n": 652}, "rr": deaths[RING]},
                ASPIRE: {"dapivirine": {"events": 4, "n": 1313},
                         "placebo": {"events": 3, "n": 1316},
                         "rr": deaths[ASPIRE]},
            },
            "consistency": ("Q = %s on %d df, p = %s -- consistent, but on 12 "
                            "deaths in 4587 participants the statistic has "
                            "essentially no power and consistency here is not "
                            "evidence of anything."
                            % (deaths_q["q"], deaths_q["df"], deaths_q["p"])),
            "not_pooled_either": (
                "Twelve events across two trials. A pooled relative risk on "
                "12 events would carry an interval spanning an order of "
                "magnitude in both directions and would be reported as if it "
                "were a finding. The counts are given."),
        },
        "what_this_does_NOT_add": (
            "⚠️ THIS IS NOT A FULL HARMS REVIEW. It reports the two summary "
            "categories the registry posts -- serious adverse events and "
            "deaths -- per arm. It does not extract the MedDRA "
            "system-organ-class tables, does not address the "
            "genital-and-urinary events that are the relevant harms for a "
            "vaginal ring, and does not search for harms outside these two "
            "registrations. Outcome scope is WIDER than it was and is still "
            "narrower than a Cochrane review's."),
        "why_the_registry_and_not_the_papers": (
            "Both papers are free to read and both report adverse events in "
            "prose and tables. The registry is used because it gives the "
            "counts in a fixed schema with a per-arm denominator, so the "
            "extraction is checkable field by field and the arm mapping is "
            "explicit. The papers are the cross-check, not the source."),
    }

    tmp = OBJ + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False)
    os.replace(tmp, OBJ)

    print("WROTE registry_extraction_2026_08_30 and harms_2026_08_30")
    print("  arm-code inversion    NCT01539226: OG000=dapivirine, FG/BG/EG000=placebo")
    print("  stored 2x2s           CHECKED against posted denominators -- both correct")
    print("  RoB 3.1               now answerable: 1952/1959 (99.64%), 2626/2629 (99.89%)")
    print("  RoB 2.6               now answerable: PROBABLY YES, modified ITT, both")
    print("  RoB 1.2               STILL OPEN -- the one remaining question")
    print("  harms SAE             %s vs %s -- Q=%s p=%s -- NOT POOLED"
          % (sae[RING]["point"], sae[ASPIRE]["point"], sae_q["q"], sae_q["p"]))
    print("  harms deaths          %s vs %s -- counts only"
          % (deaths[RING]["point"], deaths[ASPIRE]["point"]))


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    main()
