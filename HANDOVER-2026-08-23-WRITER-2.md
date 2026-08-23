# Writer handover — 2026-08-23, second lane

`main` (the Pages deploy ref) is at **`4a3e50aa5`**. Everything below is on
**`fix/ssot-tabbed-shell`**, six commits ahead. **None of it is live.** Verification here is
on committed and built bytes, stated as such rather than implied.

---

## 1. Done, with the commit

| | |
|---|---|
| `48bb02bda` | the 17 "hold nothing" — **premise disproved, nothing retired** |
| `6ef6a091f` | audit table: 97 rows withdrawn into a linked record |
| `d48b4de31` | GRADE: one authority, four states, 7 of 34 → 28 of 34 |
| `57f632eae` | arm roles: 12 arms in 6 trials corrected from the registration |
| `433a3c2d3` | rebuild(5): the corrections reach a reader |
| `e085f55e4` | attr-pn-review/primary withdrawn — borrowed controls |

## 2. The item that was refused, and why

**Retire the 17 objects that hold nothing.** Read by every shape trial-level data takes on
a legacy page rather than by the one the bucket's probe read:

    HOLDS_A_TRIAL_LEDGER                      1
    HOLDS_A_RESULTS_RECORD_KEYED_BY_PMID      1
    HOLDS_IDENTIFIERS_ONLY                   15
    HOLDS_NOTHING                             0

`HFREF_NMA_AUTO_FULL_REVIEW.html` holds nine ledger trials with per-arm counts, PMIDs, DOIs
and one recorded PMID correction. Retiring it would have deleted the best-evidenced network
in the legacy corpus. `scripts/audit_no_review_done_bucket_is_shape_bound_2026_08_23.py`
reproduces this with both controls and a planted defect.

**What is still owed:** a decision on the 15 that identified trials and extracted no
results. "Trials identified, no results extracted" is not "holds nothing", and it is not the
merge-and-absorb case the PCSK9 tombstone style was written for.

## 3. Not started

Items 9–18 of the brief. In order: route the 7 non-`locate()` screening paths · the
single-arm definitional gate · the 101 `protocol v1.0` rows · the 5 `emit_sidecar` refusals ·
and all of Group 3 (v13 gate coverage, the `TEMPLATE_PATH` freeze, the PRISMA-NMA block,
topology disclosure on the 25 networks, the 111 pages claiming an NMA with no network).

**The `TEMPLATE_PATH` freeze is the cheapest and most live of these.** Blast radius 1,314
pages, and it is a refusal, not an analysis.

## 4. Item 8 — read before touching, and the reading changes the item

The brief says comparator has 41 spellings. It has **40**: 29 name-shaped, **11
sentence-shaped**. The sentence-shaped ones are not schema drift — each records a finding
that aliasing would flatten:

- `THE_COMPARATORS_ARE_THREE_DIFFERENT_DRUGS` (apixaban-vte-treatment) — the pooled quantity
  is *"apixaban against WHATEVER ELSE WAS GIVEN"*; GRADE already rates indirectness down and
  the certainty is VERY LOW.
- `a_the_two_trials_differ_in_route_and_duration_not_only_in_comparator` (lefamulin-cabp) —
  *"THE EXPERIMENTAL ARMS ARE NOT THE SAME INTERVENTION"*: LEAP 1 intravenous, LEAP 2 oral.
- `why_experimental_and_comparator_are_added` (ablation-af ×2) — RAFT-AF types **both** arms
  ACTIVE_COMPARATOR, so registry typing carries no information about which side is the
  intervention and the classifier declines to invent one.

And several short keys are **not synonyms**: `comparator_type` holds `active`,
`comparator_kind` holds `randomised concurrent control`, `comparator_class` holds
`ACTIVE -- LMWH/vitamin-K antagonist`. Three vocabularies, three questions.

> **Comparator is not one concept, so it cannot be unified as one.** The other six duplicate
> pairs may still be mechanical; this one is not, and the brief's own instruction to read
> first is what surfaced it.

## 5. Live findings, named, not fixed

- **`SGLT2_HF_REVIEW.html` Table 12** — *"Does the answer depend on the pooling method?"* —
  prints the **withdrawn** summary HR 0.7785 (0.7296 to 0.8306) four more times as a live
  estimator comparison. The object's own `withdrawn_note` describes exactly this in the past
  tense and it is still happening. On the flagship.
- **`portfolio_pools.html` has 50 dead links, `auto-gallery.html` has 5.** The portfolio rows
  are worse in kind than the audit rows this lane fixed: they carry pooled estimates, PI, I²,
  τ² and an HKSJ-floor flag for pages that do not exist.
- **539 `_AUTO_REVIEW.html` root pages were never in the 745-page legacy triage denominator.**
  No page in that class carries a `realData` block, so the payload probe is uninformative for
  all 539. 57 of them hold a non-template NCT somewhere in the file.
- **`pooled.previous_values` is a LIST on some objects and a DICT on others.** Reading it as
  one shape raises `KeyError: 0` on the other.

## 6. Two lessons this lane paid for

**A diff nobody can read is a review nobody can do.** Writing four objects without
`newline=""` turned a five-value change into a 2,452-line diff. Nothing was lost, and that is
not the point: the real change was invisible inside it. Reverted and rewritten preserving the
file's own line ending — 184 insertions.

**A shrink under the threshold is still a question.** The attr-pn withdrawal shrank its
manuscript 4.63%, just under the guard's 5% refusal. The shrink was the withdrawal working.
Reading it anyway surfaced two defects the guard could not have named: a page printing no
withdrawal reason while holding one, and stored drafts still asserting the number that had
just been taken down.

## 7. The gates that refused this lane, and were right each time

- `pre-commit-staging` — three times, until `STAGING_WIDE=1` was set deliberately
- `sweep_mojibake --gate` — two double-encoded em dashes; the source was
  `removed/REMOVED_MANIFEST_SOURCED.md`, repaired there rather than in the quote
- `dashboard_projection_gate` — the dashboard still served an estimate the object had just
  withdrawn. It found the surface I would otherwise have reported as done.
- `lint_withholding_asked` — the withdrawal declined to pool with no evidence any rank below
  the primary was read. Answered by reading all three registrations live, not by supplying a
  string.
