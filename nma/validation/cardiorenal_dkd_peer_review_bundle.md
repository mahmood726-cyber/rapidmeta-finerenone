# Modern Cardiorenal Therapies in CKD (±T2D) NMA — Peer-Review Defence Bundle

**Generated:** 2026-04-22 · **Version:** v1.0 (k=6, Pbo-star, HR scale)
**Engine:** `netmeta` R package v3.2.0
**App:** `CARDIORENAL_DKD_NMA_REVIEW.html`
**Outcome:** Trial-specific primary composite kidney endpoint (eGFR decline + ESKD + renal/CV death).
**Educational focus:** Six landmark post-2019 cardiorenal trials across three drug classes — the new CKD standard-of-care.

---

## 1. Network

| Trial | NCT | Drug / Class | Year | Primary composite |
|---|---|---|---|---|
| CREDENCE | NCT02065791 | Canagliflozin (SGLT2i) | 2019 | ESKD + doubling creatinine + renal/CV death |
| FIDELIO-DKD | NCT02540993 | Finerenone (nsMRA) | 2020 | Kidney failure + ≥40% eGFR decline + renal death |
| DAPA-CKD | NCT03036150 | Dapagliflozin (SGLT2i) | 2020 | ≥50% eGFR decline + ESKD + renal/CV death |
| FIGARO-DKD | NCT02545049 | Finerenone (nsMRA) | 2021 | Kidney composite (pre-specified secondary) |
| EMPA-KIDNEY | NCT03594110 | Empagliflozin (SGLT2i) | 2022 | Kidney disease progression + CV death |
| FLOW | NCT03819153 | Semaglutide (GLP-1 RA) | 2024 | Kidney failure + ≥50% eGFR decline + renal/CV death |

**Geometry:** Placebo-star. k=6 trials / 5 drugs. Finerenone has 2 pivotal trials (FIDELIO + FIGARO).

---

## 2. Results (RE, REML, HKSJ)

τ² = 0.000, I² = 0% — class-consistent.

| Drug | HR vs Pbo | 95% CI |
|---|---:|---:|
| **Dapagliflozin** | **0.61** | (0.51, 0.73) |
| Canagliflozin | 0.70 | (0.59, 0.83) |
| Empagliflozin | 0.72 | (0.64, 0.82) |
| Semaglutide | 0.76 | (0.66, 0.88) |
| Finerenone (pooled) | 0.84 | (0.77, 0.92) |
| Placebo | 1.00 | — |

**SGLT2i class dominates the renal-composite outcome.** Dapagliflozin leads numerically but CIs overlap substantially with Canagliflozin and Empagliflozin. Semaglutide's FLOW result (first GLP-1 dedicated renal trial) places GLP-1 RA in the mix at class-competitive effect size. Finerenone shows a smaller relative effect — consistent with its distinct mechanism (mineralocorticoid receptor antagonism vs glucose-transport/hormonal).

---

## 3. Transitivity

| Modifier | Concern |
|---|---|
| **Composite definition** | **Serious** — eGFR-decline threshold varies (≥40% FIDELIO vs ≥50% DAPA/FLOW); FIDELIO/EMPA-KIDNEY include CV death, FIGARO has kidney as secondary. Drug ordering robust to definition but absolute effect sizes should not be compared directly across trials. |
| Background therapy | Low — all trials required ACEi or ARB at maximal tolerated dose. |
| Population | Moderate — CREDENCE + FIDELIO + FIGARO + FLOW required T2D; DAPA-CKD + EMPA-KIDNEY included non-diabetic CKD. SGLT2i benefit shown equivalently in T2D and non-T2D subgroups. |
| Baseline eGFR | Moderate — ranges 25–90 mL/min across trials. |
| Albuminuria | Moderate — FIDELIO required UACR ≥30; DAPA-CKD ≥200; EMPA-KIDNEY broader including normoalbuminuric. |

---

## 4. CINeMA

| Contrast | Certainty |
|---|---|
| Any drug vs Placebo (direct) | **HIGH** |
| Any drug vs Any drug (indirect via Placebo) | **MODERATE** — composite-definition transitivity concern |

---

## 5. Changelog

- **v1.0** (2026-04-22) — First release. Educational synthesis of the 6 landmark post-2019 cardiorenal RCTs. Key teaching point: SGLT2i class provides the largest relative renal-composite effect; GLP-1 RA and finerenone add complementary benefit via distinct mechanisms; modern CKD care increasingly uses pillar combinations (SGLT2i + RAAS blocker + finerenone ± GLP-1 RA).
