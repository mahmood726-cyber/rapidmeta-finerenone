---
title: "SGLT2 Inhibitor CVOT Class Pool for 3P-MACE"
slug: sglt2_mace_cvot
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Cardiology (Diabetes)
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/sglt2_mace_cvot_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/SGLT2_MACE_CVOT_REVIEW.html
license: MIT
---

# SGLT2i CVOT Class Pool for 3P-MACE (EMPA-REG / CANVAS / DECLARE / VERTIS-CV)
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Cardiology (Diabetes)

---

## 1. Review Title and Registration

**Title:** SGLT2 Inhibitors (Empagliflozin, Canagliflozin, Dapagliflozin, Ertugliflozin) vs Placebo for Three-Point Major Adverse Cardiovascular Events in Type 2 Diabetes: A Living Systematic Review and Meta-Analysis of the Phase 3 Pivotal Cardiovascular Outcome Trials

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding). Corresponding address: drmahmoodclinic@pm.me.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with type 2 diabetes and established CVD (secondary-prevention-only) or mixed primary/secondary prevention with CV risk factors |
| **Intervention** | SGLT2 inhibitor (empagliflozin, canagliflozin, dapagliflozin, or ertugliflozin) |
| **Comparator** | Matched placebo on top of standard of care |
| **Outcome (primary)** | 3P-MACE (CV death, non-fatal MI, non-fatal stroke); hazard ratio |

---

## 3. Eligibility / Search / Selection

Inclusion: phase III pivotal CVOT, adults with T2D, SGLT2 inhibitor vs placebo, 3P-MACE as primary or co-primary endpoint. Exclusion: phase II dose-finding, SGLT2i HF-specific trials (SGLT2_HF separate app), SGLT2i CKD-specific trials (SGLT2_CKD separate app), non-CVOT glycaemic-control studies, sotagliflozin (dual SGLT1/2 mechanistically distinct - SOTAGLIFLOZIN_HF separate app). Two-reviewer adjudication; PRISMA 2020.

---

## 6-7. Data Extraction + RoB

Per-arm 3P-MACE event counts + HR on log-hazard scale, CV death, HF hospitalisation, renal composite, all-cause mortality. Safety: genital mycotic infections, DKA, volume depletion, amputation (canagliflozin signal), fracture, Fournier gangrene. RoB 2 LOW across D1-D5 for EMPA-REG / DECLARE / VERTIS-CV. CANVAS Program D5 SOME CONCERNS (CANVAS + CANVAS-R integrated post-hoc per pre-specified SAP; amputation signal flagged post-publication). Author sign-off per provisional-RoB banner.

---

## 8. Synthesis / Statistical Methods

- DerSimonian-Laird random-effects IVW on log-HR scale (3P-MACE).
- HKSJ t-df=k-1 with `max(1, Q/(k-1))` floor.
- At k=4, prediction interval computable.
- Subgroup: established-CVD-only vs mixed primary/secondary-prevention populations; agent-specific within-class subgroups.
- Sensitivity: HF hospitalisation pool as consistency check (class effect more pronounced on HF than MACE).
- Bayesian half-normal(0, 0.3) prior on tau (log-HR scale).
- Browser-hosted WebR cross-validation (optional, user-triggered).

---

## 9-10. GRADE / Reporting

Standard GRADE. Class-level pool across 4 SGLT2 inhibitors is the estimand; DECLARE and VERTIS-CV individually failed 3P-MACE superiority but class-level pool confirms modest MACE reduction (~9%). Population heterogeneity (secondary-only EMPA-REG/VERTIS vs mixed CANVAS/DECLARE) is a pre-specified indirectness factor. HF hospitalisation benefit is more pronounced and consistent across agents. Reference: Zelniker 2019 Lancet class-level meta-analysis reports pooled HR 0.89. PRISMA 2020, CONSORT-Harms.

---

## 11. Living-MA Update Cadence

Formal 3-monthly cadence. Triggers: post-hoc CVOT follow-up extensions, any new SGLT2i CVOT (unlikely within current pipeline), dapa-MI / EMPACT-MI post-MI class expansion, SGLT2i + finerenone combination CV outcomes.

---

## 12-14

Aggregate-data only. No competing interests, no funding.

---

## Appendix A. AMSTAR-2 Critical-Domain Self-Assessment

| # | Domain | Self-rating | Evidence |
|---|---|---|---|
| 2 | Registered protocol | Yes (partial) | GitHub-canonical-URL freeze |
| 4 | Search strategy | Yes | §4 |
| 7 | Excluded-studies list | Yes | Screening tab (HF-specific / CKD-specific / phase II explicitly excluded) |
| 9 | RoB assessment | Yes | Authors have double-checked screening and data extraction against the record excerpts shown in the Extraction tab; provisional AI-drafted RoB-2 is now author-confirmed. Formal dual-assessor RoB-2 remains a per-submission step. |
| 11 | Statistical methods | Yes | §8 |
| 13 | RoB in interpretation | Partial | GRADE §9, population-mix indirectness noted |
| 15 | Publication bias | Yes | k=4, Egger radial test included; funnel plot visually inspected |
| 1 | PICO | Yes | §2 |

---

## Changelog
- **v1.1** (2026-04-20) — Initial editor-review-revision release.
