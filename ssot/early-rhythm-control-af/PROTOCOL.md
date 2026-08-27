# Protocol - Early rhythm control as a STRATEGY in atrial fibrillation: what the strategy trials report, and why their four registered primaries do not pool

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

**Status: RETROSPECTIVELY REGISTERED BY COMMIT, PUBLIC PUSH, AND TRANSPARENCY-LOG ANCHOR. This document is the registration.**

This protocol is registered as a commit in a public repository rather than in
PROSPERO. The commit hash is the strong half of that record: the content is
immutable under it, so this text cannot be altered later without producing a
different hash, and anyone can check that much without asking us. The repository
is public, so the text is readable by anyone at that hash.

**The commit timestamp is the weak half, and this document will not pretend
otherwise.** Both the author and the committer date on a git commit are supplied
by whoever makes the commit and can be set to any value. Commits here are
unsigned. A git timestamp is therefore not treated as proof of when the commit
was made.

What the mechanism supports, and no more: this exact text is bound to this hash;
the repository is public; and where an entry for the commit exists in a public
transparency log, that log's inclusion time is an upper bound on when this text
existed, set by a third party rather than by us. The transparency-log entry proves
something narrow: the text existed no later than the log time.

What it does not support: it does not prove when the commit was made, it does not
prove that no earlier or parallel version existed elsewhere, it does not prove
the trials had not already been seen, and it says nothing about the independence
of the people who wrote it. Those are claims about conduct, and no timestamp can
carry them. A timestamp bounds when, never what was known.

**How to check this without us.** The verification recipe, the public half of the signing key, and a worked example are at [`ssot/registration/VERIFY.md`](../registration/VERIFY.md). It states the limitation plainly as well: the log time is independent of us, the key custody is not. A stranger can verify the text existed by the log time and that we signed it; a stranger cannot verify we did not hold an earlier version.

**It is written before the search runs, but after evidence was already assembled
for this topic.** The ordering test this review publishes is that this protocol
commit is committed, pushed, and anchored in a public transparency log before the
first executed query. The first executed query means the first attempt, including
a failed attempt, not the first successful execution. Reporting only the
successful execution would move the first-query time later and flatter the claim.

The search record is anchored afterwards, so two public transparency-log times
bracket the operation: one before the first query attempt and one after the
search record is written. The databases return hit counts and records, not
trusted third-party times. The bracketing claim is therefore the narrow claim the
anchors can support: this text existed by the first log time, and the later search
record existed by the second log time. The anchors do not prove the search had
not been mentally or manually anticipated, and they do not make this protocol
anything other than retrospectively registered.

---

## 1 - Review question, in PICO

This topic already holds 1 trial: NCT01288352. The question is being authored
after that evidence was assembled. However carefully it is written now, this is a
retrospectively registered protocol. The anchor proves only when this text
existed, bounded by the transparency-log inclusion time, and cannot prove the
trials had not already been seen. A timestamp bounds when, never what was known.

| | |
|---|---|
| **Population** | Adults with atrial fibrillation. |
| **Intervention** | An early rhythm-control strategy: antiarrhythmic drugs or ablation, chosen and escalated as a strategy rather than as a single procedure. |
| **Comparator** | Usual care or rate-control-oriented care without early rhythm-control strategy assignment. |
| **Outcome** | Cardiovascular death, stroke or hospitalisation, read first as each trial's own registered primary outcome and then checked for exact component compatibility. |
| **Study design** | Randomised controlled trials. |

**Frozen question:** In adults with atrial fibrillation, does an early
rhythm-control STRATEGY -- antiarrhythmic drugs or ablation, chosen and escalated
as a strategy rather than as a single procedure -- reduce cardiovascular death,
stroke or hospitalisation compared with usual care?

## 2 - Estimand, stated in advance

The intended estimand is the **time-to-first-event hazard ratio for a shared
cardiovascular composite**, on the log scale, with the participant as the unit of
analysis and the time to the first component event as the event time.

The strategy question and the meta-analytic estimand are deliberately separated.
A trial can answer the strategy question and still fail to enter a pool if its
registered primary outcome is not the same outcome as the others at the component
level. The review will not pool four registered primaries merely because they are
all important cardiovascular composites. Cardiovascular death, all-cause death,
stroke, heart-failure events, hospitalisation, bleeding, and cardiac arrest are
not interchangeable components.

