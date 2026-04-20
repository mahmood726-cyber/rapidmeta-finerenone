---
title: "Venetoclax plus Hypomethylator or LDAC for Untreated AML"
slug: ven_aml_untreated
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Haematology (Leukaemia)
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/venetoclax_aml_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/VENETOCLAX_AML_REVIEW.html
license: MIT
---

# Venetoclax + Hypomethylator or LDAC for Untreated AML
## A Living Systematic Review and Meta-Analysis Protocol (VIALE Phase 3 Programme)

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Haematology (Leukaemia)

---

## 1. Review Title and Registration

**Title:** Venetoclax in Combination with Hypomethylating Agents or Low-Dose Cytarabine for Newly-Diagnosed AML Ineligible for Intensive Chemotherapy: A Living Systematic Review and Meta-Analysis of the VIALE Phase 3 Programme

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding).

**Corresponding address:** drmahmoodclinic@pm.me (GMC 6071047), Royal Free Hospital and Barnet Hospital, London, UK.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with newly-diagnosed AML, ineligible for intensive induction (age >=75 or comorbidities) |
| **Intervention** | Venetoclax (400 mg PO daily ramp + azacitidine, or 600 mg + LDAC) at licensed regimen |
| **Comparator** | Azacitidine + placebo, or LDAC + placebo |
| **Outcome (primary)** | Overall survival |

---

## 3. Eligibility Criteria

### Inclusion
- RCT (parallel, double-blind)
- Phase III pivotal trials
- Untreated AML, unfit for intensive chemo
- Venetoclax + HMA or LDAC at licensed regimen
- Placebo-controlled comparator on the same backbone
- OS as primary endpoint

### Exclusion
- Intensive-induction-eligible populations (separate review)
- Single-arm venetoclax expansion cohorts
- Frontline venetoclax in MDS-AML high-risk overlap without phase 3 OS primary
- Salvage or R/R AML trials (separate future review)

---

## 4. Information Sources and Search Strategy

| Database | Query |
|---|---|
| ClinicalTrials.gov | `venetoclax AND (newly diagnosed AML OR untreated AML) AND randomized` |
| Europe PMC / PubMed | `(VIALE-A OR VIALE-C) AND venetoclax AND randomized` |

---

## 5. Study Selection

Two-reviewer adjudication with HMAC-signed seal; PRISMA 2020.

---

## 6. Data Extraction

Study IDs, N randomized per arm, OS events, median OS, CR + CRi rates, MRD-negativity, safety (tumour lysis, neutropaenia, early mortality), RoB 2.

---

## 7. Risk of Bias Assessment

Cochrane **RoB 2**. Design-based priors: D5 SOME CONCERNS for VIALE-C (the pre-specified primary OS analysis did not reach significance; the 6-month updated analysis was pre-specified as a supportive secondary, which some reviewers may consider as outcome-data reporting). VIALE-A rated LOW across all five domains. Author sign-off required per the provisional-RoB banner.

---

## 8. Synthesis / Statistical Methods

- **Primary pool:** DerSimonian-Laird random-effects IVW on log-HR scale.
- **CI adjustment:** HKSJ with t-distribution df=k-1; floor `max(1, Q/(k-1))`.
- **Prediction interval:** Undefined at k=2 (suppressed).
- **Subgroup / meta-regression:** By backbone (HMA vs LDAC), IDH1/2 mutation status, secondary AML vs de novo.
- **Heterogeneity:** Q, I^2, tau^2 (poorly estimated at k=2 — descriptive only).
- **Zero-cell handling:** Conditional 0.5 correction.
- **Publication bias:** Not informative for k=2.
- **Trim-and-fill sensitivity:** Low-power caveat at k<10.
- **Bayesian:** Grid-approximation with half-normal(0, 0.5) prior on tau.
- **Browser-hosted WebR cross-validation (optional, user-triggered):** Analysis tab button loads WebR + `metafor` on first click; runs `rma(method="DL", test="knha")` independently.

---

## 9. Certainty of Evidence (GRADE)

Standard GRADE domains. Note: VIALE-C updated-analysis estimand (primary did not meet significance) may warrant an additional risk-of-bias downgrade for reporting estimand.

---

## 10. Reporting and Dissemination

- **Reporting guideline:** PRISMA 2020
- **Published benchmark:** No single external IPD meta-analysis combining VIALE-A + VIALE-C at protocol freeze. Internal DL pool + methodological footnote per the benchmark JSON.

---

## 11. Living-MA Update Cadence

- **Trigger:** New venetoclax-AML phase 3 data (intensive-induction overlap trials, MDS-AML trials, relapsed/refractory phase 3).
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
| 9 (critical) | RoB assessment | Partial | Provisional AI-drafted; VIALE-C D5 SOME pre-specified. |
| 11 (critical) | Appropriate statistical methods | Yes | §8. |
| 13 (critical) | RoB accounted for in interpretation | Partial | GRADE §9 acknowledges VIALE-C estimand distinction. |
| 15 (critical) | Publication bias assessment | Yes (k-appropriate) | §8, k=2 so formal tests suppressed. |
| 1 | PICO research question | Yes | §2. |

---

## Changelog

- **v1.1** (2026-04-20) — Initial editor-review-revision release.
