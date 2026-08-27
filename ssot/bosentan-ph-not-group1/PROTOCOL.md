# Protocol - Bosentan in pulmonary hypertension that is not WHO group 1: eight eligible trials and not one posted result

> ## ⚠ THIS IS AN UNANCHORED DRAFT. IT IS NOT A REGISTRATION.
>
> Drafted 2026-08-27 and committed **only so the work is preserved** when the
> registration stream was paused. Three things that a registration has, this does not:
>
> - **No transparency-log anchor exists for it.** Nothing has been submitted to Rekor.
> - **No search has been run against it.** The ordering test it describes below —
>   protocol anchored before the first query — has NOT been performed.
> - **Its own Status line, written by the drafting model, calls it a registration.**
>   That line is wrong until the two steps above happen, and is left in place rather
>   than edited so that the draft is preserved exactly as generated.
>
> To become a registration this file must be committed, pushed, anchored in the public
> log, and only then searched, with the log index and the first query time recorded.
> Until then it is a proposal. See `ssot/registration/PAUSED-POSITION.md`.

**Status: RETROSPECTIVELY REGISTERED BY COMMIT. This document is the
registration.**

This protocol is registered as a commit in a public repository rather than in
PROSPERO. The commit hash binds this exact text; the repository is public.

**The commit timestamp is the weak half, and this document will not pretend
otherwise.** The commit timestamp is author-supplied and forgeable: git author
and committer dates are set by whoever makes the commit, and commits here are
unsigned.

What the mechanism supports, and no more: this exact text is bound to this hash,
and the repository is public, so the text is readable by anyone at that hash.
A public transparency-log entry gives an inclusion time set by a third party,
and what it proves is narrow: THE TEXT EXISTED NO LATER THAN THE LOG TIME.

What it does not support: it does not prove when the commit was made, and it
does not prove no earlier or parallel version existed elsewhere. It does not
prove the data had not already been seen, and it says nothing about the
independence of the people who wrote it. Those are claims about conduct, and no
timestamp can carry them.

**How to check this without us.** The verification recipe, the public half of the signing key, and a worked example are at [`ssot/registration/VERIFY.md`](../registration/VERIFY.md). It states the limitation plainly as well: the log time is independent of us, the key custody is not. A stranger can verify the text existed by the log time and that we signed it; a stranger cannot verify we did not hold an earlier version.

**It is written after the evidence object already held trials, and before the
registered search lane runs.** This protocol is committed, pushed, and
log-anchored before the first query. The ordering test this review publishes uses
the earliest query time, including a failed attempt, rather than the first
successful one, because reporting only the successful execution would move the
first-query time later and flatter the claim.

The search record will itself be log-anchored afterwards, so two third-party
times bracket the operation: one before the first query attempt, and one after
the search record exists. Both local execution times are read from the search
lane's own clock. The databases return records and hit counts, not authoritative
timestamps for our act of searching. The sequence is therefore auditable and
bounded by third-party log times, and it is recorded here as less than proof.

The anchor proves WHEN this text was written and CANNOT prove the trials had not
already been seen. A timestamp bounds when, never what was known.

---

## 1 - Review question, in PICO

This is a RETROSPECTIVELY REGISTERED protocol. The topic already holds 8 trials:
NCT00310830, NCT00313196, NCT00581607, NCT00625469, NCT00637065, NCT00820352,
NCT00926627, and NCT01449253. The question is being authored after that evidence
was assembled.

| | |
|---|---|
| **Population** | Adults with pulmonary hypertension due to chronic thromboembolic disease, lung disease, left heart disease, sickle cell disease, or sarcoidosis, and not WHO group 1 pulmonary arterial hypertension as the target population. |
| **Intervention** | Bosentan. |
| **Comparator** | Placebo, inactive control, or usual care. |
| **Outcome** | Exercise capacity and clinical worsening, using the registered outcome definitions for each trial. |
| **Study design** | Randomised controlled trials. |

**Frozen question:** In adults with pulmonary hypertension due to chronic
thromboembolic disease, lung disease, left heart disease, sickle cell disease or
sarcoidosis, what is the effect of bosentan compared with placebo or usual care
on exercise capacity and on clinical worsening?

