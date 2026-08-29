# Protocol - V114 versus Prevnar 13: the four solicited injection-site symptoms

**Status: RETROSPECTIVELY REGISTERED BY COMMIT. This document is the
registration.**

This protocol is registered as a commit in a public repository rather than in
PROSPERO. The commit hash is the strong half of that record: the content is
immutable under it, so this text cannot be altered later without producing a
different hash, and anyone can check that much without asking us. No PROSPERO
registration number is claimed.

**The commit timestamp is the weak half, and this document will not pretend
otherwise.** Both the author and the committer date on a git commit are supplied
by whoever makes the commit and can be set to any value; commits here are
unsigned and a git timestamp proves nothing further. The commit hash binds the
text; the repository is public. Where an entry for the commit exists in a public
transparency log, that log's inclusion time is an upper bound on when this text
existed, set by a third party rather than by us.

What the mechanism supports, and no more: this exact text is bound to this hash;
the repository is public, so the text is readable by anyone at that hash; and a
transparency-log entry proves the narrow claim that **the text existed no later
than the log time**.

What it does not support: it does not prove when the commit was made, it does not
prove that no earlier or parallel version existed elsewhere, it does not prove
the data had not already been seen, and it says nothing about the independence
of the people who wrote it. Those are claims about conduct, and no timestamp can
carry them.

**How to check this without us.** The verification recipe, the public half of
the signing key, and a worked example are at
[`ssot/registration/VERIFY.md`](../registration/VERIFY.md). It states the
limitation plainly as well: the log time is independent of us, the key custody
is not. A stranger can verify the text existed by the log time and that we
signed it; a stranger cannot verify we did not hold an earlier version.

**It is written before the search runs.** The ordering test this review
publishes is that this protocol is committed, pushed, and anchored in a public
transparency log before the first executed query - the first *attempt*, including
a failed attempt, not the first success, because reporting only the successful
execution would move the first-query time later and flatter the claim. The
search record is anchored afterwards so two third-party times bracket the
operation.

Both execution times are read from the search lane's own clock. The databases
return records, not authoritative execution timestamps, so no part of the search
ordering is timestamped by a third party unless an external anchor is placed on
each end. The sequence is therefore auditable and bracketed, and it is not, on
its own, proof of what was known before authorship.

---

## 1 · Review question, in PICO

This topic already holds 7 trials:
NCT02547649, NCT03547167, NCT03620162, NCT03692871, NCT03848065, NCT03921424,
and NCT03950622. The question is being authored after that evidence was
assembled. However carefully it is written now, this is a retrospectively
registered protocol. The anchor proves when this text was written and CANNOT
prove the trials had not already been seen. A timestamp bounds when, never what
was known.

| | |
|---|---|
| **Population** | Participants randomised in pneumococcal conjugate vaccine trials comparing a V114-containing arm with a Prevnar 13-containing comparator arm. |
| **Intervention** | V114, the 15-valent pneumococcal conjugate vaccine, including labelled formulation or schedule variants when the arm is analyzable as V114. |
| **Comparator** | Prevnar 13, including labelled formulation or schedule variants when the arm is analyzable as Prevnar 13. |
| **Outcome** | Each solicited injection-site symptom reported as a participant-level risk within the trial's protocol-defined post-vaccination window: pain or tenderness; swelling; erythema or redness; induration or hard lump. |
| **Study design** | Randomised controlled trials. |

**Frozen question:** in participants randomised to the 15-valent pneumococcal
conjugate vaccine V114 or to the 13-valent comparator Prevnar 13, how does the
risk of each solicited injection-site symptom compare?

## 2 · Estimand, stated in advance

The estimand is the **per-participant risk ratio for each solicited
injection-site symptom**, on the log scale, comparing V114 with Prevnar 13
within the outcome window defined by the trial protocol. The participant is the
unit of analysis.

**Quantities that cannot be converted into that estimand are excluded on the
OUTCOME axis, not on grounds of quality.** This is registered because it is a
criterion and not a judgement made after seeing results. A trial may be large,
well conducted and directly on topic and still fail this review's eligibility
because it reports something else. Specifically and in advance:

- A count of any solicited injection-site adverse event is not the same outcome
  as a named symptom class.
- A severity-only result without an analyzable participant-level occurrence
  count is not this estimand.
- A percentage without a recoverable analysis denominator is not used to invent a
  count.
- A systemic adverse event, immunogenicity endpoint, or pneumococcal disease
  endpoint is not this estimand.

## 3 · Eligibility criteria

