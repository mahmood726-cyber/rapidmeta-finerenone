# Rebuilding the served corpus — a staged proposal

**Status: proposal only. Nothing in this document has been executed against a served tree.**
Eight rebuilds were made to scratch paths; no served page has been written.

---

## Why the corpus must be rebuilt at all

This is not housekeeping. **123 served pages are missing `f90a8cabe`**, the generator fix that
stops publishing one assessor's judgements as the review's finding. On the topic that exposed
it, *the two assessors agreed on zero of four results and no adjudication existed in the
store*. That defect is currently served on 123 pages, and until they are rebuilt the fix
exists and reaches nobody.

The same rebuild also carries `36ae41332` (per-outcome participant counts, withdrawn-state
fallthrough) and today's three declared surfaces.

---

## The corpus is five build vintages, not one

Measured by reading `Generator build <code>SHA</code>` out of all 163 served pages
(`scripts/stamp_census_2026_08_27.py`, `outputs/stamp_census_2026_08_27.json`):

| sha | pages | committed | what it was |
|---|---|---|---|
| `2c0cf3bf0` | 123 | 08-25 11:15 | undecidable as a third state on the page |
| `f90a8cabe` | 22 | 08-26 17:29 | do not publish one assessor's judgements as the review's |
| `36ae41332` | 2 | 08-27 01:16 | per-outcome counts, withdrawn-state fallthrough |
| `fa7ef6686` | 1 | 08-25 08:59 | ARNI manuscript defects |
| `948cec5ef` | 1 | 08-26 22:56 | no-information is not a domain judgement |
| **UNSTAMPED** | **14** | — | carries no reproducibility block |

Two further pages — `ARNI_HF_REVIEW` and `SOTAGLIFLOZIN_HF_REVIEW` — are stamped **from a
dirty tree**: the sha names a real commit that does not contain the code that built them.

---

## Four populations, ordered by how many causes a difference could have

This is the axis the plan rests on — not size, not risk. **A diff is only actionable if it
can be attributed.**

| # | population | pages | a difference means |
|---|---|---|---|
| **A** | `f90a8cabe` + `36ae41332` + `948cec5ef`, objects unmoved | **25** | the generator only — one cause |
| **B** | `2c0cf3bf0`, objects unmoved | **24** | the generator only, two days of it |
| **C** | `2c0cf3bf0` / `fa7ef6686`, **objects also moved** | **100** | the generator **and** the store — two causes |
| **D** | UNSTAMPED | **14** | nothing — no vintage to diff against |

**Order: A → B → C → D.** A is nearest to HEAD with a single varying factor. D is last because
it has no baseline at all.

### Batch sizes

| population | batches | why |
|---|---|---|
| A | 25 in one | three of them already rebuilt identically in testing |
| B | **5, then 19** | the first batch confirms the two-day gap is additive beyond the one page tested |
| C | **3, then 8, then 89** | the batch of three is diagnostic, not productive |
| D | **1, then 13** | the first establishes what an unstamped page even produces |

---

## Verification per batch

**Never a byte gate.** Rasterisation is non-deterministic: `ssot/figures.py` rasterises via
Chrome per figure and returns `None` on failure by design. Measured, rasters vary in
**dimensions and file size**, not merely in presence — a same-vintage rebuild of
`ACS_ANTIPLATELET_REVIEW` differed only in TIFF size (25,576 KB → 14,370 KB), EPS size
(3 KB → 4 KB) and raster dimensions (4500x1940 → 4500x1090).

1. **Rendered text**, with `<script>` stripped first, normalised for dates, the stamp,
   `SHA-256`, `NN KB` and `NNNNxNNNN`. The last two exist because **the page prints numbers
   about files and numbers about trials in the same document**, and a naive "did any number
   change?" gate flags a TIFF's size as though it were an estimate.
2. **Captioned-figure count** (`Figure N.`) unchanged — *not* `base64,` count, which counts
   payloads rather than figures.
3. **Deletes = 0.** The vintage gap has been additive on every page tested (4 inserts,
   0 deletes). A delete is the stop signal, not a diagnosis.
4. **All nine required ancestors satisfied.** The build refuses otherwise
   (`ssot/do_not_rebuild.py::check_generator_pin`), and that refusal has been proven to fire.
5. **Population C only: build each page twice** — once from its own vintage generator with the
   *current* object, once from HEAD. The first attributes a change to the store, the second to
   the generator. This makes a two-cause diff single-cause **by construction rather than by
   argument**.

---

## If a batch goes wrong, in this order

1. **Delete or insert?** Inserts are catch-up; deletes are damage. This is the stop signal.
2. **Did the object move?** From C's two-build split.
3. **Captioned-figure count.** A lost caption is real; a lost raster is the known
   non-determinism.
4. **Does a same-vintage rebuild reproduce the served page?** Isolates generator from store.
5. **Only then read the diff text.**

---

## What is established, and on which population

Three properties hold, all demonstrated on `ACS_ANTIPLATELET_REVIEW`:

- **Today's three surfaces are reader-invisible.** `e7194e3b4` → HEAD, same worktree, same
  object: **1 rendered-word change region** (the stamp), rendered characters 55,959 → 55,959,
  **+114 bytes**, figures 5 → 5, `data-store`/`data-artefact`/`data-pool` 0/0/0 → 1/1/1.
- **A same-vintage rebuild reproduces served content** — 7 differences, all export metadata.
- **The vintage gap is additive** — 4 inserts, 0 deletes.

**And the caveat that governs the plan: ACS is in population B.** Only 24 of the 123 pages on
`2c0cf3bf0` have objects identical to HEAD; **99 have moved**. Every property above was
established on the easy 20%. **Population C is 100 pages where none of them is tested**, which
is exactly why its first batch is three pages and diagnostic.

---

## Excluded from early batches

`ARNI_HF_REVIEW` and `SOTAGLIFLOZIN_HF_REVIEW`, both served from a dirty tree. One is the
topic a methodological criticism is being prepared about.

---

## Method notes worth carrying

- **Only the isolation run was clean by design.** The vintage-baseline comparison varied the
  generator *and* the object, since each worktree carries its own — it happened not to matter
  because the ACS object is byte-identical across both, checked rather than assumed. The
  result was safe by luck, not by construction.
- **`build()` is not the entry point.** `python ssot/build_tabbed.py <object> <out>` is.
  Calling `build()` directly bypasses five guards installed at the write site: the
  do-not-rebuild list, the generator pin, the raster setup, the placeholder-leak refusal and
  the manuscript guard. A page built that way loses every rasterised figure and still looks
  structurally correct.
