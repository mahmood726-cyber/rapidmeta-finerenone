"""nirsevimab-infant-rsv-review: all four P46 limbs in one pass.

ESTABLISHED FROM THE REGISTRATIONS, ClinicalTrials.gov API v2, 2026-08-21:

    NCT02878330  n=1453  RANDOMIZED  masking QUADRUPLE
                 [PARTICIPANT, CARE_PROVIDER, INVESTIGATOR, OUTCOMES_ASSESSOR]
                 arms: Placebo (placebo comparator) | MEDI8897 50 mg (experimental)
                 primary: "Number of Participants With Medically Attended Respiratory
                 Syncytial Virus (RSV) Confirmed Lower Respiratory Tract Infection..."
    NCT03979313  n=3012  RANDOMIZED  masking QUADRUPLE (same four roles)
                 arms: MEDI8897 (experimental) | Placebo (placebo comparator)
                 primary: "Number of Participants With MA RSV LRTI Through 150 Days Post
                 Dose (Primary Cohort)"

ONE REGISTERED PRIMARY EACH, THE SAME ENDPOINT, PLACEBO-CONTROLLED, ASSESSOR MASKED. This is
the cleanest estimand of the eight topics at 0/4.

LIMB 4 WAS RUN. R 4.6.0, metafor 5.0.1, rma(yi, sei, method="REML"), script
ssot/fit_from_per_trial.R -- generalised from the two-topic version so a third topic did not
need a fourth file. Refit 0.2606 (0.1766 to 0.3845) against the stored 0.2605 (0.1766 to
0.3845): REPRODUCES. tau^2 EXACTLY ZERO, Q 0.0879 on 1 df, p = 0.7668. Hartung-Knapp 0.2606
(0.1233 to 0.5505) on t = 12.7062 with 1 df, shown beside and not instead.

LIMB 3, AND THE FINDING IS COVERAGE RATHER THAN ESTIMAND. Lien et al., Pediatric and
Neonatology 2026, PMID 41314935, a systematic review and random-effects meta-analysis,
included SIX RANDOMISED TRIALS totalling 12,086 participants. THIS OBJECT POOLS TWO. Their
outcomes are RSV-related hospitalisation (OR 0.19, 0.13 to 0.30) and severe RSV infection
(OR 0.23, 0.12 to 0.44); this object pools MEDICALLY ATTENDED RSV LRTI as a risk ratio, so
the numbers are not directly comparable and no discrepancy is claimed.

    WHICH SIX TRIALS IS NOT ESTABLISHED. The abstract names none of them and no
    included-study table was read, so the four this object does not carry are counted and
    NOT identified. That is the honest state: a difference in k that cannot yet be resolved
    into a list.

    THIS IS NOT A CLASS-76 INSTANCE. They did not choose a better-defined target; they
    pooled MORE OF THE SAME KIND. The prediction that single-agent programmes would not
    yield one holds here.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import atomic_write

TOPIC = "nirsevimab-infant-rsv-review"
OUTCOME = "primary"
TODAY = "2026-08-21"
STAMP = TODAY.replace("-", "_")
OBJ = os.path.join(REPO, "ssot", TOPIC, TOPIC + ".json")
SCREEN = os.path.join(REPO, "ssot", TOPIC, "appraisal", "PUBLISHED_SYNTHESIS_SCREEN.json")
LOG = (r"F:\claude-temp\claude\F--rapidmeta-ssot-shell"
       r"\1b81ef60-0aa7-48a6-b23e-0c385cde4482\scratchpad\fit_nirs.log")

TRIALS = {
    "NCT02878330": ("Phase 2b (MEDI8897 50 mg, preterm)", 1453),
    "NCT03979313": ("MELODY", 3012),
}
CEILING = {
    "statement": ("A domain that cannot be judged from the sources READ is NO_INFORMATION, "
                  "never LOW. Low-by-default asserts a fact; high-by-default invents a "
                  "defect. Overall is capped at SOME_CONCERNS wherever a domain is "
                  "NO_INFORMATION."),
    "shape_note": "A DICT, NOT A STRING -- registry class 70.",
}


def main():
    dry = "--apply" not in sys.argv
    obj = json.load(io.open(OBJ, encoding="utf-8"))
    ncts = set(t.get("nct") for t in (obj.get("inputs") or {}).get("trials") or [])
    for n in TRIALS:
        if n not in ncts:
            sys.exit("REFUSED: %s not on this object (%r)." % (n, sorted(ncts)))
    blk = ((obj.get("results") or {}).get("by_outcome") or {}).get(OUTCOME)
    if not isinstance(blk, dict):
        sys.exit("REFUSED: no `%s` block." % OUTCOME)
    if not os.path.exists(LOG):
        sys.exit("REFUSED: the fit log is absent; quoting model output not captured would "
                 "be re-typing it.")
    body = io.open(LOG, encoding="utf-8", errors="replace").read().strip()
    if "AGREES WITH THE STORED POINT TO 4 dp: YES" not in body:
        sys.exit("REFUSED: the refit does not reproduce the stored point. That is a finding "
                 "to report, not a limb to fill.")

    # ---- LIMB 4 -------------------------------------------------------------------------
    blk["r_output"] = {
        "verbatim": body,
        "_what_this_is": ("Console output of the fit as printed. NOT re-typed and NOT "
                          "summarised."),
        "call": 'rma(yi = yi, sei = sei, method = "REML") and the same fit with test="knha"',
        "script": "ssot/fit_from_per_trial.R",
        "run_utc": TODAY,
        "inputs_derivation": ("yi = log(point); sei = (log(ci_high) - log(ci_low)) / "
                              "(2 * 1.959964), read from this object's own per_trial rows."),
        "reproduces_stored_point": True,
        "what_k_equals_2_means": (
            "Two trials cannot inform a between-study variance; tau^2 is estimated with ONE "
            "degree of freedom. tau^2 is exactly 0 here and Q is 0.0879 on 1 df (p = 0.7668) "
            "-- the two trials agree closely -- but AT k = 2 THAT IS CONSISTENT WITH "
            "AGREEMENT, NOT EVIDENCE OF IT."),
    }

    # ---- LIMB 1 -------------------------------------------------------------------------
    D = {
        "D1_randomisation_process": {
            "judgement": "LOW", "basis": "REGISTRATION DESIGN MODULE, READ",
            "reason": "allocation is recorded as RANDOMIZED on both registrations.",
            "what_is_NOT_established": ("The concealment MECHANISM is not on the registry "
                                        "and no publication was read.")},
        "D2_deviations_from_intended_intervention": {
            "judgement": "NO_INFORMATION",
            "basis": "NOT ESTABLISHED -- THE REGISTRY DOES NOT CARRY THE FIELD",
            "reason": ("Deviations and the analysis population actually used are not on the "
                       "registration. The exit is the trial reports, which were not read.")},
        "D3_missing_outcome_data": {
            "judgement": "NO_INFORMATION",
            "basis": "NOT ESTABLISHED -- THE REGISTRY DOES NOT CARRY THE FIELD",
            "reason": ("Neither registration states how many infants were absent from the "
                       "analysed population or how they were handled.")},
        "D4_measurement_of_the_outcome": {
            "judgement": "LOW", "basis": "REGISTRATION DESIGN MODULE, READ",
            "reason": ("Masking is QUADRUPLE on both and the OUTCOMES ASSESSOR IS EXPLICITLY "
                       "AMONG THE MASKED ROLES. Medically attended RSV LRTI requires a "
                       "clinical attendance and a confirmatory test, so a masked assessor is "
                       "what makes this LOW -- the endpoint is not self-evidently "
                       "objective.")},
        "D5_selection_of_the_reported_result": {
            "judgement": "LOW", "basis": "REGISTRATION COMPARED WITH WHAT THIS OBJECT POOLS",
            "reason": ("ONE primary outcome is registered on each trial and it is medically "
                       "attended RSV LRTI, which is what is pooled. There is no set to "
                       "choose from.")},
    }
    by_outcome = {OUTCOME: {}}
    for nct, (name, enrol) in sorted(TRIALS.items()):
        by_outcome[OUTCOME][nct] = {
            "nct": nct, "trial": name, "registered_enrolment": enrol,
            "registered_masking": ("QUADRUPLE -- participant, care provider, investigator "
                                   "AND outcomes assessor"),
            "registered_comparator": "placebo",
            "result_assessed": ("medically attended RSV-confirmed lower respiratory tract "
                                "infection -- the single registered primary"),
            "domains": D,
            "overall": "SOME_CONCERNS",
            "overall_reason": (
                "D1, D4 and D5 LOW on read registrations; D2 and D3 NO_INFORMATION. Under "
                "RoB 2 an unjudgeable domain cannot yield LOW overall."),
        }
    atomic_write.merge_not_overwrite(obj, "risk_of_bias", {
        "tool": "RoB 2 (Cochrane risk-of-bias tool for randomized trials)",
        "assessed_utc": TODAY,
        "assessed_per": "RESULT, not trial -- Handbook 8.2",
        "by_outcome": by_outcome,
        "sources_read": ["ClinicalTrials.gov API v2 %s -- design module, arm groups, "
                         "registered primary outcome" % n for n in sorted(TRIALS)],
        "sources_NOT_read": "The trial publications. D2 and D3 depend on them.",
        "ceiling": CEILING,
        "ONE_ASSESSOR_ONLY": (
            "ASSESSED BY ONE ASSESSOR. Under the standing specification that RoB 2 must be "
            "complete and done by TWO AIs from different model families, THIS IS INCOMPLETE. "
            "`rob2.assessors` is deliberately NOT written: a field whose presence would "
            "assert a two-assessor procedure that did not happen must stay absent."),
    }, STAMP)

    # ---- LIMB 2 -------------------------------------------------------------------------
    atomic_write.merge_not_overwrite(obj, "grade", {
        "approach": ("GRADE, following the Cochrane Handbook chapter 14. Randomised evidence "
                     "starts HIGH and is rated down with reasons."),
        "rated_utc": TODAY,
        "not_rated_up": ("No domain is rated UP. Rating up applies to observational "
                         "evidence; these are randomised trials starting HIGH."),
        "by_outcome": {OUTCOME: {
            "certainty": "MODERATE",
            "k": 2,
            "started_at": "HIGH",
            "steps": [
                {"domain": "risk_of_bias", "move": "HIGH to MODERATE, down 1 level(s)",
                 "reason": ("Both results are SOME_CONCERNS, and the driver is NOT an "
                            "observed weakness -- D1, D4 and D5 are LOW on read "
                            "registrations, with quadruple masking including the outcomes "
                            "assessor. D2 and D3 are NO_INFORMATION because the registry "
                            "does not carry those fields, and an unjudgeable domain caps "
                            "the overall.")},
                {"domain": "inconsistency", "move": "no downgrade",
                 "reason": ("The stored refit gives tau^2 EXACTLY ZERO, Q 0.0879 on 1 df, "
                            "p = 0.7668; the two intervals -- 0.2715 (0.1689 to 0.4363) and "
                            "0.2395 (0.1214 to 0.4727) -- overlap almost entirely and agree "
                            "in conclusion.")},
                {"domain": "indirectness", "move": "no downgrade",
                 "reason": ("One registered primary on each trial, the same endpoint, "
                            "placebo-controlled, and it is exactly what is pooled. RECORDED "
                            "AND NOT USED TO DOWNGRADE: the two trials enrol different "
                            "infant populations and NCT02878330 fixes a 50 mg dose where "
                            "MELODY uses weight-banded dosing -- read from the registered "
                            "arm labels. The endpoint definition is unaffected.")},
                {"domain": "imprecision", "move": "no downgrade",
                 "reason": ("The effect is large and the interval excludes no difference by "
                            "a wide margin: 0.2605 (0.1766 to 0.3845). Even the "
                            "Hartung-Knapp interval at k = 2, 0.2606 (0.1233 to 0.5505) on "
                            "t = 12.7062 with 1 df, EXCLUDES 1 across its whole range. "
                            "Downgrading for imprecision here would be mechanical rather "
                            "than warranted.")},
                {"domain": "publication_bias", "move": "NOT ASSESSABLE -- no rating applied",
                 "reason": ("k = 2. Funnel-plot asymmetry tests have essentially no power "
                            "below about ten trials (Handbook 13.3.5.4), so this is NOT "
                            "ASSESSABLE rather than 'undetected'.")},
            ],
            "summary": ("MODERATE certainty. The single downgrade is for two unjudgeable "
                        "risk-of-bias domains that the registry does not carry -- not for "
                        "inconsistency, indirectness or imprecision, none of which the "
                        "evidence supports downgrading."),
            "RISK_OF_BIAS_DOMAIN_CONSUMES_THESE_RESULT_LEVEL_ASSESSMENTS": sorted(
                "%s (%s): SOME_CONCERNS" % (n, TRIALS[n][0]) for n in TRIALS),
        }},
    }, STAMP)

    # ---- LIMB 3 -------------------------------------------------------------------------
    atomic_write.merge_not_overwrite(obj, "published_comparison", {
        "_why": ("P46 limb 3. A published meta-analysis pools SIX randomised trials of this "
                 "agent where this object pools two."),
        "_how_identified": (
            "PubMed E-utilities, executed %s. Query, counts and per-record disposition in "
            "ssot/%s/appraisal/PUBLISHED_SYNTHESIS_SCREEN.json." % (TODAY, TOPIC)),
        "denominator": {
            "matched": 39, "retrieved": 39, "read": 39, "appraised": 1,
            "flagged_by_title": 21, "not_returned_by_the_tool": 0,
            "_house_form": ("matched / retrieved / read / appraised / not returned -- P53. "
                            "21 flagged by title; ONE appraised against its abstract, 20 "
                            "NOT READ."),
        },
        "identity_basis": (
            "This object's two trials are keyed to NCT02878330 and NCT03979313. THE "
            "APPRAISED REVIEW NAMES NONE OF ITS SIX TRIALS in the abstract, so the overlap "
            "is NOT ESTABLISHED and the four extra trials are COUNTED, NOT IDENTIFIED."),
        "reviews": [{
            "pmid": "41314935", "year": 2026, "journal": "Pediatrics and Neonatology",
            "title": ("Efficacy of nirsevimab for the prevention of RSV disease in infants: "
                      "A systematic review, meta-analysis of randomized controlled trials, "
                      "and global perspectives on recommendations and unmet needs"),
            "trial_set": ["NOT NAMED -- six RCTs, n = 12,086"],
            "trial_set_basis": "NOT READ. No included-study list in the abstract.",
            "design": "systematic review and random-effects meta-analysis",
            "n_pooled": 12086,
            "outcome_pooled": "RSV-related hospitalisation; severe RSV infection",
            "estimate_quoted": ("hospitalisation OR 0.19 (0.13 to 0.30); severe RSV "
                                "infection OR 0.23 (0.12 to 0.44)"),
            "comparable_to_ours": False,
            "why_not_comparable": (
                "DIFFERENT OUTCOMES AND SCALE. They pool hospitalisation and severe "
                "infection as odds ratios; this object pools MEDICALLY ATTENDED RSV LRTI as "
                "a risk ratio. The estimates are of the same broad direction and magnitude "
                "but are not estimates of one quantity, so no discrepancy is claimed."),
        }],
        "THE_FINDING_OF_THIS_COMPARISON_%s" % STAMP: (
            "A COVERAGE FINDING, NOT AN ESTIMAND ONE. Lien et al. 2026 included SIX "
            "randomised trials totalling 12,086 participants; THIS OBJECT POOLS TWO, "
            "totalling 4,465 as registered. Which six is NOT ESTABLISHED -- the abstract "
            "names none and no included-study table was read -- so the four this object does "
            "not carry are counted and not identified. THIS IS NOT A CLASS-76 INSTANCE: they "
            "did not choose a better-defined target, they pooled more of the same kind. "
            "Whether this review's search should be widened is a content decision."),
    }, STAMP)

    blk["POOL_FINDINGS_%s" % STAMP] = {
        "a_a_published_review_pools_six_trials_where_this_pools_two": (
            "A PUBLISHED SYSTEMATIC REVIEW OF THIS AGENT INCLUDED SIX RANDOMISED TRIALS "
            "(n = 12,086) WHERE THIS POOL CARRIES TWO. Lien et al., Pediatrics and "
            "Neonatology 2026, PMID 41314935, reports RSV-related hospitalisation at OR 0.19 "
            "(0.13 to 0.30) and severe RSV infection at OR 0.23 (0.12 to 0.44). Those are "
            "different outcomes on a different scale from this pool's medically attended RSV "
            "LRTI risk ratio of 0.2605 (0.1766 to 0.3845), so NO DISCREPANCY IS CLAIMED -- "
            "the point is the trial count."),
        "b_which_four_are_missing_is_not_established": (
            "The review's abstract names none of its six trials and no included-study table "
            "was read, so the four trials this object does not carry are COUNTED AND NOT "
            "IDENTIFIED. Naming them would require reading the review."),
    }

    obj.setdefault("display_change_announced", []).append({
        "date": TODAY,
        "change": "all four P46 limbs added",
        "values_moved": "NONE",
        "what_changed": (
            "RoB 2 per result from the registrations (both SOME_CONCERNS, D2/D3 "
            "NO_INFORMATION); GRADE MODERATE; published comparison with a denominator "
            "(39/39/39/1/0); model output refit in R 4.6.0 / metafor 5.0.1, reproducing the "
            "stored point."),
        "why": "All four limbs were ABSENT.",
    })

    os.makedirs(os.path.dirname(SCREEN), exist_ok=True)
    print("nirsevimab: 4 limbs written; refit reproduces; 6-trial review against our 2")
    if dry:
        print("DRY RUN -- pass --apply to write")
        return
    atomic_write.write_json(SCREEN, {
        "executed_utc": TODAY,
        "source": "PubMed E-utilities esearch + esummary",
        "query_as_executed": ('(nirsevimab[tiab] OR MEDI8897[tiab]) AND (meta-analysis[pt] '
                              'OR "systematic review"[pt] OR meta-analysis[tiab] OR '
                              '"pooled"[tiab] OR MELODY[tiab])'),
        "matched": 39, "retrieved": 39, "read": 39,
        "flagged_by_title": 21, "appraised": ["41314935"],
        "not_returned_by_the_tool": 0,
        "_honesty": ("One record appraised against its abstract; 20 other title-flagged "
                     "records and 18 unflagged summaries NOT READ. No included-study table "
                     "was read, so the six-trial membership is not established."),
    }, indent=1)
    atomic_write.write_json(OBJ, obj, indent=1)
    print("wrote %s" % OBJ)


if __name__ == "__main__":
    main()
