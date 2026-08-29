# Protocol - Colchicine for stroke prevention

**Status: RETROSPECTIVELY REGISTERED BY COMMIT, PUBLIC PUSH, AND TRANSPARENCY-LOG ANCHOR. This document is the registration.**

This protocol is registered as a commit in a public repository rather than in
PROSPERO. The commit hash is the strong half of that record: the content is
immutable under it, so this text cannot be altered later without producing a
different hash, and anyone can check that much without asking us.

**The commit timestamp is the weak half, and this document will not pretend
otherwise.** The commit timestamp is author-supplied and forgeable. Both the
author and the committer date on a git commit are supplied by whoever makes the
commit and can be set to any value; commits here are unsigned and carry nothing
further.

What the mechanism supports, and no more: this exact text is bound to this hash;
the repository is public, so the text is readable by anyone at that hash; and
where an entry for the commit exists in a public transparency log, that log's
inclusion time is an upper bound on when this text existed, set by a third party
rather than by us. The transparency-log entry proves something narrow: the text
existed no later than the log time.

What it does not support: it does not prove the commit was made when it says it
was, it does not prove that no earlier or parallel version existed elsewhere, it
does not prove the trials had not already been seen, and it says nothing about
the independence of the people who wrote it. Those are claims about conduct, and
no timestamp can carry them. A timestamp bounds when, never what was known.

**How to check this without us.** The verification recipe, the public half of the signing key, and a worked example are at [`ssot/registration/VERIFY.md`](../registration/VERIFY.md). It states the limitation plainly as well: the log time is independent of us, the key custody is not. A stranger can verify the text existed by the log time and that we signed it; a stranger cannot verify we did not hold an earlier version.

**It is written before the search runs.** This file contains no search results,
no search yields, and no hit counts from any search to be run under this protocol.
The ordering rule for this review is: protocol committed, pushed to the public
repository, and anchored in a public transparency log before the first query is
attempted. The ordering test uses the EARLIEST query time INCLUDING A FAILED
ATTEMPT. It does not use the first successful query, because reporting only the
successful execution would move the first-query time later and flatter the claim.

The search record is anchored afterwards so two third-party times bracket the
operation. The first anchor proves only that this text existed no later than the
log time. The second anchor proves only that the search record existed no later
than its log time. The bracket does not prove what was known before the first
anchor, and this retrospective protocol does not claim that it does.

---

## 1 - Review question, in PICO

| | |
|---|---|
| **Population** | Adults with cerebrovascular disease, including ischemic stroke, transient ischemic attack, intracranial atherosclerotic disease, atrial fibrillation populations recruited for stroke prevention, or other stroke-prevention cerebrovascular populations. |
| **Intervention** | Colchicine, at the dose and schedule each trial randomised. |
| **Comparator** | The comparator each trial randomised, recorded exactly as registered or published. |
| **Outcome** | Recurrent stroke or vascular events, using the registered primary outcome and relevant registered stroke or vascular outcomes before any publication result is interpreted. |
| **Study design** | Randomised controlled trials. |

**Frozen question:** in adults with cerebrovascular disease, does colchicine
reduce recurrent stroke or vascular events against the comparator each trial
randomised?

This topic already holds 9 trials. The nine trial identifiers on the object are
NCT02282098, NCT02898610, NCT05439356, NCT05476991, NCT05503225, NCT06102720,
NCT06352632, NCT06396858, and NCT07035405.

The question is being authored after that evidence was assembled. However
carefully it is written now, this is a retrospectively registered protocol. The
anchor proves when this text existed and cannot prove the trials had not already
been seen.

## 2 - Estimand, stated in advance

The target estimand is the treatment effect of randomised colchicine assignment
versus the comparator each trial randomised on recurrent stroke or vascular
events in adults with cerebrovascular disease.

