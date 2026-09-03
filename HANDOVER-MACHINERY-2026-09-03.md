# Machinery lane handover — 2026-09-03

Written because everything below existed only in a transcript, and a finding that lives
only in a transcript is one detached drive away from never having happened. This lane has
the receipt for that: seven commits went with `E:` earlier today.

Pushed as a single commit, deliberately unbundled.

---

## 1. THE MOST SERIOUS ITEM — a gate that is armed and structurally unreachable

**`.githooks/pre-push:355-357`**

```sh
if [ -z "$CHANGED" ]; then
    echo "[pre-push] No *_REVIEW.html pages in this push; nothing to regression-check."
    exit 0
fi
```

`CHANGED` holds only `*_REVIEW.html` paths. **A push that touches no review page exits 0
here — before line 557**, where six gates are invoked in a loop:

```
audit_index_identity_drift · control_label_audit
gate_stored_estimate_declares_provenance_2026_08_27
sweep_estimand_established_unrecorded_2026_08_27
gate_screening_row_has_registration_id_2026_08_26
audit_trial_label_identity
```

plus `check_page_format.py --gate` immediately after.

**This is not the opt-in-gate class ("the gate is unarmed"). It is one level deeper: the
gate is armed, wired, and unreachable for an entire category of push — and it reports
GREEN.** Most pushes touch no review page, including every push this lane made except one.

**It is worse than the four unbuilt gates below**, because those are known-absent while this
one is believed present.

**Observed directly.** `gate_stored_estimate_declares_provenance_2026_08_27` returns exit 1
on the current tree (seven findings, section 5). It refused a push of mine that had a page
in scope, and silently did not run on a later push that did not. Same tree, same gate,
opposite outcomes, decided by whether a `*_REVIEW.html` happened to be in the diff.

**The hook's own header, at line 267, documents this exact failure having happened before:**
*"a push that touches no `*_REVIEW.html` … hit `exit 0` at the 'nothing to
regression-check' line thirty lines below and returned SUCCESS without executing a single
gate."* The fix was applied above that line and the same defect now exists below it.

**Not fixed here.** Fixing it makes this lane's own pushes fail on section 5's seven rows,
which belong to another lane. That is the correct outcome and should be someone's deliberate
decision, not a side effect of this handover.

---

## 2. FOUR GATES: AUTHORISED, SPECIFIED, NOT BUILT

All four are **oracle-free** — both sides of every comparison are already in the repository.

### 2.1 Every RoB/GRADE downgrade reason must name a checkable fact, and assert it

A downgrade whose stated reason is a claim about **our own record** is the cheapest of all
to check and the least often checked.

- **icosapent**, two false premises, both load-bearing: *"the registered primary is a MEDIAN
  … this pool is a MEAN difference"* — the stored `-33.1` and `-21.5` ARE Hodges-Lehmann
  placebo-adjusted medians, which the FDA statistical review labels "Estimated Median"; and
  *"a dose arm was selected and the selection is recorded nowhere"* — the PICO on the same
  page reads AMR101 4 g/day, and the numbers uniquely identify the 4 g arm. Both drive
  RoB-2 D5, GRADE indirectness, part of imprecision, and manuscript prose.
- **empagliflozin**: RoB downgraded **because the NEJM methods were not in PMC** — a
  source-retrieval failure recorded as a trial-conduct judgement.
- **finerenone**: D5 *some concerns* because the CV composite was a SECONDARY outcome. D5
  asks whether the result was SELECTED from multiple eligible analyses ON THE BASIS OF
  RESULTS. *Secondary outcome = some concerns* is not a RoB-2 rule.

### 2.2 Arm-role labels asserted against the direction of the stored effect

**icosapent** records **placebo as treatment** and **AMR101 4 g/day as control** on both
trials. The signs happen to be consistent, so the pooled number is not reversed — **only a
label check catches it**, and any downstream step reading labels rather than signs inverts.

### 2.3 The population string, consistent across surfaces and asserted against enrolment

Two instances:

- **AGYW** is 15-24 by the UNAIDS definition; the pooled trials enrolled **18-45**, and the
  estimate is dominated by women 25+ where efficacy is greatest. The page's own indirectness
  note names the under-18 gap and misses that 25-45 is also outside AGYW.
- **rosuvastatin** says **"adults with stroke"** in title, abstract, visual abstract,
  introduction and figures. JUPITER and HOPE-3 are **primary prevention** trials in people
  without cardiovascular disease. A corrected question is buried in the object and reached
  no reader-facing surface, while the visual abstract attaches `30,507 participants` to the
  wrong one.

