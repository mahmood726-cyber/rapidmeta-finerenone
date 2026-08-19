"""CREATE the `ablation-af-heart-failure` object -- one of the three reviews
`ablation-af-review` was split into.

CREATES, AND REFUSES TO OVERWRITE. If the object already exists this script exits without
touching it: a create script that silently replaces is a wholesale write, which is the class
this repository has met six times.

WHAT IT WRITES, and where each part comes from:
  question / title      composed for THIS review and traceable to the two trials' own
                        registry fields -- never a copied registry string, which is the defect
                        that blocked the parent topic
  inputs.trials         carried across from `ablation-af-review` WITH their original
                        provenance, not re-typed
  screening             criteria derived post hoc, `predefined: false` on its face
  screening_of_remainder  the 43 verdicts from
                        evidence/2026-08-19-batch1/ablation_hf_screening.json
  shared_with_other_topics  P22: both trials appear in the sibling reviews BY DESIGN
  results.by_outcome    A REFUSAL TO POOL, with the pool it declines shown beside it
"""
import io
import json
import math
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPIC = "ablation-af-heart-failure"
DEST_DIR = os.path.join(REPO, "ssot", TOPIC)
DEST = os.path.join(DEST_DIR, TOPIC + ".json")
SRC = os.path.join(REPO, "ssot", "ablation-af-review", "ablation-af-review.json")
SCREEN = os.path.join(REPO, "evidence", "2026-08-19-batch1", "ablation_hf_screening.json")
Z = 1.959963984540054

