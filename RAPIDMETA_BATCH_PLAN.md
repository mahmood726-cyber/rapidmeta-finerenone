# RAPIDMETA BATCH-EXECUTION PLAN

**Version:** 1.0 · **Date:** 2026-07-30 · **Branch:** `build/error-registry-2026-07-30`
**Status:** STAGED, **NOT PUSHED**. `main` is the deploy ref; this branch deploys nothing.
**Authorisation:** Mahmood's GO to remediate the whole corpus. **Per-batch go still required before any push.**

**Inputs.** `RAPIDMETA_ERROR_REGISTRY.md` (67 error types) · `RAPIDMETA_ERROR_SWEEP.{md,json}`
(52 STATIC detectors × 1,088 apps) · `assets/js/rapidmeta-guards.js` (20 fail-closed guards) ·
`tests/fixtures/rapidmeta_error_fixtures.json` (3 source-verified worked examples).

**The batch order is DERIVED, not authored.** `scripts/rapidmeta_batch_plan.py` reads the sweep and
re-emits `outputs/rapidmeta_batch_list.json`. Re-run it after any fresh sweep; the plan cannot drift
from the evidence.

---

## 0. The measured corpus

| | |
|---|---:|
| `*_REVIEW.html` files | 1,659 |
| Apps scanned (≥ 20 KB) | **1,088** |
| Redirect stubs (< 20 KB, excluded from denominators) | 571 |
| Apps in the repo **root** ≥ 20 KB | 909 |
| Apps with ≥ 1 static finding | **1,088 (100%)** |
| Apps whose `realData` ledger does not parse (reported, not silently skipped) | 19 |
| Detector errors | 0 |

**100% is not a headline — it is arithmetic.** Twelve error types sit above 85% prevalence, and each
of those twelve is **one shared code path**. That is what makes Phase 1 possible.

---

# PHASE 1 — ENGINE-GUARD PATCH

**One patch. One pass. The single point of leverage in the whole corpus.**

## 1.1 How many apps share the engine — measured, not assumed

`grep -lc` over the 909 root apps ≥ 20 KB:

| Shared-engine marker | apps | what it gates |
|---|---:|---|
| `COMPLETE-POOLING-REPAIR` | **909** | RM-B02 scope-lock bypass |
| `id="rapidmeta-integrity-badge"` | 894 | RM-F01/F02/F03 badge parity |
| `safeRob` | **881** | RM-G01 |
| `(allOutcomes\|outcomes)[0]` | 881 | RM-B01/B03 scope-lock |
| `window.__verdict` | 881 | RM-F02, RM-J07 |
| `Per ICMJE 2023` | 881 | RM-J01 |
| `escalc(measure=` generator | 881 | RM-A14 |
| `assets/js/paper-studio.js` | 881 | RM-B02 Defect 4 |
| `CTGOV_EVIDENCE_REGISTRY` | 716 | RM-E03 watchlist |
| `"RR" !== String(` denylist | 716 | RM-A02 |

**Phase-1 scope: 909 root apps carry the engine, 881 carry the full v12 template.** Add the
sub-directory copies (`e156-submission/assets/`, `docs/`, …) and the sweep's denominator is
**1,088**. **17 basenames occur twice** — a root app plus a stale copy — and *both* must be patched:
a fix applied to one variant is not applied to the app.

## 1.2 What Phase 1 lands

> **Phase 1 is GUARDS-ONLY.** Three textual transforms (T1 ICMJE claim, T2 estimand denylist,
> T3 `safeRob`) plus the runtime guard overlay. **No T4** — the pooling-repair neutralisation was
> withdrawn after the re-gate proved it blanks `state.results` at load on ~944 apps; it is now a
> per-app Phase-2 item (§2.7). **No G07** — that step searched the DOM for a marker string that
> sat inside its own `indexOf()` call, so it could never fail and was evidence of nothing.

All 20 guards from `assets/js/rapidmeta-guards.js`, plus the fail-closed integrity gate:

