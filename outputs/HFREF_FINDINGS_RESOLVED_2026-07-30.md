# HFrEF integrity findings — resolution

**Date:** 2026-07-30 · **Branch:** `audit/hfref-integrity-gates-2026-07-30` · **Status:** STAGED, NOT PUSHED
**Resolves:** the 5 findings in `outputs/HFREF_INTEGRITY_GATES_2026-07-30.md`
**Ledger:** `outputs/hfref_quarantine_ledger.json` · **Re-fit:** `outputs/hfref_quarantine_primary.json`, `outputs/hfref_quarantine_refit.json`

Principle applied: **quarantine, never silent deletion**; reconcile discrepancies **to the
primary source**; never fabricate. Where a value could not be read from the primary in this
pass, the evidence tier is stated rather than glossed.

**No extracted count was altered.** Four findings resolved to *"the extraction was right, the
provenance record was wrong."* One resolved to *"the extraction has no source"* — and was
quarantined, because there is no sourced value to correct it to.

---

## 1. Disposition of each finding

| # | Trial | Audit finding | Disposition | Named violation |
|---|---|---|---|---|
| F1 | RESOLVD | Wrong PMID; 3.4% vs 3.7% residual | **Citation corrected, residual closed** | — |
| F2 | CARMEN | 14/14/14 has no located source | **QUARANTINED** | *no death data in source; 14/14/14 unsourced; primary is LVESVI* |
| F3 | SPICE | "No primary source at all" | **Claim WITHDRAWN — source located** | — |
| F4 | He 2015 | Per-arm denominators unverified | **Claim WITHDRAWN — verified exactly** | — |
| F5 | QUEST | Significance discordance | **Counts verified; presentation constrained** | — |

### F2 — CARMEN: QUARANTINED (the only one)

PMID 15115904 confirms the arms exactly (carvedilol 191, enalapril 190, combination 191) but
the trial's primary endpoint is **left-ventricular end-systolic volume index** and it reports
**no per-arm deaths anywhere**. The ledger carried an identical 14 deaths in all three arms.
`hfref_eightcell_fit.R:377` already annotated CARMEN inadmissible — the project's own code
contradicted its own ledger.

The three arm rows are **retained** in the ledger with a stated reinstatement condition
(locate a primary or CARMEN-authored secondary reporting per-arm all-cause deaths). The app
verifier **blocks** if CARMEN is deleted rather than flagged.

### F3 — SPICE: the audit was wrong, and this is the consequential one

The primary **exists**: **PMID 10740141**, Granger CB et al, *Am Heart J* 2000;139(4):609-17 —
SPICE = **S**tudy of **P**atients **I**ntolerant of **C**onverting **E**nzyme inhibitors. The
acronym never appears in the PubMed record, which is why an acronym-keyed search returned only
the observational SPICE Registry and the audit concluded no source existed.

> "…double-blind randomization in a 2:1 ratio to receive candesartan (n = 179) or a placebo
> (n = 91)" … "death 3.4% and 3.3%"

179 + 91 = 270 exact. 6/179 = 3.35% → 3.4%; 3/91 = 3.30% → 3.3%. The ledger's 6/179 and 3/91
are the only integer pairs consistent with both percentages. **Retained and now cited.**

Had SPICE been quarantined as the audit proposed, the network would have lost its only
between-trial loop (see §3).

### F4 — He 2015: verified exactly from full text

PMC5746969 **Table 1** gives the five arm sizes and **Table 2** the per-arm all-cause deaths:

| Arm | n | All-cause deaths |
|---|---:|---:|
| Metoprolol | 96 | 14 |
| Benazepril low-dose | 97 | 11 |
| Valsartan low-dose | 100 | 13 |
| Benazepril high-dose | 101 | 8 |
| Valsartan high-dose | 97 | 8 |

Ledger BB **14/96** — exact. Ledger ACEI **19/198** = 11/97 + 8/101 — exact. The audit's
hypothesised equal-split 192 is superseded by the stated 198.

Three disclosures now carried in the app, none of them integrity violations:
- **Dose pooling.** The two benazepril arms are pooled onto one ACEI node. The trial found them
  significantly different (41% RRR, P=0.042) — but **that P is for the primary composite**
  (death *or* HF admission), not all-cause death. On the outcome actually pooled here the arms
  are 11/97 vs 8/101, **Fisher p = 0.49**. The pooling is defensible *for this outcome*.
- **Dropped valsartan arms.** 13/100 and 8/97 are discarded rather than mapped to the ARB node.
- **Source-internal inconsistency.** Abstract and registry say 480 randomised; the Results text
  and Table 1 sum to **491**.

