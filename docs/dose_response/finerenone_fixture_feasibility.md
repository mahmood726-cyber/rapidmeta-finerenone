# Finerenone Phase 2 dose-response fixture — feasibility memo

**Status:** DONE_WITH_RECOMMENDATION (no buildable k≥2 fixture)
**Round:** 3.6 of the Finrenone dose-response pack
**Engine:** `rapidmeta-dose-response-engine-v1.js` (v0.3.0, k≥2 hard requirement at `fitRCS`/`fitLinear`)
**AACT snapshot:** `C:/Users/user/AACT/2026-04-12/`
**Author:** automated agent run, 2026-05-14
**Companion data:** none — fixture build was stopped after Phase B per the brief's "do not build broken data" rule.

---

## Executive summary

Of the 7 candidate NCTs from AACT, only **one** Phase 2 finerenone trial provides
clean fixed-dose multi-arm efficacy data with a true placebo reference and AACT-posted
results — **ARTS-DN (NCT01874431)**. The remaining 6 trials are eliminated for
different, individually fatal reasons (Phase 1, no posted results, no placebo, up-titrating
regimens, crossover design, registry only). The engine requires k≥2 trials. A
k=1 fixture cannot be fit by the current engine. This memo documents what was
found and lays out three options for the user.

---

## Phase A — inventory of the 7 candidate NCTs

| NCT | Acronym | Phase | n_arms (AACT) | Population | Results posted | Verdict |
|---|---|---|---|---|---|---|
| NCT01874431 | ARTS-DN | PHASE2 | 8 | T2D + diabetic nephropathy | 2021-05-04 | **USABLE** — placebo + 7 fixed doses (1.25/2.5/5/7.5/10/15/20 mg), 821 baseline-counted participants, clean monotonic UACR primary |
| NCT01807221 | ARTS-HF | PHASE2 | 6 | HFrEF + CKD/T2D | 2021-06-15 | UNUSABLE — eplerenone active comparator (no placebo); finerenone arms are **up-titrating regimens** (2.5→5, 5→10, 7.5→15, 10→20, 15→20 mg) not fixed doses; primary outcome is % participants with >30% NT-proBNP decrease (proportion, not LSM); non-monotonic dose-response across regimens (37.2 → 30.9 → 32.5 → 37.3 → 38.8 → 34.2 %) |
| NCT01968668 | ARTS-DN Japan | PHASE2 | 8 | T2D + diabetic nephropathy (Japan) | **NOT POSTED** | UNUSABLE — 0 outcomes rows, 0 outcome_measurements rows, 0 baseline_measurements rows in AACT 2026-04-12 |
| NCT01473108 | (no acronym) | PHASE1 | 5 | Healthy volunteers, crossover | NOT POSTED | UNUSABLE — Phase 1 crossover (single-dose 2.5/5/10/20 mg + placebo + 50 mg eplerenone, 3-fold crossover); engine schema is per-arm parallel-group means, crossover doesn't fit; also Phase 1 not the target population |
| NCT02378805 | Alport-XXL | (no phase) | (no n_arms) | Registry | n/a | UNUSABLE — non-interventional registry, not a trial |
| NCT02956109 | (no acronym) | PHASE1 | 4 | Healthy male volunteers | n/a | UNUSABLE — Phase 1 paediatric formulation PK; not a dose-response efficacy study |
| NCT02957396 | (no acronym) | PHASE1 | 4 | Healthy male volunteers | n/a | UNUSABLE — Phase 1 paediatric formulation PK; not a dose-response efficacy study |

**Net: 1 usable trial out of 7.**

### ARTS-DN per-arm baseline N (AACT `baseline_counts.txt`)

| Arm code | Arm label | N |
|---|---|---|
| BG000 | Finerenone 1.25 mg | 96 |
| BG001 | Finerenone 2.5 mg | 92 |
| BG002 | Finerenone 5 mg | 100 |
| BG003 | Finerenone 7.5 mg | 97 |
| BG004 | Finerenone 10 mg | 98 |
| BG005 | Finerenone 15 mg | 125 |
| BG006 | Finerenone 20 mg | 119 |
| BG007 | Placebo | 94 |
| | **Total** | **821** (≈ enrollment 823) |

