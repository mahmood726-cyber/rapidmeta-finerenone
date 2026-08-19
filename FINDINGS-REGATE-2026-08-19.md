# Re-gating the five completed topics against the repaired classifier

**Every number below was recomputed, not inherited.** The old classifier was loaded from git
rather than reimplemented from its commit message; every surfaced set was re-executed from the
object's own recorded query; pagination was checked rather than assumed.

Commit `e20f94068` repaired `topic_identity.locate()` for the trailing placebo convention and
said, in its own message, what had not been done:

> no INCLUDED trial of any of the five gated topics changed role — checked, not assumed. Their
> CASCADE COUNTS may move where a changed registration was in their surfaced set… **To be
> re-run and re-gated with old and new side by side, not silently.**

This is that re-run.

---

## The headline

**Four of five cascades moved. No included trial of any topic changed role, so no pooled
estimate moves because of the classifier.** What moved is the denominator each page reports
its search against — and on two pages, a `k_unscreened_remainder: 0` that had stopped being
true.

| topic | k0 | k2 located | k3 exp | k4 comp | k5 bkgd | kNA | movers |
|---|---:|---|---|---|---|---|---:|
| **alirocumab-lipid** | 99 | 99 → **97** | 87 → **89** | 5 | 6 → **3** | 1 → **2** | 3 |
| **sglt2-hf** | 56 | 56 | 46 → **49** | 2 → **1** | 8 → **6** | 0 | 3 |
| **bempedoic-acid-review** | 21 | 21 | 16 | 3 → **5** | 2 → **0** | 0 | 2 |
| **iv-iron-hf** | 47 | 47 → **43** | 34 | 6 | 5 → **3** | 2 → **4** | 2 |
| attr-cm-review | 55 | 55 → **52** | 48 | 3 | 1 | 3 | **0** |

`k0` is identical to the stored value on all five, so **none of the delta is registry drift**.

`attr-cm-review`'s zero is recorded as a measured null. On a finished page, *unchanged* and
*not checked* look the same.

---

## Six defect classes, five of them new

### 1. A restatement block is a claim about a moment, and it ages silently

`sglt2-hf`'s stored cascade **did not reproduce** under the classifier of its own era. Run
across four revisions:

```
b65d892de   36 12  8  0    no
f2bf16022   46  2  8  0    YES -- the revision the page was built to
c5b98b329   48  2  6  0    no
e20f94068   49  1  6  0    no
```

Reproducing at exactly one revision and no other identifies **a missed re-run, not changed
data**. Two later classifier commits shipped the same night and were never carried back to a
page that had already been gated.

> **What made it look current is that it carried a correction note.** The object holds a
> `restated_2026_08_19_placebo_discriminator` block naming its own 36 → 46 delta, dated the
> same day as the two commits that superseded it. The presence of a restatement is evidence
> that someone once looked — not that anyone looked last.

The same sentence in `SGLT2_PRISMA` has now said **43, then 36, then 46, and now 49**. Each was
true when written. The fix is not another correct number: it is that the number is now
**produced by a command** (`scripts/regate_cascade_2026_08_19.py`) and **refused by a gate**
when it stops reconciling.

### 2. The stage named "role located" was counting the records it could not locate

`k2_role_located` is defined by the instrument that produced it as `experimental + comparator +
background`. Three objects stored `k0` there instead:

| | k2 stored | k3+k4+k5 | kNA |
|---|---:|---:|---:|
| alirocumab-lipid | 99 | 98 | 1 |
| attr-cm-review | 55 | 52 | 3 |
| iv-iron-hf | 47 | 45 | 2 |

`kNA` was counted twice — once as itself, once inside the count that says it was resolved. The
direction is the familiar one: it makes the instrument look exhaustive.

> **And it is invisible on exactly the objects that cannot expose it.** `bempedoic` and `sglt2`
> both carry `kNA = 0`, so the two quantities coincide and the field reads correct. **A sum
> that is right whenever the thing it omits is zero has not been tested.**

