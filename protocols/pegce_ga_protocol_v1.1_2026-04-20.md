---
title: "Pegcetacoplan for Geographic Atrophy Secondary to AMD"
slug: pegce_ga
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Ophthalmology
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/pegce_ga_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/PEGCETACOPLAN_GA_REVIEW.html
license: MIT
---

# Pegcetacoplan for Geographic Atrophy Secondary to AMD (OAKS / DERBY)
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Ophthalmology

---

## 1. Review Title and Registration

**Title:** Pegcetacoplan (Intravitreal Complement C3 Inhibitor) for Geographic Atrophy Secondary to Age-Related Macular Degeneration: A Living Systematic Review and Meta-Analysis of the OAKS and DERBY Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding). Corresponding address: drmahmoodclinic@pm.me.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with geographic atrophy secondary to AMD, with or without foveal involvement |
| **Intervention** | Pegcetacoplan 15 mg intravitreal monthly (primary) or every-other-month (sensitivity) |
| **Comparator** | Sham intravitreal procedure |
| **Outcome (primary)** | Change from baseline in GA lesion area (square-root-transformed mm^2) on fundus autofluorescence at month 12 |

---

## 3. Eligibility / Search / Selection

Inclusion: phase III pivotal, GA secondary to AMD, pegcetacoplan IVT monthly or Q2M, sham comparator, FAF-measured GA lesion area primary. Exclusion: wet AMD, other retinal pathology, phase II dose-finding. Two-reviewer adjudication; PRISMA 2020.

---

## 6-7. Data Extraction + RoB

Per-arm mean change + SE for GA lesion area (sqrt-transformed), safety (intraocular inflammation, exudative AMD conversion, endophthalmitis, ischaemic optic neuropathy). RoB 2 LOW across D1-D5 (double-blind sham procedure, central FAF reading, SAP locked). Author sign-off per provisional-RoB banner.

---

## 8. Synthesis / Statistical Methods

- DerSimonian-Laird random-effects IVW on MD scale (sqrt-transformed mm^2).
- HKSJ t-df=k-1 with `max(1, Q/(k-1))` floor.
- At k=2, FE-IVW sensitivity per CART-MM SAP.
- PI suppressed at k<3.
- Subgroup: foveal vs extrafoveal GA, baseline lesion size.
- Sensitivity: month-24 timepoint (when both trials met significance) vs month-12 (DERBY did not).
- Bayesian half-normal(0, 0.5) prior on tau.
- Browser-hosted WebR cross-validation (optional, user-triggered).

---

## 9-10. GRADE / Reporting

Standard GRADE. Downgrade candidate: DERBY did not meet the 12-month primary endpoint (P=0.086); OAKS did (P=0.0054). Pre-specified 24-month combined analysis and monthly-dosing pool supports class-level efficacy but with imprecision. Safety signal for exudative AMD conversion (~12% vs ~3% sham) warrants monitoring.

---

## 11. Living-MA Update Cadence

Formal 3-monthly cadence. Triggers: GALE long-term extension; avacincaptad pegol (Izervay) GATHER-1/2 head-to-head; next-generation C3/C5 inhibitors.

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
| 13 | RoB in interpretation | Partial | GRADE §9, DERBY 12-month miss noted |
| 15 | Publication bias | Yes (k-appropriate) | k=2, formal tests suppressed |
| 1 | PICO | Yes | §2 |

---

## Changelog
- **v1.1** (2026-04-20) — Initial editor-review-revision release.
