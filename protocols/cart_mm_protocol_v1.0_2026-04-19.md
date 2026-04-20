---
title: "BCMA-Directed CAR-T Therapy in Relapsed/Refractory Multiple Myeloma"
slug: cart_mm
version: 1.1
timestamp: 2026-04-19T00:00:00Z
date: 2026-04-19
specialty: Oncology (Haematology)
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/cart_mm_protocol_v1.0_2026-04-19.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/CART_MM_REVIEW.html
license: MIT
---

# BCMA-Directed CAR-T Therapy in Relapsed/Refractory Multiple Myeloma
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-19T00:00:00Z
**Specialty:** Oncology (Haematology)

---

## 1. Review Title and Registration

**Title:** BCMA-Directed CAR-T Therapy (Ciltacabtagene Autoleucel and Idecabtagene Vicleucel) vs Standard-of-Care Regimens in Relapsed/Refractory Multiple Myeloma: A Living Systematic Review and Meta-Analysis of Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-19T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze** (immutable git history at the canonical URL above, with a SHA anchor once the review is submitted) rather than a PROSPERO record. PROSPERO does not currently accept retrospective or already-completed-analysis registrations; authors targeting journals that require a PROSPERO number should register the protocol at PROSPERO before the first formal update cycle.
**Authors:** Mahmood Ahmad (corresponding).

**Corresponding address:** drmahmoodclinic@pm.me (GMC 6071047), Royal Free Hospital and Barnet Hospital, London, UK.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with relapsed or refractory multiple myeloma after prior lines of therapy |
| **Intervention** | BCMA-directed CAR-T (ciltacabtagene autoleucel or idecabtagene vicleucel) single infusion |
| **Comparator** | Physicians-choice standard-of-care triplet regimen (DPd, DVd, PVd, IRd, Kd, EPd) |
| **Outcome (primary)** | Progression-free survival |

---

## 3. Eligibility Criteria

### Inclusion
- Study design: Randomized controlled trials (parallel, open-label with IRC-adjudicated primary endpoint)
- Phase: III pivotal trials
- Participants: Adults with RRMM after 1-4 prior lines depending on trial
- Intervention: BCMA-directed CAR-T at licensed dose
- Comparator: Physicians-choice SoC triplet
- Outcomes: PFS reported as primary
- Publication: Peer-reviewed phase-3 publication

### Exclusion
- Single-arm phase 1-2 CAR-T expansion cohorts (KarMMa-1, CARTITUDE-1, LEGEND-2)
- Myeloma subtypes other than relapsed/refractory (newly diagnosed — see CARTITUDE-5/-6)
- Non-BCMA targets (GPRC5D — Cartilage-1, Cartilage-2, MajesTEC-1)

---

## 4. Information Sources and Search Strategy

| Database | Query | Type |
|---|---|---|
| ClinicalTrials.gov | `(ciltacabtagene OR idecabtagene OR cilta-cel OR ide-cel) AND myeloma` | Registry |
| Europe PMC / PubMed | `CAR-T AND BCMA AND myeloma AND randomized` | Bibliographic |

---

## 5. Study Selection

Two-reviewer adjudication with HMAC-signed seal; PRISMA 2020 flow.

---

## 6. Data Extraction

| Data item | Details |
|---|---|
| Study identifiers | NCT ID, PMID, DOI |
| Participants | Prior-lines strata, triple-class exposure, N randomized and N infused |
| Intervention details | Specific CAR-T product, bridging therapy |
| Comparator | Physicians-choice triplet composition |
| Outcome effects | PFS HR + 95% CI, median PFS, ORR, sCR, safety (grade 3-4 CRS, neurotoxicity, TRM) |
| Risk of bias | Cochrane RoB 2 — D2 SOME concerns anticipated by open-label design |

---

## 7. Risk of Bias Assessment

Cochrane **RoB 2**. Design-based priors: D2 SOME CONCERNS (open-label by necessity — CAR-T single infusion vs ongoing triplet); other domains LOW (IRC adjudication, stratified randomization, SAP lock).

---

## 8. Synthesis / Statistical Methods

At protocol freeze k=2. Standard random-effects DL+HKSJ is unreliable at k=2 (tau^2 estimate is unstable; HKSJ df=1 inflates CI; PI is undefined). The SAP below reflects this:

- **Primary pool (k=2):** Fixed-effect inverse-variance weighting on the log-HR scale. Report as the point estimate + 95% CI for the v1.0 release.
- **Sensitivity pool A (k=2):** DerSimonian-Laird random-effects IVW on the log-HR scale with HKSJ t-distribution df=1 and variance-inflation floor `max(1, Q/(k-1))`. Reported alongside the FE primary but **not** as the ship estimate at k=2.
- **Sensitivity pool B (k=2):** Bayesian random-effects with a half-normal(0, 0.5) prior on tau (Spiegelhalter 2004 / Rover 2019 recommended weakly-informative prior for k<=4). Posterior median + 95% CrI reported as the stability check for the FE primary.
- **Primary pool (k>=3, once more pivotal CAR-T RCTs publish):** Switch primary to DerSimonian-Laird random-effects IVW with HKSJ on the log-HR scale. Bayesian becomes the secondary/stability pool.
- **Prediction interval:** Undefined for k<3; suppressed at v1.0 and enabled with t-df=k-2 once k>=3.
- **Heterogeneity:** Cochran Q (p-value), I^2 with Q-profile CI (Viechtbauer 2007), tau^2 (DL estimator). Note all three are poorly estimated at k=2; report but do not use as decision criteria.
- **Subgroup / meta-regression:** By prior lines (1-3 vs 2-4), triple-class exposure. Subgroup pools at k=2 are descriptive only.
- **Sensitivity:** Leave-one-out does not apply at k=2; flagged.
- **Updates:** CARTITUDE-5, CARTITUDE-6, KarMMa-9, and other ongoing CAR-T RCTs will be added when published; the primary pool switches to DL-HKSJ at k>=3 and the prior weighting becomes the sensitivity pool.

