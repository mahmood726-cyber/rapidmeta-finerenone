# The corpus panel: what 149 Paper Studio pages look like to a student and to an editor

**Read date 2026-08-25. Complete: 298 of 298 jobs returned, 0 failures, all 149 pages read by
both personas. Every rate carries its denominator.**

Two readers per page. A **medical student** unfamiliar with the field, asked the only
question Mahmood has ever set for this work — *could you improve this without being misled by
it?* And an **editor**, asked whether the submission goes to peer review or is desk-rejected.
They disagree by construction: the student rewards disclosure, the editor punishes it.

Every job carried a published comparator. Each reader saw two documents, A and B, one of them
the Zelniker *Lancet* 2019 SGLT2 meta-analysis, and was not told which was which. Order
alternated by page index.

---

## First, the thing that has to be said before any rate is read

**The median Paper Studio panel is 1,397 characters. 99 of the 149 are notes, not
manuscripts.**

I ran the whole corpus against a published *Lancet* paper and reported the result before
checking that the two things were the same kind of object. They are not. Of 149 pages:

| | pages | median length |
|---|---|---|
| full manuscripts (≥3,000 chars) | **50** | — |
| short notes explaining why no pool was possible | **99** | ~1,400 chars |

DABIGATRAN_VTE_EXTENDED's entire paper panel is 1,064 characters. The editor sent it for
peer review and called its method "sound … correctly noting that 'the contrast differs, not
just the measurement.'" That is not a page clearing the bar. It is a page with too little in
it to reject — and its 1,064 characters never contain the word "search" at all, so it does
not carry the disclosure that sinks the pages that do.

So the corpus-wide rates below are real but they are not what they look like, and the honest
comparison is the manuscripts-only row.

**And the 99 notes are correct behaviour, not a rendering failure** — which took a fourth
over-flag today to establish. A first count said 97 of the 99 short pages held a pooled
estimate on the object while rendering ~1,100 characters, which would have been a large
rendering defect. It counted any populated result block as a pool. BEMPEDOIC_ACID is typical:
`k: 1`, `model: "single study"`, `poolable: false`, and the page correctly reports that one
trial's own HR with the reason nothing is combined. Re-measured on the thing actually meant —
two or more trials **and** the object marking the outcome poolable — **0 of the 99 short pages
hide a real pool.** The short page is what an honest projection of a single-trial or
no-result topic looks like.

What the corpus actually contains, by what the objects hold:

| | pages |
|---|---|
| a pooled synthesis written up | **22** |
| a long argument for why this topic does not pool (≥3,000 chars, no poolable outcome) | 28 |
| a short note: one trial, or no results at all | 99 |

69 objects have no result recorded on any outcome; 21 have exactly one trial. That is 90 of
149 topics on which no meta-analysis is possible, and on which the page says so. **The answer
to "are the papers finished" starts by conceding that there are 22 papers, not 149.**

---

## The result, split by whether there is a paper there

| | all 149 | **full manuscripts (50)** | short notes (99) | Zelniker |
|---|---|---|---|---|
| student says SAFE | 111/149  74.5% | **38/50   76.0%** | 73/99  73.7% | 81/149  54.4% |
| editor sends to REVIEW | 4/149   2.7% | **1/50    2.0%** | 3/99   3.0% | 146/149  98.0% |

The anchor is behaving as a control in both directions, which is what licenses reading either
row. The editor sends the published paper to review 146 times out of 149 — so a 2% review
rate is not a reader who rejects everything. The student calls the published paper misleading
68 times out of 149 — so a 76% safe rate is not a reader who accepts everything.

**On full manuscripts, our pages mislead a novice less than a Lancet meta-analysis — 76.0%
against 54.4% — and one of fifty was sent to review.** That one was ARNI, on a single draw
that **does not replicate** — see the ARNI section below, where 24 replicated jobs return
DESK-REJECT 10 times out of 12. Read the 1/50 as "one page got a favourable draw", not as
"one page cleared the bar".

Note what the split does *not* show: the student's safe rate is the same for notes as for
manuscripts (73.7% against 76.0%). A one-paragraph note is safe because there is nothing in
it to be misled by. The student measure is close to insensitive to whether a paper exists,
which is a limitation of the instrument and not a property of the corpus.

The joint shape across all 149:

| student | editor | pages |
|---|---|---|
| SAFE | DESK-REJECT | **108** |
| MISLEADING | DESK-REJECT | 37 |
| SAFE | REVIEW | 3 |
| MISLEADING | REVIEW | 1 |

