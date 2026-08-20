"""empagliflozin-hf: a risk-of-bias assessment PER RESULT, from the sources actually read.

WHAT THIS REPLACES. The topic's risk-of-bias limb was discharged by

    "no risk-of-bias assessment was recoverable from the page this object was extracted
     from"

which is a sentence about WHERE SOMEBODY LOOKED. It discharges P46 as written and is the
thing P46's refinement exists to exclude. This is the assessment.

PER RESULT, NOT PER TRIAL -- Handbook 8.2, "risk of bias is assessed for a specific result".
Both results here are the SAME endpoint from two sibling trials, and both are ADJUDICATED
composites, which is what makes D4 assessable at all; a self-reported outcome from the same
trials would need its own judgement and would not inherit this one.

IDENTITY BEFORE JUDGEMENT. Each assessment is keyed to the REGISTRATION ID, and each
trial's arm counts were checked against the published report before a domain was scored:
EMPEROR-Reduced 361/1863 against 462/1867, which is what NEJM 2020 reports and what this
object stores.

WHAT WAS READ, AND WHAT WAS NOT -- stated because the limits of the assessment are part of
the assessment:

  READ  ClinicalTrials.gov NCT03057977 and NCT03057951, registration records including the
        registered title, the verbatim primary outcome and its censoring rule, enrolment,
        and the fact that results are posted.
  READ  the NEJM 2020 abstract of EMPEROR-Reduced (PMID 32865377, doi
        10.1056/NEJMoa2022190), which states the design, the arm sizes and the effect.
  NOT READ  the full methods sections. NEITHER PRIMARY PUBLICATION IS IN PMC OPEN ACCESS --
        the PMID-to-PMCID conversion returns no PMC record for 32865377. So allocation
        CONCEALMENT mechanism, the analysis population definition and the deviation
        handling could not be read, and the domains that depend on them are scored
        NO_INFORMATION rather than LOW.

  THAT LAST LIMIT IS ABOUT OUR ACCESS AND NOT ABOUT THE EVIDENCE, AND IT IS LABELLED AS
  SUCH. A NO_INFORMATION written because a paywall stopped us is not the same as one
  written because the trialists did not describe the method, and this file does not blur
  them: each domain says which it is.

RoB 2, and the ceiling rule this project already applies: a domain that cannot be judged
from the sources READ is NO_INFORMATION, never LOW. Low-by-default asserts a fact;
high-by-default invents a defect.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import atomic_write

TOPIC = "empagliflozin-hf-auto-full-review"
TODAY = "2026-08-20"
STAMP = TODAY.replace("-", "_")
OBJ = os.path.join(REPO, "ssot", TOPIC, TOPIC + ".json")

SHARED_D1 = {
    "judgement": "LOW",
    "basis": "REGISTRATION, READ",
    "reason": (
        "The registered title is 'A Phase III RANDOMISED, DOUBLE-BLIND Trial to Evaluate "
        "Efficacy and Safety of Once Daily Empagliflozin 10 mg Compared to Placebo'. "
        "Randomisation and double-blinding are registered facts, and the arm sizes are "
        "closely balanced, which is what a concealed sequence produces at this scale."),
    "what_is_NOT_established": (
        "THE ALLOCATION CONCEALMENT MECHANISM IS NOT DESCRIBED in the registration, and the "
        "methods section that would describe it is not open access. LOW is scored on "
        "randomisation and balance; it is NOT scored on a concealment mechanism nobody "
        "here has read."),
}

SHARED_D2 = {
    "judgement": "NO_INFORMATION",
    "basis": "NOT ESTABLISHED -- OUR ACCESS, NOT THE EVIDENCE",
    "reason": (
        "Deviations from intended intervention, and whether the analysis was by intention "
        "to treat, cannot be judged from the registration or the abstract. The full "
        "methods section states this and IS NOT OPEN ACCESS -- the PMID-to-PMCID "
        "conversion returns no PMC record for 32865377. THIS IS A LIMIT ON WHAT WE READ, "
        "NOT A GAP IN WHAT THE TRIALISTS REPORTED, and it is labelled so rather than "
        "dressed as a finding about the trial."),
}

SHARED_D4 = {
    "judgement": "LOW",
    "basis": "REGISTRATION, READ VERBATIM",
    "reason": (
        "The registered primary outcome is 'Time to First Event of ADJUDICATED "
        "Cardiovascular (CV) Death or ADJUDICATED Hospitalisation for Heart Failure "
        "(HHF)'. Both components are adjudicated, the trial is double-blind, and death "
        "and hospitalisation are not outcomes an unblinded assessor can shade. THIS "
        "JUDGEMENT IS FOR THIS RESULT ONLY -- a self-reported outcome from the same trial "
        "would need its own, and would not inherit it."),
}

SHARED_D5 = {
    "judgement": "LOW",
    "basis": "REGISTRATION COMPARED WITH PUBLICATION, BOTH READ",
    "reason": (
        "The result pooled here is the trial's FIRST REGISTERED PRIMARY OUTCOME, and the "
        "registered wording matches what the publication reports as the primary. There is "
        "one registered primary, not a set to choose from, so the selection this project "
        "found on DECLARE-TIMI 58 -- two co-primaries and a silent choice between them -- "
        "cannot arise here. The censoring rule is registered in advance and stated "
        "verbatim: patients without an event censored at the last date known to be free of "
        "it or at the end of the planned treatment period, whichever was earlier."),
}

ASSESSMENTS = {
    "NCT03057977": {
        "trial": "EMPEROR-Reduced",
        "result_assessed": ("cardiovascular death or hospitalisation for heart failure, "
                            "first event -- the pooled result, not the trial"),
        "counts_checked_against_the_report": (
            "361 of 1,863 on empagliflozin against 462 of 1,867 on placebo, HR 0.75 (0.65 "
            "to 0.86), NEJM 2020, PMID 32865377, doi 10.1056/NEJMoa2022190. These are the "
            "arm sizes this object stores. IDENTITY BEFORE JUDGEMENT."),
        "D3": {
            "judgement": "LOW",
            "basis": "REGISTRATION, READ",
            "reason": (
                "The outcome is time-to-first-event with a registered censoring rule, so a "
                "participant who leaves the trial contributes their time at risk rather "
                "than becoming a missing value. Enrolment 3,730 is the number randomised "
                "and the number analysed in the published arms is 3,730 -- 1,863 plus "
                "1,867 -- so no randomised participant is absent from the primary result."),
        },
        "overall": "SOME_CONCERNS",
        "overall_reason": (
            "Three domains LOW on read sources and one NO_INFORMATION. Under RoB 2 an "
            "unjudgeable domain cannot yield LOW overall, and SOME_CONCERNS is the "
            "ceiling this project applies where a domain is unread rather than adverse."),
    },
    "NCT03057951": {
        "trial": "EMPEROR-Preserved",
        "result_assessed": ("cardiovascular death or hospitalisation for heart failure, "
                            "first event -- the pooled result, not the trial"),
        "counts_checked_against_the_report": (
            "Enrolment 5,988 as registered; this object stores 2,997 against 2,991, which "
            "sums to 5,988. The arm split reconciles with the registered enrolment."),
        "D3": {
            "judgement": "LOW",
            "basis": "REGISTRATION, READ",
            "reason": (
                "Same registered censoring rule, quoted verbatim on the registry: patients "
                "without a specific endpoint event were censored at the last date known to "
                "be free of the event or at the end of the planned treatment period. "
                "Time-to-event with censoring does not generate missing outcome data in "
                "the way a fixed-timepoint measurement does."),
        },
        "overall": "SOME_CONCERNS",
        "overall_reason": (
            "Identical domain profile to its sibling and for identical reasons -- the two "
            "trials share a protocol shape, a registered outcome wording and a censoring "
            "rule. STATED SEPARATELY RATHER THAN INHERITED: an assessment copied from a "
            "sibling is an assertion about a trial nobody assessed."),
    },
}


def main():
    dry = "--apply" not in sys.argv
    obj = json.load(io.open(OBJ, encoding="utf-8"))
    ncts = set(t.get("nct") for t in (obj.get("inputs") or {}).get("trials") or [])
    for nct in ASSESSMENTS:
        if nct not in ncts:
            sys.exit("REFUSED: %s is not on this object (%r)." % (nct, sorted(ncts)))

    # THE CONSUMER CONTRACT IS by_outcome[<outcome id>][<trial key>], AND THE FIRST DRAFT
    # OF THIS FILE IGNORED IT. It wrote by_outcome["primary/NCT03057977"] -- a flat key
    # nobody reads -- so scripts/p46_queue.py still scored the limb REFUSED and the
    # assessment sat on the object, correct and invisible. THAT IS REGISTRY CLASS 65
    # COMMITTED BY ME AN HOUR AFTER WRITING IT UP: a correct field with no consumer obliged
    # to read it. The shape below is the one arni-hfref uses and the one the scorer reads.
    by_outcome = {"primary": {}}
    for nct, a in ASSESSMENTS.items():
        by_outcome["primary"][nct] = {
            "nct": nct,
            "trial": a["trial"],
            "result_assessed": a["result_assessed"],
            "counts_checked_against_the_report": a["counts_checked_against_the_report"],
            "domains": {
                "D1_randomisation_process": SHARED_D1,
                "D2_deviations_from_intended_intervention": SHARED_D2,
                "D3_missing_outcome_data": a["D3"],
                "D4_measurement_of_the_outcome": SHARED_D4,
                "D5_selection_of_the_reported_result": SHARED_D5,
            },
            "overall": a["overall"],
            "overall_reason": a["overall_reason"],
        }

    _rob = {
        "tool": ("RoB 2 (Cochrane risk-of-bias tool for randomized trials), 22 August 2019 "
                 "version as reproduced in the Cochrane Handbook"),
        "assessed_utc": TODAY,
        "assessed_per": "RESULT, not trial -- Handbook 8.2",
        "by_outcome": by_outcome,
        "sources_read": [
            "ClinicalTrials.gov NCT03057977 -- registered title, verbatim primary outcome, "
            "censoring rule, enrolment 3730, results posted",
            "ClinicalTrials.gov NCT03057951 -- registered title, verbatim primary outcome, "
            "censoring rule, enrolment 5988, results posted",
            "NEJM 2020 abstract of EMPEROR-Reduced, PMID 32865377, doi "
            "10.1056/NEJMoa2022190 -- design, arm sizes, effect estimate",
        ],
        "sources_NOT_read": (
            "THE FULL METHODS SECTIONS. Neither primary publication is in PMC open access; "
            "the PMID-to-PMCID conversion returns no PMC record for 32865377. Allocation "
            "concealment mechanism, analysis population and deviation handling could not "
            "be read, and D2 is NO_INFORMATION for that reason."),
        "ceiling": {"statement": "A domain that cannot be judged from the sources READ is NO_INFORMATION, never LOW. Low-by-default asserts a fact; high-by-default invents a defect. Overall is capped at SOME_CONCERNS wherever a domain is NO_INFORMATION.", "shape_note": "A DICT, NOT A STRING. paper_projector does ceil.get('statement'), so a bare string here raises AttributeError and the ENTIRE MANUSCRIPT VANISHES -- 17,012 chars and 27 sections down to a 318-char projector-failed banner."},
        "WHAT_WOULD_RAISE_THIS_TO_LOW": (
            "Reading the two methods sections. D2 is the only domain scored on absence, "
            "and the absence is OUR ACCESS rather than the trialists' reporting -- so this "
            "is a queue item with a named exit, not a fact about the trials. IT IS "
            "LABELLED THAT WAY DELIBERATELY: a NO_INFORMATION written because a paywall "
            "stopped us is not the same as one written because a method was never "
            "described, and calling them the same is how a provenance refusal comes back "
            "wearing an evidence refusal's clothes."),
        "supersedes": (
            "The prior state was 'no risk-of-bias assessment was recoverable from the page "
            "this object was extracted from' -- a sentence about where somebody looked. "
            "Four of five domains are now judged on sources read and named."),
    }
    atomic_write.merge_not_overwrite(obj, "risk_of_bias", _rob,
                                     TODAY.replace("-", "_"))

    obj.setdefault("display_change_announced", []).append({
        "date": TODAY,
        "change": "risk of bias assessed PER RESULT for both contributing results",
        "values_moved": "NONE -- no estimate changes",
        "what_changed": (
            "Both registrations were read and both results assessed on RoB 2: D1, D3, D4 "
            "and D5 LOW on read sources; D2 NO_INFORMATION because the methods sections "
            "are not open access. Overall SOME_CONCERNS for each."),
        "why": ("The previous risk-of-bias limb was discharged by a sentence about where "
                "somebody looked, which is what P46's refinement exists to exclude."),
    })

    print("empagliflozin-hf: 2 results assessed per result; D2 NO_INFORMATION, overall "
          "SOME_CONCERNS each")
    if dry:
        print("DRY RUN -- pass --apply to write")
        return
    atomic_write.write_json(OBJ, obj, indent=1)
    print("wrote %s" % OBJ)


if __name__ == "__main__":
    main()
