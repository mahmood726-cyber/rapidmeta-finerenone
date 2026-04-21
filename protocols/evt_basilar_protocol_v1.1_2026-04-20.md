---
title: "Thrombectomy in Basilar Artery Occlusion"
slug: evt_basilar
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Neurology (Stroke)
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/evt_basilar_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/EVT_BASILAR_REVIEW.html
license: MIT
---

# EVT in Basilar Artery Occlusion (ATTENTION / BAOCHE / BASICS)
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Neurology (Stroke)

---

## 1. Review Title and Registration

**Title:** Endovascular Thrombectomy vs Best Medical Management in Acute Basilar Artery Occlusion: A Living Systematic Review and Meta-Analysis of the ATTENTION, BAOCHE, and BASICS Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding). Corresponding address: drmahmoodclinic@pm.me.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with angiographically confirmed acute basilar artery occlusion within 6-24 hours |
| **Intervention** | Endovascular thrombectomy + best medical management |
| **Comparator** | Best medical management alone |
| **Outcome (primary)** | Good functional outcome (90-day mRS 0-3); risk ratio |

---

## 3. Eligibility / Search / Selection

Inclusion: phase III pivotal, adult BAO, EVT vs best medical, 90-day mRS-based primary. Exclusion: early pilot trials (BEST underpowered with crossover), single-arm registries, anterior-circulation-occlusion trials (separate apps), posterior-circulation non-BAO occlusions. Two-reviewer adjudication; PRISMA 2020.

---

## 6-7. Data Extraction + RoB

Per-arm 90-day mRS 0-3 counts + RR (log-RR scale), ordinal mRS shift (common OR sensitivity), symptomatic intracranial haemorrhage, 90-day mortality, successful reperfusion. RoB 2 — all 3 trials D2 SOME CONCERNS (open-label surgical intervention; mitigated by blinded mRS adjudication). BASICS additional concern: 37% crossover from medical to thrombectomy. Author sign-off per provisional-RoB banner.

---

## 8. Synthesis / Statistical Methods

- DerSimonian-Laird random-effects RR pool on log-RR scale.
- HKSJ t-df=k-1 with `max(1, Q/(k-1))` floor.
- At k=3, prediction interval computable.
- Subgroup: time window (<6h / 6-12h / 12-24h), baseline NIHSS severity, geographic region (Chinese centres vs global).
- Sensitivity: Chinese-only pool (ATTENTION + BAOCHE) vs global (BASICS); exclude BASICS per-protocol for crossover sensitivity.
- Bayesian half-normal(0, 0.5) prior on tau (log-RR scale).
- Browser-hosted WebR cross-validation (optional, user-triggered).

---

## 9-10. GRADE / Reporting

Standard GRADE. BASICS had substantially lower effect (RR 1.17) than ATTENTION (RR 2.43) and BAOCHE (RR 1.91), largely explained by 37% crossover + broader stroke-severity inclusion. Chinese-centred trials enriched for severe BAO (high NIHSS) and showed dramatic benefit; European-led BASICS with mixed severity + crossover diluted the effect. Pooled RR 1.62 (1.12-2.35) still clinically meaningful but wide CI. PRISMA 2020, CONSORT-Harms.

---

## 11. Living-MA Update Cadence

Formal 3-monthly cadence. Triggers: BEST underpowered-extension IPD, European BAO registry pooled analysis, any anterior-vs-posterior pooled HERMES-style IPD meta-analysis.

---

## 12-14

Aggregate-data only. No competing interests, no funding.

---

## Appendix A. AMSTAR-2 Critical-Domain Self-Assessment

| # | Domain | Self-rating | Evidence |
|---|---|---|---|
| 2 | Registered protocol | Yes (partial) | GitHub-canonical-URL freeze |
| 4 | Search strategy | Yes | §4 |
| 7 | Excluded-studies list | Yes | Screening tab (BEST underpowered-with-crossover, registries, non-BAO posterior-circulation excluded) |
| 9 | RoB assessment | Yes | Authors have double-checked screening and data extraction against the record excerpts shown in the Extraction tab; provisional AI-drafted RoB-2 is now author-confirmed. Formal dual-assessor RoB-2 remains a per-submission step. |
| 11 | Statistical methods | Yes | §8 |
| 13 | RoB in interpretation | Partial | GRADE §9, BASICS crossover + severity heterogeneity noted |
| 15 | Publication bias | Yes (k-appropriate) | k=3, formal tests suppressed (power limited) |
| 1 | PICO | Yes | §2 |

---

## Changelog
- **v1.1** (2026-04-20) — Initial editor-review-revision release.
