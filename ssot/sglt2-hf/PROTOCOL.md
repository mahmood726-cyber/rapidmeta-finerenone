# Protocol - SGLT2 inhibitors against placebo in chronic heart failure across the ejection fraction spectrum: the four randomised outcome trials that report cardiovascular death or a worsening heart failure event as a time-to-first hazard ratio

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

**Status: RETROSPECTIVELY REGISTERED BY COMMIT AND PUBLIC TRANSPARENCY LOG. This document is the registration.**

This protocol is registered by a commit that is pushed to a public repository
and anchored in a public transparency log before the search runs. The commit
hash is the strong half of that record: the content is immutable under it, so
this exact text cannot be altered later without producing a different hash, and
anyone can check that much without asking us.

**The commit timestamp is the weak half, and this document will not pretend
otherwise.** The commit timestamp is author-supplied and forgeable: both the
author and the committer date on a git commit are supplied by whoever makes the
commit and can be set to any value; commits here are unsigned, and an unsigned
commit carries nothing further.

What the mechanism supports, and no more: this exact text is bound to this hash;
the repository is public, so the text is readable by anyone at that hash; and
where an entry for the commit exists in a public transparency log, that log's
inclusion time is an upper bound on when this text existed, set by a third party
rather than by us. The transparency-log entry proves the narrow claim that the
text existed no later than the log time.

What it does not support: it does not prove the commit was made when it says it
was, it does not prove that no earlier or parallel version existed elsewhere, it
does not prove the trials had not already been seen, and it says nothing about
the independence of the people who wrote it. Those are claims about conduct, and
no timestamp can carry them.

**How to check this without us.** The verification recipe, the public half of the signing key, and a worked example are at [`ssot/registration/VERIFY.md`](../registration/VERIFY.md). It states the limitation plainly as well: the log time is independent of us, the key custody is not. A stranger can verify the text existed by the log time and that we signed it; a stranger cannot verify we did not hold an earlier version.

**It is written before the search runs, but after the evidence was assembled.**
The ordering test this review publishes is that this protocol commit is made,
pushed, and anchored before the first executed query. The first executed query is
the first attempt, including a failed attempt, not the first successful response,
because reporting only a later success would move the search start later and
flatter the claim. The search record is anchored afterwards so two third-party
log inclusion times bracket the operation.

Both execution times are read from the search lane's own clock. The databases do
not return trusted execution times, so no part of the ordering is timestamped by
a third party unless an external anchor is placed on each end. The sequence is
therefore auditable and internally consistent, and it is not, on its own, proof
of what was known.

---

## 1. Review question, in PICO

| | |
|---|---|
| **Population** | Adults with chronic heart failure across the ejection fraction spectrum. |
| **Intervention** | An SGLT2 inhibitor, restricted to dapagliflozin 10 mg once daily or empagliflozin 10 mg once daily. |
| **Comparator** | Placebo, added to background therapy. |
| **Outcome** | The composite of cardiovascular death or a worsening heart failure event, analysed as time to first event. |
| **Study design** | Randomised controlled trials. |

**Frozen question:** in adults with chronic heart failure, what is the hazard of
a first cardiovascular death or worsening heart failure event with an SGLT2
inhibitor compared with placebo added to background therapy?

This topic already holds 4 trials: NCT03036124, NCT03057951, NCT03057977, and
NCT03619213. The question is being authored after that evidence was assembled.
However carefully it is written now, this is a retrospectively registered
protocol. The anchor proves when this text was written and cannot prove the
trials had not already been seen. A timestamp bounds when, never what was known.

## 2. Estimand, stated in advance

The estimand is the **time-to-first-event hazard ratio for the composite**, on
the log scale, with the participant as the unit of analysis and the time to the
first cardiovascular death or worsening heart failure event as the event time.

**Quantities that cannot be converted into that estimand are excluded on the
MEASURE axis, not on grounds of quality.** This is registered because it is a
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

## 3. Eligibility criteria

**Include** a study if all four hold: it is randomised; it enrols adults with
chronic heart failure; it randomises dapagliflozin 10 mg once daily or
empagliflozin 10 mg once daily against placebo added to background therapy; and
it reports the composite of cardiovascular death or a worsening heart failure
event as a time-to-first-event hazard ratio.

**Exclude** on any single failed axis - population, intervention, comparator, or
measure - and record which axis failed and what the study reports instead.

Any axis read from a registry title is provisional until the registered primary
outcome measure is read from the outcome module: a title is not an outcome
definition.

Populations narrower than the question, including ejection-fraction strata, are
**not** indirect on that ground alone; narrowness is recorded and carried into
the GRADE indirectness domain rather than used as an exclusion.

## 4. Information sources

PubMed through NCBI E-utilities and ClinicalTrials.gov API v2 are the only
databases searched for this registration. Embase was **not** searched. CENTRAL
was **not** searched. Web of Science was **not** searched. Scopus was **not**
searched. This is not a comprehensive search.

