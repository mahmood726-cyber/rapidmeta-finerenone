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

---

## 9. Worked example against a KNOWN answer — the dapivirine ring

Added 2026-08-28 after Mahmood's ruling that prior published reviews supply the validation set
this protocol was missing. **This is the first accuracy measurement this project has ever had**
— our readers scored against a human expert panel rather than against each other.

### The reference standard, and its exact provenance

`agyw-hiv-prep-review` holds both ring trials: **NCT01539226** (The Ring Study / IPM 027) and
**NCT01617096** (ASPIRE / MTN-020).

The published assessment is Cochrane's, reported per domain in *A Review and Economic Analysis
of the Dapivirine Vaginal Ring as HIV Pre-Exposure Prophylaxis for Women, to Inform South
African Public-Sector Guidelines* (JAIDS 2024, PMC11458098,
[10.1097/QAI.0000000000003496](https://doi.org/10.1097/QAI.0000000000003496)), retrieved via
Europe PMC. According to that source, quoting the Cochrane review: *"Cochrane reviewers
assessed the 2 RCTs as low risk of bias"*, with every domain **low risk**.

⚠️ **Two provenance facts that must travel with every use of this comparison:**

1. **It is a secondary report of Cochrane's table, not the Cochrane review itself.** Under §6b's
   tier order a prior-meta table is already an unverified tier; a second review *citing* that
   table is one step further removed. **The primary read is still owed.**
2. ⛔ **Cochrane used RoB 1, not RoB 2.** The domains listed are random sequence generation,
   allocation concealment, blinding of participants and personnel, blinding of outcome
   assessment, incomplete outcome data, and selective reporting. **There is no exact mapping to
   RoB 2**, and the conventional approximate one is used here and labelled as approximate:

   | RoB 1 domain(s) | ≈ RoB 2 | exactness |
   |---|---|---|
   | random sequence generation + allocation concealment | D1 | close |
   | blinding of participants and personnel | D2 | **loose** — D2 is deviations *and* analysis, wider than blinding |
   | incomplete outcome data | D3 | close |
   | blinding of outcome assessment | D4 | close |
   | selective reporting | D5 | close |

### The comparison — 2 trials × 5 domains = 10 cells per reader

Both trials carry identical judgements from every party, so one row states both.

| ≈domain | Cochrane (RoB 1) | our reader 1 | our reader 2 | agree? |
|---|---|---|---|---|
| D1 | **low** | `NO_INFORMATION` | `SOME_CONCERNS` | ✗ ✗ |
| D2 | **low** | `NO_INFORMATION` | `NO_INFORMATION` | ✗ ✗ |
| D3 | **low** | `NO_INFORMATION` | `NO_INFORMATION` | ✗ ✗ |
| D4 | **low** | `LOW` | `LOW` | ✓ ✓ |
| D5 | **low** | `LOW` | `LOW` | ✓ ✓ |
| overall | **low** | `SOME_CONCERNS` | `SOME_CONCERNS` | ✗ ✗ |

**Agreement with the published panel: 4 of 10 domain cells for each reader (2 of 5 per trial).**
Reported as a raw fraction with its n, per §4 — 10 cells is not a rate.

### ⭐ What the disagreements are, and this is the finding

**Every single disagreement is a cell where our reader recorded `NO_INFORMATION` (or, for
reader 2 on D1, `SOME_CONCERNS` on partial registry evidence) and Cochrane recorded a verdict
from the papers.** Not one is a case of two parties reading the same evidence differently.

Split by whether the domain is answerable from what we actually hold:

| | cells | agreement with Cochrane |
|---|---|---|
| **D4, D5** — answerable from the registry we hold | 4 | **4 of 4 — 100%** |
| **D1, D2, D3** — need the paper, which we do not hold | 6 | **0 of 6 — 0%** |

⇒ **Our readers agree with a human expert panel on every domain where they had the evidence,
and on none where they did not.** That is the same document boundary as §0's step function,
arriving from a completely independent direction — a human reference standard instead of a
between-model comparison.

⇒ **It also settles what the 40.3% disagreement rate measures.** It is not reader quality. **The
readers are accurate where they can see and silent where they cannot**, and the silence is
correctly placed.

### What this worked example does NOT establish

- **n = 2 trials, one topic, and both trials received identical judgements from every party** —
  so this is effectively **one** independent comparison, not ten. It is a demonstration of the
  method, not an accuracy estimate.
- **It cannot distinguish "our reader was right to abstain" from "our reader would have been
  wrong had it answered."** Abstention is neither correct nor incorrect against a verdict; it
  is a different kind of output. **Scoring abstention as disagreement is generous to Cochrane
  and harsh to us, and that is the right direction for a self-assessment.**
- **A cross-tool comparison cannot be exact.** RoB 1 "low" on blinding of participants does not
  entail RoB 2 "Low" on D2, which also asks whether an appropriate analysis was used.
- **Cochrane could be wrong.** Where we later disagree *with the paper in hand*, that is a
  publishable position — **disagreeing with a stated reason is stronger than agreeing
  silently** — but nothing here is evidence of that yet, because we have not read the papers.

### What it changes in the protocol

**Add a fifth triage class, ahead of the adjudicator:**

> **E EXTERNAL_REFERENCE** — a published review has assessed this trial. Record its judgement,
> its tool, its provenance tier, and the mapping used. **Score our readers against it before
> any model adjudicates anything**, and where we differ *with evidence in hand*, publish the
> disagreement with its reason.

**And it re-orders the queue.** The re-ask (§8.1) is still first, but the retrieval it
implies is now cheaper than assumed: **for these two trials the papers are open**, and D1/D2/D3
are answerable from them today. **The binding constraint was never adjudication capacity — it
is six unread documents.**

### ⛔ On RoB 1, for the record

Switching to RoB 1 would let every unreachable domain be marked *unclear* and closed. **That
converts a retrieval failure into a methodological judgement and hides it.** Keep RoB 2, and
keep the honest fourth state — **`blocked — document needed`, naming the document.** A work
queue, not a dead end.

---

## 10. Family allocation — and why `agy`'s biggest limitation is what makes Stage 0 possible

Added 2026-08-28. Capacity: Claude direct 5% (resets in 17h), Codex 77% (resets 3 Sep), `agy`
carrying three families including **a separate Claude allocation**. That is the first time this
project has had three *properly pinnable* families at once, which is exactly what a
two-readers-plus-adjudicator design requires and has never cleanly had.

| role | worker | family |
|---|---|---|
| Reader A | Codex | openai |
| Reader B | `agy --model gemini-3.1-pro-high` | google |
| Adjudicator (class D only) | third family — `agy`'s Claude allocation | anthropic |
| Rulings only | Claude direct | — |

### ⭐ The limitation that is actually the enabling constraint

**`agy` works on indexed text and fails on fetch, and a denial returns nothing.**

Read as a capability gap that is a problem. Read against §1 it is the opposite: **a reader that
fetches its own evidence can never be shown to have parity with another reader.** Two readers
that each go and get their own material have no common bundle, no shared hash, and therefore no
adjudicable disagreement — *which is precisely how the 90.3%-abstention run happened.*

⇒ **A reader that must be HANDED its evidence is a reader whose evidence set is knowable.**
So Stage 0 stops being an aspiration and becomes mechanical:

1. Codex fetches and extracts — it is the only worker permitted to retrieve.
2. The bundle is frozen and hashed **once**.
3. **The same bytes** are handed inline to Reader A and Reader B.
4. The hash is recorded on both assessments.

**Evidence parity is not enforced by discipline; it is enforced by the fact that neither reader
can obtain anything else.** That is the strongest form of a gate this project has: not a check
that the rule was followed, but an arrangement in which breaking it is not possible.

### ⚠️ The pin is a measurement, not a setting

**`agy`'s default is gpt-oss — the same family as Codex.** An unpinned Reader B silently
collapses a cross-family design into a single family, and **every agreement rate computed from
it becomes meaningless while continuing to look exactly like a number.** Same shape as the
adjudicator that could only say "present", and as `login status` reporting a dead seat as live.

**Two requirements, and the second is the one that bites:**

- Pin explicitly: `--model gemini-3.1-pro-high`.
- ⛔ **Verify from the CLI log, never from a self-claim:**
  `grep 'Propagating selected model override to backend: label=' <log>`
  A model asked which model it is will answer confidently and may be wrong; the backend log is
  the record of what was actually routed.

**And record the family on every assessment as a stored field.** Then make the agreement
computation **refuse** when two readers share a family — a rate across one family is not an
inter-rater rate, and the refusal must name the two workers rather than silently averaging
them. **An unverifiable family is the same as a shared one: both are recorded as `UNKNOWN` and
both block the rate.**

### The pipeline, end to end

```
Codex          fetch + extract         -> evidence bundle, frozen, sha256 recorded
Codex          Reader A, cold + blind  -> signalling responses + evidence + family=openai
agy/gemini     Reader B, cold + blind  -> signalling responses + evidence + family=google
Stage 1        mechanical triage       -> A re-ask | B re-derive | C algorithm | D adjudicate
                                          E external reference, scored first
agy/claude     adjudicator, class D    -> criterion + bundle, NOT the two verdicts
Claude direct  rulings only            -> factual divergence; never a threshold split
```

**Claude direct never reads a trial.** Threshold splits are the algorithm's; class E is scored
against the published panel; only a *factual* divergence — two readers, same bundle, different
signalling responses — is worth a ruling.

⚠️ **Everything above is conditional on the re-ask.** Reader B currently returns verdict letters
and no signalling responses, so classes B, C and D are empty by construction and the pipeline
has no input. **The re-ask is not the first task in the queue; it is the precondition for the
queue existing.**

---

## 11. Cost, and the fallback allocation is the DEARER one

Added 2026-08-28. `agy` is a £20/month seat with unknown limits, so it is a **judgement
resource, not an extraction one**: Codex fetches, extracts, assembles the bundle and reads as
Reader A; `agy` is spent only where a second or third *family* is the point.

### Family assignment is a parameter, not a hardcode

```python
FAMILY_ASSIGNMENT = {
    "reader_a":    {"worker": "codex", "family": "openai"},
    "reader_b":    {"worker": "agy",   "family": "google",
                    "pin": "gemini-3.1-pro-high"},
    "adjudicator": {"worker": "agy",   "family": "anthropic"},
}
```

A limit then changes a setting rather than a design. **Two constraints on any assignment**, and
they are checks rather than conventions: no two roles may share a `family`, and a `family` that
cannot be verified from the CLI log is recorded `UNKNOWN` and **blocks the agreement rate** the
same way a shared family does.

### ⭐ The measured call counts — and they invert the fallback's premise

The fallback was proposed as *"one call per disagreement instead of one per domain"*. **Reading
is not billed per domain.** Reader B answers all five domains for a trial-outcome record in one
call, exactly as the current reader-2 prompt does. So the units are **per trial-outcome record**
for reading and **per disagreement** for adjudicating, and on this corpus the second is larger:

| | unit | total | per topic |
|---|---|---|---|
| **Allocation 1** — `agy` reads (Reader B) | trial-outcome record | 75 | **3.3** |
| **Allocation 2** — `agy` adjudicates only | disagreement | 133 | **5.8** |

**Ratio 1.77× — the "cheaper" fallback costs 77% more `agy` calls**, and it is dearer on
**12 of 23 topics**. Projected to the 155 stored topics at these means: **505 calls for
allocation 1 against 896 for allocation 2.**

⇒ **The crossover rule: adjudication-only is cheaper only where a topic has fewer disagreements
than trial-outcome records.** With a 40.3% disagreement rate over five domains, that is the
minority case. **If `agy` turns out to be tight, the answer is not to move it to adjudication —
it is to keep it reading and shrink the disagreement rate**, which the re-ask and the parity
gate do directly.

⚠️ **These are CALL counts, not token counts and not money.** `agy` has not been run for this
protocol, so no per-topic token cost has been measured and none is stated here. Calls are the
unit that is exactly derivable today; the token rate must be measured on the first real batch
and reported beside these numbers before any corpus-wide commitment.

### The stale artefact this measurement produced, and the provenance gap behind it

The first cost run read `adjudication_triage.json` left behind by a **scoped** run of one topic,
so it counted **6** disagreements instead of **133** and put allocation 2 at 0.3 calls per topic
— a 22× understatement, in the direction that would have made the fallback look free.

**The provenance sidecar reported that file `True`, unchanged and valid** — correctly, by its
own definition: the artefact matched its own hash and its inputs had not moved. **It recorded
how the artefact was produced and not what it was produced ABOUT.** The command's arguments are
part of its production, and they were not stored.

⇒ Fixed at the source: `provenance.py` now records `argv`. **Same shape as a page naming its
generator and not its object** — a provenance record that cannot distinguish two runs of the
same script over different populations is not yet provenance.

---

## 12. Closing the six blind cells — the regulators were not the route

Tested 2026-08-28 on the same two trials. **Answer: the regulatory documents answered ZERO of
the six, because no regulatory document was reachable at all. Three of six were closed by a
different route.**

### What was tried, named

| route | result |
|---|---|
| **FDA** | **not applicable** — the US application for the ring was withdrawn, so no FDA review exists |
| **EMA** EPAR page | `404` on the medicine slug |
| **EMA** site search | `403` — bot-blocked |
| **Europe PMC** OA full text, ASPIRE | `404` — `inPMC=Y` but **not in the open-access subset** |
| ⭐ **NCBI efetch**, same deposit | **`200`, 44,181 rendered characters** |
| **Europe PMC**, Ring Study | **not in PMC, not open access** — paywalled |

⚠️ **`inPMC=Y` is not `isOpenAccess=Y` is not "machine-retrievable".** Europe PMC's OA endpoint
refused the ASPIRE deposit; NCBI's `efetch` served the same record. **Two indexes over one
deposit disagreed about whether it exists, and the pessimistic one was wrong.** A retrieval
that stops at the first index reports a paywall that is not there.

### What the accessible paper answers — ASPIRE, `NCT01617096`

| signalling question | in the manuscript? |
|---|---|
| 1.1 sequence generation | **yes** — *"assigned in a 1:1 ratio, with the use of fixed-size block randomization, stratified according to site"* |
| 1.2 allocation concealment | **no** — not reported |
| 2.1 blinding of participants | **yes** — *"phase 3, randomized, double-blind, placebo-controlled"* |
| 2.6 appropriate analysis | **yes** — *"performed according to the intention-to-treat principle"* |
| 3.1 data for all randomised | **yes** — discontinuation and follow-up reported |

**4 of 5.** The one gap is **allocation concealment, and that is a finding about the trial, not
about our retrieval** — a great many trials never report it. It is the honest `NO_INFORMATION`
that RoB 2 signalling responses exist to carry.

### The six cells, resolved

| trial | D1 | D2 | D3 | |
|---|---|---|---|---|
| **ASPIRE** `NCT01617096` | now answerable | now answerable | now answerable | **3 of 3 closed** |
| **Ring Study** `NCT01539226` | blocked | blocked | blocked | **0 of 3** — paywalled |

**3 of 6.** Not by a regulator, and not by a Cochrane table — **by an NIH author-manuscript
deposit, reached only after the first index said it was not there.**

⚠️ **"Answerable" is not "answered".** This establishes that the document contains the material.
It does not assign a domain judgement — that is a reading task for Reader A and Reader B on the
frozen bundle, and it is now unblocked for one trial of two.

⇒ **And the split is itself the finding: the funder decides the retrieval.** ASPIRE was
NIH-funded and therefore deposited; the Ring Study was industry-funded and is not. **Our blind
cells are not distributed by domain or by difficulty — they are distributed by who paid for the
trial.** That is worth measuring corpus-wide before any retrieval programme is scoped, because
it predicts which gaps will close and which will not.

---

## 13. Funder versus retrievability, corpus-wide — the hypothesis is REFUTED

353 of 353 trials with a lead-sponsor class probed on **both** retrieval routes.

| funder | n | inPMC | isOA | **reachable** | efetch-ONLY |
|---|---|---|---|---|---|
| INDUSTRY | 214 | 205 | 198 | **205 — 96%** | 22 |
| OTHER | 121 | 97 | 92 | **97 — 80%** | 18 |
| NIH | 7 | 6 | 6 | 6 — 86% | 2 |
| FED | 5 | 5 | 5 | 5 — 100% | 1 |
| OTHER_GOV | 4 | 2 | 2 | 2 — 50% | 0 |
| NETWORK | 2 | 2 | 2 | 2 — 100% | 0 |
| **ALL** | **353** | — | 305 | **317 — 90%** | **43** |

**Industry-funded trials are MORE reachable, not less — 96% against 80%, a ratio of 1.19 in the
opposite direction to the prediction.** The eight trials with no local registration record are
excluded from every row and counted as their own kind.

⇒ **The dapivirine pair does not generalise.** ASPIRE-deposited / Ring-Study-paywalled was a
real observation about two trials and a **false inference about a population**. Two cases, one
per arm, produced a story with a mechanism and a policy implication, and the corpus says the
effect runs the other way.

### ⚠️ What "reachable" means here, and why the refutation is narrower than it looks

This probe asks: **does Europe PMC's NCT search return ANY linked paper whose full text one of
the two routes will serve?** That is **not** "is the primary report retrievable", which is the
question the dapivirine case actually turned on.

**Industry trials attract many secondary papers** — post-hoc analyses, pooled safety, economic
models — and any one of them satisfies this criterion while the primary report stays behind a
paywall. So this measurement refutes the hypothesis **as I operationalised it** and leaves the
sharper version open: *is the PRIMARY report reachable, by funder?* That needs an
NCT-to-primary-publication link this corpus does not yet hold for most trials.

**Stated plainly: a 96% reachability figure must not be quoted as 96% of trials being
assessable.** Reachable means a document arrived. Whether it answers D1, D2 and D3 is the
separate question §12 measured on one trial and found to be 4 of 5.

### ⭐ The finding that survives, and it runs in our favour

**43 of the 317 reachable trials — 14% — are reachable ONLY via NCBI `efetch`.** Europe PMC
alone would have recorded every one of them as unavailable.

⇒ **A single-index retrieval understates our reach by an eighth.** Every "abstract only" and
"no full text" record in this corpus that was decided on one index is suspect and should be
re-tested. **`inPMC`, `isOpenAccess` and machine-retrievable are three properties**, and the
route that succeeded is now recorded per trial rather than collapsed into one flag.
