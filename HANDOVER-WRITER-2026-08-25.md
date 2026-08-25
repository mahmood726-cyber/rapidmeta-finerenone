# Writer lane — handover, 2026-08-25

Supersedes `HANDOVER-WRITER-2026-08-24-0800.md`. Everything in §1 of that document is done.

**Read §6 before running any git command in this repo.** Multiple lanes share one index and
one working tree here, and it has now cost work in both directions.

---

## 1. THE HEADLINE MEASUREMENT — how much of our green is meaningless

`scripts/measure_check_controls_2026_08_25.py`, output
`outputs/check_controls_2026_08_25.json`. Two measurements, never one number.

| | |
|---|---|
| **population** | 226 check modules in `scripts/` (17 provers excluded so they cannot inflate it) |
| **MEASURE 1 — can it fail at all?** | can fail **175** · **CANNOT FAIL 51** · could not determine 0 |
| **MEASURE 2 — has it ever been *shown* to fail?** | has a control **24** · **NO CONTROL 151** (denominator 175) |
| **hook chain — what actually blocks a commit** | **37** modules · **24 of them have NO control** |

**The last line is the finding. Roughly two thirds of what blocks a commit in this repo has
never been shown to block anything.** A reachable `sys.exit(1)` that nobody has watched fire
is not a control, it is an assertion about the future.

### MEASURE 1 was already answered, and the answer has decayed

`scripts/baselines/gate_can_fail_baseline.json`, written 2026-08-20, found **45** and says in
its own words: *"NOT A CLEARANCE — each of these still cannot fail. **THE COUNT MUST NOT
RISE.**"*

**It has risen. 22 modules cannot fail that were not on that list** — among them
`audit_silent_truncation`, `audit_qualifications_reach_a_reader`, `audit_citation_decay`,
and `add_f1000_gate`, which is a file named *gate*.

**AND THE NET HIDES IT.** 45 → 51 is +6. The components are **+22 new**, −13 that now pass my
detector, −2 files deleted, −1 excluded as a prover by my scope. **I am not claiming 13 were
fixed:** my detector counts `sys.exit(<expr>)` as can-fail because an expression cannot be
shown to be zero, and the baseline may have required a literal. Some of the 13 may be
detector permissiveness rather than repair. **The 22 are not in doubt.**

### Why AST and not regex — this is the point, not a detail

The defect class being measured *is* vocabulary-bound matching. An instrument built from
`grep sys.exit` would miss `raise SystemExit(2)` and `return 1` from a `main()` invoked as
`sys.exit(main())`, and would score them cannot-fail. Exits are found by walking the parse
tree; unparseable modules are **reported, never scored**.

### The instrument was caught by the repo it measures, twice

**First:** `lint_instrument_declares_a_control.py` sits in the hook chain at **line 171** and
refuses any new corpus-wide instrument with no control. My first version declared known
positives in a private list and would have been refused — *an instrument built to measure
whether checks have controls, itself lacking one by the repo's own definition.*

**Second, and worse: my negative control had its polarity inverted.** I passed an
*uncontrolled* module and asserted it must not be uncontrolled. `require_controls` **refused
the entire run before printing a single count.** The count it withheld was correct. The
control vouching for it was not — and that difference is the whole exercise. Fixed by
reading the contract (`negative` raises when `actual == must_not_be`) rather than guessing:
the over-flagging direction is *"uncontrolled"*, so the negative must be a module that
genuinely **is** controlled.

Both controls now hold, on **different items**: positive reads `prove_our_gates_can_fail`
planting into `lint_control_chars`; negative reads `prove_criteria_fingerprint` against
`lint_criteria_fingerprint`.

---

## 2. THE PATTERN WORTH REUSING — a replacement check must be shown what the old one missed

Named here because it generalises to every replacement check we write, and it is the
strongest available demonstration that a new check does something the old one didn't.

> **Reconstruct the OLD broken check inside the new check's test, and REQUIRE it to miss the
> real, measured loss.**

In `scripts/plant_merge_nested_key_guard_2026_08_25.py`, test 1 rebuilds the old top-level-only
guard and asserts: wholesale replace drops 4 enrichment keys → **old guard reports 0** (it must
MISS) → **new guard reports 6**. Without that test, the new guard is just another first run that
looks like it works.

The full set is worth copying as a shape: **known positive** (old misses, new catches) ·
**repair works** · **derived values still update** (a no-op is not a fix) · **negative control**
(untouched input reports zero) · **exemption behaves** · **exemption is not a hole**. All six on
in-memory fixtures, so no corpus state can make them pass — the control-keyed-to-corpus-state
trap that has expired six controls in this project.

**The sentence for the record, which describes this whole week:**
*"true of a level it never touched, blind to the level it rewrote."*

---

## 3. ITEM 4a — DONE. The D5 position reached the objects

