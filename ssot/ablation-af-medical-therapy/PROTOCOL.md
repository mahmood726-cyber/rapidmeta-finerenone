# Protocol - catheter ablation of atrial fibrillation against medical rate- or rhythm-control therapy

**Status: RETROSPECTIVELY REGISTERED BY COMMIT. This document is the registration.**

This protocol is registered as a commit in a public repository rather than in
PROSPERO. The commit hash binds this exact text; the repository is public. This
document is written before the search runs and contains no results, no yields,
and no counts from any search.

This is a retrospectively registered protocol. The topic already holds three
trials before this text is authored, and the question is being written after
that evidence was assembled. However carefully it is written now, the anchor
proves when this text existed and cannot prove that the trials had not already
been seen. A timestamp bounds when, never what was known.

**The commit timestamp is the weak half, and this document will not pretend
otherwise.** The commit timestamp is author-supplied and forgeable: git author
and committer dates are set by whoever makes the commit, and commits here are
unsigned.

What the mechanism supports, and no more: this exact text is bound to this hash,
and the repository is public, so the text is readable by anyone at that hash. A
public transparency-log entry gives an inclusion time set by a third party,
proving something narrow: THE TEXT EXISTED NO LATER THAN THE LOG TIME. Not when
the commit was made, not that no earlier version existed elsewhere, and not what
was already known.

What it does not support: it does not prove when the commit was made, it does not
prove that no earlier or parallel version existed elsewhere, it does not prove
the data had not already been seen, and it says nothing about the independence
of the people who wrote it. Those are claims about conduct, and no timestamp can
carry them.

**How to check this without us.** The verification recipe, the public half of the signing key, and a worked example are at [`ssot/registration/VERIFY.md`](../registration/VERIFY.md). It states the limitation plainly as well: the log time is independent of us, the key custody is not. A stranger can verify the text existed by the log time and that we signed it; a stranger cannot verify we did not hold an earlier version.

**It is written before the search runs.** This protocol is committed, pushed, and
log-anchored before the first query. The ordering test this review publishes
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

## 1. Review question, in PICO

| | |
|---|---|
| **Population** | Adults with atrial fibrillation. |
| **Intervention** | Catheter ablation of atrial fibrillation, including ablation-based rhythm-control strategies where the ablation effect is attributable. |
| **Comparator** | Medical rate-control therapy, medical rhythm-control therapy, conventional care, or rate-or-rhythm-control therapy without catheter ablation as the assigned invasive strategy. |
| **Outcome** | Death, stroke, and hospitalisation outcomes as defined by the trial's registered primary outcome and extractable secondary outcomes. |
| **Study design** | Randomised controlled trials. |

**Frozen question:** in adults with atrial fibrillation, what is the effect of
catheter ablation compared with medical rate- or rhythm-control therapy on
death, stroke and hospitalisation?

This is a retrospectively registered protocol. THIS TOPIC ALREADY HOLDS 3
TRIALS: NCT00643188, NCT00911508, and NCT01420393. Those registrations are
therefore starting objects, not search results generated after this protocol.
The anchor proves when this protocol text existed and cannot prove the trials
had not already been seen.

## 2. Estimand, stated in advance

The primary estimand is the **time-to-first-event hazard ratio for each trial's
own registered primary composite**, on the log scale, with the participant as the
unit of analysis and the time to the first component event as the event time.

The object already records that the three trials register different primary
composites. This protocol does not make those composites identical by wording.
The review will report what each registered outcome is, and any synthesis will
state whether it is pooling like with like or declining to pool because the
outcome definitions are not coherent enough for a single estimand.

**Quantities that cannot be converted into that estimand are excluded on the
OUTCOME MEASURE axis, not on grounds of quality.** This is fixed because it is a
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
  difference will be computed and reported as sensitivity analyses only, never
  as the headline.

## 3. Eligibility criteria

**Include** a study if all five hold: it is randomised; it enrols adults with
atrial fibrillation; it includes catheter ablation or an ablation-based rhythm
control arm whose effect is attributable to ablation; it compares against
medical rate-control therapy, medical rhythm-control therapy, conventional care,
or rate-or-rhythm-control therapy without catheter ablation as the assigned
invasive strategy; and it reports death, stroke, hospitalisation, or a composite
containing those outcomes as a time-to-first-event hazard ratio, or enough
source-backed information to place the result in the correct non-headline
sensitivity field.

