# Protocol -- Dabigatran for cerebral venous and dural sinus thrombosis

**Status: RETROSPECTIVELY REGISTERED BY COMMIT. This document is the
retrospectively registered protocol.**

This protocol is registered as a commit in a public repository rather than in
PROSPERO. The commit hash is the strong half of that record: the content is
immutable under it, so this text cannot be altered later without producing a
different hash, and anyone can check that much without asking us.

**The commit timestamp is the weak half, and this document will not pretend
otherwise.** Both the author and the committer date on a git commit are supplied
by whoever makes the commit and can be set to any value; GitHub stores and
displays what it is given, and an unsigned commit carries nothing further. The
commit hash binds the text; the repository is public. The commit timestamp is
author-supplied and forgeable because git author and committer dates are set by
whoever makes the commit and commits here are unsigned.

A transparency-log entry gives an inclusion time set by a third party, proving
something narrow: **the text existed no later than the log time**. It does not
prove when the commit was made, that no earlier version existed elsewhere, or
what was already known. The anchor proves when this text was written and cannot
prove the trials had not already been seen. A timestamp bounds when, never what
was known.

What the mechanism supports, and no more: this exact text is bound to this hash;
the repository is public, so the text is readable by anyone at that hash; and
where an entry for the commit exists in a public transparency log, that log's
inclusion time is an upper bound on when this text existed.

What it does not support: it does not prove the commit was made when it says it
was, it does not prove that no earlier or parallel version existed elsewhere, it
does not prove the data had not already been seen, and it says nothing about the
independence of the people who wrote it. Those are claims about conduct, and no
timestamp can carry them.

**How to check this without us.** The verification recipe, the public half of the signing key, and a worked example are at [`ssot/registration/VERIFY.md`](../registration/VERIFY.md). It states the limitation plainly as well: the log time is independent of us, the key custody is not. A stranger can verify the text existed by the log time and that we signed it; a stranger cannot verify we did not hold an earlier version.

**It is written before this search runs, but after this topic already held
trials.** The ordering test this review publishes is that this protocol commit is
committed, pushed and anchored before the first executed query: the first
attempt, including a failed attempt, not the first success, because reporting only
the successful execution would move the first-query time later and flatter the
claim. The search record is anchored afterwards, so two third-party times bracket
the operation.

Both query times are read from the search lane's own clock. The databases return
records and hit counts, not execution times, so no query time is timestamped by a
third party unless an external anchor is placed on each end. The sequence is
therefore auditable and internally consistent, and the third-party anchors prove
only the narrow claims they can prove: that the registered text existed no later
than the first anchor time, and that the search record existed no later than the
second anchor time.

---

## 1 - Review question, in PICO

| | |
|---|---|
| **Population** | Adults with cerebral venous thrombosis, cerebral venous sinus thrombosis, or dural sinus thrombosis. |
| **Intervention** | Dabigatran or dabigatran etexilate. |
| **Comparator** | The comparator each trial actually randomised against. |
| **Outcome** | The endpoint that trial registered as its primary outcome, read from the outcome module rather than inferred from the title alone. |
| **Study design** | Randomised controlled trials. |

**Frozen question:** in adults with cerebral venous or dural sinus thrombosis,
does dabigatran compare favourably with the comparator each trial actually
randomised against, on the endpoint that trial registered?

This is a retrospectively registered protocol. This topic already holds 5 trials:
NCT02913326, NCT03217448, NCT06551402, NCT06551415, and NCT07352358. The question
is being authored after that evidence was assembled. However carefully it is
written now, it cannot change that timing.

## 2 - Estimand, stated in advance

The estimand is trial-specific rather than pooled across the whole reading:
dabigatran versus the comparator actually randomised in that trial, for the
trial's registered primary endpoint as defined in the registry outcome module.

The unit of analysis is the randomised participant unless the registry or
publication names a different analysis population for that registered primary
endpoint. If a trial reports a time-to-event estimate, a risk contrast, a rate
contrast, a recanalisation proportion, or a composite safety-efficacy endpoint,
the measure is recorded as reported and is not converted into another estimand.

**Quantities that cannot be compared on a common scale are not pooled.** This is
pre-stated because it is a method rule and not a judgement made after seeing
results. A trial may be eligible for the review and still fail any particular
pool because its comparator, endpoint definition, or effect measure differs.

## 3 - Eligibility criteria

**Include** a study if all four hold: it is randomised; it enrols adults with
cerebral venous thrombosis, cerebral venous sinus thrombosis, or dural sinus
thrombosis; it includes a dabigatran or dabigatran-etexilate arm; and it records
or reports the primary endpoint that the trial registered.

