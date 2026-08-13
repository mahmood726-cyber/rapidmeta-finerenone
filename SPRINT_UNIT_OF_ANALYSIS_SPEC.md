# SPRINT unit-of-analysis repair — specification (PREPARED, NOT APPLIED)

Target: `e156-submission/assets/INTENSIVE_BP_REVIEW.html`
Status: blocked on one sourced input (see §4). Number-affecting -> cross-family gate required.

## 1. Evidence, read from the file

| Line | Record | Counts | Effect | Source |
|---|---|---|---|---|
| 1790 | `NCT01206062` parent | **none — registry metadata only** | — | NEJM PMID:26551272 |
| 2191 | `NCT01206062_SENIOR` | tE 102 / tN 1317, cE 148 / cN 1319 | HR 0.66 (0.51–0.85) | JAMA 2016;315:2673-2682 |
| 2201 | `NCT01206062_CKD` | tE 112 / tN 1330, cE 131 / cN 1316 | HR 0.81 (0.63–1.05) | JASN 2017;28:2812-2823 |
| 12579 | pool `no_dm` "Without Diabetes" | contains **both** splits | | |
| 12585 | pool `elderly` ">=65/75y" | `_SENIOR` | | |
| 12586 | pool `general` "General/Middle-age" | `_CKD` | | |

Found by grep during a repair-spec run, not by a detector. D-35 remains unproven and
was not used to reach this; the finding stands on the lines above.

## 2. The defect, which differs by pool

- `no_dm`: two rows from ONE randomisation in ONE pooled estimate. Direct double-counting.
- `elderly` vs `general`: contrasted strata must be disjoint at participant level. `_CKD`
  is defined by eGFR, not age; it spans all ages and necessarily contains participants
  >=75 who are simultaneously counted in `elderly` via `_SENIOR`. Neither pool is
  internally double-counted — the CONTRAST between them is what is invalid.

## 3. Invariants

1. Within one pooled estimate, at most one row per randomisation.
2. Strata that are contrasted must be mutually exclusive at participant level.

## 4. Edits

1. `no_dm` — remove both splits; insert a single parent SPRINT row.
   SPRINT excluded diabetes trial-wide, so the whole randomisation satisfies the pool
   criterion. **BLOCKING: the parent's four arm counts are not on the page** (line 1790
   is metadata only). They must be read from the NEJM primary report and enter the
   ledger as an addition with provenance. Not applicable until sourced.
2. `general` — remove `_CKD`. **Relocate, do not delete** (see §5).
3. `elderly` — `_SENIOR` stays. Once `_CKD` leaves `general`, the randomisation appears
   once in that analysis.

Net: SPRINT appears once in the diabetes-status analysis (whole trial) and once in the
age analysis (>=75 subgroup). Different analyses, one row each, no pool holds it twice.

## 5. Amendment after adversarial review (laptop leg, GPT-5)

My first specification said to drop `_CKD` from `general` with no replacement. That is
wrong in a way worth recording: it restores disjointness by discarding real evidence.
A published CKD-subgroup result with its own counts and effect is data, and deleting it
to fix a classification error trades one defect for another.

Corrected: `_CKD` moves to a CKD-specific stratum or sensitivity analysis. The age strata
become disjoint because `_CKD` is no longer in one of them, and the evidence survives
where it actually belongs.

The same review confirmed the parent row is only valid if it is genuinely the
non-diabetes population sourced from the primary report — the registry-only row at
L1790 cannot be used as evidence as-is. That is already §4.1's blocking condition.

## 6. Overlap magnitude

SENIOR ∩ CKD is NOT derivable from this page or from published marginals. It requires
IPD or a published cross-tabulation. Recorded as a required input; NOT estimated.

## 7. Detector status arising from this

- **D-34 form (b) — RETIRED.** It inferred shared-control double-counting by comparing
  summed arm N against `enrollment_count`. `enrollment_count` is the REGISTERED TARGET,
  not randomised N (COAPT registers 776, randomises 614), so the premise is false and the
  rule yields both false positives and false negatives as a function of recruitment.
  Replaceable only by actual randomised/analysed N from source publications.
- **D-35 — unproven, narrow scope only.** Suffix-keyed matching cannot separate the three
  shapes that share the syntax: overlapping subgroups (`_SENIOR`/`_CKD`), disjoint platform
  arms on a shared control (`NCT04381936c/d/e`, which is D-34 not D-35), and genuinely
  separate registrations. Any numeric rule must key on shared/near-identical control
  denominators, and even then cannot prove disjointness for SPRINT. Not usable until it
  fires on a known-bad, stays silent on a known-good near-miss, and clears a
  hand-adjudicated precision audit.
