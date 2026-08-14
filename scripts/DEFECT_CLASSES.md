# Portable defect classes, and the checks that catch them

Written 2026-08-14 from the ARNI flagship pass. Every class here was found on our
own pages first, which is the point: the classes we apply to the published
reviews we audit are the classes we have to survive ourselves, and on the night
this was written ARNI failed four of them.

Each class is stated so it can be applied to **any** review — ours or a published
one — not just to this codebase.

---

## 1. The silently missing row

**Shape.** A derived view shows fewer units than the analysis it sits beside, and
nothing declares the gap. The reader cannot tell the difference between "this
unit was assessed and is fine" and "this unit was never assessed".

**Instances found here.**
- The analysis panels — leave-one-out, cumulative, influence, Baujat, Galbraith,
  funnel, the prediction interval, the tau-squared interval — were the k=3
  analysis under a k=4 headline. Every number was individually correct; they were
  correct about a different pool.
- `count_panels` (RR/OR/RD, L'Abbé, baseline risk, NNT) likewise at k=3.
- The risk-of-bias traffic light drew three trials beside a four-trial forest,
  because RoB-2 ran before the fourth trial was adjudicated in.

**Why it is the most productive class we have.** It never raises an error, every
displayed value is true, and it survives any check that compares numbers to their
own source. It is only visible when you compare a view's *cardinality* against
the analysis it claims to describe.

**Check.** `k_consistency_gate.py`. For each outcome, every block carrying a `k`
and every row-per-trial list must match the number of contributing trials, or
carry an explicit `_STALE`. Extended to TEXTUAL k, because k is written as a word
in a phrase far more often than stored as a number — the numeric half passed
while the title said "the three randomised trials" over a k=4 pool.

**Applying it to a published review.** Count the rows of every forest, funnel and
sensitivity figure and compare against the stated k and the reference list. A
figure with fewer points than the stated study count, with no stated reason, is
this class.

---

## 2. A flow diagram whose arithmetic does not close

**Shape.** A PRISMA-style flow whose stage counts do not reconcile: screened
minus excluded does not equal the number carried forward.

**Instance found here.** Our own PRISMA box said 414 screened. That was the count
*resolved at* title/abstract, not the number screened — 423 entered, 414 were
removed there, 9 went to full text. A reader doing the arithmetic would have
found the diagram short by nine.

**Check.** `prisma_figure()` now **refuses to draw** unless
`screened − removed_at_screening == assessed_at_full_text`. A diagram that cannot
reconcile is replaced with a stated reason, not shipped.

**Applying it to a published review.** This is directly portable and we already
run it: the Reyaz 2023 flow (1,066 → 985 → 28 → 9) closes and is recorded as
CONFIRMED. Check every stage transition, and check the included count against the
number of rows in the characteristics table.

---

## 3. A panel that contradicts itself

**Shape.** Two elements of the same object assert incompatible things. Neither is
wrong in isolation; together they cannot both hold.

**Instances found here.**
- The Discussion said the pooled interval "excludes the null" while the
  Conclusions of the same manuscript said "consistent with no difference" — and
  the interval was 0.746 to 1.018, which contains 1.
- The title said three randomised trials; the contents were four.
- A GOSH panel titled "not computable" whose own reason line began "Computable
  but uninformative".
- `prisma_items.24c` said "three amendments, all post-dating the search" beside an
  array marking two as preceding it.

**Check.** The k gate compares the pooled interval against prose asserting
exclusion of the null. The empty-state renderer now takes an explicit `state`
argument so a panel cannot title itself one thing and explain itself as another.

**Applying it to a published review.** Compare abstract against results against
discussion for each headline quantity, and compare every significance claim
against the interval it refers to. Reyaz 2023 failed exactly this: the Discussion
called all three outcomes significant when the primary all-cause estimate was
RR 0.57 (0.31 to 1.04).

---

## 4. A caption promising an element that is not drawn

**Shape.** A caption tells the reader how to read a figure against a reference —
a diagonal, a null line, contours — that the figure does not contain.

**Instance found here.** The L'Abbé caption said "below the diagonal favours the
intervention". No diagonal was drawn. The funnel caption described a funnel with
no pseudo-confidence contours; the "funnel" was four points in a box.

**Check.** `figure_audit.py` parses each caption for promise words (diagonal,
null/reference line, contour, pseudo-confidence, dashed line) and asserts the
corresponding geometry exists in the rendered SVG.

**Applying it to a published review.** Read the caption, then look at the figure.
This is one of the few classes that needs no data access at all.

---

## THE META-LESSON: a check reading the wrong element cannot fail

This is the fifth instance of the same species in one day, and it is the one that
makes every other check untrustworthy.

The caption check above reported **zero** against the very build whose L'Abbé
caption promised an undrawn diagonal. The selector took the first `<p>` in the
figure card — the downloads block — so every figure's "caption" read
`"⬇ SVG (vector) 2 KB"`. It was not looking at captions at all.

Same shape as:
- a liveness probe querying a model pool the seat never uses, reporting death;
- a `$?` read through a pipe, reporting the exit status of `tail`;
- a holdings table read as an entitlement;
- a mammoth preview that collapses whitespace, making a correctly aligned Word
  file look broken — an instrument understating rather than overstating, which is
  the same fault.

**Rule.** Before recording a check as passed, state what a failure would have
looked like on that instrument, then produce one. A check that has never been
seen to fail has not been tested; it has been run.

**Corollary — degenerate input is not a clean result.** `figure_audit.py` now
REFUSES on pages whose chart containers measure 0×0: their geometry is all zeros,
so a collision check would pass by measuring nothing. Refusing is the correct
output; "0 collisions" would have been a lie.

**Corollary — an exemption that holds by accident stops holding.** The k gate
skipped the comparison section and the R blocks only as a side effect of a
bare-noun rule. They are now excluded deliberately, with the reason, because the
accident would have ended the moment someone wrote "nine included trials" there.

---

## Applicability of the checks in this directory

| Check | SSOT pages | Corpus pages (Plotly) | Published reviews |
|---|---|---|---|
| `k_consistency_gate.py` (numeric + textual) | yes | yes — reads the object, not the page | portable by hand |
| `alignment_gate.py` (docx ↔ page ↔ docmodel) | yes | n/a — no docmodel | n/a |
| `figure_audit.py` (series, axes, captions) | yes | **REFUSES** — 0×0 geometry | by eye |
| PRISMA arithmetic closure | yes | not yet wired | portable by hand |
| RoB row completeness | yes | not yet wired | portable by hand |

**Scope correction, measured not assumed.** The two shared-projector bugs fixed on
ARNI — the shifted `scatter_svg` argument tuple and the contourless funnel — do
**not** affect the 1,217 built corpus pages. Those pages render figures with a
local Plotly bundle (`vendor/plotly-2.27.0.min.js`) into `.chart-container` divs,
a completely different implementation. Measured: 0 of 1,217 carry the shifted
aria-label signature, and 0 carry a server-side funnel at all. The bugs are real
for every page built by `ssot/projectors.py` — currently 12 SSOT objects — and
ARNI is the only one rebuilt so far.