| Guard | Registry ids | What it makes impossible |
|---|---|---|
| **G01** | RM-A05 A07 A09 A01 | continuous / win-ratio / rate-ratio into an HR/OR/RR model; **and a ratio field outside [0.01, 100] (impossible) or [0.02, 25] (implausible)** — this is the `-19.50` "hazard ratio" and the `73.83` percent-change |
| **G02** | RM-A04 | Peto output labelled anything but OR |
| **G03** | RM-B01 B03 | a silent endpoint fallback — BLOCK + "not available for this outcome" |
| **G04** | RM-A08 | component counts beside a composite effect |
| **G05** | RM-F05 F06 C01 | missing rendered as 0; impossible PRISMA; unlabelled denominators |
| **G06** | RM-A02 A01 | an analysis below 2 SAME-estimand estimates |
| **G07** | RM-B02 | stale outcome state surviving a selector change |
| **G08** | RM-G01 G02 | `safeRob` unknown → "low" |
| **G09** | RM-D01 B06 B07 | an NCT-linked row whose registry record contradicts it |
| **G10** | RM-H01 H02 H03 | funnel/Egger/trim-fill/Copas/meta-reg/TSA/NMA/FI below threshold |
| **G11** | RM-F07 H05 J01 J02 | a verification claim over a `--` source; a benchmark validating a different scope; the ICMJE/PROSPERO attribution — **while asserting the tamper-evident mechanism SURVIVES** |
| **G12** | RM-F01 F02 F03 H04 | a badge asserting a pass over a non-STABLE verdict, an open finding, an empty ledger, or itself |
| **G13** | RM-D06 | a filename naming a different subject from the content |
| **G14** | RM-E01 E02 | cross-topic donor strings and foreign alias tables |
| **G15** | RM-A06 C03 | a person-time rate read as a proportion; arms bound by index |
| **G16** | RM-F08 | a sensitivity interval crossing 1 hidden from the headline |
| **G17** | RM-I01 I02 | a direction word, NNT or NNH without an explicit polarity |
| **G18** | **RM-J07 D10** | **THE FAIL-CLOSED INTEGRITY GATE** — blocks on a null/NULLED trial id, a mismatched composite across pooled rows, a NaN or impossible output, or trial counts/N disagreeing across surfaces |
| **G19** | RM-A13 | MACE-3 pooled with MACE-4; any undeclared component set |
| **G20** | RM-E03 | a monitoring watchlist that is not the app's own topic |

**Verified now:** 119/119 unit tests pass; the mutation self-test re-seeds **14 shipped defects and
catches 14/14**, restoring green. `python tests/mutate_guards_selftest.py`.

## 1.3 What Phase 1 fixes structurally, and how many apps

24 of the 67 registry types are **template strings or engine logic**. Landing Phase 1 once fixes them
across every app that carries the engine:

| id | type | apps | % |
|---|---|---:|---:|
| RM-F05 | missing rendered as zero | 1059 | 97.3% |
| RM-I01 | no explicit polarity anywhere | 1053 | 96.8% |
| RM-H01 | k-inappropriate machinery | 1049 | 96.4% |
| RM-J07 | integrity gate passes over a fail-closed condition | 1030 | 94.7% |
| RM-B03 | silent endpoint fallback | 1024 | 94.1% |
| RM-B02 | stale outcome-state leakage | 1010 | 92.8% |
| RM-G01 | `safeRob` unknown → low | 1006 | 92.5% |
| RM-J01 | ICMJE / PROSPERO attribution | 1006 | 92.5% |
| RM-H04 | N/A gate reported as a pass | 999 | 91.8% |
| RM-F04 | interface state desync | 991 | 91.1% |
| RM-H02 | inadmissible estimator at small k | 976 | 89.7% |
| RM-B01 | scope-lock failure | 939 | 86.3% |
| RM-A02 | estimand mixing | 810 | 74.4% |
| RM-J02 | retrospective framed as prospective | 808 | 74.3% |
| RM-H05 | benchmark scope mismatch | 807 | 74.2% |
| RM-D08 | false registry-status claim | 767 | 70.5% |
| RM-A14 | escalc over mixed endpoints | 744 | 68.4% |
| RM-A05 | continuous into a ratio model | 748 | 68.8% |
| RM-G03 | RoB chip contradicts its own evidence | 701 | 64.4% |
| RM-F01 / RM-F03 | false-green badge / self-contradiction | 802 | 73.7% |
| RM-F02 | verdict-surface disagreement | 596 | 54.8% |
| RM-D07 | "no external benchmark" fallback | 171 | 15.7% |
| RM-J05 | COMPLETED-only registry filter | 216 | 19.9% |
| RM-H03 | fragility index where undefined | 207 | 19.0% |

> **Phase-1 estimate: ~909 root apps (~1,088 including sub-directory copies) are fixed
> STRUCTURALLY in one pass, for 24 of the 67 error types — including 11 of the 12 types above 85%.**
> No per-app source verification is needed for any of them, because none of them is a data error.

## 1.4 Phase-1 execution order

