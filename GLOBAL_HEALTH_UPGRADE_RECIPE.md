# The HFrEF upgrade procedure, generalised — operational per-app checklist

**Programme:** raise every communicable-disease / Africa-relevant / global-health RapidMeta app
to the standard set by the HFrEF GDMT network audit
(`audit/hfref-integrity-gates-2026-07-30`).
**Audience of the output:** scientists in resource-limited settings. They cannot buy the
full text, cannot re-run the extraction, and cannot see the machine verdict. Everything
they need to know about how far to trust a number must be on the surface they *can* see.
**Status of this document:** the recipe. It is executed per app on a branch, staged,
gated, and only then proposed for push.
**Version:** 1.1 (2026-07-30) — **v1.1 adds §R, the mandatory error-registry checklist.**

---

## §R. The error registry is the checklist (MANDATORY) ⭐⭐⭐

**Added in v1.1, 2026-07-30.** Every defect this recipe was written to catch now has an **id**, a
**detector that can fail**, and a **fail-closed engine guard**. **A per-app report that names no
registry ids has not run the checklist.**

| Artifact | What it is |
|---|---|
| `RAPIDMETA_ERROR_REGISTRY.md` | **67** error types; id · root cause · detector · fix · example apps · base-engine flag |
| `scripts/rapidmeta_error_sweep.py` | every STATIC detector, per app or corpus-wide; `--selftest` proves they fire |
| `assets/js/rapidmeta-guards.js` | **20** fail-closed guards, G01–G20 (G18 = the fail-closed integrity gate) |
| `tests/mutate_guards_selftest.py` | re-seeds the shipped defects; a guard that survives its seed is theatre |
| `RAPIDMETA_ERROR_SWEEP.{md,json}` | corpus prevalence matrix, including the global-health scope set |
| `F:\E156\GOVERNING-RULES-ADDENDUM-ERROR-REGISTRY-2026-07-30.md` | §18, the governing rules for all of the above |

```
python scripts/rapidmeta_error_sweep.py --only RM-E02     # e.g. the 526-app alias table
python scripts/rapidmeta_error_sweep.py --selftest        # every seeded defect must fire
```

**R.1** Run the static detectors on the app **before** touching it and again on the **final** file.
**R.2** Disposition every firing **by id**, using the five dispositions in §0.1 / the cardio Phase 4.1.
**R.3** Where the registry marks a type **base-engine-shared** (35 of 67), a per-app fix is a
**workaround** and must be labelled one. State the corpus denominator in the commit message.
**R.4** A firing is a **hypothesis**. The HFrEF pass withdrew three of its five findings.

### §R.5 — the ids this disease set hits hardest

| Concern in this corpus | Registry ids |
|---|---|
| Foreign trial-alias table (**526 apps**, 56 in the global-health set) | `RM-E02` |
| SGLT2i / MRA / CKD donor residue in a claim-bearing slot | `RM-E01` |
| Wrong population — active-TB trial in an LTBI review | `RM-B06` `RM-D01` |
| Wrong outcome extracted (culture conversion vs completion; wk48 vs wk96) | `RM-B04` |
| Person-time denominators read as a 2×2 | `RM-A06` `RM-A01` |
| Cluster randomisation ignored (design effect **reduces** N_eff) | `RM-H02` |
| Non-inferiority margin discarded into a superiority pool | `RM-H06` |
| Multi-dose / schedule arms silently collapsed | `RM-B07` |
| Landmark trial absent from the review (PREVENT TB) | `RM-B05` |
| False-green badge over a fabricated fit | `RM-F01` `RM-F02` `RM-F03` |
| Good-outcome / bad-outcome sign conflict in one pool | `RM-I01` `RM-I02` |
| Whole-file rewrite from CRLF drift on edit | `RM-J06` |

**Non-CT.gov registries are N/A, not a failure** (`RM-D01`): PACTR, ISRCTN, CTRI, ChiCTR, EudraCT
and the WHO ICTRP carry much of this corpus. Report the covered fraction; never report N/A as a pass.

---

## 0. The three principles the HFrEF pass actually ran on

Everything below is a mechanisation of these. When the checklist and the principle
conflict, the principle wins.

