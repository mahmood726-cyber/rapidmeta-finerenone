---
title: "Immunotherapy + Chemotherapy in 1L NSCLC"
slug: io_chemo_nsclc_1l
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Oncology (Lung)
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/io_chemo_nsclc_1l_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/IO_CHEMO_NSCLC_1L_REVIEW.html
license: MIT
---

# Checkpoint Inhibitor + Chemotherapy 1L NSCLC (KEYNOTE-189 / 407 / IMpower150 / POSEIDON)
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Oncology (Lung)

---

## 1. Review Title and Registration

**Title:** Checkpoint Inhibitor plus Platinum-Doublet Chemotherapy (with or without Anti-VEGF) as First-Line Therapy for Metastatic Non-Small-Cell Lung Cancer: A Living Systematic Review and Meta-Analysis of the KEYNOTE-189, KEYNOTE-407, IMpower150, and POSEIDON Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding). Corresponding address: drmahmoodclinic@pm.me.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with previously untreated metastatic NSCLC (non-squamous or squamous; EGFR/ALK wild-type) |
| **Intervention** | Checkpoint inhibitor (pembrolizumab, atezolizumab, or durvalumab +/- tremelimumab) + platinum-doublet chemotherapy (+/- bevacizumab) |
| **Comparator** | Platinum-doublet chemotherapy (+/- bevacizumab; matched regimen) |
| **Outcome (primary)** | Overall survival; hazard ratio |

---

## 3. Eligibility / Search / Selection

Inclusion: phase III pivotal, 1L metastatic NSCLC, checkpoint-inhibitor + chemotherapy vs chemotherapy alone, OS as primary or co-primary. Exclusion: IO monotherapy without chemotherapy backbone (KEYNOTE-024, EMPOWER-Lung 1; separate app candidate for PD-L1-high subset), neoadjuvant/adjuvant trials, EGFR/ALK-mutant-targeted trials, phase II. Two-reviewer adjudication; PRISMA 2020.

---

## 6-7. Data Extraction + RoB

Per-arm OS HR + CI (log-hazard scale), PFS HR, ORR, PD-L1-subgroup HRs. Safety: grade >=3 AEs, immune-related AEs (pneumonitis, colitis, hepatitis, endocrine), treatment discontinuation due to AE. RoB 2 LOW across D1-D5 for KEYNOTE-189 / KEYNOTE-407 (both double-blind placebo-controlled) and for IMpower150 / POSEIDON (open-label but OS objective + BICR PFS mitigate). Author sign-off per provisional-RoB banner.

---

## 8. Synthesis / Statistical Methods

- DerSimonian-Laird random-effects IVW on log-HR scale (OS).
- HKSJ t-df=k-1 with `max(1, Q/(k-1))` floor.
- At k=4, prediction interval computable.
- Subgroup: histology (squamous vs non-squamous), PD-L1 TPS (<1% / 1-49% / >=50%), ECOG PS.
- Sensitivity: PFS as consistency check; exclude POSEIDON (CTLA-4 add-on) as sensitivity.
- Bayesian half-normal(0, 0.3) prior on tau (log-HR scale).
- Browser-hosted WebR cross-validation (optional, user-triggered).

---

## 9-10. GRADE / Reporting

Standard GRADE. Class-level pool across distinct checkpoint-inhibitor regimens (PD-1 pembrolizumab, PD-L1 atezolizumab + anti-VEGF bevacizumab, PD-L1 durvalumab + CTLA-4 tremelimumab) and across histologies — indirectness downgrade candidate. KEYNOTE-189 (non-squamous pembro+chemo, HR 0.56) shows largest benefit; POSEIDON (durva+treme+chemo, HR 0.77) smallest. CTLA-4 addition adds toxicity without clearly more OS benefit. Drug-specific and histology-specific subgroup analyses preferred for clinical decisions. PRISMA 2020, CONSORT-Harms.

---

## 11. Living-MA Update Cadence

Formal 3-monthly cadence. Triggers: KEYNOTE-189/407 5-year updates, IMpower150 final OS, POSEIDON durvalumab-chemo arm (not analysed here), CheckMate 9LA nivo+ipi+chemo update, EMPOWER-Lung 3 cemiplimab+chemo, next-generation LAG-3 / TIGIT combinations.

---

## 12-14

Aggregate-data only. No competing interests, no funding.

---

## Appendix A. AMSTAR-2 Critical-Domain Self-Assessment

| # | Domain | Self-rating | Evidence |
|---|---|---|---|
| 2 | Registered protocol | Yes (partial) | GitHub-canonical-URL freeze |
| 4 | Search strategy | Yes | §4 |
| 7 | Excluded-studies list | Yes | Screening tab (IO monotherapy, neo/adjuvant trials, EGFR/ALK-targeted explicitly excluded) |
| 9 | RoB assessment | Yes | Authors have double-checked screening and data extraction against the record excerpts shown in the Extraction tab; provisional AI-drafted RoB-2 is now author-confirmed. Formal dual-assessor RoB-2 remains a per-submission step. |
| 11 | Statistical methods | Yes | §8 |
| 13 | RoB in interpretation | Partial | GRADE §9, regimen/histology indirectness noted |
| 15 | Publication bias | Yes | k=4, formal tests included with funnel plot inspection |
| 1 | PICO | Yes | §2 |

---

## Changelog
- **v1.1** (2026-04-20) — Initial editor-review-revision release.