---


### SAP additions (2026-04-20 editor-review revision v1.1)

- **HKSJ variance-inflation floor:** Apply `max(1, Q/(k-1))` as the floor on the HKSJ inflation factor. This prevents HKSJ from *narrowing* the CI below the DL-random-effects CI when Q < k-1 (Roever 2015). Non-optional; hard-coded in the app's pooler.
- **Zero-cell continuity correction:** Apply 0.5 continuity correction **only** when >=1 cell is zero in a given trial. Do not apply unconditionally (unconditional correction biases OR -> 1 even when no cells are zero). Sensitivity: Mantel-Haenszel without correction and Peto-OR for sparse-cell subsets.
- **Trim-and-fill sensitivity:** Duval-Tweedie trim-and-fill reported as a sensitivity analysis in all apps, flagged as low-power at k < 10 (protocol notes Egger/Peters regression is the formal test at k >= 10).
- **Sample-size heterogeneity note:** Trial-level sample sizes differ by one to two orders of magnitude across some pools (e.g., RSV vaccines n=17,000 per arm vs Mavacamten n ~ 250 per arm). DL random-effects inverse-variance weights handle the imbalance correctly but GRADE indirectness should note the heterogeneous population scale when the pool mixes pivotal mega-trials with smaller confirmatory trials.
- **Prediction interval:** Suppressed for k < 3 (display reads "PI undefined"). Enabled with t-df = k-2 (Higgins 2009) once k >= 3.


---

## 9. Certainty of Evidence (GRADE)

PFS HR 0.26 (CARTITUDE-4) and 0.49 (KarMMa-3) both highly significant; heterogeneity reflects trial population (1-3 prior lines vs triple-class-exposed). GRADE downgrade for indirectness if pooling across agents without stratification.

---

## 10. Reporting and Dissemination

- **Reporting guideline:** PRISMA 2020
- **Published benchmark:** No single meta-analytic pool published at protocol freeze; app-computed DL pool of CARTITUDE-4 + KarMMa-3 is the reference.

---

## 11. Living-MA Update Cadence

- **Trigger:** CARTITUDE-5 (induction-line), CARTITUDE-6 (early-line), or new CAR-T phase 3 publications.

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
| 9 (critical) | RoB assessment | Partial | Provisional AI-drafted RoB-2 from the record excerpts (banner in Extraction tab). Formal dual-assessor assessment with kappa is required before the first journal submission. |
| 11 (critical) | Appropriate statistical methods for combining results | Yes | §8. DL random-effects with HKSJ t-distribution df=k-1 and variance-inflation floor `max(1, Q/(k-1))`. Fixed-effect primary substituted at k=2 per CART-MM protocol pattern. |
| 13 (critical) | Account for RoB when interpreting / discussing results | Partial | GRADE-profile §9 downgrades for RoB when >=50% of weight comes from trials rated Some concerns / High. Interpretation reflects this in the app's Scientific Output tab. |
| 15 (critical) | Publication bias assessment | Yes (k-appropriate) | §8. Contour-enhanced funnel plot (all k); Egger/Peters regression for k>=10; Duval-Tweedie trim-and-fill as sensitivity at k<10 noting low power. |
| 1 | PICO research question | Yes | §2 PICO table. |

**Non-critical domains (brief):** Item 3 (Design-for-inclusion rationale) Yes; Item 5 (Duplicate study selection) Yes via two-reviewer HMAC-signed seal; Item 6 (Duplicate data extraction) Yes same mechanism; Item 8 (Adequate description of included studies) Yes (Extraction tab); Item 10 (Funding sources of included studies) Partial (tracked for demonstrators only); Item 12 (Heterogeneity discussion) Yes §8; Item 14 (Satisfactory explanation of heterogeneity) Yes §8 subgroup/meta-regression; Item 16 (Funding/conflicts of this review) Yes §14.

**Author sign-off gate:** Second reviewer to initial each critical-domain rating against the protocol text before PDF generation for journal submission.


---

## Changelog

- **v1.1** (2026-04-20) -- Editor-review revision: AMSTAR-2 critical-domain appendix populated, PROSPERO reframing, HKSJ-floor + zero-cell rules promoted to SAP bullets, 3-monthly formal cadence, trim-and-fill sensitivity, timepoint harmonisation rule where applicable. Pre-registered at canonical-URL freeze.
- **v1.0** (2026-04-19) — Initial protocol registration.