## 2 - Estimand, stated in advance

This review does not register a single shared pooled estimand at the time of this
commit. The planned extraction is outcome-family first: exercise capacity and
clinical worsening are read from the registry outcome module and from any linked
publication, then each recovered result is classified by measure, timepoint,
analysis population, and comparator.

The primary exercise-capacity estimand, where extractable, is the between-arm
mean difference in change in six-minute walk distance or another explicitly
registered exercise-capacity measure, on its natural scale, at the trial's
registered assessment time. The primary clinical-worsening estimand, where
extractable, is the trial-defined clinical-worsening effect measure as posted or
published, preserving whether it is time-to-first-event, binary, or another
measure.

**Quantities are not forced into a common field.** A hazard ratio, risk ratio,
odds ratio, risk difference, rate ratio, mean difference, or median difference is
stored as the measure it is. If no common estimand exists after extraction, the
review reports the absence of a pool rather than manufacturing one.

## 3 - Eligibility criteria

**Include** a study if all six axes hold: it is randomised; it enrols adults; its
target population is pulmonary hypertension due to chronic thromboembolic
disease, lung disease, left heart disease, sickle cell disease, or sarcoidosis
rather than WHO group 1 pulmonary arterial hypertension; it tests bosentan; its
comparator is placebo, inactive control, or usual care; and it registers or
reports exercise capacity or clinical worsening.

**Exclude** on any single failed axis - adult status, population, intervention,
comparator, randomised design, or outcome family - and record which axis failed
and what the record states instead.

Posted-result absence is not an eligibility failure. It is recorded separately as
a data-availability state for an otherwise eligible trial.

Populations narrower than the question are **not** indirect on that ground alone;
narrowness is recorded and carried into the GRADE indirectness domain rather
than used as an exclusion.

Any axis read from a registry title is provisional until the relevant registry
module is read. In particular, a title is not an outcome definition; outcome
eligibility is settled only from the registered primary and secondary outcome
measures or from a linked publication's defined outcome.

## 4 - Information sources

PubMed (NCBI E-utilities) and ClinicalTrials.gov API v2 only.

Embase was NOT searched, nor CENTRAL, Web of Science or Scopus. This is a narrow
two-source search. The cost of the omission is that trials or publications
indexed only in the omitted databases, conference records not represented in
PubMed, citation-only records outside ClinicalTrials.gov, and non-indexed
publication links may be missed. Any absence found by this review is therefore
an absence from the stated sources and linked records, not an absence from the
world.

## 4A - Linkage method and its known failure modes

Before the search runs, registry records will be linked to publications in this
order:

1. Resolve each known NCT identifier directly through ClinicalTrials.gov API v2.
2. Read the registry reference module and retain any reference explicitly linked
   to the trial record, recording its reference type.
3. Query PubMed through NCBI E-utilities for the NCT identifier and for the trial
   name when an identifier query does not recover a publication.
4. Treat a publication link as successful only when the publication and registry
   agree on the trial identity by NCT identifier, trial acronym, registered
   population, intervention, comparator, and outcome context.
5. If those checks conflict, retain the citation as a candidate link and mark it
   unresolved rather than treating it as evidence.

Two linkage failure modes are known and measured on this corpus before this
search is executed. First, PubMed silently DROPS trials from ID-based queries
when the record is not indexed, so an absent result is indistinguishable from a
trial that does not exist. Second, registry `reference_type='result'` links can
point at the WRONG paper, which is worse than a missing link because a wrong link
looks like a successful one.

Where linkage succeeds, registry data matched the publication in 26 of 28
analyses compared on this corpus. That is a conditional figure whose denominator
is LINKED analyses, not all analyses, and therefore it is not a general
reliability rate.

## 5 - Search strategy - the exact strings to be executed

These strings are stated **before** execution. The search lane will record what
it actually ran, on what date, with what filters, and how many records each
returned; any departure from the strings below will be recorded as a departure
rather than silently substituted. Each string is kept under 20 Boolean operators
because a registered string that the interface refuses cannot be executed without
a departure on the first attempt.

**PubMed (NCBI E-utilities)**

