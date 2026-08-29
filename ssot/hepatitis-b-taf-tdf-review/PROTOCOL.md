# Protocol - tenofovir alafenamide versus tenofovir disoproxil fumarate in chronic hepatitis B

**Status: RETROSPECTIVELY REGISTERED BY COMMIT. This document is the registration.**

This retrospectively registered protocol is registered as a commit in a public
repository rather than in PROSPERO. The commit hash is the strong half of that
record: the content is immutable under it, so this text cannot be altered later
without producing a different hash, and anyone can check that much without asking
us.

The commit hash binds the text, and the repository is public. The commit
timestamp is author-supplied and forgeable: both the author and committer dates
on a git commit are set by whoever makes the commit, and commits here are
unsigned. A public transparency-log entry gives an inclusion time set by a third
party, proving something narrow: the text existed no later than the log time. It
does not prove when the commit was made, that no earlier version existed
elsewhere, or what was already known.

**How to check this without us.** The verification recipe, the public half of the signing key, and a worked example are at [`ssot/registration/VERIFY.md`](../registration/VERIFY.md). It states the limitation plainly as well: the log time is independent of us, the key custody is not. A stranger can verify the text existed by the log time and that we signed it; a stranger cannot verify we did not hold an earlier version.

**It is written before the search runs.** The ordering test this review publishes
is that this commit precedes the first executed query - the first *attempt*, not
the first success, because reporting only the successful execution would move the
first-query time later and flatter the claim. The protocol commit is committed,
pushed and anchored before the first query is attempted. The search record is
anchored afterwards, so two third-party times bracket the operation.

Both execution times are read from the search lane's own clock. The databases
return records and hit counts, not trusted execution times, so no part of the
ordering is timestamped by a third party unless an external anchor is placed on
each end. The sequence is therefore auditable and internally consistent, and it
is recorded as less than proof. The anchor proves when this text existed and
cannot prove the trials had not already been seen. A timestamp bounds when, never
what was known.

---

## 1 · Review question, in PICO

| | |
|---|---|
| **Population** | Adults with chronic hepatitis B. |
| **Intervention** | Tenofovir alafenamide. |
| **Comparator** | Tenofovir disoproxil fumarate. |
| **Outcome** | HBV DNA below 29 IU/mL. |
| **Study design** | Randomised controlled trials. |

**Frozen question:** in adults with chronic hepatitis B, does tenofovir
alafenamide compared with tenofovir disoproxil fumarate increase the proportion
achieving HBV DNA below 29 IU/mL?

This topic already holds 2 trials: NCT01940341 and NCT01940471. The question is
therefore being authored after that evidence was assembled. However carefully it
is written now, this is a retrospectively registered protocol, and the anchor
cannot prove those trials had not already been seen.

## 2 · Estimand, stated in advance

The estimand is the **risk ratio for achieving HBV DNA below 29 IU/mL**, with the
participant as the unit of analysis and the trial's prespecified analysis
timepoint for this virological response as the timepoint of interest.

**Quantities that cannot be converted into that estimand are excluded on the
OUTCOME axis, not on grounds of quality.** This is fixed here because it is a
criterion and not a judgement made during extraction. A trial may be large,
well conducted and directly on topic and still fail this review's eligibility
because it reports something else. Specifically and in advance:

- A **mean change in HBV DNA** is not this estimand.
- A **time-to-viral-suppression hazard ratio** is not this estimand.
- A **different viral-suppression threshold** is not this estimand unless the
  trial also reports HBV DNA below 29 IU/mL.
- A **risk difference** or **odds ratio** for the same responder definition will
  be recorded where published and may be computed where per-arm counts are
  recovered, but it will be reported as a sensitivity analysis only, never as the
  headline.

## 3 · Eligibility criteria

**Include** a study if all four hold: it is randomised; it enrols adults with
chronic hepatitis B; it randomises tenofovir alafenamide against tenofovir
disoproxil fumarate; and it reports the proportion achieving HBV DNA below
29 IU/mL or enough per-arm data to compute that proportion.

**Exclude** on any single failed axis - population, intervention, comparator, or
outcome measure - and record which axis failed and what the study reports
instead.

