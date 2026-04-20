---
title: "Lenacapavir Twice-Yearly Injection for HIV Pre-Exposure Prophylaxis"
slug: lenacapavir_prep
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Infectious Disease (HIV)
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/lenacapavir_prep_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/LENACAPAVIR_PREP_REVIEW.html
license: MIT
---

# Lenacapavir for HIV Pre-Exposure Prophylaxis (PURPOSE Programme)
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Infectious Disease (HIV)

---

## 1. Review Title and Registration

**Title:** Lenacapavir (Twice-Yearly Subcutaneous Capsid Inhibitor) vs Daily Oral F/TAF or F/TDF for HIV Pre-Exposure Prophylaxis: A Living Systematic Review and Meta-Analysis of the PURPOSE Phase 3 Programme

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding).

**Corresponding address:** drmahmoodclinic@pm.me (GMC 6071047), Royal Free Hospital and Barnet Hospital, London, UK.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults and adolescents >=16 years at high risk of HIV acquisition (cisgender women, cisgender men, transgender and non-binary people who have sex with men) |
| **Intervention** | Lenacapavir 927 mg SC every 26 weeks (after oral loading) |
| **Comparator** | Daily oral F/TDF (Truvada) and/or F/TAF (Descovy) with background-HIV-incidence comparator |
| **Outcome (primary)** | Incident HIV infection over follow-up |

---

## 3. Eligibility / Search / Selection

Inclusion: phase III pivotal, adults/adolescents at high HIV risk, lenacapavir SC Q6M intervention, daily oral F/TDF or F/TAF comparator, HIV incidence primary. Exclusion: phase I/II dose-finding, maternal PrEP, lenacapavir for HIV treatment (CAPELLA). Two-reviewer adjudication; PRISMA 2020.

---

## 6-7. Data Extraction + RoB

Per-arm incident HIV counts, person-years follow-up, injection-visit adherence, integrase resistance, safety (injection-site reactions, grade 3+ AEs). RoB 2 priors: LOW for most domains; D2 SOME CONCERNS (double-blind double-dummy with early DSMB unblinding for overwhelming efficacy). Author sign-off per the provisional-RoB banner.

---

## 8. Synthesis / Statistical Methods

- DerSimonian-Laird random-effects IVW on log-RR scale for HIV incidence.
- HKSJ t-df=k-1 with `max(1, Q/(k-1))` floor.
- At k=2 (PURPOSE-1 + PURPOSE-2), FE-IVW sensitivity pool per CART-MM SAP.
- Zero-cell handling: conditional 0.5 correction. PURPOSE-1 has 0 events in the lenacapavir arm -- warrants Peto-OR sensitivity.
- Subgroup: cisgender women (PURPOSE-1) vs MSM/TGW/non-binary (PURPOSE-2).
- PI suppressed at k<3.
- Bayesian half-normal(0, 0.5) prior on tau.
- Browser-hosted WebR cross-validation (optional, user-triggered).

---

## 9-10. GRADE / Reporting

Standard GRADE domains. Anticipated HIGH certainty given the magnitude of effect (near-100% efficacy in PURPOSE-1) and consistency. No external IPD MA at freeze; app's DL pool is the reference alongside published per-trial rate ratios.

---

## 11. Living-MA Update Cadence

Formal 3-monthly cadence. Triggers: PURPOSE-3 (long-acting islatravir), PURPOSE-4/5 adolescent extensions, real-world effectiveness post-rollout.

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
