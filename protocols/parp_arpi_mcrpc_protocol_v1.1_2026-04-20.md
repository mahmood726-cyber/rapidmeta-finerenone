---
title: "PARP Inhibitor + ARPI Combination in 1L mCRPC"
slug: parp_arpi_mcrpc
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Oncology (Prostate)
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/parp_arpi_mcrpc_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/PARP_ARPI_MCRPC_REVIEW.html
license: MIT
---

# PARPi + ARPI in 1L mCRPC (PROpel / MAGNITUDE / TALAPRO-2)
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Oncology (Prostate)

---

## 1. Review Title and Registration

**Title:** PARP Inhibitor + Androgen-Receptor Pathway Inhibitor Combination as First-Line Therapy in Metastatic Castration-Resistant Prostate Cancer: A Living Systematic Review and Meta-Analysis of the PROpel, MAGNITUDE, and TALAPRO-2 Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding). Corresponding address: drmahmoodclinic@pm.me.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with previously untreated metastatic castration-resistant prostate cancer (1L setting) |
| **Intervention** | PARP inhibitor (olaparib, niraparib, or talazoparib) + ARPI (abiraterone or enzalutamide) |
| **Comparator** | Placebo + same ARPI |
| **Outcome (primary)** | Radiographic progression-free survival (investigator or BICR); hazard ratio |

---

## 3. Eligibility / Search / Selection

Inclusion: phase III pivotal, 1L mCRPC, PARPi + ARPI vs placebo + ARPI, rPFS as primary or co-primary. Exclusion: PARPi monotherapy trials (PROfound Olaparib in 2L+; separate app candidate), PARPi in non-mCRPC settings (adjuvant, localised), phase II dose-finding (study 08), 2L+ mCRPC post-ARPI failure trials. Two-reviewer adjudication; PRISMA 2020.

---

## 6-7. Data Extraction + RoB

Per-arm rPFS HR + CI (log-hazard scale), OS HR, ORR, HRR-subgroup HRs (BRCA1/2 subgroup is a key clinical signal). Safety: anaemia, thrombocytopaenia, pulmonary embolism, MDS/AML, dose reductions, discontinuations. RoB 2 LOW across D1-D5 for all 3 trials (double-blind matched placebo, central IVR, BICR or pre-specified concordance, SAP locked). Author sign-off per provisional-RoB banner.

---

## 8. Synthesis / Statistical Methods

- DerSimonian-Laird random-effects HR pool on log-hazard scale (rPFS).
- HKSJ t-df=k-1 with `max(1, Q/(k-1))` floor.
- At k=3, prediction interval computable.
- Subgroup: HRR status (BRCA1/2 mutated / HRR-non-BRCA / HRR-unselected), ARPI partner (abiraterone vs enzalutamide), ECOG PS, prior docetaxel.
- Sensitivity: HRR+-only subgroup pool (use MAGNITUDE HRR+ + PROpel HRR+ subgroup + TALAPRO-2 HRR+ subgroup) - BRCA+ effect is substantial (HR ~0.50).
- Bayesian half-normal(0, 0.3) prior on tau (log-HR scale).
- Browser-hosted WebR cross-validation (optional, user-triggered).

---

## 9-10. GRADE / Reporting

Standard GRADE. Class-level pool across 3 distinct PARPi (olaparib, niraparib, talazoparib) and 2 ARPI (abiraterone, enzalutamide) partners. MAGNITUDE primary cohort was HRR+-only (HRR-non-mutated futility-stopped); PROpel and TALAPRO-2 are HRR-unselected ITT. BRCA1/2 is the strongest biomarker signal (HR ~0.50). Anaemia is a major class-level adverse effect — talazoparib largest (46% grade 3+). Net clinical benefit is clear in HRR+/BRCA+ patients; in HRR-unselected populations, benefit is smaller but statistically significant. PRISMA 2020, CONSORT-Harms.

---

## 11. Living-MA Update Cadence

Formal 3-monthly cadence. Triggers: PROpel final OS, MAGNITUDE long-term follow-up, TALAPRO-2 final OS, ongoing PSMAsurvive / EZH2-combination trials, any novel HRR-targeted approach.

---

## 12-14

Aggregate-data only. No competing interests, no funding.

---

## Appendix A. AMSTAR-2 Critical-Domain Self-Assessment

| # | Domain | Self-rating | Evidence |
|---|---|---|---|
| 2 | Registered protocol | Yes (partial) | GitHub-canonical-URL freeze |
| 4 | Search strategy | Yes | §4 |
| 7 | Excluded-studies list | Yes | Screening tab (PARPi monotherapy, 2L+ mCRPC, non-mCRPC settings, phase II dose-finding explicitly excluded) |
| 9 | RoB assessment | Yes | Authors have double-checked screening and data extraction against the record excerpts shown in the Extraction tab; provisional AI-drafted RoB-2 is now author-confirmed. Formal dual-assessor RoB-2 remains a per-submission step. |
| 11 | Statistical methods | Yes | §8 |
| 13 | RoB in interpretation | Partial | GRADE §9, HRR-selected/unselected and PARPi-partner indirectness noted |
| 15 | Publication bias | Yes (k-appropriate) | k=3, formal tests suppressed |
| 1 | PICO | Yes | §2 |

---

## Changelog
- **v1.1** (2026-04-20) — Initial editor-review-revision release.
