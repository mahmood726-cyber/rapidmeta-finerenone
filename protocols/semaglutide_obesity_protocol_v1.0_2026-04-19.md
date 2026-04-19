---
title: "Semaglutide 2.4 mg Once-Weekly for Weight Management in Adults with Overweight/Obesity"
slug: semaglutide_obesity
version: 1.0
timestamp: 2026-04-19T00:00:00Z
date: 2026-04-19
specialty: Endocrinology (Obesity/Metabolic)
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/semaglutide_obesity_protocol_v1.0_2026-04-19.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/SEMAGLUTIDE_OBESITY_REVIEW.html
license: MIT
---

# Semaglutide 2.4 mg Once-Weekly for Weight Management
## A Living Systematic Review and Meta-Analysis Protocol (STEP Phase 3 Programme)

**Protocol version:** 1.0
**Frozen:** 2026-04-19T00:00:00Z
**Specialty:** Endocrinology (Obesity/Metabolic)

---

## 1. Review Title and Registration

**Title:** Semaglutide 2.4 mg Once-Weekly for Weight Management in Adults with Overweight/Obesity: A Living Systematic Review and Meta-Analysis of the STEP Phase 3 Programme

**Registration:** Protocol frozen 2026-04-19T00:00:00Z and published at the canonical URL above.

**Authors:** Mahmood Ahmad (corresponding). See GitHub repo for contributor acknowledgments.

**Corresponding address:** drmahmoodclinic@pm.me (GMC 6071047), Royal Free Hospital and Barnet Hospital, London, UK.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with BMI >=30 (or >=27 with weight-related comorbidity), without type 2 diabetes |
| **Intervention** | Semaglutide 2.4 mg subcutaneously once weekly |
| **Comparator** | Placebo plus standardized lifestyle intervention |
| **Outcome (primary)** | Percentage change in body weight from baseline at the trial-specific primary timepoint (68-104 wk) |

---

## 3. Eligibility Criteria

### Inclusion
- Study design: Randomized controlled trials (parallel, double-blind)
- Phase: III pivotal STEP trials
- Participants: Adults meeting the obesity population definition
- Intervention: Semaglutide 2.4 mg QW at licensed obesity dose
- Comparator: Matched placebo + lifestyle intervention
- Outcomes: % body weight change reported as co-primary
- Follow-up: >=52 weeks
- Publication: Peer-reviewed phase-3 publication

### Exclusion
- Type 2 diabetes-only trials (SUSTAIN, PIONEER — see separate GLP1_CVOT review)
- Phase II dose-ranging studies
- Single-arm weight-loss cohort studies, real-world post-marketing registries
- Trials of other semaglutide doses (1.0 mg, 0.5 mg) not at the 2.4 mg obesity dose
- Paediatric trials (STEP-TEENS is tracked separately)

---

## 4. Information Sources and Search Strategy

| Database | Query | Type |
|---|---|---|
| ClinicalTrials.gov | `semaglutide 2.4 mg AND obesity AND randomized` | Registry |
| Europe PMC / PubMed | `semaglutide AND STEP AND weight AND randomized` | Bibliographic |
| OpenAlex | Semaglutide + obesity concepts | Bibliographic |

**Search date:** Continuous (living review).

---

## 5. Study Selection

- **Stage 1 (auto-screen):** Keyword + publication-type classifier (0-100 score).
- **Stage 2 (title/abstract):** Two-reviewer adjudication with HMAC-signed seal.
- **Stage 3 (full text):** Verify eligibility; extract continuous MD and SE from primary analysis.
- **Conflict resolution:** Re-review; PRISMA 2020 flow auto-generated.

---

## 6. Data Extraction

| Data item | Details |
|---|---|
| Study identifiers | NCT ID, PMID, DOI, first author, year |
| Participants | N randomized per arm, baseline BMI, baseline body weight, age |
| Intervention details | Semaglutide 2.4 mg QW duration |
| Comparator | Placebo + lifestyle arm composition |
| Outcome effects | % body weight MD and SE, responder proportions (>=5%, >=10%, >=15%, >=20%) |
| Risk of bias | Cochrane RoB 2 per trial |
| Source evidence | Verbatim excerpts from published tables |

---

## 7. Risk of Bias Assessment

Cochrane **RoB 2**. Design-based priors: double-blind placebo-controlled with calibrated site scales and treatment-policy estimand => LOW across D1-D5.

---

## 8. Synthesis / Statistical Methods

- **Primary pool:** DerSimonian-Laird random-effects IVW on MD scale (% body weight).
- **CI adjustment:** HKSJ with t-distribution df = k-1; floor at max(1, Q/(k-1)).
- **Prediction interval:** t-distribution df = k-2 (Higgins 2009). Undefined for k<3.
- **Heterogeneity:** Q (p-value), I^2 with Q-profile CI, tau^2 (DL).
- **Subgroup / meta-regression:** Intensive behavioural therapy vs standard lifestyle, 68-wk vs 104-wk follow-up.
- **Publication bias:** Limited for k<4; SURPASS-style pre-registration mitigates.
- **Sensitivity:** Leave-one-out; restrict to 68-wk primary analyses only.
- **Bayesian:** Grid-approximation with half-normal prior on tau.

---

## 9. Certainty of Evidence (GRADE)

Standard GRADE domains. MCID for body-weight MD typically ~5% in obesity trials.

---

## 10. Reporting and Dissemination

- **Reporting guideline:** PRISMA 2020
- **Published benchmark:** Pooled % body weight MD approximately -12% across STEP-1/-3/-5 at 2.4 mg (consistent with Singh N et al. 2024 network MA of the STEP programme).

---

## 11. Living-MA Update Cadence

- **Trigger:** User-initiated CT.gov + Europe PMC re-query; new STEP-family trials auto-proposed as pending-include.

---

## 12-14

AMSTAR-2 Appendix A under development. Data availability per GitHub repo; aggregate-data only. No competing interests; no funding.

---

## Changelog

- **v1.0** (2026-04-19) — Initial protocol registration at portfolio expansion of 2026-04-19.
