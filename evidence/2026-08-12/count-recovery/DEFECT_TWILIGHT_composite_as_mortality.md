# DEFECT — TWILIGHT: a composite endpoint stored as all-cause mortality

**Severity:** invalidates a displayed pooled estimate
**Object:** `F:\rapidmeta-finerenone\cardiology_mortality_atlas.json`
**Path:** `classes[20]` (`"P2Y12 mono"`, population `"Post-PCI (selected)"`) → `trials[0]`
**Owner:** build lane (single writer). This lane wrote nothing.
**Raised:** 2026-08-12, count-recovery lane

---

## 1. The row as it stands

```json
{"hr": 0.99, "lo": 0.78, "hi": 1.25, "tE": null, "cE": null,
 "nct": "NCT02270242", "name": "TWILIGHT", "year": 2019, "rob": "low",
 "primary_hr": 0.56, "tN": 3555, "cN": 3564}
```

It sits in an atlas whose stated quantity is all-cause mortality, and it is pooled with one other trial in `classes[20].pool` (k=2).

## 2. What the hazard ratio actually measures

Read at source — Mehran R et al., *Ticagrelor with or without Aspirin in High-Risk Patients after PCI*, N Engl J Med 2019, NCT02270242, https://www.nejm.org/doi/full/10.1056/NEJMoa1908419, Results:

> The key secondary composite end point of **death from any cause, nonfatal myocardial infarction, or nonfatal stroke** occurred in **135 patients (3.9%)** who received ticagrelor plus placebo and in **137 patients (3.9%)** who received ticagrelor plus aspirin (**hazard ratio, 0.99; 95% CI, 0.78 to 1.25**) …

and, on the analysis population:

> … analyzed in the **per-protocol population, which included the 7039 patients** who underwent randomization and had no major deviations from the protocol (**3524** who received ticagrelor plus placebo and **3515** who received ticagrelor plus aspirin).

**hr 0.99, lo 0.78, hi 1.25** matches that composite exactly, on all three numbers, to the precision printed. The stored value is a composite of death, myocardial infarction and stroke.

Two further mismatches follow from the same misidentification:

| | stored in the row | correct for that hazard ratio |
|---|---|---|
| population | randomised, 3555 / 3564 | **per-protocol, 3524 / 3515** |
| quantity | all-cause mortality | **death or non-fatal MI or non-fatal stroke** |

## 3. Why it survived review

The row is **internally consistent**. Nothing in it contradicts anything else in it, and any check that validates a row by reproducing its own effect estimate passes it. This is the second confirmed instance of that failure mode in this atlas — see also GLOBAL LEADERS in the main ledger, where an implied risk ratio of 0.937 sits against a stored 0.93 while the event counts match neither the registry nor the publication.

The lesson is already encoded as `CHK014_CAVEAT` in the harness and prints on every report containing a consistency finding: **agreement authenticates nothing; only disagreement is informative.**

## 4. Consequences — the pool, not just the value

`classes[20].pool` (k=2) currently pools this composite hazard ratio with GLOBAL LEADERS as though both were mortality estimates. **That pooled estimate is invalid.** It is not merely imprecise; one of its two inputs measures a different quantity, and the other (per the main ledger) has unresolved denominator and event-count defects of its own. With k=2 there is no scenario in which the pool survives the removal of one input.

## 5. What is being asked for — flag, do not quietly correct

The pooled estimate has been **displayed**. A wrong number that has been shown to readers is a defect with a history, not a value to overwrite. Correcting the row silently would leave no trace that anything was ever wrong, and anyone who saw or cited the earlier figure would have no way to learn otherwise.

Requested handling, in order:

1. **Mark `classes[20].pool` invalid** and suppress its display, with a visible reason, rather than recomputing it in place.
2. **Annotate `classes[20].trials[0]`** as defective, retaining the incorrect values with a note recording what they actually were. Do not delete them.
3. **Record the display history** — when the pooled estimate first appeared and through which artefacts — so the exposure is known.
4. **Only then** substitute the correct value, if and when it is recovered.

## 6. The correct value is not yet available

TWILIGHT's all-cause mortality has **not** been recovered, and must not be improvised:

- The **publication** reports it in a table that NEJM renders outside the DOM; the Results prose gives only the composite quoted above.
- The **registry results module** (NCT02270242) posts no death-titled outcome measure at all.
- The **registry adverse-events module** gives 34 / 3524 versus 45 / 3515 at one year, safety population. **This is not the efficacy endpoint and must not be substituted** — see `CHK013` in the harness, where the same substitution is out by more than a factor of two in EMPA-KIDNEY and by roughly a hundred events per arm in ODYSSEY OUTCOMES.
- Do **not** reconstruct it from a percentage. Percentage-times-denominator was tested this round against ten PARADIGM-HF quantities whose true counts are known from the FDA review: it was wrong in eight, once by two events, and the rounding interval admitted four or five candidate integers every time.

**Next avenue:** tier T3. TWILIGHT supported no US registration of its own, so Drugs@FDA is unlikely to help; the more promising route is the AstraZeneca clinical study report or an EMA submission referencing the trial.

---

## Reproduction

```bash
python rapidmeta_count_harness.py cardio_acm_extraction.json --report r.md
```

The TWILIGHT cells carry `not_recovered_reason` describing precisely this situation, so the row is visible as unrecovered rather than as absent.

**Sources:** Mehran R et al., N Engl J Med 2019 ([article](https://www.nejm.org/doi/full/10.1056/NEJMoa1908419)) · [NCT02270242 results](https://clinicaltrials.gov/study/NCT02270242?tab=results) · `cardiology_mortality_atlas.json` (read-only).