Closed by `scripts/lint_cascade_arithmetic.py`, limb A. Exit 1 on all three; exit 0 now.

### 3. A block scoped out as "about other work" is where a field named `ours` hides

`alirocumab-lipid` was restated to k=8 and MD −54.82. Its published-comparison block was not:

```
published_comparison.divergence_decomposed.ours
    "Mean difference -54.66 percent (-60.75 to -48.56) ... k=6, random effects,
     DerSimonian-Laird. PREDICTION INTERVAL -74.1 to -35.2, which is the number to quote."
```

A gated page stating two different estimates for its own review, with the superseded one in
the table a reader consults to compare us against the literature — P7, which must agree
between the page and the Word manuscript, and agreed with neither.

`lint_block_contradicts_object.py` is silent on it **by construction**: it scopes
`published_comparison` out entirely as a FOREIGN_SUBJECT, because that block describes other
people's reviews and reading *"reports no pooled estimate of its own"* as a claim about this
object was one of its two false-alarm families.

> **That exclusion was right about the block and wrong about one field inside it. The scope-out
> is at block level; the first person is at field level.**

Closed by `scripts/lint_ours_matches_pool.py`, which decides the subject from the **key**
(`ours`, `our_*`, `this_review`) and never from parsing a sentence — so it is not the removed
prose check returning. It found five failing limbs on the shipped object, including three
`our -54.66` / `our -54.7` in running prose.

**Two false alarms were fixed rather than baselined.** `incretin-hfpef-review` carries a
first-person field whose content is an **NCT-id list**, and `NCT04847557` was read as a quoted
number. A field can be first-person and not be a numeric claim.

### 4. A promotion applied to the headline and not to the derived blocks

The k=6 → k=8 recovery moved the headline and `results.by_outcome`. It did not move:

- `prisma_flow.included` — still 6, with six NCTs, against `inputs.trials`' eight
- `k_cascade.k_included_in_object` — still 6
- `prediction_interval` — **−74.08 to −35.23, computed over six trials, and its own text calls
  it "THIS IS THE NUMBER TO QUOTE"**
- `estimator_sensitivity` — three estimator rows computed "on exactly these six values"
- `recovery_2026_08_19.not_done_and_named` — still stating the two trials were *not* promoted

All recomputed by `scripts/recompute_alirocumab_k8.py`, which refuses to emit anything derived
unless the stored k=8 headline first reproduces from the object's own per-trial values, and
checks its REML against metafor's result already stored on the object.

| | k=6 | k=8 |
|---|---|---|
| prediction interval | −74.08 to −35.23 (t₅) | **−72.77 to −36.87** (t₇) |
| DL | τ² 47.42, I² 87.9 | τ² 50.04, I² 88.0 |
| REML | τ² 71.22, I² 91.6 | τ² 61.44, **I² 90.0** |
| REML + HKSJ | −64.13 to −44.53 | **−62.06 to −47.38** |

**The prediction interval narrowed by 3.0 points while τ² went up.** Almost all of the
narrowing is the t multiplier falling from 2.5706 to 2.3646 as the degrees of freedom rise.
Reporting only the narrowing would suggest the evidence became more consistent when it did not.

**And I² landed on the threshold rather than across it.** 90.0 under REML at k=8 against 91.6
at k=6. This project treats 90 per cent as the point at which an average conceals more than it
conveys, so the recovery moved this *toward* poolability — the opposite direction from the one
that would flatter a decision already taken, which is why it is stated.

**A second finding fell out of that recompute:** the I² column of a sensitivity table is
metafor's `τ²/(τ²+s²)`, **not** Higgins's `(Q−df)/Q`. Higgins is computed from Q, which uses
fixed-effect weights, so it *cannot move between estimators* — it reads 88.0 for every row.
**A sensitivity column that cannot move is not a sensitivity column.** The stored k=6 rows
(87.9 / 91.6 / 91.6) could only have come from metafor's definition; that is now named on the
block instead of assumed.

