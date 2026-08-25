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
against 54.4% — and one of fifty clears an editor.** That one is ARNI, the authored page.

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

## ARNI as an internal anchor

Mahmood's suggestion, and it earns its place: ARNI is the one authored manuscript in the
corpus, and it is the counter-example that stops the 2.0% review rate being read as a ceiling.
It is also the ONLY full manuscript of the fifty that an editor sent to review; the other
three REVIEW verdicts all went to notes of about 1,100-1,400 characters.

| | ARNI | Zelniker |
|---|---|---|
| editor | **REVIEW** | DESK-REJECT |
| student | MISLEADING | SAFE |

The editor preferred our authored page **over the published Lancet paper**, and desk-rejected
the latter:

> "I desk-reject for an unsound method because it presents opaque, naked numbers, asserting
> 'SGLT2i reduced major adverse cardiovascular events by 11%' without reporting heterogeneity
> or robustness checks."

> "Document A prioritizes rigorous data provenance and exposes its own fragility, whereas
> Document B conceals its internal variance behind a polished but unverifiable narrative."

**An authored page in this house style can clear an editor. The projected pages are not
failing because of the standard; they are failing because of what they have to disclose.**

And the student caught ARNI on something real, which is the whole reason to keep it:

> "It confidently summarizes incomplete assessment as certainty: 'No risk-of-bias domain was
> rated high,' while the risk-of-bias tables assess only three trials in a four-trial
> synthesis."

Verified on the object: `risk_of_bias.by_outcome` holds `paradigm-hf`, `parallel-hf`,
`parachute-hf` — three — and the conclusion reads "Across 4 randomised trials". The sentence
sits immediately before that conclusion, so a reader takes it as covering all four. It is the
same family as every other defect this week: **an absence stated as a clean result.** The
sentence now names its denominator and says the fourth trial was not assessed.

That is a fourth ARNI defect, found by a reader and not by us, on the page we hold up as the
standard.

---

## Denominators, stated

- 149 pages carry a Paper Studio panel; 14 pages in `PAGE_MAP` do not.
- 298 of 298 panel jobs returned. All 149 pages have both personas. No page unread.
- **99 of the 149 are notes under 3,000 characters, not manuscripts.** Corpus-wide rates mix
  the two; the manuscripts-only column is the comparable one.
- 0 jobs recorded a verdict without output. A job that produced nothing is recorded MISSING,
  never as a clean page.
- Rates above are final for this reading. They will move if the pages change.

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