1. **Land the guards in the generator/template first**, not in the 909 files. Patch
   `scripts/clone_dashboard.py` / `generate_new_apps.py` / the v12 template so that any app
   regenerated or cloned from here on is born correct.
2. **Write the injection script** that applies the same patch to existing apps by **balanced-span
   replacement**, never regex-and-append. Badges are replaced **wholesale** (RM-F03).
3. **Line endings:** `newline=""` on **both** read and write. After every edit
   `git diff --numstat` must show a line count proportional to the **edit**, not the **file**
   (RM-J06). A whole-file rewrite makes a 909-app change unreviewable.
4. **Pilot on 5 apps**, then re-run the sweep on those 5 and assert the 24 structural types drop to
   zero. **A structural type that does not drop to zero means the patch missed a slot** — find it
   before scaling.
5. **Then the full pass**, in chunks of ~100 with a sweep re-run after each chunk.
6. **Negative-test the injection**: seed a reverted app and confirm the verifier BLOCKS.
7. **Cross-family gate on the PATCH** (Claude → Codex → agy-Gemini), then Mahmood's go.

**What Phase 1 explicitly does NOT fix:** every data error. A green Phase-1 app can still carry a
wrong NCT, a fabricated count, an inverted arm, or an omitted trial. **Phase 1 must not be reported
as "the corpus is fixed."**

---

# PHASE 2 — DATA-REMEDIATION BATCHES

## 2.1 Scoring

After removing the 28 Phase-1 structural types, each app is scored:

```
score = Σ  severity_weight(type) × (1 − prevalence(type))
        over its remaining DATA error types
severity_weight: P0 = 10, P1 = 4, P2 = 1
```

**A P0 that is RARE ranks high; a P0 present in 95% of apps is structural and Phase 1 owns it.**
That inversion is deliberate — it is what makes the ordering carry information.

Ordering: **apps with a source-verified fixture first** → **priority lane** → **score** → name.

## 2.2 The four priority lanes

| Lane | ids | why it goes first |
|---|---|---|
| **L1 live-harm** | `RM-I01` `RM-I02` `RM-A12` `RM-A10` `RM-C03` `RM-C04` `RM-V01` | direction inversion, an effect contradicting its own 2×2, a KM risk rendered as a count, arm reversal, a fixture-verified value error. **A reader acting on these acts wrongly.** |
| **L2 contamination** | `RM-E03` `RM-E02` `RM-E01` | a live monitoring watchlist or a claim-bearing slot carrying another drug class — the finerenone watchlist, the "non-steroidal MRA" descriptor, the PARADIGM alias table |
| **L3 wrong identity** | `RM-D01` `RM-D06` `RM-D10` `RM-D02` `RM-D12` | a wrong NCT importing foreign eligibility text, a NULLED ghost row, a wrong citation, a filename naming a different subject |
| **L4 completeness** | `RM-B08` `RM-B05` `RM-A13` `RM-A01` `RM-A03` | an omitted eligible trial, k far below a known synthesis, composites pooled across different component sets |

## 2.3 Scale

| | |
|---|---:|
| Apps with ≥ 1 **data** (non-Phase-1) error | **1,088** |
| Scheduled now, in 24 gated batches of 8 | **192** |
| Backlog after those | 896 |
| Estimated effort, 24 batches | **≈ 656 h** |
| Effort model (per app) | `1.6 h + 0.33·k + 0.08·findings` |

The effort model is calibrated on the APIXABAN_ACS pilot's measured `95 min + 20·k + 5·findings`,
discounted because the detectors now pre-locate the findings.

## 2.4 BATCH 1 — the three calibration apps plus their nearest neighbours

**This is the batch to run first, and it is the only one with source-verified truth already in hand.**