1. **Quarantine, never silent deletion.** A trial whose numbers have no source is
   *retained in the ledger, flagged, with a stated reinstatement condition*, and excluded
   from the fit. It is never dropped quietly. The verifier **blocks if it is deleted
   instead of flagged** — because a deletion looks identical to a trial that was never
   found, and destroys the record that a problem existed.
2. **Reconcile to the primary source; never fabricate; state the evidence tier.** Where a
   value cannot be read from the primary in this pass, say which tier it came from
   (`VERIFIED_FULL` / `VERIFIED_DENOM_ONLY` / `SECONDARY_CORROBORATED` / `UNSOURCED`)
   rather than glossing. In HFrEF, RESOLVD's counts were labelled
   `SECONDARY_CORROBORATED` because a Cloudflare check was **not circumvented** and the
   full text was therefore never actually read. That label is the deliverable, not a
   caveat on it.
3. **A correction is not a result that got better.** Withdrawing CARMEN's null-pulling
   14/14/14 moved every estimate *away* from the null and raised CI-excludes-1 from 12 to
   17. The report says, in those words, that this is a provenance correction and must not
   be reported as strengthened evidence. Any upgrade that makes an app's headline look
   stronger must carry that sentence.

**A fourth, learned the hard way in HFrEF:** the audit itself is a source of false
findings. Three of its five findings were **withdrawn as wrong** on verification — SPICE
"has no primary source" was an artefact of searching on an acronym that never appears in
the PubMed record. Budget for the withdraw step. An audit finding is a hypothesis.

---

## 1. Scope & pre-flight (per app)

| # | Step | Command / evidence | Fail-closed? |
|---|---|---|---|
| 0.1 | Branch off the current corpus head; never `main`, never another thread's branch | `git switch -c upgrade/<slug>-<date>` | — |
| 0.2 | Confirm the app is in scope and not owned by another thread (**malaria NMA rebuild is owned elsewhere — defer, do not duplicate**) | `outputs/gh_inventory.json` row | yes |
| 0.3 | Record the app's **starting** state: both badge surfaces, trial count, data state, contamination hits | `python scripts/gh_inventory.py` | — |
| 0.4 | Confirm the trial ledger is machine-readable (a `TRIALS=[...]` array or an equivalent payload). If the app is a **stub** (<20 KB) or a **template** (0 NCT, no payload), it does not enter this recipe — it enters the *build* queue instead | grep for the payload | yes |
| 0.5 | Locate the fitted payload the visible claims are rendered from, and confirm there is exactly **one** data source. HFrEF's live-render check found the app was rendering from `window.HFREF_FIT` alone; an app with two payloads can contradict itself silently | — | yes |

---

## 2. Verify every extracted number to a primary source — `RM-A06` `RM-B04`–`RM-B07` `RM-C01`–`RM-C03` `RM-D01`–`RM-D04`

**Rule: every number and identifier by lookup, never recall.** Output is one row per
trial in `outputs/<APP>_source_verification.json`, each carrying the *quoted source
field* it was verified against.

| # | Step | Notes for this disease set |
|---|---|---|
| 2.1 | Resolve every **PMID** against PubMed (E-utilities) and every **NCT** against ClinicalTrials.gov API v2 | Many global-health trials are registered on **PACTR** (Pan African Clinical Trials Registry), **ISRCTN**, **CTRI** (India), **ChiCTR**, or the **WHO ICTRP** — *not* on ClinicalTrials.gov. A missing NCT is **N/A, not a failure** (see §4.G6) |
| 2.2 | Confirm **denominators** against the source | |
| 2.3 | Confirm **per-arm event counts** against the source | |
| 2.4 | Where only percentages are published, back-compute the integer pair and require agreement to **<0.1 pp**; record both integers and the published percentage | HFrEF accepted 12 back-computations at <0.06 pp. SPICE's 6/179 (3.35%→3.4%) and 3/91 (3.30%→3.3%) were the *only* integer pairs consistent with both published percentages — that uniqueness is what makes the back-computation admissible |
| 2.5 | Assign a tier: `VERIFIED_FULL` · `VERIFIED_DENOM_ONLY` · `SECONDARY_CORROBORATED` · `UNSOURCED` | `VERIFIED_DENOM_ONLY` is the honest limit of abstract-level work and must be **counted on the badge**, not hidden |
| 2.6 | **Search on more than the acronym.** If a trial's source is "not found", re-search on first author + year + design + N + journal before concluding it does not exist | This is the SPICE lesson. It cost the network its only between-trial loop in the first draft |
| 2.7 | If the paywall/bot-check is not circumvented, say so and drop the tier — do **not** claim a read you did not perform | |

