# Protocol - Dapivirine vaginal ring versus placebo ring for HIV prevention in women

> **No prior protocol.** No file in `protocols/` covers this topic, so this document is the first protocol for it and supersedes nothing.

**Status: RETROSPECTIVELY REGISTERED BY COMMIT AND TRANSPARENCY-LOG ANCHOR. This document is the registration.**

This protocol is registered as a commit in a public repository, pushed to that
repository, and anchored in a public transparency log before the search lane runs
the first query. It contains no search results, no search yields, and no counts
returned by any search. It is retrospective because the topic object already held
evidence before this text was written.

The commit hash binds the text; the repository is public. The commit timestamp is
the weak half, and this document will not pretend otherwise. Both the author and
the committer date on a git commit are supplied by whoever makes the commit and
can be set to any value; commits here are unsigned, so the dates are forgeable
metadata rather than proof.

A transparency-log entry gives an inclusion time set by a third party, proving
something narrow: the text existed no later than the log time. It does not prove
when the commit was made, it does not prove that no earlier version existed
elsewhere, and it does not prove what was already known. The anchor proves WHEN
this text was written and CANNOT prove the trials had not already been seen. A
timestamp bounds when, never what was known.

**How to check this without us.** The verification recipe, the public half of the signing key, and a worked example are at [`ssot/registration/VERIFY.md`](../registration/VERIFY.md). It states the limitation plainly as well: the log time is independent of us, the key custody is not. A stranger can verify the text existed by the log time and that we signed it; a stranger cannot verify we did not hold an earlier version.

**It is written before the search runs.** The ordering test this review publishes
is that this commit precedes the first executed query, meaning the first attempt,
including a failed attempt, not the first successful execution. Reporting only
the successful execution would move the first-query time later and flatter the
claim.

Both sides of the operation are anchored. The protocol is committed, pushed and
anchored before the first query. The search record is anchored afterwards so two
third-party times bracket the operation. The databases return records and hit
counts, not authoritative execution times, so local query times are useful for
ordering but are not by themselves third-party proof.

---

## 1 - Review question, in PICO

This is a retrospectively registered protocol. This topic already holds 2 trials:
NCT01539226 and NCT01617096. The question is being authored after that evidence
was assembled, and the protocol therefore cannot be read as a claim that the
included trials had not already been seen.

| | |
|---|---|
| **Population** | Women at risk of HIV-1 infection. |
| **Intervention** | Dapivirine vaginal ring. |
| **Comparator** | Placebo vaginal ring. |
| **Outcome** | HIV-1 seroconversion during randomized follow-up. |
| **Study design** | Randomised controlled trials. |

**Frozen question:** Does a dapivirine vaginal ring reduce HIV-1 seroconversion
compared with a placebo vaginal ring in women?

## 2 - Estimand, stated in advance

The estimand is the **risk ratio for HIV-1 seroconversion**, on the log scale,
with the participant as the unit of analysis and the randomized comparison as the
contrast.

**Quantities that cannot be converted into that estimand are excluded on the
MEASURE axis, not on grounds of quality.** This is pre-specified because it is a
criterion and not a judgement made after seeing results. A trial may be large,
well conducted and directly relevant to HIV prevention and still fail this
review's eligibility because it reports something else. Specifically and in
advance:

- A **time-to-event hazard ratio** answers a different question from a
  dichotomous seroconversion risk ratio and will not be stored in a risk-ratio
  field.
- An **incidence rate ratio per person-time** shares direction with the risk
  ratio but has a different denominator and will not be pooled as the headline
  effect.
- A **within-arm incidence estimate** without a randomized placebo-ring
  comparator is not this estimand.
- Per-arm counts, when recovered, may be used to compute a risk ratio, odds ratio
  and risk difference. The risk ratio is the headline measure; the odds ratio and
  risk difference are sensitivity analyses only.

## 3 - Eligibility criteria

**Include** a study if all four axes hold: it is randomized; it enrols women at
risk of HIV-1 infection; it randomizes a dapivirine vaginal ring against a
placebo vaginal ring; and it reports HIV-1 seroconversion in a form that supports
the pre-specified risk-ratio estimand.

**Exclude** on any single failed axis -- population, intervention, comparator, or
measure -- and record which axis failed and what the study reports instead.

Populations narrower than the question, including age-band restrictions, are
**not** indirect on that ground alone. Narrowness is recorded and carried into
the GRADE indirectness domain rather than used as an exclusion.

Any axis read from a registry title is provisional until the registered primary
outcome measure is read from the outcome module. A title is not an outcome
definition.

## 4 - Information sources

PubMed through NCBI E-utilities and ClinicalTrials.gov API v2 only.

Embase was NOT searched. CENTRAL was NOT searched. Web of Science was NOT
searched. Scopus was NOT searched. This is not a comprehensive search.

