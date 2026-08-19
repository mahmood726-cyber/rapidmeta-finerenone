# BLOCKED — `apixaban-vte` needs one decision from Mahmood

**It is blocked on a judgement about what the review asks, not on retrieval.** The search is
executed and recorded, the cascade is counted at every stage, and the preconditions have been
run. Everything below is computed from named registry fields; nothing is invented, and no
question has been chosen to make a check pass.

*Second topic in the queue to reach this state, and it is a DIFFERENT shape from
`ablation-af-review` — see "How this differs" at the end. It is also not rare: 58 of 135 topic
objects answer "what is the question" with the object's own verdict. See
FINDINGS-TWO-READ-FAILURES-2026-08-19.md.*

---

## What the question currently is

```
"Apixaban Vte: NOT POOLABLE AS POSED -- the COMPARATOR and PARTICIPANTS and OUTCOME limb
 fails on each trial's own registered primary outcome?"
```

It is the object's **own verdict**, composed by the generator from `title`, `which_limb_fails`
and the outcome name, with a question mark appended. It is not a copied registry field, so
`scripts/lint_question_is_a_question.py` is correctly silent on it — that check compares
questions against the object's own trials' registry text, and this string is in neither place.

`population_stated` returns **PASS**, because it tests whether a field is non-empty:

> THE PROPERTY CLAIMED IS "POPULATION STATED". THE PROPERTY VERIFIED IS "FIELD NON-EMPTY".

That sentence was written for `ablation-af-review`. This is the same gap in a shape the
companion check cannot see.

---

## Why the criteria cannot be derived from the object — one coded field settles it

`attr-cm-review` was built with criteria **derived post hoc from the object's own recorded
fields**, carrying `predefined: false` on its face. That was legitimate there because its two
trials share a population, an intervention and a comparator, and differ only on estimand.

Here the two included trials fall on **opposite sides of the registry's own coded field**:

| trial | `designInfo.primaryPurpose` | arm typing | n | registered primary |
|---|---|---|---:|---|
| **NCT02366871** apixaban vs enoxaparin, suspected pelvic malignancy | **PREVENTION** | EXPERIMENTAL vs ACTIVE_COMPARATOR — apixaban is the intervention | 400 | major bleeding; clinically relevant non-major bleeding |
| **NCT02829957** RAMBLE, rivaroxaban vs apixaban, heavy menstrual bleeding | **TREATMENT** | **both arms ACTIVE_COMPARATOR** — apixaban is *not* the declared intervention | 19 | PBAC score (pictorial menstrual blood-loss chart) |

So a criteria set derived from "the object's own recorded fields" would have to **pick one of
the two trials and discard the other**. That is criteria written backwards from a chosen
included set, which is the exact thing `bempedoic-acid-review`'s provenance block was made to
declare rather than to hide.

The object already says so in its own words, and it is right:

> "THREE LIMBS DIFFER AT ONCE… Different comparators, different populations, different
> outcomes. No two of these can be averaged into one answer."

---

## What the executed search found — the work that did not depend on the decision

| stage | k | |
|---|---:|---|
| **k0 surfaced** | **82** | ClinicalTrials.gov v2, `cond="venous thromboembolism OR deep vein thrombosis OR pulmonary embolism"`, `intr="apixaban"`, INTERVENTIONAL, no phase filter, 2026-08-19 |
| k2 role located | 82 | every record classified; none refused for want of a payload |
| k3 experimental | 54 | apixaban is the randomised intervention |
| k4 comparator | 19 | apixaban is a declared comparator |
| k5 background | 7 | apixaban in every arm — the contrast is something else |
| kNA not assessable | 2 | see below; **neither is "excluded"** |
| **k in this object** | **2** | |
| **k unscreened remainder** | **71** | 54 + 19 − 2. **Unscreened, and blocked rather than pending** |

`82 = 54 + 19 + 7 + 2` reconciles.

**A search that missed one of its own included trials, recorded rather than replaced.** The
first query carried `phase=[PHASE3,PHASE4]` and returned 49 records — and **NCT02366871, one of
this object's own two trials, was not among them**, because it is registered PHASE2. A third
distinct shape of the same recall defect: `sglt2-hf` lost DELIVER and `iv-iron-hf` lost
AFFIRM-AHF and HEART-FID to condition terms one word too narrow; here it was a **design filter**
rather than a topic term.

**PubMed**: 439 records, 50 retrieved. The other 389 are **unexamined**, not excluded.

**Pagination checked rather than assumed**: `nextPageToken` null and `returned == totalCount`
on both queries. DEFECT-REGISTRY E10 names cursor abandonment as a class nothing here looks for.

### The two NOT_ASSESSABLE are two different absences

- **NCT00252005** (Botticelli DVT) — RANDOMIZED, PARALLEL, DOUBLE-blind, n=520, and the payload
  declares **no `armGroups` at all**. Role cannot be read from an absent field.
- **NCT04128254** — one record, `Drug: Apixaban Oral Tablet`, attached to **both** the
  EXPERIMENTAL arm labelled 'Apixaban' **and** the PLACEBO_COMPARATOR arm labelled 'Placebo'.
  The registration contradicts itself.

