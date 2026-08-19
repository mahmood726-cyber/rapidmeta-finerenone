# BLOCKED — `ablation-af-review` needs one decision from Mahmood

**It is blocked on a judgement about what the review asks, not on retrieval.** Everything needed
to decide is below; the decision should take a minute. Nothing here was invented — every
candidate traces to a named registry field, and the trials' own fields are quoted.

*Not resolved at 4am by the author, for the same reason a question was not invented to satisfy a
failing check: a question written to make a check pass is the post-hoc-criteria defect wearing a
different hat.*

---

## What the question currently is

```
"Number of Participants With Composite of Total Mortality, Disabling Stroke, Serious
 Bleeding, or Cardiac Arrest in Patie"
```

- It is **CABANA's (NCT00911508) registered primary outcome measure**, from
  `protocolSection.outcomesModule.primaryOutcomes[0].measure`
- **Truncated at exactly 120 characters**, mid-word — the sentence ends `…in Patie`
- **The same string also fills `title`, `outcomes[0].name`, and `outcomes[0].definition`.** The
  object's entire identity is one of its four trials' registry fields
- `population_stated` returns **PASS** on it, because it tests whether the field is non-empty

## Why this is not a wording fix — the four trials do not share an intervention

| trial | registered condition | randomised contrast (from `armGroups`) |
|---|---|---|
| **CASTLE-AF** NCT00643188 | Atrial Fibrillation; **Heart Failure** | catheter ablation vs conventional (EXPERIMENTAL vs ACTIVE_COMPARATOR) |
| **CABANA** NCT00911508 | Atrial Fibrillation; Arrhythmia | **Left Atrial Ablation** vs Rate **or** Rhythm Control Therapy |
| **EAST** (EAST-AFNET 4) NCT01288352 | Atrial Fibrillation; Stroke | **early standardised rhythm control** vs **usual care** (NO_INTERVENTION) |
| **RAFT-AF** NCT01420393 | **Heart Failure**; Atrial Fibrillation | Rhythm Control vs Rate Control |

Two facts follow directly, and they are what makes this a decision rather than an edit:

1. **EAST-AFNET 4's intervention is early rhythm control, not ablation.** A topic named
   *ablation* includes a trial whose randomised contrast is a rhythm-control **strategy**.
2. **Only CASTLE-AF and RAFT-AF require heart failure.** CABANA and EAST do not.

So the question chosen **decides the included set**. That is why it cannot be picked to fit the
four trials already present — doing so would be criteria written backwards from an included set,
the exact thing `bempedoic-acid-review`'s provenance block was made to declare.

---

## Three candidate restatements — pick one

### A — Catheter ablation vs medical therapy
> *In adults with atrial fibrillation, what is the effect of catheter ablation compared with
> medical rate- or rhythm-control therapy on death, stroke, and hospitalisation?*

- **Traces to:** CABANA `armGroups[0].label = "Left Atrial Ablation"`; CASTLE-AF EXPERIMENTAL arm
- **Included set becomes 3.** EAST-AFNET 4 drops out — its contrast is early rhythm control, not
  ablation
- **Matches the topic's own name.** Narrowest and most defensible; costs one trial

### B — Rhythm control vs rate control or usual care
> *In adults with atrial fibrillation, what is the effect of a rhythm-control strategy
> (including catheter ablation) compared with rate control or usual care on death, stroke, and
> heart-failure hospitalisation?*

- **Traces to:** RAFT-AF `"Rhythm Control"` vs `"Rate Control"`; EAST `"early standardised rhythm
  control"` vs `"usual care"`
- **Included set stays 4.** All four fit
- **Cost:** the intervention is a *strategy*, not a procedure, and the topic name `ablation-af`
  would then be wrong. CABANA's comparator is rate **or** rhythm control, so one arm of the
  comparator is the intervention of another trial

### C — Rhythm control in AF **with heart failure**
> *In adults with atrial fibrillation and heart failure, what is the effect of a rhythm-control
> strategy compared with rate control or usual care on death and heart-failure hospitalisation?*

- **Traces to:** CASTLE-AF and RAFT-AF `conditionsModule.conditions`, both naming Heart Failure
- **Included set becomes 2.** CABANA and EAST drop out — neither requires heart failure
- **Most homogeneous population and estimand**; smallest evidence base

| | question | k included | drops | keeps topic name honest |
|---|---|---|---|---|
| **A** | ablation vs medical therapy | 3 | EAST | yes |
| **B** | rhythm control vs rate/usual | 4 | none | no — rename needed |
| **C** | rhythm control in AF+HF | 2 | CABANA, EAST | no — rename needed |

**If no answer comes, the topic stays blocked rather than defaulting.** A default here would
silently pick an evidence base.

---

## What happens after the decision

1. `question`, `title`, `outcomes[0].name` and `outcomes[0].definition` restated — all four carry
   the truncated string today
2. The eligibility block written to match, carrying `predefined: false` and its post-hoc status
   on its face, as `bempedoic-acid-review` does
3. Search executed and recorded verbatim; cascade counted; remainder screened on the three-way
   disposition
4. `scripts/lint_question_is_a_question.py` must return clean for this topic

## How it was found, and what else it found

`scripts/lint_question_is_a_question.py`, written after the truncation was spotted. It compares
`question`/`title`/outcome text against the registry text of the object's **own** trials.

It also flags **`bococizumab-lipid-review`** — `outcomes[1].definition`, truncated at **150**
characters from NCT01968967. **Two different truncation widths on two topics, so this is not one
bad extraction run.** That topic will need the same decision when it is reached.

Scope stated honestly: 16 topics could be compared; **119 could not**, because no registry record
is cached for their trials. The clean count is 14, not 133.

*Silent truncation was named as a class this registry was missing by an outside critic (agy,
Gemini 3.1 Pro) minutes before it was found here.*
