# Protocol -- intravenous iron against placebo or usual care in heart failure with iron deficiency

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

**Status: REGISTERED BY COMMIT, RETROSPECTIVE. This document is the registration.**

This protocol is registered as a commit in a public repository rather than in
PROSPERO. The commit hash is the strong half of that record: the content is
immutable under it, so this text cannot be altered later without producing a
different hash, and anyone can check that much without asking us.

**The commit timestamp is the weak half, and this document will not pretend
otherwise.** Both the author and the committer date on a git commit are supplied
by whoever makes the commit and can be set to any value; GitHub stores and
displays what it is given, and an unsigned commit carries nothing further.

What the mechanism supports, and no more: this exact text is bound to this hash;
the repository is public, so the text is readable by anyone at that hash; and
where an entry for the commit exists in a public transparency log, that log's
inclusion time is an upper bound on when this text existed, set by a third party
rather than by us. The transparency-log entry proves something narrow: **the text
existed no later than the log time**. It does not prove when the commit was made,
that no earlier version existed elsewhere, or what was already known.

What it does not support: it does not prove the commit was made when it says it
was, it does not prove that no earlier or parallel version existed elsewhere, it
does not prove the data had not already been seen, and it says nothing about the
independence of the people who wrote it. Those are claims about conduct, and no
timestamp can carry them.

**How to check this without us.** The verification recipe, the public half of the signing key, and a worked example are at [`ssot/registration/VERIFY.md`](../registration/VERIFY.md). It states the limitation plainly as well: the log time is independent of us, the key custody is not. A stranger can verify the text existed by the log time and that we signed it; a stranger cannot verify we did not hold an earlier version.

**It is written before the search runs, but after the evidence object already
holds trials.** The ordering test this review publishes is that this protocol is
committed, pushed, and anchored in a public transparency log before the first
executed query -- the first attempt, including a failed attempt, not the first
success, because reporting only the successful execution would move the
first-query time later and flatter the claim. The search record is anchored
afterwards, so two third-party log inclusion times bracket the operation.

Both execution times are read from the search lane's own clock. The databases
return records and counts, not trustworthy execution times, so no part of the
ordering is timestamped by a third party unless an external anchor is placed on
each end. The sequence is therefore auditable and externally bounded, and it is
not, on its own, proof of what was known.

---

## 1 . Review question, in PICO

| | |
|---|---|
| **Population** | Adults with heart failure and iron deficiency. |
| **Intervention** | Intravenous iron, including ferric carboxymaltose and ferric derisomaltose regimens. |
| **Comparator** | Placebo, matching saline placebo, or usual care/no intravenous iron. |
| **Outcomes** | Six outcome questions: recurrent hospitalisations for heart failure together with cardiovascular death; time to first cardiovascular death or hospitalisation for heart failure; recurrent hospitalisations for heart failure alone; time to death from any cause; a hierarchical composite of death, heart-failure hospitalisation and walk distance; and change in six-minute walk distance. |
| **Study design** | Randomised controlled trials. |

**Frozen question:** In adults with heart failure and iron deficiency, what is
the effect of intravenous iron compared with placebo or usual care on recurrent
hospitalisations for heart failure with and without cardiovascular death, on the
time to a first such event, on death from any cause, on a hierarchical composite
of death, hospitalisation and walk distance, and on exercise capacity itself --
with each of those questions answered separately?

This topic already holds 5 trials: NCT01453608, NCT02642562, NCT02937454,
NCT03036462, and NCT03037931. The question is being authored after that evidence
was assembled. However carefully it is written now, this is a retrospectively
registered protocol. The anchor proves when this text was written and cannot
prove the trials had not already been seen. A timestamp bounds when, never what
was known.

## 2 . Estimand, stated in advance

The review has six estimands and four effect measures. Each estimand is answered
on its own scale, in its own direction, and without conversion into another
estimand:

- Recurrent hospitalisations for heart failure together with cardiovascular
  death, as a recurrent-event rate ratio.
- Time to first cardiovascular death or hospitalisation for heart failure, as a
  hazard ratio.
- Recurrent hospitalisations for heart failure alone, with no death component, as
  a recurrent-event rate ratio.
- Time to death from any cause, as a hazard ratio.
- A hierarchical composite of death, hospitalisations for heart failure and
  change in walk distance, as an unmatched win ratio.
