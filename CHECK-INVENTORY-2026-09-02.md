# Every check, crossed with: is it INVOKED · by WHAT · can it FAIL · when did it LAST FAIL

Measured 2026-09-02 against `origin/main` `13238c15c` and this worktree.
Regenerate: `python scripts/audit_check_liveness.py --json CHECK-LIVENESS.json`

Three pieces of machinery in this repo were built, committed, and never fired: `rebuild_guard.py`
(written for the exact defect that recurred the next day), four files named `*_gate.py` with no
reachable non-zero exit, and a Docker CI step gated on a path that never matched, inside a job
that went green every time. Each was AVAILABLE. None was OPERATIVE.

---

## The numbers

| | count |
|---|---|
| Python files enumerated (tracked set, walked — not grepped for names) | **1,283** |
| …**can fail** (a non-zero exit is reachable) | **664** |
| …no verdict path at all | 619 |
| …unparsable, so not assessed | 0 |
| Of the 664: **invoked** by a hook, CI, runner or script | **514** |
| Of the 664: **named by nothing that runs** | **150** |
| …of those, named only in prose (documented, not wired) | 87 |

Invocation surfaces (a check may have several): `REGISTRY 1162 · PY 611 · HOOK 51 · CI 9 · SHELL 3`.

**Only 51 checks can block a commit.** Everything else is advisory, whatever its name says.

## The fourth column has no answer, and that is the finding

**`when did it last fail` is UNRECORDED for all 664.** Nothing in this repo stores that a check
ran, let alone what it returned. So the column cannot be filled for a single check, and the
ranking the column was meant to produce cannot be computed at all.

> A check that has never been observed to fail is not thereby passing. It is unobserved, and
> from outside the two are identical.

This is the same shape as the three precedents: each was *believed* to be working because
nothing had ever reported otherwise. Until a run-ledger exists, every "this is wired" claim in
this repo rests on the first three columns only.

## The sharpest row: 18 checks whose NAME is a promise nothing keeps

Of the 150 that nothing invokes, **18 are named `gate_*`, `lint_*`, `audit_*`, `control_*` or
`test_*`** — they can fail, and no hook, workflow, runner or script calls them:

```
scripts/gate2_corrections_survive_regeneration.py
scripts/gate_acquired_claim_shows_its_history.py
scripts/gate_screening_row_has_registration_id_2026_08_26.py
scripts/gate_stored_estimate_declares_provenance_2026_08_27.py
scripts/lint_interactive_layer_2026_08_26.py
scripts/lint_scope_derivations_agree.py
scripts/lint_split_children_are_reachable.py
scripts/audit_page_sidecar_agreement.py
scripts/audit_trial_label_identity.py
scripts/control_label_audit.py
scripts/measure_check_controls_2026_08_25.py
scripts/plant_merge_nested_key_guard_2026_08_25.py
scripts/test_delegated_job_produced_output_2026_08_24.py
propagate_v16_features.py
```

The repo already enforces *a file named `*_gate.py` must be able to FAIL* (`lint_gate_can_fail.py`,
hook-wired). **This is that rule's missing twin: it must also be CALLED.** A gate that can fail
and is never invoked is the more dangerous of the two, because it passes every audit that asks
whether it works.

## Reach, not coverage — stated per measurement

- **33 files were NOT scanned for citers** (`OVERSIZE`, >1.5 MB — the largest is
  `IV_IRON_HF_REVIEW.html` at 7.3 MB). A citer inside one would be invisible, so *150 uninvoked*
  means **uninvoked by the surfaces actually read**.
- **`git log --all -S` TIMED OUT at ten minutes** on this repo. Any absence it reports is a reach
  figure. Capabilities that moved, were renamed, or live on another branch are **not** ruled out.
- The pre-existing chain manifest at `F:\rapidmeta-xsurface\gates\WIRED_REPO_CHECKS.json` is
  ground truth for the push chain and was NOT re-derived here:
  `pre_push 24 · ci_only 8 · red_not_yet_a_gate 12 · timeout_needs_scoping 4`.
  **Twelve checks are red and not yet gates; four are known to time out.**

---

# The fifth column: does this capability ALREADY EXIST on `origin/main`?

`python scripts/capability_index.py --rev origin/main --find "what it should do"`

