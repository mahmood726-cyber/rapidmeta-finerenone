# Protocol - empagliflozin in adults with heart failure

**Status: REGISTERED BY COMMIT. This document is the registration.**

This protocol is registered as a commit in a public repository rather than in
PROSPERO. The commit hash is the strong half of that record: the content is
immutable under it, so this text cannot be altered later without producing a
different hash, and anyone can check that much without asking us. The repository
is public, so the text bound to that hash is readable by anyone.

**The commit timestamp is the weak half, and this document will not pretend
otherwise.** Both the author and the committer date on a git commit are supplied
by whoever makes the commit and can be set to any value. Commits here are
unsigned, so the commit carries no cryptographic signature that would add a
second attestation to those dates.

What the mechanism supports, and no more: this exact text is bound to this hash;
the repository is public, so the text is readable by anyone at that hash; and
where an entry for the commit exists in a public transparency log, that log's
inclusion time is an upper bound on when this text existed, set by a third party
rather than by us. That proves something narrow: this text existed no later than
the log time.

What it does not support: it does not prove the commit was made when it says it
was, it does not prove that no earlier or parallel version existed elsewhere, it
does not prove the data had not already been seen, and it says nothing about the
independence of the people who wrote it. Those are claims about conduct, and no
timestamp can carry them.

**How to check this without us.** The verification recipe, the public half of the signing
key, and a worked example are at [`ssot/registration/VERIFY.md`](../registration/VERIFY.md).
It states the limitation plainly as well: the log time is independent of us, the key
custody is not. A stranger can verify the text existed by the log time and that we signed
it; a stranger cannot verify we did not hold an earlier version.

**It is written before the search runs.** The ordering test this review publishes
is that this protocol is committed, pushed, and anchored before the first
executed query. The test uses the earliest query time, including a failed
attempt, not the first successful execution, because reporting only the
successful execution would move the first-query time later and flatter the
claim. The search record is anchored after the search, so two third-party times
bracket the operation: one for the registered protocol before searching, and one
for the search record after searching.

Both query times are read from the search lane's own clock. The databases return
records and metadata, not the external time at which this protocol was anchored.
The sequence is therefore auditable and internally consistent, and the public
anchors prove only their own inclusion times. That is still more than a mutable
private protocol offers, but it is less than proof of conduct, and it is recorded
here as less.

---

## 1 - Review question, in PICO

| | |
|---|---|
| **Population** | Adults with heart failure. |
| **Intervention** | Empagliflozin. |
| **Comparator** | Placebo. |
| **Outcome** | First occurrence of adjudicated cardiovascular death or adjudicated hospitalisation for heart failure, time-to-first-event. |
| **Study design** | Randomised controlled trials. |

**Frozen question:** in adults with heart failure, what is the hazard of a first
adjudicated cardiovascular death or adjudicated hospitalisation for heart failure
with empagliflozin compared with placebo?

The object's stored question carries the trailing clause "the outcome BOTH
trials register as their primary". This protocol deliberately does not adopt that
clause, because a search that returned a third eligible trial would make it
false. If that happens, the stored question must be updated rather than the
search discounted.

## 2 - Estimand, stated in advance

The estimand is the **time-to-first-event hazard ratio for the composite**, on the
log scale, with the participant as the unit of analysis and the time to the first
component event as the event time. The components are adjudicated cardiovascular
death and adjudicated hospitalisation for heart failure.

**Quantities that cannot be converted into that estimand are excluded on the
OUTCOME axis, not on grounds of quality.** This is pre-registered because it is a
criterion and not a judgement made after seeing results. A trial may be large,
well conducted and directly on topic and still fail this review's eligibility
because it reports something else. Specifically and in advance:

- A **recurrent-event rate ratio** counts repeat events per person over time; a
  time-to-first hazard ratio counts each person once, at their first event. The
  two share a scale and a direction and answer different questions. A rate ratio
  will not be stored in a hazard-ratio field.
- A **win ratio** over a hierarchical composite is not this estimand.
- A **dichotomous risk ratio** at a fixed timepoint is not this estimand, though
  where per-arm counts are recovered a risk ratio, odds ratio and risk difference
  will be computed and reported as **sensitivity analyses only**, never as the
  headline.

## 3 - Eligibility criteria

**Include** a study if all four hold: it is randomised; it enrols adults with
heart failure; it randomises empagliflozin against placebo; and it reports the
first occurrence of adjudicated cardiovascular death or adjudicated
hospitalisation for heart failure as a time-to-first-event hazard ratio.

**Exclude** on any single failed axis - population, intervention, comparator, or
measure - and record which axis failed and what the study reports instead.

