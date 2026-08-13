# ANSWER-HF: prepared change set — NOT APPLIED

**Status: waiting on the search lane's formal adjudication.** Nothing in this
file has been written to the canonical object. Every number must be read from the
lane's adjudication record, not from the message that announced it — the message
is a summary and a summary is not a source.

This document exists so that when the adjudication lands the change is mechanical
rather than archaeological. The audit below is real: it is every field in the
object that currently asserts k=3, a lower bound, or "three trials".

---

## 1. What changes, and why it is not just a number

k goes 3 → 4, **and it stops being a lower bound**. Those are two separate
changes and the second is the one that is easy to miss. `k_status.is_lower_bound`
is true *because* ANSWER-HF was undetermined behind a paywall. Resolve ANSWER-HF
and the stated reason for the lower bound is gone — so leaving `is_lower_bound`
true would be as wrong as leaving k at 3, and it would be wrong in a way that
looks conservative rather than stale.

The remaining undetermined record must be re-checked: if another row is still
undetermined the bound stands for a *different* reason and must say so.

## 2. Object fields to change (audited, 33 sites)

**Counts**
- `results.by_outcome.<oid>.k` : 3 → 4
- `secondary_pools.outcomes[0..2].k` : 3 → 4 each
- `outcomes_considered.registered_primary.k` : 3 → 4
- `outcomes_considered.secondary_now_pooled[0..2].k` : 3 → 4

**The lower-bound claim**
- `results.by_outcome.<oid>.k_status.is_lower_bound` : true → false *only if* no
  other record remains undetermined
- `k_status.why` : rewrite. The current text names ANSWER-HF as the reason.

**Screening**
- the ANSWER-HF corpus row: `decision` undetermined → include
- **keep the prior state visible.** Add an adjudication block naming the previous
  decision, the evidence, the route, and the UTC date. Overwriting it would erase
  the row's history, and the history is part of what this page demonstrates.
- `reconciliation.trial_list_diffs[0].theirs_not_ours[6]` : the "NOT decided …
  could not be retrieved" reason is now false and must be superseded, not deleted.
- `claims_corrected[0]` already records "ANSWER-HF to be resolved"; it closes.

**Manuscript prose that says "three" in words, not tokens**
- `introduction[2]` "Two later randomised comparisons" → three
- `introduction[3]` "A meta-analysis of three trials"
- `results_prose[1]` "The three trials differ in ways that matter"
- `limitations[1]` "The count of eligible trials is a lower bound"
- `discussion[2]`, `discussion[3]`, `conclusions` — all reason about a
  three-trial structure where one trial dominates
- `outcomes_considered.considered_and_not_pooled[3].why` "across the three trials"
- Paper Studio methods sentence carries "(a LOWER BOUND, not a settled count)"

These are prose, so they do **not** update from the token substitution. They are
the sites most likely to be left stale, because every numeral around them will
change automatically and look correct.

## 3. Numbers to store — from the adjudication, once confirmed

Per-arm counts on the **randomised** denominators, 95 and 95, for all four
outcomes. The trial's *primary* endpoint used a modified ITT of **87 per group**
excluding patients who died. Store that distinction explicitly so nobody later
picks 87 up for our composite — a denominator that differs by outcome inside one
trial is exactly the shape that produces a wrong weight silently.

The registered estimand is the composite of CV death and HF hospitalisation.

## 4. Everything that must be recomputed, not edited

The pooled estimate, tau², I², Q, the leave-one-out set, the estimator
comparison, the forest plot, the count panels, and all three secondary pools —
each in R with metafor at build time, as before. **Nothing may be edited by hand.**

Expect the pooled estimate to move materially and heterogeneity to rise: this is
the first contributing trial whose point estimate sits well above the null, so
the leave-one-out story and the GRADE inconsistency domain both need re-reading
rather than re-labelling.

## 5. Gates

- **Cross-family certification** is required: this is a number-changing rebuild.
- **The regression guard should PASS**, because adding a trial is an addition.
  Watch it anyway. Every derived value is recomputed, and a recomputation that
  silently drops a cell would look exactly like a legitimate addition in the
  aggregate counts. The value-level check added on 2026-08-13 is what would catch
  it; before that change it would not have.
- Content floor, unexplained numerals, download-equals-render, D14/D15 all re-run.

## 6. Access ledger — the counter-example

Every open route returned closed on this row: no DOI resolution, no PubMed full
text, no Crossref match, no preprint. It was resolved by **institutional access**
(Royal Free London).

This is the **one confirmed case in the programme where a paywall was the binding
constraint**. It is worth recording precisely because the argument has run the
other way all week: repeatedly, rows that looked paywalled turned out to be
retrievable by a route we had not tried, and the honest generalisation was that
"paywalled" usually meant "not yet looked for properly". That generalisation now
has a documented exception, and one real exception is worth more than the
impression it corrects — it stops the rule hardening into a dogma that would have
us stop looking.
