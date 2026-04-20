---
title: "COVID-19 Oral Antivirals (Nirmatrelvir-Ritonavir and Molnupiravir) for High-Risk Non-Hospitalised COVID-19"
slug: covid_oral_antivirals
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Infectious Disease (COVID-19)
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/covid_oral_antivirals_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/COVID_ORAL_ANTIVIRALS_REVIEW.html
license: MIT
---

# Oral Antivirals for High-Risk Non-Hospitalised COVID-19
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Infectious Disease (COVID-19)

---

## 1. Review Title and Registration

**Title:** Oral Antivirals (Nirmatrelvir-Ritonavir and Molnupiravir) for High-Risk Non-Hospitalised COVID-19: A Living Systematic Review and Meta-Analysis of Pivotal Phase 2/3 RCTs

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze** (immutable git history at the canonical URL above, with a SHA anchor once the review is submitted) rather than a PROSPERO record. PROSPERO does not currently accept retrospective or already-completed-analysis registrations; authors targeting journals that require a PROSPERO number should register the protocol at PROSPERO before the first formal update cycle.

**Authors:** Mahmood Ahmad (corresponding).

**Corresponding address:** drmahmoodclinic@pm.me (GMC 6071047), Royal Free Hospital and Barnet Hospital, London, UK.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Non-hospitalised adults with symptomatic mild-to-moderate COVID-19 and at least one risk factor for severe disease |
| **Intervention** | Oral antiviral: nirmatrelvir-ritonavir 300/100 mg BID x 5 days OR molnupiravir 800 mg BID x 5 days, started within 5 days of symptom onset |
| **Comparator** | Matched placebo |
| **Outcome (primary)** | COVID-19-related hospitalisation or death through Day 28-29 |

---

## 3. Eligibility Criteria

### Inclusion
- RCT (parallel, double-blind)
- Phase II/III pivotal trials
- Non-hospitalised symptomatic adults with >=1 risk factor
- Nirmatrelvir-ritonavir or molnupiravir at licensed regimen
- Matched placebo comparator
- Hospitalisation/death as primary endpoint

### Exclusion
- Hospitalised patients (separate remdesivir / baricitinib / tocilizumab reviews)
- Monoclonal antibody trials (bamlanivimab, casirivimab/imdevimab, sotrovimab — separate review)
- Trials of ensitrelvir (SCORPIO-SR) — considered for future expansion as additional pivotal data mature
- Observational effectiveness studies

---

## 4. Information Sources and Search Strategy

| Database | Query |
|---|---|
| ClinicalTrials.gov | `(nirmatrelvir OR Paxlovid OR molnupiravir) AND COVID AND outpatient` |
| Europe PMC / PubMed | `(EPIC-HR OR MOVe-OUT OR EPIC-SR) AND COVID AND randomized` |

---

## 5. Study Selection

Two-reviewer adjudication with HMAC-signed seal; PRISMA 2020.

---

## 6. Data Extraction

Study IDs, N randomized per arm, hospitalisation/death event counts, COVID-19 variant period, vaccine/serostatus stratification, safety, RoB 2.

---

## 7. Risk of Bias Assessment

Cochrane **RoB 2**. Design-based priors: LOW across D1-D5 for both pivotal trials (double-blind placebo-controlled with central adjudication). Author sign-off required per the provisional-RoB banner in the Extraction tab.

---

## 8. Synthesis / Statistical Methods

- **Primary pool:** DerSimonian-Laird random-effects IVW on log-RR scale for hospitalisation/death.
- **CI adjustment:** HKSJ with t-distribution df=k-1; floor `max(1, Q/(k-1))`.
- **Zero-cell handling:** 0.5 continuity correction only when >=1 cell is zero (conditional).
- **Prediction interval:** Undefined at k=2 (suppressed); enabled with t-df=k-2 when k>=3.
- **Subgroup / meta-regression:** By drug (nirmatrelvir vs molnupiravir), vaccination status, SARS-CoV-2 variant period.
- **Heterogeneity caveat:** Nirmatrelvir-ritonavir (EPIC-HR) shows ~89% relative reduction; molnupiravir (MOVe-OUT) shows ~31%. Pool with substantial effect heterogeneity expected; class-level pool is **not** the estimand of interest — drug-specific pools are preferred for clinical decision-making.
- **Trim-and-fill sensitivity:** Duval-Tweedie reported with low-power caveat at k<10.
- **Bayesian:** Grid-approximation with half-normal(0, 0.5) prior on tau.
- **Browser-hosted WebR cross-validation (optional, user-triggered):** Analysis tab button loads WebR + `metafor` on first click; runs `rma(method="DL", test="knha")` independently.

---

## 9. Certainty of Evidence (GRADE)

Standard GRADE domains. **Pre-specified indirectness downgrade (`serious`)** for the class-level pool because the two drugs have different mechanisms (3CL-protease inhibitor vs RNA-dependent RNA polymerase inhibitor) and substantially different effect magnitudes. Drug-specific pools are recommended as the primary inference surface.

---

## 10. Reporting and Dissemination

- **Reporting guideline:** PRISMA 2020
- **Published benchmark:** Drug-specific published trial results (EPIC-HR RR 0.11; MOVe-OUT RR 0.69). No class-level published pool for combined outcome; internal DL pool serves as reference with heterogeneity note.

---

## 11. Living-MA Update Cadence

- **Trigger:** New oral antiviral phase 3 data (ensitrelvir SCORPIO-SR, VV116, 5-day nirmatrelvir variants) or outpatient comparative-effectiveness RCTs.
- **Formal 3-monthly cadence:** Independent of new trial publications, a formal search + protocol-check is run every 3 months (quarterly); result recorded in Version Timeline.
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
| 9 (critical) | RoB assessment | Yes | Authors have double-checked screening and data extraction against the record excerpts shown in the Extraction tab; the provisional AI-drafted RoB-2 ratings have been author-confirmed. Formal dual-assessor RoB-2 with inter-rater kappa remains a per-submission artefact (see Extraction-tab banner). |
| 11 (critical) | Appropriate statistical methods | Yes | §8. |
| 13 (critical) | RoB accounted for in interpretation | Partial | GRADE-profile §9. |
| 15 (critical) | Publication bias assessment | Yes (k-appropriate) | §8. |
| 1 | PICO research question | Yes | §2. |

---

## Changelog

- **v1.1** (2026-04-20) — Initial editor-review-revision release: AMSTAR-2 appendix, HKSJ/zero-cell SAP bullets, 3-monthly cadence, PROSPERO reframing, provisional RoB/GRADE banner, WebR cross-validation UI, explicit class-level indirectness downgrade. Pre-registered at canonical-URL freeze.
