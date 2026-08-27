# Protocol - catheter ablation in adults with atrial fibrillation and heart failure

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
| **Population** | Adults with atrial fibrillation and heart failure. |
| **Intervention** | Catheter ablation of atrial fibrillation, including ablation-based rhythm-control strategies. |
| **Comparator** | Medical rate- or rhythm-control therapy, conventional care, usual care, or rate control. |
| **Outcome** | Composite of all-cause mortality and heart-failure events, using each trial's registered primary composite definition. |
| **Study design** | Randomised controlled trials. |

**Frozen question:** in adults with atrial fibrillation and heart failure, what
is the effect of catheter ablation of atrial fibrillation compared with medical
rate- or rhythm-control therapy on the composite of all-cause mortality and
heart-failure events?

This topic already holds 2 trials: NCT00643188 and NCT01420393. The question is
being authored after that evidence was assembled. However carefully it is written
now, this is a **retrospectively registered protocol**, not an advance
registration. The anchor proves WHEN this text was written, in the narrow sense
that the text existed no later than the log time, and CANNOT prove the trials had
not already been seen. A timestamp bounds when, never what was known.

## 2 - Estimand, stated in advance

The estimand is the **time-to-first-event hazard ratio for the composite**, on
the log scale, with the participant as the unit of analysis and the time to the
first component event as the event time.

The composite is death from any cause plus a heart-failure event or
heart-failure hospitalisation, as defined by the trial's registered primary
outcome. Variation in the heart-failure limb is not silently normalised; it is
recorded as clinical and outcome-definition heterogeneity.

**Quantities that cannot be converted into that estimand are excluded from the
primary synthesis on the MEASURE axis, not on grounds of quality.** This is a
criterion and not a judgement made after seeing results. A trial may be large,
well conducted, and directly on topic and still fail the primary synthesis
because it reports something else. Specifically and in advance:

- A **recurrent-event rate ratio** counts repeat events per person over time; a
  time-to-first hazard ratio counts each person once, at their first event. The
  two share a scale and a direction and answer different questions. A rate ratio
  will not be stored in a hazard-ratio field.
- A **win ratio** over a hierarchical composite is not this estimand.
- A **dichotomous risk ratio** at a fixed timepoint is not this estimand, though
  where per-arm counts are recovered a risk ratio, odds ratio, and risk
  difference will be computed and reported as sensitivity analyses only, never as
  the headline.

## 3 - Eligibility criteria

**Include** a study if all four hold: it is randomised; it enrols adults with
atrial fibrillation and heart failure or left-ventricular dysfunction; it
randomises catheter-based ablation of atrial fibrillation, pulmonary-vein
isolation, radiofrequency ablation, cryoballoon ablation, or an ablation-based
rhythm-control strategy against medical rate- or rhythm-control therapy,
conventional care, usual care, or rate control; and it reports, at any outcome
rank, a composite of all-cause mortality with heart-failure events or
heart-failure hospitalisation in a form usable for the review's estimand.

**Exclude** on any single failed axis - population, intervention, comparator, or
measure - and record which axis failed and what the study reports instead.
Section 7 will classify records against these axes and no others.

The intervention axis excludes atrioventricular-node or atrioventricular-junction
ablation used as rate control with pacing when it is not catheter ablation of
atrial fibrillation intended to restore or maintain sinus rhythm. Surgical maze
ablation is excluded on the intervention axis. Ablation-technique comparisons
without an eligible medical comparator are excluded on the comparator axis.

Populations narrower than the question, for example patients with implanted
defibrillators or high-burden atrial fibrillation, are **not** indirect on that
ground alone; narrowness is recorded and carried into the GRADE indirectness
domain rather than used as an exclusion.

Any axis read from a registry title is provisional until the registered primary
outcome measure is read from the outcomes module. A title is not an outcome
definition.

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

- Query ClinicalTrials.gov API v2 for eligible registry records.
- Read each candidate record's NCT identifier, conditions, arms, interventions,
  design, recruitment status, primary outcome module, and reference module.
- Query PubMed through NCBI E-utilities using the NCT identifier and the planned
  topic string.
- Accept a publication link only when the NCT identifier, trial acronym or title,
  arms, population, and registered primary outcome align between the registry
  record and the publication.
- Treat registry result references as candidates, not proof, until the target
  publication is checked against the registry fields.

