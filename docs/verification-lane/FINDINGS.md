# Three findings, recorded in their own right

**Date:** 15 August 2026 · **Status:** all three now measured against
`F:\E156\ERROR-REVERSAL-REGISTRY.md` (64 records + 3 Class C) and
`validator-validation-protocol.md`, rather than against my n=7 sample.

These are stated separately from the taxonomy because each is a claim about the
programme, not about an incident, and each carries an operational consequence.

---

## FINDING 1 — M4 is the spine: self-validation is an architecture, not a bug

> **"Consistency does not authenticate a row."**
> — `DEFECT_LEDGER_cardiology_mortality_atlas.md`
>
> **"Agreement authenticates nothing. Only disagreement is informative."**
> — `cardio_acm_harness_report.md`, CHK014 caveat

**The measurement.** Three defects — TWILIGHT, GLOBAL LEADERS, CANVAS Program —
each survived **71 days** (object generated 2026-06-02, raised 2026-08-12) inside
a generated object where the only automated check available could return nothing
but PASS. TWILIGHT's Location B reproduces its own hazard ratio to three decimal
places (172/4614 vs 168/4603 → RR 0.995 against a stored HR of 0.99) while its
denominators exceed the trial's registered randomised total by **2098** and its
death count is **4.3×** the registry's.

**Why this is architectural rather than incidental.** A check that validates a
row by re-deriving the row's own effect estimate from the row's own counts has
no external referent. Its verdict function is *total on PASS*: for any
internally coherent row, including a wholly invented one, PASS is the only
reachable output. It is not a check that failed. It is a check that had no FAIL
branch.

The registry quantifies how little the automated layer contributes: of 45 Class B
records, **`ledger-guard` caught 3**. Adversary passes caught **20 of 45
(44.4%)**, `cross-source-comparison` 13. The mechanisms that find things are the
ones that bring in something from outside; the in-family automated guard is the
weakest catcher in the programme.

**And it is the same defect we document in published reviews.** Jyotsna 2023 and
Chen 2026 both triple-count FIDELIO-DKD and both report **I² ≈ 0%** — *"which is
what pooling data against itself produces."* A synthesis that reproduces its own
numbers has proved nothing about whether they match the source. We publish that
finding about others' work; M4 is us doing it to ourselves, in code, with a
71-day latency.

**Operational consequence.** `CHK005_EXTERNAL_REFERENT` returns **INVALID**, never
PASS, when no external referent is supplied. Not FAIL — INVALID: a row validated
only against itself is unadjudicated, and the distinction has to survive into
whatever counts the rows.

---

## FINDING 2 — asymmetric scrutiny is not attitudinal; it is a property of the instruments

**Mahmood's hypothesis, as posed:** confirming results get less scrutiny than
contradicting ones — a bias in what we choose to examine.

**What the evidence supports instead, and it is stronger:** in **6 of 7** errors
with documented timing, *the instrument had no channel on which the contradicting
answer could have arrived.* Deciding to be more sceptical would not have caught
DEFECT-01. Requiring an external referent does. This converts a disposition into
an engineering requirement, and only the second form survives a handover.

### The registry had already measured the attitudinal version

| Statistic | Value |
|---|---|
| Our content-changing errors (denominator rule stated in the file) | **37** |
| Favoured us | **25** |
| Against us | **11** |
| Neutral | 1 |
| **Fraction favouring us** | **0.676** (0.694 excluding neutral) |
| Declared a **floor**, with four stated reasons | `fraction_is_a_floor: true` |
| Independent-source measured, pooled across 6 named audits | **20 of 28 = 0.714 flattering** |

So the directional asymmetry is real and measured at **≈68%, as a floor**. That
is Mahmood's hypothesis, confirmed on a proper denominator — not mine.

### But the decisive evidence separates the two explanations

The registry maintains a **Class C** for defects in the *tools*, and records
their direction at two levels:

> *"`direction` is recorded at the tool level as `NEUTRAL` — **a tool has no
> interest** — but every record carries `consequence_direction`, and every one of
> them is the same: `FAVOURS-US-IF-UNCAUGHT`. A false 'nothing exists' flatters
> our coverage and excuses our ceiling."*

**This is the test that discriminates.** In Class C an attitudinal explanation is
impossible by construction: `WebSearch` silently ignoring `allowed_domains` has
no preference about our coverage; PubMed discarding every Chinese character from
a CJK query has no view on our recall. Yet the consequence direction is
**3 of 3 flattering** (EC-001, EC-002, EC-003 — and EC-003 alone contains five
false *"unfindable"* verdicts).

