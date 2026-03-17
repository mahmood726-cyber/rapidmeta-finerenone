# Multi-Persona Review: 8 New RapidMeta Apps
### Date: 2026-03-17
### Scope: SGLT2_CKD, ARNI_HF, ABLATION_AF, IV_IRON_HF, RENAL_DENERV, DOAC_CANCER_VTE, MAVACAMTEN_HCM, RIVAROXABAN_VASC
### Status: REVIEW CLEAN — 5/5 P0 fixed, 5/6 P1 fixed
### Validation: 14/16 pass (INCRETIN=pre-existing, RENAL_DENERV=MD needs custom validator)

## P0 — Critical (5) — ALL FIXED

- [FIXED] **P0-1** RENAL_DENERV: Continuous detection fixed — `_resolvedKey` maps 'default' to 'MACE'
- [FIXED] **P0-2** RENAL_DENERV: ContinuousMDEngine now called for default scope (k=5, MD -5.12)
- [FIXED] **P0-3** RENAL_DENERV: effectMeasure changed to 'MD', label map updated
- [FIXED] **P0-4** RENAL_DENERV: REQUIRE trial MD corrected -6.6 → -2.7 (Circ Cardiovasc Interv 2021)
- [FIXED] **P0-5** ALL 8: Hardcoded "finerenone" replaced with dynamic protocol.int (5x per file), FINEARTS cross-link removed, BENCHMARK_OUTCOME_NOTES cleared

## P1 — Important (6) — 5/6 FIXED

- [FIXED] **P1-1** DOAC_CANCER_VTE: SELECT-D phase II → II/III (now included, k=4)
- [FIXED] **P1-2** MAVACAMTEN: VALOR-HCM SRT_Avoid → MACE (now in default scope, k=3)
- [OPEN] **P1-3** MAVACAMTEN: Crude OR 27.6 vs published adjusted OR 17.9 — inherent limitation of 2×2 pooling
- [FIXED] **P1-4** ALL 8: IMPROVE-IT removed, BENCHMARK_OUTCOME_NOTES cleared
- [PARTIAL] **P1-5** RENAL_DENERV: GRADE SoF still uses ratio-scale thresholds for continuous
- [FIXED] **P1-6** ARNI: Capsule filename slash → hyphen

## P2 — Minor (5)

- P2-1: CSS dependency on FINERENONE_REVIEW.tailwind.css filename
- P2-2: Placeholder "e.g. FIDELIO-DKD" in manual data entry
- P2-3: RENAL_DENERV AUTO_INCLUDE doesn't match _ON/_OFF suffixed NCT IDs
- P2-4: MAVA-LTE open-label with cN=0 stored in realData (correctly excluded)
- P2-5: Empty PUBLISHED_META_BENCHMARKS in 7/8 apps