Populations narrower than the question, such as heart failure with reduced
ejection fraction or heart failure with preserved ejection fraction, are **not**
indirect on that ground alone; narrowness is recorded and carried into the GRADE
indirectness domain rather than used as an exclusion.

## 4 - Information sources

PubMed through NCBI E-utilities and ClinicalTrials.gov API v2 are the only
information sources for the registered search.

Embase was not searched. CENTRAL, Web of Science and Scopus were not searched
either. This is not a comprehensive or exhaustive search. The cost of the
omission is that conference records, indexed trial reports, abstracts, and
records not visible in PubMed or ClinicalTrials.gov may be missed. A missed
eligible trial under those omitted sources would be a limitation of this review's
retrieval system, not evidence that the trial is irrelevant.

## 5 - Search strategy - the exact strings to be executed

These strings are stated **before** execution. The search lane will record what it
actually ran, on what date, with what filters, and how many records each returned;
any departure from the strings below will be recorded as a departure rather than
silently substituted.

**PubMed (NCBI E-utilities)**

```
("empagliflozin"[tiab] OR "BI 10773"[tiab] OR Jardiance[tiab])
AND ("heart failure"[MeSH Terms] OR "heart failure"[tiab] OR HFrEF[tiab] OR HFpEF[tiab])
AND (placebo[tiab] OR randomized controlled trial[pt] OR randomised[tiab] OR randomized[tiab] OR trial[tiab])
```

Filters: none on language, none on date. Rationale: the intervention, condition,
comparator, and randomised-trial terms are explicit, while language and date
filters would make the search less reproducible across interfaces and could
exclude relevant records.

**ClinicalTrials.gov (API v2)**

```
query.intr=empagliflozin OR BI 10773 OR Jardiance
query.cond=heart failure
filter.overallStatus=COMPLETED|TERMINATED|ACTIVE_NOT_RECRUITING
```

No other source, citation chase, regulatory review, search engine, or synthesis
table is part of the registered search.

## 5A - How this search can fail, decided in advance

The meaning of the search result is fixed before execution, because choosing the
interpretation after seeing the result is the defect this registration is meant
to remove.

**(a) The search reproduces exactly the trials the object already holds.** Then
the included set is not a convenience sample but a set that has been searched for
and cannot be improved on with PubMed and ClinicalTrials.gov API v2 under the
registered strings.

**(b) The search returns additional eligible trials.** That is a finding about
the review. Each additional eligible trial is named, and either included or
excluded on a stated axis: population, intervention, comparator, measure, or
study design.

**(c) The search returns fewer trials than the object holds.** If the search
misses a trial known to exist, that is a finding about the search, not about the
review, and it must never be reported as though the review were wrong. Worked
example: on finerenone-cv, executed earlier the same day, the registered
ClinicalTrials.gov condition query missed FIGARO-DKD (NCT02545049), a pivotal
trial, because FIGARO registers its condition as "Diabetic Kidney Disease" alone
while its sibling FIDELIO-DKD (NCT02540993) registers "Chronic Kidney Disease".
A narrow query looks exactly like a wrong review.

## 6 - Study selection process

Two **independent screeners of different model families** - the cross-family rule
is a requirement, not a preference, because two instances of one model is one
screener run twice and its agreement statistic is meaningless.

Screening is in two stages: title and abstract, then full text. **Each screener's
decision is recorded per record at the stage it was applied**, together with the
reason. Both screeners' decisions are published, not only the reconciled outcome,
along with the agreement rate and how every disagreement was resolved.

**Adjudication of disagreements is by a named human.**

**Two release tiers, and the difference between them is attestation, not
content.** The website release requires the two cross-family AI assessments and
states plainly that it has not been human-verified. The submission release
additionally requires two named human reviewers to have checked every included
study and every extracted datum; the statement to that effect is emitted only
when those attestation records exist and is never written as prose.

## 7 - Data extraction

Extracted per trial and per outcome: registry identifier, primary publication,
year, design, population, arms, **the analysed denominator and the randomised
total separately**, per-arm event counts, and the published effect estimate with
its interval and its stated confidence level.

Every extracted cell carries a resolvable pointer to the specific document and,
where possible, to the table within it, so that a human check can be made without
leaving the page. **Nothing is computed that can be read.** No count is derived
from a percentage; no composite is reconstructed by summing its components.
Identifiers are resolved by lookup, never from recall.

Where two populations exist for one outcome - for example a full analysis set and
a randomised set - both are recorded, exactly one is marked as selected, and the
population is named on the cell.

## 8 - Outcomes and prioritisation

**Primary:** first occurrence of adjudicated cardiovascular death or adjudicated
hospitalisation for heart failure, as a time-to-first-event hazard ratio.

**Components, read and reported but not pooled:** adjudicated cardiovascular
death; adjudicated first hospitalisation for heart failure; all-cause death. They
are shown because a reader should see them; they are not pooled because the
review's estimand is the composite.

