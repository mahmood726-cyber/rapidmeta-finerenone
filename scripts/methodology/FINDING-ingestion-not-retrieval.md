# The k deficit is an ENUMERATION failure, not a retrieval one

**Date:** 2026-09-02 · **Topic tested:** `agyw-hiv-prep-review` (dapivirine ring)
**Snapshot:** `F:\AACT-storage\AACT\2026-08-30` — **DATA DATE 2026-08-27**, cite the data
date, never the folder date. **No phase filter applied.**
**MEASURED** — `python aact_ingestion_loss.py dapivirine NCT01539226,NCT01617096`

---

## The result

| | |
|---|---|
| randomised dapivirine trials **in the local snapshot** | **39** |
| candidate pool the topic actually screened | **5** (2 included + 3 stated exclusions) |
| **never screened at all** | **34** |
| ingestion recall (ingested / available) | **0.051** |

**Tight, defensible subset — completed phase-3 randomised trials never screened: 2.**

```
NCT03965923  n=1,104  COMPLETED
NCT04140266  n=  394  COMPLETED
```

The topic pools **k=2**. Two completed phase-3 trials of the same intervention sat on local
disk and were never considered.

## Why this is decisive, and needs no ground truth

**The snapshot is a local file. No search was involved.** A retrieval-recall explanation
cannot account for a trial you already have on disk. Same logical shape as the OR<AND
impossibility: it is settled by the structure of the situation, not by adjudicating a label.

## ⛔ The mechanism: the pool was SEEDED, not ENUMERATED

The object's own text reads `"3 seeded trials excluded and stated"`, and **`inputs` has
exactly one key — `trials`.** `candidates` appears **zero** times in the object.

⇒ **There is no candidate-pool field.** The 5 were seeds; the 34 were never candidates.

**This is the load-bearing point: ingestion precedes eligibility screening.** A pool of 5
means 34 trials were never *screened*, whatever their eligibility would have been. The topic
cannot have excluded them on eligibility grounds, because it never enumerated them. A PRISMA
flow is not reportable from a seeded pool — there is no screened denominator to report.

**And the honest boundary on my own claim:** I am *not* asserting that 34 trials belong in
the review. Many of the 39 are phase-1 PK studies a review of efficacy would rightly exclude.
**Whether each is eligible is unknown precisely because it was never screened** — and that is
the finding, not a hedge on it.

## ⛔ A phase filter is NOT the main mechanism here

**MEASURED** phase distribution of the 39 randomised: PHASE1 21 · PHASE1/PHASE2 7 ·
PHASE3 6 · PHASE2 4 · **NA 1**.

A phase filter would silently drop **1 of 39 (3%)** — and the single `NA` trial
(`NCT01539226`, The Ring Study) **was** ingested. So the phase-filter hazard is real and worth
keeping out of the code, but it does **not** explain this loss. The loss is the seeded pool.

## Is this the same defect as the 10.4% screening recall? **NO — and that matters**

| | 10.4% (PREREG-2) | this |
|---|---|---|
| what failed | a search **ran** and retrieved 11 of 106 knowns | **no search ran**; the pool was seeded |
| stage | retrieval | **enumeration, upstream of screening** |
| fix | a better query, or a different source | **enumerate the local snapshot** |

They are **two independent failure modes that both depress k**, not one defect seen from two
ends. Treating them as one would hide the more severe: **enumeration failure precedes
screening, so no improvement in search quality can repair it.**

**What they share is the family**, and it is the same family as `retmax` and as every
reach-vs-coverage finding this week: **a bounded pool standing in for a population.**
`retmax=200` for a 843-record query; a 5-seed pool for a 39-trial population; a recency window
for a result set. Three instances, one shape.

## The experiment as posed, and its answer

> *"re-score recall for a topic using the AACT-complete trial set instead of our ingested one.
> If recall jumps, the search was never the bottleneck."*

**The answer is stronger than a jump: for this topic there was no retrieval step to re-score.**
Search was never the bottleneck because search was never run. The apparatus can still score any
search strategy against known positives — but on this topic it would be measuring a stage the
pipeline does not have.

## What to do, in order

1. **Add an enumerated candidate pool to the topic schema** — `inputs.candidates` with the
   local-snapshot query that produced it and its count. Absent that field, `k` has no
   denominator and no PRISMA flow is reportable.
2. **Make it structural, not a convention** — the builder should **refuse** to emit a topic
   whose `inputs.candidates` is missing, the way `grade_inputs.py` refuses a certainty. A
   convention gets broken by the next person in a hurry and fails silently.
3. **Then screen the 34** for this topic and report the flow. `NCT03965923` (n=1,104) and
   `NCT04140266` (n=394) first.
4. **Sweep the corpus** with `aact_ingestion_loss.py` — it takes a topic term and an ingested
   NCT list and needs nothing else. Every topic with an intervention name can be scored today.