- Change in six-minute walk distance at the trial primary timepoint, in metres.

The primary estimand for each row is the measure named in that row. Quantities
that cannot be converted into that estimand are excluded on the OUTCOME/MEASURE
axis for that row, not on grounds of quality. Specifically and in advance:

- A recurrent-event rate ratio is not a time-to-first hazard ratio.
- A recurrent hospitalisation endpoint with cardiovascular death is not a
  hospitalisation-only endpoint.
- All-cause death is not cardiovascular death.
- A win ratio over a hierarchical composite is not a hazard ratio, rate ratio,
  risk ratio, odds ratio, or mean difference.
- A mean difference in metres is not a ratio measure and is not a component-level
  substitute for a hierarchical composite that includes walk distance.

## 3 . Eligibility criteria

**Include** a study if all five hold: it is randomised; it enrols adults with
heart failure and iron deficiency; it randomises intravenous iron against placebo,
matching saline placebo, usual care, or no intravenous iron; it reports at least
one of the six stated outcomes; and the reported effect measure is the effect
measure specified for that outcome.

**Exclude** on any single failed axis -- DESIGN, POPULATION, INTERVENTION,
COMPARATOR, or OUTCOME/MEASURE -- and record which axis failed and what the study
reports instead. These are the only exclusion axes. A study may be eligible for
the review but not contribute to a specific synthesis because its reported
outcome, death component, counting rule, time basis, or effect measure belongs to
another row.

Any axis read from a registry title is provisional until the registered primary
outcome measure is read from the outcome module. A title is not an outcome
definition. If a title suggests heart failure, iron deficiency, recurrent
hospitalisation, death, or exercise capacity, that suggestion must be checked
against the registered condition, intervention, arm, and outcome fields before it
is used for inclusion, exclusion, or pooling.

Populations narrower than the question are not indirect on that ground alone;
narrowness is recorded and carried into GRADE indirectness rather than used as an
exclusion.

## 4 . Information sources

PubMed through NCBI E-utilities and ClinicalTrials.gov API v2 are the only
databases searched. Embase was not searched. CENTRAL was not searched. Web of
Science was not searched. Scopus was not searched. This is not a comprehensive
search.

The cost of that omission is explicit: trials or publications indexed only in
those omitted databases can be missed; conference records, regional journal
records, and records with weak PubMed indexing can be under-ascertained; and the
review cannot claim database-complete recall. The review can only claim what its
two named public sources and its recorded linkage procedure support.

Only public, resolvable sources are used for extraction. No private document,
non-public correspondence, or remembered result is evidence.

## 4A . Linkage method and its known failure modes

Before the search runs, registry records will be linked to publications by a
fixed cascade:

1. Search PubMed for the exact NCT identifier from the ClinicalTrials.gov record.
2. Read the ClinicalTrials.gov references module and identify references marked
   as result publications.
3. Match candidate publications back to the registry record by NCT identifier,
   trial acronym, intervention, comparator, population, trial dates, and outcome
   definitions.
4. Treat a candidate as linked only when the registry record and publication
   agree on the trial identity, not merely because one surface points to the
   other.

Two failure modes have already been measured on this corpus and are named before
the search is executed. First, PubMed silently drops trials from ID-based queries
when the record is not indexed, so an absent result is indistinguishable from a
trial that does not exist. Second, ClinicalTrials.gov
`reference_type='result'` links can point at the wrong paper, which is worse than
a missing link because a wrong link looks like a successful one.

Where linkage succeeds, registry data matched the publication in 26 of 28
analyses compared on this corpus. That is a conditional figure whose denominator
is linked analyses, not all analyses, and it is not a general reliability rate.
It cannot be used to trust an unlinked row, an absent PubMed result, or a
registry result link that has not been checked against trial identity.

## 5 . Search strategy -- the exact strings to be executed

These strings are stated before execution. The search lane will record what it
actually ran, on what date, with what filters, and how many records each returned;
any departure from the strings below will be recorded as a departure rather than
silently substituted. Each Boolean string is deliberately kept under 20 Boolean
operators so that the interface can execute it as registered.

**PubMed through NCBI E-utilities**

