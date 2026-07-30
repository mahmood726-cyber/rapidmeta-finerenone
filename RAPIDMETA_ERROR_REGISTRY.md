# RAPIDMETA ERROR REGISTRY

**Version:** 2.0 · **Date:** 2026-07-30 · **Branch:** `build/error-registry-2026-07-30`
**Status:** STAGED, committed on branch, **NOT PUSHED**. `main` is the deploy ref; this branch deploys nothing.

The canonical list of every error TYPE observed in the RapidMeta corpus across the reviews of
2026-07-28 → 2026-07-30. One entry per type. Each entry carries a **detector that can fail**, a
**fix**, the **apps it was observed in**, and whether the defect lives in the **shared base engine**
(in which case a per-app fix is not a fix).

**Nothing here is invented.** Every entry cites the artifact that recorded it. Where a defect was
named by a branch name but no commit landed, that is stated as such and the type is corroborated
from another app rather than asserted from the branch alone.

**67 error types · 52 STATIC detectors · 20 fail-closed guards · 3 source-verified fixtures.**

**v2.0 (2026-07-30)** adds 16 types from three calibration cases — the mitral-TEER app
(`MITRAL_FUNCMR_REVIEW.html`), `PCSK9_REVIEW.html` and `BEMPEDOIC_ACID_REVIEW.html`. All three are
**priority batch targets** and their source-verified extraction truth is recorded as a labelled test
case in `tests/fixtures/rapidmeta_error_fixtures.json`. See §14.

| Companion artifact | What it does |
|---|---|
| `assets/js/rapidmeta-guards.js` | the 17 guards, G01–G17. Fail closed: a guard that cannot decide BLOCKS |
| `tests/test_rapidmeta_guards.mjs` | `node --test` — every BLOCK case seeded with the value that actually shipped |
| `tests/mutate_guards_selftest.py` | re-seeds **14** shipped defects into the guards; each must be caught (14/14) |
| `tests/fixtures/rapidmeta_error_fixtures.json` | the 3 worked examples: what each app DISPLAYS vs what the source SAYS, per error id |
| `RAPIDMETA_BATCH_PLAN.md` | Phase-1 engine patch (909 root apps) + the 24 gated Phase-2 data batches |
| `scripts/rapidmeta_error_sweep.py` | every STATIC detector, per app or corpus-wide; `--selftest` proves they fire |
| `RAPIDMETA_ERROR_SWEEP.{md,json}` | the corpus prevalence matrix this registry drives |
| `F:\E156\GOVERNING-RULES-ADDENDUM-ERROR-REGISTRY-2026-07-30.md` | §18 — the governing rules that make all of it mandatory |

---

## 0. Sourcing key

| Tag | Artifact |
|---|---|
| `[BUG-CAT]` | Orchestrator memory `rapidmeta-generator-bug-catalogue.md` (2026-07-30) |
| `[HARNESS]` | `F:\E156\HARNESS-FAILURE-MODES-2026-07-30.md` (F-01…F-12) |
| `[APIXABAN]` | `outputs/APIXABAN_ACS_PILOT_2026-07-30.md` (branch `audit/cardio-program-2026-07-30`) |
| `[RECIPE-C]` | `outputs/CARDIO_UPGRADE_RECIPE.md` |
| `[RECIPE-GH]` | `GLOBAL_HEALTH_UPGRADE_RECIPE.md` |
| `[HFREF]` | `outputs/HFREF_INTEGRITY_GATES_2026-07-30.md`, `outputs/HFREF_FINDINGS_RESOLVED_2026-07-30.md` |
| `[IRON]` | `IV_IRON_HF_SCOPE_LOCK_LEDGER.md` (branch `fix/iv-iron-hf-scope-lock-2026-07-30`) |
| `[SGLT2]` | `SGLT2_HF_CORRECTION_LEDGER.md` (branch `fix/sglt2-hf-soloist-recurrent-2026-07-30`) |
| `[RIFA]` | `outputs/RIFAPENTINE_TB_INTEGRITY_GATES_2026-07-30.md` (branch `upgrade/tb-prevention-rifapentine-2026-07-30`) |
| `[ARNI]` | Commits `d906ba931 c641f552f 6985c85cd ecc68e1e3 554b6f2a2 ea1a8fea1 ce187425e b0dbdd1ed` |
| `[SOTA]` | Commits `56c74b87c c682aa9b4 eb67df36c 765318c3c ecb64eaec d5ec48c16 9bd584001 bd43222da b1cef25fb 96bc2b03e` |
| `[CARDIO-MIS]` | `outputs/CARDIO_MISLABELLED_APPS_2026-07-30.md` |
| `[ACS-GATE]` | Commits `cb876d805 e55235fe8 acc656de0` (APIXABAN_ACS cross-family gate rounds 1–3) |
| `[VIVAX]` | Commits `5c8a8c5b8 1c0c0bb6d 5544d4260 1daa80c2e 9b739aa65` |
| `[ATTR]` | Commit `9e658033f` (ATTR-CM / HELIOS-B wrong-NCT repair) |
| `[INCRETIN]` | Commits `788156034 494cf2631 ac777b130` (incretin-HFpEF scope lock, provenance, Tier 1) |
| `[MAVA]` | Commits `ecd1aba43 155bb96c1 a399133aa` (mavacamten HCM Tiers 1–3) |

**Detector class:**
`STATIC` = implemented in `scripts/rapidmeta_error_sweep.py`, runs on the file alone ·
`RENDER` = requires serving the app and driving it in-browser ·
`SOURCE` = requires a registry / PubMed / regulator lookup, per-app.

**Guard column** names the fail-closed guard in `assets/js/rapidmeta-guards.js` that makes the
defect structurally impossible, where one exists.

---

## 1. INDEX — 51 error types

| id | name | family | detector | guard | base-engine-shared |
|---|---|---|---|---|---|
| RM-A01 | Recurrent-event coercion | estimand | STATIC | G01,G06 | **yes** |
| RM-A02 | Estimand mixing in one pool | estimand | STATIC | G06 | **yes** |
| RM-A03 | Wrong effect-measure label | estimand | STATIC | G02 | **yes** |
| RM-A04 | Peto output labelled HR | estimand | STATIC | G02 | **yes** |
| RM-A05 | Continuous outcome in a ratio model | estimand | STATIC | G01 | **yes** |
| RM-A06 | Rate read as a proportion → manufactured counts | estimand | SOURCE | G15 | **yes** |
| RM-A07 | Non-ratio quantity in a ratio field | estimand | STATIC | G01 | **yes** |
| RM-A08 | Component counts paired with a composite effect | estimand | STATIC | G04 | **yes** |
| RM-A09 | Hierarchical (win-ratio) estimate paired with an HR | estimand | STATIC | G01 | **yes** |
| RM-B01 | Scope-lock failure (selector does not filter) | scope | STATIC | G03,G07 | **yes** |
| RM-B02 | Stale outcome-state leakage across selector change | scope | STATIC | G07 | **yes** |
| RM-B03 | Silent endpoint fallback (`outcomes[0]` heuristic) | scope | STATIC | G03 | **yes** |
| RM-B04 | Outcome substitution (wrong outcome row extracted) | scope | SOURCE | — | no |
| RM-B05 | Omitted eligible trial (selection bias) | scope | SOURCE | — | no |
| RM-B06 | PICO / population mismatch row | scope | SOURCE | G09 | no |
| RM-B07 | Undisclosed arm dropping / multi-arm collapse | scope | SOURCE | G09 | no |
| RM-C01 | Randomised vs analysed denominator unlabelled | population | STATIC | G05 | partly |
| RM-C02 | Arm value presented as the overall value | population | SOURCE | — | no |
| RM-C03 | Arm orientation inversion (bound by index) | population | SOURCE | G15 | **yes** |
| RM-D01 | Wrong NCT / registry-concordance failure | provenance | STATIC+SOURCE | G09 | no |
| RM-D02 | Wrong or cross-topic citation | provenance | STATIC+SOURCE | — | no |
| RM-D03 | Protocol/design paper cited for outcome data | provenance | SOURCE | — | no |
| RM-D04 | Fabricated counts (reconcile with nothing) | provenance | SOURCE | G15 | no |
| RM-D05 | Fabricated / imported analysis row | provenance | STATIC | G14 | no |
| RM-D06 | App identity mismatch (filename ≠ content) | provenance | STATIC | G13 | no |
| RM-E01 | Cross-topic template contamination | contamination | STATIC | G14 | **yes** |
| RM-E02 | Foreign trial-alias registry | contamination | STATIC | G14 | **yes** |
| RM-F01 | False-green verdict badge | verdict | STATIC | G12 | **yes** |
| RM-F02 | Verdict-surface disagreement | verdict | STATIC | G12 | **yes** |
| RM-F03 | Badge self-contradiction | verdict | STATIC | G12 | **yes** |
| RM-F04 | Interface state desync (version / rounds / scope) | verdict | STATIC | G12 | **yes** |
| RM-F05 | Missing rendered as zero | display | STATIC | G05 | **yes** |
| RM-F06 | Impossible PRISMA zeros | display | STATIC | G05 | **yes** |
| RM-F07 | Unearned confidence on unsourced fields | display | STATIC | G11 | **yes** |
| RM-F08 | Selective reporting of the favourable interval | display | STATIC | G16 | **yes** |
| RM-G01 | `safeRob` unknown → "low" | RoB | STATIC | G08 | **yes** |
| RM-G02 | RoB asserted from design fields alone | RoB | STATIC | G08 | **yes** |
| RM-H01 | k-inappropriate machinery | machinery | STATIC | G10 | **yes** |
| RM-H02 | Inadmissible estimator / uninterpretable τ² at small k | machinery | STATIC | G10 | **yes** |
| RM-H03 | Fragility index where undefined | machinery | STATIC | G10 | **yes** |
| RM-H04 | N/A gate reported as a pass | machinery | STATIC | G12 | **yes** |
| RM-H05 | External-validation claim against a different-scope benchmark | machinery | STATIC | G11 | **yes** |
| RM-H06 | Non-inferiority margin discarded into a superiority pool | machinery | SOURCE | — | no |
| RM-I01 | Direction inversion (benefit ↔ harm) | direction | STATIC | G17 | **yes** |
| RM-I02 | Good-outcome / bad-outcome sign conflict in one pool | direction | SOURCE | G17 | **yes** |
| RM-J01 | False ICMJE / PROSPERO equivalence attribution | governance | STATIC | G11 | **yes** |
| RM-J02 | Retrospective protocol framed as prospective | governance | STATIC | G11 | **yes** |
| RM-J03 | Eligibility criteria self-contradiction | governance | SOURCE | — | no |
| RM-J04 | Gate that cannot fail | process | STATIC | — | n/a |
| RM-J05 | COMPLETED-only registry filter | process | STATIC | — | **yes** |
| RM-J06 | Line-ending drift / whole-file rewrite on edit | process | STATIC | — | n/a |

---

## 1a. MEASURED PREVALENCE — corpus sweep, 2026-07-30

`python scripts/rapidmeta_error_sweep.py` over **1,659** `*_REVIEW.html` files.
**1,088 apps scanned** (571 redirect stubs < 20 KB excluded from the denominator) ·
**0 detector errors** · **19 apps whose `realData` ledger did not parse** — recorded as a finding
about those apps, not as a clean result, so every ledger-based count below is measured on 1,069.

> **Every one of the 1,088 apps has at least one static finding.** That number is not a
> catastrophe headline; it is what "the defect is in the base engine" means arithmetically.
> Twelve types sit above 85%, and each of those twelve is one shared code path.

| id | sev | apps | % | note |
|---|---|---:|---:|---|
| `RM-F05` | P1 | 1059 | 97.3% | |
| `RM-I01` | P1 | 1053 | 96.8% | **no app in the corpus carries an outcome polarity field** |
| `RM-H01` | P1 | 1049 | 96.4% | |
| `RM-E01` | P0 | 1035 | 95.1% | evidence tagged CLAIM-BEARING vs residue for triage |
| `RM-B03` | P0 | 1024 | 94.1% | |
| `RM-B02` | P0 | 1010 | 92.8% | |
| `RM-G01` | P0 | 1006 | 92.5% | |
| `RM-J01` | P0 | 1006 | 92.5% | |
| `RM-H04` | P1 | 999 | 91.8% | |
| `RM-F04` | P2 | 991 | 91.1% | |
| `RM-H02` | P1 | 976 | 89.7% | |
| `RM-B01` | P0 | 939 | 86.3% | |
| `RM-A02` | P0 | 810 | 74.4% | |
| `RM-J02` | P1 | 808 | 74.3% | |
| `RM-H05` | P1 | 807 | 74.2% | |
| `RM-F03` | P0 | 802 | 73.7% | |
| `RM-F01` | P0 | 802 | 73.7% | matches `[BUG-CAT]`'s independent "~70% of cardio apps" |
| `RM-A05` | P0 | 748 | 68.8% | |
| `RM-E02` | P1 | 716 | 65.8% | measured, against `[RIFA]`'s recalled **526** — see below |
| `RM-F02` | P0 | 596 | 54.8% | |
| `RM-D05` | P1 | 351 | 32.3% | |
| `RM-A07` | P0 | 315 | 29.0% | |
| `RM-J05` | P2 | 216 | 19.9% | |
| `RM-H03` | P1 | 207 | 19.0% | |
| `RM-G02` | P2 | 169 | 15.5% | |
| `RM-A03` | P1 | 168 | 15.4% | |
| `RM-A08` | P1 | 165 | 15.2% | |
| `RM-D02` | P1 | 132 | 12.1% | |
| `RM-C01` | P2 | 30 | 2.8% | |
| `RM-D06` | P1 | 21 | 1.9% | |
| `RM-F07` | P1 | 17 | 1.6% | |
| `RM-D01` | P1 | 10 | 0.9% | all 10 are malformed identifiers, e.g. `NCT01206062_SENIOR` |
| `RM-A01` | P0 | 8 | 0.7% | |
| `RM-A09` | P1 | 3 | 0.3% | |
| `RM-A04` | P1 | 3 | 0.3% | |
| `RM-F06` | P1 | 0 | 0.0% | **not measurable statically** — see below |

**Three results that correct or qualify what was recorded before this sweep:**

1. **`RM-E02` is 716 apps, not 526.** `[RIFA]` §4 recorded 526 from an earlier count. The measured
   figure is **716 of 1,088 (65.8%)** by the topic-conditional detector. Use the measured number.
