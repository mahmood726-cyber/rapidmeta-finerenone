---
title: "Upadacitinib for Moderate-to-Severe Crohn Disease"
slug: upa_cd
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Gastroenterology
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/upa_cd_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/UPADACITINIB_CD_REVIEW.html
license: MIT
---

# Upadacitinib for Moderate-to-Severe Crohn Disease
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Gastroenterology

---

## 1. Review Title and Registration

**Title:** Upadacitinib (Oral JAK1-Selective Inhibitor) for Moderate-to-Severe Crohn Disease: A Living Systematic Review and Meta-Analysis of the U-EXCEL, U-EXCEED, and U-ENDURE Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding).

**Corresponding address:** drmahmoodclinic@pm.me (GMC 6071047), Royal Free Hospital and Barnet Hospital, London, UK.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with moderate-to-severe Crohn disease (CDAI 220-450) with inadequate response to conventional or biologic therapy |
| **Intervention** | Upadacitinib 45 mg PO daily (induction) or 30 mg PO daily (maintenance) |
| **Comparator** | Matched placebo |
| **Outcome (primary)** | Clinical remission (CDAI <150) at the trial-specific primary timepoint (week 12 induction; week 52 maintenance) |

---

## 3. Eligibility / Search / Selection

Inclusion: RCT, phase III pivotal, upadacitinib at licensed dose, placebo comparator. Exclusion: ulcerative colitis, psoriatic arthritis, atopic dermatitis (separate reviews). Two-reviewer adjudication with HMAC-signed seal; PRISMA 2020.

---

## 6-7. Data Extraction + RoB

Clinical remission counts, endoscopic response (SES-CD), biologic-failure stratification, RoB 2. Design-based priors LOW across D1-D5; author sign-off per the provisional-RoB banner.

---

## 8. Synthesis / Statistical Methods

- DerSimonian-Laird random-effects IVW on log-OR (or log-RR) scale; HKSJ t-df=k-1 with `max(1, Q/(k-1))` floor.
- PI t-df=k-2 (Higgins 2009), enabled at k=3.
- Subgroup: biologic-naive (U-EXCEL) vs biologic-failure (U-EXCEED) vs maintenance (U-ENDURE).
- Zero-cell conditional 0.5 correction.
- Trim-and-fill sensitivity with k<10 low-power caveat.
- Bayesian half-normal(0, 0.5) prior on tau.
- **Browser-hosted WebR cross-validation (optional, user-triggered)** via the Analysis tab button.

---

## 9-10. GRADE / Reporting

Standard GRADE; PRISMA 2020. Internal DL pool benchmark (no external IPD MA of the U-EXCEL/U-EXCEED/U-ENDURE trio at freeze).

---

## 11. Living-MA Update Cadence

Formal 3-monthly cadence; new phase 3 JAK-CD publications trigger amendment.

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
| 15 | Publication bias | Yes (k-appropriate) | §8 |
| 1 | PICO | Yes | §2 |

---

## Changelog
- **v1.1** (2026-04-20) — Initial editor-review-revision release.
