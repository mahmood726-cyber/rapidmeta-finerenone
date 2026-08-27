# Protocol - RTS,S/AS01 and R21/Matrix-M against clinical malaria

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
PROSPERO. The commit hash is the strong half of that record: the content is
immutable under it, so this text cannot be altered later without producing a
different hash, and anyone can check that much without asking us.

**The commit timestamp is the weak half, and this document will not pretend
otherwise.** Both the author and the committer date on a git commit are supplied
by whoever makes the commit and can be set to any value; GitHub stores and
displays what it is given, and an unsigned commit carries nothing further. The
commit hash binds the text; the repository is public. The commit timestamp is
author-supplied and forgeable. A transparency-log entry gives an inclusion time
set by a third party, proving something narrow: **the text existed no later than
the log time**. It does not prove when the commit was made, that no earlier
version existed elsewhere, or what was already known.

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

**It is written before the search runs.** The ordering test this review publishes
is that this protocol is committed, pushed, and anchored in a public transparency
log before the first executed query. The first executed query means the first
attempt, including a failed attempt, not the first success. Reporting only the
successful execution would move the first-query time later and flatter the claim.
The search record is anchored afterwards, so two third-party log times bracket
the operation.

This document contains no results, no yields, and no counts from any search. The
databases timestamp none of this ordering for us. The protocol anchor can prove
only that this text existed no later than the log time. The post-search anchor can
prove only that the search record existed no later than its log time. Together
they make the sequence auditable; they do not prove what the reviewers knew.

---

## 1 - Review question, in PICO

| | |
|---|---|
| **Population** | Randomised cohorts in malaria-endemic settings for which clinical malaria is reported. |
| **Intervention** | RTS,S/AS01 or R21/Matrix-M, analysed separately by vaccine and by regimen where the source requires it. |
| **Comparator** | Inactive or comparator-vaccine control for vaccine efficacy pools; active-comparator contrasts are carried separately and not converted into efficacy against no protection. |
| **Outcome** | Clinical malaria, using only cohorts that report the same effect measure within a pool, with the estimand and follow-up window stated on every row. |
| **Study design** | Randomised controlled trials and randomised cohorts within trials. |

**Frozen question:** For each of the two malaria vaccines separately, what is the
efficacy against clinical malaria across the randomised cohorts that report the
SAME EFFECT MEASURE for clinical malaria, aligned on every dimension the sources
permit and crossing the rest with each difference named on the pool that crosses
it -- and where does that differ from the published synthesis of the same
literature? The question does NOT claim these cohorts estimate identical
quantities. Each pool records whether they do, and neither of them does.

This topic already holds 8 trials. The question is being authored after that
evidence was assembled. However carefully it is written now, this is a
retrospectively registered protocol. The anchor proves when this text was written
and cannot prove the trials had not already been seen. A timestamp bounds when,
never what was known.

The trial registrations already on the object are NCT00081744, NCT00380393,
NCT00436007, NCT00866619, NCT03143218, NCT03276962, NCT03896724, and
NCT04704830. That list is stated as existing object state, not as the product of
the search to be run under this protocol.

## 2 - Estimand, stated in advance

The estimand is vaccine-specific efficacy against clinical malaria on the log
ratio scale, never a combined RTS,S-plus-R21 effect. The selected effect measure
is named on the pool before synthesis: log hazard ratio for time-to-first-event
clinical malaria pools, log rate ratio or other explicitly named log ratio for
episode-rate pools, and no conversion between those measures unless the source
or a pre-specified statistical rule supplies one.

The row is the unit at which the estimand is made explicit. Every row states the
vaccine, regimen, comparator, population, clinical-malaria definition as far as
the source permits, effect measure, analysis population, and follow-up window. A
pool is eligible only when its contributing rows share the same effect measure.
It may still cross other differences; those differences are named on the pool
rather than hidden by the pooled value.

