# ADC NMA in HER2+ MBC 2L+ PFS — Peer-Review Defence Bundle

**Generated:** 2026-04-21 · **Version:** v1.1 (k=4, closed-loop, HR scale)
**Engine:** `netmeta` R package v3.2.0
**App:** `ADC_HER2_NMA_REVIEW.html`
**Scope (explicit):** HER2-positive metastatic breast cancer, 2L / 3L+ setting, PFS outcome. **Excludes** adjuvant (KATHERINE — different outcome, iDFS) and HER2-low (DESTINY-Breast04 — different disease).

---

## 0. What v1.1 changes

**v1.0 → v1.1**: Added DESTINY-Breast02 (T-DXd vs TPC in HER2+ MBC 3L+ post-T-DM1, Andre 2023 Lancet; HR 0.36 [0.28, 0.45]). This creates a **closed T-DXd–T-DM1–TPC triangle** (via DESTINY-Breast03 + TH3RESA + DESTINY-Breast02), enabling the first design-by-treatment consistency test in this network.

**Key new finding: Q_inc = 11.9 (df = 1, p < 0.001) — statistically significant inconsistency detected.**

This is an honest-reporting outcome. Adding DESTINY-Breast02 moved the network from a transitivity-assumed tree to a loop-tested triangle, and the loop test **failed**. Diagnosis:

- **TH3RESA's TPC** = investigator-choice single-agent chemotherapy ± trastuzumab, 3L+ with no prior T-DM1 requirement
- **DESTINY-Breast02's TPC** = trastuzumab + capecitabine OR lapatinib + capecitabine, 3L+ post-T-DM1 specifically

These two TPC definitions are clinically distinct comparators grouped under the same node label. The apparent T-DXd-vs-TPC indirect effect via T-DM1 (0.33 × 0.528 ≈ 0.174) is ~2× stronger than the direct effect from DESTINY-Breast02 (0.36) — the TPC definition is the driver.

**v1.2 roadmap:** Split TPC into `TPC_chemo_TH3RESA` and `TPC_H_plus_chemo_DB02` as separate nodes. This will restore transitivity but remove the closed loop (network reverts to a tree of 4 edges across 5 nodes). Trade-off is acknowledged and pre-specified.

---

## 1. Network (v1.1)

| Trial | NCT | Comparison | N | Setting |
|---|---|---|---|---|
| DESTINY-Breast03 | NCT03529110 | T-DXd vs T-DM1 | 524 | 2L HER2+ MBC |
| EMILIA | NCT00829166 | T-DM1 vs Lapatinib + Capecitabine | 991 | 2L HER2+ MBC |
| TH3RESA | NCT01419197 | T-DM1 vs TPC (single-agent chemo ± trast) | 602 | 3L+ HER2+ MBC |
| DESTINY-Breast02 | NCT03523585 | T-DXd vs TPC (trast+cape or lapa+cape) | 608 | 3L+ HER2+ MBC, post-T-DM1 |

**Geometry:** Closed triangle T-DXd–T-DM1–TPC (via DESTINY-Breast03 + TH3RESA + DESTINY-Breast02) with LapaCape as a T-DM1 pendant (via EMILIA).

---

## 2. Consistency + heterogeneity (v1.1)

| Test | Result |
|---|---|
| τ² (REML) | **0.161** |
| I² | **91.6%** [wide CI] |
| Q_heterogeneity | modest |
| **Q_inconsistency** | **11.91, df = 1, p < 0.001 — INCONSISTENT** |
| Node-splitting T-DXd–TPC | direct (DESTINY-Breast02) vs indirect (DESTINY-Breast03 × TH3RESA) differ by exp(0.73) ≈ 2× |

**Interpretation:** The closed loop test fails because the "TPC" node is a composite — TH3RESA's TPC and DESTINY-Breast02's TPC are not interchangeable. The Q_inc value is a real signal, not a statistical artefact.

---

## 3. Treatment effects (random-effects, REML, HKSJ)

Reference = TPC (the composite). **These v1.1 estimates are honest reflections of the inconsistency-inflated τ² — wider than v1.0's, and LapaCape/T-DM1 now have CIs that cross the null.** This is the correct behaviour when τ² is high. A clean tree (v1.2 with split-TPC) will yield narrower CIs but at the cost of losing the closed-loop test.

| Treatment | HR vs TPC | 95% CI |
|---|---:|---:|
| **T-DXd** | **0.283** | (0.145, 0.553) |
| T-DM1 | 0.671 | (0.344, 1.310) |
| LapaCape | 1.032 | (0.363, 2.937) |
| TPC (composite) | 1.00 | — |

