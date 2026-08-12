# Defect ledger — `cardiology_mortality_atlas.json`

**Target object:** `F:\rapidmeta-finerenone\cardiology_mortality_atlas.json` (generated 2026-06-02; 30 classes, 63 trial rows)
**Raised by:** count-recovery lane, 2026-08-12 · **Owner needed:** build lane (single writer on the repo)
**Nothing in this file was written by me.** Every path below is given so the fix can be applied at the object without re-deriving the investigation.

Each defect states: where it is, what is wrong, what the registry actually says, how it was found, and what still has to be decided by a human.

---

## DEFECT-01 — TWILIGHT carries two irreconcilable denominator pairs, and one of them exceeds the trial's randomised total

**Location A** — `classes[20]` (`"P2Y12 mono"`) → `trials[0]`
```json
{"nct":"NCT02270242","name":"TWILIGHT","hr":0.99,"lo":0.78,"hi":1.25,
 "tE":null,"cE":null,"tN":3555,"cN":3564}
```

**Location B** — `classes[24]` (`"Ticagrelor mono"`) → `trials[0]`
```json
{"nct":"NCT02270242","name":"TWILIGHT","hr":0.99,"lo":0.80,"hi":1.23,
 "tE":172,"cE":168,"tN":4614,"cN":4603}
```

### What the registry says
ClinicalTrials.gov NCT02270242, participant-flow module, `STARTED`: **3555 / 3564 = 7119 randomised**. Adverse-events module, time frame "1 year": **34 deaths / 3524 at risk (placebo + ticagrelor)** and **45 / 3515 (aspirin + ticagrelor)** — 79 deaths in total.

### The arithmetic
| | Location A | Location B | Registry |
|---|---|---|---|
| Sum of denominators | 7119 | **9217** | 7119 |
| Deaths recorded | — | 340 (172 + 168) | 79 (AE module, 1 y) |

Location B's denominators exceed the registered randomised total by **2098**, and its death count is **4.3× the registry's**. TWILIGHT was a 12-month trial, so 340 deaths in 7119 patients is not plausible on its face. Location A matches the registry exactly.

### How this was found
Two rows for the same NCT surfaced during the atlas sweep; the denominators were then compared against the registry participant flow retrieved via the ClinicalTrials.gov results API.

### Note on why this survived
Location B is **internally consistent**: 172/4614 vs 168/4603 gives RR 0.995 against the stored HR of 0.99. Any check that validates a row by reproducing its own effect estimate passes it. Consistency does not authenticate a row.

### ESCALATION — Location A is not a mortality endpoint at all

