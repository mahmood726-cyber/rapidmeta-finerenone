# The mistake ledger

**51 mistakes, sourced. What now prevents each one. What still doesn't.**

Machine-readable source: `nafis_harness/ledger.py` · tests: `test_ledger.py` ·
run `python -m nafis_harness` for the live numbers.

> *"we need to log every mistake we have made so doesn't happen again"*
> *"so it should be easier each time"*

The second line is the specification, so this is not an archive. Its job is to
make page N+1 cheaper than page N. **A mistake that is recorded but does not
reduce future cost has not been logged, only remembered** — so every row ends in
a named artefact or in `NONE`.

---

## The headline, measured

> ## If every one of these 51 mistakes happened again tomorrow, **8 would be caught by something that runs on its own.**
>
> ## **15.7% today — and 52.9% the moment the harness gate is installed.**

| | |
|---|---|
| Caught today by an artefact that runs by itself (**WIRED**) | **15.7%** (8/51) |
| **The moment `harness_gate.py` is installed** | **52.9%** (27/51) |
| Ceiling if the retrieval lanes are wired too | 80.4% (41/51) |
| No mechanism at all (**NONE**) | **19.6%** (10/51) |
| **Caught autonomously when they actually happened** | **9.8%** (5/51) |

> ### ⚠ CORRECTION, 2026-08-17 — the previous version of this paragraph was wrong
>
> It said *"15.7% is up from 10.9%, and the whole rise is the nonce. Three rows
> moved to WIRED."* **No row moved from AVAILABLE to WIRED. Not one.**
>
> The three extra WIRED rows (W-01, W-02, W-03) are **new rows that were already
> guarded when they were written**, and W-03's guard is `gate_integrity.py`'s
> promotion criterion, which predates today and is not the nonce. **Holding the
> row set fixed at the original 46, the figure is unchanged at 10.9%.**
>
> A denominator that grows by five while the numerator grows by three raises a
> percentage without anything being guarded. I reported that rise as evidence of
> progress; it was arithmetic. Logged as **W-07**, and the corpus lane caught it
> by asking me to name the three rows.

**Nothing measured today improved the guarded fraction.** Five mistakes were
added to the ledger, three of which already had guards. That is the honest
statement of what changed.

### WIRED is detected, not declared

`nafis_harness/wiring.py` probes for a hook referencing `harness_gate.py` and for
the script beside it. The headline is computed from that probe, so **I cannot
move this number by editing a field, and I have not tried.** Current reading:

```
harness gate: NOT INSTALLED -- no hook in 2 probed root(s) references harness_gate.py
```

Install it and 15.7% becomes 52.9% on the next run, automatically. That is the
whole of `HANDOFF_CORPUS_LANE.md` §3a. If it is installed and the number does not
move, the detection is wrong and I want to know — which is the point of measuring
rather than asserting.

**Why not 80.4%?** Twenty of thirty detectors are artefact-decidable and can run
at push time. Ten are **retrieval-scoped** — they need an HTTP status, a click's
post-state, a route log, a source document's wording — and belong at the
retrieval lanes, not in a hook. The partition is a data structure
(`nafis_harness/artefact.py`), not a comment, and a test asserts every registered
detector is assigned to exactly one wiring point. A detector in neither list
would be silently uncovered.

**9.8% is still the number I would put in front of anyone who thinks we are
careful.** Five of fifty-one were caught by a mechanism rather than by a person
noticing.

### The wiring is proved to block, on real defects

`test_build_gate.py` replays **13 mistakes this project actually made** and
asserts the gate exits 1 on each and 0 on a clean artefact of the same shape.
Per `gate_integrity.py`: *"A synthetic failing input proves a detector CAN fire.
It does not prove the detector DISCRIMINATES."* Wiring that has never blocked
anything is a library with extra steps.

---

## W-02 — the row that explains the rest of this document

**Two probes, one root cause, opposite directions, and the survival times are
explained entirely by which way each failed.**

| | direction | survived |
|---|---|---|
| the agy vendor probe hit the wrong **quota pool** | **false death** | minutes |
| `regression_check.py` hit the wrong **working tree** | **false life** | **all day** |

Both are "a probe that cannot name its target." One raised an alarm and was fixed
immediately. The other issued green verdicts against a sibling clone on a
different branch — ARNI at **912,140 bytes over the wire against 6,147,695 on
disk** — and every regression PASS that day, including the ones relayed to
Mahmood as evidence things were fine, was measured against files that were not
being pushed.

