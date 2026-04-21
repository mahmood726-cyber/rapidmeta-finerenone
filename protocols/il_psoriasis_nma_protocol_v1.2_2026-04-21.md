---
title: "IL-17 / IL-23 Biologics NMA in Plaque Psoriasis"
slug: il_psoriasis_nma
version: 1.2
timestamp: 2026-04-21T00:00:00Z
date: 2026-04-21
specialty: Dermatology
analysis_type: NMA
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/il_psoriasis_nma_protocol_v1.2_2026-04-21.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/IL_PSORIASIS_NMA_REVIEW.html
license: MIT
---

# IL-17 / IL-23 Biologics NMA in Plaque Psoriasis
## A Living Systematic Review and Network Meta-Analysis Protocol

**Version:** 1.2 · **Frozen:** 2026-04-21 · **Authors:** Mahmood Ahmad

---

## 1. Title and Registration

Network Meta-Analysis of IL-17 (Ixekizumab, Secukinumab, Bimekizumab) and IL-23 (Guselkumab, Risankizumab) Biologics vs Placebo + TNFi Active Comparators in Moderate-to-Severe Plaque Psoriasis. Protocol frozen 2026-04-21.

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with moderate-to-severe plaque psoriasis (PASI ≥12, BSA ≥10%, IGA ≥3) |
| **Interventions (5 biologics + 2 active comparators)** | Guselkumab · Risankizumab · Ixekizumab · Secukinumab · Bimekizumab · Adalimumab · Etanercept |
| **Comparator** | Placebo (reference) |
| **Outcome (primary)** | PASI 90 response at week 10–16 (primary timepoint varies by agent); **odds ratio (OR)** — Cochrane convention; RR unstable at low placebo rates |

## 3. Network (v1.2)

| Edge | Trial (NCT) | Comparison | OR |
|---|---|---|---|
| Guselkumab — Placebo | VOYAGE 1 (NCT02207231) | wk 16 | 86.8 |
| Risankizumab — Placebo | UltIMMa-1 (NCT02684370) | wk 16 | 74.8 |
| Ixekizumab — Placebo | UNCOVER-1 (NCT01474512) | wk 12 | 252.2 |
| Ixekizumab — Etanercept | UNCOVER-2 (NCT01597245) | wk 12 | 5.3 |
| Ixekizumab — Placebo | UNCOVER-3 (NCT01646177) | wk 12 | 63.6 |
| Secukinumab — Placebo | ERASURE (NCT01365455) | wk 12 | 314.1 |
| Secukinumab — Etanercept | FIXTURE (NCT01358578) | wk 12 | 6.4 |
| Bimekizumab — Secukinumab | BE RADIANT (NCT03536884) | wk 16 | 1.6 |
| Bimekizumab — Placebo | BE VIVID (NCT03370133) | wk 16 | 88.6 |
| Bimekizumab — Adalimumab | BE SURE (NCT03412747) | wk 16 | 4.0 |

**Geometry:** Star through Placebo + multiple active-comparator edges (to Eta, Ada, Secu) + head-to-head (Bime–Secu). k = 10. Closed loops exist → consistency tests informative.

## 4. Synthesis

- `netmeta` 3.2.0, `sm="OR"`, REML τ², HKSJ CI
- Reference = Placebo
- Consistency: design-by-treatment Q_inc = 3.58 (df=2, p = 0.17) **CONSISTENT**
- Ranking: SUCRA via mvrnorm MC (N=100k)

## 5. Transitivity

| Effect modifier | Clinical concern | Declared |
|---|---|---|
| Primary timepoint | wk 12 (UNCOVER/ERASURE/FIXTURE) vs wk 16 (others) — IL-23s still climbing at wk 12 | **Moderate** — pre-specified heterogeneity downgrade; v1.3 roadmap adds wk-16-common subset |
| Baseline severity | PASI ≥12 all trials | Compatible |
| Prior biologic exposure | Mixed bio-naive / bio-experienced | Declared; bio-naive subgroup sensitivity planned |
| Primary PASI cutoff | PASI 90 all trials | Compatible |
| Continuity correction | UNCOVER-1/ERASURE have placebo event 2 cells (0.5 added) | Declared |

## 6. CINeMA GRADE-NMA

| Comparison | Within | Across | Indirectness | Imprecision | Heterogeneity | Incoherence | Pub bias | **Certainty** |
|---|---|---|---|---|---|---|---|---|
| Bimekizumab vs Placebo (indirect) | Moderate | Low | Moderate (indirect + wk-16/12 mix) | Low | Moderate (τ²=0.21) | Low (p=0.17) | Low | **MODERATE** |
| Ixekizumab vs Placebo | Low | Low | Low | Low | Moderate | Low | Low | **MODERATE-HIGH** |
| Secukinumab vs Placebo | Low | Low | Low | Low | Moderate | Low | Low | **MODERATE-HIGH** |
| Guselkumab vs Placebo | Low | Low | Moderate (wk 16 IL-23 kinetics) | Low | Moderate | Low | Low | **MODERATE** |
| Risankizumab vs Placebo | Low | Low | Moderate | Moderate (single trial, wide CI) | Moderate | Low | Low | **MODERATE** |
| Bimekizumab vs Ixekizumab (indirect) | Low | Low | Moderate | Low | Moderate | Low | Low | **MODERATE** |

## 7. Living-NMA cadence

3-monthly. Triggers: IXORA-R (ixekizumab vs guselkumab head-to-head), ECLIPSE (guselkumab vs secukinumab), IMMhance (risankizumab continuation).

## 8. Reporting

PRISMA-NMA 2020 + CONSORT-Harms for Candida mucocutaneous (bimekizumab ~19%), injection-site reactions, IBD exacerbation with IL-17.

## Changelog

- **v1.2** (2026-04-21) — First dedicated protocol; k expanded to 10; OR scale (Cochrane-standard; RR inflation resolved).
