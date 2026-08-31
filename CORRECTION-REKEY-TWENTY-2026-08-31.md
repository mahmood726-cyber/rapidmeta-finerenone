# CORRECTION to REKEY-TWENTY-2026-08-31.md (committed as 88aef9525)
# The amendment never reached the twenty

**The original claim is left standing in `RULE-AMENDMENT.md`, unedited.** A correction that
removes the error leaves a clean page where a retraction should be. This file is the
retraction; the error stays where it was written.

---

## 1. The false sentence, quoted verbatim

`RULE-AMENDMENT.md`, line 49, under *Amendment 2*:

> **Applied uniformly**, to all 156 topics and both controls. No topic named, no topic
> special-cased. Made before any candidate, verified or judged count existed.

**It reached the controls only.** The twenty were scored with the unamended splitter.

### The mechanism

`scan.py` had **two sources for one rule**:

| call site | how it got class terms | which rule it used |
|---|---|---|
| line 79 — the **controls** | `class_phrases()` called **live** | **amended** |
| line 140 — the **twenty** | `class_phrases` read **frozen from `twenty.json`**, written at draw time | **unamended** |

Amendment 2 was authored after `twenty.json` was materialised, so it changed the live path
and could not reach the frozen one.

**The consequence is worse than a stale term list: the positive control certified a splitter
the twenty never used, so it was not measuring the twenty at all.** The class name for this,
recorded: **AN INSTRUMENT CERTIFIED IN ONE CONFIGURATION AND RUN IN ANOTHER** — the same
family as a gate proven on fixtures and never run on its corpus.

Five records differed between the pool the scan used and the pool the rule as written
produces — `dabigatran-af`, `dabigatran-stroke`, `enoxaparin-vte`, `etripamil-psvt`,
`pitavastatin-auto-full-review`, all in `class_phrases`. Found while verifying the offsite
backup, which is the only reason it was found at all.

---

## 2. ⭐ Why the re-run is a BUG FIX and not a rule change

**The surface appearance is what a reader will suspect: *"they re-ran after learning the
number might improve."* The defence is not our word — it is the amendment's own timestamp
and content.**

Amendment 2 was **authored, justified and frozen in `RULE-AMENDMENT.md` before the scan
ran**. It states, before any scan output existed, that `beta-blockers (propranolol type)`
must split to `beta blocker`. Nothing about the rule has changed since. The re-run applies
the **already-frozen rule correctly** for the first time.

**The expectation was written to disk before the re-run** — `EXPECTATION-REKEY-RERUN-2026-08-31.md` — naming
the predicted figure, the four affected topics, the direction of the likely miss, and the
one outcome that would make me distrust the corrected number.

---

## 3. The corrected figure — both visible

| | **SUPERSEDED** (published) | **CORRECTED** |
|---|---|---|
| A — drug-keyed | 1 / 20 | **1 / 20** |
| B — class only | 3 / 20 | **4 / 20** |
| **A∪B — the re-key** | **4 / 20** | **5 / 20** |
| candidates | 7 → 20 | 7 → 33 |
| verified | 2 → 10 | 2 → 14 |
| judged pairs | 10 | 14 |
| **independent new counterparts** | **1** | **2, across 4 topics** |

**`1/20 → 4/20` is SUPERSEDED. The corrected figure is `1/20 → 5/20`.**

### What moved, and why

**`enoxaparin-vte` alone.** The unamended splitter produced
`heparin derivative and low molecular weight or depolymerized heparin` — one unmatchable
phrase. The rule as written produces `heparin`, `molecular weight` and others, which reach
the LMWH literature.

The two independent counterparts:

| review | drug | topics covered |
|---|---|---|
| `CD004434` *Endothelin receptor antagonists for pulmonary arterial hypertension* | bosentan | **3** — `bosentan-pah`, `-children`, `-monotherapy` |
| `CD006681` *Low molecular weight heparin for prevention of venous thromboembolism…* | enoxaparin | 1 — `enoxaparin-vte` |

⭐ **The near-duplicate finding is unchanged and is still the portable half:** four topics,
**two** independent findings, because three of the four are one question under three names.
Any per-topic count over this corpus carries that inflation.

`dabigatran-af`, `dabigatran-stroke`, `etripamil-psvt` and `pitavastatin-auto-full-review`
gained candidates but **no verified pair**. They did not move.

### ⭐ The risk I named in advance did NOT materialise — checked, not assumed

`EXPECTATION-REKEY-RERUN-2026-08-31.md` warned that the amended split yields `heparin` as a bare one-word
phrase, and that flips driven by one-word fragments would make the corrected figure **worse**
evidence, not better. **All four new `enoxaparin-vte` pairs matched on `heparin` AND
`molecular weight` together** — never on the bare fragment alone. The matches are genuinely
low-molecular-weight-heparin reviews. The corrected number is not fragment noise.

**And the new pairs were not waved through:** of the four newly verified, **three were
refuted** — `CD001100` and `CD006650` are VTE *treatment* where the topic is *prevention*,
and `CD007557`'s outcome is heparin-induced thrombocytopenia, not VTE. One survived.

### Which way the expectation missed

Predicted **6 / 20**, observed **5 / 20**. **Optimistic by one — the direction named in
advance**, and the thirteenth consecutive optimistic miss.

---

## 4. The structural fix, so it cannot recur silently

**The defect was not the amendment. It was two sources for one rule.**

1. **One source.** `rekey_rule.class_terms_for_drug()` now holds R4 *and* its F4/F5/F6
   refusals, and is the only place a drug becomes class terms. `build_pool.py` and
   `scan.py` both call it; `scan.py` derives the twenty's terms through the same
   `terms_for()` the controls use. **Nothing reads a frozen class term.**
   ⚠️ This mattered more than it looks: moving `scan.py` to compute live *without* moving
   the gating would have silently begun scoring the `F5_MODALITY_CLASS` classes the rule
   rejects. One source has to mean the whole rule, not just the splitter.
2. **An assertion, because a convention would be broken silently by the next amendment.**
   `rule_fingerprint()` is a sha256 over the rule's **output** for a fixed probe. Every
   artefact records the fingerprint it was built under; every consumer recomputes it and
   **REFUSES on mismatch**, naming both fingerprints.
3. **Planted, both directions** — `plant_fingerprint.py`, 4/4: a fresh artefact passes, a
   stale one and one with no fingerprint are refused with both fingerprints named, **and the
   probe is proven sensitive to the exact amendment that was missed** by reconstructing the
   pre-amendment splitter and showing it fingerprints differently
   (`005d14e46d41f9b2` vs `604ed6957a1adf17`). A fingerprint blind to the drift it exists to
   catch would be decoration.

`plant_frame_contract.py` 6/6 and `plant_gate.py` 7/7 still pass. The four scan controls
still pass, and the corrected run's 14 judgements pass the label-vs-reason gate 14/14 with
exact coverage.