**Exclude** on any single failed axis - STUDY DESIGN, POPULATION, INTERVENTION,
COMPARATOR, or OUTCOME MEASURE - and record which axis failed and what the study
reports instead. These are the only exclusion axes.

The canonical object already names NCT00643188, NCT00911508, and NCT01420393 as
the three held trials. Candidate or held status is not proof of eligibility:
each held trial and any searched record must still be classified against the
same five axes before it can enter the review.

Populations narrower than the question, including heart-failure-only atrial
fibrillation populations, are **not** indirect on that ground alone. Narrowness
is recorded and carried into the GRADE indirectness domain rather than used as
an exclusion unless the population is not an adult atrial-fibrillation
population.

## 4. Information sources

PubMed (NCBI E-utilities) and ClinicalTrials.gov API v2 only.

Embase was NOT searched. CENTRAL, Web of Science and Scopus were NOT searched.
This is not a comprehensive search, and it must not be described as
comprehensive. The cost of the omission is that records indexed only in the
omitted services, conference material present only there, trial reports
discoverable through those databases, and citations missed by the stated PubMed
and ClinicalTrials.gov strings may be absent from the review.

Only open-access records and documents are admissible as evidence for
extraction. Memory is not evidence, and no paywalled text will be treated as
source material unless an openly accessible copy is available and cited.

## 4A. Linkage method and its known failure modes

Registry records are linked to publications before extraction by source-backed
identifier matching, not by recall. The search lane first resolves the
ClinicalTrials.gov record. It then queries PubMed for the registry identifier,
trial acronym where available, and intervention/population terms. A publication
is accepted as linked only when the registry identifier is present in PubMed or
the publication text, or when a registry reference and the publication agree on
the trial identity, population, intervention, comparator, and registered outcome
well enough that the linkage is auditable. Any weaker match is recorded as
unresolved rather than silently accepted.

Two linkage failure modes are already measured on this corpus and are named
before the search.

First, PubMed silently DROPS trials from ID-based queries when the record is not
indexed, so an absent result is indistinguishable from a trial that does not
exist. An absent PubMed identifier hit therefore cannot be used to prove that a
registry trial is absent from the literature.

Second, registry `reference_type='result'` links can point at the WRONG paper,
which is worse than a missing link because a wrong link looks like a successful
one. A registry result reference is therefore treated as a candidate link that
must still pass identity checks against the record.

Where linkage succeeds, registry data matched the publication in 26 of 28
analyses compared on this corpus. That is a conditional figure whose denominator
is LINKED analyses, not all analyses. It is not a general reliability rate for
ClinicalTrials.gov, PubMed, or this review.

## 5. Search strategy - the exact strings to be executed

These strings are stated **before** execution. The search lane will record what
it actually ran, on what date, with what filters, and how many records each
returned; any departure from the strings below will be recorded as a departure
rather than silently substituted. Each string is kept under 20 Boolean operators
because the interface refuses more, and a registered string that cannot be
executed forces a departure on the first attempt.

The strings cover the ablation and medical-therapy nodes, not only the names of
the held trials, because a network search scoped to known identifiers alone
would be unable to find a new trial that changes the graph.

**PubMed (NCBI E-utilities): clinical query**

```
("atrial fibrillation"[MeSH Terms] OR "atrial fibrillation"[tiab] OR AF[tiab])
AND ("catheter ablation"[tiab] OR "pulmonary vein isolation"[tiab] OR ablation[tiab])
AND ("medical therapy"[tiab] OR "rate control"[tiab] OR "rhythm control"[tiab] OR antiarrhythmic[tiab] OR conventional[tiab])
AND (randomized controlled trial[pt] OR randomised[tiab] OR randomized[tiab] OR trial[tiab])
```

Filters: none on language, none on date. Rationale: a language or date filter
would narrow the record set for reasons not part of the eligibility criteria.

**PubMed (NCBI E-utilities): held-identifier resolution**

```
(NCT00643188[si] OR NCT00911508[si] OR NCT01420393[si] OR CASTLE-AF[tiab] OR CABANA[tiab] OR RAFT-AF[tiab])
```

Filters: none on language, none on date.

**ClinicalTrials.gov (API v2): clinical query**

```
query.intr=catheter ablation OR pulmonary vein isolation
query.cond=atrial fibrillation
filter.overallStatus=COMPLETED|TERMINATED|ACTIVE_NOT_RECRUITING
```

**ClinicalTrials.gov (API v2): held-identifier resolution**

