# The page standard, versioned

**`PAGE_STANDARD_VERSION = "1.6.0-2026-08-19"`**

Until tonight this standard existed only as practice and as one exemplary object
(`arni-hfref`). It had **no version marker anywhere in the repo** — `grep` for `build_stamp`
or `standard_version` across every object returns nothing, ARNI included. That is the gap
this file closes, and it closes it in the direction the ratchet requires: a page records the
standard version it was built to, so a page built to v1 while the standard is v3 is
**honestly labelled rather than silently stale**.

**No page is grandfathered, `arni-hfref` included.** ARNI is presently unstamped and is
therefore *unknown-version*, not *compliant*. That is a fact about the register, not a
criticism of the page.

---

## The properties

A page meets the standard when **every property below is either HELD or REFUSING WITH A
STATED REASON ON THE PAGE**. A refusal is a complete outcome. A blank is not.

| # | property | held means |
|---|---|---|
| P1 | **Executed search** | query string verbatim, date, records returned, per database; PRISMA counts that reconcile arithmetically |
| P2 | **k cascade** | k reported at every stage, never as a single number |
| P3 | **Inclusion criteria** | a criteria block carrying `predefined:` on its face |
| P4 | **Preconditions** | every precondition with its verdict and its cited authority |
| P5 | **Extraction table** | verbatim source sentence per cell, resolvable link, and each cell labelled READ or DERIVED |
| P6 | **Analysis output verbatim** | the model call, estimate with CI, heterogeneity and package version, quoted. **If there is no quotable output, the absence is recorded as a finding** |
| P7 | **Published-meta comparison** | with a denominator, present in BOTH the page and the Word manuscript, charts aligned |
| P8 | **Registration identity** | every trial keyed to a registration id verified against the registry |
| P9 | **Build stamp** | naming this standard version |
| P10 | **Served-bytes verification** | the property is confirmed in bytes served over HTTP, not in a source file and not by an exit code — **and not by a hash alone**. `md5(served) == md5(disk)` proves the wire agrees with the disk and says nothing about whether the disk agrees with the object, because **a stale file matches its own disk copy perfectly**. A content check must accompany it, with its expected strings PROJECTED FROM THE OBJECT rather than typed into the verifier |
| P11 | **Coded field governs** | where the object holds BOTH a coded field and a free-text label for the same thing, the verdict is taken from the CODE; the text only corroborates. Where the code is absent and the verdict falls back to text, **the verdict says so on its face** |
| P12 | **The known-answer suite ran** | the suite executed and passed in this build. An import error is a BUILD FAILURE, not a skipped test |
| P13 | **Keyed by entity, never by module constant** | a function that accepts an identifier must REFUSE when it holds no record keyed to it. Per-entity data is keyed by entity; it is never reached for from whichever constant is in scope |
| P14 | **No substring matching over clinical text** | identity is decided by a declared, enumerated term set or a coded field. Registry text carries parenthetical abbreviations — `Cardiovascular (CV) Death` — so substring containment is a KNOWN-BROKEN method, not a shortcut |
| P15 | **A short-circuiting check reports all failing limbs** | a check that returns on first failure must report EVERY limb that fails, or state that the named limb is merely the first tested. A single reason drawn from an ordered sequence of tests is a fact about the sequence |
| P16 | **A guard is proven in three parts, and the case it guards against must have OCCURRED** | it **must be able to fire**; it **must not fire on the correct case**; and **neither can be established by the build reporting success**. All three are demonstrated, not assumed. **Added 1.6.0:** the triggering condition must have actually arisen in data the guard has run on — a guard whose condition has never occurred is *unproven, however green it reads*, and "it would have caught it" is a claim about an event that never happened |
| P17 | **Negative claims are computed, never asserted** | any field whose name implies a check — `shared_with_other_topics`, `conflicts`, `unresolved`, `discrepancies` — carries a computed value and names what it was computed against. A literal `false` or `[]` in such a field is a claim, not a result |
| P18 | **A restated quantity is reproducible by a command** | a number that has been corrected carries the COMMAND that re-derives it, and a gate that refuses the object when it stops reconciling. A `restated_*` note is a claim about a MOMENT and ages silently — its presence shows someone once looked, never that anyone looked last |
| P19 | **A promotion reaches every derived block, or it is not applied** | when k, the included set, or the headline estimate changes, every quantity DERIVED from them moves in the same pass — prediction interval, estimator sensitivity, PRISMA flow, cascade `k_included`, and the published-meta comparison. A page carrying two answers is worse than a page carrying the old one |
| P20 | **The cascade reconciles with itself** | `k2_role_located == k3 + k4 + k5`, and `k0 == k3 + k4 + k5 + kNA (+ kUNREACHABLE)`. A stage that does not reconcile with the stages beside it is a number the reader it was written for cannot check |
| P21 | **An ambiguous question is built as several reviews, never chosen between** | where a topic's question admits more than one legitimate reading, **each reading becomes its own review** with its own question, criteria, search, cascade and screening. Choosing one is a decision to withhold evidence from every reading that loses, and it leaves no trace in any object |
| P22 | **Deliberate trial sharing is recorded on both sides** | a trial legitimately appearing in more than one topic carries, on each object, **which other topics hold it and why**. Sharing is legitimate; unrecorded sharing is not. Every page that shares states that **a corpus-level k obtained by summing per-topic k double-counts** |
| P23 | **Recall is measured against the review's own included set** | every executed search reports how many of the trials this review includes it actually surfaced. A **design filter** (phase, status, study type) is a recall hazard: `NA` is not a phase, and enumerating phases drops every registrant who declared none. A query that misses is **recorded, not replaced** |
| P24 | **Every disposition in a taxonomy is demonstrably reachable** | each state a screen can assign must be reached by at least one real instance in the run, or be reported as **reached zero times and why**. *A disposition that cannot be reached is not a conservative default* — it looks cautious, so a zero there invites no suspicion at all |

