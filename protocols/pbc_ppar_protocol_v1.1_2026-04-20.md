---
title: "PPAR Modulators (Elafibranor, Seladelpar) in PBC Second-Line"
slug: pbc_ppar
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Hepatology
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/pbc_ppar_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/PBC_PPAR_REVIEW.html
license: MIT
---

# PPAR Modulators in Primary Biliary Cholangitis Second-Line (ELATIVE / RESPONSE)
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Hepatology

---

## 1. Review Title and Registration

**Title:** PPAR Modulators (Elafibranor Dual PPARalpha/delta Agonist and Seladelpar Selective PPARdelta Agonist) as Second-Line Therapy in Primary Biliary Cholangitis with Inadequate Response or Intolerance to Ursodeoxycholic Acid: A Living Systematic Review and Meta-Analysis of Phase 3 RCTs (ELATIVE and RESPONSE)

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding). Corresponding address: drmahmoodclinic@pm.me.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with PBC and inadequate response or intolerance to UDCA (ALP >=1.67x ULN or bilirubin elevation) |
| **Intervention** | Elafibranor 80 mg PO daily (ELATIVE) or seladelpar 10 mg PO daily (RESPONSE), most with continued UDCA |
| **Comparator** | Matched placebo (with continued UDCA) |
| **Outcome (primary)** | Composite biochemical response at week 52 / month 12 (ALP <1.67x ULN with >=15% reduction AND total bilirubin <=ULN); risk ratio |

---

## 3. Eligibility / Search / Selection

Inclusion: phase III pivotal, adults with UDCA-inadequate-response or -intolerant PBC, oral PPAR modulator (PPARalpha/delta or selective PPARdelta) vs placebo, composite biochemical response primary at 12 months. Exclusion: OCA/bezafibrate trials (separate apps candidate), phase II dose-finding, decompensated cirrhosis. Two-reviewer adjudication; PRISMA 2020.

---

## 6-7. Data Extraction + RoB

Per-arm counts for biochemical response + RR/OR, ALP normalisation, pruritus (5D-itch, PBC-40), liver stiffness (FibroScan), liver-related events. Safety: GI AEs, hepatotoxicity (ALT/AST), creatine kinase, myalgia. RoB 2 LOW across D1-D5 for both trials (central IVR, double-blind matched placebo, central laboratory, SAP locked). Author sign-off per provisional-RoB banner.

---

## 8. Synthesis / Statistical Methods

- DerSimonian-Laird random-effects IVW on log-RR scale (biochemical response).
- HKSJ t-df=k-1 with `max(1, Q/(k-1))` floor.
- At k=2, FE-IVW sensitivity per CART-MM SAP.
- PI suppressed at k<3.
- Subgroup: baseline ALP severity (>=3x ULN vs <3x ULN), pre-existing cirrhosis status, UDCA continuation.
- Sensitivity: ALP normalisation as consistency check; exclude UDCA-intolerant subset as sensitivity.
- Bayesian half-normal(0, 1.0) prior on tau (log-RR scale).
- Browser-hosted WebR cross-validation (optional, user-triggered).

---

## 9-10. GRADE / Reporting

Standard GRADE. ELATIVE and RESPONSE use the same composite primary biochemical response endpoint at 52 weeks / 12 months — direct. Both positive with concordant direction. Class-level PPAR modulator pool is the estimand; elafibranor (PPARalpha/delta) and seladelpar (PPARdelta) have distinct receptor selectivity profiles — pre-specified indirectness downgrade for the pooled class effect. Long-term hard endpoints (liver-related death, transplant) not yet powered. PRISMA 2020, CONSORT-Harms.

---

## 11. Living-MA Update Cadence

Formal 3-monthly cadence. Triggers: ELATIVE open-label extension + long-term clinical outcomes, RESPONSE long-term open-label, ongoing pivotal for bezafibrate (BEZURSO-2) and obeticholic acid (COBALT confirmatory), next-generation FXR agonists (cilofexor), ileal-bile-acid-transporter inhibitors (linerixibat PILLAR).

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
| 13 | RoB in interpretation | Partial | GRADE §9, class-level PPAR indirectness noted |
| 15 | Publication bias | Yes (k-appropriate) | k=2, formal tests suppressed |
| 1 | PICO | Yes | §2 |

---

## Changelog
- **v1.1** (2026-04-20) — Initial editor-review-revision release.
