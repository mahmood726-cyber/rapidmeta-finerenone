# Prediction, logged BEFORE the indirectness procedure was written or run

**Logged 2026-08-30, before `indirectness_procedure.py` existed.** Recorded because a
prediction made after seeing the output is not a prediction, and because this project has
already logged one miss today (Embase records: predicted 300–700, observed 1,044) and one
falsified expectation (the RR 0.90 threshold, which I said would raise the letter and did
not). Both are worth more than the hits.

## The denominator

**53 pooled results currently refuse GRADE on indirectness**, out of 157 the engine can
evaluate. That is the number the procedure will be applied to.

## What I predict

| quantity | prediction |
|---|---|
| results the procedure RATES | **10–15 of 53 (20–28%)** |
| results it REFUSES for a stated reason | **38–43 of 53 (72–80%)** |
| of those rated, DOWNGRADE ≥1 level | **60–80%** |
| of those rated, DOWNGRADE 2 levels | **0–2 results** |

## Why — the reasoning, so the miss is diagnosable

**The refusal rate is the prediction I hold most confidently, and it is a prediction about
OUR OBJECTS, not about the evidence.** The procedure compares the QUESTION'S PICO against
the TRIALS' PICO. Almost every object in this corpus states its question as a single prose
sentence — *"In adults with covid, does Sarilumab compared with usual care affect the
outcome each trial registered as its primary…"* — and prose is not a structure that can be
compared axis by axis. Where the population, comparator and setting the review INTENDS are
not declared separately, there is nothing to compare the trials against, and the honest
output is a refusal naming the missing field.

⇒ **So I expect the dominant finding to be an OBJECT DEFECT, not a rating distribution: this
corpus does not state its own questions in a form that permits an indirectness judgement.**
That is the same class as "a review whose name and whose question describe different
populations" — unstated scope — and it is why the slug nearly governed a rating today.

**Among those that DO rate, I expect downgrades to dominate**, because restriction is the
normal condition of trial evidence: registrational trials recruit narrow age bands, single
regions, and run against placebo where practice uses an active comparator. Dapivirine
downgraded on population; I expect setting and comparator to be the next most common axes.

**Two levels should be rare.** Two levels requires the trials not to address the question at
all, which is closer to an eligibility error than an indirectness rating — if the evidence
is that far from the question, the wrong trials were included.

## What would make me wrong, in each direction

- **Rate rate much higher than 28%**: objects carry structured PICO fields I have not seen,
  or the trials' registry data substitutes adequately for an unstated question. The second
  would be a defect in the procedure, not a finding — comparing trials against trials is
  circular and would produce DIRECT by construction.
- **Rate rate much lower than 20%**: the procedure demands a form of PICO nothing in the
  corpus carries, which makes it unusable rather than strict.
- **Downgrade rate below 50%**: either the questions really are scoped to their evidence, or
  the comparison is too lenient to detect restriction — the second is the likelier and is
  the failure mode to check first.