## Reading the remainder — the same number, opposite diagnoses

**Added 2026-08-19, from screening three topics' remainders to zero.** A `k_unscreened_remainder`
is not just a backlog count. Once screened, **the shape of its dispositions diagnoses the
search**, and two topics with identical remainders can mean opposite things:

| remainder dominated by | diagnosis | what to do |
|---|---|---|
| **POPULATION failures** | the surfacing query is **too broad** — it is reaching outside the review's own population | narrow the query; the cost is reviewer time spent excluding trials that were never candidates |
| **ESTIMAND failures** (eligible, not poolable) | the query is well-aimed and the **evidence base is genuinely fragmented** | nothing to fix in the search; the limit is real and belongs in the interpretation |
| **NOT-YET-REPORTED** | the query is well-aimed and the **field is still in flight** | name the largest pending trials — they are what will change the answer |
| **COMPARATOR failures — few trials declare a control arm at all** | the query is well-aimed and **the field has produced few controlled trials**. This is a fact about the literature, not about us | say so plainly; the limit is the evidence that exists, and no better query recovers it |

Observed, on the same night, on two topics with the same criteria discipline:

- `iv-iron-hf` — 29 screened, **16 of 29 ELIGIBLE**. Only 13 failed a criterion. The base is
  limited by estimand match and by trials that have not reported.
- `sglt2-hf` — 10 screened, **7 excluded, six of those on POPULATION**: acute myocardial
  infarction, heart transplant, diabetic nephropathy, congenital heart disease, acute
  decompensation. The surfacing query reaches well beyond its own population.
- `attr-cm-review` — 46 screened, 31 excluded, and **only 6 of the 46 declare a placebo arm at
  all**. A drug programme dominated by open-label extension and single-arm studies. No better
  query recovers randomised evidence that was never generated.

**"Few controlled trials exist" is a different finding from "our query was too broad", and a
reader must be able to tell them apart.** Both produce a large excluded count; only one is a
criticism of the search.

> **This is a fact about our search, not about the evidence — and it was invisible while the
> remainder was carried as a number rather than screened.** A remainder is not a queue to be
> drained; it is unread evidence *about the query that produced it*.

**Therefore P1 is not fully held by a search that merely reconciles.** Where a remainder has
been screened, the disposition split belongs on the page beside the count, because
`remainder: 29` and `remainder: 10` tell a reader nothing about which of the three situations
above they are in.

## The ratchet

Each topic must meet everything learned **up to the moment it is built**. The version string
is what makes staleness visible instead of silent. When a lesson is added, the version rises
and every page below it is *known* to be below it.

## What a refusal must carry

A refusing property states **which** property, **why**, and **what would change it**. "Not
applicable" is not a reason; "k=1, so there is no between-study variance to estimate" is.

Nothing is generated to fill a slot. A tab with nothing to render keeps refusing.

---

## Version log

### 1.7.0-2026-08-19
Adds P24, and records two method lessons from the screen that produced it.

