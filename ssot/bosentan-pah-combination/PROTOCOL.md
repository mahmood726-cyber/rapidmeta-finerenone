# Protocol - Bosentan added to established pulmonary arterial hypertension therapy: one trial has reported, and its design is invisible in the registry's arm fields

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

**Status: RETROSPECTIVELY REGISTERED BY COMMIT. This document is the registration.**

This protocol is registered as a commit in a public repository rather than in
PROSPERO. The commit hash binds the text; the repository is public. The commit
hash is the strong half of that record: the content is immutable under it, so
this text cannot be altered later without producing a different hash, and anyone
can check that much without asking us.

**The commit timestamp is the weak half, and this document will not pretend
otherwise.** The commit timestamp is author-supplied and forgeable: git author
and committer dates are set by whoever makes the commit, and commits here are
unsigned. GitHub stores and displays what it is given. A transparency-log entry
gives an inclusion time set by a third party, proving something narrow: the text
existed no later than the log time. It does not prove when the commit was made,
it does not prove that no earlier version existed elsewhere, and it does not
prove what was already known.

**How to check this without us.** The verification recipe, the public half of the signing key, and a worked example are at [`ssot/registration/VERIFY.md`](../registration/VERIFY.md). It states the limitation plainly as well: the log time is independent of us, the key custody is not. A stranger can verify the text existed by the log time and that we signed it; a stranger cannot verify we did not hold an earlier version.

**It is written before the new search runs, but it is not written before the
evidence was first seen.** The ordering test this review publishes is that this
protocol commit is committed, pushed, and anchored in a public transparency log
before the first executed query for the search registered below. The first query
means the earliest query attempt, including a failed attempt, not the first
successful response. Reporting only the successful execution would move the
first-query time later and flatter the claim.

The search record is anchored afterwards, so two third-party transparency-log
times bracket the operation: one for this text before the search and one for the
search record after it. Those anchors prove only that each text existed no later
than its log time. They do not prove what was known before either text was
written. A timestamp bounds when, never what was known.

This file contains no search results, no search yields, and no counts returned
from any search. Counts already held in the canonical object are named only as
pre-existing object state, not as findings from the search this protocol
registers.

---

## 1. Review question, in PICO

This topic already holds 7 trials: NCT00120380, NCT00303459, NCT01100736,
NCT01352065, NCT03053739, NCT04039464, and NCT06317805. The question is being
authored after that evidence was assembled. However carefully it is written now,
this is a retrospectively registered protocol. The anchor proves when this text
was written and cannot prove the trials had not already been seen.

| | |
|---|---|
| **Population** | Adults with pulmonary arterial hypertension already receiving a PAH-specific therapy. |
| **Intervention** | Bosentan added to that established PAH-specific therapy. |
| **Comparator** | Continuing the established PAH-specific therapy alone, including placebo add-on where placebo preserves background therapy. |
| **Outcome** | Morbidity and mortality, prioritising time to first morbidity or mortality event where reported. |
| **Study design** | Randomised controlled trials. |

**Frozen question:** In adults with pulmonary arterial hypertension already
receiving a PAH-specific therapy, what is the effect of adding bosentan, compared
with continuing that therapy alone, on morbidity and mortality?

## 2. Estimand, stated in advance

The headline estimand is the **time-to-first-event hazard ratio for morbidity or
mortality**, on the log scale, with the participant as the unit of analysis and
the time to the first qualifying event as the event time.

The event definition is accepted only from a trial report, registry outcome
module, protocol, or statistical analysis plan. A title can alert the reader to a
possible morbidity or mortality endpoint, but a title is not an outcome
definition.

**Quantities that cannot be converted into that estimand are excluded on the
MEASURE axis, not on grounds of quality.** This is stated before execution
because it is a criterion and not a judgement made after seeing results. A trial
may be large, well conducted, and directly on topic and still fail this review's
eligibility because it reports something else. Specifically and in advance:

- A **recurrent-event rate ratio** counts repeat events per person over time; a
  time-to-first hazard ratio counts each person once, at their first event. The
  two share a scale and a direction and answer different questions. A rate ratio
  will not be stored in a hazard-ratio field.
- A **win ratio** over a hierarchical composite is not this estimand.
- A **dichotomous risk ratio** at a fixed timepoint is not this estimand, though
  where per-arm counts are recovered a risk ratio, odds ratio and risk difference
  will be computed and reported as **sensitivity analyses only**, never as the
  headline.