Populations narrower than the question, such as hepatitis B e-antigen positive
or hepatitis B e-antigen negative subgroups, are **not** indirect on that ground
alone; narrowness is recorded and carried into the GRADE indirectness domain
rather than used as an exclusion.

Any axis read from a registry title is provisional until the registered primary
outcome measure is read from the outcome module. A title is not an outcome
definition.

## 4 · Information sources

PubMed through NCBI E-utilities and ClinicalTrials.gov API v2 only.

Embase was not searched, nor CENTRAL, Web of Science or Scopus. The search is not
comprehensive. The cost of that omission is that conference records, trials
indexed outside PubMed, controlled-trials records not mirrored in
ClinicalTrials.gov, and citation paths visible only in subscription or specialist
bibliographic databases may be missed. Any missing eligible study caused by this
source restriction is a limitation of the search, not evidence that the review
object was complete.

## 4A · Linkage method and its known failure modes

Registry records will be linked to publications before extracting publication
data. For every ClinicalTrials.gov record included or already held, the NCT
identifier is treated as the primary key. PubMed E-utilities will be queried for
that NCT identifier in PubMed's secondary-source identifier and text fields.
ClinicalTrials.gov references with `reference_type='result'` are treated as
candidate publication links, not as truth.

A candidate publication is linked only after checking that the registry
identifier, enrolled condition, trial arms, and relevant outcome definition
describe the same trial. Where the registry title appears to establish an
eligibility axis, that reading remains provisional until the outcome module has
been read.

Two linkage failure modes are known and measured on this corpus before this
search runs:

- PubMed silently drops trials from ID-based queries when the record is not
  indexed, so an absent result is indistinguishable from a trial that does not
  exist.
- ClinicalTrials.gov `reference_type='result'` links can point at the wrong
  paper, which is worse than a missing link because a wrong link looks like a
  successful one.

Where linkage succeeds, registry data matched the publication in 26 of 28
analyses compared on this corpus. That is a conditional figure with linked
analyses as its denominator, not all analyses, and therefore not a general
reliability rate.

## 5 · Search strategy - the exact strings to be executed

These strings are stated **before** execution. The search lane will record what
it actually ran, on what date, with what filters, and how many records each
returned; any departure from the strings below will be recorded as a departure
rather than silently substituted.

Each string is kept under 20 Boolean operators because an interface that refuses
the registered query would force a departure on the first attempt.

**PubMed**

```
("tenofovir alafenamide"[tiab] OR TAF[tiab] OR Vemlidy[tiab])
AND ("tenofovir disoproxil fumarate"[tiab] OR TDF[tiab] OR Viread[tiab])
AND ("Hepatitis B, Chronic"[MeSH Terms] OR "hepatitis B"[tiab] OR HBV[tiab])
AND (randomized controlled trial[pt] OR randomized[tiab] OR randomised[tiab] OR trial[tiab])
```

Filters: none on language, none on date. Rationale: language and date filters
make the search less reproducible across interfaces and can hide eligible trials
or their linked publications.

**ClinicalTrials.gov (API v2)**

```
query.intr=tenofovir alafenamide OR TAF OR Vemlidy
query.cond=hepatitis B OR HBV
filter.overallStatus=COMPLETED|TERMINATED|ACTIVE_NOT_RECRUITING
```

## 5A · How this search can fail, decided in advance

The interpretation of every search outcome is fixed before execution:

- If the search reproduces the held set, the held trials are treated as
  searched-for rather than convenient. This supports the review's traceability
  but does not make the registration forward-looking.
- If the search returns additional eligible trials, that is a finding about the
  review. Each trial will be named and included or excluded on one of the stated
  axes only: population, intervention, comparator, or outcome measure.
- If the search returns fewer trials than the object holds, that is a finding
  about the search, never reported as the review being wrong.

The worked example for the third case is the finerenone cardiovascular-outcomes
registry query: it missed FIGARO-DKD (NCT02545049), a pivotal trial, because that
trial registers its condition as "Diabetic Kidney Disease" alone while its
sibling FIDELIO-DKD registers "Chronic Kidney Disease". A narrow query looks
exactly like a wrong review.

