---
title: "Patisiran and Vutrisiran for hATTR Polyneuropathy"
slug: patisiran_polyneuropathy
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Neurology
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/patisiran_polyneuropathy_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/PATISIRAN_POLYNEUROPATHY_REVIEW.html
license: MIT
---

# Patisiran and Vutrisiran for hATTR Polyneuropathy (APOLLO / HELIOS-A)
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Neurology

---

## 1. Review Title and Registration

**Title:** Patisiran and Vutrisiran (Hepatic-Targeted TTR-Silencing siRNA) for Hereditary Transthyretin-Mediated Amyloidosis with Polyneuropathy: A Living Systematic Review and Meta-Analysis of Phase 3 RCTs (APOLLO and HELIOS-A)

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding). Corresponding address: drmahmoodclinic@pm.me.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with hereditary transthyretin-mediated amyloidosis and polyneuropathy (stages 1-2) |
| **Intervention** | Patisiran 0.3 mg/kg IV Q3W (APOLLO) or vutrisiran 25 mg SC Q3M (HELIOS-A) |
| **Comparator** | Placebo (APOLLO: concurrent; HELIOS-A: external APOLLO placebo by prospective design) |
| **Outcome (primary)** | Modified Neuropathy Impairment Score +7 (mNIS+7) change from baseline at month 18 (continuous MD) |

---

## 3. Eligibility / Search / Selection

Inclusion: phase III pivotal, adults with hATTR polyneuropathy (stages 1-2), TTR-silencing siRNA (patisiran or vutrisiran), placebo or external-placebo comparator, mNIS+7 at 18 months. Exclusion: wild-type ATTR without genetic variant, ATTR cardiomyopathy without polyneuropathy (covered by ATTR_CM app), phase II dose-finding, non-siRNA therapies (tafamidis, inotersen separate apps). Two-reviewer adjudication; PRISMA 2020.

---

## 6-7. Data Extraction + RoB

Per-arm mNIS+7 mean change + SE (MD scale), Norfolk QoL-DN, timed 10-metre walk, mBMI, COMPASS-31, serum TTR knockdown. Safety: infusion-related reactions (patisiran), injection-site reactions (vutrisiran), peripheral oedema, liver enzymes, vitamin A supplementation. RoB 2 across D1-D5 — APOLLO LOW across all; HELIOS-A D2 SOME CONCERNS (open-label active arms; primary vs external APOLLO placebo raises risk of performance bias, partly mitigated by centrally adjudicated mNIS+7). Author sign-off per provisional-RoB banner.

---

## 8. Synthesis / Statistical Methods

- DerSimonian-Laird random-effects IVW on MD scale (mNIS+7).
- HKSJ t-df=k-1 with `max(1, Q/(k-1))` floor.
- At k=2, FE-IVW sensitivity per CART-MM SAP.
- PI suppressed at k<3.
- Subgroup: V30M vs non-V30M genotype, prior tetrabenazine use, baseline NIS severity.
- Sensitivity: Norfolk QoL-DN as co-primary consistency check; exclude HELIOS-A (open-label/external-placebo) to obtain APOLLO-only RE estimate.
- Bayesian half-normal(0, 10) prior on tau (scale chosen for mNIS+7 MD).
- Browser-hosted WebR cross-validation (optional, user-triggered).

---

## 9-10. GRADE / Reporting

Standard GRADE. HELIOS-A D2 SOME CONCERNS (open-label with external APOLLO placebo) is a downgrade candidate; APOLLO-only sensitivity drop is reported. Both trials show clinically meaningful halt/reversal of neuropathy progression (LS mean diff -34 APOLLO, -29 HELIOS-A on mNIS+7 — direction and magnitude consistent). Class-level (hepatic TTR-silencing siRNA) conclusion supported. PRISMA 2020, CONSORT-Harms.

---

## 11. Living-MA Update Cadence

Formal 3-monthly cadence. Triggers: APOLLO-B (patisiran in ATTR cardiomyopathy) if applicable for a cardiac-specific app, vutrisiran long-term open-label extension, eplontersen (ION-682884/WAINUA) phase 3 readouts, any CRISPR-based in-vivo TTR editors (NTLA-2001 Phase 1/2 → Phase 3).

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
| 13 | RoB in interpretation | Partial | GRADE §9, HELIOS-A open-label + external-placebo downgrade noted |
| 15 | Publication bias | Yes (k-appropriate) | k=2, formal tests suppressed |
| 1 | PICO | Yes | §2 |

---

## Changelog
- **v1.1** (2026-04-20) — Initial editor-review-revision release.