**Include** a study-outcome if all axes hold: the study is randomised; the
population consists of participants receiving pneumococcal conjugate vaccination;
the intervention/comparator contrast can be classified as V114 versus Prevnar
13; and the outcome module reports an analyzable participant-level risk for at
least one of the four solicited injection-site symptoms named in section 1.

**Exclude** on any single failed axis - study design, population,
intervention/comparator, or outcome/measure - and record which axis failed and
what the study reports instead. Section 7 will classify records against these
axes and no others.

Arm labels, title words, and registry brief titles are not outcome definitions.
Any axis read from a registry title is provisional until the registered primary
outcome measure is read from the outcome module. A title may help locate a
record; it does not decide eligibility for an outcome.

Populations narrower than the question, such as infants, children, adults, or a
single risk stratum, are **not** indirect on that ground alone; narrowness is
recorded and carried into the GRADE indirectness domain rather than used as an
exclusion.

## 4 · Information sources

PubMed through NCBI E-utilities and ClinicalTrials.gov API v2 only.

Embase was NOT searched. CENTRAL was NOT searched. Web of Science was NOT
searched. Scopus was NOT searched. This search is not comprehensive and will
not be described as comprehensive. The omission costs coverage: records indexed
only in subscription bibliographic databases, conference proceedings, or trial
registers outside ClinicalTrials.gov can be missed; citation chaining from
published syntheses is also not a rescue path in this protocol.

## 4A · Linkage method and its known failure modes

Registry records will be linked to publications before extraction by a bounded,
recorded rule:

- First, read the ClinicalTrials.gov API v2 record and collect registry-posted
  references, PMIDs, DOIs, and any NCT identifiers present in reference metadata.
- Second, query PubMed through NCBI E-utilities for the NCT identifier and for
  the topic strings in section 5.
- Third, accept a publication link only when the candidate publication matches
  the registry record on the NCT identifier or an equivalent trial identifier
  and on the vaccine arms relevant to this review. A registry reference marked
  as a result is a candidate link, not proof.
- Fourth, where a linked publication is used, reconcile the publication against
  the registry outcome module and record the source used for each extracted
  cell.

Two failure modes are already measured on this corpus and are named here before
the search is run. First, PubMed silently DROPS trials from ID-based queries when
the record is not indexed, so an absent result is indistinguishable from a trial
that does not exist. Second, registry `reference_type='result'` links can point
at the WRONG paper, which is worse than a missing link because a wrong link
looks like a successful one.

Where linkage succeeds, registry data matched the publication in 26 of 28
analyses compared on this corpus. That is conditional on linked analyses; its
denominator is linked analyses, not all analyses, and it is therefore not a
general reliability rate.

## 5 · Search strategy - the exact strings to be executed

These strings are stated **before** execution. The search lane will record what
it actually ran, on what date, with what filters, and how many records each
returned; any departure from the strings below will be recorded as a departure
rather than silently substituted. Each string is kept under 20 Boolean
operators because the interface refuses more; a registered string that cannot
be executed would force a departure on the first attempt.

**PubMed topic query**

```text
("V114"[tiab] OR "PCV15"[tiab] OR VAXNEUVANCE[tiab] OR "15-valent pneumococcal conjugate vaccine"[tiab])
AND ("Prevnar 13"[tiab] OR "PCV13"[tiab] OR "13-valent pneumococcal conjugate vaccine"[tiab])
AND ("Pneumococcal Vaccines"[MeSH Terms] OR pneumococcal[tiab])
AND (randomized controlled trial[pt] OR randomised[tiab] OR randomized[tiab] OR trial[tiab])
```

Filters: none on language, none on date. Rationale: a language or date filter
would make the omission of records harder to interpret and would create another
axis of departure across interfaces.

**PubMed trial-identifier linkage query**

```text
NCT02547649[si] OR NCT03547167[si] OR NCT03620162[si] OR NCT03692871[si] OR NCT03848065[si] OR NCT03921424[si] OR NCT03950622[si]
```

Filters: none on language, none on date. An absent PubMed result from this query
is treated as an unresolved linkage state, not as proof that no publication
exists.

**ClinicalTrials.gov (API v2)**

```text
query.intr=V114 OR PCV15 OR VAXNEUVANCE OR "15-valent pneumococcal conjugate vaccine"
query.cond=pneumococcal
filter.overallStatus=COMPLETED|TERMINATED|ACTIVE_NOT_RECRUITING
```

## 5A · How this search can fail, decided in advance

The search result will be read under these fixed interpretations:

- If the search reproduces the held set, that is reported as searched-for rather
  than convenient. The result supports discoverability under the registered
  strings; it does not erase the retrospective status of the protocol.
