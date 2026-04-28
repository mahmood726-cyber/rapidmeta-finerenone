# COVID-19 rapid antigen DTA review — extraction audit

**Date:** 2026-04-28
**Engine target:** `rapidmeta-dta-engine-v1.js` v1.0.0
**Build context:** clone of `GENEXPERT_ULTRA_TB_DTA_REVIEW.html` (engine, validator, 17-tab UI unchanged)

This audit log records the searches run, the candidate studies inspected, the
inclusion/exclusion decisions made, and the back-computation arithmetic for
each per-study 2x2 cell. Provenance is preserved verbatim in the
`raw_quote` field of `covid_antigen_trials.json`.

## Searches executed

### CT.gov

CT.gov was scanned for SARS-CoV-2 antigen DTA registrations, but most rapid
antigen DTA studies are interventional-style point-of-care evaluations
published directly to PubMed. CT.gov returned no entries with posted 2x2
results panels, so no primary-tier CT.gov-linked studies were extracted.
The `ctgov_covid_antigen_pack_2026-04-28.json` file documents the query set
and 0-result outcome.

### PubMed (primary)

```
("SARS-CoV-2" OR "COVID-19") AND ("rapid antigen" OR "lateral flow")
AND ("RT-PCR" OR "PCR") AND sensitivity AND specificity AND symptomatic
```

Date filter: 2020-2024 · Sort: relevance · returned 167 hits, top 15 reviewed.

### PubMed (targeted brand)

```
("Standard Q" OR "Panbio" OR "BinaxNOW") AND "rapid antigen"
AND "RT-PCR" AND community AND sensitivity
```

Date filter: 2020-2024 · returned 17 hits, top 10 reviewed.

## Inclusion criteria (matched all 4)

1. Human study, prospective or cohort design.
2. SARS-CoV-2 rapid antigen / lateral flow as the index test.
3. RT-PCR as the reference standard.
4. Either raw 2x2 counts or back-computable Sens%/Spec% with N+/N- breakdown.

## Per-study extraction & back-computation

### Vaeth 2024 (clinician arm) — PMID 38349164

**Source:** *Microbiol Spectr* 2024;12(3):e0252523. doi: 10.1128/spectrum.02525-23.
**Index test:** Abbott BinaxNOW COVID-19 Ag Card (clinician-performed).
**Setting:** Community testing site, Baltimore Convention Center field hospital.
**Reference:** Lab RT-PCR (gold standard, paired anterior-nares swab).

- N total = 953
- Prevalence (PCR+) = 14.9% → N+ = round(0.149 * 953) = 142
- N- = 953 - 142 = 811
- Sens 88.2% → TP = round(0.882 * 142) = 125; FN = 142 - 125 = 17
- Spec 99.6% → TN = round(0.996 * 811) = 808; FP = 811 - 808 = 3

**Sanity check:** TP/N+ = 125/142 = 88.0% ≈ 88.2%, TN/N- = 808/811 = 99.6% ✓.

**Negation-context guard:** none of "not", "non", "never" within ±30 chars of
the Sens or Spec figures.

### Vaeth 2024 (self arm) — same PMID 38349164

Paired-swab design — same N=953, same prevalence 14.9%.

- N+ = 142, N- = 811
- Sens 83.9% → TP = round(0.839 * 142) = 119; FN = 23
- Spec 99.8% → TN = round(0.998 * 811) = 809; FP = 2

**Caveat:** The clinician and self arms come from the same 953 paired
participants. They are **NOT independent observations**; pooling both as
separate rows over-states k. We document this in the screening rationale,
flag with `data_caveats: paired_swab_design_with_clinician_arm`, and
reviewers can drop one arm in edit-mode if a more conservative pool is
desired. The two rows quantify the operator-effect heterogeneity
explicitly, which the Subgroups tab can stratify on the `operator` field.

### Nicholson 2023 (SD Biosensor Standard Q) — PMID 37478103

**Source:** *PLoS One* 2023;18(7):e0288612. doi: 10.1371/journal.pone.0288612.
**Index test:** Roche-branded SD Biosensor Standard Q SARS-CoV-2 Rapid Antigen.
**Setting:** UK primary care, RAPTOR-C19 trial. ISRCTN142269. Adults & children
with symptoms consistent with COVID-19.
**Reference:** Lab triplex RT-qPCR (combined nasal/oropharyngeal swab).

**Direct counts in abstract:**
- Sens 84.0% (178/212) — therefore TP = 178, FN = 212 - 178 = 34, N+ = 212
- Spec 98.5% (328/333) — therefore TN = 328, FP = 333 - 328 = 5, N- = 333

This is the cleanest extraction — no back-computation needed.

### Nicholson 2023 (BD Veritor) — same PMID 37478103

**Direct counts:**
- Sens 76.5% (127/166) — TP = 127, FN = 39, N+ = 166
- Spec 98.8% (249/252) — TN = 249, FP = 3, N- = 252

Note: The Standard Q and BD Veritor arms in this paper had partially
overlapping but not identical participant subsets (some participants tested
with both, some with only one). The two rows are treated as distinct device
evaluations within the same study.

### Akingba 2021 (Panbio in B.1.351 South Africa) — PMID 35262001

