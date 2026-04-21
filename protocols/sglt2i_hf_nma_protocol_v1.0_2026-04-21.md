---
title: "SGLT2i Class NMA in Heart Failure"
slug: sglt2i_hf_nma
version: 1.0
timestamp: 2026-04-21T00:00:00Z
date: 2026-04-21
specialty: Cardiology (HF)
analysis_type: NMA
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/sglt2i_hf_nma_protocol_v1.0_2026-04-21.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/SGLT2I_HF_NMA_REVIEW.html
license: MIT
---

# SGLT2i Class NMA in Heart Failure (DAPA-HF / EMPEROR / DELIVER / SOLOIST-WHF / SCORED)
## Network Meta-Analysis Protocol

**Version:** 1.0 · **Frozen:** 2026-04-21 · **Author:** Mahmood Ahmad

## 1. Title + Registration

Network Meta-Analysis of SGLT2 Inhibitors (Dapagliflozin, Empagliflozin, Sotagliflozin) vs Placebo for Cardiovascular Death or Hospitalisation for Heart Failure Across the Ejection-Fraction Spectrum.

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with heart failure (HFrEF, HFmrEF, HFpEF) or at high HF-risk (T2D + CV risk + CKD) |
| **Interventions** | Dapagliflozin 10 mg · Empagliflozin 10 mg · Sotagliflozin 200–400 mg (dual SGLT1/2) |
| **Comparator** | Placebo |
| **Outcome (primary)** | CV death or hospitalisation for heart failure (trial-specific primary composite); HR scale |

## 3. Network (k = 6)

| Edge | Trial | HR | Direction |
|---|---|---|---|
| Dapa–Pbo | DAPA-HF (NCT03036124) | 0.74 (0.65–0.85) | Dapa better |
| Empa–Pbo | EMPEROR-Reduced (NCT03057977) | 0.75 (0.65–0.86) | Empa better |
| Empa–Pbo | EMPEROR-Preserved (NCT03057951) | 0.79 (0.69–0.90) | Empa better |
| Dapa–Pbo | DELIVER (NCT03619213) | 0.82 (0.73–0.92) | Dapa better |
| Sota–Pbo | SOLOIST-WHF (NCT03521934) | 0.67 (0.52–0.85) | Sota better (early-terminated) |
| Sota–Pbo | SCORED (NCT03315143) | 0.74 (0.63–0.88) | Sota better (early-terminated) |

**Geometry:** Placebo-star. Each SGLT2i has 2 direct Pbo-anchored trials. No head-to-head. No closed loops.

## 4. Analysis

- **Software:** netmeta v3.2.0 (R 4.5.2)
- **Estimator:** REML for τ² (though τ² = 0 in observed data)
- **CI:** HKSJ adjustment (though marginal effect given τ² = 0)
- **Ranking:** P-score + SUCRA via MVN MC (N = 100k draws from nma$Cov.random)
- **Pre-specified sensitivity:** Stratum A (HF-primary trials only, k = 4) excluding SOLOIST-WHF + SCORED

## 5. Results summary (v1.0)

| Metric | Unified (k=6) | Stratum A (k=4) |
|---|---|---|
| τ² | 0.000 | 0.000 |
| I² | 0.0% | 0.0% |
| Sota vs Pbo HR | 0.717 (0.625, 0.823) | — (excluded) |
| Empa vs Pbo HR | 0.771 (0.700, 0.849) | 0.771 (0.700, 0.849) |
| Dapa vs Pbo HR | 0.785 (0.719, 0.857) | 0.785 (0.719, 0.857) |

## 6. Transitivity declarations

1. Sotagliflozin is a **dual SGLT1/SGLT2** inhibitor, not a pure SGLT2i — declared but does not violate transitivity for the HHF outcome.
2. SOLOIST-WHF + SCORED were **both terminated early** by Sanofi for funding reasons — effect estimates may be optimistic (Montori 2005 JAMA bias).
3. SOLOIST-WHF enrolled during/post an acute HHF episode while DAPA-HF/EMPEROR/DELIVER enrolled **chronic compensated HF**. Population severity differs; declared.
4. Primary-endpoint operationalisation differs: time-to-first-event (DAPA-HF, EMPEROR series) vs total recurrent events (SOLOIST-WHF, SCORED).

## 7. CINeMA

See peer-review bundle §6. Headline: **HIGH** certainty for Dapa-vs-Pbo and Empa-vs-Pbo; **MODERATE** for Sota-vs-Pbo (early termination); **MODERATE** for within-class indirect rankings.

## 8. Changelog

- **v1.0** (2026-04-21) — First release.