```
query.id=NCT00643188 OR NCT00911508 OR NCT01420393
```

No backward citation search, forward citation search, registry outside
ClinicalTrials.gov, or bibliographic database outside PubMed is registered for
this review.

## 5A. How this search can fail, decided in advance

Three readings are fixed before execution.

**A. The search reproduces the held set.** That is evidence that the three
starting trials were searched-for rather than convenient. It is not evidence
that the search was comprehensive, because the sources are deliberately limited
to PubMed and ClinicalTrials.gov.

**B. The search returns additional eligible trials.** That is a finding about the
review. Each additional trial will be named and included or excluded on a stated
axis. If eligible, it changes the object rather than being treated as a nuisance
record.

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

Screening is in two stages: title and abstract, then full text or registry
record. **Each screener's decision is recorded per record at the stage it was
applied**, together with the reason. Both screeners' decisions are published,
not only the reconciled outcome, along with the agreement rate and how every
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

Every extracted cell carries a resolvable pointer to the specific document and,
where possible, to the table, figure, registry module, or outcome field within
it, so that a human check can be made without leaving the page. **Nothing is
computed that can be read.** No count is derived from a percentage; no composite
is reconstructed by summing its components. Identifiers are resolved by lookup,
never from recall.

Records are classified against exactly the five axes declared in Section 3:
STUDY DESIGN, POPULATION, INTERVENTION, COMPARATOR, and OUTCOME MEASURE. No
extra exclusion axis is introduced during extraction or screening. Any axis read
from a registry TITLE is provisional until the registered primary outcome
measure is read from the outcome module: a title is not an outcome definition.

Where two populations exist for one outcome - for example a full analysis set
and a randomised set - both are recorded, exactly one is marked as selected, and
the population is named on the cell.

No invented trial data, effect sizes, counts, or PROSPERO numbers are permitted.

## 8. Outcomes and prioritisation

**Primary:** each trial's own registered primary composite, read from the
ClinicalTrials.gov outcome module and, where linked, checked against the primary
publication. It is reported as a time-to-first-event hazard ratio when that is
the source-backed estimand.

**Components, read and reported but not silently substituted for the primary
outcome:** death; cardiovascular death where separately defined; stroke;
hospitalisation; heart-failure hospitalisation; serious bleeding; cardiac
arrest; and any other component explicitly present in the registered primary
composite. They are shown because a reader should see them. They are not pooled
as the headline unless they are the same source-defined outcome on the same
estimand.

## 9. Risk of bias

**Tool.** Cochrane risk-of-bias tool for randomized trials, version 2 (RoB-2).

**Unit of assessment.** RoB-2 is applied **to the result being pooled, not to the
trial as a whole**: the registered primary composite result, expressed as a
time-to-first-event hazard ratio where available. One trial may therefore carry
a different judgement for this result than it would for another endpoint, and
that is the intended behaviour of the tool.

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
implied as done.** No RoB-2 assessment is completed by this protocol. Performing
it later **executes this section rather than amending it**, and the object will
record that distinction.

## 10. Synthesis methods

Random-effects meta-analysis on the log hazard-ratio scale,
inverse-variance weighted, will be used only where the connected evidence
structure supports the target comparison and the outcome definitions support a
single estimand. If the outcome definitions remain incompatible, the review will
decline to pool and will report the reason as a finding rather than selecting a
more convenient outcome after the fact.

Methods fixed in this protocol:

- **REML** is the headline between-study-variance estimator.
- The **Hartung-Knapp-Sidik-Jonkman interval is reported alongside** the Wald
  interval, and where the two disagree about whether the interval crosses the
  null, that disagreement is reported in the results rather than resolved by
  choosing one.
- **Leave-one-out** analysis is run and reported for every pairwise pool where
  it is defined.
- An **estimator comparison** - DerSimonian-Laird, REML, Paule-Mandel - is run
  and reported, on the understanding that with few studies the choice is
  plausibly influential.
- A **prediction interval** is reported using the t distribution on k-1 degrees
  of freedom and is not reported where k makes it undefined.
- The analysis is **cross-checked in a second engine** at build time and the
  comparison published, including any quantity on which the two engines disagree
  by definition rather than by error.

**Heterogeneity:** tau-squared, I-squared with its confidence interval where
defined, and Q with its degrees of freedom and p value. I-squared is reported
with the caveat that at small k a low value reflects imprecision as much as
agreement.

