# -*- coding: utf-8 -*-
"""Declare `question_pico` / `trial_pico` so the indirectness domain can be DERIVED.

WHY THIS EXISTS. `ssot/indirectness_procedure.py` has implemented Handbook 14.2.2 domain
(3) for months and nothing called it. It is now wired into `grade_engine.d_indirectness`,
but wiring converted ZERO of the 54 live results, because the module refuses without a
DECLARED question PICO and exactly one object carried one. The binding constraint was
never the unwired code. It is the undeclared question.

⛔ WHAT IS DECLARED HERE IS A JUDGEMENT, AND IT IS LABELLED AS ONE. The question PICO is
the review's own question restated axis by axis; the trial PICO is a summary of what the
contributing trials registered. Neither is computed. The gain is not that a machine decided
anything -- it is that the comparison is now EXPLICIT, REPEATABLE and CHECKABLE by a reader
against strings the page shows.

⭐ EVERY QUESTION-PICO VALUE IS QUOTED FROM THE QUESTION PROSE, and the anti-rescoping
guard in `indirectness_procedure.question_pico_divergence` enforces it: a value that does
not appear in the question a reader meets REFUSES the rating and names both strings.
Narrowing the declared population to escape a downgrade is the defect that guard closes,
so these declarations are written to survive it rather than to dodge it.

⚠️ AND EACH ONE RECORDS WHAT IT EXCLUDES. Scope is the axis this corpus loses on in blinded
comparison, and a declared exclusion is the material that fixes it: a reader should be able
to see what the question does NOT cover without reverse-engineering it from the trials.

TWO TOPICS ARE REFUSED RATHER THAN DECLARED, and the refusals are the finding -- see
REFUSED below. Inferring a PICO from the included studies returns DIRECT by construction
and would hand out a certainty letter that means nothing.
"""
from __future__ import annotations

import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from atomic_write import write_json            # noqa: E402
import indirectness_procedure as IP            # noqa: E402
import grade_engine as ge                      # noqa: E402

STAMP = "2026-08-30"

# ---------------------------------------------------------------------------
# DECLARED. Question values are quoted from the question prose; trial values are
# summarised from the registry material this object already holds.
# ---------------------------------------------------------------------------
DECLARE = {
    "alirocumab-lipid": {
        "oid": "ldlc_pct_change_wk24",
        "question_pico": {
            "population": "adults treated for hypercholesterolaemia",
            "intervention": "alirocumab",
            "comparator": "placebo",
            "outcome": "calculated LDL cholesterol",
        },
        "trial_pico": {
            "population": ("adults treated for hypercholesterolaemia who were not "
                           "adequately controlled on their maximally tolerated "
                           "lipid-modifying therapy"),
            "intervention": "alirocumab",
            "comparator": "placebo",
            "outcome": "calculated LDL cholesterol",
            "source": ("ClinicalTrials.gov eligibility modules for the 8 contributing "
                       "NCTs, as already quoted verbatim on this object at "
                       "results.by_outcome.ldlc_pct_change_wk24.per_trial[].registered_eligibility "
                       "(read %s). Every one enrols participants 'not adequately "
                       "controlled' on existing lipid-modifying therapy." % STAMP),
        },
        "excludes": [
            "Untreated hypercholesterolaemia. Every contributing trial enrolled "
            "participants already on lipid-modifying therapy and inadequately "
            "controlled on it, so the pooled estimate does not speak to alirocumab as "
            "first-line therapy in an untreated population.",
            "Children and adolescents: the trials set a minimum age of 18.",
            "Clinical events. The outcome is a laboratory measure at week 24, not "
            "cardiovascular death, myocardial infarction or stroke.",
        ],
    },
    "apixaban-vte-treatment": {
        "oid": "recurrent_vte",
        "question_pico": {
            "population": "adults with acute or recent venous thromboembolism",
            "intervention": "apixaban",
            "comparator": ("conventional anticoagulation, another direct oral "
                           "anticoagulant, or placebo"),
            "outcome": "recurrent venous thromboembolism",
        },
        "trial_pico": {
            "population": ("adults with acute symptomatic venous thromboembolism, one "
                           "of the three trials restricted to cancer-associated venous "
                           "thromboembolism"),
            "intervention": "apixaban",
            "comparator": "conventional anticoagulation, another direct oral anticoagulant",
            "outcome": "recurrent venous thromboembolism",
            "source": ("ClinicalTrials.gov records for CARAVAGGIO (NCT03045406, "
                       "cancer-associated VTE, comparator dalteparin), COBRRA "
                       "(NCT03266783, comparator rivaroxaban -- another DOAC) and the "
                       "Japanese acute DVT/PE study (NCT01780987, comparator "
                       "conventional heparin/VKA), as held on this object (read %s)."
                       % STAMP),
        },
        "excludes": [
            "A placebo comparison. The question offers placebo as one of three "
            "comparators and NO contributing trial has a placebo arm, so the pooled "
            "estimate is entirely against active anticoagulation.",
            "Extended secondary prevention after the initial treatment period.",
            "Bleeding. The question asks about recurrent VTE 'and on bleeding'; this "
            "pooled result is the recurrence outcome only.",
        ],
    },
    "gepotidacin-urinary-tract-auto-full-review": {
        "oid": "primary",
        "question_pico": {
            "population": "adults with uncomplicated urinary tract infection",
            "intervention": "gepotidacin",
            "comparator": "nitrofurantoin",
            "outcome": ("therapeutic response (combined clinical and microbiological "
                        "success) at the test-of-cure visit"),
        },
        "trial_pico": {
            "population": ("female participants aged 12 years and over with "
                           "uncomplicated urinary tract infection"),
            "intervention": "gepotidacin",
            "comparator": "nitrofurantoin",
            "outcome": ("therapeutic response (combined clinical and microbiological "
                        "success) at the test-of-cure visit"),
            "source": ("ClinicalTrials.gov eligibility for EAGLE-2 (NCT04020341) and "
                       "EAGLE-3 (NCT04187144), quoted on this object: both require "
                       "'The participant is female' and an age of 12 years or over "
                       "(read %s)." % STAMP),
        },
        "excludes": [
            "Men. Both trials require female participants, so the pooled estimate says "
            "nothing about uncomplicated UTI in men.",
            "⚠️ AND IT IS NOT A CLEAN SUBSET OF THE QUESTION: the trials enrol from age "
            "12, so part of the evidence is in ADOLESCENTS while the question asks "
            "about adults. The evidence is at once narrower (female only) and broader "
            "(includes under-18s) than the question -- which is a SUBSTITUTION on the "
            "population axis, not merely a restriction.",
            "Complicated urinary tract infection, pyelonephritis, and catheter-"
            "associated infection.",
        ],
    },
}

