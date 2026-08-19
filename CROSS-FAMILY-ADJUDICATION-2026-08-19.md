# Cross-family adjudication of the four most contestable screening calls

**Adjudicator: agy / Gemini 3.1 Pro (google family).** Independent of the lane that made the
calls (Claude, anthropic family). Neutral wording: the trials were presented as A–D with only
their registered fields, the criterion was quoted, and **no indication was given of what verdict
had already been recorded** or that any verdict existed.

The four were chosen because they are the calls that rest on judgement rather than on a field
read — the ones where being wrong would be invisible to every mechanical check in this repo.

## Result: 4 of 4 agree, and one of them vindicates a rule rather than a verdict

| | Trial | This lane recorded | agy, blind | Agree |
|---|---|---|---|---|
| A | NCT05776043 EMPATHY | EXCLUDED — population (acute, not chronic) | NOT ELIGIBLE, population, high confidence | yes |
| B | NCT03087773 EMMY | EXCLUDED — population (acute MI) | NOT ELIGIBLE, population, high confidence | yes |
| C | NCT05182658 EMPA-REPAIR | ELIGIBLE_NO_RESULTS_YET — **status**, population not argued | **CANNOT DECIDE** on population | yes |
| D | NCT06082063 Steno1 | EXCLUDED — intervention (4-agent bundle) | NOT ELIGIBLE, intervention, high confidence | yes |

**Trial C is the one worth keeping.** This lane declined to decide EMPA-REPAIR on population,
settling it on status instead, under the rule that *where more than one limb fails, the decision
is recorded on the strongest ground and the others are named rather than leaned on*. An
independent adjudicator, given the same registered fields and no knowledge of that rule,
returned **CANNOT DECIDE** on precisely that limb — and named exactly what was missing (whether
the heart failure is chronic, whether participants are adults, whether background therapy was
given).

> The stronger-ground rule was not just followed; it was **independently confirmed to have been
> necessary**. Had the trial been excluded on population, that exclusion would have been
> undecidable from the record, and nothing in this repository would ever have said so.

**Trial A is the most consequential call of the three topics** and it survives the strongest
available challenge. EMPATHY (n=1364) registers exactly `sglt2-hf`'s pooled estimand, so its
exclusion is the one that most changes the answer. A cross-family adjudicator, shown the
outcome and told outcome does not bear on eligibility, still returned NOT ELIGIBLE on population
at high confidence.

## What this does not establish

Agreement is not proof. All four judgements read the same registered fields, so a defect in
those fields — or a shared misreading of "chronic" as a registry term — would produce agreement
without correctness. What it rules out is a *lane-specific* error: a call made by one family's
reasoning that another family, asked neutrally, would not have made.

It also does not extend beyond these four. The remaining 36 screening decisions across the
three topics were not adjudicated, and this document does not imply they were.

## Method note, for reuse

The packet sent to the adjudicator was the **complete** evidence needed to answer, inline, so it
required no file access and no exploration — the recommendation recorded earlier tonight as
*store the packet that was actually sent, not a truncation of it*. The packet is the prompt in
`scripts/`-adjacent session logs; the reply is reproduced above without editing.

Wording was neutral in the specific sense that matters: the adjudicator was not told a verdict
existed, so it could not agree with one. Asking "do you agree that X is ineligible?" would have
tested compliance, not judgement.

*2026-08-19. Adjudicator model self-identified as Gemini 3.1 Pro in the same call.*
