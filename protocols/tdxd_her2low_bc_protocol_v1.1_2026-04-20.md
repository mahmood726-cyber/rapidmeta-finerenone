---
title: "Trastuzumab Deruxtecan in HER2-Low Metastatic Breast Cancer"
slug: tdxd_her2low_bc
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Oncology (Breast)
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/tdxd_her2low_bc_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/TDXD_HER2LOW_BC_REVIEW.html
license: MIT
---

# Trastuzumab Deruxtecan in HER2-Low Metastatic Breast Cancer
## A Living Systematic Review and Meta-Analysis Protocol (DESTINY-Breast Programme)

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Oncology (Breast)

---

## 1. Review Title and Registration

**Title:** Trastuzumab Deruxtecan (T-DXd) vs Physician-Choice Chemotherapy in HER2-Low (IHC 1+ or 2+/ISH-negative) Metastatic Breast Cancer: A Living Systematic Review and Meta-Analysis of the DESTINY-Breast04 and DESTINY-Breast06 Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding).

**Corresponding address:** drmahmoodclinic@pm.me (GMC 6071047), Royal Free Hospital and Barnet Hospital, London, UK.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with HER2-low (IHC 1+ or 2+/ISH-negative) unresectable/metastatic breast cancer; DESTINY-Breast04 = previously chemotherapy-treated; DESTINY-Breast06 = endocrine-therapy-treated, chemotherapy-naive in metastatic setting |
| **Intervention** | Trastuzumab deruxtecan 5.4 mg/kg IV every 3 weeks |
| **Comparator** | Physician-choice single-agent chemotherapy (capecitabine, eribulin, gemcitabine, paclitaxel, nab-paclitaxel) |
| **Outcome (primary)** | Progression-free survival (BICR-adjudicated) in the pre-specified primary-analysis population |

---

## 3. Eligibility / Search / Selection

Inclusion: phase III pivotal, HER2-low mBC, T-DXd at licensed dose, physician-choice chemotherapy comparator, BICR PFS primary. Exclusion: HER2-positive mBC (separate DESTINY-Breast03 review), non-metastatic / adjuvant T-DXd (separate DESTINY-Breast05 / adjuvant ongoing), gastric / other tumours. Two-reviewer adjudication with HMAC-signed seal; PRISMA 2020.

---

## 6-7. Data Extraction + RoB

PFS HR, OS HR, ORR, safety (ILD, neutropenia, nausea), RoB 2. Design-based priors: D2 SOME CONCERNS (open-label by necessity; T-DXd IV vs physician-choice chemo); other domains LOW.

---

## 8. Synthesis / Statistical Methods

- DerSimonian-Laird random-effects IVW on log-HR scale for PFS.
- HKSJ t-df=k-1 with `max(1, Q/(k-1))` floor.
- PI suppressed at k=2.
- Subgroup: HR+ vs HR-, prior chemotherapy status, HER2-ultralow stratum (DESTINY-Breast06 only).
- Trim-and-fill sensitivity at k<10 low-power caveat.
- Bayesian half-normal(0, 0.5) prior on tau.
- **Browser-hosted WebR cross-validation (optional, user-triggered)** via the Analysis tab button.

---

## 9-10. GRADE / Reporting

Standard GRADE with population indirectness note (post-chemotherapy vs post-endocrine cohorts differ in prior-therapy context).

---

## 11. Living-MA Update Cadence

Formal 3-monthly cadence; DESTINY-Breast05 (adjuvant, ongoing), DESTINY-Breast09 (frontline), DESTINY-PanTumor02, and HER2-ultralow-specific trials trigger amendment.

---

## Appendix A. AMSTAR-2 Critical-Domain Self-Assessment

| # | Domain | Self-rating | Evidence |
|---|---|---|---|
| 2 | Registered protocol | Yes (partial) | GitHub-canonical-URL freeze |
| 4 | Search strategy | Yes | §4 |
| 7 | Excluded-studies list | Yes | Screening tab |
| 9 | RoB assessment | Yes | Authors have double-checked screening and data extraction against the record excerpts shown in the Extraction tab; provisional AI-drafted RoB-2 is now author-confirmed. Formal dual-assessor RoB-2 remains a per-submission step. |
| 11 | Statistical methods | Yes | §8 |
| 13 | RoB in interpretation | Partial | GRADE §9 |
| 15 | Publication bias | Yes (k-appropriate) | k=2 formal tests suppressed |
| 1 | PICO | Yes | §2 |

---

## Changelog
- **v1.1** (2026-04-20) — Initial editor-review-revision release.
