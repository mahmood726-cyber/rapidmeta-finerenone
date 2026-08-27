# Protocol - Alirocumab versus placebo: percent change in calculated LDL cholesterol at week 24

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

**Status: RETROSPECTIVELY REGISTERED BY COMMIT, PUBLIC PUSH, AND TRANSPARENCY-LOG ANCHOR. This document is the registration.**

This protocol is registered as a commit in a public repository rather than in
PROSPERO. The commit hash binds the text: the content is immutable under it, so
this text cannot be altered later without producing a different hash, and anyone
can check that much without asking us. The repository is public, so the text is
readable by anyone at that hash. At registration, this document contains no
search results, no search yields, and no counts from any search.

**The commit timestamp is the weak half, and this document will not pretend
otherwise.** Both the author and the committer date on a git commit are supplied
by whoever makes the commit and can be set to any value; commits here are
unsigned, so the commit itself carries no cryptographic proof about when it was
made. A transparency-log entry gives an inclusion time set by a third party,
proving something narrow: the text existed no later than the log time.

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
is that this commit is made, pushed to the public repository, and anchored in a
public transparency log before the first executed query. The first query means
the earliest query time including a failed attempt, not the first success, because
reporting only the successful execution would move the first-query time later and
flatter the claim. The search record is anchored afterwards, so two third-party
times bracket the operation.

Both execution times are read from the search lane's own clock. The databases
return hit counts, not execution times, so no query time is timestamped by a third
party unless an external anchor is placed on each end. The sequence is therefore
auditable and internally consistent, and it is not, on its own, independently
proven. The anchor proves when this text had to exist by; it cannot prove what
the authors had or had not already seen.

---

## 1 - Review question, in PICO

| | |
|---|---|
| **Population** | Adults treated for hypercholesterolaemia. |
| **Intervention** | Alirocumab, including registered every-two-week dose strategies and dose-escalation strategies. |
| **Comparator** | Placebo, including placebo every two weeks where that is the registered comparator arm. |
| **Outcome** | Percent change from baseline in calculated LDL cholesterol at week 24. |
| **Study design** | Randomised controlled trials. |

**Frozen question:** in adults treated for hypercholesterolaemia, how much does
alirocumab change calculated LDL cholesterol from baseline to week 24 compared
with placebo?

This is a retrospectively registered protocol. This topic already holds 8 trials:
NCT01507831, NCT01617655, NCT01623115, NCT01644175, NCT01709500, NCT02107898,
NCT02289963, and NCT02585778. The question is being authored after that evidence
was assembled. However carefully it is written now, this is a retrospectively
registered protocol and must be read as one. The anchor proves when this text was
written and cannot prove the trials had not already been seen. A timestamp bounds
when, never what was known.

## 2 - Estimand, stated in advance

The estimand is the **between-arm mean difference in percent change from baseline
in calculated LDL cholesterol at week 24**, expressed as alirocumab minus placebo
in percentage points, with the participant as the unit of analysis and the trial's
intention-to-treat or closest randomized-analysis population preferred where more
than one analysis set is available.

**Quantities that cannot be converted into that estimand are excluded on the
MEASURE axis, not on grounds of quality.** This is pre-specified because it is a
criterion and not a judgement made after seeing results. A trial may be large,
well conducted and directly on topic and still fail this review's eligibility
because it reports something else. Specifically and in advance:

- A percent change in **measured** LDL cholesterol is not a percent change in
  calculated LDL cholesterol.
- An absolute change in LDL cholesterol, whether reported in mg/dL or mmol/L, is
  not this estimand.
- A proportion reaching an LDL cholesterol target is not this estimand.
- A week-12, week-52, or other non-week-24 LDL cholesterol result is not this
  estimand.
- A safety outcome, apolipoprotein outcome, imaging outcome, or treatment-use
  outcome is not this estimand.

Where a publication or registry reports both a model-adjusted difference and
per-arm model-adjusted means, the reported between-arm difference is extracted
rather than recomputed. Where only per-arm model-adjusted means and their
uncertainty are available, any calculation needed to form a contrast is marked as
a derivation and the source inputs are retained.

## 3 - Eligibility criteria

**Include** a study if all five hold: it is randomised; it enrols adults treated
for hypercholesterolaemia; it randomises alirocumab; it includes a placebo
comparator for alirocumab; and it reports percent change from baseline in
calculated LDL cholesterol at week 24, or enough source data to derive the same
contrast without changing scale, timepoint, or LDL definition.

**Exclude** on any single failed axis: DESIGN, POPULATION, INTERVENTION,
COMPARATOR, or MEASURE. The failed axis and the reported reason are recorded.
Those are the only exclusion axes for this review.