The cost of that omission is recorded now rather than softened later: trials,
conference records, indexing variants, and systematic-review traces that are
visible in those databases and not in PubMed or ClinicalTrials.gov may be missed.
The review is therefore a PubMed plus registry verification of a held object, not
a claim that every bibliographic route to this question has been exhausted.

## 4A. Linkage method and its known failure modes

Before the search runs, a registry record will be linked to a publication by a
resolvable identifier path: an NCT identifier in the publication metadata,
abstract, full text, supplement, or PubMed record; a PubMed identifier listed in
the ClinicalTrials.gov references module; or a ClinicalTrials.gov
`reference_type='result'` link that survives manual checking against the trial
arms, population, and registered outcome. A candidate link is not accepted merely
because it is present in one source field. It must point to the same trial and to
the publication used for the eligible result.

Two failure modes have already been measured on this corpus and are named before
execution:

- PubMed silently drops trials from ID-based queries when the record is not
  indexed, so an absent result is indistinguishable from a trial that does not
  exist.
- Registry `reference_type='result'` links can point at the wrong paper, which is
  worse than a missing link because a wrong link looks like a successful one.

Where linkage succeeds, registry data matched the publication in 26 of 28
analyses compared on this corpus. That is a conditional figure whose denominator
is linked analyses, not all analyses, and therefore it is not a general
reliability rate.

## 5. Search strategy - the exact strings to be executed

These strings are stated **before** execution. The search lane will record what
it actually ran, on what date, and with what filters; any departure from the
strings below will be recorded as a departure rather than silently substituted.
Each Boolean string is deliberately kept below the interface limit that would
make the registered query unexecutable on first attempt.

**PubMed, through NCBI E-utilities**

```
("dapagliflozin"[tiab] OR "empagliflozin"[tiab] OR "SGLT2 inhibitor"[tiab] OR "sodium-glucose cotransporter 2"[tiab])
AND ("heart failure"[MeSH Terms] OR "heart failure"[tiab] OR HFrEF[tiab] OR HFpEF[tiab])
AND placebo[tiab]
AND (randomized controlled trial[pt] OR randomised[tiab] OR randomized[tiab] OR trial[tiab])
AND ("cardiovascular death"[tiab] OR "worsening heart failure"[tiab])
```

Filters: none on language, none on date.

**ClinicalTrials.gov API v2**

```
query.intr=dapagliflozin OR empagliflozin OR SGLT2 inhibitor
query.cond=heart failure
filter.overallStatus=COMPLETED|TERMINATED|ACTIVE_NOT_RECRUITING
```

ClinicalTrials.gov records are then screened against the same population,
intervention, comparator, and measure axes as PubMed records. A registry title is
not treated as an outcome definition; the registered primary outcome measure is
read from the outcome module before the measure axis is classified.

## 5A. How this search can fail, decided in advance

The interpretation of every possible search outcome is fixed before execution:

- If the search reproduces the held set, that is reported as the result of a
  searched-for check rather than as proof that the held set was convenient or
  complete.
- If the search returns additional eligible trials, that is a finding about the
  review. Each trial is named and included or excluded on one of the axes stated
  in section 3.
- If the search returns fewer trials than the object holds, that is a finding
  about the search, never reported as the review being wrong.

The worked example for the third case is the finerenone-cv registry query, which
missed FIGARO-DKD (NCT02545049), a pivotal trial, because it registers its
condition as "Diabetic Kidney Disease" alone while its sibling FIDELIO-DKD
registers "Chronic Kidney Disease". A narrow query looks exactly like a wrong
review.

## 6. Study selection process

Two **independent screeners of different model families** - the cross-family rule
is a requirement, not a preference, because two instances of one model is one
screener run twice and its agreement statistic is meaningless.

Screening is in two stages: title and abstract, then full text or registry
module. **Each screener's decision is recorded per record at the stage it was
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

## 7. Data extraction

Extracted per trial and per outcome: registry identifier, primary publication,
year, design, population, arms, **the analysed denominator and the randomised
total separately**, per-arm event counts, and the published effect estimate with
its interval and its stated confidence level.

Each candidate record is classified against the section 3 axes and no others:
population, intervention, comparator, and measure. Any axis read from a registry
title is provisional until the registered primary outcome measure is read from
the outcome module. A title is not an outcome definition.

Every extracted cell carries a resolvable pointer to the specific document and,
where possible, to the table within it, so that a human check can be made without
leaving the page. **Nothing is computed that can be read.** No count is derived
from a percentage; no composite is reconstructed by summing its components.
Identifiers are resolved by lookup, never from recall.

Where two populations exist for one outcome - for example a full analysis set and
a randomised set - both are recorded, exactly one is marked as selected, and the
population is named on the cell.

## 8. Outcomes and prioritisation

**Primary:** the composite of cardiovascular death or a worsening heart failure
event, as a time-to-first-event hazard ratio.

**Components, read and reported but not pooled:** cardiovascular death; worsening
heart failure events as defined in the trial source; all-cause death. They are
shown because a reader should see them; they are not pooled because the review's
estimand is the composite.

## 9. Risk of bias

**Tool.** Cochrane risk-of-bias tool for randomized trials, version 2 (RoB-2).

