# One trial, several topics: the count problem, in our own corpus

**2026-08-19. Volunteered, not asked for.**

This project audits published syntheses for counting one trial more than once inside a single
pool. The structurally analogous fact about **this corpus** is stated here, in the same
document style, before anyone asks — because a standard applied outwards and not inwards is
not a standard.

---

## The measurement

Computed from every object's `inputs.trials[].nct`, not inherited from an earlier run.

| | |
|---|---:|
| objects carrying an included set | 131 |
| objects carrying none | 4 |
| objects unreadable | **0** |
| distinct registration ids across the corpus | **257** |
| ids appearing in **more than one** topic | **51** |
| **share of corpus registration identities that are not exclusive** | **20%** |

| seeded by | ids |
|---|---:|
| 4 topics | 1 |
| 3 topics | 5 |
| 2 topics | 45 |

The ids in three or more topics, in full:

| registration | topics |
|---|---|
| `NCT00262600` | dabigatran-af, dabigatran-stroke, doac-af-review, warfarin-af |
| `NCT01035255` | **arni-hfref**, sacubitril-heartfail, sacubitril-valsartan-hf |
| `NCT01764633` | evolocumab-dyslipidemia-review, pcsk9-inhibitors-cv-review, pcsk9-review |
| `NCT02929329` | omecamtiv-heartfail, omecamtiv-hf, omecamtiv-hfref |
| `NCT03470545` | mavacamten-hcm-review, mavacamten-ohcm, mavacamten-ohcm-review |
| `NCT04652102` | covid19-vaccines, cvncov-covid19, cvncov-sarscov2 |

`NCT01035255` seeds **the flagship**. An earlier record described this as two sacubitril
pages; it is three, and the third is `arni-hfref`.

---

## What this is, and what it is not

**It is not double-counting inside a pool.** No topic includes the same registration twice.
That is the defect this project audits others for, and it is not what this is.

**It is non-independence across topics.** Different questions can properly include the same
trial — `NCT00262600` (RE-LY) genuinely bears on dabigatran in AF, on dabigatran and stroke,
on DOACs as a class, and on warfarin as a comparator. Each inclusion is defensible on its own.

**The consequence is arithmetic, and it is ours to state.** Any corpus-level statement of the
form "this corpus synthesises N trials" that is computed by summing per-topic k **double-counts
51 registrations, one of them four times**. The honest corpus-level number is **257 distinct
registrations**, not the sum of per-topic k.

**And it makes topic-level results correlated.** Two topics sharing a pivotal trial are not two
independent readings of the literature. Anyone reading across topics — a portfolio count, a
"how often do we refuse" rate, a comparison between topics — is reading partly the same
evidence twice.

---

## Why this is published unprompted

The other lane is establishing whether published syntheses mis-key their included sets. When
that lands it will be a criticism of other people's counting. A criticism of counting, made by
a corpus that had not measured its own, is worth less than one made by a corpus that had.

The asymmetry is also the easier failure. Outward findings are sought; inward ones have to be
volunteered, and nothing in the system asks for them.

---

## What is owed next

- **Per-topic disclosure.** Each of the 51 shared registrations should say so *on the topic
  pages that share it*, naming the other topics. Presently the fact exists only in this
  document and in one object's `duplicate_seeding_check`.
- **A corpus-level count that is distinct-by-construction**, so no future summary can be
  produced by summing k.
- **The three-topic clusters read for redundancy.** Three omecamtiv topics over one trial, and
  three mavacamten topics over one trial, may be one topic each rather than three. That is a
  topic-list question, not a synthesis question, and it is open.

---

## A note on which numbers have held

Two figures tonight survived independent recomputation rather than being corrected:

- **`0.7636 (0.7062 to 0.8258)`** — sglt2-hf's published two-component pool, reproduced
  digit-for-digit by a fresh `metafor` run from the stored per-trial estimates.
- **`51`** — the shared-seeding count, recomputed from the objects rather than inherited.

Against a night of corrections, two confirmations is a small number and worth naming as such.
Both are *arithmetic over data that was already right*. Every correction tonight was to a
**reason, an attribution, or an instrument** — not to a stored quantity. That is a pattern:
this corpus's numbers have held better than its explanations of them.
