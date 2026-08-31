# Committing in this worktree

Read this before your first commit here. It is short because it is about two mistakes, and
both of them cost hours on 2026-08-30/31.

**Several agents share ONE index in this worktree.** That single fact causes everything
below.

---

## 1. Always commit with an explicit pathspec, in ONE command

```sh
git add -- path/a path/b && git commit -F msg.txt -- path/a path/b
```

**A bare `git commit` commits whatever the index holds — not your work.** Another lane's
`git add` may have run thirty seconds ago, and its files are now in your commit under your
message.

That is not hypothetical. Commit `48cd999bc` ("land the reader cards…") is a 32-file
no-pathspec commit that swept **nine modules belonging to a different lane** —
`claims.py`, `plant_claims.py`, `growth_guard.py`, `screening_ledger.py`,
`page_format_v1.json`, `check_page_format.py` and three more. Nothing was lost and neither
lane did anything careless; the attribution simply went to whoever committed first.

**Chain the add and the commit.** `git commit -- <paths>` accepts only files git already
TRACKS, so anything new needs `git add` first — and *that add is the moment your files enter
the shared index and become sweepable by anyone else's bare commit*. Keep the window to one
command. Never add, then think, then commit.

---

## 2. A pathspec does NOT protect you from someone else's broken file

This is the half people get wrong, and it is why "just use a pathspec" is not the whole rule.

**The pre-commit lints run over the WHOLE TREE, not over your committed paths.** So a file
you have never touched can refuse your commit.

Real example: a 21-path commit was refused by `scripts/lint_gate_can_fail.py` naming
`scripts/audit_included_trial_design.py` — not in the pathspec, not that lane's file. Another
lane spent an hour reading the same refusal as lock contention. And one of the five files
refusing everybody turned out to belong to the lane doing the diagnosing:
`check_page_format.py` returned a verdict and could never fail, so an unfailable checker was
blocking every lane's commits for hours.

    A pathspec protects you from committing someone else's WORK.
    It does not protect you from someone else's BROKEN FILE.

**If a lint refuses you, read WHICH FILE it names before concluding anything about your own
commit.** A refusal that arrives with a specific, correct-looking error string about a real
rule is the most durable kind of wrong diagnosis available.

Check before you spend 50 minutes:

```sh
python scripts/lint_gate_can_fail.py    # exit 0 = clear to commit
```

---

## 3. Timing: what "no lock" and "a lock" actually mean

**The pre-commit chain runs 30–77 minutes.** Standalone timing: 3164s. Budget for it.

`index.lock` is taken at the END, for the index write — not held through the hook chain. All
of these states were observed in one night and **every one of them was ALIVE**:

| lock | for how long | verdict |
|---|---|---|
| absent | the whole hook chain | alive |
| present, mtime FROZEN | 21 minutes | alive |
| present, size GROWING | 0 → 1.6 MB in two minutes | alive |

⇒ **Presence, absence, mtime and size are each insufficient, in both directions.** One lane
read a growing lock as another lane camping the index; then nearly deleted a frozen one as
debris while a healthy 27-file commit was writing through it. A clear-the-lock authorisation
had already been issued. What stopped it was enumerating processes **by command line**:

```powershell
Get-CimInstance Win32_Process -Filter "Name='git.exe'" |
  Where-Object { $_.CommandLine -like "*commit*" } |
  Select-Object ProcessId, CreationDate, CommandLine
```

`git.exe` alone tells you nothing. The command line tells you *whose* commit it is and *what
paths* it holds, instantly.

**And use a probe you have checked against a known-alive case.** A `ps -W | grep -c` probe
returned 0 for a process `Get-CimInstance` showed alive — the weaker probe was wrong, not the
process, and it nearly caused the deletion a second time. *Only the process table settles it,
and only a probe you have calibrated.*

---

## 4. If you must wait for the lock, do not poll with git

```sh
# WRONG: contends for the lock, and manufactures the traffic you are measuring
while ! git add -- x.py; do sleep 12; done

# RIGHT: stat the file, which is read-only and contends with nothing
while [ -e "$GIT_DIR/index.lock" ]; do sleep 5; done
git add -- x.py && git commit -F msg.txt -- x.py
```

Two lanes ran `git`-based retry loops at 12s and 13s against one index for hours, each
reading the other's traffic as evidence about the other lane. **A self-generated signal read
as a fact about someone else.** Bound the wait and give up rather than hammer.

---

## 5. Staging guard

`.githooks/pre-commit-staging` refuses paths outside `ssot/`, `scripts/`, `.githooks/`,
`evidence/`, and top-level `md|json|txt|yml|yaml`. `outputs/`, `findings/`, `protocols/`,
`tests/` and `docs/` need `STAGING_WIDE=1`, set deliberately.

It checks **WHERE paths are, not HOW you staged them** — staging by explicit pathspec does
not clear it.

---

## 6. The stat-poll works — measured

The `[ -e index.lock ]` wait in §4 is not theory. On 2026-08-31, after roughly four hours in
which two lanes' git-based retry loops never once landed a commit, the first stat-poll
attempt acquired the lock cleanly:

    lock clear 03:40:33
    ADD OK     03:40:40

Seven seconds from the lock clearing to the add landing, and it cost the index nothing while
it waited. **Bound the wait, fire once, give up rather than hammer.**
