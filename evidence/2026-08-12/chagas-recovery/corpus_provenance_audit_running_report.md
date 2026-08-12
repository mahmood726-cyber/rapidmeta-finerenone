# Corpus provenance audit — running report #1

**Started:** 12 August 2026
**Trigger:** the Li 2019 finding — Reyaz 2023's characteristics table got the comparator *and* the follow-up wrong, and pooled a benazepril-controlled trial into a sacubitril/valsartan-vs-enalapril analysis. Hypothesis under test: **a published synthesis's characteristics table is an unverified source tier, and the corpus has inherited rows from such tables.**
**Access:** read-only mount of `F:\rapidmeta-finerenone`. **Nothing written to the repo.** All output is in this scratchpad.
**Status:** RUNNING. 4 rows verified of 3,656. This is report #1, not a conclusion.

---

## 1. Headline

Three findings, in order of importance:

1. **The hypothesis as stated is largely NOT confirmed.** Synthesis-derived provenance is rare in this corpus: **3 evidence entries out of 3,389 (0.09%)**, across 3 trial rows in 2 apps. The `prior_meta` tier label does not exist anywhere in the corpus. Reyaz 2023 and Li 2019 are not in the corpus at all. **Prior metas are not a widespread contaminant here.**

2. **But all 3 of those rows are wrong**, and 2 of the 3 are wrong in exactly the way Reyaz was — **the trial is not the trial the row says it is.** Wrong intervention, wrong design, wrong sample size. One row describes a pembrolizumab single-arm study that is actually a randomised nivolumab/ipilimumab/relatlimab trial.

3. **A larger exposure class exists that the brief did not anticipate.** **1,189 of 3,656 trial rows (32.5%) carry no evidence block at all.** Of the 1,870 rows carrying a `publishedHR`, **1,044 (55.8%) have no evidence block**. A further 1,447 of 3,389 evidence entries carry no `sourceUrl`. Unsourced rows outnumber synthesis-sourced rows by roughly **400 to 1**. If the concern is "cells whose provenance cannot be checked", this is where the corpus's actual exposure lives.

---

## 2. Exposure enumeration

Scope: `outputs/extraction_audit/data/*.json`, the structured extraction records behind the review apps.

| Quantity | Count |
|---|---|
| Extraction-audit data files | 1,034 |
| Apps with trial data (`realData`) | 1,006 |
| **Trial rows** | **3,656** |
| Evidence entries | 3,389 |
| Rows with ≥1 evidence entry | 2,467 (67.5%) |
| Rows with ≥1 verbatim evidence `text` | 2,467 (67.5%) |
| **Rows with NO evidence block** | **1,189 (32.5%)** |
| Rows carrying a `publishedHR` | 1,870 |
| — of those, with NO evidence block | **1,044 (55.8%)** |
| Evidence entries with a `sourceUrl` | 1,942 |
| Evidence entries with NO `sourceUrl` | 1,447 |

### Provenance vocabulary — the brief's assumption corrected

The brief asked for "the `prior_meta` tier and anything equivalent". **`prior_meta`, `prior-meta` and `priorMeta` return zero files across the entire repo.** The corpus does not use a tier-label model.

The actual provenance model is per-evidence-entry:

```
evidence: [ { label, source, sourceUrl, text, highlights } ]
```

Provenance is judged by what `source`/`sourceUrl` point at, not by a tier field. So the enumeration had to be done by classifying source targets.

### Evidence source domains

| Count | Domain |
|---|---|
| 1,538 | clinicaltrials.gov |
| 339 | doi.org |
| 34 | www.nejm.org |
| 11 | www.ncbi.nlm.nih.gov |
| 9 | www.thelancet.com |
| 3 | jamanetwork.com |
| 3 | pubmed.ncbi.nlm.nih.gov |
| 1 each | ascopubs.org, onlinelibrary.wiley.com, academic.oup.com, jacc.org, ahajournals.org |

### Synthesis-derived provenance — the exposure the brief targeted

Pattern-matched `meta-analys|systematic review|pooled analysis|cochrane|network meta|umbrella|cureus` across every evidence `source`, `sourceUrl` and `label`.

**Result: 3 entries. 0.09% of all evidence entries.** All three name a Cochrane systematic review as the source of a trial's outcome.

**Reyaz 2023 / Li 2019 are absent from the corpus.** Searches for `Reyaz|48623|38084196|10710849` returned two files, both **coincidental substring matches**: an author surname "Reyazur" and a Retraction Watch record ID "48623" in a bundled third-party CSV. Verified by reading the matching lines. The seed case is not represented here — it presumably lives on the other machine or in a working file outside this repo.

---

## 3. Rows verified at primary

Protocol: check the four fields that silently invalidate a pool — **comparator/intervention, population, outcome definition, reported quantity** — against ClinicalTrials.gov or the trial's own publication. Never against another synthesis. Identifiers resolved by live lookup.

### 3.1 — WRONG (identity): `MELANOMA_NEOADJUVANT_REVIEW.json` / NCT02519322

