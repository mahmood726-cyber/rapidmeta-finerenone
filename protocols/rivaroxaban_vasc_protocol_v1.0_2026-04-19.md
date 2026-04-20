---
title: "Rivaroxaban for Vascular Protection in CAD/PAD/HF"
slug: rivaroxaban_vasc
version: 1.0
timestamp: 2026-04-19T00:00:00Z
date: 2026-04-19
specialty: Cardiology (Vascular Protection)
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/rivaroxaban_vasc_protocol_v1.0_2026-04-19.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/RIVAROXABAN_VASC_REVIEW.html
license: MIT
---

# Rivaroxaban for Vascular Protection in CAD/PAD/HF
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.0
**Frozen:** 2026-04-19T00:00:00Z
**Specialty:** Cardiology (Vascular Protection)

---

## 1. Review Title and Registration

**Title:** Rivaroxaban for Vascular Protection in CAD/PAD/HF

**Registration:** Protocol frozen 2026-04-19T00:00:00Z and published at the canonical URL above. This protocol serves as the pre-registration for the living meta-analysis hosted at the app URL above. We note that the registration mechanism is a **GitHub-canonical-URL freeze** (immutable git history at the URL above, with a SHA anchor once the review is submitted) rather than a PROSPERO record. PROSPERO does not currently accept retrospective or already-completed-analysis registrations, which is why we use the canonical-URL mechanism here; authors targeting journals that require a PROSPERO number should register the protocol at PROSPERO before the first formal update cycle. Subsequent amendments will bump the `version` field and preserve prior versions in the `/protocols` directory of the rapidmeta-finerenone GitHub repository.

**Authors:** Mahmood Ahmad (corresponding). See GitHub repo for contributor acknowledgments.

**Corresponding address:** drmahmoodclinic@pm.me (GMC 6071047), Royal Free Hospital and Barnet Hospital, London, UK.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with chronic coronary or peripheral artery disease or heart failure |
| **Intervention** | Rivaroxaban 2.5 mg BID (vascular dose) added to antiplatelet therapy |
| **Comparator** | Antiplatelet therapy alone (placebo-equivalent rivaroxaban) |
| **Outcome (primary)** | MACE composite |

---

## 3. Eligibility Criteria

### Inclusion
- Study design: Randomized controlled trials (parallel or crossover)
- Phase: III or IV (Phase II included only if pivotal)
- Participants: Adults meeting the population definition above
- Intervention: Active drug or device matching the intervention definition
- Comparator: Matching the comparator definition (placebo or active)
- Outcomes: >=1 outcome matching the primary outcome or a secondary outcome in the pre-specified set
- Follow-up: >=12 weeks (or trial-specific primary assessment point)
- Publication: Published in a peer-reviewed journal OR results posted on ClinicalTrials.gov for a completed registered trial

### Exclusion
- Non-randomized, observational, single-arm, or case series
- Phase I or early Phase II
- Healthy volunteer trials, paediatric-only trials (unless condition-specific), or animal/in-vitro studies
- Re-analyses of the same cohort where a later primary-analysis publication supersedes
- Trials with duplicate cohorts already represented
- Editorials, letters, reviews (used for citation network only)

---

## 4. Information Sources and Search Strategy

| Database | Query | Type |
|---|---|---|
| ClinicalTrials.gov | Filter by intervention and condition matching PICO | Registry (API v2) |
| Europe PMC / PubMed | Drug class AND condition AND (randomized controlled trial) | Bibliographic |
| OpenAlex | Drug class AND condition concepts | Bibliographic |

**Search date:** Continuous (living review); formal snapshot at each new trial publication.

**Search updates:** The app re-queries CT.gov on user-triggered refresh; new trials matching the eligibility criteria are proposed as pending-include and require reviewer confirmation.

---

## 5. Study Selection

- **Stage 1 (auto-screen):** Keyword + publication-type classifier (0-100 score). Auto-exclude score <25.
- **Stage 2 (title/abstract):** Two-reviewer adjudication. Reviewer 1 proposes include/exclude with rationale. Reviewer 2 confirms. HMAC-signed seal per reviewer, timestamped.
- **Stage 3 (full text):** Verify eligibility; extract 2×2 event counts or HR/CI from the primary analysis.
- **Conflict resolution:** Re-review with exclusion reason in audit log. PRISMA 2020 flow auto-generated from search and screening counts.

---

## 6. Data Extraction

