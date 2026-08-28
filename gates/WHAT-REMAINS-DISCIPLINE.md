# What remains discipline

**Standing list. Last measured 2026-08-28.**

Eight gates now run on every push and in CI. This is the list of things they do **not** cover —
the rules that still depend on somebody remembering. An honest list is worth more than a claim
that everything is enforced, and every item here has a stated reason and a named next step.

**The test for this list:** if the rule were broken tomorrow, would anything fail? If the answer
is "someone would notice", it belongs here.

---

## The rule that governs this list

> **AVAILABLE IS NOT OPERATIVE.** A gate no script calls is a rule in a document with extra
> steps.

`gates/absence.py` sat for one day, correct and tested and inert, before anything invoked it.
That is the diagnosis this whole batch is named after, arriving in the work of the person
building the gate for it. **Gate 8 now enforces the general form: every gate module must be
named by a caller, and an uncalled gate is VACUOUS, never PASS.**

---

## 1. `H.APPEND_ONLY` is a hand-maintained list — **discipline**

The shrink assertion covers `out/ESCALATIONS.jsonl` and nothing else. Any other shared
append-only artefact must be added by hand.

**Why it is not closed:** there is no mechanical way to know which files are append-only by
contract. **Next step:** a `.appendonly` marker file, or a naming convention (`*.jsonl` under
`out/`) that the harness enumerates.

## 1b. `/tmp` is shared between lanes and nothing guards it — **OPEN, and it bit within minutes**

Generic filenames in a shared scratch directory collide, because every lane picks the same
obvious names. This lane redirected gate output to `/tmp/f1.txt` and `/tmp/f2.txt`; `f2.txt`
was another lane's Rekor/ancestry verification log from 2026-08-26, and `>` truncated it to
zero the instant the command started. Recovered byte-for-byte including mtime, because the
Aug-26 timestamp was noticed while polling — **luck again, not a gate.**

**This is the FOURTH shared-artefact collision in one night**, and it happened *minutes after*
item 1 below was written, on a different artefact in a different location. The limitation was
recorded and then immediately demonstrated.

**Next step:** a lint refusing a redirect to a bare `/tmp/...` path in committed scripts —
lanes write to the session scratchpad. Cheaper than snapshotting, and it covers the actual
failure. **Nothing implements this yet.**

## 2. Removal-by-move with variable paths is invisible to gate 8 — **discipline**

`prune_legacy_corpus_2026_08_26.py` — the 1,191-page prune, and the script whose own docstring
carries the rule gate 5 enforces — does not delete. It `os.replace(src, dst)` into
`_pruned_2026_08_26/`, deliberately, so an abort is recoverable without git. Both paths are
variables, so name-based inference cannot resolve them, and treating every `os.replace` as a
removal would flag every atomic write in the repo.

**Covered by name** in `gates/REMOVAL_PATHS.json`. **A NEW script of that shape would pass.**
Gate 8 prints this blind spot on every run. **Next step:** an artefact-side check — anything
appearing in a quarantine directory must be attributable to a registered removal path.

## 3. Nothing writes `subject_ref` — **discipline**

Gate 4 stops *new* bare judgements and demonstrates the one-line fix. **40 of 2,789 judgements
(1.4%) are re-checkable**; retrofitting the 484 kind-D and 868 kind-C sites is unstarted.
Routed to the frozen-judgement lane.

## 4. The reason data is not unified — **deliberately deferred, not forgotten**

Only the *reader* is single. 152 objects carry `poolable_reason`, 7 carry
`not_poolable_reason`. `field_aliases.py` already records that unifying 155 objects is
Mahmood's decision, not a gate's. Escalated 2026-08-28T16:35Z.

## 5. Gate 2's scope is a naming convention — **discipline**

Enforcement covers `gate_|check_|lint_|audit_|sweep_|verify_…` plus all of `gates/`. A text
matcher inside a module named something else is uncovered. Narrow-and-enforceable was chosen
over broad-and-ignored after a first draft flagged **739 of 820 modules**, which is a gate
bypassed on day one.

## 6. Gate 6 arm B is reported, not enforced — **discipline**

15 generator render sites emit a trial name with no registration in the same fragment. Frozen,
not fixed. The 136 names in served prose all do carry one.

## 7. Gate 7 covers `ssot/` only — **discipline**

`outputs/_baseline_projector.py` is a projector that gate 6 reads and gate 7 does not weigh for
blast radius.

## 8. Gate 5's positive-restatement regex has a measured 16.7% false-positive rate — **known, un-tuned on purpose**

`"the risk of bias assessment is not pooled across domains"` matches it. Left alone: tuning
against the validation sample burns the only measurement of the instrument. **The direction is
recorded** — a false positive inflates the positive count and therefore *shrinks* the gap, so
754 is a lower bound.

## 9. Every known-negative control was hand-written by the classifier's author — **structural weakness**

The labeller is the person who wrote the thing being labelled. Recorded rather than dropped.
**Next step:** a second family labels a fresh sample at a seed recorded before it is drawn.

## 10. The pre-push hook only runs where `core.hooksPath` is set — **CI is the backstop**

A clone that has not run `git config core.hooksPath .githooks` gets no pre-push gates. The CI
workflow runs all eight plus the meta-gate on every branch.

## 11. A ratcheted PASS means "no new instances", never "clean" — **must be said every time**

| gate | frozen at | what is frozen |
|---|---|---|
| 1 trial identity | 6 | the AGYW swap sites |
| 2 text-match control | 188 | uncontrolled matchers |
| 3 reason divergence | 11 | outcomes with two substantive answers |
| 4 judgement reference | 484 | kind-D judgements |
| 5 selector miss | 1 | the KFRE en-dash page |
| 6 bare name / swap | 15 / 2 | generator sites / served swaps |

Every run prints both numbers. **The discipline is not letting the frozen list be read as zero.**

---

## Register entry — earned 2026-08-28, twice, inside gates written to enforce rules

> **A CONTROL ANCHORED TO LIVE DATA SILENTLY RETIRES ITSELF THE MOMENT THE CORPUS IS FIXED.**
>
> It passes today because the corpus currently matches it. When the defect is repaired the case
> becomes unreachable, and the gate reports VACUOUS — or worse, PASS forever, having checked
> nothing.
>
> **Trigger, checkable without knowing the topic:** whenever you register a case a check must
> see, ask *what happens to this control when the thing it points at is fixed?* If the answer is
> "it stops existing", it is not a control.
>
> **Anchor to a fixture: synthetic, or pinned to an immutable object id.** `gate3` is pinned to
> blob `c623a213`; `gate4`'s are synthetic classifier probes.
>
> This rule already existed in `lessons.md`. It was violated twice in one evening inside gates
> written to enforce rules, and both times it was caught by running `--repair` rather than by
> re-reading the code.