**Unit of assessment.** RoB-2 is applied **to the result being pooled, not to the
trial as a whole**: the composite of cardiovascular death or a worsening heart
failure event, expressed as a time-to-first-event hazard ratio. One trial may
therefore carry a different judgement for this result than it would for its own
primary endpoint, and that is the intended behaviour of the tool.

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

**Relationship to the recorded bias features.** Any existing bias-relevant
features in the object are **inputs to the assessment and never substitutes for a
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

## 10. Synthesis methods

Random-effects synthesis on the log hazard-ratio scale, inverse-variance
weighted. The active treatments are dapagliflozin 10 mg once daily and
empagliflozin 10 mg once daily, each compared with placebo. Placebo is the common
reference node.

**Pre-specified, so that reporting a disagreement between methods is a commitment
rather than a post-hoc observation:**

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
- A **prediction interval** is reported using the t distribution on k - 1 degrees
  of freedom per Handbook v6.5, and is not reported where k makes it undefined.
- The analysis is **cross-checked in a second engine** (R with metafor or netmeta,
  as appropriate to the estimand) at build time and the comparison published,
  including any quantity on which the two engines disagree by definition rather
  than by error.

**Heterogeneity:** tau-squared, I-squared with its Q-profile confidence interval,
and Q with its degrees of freedom and p value. I-squared is reported with the
caveat that at small k a low value reflects imprecision as much as agreement.

## 10A. Network geometry and what it forbids

This is a network. Its topology is derived from the object's own arms and is an
established fact, not an assumption:

| Quantity | Value |
|---|---|
| **Nodes** | dapagliflozin 10 mg once daily; empagliflozin 10 mg once daily; placebo |
| **Number of nodes** | 3 |
| **Edges** | dapagliflozin 10 mg once daily vs placebo; empagliflozin 10 mg once daily vs placebo |
| **Number of edges** | 2 |
| **Connected** | True |
| **Independent loops (E - V + 1)** | 0 |

There are zero loops. Indirect comparisons are computable because the network is
connected, but the consistency assumption they rest on **cannot be tested** - not
"was not tested", cannot be, by the geometry. Node-splitting and
design-by-treatment interaction are unavailable and their absence must never be
reported as consistency having been checked.

No SUCRA or ranking will be reported. Publication bias is **not assessable**
rather than not serious, and GRADE carries incoherence as untestable.

A head-to-head trial between the two non-comparator nodes, dapagliflozin 10 mg
once daily and empagliflozin 10 mg once daily, would add the missing active-active
edge. In this three-node network, that would create one closed loop, provide a
direct active-active estimate, and make a local inconsistency check possible for
that loop. It would not by itself make rankings clinically meaningful or remove
the need to judge transitivity.

## 11. Subgroup and sensitivity analyses

**Sensitivity, pre-specified:** leave-one-out where defined; the estimator
comparison above; active-drug separated contrasts against placebo; and, where
per-arm counts are recovered, the same 2x2 data pooled as a risk ratio, an odds
ratio and a risk difference - reported as sensitivity to the primary hazard-ratio
pool, never as the headline.

**Subgroup: none pre-specified.** The question spans the ejection fraction
spectrum, but any subgroup contrast would depend on trial-level strata and would
be underpowered. No subgroup result will be presented as though it were planned.

## 12. Meta-bias assessment

Funnel plot, Egger's regression and - for any count-based pool - Peters' test are
not interpreted as evidence about small-study effects in this held network. The
network has too few studies for publication bias to be assessed with useful
power, and the zero-loop geometry adds no independent check against selective
availability of comparisons. Publication bias is therefore reported as **not
assessable**, not as not serious.

## 13. Certainty of the evidence

GRADE, per Cochrane Handbook v6.5 sections 14.2.1-14.2.2 and MECIR C74/C75. All
five downgrade domains are assessed and **each rating is published with the
evidence it rests on**; the overall certainty is computed from the domains and
shown against them so a reader can check the arithmetic.

GRADE is **PENDING** at the time of this commit. When performed, GRADE carries
incoherence as untestable because the network has no independent loop.
Publication bias is carried as not assessable rather than not serious unless a
later amendment defines and justifies a different evidence base.

## 14. Data sharing and reproducibility

The canonical data object from which every number on the review page is projected
is published with the review, together with the R session information and the
analysis scripts actually executed. The intent is that the review can be rebuilt
from the object alone.

The protocol commit is pushed and anchored before the first query attempt. The
search record is anchored after the search execution so the operation is bounded
by two public log inclusion times. Any executed query that differs from section 5
is stored as a departure, not substituted into the protocol as though it had been
planned.

## 15. Funding and conflicts of interest

**No funding was received for this review.** No competing interests are declared
by the authors of this protocol at the time of this commit. Any change is to be
recorded as an amendment rather than by editing this section.

## 16. Amendments

No amendments at the time of this commit.

Amendments will be recorded as further commits to this file; the full commit
history, not only its head, is projected onto the review page, because a log that
displays only its own head is no better than a mutable document.
