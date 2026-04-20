---
title: "High-Efficacy Anti-CD20 Monoclonal Antibodies in Relapsing-Remitting Multiple Sclerosis"
slug: highefficacy_ms
version: 1.0
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Neurology
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/highefficacy_ms_protocol_v1.0_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/HIGH_EFFICACY_MS_REVIEW.html
license: MIT
---

# High-Efficacy Anti-CD20 mAbs vs Platform DMTs in Relapsing MS
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.0
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Neurology

---

## 1. Review Title and Registration

**Title:** High-Efficacy Anti-CD20 Monoclonal Antibodies (Ocrelizumab, Ofatumumab) vs Platform Disease-Modifying Therapies in Relapsing-Remitting Multiple Sclerosis: A Living Systematic Review and Meta-Analysis of Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze** (immutable git history at the canonical URL above, with a SHA anchor once the review is submitted) rather than a PROSPERO record. PROSPERO does not currently accept retrospective or already-completed-analysis registrations; authors targeting journals that require a PROSPERO number should register the protocol at PROSPERO before the first formal update cycle.
**Authors:** Mahmood Ahmad (corresponding).

**Corresponding address:** drmahmoodclinic@pm.me (GMC 6071047), Royal Free Hospital and Barnet Hospital, London, UK.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with relapsing-remitting MS (EDSS 0-5.5, >=1 relapse in prior year or >=2 in prior 2 years) |
| **Intervention** | Ocrelizumab 600 mg IV Q24W or ofatumumab 20 mg SC monthly at licensed regimen |
| **Comparator** | Platform DMT (interferon beta-1a or teriflunomide) at licensed dose |
| **Outcome (primary)** | Annualized relapse rate ratio |

---

## 3. Eligibility Criteria

### Inclusion
- RCT (parallel, double-blind double-dummy)
- Phase III pivotal trials
- RRMS adults meeting entry criteria
- High-efficacy anti-CD20 mAb intervention
- Platform DMT comparator (IFN-beta-1a 44 mcg SC 3x/week; teriflunomide 14 mg PO daily)
- Annualized relapse rate reported as primary
- Follow-up >=24 months (or event-driven primary analysis)

### Exclusion
- Primary progressive MS (ORATORIO — separate review)
- Relapsing MS trials of other agents (fingolimod FREEDOMS, cladribine CLARITY, natalizumab AFFIRM — considered for future expansion)
- Extension studies without parallel control

---

## 4. Information Sources and Search Strategy

| Database | Query |
|---|---|
| ClinicalTrials.gov | `(ocrelizumab OR ofatumumab) AND relapsing multiple sclerosis` |
| Europe PMC / PubMed | `(OPERA OR ASCLEPIOS) AND multiple sclerosis` |

---

## 5. Study Selection

Two-reviewer adjudication with HMAC-signed seal; PRISMA 2020.

---

## 6. Data Extraction

Study IDs, N randomized, baseline EDSS, ARR per arm, confirmed disability progression HR, Gd-enhancing lesion counts, safety (infections, infusion reactions), RoB 2.

---

## 7. Risk of Bias Assessment

Cochrane **RoB 2**. Design-based priors: LOW across D1-D5 (double-blind double-dummy with matched SC injections and IV infusions; blinded MRI and EDSS assessors).

---

## 8. Synthesis / Statistical Methods

- **Primary pool:** DerSimonian-Laird random-effects IVW on log-rate-ratio scale for ARR.
- **CI adjustment:** HKSJ with t-distribution df = k-1.
- **Prediction interval:** t df = k-2 (Higgins 2009).
- **Subgroup / meta-regression:** By anti-CD20 agent (ocrelizumab IV vs ofatumumab SC), by platform comparator (IFN vs teriflunomide).
- **Sensitivity:** Leave-one-out; pair-wise replicate (OPERA-I+II or ASCLEPIOS-I+II) as primary, cross-class as secondary.
- **Bayesian:** Grid-approximation with half-normal prior on tau.

---

## 9. Certainty of Evidence (GRADE)

Standard GRADE domains.

---

## 10. Reporting and Dissemination

- **Reporting guideline:** PRISMA 2020
- **Published benchmark:** Composite anti-CD20-vs-platform ARR rate ratio approximately 0.5 across 4 pivotal phase 3 trials (pooled OPERA + ASCLEPIOS data).

---

## 11. Living-MA Update Cadence

Trigger: new anti-CD20 (rituximab, ublituximab — ULTIMATE trial) or B-cell-depleting phase 3 publications.

---

## 12-14

AMSTAR-2 appendix under development. Aggregate-data only. No competing interests, no funding.

---

## Changelog

- **v1.0** (2026-04-20) — Initial protocol registration.
