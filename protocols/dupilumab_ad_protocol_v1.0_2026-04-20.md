---
title: "Dupilumab (IL-4Ralpha Monoclonal Antibody) for Moderate-to-Severe Atopic Dermatitis"
slug: dupilumab_ad
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Dermatology
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/dupilumab_ad_protocol_v1.0_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/DUPILUMAB_AD_REVIEW.html
license: MIT
---

# Dupilumab for Moderate-to-Severe Atopic Dermatitis
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Dermatology

---

## 1. Review Title and Registration

**Title:** Dupilumab (IL-4Ralpha Monoclonal Antibody) for Moderate-to-Severe Atopic Dermatitis: A Living Systematic Review and Meta-Analysis of Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze** (immutable git history at the canonical URL above, with a SHA anchor once the review is submitted) rather than a PROSPERO record. PROSPERO does not currently accept retrospective or already-completed-analysis registrations; authors targeting journals that require a PROSPERO number should register the protocol at PROSPERO before the first formal update cycle.
**Authors:** Mahmood Ahmad (corresponding).

**Corresponding address:** drmahmoodclinic@pm.me (GMC 6071047), Royal Free Hospital and Barnet Hospital, London, UK.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults (>=18) with moderate-to-severe atopic dermatitis (IGA >=3, EASI >=16, BSA >=10%) inadequately controlled with topical therapy |
| **Intervention** | Dupilumab 300 mg SC every 2 weeks (licensed regimen) |
| **Comparator** | Matched placebo (monotherapy or + TCS) |
| **Outcome (primary)** | Proportion achieving IGA 0/1 at week 16 (co-primary with EASI-75) |

---

## 3. Eligibility Criteria

### Inclusion
- RCT (parallel, double-blind)
- Phase III pivotal trials
- Adults meeting AD severity criteria
- Dupilumab 300 mg SC Q2W (with or without TCS)
- Placebo with or without TCS as comparator
- IGA 0/1 at 16 weeks reported as primary or co-primary

### Exclusion
- Paediatric AD trials (separate age-specific review)
- Phase II dose-ranging studies
- Trials of other IL-4/IL-13 agents (tralokinumab ECZTRA, lebrikizumab ADvocate)
- Asthma or chronic rhinosinusitis with nasal polyposis trials

---

## 4. Information Sources and Search Strategy

| Database | Query |
|---|---|
| ClinicalTrials.gov | `dupilumab AND atopic dermatitis` |
| Europe PMC / PubMed | `dupilumab AND atopic dermatitis AND randomized` |

**Search date:** Continuous (living review).

---

## 5. Study Selection

Two-reviewer adjudication with HMAC-signed seal; PRISMA 2020 flow.

---

## 6. Data Extraction

Study IDs, N randomized, baseline IGA/EASI/BSA, IGA 0/1 and EASI-75 event counts per arm, pruritus NRS change, safety (conjunctivitis, injection-site), RoB 2.

---

## 7. Risk of Bias Assessment

Cochrane **RoB 2**. Design-based priors: LOW across D1-D5 (double-blind, central blinded IGA scoring from standardized photographs).

---

## 8. Synthesis / Statistical Methods

- **Primary pool:** DerSimonian-Laird random-effects IVW on log-OR scale for IGA 0/1.
- **CI adjustment:** HKSJ with t-distribution df = k-1.
- **Prediction interval:** t df = k-2 (Higgins 2009).
- **Subgroup / meta-regression:** Monotherapy vs concomitant TCS, primary-assessment timepoint.
- **Sensitivity:** Leave-one-out; restrict to monotherapy pivotal trials (SOLO-1 + SOLO-2).
- **Bayesian:** Grid-approximation with half-normal prior on tau.

---


### SAP additions (2026-04-20 editor-review revision v1.1)

- **HKSJ variance-inflation floor:** Apply `max(1, Q/(k-1))` as the floor on the HKSJ inflation factor. This prevents HKSJ from *narrowing* the CI below the DL-random-effects CI when Q < k-1 (Roever 2015). Non-optional; hard-coded in the app's pooler.
- **Zero-cell continuity correction:** Apply 0.5 continuity correction **only** when >=1 cell is zero in a given trial. Do not apply unconditionally (unconditional correction biases OR -> 1 even when no cells are zero). Sensitivity: Mantel-Haenszel without correction and Peto-OR for sparse-cell subsets.
- **Trim-and-fill sensitivity:** Duval-Tweedie trim-and-fill reported as a sensitivity analysis in all apps, flagged as low-power at k < 10 (protocol notes Egger/Peters regression is the formal test at k >= 10).
- **Sample-size heterogeneity note:** Trial-level sample sizes differ by one to two orders of magnitude across some pools (e.g., RSV vaccines n=17,000 per arm vs Mavacamten n ~ 250 per arm). DL random-effects inverse-variance weights handle the imbalance correctly but GRADE indirectness should note the heterogeneous population scale when the pool mixes pivotal mega-trials with smaller confirmatory trials.
- **Prediction interval:** Suppressed for k < 3 (display reads "PI undefined"). Enabled with t-df = k-2 (Higgins 2009) once k >= 3.
- **Browser-hosted WebR cross-validation (optional, user-triggered):** The Analysis tab exposes a "Validate pool with R" button that loads WebR (WebAssembly R) and installs `metafor` on first click (~40 MB one-time download, cached thereafter). Running the validation re-computes the DL random-effects pool via `metafor::rma(method="DL", test="knha")` independently of the app's native pool and reports an EXACT / CLOSE / DIFFER flag against the displayed pool. No automated sharing of code between the R and JS poolers — independent implementations in two languages, two numerical libraries.


