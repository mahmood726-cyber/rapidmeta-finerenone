---
title: "IL-23 Inhibitors for Moderate-to-Severe Plaque Psoriasis"
slug: il23_pso
version: 1.0
timestamp: 2026-04-19T00:00:00Z
date: 2026-04-19
specialty: Dermatology
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/il23_psoriasis_protocol_v1.0_2026-04-19.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/IL23_PSORIASIS_REVIEW.html
license: MIT
---

# IL-23 Inhibitors for Moderate-to-Severe Plaque Psoriasis
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.0
**Frozen:** 2026-04-19T00:00:00Z
**Specialty:** Dermatology

---

## 1. Review Title and Registration

**Title:** Interleukin-23 Inhibitors (Guselkumab, Risankizumab, Tildrakizumab) for Moderate-to-Severe Plaque Psoriasis: A Living Systematic Review and Meta-Analysis of Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-19T00:00:00Z and published at the canonical URL above. This protocol serves as the pre-registration for the living meta-analysis hosted at the app URL above. We note that the registration mechanism is a **GitHub-canonical-URL freeze** (immutable git history at the URL above, with a SHA anchor once the review is submitted) rather than a PROSPERO record. PROSPERO does not currently accept retrospective or already-completed-analysis registrations, which is why we use the canonical-URL mechanism here; authors targeting journals that require a PROSPERO number should register the protocol at PROSPERO before the first formal update cycle. Subsequent amendments will bump the `version` field and preserve prior versions in the `/protocols` directory of the rapidmeta-finerenone GitHub repository.

**Authors:** Mahmood Ahmad (corresponding). See GitHub repo for contributor acknowledgments.

**Corresponding address:** drmahmoodclinic@pm.me (GMC 6071047), Royal Free Hospital and Barnet Hospital, London, UK.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with moderate-to-severe plaque psoriasis (BSA >=10%, PASI >=12, IGA >=3) |
| **Intervention** | Selective IL-23 p19-subunit inhibitor (guselkumab, risankizumab, or tildrakizumab) at the licensed phase-3 regimen |
| **Comparator** | Placebo (co-primary evaluation); active comparators (adalimumab, ustekinumab) for head-to-head subgroup |
| **Outcome (primary)** | Proportion achieving PASI 90 at week 12 or week 16 (trial-specific pre-specified primary assessment) |

---

## 3. Eligibility Criteria

### Inclusion
- Study design: Randomized controlled trials (parallel, double-blind)
- Phase: III pivotal trials
- Participants: Adults with moderate-to-severe plaque psoriasis meeting the population definition
- Intervention: Guselkumab 100 mg SC, risankizumab 150 mg SC, or tildrakizumab 100/200 mg SC at licensed induction regimen
- Comparator: Placebo as co-primary control; active-comparator arms (adalimumab, ustekinumab) included where reported
- Outcomes: PASI 90 reported at the trial-specific pre-specified primary endpoint (week 12 for tildrakizumab; week 16 for guselkumab, risankizumab)
- Follow-up: >=12 weeks
- Publication: Peer-reviewed phase-3 publication

### Exclusion
- Paediatric psoriasis trials (separate review)
- Psoriatic arthritis-only trials without skin co-primary (separate review)
- Guttate, pustular, or erythrodermic psoriasis-only trials
- Phase I/II dose-finding studies without a pivotal confirmatory arm
- Observational, single-arm, or registry studies
- Non-selective IL-12/23 inhibitors (ustekinumab) as the intervention class (included only as active comparator)

---

## 4. Information Sources and Search Strategy

| Database | Query | Type |
|---|---|---|
| ClinicalTrials.gov | `(guselkumab OR risankizumab OR tildrakizumab) AND psoriasis` | Registry (API v2) |
| Europe PMC / PubMed | `IL-23 inhibitor AND plaque psoriasis AND randomized` | Bibliographic |
| OpenAlex | IL-23 p19 + psoriasis concepts | Bibliographic |

**Search date:** Continuous (living review); formal snapshot at each new trial publication.

**Search updates:** The app re-queries CT.gov on user-triggered refresh; new trials matching the eligibility criteria are proposed as pending-include and require reviewer confirmation.

---

## 5. Study Selection

- **Stage 1 (auto-screen):** Keyword + publication-type classifier (0-100 score). Auto-exclude score <25.
- **Stage 2 (title/abstract):** Two-reviewer adjudication. Reviewer 1 proposes include/exclude with rationale. Reviewer 2 confirms. HMAC-signed seal per reviewer, timestamped.
- **Stage 3 (full text):** Verify eligibility; extract 2x2 PASI 90 event counts per arm.
- **Conflict resolution:** Re-review with exclusion reason in audit log. PRISMA 2020 flow auto-generated from search and screening counts.

