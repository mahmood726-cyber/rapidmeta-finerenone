# DECIDED — `ablation-af-review` becomes THREE reviews

> **RETIRED 2026-08-19, NOT DELETED.** The question below was real and the analysis under it
> stands. What did not stand is its framing. Kept in full, with the decision at the top, because
> a packet that asked the wrong question is worth more as a record than as an absence.

## The decision, and why it is better than any option this packet offered

**Mahmood's answer: build all three. Each becomes its own topic, with its own question, its own
included set, its own search, cascade and screening.**

| new topic | question | k | trials |
|---|---|---:|---|
| `ablation-af-medical-therapy` | catheter ablation vs medical rate- or rhythm-control therapy | **3** | CASTLE-AF, CABANA, RAFT-AF |
| `early-rhythm-control-af` | early rhythm control vs usual care — **a rhythm-control review, not an ablation one** | **4** | CASTLE-AF, CABANA, EAST-AFNET 4, RAFT-AF |
| `ablation-af-heart-failure` | ablation-based rhythm control in AF **with heart failure** | **2** | CASTLE-AF, RAFT-AF |

**THE PACKET FRAMED THE PROBLEM THE WRONG WAY ROUND, AND ITS OWN SUMMARY TABLE SHOWS IT.** The
comparison column below is headed `drops` — A drops EAST, B drops none but makes the topic name
wrong, C drops CABANA and EAST. **Every row is a count of evidence discarded**, and the packet
presented that as the axis of choice.

> All three questions are legitimate. Each trial genuinely belongs to at least one of them.
> There was no good answer because *"which do we keep"* has no good answer.
>
> **Choosing is a decision to withhold evidence from whichever readings lose, and nothing in
> this project's guard set catches that.** A dropped trial leaves no trace in any object: it is
> simply not there, and the page reads as complete.

Three topics discard nothing and give each question its honest answer. Written into the standard
as **P21**, because the same shape was already queued — `apixaban-vte` was blocked on TREATMENT
(34) versus PREVENTION (33), two legitimate questions with near-equal evidence, and it is now to
be built as two.

**What this creates, and it is handled rather than tolerated: deliberate cross-topic sharing.**
CASTLE-AF and RAFT-AF appear in all three; CABANA in two. Recorded on each object under
**P22** — which other topics hold each trial and why — and every page states that a corpus-level
k obtained by summing per-topic k double-counts.

**One thing carries forward unchanged from the analysis below.** The four trials measure four
different composites, and the object's own `poolable_reason` says so. That does not dissolve
under the split: within `ablation-af-medical-therapy`, CASTLE-AF, CABANA and RAFT-AF still
register three different primaries. **The split fixes the question, not the estimand**, and each
new review reaches its own pooling decision on its own evidence rather than inheriting one.

---

# The original packet, as written

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
