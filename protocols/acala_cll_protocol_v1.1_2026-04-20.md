---
title: "Acalabrutinib for Chronic Lymphocytic Leukaemia"
slug: acala_cll
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Haematology
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/acala_cll_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/ACALABRUTINIB_CLL_REVIEW.html
license: MIT
---

# Acalabrutinib for CLL (ELEVATE-TN / ASCEND)
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Haematology

---

## 1. Review Title and Registration

**Title:** Acalabrutinib (Selective Second-Generation Bruton Tyrosine Kinase Inhibitor) for Treatment-Naive and Relapsed/Refractory Chronic Lymphocytic Leukaemia: A Living Systematic Review and Meta-Analysis of the ELEVATE-TN and ASCEND Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding). Corresponding address: drmahmoodclinic@pm.me.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with CLL — treatment-naive (ELEVATE-TN, aged >=65 or unfit) or relapsed/refractory with >=1 prior line (ASCEND) |
| **Intervention** | Acalabrutinib 100 mg orally BID (monotherapy in both trials; +/- obinutuzumab in ELEVATE-TN +O arm) |
| **Comparator** | ELEVATE-TN: chlorambucil + obinutuzumab; ASCEND: investigator choice (idelalisib+rituximab or bendamustine+rituximab) |
| **Outcome (primary)** | Progression-free survival (IRC-assessed; hazard ratio) |

---

## 3. Eligibility / Search / Selection

Inclusion: phase III pivotal, CLL (treatment-naive or R/R), acalabrutinib vs active comparator, IRC-assessed PFS primary. Exclusion: phase II, SLL-only cohorts, BTKi head-to-head trials (ELEVATE-RR covered separately), ibrutinib trials (ECOG 1912/RESONATE separate apps), venetoclax/obinutuzumab combinations. Two-reviewer adjudication; PRISMA 2020.

---

## 6-7. Data Extraction + RoB

Per-arm PFS HR and CI (log-HR scale), ORR, OS HR, del17p/TP53-mutated subgroup HRs. Safety: atrial fibrillation, major haemorrhage, hypertension, infections (grade >=3), second primary malignancies, treatment discontinuations. RoB 2 across D1-D5 — both trials D2 SOME CONCERNS (open-label allocation; route/schedule differ between arms, mitigated by IRC-adjudicated PFS). D1 LOW (central IVR stratified by del17p/TP53/ECOG/prior therapies), D3-D5 LOW. Author sign-off per provisional-RoB banner.

---

## 8. Synthesis / Statistical Methods

- DerSimonian-Laird random-effects IVW on log-HR scale (PFS).
- HKSJ t-df=k-1 with `max(1, Q/(k-1))` floor.
- At k=2, FE-IVW sensitivity per CART-MM SAP.
- PI suppressed at k<3.
- Subgroup: line of therapy (treatment-naive vs R/R), del17p/TP53-mutated presence, IGHV status.
- Sensitivity: ORR as consistency check; acalabrutinib+obinutuzumab arm (ELEVATE-TN) as class-combination sensitivity.
- Bayesian half-normal(0, 0.5) prior on tau (log-HR scale).
- Browser-hosted WebR cross-validation (optional, user-triggered).

---

## 9-10. GRADE / Reporting

Standard GRADE. Pooling ELEVATE-TN and ASCEND is indirectness-flagged — different comparators (Clb+O chemoimmunotherapy vs investigator choice with idelalisib+R or bendamustine+R) and different lines (treatment-naive vs R/R). Class-level BTKi effect is the pooled estimand; comparator heterogeneity is explicit. Both HRs substantially favour acalabrutinib (0.21 treatment-naive, 0.28 R/R at mature follow-up) — consistency is high. AF/bleeding/hypertension profile is more favourable than first-generation ibrutinib (historical benchmarks, not within-trial). PRISMA 2020, CONSORT-Harms.

---

## 11. Living-MA Update Cadence

Formal 3-monthly cadence. Triggers: ELEVATE-TN 7-year update, ASCEND 6-year update, ELEVATE-RR (acalabrutinib vs ibrutinib head-to-head), zanubrutinib ALPINE/SEQUOIA comparisons, pirtobrutinib BRUIN-CLL-321 readouts, any fixed-duration BTKi + venetoclax combinations.

---

## 12-14

Aggregate-data only. No competing interests, no funding.

---

## Appendix A. AMSTAR-2 Critical-Domain Self-Assessment

| # | Domain | Self-rating | Evidence |
|---|---|---|---|
| 2 | Registered protocol | Yes (partial) | GitHub-canonical-URL freeze |
| 4 | Search strategy | Yes | §4 |
| 7 | Excluded-studies list | Yes | Screening tab |
| 9 | RoB assessment | Yes | Authors have double-checked screening and data extraction against the record excerpts shown in the Extraction tab; provisional AI-drafted RoB-2 is now author-confirmed. Formal dual-assessor RoB-2 remains a per-submission step. |
| 11 | Statistical methods | Yes | §8 |
| 13 | RoB in interpretation | Partial | GRADE §9, comparator and line-of-therapy indirectness noted |
| 15 | Publication bias | Yes (k-appropriate) | k=2, formal tests suppressed |
| 1 | PICO | Yes | §2 |

---

## Changelog
- **v1.1** (2026-04-20) — Initial editor-review-revision release.
