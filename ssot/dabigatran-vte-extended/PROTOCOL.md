# Protocol - Dabigatran for extended secondary prevention after venous thromboembolism

**Status: RETROSPECTIVELY REGISTERED BY COMMIT. This document is the
registration.**

This protocol is registered as a commit in a public repository rather than in
PROSPERO. The commit hash binds the text; the repository is public. This
document is written before the search runs and contains no results, no yields,
and no counts from any search.

**The commit timestamp is the weak half, and this document will not pretend
otherwise.** The commit timestamp is author-supplied and forgeable: git author
and committer dates are set by whoever makes the commit, and commits here are
unsigned.

What the mechanism supports, and no more: this exact text is bound to this hash,
and the repository is public, so the text is readable by anyone at that hash. A
public transparency-log entry gives an inclusion time set by a third party,
proving something narrow: THE TEXT EXISTED NO LATER THAN THE LOG TIME. Not when
the commit was made, not that no earlier version existed elsewhere, and not what
was already known.

What it does not support: it does not prove when the commit was made, it does
not prove that no earlier or parallel version existed elsewhere, it does not
prove the data had not already been seen, and it says nothing about the
independence of the people who wrote it. Those are claims about conduct, and no
timestamp can carry them.

**How to check this without us.** The verification recipe, the public half of the signing key, and a worked example are at [`ssot/registration/VERIFY.md`](../registration/VERIFY.md). It states the limitation plainly as well: the log time is independent of us, the key custody is not. A stranger can verify the text existed by the log time and that we signed it; a stranger cannot verify we did not hold an earlier version.

**It is written before the search runs, but after the object already held
trials.** This protocol is committed, pushed, and anchored in a public
transparency log BEFORE the search runs. The ordering test this review publishes
uses the earliest query time, including a failed attempt, rather than the first
successful one, because reporting only the successful execution would move the
first-query time later and flatter the claim.

The search record will itself be anchored afterwards, so two third-party times
bracket the operation: one before the first query attempt, and one after the
search record exists. Both local execution times are read from the search lane's
own clock. The databases return records and hit counts, not authoritative
timestamps for our act of searching. The sequence is therefore auditable and
bounded by third-party log times, and it is recorded here as less than proof.

This is a retrospectively registered protocol. The anchor proves WHEN this text
was written and CANNOT prove the trials had not already been seen. A timestamp
bounds when, never what was known.

---

## 1 - Review question, in PICO

This topic already holds 2 trials: NCT00329238 and NCT00558259. The review
question is being authored after that evidence was assembled. However carefully
it is written now, this is a retrospectively registered protocol, and the anchor
proves WHEN this text was written and CANNOT prove the trials had not already
been seen. A timestamp bounds when, never what was known.

| | |
|---|---|
| **Population** | Adults who have completed anticoagulation for venous thromboembolism. |
| **Intervention** | Extended dabigatran. |
| **Comparator** | The comparator each trial actually randomised against. |
| **Outcome** | Recurrent venous thromboembolism, using the trial's registered recurrence definition. |
| **Study design** | Randomised controlled trials. |

**Frozen question:** In adults who have completed anticoagulation for venous
thromboembolism, does extended dabigatran reduce recurrence compared with the
comparator each trial actually randomised against?

## 2 - Estimand, stated in advance

The estimand is the **randomised contrast for recurrent venous thromboembolism
after completion of initial anticoagulation**, with the participant as the unit
of analysis and the comparator defined within each trial rather than imposed
across trials after the fact.

The primary effect measure is the measure reported for the trial's registered
recurrent-VTE outcome, provided it is a randomized comparative result. If a
trial reports a time-to-first recurrent-event hazard ratio, it is stored as a
hazard ratio. If a trial reports arm-level recurrence counts and denominators,
the count-based contrasts are computed only as specified sensitivity measures.

**Quantities that cannot be converted into this estimand are excluded on the
MEASURE axis, not on grounds of quality.** This is registered because it is a
criterion and not a judgement made after seeing results. A trial may be large,
well conducted and directly relevant to anticoagulation and still fail this
review's eligibility because it reports something else. Specifically and in
advance:

- A safety outcome, laboratory outcome, bleeding-only outcome, or adherence
  outcome is not recurrent VTE and will not determine inclusion in the primary
  analysis.
- A prophylaxis trial before completion of initial anticoagulation is not this
  population even if the drug and disease area match.
- A non-randomized comparison, extension cohort without a randomized comparator,
  or before-after comparison is not this estimand.
- A composite whose recurrence component cannot be separated or audited against
  the registered outcome definition is not silently substituted for recurrent
  VTE.

## 3 - Eligibility criteria