**Quantities that cannot be converted into the stated estimand are excluded on
the MEASURE axis, not on grounds of quality.** This is pre-specified because it
is a criterion and not a judgement made after seeing results. A trial may be
large, well conducted and directly on topic and still fail this review's pooling
eligibility because it reports a different estimand. Specifically and in advance:

- A recurrent-event rate ratio counts repeat events per person over time; a
  time-to-first hazard ratio counts each person once, at their first event.
- A win ratio over a hierarchical composite is not this estimand.
- A dichotomous risk ratio at a fixed timepoint is not this estimand, though
  where per-arm counts are recovered a risk ratio, odds ratio and risk difference
  will be computed and reported as sensitivity analyses only, never as the
  headline.
- A hazard ratio for a composite with different components is not pooled with the
  target composite. It is reported as that trial's registered primary result.

## 3 - Eligibility criteria

**Include** a study if all four axes hold:

- **Population:** adults with atrial fibrillation.
- **Intervention:** assignment to an early rhythm-control strategy, where rhythm
  control may use antiarrhythmic drugs, ablation, cardioversion, or escalation
  between them as part of a strategy.
- **Comparator:** usual care, standard care, or rate-control-oriented care
  without assignment to the early rhythm-control strategy.
- **Measure:** a time-to-first-event hazard ratio for the same cardiovascular
  composite at the same component definition, or a trial's own registered primary
  composite when the review is reporting registered primaries without pooling.

**Exclude** on any single failed axis -- population, intervention, comparator, or
measure -- and record which axis failed and what the study reports instead. No
other exclusion axis is available for study selection in this protocol.

Trials of one rhythm-control procedure against another rhythm-control procedure
are excluded on the comparator axis. Trials in which every randomized group
receives rhythm control are not trials of adopting an early rhythm-control
strategy against usual care.

Populations narrower than the question are not indirect on that ground alone;
narrowness is recorded and carried into the GRADE indirectness domain rather than
used as an exclusion.

Any axis read from a registry title is provisional until the registered primary
outcome measure is read from the outcome module. A title is not an outcome
definition.

## 4 - Information sources

PubMed, accessed through NCBI E-utilities, and ClinicalTrials.gov API v2 are the
only information sources for this registered search.

Embase was not searched. CENTRAL was not searched. Web of Science was not
searched. Scopus was not searched. This is not a comprehensive search and will
not be described as one.

The cost of those omissions is real: conference records, trial reports indexed
outside PubMed, records captured only in CENTRAL, and citation-network records
can be missed. A trial absent from this search is therefore not evidence that the
trial does not exist. It is evidence only that this limited PubMed plus
ClinicalTrials.gov search did not retrieve it.

## 4A - Linkage method and its known failure modes

Registry records and publications are linked before extraction by recorded,
checkable identifiers, not by memory.

For each ClinicalTrials.gov candidate, the NCT identifier is read from
`protocolSection.identificationModule.nctId`. Candidate publications are then
sought in two ways: PubMed E-utilities queries using the NCT identifier and trial
name/acronym, and ClinicalTrials.gov `referencesModule.references` entries. A
ClinicalTrials.gov reference marked `reference_type='result'` is treated as a
candidate link, not as proof.

A link is accepted only when the registry record and publication match on the
trial identity. Acceptable confirmation includes the NCT identifier in the
publication or abstract, or a concordant match on acronym/name, randomized arms,
population, and registered primary outcome. When those checks conflict, the link
fails closed and the conflict is recorded.

Two failure modes are known and measured on this corpus before the search runs.

First, PubMed silently DROPS trials from ID-based queries when the record is not
indexed, so an absent result is indistinguishable from a trial that does not
exist. An empty PubMed result for an NCT query is therefore never used as evidence
that the trial is absent or invalid.

Second, registry `reference_type='result'` links can point at the WRONG paper,
which is worse than a missing link because a wrong link looks like a successful
one. A posted registry result reference is therefore verified against trial
identity before use.