Assert: the population string identical across title, abstract, visual abstract, PICO and
figures, **and** asserted against the contributing trials' enrolled populations.

### 2.4 Registry `param_type` and `unit` asserted against the ingested field

**rosuvastatin** labels JUPITER's `1,646.4` and `1,578.3` as counts or rates.
ClinicalTrials.gov declares them **parameter type MEAN, unit DAYS**, measure
*"Kaplan-Meier estimate of time to event/censoring"*. **A continuous time-to-event
measurement read as a count.** This is a generic registry-extraction defect and it is
**silent wherever it fires** — sweep corpus-wide.

### 2.5 Two further gates specified in the register but not built

- **T7** — assert a displayed R transcript's printed **statistic type** against the **call
  line above it**. apixaban prophylaxis stores a transcript claiming
  `rma(..., test="knha")` and prints a **z statistic with a normal interval**, then prints
  the genuine t-based one below. Both cannot come from one `knha` call. The numbers are
  fine; the provenance is fabricated by assembly — **the password class in the one layer
  whose selling point is verbatim reproducibility.**
- **A15** — fetch every stored PMID and assert its **title and authors** against the trial
  it is attached to. finerenone cites FIDELIO as `PMID 33034526`, which is *"Variability in
  antemortem and postmortem blood alcohol concentration"*; the correct PMID is `33264825`.
  **The portfolio index advertises identifier and provenance checking, so the blast radius
  is the advertised claim, not one page.**

---

## 3. SGLT2-HF — WHAT IS AND IS NOT CORRECTED, AND A LIKELY COLLISION

**Read this before touching that topic.** Another lane (*Rotavirus page and new detectors*)
is rebuilding this pool.

**MEASURED on this branch at `16da44a1c`:**

```
git diff --name-only origin/main..HEAD -- ssot/sglt2-hf SGLT2_HF_REVIEW.html   →  EMPTY
ssot/sglt2-hf/sglt2-hf.json
  harmonised_cvdeath_or_hhf        k=3   HR 0.7636      <- UNCORRECTED
  threecomp_cvdeath_hhf_urgent     k=2   HR 0.7835
  inputs.trials  NCT03036124 (DAPA-HF) · NCT03057977 (EMPEROR-Reduced)
                 NCT03057951 (EMPEROR-Preserved) · NCT03619213 (DELIVER)
SGLT2_HF_REVIEW.html  contains "20,725"  ×2                <- UNCORRECTED
```

> **THIS BRANCH CONTAINS ONLY THE REGISTER ENTRY DESCRIBING THE CORRECTION. IT CHANGES NO
> STORED VALUE AND NO SERVED PAGE.** The `0.774` probed at `16da44a1c` is register PROSE,
> not a stored number.

**The defect, stated so two lanes do not disagree about it.** `inputs.trials` already lists
**all four** NCTs including DELIVER, and the `k=3` pool contains three of them. The page
labels that analysis `20,725 participants`, which is arithmetically DAPA-HF 4,744 +
EMPEROR-Reduced 3,730 + EMPEROR-Preserved 5,988 + **DELIVER 6,263**. The correct n for its
three studies is `14,462`.

**It counted DELIVER's participants while omitting DELIVER's effect.** The wrong number is
the evidence that DELIVER's row failed to propagate.

**Cause, reached independently from two directions** — this is the strongest confirmation
available and both halves should be kept:

- from **inside the code**: `contributing_n()` returns `None` because the store holds no
  `inputs.trials[*].by_outcome` rows, so the renderer falls back to the topic total;
- from **outside, by arithmetic on a printed number**: `20,725` is the four-trial sum on a
  three-trial analysis.

**The correction, if that lane lands it:** DELIVER's own publication reports the
two-component endpoint directly, `475/3131` vs `577/3132`, `HR 0.80 (0.71-0.91)`. Corrected
pool **`HR 0.774 (0.724-0.827)`, k=4, N=20,725, I² = 0%**, externally confirmed by the 2022
Lancet prespecified synthesis over the same endpoint and the same trials at
`HR 0.77 (0.72-0.82)`.

**And the earlier framing was wrong.** This lane recorded DELIVER as *"an evidence blocker,
not an effort one"*. It was a blocker **given our source set, and the source set was the
defect** — FIX α, not an evidence gap. The withdrawn mixed-primary derivation was `0.7785`,
numerically almost identical, **so the endpoint error had little consequence and the
withdrawal was still right**. Both halves stated, because W1 exists.

**Collision risk.** If the other lane corrects the object and page, register row **A16**
becomes a description of completed work and should be restated. Two lanes converging on the
same number by different routes is worth recording; two lanes editing the same object is
not. **That topic is theirs.**