2. **`RM-A04` "Peto HR" is nearly absent — 3 apps.** The corpus overwhelmingly labels it **"Peto
   OR"** correctly (verified by reading the `_petoPool` call sites). The three real instances are
   `INCRETIN_HFpEF_REVIEW.html`, which carries a literal outcome title
   *"Worsening HF events (**Peto HR** from counts)"*, and two apps whose `res-mh` branch prints an
   HR label beside a Peto result. `[BUG-CAT]` listed this as an engine guard; it is a correct guard
   against a **rare** defect, and the registry now says so rather than implying corpus scale.
3. **`RM-F06` reports 0 because it cannot see the data, not because the corpus is clean.** PRISMA
   counts are rendered by `vendor/prisma-flow.js` from data the static sweep cannot reach. The
   detector returns **no verdict** for those apps rather than a false clean. This is the registry's
   own §18.4 rule applied to itself: **N/A is not a pass.**

**Worst offenders overall** — apps hitting the most distinct error types (24 of 36 each):
`INDACATEROL_GLYCOPYR_COPD_AUTO_FULL_REVIEW.html` · `VADADUSTAT_RENAL_ANEMIA_AUTO_FULL_REVIEW.html`
· `INCLISIRAN_LIPID_KIDNEY_AUTO_FULL_REVIEW.html` · `VADADUSTAT_ANEMIA_AUTO_FULL_REVIEW.html` ·
`ALIROCUMAB_LIPID_AUTO_FULL_REVIEW.html` · `TIRZEPATIDE_ARDS_AUTO_FULL_REVIEW.html`.

**Two bugs in the sweep itself, found and fixed before these numbers were trusted** — recorded
because a detector that is silently blind is the same failure class the registry documents:

- **Basename keying collided.** Results were keyed by filename, and **17 basenames occur twice**
  (a root app plus a stale copy under `e156-submission/assets/`). The copy overwrote the root app's
  row, so a known-bad app reported clean. Now keyed by **relative path**.
- **The JS-literal parser choked on minified booleans.** `serious:!0` raised `unexpected '!'`, and
  the failure was **swallowed** — `realData` came back empty and every ledger-based detector went
  quiet on a file that looked scanned. `!0`/`!1`/`void 0` are now parsed, and an unparsable ledger
  is **reported** (`unparsable_ledgers` in the JSON, and a line in the report's corpus table).

Full matrix, per-app evidence and worst-offender lists: `RAPIDMETA_ERROR_SWEEP.{md,json}`.

---

## 2. FAMILY A — ESTIMAND AND MEASURE

### RM-A01 · Recurrent-event coercion
**One line.** A recurrent-event or rate endpoint is force-fitted into a binary 2×2, or relabelled
"continuous", or relabelled a hazard ratio, because the engine has no representation for the estimand.

**Root cause.** The trial-record schema has exactly three shapes — 2×2 counts, a published HR, and a
continuous mean difference. A recurrent-event total (`245`, `355`) is written into `tE`/`cE`, so the
totals are read as *patients with an event* and divided by the randomised n, producing a percentage
that is not a risk. `[BUG-CAT] #1`, `[SGLT2]` SOLOIST-WHF row, `[IRON]` AFFIRM-AHF and IRONMAN rows.

**Detector (STATIC).** For every trial row: flag when `tE > tN` or `cE > cN`; **and** — the case that
survives arithmetic checks — flag when a trial known to report a recurrent-event primary carries a
`type:"PRIMARY"` row with per-arm counts and a percentage is rendered from them. The corpus-safe form
is a **name-keyed** check against the recurrent-event trial list:
```
rg -o 'SOLOIST[^"]{0,40}|AFFIRM-AHF|IRONMAN|PARAGON-HF|EMPACT-MI' *_REVIEW.html
# then, in the same realData block, assert estimandType is RATE_RATIO and no tE/cE pair exists
python scripts/rapidmeta_error_sweep.py --only RM-A01
```
Fails when a listed trial carries `tE`/`cE` **and** `estimandType` is absent, `"HR"`, `"RR"`, or `"MD"`.

**Fix.** Add `RATE_RATIO` to the estimand taxonomy. Store totals as `eventsTotal`, never `tE`.
Render "N vs M total events" plus the published per-100-patient-year rates; never a proportion of the
randomised n. Carry the published recurrent-event HR/rate ratio as the effect. `[SGLT2]` d414b27eb,
`[SOTA]` 56c74b87c, `[IRON]` §2.

**Observed in.** `SGLT2_HF_REVIEW.html` (SOLOIST-WHF), `SOTAGLIFLOZIN_*` (SCORED + SOLOIST),
`IV_IRON_HF_REVIEW.html` (AFFIRM-AHF, IRONMAN), `ARNI_HF_REVIEW.html` (PARAGON-HF).

**Base engine: YES.** The schema and the percentage renderer are shared.

---

### RM-A02 · Estimand mixing in one pool
**One line.** Hazard ratios, rate ratios, win ratios, risk ratios and continuous ratios are pooled
into a single random-effects model.

**Root cause.** The poolability test was a **denylist** — `"RR" !== String(d?.estimandType ?? "HR")`
— so anything that was not literally `"RR"` was treated as a hazard ratio and admitted. `[ARNI]`
c641f552f. A rate ratio therefore entered a hazard-ratio model unchallenged.

**Detector (STATIC).** Collect the distinct `estimandType` values among the trials actually entering
the pool; flag when the set has >1 member and a single pooled estimate is rendered.
```
python scripts/rapidmeta_error_sweep.py --only RM-A02
# grep form (finds the denylist itself, which is the root cause):
rg -c '"RR"\s*!==\s*String\(' *_REVIEW.html
```
Fails on any file still carrying the denylist, or any file whose pooled `k` counts trials of ≥2 estimand types.

**Fix.** Replace the denylist with an **allowlist** (`"HR" === estimandTypeOf(trial)`), publish an
estimand taxonomy (`HR` / `RATE_RATIO` / `RATIO_CONTINUOUS` / `RR` / `OR` / `WIN_RATIO`), and pool
**within stratum only**. Render one panel per stratum with the held-out trials named alongside their
estimand. `[ARNI]` c641f552f + ecc68e1e3; `[SGLT2]` 2083ee8bf; `[SOTA]` ecb64eaec.

**Observed in.** `ARNI_HF_REVIEW.html` (HR + rate ratio + win ratio + continuous → spurious 0.84),
`SGLT2_HF_REVIEW.html` (first-event HRs + SOLOIST recurrent), `SOTAGLIFLOZIN_*`, `IV_IRON_HF_REVIEW.html`.

**Base engine: YES.**

---

### RM-A03 · Wrong effect-measure label
**One line.** The same number is called `RR` in one field and `publishedHR` in another, or a rate
ratio is displayed as a hazard ratio.

**Root cause.** Two independent label sites (the trial record's `estimandType` and the outcome row's
`publishedHR` key) with no consistency check between them. `[SGLT2]` SOLOIST row: `estimandType "RR"`
against `publishedHR 0.67` for the same estimate.

**Detector (STATIC).** Within one trial record, assert `estimandType` is consistent with which effect
key carries the value; and assert the rendered label string matches `estimandType`.
```
python scripts/rapidmeta_error_sweep.py --only RM-A03
```
Fails when `estimandType:"RR"` co-occurs with `publishedHR`, or when the rendered measure word
disagrees with the stored estimand tag.

**Fix.** One effect-measure field per estimate, and the display label is derived from it, never
hardcoded. `[SGLT2]` ea489efae, `[SOTA]` ecb64eaec.

**Observed in.** `SGLT2_HF_REVIEW.html`, `SOTAGLIFLOZIN_*`.

**Base engine: YES.**

---

### RM-A04 · Peto output labelled HR
**One line.** A Peto odds ratio is presented as a hazard ratio.

**Root cause.** The Peto estimator is an odds-ratio method; the display layer inherits the app's
default "HR" wording. `[BUG-CAT]` ⭐⭐ guard 2 — *"Peto HR is a contradiction"*.

**Detector (STATIC).**
```
rg -i 'peto[^<]{0,60}(hazard ratio|HR\b)' *_REVIEW.html
python scripts/rapidmeta_error_sweep.py --only RM-A04
```
Fails on any co-occurrence of `Peto` with an HR label inside the same rendered element.

**Fix.** Guard **G02**: the Peto branch stamps `measure = "OR"` on its own output and the label is
read from that stamp. Also print the Peto large-effect bias caveat. `[BUG-CAT]` guard 2.

**Observed in.** **3 apps of 1,088 (0.3%)** — this is a correct guard against a **rare** defect, not
a corpus-wide one. The corpus overwhelmingly labels it **"Peto OR"** correctly. The real instance is
`INCRETIN_HFpEF_REVIEW.html`, carrying the literal outcome title *"Worsening HF events (**Peto HR**
from counts)"*; `COLCHICINE_CVD_REVIEW.html` and `GLP1_CVOT_REVIEW.html` print an HR label beside a
Peto result in the `res-mh` branch.

**Base engine: YES.**

---

### RM-A05 · Continuous outcome in a ratio model
**One line.** A continuous endpoint enters an HR / OR / RR model, or one continuous trial routes the
*whole* analysis to the continuous engine.

**Root cause.** Two symmetric bugs. (a) A continuous estimate is admitted to the ratio pool because
the poolability test is a denylist (RM-A02). (b) `trials.some(...)` sent the whole analysis to
`ContinuousMDEngine` if **any** trial had a continuous outcome, and `pool()` then fell back to
`||{md:t.data.md, se:t.data.se}` for the trials lacking that outcome — silently substituting a
different estimand for them. `[ARNI]` ea1a8fea1.

**Detector (STATIC).**
```
rg -c 'trials\.some\([^)]{0,80}continuous|\|\|\s*\{\s*md\s*:' *_REVIEW.html
python scripts/rapidmeta_error_sweep.py --only RM-A05
```
Fails on the `trials.some(...)`-routing pattern, on the `||{md:…}` fallback, or on a rendered ratio
pool whose contributing set includes a `RATIO_CONTINUOUS` / `MD` trial.

**Fix.** Guard **G01**, fail-closed: a continuous estimate can never be converted into or admitted to
a ratio model; route **only** the continuous trials to the continuous engine; delete the fallback and
name the held-out trials with their estimand. `[ARNI]` ea1a8fea1, `[BUG-CAT]` guard 1.

**Observed in.** `ARNI_HF_REVIEW.html` (PARAGON routed as continuous), `SOTAGLIFLOZIN_*`
(SCORED/SOLOIST mislabelled "continuous", `[SOTA]` 56c74b87c).

**Base engine: YES.**

---

### RM-A06 · Rate read as a proportion → manufactured counts
**One line.** A ClinicalTrials.gov value posted in units of *events per 100 patient-years* is
multiplied by an arm denominator and stored as an event count; the resulting count exists in no document.

**Root cause.** The extractor reads `outcomeMeasure.value` without reading `unitOfMeasure`.
`"percentage of participants"` is a proportion and the multiplication is valid; `"percentage of
participants/100-pt years"` and `"Percentage per year"` are incidence rates and the multiplication
fabricates a number. `[APIXABAN]` §2.1 — the single highest-yield check in the recipe.

**Detector (SOURCE).** For each ledger count, pull the registry's posted outcome and its
`unitOfMeasure`; recompute `value × denominator / 100` against **both** the registry denominators and
the ledger's own denominators. Reproduction to <1 unit on a rate-unit outcome is the finding.
Implemented as gate **G6b** in `scripts/cardio_integrity_gates.py`.

**Fix.** Read `unitOfMeasure` before using any posted value; refuse to derive a count from a
person-time rate; carry the rate as a rate with its person-time denominator, or leave the count blank
with a stated reason. Guard **G15**. `[APIXABAN]` §7, `[ACS-GATE]` e55235fe8.

**Observed in.** `APIXABAN_ACS_AUTO_FULL_REVIEW.html` — APPRAISE-2 `515/489` reproduce as
`3687 × 13.96/100` and `3705 × 13.20/100` (true counts 293 and 279); AUGUSTUS `284/413` reproduce as
`1153 × 24.66/100` and `1153 × 35.79/100`. Max deviation over the four, measured: **0.3413**
(`[ACS-GATE]` acc656de0 R2).

**Base engine: YES** — the extractor is shared.

> **Corrected sub-claim, recorded because the correction is the finding** (`[ACS-GATE]` e55235fe8 G2):
> round 1 asserted AUGUSTUS's denominator 1153 "matches no arm of the trial". That is **false** —
> 1153 is the randomised size of each apixaban cell of the 2×2 factorial. The real defect is a
> **level-of-aggregation mismatch**: a factorial-*cell* denominator paired with a factor-*level*
> marginal rate (analysed on 2290 and 2259), compounded by applying the apixaban-side cell figure to
> the VKA arm, whose cells are 1154.

---

### RM-A07 · Non-ratio quantity in a ratio field
**One line.** A percent change from baseline, or any other non-ratio quantity, is stored in the
hazard-ratio field.

**Root cause.** The extractor writes whatever numeric "effect" it finds into `pubHR`/`publishedHR`
without a domain check. Two structural proofs it is a mistype, not an implausible value: a hazard
ratio of **73.83**; and a lower confidence bound of **−0.5509**, which is impossible for a ratio of
positive rates and yields `NaN` under any log transform. `[CARDIO-MIS]` §1 F1.

**Detector (STATIC).**
```
python scripts/rapidmeta_error_sweep.py --only RM-A07
```
Fails when any `pubHR`/`publishedHR`/`hrLCI`/`hrUCI`/`effect`/`lci`/`uci` value is ≤ 0, or when the
point estimate exceeds 20, or when the outcome title matches `percent change|change from baseline|
absolute change` while the value sits in a ratio field.

**Fix.** Guard **G01** extended: ratio fields accept only finite values > 0; a title matching a
change-from-baseline pattern forces the value into a continuous slot with its unit. Fail closed —
render "effect measure not resolvable" rather than a number.

**Observed in.** `TIRZEPATIDE_ARDS_AUTO_FULL_REVIEW.html` (which contains an **andexanet alfa**
review — see RM-D06): `NCT02220725` pubHR 73.83, `NCT02207725` pubHR 73.15, `NCT02329327` pubHR
0.80 with CI `(−0.5509, 2.1509)`. All three rows' outcome titles read "Percent Change From Baseline
in Anti-fXa Activity".

**Base engine: YES.**

---

