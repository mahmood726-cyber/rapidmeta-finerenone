---
title: "Anti-VEGF Class NMA in Neovascular AMD"
slug: antivegf_namd_nma
version: 1.3
timestamp: 2026-04-21T00:00:00Z
date: 2026-04-21
specialty: Ophthalmology
analysis_type: NMA
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/antivegf_namd_nma_protocol_v1.3_2026-04-21.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/ANTIVEGF_NAMD_NMA_REVIEW.html
license: MIT
---

# Anti-VEGF NMA in Neovascular AMD (VIEW-1/2 / TENAYA-LUCERNE / PULSAR / HAWK-HARRIER)
## A Living Systematic Review and Network Meta-Analysis Protocol

**Version:** 1.3 · **Frozen:** 2026-04-21 · **Authors:** Mahmood Ahmad

---

## 1. Title and Registration

Network Meta-Analysis of Intravitreal Anti-VEGF Agents (Ranibizumab, Aflibercept 2 mg, Aflibercept 8 mg, Faricimab, Brolucizumab) in Treatment-Naive Neovascular AMD. Protocol frozen 2026-04-21.

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with treatment-naive neovascular AMD, visual-acuity impairment suitable for anti-VEGF |
| **Interventions (5)** | Ranibizumab 0.5 mg monthly; Aflibercept 2 mg Q8W; Aflibercept 8 mg Q12W/Q16W; Faricimab 6 mg PTI; Brolucizumab 6 mg Q12W |
| **Comparator (reference)** | Aflibercept 2 mg Q8W (modern standard-of-care anchor) |
| **Outcome (primary)** | BCVA letter-score change from baseline at week 48–52; **mean difference (MD, ETDRS letters)**; non-inferiority margin −4 letters |

## 3. Network (v1.3)

| Edge | Trial (NCT) | Comparison |
|---|---|---|
| Aflibercept 2 mg — Ranibizumab | VIEW-1 (NCT00509795) | MD +0.5 (−1.1, +2.1) |
| Aflibercept 2 mg — Ranibizumab | VIEW-2 (NCT00637377) | MD +0.6 (−1.1, +2.3) |
| Faricimab — Aflibercept 2 mg | TENAYA (NCT03823287) | MD +0.7 (−0.65, +2.05) |
| Faricimab — Aflibercept 2 mg | LUCERNE (NCT03823300) | MD +0.5 (−0.85, +1.85) |
| Aflibercept 8 mg — Aflibercept 2 mg | PULSAR (NCT04964089) | MD +1.0 (−0.4, +2.5) |
| Brolucizumab — Aflibercept 2 mg | HAWK (NCT02307682) | MD −0.2 (−1.5, +1.1) |
| Brolucizumab — Aflibercept 2 mg | HARRIER (NCT02434328) | MD +0.7 (−0.6, +2.0) |

**Geometry:** Star through Aflibercept 2 mg + replicate pivotal pairs (VIEW-1/2, TENAYA/LUCERNE, HAWK/HARRIER) for direct-pool precision. k = 7.

## 4. Synthesis

- `netmeta` 3.2.0, `sm="MD"`, REML τ², HKSJ CI
- Reference: Aflibercept 2 mg (alphabetical in R; semantically the modern SoC anchor)
- Consistency: 3 parallel-pair direct pools (each edge has 2 trials) → design-by-treatment test informative at Q_inc on replicates
- Ranking: SUCRA via mvrnorm-sampled rank-probability

## 5. Transitivity

| Effect modifier | VIEW-1/2 | TENAYA/LUCERNE | PULSAR | HAWK/HARRIER | Concern |
|---|---|---|---|---|---|
| Year of trial | 2012 | 2022 | 2024 | 2020 | Secular change in imaging-based disease activity definitions |
| BCVA primary timepoint | wk 52 | wk 48 | wk 48 | wk 48 | Broadly compatible |
| Dosing paradigm of reference | monthly → Q8W mix | Q8W fixed | Q8W fixed | Q8W fixed | Secular change in monthly loading requirements |
| Non-inferiority margin | −5 letters | −4 letters | −4 letters | −4 letters | Margin tightened over time |
| Sham/placebo eligibility | n/a (head-to-head) | n/a | n/a | n/a | — |

## 6. CINeMA GRADE-NMA

| Comparison | Within | Across | Indirectness | Imprecision | Heterogeneity | Incoherence | Pub bias | **Certainty** |
|---|---|---|---|---|---|---|---|---|
| Faricimab vs Aflib 2 mg | Low | Low | Low | Low | Low (VIEW-comparable τ²=0) | n/a | Low | **HIGH** |
| Aflib 8 mg vs Aflib 2 mg | Low | Low | Low | Low | Low | n/a | Low | **HIGH** |
| Brolucizumab vs Aflib 2 mg | Moderate (post-market IOI/vasculitis) | Low | Low | Low | Low | n/a | Low | **MODERATE** |
| Ranibizumab vs Aflib 2 mg | Low | Low | Low | Low | Low | n/a | Low | **HIGH** |
| Faricimab vs Aflib 8 mg | Low | Low | Moderate (indirect-only) | Moderate | Low | n/a | Low | **MODERATE** |
| Brolucizumab vs Faricimab | Moderate | Low | Moderate (indirect) | Moderate | Low | n/a | Low | **LOW-MODERATE** |

## 7. Living-NMA cadence

3-monthly. Triggers: aflibercept-8-mg long-term (96-wk PULSAR), faricimab Q24W extension, port-delivery system re-analysis, next-generation complement/VEGF bispecifics.

## 8. Reporting

PRISMA-NMA 2020 + CONSORT-Harms for IOI (brolucizumab ~4% vs others <0.5%), retinal-artery occlusion, endophthalmitis.

## Changelog

- **v1.3** (2026-04-21) — First dedicated protocol; SCALE fix (MD, not HR-equivalent ratio); ANCHOR proxy-bridge REMOVED and replaced with VIEW-1 + VIEW-2 (direct rani-vs-aflib) + LUCERNE (faricimab pair) + HARRIER (brolucizumab pair).