In one night three lanes rebuilt something main already ships — a guideline coverage map, an
HTA / Summary-of-Findings projector, a metafor oracle — and two lanes wrote the same stdout lint
within minutes of each other. Every one was diagnosed as *"the thing is missing"* from a stale or
partial view, and two of the three were **better on main** than in the rebuild.

> That is not four mistakes. It is one missing capability: no inventory of what exists.

**A name-keyed index would have missed every one.** `sof_card` does not contain "HTA";
`etd_coverage_card` does not contain "guideline". Searching by the name of the thing you are about
to build returns nothing, and returns it confidently. So the index is keyed on the **prose** a
symbol carries, and is scored on description overlap weighted by term rarity — never on name.

### It ships with controls that have known answers

| query | expects | provenance | result |
|---|---|---|---|
| "guideline coverage map evidence to decision" | `projectors_sof.py::etd_coverage_card` | development | FOUND |
| "HTA tab summary of findings table" | `projectors_sof.py::sof_card` | development | FOUND |
| "refuse a commit that net-deletes content from an SSOT object" | `ssot_net_deletion_check.py` | **HELD OUT** | FOUND |

Cases 1–2 were used while building the scorer and are development data — fitting a scorer to the
examples you tuned on measures nothing. **Case 3 was added after the scorer was finished and has
never been tuned against. It is the only one whose result is evidence.**

### The controls caught four real defects in the index itself

1. **Blob misalignment.** Reading `git cat-file --batch` by offset desynchronised, attributing one
   file's contents to another path — with total confidence and nothing in the output to show it.
   Now requested **by SHA**, and the reply's SHA is compared to the requested one, so a desync
   raises instead of being indexed.
2. **Silent truncation of the exact signal.** Module prose was appended *last* and the field cut at
   1,200 chars, so on `sof_card` the module docstring — the only place the word HTA appears — was
   trimmed off the end. Each part is capped separately now, module prose first.
3. **Equal term weighting.** The right answer tied with every module containing "table",
   "summary" and "findings" — most of a meta-analysis repo — and lost the tie. The word carrying
   the meaning was "hta". Rarity is the signal; equal weighting discards it.
4. **Inherited prose swamping own prose.** Carrying the module docstring onto every symbol made
   `_e` and `_blocks` tie with `sof_card`. Own and inherited prose are now scored apart.

### And one finding about `main` itself

`ssot/projectors_sof.py` on `origin/main` begins:

```
import re
# -*- coding: utf-8 -*-
"""The HTA tab as a SUMMARY OF FINDINGS table, and the Guideline tab as an
EVIDENCE-TO-DECISION COVERAGE MAP...
```

**One `import` above the docstring, and it is no longer a docstring** — just a discarded string
expression. `ast.get_docstring()` correctly returns nothing, and every doc-driven tool goes blind
to the sentence that says what the module does. That is precisely how a shipped capability becomes
invisible to a search for it, and then gets rebuilt by someone who looked and honestly found
nothing. The index therefore reads **all** top-level prose, not only formal docstrings.

### What this index cannot do, on the object rather than discovered later

- It indexes **one revision**. A capability living only on another branch is not here.
- It indexes **prose**. Excellent code with an empty docstring is invisible to it, and will be
  reported absent when it is merely undescribed.
- Absence means **absent from what was searched**. Every run prints its own reach.

---

# The newest entry: a check for the mechanism that fired twice in one night

`scripts/lint_pathspecless_commit.py` — **wired first in `.githooks/pre-commit`.**

Two near-misses tonight, one mechanism, and its only defence was a paragraph being relayed
by hand to seven lanes:

1. **Capture.** Four lanes stage into one index. `git commit -m "..."` with no pathspec
   commits *every* staged entry — including files another lane staged seconds ago and has
   not finished. At 02:00 that index held **52 staged paths** from several lanes at once.
2. **Inverse deletion.** A commit built on a private `GIT_INDEX_FILE` leaves the shared index
   one commit stale, so it stages the **inverse** of what was just committed — a deletion of
   the file just added — which the next pathspec-less commit from any lane silently applies.

Both are one shape: **a pathspec-less commit commits a shared object that nobody owns.**

### How it knows — measured, not assumed

git hands the pre-commit hook a different `GIT_INDEX_FILE` per invocation. Measured in a
throwaway repo:

