# Protocol — Bosentan alone against an inactive control in pulmonary arterial hypertension: four eligible trials, and not one registering an endpoint this review could pool

**Status: RETROSPECTIVELY REGISTERED BY COMMIT. This document is the registration.**

This protocol is registered as a commit in a public repository rather than in
PROSPERO. The commit hash is the strong half of that record: the content is
immutable under it, so this text cannot be altered later without producing a
different hash, and anyone can check that much without asking us.

**The commit timestamp is the weak half, and this document will not pretend
otherwise.** Both the author and the committer date on a git commit are supplied
by whoever makes the commit and can be set to any value. Commits here are
unsigned, so the timestamp is author-supplied and forgeable. A transparency-log
entry gives an inclusion time set by a third party, proving something narrow:
the text existed no later than the log time. It does not prove when the commit
was made, it does not prove that no earlier version existed elsewhere, and it
does not prove what was already known.

What the mechanism supports, and no more: this exact text is bound to this hash;
the repository is public, so the text is readable by anyone at that hash; and
where an entry for the commit exists in a public transparency log, that log's
inclusion time is an upper bound on when this text existed, set by a third party
rather than by us.

What it does not support: it does not prove the commit was made when it says it
was, it does not prove that no earlier or parallel version existed elsewhere, it
does not prove the data had not already been seen, and it says nothing about the
independence of the people who wrote it. Those are claims about conduct, and no
timestamp can carry them.

**How to check this without us.** The verification recipe, the public half of the signing key, and a worked example are at [`ssot/registration/VERIFY.md`](../registration/VERIFY.md). It states the limitation plainly as well: the log time is independent of us, the key custody is not. A stranger can verify the text existed by the log time and that we signed it; a stranger cannot verify we did not hold an earlier version.

**It is written before the search runs, but after the evidence object already
holds trials.** The ordering test this review publishes is that this commit is
made, pushed and anchored before the first executed query -- the first attempt,
not the first success, because reporting only the successful execution would move
the first-query time later and flatter the claim. Both times go into the
canonical object so a reader can check the sequence.

Both are read from the search lane's own clock. The databases return records and
hit counts, not trustworthy external times for our execution, so no part of the
ordering is timestamped by a third party unless an external anchor is placed on
each end. The protocol is committed, pushed and anchored before the first query.
The search record is anchored afterwards, so two third-party times bracket the
operation. The ordering test uses the earliest query time including a failed
attempt, not the first successful query.

---

## 1 · Review question, in PICO

This topic already holds four eligible trials: NCT00091715, NCT00377455,
NCT00825266 and NCT01827059. The question is being authored after that evidence
was assembled. However carefully it is written now, this is a retrospectively
registered protocol. The anchor proves when this text was written and cannot
prove the trials had not already been seen. A timestamp bounds when, never what
was known.

| | |
|---|---|
| **Population** | Adults with WHO group 1 pulmonary arterial hypertension. |
| **Intervention** | Bosentan alone. |
| **Comparator** | Placebo or no active pulmonary vasodilator. |
| **Outcome** | Exercise capacity and clinical worsening, only where the registered outcome measure establishes a poolable outcome definition. |
| **Study design** | Randomised controlled trials. |

**Frozen question:** in adults with WHO group 1 pulmonary arterial hypertension,
what is the effect of bosentan compared with placebo or no active pulmonary
vasodilator on exercise capacity and on clinical worsening?

## 2 · Estimand, stated in advance

The estimand is the trial-level effect of assignment to bosentan alone versus an
inactive control on a registered measure of exercise capacity or clinical
worsening. The preferred exercise-capacity estimand is the between-arm difference
in change from baseline in six-minute walk distance, on the natural scale. The
preferred clinical-worsening estimand is a time-to-first-event hazard ratio for a
registered clinical-worsening or morbidity/mortality composite, on the log scale.

**Quantities that cannot be converted into either estimand are excluded on the
MEASURE axis, not on grounds of quality.** This is pre-specified here because it
is a criterion and not a judgement made after seeing results. A trial may be
randomised, adult, group 1 PAH, bosentan monotherapy and placebo-controlled, and
still fail this review's eligibility for synthesis if the registered outcome
module does not define a poolable exercise-capacity change measure or a poolable
clinical-worsening result. Specifically and in advance:

- A bare phrase such as "exercise capacity" is not an outcome definition unless
  the registered primary outcome measure gives the measure, timepoint and
  direction needed to pool it.
- A haemodynamic endpoint is not exercise capacity and is not clinical
  worsening.
- Total exercise time on a stress protocol is not six-minute walk distance change.
- A metabolic or biomarker change is not exercise capacity and is not clinical
  worsening.
- A dichotomous event count at a fixed timepoint is not a time-to-first-event
  hazard ratio, though where per-arm counts are recovered it may be reported as a
  sensitivity analysis only, never as the headline clinical-worsening estimand.

## 3 · Eligibility criteria

**Include** a study if all five hold: it is randomised; it enrols adults with WHO
group 1 pulmonary arterial hypertension; it randomises bosentan monotherapy
against placebo or no active pulmonary vasodilator; it has a registry record
available through ClinicalTrials.gov API v2; and it reports or registers an
exercise-capacity or clinical-worsening measure that can be mapped to one of the
estimands in section 2.

**Exclude** on any single failed axis -- population, intervention, comparator,
registry availability or measure -- and record which axis failed and what the
study reports instead. Section 7 may classify records against those axes and no
others.

Any axis read from a registry title is provisional until the registered primary
outcome measure is read from the outcome module: a title is not an outcome
definition.

Populations narrower than the question, for example a PAH aetiology subgroup, are
**not** indirect on that ground alone if they remain WHO group 1 PAH. Narrowness
is recorded and carried into the GRADE indirectness domain rather than used as an
exclusion.

## 4 · Information sources

PubMed through NCBI E-utilities and ClinicalTrials.gov API v2 only.

Embase was not searched. CENTRAL was not searched. Web of Science was not
searched. Scopus was not searched. The search is not comprehensive. The cost of
that omission is that conference abstracts, records indexed outside PubMed,
controlled-trials records not represented in ClinicalTrials.gov, and citation
links visible only in subscription databases may be missed. A missing record in
this review is therefore evidence about this restricted search lane, not evidence
that the study cannot exist.

## 4A · Linkage method and its known failure modes

Registry records are linked to publications before extraction by a fixed order:
first, ClinicalTrials.gov references with an NCT identifier or PMID are read;
second, PubMed E-utilities is queried for the NCT identifier and bosentan/PAH
terms; third, candidate publications are accepted only when the publication and
registry agree on the NCT ID or on a combination of sponsor, intervention,
population and trial design specific enough to identify the same trial. A link
that cannot be resolved by those rules is recorded as missing rather than
reconstructed from memory.

Two linkage failure modes are known in this corpus before the search runs.
First, PubMed silently drops trials from ID-based queries when the record is not
indexed, so an absent result is indistinguishable from a trial that does not
exist. Second, registry `reference_type='result'` links can point at the wrong
paper, which is worse than a missing link because a wrong link looks like a
successful one.

Where linkage succeeds, registry data matched the publication in 26 of 28
analyses compared on this corpus. That is a conditional figure whose denominator
is linked analyses, not all analyses, and therefore it is not a general
reliability rate.

## 5 · Search strategy — the exact strings to be executed

These strings are stated **before** execution. The search lane will record what it
actually ran, on what date, with what filters, and how many records each returned;
any departure from the strings below will be recorded as a departure rather than
silently substituted. Each string is kept under the interface limit of 20 Boolean
operators.

**PubMed (NCBI E-utilities)**

```
(bosentan[tiab] OR Tracleer[tiab])
AND ("pulmonary arterial hypertension"[tiab] OR "Hypertension, Pulmonary"[MeSH Terms] OR PAH[tiab])
AND (placebo[tiab] OR "inactive control"[tiab] OR "control group"[tiab])
AND (randomized controlled trial[pt] OR randomized[tiab] OR randomised[tiab] OR trial[tiab])
```

Filters: none on language, none on date. Rationale: a language or date filter
would make this restricted search narrower than the question and would create a
silent exclusion layer outside the eligibility criteria.

**ClinicalTrials.gov (API v2)**

