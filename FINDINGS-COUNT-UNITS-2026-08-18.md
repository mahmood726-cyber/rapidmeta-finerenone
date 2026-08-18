# A value that is not a count, stored in a field called `counts`

**Written as a standalone file deliberately.** `TOOLING-QUEUE.md`,
`STATUS.md` and `MISTAKE-LEDGER.md` were being rewritten by another lane in this
same working tree while this was found — see the concurrency note at the end —
and appending to a file another writer holds is how one of the two sets of edits
disappears. Fold this into queue item 18 when there is a single writer again.

Found 2026-08-18 while reading `arni-hfref`'s three unread endpoint definitions
(queue item 20). Both faults are in the **fetcher**, not in
`count_provenance_gate`'s comparison logic. Both were caught because the topic
was worked at depth; neither would have surfaced from a corpus sweep, because
both produce *plausible-looking* verdicts.

---

## Fault A — a percentage, a rate or a mean change stored as an event count

The registry's outcome measures carry a unit. `paramType` and `unitOfMeasure`
say whether a posted value is a participant count, a percentage, a mean, or an
exposure-adjusted rate. **Neither is stored.** Every posted first-measurement
value lands in `registration_primary_counts.treatment_events` /
`control_events`, or in `registration_other_outcome_counts[].counts`, with no
unit beside it.

### What it cost, on the row that found it

`count_provenance_gate` matched PARACHUTE-HF's contributed row to the correct
registry outcome — correctly, on the title I had just recorded — then compared
the row's `155` and `169` against the registry's `33.5` and `36.7` and reported:

> denominators match the registry exactly but the events differ by a factor of
> 5 … No other outcome in the record matches the row's numbers, so the source
> could not be named

**The row is right.** `155/462 = 33.55%` and `169/460 = 36.74%`; the registry's
own posted results confirm the object digit for digit. The gate impugned a
correct row, in prose that reads like a finding.

### The direction that is worse

The alarm direction is survivable — a human checks and clears it. The FAIL
branch is not. It names a row's numerators as some **other** outcome whenever
they land within 1 of that outcome's stored pair:

```python
if len(pair) >= 2 and abs(pair[0] - te) <= 1 and abs(pair[1] - ce) <= 1:
    return ("FAIL", "MISMATCHED NUMERATOR AND DENOMINATOR …")
```

A percentage lives in 0–100. So do a great many event counts. A coincidence
there produces a **FAIL that names a wrong source outcome** — a confident,
specific, false accusation against a correct row, of exactly the kind this
project has withdrawn estimates over.

### Scope — measured, not estimated

`python scripts/measure_count_units_defect.py`, over all 49 SSOT objects:

| | |
|---|---|
| primary-count rows stored | **109** |
| of those, values that are **not plausibly counts** | **63 (57.8%)** |
| other-outcome count pairs stored | **1,337** |
| of those, not plausibly counts | **912 (68.2%)** |
| objects carrying at least one | **42 of 49** |

Judged conservatively three ways: the title begins *Percentage* / *Percent* /
*Change From Baseline* / *Mean*, or contains *Rate* / *Ratio* / *Number of Days*
/ *Score*; or a stored value is negative; or a stored value is not an integer.

The primary-count rows are the ones that **produce a verdict**, so 63 is the
number that matters. Some are unmistakable once seen — `alirocumab-lipid`
NCT01507831 stores `[109.1, 107.4]` "events", and `prevnar15-pneumo` NCT03620162
stores `[149.1, 126.0]`. Event counts exceeding their own denominators by 50%
are percentages of participants with ≥1 solicited adverse event, and they have
been sitting in an events field.

**What this does NOT establish:** that 63 rows produced wrong verdicts. Most
will be UNCHECKABLE or REVIEW for other reasons, and a mismatched unit against a
mismatched unit can still compare as equal. The measured claim is that 63 of 109
verdict-producing rows are computed on a quantity the gate believes is an event
count and is not. **How many of those verdicts are wrong is a separate
measurement and has not been made.**

### The fix, not applied here

Store `paramType` and `unitOfMeasure` with every fetched pair, and have the gate
**refuse to compare** anything not posted as a participant count — UNCHECKABLE
with the unit named, never a numeric verdict across units. That is a fetcher
change plus a re-fetch of 109 rows, and it should not be started in a tree with
two writers in it.

---

## Fault B — classes summed when they are a total and its parts

PARADIGM-HF's posted primary carries three classes:

| class | LCZ696 | enalapril |
|---|---|---|
| Primary Composite | 914 | 1117 |
| CV death | 558 | 693 |
| 1st HF Hospitalization | 537 | 658 |

The second and third **decompose** the first. The fetcher summed all three and
stored `2009` and `2468` — every composite event counted up to three times. The
gate then reported:

> events differ modestly (914/1117 against the registry's 2009/2468) — an
> analysis-set difference would look like this

A factor of 2.2 described as *modest*, on the largest trial in the flagship,
against an object whose `914` and `1117` are the registry's own Primary
Composite row exactly.

Summing across classes is **correct** for a genuinely categorical outcome —
causes of death, NYHA class — and wrong for total-plus-parts. Nothing recorded
which kind an outcome was, so one rule was applied to both.

`TOOLING-QUEUE.md`'s closed entry for `count_provenance_gate` lists
"multi-category outcomes summed per arm" as one of three parser faults fixed
before the gate was trusted. **The fix made summing unconditional; the
distinction it needed was never drawn.** A repair that removes one failure mode
by installing its mirror image.

**Scope: NOT MEASURED, deliberately.** Counting rows that *look* summed is an
inference. Establishing it needs the class structure re-fetched per trial, and a
number produced any other way would be the blast-radius-without-a-measurement
this project has twice published and twice had to correct.

---

## Why both faults read as findings rather than as noise

Both produce output shaped like a discovery: a factor, a comparison, a named
registry quantity. Neither says "I could not tell what unit this is." A gate
that cannot represent *unit unknown* has to guess, and a guess dressed as a
verdict is indistinguishable from a result.

Both rows it fired on here were **correct**, and both were cleared only because
the trial's registry record had just been read by hand for another purpose. On a
row nobody had read, the alarm would have been the evidence.

---

## Concurrency note — the condition this file was written under

At 07:25–07:55 on 2026-08-18 a second agent lane was committing into this same
working tree, roughly every two to five minutes, while this lane was working.
Established from `git reflog` and confirmed by `HEAD` moving between two
consecutive commands of this lane's own session. It rewrote `STATUS.md`,
`TOOLING-QUEUE.md` and `MISTAKE-LEDGER.md` several times in that window, and it
picked up and correctly recorded this lane's ARNI result — so the two lanes were
not merely adjacent, they were reading each other's commits.

Also from that window, and not this lane's doing: `git push origin HEAD` from
this worktree creates a remote branch `fix/ssot-tabbed-shell` rather than
updating `main`, because the local branch name differs from its upstream. The
first push of this lane's ARNI work therefore went to GitHub and **not** to the
deploy ref. Corrected with `git push origin HEAD:main`, and the page is
live-verified byte-identical. **The stray remote branch
`fix/ssot-tabbed-shell` still exists and should be deleted** — deleting it was
refused by this session's permission classifier.

And a gate gap that fell out of the same mistake: the pre-push regression hook
reported *"No `*_REVIEW.html` pages in this push; nothing to regression-check"*
for a push that contained `ARNI_HF_REVIEW.html`, because a push **creating** a
remote branch has no remote base to diff against. **A push that creates a branch
regression-checks nothing and says so in the voice of a scoped pass.** The
second push, to `main`, checked 1 page and reported `fully_ok 1/1`.