**Exclude** on any single failed axis -- population, intervention, comparator, or
measure -- and record which axis failed and what the study reports instead.

The comparator axis is descriptive, not exclusionary by itself: trials may compare
dabigatran with warfarin, another direct oral anticoagulant, standard care, or
another randomised anticoagulation strategy, but each trial is interpreted only
against the comparator it actually randomised.

Any axis read from a registry title is provisional until the registered primary
outcome measure is read from the outcome module. A title is not an outcome
definition.

Populations narrower than the question are **not** indirect on that ground alone;
narrowness is recorded and carried into the GRADE indirectness domain rather than
used as an exclusion.

## 4 - Information sources

PubMed through NCBI E-utilities and ClinicalTrials.gov API v2 are the only
information sources for this registered search.

Embase was **not** searched. CENTRAL was **not** searched. Web of Science was
**not** searched. Scopus was **not** searched. This search is not comprehensive.
The cost of those omissions is known in advance: eligible trials or publications
indexed outside PubMed, trial reports not linked from ClinicalTrials.gov, and
conference or regional-index records may be missed. Any such miss is a limitation
of the search, not evidence that the trial does not exist.

## 4A - Linkage method and its known failure modes

Registry records will be linked to publications before results are extracted by
using explicit identifiers first and inference only as a checked fallback.

The linkage order is:

1. Query PubMed for the NCT identifier and inspect returned records for a direct
   match to the registry record.
2. Read ClinicalTrials.gov API v2 reference entries, including entries marked
   `reference_type='result'`.
3. Accept a registry-to-publication link only when the publication matches the
   registry on the NCT identifier or, if the identifier is absent from PubMed, on
   trial design, population, intervention, comparator, and registered outcome.
4. Record unresolved publication links as unresolved rather than approximating
   them from title similarity.

Two failure modes are named before this search because they have already been
measured on this corpus.

First, PubMed silently drops trials from ID-based queries when the record is not
indexed, so an absent result is indistinguishable from a trial that does not
exist.

Second, registry `reference_type='result'` links can point at the wrong paper,
which is worse than a missing link because a wrong link looks like a successful
one.

Where linkage succeeds, registry data matched the publication in 26 of 28
analyses compared on this corpus. That is a conditional figure whose denominator
is linked analyses, not all analyses, and therefore it is not a general
reliability rate.

## 5 - Search strategy -- the exact strings to be executed

These strings are stated **before** execution. The search lane will record what it
actually ran, on what date, with what filters, and how many records each returned;
any departure from the strings below will be recorded as a departure rather than
silently substituted. Each string is kept under 20 Boolean operators because an
unexecutable registered string would force a departure on the first attempt.

**PubMed, through NCBI E-utilities**

```
(dabigatran[tiab] OR "dabigatran etexilate"[tiab] OR Pradaxa[tiab])
AND ("cerebral venous thrombosis"[tiab] OR "cerebral vein thrombosis"[tiab] OR "dural sinus thrombosis"[tiab] OR "cerebral venous sinus thrombosis"[tiab] OR CVT[tiab] OR CVST[tiab])
AND (randomized[tiab] OR randomised[tiab] OR trial[tiab])
```

Filters: none on language, none on date. Rationale: a language or date filter
would make the search narrower than the question and would hide whether the
source set depends on indexing rather than eligibility.

**ClinicalTrials.gov API v2**

```
query.intr=dabigatran OR dabigatran etexilate
query.cond=cerebral venous thrombosis OR cerebral vein thrombosis OR dural sinus thrombosis OR cerebral venous sinus thrombosis
```

Filters: none on recruitment status, phase, funder type, country, language, or
date. Rationale: recruitment status is not an eligibility criterion, and the aim
is to test the held object against the registry search rather than pre-trim it to
completed studies.

## 5A - How this search can fail, decided in advance

Every search outcome is interpreted before execution.

**If the search reproduces the held set**, the held trials are reported as
searched-for rather than convenient. This does not change the protocol timing
and does not prove no eligible record exists elsewhere.

**If the search returns additional eligible trials**, that is a finding about the
review. Each additional trial is named and included or excluded on one of the
pre-stated axes: population, intervention, comparator, or measure.