**P24 — every disposition must be demonstrably reachable.** The 621-trial screen of
`ablation-af-medical-therapy` returned `ELIGIBLE_NOT_POOLABLE: 0`. That was not a finding about
the evidence base; the branch **could not be reached**. `ctgov_transport.fetch_raw` defaults to
`fields="protocolSection"`, so `hasResults` is absent from every cached record and
`not doc.get("hasResults")` was always true — every eligible trial routed to "no results yet",
including trials that had posted results and could have been assessed.

> **A disposition that cannot be reached is not a conservative default.** That is why it hides:
> the branch looks cautious, so a zero sitting in it invites no suspicion at all. A wrong
> *large* number gets argued with. A wrong *zero* in a careful-looking cell gets read as
> diligence.

**The tell was the zeroes, not the big number.** The same run reported `EXCLUDED: 556` and
`NEEDS_ADJUDICATION: 0`, and 135 of those exclusions were wrong. What broke through was not the
implausible 556 — it was **two implausible zeros sitting beside it**. A count that *should
sometimes be non-zero and never is* says more than a count that is merely surprising, because
the first is a statement about the instrument and the second only about the data.

**A known-answer file must not smuggle in knowledge from outside the instrument's inputs.**
The screener was told RAFT-AF must clear the intervention limb, because RAFT-AF *is*
ablation-based — its TITLE says so. Its `armGroups` do not; they declare `Procedure: Rhythm
control`. **The instrument was right and the expectation was contaminated by knowing the
answer.** Second occurrence here: the placebo-naming file expected ADVANCE-3 to behave like
ADVANCE-2 and the registry disagreed. An expected answer must be derivable from the same fields
the rule reads, or it tests the author rather than the code.

**And a hand-written vocabulary cannot be complete.** `Device: Catheter Ablation` vs
`Drug: Drug Treatment` was excluded on the comparator limb because the term list held "drug
therapy" and not "drug treatment". Every gap in such a list failed toward EXCLUSION — the
withholding direction, in the most banal possible mechanism. Where a coded field exists
(`Drug:` / `Procedure:` / `Device:` intervention types), it governs; and where the vocabulary
simply cannot say, the verdict is **UNSETTLED, never "not found"**.

### 1.6.0-2026-08-19
Extends P16 with its missing fourth clause, and adds P23. Both come from **a guard that was
green because the case it existed for had never happened.**

**P16, fourth clause — the guarded case must have OCCURRED.** The pagination guard reads
`returned == totalCount` to confirm a fetch was not truncated at a page boundary. It read
`totalCount` from the **last** page, where the API returns null; `countTotal` populates it on
the **first**. Every query this project had ever run fit in a single page, so the last page
*was* the first, and the defect could not appear. It shipped that morning inside
`regate_cascade_2026_08_19.py` and was exercised, correctly, on five topics — proving nothing.
It surfaced within hours on the first two-page query ever run here.

> **A guard whose triggering condition has never occurred in the data it has run on is
> unproven, however green it reads.** Three parts were satisfied — it could fire, it was silent
> on the correct case, and the build's success was not the evidence. What was missing is that
> the *world* had never presented the case. "It would have caught it" is a claim about an event
> that never happened.

This generalises well past pagination. Any guard written for a rare condition — a truncated
fetch, an empty result set, a missing baseline, a second page, a duplicate id — is untested
until that condition is *present in a run*, and a synthetic input is the weaker substitute the
known-answer rule already warns about.

**And the direction is why it was recoverable.** It printed `returned==totalCount: False` on a
complete fetch — a false ALARM, on a screen someone was reading.

> **A guard that fails loud is recoverable. A guard that fails quiet is the class this project
> has spent two nights on.** When choosing how a check behaves under its own failure, choose
> the noisy wrong answer over the silent one.

**P23 — a design filter is a recall hazard, and its cost is measured, not assumed.** Four
distinct shapes of one defect are now on record, all in the withholding direction:

| topic | lost | to |
|---|---|---|
| `sglt2-hf` | DELIVER | a CONDITION term one word too narrow |
| `iv-iron-hf` | AFFIRM-AHF, HEART-FID | a CONDITION term one word too narrow |
| `apixaban-vte` | NCT02366871 | `phase=[PHASE3,PHASE4]` on a PHASE2 trial |
| `ablation-af-medical-therapy` | **CABANA (n=2204), RAFT-AF** | the same filter on trials registered `phases: ["NA"]` |

