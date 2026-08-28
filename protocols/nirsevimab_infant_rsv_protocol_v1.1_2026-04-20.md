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
| 9 (critical) | RoB assessment | Yes | Authors have double-checked screening and data extraction against the record excerpts shown in the Extraction tab; the provisional AI-drafted RoB-2 ratings have been author-confirmed. Formal dual-assessor RoB-2 with inter-rater kappa remains a per-submission artefact (see Extraction-tab banner). |
| 11 (critical) | Appropriate statistical methods | Yes | §8. |
| 13 (critical) | RoB accounted for in interpretation | Partial | GRADE §9. |
| 15 (critical) | Publication bias assessment | Yes (k-appropriate) | §8, k=3 so formal tests low-power. |
| 1 | PICO research question | Yes | §2. |

---

## Changelog

- **v1.2** (2026-08-28) -- Amendment 1: five-source search executed under this protocol; protocol anchored before the first query and the search record anchored after. See Amendment 1.
- **v1.1** (2026-04-20) — Initial editor-review-revision release.

## Amendment 1 -- 2026-08-28 -- five-source search executed under this protocol

**This protocol governs the search for topic `nirsevimab-infant-rsv-review`. It is amended here, not replaced.**

Under Mahmood's ruling of 2026-08-28, an auto-generated protocol specifies nothing --
1,093 of them share a single byte-identical statistical-methods text -- and so cannot
govern a search. This file is **not** one of those 1,093, so it governs, and a draft
written later does not displace it.

**What is being done under it.** A search of five sources -- PubMed, Europe PMC,
ClinicalTrials.gov, an ICTRP route (ISRCTN), and guideline bodies as a source class --
executed on 2026-08-28, recorded in `ssot/nirsevimab-infant-rsv-review/SEARCH-RECORD.json`, with each source
carrying one of exactly three outcomes: EXECUTED, EMPTY, or FAILED. A non-200 is FAILED
and never carries a record count of zero.

**Ordering.** This file is committed and anchored in a public transparency log before the
first query for this topic is attempted, and the search record is anchored after it. Two
times supplied by a third party bracket the operation. The git commit timestamp is not
one of them: both dates on a git commit are supplied by whoever makes the commit and are
forgeable, which was demonstrated rather than assumed.

**What this protocol does not specify, stated so the record is not read as stronger than
it is.** Its substantive methods prose is shared with up to 40 other protocols in this
repository, including analysis-constraining statements such as the HKSJ variance-inflation
floor `max(1, Q/(k-1))`. It is a house-standard document with topic-specific headers, not
an individually reasoned protocol. It governs because it is not one of the 1,093 AUTO
templates -- which is the test the ruling set, and a lower bar than "bespoke".

**Guideline coverage is a fraction, never a checkmark.** GIN lists 136 bodies. The search
record states how many were queried, how many were reached and refused by a named
obstacle, and how many were never resolved to a queryable endpoint. "All guideline
bodies" is not a claim this search supports.