### RM-A08 · Component counts paired with a composite effect
**One line.** Per-arm counts for one component of a composite endpoint are displayed beside the
hazard ratio for the whole composite.

**Root cause.** The count extractor and the effect extractor resolve the outcome independently, so a
row can carry counts from a *worsening-HF-alone* outcome and an effect from the *composite*.
`[BUG-CAT]` guard 4 — SUMMIT `29/52` is worsening-HF alone, not the composite.

**Detector (STATIC).** Assert that the count row and the effect row resolve to the same
`shortLabel`/`title`; and that the crude effect recomputed from the counts is within a stated
tolerance of the displayed effect (this is gate **G8**, `[RECIPE-C]` §3).
```
python scripts/rapidmeta_error_sweep.py --only RM-A08
```
Fails when the crude 2×2 and the published effect point in **opposite directions**, or when the count
row's label differs from the effect row's label.

**Fix.** Guard **G04**, fail-closed: counts and effect must carry the same outcome key, or the counts
are not rendered. `[BUG-CAT]` guard 4.

**Observed in.** Named in `[BUG-CAT]` (SUMMIT). The direction form of the same defect is measured:
`APIXABAN_ACS` APPRAISE-2 carries HR 0.95 beside counts giving RR 1.058 — gate G8, 1 HIGH
(`[APIXABAN]` §3).

**Base engine: YES.**

---

### RM-A09 · Hierarchical (win-ratio) estimate paired with an HR
**One line.** A hazard ratio is attached to a hierarchical composite whose only reported estimate is
a win ratio.

**Root cause.** Same mechanism as RM-A08: an effect field is populated from a different analysis than
the one the row names. `[IRON]` §3 HEART-FID — `HR 0.93 (0.81–1.06)` attached to the hierarchical
primary, and no such hazard ratio exists in the NEJM abstract or the registry results.

**Detector (STATIC).**
```
rg -i 'win ratio' *_REVIEW.html   # then assert no HR field on the same row
python scripts/rapidmeta_error_sweep.py --only RM-A09
```
Fails when a row whose title or `estimandType` says win ratio also carries `publishedHR`/`pubHR`.

**Fix.** Remove, do **not** reassign — moving the HR to a CV-death/HF-hosp row would itself be
unsourced. `[IRON]` §3. Guard **G01** rejects the pairing.

**Observed in.** `IV_IRON_HF_REVIEW.html` (HEART-FID). Also: the displayed win ratio itself was wrong
— `1.02 (99% CI 0.87–1.18; P=0.78)` against the published unmatched win ratio **1.10 (0.99–1.23),
P = 0.02** vs a prespecified α of **0.01**.

**Base engine: YES.**

---

## 3. FAMILY B — SCOPE AND SELECTION

### RM-B01 · Scope-lock failure
**One line.** The outcome selector reads "All-cause mortality" while each trial displays a different
endpoint — recurrent composites, win ratios, CV-death composites.

**Root cause.** Label and binding were decoupled. `outcomeLabel("default")` returned the **modal
outcome title** across the trial corpus, while `applyOutcomeScope("default")` bound each trial to
**`outcomes[0]`** — that trial's own primary composite. Three of four trials carried an
`AllCauseMortality` row, so "All-cause mortality" became the visible label of a binding that never
selected it. `[IRON]` §1 Defect 1; `[BUG-CAT]` #3.

**Detector (STATIC).**
```
python scripts/rapidmeta_error_sweep.py --only RM-B01
```
Fails when `outcomeLabel` derives from a frequency sort (`sort((a,b)=>b.count-a.count)`) while
`applyOutcomeScope` indexes `outcomes[0]` / `allOutcomes[0]`. Grep form:
```
rg -c 'sort\(\(a,b\)=>b\.count-a\.count\)' *_REVIEW.html
rg -c 'allOutcomes\[0\]|outcomes\[0\]' *_REVIEW.html
```

**Fix.** Type every outcome row (`scopeClass`, `unit`, `estimandType`); the selector offers **scope
classes**, not per-trial labels; a scope admits only rows whose `scopeClass` matches; a trial with no
matching row is **excluded with a stated reason**, never shown carrying another endpoint's numbers.
Guard **G03**. `[IRON]` §2.

**Observed in.** `IV_IRON_HF_REVIEW.html` (confirmed and reproduced) and
`INCRETIN_HFpEF_REVIEW.html` (`[INCRETIN]` 788156034), which is the **same two-resolver root cause,
independently found**: the app declared a *"KCCQ-CSS change at 52 weeks"* scope while all three
trials pooled cardiovascular-event outcomes, because `outcomeLabel()` resolved the label by
frequency across trials (→ KCCQ, present in all 3) while `applyOutcomeScope()` resolved the payload
positionally as `allOutcomes[0]` (→ the CV-event outcome). **The UI advertised KCCQ; the engine
consumed CV events.** Fixed with a single canonical resolver plus defence in depth: a scope miss
**hard-excludes** the trial instead of falling back, and event counts are **nulled** when the scoped
outcome has none, so CV counts cannot reach a continuous-scope pool.

**Base engine: YES.**

---

### RM-B02 · Stale outcome-state leakage across a selector change
**One line.** Switching outcome leaves the previous endpoint's counts, denominators or effect measure
in place.