**Quantities that cannot be converted into the stated pool estimand are excluded
from that pool on the MEASURE axis, not on grounds of quality.** A trial may be
large, well conducted and directly on topic and still fail a pool's eligibility
because it reports a different quantity. Specifically and in advance:

- A hazard ratio and a rate ratio are different effect measures and are not
  pooled together.
- A first-episode endpoint and an all-episode endpoint are different estimands
  unless the source and row definition state why they are the same quantity.
- A contrast against seasonal chemoprevention or another active intervention is
  not an efficacy estimate against no protection.
- A percentage efficacy without a recoverable ratio, interval, confidence level,
  and estimand remains a carried result and is not promoted into a pooled log
  ratio.

## 3 - Eligibility criteria

**Include** a study or cohort in a pool if all five hold: it is randomised; it
evaluates RTS,S/AS01 or R21/Matrix-M; it reports clinical malaria; it reports the
same effect measure required by that vaccine-specific pool; and the source gives
enough information to state the estimand and follow-up window on the row.

**Exclude from a pool** on any single failed axis -- population, intervention,
comparator, outcome, or measure -- and record which axis failed and what the
study reports instead. These are the only exclusion axes used by this protocol.
A row may be included in the object, shown as a carried contrast, and excluded
from a specific pool; that is not a contradiction if the failed axis is recorded.

Population, schedule, dose, case-definition, comparator, follow-up-window, and
analysis-population differences that do not fail a declared axis are recorded as
alignment fields. They are then either held constant within a pool or crossed
with the difference named. A title is not an outcome definition: any axis read
from a registry title is provisional until the registered primary outcome measure
is read from the outcome module.

## 4 - Information sources

The only information sources searched under this protocol are PubMed through NCBI E-utilities and ClinicalTrials.gov API v2. Embase was not searched. CENTRAL
was not searched. Web of Science was not searched. Scopus was not searched. This
is not a comprehensive search.

The cost of that omission is real: trials or reviews indexed outside PubMed, or
indexed in PubMed without the terms used here, can be missed; conference-only
records and records discoverable mainly through CENTRAL or Embase can be missed;
and citation-network recovery is deliberately weaker than it would be in a full
systematic-review search. Any such miss is a limitation of the search, not proof
that the trial or review does not exist.

## 4A - Linkage method and its known failure modes

Before the search runs, a registry record will be linked to a publication only by
a recorded, checkable path. The preferred path is an NCT identifier in a PubMed
record or full text that names the same registry record. The second path is a
ClinicalTrials.gov reference in the study record, after checking that the cited
paper's trial identifier, intervention, comparator, population, and clinical
malaria outcome match the registry record. Where neither path succeeds, the
record remains unlinked rather than being matched by memory or topic resemblance.

Two failure modes are already measured on this corpus and are named before
execution. First, PubMed silently drops trials from ID-based queries when the
record is not indexed, so an absent result is indistinguishable from a trial that
does not exist. Second, registry `reference_type='result'` links can point at the
wrong paper, which is worse than a missing link because a wrong link looks like a
successful one.

Where linkage succeeds, registry data matched the publication in 26 of 28
analyses compared on this corpus. That is a conditional figure: the denominator
is linked analyses, not all analyses, and therefore it is not a general
reliability rate for registry-publication linkage.

## 5 - Search strategy - the exact strings to be executed

These strings are stated **before** execution. The search lane will record what
it actually ran, on what date, with what filters, and what each query returned;
any departure from the strings below will be recorded as a departure rather than
silently substituted. Each PubMed Boolean string is kept under 20 Boolean
operators because a registered string that cannot be executed forces a departure
on the first attempt.

**PubMed, primary trials**

```
(("RTS,S"[tiab] OR "RTS,S/AS01"[tiab] OR R21[tiab] OR "R21/Matrix-M"[tiab])
AND (malaria[tiab] OR "Malaria"[Mesh])
AND vaccin*[tiab]
AND (randomized[tiab] OR randomised[tiab] OR trial[tiab]))
```

Filters: none on language, none on date.