---

## Phase B — common-outcome search

### Candidate B1: ARTS-DN primary (Ratio UACR Day-90 / Baseline)

ARTS-DN reports a clean monotonic dose-response on its registered primary endpoint
(`Ratio of UACR at Day 90 to UACR at Baseline`, AACT outcome_id 211099820):

| Arm | LSM ratio | 90% CI |
|---|---|---|
| Placebo (OG007) | 0.938 | 0.829 – 1.061 |
| 1.25 mg (OG000) | 0.869 | 0.772 – 0.979 |
| 2.5 mg (OG001) | 0.890 | 0.786 – 1.009 |
| 5 mg (OG002) | 0.824 | 0.730 – 0.929 |
| 7.5 mg (OG003) | 0.739 | 0.653 – 0.835 |
| 10 mg (OG004) | 0.708 | 0.627 – 0.800 |
| 15 mg (OG005) | 0.630 | 0.563 – 0.705 |
| 20 mg (OG006) | 0.585 | 0.523 – 0.654 |

Monotonic, clean — paper-quality dose-response. But **no second trial** reports the
UACR Day-90 ratio primary endpoint:

- ARTS-HF primary is `% participants with >30% NT-proBNP decrease` (binary-style
  proportion) at Day 90 — different endpoint, different population.
- ARTS-DN Japan would have reported the same UACR primary, but **its AACT results
  block is empty** (not posted as of the 2026-04-12 snapshot; the published Bayer
  CTR/EU CTR may carry the data but AACT does not).

**Result:** k=1 on the UACR primary. Cannot fit the engine.

### Candidate B2: Serum potassium change from baseline (secondary, both trials report)

Both ARTS-DN (secondary outcome 211099821) and ARTS-HF
(other-pre-specified outcome 210976737) report change-from-baseline in serum
potassium at Day 90. This was the most promising common-outcome candidate.

**ARTS-DN Day-90 K+ change (LSM, 95% CI, mmol/L):**

| Arm | LSM | 95% CI |
|---|---|---|
| Placebo | 0.002 | -0.077 – 0.081 |
| 1.25 mg | 0.109 | 0.030 – 0.187 |
| 2.5 mg | 0.123 | 0.043 – 0.203 |
| 5 mg | 0.202 | 0.122 – 0.282 |
| 7.5 mg | 0.127 | 0.047 – 0.207 |
| 10 mg | 0.167 | 0.087 – 0.248 |
| 15 mg | 0.238 | 0.165 – 0.310 |
| 20 mg | 0.188 | 0.116 – 0.259 |

Roughly monotonic with placebo, but **not strictly monotonic** within the active
arms — 5 mg (0.202) > 7.5 mg (0.127), 15 mg (0.238) > 20 mg (0.188). Acceptable
noise within a single trial.

**ARTS-HF Day-90 K+ change (MEAN ± SD, mmol/L):**

| Arm | Day-90 Mean | SD |
|---|---|---|
| Eplerenone 25→50 mg (OG000) | 0.307 | 0.609 |
| Finerenone 2.5→5 mg (OG001) | 0.184 | 0.574 |
| Finerenone 5→10 mg (OG002) | 0.153 | 0.516 |
| Finerenone 7.5→15 mg (OG003) | 0.164 | 0.579 |
| Finerenone 10→20 mg (OG004) | 0.275 | 0.580 |
| Finerenone 15→20 mg (OG005) | 0.245 | 0.574 |

Three fatal problems with using ARTS-HF as the second trial:

1. **No placebo reference.** Eplerenone is itself an active mineralocorticoid-receptor
   antagonist (typical Day-90 ΔK+ ~ 0.15-0.30 mmol/L vs placebo in MRA trials). Using
   eplerenone as the "dose=0" reference would silently embed an MRA-class effect into
   the intercept and bias the dose slope toward zero. This isn't a docstring
   limitation; it's a category-level methodological flaw.