**Include** a study if all four hold: it is randomised; it enrols adults who
have completed anticoagulation for venous thromboembolism; it randomises
extended dabigatran against a comparator defined by the trial; and it reports
recurrent venous thromboembolism or a directly stated recurrence-containing
registered outcome with extractable randomized comparative data.

**Exclude** on any single failed axis - population, intervention, comparator, or
measure - and record which axis failed and what the study reports instead.

The canonical object already names NCT00329238 and NCT00558259 as trials held
by this topic. Held status is not automatic inclusion in the synthesis: each
trial must still pass the axes above, and any searched record must pass the same
axes before it can enter the analysis.

Populations narrower than the question, such as a subgroup defined by index VTE
type or prior anticoagulant exposure, are **not** indirect on that ground alone.
Narrowness is recorded and carried into the GRADE indirectness domain rather
than used as an exclusion unless the population did not complete initial VTE
anticoagulation.

Any axis read from a registry TITLE is provisional until the registered primary
outcome measure is read from the outcome module. A title is not an outcome
definition.

## 4 - Information sources

PubMed (NCBI E-utilities) and ClinicalTrials.gov API v2 only.

Embase was NOT searched, nor CENTRAL, Web of Science or Scopus. This is not a
comprehensive search. The cost of the omission is that records indexed only in
the omitted services, conference material present only there, non-PubMed
bibliographic records, and citations missed by the stated PubMed and
ClinicalTrials.gov strings may be absent from the review.

Only open-access records and documents are admissible as evidence for
extraction. Memory is not evidence, and no paywalled text will be treated as
source material unless an openly accessible copy is available and cited.

## 4A - Linkage method and its known failure modes

Before the search runs, registry records will be linked to publications by this
ordered method:

1. Read the ClinicalTrials.gov API v2 record for the NCT identifier.
2. Extract registry references that assert a publication link, including
   reference records whose type is marked as result.
3. Query PubMed through NCBI E-utilities by NCT identifier and by any PMID
   supplied in the registry record.
4. Accept a link only when the publication and registry match on the trial
   identifier or on enough design fields to make the link auditable: population,
   intervention, comparator, outcome definition, trial acronym or registration
   identifier, and trial timing.
5. Record the link source and the fields that supported the match.

Two failure modes are known before execution and are measured on this corpus.
First, PubMed silently DROPS trials from ID-based queries when the record is not
indexed, so an absent result is indistinguishable from a trial that does not
exist. Second, registry reference_type='result' links can point at the WRONG
paper, which is worse than a missing link because a wrong link looks like a
successful one.

Where linkage succeeds, registry data matched the publication in 26 of 28
analyses compared on this corpus. That is a conditional figure whose denominator
is LINKED analyses, not all analyses, and therefore not a general reliability
rate.

## 5 - Search strategy - the exact strings to be executed

These strings are stated **before** execution. The search lane will record what
it actually ran, on what date, with what filters, and how many records each
returned; any departure from the strings below will be recorded as a departure
rather than silently substituted.

Each string is kept under 20 Boolean operators because the interface refuses
more, and a registered string that cannot be executed would force a departure on
the first attempt.

**PubMed (NCBI E-utilities): topic search**

```
(dabigatran[tiab] OR "dabigatran etexilate"[tiab] OR Pradaxa[tiab])
AND ("venous thromboembolism"[tiab] OR VTE[tiab] OR "pulmonary embolism"[tiab] OR "deep vein thrombosis"[tiab])
AND (extended[tiab] OR secondary[tiab] OR recurrence[tiab] OR recurrent[tiab])
AND (randomized controlled trial[pt] OR randomized[tiab] OR randomised[tiab] OR trial[tiab])
```

Filters: none on language, none on date. Rationale: a language or date filter
would narrow the record set for reasons not part of the eligibility criteria.

**PubMed (NCBI E-utilities): known-identifier resolution**

```
NCT00329238[si] OR NCT00558259[si]
```

**ClinicalTrials.gov (API v2): topic search**

```
query.intr=dabigatran OR dabigatran etexilate OR Pradaxa
query.cond=venous thromboembolism OR pulmonary embolism OR deep vein thrombosis
query.term=extended OR recurrence OR recurrent OR secondary prevention
```

**ClinicalTrials.gov (API v2): known-identifier resolution**

```
query.id=NCT00329238 OR NCT00558259
```

No Embase, CENTRAL, Web of Science, Scopus, backward citation search, forward
citation search, or registry outside ClinicalTrials.gov is registered for this
review.

## 5A - How this search can fail, decided in advance

The meaning of the search result is fixed before execution, because choosing the
interpretation after seeing the result is the defect this registration is meant
to prevent.

**A. The search reproduces the held set.** That means the held set was
searched-for rather than convenient. It does not change the retrospective status
and does not prove the held set was unknown before this text.

