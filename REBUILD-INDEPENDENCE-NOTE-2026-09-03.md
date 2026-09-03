# What the rebuild comparison does and does not establish

Written **before** the rebuild was run, and committed so it cannot be adjusted afterwards.

## The situation

On 2026-09-03 the `E:` volume detached with seven committed-but-unpushed commits on it.
The work was rebuilt on `harness/rebuild-20260903`. When `E:` returns there will be two
implementations of the same five gates.

## The claim that must not be made

> "Two independent implementations of the same gates, written hours apart, without sight
> of each other. An independent reimplementation agreeing beats any control we could have
> designed."

**That overstates it, and overstating a validation is the class this lane audits other
people for.** The two implementations share an author, are hours apart, and the earlier one
was still in the author's working memory while the later one was written. They are not
independent in the sense that word carries when it is used to license a conclusion.

## What it does establish

**Reproducibility.** It genuinely catches:

- a figure transcribed from memory rather than re-derived;
- a baseline retyped rather than recomputed;
- an environment difference between the `E:` clone and the `C:` worktree;
- a rebuilt predicate that reaches a different population from the original.

## What it does not establish

What a blind reimplementation, by a different author who had never seen the first, would
establish. Nothing here substitutes for that.

## The evidence that is stronger than the headline numbers

**A sequence of intermediate failures agreeing is much harder to get by accident than a
number agreeing.** On the B2 rebuild, two side-effects reproduced in the same order as
before the volume was lost:

1. the negative test's control object refused, because it declared no `search.strategy`;
2. the recompute gate's negative control fired, because it was scoped to a whole PAGE
   rather than to the `P5` reason it protects.

Neither was aimed for. A single number can agree by coincidence; an ordered sequence of
intermediate failures agreeing is considerably harder to get that way.

## The figures, pinned before any rebuilt gate was run

Recorded here so the comparison cannot be quietly adjusted. Each is **re-measured, never
transcribed**: every rebuilt gate is run and whatever it prints is what gets recorded.

| measurement | figure from the lost commits | rebuilt |
|---|---|---|
| served marker pages with the P1-vs-banner contradiction | **17 of 19** | **17 of 19 — agrees** |
| checkable pages contradicting the "two-trial" constant (146 render it) | **13 of 18** | pending |
| comparable protocols DRIFTING, with 0 recorded amendments | **9 of 127** | pending |
| withdrawal reasons UNQUALIFIED, of which 2 HARMFUL | **111 of 151** | pending |

**If one disagrees, that is the most valuable outcome available.** It gets reported, the
wrong implementation gets identified, and the cause of the divergence gets recorded. It
does not get reconciled quietly, and the new number is not adopted merely because it is the
one currently visible.

`111 of 151` matters most: the `2 HARMFUL` are a claim about live pages, and this project
has already had to retract "the correction reverses the conclusion" once when only its own
derivation had collapsed.

## A rule earned during the rebuild

A failed patch anchor let `--write-baseline` run twice **without** the reason mechanism in
place, silently writing a `21` where the committed baseline said `11`. It was reverted with
`git checkout`, the mechanism was added, and the baseline was re-derived — it now records
`moved_from: 11` alongside the reason.

> **A BASELINE THAT CANNOT SAY WHY IT MOVED IS A RATCHET THAT CAN BE LOOSENED SILENTLY.**
> "Records its own reason" is a property of the baseline write, not a habit of whoever
> happens to be running it.

## And the reason this file is in the repository

The pinned figures and this caveat first existed only in a scratch directory. **A finding
that lives only on scratch is one detached drive away from never having happened**, and
this lane has the receipt for that.