**PubMed, published syntheses of the same literature**

```
(("RTS,S"[tiab] OR "RTS,S/AS01"[tiab] OR R21[tiab] OR "R21/Matrix-M"[tiab])
AND malaria[tiab]
AND ("systematic review"[pt] OR "meta-analysis"[pt] OR meta-analysis[tiab] OR pooled[tiab]))
```

Filters: none on language, none on date.

**PubMed, registry-publication linkage checks**

```
NCT00081744[si] OR NCT00081744[tiab]
NCT00380393[si] OR NCT00380393[tiab]
NCT00436007[si] OR NCT00436007[tiab]
NCT00866619[si] OR NCT00866619[tiab]
NCT03143218[si] OR NCT03143218[tiab]
NCT03276962[si] OR NCT03276962[tiab]
NCT03896724[si] OR NCT03896724[tiab]
NCT04704830[si] OR NCT04704830[tiab]
```

Each line is a separate PubMed E-utilities query.

**ClinicalTrials.gov API v2, trial discovery**

```
query.intr=RTS,S OR RTS,S/AS01 OR R21 OR R21/Matrix-M
query.cond=malaria
```

No status, date, phase, age, or geography filter is applied at search. Those
features are read after retrieval and classified only against the axes in
section 3.

**ClinicalTrials.gov API v2, object-record refresh**

```
GET https://clinicaltrials.gov/api/v2/studies/NCT00081744
GET https://clinicaltrials.gov/api/v2/studies/NCT00380393
GET https://clinicaltrials.gov/api/v2/studies/NCT00436007
GET https://clinicaltrials.gov/api/v2/studies/NCT00866619
GET https://clinicaltrials.gov/api/v2/studies/NCT03143218
GET https://clinicaltrials.gov/api/v2/studies/NCT03276962
GET https://clinicaltrials.gov/api/v2/studies/NCT03896724
GET https://clinicaltrials.gov/api/v2/studies/NCT04704830
```

## 5A - How this search can fail, decided in advance

Every possible search outcome is interpreted before execution.

If the search reproduces the held set, it is reported as searched-for rather than
convenient. That outcome would show that the pre-registered sources and strings
recover the object already assembled; it would not prove no other trial exists.

If the search returns additional eligible trials, that is a finding about the
review. Each additional trial is named and either included or excluded on one of
the axes in section 3. Additional eligible trials are not treated as a nuisance
created by the search; they are the reason to run it.

If the search returns fewer trials than the object holds, that is a finding about
the search, never reported as the review being wrong. Worked example decided in
advance: the finerenone-cv registry query missed FIGARO-DKD (NCT02545049), a
pivotal trial, because it registers its condition as "Diabetic Kidney Disease"
alone while its sibling FIDELIO-DKD registers "Chronic Kidney Disease". A narrow
query looks exactly like a wrong review.

## 6 - Study selection process

Two **independent screeners of different model families** will screen every
record returned by the registered searches. The cross-family rule is a
requirement, not a preference, because two instances of one model is one screener
run twice and its agreement statistic is meaningless.

Screening is in two stages: title and abstract, then full text or registry record
where available. **Each screener's decision is recorded per record at the stage
it was applied**, together with the reason and the failed axis if excluded. Both
screeners' decisions are published, not only the reconciled outcome, along with
the agreement rate and how every disagreement was resolved.

**Adjudication of disagreements is by a named human.**

**Two release tiers, and the difference between them is attestation, not
content.** The website release requires the two cross-family AI assessments and
states plainly that it has not been human-verified. The submission release
additionally requires two named human reviewers to have checked every included
study and every extracted datum; the statement to that effect is emitted only
when those attestation records exist and is never written as prose.

## 7 - Data extraction

Extracted per trial, per cohort, per arm, and per clinical-malaria result:
registry identifier, primary publication, year, design, population, arms,
comparator, vaccine, regimen, dose or schedule label, clinical-malaria case
definition, analysis population, follow-up window, analysed denominator and
randomised total separately, per-arm event counts or person-time where reported,
and the published effect estimate with its interval and stated confidence level.

