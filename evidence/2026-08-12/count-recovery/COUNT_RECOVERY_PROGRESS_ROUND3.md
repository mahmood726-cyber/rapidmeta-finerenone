# Count recovery — round 3

**Date:** 2026-08-12 · **Harness:** v1.1.0, **17 checks**, 23 controls (20 must-block, 3 must-not-block), all passing · **Corpus read-only.**

---

## 1. Headline — the empirical check found something, and it is the thing you predicted

You asked whether determined reconstruction always reproduces the read value, and flagged rounding in published percentages as where a determined-*looking* reconstruction can drift. It does drift, and the drift is measurable.

Tier T3 gave a calibration set nothing else could: the FDA review for NDA 207620 prints PARADIGM-HF's true counts **and** their percentages side by side. Reconstructing each count by percentage × denominator:

| quantity | true | reconstructed | error | integers the rounding interval admits |
|---|---|---|---|---|
| composite, LCZ696 | 914 | 913 | −1 | 911–914 (4) |
| composite, enalapril | 1117 | 1116 | −1 | 1115–1118 (4) |
| all-cause death, LCZ696 | 711 | 712 | **+1** | 710–713 (4) |
| all-cause death, enalapril | 835 | 834 | −1 | 832–836 (5) |
| CV death (total), LCZ696 | 558 | 557 | −1 | 555–558 (4) |
| CV death (total), enalapril | 693 | 695 | **+2** | 693–697 (5) |
| HF hosp (total), LCZ696 | 537 | 536 | −1 | 534–538 (5) |
| HF hosp (total), enalapril | 658 | 657 | −1 | 655–659 (5) |
| CV death (first event), LCZ696 | 377 | 377 | 0 | 375–378 (4) |
| CV death (first event), enalapril | 459 | 459 | 0 | 458–461 (4) |

**Wrong in 8 of 10, once by two events. The rounding interval admitted four or five candidate integers in 10 of 10 — never one.**

This does not overturn your ruling; it sharpens the line you drew. Percentage × denominator was already on the forbidden side, and this is why: at one printed decimal against a denominator in the thousands, the percentage pins an *interval*, not a count. The two that happened to land exactly did so by luck of the denominator, not by determinacy.

The operative consequence: **determinacy has to be tested per cell, not inferred from the presence of a percentage and an n.** `determinacy_test.py` does that — a reconstruction is determined only if the reported statistic's rounding interval admits exactly one integer.

---

## 2. Your two questions, answered

### Q1 — determined versus underdetermined

Two conditions must both hold, and testing only one overstates the answer badly:

- **(a)** both group sizes are reported in the source, and
- **(b)** the reported statistic's rounding interval admits exactly one integer.

| | rows |
|---|---|
| Back-computed rows in the corpus | 26 |
| (a) group sizes reported | 4 |
| (b) interval pins a unique integer | 11 |
| **(a) AND (b) — determined, may proceed** | **2** |
| **Required an assumption — stays forbidden** | **24** |

The two that qualify are **Akingba 2021** and **Andama 2021**. The gap between 11 and 2 is the set of rows whose cells look pinned only because a group size was itself imputed — Palmqvist 2020 reports N=301 and nothing else, so its 138/163 split is an imputation and the "pinned" TP is pinned to a number nobody reported. **Pinned to an imputation is not determined.**

A third axis emerged from the corpus's own `data_caveats` strings and is worth separating: **9 of 26 rows carry a construct flag** — management-strategy endpoints counted as diagnostic accuracy (YEARS, RAPID-TnT), operating points derived from AUC and Youden rather than a reported cutoff (Mielke 2021), prevalence borrowed from a different cohort (PI-CAI). An exactly determined 2×2 of the wrong quantity is still the wrong quantity, and that problem is untouched by the ruling.

### Q2 — does back-computation disagree with reported counts?

**Yes, and the mechanism is exactly rounding.** See section 1.

I should be straight about one thing: my first attempt at this was circular. Rebuilding each cell with the same arithmetic the original extractor used, from the same quote, guarantees agreement and proves nothing. It rules out transcription slips and nothing more. The FDA calibration set is what made a real test possible, because it is the only place the true integers and the percentages appear together.

One non-circular observation stands: ten back-computed rows state at least one of their four cells verbatim in the stored quote, and in every case the stored value equals the stated value. Where a real count was on the page, the extractor used it. That is reassuring about intent; it says nothing about the cells that were not on the page.

---

## 3. The ruling, implemented and proved in both directions