### k3 was 52 before a repair made this morning

ADVANCE-2 (NCT00452530) and APROPOS (NCT00097357) were classified **background** because their
control arms carry `Drug: Apixaban-matching placebo` and `Drug: Apixaban Placebo` — the drug's
own name at the **start** of a record that is a **placebo for it**. Two of the pivotal apixaban
thromboprophylaxis trials, withheld from the experimental set of an apixaban topic.

---

## Two candidate questions — pick one

Both are traced to `designModule.designInfo.primaryPurpose`, a **coded** field, counted over
the 73 trials in which apixaban is part of the randomised contrast.

### A — Apixaban for the TREATMENT of venous thromboembolism
> *In adults with acute or recent venous thromboembolism, what is the effect of apixaban
> compared with conventional anticoagulation or placebo on recurrent VTE and bleeding?*

- **34 of 73** randomised-apixaban trials are coded `TREATMENT`; **15 COMPLETED**, 5 of those
  with n ≥ 1000
- Anchors: **NCT00643201** (n=5614, apixaban vs enoxaparin/warfarin), **NCT00633893** (n=2711,
  extended treatment vs placebo), **CARAVAGGIO** NCT03045406 (n=1170, cancer-associated VTE)
- **Keeps NCT02829957** (RAMBLE) in scope by population — though apixaban is not its declared
  intervention and its primary is a menstrual blood-loss chart, so it would very likely screen
  out on comparator and outcome. **Drops NCT02366871.**

### B — Apixaban for the PREVENTION of venous thromboembolism
> *In adults at risk of venous thromboembolism, what is the effect of apixaban thromboprophylaxis
> compared with enoxaparin, another anticoagulant, or no anticoagulation on symptomatic VTE and
> bleeding?*

- **33 of 73** are coded `PREVENTION`; **17 COMPLETED**, 4 of those with n ≥ 1000
- Anchors: **ADOPT** NCT00457002 (n=6758, medically ill), **ADVANCE-3** NCT00423319 (n=5407),
  **ADVANCE-1** NCT00371683 (n=3608)
- **Keeps NCT02366871.** **Drops RAMBLE.**

| | question | coded-field pool | completed | keeps of the object's 2 |
|---|---|---:|---:|---|
| **A** | apixaban for VTE treatment | 34 | 15 | RAMBLE only |
| **B** | apixaban for VTE prophylaxis | 33 | 17 | NCT02366871 only |

**If no answer comes, the topic stays blocked rather than defaulting.** A default here would
silently pick an evidence base, and the two are almost the same size, so nothing about the
numbers recommends one.

### And the coded field is a convention too — stated, not hidden

`primaryPurpose` splits the field cleanly and **is not reliable at the row level**. The proof
is the same pair that disagree on arm typing:

```
ADVANCE-2  NCT00452530  knee replacement thromboprophylaxis  -> coded TREATMENT
ADVANCE-3  NCT00423319  hip  replacement thromboprophylaxis  -> coded PREVENTION
```

One programme, one design, months apart, **coded on opposite sides of the split this decision
turns on** — and typed on opposite sides of EXPERIMENTAL/ACTIVE_COMPARATOR as well. So the
counts above are *the registry's coding*, not a fact about the trials, and whichever question is
chosen, the screen must read each trial's design rather than inherit its label.

---

## What happens after the decision

1. `question`, `title` and `outcomes[0]` restated to the chosen question; the eligibility block
   written to match, carrying `predefined: false` and its post-hoc status on its face
2. **All 71 remaining trials screened three-way**, with k3 and k4 read **together** — the
   ADVANCE-2/ADVANCE-3 typing inversion means the boundary between them is a registrant's habit,
   not a property of the trials
3. Any `ELIGIBLE_POOLABLE_NOT_INCLUDED` recovered, extracted from source, and re-pooled with old
   and new side by side. **On present evidence there will be several**: this object holds 2
   trials and the completed, large, placebo- or active-controlled apixaban VTE trials are not
   among them
4. Built with `python ssot/build_tabbed.py`, verified in served bytes with md5 **and** a content
   check

Per-topic search, PRISMA, cascade and extraction are already written and keyed to the topic at
`ssot/apx_topic_data.py`, so the build is one registration away once the question is settled.

---

## How this differs from `ablation-af-review`

Both are "the question is not a question", and the remedies are not the same.

| | `ablation-af-review` | `apixaban-vte` |
|---|---|---|
| what the question holds | **one trial's registry field**, truncated at 120 chars mid-word | **the object's own verdict**, generator-composed |
| detectable by | `lint_question_is_a_question.py` — it compares against the trials' registry text | **nothing currently** — the string appears in no registry record |
| the decision | which of three restatements, over 4 trials already present | which of two evidence bases, over 71 unscreened trials |
| cost of a default | drops or keeps 1–2 trials | picks between two pools of ~34 and ~33 |

The second row is the one worth acting on. A check written against the shape that was found
does not see the shape that was not, and **58 of 135 objects are in this second shape** —
measured, and recorded in FINDINGS-TWO-READ-FAILURES-2026-08-19.md.