| invocation | hook sees | |
|---|---|---|
| `git commit -m x` | `.git/index` | **shared — hazard** |
| `git commit -m y -- b.txt` | `.git/next-index-22232.lock` | private — safe |
| `git commit -a -m z` | `.git/index.lock` | **shared — worse** (`-a` stages every modified file first) |

A basename of `next-index-*` means git built a temporary index for a pathspec, so the commit
cannot reach anyone else's work. No command-line parsing, no guessing.

### It fires only where the hazard exists, and it ships with controls

Trigger: **more than one worktree shares the index AND something is staged.** In a
single-worktree repo a pathspec-less commit is normal, and refusing it would be the
refuse-everything failure this repo has already paid for once.

The selftest builds a **real two-worktree repo and runs real commits through this file as the
hook** — nothing is mocked, because the subject is a hook firing during an actual commit:

```
REFUSES  pathspec-less `git commit -m ...`  -> rc=1
ALLOWS   `git commit -- b.txt`               -> rc=0
ALLOWS   SHARED_INDEX_OK override            -> rc=0
```

Override, with the reason on the record: `SHARED_INDEX_OK="why" git commit ...`
The refusal names every path it would have captured, so the fix is visible rather than
looked up.

---

# Two columns every row needs, and neither was there

| column | values | why it matters |
|---|---|---|
| `LANGUAGE_SCOPE` | `python-ast` · `bytes` · `any-text` | a clean result is clean **only for that population** |
| `ENFORCEMENT` | `MECHANISABLE` · `CONSEQUENCE-CAUGHT` · `RULE ONLY` | separates a wired rule from one whose *outcome* is wired from one that is only written down |

**Why `LANGUAGE_SCOPE`.** `lint_recurring_traps.py` detects `unanchored_substring` and finds
100 instances on main. One hour after wiring it into the commit path, its author killed four
processes with a PowerShell filter `-like '*refs/heads/main*'` — a pattern selecting on a
string several lanes share — and reached into other lanes' pushes. The lint reported clean on
that code **because that code was never in its corpus**. The detector is language-scoped; the
defect class is not. That is the denominator problem one level up: not *did the scan miss a
file*, but *was the language ever in the population*. Now declared on the lint itself.

**Why `ENFORCEMENT`.** Tonight's pair:

- *A hook and every script it invokes land in one commit* — **MECHANISABLE**
  (`lint_hook_references_resolve.py`, hook-wired).
- *A retry loop must freeze its CONTENT, not its filenames* — **CONSEQUENCE-CAUGHT**. No
  pre-commit hook can see how a loop was written. Rule 1 catches its worst outcome, which is
  why rule 1 is the one wired. Naming a rule as unenforced beats implying it is enforced.

### Correction to that rule as first written

I froze a list of **paths**. Insufficient: `git update-index --add` re-reads file **contents**
each attempt, so a frozen path list still commits different bytes every retry.
**A frozen path list is not a frozen commit — freeze the tree.** Mechanically: `git write-tree`
once before the first attempt, then re-parent that same immutable tree object on each retry.

### And the fresh-clone read-back caught a check that would have been inert

`lint_pathspecless_commit.py` passed its selftest here and **failed it in a clean clone**. Its
git queries ran against `_ROOT`, derived from `__file__` — not the repository the commit is
happening in. This shared worktree happens to have several worktrees and staged files, so the
refusal fired regardless of what the temporary test repo contained: **green for the wrong
reason.** Cloned fresh, `_ROOT` was a one-worktree repo with nothing staged and the check
passed everything.

> A check that reads a different repository than the one being committed to is inert, and it
> is inert in the direction that looks like success.

Fixed to resolve the repo from `cwd` (where git runs a hook), and re-verified **in the clone
that exposed it**. Nothing local could have found this; only the read-back did.

---

# The frozen-tree rule was wrong, and it nearly deleted another lane's work

The rule as first written — *a retry loop must freeze its CONTENT, not its filenames* — was
corrected once to **freeze the tree**. That correction is right about idempotency and
**dangerous about everything else**, and the implementation proved it within minutes.

**A tree is a full snapshot of the whole repository.** `git commit-tree <frozen-tree> -p
<new-parent>` does not merge: it declares that the repository looks exactly like the frozen
snapshot. Every file the new parent added since the snapshot is **deleted**, silently, with
no conflict and no warning — the commit looks like a normal three-file change in its message
and is a mass deletion in its diff.

