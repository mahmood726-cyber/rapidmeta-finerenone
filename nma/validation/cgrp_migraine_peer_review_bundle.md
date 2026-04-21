# CGRP mAb Class NMA for Episodic Migraine Prevention — Peer-Review Defence Bundle

**Generated:** 2026-04-21 · **Version:** v1.0 (k=4, Pbo-star, MD scale)
**Engine:** `netmeta` R package v3.2.0
**App:** `CGRP_MIGRAINE_NMA_REVIEW.html`
**Outcome:** Change from baseline in mean monthly migraine days (MMD) at primary timepoint. **MD scale.**

---

## 1. Network

| Trial | NCT | Drug / Route / Dose | N | Primary TP |
|---|---|---|---|---|
| STRIVE | NCT02456740 | Erenumab 140 mg SC monthly | 635 | months 4–6 |
| HALO-EM | NCT02629861 | Fremanezumab 675 mg SC quarterly | 584 | 12 wk |
| EVOLVE-1 | NCT02614183 | Galcanezumab 120 mg SC monthly | 638 | months 1–6 |
| PROMISE-1 | NCT02559895 | Eptinezumab 100 mg IV q3mo | 444 | wks 1–12 |

**Geometry:** Pbo-star. No head-to-head between CGRP mAbs. k=4 drugs, 5 nodes.

---

## 2. Consistency + heterogeneity

τ² = 0.000 · I² = NA (star) · Q_inc = NA.

---

## 3. Treatment effects vs Placebo

| Drug | MD (MMD) | 95% CI | Published (ref) |
|---|---:|---:|---:|
| **Galcanezumab 120 mg** | **−1.90** | (−2.51, −1.29) | −1.9 (−2.5, −1.3) ✅ |
| **Erenumab 140 mg** | **−1.85** | (−2.47, −1.23) | −1.85 (−2.47, −1.23) ✅ |
| **Fremanezumab Q675** | **−1.30** | (−1.79, −0.82) | −1.3 (−1.8, −0.8) ✅ |
| **Eptinezumab 100 mg IV** | **−0.69** | (−1.16, −0.22) | −0.69 (−1.16, −0.22) ✅ |
| Placebo | 0 | — | — |

All point estimates match published trial values exactly (star-network pass-through).

---

## 4. Ranking

| Drug | P-score | SUCRA |
|---|---:|---:|
| Galcanezumab | 0.889 | 0.889 |
| Erenumab | 0.833 | 0.833 |
| Fremanezumab | 0.504 | 0.504 |
| Eptinezumab | 0.230 | 0.230 |
| Placebo | 0.045 | 0.045 |

Gal ≈ Ere (indistinguishable rank-1/2), Frem middle, Epti weakest effect.

---

## 5. Transitivity

| Effect modifier | Concern |
|---|---|
| **Primary timepoint** | Moderate — 12 wk (HALO-EM, PROMISE-1) vs months 4–6 (STRIVE, EVOLVE-1). Longer observation allows more placebo drift, may inflate MD in shorter-window trials. Declared. |
| **Route** | Low — 3 SC (monthly/quarterly) + 1 IV (quarterly, PROMISE-1). PK differs but primary efficacy outcome timepoint-harmonised. |
| **Dose selection** | Moderate — one approved dose per drug chosen. Other doses tested (e.g. Erenumab 70 mg, Galcanezumab 240 mg) excluded for network coherence. |
| **MOA** | Noted — Erenumab targets CGRP receptor; others target CGRP ligand. Declared but both block CGRP signalling. |

---

## 6. CINeMA

All direct Pbo edges: **HIGH** certainty. Indirect drug-vs-drug contrasts: **MODERATE** (single-trial per drug + timepoint heterogeneity).

---

## 7. Artifact manifest

- `cgrp_migraine_nma_netmeta.R`
- `cgrp_migraine_nma_netmeta_results.{txt,rds,json}`
- `cgrp_migraine_peer_review_bundle.md` — this file
- App: `CGRP_MIGRAINE_NMA_REVIEW.html`
- Protocol: `protocols/cgrp_migraine_nma_protocol_v1.0_2026-04-21.md`

## Changelog

- **v1.0** (2026-04-21) — First release; k=4 EM Phase-3 trials; ranking matches Drellia 2021 Cephalalgia NMA + Forbes 2023 BMJ NMA.