```
(bosentan[tiab] OR Tracleer[tiab])
AND ("pulmonary hypertension"[tiab] OR "pulmonary hypertension"[MeSH Terms] OR CTEPH[tiab] OR "chronic thromboembolic"[tiab] OR sarcoidosis[tiab] OR "sickle cell"[tiab] OR "interstitial lung disease"[tiab] OR "diastolic heart failure"[tiab] OR "left heart disease"[tiab])
AND (randomized controlled trial[pt] OR randomised[tiab] OR randomized[tiab] OR placebo[tiab] OR trial[tiab])
```

Filters: none on language, none on date. Rationale: a language or date filter
would narrow the record set for reasons not part of the eligibility criteria.

**ClinicalTrials.gov (API v2)**

```
query.intr=bosentan OR Tracleer
query.cond=pulmonary hypertension OR chronic thromboembolic OR interstitial lung disease OR sickle cell OR sarcoidosis OR diastolic heart failure OR left heart disease
filter.overallStatus=COMPLETED|TERMINATED|ACTIVE_NOT_RECRUITING
```

**ClinicalTrials.gov known-identifier resolution (API v2)**

```
query.id=NCT00310830 OR NCT00313196 OR NCT00581607 OR NCT00625469 OR NCT00637065 OR NCT00820352 OR NCT00926627 OR NCT01449253
```

No backward citation search, forward citation search, registry outside
ClinicalTrials.gov, or bibliographic database outside PubMed is registered for
this review.

## 5A - How this search can fail, decided in advance

Every possible search outcome is interpreted before execution:

- If the search reproduces the held set, the held set is treated as
  searched-for rather than convenient. The review may report that the registered
  search recovered the trials already held, without implying that the question
  was authored before those trials were seen.
- If the search returns additional eligible trials, that is a finding about the
  review. Each additional trial is named and either included or excluded on one
  of the section 3 axes, with the axis stated.
- If the search returns fewer trials than the object holds, that is a finding
  about the search, never reported as the review being wrong. The held trials
  remain candidate records requiring source-level verification.

Worked example for the third outcome: the finerenone-cv registry query missed
FIGARO-DKD (NCT02545049), a pivotal trial, because it registers its condition as
"Diabetic Kidney Disease" alone while its sibling FIDELIO-DKD registers
"Chronic Kidney Disease". A narrow query looks exactly like a wrong review.

## 6 - Study selection process

Two **independent screeners of different model families** - the cross-family rule
is a requirement, not a preference, because two instances of one model is one
screener run twice and its agreement statistic is meaningless.

Screening is in two stages: title and abstract or registry summary, then full
text or full registry record. **Each screener's decision is recorded per record
at the stage it was applied**, together with the reason. Both screeners'
decisions are published, not only the reconciled outcome, along with the
agreement rate and how every disagreement was resolved.

**Adjudication of disagreements is by a named human.**

**Two release tiers, and the difference between them is attestation, not
content.** The website release requires the two cross-family AI assessments and
states plainly that it has not been human-verified. The submission release
additionally requires two named human reviewers to have checked every included
study and every extracted datum; the statement to that effect is emitted only
when those attestation records exist and is never written as prose.

## 7 - Data extraction

Extracted per trial and per outcome: registry identifier, linked publication if
any, year, design, population, arms, comparator, registered primary and secondary
outcomes relevant to exercise capacity or clinical worsening, data-availability
state, **the analysed denominator and the randomised total separately**, per-arm
counts or continuous summaries when present, and the published or posted effect
estimate with its interval and stated confidence level when present.

Every screened record is classified against the section 3 axes and no others:
adult status, population, intervention, comparator, randomised design, and
outcome family. A record is not excluded for publication status, sample size,
sponsor, geography, journal status, language, or whether the result is convenient
for pooling.

Any axis read from a registry title is provisional until the relevant module is
read. A title is not an outcome definition. Outcome classification is not final
until the registered primary outcome measure and relevant secondary outcome
measures have been read from the outcome module, or the publication defines the
outcome directly.

Every extracted cell carries a resolvable pointer to the specific document and,
where possible, to the table, figure, registry field, or outcome module within it
so that a human check can be made without leaving the page. **Nothing is
computed that can be read.** No count is derived from a percentage; no composite
is reconstructed by summing its components. Identifiers are resolved by lookup,
never from recall.

