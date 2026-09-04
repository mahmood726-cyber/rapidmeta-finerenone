# Writing a guard that refuses an irreversible action

A guard that stops an irreversible action is only as good as the argument it makes at the
moment it fires. Someone is always in a hurry when they meet it, and the guard is the only
thing in the room that knows what is about to be lost.

The best-argued guard in this repository is `ssot/do_not_rebuild.py`'s entry for
`ARNI_HF_REVIEW.html`. It is quoted here in full because the reasoning currently exists
only inside the one file that needed it.

## The reference

```
REFUSED: ARNI_HF_REVIEW.html is on the do-not-rebuild list.

  AUTHORED DOCMODEL MANUSCRIPT. The projector reproduces roughly 26% of it, so a rebuild
  replaces written argument with a projection. Standing instruction from Mahmood;
  ssot/manuscript_guard.py is the second line, not the first.   WHAT WOULD BE LOST, stated
  because a do-not-rebuild flag with no named cost is an instruction someone eventually
  overrules: roughly three quarters of this page is written argument that exists NOWHERE
  ELSE -- not on the object, not in any other page. It is the corpus's ONLY authored
  manuscript, and authorship is the property the whole programme is trying to acquire.
  A rebuild trades that for a projection.   AND IT IS NOT PURELY AUTHORED. Its F1000 prose
  carries [[certainty]] substitution tokens, already resolved and baked in -- a hand-written
  surface with generated holes. So a defect here can appear in prose as well as in a
  rendered cell, and a fix that only corrects the generated-looking surfaces leaves the
  prose asserting what the rest of the page withholds. On 2026-08-27 that was five published
  certainty levels, not the three a gate reading rendered cells found.   HOW TO MAINTAIN IT:
  edit it BY HAND. That is not the edited-not-rebuilt defect -- that defect is hand-editing
  a GENERATED artefact, where the next build silently reverts you. Hand-editing a
  hand-written surface is simply maintenance.

  This check runs BEFORE the build, so nothing has been written.
  To proceed deliberately for this one page:  REBUILD_ANYWAY=ARNI_HF_REVIEW.html <command>
  There is no blanket override.
```

## The five properties, drawn out

**1. Name the cost, in what quantity, and why.** Not "this page is protected" but *roughly
three quarters of this page is written argument that exists NOWHERE ELSE*. A quantity can be
checked and can be argued with. A prohibition can only be obeyed or overruled, and under
time pressure it gets overruled. The guard says why it states a cost at all: *"a
do-not-rebuild flag with no named cost is an instruction someone eventually overrules."*

**2. State what the reader would lose, not what the operator would break.** "The projector
reproduces roughly 26% of it" is a fact about the artefact. "Do not run this" is a fact
about the rules. Only the first survives contact with someone who has a good reason.

**3. Say the thing that makes the case HARDER, not easier.** *"AND IT IS NOT PURELY
AUTHORED"* — the guard volunteers the complication that a naive fix would trip over, and
names the date and the number it cost last time (2026-08-27, five published certainty
levels against the three a gate reading rendered cells found). A guard that only argues its
own side teaches the reader to discount it.

**4. State the maintenance route.** A guard that forbids without saying how to proceed
converts every legitimate need into a reason to override. *"HOW TO MAINTAIN IT: edit it BY
HAND"* — and then the distinction that makes that safe rather than reckless: hand-editing a
GENERATED artefact is the defect where the next build silently reverts you; hand-editing a
hand-written surface is simply maintenance.

**5. Offer a single-target override and no blanket one.**
`REBUILD_ANYWAY=ARNI_HF_REVIEW.html` names the page. There is no `REBUILD_ANYWAY=1`. An
override that must be spelled with the thing it destroys cannot be set once in a shell
profile and forgotten, and it appears in the shell history of whoever used it.

**6. Put the check before the write, and say so.** *"This check runs BEFORE the build, so
nothing has been written."* A reader who has just been refused needs to know whether they
are looking at a clean tree or a half-written one. Say which.

## Two failure modes this shape avoids

**A guard whose ordinary use requires its own escape hatch teaches the hatch.**
`.githooks/pre-commit-staging` records this about itself: `gates/` was missing from its
allowlist, so every commit touching a gate needed `STAGING_WIDE=1`, and *"the hatch is the
thing actually holding back `git add -A`."* If the legitimate path through your guard is the
override, you have not written a guard.

**A guard that cannot fire is indistinguishable from one that passed.** Measured on this
corpus: six of seven pre-push gates printed the word "clean" while examining an empty diff
scope, and every scratch-path dry run silently disabled the manuscript shrink guard because
writing to scratch removes the delivered copy the guard diffs against — it logged
`NOT_ASSESSABLE -- no delivered copy ... nothing to compare against, so this build is not
judged` and was read as approval. **A dry run is not a rehearsal of the real thing; it is a
rehearsal with a different set of guards, and the ones it disables are exactly the ones that
compare against the delivered artefact.** Enumerate which guards a scratch path disables
before trusting the run.

**And assert the refusal text, never the exit status.** `scripts/regression_check.py`
refuses with *"a gate that reads another directory's bytes is worse than no gate: it reports
PASS having never seen the files being pushed"* — and its exit code arrives as `0` through a
pipe. Anything reading `$?` records a pass. A success probe must name a property of the
artefact that could not exist if the operation had failed.

## Scope: a tree-scoped check makes concurrent authoring a serialisation problem

Measured on 2026-09-04, in one shared worktree with three lanes active.

