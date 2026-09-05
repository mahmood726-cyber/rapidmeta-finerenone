# This branch is unattributable by git, 2026-09-05

MEASURED, not asserted. Walking every commit between the live remote tip
`16da44a1caad0474dd9c8c82dd3ab74d273e8993` and `harness/rebuild-20260903` HEAD:

    git log --format='%an' 16da44a1c..HEAD | sort | uniq -c
      35  mahmood789

**All 35 commits carry one git author.** Two different lanes wrote them on the same day, in
the same worktree, and `%an` cannot tell them apart. Neither can `%ae`, `%cn` or `%ce`.

## The only thing that separates them is a trailer nothing enforces

    git log --format='%h %(trailers:key=Co-authored-by,valueonly)' 16da44a1c..HEAD
      23  Co-Authored-By: Claude Opus 5 (1M context)
       9  Co-Authored-By: Claude Opus 4.8 (1M context)
       3  NO TRAILER AT ALL

Tonight alone, 3 commits came from one lane and 9 from the other, interleaved by minutes:

    22:31  Opus 5     fix seven of eight gate defects on three served objects
    22:09  Opus 4.8   exporter: do not emit a pool the store declared non-poolable
    22:05  Opus 4.8   apixaban-vte: correct provenance migration to typed tiers
    21:52  Opus 5     harness: add the producer and the verifier of the relabelling
    21:48  Opus 5     pick up another lane's in-flight work: outcome-verdict relabelling
    21:19  Opus 4.8   apixaban-vte: migrate 7 legacy provenance strings to the tier schema

## Why this is a defect and not bookkeeping

**A convention held by habit is not a control.** Three commits in the range already carry no
trailer, so the convention has already failed three times without anyone noticing, and
nothing in the repository would have reported it. The failure mode is silent by
construction: a commit with no trailer looks exactly like a commit whose author simply is
the git author.