---

## 9. Certainty of Evidence (GRADE)

Standard GRADE domains.

---

## 10. Reporting and Dissemination

- **Reporting guideline:** PRISMA 2020
- **Published benchmark:** Sawangjit R et al. JAAD 2020 network MA reported dupilumab 300 mg Q2W IGA 0/1 OR approximately 5-6 vs placebo across SOLO-1, SOLO-2, CHRONOS.

---

## 11. Living-MA Update Cadence

Trigger: new dupilumab phase 3 publications (long-term open-label extensions, head-to-head).

---

## 12-14

Aggregate-data only. No competing interests, no funding.

---

- **Formal 3-monthly cadence:** Independent of new trial publications, a formal search + protocol-check is run every 3 months (quarterly); the result is recorded in the app's Version Timeline with a dated "no change" or "new trial added" entry.
- **Change-of-estimate threshold:** If a newly-added trial shifts the pooled estimate by > the pre-specified MCID (or by > half the width of the current 95% CI, whichever is smaller), a protocol amendment bump (v1.1 -> v1.2) is issued and noted in the Changelog.

## Appendix A. AMSTAR-2 Critical-Domain Self-Assessment

AMSTAR-2 has 16 items; the **8 critical domains** most load-bearing for the journal editor's confidence judgment are 2, 4, 7, 9, 11, 13, 15 (Shea 2017 BMJ). Our self-assessment below should be re-scored by the second reviewer before journal submission.

| # | Domain | Self-rating | Evidence / location |
|---|---|---|---|
| 2 (critical) | Protocol registered before data extraction | Yes (partial) | GitHub-canonical-URL freeze at the `canonical_url` above; PROSPERO registration not attempted (see §1). Authors targeting PROSPERO-required journals should register before the first formal update cycle. |
| 4 (critical) | Comprehensive search strategy | Yes | §4. CT.gov API v2 + Europe PMC + OpenAlex with CT.gov live re-query triggered from the Search tab. Search cadence documented in §11. |
| 7 (critical) | List of excluded studies with reasons | Yes | App Screening tab "Excluded" filter lists each excluded trial with the Protocol-§3 exclusion reason in the audit log. |
| 9 (critical) | RoB assessment | Yes | Authors have double-checked screening and data extraction against the record excerpts shown in the Extraction tab; the provisional AI-drafted RoB-2 ratings have been author-confirmed. Formal dual-assessor RoB-2 with inter-rater kappa remains a per-submission artefact (see Extraction-tab banner). |
| 11 (critical) | Appropriate statistical methods for combining results | Yes | §8. DL random-effects with HKSJ t-distribution df=k-1 and variance-inflation floor `max(1, Q/(k-1))`. Fixed-effect primary substituted at k=2 per CART-MM protocol pattern. |
| 13 (critical) | Account for RoB when interpreting / discussing results | Partial | GRADE-profile §9 downgrades for RoB when >=50% of weight comes from trials rated Some concerns / High. Interpretation reflects this in the app's Scientific Output tab. |
| 15 (critical) | Publication bias assessment | Yes (k-appropriate) | §8. Contour-enhanced funnel plot (all k); Egger/Peters regression for k>=10; Duval-Tweedie trim-and-fill as sensitivity at k<10 noting low power. |
| 1 | PICO research question | Yes | §2 PICO table. |

**Non-critical domains (brief):** Item 3 (Design-for-inclusion rationale) Yes; Item 5 (Duplicate study selection) Yes via two-reviewer HMAC-signed seal; Item 6 (Duplicate data extraction) Yes same mechanism; Item 8 (Adequate description of included studies) Yes (Extraction tab); Item 10 (Funding sources of included studies) Partial (tracked for demonstrators only); Item 12 (Heterogeneity discussion) Yes §8; Item 14 (Satisfactory explanation of heterogeneity) Yes §8 subgroup/meta-regression; Item 16 (Funding/conflicts of this review) Yes §14.

**Author sign-off gate:** Second reviewer to initial each critical-domain rating against the protocol text before PDF generation for journal submission.


---

## Changelog

- **v1.1** (2026-04-20) -- Editor-review revision: AMSTAR-2 critical-domain appendix populated, PROSPERO reframing, HKSJ-floor + zero-cell rules promoted to SAP bullets, 3-monthly formal cadence, trim-and-fill sensitivity, timepoint harmonisation rule where applicable. Pre-registered at canonical-URL freeze.
- **v1.0** (2026-04-20) — Initial protocol registration.
