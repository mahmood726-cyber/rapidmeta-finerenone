# Protocol - Bosentan in children with pulmonary hypertension: two trials have reported, and they measure different things

**Status: RETROSPECTIVELY REGISTERED BY COMMIT. This document is the retrospective registration.**

This protocol is registered as a commit in a public repository rather than in
PROSPERO. The commit hash is the strong half of that record: the content is
immutable under it, so this text cannot be altered later without producing a
different hash, and anyone can check that much without asking us.

**The commit timestamp is the weak half, and this document will not pretend
otherwise.** Both the author and the committer date on a git commit are supplied
by whoever makes the commit and can be set to any value; GitHub stores and
displays what it is given, and the commits here are unsigned. The timestamp
therefore cannot prove when the commit was made.

What the mechanism supports, and no more: this exact text is bound to this hash;
the repository is public, so the text is readable by anyone at that hash; and
where an entry for the commit exists in a public transparency log, that log's
inclusion time is an upper bound on when this text existed, set by a third party
rather than by us. A transparency-log entry proves something narrow: **the text
existed no later than the log time**.

What it does not support: it does not prove the commit was made when it says it
was, it does not prove that no earlier or parallel version existed elsewhere, it
does not prove the data had not already been seen, and it says nothing about the
independence of the people who wrote it. Those are claims about conduct, and no
timestamp can carry them.

**How to check this without us.** The verification recipe, the public half of the signing key, and a worked example are at [`ssot/registration/VERIFY.md`](../registration/VERIFY.md). It states the limitation plainly as well: the log time is independent of us, the key custody is not. A stranger can verify the text existed by the log time and that we signed it; a stranger cannot verify we did not hold an earlier version.

**It is written before the search runs.** This protocol must be committed,
pushed, and anchored in a public transparency log before the first search query
runs. The ordering test this review publishes is that this commit precedes the
first executed query, including the first failed attempt, not the first
successful execution. Reporting only the first success would move the
first-query time later and flatter the claim.

The search record is anchored afterwards, so two third-party inclusion times
bracket the operation: one before the search and one after the search record is
written. The databases return hit counts, not trustworthy external execution
times. The lane's own clock records attempts; the transparency log bounds when
the text and the later search record existed. This is an ordering audit, not
proof about what was known.

No search result, search yield, screening count, effect estimate, or result from
any search is recorded in this protocol.

---

## 1 - Review question, in PICO

| | |
|---|---|
| **Population** | Children with pulmonary arterial hypertension or persistent pulmonary hypertension of the newborn. |
| **Intervention** | Bosentan. |
| **Comparator** | Placebo, inactive control, standard care without bosentan, or an alternative bosentan regimen. |
| **Outcome** | Clinical outcomes, including survival, clinical worsening, treatment failure, need for pulmonary-hypertension rescue therapy, respiratory support, or other registered patient-relevant clinical outcomes. |
| **Study design** | Randomised controlled trials. |

**Frozen question:** in children with pulmonary arterial hypertension or
persistent pulmonary hypertension of the newborn, what is the effect of bosentan
compared with placebo or an alternative regimen on clinical outcomes?

This topic already holds 2 trials: NCT01223352 and NCT01389856. The question is
being authored after that evidence was assembled. However carefully it is
written now, this is a **retrospectively registered protocol**, not an advance
registration. The anchor proves WHEN this text was written, in the narrow sense
that the text existed no later than the log time, and CANNOT prove the trials had
not already been seen. A timestamp bounds when, never what was known.

## 2 - Estimand, stated in advance

The target estimand is the comparative effect of bosentan on a **shared clinical
outcome** in randomised paediatric pulmonary-hypertension trials. The participant
is the unit of analysis. The effect scale is determined by the registered and
published outcome definition: time-to-event outcomes are handled on the log
hazard-ratio scale; dichotomous outcomes on the log risk-ratio scale; continuous
outcomes on the mean-difference scale when the scale is common and clinically
interpretable.

No result is pooled unless at least two eligible trials report the same clinical
outcome on a compatible scale. If the eligible trials measure different clinical
constructs, or if one trial reports only non-clinical pharmacokinetic exposure,
the synthesis is withdrawn for lack of a shared estimand rather than forced into
a misleading pooled number.

**Quantities that cannot be converted into the shared clinical estimand are
excluded from the primary synthesis on the MEASURE axis, not on grounds of
quality.** This is a criterion and not a judgement made after seeing results. A
trial may be well conducted and directly relevant to paediatric bosentan and
still fail this review's synthesis eligibility because it reports something
else. Specifically and in advance:

- A **pharmacokinetic exposure endpoint** is not a clinical outcome and will not
  be stored in a clinical-effect field.
- A **dose-regimen contrast** in which every participant receives bosentan is a
  regimen comparison. It is not a bosentan-versus-no-bosentan drug-effect
  contrast, and it will be labelled as such.