| App | k | lanes | the specific work |
|---|---:|---|---|
| `MITRAL_FUNCMR_REVIEW.html` | 3 | L1 L2 L3 L4 | arm reversal (RESHAPE-HF2 device 250/control 255, displayed 255/250); recurrent rate ratio mislabelled HR; COAPT KM 29.1%/46.1% must not become counts; MITRA-FR 24-mo mortality 53/152 vs 52/152 HR 1.02; pool the three published mortality HRs by generic IV, **never the binary counts**; the external benchmark **exists** (ACM HR 0.76, 0.57–1.01) |
| `BEMPEDOIC_ACID_REVIEW.html` | 4 | L1 L2 L3 | CLEAR Wisdom NCT02973841 → **NCT02991118** (the wrong id is a 40-patient jugular-vein cannulation study whose eligibility text the app displays); citation JAMA 322(14):1380-1388 → **322(18):1780-1788, PMID 31714986**; Harmony 108/1488 vs 40/742 gives crude RR 1.346 against a displayed HR 0.75; two `NULLED:` ghost rows under a "Trials: 4" badge; ACM 434/434 → **434/420, HR 1.03**; stroke 133/156 → **135/158, HR 0.85** |
| `PCSK9_REVIEW.html` | 2 | L2 L4 | **the two trial rows are CORRECT to source** (FOURIER 1344/13784 vs 1563/13780, HR 0.85 0.79–0.92; ODYSSEY 903/9462 vs 1052/9462, HR 0.85 0.78–0.93 — both verified against PubMed this session). The work is the finerenone watchlist, FOURIER-vs-ODYSSEY composite mismatch, and under-inclusion (SPIRE/OSLER/ODYSSEY LONG TERM absent; a synthesis found 38 RCTs) |
| `e156-submission/assets/BEMPEDOIC_ACID_REVIEW.html` | 4 | same | the stale submission copy — **must be fixed with the root app or the bundle diverges** |
| `e156-submission/assets/PCSK9_REVIEW.html` | 2 | same | same |
| `COVID19_HOSPITALIZED_TX_REVIEW.html` | — | L3 | malformed identifier `NCT04381936c` |
| `HEMOPHILIA_GENE_THERAPY_REVIEW.html` | — | L1 L3 | |
| `TIRZEPATIDE_ARDS_AUTO_FULL_REVIEW.html` | 3 | L1 L3 | contains an **andexanet alfa** review; percent-change in the HR field (73.83, and a CI lower bound of −0.5509) |

**Batch-1 source needs:** ClinicalTrials.gov API v2 (every NCT) · PubMed (every PMID, plus
volume/issue/pages) · each trial's registered primary component set · the primary publication for
each KM-vs-count decision · the benchmark synthesis's own trial list · and for three of the eight,
**nothing** — their truth is already in `tests/fixtures/rapidmeta_error_fixtures.json`.

**Full batch list, batches 1–24, with apps, lanes, dominant error types and source needs:**
`outputs/rapidmeta_batch_list.json`. Regenerate with
`python scripts/rapidmeta_batch_plan.py --md`.

## 2.7 · PHASE-2 ITEM: the pooling-repair scope-lock fix (moved out of Phase 1)

**Registry: RM-B02 · 944 apps · per-app, source-verified · NOT a corpus-wide neutralisation.**

**Why it is here and not in Phase 1.** The Phase-1 patch originally shipped a textual
neutralisation (T4) of the `COMPLETE-POOLING-REPAIR` block. The cross-family re-gate proved by
2×2 isolation that **T4 alone sets `state.results = NULL` at load on ~944 apps** — reproduced on
`ACS_ANTIPLATELET` (k=4), `ABATACEPT_RA` (k=2) and `ABEMACICLIB` (k=2).

**Mechanism.** The block's `rerun()` is the **only unconditional load-time trigger** for
`AnalysisEngine.run()`; every other call site is gated on `activeTab === 'analysis'` or an event
handler. Disabling it removes the only thing that populates `state.results` at load, so the
pooled estimate goes **missing** until the reader opens the Analysis tab.

It does **not** produce a wrong number — the Analysis tab restores identical values — but
**a structural patch must never change a correct rendered result.** T4 was withdrawn.

**What the defect actually is** (the registry text was corrected too): on a **secondary** scope
the block injects `realData[id]`'s **top-level** `tE`/`cE`, which is the **primary** endpoint;
the per-endpoint values live in `allOutcomes[]`. So it renders the primary endpoint's counts
under a secondary endpoint's label, and force-sets `effectMeasure = "HR"`.

> **Withdrawn claim, recorded:** it does **not** add or remove trials. `inclTrials` only fills
> counts on rows already marked `s === "include"`; `k` is unchanged.

**The per-app fix, per batch:**
1. Bind the scoped row to its **own** `allOutcomes[]` entry; never fall back to the trial's
   top-level counts.
2. Where the scoped row genuinely has no counts, render **NA** and exclude the trial from the
   pool with a stated reason (G03/G05), rather than borrowing the primary's.
3. Do **not** force `effectMeasure`; resolve it from the scoped row's `estimandType` (G01/G06).
4. **Preserve the load-time trigger.** Give the app an unconditional `AnalysisEngine.run()` at
   load that does not depend on this block, and verify in-browser that `state.results` is
   populated at load and matches the Analysis-tab values exactly.