The cost of that omission is explicit: eligible trials or publications indexed
only in those sources, or easier to discover through their citation indexing, may
be missed. If the two permitted sources reproduce the held set, that is evidence
about this constrained search and not evidence that the universe of evidence has
been exhausted.

## 4A - Linkage method and its known failure modes

Registry records are linked to publications before results extraction by a
fail-closed rule. A publication is linked to a registry record only when at least
one of these source-backed links is present: the PubMed record carries the NCT
identifier or trial identifier; the ClinicalTrials.gov record supplies a PMID or
citation in its references module; or the publication names the registered trial
identifier. The link is then checked against the registry record for the same
trial identity, intervention, comparator, population, and outcome module. A
publication that cannot be linked on those grounds remains unlinked rather than
being guessed from topic similarity.

Two failure modes are already known on this corpus and are measured before this
search is run:

- PubMed silently DROPS trials from ID-based queries when the record is not
  indexed, so an absent result is indistinguishable from a trial that does not
  exist.
- Registry `reference_type='result'` links can point at the WRONG paper, which is
  worse than a missing link because a wrong link looks like a successful one.

Where linkage succeeds, registry data matched the publication in 26 of 28
analyses compared on this corpus. That figure is conditional on linked analyses:
the denominator is linked analyses, not all analyses, and it is therefore not a
general reliability rate.

## 5 - Search strategy - the exact strings to be executed

These strings are stated **before** execution. The search lane will record what it
actually ran, on what date, with what filters, and how many records each
returned; any departure from the strings below will be recorded as a departure
rather than silently substituted. Each string is kept below 20 Boolean operators
so the registered string can be executed without forcing a first-attempt
departure.

**PubMed (NCBI E-utilities)**

```
(dapivirine[tiab] OR TMC120[tiab] OR "vaginal ring"[tiab] OR "MTN-020"[tiab] OR "IPM 027"[tiab])
AND ("HIV"[tiab] OR "HIV-1"[tiab])
AND (women[tiab] OR female[tiab])
AND (randomized[tiab] OR randomised[tiab] OR placebo[tiab] OR trial[tiab])
```

Filters: none on language, none on date.

**ClinicalTrials.gov (API v2)**

```
query.intr=dapivirine OR TMC120
query.cond=HIV
filter.overallStatus=COMPLETED|TERMINATED|ACTIVE_NOT_RECRUITING
```

Filters: none on location, sex, phase, funder type, date, or results-posting
status beyond the overall-status filter stated above.

## 5A - How this search can fail, decided in advance

Every possible search outcome is interpreted before execution:

- If the search reproduces the held set, the conclusion is that the two held
  trials were searched-for rather than merely convenient. It is not a claim that
  no other evidence exists outside the two searched sources.
- If the search returns additional eligible trials, that is a finding about the
  REVIEW. Each additional trial is named and included or excluded on one of the
  four pre-specified axes: population, intervention, comparator, or measure.
- If the search returns fewer trials than the object already holds, that is a
  finding about the SEARCH, never reported as the review being wrong.

Worked example for the third case: the finerenone-cv registry query missed
FIGARO-DKD (NCT02545049), a pivotal trial, because it registers its condition as
`Diabetic Kidney Disease` alone while its sibling FIDELIO-DKD registers `Chronic
Kidney Disease`. A narrow query looks exactly like a wrong review.

## 6 - Study selection process

Two **independent screeners of different model families** screen records. The
cross-family rule is a requirement, not a preference, because two instances of
one model is one screener run twice and its agreement statistic is meaningless.

Screening is in two stages: title and abstract, then full text or full registry
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

Extracted per trial and per outcome: registry identifier, primary publication,
year, design, population, arms, **the analysed denominator and the randomised
total separately**, per-arm HIV-1 seroconversion counts, and the published effect
estimate with its interval and its stated confidence level.

Eligibility classification is made against the axes declared in section 3 and no
others: population, intervention, comparator, and measure. An exclusion reason
must name one of those axes. A reason read from a registry title is provisional
until the registered primary outcome measure is read from the outcome module; a
title is not an outcome definition.

Every extracted cell carries a resolvable pointer to the specific document and,
where possible, to the table or registry module within it, so that a human check
can be made without leaving the page. **Nothing is computed that can be read.**
No count is derived from a percentage; no composite is reconstructed by summing
components. Identifiers are resolved by lookup, never from recall.

Where two populations exist for one outcome -- for example a full analysis set
and a randomized set -- both are recorded, exactly one is marked as selected, and
the population is named on the cell.

## 8 - Outcomes and prioritisation

**Primary:** HIV-1 seroconversion during randomized follow-up, expressed as a
risk ratio for dapivirine vaginal ring compared with placebo vaginal ring.

