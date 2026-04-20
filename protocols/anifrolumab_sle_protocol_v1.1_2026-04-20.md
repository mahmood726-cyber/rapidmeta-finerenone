---
title: "Anifrolumab (Type I IFN Receptor Monoclonal Antibody) in Moderate-to-Severe SLE"
slug: anifrolumab_sle
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Rheumatology (SLE)
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/anifrolumab_sle_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/ANIFROLUMAB_SLE_REVIEW.html
license: MIT
---

# Anifrolumab in Moderate-to-Severe SLE
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Rheumatology (SLE)

---

## 1. Review Title and Registration

**Title:** Anifrolumab (Type I Interferon Receptor Monoclonal Antibody) in Moderate-to-Severe Systemic Lupus Erythematosus: A Living Systematic Review and Meta-Analysis of the TULIP Phase 3 Programme

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding).

**Corresponding address:** drmahmoodclinic@pm.me (GMC 6071047), Royal Free Hospital and Barnet Hospital, London, UK.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with moderate-to-severe active SLE (SLEDAI-2K >=6, at least one BILAG A or two BILAG B domains) on stable background standard therapy |
| **Intervention** | Anifrolumab 300 mg IV every 4 weeks |
| **Comparator** | Matched placebo IV infusion |
| **Outcome (primary)** | BICLA response at week 52 |

---

## 3. Eligibility Criteria

### Inclusion
- RCT (parallel, double-blind)
- Phase III pivotal trials
- Moderate-severe active SLE on stable background therapy
- Anifrolumab 300 mg IV Q4W at licensed regimen
- Matched placebo comparator
- BICLA at wk 52 reported as primary or key secondary

### Exclusion
- Severe active lupus nephritis requiring induction immunosuppression (separate BLISS-LN-style review)
- Severe neuropsychiatric SLE
- Paediatric SLE
- Phase II dose-finding

---

## 4. Information Sources and Search Strategy

| Database | Query |
|---|---|
| ClinicalTrials.gov | `anifrolumab AND SLE` |
| Europe PMC / PubMed | `(TULIP-1 OR TULIP-2 OR anifrolumab) AND lupus AND randomized` |

---

## 5. Study Selection

Two-reviewer adjudication with HMAC-signed seal; PRISMA 2020.

---

## 6. Data Extraction

Study IDs, N per arm, BICLA response counts, SRI-4 response, CLASI-50, glucocorticoid-sparing, flare rates, type-I IFN signature status, RoB 2.

---

## 7. Risk of Bias Assessment

Cochrane **RoB 2**. Design-based priors:
- **TULIP-1**: D4 SOME CONCERNS — pre-specified primary was SRI-4 (not met); BICLA became the programme-level primary after TULIP-1 read-out, a form of outcome-switching that was transparently reported but deserves an RoB D4 note.
- **TULIP-2**: LOW across D1-D5 with BICLA as the programme-pre-specified primary.

Author sign-off required per the provisional-RoB banner.

---

## 8. Synthesis / Statistical Methods

- **Primary pool:** DerSimonian-Laird random-effects IVW on log-OR scale for BICLA.
- **CI adjustment:** HKSJ with t-distribution df=k-1; floor `max(1, Q/(k-1))`.
- **Prediction interval:** Undefined at k=2 (suppressed).
- **Subgroup / meta-regression:** By type-I IFN signature (high vs low), baseline SLEDAI-2K.
- **Zero-cell handling:** Conditional 0.5 continuity correction.
- **Trim-and-fill sensitivity:** Duval-Tweedie low-power caveat at k=2.
- **Bayesian:** Grid-approximation with half-normal(0, 0.5) prior on tau.
- **Browser-hosted WebR cross-validation (optional, user-triggered).**

---

## 9. Certainty of Evidence (GRADE)

Standard GRADE domains. **Downgrade for risk of bias** warranted by TULIP-1 SRI-4 / BICLA outcome-switching narrative.

---

## 10. Reporting and Dissemination

- **Reporting guideline:** PRISMA 2020
- **Published benchmark:** FDA clinical review cites pooled BICLA OR ~1.8 across TULIP-1 + TULIP-2; Bruce IN et al. 2022 post-hoc pooled analysis reports consistent effect direction.

---

## 11. Living-MA Update Cadence

- **Trigger:** New SLE biologic phase 3 (belimumab, obinutuzumab NOBILITY, deucravacitinib SLE) or anifrolumab extensions.
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
| 9 (critical) | RoB assessment | Partial | Provisional; TULIP-1 D4 SOME pre-specified. |
| 11 (critical) | Appropriate statistical methods | Yes | §8. |
| 13 (critical) | RoB accounted for in interpretation | Partial | GRADE §9. |
| 15 (critical) | Publication bias assessment | Yes (k-appropriate) | §8, k=2 so formal tests suppressed. |
| 1 | PICO research question | Yes | §2. |

---

## Changelog

- **v1.1** (2026-04-20) — Initial editor-review-revision release.