5. Source-verify every count that changes, per the standard batch procedure.

**Acceptance, per app:** `state.results` non-null at load; the load-time pooled estimate is
byte-identical to the Analysis-tab value; every scoped row's counts trace to its own
`allOutcomes[]` entry; no `effectMeasure` is forced.

**Detector:** `RM-B02` (existing, 92.8%) plus a render check — *does `state.results` exist at
load, and does it equal the Analysis-tab value?* — which is RENDER-class and cannot be measured
by the static sweep.

---

## 2.5 The per-batch procedure

Per app, in this order — this is `CARDIO_UPGRADE_RECIPE.md` v1.1 with the registry ids bound in:

1. **Phase R** — run every STATIC detector on the app **before** touching it; record the baseline.
2. **Re-source every flagged number** in this order: benchmark/meta supplements → ClinicalTrials.gov
   / AACT posted results → FDA / EMA / WHO-PQ review documents → open-access full text.
   **Every number and identifier by lookup, never recall.**
3. **Disposition every firing BY ID** — citation corrected · claim withdrawn · re-sourced ·
   quarantined · counts corrected. **Quarantine, never silent deletion.**
4. **Run the guards + G18 fail-closed gate** on the final file.
5. **Re-run the sweep** on the app; every dispositioned id must be gone or explained.
6. **Render it.** Serve over HTTP, walk every tab, re-read `state.selectedOutcome` after each,
   confirm 0 console errors and no stale value in the rendered text. *The HFrEF badge contradiction
   was found by rendering, after a file-level gate had passed it.*
7. **Check the diff shape** — `git diff --numstat` proportional to the edit (RM-J06).
8. **Cross-family gate**: Claude produces → **Codex (openai)** bug-hunts the code → **agy routed to
   Gemini (google)** re-derives. Each must **name its own model family from a real exec**; a lane
   titled "Codex" that is running Claude is a same-family pass and is VOID. Transport: **bash only**,
   with a marker echoed in the adversary's first line.
9. **Stage. Do not push.** Mahmood's go, per batch.

## 2.6 Definition of done, per batch

- [ ] Every STATIC detector run on every final file, every firing dispositioned **by id**
- [ ] Every re-sourced number carries its **quoted source field** and an evidence tier
- [ ] Every N/A gate printed **with its reason** — N/A is not a pass
- [ ] Both verdict surfaces agree; badge replaced **wholesale**
- [ ] Guards + **G18** pass, and the verifier has been **negative-tested to fail**
- [ ] Live render clean; no stale value anywhere in the rendered text
- [ ] Diff shape proportional to the edit
- [ ] Cross-family gate report naming **family, transport, marker result**
- [ ] Any correction that moves a headline carries: *"this is a provenance correction, not a result
      that got better or worse. The evidence did not change. The app was wrong."*
- [ ] **"Still not done"** list written
- [ ] Staged, committed on the batch branch, **NOT pushed**

---

## 3. Sequencing, and the one dependency that matters

```
Phase 1  ──►  pilot 5 ──► sweep-verify ──► full pass ──► cross-family gate ──► GO
   │
   └──►  Phase 2 batches run AFTER Phase 1 lands
```

**Phase 2 must not start before Phase 1 lands on the apps in the batch.** Otherwise every batch
re-fixes the same 24 structural types by hand, 909 times — which is the exact mistake the registry
exists to prevent. The only exception is **Batch 1**, which doubles as the Phase-1 pilot: its three
calibration apps have verified truth, so they can validate the engine patch *and* the data
procedure in one pass.

## 4. What this plan does not claim

1. **The sweep is STATIC.** 11 registry types are SOURCE-class and 2 are RENDER-class. **A zero in
   the sweep is not a clean result for those** — and treating it as one would be the N/A-as-pass
   error one level up.
2. **1,088 apps have a data error is an upper bound on batching, not a claim that 1,088 apps have a
   *serious* data error.** Many will resolve to a disposition of "no finding" once source-verified.
   The lanes exist so the serious ones are not queued behind the trivial ones.
3. **A detector firing is a hypothesis.** The HFrEF pass withdrew **three of its five** findings on
   verification. Budget for the withdraw step in every batch, and record it.
4. **656 h covers 192 apps.** The full corpus at this rate is a multi-month programme, and the
   estimate is a model, not a measurement, for every app but the one that was timed.
5. **Nothing here has been executed.** No app file is modified by this plan.
