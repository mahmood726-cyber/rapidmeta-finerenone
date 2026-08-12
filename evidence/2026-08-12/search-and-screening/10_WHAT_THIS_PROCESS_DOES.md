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

### 5b. The search's recall is measured, not assumed — and the measurement survives paywalls

The backward citation step ran against **44 of 45** syntheses of this comparison, entirely by resolved identifier. Twenty-five had open-access full text and their reference lists were parsed from the Europe PMC REST API. **The other nineteen were paywalled, and were diffed anyway**, because OpenAlex exposes `referenced_works` for closed articles. Backward citation turns out not to require access to a synthesis — only to its bibliography.

Across roughly 760 resolved citations, **zero eligible randomised trials were missed.** Everything the registered search missed was an observational study, a cost-effectiveness model, a synthesis, or a trial with the wrong comparator or population.

> ### ⚠ The limit on that result, stated before the result is used
>
> **Backward citation measures recall against the field's own coverage, not against the truth.** It can only find what somebody else already found. A trial that every synthesis missed is invisible to it, by construction.
>
> The worked example is in this review. **ANSWER-HF** — the one trial the registered strategy nearly lost, and which was recovered only because PubMed indexed it — is invisible to this test, because it published in 2026 and is too recent to appear in anyone's reference list. Had PubMed also missed it, no amount of backward citation would have surfaced it.
>
> Two further limits, both discovered by pushing on this one:
>
> - **The frame was short by a factor of five.** The null was computed against 45 syntheses assembled from what the registered search happened to return. A dedicated search for syntheses of this comparison returns **244**. My frame was 18% of the retrievable set. The result is not withdrawn, but it was a weaker test than it was presented as, and the diff against the remaining 201 has not yet run.
> - **A broader index sees records no registered source can.** A Europe PMC sweep, title/abstract-scoped and comparable to the registered string, returned 324 records of which **101 are not in the corpus**, including seven preprints. One — a real-world cohort comparing sacubitril/valsartan against enalapril or losartan at guideline-maximum dosages — is directly on the review's comparison. It is ineligible because it is observational. That is luck, not method: **preprints are a layer neither registered database indexes and backward citation cannot reach**, because preprints are rarely cited.
>
> So the honest form of the claim is: *no eligible randomised trial was missed, as measured against an incomplete frame, by a method that is structurally blind to anything recent or unpublished.*

Within those limits, the checking-versus-breadth comparison survives but is much smaller than first reported. Verifying each candidate against the error-versus-declared-choice test **withdrew two of the three published errors**: one review's inclusion of prospective cohorts turned out to be a declared eligibility criterion with a separate risk-of-bias instrument applied to them, and the quotation offered as evidence of undeclared composite pooling turned out to be a document *disclosing* the heterogeneity in its own methods.

What remains is **one verified published error in four documents examined at extraction level** — a table cell describing a *"time-averaged reduction in NT-proBNP"* and labelling the estimate *"HR: 0.71; 95% CI: 0.63-0.81"* — against **four of our own**, and zero confirmed breadth failures for eligible trials. The sample is enriched by construction and one-in-four is not a rate for the literature. The counts are also not symmetric evidence: checking failures are found by re-reading numbers already in hand, breadth failures require finding what nobody has. Full entries, denominators, sampling method and the two withdrawals are in `13_ERROR_LIBRARY.md`.

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

**The corpus of syntheses is incomplete, and now measurably so.** A dedicated search returns **244** syntheses of this comparison against the **45** the backward-citation null was computed on. The diff against the remaining 201 is **not run** — the OpenAlex route that made paywalled reference lists readable exhausted its free daily budget mid-session (`Insufficient budget… Resets at midnight UTC`) and I did not pay for credits or route around it. One synthesis (IQWiG, PMID 29144684) has no route to its reference list at all, and 78 of 457 OpenAlex works did not resolve to metadata — unresolved, not absent.

**Preprints are outside the frame entirely.** Neither registered database indexes them; backward citation cannot reach them. A Europe PMC sweep found seven, one of them directly on the review's comparison. A fourth protocol amendment is drafted to add a preprint source, and like the other three it post-dates the search.

**The CSR layer has never been touched, and one door to it is shut structurally.** EMA Policy 0070 currently publishes clinical data only for CHMP opinions from September 2023 (new active substances) or May 2025 onwards; **Entresto's opinion was 2015**, so its clinical study reports are not on the portal. The flagship regulatory transparency route does not reach the pivotal trial of this review's own drug. The remaining route, Clinical Study Data Request, requires a named researcher to submit a proposal and sign a data-sharing agreement — a human action, not initiated. This is not abstract: a CSR is what would settle ANSWER-HF and PIONEER-HF, the two rows currently holding k at a lower bound.

**No FDA or EMA document was read.** Both are now *located* by lookup — openFDA gave the Drugs@FDA package, a domain-restricted search gave the EPAR — and §4's trigger does not fire for them, since the cells they could establish are already established and the 2015 Entresto package predates the only row that needs one. Locating a source and recording an unmet trigger is executing §4; reading them is still not done. The earlier abandoned attempt is worth keeping in view: the recalled URL ended `.cfm`, the real one ends `.html`.

**Nothing has been synthesised.** No pooled estimate, no heterogeneity, no GRADE. At k=3 the protocol's own §10 and §12 already flag the prediction interval as barely defined and the small-study tests as not assessable.

---

## The honest summary

What is demonstrated: an ordering test that could have failed and was reported when it nearly did; an estimand rule that excluded a large, well-conducted, directly relevant trial on the quantity it reported and then correctly readmitted it when a second quantity was found; a full decision record that made the error findable; a search whose recall was measured against 44 syntheses rather than asserted; a named human ruling that left the overridden decision visible; three self-corrections preserved rather than erased; and two rows held open at the cost of a tidier answer.

What is not demonstrated: anything requiring the second screener, the risk-of-bias assessment, the second human, or a synthesis.

The strongest claim today's run supports is narrow: **this process makes its own errors findable, and today it found three.** Whether the resulting review is *better* than a conventional one is not yet established — that comparison needs the second screener to have run and the pooled estimate to exist. What is established is that the failures are in the record instead of in the reader's blind spot, which is the precondition for finding out.

---

## Maintenance note

Current to **2026-08-12, end of day**. Two entries in the "what it lacks" half are expected to close, and this document should be updated when they do: **the second cross-family screener**, which closes the agreement-rate gap and independently tests the outcome-axis rows where today's failure concentrated; and **RoB-2 under §9**, which is pre-registered and PENDING. When either lands, move it out of the lacks list and say what it showed — including, especially, if it showed disagreement. The credibility of the first half rests entirely on the second half staying honest.