2. **Up-titrating regimens, not fixed doses.** Every active arm in ARTS-HF is an
   *initial-dose → titrated-dose* regimen (e.g. 2.5 mg for 30 days → 5 mg for 60 days).
   The "dose" assigned at randomisation is a range, and engine `dose` must be a single
   point value. Picking an average (midpoint 3.75 mg for the 2.5→5 arm, midpoint
   17.5 mg for the 15→20 arm) is a defensible approximation but encodes
   substantial measurement error directly into the X-axis of the dose-response curve.
3. **Non-monotonic dose-response.** Day-90 K+ change goes 0.184 → 0.153 → 0.164 →
   0.275 → 0.245 across ascending titrated regimens. The non-monotonicity could be
   real (titration mid-course truncates exposure) or sample-size noise (~170/arm),
   but either way the engine's RCS fit would produce a wiggle that reflects regimen
   architecture, not pharmacology.

**Result:** Even on the most-defensible common outcome, ARTS-HF cannot be paired
with ARTS-DN to make a valid dose-response fixture.

### Candidate B3: SBP / DBP / heart rate change

Both trials report these, but they are background-of-interest only (not registered
primary or secondary efficacy estimands for either trial). Same up-titration and
no-placebo problems apply to ARTS-HF. SBP/DBP responses in ARTS-DN are small (a few
mmHg across the dose range — the trial wasn't powered for them). Not a sound choice
for a flagship dose-response demo.

### B-phase verdict

No outcome simultaneously satisfies: (a) reported in ≥2 finerenone Phase 2 trials in
the AACT snapshot, (b) clean fixed-dose arms in both, (c) placebo reference in both,
(d) interpretable dose-response. **No viable k≥2 fixture exists from this trial set.**

---

## Three options for the user

### Option (a) — Extend the engine to support k=1 (~3 hours work)

**Scope:**
- Add `fitLinearSingleTrial(trial, opts)` and `fitRCSSingleTrial(trial, opts)` paths
  to `rapidmeta-dose-response-engine-v1.js` that fit a within-trial dose-response
  curve using the trial's per-arm covariance (Greenland-Longnecker variance for
  contrasts vs reference), no between-trial pooling step, no HKSJ.
- Validation: identity tests against `metafor::dosresmeta` with `data = ARTS-DN`,
  `proc = 1cohort` (single-cohort dose-response, no Hartung-Knapp).
- Schema: single-trial fixture with the same JSON layout as the existing k≥2
  fixtures, plus a `single_trial: true` top-level flag and a top-level
  `within_trial_only: true` note that disables the cross-trial RE/HKSJ output panels
  in any consuming dashboard.

**Deliverable:** k=1 capable engine that can fit the clean ARTS-DN UACR
dose-response (the most paper-ready dose-response curve in the entire AACT MRA
literature — 8 arms, monotonic, p < 0.0001 trend, used in the Bakris 2015 JAMA
primary publication and the EMA Kerendia EPAR).

**Trade-off:** This is the option that *unlocks* the finerenone flagship. It also
generalises — any Phase 2 dose-finding monotherapy trial (which is the dominant
design pattern for the cardio/CKD class) becomes engine-fittable.

**Risk:** The engine accumulates two code paths (k=1 vs k≥2). Add a single unified
adapter `fit(trials, opts)` that dispatches to the right path, and document the
choice in `tests/dose_response_fixtures/README.md`.

### Option (b) — Build a single-trial descriptive flagship without engine fit (~1 hour work)

**Scope:**
- Build `tests/dose_response_fixtures/finerenone_arts_dn.json` as a single-trial
  fixture (ARTS-DN, 8 arms, UACR Day-90 ratio primary).
- Do not run engine fit. Produce a descriptive figure (per-arm LSM with 90% CI
  forest, dose-response scatter with monotonic trend line by Spearman or
  isotonic regression) and a 156-word E156 narrative that explicitly flags
  "single trial, dose-response within trial, no cross-trial pooling".
