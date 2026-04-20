---
title: "CAR-T Cell Therapy as Second-Line Treatment for R/R Aggressive B-Cell Lymphoma"
slug: cart_dlbcl_2l
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Haematology (Lymphoma)
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/cart_dlbcl_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/CART_DLBCL_REVIEW.html
license: MIT
---

# Second-Line CAR-T vs SoC in Relapsed/Refractory Aggressive B-Cell Lymphoma
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Haematology (Lymphoma)

---

## 1. Review Title and Registration

**Title:** Second-Line CD19-Directed CAR-T Cell Therapy vs Standard-of-Care Chemoimmunotherapy plus Autologous Stem-Cell Transplant in Relapsed or Refractory Aggressive B-Cell Lymphoma: A Living Systematic Review and Meta-Analysis of Pivotal Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding).

**Corresponding address:** drmahmoodclinic@pm.me (GMC 6071047), Royal Free Hospital and Barnet Hospital, London, UK.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with aggressive B-cell lymphoma (DLBCL, HGBL, PMBCL) refractory to first-line chemoimmunotherapy or relapsed within 12 months |
| **Intervention** | CD19-directed CAR-T cell therapy: axicabtagene ciloleucel, lisocabtagene maraleucel, or tisagenlecleucel |
| **Comparator** | Salvage chemoimmunotherapy (2-3 cycles) + BEAM or BEAM-R conditioning + autologous stem-cell transplant for responders |
| **Outcome (primary)** | Event-free survival (trial-specific composite of disease progression, death, new anti-lymphoma therapy, or stable disease at designated assessment) |

---

## 3. Eligibility Criteria

### Inclusion
- RCT (parallel, open-label with IRC-adjudicated primary)
- Phase III pivotal trials
- R/R aggressive B-cell lymphoma (refractory to 1L or relapsed <=12 months)
- CD19-directed CAR-T at licensed dose
- SoC comparator = salvage + ASCT intent
- EFS as primary endpoint

### Exclusion
- Third-line or later CAR-T trials (separate review)
- Follicular lymphoma CAR-T trials (ZUMA-5 — separate)
- Mantle-cell lymphoma CAR-T trials (ZUMA-2, TRANSCEND-NHL-001 — separate)
- CD19-BiTE / bispecific antibody trials (mosunetuzumab, glofitamab, epcoritamab)
- CD22- or CD20-directed CAR-T (not licensed at freeze)

---

## 4. Information Sources and Search Strategy

| Database | Query |
|---|---|
| ClinicalTrials.gov | `(axicabtagene OR lisocabtagene OR tisagenlecleucel) AND (DLBCL OR aggressive B-cell lymphoma) AND second-line` |
| Europe PMC / PubMed | `(ZUMA-7 OR TRANSFORM OR BELINDA) AND randomized` |

---

## 5. Study Selection

Two-reviewer adjudication with HMAC-signed seal; PRISMA 2020.

---

## 6. Data Extraction

Study IDs, N randomized, refractory/relapsed strata, ORR, CR rate, manufacturing time, bridging therapy use, EFS events, cytokine release syndrome / neurotoxicity rates, RoB 2.

---

## 7. Risk of Bias Assessment

Cochrane **RoB 2**. Design-based priors:
- **All 3 trials:** D2 SOME CONCERNS (open-label by necessity — CAR-T single infusion vs multi-cycle chemo).
- **BELINDA specifically:** D2 SOME CONCERNS is particularly salient — the 52-day median time from randomisation to tisa-cel infusion plus 26% bridging therapy use may have systematically disadvantaged the CAR-T arm, contributing to the negative primary result.
- Other domains LOW for all three (IRC adjudication, stratified randomisation, SAP lock).

Author sign-off required per the provisional-RoB banner.

---

## 8. Synthesis / Statistical Methods

- **Primary pool:** DerSimonian-Laird random-effects IVW on log-HR scale for EFS.
- **CI adjustment:** HKSJ with t-distribution df=k-1; floor `max(1, Q/(k-1))`.
- **Prediction interval:** t-df=k-2 (Higgins 2009), k=3 so PI enabled.
- **Subgroup / meta-regression:** By CAR-T product (axi-cel vs liso-cel vs tisa-cel), refractory vs early-relapse, manufacturing-time strata.
- **Sensitivity:** Leave-one-out (critical given BELINDA's heterogeneous result); restrict to non-tisa-cel products.
- **Heterogeneity:** Expected to be HIGH because BELINDA's HR 1.07 vs ZUMA-7 0.40 / TRANSFORM 0.35 is mechanistically distinct (bridging + manufacturing time).
- **Zero-cell handling:** Conditional 0.5 correction.
- **Publication bias:** Low power at k=3; contour-enhanced funnel reported.
- **Trim-and-fill sensitivity:** Low-power caveat at k<10.
- **Bayesian:** Grid-approximation with half-normal(0, 0.5) prior on tau.
- **Browser-hosted WebR cross-validation (optional, user-triggered):** Analysis tab button loads WebR + `metafor` on first click.

---

## 9. Certainty of Evidence (GRADE)

Standard GRADE domains with a **pre-specified indirectness downgrade (`serious`)** for the class-level pool because the three CAR-T products differ in manufacturing time, bridging-therapy permissiveness, and conditioning regimen. Product-specific inference is preferred over a single class pool. Inconsistency downgrade is also anticipated given the BELINDA null result.

---

## 10. Reporting and Dissemination

- **Reporting guideline:** PRISMA 2020
- **Published benchmark:** No single external IPD MA combining ZUMA-7 + TRANSFORM + BELINDA at protocol freeze. Internal DL pool + heterogeneity narrative; agent-level results cited directly.

---

## 11. Living-MA Update Cadence

- **Trigger:** New 2L CAR-T RCTs, long-term survival updates (ZUMA-7 5-year, TRANSFORM 3-year, BELINDA final), real-world comparative cohorts.
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
| 9 (critical) | RoB assessment | Partial | Provisional AI-drafted; D2 SOME for all three trials (open-label). |
| 11 (critical) | Appropriate statistical methods | Yes | §8, pre-specified indirectness downgrade for class pool. |
| 13 (critical) | RoB accounted for in interpretation | Partial | GRADE §9 + BELINDA manufacturing/bridging narrative. |
| 15 (critical) | Publication bias assessment | Yes (k-appropriate) | §8 k=3 so formal tests low-power. |
| 1 | PICO research question | Yes | §2. |

---

## Changelog

- **v1.1** (2026-04-20) — Initial editor-review-revision release.