QUESTION = ("In adults with atrial fibrillation and heart failure, what is the effect of "
            "catheter ablation of atrial fibrillation compared with medical rate- or "
            "rhythm-control therapy on the composite of all-cause mortality and heart-failure "
            "events?")


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if os.path.exists(DEST):
        print("REFUSED: %s already exists. This script creates; it does not overwrite." % DEST)
        return 1

    src = json.load(io.open(SRC, encoding="utf-8"))
    screen = json.load(io.open(SCREEN, encoding="utf-8"))
    keep = {"NCT00643188", "NCT01420393"}
    trials = [t for t in src["inputs"]["trials"] if t.get("nct") in keep]
    if len(trials) != 2:
        print("REFUSED: expected 2 trials carried across, got %d" % len(trials))
        return 1

    per = [t for t in src["results"]["by_outcome"]["primary"]["per_trial"]
           if t.get("nct") in keep]
    ys = [math.log(t["point"]) for t in per]
    ses = [(math.log(t["ci_high"]) - math.log(t["ci_low"])) / (2 * Z) for t in per]
    w = [1.0 / s ** 2 for s in ses]
    fe = sum(a * b for a, b in zip(w, ys)) / sum(w)
    q = sum(a * (b - fe) ** 2 for a, b in zip(w, ys))
    mu, se = fe, math.sqrt(1.0 / sum(w))

    obj = {
        "app_id": TOPIC,
        "schema_version": src.get("schema_version"),
        "title": "Catheter ablation of atrial fibrillation in patients with heart failure, "
                 "against medical rate- or rhythm-control therapy",
        "question": QUESTION,
        "question_provenance": {
            "state": "COMPOSED FOR THIS REVIEW, TRACEABLE TO NAMED REGISTRY FIELDS",
            "not_a_copied_registry_string": (
                "The parent object's question WAS a copied registry string -- CABANA's primary "
                "outcome measure, truncated at 120 characters mid-word, filling `title`, "
                "`question` and both outcome fields at once. That is the defect this split was "
                "decided from. This question is composed, and every limb of it points at a "
                "field: POPULATION at conditionsModule.conditions of both included trials "
                "('Atrial Fibrillation', 'Heart Failure'), INTERVENTION and COMPARATOR at "
                "their armGroups, and the OUTCOME at each trial's registered primary."),
            "checkable_by": "scripts/lint_question_is_a_question.py",
        },
        "built": "2026-08-19",
        "build_mode": "split_from_parent",
        "split_provenance": {
            "parent": "ablation-af-review",
            "decision": "DECIDED-ablation-af-review-2026-08-19.md",
            "why_three_and_not_one": (
                "The parent's question was ambiguous between three legitimate readings and the "
                "packet framed the choice as WHICH TRIALS TO DROP. Choosing is a decision to "
                "withhold evidence from whichever readings lose, and nothing in this project's "
                "guard set catches that -- a dropped trial leaves no trace in any object. "
                "PAGE-STANDARD P21."),
            "siblings": ["ablation-af-medical-therapy", "early-rhythm-control-af"],
        },
        "shared_with_other_topics": {
            "_rule": "P22 -- sharing is legitimate; UNRECORDED sharing is not.",
            "computed_against": "the included sets of the two sibling reviews, which are "
                                "declared in DECIDED-ablation-af-review-2026-08-19.md",
            "shared": {
                "NCT00643188": {
                    "acronym": "CASTLE-AF",
                    "also_in": ["ablation-af-medical-therapy", "early-rhythm-control-af"],
                    "why": "It answers all three questions. It randomised catheter ablation "
                           "against conventional therapy (so it belongs to the "
                           "ablation-vs-medical-therapy review), it is a rhythm-control "
                           "strategy trial (so it belongs to the rhythm-control review), and "
                           "it required heart failure at entry (so it belongs here). BY "
                           "DESIGN, not by accident."},
                "NCT01420393": {
                    "acronym": "RAFT-AF",
                    "also_in": ["ablation-af-medical-therapy", "early-rhythm-control-af"],
                    "why": "Same three questions, same reason. Its conditionsModule names "
                           "Heart Failure first."},
            },
            "a_corpus_level_k_must_not_be_obtained_by_summing": (
                "BOTH of this review's two trials also appear in both sibling reviews. Adding "
                "the three reviews' k together gives 9 where the distinct evidence base is 4 "
                "trials. Any corpus-level count computed by summing per-topic k DOUBLE-COUNTS, "
                "and roughly a fifth of this corpus's registration identities were already "
                "shared across topics before this split made it deliberate."),
        },
        "sources": src.get("sources") or {},
        "outcomes": [{
            "id": "primary",
            "name": "Composite of all-cause mortality and heart-failure events",
            "definition": ("Time to first occurrence of death from any cause or a "
                           "heart-failure event, as each trial's own registered primary "
                           "composite."),
            "definition_note": ("THE TWO TRIALS DO NOT DEFINE THE HEART-FAILURE LIMB THE SAME "
                                "WAY, and that is recorded here rather than in a footnote -- "
                                "see results.by_outcome.primary.poolable_reason."),
            "measure": "HR",
            "effect_scale": "log",
            "type": "primary",
            "estimand": {"id": "primary", "family": "time-to-first-event",
                         "model": "random-effects"},
            "comparator": "medical rate- or rhythm-control therapy, or conventional care",
            "comparator_type": "active",
            "direction_of_benefit": "lower is better",
            "null_value": 1,
        }],
        "inputs": {"trials": trials},
        "screening": {
            "eligibility_provenance": {
                "state": "DERIVED_POST_HOC",
                "predefined": False,
                "post_hoc": True,
                "derived": True,
                "predefined_is_false_because": (
                    "These criteria were written on 2026-08-19, when the parent topic was "
                    "split into three reviews -- AFTER the included set existed. `false` is "
                    "asserted rather than left null because the derivation order is known: the "
                    "trials came first. That is the honest label and it is worse than null, "
                    "which is why it is on the block's face."),
                "authority_it_satisfies": "MECIR R29/R30/R31 -- the review STATES its "
                                          "eligibility criteria.",
                "authority_it_does_NOT_establish": "MECIR C5/C7 -- criteria DEFINED IN ADVANCE.",
                "what_would_settle_it": "a protocol record timestamped before the first "
                                        "executed query",
                "elements": [
                    {"element": "POPULATION",
                     "criterion": "adults with atrial fibrillation AND heart failure or "
                                  "left-ventricular dysfunction",
                     "auditable_against": "protocolSection.conditionsModule.conditions",
                     "settles_it": True,
                     "evidence": "Both included registrations list Atrial Fibrillation and "
                                 "Heart Failure among their conditions."},
                    {"element": "INTERVENTION",
                     "criterion": "catheter-based ablation of atrial fibrillation -- pulmonary "
                                  "vein isolation, radiofrequency or cryoballoon -- as the "
                                  "randomised intervention",
                     "auditable_against": "protocolSection.armsInterventionsModule.armGroups",
                     "settles_it": True,
                     "evidence_and_the_judgement_it_carries": (
                         "AV-NODE AND AV-JUNCTION ABLATION ARE NOT THIS INTERVENTION. They "
                         "ablate the conduction system, require a permanent pacemaker, and are "
                         "RATE CONTROL DELIVERED BY ABLATION -- they do not restore sinus "
                         "rhythm. Eight of the twenty exclusions turn on this one distinction "
                         "and every one of them says `ablation` in its arm labels, which is "
                         "why identity is taken from what the arm DOES rather than from the "
                         "word it contains. TWO OF THE EIGHT -- NCT01522898 and NCT06833138 -- "
                         "register EXACTLY this review's estimand, so the boundary is what "
                         "excludes them and not the outcome. A reader who draws the line "
                         "elsewhere can see precisely what including them would add. "
                         "Surgical maze ablation is excluded on the same limb, and drug trials "
                         "run after an ablation are excluded because the randomised contrast "
                         "is the drug.")},
                    {"element": "COMPARATOR",
                     "criterion": "medical therapy -- rate- or rhythm-control drugs, or "
                                  "conventional / usual / standard care",
                     "auditable_against": "protocolSection.armsInterventionsModule.armGroups",
                     "settles_it": True,
                     "evidence": "Eight exclusions are ablation-against-ablation technique "
                                 "comparisons or single-arm studies with no control declared. "
                                 "A NO_INTERVENTION arm counts as medical therapy where the "
                                 "registration describes it as conventional or usual care."},
                    {"element": "ESTIMAND (poolability, NOT eligibility)",
                     "criterion": "a time-to-first-event composite of all-cause mortality with "
                                  "heart-failure hospitalisation or heart-failure events, as a "
                                  "hazard ratio",
                     "auditable_against": "protocolSection.outcomesModule, EVERY rank",
                     "settles_it": True,
                     "evidence": "Eligibility deliberately does NOT turn on the reported "
                                 "outcome -- Handbook s3.2.4, because making eligibility "
                                 "depend on what a trial reported invites outcome-reporting "
                                 "bias. Poolability is a separate axis under s10.9, and "
                                 "ELIGIBLE_NOT_POOLABLE means the estimand appears at NO rank, "
                                 "primary or secondary."},
                ],
            },
        },
        "screening_of_remainder": {"ablation_hf_2026_08_19": screen},
        "results": {"by_outcome": {"primary": {
            "k": 2,
            "estimand_id": "primary",
            "model": "random-effects",
            "estimator": "DerSimonian-Laird",
            "estimator_used": "DerSimonian-Laird",
            "comparator_type": "active",
            "favours": "treatment",
            "poolable": False,
            "poolable_reason": (
                "THE TWO TRIALS DEFINE THE HEART-FAILURE LIMB OF THEIR COMPOSITE DIFFERENTLY, "
                "AND THE REGISTRY STATES BOTH. CASTLE-AF counts 'All-cause mortality or "
                "worsening heart failure requiring unplanned HOSPITALIZATION'. RAFT-AF counts "
                "all-cause mortality plus heart-failure events, where an event is an admission "
                "of more than 24 hours OR treatment in an emergency department OR a same-day "
                "access clinic OR an infusion centre OR an unscheduled visit for intravenous "
                "diuretic with an increase in chronic heart-failure therapy. RAFT-AF's limb "
                "counts OUTPATIENT events that CASTLE-AF does not count at all. Two composites "
                "of the same SHAPE are not the same QUANTITY, and pooling them would report an "
                "average over two definitions as though it were one effect."),
            "the_split_did_not_dissolve_this": (
                "Stated plainly because it would be easy to read the split as having fixed it. "
                "THE SPLIT FIXED THE QUESTION, NOT THE ESTIMAND. The parent object refused to "
                "pool four trials measuring four different composites; this review refuses to "
                "pool two measuring two. Correctly scoping a review does not make its trials "
                "measure the same thing."),
            "pooled": {"withdrawn": True, "point": None,
                       "withdrawn_because": "see poolable_reason"},
            "the_pool_this_refusal_declines_to_report": {
                "_why_shown": (
                    "SHOWN SO THE COST OF THE REFUSAL IS INSPECTABLE, and labelled so it "
                    "cannot be mistaken for this review's answer. A reader who judges the two "
                    "heart-failure definitions close enough to combine can see exactly what "
                    "they would get; a reader who agrees with the refusal can see that nothing "
                    "is being hidden by it."),
                "measure": "HR", "k": 2,
                "point": round(math.exp(mu), 4),
                "ci_low": round(math.exp(mu - Z * se), 4),
                "ci_high": round(math.exp(mu + Z * se), 4),
                "q": round(q, 4), "df": 1, "tau2": 0.0, "i2_pct": 0.0,
                "AND THIS IS THE POINT WORTH TAKING FROM THE PAGE": (
                    "I-SQUARED IS EXACTLY ZERO AND Q IS 0.27 ON 1 DEGREE OF FREEDOM. The two "
                    "trials are as statistically consistent as two trials can be -- and they "
                    "still measure different things. HETEROGENEITY STATISTICS CANNOT DETECT AN "
                    "ESTIMAND MISMATCH: they are computed from the numbers, and the numbers "
                    "are all that survives extraction. A low I-squared is evidence that two "
                    "estimates agree, and NO evidence that they answer the same question. Had "
                    "this review pooled on the strength of I-squared = 0, every downstream "
                    "check would have passed."),
            },
            "per_trial": [
                {"trial_id": t["trial_id"], "nct": t["nct"], "measure": t["measure"],
                 "point": t["point"], "ci_low": t["ci_low"], "ci_high": t["ci_high"],
                 "ci_level": t["ci_level"],
                 "endpoint_rank_in_its_own_trial": "PRIMARY",
                 "outcome_definition": (
                     "All-cause mortality or worsening heart failure requiring unplanned "
                     "hospitalization" if t["nct"] == "NCT00643188" else
                     "Composite of All-cause Mortality and Heart Failure Events, where an "
                     "event includes outpatient intravenous diuretic administration"),
                 "derivation": t["derivation"]}
                for t in per],
            "heterogeneity": {"q": round(q, 4), "df": 1, "tau2": 0.0, "i2": 0.0,
                              "i2_definition": "Higgins (Q - df)/Q, clamped at 0",
                              "note": "Computed for the pool this review DECLINES to report, "
                                      "and carried here for that reason only."},
            "heterogeneity_status": "not applicable -- nothing was pooled",
        }}},
        "config": src.get("config") or {},
    }

    os.makedirs(DEST_DIR, exist_ok=True)
    with io.open(DEST, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, indent=1, ensure_ascii=True))
    print("created %s" % DEST)
    print("   k                 %d" % 2)
    print("   remainder         %d screened to 0" % screen["remainder"])
    print("   pooling           REFUSED (%s)" % "different heart-failure event definitions")
    print("   pool declined     HR %.4f (%.4f, %.4f), I2 %.1f%%"
          % (math.exp(mu), math.exp(mu - Z * se), math.exp(mu + Z * se), 0.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