Where two populations exist for one outcome - for example a full analysis set
and a randomised set - both are recorded, exactly one is marked as selected, and
the population is named on the cell.

## 8 - Outcomes and prioritisation

**Primary outcome family 1:** exercise capacity, prioritising change in
six-minute walk distance where it is registered or reported, and otherwise the
registered exercise-capacity measure named by the trial.

**Primary outcome family 2:** clinical worsening, prioritising the trial-defined
time to clinical worsening where it is registered or reported, and otherwise the
registered clinical-worsening or morbidity/mortality measure named by the trial.

Results are not pooled across outcome families. Within an outcome family, results
are pooled only if measure, direction, timepoint, and analysis population are
coherent enough to make the pooled estimand defensible. Otherwise they are
reported narratively as source-backed cells.

## 9 - Risk of bias

**Tool.** Cochrane risk-of-bias tool for randomized trials, version 2 (RoB-2).

**Unit of assessment.** RoB-2 is applied **to the result being synthesized, not
to the trial as a whole**. If no result is extractable for an eligible trial, the
RoB-2 assessment for that missing result is not invented; the trial is recorded
as eligible with no assessable posted or published result for that outcome
family.

**Variant.** The **effect of assignment to intervention** variant, because that
is what an intention-to-treat randomized comparison estimates. The adherence
variant is not used, and no result assessed under one variant will be reported
as though assessed under the other.

**Domains.** All five, each reached through the RoB-2 signalling questions rather
than by overall impression, with a recorded answer per signalling question, a
**domain judgement** of low / some concerns / high, and a rationale naming the
evidence it rests on:

1. Bias arising from the randomization process
2. Bias due to deviations from intended interventions (effect of assignment)
3. Bias due to missing outcome data
4. Bias in measurement of the outcome
5. Bias in selection of the reported result

An **overall judgement** follows the standard RoB-2 algorithm: low only if every
domain is low; high if any domain is high or if multiple domains raise some
concerns in a way that substantially lowers confidence; some concerns otherwise.

**Assessors.** Two independent assessors **from different model families**. Two
instances of one model is one assessor run twice and its agreement statistic is
meaningless, so same-family duplication does not satisfy this requirement.
Neither assessor may be the agent that assembled the canonical object, because
assessing one's own extraction is not an independent assessment.

**Both sets of judgements are recorded and published** - per domain, per
assessor, with rationales - not only the reconciled outcome. The **per-domain
agreement rate is published as measured**. Agreement on RoB-2 domains is expected
to be substantially lower than agreement on screening; if that proves true it is
a finding worth reporting and it will not be smoothed. **Disagreements are
adjudicated by a named human**, and the adjudication and its reason are recorded
per disagreement.

**Evidence admissible to an assessment.** The trial's registry record including
its protocol and statistical analysis plan where posted, the primary publication
and its supplement, and the posted results module. A judgement made from an
abstract alone is not the same act as one made from a protocol, so **the sources
actually consulted are recorded per domain**, and a domain judged without access
to the protocol is marked as such rather than presented as equivalent.

**Relationship to the recorded bias features.** The object may already hold
bias-relevant features. These are **inputs to the assessment and never
substitutes for a domain judgement**. No existing prose in the object may stand
in for a signalling question or a domain rating.

**Feeding GRADE.** The completed RoB-2 result becomes the basis of the GRADE
risk-of-bias domain, replacing any current reasoning from recorded features.
When it does, the review will state **whether the GRADE rating moves and why -
and if it does not move, will say so explicitly** rather than leaving the reader
to infer that nothing changed.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No RoB-2 assessment exists for these trials in this protocol.
Performing it later **executes this section rather than amending it**, and the
object will record that distinction.

## 10 - Synthesis methods

If at least two trials report the same outcome family on a compatible scale,
random-effects meta-analysis is planned on that scale, inverse-variance weighted
where an effect estimate and standard error can be recovered.

**Decided in advance, so that reporting a disagreement between methods is a
commitment rather than a post-hoc observation:**

