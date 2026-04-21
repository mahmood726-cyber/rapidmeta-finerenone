---
title: "Incretin Class NMA in Type 2 Diabetes — v1.3 with sensitivity strata"
slug: incretins_t2d_nma
version: 1.3
timestamp: 2026-04-21T00:00:00Z
date: 2026-04-21
specialty: Endocrinology (Diabetes)
analysis_type: NMA
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/incretins_t2d_nma_protocol_v1.3_2026-04-21.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/INCRETINS_T2D_NMA_REVIEW.html
license: MIT
supersedes: [incretins_t2d_nma_protocol_v1.0_2026-04-21.md]
---

# Incretin Class NMA in T2D — v1.3 (SURPASS / SUSTAIN / LEAD / AWARD / PIONEER / EXSCEL)
## Network Meta-Analysis Protocol with Pre-Specified Sensitivity Strata

**Version:** 1.3 · **Frozen:** 2026-04-21 · **Author:** Mahmood Ahmad (drmahmoodclinic@pm.me)

## 0. What v1.3 adds

v1.2 (k=13) detected a significant design-by-treatment inconsistency (**Q_inc = 73.75, df=5, p<0.001**) driven by heterogeneity between (a) short-term glycaemic-efficacy trials (26–56 wk, single-background-layer, HbA1c as primary) and (b) long-term CV-outcome trials (≥2 yr, heterogeneous multi-drug background, HbA1c as secondary).

v1.3 resolves this with **two pre-specified sensitivity analyses run as a matched pair**:

1. **Analysis 1 — Broad-scope unified (k=13):** retained for transparency. CINeMA coherence downgraded to **VERY LOW** for indirect comparisons in the unified network. Direct comparisons keep per-edge ratings.
2. **Analysis 2 — Stratum A (k=11):** drops SUSTAIN-6 + EXSCEL. Short-term glycaemic efficacy.
3. **Analysis 3 — Stratum B (k=2):** SUSTAIN-6 + EXSCEL alone. Long-term CV-outcome trial HbA1c drift.

**Clinical-interpretation primary:** Stratum A.
**Ranking primary:** Stratum A (ordering identical to unified so interpretation is robust).
**Transparency primary:** Unified (reported with explicit coherence downgrade).

## 1. Title + Registration

Network Meta-Analysis of Incretin-Based Therapies (Tirzepatide, Semaglutide, Oral Semaglutide, Dulaglutide, Liraglutide, Exenatide) vs Placebo (and active comparator Sitagliptin) for Glycaemic Control in Type 2 Diabetes — with pre-specified stratum-split sensitivity analyses for design heterogeneity between short-term glycaemic-efficacy trials and long-term CV-outcome trials.

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with type 2 diabetes; Stratum A requires drug-naive or single-background-layer (metformin ± one other); Stratum B covers CV-outcome-trial populations on variable multi-drug background including insulin and sulfonylurea |
| **Interventions (6 incretins + 1 active comparator)** | Tirzepatide 15 mg SC weekly (dual GIP/GLP-1) · Semaglutide 1 mg SC weekly · Oral Semaglutide 14 mg once daily · Dulaglutide 1.5 mg SC weekly · Liraglutide 1.8 mg SC daily · Exenatide (ER 2 mg weekly or BID 10 mcg — see transitivity) · Sitagliptin 100 mg daily (DPP-4 active comparator) |
| **Comparator** | Placebo |
| **Outcome (primary)** | HbA1c change from baseline at the trial-primary timepoint; **mean difference (MD, %)** |

## 3. Networks

### 3.1 Stratum A edges (k = 11)

| Edge | Trial | MD | Direction |
|---|---|---|---|
| Tirzepatide — Placebo | SURPASS-1 (NCT03954834) | −2.11 | Tirz better |
| Tirzepatide — Semaglutide | SURPASS-2 (NCT03987919) | −0.45 | Tirz better |
| Semaglutide — Placebo | SUSTAIN-1 (NCT02054897) | −1.55 | Sema better |
| Semaglutide — Sitagliptin | SUSTAIN-2 (NCT01930188) | −1.10 | Sema better |
| Semaglutide — Exenatide | SUSTAIN-3 (NCT01885208) | −0.62 | Sema better (vs Exe-ER) |
| Semaglutide — Dulaglutide | SUSTAIN-7 (NCT02648204) | −0.31 | Sema better |
| Liraglutide — Exenatide | LEAD-6 (NCT00518882) | −0.33 | Lira better |
| Dulaglutide — Liraglutide | AWARD-6 (NCT01624259) | −0.06 | Non-inferior |
| Liraglutide — Placebo | LEAD-2 (NCT00318461) | −1.10 | Lira better (on metformin) |
| OralSemaglutide — Liraglutide | PIONEER-4 (NCT02863419) | −0.10 | Non-inferior |
| OralSemaglutide — Sitagliptin | PIONEER-3 (NCT02607865) | −0.50 | OralSema better |