`CHK016` no longer blocks determined reconstruction. `CHK017` is new and enforces the condition you attached to the permission.

| construction | status |
|---|---|
| `read` | permitted |
| `derived_determined` | **permitted** — requires `derivation_inputs`, `derivation_formula`, and a source pointer per input; `CHK017` re-executes the arithmetic and blocks if it does not reproduce |
| `derived_underdetermined` | blocked |
| `summed_components` (total-basis) | blocked |
| `percent_times_denominator` | blocked |

Controls, same bar as everything else — **three of them assert the harness must NOT block**, which is the direction that matters for a relaxation:

- determined derivation with inputs + formula that reproduces → **must not block** (CHK016) ✓
- determined derivation with inputs + formula that reproduces → **must not block** (CHK017) ✓
- determined derivation with no inputs recorded → blocked ✓
- determined derivation whose arithmetic does not reproduce → blocked ✓
- underdetermined reconstruction → blocked ✓
- percentage × denominator → blocked ✓

Re-running the diagnostic-accuracy set under the new rule: **48 blocks (was 53)**. The four cells belonging to Akingba and Andama now pass, carrying their inputs and formula; the 48 underdetermined cells stay blocked.

---

## 4. A harness check that was wrong, and the evidence that corrected it

`CHK007` v1.0 asserted flatly that a composite must never equal the sum of its components. That rule **would have blocked a correct extraction**, and the FDA review is what exposed it. NDA 207620 Table 2 prints both decompositions of the same composite:

| basis | CV death | HF hosp | composite |
|---|---|---|---|
| **First event**, LCZ696 | 377 | 537 | **914 = 377 + 537** |
| **First event**, enalapril | 459 | 658 | **1117 = 459 + 658** |
| Total events, LCZ696 | 558 | 537 | 914 ≠ 1095 |
| Total events, enalapril | 693 | 658 | 1117 ≠ 1351 |

First-event components sum to the composite *exactly*, by construction. Total-event components cannot, because a participant may appear in both. The relationship is **opposite in the two cases**, so the check now requires `component_basis` to be declared before it will judge, and enforces equality for `first_event` and strict inequality for `total`. Four controls cover both directions plus the mixed-basis case.

This is also the first genuinely new *data* tier T3 has produced: the first-event decomposition appears in neither the publication nor the registry.

---

## 5. Tier T3 — validated, and its limits mapped

The pointer pattern the sibling lane found works and generalises:

```
https://www.accessdata.fda.gov/drugsatfda_docs/nda/<year>/<app>Orig1s000TOC.html   ← .html, not .cfm
  → …Orig1s000StatR.pdf   (statistical)
  → …Orig1s000SumR.pdf    (summary — start here)
  → …Orig1s000MedR.pdf    (clinical)
```

Three practical findings now in the procedure so nobody rediscovers them:

- **`web_fetch` reads these PDFs and returns extracted text.** `timeout_ms` is capped at 30 000 and the 1.7 MB `StatR.pdf` timed out; the much smaller `SumR.pdf` succeeded and carries the pivotal efficacy tables. **Start with SumR.**
- **The interactive PDF viewer does not work in a non-interactive session** — the iframe never mounts and the viewUUID expires after 8 s. Do not route through it.
- **PubMed's web interface served a reCAPTCHA** to the browser. Not bypassed; the PubMed MCP tool was used instead.

Coverage limit: T3 only helps where a trial supported a registration. Of the 15 open rows, roughly half have an associated NDA/BLA (FOURIER, CREDENCE, EMPEROR-Reduced, SUSTAIN-6, EMPA-REG, VERTIS-CV, CANVAS, SOLOIST-WHF). TWILIGHT, GLOBAL LEADERS, ADVANCE and VADT are investigator-led with no US application, and need the CSR or an EMA submission instead.

---

## 6. NEJM tier order — now procedure, not folklore

**For an NEJM trial, go to the registry results module or the regulatory layer first. Do not fight the article.**

NEJM renders outcome tables outside the DOM — `querySelectorAll('table').length` is 0, the Table 2 anchors are fragments that never populate, and clicking the Tables tab does nothing. The Results prose yields counts only where the authors wrote them out: it worked for ODYSSEY OUTCOMES, HEART-FID and TWILIGHT's composite, and failed for FOURIER, CREDENCE and EMPEROR-Reduced. A per-publisher tier table is now in the procedure doc.

---

## 7. TWILIGHT — written up for the build lane

