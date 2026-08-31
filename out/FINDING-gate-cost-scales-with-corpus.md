
---

## ADDENDUM 2026-08-30 — it is FOUR gates, not one, and the pattern is uniform

Measured live, during a commit staging **13 files**, by sampling the pre-commit process chain
at 60-second intervals:

| gate | what it scopes to | what it therefore reads |
|---|---|---|
| `sweep_mojibake.py --gate` | the corpus | ~1,478 pages, ~1.5 GB |
| `lint_control_chars.py` | `git ls-files -z` **AND** `os.walk(REPO)` | every tracked file *and* every untracked one |
| `lint_escape_hazards.py` | `os.walk(REPO)` | the whole tree |
| `lint_refusal_contradicted_by_its_own_section.py` | `glob("*_REVIEW.html")` | every review page, each ~1.1 MB |

**NOT ONE of the four reads `git diff --cached`.** The staged set is available to every one of
them, for free, and none asks for it.

### Why four instances change the argument

One slow gate is a cost. Four gates that independently chose corpus scope is a **default**:
each author, writing a guard for a real defect, reached for "scan everything" because it is the
formulation that cannot miss. The reasoning is sound in isolation and compounds to a hook where
committing 13 files costs four full-corpus passes.

⚠️ **And the cost is not the real danger.** It is that a hook this slow *manufactures the
pressure to bypass it* — which is the exact failure this run has already recorded once, when a
two-minute timeout produced a reach for `--no-verify` against a gate that had not objected.
**A gate expensive enough to tempt an override is, over enough commits, a gate that gets
overridden.** Its cost is therefore a correctness property, not a convenience one.

### What to change, and the one that must NOT

* `lint_refusal_contradicted_by_its_own_section.py` and `sweep_mojibake.py` should scope to
  **staged paths** — a page not in the diff cannot have acquired a new defect in this commit.
* `lint_control_chars.py` and `lint_escape_hazards.py` should scope to **staged text files**,
  keeping the full-corpus form available as an explicit periodic sweep.
* ⛔ **`ssot_net_deletion_check.py` must stay diff-scoped as it already is** — it is the one
  that fired tonight and found three lost blocks. Nothing here argues for weakening a gate;
  the argument is that a gate should read *what changed*, which is both cheaper AND more
  precisely what the gate is claiming to check.

### Evidence trail

* `lint_control_chars.py` observed at 12.23 s -> 13.44 s CPU over 40 s, then completed.
* `lint_refusal_contradicted_by_its_own_section.py` observed at 3.88 s -> 6.86 s over 60 s.
* `git commit` itself flat at 0.47 s throughout: correctly blocked on its children, which is
  why a single sample of the parent reads as "hung".

**NOT IMPLEMENTED. Filed only.** Changing a gate while it is adjudicating your own commit is
the conflict of interest this project has a register entry about.

---

## ADDENDUM 2 — MEASURED INVENTORY, AND THE COMPOUNDING THAT MAKES IT A DESIGN DEFECT

**Measured on this worktree, 2026-08-30, during a commit staging THIRTEEN files.**

| gate | what it globs | files | bytes read |
|---|---|---|---|
| `sweep_mojibake.py --gate` | the corpus | ~1,478 pages | ~1.5 GB |
| `lint_refusal_contradicted_by_its_own_section.py` | `glob("*_REVIEW.html")` | **1,427** | **712.3 MB** |
| `lint_control_chars.py` | `git ls-files -z` **AND** `os.walk(REPO)` | 14,713 + 14,888 | up to **2.0 GB** |
| `lint_escape_hazards.py` | `os.walk(REPO)` | 14,888 | up to **2.0 GB** |
| `audit_exclusion_by_absence.py --gate` | every `scripts/*.py` | ~hundreds | small |
| `ssot_net_deletion_check.py` | **`git diff --cached`** | 13 | trivial |

⇒ **Roughly 6 GB read to commit thirteen files.** One gate in the chain reads the staged diff.
It is also the only one that found a real defect tonight.

### ⛔ THE COMPOUNDING, WHICH IS THE ACTUAL ARGUMENT

The gates run **in series, and a refusal restarts the chain from the beginning.** This commit is
on **ATTEMPT 4**. Each refusal cost a full re-run of every gate that had already passed:

| attempt | refused by | gates re-run from scratch |
|---|---|---|
| 1 | net-deletion (1st in chain) | 0 wasted |
| 2 | staging guard (2nd) | 1 |
| 3 | exclusion-by-absence (~7th) | 6, including all four corpus passes |
| 4 | — | 6 again |

**So the cost of a refusal is proportional to how many gates already passed.** A defect caught
EARLY is cheap; a defect caught LATE costs the entire corpus scan again, and again for each
subsequent fix.

⚠️ **This punishes precisely the behaviour the suite exists to produce.** An author who fixes a
refusal pays the full chain again. An author who reaches for `--no-verify` pays nothing. **The
incentive gradient points at the bypass**, and it steepens with every gate added — which means
the suite gets *more* bypass-prone exactly as it gets more thorough.

⭐ **That is the finding: it is not that the gates are slow. It is that a serial chain of
corpus-scale gates makes honesty expensive and bypass free.**

### What follows

1. **Scope to `git diff --cached`.** Four of the six can. A page not in the diff cannot have
   acquired a defect in this commit.
2. **Order cheap-and-diff-scoped gates FIRST**, corpus sweeps last. Then a refusal from a cheap
   gate costs nothing to retry, and only a genuinely rare late failure pays the full price.
3. **Run the corpus sweeps on a schedule, not per commit** — they are checking for drift the
   commit did not cause.
4. ⛔ **Do not weaken any gate.** Every one of the three that refused tonight was RIGHT, and the
   first prevented shipping a page missing a judge-named feature. The argument is entirely about
   *what they read*, never about *what they check*.

**NOT IMPLEMENTED. Filed only** -- changing a gate while it adjudicates your own commit is the
conflict of interest this project already has a register entry about.
