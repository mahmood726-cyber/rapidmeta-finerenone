# Blinded-AI adjudication protocol for RoB 2 domain judgements

**Status: design + worked example. NOT run corpus-wide.** Written 2026-08-28 against the
corpus at `806c8666f`.

---

## 0. Why the obvious design failed, with the mechanism

A third model was shown two readers' verdicts and asked to settle them. It abstained on
**90.3%** of cells; stripping cells where any reader abstained left **31 of 360**. That was
read as the adjudicator's disposition.

**It was not a disposition. The two readers had not been shown the same evidence.**

Reader 1 (Claude) read the store, which holds paper-derived fields. Reader 2 (Codex) was sent
a **14-field allow-list of registry facts** — by design, to keep the second read blind. So the
two readers were answering different questions, and no adjudicator can settle that.

The evidence is a step function, not a gradient:

| domain | what the 14-field allow-list can answer | reader 2 `NO_INFORMATION` |
|---|---|---|
| D1 | partly — no allocation-concealment field | 77 of 81 — **95.1%** |
| D2 | **no** — needs the paper | 81 of 81 — **100.0%** |
| D3 | **no** — needs the paper | 81 of 81 — **100.0%** |
| D4 | yes — registered masking | 1 of 81 — **1.2%** |
| D5 | yes — registered outcomes | 7 of 81 — **8.6%** |

A model's disposition produces a graded pattern. **100 / 100 / 95 against 1 / 9 is the shape
of a document boundary**, and it maps exactly onto what those fourteen fields contain.

⇒ **Reader 2's abstentions measure the prompt, not the trials.** The corpus-wide 40.3%
disagreement rate is therefore dominated by an evidence asymmetry between readers. Adjudicating
those cells adjudicates our retrieval.

---

## 1. Stage 0 — the evidence-parity gate

**A cell is adjudicable only if both readers were shown the same evidence.**

Every assessment must record an **evidence bundle hash**: the sha256 of the exact material the
reader was given. Two readers with different hashes have not disagreed; they have answered
different questions.

Cells failing parity are **not "unadjudicated"** — they are **not yet assessable**, and each
emits a task naming what was missing. That is the requirement that converts our largest
weakness into a work queue rather than a shrug.

⚠️ **Today, zero cells pass this gate**, because no bundle hash has ever been recorded. That is
the honest starting position and it is why the protocol's first output is a re-ask queue, not
an adjudication queue.

---

## 2. Stage 1 — triage without a model

RoB 2 **already fixes** the mapping from signalling responses to a domain judgement. So a
disagreement about *where the line sits* is not a matter of opinion to arbitrate — the
published algorithm decides it. Only a disagreement about *the responses* means someone read
the source differently.

| class | condition | who resolves it |
|---|---|---|
| **A NO_SIGNALLING** | a reader recorded no signalling responses at all | **re-ask** — a data-collection defect |
| **B DERIVATION_MISMATCH** | a reader's stored verdict does not follow from that reader's own responses | **re-derivation** — no second opinion needed |
| **C THRESHOLD** | responses identical, verdicts differ | **the algorithm** — no model |
| **D FACTUAL** | responses differ | **the adjudicator** — this is the only class it should see |

`scripts/lane_rob/adjudication_triage.py` implements Stage 1. Corpus-wide today:

```
paired domain cells      330  == the denominator
   AGREE                 197    59.7%
   DISAGREE              133    40.3%

   B_DERIVATION_MISMATCH   0     0.0% of disagreements
   A_NO_SIGNALLING       133   100.0% of disagreements
   C_THRESHOLD             0     0.0% of disagreements
   D_FACTUAL               0     0.0% of disagreements

CELLS AN ADJUDICATOR SHOULD SEE TODAY     0
cells needing a RE-ASK, not a judge     133
```

**Every disagreement in the corpus is class A.** Reader 2 returned verdict letters and no
signalling responses, so nothing can currently be triaged as factual or threshold. **The
adjudication queue is empty and the re-ask queue is 133.**

