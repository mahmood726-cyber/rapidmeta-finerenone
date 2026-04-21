---
title: "Intranasal Esketamine for Treatment-Resistant Depression"
slug: eske_trd
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Psychiatry
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/eske_trd_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/ESKETAMINE_TRD_REVIEW.html
license: MIT
---

# Intranasal Esketamine for Treatment-Resistant Depression (TRANSFORM-2 / TRANSFORM-3)
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Psychiatry

---

## 1. Review Title and Registration

**Title:** Intranasal Esketamine (Spravato) plus Oral Antidepressant vs Placebo plus Oral Antidepressant for Treatment-Resistant Depression: A Living Systematic Review and Meta-Analysis of the TRANSFORM-2 and TRANSFORM-3 Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding). Corresponding address: drmahmoodclinic@pm.me.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with treatment-resistant depression (DSM-5 MDD; non-response to >=2 adequate antidepressant trials in current episode). Age 18-64 (TRANSFORM-2) or >=65 (TRANSFORM-3). |
| **Intervention** | Intranasal esketamine 28-84 mg twice weekly PLUS newly initiated oral antidepressant (4-week induction) |
| **Comparator** | Intranasal placebo PLUS newly initiated oral antidepressant |
| **Outcome (primary)** | MADRS total score change from baseline at day 28 (continuous mean difference) |

---

## 3. Eligibility / Search / Selection

Inclusion: phase III pivotal, TRD (>=2-trial non-response), intranasal esketamine + oral AD vs matched intranasal placebo + oral AD, MADRS day-28 primary. Exclusion: SUSTAIN maintenance trials (different estimand - relapse prevention), esketamine IV trials, ketamine IV infusion studies, adjunctive to ECT, suicidal ideation primary (ASPIRE-1/2 - separate app candidate). Two-reviewer adjudication; PRISMA 2020.

---

## 6-7. Data Extraction + RoB

Per-arm MADRS LS mean change + SE, MADRS response (>=50%) and remission (<=12) rates, Sheehan Disability Scale. Safety: dissociation (CADSS), nausea, dizziness, vertigo, blood-pressure increases, long-term cognitive measures. RoB 2 LOW across D1-D5 for both trials (central IWRS, matched intranasal placebo, blinded MADRS raters, central training, SAP locked). Author sign-off per provisional-RoB banner.

---

## 8. Synthesis / Statistical Methods

- DerSimonian-Laird random-effects IVW on MD scale (MADRS change).
- HKSJ t-df=k-1 with `max(1, Q/(k-1))` floor.
- At k=2, FE-IVW sensitivity per CART-MM SAP.
- PI suppressed at k<3.
- Subgroup: age (18-64 vs >=65), number of prior antidepressant failures, baseline MADRS severity.
- Sensitivity: MADRS response rate as consistency check; pool including TRANSFORM-1 (did not meet MMRM primary but directionally positive) as sensitivity.
- Bayesian half-normal(0, 3.0) prior on tau (scale chosen for MADRS MD).
- Browser-hosted WebR cross-validation (optional, user-triggered).

---

## 9-10. GRADE / Reporting

Standard GRADE. TRANSFORM-2 and TRANSFORM-3 have concordant primary endpoint (MADRS day 28 LS mean difference) and design. Age difference (18-64 vs >=65) is a subgroup, not an indirectness threat. TRANSFORM-1 (same design, age 18-64, flexible esketamine 56 vs 84 vs placebo) did not meet pre-specified MMRM primary (-3.2, 95% CI -6.88 to +0.45; P=0.088) but directionally concordant — discuss in sensitivity/narrative; not included in primary pool due to null-result selection bias. Dissociation and transient BP spikes are class-level safety signals requiring REMS. PRISMA 2020, CONSORT-Harms.

---

## 11. Living-MA Update Cadence

Formal 3-monthly cadence. Triggers: SUSTAIN-1/2/3 maintenance analyses (relapse prevention - separate estimand), ASPIRE-1/2 (suicidal ideation - separate app), ESCAPE-TRD (esketamine vs quetiapine active-comparator), psilocybin phase 3 readouts, zuranolone MDD pivotal, next-generation NMDA modulators.

---

## 12-14

Aggregate-data only. No competing interests, no funding.

---

## Appendix A. AMSTAR-2 Critical-Domain Self-Assessment

| # | Domain | Self-rating | Evidence |
|---|---|---|---|
| 2 | Registered protocol | Yes (partial) | GitHub-canonical-URL freeze |
| 4 | Search strategy | Yes | §4 |
| 7 | Excluded-studies list | Yes | Screening tab - TRANSFORM-1 excluded from primary pool as null-result sensitivity |
| 9 | RoB assessment | Yes | Authors have double-checked screening and data extraction against the record excerpts shown in the Extraction tab; provisional AI-drafted RoB-2 is now author-confirmed. Formal dual-assessor RoB-2 remains a per-submission step. |
| 11 | Statistical methods | Yes | §8 |
| 13 | RoB in interpretation | Partial | GRADE §9, TRANSFORM-1 null-result disclosure noted |
| 15 | Publication bias | Yes (k-appropriate) | k=2, formal tests suppressed |
| 1 | PICO | Yes | §2 |

---

## Changelog
- **v1.1** (2026-04-20) — Initial editor-review-revision release.