- A **change in six-minute walk distance**, haemodynamic endpoint, or functional
  class endpoint is not the morbidity or mortality estimand. It may be extracted
  as context, but it will not enter the headline pool.

## 3. Eligibility criteria

**Include** a study if all five axes hold:

- **DESIGN:** participants are randomised.
- **POPULATION:** participants are adults with pulmonary arterial hypertension
  and are already receiving a PAH-specific therapy at randomisation.
- **INTERVENTION:** bosentan is added to the established PAH-specific therapy as
  the randomised contrast.
- **COMPARATOR:** the comparator is the established PAH-specific therapy alone,
  with or without placebo add-on.
- **MEASURE:** the study reports, or provides enough information to extract, a
  morbidity or mortality outcome as the time-to-first-event hazard ratio defined
  in Section 2.

**Exclude** on any single failed axis - DESIGN, POPULATION, INTERVENTION,
COMPARATOR, or MEASURE - and record which axis failed and what the study reports
or randomises instead. These are the only exclusion axes for this protocol.

The seven trials already held by the object are candidates, not proof of
eligibility under this protocol. Each is read again against the axes above. A
trial that entered the object because the design was inferred from a registry
title remains provisional until the arms, interventions, eligibility module, and
outcome module have been read. Any axis read from a registry title is
provisional until the registered primary outcome measure is read from the outcome
module: a title is not an outcome definition.

Populations narrower than the question are **not** indirect on that ground alone;
narrowness is recorded and carried into the GRADE indirectness domain rather
than used as an exclusion.

## 4. Information sources

PubMed (NCBI E-utilities) and ClinicalTrials.gov API v2 only.

Embase was NOT searched, nor CENTRAL, Web of Science, or Scopus. This is a narrow
two-source search and the review's discovery claim is limited to PubMed,
ClinicalTrials.gov API v2, and the seven trial identifiers already held in the
canonical object. The cost of the omission is that records indexed only in the
omitted services, conference material present only there, registry records
outside ClinicalTrials.gov, and citations missed by the stated PubMed and
ClinicalTrials.gov strings may be absent from the review.

No backward citation search, forward citation search, hand search, regulatory
document search, or non-ClinicalTrials.gov registry search is registered for this
review.

## 4A. Linkage method and its known failure modes

A registry record will be linked to a publication before extraction by exact NCT
identity wherever possible. The planned linkage order is:

- Query PubMed through NCBI E-utilities for each known NCT identifier and for the
  known-identifier string in Section 5.
- Read the ClinicalTrials.gov API v2 references module for references marked as
  result publications.
- Accept a link only after the candidate publication and registry record match
  on the NCT identifier or, where the identifier is absent from the publication,
  on trial name, intervention, population, comparator structure, and outcome
  definition.
- Treat every automatic link as provisional until the publication itself is read.

Two failure modes are already measured on this corpus and are named before this
search executes.

First, PubMed silently drops trials from ID-based queries when the record is not
indexed, so an absent result is indistinguishable from a trial that does not
exist. A missing PubMed return is therefore a linkage failure, not evidence that
there is no publication.

Second, registry `reference_type='result'` links can point at the wrong paper.
That is worse than a missing link because a wrong link looks like a successful
one. A result reference is not accepted as identity until the paper has been read
against the registry record.

Where linkage succeeds, registry data matched the publication in 26 of 28
analyses compared on this corpus. That is a conditional figure whose denominator
is linked analyses, not all analyses, and therefore not a general reliability
rate.

## 5. Search strategy - the exact strings to be executed

These strings are stated **before** execution. The search lane will record what
it actually ran, on what date, with what filters, and how many records each
returned; any departure from the strings below will be recorded as a departure
rather than silently substituted. Each registered string is kept under 20 Boolean
operators because the execution interface refuses longer strings.

**PubMed discovery search (NCBI E-utilities)**

```
(bosentan[tiab] OR Tracleer[tiab])
AND ("pulmonary arterial hypertension"[tiab] OR "pulmonary hypertension"[MeSH Terms] OR PAH[tiab])
AND (sildenafil[tiab] OR iloprost[tiab] OR treprostinil[tiab] OR tadalafil[tiab] OR prostacyclin[tiab] OR combination[tiab] OR "add-on"[tiab])
AND (randomized controlled trial[pt] OR randomised[tiab] OR randomized[tiab] OR trial[tiab])
```