### F1 — RESOLVD: citation corrected, residual closed

Citation → **PMID 10653828**, *Circulation* 2000;101(4):378-84 ("Four hundred twenty-six
patients … randomized to receive metoprolol CR or placebo"; 212+214 = 426 exact). The
superseded PMID 10477530 (McKelvie 1999, 768 patients, no metoprolol randomisation) is gone
except where the correction itself is documented.

**The residual is closed as an inconsistency *internal to the source*.** The paper's body text
reports the metoprolol deaths as **n=8 (3.7%)** against placebo **n=17 (8.1%)**, while its own
abstract says **3.4%** for the same arm. The extracted counts **8 and 17 match the body text**.
Correcting them to the abstract's 3.4% would mean inventing a count the source never states.

> **Evidence tier, stated honestly:** the body-text figures are **SECONDARY_CORROBORATED** —
> returned concordantly by two independent retrievals of the publisher page. The publisher's
> HTML and PDF sit behind a Cloudflare bot check which was **not circumvented**, so I have not
> read the full text myself. This is labelled, not glossed.

One sub-question remains precisely characterised rather than hidden: 214/212 reproduces the
metoprolol 3.7% but yields 8.02% (prints 8.0) for placebo, whereas 216/210 reproduces **both**
published percentages exactly and also sums to 426. **Impact quantified: logRR −0.763085 vs
−0.781869, a shift of 0.0188 against a contrast SE of 0.4177 — 0.045 SE.** It cannot move any
network estimate materially. Retained as extracted, flagged rather than switched, because
switching would substitute an inference for a read.

### F5 — QUEST: counts verified, presentation constrained

PMC11333273 states it verbatim: *"A total of 221 patients (14.21%) … and 262 patients (16.85%)
… died from any cause (HR, 0.84; 95% CI, 0.70–1.01; P = 0.058)."* Counts and denominators
exact — **upgraded to VERIFIED_FULL, no change.**

The finding is a **presentation** issue. The trial's own analysis — a Cox model accounting for
follow-up and censoring — is **not significant**. Fisher's exact on the crude 2×2 gives
p = 0.0426 with **fragility index 1**. The trial's reported analysis is authoritative; the app
now states HR 0.84 (0.70–1.01), P=0.058 on the badge, and **no QLQX contrast is presented as
significant on the crude 2×2**.

---

## 2. k-ledger

| | k |
|---|---:|
| Trials in the settled primary | 28 |
| **Quarantined** (CARMEN — unsourced mortality) | **−1** |
| **Trials in the re-fitted primary** | **27** |
| Trials on record in the app ledger (CARMEN retained, flagged) | 28 |
| Arm rows | 57 → **54** |
| Fitted contrasts | 30 → **27** |
| Trials with a PMID | 27 of 28 → **27 of 27** (SPICE's located) |

---

## 3. Structural consequence — the audit's expectation was wrong

| | Before | After |
|---|---:|---:|
| Nodes (V) | 15 | 15 |
| Edges (E) | 16 | **15** |
| Designs | 16 | 15 |
| Cyclomatic number | 2 | **1** |
| Multi-arm internal loops | 1 | **0** |
| **ICDF** | **1** | **1 — UNCHANGED** |

Edge lost: **ACEI+BB vs BB** (CARMEN was its only trial). **No node lost** — He 2015 still
supplies ACEI–BB. Placebo–ARB direct leg unchanged at k=1, 9 events.

**ICDF does not fall.** The loop CARMEN closed lay entirely *inside a single multi-arm study*,
and the ICDF definition already subtracts such loops because they carry no between-trial
inconsistency information. Removing CARMEN costs a cyclomatic loop that was **never counted**.
Inconsistency does not become less assessable than it already was.

The surviving between-trial loop is **Placebo–ACEI–ARB**, and it rests entirely on **SPICE**:
branches 7b/7c, which drop SPICE at elig L3, show **ICDF 0** both before and after. Re-sourcing
SPICE rather than quarantining it is precisely what preserves the only loop the network has.

Heterogeneity: τ² 0.02323609 → **0.02402829**; I² 57.3% → **60.9%**; HKSJ df 15 → 13,
multiplier 2.2754 → 2.2536.

---

## 4. Anchor: before → after

Anchor gate **PASSED** — the pre-quarantine re-fit reproduces the settled primary to <1e-8 on
both anchor nodes and on τ², and only then is the quarantined fit emitted.

| Node vs Placebo | Before | After | Δ |
|---|---|---|---:|
| **ACEI+BB** | **0.645 (0.433–0.959)** | **0.631 (0.423–0.943)** | −2.04% |
| **ACEI+BB+MRA** | **0.593 (0.348–1.011)** | **0.582 (0.341–0.995)** | −1.86% |
| ARNI+BB | 0.579 (0.357–0.939) | 0.568 (0.349–0.923) | −2.02% |
| +SGLT2i | 0.526 (0.288–0.958) | 0.516 (0.282–0.943) | −1.85% |
| +QLQX | 0.500 (0.258–0.972) | 0.491 (0.252–0.957) | −1.86% |
| +Vericiguat | 0.508 (0.265–0.976) | 0.499 (0.259–0.961) | −1.86% |
| +Digitoxin | 0.547 (0.280–1.068) | 0.537 (0.274–1.051) | −1.86% |
| +Omecamtiv | 0.592 (0.312–1.125) | 0.581 (0.305–1.107) | −1.86% |
| ACEI+BB+ARB | 0.588 (0.341–1.014) | 0.576 (0.333–0.997) | −2.04% |
| ACEI | 0.894 (0.625–1.277) | 0.894 (0.624–1.280) | +0.04% |
| ACEI+MRA | 0.673 (0.401–1.128) | 0.673 (0.400–1.131) | +0.04% |
| ACEI+ARB | 0.910 (0.544–1.522) | 0.910 (0.542–1.526) | +0.04% |
| ARB | 0.851 (0.527–1.372) | 0.849 (0.526–1.371) | −0.20% |
| **BB** | **0.996 (0.509–1.949)** | **1.359 (0.555–3.328)** | **+36.40%** |

**BB is the big mover** and the honest reading is that it should not be read as an estimate of
much: it was informed by CARMEN's two BB edges and now rests on He 2015 alone (14/96 vs 19/198),
with an interval spanning 0.56–3.33.

### The uncomfortable direction, stated plainly

CARMEN's identical **14/14/14** was **RR = 1.00 on every edge it touched** — a null-pulling
weight. Withdrawing it moves estimates **away from the null**, and the count of contrasts whose
CI excludes 1 rises **12 → 17**. ACEI+BB+MRA (1.011 → 0.995) and ACEI+BB+ARB (1.014 → 0.997)
cross into nominal significance.

**This is a provenance correction, not a result that got better.** It must not be reported as
strengthened evidence. **16 of the 17** CI-excludes-1 contrasts are **purely indirect**; the
Walsh fragility index is defined on an observed 2×2 and an indirect estimate has none, so
fragility for them is **undefined — not favourable**.

---

## 5. Multiverse (every cell moves the same direction)

| Cell | Trials | ACEI+BB | ACEI+BB+MRA |
|---|---|---|---|
| 1. Tang 2024 | 43→42 | 0.598→0.585 | 0.518→0.507 |
| 2. Burnett 2017 | 38→37 | 0.623→0.612 | 0.541→0.532 |
| 3. Komajda 2018 | 42→41 | 0.590→0.575 | 0.516→0.505 |
| 4. Tromp 2021/22 | 38→37 | 0.686→0.683 | 0.574→0.571 |
| 5. De Marzo 2022 | 42→41 | 0.590→0.575 | 0.516→0.505 |
| 6. van Essen 2025 | 38→37 | 0.686→0.683 | 0.574→0.571 |
| **7a. OURS-STRICT (primary)** | **28→27** | **0.645→0.631** | **0.593→0.582** |
| 8. OURS-INCLUSIVE | 31→30 | 0.626→0.612 | 0.577→0.565 |
| 7b. X-10 executed | 27→26 | 0.638→0.624 | 0.589→0.578 |
| 7c. X-10, −CARMEN | 27→26 | 0.638→0.624 | 0.589→0.578 |
| CAL. frozen v1.3 | 39→39 | 0.623→0.623 | 0.539→0.539 |

The quarantine is a **data-integrity disposition, not a coordinate choice**, so it applies to
every cell regardless of whose review the cell encodes. **CAL is the sole exception by design**:
it exists to reproduce the frozen Python fit (`netfit_hfref.py`), which included CARMEN;
quarantining there would destroy the reproducibility check the cell is for. It is a witness,
never a claim.

7c already dropped CARMEN in the settled definition, so its "before" column is a synthetic
CARMEN-included variant computed only to keep the columns comparable; its "after" (26) is the
settled 7c.

---

## 6. Proposed badge / verdict

> **VERDICT: UNCERTAIN — 5 FINDINGS DISPOSITIONED, 1 TRIAL QUARANTINED**
> Network **27 trials** (CARMEN quarantined) · Quarantined **1** · Arithmetic gates **0 findings**
> · Provenance findings **5 raised, 5 dispositioned, 0 open** · **Counts changed: 0**
>
> **Quarantined:** CARMEN — *no death data in source; 14/14/14 unsourced; primary is LVESVI*.
> Arm rows retained in the ledger, not deleted.
>
> **Withdrawn as wrong:** the audit's claims that SPICE has no primary source (it is PMID
> 10740141), that He 2015's per-arm denominators are unverified (PMC5746969 verifies
> 19/198 = 11/97 + 8/101 exactly), and that QUEST's counts are unverified (PMC11333273 states
> 221 and 262 verbatim).
>
> **Anchor moved:** ACEI+BB 0.645 → 0.631 · ACEI+BB+MRA 0.593 → 0.582. CARMEN's identical
> 14/14/14 was RR=1.00 on every edge, so removing it moves estimates AWAY from the null and
> CI-excludes-1 rises 12 → 17. That is a provenance correction, **not** a result that got better.
>
> **Structure:** cyclomatic 2 → 1, but **ICDF unchanged at 1** — CARMEN's loop was internal to
> one study and was never counted. The surviving between-trial loop is Placebo–ACEI–ARB and it
> exists only because SPICE was re-sourced rather than quarantined.
>
> **QUEST:** the trial's own all-cause-mortality analysis is HR 0.84 (0.70–1.01), P=0.058 —
> **not significant**. No QLQX contrast is presented as significant on the crude 2×2.
>
> **16 of 17** CI-excludes-1 contrasts are purely indirect; fragility index is **undefined**
> for them, not favourable. All 54 remaining arm rows pass count plausibility and all 27
> contrasts recompute to <1e-8 — a tested zero. GRIM/GRIMMER **not applicable** (binary
> outcome). Registry concordance covers **9 of 27**; the rest have no record to concord with.
> Full text still absent for 8 denominator-only trials; no inconsistency test fitted.
> AMSTAR-2 confidence: **CRITICALLY LOW**.