`lint_gate_can_fail.py`, `audit_exclusion_by_absence.py --gate` and
`lint_instrument_declares_a_control.py` all scan the WORKTREE rather than the staged diff.
That is deliberate and it is right for what they check. But it has a consequence nobody
declared:

> **An unfinished instrument is not private. It is a gate failure for everybody else in
> the tree.**

A lane part-way through writing a new `audit_*` or `lint_*` script has, by definition, a
script that returns a verdict and cannot yet fail, or a negative guard without a control.
The tree-scoped linters see it and refuse **every other lane's commit**, whatever pathspec
that commit names.

What that cost, in one evening: three consecutive refusals of one lane's commits, caused by
three files it did not write —

    scripts/registry_read_sweep.py                 (cleared 18:35, re-edited 18:47)
    scripts/audit_manuscript_h3_sets_2026_09_04.py (created 18:38)

and it does not converge: the first block cleared at 18:35 and the next arrived from a file
created at 18:38. Waiting races whichever lane saves last.

**It is not concurrent WRITING that serialises a tree. It is concurrent PRESENCE.**

This was got wrong once, and the correction matters more than the original claim. The first
mitigation tried was to tell the writing lanes to stop. Both stopped; the tree went quiet
for a measured two minutes with zero non-mine writes; **and the commits were still refused.**
Holding a lane stops it adding NEW blockers. It does not remove the one it already left. The
blocking file had not been touched for sixteen minutes.

So the window in which a lane blocks every other lane does not run for the duration of its
edit. **It runs from the lane's first save until the file is finished or gone** -- and an
interrupted, abandoned or merely paused lane blocks the tree indefinitely.

That changes the mitigation completely:

    telling lanes to stop writing        -- useless
    telling lanes to keep unfinished
    work OUTSIDE the tree                -- the whole fix

**And the failure is invisible from the inside.** The refused lane had never opened any of
the three files it was refused for, and nothing in any refusal said whose they were. From
inside a lane there is no way to tell "my work is wrong" from "somebody else's unfinished
file is in the room" -- and the two call for opposite responses. That is precisely why
quoting the refusal and stopping was the only move that worked: retrying assumes the tree
will change, and assuming it is your own defect sends you to fix something that was never
broken. Both lead somewhere false.

**Credit where the gate is right.** `lint_gate_can_fail`'s rule -- a file that returns a
verdict and cannot fail -- is not pedantry. It is refusing to admit a new instance of the
single worst class measured on this corpus today: six of seven pre-push gates printing
"clean" over an empty scope, and ten dry runs silently unjudged by a guard. Being blocked
by a correct gate is a far better problem than the alternative, and the correct response is
to finish the instrument, not to route around the linter.

**So: concurrent authoring and concurrent committing cannot overlap in one worktree.**
Parallel lanes stop being a throughput win and become a serialisation problem, silently,
because the failure surfaces as somebody else's commit being refused for somebody else's
work-in-progress.

Two structural fixes, in preference order:

1. **A worktree per lane.** Authoring in one tree cannot then refuse a commit in another.
2. **Scope those three linters to the staged diff** rather than the tree. This narrows what
   they can catch and is a change to the gates themselves, so it is a deliberate decision
   rather than a convenience.

The interim rule, which is cheap: never point two lanes at one worktree, and announce every
edit to a file a running lane can see.

## Why this is worth writing down: quote the refusal, then stop

The tree-scoped problem above is not worth recording because it cost one lane three
commits. It is worth recording because of the shape of the failure:

> **A check that scans the whole worktree makes every lane's unfinished work into every
> other lane's failure, and none of them can see why.**

The lane that was refused had never opened any of the three files it was refused for. From
inside that lane, the repository simply stopped accepting commits, for reasons naming paths
it had no knowledge of. There is no amount of care within a lane that surfaces this. It is
only visible from outside, and only if somebody wrote down what the refusal actually said.

**And that is the point.** The reason this is understood tonight rather than filed as
flakiness is a single behaviour, applied consistently:

    quote the refusal verbatim, record the surrounding state, and STOP
    -- rather than retrying, overriding, or working around it

Retrying would have raced whichever lane saved last and produced nothing but a later
success. Overriding -- `STAGING_WIDE=1` on the wrong commit, `RM_ALLOW_MANUSCRIPT_SHRINK=1`,
a bumped baseline -- would have landed the work and destroyed the evidence in the same
motion. Instead the refusal text, the file mtimes and the timing were kept, and three
findings fell out of them that no amount of successful pushing would have produced:

  * a manuscript shrink guard was holding a two-week-old reader-facing false claim in
    place, because the thing behind it was broken -- found by being refused, not by passing

  * every scratch-path dry run had silently disabled that same guard, because writing to
    scratch removes the delivered copy it diffs against -- found by the guard firing on the
    real path after ten dry runs had not

  * tree-scoped pre-commit checks serialise concurrent lanes -- found by keeping the mtimes
    of files this lane had never opened

**So the template argues for two things, not one.** Write the guard so that its refusal
carries the argument. And when you meet somebody else's guard, treat its refusal as the
finding rather than the obstacle: a gate that refuses is telling you something that a gate
that passes never can.

## Checklist

- [ ] Names what is lost, with a quantity
- [ ] States the loss to the reader, not the inconvenience to the operator
- [ ] Volunteers the fact that makes the case harder, with a date and a number
- [ ] Gives the maintenance route, and distinguishes it from the defect it resembles
- [ ] Single-target override, spelled with the thing it destroys; no blanket flag
- [ ] Runs before the write, and says nothing has been written
- [ ] Can fail: has a known-answer case it must catch and a case it must NOT flag
- [ ] Refuses by text, and callers assert the text rather than the exit code
