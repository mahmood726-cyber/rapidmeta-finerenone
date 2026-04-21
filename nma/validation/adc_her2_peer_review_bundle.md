# ADC NMA in HER2-Positive MBC — Peer-Review Defence Bundle

**Generated:** 2026-04-21 · **Version:** v1.0 (k=3, T-DM1-anchored tree, HR scale)
**Engine:** `netmeta` R package v3.2.0
**App:** `ADC_HER2_NMA_REVIEW.html`
**Outcome:** Progression-free survival (PFS) by BICR or investigator (TH3RESA).

---

## 1. Network

| Trial | NCT | Comparison | N | Setting |
|---|---|---|---|---|
| DESTINY-Breast03 | NCT03529110 | T-DXd 5.4 mg/kg vs T-DM1 3.6 mg/kg | 524 | 2L HER2+ MBC |
| EMILIA | NCT00829166 | T-DM1 vs Lapatinib + Capecitabine | 991 | 2L HER2+ MBC |
| TH3RESA | NCT01419197 | T-DM1 vs Treatment-of-Physician's-Choice | 602 | 3L+ HER2+ MBC |

**Geometry:** Connected tree centred on T-DM1. Three edges, no closed loops. Indirect T-DXd vs LapaCape/TPC contrasts via the T-DM1 anchor.

---

## 2. Consistency + heterogeneity

τ² = 0.000 · I² = NA · Q_inc = NA (tree-network, consistency test not defined).

---

## 3. Treatment effects (reference = TPC, the weakest node)

| Treatment | HR vs TPC | 95% CI |
|---|---:|---:|
| **T-DXd** | **0.174** | (0.124, 0.244) |
| **T-DM1** | 0.528 | (0.422, 0.661) |
| LapaCape | 0.812 | (0.614, 1.075) |
| TPC | 1.00 | — |

**Re-expressed head-to-head contrasts:**

| Contrast | HR | 95% CI | Evidence |
|---|---:|---:|---|
| T-DXd vs T-DM1 | 0.330 | (0.26, 0.43) | Direct (DESTINY-Breast03) |
| T-DM1 vs LapaCape | 0.650 | (0.55, 0.77) | Direct (EMILIA) |
| T-DM1 vs TPC | 0.528 | (0.42, 0.66) | Direct (TH3RESA) |
| T-DXd vs LapaCape | 0.214 | (~0.14, 0.32) | Indirect (via T-DM1) |
| T-DXd vs TPC | 0.174 | (0.12, 0.24) | Indirect (via T-DM1) |

---

## 4. Ranking

| Treatment | P-score | SUCRA |
|---|---:|---:|
| **T-DXd** | **1.000** | 1.000 |
| T-DM1 | 0.667 | 0.667 |
| LapaCape | 0.303 | 0.303 |
| TPC | 0.030 | 0.030 |

T-DXd is deterministically rank-1 with >99% probability in MC rank-prob matrix.

---

## 5. Transitivity

| Effect modifier | Concern |
|---|---|
| **Line of therapy** | **Moderate-Serious** — DESTINY-Breast03 and EMILIA are 2L; TH3RESA is 3L+. Baseline PFS on TPC arm in 3L+ is shorter; transitivity to 2L network assumes proportional-hazards across lines. |
| **PFS assessment** | Low — BICR in DESTINY-Breast03 + EMILIA; investigator-assessed in TH3RESA. |
| **Comparator heterogeneity (TPC)** | **Moderate** — TPC in TH3RESA was investigator-choice single-agent chemo ± trastuzumab. Differs from modern 3L SOC (tucatinib + trastuzumab + capecitabine, HER2CLIMB regimen, now preferred). |
| **Era / publication year** | Moderate — EMILIA 2012; TH3RESA 2014; DESTINY-Breast03 2022. Supportive-care and subsequent-line options improved over the decade. |
| **Central-review bias** | Low — all three trials used independent review for primary or sensitivity. |

---

## 6. CINeMA

| Comparison | Certainty |
|---|---|
| T-DXd vs T-DM1 (direct DESTINY-Breast03) | **HIGH** |
| T-DM1 vs LapaCape (direct EMILIA) | **HIGH** |
| T-DM1 vs TPC (direct TH3RESA) | **MODERATE-HIGH** (3L+ vs 2L transitivity concern) |
| T-DXd vs LapaCape (indirect) | **MODERATE** |
| T-DXd vs TPC (indirect) | **LOW-MODERATE** (line-of-therapy mismatch) |

---

## 7. Artifact manifest

- `adc_her2_nma_netmeta.R`
- `adc_her2_nma_netmeta_results.{txt,rds,json}`
- `adc_her2_peer_review_bundle.md`
- App: `ADC_HER2_NMA_REVIEW.html`
- Protocol: `protocols/adc_her2_nma_protocol_v1.0_2026-04-21.md`

## Changelog

- **v1.0** (2026-04-21) — First release; 3 pivotal HER2+ MBC Phase 3 trials; T-DXd rank-1 100%; matches ASCO 2022 2L HER2+ MBC guideline + Hurvitz 2022 DESTINY-Breast03 primary publication.