Measured, not hypothesised. Attempt 1 lost the race; attempt 2 re-parented the same frozen
tree onto the new main and produced commit `2b3a9d0f0`:

```
frozen tree  1a7b641c6   scripts/methodology files: 18
current main 9c309906d   scripts/methodology files: 20

git diff --stat 9c309906d 2b3a9d0f0
  scripts/methodology/aact_sweep.py            221 ------
  scripts/methodology/aact_sweep_result.json   744 ------
  .../FINDING-ingestion-not-retrieval.md       160 ++---
  6 files changed, 145 insertions(+), 1063 deletions(-)
```

**1,063 deletions of another lane's work, in a commit whose message describes three files.**
It did not land only because it lost the race too. That is luck, not a control.

### The correct form: freeze the BLOBS, not the tree

| freeze | idempotent? | safe against a moving parent? |
|---|---|---|
| file **paths** | no — `update-index` re-reads contents each attempt | yes |
| whole **tree** | yes | **no — deletes everything the new parent added** |
| **blobs** of your own files | yes | yes |

Capture each file's blob once with `git hash-object -w`, then on every attempt: `read-tree`
the **current** main, `update-index --cacheinfo` each frozen blob onto its path, `write-tree`,
`commit-tree`. The base is always current; only your own paths are pinned.

> **A retry must pin what it is CHANGING, never what it is CHANGING IT AGAINST.** Freezing
> the base is how a retry turns into a revert.

`ENFORCEMENT: RULE ONLY` — no pre-commit hook can see how a retry loop was written. What a
hook *can* see is the consequence, and a mass deletion is exactly what
`ssot_net_deletion_check.py` already refuses. That is why the consequence-caught column
matters: the rule is unenforceable and its worst outcome is already gated.

---

# `SCOPE: DIFF` vs `SCOPE: TREE` — the column that decides where a check belongs

Measured on the hook/shell-wired checks:

| scope | count |
|---|---|
| **TREE** | 23 |
| **BOTH** | 4 |
| **DIFF** | **1** |
| UNKNOWN (classifier cannot tell) | 26 |

**Exactly one hook-wired check is diff-scoped. At least 27 scan the tree** — a floor, not a
total, because 26 are unclassified.

That single ratio explains two separate problems that were being diagnosed apart:

1. **The chain runs 30–77 minutes** (one gate 178s, another 486s). A pre-push chain that
   takes an hour is not a gate, it is a **queue** — and a queue makes every *wall*
   indistinguishable from a *race*. Five lanes spent hours believing they were losing races
   to a moving main while one gate was refusing outright. The slowness is not incidental to
   the misdiagnosis; **it destroys the evidence that would separate the two explanations.**

2. **A tree-scanning gate frozen against a baseline penalises the most up-to-date lane and
   exempts the most stale one.** A lane 304 commits behind sails through, because the
   offending file is not in its tree. A fully merged lane is stopped for work it did not do,
   and nothing in its own diff explains why — the hardest failure of all to attribute.

> This lane pushed successfully **because it had integrated least.** That is the argument
> for this column in one sentence.

### The remedy is one change

**Tree-scanning gates belong in CI on `main`**, where the tree is the thing being judged and
one machine pays the cost once. **Diff-scoped checks stay in the hook**, fast, judging only
what the lane actually did. The column tells you which is which; today the hook holds 27 of
the wrong kind and 1 of the right kind.

---

# When did it last fail: `51 ANSWERABLE / 613 NO EVIDENCE EITHER WAY / 664 total`

`scripts/check_ledger.py` records a refusal at the one place that already knows both the gate
and the verdict — `_refuse` in the pre-commit hook. That makes the column answerable for the
**51 hook-wired** checks, from the moment it was wired.

For the other **613 there is no evidence either way.**

> They are **not** "613 dead". *No recorded failure* is not the same fact as *cannot fail*,
> and collapsing those two is the folding error corrected six times in this file already.
> The indistinguishability **is** the finding: it is exactly how `rebuild_guard.py`, four
> unfailable `*_gate.py` files, and a CI step gated on a path that never matched all went
> unnoticed while everything around them stayed green.

An empty ledger means **nothing has been observed in this working copy** — never that nothing
has failed. It starts empty in every fresh clone.
