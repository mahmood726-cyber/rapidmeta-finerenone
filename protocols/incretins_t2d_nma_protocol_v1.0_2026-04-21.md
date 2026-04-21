---
title: "Incretin Class NMA in Type 2 Diabetes"
slug: incretins_t2d_nma
version: 1.0
timestamp: 2026-04-21T00:00:00Z
date: 2026-04-21
specialty: Endocrinology (Diabetes)
analysis_type: NMA
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/incretins_t2d_nma_protocol_v1.0_2026-04-21.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/INCRETINS_T2D_NMA_REVIEW.html
license: MIT
---

# Incretin Class NMA in T2D (SURPASS / SUSTAIN / LEAD / AWARD)
## Network Meta-Analysis Protocol

**Version:** 1.0 · **Frozen:** 2026-04-21 · **Authors:** Mahmood Ahmad (drmahmoodclinic@pm.me)

## 1. Title + Registration

Network Meta-Analysis of Incretin-Based Therapies (Tirzepatide, Semaglutide, Dulaglutide, Liraglutide, Exenatide) vs Placebo for Glycaemic Control in Type 2 Diabetes.

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with type 2 diabetes on background metformin ± other oral agents |
| **Interventions (5 incretins)** | Tirzepatide 15 mg SC weekly (dual GIP/GLP-1) · Semaglutide 1 mg SC weekly · Dulaglutide 1.5 mg SC weekly · Liraglutide 1.8 mg SC daily · Exenatide (ER 2 mg weekly or BID 10 mcg — see transitivity) |
| **Comparator** | Placebo |
| **Outcome (primary)** | HbA1c change from baseline at the trial-primary timepoint (26–40 weeks); **mean difference (MD, %)** |

## 3. Network

| Edge | Trial | MD | Direction |
|---|---|---|---|
| Tirzepatide — Placebo | SURPASS-1 (NCT03954834) | −2.11 | Tirz better |
| Tirzepatide — Semaglutide | SURPASS-2 (NCT03987919) | −0.45 | Tirz better (head-to-head) |
| Semaglutide — Placebo | SUSTAIN-1 (NCT02054897) | −1.55 | Sema better |
| Semaglutide — Exenatide | SUSTAIN-3 (NCT01885208) | −0.62 | Sema better (vs Exenatide-ER) |
| Semaglutide — Dulaglutide | SUSTAIN-7 (NCT02648204) | −0.31 | Sema better (head-to-head) |
| Liraglutide — Exenatide | LEAD-6 (NCT00518882) | −0.33 | Lira better (vs Exenatide-BID) |
| Dulaglutide — Liraglutide | AWARD-6 (NCT01624259) | −0.06 | non-inferior |

**Geometry:** Rich network with **one 4-node closed loop** (Sema–Dula–Lira–Exe–Sema) enabling consistency testing. Tirzepatide anchored to Placebo (SURPASS-1) and to Semaglutide (SURPASS-2).

## 4. Synthesis

- `netmeta` 3.2.0, `sm="MD"`, REML τ², HKSJ CI
- Reference = Placebo
- Consistency: design-by-treatment Wald + node-splitting + loop-specific incoherence test
- Ranking: SUCRA via mvrnorm MC (N=100,000) + P-score (netrank)

## 5. Key results (v1.0)

**HbA1c MD vs Placebo (random-effects):**

| Treatment | MD (%) | 95% CI |
|---|---:|---:|
| **Tirzepatide** | **−2.05** | (−2.21, −1.89) |
| **Semaglutide** | **−1.59** | (−1.74, −1.43) |
| Dulaglutide | −1.29 | (−1.47, −1.11) |
| Liraglutide | −1.24 | (−1.45, −1.04) |
| Exenatide (composite) | −0.94 | (−1.14, −0.73) |

**Consistency:** τ² = 0, I² = 0%, Q_inc = 0.75 (df=2, **p = 0.69**) → **CONSISTENT**.

**SUCRA:** Tirz 1.00 · Sema 0.80 · Dula 0.53 · Lira 0.47 · Exe 0.20 · Placebo 0.00. Tirzepatide rank-1 probability **100%**; Semaglutide rank-2 probability 99.9%.

## 6. Transitivity

| Effect modifier | Concern | Declared |
|---|---|---|
| Primary timepoint | 26 wk (LEAD-6, AWARD-6) vs 30–56 wk (SUSTAIN, SURPASS) | Low — HbA1c plateau typically reached by wk 12-16 |
| Background therapy | Mostly metformin-dominant | Compatible |
| Baseline HbA1c | 7.5–9.5% range across trials | Similar |
| Population age | 52–59 years median | Similar |
| **Exenatide composite** (ER in SUSTAIN-3 vs BID in LEAD-6) | Different PK profiles | **Moderate** — declared; v1.1 may split into Exe_ER + Exe_BID |
| Drug-naive vs background | Drug-naive (SURPASS-1, SUSTAIN-1) vs background (others) | Compatible after baseline-HbA1c adjustment |

## 7. CINeMA GRADE-NMA

| Comparison | Within | Across | Indirectness | Imprecision | Heterogeneity | Incoherence | Pub bias | **Certainty** |
|---|---|---|---|---|---|---|---|---|
| Tirz vs Placebo (direct) | Low | Low | Low | Low | Low | n/a | Low | **HIGH** |
| Tirz vs Sema (direct) | Low | Low | Low | Low | Low | n/a | Low | **HIGH** |
| Sema vs Placebo (direct) | Low | Low | Low | Low | Low | n/a | Low | **HIGH** |
| Dula vs Lira (direct) | Low | Low | Low | Low | Low | n/a | Low | **HIGH** |
| Sema vs Dula (direct) | Low | Low | Low | Low | Low | n/a | Low | **HIGH** |
| Sema vs Exe (direct) | Low | Low | Moderate (Exenatide composite) | Low | Low | Low (p=0.69) | Low | **MODERATE-HIGH** |
| Lira vs Exe (direct) | Low | Low | Moderate (Exe composite) | Low | Low | Low | Low | **MODERATE-HIGH** |
| Tirz vs Dula (indirect via Sema) | Low | Low | Moderate | Low | Low | Low | Low | **MODERATE-HIGH** |
| Tirz vs Lira (indirect) | Low | Low | Moderate | Low | Low | Low | Low | **MODERATE** |
| Tirz vs Exe (indirect) | Low | Low | Moderate-Serious | Low | Low | Low | Low | **MODERATE** |

## 8. Living-NMA cadence

3-monthly. Triggers: SURPASS-6 (vs insulin lispro), SURPASS-CVOT, tirzepatide oral formulation trials, orforglipron oral GLP-1, retatrutide (triple-agonist).

## 9. Reporting

PRISMA-NMA 2020 + CONSORT-Harms: GI AEs (nausea, diarrhoea — class effect; tirzepatide ≈ semaglutide intensity), pancreatitis signal, thyroid C-cell hyperplasia (boxed warning), retinopathy worsening (semaglutide).

## Changelog

- **v1.0** (2026-04-21) — First release; 7 pivotal phase 3 RCTs; one closed consistency loop; network consistent at p=0.69.
