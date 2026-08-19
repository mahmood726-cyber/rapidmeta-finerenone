# BLOCKED — `bosentan-pah` asks at least three questions under one title

**Blocked on a judgement about what the review asks, not on retrieval.** The search is executed
and recorded below. Everything here is read from named registry fields; nothing is invented.

*Third topic to reach this state, after `ablation-af-review` and `apixaban-vte`, and it is the
same shape as the second: **the object's two trials fall on opposite sides of the split**.*

---

## What the question currently is

```
"Bosentan Pah: NOT POOLABLE AS POSED -- the OUTCOME and DESIGN limb fails on each trial's
 own registered primary outcome?"
```

It is the object's **own verdict**, generator-composed from `title`, `which_limb_fails` and the
outcome name, with a question mark appended. It is not a copied registry field, so
`scripts/lint_question_is_a_question.py` is correctly silent on it — that check compares
questions against the object's own trials' registry text, and this string is in neither place.

This is the fourth instance of the shape measured at 58 of 135 objects in
`FINDINGS-TWO-READ-FAILURES-2026-08-19.md`, and the second where the remedy is a **split**
rather than a restatement.

## The executed search

| database | query as executed | date | returned |
|---|---|---|---:|
| ClinicalTrials.gov v2 | `intervention="bosentan"`, `condition="pulmonary arterial hypertension OR pulmonary hypertension"`, INTERVENTIONAL, **no phase filter** | 2026-08-19 | **57** |

`next_page_token` null and `returned == totalCount`, read from the first page.
**No PubMed search has been run for this topic** — recorded as an absence, not omitted.

**Recall against the object's own included set: 2/2.** Both `NCT00303459` and `NCT00319020`
were surfaced.

## Why this cannot be one review

The 57 records span at least four questions that do not share a population, a comparator, or an
outcome. Every trial named below is quoted from the surfaced set.

### A — Bosentan **monotherapy** against placebo in pulmonary arterial hypertension

The licensing question. Anchors, all placebo-controlled:

- **NCT00091715** EARLY, *"mildly symptomatic pulmonary arterial hypertension"*, n=185
- **NCT00317486** BREATHE-5, *"PAH related to Eisenmenger physiology"*, n=54
- **NCT00377455** scleroderma, exercise-induced PH, n=5, TERMINATED
- **NCT01827059** congenital heart disease, exercise-induced PAH, n=12

### B — Bosentan as **ADD-ON** to established PAH therapy

A different question with a different comparator: background therapy, not nothing.

- **NCT00303459** COMPASS-2, *"bosentan and sildenafil versus sildenafil monotherapy"*, n=334
  — **this is one of the object's two trials**
- **NCT00323297** sildenafil added to bosentan, n=105 — the same combination, **randomised the
  other way round**, which is a fact worth a page of its own
- **NCT01712997** initial combination bosentan + iloprost, n=90
- **NCT03053739** combination versus monotherapy in systemic sclerosis, n=50

### C — Bosentan in pulmonary hypertension that is **not** WHO group 1

Different disease, different natural history, and in two cases a **terminated programme**.

- **NCT00313222** BENEFIT, *inoperable chronic thromboembolic* PH, n=157
- **NCT00310830** / **NCT00313196** ASSET-1 and ASSET-2, PH in **sickle cell disease**, both
  TERMINATED at n=14 and n=12
- **NCT00581607** sarcoidosis-associated PH, n=43
- **NCT00637065** PH with fibrotic lung disease, n=48
- **NCT00820352** heart failure with diastolic dysfunction and PH, n=20

### D — Bosentan in **children**

- **NCT00319267** FUTURE-1, open-label, single-arm, n=36
- **NCT00319020** FUTURE-2, open-label extension, n=33 — **the object's other trial**
- **NCT01223352** FUTURE-3, two-versus-three-times-daily dosing, n=64
- **NCT01338415** FUTURE-4 extension, n=58
- **NCT01389856** PPHN of the newborn, n=23, TERMINATED

## The pair that settles it

The object's own two trials are **NCT00303459** (reading B — a 334-patient randomised add-on
morbidity/mortality trial) and **NCT00319020** (reading D — a 33-patient open-label paediatric
safety extension with **no control arm**, whose registered primary is growth).

The object already says so, and it is right:

> "ONE TRIAL HAS NO CONTROL ARM AND ITS PRIMARY OUTCOME IS GROWTH."

**That is not a poolability problem to be solved. It is two reviews in one object**, and any
criteria set derived from "the object's own recorded fields" would have to pick one and discard
the other — the exact thing `bempedoic-acid-review`'s provenance block was made to declare
rather than hide.

## What P21 requires

> **An ambiguous question is built as several reviews, never chosen between.** Choosing one is
> a decision to withhold evidence from every reading that loses, and it leaves no trace in any
> object.

The precedent has now paid off three times — `ablation-af-review` into three,
`apixaban-vte` into two, and in both cases the split recovered trials that the single object
had silently dropped. **This is the recommendation: build A, B, C and D as four reviews**, or,
if C is judged too heterogeneous to be one review, as A, B, D and a documented refusal for C.

## What is NOT computed yet, and is recorded as owed rather than described

- **Per-reading counts.** The trials above are quoted from the surfaced listing; the number of
  records falling into each reading has **not** been computed. A screen keyed to each reading's
  own criteria is what produces those counts, and no number should be quoted for them until it
  does. `scripts/screen_bosentan_split_2026_08_19.py` does not exist yet.
- **Arm roles.** `topic_identity.locate()` has not been run over these 57 records, so no
  cascade exists and `k3/k4/k5/kNA` are unknown rather than zero.
- **Which reading each of the 57 belongs to.** Assignment must be read from each trial's own
  design, not from its title — the `NCT01309828` lesson from `azilsartan` this same day is that
  a coded field can name a study objective where the disease belongs.

## If no answer comes

**The topic stays blocked rather than defaulting.** A default here would silently pick an
evidence base, and readings A and B are of comparable size with the object holding one trial
from each of B and D.