**Root cause.** Three composing bugs, all in the shared engine.
1. **`??` fallbacks.** `t.data.tE = oc.tE ?? t.data.tE` — a selected row with `tE:null` fell through
   to the previously bound endpoint's count. Denominators were worse: `null != oc.nT && (t.data.tN =
   oc.nT)` left `tN`/`cN` at the composite's values entirely, which is how `336/569` came to be
   printed as a percentage. `[IRON]` §1 Defect 2.
2. **`pooling-repair`.** An inline post-load block copies `realData[id]`'s **TOP-LEVEL** `tE`/`cE`
   into `t.data` whenever the *scoped* row has no counts, and force-sets `effectMeasure = "HR"`.
   The top-level counts are the trial's **PRIMARY** endpoint — the per-endpoint values live in
   `allOutcomes[]` — so on a **secondary** scope the block writes the primary endpoint's counts
   under the secondary endpoint's label. A direct scope-lock bypass. `[IRON]` §1 Defect 3.
   **Present corpus-wide** — 944 apps measured; confirmed by grep in `ABATACEPT_PSA`,
   `ABATACEPT_RA`, `ABEMACICLIB_BREAST`, … (`[IRON]` §6).

   > **CORRECTION (re-gate, 2026-07-30).** An earlier draft of this entry said the block "adds
   > off-scope trials" to the pool. **That is wrong and is withdrawn.** `inclTrials` only fills
   > COUNTS on rows already marked `s === "include"`; it does not add or remove trials, and `k`
   > is unchanged. The defect is **counts-on-the-wrong-scope plus a forced HR label**, nothing
   > more. The correct statement is above.
   >
   > **It is also NOT safe to neutralise corpus-wide, and the attempt was withdrawn from
   > Phase 1.** A 2×2 isolation showed that disabling the block ALONE sets `state.results = NULL`
   > at load on ~944 apps (reproduced on `ACS_ANTIPLATELET` k=4, `ABATACEPT_RA` k=2,
   > `ABEMACICLIB` k=2): its `rerun()` is the **only unconditional load-time trigger** for
   > `AnalysisEngine.run()` — every other call site is gated on `activeTab === 'analysis'` or an
   > event handler. Disabling it therefore blanks the pooled estimate until the user opens the
   > Analysis tab. It does not produce a *wrong* number (the Analysis tab restores identical
   > values), but **a structural patch must never change a correct rendered result.**
   >
   > The fix is therefore **per-app and PHASE 2**: bind the scoped row to its own
   > `allOutcomes[]` entry, and give the app a load-time analysis trigger that does not depend
   > on this block. See `RAPIDMETA_BATCH_PLAN.md` §2.7.
3. **`paper-studio.js`.** `PS.ensureAnalysisReady()` tests `state.selectedOutcome` against each row's
   `shortLabel` and, on a miss, assigns `trials[0].allOutcomes[0].shortLabel`. Because state holds a
   scope **key** while rows carry shortLabels, the test always misses — so merely **opening the Paper
   tab flips the analysis scope**. `[IRON]` §1 Defect 4. **Ships to every app** in
   `assets/js/paper-studio.js` (211 KB, shared).

**Detector (STATIC).**
```
rg -c 'COMPLETE-POOLING-REPAIR' *_REVIEW.html
rg -c 'ensureAnalysisReady' assets/js/paper-studio.js *_REVIEW.html
python scripts/rapidmeta_error_sweep.py --only RM-B02
```
Fails on the presence of `pooling-repair`, on `?? t.data.t[EN]` fallback patterns, or on an
un-overridden `ensureAnalysisReady`.

**Detector (RENDER).** Walk **all** tabs; after each, re-read `state.selectedOutcome` and assert it
is unchanged. This is how Defect 4 was found — a file-level gate cannot see it.

**Fix.** Guard **G07**: `applyOutcomeScope` clears **every** scoped field before rebinding; no `??`
fallback survives a scope change; `pooling-repair` disabled with the reason recorded inline;
`ensureAnalysisReady` neutralised by an app-local no-op override (do not edit the shared file
piecemeal — it needs its own corpus sweep). `[IRON]` §1–§2.

**Observed in.** `IV_IRON_HF_REVIEW.html`; `pooling-repair` corpus-wide.

**Base engine: YES.**

---

### RM-B03 · Silent endpoint fallback
**One line.** When the selected scope's outcome is missing for a trial, the engine substitutes
another endpoint instead of blocking.

**Root cause.** The `outcomes[0]` heuristic, reimplemented in at least three places (selector, pool,
paper module). `[BUG-CAT]` guard 3; `[IRON]` §1.

**Detector (STATIC).** As RM-B01/RM-B02 — any `outcomes[0]` / `allOutcomes[0]` assignment reachable
from a scope resolution path.

**Fix.** Guard **G03**, fail-closed: **BLOCK** and render *"not available for this outcome"*. Never
substitute. `[BUG-CAT]` guard 3.

**Base engine: YES.**

---

### RM-B04 · Outcome substitution (wrong outcome row extracted)
**One line.** The extracted numerator is a real number from the source — from the wrong outcome.

**Root cause.** Outcome matching by fuzzy score with no minimum, so an administrative or secondary
category wins over the primary.

**Detector (SOURCE).** For each fitted count, name the registry outcome it came from and confirm the
outcome is the one the row's title claims. `[RECIPE-GH]` §2.8 lists the disease-specific traps
(any-severity vs severe disease; sputum-culture conversion vs relapse-free cure; wk48 vs wk96;
incidence per person-year vs cumulative incidence).

**Fix.** Require an explicit outcome key per extracted value; refuse a match below a stated score;
carry the quoted source field in the ledger.

**Observed in.** `RIFAPENTINE_TB_AUTO_FULL_REVIEW.html` — iAdhere `tE=2, cE=5` are the class
*"Not advisable to continue study drugs"*, one of **eight** reasons-for-failure-to-complete
categories and a clinician-judgement administrative reason. The trial's actual primary — treatment
completion 294/337 vs 248/335 — is nowhere in the app. `[RIFA]` §2.2.
Also `NCT00814671`: `tE=46` and `cE=45` are the **denominators** of a secondary median-days outcome,
paired with participant-flow counts from **two different arms** as denominators. `[RIFA]` §2.1.

**Base engine:** no — extraction-time, but the fuzzy matcher is shared.

---

### RM-B05 · Omitted eligible trial (selection bias)
**One line.** An eligible trial is absent from the review with no recorded decision.

**Root cause.** Silent omission. `[ARNI]` ea1a8fea1 states the rule: *"silently omitting an eligible
trial is a selection bias"*.

**Detector (SOURCE).** Run the review's own stated eligibility criteria against a registry/PubMed
search; every eligible trial must appear either in the pool or in an **excluded-with-reason** list.

**Fix.** An explicit include/exclude decision per eligible trial, rendered.

**Observed in.** `ARNI_HF_REVIEW.html` — **PIONEER-HF** (NCT02554890, n=881) and **LIFE**
(NCT02816736, n=335) were absent from every earlier revision; both now included as their own
comparisons. `RIFAPENTINE_TB_AUTO_FULL_REVIEW.html` — **PREVENT TB / TBTC Study 26** (NCT00023452,
7/3986 vs 15/3745), the trial that underpins the WHO recommendation for the regimen the app reviews,
does not appear anywhere in it; `[RIFA]` §2.4 also names PMIDs 25904367, 30029896, 38996972 as absent.

> **Discipline note.** `[RIFA]` §2.4 explicitly labels its list *"a starting set for a rebuild, not a
> completed systematic search"* — BRIEF-TB/A5279, WHIP3TB, V-QUIN and ASTERoiD were not verified.
> The detector's output is a candidate list, not a proof of completeness.

---

### RM-B06 · PICO / population mismatch row
**One line.** A row is perfectly extracted and does not belong — different comparator, different
population, different design.

**Root cause.** No per-row comparator/population field, so nothing can be tested against the app's own
question. Invisible to a donor-string contamination scan. `[APIXABAN]` §2.4, `[RECIPE-C]` §2.8.

**Detector (SOURCE).** Per row, resolve the registry's population, comparator, masking and phase and
compare to the review's PICO. `[RECIPE-C]` gate G6.

**Fix.** Add an `indirect`/`comparator`/`population` marker to every row and refuse to pool across
comparator classes without an explicit stratum. Guard **G09**. `[APIXABAN]` §7.

**Observed in.**
- `APIXABAN_ACS` — **AUGUSTUS** is apixaban vs **vitamin K antagonist** in **atrial fibrillation**,
  open-label, phase 4, 2×2 factorial, pooled into an app asking about apixaban vs placebo in ACS.
- `RIFAPENTINE_TB` — **NCT00814671** is an **active** smear-positive pulmonary TB *treatment* trial
  sitting in a **latent**-TB prevention review. Not reinstatable at any count. `[RIFA]` §2.1.
- `ICAGEN_AUTO_FULL_REVIEW.html` — titled *"Edoxaban TIMI 48 cancer-VTE"*; its three rows are a
  **paediatric** VTE trial and two **orthopaedic-surgery prophylaxis** trials. Not one is a cancer-VTE
  trial and not one is ENGAGE AF-TIMI 48. `[CARDIO-MIS]` §2.
- `ARNI_HF_REVIEW.html` — **PARADISE-MI** exclusion criterion 1 is *"Known history of chronic HF prior
  to randomization"*, so it cannot be pooled with chronic-HFrEF PARADIGM-HF. `[ARNI]` 554b6f2a2.
- `[HFREF]` — PARACHUTE-HF is Chagas cardiomyopathy and the only open-label trial in the network;
  He 2015 is idiopathic DCM only. Both **retained and disclosed** — disclosure is a valid disposition.

---

### RM-B07 · Undisclosed arm dropping / multi-arm collapse
**One line.** Arms are dropped or merged without a statement, often the arm carrying the trial's own
experimental variable.

**Detector (SOURCE).** Compare the ledger's summed N against the registry `enrollmentInfo` and the
`armGroups` count. A gap >5% with no disclosure is the finding. Arm-balance ratios **cannot** detect
this — `[RIFA]` §3 records ratios of 1.125:1 and 1.000:1 masking a 3-arm → 2-arm collapse.

**Fix.** Disclose every dropped/merged arm and test equivalence **on the outcome actually pooled**,
not on the trial's own primary. `[RECIPE-C]` §2.10 — He 2015's benazepril doses differ at P=0.042 on
the *composite* but are 11/97 vs 8/101, Fisher p=0.49, on **all-cause death**, so pooling is
defensible for that outcome and saying so requires the distinction.

**Observed in.** `APIXABAN_ACS` — APPRAISE-1 drops 3 of 4 apixaban arms (787 patients, 53% of
enrolment), APPRAISE-J drops its 5 mg arm (67%), AUGUSTUS drops half the factorial (50%).
`RIFAPENTINE_TB` — NCT00814671 randomised **three** arms and the app fits two, silently dropping
**RPT600, the best-performing arm (96%)**, when rifapentine dose is the trial's own experimental
variable; iAdhere's SAT+SMS arm silently dropped. `[RIFA]` §2.1–2.2.

---

## 4. FAMILY C — POPULATION AND DENOMINATOR

### RM-C01 · Randomised vs analysed denominator unlabelled
**One line.** The randomised n and the analysed n are used interchangeably, hiding attrition.

**Detector (STATIC + SOURCE).** Assert every denominator is labelled `randomised` or `analysed`, and
that both are shown where they differ.
```
python scripts/rapidmeta_error_sweep.py --only RM-C01
```
Static form fails when a header N and a forest N differ with no reconciling label.

**Fix.** Two labelled fields per arm; show both with the reason for the gap. `[ARNI]` b0dbdd1ed.

**Observed in.**
- `ARNI_HF_REVIEW.html` — PARAGLIDE-HF recorded `analysed: 466` while the registry's primary
  NT-proBNP analysis used **180 + 197 = 377**, hiding **19% attrition** (material correction);
  LIFE registry posts 155 + 158 against the paper's 167 + 168; header N 19,322 vs forest N 18,856.
- `VIVAX_RADICAL_CURE_NMA_REVIEW.html` — N=2153 randomised vs **2071 evaluable**; the 82 patients
  (3.81%) conditioned away are now broken down by trial. `[VIVAX]` 1daa80c2e F4.
- `IV_IRON_HF_REVIEW.html` — CONFIRM-HF mortality denominators are the FAS (150/151), **not** the
  152/152 randomised. `[IRON]` §3.
- `SOTAGLIFLOZIN_*` — population framing corrected across `9bd584001`, `c682aa9b4`.

---

### RM-C02 · Arm value presented as the overall value
**One line.** A single arm's mean/median/percentage is displayed as the trial's overall value; or two
arms' medians are averaged into a "pooled median" no source reports.

**Root cause.** The extractor takes the first baseline row rather than the registry's `Total` row.
`[SGLT2]` — *"the recurring defect was an arm value presented as the overall value"*.

**Detector (SOURCE).** Compare every baseline value against the registry results baseline module's
`Total` row.

**Fix.** Prefer the registry `Total`. Never average medians. `[SGLT2]`.

**Observed in.** `SGLT2_HF_REVIEW.html`: SOLOIST age 68.6 (sotagliflozin arm) shown as the trial mean
(true 68.9); DAPA-HF age 66.2 (dapagliflozin arm) → 66.3; male 76.2% (arm) → 76.6%;
EMPEROR-Reduced age 67.2/66.5 both arm values → 66.8; EMPEROR-Preserved NT-proBNP 994 (empagliflozin
arm) → pooled 974; DELIVER NT-proBNP 1,126 → 1,011.

> **A correction that was itself withdrawn, recorded because withdrawal is the discipline** (`[SGLT2]`
> DAPA-HF row): the audit flagged DAPA-HF's median NT-proBNP 1,437 as a fabricated average of the arm
> medians. **RETRACTED — 1,437 STANDS**; the benchmark meta-analysis independently reports 1,437 as
> the pooled median, and the coincidence with the mean of 1,428/1,446 is a coincidence. The general
> rule that medians cannot be averaged is unaffected.

---

### RM-C03 · Arm orientation inversion
**One line.** Arms are bound by registry group **index**, and ClinicalTrials.gov frequently lists
placebo first — so treatment and control are swapped.

**Root cause.** `OG000 = Placebo` in many records; the extractor maps index 0 → treatment.
`[APIXABAN]` §2.2, gate **G6c**.

**Detector (SOURCE).** For each ledger slot, ask **which registry group title** it reproduces. Gate
G6c mechanises the bind-by-title rule.

**Fix.** Bind by group **TITLE**, never by index. Guard **G15**. `[RECIPE-C]` rule 3.

**Observed in.** `APIXABAN_ACS` — three of four trials inverted. APPRAISE-2 `tN = 3687` is the
**placebo** denominator; APPRAISE-1 `tN = 611` is the publication's **placebo** n; APPRAISE-J
`tN = 52` is the **placebo** n. **The consequence is not cosmetic:** the app read apixaban bleeding as
18/611 = 2.9% against placebo 18/317 = 5.7%, while the trial found apixaban *increased*
major/CRNM bleeding dose-dependently and its two highest-dose arms were stopped for excess bleeding.
The app inverted the trial's central safety finding. `[APIXABAN]` §2.2.

**Base engine: YES** — the extractor is shared.

---

## 5. FAMILY D — PROVENANCE

### RM-D01 · Wrong NCT / registry-concordance failure
**One line.** The displayed NCT is not the trial the row describes, so the app renders foreign
eligibility criteria, phase, enrolment and arms.

**Detector (STATIC + SOURCE).** Static: NCT well-formedness and cross-app collision
(`scripts/cross_app_nct_name_check.py`, `scripts/resolve_nct_collisions.py` already exist). Source:
resolve every NCT against API v2 and compare `briefTitle`, `phases`, `enrollmentInfo`,
`designInfo.maskingInfo`, `armGroups`, `overallStatus` against the row. Gate **G6**.

**Fix.** Guard **G09**: block rendering of an NCT-linked row whose registry title does not match the
trial name, and whose registry condition does not match the review topic.

**Observed in.** `ATTR_CM_REVIEW.html` — **the cleanest instance in the registry** (`[ATTR]`
9e658033f): the app carried **NCT05534659** for HELIOS-B, which is a Chang Gung Memorial Hospital
**observational study of programmable vs non-programmable cerebrospinal-fluid ventricular shunts in
adult hydrocephalus** — and that record was the source of the **foreign eligibility criteria
displayed on the trial card**. Re-bound to NCT04153149. This is the failure mode in its pure form:
a wrong identifier does not merely mislabel a row, it imports another trial's text into the app.
`ICAGEN_AUTO_FULL_REVIEW.html` — all three NCTs resolve to trials matching
neither the title nor each other (`[CARDIO-MIS]` §2). `RIFAPENTINE_TB` — NCT00814671 resolves to an
active-TB treatment trial (`[RIFA]` §2.1). `[RECIPE-C]` §3.1: registry concordance is **N/A, not
passed**, for unregistered trials — state the covered fraction.

**Checked and found NOT to be a defect, recorded so it is not "found" again** (`[CARDIO-MIS]` §1):
`NCT02220725` and `NCT02207725` both display "Siegal 2015" and look like a digit transposition. They
are ANNEXA-A and ANNEXA-R, two genuinely distinct trials reported in one publication. **Correct as it
stands.**

---

### RM-D02 · Wrong or cross-topic citation
**One line.** The cited PMID/DOI points at a different trial, sometimes in a different field entirely.

**Detector (STATIC + SOURCE).** Static: PMID/DOI well-formedness; duplicate PMIDs across unrelated
trials. Source: resolve the PMID and compare title/population/intervention to the row.

**Fix.** Resolve every identifier by lookup; repoint the `sourceUrl`s too, not just the PMID field.

**Observed in.** `ARNI_HF_REVIEW.html` — PARAGLIDE-HF cited *"JAMA 2023; 329(12):990-1002"* =
**PMID 36826844**, *"Effect of Verapamil on Pancreatic Beta Cell Function in Newly Diagnosed
Pediatric Type 1 Diabetes"*, an unrelated trial in a different disease area; corrected to
J Am Coll Cardiol 2023;82(1):1-12, DOI 10.1016/j.jacc.2023.04.019 (PMID 37212758, which the app
already stored). Two `jamanetwork` sourceUrls repointed. `[ARNI]` d906ba931.
Corpus history: `scripts/fix_pmid_miscitations{,_round2,_round3,_round4}.py`, `fix_wrong_pmids.py`,
`fix_known_wrong_pmids.py` — this class has four prior remediation rounds.

---

### RM-D03 · Protocol / design paper cited for outcome data
**One line.** The cited paper is a protocol, design, sub-study or pooled analysis and cannot
substantiate the extracted per-arm counts.

**Detector (SOURCE).** PubMed `article_types` — reject `Clinical Trial Protocol` as a source for
outcome counts. `[RECIPE-C]` §2.1.

**Fix.** Locate the results paper via the registry's own `referencesModule`, then confirm in PubMed.

**Observed in.** `APIXABAN_ACS` — AUGUSTUS cited **PMID 29898844**, *"…Rationale and design of the
AUGUSTUS trial"*, *Am Heart J* 2018;200:17-23, typed by PubMed as **"Clinical Trial Protocol"**;
results paper is **PMID 30883055**, *N Engl J Med* 2019;380(16):1509-1524. `[APIXABAN]` §2.4.
`[HFREF]` F1 — RESOLVD cited a paper with no metoprolol arm.

---

### RM-D04 · Fabricated counts (reconcile with nothing)
**One line.** Per-arm counts that appear in no document and match no arm of the posted results.

**Root cause.** Several — RM-A06, RM-B04, RM-C03 all produce it. What unites them is that the
resulting numbers are **internally plausible**: valid non-negative integers with `e ≤ N`, from which
the log-odds-ratio and variance recompute **exactly**. `[RIFA]` §Headline: *"The pipeline is faithful;
its input is not."*

**Detector (SOURCE).** Gate **G6d** — posted-results reconcilability: a count matching no arm of the
posted results has no located source. Arithmetic gates (G1, G1b) are **structurally blind** to this;
`[RIFA]` measured `Δ = 0.00e+00` on a fabricated 2×2 and `[APIXABAN]` G1 returned 0 findings on eight
corrupted rows.

**Fix.** **Quarantine, never silent deletion** — retain the row flagged, with a stated reinstatement
condition, and make the verifier **block** if a quarantined row is deleted rather than flagged.
`[RECIPE-GH]` §0.1. Never invent a number to resolve a discrepancy.

**Observed in.** `RIFAPENTINE_TB` — **both** fitted trials; all four cells of NCT00814671 wrong;
pooled OR 0.389 (0.134–1.124) withdrawn; verdict `STABLE` → `FABRICATED`; badge green →
`#991b1b` "FABRICATED EXTRACTION — DO NOT CITE"; **counts changed: 0**, because no sourced value
exists to correct them to. `APIXABAN_ACS` — APPRAISE-J's `17/19` against a source stating 2, 2 and 1.
`IV_IRON_HF_REVIEW.html` — CONFIRM-HF `25/150 vs 36/151, HR 0.69` appears nowhere in the primary
publication; HEART-FID `560/1532, 581/1533` matches no statement in NEJM or the registry; AFFIRM-AHF
all-cause mortality `65 vs 74, HR 0.93` was unsourced **and wrong in direction** (true 98/558 vs
96/550, HR 0.99, p=0.944 — null, not favourable).

---

### RM-D05 · Fabricated / imported analysis row
**One line.** A GRADE row, benchmark or endpoint estimate is displayed with no reproducible analysis
behind it.

**Detector (STATIC).** Every displayed estimate must be reachable from a stored input by a named
computation, or be labelled an **external published result**. Flag estimates with no
`source`/`derivation` field.
```
python scripts/rapidmeta_error_sweep.py --only RM-D05
```

**Fix.** Either recompute and show the derivation, or label it external and cite it. `[ARNI]`
b0dbdd1ed does the latter correctly for the investigators' own pre-specified participant-level pooled
analysis of PARAGON-HF + PARAGLIDE-HF (*Eur Heart J* 2023;44(31):2982, open access), reported as an
external result, **not recomputed here**, with an explicit caveat that it does not rehabilitate the
withdrawn 4-trial pool.

**Observed in.** `ARNI_HF_REVIEW.html` — PARAGLIDE's primary was stored as `md:-223, se:85`, an
absolute pg/mL mean difference that **appears nowhere in the publication**; PARAGON's all-cause
mortality CI `0.81–1.16` matched no posted result (corrected to 0.84–1.13).
`VIVAX_RADICAL_CURE_NMA` F6 — non-estimable multiverse cells shipped `OR/lo/hi` in the JSON while the
HTML rendered NOT ESTIMABLE, so a JSON consumer could quote a number the app deliberately refused to
estimate. `[VIVAX]` 1daa80c2e.

---

### RM-D06 · App identity mismatch
**One line.** The filename, the published URL and the storage key describe a different drug or
indication from the content.

**Detector (STATIC).**
```
rg -o '<title>[^<]{0,110}' *_REVIEW.html      # compare to the filename stem
python scripts/rapidmeta_error_sweep.py --only RM-D06
```
Fails when no token of the filename stem appears in the `<title>` or the ledger `group` string.

**Fix.** Rename **only together with** the substantive fixes — *"renaming either app without
addressing the findings below would make it look corrected while leaving it wrong"* (`[CARDIO-MIS]`).
Renaming changes the published Pages URL and orphans the claims-board review id.