**If the search returns fewer trials than the object holds**, that is a finding
about the search, never reported as the review being wrong. Registry search terms
can miss known trials when condition coding differs from the review's language.
Worked example: the finerenone-cv registry query missed FIGARO-DKD
(NCT02545049), a pivotal trial, because it registers its condition as "Diabetic
Kidney Disease" alone while its sibling FIDELIO-DKD registers "Chronic Kidney
Disease". A narrow query looks exactly like a wrong review.

## 6 - Study selection process

Two **independent screeners of different model families** -- the cross-family rule
is a requirement, not a preference, because two instances of one model is one
screener run twice and its agreement statistic is meaningless.

Screening is in two stages: title and abstract where a publication record exists,
then full text or full registry record. **Each screener's decision is recorded per
record at the stage it was applied**, together with the reason. Both screeners'
decisions are published, not only the reconciled outcome, along with the
agreement rate and how every disagreement was resolved.

**Adjudication of disagreements is by a named human.**

**Two release tiers, and the difference between them is attestation, not content.**
The website release requires the two cross-family AI assessments and states
plainly that it has not been human-verified. The submission release additionally
requires two named human reviewers to have checked every included study and every
extracted datum; the statement to that effect is emitted only when those
attestation records exist and is never written as prose.

## 7 - Data extraction

Extracted per trial and per outcome: registry identifier, primary publication if
resolved, year, design, population, arms, comparator actually randomised,
registered primary outcome title, registered primary outcome definition from the
outcome module, time frame, analysed denominator and randomised total separately
where available, per-arm event or response counts where available, and the
published effect estimate with its interval and stated confidence level where
available.

Every extracted cell carries a resolvable pointer to the specific document and,
where possible, to the table or outcome module field within it, so that a human
check can be made without leaving the page. **Nothing is computed that can be
read.** No count is derived from a percentage; no composite is reconstructed by
summing its components. Identifiers are resolved by lookup, never from recall.

Selection and exclusion classifications are made against the four axes declared
in section 3 and no others: population, intervention, comparator, and measure.
Any provisional classification made from a registry title is replaced or
confirmed only after the registered primary outcome measure is read from the
outcome module.

Where two populations exist for one outcome -- for example a full analysis set
and a randomised set -- both are recorded, exactly one is marked as selected, and
the population is named on the cell.

## 8 - Outcomes and prioritisation

**Primary:** each trial's registered primary endpoint, as defined in the registry
outcome module, compared between dabigatran and the comparator that trial
randomised against.

**Components, read and reported but not pooled unless they are the registered
primary endpoint in a compatible comparator-and-measure subset:** recurrent
cerebral venous thrombosis, venous thrombotic events, major bleeding,
intracranial bleeding, cerebral venous recanalisation, and mortality.

They are shown because a reader should see them; they are not pooled unless the
population, intervention, comparator, and measure are sufficiently similar to
answer one clinically meaningful question.

## 9 - Risk of bias

**Tool.** Cochrane risk-of-bias tool for randomized trials, version 2 (RoB-2).

**Unit of assessment.** RoB-2 is applied **to the result being interpreted, not to
the trial as a whole**: the registered primary endpoint for dabigatran against
the comparator actually randomised in that trial. One trial may therefore carry a
different judgement for this result than it would for another endpoint, and that
is the intended behaviour of the tool.

**Variant.** The **effect of assignment to intervention** variant, because that
is what an intention-to-treat randomised comparison estimates. The adherence
variant is not used, and no result assessed under one variant will be reported as
though assessed under the other.

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

**Both sets of judgements are recorded and published** -- per domain, per
assessor, with rationales -- not only the reconciled outcome. The **per-domain
agreement rate is published as measured**. Agreement on RoB-2 domains is expected
to be substantially lower than agreement on screening; if that proves true it is
a finding worth reporting and it will not be smoothed. **Disagreements are
adjudicated by a named human**, and the adjudication and its reason are recorded
per disagreement.

**Evidence admissible to an assessment.** The trial's registry record including
its protocol and statistical analysis plan where posted, the primary publication
and its supplement where resolved, and the posted results module. A judgement
made from an abstract alone is not the same act as one made from a protocol, so
**the sources actually consulted are recorded per domain**, and a domain judged
without access to the protocol is marked as such rather than presented as
equivalent.

**Relationship to the recorded bias features.** The object may already hold
bias-relevant features. These are **inputs to the assessment and never
substitutes for a domain judgement**. No existing prose in the object may stand
in for a signalling question or a domain rating.

**Feeding GRADE.** The completed RoB-2 result becomes the basis of the GRADE
risk-of-bias domain, replacing any current reasoning from recorded features. When
it does, the review will state **whether the GRADE rating moves and why -- and if
it does not move, will say so explicitly** rather than leaving the reader to
infer that nothing changed.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No RoB-2 assessment exists for these trials in this protocol.
Performing it later **executes this section rather than amending it**, and the
object will record that distinction.

