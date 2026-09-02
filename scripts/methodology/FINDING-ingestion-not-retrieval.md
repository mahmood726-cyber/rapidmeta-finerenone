# The k deficit is an ENUMERATION failure, not a retrieval one

**Date:** 2026-09-02 · **Revised the same night — see the correction below.**
**Snapshot:** `F:\AACT-storage\AACT\2026-08-30` — **DATA DATE 2026-08-27**; cite the data
date, never the folder date. **No phase filter.**
**MEASURED** — `python aact_sweep.py agyw-hiv-prep-review sglt2-hf iv-iron-hf`

---

## ⛔ CORRECTION TO THE FIRST VERSION OF THIS FINDING

The first version reported **34 trials never screened** for the dapivirine topic. **That was
inflated and it was my error.** The drug expression was derived from the topic's *title*
(bare `dapivirine`), which captures gel and film formulations across phase-1 work.

Derived instead from the topic's **own registered intervention names** — `dapivirine vaginal
ring` — plus its **own registered condition** (`hiv infections`), the pool is **5, not 39**,
and the number never screened is **3, not 34**.

**The finding did not soften. It got sharper**, and the corrected form is the one that should
be quoted.

---

## The dapivirine result: two pools of IDENTICAL SIZE that share only 40%

| | |
|---|---|
| the topic screened | **5** — included `NCT01539226`, `NCT01617096`; excluded `NCT00625404`, `NCT00705679`, `NCT01386294` |
| AACT holds (ring + HIV + randomised) | **5** — the same 2, plus `NCT01363037`, `NCT02920827`, `NCT03593655` |
| **overlap** | **only the 2 included** |

⇒ **A SEEDED POOL IS NOT A SMALL SUBSET OF THE ENUMERABLE POPULATION — IT IS A DIFFERENT
SET.** That is worse than "too small", because the bias cannot even be characterised.

⇒ **A COUNT COMPARISON WOULD HAVE SAID "NO PROBLEM."** 5 against 5. The defect is invisible
to any check that compares sizes rather than membership.

---

## The three flagship topics, condition-restricted

| topic | available | ingested | **never screened** | completed phase-3 unseen |
|---|---|---|---|---|
| **`sglt2-hf`** | 117 | 4 | **113** | **9** — largest `NCT04564742` **n=4,017** |
| **`iv-iron-hf`** | 18 | 5 | **14** | **2** — `NCT00520780` n=456, `NCT01394562` n=174 |
| `agyw-hiv-prep-review` | 5 | 2 | **3** | 0 |

### ⛔ What this does to the claim we publish

**On `sglt2-hf` the decision record covers 4 trials out of 117 available.**

We say *"every screened record carries a named decision"* and set it against a Cochrane
abstract that names four databases and zero trials. That claim is **true, and much weaker
than it sounds**, when the pool is a seed list rather than an enumeration:
**a perfect audit trail over a pool somebody typed.**

**Verbatim, and it is what makes the claim unarguable:**

> I am NOT claiming the 113 belong — many will be small mechanistic RCTs a review would
> rightly exclude. Their eligibility is unknown because they were never screened, and that is
> the finding rather than a hedge on it.

---

## Why this is decisive, and needs no ground truth

**The snapshot is a local file. No search was involved.** A retrieval-recall explanation
cannot account for a trial you already have on disk. Same logical shape as the OR<AND
impossibility: settled by the structure of the situation, not by adjudicating a label.

## The mechanism: the pool was SEEDED, not ENUMERATED

The object's own text reads `"3 seeded trials excluded and stated"`; `inputs` has exactly one
key — `trials`; `candidates` appears **zero** times.

**Ingestion precedes eligibility screening.** A pool of 5 means the rest were never
*screened*, whatever their eligibility would have been — so **no PRISMA flow is reportable,
because there is no screened denominator.**

## ⛔ A phase filter is NOT the mechanism here

**MEASURED:** of the broader dapivirine randomised set, **1 of 39 is `phase=NA` (3%)** — and
that one, `NCT01539226`, **was** ingested. Keep the no-phase-filter rule; it does not explain
this loss.

---

## Not the same defect as the 10.4% screening recall

| | 10.4% (PREREG-2) | this |
|---|---|---|
| what failed | a search **ran**, retrieved 11 of 106 | **no search ran**; pool was seeded |
| stage | retrieval | **enumeration, upstream of screening** |
| fix | better query or another source | **enumerate the local snapshot** |

Two independent modes that both depress k. **No improvement in search quality can repair an
enumeration failure.** What they share is the family — **a bounded pool standing in for a
population** — now four instances: `retmax=200` for an 843-record query; a recency window for
a result set; a 5-seed pool for a 117-trial population; a title-derived drug term for a
registered one.

---

## Two defects in the sweep itself, both caught by IMPLAUSIBILITY

**1. `COMBINATION_PRODUCT` has an UNDERSCORE.** I compared against `"combination product"`
with a space, so every dapivirine intervention was rejected and the topic scored as
**unmeasurable**. A working measurement turned into a **false absence by a format mismatch** —
same class as Crossref lowercasing its DOIs.

**2. The drug is not the population when a drug has several indications.** Without a condition
restriction, `sglt2-hf` counted **846** dapagliflozin/empagliflozin trials in diabetes and CKD
as unscreened heart-failure trials. `iv-iron-hf` needed it twice over: `iron deficiency` alone
gives **224**, but only **18** of those also register heart failure — hence **14**, not 220.

**Both were caught because the number was implausible, which is the only detector that works
on your own queries.** Neither would have been caught by a test.

---

## What to do, in order

1. **Full-corpus sweep** ranked by absolute trials-never-screened, drug **and** condition both
   derived from each topic's own registered fields and **printed per topic for audit**.
   *Coordinated with the AACT lane — one sweep, not two.*
2. **`inputs.candidates` as a named, rendered state.** A topic with no enumerated pool must
   render `NO_CANDIDATE_POOL_ENUMERATED`. The reader deserves to know the denominator does not
   exist.
3. **Make it structural, not a convention** — the builder should refuse to emit a topic with no
   candidate pool, the way `grade_inputs.py` refuses a certainty.