**Observed in.** `TIRZEPATIDE_ARDS_AUTO_FULL_REVIEW.html` → contains **andexanet alfa** (ANNEXA-A/R/4);
`ICAGEN_AUTO_FULL_REVIEW.html` → contains **edoxaban** ("Icagen" is a company name, not a drug).
`[RECIPE-C]` §0.3 records **four** cardio-adjacent apps with this property.

> **False-positive warning, recorded** (`[CARDIO-MIS]`): grepping `ARDS` case-insensitively returns 83
> hits in that file and 18 in ICAGEN, but `ards` is a substring of `cards` (`stat cards`,
> `renderDataCards`). Do not read the raw count as contaminated claim text.

---

## 6. FAMILY E — CONTAMINATION

### RM-E01 · Cross-topic template contamination
**One line.** Donor-app drug-class, trial-name or endpoint strings survive in a clone.

**Detector (STATIC).** `python scripts/clone_contamination_gate.py <FILE>` (exists, `--selftest`
proves it can fail) plus the blocklist sweep:
```
rg -i 'SGLT2|dapagliflozin|empagliflozin|Fournier|genital mycotic|diabetic ketoacidosis|DAPA-HF|EMPEROR-|DELIVER|EMPA-REG|finerenone|FIDELIO|FIGARO|MRA\b|eGFR slope' <FILE>
```
excluding the legitimate `rapidmeta-finerenone` repo/asset URL. A hit in a **claim-bearing slot**
(safety-outcome definition, i18n value, data seal, export title) is **P0**. `[RECIPE-GH]` §8.

**Fix.** Guard **G14** blocklist + the existing decontamination scripts.

**Observed in.** `MAVACAMTEN_HCM_REVIEW.html` shows how deep it reaches (`[MAVA]` ecd1aba43): the
donor's *"non-steroidal mineralocorticoid receptor antagonist"* described a **cardiac myosin
inhibitor**; the **Arabic UI translated the word "mavacamten" to "finerenone"** (21 other
contaminated pairs removed alongside it); and CKD/MACE/eGFR carryover survived in **both verdict
generators**, the outcome and endpoint vocabulary maps, the auto-extractor's endpoint bridges,
keyword catalogues, the short-label deriver, the scoring heuristics, the **screening relevance
scorer** (which awarded points to CKD/HFpEF papers) and the arm-matching regexes. A blocklist over
prose alone would have missed most of these slots.
Corpus history: 148 clones + 7 main-only apps fixed at `619512b4d` / `ad1f6968d` / `d11d9f167`
(SGLT2i adverse-event profile); 154 clones at `a233968b0` (PICO rows, SOLOIST button, protocol badge,
baked benchmarks); registry search queries repointed at `21efe48aa`.

**Base engine: YES.**

---

### RM-E02 · Foreign trial-alias registry
**One line.** A `KNOWN_TRIAL_ALIASES` table of sacubitril/valsartan heart-failure trials is baked into
apps on unrelated topics.

**Root cause.** A **different slot** from RM-E01 — trial-alias resolution — which the drug-class
blocklist does not cover. `[RIFA]` §4.

**Detector (STATIC).**
```
rg -c 'NCT01035255|NCT01920711|NCT02924727|NCT03988634' *_REVIEW.html   # paradigm/paragon/paradise/paraglide
python scripts/rapidmeta_error_sweep.py --only RM-E02
```
Fails when those NCTs appear in an app whose `<title>` does not name sacubitril/valsartan/ARNI/heart
failure. Note the table is **legitimate** in the ARNI app — the detector is topic-conditional.

**Fix.** Derive `KNOWN_TRIAL_ALIASES` from the app's own `realData` at build time; never bake a
donor's table. Guard **G14**.

**Observed in.** `[RIFA]` §4 recorded **526 apps**, 56 of them in the global-health scope set.
**Measured by this sweep: 716 of 1,088 apps (65.8%)** — use the measured figure.
`RIFAPENTINE_TB_AUTO_FULL_REVIEW.html` is the worked instance: four
sacubitril/valsartan heart-failure trials baked into a tuberculosis app, `clone_contamination_gate.py`
→ **exit 1, BLOCKING**, finding `foreign_trial_registry_rendered`. Reported, **not fixed** — the
526-app remediation is a separate gated batch. The sweep re-measures the 526 rather than quoting it.

**Base engine: YES.**

---

## 7. FAMILY F — VERDICT AND DISPLAY

### RM-F01 · False-green verdict badge
**One line.** A green `INTERNAL CHECKS PASSED` banner sits above an app whose own machine verdict
records open findings, empty data, or `UNCERTAIN`.

**Root cause.** The badge is inherited boilerplate that is not recomputed from the verdict object.
`p0_total: 0` means *"no P0s"*, not *"passed"*. `[BUG-CAT]` #4, `[HARNESS]` F-05.

**Detector (STATIC).**
```
python scripts/rapidmeta_error_sweep.py --only RM-F01
```
Fails when the badge background is `#15803d` / `#0a7d33` (or the text `CHECKS PASSED` / `VERIFIED`
appears) **and** any of: `window.__verdict.verdict != "STABLE"`; any non-zero `P1_*` or `P2_*`
counter; a non-empty `reasons[]`; `n_trials_seen == 0`; or `realData` empty.
Grep form — **both** surfaces, never one:
```
rg -o '__verdict[^;]{0,400}' <FILE>
rg -o 'id="rapidmeta-integrity-badge"[\s\S]{0,1600}' <FILE>
```

**Fix.** Guard **G12**: the badge is rendered **from** the verdict object, not beside it; replace the
badge's **entire inner content** by balanced-`<div>` matching — partial replacement is what shipped
the HFrEF 28-vs-27 contradiction. Running the gates does not earn a PASS; it converts "untested" into
"tested, with N findings". `[RECIPE-C]` §6, `[RECIPE-GH]` §5.

**Observed in.** `[BUG-CAT]`: **~70% of cardio apps**. Worked instances:
- `[HARNESS]` F-05 — HFrEF AUTO live on `main` 2026-07-29: `__verdict` honest (`UNCERTAIN`, 28
  trials) while a green badge asserted `INTERNAL CHECKS PASSED · Trials: 2`. **The gate read only
  `__verdict` and passed the app.** Caught by a cross-family (agy/Gemini) pass; missed by the gate and
  by every same-family Claude review. Fixed `b02990a02`, `9a2cdff58`.
- `APIXABAN_ACS` — green badge while `__verdict` carried `P1_aact_concord: 2`,
  `P2_evidence_incomplete: 2`, `P2_aact_advisory: 2` and the reason **`"2 AACT outcome-direction
  divergence(s)"`** — *"the machinery detected it, and the badge rendered green over it."*
- `RIFAPENTINE_TB` — green badge, fabrication-risk 0.275, over two fabricated 2×2s.
- Two cardio apps holding **ZERO trials** with a green `CHECKS PASSED · Trials: 2` badge, fixed at
  `276d749a3` (EZETIMIBE_LIPID, LISINOPRIL_HTN).
- `ARNI_HF_REVIEW.html` — green `#0a7d33` "EVIDENCE GRADE: VERIFIED / externally validated … passes
  all gates" while `__verdict` said `UNCERTAIN` with **every counter at 0 and `n_trials_seen = 0`**,
  i.e. the gates had never run. *"Every clause of the green banner was false."* `[ARNI]` 6985c85cd.
- `IV_IRON_HF_REVIEW.html` — green "✓ VERIFIED · k = 4 · externally validated … every displayed
  number was checked against its source" over `__verdict` with all counts 0.

**Base engine: YES.**

---

### RM-F02 · Verdict-surface disagreement
**One line.** The machine verdict, the visible badge and the ledger state different trial counts or
different verdicts.

**Detector (STATIC).** Extract all three and assert equality of `verdict`, trial count and finding
count.
```
python scripts/rapidmeta_error_sweep.py --only RM-F02
```
Fails on any disagreement. **Enumerate the surfaces first** — a gate that reads one certifies the
other by omission (`[HARNESS]` F-05).

**Fix.** Guard **G12**, both surfaces or neither; ⛔ no new verdict surface without a same-commit gate
update; mutation test required.

**Observed in.** `APIXABAN_ACS` — badge `Trials: 2`, `__verdict.n_trials_seen: 2`, `realData` carries
**4**; nothing on the page says which two were audited. Both variants disagree about whether an audit
exists at all: `APIXABAN_ACS_AUTO_REVIEW.html` has **no badge and no `__verdict`**.
`TIRZEPATIDE_ARDS` and `ICAGEN` — `"STABLE", n_trials_seen: 2` over a **3-row** ledger.
`ARNI_HF_REVIEW.html` — `n_trials_seen: 0` under a badge claiming k = 4.

**Base engine: YES.**

---

### RM-F03 · Badge self-contradiction
**One line.** One badge states two different numbers for the same quantity.

**Root cause.** Regex-and-append patching of a surface that states numbers, instead of wholesale
replacement. `[RECIPE-C]` §1.3.

**Detector (STATIC).** Within the badge's balanced-`<div>` span, extract every `Trials: N`,
`k = N` and `N internal-consistency rounds` and assert they are unique and equal to the
post-disposition value.
```
python scripts/rapidmeta_error_sweep.py --only RM-F03
```

**Fix.** Replace the badge **wholesale** by balanced-`<div>` matching; add the self-contradiction
check to the verifier and **confirm it fires on the bug it was written for**. `[RECIPE-C]` §6.5.

**Observed in.** HFrEF — `"Trials: 28"` left beside the new `"27 trials"` by a partial replacement.
`APIXABAN_ACS` and `RIFAPENTINE_TB` — *"AACT 2026-04-12 + PubMed + **10** internal-consistency
rounds"* in one sentence and *"**14** internal-consistency rounds"* in the next, **both shipped**.
`ARNI_HF_REVIEW.html` — same 10-vs-14 pair, and **neither number appears** in the
`FINAL_INTEGRITY_REPORT_V2.md` the badge cites; replaced with an explicit *"not reliably recorded"*.
`[ARNI]` 554b6f2a2.

> This 10-vs-14 pair is present in the *unmodified* boilerplate on `main` — verified in
> `SGLT2_HF_REVIEW.html` at HEAD. It is a **base-engine string**, not a per-app slip.

**Base engine: YES.**

---

### RM-F04 · Interface state desync
**One line.** Version numbers, audit-round counts, scope strings and trial counts contradict each
other across the interface.

**Detector (STATIC).** Collect every version token, scope string and trial count; assert internal
consistency.
```
python scripts/rapidmeta_error_sweep.py --only RM-F04
```

**Fix.** Single source for each; render, never hardcode. `[ARNI]` 554b6f2a2 (version drift title
v12.5 / app v12.0 / R v11.0 → single v12.5 across **13 sites**).

**Observed in.** `ARNI_HF_REVIEW.html` — version drift (13 sites); the *"Living Systematic Review"*
title contradicting the app's own `LIVING:NEVER` badge (**the badge was right; the title changed**);
scope badge reading *"in HFrEF · CV death + HHF · PARADIGM-HF"* for a four-trial, four-population app;
meta description, JSON-LD description, outcome selector, PICO outcome field and `state.protocol.out`
all saying *"CV Death or HF Hospitalization"* — **true for none of the four trials**; methods text
claiming node-splitting / comparison-adjusted funnel / CINeMA-lite / POTH / contribution matrix,
machinery that never applied.

**Base engine: YES.**

---

### RM-F05 · Missing rendered as zero
**One line.** A missing value displays as `0` or `0.0%` instead of NA.

**Root cause.** Presence guards that test the denominator only, or that accept `null` numerically.
`[ARNI]` ea1a8fea1 records **both** the bug and a wrong first fix:
```js
d.tN > 0                                  // checks the DENOMINATOR; a null numerator coerces to 0
Number.isFinite(Number(x))                // ALSO WRONG: Number(null) === 0, isFinite(0) === true
```

**Detector (STATIC).**
```
rg -c 'Number\.isFinite\(Number\(' *_REVIEW.html
rg -o '0\.0%\s*(vs|·|/)' *_REVIEW.html
python scripts/rapidmeta_error_sweep.py --only RM-F05
```
Fails on the `Number.isFinite(Number(x))` presence-check idiom, or on a rendered `0.0%` for a trial
whose count field is null.

**Fix.** A real presence check that rejects `null`/`undefined`/`""` **first** (`window._rmHasCount`),
applied at **every** count-presence site — `[ARNI]` found **6**, including the outcome-selection label
that would otherwise have printed *"counts 0/2407 vs 0/2389"*. Guard **G05**, fail-closed to NA.

**Observed in.** `ARNI_HF_REVIEW.html` (PARAGON-HF and PARAGLIDE-HF "0.0% event rate"; and the Total
row dividing 2-trial numerators by 4-trial denominators, 13.0/15.4 → corrected 17.8% vs 21.2%).
Corpus history: `scripts/fix_python_none_in_js.py`, `scripts/fix_prisma_svg_zeros.py`,
`scripts/fix_evdata_null_map.py`, `tests/test_no_impossible_counts.py`.

**Base engine: YES.**

---

### RM-F06 · Impossible PRISMA zeros
**One line.** An unpopulated search/screening pipeline renders "0 identified", which asserts that a
search ran and returned nothing.

**Root cause.** Missing → 0 (RM-F05) applied to the SR stages. **A 0 is a different and false claim
from "not recorded"** — `[ARNI]` ea1a8fea1.

**Detector (STATIC).**
```
python scripts/rapidmeta_error_sweep.py --only RM-F06
```
Fails when the PRISMA identified/screened/eligible counts are 0 while `realData` holds ≥1 trial, or
when any downstream stage exceeds an upstream one.

**Fix.** Render **"not recorded"**; mark RoB 2 / GRADE / AMSTAR 2 **NOT COMPLETED** rather than
defaulted, and name the AMSTAR-2 critical domains known to fail (no registration, no documented
search, no excluded-studies list). Guard **G05**. `[ARNI]` ea1a8fea1; `[BUG-CAT]` #7.

**Observed in.** `ARNI_HF_REVIEW.html`; PRISMA coherence fixed on HFrEF at `4342b2259`
(*"PRISMA flow is coherent on all three surfaces; gaps shown, not smoothed"*).

**Base engine: YES.**

---

### RM-F07 · Unearned confidence on unsourced fields
**One line.** Fields whose source is `"--"` or absent are marked "100% confidence", "VERIFIED", or
`fabrication-risk 0.000`.