### 2.8 Disease-specific verification traps in this corpus

- **Outcome substitution.** The abstract commonly reports a *different quantity* than the
  ledger extracts. In HFrEF it was primary-composite vs all-cause death. Here expect:
  **efficacy against any-severity disease vs severe disease** (malaria and dengue
  vaccines), **sputum-culture conversion vs relapse-free cure** (TB), **viral suppression
  at wk 48 vs wk 96, ITT vs per-protocol vs snapshot** (HIV ART), **incidence per
  person-year vs cumulative incidence** (PrEP, LF/oncho MDA). Confirm the *quantity*, not
  just the numbers.
- **Person-time denominators.** Malaria, TB-prevention, PrEP and MDA trials report
  events per person-year. A 2×2 built from person-time is **not** a 2×2 — the plausibility
  gate and the fragility index behave differently (§4.G1, §4.G7).
- **Cluster randomisation.** MDA (azithromycin child mortality, ivermectin LF,
  praziquantel), most WASH/diarrhoea and many vaccine-effectiveness trials are
  **cluster-randomised**. The design effect **reduces** N_eff (N/DEFF). An extraction that
  used raw individual counts has an over-precise SE. Flag, quantify, do not silently pool.
- **Non-inferiority designs.** Most first-line ART and shortened-TB-regimen trials are
  non-inferiority. A pooled superiority estimate from NI trials is a claim the sources do
  not make; the margin must be carried.
- **Multi-dose / schedule arms.** HPV dose reduction, malaria vaccine fractional dosing,
  rotavirus schedules. Pooling dose arms onto one node repeats the He-2015 situation:
  admissible only if the arms are non-significantly different **on the outcome actually
  pooled**, and the test must be reported (He 2015: Fisher p = 0.49 on all-cause death,
  even though the arms differed at P=0.042 on the composite).

---

## 3. Triangulate — four independent lanes

The point is not corroboration for its own sake; it is that each lane fails differently.
Record each lane's verdict separately; **never collapse them into one "verified".**

| Lane | Source | What it uniquely catches | Global-health notes |
|---|---|---|---|
| **L1 Registry** | ClinicalTrials.gov API v2; **PACTR / ISRCTN / CTRI / ChiCTR / EudraCT / WHO ICTRP** where CT.gov has no record | Wrong N, wrong arms, outcome switching, wrong population | AACT snapshot ≠ live API — say which was used |
| **L2 Regulator** | FDA (Drugs@FDA, review packages), EMA (EPAR), **WHO Prequalification** dossiers, **WHO SAGE** background papers, **AVAREF**/NMRA where available | Counts the publication never printed; per-arm safety; the sponsor's own primary analysis | For this corpus, WHO PQ + SAGE is often the **only** regulatory lane (RTS,S/R21, TCV, rotavirus, PCV, MenAfriVac). Treat WHO PQ as first-class, not a fallback |
| **L3 Prior synthesis** | Cochrane, prior published MAs/NMAs, **WHO guideline evidence-to-decision tables**, GRADE profiles | Whether *this* app's k, inclusion set and pooled estimate are discordant with an existing verified synthesis | A discordance is a finding either way — it may be the prior MA that is wrong |
| **L4 Open access** | PMC, medRxiv/bioRxiv, publisher OA | Full text for the `DENOM_ONLY` residue | **Highest yield in this corpus** — global-health trials are disproportionately OA (Wellcome/Gates/NIH mandates). Run L4 *before* declaring a full-text gap |

> **Triangulation gate:** if two lanes disagree on a count, that is a **finding**, not a
> tie to be broken by preference. Record both, state which is primary, and disposition it.

---

## 4. Integrity gates — `RM-H01`–`RM-H06` `RM-J04`

Run them; publish which ones **do not apply and why**. "Not applicable" is a result and
must be printed as `N/A`, never as `passed` — the HFrEF badge's core honesty move.