Where trials report a time-to-first-event hazard ratio for a stroke or vascular
event outcome that matches the review question, the log hazard ratio is the
preferred effect scale. Where a trial reports only event counts for the same
target outcome, risk ratio, odds ratio and risk difference are recorded as
count-based summaries. These are not interchangeable with a hazard ratio and
will not be stored in a hazard-ratio field.

Quantities that cannot be connected to the target estimand are excluded on the
OUTCOME/MEASURE axis, not on grounds of quality. A trial may be large, well
conducted and directly informative for another question and still fail this
review's eligibility because it reports a different population, intervention,
comparator, outcome, or measure.

## 3 - Eligibility criteria

**Include** a study if all five hold: it is randomised; it enrols adults with
cerebrovascular disease or a cerebrovascular stroke-prevention population; it
randomises colchicine; it randomises colchicine against a concurrent comparator;
and it reports recurrent stroke or vascular events in a form that can be
classified against the target outcome or measure.

**Exclude** on any single failed axis - DESIGN, POPULATION, INTERVENTION,
COMPARATOR, or OUTCOME/MEASURE - and record which axis failed and what the record
shows instead. These are the only exclusion axes for this review.

Populations narrower than the question are not indirect on that ground alone.
Narrowness is recorded and carried into the GRADE indirectness domain rather than
used as an exclusion.

Any axis read from a registry title is provisional until the registered primary
outcome measure is read from the outcome module. A title is not an outcome
definition.

## 4 - Information sources

PubMed through NCBI E-utilities and ClinicalTrials.gov API v2 are the only
databases searched under this protocol.

Embase was NOT searched. CENTRAL was NOT searched. Web of Science was NOT
searched. Scopus was NOT searched. This source set is deliberately limited.

The cost of those omissions is plain: trials or publications indexed only in
those sources, conference records with no PubMed record, and records whose
ClinicalTrials.gov entry cannot be retrieved or correctly linked may be missed.
The review may therefore under-detect eligible trials and may under-detect
publications for trials already present on the object.

## 4A - Linkage method and its known failure modes

Registry records will be linked to publications before result extraction by two
routes.

First, each ClinicalTrials.gov API v2 record is read for its references module.
References of any type are retained as candidate links. A reference marked
`result` is not accepted merely because the registry gives it that type; it must
be checked against the trial identifier, population, intervention, comparator,
and outcome details before it is treated as the primary result publication.

Second, PubMed is queried by trial registration identifier through NCBI
E-utilities. A missing PubMed result is not treated as evidence that no
publication exists. It means only that this linkage route did not resolve one.

Two failure modes are known in advance and are measured on this corpus:

- PubMed silently drops trials from ID-based queries when the record is not
  indexed, so an absent result is indistinguishable from a trial that does not
  exist.
- Registry `reference_type='result'` links can point at the wrong paper, which is
  worse than a missing link because a wrong link looks like a successful one.

Where linkage succeeds, registry data matched the publication in 26 of 28
analyses compared on this corpus. That is a conditional figure: the denominator
is linked analyses, not all analyses, and therefore it is not a general
reliability rate.

## 5 - Search strategy - the exact strings to be executed

These strings are stated before execution. The search lane will record what it
actually ran, on what date, with what filters, and how many records each returned;
any departure from the strings below will be recorded as a departure rather than
silently substituted. Each string is kept under 20 Boolean operators because the
interface refuses more, and a registered string that cannot be executed would
force a departure on the first attempt.

**PubMed (NCBI E-utilities)**

```
(colchicine[tiab] OR colcrys[tiab])
AND ("Stroke"[Mesh] OR stroke[tiab] OR cerebrovascular[tiab] OR "transient ischemic attack"[tiab] OR "transient ischaemic attack"[tiab] OR TIA[tiab])
AND (randomized controlled trial[pt] OR randomized[tiab] OR randomised[tiab] OR trial[tiab])
```

Filters: none on language, none on date, none on publication type beyond the
terms inside the query.

**ClinicalTrials.gov (API v2)**

