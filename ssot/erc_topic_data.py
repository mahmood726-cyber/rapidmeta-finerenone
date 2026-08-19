"""Per-topic data for `early-rhythm-control-af`. Keyed to THIS topic and to no other.

Third of the three reviews `ablation-af-review` was split into (P21). Its criteria are NOT the
siblings' criteria, and a `sed`-rename of a sibling's screener is contamination route 7 --
guarded since 2026-08-19 by scripts/lint_criteria_fingerprint.py.
"""

# ==========================================================================================
# THE CRITERIA BLOCK. Its INTERVENTION element carries the single most consequential judgement
# on this page, because it disposes of 18 trials as a class and it is what admits CABANA.
# ==========================================================================================
ERC_CRITERIA = {
    "state": "DERIVED_POST_HOC",
    "predefined": False,
    "post_hoc": True,
    "derived": True,
    "predefined_is_false_because": (
        "written on 2026-08-19 when `ablation-af-review` was split into three reviews -- AFTER "
        "the included set existed. `false` is asserted rather than left null because the "
        "derivation order is known: the trials came first."),
    "authority_it_satisfies": "MECIR R29/R30/R31 -- the review STATES its eligibility criteria.",
    "authority_it_does_NOT_establish": "MECIR C5/C7 -- criteria DEFINED IN ADVANCE.",
    "what_would_settle_it": "a protocol record timestamped before the first executed query",
    "elements": [
        {
            "element": "POPULATION",
            "criterion": "adults with atrial fibrillation",
            "auditable_against": "protocolSection.conditionsModule.conditions",
            "settles_it": True,
            "evidence": "all four included registrations list Atrial Fibrillation; only 11 of "
                        "551 screened trials failed this limb, so the query is well aimed.",
        },
        {
            "element": "INTERVENTION",
            "criterion": ("a strategy that PRIORITISES restoring and maintaining sinus rhythm, "
                          "however delivered -- by antiarrhythmic drugs, by cardioversion, by "
                          "catheter ablation, or by any combination of them"),
            "auditable_against": "protocolSection.armsInterventionsModule.armGroups",
            "settles_it": True,
            "THE_JUDGEMENT_THIS_REVIEW_TURNS_ON": (
                "WHEN IS A HEAD-TO-HEAD COMPARISON IN SCOPE? Every arm of 97 surfaced trials "
                "receives some rhythm-control treatment, and 18 of the first 44 adjudicated "
                "are that shape. CABANA is one of them AND IS INCLUDED, so a rule that "
                "excluded head-to-heads as a class would exclude this review's own second "
                "largest trial. The rule below is therefore stated, not assumed.\n\n"
                "    IN SCOPE when the contrast is between a strategy that PRIORITISES sinus "
                "rhythm and one that DOES NOT MANDATE IT -- rate control, usual care, "
                "conventional management, or a comparator in which rhythm control is "
                "PERMITTED BUT NOT REQUIRED.\n\n"
                "    OUT OF SCOPE when BOTH arms mandate sinus rhythm and only the MODALITY or "
                "TECHNIQUE differs -- ablation against antiarrhythmic drugs as equally-intended "
                "first-line therapy, one ablation technique against another, one antiarrhythmic "
                "against another.\n\n"
                "WHY THAT ADMITS CABANA, read from its own arms rather than from its "
                "reputation. Its comparator arm is `Drug: Rate OR Rhythm Control Therapy` -- "
                "rate or rhythm at the treating physician's discretion, which is conventional "
                "management and NOT a mandate to restore sinus rhythm. The ablation arm "
                "mandates it. So the contrast is strategy-versus-usual-care and the trial is "
                "in scope.\n\n"
                "WHAT IT COSTS, STATED BEFORE THE 18 ARE DISPOSITIONED RATHER THAN AFTER. Any "
                "trial randomising ablation against antiarrhythmic drugs where BOTH arms aim "
                "at sinus rhythm is OUT -- and those are numerous, they are good trials, and "
                "several are larger than trials this review keeps. They belong to the sibling "
                "review `ablation-af-medical-therapy`, whose question is exactly that "
                "contrast. NOTHING IS DISCARDED BY THIS BOUNDARY; it is routed."),
            "how_the_18_are_dispositioned": (
                "Each is read for whether its comparator MANDATES sinus rhythm or merely "
                "PERMITS it. That is a reading of the arm's own declared text, not a "
                "judgement about the trial's quality, and a reader who draws the line "
                "elsewhere can recount the 18 from the evidence file."),
        },
        {
            "element": "COMPARATOR",
            "criterion": ("rate control, usual care, conventional management, or no "
                          "rhythm-control mandate"),
            "auditable_against": "protocolSection.armsInterventionsModule.armGroups",
            "settles_it": True,
            "evidence": (
                "EAST-AFNET 4's comparator arm is typed NO_INTERVENTION and labelled 'Usual "
                "care'; RAFT-AF's is 'Other: Rate Control'; CASTLE-AF's is 'Other: "
                "Conventional treatment'; CABANA's is 'Drug: Rate or Rhythm Control Therapy'. "
                "All four are the same kind of comparator -- what a patient gets when no one "
                "is committed to restoring sinus rhythm."),
            "and_AV_node_ablation_is_a_comparator_not_an_intervention": (
                "AV-node and AV-junction ablation with a pacemaker is RATE CONTROL DELIVERED "
                "BY ABLATION. It contains ablation words and is the opposite of this "
                "review's strategy, so it is checked BEFORE the rhythm family in every rule "
                "that reads an arm."),
        },
        {
            "element": "ESTIMAND (poolability, NOT eligibility)",
            "criterion": ("a time-to-first-event composite carrying all-cause or "
                          "cardiovascular mortality"),
            "auditable_against": "protocolSection.outcomesModule, EVERY registered rank",
            "settles_it": True,
            "evidence": (
                "eligibility deliberately does NOT turn on the reported outcome (Handbook "
                "s3.2.4 -- making eligibility depend on what a trial reported invites "
                "outcome-reporting bias); poolability is separate under s10.9. A COMPOSITE IS "
                "DETECTED STRUCTURALLY, as a mortality term together with another clinical "
                "event term in one endpoint -- not by the presence of the word 'composite'. "
                "CASTLE-AF's primary contains neither that word nor the phrase an earlier rule "
                "searched for, and that rule failed it toward NOT-POOLABLE. P33."),
        },
    ],
    "the_four_included_trials_against_these_criteria": {
        "NCT01288352": "EAST-AFNET 4 -- early systematic rhythm control vs usual care. The "
                       "cleanest instance of the contrast; its comparator is typed "
                       "NO_INTERVENTION.",
        "NCT00643188": "CASTLE-AF -- ablation vs conventional treatment.",
        "NCT00911508": "CABANA -- ablation vs rate-OR-rhythm control at physician discretion. "
                       "IN SCOPE on the head-to-head rule above, and the reason it is in scope "
                       "is the reason that rule had to be written.",
        "NCT01420393": "RAFT-AF -- ablation-based rhythm control vs rate control.",
    },
}