```
("ferric carboxymaltose"[tiab] OR "ferric derisomaltose"[tiab] OR "iron isomaltoside"[tiab] OR "intravenous iron"[tiab] OR FCM[tiab] OR FDI[tiab])
AND ("heart failure"[MeSH Terms] OR "heart failure"[tiab])
AND (randomized controlled trial[pt] OR randomized[tiab] OR randomised[tiab] OR placebo[tiab] OR trial[tiab])
```

Filters: none on language, none on date, none on publication status beyond what
PubMed itself indexes.

**ClinicalTrials.gov API v2**

```
query.intr="ferric carboxymaltose" OR "ferric derisomaltose" OR "iron isomaltoside" OR "intravenous iron" OR FCM OR FDI
query.cond="heart failure"
```

Filters: none on recruitment status, phase, enrolment, location, date, sex, or
posted-results availability. The reason is that a completed trial, an active
trial, and an eligible trial without posted results answer different review
process questions and must not be erased by the query itself.

## 5A . How this search can fail, decided in advance

The search result will be read in three mutually exclusive ways.

**A. It reproduces the held set.** That is evidence that the two-source search can
find the five trials already on the object. They are searched-for trials, not a
convenience set, and this outcome does not prove that no eligible trial exists
outside PubMed or ClinicalTrials.gov.

**B. It returns additional eligible trials.** That is a finding about the review.
Each additional trial is named and either included or excluded on one of the axes
declared in section 3. If it is eligible but has no extractable result for a
specified outcome, it is recorded as eligible but not contributing rather than
silently dropped.

**C. It returns fewer trials than the object holds.** That is a finding about the
search, not proof that the review is wrong. A failed search can be too narrow
while the review object remains correct. Worked example fixed in advance: the
finerenone cardiovascular registry query missed FIGARO-DKD (NCT02545049), a
pivotal trial, because it registers its condition as "Diabetic Kidney Disease"
alone while its sibling FIDELIO-DKD registers "Chronic Kidney Disease". A narrow
query looks exactly like a wrong review until the registry wording is read.

The earliest query time used for ordering includes a failed attempt. A failed
attempt that proves the string was tried is part of the chronology and must not
be removed to make the registration look cleaner.

## 6 . Study selection process

Two independent screeners of different model families screen every record. The
cross-family rule is a requirement, not a preference, because two instances of
one model is one screener run twice and its agreement statistic is meaningless.

Screening is in two stages: title and abstract or registry summary, then full
record or full text where available. Each screener's decision is recorded per
record at the stage it was applied, together with the reason. Both screeners'
decisions are published, not only the reconciled outcome, along with the
agreement rate and how every disagreement was resolved.

Adjudication of disagreements is by a named human.

Two release tiers, and the difference between them is attestation, not content.
The website release requires the two cross-family AI assessments and states
plainly that it has not been human-verified. The submission release additionally
requires two named human reviewers to have checked every included study and every
extracted datum; the statement to that effect is emitted only when those
attestation records exist and is never written as prose.

## 7 . Data extraction

Extracted per trial and per outcome: registry identifier, publication identifier,
year, design, population, arms, analysed denominator and randomised total
separately, per-arm event counts where the outcome is count-bearing, the
published effect estimate, its interval or other dispersion statement, the stated
confidence level where an interval exists, and the source layer from which the
cell was read.

Every extracted cell is classified only against the DESIGN, POPULATION,
INTERVENTION, COMPARATOR, and OUTCOME/MEASURE axes declared in section 3. No
other exclusion axis is introduced during extraction. A record is not excluded
because it is inconvenient, because it is small, because its result is absent, or
because its registry-publication linkage is difficult; those facts are recorded
in their own fields.

Any outcome classification that came first from a registry title remains
provisional until the registered primary outcome measure has been read from the
outcome module. A title is not an outcome definition. This is especially
load-bearing here because recurrent hospitalisations with cardiovascular death,
recurrent hospitalisations without death, time to first cardiovascular death or
heart-failure hospitalisation, all-cause death, a hierarchical win-ratio
composite, and walk distance can all be abbreviated in titles in ways that erase
their differences.

Every extracted cell carries a resolvable pointer to the specific document and,
where possible, to the table, outcome module, figure, or registry analysis within
it. Nothing is computed that can be read. No count is derived from a percentage;
no composite is reconstructed by summing its components; no hazard ratio is
derived from event counts; and no recurrent-event ratio is stored in a
time-to-first field. Identifiers are resolved by lookup, never from recall.

