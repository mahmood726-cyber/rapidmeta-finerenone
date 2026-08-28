# Two declared surfaces

A proposal for the generator, with the case for each measured rather than argued.

Both requirements share a shape: **a page should be able to state about itself what we
currently recover by forensics.** Neither is proposed because it enables a check. Each is
proposed because a night was spent establishing, from outside, something the page could have
declared in one attribute.

---

## 0. THE ROOT BENEATH BOTH — found by the store-side lane

**Only 31 of 144 pages declare their object's identity in their served bytes. 138 of 144
declare the generator that built them.**

> **The corpus records how a page was made and not what it is about.**

That single asymmetry is why both requirements below were necessary and why the census was
forensic rather than a lookup. The fix is one line: **emit the store path beside the build
stamp that is already being written.** It is strictly smaller than either requirement below,
it comes first, and it makes both of them cheaper — `data-artefact` because a page that names
its store has already answered "review or tool", and `data-pool` because the pool ids it must
carry are the store's own.

---

## 1. `data-artefact` — what kind of thing is this page?

```html
<html data-artefact="review">      <!-- a synthesis presenting results -->
<html data-artefact="tool">        <!-- an application a reader operates -->
<html data-artefact="redirect">    <!-- a notice pointing at the canonical page -->
<html data-artefact="landing">     <!-- an index, dashboard or gallery -->
```

### What it cost not to have it

The served corpus is **1,463 root pages**. Establishing what they are took a full census, a
structural-signature classifier, a live sampling check, a cross-lane join, and 58 pages opened
one at a time. The answer:

| kind | pages | share |
|---|---|---|
| unpopulated application shells | 744 | 50.9% |
| redirect / withdrawal notices | 506 | 34.6% |
| attributed reviews | 141 | 9.6% |
| current-generation without a store | 14 | 1.0% |
| needed opening by hand | 58 | 4.0% |

**Every one of those numbers is a `grep -c 'data-artefact="…"'` if the attribute exists.**

### The three questions it answers at once

1. **Retired or live.** Nothing in the delivered bytes distinguishes a legacy page that is the
   sole coverage of its subject from one whose successor exists. It took a store-side
   classification joined to a served-side census to say that **510 pages are LIVE_SOLE** and
   **282 are ORPHAN_NO_ROUTE**.
2. **Tool or review.** 744 pages present the full apparatus of a systematic review — PRISMA,
   GRADE, AMSTAR-2, RoB-2 tables — with `--` in every result slot, at URLs ending
   `_REVIEW.html`. They are applications awaiting a run. **A reader is invited to run them and
   the URL says they are invited to believe them.**
3. **Stub classification.** 506 redirect notices were identified only by matching phrases like
   *"Moved, not removed"* in their prose.

### The number that makes it urgent

Of the **510 pages that are the only coverage of their subject**, **488 (95.7%) are
unpopulated shells**. Across **760 distinct subjects, 13 have at least one populated page and
727 appear covered and are not.**

**That 727 is stable across two different versions of the store-side classification** — it did
not move when `SUPERSEDED` went 55 → 5 and `HAS_STORE` went 94 → 166. A figure that survives a
substantial change in one of its inputs is measuring the corpus rather than a boundary.

---

## 2. `data-pool` — which pool does this number come from?

```html
<span data-pool="hfcv_total">11,806 participants</span>
<td data-pool="hfcv_first">k = 2</td>
```

On every reader-facing number derived from a pool: the visual-abstract N and trial count, the
index-card `k`, the published-comparison `k`, and each forest-plot row.

### Three checks it converts from unbuildable to mechanical

| class | status today |
|---|---|
| a denominator that survived the withdrawal of the analysis it described | **not buildable** |
| `k` conflated between review-level and outcome-specific counts | **not buildable** |
| three-surface set equality (table = forest = computation) | **not buildable** |

All three fail for one reason: **no page emits a link between a stated number and the pool it
came from.**

### What was tried instead, and what it cost