| Gate | Applies when | Fails when |
|---|---|---|
| **G1 per-arm count plausibility** | binary per-arm counts exist | non-integer, `e<0`, `e>N`, arm rows disagree with the trial totals or with the fitted contrasts |
| **G1b contrast recompute** | always | `logRR`/`seLogRR` does not recompute from the arm ledger to **<1e-8** |
| **G2 GRIM / GRIMMER** | a **mean of a bounded integer scale** is reported | reported mean not reconstructible as `X/N`. **N/A for pure binary outcomes** — HFrEF printed this as N/A and replaced it with G1. Relevant *here* for: MUAC / weight-for-height z-scores (SAM), CD4 counts, haemoglobin, adherence %, symptom scores |
| **G3 Benford first-digit** | ≥ ~30 count/denominator digits | advisory only; χ² on 8 df |
| **G4 arm-balance ratio** | randomised arms | advisory; a ratio far from the stated allocation. Explain before flagging (HFrEF: both advisories were explained by design, neither was an error) |
| **G5 identifier format** | always | malformed or missing PMID/DOI/registry ID |
| **G6 registry concordance** | **only** for trials with a registry record | N vs registry, arms vs registry, outcome vs registry. **Report the covered fraction explicitly** ("covers 9 of 28") and state that the remainder is **N/A — no record to concord with**, not passed. Expect a *low* covered fraction here: pre-2005 trials, and African/Asian trials registered on PACTR/CTRI/ChiCTR |
| **G7 Fragility Index** (Walsh 2014) | a **significant, direct, observed 2×2** | FI below threshold. **UNDEFINED for indirect contrasts** (no 2×2 exists) and for **person-time / cluster** outcomes. HFrEF: 11 of 12 CI-excludes-1 contrasts were purely indirect → FI undefined, *not favourable*. **Never quote an FI for an indirect estimate** |
| **G8 cross-meta / clone contamination** | always | `python scripts/clone_contamination_gate.py <FILE>` — must be clean for the app under upgrade regardless of the corpus baseline |
| **G9 self-contradiction** | always | any count in the visible badge that disagrees with the post-upgrade figure. **This gate exists because the first HFrEF draft shipped a badge asserting 28 and 27 trials simultaneously** |
| **G10 anchor gate** | any re-fit | the pre-change re-fit must reproduce the settled primary to **<1e-8** on the anchor nodes and τ² *before* the changed fit is emitted. If it does not, the pipeline is wrong, not the data |

---

## 5. Honest verdict — replace the badge **wholesale** — `RM-F01` `RM-F02` `RM-F03` `RM-F04` `RM-F07` `RM-H04`

The false-green pattern this programme exists to kill: a green
`#15803d` `INTERNAL CHECKS PASSED` banner sitting above an app whose own
`window.__verdict` records open findings, or whose every trial is missing evidence rows.

