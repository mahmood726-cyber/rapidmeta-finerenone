# vendor/prisma-flow.js — corpus-wide PRISMA fix, held back from the HFrEF release

**Status:** NOT applied on this branch. Exported for the Phase 1 engine patch.
**Patch:** `outputs/prisma-flow-vendor-fix.diff` (136 insertions, 33 deletions)
**Date held back:** 2026-07-30

## Why this is not in the HFrEF branch

`vendor/prisma-flow.js` is loaded by **1011 apps** in this repo. The fix below is
correct and worth shipping, but shipping it *through an HFrEF release* would change
1011 unrelated apps as a side effect of a single-topic push. It is therefore
reverted out of `rebuild/hfref-nma-on-main-2026-07-30`, which now touches only
HFrEF files, and is queued for the corpus-wide gated rollout instead.

The HFrEF page still renders a correct PRISMA flow. It does so **without** this
patch, by driving tab 2 from the app's own inline `PrismaEngine` — the same engine
tabs 6/7 use. See the `HFrEF-SCOPED PRISMA RECONCILIATION` block at the end of
`HFREF_NMA_AUTO_FULL_REVIEW.html`.

## Applying it

```
git apply outputs/prisma-flow-vendor-fix.diff
```

Verified: `origin/main`'s `vendor/prisma-flow.js` + this patch is byte-identical
to the fixed file (13,265 bytes) after newline normalisation.

## What the patch fixes

**1. Pre-hydration paint reported 0 for every upstream stage.**
The module rendered on `DOMContentLoaded`, before `RapidMeta.state.trials` was
populated, and reported `0` identified / `0` screened. Zero is a *claim* — that no
records were found — not an absence of data. A `hydrated` gate now returns `null`
for every unknown stage, which renders as "not recorded".

**2. The retry guard disabled itself.**
```js
if (total_search === 0 && in_nma === 0 && attempts < 10)   // never true
```
`realData` is embedded and non-empty from the first paint, so `in_nma` was already
non-zero and the `&&` short-circuited. The retry loop never executed once; the
diagram was painted pre-hydration and frozen. It now retries on `!hydrated`.

**3. A fallback fabricated the lower boxes.**
```js
if (total_search === 0 && in_nma > 0) { fulltext = included = in_nma; }
```
This is what turned an *empty* diagram into an *impossible* one — on HFrEF it
produced `0 identified / 0 screened / 28 full-text`. Removed.

**4. The caption claimed live re-rendering that never happened.**
Nothing subscribed to state changes. Adds a signature-based watcher and
`PrismaFlow.refresh()`.

**5. Records with no screening decision vanished.**
`identified − screened` silently disappeared between stages. They now get their own
arm, and PRISMA-2020 semantics are adopted for "Records screened" (records that
*entered* screening), so the label no longer means two different things on two
surfaces of the same app.

## Known open issue this patch does NOT resolve

The tab-2 vs tab-6 **"excluded after full-text"** disagreement. A record that is
include-flagged but carries no extraction data is booked by `prisma-flow.js` as
`excluded_fulltext` (an exclusion decision that was never actually recorded),
while the inline `PrismaEngine` books the same record as "included but awaiting
data / not in the fitted network — reason not recorded".

`PrismaEngine`'s framing is the honest one: no full-text exclusion decision exists
for that record. Before this patch goes corpus-wide, `prisma-flow.js` should stop
classifying missing-extraction as full-text-exclusion and adopt an
"awaiting data" arm instead. Because that changes a *published count* on every one
of the 1011 apps, it needs its own review — it is not folded in here.

On HFrEF this disagreement is already structurally gone: both surfaces are rendered
from one engine, so they agree by construction rather than by coincidence.
