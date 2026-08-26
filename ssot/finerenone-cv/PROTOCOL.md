# Protocol — finerenone against placebo in chronic kidney disease with type 2 diabetes: the cardiovascular composite, pooled from the two pivotal trials

**Status: REGISTERED BY COMMIT. This document is the registration.**

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

**It is written before the search runs.** This protocol is committed, pushed,
and log-anchored before the first query. The ordering test this review publishes
uses the earliest query time, including a failed attempt, rather than the first
successful one, because reporting only the successful execution would move the
first-query time later and flatter the claim.

The search record will itself be log-anchored afterwards, so two third-party
times bracket the operation: one before the first query attempt, and one after
the search record exists. Both local execution times are read from the search
lane's own clock. The databases return records and hit counts, not authoritative
timestamps for our act of searching. The sequence is therefore auditable and
bounded by third-party log times, and it is recorded here as less than proof.

---

## 1 · Review question, in PICO

| | |
|---|---|
| **Population** | Adults with chronic kidney disease and type 2 diabetes. |
| **Intervention** | Finerenone. |
| **Comparator** | Placebo. |
| **Outcome** | The first occurrence of the composite of cardiovascular death, non-fatal myocardial infarction, non-fatal stroke, or hospitalisation for heart failure. |
| **Study design** | Randomised controlled trials. |

**Frozen question:** in adults with chronic kidney disease and type 2 diabetes,
what is the hazard of a first cardiovascular death, non-fatal myocardial
infarction, non-fatal stroke, or hospitalisation for heart failure with
finerenone compared with placebo?

## 2 · Estimand, stated in advance

The estimand is the **time-to-first-event hazard ratio for the cardiovascular
composite**, on the log scale, with the participant as the unit of analysis and
the time to the first component event as the event time.

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
  where per-arm counts are recovered a risk ratio, odds ratio and risk
  difference will be computed and reported as **sensitivity analyses only**,
  never as the headline.

## 3 · Eligibility criteria

**Include** a study if all four hold: it is randomised; it enrols adults with
chronic kidney disease and type 2 diabetes; it randomises finerenone against
placebo; and it reports the composite of cardiovascular death, non-fatal
myocardial infarction, non-fatal stroke, or hospitalisation for heart failure as
a time-to-first-event hazard ratio.

**Exclude** on any single failed axis — population, intervention, comparator, or
measure — and record which axis failed and what the study reports instead.

The canonical object already names FIDELIO-DKD (NCT02540993) and FIGARO-DKD
(NCT02545049) as candidate pivotal trials. Candidate status is not inclusion:
each candidate must still pass the axes above, and any searched record must pass
the same axes before it can enter the pool.

Populations narrower than the question are **not** indirect on that ground
alone; narrowness is recorded and carried into the GRADE indirectness domain
rather than used as an exclusion.

## 4 · Information sources

PubMed (NCBI E-utilities) and ClinicalTrials.gov API v2.

Embase was not searched. CENTRAL, Web of Science and Scopus were not searched
either. This is a narrow search, and the review's discovery claim is limited to
the two named sources and the candidate trial identifiers already held in the
canonical object. The cost of the omission is that records indexed only in the
omitted services, conference material present only there, and citations missed by
the stated PubMed and ClinicalTrials.gov strings may be absent from the review.

## 5 · Search strategy — the exact strings to be executed

These strings are stated **before** execution. The search lane will record what it
actually ran, on what date, with what filters, and how many records each returned;
any departure from the strings below will be recorded as a departure rather than
silently substituted.

**PubMed (NCBI E-utilities)**

```
(finerenone[tiab] OR "BAY 94-8862"[tiab] OR Kerendia[tiab] OR FIDELIO-DKD[tiab] OR FIGARO-DKD[tiab])
AND ("chronic kidney disease"[tiab] OR "diabetic kidney disease"[tiab] OR CKD[tiab] OR "kidney disease"[MeSH Terms] OR "type 2 diabetes"[tiab] OR T2D[tiab] OR T2DM[tiab] OR "Diabetes Mellitus, Type 2"[MeSH Terms])
AND (placebo[tiab] OR randomized controlled trial[pt] OR randomised[tiab] OR randomized[tiab] OR trial[tiab])
```

Filters: none on language, none on date. Rationale: a language or date filter
would narrow the record set for reasons not part of the eligibility criteria.

**ClinicalTrials.gov (API v2)**

```
query.intr=finerenone OR BAY 94-8862 OR Kerendia
query.cond=chronic kidney disease AND type 2 diabetes
filter.overallStatus=COMPLETED|TERMINATED|ACTIVE_NOT_RECRUITING
```

**ClinicalTrials.gov known-identifier resolution (API v2)**

```
query.id=NCT02540993 OR NCT02545049
```

No backward citation search, forward citation search, registry outside
ClinicalTrials.gov, or bibliographic database outside PubMed is registered for
this review.

## 6 · Study selection process

Two **independent screeners of different model families** — the cross-family rule
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
year, design, population, arms, **the analysed denominator and the randomised
total separately**, per-arm event counts, and the published effect estimate with
its interval and its stated confidence level.