**Read and reported but not pooled as efficacy outcomes:** adherence or product
use measures; safety outcomes; HIV drug-resistance outcomes among participants
who seroconvert. They are shown because a reader should see them; they are not
pooled because the review's estimand is the HIV-1 seroconversion risk ratio.

## 9 - Risk of bias

**Tool.** Cochrane risk-of-bias tool for randomized trials, version 2 (RoB-2).

**Unit of assessment.** RoB-2 is applied **to the result being pooled, not to the
trial as a whole**: HIV-1 seroconversion during randomized follow-up, expressed
as a risk ratio. One trial may therefore carry a different judgement for this
result than it would for another endpoint, and that is the intended behaviour of
the tool.

**Variant.** The **effect of assignment to intervention** variant, because that
is what an intention-to-treat randomized comparison estimates. The adherence
variant is not used, and no result assessed under one variant will be reported as
though assessed under the other.

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

**Relationship to the recorded bias features.** The object may already hold
bias-relevant features. These are **inputs to the assessment and never
substitutes for a domain judgement**. No existing prose in the object may stand in
for a signalling question or a domain rating.

**Feeding GRADE.** The completed RoB-2 result becomes the basis of the GRADE
risk-of-bias domain, replacing any current reasoning from recorded features. When
it does, the review will state **whether the GRADE rating moves and why -- and if
it does not move, will say so explicitly** rather than leaving the reader to
infer that nothing changed.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No RoB-2 assessment is registered here. Performing it later
**executes this section rather than amending it**, and the object will record
that distinction.

## 10 - Synthesis methods

Random-effects meta-analysis on the log risk-ratio scale, inverse-variance
weighted.

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
- A **prediction interval** is reported using the t distribution on k-1 degrees
  of freedom per Handbook v6.5, and is not reported where k makes it undefined.
- The analysis is **cross-checked in a second engine** (R with metafor) at build
  time and the comparison published, including any quantity on which the two
  engines disagree by definition rather than by error.

**Zero-cell handling.** If any selected 2x2 table contains a zero cell, the
continuity correction used by the analysis engine is recorded on the output. A
computed cell correction is never hidden inside a stored extracted count.

**Heterogeneity:** tau^2, I^2 with its Q-profile confidence interval, and Q with
its degrees of freedom and p value. I^2 is reported with the caveat that at small
k a low value reflects imprecision as much as agreement.

## 10A - Static-versus-dynamic choices and hardcode disclosure

| Item | Status | How it is used |
|---|---|---|
| Review question | Static | Frozen in this protocol before the search lane runs. |
| Held trial IDs | Static object state | NCT01539226 and NCT01617096 are named because the object already held them before this retrospective registration. They are not search yields. |
| Search strings | Static | Executed as written or recorded as departures. |
| Search results | Dynamic | Not present in this protocol; read only after the protocol anchor. |
| Eligibility decisions | Dynamic | Classified only on the section 3 axes after records are read. |
| Extracted outcomes | Dynamic | Read from source-backed records and publications; not hardcoded from memory. |
| RoB-2 | Pending | Executed later from admissible sources. |
| GRADE | Pending | Executed later after RoB-2 and synthesis inputs exist. |

## 11 - Subgroup and sensitivity analyses

**Sensitivity, pre-specified:** leave-one-out where defined; the estimator
comparison above; and, where per-arm counts are recovered, the same 2x2 data
pooled as an odds ratio and a risk difference -- reported as sensitivity to the
primary risk-ratio pool, never as the headline.

Where person-time incidence rates are available, incidence rate ratios may be
read and shown as a sensitivity description, not pooled into the primary
risk-ratio analysis.

**Subgroup: none pre-specified.** With the small number of trials this comparison
is expected to have, any subgroup contrast would be underpowered and post-hoc,
and none will be presented as though it were planned.

## 12 - Meta-bias assessment

Funnel plot, Egger's regression and Peters' test for count-based pools.
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
implied as done.** No GRADE assessment is registered here. Performing it later
executes this section rather than amending it.

## 14 - Data sharing and reproducibility

The canonical data object from which every number on the review page is projected
is published with the review, together with the R session information and the
analysis scripts actually executed. The intent is that the review can be rebuilt
from the object alone.

The protocol anchor and the later search-record anchor are both retained. The
first bracket says the protocol text existed before the search attempt; the
second says the search record existed after the operation. The pair brackets the
operation and does not prove what anyone knew before the first anchor.

## 15 - Funding and conflicts of interest

**No funding was received for this review.** No competing interests are declared
by the authors of this protocol at the time of this commit. Any change is to be
recorded as an amendment rather than by editing this section.

## 16 - Amendments

No amendments exist at the registration commit.

Amendments will be recorded as further commits to this file; the full commit
history, not only its head, is projected onto the review page, because a log that
displays only its own head is no better than a mutable document.