| Data item | Details |
|---|---|
| Study identifiers | NCT ID, PMID, DOI, first author, year |
| Participants | N randomized per arm, age, sex distribution, baseline severity, subgroup strata |
| Intervention details | Drug, dose, regimen; device, generation |
| Comparator | Placebo or active comparator |
| Outcome events | 2×2 table OR published HR/OR/MD with 95% CI |
| Risk of bias | Cochrane RoB 2 per trial (5 domains: randomization, deviations, missing data, outcome measurement, reported result) |
| Source evidence | Verbatim extracts from published manuscripts with page/table refs |

---

## 7. Risk of Bias Assessment

Cochrane **RoB 2** for randomized trials. Per-trial assessment across 5 signalling domains (Low / Some concerns / High). Traffic-light plot per trial + stacked bar across domains.

> **Status flag:** Ratings in the current app are **placeholder** pending completion by a trained assessor. A visible banner will indicate this status in the Extraction tab until real RoB-2 is entered.

---

## 8. Synthesis / Statistical Methods

- **Primary pool:** DerSimonian-Laird random-effects inverse-variance weighting on the log effect scale.
- **CI adjustment:** Hartung-Knapp-Sidik-Jonkman (HKSJ) with t-distribution df = k-1; floor variance inflation at max(1, Q/(k-1)).
- **Prediction interval:** t-distribution with df = k-2 (Higgins 2009). Undefined for k < 3.
- **Heterogeneity:** Cochran Q (p-value), I² with Q-profile CI (Viechtbauer 2007), τ² (DL estimator).
- **Subgroup / meta-regression:** Pre-specified by the Subgroup field in the app (see PICO Subgroup row).
- **Publication bias:** Contour-enhanced funnel plot; Egger's radial regression (k >=10); Duval-Tweedie trim-and-fill as sensitivity.
- **Sensitivity:** Leave-one-out; RoB-restricted pool.
- **Bayesian:** Grid-approximation random-effects with half-normal prior on τ; posterior with credible interval.
- **Cross-validation:** R (`metafor::rma`) and Python (`scipy`) reference scripts exportable from the Analysis Suite.

---

## 9. Certainty of Evidence (GRADE)

GRADE per outcome with downgrading domains:
- Risk of bias (>=50% of weight from trials rated Some concerns / High)
- Inconsistency (I² >=50% or PI crosses the null)
- Indirectness (PICO mismatch)
- Imprecision (CI crosses a minimally important difference)
- Publication bias (Egger p <0.10, asymmetric funnel)

Summary of Findings (SoF) table auto-generated from the GRADE profile.

---

## 10. Reporting and Dissemination

- **Reporting guideline:** PRISMA 2020 (27-item checklist exportable)
- **Export formats:** JSON state bundle, R validation script, Python validation script, PRISMA checklist CSV, HTML standalone report
- **Data integrity:** SHA-256 seal on every report; version timeline with delta alerts
- **Published benchmark:** Comparison to an independent published pooled estimate is displayed as a "vs published" chip in the Analysis tab; see `PUBLISHED_META_BENCHMARKS.json` for source citations.
- **Published benchmark (this topic):** HR 0.85 (0.77-0.94), k=4 (COMPASS + VOYAGER-PAD + COMMANDER-HF + ATLAS-ACS2)

---

## 11. Living-MA Update Cadence

- **Automatic trigger:** User-initiated re-query of ClinicalTrials.gov and Europe PMC from the Search tab.
- **Manual trigger:** Reviewer adds a newly-discovered trial via the Screening tab.
- **Protocol amendment cadence:** A new version of this protocol is cut whenever (a) the eligibility criteria change substantively, (b) the primary outcome is revised, or (c) a new trial is added that shifts the pooled estimate beyond the published-benchmark CI. Prior versions are preserved in `/protocols` with their frozen timestamp.

---

## 12. AMSTAR-2 Compliance Self-Declaration

> **Status flag:** A full AMSTAR-2 self-assessment table is under development and will be appended as Appendix A in a future version. The protocol structure above is designed to meet AMSTAR-2 critical domains 1, 2, 4, 7, 9, 11, 13, and 15.

---

## 13. Data Availability

- Raw trial event counts and HRs are in the `realData` block of the app's source HTML (public GitHub repo).
- Structured benchmarks for pooling cross-checks live in `PUBLISHED_META_BENCHMARKS.json` (same repo).
- This protocol document itself is version-controlled at the `canonical_url` above.
- No individual patient data are used; this is an aggregate-data meta-analysis.

---

## 14. Competing Interests and Funding

- **Funding:** None (independent academic review).
- **Competing interests:** None declared for the corresponding author.

---

## Changelog

- **v1.0** (2026-04-19T00:00:00Z) — Initial protocol registration frozen at portfolio expansion of 2026-04-19.
