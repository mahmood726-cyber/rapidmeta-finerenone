# `bococizumab-lipid-review` needs NO decision packet — and here is why

**Expected to need one, and it does not.** It was queued alongside `ablation-af-review` and
`apixaban-vte` as a third instance of the truncated-question class, on the strength of
`scripts/lint_question_is_a_question.py` flagging a **150-character truncation** from
NCT01968967. The instruction was explicit: build each legitimate reading as its own review *if*
the truncation resolves into more than one real question; **if it resolves into exactly one,
build it, and produce a packet only if the question cannot be recovered from source at all.**

**It resolves into exactly one.** Read from the five registrations' own coded fields:

| trial | acronym | condition | intervention | comparator | registered primary |
|---|---|---|---|---|---|
| NCT01968967 | SPIRE-LDL | Hyperlipidemia | Bococizumab | Placebo | % change from baseline in fasting LDL-C at week 12 |
| NCT02100514 | SPIRE-LL | Hyperlipidemia | Bococizumab | Placebo | *(identical)* |
| NCT01968954 | SPIRE-HR | Hyperlipidemia | Bococizumab | Placebo | *(identical)* |
| NCT02458287 | SPIRE-AI | Hyperlipidemia | Bococizumab 150 mg / 75 mg | matching placebos | *(identical, per dose)* |
| NCT02135029 | SPIRE-SI | Hyperlipidemia | Bococizumab | Placebo **and** atorvastatin | *(identical)* |

One population, one intervention, one comparator, **one estimand — word for word across all
five.** There is no second legitimate reading to build, so P21 does not apply: it says an
ambiguous question becomes several reviews, not that every flagged question is ambiguous.

> **The recoverable question:** *In adults with hyperlipidaemia, what is the effect of
> bococizumab compared with placebo on the percent change from baseline in fasting LDL
> cholesterol at week 12?*

Composed, and every limb points at a field: population at `conditionsModule.conditions`,
intervention and comparator at `armsInterventionsModule.armGroups`, outcome at each trial's
`outcomesModule.primaryOutcomes[0].measure`.

---

## What it has instead, and it is worse than an ambiguous question

The object's `question` field does not hold a truncated registry string. It holds **the
object's own finding**:

```
"Every trial here registers a CONTINUOUS percent change in LDL-C, and this page derived an
 odds ratio from counts."
```

That is the **58-of-135 shape** — a question field answering *what is wrong with this page*
rather than *what does this review ask* — and it is the same shape that blocked `apixaban-vte`.
The 150-character truncation the lint flagged is real but sits in
`outcomes[1].definition`, not in the question.

**And the finding that field carries is a genuine analysis defect, not a wording problem.**
Five trials register a **continuous** endpoint — percent change in LDL-C — and the page derived
an **odds ratio from counts**. An odds ratio over a dichotomised continuous outcome is not the
registered estimand, discards information, and depends on a threshold none of the trials
declares.

> **This topic does not need a decision. It needs a re-analysis on the estimand its own trials
> registered**, and that is a larger and more consequential job than the packet it was queued
> for.

## Disposition

- **No packet written.** Writing one would manufacture a judgement where the source settles it,
  and a decision requested for a question that has only one answer is a decision that teaches
  the reader the wrong thing about the corpus.
- **Not built here.** It needs the full unit — executed search with recall measured, cascade,
  remainder screened, and a re-pool on the continuous estimand rather than the derived odds
  ratio.
- **Recorded as buildable**, not blocked. The distinction matters: `ablation-af-review` and
  `apixaban-vte` were blocked because *no one could tell what the review asked*. This one is
  merely unbuilt.
