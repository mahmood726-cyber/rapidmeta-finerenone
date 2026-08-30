# -*- coding: utf-8 -*-
"""Apply ICEMAN to this review's effect-modification claim, item by item.

⭐ WHY AN INSTRUMENT AT ALL. The claim that the ring's effect is modified by AGE currently
carries a whole GRADE domain, and it was assessed in prose. ICEMAN turns that into a scored
assessment against 8 published questions, each answerable and each checkable.

⚠️ ITS WARRANT IS CONSENSUS, NOT SIMULATION. Schandelmaier et al developed ICEMAN by expert
consensus and refined it against feedback from investigators, reviewers and editors, then
tested usability with 17 users. There is no simulation establishing operating
characteristics, because it is not that kind of object. That is a real limitation and it is
stated rather than dressed up.

⛔ AND IT IMMEDIATELY CAUGHT A FACT THIS REVIEW HAD BACKWARDS -- see `the_correction` below.
An instrument that only ever confirms the author is not an instrument; this one disagreed
with the author in BOTH directions on different items, which is the behaviour that makes it
worth running.

The 8 meta-analysis core questions were READ FROM TABLE 1 of the paper (PMC7829020), not
reconstructed from memory.
"""
import datetime
import io
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "ssot"))

import atomic_write as aw    # noqa: E402

TOPIC = "agyw-hiv-prep-review"
UTC = datetime.datetime.now(datetime.timezone.utc).isoformat()

INSTRUMENT = (
    "ICEMAN, Instrument for assessing the Credibility of Effect Modification Analyses. "
    "Schandelmaier S et al, CMAJ 2020;192:E901-6. PMID 32778601, PMC7829020. Tool at "
    "https://www.iceman.help. The 8 META-ANALYSIS core questions were read from Table 1 of "
    "the paper, not reconstructed."
)

CORRECTION = (
    "THE AGE INTERACTION IS NOT POST HOC, AND THIS REVIEW SAID IT WAS. ASPIRE states: 'To "
    "better characterize the relationship between age and HIV-1 protection seen in the "
    "PRE-SPECIFIED SUBGROUP ANALYSIS (age <25 vs. >=25 years), an exploratory analysis was "
    "conducted post hoc.' The figures this review cites -- 61% at 25 or above against 10% "
    "below, P = 0.02 for interaction -- come from the PRE-SPECIFIED analysis. What was post "
    "hoc is the 21-year cut (56% against -27%) and the age-thirds exploration. The Ring "
    "Study likewise states its 21-year subgroup 'was prespecified in the statistical "
    "analysis plan'. "
    "⚠️ THIS CORRECTION RAISES THE CREDIBILITY OF OUR OWN CLAIM, which is the "
    "direction that deserves suspicion -- so it is quoted rather than asserted, and anyone "
    "can check it in one search of a free full text."
)

ITEMS = [
    (1, "Is the analysis of effect modification based on comparison within rather than "
        "between trials?",
     "DEFINITELY YES",
     "Both contributing trials report age subgroups computed WITHIN the trial, each "
     "comparing randomised arms inside an age stratum. No part of the claim rests on "
     "comparing one trial against the other."),
    (2, "For within-trial comparisons, is the effect modification similar from trial to "
        "trial?",
     "POSSIBLY YES -- the weakest item, and it is not favourable",
     "DIRECTION agrees and STRENGTH does not. ASPIRE: P = 0.02 for interaction. The Ring "
     "Study: hazard ratio 0.63 above 21 against 0.85 at 21 or younger, P = 0.43 for "
     "interaction -- same direction, not significant. And the two trials cut age at "
     "DIFFERENT points, 25 and 21, so the subgroups are not the same subgroups."),
    (3, "For between-trial comparisons, is the number of trials large?",
     "NOT APPLICABLE",
     "The claim is within-trial (item 1). ICEMAN provides NA and it is used rather than "
     "scored, because scoring an inapplicable item would manufacture a number."),
    (4, "Was the direction of effect modification correctly hypothesized a priori?",
     "PROBABLY YES, WITH A DISTINCTION STATED",
     "The ANALYSIS was pre-specified in both trials, quoted above. But ICEMAN asks about "
     "the DIRECTION, and neither paper states that a direction was hypothesised in "
     "advance. Pre-specifying that age will be examined is not the same as predicting "
     "which way it will go, and the item is answered at PROBABLY rather than DEFINITELY "
     "for exactly that reason."),
    (5, "Does a test for interaction suggest that chance is an unlikely explanation of the "
        "apparent effect modification?",
     "POSSIBLY YES",
     "ASPIRE P = 0.02; the Ring Study P = 0.43. One of two contributing trials supports "
     "it. A single significant interaction test across two trials is weak evidence that "
     "chance is an unlikely explanation."),
    (6, "Did the authors test only a small number of effect modifiers, or consider the "
        "number in their statistical analysis?",
     "CANNOT BE ANSWERED FROM WHAT THIS REVIEW HOLDS",
     "ASPIRE states 'Prespecified subgroup analyses were planned' and reports a forest plot "
     "of several, without stating how many were tested or any multiplicity adjustment. "
     "⛔ REFUSED RATHER THAN GUESSED: the number of modifiers tested is the single "
     "strongest determinant of a false subgroup claim, and inventing a favourable answer "
     "for it would corrupt the whole instrument."),
    (7, "Did the authors use a random-effects model?",
     "NO",
     "This review has not pooled the interaction across the two trials at all -- it cites "
     "ASPIRE's within-trial interaction and notes the Ring Study runs the same direction. "
     "No random-effects model of the effect modification exists here."),
    (8, "If the effect modifier is a continuous variable, were arbitrary cut points "
        "avoided?",
     "NO",
     "⛔ THE CLEAREST UNFAVOURABLE ANSWER. Age is continuous and was dichotomised -- at "
     "25 in ASPIRE, at 21 in the Ring Study, and additionally into thirds in ASPIRE's "
     "post-hoc exploration. Three different cut points across two trials, none derived "
     "from anything but convenience."),
]

