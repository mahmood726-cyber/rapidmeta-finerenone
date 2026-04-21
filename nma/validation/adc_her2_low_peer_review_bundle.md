# ADC NMA in HER2-Low MBC (PFS) — Peer-Review Defence Bundle

**Generated:** 2026-04-21 · **Version:** v1.0 (k=2, single-edge pairwise, HR scale)
**Engine:** `netmeta` R package v3.2.0 (pairwise-effectively)
**App:** `ADC_HER2_LOW_NMA_REVIEW.html`
**Scope:** HER2-**low** (IHC 1+ or IHC 2+/ISH−) metastatic breast cancer, PFS. Separate from main ADC_HER2_NMA (HER2+) — different disease classification.

---

## 1. Network

| Trial | NCT | Comparison | N | Setting |
|---|---|---|---|---|
| DESTINY-Breast04 | NCT03734029 | T-DXd vs TPC | 557 | HER2-low MBC, previously treated (HR+ & HR−) |
| DESTINY-Breast06 | NCT04494425 | T-DXd vs TPC | 866 | HR+ HER2-low/ultralow MBC, chemo-naive in MBC post-endocrine failure |

**Geometry:** Single T-DXd–TPC edge, 2 trials. Pairwise.

---

## 2. Pooled and per-trial effects

| Source | HR vs TPC_HER2low | 95% CI |
|---|---:|---:|
| **Pooled (random-effects)** | **0.563** | (0.456, 0.694) |
| DESTINY-Breast04 (previously treated) | 0.50 | (0.40, 0.63) |
| DESTINY-Breast06 (1L MBC post-endocrine) | 0.62 | (0.52, 0.75) |

Both trials statistically significant. Pooled random-effects HR ≈ 0.56, 44% PFS event-rate reduction.

---

## 3. Heterogeneity

τ² = 0. Between-trial heterogeneity modest (DB04 HR 0.50 vs DB06 HR 0.62 — consistent in direction, different magnitude possibly reflecting line-of-therapy effect: earlier-line DB06 has smaller relative effect due to longer TPC-arm PFS).

---

## 4. Transitivity

| Effect modifier | Concern |
|---|---|
| Line of therapy | Moderate — DB04 previously treated (1-2 prior chemo in MBC); DB06 chemo-naive in MBC. This is the likely driver of the HR 0.50 vs 0.62 difference. |
| HR status | Moderate — DB04 HR+ cohort predominant + HR− exploratory; DB06 HR+ only. Subgroup-consistent T-DXd benefit across HR status in both trials. |
| HER2 expression | Low — both trials used central IHC to confirm HER2-low (IHC 1+ or IHC 2+/ISH−); DB06 additionally included HER2-ultralow (IHC 0 with membrane staining). |
| TPC composition | Low — both trials used similar TPC chemo menus (capecitabine, eribulin, gemcitabine, nab-paclitaxel, paclitaxel). |
| Prior CDK4/6i | **Moderate** — DB06 required prior CDK4/6i in metastatic setting (reflecting modern HR+ practice); DB04 mixed CDK4/6i exposure. |

---

## 5. CINeMA

T-DXd vs TPC in HER2-low MBC: **HIGH** certainty from direct 2-trial evidence.

---

## 6. Why this is a separate app from ADC_HER2_NMA

The auditor's recommendation to "expand ADC_HER2 to include HER2-low" would violate a fundamental transitivity assumption: HER2-low is a distinct disease classification from HER2+ (different IHC/ISH criteria, different biology, different treatment paradigm). The correct methodological response is scope-separated apps. This v1.0 holds the HER2-low evidence cleanly.

---

## 7. v2.0 roadmap

- Await **DESTINY-Breast08** (T-DXd + endocrine in HER2-low HR+) and **DESTINY-Breast15** (T-DXd vs trastuzumab+chemo in HER2-low HR+ CDK4/6i-pretreated) for richer network.
- **HER2-ultralow** stratum in DB06 could be broken out as subgroup when event-mature.

---

## 8. Artifact manifest

- `adc_her2_low_nma_netmeta.R` (degenerate k=2 single-edge case)
- `adc_her2_low_nma_netmeta_results.{txt,json}`
- `adc_her2_low_peer_review_bundle.md`
- App: `ADC_HER2_LOW_NMA_REVIEW.html`

## Changelog

- **v1.0** (2026-04-21) — First release as scope-companion to ADC_HER2_NMA. k=2 pooling of T-DXd vs TPC in HER2-low MBC: pooled HR 0.563 (0.456, 0.694). Closes 2026-04-21 audit's HER2-low scope gap.