**A false death interrupts you. A false life congratulates you.** The difference
in survival is not a fact about attention; it is a selection effect on which
errors get investigated. This is the sharpest evidence in the ledger for
`FINDINGS.md` Finding 2 — the asymmetry is structural, not attitudinal — and it
is now a matched pair with both directions observed rather than an inference.

**Why the guard is a nonce and not a hash.** Two clones of one repo agree on file
content constantly, so *any* content comparison passes. Only a value that did not
exist a moment ago cannot be satisfied by a stranger. The hook's own words:
*"index.html answering proves SOMETHING is there. It cannot prove it is us."*

**W-03, the payoff, belongs beside it.** The wrong-tree defect was found because
somebody was constructing a failing input to prove an unrelated detector could
fail — a fixture that should have 404'd returned 200 from a server answering for
every real page. **The discipline discovered a larger, unrelated defect while
verifying something else.** That is the return on "what input would make this
fail?", and it is not hypothetical.

---

## Provenance

36 of 46 rows are **[F]** — read verbatim from a named file this session. 10 are
**[R]** — operator-relayed, not file-backed here, and marked as such in the data.
Nothing is reconstructed from memory. Where the brief and a file disagreed, the
file is recorded and the discrepancy noted:

- the brief said the pre-push mechanism had **six** instances; `gate_integrity.py`
  documents **five**, and five is what is logged.
- the brief said the hardcoded docmodel contaminated **every tabbed build**;
  the file says **four other pages**.
- the brief said **one** of twelve clones had the repaired hook; the file says
  **6 of 12 still carried the broken one**.

Two of the three screening-parser defects could not be sourced at all and have
**no rows**. An unsourced row would make the ledger longer and less true.

---

## The mechanisms, by frequency

| Mechanism | n | What it is |
|---|---|---|
| M1 dead-plate negative | 5 | absence reported from an instrument that could not see |
| M5 identity by surface features | 5 | a name, label or citation string used as a key |
| M-GATE-CANNOT-FAIL | 4 | **a check that reports success without performing the check** |
| M10 bad correction | 4 | the repair was wrong, or worse than the original |
| M4 self-validation | 3 | a row authenticated against itself |
| M8 layer substitution | 3 | a sensitive check answering the wrong question |
| M-BUILD-PATH | 3 | text true on one build path, false on another |
| M-INSTANCE-FIX | 2 | the repair existed and had not arrived everywhere |
| M7 frame over-claim | 2 | a proportion against a denominator nobody maintained |
| M-PARSER | 2 | the parser silently mis-read the input |
| M6 wrong pool | 2 | every number correct, about different pools |
| M2 no error read as effect | 2 | absence of an exception taken as evidence |
| 9 others | 1 each | |

**M-GATE-CANNOT-FAIL is called "our most recurrent" in `gate_integrity.py`, and
the ledger agrees in substance**: its five instances share one shape — *the
success path is reachable and the failure path is not*. Add M4 and M11 and it is
11 of 46. A green result from such a check is evidence of nothing, and nobody
investigates a green result, which is why they survive.

---

## The unguarded queue — the actual work

Nine rows. Ordered: no mechanism first, then repairs that exist but only at the
instance.

### Priority 1 — no mechanism, and consequential

**R-03 · "81 commits were unpushed work at risk."**
*Truth: forcing that push would have destroyed the day's work. Caught only
because Mahmood did not act on the advice.*
This is the most serious row in the ledger and it is mine. An assistant's claim
about repository state is an extraction like any other, and it went out with no
witness, no instrument declaration, and no statement of what the opposite would
have looked like. Everything this project has built for *data* claims was absent
for an *advice* claim. **Guard: NONE. Nothing proposed yet.**

**G-02 · the repaired pre-push hook was not in force across the estate.**
6 of 12 checkouts still carried the broken one. `gate_integrity.py` states
plainly that wiring is outside its own scope. **A clone sweep exists as an
action, not as a standing artefact.**

**R-02 · a `sys.stdout` defect fixed in one module while three siblings carried
it.** Same shape as G-02. Nothing sweeps siblings for a repaired defect.

**W-05 · three checks that assert more than they measure** — `zero_included`
(since renamed `no_studies_rendered`, which is what it actually observes), the
RoB banner signal, and my raw-HTML rule. **A check's name is a claim about what
it observed, and nothing tests the name against the observation.** The rename is
the only repair and it is one instance of three.

### Priority 2 — no mechanism, narrower blast radius