Every extracted cell carries a resolvable pointer to the specific document and,
where possible, to the table within it, so that a human check can be made without
leaving the page. **Nothing is computed that can be read.** No count is derived
from a percentage; no composite is reconstructed by summing its components.
Identifiers are resolved by lookup, never from recall.

Where two populations exist for one outcome — for example a full analysis set and
a randomised set — both are recorded, exactly one is marked as selected, and the
population is named on the cell.

## 8 · Outcomes and prioritisation

**Primary:** the composite of cardiovascular death, non-fatal myocardial
infarction, non-fatal stroke, or hospitalisation for heart failure, as a
time-to-first-event hazard ratio.

**Components, read and reported but not pooled:** cardiovascular death; non-fatal
myocardial infarction; non-fatal stroke; hospitalisation for heart failure;
all-cause death. They are shown because a reader should see them; they are not
pooled because the review's estimand is the composite.

## 9 · Risk of bias

**Tool.** Cochrane risk-of-bias tool for randomized trials, version 2 (RoB-2).

**Unit of assessment.** RoB-2 is applied **to the result being pooled, not to the
trial as a whole**: the cardiovascular composite, expressed as a
time-to-first-event hazard ratio. One trial may therefore carry a different
judgement for this result than it would for another endpoint, and that is the
intended behaviour of the tool.

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

**Both sets of judgements are recorded and published** — per domain, per
assessor, with rationales — not only the reconciled outcome. The **per-domain
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
When it does, the review will state **whether the GRADE rating moves and why —
and if it does not move, will say so explicitly** rather than leaving the reader
to infer that nothing changed.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No RoB-2 assessment exists for these trials in this protocol.
Performing it later **executes this section rather than amending it**, and the
object will record that distinction.

## 10 · Synthesis methods

Random-effects meta-analysis on the log hazard-ratio scale, inverse-variance
weighted.

**Pre-specified, so that reporting a disagreement between methods is a commitment
rather than a post-hoc observation:**

- **REML** is the headline between-study-variance estimator.
- The **Hartung–Knapp–Sidik–Jonkman interval is reported alongside** the Wald
  interval, and where the two disagree about whether the interval crosses the
  null, that disagreement is reported in the results rather than resolved by
  choosing one.
- **Leave-one-out** analysis is run and reported for every pool where it is
  defined.
- An **estimator comparison** — DerSimonian–Laird, REML, Paule–Mandel — is run
  and reported, per Cochrane Handbook v6.5 §10.10.4.4, on the understanding that
  with few studies the choice is plausibly influential.
- A **prediction interval** is reported using the t distribution on k−1 degrees
  of freedom per Handbook v6.5, and is not reported where k makes it undefined.
- The analysis is **cross-checked in a second engine** (R with metafor) at build
  time and the comparison published, including any quantity on which the two
  engines disagree by definition rather than by error.

**Heterogeneity:** τ², I² with its Q-profile confidence interval, and Q with its
degrees of freedom and p value. I² is reported with the caveat that at small k a
low value reflects imprecision as much as agreement.

## 11 · Subgroup and sensitivity analyses

**Sensitivity, pre-specified:** leave-one-out where defined; the estimator
comparison above; and, where per-arm counts are recovered, the same 2×2 pooled as
a risk ratio, an odds ratio and a risk difference — reported as sensitivity to
the primary hazard-ratio pool, never as the headline.

**Subgroup: none pre-specified.** With the small number of candidate pivotal
trials already named for this comparison, any subgroup contrast would be
underpowered and post-hoc, and none will be presented as though it were planned.

## 12 · Meta-bias assessment

Funnel plot, Egger's regression and — for any count-based pool — Peters' test.
**Pre-specified caveat:** below approximately ten studies these tests have almost
no power and the Cochrane Handbook advises against interpreting them. Where k is
below that threshold the tests may still be computed for completeness, and will
be reported as computed values, explicitly not as evidence about small-study
effects. Where publication bias cannot be assessed, the GRADE domain will read
*not assessable* rather than *not serious* — the two are different statements.

## 13 · Certainty of the evidence

GRADE, per Cochrane Handbook v6.5 §14.2.1–14.2.2 and MECIR C74/C75. All five
downgrade domains are assessed and **each rating is published with the evidence
it rests on**; the overall certainty is computed from the domains and shown
against them so a reader can check the arithmetic.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No GRADE assessment exists for this review in this protocol.
Performing it later executes this section rather than amending it.

## 14 · Data sharing and reproducibility

The canonical data object from which every number on the review page is projected
is published with the review, together with the R session information and the
analysis scripts actually executed. The intent is that the review can be rebuilt
from the object alone.

The protocol commit and its pre-search transparency-log entry are stored with the
canonical object. The post-search search record and its transparency-log entry
are stored with the same object, so the registration text and the executed search
record can be read together.

## 15 · Funding and conflicts of interest

**No funding was received for this review.** No competing interests are declared
by the authors of this protocol at the time of this commit. Any change is to be
recorded as an amendment rather than by editing this section.

## 16 · Amendments

None at this registration commit.

Amendments will be recorded as further commits to this file; the full commit
history, not only its head, is projected onto the review page, because a log that
displays only its own head is no better than a mutable document.