Background lipid-modifying therapy does not make a trial indirect if it is
balanced by design across arms. Populations narrower than the question, including
heterozygous familial hypercholesterolaemia, high cardiovascular risk, diabetes,
or a single country, are not indirect on that ground alone; narrowness is
recorded and carried into the GRADE indirectness domain rather than used as an
additional exclusion axis.

Any axis inferred from a registry title is provisional until the registered
primary outcome measure is read from the outcome module. A title is not an
outcome definition.

## 4 - Information sources

The search uses **PubMed through NCBI E-utilities** and the
**ClinicalTrials.gov API v2** only.

Embase was not searched. CENTRAL was not searched. Web of Science was not
searched. Scopus was not searched. This is not a comprehensive search, and it
will not be described as one. The omission costs are real: conference records,
non-MEDLINE indexed articles, records indexed only in subscription bibliographic
databases, and trials discoverable through curated trial-register collections may
be missed. Any missing study found later from one of those omitted sources is a
finding about the limits of this review's search, not a reason to relabel the
search as comprehensive.

## 4A - Linkage method and its known failure modes

Before the search runs, registry records will be linked to publications in this
order:

1. Read the ClinicalTrials.gov API v2 study record, including protocol-section
   identifiers, arms, outcome modules, references, and posted results where
   available.
2. Treat a registry reference with `reference_type='result'` and a PMID as a
   candidate publication, not as proof.
3. Query PubMed through E-utilities for the NCT identifier using the registered
   identifier as a secondary-source identifier or text identifier.
4. Accept a publication link only when the NCT identifier, trial acronym, sponsor
   trial name, population, arms, and week-24 calculated LDL cholesterol outcome
   are concordant enough to identify the same trial. Discordance is recorded
   rather than resolved by convenience.

Two known linkage failure modes are fixed here before execution. First, PubMed
silently drops trials from ID-based queries when the record is not indexed, so an
absent result is indistinguishable from a trial that does not exist. Second,
registry `reference_type='result'` links can point at the wrong paper, which is
worse than a missing link because a wrong link looks like a successful one.

Where linkage succeeds, registry data matched the publication in 26 of 28
analyses compared on this corpus. That is a conditional figure: the denominator
is linked analyses, not all analyses, and therefore it is not a general registry
reliability rate.

## 5 - Search strategy - the exact strings to be executed

These strings are stated **before** execution. The search lane will record what it
actually ran, on what date, with what filters, and how many records each returned;
any departure from the strings below will be recorded as a departure rather than
silently substituted. Each string is kept under 20 Boolean operators because an
unexecutable registered string would force a departure on the first attempt.

**PubMed topic search, through NCBI E-utilities**

```
("alirocumab"[tiab] OR "SAR236553"[tiab] OR "REGN727"[tiab])
AND (placebo[tiab])
AND ("LDL-C"[tiab] OR "LDL cholesterol"[tiab] OR "low-density lipoprotein cholesterol"[tiab])
AND (randomized[tiab] OR randomised[tiab] OR trial[tiab])
```

Filters: none on language, none on date.

**PubMed registry-publication linkage query template, through NCBI E-utilities**

```
"{NCT_ID}"[si] OR "{NCT_ID}"[tiab]
```

The concrete NCT identifier substituted into `{NCT_ID}` is recorded for each
execution. A failed execution still counts as a query attempt for the ordering
test.

**ClinicalTrials.gov API v2**

```
query.intr=alirocumab OR SAR236553 OR REGN727
query.cond=hypercholesterolemia OR hypercholesterolaemia OR dyslipidemia
filter.overallStatus=COMPLETED|TERMINATED|ACTIVE_NOT_RECRUITING
```

No date filter is applied. Records returned by the registry search are screened
against the axes in section 3, not against the convenience of matching the
current object.

## 5A - How this search can fail, decided in advance

Every search outcome is interpreted before execution:

- If the search reproduces the held set, the held set is described as
  searched-for rather than convenient. It is still not proof that no other
  eligible trial exists.
- If the search returns additional eligible trials, that is a finding about the
  review. Each additional trial is named and included or excluded on one of the
  axes in section 3.
- If the search returns fewer trials than the object holds, that is a finding
  about the search, never reported as the review being wrong.

The worked example is finerenone-cv: the registry query missed FIGARO-DKD
(NCT02545049), a pivotal trial, because it registers its condition as "Diabetic
Kidney Disease" alone while its sibling FIDELIO-DKD registers "Chronic Kidney
Disease". A narrow query looks exactly like a wrong review.