- A **time-to-event hazard ratio**, a **binary risk ratio**, and a **continuous
  mean difference** answer different questions. They will not be pooled together
  merely because all are favourable or unfavourable to bosentan.

## 3 - Eligibility criteria

**Include** a study if all four hold: it is randomised; it enrols children with
pulmonary arterial hypertension or persistent pulmonary hypertension of the
newborn; it randomises bosentan against placebo, inactive control, standard care
without bosentan, or an alternative bosentan regimen; and it reports a registered
clinical outcome in a form usable for the review's estimand.

**Exclude** on any single failed axis - population, intervention, comparator, or
measure - and record which axis failed and what the study reports instead.
Section 7 will classify records against these axes and no others.

The population axis excludes adults and excludes pulmonary-hypertension
populations that are not paediatric pulmonary arterial hypertension or persistent
pulmonary hypertension of the newborn. Mixed-age studies are eligible only when
the paediatric stratum is randomised and extractable.

The intervention axis excludes endothelin-receptor antagonists other than
bosentan when bosentan is not an assigned intervention. The comparator axis
separates bosentan versus no bosentan from alternative bosentan regimen
comparisons; both are eligible to the review question, but they are not pooled as
the same contrast.

The measure axis excludes outcomes that are pharmacokinetic, pharmacodynamic,
growth-only, laboratory-only, or administrative-only unless the same record also
reports a registered patient-relevant clinical outcome. Any axis read from a
registry title is provisional until the registered primary outcome measure is
read from the outcome module: a title is not an outcome definition.

## 4 - Information sources

PubMed through NCBI E-utilities and ClinicalTrials.gov API v2 are the only
databases searched for this registration run.

Embase was **not** searched. CENTRAL was **not** searched. Web of Science was
**not** searched. Scopus was **not** searched. This is not a comprehensive
search. The cost of that omission is predictable: conference records, records
indexed only outside PubMed, trials indexed under unexpected terms, and
bibliographic links curated in CENTRAL or Embase can be missed. Any missing
trial caused by that restricted source set is a limitation of the search, not
evidence that the trial does not exist.

## 4A - Linkage method and its known failure modes

Registry records will be linked to publications before data extraction by this
sequence:

- Query ClinicalTrials.gov API v2 for candidate registry records.
- Read each candidate record's NCT identifier, conditions, arms, interventions,
  design, recruitment status, primary outcome module, and reference module.
- Query PubMed through NCBI E-utilities using the NCT identifier and the planned
  topic string.
- Accept a publication link only when the NCT identifier, trial acronym or
  title, arms, population, intervention, comparator, and registered outcome
  module align between the registry record and the publication.
- Treat registry result references as candidates, not proof, until the target
  publication is checked against the registry fields.

Two linkage failure modes have already been measured on this corpus and are
named before this search runs.

First, PubMed silently DROPS trials from ID-based queries when the record is not
indexed, so an absent result is indistinguishable from a trial that does not
exist. Absence from an ID-based PubMed query is therefore not evidence of
absence.

Second, registry `reference_type='result'` links can point at the WRONG paper,
which is worse than a missing link because a wrong link looks like a successful
one. A registry result reference is therefore checked, not trusted.

Where linkage succeeds, registry data matched the publication in 26 of 28
analyses compared on this corpus. That is a conditional figure whose denominator
is **linked analyses**, not all analyses, and it is therefore not a general
reliability rate.

## 5 - Search strategy - the exact strings to be executed

These strings are stated **before** execution. The search lane will record what
it actually ran, on what date, with what filters, and how many records each
returned; any departure from the strings below will be recorded as a departure
rather than silently substituted. Each string is kept below 20 Boolean operators
so the interface can execute it without forcing a departure on the first attempt.

**PubMed (NCBI E-utilities)**

```
(bosentan[tiab] OR Tracleer[tiab])
AND (children[tiab] OR pediatric[tiab] OR paediatric[tiab] OR newborn[tiab] OR neonate[tiab])
AND ("pulmonary hypertension"[tiab] OR "pulmonary arterial hypertension"[tiab] OR PPHN[tiab])
AND (randomized[tiab] OR randomised[tiab] OR trial[tiab] OR placebo[tiab])
```

Filters: none on language, none on date, none on publication type beyond the
text string above. Rationale: a language, date, or publication-type filter would
narrow the record set for reasons not part of the eligibility criteria.

**ClinicalTrials.gov (API v2)**

```
query.intr=bosentan OR Tracleer
query.cond=pulmonary hypertension OR pulmonary arterial hypertension OR persistent pulmonary hypertension of the newborn OR PPHN
filter.advanced=AREA[StudyType]INTERVENTIONAL AND AREA[DesignAllocation]RANDOMIZED
```

