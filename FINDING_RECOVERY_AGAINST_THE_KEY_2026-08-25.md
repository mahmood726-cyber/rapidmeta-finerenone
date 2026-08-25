# 62% of the registered trials in these meta-analyses have posted no results at all

**With a validated answer key of 866 (review, study) pairs whose registration is known, the
registry was asked to reproduce the numbers the Cochrane rows claim. The recovery rate is
secondary. The dominant fact is that for 62% of these trials there is nothing in the registry
to compare against.**

---

## Two tiers, different units, never summed

| **Tier A — arm denominators** (unit: trial) | |
|---|---|
| trials in the key | 860 |
| **no results posted** | **532 — 62%** |
| assessable | 328 |
| **recovered exactly** | **130 / 328 — 40% of assessable** |
| near (within 2, *not* counted as recovered) | 39 |
| **null** — the same pair against a *different* trial | **0 / 860 — 0%** |

| **Tier B — event counts** (unit: Cochrane row) | |
|---|---|
| dichotomous rows in the key | 8,427 |
| **no results posted** | **4,899 — 58%** |
| assessable | 3,528 |
| **recovered exactly** | **1,535 / 3,528 — 44% of assessable** |
| near (within 2, *not* counted as recovered) | 886 |
| **null** — the same counts against a *different* trial | **620 / 8,427 — 7%** |

A trial and a row are different units. The two tiers are reported separately and are never
added together.

## The null does the work here

Small integers collide, so "the registry contains these two numbers" is a weak claim by
construction. Scoring every Cochrane row against a *different* trial's registry record gives
the floor:

- **Tier A null is 0%.** A pair of arm sizes is highly specific — 130 of 328 is a real
  recovery, not arithmetic coincidence.
- **Tier B null is 7%.** Event counts are small numbers and do collide. The 44% is measured
  against that 7%, and only the gap is about recovery.

Reporting Tier B's 44% without the 7% would overstate it. Reporting it as 44 − 7 would be a
different kind of error, so both are given and neither is subtracted.

---

## What a non-match is, and is not

**A non-match is not a disagreement.** A Cochrane row and a registry outcome can differ
legitimately for reasons that have nothing to do with error: a different follow-up timepoint, a
different outcome definition, a subgroup, an intention-to-treat versus per-protocol
denominator, or a count the review took from a later publication than the registry posting.

This measures **exact reproducibility of a stated number from the public registry** — not
whether either party is right. The 886 near-misses in Tier B, within two of the stated count,
are consistent with exactly those legitimate differences and are counted as *not recovered*
rather than folded in.

**`NO RESULTS POSTED` is a third state, kept separate throughout.** The registry not holding a
number is not the registry disagreeing with one. Collapsing the two would convert a
transparency fact into an accuracy claim, and the transparency fact is the larger finding:

> **Of 860 registered trials contributing to these Cochrane meta-analyses, 532 have posted no
> results to ClinicalTrials.gov.**

---

## How this sits with the rest

The three-layer finding was that the registration identifier is obtained during risk-of-bias
assessment and then discarded at every layer below — so a third party cannot get from a
meta-analysis row to the trial. This adds the layer below that:

**Even when the identifier is recovered, the registry answers for well under half of what the
row claims — and for 62% of trials it does not answer at all.** The identifier is necessary and
it is not sufficient. Both facts are about what the public record supports, not about whether
any number is correct.

---

## Limits, stated

- **The key is 866 pairs** from the validated join, restricted to those with at least one
  dichotomous Cochrane row. Two registry records could not be fetched and are recorded MISSING,
  not scored.
- **Matching is exact, to the integer**, and that choice is deliberate: a tolerance would make
  the measurement a statement about how close counts as close, and no principled value exists
  for that. Near-misses within two are reported so the strictness is visible.
- **ClinicalTrials.gov only.** A trial that posted results to another registry, to a regulator,
  or in a journal supplement counts here as "no results posted" — so 62% is a statement about
  *this* registry, and the recoverable fraction across all sources is higher by an unmeasured
  amount.
- **Tier B searches all posted outcome measures and adverse-event tables** for a pair matching
  the row. That is generous to recovery: it does not require the matched outcome to be *the*
  outcome the review analysed. The rate is therefore an upper bound on outcome-level
  reproducibility.
- **The answer key comes from our own join.** Its resolution step is corroborated against
  PubMed at 583/584 and its era stratification reproduces the 2005 ICMJE policy change, but a
  systematic error in the join would propagate here.
- Every figure above is produced by executing code against data. No model judgement is
  involved, so the k=3 adjudication specification does not apply.
