# Citation-consistency audit — portfolio triage 2026-05-01

`scripts/audit_citation_consistency.py` cross-checked every
`(pmid, snippet, sourceUrl)` triple in 170 dashboards against
PubMed E-utilities ESummary. The audit caught the same class of
error that hit `PEGCETACOPLAN_GA` (wrong PMID → wrong author / year
/ pages / journal).

## Headline numbers

```
Total trial-citation rows audited:      549
Unique PMIDs:                           428
Rows with ≥1 issue:                     200 (36%)
HIGH-CONFIDENCE rows (≥2 issue classes): 140 (26%)
Dashboards affected (HIGH-CONF):         88 / 170 (52%)
```

Per-class issue counts (post-refinement):

| Class | n | Meaning |
|---|---:|---|
| AUTHOR_MISMATCH | 171 | Snippet attributes paper to author X; PubMed says first author is Y. Refinements: accent-normalised (`Schüpke` == `Schupke`), only fires when the snippet actually names AN author at all (skips bare "Journal year:pages" snippets). |
| PAGE_MISMATCH | 141 | Snippet pages don't match PubMed pages. |
| YEAR_MISMATCH | 62 | Snippet quotes a 4-digit year different from PubMed's pubdate year. |
| JOURNAL_MISMATCH | 43 | URL host implies journal X (lancet.com/lancet/, nejm.org, jama, etc.); PubMed says paper is in journal Y. |
| PMID_NOT_FOUND | 0 | All PMIDs return *something*. |

## What this means

A row with **≥2 issue classes** is almost certainly a wrong-PMID:
the dashboard's `pmid: 'XXXXXXX'` value points to a paper that is
NOT the one the snippet/URL describes. Two independent signals (e.g.
author mismatch + journal mismatch) almost never both fire for a
right-PMID-with-formatted-snippet case.

Examples of clear wrong-PMIDs caught:

| Dashboard | Trial | Dashboard PMID points to... | Snippet claims |
|---|---|---|---|
| ACALABRUTINIB_CLL | ASCEND | "Yang J 2019 Molecular cancer" | Ghia P JCO 2020 |
| ACORAMIDIS_ATTR_CM | ATTRibute-CM | "Kletskaya I 2024 Am J Dermat" | Gillmore JD NEJM 2024 |
| AFICAMTEN_HCM | SEQUOIA-HCM | "Zhu H 2024 Food chemistry" | Maron MS NEJM 2024 |
| ALDO_SYNTHASE | Target-HTN | "Ng MY 2023 Hong Kong med j" | Laffin LJ JAMA 2023 |
| ALOPECIA_JAKI | ALLEGRO-2b/3 | "Zhan W 2023 Cell chem biol" | King B Lancet 2023 |
| ANTIAMYLOID_AD | EMERGE+ENGAGE | "Salloway S 2022 JAMA neurol" | Budd Haeberlein S J Prev AD 2022 |
| ANTIVEGF_NAMD | VIEW-1/VIEW-2 | "Reichert JM 2011 mAbs" | Heier JS Ophthalmology 2012 |
| ANTI_CD20_MS | ULTIMATE I/II | "PLOS ONE Editors 2022" | Steinman L NEJM 2022 |

These are not formatting issues — these are structurally wrong
PMIDs. A reader pasting the dashboard's PMID into PubMed gets a
totally different paper. Same class as PEGCETACOPLAN_GA pre-fix.

## Top-20 dashboards ranked by HIGH-CONFIDENCE count

```
 5  JAKI_AD_NMA
 4  ANTIVEGF_NAMD_NMA
 4  MIGRAINE_ACUTE_NMA
 3  ALOPECIA_JAKI_NMA
 3  ATOPIC_DERM_NMA
 3  CABOTEGRAVIR_HIV_ART
 3  CBD_SEIZURE
 3  HER2_LOW_ADC_NMA
 3  HIV_LA_PREP_NMA
 3  INCRETIN_HFpEF
 3  PSA_BIOLOGICS_NMA
 3  SPONDYLOARTHRITIS_NMA
 3  TYVAC_TYPHOID
 2  ALDO_SYNTHASE_NMA
 2  ANTI_CD20_MS_NMA
 2  ANTIAMYLOID_AD
 2  AVACINCAPTAD_GA
 2  BTKI_CLL_NMA
 2  CARDIORENAL_DKD_NMA
 2  CD_BIOLOGICS_NMA
```

The full per-dashboard list is in `outputs/citation_audit.csv`.

## Suggested next steps (user decides)

1. **Manual review pass** — open the top-20 dashboards, look at the
   high-confidence rows, confirm they're real wrong-PMIDs.
2. **Auto-correction script** — for each wrong-PMID row, search
   PubMed by `(trial acronym) AND (drug) AND (year-window)` and pick
   the best-matching record. Risky for portfolio scale; better to
   target the obvious cases and let the user confirm each.
3. **Mass triage workflow** — generate a batch of one-trial-per-page
   verification cards (NCT, dashboard claim, PubMed reality, propose
   correct PMID). Cohort users (Makerere, etc.) verify in parallel.

The audit script is now part of the regular reverification pass.
Run after any new dashboard or any PMID edit:

```
python scripts/audit_citation_consistency.py
python scripts/audit_citation_consistency.py --offline   # cache only
```

The 24h-TTL PubMed cache (`outputs/_pubmed_cache.json`) makes
re-runs near-instant.

## Methodology notes

- AUTHOR_MISMATCH suppresses when snippet has no author pattern
  (e.g. bare "Journal year; vol:pages" style). Without this filter
  the audit would over-flag a stylistic choice.
- Accents normalised via NFKD before comparison (`Schüpke` ≈
  `Schupke`).
- YEAR_MISMATCH only fires on POSITIVE evidence: snippet quotes a
  different 4-digit year. Absence of any year doesn't flag.
- JOURNAL_MISMATCH replaces the prior PII_MISMATCH heuristic, which
  was noisy because PubMed's `articleids` returns whatever ID type
  it finds first (PMC ID, NLM ID, DOI), not always the print PII.
- HIGH-CONFIDENCE = ≥2 independent issue classes for the same row.
  This filter cuts false-positive rate dramatically.