```
query.intr=colchicine
query.cond=stroke OR cerebrovascular disease OR transient ischemic attack OR transient ischaemic attack
filter.studyType=INTERVENTIONAL
```

Filters: no overall-status filter, no phase filter, no date filter, no geography
filter, and no sponsor filter.

## 5A - How this search can fail, decided in advance

Every search outcome is interpreted before execution.

**If the search reproduces the held set**, that is reported as searched-for rather
than convenient. The finding would be that the registered search recovered the
trials already held by the object, not that the original assembly process was
unbiased or complete.

**If the search returns additional eligible trials**, that is a finding about the
review. Each additional trial is named and included or excluded on one of the
five stated axes: DESIGN, POPULATION, INTERVENTION, COMPARATOR, or
OUTCOME/MEASURE. No additional axis is introduced after seeing the record.

**If the search returns fewer trials than the object holds**, that is a finding
about the search, never reported as the review being wrong. A narrow query can
look exactly like a wrong review. The worked example is the finerenone-cv
registry query: it missed FIGARO-DKD (NCT02545049), a pivotal trial, because that
trial registers its condition as "Diabetic Kidney Disease" alone while its
sibling FIDELIO-DKD registers "Chronic Kidney Disease".

## 6 - Study selection process

Two independent screeners of different model families are required. The
cross-family rule is a requirement, not a preference, because two instances of
one model is one screener run twice and its agreement statistic is meaningless.

Screening is in two stages: title and abstract or registry summary, then full
record or full text. Each screener's decision is recorded per record at the stage
it was applied, together with the reason. Both screeners' decisions are
published, not only the reconciled outcome, along with the agreement rate and how
every disagreement was resolved.

Adjudication of disagreements is by a named human.

Two release tiers are allowed, and the difference between them is attestation,
not content. The website release requires the two cross-family AI assessments and
states plainly that it has not been human-verified. The submission release
additionally requires two named human reviewers to have checked every included
study and every extracted datum; the statement to that effect is emitted only
when those attestation records exist and is never written as unsupported prose.

## 7 - Data extraction

Extracted per trial and per outcome: registry identifier, primary publication if
resolved, year, design, population, arms, comparator as randomised, the analysed
denominator and the randomised total separately, per-arm event counts where
reported, the published effect estimate with its interval and its stated
confidence level where reported, and the registered outcome title, description,
rank and time frame.

Every candidate record is classified only on the five axes declared in Section 3:
DESIGN, POPULATION, INTERVENTION, COMPARATOR, and OUTCOME/MEASURE. Section 7 does
not create additional exclusion axes.

Every extracted cell carries a resolvable pointer to the specific document and,
where possible, to the table, figure, outcome module, or results module within
it, so that a human check can be made without leaving the page. Nothing is
computed that can be read. No count is derived from a percentage; no composite is
reconstructed by summing its components. Identifiers are resolved by lookup, never
from recall.

Where the registry title suggests an outcome category, that category remains
provisional until the registered primary outcome measure is read from the outcome
module. A title is not an outcome definition.

Where two populations exist for one outcome - for example a full analysis set and
a randomised set - both are recorded, exactly one is marked as selected, and the
population is named on the cell.

## 8 - Outcomes and prioritisation

**Primary:** recurrent stroke or vascular events in adults with cerebrovascular
disease, using each trial's registered primary outcome when it matches that
target and otherwise using the highest-ranked registered stroke or vascular event
outcome that matches the target.

**Components, read and reported but not automatically pooled:** ischemic stroke;
hemorrhagic stroke; fatal or non-fatal stroke; transient ischemic attack; major
adverse cardiovascular events; myocardial infarction; vascular death; all-cause
death; revascularization; and functional neurological outcomes when a trial
registers them. They are shown because a reader should see what each trial
measured. They are pooled only when the outcome definition and effect measure
match closely enough to make the pool answer the stated question.

## 9 - Risk of bias

**Tool.** Cochrane risk-of-bias tool for randomized trials, version 2 (RoB-2).

