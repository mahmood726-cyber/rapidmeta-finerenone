---
title: "Direct Oral Anticoagulants vs Warfarin in Non-Valvular Atrial Fibrillation"
slug: doac_af
version: 1.0
timestamp: 2026-04-19T00:00:00Z
date: 2026-04-19
specialty: Cardiology (Anticoagulation)
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/doac_af_protocol_v1.0_2026-04-19.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/DOAC_AF_REVIEW.html
license: MIT
---

# Direct Oral Anticoagulants vs Warfarin in Non-Valvular Atrial Fibrillation
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.0
**Frozen:** 2026-04-19T00:00:00Z
**Specialty:** Cardiology (Anticoagulation)

---

## 1. Review Title and Registration

**Title:** Direct Oral Anticoagulants vs Warfarin in Non-Valvular Atrial Fibrillation

**Registration:** Protocol frozen 2026-04-19T00:00:00Z and published at the canonical URL above. This protocol serves as the pre-registration for the living meta-analysis hosted at the app URL above. We note that the registration mechanism is a **GitHub-canonical-URL freeze** (immutable git history at the URL above, with a SHA anchor once the review is submitted) rather than a PROSPERO record. PROSPERO does not currently accept retrospective or already-completed-analysis registrations, which is why we use the canonical-URL mechanism here; authors targeting journals that require a PROSPERO number should register the protocol at PROSPERO before the first formal update cycle. Subsequent amendments will bump the `version` field and preserve prior versions in the `/protocols` directory of the rapidmeta-finerenone GitHub repository.

**Authors:** Mahmood Ahmad (corresponding). See GitHub repo for contributor acknowledgments.

**Corresponding address:** drmahmoodclinic@pm.me (GMC 6071047), Royal Free Hospital and Barnet Hospital, London, UK.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with non-valvular atrial fibrillation eligible for oral anticoagulation (CHADS2 >=1 or CHA2DS2-VASc >=2) |
| **Intervention** | Direct oral anticoagulant (dabigatran, rivaroxaban, apixaban, or edoxaban) at the phase-3 licensed dose |
| **Comparator** | Dose-adjusted warfarin (VKA) targeting INR 2.0-3.0 |
| **Outcome (primary)** | Composite of stroke or systemic embolism |

---

## 3. Eligibility Criteria

### Inclusion
- Study design: Randomized controlled trials (parallel, double- or open-label with blinded endpoint adjudication)
- Phase: III pivotal trials
- Participants: Adults with non-valvular AF eligible for long-term oral anticoagulation
- Intervention: DOAC at the licensed phase-3 dose (dabigatran 150 mg BD, rivaroxaban 20 mg OD, apixaban 5 mg BD, edoxaban 60 mg OD)
- Comparator: Adjusted-dose warfarin (target INR 2.0-3.0)
- Outcomes: Stroke/systemic embolism reported as primary or co-primary endpoint
- Follow-up: Median follow-up >=1 year
- Publication: Peer-reviewed phase-3 publication

### Exclusion
- Valvular AF (mechanical or moderate-to-severe mitral stenosis)
- Single-arm, observational, or registry studies
- Phase I/II studies, bridging studies, or dose-ranging substudies
- Trials of DOACs for VTE, ACS, or post-operative thromboprophylaxis (see separate DOAC_CANCER_VTE and RIVAROXABAN_VASC reviews)

---

## 4. Information Sources and Search Strategy

| Database | Query | Type |
|---|---|---|
| ClinicalTrials.gov | `(dabigatran OR rivaroxaban OR apixaban OR edoxaban) AND atrial fibrillation` | Registry (API v2) |
| Europe PMC / PubMed | `(DOAC OR NOAC) AND atrial fibrillation AND randomized` | Bibliographic |
| OpenAlex | DOAC + atrial fibrillation concepts | Bibliographic |

**Search date:** Continuous (living review); formal snapshot at each new trial publication.

