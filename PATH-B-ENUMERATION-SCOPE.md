# What it would take for a search to reach a Path-B object

**Scope only. Nothing built.** Every number MEASURED at `cbf3233c` against the tree, with the
command that re-derives it named.

## First, the finding that reframes the whole lane

| | brief | Path B measured |
|---|---:|---:|
| trials | 398 | **393** |
| topics | 135 | **152** |
| topics with k ≤ 5 | 125 of 135 | **143 of 152** |

> **The `398 / 135` that opened this lane was a PATH-B figure.** The cap, the ledger, the
> 1,453 discarded candidates and the 5 resurrected topics are all Path A. The pages the
> number described were never on that path.

Path B, measured over the 152 distinct objects behind 163 PAGE_MAP entries:

```
WITH an executed search    objects  18   trials  71   mean k 3.9   with 0 trials   0
WITHOUT one                objects 134   trials 322   mean k 2.4   with 0 trials  18
                                   ---          ---
                                   152          393   median k 2
largest: colchicine-periprocedural(26), colchicine-stroke-prevention(9), alirocumab-lipid(8)
```

## The bottleneck is NOT the search

There is one precedent for building a Path-B object search-first:
`scripts/create_rhythm_control_object_2026_08_19.py` for `early-rhythm-control-af`. It
adjudicated **352 trials**, had two model families read 264 of them, refused to treat a
single-seat reading as a verdict, and published `k_unscreened_remainder: 88` — **the only
non-zero aggregate remainder in the corpus, and the only object that got that right.**

It ended with **1 trial** in `inputs.trials`.

> **A search reaching a Path-B object produced a documented cascade, an honest remainder, and
> one pooled trial. The search was never the constraint.**

## What the constraint is: 29 fields per trial

One entry in `inputs.trials` (`sglt2-hf`, DAPA-HF) carries **29 fields**. Split by what could
produce them:

**Machine-derivable from AACT / the registry — 16**
`nct` · `enrolled` · `registration_brief_title` · `registration_org_study_id` ·
`registration_enrolment` · `registration_arm_count` · `registration_primary_counts` ·
`registration_other_outcome_counts` · `registered_primaries` · `registered_secondaries` ·
`registered_other_outcomes` · `registered_primary_timeframe` · and four `*_read_utc` stamps.

**Requiring a document or a judgement — 13**
`id` · `name` · `pmid` · `year` · `design` · `population` · `comparator_type` ·
`comparator_type_basis` · `arms` (per-arm event counts) · `arms_not_used` · `enrolment_note` ·
`by_outcome` (point and interval) · `registered_primary_timeframe_basis`

The `_basis` fields are the load-bearing ones and they are the reason this cannot be a
scraper: `comparator_type_basis` on DAPA-HF is a sentence explaining that the trial randomised
against a matching placebo **added to background therapy**, which is what makes the contrast
poolable with EMPEROR-Reduced. That judgement decides inclusion, and no registry field states
it.

## So the work, in four stages, and only the first is cheap

| stage | what it needs | cost |
|---|---|---|
| **1. search** | an executed-search record per object, in the `evidence/**` schema that already exists and that `verify_search_record_reconciles.py` already reads | **cheap** — the emitter is built and landed; 134 objects need one |
| **2. screen** | a disposition per candidate with a named reason, and the three states (`INCLUDED`/`EXCLUDED`/`UNDECIDABLE`) rather than two | **moderate** — `screening_states.py` exists and is wired; needs per-object criteria |
| **3. extract** | the 16 machine-derivable fields per included trial | **moderate, automatable** |
| **4. adjudicate** | the 13 judgement fields, above all `arms[].events` and the `_basis` sentences | **the constraint** |

**Stage 4 is where `early-rhythm-control-af` stopped at 1 of 352**, and it is where any
widening of Path B will stop too unless something changes about how per-arm counts and
comparator judgements are obtained.

## Three things worth deciding before any of it is built

1. **Is raising Path-B `k` the goal, or is publishing the remainder the goal?** They are
   different, and the second is far cheaper. `early-rhythm-control-af` has k=1 and an honest
   88; `sglt2-hf` has k=4 and a false 0. **The second page is the more misleading one**, and
   stage 1 alone fixes that class across 134 objects without adding a single trial.

2. **The overlapping-population rule must exist before records arrive, not after.** A pooled
   programme paper covering two trials (Babinchak 2005) must never enter as one study, and a
   regional subset of trials already included (Fomin 2008) must never enter as a fourth. An
   unbounded pass surfaces exactly this class. Not built; named here so it is not discovered
   at stage 4.

3. **`CLAIMED_INACCESSIBLE` largely already exists** on Path B as
   `eligible_but_not_contributing`, carrying `reason_no_data`, `what_would_be_needed` and an
   explicit `arithmetic_deliberately_not_done`. The gap is narrower than "laundered": **the
   FDA label is not among the sources checked.** That is a source to add, not a state to
   invent.

## What this scope does NOT establish

Not that the 393 trials are wrong, not that any of the 134 objects is missing a specific
trial, and not that stage 1 would change any served estimate. It establishes only where the
work is, and that it is not where this lane spent the night.