Three-surface equality was attempted twice and neither shipped.

1. Matching a plot to a pool **by label overlap** assigned every plot to pool 0 and then
   reported the mismatch it had itself created.
2. Matching **by document position** collapsed every plot onto the nearest table, which on a
   multi-pool page is the last one.

The obstacle is not the matching rule. Forest plots key rows on a trial short name
(`soloist-whf`) on some pages and a registration id (`NCT02540993`) on others, while
contributing-table cells carry the trial name followed by explanatory prose (`CONFIRM-HF the
trial's own primary …`). No normalisation reconciles them without guessing.

**The price of guessing is measured.** `direction_label` shipped as a proxy and was retired at
**precision 0 of 2** — both corpus failures were false positives, and *the second was caused by
the patch for the first*: a passing mention of a different trial's win ratio, 2,500 characters
away in the discussion, flipped a polarity override on a page whose outcome was
"Cardiovascular death or hospitalization for heart failure", where lower genuinely is better.

**A specified surface beats a tuned detector. This is the third time tonight that held.**

### It is genuinely unmet

Checked before proposing it again: across all 141 attributed pages there is exactly **one**
`data-*` attribute in use — `data-fw="fit"`, a formatting hook, 240 occurrences. **Zero pages
carry an attribute whose value equals an outcome id.** 64 pages produce a substring match and
all 64 are coincidental.

---

## 3. A third, for cross-lane artefacts

Not a page attribute, but the same class one layer up.

> **An artefact consumed by another lane must declare what produced it and when.**

An intersection computed at 02:07 rested on two JSON files another lane replaced at 02:17.
`SUPERSEDED` went **55 → 5**, `HAS_STORE` **94 → 166**, the legacy population **860 → 797** —
and nothing warned, because the files carry no version of their own. The figures had already
been relayed.

This is the build stamp's argument at the level of intermediate data: **an artefact that cannot
say what it is can only be trusted by the process that made it.** `intersect.py` now stamps
every input with size, sha256 and mtime and prints them above its result. The producing side
should stamp too, so the consumer does not have to.

---

## Sequencing

`data-artefact` first. It is one attribute at the top of every page, it needs no per-number
plumbing, and it retires an entire class of forensic work. `data-pool` second, because it
touches every rendered figure. Both belong on `REQUIRED_GENERATOR_COMMITS` once landed, beside
`c5409eaa1`.

---

## A `<script>` block is not page content

Two independent lanes produced a headline finding from one unstripped tag on the same night:

- **here** — "six DTA reviews carry genuine results". The matches were template source:
  `'+pct(pooled`, `"+fmtNum(qSpec`, `'+chip+'`.
- **the store-side lane** — "870 pages publish adverse claims about other people's trials",
  which nearly bought a mass deletion. Also strings inside `<script>` that render nowhere.

**Any instrument that reads served bytes must strip `<script>` and `<style>` bodies and HTML
comments before counting anything.** Stripping tags alone leaves JavaScript in the text.

### And the second cause, which the first fix hides

Stripping `<script>` here **did not move the count**. The pattern still matched narrative
prose — *"Sensitivity ~96-100%"* — while the result table beneath read an em dash.

**A defect can have two independent causes that each look like the whole cause. Fixing one
leaves the number unchanged, which reads as confirmation.** That is nastier than either bug
alone, and the only defence is to hand-check the survivors rather than trust the pass.

The verdict now requires both: **a value WITH AN INTERVAL, and NO EMPTY RESULT SLOT.** A page
can carry a real interval in its narrative while its own result table reads `-`, and the `-`
is what a reader meets where the answer belongs. The reader's position is the vantage.

### A number with a known one-sided error is worth more than one that happens to be right

Across three revisions of the instrument and three revisions of the other lane's input, the
hollow-subject count moved 727 -> 727 -> **733**. It only ever rose, because both bugs moved
pages OUT of the hollow column and never into it. **That is why it stayed quotable while
every figure around it changed.**