**W-04 · two confident, wrong diagnoses of the render flakiness** — a rate
limiter (mine) and stale browser state (the lane's). It was neither: the value
was being sampled before it settled. This row is here as a *contrast*, not a
reproach: both hypotheses were **cheap because testable**, and being wrong cost
minutes. Set it against R-03, where the wrong claim was not testable and would
have destroyed a day. The difference is not care; it is whether the claim came
with a way to check it.

**G-03 · figure_audit passed pages it could not render** — a hidden or 0×0
element measured as a silent zero rather than reported unmeasurable. This is the
three-state failure inside a renderer: *measured zero* and *could not measure*
share a cell.

**B-05 · the text extractor silently dropped hidden tab panels.** Note that
`degrade_test.py` already prints `*** N/M PANELS HIDDEN WITH NO CONTROL TO OPEN
THEM ***`. **The observation exists and nothing consumes it** — which is a
cheaper fix than it looks.

**B-01 · the inverted provenance conditional** and **P-01 · the ordinal-split
parser that merged two screening records**. Both are named in `gate_integrity.py`
as free discriminating cases that *"no detector has yet been run against"*.

**R-04 · search breadth.** Not a mistake we caught — a property we have never
measured. 0 confirmed breadth failures against 22 checking failures, with both
measuring instruments field-internal. `CHK031_SEARCH_RECALL` is written and
deliberately **held out of the registry**, because it has no real positive.

### Priority 3 — a mechanism exists, applied only to the instance

**A-06 · the holdings table read as an institutional entitlement.** The claim was
backwards and had reached the spine of a paper. `CHK012_LAYER_MATCH` fires only
when both layers are labelled, and the original error was not noticing there were
two layers. `validator-validation-protocol.md` §6 marks this class **NOT CAUGHT**
by any coverage, mutation or vacuity criterion. **The only known countermeasure
is independent review by someone who did not frame the question** — a human
dependency the harness does not remove.

---

## What now prevents recurrence — the five WIRED artefacts

These run without anyone choosing to look. All five live in
`scripts/gate_integrity.py`.

| Guard | Catches | Earned from |
|---|---|---|
| **D1 pipeline status** | `$?` read after a pipeline, making the failure branch unreachable | the pre-push hook that printed "Regression check PASS" while gating nothing |
| **D2 scope honesty** | a gate's claimed scope vs what it globs | the header claiming "53 apps" over a script globbing 1,449 pages |
| **D3 skip flags** | an advertised bypass | *"a gate that documents its own bypass will be bypassed"* |
| **D4 no `sys.exit`** | a Python gate that cannot return non-zero | restricted to hook-invoked scripts after 217 false positives |
| **expected-section manifest** | a section present in one surface and absent from the other | the extraction provenance table missing from **every** Word manuscript the project ever produced |

Two of these were themselves repaired after firing badly: D4 was globbing
reporting tools that were never gates, and the scope check fired on the *repaired*
hook because its header explains the old false claim — **the detector was reading
a description of the defect as the defect.** Both repairs are in the shipped file.

---

## Three rows I want read rather than skimmed

**G-05 — my own.** CHK005's mutation test swept one key of six, so the pooled
estimate was never mutated and the test could not have failed. I reported it
protected. Found by another lane's mutant set, not mine.

**C-04 — also mine, and worse.** My fix for the referent interface hole broke the
honest caller: Arm A fell **7/7 → 2/7**, five real kills becoming five refusals.
My own mutation suite scored that change **0 survivors and clean**. It was caught
by the benchmark lane's set. This is why the external acceptance suite is vendored
into the test run rather than referenced.

**C-02 — the shape to remember.** The rule *"a bash zero is not a zero"* was
itself wrong for ~7 hours, because it correctly convicted bash and then wrongly
acquitted the whole live toolchain. The corrections that held in this project
were sourced from a **document not previously read**; the ones that failed were
re-interpretations of the instrument that produced the original. That is the rule
`CHK011_CORRECTION_BURDEN` now enforces.

---

## How to keep this honest

`test_ledger.py` fails if the ledger drifts toward flattery:

- a row whose `guard_state` is `NONE` but whose guard text names a detector
- a guard naming a detector that is not in the registry
- an `[R]` row whose source does not say it is operator-relayed
- an **instance** fix counted as class coverage, or absent from the work queue
- `WIRED` and `AVAILABLE` collapsing into one number

That last test is the important one. The moment those two are added together,
this document starts claiming 82.6% and the 33 uncalled detectors become
invisible.