```
query.intr=bosentan OR Tracleer
query.cond=pulmonary arterial hypertension OR PAH
filter.overallStatus=COMPLETED|TERMINATED|ACTIVE_NOT_RECRUITING|UNKNOWN
```

**ID linkage queries**

Each trial already on the object is queried by NCT identifier in PubMed
E-utilities and by `query.id` in ClinicalTrials.gov API v2. An absent PubMed
return is not treated as proof that the trial has no publication, because section
4A names the known ID-drop failure mode.

**PubMed held-ID linkage query**

```
NCT00091715 OR NCT00377455 OR NCT00825266 OR NCT01827059
```

**ClinicalTrials.gov held-ID linkage query**

```
query.id=NCT00091715|NCT00377455|NCT00825266|NCT01827059
```

## 5A · How this search can fail, decided in advance

The meaning of every search outcome is fixed before execution.

If the search reproduces the held set, the review will report that the held set
was searched for rather than convenient. It will not imply that the restricted
lane is comprehensive.

If the search returns additional eligible trials, that is a finding about the
review. Each additional trial is named and then included or excluded on one of
the axes in section 3: population, intervention, comparator, registry
availability or measure.

If the search returns fewer trials than the object already holds, that is a
finding about the search, never reported as the review being wrong. A worked
example already known from the same operating environment is the finerenone-cv
registry query, which missed FIGARO-DKD (NCT02545049), a pivotal trial, because
it registers its condition as "Diabetic Kidney Disease" alone while its sibling
FIDELIO-DKD registers "Chronic Kidney Disease". A narrow query looks exactly like
a wrong review.

## 6 · Study selection process

Two **independent screeners of different model families** -- the cross-family
rule is a requirement, not a preference, because two instances of one model is
one screener run twice and its agreement statistic is meaningless.

Screening is in two stages: title and abstract, then full text or registry module
where no publication is linked. **Each screener's decision is recorded per record
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

## 7 · Data extraction

Extracted per trial and per outcome: registry identifier, linked publication if
any, year, design, population, arms, the analysed denominator and the randomised
total separately, per-arm event counts where reported, per-arm continuous outcome
values where reported, and the published effect estimate with its interval and
its stated confidence level.

Every extracted cell carries a resolvable pointer to the specific document and,
where possible, to the table or registry module within it, so that a human check
can be made without leaving the page. **Nothing is computed that can be read.**
No count is derived from a percentage; no composite is reconstructed by summing
its components. Identifiers are resolved by lookup, never from recall.

Each record is classified only on the axes declared in section 3: population,
intervention, comparator, registry availability and measure. Any axis read from a
registry title remains provisional until the registered primary outcome measure
is read from the outcome module. A title is not an outcome definition.

Where two populations exist for one outcome, for example a full analysis set and
a randomised set, both are recorded, exactly one is marked as selected, and the
population is named on the cell.

## 8 · Outcomes and prioritisation

**Primary:** exercise capacity, preferably change from baseline in six-minute
walk distance, as a between-arm difference on the natural scale, where the
registered outcome measure establishes that definition.

**Co-primary clinical outcome:** clinical worsening or morbidity/mortality, as a
time-to-first-event hazard ratio, where the registered outcome measure
establishes that definition.

**Reported but not pooled unless they meet section 2:** haemodynamic measures,
exercise-test measures other than six-minute walk distance change, metabolic or
biomarker outcomes, discontinuation, adverse events and fixed-time event counts.
They are shown because a reader should see what the trial registered or reported;
they are not pooled as though they answered this review's estimand.

## 9 · Risk of bias

**Tool.** Cochrane risk-of-bias tool for randomized trials, version 2 (RoB-2).

**Unit of assessment.** RoB-2 is applied **to the result being pooled, not to the
trial as a whole**. If no result is poolable, RoB-2 remains pending for the
unpooled registered result rather than converted into a trial-level judgement.
One trial may therefore carry a different judgement for this review's target
result than it would for its own primary endpoint, and that is the intended
behaviour of the tool.

**Variant.** The **effect of assignment to intervention** variant, because that
is what an intention-to-treat comparison estimates. The adherence variant is not
used, and no result assessed under one variant will be reported as though
assessed under the other.

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
and its supplement, and the posted results module. A judgement made from an
abstract alone is not the same act as one made from a protocol, so **the sources
actually consulted are recorded per domain**, and a domain judged without access
to the protocol is marked as such rather than presented as equivalent.