**Detector (STATIC).**
```
rg -o 'fabrication[- ]risk[^<]{0,40}0\.000' *_REVIEW.html
rg -o '100%\s*(confidence|verified)' *_REVIEW.html
python scripts/rapidmeta_error_sweep.py --only RM-F07
```
Fails when a confidence/verification claim co-occurs with a `"--"`, empty or absent source field, or
when `fabrication-risk 0.000` co-occurs with any unverified row.

**Fix.** Guard **G11**: a verification claim requires a non-empty source field on the same record;
otherwise render the evidence tier (`VERIFIED_FULL` / `VERIFIED_DENOM_ONLY` /
`SECONDARY_CORROBORATED` / `UNSOURCED`). `VERIFIED_DENOM_ONLY` is an honest limit, not a failure —
8 of 28 rows in HFrEF. `[RECIPE-C]` §2.7.

**Observed in.** `SGLT2_HF_REVIEW.html` at HEAD — `Fabrication-risk score: 0.000 · Trials: 5` over
`P2_evidence_incomplete: 5` ("5 trial(s) missing evidence rows") in its own `__verdict`.
`SOTAGLIFLOZIN_*` — *"no `--` sources"* fix at `d5ec48c16`. `[BUG-CAT]` #7.

**Base engine: YES.**

---

### RM-F08 · Selective reporting of the favourable interval
**One line.** The headline quotes the narrower interval and the prespecified sensitivity interval
crossing 1 is not shown.

**Detector (STATIC).** If an HKSJ, Paule-Mandel or prediction interval is computed, assert it is
rendered on the same surface as the headline whenever it crosses the null and the headline does not.
```
python scripts/rapidmeta_error_sweep.py --only RM-F08
```

**Fix.** Guard **G16**: co-render. `[ACS-GATE]` acc656de0 R3 does this — the badge's PRELIMINARY block
carries k=2, 41 events/1,065 participants, **fragility index 1**, and the **HKSJ interval crossing 1**
directly under the headline. `[VIVAX]` F3 does the edge-specific version: a Paule-Mandel sensitivity
`OR 1.067 (0.516, 2.210)` shown against the common-τ² `1.072 (0.629, 1.825)`, with the page telling
the reader **the wider interval is the one to read**, because with 14/17 edges single-trial the
common-τ² assumption borrows strength the edge has not earned.

**Base engine: YES.**

---

## 8. FAMILY G — RISK OF BIAS

### RM-G01 · `safeRob` unknown → "low"
**One line.** Every *Some concerns* RoB rating is silently coerced to *Low*, corpus-wide.

**Root cause.** The sanitiser's valid list omits the curated vocabulary:
```js
safeRob = rob => { const valid=["low","some","high"];
  return Array.isArray(rob) ? rob.map(r => valid.includes(r) ? r : "low")
                            : ["low","low","low","low","low"] }
```
The stored value is `"some-concerns"`, which is **not** in `valid`, so it maps to `"low"`. The overall
judgement is `rob.includes("high") ? "high" : rob.includes("some") ? "some" : "low"`, so the whole
trial renders **Low Risk**. `[IRON]` §4(1), `[BUG-CAT]` #2.

**Detector (STATIC).**
```
rg -c 'valid\.includes\(r\)\?r:"low"|valid.includes\(r\) \? r : "low"' *_REVIEW.html
rg -c 'safeRob' *_REVIEW.html
python scripts/rapidmeta_error_sweep.py --only RM-G01
```
Fails on any `safeRob` whose fallback is `"low"`, and on the all-`"low"` non-array default.
**Verified present at HEAD** in `SGLT2_HF_REVIEW.html`: `safeRob=rob=>{const valid=["low","some","high"]`.

**Fix.** Guard **G08**: map known aliases (`some-concerns`, `some concerns`, `unclear`, `moderate`,
`medium`) → `"some"`; `serious`/`critical` → `"high"`; **any unrecognised value → `"some"`, never
`"low"`**; a non-array → all-`"some"`. `[IRON]` §4(1); verified in-browser (HEART-FID renders
**Some Concerns**).

**Observed in.** Corpus-wide — every app carrying the sanitiser. `IV_IRON_HF_REVIEW.html` is the
worked instance: all four trials rendered "Low Risk" against a true rating of "Some concerns".
Also fixed on `SOTAGLIFLOZIN_*` (`765318c3c` RoB2 D4/D5 reassessed against the signalling questions;
`b1cef25fb` "RoB chart truth").

**Base engine: YES — this is the single widest defect in the registry.**

---

### RM-G02 · RoB asserted from design fields alone
**One line.** A "Low" RoB is asserted from AACT design fields (randomised, double-blind) rather than
from a RoB 2 assessment.

**Detector (STATIC).** Flag a RoB column populated where no RoB 2 domain answers are stored.

**Fix.** Render **"not assessed"**. `[ARNI]` ea1a8fea1.

**Observed in.** `ARNI_HF_REVIEW.html` — all four trials.

**Base engine: YES.**

---

## 9. FAMILY H — MACHINERY

### RM-H01 · k-inappropriate machinery
**One line.** NMA league tables, node-splitting, CINeMA, funnel plots, Egger, trim-and-fill, Copas,
meta-regression, TSA/RIS, L'Abbé and NNT-from-HR are rendered where `k` or the estimand cannot support
them, manufacturing an appearance of depth.

**Root cause.** Panels render unconditionally. `[BUG-CAT]` #5.

**Detector (STATIC).**
```
python scripts/rapidmeta_error_sweep.py --only RM-H01
```
Fails per panel against its threshold: funnel/Egger/trim-fill **k < 10**; Copas **k < 15**;
meta-regression **k < 10 or covariates ≥ k−2**; subgroup interaction **any subgroup with k = 1**;
L'Abbé **non-binary estimand**; NNT **non-RR/OR estimand or no baseline risk**; NMA surfaces **no
network / no closed loop**; TSA **k < 5 or a fixed 100% information fraction**.

**Fix.** Guard **G10**: suppress with an **on-panel reason**, keep the forest plot and the pooled
estimate. Extend suppression to **every** pooled-model derivative — leave-one-out, Baujat, influence,
sensitivity, cumulative MA, conditional power, RoB-ME — *"a leave-one-out of an invalid pool is
exactly as misleading as the pool"* (`[ARNI]` 554b6f2a2). Where a panel is **not applicable** rather
than under-powered, **remove it with a note that explains the absence**, not a blank space.

**Observed in.** `ARNI_HF_REVIEW.html`, reproduced in-browser on the pre-fix build before anything was
changed: `"TSA: Evidence sufficient — OBF boundary crossed"`, `"RIS: 292"` against 18,856 randomised,
information fraction pinned at **100% for every outcome including a k = 1 one** while
*"info fraction = ?%"* printed in its own caption; `"R² = 100.0% of heterogeneity explained"` with
covariate p = 0.420 **from 3 studies**; a subgroup interaction test with **exactly one trial per
subgroup**; `"Copas (exploratory): Robust"` at **k = 3**; `"NNT ≈ 63"` derived from the pooled HR via
**one assumed 10% baseline risk**. **31 surfaces suppressed, 5 removed.**
`SOTAGLIFLOZIN_*` — `bd43222da` "suppress the k=2-invalid and wrong-estimand diagnostics".

**Base engine: YES.**

---

### RM-H02 · Inadmissible estimator / uninterpretable heterogeneity at small k
**One line.** DerSimonian-Laird at k < 10, and `I² = 0%` / `τ² = 0` quoted as evidence of homogeneity
at k = 2.

**Detector (STATIC).**
```
rg -o 'pooled_DL|DerSimonian' *_REVIEW.html
python scripts/rapidmeta_error_sweep.py --only RM-H02
```
Fails when the DL estimator is used with k < 10, or when `I²` / `τ²` is rendered without a k-gate at
k < 3.

**Fix.** REML or Paule-Mandel below k = 10; a Mantel-Haenszel fixed-effect summary at very small k;
never quote `τ²`/`I²` as interpretable at k = 2. `[RECIPE-C]` §5.2, `rules/advanced-stats.md`.

**Observed in.** `RIFAPENTINE_TB` S1 — `pooled_DL` at **k = 2**; `τ² = 0.0` from `Q = 0.00093` on
df = 1 is uninformative and the reported **I² = 0.0% is an artefact of k = 2**. `[RIFA]` §3.
`APIXABAN_ACS` uses MH-OR with Robins-Breslow-Greenland SE and **quotes no τ² or I²** — the correct
handling, recorded as the reference behaviour.

**Base engine: YES.**

---

### RM-H03 · Fragility index where undefined
**One line.** A fragility index is quoted for an indirect network contrast, a person-time outcome, or
a cluster-randomised trial — where no observed 2×2 exists.

**Detector (STATIC).** Assert an FI is rendered only for a **significant, direct, observed** 2×2.

**Fix.** Guard **G10**: state the fragility is **unmeasurable**, not favourable. `[RECIPE-C]` §3.2:
computing one for an indirect estimate requires inventing patients.

**Observed in.** `[HFREF]` — **16 of 17** CI-excludes-1 contrasts were purely indirect (`direct_k = 0`)
(`[RECIPE-C]` §3.2); §5b of the gates report states 11 of 12 for the earlier fit. Also a **crash**,
not just a wrong number: the FI called Fisher's exact on an implausible 2×2 and raised
`math domain error` instead of skipping the row — found while building the gate's self-test
(`[APIXABAN]` §3). FI must skip rows failing G1.

**Base engine: YES.**

---

### RM-H04 · N/A gate reported as a pass
**One line.** A gate that does not apply reports `0`, which reads as a pass.

**Root cause.** The verdict counters have no `N/A` state — the same family as the recorded
SKIP-as-pass arbitrator bug (`rules/lessons.md`).

**Detector (STATIC).**
```
python scripts/rapidmeta_error_sweep.py --only RM-H04
```
Fails when `P0_grim: 0` is present on an app whose outcomes are all binary (no mean of a bounded
integer scale exists to reconstruct), or when a Benford verdict is rendered on < 30 digits, or when
registry concordance is reported without a covered fraction.

**Fix.** A distinct `N/A` state printed **with its reason**. *"N/A is not a pass"* — `[RECIPE-C]`
rule 6; `[RECIPE-GH]` §4.

**Observed in.** `APIXABAN_ACS` B5 — `P0_grim: 0` on binary per-arm counts. Benford at **16 values**
against a ≥30 requirement → the honest verdict is `UNDERPOWERED`, not "no signal";
`RIFAPENTINE_TB` at **8 digits** → N/A, *"a verdict here would be noise presented as evidence"*.

**Base engine: YES.**

---

### RM-H05 · External-validation claim against a different-scope benchmark
**One line.** "Externally validated against a published meta-analysis" where the benchmark's scope is
a different outcome.

**Detector (STATIC).** Assert the benchmark record's declared scope matches the selected scope, and
that the benchmark's own `k` is consistent with the trials it names.

**Fix.** Bind benchmarks to the scopes they actually cover; relabel as **not re-verified** where they
do not. Guard **G11**.

**Observed in.** `IV_IRON_HF_REVIEW.html` — the only stored benchmark is
`PUBLISHED_META_BENCHMARKS.MACE` (Graham 2023, RR 0.84, 0.76–0.93) whose declared scope is
**"CV death + HHF"**, a composite, and whose `k: 3` **contradicts the four trials named in its own
scope string**. `BENCHMARK_OUTCOME_MAP` mapped `default`, `ACM` and `ACH` onto it, so an **all-cause
mortality** selection was being "validated" against a composite-outcome meta-analysis. `[IRON]` §4(2).

**Base engine: YES.**

---

### RM-H06 · Non-inferiority margin discarded into a superiority pool
**One line.** A non-inferiority trial is pooled into a superiority estimate with its margin dropped.

**Detector (SOURCE).** Registry `designInfo.primaryPurpose` / the publication's stated design and margin.

**Fix.** Carry the margin; a pooled superiority estimate from NI trials is a claim the sources do not
make. `[RECIPE-GH]` §2.8.

**Observed in.** `RIFAPENTINE_TB` — iAdhere is a non-inferiority trial with a **15% margin**, pooled
into a superiority odds ratio with the margin discarded. `[RIFA]` §2.2.

---

## 10. FAMILY I — DIRECTION

### RM-I01 · Direction inversion
**One line.** A harm is presented as a benefit, or a benefit as a harm; an NNH is computed on a
benefit outcome.

**Root cause.** Three distinct mechanisms, all producing the same surface error:
1. **Arm inversion** (RM-C03) — the estimate is computed the right way round on the wrong arms.
2. **Good-outcome polarity** — an OR < 1 on a *good* outcome (negative culture, treatment completion)
   means the intervention is **worse**, and the app presents OR < 1 as favourable regardless.
   `[RIFA]` §2.1.
3. **A direction flag computed from the wrong quantity** — `[HFREF]` `2acab11aa`:
   *"direction is |ln RR|, not sign(RR change) — BB moves AWAY, not toward"*.

**Detector (STATIC).** Assert every outcome row carries an explicit `polarity` (`benefit` = lower is
better / `harm` = lower is worse / `neutral`), and that the rendered direction word is derived from
`polarity × effect`, never hardcoded.
```
python scripts/rapidmeta_error_sweep.py --only RM-I01
```
Fails on a missing `polarity` field, on an NNH rendered for a `benefit`-polarity outcome, and on a
hardcoded direction word.

**Fix.** Guard **G17**, fail-closed: no direction word without an explicit polarity.

**Observed in.** `APIXABAN_ACS_AUTO_FULL_REVIEW.html` — **the live app claimed apixaban BENEFIT**
(pooled OR 0.850, 0.780–0.926, nominally significant, favouring apixaban). Corrected to
**OR 1.975 (1.223–3.189)** — apixaban roughly **doubles** major/CRNM bleeding, which is why APPRAISE-2
was terminated. `cb876d805`. The sign flip is the headline of `[APIXABAN]` §4, and the final gated
value is **OR 1.9748 (1.0411–3.7458), p = 0.0372, k = 2** with `preliminary: true`.
`[HFREF]` — direction flag corrected at `c0627f56f` / `2acab11aa`.