# ---------------------------------------------------------------------------
REFUSED = {
    "cab-prep-hiv-review": (
        "REFUSED -- THE QUESTION STATES NO POPULATION, AND THE PROSE IS BROKEN. The "
        "question reads: 'In Long-acting injectable cabotegravir versus daily oral "
        "TDF/FTC for HIV pre-exposure prophylaxis, what is the effect ON VERSUS daily "
        "oral TDF/FTC on documented incident HIV infection?' -- the comparator is "
        "duplicated, the sentence is ungrammatical, and NO population appears anywhere "
        "in it. Declaring a population here would mean reading it off HPTN 083/084, "
        "which is inferring the question from the studies that answer it. That returns "
        "DIRECT by construction and is the single most dangerous answer this domain can "
        "give. ⇒ The repair is EDITORIAL and comes first: fix the question prose and "
        "state the population the review is asking about. Then the PICO can be quoted "
        "from it. (The broken sentence is also rendered to readers in "
        "CAB_PREP_HIV_REVIEW.html -- a clarity defect independent of GRADE.)"),
    "sotagliflozin-hf": (
        "REFUSED -- THIS IS A SCOPED QUESTION, NOT A PICO ONE. The question reads 'In "
        "both phase 3 trials that supported sotagliflozin's approval, what is the "
        "effect of...', which scopes the question to the trials that answer it. "
        "Population, intervention, comparator and outcome then match BY CONSTRUCTION "
        "and the indirectness domain carries no information -- structurally "
        "uninformative rather than unmeasured. The engine already models this as "
        "`question_scope.scoped_to_contributing_trials`, and it is `None` here. ⇒ The "
        "correct act is an explicit scope DECLARATION with a recorded reason, not a "
        "PICO. It is deliberately left undeclared: the engine names this state as its "
        "one gaming risk, and declaring it is an editorial decision with a caveat "
        "attached to every rating it permits."),
}


def main():
    changed, refused = [], []
    for slug, spec in DECLARE.items():
        path = os.path.join(_HERE, slug, slug + ".json")
        canon = json.load(open(path, encoding="utf-8"))
        oid = spec["oid"]
        res = canon["results"]["by_outcome"][oid]

        qp = dict(spec["question_pico"])
        # ⛔ FAIL CLOSED. Refuse to write a PICO the guard would reject: a declaration
        # that cannot survive its own invariant is a defect, not a rating.
        diverged = IP.question_pico_divergence(canon, qp)
        if diverged:
            print("  SKIP %-44s declared value not in question prose: %s"
                  % (slug, ", ".join(diverged)))
            refused.append(slug)
            continue
        qp["declared_utc"] = STAMP
        qp["source"] = ("The question and title as published on this page, restated axis "
                        "by axis. Every value appears verbatim in the question prose, "
                        "which the anti-rescoping guard enforces.")
        qp["excludes"] = spec["excludes"]
        res["question_pico"] = qp
        res["trial_pico"] = dict(spec["trial_pico"])

        rec = ge.derive(canon, oid)
        d = [x for x in rec["domains"] if x["domain"] == "indirectness"][0]
        write_json(path, canon, indent=1)
        changed.append((slug, oid, d["state"], d.get("levels"), rec["rated"]))
        print("  WROTE %-44s indirectness=%-11s levels=%s rated=%s"
              % (slug, d["state"], d.get("levels"), rec["rated"]))

    print()
    for slug, why in REFUSED.items():
        print("  REFUSED %s" % slug)
        print("     %s" % why[:160].replace("\n", " "))
    print()
    print("declared %d, refused %d (%d by stop-condition, %d by the guard)"
          % (len(changed), len(REFUSED) + len(refused), len(REFUSED), len(refused)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
