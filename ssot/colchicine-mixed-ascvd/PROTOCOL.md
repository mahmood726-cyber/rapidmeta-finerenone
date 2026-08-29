# Protocol - Colchicine in mixed atherosclerotic populations

**Status: RETROSPECTIVELY REGISTERED BY COMMIT. This document is the registration.**

This protocol is registered as a commit in a public repository rather than in
PROSPERO. It is retrospectively registered: this topic already holds 5 trials,
and the question is being authored after that evidence was assembled. However
carefully the methods are written now, this document cannot be represented as a
prospective protocol.

The commit hash is the strong half of the record. The content is immutable under
that hash, so this text cannot be altered later without producing a different
hash, and anyone can check that much without asking us. The repository is public,
so the text is readable by anyone at that hash.

**The commit timestamp is the weak half, and this document will not pretend
otherwise.** Both the author and the committer date on a git commit are supplied
by whoever makes the commit and can be set to any value; commits here are
unsigned and carry nothing further. A transparency-log entry gives an inclusion
time set by a third party, proving something narrow: **the text existed no later
than the log time**. It does not prove when the commit was made, it does not prove
that no earlier version existed elsewhere, and it does not prove what was already
known.

**How to check this without us.** The verification recipe, the public half of the signing key, and a worked example are at [`ssot/registration/VERIFY.md`](../registration/VERIFY.md). It states the limitation plainly as well: the log time is independent of us, the key custody is not. A stranger can verify the text existed by the log time and that we signed it; a stranger cannot verify we did not hold an earlier version.

**It is written before the search runs.** The ordering test this review publishes
is that this protocol is committed, pushed and anchored before the first executed
query. The first executed query means the first attempt, including a failed
attempt, not the first successful retrieval. Reporting only the successful
execution would move the first-query time later and flatter the claim.

The search record is anchored afterwards, so two third-party times bracket the
operation: one for this protocol before the search and one for the search record
afterwards. That proves the text existed no later than the first log time and
that the later search record existed no later than its own log time. It does not
prove the trials had not already been seen. A timestamp bounds when, never what
was known.

---

## 1 - Review question, in PICO

| | |
|---|---|
| **Population** | Adults with atherosclerotic disease not confined to one arterial bed. |
| **Intervention** | Colchicine. |
| **Comparator** | The comparator each trial randomised. |
| **Outcome** | Cardiovascular events, using the eligible effect measure specified in this protocol. |
| **Study design** | Randomised controlled trials. |

**Frozen question:** in adults with atherosclerotic disease not confined to one
arterial bed, does colchicine reduce cardiovascular events against the comparator
each trial randomised?

This is a retrospectively registered review question. This topic already holds 5
trials: NCT02162303, NCT04073797, NCT04181996, NCT06930885 and NCT07654231.
The question is being authored after that evidence was assembled. The anchor
therefore proves when this text existed; it cannot prove the trials had not
already been seen.

## 2 - Estimand, stated in advance

The estimand is the **time-to-first-event hazard ratio for cardiovascular
events**, on the log scale, with the participant as the unit of analysis and the
time to the first eligible cardiovascular event as the event time.

**Quantities that cannot be converted into that estimand are excluded on the
MEASURE axis, not on grounds of quality.** This is pre-specified because it is a
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
- A surrogate imaging or biomarker outcome is not this estimand unless the same
  trial also reports an eligible cardiovascular-event time-to-first hazard ratio.

## 3 - Eligibility criteria

**Include** a study if all five hold: it is randomised; it enrols adults with
atherosclerotic disease not confined to one arterial bed; it randomises
colchicine against a comparator; it reports cardiovascular events; and it reports
the eligible cardiovascular-event result as a time-to-first-event hazard ratio.

**Exclude** on any single failed axis - population, intervention, comparator,
study design, or measure - and record which axis failed and what the study
reports instead.

Populations narrower than the question are **not** indirect on that ground alone
if they still cross arterial beds. Narrowness is recorded and carried into the
GRADE indirectness domain rather than used as an exclusion. Populations confined
to a single arterial bed fail the population axis for this review and belong to a
different reading.

Any axis read from a registry title is provisional until the registered primary
outcome measure is read from the outcome module. A title is not an outcome
definition.

## 4 - Information sources

PubMed through NCBI E-utilities and ClinicalTrials.gov API v2 are the only
information sources for this registered search.

Embase was **NOT** searched, nor CENTRAL, Web of Science or Scopus. This is not
a comprehensive search, and it must not be described as one.

The cost of those omissions is explicit: trials or publications indexed outside
PubMed, conference records without PubMed entries, records better captured by
CENTRAL, and citation-network discoveries available through Web of Science or
Scopus may be missed. Any missing eligible study found later through those routes
is a limitation of this search, not evidence that the later study is outside the
review question.

## 4A - Linkage method and its known failure modes