**Re-expressed direct contrasts (head-to-head evidence; unchanged from v1.0):**

| Contrast | HR | 95% CI | Evidence |
|---|---:|---:|---|
| T-DXd vs T-DM1 | 0.33 | (0.26, 0.43) | Direct DESTINY-Breast03 |
| T-DM1 vs LapaCape | 0.65 | (0.55, 0.77) | Direct EMILIA |
| T-DM1 vs TPC_TH3RESA | 0.528 | (0.42, 0.66) | Direct TH3RESA |
| T-DXd vs TPC_DB02 | 0.36 | (0.28, 0.45) | Direct DESTINY-Breast02 |

For clinical decision-making, prefer the **direct** head-to-heads over the network-synthesised indirect estimates until v1.2 resolves the TPC composite.

---

## 4. Ranking (v1.1)

| Treatment | P-score | SUCRA | rank-1 probability |
|---|---:|---:|---:|
| **T-DXd** | **0.995** | 0.995 | **98.6%** |
| T-DM1 | 0.579 | 0.579 | 0.5% |
| TPC | 0.232 | 0.232 | 0.9% |
| LapaCape | 0.194 | 0.194 | 0.0% |

T-DXd remains rank-1 with near-certainty (98.6%) despite the inconsistency — its direct evidence vs both T-DM1 (HR 0.33) and TPC (HR 0.36) independently place it at the top. The ranking is robust to the TPC definition issue.

---

## 5. Transitivity (v1.1 — strengthened)

| Effect modifier | Concern |
|---|---|
| **TPC definition** | **SERIOUS** — composite of two distinct regimens (single-agent chemo ± trastuzumab in TH3RESA vs dual-agent trast/lapa + capecitabine in DESTINY-Breast02). **This is the inconsistency driver.** |
| Line of therapy | Moderate — 2L (EMILIA, DESTINY-Breast03) vs 3L+ (TH3RESA, DESTINY-Breast02). |
| PFS assessment | Low — BICR in 3 of 4; investigator in TH3RESA. |
| Prior T-DM1 | Relevant — DESTINY-Breast02 required prior T-DM1; TH3RESA excluded it. Contributes to the TPC composite issue. |
| Era / comparator evolution | 10 yr span (2012 EMILIA → 2023 DESTINY-Breast02); supportive-care and subsequent-line options improved. |

---

## 6. CINeMA (v1.1)

| Comparison | Certainty |
|---|---|
| T-DXd vs T-DM1 (direct DESTINY-Breast03) | **HIGH** |
| T-DM1 vs LapaCape (direct EMILIA) | **HIGH** |
| T-DM1 vs TPC_TH3RESA (direct TH3RESA) | **HIGH** (within scope) |
| T-DXd vs TPC_DB02 (direct DESTINY-Breast02) | **HIGH** (within scope) |
| Network-synthesised T-DXd vs TPC (v1.1 composite) | **LOW-MODERATE** (driven by TPC composite, Q_inc significant) |
| Network-synthesised T-DM1 vs TPC (v1.1 composite) | **LOW-MODERATE** |
| LapaCape vs TPC (2-step indirect, composite) | **VERY LOW** |

---

## 7. PRISMA-NMA 2020 — Status: 23/27 ✅, 2/27 ⚠️, 2/27 declared limitation (consistency test fails, to be resolved in v1.2)

---

## 8. Artifact manifest

- `adc_her2_nma_netmeta.R`
- `adc_her2_nma_netmeta_results.{txt,rds,json}`
- `adc_her2_peer_review_bundle.md`
- App: `ADC_HER2_NMA_REVIEW.html`
- Protocol: `protocols/adc_her2_nma_protocol_v1.0_2026-04-21.md` (v1.1 supplement appended)

## Changelog

- **v1.1** (2026-04-21) — Added DESTINY-Breast02 per audit recommendation. Network closes T-DXd–T-DM1–TPC triangle; first consistency test now possible. **Q_inc=11.9 (p<0.001) — significant inconsistency detected.** Diagnosed as TPC composite (TH3RESA's single-agent chemo ± trast vs DESTINY-Breast02's trast+cape/lapa+cape). T-DXd rank-1 probability remains 98.6% — ranking robust to the inconsistency, but CIs for T-DM1 and LapaCape widened (CI for T-DM1 vs TPC now crosses null). Direct head-to-heads preserved. v1.2 roadmap: split TPC into two distinct nodes.
- **v1.0** (2026-04-21) — First release; 3 pivotal HER2+ MBC Phase 3 trials; T-DXd rank-1 100%; matches ASCO 2022 2L HER2+ MBC guideline + Hurvitz 2022 DESTINY-Breast03 primary publication.
