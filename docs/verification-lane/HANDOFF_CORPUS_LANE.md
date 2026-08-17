# Handoff to the corpus lane — adopting `Result` in the existing gates

**From:** the retrospective lane · **To:** the corpus lane (single writer on `F:\E156`, `F:\rapidmeta-*`)
**Date:** 15 August 2026
**What you are being asked to adopt:** `nafis_harness.verdict` — the three-state `Result` with the raising `bool`. Nothing else is required.

This lane holds **no writer lock** and has written nothing to `F:\`. Everything below is a proposal for you to accept, amend or reject, in the same form as the `errors[]` specification in `14_RULE_TESTS_AND_SPECIFICATIONS.md`.

---

## 1. Why this piece first

Your registry already records this failure twice, in code you own:

- **EB-024** — *"**54 apps would have scored CLEAN on ZERO executed checks.**"* Remedy applied: a separate `UNVERIFIED-INSUFFICIENT-DATA` tier. Related: the push gate *"blocks only on `is False`; **`None` falls through to `[OK]`**"* → `None` now maps to `skipped_undetermined`, explicitly **NOT a pass**. And `NOT ADJUDICATED 1966 (70.2%) <- NOT a pass`.
- The registry's own summary of the class: **"Do not render grey tiers as green."**

Both fixes are correct and both are *local*. They patch the two places where the collapse was noticed. `Result` makes the collapse **unrepresentable everywhere**, because there is no boolean to fall through to:

```python
def __bool__(self):
    raise TypeError("a Result is three-state and must not be used as a boolean")
```

Any surviving `if verdict:` or `if not result:` in the codebase raises on first execution rather than silently reading INVALID as clean. That is the whole value of adopting it: **the migration finds the remaining instances for you.** You do not have to go looking.

---

## 2. What you get, and what it costs

| | |
|---|---|
| **Import cost** | stdlib only. `dataclasses`, `enum`, `json`, `os`, `copy`, `platform`, `argparse`. No third-party dependency, no network, no model call |
| **Token cost** | zero, in the harness and in the migration |
| **Runtime** | 15 detectors + controls + vacuity + a 48-case dataset: **2.1 ms**. The 34-test suite: **48 ms** |
| **Blast radius** | `verdict.py` alone is 197 lines and depends on nothing else in the package. You can take that one file |

---

## 3. Migration, in the order that cannot regress

**Step 0 — take one file.** Copy `nafis_harness/verdict.py`. It has no intra-package imports. Everything else (`check.py`, `registry.py`, `probes.py`, `baseline.py`, `interrupt.py`) is optional and can follow later or never.

> ⚠️ **Changed since the first version of this handoff: the witness obligation is now SYMMETRIC.** A `FAIL` requires a witness exactly as a `PASS` does; on a FAIL, `opposite_would_be` is what a PASS would have looked like on that instrument. This matters for your migration because the adapter in step 1 must supply a witness on the `False` branch too, or the legacy FAIL becomes INVALID. That is deliberate — a defect asserted from an instrument that could not have cleared the subject is as void as a clean bill from one that could not have failed it, and a false defect is how a correction becomes worse than the original. Expect the first run to convert some legacy `False` results to INVALID; those are gates that have never recorded *why* they failed.

**Step 1 — wrap, do not replace.** For each existing gate, add an adapter that produces a `Result` *alongside* the current return value. Do not change the gate's own logic yet. Run both for one cycle and diff. This is the `--update-baseline` discipline applied to the migration itself: you want a run where the only change is that a second, richer verdict is being recorded.

```python
from verdict import Verdict, make_pass, make_fail, make_invalid

