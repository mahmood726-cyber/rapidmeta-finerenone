# Overnight adversarial hunts — 2026-08-25

15 jobs (5 hunts × 3 rounds). **All 15 produced an artefact on the first attempt** — no
silent no-ops, and the byte-verification never had to retry. Every finding below was
re-measured independently before it was believed; where my number and the hunt's disagree,
mine is the one reported and the gap is stated.

## Found, verified, fixed

| Finding | Hunt | Verified radius |
|---|---|---|
| **Screening decisions rendered "included" when the review excluded them** | unenumerated | **695 of 799 records, 3 topics** |
| A gate that cannot see a plain list of strings | gate_blind_spots | 29 pages (10 reader prose, 19 engineering tabs) |
| Dead links on pages the link gate never visits | gate_blind_spots | **102 dead links, 49 pages** |

### The serious one

`ssot/projectors2.py` rendered a screening decision as `disposition`, else `"excluded"` if
`criteria_failed`, else **`"included"`**. Both are the old vocabulary; records written since
store their decision in `verdict`, have neither legacy field, and hit the final `else`.

A page therefore said:

> *"This review's decision: **included**."*
> *"All limbs: Population holds, **comparator fails**, intervention holds, **estimand fails**."*

on a record whose stored verdict is `EXCLUDED`, with its own exclusion reasons directly
beneath. Verified by hand (EARLY_RHYTHM_CONTROL_AF / NCT00184249) before anything changed,
then counted independently: **225 stored EXCLUDED, 383 NEEDS_ADJUDICATION, 71
ELIGIBLE_NO_RESULTS_YET**. Every one errs in the direction that inflates the evidence base.

Fixed to read `verdict` first, keep both legacy shapes, and say *"not recorded on this
record"* where no decision can be read — **a missing field is not a decision**, the same rule
as a SKIP that must not count as a PASS. Seven cases tested.

## Which hunts came back empty, and what that means

**None came back empty.** That is itself worth stating, because the last time these briefs
asked Codex to confirm a known list, every hunt returned nothing. The difference is the
brief, not the corpus.

But two hunts were **blunt in the other direction**, which is the same problem wearing the
opposite face:

- **`identifier_in_prose`** reported 2,119 hits (r1) and 3,508 (r3). Re-measured against
  reader-facing prose only — collapsed disclosures, `<pre>` and `<code>` excluded, since a
  reader meets none of those without choosing to — the truth is **31 pages and 40 distinct
  tokens** (`prisma_flow`, `what_verifies_this_object`, `poolable_reason`). The class is
  real; the count was inflated ~100× by counting the provenance apparatus as prose. **The
  exact error I made yesterday when my extractor flattened a `<details>` and a persona
  desk-rejected a document no reader sees.**
- **`untraceable_number`** and **`false_absence`** returned 1–7 findings per round, each
  needing individual verification. Low yield, but the false-absence class is the one a reader
  cannot detect, so low yield there is worth the cost.

## Standing conclusion

The open brief — *no target, no list, find a category error at a join* — produced the night's
best finding for the **fourth** time. Every hunt aimed at confirming something known has
produced nothing, all week. Brief accordingly.