**NA is not a phase.** A filter that *enumerates* phases silently drops every registrant who
declined to declare one — and on the ablation topic that was two of the three pivotal trials,
including the largest. Recall against the review's own included set is therefore **measured for
every executed search**, and a query that misses is **recorded rather than replaced**.

### 1.5.0-2026-08-19
Adds P21 and P22, from Mahmood's decision on `ablation-af-review` — **and the decision was
better than any of the three options the packet offered.**

**P21 — an ambiguous question is built as several reviews.** The packet framed the ablation
question as a choice between three restatements, and tabulated each by *which trials it drops*:
A drops EAST, B drops none but makes the topic name wrong, C drops CABANA and EAST. Every row of
that table is a count of evidence discarded.

> **The packet was well-built and it framed the problem the wrong way round.** All three
> questions are legitimate, and each trial genuinely belongs to at least one of them. There was
> no good answer because the question "which do we keep" had no good answer — **choosing is a
> decision to withhold, and nothing in this guard set catches it.** Three reviews discard
> nothing and give each question its honest answer.

This is why it is a property and not a note on one topic: the same shape is already queued.
`apixaban-vte` was blocked on TREATMENT versus PREVENTION over pools of 34 and 33 — **two
legitimate questions with nearly equal evidence, where choosing discards one for no reason but
tidiness.** Both are now to be built. `bococizumab-lipid` gets the same treatment if its
truncation resolves into more than one real question, and a packet only if the question cannot
be recovered from source at all.

The rule does **not** license inventing readings. A reading qualifies when it traces to named
registry fields of trials the corpus already holds, exactly as the three ablation candidates
did.

**P22 — deliberate sharing is recorded on both sides.** Splitting one topic into several makes
cross-topic trial sharing intentional rather than accidental: CASTLE-AF and RAFT-AF will each
appear in all three ablation reviews by design. Roughly a fifth of the corpus's registration
identities are already shared across topics, so the rule was already needed and is now
unavoidable. **Sharing is legitimate; unrecorded sharing is not**, and any corpus-level count
computed by summing per-topic k double-counts — which every sharing page must say on its face.

### 1.4.0-2026-08-19
Adds P18, P19, P20 and strengthens P10. All four come from **re-gating five topics that were
already complete**, and every one of them was invisible on a page that read as finished.

**P18 — a restated quantity is reproducible by a command.** `sglt2-hf`'s stored cascade
reproduces at exactly one classifier revision (`f2bf16022`) and at no other. Two later commits
shipped the same night and were never carried back. **What made the page look current is that
it carried a correction note** — a `restated_2026_08_19_placebo_discriminator` block naming its
own 36 → 46 delta, dated the same day as the commits that superseded it. The same PRISMA
sentence has now said 43, then 36, then 46, then 49; each was true when written. A fifth
correct number is not the fix. The fix is that the number is produced by a command and refused
by a gate.

**P19 — a promotion reaches every derived block.** `alirocumab-lipid` was restated from k=6 to
k=8 in its headline and results. Left at k=6: `prisma_flow.included`, `k_cascade.k_included_in_object`,
the whole published-meta comparison including a field named `ours`, the estimator-sensitivity
table, and **the prediction interval — whose own text calls it "the number to quote"**. One
page, two answers, and the superseded one in the table a reader consults to compare us against
the literature.

**P20 — the cascade reconciles with itself.** Three of five objects stored `k0` in
`k2_role_located`, so **the stage named "role located" counted the records whose role could not
be located** and `kNA` was added twice. It is invisible on the two objects whose `kNA` is 0 —
*a sum that is right whenever the thing it omits is zero has not been tested.*

**P10 strengthened.** The served-bytes verifier's first run returned `md5 served == disk: OK`
on a page that was stale, because that topic's pooled estimates had not changed and only its
cascade sentence had. A hash cannot detect staleness; only content projected from the object
can.

Two further lessons from the same night, recorded here because they are about instruments
rather than pages:

- **A round trip through a parser is not a copy.** A reproduction gate failed because SEs were
  re-derived from per-trial CIs rounded to 2 dp for display; a guard-proof restored a planted
  object by re-serialising a parsed copy and left the tree in a state neither the builder nor
  git had produced. Where the original bytes exist, restore those.
- **A lint that counts its own documentation as a violation taxes writing the rule down.**
  `lint_subprocess_decode.py` read a comment saying `text=True` as a hazard site; two of its
  eighteen baselined entries were prose describing the rule.