| Field | Corpus row | Primary source | Verdict |
|---|---|---|---|
| Trial name | "IMmuNED" | "Neoadjuvant and Adjuvant Checkpoint Blockade" (no acronym) | **WRONG** |
| Sponsor | — | M.D. Anderson Cancer Center + NCI | — |
| **Intervention** | "Pembro neoadj single-arm" | **Ipilimumab, Nivolumab, Relatlimab** — no pembrolizumab | **WRONG** |
| **Design** | single-arm | **Randomised Phase 2, 3 arms (A/B/C)** | **WRONG** |
| **n** | tN 30 | **53** enrolled | **WRONG** |
| Outcome | "pCR/MPR rate", RR 0.466 (0.30–0.62) | Primary: Arm C pathologic response rate | unverifiable against a row this misidentified |
| Evidence `source` | Cochrane CD012974.pub2 | quote is about **dabrafenib+trametinib OS/TTR in 21 participants** — unrelated to the row's pCR datum | **WRONG** |

Pointer: `https://clinicaltrials.gov/study/NCT02519322`, read 12 Aug 2026.
**This is the Reyaz class**: a trial pooled under an intervention it does not use.

### 3.2 — WRONG (identity): `MELANOMA_NEOADJUVANT_REVIEW.json` / NCT02437279

| Field | Corpus row | Primary source | Verdict |
|---|---|---|---|
| Trial name | "OPTIMUS-1" | **OpACIN** | **WRONG** |
| Sponsor | — | The Netherlands Cancer Institute | — |
| Design | "Ipi+nivo personalized dosing" | **Phase 1b feasibility**, randomised 2-arm (adjuvant vs split neoadjuvant/adjuvant) | **WRONG** |
| **n** | tN 30 | **20** (10 per arm) | **WRONG** |
| Year | 2023 | study 2016-11-24 → 2018-06-28 | **WRONG** |
| Outcome | "pCR with reduced ipi dose", RR 0.40 (0.25–0.55) | Primary outcomes are **neo-antigen T-cell response, safety (SUSARs), feasibility** — no pCR primary | **WRONG** |
| Evidence `source` | Cochrane CD012974.pub2 | same unrelated dabrafenib/trametinib quote, pasted identically onto two different trials | **WRONG** |

Pointer: `https://clinicaltrials.gov/study/NCT02437279`, read 12 Aug 2026.

### 3.3 — MIXED: `DAPT_DE_ESCALATION_PCI_REVIEW.json` / NCT03971500

| Field | Corpus row | Primary source | Verdict |
|---|---|---|---|
| Trial name | ULTIMATE-DAPT | "1-month vs 12-month DAPT for ACS Patients Who Underwent PCI Stratified by IVUS: IVUS-ACS and **ULTIMATE-DAPT** Trials" | **CORRECT** |
| Sponsor | — | Nanjing First Hospital, Nanjing Medical University | — |
| n | tN 1751 / cN 1754 (=3505) | 3710 enrolled (2×2 factorial with IVUS-ACS) | **plausible** — randomised DAPT subset; not yet confirmed against the publication |
| Outcome | BARC 2/3/5 bleeding 1–12 mo, HR 0.45 (0.30–0.66) | not yet checked against the primary publication | **pending** |
| Evidence `source` | Cochrane **CD003451.pub3** | quote is about **non-surgical orthodontic treatment, overjet and ANB angle** | **WRONG — entirely unrelated field of medicine** |

Pointer: `https://clinicaltrials.gov/study/NCT03971500`, read 12 Aug 2026.
**Trial identity correct; provenance fabricated.** The numbers may well be right — but the evidence block asserting they came from somewhere is worthless, and it *looks* authoritative.

### 3.4 — CORRECT, every checkable cell: `ARNI_HF_REVIEW.json` / NCT01035255

Included deliberately as a confirmation case.

| Cell | Corpus row | NEJM abstract (PMID 25176015) | Verdict |
|---|---|---|---|
| Trial | PARADIGM-HF | "PARADIGM-HF ClinicalTrials.gov number, **NCT01035255**" | **CORRECT** |
| pmid | 25176015 | resolves to *Angiotensin-neprilysin inhibition versus enalapril in heart failure*, N Engl J Med 2014;371(11):993–1004 | **CORRECT** |
| n | 8442 | "8442 patients" | **CORRECT** |
| Primary tE / cE | 914 / 1117 | "914 patients (21.8%) … 1117 patients (26.5%)" | **CORRECT** |
| Primary HR | 0.80 (0.73–0.87) | "hazard ratio … 0.80; 95% CI, 0.73 to 0.87" | **CORRECT** |
| CV death tE / cE | 558 / 693 | "558 (13.3%) and 693 (16.5%)" | **CORRECT** |
| CV death HR | 0.80 (0.71–0.89) | "hazard ratio, 0.80; 95% CI, 0.71 to 0.89" | **CORRECT** |
| ACM tE / cE | 711 / 835 | "711 patients (17.0%) … 835 patients (19.8%)" | **CORRECT** |
| ACM HR | 0.84 (0.76–0.93) | "hazard ratio for death from any cause, 0.84; 95% CI, 0.76 to 0.93" | **CORRECT** |
| Comparator | enalapril | enalapril 10 mg twice daily | **CORRECT** |
| Population | HFrEF, LVEF ≤40% | "class II, III, or IV heart failure and an ejection fraction of 40% or less" | **CORRECT** |
| Evidence `text` | quote of the primary result | matches the abstract verbatim | **CORRECT** |

