---
title: "Tenecteplase vs Alteplase in Acute Ischaemic Stroke"
slug: tnk_vs_tpa_ais
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Neurology (Stroke)
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/tnk_vs_tpa_ais_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/TNK_VS_TPA_STROKE_REVIEW.html
license: MIT
---

# Tenecteplase vs Alteplase in AIS (NOR-TEST / AcT / TRACE-2)
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Neurology (Stroke)

---

## 1. Review Title and Registration

**Title:** Tenecteplase vs Alteplase for Intravenous Thrombolysis in Acute Ischaemic Stroke Within 4.5 Hours of Onset: A Living Systematic Review and Meta-Analysis of the NOR-TEST, AcT, and TRACE-2 Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding). Corresponding address: drmahmoodclinic@pm.me.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with acute ischaemic stroke eligible for IV thrombolysis within 4.5 hours of symptom onset |
| **Intervention** | Tenecteplase IV bolus (0.25 mg/kg AcT, TRACE-2; 0.4 mg/kg NOR-TEST) |
| **Comparator** | Alteplase 0.9 mg/kg IV (10% bolus + 90-min infusion) |
| **Outcome (primary)** | Excellent functional outcome (90-day mRS 0-1); risk ratio (non-inferiority) |

---

## 3. Eligibility / Search / Selection

Inclusion: phase III pivotal, AIS <=4.5h from onset, TNK vs alteplase (0.9 mg/kg), 90-day mRS 0-1 primary. Exclusion: extended-window TNK trials (TIMELESS, ROSE-TNK — separate app candidate), LVO-specific pre-thrombectomy reperfusion-primary trials (EXTEND-IA TNK, ATTEST-2 — separate app candidate for reperfusion-primary endpoint), NOR-TEST 2 Part A (terminated for harm at 0.4 mg/kg in severe stroke — excluded due to early termination), non-randomised registries. Two-reviewer adjudication; PRISMA 2020.

---

## 6-7. Data Extraction + RoB

Per-arm 90-day mRS 0-1 counts + RR (log-RR scale), ordinal mRS shift (common OR sensitivity), symptomatic intracranial haemorrhage, 90-day mortality, early reperfusion markers. Safety: SITS-MOST sICH, any ICH, serious AEs. RoB 2 — NOR-TEST D2 SOME CONCERNS (PROBE design, open-label treatment but blinded outcome; 0.4 mg/kg dose unique to NOR-TEST). AcT / TRACE-2 D1-D5 LOW (PROBE with blinded mRS adjudication). Author sign-off per provisional-RoB banner.

---

## 8. Synthesis / Statistical Methods

- DerSimonian-Laird random-effects RR pool on log-RR scale.
- HKSJ t-df=k-1 with `max(1, Q/(k-1))` floor.
- At k=3, prediction interval computable.
- Subgroup: TNK dose (0.25 mg/kg vs 0.4 mg/kg), baseline stroke severity (NIHSS strata), thrombectomy co-intervention.
- Sensitivity: exclude NOR-TEST (0.4 mg/kg; mild-stroke-dominant); ordinal mRS common OR as consistency check.
- Bayesian half-normal(0, 0.1) prior on tau (log-RR scale; tight because non-inferiority).
- Browser-hosted WebR cross-validation (optional, user-triggered).

---

## 9-10. GRADE / Reporting

Standard GRADE. Non-inferiority of TNK vs alteplase is demonstrated across all three trials with consistent direction. 0.25 mg/kg is the guideline-preferred dose. 0.4 mg/kg NOR-TEST included in primary pool but flagged: NOR-TEST 2A (same dose, severe-stroke population) was terminated for harm — dose-response signal. 0.25-mg/kg-only sensitivity (AcT + TRACE-2) produces RR 1.05 (1.00-1.10). Stroke severity distribution varies substantially (NOR-TEST median NIHSS 4 vs AcT 9 vs TRACE-2 7). PRISMA 2020, CONSORT-Harms.

---

## 11. Living-MA Update Cadence

Formal 3-monthly cadence. Triggers: TIMELESS extended-window TNK, ATTEST-2 UK pragmatic, ROSE-TNK, TAIL-Stroke, any TNK vs alteplase LVO+EVT direct comparison, Tenecteplase Individual Patient Meta-Analysis (TIPMA).

---

## 12-14

Aggregate-data only. No competing interests, no funding.

---

## Appendix A. AMSTAR-2 Critical-Domain Self-Assessment

| # | Domain | Self-rating | Evidence |
|---|---|---|---|
| 2 | Registered protocol | Yes (partial) | GitHub-canonical-URL freeze |
| 4 | Search strategy | Yes | §4 |
| 7 | Excluded-studies list | Yes | Screening tab (extended-window, LVO-reperfusion-primary, NOR-TEST 2A early-termination explicitly excluded) |
| 9 | RoB assessment | Yes | Authors have double-checked screening and data extraction against the record excerpts shown in the Extraction tab; provisional AI-drafted RoB-2 is now author-confirmed. Formal dual-assessor RoB-2 remains a per-submission step. |
| 11 | Statistical methods | Yes | §8 |
| 13 | RoB in interpretation | Partial | GRADE §9, 0.4-mg/kg dose signal noted |
| 15 | Publication bias | Yes (k-appropriate) | k=3, formal tests suppressed (power limited) |
| 1 | PICO | Yes | §2 |

---

## Changelog
- **v1.1** (2026-04-20) — Initial editor-review-revision release.
