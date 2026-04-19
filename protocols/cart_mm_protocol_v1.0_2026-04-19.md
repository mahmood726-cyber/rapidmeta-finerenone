---
title: "BCMA-Directed CAR-T Therapy in Relapsed/Refractory Multiple Myeloma"
slug: cart_mm
version: 1.0
timestamp: 2026-04-19T00:00:00Z
date: 2026-04-19
specialty: Oncology (Haematology)
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/cart_mm_protocol_v1.0_2026-04-19.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/CART_MM_REVIEW.html
license: MIT
---

# BCMA-Directed CAR-T Therapy in Relapsed/Refractory Multiple Myeloma
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.0
**Frozen:** 2026-04-19T00:00:00Z
**Specialty:** Oncology (Haematology)

---

## 1. Review Title and Registration

**Title:** BCMA-Directed CAR-T Therapy (Ciltacabtagene Autoleucel and Idecabtagene Vicleucel) vs Standard-of-Care Regimens in Relapsed/Refractory Multiple Myeloma: A Living Systematic Review and Meta-Analysis of Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-19T00:00:00Z.

**Authors:** Mahmood Ahmad (corresponding).

**Corresponding address:** drmahmoodclinic@pm.me (GMC 6071047), Royal Free Hospital and Barnet Hospital, London, UK.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with relapsed or refractory multiple myeloma after prior lines of therapy |
| **Intervention** | BCMA-directed CAR-T (ciltacabtagene autoleucel or idecabtagene vicleucel) single infusion |
| **Comparator** | Physicians-choice standard-of-care triplet regimen (DPd, DVd, PVd, IRd, Kd, EPd) |
| **Outcome (primary)** | Progression-free survival |

---

## 3. Eligibility Criteria

### Inclusion
- Study design: Randomized controlled trials (parallel, open-label with IRC-adjudicated primary endpoint)
- Phase: III pivotal trials
- Participants: Adults with RRMM after 1-4 prior lines depending on trial
- Intervention: BCMA-directed CAR-T at licensed dose
- Comparator: Physicians-choice SoC triplet
- Outcomes: PFS reported as primary
- Publication: Peer-reviewed phase-3 publication

### Exclusion
- Single-arm phase 1-2 CAR-T expansion cohorts (KarMMa-1, CARTITUDE-1, LEGEND-2)
- Myeloma subtypes other than relapsed/refractory (newly diagnosed — see CARTITUDE-5/-6)
- Non-BCMA targets (GPRC5D — Cartilage-1, Cartilage-2, MajesTEC-1)

---

## 4. Information Sources and Search Strategy

| Database | Query | Type |
|---|---|---|
| ClinicalTrials.gov | `(ciltacabtagene OR idecabtagene OR cilta-cel OR ide-cel) AND myeloma` | Registry |
| Europe PMC / PubMed | `CAR-T AND BCMA AND myeloma AND randomized` | Bibliographic |

---

## 5. Study Selection

Two-reviewer adjudication with HMAC-signed seal; PRISMA 2020 flow.

---

## 6. Data Extraction

| Data item | Details |
|---|---|
| Study identifiers | NCT ID, PMID, DOI |
| Participants | Prior-lines strata, triple-class exposure, N randomized and N infused |
| Intervention details | Specific CAR-T product, bridging therapy |
| Comparator | Physicians-choice triplet composition |
| Outcome effects | PFS HR + 95% CI, median PFS, ORR, sCR, safety (grade 3-4 CRS, neurotoxicity, TRM) |
| Risk of bias | Cochrane RoB 2 — D2 SOME concerns anticipated by open-label design |

---

## 7. Risk of Bias Assessment

Cochrane **RoB 2**. Design-based priors: D2 SOME CONCERNS (open-label by necessity — CAR-T single infusion vs ongoing triplet); other domains LOW (IRC adjudication, stratified randomization, SAP lock).

---

## 8. Synthesis / Statistical Methods

- **Primary pool:** DerSimonian-Laird random-effects IVW on log-HR scale.
- **CI adjustment:** HKSJ with t-distribution df = k-1.
- **Prediction interval:** Undefined for k<3 (we have k=2 at v1.0 — PI suppressed).
- **Heterogeneity:** Q (p-value), I^2, tau^2.
- **Subgroup / meta-regression:** By prior lines (1-3 vs 2-4), triple-class exposure.
- **Sensitivity:** Leave-one-out does not apply at k=2; flagged.
- **Updates:** CARTITUDE-5, CARTITUDE-6, KarMMa-9, and other ongoing CAR-T RCTs will be added when published.

---

## 9. Certainty of Evidence (GRADE)

PFS HR 0.26 (CARTITUDE-4) and 0.49 (KarMMa-3) both highly significant; heterogeneity reflects trial population (1-3 prior lines vs triple-class-exposed). GRADE downgrade for indirectness if pooling across agents without stratification.

---

## 10. Reporting and Dissemination

- **Reporting guideline:** PRISMA 2020
- **Published benchmark:** No single meta-analytic pool published at protocol freeze; app-computed DL pool of CARTITUDE-4 + KarMMa-3 is the reference.

---

## 11. Living-MA Update Cadence

- **Trigger:** CARTITUDE-5 (induction-line), CARTITUDE-6 (early-line), or new CAR-T phase 3 publications.

---

## 12-14

AMSTAR-2 appendix under development. Aggregate-data only. No funding, no competing interests.

---

## Changelog

- **v1.0** (2026-04-19) — Initial protocol registration.
