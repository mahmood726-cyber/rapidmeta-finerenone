---
title: "Nirsevimab (Long-Acting Anti-RSV F mAb) for Infant RSV-LRTI Prevention"
slug: nirsevimab_infant_rsv
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Infectious Disease (Paediatric RSV)
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/nirsevimab_infant_rsv_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/NIRSEVIMAB_INFANT_RSV_REVIEW.html
license: MIT
---

# Nirsevimab for Infant RSV-LRTI Prevention
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Infectious Disease (Paediatric RSV)

---

## 1. Review Title and Registration

**Title:** Nirsevimab (Long-Acting Anti-RSV F Monoclonal Antibody) for Prevention of Respiratory Syncytial Virus Lower Respiratory Tract Infection in Infants: A Living Systematic Review and Meta-Analysis of Phase 2b/3 RCTs

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding).

**Corresponding address:** drmahmoodclinic@pm.me (GMC 6071047), Royal Free Hospital and Barnet Hospital, London, UK.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Healthy preterm, late-preterm, and term infants entering their first RSV season |
| **Intervention** | Nirsevimab single intramuscular injection (50 or 100 mg by weight) |
| **Comparator** | Matched placebo IM (Phase 2b, MELODY) OR no intervention / standard of care (HARMONIE pragmatic) |
| **Outcome (primary)** | Medically attended RSV-associated LRTI through Day 150 (Phase 2b / MELODY) OR RSV-LRTI hospitalisation through first RSV season (HARMONIE) |

---

## 3. Eligibility Criteria

### Inclusion
- RCT (parallel; double-blind for placebo-controlled, open-label for pragmatic effectiveness)
- Phase IIb pivotal or phase III trials
- Infants entering first RSV season
- Nirsevimab single-dose IM at licensed regimen
- Medically attended RSV-LRTI or RSV hospitalisation as primary endpoint

### Exclusion
- MEDLEY safety/PK study (nirsevimab vs palivizumab, not a placebo or no-treatment comparator for efficacy)
- Palivizumab monthly-dosing trials (separate review of high-risk-infant monoclonal therapy)
- Observational effectiveness studies (post-licensure — reserved for sensitivity-only in future updates)

---

## 4. Information Sources and Search Strategy

| Database | Query |
|---|---|
| ClinicalTrials.gov | `nirsevimab AND RSV AND infant` |
| Europe PMC / PubMed | `(MELODY OR HARMONIE OR nirsevimab) AND RSV AND randomized` |

---

## 5. Study Selection

Two-reviewer adjudication with HMAC-signed seal; PRISMA 2020.

---

## 6. Data Extraction

Study IDs, N per arm, RSV-LRTI event counts, RSV-hospitalisation counts, gestational-age / birthweight strata, safety (anaphylaxis, injection-site reactions, grade 3+ AEs), RoB 2.

---

## 7. Risk of Bias Assessment

Cochrane **RoB 2**. Design-based priors: Phase 2b (Griffin 2020) + MELODY = LOW across D1-D5 (double-blind placebo-controlled with central PCR confirmation). HARMONIE = **D2 SOME CONCERNS** (open-label pragmatic effectiveness design, no placebo). Author sign-off required per the provisional-RoB banner.

---

## 8. Synthesis / Statistical Methods

- **Primary pool:** DerSimonian-Laird random-effects IVW on log-RR scale for the primary outcome.
- **CI adjustment:** HKSJ with t-distribution df=k-1; floor `max(1, Q/(k-1))`.
- **Prediction interval:** t-df=k-2 (Higgins 2009), enabled at k=3.
- **Subgroup / meta-regression:** By study design (blinded-placebo vs pragmatic), gestational age (term vs preterm), hemisphere.
- **Heterogeneity caveat:** Effect sizes are consistent (VE 70-83%), pool expected to be stable. Primary endpoint definition differs (medically-attended RSV-LRTI in Phase 2b / MELODY; RSV-hospitalisation in HARMONIE); pool interprets the broader class-level "protection from RSV medical-care utilisation".
- **Zero-cell handling:** Conditional 0.5 continuity correction.
- **Primary-timepoint harmonisation:** Day 150 is the harmonised timepoint for Phase 2b + MELODY; HARMONIE uses first full RSV season which is approximately Day 150-210 depending on hemisphere.
- **Trim-and-fill:** Duval-Tweedie low-power caveat at k<10.
- **Bayesian:** Grid-approximation with half-normal(0, 0.5) prior on tau.
- **Vaccine efficacy reporting:** VE = 100 * (1 - pooled RR) with 95% CI derived from pooled log-RR.
- **Browser-hosted WebR cross-validation (optional, user-triggered).**

---

## 9. Certainty of Evidence (GRADE)

Standard GRADE domains. Anticipated HIGH certainty for RSV-LRTI / RSV-hospitalisation efficacy given large placebo-controlled pivotal sizes and consistent effect direction. **Timepoint-harmonisation note** applies.

---

## 10. Reporting and Dissemination

- **Reporting guideline:** PRISMA 2020
- **Published benchmark:** CDC/ACIP 2023 cites consistent 70-80% VE against RSV-LRTI across the nirsevimab pivotal programme.

---

## 11. Living-MA Update Cadence

- **Trigger:** (a) New nirsevimab real-world effectiveness data from US/EU/UK rollouts, (b) second-season booster-dose trials, (c) phase 3 trials of other long-acting anti-RSV monoclonals (clesrovimab).
- **Formal 3-monthly cadence:** Quarterly search + protocol-check.
- **Change-of-estimate threshold:** > MCID or > half 95% CI width triggers v1.x amendment.

---

## 12-14

Aggregate-data only. No competing interests, no funding.

---

## Appendix A. AMSTAR-2 Critical-Domain Self-Assessment

| # | Domain | Self-rating | Evidence / location |
|---|---|---|---|
| 2 (critical) | Protocol registered before data extraction | Yes (partial) | GitHub-canonical-URL freeze. |
| 4 (critical) | Comprehensive search strategy | Yes | §4. |
| 7 (critical) | List of excluded studies with reasons | Yes | Screening tab. |
| 9 (critical) | RoB assessment | Partial | Provisional; HARMONIE D2 SOME pre-specified. |
| 11 (critical) | Appropriate statistical methods | Yes | §8. |
| 13 (critical) | RoB accounted for in interpretation | Partial | GRADE §9. |
| 15 (critical) | Publication bias assessment | Yes (k-appropriate) | §8, k=3 so formal tests low-power. |
| 1 | PICO research question | Yes | §2. |

---

## Changelog

- **v1.1** (2026-04-20) — Initial editor-review-revision release.