### 1.3.0-2026-08-19
Adds P15, P16, P17 — all three from defects that produced *correct-looking output*.

**P15 — short-circuit attribution.** bempedoic's screen reported 13 of 16 trials failing on
the OUTCOME limb. Restated on two axes, only **2** are genuinely eligible-but-unpoolable; the
rest fail population or comparator anyway. The screener checked outcome FIRST and returned on
first failure, so **the limb it named was decided by the order the checks were written in**.
Sixteen verdicts, sixteen right answers, attributed reason wrong throughout — and nothing
downstream could detect it, because everything downstream reads verdicts. That number was
relayed onward before it was corrected.

**P16 — a guard is proven in three parts.** The foreign-registration-id guard, written against
the cross-contamination class, was destroyed by the heredoc-mangling class: its `\b` became a
literal BACKSPACE byte. It compiled, imported, ran, and the build printed `HELD 7 / REFUSING 1`
and success — while unable to match anything. Exposed only by planting a fake id. Repaired, it
then fired on a *correct* object. **The last clause is the one people skip**: a build reporting
success is not evidence a guard within it can fire.

**P17 — negative claims are computed.** `duplicate_seeding_check` asserted
`shared_with_other_topics: false`. Computed, it is **true** — two of sglt2-hf's trials are also
seeded by another topic. "Not shared", "no conflicts", "none found" all read as diligence and
are free to assert.

### 1.2.0-2026-08-19
Adds P13 and P14. Both are the same family as P11: the check ran, and it ran on the wrong
thing.

**P13 — keyed by entity.** `build_to_standard.py` accepted a topic argument and held
bempedoic-acid-review's executed queries, dates and record counts as MODULE CONSTANTS,
assigning them to whatever topic was passed. Run on another topic it would have written one
topic's executed search onto another — a **fabricated provenance record, on the property whose
entire purpose is provenance**. It did not ship only because it crashed first on an unrelated
hardcoded key and because the write happens at the end. **Luck, not design.** A parameter a
function does not honour is worse than no parameter: the signature advertises a generality the
body lacks, and it fails silently wherever the shapes happen to line up.

**P14 — no substring matching over clinical text.** Screening sglt2-hf's trials for a
two-component endpoint by substring returned ZERO for both EMPEROR trials, whose primaries ARE
that endpoint, because the registry writes `Cardiovascular (CV) Death` and the matcher wanted
contiguous `cardiovascular death`. It produced the right answer for one trial for the wrong
reason and the wrong answer for two others; trusted, it implies the pool was k=1 rather than
k=3. Parenthetical abbreviations are ubiquitous in registry outcome names.

### 1.1.0-2026-08-19
Adds P11 and P12, both from live defects on 2026-08-19.

**P11 — the coded field governs.** `comparators_identified_and_consistent` FAILed `sglt2-hf`
on `'placebo added to background heart failure therapy'` vs `'placebo'`, while
`comparator_type` read `'placebo'` on both and every control arm was labelled exactly
`placebo`. Routing through `text_match` was necessary and NOT sufficient: the strings really
are different and `text_match` was right to say so. **The error was asking a text question at
all**, when the semantic answer was recorded in the coded field beside it. This will recur
anywhere the corpus holds both a code and a label, so it is a property rather than one
assessor's fix.

**P12 — the suite ran.** The `criteria_stated` / `criteria_predefined` split was committed
without re-running `known_answer_preconditions.py`, which had been erroring on import since
the rename. It was "verified" by running the batch assessment and reading the matrix — which
is checking VERDICTS, not REASONING, for the third time in one night, and done to the suite
whose entire job is to catch that. **A green matrix is not evidence the suite ran.**

### 1.0.0-2026-08-19
First versioned statement. Encodes the lessons established through 2026-08-19:

- absent / empty / unreadable input is NOT_ASSESSABLE, never FAIL
- an instrument asserts the shape of its input and **raises** rather than returning a verdict
- a cross-instrument disagreement is evidence about the instruments only if both were asked
  the same question
- the known answer must come from the data, never from a fixture the author invented
- an object's record of what it EXCLUDED is not what it INCLUDED
- a Handbook section cited from memory is a registration number cited from memory
- a correct verdict reached by broken reasoning passes every outcome-based test; verdict and
  reason are two outputs and both need testing
- defects can run toward noise as well as toward silence — a check that fires on most of the
  corpus is more likely broken than the corpus is
