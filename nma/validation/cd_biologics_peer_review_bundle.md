# Crohn's Disease Biologics Induction-Remission NMA — Peer-Review Defence Bundle

**Generated:** 2026-04-21 · **Version:** v1.0 (k=7, Pbo-star, OR scale)
**Engine:** `netmeta` R package v3.2.0
**App:** `CD_BIOLOGICS_NMA_REVIEW.html`
**Outcome:** Clinical remission (CDAI <150) or response (CDAI decrease ≥100) at induction timepoint.

---

## 1. Network

| Trial | Drug | N | Primary TP | Endpoint |
|---|---|---:|---|---|
| ACCENT-1 | Infliximab | 573 | wk 2+30 | Remission among wk-2 responders |
| CLASSIC-1 | Adalimumab | 148 | wk 4 | Remission (TNF-naive) |
| PRECiSE-1 | Certolizumab | 662 | wk 6 | Response (CDAI decrease ≥100) |
| GEMINI-2 | Vedolizumab | 368 | wk 6 | Remission |
| UNITI-1 | Ustekinumab | 496 | wk 8 | Response (TNF-failures) |
| ADVANCE | Risankizumab | 547 | wk 12 | CDAI remission |
| U-EXCEL | Upadacitinib | 483 | wk 12 | CDAI remission |

**Geometry:** Placebo-star network. k=7. τ²=0, no closed loops.

---

## 2. Results

| Drug | OR vs Pbo | 95% CI | Published |
|---|---:|---:|---|
| **Adalimumab** | **4.74** | (2.19, 10.26) | CLASSIC-1 (wk 4 early endpoint, TNF-naive; interpret with caution) |
| **Upadacitinib 45** | **4.69** | (3.04, 7.24) | U-EXCEL |
| Vedolizumab | 2.54 | (1.21, 5.33) | GEMINI-2 |
| Infliximab | 2.11 | (1.28, 3.48) | ACCENT-1 (different design — wk 30 among wk-2 responders) |
| Ustekinumab | 1.99 | (1.27, 3.13) | UNITI-1 (TNF-failures — harder population) |
| Risankizumab | 1.82 | (1.21, 2.73) | ADVANCE |
| Certolizumab | 1.53 | (1.07, 2.20) | PRECiSE-1 (response, not remission) |

---

## 3. Transitivity

**Substantial heterogeneity in endpoint definition and timepoint:**

- CLASSIC-1 (ADA): wk-4 primary in TNF-naive — unusually high remission rate (89% vs 19%) inflates OR relative to other drugs
- ACCENT-1 (IFX): wk-30 remission *among wk-2 responders* — enriched-population design, not ITT remission
- PRECiSE-1 (CZP): **response** (CDAI Δ≥100), not remission — easier endpoint
- UNITI-1 (UST): TNF-failure-enriched population — harder to achieve remission
- U-EXCEL (UPA): wk 12 remission in broad population
- ADVANCE (RISA): wk 12 remission in broad population

**Interpretation warning:** Adalimumab's apparent rank-1 OR is a design artefact. Cross-trial comparison requires standardising to wk-6-to-8 all-comers CDAI <150. Published comprehensive CD NMAs (Singh 2020 Lancet GH, Barberio 2022 Gut) harmonise endpoints and typically rank **Upadacitinib** or **Infliximab** rank-1 for induction of remission. Recommend this NMA be read alongside those comprehensive analyses.

---

## 4. Ranking

| Drug | P-score |
|---|---:|
| Adalimumab | 0.798 (design-inflated) |
| Upadacitinib | 0.614 |
| Vedolizumab | 0.572 |
| Infliximab | 0.356 |
| Ustekinumab | 0.244 (TNF-failure population) |
| Risankizumab | 0.156 |
| Certolizumab | 0.097 (response not remission) |
| Placebo | 0.032 |

---

## 5. CINeMA

All direct Pbo edges: **MODERATE-HIGH** individually; the network as a whole has **MODERATE** certainty due to transitivity concerns around endpoint/timepoint heterogeneity (declared above).

---

## 6. Artifact manifest

- `cd_biologics_nma_netmeta.R`
- `cd_biologics_nma_netmeta_results.{txt,rds,json}`
- `cd_biologics_peer_review_bundle.md`
- App: `CD_BIOLOGICS_NMA_REVIEW.html`
- Protocol: `protocols/cd_biologics_nma_protocol_v1.0_2026-04-21.md`

## Changelog

- **v1.0** (2026-04-21) — First release; 7 pivotal trials; honest declaration of endpoint-heterogeneity transitivity concern in §3. Companion to UC_BIOLOGICS_NMA (gastroenterology specialty). Ranking preserved but clinical interpretation requires harmonised-endpoint cross-checking vs Singh 2020 / Barberio 2022.