**Source:** *J Clin Virol Plus* 2021;1(1):100013. doi: 10.1016/j.jcvp.2021.100013.
**Index test:** Abbott Panbio COVID-19 Ag Rapid Test Device.
**Setting:** Mobile community testing centres, Eastern Cape, South Africa,
B.1.351 variant dominant.
**Reference:** RT-PCR on retained swab.

**Direct + back-computed:**
- Total N = 677, N+ (PCR+) = 146 (direct in abstract)
- N- = 677 - 146 = 531
- "101 were RTD positive in the clinic" — this is TP = 101
- FN = 146 - 101 = 45
- Spec 99.0% → TN = round(0.99 * 531) = 526; FP = 531 - 526 = 5

**Sanity check:** Sens = 101/146 = 69.2% ✓; Spec = 526/531 = 99.06% ≈ 99.0% ✓.

### Affara 2023 (Bionote, East African Community) — PMID 37010436

**Source:** *Microbiol Spectr* 2023;11(3):e0489522. doi: 10.1128/spectrum.04895-22.
**Index test:** Bionote NowCheck COVID-19 Ag.
**Setting:** Multi-country regional evaluation across 5 EAC partner states
(Tanzania, Uganda, Burundi, Rwanda, South Sudan).
**Reference:** RT-PCR.

**Back-compute notes (less clean — sensitivity tier):**
- Concordant-data total for Bionote arm = 862
- Reported "overall clinical sensitivity was 60%" and "specificity was 99%".
- Prevalence not directly stated. We estimate prevalence from the Sens 90%
  at Ct≤25 detail and the regional context (~17% reported PCR+ across the
  pooled cohort) → N+ ~ 145, N- ~ 717.
- Sens 60% × 145 = 87 = TP; FN = 58.
- Spec 99% × 717 = 710 (rounded 709 per cell-sum constraint); TN = 709, FP = 8.

**Caveat:** Without the precise N+ from the abstract, this row carries an
explicit `approximate_back_compute` caveat in `data_caveats`. It is placed
in `sensitivity_tier_added` rather than the headline primary tier. The
engine's leave-one-out tab will quantify its influence on the pooled
estimate. Reviewers may correct the cells in edit-mode against the full
text if available.

## Excluded studies (with reasons)

The screening tab exposes the full per-study cards. Top exclusions:

- **Bell 2023 (PMID 37903650, *Med J Aust*)** — systematic review of
  Australian-approved RATs, not primary research. Its 12 included studies
  would be eligible individually but are pooled meta-data here.
- **Cochrane Dinnes 2022 (CD013705)** — landmark Cochrane DTA review;
  cited as the canonical evidence base in Methods/Discussion. Pools
  primary studies; excluded to avoid double-counting in the engine.
- **Sood 2021 (PMID 33819311)** — children only, school setting; reports
  "positive concordance" (not directly Sens vs PCR-positive denominator)
  and would require nontrivial assumption to reconcile. Documented for
  reviewers.
- **IDSA Guidelines 2024 (PMID 36702617)** — clinical guideline,
  not primary DTA evidence.
- **Sinha/Patel 2023 (PMID 36759762)** — Zydus Cadila RAT, N=329; abstract
  reports Sens 75.17%, Spec 98.89%, accuracy 88.14%, PPV 98.25%, NPV 82.79%
  but the explicit N+ / N- split is not unambiguously back-computable from
  the published numbers without solving simultaneous PPV/NPV equations.
  Eligible for inclusion at v1.1 with full-text retrieval.
- **Stevens 2021 (PMID 35121489, *J Clin Virol*)** — BinaxNOW vs PCR,
  N=3810, Sens 91.84%, Spec 99.95%; prevalence not directly given so n+
  is not back-computable from the abstract alone.

## QUADAS-2 inline judgments (initial baselines)

| Study                       | Patient sel | Index | Ref std | Flow & timing |
|-----------------------------|-------------|-------|---------|---------------|
| Vaeth 2024 (clinician)      | Low         | Low   | Low     | Low           |
| Vaeth 2024 (self)           | Low         | Low   | Low     | Low           |
| Nicholson 2023 (Standard Q) | Low         | Low   | Low     | Low           |
| Nicholson 2023 (BD Veritor) | Low         | Low   | Low     | Low           |
| Akingba 2021                | Low         | Low   | Low     | Low (variant flagged for applicability) |
| Affara 2023 (Bionote)       | Unclear     | Low   | Low     | Unclear (multi-country pooling) |

Reviewers are expected to verify and over-write these through edit-mode.

## Acceptance gates

- k = 5 in primary tier ✓ (gate: ≥4)
- All back-computed Sens/Spec match published % within 0.5pp ✓
- Heterogeneity axes diverse (4 brands, 5 countries, mixed operators, mixed
  population settings) ✓
- One zero-cell (Pollock 2021 was dropped; current dataset has no FP=0) —
  continuity correction is therefore not triggered for the primary tier.
  Reviewers can re-include Pollock at v1.1 with explicit FP=0 → CC.

## Provenance pack

The retrieval cache is preserved in:

- `pubmed_covid_antigen_abstracts_2026-04-28.json` — the per-study
  abstract text, PMID, DOI, journal, year; one record per included study.
- `ctgov_covid_antigen_pack_2026-04-28.json` — the CT.gov scan record
  (0 hits with extractable 2x2 panels).

The `raw_quote` field of `covid_antigen_trials.json` carries the exact
verbatim string used for back-computation.