Every extracted cell carries a resolvable pointer to the specific document and,
where possible, to the table, figure, registry module, or quoted sentence within
it, so that a human check can be made without leaving the page. **Nothing is
computed that can be read.** No count is derived from a percentage; no composite
is reconstructed by summing its components; no hazard ratio is converted into a
rate ratio; and no active-comparator ratio is converted into vaccine efficacy
against no protection. Identifiers are resolved by lookup, never from recall.

Section 7 classifies records against the axes declared in section 3 and no
others: population, intervention, comparator, outcome, and measure. Schedule,
dose, case-definition, follow-up-window, and analysis-population differences are
alignment fields unless they fail one of those axes. Any axis read from a
registry title is provisional until the registered primary outcome measure is
read from the outcome module: a title is not an outcome definition.

Where two populations exist for one outcome, both are recorded, exactly one is
marked as selected, and the population is named on the cell. Where a trial
contains multiple randomised cohorts or multiple eligible arms sharing a
comparator, the choice of contrast is recorded before pooling so that the same
control group is not silently counted twice.

## 8 - Outcomes and prioritisation

**Primary:** vaccine-specific clinical-malaria efficacy on the log scale, pooled
only within rows that share the same effect measure. R21/Matrix-M and RTS,S/AS01
are not pooled with each other. The estimand and follow-up window are stated on
every row.

**Secondary, read and reported but not promoted into the headline:** vaccine- or
regimen-specific clinical-malaria results that are eligible for the object but
not for a pool; clinical-malaria contrasts against active comparators; results
whose ratio type is not named by the source; safety outcomes; immunogenicity
outcomes; and published-synthesis conclusions about the same literature.

Published syntheses are compared on scope, included-set ascertainability,
vaccine separation, effect measure, outcome definition, follow-up window, and
whether their reported quantity can be matched to a quantity in this object. No
numeric agreement or disagreement is claimed unless the same quantity is
identified on both sides.

## 9 - Risk of bias

**Tool.** Cochrane risk-of-bias tool for randomized trials, version 2 (RoB-2).

**Unit of assessment.** RoB-2 is applied **to the result being pooled, not to the
trial as a whole**: the clinical-malaria result expressed in the effect measure
selected for its vaccine-specific pool. One trial may therefore carry a different
judgement for this result than it would for another endpoint, and that is the
intended behaviour of the tool.

**Variant.** The **effect of assignment to intervention** variant, because that
is what an intention-to-treat or assignment-based clinical-malaria contrast
estimates. The adherence variant is not used, and no result assessed under one
variant will be reported as though assessed under the other.

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

**Relationship to recorded bias features.** The object may hold bias-relevant
features such as masking, endpoint rank within its own trial, early stopping,
analysis population, or endpoint adjudication. These are **inputs to the
assessment and never substitutes for a domain judgement**. No existing prose in
the object may stand in for a signalling question or a domain rating.

**Feeding GRADE.** The completed RoB-2 result becomes the basis of the GRADE
risk-of-bias domain, replacing any reasoning from recorded features. When it
does, the review will state **whether the GRADE rating moves and why -- and if it
does not move, will say so explicitly** rather than leaving the reader to infer
that nothing changed.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No final RoB-2 assessment is registered by this protocol.
Performing it later **executes this section rather than amending it**, and the
object will record that distinction.

## 10 - Synthesis methods

Random-effects meta-analysis on the selected log effect-measure scale,
inverse-variance weighted, run separately by vaccine and by pool. A hazard-ratio
pool stays on the log hazard-ratio scale. A rate-ratio pool stays on the log
rate-ratio scale. A pool that crosses a follow-up-window, schedule,
case-definition, analysis-population, or comparator-class difference names that
difference on the pool and does not describe the contributors as estimating
identical quantities.

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
- The analysis is **cross-checked in a second engine** (R with metafor) at build
  time and the comparison published, including any quantity on which the two
  engines disagree by definition rather than by error.

