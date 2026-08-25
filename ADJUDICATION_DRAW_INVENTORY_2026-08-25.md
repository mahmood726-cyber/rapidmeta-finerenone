# Which of our figures rest on a single model draw

**Specification adopted 2026-08-25, from the site lane's stability measurement: three
independent adjudications, majority vote, against a pinned artefact. A single adjudication is
91% reproducible; three by majority vote is 99%. One must never be quoted alone.**

This is a labelling pass, not a re-run. Every figure below is marked by how many draws stand
behind it, counted from the ledgers rather than remembered.

---

## Counted, not asserted

| ledger | verdicts | draws per cell |
|---|---|---|
| `corpus_panel_2026_08_25.jsonl` | 298 | **1 — all of them** |
| `corpus_panel_round2_2026_08_25.jsonl` | 184 | **1 — all of them** |
| `panel_four_families_2026_08_25.jsonl` | 123 | **1 — all of them** |
| `panel_claims_adjudicated_2026_08_25.jsonl` | 38 | **1 for 36, 2 for one claim** |

**Every model-adjudicated figure this project has reported is k=1.** None meets the
specification. The adjudication ledger additionally records `artefact_sha` on **0 of 38** rows,
so those verdicts are unpinned as well as single-draw.

---

## The two classes, and only one is affected

The specification applies to figures produced by a **model judgement**. It does not apply to
figures produced by **executing code against data** — those are reproducible by re-running them,
and their failure mode is a wrong instrument rather than a wrong draw.

### Single draw — must not be quoted alone

| figure | where |
|---|---|
| student `MISLEADING` / editor `DESK-REJECT` verdicts, 149 pages | corpus panel round 1 |
| the 37 both-personas-negative pages | derived from those verdicts |
| cross-family agreement (reported as 83%) | round 2 |
| four-family unanimity / 3-1 / 2-2 splits | four-family panel |
| 48 of 61 within-family divergence | four-family panel |
| raiser survival rates (63% / 20%) | the 38 adjudications |
| **anything surviving from the 38** | already retired for two other reasons |

### Mechanical — reproducible by re-running, k=3 not applicable

| figure | |
|---|---|
| end-to-end join 128/886, null 1/886 | executes and re-executes identically |
| era stratification 0% pre-2005, 23% 2015+ | same |
| PubMed corroboration 583/584 | same |
| DataBank recovery 32/34, and 87/87 in-field | same |
| 137 of 220 modern RCTs with no registration | same |
| title-search ceiling 42/128, precision 21/31 | same |
| 3,063/3,171 labels unique in-bibliography | same |

**The three-layer argument rests entirely on the mechanical class.** No part of it depends on
a model judgement, single-draw or otherwise. That is worth stating because it is the material
most likely to be published.

---

## Two traps to avoid if a k=3 panel is ever built here

**Panels being compared must be disjoint.** The site lane's first attempt drew both panels
from the same pool, and pure coin flips scored 62% at k=1 and 77% at k=3 — averaging noise
*appeared* to stabilise it. Disjoint or nothing.

**Only odd panel sizes are comparable.** An even panel can tie, produce no verdict, and drop
silently out of the denominator — excluding precisely the contested cases. Their k=2 scored
99% and would have shipped as a wrong specification. This is the denominator problem in a new
costume, and it is the fourth costume this week.

---

## The caveat, carried verbatim

> **Reproducibility is not accuracy.**

No ground truth exists for these judgements. A consistently wrong panel is exactly as
reproducible as a consistently right one, and k=3 raises reproducibility without touching
accuracy. This matters most for the **med-student verdicts**, which are the judgements this
project has leaned on hardest and which have no external referent at all.

---

## What follows

- No existing model-adjudicated figure is republished without re-running at k=3 against a
  pinned SHA.
- Any figure intended for publication runs k=3 first.
- Re-adjudicating all 643 existing verdicts at k=3 is not proposed; the labelling above is
  what makes the current numbers honest without spending the quota.