Where linkage succeeds, registry data matched the publication in 26 of 28
analyses compared on this corpus. That is a conditional figure whose denominator
is linked analyses, not all analyses, and therefore not a general reliability
rate for registries, publications, PubMed, or this review.

## 5 - Search strategy - the exact strings to be executed

These strings are stated before execution. The search lane will record what it
actually ran, on what date, with what filters, and how many records each returned;
any departure from the strings below will be recorded as a departure rather than
silently substituted. Each Boolean string is deliberately kept below 20 Boolean
operators because the interface refuses more; a registered string that cannot be
executed would force a departure on the first attempt.

**PubMed via NCBI E-utilities**

```
("atrial fibrillation"[MeSH Terms] OR "atrial fibrillation"[tiab])
AND ("early rhythm control"[tiab] OR "rhythm control"[tiab] OR antiarrhythmic[tiab] OR ablation[tiab])
AND ("usual care"[tiab] OR "rate control"[tiab] OR "standard care"[tiab])
AND (randomized controlled trial[pt] OR randomized[tiab] OR randomised[tiab] OR trial[tiab])
```

Filters: none on language, none on date, none on publication type beyond the
terms embedded in the query.

**ClinicalTrials.gov API v2**

```
query.cond=atrial fibrillation
query.intr=early rhythm control OR rhythm control OR antiarrhythmic OR catheter ablation
filter.advanced=AREA[StudyType]INTERVENTIONAL
```

Filters: no date filter, no recruitment-status filter, no country filter, no
sex filter, and no age filter. Age eligibility is read during screening rather
than imposed in the query.

## 5A - How this search can fail, decided in advance

The meaning of each search outcome is fixed before execution.

**If the search reproduces the held set**, that is reported as a searched-for
result rather than as convenience. It means the registered search retrieved the
trial or trials already held by the topic object under the stated linkage and
eligibility rules.

**If the search returns additional eligible trials**, that is a finding about the
review. Each additional trial is named and included or excluded on one of the
four declared axes: population, intervention, comparator, or measure. Additional
eligible trials do not become a reason to rewrite the question silently.

**If the search returns fewer trials than the object holds**, that is a finding
about the search, never reported as the review being wrong. The pre-specified
interpretation is that the search may be too narrow, the indexing may be
incomplete, the linkage may have failed, or the registry vocabulary may not match
the clinical concept.

Worked example for the third case: the finerenone-cv registry query missed
FIGARO-DKD (NCT02545049), a pivotal trial, because it registers its condition as
`Diabetic Kidney Disease` alone while its sibling FIDELIO-DKD registers `Chronic
Kidney Disease`. A narrow query looks exactly like a wrong review.

## 6 - Study selection process

Two independent screeners of different model families will screen the records.
The cross-family rule is a requirement, not a preference, because two instances
of one model is one screener run twice and its agreement statistic is
meaningless.

Screening is in two stages: title and abstract where available, then registry
record and full text. Each screener's decision is recorded per record at the
stage it was applied, together with the reason and the exclusion axis when
excluded. Both screeners' decisions are published, not only the reconciled
outcome, along with the agreement rate and how every disagreement was resolved.

Adjudication of disagreements is by a named human.

Two release tiers, and the difference between them is attestation, not content.
The website release requires the two cross-family AI assessments and states
plainly that it has not been human-verified. The submission release additionally
requires two named human reviewers to have checked every included study and every
extracted datum; the statement to that effect is emitted only when those
attestation records exist and is never written as unsupported prose.

## 7 - Data extraction

Extracted per trial and per outcome: registry identifier, primary publication,
year, design, population, arms, the analysed denominator and the randomised total
separately, per-arm event counts, and the published effect estimate with its
interval and its stated confidence level.

Every extracted cell carries a resolvable pointer to the specific document and,
where possible, to the table or registry field within it, so that a human check
can be made without leaving the page. Nothing is computed that can be read. No
count is derived from a percentage; no composite is reconstructed by summing its
components. Identifiers are resolved by lookup, never from recall.

Every candidate is classified against the four axes declared in section 3 and
against no others: population, intervention, comparator, and measure. A title can
suggest an axis, but it cannot settle one. Any axis read from a registry title is
marked provisional until the registered primary outcome measure is read from the
ClinicalTrials.gov outcome module.

