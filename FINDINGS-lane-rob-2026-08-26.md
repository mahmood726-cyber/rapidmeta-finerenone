# Lane findings — RoB retrieval and adjudication, 2026-08-26

## 1. The blinding bug does not exist

Proven by planting, four controls, keyed to a real stored assessment
(`ablation-af-heart-failure`), header verified in commit `0f6764f42` (2026-08-21) — the
version the second assessor actually ran under, so it is not today's file flattering itself.

| control | what it shows | result |
|---|---|---|
| P1 | the decision rule reaches assessor 2 | present, 3 markers |
| P2 | no first-assessor judgement in the fact blocks | none |
| N1 | a verdict word **planted** in a fact field | **REFUSED**, word named |
| N2 | the same topic unplanted | builds |

N1 carries the weight: a blinding check that cannot fail is not a blinding check.

**My own control reproduced the original mistake.** P2 first searched the *whole prompt* for
verdict words and failed — because the header legitimately contains `NO_INFORMATION, never
LOW` **as the rule**. Presence of a verdict word is not evidence of a leaked verdict. That is
exactly the conflation the diagnosis rested on, reproduced inside the instrument built to
test it.

**Consequence:** `second_assessor_prompt.py` needs no repair, and re-running assessor 2 would
tell it precisely what it was told before.

## 2. The 38.1% disagreement is real, and its shape proves it

375 domain comparisons, 23 dual topics: 232 agreed, **143 disagreed (38.1%)**.

| domain | dominant direction (assessor 1 → 2) | n |
|---|---|---|
| D1 | SOME_CONCERNS → NO_INFORMATION | 26 of 32 |
| D2 | LOW → NO_INFORMATION | 11 of 17 |
| D3 | LOW → NO_INFORMATION | 16 of 24 |
| D4 | SOME_CONCERNS → LOW | 18 of 25 |
| D5 | SOME_CONCERNS → LOW | 33 of 45 |

A reader who never got the rule scores LOW where the other says NO_INFORMATION. On D1–D3
assessor 2 applies it **more** strictly; on D4–D5 it is the lenient one.
**One-directional is a harness artefact; bidirectional is a reading difference.**

## 3. Whose gap is each `NO_INFORMATION`? Recorded, not inferred

**411** NO_INFORMATION domain judgements across both assessors — which reconciles the
standing figure of 191: that is **assessor 1's** count (23 + 168).

| | about the trial | about us |
|---|---|---|
| **total** | 70 (17.0%) | **341 (83.0%)** |
| D1 | 16 | 110 |
| D2 | 19 | 120 |
| D3 | 21 | 111 |
| D4 | 4 | 0 |
| D5 | 10 | 0 |

What decides it is **which source answers that domain and whether we hold it** — not the
assessor's prose, which would be inference wearing a field name. D1–D3 need a protocol, SAP
or full report; D4–D5 are answered by the registry record, which we do hold, so their
absences are genuinely findings about the trials.

**83% of our `NO_INFORMATION` is a statement about us.** Publishing that as a statement about
the trials is the 870-page defect one layer up.

## 4. Retrieval is unblocked, and the snapshot matters

`.ctgov-raw-cache` holds all 353 of our distinct NCTs and **9** carry results — it is a
*protocol* cache. `F:/AACT-storage/AACT/2026-04-12` holds `outcome_analyses`,
`outcome_counts`, `result_groups`. Against AACT, on distinct NCTs contributing nothing:
**86 read-verbatim + 66 derive = 152 actionable without retrieving a paper.**

Denominator: 403 trial rows, 353 distinct NCTs, 127 already contributing, 245 contributing
nothing, 93 of those with no results in AACT at all.

**Also:** 89 trial rows that *already* contribute have a posted analysis with effect and CI —
a cross-check against what we derived, and a possible discrepancy source.

*(Estimate extraction is a different lane. This lane's retrieval is the conduct fields.)*

## 5. Instrument finding — a checkout that stops partway and reports success

`git worktree add` on this tree **stopped mid-checkout twice and returned exit 0 both times**.

- tree: **13,614 files, ~1.1 GB**
- attempt 1 (foreground): stopped at **43%** (5,938/13,614)
- attempt 2 (background): stopped at **32%** (4,472/13,614), background job reported
  **exit code 0**
- result both times: a directory of ~1,700 files, **no `.git` file**, `git worktree list`
  showing it `prunable`; `ssot/` absent entirely

**A completed process is not a completed checkout.** This is a new instance of the failure
mode that has cost more than any other this week: a silent instrument failure that returns
success. It joins the backgrounded-Codex no-op, the parser that scored one vendor 100%
unparseable, and the pre-push gate that printed PASS at 0/1522.

**What worked:** `--no-checkout` plus `git sparse-checkout set ssot scripts`, then `checkout`
— a small fraction of the tree, completed first time.

**Rule:** after any bulk checkout, assert the paths you need exist. Do not read exit status.

## 6. Branch-per-lane is not isolation

Another lane checked out `paper-studio/manuscript-review` in the shared worktree and **my
HEAD moved off my branch mid-task**, leaving my corrected file staged in their index where a
pathspec-less commit would have swept it onto their branch. A branch is not isolation when
the worktree is shared — a worktree has one HEAD. **Worktree-per-lane is the isolation.**

## 7. Exit status is not a verdict — a structural rule, not a remembered one

I read `rc=$?` through a pipe **again** today, after writing the rule down twice. A rule that
lives in prose gets violated; the fix is a shape that cannot be got wrong.

**The rule: every instrument puts its verdict in stdout, never only in its exit status.**
`ALL CONTROLS HELD` / `n CONTROL(S) FAILED` / `REFUSED: …` survive a pipe. `$?` does not —
in `cmd | tail`, `$?` is `tail`'s, and `tail` always succeeds. Exit status stays as a
secondary signal for automation; the human-read verdict is a line of output.

This also covers the four-tool pattern in §5: `git worktree add` returned 0 on a 43% checkout,
so its status was never the verdict either. **Read the artefact, not the status.**

## 8. The `by_outcome` freeze hazard, watched failing

`scripts/lane_rob/plant_by_outcome_drop.py`, keyed to a real stored assessment
(`ablation-af-heart-failure`, 5 stored judgements), six controls both directions:

| | case | result |
|---|---|---|
| N1 | a stored result **dropped** from the incoming assessment | **REFUSES**, names the result |
| N2 | a stored judgement **changed** | **REFUSES**, names the domain |
| P1 | incoming identical to stored | does not refuse |
| P2 | incoming **adds** a result, changes nothing | does not refuse |
| P3 | the drop, with the topic in `--allow-overwrite` | does not refuse |

P1 and P2 are what stop "always refuse" passing — the easier of the two failures to ship by
accident. Store sha256 asserted equal before and after: `1c6bf98b3…`, nothing written.

**This is the evidence for lifting the freeze, not the decision.** Lifting is Mahmood's call.

## 9. Freeze — still on, for its own reason

The regen/merge hazard is `by_outcome` being assigned **wholesale** and exempt from the
key-loss guard by design and by name. Nothing proven here touches that. Lifting it needs its
own planted control: **drop a stored `by_outcome` judgement and watch the merge refuse.**
