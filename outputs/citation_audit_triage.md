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

## Update 2026-06-09 — re-run after minification + 15 fixes applied

Two audit-tool bugs were fixed before this run (dashboards had been
minified to **double-quoted** field literals, e.g. `name:"CASTLE-AF",pmid:"…"`):

1. **Quote-agnostic extraction.** The field/anchor regexes only matched
   single quotes, so extraction returned **0 triples** on the minified
   portfolio. Now backreference the opening quote (value = group `val`).
2. **High-precision AUTHOR_MISMATCH.** `has_any_author_pattern` matched
   journal abbreviations ("N Engl **J** Med" → looked like "Surname I"),
   firing AUTHOR_MISMATCH on ~93% of rows (1408 false positives) against
   the *correct* PMID's real first author. Now requires a genuine author
   list ("et al", "Source: Surname AB", or two "Surname AB, Surname CD").

Also discovered the bulk live run's **44 PMID_NOT_FOUND were all false**
— NCBI rate-limited during the 1101-PMID burst and the script cached the
empty results as null. Purged + refetched slowly → 0 genuine not-found.

Clean numbers (1521 dashboards, 1508 trial-citation rows):

```
                 before fixes   after 15 fixes
rows with issue        31              17
HIGH-CONFIDENCE        20               7
```

**15 wrong-PMID corrections applied** (`scripts/fix_wrong_pmids.py`,
name-anchored + idempotent; each NEW pmid verified against PubMed by
journal+volume+pages+author+title). Several were transposition typos
(ACTA 29539276→29539274, SPYRAL-ON 29803590→29803589). Notably
`29803590` is the *correct* pmid for RADIANCE-HTN SOLO but had been
copied onto SPYRAL HTN-ON MED in the same file — name-anchoring fixed
only the SPYRAL block. Full list with sources is in the codemod's `FIXES`.

**2 genuinely-wrong PMIDs flagged for manual review — RESOLVED 2026-06-09 (PubMed-verified):**
- `SEVERE_PEDIATRIC_FEBRILE_AFRICA / TRACT` — **FIXED** (`fix_wrong_pmids.py`,
  `31314969 → 31365799`). The old pmid was Song Z, *Health Care Spending… Global
  Payment*, NEJM 2019;381:252-263 (DOI 10.1056/NEJMsa1813621) — unrelated. The
  correct paper is Maitland K et al., *Immediate Transfusion in African Children
  with Uncomplicated Severe Anemia* (TRACT), NEJM 2019;381(5):407-419, DOI
  10.1056/NEJMoa1900105, ISRCTN84086586 — which **matches the dashboard's existing
  snippet (pages/DOI/author/registry) exactly**; only the pmid field was wrong.
  Verified two ways: DOI→PMID conversion and citation lookup (page 407 + author
  Maitland) both returned 31365799. JS re-parses clean.
- `MEDITERRANEAN_DIET_CV / PREDIMED-Plus` — **CONFIRMED FABRICATED; NOT auto-fixed
  (needs a data-integrity decision).** The cited paper does not exist in PubMed:
  (a) pmid `38924767` → a perinatal paper (*Accidental uterine extensions…*, J
  Perinat Med 2024, DOI 10.1515/jpm-2024-0077); (b) the cited DOI
  `10.1016/S0140-6736(24)00822-0` resolves to **no** PubMed record; (c) a citation
  lookup for *Lancet 2024;404:1247-1257, Salas-Salvadó* is **NOT_FOUND**; (d) a
  PubMed search returns **zero** PREDIMED-Plus papers in *Lancet* and zero
  Salas-Salvadó PREDIMED-Plus CVD-events papers (2023–2026). PREDIMED-Plus primary
  hard-CVD-endpoint results were not published as cited. The dashboard's event
  counts for this arm (`tE:295/tN:3438, cE:354/cN:3436`) therefore have no source
  and are very likely fabricated too — this is a poolable row in the
  MEDITERRANEAN_DIET_CV NMA, so removing vs. nulling it CHANGES the analysis.
  **RESOLVED 2026-06-09: REMOVED** the trial row entirely (user decision) via
  `scripts/remove_predimedplus_fabricated.py` — deleted the realData entry, the
  canonical AL_IDS id, the nctAcronyms pair, and the cosmetic title strings. The
  MEDITERRANEAN_DIET_CV NMA now pools the 2 real arms (PREDIMED reanalysis +
  CORDIOPREV). JS re-parses clean; 0 residual PREDIMEDPLUS/38924767/00822-0 tokens.
  See outputs/citation_doi_sweep_findings.md for the portfolio-wide sweep this
  triggered.

**5 remaining high-confidence rows are PMID-correct / snippet-wrong**
(the pmid resolves to the right trial; only the descriptive snippet text
or page string is off): PARAGLIDE-HF, HEART-FID, VALOR-HCM, MAVA-LTE,
RADIANCE II. These are snippet-text fixes, not wrong-PMID fixes.

## Suggested next steps (original)

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
