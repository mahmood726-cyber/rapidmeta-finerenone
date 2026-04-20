---
title: "Insulin Icodec (Once-Weekly Basal Insulin) in Type 2 Diabetes"
slug: insulin_icodec
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Endocrinology (Diabetes)
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/insulin_icodec_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/INSULIN_ICODEC_REVIEW.html
license: MIT
---

# Insulin Icodec Once-Weekly Basal Insulin in Type 2 Diabetes
## A Living Systematic Review and Meta-Analysis Protocol (ONWARDS Phase 3 Programme)

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Endocrinology (Diabetes)

---

## 1. Review Title and Registration

**Title:** Insulin Icodec (Once-Weekly Basal Insulin) vs Once-Daily Basal-Insulin Analogues in Type 2 Diabetes: A Living Systematic Review and Meta-Analysis of the ONWARDS Phase 3 Programme

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding).

**Corresponding address:** drmahmoodclinic@pm.me (GMC 6071047), Royal Free Hospital and Barnet Hospital, London, UK.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with type 2 diabetes (insulin-naive or previously on once-daily basal insulin) |
| **Intervention** | Insulin icodec (once-weekly SC injection, licensed titration) |
| **Comparator** | Once-daily basal insulin analogue (insulin glargine U100, insulin degludec U100) |
| **Outcome (primary)** | HbA1c change from baseline at the trial-specific primary timepoint (week 26 or 52) |

---

## 3. Eligibility Criteria

### Inclusion
- RCT (parallel, open-label or double-blind double-dummy)
- Phase III pivotal trials
- Adults with T2D, insulin-naive or previously-treated basal insulin
- Icodec once-weekly at licensed regimen
- Comparator = once-daily basal insulin analogue
- HbA1c change as primary endpoint

### Exclusion
- Type 1 diabetes trials (separate future review — ONWARDS-6)
- Phase II dose-finding
- Prandial-insulin-intensification comparisons (ONWARDS-5 primary-care dosing guide is reserved for a sensitivity analysis)

---

## 4. Information Sources and Search Strategy

| Database | Query |
|---|---|
| ClinicalTrials.gov | `insulin icodec AND type 2 diabetes` |
| Europe PMC / PubMed | `(ONWARDS-1 OR ONWARDS-2 OR ONWARDS-3 OR insulin icodec) AND T2D AND randomized` |

---

## 5. Study Selection

Two-reviewer adjudication with HMAC-signed seal; PRISMA 2020.

---

## 6. Data Extraction

Study IDs, N per arm, HbA1c change MD + SE, TIR (time-in-range), body-weight change, clinically-significant + severe hypoglycaemia rates, RoB 2.

---

## 7. Risk of Bias Assessment

Cochrane **RoB 2**. Design-based priors: ONWARDS-1 and ONWARDS-2 **D2 SOME CONCERNS** (open-label by necessity — weekly vs daily injection frequency cannot be blinded with a matched-schedule placebo). ONWARDS-3 **LOW across D1-D5** (double-blind double-dummy). Author sign-off required per the provisional-RoB banner.

---

## 8. Synthesis / Statistical Methods

- **Primary pool:** DerSimonian-Laird random-effects IVW on MD scale (HbA1c %).
- **CI adjustment:** HKSJ with t-distribution df=k-1; floor `max(1, Q/(k-1))`.
- **Prediction interval:** t-df=k-2 (Higgins 2009), enabled at k=3.
- **Subgroup / meta-regression:** By baseline insulin-naive vs switch status, by comparator (glargine vs degludec).
- **Heterogeneity caveat:** Effect sizes are similar (ETD approximately -0.20 across all three trials); pool expected to be consistent but subgroup-confirmed.
- **Zero-cell handling:** Conditional 0.5 correction (not applicable for MD endpoint).
- **Sensitivity:** Open-label-only sensitivity (ONWARDS-1 + -2) vs blinded-only (ONWARDS-3) to quantify blinding impact.
- **Trim-and-fill:** Duval-Tweedie low-power caveat at k<10.
- **Bayesian:** Grid-approximation with half-normal(0, 0.5) prior on tau.
- **Browser-hosted WebR cross-validation (optional, user-triggered).**

---

## 9. Certainty of Evidence (GRADE)

Standard GRADE domains. MCID for HbA1c MD typically 0.3-0.5%; pooled ETD ~-0.2 is below MCID for superiority claim but non-inferiority is robust.

---

## 10. Reporting and Dissemination

- **Reporting guideline:** PRISMA 2020
- **Published benchmark:** Kumar A et al. 2024 narrative pooled analysis of ONWARDS programme reports pooled ETD ~-0.2% across T2D ONWARDS trials.

---

## 11. Living-MA Update Cadence

- **Trigger:** New icodec phase 3 data (ONWARDS-4, -5, -6 pooled analyses; T1DM expansion), other once-weekly basal insulins (insulin efsitora).
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
| 13 (critical) | RoB accounted for in interpretation | Partial | GRADE §9 + open-label sensitivity. |
| 15 (critical) | Publication bias assessment | Yes (k-appropriate) | §8, k=3 so formal tests suppressed. |
| 1 | PICO research question | Yes | §2. |

---

## Changelog

- **v1.1** (2026-04-20) — Initial editor-review-revision release.
