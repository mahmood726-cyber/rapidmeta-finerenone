<!-- sentinel:skip-file - audit findings / operator notes -->
# Portfolio citation sweep — findings (2026-06-09)

Triggered while resolving the 2 flagged citations (PREDIMED-Plus, TRACT). User
asked to sweep other dashboards for fabricated rows before deciding. The sweep
grew the picture well beyond the original 2 — summarised here for a decision.

## Method
- Extracted every DOI across 1521 `*_REVIEW.html` (714 unique; fixed a regex bug
  that truncated Lancet/Elsevier PII DOIs like `S0140-6736(24)00822-0`).
- Resolved all 714 via NCBI esearch `[AID]`; 35 didn't match.
- Re-checked those 35 at the **DOI Handle registry (doi.org)** — authoritative for
  "does this DOI exist": 3 are real-but-PubMed-unindexed (e.g. `10.18637/jss…` =
  the metafor R package), **32 are NOT registered** (don't exist).
- For each unregistered-DOI row, resolved the trial's PMID to classify.

## Severity tiers

### Tier 0 — FABRICATED trial row (pollutes the meta-analysis). **1 confirmed.**
- **MEDITERRANEAN_DIET_CV / PREDIMED-Plus** — realData pmid `38924767` → a perinatal
  paper; DOI `10.1016/S0140-6736(24)00822-0` unregistered; no PREDIMED-Plus paper
  exists in Lancet (PubMed search = 0). Event counts `tE:295/tN:3438, cE:354/cN:3436`
  have no source. **No real paper → invented data.** (Decision still pending.)

### Tier 1 — WRONG realData PMID on a REAL trial (pool uses a wrong-paper pmid).
Same class as the 15 already fixed (often off-by-one/transposition). The prior
`audit_citation_consistency.py` run did NOT catch these — so its "clean" result
was not comprehensive.
- **PEDIATRIC_HIV_ART / ARROW** — realData pmid `23541054` → "Health law and policy
  in the EU" (not the real ARROW Lancet 2013 trial). Trial is real; pmid is wrong.
- (Likely more exist — a proper re-audit of all 1103 realData pmids is needed to
  enumerate Tier-1 fully; the DOI sweep only surfaces rows that also had a DOI.)

### Tier 2 — WRONG DOI string on a REAL trial, correct PMID (cosmetic; pool OK).
~21 rows. The realData pmid is correct and matches the trial; only the DOI *string*
is wrong/non-existent. Does NOT affect any pooled estimate. Examples (dash DOI →
real DOI):
- ABLATION_AF / RAFT-AF: pmid 35313733 OK; DOI `10.1056/nejmoa2204164` → real
  `10.1161/CIRCULATIONAHA.121.057095`
- ARNI_HF / PARAGON-HF: pmid 31475794 OK; `…nejmoa1901907` → `…NEJMoa1908655`
- ATTR_CM / APOLLO-B: pmid 37888916 OK; `…circulationaha.123.066353` → `…NEJMoa2300757`
- AFICAMTEN_HCM / SEQUOIA-HCM, HIFPH / PRO2TECT+INNO2VATE, BEMPEDOIC / CLEAR Serenity,
  ENSIFENTRINE / ENHANCE-1, DELANDISTROGENE / EMBARK, ATTR_PN / HELIOS-A,
  RENAL_DENERV / REQUIRE, MAVACAMTEN / MAVA-LTE, AGYW / FACTS-001, PRIMAQUINE /
  SAFEPRIM, CABOTEGRAVIR / FLAIR … (full list in `_baddoi_classified.json`).

### Tier 3 — WRONG PMID in a REFERENCES/prose block only (not realData; cosmetic).
- PPH_BUNDLE / WOMAN-2 (pmid 37499666 → Arctic phenology), HPV / DoRIS (36410354 →
  breast-cancer screening), DIABETIC_RETINOPATHY / Protocol-W (34727134 → substance
  misuse). The poolable realData pmid is elsewhere/not this value.

### Plus oncology rows where the realData pmid points to a drug-related-but-wrong paper
- MM_1L / IMROZ pmid `38573925` → an isatuximab *assay* paper (not the IMROZ trial);
  HER2_LOW_ADC / DESTINY-Breast06 pmid `37499870` → a T-DXd review. Need Tier-1
  treatment (find correct pmid).

## Bottom line
- **Only PREDIMED-Plus is a fabricated-data row** (Tier 0). That is the one that
  pollutes a meta-analysis.
- Tiers 2–3 are citation-quality defects (wrong DOI/ref strings on real trials) —
  they don't change any pooled number, but they are wrong and should be cleaned.
- **Tier 1 is the concerning discovery**: the prior PMID audit was not comprehensive
  (ARROW slipped through), so an unknown number of realData rows carry wrong PMIDs.
  A full re-audit of all 1103 realData pmids (resolve each, compare journal/year/
  author/pages to the snippet) is the only way to enumerate them.

## Update 2026-06-09 — Tier-0 done; full re-audit needs the TUNED tool

- **Tier 0 DONE:** PREDIMED-Plus removed entirely (`remove_predimedplus_fabricated.py`).
- **Full realData PMID re-audit — homegrown attempt FAILED (too noisy).** A from-scratch
  re-audit (`comprehensive_pmid_reaudit.py`, since deleted) flagged 1493/1504 rows
  (AUTHOR 1454, TOPIC 1223, YEAR 707) — ~99% false positives, because acronym trial
  names ("DAPA-HF") share no word with the paper title ("Dapagliflozin in Heart
  Failure"), and realData `year:` (trial/completion year) routinely differs from the
  PMID publication year. Mass-editing on this signal would corrupt correct rows, so
  it was discarded (no edits made from it).
- **Correct path for the comprehensive Tier-1 sweep:** run the EXISTING tuned
  `scripts/audit_citation_consistency.py` (its AUTHOR precision + accent-normalisation
  were hardened on 2026-06-09), review ALL issues (not just >=2-class HIGH-CONF — that
  threshold is what let single-class wrong-PMIDs like ARROW slip through), and
  PubMed-verify + fix each genuine wrong-PMID individually via `fix_wrong_pmids.py`.
  This is a careful multi-step effort, recommended as a focused follow-up rather than
  an automated blast. Confirmed Tier-1 example still open: PEDIATRIC_HIV_ART / ARROW
  (realData pmid 23541054 -> "Health law in the EU"; needs the real ARROW pmid).
- **Tier 2 (wrong DOI strings) and Tier 3 (reference-only wrong PMIDs)** are cosmetic
  (do not change any pooled estimate) and remain a backlog; real DOIs for the Tier-2
  rows are in `_baddoi_classified.json`.

## Artifacts
- `outputs/_all_dois.json`, `_doi_resolution.json`, `_doi_fabrication_verdict.json`,
  `_baddoi_classified.json` — raw sweep data.
- Verifier scripts: `scripts/_extract_all_dois.py`, `_resolve_dois.py`,
  `_verify_dois_doiorg.py`, `_classify_baddoi_rows.py`, `_check_nopmid_refs.py`.