def as_result(check_id, legacy, *, instrument, witness=None):
    """legacy is the existing True/False/None. `witness` is required for BOTH
    True and False -- the obligation is symmetric."""
    if legacy is None:
        return make_invalid(check_id, instrument,
                            "legacy check returned None: not executed, or could not see")
    if witness is None:
        state = "False" if legacy is False else "True"
        return make_invalid(check_id, instrument,
                            f"legacy {state} with no witness -- neither a defect nor "
                            "a clean bill can be reported without one")
    if legacy is False:
        return make_fail(check_id, instrument, "legacy check returned False", **witness)
    return make_pass(check_id, instrument, **witness)
```

### ⚠️ EXPECT A WAVE OF INVALIDs ON THE FIRST RUN. THAT IS THE MIGRATION WORKING.

**Read this before anyone "fixes" it.**

On day one, every legacy `True` without a witness becomes **INVALID**, and — since the obligation is symmetric — so does every legacy `False` without one. Expect a large INVALID share. `run_dataset()` will report **INSTRUMENT DEGRADED** above 25%.

**That is the honest verdict for those gates, not a breakage.** A gate that returned `False` while recording nothing about *what it saw* and *what a pass would have looked like* has never been able to distinguish a real defect from an instrument that could not clear the subject. It was reporting a verdict it had no evidence for. INVALID says so. The gate did not just get worse — it got truthful.

**The failure mode to guard against is someone restoring the silent FAIL to make the dashboard green again.** That is EB-024 running backwards: `CLEAN` re-absorbing "unchecked", the push gate letting `None` fall through to `[OK]`, *"do not render grey tiers as green."* If a gate's INVALID share is uncomfortable, the fix is to add the witness, never to remove the requirement. A green board bought by deleting the check is the exact artefact this whole exercise exists to prevent.

Work through them in the order `tally()` says matters. A gate that cannot be given a witness is a gate that was never observing anything, and it should be deleted rather than restored.

**Step 2 — flip the consumer.** Once the two verdicts agree for a cycle, change the *caller* to branch on `Verdict`, and delete the legacy return. The raising `bool` catches anything you missed:

```python
if r.verdict is Verdict.FAIL:      raise_defect(r)
elif r.verdict is Verdict.INVALID: hold(r)      # NOT clean, NOT a pass
else:                              record(r.witness)
```

**Step 3 — counts.** Replace any pass-rate computation with `tally()`. It deliberately offers no `clean` total: whatever you do with INVALID has to be written down, so a denominator can never be acquired by accident. This is the same principle as your **Denominator gate** (*"no proportion renders unless `documents_examined_at_extraction_level` is a maintained counter, not a typed literal"*).

**Step 4 — optional.** If you want the admission rule, `registry.py` refuses to register a detector without a must-fire fixture, a must-be-silent fixture and an observation term. That enforces your own house standard mechanically: *"IMPLEMENTED requires code; SELF-TESTED requires a seeded failure that must fire AND a legitimate case that must not fire."*

---

## 4. Mapping onto your existing vocabulary

`Result` is deliberately compatible with the registry schema rather than a competing one.

| `detector_status_vocabulary_closed_set` | Harness equivalent |
|---|---|
| `IMPLEMENTED` | a registered `Check` |
| `IMPLEMENTED-NO-SELF-TEST` | **cannot exist** — `Registry.register()` raises without fixtures |
| `IMPLEMENTED-AS-RULE-NOT-CODE` | a mechanism with no `Check` |
| `PROPOSED` / `NONE-YET` | absent from `ALL_CHECKS` |
| `CANNOT-BE-AUTOMATED` | see `TAXONOMY.md` §4.1 — the holdings class |

Your `direction` / `consequence_direction` fields have no harness equivalent and should stay where they are. They are the measurement that produced Finding 2 and nothing here replaces them.

---

## 5. Two registry positions already moved to code

Take these if useful; they are self-contained and self-tested both directions.

- **`CHK014_FILTER_FIRED`** implements **P34** — *"a domain filter must be verified to have fired by inspecting the returned URLs, or the search is recorded as UNFILTERED. Never record a negative from a filtered search whose filter was not confirmed."* Fires on EC-001's shape.
- **`CHK015_HIT_COUNT_SANITY`** implements **P33** — *"hit-count sanity bound per query; a count above a declared expectation raises rather than returns."* Fires on EC-002 (471,547 hits from a discarded CJK query) and on the saturation form (a pattern matching 1009 of 1243 pages is degenerate, not the corpus uniform).

Both need a declared prior expectation. That is a real cost — someone has to say what they expect before running the query — and it is the same cost the protocol's rule imposes: state what the opposite would look like *before* the instrument runs.

---

## 6. What NOT to adopt, and why

- **Do not adopt `interrupt.py` as a replacement for your adjudication records.** It is a thin JSONL ledger, useful where a lane needs a hard stop it cannot walk past (your *"Decision required (do not guess)"* blocks). Your existing named-adjudication records are richer.
- **Do not treat the 15 green detectors as coverage.** `TAXONOMY.md` §4 lists what they do not reach, including one class — the holdings/entitlement mismatch — that no mechanical criterion touches at all, and where the only countermeasure is independent review by someone who did not frame the question.
- **Do not port the witness rule as written without reading `TAXONOMY.md` §4.8.** It is enforced on PASS only. That one-sidedness is the documented cause of Instance 5 in the synthesis-audit lane. If you fix it before I do, fix it in `Result.__post_init__` and run the full suite; it touches every detector's FAIL path.

---

## 3a. WIRING — the actual ask. You hold the hook; I have not touched it.

**Two files to copy, one block to paste.** I have deliberately not edited
`.githooks/pre-push` because `local_150089dd` holds it. This block follows the
pattern already in your hook — a named gate script, missing-script refusal, no
override — and slots in after the durable-artefact gate.

```bash
# ---------------------------------------------------------------------------
# HARNESS GATE. Runs the artefact-decidable detectors over the pages this push
# touches. Scoped for the same reason the regression check is: an unscoped walk
# is what made bypassing feel reasonable last time.
# ---------------------------------------------------------------------------
if [ -n "$CHANGED" ]; then
    HGATE="$REPO_ROOT/scripts/harness_gate.py"
    if [ ! -f "$HGATE" ]; then
        echo "[pre-push] harness_gate.py is missing." >&2
        echo "[pre-push] Refusing to pass a check that is not present." >&2
        exit 1
    fi
    set +e
    python "$HGATE" $(printf "$REPO_ROOT/build-artefacts/%s.json " $CHANGED)
    HG_STATUS=$?
    set -e
    if [ "$HG_STATUS" -eq 2 ]; then
        echo "[pre-push] Harness gate could not see (unfit registry or INVALID"
        echo "[pre-push] share above ceiling). That is not a pass."
        exit 1
    fi
    if [ "$HG_STATUS" -ne 0 ]; then
        echo "[pre-push] Harness gate FAILED. This gate has no override."
        exit 1
    fi
