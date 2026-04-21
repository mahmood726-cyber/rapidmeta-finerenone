---
title: "Thrombectomy in Large-Core Infarct Stroke"
slug: evt_largecore
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Neurology (Stroke)
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/evt_largecore_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/EVT_LARGECORE_REVIEW.html
license: MIT
---

# EVT in Large-Core Stroke (RESCUE-Japan LIMIT / ANGEL-ASPECT / SELECT2)
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Neurology (Stroke)

---

## 1. Review Title and Registration

**Title:** Endovascular Thrombectomy in Acute Ischaemic Stroke with Large Ischaemic Core (ASPECTS 3-5 or Core >=50 mL): A Living Systematic Review and Meta-Analysis of the RESCUE-Japan LIMIT, ANGEL-ASPECT, and SELECT2 Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding). Corresponding address: drmahmoodclinic@pm.me.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with acute anterior-circulation LVO and large ischaemic core (ASPECTS 3-5 or core volume >=50 mL) |
| **Intervention** | Endovascular thrombectomy + medical management |
| **Comparator** | Medical management alone |
| **Outcome (primary)** | Functional independence (90-day mRS 0-2); risk ratio |

---

## 3. Eligibility / Search / Selection

Inclusion: phase III pivotal, large-core AIS (ASPECTS 3-5 or core >=50 mL), EVT vs medical, 90-day mRS primary or key secondary. Exclusion: small-core (ASPECTS 6-10) trials (covered by standard early-window EVT evidence), extended-window trials with strict-mismatch selection (DAWN, DEFUSE 3 — EVT_EXTENDED_WINDOW app), basilar-occlusion trials (EVT_BASILAR app), phase II. Two-reviewer adjudication; PRISMA 2020.

---

## 6-7. Data Extraction + RoB

Per-arm mRS 0-2 counts + RR (log-RR scale), ordinal mRS shift (common OR sensitivity), mRS 0-3 functional outcome, symptomatic intracranial haemorrhage, 90-day mortality, successful reperfusion (TICI 2b-3). RoB 2 — all 3 trials D2 SOME CONCERNS (open-label surgical intervention; mitigated by blinded mRS adjudication). D1 LOW, D3-D5 LOW. Author sign-off per provisional-RoB banner.

---

## 8. Synthesis / Statistical Methods

- DerSimonian-Laird random-effects RR pool on log-RR scale (mRS 0-2).
- HKSJ t-df=k-1 with `max(1, Q/(k-1))` floor.
- At k=3, prediction interval computable.
- Subgroup: time window (<6h RESCUE-Japan LIMIT vs <24h ANGEL-ASPECT/SELECT2), core-size definition (ASPECTS-only vs ASPECTS-or-volume-based), regional site (Japan / China / Global).
- Sensitivity: ordinal mRS shift common OR as consistency; exclude SELECT2 (most permissive core definition) as sensitivity.
- Bayesian half-normal(0, 0.5) prior on tau (log-RR scale).
- Browser-hosted WebR cross-validation (optional, user-triggered).

---

## 9-10. GRADE / Reporting

Standard GRADE. Highly consistent effect direction and magnitude across 3 trials (mRS 0-2 RR 1.75 / 2.50 / 2.82). Large-core patients were previously excluded from EVT trials; this pool establishes benefit in that population. Trial-selection criteria differ slightly (time window, ASPECTS-only vs ASPECTS-or-core-volume) but direction invariant. Pre-specified GRADE indirectness downgrade for criterion heterogeneity. PRISMA 2020, CONSORT-Harms.

---

## 11. Living-MA Update Cadence

Formal 3-monthly cadence. Triggers: TENSION 24h large-core readout, LASTE Tokyo-criteria extension, TESLA 24h readout, any pooled HERMES-LC IPD meta-analysis.

---

## 12-14

Aggregate-data only. No competing interests, no funding.

---

## Appendix A. AMSTAR-2 Critical-Domain Self-Assessment

| # | Domain | Self-rating | Evidence |
|---|---|---|---|
| 2 | Registered protocol | Yes (partial) | GitHub-canonical-URL freeze |
| 4 | Search strategy | Yes | §4 |
| 7 | Excluded-studies list | Yes | Screening tab (small-core, strict-mismatch extended-window, basilar-occlusion explicitly excluded) |
| 9 | RoB assessment | Yes | Authors have double-checked screening and data extraction against the record excerpts shown in the Extraction tab; provisional AI-drafted RoB-2 is now author-confirmed. Formal dual-assessor RoB-2 remains a per-submission step. |
| 11 | Statistical methods | Yes | §8 |
| 13 | RoB in interpretation | Partial | GRADE §9, criterion-heterogeneity indirectness noted |
| 15 | Publication bias | Yes (k-appropriate) | k=3, formal tests suppressed |
| 1 | PICO | Yes | §2 |

---

## Changelog
- **v1.1** (2026-04-20) — Initial editor-review-revision release.
