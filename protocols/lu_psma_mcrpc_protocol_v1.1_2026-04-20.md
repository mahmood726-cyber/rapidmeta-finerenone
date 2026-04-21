---
title: "177Lu-PSMA-617 Radioligand Therapy in mCRPC"
slug: lu_psma_mcrpc
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Oncology (Prostate)
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/lu_psma_mcrpc_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/LU_PSMA_MCRPC_REVIEW.html
license: MIT
---

# 177Lu-PSMA-617 in mCRPC (VISION / PSMAfore)
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Oncology (Prostate)

---

## 1. Review Title and Registration

**Title:** 177Lutetium-PSMA-617 Radioligand Therapy (Pluvicto) in Metastatic Castration-Resistant Prostate Cancer: A Living Systematic Review and Meta-Analysis of the VISION (post-taxane) and PSMAfore (pre-taxane) Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding). Corresponding address: drmahmoodclinic@pm.me.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with PSMA-positive (68Ga-PSMA-11 PET/CT) metastatic castration-resistant prostate cancer |
| **Intervention** | 177Lu-PSMA-617 7.4 GBq IV Q6W (up to 6 cycles) |
| **Comparator** | VISION: protocol-permitted standard of care (without 177Lu). PSMAfore: switch to alternative ARPI. |
| **Outcome (primary)** | Radiographic progression-free survival (BICR-assessed); hazard ratio |

---

## 3. Eligibility / Search / Selection

Inclusion: phase III pivotal, PSMA-positive mCRPC confirmed on PET/CT, 177Lu-PSMA-617 vs SoC or ARPI switch, BICR-assessed rPFS primary. Exclusion: phase II, 177Lu-PSMA-I&T (distinct chemotype; separate app candidate), 225Ac-PSMA alpha-emitter trials (single-arm currently), prior lutetium exposure. Two-reviewer adjudication; PRISMA 2020.

---

## 6-7. Data Extraction + RoB

Per-arm rPFS HR + CI (log-HR scale), OS HR, PSA50 response, ORR, dosimetry. Safety: xerostomia, anaemia, thrombocytopaenia, fatigue, nausea, renal function. RoB 2 across D1-D5 — both trials D2 SOME CONCERNS (open-label allocation; VISION: SoC heterogeneous; PSMAfore: high crossover confounds OS — mitigated by BICR rPFS). Author sign-off per provisional-RoB banner.

---

## 8. Synthesis / Statistical Methods

- DerSimonian-Laird random-effects IVW on log-HR scale (rPFS).
- HKSJ t-df=k-1 with `max(1, Q/(k-1))` floor.
- At k=2, FE-IVW sensitivity per CART-MM SAP.
- PI suppressed at k<3.
- Subgroup: prior taxane exposure (VISION post-taxane, PSMAfore taxane-naive), baseline LDH, visceral disease, PSMA-SUV max.
- Sensitivity: OS as secondary estimand (PSMAfore crossover-adjusted vs ITT); PSA50 as consistency check.
- Bayesian half-normal(0, 0.5) prior on tau (log-HR scale).
- Browser-hosted WebR cross-validation (optional, user-triggered).

---

## 9-10. GRADE / Reporting

Standard GRADE. Pooling VISION and PSMAfore pools across distinct lines (post-taxane vs taxane-naive) — indirectness downgrade candidate. Both show substantial rPFS benefit (HR 0.40 and 0.43). OS interpretation requires crossover adjustment in PSMAfore. Xerostomia and cytopenias are predictable on-target/on-path effects. PRISMA 2020, CONSORT-Harms.

---

## 11. Living-MA Update Cadence

Formal 3-monthly cadence. Triggers: VISION final OS, PSMAfore final rPFS + crossover-adjusted OS, SPLASH (177Lu-PSMA-I&T, distinct chemotype), ENZA-p (177Lu + enzalutamide combination), PSMA-addition (earlier lines), 225Ac-PSMA-617 phase 3 planning.

---

## 12-14

Aggregate-data only. No competing interests, no funding.

---

## Appendix A. AMSTAR-2 Critical-Domain Self-Assessment

| # | Domain | Self-rating | Evidence |
|---|---|---|---|
| 2 | Registered protocol | Yes (partial) | GitHub-canonical-URL freeze |
| 4 | Search strategy | Yes | §4 |
| 7 | Excluded-studies list | Yes | Screening tab |
| 9 | RoB assessment | Yes | Authors have double-checked screening and data extraction against the record excerpts shown in the Extraction tab; provisional AI-drafted RoB-2 is now author-confirmed. Formal dual-assessor RoB-2 remains a per-submission step. |
| 11 | Statistical methods | Yes | §8 |
| 13 | RoB in interpretation | Partial | GRADE §9, line-of-therapy indirectness + crossover OS confounding noted |
| 15 | Publication bias | Yes (k-appropriate) | k=2, formal tests suppressed |
| 1 | PICO | Yes | §2 |

---

## Changelog
- **v1.1** (2026-04-20) — Initial editor-review-revision release.