Where two populations exist for one outcome, both are recorded, exactly one is
marked as selected, and the population is named on the cell.

## 8 - Outcomes and prioritisation

**Primary for reporting:** each eligible trial's own registered primary
time-to-first-event composite, with its components read from the registry outcome
module and checked against the publication.

**Primary for pooling:** only an exact shared time-to-first-event hazard ratio
for the same cardiovascular composite, if such a shared estimand exists after
the registered primary and lower-ranked registered outcomes are read.

**Components, read and reported but not pooled as the headline:**
cardiovascular death; stroke; hospitalisation; heart-failure hospitalisation;
all-cause death; and other components only when they are part of a registered
primary composite. They are shown because a reader should see them; they are not
pooled as substitutes for the registered composite unless the component-level
definition is identical.

## 9 - Risk of bias

**Tool.** Cochrane risk-of-bias tool for randomized trials, version 2 (RoB-2).

**Unit of assessment.** RoB-2 is applied to the result being reported or pooled,
not to the trial as a whole. One trial may therefore carry a different judgement
for its registered primary result than it would for another result, and that is
the intended behaviour of the tool.

**Variant.** The effect of assignment to intervention variant, because that is
what an intention-to-treat hazard ratio estimates. The adherence variant is not
used, and no result assessed under one variant will be reported as though
assessed under the other.

**Domains.** All five, each reached through the RoB-2 signalling questions rather
than by overall impression, with a recorded answer per signalling question, a
domain judgement of low / some concerns / high, and a rationale naming the
evidence it rests on:

1. Bias arising from the randomization process
2. Bias due to deviations from intended interventions (effect of assignment)
3. Bias due to missing outcome data
4. Bias in measurement of the outcome
5. Bias in selection of the reported result

An overall judgement follows the standard RoB-2 algorithm: low only if every
domain is low; high if any domain is high or if multiple domains raise some
concerns in a way that substantially lowers confidence; some concerns otherwise.

**Assessors.** Two independent assessors from different model families. Two
instances of one model is one assessor run twice and its agreement statistic is
meaningless, so same-family duplication does not satisfy this requirement.
Neither assessor may be the agent that assembled the canonical object, because
assessing one's own extraction is not an independent assessment.

Both sets of judgements are recorded and published -- per domain, per assessor,
with rationales -- not only the reconciled outcome. The per-domain agreement rate
is published as measured. Disagreements are adjudicated by a named human, and the
adjudication and its reason are recorded per disagreement.

**Evidence admissible to an assessment.** The trial's registry record including
its protocol and statistical analysis plan where posted, the primary publication
and its supplement, and the posted results module. A judgement made from an
abstract alone is not the same act as one made from a protocol, so the sources
actually consulted are recorded per domain, and a domain judged without access to
the protocol is marked as such rather than presented as equivalent.

**Relationship to the recorded bias features.** The object may hold
bias-relevant features such as open-label design, blinded endpoint adjudication,
endpoint rank within its own trial, early stopping, and analysis population.
These are inputs to the assessment and never substitutes for a domain judgement.
No existing prose in the object may stand in for a signalling question or a
domain rating.

**Feeding GRADE.** The completed RoB-2 result becomes the basis of the GRADE
risk-of-bias domain, replacing any current reasoning from recorded features. When
it does, the review will state whether the GRADE rating moves and why -- and if
it does not move, will say so explicitly rather than leaving the reader to infer
that nothing changed.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No RoB-2 assessment exists for this protocol. Performing it
later executes this section rather than amending it, and the object will record
that distinction.

## 10 - Synthesis methods

The first synthesis decision is whether synthesis is permitted at all. Registered
primary composites are pooled only when they share the same estimand: same
event-time family, same effect measure, same comparator contrast, and same
component definition. A shared label such as cardiovascular composite is not
enough.

Where a valid pool exists, random-effects meta-analysis is run on the log
hazard-ratio scale, inverse-variance weighted.

Pre-specified, so that reporting a disagreement between methods is a commitment
rather than a post-hoc observation:

- REML is the headline between-study-variance estimator.
- The Hartung-Knapp-Sidik-Jonkman interval is reported alongside the Wald
  interval, and where the two disagree about whether the interval crosses the
  null, that disagreement is reported in the results rather than resolved by
  choosing one.
- Leave-one-out analysis is run and reported for every pool.
- An estimator comparison -- DerSimonian-Laird, REML, Paule-Mandel -- is run and
  reported, per Cochrane Handbook v6.5 section 10.10.4.4, on the understanding
  that with few studies the choice is plausibly influential.
- A prediction interval is reported using the t distribution on k - 1 degrees of
  freedom per Handbook v6.5, and is not reported where k makes it undefined.
- The analysis is cross-checked in a second engine, R with metafor, at build time
  and the comparison published, including any quantity on which the two engines
  disagree by definition rather than by error.

Heterogeneity: tau-squared, I-squared with its Q-profile confidence interval, and
Q with its degrees of freedom and p value. I-squared is reported with the caveat
that at small k a low value reflects imprecision as much as agreement.

## 10A - Why the registered primaries do not pool

This review's title names the reason in advance: the strategy trials' registered
primary outcomes are not automatically one meta-analysis because their registered
primary composites do not necessarily define the same event.

The pooling rule is mechanical. Each registered primary outcome is read from the
ClinicalTrials.gov outcome module, not inferred from the registry title, paper
title, abstract wording, or clinical familiarity. Its components are recorded.
Only outcomes with the same time-to-first-event structure, effect measure,
comparator contrast, and component definition may enter the same primary pool.

If the four registered primaries differ at the component level, the review will
report that fact as the result of the eligibility and extraction rules rather
than repair it by relabelling them as a shared cardiovascular composite. If a
lower-ranked registered outcome is checked for a shared estimand, that check is
recorded before use, and a missing lower-ranked outcome remains missing rather
than being replaced by an unregistered reconstruction.

No composite is rebuilt by adding components. No component is silently dropped to
make a pool possible. No single trial result is duplicated into more than one
headline.

## 11 - Subgroup and sensitivity analyses

Sensitivity, pre-specified: leave-one-out; the estimator comparison above; and,
where per-arm counts are recovered, the same 2-by-2 data pooled as a risk ratio,
an odds ratio and a risk difference -- reported as sensitivity to the primary
hazard-ratio pool, never as the headline.

Subgroup: none pre-specified. With the small number of trials expected for this
comparison, any subgroup contrast would be underpowered and post-hoc, and none
will be presented as though it were planned.

## 12 - Meta-bias assessment

Funnel plot, Egger's regression and -- for any count-based pool -- Peters' test.
Pre-specified caveat: below approximately ten studies these tests have almost no
power and the Cochrane Handbook advises against interpreting them. Where k is
below that threshold the tests may still be computed for completeness, and will
be reported as computed values, explicitly not as evidence about small-study
effects. Where publication bias cannot be assessed, the GRADE domain will read
not assessable rather than not serious -- the two are different statements.

## 13 - Certainty of the evidence

GRADE, per Cochrane Handbook v6.5 sections 14.2.1-14.2.2 and MECIR C74/C75. All
five downgrade domains are assessed and each rating is published with the
evidence it rests on; the overall certainty is computed from the domains and
shown against them so a reader can check the arithmetic.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No GRADE assessment exists for this protocol. Performing it
later executes this section rather than amending it, and the object will record
that distinction.

## 14 - Data sharing and reproducibility

The canonical data object from which every number on the review page is projected
is published with the review, together with the search record, linkage decisions,
screening decisions, extraction file, R session information, and the analysis
scripts actually executed. The intent is that the review can be rebuilt from the
object alone.

The protocol file contains no search results, no search yields, and no counts
from any search. Search yields belong in the later anchored search record, not in
this registration.

## 15 - Funding and conflicts of interest

No funding was received for this review. No competing interests are declared by
the authors of this protocol at the time of this commit. No PROSPERO number is
asserted. Any change is to be recorded as an amendment rather than by editing
this section silently.

## 16 - Amendments

No amendments exist at first registration.

Amendments will be recorded as further commits to this file; the full commit
history, not only its head, is projected onto the review page, because a log that
displays only its own head is no better than a mutable document.
