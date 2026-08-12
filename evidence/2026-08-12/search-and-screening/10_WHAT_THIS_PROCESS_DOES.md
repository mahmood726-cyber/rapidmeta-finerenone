# What this process does that a conventional systematic review does not

*And what it does not yet have. Grounded only in what happened on 2026-08-12, with the failures included.*

---

## The short version

A conventional systematic review asks you to trust a set of claims: that the protocol came first, that two screeners worked independently, that disagreements were resolved sensibly, that the search was broad enough. Each claim is asserted in the methods section and none is checkable by the reader.

Today's run replaced six of those assertions with artefacts a reader can inspect. It did not replace all of them, and three of the six only became convincing *because* the process caught itself being wrong.

---

## Six things that are different, each with today's evidence

### 1. The pre-registration is provable, not asserted

The protocol was committed at **2026-08-12T11:27:47Z** (strengthened at 12:05:56Z). The first query was issued at **12:19:18Z** and first executed successfully at **12:22:39.556Z**. Both timestamps come from systems the authors do not control — a git committer field and a browser's Navigation Timing API — and both are independently checkable.

The detail that makes this more than a nicer PROSPERO: **the first query attempt failed.** It hit a proxy that returned 403 and produced nothing. Reporting only the successful execution would have been true, and would have quietly moved the first-query time three minutes later. Both are recorded. A process that reports the timestamp that flatters it is not measuring anything.

The counterfactual matters too. Earlier the same morning the review **halted** because the protocol commit did not exist: the SHA returned `422 No commit found`, and the HEAD of `main` was 28 hours older than the claimed protocol time. The correct move was to stop rather than search, because running then would have produced a real query timestamp paired with a phantom protocol timestamp — a pair that *looks* like a pass. The ordering test is only worth anything if it can fail, and this one nearly did, for the most boring possible reason.

### 2. The estimand is a criterion applied to the quantity reported, not a preference

The protocol froze the target as the time-to-first-event hazard ratio for cardiovascular death or first HF hospitalisation, and named three disqualifying quantity types **in advance**: a recurrent-event rate ratio, a win ratio over a hierarchical composite, and a fixed-timepoint dichotomous risk ratio.

All three fired today, on real trials:

- **PARADIGM-HF's recurrent-events paper** — rate ratio 0.77. Excluded.
- **PARACHUTE-HF** — win ratio 1.52. Excluded on its primary. (Then included; see §5.)
- **Bano 2021** — risk ratios 0.61 and 0.47 on components at 12 months, never combined, no hazard ratio anywhere in the paper. Excluded.

Why this matters: PARACHUTE-HF's own table reports **four different quantity types for overlapping outcomes** — a win ratio, a Cox HR for the composite, an LWYY recurrent-event rate ratio, and a Fine-Gray subdistribution HR. A review without a pre-committed estimand picks one of those four after seeing them. That is not a methodological nicety; four numbers pointing four directions is exactly the situation in which unregistered choice becomes result-driven choice.

There is a live example of what happens without the rule. A published meta-analysis in the corpus (PMC11883387) tabulates PIONEER-HF's finding as *"Greater time-averaged reduction in NT-proBNP (**HR**: 0.71; 95% CI: 0.63-0.81)"*. That 0.71 is a ratio of change in a biomarker. It is labelled a hazard ratio in a peer-reviewed table.

### 3. Every screening decision is published, not a kappa

`02_CORPUS_AND_SCREENING.tsv` is 423 rows: every record retrieved, with the decision, the stage it was taken at, the axis that failed, **and the quantity the study reports instead**. Conventional reviews publish a PRISMA box and an agreement statistic. An agreement statistic tells you two people agreed; it does not tell you what they agreed about, and it cannot be audited.

That last column is what caught the error. The exclusion note for PARACHUTE-HF read "No time-to-first-event hazard ratio for the composite" — a checkable claim about a specific paper, which a sibling lane checked, and which was false.

### 4. Human adjudication is named, dated, and shows what it overrode

Mahmood ruled INCLUDE on PARACHUTE-HF at **2026-08-12T13:30:45Z**, on stated grounds. The screener's original exclusion **stands unedited in the corpus file**; the ruling sits in an overlay beside it.

A reader can therefore see: the machine's decision, the challenge, the evidence read at source, and the human's ruling — four separately inspectable links. A conventional review shows only the final included-studies table, from which none of the preceding three can be recovered.

### 5. Corrections are struck through, not rewritten

Three self-corrections today, all still visible in the record:

