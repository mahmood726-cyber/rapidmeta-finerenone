---
title: "KarXT (Xanomeline-Trospium) for Schizophrenia"
slug: karxt_scz
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Psychiatry
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/karxt_scz_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/KARXT_SCZ_REVIEW.html
license: MIT
---

# KarXT (Xanomeline-Trospium) for Schizophrenia (EMERGENT-2 / EMERGENT-3)
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Psychiatry

---

## 1. Review Title and Registration

**Title:** KarXT (Xanomeline-Trospium; Muscarinic M1/M4 Agonist + Peripheral Anticholinergic) for Acute Schizophrenia Exacerbation: A Living Systematic Review and Meta-Analysis of the EMERGENT Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding). Corresponding address: drmahmoodclinic@pm.me.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults (18-65) with DSM-5 schizophrenia in acute psychotic exacerbation (PANSS total >=80) |
| **Intervention** | KarXT (xanomeline 125 mg + trospium 30 mg) orally twice daily for 5 weeks |
| **Comparator** | Matched placebo |
| **Outcome (primary)** | Change from baseline in PANSS total score at week 5 (mean difference, continuous) |

---

## 3. Eligibility / Search / Selection

Inclusion: phase III pivotal, adults with DSM-5 schizophrenia in acute exacerbation, KarXT vs placebo, PANSS total week-5 primary. Exclusion: phase II dose-finding (EMERGENT-1), schizoaffective disorder, first-episode psychosis trials, open-label extensions. Two-reviewer adjudication; PRISMA 2020.

---

## 6-7. Data Extraction + RoB

Per-arm mean change + SE on PANSS total, PANSS positive, PANSS negative, CGI-Severity, Marder factors. Safety: cholinergic TEAEs (nausea, dyspepsia, vomiting), anticholinergic TEAEs (constipation, dry mouth), weight change, EPS, prolactin, QTc. RoB 2 LOW across D1-D5 (central IVR stratified, double-blind matched placebo, PANSS raters centrally certified, SAP locked). Author sign-off per provisional-RoB banner.

---

## 8. Synthesis / Statistical Methods

- DerSimonian-Laird random-effects IVW on MD scale (PANSS total).
- HKSJ t-df=k-1 with `max(1, Q/(k-1))` floor.
- At k=2, FE-IVW sensitivity per CART-MM SAP.
- PI suppressed at k<3.
- Subgroup: prior antipsychotic exposure, baseline PANSS severity (PANSS total >=100 vs 80-99).
- Sensitivity: PANSS positive and CGI-S as consistency checks.
- Bayesian half-normal(0, 2.5) prior on tau (scale chosen for PANSS MD).
- Browser-hosted WebR cross-validation (optional, user-triggered).

---

## 9-10. GRADE / Reporting

Standard GRADE. EMERGENT-2 and EMERGENT-3 are independent pivotal replicates — consistency is high. Inpatient-only populations (73-77% completion rates typical for acute antipsychotic trials) — extrapolation to chronic/outpatient use is indirect. Metabolic, EPS, and prolactin advantages over D2 antagonists are descriptive (no head-to-head comparator in these RCTs). PRISMA 2020, CONSORT-Harms for adverse events.

---

## 11. Living-MA Update Cadence

Formal 3-monthly cadence. Triggers: EMERGENT-4 open-label long-term extension, EMERGENT-5 maintenance/relapse-prevention readout, ARISE (adjunctive to D2 antagonist), any class-level muscarinic agonist (emraclidine ARISE series, others).

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
| 13 | RoB in interpretation | Partial | GRADE §9 |
| 15 | Publication bias | Yes (k-appropriate) | k=2, formal tests suppressed |
| 1 | PICO | Yes | §2 |

---

## Changelog
- **v1.1** (2026-04-20) — Initial editor-review-revision release.