Filters: none on language, none on date. Rationale: a language or date filter
would narrow the record set for reasons not part of the eligibility criteria.

**PubMed known-identifier resolution (NCBI E-utilities)**

```
NCT00120380[si] OR NCT00303459[si] OR NCT01100736[si] OR NCT01352065[si] OR NCT03053739[si] OR NCT04039464[si] OR NCT06317805[si]
```

Filters: none on language, none on date.

**ClinicalTrials.gov discovery search (API v2)**

```
query.intr=bosentan OR Tracleer
query.cond=pulmonary arterial hypertension OR pulmonary hypertension
query.term=sildenafil OR iloprost OR treprostinil OR tadalafil OR prostacyclin OR combination OR add-on
filter.overallStatus=COMPLETED|TERMINATED|ACTIVE_NOT_RECRUITING|RECRUITING
```

**ClinicalTrials.gov known-identifier resolution (API v2)**

```
query.id=NCT00120380 OR NCT00303459 OR NCT01100736 OR NCT01352065 OR NCT03053739 OR NCT04039464 OR NCT06317805
```

No source outside PubMed and ClinicalTrials.gov API v2 is part of the registered
search.

## 5A. How this search can fail, decided in advance

Three readings are fixed before execution.

**A. The search reproduces the held set.** That is evidence that the seven held
trial identifiers were searched-for rather than convenient. It is not evidence
that the search was exhaustive, because the sources are deliberately limited to
PubMed and ClinicalTrials.gov API v2.

**B. The search returns additional eligible trials.** That is a finding about
the review. Each additional trial will be named and included or excluded on a
stated axis from Section 3. If eligible, it changes the canonical object rather
than being treated as a nuisance record.

**C. The search returns fewer trials than the object holds.** That is a finding
about the search, never reported as the review being wrong. Worked example: the
finerenone-cv registry query missed FIGARO-DKD (NCT02545049), a pivotal trial,
because it registers its condition as "Diabetic Kidney Disease" alone while its
sibling FIDELIO-DKD registers "Chronic Kidney Disease". A narrow query looks
exactly like a wrong review.

## 6. Study selection process

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

## 7. Data extraction

Every candidate record is classified against the five axes declared in Section 3
and against no others: DESIGN, POPULATION, INTERVENTION, COMPARATOR, and MEASURE.
For each failed axis, the extraction table records the text that made it fail. A
candidate is not excluded for a reason outside those axes.

Extracted per trial and per outcome: registry identifier, primary publication,
year, design, population, background PAH therapy, randomised arms, the analysed
denominator and the randomised total separately, per-arm event counts where
reported, and the published effect estimate with its interval and its stated
confidence level.

Every extracted cell carries a resolvable pointer to the specific document and,
where possible, to the table or registry module within it, so that a human check
can be made without leaving the page. **Nothing is computed that can be read.**
No count is derived from a percentage; no composite is reconstructed by summing
its components. Identifiers are resolved by lookup, never from recall.

Any axis read from a registry title is provisional until the registered primary
outcome measure is read from the outcome module. A title can describe a trial,
but it is not an outcome definition. The add-on design is expected to be fragile
in registry arm fields because background PAH therapy may not be encoded as a
registered intervention; when the arm fields do not carry the distinction, the
source of the design classification is named rather than treated as coded fact.

Where two populations exist for one outcome - for example a full analysis set
and a randomised set - both are recorded, exactly one is marked as selected, and
the population is named on the cell.

## 8. Outcomes and prioritisation

**Primary:** morbidity or mortality as a time-to-first-event hazard ratio.

**Components, read and reported but not pooled unless they become separately
eligible outcomes by amendment:** all-cause death; PAH-related death;
hospitalisation for worsening pulmonary arterial hypertension; clinical
worsening; lung transplantation; atrial septostomy; treatment failure or rescue
therapy where it is part of the registered morbidity or mortality definition.
They are shown because a reader should see them; they are not pooled as the
headline because the review's estimand is the composite.

Functional class, six-minute walk distance, haemodynamic measures, biomarkers,
and adverse events are extracted as descriptors or safety context when they are
available. They do not replace the primary morbidity or mortality estimand.