---

## 4. ENVIRONMENT — a measured standing constraint, not an incident

```
total physical            16,238 MB
free physical                806 MB
free virtual                 740 MB   (247 MB at the worst observation)
concurrent `claude`      43 processes holding 10,037 MB
```

Two pushes failed with `[pre-push] Executable-rule gates FAILED (exit 3)`. The cause was
`MemoryError` — `gate16`, `gate15` and `gate19` crashed, then `gates/run_all.py` itself died
in `importlib`. **The same suite run standalone minutes later was 16/16 PASS.**

> **AN `exit 3` UNDER THESE CONDITIONS IS NOT A SIGNAL ABOUT THE CODE — AND AN ARTEFACT
> PRODUCED UNDER THEM IS NOT TRUSTWORTHY EITHER.**

The house note says concurrency 3, and a 4th lane OOMs at rc=0 with an empty artefact. **We
are at 43.** A crashed gate is not a passed gate; the hook was right to refuse, and treating
the crash as a finding about the code would have been wrong in the other direction.

**Objects still live on `F:`.** Files are on `C:` (`C:\rmfw`) but that is a git *worktree*,
not a clone — its `.git` points at `F:\rapidmeta-finerenone\.git\worktrees\rmfw`, and
`F:` has ~234 MB free and is I/O-degraded. A direct `git clone` from `F:` timed out twice
(400 s, 900 s); `--shared` would keep the dependency. **The route that severs it is a clone
from GitHub.** Nothing on `F:` has been deleted and `git worktree prune` has never been run
— ~103 worktrees share that one object store.

---

## 5. BLOCKERS THAT ARE NOT THIS LANE'S

| gate | finding | introducing sha |
|---|---|---|
| `gate_stored_estimate_declares_provenance_2026_08_27` | **7 estimates with no declared provenance tier** — `provenance` is a legacy STRING (`'REGISTRY -- ClinicalTrials…'`). `apixaban-vte-prophylaxis` `major_bleeding.per_trial[0..3]`, `apixaban-vte-treatment` `[0..2]` | **`98526921a`** |
| `lint_recurring_traps.py` | `scripts/comparator_seed/phase3_measure.py:414` `unanchored_substring`. **FALSE POSITIVE** — `held_pmid` is a `set`, so `in` is membership. The value arrives via a tuple-unpacked subscript, so no sound static narrowing was available | not named by the gate |
| `gates/gate20_correction_pins.py` | BROKEN in any clone lacking a **local** `paper-studio/manuscript-review` ref — `scripts/check_correction_pins.py` `KNOWN_LANES` is a bare local branch name. 60 remote refs did not fix it; only `git update-ref` did. **To its credit it refuses rather than reporting a false clean** | not named by the gate |
| trunk gate chain | two guards on the trunk that their own gate refuses | `e1ccb9f9c`, `66c1ed934` |

Also measured and not this lane's: `source_hierarchy_gate`'s A2 count rose **610 → 623**
entirely from trunk content — `agyw-hiv-prep-review` +3, `apixaban-vte-prophylaxis` +7,
`apixaban-vte-treatment` +3 — introduced by **`cb5651469`** and **`98526921a`**, which add
harms provenance as new stored effects declaring no `analysis_variant`. Attributed by
diffing per-topic counts against the baseline and matching the gainers to
`git log origin/main~4..origin/main`. Recorded in that baseline's
`baseline_moved_because` field.

---

## 6. STATE

- **`harness/complete-20260902` = `a88466e46`** — the seven recovered commits. All seven
  verified `merge-base --is-ancestor` against `FETCH_HEAD`, with content probes at push
  time. **`E:` is permanently out of the loop.**
- **`harness/rebuild-20260903` = `16da44a1c`** — 18 commits ahead of `852b0478e`, working
  tree clean, content-probed from the remote.
- The register is `DEFECT-CLASS-REGISTER-2026-09-02.md`; protected refusals are
  `PROTECTED-REFUSALS-2026-09-02.md`; the reproducibility caveat and the four pinned figures
  are `REBUILD-INDEPENDENCE-NOTE-2026-09-03.md`.
- **The two implementations diverged on exactly one topic** and the rebuild was right —
  `apixaban-vte-treatment`, where the original's pattern could not match across an
  intervening noun in *"WHAT THIS WITHDRAWAL DOES NOT ESTABLISH"*. **They agreed on the
  four headline figures because the corpus did not yet contain the case that separates
  them.** Set-level agreement (protocol gate, 127 topics, zero symmetric difference) is much
  stronger evidence than an integer matching.
