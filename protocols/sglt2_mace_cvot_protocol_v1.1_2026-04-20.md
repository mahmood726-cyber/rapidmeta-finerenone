---
title: "SGLT2 Inhibitor CVOT Class Pool for 3P-MACE"
slug: sglt2_mace_cvot
version: 1.1
timestamp: 2026-04-20T00:00:00Z
date: 2026-04-20
specialty: Cardiology (Diabetes)
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/sglt2_mace_cvot_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/SGLT2_MACE_CVOT_REVIEW.html
license: MIT
---

# SGLT2i CVOT Class Pool for 3P-MACE (EMPA-REG / CANVAS / DECLARE / VERTIS-CV)
## A Living Systematic Review and Meta-Analysis Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-20T00:00:00Z
**Specialty:** Cardiology (Diabetes)

---

## 1. Review Title and Registration

**Title:** SGLT2 Inhibitors (Empagliflozin, Canagliflozin, Dapagliflozin, Ertugliflozin) vs Placebo for Three-Point Major Adverse Cardiovascular Events in Type 2 Diabetes: A Living Systematic Review and Meta-Analysis of the Phase 3 Pivotal Cardiovascular Outcome Trials

**Registration:** Protocol frozen 2026-04-20T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding). Corresponding address: drmahmoodclinic@pm.me.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with type 2 diabetes and established CVD (secondary-prevention-only) or mixed primary/secondary prevention with CV risk factors |
| **Intervention** | SGLT2 inhibitor (empagliflozin, canagliflozin, dapagliflozin, or ertugliflozin) |
| **Comparator** | Matched placebo on top of standard of care |
| **Outcome (primary)** | 3P-MACE (CV death, non-fatal MI, non-fatal stroke); hazard ratio |

---

## 3. Eligibility / Search / Selection

Inclusion: phase III pivotal CVOT, adults with T2D, SGLT2 inhibitor vs placebo, 3P-MACE as primary or co-primary endpoint. Exclusion: phase II dose-finding, SGLT2i HF-specific trials (SGLT2_HF separate app), SGLT2i CKD-specific trials (SGLT2_CKD separate app), non-CVOT glycaemic-control studies, sotagliflozin (dual SGLT1/2 mechanistically distinct - SOTAGLIFLOZIN_HF separate app). Two-reviewer adjudication; PRISMA 2020.

---

## 6-7. Data Extraction + RoB

Per-arm 3P-MACE event counts + HR on log-hazard scale, CV death, HF hospitalisation, renal composite, all-cause mortality. Safety: genital mycotic infections, DKA, volume depletion, amputation (canagliflozin signal), fracture, Fournier gangrene. RoB 2 LOW across D1-D5 for EMPA-REG / DECLARE / VERTIS-CV. CANVAS Program D5 SOME CONCERNS (CANVAS + CANVAS-R integrated post-hoc per pre-specified SAP; amputation signal flagged post-publication). Author sign-off per provisional-RoB banner.

---

## 8. Synthesis / Statistical Methods

- DerSimonian-Laird random-effects IVW on log-HR scale (3P-MACE).
- HKSJ t-df=k-1 with `max(1, Q/(k-1))` floor.
- At k=4, prediction interval computable.
- Subgroup: established-CVD-only vs mixed primary/secondary-prevention populations; agent-specific within-class subgroups.
- Sensitivity: HF hospitalisation pool as consistency check (class effect more pronounced on HF than MACE).
- Bayesian half-normal(0, 0.3) prior on tau (log-HR scale).
- Browser-hosted WebR cross-validation (optional, user-triggered).

---

## 9-10. GRADE / Reporting

Standard GRADE. Class-level pool across 4 SGLT2 inhibitors is the estimand; DECLARE and VERTIS-CV individually failed 3P-MACE superiority but class-level pool confirms modest MACE reduction (~9%). Population heterogeneity (secondary-only EMPA-REG/VERTIS vs mixed CANVAS/DECLARE) is a pre-specified indirectness factor. HF hospitalisation benefit is more pronounced and consistent across agents. Reference: Zelniker 2019 Lancet class-level meta-analysis reports pooled HR 0.89. PRISMA 2020, CONSORT-Harms.

---

## 11. Living-MA Update Cadence

Formal 3-monthly cadence. Triggers: post-hoc CVOT follow-up extensions, any new SGLT2i CVOT (unlikely within current pipeline), dapa-MI / EMPACT-MI post-MI class expansion, SGLT2i + finerenone combination CV outcomes.

---

## 12-14

Aggregate-data only. No competing interests, no funding.

---

## Appendix A. AMSTAR-2 Critical-Domain Self-Assessment

| # | Domain | Self-rating | Evidence |
|---|---|---|---|
| 2 | Registered protocol | Yes (partial) | GitHub-canonical-URL freeze |
| 4 | Search strategy | Yes | §4 |
| 7 | Excluded-studies list | Yes | Screening tab (HF-specific / CKD-specific / phase II explicitly excluded) |
| 9 | RoB assessment | Yes | Authors have double-checked screening and data extraction against the record excerpts shown in the Extraction tab; provisional AI-drafted RoB-2 is now author-confirmed. Formal dual-assessor RoB-2 remains a per-submission step. |
| 11 | Statistical methods | Yes | §8 |
| 13 | RoB in interpretation | Partial | GRADE §9, population-mix indirectness noted |
| 15 | Publication bias | Yes | k=4, Egger radial test included; funnel plot visually inspected |
| 1 | PICO | Yes | §2 |

