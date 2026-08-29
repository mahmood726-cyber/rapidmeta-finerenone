# Correction: my E7 finding was wrong in its central claim, and a ruling was made on it

**Raised 2026-08-29, before acting on the ruling it produced.**

## What I reported

That `scripts/lint_question_is_a_question.py` **"PASSED a live instance of the defect it
exists to catch"**, that *"a comparison against absent reference text always passes"*, and
that it was therefore presenting a false all-clear.

That produced a ruling: **mark it INOPERATIVE and withdraw every prior pass.**

## What is actually true

**The gate discloses its own reach, loudly, on every run.** Its output ends:

```
topics compared against their own trials' registry text   30
questions that are a COPIED REGISTRY FIELD                 2
not compared (reported, never silently skipped)          125
baseline (known, awaiting a human decision)                2
```

And for the specific topic I accused it of passing, it records the reason by name:

> `icosapent-lipid-auto-full-review` — *"no registration records cached for this topic's
> trials"*

**It never claimed to have checked icosapent.** It counted icosapent among the 125 it says
it could not compare, and said why. The line I quoted as damning — *"not compared (reported,
never silently skipped)"* — is the gate doing exactly what I have argued all night that gates
must do.

It is also better defended than I said. It carries an **exit-2 refusal** for the case where a
known-bad baseline topic becomes uncomparable, on the stated grounds that *"a check that
cannot see its own known answer cannot report an all-clear about anything else"* — and its
own comments warn that the cache *"lives OUTSIDE the repo, so it can disappear without a
commit."* The author anticipated this failure and instrumented for it.

## How I got it wrong

**I ran the gate with `head -8` and never read its summary.** I saw the two baseline hits,
saw exit 0, and concluded PASS. The disclosure was four lines below where I stopped reading.

This is my own documented failure mode, committed while writing a report about that failure
mode: *a scan reports where it looked, not the population it claims to cover.* The gate
reported where it looked. **I did not read it, and then accused it of not reporting.**

The accusation was also the flattering result: finding a broken gate is a better finding than
finding nothing, and I did not apply to my own accusation the standard I had applied to my
own protocols an hour earlier.

## What survives, at its real size

| claim | status |
|---|---|
| "passed a live instance while claiming to have checked it" | **withdrawn — false** |
| "a comparison against absent text always passes" | true of the mechanism, **but disclosed, so not a false all-clear** |
| reach is low | **true and material: 30 of 155 topics, 19%** |
| over the ruled 24, only 10 were compared | **true** |
| the cache is hardcoded into another session's scratchpad | **true, and a real fragility** |
| `icosapent` and `sglt2-mace-cvot` titles are copied registry fields | **true, and unchecked by the gate** |

**The residual finding is "under-reaching, and it says so", not "vacuous".** The actionable
fix is not to rebuild the gate — it is to **populate or relocate its registry cache**, which
would raise reach from 19% toward complete without touching a line of its logic.

## Why I have not executed the INOPERATIVE ruling

**The ruling rests on a claim I now know to be false, so executing it would propagate my
error into the register under someone else's name.** Marking a self-disclosing gate
INOPERATIVE and withdrawing every pass it has ever given would be an unjust act, and the
passes it gave over the 30 topics it actually compared *are* evidence — it never asserted
anything about the other 125.

I have not unilaterally cancelled the ruling either. **The decision is put back, with
corrected evidence.** What I recommend:

1. **Do not withdraw its passes.** They were always scoped to the compared set, and the gate
   said so.
2. **Do treat any citation of it as covering 19% of topics**, unless the cache is fixed.
   A pass is evidence about the compared population and nothing wider — which is what it
   already prints.
3. **Fix the cache**, which is the whole remedy: move it inside the repo or make its absence
   a refusal rather than a disclosed skip.

## The rule this leaves behind

**Before reporting that a check is broken, read all of its output.** A gate accused on a
partial read is the same error as a corpus counted on a partial scan — and it is worse,
because the accusation gets acted on by someone who was not there to see how little of it I
had read.
