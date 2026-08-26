# Import verification gate — v1

**Frozen 2026-08-26, BEFORE any comparison was run.** Thresholds written first so that
whatever comes back cannot be reasoned into acceptability afterwards. That is the same
trap as calibrating a control after seeing the result.

## What is being verified

For a sample of tier-A rows, does the estimate we would import from
`AACT 2026-04-12 outcome_analyses` match what the trial's **publication** reports?

## The gate CLASSIFIES; it does not flag mismatches

Divergence is expected. A registry-posted analysis and a published primary legitimately
differ — different analysis populations (ITT vs per-protocol vs modified ITT), different
censoring, different data cut-off dates, different adjustment. A gate built to flag
mismatches would return a large number that means nothing.

Every compared pair lands in exactly one class:

| class | meaning | verdict |
|---|---|---|
| **S1 same quantity, same value** | same outcome, same population, values agree within rounding | fine |
| **S2 same quantity, different value** | same outcome and population, values disagree | **ALARMING** |
| **S3 different quantity** | different outcome, population, timepoint or analysis set — the two numbers are answers to different questions | fine, but must be RECORDED so the imported row states which quantity it is |

Only **S2** indicates the registry value is unreliable as an import source. S3 is the
normal case and its handling requirement is labelling, not rejection.

## Pre-registered stopping thresholds

Sample: **20 tier-A trials**, drawn at a seed recorded before drawing, spread across
cardio and ID and across param types.

- **S2 ≥ 3 of 20 (15%) → STOP.** Do not import tier A. The registry value cannot be
  quoted verbatim if it disagrees with the publication on the same quantity at that rate.
- **S2 = 1 or 2 of 20 → IMPORT ONLY WITH PER-ROW PUBLICATION CHECK.** Each tier-A row
  must be reconciled against its publication before it lands.
- **S2 = 0 of 20 → IMPORT TIER A**, with every row carrying its S1/S3 class and, for S3,
  the quantity distinction stated on the row.
- **Unresolvable ≥ 8 of 20 (40%)** — publication not retrievable, or the comparison
  cannot be made — **→ STOP and report the sample as NOT_ASSESSABLE.** A gate that
  cannot see most of its sample has not measured anything. This is not a pass.

## Tier B is NOT covered by this gate

Tier B derives estimates from arm counts. Its failure mode is arithmetic and arm
misassignment, not divergence from a publication. It needs its own check: recompute a
sample by hand and confirm the arm identities. **Tier B does not import on the strength
of a tier-A result.**

## What a pass does not license

A pass licenses importing the tier-A *values*. It does not license pooling them —
whether two imported estimates are the same quantity is the commensurability judgement
the corpus makes, and the screen found candidate shared outcomes in only 9 of 80 topics.

## Refusal to self-certify

Nothing here is closed by me. Mahmood closes.