Commit **`fe54c7d3e`**.

`merge_rob_grade_into_objects_2026_08_19.py` promised *"REFUSES to run if the reserialised
object loses any key"* while comparing `set(obj.keys())` — the top level — and replacing
`obj["risk_of_bias"]` wholesale. **It passed every run it ever made.** Measured: **18 nested
keys across 8 of 9 targets** would have vanished silently, several of which
`paper_projector.py` renders.

Fixed both halves: `key_paths()` walks the whole tree; `nest_merge()` preserves unsupplied
keys; `by_outcome` exempted **by name** because it *is* the recomputed assessment and its
record keys legitimately change between runs.

**Run, with counts:** 9 objects merged, none refused, key paths **25,494 → 25,805 (+311)**,
**every object gained**, **zero** `risk_of_bias` keys lost. `d5_scope_rule` now on 8 of 9 —
the ninth, `ablation-af-review`, correctly has no `risk_of_bias` block.

### BUILT IS NOT SERVED, and this is exactly that distinction

> **The decided D5 position is now in the OBJECTS. It is on NO PAGE, and no reader can see
> it.** Nobody should read "it's in the objects" as "a reader can see it". The projector
> change (4b/4c) has not been written, no page has been rebuilt, and nothing has been
> verified on served bytes.

---

## 4. WHAT IS COMMITTED, AND ONE COMMIT THAT IS MIS-ATTRIBUTED

| commit | what |
|---|---|
| `2f7f524c6` | ITEM 1.3 — converter-derived-effect enumeration + plant harness |
| `6d579f2f7` | ITEM 1.2 — `_d5` declares its position; declaration reads both layers |
| `464d3101c` | previous handover |
| `fe54c7d3e` | **ITEM 4a** — merge guard repair + 6-of-6 plant + 9 merged objects |
| `79aa1b553` | **NOT MINE.** Another lane's commit, which swept up my two staged files |

**`scripts/measure_check_controls_2026_08_25.py` and `outputs/check_controls_2026_08_25.json`
are committed inside `79aa1b553`**, a commit whose message is about pre-2005 registration
labels and says nothing about them. Content verified identical to the working copy, so
**nothing is lost** — but the message is wrong and mine never landed. The intended message is
preserved at
`F:\claude-temp\claude\F--rapidmeta-ssot-shell\09b3a8ae-99bc-499a-854b-602193b3f505\scratchpad\cm-controls.txt`
and its substance is §1 above.

---

## 5. WHAT DID NOT RUN, AND WHY — the honest gap

**The five overnight hunts I was briefed to run never ran.** At 00:10 another lane committed
`973985c14`, *"overnight adversarial hunts, aimed at the gates rather than the pages"*, whose
hunt 1 is the same brief almost verbatim. Launching mine would have duplicated all five. I
raised the collision, asked how to sequence it, **and then waited ~14 hours for an answer
that never came.**

> **The lesson, now a standing instruction: if blocked on the orchestrator and a defensible
> non-overlapping path exists, TAKE IT and say which you chose.** Waiting cost the night.

**The non-overlapping axis is now running** — `outputs/hunt_gates_pass_good_pages_2026_08_25.json`,
briefed to take a gate, take a page the gate **passes**, and find the defect that gate exists
to catch present on that page in a form the gate does not match; biased toward pages believed
**good**, because the week's biggest finding came from checking a page nobody suspected. It
runs under retry-until-artefact-exists. **If that file is absent or not valid JSON, the hunt
did not run — treat it as absent, not as "no defects found".**

**Do not read or report the other lane's `outputs/hunt_*` artefacts.** They are not this
lane's and cross-lane reporting of unverified results is how folklore starts.

---

## 6. THE OPERATIONAL HAZARD — read before any git command

`F:\rapidmeta-ssot-shell` is a worktree of `F:\rapidmeta-finerenone`, and **multiple lanes
work in it simultaneously, sharing one index, one working tree and one git identity.**

- **Never `git commit` without a pathspec.** On 2026-08-24 another lane's file was staged into
  my set; committing without a pathspec would have put it under my message.
- **And it cuts both ways.** On 2026-08-25 `79aa1b553` swept **my** staged files into **their**
  commit (§4). A pathspec protects your commit from their files; it does **not** protect your
  files from their wide commit. **Stage and commit in one step, and confirm from `git log`.**
- **Never `git stash`** — it takes the other lanes' uncommitted work.
- **`/tmp` resolves to `F:\claude-temp`, the SHARED root.** Every `/tmp/...` path is shared
  while looking private. Use the per-lane scratchpad; this lane's is
  `F:\claude-temp\claude\F--rapidmeta-ssot-shell\09b3a8ae-99bc-499a-854b-602193b3f505\scratchpad`.