### 5. False provenance on the field whose only job is provenance

`sglt2-hf`'s `k_cascade.source` cited `evidence/2026-08-19-batch1/cascade.json`. **sglt2-hf is
not in that file** — that run covered eight other topics. `iv-iron-hf` is absent from the same
file and carries no `source` key at all, which is a gap rather than a wrong citation.

Now cited as **scripts that re-derive the numbers** rather than a file that once held them, so
the citation stays true when the classifier next changes.

### 6. A round trip through a parser is not a copy

Two instances in one session, both in instruments rather than objects:

- The k=8 reproduction gate failed at first because SEs were re-derived from per-trial CIs
  **rounded to 2 dp for display**. Reading a quantity back out of its own printed form and
  calling it the input made a correct computation look unreproducible. Fixed by rebuilding the
  recovered contrasts from the posted LS means, with a check that each rebuild matches the
  object's stored display before it is used.
- `prove_regate_guards.py` restored a planted object by re-serialising a parsed copy. The
  restore "succeeded" while leaving the tree in a state neither the builder nor git had
  produced, and took one builder run to converge back. Fixed to snapshot raw bytes.

---

## Two newly-unscreened trials on each of two gated pages

Both pages carried `k_unscreened_remainder: 0`. It was true when written and the classifier
repair made it false, with nothing on either page changing.

**alirocumab-lipid** — remainder 81, dispositions now 34 / 21 / 26 / 0.

| trial | verdict | ground |
|---|---|---|
| NCT01812707 | ELIGIBLE_NOT_POOLABLE | Population, intervention and comparator all hold (atorvastatin is in every arm, so it is background). **Every registered rank — the primary and all six secondaries — is at WEEK 12**, and this object's estimand is week 24. Not an exclusion: right quantity, wrong time. |
| NCT03004001 | EXCLUDED | POPULATION: conditions are `['Nephrotic Syndrome']`; the dyslipidaemia is secondary to renal disease. The estimand limb **also** fails and is named rather than relied on. It is TERMINATED at n=3, which would settle it on status alone — deliberately *not* the stated ground, because that would hide that this population was never in scope. |

`NCT03067844` moved background → **NOT_ASSESSABLE** and so is not in the remainder at all: its
`PLACEBO_COMPARATOR` arm labelled 'Placebo' carries `Drug: Alirocumab` and declares no placebo
record. A refusal is not an exclusion.

**sglt2-hf** — remainder 45, reconciled across four passes (32 two-axis + 1 native + 10
three-state + 2 re-gate).

| trial | verdict | ground |
|---|---|---|
| NCT06434025 | ELIGIBLE_NO_RESULTS_YET | Eligible, and it takes reading the *arms* to see it: FCM + dapagliflozin against FCM + placebo-of-dapagliflozin, so FCM is background and the contrast is the SGLT2 inhibitor. NOT_YET_RECRUITING. Recorded now: its primary is LVEF by CMR at 30 days and neither secondary is a time-to-event, so **it will not pool however it reports**. |
| NCT07025629 | EXCLUDED | POPULATION: enrolment is patients ready for ICU discharge after ≥24 h of ventilation or vasopressors, entering on `NT-proBNP > 800 **and/or** eGFR 25–90` — a participant can qualify on the renal threshold alone with no heart-failure diagnosis. Its registered condition string contains the words "Heart Failure"; **deciding this from the condition string alone would have admitted it.** |

`NCT04157751` (EMPULSE) also moved into the experimental set but is already screened in the
object's native records. Three moved, two were new — checked rather than assumed.

---

## What was proved about the guards themselves

`scripts/prove_regate_guards.py`, all three parts of P16, planting **the real shipped defects
read out of git `21e9cfcf3`** rather than a fixture:

1. **It can fire** — 2 failing limbs from `lint_ours_matches_pool`, 1 from
   `lint_cascade_arithmetic`.
2. **It is silent on the correct case** — 0 alarms on the corrected object.
3. **Neither is established by the build reporting success** — planted on disk, the builder
   printed `HELD 8 / REFUSING 0 of 8` and exited 0 **while the guard exited 1**.

The planted object is restored from a raw-byte snapshot and the restore is verified by md5;
the script fails rather than leaving the tree modified.

### And a defect in a guard, found by writing to it

`lint_subprocess_decode.py` counted **a comment saying `text=True` as a site**. Two of its
eighteen baselined entries are exactly that — prose describing the hazard. They had been
absorbed into the baseline rather than recognised, and the ratchet then made every future
comment about the rule cost a refusal.

> **A lint that counts its own documentation as a violation taxes writing the rule down.**

The AST was already being walked for the safe case; asking it which lines carry a real keyword
removed the class. Baseline 18 → 16, and the five real hazards this session introduced were
fixed rather than baselined.

---

## Verified in served bytes

`scripts/verify_served_bytes_2026_08_19.py` — HTTP fetch from a local server, `md5(served) ==
md5(disk)`, **and** a content check whose expected strings are projected from each object's own
`build_stamp` P2 sentence and pooled points rather than typed into the script.

**The content check earned itself on the first run.** `SGLT2_HF_REVIEW.html` returned
`md5 served == disk: OK` and both pooled points present — and was **stale**, because its
pooled estimates did not change and only the cascade sentence did.

> **A stale file matches its own disk copy perfectly.** A hash proves the wire agrees with the
> disk. It says nothing about whether the disk agrees with the object.

---

## Not done, and named

- **`bococizumab-lipid-review`** carries a 150-character truncated research question and needs
  a decision packet, not a build. Untouched.
- **`ablation-af-review`** and **`apixaban-vte`** remain BLOCKED on user decisions. `apixaban-vte`
  is registered in the builder without `primary_outcome_key`, so the builder mechanically
  refuses it. Verified still refusing.
- **The 41-object `arms_as_registered` schema drift** is unfixed and deliberately so: the two
  keys are two vocabularies and a literal map would import the exact defect `locate()` exists
  to fix. It would restate 41 topics at once and deserves its own pass.
- **The 58-object "question is the object's own verdict" shape** has a named detector that is
  not built.
- **The positive-property contamination detector** with 18 uninspected alarms is untriaged.
  Not wired, and not baselined.
- **`figs/*.html`** are alirocumab's figures overwritten into what were sglt2's slots — one
  shared slot per figure, which is the supersede-chain rule failing at the figure layer. Left
  uncommitted rather than enshrined.
- **The staging guard's declared set omits the two directories every build commit must touch.**
  `.githooks/pre-commit-staging` allows `ssot/`, `scripts/`, `.githooks/` and top-level
  `.md/.json/.txt/.yml`. It refuses top-level `.html` — the built pages, which are the
  project's output — and `evidence/**`, where every verifier writes. So a commit that ships a
  page *cannot* pass without `STAGING_WIDE=1`.

  > **An override that fires on every legitimate commit is an override that stops being read.**
  > The guard exists to stop `git add -A`; it is currently also stopping the normal case, which
  > trains the exact reflex it was built to prevent.

  Every file in this commit was staged by name, so the override was used as designed. The
  declared set is **not** widened here: what belongs in it is a judgement about what this
  repository ships, and that should be a visible decision rather than a side effect of one
  session needing to get past it.
- **`PAGE_MAP.json`** maps `alirocumab-lipid` to `ALIROCUMAB_LIPID_AUTO_FULL_REVIEW.html`,
  which is a pre-standard page last built 2026-08-17. The page the completion commit shipped,
  and the one rebuilt and verified here, is `ALIROCUMAB_LIPID_SSOT.html`. **The map names a
  file that is not the built page**, and that is recorded rather than quietly repointed.
