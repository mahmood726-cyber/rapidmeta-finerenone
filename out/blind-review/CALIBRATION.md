# Blinded external-review harness — calibration against the three external reviews

Harness `bh-2026-08-27-disclosure-aware`. Run 2026-08-27, live pages fetched from
`https://mahmood726-cyber.github.io/rapidmeta-finerenone/` (GitHub Pages, source = `main`, path `/`).

## Provenance of what was reviewed

| topic | bytes | HTTP Last-Modified | sha256 (served bytes, first 12) | pools |
|---|---|---|---|---|
| SOTAGLIFLOZIN_HF | 3,587,327 | Wed, 26 Aug 2026 22:59:36 GMT | `ce806fea0e6d` | 3 |
| IV_IRON_HF | 7,262,859 | Wed, 26 Aug 2026 22:59:36 GMT | `4a83a23122d4` | 6 |
| INCRETIN_HFpEF | 1,464,073 | Wed, 26 Aug 2026 22:59:37 GMT | `c9df7818c4ef` | 2 |

Every verdict below is anchored to those exact bytes. The corpus was rebuilt by another lane
*during* this session, so an unanchored verdict would already be stale.

## Scoreboard against the external reviews' findings

| # | External-review finding | Harness verdict | Status |
|---|---|---|---|
| 1 | Pooled estimates independently recompute and reproduce | 6 of 6 assessable pools reproduce exactly | **CONFIRMS** |
| 2 | KCCQ axis said "lower is better" on a higher-is-better scale | fires on the pre-fix blob, clean on the live page | **CAUGHT — already fixed** |
| 3 | "HKSJ" labels a modified / t-safeguarded interval | detected on 6 of 6 pools, but **downgraded** | **CAUGHT, overstated by the review** |
| 4 | A denominator that survived withdrawal of its own analysis | no detector built | **MISS** |
| 5 | Three sources called unavailable whose full text is open | needs open-source lookup — LLM lane, not built | **MISS** |
| 6 | "Four trials versus our two" — k conflated across outcome levels | no detector built | **MISS** |
| 7 | Recurrent-event totals vs first-event times as one estimand | no detector built | **MISS** |

**Caught 3 of 7 (one materially downgraded). Missed 4.**

### On finding 2 — caught, but already fixed
Commit `463c6d625` (2026-08-26) — *"fix(render): KCCQ forest plot said 'lower is better' on a
0-100 scale"*. The defect was real; it was fixed after the review and before this run. Scoring
this as a detector miss would have been wrong, and scoring it as a detector hit on the live page
would also have been wrong. Both blobs are pinned as an immutable fixture pair.

### On finding 3 — the review overstated it, and so did I initially
The displayed "HKSJ" interval is the **q-floored** variant (`q = max(1, Q/(k-1))`), not raw
Knapp-Hartung. On sotagliflozin pool 0 the page shows `0.2928–1.7560`; raw HKSJ is `0.3986–1.2901`.

But the page **does** disclose it, in its methods prose: *"The Hartung-Knapp-Sidik-Jonkman interval
is reported beside it with the floor on its scale factor applied, so it can widen and can never come
out narrower than the ordinary one."*

So this is **not** a fabricated method label. It is a surface-consistency defect: the qualifier does
not travel with the number — the results-table row reads as unmodified HKSJ. The harness now emits
`QUALIFIED` for disclosed flooring and `FAIL` for undisclosed flooring.

## What the harness found beyond the reviews

All within the rubric's named classes.

| topic | finding | severity |
|---|---|---|
| IV_IRON_HF | Trial name renders as `?` with an **empty** ClinicalTrials.gov link and an em dash — 204 `?`, 24 empty links | reader-facing falsehood |
| SOTAGLIFLOZIN_HF | RoB 2 "No information" used as a **domain judgement** in 29 cells, with "Agreed: yes" recorded on it | reader-facing falsehood |
| IV_IRON_HF | same, 38 cells | reader-facing falsehood |
| SOTAGLIFLOZIN_HF | 3 NCT labels link to an FDA PDF / PubMed, not ClinicalTrials.gov | identifier does not link to what it identifies |
| IV_IRON_HF | 1 NCT label links to PubMed | same |
| INCRETIN_HFpEF | contributing table shows `not stated (not stated to not stated)` for every trial; "Source of this cell" renders as a bare `:` | promised surface is empty |
| IV_IRON_HF | RoB table lacks the result/outcome column | RoB 2 is per-result |

## Denominators

- Topics examined **3**; fetched OK **3/3**; FETCH-FAIL **0**.
- Pools **11**. Judgements **51**: PASS 21, FAIL 7, QUALIFIED 6, NOT-ASSESSABLE 17.
- NOT-ASSESSABLE is reported as its own state and is never counted as PASS. 5 of the 17 are pools
  with k=1 or no displayed summary; the incretin ones are NOT-ASSESSABLE *because* the page
  displays no per-trial inputs — which is itself a finding, reported separately.

## Instrument error rate — measured, and not yet good enough

Two false positives were produced by my own checks and caught by hand-verification, not by the
harness:

1. **`direction_label` on a hierarchical win ratio.** The page states *"values above one favour
   treatment — the opposite of every other ratio in this object."* "Higher is better" was correct;
   my nearest-keyword rule saw "death"/"hospitalisations" in the hierarchy description. Fixed with a
   measure-level override; the pinned control still fires, so the fix did not over-suppress.
2. **`method_label` severity.** Reported as a fabricated label before checking whether the page
   discloses the flooring. It does.

Both were in the direction of *accusing the page*. That is the dangerous direction: a check that is
wrong toward "the subject is defective" reads as the harness working.

**The classifier-style checks (`direction_label`) have no measured error rate against a hand-labelled
sample. Until they do, their corpus-wide counts are reach figures, not defect rates.**

## Proof that the checks work in both directions

`test_bh.py`, 30 tests:
- every check PASSES on a clean synthetic fixture and FAILS on one carrying its own defect;
- planting one defect does not trip any unrelated check (specificity);
- a degeneracy guard asserts raw and floored HKSJ actually differ, so the planted defect is plantable;
- the real-world pinned pair (`463c6d625` ± 1) must FAIL pre-fix and PASS post-fix.

Mutation-tested: forcing `method_label` to always PASS, forcing `falsy_render` to always FAIL, and
widening the arithmetic tolerance to 99 each turn the suite red. The gate can fail.

Fixtures are synthetic or pinned to immutable git blobs, and are built in memory — no control writes
to a shared output path.