| What was claimed | What was true | How it was found |
|---|---|---|
| PARACHUTE-HF reports no qualifying HR | It reports **HR 0.91 (0.73–1.13)** in Table 2 | external challenge, verified at source |
| The fixed-timepoint risk ratio type was "not encountered" | Bano 2021 was reporting exactly that, in a row already flagged undetermined | found while re-examining after correction 1 |
| Backward citation pass 1 "found records neither database string returned" | Both were already in the corpus; I had matched on surname and sample size instead of resolving identifiers | found while resolving the reference list properly |

The originals are struck through, not deleted. This is the part that reads as weakness and is not. A review that never records a correction is not a review that made none — it is a review that overwrote them. The failure rate here is observable; in a conventional review it is structurally invisible.

Two of the three corrections share a root cause worth naming: **matching on surface features instead of resolving identifiers.** It bit in the screen and again in the diff. It is now a standing rule rather than a lesson.

### 6. Undetermined rows stay undetermined

Two records are carried as `undetermined` rather than excluded, because their full texts are paywalled and the evidence available is the same class of evidence that failed for PARACHUTE-HF. Consequently **k = 3 is reported as a lower bound, not a result.**

The temptation runs the other way: excluding ANSWER-HF would make the included set look settled and cost almost nothing, since n=190 over 6 months would carry little weight. But weight is not eligibility, and "probably immaterial" is the reasoning that produced the PARACHUTE-HF error.

The distinction actually applied: **PIONEER-HF was excluded** — determinate — because two independent synthesis teams opened the paper and extracted its outcomes, and both recorded a *different* composite (all-cause mortality, device implantation, transplant listing). **ANSWER-HF stays undetermined** because nobody independent has read its tables; all that exists is the trial's own abstract, its registry record, and a mini-review co-authored by its own investigators. The rule is not "how confident do I feel" but "has anyone independent actually looked".

---

## What this does NOT have

Stated at the same level of detail, because a comparison that omits these is the over-claim the whole process is built to prevent.

**No second screener has run.** The cross-family requirement is in protocol §6 and it is the single most important control in the design — two instances of one model is one screener run twice. Only screener A has executed. Every agreement statistic this review will publish does not yet exist, and the outcome-axis rows, where today's failure concentrated, are precisely where that second pass is most needed.

**No RoB-2.** Protocol §9 was strengthened *before* the search to pre-register the tool, the unit of assessment, the variant and the domains. It remains PENDING. Not one signalling question has been answered.

**One human adjudicator, not two.** §6's submission tier requires two named human reviewers to have checked every included study and every extracted datum. One human has ruled on one conflict. The attestation records that gate the submission tier do not exist.

**The registered search missed a trial.** ANSWER-HF (NCT04853758) was not retrieved by the registered ClinicalTrials.gov string, because its `overallStatus` is `UNKNOWN` and the registered filter admits only three other values. The trial completed and published in *JACC*; the registry field is stale. A status filter filters the registry's record-keeping, not the trial. It was recovered only because the protocol registers two databases — a PubMed-only or registry-only search would have lost it silently.

**Two rows are blocked by paywalls.** PIONEER-HF and ANSWER-HF both sit behind subscriptions with no PMC record. PIONEER-HF was resolved through third parties who could read it; ANSWER-HF could not be. One paywalled article is the difference between k=3 and k=4.

**The backward citation search is 17 of 45 done**, and the corpus of syntheses is itself incomplete — a systematic review of exactly this comparison (PMID 38084196) was missed by the registered search. Eight fetched reference lists returned few tagged PMIDs and need reading by eye. The interim result — zero randomised trials missed across 231 resolved citations — is interim.

**No FDA or EMA document was consulted.** One attempt was made by typing a Drugs@FDA URL from recall; it 404'd and was abandoned rather than guessed at again, because constructing a document URL from memory is the same error as citing an identifier from memory.

**Nothing has been synthesised.** No pooled estimate, no heterogeneity, no GRADE. At k=3 the protocol's own §10 and §12 already flag the prediction interval as barely defined and the small-study tests as not assessable.

---

## The honest summary

What is demonstrated: an ordering test that could have failed and was reported when it nearly did; an estimand rule that excluded a large, well-conducted, directly relevant trial on the quantity it reported and then correctly readmitted it when a second quantity was found; a full decision record that made the error findable; a named human ruling that left the overridden decision visible; three self-corrections preserved rather than erased; and two rows held open at the cost of a tidier answer.

What is not demonstrated: anything requiring the second screener, the risk-of-bias assessment, the second human, a complete search, or a synthesis.

The strongest claim today's run supports is narrow: **this process makes its own errors findable, and today it found three.** Whether the resulting review is *better* than a conventional one is not yet established — that comparison needs the second screener to have run and the pooled estimate to exist. What is established is that the failures are in the record instead of in the reader's blind spot, which is the precondition for finding out.
