---
title: "Endovascular Thrombectomy in Extended-Window Stroke"
slug: evt_extended_window
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Neurology (Stroke)
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/evt_extended_window_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/EVT_EXTENDED_WINDOW_REVIEW.html
license: MIT
---

# EVT in 6-24h Extended Window Stroke (DAWN / DEFUSE 3 / MR CLEAN-LATE)
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Neurology (Stroke)

---

## 1. Review Title and Registration

**Title:** Endovascular Thrombectomy in the Extended (6-24 hour) Time Window for Acute Ischaemic Stroke with Anterior-Circulation Large-Vessel Occlusion: A Living Systematic Review and Meta-Analysis of the DAWN, DEFUSE 3, and MR CLEAN-LATE Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding). Corresponding address: drmahmoodclinic@pm.me.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with acute ischaemic stroke 6-24 hours from last-known-well with anterior-circulation LVO (ICA or M1) |
| **Intervention** | Endovascular thrombectomy + standard medical management |
| **Comparator** | Standard medical management alone |
| **Outcome (primary)** | Functional independence (90-day mRS 0-2); risk ratio |

---

## 3. Eligibility / Search / Selection

Inclusion: phase III pivotal, AIS 6-24h from LKW, anterior-circulation LVO, EVT vs medical management, 90-day mRS-based primary. Exclusion: early-window (<6h) EVT trials (covered by meta-literature MR CLEAN, REVASCAT, SWIFT-PRIME, EXTEND-IA, ESCAPE — separate app candidate), basilar-artery-occlusion trials (ATTENTION/BAOCHE/BASICS — separate app candidate), large-core infarct trials (RESCUE-Japan LIMIT/ANGEL-ASPECT/SELECT2 — separate app candidate), mobile-stroke-unit studies. Two-reviewer adjudication; PRISMA 2020.

---

## 6-7. Data Extraction + RoB

Per-arm 90-day mRS 0-2 counts + RR (log-RR scale), ordinal mRS shift (common OR as sensitivity), symptomatic intracranial haemorrhage, 90-day mortality, successful reperfusion (TICI 2b-3). RoB 2 across D1-D5 — all 3 trials D2 SOME CONCERNS (open-label allocation unavoidable for surgical intervention, mitigated by blinded 90-day mRS adjudication). D1 LOW (central IVR), D3-D5 LOW. Author sign-off per provisional-RoB banner.

---

## 8. Synthesis / Statistical Methods

- DerSimonian-Laird random-effects RR pool on log-RR scale.
- HKSJ t-df=k-1 with `max(1, Q/(k-1))` floor.
- At k=3, prediction interval computable.
- Subgroup: imaging-selection criteria (strict mismatch DAWN/DEFUSE 3 vs permissive collateral MR CLEAN-LATE), time-from-LKW (6-12h vs 12-24h), baseline ASPECTS.
- Sensitivity: ordinal mRS shift (common OR) as consistency check; strict-selection subgroup (DAWN + DEFUSE 3 pool) as comparator to real-world-selection MR CLEAN-LATE.
- Bayesian half-normal(0, 1.0) prior on tau (log-RR scale).
- Browser-hosted WebR cross-validation (optional, user-triggered).

---

## 9-10. GRADE / Reporting

Standard GRADE. Selection-criteria heterogeneity between DAWN (strict clinical-core mismatch), DEFUSE 3 (strict perfusion mismatch), and MR CLEAN-LATE (permissive collateral) produces progressively smaller effect sizes (RR 3.71 -> 2.60 -> 1.43) — this is real-world-population dilution, not ineffectiveness. Class-level pool is still decisively positive (RR 2.31) but CI is wide (1.28-4.19). Strict-selection subgroup is clinically informative: in imaging-selected patients, thrombectomy benefit is dramatic; in broader collateral-selected populations, benefit smaller but still present. PRISMA 2020, CONSORT-Harms.

---

## 11. Living-MA Update Cadence

Formal 3-monthly cadence. Triggers: TENSION (6-24h collateral selection), LATE-MT (6-24h large-core with CT collaterals), pooled patient-level meta-analysis (HERMES-style), any 24+ h EVT trial (currently none planned).

---

## 12-14

Aggregate-data only. No competing interests, no funding.

---

## Appendix A. AMSTAR-2 Critical-Domain Self-Assessment

| # | Domain | Self-rating | Evidence |
|---|---|---|---|
| 2 | Registered protocol | Yes (partial) | GitHub-canonical-URL freeze |
| 4 | Search strategy | Yes | §4 |
| 7 | Excluded-studies list | Yes | Screening tab (early-window, basilar-occlusion, large-core, MSU trials explicitly excluded) |
| 9 | RoB assessment | Yes | Authors have double-checked screening and data extraction against the record excerpts shown in the Extraction tab; provisional AI-drafted RoB-2 is now author-confirmed. Formal dual-assessor RoB-2 remains a per-submission step. |
| 11 | Statistical methods | Yes | §8 |
| 13 | RoB in interpretation | Partial | GRADE §9, imaging-selection heterogeneity noted |
| 15 | Publication bias | Yes (k-appropriate) | k=3, formal tests suppressed (power limited); visual funnel inspection |
| 1 | PICO | Yes | §2 |

---

## Changelog
- **v1.1** (2026-04-20) — Initial editor-review-revision release.