Not checkable from the abstract: baseline `lvef` 29.6, `age` 63.8, `female` 21.0, `dm` 34.7, and arm sizes 4187/4212 (consistent with the reported percentages but not stated). Would need the paper's Table 1.

**Side benefit:** this resolves, by live lookup, the PARADIGM-HF NCT I deliberately left blank in the Li memo. It is **NCT01035255**, stated in the trial's own abstract.

---

## 4. Root cause — mechanistic, and generalisable

**ClinicalTrials.gov auto-links PubMed publications to trial records, and explicitly warns they "may or may not be about the study."**

NCT02437279's record carries, under *Publications → From PubMed*, this entry:

> Gorry C, et al. **Neoadjuvant treatment for stage III and IV cutaneous melanoma. Cochrane Database Syst Rev. 2023 Jan 17;1(1):CD012974. doi: 10.1002/14651858.CD012974.pub2.**

That is **exactly** the DOI appearing as the evidence `source` on both melanoma rows. A pipeline harvesting a trial's CTG auto-linked publication list and treating it as evidence provenance will attach systematic reviews — and any other loosely-related paper — as the trial's source.

This is a **structural** defect, not a transcription slip, and it predicts where else to look: any row whose evidence `sourceUrl` is a `doi.org` link that was not independently confirmed to be the trial's own primary publication. That is **339 evidence entries** — the next verification tranche.

It does **not** explain row 3.3 (an orthodontics review on a DAPT trial), which must have a second, different mechanism. Unresolved.

---

## 5. Running scoreboard

| Metric | Count |
|---|---|
| Trial rows in corpus | 3,656 |
| Rows in the synthesis-sourced exposure class | 3 |
| **Rows verified at primary so far** | **4** |
| — confirmed correct on all checkable cells | 1 (PARADIGM-HF) |
| — identity wrong (intervention/design/n) | 2 |
| — identity right, provenance wrong | 1 |
| Rows remaining unverified | 3,652 |

**Error rate within the targeted exposure class: 3 of 3.** Small denominator — this is a signal to keep going, not a rate to quote.

---

## 6. What remains

Prioritised by the brief's rule — pooled rows before excluded rows, largest weight first.

| # | Task | Size | Why |
|---|---|---|---|
| 1 | Verify the 339 `doi.org`-sourced evidence entries: does the DOI resolve to the trial's OWN primary publication? | 339 | Directly tests the identified root cause |
| 2 | Audit the 1,044 rows that carry a `publishedHR` but no evidence block | 1,044 | Largest pooled-and-unsourced exposure; these carry effect estimates into analyses |
| 3 | Verify the 1,538 `clinicaltrials.gov`-sourced entries: does the NCT's registered intervention match the row's stated comparator? | 1,538 | The mismatch class that is invisible to internal checks |
| 4 | Confirm ULTIMATE-DAPT's HR 0.45 (0.30–0.66) and arm sizes against its primary publication | 1 | Row 3.3 left pending |
| 5 | Explain the CD003451 orthodontics attachment | 1 | Second, unexplained mechanism |
| 6 | Check `outputs/extraction_audit/truthcert/` (421 files) and `quarantine/` (138 files) | 559 | May already encode a certification/quarantine tier not yet examined |
| 7 | Locate the actual ARNI_HF screening log holding the Li 2019 row | — | Not in this repo; likely the other machine |
| 8 | Extend enumeration beyond `extraction_audit/data` to `findings/`, `nma/`, `outputs/r_validation/` | — | Exposure count above covers one directory only |

---

## 7. Method notes and honesty caveats

- **The exposure count covers `outputs/extraction_audit/data/` only.** Other directories (`findings/`, `nma/`, `synthesis-notes/`, `injections/`) were not enumerated. The 3,656 figure is a floor, not a total.
- **4 rows verified out of 3,656 is 0.1%.** Nothing here supports a corpus-wide error-rate claim, in either direction.
- **The one confirmation is as real as the three errors.** PARADIGM-HF's row is exemplary: verbatim quote, correct HR, correct CIs, correct event counts, correct comparator, correct population. Where this corpus sources properly, it sources well.
- **Two `Reyaz`/`48623` hits were false positives** and were read line-by-line before being dismissed. Recorded so nobody re-chases them.
- Every identifier resolved by live lookup. No number computed, summed or back-derived. Where a value could not be checked against the source consulted (e.g. PARADIGM-HF baseline characteristics), it is marked unverifiable rather than assumed correct.
- No repo writes. Read-only mount throughout.

**Attribution:** trial records read from ClinicalTrials.gov. Bibliographic record for PMID 25176015 retrieved from PubMed: [10.1056/NEJMoa1409077](https://doi.org/10.1056/NEJMoa1409077).