## 9 - Risk of bias

**Tool.** Cochrane risk-of-bias tool for randomized trials, version 2 (RoB-2).

**Unit of assessment.** RoB-2 is applied **to the result being pooled, not to the
trial as a whole**: the first occurrence of adjudicated cardiovascular death or
adjudicated hospitalisation for heart failure, expressed as a time-to-first-event
hazard ratio. One trial may therefore carry a different judgement for this result
than it would for its own primary endpoint, and that is the intended behaviour of
the tool.

**Variant.** The **effect of assignment to intervention** variant, because that is
what an intention-to-treat hazard ratio estimates. The adherence variant is not
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

**Relationship to the recorded bias features.** Any existing bias-relevant
features in the object - for example endpoint adjudication, endpoint rank within
the trial, early stopping, masking, or analysis population - are **inputs to the
assessment and never substitutes for a domain judgement**. No existing prose in
the object may stand in for a signalling question or a domain rating.

**Feeding GRADE.** The completed RoB-2 result becomes the basis of the GRADE
risk-of-bias domain, replacing any current reasoning from recorded features. When
it does, the review will state **whether the GRADE rating moves and why - and if
it does not move, will say so explicitly** rather than leaving the reader to
infer that nothing changed.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No RoB-2 assessment exists for this review. Performing it
later **executes this section rather than amending it**, and the object will
record that distinction.

## 10 - Synthesis methods

Random-effects meta-analysis on the log hazard-ratio scale, inverse-variance
weighted.

**Pre-specified, so that reporting a disagreement between methods is a commitment
rather than a post-hoc observation:**

- **REML** is the headline between-study-variance estimator.
- The **Hartung-Knapp-Sidik-Jonkman interval is reported alongside** the Wald
  interval, and where the two disagree about whether the interval crosses the
  null, that disagreement is reported in the results rather than resolved by
  choosing one.
- **Leave-one-out** analysis is run and reported for every pool.
- An **estimator comparison** - DerSimonian-Laird, REML, Paule-Mandel - is run
  and reported, per Cochrane Handbook v6.5 section 10.10.4.4, on the
  understanding that with few studies the choice is plausibly influential.
- A **prediction interval** is reported using the t distribution on k - 1
  degrees of freedom per Cochrane Handbook v6.5, and is not reported where k
  makes it undefined.
- The analysis is **cross-checked in a second engine** (R with metafor) at build
  time and the comparison published, including any quantity on which the two
  engines disagree by definition rather than by error.

**Heterogeneity:** tau-squared, I-squared with its Q-profile confidence interval,
and Q with its degrees of freedom and p value. I-squared is reported with the
caveat that at small k a low value reflects imprecision as much as agreement.

## 11 - Subgroup and sensitivity analyses

**Sensitivity, pre-specified:** leave-one-out; the estimator comparison above;
and, where per-arm counts are recovered, the same 2x2 pooled as a risk ratio, an
odds ratio and a risk difference - reported as sensitivity to the primary
hazard-ratio pool, never as the headline.

**Subgroup: none pre-specified.** With the small number of trials this comparison
is expected to have, any subgroup contrast would be underpowered and post-hoc,
and none will be presented as though it were planned.

## 12 - Meta-bias assessment

Funnel plot, Egger's regression and - for any count-based pool - Peters' test.
**Pre-specified caveat:** below approximately ten studies these tests have almost
no power and the Cochrane Handbook advises against interpreting them. Where k is
below that threshold the tests may still be computed for completeness, and will
be reported as computed values, explicitly not as evidence about small-study
effects. Where publication bias cannot be assessed, the GRADE domain will read
*not assessable* rather than *not serious* - the two are different statements.

## 13 - Certainty of the evidence

GRADE, per Cochrane Handbook v6.5 sections 14.2.1-14.2.2 and MECIR C74/C75. All
five downgrade domains are assessed and **each rating is published with the
evidence it rests on**; the overall certainty is computed from the domains and
shown against them so a reader can check the arithmetic.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No GRADE assessment exists for this review. Performing it
later **executes this section rather than amending it**, and the object will
record that distinction.

## 14 - Data sharing and reproducibility

The canonical data object from which every number on the review page is projected
is published with the review, together with the R session information and the
analysis scripts actually executed. The intent is that the review can be rebuilt
from the object alone.

## 15 - Funding and conflicts of interest

**No funding was received for this review.** No competing interests are declared
by the authors of this protocol at the time of this commit. Any change is to be
recorded as an amendment rather than by editing this section.

## 16 - Amendments

Amendments will be recorded as further commits to this file; the full commit
history, not only its head, is projected onto the review page, because a log that
displays only its own head is no better than a mutable document.
