---
title: "Respiratory Syncytial Virus Vaccines in Adults >=60 Years"
slug: rsv_vaccine_older
version: 1.0
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Respiratory (Vaccinology)
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/rsv_vaccine_older_protocol_v1.0_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/RSV_VACCINE_OLDER_REVIEW.html
license: MIT
---

# RSV Vaccines in Adults >=60 Years
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.0
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Respiratory (Vaccinology)

---

## 1. Review Title and Registration

**Title:** Respiratory Syncytial Virus Vaccines in Adults >=60 Years: A Living Systematic Review and Meta-Analysis of Phase 3 Efficacy RCTs (RSVpreF / Abrysvo, Adjuvanted Prefusion F / Arexvy, mRNA-1345 / mRESVIA)

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze** (immutable git history at the canonical URL above, with a SHA anchor once the review is submitted) rather than a PROSPERO record. PROSPERO does not currently accept retrospective or already-completed-analysis registrations; authors targeting journals that require a PROSPERO number should register the protocol at PROSPERO before the first formal update cycle.
**Authors:** Mahmood Ahmad (corresponding).

**Corresponding address:** drmahmoodclinic@pm.me (GMC 6071047), Royal Free Hospital and Barnet Hospital, London, UK.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults aged >=60 years |
| **Intervention** | Licensed RSV vaccine (Abrysvo RSVpreF 120 mcg IM; Arexvy AS01E-adjuvanted prefusion F IM; mRNA-1345 50 mcg IM) single dose |
| **Comparator** | Matched saline placebo IM single dose |
| **Outcome (primary)** | RSV-associated lower respiratory tract disease (RSV-LRTD) over the first RSV season (or event-driven primary analysis) |

---

## 3. Eligibility Criteria

### Inclusion
- RCT (parallel, double-blind, individually randomized)
- Phase III pivotal efficacy trials
- Adults >=60 years
- Licensed RSV vaccine single dose as intervention
- Matched placebo IM injection
- RSV-LRTD confirmed by PCR reported as primary or co-primary

### Exclusion
- Maternal RSV vaccine trials in pregnancy (MATISSE — separate review)
- Paediatric trials (<60 years) or mixed-age trials without pre-specified >=60 subgroup primary
- Trials of monoclonal antibodies (nirsevimab, palivizumab) in high-risk adults
- Post-licensure observational effectiveness studies

---

## 4. Information Sources and Search Strategy

| Database | Query |
|---|---|
| ClinicalTrials.gov | `(RSV vaccine OR RSVpreF OR mRNA-1345) AND older adults AND randomized` |
| Europe PMC / PubMed | `RSV vaccine AND >=60 AND randomized` |

---

## 5. Study Selection

Two-reviewer adjudication with HMAC-signed seal; PRISMA 2020.

---

## 6. Data Extraction

Study IDs, N randomized, age strata (>=60, >=70), vaccine composition/adjuvant, case counts (vaccine vs placebo) for primary (RSV-LRTD >=2 or >=3 signs/symptoms per trial), severe RSV-LRTD, safety (solicited local/systemic, SAEs), RoB 2.

---

## 7. Risk of Bias Assessment

Cochrane **RoB 2**. Design-based priors: LOW across D1-D5 (double-blind placebo-controlled, central RT-PCR confirmation, blinded adjudication panel, SAP locked).

---

## 8. Synthesis / Statistical Methods

- **Primary pool:** DerSimonian-Laird random-effects IVW on log-RR scale for RSV-LRTD.
- **CI adjustment:** HKSJ with t-distribution df = k-1.
- **Prediction interval:** t df = k-2 (Higgins 2009).
- **Subgroup / meta-regression:** By vaccine platform (protein RSVpreF, adjuvanted protein, mRNA), by age strata (>=60 vs >=70), by case definition (>=2 vs >=3 signs/symptoms).
- **Sensitivity:** Leave-one-out; adjudicated RSV-LRTD case-definition restriction.
- **Zero-cell correction:** Apply Mantel-Haenszel without continuity correction where only one arm has events.
- **Vaccine efficacy reporting:** VE = 100 * (1 - pooled RR) with 95% CI derived from pooled log-RR.

---

## 9. Certainty of Evidence (GRADE)

Standard GRADE domains. Anticipated HIGH certainty for RSV-LRTD efficacy given large placebo-controlled phase 3 sample sizes and consistent effect direction.

---

## 10. Reporting and Dissemination

- **Reporting guideline:** PRISMA 2020
- **Published benchmark:** ACIP 2023 recommendation notes VE approximately 80% across Abrysvo/Arexvy/mRESVIA pivotal trials for RSV-LRTD in adults >=60 after first season.

---

## 11. Living-MA Update Cadence

Trigger: (a) multi-season follow-up data for the three licensed vaccines, (b) new phase 3 RSV vaccine trials (e.g. Sanofi/Janssen candidates), (c) head-to-head or mix-and-match dosing trials.

---

## 12-14

AMSTAR-2 appendix under development. Aggregate-data only. No competing interests, no funding.

---

## Changelog

- **v1.0** (2026-04-20) — Initial protocol registration.