SUMMARY = "LOW to MODERATE credibility"

SUMMARY_WHY = (
    "Favourable on the structural items -- the comparison is within-trial (1) and the "
    "analysis was pre-specified (4). Unfavourable on the statistical ones -- arbitrary cut "
    "points on a continuous modifier (8), no random-effects model (7), and only one of two "
    "trials showing a significant interaction (5). Unresolvable on the item that matters "
    "most (6). ⇒ NOT the 'highly credible' reading our prose implied, and NOT the "
    "'post hoc, therefore weak' reading the commissioning brief assumed either. THE "
    "INSTRUMENT DISAGREED WITH THE AUTHOR IN BOTH DIRECTIONS, on different items."
)

CONSEQUENCE = (
    "The indirectness downgrade is justified partly on this interaction being MEASURED "
    "rather than anticipated. At LOW-to-MODERATE credibility that support is weaker than "
    "the prose claimed. ⭐ THE DOWNGRADE ITSELF DOES NOT FALL: the plain restriction "
    "argument stands on its own -- the question asks about women, the trials enrolled women "
    "aged 18 to 45 in four sub-Saharan African countries -- and Handbook 14.2.2 reaches "
    "indirectness with no modifier at all. What weakens is the STRENGTH of the supporting "
    "argument, and that is recorded rather than left implied."
)

ALONGSIDE = (
    "The prose judgement is unchanged and still published beside this. That is the "
    "improvement-not-regression rule: the instrument is ADDED, the incumbent is NOT "
    "removed, and where they differ the difference is the finding. Here they differ in "
    "STRENGTH, not direction -- prose said the interaction is evidence against transfer; "
    "ICEMAN says that evidence is of low-to-moderate credibility."
)


def main(apply_changes=False):
    path = os.path.join(_HERE, "..", "ssot", TOPIC, "%s.json" % TOPIC)
    obj = json.load(open(path, encoding="utf-8"))
    mods = obj["results"]["by_outcome"]["primary"].get("effect_modifiers")
    if not mods:
        print("REFUSED: no effect_modifiers recorded on this result -- nothing to assess.")
        return 1
    mods[0]["ICEMAN_2026_08_30"] = {
        "instrument": INSTRUMENT,
        "version_used": "meta-analysis form, 8 core questions",
        "what_is_being_assessed": ("The claim that the effect of the dapivirine ring on "
                                   "HIV-1 seroconversion is modified by AGE."),
        "its_warrant_is_consensus_not_simulation": (
            "ICEMAN was developed by expert consensus and usability-tested with 17 users. "
            "No simulation establishes its operating characteristics, because it is not "
            "that kind of instrument. Stated rather than dressed up."),
        "the_correction": CORRECTION,
        "items": [{"n": n, "question": q, "answer": a, "why": w}
                  for n, q, a, w in ITEMS],
        "summary_rating": SUMMARY,
        "summary_reasoning": SUMMARY_WHY,
        "what_this_does_to_the_indirectness_domain": CONSEQUENCE,
        "run_alongside_the_prose_judgement": ALONGSIDE,
        "assessed_utc": UTC,
    }
    print("ICEMAN, %d items answered, summary: %s" % (len(ITEMS), SUMMARY))
    for n, q, a, _w in ITEMS:
        print("  %d  %-46s %s" % (n, q[:46], a))
    if not apply_changes:
        print("dry run -- pass --apply to write")
        return 0
    print("WRITTEN %d bytes" % aw.write_json(path, obj))
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main(apply_changes="--apply" in sys.argv))