The asymmetry therefore cannot be wholly a matter of what we chose to scrutinise,
because a class of it occurs in instruments that cannot choose. **A broken
instrument almost always fails toward "nothing there", and "nothing there" is
almost always the answer that reduces work.** The bias is in the failure mode of
measurement, not in the character of the measurer.

Two verified cases make the mechanism concrete:

- **EC-001** — a domain-restricted search *"returns chrome and no products"*. Two
  *"no EMA document exists"* verdicts were reached through it. They were
  discarded **"only because the lane distrusted them"** — scepticism worked here,
  and it worked by luck of disposition rather than by construction.
- **EB-023** — a control-node recode tested `startswith('Warfarin')` against a
  string `norm_node()` had already lowercased. *"Scenario B was byte-identical to
  scenario A and looked like a completed sensitivity analysis."* Direction:
  **FAVOURED US**. A sensitivity analysis that passes because it never ran.

**Operational consequence.** Three detectors are implemented against this
directly, and two of them are the registry's own PROPOSED positions now written
as code: `CHK014_FILTER_FIRED` (registry **P34** — *never record a negative from
a filtered search whose filter was not confirmed*), `CHK015_HIT_COUNT_SANITY`
(registry **P33** — *a count orders of magnitude above expectation means the
query was discarded, not that it matched*), and the vacuity sweep in `check.py`,
which is EB-023's *"assert that a sensitivity recode FIRED before reporting its
result"* generalised (registry has it as **IMPLEMENTED AS A RULE, PROPOSED AS
CODE**; it is now code).

---

## FINDING 3 — the discriminating feature of a correction that holds

**The rule:** *a correction that holds is sourced from a document not previously
read. A correction that fails is a re-interpretation of the instrument that
produced the original.*

**Measured support, three independent lines:**

| Evidence | Result |
|---|---|
| `13_ERROR_LIBRARY.md` §6 — the library's own control | **2 of 3** external error accusations withdrawn on verification |
| **EB-021 → EB-022** | The rule correcting the bash false zeros was itself *"UNSAFE AS WRITTEN AND HAS BEEN MISLEADING RUNS FOR ~7 h"* — it *"correctly convicted bash and then **wrongly acquitted the whole live toolchain**"* |
| ANSWER-HF | Original extraction right; **three** separate corrections wrong |

**EB-022 is the cleanest instance in the corpus**, and it is the one the new rule
is built on. The correction to EB-021 was a careful, well-motivated
re-interpretation of *the same 265 MB network mount through a second tool on the
same host*. It was wrong for seven hours. What eventually settled it was a new
observation — a dead regex branch that *dropped* a file from the result set,
proving *"the result set is a function of clock speed, not of file content."*

Contrast the corrections that held: Li 2019's comparator (enalapril →
**benazepril**, *"flipped the verdict from undetermined to ineligible"*) came from
a CQVIP record retrieved for the first time, through one of seven routes tried.
Reyaz 2023's reference [15] came from a publisher PDF not previously opened.

**Why the mechanism is not just "be careful".** A correction is issued *because* a
discrepancy was noticed, so the prior is already against the original. The step
that would catch a bad correction — re-reading the original at its own source —
is by definition the step the correction skipped, since had it been performed
there would have been no discrepancy to correct. And once issued, the object is
"fixed" and rarely re-reviewed. The only reliable circuit-breaker is **new
evidence**, because it is the only input that was not available to the reasoning
that produced the error.

**Operational consequence, implemented.** `CHK011_CORRECTION_BURDEN` now returns
**FAIL** on any correction where `evidence_is_newly_retrieved_source` is false,
with the reason *"a re-interpretation of already-held material is the failing
pattern; a document not previously read is the holding one."* Its must-fire
fixture is EB-022 itself. Pinned by
`test_correction_reinterpreting_held_material_fails`.

---

## Cross-reference: where these three land in the harness

| Finding | Detector / mechanism | Registry status before | Status now |
|---|---|---|---|
| 1 — M4 self-validation | `CHK005_EXTERNAL_REFERENT` | implied by CHK014 caveat, prose | code, INVALID-by-default |
| 2 — structural asymmetry | `CHK014_FILTER_FIRED` (P34) | **PROPOSED** | **implemented + self-tested** |
| 2 — structural asymmetry | `CHK015_HIT_COUNT_SANITY` (P33) | **PROPOSED** | **implemented + self-tested** |
| 2 — structural asymmetry | vacuity sweep (EB-023 generalised) | IMPLEMENTED-AS-RULE-NOT-CODE | **code** |
| 3 — correction burden | `CHK011_CORRECTION_BURDEN` | no position in the registry | **implemented + self-tested** |

Registry house standard, met by all four: *"IMPLEMENTED requires code;
SELF-TESTED requires a seeded failure that must fire AND a legitimate case that
must not fire."*
