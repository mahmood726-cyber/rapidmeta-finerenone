---
title: "Faricimab for Neovascular Age-Related Macular Degeneration"
slug: faricimab_namd
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Ophthalmology
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/faricimab_namd_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/FARICIMAB_NAMD_REVIEW.html
license: MIT
---

# Faricimab for Neovascular Age-Related Macular Degeneration
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Ophthalmology

---

## 1. Review Title and Registration

**Title:** Faricimab (Anti-VEGF-A + Anti-Ang-2 Bispecific Antibody) with Up-to-Q16W Personalised Treatment Interval vs Aflibercept Q8W in Treatment-Naive Neovascular Age-Related Macular Degeneration: A Living Systematic Review and Meta-Analysis of the TENAYA and LUCERNE Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding).

**Corresponding address:** drmahmoodclinic@pm.me (GMC 6071047), Royal Free Hospital and Barnet Hospital, London, UK.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with treatment-naive neovascular age-related macular degeneration |
| **Intervention** | Faricimab 6 mg intravitreal with up-to-Q16W personalised treatment interval |
| **Comparator** | Aflibercept 2 mg intravitreal Q8W fixed |
| **Outcome (primary)** | Adjusted mean change in best-corrected visual acuity (BCVA, ETDRS letter score) from baseline at the average of weeks 40, 44, and 48 |

---

## 3. Eligibility / Search / Selection

Inclusion: phase III pivotal, treatment-naive nAMD, faricimab vs aflibercept, BCVA at wk 40-48 as primary. Exclusion: DME (separate review), macular edema due to RVO (separate review). Two-reviewer adjudication with HMAC-signed seal; PRISMA 2020.

---

## 6-7. Data Extraction + RoB

BCVA letter change (ETDRS), central subfield thickness, dosing-interval achievement, safety (IOI, vitritis). RoB 2 design-based LOW across D1-D5; double-blind design with masked BCVA examiners.

---

## 8. Synthesis / Statistical Methods

- DerSimonian-Laird random-effects IVW on MD scale (letter score).
- HKSJ t-df=k-1 with `max(1, Q/(k-1))` floor.
- PI suppressed at k=2.
- Subgroup: baseline BCVA strata.
- Non-inferiority primary (margin -4 letters); superiority secondary.
- Trim-and-fill sensitivity with k<10 caveat.
- Bayesian half-normal(0, 0.5) prior on tau.
- **Browser-hosted WebR cross-validation (optional, user-triggered)** via the Analysis tab button.

---

## 9-10. GRADE / Reporting

Standard GRADE; PRISMA 2020. No external IPD MA at freeze; TENAYA + LUCERNE were designed as replicate pivotals and the app's DL pool is the reference.

---

## 11. Living-MA Update Cadence

Formal 3-monthly cadence; TRUCKEE/WOODS real-world extensions and EyleaHD trials trigger amendment.

---

## Appendix A. AMSTAR-2 Critical-Domain Self-Assessment

| # | Domain | Self-rating | Evidence |
|---|---|---|---|
| 2 | Registered protocol | Yes (partial) | GitHub-canonical-URL freeze |
| 4 | Search strategy | Yes | §4 |
| 7 | Excluded-studies list | Yes | Screening tab |
| 9 | RoB assessment | Partial | Provisional; formal dual-assessor required |
| 11 | Statistical methods | Yes | §8 |
| 13 | RoB in interpretation | Partial | GRADE §9 |
| 15 | Publication bias | Yes (k-appropriate) | k=2 formal tests suppressed |
| 1 | PICO | Yes | §2 |

---

## Changelog
- **v1.1** (2026-04-20) — Initial editor-review-revision release.
