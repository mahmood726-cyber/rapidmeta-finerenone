---
title: "Dupilumab for Moderate-to-Severe COPD with Type 2 Inflammation"
slug: dupi_copd
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Respiratory
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/dupilumab_copd_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/DUPILUMAB_COPD_REVIEW.html
license: MIT
---

# Dupilumab for Moderate-to-Severe COPD with Type 2 Inflammation
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Respiratory

---

## 1. Review Title and Registration

**Title:** Dupilumab (IL-4Ralpha Monoclonal Antibody) for Moderate-to-Severe COPD with Type 2 Inflammation (Blood Eosinophils >=300/uL): A Living Systematic Review and Meta-Analysis of the BOREAS and NOTUS Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding). Corresponding address: drmahmoodclinic@pm.me.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with moderate-severe COPD on stable triple inhaled therapy (ICS + LABA + LAMA), symptomatic (CAT >=10), post-bronchodilator FEV1 30-80% predicted, current/former smokers, blood eosinophils >=300/uL |
| **Intervention** | Dupilumab 300 mg SC every 2 weeks |
| **Comparator** | Matched placebo |
| **Outcome (primary)** | Annualized rate of moderate or severe COPD exacerbations at week 52 |

---

## 3. Eligibility / Search / Selection

Inclusion: phase III pivotal, COPD with type 2 inflammation biomarker (eos >=300/uL), dupilumab at licensed dose, placebo comparator, moderate/severe exacerbation primary. Exclusion: asthma-COPD overlap without pre-specified COPD subset, phase II dose-finding. Two-reviewer adjudication; PRISMA 2020.

---

## 6-7. Data Extraction + RoB

Per-arm exacerbation event counts, FEV1 MD + SE, SGRQ, E-RS:COPD, safety. RoB 2 priors: LOW across D1-D5 (double-blind, central exacerbation adjudication, SAP locked). Author sign-off per provisional-RoB banner.

---

## 8. Synthesis / Statistical Methods

- DerSimonian-Laird random-effects IVW on log-rate-ratio scale for exacerbations.
- HKSJ t-df=k-1 with `max(1, Q/(k-1))` floor.
- At k=2, FE-IVW sensitivity pool per CART-MM SAP.
- PI suppressed at k<3.
- Subgroup: blood-eosinophil strata (300-500 vs >=500), smoking-status, baseline ICS/LABA/LAMA.
- Zero-cell conditional 0.5 correction.
- Trim-and-fill sensitivity at k<10 (low-power caveat).
- Bayesian half-normal(0, 0.5) prior on tau.
- Browser-hosted WebR cross-validation (optional, user-triggered).

---

## 9-10. GRADE / Reporting

Standard GRADE. BOREAS (RR 0.70) and NOTUS (RR 0.66) are highly consistent; pool expected with narrow CI and HIGH certainty. No external IPD MA at freeze; internal DL pool is the reference.

---

## 11. Living-MA Update Cadence

Formal 3-monthly cadence. Triggers: long-term open-label extensions; itepekimab (IL-33 mAb) AERIFY-1/2; tezepelumab COPD phase 3 (COURSE); other type-2-biologic COPD trials.

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