- **`STAGING_WIDE=1`** is required for anything under `outputs/`, plus `git add -f` where
  `.gitignore` covers it.
- **A commit can block for minutes** on another lane's `index.lock` while its pre-commit hook
  runs. The Bash tool times out at 2 minutes and SIGTERMs your git, so the commit does not
  land. Launch in background, wait on the lock, **read `git log`** — never an exit code.
- **A lock file is an artefact; a running process is a fact.** One lane's `git.exe` died at
  its own timeout while its hook kept running orphaned under PID 1, holding the lock
  legitimately. Check `ps -ef | grep -E "[p]re-commit|[g]it.exe"` before calling a lock stale,
  and never clear another lane's lock.

---

## 7. NEXT ACTIONS, in order

1. **Read the hunt artefact** (§5) if it landed; verify its quotes against the files before
   believing any of them. Two of six probes elsewhere were wrong on first run.
2. **Fix what the control measurement found**, highest value first: **the 24 hook-chain gates
   with no control**. These block commits and have never been shown to block anything. The
   mechanism already exists — `prove_our_gates_can_fail_2026_08_23.py` covers 8 gates by
   planting a defect into each one's input and requiring a non-zero exit. Extend it.
3. **The 22 new cannot-fail modules** violate a baseline that says the count must not rise.
   Each is either a triage tool wearing the wrong name (rename to `*_triage.py`, as four were
   on 2026-08-19) or a real gap. Decide per module.
4. **ITEM 4b** — declare the D5 rule in Methods citing §8.7. Text already exists as
   `D5_POSITION` / `d5_scope_rule`; **do not retype it**. 31 of 155 objects carry a
   `risk_of_bias` block. Render in the `risk_of_bias` section projector,
   `ssot/paper_projector.py` ~line 2471.
5. **ITEM 4c** — render `our_selection_declared_not_rated` beside the estimate. **Give it its
   own table, NOT the risk-of-bias table** — it is explicitly not a risk-of-bias judgement and
   filing it there would misdescribe it as one.
6. **ITEM 4d** — build, then **verify on served bytes**. Only `main` deploys.
7. **ITEM 2 (the 480 legacy conversion) NOT STARTED.** Pilot of five, cardiology and ID first,
   through every gate, report before converting a sixth. Do not port the legacy app forward or
   patch its HTML — build canonical objects and project them. The "full trial data" wording is
   withdrawn; cite the field survey (`registry id 137/137, arms 58/137, per-arm counts 59/137,
   year 12/137`).

---

## 8. KNOWLEDGE THAT WOULD OTHERWISE DIE WITH THE SESSION

**Four D5 key spellings**, so a single-spelling selector sees at most 51 of 87:
`D5_selection_of_the_reported_result` 51 · `D5_selection_of_result` 29 ·
`D5_selection_of_reported_result` 4 · `D5` 3. **87 records over 24 objects.**

**`endpoint_rank_in_its_own_trial` is written two ways** — bare token (`PRIMARY`, 23 rows) and
sentence (`the trial's own primary composite endpoint`). Match the bare token **exactly**:
`"SECONDARY -- this trial's only primary outcome is …"` contains "primary" and is not one.
This cost three separate defects in one session — the marker list, the rank matcher, and the
harness written to test them.

**The rank lives on TWO layers**, not interchangeable: `inputs.trials[].by_outcome[]` (what the
assessor walks, 22 rows) and `results.by_outcome[].per_trial[]` (what the page renders, 49
rows). They agree on all 14 where both are present; **0 disagreements.** Any new instrument
must read both.

**The RoB 2 lane's FIX 1 is retired** by Mahmood's D5 decision and must not be re-implemented
by a later reader of `HANDOFF_TO_WRITER_LANE.md`. Its other four fixes are untouched and still
owed.

**Laptop node was offline** (`100.80.183.43 mahmood … offline, last seen 1h ago, tx 780 rx 0`),
so no second Codex node. Local Codex is alive — verified by a real exec returning
`OK Codex, GPT-5 family`, not by a status check.

---

## 9. RE-VERIFY THIS LANE'S WORK IN TWO MINUTES

    python scripts/measure_check_controls_2026_08_25.py          # both controls must hold first
    python scripts/plant_merge_nested_key_guard_2026_08_25.py    # expect 6 of 6
    python scripts/plant_converter_derived_enumeration_2026_08_24.py   # expect 5 of 5
    python scripts/plant_d5_selection_declaration_2026_08_24.py        # expect 4 of 4

The last two restore what they touch and assert restoration by sha256 read back from disk;
baselines `9f5b2206b1ee86ff` (`ssot/ablation-af-review`) and `ff3f3b4344d04a51`
(`ssot/sglt2-hf`). All are pinned to their target's **properties**, not its state, so they fail
loudly rather than passing vacuously if later work removes what they exercise.