`DEFECT_TWILIGHT_composite_as_mortality.md`, standalone and actionable.

The row at `classes[20].trials[0]` stores **hr 0.99, lo 0.78, hi 1.25** — an exact three-number match for TWILIGHT's *key secondary composite of death from any cause, nonfatal MI, or nonfatal stroke* (135/3524 vs 137/3515, per-protocol), read from the publication. In a mortality atlas. The stored denominators (3555/3564, randomised) are also wrong for that hazard ratio, which belongs to the per-protocol population.

`classes[20].pool` (k=2) pools this with GLOBAL LEADERS as though both were mortality. **That pooled estimate is invalid**, and with k=2 it does not survive removing either input.

The note asks for the handling you specified: **flag, do not quietly correct.** Mark the pool invalid and suppress its display with a visible reason; annotate the row as defective while retaining the incorrect values; record when and where the wrong pooled estimate was displayed; substitute a correct value only once one exists. A wrong number that has been shown to readers is a defect with a history, not a value to overwrite.

The correct value is not yet available and must not be improvised — the note spells out why the registry adverse-events figure (34/45) and any percentage-based reconstruction are both inadmissible.

---

## 8. Rate

**Unchanged this round: 48 of 63 atlas rows, 76.2%.** Round 3 added no new atlas rows.

That is the honest number. T3 produced new PARADIGM-HF data — the first-event decomposition — but that is a different outcome, not an atlas gap, and it would be misleading to book it as progress against the mortality denominator. What round 3 bought instead: the ruling implemented and proved, the determinacy question answered with evidence, a wrong harness check found and corrected, T3 validated with its limits mapped, and TWILIGHT documented.

Fifteen rows remain open, each with a named obstacle. Round 4 should work the eight with an associated FDA application, in descending pool weight, using the SumR-first recipe.

---

## 9. Files

`C:\Users\mahmo\AppData\Roaming\Claude\local-agent-mode-sessions\bdc5772c-ca03-473f-9464-80d37a7559d2\44788c9b-d162-4f2e-b3c2-d89031e65ab6\local_95f555f3-c719-446f-9f1a-d5253bed5c4e\outputs\`

| File | What it is |
|---|---|
| `rapidmeta_count_harness.py` | v1.1.0 — 17 checks, 23 controls, stdlib only |
| `determinacy_test.py` → `determinacy_test_report.txt` | The rounding-interval test and the FDA calibration set |
| `audit_dta_backcomputation.py` → `dta_backcomputation_audit.txt` | Determinacy, construct flags, and the circularity caveat |
| `DEFECT_TWILIGHT_composite_as_mortality.md` | Standalone defect note for the build lane |
| `DEFECT_LEDGER_cardiology_mortality_atlas.md` | The three atlas defects at exact JSON paths |
| `COUNT_RECOVERY_PROCEDURE.md` | Ruling, tier order by publisher, T3 recipe, cell schema |
| `build_cardio_extraction.py` → `cardio_acm_extraction.json` | 70 cells, **0 blocks** |
| `adapt_dta_to_cells.py` → `dta_extraction.json` | 68 cells, 48 blocks (all underdetermined) |
| `COUNT_RECOVERY_PROGRESS_ROUND2.md`, `CARDIO_COUNT_RECOVERY_PROGRESS.md`, `ARNI_HFrEF_per_arm_event_counts_extraction.md` | Earlier rounds |

*Nothing renamed. New artefacts named neutrally.*

---

## Sources

- FDA, NDA 207620 (Entresto) Summary Review, 2015 — [TOC](https://www.accessdata.fda.gov/drugsatfda_docs/nda/2015/207620Orig1s000TOC.html) · [SumR](https://www.accessdata.fda.gov/drugsatfda_docs/nda/2015/207620Orig1s000SumR.pdf)
- Mehran R et al. Ticagrelor with or without Aspirin in High-Risk Patients after PCI. *N Engl J Med* 2019. [Article](https://www.nejm.org/doi/full/10.1056/NEJMoa1908419)
- McMurray JJV et al. *N Engl J Med* 2014;371:993-1004. [DOI](https://doi.org/10.1056/NEJMoa1409077)
- ClinicalTrials.gov: [NCT01035255](https://clinicaltrials.gov/study/NCT01035255?tab=results) · [NCT02270242](https://clinicaltrials.gov/study/NCT02270242?tab=results)
- Corpus (read-only): `cardiology_mortality_atlas.json` and the six `*_trials.json` diagnostic-accuracy datasets.