**Verdict stays UNCERTAIN.** Dispositioning the findings did not earn a PASS.

---

## 7. Verification performed

- **Anchor gate** — pre-quarantine re-fit reproduces the settled primary to <1e-8 (`PASS`);
  the script refuses to emit otherwise.
- **`scripts/hfref_verify_app_quarantine.py`** — structure (div balance, script integrity,
  every `data-tab` has a panel, placeholder leaks), payload row-for-row vs the R re-fit at
  1e-8, **verdict-surface agreement**, quarantine integrity, QUEST constraint. `PASS`.
  **Negative-tested and it blocks:** league RR perturbed 1e-6 → FAIL; badge trial count
  27→28 → FAIL; badge anchor 0.631→0.501 → FAIL; CARMEN deleted instead of flagged → FAIL.
- **JS parse gate** (`scripts/jscheck.py`) — `[JS-OK]`.
- **Cross-meta contamination gate** (`scripts/scan_cross_meta.py`) — 410 clean / 127
  contaminated repo-wide (pre-existing); **this app is not flagged**.
- **Live render** — served over HTTP and driven in-browser: all 8 tabs activate, 0 console
  errors, single data source `window.HFREF_FIT` carrying 27 trials / 0.63142 / ICDF 1, and no
  stale value (`0.64459765`, `0.59333495`, `"trials": 28`) anywhere in rendered text.

> Rendering is what caught the one real defect in this pass: a first draft replaced only the
> badge headline and appended the new body, leaving a stale "Trials: 28" row and an "all 57 arm
> rows" sentence in place — the badge asserted 28 and 27 simultaneously. The badge is now
> replaced wholesale by balanced-`<div>` matching, and the verifier gained a
> **self-contradiction** check that fails on any trial/arm-row count in the badge that
> disagrees with the post-quarantine figure.

## 8. Still not done — explicit

1. Full-text verification for the **8 denominator-only** trials.
2. **RESOLVD per-arm split** (214/212 vs 216/210) — impact bounded at 0.045 SE.
3. **AACT posted-results** event-count checks.
4. **Inconsistency testing** — still not fitted or quoted.
5. Whether **He 2015's valsartan arms** should be mapped to the ARB node rather than dropped.

**Not pushed.** Pending the cross-family Gemini gate and Mahmood's explicit go.