The concrete risk was live on this branch tonight. One lane's work was **picked up and
committed by the other** (`edb7856ab`, "pick up another lane's in-flight work"), and one
lane **reversed a decision the other had recorded three hours earlier** (`a857b7a0d`
supersedes `b024ad089`'s `NOT_YET_RECORDED` with typed tiers). Both were legitimate and both
were disclosed in their messages -- but that disclosure was prose written by the lane doing
it, not a fact the repository can check. A push carrying work its author had not finished
would be indistinguishable, afterwards, from a push carrying work they had.

This is the same family as the defects this corpus already refuses: an identity that cannot
be resolved from the artefact. A page name is not an artefact identity; a git author is not
a lane identity.

## A cheap enforcement, NAMED AND NOT BUILT

Not built here, deliberately -- it is not on the path to the push and a guard written in
passing is how guards acquire the wrong scope.

A `commit-msg` hook of a few lines: assert the message contains a `Co-Authored-By:` trailer,
and refuse with the list of recognised lanes if it does not. `.githooks/commit-msg` already
exists (262 bytes) and is the natural home. It must ship with the negative test that this
repo requires of every gate: a message WITH a trailer must pass, a message WITHOUT one must
be refused, and the second half must be shown to fire against the pre-fix hook -- a plant
that passes post-fix proves nothing unless it fired pre-fix.

Whether the trailer is the right identity at all is a separate question worth asking before
building: it names a MODEL, not a lane or a session, and two sessions of the same model
would still be indistinguishable. A session id would be the stronger key.

## What was verified rather than trusted

`b0fc2ddc9` was in the ancestry of a push this lane was preparing, and was authored by the
other lane. It was read rather than pushed on trust. It reverses `46aa168e9`: instead of
teaching CHK018 to tolerate a pool, it stops the exporter emitting one the store declared
`poolable: False`, records the omission visibly, and states "CHK018 is left untouched." That
is fixing at the source rather than at the detector, and it is the stronger of the two.
It stands.

**WHEN A CHECK AND AN ARTEFACT DISAGREE, THE ARTEFACT IS THE FIRST SUSPECT, NOT THE CHECK.**

---

## SECOND DEFECT OF THE SAME FAMILY: TWO LANES, ONE FILE, TWO SERIALISERS

`ssot/apixaban-vte-prophylaxis/apixaban-vte-prophylaxis.json` can no longer be rewritten
safely by either lane. Measured: **no combination of `json.dumps` indent, `ensure_ascii`,
line ending and trailing newline reproduces it byte-for-byte** -- the closest is 427 bytes
adrift. The cause is visible at the first divergence, byte 41607:

    on disk : "provenance": {"tier": "DERIVED_HERE", "formula": "the unique integer k suc...
    any dump: "provenance": {
               "tier": "DERIVED_HERE",
               "formula": "the uniqu...

The other lane's `a857b7a0d` wrote the seven provenance blocks as **compact inline objects**
inside a file whose every other block is `indent=1`. The file is now mixed-format, and any
lane that loads-modifies-dumps it will reformat several hundred lines it did not intend to
touch -- burying whatever it did intend to change.

**TWO LANES WRITING ONE FILE WITH DIFFERENT SERIALISERS LEAVE A FILE NEITHER CAN SAFELY
REWRITE.** This is the attribution defect in another form: the artefact carries no record of
which convention governs it, so the next writer must either discover the mismatch or destroy
the formatting. It was discovered here only because a round-trip fidelity guard ABORTED the
edit rather than proceeding -- without that guard the change would have shipped as a
several-hundred-line diff with three real lines inside it.

The safe substitute, used here: edit as TEXT, then prove the result by diffing the PARSED
objects before and after. This edit was accepted only on that evidence -- **2 keys changed,
both `outcome_definition`; 18 keys added, all under the restoration record; 0 keys removed.**

A format assumption that holds for two files is not a format rule, and in a multi-lane
worktree it is not even stable for one file over time.

---

## DELEGATION: A WRAPPER REPORTED SUCCESS FOR A JOB THAT NEVER STARTED

Two Codex jobs were delegated on 2026-09-05 -- a corpus-wide reach measurement and an
arm-identity investigation. Measured outcome:

    wall clock          ~40 minutes each, ~80 minutes total
    descendant CPU      227s (evolocumab) + 245s and counting (reach)
    model tokens        ZERO. Neither job ever reached the model.
    artefacts on disk   ZERO of 2
    reported exit code  0

The evolocumab job's real ending, from its log:

    execution error: Io(Custom { kind: Other, error: "windows sandbox:
      orchestrator_helper_exit_nonzero: setup helper exited with status Some(143)" })
    [exited with code 0]

Status 143 is SIGTERM: the delegating timeout killed a setup helper that was still
initialising after 40 minutes. Every CPU-second went to
`codex-windows-sandbox-setup.exe` walking a large worktree.

**THE LESSON IS NOT THAT THE VENDOR IS UNRELIABLE. IT IS THAT THE WRAPPER REPORTED EXIT 0
FOR A JOB THAT NEVER STARTED** -- the same failure shape as every other unearned success
caught tonight: a staging refusal that returned 0, an untracked-pathspec miss that returned
0, a push refused by five gates that returned 0. A status code is not a result, and here it
was not even evidence that the work began.

Three signals disagreed throughout, and only one was right:

    wrapper CPU     flat at ~6s for 40 minutes  -> would have read DEAD
    log growth      frozen after 90 seconds     -> would have read STALLED
    descendant CPU  12 -> 48 -> 245, climbing   -> BUSY, and busy on setup, not on the task

**Killing on either of the first two would have destroyed live work; trusting either would
have wasted the budget.** Only walking to the leaf distinguished them.

### The practical rule for the next handoff

The same arm-identity question that was delegated and never started was then answered
DIRECTLY in **two registry reads**, using tooling already loaded in this session and 118
registrations already cached on disk. Earlier the same evening, the SPIRE-AI arm-identity
question -- which two people had characterised as an unsettleable conflict between two
recorded facts -- took **one** read.

**DELEGATION IS CHEAP FOR WORK THAT DOES NOT NEED THIS TREE AND EXPENSIVE FOR WORK THAT
DOES.** A liveness probe requiring no repository access returned `OK GPT-5` in under a
minute on the same machine, the same hour, with the same binary. The cost is not the model;
it is standing up a sandbox over the worktree. Before delegating, ask whether the task needs
the repository. If it does, the round trip may exceed the task.
