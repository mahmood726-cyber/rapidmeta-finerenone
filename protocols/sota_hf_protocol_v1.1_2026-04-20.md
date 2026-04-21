---
title: "Sotagliflozin (Dual SGLT1/2 Inhibitor) in HF / CKD-T2D"
slug: sota_hf
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Cardiology (Heart Failure)
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/sota_hf_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/SOTAGLIFLOZIN_HF_REVIEW.html
license: MIT
---

# Sotagliflozin in HF / CKD-T2D (SOLOIST-WHF / SCORED)
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Cardiology (Heart Failure)

---

## 1. Review Title and Registration

**Title:** Sotagliflozin (Dual SGLT1/SGLT2 Inhibitor) in Type 2 Diabetes with Recent Worsening Heart Failure (SOLOIST-WHF) or Chronic Kidney Disease (SCORED): A Living Systematic Review and Meta-Analysis of Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding). Corresponding address: drmahmoodclinic@pm.me.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with type 2 diabetes + either recent worsening HF hospitalisation (SOLOIST-WHF) OR CKD stage 3-4 with CV risk factors (SCORED) |
| **Intervention** | Sotagliflozin 200 mg/day PO (up-titrated to 400 mg/day) |
| **Comparator** | Matched placebo |
| **Outcome (primary)** | Total events of CV death, HF hospitalisation, or urgent HF visit (amended primary after trial truncation); hazard ratio |

---

## 3. Eligibility / Search / Selection

Inclusion: phase III pivotal, T2D-containing populations, sotagliflozin (dual SGLT1/2) vs placebo, CV death/HF hosp/urgent HF composite (total-event) primary. Exclusion: SGLT2-selective inhibitor trials (covered by separate apps: SGLT2-HF, SGLT2-CKD), phase II, sotagliflozin T1D adjunct trials (distinct indication - DEPICT, inTandem). Two-reviewer adjudication; PRISMA 2020.

---

## 6-7. Data Extraction + RoB

Per-arm total event count + HR on log-hazard scale, HF hospitalisation only, CV death, renal composite, albuminuria. Safety: diarrhoea (SGLT1-class effect), genital mycotic infection, DKA, volume depletion, amputation, Fournier gangrene. RoB 2 across D1-D5 — both trials D5 SOME CONCERNS (early sponsor-initiated truncation with amended primary-endpoint definition; non-adjudication concern low given central adjudication). D1-D4 LOW. Author sign-off per provisional-RoB banner.

---

## 8. Synthesis / Statistical Methods

- DerSimonian-Laird random-effects IVW on log-HR scale (total CV composite).
- HKSJ t-df=k-1 with `max(1, Q/(k-1))` floor.
- At k=2, FE-IVW sensitivity per CART-MM SAP.
- PI suppressed at k<3.
- Subgroup: LVEF (reduced/mildly-reduced/preserved), CKD stage, baseline SGLT2 use.
- Sensitivity: HF hospitalisation alone (cleaner endpoint unaffected by amended primary); time-to-first vs total-events parameterisation.
- Bayesian half-normal(0, 0.3) prior on tau (log-HR scale).
- Browser-hosted WebR cross-validation (optional, user-triggered).

---

## 9-10. GRADE / Reporting

Standard GRADE. Dual SGLT1/2 inhibition is a distinct mechanism from selective SGLT2 inhibitors — the SGLT1 component contributes the GI-intestinal glucose-uptake blockade (driving diarrhoea on-target) and may add postprandial glucose control. Both trials truncated early — amended primary endpoint definitions (total events rather than time-to-first) are pre-specified in amendments but introduce minor imprecision. Results directionally concordant with and not meaningfully different from selective SGLT2i class pool for HF composite. PRISMA 2020, CONSORT-Harms.

---

## 11. Living-MA Update Cadence

Formal 3-monthly cadence. Triggers: SOLOIST/SCORED pooled-subgroup publications, any revived sotagliflozin T2D + HF pivotal (if sponsorship restored), long-term extension cohorts, head-to-head SGLT1/2 vs selective SGLT2 (unlikely but possible).

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
| 13 | RoB in interpretation | Partial | GRADE §9, trial-truncation amended-primary noted |
| 15 | Publication bias | Yes (k-appropriate) | k=2, formal tests suppressed |
| 1 | PICO | Yes | §2 |

---

## Changelog
- **v1.1** (2026-04-20) — Initial editor-review-revision release.