fi
```

Copy `harness_gate.py` to `scripts/harness_gate.py` and the `nafis_harness/`
package beside it (or onto `PYTHONPATH`). The gate needs one JSON artefact per
page; `nafis_harness/artefact.py` documents the fields it reads and ignores what
is absent.

### It has been proved to block, on real past defects — not synthetic ones

`test_build_gate.py` replays **13 defects this project actually made** and
asserts the gate exits 1 on each, and 0 on a clean artefact built from the same
shape. Per `gate_integrity.py`: *"A synthetic failing input proves a detector CAN
fire. It does not prove the detector DISCRIMINATES."*

TWILIGHT's composite in a mortality pool · ARNI's absence reason on a converted
page · `&minus;71.31` read as `+71.31` · an inert engine · a leaked sentinel ·
AZITHROMYCIN's bit-identical duplicate · a hazard ratio pooled with an odds
ratio · a cross-agent pool with no declared class · MD exponentiated ·
MAVACAMTEN's precision–sample mismatch · an orphan pooled result · a false NMA
claim. **17/17 tests pass.**

### Two things the gate says out loud on every run

**Twenty of thirty detectors run here. Ten are retrieval-scoped and cannot.**
They need an HTTP status, a click's post-state, a route log, a source document's
wording. The gate prints them by name every run, because silence from a check
that never ran must not read as coverage. Wiring those is a second job, at the
retrieval lanes, not at push time.

**A high INVALID share exits 2, not 0.** A gate that cannot see must not wave
things through — the failure mode your hook header already documents twice over.

### The number moves when you install it, not when I say so

`nafis_harness/wiring.py` **detects** whether a hook references
`harness_gate.py` and whether the script is present. The ledger's headline is
computed from that detection, so:

| | |
|---|---|
| today, measured | **15.7%** of logged mistakes would be caught by something that runs on its own |
| the moment this block is installed | **52.9%**, automatically, on the next run |

I cannot move that number by editing a field, and I have not tried to. If you
install it and the number does not move, the detection is wrong and I want to
know.

---

## 6a. For the page gates that just failed on the pooled estimate

That failure is the shape `CHK005_EXTERNAL_REFERENT` now handles, so take it with the interface below rather than the detector alone. The rule, in one line: **provenance is required to clear a row, never to convict one.**

```python
r = reg.run("CHK005_EXTERNAL_REFERENT", {
    "referent_name":        "PMC9726273 Cochrane SoF",
    "referent_document_id": "PMC9726273",              # required to PASS
    "row":                  {"pooled_ve": 91.1, "ci_low": 83.8, "ci_high": 95.1},
    "keys_under_test":      ["pooled_ve", "ci_low", "ci_high"],   # declare, don't infer
    "external_referent": {
        "pooled_ve": {"value": 91.1, "locator": "SoF row 1, effect column"},
        "ci_low":    {"value": 83.8, "locator": "SoF row 1, 95% CI"},
        "ci_high":   {"value": 95.1, "locator": "SoF row 1, 95% CI"},
    },
})
```

Three behaviours to expect, all of them deliberate:

- **A disagreement is reported whether or not you supply provenance.** If your extractor already keys the referent by field, you get your defects today, with no metadata work. This is the fix for the regression described in `HARNESS.md` D5 — an earlier version demanded provenance before any verdict and silently converted five real kills into five refusals.
- **Agreement without a document id or per-key locators is INVALID, not PASS.** A pooled estimate that "matches" a referent which cannot say where its numbers came from is the number-bag case: `{float(x) for x in re.findall(...)}` over the document will contain your value by coincidence. Agreement authenticates nothing.
- **A key you list in `keys_under_test` but do not source is INVALID, naming it.** No silent skips. If you genuinely cannot source a field, narrow `keys_under_test` so the omission is on the record rather than in the gaps.

`CHK006_IDENTITY_KEY` changed too: a **non-zero enrolment delta inside the tolerance band** is now INVALID rather than PASS, unless you pass `enrolment_delta_explained`. A tolerance says the instrument cannot resolve differences of that size; it must not therefore clear them. Same logic as your own `CHK002_DENOMINATOR_NOT_RANDOMISED` on PARAGON-HF.

---

## 7. Acceptance test for the migration

The migration is done when all three hold:

1. No call site in the corpus lane passes a `Result` to `if`, `and`, `or`, `not`, `bool()`, `all()` or `any()`. The raising `__bool__` proves this by execution, not by grep — **and a grep for it would be M3** (`grep "fatal"` matching `Nonfatal`).
2. Every gate that can report a clean state records a witness with a `locator` and an `opposite_would_be`, or reports INVALID.
3. `tally()` is the only source of counts, and the INVALID share is stated wherever a rate is quoted.

**Standing condition, borrowed from your own registry and applying equally here:** *"This file fails its purpose the moment Class B stops growing. A registry recording only other people's errors is the artifact it was built to prevent."* The same is true of this harness. If nothing new is ever added to `ALL_CHECKS`, it has stopped being used.