## 6 · Study selection process

Two **independent screeners of different model families** - the cross-family rule
is a requirement, not a preference, because two instances of one model is one
screener run twice and its agreement statistic is meaningless.

Screening is in two stages: title and abstract, then full text or registry
record. **Each screener's decision is recorded per record at the stage it was
applied**, together with the reason. Both screeners' decisions are published, not
only the reconciled outcome, along with the agreement rate and how every
disagreement was resolved.

**Adjudication of disagreements is by a named human.**

**Two release tiers, and the difference between them is attestation, not
content.** The website release requires the two cross-family AI assessments and
states plainly that it has not been human-verified. The submission release
additionally requires two named human reviewers to have checked every included
study and every extracted datum; the statement to that effect is emitted only
when those attestation records exist and is never written as prose.

## 7 · Data extraction

Extracted per trial and per outcome: registry identifier, primary publication,
year, design, population, arms, randomised total, analysed denominator, per-arm
responder counts for HBV DNA below 29 IU/mL, the assessment timepoint, and the
published effect estimate with its interval and stated confidence level where one
is reported.

Every extracted cell carries a resolvable pointer to the specific document and,
where possible, to the table, figure, results module field, or outcome module
field within it, so that a human check can be made without leaving the page.
**Nothing is computed that can be read.** No count is derived from a percentage;
no composite is reconstructed by summing components. Identifiers are resolved by
lookup, never from recall.

Classification is against the axes declared in section 3 and no others:
population, intervention, comparator, and outcome measure. Any classification
read from a registry title is provisional until the registered primary outcome
measure has been read from the outcome module. A title is not an outcome
definition.

Where two populations exist for one outcome, such as a full analysis set and a
randomised set, both are recorded, exactly one is marked as selected, and the
population is named on the cell.

## 8 · Outcomes and prioritisation

**Primary:** HBV DNA below 29 IU/mL, expressed as a responder proportion and
pooled as a risk ratio.

**Secondary outcomes, read and reported but not pooled as the headline:** ALT
normalisation; HBeAg loss or seroconversion where applicable; HBsAg loss; renal
safety outcomes; and bone mineral density outcomes. They are shown because a
reader should see them; they are not pooled as the headline because the stored
question is the HBV DNA response outcome.

## 9 · Risk of bias

**Tool.** Cochrane risk-of-bias tool for randomized trials, version 2 (RoB-2).

**Unit of assessment.** RoB-2 is applied **to the result being pooled, not to the
trial as a whole**: HBV DNA below 29 IU/mL, expressed as a responder proportion.
One trial may therefore carry a different judgement for this result than it would
for another endpoint, and that is the intended behaviour of the tool.

**Variant.** The **effect of assignment to intervention** variant, because that
is what an intention-to-treat responder analysis estimates. The adherence variant
is not used, and no result assessed under one variant will be reported as though
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

**Relationship to the recorded bias features.** The object may already hold
bias-relevant features. These are **inputs to the assessment and never
substitutes for a domain judgement**. No existing prose in the object may stand
in for a signalling question or a domain rating.

**Feeding GRADE.** The completed RoB-2 result becomes the basis of the GRADE
risk-of-bias domain, replacing any current reasoning from recorded features. When
it does, the review will state **whether the GRADE rating moves and why - and if
it does not move, will say so explicitly** rather than leaving the reader to
infer that nothing changed.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No RoB-2 assessment exists for these trials. Performing it
later **executes this section rather than amending it**, and the object will
record that distinction.

## 10 · Synthesis methods

Random-effects meta-analysis on the log risk-ratio scale, inverse-variance
weighted. If only one eligible trial is available for the primary outcome after
execution, no meta-analysis is performed and the single eligible result is
reported descriptively.

**Pre-specified, so that reporting a disagreement between methods is a commitment
rather than a post-hoc observation:**

- **REML** is the headline between-study-variance estimator.
- The **Hartung-Knapp-Sidik-Jonkman interval is reported alongside** the Wald
  interval, and where the two disagree about whether the interval crosses the
  null, that disagreement is reported in the results rather than resolved by
  choosing one.
