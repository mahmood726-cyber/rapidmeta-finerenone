# Item 1 — one statistic, two values, one page. Swept corpus-wide.

**1,463 pages examined. 8 serve two different values of Q for one pool.**
And the direction is the opposite of the one reported.

## Kinds before counts

| kind | n |
|---|---|
| pages examined | 1463 |
| no repeated statistic | 1427 |
| several pools, no mismatch | 25 |
| one value at two precisions — **not** a contradiction | 35 |
| **page with a genuine mismatch** | **11** |

Of the 11, **8 are `Q`** and 3 are `I²`/`τ²` only.

## Why the split matters: Q is estimator-invariant

`Q` is computed with fixed-effect weights and **does not depend on the τ² estimator**, so a
`Q` disagreement on one pool is a contradiction whatever method was used. `I²` and `τ²` are
not: `INCLISIRAN` shows `I² 72.0 / τ² 9.52` beside `74.1 / 10.6`, and the page itself says
these are **DerSimonian–Laird and REML**. That is a labelling weakness — the I² is printed
with no estimator named — not a stale value. It is excluded from the count above.

## The eight, every one hand-verified as the same pool

Same `k`, same `df`, same `τ²`; the result line against the GRADE inconsistency narrative.

| page | result line | GRADE narrative | recomputed | correct |
|---|---|---|---|---|
| `agyw-hiv-prep-review` | 0.1533 | 0.1535 | **0.1535** | narrative |
| `alirocumab-lipid` | 58.42 | 58.4577 | **58.4577** | narrative |
| `apixaban-vte-treatment` | 1.257 | 1.2575 | **1.2575** | narrative |
| `ceftaroline-auto-full-review` | 0.6562 | 0.6553 | **0.6553** | narrative |
| `gepotidacin` *(frozen — measured, not fixed)* | 3.385 | 3.3879 | **3.3879** | narrative |
| `lefamulin-cabp` | 0.7313 | 0.7316 | **0.7316** | narrative |
| `nirsevimab-infant-rsv` | 0.0876 | 0.0879 | **0.0879** | narrative |
| `tigecycline-ciai` | 2.157 | 2.1564 | **2.1564** | narrative |

## ⚠️ The adjudication in the review is inverted, and 8 of 8 say so

The review states *"the correct value from the counts is 0.7313"*. Recomputing Q from
`lefamulin`'s own stored per-trial CIs gives **0.731640**, which reproduces the stored metafor
log exactly — and the p-value settles it independently: the log states `p = 0.3924`, and
`Q = 0.7316 → p = 0.3924` while `Q = 0.7313 → p = 0.3925`. **The object holds no arm-level
counts at all** (`arms = 0`, no events), so a value "from the counts" cannot have been derived
from it.

Then the same recomputation was run on all eight. **In every case the narrative matches and the
result line does not.**

⇒ **The diagnosis stands and is stronger than reported — the GRADE section is not regenerated
from the same object as the result — but the stale side is the STRUCTURED `heterogeneity.q`
FIELD that the headline renders, not the GRADE prose.** A fix that propagated the result-line
value into GRADE would have made eight pages uniformly wrong instead of visibly inconsistent.

## The instrument, and the four times it was wrong first

Two detectors, all six control legs run on every invocation.

1. **NEAR** — one statistic, two values within 1%. Proximity is the signal: distinct pools
   differ by tens of percent, a value recomputed on slightly different inputs by a fraction.
2. **BUNDLE** — statistics written beside one `on N df`, compared only when two bundles
   **agree on a distinctive (non-zero) statistic**. Agreement, not `df`, is the same-pool test.

Each correction came from a control failing, not from the sweep looking clean:

- **16 pages → 5** once *"is the shorter value a correct rounding of the longer?"* was added.
  `5.16` beside `5.161` is inconsistent decimal places, not a contradiction.
- **`df` alone does not identify a pool.** `IV_IRON_HF` has four k=2 outcomes, all `df=1`, and
  the first bundle detector reported all six pairings. Every one wrong.
- **The bundle windows overlapped**, so both bundles picked the same first match and two
  bundles identical by construction can never conflict. Its own positive control caught it.
- **Two thresholds were tried and both rejected real cases**: 3 significant figures rejects
  lefamulin (0.731 vs 0.732); 0.1% rejects AGYW (0.13%). Every finding is printed with its
  percentage so the 1% choice can be argued with rather than trusted.

**What it cannot see:** a statistic rendered into a rasterised SVG, and a value wrong in both
places. It finds disagreement, never error — which is why all eight were recomputed.

## Recommendation

The fix is **one generator change, not eight page edits**: make the result line derive Q from
the same refit the GRADE narrative quotes, or re-derive `heterogeneity.q` and correct the
stored field. Eight pages, one of them frozen. I have not touched anything.
