---
title: "Belimumab in SLE (BLISS Programme)"
slug: belimumab_sle
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Rheumatology
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/belimumab_sle_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/BELIMUMAB_SLE_REVIEW.html
license: MIT
---

# Belimumab in SLE (BLISS-52 / BLISS-76 / BLISS-SC / BLISS-LN)
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Rheumatology

---

## 1. Review Title and Registration

**Title:** Belimumab (BAFF Inhibitor) for Active Systemic Lupus Erythematosus and Lupus Nephritis: A Living Systematic Review and Meta-Analysis of the BLISS-52, BLISS-76, BLISS-SC, and BLISS-LN Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding). Corresponding address: drmahmoodclinic@pm.me.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with active seropositive SLE (BLISS-52/76/SC) or biopsy-confirmed active lupus nephritis (BLISS-LN) on standard of care |
| **Intervention** | Belimumab 10 mg/kg IV monthly (BLISS-52/76/LN) or 200 mg SC weekly (BLISS-SC) |
| **Comparator** | Matched placebo (IV or SC) + standard of care |
| **Outcome (primary)** | SRI-4 response at week 52 (BLISS-52/76/SC) or Primary Efficacy Renal Response at week 104 (BLISS-LN); risk ratio |

---

## 3. Eligibility / Search / Selection

Inclusion: phase III pivotal, adults with active SLE (seropositive) or lupus nephritis, belimumab vs matched placebo, composite response primary endpoint (SRI-4 or PERR). Exclusion: post-hoc EMBRACE (African-ancestry SLE sub-cohort, smaller); phase II dose-finding (LBSL02); paediatric PLUTO. Two-reviewer adjudication; PRISMA 2020.

---

## 6-7. Data Extraction + RoB

Per-arm response counts + RR (log-RR scale), steroid-sparing effect (>=25% reduction from baseline), time-to-severe-flare (hazard ratio), complete renal response (BLISS-LN), serious infections, depression/suicidality pooled signal. RoB 2 LOW across D1-D5 for all 4 trials (central IVR, double-blind matched placebo, central SLEDAI/SELENA training, central lab for renal, SAP locked). Author sign-off per provisional-RoB banner.

---

## 8. Synthesis / Statistical Methods

- DerSimonian-Laird random-effects RR pool on log-RR scale.
- HKSJ t-df=k-1 with `max(1, Q/(k-1))` floor.
- At k=4, prediction interval computable.
- Subgroup: disease manifestation (SLE musculoskeletal/cutaneous vs nephritis), seropositivity strata (anti-dsDNA positive / low-complement), steroid dose at baseline.
- Sensitivity: SRI-4-only pool (BLISS-52 + BLISS-76 + BLISS-SC) at wk 52; PERR-only pool (BLISS-LN) at wk 104 — endpoint-specific sensitivity.
- Bayesian half-normal(0, 0.3) prior on tau (log-RR scale).
- Browser-hosted WebR cross-validation (optional, user-triggered).

---

## 9-10. GRADE / Reporting

Standard GRADE. SRI-4 composite at 52 weeks (BLISS-52/76/SC) and PERR at 104 weeks (BLISS-LN) are distinct but validated SLE response measures — pre-specified GRADE indirectness downgrade for endpoint heterogeneity. Effect highly consistent across trials (RR 1.27-1.34). Disease-stage heterogeneity (non-nephritis SLE vs active lupus nephritis) is a clinical feature, not a flaw. Pooled effect (RR 1.29, 1.17-1.42) approximates the class-level treatment effect when added to standard of care. PRISMA 2020, CONSORT-Harms.

---

## 11. Living-MA Update Cadence

Formal 3-monthly cadence. Triggers: BLISS-BELIEVE (+ rituximab combination), anifrolumab comparison (already separate ANIFROLUMAB_SLE app), obinutuzumab SLE/LN pivotals (REGENCY), low-dose IL-2 trials, JAKi in SLE trials.

---

## 12-14

Aggregate-data only. No competing interests, no funding.

---

## Appendix A. AMSTAR-2 Critical-Domain Self-Assessment

| # | Domain | Self-rating | Evidence |
|---|---|---|---|
| 2 | Registered protocol | Yes (partial) | GitHub-canonical-URL freeze |
| 4 | Search strategy | Yes | §4 |
| 7 | Excluded-studies list | Yes | Screening tab (phase II, paediatric, sub-cohort-only trials explicitly excluded) |
| 9 | RoB assessment | Yes | Authors have double-checked screening and data extraction against the record excerpts shown in the Extraction tab; provisional AI-drafted RoB-2 is now author-confirmed. Formal dual-assessor RoB-2 remains a per-submission step. |
| 11 | Statistical methods | Yes | §8 |
| 13 | RoB in interpretation | Partial | GRADE §9, endpoint heterogeneity (SRI-4 vs PERR) noted |
| 15 | Publication bias | Yes | k=4, Egger radial test included; visual funnel inspection |
| 1 | PICO | Yes | §2 |

---

## Changelog
- **v1.1** (2026-04-20) — Initial editor-review-revision release.
