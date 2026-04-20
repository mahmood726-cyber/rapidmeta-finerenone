---
title: "Long-Acting Cabotegravir Injection for HIV Pre-Exposure Prophylaxis"
slug: cab_prep_hiv
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Infectious Disease (HIV)
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/cab_prep_hiv_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/CAB_PREP_HIV_REVIEW.html
license: MIT
---

# Long-Acting Cabotegravir Injection for HIV Pre-Exposure Prophylaxis
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Infectious Disease (HIV)

---

## 1. Review Title and Registration

**Title:** Long-Acting Cabotegravir Injection vs Daily Oral TDF/FTC for HIV Pre-Exposure Prophylaxis: A Living Systematic Review and Meta-Analysis of Pivotal Phase 2b/3 RCTs

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze** (immutable git history at the canonical URL above, with a SHA anchor once the review is submitted) rather than a PROSPERO record. PROSPERO does not currently accept retrospective or already-completed-analysis registrations; authors targeting journals that require a PROSPERO number should register the protocol at PROSPERO before the first formal update cycle.

**Authors:** Mahmood Ahmad (corresponding).

**Corresponding address:** drmahmoodclinic@pm.me (GMC 6071047), Royal Free Hospital and Barnet Hospital, London, UK.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults at high risk of HIV acquisition (MSM, transgender women, cisgender women) |
| **Intervention** | Cabotegravir long-acting 600 mg IM injection every 8 weeks (after oral lead-in) |
| **Comparator** | Daily oral tenofovir disoproxil fumarate + emtricitabine (TDF/FTC 200/300 mg) |
| **Outcome (primary)** | Incident HIV infection over follow-up period |

---

## 3. Eligibility Criteria

### Inclusion
- RCT (parallel, double-blind double-dummy)
- Phase IIb/III pivotal trials
- Adults at high HIV-acquisition risk
- Cabotegravir LA IM at licensed regimen
- TDF/FTC daily oral comparator
- HIV incidence as primary or co-primary

### Exclusion
- Monotherapy oral cabotegravir trials (phase 1/2)
- Maternal PrEP trials in pregnancy (separate review)
- Trials of other injectable ARVs (lenacapavir PURPOSE — considered for future expansion)
- Observational PrEP effectiveness studies

---

## 4. Information Sources and Search Strategy

| Database | Query |
|---|---|
| ClinicalTrials.gov | `cabotegravir AND PrEP AND HIV` |
| Europe PMC / PubMed | `(HPTN 083 OR HPTN 084 OR cabotegravir LA) AND prevention AND randomized` |

---

## 5. Study Selection

Two-reviewer adjudication with HMAC-signed seal; PRISMA 2020.

---

## 6. Data Extraction

Study IDs, N randomized per arm, incident HIV infections, person-years of follow-up, integrase-inhibitor resistance emergence, adherence metrics, RoB 2.

---

## 7. Risk of Bias Assessment

Cochrane **RoB 2**. Design-based priors: LOW across D1-D5 for both pivotal trials (double-blind double-dummy with matched IM injections + oral tablets, central HIV testing, DSMB-triggered unblinding on superiority). Author sign-off required per the provisional-RoB banner in the app's Extraction tab.

---

## 8. Synthesis / Statistical Methods

- **Primary pool:** DerSimonian-Laird random-effects IVW on log-HR scale.
- **CI adjustment:** HKSJ with t-distribution df = k-1.
- **HKSJ variance-inflation floor:** `max(1, Q/(k-1))` (non-optional, hard-coded).
- **Zero-cell handling:** 0.5 continuity correction applied only when >=1 cell is zero (conditional, not unconditional).
- **Prediction interval:** Suppressed for k < 3 (at v1.1 k=2, PI undefined). Enabled with t-df=k-2 (Higgins 2009) once k>=3.
- **Subgroup / meta-regression:** By population (MSM/transgender vs cisgender women), by region (sub-Saharan Africa vs mixed).
- **Publication bias:** Not informative for k<4; note PROSPERO-independent canonical-URL freeze + pre-specified interim boundaries minimize selective reporting risk.
- **Trim-and-fill sensitivity:** Duval-Tweedie reported as sensitivity with low-power caveat at k<10.
- **Sample-size heterogeneity:** HPTN 083 n=4,566 and HPTN 084 n=3,224 are comparable scale; weight imbalance minimal.
- **Bayesian:** Grid-approximation with half-normal(0, 0.5) prior on tau.
- **Browser-hosted WebR cross-validation (optional, user-triggered):** The Analysis tab exposes a "Validate pool with R" button that loads WebR and installs `metafor` on first click; runs `metafor::rma(method="DL", test="knha")` independently and reports EXACT/CLOSE/DIFFER vs the app's native pool.

---

## 9. Certainty of Evidence (GRADE)

Standard GRADE domains. Population heterogeneity (MSM/TGW vs cisgender women) may warrant within-subgroup interpretation rather than single pooled estimate.

---

## 10. Reporting and Dissemination

- **Reporting guideline:** PRISMA 2020
- **Published benchmark:** Landovitz 2023 update and WHO 2023 PrEP guidelines cite pooled HR approximately 0.2 across HPTN 083 + 084 for HIV acquisition.

---

## 11. Living-MA Update Cadence

- **Trigger:** New cabotegravir LA phase 3 or real-world efficacy publications (PURPOSE, PILLAR).
- **Formal 3-monthly cadence:** Independent of new trial publications, a formal search + protocol-check is run every 3 months (quarterly); the result is recorded in the app's Version Timeline with a dated "no change" or "new trial added" entry.
- **Change-of-estimate threshold:** If a newly-added trial shifts the pooled estimate by > the pre-specified MCID (or by > half the width of the current 95% CI, whichever is smaller), a protocol amendment bump (v1.1 -> v1.2) is issued and noted in the Changelog.

---

## 12-14

Aggregate-data only. No competing interests, no funding.

---

## Appendix A. AMSTAR-2 Critical-Domain Self-Assessment

| # | Domain | Self-rating | Evidence / location |
|---|---|---|---|
| 2 (critical) | Protocol registered before data extraction | Yes (partial) | GitHub-canonical-URL freeze; PROSPERO not attempted. |
| 4 (critical) | Comprehensive search strategy | Yes | §4. CT.gov API v2 + Europe PMC + OpenAlex. |
| 7 (critical) | List of excluded studies with reasons | Yes | App Screening tab "Excluded" filter. |
| 9 (critical) | RoB assessment | Partial | Provisional AI-drafted RoB-2 per record excerpts; formal dual-assessor sign-off required before submission. |
| 11 (critical) | Appropriate statistical methods | Yes | §8 DL random-effects with HKSJ t-distribution df=k-1 and variance-inflation floor. |
| 13 (critical) | RoB accounted for in interpretation | Partial | GRADE-profile §9 downgrades for RoB when >=50% weight from Some/High-risk trials. |
| 15 (critical) | Publication bias assessment | Yes (k-appropriate) | §8. Contour-enhanced funnel; trim-and-fill sensitivity at k<10. |
| 1 | PICO research question | Yes | §2. |

---

## Changelog

- **v1.1** (2026-04-20) — Initial editor-review-revision release: AMSTAR-2 appendix, HKSJ/zero-cell SAP bullets, 3-monthly cadence, PROSPERO reframing, provisional RoB/GRADE banner, WebR cross-validation UI. Pre-registered at canonical-URL freeze.
