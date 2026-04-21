---
title: "JAK Inhibitors in Atopic Dermatitis"
slug: jaki_ad
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Dermatology
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/jaki_ad_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/JAKI_AD_REVIEW.html
license: MIT
---

# JAK Inhibitors (Abrocitinib + Upadacitinib) Monotherapy AD (JADE MONO-1/2 / MEASURE-UP 1/2)
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Dermatology

---

## 1. Review Title and Registration

**Title:** JAK Inhibitors (Abrocitinib and Upadacitinib) as Monotherapy for Moderate-to-Severe Atopic Dermatitis: A Living Systematic Review and Meta-Analysis of the JADE MONO-1, JADE MONO-2, MEASURE-UP 1, and MEASURE-UP 2 Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**. **Authors:** Mahmood Ahmad (corresponding). drmahmoodclinic@pm.me.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adolescents and adults (age >=12) with moderate-to-severe atopic dermatitis (EASI >=16, IGA >=3, BSA >=10%) |
| **Intervention** | Abrocitinib 200 mg or upadacitinib 30 mg orally daily (monotherapy; topicals discontinued) |
| **Comparator** | Matched placebo |
| **Outcome (primary)** | IGA 0/1 with >=2-grade improvement at week 12 (abrocitinib) or week 16 (upadacitinib); RR |

---

## 3. Eligibility / Search / Selection

Inclusion: phase III pivotal, moderate-severe AD, highest-phase-3-dose JAKi vs placebo monotherapy, IGA 0/1 primary. Exclusion: combination with topicals (JADE COMPARE, JADE REGIMEN, HEADS-UP active-comparator upa vs dupi — separate app candidate for head-to-head); paediatric-only trials (JADE TEEN); baricitinib trials (BREEZE-AD — separate app candidate); phase II. Two-reviewer adjudication; PRISMA 2020.

---

## 6-7. Data Extraction + RoB

Per-arm IGA 0/1 counts + RR, EASI-75 (co-primary), PP-NRS >=4-point itch response, serious infections, herpes zoster, CPK elevation, thrombocytopaenia, acne. RoB 2 LOW across D1-D5 for all 4 trials (central IVR, double-blind matched placebo, central IGA rater training, SAP locked). Class-level boxed warning (MACE/thrombosis/malignancy based on tofacitinib ORAL-Surveillance pooled signal) applies to long-term safety monitoring. Author sign-off per provisional-RoB banner.

---

## 8. Synthesis

- DerSimonian-Laird RE IVW on log-RR; HKSJ t-df=k-1 with floor; PI computable at k=4.
- Subgroup: agent (abrocitinib vs upadacitinib), adolescent vs adult, baseline disease severity (IGA 3 vs 4).
- Sensitivity: EASI-75 as consistency check; dose-specific (abro 100 vs 200; upa 15 vs 30) sub-pools.
- Bayesian half-normal(0, 0.5) prior on tau (log-RR).

---

## 9-10. GRADE / Reporting

Standard GRADE. Class-level JAKi pool across 2 agents (both JAK1-selective) at highest phase 3 dose. Primary endpoint timepoint differs (wk 12 abrocitinib vs wk 16 upadacitinib) - minor indirectness. Effect highly consistent across agents (RR 4.25-11.16, all favouring JAKi). Safety: class-level boxed warning applies (tofacitinib ORAL-Surveillance); long-term MACE/thrombosis/malignancy surveillance required. PRISMA 2020, CONSORT-Harms.

---

## 11. Living-MA Update Cadence

3-monthly. Triggers: baricitinib (BREEZE-AD) pooled inclusion, paediatric extension (JADE TEEN, Measure-Up teens), oral GLP-1 orforglipron, next-generation TYK2-selective (deucravacitinib AD ph3 ECZTEND), OX40 axis biologics (amlitelimab, rocatinlimab).

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
| 13 | RoB interpretation | Partial | Agent + timepoint indirectness noted; class boxed warning flagged |
| 15 | Publication bias | Yes | k=4, formal tests + funnel |

---
## Changelog
- **v1.1** (2026-04-20) — Initial editor-review-revision release.