Where two populations exist for one outcome, both are recorded, exactly one is
marked as selected, and the population is named on the cell.

## 8 . Outcomes and prioritisation

The review reports six questions separately and gives none permission to stand
for another.

**Primary outcome family for clinical events:** recurrent hospitalisations for
heart failure together with cardiovascular death, as a recurrent-event rate
ratio.

**Other pooled clinical-event outcomes, still separate:** time to first
cardiovascular death or hospitalisation for heart failure, as a hazard ratio;
recurrent hospitalisations for heart failure alone, as a recurrent-event rate
ratio; and time to death from any cause, as a hazard ratio.

**Single-trial endpoints with no ordinary shared interval basis:** the
hierarchical composite of death, hospitalisation and walk distance is reported as
the trial's own unmatched win ratio and interval level; the six-minute walk
distance endpoint is reported in metres from the single trial and any interval
not printed by the source is labelled as computed rather than as an ordinary
published interval. Neither endpoint is pooled with another endpoint.

Outcome priority does not override estimand integrity. A secondary outcome with
the right estimand is eligible for that estimand; a primary outcome with the
wrong estimand is not.

## 9 . Risk of bias

**Tool.** Cochrane risk-of-bias tool for randomized trials, version 2 (RoB-2).

**Unit of assessment.** RoB-2 is applied to the result being pooled or reported,
not to the trial as a whole. One trial may therefore carry a different judgement
for a recurrent-event rate ratio, a time-to-first hazard ratio, an all-cause
mortality hazard ratio, a win ratio, or a walk-distance mean difference.

**Variant.** The effect of assignment to intervention variant, because these
randomised comparisons estimate assignment effects. The adherence variant is not
used, and no result assessed under one variant will be reported as though
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

Both sets of judgements are recorded and published -- per domain, per assessor,
with rationales -- not only the reconciled outcome. The per-domain agreement rate
is published as measured. Disagreements are adjudicated by a named human, and the
adjudication and its reason are recorded per disagreement.

**Evidence admissible to an assessment.** The trial's registry record including
its protocol and statistical analysis plan where posted, the primary publication
and its supplement, and the posted results module. A judgement made from an
abstract alone is not the same act as one made from a protocol, so the sources
actually consulted are recorded per domain, and a domain judged without access to
the protocol is marked as such rather than presented as equivalent.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** Performing RoB-2 later executes this section rather than
amending it, and the object will record that distinction.

## 10 . Synthesis methods

No synthesis crosses an outcome, effect measure, death component, time basis, or
analysis-family boundary. The six questions are first separated by case
definition and measure, and only then considered for pooling.

The three analysis families are:

- Recurrent-event rate ratios for recurrent hospitalisation outcomes.
- Time-to-event hazard ratios for first-event and death outcomes.
- Mean differences for exercise-capacity outcomes measured in metres.

The hierarchical win ratio is a fourth effect measure and is reported on its own
trial-defined scale. It is not pooled with any of the three analysis families.

For each outcome with at least two eligible, non-duplicated comparisons on the
same effect scale, random-effects meta-analysis is run on the log scale for ratio
measures and on the raw metre scale for walk-distance mean differences. The
participant, event, or pair unit is the unit named by that outcome's estimand.

Pre-stated, so that reporting a disagreement between methods is a commitment
rather than a post-hoc observation:

- REML is the headline between-study-variance estimator.
- The Hartung-Knapp-Sidik-Jonkman interval is reported alongside the Wald
  interval, and where the two disagree about whether the interval crosses the
  null, that disagreement is reported in the results rather than resolved by
  choosing one.
- Leave-one-out analysis is run and reported for every pool where it is defined.
- An estimator comparison -- DerSimonian-Laird, REML, Paule-Mandel -- is run and
  reported where the data structure permits it.
- A prediction interval is reported where it is defined and not reported where
  the number of studies makes it undefined.
- The analysis is cross-checked in a second engine at build time and the
  comparison published, including any quantity on which the two engines disagree
  by definition rather than by error.

Heterogeneity: tau-squared, I-squared with its uncertainty statement where
defined, and Q with its degrees of freedom and p value. I-squared is reported
with the caveat that at small study numbers a low value reflects imprecision as
much as agreement.

