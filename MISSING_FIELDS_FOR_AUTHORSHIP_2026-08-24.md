# What is missing, and which of it needs a person

Measured against all **50 topics that hold at least one readable per-trial estimate** (groups A
and B). Every count below comes from probing the objects for keys **observed in the corpus**,
not keys I expected to find — the first pass of this measurement guessed `n_randomised` and an
object-level `grade`, reported `0/50` for both, and was wrong on both. The corrected numbers are
the ones here.

The question this answers: *what would have to exist before these pages could carry a rationale,
a synthesis and an interpretation* — split into what costs extraction work and what costs a
judgement somebody puts their name to.

---

## Bucket 1 — already held, simply not projected

No new data. This is projection debt, and it is the cheapest work on the list.

| Field | Topics holding it | Note |
|---|---|---|
| Estimator / model named | 50/50 (100%) | |
| Arm structure per trial | 43/50 (86%) | |
| Heterogeneity | 42/50 (84%) | |
| Comparator type | 41/50 (82%) | |
| Direction of benefit | 34/50 (68%) | |
| How each estimate was derived | 34/50 (68%) | reads as codebook prose; needs English, not data |
| Comparison with published meta-analyses | 32/50 (64%) | |
| **Per-trial estimate on an unpooled outcome** | 28/50 (56%) | **was being withheld from readers entirely** |
| N enrolled per trial | 28/50 (56%) | stored as `enrolled` / `registration_enrolment` |
| Risk of bias | 25/50 (50%) | held per *result*, which is better than most reviews manage |
| Population, per result | 24/50 (48%) | the omission every blind reviewer named first |
| Design per trial | 18/50 (36%) | carries "stopped early", "primary endpoint changed" |
| Source links | 12/50 (24%) | |
| Sensitivity analysis | 10/50 (20%) | |
| GRADE certainty | 4/50 (8%) | on the **outcome block**, not the object |

The prototype now projects all of these for `sotagliflozin-hf`. Doing so raised the blind panel
from 2/5 to **5/5 clear** and moved every reviewer to preferring this form over a review article.

## Bucket 2 — not held, but retrievable without anyone exercising judgement

Extraction work against sources we have already read. No authorship required; a second reader
could check every value against the registry or the paper and agree or disagree on fact.

| Field | Topics holding it | Where it would come from |
|---|---|---|
| Follow-up duration | 0/50 | the registrations, already read in full |
| Arm-level event counts | ~2/50, ad hoc | see note below |
| Arm denominators | 1/50 | registry results postings |
| Baseline / control-arm risk | 0/50 | derivable once arm counts exist |
| Absolute risk reduction, NNT | 0/50 | derivable once arm counts exist |
| Harms / adverse events | 0/50 | registry adverse-event tables, publications |
| Endpoint definitions verbatim | 5/50 | registrations |

**On arm-level counts.** They are not simply absent. A handful of topics carry them under
bespoke, topic-specific key names — `events_apixaban`, `n_apixaban`, `events_comparator`,
`treatment_deaths`, `control_deaths`, `treatment_cured`, `control_failures`, `treatment_evaluable`.
That is ad hoc storage on two or three topics, not a schema, and nothing can project it
generically. Reporting this as "0/50" would be wrong; reporting it as "held" would be worse.

Bucket 2 is what stands between the current report and clinical usefulness. Every one of the five
blind reviewers said the same thing in the same place: they could not act on the report without
absolute numbers, follow-up time and harms. Two of them said the document was "entirely useless
for making a prescribing decision" for exactly this reason — while still preferring its form.

## Bucket 3 — requires a judgement someone stands behind

Nothing in the objects supports these, and nothing can be extracted to produce them. Each is a
claim a named author defends.

| Field | Topics holding it | What it actually requires |
|---|---|---|
| Rationale — why this question matters now | 0/50 | a view about the clinical gap |
| Synthesis — what the estimates mean together | 0/50 | a judgement that these results cohere, or do not |
| Interpretation / applicability | 0/50 | who this evidence is for, and who it is not for |
| Position against the rest of the field | 0/50 | a comparison the data cannot make for itself |
| Decision threshold for "imprecision" | 0/50 | reviewers asked "wide relative to what?" — an answer is a judgement |

**This is the list Mahmood is being asked to buy.** Buckets 1 and 2 are labour. Bucket 3 is
authorship, and it is the entire distance between an evidence report and a review.

---

## What the measurement settled

The five preceding rounds of fixes treated the problem as prose quality — vocabulary, structure,
length. Each corrected a real defect and none moved a blind panel. This measurement says why:
the objects hold an extraction record, and the three sections a review is *for* have no source in
them at all. Bucket 3 is empty and cannot be filled by any generator.

But the panel result is the useful half. Asked to judge the same evidence presented **as what it
is** — a report that states what was found and refuses to interpret it — five of five reviewers
across two model families called it clear, five of five called it honest, and five of five said
they would rather have it than a review article written from the same evidence. One of them had
preferred the review article one round earlier and changed position after the projection debt in
Bucket 1 was paid.

That makes the genre decision straightforward and the authorship decision optional rather than
blocking: **49 A/B topics can ship as evidence reports without anyone writing a word of Bucket
3**, provided Bucket 2 is funded so the reports are usable as well as honest.

## Defect found while doing this

`sotagliflozin-hf` / `mace3_first` is rated LOW certainty and downgraded **for risk of bias**,
while no risk-of-bias assessment exists for that result. Corpus-wide: **1 of 11 GRADE-rated
outcomes**. Bounded, not systemic. The prototype states the inconsistency to the reader rather
than passing the rating on silently; the object still needs fixing at source.