**Relationship to the recorded bias features.** Bias-relevant features in the
canonical object are **inputs to the assessment and never substitutes for a
domain judgement**. No existing prose in the object may stand in for a signalling
question or a domain rating.

**Feeding GRADE.** The completed RoB-2 result becomes the basis of the GRADE
risk-of-bias domain, replacing reasoning from recorded features. When it does,
the review will state **whether the GRADE rating moves and why -- and if it does
not move, will say so explicitly** rather than leaving the reader to infer that
nothing changed.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No RoB-2 assessment exists for these trials. Performing it
later **executes this section rather than amending it**, and the object will
record that distinction.

## 10 · Synthesis methods

Where at least two trials report the same section 2 estimand, random-effects
meta-analysis is performed on the relevant scale: mean difference for six-minute
walk distance change, or log hazard ratio for clinical worsening.
Inverse-variance weighting is used.

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
- A **prediction interval** is reported using the t distribution on k - 1 degrees
  of freedom per Handbook v6.5, and is not reported where k makes it undefined.
- The analysis is **cross-checked in a second engine** at build time and the
  comparison published, including any quantity on which the two engines disagree
  by definition rather than by error.

**Heterogeneity:** tau-squared, I-squared with its Q-profile confidence interval,
and Q with its degrees of freedom and p value. I-squared is reported with the
caveat that at small k a low value reflects imprecision as much as agreement.

## 10A · If no poolable registered estimand exists

If no trial establishes a shared registered outcome definition for exercise
capacity or clinical worsening, the review will not pool a construct. The result
slot will be withdrawn with the reason recorded against the measure axis, and the
page will show the registered primary outcome measures that prevented synthesis.

This is not a failure of software and not an invitation to substitute a nearby
endpoint. It is the review's answer to the stored question under the rules above:
without a shared measure, no meta-analytic estimand exists for this protocol.

## 11 · Subgroup and sensitivity analyses

**Sensitivity, pre-specified:** leave-one-out where defined; the estimator
comparison above; and, where per-arm counts are recovered for a comparable event
outcome, the same 2 by 2 data pooled as a risk ratio, an odds ratio and a risk
difference -- reported as sensitivity to the clinical-worsening estimand, never
as the headline.

**Subgroup: none pre-specified.** With the small number of trials this comparison
already holds, any subgroup contrast would be underpowered and post-hoc, and none
will be presented as though it were planned.

## 12 · Meta-bias assessment

Funnel plot, Egger's regression and -- for any count-based pool -- Peters' test.
**Pre-specified caveat:** below approximately ten studies these tests have almost
no power and the Cochrane Handbook advises against interpreting them. Where k is
below that threshold the tests may still be computed for completeness, and will
be reported as computed values, explicitly not as evidence about small-study
effects. Where publication bias cannot be assessed, the GRADE domain will read
*not assessable* rather than *not serious* -- the two are different statements.

## 13 · Certainty of the evidence

GRADE, per Cochrane Handbook v6.5 sections 14.2.1-14.2.2 and MECIR C74/C75. All
five downgrade domains are assessed and **each rating is published with the
evidence it rests on**; the overall certainty is computed from the domains and
shown against them so a reader can check the arithmetic.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No GRADE assessment exists for these trials. Performing it
later executes this section rather than amending it, and the object will record
that distinction.

## 14 · Data sharing and reproducibility

The canonical data object from which every number on the review page is projected
is published with the review, together with the session information and the
analysis scripts actually executed. The intent is that the review can be rebuilt
from the object alone.

The registration artifact is part of that object family. The protocol commit is
anchored before the search runs; the search record is anchored after the search
runs; and the canonical object records the two anchors so a reader can check the
bracket.

## 15 · Funding and conflicts of interest

**No funding was received for this review.** No competing interests are declared
by the authors of this protocol at the time of this commit. Any change is to be
recorded as an amendment rather than by editing this section.

## 16 · Amendments

None at the time of this registration.

Amendments will be recorded as further commits to this file; the full commit
history, not only its head, is projected onto the review page, because a log that
displays only its own head is no better than a mutable document.