- **REML** is the headline between-study-variance estimator.
- The **Hartung-Knapp-Sidik-Jonkman interval is reported alongside** the Wald
  interval, and where the two disagree about whether the interval crosses the
  null, that disagreement is reported in the results rather than resolved by
  choosing one.
- **Leave-one-out** analysis is run and reported for every pool where it is
  defined.
- An **estimator comparison** - DerSimonian-Laird, REML, Paule-Mandel - is run
  and reported, per Cochrane Handbook v6.5 section 10.10.4.4, on the
  understanding that with few studies the choice is plausibly influential.
- A **prediction interval** is reported using the t distribution on k-1 degrees
  of freedom per Handbook v6.5, and is not reported where k makes it undefined.
- The analysis is **cross-checked in a second engine** at build time and the
  comparison published, including any quantity on which the two engines disagree
  by definition rather than by error.

**Heterogeneity:** tau-squared, I-squared with its Q-profile confidence interval,
and Q with its degrees of freedom and p value. I-squared is reported with the
caveat that at small k a low value reflects imprecision as much as agreement.

## 10A - No-result operating rule

If the registered search and linkage process finds eligible trials but no posted
or published result for exercise capacity or clinical worsening, the review
reports that data-availability finding and does not run a numerical synthesis.

If a result is absent from ClinicalTrials.gov but present in a linked publication,
the publication result is extracted and the registry absence is still recorded.
If a result is absent from PubMed and ClinicalTrials.gov linkage but present only
through a route not registered in section 4, it is not silently imported into the
main synthesis; it is recorded as an unregistered-source finding or as an
amendment, depending on when and how it is found.

## 11 - Subgroup and sensitivity analyses

**Sensitivity, decided in advance:** leave-one-out where a pool is defined; the
estimator comparison above; and, where per-arm counts are recovered, the same
2-by-2 table pooled as a risk ratio, an odds ratio and a risk difference -
reported as sensitivity to the primary scale, never as the headline when the
primary scale is different.

**Subgroup: none specified.** With the small number of trials this comparison has
and the heterogeneity expected across non-group-1 pulmonary hypertension
etiologies, any subgroup contrast would be underpowered and vulnerable to
post-hoc interpretation. Etiology is recorded and shown; it is not used to make a
planned subgroup claim in this protocol.

## 12 - Meta-bias assessment

Funnel plot, Egger's regression and - for any count-based pool - Peters' test.
**Caveat fixed in advance:** below approximately ten studies these tests have
almost no power and the Cochrane Handbook advises against interpreting them.
Where k is below that threshold the tests may still be computed for completeness,
and will be reported as computed values, explicitly not as evidence about
small-study effects.

Where publication bias cannot be assessed, the GRADE domain will read *not
assessable* rather than *not serious* - the two are different statements. If no
pool exists because no extractable result exists, meta-bias testing is not
applicable and will be labelled that way rather than replaced with narrative
speculation.

## 13 - Certainty of the evidence

GRADE, per Cochrane Handbook v6.5 sections 14.2.1-14.2.2 and MECIR C74/C75. All
five downgrade domains are assessed and **each rating is published with the
evidence it rests on**; the overall certainty is computed from the domains and
shown against them so a reader can check the arithmetic.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No GRADE assessment exists for these trials in this protocol.
Performing it later **executes this section rather than amending it**, and the
object will record that distinction.

## 14 - Data sharing and reproducibility

The canonical data object from which every number on the review page is
projected is published with the review, together with the session information
and the analysis scripts actually executed. The intent is that the review can be
rebuilt from the object alone.

The registration commit, the public transparency-log anchor for this text, the
search execution record, and the later transparency-log anchor for the search
record are part of the reproducibility record. The ordering claim is the bracket
between those artifacts, not a bare timestamp asserted in prose.

## 15 - Funding and conflicts of interest

**No funding was received for this review.** No competing interests are declared
by the authors of this protocol at the time of this commit. Any change is to be
recorded as an amendment rather than by editing this section.

## 16 - Amendments

Amendments will be recorded as further commits to this file; the full commit
history, not only its head, is projected onto the review page, because a log that
displays only its own head is no better than a mutable document.