The 3–2 split first seen on SGLT2_HF is not a property of that page. It is the corpus.

---

## Why the editor rejects, in the editor's own words

145 desk-rejections read; a rejection may cite more than one reason.

| reason | count | share |
|---|---|---|
| unsound method | **118** | 81% |
| no advance | 56 | 39% |
| unreadable | 52 | 36% |
| unclear question | 9 | 6% |

**This is not a finding about writing.** Read the quotations and the same two sentences come
back page after page — and both of them are *ours*, and both are *true*:

> "No bibliographic search for primary trials was run"

> "No pooled estimate, risk-of-bias assessment or certainty rating is published for this
> question"

The first is the registry-first search method, disclosed. The second is the refusal to pool
where the evidence does not support pooling. The editor reads disclosure one as a fatal
methodological flaw and refusal two as an absence of contribution. By the conventions of
systematic reviews the editor is not wrong.

What separates the documents, in the editor's summary:

> "A is a coherent systematic review with defined eligibility, outcomes, and synthesis, while
> B is an incomplete audit record documenting why no defensible pooled clinical question
> exists."

> "B foregrounds method gaps and machine-rendered omissions rather than a reviewable
> manuscript."

**This is the "equal but different to Cochrane" question, answered with a measurement.** The
difference is priced, and the invoice is itemised. One line of it is addressable: the
registry-first search is measured at 97.3% recall (73 of 75, both misses development code
names), so the trials are being *found* — what is missing is the conventional bibliographic
arm that an editor requires to see. The other two lines are the method working as designed,
and the question is whether to defend them or change them. That is Mahmood's call, not a
defect to fix.

---

## What the student found that no gate of ours did

The student persona found a defect class our checks are structurally unable to see.

> "It says 'The trials agreed moderately (I-squared 31.4%)' even though later it says
> 'These 4 trials are not pooled.'"

An **agreement statistic in the abstract, describing a pool the page does not present.** On
FINERENONE the pool had been *withdrawn* on 2026-08-18; the withdrawal cleared the result rows
and refused the forest and funnel plots, and left this sentence standing — so the abstract
still reported the heterogeneity of an analysis the page had retracted.

Our gates could not find it because every one of them reads a claim against the object, and
on the object the I² genuinely *is* stored. The contradiction does not live between a sentence
and a field. It lives between two sentences.

**The panel named five pages. The population was 15 of 149. It is now 0 of 149.**

Getting to 15 took three measurements, and the two wrong ones were both wrong in the same
direction — mine, not the corpus's:

| measurement | count | what was wrong with it |
|---|---|---|
| first | 38 | matched any I² against any "not pooled" anywhere on the page. Most pages legitimately do both: pool outcome X and report its heterogeneity, decline to pool outcome Y and say so. |
| second | 25 | added the right discriminator — does the agreement claim carry a point estimate — but the pattern for "estimate" listed only ratio measures and required the interval to open on a digit. Every continuous outcome in this corpus reports a **mean difference** with a **negative** lower limit: `mean difference -5.69 (-7.3 to -4.08)`. Seven pages were reported as defective while their abstracts stated a pooled estimate in the same sentence. |
| third | **15** | both shapes added as negative controls, plus one exemption: an I² cited as the *reason* for withdrawing a pool is the statistic doing its job, not the defect. |

A reviewer flags whichever contradiction it happens to quote, so five was reviewer reach.
But an instrument that over-flags is not the safe direction either — it manufactures defect
classes, and this one manufactured two.

Fixed in `paper_projector.py` at the diagnosed layer: an I² is emitted only where a pooled
estimate is emitted, and where it is suppressed the abstract records a refusal naming why.
Re-measured on the rebuilt pages: **0 of 149**, with the detector's positive control still
firing, so the zero is a measurement rather than a broken instrument's silence.

---

## ARNI as an internal anchor — and the round-1 result does NOT replicate

Mahmood asked for ARNI to be run against the published comparators, on the reasoning that if
our best page scores like Zelniker, that is the achievable target for the manuscript layer.

**It does not score like Zelniker, and the round-1 finding that it did was noise.**

Round 1 put ARNI against one anchor, once per persona, in one position, each job going to one
family. The editor sent ARNI to REVIEW and desk-rejected Zelniker, and I reported that as
"an authored page in this house style can clear an editor". That was one draw.

Replicated properly — three published anchors, two personas, two families, **both orderings**,
24 jobs, all 24 returning:

| | ARNI | anchor |
|---|---|---|
| editor, vs Zelniker (*Lancet* 2019) | **DESK-REJECT 4/4** | REVIEW 4/4 |
| editor, vs Zannad (*Lancet* 2020) | DESK-REJECT 3/4 | REVIEW 3/4 |
| editor, vs Tromp (*JACC HF* 2021) | DESK-REJECT 3/4 | REVIEW 4/4 |
| student, all three | SAFE 7/12 | SAFE 4/12 |

Against Zelniker specifically the result is **the exact inverse of round 1**: 4 of 4
desk-rejections where round 1 recorded a review. Eleven of the twelve editor cells and every
student cell are **position-dependent** — the verdict changes with which slot ARNI occupies —
and five of six cells show the two families disagreeing, with Codex consistently harsher than
Gemini on this page.

So the honest answer to the question as posed: **the manuscript layer has no demonstrated
exemplar.** ARNI is desk-rejected like the rest of the corpus. That is a harder place to
start from than yesterday's reading, and it is where we actually are.

**What this does and does not undermine.** It does not undermine the corpus-wide rates. Round
2 re-read 41 page-role pairs with *both* families and they agree on 34 of them — 83 per cent
— with the seven disagreements running symmetrically in both directions (4 one way, 3 the
other) and no family systematically more lenient: student SAFE 72.7% for Codex against 65.0%
for Gemini, editor REVIEW 0% for both. Aggregate rates over 149 pages are sound.

What it undermines is **any single page's verdict**, which is one draw with roughly a 1-in-6
chance of flipping on family alone before position is considered. ARNI's round-1 REVIEW was
that draw. No individual page verdict in this record should be quoted without replication.

And the student's finding about ARNI stands independently of any of this, because it was
adjudicated against the object rather than voted on:

> "It confidently summarizes incomplete assessment as certainty: 'No risk-of-bias domain was
> rated high,' while the risk-of-bias tables assess only three trials in a four-trial
> synthesis."

Verified: `risk_of_bias.by_outcome` holds `paradigm-hf`, `parallel-hf`, `parachute-hf` —
three — and the conclusion reads "Across 4 randomised trials". The sentence now names its
denominator.

---

## The specialist and the editor are making the same complaint

Two clinical objections from the multipersona round are still open, still Mahmood's to
settle, and still unacted — correctly, because both challenge a design principle rather than
a defect. The panel has now produced evidence bearing on them, which is the reason to raise
them again rather than to decide them.

The heart-failure specialist, on SGLT2_HF:

> "'Two trials count an event class the other two do not'. **This is clinically false.** An
> 'urgent heart-failure visit' requiring intravenous therapy is functionally and clinically
> synonymous with an HF hospitalisation."

> "it excludes the landmark DELIVER trial … **This is a catastrophic omission.** Throwing out
> a pivotal 6,263-patient trial simply because its first-event two-component outcome is
> reported in the peer-reviewed publication rather than the registry artificially shrinks the
> evidence base."

The editor, on 118 of 145 desk-rejections, quoting our own disclosure:

> "No bibliographic search for primary trials was run"

**These are one complaint.** The specialist objects to the registry-first rule applied to an
*outcome definition*; the editor objects to it applied to the *search*. Both are saying the
same thing: the registry is being treated as the arbiter of what counts as evidence, and
clinical and editorial convention both treat the peer-reviewed literature that way instead.
The 97.3% recall measurement answers "does registry-first find the trials" — it does. Neither
of these objections is about recall.

What the panel adds is that the cost is now quantified. It is 2.0% versus 98.0% on full manuscripts, and the
disclosures being punished are true. Three things follow, and choosing between them is a
methodological decision, not a bug fix:

1. **Add a bibliographic arm** to the search and report it alongside the registry arm. This
   addresses the editor directly and is the only one of the three that is purely additive.
2. **Allow clinically-equivalent endpoint classes** to pool where a named clinical rationale
   is recorded — which is what the specialist is asking for, and what would readmit DELIVER.
   It weakens the endpoint-identity rule that currently prevents a class of silent errors.
3. **Defend both rules and accept the desk-rejection rate** as the price of a method that
   does not mislead a novice, which is the one thing this corpus measurably does better than
   the published comparator.

The student rate on full manuscripts — 76.0% against Zelniker's 54.4% — is the argument for (3). The editor rate
is the argument for (1) and (2). Nothing in the data chooses between them.