Read at source after the above was written. TWILIGHT primary publication (Mehran R et al., *N Engl J Med* 2019, NCT02270242, https://www.nejm.org/doi/full/10.1056/NEJMoa1908419), Results:

> The key secondary composite end point of **death from any cause, nonfatal myocardial infarction, or nonfatal stroke** occurred in **135 patients (3.9%)** who received ticagrelor plus placebo and in **137 patients (3.9%)** who received ticagrelor plus aspirin (**hazard ratio, 0.99; 95% CI, 0.78 to 1.25**) … analyzed in the per-protocol population, which included the 7039 patients who underwent randomization and had no major deviations from the protocol (**3524** ticagrelor plus placebo, **3515** ticagrelor plus aspirin).

`classes[20].trials[0]` carries **hr 0.99, lo 0.78, hi 1.25** — an exact match, to three decimal places on all three numbers, for the **composite** endpoint. This is a mortality atlas. The row is a composite of death, MI and stroke masquerading as all-cause mortality.

This reclassifies DEFECT-01 from a denominator problem to an **outcome-substitution problem**, which is more serious: the value is not merely attached to the wrong denominator, it is measuring the wrong thing, and it is currently pooled with genuine mortality estimates in `classes[20].pool` (k=2).

Note also that the correct denominators for that HR are the **per-protocol** 3524 / 3515, not the randomised 3555 / 3564 recorded in the row.

### Decision required (do not guess)
1. **`classes[20].trials[0]` must be removed from the mortality pool** or replaced with TWILIGHT's actual all-cause mortality. The `classes[20].pool` object (k=2) is invalid until this is resolved.
2. TWILIGHT's true all-cause mortality has **not** been recovered. The publication reports it in a paywalled table; the registry's adverse-events module gives 34 / 3524 vs 45 / 3515 at 1 year (safety population) but that is not the efficacy endpoint — see `CHK013` in the harness. **Do not substitute it.**
3. Whose numbers are 172/168 on 4614/4603 in `classes[24].trials[0]`? They match neither the registry nor the composite above. Trace before use. **Do not simply copy Location A's denominators into Location B** — that would keep an unexplained event count attached to a corrected denominator, which is worse than the present state.

---

## DEFECT-02 — GLOBAL LEADERS carries two different control-arm denominators and an event count matching neither the registry nor the publication

**Location A** — `classes[20]` (`"P2Y12 mono"`) → `trials[1]`
```json
{"nct":"NCT01813435","name":"GLOBAL LEADERS","hr":0.87,"lo":0.75,"hi":1.01,
 "tE":null,"cE":null,"tN":7980,"cN":8011}
```

**Location B** — `classes[24]` (`"Ticagrelor mono"`) → `trials[2]`
```json
{"nct":"NCT01813435","name":"GLOBAL LEADERS","hr":0.93,"lo":0.83,"hi":1.05,
 "tE":461,"cE":493,"tN":7980,"cN":7988}
```

### What the registry says
ClinicalTrials.gov NCT01813435, adverse-events module, time frame "monitored for 2 years":
- Experimental treatment strategy: **224 deaths / 7980 at risk**
- Reference treatment strategy: **253 deaths / 7988 at risk**

### The problems, in order of seriousness
1. **Two control-arm denominators for one trial.** `cN` is 8011 in Location A and 7988 in Location B. Both cannot be right for the same trial and the same outcome. 7988 matches the registry's adverse-events `deathsNumAtRisk`; 8011 does not appear in the registry results module at all.
2. **The event count matches nothing.** Location B's 461 / 493 is roughly **twice** the registry's 224 / 253. It is also not the published primary endpoint (all-cause death or new Q-wave MI). Its origin is unknown.
3. **Two different hazard ratios** for the same trial and the same outcome concept: 0.87 (0.75–1.01) and 0.93 (0.83–1.05).

### Note on why this survived
Again internally consistent: 461/7980 vs 493/7988 gives RR 0.937 against the stored 0.93. The row validates against itself.

### Decision required
Establish which outcome each row is actually measuring — the two hazard ratios suggest they are not the same endpoint, in which case the defect is a labelling error rather than a data error, and both rows need their `outcome` field populated. The atlas has an `outcome` field on some rows (see `classes[29]`) and not on these; **populating `outcome` on every row would prevent this class of defect entirely.**

---

## DEFECT-03 — "CANVAS Program" points at an NCT that is CANVAS alone

**Location** — `classes[29]` (`"SGLT2 CVOT (T2D)"`) → `trials[2]`
```json
{"nct":"NCT01032629","name":"CANVAS Program","year":2017,"rob":"low",
 "hr":0.87,"lo":0.74,"hi":1.01,"source":"ctgov_analyses",
 "outcome":"All-cause mortality (Neal NEJM 2017)"}
```

### What the registry says — verified by lookup, not recall
| NCT | Acronym | Registered enrolment | Official title (truncated) |
|---|---|---|---|
| **NCT01032629** | **CANVAS** | **4330** | "…Effects of JNJ-28431754 on Cardiovascular Outcomes…" |
| **NCT01989754** | **CANVAS-R** | **5813** | "…Effects of Canagliflozin on Renal Endpoints in Adults with Type 2 Diabetes…" |

The CANVAS **Program** is the pooled CANVAS + CANVAS-R entity (4330 + 5813 = **10 143** registered). The row's `outcome` field correctly names the pooled publication (Neal, NEJM 2017), but its `nct` points at the 4330-patient sub-trial.

### Consequence
Any extraction lane that resolves this row by its NCT — which is exactly what the count-recovery procedure instructs — will retrieve CANVAS-only participant flow (registry `STARTED`: 1442 / 1445 / 1443) and attach a **sub-trial's denominators to a pooled effect estimate**. That is a silent 57% under-count of the denominator. This lane hit it and stopped; the next one may not.

### Decision required
Either (a) give the row a list-valued `nct` (`["NCT01032629","NCT01989754"]`) and teach the extractor to pool, or (b) split it into two rows and pool at synthesis time. Option (a) preserves the published pooled HR; option (b) does not exist in the source publication and would require re-analysis. **(a) is the smaller change and matches what the publication reports.**

### Related, same class of defect
`classes[29]` also carries **EMPA-REG OUTCOME** (`trials[0]`, NCT01131676) and **VERTIS-CV** (`trials[3]`, NCT01986881) as single rows, both of which are **pooled dose arms** in the registry (EMPA-REG: 2337 / 2347 / 2344 across placebo, 10 mg, 25 mg; VERTIS-CV: 2752 / 2747 / 2747). Those are not entity mismatches, but any extractor must pool the active arms explicitly rather than taking one dose group. Worth the same `outcome`-field discipline.

---

## Cross-cutting recommendation

All three defects share one root cause: **a trial row does not record which outcome, which population, and which analysis window it represents.** `classes[29]` has an `outcome` field and is the only class where the intended endpoint is unambiguous. Adding three required fields to every trial row —

```jsonc
"outcome":        "All-cause mortality",
"population":     "randomised" | "FAS" | "safety",
"window":         "full follow-up" | "12 months" | ...
```

— would have made DEFECT-01 and DEFECT-02 visible at write time rather than two months later during a recovery sweep.

---

## Verification note

Every registry figure quoted above was read from the ClinicalTrials.gov results API via the browser (same-origin fetch), not from a cached extraction and not from recall. NCT-to-acronym mappings for CANVAS and CANVAS-R were resolved by a live registry title search. No file in the repository was modified.
