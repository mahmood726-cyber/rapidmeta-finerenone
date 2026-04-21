---
title: "Anti-Amyloid mAbs NMA in Early Alzheimer Disease"
slug: antiamyloid_ad_nma
version: 1.3
timestamp: 2026-04-21T00:00:00Z
date: 2026-04-21
specialty: Neurology (Alzheimer Disease)
analysis_type: NMA
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/antiamyloid_ad_nma_protocol_v1.3_2026-04-21.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/ANTIAMYLOID_AD_NMA_REVIEW.html
license: MIT
---

# Anti-Amyloid mAbs NMA in Early AD (Clarity AD / TRAILBLAZER-ALZ 2 / EMERGE / ENGAGE)
## A Living Systematic Review and Network Meta-Analysis Protocol

**Version:** 1.3 · **Frozen:** 2026-04-21 · **Authors:** Mahmood Ahmad (drmahmoodclinic@pm.me)

---

## 1. Title and Registration

Network Meta-Analysis of Anti-Amyloid Monoclonal Antibodies (Lecanemab, Donanemab, Aducanumab) vs Placebo in Early Alzheimer Disease. Protocol frozen via GitHub-canonical-URL freeze 2026-04-21.

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with early Alzheimer disease (MCI or mild AD dementia), amyloid-PET or CSF-confirmed pathology |
| **Interventions (3)** | Lecanemab 10 mg/kg IV Q2W · Donanemab 700/1400 mg IV Q4W · Aducanumab 10 mg/kg IV Q4W (high-dose arm) |
| **Comparator** | Matched placebo |
| **Outcome (primary)** | CDR-SB (Clinical Dementia Rating Sum of Boxes) change from baseline at 18–19 months; **mean difference (MD, points)** — anti-mAb minus placebo; lower = better |

## 3. Network

| Edge | Trial (NCT) | Comparison |
|---|---|---|
| Lecanemab — Placebo | Clarity AD (NCT03887455) | MD −0.45 (−0.67 to −0.23) |
| Donanemab — Placebo | TRAILBLAZER-ALZ 2 (NCT04437511) | MD −0.70 (−0.95 to −0.45) |
| Aducanumab — Placebo | EMERGE (NCT02477800) | MD −0.39 (−0.69 to −0.09) |
| Aducanumab — Placebo | ENGAGE (NCT02484547) | MD +0.03 (−0.26 to +0.32) — **negative pivotal** |

**Geometry:** Star network (3 active treatments vs shared Placebo node). Aducanumab has two-trial pool (EMERGE + ENGAGE). k = 4 total.

## 4. Synthesis

- `netmeta` 3.2.0 on MD scale with `sm="MD"`
- `method.tau="REML"` (per user rule: no DL for k<10) + HKSJ CI (`hakn=TRUE`)
- Reference = Placebo
- Consistency: star network → no closed loops → formal loop-inconsistency test n/a; design-by-treatment not applicable
- Ranking: SUCRA + P-score + full rank-probability matrix via `MASS::mvrnorm` from `nma$Cov.random`

## 5. Transitivity (effect-modifier assessment)

| Effect modifier | Clarity AD | TRAILBLAZER-ALZ 2 | EMERGE | ENGAGE | Concern |
|---|---|---|---|---|---|
| Population | Early AD + CSF/PET | Early AD + amyloid-PET + **tau-PET low-medium stratum** | Early AD + amyloid-PET | Early AD + amyloid-PET | **Moderate** — TRAILBLAZER-ALZ 2 tau-stratification (no-tau-high) may amplify donanemab effect |
| Median age (years) | ~71 | ~73 | ~70 | ~70 | Similar |
| MMSE range | 22–30 | 20–28 | 24–30 | 24–30 | Similar |
| Primary endpoint | CDR-SB | iADRS (CDR-SB co-primary) | CDR-SB | CDR-SB | Compatible after iADRS→CDR-SB conversion |
| Follow-up at primary | 18 mo | 76 wk | 78 wk | 78 wk | Compatible |
| ARIA monitoring | Mandated MRI | Mandated MRI | Mandated MRI | Mandated MRI | Compatible |

**Declared limitations:**
1. **Tau-PET stratification in TRAILBLAZER-ALZ 2** — donanemab's estimate may shift in the tau-high stratum (showed smaller effect in the combined analysis)
2. **ENGAGE + EMERGE discordance** — aducanumab's two pivotals went in opposite directions; the pooled MD −0.18 (CI crosses 0) reflects the FDA's own conclusion that aducanumab efficacy is uncertain

## 6. CINeMA GRADE-NMA worksheet

| Comparison | Within-study bias | Across-study bias | Indirectness | Imprecision | Heterogeneity | Incoherence | Publication bias | **Certainty** |
|---|---|---|---|---|---|---|---|---|
| Lecanemab vs Placebo | Low | Low | Low | Low | Low (single-trial edge) | n/a (no loops) | Low (k<10 suppressed) | **HIGH** |
| Donanemab vs Placebo | Low | Low | Moderate (tau-PET stratification) | Low | Low | n/a | Low | **MODERATE** |
| Aducanumab vs Placebo | Moderate (trial truncation, reanalysis) | Low | Low | Moderate (CI crosses 0 with ENGAGE) | Moderate (τ²>0 EMERGE-ENGAGE) | n/a | Low | **LOW** |
| Lecanemab vs Donanemab | Low | Low | Moderate (indirect only; tau-PET heterogeneity) | Low | Low | n/a | Low | **MODERATE** |
| Lecanemab vs Aducanumab | Moderate | Low | Moderate | Moderate | Moderate | n/a | Low | **LOW-MODERATE** |
| Donanemab vs Aducanumab | Moderate | Low | Moderate | Moderate | Moderate | n/a | Low | **LOW-MODERATE** |

## 7. Living-NMA cadence

3-monthly. Triggers: remternetug (NCT05463731), trontinemab (early Alzheimer), gantenerumab post-GRADUATE-I/II, long-term ARIA surveillance updates.

## 8. Reporting

PRISMA-NMA 2020 + CONSORT-Harms for ARIA-E (symptomatic vs asymptomatic), ARIA-H, brain-volume change. Dual-assessor RoB-2 per submission.

## Appendix — R validation + in-app tools

- Static R: `nma/validation/antiamyloid_ad_nma_netmeta.R` (REML + HKSJ + mvrnorm MC)
- JSON/RDS/txt outputs: `nma/validation/antiamyloid_ad_nma_netmeta_results.*`
- In-browser WebR: "Run netmeta in browser" button in app PR panel
- Interactive CINeMA builder: `nma-peer-review-tools.js` section 3

## Changelog

- **v1.3** (2026-04-21) — First dedicated protocol; SCALE fix (MD, not HR-equivalent); ENGAGE added to address selective-pivotal-reporting concern.
