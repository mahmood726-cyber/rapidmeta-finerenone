# The strongest evidence a gate is real is that it blocked the person who built it

**Registered 2026-08-30. Two instances in one night, in two different lanes, on their authors'
own changes.**

---

## Why this is worth a register entry at all

Every gate in this suite was written by someone who believed the rule. That belief is exactly
what a gate cannot rely on: the rule it enforces was, in every case, **already written down,
owned, and broken anyway** — `run_all.py`'s own header says so.

So the question "is this gate real?" cannot be answered by reading it, and it cannot be answered
by watching it pass. ⚠️ **A gate that has only ever passed is indistinguishable from a gate that
cannot fail** — four files in this repository were renamed `*_triage.py` for precisely that
reason, and gate 8 exists because five rules were installed, invoked and inert.

⭐ **A gate that stops its own author is the one observation that cannot be produced by belief.**
The author had the rule in mind, wanted the change to land, and the gate refused anyway.

---

## Instance 1 — gate 9, shared scratch, refusing the lane that had just fixed shared scratch

`regeneration_test.py` wrote its rebuilt pages to `F:\claude-temp\pend\out`, the shared scratch
root. The per-object filename in that same function stops the test colliding with **itself**; it
does nothing about a second lane running the same object.

**I had noticed this and deferred it.** The gate did not defer it. And its own note records that
this same lint *"did not fire when this lane truncated another lane's file in the shared root"*
— so the collision is not hypothetical, it has already happened here.

⛔ **AND IT REFUSED THE FIX TOO, WHICH IS THE PART THAT MATTERS.** The first fix kept the literal
`F:\claude-temp\regen-out` and appended the lane name **at runtime**. Gate 9 reads the LITERAL,
and states in its own coverage line that *"any path assembled at runtime from a variable"* is
uncounted. **That fix would have made the collision invisible to the lint rather than
impossible.**

*Satisfying a detector by moving out of its view is the failure mode, not the fix.* The output
now leaves the shared root entirely — `<worktree>/out/regen`, unique per lane **by
construction**, no convention to remember.

## Instance 2 — gate 10, `REGISTRY-STALE-CLASS-NOW-DETECTED`, on a sibling lane's own change

Reported by the sibling lane the same night: gate 10 failed on the change made by the lane that
owns it. Same shape, different rule.

---

## What generalises

1. **Count these deliberately.** A suite's credibility is not its pass rate; it is the number of
   times it has refused someone who wanted to proceed. That number should be *published*, like
   every other denominator here.
2. **The moment to be most suspicious is when a gate blocks you and the fix looks easy.** Both
   of tonight's easy fixes — a runtime-assembled path, a re-baseline at the new line number —
   would have left the defect in place and the gate quiet.
3. ⚠️ **Distinguish "the gate is wrong" from "the gate is inconvenient."** Gate 9 was
   inconvenient four times and wrong zero times. When a gate refuses, the first hypothesis is
   that it is right, and the second is that the fix you reached for is the one it was built to
   stop.
4. **A refusal that names its cause is worth more than one that names a symptom.** Gate 9 said
   *which line*, *which root*, and *why a runtime suffix does not count*. The pre-push port
   refusal, by contrast, surfaced several layers down inside `regression_check.py` and read as a
   defect in the pushed pages — that hook now re-proves the server's identity at the point of
   failure so the cause is named where it happens.

---

## Companion: the runner that publishes what it did not run

The same night, `gates/run_all.py` printed:

> `[pre-push] Executable-rule gates PASS (6 of 9; 2, 5 and 6 are CI-only, see above).`
> `NOT run; this run says nothing about what they check.`

⭐ **That is the coverage-fraction discipline applied to the gate runner itself.** A PASS that
does not say what it did not run is a PASS nobody can use — it is the same defect as a scan
reporting its reach as its population, one level up. **Keep it, and require it of every new
gate:** gate 9 prints `COVERAGE: 1072 of 1277 (83.9%)`, gate 15 prints its backlog on every run,
and the harness gate prints `NOT RUN HERE (retrieval-scoped, 10): CHK001, CHK003, …` with
*"Silence from them is not evidence."*
