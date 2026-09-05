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

### THE NUMBER THAT DECIDES THE NEXT DELEGATION, AND NEITHER JOB'S SUMMARY CONTAINS IT

    two jobs, wall clock          ~80 minutes
    two jobs, descendant CPU      ~470 CPU-seconds
    MODEL TOKENS PRODUCED         ZERO

**Not zero output -- zero TOKENS.** Both jobs spent their entire budgets in sandbox setup
and neither ever reached the model. A job that produced a wrong answer would at least have
consumed the resource it was delegated for; these consumed 80 minutes of the resource they
were delegated to AVOID.

**THAT FIGURE IS OBTAINABLE FROM NEITHER JOB'S SUMMARY.** Both would have shown a clean
exit; one reported `exit code 0` on an explicit sandbox execution error. The cost had to be
assembled by hand from the descendant-process walk and the log tail -- the same two places
every true answer came from tonight. **If the decision to delegate again rests on a job's
own report of itself, it rests on the one artefact that cannot show this failure.**

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

---

## THE ROUND-TRIP GUARD'S SCOPE WAS THE DEFECT, NOT ITS LOGIC

A byte-fidelity guard was built tonight after a JSON edit nearly rewrote 115,094 bytes to
change nine lines, and it fired correctly twice more. **IT WAS NEVER EXTENDED BEYOND JSON.**

Editing the two harness gates through Python heredocs used text-mode `open(p, 'w')`, which
on Windows silently translates `\n` to `\r\n`. Both gates became whole-file rewrites:

    registration_chronology_gate.py   825 added lines,  158 of them real
    refusal_reads_outcome_groups_gate.py  698 added lines, 111 of them real

Caught before the commit only because the added-line count did not match what had been
written. **A GATE DIFF NOBODY CAN READ IS A GATE CHANGE NOBODY REVIEWED** -- and this would
have landed looking like a rewrite of two safety checks, on the night two safety checks were
changed. Restored with binary-mode I/O; the diff then read 158/5 and 111/0, identical to the
ignore-whitespace figures.

**A FORMAT RULE HELD FOR ONE FILE TYPE IS NOT A FORMAT RULE.** The guard's logic was right
the whole time; its SCOPE was the defect. Read bytes, write bytes, and verify a no-op
round-trip is byte-identical before editing ANY text file -- .py, .md, .txt, .html, not only
.json. On Windows the failure is silent and invisible in the editor.

## AN INSTRUMENT THAT CANNOT EXCLUDE ITS OWN ACTIVITY WILL REPORT ITSELF AS A FINDING

Three times on 2026-09-05, one shape:

1. A hook scan reported three new `pre-push` hooks. They were the shells running the scan;
   its own filter string contained the words it searched for.
2. A truncation sweep printed a "dropped text" column naming the 75 mg outcome. That was a
   property of `min(longer, key=len)` picking the shorter of two candidate titles, not
   evidence about the object -- an output column that looks like a finding and is a property
   of the sort order.
3. Harness notices saying a gate file "changed on disk" were read as evidence of a
   concurrent lane. They were reports of this lane's own heredoc writes, and a mixed-
   authorship warning was raised on that basis and then retracted: `INVERTED AND DISCLOSED`
   is in HEAD at line 370, original design from 78cf9d4e1, and every uncommitted hunk in
   both gates was this lane's.

**Before an instrument reports a finding, it must be able to exclude its own activity from
the population it is measuring.** Case 3 was raised in good faith and was still wrong -- and
raising it stopped a push on a false premise rather than pushing through an uncertainty,
which is the correct direction to be wrong in.

---

## TEN UNEARNED SUCCESS REPORTS IN ONE DAY, AND THE TENTH WAS THE PUSH

Every one returned `exit code 0` for an operation that did not happen:

     1  a commit refused by .githooks/pre-commit-staging
     2  a commit whose pathspec matched no tracked file
     3-7 five pre-push hooks stranded in sandbox/setup, wrappers alive, work never done
     8  a push refused by five harness gates
     9  a delegated Codex job that never reached the model at all
    10  THE PUSH OF 2026-09-06 00:12, refused by check_page_format.py

The tenth is the one that matters most, because it is the operation everyone would most
want to trust. The command returned 0; the last line of its log read
`error: failed to push some refs`; and `ls-remote` showed the branch ref had not moved.

    THE PUSH IS NOT DONE WHEN THE COMMAND RETURNS. IT IS DONE WHEN ls-remote SHOWS THE
    REF MOVED. THE MERGE IS NOT DONE WHEN main MOVES. IT IS DONE WHEN THE SERVED BYTES
    CARRY THE CHANGE. Two probes, both on the artefact, neither on a status.

---

## A GATE ACQUIRES REACH BEYOND THE FAILURE IT WAS WRITTEN FOR

