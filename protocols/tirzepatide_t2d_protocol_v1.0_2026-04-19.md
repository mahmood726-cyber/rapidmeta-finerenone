---
title: "Tirzepatide (Dual GIP/GLP-1 Agonist) for Glycaemic Control in Type 2 Diabetes"
slug: tirzepatide_t2d
version: 1.0
timestamp: 2026-04-19T00:00:00Z
date: 2026-04-19
specialty: Endocrinology (Diabetes)
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/tirzepatide_t2d_protocol_v1.0_2026-04-19.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/TIRZEPATIDE_T2D_REVIEW.html
license: MIT
---

# Tirzepatide (Dual GIP/GLP-1 Agonist) for Glycaemic Control in Type 2 Diabetes
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.0
**Frozen:** 2026-04-19T00:00:00Z
**Specialty:** Endocrinology (Diabetes)

---

## 1. Review Title and Registration

**Title:** Tirzepatide (Dual GIP/GLP-1 Agonist) for Glycaemic Control in Type 2 Diabetes: A Living Systematic Review and Meta-Analysis of the SURPASS Phase 3 Programme

**Registration:** Protocol frozen 2026-04-19T00:00:00Z and published at the canonical URL above. This protocol serves as the pre-registration for the living meta-analysis hosted at the app URL above. We note that the registration mechanism is a **GitHub-canonical-URL freeze** (immutable git history at the URL above, with a SHA anchor once the review is submitted) rather than a PROSPERO record. PROSPERO does not currently accept retrospective or already-completed-analysis registrations, which is why we use the canonical-URL mechanism here; authors targeting journals that require a PROSPERO number should register the protocol at PROSPERO before the first formal update cycle. Subsequent amendments will bump the `version` field and preserve prior versions in the `/protocols` directory of the rapidmeta-finerenone GitHub repository.

**Authors:** Mahmood Ahmad (corresponding). See GitHub repo for contributor acknowledgments.

**Corresponding address:** drmahmoodclinic@pm.me (GMC 6071047), Royal Free Hospital and Barnet Hospital, London, UK.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with type 2 diabetes (HbA1c 7.0-10.5%) — drug-naive or on background metformin/insulin |
| **Intervention** | Tirzepatide (dual GIP/GLP-1 receptor agonist) at 15 mg subcutaneously weekly |
| **Comparator** | Placebo or active comparator (insulin degludec, semaglutide) |
| **Outcome (primary)** | HbA1c change from baseline (%) at the trial's pre-specified primary timepoint |

---

## 3. Eligibility Criteria

### Inclusion
- Study design: Randomized controlled trials (parallel)
- Phase: III pivotal SURPASS trials or phase-3 comparative trials
- Participants: Adults with type 2 diabetes as per trial eligibility
- Intervention: Tirzepatide at 15 mg QW (top dose), with 5 mg and 10 mg arms reported as sensitivity
- Comparator: Placebo, insulin degludec titrated, semaglutide, or standard-of-care as active control
- Outcomes: HbA1c change from baseline reported as primary or co-primary endpoint
- Follow-up: >=40 weeks
- Publication: Peer-reviewed phase-3 publication

### Exclusion
- Type 1 diabetes, gestational diabetes, or paediatric populations
- Phase I/II dose-ranging studies without a blinded comparator arm
- Trials reporting weight loss as the sole primary outcome without HbA1c (see separate future review for obesity indications)
- Single-arm studies, real-world cohort analyses, post-marketing registries

---

## 4. Information Sources and Search Strategy

| Database | Query | Type |
|---|---|---|
| ClinicalTrials.gov | `tirzepatide AND type 2 diabetes` | Registry (API v2) |
| Europe PMC / PubMed | `tirzepatide AND HbA1c AND randomized` | Bibliographic |
| OpenAlex | Tirzepatide + diabetes concepts | Bibliographic |

**Search date:** Continuous (living review); formal snapshot at each new trial publication.

**Search updates:** The app re-queries CT.gov on user-triggered refresh; new trials matching the eligibility criteria are proposed as pending-include and require reviewer confirmation.

---

## 5. Study Selection