## 10A. Network geometry and what it forbids

The network geometry is derived from the object's own arms and is an established
fact, not an assumption.

| Network element | Established value |
|---|---|
| **Nodes** | Ablation-based rhythm control; Catheter ablation; Left Atrial Ablation; Medical therapy (rate or rhythm control); Rate control; Rate or Rhythm Control Therapy |
| **Edges** | 3 |
| **Connected** | False |
| **Independent loops** | E - V + 1 = 3 - 6 + 1 = -2 |

This is a disconnected network with zero loops. Because the network is not
connected, indirect comparisons across disconnected components are not
computable from the current geometry.

The connected-zero-loop rule is recorded here so it is not silently misapplied:
indirect comparisons are computable because the network is connected, but the
consistency assumption they rest on **CANNOT BE TESTED** - not "was not tested",
cannot be, by the geometry. That sentence is the rule for a connected zero-loop
network; it is not the fact of this object while the established value is
`connected: False`.

For this object, the stronger limitation applies: there is no connected path
across all six nodes, and therefore no valid indirect comparison between nodes
in separated components. If a future head-to-head trial links two non-comparator
nodes across disconnected components, it could make the graph connected and
make indirect comparisons across all nodes computable. If that single added
edge leaves the graph with zero independent loops, the consistency assumption
would still be untestable. A later additional edge that closes a loop would be
needed before loop-based inconsistency checks become available.

Node-splitting and design-by-treatment interaction are unavailable in this
zero-loop geometry, and their absence must never be reported as consistency
having been checked. No SUCRA or ranking will be reported. Publication bias is
**NOT ASSESSABLE** rather than not serious, and GRADE carries incoherence as
untestable.

## 11. Subgroup and sensitivity analyses

**Sensitivity, fixed in this protocol:** leave-one-out where defined; the
estimator comparison above; and, where per-arm counts are recovered, the same
2x2 data pooled as a risk ratio, an odds ratio, and a risk difference - reported
as sensitivity to the primary hazard-ratio pool, never as the headline.

**Subgroup: none.** With the small and disconnected evidence structure this
comparison has, any subgroup contrast would be underpowered and post-hoc, and
none will be presented as though it were planned.

## 12. Meta-bias assessment

Funnel plot, Egger's regression and - for any count-based pool - Peters' test are
not interpretable for the established starting network. Below approximately ten
studies these tests have almost no power and the Cochrane Handbook advises
against interpreting them. With this small, disconnected, zero-loop network,
publication bias and small-study effects are therefore **not assessable**, not
**not serious**. Where publication bias cannot be assessed, the GRADE domain will
read *not assessable* rather than *not serious* - the two are different
statements.

If the search returns enough additional eligible studies for a valid small-study
effects assessment, the tests named above may be computed for completeness and
will be reported as computed values with the same caveat.

## 13. Certainty of the evidence

GRADE, per Cochrane Handbook v6.5 Section 14.2.1-14.2.2 and MECIR C74/C75. All
five downgrade domains are assessed and **each rating is published with the
evidence it rests on**; the overall certainty is computed from the domains and
shown against them so a reader can check the arithmetic.

For any indirect comparison that later becomes computable, GRADE starts from the
lower certainty of the direct comparisons that form the indirect estimate and
then considers additional downgrading for intransitivity, imprecision,
incoherence where testable, and publication bias where assessable. In this
starting network, incoherence is untestable because there is no loop, and that
limitation is carried into GRADE rather than hidden.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No GRADE assessment is completed by this protocol. Performing
it later **executes this section rather than amending it**, and the object will
record that distinction.

## 14. Data sharing and reproducibility

The canonical data object from which every number on the review page is
projected is published with the review, together with the analysis scripts
actually executed and the second-engine check where applicable. The intent is
that the review can be rebuilt from the object alone.

The public release will include the committed protocol, the post-search
search-record anchor, the exact queries executed, the record-level screening
decisions, the extraction pointers, and any departures from this protocol. No
local path, secret, memory-only claim, or non-open-access evidence source is
permitted as a reproducibility dependency.

## 15. Funding and conflicts of interest

**No funding was received for this review.** No competing interests are declared
by the authors of this protocol at the time of this commit. Any change is to be
recorded as an amendment rather than by editing this section.

## 16. Amendments

Amendments will be recorded as further commits to this file; the full commit
history, not only its head, is projected onto the review page, because a log
that displays only its own head is no better than a mutable document.
