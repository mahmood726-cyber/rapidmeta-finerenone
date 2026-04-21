# ADC NMA in HER2+ EBC Adjuvant (Residual Disease) — Peer-Review Defence Bundle

**Generated:** 2026-04-21 · **Version:** v1.0 (k=1 pairwise through NMA scaffold, HR scale)
**Engine:** `netmeta` R package v3.2.0 (degenerate — pairwise effectively)
**App:** `ADC_HER2_ADJUVANT_NMA_REVIEW.html`
**Scope:** HER2-positive **early breast cancer** with **residual invasive disease** after neoadjuvant chemotherapy + HER2-directed therapy. Outcome: **invasive disease-free survival (iDFS)** — not PFS.

---

## 0. Why this is a separate app from ADC_HER2_NMA

The main ADC_HER2 NMA covers HER2+ **metastatic** 2L+ with **PFS**. Adjuvant EBC uses a different endpoint (iDFS) and a different disease setting (curative-intent). Grouping them would violate transitivity at the endpoint level. This v1.0 app is a scope-companion holding the adjuvant evidence.

---

## 1. Network

| Trial | NCT | Comparison | N | Setting |
|---|---|---|---|---|
| KATHERINE | NCT01772472 | T-DM1 3.6 mg/kg q3w × 14 vs Trastuzumab 6 mg/kg q3w × 14 | 1486 | HER2+ EBC, residual invasive disease post-neoadjuvant |

**Geometry:** Single edge. Pairwise.

---

## 2. Consistency + heterogeneity

Not applicable (k = 1). τ² = 0 by definition.

---

## 3. Treatment effect (KATHERINE primary)

| Treatment | HR vs Trastuzumab | 95% CI |
|---|---:|---:|
| **T-DM1** | **0.50** | (0.39, 0.64) |
| Trastuzumab | 1.00 | — |

**3-yr iDFS:** T-DM1 **88.3%** vs Trastuzumab **77.0%**. Absolute difference ~11.3 pp — practice-changing.

---

## 4. Ranking

Trivially determined: T-DM1 superior (P-score 1.0) vs Trastuzumab (P-score 0.0).

---

## 5. Transitivity

Not applicable (single trial). Internal validity (KATHERINE RoB: low across all 5 Cochrane domains).

---

## 6. CINeMA

T-DM1 vs Trastuzumab (direct, KATHERINE): **HIGH** certainty.

---

## 7. Why not a full "HER2-ADC class NMA"?

The auditor asked whether KATHERINE could join the main ADC_HER2_NMA. Answer: **no**, because:

1. **Endpoint mismatch**: KATHERINE uses iDFS; EMILIA/DESTINY-Breast03/TH3RESA/DESTINY-Breast02 use PFS. iDFS is a composite of invasive recurrence/new primary/death and is measured in curative-intent follow-up; PFS in metastatic disease measures progression-on-therapy. These are not on the same HR-scale.
2. **Population mismatch**: Adjuvant (curative intent, typically early-stage, residual disease after neoadjuvant) vs metastatic (palliative intent, disseminated disease).
3. **Competing comparator**: KATHERINE's control arm is plain trastuzumab (effectively "active surveillance + HER2 maintenance"); metastatic NMA controls are active chemo regimens.

The correct methodological resolution is a **scope-separated** analysis, which is what this v1.0 app provides.

---

## 8. v2.0 roadmap

Add T-DXd adjuvant data when DESTINY-Breast05 (NCT04622319, T-DXd vs T-DM1 in HER2+ EBC residual disease) reads out (estimated 2025–2026). That trial will enable a 2-node NMA triangle (T-DXd vs T-DM1 vs Trastuzumab indirect).

---

## 9. Artifact manifest

- `adc_her2_adjuvant_nma_netmeta.R` (degenerate k=1 case)
- `adc_her2_adjuvant_nma_netmeta_results.{txt,json}` (RDS skipped due to MC-step failure at k=1; expected)
- `adc_her2_adjuvant_peer_review_bundle.md` — this file
- App: `ADC_HER2_ADJUVANT_NMA_REVIEW.html`

## Changelog

- **v1.0** (2026-04-21) — First release as scope-companion to ADC_HER2_NMA. Responds to 2026-04-21 audit recommendation for adjuvant-setting coverage. Single-trial pairwise; upgrade path documented (DESTINY-Breast05 readout).
