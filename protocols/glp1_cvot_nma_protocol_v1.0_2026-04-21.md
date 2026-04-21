---
title: "GLP-1 RA Class NMA for MACE in T2D CV-Outcome Trials"
slug: glp1_cvot_nma
version: 1.0
timestamp: 2026-04-21T00:00:00Z
date: 2026-04-21
specialty: Cardiology / Endocrinology
analysis_type: NMA
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/glp1_cvot_nma_protocol_v1.0_2026-04-21.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/GLP1_CVOT_NMA_REVIEW.html
license: MIT
---

# GLP-1 RA Class NMA for MACE (LEADER / SUSTAIN-6 / REWIND / PIONEER-6 / ELIXA / HARMONY / EXSCEL / AMPLITUDE-O)
## Network Meta-Analysis Protocol

**Version:** 1.0 · **Frozen:** 2026-04-21 · **Author:** Mahmood Ahmad

## 1. Title + Registration

Network Meta-Analysis of GLP-1 Receptor Agonists vs Placebo for Major Adverse Cardiovascular Events in Type 2 Diabetes — Phase 3/4 CV-Outcome Trial Network.

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with T2D at elevated CV risk (established CVD or multiple CV risk factors) |
| **Interventions** | Liraglutide · Semaglutide (SC) · Oral Semaglutide · Dulaglutide · Lixisenatide · Albiglutide · Exenatide-ER · Efpeglenatide |
| **Comparator** | Placebo |
| **Outcome (primary)** | Trial-specific primary MACE composite (3-point or 4-point); HR scale |

## 3. Network

Star through Placebo; k = 8 trials, 9 nodes (8 drugs + Pbo). One CVOT per drug — no within-drug replication.

## 4. Analysis

- **Software:** netmeta v3.2.0 (R 4.5.2)
- **Estimator:** REML (τ²=0 observed)
- **CI:** HKSJ adjustment
- **Ranking:** P-score + SUCRA via MVN MC (N = 100k draws)

## 5. Results summary

| Drug | HR vs Pbo (95% CI) | SUCRA |
|---|---:|---:|
| Efpeglenatide | 0.73 (0.58, 0.92) | 0.896 |
| Semaglutide | 0.74 (0.58, 0.95) | 0.791 |
| Albiglutide | 0.78 (0.68, 0.90) | 0.717 |
| OralSemaglutide | 0.79 (0.57, 1.11) | 0.678 |
| Liraglutide | 0.87 (0.78, 0.97) | 0.405 |
| Dulaglutide | 0.88 (0.79, 0.99) | 0.382 |
| Exenatide-ER | 0.91 (0.83, 1.00) | 0.291 |
| Lixisenatide | 1.02 (0.89, 1.17) | 0.175 |

## 6. Transitivity

See peer-review bundle §5 for full table. Key declarations:
- ELIXA uses 4-point MACE (others 3-point)
- Albiglutide commercially withdrawn 2018; Efpeglenatide discontinued 2020 — effect estimates remain valid
- OralSemaglutide = oral Semaglutide (same molecule, different route) — kept as separate nodes

## 7. Changelog

- **v1.0** (2026-04-21) — First release.