## 10 - Synthesis methods

The primary synthesis is narrative and tabular unless at least two trials share a
compatible population, intervention, comparator family, registered primary
endpoint definition, and effect-measure scale.

If a pool is admissible, random-effects meta-analysis is run on the natural scale
for the reported effect measure after transformation to its log scale where
standard for that measure, inverse-variance weighted.

**Pre-specified, so that reporting a disagreement between methods is a commitment
rather than a post-hoc observation:**

- **REML** is the headline between-study-variance estimator.
- The **Hartung-Knapp-Sidik-Jonkman interval is reported alongside** the Wald
  interval, and where the two disagree about whether the interval crosses the
  null, that disagreement is reported in the results rather than resolved by
  choosing one.
- **Leave-one-out** analysis is run and reported for every pool where it is
  defined.
- An **estimator comparison** -- DerSimonian-Laird, REML, Paule-Mandel -- is run
  and reported, per Cochrane Handbook v6.5 section 10.10.4.4, on the
  understanding that with few studies the choice is plausibly influential.
- A **prediction interval** is reported using the t distribution on k-1 degrees
  of freedom per Handbook v6.5, and is not reported where k makes it undefined.
- The analysis is **cross-checked in a second engine** (R with metafor) at build
  time and the comparison published, including any quantity on which the two
  engines disagree by definition rather than by error.

**Heterogeneity:** tau-squared, I-squared with its Q-profile confidence interval,
and Q with its degrees of freedom and p value. I-squared is reported with the
caveat that at small k a low value reflects imprecision as much as agreement.

If no pool is admissible, no pooled estimate is computed and the review reports
why pooling failed against the section 3 axes and the section 8 outcome rule.

## 10A - Static-vs-dynamic hardcode disclosure

| Item | Static or dynamic | Commitment |
|---|---|---|
| Topic slug, title, frozen question, and the five already-held trial IDs | Static protocol facts | Recorded because they define this retrospectively registered topic; not treated as search results. |
| PubMed and ClinicalTrials.gov search strings | Static protocol method | Written before execution; departures are logged rather than silently substituted. |
| Search yields, returned records, and execution timestamps | Dynamic execution data | Not present in this protocol; recorded only in the search record after execution. |
| Registry outcome definitions, denominators, events, and effect estimates | Dynamic source data | Read from ClinicalTrials.gov records and linked publications; unresolved cells stay unresolved. |
| RoB-2 and GRADE judgements | Dynamic assessment data | PENDING at this commit; generated only when the assessment workflow is executed. |

## 11 - Subgroup and sensitivity analyses

**Sensitivity, pre-specified:** leave-one-out where a pool exists and k makes it
defined; the estimator comparison above; and, where per-arm counts are recovered,
the same 2x2 data pooled as a risk ratio, an odds ratio and a risk difference --
reported as sensitivity to the primary synthesis, never as the headline if the
registered primary measure is different.

**Subgroup: none pre-specified.** With the small number of trials this comparison
has and the likelihood of different comparators and registered primary outcomes,
any subgroup contrast would be underpowered and post-hoc, and none will be
presented as though it were planned.

## 12 - Meta-bias assessment

Funnel plot, Egger's regression and -- for any count-based pool -- Peters' test.
**Pre-specified caveat:** below approximately ten studies these tests have almost
no power and the Cochrane Handbook advises against interpreting them. Where k is
below that threshold the tests may still be computed for completeness, and will
be reported as computed values, explicitly not as evidence about small-study
effects. Where publication bias cannot be assessed, the GRADE domain will read
*not assessable* rather than *not serious* -- the two are different statements.

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

The canonical data object from which every number on the review page is projected
is published with the review, together with the R session information and the
analysis scripts actually executed. The intent is that the review can be rebuilt
from the object alone.

The protocol commit is committed, pushed and anchored before the first search
query. The search record is committed and anchored after execution. The first
query time used for ordering is the earliest query attempt, including a failed
attempt, not the first successful query.

## 15 - Funding and conflicts of interest

**No funding was received for this review.** No competing interests are declared
by the authors of this protocol at the time of this commit. Any change is to be
recorded as an amendment rather than by editing this section.

## 16 - Amendments

Amendments will be recorded as further commits to this file; the full commit
history, not only its head, is projected onto the review page, because a log that
displays only its own head is no better than a mutable document.