**Geometry:** Rich network with two closed loops. Loop 1: Sema–Dula–Lira–Exe–Sema (SUSTAIN-7 + AWARD-6 + LEAD-6 + SUSTAIN-3). Loop 2: Sema–Sita–OralSema–Lira–Sema (SUSTAIN-2 + PIONEER-3 + PIONEER-4 + via Sema-Lira indirect). Tirzepatide attached via SURPASS-1/2.

### 3.2 Stratum B edges (k = 2)

| Edge | Trial | MD | Direction |
|---|---|---|---|
| Semaglutide — Placebo | SUSTAIN-6 (NCT01720446, 2 yr CVOT) | −0.77 | Sema better (secondary endpoint) |
| Exenatide-ER — Placebo | EXSCEL (NCT01144338, 3.2 yr CVOT) | −0.53 | Exe-ER better (secondary endpoint) |

**Geometry:** 2-trial Pbo-star. No closed loop. Direct pairwise only.

### 3.3 Unified (k = 13)

Union of Stratum A + Stratum B. Reported with the same effect estimates as above but with Q_inc = 73.75, τ² = 0.077, I² = 95%, CINeMA coherence downgraded to VERY LOW for indirect contrasts.

## 4. Analysis specification

- **Software:** netmeta v3.2.0 (R 4.5.2); pinned via renv.lock
- **Estimator:** REML for τ² (Stratum A and Unified); DerSimonian-Laird for Stratum B (REML undefined with k=2 at a single design)
- **CI method:** Hartung-Knapp-Sidik-Jonkman (HKSJ) adjustment for Stratum A + Unified
- **Ranking:** P-score + SUCRA via MVN MC (N = 100,000 draws from `nma$Cov.random`-derived contrast vcov)
- **Pre-specified primary analysis:** Stratum A (clinical interpretation + ranking)
- **Pre-specified sensitivity analyses:** Unified (transparency) and Stratum B (long-term drift quantification)

## 5. Results summary (see peer-review bundle for full detail)

| Metric | Unified (k=13) | Stratum A (k=11) | Stratum B (k=2) |
|---|---|---|---|
| τ² | 0.0775 | 0.00786 | undefined |
| I² | 95.4% | 63.1% | NA |
| Q_inc | 73.75 (p<0.001) | 10.85 (p=0.028) | — |
| Tirz vs Pbo MD | −1.906 (−2.344, −1.468) | −2.053 (−2.259, −1.847) | n/a |
| Sema vs Pbo MD | −1.276 (−1.580, −0.972) | −1.574 (−1.748, −1.399) | −0.770 (−0.850, −0.690) |
| Exe vs Pbo MD | −0.596 (−0.970, −0.222) | −0.864 (−1.100, −0.628) | −0.530 (−0.570, −0.490) |

## 6. Transitivity

See peer-review bundle §5 for stratum-aware transitivity table.

## 7. CINeMA GRADE-NMA

See peer-review bundle §6 for stratum-aware per-comparison certainty ratings. The **Unified-network row** explicitly downgrades incoherence to SERIOUS and overall certainty to **VERY LOW** per the broad-scope sensitivity requirement.

## 8. Pre-registration and reporting

- Protocol v1.0 (2026-04-21) logged the original k=7 network
- Protocol v1.3 (2026-04-21) supersedes v1.0 with k=13 expansion and sensitivity strata
- Registration: to be submitted to PROSPERO post-peer-review
- Reporting: PRISMA-NMA 2020 compliant (25/27 items)

## 9. Changelog

- **v1.3** (2026-04-21) — Pre-specified stratum-split + broad-scope sensitivity analyses. Q_inc in Stratum A reduced to 10.85 (p=0.028). Unified retained with CINeMA coherence downgrade to VERY LOW.
- **v1.2** (2026-04-21) — Added PIONEER-3, PIONEER-4, SUSTAIN-2 (k=7 → k=13). Detected Q_inc=73.75 (p<0.001). Declared roadmap.
- **v1.0** (2026-04-21) — First release; k=7; Q_inc p=0.69.