- **Stage 1 (auto-screen):** Keyword + publication-type classifier (0-100 score). Auto-exclude score <25.
- **Stage 2 (title/abstract):** Two-reviewer adjudication. Reviewer 1 proposes include/exclude with rationale. Reviewer 2 confirms. HMAC-signed seal per reviewer, timestamped.
- **Stage 3 (full text):** Verify eligibility; extract continuous (mean difference and SE) from the primary analysis.
- **Conflict resolution:** Re-review with exclusion reason in audit log. PRISMA 2020 flow auto-generated from search and screening counts.

---

## 6. Data Extraction

| Data item | Details |
|---|---|
| Study identifiers | NCT ID, PMID, DOI, first author, year |
| Participants | N randomized per arm, baseline HbA1c, baseline BMI, diabetes duration |
| Intervention details | Tirzepatide dose, dosing schedule, duration |
| Comparator | Placebo or active agent; target/titration rules if relevant |
| Outcome effects | Estimated treatment difference MD for HbA1c with SE; body weight MD; proportion reaching HbA1c targets |
| Risk of bias | Cochrane RoB 2 per trial (open-label active-comparator trials get SOME concerns on D2) |
| Source evidence | Verbatim extracts from published manuscripts with page/table refs |

---

## 7. Risk of Bias Assessment

Cochrane **RoB 2** for randomized trials. Per-trial assessment across 5 signalling domains (Low / Some concerns / High). Traffic-light plot per trial + stacked bar across domains.

> **Status flag:** Ratings in the current app are design-based prior judgments pending formal completion by a trained assessor. Open-label active-comparator arms (e.g. SURPASS-3 vs insulin degludec) carry `Some concerns` on D2 by design. A visible banner will indicate this status in the Extraction tab.

---

## 8. Synthesis / Statistical Methods

- **Primary pool:** DerSimonian-Laird random-effects inverse-variance weighting for continuous outcomes (mean difference scale, HbA1c in %).
- **CI adjustment:** Hartung-Knapp-Sidik-Jonkman (HKSJ) with t-distribution df = k-1; floor variance inflation at max(1, Q/(k-1)).
- **Prediction interval:** t-distribution with df = k-2 (Higgins 2009). Undefined for k < 3.
- **Heterogeneity:** Cochran Q (p-value), I^2 with Q-profile CI (Viechtbauer 2007), tau^2 (DL estimator).
- **Subgroup / meta-regression:** Background therapy (naive vs metformin vs insulin), baseline HbA1c.
- **Publication bias:** Not informative for k<4; defer to protocol-adherence (SURPASS programme pre-registration).
- **Sensitivity:** Leave-one-out; restrict to placebo-controlled trials; restrict to 40-week primary analyses.
- **Bayesian:** Grid-approximation random-effects with half-normal prior on tau; posterior with credible interval.
- **Cross-validation:** R (`metafor::rma`) and Python (`scipy`) reference scripts exportable from the Analysis Suite.

---

## 9. Certainty of Evidence (GRADE)

GRADE per outcome with downgrading domains:
- Risk of bias (>=50% of weight from trials rated Some concerns / High)
- Inconsistency (I^2 >=50% or PI crosses the null)
- Indirectness (PICO mismatch)
- Imprecision (CI crosses a minimally important difference — for HbA1c, MCID typically 0.3-0.5%)
- Publication bias (limited for k<4; note SURPASS programme pre-registration as mitigating)

Summary of Findings (SoF) table auto-generated from the GRADE profile.

---

## 10. Reporting and Dissemination

- **Reporting guideline:** PRISMA 2020 (27-item checklist exportable)
- **Export formats:** JSON state bundle, R validation script, Python validation script, PRISMA checklist CSV, HTML standalone report
- **Data integrity:** SHA-256 seal on every report; version timeline with delta alerts
- **Published benchmark:** Pooled MD for HbA1c change approximately -1.9% across SURPASS-1, -3, -5 at tirzepatide 15 mg QW, consistent with the SURPASS programme summary (Sattar N et al. Lancet Diabetes Endocrinol 2022 network meta-analysis).

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

- Raw trial event counts, MDs, and SEs are in the `realData` block of the app's source HTML (public GitHub repo).
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