**B. The search returns additional eligible trials.** That is a finding about
the REVIEW. Each additional trial will be named and then included or excluded on
a stated eligibility axis from Section 3.

**C. The search returns fewer trials than the object holds.** That is a finding
about the SEARCH, never reported as the review being wrong. Worked example: the
finerenone-cv registry query missed FIGARO-DKD (NCT02545049), a pivotal trial,
because it registers its condition as "Diabetic Kidney Disease" alone while its
sibling FIDELIO-DKD registers "Chronic Kidney Disease". A narrow query looks
exactly like a wrong review.

## 6 - Study selection process

Two **independent screeners of different model families** - the cross-family
rule is a requirement, not a preference, because two instances of one model is
one screener run twice and its agreement statistic is meaningless.

Screening is in two stages: title and abstract, then full text or registry
record. **Each screener's decision is recorded per record at the stage it was
applied**, together with the reason. Both screeners' decisions are published,
not only the reconciled outcome, along with the agreement rate and how every
disagreement was resolved.

**Adjudication of disagreements is by a named human.**

**Two release tiers, and the difference between them is attestation, not
content.** The website release requires the two cross-family AI assessments and
states plainly that it has not been human-verified. The submission release
additionally requires two named human reviewers to have checked every included
study and every extracted datum; the statement to that effect is emitted only
when those attestation records exist and is never written as prose.

## 7 - Data extraction

Extracted per trial and per outcome: registry identifier, primary publication,
year, design, population, arms, comparator, outcome definition, follow-up
timepoint, **the analysed denominator and the randomised total separately**,
per-arm recurrent-VTE event counts where reported, and the published effect
estimate with its interval and its stated confidence level.

Every extracted cell carries a resolvable pointer to the specific document and,
where possible, to the table, figure, registry module, or outcome field within
it, so that a human check can be made without leaving the page. **Nothing is
computed that can be read.** No count is derived from a percentage; no composite
is reconstructed by summing its components. Identifiers are resolved by lookup,
never from recall.

Eligibility classification is made against the axes declared in Section 3 and
against those axes only: population, intervention, comparator, and measure. Any
axis read from a registry TITLE is provisional until the registered primary
outcome measure is read from the outcome module: a title is not an outcome
definition.

Where two populations exist for one outcome - for example a full analysis set
and a randomised set - both are recorded, exactly one is marked as selected, and
the population is named on the cell.

No invented trial data, effect sizes, counts, or PROSPERO numbers are permitted.

## 8 - Outcomes and prioritisation

**Primary:** recurrent venous thromboembolism using the trial's registered
recurrence definition, compared between extended dabigatran and the comparator
actually randomised in the trial.

**Secondary, read and reported but not substituted for the primary outcome:**
VTE-related death where separately reported; major bleeding; clinically relevant
non-major bleeding; all-cause mortality; treatment discontinuation; and
laboratory safety outcomes. They are shown where available because a reader
should see them. They are not pooled as the headline because the review's
estimand is recurrent VTE.

## 9 - Risk of bias

**Tool.** Cochrane risk-of-bias tool for randomized trials, version 2 (RoB-2).

**Unit of assessment.** RoB-2 is applied **to the result being pooled, not to the
trial as a whole**: recurrent venous thromboembolism, expressed on the
randomized comparative scale selected for synthesis. One trial may therefore
carry a different judgement for this result than it would for a safety endpoint,
and that is the intended behaviour of the tool.

**Variant.** The **effect of assignment to intervention** variant, because this
review estimates the effect of allocation to extended dabigatran. The adherence
variant is not used, and no result assessed under one variant will be reported
as though assessed under the other.

**Domains.** All five, each reached through the RoB-2 signalling questions
rather than by overall impression, with a recorded answer per signalling
question, a **domain judgement** of low / some concerns / high, and a rationale
naming the evidence it rests on:

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
agreement rate is published as measured**. Agreement on RoB-2 domains is
expected to be substantially lower than agreement on screening; if that proves
true it is a finding worth reporting and it will not be smoothed.
**Disagreements are adjudicated by a named human**, and the adjudication and its
reason are recorded per disagreement.

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

Each trial is first analysed as its own randomised comparison against the
comparator it actually randomised. If two or more eligible trials share the same
population, intervention, comparator family, outcome definition, and effect
measure closely enough to answer one clinical question, they are pooled on the
log scale using inverse-variance weighting.

If compatible time-to-first-event hazard ratios are available, the primary pool
uses the log hazard-ratio scale. If compatible arm-level recurrence counts and
denominators are available but hazard ratios are not, count-based contrasts are
reported as sensitivity analyses rather than silently replacing a reported
hazard ratio. If no pool is possible without combining unlike comparator
families or unlike outcome definitions, the review reports the eligible studies
narratively and states that the planned pool was not executed.