**Search updates:** The app re-queries CT.gov on user-triggered refresh; new trials matching the eligibility criteria are proposed as pending-include and require reviewer confirmation.

---

## 5. Study Selection

- **Stage 1 (auto-screen):** Keyword + publication-type classifier (0-100 score). Auto-exclude score <25.
- **Stage 2 (title/abstract):** Two-reviewer adjudication. Reviewer 1 proposes include/exclude with rationale. Reviewer 2 confirms. HMAC-signed seal per reviewer, timestamped.
- **Stage 3 (full text):** Verify eligibility; extract 2x2 event counts or HR/CI from the primary analysis.
- **Conflict resolution:** Re-review with exclusion reason in audit log. PRISMA 2020 flow auto-generated from search and screening counts.

---

## 6. Data Extraction

| Data item | Details |
|---|---|
| Study identifiers | NCT ID, PMID, DOI, first author, year |
| Participants | N randomized per arm, age, sex distribution, CHADS2/CHA2DS2-VASc, prior stroke |
| Intervention details | Specific DOAC, dose, regimen |
| Comparator | Warfarin target INR, TTR if reported |
| Outcome events | Stroke/SE counts per arm; major bleeding (ISTH); intracranial haemorrhage; all-cause mortality |
| Risk of bias | Cochrane RoB 2 per trial |
| Source evidence | Verbatim extracts from published manuscripts with page/table refs |

---

## 7. Risk of Bias Assessment

Cochrane **RoB 2** for randomized trials. Per-trial assessment across 5 signalling domains (Low / Some concerns / High). Traffic-light plot per trial + stacked bar across domains.

> **Status flag:** Ratings in the current app are design-based prior judgments (open-label PROBE designs get `Some concerns` on D2) pending formal completion by a trained assessor. A visible banner will indicate this status in the Extraction tab.

---

## 8. Synthesis / Statistical Methods

- **Primary pool:** DerSimonian-Laird random-effects inverse-variance weighting on the log-hazard scale.
- **CI adjustment:** Hartung-Knapp-Sidik-Jonkman (HKSJ) with t-distribution df = k-1; floor variance inflation at max(1, Q/(k-1)).
- **Prediction interval:** t-distribution with df = k-2 (Higgins 2009). Undefined for k < 3.
- **Heterogeneity:** Cochran Q (p-value), I^2 with Q-profile CI (Viechtbauer 2007), tau^2 (DL estimator).
- **Publication bias:** Contour-enhanced funnel plot; Peters' test for binary outcomes (k low but run as sensitivity).
- **Sensitivity:** Leave-one-out; DOAC class-level pool vs agent-level pool.
- **Bayesian:** Grid-approximation random-effects with half-normal prior on tau; posterior with credible interval.
- **Cross-validation:** R (`metafor::rma`) and Python (`scipy`) reference scripts exportable from the Analysis Suite.

---

## 9. Certainty of Evidence (GRADE)

GRADE per outcome with downgrading domains:
- Risk of bias (>=50% of weight from trials rated Some concerns / High)
- Inconsistency (I^2 >=50% or PI crosses the null)
- Indirectness (PICO mismatch)
- Imprecision (CI crosses a minimally important difference)
- Publication bias (Egger/Peters p <0.10, asymmetric funnel)

Summary of Findings (SoF) table auto-generated from the GRADE profile.

---

## 10. Reporting and Dissemination

- **Reporting guideline:** PRISMA 2020 (27-item checklist exportable)
- **Export formats:** JSON state bundle, R validation script, Python validation script, PRISMA checklist CSV, HTML standalone report
- **Data integrity:** SHA-256 seal on every report; version timeline with delta alerts
- **Published benchmark:** HR 0.81 (0.73-0.91) for stroke or systemic embolism (Ruff CT et al. Lancet 2014;383:955-62, IPD meta-analysis of 4 pivotal DOAC-AF trials: RE-LY, ROCKET-AF, ARISTOTLE, ENGAGE AF-TIMI 48).

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
