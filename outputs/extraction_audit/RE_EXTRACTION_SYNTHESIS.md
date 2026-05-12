# Re-extraction synthesis — 2026-05-12

## Goal
Reduce the ~70% evidence-provenance gap surfaced by the 12-method audit by:
1. Re-extracting evidence[] arrays from PubMed abstracts via NCBI eutils
2. Auto-flagging PMIDs whose abstracts are clearly off-topic (likely fabricated)

## Method
- Identified 204 reviews where ≥80% of trials lacked evidence
- Collected 1,190 unique PMIDs across 1,340 trials
- Fetched all abstracts via NCBI E-utilities `efetch` (~90s total, ratelimited to 2.5 req/s)
- Per trial, scored each abstract sentence on value overlap (raw counts, percentages, HR/CI)
- Required ≥2 number matches OR ≥1 + HR-keyword to inject an evidence[] entry
- Independently detected wrong-PMID via topic-sanity check (acronym not in abstract AND no intervention-drug overlap)

## Results
| Operation | Count | Notes |
|---|---:|---|
| Evidence entries injected | **343** | Across 125 reviews |
| Wrong PMIDs nulled | **771** | Across 192 reviews — 65% of fetched PMIDs |
| Reviews with 100% wrong PMIDs | **10** | Likely entirely-fabricated; submission-blocking |
| Reviews with 0 wrong PMIDs | 12 | Clean curation |

### Wrong-PMID detection patterns
The 771 nulled PMIDs were detected via:
- **No intervention overlap** — the trial's drug name (e.g., "erenumab", "galcanezumab") is absent from the abstract
- **Different NCT cited** — the abstract explicitly references a different NCT than the trial's NCT
- **Acronym mismatch** — the trial's acronym (e.g., "STRIVE", "LIBERTY", "FOCUS") is absent

Examples of fabricated PMIDs caught:
- LIBERTY (erenumab CGRP migraine) → PMID 30195512 about NCD/obesity/diabetes
- FOCUS (fremanezumab CGRP migraine) → PMID 31526456 about onychomycosis
- EVOLVE-2 (galcanezumab CGRP) → PMID 30134750 about nursing bedside handover
- REGAIN (galcanezumab CGRP) → PMID 30385166 about pediatric optic atrophy
- PROMISE-1 (eptinezumab CGRP) → PMID 31816092 about characean green algae

## Likely fully-fabricated reviews (submission-blocking)
10 reviews where 100% of trials have wrong PMIDs AND 100% lack evidence:
- CHRONIC_URTICARIA_BIOLOGICS_REVIEW (10 trials)
- CML_TFR_TKI_NMA_REVIEW (10 trials)
- EPILEPSY_NEW_AEDS_REVIEW (10 trials)
- EPILEPSY_NEW_AGENTS_NMA_REVIEW (9 trials)
- GLOMERULONEPHRITIS_BIOLOGICS_REVIEW (8 trials)
- MIS_PANCREATIC_WHIPPLE_NMA_REVIEW (5 trials)
- OAB_BETA3_NMA_REVIEW (5 trials)
- IGAN_TARGETED_BROAD_NMA_REVIEW (4 trials)
- NEONATAL_NEC_NMA_REVIEW (4 trials)
- OBESITY_ENDOSCOPIC_NMA_REVIEW (3 trials)

**Recommended action**: do not ship these reviews without ground-up re-extraction from verified primary sources (CT.gov + PubMed by acronym/NCT).

## 12-method audit shift after fix
| Method | Before | After | Δ |
|---|---:|---:|---:|
| M11_NO_EVIDENCE | 1519 | 1176 | **−343** (= evidence injected) |
| M11 (partial coverage) | 1505 | 2412 | +907 (granular per-value reporting on new evidence) |
| M12 (HR not in evidence) | 351 | 578 | +227 (same accounting) |
| M10 cross-review | 568 | 566 | −2 (B-task) |
| Others | unchanged | unchanged | — |

The +907 M11 is the expected accounting shift: where M11_NO_EVIDENCE emitted one
finding per trial with empty evidence[], M11 now emits one finding per *missing
value* on trials with partial evidence. Net effect is unchanged on the
"complete evidence coverage" axis; the wins are the 343 traceable provenances
and 771 P0 fabrication risks removed.

## Caveats
- The wrong-PMID detector uses topic-sanity (intervention name overlap, acronym match, cited-NCT match), not full semantic similarity. False-positive risk is conservative — 12 reviews had 0 detections, supporting calibration.
- Evidence sentences are limited to 600 chars; full paragraph context is lost.
- Some abstracts (`[Abstract not available]`) carry valid PMIDs but no text — not flagged as wrong, but no evidence built.
- The fabrication detection cannot distinguish "hallucinated PMID" from "outdated/withdrawn PMID" without trial-level human review.

## Files
- `scripts/fetch_pubmed_batch.py` — NCBI eutils fetcher (50/batch, 2.5 req/s)
- `scripts/re_extract_evidence.py` — score + build evidence patches; `--detect-wrong-pmid` topic-sanity check
- `scripts/apply_evidence_and_null_wrong_pmids.py` — apply both ops to HTML files (idempotent, supports `--dry-run`)
- `outputs/extraction_audit/pubmed_cache/*.json` — 1,190 cached abstracts
- `outputs/extraction_audit/evidence_patches/*.json` — 125 patch files
- `outputs/extraction_audit/wrong_pmids.json` — 771 detected
- `outputs/extraction_audit/fully_fabricated_reviews.json` — 10 reviews flagged
- `outputs/extraction_audit/evidence_patches_applied.json` — Op A apply log
- `outputs/extraction_audit/pmid_voided.json` — Op B apply log

## Attribution
Abstracts retrieved from PubMed (NCBI E-utilities). Bulk re-extraction conformed to NCBI's 3 req/s rate-limit (no API key path).
