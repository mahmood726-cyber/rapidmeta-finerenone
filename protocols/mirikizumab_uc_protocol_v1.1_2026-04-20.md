---
title: "Mirikizumab for Moderate-to-Severe Ulcerative Colitis"
slug: mirikizumab_uc
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Gastroenterology
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/mirikizumab_uc_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/MIRIKIZUMAB_UC_REVIEW.html
license: MIT
---

# Mirikizumab for Moderate-to-Severe Ulcerative Colitis (LUCENT Programme)
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Gastroenterology

---

## 1. Review Title and Registration

**Title:** Mirikizumab (Selective IL-23 p19 Inhibitor) for Moderate-to-Severe Ulcerative Colitis: A Living Systematic Review and Meta-Analysis of the LUCENT-1 Induction and LUCENT-2 Maintenance Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding). Corresponding address: drmahmoodclinic@pm.me.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with moderate-severe UC (modified Mayo 4-9) with inadequate response / intolerance to conventional or biologic therapy |
| **Intervention** | Mirikizumab 300 mg IV induction (wk 0/4/8) + 200 mg SC Q4W maintenance |
| **Comparator** | Matched placebo |
| **Outcome (primary)** | Clinical remission at the trial-specific timepoint (wk 12 induction; wk 40 maintenance) |

---

## 3. Eligibility / Search / Selection

Inclusion: phase III pivotal, moderate-severe UC, mirikizumab at licensed regimen, placebo comparator. Exclusion: Crohn's disease (separate RISANKIZUMAB_CD review), psoriasis, paediatric UC. Two-reviewer adjudication; PRISMA 2020.

---

## 6-7. Data Extraction + RoB

Clinical remission counts, endoscopic remission, corticosteroid-free remission, biologic-failure stratification. RoB 2 LOW across D1-D5 (double-blind, central endoscopy, SAP locked). Author sign-off per provisional-RoB banner.

---

## 8. Synthesis / Statistical Methods

- DerSimonian-Laird random-effects IVW on log-OR / log-RR scale for clinical remission.
- HKSJ t-df=k-1 with `max(1, Q/(k-1))` floor.
- At k=2 (induction + maintenance), FE-IVW sensitivity per CART-MM SAP.
- PI suppressed at k<3.
- Subgroup: biologic-failure vs biologic-naive, baseline Mayo severity.
- Zero-cell conditional 0.5 correction.
- Bayesian half-normal(0, 0.5) prior on tau.
- Browser-hosted WebR cross-validation (optional, user-triggered).

---

## 9-10. GRADE / Reporting

Standard GRADE. Induction and maintenance are different clinical phases; pool primarily for class-level IL-23 UC efficacy but prefer trial-specific inference. No external IPD MA at freeze.

---

## 11. Living-MA Update Cadence

Formal 3-monthly cadence. Triggers: long-term SHINE-1/2 extensions; head-to-head IL-23 vs TNFi vs JAK trials (VEGA, SEQUENCE-like); paediatric UC trials.

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
| 13 | RoB in interpretation | Partial | GRADE §9 |
| 15 | Publication bias | Yes (k-appropriate) | k=2, formal tests suppressed |
| 1 | PICO | Yes | §2 |

---

## Changelog
- **v1.1** (2026-04-20) — Initial editor-review-revision release.