## 10A . Network geometry and what it forbids

This is a network, but its geometry is sparse and forbids the usual ranking
claims. The topology is derived from the object's own arms and is an established
fact, not an assumption.

Nodes:

- ferric carboxymaltose
- ferric carboxymaltose, an initial intravenous dose followed by maintenance dosing
- ferric carboxymaltose, dosed by the extent of iron deficiency
- ferric carboxymaltose, given every six months as needed on the basis of iron indexes and haemoglobin
- ferric derisomaltose, dosed by bodyweight and haemoglobin concentration
- matching placebo added to standard heart failure therapy
- matching saline placebo, administered in black syringes by personnel taking no study assessments
- saline placebo
- usual care, with no placebo infusion of any kind

The object records 9 nodes, 5 edges, `connected: False`, and independent loops
`E - V + 1 = -3`. This means there are zero loops. Across disconnected
components, indirect comparisons are not computable at all. Within any connected
component, indirect comparisons are computable because the network is connected
at that component level, but the consistency assumption they rest on cannot be
tested by the geometry. Node-splitting and design-by-treatment interaction are
unavailable, and their absence must never be reported as consistency having been
checked.

No SUCRA or ranking will be reported. Publication bias is not assessable rather
than not serious, and GRADE carries incoherence as untestable. A head-to-head
trial between two non-comparator active nodes would add an edge; if that edge
closed a loop inside a connected component, it would make a consistency check
possible for that loop, and if it merely connected two previously disconnected
components, it would permit new indirect comparisons but still would not by
itself create a testable loop.

## 11 . Subgroup and sensitivity analyses

Sensitivity analyses, stated in advance: leave-one-out where defined; estimator
comparison as described above; exclusion of comparisons that do not share the
same comparator class where enough comparisons remain; and separate display of
single-trial endpoints that cannot enter a pool.

No subgroup contrast is claimed as confirmatory. Any subgroup or molecule-level
contrast not structurally required by the estimand is exploratory and labelled as
such.

## 12 . Meta-bias assessment

For ordinary pairwise pools, funnel plots and regression tests for small-study
effects are considered only where the number of studies makes them interpretable.
Below approximately ten studies these tests have almost no power and the Cochrane
Handbook advises against interpreting them.

In this network, publication bias is not assessable rather than not serious. That
wording is mandatory because an unassessable domain and a reassuring domain are
different claims. No funnel-plot symmetry, Egger test, Peters test, SUCRA value,
ranking, node-splitting output, or design-by-treatment interaction result will be
used to imply that publication bias or incoherence has been checked when the
geometry does not permit the check.

## 13 . Certainty of the evidence

GRADE, per Cochrane Handbook methods, will be applied per outcome and per effect
measure. All five downgrade domains are assessed and each rating is published
with the evidence it rests on; the overall certainty is computed from the domains
and shown against them so a reader can check the arithmetic.

Risk of bias is fed by the completed RoB-2 assessment, not by general trial
features. Inconsistency is assessed within each pool where the data permit it.
Indirectness records population, intervention, comparator, outcome, and measure
differences without using narrowness alone as an exclusion. Imprecision is judged
on the interval appropriate to that outcome's measure. Publication bias is marked
not assessable where the search and geometry do not support assessment.

For the network domain, incoherence is untestable because there are zero loops.
GRADE carries that as untestable, not as checked and not as absent.

**Status at the time of this commit: PENDING.** No completed GRADE assessment is
claimed by this protocol.

## 14 . Data sharing and reproducibility

The canonical data object from which every number on the review page is projected
is published with the review, together with the search record, linkage decisions,
screening log, extraction pointers, analysis scripts actually executed, and
session information for the analysis engines. The intent is that the review can
be rebuilt from the object and public sources alone.

The protocol commit is anchored before the search. The search record is anchored
after the search. The two anchors bracket the operation and do not prove what was
known before the first anchor.

## 15 . Funding and conflicts of interest

**No funding was received for this review.** No competing interests are declared
by the authors of this protocol at the time of this commit. Any change is to be
recorded as an amendment rather than by editing this section.

## 16 . Amendments

Amendments will be recorded as further commits to this file; the full commit
history, not only its head, is projected onto the review page, because a log that
displays only its own head is no better than a mutable document.