Four gates in this repository show one behaviour, and it is invisible until something
legitimate trips it.

    .githooks/pre-commit-staging      refused out/ and figs/ -- tracked source directories
                                      outside its declared set. Its OWN HEADER records this
                                      happening three times to itself: gates/ added
                                      2026-09-02, tests/ and outputs/ added 2026-09-04, each
                                      after blocking ordinary work.
    refusal_reads_outcome_groups      flagged the machinery of retraction: quoted
                                      withdrawals read as live claims.
    registration_chronology           same defect, disabling its own `not claims` guard from
                                      the inside, so its stated remedy was unreachable.
    SSOT NET-DELETION CHECK           refused a one-key removal from PAGE_MAP.json, a
                                      ROUTING TABLE. Its premise -- "an SSOT object is an
                                      ACCUMULATING record ... registry reads, withdrawal
                                      reasons, sources, risk-of-bias verdicts" -- is simply
                                      not true of a filename-to-path map.

**A GATE WRITTEN AGAINST A REAL FAILURE ACQUIRES REACH BEYOND THAT FAILURE, AND THE EXCESS
REACH IS INVISIBLE UNTIL SOMETHING LEGITIMATE TRIPS IT.** In every case the gate's premise
was sound and its population was wrong. None of them was a false alarm in the ordinary
sense: each correctly reported what it saw.

Two consequences worth separating:

  * The excess reach is only ever discovered by a legitimate action being blocked, so it is
    found at the worst moment -- when someone is trying to land correct work, under time
    pressure, and the cheapest response is to reach for an override.
  * A gate's SCOPE therefore needs the same evidence its LOGIC does. Three of these four
    were scoped by enumerating a set of directories or fields; none was scoped by measuring
    the population it would actually meet.

## OVERRIDE VERSUS PRESCRIBED PATH, AND THE TEST THAT SEPARATES THEM

`SSOT_ALLOW_NET_DELETION` was used once, on 2026-09-06, to unmap MALARIA_VACCINES_SSOT.html.
That is NOT the same act as suppressing a check, and the distinction is worth stating
because both look like environment variables:

    DOES THE MECHANISM RECORD THE ACT, OR HIDE IT?

`SSOT_ALLOW_NET_DELETION` requires a written reason and preserves it -- the gate's own words
are "If this is deliberate, re-run with a reason on the record." It is the prescribed path
for a deliberate deletion, and using it for the purpose it was built for, with a true
reason, is compliance. Contrast `RM_ALLOW_MANUSCRIPT_SHRINK`, which suppresses a loss check:
that one required its premise to be separately disproven -- 10 of 10 refusals present in the
built bytes, zero numeric loss -- BEFORE it could honestly be used.

## ELEVEN UNEARNED SUCCESS REPORTS

The count is now eleven. The eleventh: a commit refused by the SSOT NET-DELETION CHECK
returned `exit code 0`, HEAD unchanged, both paths absent from HEAD. Two consecutive
operations in one hour -- a push and a commit -- each refused by a gate and each reporting
success.

## A LOG IS NOT A LESSON

`.githooks/pre-commit-staging` is the only place in this repository where a gate recorded
its own scope being wrong -- and it recorded it THREE TIMES, each faithfully, each with its
reasoning:

    gates/   added 2026-09-02  "a guard whose ORDINARY use requires its own escape hatch
                                teaches the hatch"
    tests/   added 2026-09-04  "works against the thing this repo most needs more of"
    outputs/ added 2026-09-04  "a count whose denominator cannot be committed beside it is
                                a proxy nobody can re-check"

    ⭐ IT IS THE ONLY PLACE WHERE A GATE RECORDED ITS OWN SCOPE BEING WRONG THREE TIMES,
      AND IT STILL DID NOT GENERALISE THE LESSON TO THE FOURTH.

On 2026-09-05 it refused `out/` and `figs/` -- the fourth instance of one cause, arriving as
a surprise to a system that had already written that cause down three times.

**NOBODY WAS CARELESS AND NO INFORMATION WAS MISSING.** Three incidents were logged
accurately with their reasoning intact. What never happened was someone READING the three
together and extracting the pattern -- that this guard's declared set lags the repository's
real source directories, and will keep doing so.

    A RECORD NEEDS A PERIODIC READING, NOT ONLY FAITHFUL WRITING. Writing an incident down
    prevents nothing by itself; it only makes the prevention POSSIBLE for whoever reads
    across the entries. Three entries in one file, unread as a set, cost a fourth incident
    on the night the repository could least afford one.

The same shape appears in the reach measurement, and it is the same distinction the gates
were making about themselves:

    A GATE'S DECLARED SET IS A SCOPE. THE FILES IT WILL ACTUALLY BE HANDED ARE A CORPUS.

`6, 62, 52, 1, 2 of 155` is what five gates could see. `85 of 155` is what the corpus holds
that none of them can. We spent a night measuring scopes rather than corpora, and the gates
were doing it to themselves.
