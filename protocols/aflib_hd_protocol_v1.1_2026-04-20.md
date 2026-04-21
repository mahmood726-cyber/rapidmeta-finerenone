---
title: "Aflibercept 8 mg High-Dose for nAMD and DME"
slug: aflib_hd
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Ophthalmology
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/aflib_hd_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/AFLIBERCEPT_HD_REVIEW.html
license: MIT
---

# Aflibercept 8 mg High-Dose for nAMD and DME (PULSAR / PHOTON)
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Ophthalmology

---

## 1. Review Title and Registration

**Title:** Aflibercept 8 mg (High-Dose Anti-VEGF) with Extended Q12W/Q16W Dosing vs Aflibercept 2 mg Q8W in Neovascular Age-Related Macular Degeneration (PULSAR) and Diabetic Macular Edema (PHOTON): A Living Systematic Review and Meta-Analysis of Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding). Corresponding address: drmahmoodclinic@pm.me.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with treatment-naive neovascular AMD (PULSAR) or DME with visual-acuity impairment (PHOTON) |
| **Intervention** | Aflibercept 8 mg intravitreal Q12W or Q16W (after 3-dose monthly loading) |
| **Comparator** | Aflibercept 2 mg intravitreal Q8W |
| **Outcome (primary)** | BCVA letter-score change from baseline at week 48 (continuous, non-inferiority margin -4 letters) |

---

## 3. Eligibility / Search / Selection

Inclusion: phase III pivotal, treatment-naive nAMD or DME with baseline BCVA impairment, aflibercept 8 mg IVT Q12W/Q16W vs 2 mg Q8W, BCVA week-48 primary. Exclusion: phase II dose-finding, wet AMD with subretinal fibrosis, DR without DME. Two-reviewer adjudication; PRISMA 2020.

---

## 6-7. Data Extraction + RoB

Per-arm BCVA letter-score change + SE (non-inferiority MD scale), central subfield thickness, dosing-interval maintenance, injections over 48 weeks. Safety: intraocular inflammation, endophthalmitis, IOP elevation, retinal vasculitis. RoB 2 LOW across D1-D5 (central IVR randomization, double-blind with matched syringe volume, central reading centre, SAP locked). Author sign-off per provisional-RoB banner.

---

## 8. Synthesis / Statistical Methods

- DerSimonian-Laird random-effects IVW on MD scale (BCVA letters).
- HKSJ t-df=k-1 with `max(1, Q/(k-1))` floor.
- At k=2, FE-IVW sensitivity per CART-MM SAP.
- PI suppressed at k<3.
- Subgroup: indication (nAMD vs DME), dosing interval (Q12W vs Q16W).
- Sensitivity: BCVA at week 96 (2-year maintained benefit) when available.
- Bayesian half-normal(0, 1.0) prior on tau (scale chosen for BCVA MD).
- Browser-hosted WebR cross-validation (optional, user-triggered).

---

## 9-10. GRADE / Reporting

Standard GRADE. Pooling nAMD and DME is permissible for class-level anti-VEGF dose-optimisation but populations differ (exudative vs leakage-driven disease) — indirectness downgrade candidate. Both PULSAR and PHOTON met non-inferiority. Q16W arm is a secondary comparison. Injection-burden reduction is the clinical value proposition — document in the Living-MA text rather than a separate outcome. PRISMA 2020, CONSORT-Harms.

---

## 11. Living-MA Update Cadence

Formal 3-monthly cadence. Triggers: PULSAR 96-week readout, PHOTON 96-week readout, faricimab head-to-head (TENAYA/LUCERNE vs PULSAR class comparisons), next-generation anti-VEGF biosimilars.

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
| 13 | RoB in interpretation | Partial | GRADE §9, nAMD/DME indirectness noted |
| 15 | Publication bias | Yes (k-appropriate) | k=2, formal tests suppressed |
| 1 | PICO | Yes | §2 |

---

## Changelog
- **v1.1** (2026-04-20) — Initial editor-review-revision release.