### 2b. What Stage 1 found on its own, with no adjudicator

Of **435** domain cells that carry reader-1 signalling responses, **21** have a stored verdict
that does not follow from those responses under the published tables:

| domain | stored | algorithm proposes | n |
|---|---|---|---|
| D2 | `NO_INFORMATION` | **HIGH** | 9 |
| D2 | `SOME_CONCERNS` | **HIGH** | 6 |
| D1 | `NO_INFORMATION` | SOME_CONCERNS | 3 |
| D2 | `NO_INFORMATION` | SOME_CONCERNS | 3 |

**Every divergence runs toward MORE risk.** Our readers were more lenient than the tool — the
opposite direction to this project's measured bias toward accusing its own pages, and worth
recording as a counterexample to it.

The mechanism, hand-traced on `NCT00643188` D2: all three responses are `NO_INFORMATION`;
Table 6 Part 1 row 3 gives *Some concerns*, Part 2 row 3 (`2.6 = N/PN/NI, 2.7 = Y/PY/NI`) gives
*High*, and the domain takes the more severe. ⇒ **RoB 2 is not neutral about ignorance in D2:
not knowing whether an appropriate analysis was used *is* High risk.** Recording
`NO_INFORMATION` as the domain judgement is not caution — it is a verdict the tool does not
offer, standing in place of one it does.

---

## 3. Stage 2 — the adjudicator, for class D only

**Give it the criterion, not the two verdicts.** An adjudicator shown two answers optimises for
agreement, and agreement is not correctness.

**Order of operations, and the order is the design:**

1. It receives the **signalling questions**, the **RoB 2 criterion text**, and the **evidence
   bundle** — the same bundle both readers saw, by hash.
2. It answers **each signalling question**, and for each it **names the source that settles
   it** with a locator: publication + section, protocol + page, SAP, registry history +
   version, regulatory review. ⇒ **A judgement that cannot name its source is not a
   judgement.**
3. The domain judgement is then **derived by the algorithm** from its own responses — not
   asserted. The adjudicator never picks a verdict directly.
4. **Only then** is it shown the two readers' responses, and asked one question: *does either
   identify evidence you did not use?* A changed answer must say which evidence changed it.

**Abstention is refused unless it names the missing document.** "No information" is a
signalling-question response, never a domain or overall judgement — those are Low, Some
concerns, or High. An abstention must state **which document would resolve it**, so the output
is a retrieval task with an identifier on it.

**Threshold splits are not arbitrated.** Where the responses agree and the verdicts differ, the
adjudicator does not pick a side — Stage 1 already applied the algorithm. Reporting both rates
separately is mandatory: **a factual disagreement means someone is wrong; a threshold
disagreement means the tool was not applied.**

---

## 4. Stage 3 — the output record

Every adjudicated domain judgement carries, without exception:

```json
{
  "judgement": "HIGH",
  "derived_by": "rob2_algorithm.py :: d2 :: Table 6 Part 2 row 3",
  "signalling_responses": {"2.1": "Y/PY", "2.6": "NI", "2.7": "NI"},
  "source_per_response": {"2.6": "NCT01975376 Prot_000.pdf p.88 §9.2"},
  "evidence_bundle_sha256": "…",
  "subject_ref": "…",
  "adjudicator": "model + version",
  "shown_reader_answers_after": true,
  "changed_after_seeing_readers": false
}
```

`subject_ref` stamps **what was judged**, not merely that a judgement happened — the gates lane
found **130 of 242** checkable self-descriptions stale, and a judgement without a subject
reference joins them.

---

## 5. Validation — on known answers, never on agreement

**Do not measure agreement between two models and call it accuracy.** Agreement authenticates
nothing, and adjudication fires only on disagreement, so agreement is not even the right
denominator.

Three sources of known answers, in decreasing strength:

1. **Trials whose protocol we hold.** `NCT01975376` (SPIRE-1, 168pp) and `NCT01975389`
   (SPIRE-2, 167pp) are staged in this repo. D5 and D2 are answerable from them *by reading*,
   so an adjudicator's answer can be scored against the document rather than against a model.
2. **Registry-documented facts** — masking, registered outcomes, arm counts. Externally
   established, and the answer is not ours.
3. **Planted cases** — a fabricated bundle with a response set whose table row is known.
   Per house rule, **plant both ways**: a bundle that must yield High and one that must yield
   Low, and watch each fail before trusting either.

⚠️ Per §9g: **a hand-read must restate the criterion in its own words before looking at the
case.** If the restatement differs from the protocol's, that is a finding before any case is
read.

---

## 6. Worked example — `ablation-af-heart-failure`

Two trials (`NCT00643188` CASTLE-AF, `NCT01420393` RAFT-AF), one outcome, five domains, ten
paired cells.

```
paired domain cells    10  == the denominator
   AGREE                4    40.0%
   DISAGREE             6    60.0%

   A_NO_SIGNALLING      6   100.0% of disagreements
   B / C / D            0

reader-1 self-consistency: 2 cells where the stored verdict
does not follow from the reader's own responses
   NCT00643188 D2  stored NO_INFORMATION  ->  algorithm HIGH
   NCT01420393 D2  stored NO_INFORMATION  ->  algorithm HIGH

CELLS AN ADJUDICATOR SHOULD SEE TODAY   0
cells needing a RE-ASK, not a judge     6
```

**What the protocol does with this topic, in order:**

- **Stage 0** refuses all ten cells: no evidence-bundle hash exists, so parity cannot be shown.
- **Stage 1** resolves **2 cells with no model at all** — both D2 verdicts are re-derived to
  `HIGH` from the readers' own answers, with the table row cited.
- **6 cells emit a re-ask**, not an adjudication, each naming what reader 2 was never sent.
- **0 cells reach the adjudicator.**

⇒ On this topic the protocol's whole yield is achieved **before any model is called**, and the
remainder is a retrieval and re-ask queue. That is the correct result, and it is what the
90.3%-abstention run was actually telling us.

---

## 7. What this protocol still cannot decide

Stated plainly, because an unstated limit becomes a claim.

1. **It cannot supply evidence.** Where neither reader saw the document, the protocol produces
   a retrieval task and stops. Of ten D5 gaps examined this week, **zero** were closable from
   the registry — protocols simply are not posted for those nine trials.
2. **It cannot validate reader 2's judgement at all** until reader 2 returns signalling
   responses. Every current disagreement is class A. **The re-ask is a precondition, not a
   parallel task.**
3. **It cannot tell a threshold split from a factual one on today's data** — that separation
   needs both readers' responses, and only one reader has them.
4. **The algorithm's proposals are inputs to a person, not outputs to a reader.** The tool
   itself says users should verify and change proposed judgements. Stage 1 raises a candidate;
   it does not silently rewrite a stored verdict.
5. **`NO_INFORMATION` cells that are genuinely underivable stay underivable.** Table 10 defines
   no row for `3.2 = NI`; **15 cells** hit that. Those are a data gap, and the protocol reports
   them as one rather than inventing a row.
6. **214 of the paired cells have no reader-1 signalling responses either**, so Stage 1's
   mechanical resolution reaches only the ~101 cells that do. **Its reach is not its coverage.**

---

## 8. What to do first

**Not the adjudicator.** In order:

1. **Re-ask reader 2 for signalling responses**, on the same evidence bundle as reader 1, with
   the bundle hash recorded on both. Without this, classes B, C and D are all empty by
   construction.
2. **Land the 21 re-derivations** as candidates for a human read — 15 of them raise a domain to
   `HIGH`, which changes GRADE, so they are third-party-facing and get a human read per
   standing orders §0.
3. **Then**, and only then, run Stage 2 on whatever lands in class D.