- If the search returns additional eligible trials, that is a finding about the
  REVIEW. Each additional trial is named and then included or excluded on one of
  the section 3 axes.
- If the search returns fewer trials than the object holds, that is a finding
  about the SEARCH, never reported as the review being wrong.

Worked example for the third case: the finerenone-cv registry query missed
FIGARO-DKD (NCT02545049), a pivotal trial, because it registers its condition as
"Diabetic Kidney Disease" alone while its sibling FIDELIO-DKD registers "Chronic
Kidney Disease". A narrow query looks exactly like a wrong review.

## 6 · Study selection process

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

## 7 · Data extraction

Extracted per trial and per symptom: registry identifier, primary publication
where linked, year, design, population, arms, the analysed denominator and the
randomised total separately, per-arm symptom counts where directly available,
the reported percentage where given, the observation window, who recorded the
symptom when stated, and the source outcome/module/table used.

Every extracted cell carries a resolvable pointer to the specific document and,
where possible, to the table or registry module within it, so that a human check
can be made without leaving the page. **Nothing is computed that can be read.**
No count is derived from a percentage; no composite is reconstructed by summing
its components. If a source reports only a percentage and denominator, those are
stored as the source reports them and the missing count is treated as missing
rather than invented. Identifiers are resolved by lookup, never from recall.

Eligibility classifications use only the section 3 axes: study design,
population, intervention/comparator, and outcome/measure. A registry title can
only create a provisional classification; final outcome classification requires
reading the registered primary outcome measure and posted outcome module.

Where two populations exist for one outcome - for example a safety analysis set
and a randomised set - both are recorded, exactly one is marked as selected, and
the population is named on the cell.

## 8 · Outcomes and prioritisation

**Primary outcomes:** the four solicited injection-site symptoms, reported
separately:

- Injection-site pain or tenderness.
- Injection-site swelling.
- Injection-site erythema or redness.
- Injection-site induration or hard lump.

No hierarchy among the four symptoms is registered. They are not components of a
single headline chosen after extraction; all four are displayed and interpreted
as separate symptom risks.

**Read but not pooled as primary symptom outcomes:** any solicited injection-site
adverse event, severe symptom grades, systemic adverse events, immunogenicity
endpoints, and pneumococcal disease endpoints.

## 9 · Risk of bias

**Tool.** Cochrane risk-of-bias tool for randomized trials, version 2 (RoB-2).

**Unit of assessment.** RoB-2 is applied **to the result being pooled or
displayed, not to the trial as a whole**: each solicited injection-site symptom,
expressed as participant-level risk. One trial may therefore carry a different
judgement for this result than it would for its own primary immunogenicity
endpoint, and that is the intended behaviour of the tool.

**Variant.** The **effect of assignment to intervention** variant, because the
review compares randomised vaccine arms. The adherence variant is not used, and
no result assessed under one variant will be reported as though assessed under
the other.

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
and its supplement where linked, and the posted results module. A judgement made
from an abstract alone is not the same act as one made from a protocol, so **the
sources actually consulted are recorded per domain**, and a domain judged
without access to the protocol is marked as such rather than presented as
equivalent.

**Relationship to the recorded bias features.** The object may already hold
bias-relevant features, including analysis population, blinding, endpoint rank,
and source of outcome reporting. These are **inputs to the assessment and never
substitutes for a domain judgement**. No existing prose in the object may stand
in for a signalling question or a domain rating.

**Feeding GRADE.** The completed RoB-2 result becomes the basis of the GRADE
risk-of-bias domain, replacing any current reasoning from recorded features.
When it does, the review will state **whether the GRADE rating moves and why -
and if it does not move, will say so explicitly** rather than leaving the reader
to infer that nothing changed.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No RoB-2 assessment exists for these trials in this protocol.
Performing it later executes this section rather than amending it, and the
object will record that distinction.

## 10 · Synthesis methods

The primary comparison is V114 versus Prevnar 13 for each symptom on the log
risk-ratio scale, with inverse-variance weighting where a pool is justified by
the registered measurement definitions. If observation windows, reporter
definitions, arm mappings, or endpoint definitions make pooling incoherent, the
review will display trial-level estimates and state why a pool is not made.

Where a direct pairwise pool is justified:

- **REML** is the headline between-study-variance estimator.
- The **Hartung-Knapp-Sidik-Jonkman interval is reported alongside** the Wald
  interval, and where the two disagree about whether the interval crosses the
  null, that disagreement is reported in the results rather than resolved by
  choosing one.
