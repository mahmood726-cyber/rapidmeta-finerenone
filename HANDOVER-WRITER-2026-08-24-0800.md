# Writer lane — handover, 2026-08-24 ~08:00

Wound down deliberately for machine memory pressure, not at a natural end of work.
**Nothing was mid-write.** Working tree clean on every path this lane touched; no
processes of this lane running; no stash taken (see §6 — a stash here would take
another lane's work).

`HEAD` = **`6d579f2f7`** on `fix/ssot-tabbed-shell`. **3 commits ahead of `origin/main`.**
`origin/HEAD` → `refs/remotes/origin/main`, and **main is the Pages deploy ref**, so:

> **NOTHING FROM THIS SESSION IS LIVE.** Not pushed, not merged, not deployed.
> Verified: the D5 content reaches **zero bytes** of any built page (§3), so there is
> nothing that *should* be deployed yet either. Do not report any of it as delivered.

---

## 1. WHAT IS COMMITTED

| commit | what |
|---|---|
| `2f7f524c6` | ITEM 1.3 — the converter-derived-effect enumeration + its plant harness |
| `6d579f2f7` | ITEM 1.2 — `_d5` declares its position; the selection declaration reads both layers; its plant harness |

`bfa402e22` between them is **another lane's** commit, not this one's.

Files: `scripts/enumerate_converter_derived_effects_2026_08_24.py`,
`scripts/plant_converter_derived_enumeration_2026_08_24.py`,
`scripts/plant_d5_selection_declaration_2026_08_24.py`,
`scripts/rob2_assess_2026_08_19.py`,
`outputs/converter_derived_effects_2026_08_24.json`,
`evidence/2026-08-19-batch1/rob2.json`.

## 2. WHAT IS UNCOMMITTED

**Nothing of this lane's.** Two paths are dirty/untracked and are **NOT** this lane's —
do not commit them:

- `evidence/withholding_asked_baseline.json` — modified, mtime **2026-08-23 10:57**,
  before this session. Pre-existing worktree state, not crash damage.
- `scripts/audit_prisma_nma_block_2026_08_23.py` — untracked, present at session start.

## 3. THE NUMBERS, so they are not re-derived or misquoted

**ITEM 1.3 enumeration.** Denominator **178** render-facing `per_trial` rows, 50 topics.
Two axes, never summed into one figure.

| axis 1 — whose NUMBER | n | axis 2 — whose CHOICE | n |
|---|---|---|---|
| point computed here | 80 | selection by this review | 16 |
| point printed, interval computed here | 1 | the trial's own primary | 33 |
| as printed | 66 | could not determine (no rank field) | 129 |
| could not determine (no field) | 31 | | |

**Declaration population: 97 of 178 rows, 35 topics.** Unclassifiable on both axes:
**24 of 178** — a missing field to name, not a sentence to invent. 123 of 178 were
classified by prose fallback; the enumerator prints that number every run.

**ITEM 1.2 D5.** 29 records, 8 topics. Declaration states after the both-layer fix:
`COULD_NOT_DETERMINE` **4**, `NO_SELECTION_BY_THIS_REVIEW` **18**,
`SELECTED_BY_THIS_REVIEW` **7**, `LAYERS_DISAGREE` **0**.
Before the fix: 15 / 8 / 6 / 0.

**Measured, so it is not re-asked:** the withdrawn position-B sentence reached **4**
stored records (all `iv-iron-hf`) and **0** bytes of `IV_IRON_HF_REVIEW.html`
(7,056,385 bytes; 0 occurrences of the string, of `D5_selection_of_result`, and of the
5.2 slug).

## 4. NEXT ACTION, in order

**4a. Repair `scripts/merge_rob_grade_into_objects_2026_08_19.py` — this is the blocker.**
It is the only path from `rob2.json` into the objects. It **replaces**
`obj["risk_of_bias"]` wholesale, and its key-loss guard compares **TOP-LEVEL keys only**,
so everything nested under `risk_of_bias` is destroyed silently and the guard passes.

Measured, not assumed — running it today would drop **18 nested keys across 8 of its 9
target objects**:

- `SECOND_ASSESSOR_2026_08_21` on seven (`ablation-af-heart-failure`,
  `ablation-af-medical-therapy`, `alirocumab-lipid`, `attr-cm-review`,
  `bempedoic-acid-review`, `early-rhythm-control-af`, `iv-iron-hf`)
- **eleven** on `sglt2-hf`: `ONE_ASSESSOR_ONLY`, `SECOND_ASSESSOR_2026_08_21`,
  `THE_EMPEROR_TRIALS_DO_NOT_MASK_THEIR_OUTCOMES_ASSESSOR`,
  `THE_SAME_TRIAL_IS_JUDGED_DIFFERENTLY_IN_THE_TWO_POOLS`, `assessed_per`,
  `assessed_utc`, `restored_2026_08_21`, `restored_framing_2026_08_21`,
  `sources_NOT_read`, `sources_read`, `superseded_state_2026_08_21`
- `ablation-af-review` has no `risk_of_bias` block; the merge would create one.

`paper_projector.py` renders several of these (`SECOND_ASSESSOR*` at ~line 2500,
`ONE_ASSESSOR_ONLY` at ~2594). Fix: nest-merge rather than replace, and make the
guard compare keys **recursively**. Plant it — the guard must be watched to fail on a
nested loss before it is trusted.

**4b. Then ITEM 1.1** — declare the D5 rule in Methods citing §8.7. The rule text
already exists as `D5_POSITION` / `d5_scope_rule` in
`scripts/rob2_assess_2026_08_19.py` and in `rob2.json`; do not retype it. Population:
**31 of 155** objects carry a `risk_of_bias` block (all 31 have `.tool`, so all 31
render the section). Render it in the `risk_of_bias` section projector
(`ssot/paper_projector.py` line ~2471).

**4c. Then ITEM 1.4** — render `our_selection_declared_not_rated` beside the estimate.
It currently exists only in `rob2.json`, at **record** level. **Give it its own table,
NOT the "Risk-of-bias judgement for every included result" table** — it is explicitly
not a risk-of-bias judgement and filing it there would misdescribe it as one.

**4d. Then build, and verify on SERVED bytes**, polling to a stated condition. Only
`main` deploys.

**4e. ITEM 2 (the 480 legacy conversion) NOT STARTED.** Pilot of five, cardiology and
ID first, through every existing gate, report before converting a sixth. Two standing
constraints from Mahmood: do not port the legacy app forward or patch its HTML — build
canonical objects and project them; and the "full trial data" wording is withdrawn, cite
the field survey (`registry id 137/137, arms 58/137, per-arm counts 59/137, year 12/137`).

## 5. IN-SESSION KNOWLEDGE THAT IS NOT IN THE COMMITS

**Four D5 key spellings in the corpus**, so any selector keyed to one sees at most 51
of 87: `D5_selection_of_the_reported_result` **51**, `D5_selection_of_result` **29**,
`D5_selection_of_reported_result` **4**, `D5` **3**. Total **87 D5 records over 24
objects** — the 29 in `rob2.json` are only the batch1 subset. The projector's domain
loop is generic (`_ROB_DOMAINS.get(dn, dn.replace("_", " "))`) so all four render, but
anything *counting* them must handle all four.

**The corpus writes `endpoint_rank_in_its_own_trial` two ways** — a bare token
(`PRIMARY`, 23 rows) and a sentence (`the trial's own primary composite endpoint`).
Match the bare token **exactly**: `"SECONDARY -- this trial's only primary outcome is
the proportion of participants with adverse events"` contains the word "primary" and is
not one. This cost three separate defects in one session — the marker list, the rank
matcher, and the plant harness written to test them.

**The rank lives on TWO layers** and they are not interchangeable:
`inputs.trials[].by_outcome[]` (what the assessor walks) and
`results.by_outcome[].per_trial[]` (what the page renders). Coverage differs sharply —
per_trial 49 rows with a rank, inputs 22. They agree on all 14 records where both are
present; **0 disagreements**. Any new instrument must read both.

**`results.by_outcome[].per_trial[]` is the render-facing estimate population** (178
rows, 50 topics) and carries `derivation`, `how`, `derived_here`, `as_posted`.
`inputs.trials[].by_outcome[].effect` is a different, smaller population (170 effect
blocks of 209 rows). 407 trials exist but only 209 have a `by_outcome` child — most
trials' `by_outcome` is empty, which is the RoB 2 lane's selector defect #1.

**The RoB 2 lane's FIX 1 is retired by Mahmood's decision** and this must not be
re-implemented by a later reader of `HANDOFF_TO_WRITER_LANE.md`. It predicted four
`iv-iron-hf` records moving SOME_CONCERNS → HIGH via 5.2 = Y/PY. Under position A, 5.2
is not answerable about the trial from what we hold, so **no record moves**. Its other
four fixes (FIX 2 `_d2`/`_d3`/`_d4` are not RoB 2; FIX 3 `NO_INFORMATION` is not a
domain judgement; FIX 4 the 11 unsupported GRADE downgrades; FIX 5 the Table 4 gap)
**are untouched and still owed.**

**All 33 pooled points carry no `derived_from`** and were deliberately excluded from the
enumeration: a pool is by construction a number no trial printed, and the page already
says so. Do not re-open this as a gap.

**`ssot/` was clean at session start and is clean now** (0 modified). The ~613 dirty
files at session start were built HTML, pre-existing. Do not sweep them.

## 6. THE OPERATIONAL HAZARD — READ THIS BEFORE ANY GIT COMMAND

**Two other lanes are working in `F:\rapidmeta-ssot-shell` at the same time.** This
directory is itself a worktree of `F:\rapidmeta-finerenone`, and the concurrent lanes
share **one index, one working tree and one git identity**.

- **Never `git commit` without a pathspec.** A plain commit here stages and commits the
  other lanes' files under your message. This happened: `HANDOVER-PAUSE-2026-08-24.md`
  was staged into this lane's set. Always
  `git commit -F <msgfile> -- <path> <path>`.
- **Never `git stash`.** It would take the other lanes' uncommitted work.
- **`STAGING_WIDE=1` is required** for anything under `outputs/` (the add-all guard),
  and `git add -f` for `outputs/` paths that `.gitignore` covers.
- **A commit can block for many minutes** on another lane's `index.lock` while its
  pre-commit hook runs. The Bash tool times out at 2 minutes and **SIGTERMs your git,
  so the commit does not land**. Launch the commit in the background, wait on the lock
  file, and then **read `git log` to confirm** — never an exit code.
- **A lock file is an artefact; a running process is a fact.** One lane's `git.exe` died
  at its own timeout while its pre-commit hook kept running orphaned under PID 1
  (`lint_primary_by_position.py`), holding the lock legitimately. Check
  `ps -ef | grep -E "[p]re-commit|[g]it.exe"` before concluding a lock is stale, and do
  not clear another lane's lock.

## 7. HOW TO RE-VERIFY THIS LANE'S WORK IN ONE MINUTE

    python scripts/enumerate_converter_derived_effects_2026_08_24.py
    python scripts/plant_converter_derived_enumeration_2026_08_24.py   # expect 5 of 5
    python scripts/plant_d5_selection_declaration_2026_08_24.py        # expect 4 of 4

Both plants restore what they touch and assert the restoration by sha256 read back from
disk. Both are pinned to their target's **properties**, not its state, so they fail
loudly rather than passing vacuously if later work removes what they exercise. The
second one also restores `evidence/2026-08-19-batch1/rob2.json`, because the assessor
**merges** into it and a plant that left it holding planted values would poison every
later reader.

Expected baselines: enumeration `9f5b2206b1ee86ff` on
`ssot/ablation-af-review/ablation-af-review.json`; declaration `ff3f3b4344d04a51` on
`ssot/sglt2-hf/sglt2-hf.json`.