---

## Changelog
- **v1.1** (2026-04-20) — Initial editor-review-revision release.

## Amendment 1 -- 2026-08-28 -- five-source search executed under this protocol

**This protocol governs the search for topic `sglt2-mace-cvot-review`. It is amended here, not replaced.**

Under Mahmood's ruling of 2026-08-28, an auto-generated protocol specifies nothing --
1,093 of them share a single byte-identical statistical-methods text -- and so cannot
govern a search. This file is **not** one of those 1,093, so it governs, and a draft
written later does not displace it.

**What is being done under it.** A search of five sources -- PubMed, Europe PMC,
ClinicalTrials.gov, an ICTRP route (ISRCTN), and guideline bodies as a source class --
executed on 2026-08-28, recorded in `ssot/sglt2-mace-cvot-review/SEARCH-RECORD.json`, with each source
carrying one of exactly three outcomes: EXECUTED, EMPTY, or FAILED. A non-200 is FAILED
and never carries a record count of zero.

**Ordering.** This file is committed and anchored in a public transparency log before the
first query for this topic is attempted, and the search record is anchored after it. Two
times supplied by a third party bracket the operation. The git commit timestamp is not
one of them: both dates on a git commit are supplied by whoever makes the commit and are
forgeable, which was demonstrated rather than assumed.

**What this protocol does not specify, stated so the record is not read as stronger than
it is.** Its substantive methods prose is shared with up to 40 other protocols in this
repository, including analysis-constraining statements such as the HKSJ variance-inflation
floor `max(1, Q/(k-1))`. It is a house-standard document with topic-specific headers, not
an individually reasoned protocol. It governs because it is not one of the 1,093 AUTO
templates -- which is the test the ruling set, and a lower bar than "bespoke".

**Guideline coverage is a fraction, never a checkmark.** GIN lists 136 bodies. The search
record states how many were queried, how many were reached and refused by a named
obstacle, and how many were never resolved to a queryable endpoint. "All guideline
bodies" is not a claim this search supports.

## Amendment 2 -- 2026-08-29 -- the executed query was malformed; disclosed, corrected, and BOTH results published

**This amendment is written and committed BEFORE the corrected query is run.** That
ordering is the entire point of registering a protocol first, and this is the first
occasion in this project where it pays out rather than merely being defensible.

### The defect

The search executed under Amendment 1 derived its query from this topic's `title`. That is
sound only when the title is a review question. **This title is not a title.** It is four
ClinicalTrials.gov outcome-measure strings concatenated with `|`:

> *Multiple trial-declared outcomes: Time to the First Occurrence of Any of the Following
> Adjudicated Components of the Primary Composite Endpoint (3-point M | Major Adverse
> Cardiovascular Events (MACE) Composite of Cardiovascular (CV) Death, Non-Fatal Myocardial
> Infarction (MI), | Subjects Included in the Composite Endpoint of CV Death, MI or
> Ischemic Stroke | Time to First Occurrence of MACE ...*

Truncated to its first four usable words, the query actually sent was:

> **`Multiple trial-declared outcomes Time`**

### The result it produced, recorded rather than discarded

| source | outcome | n |
|---|---|---|
| PubMed | EXECUTED | **78,608** |
| Europe PMC | EXECUTED | **125,695** |
| ClinicalTrials.gov | EXECUTED | 22 |
| ISRCTN | EXECUTED | 42 |

**Every source returned EXECUTED.** Nothing failed, nothing was empty, and the three-count
law recorded a clean row. The counts are of generic English words and mean nothing about
SGLT2 inhibitors, but *the record could not tell the difference* -- which is the finding,
not the numbers.

**AN EXECUTED SEARCH IS NOT A VALID ONE.** A query that runs and returns a number is
indistinguishable, in the record, from a query that means something. This sits beside
*a 200 is not a document* and *a 000 is not a paywall*.

### The corrected query, stated here before it is executed

> **`SGLT2 inhibitor major adverse cardiovascular events`**

**Derived from the topic's declared scope and its own trials, NOT from its title** -- the
slug names SGLT2, MACE and CVOT, and the two trials held are EMPA-REG OUTCOME
(`NCT01131676`, empagliflozin) and DECLARE-TIMI 58 (`NCT01730534`, dapagliflozin). The
derivation is written down so that it can be disagreed with, and so that it is fixed before
any count from it is seen.

### What is NOT done, and why it matters more than what is

**The original result is not replaced, overwritten, or removed.** Both searches will stand
side by side in `SEARCH-RECORD.json`, each with its own query, timestamps and counts.

Changing a search strategy *after seeing its result* is the defect a registered protocol
exists to prevent. Changing it after **disclosing** that result is method. The difference
between the two is not the change -- it is the disclosure, and this amendment is the
disclosure.

### Ordering, unchanged

The governing protocol was committed and anchored before the original search
(anchored 2026-08-28T23:01:31Z). This amendment is committed before the corrected search.
No search precedes its own registration; the corrected search is a **declared re-run under
an amended protocol**, not a fresh registration, and it must never be reported as
prospective with respect to the trials this topic already holds.
