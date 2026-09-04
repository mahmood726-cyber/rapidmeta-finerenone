# What it would take for a search to reach a Path-B object

> ## THIS CANNOT BE A SCRAPER.

> The 13 judgement fields per trial are load-bearing. DAPA-HF's `comparator_type_basis` is
> a sentence explaining that it randomised against placebo **added to background therapy** —
> which is what makes the contrast poolable with EMPEROR-Reduced. **That judgement decides
> inclusion, and no registry field states it.**

> ## AND THE ENUMERATION ROUTE AS CONSTITUTED DOES NOT RAISE `k`.

> `early-rhythm-control-af` was built search-first: **352 trials adjudicated, 264 read by two
> model families, `k_unscreened_remainder: 88`** — the only honest aggregate remainder in the
> corpus — and it ended at **`k=1`**. Someone already ran this properly, at scale, and got one
> trial.

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
   88; `sglt2-hf` has k=4 and a false 0. **The second page is the more misleading one.**

   ⛔ **CORRECTED 2026-09-04, and the correction matters because it was acted on.** An earlier
   revision of this document said *"stage 1 alone fixes that class across 134 objects without
   adding a single trial"*. **That is wrong on both counts.** Measured:

   | category | objects |
   |---|---:|
   | **A** publishes an aggregate remainder AND records sources — fixable from what is there | **17** |
   | **C** records sources but publishes no aggregate — compute and publish it | **1** |
   | **D** neither — cannot have a remainder until a search is executed | **134** |
   | **B** publishes an aggregate with no sources at all | **0** |

   **The 134 do not publish a false zero. They publish nothing at all.** The unproven-remainder
   class lives entirely in the 17. Fixing the 134 is not *record a number*, it is *execute 134
   searches* — the expensive stage, mislabelled as the cheap one.

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

## STAGE 1, SCOPED CONCRETELY — and it is 17 objects, not 134

Measured over every recorded source on Path B: **40 source rows across 18 objects.**

| row state | n | what it needs |
|---|---:|---|
| `RECORDED` — the object states its own remainder | **2** | nothing |
| `COMPUTABLE` — `total` and `returned` both present, remainder follows by subtraction | **30** | derive and write it. Mechanical. |
| `NOT_ASSESSABLE` — **neither a remainder nor a total/returned pair** | **8** | a state, never a zero |

**Only 2 of 40 source rows currently record their remainder.**

### The 8 that must not become proven zeros

This is the `two silences and one honest 1,402` case at scale, and it is the reason stage 1
cannot be a single pass that fills every blank with arithmetic:

```
arni-hfref                                    PubMed
arni-hfref                                    ClinicalTrials.gov API v2
azilsartan-chlorthalidone-vs-olmesartan-hctz  PubMed
bosentan-pah-children                         PubMed
bosentan-pah-combination                      PubMed
bosentan-pah-monotherapy                      PubMed
  (+2 more)
```

For these the object records a search it ran and **does not say how many records it returned**.
A remainder cannot be derived, and a `0` written there would be an invention. They need an
explicit `NOT_RECORDED` — a fourth state beside `RECORDED`, `COMPUTABLE` and the aggregate —
and an object carrying one **must not publish an aggregate remainder at all**, because a sum
containing an unknown is unknown.

> **AN ABSENCE MUST NOT BECOME A PROVEN ZERO. A sum over a silent field is not a smaller sum,
> it is not a sum.**

### The shape of the work

| step | population | cost |
|---|---|---|
| derive and record the remainder on `COMPUTABLE` rows | 30 rows / ~17 objects | **mechanical**, one pass, re-derivable from the object's own numbers |
| mark `NOT_ASSESSABLE` rows `NOT_RECORDED` and suppress the aggregate on their objects | 8 rows / ~6 objects | **mechanical**, but it REMOVES a published number and so needs the before/after page protocol |
| publish the aggregate on the one object that has sources and no aggregate | 1 object | mechanical |
| re-derive each aggregate as the sum of per-source remainders | 17 objects | mechanical; the gate already refuses the ones that disagree |

**Every one of these edits a store object that serves a page**, so each needs the before/after
protocol: served sha256, rendered `k`, every retraction and protected refusal enumerated by
string, then re-asserted after. That is the real cost of stage 1 — not the arithmetic.

### What stage 1 does NOT do

It does not touch the 134. Those publish no remainder because they have no search, and giving
them one is the retrieval stage, not the recording stage. **The false-zero class is 6 objects
serving 2,357 unexamined records; the unproven-remainder class is 17. Neither is 134.**

## What this scope does NOT establish

Not that the 393 trials are wrong, not that any of the 134 objects is missing a specific
trial, and not that stage 1 would change any served estimate. It establishes only where the
work is, and that it is not where this lane spent the night.