**Unit of assessment.** RoB-2 is applied to the result being used for this
review, not to the trial as a whole. One trial may therefore carry a different
judgement for this result than it would for its own primary endpoint, and that is
the intended behaviour of the tool.

**Variant.** The effect of assignment to intervention variant, because that is
what an intention-to-treat randomised comparison estimates. The adherence variant
is not used, and no result assessed under one variant will be reported as though
assessed under the other.

**Domains.** All five, each reached through the RoB-2 signalling questions rather
than by overall impression, with a recorded answer per signalling question, a
domain judgement of low / some concerns / high, and a rationale naming the
evidence it rests on:

1. Bias arising from the randomization process
2. Bias due to deviations from intended interventions (effect of assignment)
3. Bias due to missing outcome data
4. Bias in measurement of the outcome
5. Bias in selection of the reported result

An overall judgement follows the standard RoB-2 algorithm: low only if every
domain is low; high if any domain is high or if multiple domains raise some
concerns in a way that substantially lowers confidence; some concerns otherwise.

**Assessors.** Two independent assessors from different model families. Two
instances of one model is one assessor run twice and its agreement statistic is
meaningless, so same-family duplication does not satisfy this requirement.
Neither assessor may be the agent that assembled the canonical object, because
assessing one's own extraction is not an independent assessment.

Both sets of judgements are recorded and published - per domain, per assessor,
with rationales - not only the reconciled outcome. The per-domain agreement rate
is published as measured. Agreement on RoB-2 domains is expected to be
substantially lower than agreement on screening; if that proves true it is a
finding worth reporting and it will not be smoothed. Disagreements are
adjudicated by a named human, and the adjudication and its reason are recorded
per disagreement.

**Evidence admissible to an assessment.** The trial's registry record including
its protocol and statistical analysis plan where posted, the primary publication
and its supplement where resolved, and the posted results module where available.
A judgement made from an abstract alone is not the same act as one made from a
protocol, so the sources actually consulted are recorded per domain, and a domain
judged without access to the protocol is marked as such rather than presented as
equivalent.

**Relationship to the recorded bias features.** The object may already hold
bias-relevant features. These are inputs to the assessment and never substitutes
for a domain judgement. No existing prose in the object may stand in for a
signalling question or a domain rating.

**Feeding GRADE.** The completed RoB-2 result becomes the basis of the GRADE
risk-of-bias domain. When it does, the review will state whether the GRADE rating
moves and why - and if it does not move, will say so explicitly rather than
leaving the reader to infer that nothing changed.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No RoB-2 assessment is completed for this protocol by this
document. Performing it later executes this section rather than amending it, and
the object will record that distinction.

## 10 - Synthesis methods

No meta-analysis is run unless at least two eligible trials report sufficiently
compatible outcomes and effect measures for the same clinical question. A review
need not contain a meta-analysis, and absence of a pool is reported as absence of
a pool rather than as a negative finding about colchicine.

For compatible time-to-first-event outcomes, random-effects meta-analysis is run
on the log hazard-ratio scale, inverse-variance weighted.

For compatible count-based outcomes, random-effects meta-analysis is run on the
log risk-ratio scale, with odds ratio and risk difference reported as sensitivity
analyses when the cell counts permit them.

Specified before execution, so that reporting a disagreement between methods is a
commitment rather than a post-hoc observation:

- REML is the headline between-study-variance estimator.
- The Hartung-Knapp-Sidik-Jonkman interval is reported alongside the Wald
  interval, and where the two disagree about whether the interval crosses the
  null, that disagreement is reported in the results rather than resolved by
  choosing one.
- Leave-one-out analysis is run and reported for every pool with enough studies
  to make it defined.
- An estimator comparison - DerSimonian-Laird, REML, Paule-Mandel - is run and
  reported, per Cochrane Handbook v6.5 section 10.10.4.4, on the understanding
  that with few studies the choice is plausibly influential.
