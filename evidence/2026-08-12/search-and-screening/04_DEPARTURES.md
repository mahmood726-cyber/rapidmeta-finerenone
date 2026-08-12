# Departures from the protocol

Protocol read at commit `dde501167666f41ffdc81a07df1628734ce327a0`, parent `973f031773d3`.

---

## 1. Departures from the registered search strings

**None.**

Both registered strings executed as written, first time, without modification:

- The PubMed string parsed with all four blocks intact. PubMed's returned `querytranslation` is reproduced verbatim in `01_SEARCH_CAPTURE.md` §2 so a reader can check that no term was dropped or silently re-mapped.
- The ClinicalTrials.gov parameters, including the pipe-delimited status list `COMPLETED|TERMINATED|ACTIVE_NOT_RECRUITING`, were accepted by API v2 as written. I had expected this might need comma-delimiting; it did not, so no departure arose and none was invented.

No language filter and no date filter were applied to either database, as registered.

---

## 2. Registered work not executed in this run

Not departures — **unfinished registered work**, listed so the PRISMA numbers are not mistaken for a completed search.

| Protocol section | Registered | Status |
|---|---|---|
| §4, §5 | Backward citation search: included-study table of every retrievable synthesis, diffed against this review's included set **in both directions** | **Not executed.** 45 records in the corpus are flagged `synthesis_candidate=Y` and are the input to this step. |
| §4 | FDA statistical review and EMA EPAR for Entresto, where a cell cannot be established from the other sources | **Not consulted.** |
| §6 | Second independent screener of a different model family | Runs separately, by design. My decisions are unreconciled, as instructed. |
| §6 | Adjudication of disagreements by a named human | Not reached. |
| §7 | Data extraction with a resolvable pointer to the specific document and table for every cell | **Not performed.** The two included effect estimates come from abstracts and are not yet pinned to a table. |
| §9 | RoB-2, two cross-family assessors, per-domain with signalling questions | **Not performed.** Protocol records this as PENDING. |
| §10–13 | Synthesis, sensitivity, meta-bias, GRADE | Not reached. At k=2, §10's prediction interval and §12's small-study tests are already flagged in the protocol as undefined or not assessable. |

---

## 3. Method-of-execution notes

Neither is a departure from the protocol, which specifies strings and criteria rather than transport, but both are recorded because they affect reproducibility:

1. **The queries were executed through a browser rather than a server-side HTTP client.** The sandbox egress proxy returns `403 Forbidden` for `eutils.ncbi.nlm.nih.gov`, and the available `web_fetch` tool timed out at 180 s on both attempts. The strings, parameters and endpoints are unaffected; anyone re-running them by any client should reproduce the counts, subject to database growth.
2. **Stage-1 screening rested on title, journal and publication type for 416 of 423 records.** Full abstracts were retrieved for 7. This is stated at length in `03_PRISMA_AND_SCREENING_NOTES.md` §5 and is the largest soft spot in this run.

---

## 4. Observations about the registered strings themselves

Recorded as findings, not acted on. Changing a registered string on the basis of what it returned is exactly the move the registration exists to prevent, so these go to the human, not into a revised query.

### 4.1 The registered ClinicalTrials.gov string did not retrieve ANSWER-HF

**NCT04853758** (ANSWER-HF — sacubitril-valsartan vs enalapril in Chagas cardiomyopathy with HFrEF, n=190, primary results in *J Am Coll Cardiol* 2026, PMID 41396086) is **not among the 92 records** returned by the registered ClinicalTrials.gov parameters.

It was found anyway, through PubMed. That is the two-database design working. But it means the registered registry string has at least one known miss on a directly on-topic trial, and the miss would have been invisible had the search been PubMed-only or registry-only.

**Cause diagnosed (added after the adjudication pass).** NCT04853758 exists in ClinicalTrials.gov with `overallStatus` = **`UNKNOWN`**. The registered filter admits only `COMPLETED|TERMINATED|ACTIVE_NOT_RECRUITING`, so the record is excluded by the status filter, not by the intervention or condition terms. This was established by fetching the single record by its identifier — **not** by re-running the search with altered parameters. Testing variants and keeping whichever one finds the trial is exactly the unregistered fishing the protocol forbids, and it remains untried.

**This is a limitation of the registered strategy and must be corrected by amendment, not silently.** The substantive point for whoever drafts that amendment: a status filter is a filter on the *registry's record-keeping*, not on the trial. `UNKNOWN` means the sponsor has not updated the record recently — it does not mean the trial did not complete, and here the trial has completed and published its primary results in a major journal. A status filter that can drop a published trial on the strength of a stale registry field is doing something other than what it was intended to do.

*(ANSWER-HF is excluded on the outcome axis regardless — it reports an LVEF change and a win ratio, not a time-to-first-event hazard ratio — so this miss does not change the included set. It could easily have.)*

### 4.2 The PubMed string's fourth block is broad

`... OR trial[tiab]` admits any record with the word "trial" anywhere in title or abstract, which is why the corpus contains 195 non-randomised records — narrative reviews discussing trials, cost-effectiveness models parameterised from trials, registry papers comparing themselves to trials. This is a high-sensitivity, low-precision choice and it is the correct one for a systematic review. Recorded so the 195 is not read as a defect in execution.

### 4.3 One record returned incomplete metadata

PMID **29144684** returned an empty `title` and empty `journal` from `esummary`. Resolved by `efetch`: it is the IQWiG benefit assessment of sacubitril/valsartan under §35a SGB V — a German-language, non-journal HTA report. Recorded rather than dropped, because a record with missing metadata is a metadata failure, not an absent record, and dropping it silently would have made the corpus 330 while the read count said 331.

---

## 5. Nothing was written to the repository

Read-only throughout: five GET requests to `api.github.com`, one rendered blob page on `github.com`. No writes, branches, issues or pull requests. All deliverables were written outside the repository.