> **MAVACAMTEN_HCM_REVIEW.html is this registry's defect chain in a single app** (`[MAVA]` ecd1aba43),
> and it is worth reading as one causal sequence rather than six findings:
> 1. `realData` stored published **odds ratios** (EXPLORER-HCM 2.8, EXPLORER-CN 6.9) and a raw event
>    **percentage** (VALOR 17.9%) in a field named `publishedHR` — RM-A03, RM-A07.
> 2. `estimandType` **defaulted to "HR"** whenever `pubHR` was present — RM-A02.
> 3. `COMPLETE-POOLING-REPAIR` force-switched the effect measure to `"HR"` whenever every included
>    trial carried a `publishedHR`, **purely to maximise k** — RM-B02.
> 4. Inverse-variance pooling of those three mislabelled values gave **5.05** fixed and **6.63**
>    random, which the label layer then relabelled **"RR"** — RM-A02, RM-A03.
> 5. `interpretRelativeEffect` saw `lci > 1` and returned **"harm"** — on an outcome where a higher
>    response rate is **good** — RM-I01, RM-I02.
> 6. The narrative templates were the **finerenone donor's, unedited** — RM-E01.
>
> The fix is the same shape as guard **G17**: an **estimand registry declares whether higher or lower
> is better for each endpoint**, and benefit/harm is derived from it; where polarity is not
> established the direction is reported as **undetermined** and no benefit or harm is claimed.
> Withdrawn: *"significant harm"*, the NNH, *"33 out of 100 patients may be harmed"*, and the L'Abbé
> *"below the line = benefit"* note — **both** NNT/NNH computations, because Patient Mode and the
> Scientific Output narrative each had their own.

> **The mandatory framing, from `[RECIPE-C]` §5.3:** *"this is a provenance correction, not a result
> that got worse. The evidence did not change. The app was wrong."*

**Base engine: YES.**

---

### RM-I02 · Good-outcome / bad-outcome sign conflict in one pool
**One line.** A *good* outcome and a *bad* outcome are combined on one odds-ratio scale with no sign
reconciliation.

**Detector (SOURCE, then STATIC once polarity is stored).** With `polarity` present this becomes
static: flag any pool whose contributing rows have mixed polarity.

**Fix.** Guard **G17** blocks the pool.

**Observed in.** `RIFAPENTINE_TB` S2 (**P0**) — the withdrawn pooled estimate combined a **good**
outcome (negative culture, OR<1 = worse) with a **bad** outcome (a failure-to-complete reason,
OR<1 = better). Independently recomputed fixed-effect logOR **−0.944898**, matching the app's stored
**−0.944897553936862**: *"the app computes correctly what it should not be computing at all."*
The app's own `__verdict` had already recorded *"2 AACT outcome-direction divergence(s)"*. `[RIFA]` §2.3.

**Base engine: YES.**

---

## 11. FAMILY J — GOVERNANCE AND PROCESS

### RM-J01 · False ICMJE / PROSPERO equivalence attribution
**One line.** The page claimed *"per ICMJE 2023, GitHub commit hash + timestamp constitutes a
verifiable pre-registration record equivalent to PROSPERO"*.

**Root cause.** An invented attribution attached to a real mechanism. Checked: **ICMJE has no
systematic-review registration requirement at all** — its 2005 mandate covers clinical trials, and
PROSPERO-style SR registration is a journal-level expectation, not an ICMJE rule. `[ARNI]` ce187425e.

**Detector (STATIC).**
```
rg -i 'ICMJE|equivalent to PROSPERO|constitutes a verifiable pre-registration' *_REVIEW.html
python scripts/rapidmeta_error_sweep.py --only RM-J01
```
Fails on any ICMJE attribution for SR registration, and on any claim of equivalence to PROSPERO.

**Fix — and this is the part that must not be over-corrected.**
> **Mahmood's ruling (`[BUG-CAT]` #7, implemented at `[ARNI]` ce187425e and `[SGLT2]` 875fbd980):**
> **KEEP** the git-timestamp mechanism as a legitimate tamper-evident public-push protocol record —
> arguably **stronger** than PROSPERO. Drop **only** the false ICMJE attribution and the
> literal-equivalence label.

The first fix attempt (`[ARNI]` Tier 1, `554b6f2a2`) **over-corrected**: it deleted the mechanism
outright and replaced it with a flat *"NOT prospectively registered"*, throwing away a legitimate
mechanism along with the two false claims attached to it. `ce187425e` restores it and claims it on its
own merits:

- **Why it is real.** Git history is a Merkle chain: every commit hash covers its own content **and**
  its parents, so altering an earlier protocol commit changes the hash of every commit after it. Once
  the history is public, third parties hold the original hashes — silent revision becomes
  **detectable**, not merely discouraged.
- **Three axes where it is stronger than a registry entry:** tamper-evident rather than only curated;
  the entire protocol document diffable line by line across its whole history rather than summarised
  as field-level revision notes; and ungated — no third party decides whether or how quickly a
  protocol may be recorded.
- **What a registry has that git does not** (stated on the page): custody by an independent
  institution, and the settled expectation of journals and reviewers in this field.
- **The honest caveat.** A commit's date field is metadata the author can set, so **a commit date on
  its own proves nothing**. The evidence is the **PUBLIC PUSH** — a third-party-observed record that
  the content was visible at that time. Two strengtheners, deliberately **not** conflated: an external
  time anchor (RFC 3161 TSA or an OpenTimestamps proof) establishes that content existed by a given
  time independently of the repository owner — worth adding because GitHub's public events feed is not
  retained indefinitely; a GPG/SSH-signed tag establishes authorship and tree integrity, but the time
  inside a signature is **self-asserted**. *Signing proves who and what; anchoring proves when.*

Guard **G11** enforces the negative half (no ICMJE attribution, no equivalence label) and asserts the
mechanism text **survives**, so a future edit cannot quietly delete it again.

**Base engine: YES** — the claim is boilerplate.

---

### RM-J02 · Retrospective protocol framed as prospective
**One line.** A protocol written alongside the analysis is presented as a pre-registration.

**Detector (STATIC).** Assert that where the protocol is retrospective, the page says so explicitly
and does not carry a prospective-registration claim by **any** mechanism, git included.

**Fix.** State it plainly: the protocol is retrospective, the review is **not** prospectively
registered, and its outcome, eligibility and analysis-plan choices are **not protected against
selection after seeing the data**. The provenance mechanism of RM-J01 applies prospectively **only**
where the protocol commit is pushed *before* the analysis begins. *"Reframing the mechanism must not
smuggle a prospective claim into a retrospective review"* — `[ARNI]` ce187425e, which ships a test
asserting exactly that. Also: *"Retrospective Public Protocol Pack (OSF-ready)"* → **"NOT a
registration"** (`[ARNI]` 554b6f2a2).

**Base engine: YES.**

---

### RM-J03 · Eligibility criteria self-contradiction
**One line.** The review's stated eligibility criteria exclude the review's own included trials.

**Detector (SOURCE).** Run the stated criteria against the included set; every included trial must satisfy them.

**Fix.** Correct the criteria and **record the contradiction**.

**Observed in.** `ARNI_HF_REVIEW.html`, three instances, all corrected (`[ARNI]` ea1a8fea1):
the comparator criterion required a placebo arm and excluded *"active comparator without placebo
arm"*, which would have excluded **all four** trials (enalapril, ramipril, valsartan — none has a
placebo arm); the outcome criterion required *"extractable 2×2 data"* and excluded *"biomarker-only"*,
contradicting the inclusion of PARAGLIDE-HF (biomarker primary, no 2×2) and PARAGON-HF (no 2×2);
the publication criterion excluded pre-2015 while PARADIGM-HF (2014) was included throughout.
The single comparator claim *"RAAS Inhibitor (Enalapril or Valsartan)"* is now per-comparison —
**the comparator not being common across comparisons is itself a reason not to pool.**

---

### RM-J04 · Gate that cannot fail
**One line.** A verification gate with no failing path, or whose exit status is read through a pipe.

**Detector (STATIC).** Every gate must ship a `--selftest` that BLOCKs on a seeded defect. A gate
without one is **not reportable evidence**. `[HARNESS]` F-07 §14.

**Fix.** Negative-test every gate. Working examples in this corpus:
`clone_contamination_gate.py --selftest` → SELFTEST PASS (`[IRON]` §5);
`gh_verify_upgraded_app.py --selftest` → **6 of 6 seeded defects BLOCK** (`[RIFA]` §6);
`scripts/test_cardio_inventory.py` asserts the gate returns zero findings on a clean synthetic ledger
and non-zero on an `e > N` ledger, 15/15 (`[APIXABAN]` §3);
`[ARNI]` seeded 4 known-bad regressions and got exactly 4 failures in the 4 corresponding tests;
`[VIVAX]` `check_verdict_parity.py` passes on the artifact **and** blocks on a known-bad input.

