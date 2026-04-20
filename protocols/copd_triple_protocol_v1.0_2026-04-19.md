---
title: "Single-Inhaler Triple Therapy (ICS + LABA + LAMA) for Symptomatic COPD"
slug: copd_triple
version: 1.0
timestamp: 2026-04-19T00:00:00Z
date: 2026-04-19
specialty: Respiratory
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/copd_triple_protocol_v1.0_2026-04-19.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/COPD_TRIPLE_REVIEW.html
license: MIT
---

# Single-Inhaler Triple Therapy (ICS + LABA + LAMA) for Symptomatic COPD
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.0
**Frozen:** 2026-04-19T00:00:00Z
**Specialty:** Respiratory

---

## 1. Review Title and Registration

**Title:** Single-Inhaler Triple Therapy (ICS + LABA + LAMA) vs Dual Therapy for Symptomatic COPD with Exacerbation History: A Living Systematic Review and Meta-Analysis of Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-19T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze** (immutable git history at the canonical URL above, with a SHA anchor once the review is submitted) rather than a PROSPERO record. PROSPERO does not currently accept retrospective or already-completed-analysis registrations; authors targeting journals that require a PROSPERO number should register the protocol at PROSPERO before the first formal update cycle.
**Authors:** Mahmood Ahmad (corresponding).

**Corresponding address:** drmahmoodclinic@pm.me (GMC 6071047), Royal Free Hospital and Barnet Hospital, London, UK.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with symptomatic COPD (FEV1 25-80% predicted) and >=1 moderate/severe exacerbation in prior year |
| **Intervention** | Single-inhaler triple therapy (ICS + LABA + LAMA fixed-dose combination: FF/UMEC/VI or BGF) |
| **Comparator** | Dual LAMA/LABA (UMEC/VI, GFF) — primary class comparison |
| **Outcome (primary)** | Moderate or severe exacerbation rate ratio vs LAMA/LABA dual |

---

## 3. Eligibility Criteria

### Inclusion
- Study design: RCT (parallel, double-blind, double-dummy where masking requires multiple inhaler devices)
- Phase: III pivotal trials
- Population: Symptomatic COPD matching the population definition
- Intervention: Licensed single-inhaler triple (FF/UMEC/VI 100/62.5/25; BGF 320/18/9.6)
- Comparator: Dual LAMA/LABA (UMEC/VI; GFF); ICS/LABA dual also captured as secondary
- Outcomes: Exacerbation rate as primary or co-primary
- Follow-up: >=24 weeks; 52-week durations preferred
- Publication: Peer-reviewed phase-3 publication

### Exclusion
- Open-triple using separate inhalers (TRIBUTE, TRILOGY — separate review)
- Phase II dose-finding studies
- Studies in asthma or asthma-COPD overlap without a pre-specified COPD primary analysis
- Observational/registry/single-arm studies

---

## 4. Information Sources and Search Strategy

| Database | Query | Type |
|---|---|---|
| ClinicalTrials.gov | `(triple therapy OR ICS/LABA/LAMA) AND COPD AND randomized` | Registry |
| Europe PMC / PubMed | `COPD triple therapy exacerbation randomized` | Bibliographic |

---

## 5. Study Selection

Two-reviewer adjudication with HMAC-signed seal; PRISMA 2020.

---

## 6. Data Extraction

| Data item | Details |
|---|---|
| Study identifiers | NCT ID, PMID, DOI |
| Participants | N per arm, FEV1 % predicted strata, prior exacerbation count, smoking status |
| Intervention details | Specific molecule combination, device (MDI vs DPI), dose |
| Comparator | Dual LAMA/LABA specific molecules |
| Outcome effects | Moderate/severe exacerbation RR + 95% CI; severe (hospitalisation) RR; trough FEV1 MD; SGRQ MD; pneumonia rate |
| Risk of bias | Cochrane RoB 2 |

---

## 7. Risk of Bias Assessment

Cochrane **RoB 2**. Design-based priors: LOW across D1-D5 for IMPACT, ETHOS, KRONOS (double-blind double-dummy, central exacerbation validation, SAP locked).

---

## 8. Synthesis / Statistical Methods

- **Primary pool:** DerSimonian-Laird random-effects IVW on log-rate-ratio scale for moderate/severe exacerbations (vs LAMA/LABA).
- **CI adjustment:** HKSJ with t-distribution df = k-1.
- **Prediction interval:** t-distribution df = k-2 (Higgins 2009).
- **Heterogeneity:** Q (p-value), I^2 with Q-profile CI, tau^2.
- **Subgroup / meta-regression:** By exacerbation-history entry criterion (>=1 vs >=2), by eosinophil strata (when reported).
- **Sensitivity:** Leave-one-out; restrict to 52-week trials (IMPACT + ETHOS).
- **Safety secondary:** Pneumonia incidence pooled separately given ICS class effect.

---

## 9. Certainty of Evidence (GRADE)

Standard GRADE domains. Imprecision: CIs for individual trials narrow; pooled RR likely HIGH certainty for the exacerbation-rate endpoint.

---

## 10. Reporting and Dissemination

- **Reporting guideline:** PRISMA 2020
- **Published benchmark:** Calzetta L et al. ERJ Open Res 2022 meta-analysis reported pooled moderate/severe exacerbation rate ratio approximately 0.74 (0.68-0.80) for single-inhaler triple vs LAMA/LABA across 3 phase 3 RCTs.

---

## 11. Living-MA Update Cadence

- **Trigger:** New single-inhaler triple phase 3 publications (e.g. mepolizumab COPD adjunct) or ICS stepdown RCTs.

---

## 12-14

AMSTAR-2 appendix under development. Aggregate-data only. No funding, no competing interests.

---

## Changelog

- **v1.0** (2026-04-19) — Initial protocol registration.