Filters: none on start date, completion date, country, phase, sponsor, sex,
age, recruitment status, or results posting. These fields are read during
eligibility assessment rather than used to suppress records before screening.

No backward citation search, forward citation search, registry outside
ClinicalTrials.gov, or bibliographic database outside PubMed is registered for
this review.

## 5A - How this search can fail, decided in advance

The interpretation of each possible search outcome is fixed before execution.

If the search reproduces the held set, it will be reported as searched-for rather
than convenient. The two trials already on the object are not treated as proof
that the search was unnecessary; the search has to find them by the registered
method.

If the search returns additional eligible trials, that is a finding about the
review. Each candidate will be named and included or excluded on one of the
registered axes: population, intervention, comparator, or measure. A new trial is
not rejected because it was not already on the object.

If the search returns fewer trials than the object already holds, that is a
finding about the search, never reported as the review being wrong. A failed
search string can miss a real trial for reasons unrelated to the review
question.

Worked example decided in advance: the finerenone-cv registry query missed
FIGARO-DKD (NCT02545049), a pivotal trial, because it registers its condition as
"Diabetic Kidney Disease" alone while its sibling FIDELIO-DKD registers "Chronic
Kidney Disease". A narrow query looks exactly like a wrong review.

## 6 - Study selection process

Two **independent screeners of different model families** are required. The
cross-family rule is a requirement, not a preference, because two instances of
one model is one screener run twice and its agreement statistic is meaningless.

Screening is in two stages: title and abstract or registry summary, then full
text and full registry record. **Each screener's decision is recorded per record
at the stage it was applied**, together with the reason. Both screeners'
decisions are published, not only the reconciled outcome, along with the
agreement rate and how every disagreement was resolved.

**Adjudication of disagreements is by a named human.**

**Two release tiers, and the difference between them is attestation, not
content.** The website release requires the two cross-family AI assessments and
states plainly that it has not been human-verified. The submission release
additionally requires two named human reviewers to have checked every included
study and every extracted datum; the statement to that effect is emitted only
when those attestation records exist and is never written as unsupported prose.

## 7 - Data extraction

Extracted per trial and per outcome: registry identifier, primary publication,
year, design, population, arms, **the analysed denominator and the randomised
total separately**, per-arm event counts or continuous-outcome summaries where
applicable, and the published effect estimate with its interval and its stated
confidence level.

Eligibility and exclusion will be classified against the axes declared in
section 3 and no others: population, intervention, comparator, and measure. A
registry title may guide screening, but any axis read from a registry TITLE is
provisional until the registered primary outcome measure is read from the
outcome module: a title is not an outcome definition.

Every extracted cell carries a resolvable pointer to the specific document and,
where possible, to the table or registry module within it, so that a human check
can be made without leaving the page. **Nothing is computed that can be read.**
No count is derived from a percentage; no composite is reconstructed by summing
its components. Identifiers are resolved by lookup, never from recall.

Where two populations exist for one outcome, for example a full analysis set and
a randomised set, both are recorded, exactly one is marked as selected, and the
population is named on the cell.

## 8 - Outcomes and prioritisation

**Primary:** a shared patient-relevant clinical outcome across eligible
randomised paediatric bosentan trials. The first eligible shared outcome by this
priority order is selected: mortality; clinical worsening or treatment failure;
need for rescue pulmonary-hypertension therapy; time to discontinuation of
respiratory support; hospitalisation or intensive-care outcome; functional
capacity; symptom or quality-of-life outcome.

**Read and reported but not pooled as the primary outcome:** pharmacokinetic
exposure, pharmacodynamic markers, growth-only endpoints, laboratory-only
endpoints, adverse events, and clinical outcomes that are unique to a single
trial. They are shown because a reader should see them; they are not pooled when
they do not share the review's estimand.

If no outcome is shared by at least two eligible trials, the meta-analysis is not
run. That state is reported as absence of a shared estimand, not as zero effect,
not as failed extraction, and not as evidence that bosentan has no clinical
effect in children.

## 9 - Risk of bias

**Tool.** Cochrane risk-of-bias tool for randomized trials, version 2 (RoB-2).

**Unit of assessment.** RoB-2 is applied **to the result being pooled, not to the
trial as a whole**. If no result is pooled, RoB-2 is applied separately to each
included trial's eligible clinical result and is not collapsed into a single
pooled-result judgement.

**Variant.** The **effect of assignment to intervention** variant is used,
because that is what a randomized intention-to-treat comparison estimates. The
adherence variant is not used, and no result assessed under one variant will be
reported as though assessed under the other.

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

Meta-analysis is run only where at least two eligible trials report the same
clinical outcome on a compatible effect scale for a compatible contrast.

For time-to-event outcomes, random-effects meta-analysis is on the log
hazard-ratio scale, inverse-variance weighted. For dichotomous outcomes,
random-effects meta-analysis is on the log risk-ratio scale. For continuous
outcomes measured on the same instrument and timepoint, random-effects
meta-analysis is on the mean-difference scale.