Before the search runs, a registry record is linked to a publication by this
route:

1. Read the ClinicalTrials.gov record through API v2, including identification,
   status, arms, interventions, conditions, outcomes and references.
2. Extract every registry-supplied PMID, DOI and citation from the reference
   module without treating `reference_type='result'` as automatically correct.
3. Query PubMed by registry identifier and by registry-supplied PMID where a PMID
   exists.
4. Accept a publication link only when the publication can be reconciled to the
   registry record by trial identifier, acronym, arm structure, population and
   outcome context. Ambiguous links remain unresolved.
5. Record the linkage route and evidence pointer. A missing link is reported as
   missing, not filled from memory.

Two failure modes are measured on this corpus and are named before execution.

First, PubMed silently drops trials from ID-based queries when the record is not
indexed, so an absent result is indistinguishable from a trial that does not
exist. Absence from an ID query is therefore never evidence that the registry
record is absent, unpublished or ineligible.

Second, registry `reference_type='result'` links can point at the wrong paper.
That is worse than a missing link because a wrong link looks like a successful
one. Result-type references are therefore evidence to inspect, not evidence to
trust automatically.

Where linkage succeeds, registry data matched the publication in 26 of 28
analyses compared on this corpus. That is a conditional figure whose denominator
is linked analyses, not all analyses, and therefore it is not a general
reliability rate.

## 5 - Search strategy - the exact strings to be executed

These strings are stated **before** execution. The search lane will record what
it actually ran, on what date, with what filters, and how many records each
returned. Any departure from the strings below will be recorded as a departure
rather than silently substituted. Each string is kept under 20 Boolean operators
because a registered string that cannot be executed would force a departure on
the first attempt.

**PubMed (NCBI E-utilities)**

```
colchicine[tiab]
AND (atherosclerosis[tiab] OR atherosclerotic[tiab] OR cardiovascular[tiab] OR vascular[tiab])
AND (randomized[tiab] OR randomised[tiab] OR trial[tiab])
```

Filters: none on language, none on date. Rationale: filters make the search less
reproducible across interfaces and may remove records whose eligibility cannot
be assessed from metadata alone.

**ClinicalTrials.gov (API v2)**

```
query.intr=colchicine
query.cond=atherosclerosis OR atherosclerotic disease OR cardiovascular disease OR vascular disease
```

Filters: none on status, phase, sex, age, geography, sponsor, date or results
posting. Rationale: eligibility is determined after retrieval from the registered
record, not by pre-filtering on metadata fields whose wording varies by sponsor.

## 5A - How this search can fail, decided in advance

Every search outcome is interpreted before execution.

**If the search reproduces the held set**, the conclusion is that the set was
searched for rather than merely convenient. That does not make the registration
prospective and does not prove the trials had not already been seen.

**If the search returns additional eligible trials**, that is a finding about the
review. Each additional trial is named and then included or excluded against the
pre-specified axes in section 3: population, intervention, comparator, study
design and measure. No other exclusion axis may be introduced at that point.

**If the search returns fewer trials than the object holds**, that is a finding
about the search, never reported as the review being wrong. The worked example is
the finerenone-cv registry query: it missed FIGARO-DKD (NCT02545049), a pivotal
trial, because FIGARO-DKD registers its condition as "Diabetic Kidney Disease"
alone while its sibling FIDELIO-DKD registers "Chronic Kidney Disease". A narrow
query looks exactly like a wrong review.

## 6 - Study selection process

Two **independent screeners of different model families** assess every retrieved
record. The cross-family rule is a requirement, not a preference, because two
instances of one model is one screener run twice and its agreement statistic is
meaningless.

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

## 7 - Data extraction

Extracted per trial and per outcome: registry identifier, primary publication
where linked, year, design, population, arms, comparator, **the analysed
denominator and the randomised total separately**, per-arm event counts where
reported, and the published effect estimate with its interval and its stated
confidence level.

Each candidate record is classified only against the axes declared in section 3:
population, intervention, comparator, study design and measure. Section 7 may not
introduce a new exclusion axis.

Any axis read from a registry title remains provisional until the registered
primary outcome measure is read from the outcome module. A title is not an
outcome definition. Where the title, condition field and outcome module point in
different directions, the outcome module governs the measure axis and the
conflict is recorded rather than resolved silently.

Every extracted cell carries a resolvable pointer to the specific document and,
where possible, to the table or registry module within it, so that a human check
can be made without leaving the page. **Nothing is computed that can be read.**
No count is derived from a percentage; no composite is reconstructed by summing
its components. Identifiers are resolved by lookup, never from recall.

Where two populations exist for one outcome, for example a full analysis set and
a randomised set, both are recorded, exactly one is marked as selected, and the
population is named on the cell.

## 8 - Outcomes and prioritisation