- A prediction interval is reported using the t distribution on k-1 degrees of
  freedom per Handbook v6.5, and is not reported where k makes it undefined.
- The analysis is cross-checked in a second engine, R with metafor, at build time
  and the comparison published, including any quantity on which the two engines
  disagree by definition rather than by error.

**Heterogeneity:** tau-squared, I-squared with its Q-profile confidence interval,
and Q with its degrees of freedom and p value. I-squared is reported with the
caveat that at small k a low value reflects imprecision as much as agreement.

## 10A - Static-vs-dynamic hardcode disclosure

| Item | Fixed before execution | Dynamic after execution | Failure rule |
|---|---|---|---|
| Review question | The stored question in Section 1. | None. | Any change is an amendment, not a silent edit. |
| Held trial identifiers | The object already holds 9 trials, listed in Section 1. | Search may add candidates or fail to reproduce some held trials. | Interpret by Section 5A, not by convenience. |
| Search strings | The exact PubMed and ClinicalTrials.gov strings in Section 5. | Executed strings, run times, filters and yields are recorded in the search lane. | Any departure is named as a departure. |
| Linkage rules | The two-route linkage method and failure modes in Section 4A. | Candidate publication links found during execution. | A registry `result` link is verified before use. |
| Statistical choices | The synthesis methods in Section 10. | A pool is run only if compatible eligible results exist. | No compatible data means no pool, not a null result. |
| Local paths | No local filesystem path is an analysis input. | Build paths may vary by machine. | Pushed code must not hardcode local roots. |

## 11 - Subgroup and sensitivity analyses

**Sensitivity, specified before execution:** leave-one-out where defined; the
estimator comparison above; exclusion of records whose publication linkage is
unresolved when a linked-only analysis is being interpreted; and, where per-arm
counts are recovered, the same 2-by-2 data pooled as a risk ratio, an odds ratio
and a risk difference - reported as sensitivity to the primary effect scale,
never as the headline if a hazard-ratio pool is available.

**Subgroup: none specified.** With the small number of trials this comparison has
on the object, any subgroup contrast would be underpowered and post-hoc, and none
will be presented as though it were planned.

## 12 - Meta-bias assessment

Funnel plot, Egger's regression and - for any count-based pool - Peters' test are
computed only where the number of pooled studies makes them interpretable enough
to display. Below approximately ten studies these tests have almost no power and
the Cochrane Handbook advises against interpreting them. Where k is below that
threshold the tests may still be computed for completeness, and will be reported
as computed values, explicitly not as evidence about small-study effects.

Where publication bias cannot be assessed, the GRADE domain will read not
assessable rather than not serious - the two are different statements.

## 13 - Certainty of the evidence

GRADE, per Cochrane Handbook v6.5 sections 14.2.1-14.2.2 and MECIR C74/C75. All
five downgrade domains are assessed and each rating is published with the
evidence it rests on; the overall certainty is computed from the domains and
shown against them so a reader can check the arithmetic.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No GRADE assessment is completed for this protocol by this
document. Performing it later executes this section rather than amending it, and
the object will record that distinction.

## 14 - Data sharing and reproducibility

The canonical data object from which every number on the review page is projected
is published with the review, together with the R session information and the
analysis scripts actually executed. The intent is that the review can be rebuilt
from the object alone.

The protocol commit is pushed and anchored before the first query attempt under
this protocol. The search record is anchored afterwards. The public record
therefore contains two third-party inclusion times bracketing the search
operation, with the limitations stated in the opening section.

## 15 - Funding and conflicts of interest

**No funding was received for this review.** No competing interests are declared
by the authors of this protocol at the time of this commit. Any change is to be
recorded as an amendment rather than by editing this section.

## 16 - Amendments

No amendments exist at the time of this retrospective registration.

Amendments will be recorded as further commits to this file; the full commit
history, not only its head, is projected onto the review page, because a log that
displays only its own head is no better than a mutable document.
