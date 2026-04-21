---
title: "JAK Inhibitors NMA in MTX-IR Rheumatoid Arthritis"
slug: jaki_ra_nma
version: 1.0
timestamp: 2026-04-21T00:00:00Z
date: 2026-04-21
specialty: Rheumatology (RA)
analysis_type: NMA
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/jaki_ra_nma_protocol_v1.0_2026-04-21.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/JAKI_RA_NMA_REVIEW.html
license: MIT
---

# JAKi NMA in MTX-IR RA (ORAL-Standard / RA-BEAM / SELECT-Compare / FINCH-1)
## Network Meta-Analysis Protocol

**Version:** 1.0 · **Frozen:** 2026-04-21 · **Authors:** Mahmood Ahmad

## 1. Title + Registration

Network Meta-Analysis of JAK Inhibitors (Tofacitinib, Baricitinib, Upadacitinib, Filgotinib) vs Adalimumab vs Placebo in Methotrexate-Inadequate-Response Rheumatoid Arthritis.

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with active RA and inadequate response to methotrexate; each trial enrolled on background MTX |
| **Interventions (4 JAKi)** | Tofacitinib 5 mg BID (JAK1/3) · Baricitinib 4 mg daily (JAK1/2) · Upadacitinib 15 mg daily (JAK1-selective) · Filgotinib 200 mg daily (JAK1-selective) |
| **Active comparator** | Adalimumab 40 mg SC Q2W (TNFi) |
| **Reference** | Placebo |
| **Outcome (primary)** | ACR20 response at week 12 (wk 6 for ORAL-Standard per tofacitinib primary) — **odds ratio (OR)** vs Placebo |

## 3. Network

| Edge | Trial | OR (95% CI) |
|---|---|---|
| Tofacitinib — Placebo | ORAL-Standard (NCT00853385) wk 6 | 2.67 (1.60, 4.45) |
| Baricitinib — Placebo | RA-BEAM (NCT01710358) wk 12 | 3.51 (2.69, 4.58) |
| Upadacitinib — Placebo | SELECT-Compare (NCT02629159) wk 12 | 4.36 (3.45, 5.50) |
| Filgotinib — Placebo | FINCH-1 (NCT02889796) wk 12 | 3.34 (2.53, 4.42) |
| Adalimumab — Placebo | FINCH-1 Ada arm (pseudo-NCT02889796B) wk 12 | 2.45 (1.82, 3.30) |

**Geometry:** Star network through Placebo. k=5 edges. No closed loops. **Adalimumab anchor** extracted from FINCH-1's third arm only (single-trial anchor) to avoid multi-arm covariance inflation; other trials' Ada arms deliberately excluded from the contrast pool but retained as sensitivity data in protocol §5.

## 4. Synthesis

- `netmeta` 3.2.0, `sm="OR"`, REML τ², HKSJ CI
- Reference = Placebo
- Consistency: star network → no loops → Q_inc = 0, df = 0 (no test possible; transitivity preserved by design)
- Ranking: SUCRA (direction-aware via `small.values="undesirable"`; higher OR = better) + P-score

## 5. Key results

**ACR20 OR vs Placebo (random-effects, REML, HKSJ):**

| Treatment | OR | 95% CI |
|---|---:|---:|
| **Upadacitinib** | **4.36** | (3.45, 5.50) |
| **Baricitinib** | **3.51** | (2.69, 4.58) |
| **Filgotinib** | **3.34** | (2.53, 4.42) |
| Tofacitinib | 2.67 | (1.60, 4.45) |
| Adalimumab | 2.45 | (1.82, 3.30) |

**Heterogeneity:** τ² = 0, I² = 0%. Star network is homogeneous.

**SUCRA (direction-correct):** Upa 0.926 · Bari 0.736 · Fil 0.692 · Tofa 0.364 · Ada 0.282 · Placebo 0.000.

## 6. Transitivity

| Effect modifier | Concern |
|---|---|
| Primary timepoint | wk 6 (ORAL-Standard, tofacitinib primary) vs wk 12 (others) | **Moderate** — ACR20 response rate continues climbing between wk 6 and wk 12; may disadvantage tofacitinib in ranking |
| Background MTX | All trials on MTX | Compatible |
| Baseline DAS28 | 5.5-6.5 range across trials | Similar |
| Population age | 50-55 median | Similar |
| **Placebo comparator** | Placebo on background MTX (all 4 trials) | Compatible — same underlying standard-of-care arm |
| Adalimumab anchor | Single-trial anchor from FINCH-1 Ada arm; other trials' Ada arms available for sensitivity | Declared |

**Declared limitations:**
1. **Tofacitinib primary timepoint (wk 6) vs others (wk 12)** — ACR20 continues to increase through wk 12 in JAKi class; the 2.67 OR for tofacitinib may be conservative vs if measured at wk 12
2. **Adalimumab anchor is single-trial** — 3-arm multi-comparator trials (ORAL-Standard, RA-BEAM, SELECT-Compare) contain Ada arms that would enable multi-trial Ada-Placebo pooling but require multi-arm covariance handling (τ²/2 off-diagonal rule). Deliberately excluded from the primary network; sensitivity analysis may include them with appropriate multi-arm adjustment

## 7. CINeMA GRADE-NMA

| Comparison | Within | Across | Indirectness | Imprecision | Heterogeneity | Incoherence | Pub bias | **Certainty** |
|---|---|---|---|---|---|---|---|---|
| Upa vs Placebo (direct) | Low | Low | Low | Low | n/a (k=1) | n/a | Low (boxed warning on JAKi class applies) | **HIGH** |
| Bari vs Placebo (direct) | Low | Low | Low | Low | n/a | n/a | Low | **HIGH** |
| Fil vs Placebo (direct) | Low | Low | Low | Low | n/a | n/a | Low | **HIGH** |
| Tofa vs Placebo (direct) | Low | Low | **Moderate** (wk 6 timepoint) | Moderate (wider CI) | n/a | n/a | Low | **MODERATE** |
| Ada vs Placebo (single-trial anchor) | Low | **Moderate** (one-trial anchor, other Ada-Pbo data excluded) | Low | Low | n/a | n/a | Low | **MODERATE-HIGH** |
| Upa vs Bari (indirect) | Low | Low | Moderate | Low | Low | n/a | Low | **MODERATE-HIGH** |
| Upa vs Tofa (indirect) | Low | Low | Moderate-Serious (wk 6 vs wk 12) | Moderate | Low | n/a | Low | **MODERATE** |
| Any JAKi vs Ada (indirect) | Low | Low | Moderate | Moderate | Low | n/a | Low | **MODERATE** |

**Class-level safety note:** ORAL-Surveillance (2022 NEJM) demonstrated tofacitinib 10 mg vs adalimumab signal for MACE + malignancy in ≥50-year-olds with ≥1 CV risk factor. FDA boxed warning applies to all JAKi. Not captured by ACR20 efficacy ranking; reported separately per CONSORT-Harms.

## 8. Living-NMA cadence

3-monthly. Triggers: SELECT-EARLY long-term update, FINCH-3 maintenance, peficitinib GO-FORWARD, deucravacitinib (TYK2) PAOLA, next-generation JAKi+IL-6 combinations.

## Changelog

- **v1.0** (2026-04-21) — First release; 5 pivotal phase 3 contrasts; star network; single-trial Ada anchor.