> **Correction carried from `[HARNESS]` F-07, recorded so it is not repeated:** the session note that
> *"the repo pre-push git hook is THEATER (always PASS)"* does **not** survive contact with the
> artifact. `F:\rapidmeta-finerenone\.git\hooks\` has **no pre-push hook at all**;
> `scripts/regression_check.py` **can** fail today (`return 1`, `sys.exit(main())`, fixed at
> `552c1112d`). What **is** still live: an unguarded `from playwright.sync_api import sync_playwright`
> at L181 → `ImportError` mid-run, and a **third exit code** (`return 2`, environment failure) that a
> caller testing `==0`/`!=1` reads as its opposite.

---

### RM-J05 · COMPLETED-only registry filter
**One line.** The registry query filters to `overallStatus: COMPLETED`, silently excluding terminated
and withdrawn trials.

**Detector (STATIC).** Grep the app's stored search strategy for a status filter.

**Fix.** Include terminated/withdrawn; **a trial stopped early for harm is exactly the trial a safety
review must not miss.** `[BUG-CAT]` #7 — both sotagliflozin trials stopped early.

**Base engine: YES** — the acquisition query is shared.

---

### RM-J06 · Line-ending drift / whole-file rewrite on edit
**One line.** A 2-line edit produces a whole-file diff, defeating review.

**Root cause.** The corpus is **CRLF**; a script read with Python's default universal-newline
translation (CRLF → `\n`) and wrote with `newline=""` (passes `\n` through), so every line changed.
`[RIFA]` §8 — a 6341/6341-line diff for a 2-line edit.

**Detector (STATIC).** After any app edit: `git diff --numstat` must show a line count proportional to
the **edit**, not to the **file**.

**Fix.** `newline=""` on **both** read and write. After the fix the same edit is a **2-line diff**
with `CRLF 6341 / bare LF 0`, byte-identical endings to HEAD.

> **This must be checked on every app in every batch.** It would have made the 526-app contamination
> remediation unreviewable.

---

## 12. What this registry does NOT cover

1. **Defects that need a browser.** RM-B02 Defect 4 (`paper-studio.js` scope flip) was found only by
   walking all eight tabs and re-reading `state.selectedOutcome` after each. The static sweep can
   detect the *presence* of the shared heuristic; it cannot detect an app-local override that fails.
2. **Defects that need a source lookup.** RM-A06, RM-B04, RM-C02, RM-C03, RM-D03, RM-D04 and RM-H06
   are per-app registry/PubMed work at ~20 min/trial (`[APIXABAN]` §6 measures the full recipe at
   `95 min + 20·k + 5·findings`, ~3–4 h/app at the corpus mean k = 3.6).
3. **The 4 apps with filename/content mismatches** are recorded (RM-D06) but **two are documented and
   two are only counted** — `[RECIPE-C]` §0.3 states four exist; `[CARDIO-MIS]` documents two.
4. **Whether any of this is *fixed*.** This is a detection registry. Remediation runs as separate
   gated batches.
5. **Findings that did not survive verification are not in the prevalence counts** — deliberately.
   `[ATTR]` 9e658033f flagged two of its own review points as unconfirmed rather than acting on them:
   APOLLO-B's *"10/181 vs 10/179"* had **no primary source** and a 404 citation, so the registry
   values (4/181 vs 8/178) were used with both disclosed; and HELIOS-B's recurrent-CV rate-ratio CI
   could not be confirmed, so it is marked `ciVerification:"UNCONFIRMED"` and **excluded from
   pooling**. That is the RM-D04 disposition working as intended.

---

## 13. Attribution

Registry data: **ClinicalTrials.gov API v2**. Bibliographic data: **PubMed** (NCBI E-utilities).
Fragility index per Walsh M et al., *J Clin Epidemiol* 2014;67:622-628. Statistical admissibility
thresholds per `rules/advanced-stats.md`. Harness failure modes per `F:\E156\HARNESS-FAILURE-MODES-2026-07-30.md`.

---

# 14. ADDENDUM v2.0 — types added by the 2026-07-30 calibration cases

Three apps were run through the full detector suite as calibration. Each defect below was written
against a **real offending string** in one of them; the prevalence figures are from the 52-detector
sweep of 1,088 apps. Their corrected extraction truth is a labelled test case in
`tests/fixtures/rapidmeta_error_fixtures.json`, consumed by detector `RM-V01` and by the batch runs
as the acceptance target.

**All three are priority batch targets — Batch 1 in `RAPIDMETA_BATCH_PLAN.md`.**

## 14.0 INDEX — the 16 new types

| id | name | detector | guard | apps | % |
|---|---|---|---|---:|---:|
| RM-A10 | Kaplan-Meier risk rendered as a crude event count | STATIC | G15 | 5 | 0.5% |
| RM-A12 | Effect estimate contradicts its own 2×2 | STATIC | G18 | 134 | 12.3% |
| RM-A13 | Estimand-granularity mismatch (composite components differ) | STATIC | **G19** | 9 | 0.8% |
| RM-A14 | `escalc(measure="RR")` over rows tagged as different endpoints | STATIC | G06 | 744 | 68.4% |
| RM-C04 | Arm reversal (device/control denominators swapped) | STATIC+SOURCE | G15 | 4 | 0.4% |
| RM-D07 | False "no external benchmark exists" | STATIC | G11 | 171 | 15.7% |
| RM-D08 | False registry-status claim | STATIC+SOURCE | G09 | 767 | 70.5% |
| RM-D09 | Phase label inapplicable to a device/behavioural trial | STATIC | G09 | 23 | 2.1% |
| RM-D10 | Duplicate, NULLED or ghost trial rows | STATIC | **G18** | 512 | 47.1% |
| RM-D11 | Published pooled estimate shown as a trial-level effect | STATIC | — | 21 | 1.9% |
| RM-D12 | Citation volume/issue/page metadata mismatch | STATIC+SOURCE | — | 0 | 0.0% |
| RM-E03 | Registry/monitoring watchlist tracks the wrong drug class | STATIC | **G20** | 56 | 5.1% |
| RM-B08 | Search under-inclusion vs a known external synthesis | STATIC+SOURCE | — | 33 | 3.0% |
| RM-G03 | RoB chip contradicts the trial's own extraction evidence | STATIC | G08 | 701 | 64.4% |
| RM-J07 | Integrity gate passes over a fail-closed condition | STATIC | **G18** | 1030 | 94.7% |
| RM-V01 | Displayed value contradicts the source-verified fixture | STATIC | — | 3 | 0.3% |

---

## 14.1 · RM-A14 — the smoking gun for estimand-mixing + scope-lock

**One line.** The generated R code pools every trial's `tE`/`cE` as one binary risk ratio, whatever
endpoint or timepoint each row actually is.

**Root cause — quoted from the app, not paraphrased.** The R generator is:

```js
ai = c(${trials.map(t=>t.data.tE).join(",")}), n1i = c(${trials.map(t=>t.data.tN).join(",")}),
ci = c(${trials.map(t=>t.data.cE).join(",")}), n2i = c(${trials.map(t=>t.data.cN).join(",")})
dat <- escalc(measure="${emR}", ai=ai, n1i=n1i, ci=ci, n2i=n2i, data=dat)
```

It maps across **every included trial** with no estimand or timepoint test. Rendered on the
mitral-TEER app it emits, literally:

```r
ai = c(83,139,151); ci = c(78,170,212); escalc(measure="RR")
```

- **83 / 78** is MITRA-FR's **12-month** composite
- **139 / 170** is RESHAPE-HF2's **24-month RECURRENT** composite — *and its arms are reversed*
- **151 / 212** is COAPT's **24-month** composite

Three different constructs at three timepoints pooled as one binary risk ratio, under a selector
labelled *"All-cause mortality at 24 months"*.

**Detector (STATIC).** Fires when `escalc(measure=` is present **and** the `ai = c(${trials.map(...)})`
generator is present **and** the ledger's PRIMARY rows are not the same construct or not the same
timepoint.
```
python scripts/rapidmeta_error_sweep.py --only RM-A14
```

**Fix.** Guard **G06** — build the vector from one estimand stratum only, and name the held-out
trials with their estimand. **Base engine: YES — 744 apps (68.4%).**

---

## 14.2 · RM-A10 — a Kaplan-Meier risk rendered as a crude event count

**One line.** A KM % (or a per-100-patient-year rate) is multiplied by N to manufacture per-arm counts.

**Why it is not a rounding issue.** A KM estimate is a **model-based cumulative incidence under
censoring**. `events = KM% × N` is not a count of anything: the true numerator is smaller, and the
denominator is not the number at risk at that time.

**Observed in.** `MITRAL_FUNCMR_REVIEW.html` — COAPT's all-cause mortality is published as
**KM 29.1% vs 46.1%, HR 0.62 (0.46–0.82)**; the app displays the *composite* 151/302 vs 212/312.
The detector's own evidence line: *"COAPT: control 212/312 = 67.9% reproduces the 67.9% figure, and
the source states it as a per-patient-year rate"* — COAPT's HF-hospitalisation figures **35.8 / 67.9**
are **annualised events per 100 patient-years**, not patient percentages.

**Fix.** Carry the KM estimate as a KM estimate with its HR. Guard **G15** refuses to derive a count
from a rate; **G05** renders NA rather than a manufactured integer.

---

## 14.3 · RM-A12 — an effect that contradicts its own 2×2

**One line.** The displayed effect sits on the opposite side of 1 from the crude ratio of the counts
displayed beside it.

**Distinct from RM-A08**, which is a wrong count/effect *pairing*. Here the effect is simply **not
derivable from these counts at all**.

**Observed in.** `BEMPEDOIC_ACID_REVIEW.html` — CLEAR Harmony's own evidence prose reads
*"Adjudicated cardiovascular events occurred in **108 patients (7.3%)** in the bempedoic acid group
and in **40 patients (5.4%)** in the placebo group"*, i.e. crude RR **1.346**, beside a displayed
**HR 0.75 (0.56–1.00)**. **134 apps (12.3%).**

**Reported but not reproduced, recorded as such.** The reviewer states that 0.75 (0.56–1.00)
reproduces an earlier published **two-trial pooled RR 0.75 (0.56–0.99)** over ~3,008 participants —
a pooled estimate displayed as a trial-level HR (RM-D11). The file's own `PUBLISHED_META_BENCHMARKS`
does **not** contain that record, so it remains a source-verification task, not a confirmed static
finding.

**Fix.** Guard **G18** blocks the analysis; the row is re-sourced or quarantined.

---

## 14.4 · RM-C04 — arm reversal

**One line.** The intervention and control denominators are swapped.

RM-C03 is the registry-verified form (bind by title, not index). **RM-C04 is the same defect stated
as an app-level fact** and is the form the fixture verifies.

**Observed in.** `MITRAL_FUNCMR_REVIEW.html` — RESHAPE-HF2 ships `tN: 255, cN: 250`. The trial
randomised **device 250, control 255**. The detector fires from the fixture:
*"RESHAPE-HF2: ARM REVERSAL — tN=255 is the CONTROL n; the device arm is 250."*

**Consequence.** The reversal feeds RM-A14's `ai=c(...,139,...)` vector, so the wrong arm enters the
pooled estimate as well as the trial card.

---

## 14.5 · RM-D01 (2nd fully-verified instance) — a wrong NCT importing foreign eligibility text

`BEMPEDOIC_ACID_REVIEW.html` carries **NCT02973841** for CLEAR Wisdom. Resolved live against
ClinicalTrials.gov API v2 on 2026-07-30:

> **NCT02973841** — *"Sono-ease Device for Internal Jaguar Vein Cannulation"*, Mansoura University,
> **n = 40**, ages **18–45**, phase **NA**, `has_results: false`. Eligibility: *"all patients
> indicated for IJV catheterization"* / *"neck deformities-coagulopathy"*.

**That eligibility text is what the app displays as CLEAR Wisdom's.** The correct identifier is
**NCT02991118** (acronym *CLEAR Wisdom*, enrolment **779**, PHASE3, `has_results: true`) — and the
app's own `baseline.n: 779` matches it, which is what proves the row *is* CLEAR Wisdom wearing
another study's id.

This is the second instance of the class after ATTR-CM's HELIOS-B → a cerebrospinal-fluid shunt
study. **A wrong identifier does not mislabel a row; it imports another trial's text into the app.**

---

## 14.6 · RM-D12 — citation metadata mismatch

`BEMPEDOIC_ACID_REVIEW.html` displays *"JAMA. 2019;322(**14**):**1380-1388**"* for CLEAR Wisdom.
Verified via PubMed esummary, 2026-07-30: **PMID 31714986, JAMA 2019;322(18):1780-1788**.

**The static detector returns 0 across the corpus** — its static form only catches two *different*
citations for one trial inside one app. The bempedoic mismatch is caught by **RM-V01** against the
fixture. Recorded so the zero is not read as a clean result.

---

## 14.7 · RM-E03 — the monitoring watchlist is the wrong drug class

**One line.** The app's live registry/monitoring surface tracks another drug programme entirely.

**Distinct from RM-E01** (prose residue) and **RM-E02** (trial-alias table): this is the surface the
app uses to say *what it is watching for new evidence*.

**Observed in.** `PCSK9_REVIEW.html` **and** `BEMPEDOIC_ACID_REVIEW.html`, both carrying
`CTGOV_EVIDENCE_REGISTRY` populated with the **finerenone** programme —
**FIDELIO-DKD, FIGARO-DKD, FINEARTS-HF, ARTS-DN, FINE-ONE, CONFIDENCE** — with per-trial
`registeredPrimary` labels like *"Renal Composite (eGFR ≥57% decline)"*. **56 apps (5.1%).**

**Fix.** Guard **G20** blocks a watchlist that is wholly or partly off the app's own topic.

---

## 14.8 · RM-B08 — search under-inclusion vs a known synthesis

**One line.** k far below a synthesis the app itself cites, with no include/exclude record for the
missing trials.

**Observed in.** `PCSK9_REVIEW.html` pools **k = 2** — FOURIER and ODYSSEY OUTCOMES. A prior
published synthesis found **38 RCTs** (MACE OR 0.83, 0.78–0.88). The strings **SPIRE** and **OSLER**
do not occur anywhere in the file.

**Why it is selection bias, not just incompleteness.** SPIRE-1/2 studied **bococizumab**, a
**negative** agent stopped for immunogenicity. Omitting it while retaining the positive agents is the
same class as the omitted-trial finding recorded in ATTR-CM.

**Detector honesty.** A string-grep **cannot find an absent trial**. The detector's only static
handle is the benchmark's own declared `k`, so it flags "k far below a known synthesis" and hands off
to the source lane. **33 apps (3.0%).**

---

## 14.9 · RM-A13 — composite component sets differ across pooled rows

**Observed in.** `PCSK9_REVIEW.html` — FOURIER's primary is *"CV death, MI, stroke, UA
hospitalization, **or coronary revascularization**"*; ODYSSEY OUTCOMES' is *"**CHD death**, nonfatal
MI, ischemic stroke, or UA requiring hospitalization"*. **Different constructs, one scope label.**
`BEMPEDOIC_ACID_REVIEW.html` — CLEAR Wisdom's MACE-3 pooled with CLEAR Outcomes' MACE-4 and with
"all adjudicated events".

**Fix.** Guard **G19**: every pooled row must **declare** its component set, and the sets must be
identical. **An undeclared composite cannot be shown to match another** — so undeclared blocks too.

---

## 14.10 · RM-D09 — phase label inapplicable to a device or behavioural trial

ClinicalTrials.gov records device and behavioural RCTs as phase **Not Applicable**. The mitral-TEER
app asserts **COAPT III, MITRA-FR III, RESHAPE-HF2 IV**.

**Two harms, not one.** The label is wrong; **and** a phase-III/IV eligibility rule — which several
apps in this corpus apply — would **wrongly exclude every device trial in the topic**.

---

## 14.11 · RM-G03 — the RoB chip contradicts its own extraction evidence

**Observed in.** `MITRAL_FUNCMR_REVIEW.html` — COAPT's extraction evidence states **D2
some-concerns / D4 low**; the chart chips show **D2 high / D4 high**; and the GRADE text claims
*"majority high on D1/D4"* while its own table shows **D1 low in all three trials**.
**701 apps (64.4%).**

**Detector.** Two independent checks: a `D<n> = <level>` claim in the evidence prose vs the `rob[]`
array chip at that index; and a GRADE downgrade reason vs the RoB table it cites.

---

## 14.12 · RM-D10 / RM-J07 — ghost rows, and a gate that passes over them

**RM-D10.** `BEMPEDOIC_ACID_REVIEW.html` carries `NULLED:NCT02666664` and `NULLED:NCT02973841` as
ledger keys, while the **bare** ids are still referenced in `AUTO_INCLUDE_TRIAL_IDS` and
`bempedoicIds` — and the badge claims **"Trials: 4"**. **512 apps (47.1%).**

**RM-J07.** The integrity gate asserts a pass while a fail-closed condition holds. **1,030 apps
(94.7%)** — the highest-prevalence P0 in the registry.

**Guard G18 — adopted verbatim from the bempedoic reviewer's recommendation #9.** The gate must
**FAIL**, not warn, whenever:
1. any trial id is **null / empty / NULLED**;
2. a **composite endpoint is mismatched** across pooled rows;
3. an analysis yields **NaN or an impossible value** — a negative HR, a leave-one-out `NaN–NaN`;
4. **trial counts or N disagree across surfaces** (bempedoic: 4 vs 5 vs 2).

> A *"checks passed / 100-100 integrity / fabrication-risk 0.200"* rendered over any of those **is
> itself the bug.**

---

## 14.13 · RM-A07 strengthened — the impossible ratio

The bempedoic LDL-C selector renders **"Pooled Hazard Ratio = −19.50 / 2050% lower hazard"**. A
negative hazard ratio is mathematically impossible; **−19.50 is a continuous mean difference forced
through the HR reporting template**.

**RENDER-class, and stated as such:** the string is computed at runtime and is **not present
statically**. What *is* statically present — and what RM-A05 detects — is the precondition:
`CONTINUOUS` LDL-C rows (`md: -17.4`, `se: 1.1`) reachable by the HR reporting path.

**Guard G01 now enforces two tiers**, because they fail differently:
- **IMPOSSIBLE** — outside `[0.01, 100]`: not a ratio at all. Catches −19.50 and 2050.
- **IMPLAUSIBLE** — outside `[0.02, 25]`: inside the hard bound but outside any reported effect.
  Catches the andexanet `pubHR 73.83`.

---

## 14.14 · What these three cases proved about the detectors themselves

1. **A clean extraction does not make a sound review.** `PCSK9_REVIEW.html`'s two trial rows verify
   **exactly** to source — FOURIER *"1344 patients [9.8%] vs. 1563 patients [11.3%]; hazard ratio,
   0.85; 95% CI 0.79 to 0.92"*, ODYSSEY *"903 patients (9.5%) ... 1052 patients (11.1%) ... hazard
   ratio, 0.85; 95% CI 0.78 to 0.93"*. **Every defect in that app is structural.** An audit that
   only checks numbers would have passed it.
2. **Two of the new detectors over-fired and one under-fired on first run**, and were fixed at
   source before the numbers were used: `RM-D08` treated *0 PMIDs* as a contradiction of "no linked
   publications" (it is not — that is RM-D02); `RM-D11` matched **k = 1** benchmark records, which
   *are* the trial; `RM-D07` matched a render-time **fallback string** rather than a rendered claim,
   and is now P2 with an explicit RENDER-confirm.
3. **The sweep's own bug class recurred.** Wiring the v2 pack re-imported the base module under a
   second name, re-running its module-level `sys.stdout` wrap and closing the buffer — the exact
   trap recorded in `rules/lessons.md`. Fixed at **both** layers: the wrap is now idempotent, and
   the v2 pack binds to the already-loaded module instead of importing a second copy.

---

## 15. Attribution — v2.0 calibration pass

Registry data: **ClinicalTrials.gov API v2** (live, 2026-07-30) — NCT02991118, NCT02973841.
Bibliographic data: **PubMed** (NCBI E-utilities / esummary, 2026-07-30) — PMIDs 28304224
(Sabatine MS et al., *N Engl J Med* 2017, [DOI](https://doi.org/10.1056/NEJMoa1615664)), 30403574
(Schwartz GG et al., *N Engl J Med* 2018, [DOI](https://doi.org/10.1056/NEJMoa1801174)), 31714986
(*JAMA* 2019;322(18):1780-1788).