- **Leave-one-out** analysis is run and reported for every pool where it is
  defined.
- An **estimator comparison** - DerSimonian-Laird, REML, Paule-Mandel - is run
  and reported on the understanding that with few studies the choice is
  plausibly influential.
- A **prediction interval** is reported using the t distribution on k - 1
  degrees of freedom and is not reported where k makes it undefined.
- The analysis is **cross-checked in a second engine** at build time and the
  comparison published, including any quantity on which the two engines disagree
  by definition rather than by error.

**Heterogeneity:** tau-squared, I-squared with its interval where defined, and Q
with its degrees of freedom and p value. I-squared is reported with the caveat
that at small k a low value reflects imprecision as much as agreement.

## 10A · Network geometry and what it forbids

This is a network. The topology is derived from the object's own arms and is an
established fact, not an assumption:

- Nodes: Group 1: Prevnar 13™-Prevnar 13™-Prevnar 13™-Prevnar 13™; Group 5:
  V114-V114-V114-V114; PCV13-SC; Prevnar 13®; Prevnar 13™; V114; V114-A;
  V114-B.
- Node count: 9.
- Edges: 6.
- Connected: False.
- Independent loops by E - V + 1: -2.
- Loops available for consistency assessment: ZERO.

The full graph is recorded as disconnected. Within any connected comparison
component used for an indirect contrast, indirect comparisons are computable
because the network is connected, but the consistency assumption they rest on
CANNOT BE TESTED - not "was not tested", cannot be, by the geometry. There are
zero independent loops, so there is no closed evidence cycle against which to
compare direct and indirect estimates.

Node-splitting and design-by-treatment interaction are unavailable. Their
absence must never be reported as consistency having been checked. No SUCRA or
ranking will be reported. Publication bias is NOT ASSESSABLE rather than not
serious, and GRADE carries incoherence as untestable.

A head-to-head trial between two non-comparator nodes would add a direct edge
that does not pass through Prevnar 13. If the two nodes already had an indirect
path between them, that trial would create the first loop for that component and
would make local inconsistency checks possible for affected contrasts. If it
only connected two previously disconnected components, it would improve
connectedness but would still not create a loop or make consistency testable.

## 11 · Subgroup and sensitivity analyses

**Sensitivity, stated in advance:** leave-one-out where defined; the estimator
comparison above; continuity-correction sensitivity for zero-event cells; and
per-protocol versus safety-analysis denominators where both are available and
clearly defined.

**Subgroup: none stated in advance as confirmatory.** Age group, observation
window, reporter, formulation, route, and schedule may be shown descriptively if
they are needed to explain why a pool is or is not coherent. They will not be
presented as planned effect-modifier tests unless the object contains an
amendment recorded before those tests are run.

## 12 · Meta-bias assessment

Publication bias is NOT ASSESSABLE for this network rather than not serious.
That distinction is part of the registered method. Funnel plot, Egger's
regression, and Peters' test require more evidence structure than this network
can provide for meaningful interpretation; where computed mechanically, they
will be labelled as computed values only and not as evidence about small-study
effects.

The GRADE publication-bias domain will read *not assessable* rather than *not
serious* unless a later amendment records a defensible assessability rule before
the corresponding analysis is run.

## 13 · Certainty of the evidence

GRADE, per Cochrane Handbook principles for intervention reviews. All five
downgrade domains are assessed and **each rating is published with the evidence
it rests on**; the overall certainty is computed from the domains and shown
against them so a reader can check the arithmetic.

**Status at the time of this commit: PENDING.** No completed GRADE certainty
assessment exists for these outcomes in this protocol.

Risk of bias is PENDING until RoB-2 is completed. Incoherence is carried as
untestable because the network has zero loops. Publication bias is carried as
not assessable unless a later registered method makes it assessable.

## 14 · Data sharing and reproducibility

The canonical data object from which every number on the review page is
projected is published with the review, together with the session information
and the analysis scripts actually executed. The intent is that the review can be
rebuilt from the object alone.

The protocol commit is pushed and anchored before the first search query. The
post-search record is anchored afterwards. The two anchors bracket the search
operation, but neither anchor proves what the authors knew before the protocol
was written.

## 15 · Funding and conflicts of interest

**No funding was received for this review.** No competing interests are declared
by the authors of this protocol at the time of this commit. Any change is to be
recorded as an amendment rather than by editing this section.

## 16 · Amendments

Amendments will be recorded as further commits to this file; the full commit
history, not only its head, is projected onto the review page, because a log
that displays only its own head is no better than a mutable document.
