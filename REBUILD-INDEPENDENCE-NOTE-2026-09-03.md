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
| checkable pages contradicting the "two-trial" constant (146 render it) | **13 of 18** | **13 of 18, 146 render — agrees** |
| comparable protocols DRIFTING, with 0 recorded amendments | **9 of 127** | **9 of 127 — agrees, same nine topics** |
| withdrawal reasons UNQUALIFIED, of which 2 HARMFUL | **111 of 151** | **111 of 151, 2 harmful — agrees, same two topics** |

**All four agree.** Three of them agree on more than the headline: the two-trial breakdown
reconciles to its population (5 agreeing + 13 contradicting = 18 checkable; 18 + 128
not-checkable = 146), the protocol gate names the same nine topics, and the withdrawal gate
names the same two harmful topics — `anidulafungin-candida-auto-full-review` and
`olmesartan-htn`.

## A divergence that was NOT a divergence, and how it was caught

Anchoring the two-trial phrase search meant writing a word-boundary escape -- a backslash
followed by the letter b -- into a regex. Written through a shell heredoc, **each escape
became a literal `0x08` BACKSPACE byte.** The pattern matched nothing, so **the
measurement returned 0 pages against a pinned figure of 146**.
literal `0x08` BACKSPACE byte. The pattern became `"<0x08>named two-trial programme<0x08>"`
and matched nothing, so **the measurement returned 0 pages against a pinned figure of 146**.

Under the rule above that is a divergence, and it would have been reported and chased. It
was not a divergence: the corpus was unchanged and **the instrument had corrupted itself in
transit**. `scripts/lint_recurring_traps.py` caught it as `control_bytes`.

> **A DIVERGENCE HAS TO BE DIAGNOSED BEFORE IT IS BELIEVED, IN BOTH DIRECTIONS.** A number
> that agrees can agree by coincidence; a number that disagrees can disagree because the
> tooling broke. Neither reading is free.

The anchors are now lookarounds, which carry no backslash and cannot fail that way.

**AND IT HAPPENED A SECOND TIME, IN THIS FILE.** The paragraph above was first
written through the same shell path and the escape was eaten again, leaving one
`0x08` byte in the document describing the hazard. Two instances in one hour from
one mechanism, the second inside the write-up of the first. The rule that follows
is narrower and more useful than "be careful": **do not put a backslash escape
through a shell heredoc at all** -- write it with a tool that does not re-interpret
the string, or express the pattern without one.


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