| # | Step |
|---|---|
| 5.1 | **Grep BOTH surfaces.** `window.__verdict` (machine JSON: `verdict`, `p0_total`, `P1_*`, `n_trials_seen`) **and** `<div id="rapidmeta-integrity-badge">` (visible: headline text, background colour, `Fabrication-risk score`, `Trials: <strong>N</strong>`) |
| 5.2 | **Replace the badge wholesale** by balanced-`<div>` matching. Do **not** patch the headline and append a new body — that is exactly how the stale "Trials: 28" survived |
| 5.3 | The badge must state, in numbers: trials in fit · quarantined · arithmetic-gate findings · source-verification tier counts · provenance findings raised/dispositioned/**open** · **counts changed** |
| 5.4 | Print every **N/A** gate as N/A with its reason |
| 5.5 | Print the **indirect-evidence warning** verbatim where it applies: *"N of M contrasts whose CI excludes 1 are purely indirect; the fragility index is undefined for them — not favourable."* |
| 5.6 | Carry the **source's own analysis** where it disagrees with the crude recomputation (QUEST: HR 0.84, 0.70–1.01, P=0.058 — and no contrast presented as significant on the crude 2×2) |
| 5.7 | Carry the **AMSTAR-2 confidence** rating |
| 5.8 | **Running the gates does not earn a PASS.** It converts "untested" into "tested, k findings open". The verdict only improves when the findings are dispositioned — and even then HFrEF stayed `UNCERTAIN` |
| 5.9 | Reconcile the two surfaces and add the **G9 self-contradiction** check to the app's verifier |

---

## 6. Transparency ledger

`outputs/<APP>_ledger.json` + a rendered in-app section. Per trial:

`trial · registry ID (+ which registry) · PMID/DOI · arm rows as extracted ·
verification tier · quoted source field · lane(s) that confirmed it · quarantine status
+ named violation + reinstatement condition · any pooling/dropping decision and the test
that justifies it`

Plus, app-level: the **k-ledger** (trials settled → quarantined → fitted; arm rows;
contrasts), the **before → after anchor table** with Δ%, the **structural consequence**
(nodes/edges/loops/ICDF) for networks, and an explicit **"still not done"** list.

> The ledger is the deliverable a resource-limited-setting reader can actually act on:
> it tells them which numbers they may cite, which they must re-check, and where the
> full text is missing.

---

## 7. Verify the app, then gate it

| # | Check | Tool |
|---|---|---|
| 7.1 | Structure: div balance, no literal `</script>` in a script body, every `data-tab` has a panel, no placeholder tokens | per-app verifier (pattern: `scripts/hfref_verify_app_quarantine.py`) |
| 7.2 | Payload matches the re-fit **row for row at 1e-8** | same |
| 7.3 | **Verdict-surface agreement** (§5.9) | same |
| 7.4 | Quarantine integrity — flagged, not deleted; every named violation present | same |
| 7.5 | **Negative-test the verifier**: perturb a pooled estimate by 1e-6, change the badge trial count by 1, delete the quarantined trial. **All three must FAIL.** A gate that cannot fail is verification theatre | same |
| 7.6 | JS parse | `scripts/jscheck.py` |
| 7.7 | Clone/cross-meta contamination | `scripts/clone_contamination_gate.py` |
| 7.8 | **Live render** — serve over HTTP, drive in-browser: every tab activates, 0 console errors, one data source, and **no stale value anywhere in rendered text** | headless browser |
| 7.9 | **Cross-family gate** — an independent model family (not Claude) re-checks the new integrity claims before push | flag for it; do not self-certify |
| 7.10 | Commit on the branch. **Do not push** until 7.9 clears and Mahmood says go | |

---

## 8. Residual-contamination sweep (this corpus specifically) — `RM-E01` `RM-E02`

Several of these apps were in the 148-clone SGLT2i adverse-event contamination fixed in
`d11d9f167`. Per app, confirm zero surviving hits for: `SGLT2` / `SGLT-2` /
`dapagliflozin` / `empagliflozin`; `Fournier` / `genital mycotic` / `diabetic
ketoacidosis`; `DAPA-HF` / `EMPEROR-*` / `DELIVER` / `EMPA-REG`; `finerenone` / `FIDELIO`
/ `FIGARO` (excluding the legitimate `rapidmeta-finerenone` repo/asset URL); and the
`SGLT2-HF` report title / data-seal `app:` field. A hit in a **claim-bearing slot**
(safety-outcome definition, i18n value, data seal, export title) is P0.

---

## 9. Definition of done, per app

- [ ] Every trial has a verification tier backed by a quoted source field
- [ ] Every lane recorded separately; disagreements raised as findings
- [ ] Every gate run, or printed `N/A` **with its reason**
- [ ] Zero unsourced counts in the fit (quarantined, flagged, reinstatement condition stated)
- [ ] Both verdict surfaces state the same numbers; badge replaced wholesale
- [ ] Indirect-evidence warning present where applicable; no FI quoted for an indirect contrast
- [ ] Transparency ledger written and rendered
- [ ] Verifier passes **and has been negative-tested to fail**
- [ ] Contamination gate clean
- [ ] Live render clean, no stale values
- [ ] "Still not done" list written
- [ ] **Every STATIC registry detector run on the FINAL file, and every firing dispositioned by id** (§R)
- [ ] **Every base-engine-shared type routed to a guard in ssets/js/rapidmeta-guards.js, not patched per app** (§R.3)
- [ ] **git diff --numstat line count proportional to the edit, not the file** (RM-J06)
- [ ] Flagged for cross-family gate · **staged, committed, not pushed**