---

## 6. Data Extraction

| Data item | Details |
|---|---|
| Study identifiers | NCT ID, PMID, DOI, first author, year |
| Participants | N randomized per arm, baseline PASI, BSA, prior biologic exposure |
| Intervention details | Specific IL-23 inhibitor, dose, induction regimen |
| Comparator | Placebo; active comparator (adalimumab, ustekinumab) if applicable |
| Outcome events | PASI 90 counts per arm; IGA/sPGA/PGA 0-1; PASI 100; PASI 75 (secondary) |
| Risk of bias | Cochrane RoB 2 per trial (5 domains) |
| Source evidence | Verbatim extracts from published manuscripts with page/table refs |

---

## 7. Risk of Bias Assessment

Cochrane **RoB 2** for randomized trials. Per-trial assessment across 5 signalling domains (Low / Some concerns / High). Traffic-light plot per trial + stacked bar across domains.

> **Status flag:** Ratings in the current app are design-based prior judgments (double-blind placebo-matched schedule with central blinded PASI scoring = LOW by design across D1-D5) pending formal completion by a trained assessor. A visible banner will indicate this status in the Extraction tab.

---

## 8. Synthesis / Statistical Methods

- **Primary pool:** DerSimonian-Laird random-effects inverse-variance weighting on the log-odds scale for the PASI 90 binary outcome.
- **CI adjustment:** Hartung-Knapp-Sidik-Jonkman (HKSJ) with t-distribution df = k-1; floor variance inflation at max(1, Q/(k-1)).
- **Prediction interval:** t-distribution with df = k-2 (Higgins 2009). Undefined for k < 3.
- **Heterogeneity:** Cochran Q (p-value), I^2 with Q-profile CI (Viechtbauer 2007), tau^2 (DL estimator).
- **Subgroup / meta-regression:** By specific IL-23 inhibitor (guselkumab vs risankizumab vs tildrakizumab), by prior biologic exposure, by baseline PASI.
- **Publication bias:** Not informative for k<4; note pre-registered phase-3 programme minimizes selective reporting risk.
- **Sensitivity:** Leave-one-out; restrict to placebo-controlled arms; vary zero-cell correction (0.5 continuity vs Mantel-Haenszel without correction).
- **Bayesian:** Grid-approximation random-effects with half-normal prior on tau; posterior with credible interval on the log-odds scale.
- **Cross-validation:** R (`metafor::rma`) and Python (`scipy`) reference scripts exportable from the Analysis Suite.

---

## 9. Certainty of Evidence (GRADE)

GRADE per outcome with downgrading domains:
- Risk of bias (>=50% of weight from trials rated Some concerns / High)
- Inconsistency (I^2 >=50% or PI crosses the null)
- Indirectness (PICO mismatch — e.g. pooling across 3 related agents; flag for indirectness downgrade consideration)
- Imprecision (CI crosses a minimally important difference)
- Publication bias (k<4 limits formal testing; note pre-registered pivotal programme)

Summary of Findings (SoF) table auto-generated from the GRADE profile.

---

## 10. Reporting and Dissemination

- **Reporting guideline:** PRISMA 2020 (27-item checklist exportable)
- **Export formats:** JSON state bundle, R validation script, Python validation script, PRISMA checklist CSV, HTML standalone report
- **Data integrity:** SHA-256 seal on every report; version timeline with delta alerts
- **Published benchmark:** IL-23 p19 class network meta-analyses (Armstrong AW et al. JAMA Dermatol 2020; Sbidian E Cochrane 2022 `CD011535`) report PASI 90 OR in the range of 30-90 vs placebo at 12-16 weeks, depending on agent and timepoint.

---

## 11. Living-MA Update Cadence

- **Automatic trigger:** User-initiated re-query of ClinicalTrials.gov and Europe PMC from the Search tab.
- **Manual trigger:** Reviewer adds a newly-discovered trial via the Screening tab.
- **Protocol amendment cadence:** A new version of this protocol is cut whenever (a) the eligibility criteria change substantively, (b) the primary outcome is revised, or (c) a new trial is added that shifts the pooled estimate beyond the published-benchmark CI.

---

## 12. AMSTAR-2 Compliance Self-Declaration

> **Status flag:** A full AMSTAR-2 self-assessment table is under development and will be appended as Appendix A in a future version. The protocol structure above is designed to meet AMSTAR-2 critical domains 1, 2, 4, 7, 9, 11, 13, and 15.

---

## 13. Data Availability

- Raw trial event counts and ORs are in the `realData` block of the app's source HTML (public GitHub repo).
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
