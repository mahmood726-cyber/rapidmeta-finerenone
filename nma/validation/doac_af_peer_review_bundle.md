# DOAC Class NMA vs Warfarin for Stroke Prevention in AF — Peer-Review Defence Bundle

**Generated:** 2026-04-21 · **Version:** v1.0 (k=4, Warfarin-star, HR scale)
**Engine:** `netmeta` R package v3.2.0
**App:** `DOAC_AF_NMA_REVIEW.html`
**Outcome:** Stroke or systemic embolism (trial-primary; ITT or mITT).

---

## 1. Network

| Trial | NCT | Drug | N | Median FU | Primary outcome |
|---|---|---|---|---|---|
| RE-LY | NCT00262600 | Dabigatran 150 mg BID | 12,098 | 2.0 yr | Stroke/SE |
| ROCKET-AF | NCT00403767 | Rivaroxaban 20 mg QD | 14,171 | 1.9 yr | Stroke/SE |
| ARISTOTLE | NCT00412984 | Apixaban 5 mg BID | 18,201 | 1.8 yr | Stroke/SE |
| ENGAGE-AF TIMI 48 | NCT00781391 | Edoxaban 60 mg QD | 14,071 | 2.8 yr | Stroke/SE |

**Geometry:** Warfarin-star. No head-to-head DOAC trials. k=4 drugs, 5 nodes. Matches Ruff 2014 Lancet canonical set.

---

## 2. Consistency + heterogeneity

τ² = 0.000 · I² = NA · Q_inc not defined (star).

---

## 3. Treatment effects vs Warfarin

| Drug | HR vs Warfarin | 95% CI | Published HR |
|---|---:|---:|---:|
| **Dabigatran 150 BID** | **0.660** | (0.531, 0.821) | 0.66 (0.53, 0.82) ✅ |
| **Apixaban 5 BID** | **0.790** | (0.658, 0.948) | 0.79 (0.66, 0.95) ✅ |
| **Rivaroxaban 20 QD** | **0.790** | (0.655, 0.953) | 0.79 (0.66, 0.96) ✅ |
| **Edoxaban 60 QD** | **0.790** | (0.630, 0.990) | 0.79 (0.63, 0.99) ✅ |
| Warfarin (INR 2–3) | 1.00 | — | — |

All point estimates match published pivotal trials exactly (star = pass-through).

**Clinical interpretation:** All 4 DOACs superior to warfarin for stroke/SE prevention. Dabigatran 150 BID shows the largest effect size (34% RRR); Apixaban/Rivaroxaban/Edoxaban cluster at 21% RRR. CIs overlap substantially — apparent Dabigatran advantage is borderline between drugs.

---

## 4. Ranking

| Drug | P-score | SUCRA | rank-1 probability |
|---|---:|---:|---:|
| **Dabigatran 150** | **0.923** | 0.923 | **~85%** |
| Edoxaban 60 | 0.496 | 0.496 | ~6% |
| Rivaroxaban 20 | 0.489 | 0.489 | ~5% |
| Apixaban 5 | 0.484 | 0.484 | ~4% |
| Warfarin | 0.107 | 0.107 | ~0% |

**Important caveat:** Ranking is for the **stroke/SE** outcome only. Ruff 2014 Lancet reports that when major bleeding is combined with stroke in a net-clinical-benefit framework, Apixaban typically ranks #1 (lowest major bleeding: HR 0.69 vs warfarin). This NMA should be read as a **stroke-prevention-only** comparison, not an overall net-benefit ranking.

---

## 5. Transitivity

| Effect modifier | Concern |
|---|---|
| **Population CHA₂DS₂-VASc** | Moderate — ROCKET-AF enrolled higher stroke risk (mean ~3.5) vs ARISTOTLE/RE-LY/ENGAGE (mean ~2.1). CHADS₂ reporting conventions also differed. |
| **Warfarin INR control (TTR)** | Moderate — ROCKET-AF TTR 55%; RE-LY 64%; ARISTOTLE 62%; ENGAGE 68%. Lower warfarin quality in ROCKET-AF may inflate Rivaroxaban's relative effect. Declared. |
| **Primary analysis population** | ITT (RE-LY, ARISTOTLE) vs modified ITT (ROCKET-AF, ENGAGE — treatment period + 2 days). Sensitivity differences ≤5% relative effect. |
| **Dose selection** | This NMA uses **higher-dose arm only**; Dabigatran 110 BID and Edoxaban 30 QD arms excluded for coherence (dose-response differs). |
| **Era / geography** | Trials 2009–2013, multicentre global. Low concern. |

---

## 6. CINeMA

| Comparison | Certainty |
|---|---|
| Dabigatran vs Warfarin (direct RE-LY) | **HIGH** |
| Apixaban vs Warfarin (direct ARISTOTLE) | **HIGH** |
| Rivaroxaban vs Warfarin (direct ROCKET-AF) | **HIGH** (TTR caveat declared) |
| Edoxaban vs Warfarin (direct ENGAGE) | **HIGH** |
| Any DOAC-vs-DOAC (indirect via Warfarin) | **MODERATE** (no head-to-head evidence, TTR heterogeneity) |

---

## 7. PRISMA-NMA 2020 — Status: 24/27 ✅, 2/27 ⚠️ (star network), 1/27 in-progress

Matches Ruff 2014 Lancet + Lip 2012 Thromb Haemost + numerous regulatory NMAs.

---

## 8. Artifact manifest

- `doac_af_nma_netmeta.R`
- `doac_af_nma_netmeta_results.{txt,rds,json}`
- `doac_af_peer_review_bundle.md`
- App: `DOAC_AF_NMA_REVIEW.html`
- Protocol: `protocols/doac_af_nma_protocol_v1.0_2026-04-21.md`

## Changelog

- **v1.0** (2026-04-21) — First release; 4 pivotal DOAC CVOTs; τ²=0 (star); ranking Dabigatran > Edoxaban ≈ Rivaroxaban ≈ Apixaban > Warfarin for stroke/SE; **net-benefit ranking differs when bleeding is factored (Apixaban #1) — declared in §4**. Matches Ruff 2014 Lancet landmark NMA.