**Primary:** cardiovascular events in adults with mixed atherosclerotic disease,
expressed as a time-to-first-event hazard ratio.

**Components, read and reported but not pooled unless they are the registered
eligible cardiovascular-event result:** cardiovascular death; myocardial
infarction; stroke; coronary revascularisation; limb events; all-cause death.
They are shown because a reader should see them. They are not substituted for the
review's primary estimand.

## 9 - Risk of bias

**Tool.** Cochrane risk-of-bias tool for randomized trials, version 2 (RoB-2).

**Unit of assessment.** RoB-2 is applied **to the result being pooled, not to the
trial as a whole**: the eligible cardiovascular-event time-to-first hazard ratio.
One trial may therefore carry a different judgement for this result than it would
for its own primary endpoint, and that is the intended behaviour of the tool.

**Variant.** The **effect of assignment to intervention** variant, because that
is what an intention-to-treat hazard ratio estimates. The adherence variant is
not used, and no result assessed under one variant will be reported as though
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

**Relationship to the recorded bias features.** The object may hold
bias-relevant features such as open-label design with blinded endpoint
adjudication, endpoint rank within its own trial, early stopping, and analysis
population. These are **inputs to the assessment and never substitutes for a
domain judgement**. No existing prose in the object may stand in for a signalling
question or a domain rating.

**Feeding GRADE.** The completed RoB-2 result becomes the basis of the GRADE
risk-of-bias domain, replacing any current reasoning from recorded features. When
it does, the review will state **whether the GRADE rating moves and why - and if
it does not move, will say so explicitly** rather than leaving the reader to
infer that nothing changed.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No RoB-2 assessment exists for these trials. Performing it
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
- A **prediction interval** is reported using the t distribution on k-1 degrees
  of freedom per Cochrane Handbook v6.5, and is not reported where k makes it
  undefined.
- The analysis is **cross-checked in a second engine** at build time and the
  comparison published, including any quantity on which the two engines disagree
  by definition rather than by error.

**Heterogeneity:** tau-squared, I-squared with its Q-profile confidence interval,
and Q with its degrees of freedom and p value. I-squared is reported with the
caveat that at small k a low value reflects imprecision as much as agreement.

No synthesis is run where no eligible time-to-first cardiovascular-event hazard
ratio exists. In that case the review reports the eligibility finding rather than
manufacturing a pooled estimate from a different measure.

## 10A - Static-vs-dynamic hardcode disclosure

| Item | Static in this protocol | Dynamic at execution | What must not be hardcoded as a result |
|---|---|---|---|
| Topic slug and title | `colchicine-mixed-ascvd`; Colchicine in mixed atherosclerotic populations | No | N/A |
| Frozen question | The stored question in section 1 | No | N/A |
| Held trial identifiers | NCT02162303, NCT04073797, NCT04181996, NCT06930885, NCT07654231 | No | Eligibility conclusions beyond the section 3 axes |
| Search strings | The exact PubMed and ClinicalTrials.gov strings in section 5 | No, except recorded departures | Search yields, dates, or hit counts |
| Linkage method | The route in section 4A | Link outcomes are dynamic | Publication matches not verified by the linkage evidence |
| Effect data | No | Yes, if eligible records report it | Hazard ratios, event counts, p values, confidence intervals, weights or pooled effects |
| RoB-2 and GRADE | Method only | Yes, later | Completed ratings before assessment |

## 11 - Subgroup and sensitivity analyses

**Sensitivity, pre-specified:** leave-one-out; the estimator comparison above;
and, where per-arm counts are recovered, the same 2x2 pooled as a risk ratio, an
odds ratio and a risk difference - reported as sensitivity to the primary
hazard-ratio pool, never as the headline.

**Subgroup: none pre-specified.** With the small number of trials this comparison
has, any subgroup contrast would be underpowered and post-hoc, and none will be
presented as though it were planned.

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
implied as done.** No GRADE assessment exists for these trials. Performing it
later **executes this section rather than amending it**, and the object will
record that distinction.

## 14 - Data sharing and reproducibility

The canonical data object from which every number on the review page is projected
is published with the review, together with the session information and the
analysis scripts actually executed. The intent is that the review can be rebuilt
from the object alone.

The protocol commit, the search execution record, and their transparency-log
anchors are part of the reproducibility record. The protocol is anchored before
the first query attempt, including a failed attempt. The search record is
anchored after execution, so readers can audit the bracket rather than relying on
prose.

## 15 - Funding and conflicts of interest

**No funding was received for this review.** No competing interests are declared
by the authors of this protocol at the time of this commit. Any change is to be
recorded as an amendment rather than by editing this section.

## 16 - Amendments

No amendments exist at the time of this commit.

Amendments will be recorded as further commits to this file; the full commit
history, not only its head, is projected onto the review page, because a log that
displays only its own head is no better than a mutable document.