Two linkage failure modes have already been measured on this corpus and are
named before this search runs.

First, PubMed silently DROPS trials from ID-based queries when the record is not
indexed, so an absent result is indistinguishable from a trial that does not
exist. Absence from an ID-based PubMed query is therefore not evidence of absence.

Second, registry `reference_type='result'` links can point at the wrong paper,
which is worse than a missing link because a wrong link looks like a successful
one. A registry result reference is therefore checked, not trusted.

Where linkage succeeds, registry data matched the publication in 26 of 28
analyses compared on this corpus. That is a conditional figure whose denominator
is **linked analyses**, not all analyses, and it is not a general reliability
rate.

## 5 - Search strategy - the exact strings to be executed

These strings are stated **before** execution. The search lane will record what
it actually ran, on what date, with what filters, and how many records each
returned; any departure from the strings below will be recorded as a departure
rather than silently substituted. Each string is kept below 20 Boolean operators
so the interface can execute it without forcing a departure on the first attempt.

**PubMed (NCBI E-utilities)**

```
("atrial fibrillation"[tiab] OR AF[tiab])
AND ("heart failure"[tiab] OR "left ventricular dysfunction"[tiab])
AND ("catheter ablation"[tiab] OR ablation[tiab])
AND (randomized[tiab] OR randomised[tiab] OR trial[tiab])
```

Filters: none on language, none on date, none on publication type beyond the
text string above. Rationale: a language or date filter would make the search
less reproducible across interfaces and would exclude records before their
eligibility axes are read.

**ClinicalTrials.gov (API v2)**

```
query.cond=atrial fibrillation heart failure
query.intr=catheter ablation OR pulmonary vein isolation OR ablation
filter.advanced=AREA[StudyType]INTERVENTIONAL AND AREA[DesignAllocation]RANDOMIZED
```

Filters: none on start date, completion date, country, phase, sponsor, sex, or
results posting. Recruitment status is not restricted, because an eligible
completed trial can be miscoded or differently represented across registry
versions, and because status is not an eligibility axis.

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

If the search returns fewer trials than the object holds, that is a finding about
the search, never reported as the review being wrong. A failed search string can
miss a real trial for reasons unrelated to the review question.

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
year, design, population, arms, the analysed denominator and the randomised total
separately, per-arm event counts, and the published effect estimate with its
interval and its stated confidence level.

Eligibility and exclusion will be classified against the axes declared in section
3 and no others: population, intervention, comparator, and measure. A registry
title may guide screening, but any axis read from a registry title is provisional
until the registered primary outcome measure is read from the outcome module. A
title is not an outcome definition.

Every extracted cell carries a resolvable pointer to the specific document and,
where possible, to the table or registry module within it, so that a human check
can be made without leaving the page. **Nothing is computed that can be read.**
No count is derived from a percentage; no composite is reconstructed by summing
its components. Identifiers are resolved by lookup, never from recall.

Where two populations exist for one outcome, for example a full analysis set and
a randomised set, both are recorded, exactly one is marked as selected, and the
population is named on the cell.

## 8 - Outcomes and prioritisation

**Primary:** the composite of all-cause mortality and heart-failure events, as a
time-to-first-event hazard ratio.

**Components, read and reported but not pooled:** all-cause death;
cardiovascular death where reported; first heart-failure hospitalisation; other
trial-defined heart-failure events. They are shown because a reader should see
them; they are not pooled because the review's estimand is the composite.

## 9 - Risk of bias

**Tool.** Cochrane risk-of-bias tool for randomized trials, version 2 (RoB-2).

**Unit of assessment.** RoB-2 is applied **to the result being pooled, not to the
trial as a whole**: the composite of all-cause mortality and heart-failure
events, expressed as a time-to-first-event hazard ratio. One trial may therefore
carry a different judgement for this result than it would for its own primary
endpoint, and that is the intended behaviour of the tool.

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

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No RoB-2 assessment is completed by this protocol. Performing
it later **executes this section rather than amending it**, and the object will
record that distinction.

## 10 - Synthesis methods

Random-effects meta-analysis on the log hazard-ratio scale, inverse-variance
weighted, will be used only where the connected evidence structure supports the
target comparison and the result is not withdrawn for incoherent geometry.

Methods fixed in this protocol:

- **REML** is the headline between-study-variance estimator.
- The **Hartung-Knapp-Sidik-Jonkman interval is reported alongside** the Wald
  interval, and where the two disagree about whether the interval crosses the
  null, that disagreement is reported in the results rather than resolved by
  choosing one.
- **Leave-one-out** analysis is run and reported for every pairwise pool where it
  is defined.
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

## 10A - Network geometry and what it forbids

The network geometry is derived from the object's own arms and is an established
fact, not an assumption.

- Nodes: Ablation-based rhythm control; Catheter ablation; Medical therapy (rate
  or rhythm control); Rate control.
- Edges: 2.
- Connected: False.
- Independent loops by E - V + 1: -1.

This is a disconnected network with zero loops. Because the network is not
connected, indirect comparisons across the disconnected components are not
computable from the current geometry.

The requested connected-network rule is recorded here so it is not silently
misapplied: indirect comparisons are computable because the network is
connected, but the consistency assumption they rest on **CANNOT BE TESTED** in a
zero-loop network. That sentence is the rule for a connected zero-loop network;
it is not the fact of this object while `connected` is false.

For this object, the stronger limitation applies: there is no connected path
between the two current contrasts, and therefore no valid indirect comparison
between their separated components. If a future head-to-head trial links two
non-comparator nodes across the two components, for example Catheter ablation
against Ablation-based rhythm control, the graph would become connected with
three edges and four nodes. That would make indirect comparisons across all four
nodes computable, but it would still create no independent loop, so the
consistency assumption would remain untestable. A later additional edge that
closes a loop would be needed before loop-based inconsistency checks become
available.

Node-splitting and design-by-treatment interaction are unavailable in this
zero-loop geometry, and their absence must never be reported as consistency
having been checked. No SUCRA or ranking will be reported. Publication bias is
**NOT ASSESSABLE** rather than not serious, and GRADE carries incoherence as
untestable.

## 11 - Subgroup and sensitivity analyses

**Sensitivity, fixed in this protocol:** leave-one-out where defined; the
estimator comparison above; and, where per-arm counts are recovered, the same
2x2 data pooled as a risk ratio, an odds ratio, and a risk difference - reported
as sensitivity to the primary hazard-ratio pool, never as the headline.

**Subgroup: none.** With the small and disconnected evidence structure this
comparison has, any subgroup contrast would be underpowered and post-hoc, and
none will be presented as though it were planned.

## 12 - Meta-bias assessment

Funnel plot, Egger's regression, and - for any count-based pool - Peters' test
will be considered only where the number of studies makes the method
interpretable. Below approximately ten studies these tests have almost no power
and the Cochrane Handbook advises against interpreting them. Where k is below
that threshold the tests may still be computed for completeness, and will be
reported as computed values, explicitly not as evidence about small-study
effects.

In the current zero-loop network geometry, publication bias is **NOT ASSESSABLE**
rather than **not serious**. The GRADE domain will carry that distinction because
the two statements mean different things.

## 13 - Certainty of the evidence

GRADE will be applied per Cochrane Handbook guidance. All five downgrade domains
are assessed and **each rating is published with the evidence it rests on**; the
overall certainty is computed from the domains and shown against them so a
reader can check the arithmetic.

The GRADE risk-of-bias domain is fed by the completed RoB-2 result for the pooled
result. The inconsistency or incoherence domain will explicitly carry the network
geometry: zero loops make incoherence untestable. Publication bias is recorded as
not assessable when the evidence base is too small or the geometry prevents
meaningful assessment.

**Status at the time of this commit: PENDING.** No GRADE certainty rating is
completed by this protocol. Performing it later executes this section rather than
amending it.

## 14 - Data sharing and reproducibility

The canonical data object from which every number on the review page is
projected is published with the review, together with the session information and
the analysis scripts actually executed. The intent is that the review can be
rebuilt from the object alone.

The protocol commit is pushed publicly and anchored before the first search
attempt. The search record is anchored after execution. The review page will
display the protocol hash, the protocol anchor, the first query attempt time
including failed attempts, the search-record hash, and the search-record anchor.

## 15 - Funding and conflicts of interest

**No funding was received for this review.** No competing interests are declared
by the authors of this protocol at the time of this commit. Any change is to be
recorded as an amendment rather than by editing this section.

## 16 - Amendments

None at this registration commit.

Amendments will be recorded as further commits to this file; the full commit
history, not only its head, is projected onto the review page, because a log that
displays only its own head is no better than a mutable document.