## 6 - Study selection process

Two **independent screeners of different model families** will screen all records.
The cross-family rule is a requirement, not a preference, because two instances
of one model is one screener run twice and its agreement statistic is
meaningless.

Screening is in two stages: title and abstract where PubMed supplies them, then
the full ClinicalTrials.gov API v2 registry record and PubMed-linked publication
record where available. **Each screener's decision is recorded per record at the
stage it was applied**, together with the reason. Both screeners' decisions are
published, not only the reconciled outcome, along with the agreement rate and how
every disagreement was resolved.

**Adjudication of disagreements is by a named human.**

**Two release tiers, and the difference between them is attestation, not content.**
The website release requires the two cross-family AI assessments and states
plainly that it has not been human-verified. The submission release additionally
requires two named human reviewers to have checked every included study and every
extracted datum; the statement to that effect is emitted only when those
attestation records exist and is never written as prose.

## 7 - Data extraction

Extracted per trial and per outcome: registry identifier, linked publication if
accepted under section 4A, year, design, population, arms, analysis population,
randomised total where available, analysed denominator where available, percent
change from baseline in calculated LDL cholesterol at week 24 by arm where
reported, the between-arm effect estimate where reported, its uncertainty, and
the stated confidence level.

Every included or excluded record is classified against the section 3 axes and no
others: DESIGN, POPULATION, INTERVENTION, COMPARATOR, and MEASURE. If a record
fails more than one axis, each failed section 3 axis is recorded, but no new axis
is introduced during extraction or reporting.

Any axis read from a registry title remains provisional until the registered
primary outcome measure is read from the outcome module. A title is not an
outcome definition. Trial IDs, NCT IDs, PMIDs, DOIs, study dates, arms, outcome
names, and analysis populations are resolved from source records rather than from
recall.

Every extracted cell carries a resolvable pointer to the specific document and,
where possible, to the table, outcome module, or results field within it, so that
a human check can be made without leaving the page. **Nothing is computed that
can be read.** No model-adjusted contrast is reconstructed where the contrast is
reported directly. No value is derived from a rounded percentage when an
unrounded value or standard error is available from the source.

Where two populations exist for one outcome, both are recorded, exactly one is
marked as selected, and the population is named on the cell.

## 8 - Outcomes and prioritisation

**Primary:** percent change from baseline in calculated LDL cholesterol at week
24, expressed as alirocumab minus placebo in percentage points.

**Secondary outcomes, read and reported but not pooled unless they meet a
separate registered question:** percent change from baseline in measured LDL
cholesterol; absolute LDL cholesterol change; LDL cholesterol goal attainment;
apolipoprotein B; non-HDL cholesterol; total cholesterol; HDL cholesterol;
triglycerides; lipoprotein(a); and adverse events. They are shown because a
reader should see them; they are not pooled into this review's headline because
they are not this estimand.

## 9 - Risk of bias

**Tool.** Cochrane risk-of-bias tool for randomized trials, version 2 (RoB-2).

**Unit of assessment.** RoB-2 is applied **to the result being pooled, not to the
trial as a whole**: percent change from baseline in calculated LDL cholesterol at
week 24. One trial may therefore carry a different judgement for this result than
it would for its own primary endpoint, and that is the intended behaviour of the
tool.

**Variant.** The **effect of assignment to intervention** variant, because the
primary extraction follows the randomized-analysis population where available.
The adherence variant is not used, and no result assessed under one variant will
be reported as though assessed under the other.

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

**Relationship to the recorded bias features.** Any bias-relevant features already
held on the object are **inputs to the assessment and never substitutes for a
domain judgement**. No existing prose in the object may stand in for a signalling
question or a domain rating.

**Feeding GRADE.** The completed RoB-2 result becomes the basis of the GRADE
risk-of-bias domain, replacing any current reasoning from recorded features. When
it does, the review will state **whether the GRADE rating moves and why - and if
it does not move, will say so explicitly** rather than leaving the reader to
infer that nothing changed.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No RoB-2 assessment exists for these trials in this protocol.
Performing it later **executes this section rather than amending it**, and the
object will record that distinction.

## 10 - Synthesis methods

The primary synthesis is a random-effects network meta-analysis of mean
differences in percent change from baseline in calculated LDL cholesterol at week
24. Effects are expressed as alirocumab strategy minus placebo strategy in
percentage points. The model uses contrast-level estimates, inverse-variance
weighting, and a common between-study variance across the connected network.

**Pre-specified, so that reporting a disagreement between methods is a commitment
rather than a post-hoc observation:**