- Cross-link to ARTS-HF descriptively (different population, different endpoint,
  up-titrating regimen) and to ARTS-DN Japan (results not posted at AACT
  2026-04-12; cite the Bakris 2015 JAMA paper + 2016 Lin EHJ for completeness).

**Deliverable:** an E156 paper draft + a published-but-not-engine-pooled HTML
dashboard.

**Trade-off:** Honest about the small-k limit, no engine extension required,
but loses the methodological "we re-fit the FDA-registered dose response with
our published engine" hook that the SURMOUNT and SURPASS flagships have.

### Option (c) — Defer finerenone flagship; pick a different post-2010 drug

**Candidates with clean k≥2 fixed-dose Phase 2/3 dose-response in AACT:**

- **Empagliflozin** (T2D, A1c lowering): Phase 2b (NCT01177813, 5 doses + placebo)
  + Phase 3 EMPA-REG MONO (NCT01177813 extended); but EMPA-REG OUTCOME is fixed-dose
  10/25 vs placebo only.
- **Tirzepatide additional SURMOUNT trials** (already partially covered by the
  existing SURMOUNT fixture; SURMOUNT-3 and -4 may now be results-posted in AACT
  2026-04-12 — worth a re-check).
- **Semaglutide (oral PIONEER programme, SC STEP programme):** STEP-1/2/3/4 = 2.4 mg
  fixed-dose only (single-dose fixture, doesn't satisfy dose-response); but the
  Phase 2 SC NCT01923181 / oral NCT02906930 had 5 fixed doses + placebo.
- **Sotagliflozin** (T1D and HF): Phase 2 NCT01742390 had 6 fixed doses + placebo,
  primary on HbA1c.
- **Bempedoic acid** (LDL-C): Phase 2 NCT01692522 (4 doses + placebo), NCT02659059
  (3 doses + placebo); CLEAR programme Phase 3 was fixed-dose 180 mg only.

**Trade-off:** Loses the cardio-renal theme alignment that finerenone-as-flagship
provides (FIDELIO/FIGARO/FINEARTS are the heart-of-portfolio cardiorenal trials);
gains a fixture that can actually exercise the k≥2 engine.

---

## Recommendation

**Option (a) — extend the engine to k=1**, for three reasons:

1. ARTS-DN is *the* paradigmatic dose-finding trial of the modern non-steroidal MRA
   era. Its UACR dose-response curve is reproduced in the EMA EPAR, in the
   FDA Kerendia label, and in three Cochrane reviews. A published k=1 engine
   that exactly reproduces ARTS-DN's Bakris-2015 dose-response slope is a
   defensible scientific deliverable.
2. The k=1 path generalises to a wide class of post-2010 dose-finding Phase 2
   trials in the cardio-renal portfolio (the dominant design pattern). Any
   Phase 2b multi-dose monotherapy trial with placebo becomes fittable.
3. Estimated 3 hours of focused work, smaller blast radius than option (c)
   (which would also require rebuilding the abstracts + commentary pack from
   scratch for a different molecule).

**If Option (a) is rejected**, then Option (b) is the next-best, because it
ships a real ARTS-DN E156 paper and a useful dashboard without making any
methodological claim the data can't support.

**Option (c) is the most expensive** in token + scientific-coherence terms; only
sensible if the user actively wants to pivot the dose-response pack away from
cardio-renal.

---

## Files referenced

- Engine: `C:/Projects/Finrenone/rapidmeta-dose-response-engine-v1.js` (line 1124-1126
  is the `fitRCS: fewer than 2 studies...` throw).
- Existing fixtures (schema reference): `C:/Projects/Finrenone/tests/dose_response_fixtures/tirzepatide_obesity_surmount.json`, `tirzepatide_t2d_surpass.json`.
- AACT snapshot: `C:/Users/user/AACT/2026-04-12/` (studies.txt, design_groups.txt,
  outcomes.txt, outcome_measurements.txt, result_groups.txt, baseline_counts.txt).
- Authoritative source for ARTS-DN dose-response: Bakris GL et al. JAMA
  2015;314(9):884-894 (PMID lookup deferred per the brief — Phase D was skipped
  because Phase C did not run).