- **Leave-one-out** analysis is run and reported for every pool where k permits
  it.
- An **estimator comparison** - DerSimonian-Laird, REML, Paule-Mandel - is run
  and reported, per Cochrane Handbook v6.5 section 10.10.4.4, on the
  understanding that with few studies the choice is plausibly influential.
- A **prediction interval** is reported using the t distribution on k - 1
  degrees of freedom per Handbook v6.5, and is not reported where k makes it
  undefined.
- The analysis is **cross-checked in a second engine** at build time and the
  comparison published, including any quantity on which the two engines disagree
  by definition rather than by error.

**Heterogeneity:** tau squared, I squared with its Q-profile confidence interval,
and Q with its degrees of freedom and p value. I squared is reported with the
caveat that at small k a low value reflects imprecision as much as agreement.

## 10A · Static versus dynamic values

This table declares which values are fixed in this protocol and which are to be
produced by the later search and extraction. Static values are not search results;
dynamic values are not to be filled from memory.

| Item | Status | Source or rule |
|---|---|---|
| Topic slug | Static | `hepatitis-b-taf-tdf-review` as supplied for this protocol. |
| Review title | Static | Supplied topic title. |
| Frozen question | Static | Supplied stored question. |
| Held trial identifiers | Static existing object state | NCT01940341 and NCT01940471, recorded as already on the object before this protocol. |
| Search strings | Static | Section 5; departures are recorded rather than silently substituted. |
| Search yields and record counts | Dynamic | Produced only when the search lane runs after this protocol is committed, pushed and anchored. |
| Eligibility decisions | Dynamic | Classified only on the section 3 axes. |
| Extracted outcome data and effect estimates | Dynamic | Read from linked registry records and publications after search execution. |
| RoB-2 judgements | Dynamic, pending | Section 9; no judgement exists at this commit. |
| GRADE ratings | Dynamic, pending | Section 13; no rating exists at this commit. |

## 11 · Subgroup and sensitivity analyses

**Sensitivity, pre-specified:** leave-one-out where k permits it; the estimator
comparison above; and, where per-arm counts are recovered, the same 2 x 2 data
pooled as an odds ratio and a risk difference - reported as sensitivity to the
primary risk-ratio pool, never as the headline.

**Subgroup: none pre-specified.** With the small number of trials this comparison
has, any subgroup contrast would be underpowered and post-hoc, and none will be
presented as though it were planned.

## 12 · Meta-bias assessment

Funnel plot, Egger's regression and Peters' test for the count-based primary
pool. **Pre-specified caveat:** below approximately ten studies these tests have
almost no power and the Cochrane Handbook advises against interpreting them.
Where k is below that threshold the tests may still be computed for completeness,
and will be reported as computed values, explicitly not as evidence about
small-study effects. Where publication bias cannot be assessed, the GRADE domain
will read *not assessable* rather than *not serious* - the two are different
statements.

## 13 · Certainty of the evidence

GRADE, per Cochrane Handbook v6.5 sections 14.2.1-14.2.2 and MECIR C74/C75. All
five downgrade domains are assessed and **each rating is published with the
evidence it rests on**; the overall certainty is computed from the domains and
shown against them so a reader can check the arithmetic.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No GRADE assessment exists for this review at this commit.
Performing it later executes this section rather than amending it.

## 14 · Data sharing and reproducibility

The canonical data object from which every number on the review page is projected
is published with the review, together with the session information and the
analysis scripts actually executed. The intent is that the review can be rebuilt
from the object alone.

The search log records the first query attempt, including a failed attempt; all
subsequent executed queries; the exact strings and parameters used; the source
queried; the execution time read from the search lane's own clock; and the record
counts returned by the source. The protocol anchor precedes that log, and the
search-record anchor follows it.

## 15 · Funding and conflicts of interest

**No funding was received for this review.** No competing interests are declared
by the authors of this protocol at the time of this commit. Any change is to be
recorded as an amendment rather than by editing this section.

## 16 · Amendments

Amendments will be recorded as further commits to this file; the full commit
history, not only its head, is projected onto the review page, because a log that
displays only its own head is no better than a mutable document.