**Heterogeneity:** tau^2, I^2 with its Q-profile confidence interval, and Q with
its degrees of freedom and p value. I^2 is reported with the caveat that at small
k a low value reflects imprecision as much as agreement.

Differences from published syntheses of the same literature are tabulated before
interpretation. The comparison is not allowed to collapse all differences into
"ours versus theirs"; it must name whether the difference is vaccine grouping,
trial/cohort counting, effect measure, clinical-malaria definition, follow-up
window, comparator, age band, analysis population, or a source-linkage failure.

## 10A - Network geometry and what it forbids

This is a network. Its topology is derived from the object's own arms and is an
established fact, not an assumption: nodes: 19; edges: 24; connected: False;
independent loops (E - V + 1): 6.

The treatment nodes named on the object include R21 with Matrix-M; R21 with the
higher adjuvant dose (group 2); R21 with the lower adjuvant dose (group 1);
RTS,S full doses with a booster at month twenty (group R012-20); RTS,S full
doses with three further annual doses (group R012-14-26-38); RTS,S on the
delayed third-dose schedule; RTS,S on the earlier three-dose schedule; and
RTS,S with delayed fractional doses (group Fx017-20-32). Additional control and
schedule nodes are retained in the object even when they do not define a pooled
vaccine-specific efficacy result.

The disconnected topology forbids a single network effect across the whole
object. It also forbids pretending that all observed contrasts are exchangeable
arms of one comparison. Multi-arm trials are handled as multi-arm trials: a
shared comparator is not counted twice inside one pairwise pool, and selecting a
regimen-specific contrast is recorded as a relevance decision under the review
question rather than hidden as data cleaning.

The independent loops are not a license to combine vaccines. They are a warning
that the object contains enough geometry for consistency questions, while the
disconnected components and regimen-specific nodes limit which questions can be
answered. This protocol therefore performs vaccine-specific pairwise syntheses
and documents carried contrasts; it does not publish a connected network
meta-analysis unless a later amendment specifies a valid connected estimand and
the data support it.

## 11 - Subgroup and sensitivity analyses

**Sensitivity, pre-specified:** leave-one-out; the estimator comparison above;
Wald versus Hartung-Knapp-Sidik-Jonkman intervals; exclusion of rows that cross a
follow-up-window difference within a pool; exclusion of rows that cross a
case-definition difference within a pool; and, where per-arm counts are recovered
and the effect measure permits it, the same 2x2 pooled as a risk ratio, an odds
ratio and a risk difference -- reported as sensitivity to the primary log-ratio
pool, never as the headline.

**Subgroup: none pre-specified as confirmatory.** With the small number of
randomised cohorts expected for each vaccine-specific pool, subgroup contrasts by
age band, transmission setting, schedule, dose, or seasonality would be
underpowered and vulnerable to post-hoc interpretation. If shown, they are
labelled descriptive.

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
implied as done.** No final GRADE assessment is registered by this protocol.
Performing it later executes this section rather than amending it.

## 14 - Data sharing and reproducibility

The canonical data object from which every number on the review page is
projected is published with the review, together with the R session information,
the Python environment where used, the PubMed E-utilities calls, the
ClinicalTrials.gov API v2 calls, the linkage decisions, and the analysis scripts
actually executed. The intent is that the review can be rebuilt from the object
alone.

The protocol commit is pushed and anchored before the first query attempt. The
search record is anchored after execution. If a query fails, the failed attempt
is still the first query time for ordering purposes and is recorded.

## 15 - Funding and conflicts of interest

**No funding was received for this review.** No competing interests are declared
by the authors of this protocol at the time of this commit. Any change is to be
recorded as an amendment rather than by editing this section.

## 16 - Amendments

No amendments exist at the time of this commit.

Amendments will be recorded as further commits to this file; the full commit
history, not only its head, is projected onto the review page, because a log that
displays only its own head is no better than a mutable document.