Methods fixed in this protocol:

- **REML** is the headline between-study-variance estimator.
- The **Hartung-Knapp-Sidik-Jonkman interval is reported alongside** the Wald
  interval, and where the two disagree about whether the interval crosses the
  null, that disagreement is reported in the results rather than resolved by
  choosing one.
- **Leave-one-out** analysis is run and reported for every pool where it is
  defined.
- An **estimator comparison** - DerSimonian-Laird, REML, Paule-Mandel - is run
  and reported, on the understanding that with few studies the choice is
  plausibly influential.
- A **prediction interval** is reported using the t distribution on k-1 degrees
  of freedom and is not reported where k makes it undefined.
- The analysis is **cross-checked in a second engine** at build time and the
  comparison published, including any quantity on which the two engines disagree
  by definition rather than by error.

**Zero-cell handling.** If any selected 2x2 table contains a zero cell, the
continuity correction used by the analysis engine is recorded on the output. A
computed cell correction is never hidden inside a stored extracted count.

**Heterogeneity:** tau-squared, I-squared with its confidence interval where
defined, and Q with its degrees of freedom and p value. I-squared is reported
with the caveat that at small k a low value reflects imprecision as much as
agreement.

If no shared clinical outcome exists, no model is run, no pooled estimate is
reported, and heterogeneity is marked not assessable. That is a synthesis result
about estimand compatibility, not a substitute effect estimate.

## 10A - Static-versus-dynamic choices and hardcode disclosure

| Item | Status | How it is used |
|---|---|---|
| Review question | Static | Frozen in this protocol before the search lane runs. |
| Held trial IDs | Static object state | NCT01223352 and NCT01389856 are named because the object already held them before this retrospective registration. They are not search yields. |
| Search strings | Static | Executed as written or recorded as departures. |
| Search results | Dynamic | Not present in this protocol; read only after the protocol anchor. |
| Eligibility decisions | Dynamic | Classified only on the section 3 axes after records are read. |
| Outcome definitions | Dynamic | Read from registry outcome modules and publications; registry titles alone are provisional. |
| Extracted outcomes | Dynamic | Read from source-backed records and publications; not hardcoded from memory. |
| RoB-2 | Pending | Executed later from admissible sources. |
| GRADE | Pending | Executed later after RoB-2 and synthesis inputs exist. |

## 11 - Subgroup and sensitivity analyses

**Sensitivity, pre-specified:** leave-one-out where defined; the estimator
comparison above; and, where per-arm counts are recovered, the same 2x2 data
pooled as an odds ratio and a risk difference - reported as sensitivity to the
primary risk-ratio pool, never as the headline.

Where time-to-event and count-based versions of the same clinical outcome are
both available, they are shown side by side rather than treated as
interchangeable. A pharmacokinetic endpoint is not used as a sensitivity analysis
for a clinical outcome.

**Subgroup: none pre-specified.** With the small number of candidate trials
already named for this question, any subgroup contrast would be underpowered and
post-hoc, and none will be presented as though it were planned.

## 12 - Meta-bias assessment

Funnel plot, Egger's regression and - for any count-based pool - Peters' test.
**Pre-specified caveat:** below approximately ten studies these tests have
almost no power and the Cochrane Handbook advises against interpreting them.
Where k is below that threshold the tests may still be computed for
completeness, and will be reported as computed values, explicitly not as
evidence about small-study effects. Where publication bias cannot be assessed,
the GRADE domain will read *not assessable* rather than *not serious* - the two
are different statements.

## 13 - Certainty of the evidence

GRADE, per Cochrane Handbook v6.5 sections 14.2.1-14.2.2 and MECIR C74/C75. All
five downgrade domains are assessed and **each rating is published with the
evidence it rests on**; the overall certainty is computed from the domains and
shown against them so a reader can check the arithmetic.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No GRADE assessment exists for this review in this protocol.
Performing it later executes this section rather than amending it.

## 14 - Data sharing and reproducibility

The canonical data object from which every number on the review page is
projected is published with the review, together with the R session information
and the analysis scripts actually executed. The intent is that the review can be
rebuilt from the object alone.

The protocol commit and its pre-search transparency-log entry are stored with
the canonical object. The post-search search record and its transparency-log
entry are stored with the same object, so the registration text and the executed
search record can be read together.

## 15 - Funding and conflicts of interest

**No funding was received for this review.** No competing interests are declared
by the authors of this protocol at the time of this commit. Any change is to be
recorded as an amendment rather than by editing this section.

## 16 - Amendments

None at this registration commit.

Amendments will be recorded as further commits to this file; the full commit
history, not only its head, is projected onto the review page, because a log that
displays only its own head is no better than a mutable document.