- **REML** is the headline between-study-variance estimator.
- The **Hartung-Knapp-Sidik-Jonkman interval is reported alongside** the Wald
  interval where pairwise random-effects contrasts are estimable, and where the
  two disagree about whether the interval crosses the null, that disagreement is
  reported in the results rather than resolved by choosing one.
- **Leave-one-out** analysis is run and reported for the direct placebo-linked
  evidence where the number of studies makes it meaningful.
- An **estimator comparison** - DerSimonian-Laird, REML, Paule-Mandel - is run
  and reported, per Cochrane Handbook v6.5 section 10.10.4.4, on the
  understanding that with few studies the choice is plausibly influential.
- A **prediction interval** is reported using the t distribution on k-1 degrees
  of freedom per Handbook v6.5 where defined, and is not reported where k makes
  it undefined.
- The analysis is **cross-checked in a second engine** at build time and the
  comparison published, including any quantity on which the two engines disagree
  by definition rather than by error.

**Heterogeneity:** tau^2, I^2 with its Q-profile confidence interval, and Q with
its degrees of freedom and p value. I^2 is reported with the caveat that at small
k a low value reflects imprecision as much as agreement.

## 10A - Network geometry and what it forbids

This is a network, not a single pairwise comparison. The topology below is
derived from the object's own arms and is an established fact, not an assumption.

Nodes (6):

- Alirocumab 150 mg Q2W
- Alirocumab 75 mg/Up to 150 mg Q2W
- Alirocumab 75 mg/up to 150 mg
- Alirocumab 75/150 mg Q2W
- Placebo
- Placebo Q2W

Edges: 5. Connected: True. Independent loops by E - V + 1: 0.

This network has zero loops. Indirect comparisons are computable because the
network is connected, but the consistency assumption they rest on **CANNOT BE
TESTED** - not "was not tested", cannot be, by the geometry. Node-splitting and
design-by-treatment interaction are unavailable, and their absence must never be
reported as consistency having been checked.

No SUCRA or ranking will be reported. Publication bias is **not assessable**
rather than not serious, and GRADE carries incoherence as untestable.

A head-to-head trial between two non-comparator nodes would add a non-placebo
edge. If that edge closes a path already running through a placebo node, it would
create at least one independent loop and make inconsistency evaluation possible
for that closed geometry. It would not prove the present tree consistent after
the fact; it would change the geometry of the evidence base being analysed.

## 11 - Subgroup and sensitivity analyses

**Sensitivity, pre-specified:** leave-one-out where defined; the estimator
comparison above; exclusion of trials where the selected outcome is not the
registered primary outcome; exclusion of trials where the selected analysis set
is not the randomized or intention-to-treat population; and direct-only placebo
comparisons shown separately from network estimates.

**Subgroup: none pre-specified.** With the small number of trials this comparison
has and a tree-shaped network, any subgroup contrast would be underpowered and
post-hoc, and none will be presented as though it were planned.

## 12 - Meta-bias assessment

Funnel plot and Egger's regression are planned only as displays or computations
where the evidence base is large enough for their assumptions to be meaningful.
For this network, publication bias is **not assessable** rather than not serious.
The GRADE publication-bias domain will read *not assessable* rather than *not
serious* unless a later amendment changes the evidence base and justifies a
different pre-specified assessment.

## 13 - Certainty of the evidence

GRADE, per Cochrane Handbook v6.5 sections 14.2.1-14.2.2 and MECIR C74/C75. All
five downgrade domains are assessed and **each rating is published with the
evidence it rests on**; the overall certainty is computed from the domains and
shown against them so a reader can check the arithmetic.

RoB-2 is **PENDING**. GRADE is **PENDING**. Incoherence is carried as untestable
because the network has no independent loop. Publication bias is carried as not
assessable rather than not serious. No completed RoB-2 or GRADE judgement is
implied by this protocol.

## 14 - Data sharing and reproducibility

The canonical data object from which every number on the review page is projected
is published with the review, together with the session information and the
analysis scripts actually executed. The intent is that the review can be rebuilt
from the object alone.

The registered search strings, raw API responses where licensing permits,
screening decisions, linkage decisions, extraction pointers, analysis scripts,
and post-search anchor record are retained. No local path, secret, or private
credential is required to reproduce the public object.

## 15 - Funding and conflicts of interest

**No funding was received for this review.** No competing interests are declared
by the authors of this protocol at the time of this commit. Any change is to be
recorded as an amendment rather than by editing this section.

## 16 - Amendments

None at this commit.

Amendments will be recorded as further commits to this file; the full commit
history, not only its head, is projected onto the review page, because a log that
displays only its own head is no better than a mutable document.
