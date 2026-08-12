# Proposed protocol amendments — drafted for commit, NOT applied

Drafted 2026-08-12. **Not written to the repository.** Protocol §16 requires amendments to be recorded as further commits to `ssot/arni-hfref/PROTOCOL.md`, with the full history projected onto the review page. A build lane is the single writer; this file is the text to be committed, and each amendment must carry its own commit and timestamp so that the difference between what was registered before the search and what was learned during it stays visible.

All three amendments arise from work done **after** the search executed. That is worth stating on the face of the amendment: they are not pre-registration, they are corrections with a later timestamp, and the ordering test that this review publishes depends on nobody pretending otherwise.

---

## AMENDMENT 1 — to §3 (Eligibility criteria) and §6 (Study selection process)

**Add to §6, screening:**

> An exclusion on the OUTCOME axis may not be made at the title-and-abstract stage for any record that clears the population, intervention and comparator axes. Such a record is carried to full text regardless of what its title or abstract reports.
>
> The reason is structural, not a matter of screener care. An abstract reports a trial's primary endpoint; the estimand this review pools may be reported anywhere in the paper. A stage-1 outcome-axis exclusion is therefore blind by construction to a qualifying quantity that sits below the primary, and no amount of diligence at stage 1 can see it.
>
> Population, intervention and comparator remain excludable at stage 1: those axes are visible in a title and are not defeated by a secondary endpoint.

**Occasion:** PARACHUTE-HF (NCT04023227) was excluded on the outcome axis on the strength of its primary endpoint (a win ratio). Its first secondary endpoint is the registered estimand — HR 0.91 (0.73–1.13) for first HF hospitalisation or cardiovascular death, Cox model stratified by country, JAMA Table 2. The trial carries roughly 24% of the pool's weight.

---

## AMENDMENT 2 — to §2 (Estimand, stated in advance)

**Add to §2, after the list of excluded quantity types:**

> The outcome criterion is applied against **every quantity a trial reports**, not against the quantity the trial nominates as primary. Endpoint rank is a property of the trial's own design; the estimand is a property of this review. A trial qualifies if the time-to-first-event hazard ratio for the composite appears anywhere in its reported results, at any rank, including where the trial's primary analysis is one of the excluded types.
>
> Conversely, a trial does not qualify merely because it reports *some* hazard ratio: the hazard ratio must be for this review's composite, estimated as time to first event.
>
> A single trial may report several of the listed quantity types for overlapping outcomes. Where it does, each is recorded, exactly one is marked as selected, and the selection is the time-to-first-event hazard ratio for the composite.

**Occasion:** PARACHUTE-HF Table 2 reports **four** quantity types across overlapping outcomes — a win ratio of 1.52 over the hierarchical composite (primary), the qualifying HR of 0.91 for the composite (secondary), an LWYY recurrent-event rate ratio of 0.90, and a Fine-Gray subdistribution HR of 0.74 for first HF hospitalisation alone. Reading only the primary meant reading one of four and treating it as the trial's position. Deferring to the trialists' choice of primary is precisely the deference a pre-registered estimand exists to remove.

---

## AMENDMENT 3 — to §5 (Search strategy), ClinicalTrials.gov

**Replace:**

> ```
> query.intr=sacubitril valsartan OR LCZ696
> query.cond=heart failure
> filter.overallStatus=COMPLETED|TERMINATED|ACTIVE_NOT_RECRUITING
> ```

**With:**

> ```
> query.intr=sacubitril valsartan OR LCZ696
> query.cond=heart failure
> ```
>
> No status filter. Rationale, recorded so it is not re-litigated: a registry status filter filters **the registry's record-keeping, not the trial**. `UNKNOWN` means a sponsor has not refreshed the record; it says nothing about whether the trial completed.
>
> Records with a status indicating no results can exist (for example `WITHDRAWN`) are excluded at screening rather than by the query, so that the exclusion is visible in the PRISMA count instead of invisible in the search.

**Occasion:** the registered string did not retrieve **NCT04853758 (ANSWER-HF)** — sacubitril/valsartan versus enalapril in Chagas cardiomyopathy with HFrEF, n=190, primary results published in *J Am Coll Cardiol* 2026. The record's `overallStatus` is `UNKNOWN`, placing it outside the registered filter. The trial completed and published in a major journal; the registry field is stale. It was recovered only because the protocol registers two databases and PubMed indexed it.

**Method note, for the record:** the cause was established by fetching NCT04853758 by its identifier, **not** by re-running the search with altered parameters until the trial appeared. No variant of the registered string has been executed. Diagnosing a miss by direct lookup is legitimate; tuning a registered query against a known target is not, and the distinction should survive into the amendment.

---

## AMENDMENT 4 — to §4 (Information sources)

**Add:**

> A preprint-indexing source is searched. Europe PMC is specified, because a single query covers bioRxiv, medRxiv, Research Square and SSRN, and it is free to query.
>
> Rationale: neither PubMed nor ClinicalTrials.gov indexes preprints, and the backward citation step cannot reach them either, because preprints are rarely cited. A preprint of a directly relevant study is therefore invisible to every other source this protocol registers — not unlikely to be found, but structurally unfindable.
>
> A second consequence follows and is registered with it: **the enumeration of syntheses for the backward citation step in §5 requires its own search.** §5 names "every retrievable synthesis of this comparison" as the input without saying how that set is retrieved, and taking it from whatever the main string happens to return undercounts it.

**Occasion:** a Europe PMC sweep, scoped to title and abstract for comparability with the registered PubMed string, returned 324 records of which **101 are not in the corpus**, including seven preprints. One — `PPR1271024`, *Sacubitril-valsartan Versus Enalapril or Losartan at Guideline-Recommended Maximum Dosages in HFrEF (BEAT-HF)* — is directly on this review's comparison. It is ineligible because it is an observational cohort reporting an odds ratio, which is luck rather than method.

Separately, a dedicated search for syntheses of this comparison returns **244**, against the **45** the backward citation step was actually run on.

**Amendment 4 changes what the search returns.** Like Amendment 3, once committed it requires the added source to be executed and recorded as a separate, later search event.

---

## Recording requirements for whoever commits these

1. **One commit per amendment**, each with its own message and timestamp, so the log shows three separate decisions rather than one edit.
2. **No silent edit.** §16 already requires the full commit history, not only its head, to be projected onto the review page.
3. **State on the face of each amendment that it post-dates the search.** These are corrections learned from executing the protocol, not things registered before it. A reader checking the ordering test must be able to see which parts of the method predate the first query (11:27:47Z / 12:05:56Z) and which do not.
4. **Amendment 3 changes what the search returns.** Once committed, the ClinicalTrials.gov search must be re-executed under the amended string and the new hit count recorded as a separate, later search event — not merged into the 12:26:16Z capture.
