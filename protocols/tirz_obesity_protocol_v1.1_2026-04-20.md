---
title: "Tirzepatide for Weight Management (SURMOUNT)"
slug: tirz_obesity
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Endocrinology (Obesity)
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/tirz_obesity_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/TIRZEPATIDE_OBESITY_REVIEW.html
license: MIT
---

# Tirzepatide 15 mg for Obesity (SURMOUNT-1 / SURMOUNT-2 / SURMOUNT-3)
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Endocrinology (Obesity)

---

## 1. Review Title and Registration

**Title:** Tirzepatide (Dual GIP/GLP-1 Receptor Agonist) 15 mg for Weight Management in Adults with Obesity (With or Without Type 2 Diabetes): A Living Systematic Review and Meta-Analysis of the SURMOUNT-1, SURMOUNT-2, and SURMOUNT-3 Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**. **Authors:** Mahmood Ahmad (corresponding). drmahmoodclinic@pm.me.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with BMI >=30 (or >=27 + comorbidity), with T2D (SURMOUNT-2) or without (SURMOUNT-1, SURMOUNT-3 post-lifestyle lead-in) |
| **Intervention** | Tirzepatide 15 mg subcutaneous weekly (with max-tolerated in SURMOUNT-3) |
| **Comparator** | Matched placebo |
| **Outcome (primary)** | Percent change in body weight from baseline at week 72; mean difference (MD) |

---

## 3. Eligibility / Search / Selection

Inclusion: phase III pivotal, adults with obesity, tirzepatide 15 mg (or max-tolerated) vs placebo, % weight change at 72 weeks primary. Exclusion: SURMOUNT-4 withdrawal design (different primary estimand: post-run-in weight change); tirzepatide in other indications (SURPASS T2D-glycaemic trials — separate TIRZEPATIDE_T2D app); SURMOUNT-5 (head-to-head vs semaglutide 2.4 — NMA candidate). Two-reviewer adjudication; PRISMA 2020.

---

## 6-7. Data Extraction + RoB

Per-arm % weight change + SE (primary), categorical weight-loss thresholds (>=5% / >=10% / >=15% / >=20%), HbA1c (T2D subcohort), CV biomarkers, GI AEs, discontinuation. RoB 2 LOW across D1-D5 for all 3 trials (central IVR, double-blind matched placebo, central lab, SAP locked). Author sign-off per provisional-RoB banner.

---

## 8. Synthesis

- DerSimonian-Laird RE IVW on MD scale; HKSJ t-df=k-1 with floor; PI computable at k=3.
- Subgroup: T2D-present vs T2D-absent; lifestyle lead-in present vs absent; baseline BMI strata.
- Sensitivity: SURMOUNT-1 only (non-T2D reference); SURMOUNT-1 + SURMOUNT-2 (pre-lead-in populations).
- Bayesian half-normal(0, 5) prior on tau (MD scale).

---

## 9-10. GRADE / Reporting

Standard GRADE. Same-drug pool but across substantively distinct populations — T2D attenuates weight-loss effect (SURMOUNT-2 MD -11.5% vs SURMOUNT-1 -17.8%), lifestyle lead-in amplifies it (SURMOUNT-3 MD -20.9%). Between-trial tau2 is very high (~20 percentage-points-squared); pooled estimate therefore has wide HKSJ CI. Population-stratified inference is the preferred clinical surface. Compared with GLP-1 monotherapy (STEP-1 semaglutide 2.4 mg MD -12.4%), tirzepatide 15 mg shows larger magnitude; head-to-head SURMOUNT-5 and the NMA approach give the definitive comparative estimate.

---

## 11. Living-MA Update Cadence

3-monthly. Triggers: SURMOUNT-4 maintenance, SURMOUNT-5 head-to-head vs semaglutide, SURMOUNT-MMO (CV-outcomes), retatrutide phase 3, oral GLP-1 orforglipron phase 3.

---

## 12-14
Aggregate-data only. No CoI, no funding.

---

## Appendix A. AMSTAR-2

| # | Domain | Rating | Evidence |
|---|---|---|---|
| 1 | PICO | Yes | §2 |
| 2 | Registered protocol | Yes (partial) | GitHub-canonical-URL freeze |
| 4 | Search strategy | Yes | §4 |
| 7 | Excluded-studies list | Yes | Screening tab |
| 9 | RoB | Yes | Author-confirmed provisional |
| 11 | Statistical methods | Yes | §8 |
| 13 | RoB interpretation | Partial | Population-heterogeneity indirectness noted |
| 15 | Publication bias | Yes (k-appropriate) | k=3 |

---
## Changelog
- **v1.1** (2026-04-20) — Initial editor-review-revision release.
