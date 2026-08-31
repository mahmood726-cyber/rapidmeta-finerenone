# -*- coding: utf-8 -*-
"""THE JUDGEMENT REGISTER: every call on this topic that a harness cannot derive.

THE QUESTION THIS ANSWERS. Not "is the harness automated" -- that is a weak
claim and a reader cannot check it. The claim is: A TOPIC COSTS A SMALL,
DECLARED, COUNTABLE NUMBER OF HUMAN JUDGEMENTS, and each is written down with
its alternative and the consequence of that alternative. A reader can check a
declared judgement. A reader cannot check an inferred one. Cochrane makes these
same calls and buries them in prose.

⛔ THE RULE THAT MAKES THIS HONEST: NO ENTRY MAY BE RESOLVED BY INFERRING FROM
THE INCLUDED TRIALS. Deriving the question's population from the populations
that were enrolled returns DIRECT by construction -- a tautology wearing a
rating. Every entry below therefore records what DECIDED it, and where the
decider is "the trials", the entry is marked as a defect rather than as a
judgement.

WHAT AN ENTRY MUST CARRY, all four, or it is disclosure rather than audit:
    decided        -- what was actually chosen
    decided_by     -- who or what chose it, and whether a harness could have
    alternative    -- the defensible other option, named
    if_alternative -- WHAT WOULD CHANGE. Computed where computable, and where
                      it was computed the computation is shown.

⭐ THE COUNTERFACTUALS ARE EXECUTED, NOT ASSERTED. Three of them were run:
the GRADE engine was re-derived under an alternative decision threshold, and
the pooled estimate was recomputed on the alternative count tier from the
trials' own publications. Two of the three returned "no change", which is a
result and not a failure -- an untested counterfactual that merely SOUNDS
consequential is the thing this register exists to replace.
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


def _ci(pt, se):
    return (round(math.exp(math.log(pt) - 1.959964 * se), 4),
            round(math.exp(math.log(pt) + 1.959964 * se), 4))


def _fe(rows):
    """Fixed-effect inverse-variance pool. Used only to put the two count tiers
    on the same footing; the review's own pool is random-effects REML and at
    tau-squared = 0 the two coincide, which is why the tier-A number below
    reproduces the stored point exactly."""
    w = [1.0 / (s * s) for _, s in rows]
    mu = sum(wi * y for (y, _), wi in zip(rows, w)) / sum(w)
    se = math.sqrt(1.0 / sum(w))
    lo, hi = _ci(math.exp(mu), se)
    return round(math.exp(mu), 4), lo, hi


def _rr_participants(e1, n1, e2, n2):
    rr = (e1 / n1) / (e2 / n2)
    return math.log(rr), math.sqrt(1/e1 - 1/n1 + 1/e2 - 1/n2)


def _rr_rates(e1, py1, e2, py2):
    rr = (e1 / py1) / (e2 / py2)
    return math.log(rr), math.sqrt(1.0/e1 + 1.0/e2)


def main():
    obj = json.load(open(OBJ, encoding="utf-8"))

    # ---- executed counterfactual: the count tier -------------------------
    tier_a = _fe([_rr_participants(82, 1302, 61, 650),
                  _rr_participants(71, 1313, 97, 1313)])
    tier_b = _fe([_rr_rates(77, 1888.0, 56, 917.0),
                  _rr_rates(71, 71/0.033, 97, 97/0.045)])

    J = []

    # =====================================================================
    J.append({
        "id": "J1",
        "judgement": "The review question, declared axis by axis (question_pico).",
        "decided": ("population = \"women\"; intervention = \"dapivirine vaginal "
                    "ring\"; comparator = \"placebo vaginal ring\"; outcome = "
                    "\"HIV-1 seroconversion\". Unqualified by age, region or "
                    "baseline risk."),
        "decided_by": ("A HUMAN, from the review's title and stated question. "
                       "`question_pico.source` records exactly that."),
        "could_a_harness_derive_it": (
            "⛔ NO, AND IT MUST NOT TRY. Deriving the question's population "
            "from the enrolled populations returns DIRECT by construction: "
            "the answer would always be that the evidence matches the "
            "question, because the question was read off the evidence. "
            "`grade_engine.d_indirectness` names this as a gaming risk in its "
            "own source and refuses that branch."),
        "alternative": (
            "Declare the question as the studied band -- \"women aged 18-45 at "
            "substantial risk in sub-Saharan Africa\" -- which is what the "
            "trials actually answer."),
        "if_alternative": (
            "The indirectness downgrade would fall away and the certainty "
            "would rise VERY LOW to LOW. ⚠️ AND THE OBJECT ALREADY FORBIDS "
            "TAKING IT FOR THAT REASON: `grade.indirectness."
            "what_would_have_to_differ_BOTH_ARMS.⛔_the_guard_on_arm_(a)` "
            "states that narrowing the question to escape a downgrade is the "
            "same defect as deleting the downgrade, and that rescoping is "
            "legitimate only as an editorial decision about what the review "
            "CLAIMS, taken independently of the letter it produces, and only "
            "if it changes the title and the question a reader meets."),
        "cost_to_regenerate_on_a_new_topic": "ONE declaration. Cannot be automated.",
    })

    # =====================================================================
    J.append({
        "id": "J2",
        "judgement": ("The eligibility rule -- specifically the part that goes "
                      "beyond the concept block."),
        "decided": (
            "Included: randomised, phase 3, dapivirine VAGINAL RING (not gel, "
            "not film), against a PLACEBO ring, with HIV-1 seroconversion as "
            "the primary. That took 63 registry candidates to 2."),
        "decided_by": (
            "⚠️ PART CODE, PART HUMAN, AND THE OBJECT SAYS SO: \"The screen "
            "tests phase and randomisation; it does NOT test the comparator or "
            "the outcome.\" Comparator and outcome were applied as THREE "
            "CASE-BY-CASE VERDICTS in `adjudication_of_non_included_that_"
            "passed_screen` -- NCT03965923, NCT04140266, NCT06250504, each "
            "marked ELIGIBILITY. So the rule is ENACTED AS VERDICTS RATHER "
            "THAN DECLARED AS A RULE, and a harness cannot regenerate it from "
            "what is written."),
        "could_a_harness_derive_it": (
            "⛔ NO. And the proof is already in this corpus: a drug-only "
            "concept block returned an IDENTICAL 125 candidates across six "
            "different colchicine topics. A CANDIDATE COUNT IS NOT AN "
            "ELIGIBILITY DECISION. The block finds the drug; the rule that "
            "turns candidates into an included set is the judgement, and it is "
            "the part no query expresses."),
        "alternative": (
            "Admit active-comparator trials -- ring against oral "
            "tenofovir/emtricitabine -- which is the comparison a funder and a "
            "guideline panel actually face."),
        "if_alternative": (
            "k would rise from 2, and the three named registrations would "
            "enter: NCT03965923, NCT04140266, NCT03593655. ⚠️ BUT NOT AS "
            "EFFICACY EVIDENCE -- every one of them has a primary of safety, "
            "adherence or uptake, NOT HIV incidence. So the pooled efficacy "
            "estimate would not change at all; what would change is that the "
            "review would carry an adherence and safety comparison against "
            "oral prophylaxis that it currently does not. The head-to-head "
            "EFFICACY trial does not exist to be included."),
        "cost_to_regenerate_on_a_new_topic": (
            "ONE declaration, and it is currently UNDECLARED on this topic -- "
            "recorded here as owed rather than as done."),
    })

    # =====================================================================
    J.append({
        "id": "J3",
        "judgement": "The count tier -- which document supplies the numerator.",
        "decided": (
            "ClinicalTrials.gov POSTED RESULTS: 82/1302 and 61/650 for "
            "NCT01539226; 71/1313 and 97/1313 for NCT01617096. Events over "
            "PARTICIPANTS, giving a risk ratio."),
        "decided_by": (
            "⚠️ A HUMAN, AND THE PAGE NAMED NEITHER BASIS AS A CHOICE UNTIL "
            "THIS REGISTER. The object records the provenance of the numbers "
            "it used and never recorded that a second defensible basis existed."),
        "could_a_harness_derive_it": (
            "⛔ NO. Both tiers are defensible and both are free to read. A "
            "harness can fetch either; nothing in the data says which is the "
            "review's numerator."),
        "alternative": (
            "The trials' own primary publications: Nel 2016 (PMID 27959766) "
            "reports 77 seroconversions in 1888 person-years against 56 in "
            "917; Baeten 2016 (PMID 26900902, PMC4993693) reports 71 against "
            "97, incidence 3.3 and 4.5 per 100 person-years. Events over "
            "PERSON-YEARS, giving a rate ratio."),
        "if_alternative_COMPUTED": {
            "⚠️_the_counts_themselves_DIFFER_on_one_trial": (
                "NCT01539226: registry 82 and 61, publication 77 and 56 -- "
                "FIVE MORE EVENTS IN EACH ARM in the registry. NCT01617096: "
                "registry 71 and 97, publication 71 and 97 -- IDENTICAL. The "
                "tiers are not two views of one number; on one of these two "
                "trials they are two different numbers."),
            "tier_A_registry_risk_ratio": "%.4f (%.4f to %.4f)" % tier_a,
            "tier_B_publication_rate_ratio": "%.4f (%.4f to %.4f)" % tier_b,
            "so": (
                "⭐ THE POINT ESTIMATE MOVES BY 0.0007 AND THE CONCLUSION DOES "
                "NOT CHANGE. The interval is slightly wider on the publication "
                "tier. THIS IS A FACT ABOUT THIS TOPIC AND NOT A GENERAL "
                "PROPERTY -- the counts genuinely differ on one trial, and "
                "they happen to differ in the same direction in both arms, "
                "which is why the ratio survives. On a topic where they "
                "differed in one arm only, the tier would decide the answer."),
            "and_it_is_entangled_with_J5": (
                "The tier chooses the ESTIMAND as a side effect. The registry "
                "reports events over participants, so it forces a risk ratio; "
                "the publications report events over person-years, so they "
                "force a rate ratio. Choosing the document chose the measure, "
                "and that was never a separate decision anyone took."),
            "harms_differ_too": (
                "Serious adverse events on NCT01539226: registry 41 of 1306 "
                "and 9 of 652; the publication reports 38 (2.9%) and 6 (0.9%). "
                "The harms tier disagrees on the same trial and in the same "
                "direction."),
        },
        "cost_to_regenerate_on_a_new_topic": "ONE declaration.",
    })

    # =====================================================================
    J.append({
        "id": "J4",
        "judgement": "The indirectness rating.",
        "decided": "DOWNGRADE one level, for indirectness of POPULATION.",
        "decided_by": (
            "⚠️ A HUMAN, STORED AS TEXT, AND THE ENGINE READS IT RATHER THAN "
            "DERIVING IT. `grade.indirectness.judged_by` says so in terms: "
            "\"Explicit stored judgement. grade_engine refuses this domain by "
            "design and will not infer it.\" Verified by execution: changing "
            "`question_pico.population` and the review's `question` string and "
            "re-deriving returned the SAME rating with a BYTE-IDENTICAL reason "
            "string, because `d_indirectness` returns the stored block before "
            "it ever reaches the derivation branch."),
        "could_a_harness_derive_it": (
            "⛔ NO, and the module is explicit that it must not. There IS a "
            "derivation branch -- `indirectness_procedure.rate` compares five "
            "axes -- but it fires only where both PICOs are declared "
            "independently, and on this topic the stored judgement takes "
            "precedence. WHAT THE PROCEDURE CANNOT DECIDE is whether \"women "
            "aged 18-45 in four sub-Saharan African countries\" is a direct "
            "answer to \"women\". That is a clinical judgement about transfer, "
            "not a string comparison."),
        "alternative": (
            "NO_DOWNGRADE, on the reasoning that the trials ran in the "
            "settings carrying the burden the intervention is for."),
        "if_alternative": (
            "Certainty would be LOW rather than VERY LOW. ⭐ AND THIS "
            "ALTERNATIVE WAS ACTUALLY TAKEN, FOR EIGHT MINUTES, AND REVERSED: "
            "the object stores the earlier NO_DOWNGRADE at 15:05:54 and the "
            "reversal at 15:13:50, with the reason -- burden-relevance is an "
            "argument that these were the RIGHT TRIALS TO RUN, which is a "
            "prioritisation claim and not a directness claim. Handbook 14.2.2 "
            "domain (3) never mentions burden. THE REVERSAL LOWERED OUR OWN "
            "CERTAINTY."),
        "what_it_rests_on": (
            "A within-trial effect modifier, not an assertion from outside: "
            "ASPIRE reports efficacy 61% at 25 or older against 10% below, "
            "P = 0.02 for interaction. A cross-family reviewer qualified the "
            "strong form -- the Ring Study's own interaction is same-direction "
            "but NOT significant (P = 0.43) -- and the qualification is stored "
            "beside the rating."),
        "cost_to_regenerate_on_a_new_topic": "ONE judgement, per outcome.",
    })

    # =====================================================================
    J.append({
        "id": "J5",
        "judgement": ("The estimand -- what the pooled number is a ratio OF, and "
                      "whether the two trials measure the same thing."),
        "decided": (
            "A RISK RATIO of cumulative incidence over participants, pooled "
            "across trials whose registered primary time frames differ: 24 "
            "months for NCT01539226 against 12 to 14 months per participant "
            "for NCT01617096."),
        "decided_by": (
            "A HUMAN, and largely as a CONSEQUENCE OF J3 rather than as its "
            "own decision -- the registry reports participants, so the "
            "registry tier forces a risk ratio."),
        "could_a_harness_derive_it": (
            "⛔ NO. Both time frames are stored verbatim and a harness can see "
            "they differ. Whether that difference makes the two cumulative "
            "incidences incommensurable is a judgement about the hazard being "
            "roughly constant, which no field records."),
        "alternative": (
            "Pool RATE ratios over person-years, which is what both "
            "publications report and which is estimand-consistent across "
            "unequal follow-up."),
        "if_alternative_COMPUTED": (
            "%.4f (%.4f to %.4f) against the stored %.4f (%.4f to %.4f). The "
            "point moves by 0.0007. The estimand mismatch is REAL IN "
            "PRINCIPLE AND IMMATERIAL IN FACT ON THIS TOPIC, and saying so "
            "with the number beside it is worth more than either ignoring it "
            "or flagging it as a limitation nobody quantified."
            % (tier_b + tier_a)),
        "cost_to_regenerate_on_a_new_topic": "ONE declaration, per outcome.",
    })

    # =====================================================================
    J.append({
        "id": "J6",
        "judgement": ("The imprecision threshold -- what counts as an "
                      "appreciable effect."),
        "decided": (
            "RR 0.90, declared for this topic BEFORE the letter was "
            "recomputed, and justified from ABSOLUTE effect rather than from "
            "the ratio: at a placebo incidence of about 4.5 per 100 "
            "woman-years, RR 0.90 prevents about 0.45 infections per 100 "
            "woman-years."),
        "decided_by": "A HUMAN, and the declaration timestamp is stored.",
        "could_a_harness_derive_it": (
            "⛔ NO. The engine's fallback is the Handbook's rough guide of "
            "0.75 to 1.25, which the object correctly calls a DECLARED DEFAULT "
            "and not a clinical judgement -- \"a default standing in for a "
            "judgement is the most important line on the page being drawn by "
            "nobody\"."),
        "alternative": "The Handbook default 0.75 to 1.25.",
        "if_alternative_COMPUTED": (
            "⭐ NOTHING CHANGES. Re-deriving the engine with the threshold set "
            "to 0.75-1.25 returns VERY_LOW, down 3, with imprecision still "
            "downgraded -- identical to the stored rating. The object's own "
            "sensitivity block agrees: under the Handbook default the letter "
            "is VERY_LOW, `changes_the_letter: false`. THIS JUDGEMENT IS NOT "
            "LOAD-BEARING ON THIS TOPIC and it was worth executing to find "
            "that out."),
        "⚠️_the_judgement_that_IS_load_bearing_is_a_different_one": (
            "The stored sensitivity block shows the letter turns on the "
            "imprecision RULE, not on the threshold value: under a "
            "`line_of_no_effect` rule imprecision would NOT downgrade and the "
            "certainty would be LOW, `changes_the_letter: true`. So the "
            "consequential choice is whether imprecision is judged on the "
            "interval excluding no effect or on the interval spanning an "
            "appreciable-benefit zone -- and the object foregrounds the "
            "threshold VALUE while the RULE is what moves the letter."),
        "cost_to_regenerate_on_a_new_topic": "ONE declaration, per outcome.",
    })

    # =====================================================================
    J.append({
        "id": "J7",
        "judgement": "Whether to pool the harms.",
        "decided": (
            "NOT POOLED. Both 2x2s published, both relative risks published, "
            "the pool declined."),
        "decided_by": (
            "A HUMAN, on evidence a harness CAN compute: the placebo-arm "
            "serious-adverse-event rates differ 7.2-fold (1.38% against "
            "9.88%), the relative risks point in opposite directions, Q = "
            "5.8868 on 1 df, p = 0.0153."),
        "could_a_harness_derive_it": (
            "⚠️ PARTLY, AND THIS IS THE ONLY ENTRY IN THIS REGISTER WHERE THAT "
            "IS TRUE. The statistics are derivable. What is not derivable is "
            "the inference that a seven-fold difference in the CONTROL arm of "
            "two trials enrolling the same women in the same countries "
            "indicates ASCERTAINMENT rather than RISK. A harness that pooled "
            "on heterogeneity alone would have reported a random-effects "
            "estimate with a wide interval and no explanation."),
        "alternative": (
            "Pool with a random-effects model and report the heterogeneity, "
            "which is what most reviews do."),
        "if_alternative": (
            "A fixed-effect pool gives 0.9818 -- a serious-adverse-event "
            "relative risk of almost exactly one, which reads as reassurance "
            "and is manufactured entirely by averaging 2.27 against 0.89 "
            "across incommensurable ascertainment. That number would be the "
            "single most misleading figure on the page."),
        "cost_to_regenerate_on_a_new_topic": "ONE judgement, per harms outcome.",
    })

    # =====================================================================
    n_topic = len(J)
    standing = [
        ("free sources only; a subscription database is never a dependency",
         "scope rule, all topics"),
        ("key every value from the NCT, never from a label",
         "identity rule, all topics"),
        ("key every arm from the group TITLE, never from the group index",
         "added 2026-08-30 after the NCT01539226 inversion"),
        ("publish every screening decision, not only the near misses",
         "added 2026-08-30"),
        ("derive and do NOT apply, where a change would improve our own rating",
         "governance rule, all topics"),
        ("report numerator and denominator on every count, and say what the "
         "denominator is OF", "all topics"),
    ]

    obj["judgement_register_2026_08_30"] = {
        "_what": (
            "Every judgement this topic required that a harness cannot derive, "
            "declared, with what was decided, who decided it, the alternative, "
            "and what would change if the alternative had been taken."),
        "_why_this_is_the_claim_worth_making": (
            "\"It is automated\" is a claim a reader cannot check. \"It cost "
            "seven declared judgements, each with its alternative and the "
            "consequence of that alternative\" is a claim a reader CAN check, "
            "one entry at a time, against free sources. Cochrane makes every "
            "one of these calls and reports them as prose, where the "
            "alternative is not stated and the consequence is not computed."),
        "⛔_the_rule_that_keeps_this_honest": (
            "NO ENTRY IS RESOLVED BY INFERRING FROM THE INCLUDED TRIALS. "
            "Deriving the question from the enrolled populations returns "
            "DIRECT by construction -- a tautology dressed as a rating -- and "
            "`grade_engine.d_indirectness` names that as a gaming risk in its "
            "own source."),
        "recorded_utc": NOW,
        "per_topic_judgements": J,
        "count": {
            "per_topic_judgements": n_topic,
            "of_which_load_bearing_on_the_certainty_letter":
                "2 of %d -- J4 (indirectness) and the imprecision RULE noted "
                "under J6. J6's declared threshold VALUE is not." % n_topic,
            "of_which_computed_counterfactuals": "3 of %d -- J3, J5, J6" % n_topic,
            "of_which_returned_NO_CHANGE": (
                "2 of 3 computed. J3 moves the point estimate by 0.0007 and "
                "J6 does not move the letter at all. Recorded because a "
                "counterfactual that sounds consequential and is not is "
                "exactly what this register exists to catch."),
            "of_which_currently_UNDECLARED_in_the_object": (
                "1 of %d -- J2, the eligibility rule beyond phase and "
                "randomisation, which is enacted as three case verdicts rather "
                "than stated as a rule. Owed." % n_topic),
        },
        "standing_rules_NOT_counted_per_topic": {
            "_what": (
                "Declared once and applied to every topic. They are judgements "
                "too, but they are paid ONCE for the corpus rather than once "
                "per review, so counting them per topic would overstate the "
                "cost of a topic."),
            "rules": [{"rule": r, "scope": s} for r, s in standing],
            "count": len(standing),
        },
        "⭐_the_scaling_claim_stated_precisely": (
            "A topic costs %d declared judgements, of which 2 move the "
            "certainty letter, plus %d standing rules paid once for the whole "
            "corpus. Everything else on this page -- the search, the 1,443-"
            "record screen, the extraction, the arm mapping, the pool, the "
            "absolute effects, the four renderings and every consistency check "
            "-- is code and regenerates. THE CLAIM IS NOT THAT JUDGEMENT WAS "
            "ELIMINATED. It is that judgement was CORNERED into %d places a "
            "reader can find and argue with." % (n_topic, len(standing), n_topic)),
        "BESPOKE_FRACTION_of_the_2026_08_30_work": {
            "_the_test_applied": (
                "NOT \"is the logic reusable\" -- that flatters everything. "
                "The test is: POINT IT AT TOPIC TWO AND RUN IT UNMODIFIED. "
                "Does it work? A file that needs its constants edited counts "
                "as bespoke, because editing it is the work."),
            "artefacts_written": 7,
            "lines_written": 2924,
            "regenerates_unmodified_on_another_topic": {
                "ssot/projectors_reader_layers.py": (
                    "408 lines. YES. Reads keys generically, guarded on "
                    "presence, no-op where absent -- proved by building "
                    "ablation-af-review clean."),
                "ssot/paper_projector.py strip fix": (
                    "~55 lines. YES, and it is corpus-wide: it repaired 890 "
                    "damaged strings across 146 of 161 objects."),
                "generic functions inside the renderings script": (
                    "~120 lines -- absolute_table, readability, "
                    "consistency_check, _walk_strings. YES in logic, but they "
                    "live inside a topic-named file and would have to be "
                    "lifted out first, so they are counted as NO below."),
            },
            "does_NOT_regenerate": {
                "scripts/bibliographic_screen_dapivirine.py": (
                    "487 lines. NO. Hardcoded concept block, hardcoded output "
                    "directory, hardcoded object path, and a ring-versus-gel "
                    "rule that is specific to this drug."),
                "the four apply_* scripts": (
                    "1,929 lines. NO. Every one hardcodes the object path, "
                    "the two NCTs, the counts, and several thousand words of "
                    "prose about dapivirine specifically."),
            },
            "BY_LINE": (
                "~463 of 2,924 lines regenerate unmodified = 16%. "
                "⇒ 84% BESPOKE BY LINE."),
            "BY_CAPABILITY": (
                "Ten capabilities were delivered. FIVE are general as written "
                "-- the arm-mapping check, registry extraction by NCT, the "
                "absolute-effect table, the consistency check, the rendering "
                "cards. THREE need parameterising and would then be general "
                "-- the bibliographic screen, the harms extraction, the "
                "readability measure. TWO are irreducibly per-topic -- the "
                "rendering PROSE and the register ENTRIES themselves. "
                "⇒ 50% BESPOKE BY CAPABILITY."),
            "⚠️_WHICH_NUMBER_TO_QUOTE_AND_WHY_THE_PESSIMISTIC_ONE": (
                "QUOTE 84%. The by-capability figure counts intentions; the "
                "by-line figure counts what would actually have to be typed "
                "again tomorrow. The last honest count for this project was "
                "69% bespoke, and this session is WORSE than that, not "
                "better -- because most of what was written today is prose, "
                "and prose about dapivirine does not regenerate for "
                "topic two."),
            "the_honest_trend": (
                "⛔ THE BESPOKE FRACTION DID NOT IMPROVE TODAY. What improved "
                "is that the per-topic JUDGEMENT count is now known and small "
                "(seven), which is a different and better claim than a falling "
                "bespoke fraction. A high bespoke fraction with 7 declared "
                "judgements is a scaling problem in the ENGINEERING. A low "
                "bespoke fraction with 400 undeclared judgements would be a "
                "scaling problem in the SCIENCE. Only the second is fatal, "
                "and it is the one this register addresses."),
            "what_would_actually_move_it": (
                "Lift the four generic functions out of the topic-named "
                "renderings script; parameterise the concept block, the "
                "output path and the formulation rule in the screen; and "
                "replace the hand-written rendering prose with templates "
                "keyed on the fact table. Estimated to take the by-line "
                "figure from 84% to roughly 55%. NOT DONE, NOT SCHEDULED, "
                "and stated so nobody reads 16% general as a plan."),
        },
        "what_this_register_does_NOT_do": (
            "⚠️ It does not make the judgements right. Every entry is one "
            "person's call, and J4 was reversed once within eight minutes on "
            "this very topic. It also does not prove the list is COMPLETE -- "
            "it is bounded by what its author noticed, which is the same "
            "limitation as any enumeration, and the honest form of the claim "
            "is \"seven found\" rather than \"seven exist\"."),
    }

    # ⛔ THROUGH THE STAMPED WRITER, NOT A HAND-ROLLED TEMP-AND-REPLACE.
    # This was `open(tmp,"w") + json.dump + os.replace` -- atomic, and still
    # wrong: ssot/atomic_write.write_json STAMPS every judgement in a topic
    # object with a reference to the subject it was made about, and a
    # hand-rolled write skips the stamp silently. The judgement then references
    # nothing and staleness becomes undetectable. gate4 refused a push over it
    # and was right; the atomicity I had was the easy half.
    _here = os.path.dirname(os.path.abspath(__file__))
    if _here not in sys.path:
        sys.path.insert(0, _here)
    import atomic_write as _aw
    _aw.write_json(OBJ, obj, indent=1)

    print("WROTE judgement_register_2026_08_30")
    print("  per-topic judgements   %d" % n_topic)
    print("  standing rules         %d (paid once for the corpus)" % len(standing))
    print("  counterfactuals RUN    3 (J3 count tier, J5 estimand, J6 threshold)")
    print("  tier A registry  RR    %.4f (%.4f to %.4f)" % tier_a)
    print("  tier B publication RR  %.4f (%.4f to %.4f)" % tier_b)
    print("  undeclared today       1 (J2 eligibility rule) -- recorded as owed")


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    main()
