# `nafis_harness` — the implemented countermeasures

Companion to `TAXONOMY.md`. One mechanism, one detector, one fixture drawn from
an incident that actually happened.

```
python -m unittest test_harness mutation_suite test_external_acceptance   # 53 tests
python -m nafis_harness                    # self-test + dataset + diff + mutation + acceptance
python external/mutation_test_current_harness.py    # the authoritative set alone
```

Current state: **87/87 tests pass · 30 detectors fit · 70/70 dataset cases match ·
0 mutants survive in any arm of either suite · VERDICT CLEAN.**

---

## The classes with no defensible negative — read this list first

Coverage counts flatter. This is the list that does not.

| | what is missing | why it matters |
|---|---|---|
| **CHK031 SEARCH RECALL** | **no positive at all — HELD OUT of the registry** | Confirmed search-breadth failures in our corpus: **0**, against 22 checking failures (report #6 §6). A detector registered on a constructed positive is an unfired rule — M11 — so `Registry.register` raises on it today, by design, and a test asserts the refusal. It is written, executable and unadmitted. Its first real positive should come from a **published** review. |
| **CHK019 INERT ENGINE** | **negative does not exist in the corpus** | I scanned 786 pages and found **zero wired pages**. Among pages having an engine array, 224/233 (96.1%) AUTO and 291/311 (93.6%) curated are inert — corroborating 612/651 = 94.0%. The shipped negative is the one **constructed** fixture in the whole harness and is labelled as such. |
| **CHK030 BUILD-MODE-BLIND TEXT** | **positive is not independent** | It is the *same incident* as CHK026, generalised. Two detectors firing on one incident inflates apparent coverage, so the duplication is declared rather than left to be discovered. |
| **CHK017 DUP-1 bit equality** | negative cannot fire | Two independently derived floats are never bit-equal, so FIDELIO/FIGARO proves nothing about strictness. The stress case is a *near-miss* — agreement to 6 dp but not at full precision — pinned as a test so this can never drift into a similarity heuristic. |
| **CHK025 MULTI-SURFACE** | negative is generic, and there is a known false positive | A card rounded to 2 dp against a full-precision table row is a legitimate difference and **currently fires**. Asserted in a test rather than hidden. |

One more, different in kind: **CHK027's positive is unverified in my mount.** Two bash scans timed out and a host `Grep` for the sentinel returned nothing — which per **EB-022** is *not* a zero: *"a directory-Grep zero is not a zero either… the result set is a function of clock speed, not of file content."* Recorded as UNVERIFIED, not absent.

## The real acceptance — the benchmark lane's mutant set

| | Arm A keyed | Arm B number-bag | Arm C key omitted |
|---|---|---|---|
| `validate_v2.py` baseline | 0/7 | 0/7 | 0/7 |
| harness, before this pass | 7/7 | 2/7 (5 **SURVIVED**) | 2/7 (5 **SURVIVED**) |
| harness, after my "fix" | **2/7** ⚠️ | 2/7 | 2/7 |
| **harness, now** | **7/7** | **2/7** | **2/7** |
| | | 0 survivors | 0 survivors |

**Read the 2/7s correctly: they are zero *killed*, not zero *missed*.** A
number-bag and a referent omitting the mutated field cannot support a verdict on
those fields. What changed is that the five moved **PASS → INVALID** — refused,
not certified. The upstream headline counts only FAIL as a kill, so the number
cannot rise without the caller fixing its encoding, at which point it gets Arm A.

**Two defects that only this set found, neither visible to review, the unit
tests, or the suite I wrote myself.**

### D5 — my own fix broke the honest caller *(a regression, caught in the act)*

Requiring a document id and a per-key locator before **any** verdict closed the
number-bag hole and took Arm A from **7/7 to 2/7**. A caller that had extracted
the right quantity from the right source and keyed it correctly, but carried no
provenance metadata, went from five kills to five refusals. That is M10 in my own
code: the correction was worse than the original in one direction, and I would
have shipped it, because my own mutation suite scored it 0 survivors.

The discriminator that fixes both directions was already in the corpus — the
CHK014 caveat in `cardio_acm_harness_report.md`: *"agreement authenticates
nothing. Only disagreement is informative."* So **provenance gates the agreement
path only**:

| | verdict |
|---|---|
| disagreement, provenance or not | **FAIL** — a contradiction against any referent is a real contradiction |
| agreement **+** document id **+** per-key locators | **PASS** |
| agreement without provenance | **INVALID** — this is exactly what a bag echoing the row produces |

### D6 — an off-by-one inside a tolerance band was certified

Mutant M5b perturbs `registry_enrolment` 33758 → 33759 and `CHK006` returned
**PASS**, because 1 is far inside `max(0.1 × enrol, 50)`. My suite had no mutant
for it. The tolerance is correct — analysed N legitimately differs from
randomised N — but **a tolerance is a statement that the instrument cannot
resolve differences of that size, and a check must not clear a dimension it
cannot resolve.** A non-zero delta inside the band is now INVALID unless the
caller supplies `enrolment_delta_explained`. This mirrors the corpus's own
`CHK002_DENOMINATOR_NOT_RANDOMISED`, which holds PARAGON-HF open because 12 and
14 participants were excluded with the reason *"NOT STATED"* — *"an unexplained
exclusion is not the same as an explained one."*

**The vendored copy is verbatim.** `external/mutation_test_current_harness.py`
was copied without a line changed — including its hardcoded `sys.path.insert` for
another session's mount, which resolves to nothing and is harmless. Editing a
test to make it pass is the oldest route to a check that cannot fail. A sha256 is
recorded beside it and `test_the_vendored_copy_is_unmodified` enforces it. It is
vendored rather than referenced because an unreachable external dependency would
make the test *skip*, and a skipped acceptance reads as a passed one — EB-024,
`CLEAN` absorbing "unchecked", 54 apps.

Two of the fifteen (`CHK014`, `CHK015`) are registry positions **P34** and **P33**
moved from `PROPOSED` to `IMPLEMENTED` + self-tested both directions, per the
registry's own house standard.

---

## Three defects, found by mutation testing and now fixed

**34/34 unit tests passed while this harness scored 2/7 on planted errors.** That
is the entire case for `mutation_suite.py` being permanent: the unit tests were
written by whoever wrote the detectors and test the propositions the detectors
state about themselves. All three defects were in `CHK005_EXTERNAL_REFERENT` —
the detector for M4 — and none was visible to review.

### D1 — the interface hole *(the important one)*

`CHK005` killed all five value mutants when handed a referent keyed by field, and
**passed all five** when handed a flat number-bag echoing the row: the encoding
`validate_v2.py` used, and the historical failure. It refused an *absent*
referent while being unable to tell a sourced extraction from numbers echoed out
of a bag. **The mechanism was fixed at the detector and left open at the
interface — M4 operating inside the tool built to catch M4.**

Fix: **the referent must carry provenance — a document id, and a `locator` per
key.** A bag has nowhere to put a locator, so it cannot masquerade as an
extraction. This is structural rather than a request that callers behave.

```python
"referent_document_id": "NCT02270242",
"external_referent": {
    "tN": {"value": 3555, "locator": "participantFlow.STARTED, ticagrelor+placebo"},
    "cN": {"value": 3564, "locator": "participantFlow.STARTED, ticagrelor+aspirin"},
}
```

### D2 — missing keys were a silent skip

The comparison was `for k, v in ref.items() if k in row`, so a key under test
that the referent did not cover was skipped rather than flagged. **A field nobody
checked must not read as a field that passed.** Now INVALID, naming the keys. A
caller that genuinely wants a partial check must say so with `keys_under_test`.

### D3 — the vacuity sweep covered one key in six, by alphabetical accident

The row mutator was `_deep(p, ["row", sorted(p["row"])[0]], -1)` — the
alphabetically first key only. Renaming `dosed` → `zz_dosed`, semantics
unchanged, flipped INVALID to PASS. **Coverage that depends on key spelling is
not coverage.** `run_vacuity` now accepts list-returning mutators and sweeps
every key of a mapping-valued term, naming the specific sub-mutant
(`row[tN]`, `row[cN]`, …).

### D4 — the asymmetric witness rule, logged in §4.8 and now closed

The obligation was enforced on PASS and not on FAIL. That one-sidedness is
Instance 5 in the synthesis-audit lane — the lane's own rule *"was written
asymmetrically… Within the hour it failed in the other direction"*. `Result` now
applies the witness requirement to **PASS and FAIL alike**; on a FAIL,
`opposite_would_be` is what a PASS would have looked like. Every `make_fail` call
site in `probes.py` was updated with a real witness rather than a template.

### The measurement

7 planted defects × 3 caller encodings × 2 implementations. Scoring is three-way,
because a binary killed/survived score would read INVALID as a miss — the same
collapse the harness exists to prevent, one level up.

| | legacy killed / not-banked / **SURVIVED** | current killed / not-banked / **SURVIVED** |
|---|---|---|
| **A** keyed + provenanced | 5 / 1 / **1** | 5 / 2 / **0** |
| **B** flat bag echoing the row | 0 / 1 / **6** | 0 / 7 / **0** |
| **C** partial referent | 2 / 1 / **4** | 0 / 7 / **0** |
| **total survivors** | **11** | **0** |

**Acceptance criterion: `SURVIVED == 0` in every arm. Met.**

**Read arms B and C honestly.** Current scores 0 *killed* there — it does not
identify which value is wrong. It refuses to certify at all, because a referent
without provenance cannot support any verdict. That is the correct outcome and it
is not detection: a caller on those encodings gets INVALID until the encoding is
fixed, at which point they get arm A. Note also that legacy arm A already had one
survivor (D2's silent skip) — the best encoding was not clean either.

**Two caveats on this suite, both load-bearing.** It is **author-inherited**: I
wrote it to grade my own fixes, which is the authorship blind spot `TAXONOMY.md`
§4.1 names, and it is therefore weaker evidence than the benchmark lane's
`mutation_test_current_harness.py`. I could not reach that script — the benchmark
lane's outputs folder is a sibling session path I do not have, and requests above
`local_<id>\outputs` are refused. **Its run against this harness is the real
acceptance; these numbers are provisional.** And the legacy arm-B figure here (6
survivors) differs from the reported 2/7 because the mutant set differs; the test
asserts the *direction* and `current == 0` rather than reproducing a number I
cannot see, since asserting their figure against my set would be manufacturing
agreement.

---

## Both binding constraints, and how they are met

**No regression.** The package is additive and self-contained. It writes nothing
outside its own directory, makes no network call, imports nothing beyond the
standard library, and replaces no existing check. `F:\rapidmeta-finerenone` and
`F:\rapidmeta-ssot-shell` were mounted **read-only** and neither was modified.
The existing `detector-library/` scripts are untouched; this sits alongside them.

**No unnecessary tokens.** There is not one model call in the package, and no
dependency that could introduce one. Every detector is a pure function over a
dict. The full suite — 13 detectors × their controls, a 40-case dataset, and a
vacuity sweep — runs in **2.1 ms** of CPU; the 30-test meta-suite in **48 ms**.
The marginal token cost of running this harness is **zero**.

Anything requiring a model call had to justify itself against a deterministic
alternative. Nothing did. Every mechanism in the taxonomy turned out to be
detectable from structure — a status code, a field's presence, a hop count, a
denominator's provenance — rather than from meaning.

---

## The five priorities from the researched protocol

### 1. Three-state verdicts with a mandatory witness — `verdict.py`

`PASS` / `FAIL` / `INVALID`, and `INVALID` is not a soft `FAIL`. A `PASS`
constructed without a complete `Witness` is **rewritten to `INVALID`** with the
deficiency recorded. `bool(Result)` **raises `TypeError`** — `if result:` would
make `INVALID` truthy, which is the exact collapse the harness exists to prevent.
`tally()` keeps `INVALID` out of the reportable denominator and deliberately
offers no "clean" total, so nothing acquires a denominator by accident.

The `Witness` carries the instrument declaration as a required field:
`opposite_would_be` — *what a FAIL would have looked like on this instrument*. No
answer, no PASS.

### 2. Vacuity checking, per Beer et al. — `check.py`

Each check declares its observation terms with a mutator that forces the term to
its flipping value. On any PASS the sweep re-runs the check once per term; if the
PASS survives, the verdict never depended on that term and the result is
`INVALID` — *"PASS is vacuous"*. n+1 executions, CPU only.

`test_a_check_that_ignores_its_observation_term_is_vacuous` reproduces the caption
checker that read the downloads block, and the sweep catches it.

### 3. Mutation / fixture requirement — `registry.py`

`Registry.register()` raises `InadmissibleDetector` unless the check has at least
one fixture it must **fire** on, one it must be **silent** on, and one declared
observation term. Controls then re-run on **every execution** — the dead-plate
rule — so a detector that breaks mid-campaign voids the run rather than reporting
a clean one.

Fixtures carry a `provenance` string naming the incident, and
`test_every_shipped_fixture_names_the_incident_it_encodes` enforces it, so nobody
deletes them later as synthetic noise. The negatives that already exposed bugs are
the ones in the file: TWILIGHT Location A (matches the registry exactly),
ORION-11 @ NCT03400800 (confirmed correct in report #6), the compliant ANSWER-HF
route log, N3 as corrected.

### 4. Instrument declaration — `verdict.Witness.opposite_would_be`

Enforced at construction, not by convention. It is the field that makes a
witness-less PASS impossible to express.

### 5. Identity keying — `CHK006_IDENTITY_KEY`

Registration identifier, **verified against the source document**. A name, label,
filename or citation string returns `INVALID` with the reason *"Names are not
keys: a covering label can span two trials."* Registry acronym must match the
recorded name; registered enrolment is checked against row weight, which is what
separates ORION-4 (16,124) from ORION-11 (1,617).

---

## LangChain — implemented exactly as the researched verdict specifies

| Component | Decision | Where |
|---|---|---|
| **LangSmith pattern** — dataset → reference outputs → baseline diff | **Taken**, as our own ~200-line local implementation | `baseline.py`, `dataset.py` |
| **LangChain core** | **Not taken.** ~150 tokens of boilerplate per structured call plus a retry loop that re-bills whole calls; it would also put a model in the path of checks that are currently deterministic CPU, failing the no-regression constraint | — |
| **LangGraph** | **`interrupt()` only.** Its replay re-executes model calls, which against a written ledger is a downgrade paid for in tokens | `interrupt.py` |

**And the thing LangSmith does not solve.** An evaluator returning `{"ok": 1}`
shows 100% green with no warning. That is validator validation, and the dashboard
cannot see it. Three guards:

1. `Dataset.discrimination_problems()` refuses a dataset with no case expecting
   `FAIL` (or none expecting `PASS`) — a constant evaluator would score 100% on it.
2. A run in which every case returns the same verdict is reported
   **NON-DISCRIMINATING** and is *not scoreable* — all-green included.
3. A run whose `INVALID` share exceeds 25% is reported **INSTRUMENT DEGRADED**
   rather than scored.

Plus the registry-level guard: the `{"ok": 1}` evaluator cannot pass `self_test()`
at all, because it has no fixture it fires on. `test_the_ok_1_evaluator_cannot_be_registered`
demonstrates it.

The diff also reports **`went_blind`** — cases that moved `PASS → INVALID`
between runs. A case going blind is not neutral: it means the corpus stopped
being watched at that point, and a conventional pass-rate would show it as an
improvement or hide it entirely.

---

## The thirteen detectors

| ID | Catches | Historical anchor |
|---|---|---|
| `CHK001_RETRIEVAL_ABSENCE` | absence claimed from a non-200 | a 429 read as "no record exists" |
| `CHK002_TOKEN_MATCH` | unscoped substring search | `grep "fatal"` → `Nonfatal Myocardial Infarction` |
| `CHK003_ACTION_EFFECT` | no error read as an effect | `ref` click that silently no-op'd |
| `CHK004_LIVENESS` | death reported from a blind probe | `pgrep` on Windows; the daemon that ran for hours |
| `CHK005_EXTERNAL_REFERENT` | self-consistency as authentication | TWILIGHT Location B, RR 0.995 vs stored HR 0.99 |
| `CHK006_IDENTITY_KEY` | identity from a label | ORION-11 recorded on ORION-4's NCT |
| `CHK007_ABSENCE_SCREEN` | "none found" from prose | N2 — "not encountered" |
| `CHK008_FRAME_DENOMINATOR` | coverage over an unmaintained denominator | N3 — 44 of a 244 frame, claimed complete |
| `CHK009_POOL_IDENTITY` | right numbers, wrong pool | k=3 panel under a k=4 headline; TWILIGHT composite in a mortality atlas |
| `CHK010_CHAIN_EXHAUSTION` | abandoned reported as blocked | four-hop chain abandoned at hop zero |
| `CHK011_CORRECTION_BURDEN` | a correction that is worse than the original | ANSWER-HF; the Epub-date year "fix" |
| `CHK012_LAYER_MATCH` | **partial** — layer substitution | holdings table read as an entitlement |
| `CHK013_FIELD_SEMANTICS` | a field is not the quantity its name suggests | publication-date field returning the Epub date |
| `CHK014_FILTER_FIRED` | a filter that was silently ignored | EC-001 — `allowed_domains` ignored; two false "no EMA document exists" |
| `CHK015_HIT_COUNT_SANITY` | an implausible count means the query was discarded | EC-002 — a CJK query dropped, 471,547 hits returned |
| `CHK016_PRECISION_SAMPLE_MISMATCH` | the interval's SE ≠ the sample's SE | MAVACAMTEN OR 6.67 (2.09–21.30): SE 0.5922 vs 0.2999 from 45/123 vs 22/128 |
| `CHK017_DUP1_BIT_EQUALITY` | one estimate entered twice | AZITHROMYCIN, both entries `-0.15082288973458366` |
| `CHK018_MIXED_POOLING` | opposite directions / incompatible measures | MITRAL pooling a hazard ratio with an odds ratio |
| `CHK019_INERT_ENGINE` | engine shares no identifier with its page's data | 612/651 pages; corroborated at 93.6–96.1% in 786 scanned here |
| `CHK020_ORPHAN_POOLED_RESULT` | a rendered pooled estimate with a dead engine | 39 pages |
| `CHK021_MEASURE_SCALE_MISMATCH` | a measure at odds with its stored scale | MD −54 exponentiated → 0.0000 |
| `CHK022_RATIO_FROM_PERCENTAGE` | a ratio the source never states | MORDOR-I: *"Mortality was 13.5% lower overall"* |
| `CHK023_CROSS_AGENT_POOLING` | distinct agents, no declared class | nirmatrelvir 0.11 pooled with molnupiravir 0.69 |
| `CHK024_FALSE_METHOD_CLAIM` | "NMA" over an object with no network | a card asserting NMA |
| `CHK025_MULTI_SURFACE_DISAGREEMENT` | one claim, two surfaces, two answers | a withdrawn card leaving a live table row |
| `CHK026_WRONG_REASON_ABSENCE_PANEL` | an absence rationale false of its own page | ARNI's text on converted pages; would have shipped on 28 |
| `CHK027_SENTINEL_LEAK` | an internal marker rendered to a reader | `NOT RECOVERABLE FROM THE PAGE` ×9 |
| `CHK028_DISQUALIFIED_REFERENT_PROMOTED` | object overriding a source-verified card | `DOAC_CANCER_VTE` card HR 0.55 vs object OR 0.7290 |
| `CHK029_SIGN_NORMALISATION` | a Unicode minus read as positive | `&minus;71.31` → +71.31; 2 of 7 reported conflicts |
| `CHK030_BUILD_MODE_BLIND_TEXT` | a rationale not conditioned on its build path | the general form of CHK026 |
| `CHK031_SEARCH_RECALL` | **held out — no real positive** | breadth failures confirmed: 0 |

### Notes on three of the new ones

**CHK016 is the strongest of the batch and I verified its arithmetic before
fixturing it.** SE from CI 2.09–21.30 = **0.5922**; SE from 45/123 vs 22/128 =
**0.2999**; ratio **1.975**; and the OR those arms actually imply is **2.780**,
not 6.67 — so estimate *and* interval both came from elsewhere. MITRAL
reproduces at 0.2603 and its 0.6677 is the exact geometric mean of its own
bounds. A **declared** variance adjustment (HKSJ, random-effects) returns
**INVALID, not PASS**: the check cannot resolve a legitimate inflation from a
wrong population, so it refuses rather than clears.

**CHK018 deliberately does not read I².** The heterogeneity signature was
dismantled by the adversary, so this reads only measure type and direction of
benefit — structural properties of the endpoint, not statistics about the data.
A guard test asserts that I² ∈ {0, 50, 91, 99} changes no verdict, and
INCLISIRAN's 72% single-endpoint pool is the load-bearing negative.

**CHK029's real risk is the opposite of its positive.** Normalising every
dash-like character would turn the interval `0.73–1.13` into −1.13 and invent a
negative bound. Normalisation therefore applies to a **leading** sign only; an
internal dash makes the string a non-scalar and the parser declines rather than
guesses. Both directions are pinned: six encodings of −71.31 normalise
identically, and an en-dash range parsed as a scalar **fails**.

---

## Wiring it into a lane

```python
from nafis_harness import build_registry, Verdict

reg = build_registry()
fitness = reg.self_test()
assert fitness["ok"], fitness["unfit"]          # unfit registry ⇒ report nothing

r = reg.run("CHK005_EXTERNAL_REFERENT", {
    "referent_name": "ClinicalTrials.gov NCT02270242 participant flow",
    "row": {"tN": 4614, "cN": 4603},
    "external_referent": {"tN": 3555, "cN": 3564},
})

if r.verdict is Verdict.FAIL:      raise_defect(r)
elif r.verdict is Verdict.INVALID: hold_row(r)   # NOT "clean"
else:                              record(r.witness)
```

And for the "do not guess" decisions the defect ledger already contains:

```python
from nafis_harness import Ledger
led = Ledger("ledger.jsonl")
led.raise_interrupt("TWILIGHT-01",
                    "classes[20].pool (k=2) is invalid until the composite row is resolved",
                    ["remove row", "replace with true ACM"], nct="NCT02270242")
ok, blockers = led.may_report()   # (False, [...]) — a pending interrupt is a hard stop
```

Resumption reads the ledger. It does not re-derive the decision, because
re-deriving a recorded human adjudication is mechanism M10 with extra steps.

---

## Where this is weak

Set out in full in `TAXONOMY.md` §4. In short:

### The holdings-table class: a human dependency this harness does not remove

**M8-a would still not be caught.** The check was perfectly sensitive and
answered the wrong question. Coverage, vacuity, controls and the witness rule are
all properties of *sensitivity*; none touches a question/instrument mismatch.
`CHK012` only converts the *unsure* case into a refusal — the *confidently
wrong* case, which is the historical one, passes with a complete and honest
witness.

`validator-validation-protocol.md` §6 reaches the same verdict independently — the
only row in its table marked **"NOT CAUGHT"** — and states why: *"no coverage
criterion, no mutation score, no vacuity procedure, no metamorphic relation
touches this class, **because every one of them is defined relative to the
check's own stated proposition**."* It is a failure of **clinical validity, not
analytic validity**: the assay detects its analyte perfectly; the analyte does not
mean what the report claims.

> **The only known countermeasure is independent review by someone who did not
> frame the question. This is a human dependency, and the harness does not
> remove it.**

It cannot. Any automated check for *"is this the right question?"* would be
written by whoever framed the question and would inherit the framing — the
protocol's phrase is that neither available mechanism *"can be automated without
reintroducing the same authorship blind spot."* Two operational consequences:

1. **Independence must be in the framing, not just the person.** A second reader
   handed the same question statement checks the same proposition. The reviewer
   has to be given the underlying need, not the check's specification.
2. **The machine analogue is cross-family, not cross-run.** The registry's
   `CANNOT-BE-AUTOMATED-WITHIN-FAMILY` position — *"THE ONLY DETECTOR IS A
   DIFFERENT MODEL FAMILY… not a gap to apologise for, it is the measured
   justification for the mandatory gate"* — is the same rule at machine scale,
   and cross-family adversary passes are the highest-yield catch mechanism
   measured anywhere in the programme.

Do not read the 15 green detectors as covering this. They do not, by construction.

### Other residuals

- **My own witness obligation is one-sided** — required on PASS, not on FAIL.
  That is the exact asymmetry that produced Instance 5 (the LibKey button) in the
  other lane. Logged in `TAXONOMY.md` §4.8, unfixed, highest-priority next item.
- **A consistently-applied wrong identifier** produces no conflict. The fix is
  specified in report #6 §5 and is unrun.
- **Breadth failures** are not measured by anything here. 0 confirmed against 22
  checking failures remains *not yet caught*.
- **Eleven catalogued incidents are single-sourced** to Mahmood's brief, because
  the session transcripts are unreadable from this environment. Those detectors
  are aimed at a described mechanism, not a verified one.