## 9. Risk of bias

**Tool.** Cochrane risk-of-bias tool for randomized trials, version 2 (RoB-2).

**Unit of assessment.** RoB-2 is applied **to the result being pooled, not to the
trial as a whole**: morbidity or mortality expressed as a time-to-first-event
hazard ratio. One trial may therefore carry a different judgement for this
result than it would for its own primary endpoint, and that is the intended
behaviour of the tool.

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

**Relationship to the recorded bias features.** Bias-relevant features already
stored on the object are **inputs to the assessment and never substitutes for a
domain judgement**. No existing prose in the object may stand in for a signalling
question or a domain rating.

**Feeding GRADE.** The completed RoB-2 result becomes the basis of the GRADE
risk-of-bias domain, replacing any reasoning from recorded features. When it
does, the review will state **whether the GRADE rating moves and why - and if it
does not move, will say so explicitly** rather than leaving the reader to infer
that nothing changed.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No RoB-2 assessment exists for these trials in this protocol.
Performing it later **executes this section rather than amending it**, and the
object will record that distinction.

## 10. Synthesis methods

Where at least two eligible trials report the primary estimand, random-effects
meta-analysis will be run on the log hazard-ratio scale, inverse-variance
weighted.

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

**Heterogeneity:** tau2, I2 with its Q-profile confidence interval, and Q with
its degrees of freedom and p value. I2 is reported with the caveat that at small
k a low value reflects imprecision as much as agreement.

## 10A. Single-reported-trial and no-pool rules

If fewer than two eligible trials report the same primary estimand, no
meta-analysis is run. A single contributing result is reported as a single trial
result, not as a pooled estimate with a missing heterogeneity section.

An eligible trial without posted results contributes to the evidence map and to
the account of withheld or unavailable evidence. It does not contribute zero
events, an imputed hazard ratio, or any denominator invented from enrolment.

If a later search or update identifies a second eligible report of the same
estimand, Section 10 becomes executable. That later execution changes the object
state; it does not amend this rule.

## 11. Subgroup and sensitivity analyses

**Sensitivity, decided in advance:** leave-one-out where defined; the estimator
comparison above; and, where per-arm counts are recovered, the same 2 by 2 table
pooled as a risk ratio, an odds ratio and a risk difference - reported as
sensitivity to the primary hazard-ratio pool, never as the headline.

**Subgroup: none stated in advance.** With the small number of trials this
comparison is expected to have, any subgroup contrast would be underpowered and
post-hoc, and none will be presented as though it was planned. Background PAH
therapy, PAH aetiology, baseline functional class, and trial duration are
extracted as descriptors and GRADE inputs, not as planned subgroup tests.

## 12. Meta-bias assessment

Funnel plot, Egger's regression and - for any count-based pool - Peters' test.
**Caveat decided in advance:** below approximately ten studies these tests have
almost no power and the Cochrane Handbook advises against interpreting them.
Where k is below that threshold the tests may still be computed for completeness,
and will be reported as computed values, explicitly not as evidence about
small-study effects. Where publication bias cannot be assessed, the GRADE domain
will read *not assessable* rather than *not serious* - the two are different
statements.

## 13. Certainty of the evidence

GRADE, per Cochrane Handbook v6.5 sections 14.2.1-14.2.2 and MECIR C74/C75. All
five downgrade domains are assessed and **each rating is published with the
evidence it rests on**; the overall certainty is computed from the domains and
shown against them so a reader can check the arithmetic.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No GRADE assessment exists for this review in this protocol.
Performing it later executes this section rather than amending it.

## 14. Data sharing and reproducibility

The canonical data object from which every number on the review page is
projected is published with the review, together with the analysis scripts
actually executed and the session information for each analysis engine. The
intent is that the review can be rebuilt from the object alone.

The protocol anchor, the later search-record anchor, the canonical object, and
the executed search transcript are stored together so the ordering record can be
read without asking the authors.

## 15. Funding and conflicts of interest

**No funding was received for this review.** No competing interests are declared
by the authors of this protocol at the time of this commit. Any change is to be
recorded as an amendment rather than by editing this section.

## 16. Amendments

None at this registration commit.

Amendments will be recorded as further commits to this file; the full commit
history, not only its head, is projected onto the review page, because a log that
displays only its own head is no better than a mutable document.