**Stated before execution, so that reporting a disagreement between methods is a
commitment rather than a post-hoc observation:**

- **REML** is the headline between-study-variance estimator where a
  random-effects pool is defined.
- The **Hartung-Knapp-Sidik-Jonkman interval is reported alongside** the Wald
  interval, and where the two disagree about whether the interval crosses the
  null, that disagreement is reported in the results rather than resolved by
  choosing one.
- **Leave-one-out** analysis is run and reported for every pool where it is
  defined.
- An **estimator comparison** - DerSimonian-Laird, REML, Paule-Mandel - is run
  and reported, per Cochrane Handbook v6.5 Section 10.10.4.4, on the
  understanding that with few studies the choice is plausibly influential.
- A **prediction interval** is reported using the t distribution on k-1 degrees
  of freedom per Handbook v6.5, and is not reported where k makes it undefined.
- The analysis is **cross-checked in a second engine** at build time where a
  second engine is available. Any disagreement between engines is published with
  enough detail to distinguish definitional differences from errors.

**Heterogeneity:** tau squared, I squared with its Q-profile confidence
interval, and Q with its degrees of freedom and p value, where a pool is
defined. I squared is reported with the caveat that at small k a low value
reflects imprecision as much as agreement.

## 10A - Comparator geometry and what it forbids

This is a trial-level comparator review, not a network meta-analysis. Each trial
is first read against the comparator it actually randomised, and the comparator
label is source-backed before any synthesis decision is made.

The current object records two different comparator families across the two held
trials: placebo and vitamin K antagonist. A shared disease area and shared
dabigatran intervention do not make those one estimand. A single headline pool
across those comparator families is therefore forbidden unless the object is
amended with a source-backed justification that the comparison still answers one
clinical question; that amendment would be reported as an amendment, not a
silent analysis choice.

This section forbids four shortcuts in advance: treating every non-dabigatran
arm as the same comparator without reading it; relabelling placebo, no extended
anticoagulation, warfarin, vitamin K antagonist therapy, or another active
regimen as equivalent by convenience; making an indirect comparison between
comparator families while describing it as a direct randomized estimate; and
pooling trials whose registered recurrent-VTE outcome definitions differ in a
way that changes the event counted.

## 11 - Subgroup and sensitivity analyses

**Sensitivity, stated before execution:** leave-one-out where defined; the
estimator comparison above; and, where per-arm counts are recovered, the same
2x2 data analysed as a risk ratio, an odds ratio and a risk difference -
reported as sensitivity to the primary comparative effect, never as the
headline.

**Subgroup: none specified.** With the small number of trials this comparison
has, any subgroup contrast would be underpowered and post-hoc, and none will be
presented as though it were planned.

## 12 - Meta-bias assessment

Funnel plot, Egger's regression and - for any count-based pool - Peters' test.
**Stated caveat:** below approximately ten studies these tests have almost no
power and the Cochrane Handbook advises against interpreting them. Where k is
below that threshold the tests may still be computed for completeness, and will
be reported as computed values, explicitly not as evidence about small-study
effects. Where publication bias cannot be assessed, the GRADE domain will read
*not assessable* rather than *not serious* - the two are different statements.

## 13 - Certainty of the evidence

GRADE, per Cochrane Handbook v6.5 Sections 14.2.1-14.2.2 and MECIR C74/C75. All
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

The protocol registration anchor, the search execution record, and the
post-search anchor are part of the reproducibility record. The pre-search anchor
does not change the retrospective status; it brackets the search after the
topic object already held trials.

| Item | Static or dynamic | Disclosure |
|---|---|---|
| Review question, eligibility axes, information sources, search strings, linkage method, synthesis rules | Static | Fixed in this protocol before the search runs; departures are amendments or execution departures, not silent substitutions. |
| Search yields, screened records, linkage successes or failures, extracted trial data, effect estimates, RoB-2, and GRADE | Dynamic | Produced only when the registered methods are executed; none are inserted into this protocol as registration facts. |
| Held trial identifiers | Static at this commit | The object already held NCT00329238 and NCT00558259 before this protocol was written; this is why the protocol is retrospective. |

## 15 - Funding and conflicts of interest

**No funding was received for this review.** No competing interests are declared
by the authors of this protocol at the time of this commit. Any change is to be
recorded as an amendment rather than by editing this section.

## 16 - Amendments

No amendments exist at the time this protocol is first written.

Amendments will be recorded as further commits to this file; the full commit
history, not only its head, is projected onto the review page, because a log
that displays only its own head is no better than a mutable document.
