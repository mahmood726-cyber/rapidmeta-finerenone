---
title: "JAK Inhibitors (Baricitinib, Upadacitinib, Filgotinib) in MTX-Inadequate-Response Rheumatoid Arthritis"
slug: jak_ra
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Rheumatology
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/jak_ra_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/JAK_RA_REVIEW.html
license: MIT
---

# JAK Inhibitors in MTX-Inadequate-Response Rheumatoid Arthritis
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Rheumatology

---

## 1. Review Title and Registration

**Title:** Janus Kinase (JAK) Inhibitors (Baricitinib, Upadacitinib, Filgotinib) added to Background Methotrexate vs Placebo + Methotrexate in Methotrexate-Inadequate-Response Rheumatoid Arthritis: A Living Systematic Review and Meta-Analysis of Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze** (immutable git history at the canonical URL above). PROSPERO does not currently accept retrospective or already-completed-analysis registrations; authors targeting journals that require a PROSPERO number should register the protocol at PROSPERO before the first formal update cycle.

**Authors:** Mahmood Ahmad (corresponding).

**Corresponding address:** drmahmoodclinic@pm.me (GMC 6071047), Royal Free Hospital and Barnet Hospital, London, UK.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with active RA and inadequate response to methotrexate (MTX-IR) or conventional-synthetic DMARDs |
| **Intervention** | Baricitinib 4 mg PO daily OR upadacitinib 15 mg PO daily OR filgotinib 200 mg PO daily, added to background MTX |
| **Comparator** | Placebo added to background MTX |
| **Outcome (primary)** | ACR20 response at week 12 |

---

## 3. Eligibility Criteria

### Inclusion
- RCT (parallel, double-blind)
- Phase III pivotal trials
- Adults MTX-IR or csDMARD-IR
- Any licensed JAK inhibitor at label dose vs placebo
- ACR20 at week 12 as primary or co-primary

### Exclusion
- Active-comparator-only trials (no placebo arm)
- Tofacitinib trials (approved 2012; pivotals pre-2015 — separate review)
- RA patients naïve to any DMARD (separate review)

---

## 4. Information Sources and Search Strategy

| Database | Query |
|---|---|
| ClinicalTrials.gov | `(baricitinib OR upadacitinib OR filgotinib) AND rheumatoid arthritis AND methotrexate` |
| Europe PMC / PubMed | `(RA-BEAM OR SELECT-NEXT OR FINCH-1) AND randomized` |

---

## 5. Study Selection

Two-reviewer adjudication with HMAC-signed seal; PRISMA 2020.

---

## 6. Data Extraction

Study IDs, N per arm, ACR20/50/70 counts, DAS28-CRP, HAQ-DI, safety (VTE, MACE, serious infection per ORAL Surveillance signal), RoB 2.

---

## 7. Risk of Bias Assessment

Cochrane **RoB 2**. Design-based priors: LOW across D1-D5 for all three pivotal placebo-controlled comparisons. Author sign-off required per the provisional-RoB banner.

---

## 8. Synthesis / Statistical Methods

- **Primary pool:** DerSimonian-Laird random-effects IVW on log-OR scale for ACR20.
- **CI adjustment:** HKSJ with t-distribution df=k-1; floor `max(1, Q/(k-1))`.
- **Prediction interval:** t-df=k-2 (Higgins 2009), enabled at k=3.
- **Subgroup / meta-regression:** By JAK agent (baricitinib vs upadacitinib vs filgotinib), prior biologic exposure, baseline DAS28.
- **Zero-cell handling:** Conditional 0.5 continuity correction.
- **Trim-and-fill sensitivity:** Duval-Tweedie low-power caveat at k<10.
- **Safety:** Separate pool for MACE + VTE + serious infection using ORAL Surveillance + JAK-class PMS data.
- **Bayesian:** Grid-approximation with half-normal(0, 0.5) prior on tau.
- **Browser-hosted WebR cross-validation (optional, user-triggered).**

---

## 9. Certainty of Evidence (GRADE)

Standard GRADE domains. **Pre-specified class-level indirectness downgrade (`serious`)** for the pool across three distinct JAK agents; agent-specific inference preferred.

---

## 10. Reporting and Dissemination

- **Reporting guideline:** PRISMA 2020
- **Published benchmark:** Singh JA et al. 2022 ACR-class network MA reports ACR20 OR for JAKi class approximately 3.3 vs placebo across these pivotal trials.

---

## 11. Living-MA Update Cadence

- **Trigger:** New JAKi phase 3 RCTs (e.g., deucravacitinib RA, emerging TYK2/JAK3-selective agents) or safety updates.
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
| 9 (critical) | RoB assessment | Yes | Authors have double-checked screening and data extraction against the record excerpts shown in the Extraction tab; the provisional AI-drafted RoB-2 ratings have been author-confirmed. Formal dual-assessor RoB-2 with inter-rater kappa remains a per-submission artefact (see Extraction-tab banner). |
| 11 (critical) | Appropriate statistical methods | Yes | §8. |
| 13 (critical) | RoB accounted for in interpretation | Partial | GRADE §9. |
| 15 (critical) | Publication bias assessment | Yes (k-appropriate) | §8. |
| 1 | PICO research question | Yes | §2. |

---

## Changelog

- **v1.1** (2026-04-20) — Initial editor-review-revision release.
