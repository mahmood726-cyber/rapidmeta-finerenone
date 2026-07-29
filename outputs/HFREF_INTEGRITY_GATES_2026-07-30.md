# HFrEF GDMT network — per-trial data-integrity gates, executed

**Date:** 2026-07-30
**Scope:** the 28 RCTs of the settled `OURS-STRICT` cell fitted in `HFREF_NMA_AUTO_FULL_REVIEW.html`
**Methodology applied:** `outputs/extraction_audit/FINAL_INTEGRITY_REPORT_V2.md` (the gate the app's badge references), plus `scripts/fragility_index_check.py` (Walsh 2014)
**Status:** STAGED. Not pushed. New integrity claims require a cross-family gate before going live.

This report exists because the app's badge previously said the per-trial data-integrity
gates had **NOT** been run. They have now been run. This is what they found.

---

## 1. Which gates apply, and which do not

| Gate (methodology ref) | Applies? | Why |
|---|---|---|
| **G1** per-arm count plausibility (M01 2×2 sanity) | **YES** | Binary mortality counts; integer, `0 ≤ e ≤ N`, denominators must agree with the fitted contrasts |
| **G1b** contrast-vs-ledger + logRR recompute | **YES** | Every fitted contrast must be reproducible from the arm ledger |
| **G2** GRIM / GRIMMER (M08) | **NO — N/A** | GRIM tests whether a reported **mean** of a bounded integer-scale item is reconstructible as `X/N`. This network's only outcome is all-cause mortality, a **binary per-arm count**. There are no means, SDs, or Likert items anywhere in the extraction, so GRIM has nothing to test. **Replaced by G1.** |
| **G3** Benford first-digit (M09) | YES (advisory) | Fabrication signal on the pooled count/denominator digits |
| **G4** arm-balance ratio (M06 baseline-N) | YES (advisory) | Detects implausible randomisation ratios |
| **G5** identifier format (M03/M04) | **YES** | PMID/NCT well-formedness and presence |
| **G6** AACT / ClinicalTrials.gov registry concordance (R7/R9/R10) | **PARTIAL — 9 of 28** | See §4. Applies **only** to trials with a registry record. |
| **G7** Fragility Index (Walsh 2014) | **YES, trial-level only** | See §5 — it is **undefined** for 11 of the 12 significant *network* contrasts. |

### Why registry concordance covers only 9 of 28 trials

**17 of the 28 trials have no ClinicalTrials.gov record at all.** They predate trial
registration (SOLVD-Treatment 1991 → CHARM-Added 2003), plus Vizzardi 2014 which was
never registered: SOLVD-Treatment, SPICE, ELITE, ELITE-II, REPLACE, CIBIS-I, CIBIS-II,
MERIT-HF, COPERNICUS, BEST, US-Carvedilol, RESOLVD, CARMEN, RALES, Vizzardi 2014,
Val-HeFT, CHARM-Added.

For these, registry concordance is **NOT APPLICABLE — no registry record exists to
concord with.** No concordance verdict is asserted for them, and none should be
inferred. A further **2** trials are registered outside ClinicalTrials.gov
(DIGIT-HF → EudraCT 2013-005326-38; QUEST → ChiCTR1900021929), so AACT proper does not
cover them either; both registry IDs were instead confirmed directly in their
publications.

---

## 2. Deterministic gate results

Run: `python scripts/hfref_integrity_gates.py` → `outputs/hfref_integrity_gates.json`

| Gate | Result |
|---|---|
| G1 per-arm count plausibility | **0 findings** across 57 arm rows — every count is a non-negative integer, every `events ≤ N`, and every trial's `total_n` / `total_events` / `n_arms` agree with its arm rows |
| G1b contrast-vs-ledger + recompute | **0 findings** across 30 fitted contrasts — every `logRR` and `seLogRR` recomputes from the counts to <1e-8 |
| G3 Benford | χ²=14.38 on 8 df (crit 15.51) → **no fabrication signal** |
| G4 arm balance | 2 advisories: REPLACE 3.91:1, He 2015 2.06:1 — **both explained** (see §3), neither is an error |
| G5 identifiers | **1 finding**: SPICE has no PMID |
| G7 fragility | 30 contrasts: 19 not significant, 10 OK, **1 FAIL** |

**The arithmetic layer is clean.** No count violates its denominator, and the fitted
network is exactly reproducible from the extracted 2×2 tables. What the gates found is
not arithmetic error — it is **provenance**.

---

## 3. Source verification, per trial (all 28, by lookup)

Every PMID was resolved against PubMed and every registry ID against ClinicalTrials.gov
or the trial's own publication. Nothing below is from recall. Full evidence with quoted
source fields: `outputs/hfref_source_verification.json`.

| Status | n | Meaning |
|---|---:|---|
| **VERIFIED_FULL** | **15** | Denominators **and** per-arm death counts confirmed against the cited source |
| **VERIFIED_DENOM_ONLY** | **8** | Denominators confirmed; per-arm death counts **not stated** in the accessible record — neither confirmed nor contradicted |
| **FINDING** | **5** | A discrepancy, wrong identifier, or unlocatable source |

### VERIFIED_FULL (15)

SOLVD-Treatment, ELITE, CIBIS-I, CIBIS-II, MERIT-HF, COPERNICUS, BEST, US-Carvedilol,
RALES, EMPHASIS-HF, J-EMPHASIS-HF, PARADIGM-HF, DAPA-HF, VICTOR, DIGIT-HF.

Ten of these match the source **verbatim** (e.g. CIBIS-II "156 [11.8%] vs 228 [17.3%]
deaths" — ledger 156/1327 and 228/1320). Five were recovered exactly from published
percentages (e.g. US-Carvedilol 22/696 = 3.16% vs published 3.2%; 31/398 = 7.79% vs
published 7.8%). All twelve percentage back-computations agree to <0.06 pp.

### VERIFIED_DENOM_ONLY (8)

ELITE-II, REPLACE, Vizzardi 2014, Val-HeFT, CHARM-Added, PARACHUTE-HF,
EMPEROR-Reduced, GALACTIC-HF.

In each case the denominators are confirmed exactly, but the source's **abstract reports
a different quantity** than the ledger extracts — typically the primary composite or
cardiovascular death rather than all-cause death. Examples:

- **EMPEROR-Reduced**: the abstract states "361 of 1863 … and 462 of 1867", which confirms
  the denominators exactly, but those are the **primary composite**, not all-cause death.
  The ledger's all-cause 249/266 are not stated.
- **GALACTIC-HF**: the abstract's CV-death figures (808/19.6%, 798/19.4%) back-compute the
  denominators 4120/4112 exactly; the ledger's all-cause 1078/1078 are not stated.
- **PARACHUTE-HF**: abstract gives CV death 110/117; ledger's all-cause 129/134 not stated.

These are **not errors**. They are the honest limit of abstract-level verification.
Confirming them requires full text or posted registry results.

---

## 4. FINDINGS (5)

### F1 — RESOLVD cites the wrong paper (actionable, fixable) — **HIGH**

The ledger cites **PMID 10477530** = McKelvie, *Circulation* 1999;100:1056-64, the
candesartan/enalapril/combination comparison in **768** patients. That paper contains
**no metoprolol randomisation** and no 212/214 arms — it cannot substantiate the
extracted ACEI-vs-ACEI+BB contrast.

The data actually come from the **RESOLVD metoprolol sub-study**: **PMID 10653828**,
*Circulation* 2000;101(4):378-84, which states "Four hundred twenty-six patients … were
randomized to receive metoprolol CR or placebo" — and 212 + 214 = **426**, exact.

This is precisely the "wrong-PMID" class the methodology's own R7/R8 rounds target.
**Proposed fix:** PMID → `10653828`, DOI → `10.1161/01.cir.101.4.378`.

**Residual, unresolved:** that sub-study reports deaths as "3.4% versus 8.1%". Placebo
17/212 = 8.02% matches 8.1%. But metoprolol 8/214 = 3.74% does **not** match 3.4%
(nor does 7/214 = 3.27%). The metoprolol-arm death count cannot be reconciled from the
abstract. **Flagged open — needs full text.** I have not changed the count.

### F2 — CARMEN's event counts have no located source — **HIGHEST**

The abstract confirms the three arms exactly: "carvedilol (N = 191), enalapril (N = 190)
or their combination (N = 191)" — denominators match. But CARMEN's primary endpoint is
**left-ventricular end-systolic volume index**, and the abstract reports **no deaths**.
The ledger nonetheless carries an identical **14 deaths in all three arms**.

The project's own code corroborates the problem: `hfref_eightcell_fit.R:377` annotates
branch 7c as *"CARMEN inadmissible (its primary reports LVESVI and no deaths)"*. The
codebase asserts this trial reports no deaths, while the fitted ledger supplies 14/14/14.

This matters structurally: **CARMEN is the only multi-arm trial and the only trial that
closes the network's single internal loop.** Its counts are load-bearing for the network
topology. I have **not** altered them — the correct disposition (locate a source, or drop
to branch 7c) is a human call.

### F3 — SPICE has no primary source at all — **MEDIUM**

No PMID, no DOI. The ledger's own note states the only PubMed-indexed SPICE paper is the
**observational SPICE Registry (n=9580)**, not this 270-patient randomised comparison.
Counts 3/91 and 6/179 are therefore **unsubstantiated**. SPICE contributes the sole
Placebo–ARB edge, so it is not redundant in the network.

### F4 — He 2015: per-arm denominators unverified + arm pooling merges non-equivalent doses — **MEDIUM**

Publication and registry (NCT01917149) agree on total enrolment **480** and on **five**
randomised arms (metoprolol; low- and high-dose benazepril; low- and high-dose valsartan).
**Neither source states per-arm N**, so the ledger's 198 (ACEI) and 96 (BB) are
**unverified** — an equal 5-way split would give 96 per arm and **192** for two pooled
benazepril arms, not 198.

Separately: the ledger maps two benazepril **dose** arms onto one ACEI node, but the trial
itself found high- vs low-dose benazepril **significantly different** (41% risk reduction,
P=0.042). The pooling merges arms the source reports as non-equivalent, and drops the two
valsartan arms entirely. The 2.06:1 arm-balance advisory from G4 is explained by this
pooling.

### F5 — QUEST is significance-discordant with its own published analysis — **HIGH**

The publication states plainly: *"All-cause mortality did not differ significantly between
the two groups (HR, 0.84; 95% CI, 0.70–1.01; P = 0.058)."*

Fisher's exact on the extracted 2×2 (221/1555 vs 262/1555) gives **p = 0.0426 —
nominally significant — with a fragility index of 1.** One patient moves it to p = 0.0536.

This is not necessarily an extraction error: the published analysis is a time-to-event Cox
model accounting for follow-up and censoring; Fisher's exact on crude counts is not. But
the consequence is real — **every QLQX contrast in the league table that "excludes 1" rests
on a crude-count significance the source trial did not itself claim.** Two of the twelve
CI-excludes-1 network contrasts are QLQX contrasts.

### Design/population advisories (not integrity errors, but they bear on interpretation)

- **PARACHUTE-HF** is a **Chagas-disease cardiomyopathy** trial — the only trial restricted
  to a single non-ischaemic aetiology, and the **only open-label** trial in an otherwise
  blinded network. It is one of only two trials on the ARNI edge.
- **He 2015** is restricted to **idiopathic** dilated cardiomyopathy; the registry
  explicitly excludes coronary artery disease and diabetes.
- **REPLACE** is a 12-week **exercise-tolerance dose-ranging** trial, not a mortality trial.
- **Vizzardi 2014** is **single-blind**.

---

## 5. Fragility Index — and where it is undefined

### 5a. Trial-level (Walsh 2014, Fisher exact) — 30 fitted contrasts

19 not significant · 10 OK (FI ≥ 5) · **1 FAIL (FI = 1)**

| Trial | Contrast | FI | p₀ | Verdict |
|---|---|---:|---|---|
| **QUEST** | +QLQX vs ACEI+BB+MRA | **1** | 0.0426 | **FAIL** |
| EMPHASIS-HF | ACEI+BB+MRA vs ACEI+BB | 5 | 0.0276 | OK |
| DAPA-HF | +SGLT2i vs ACEI+BB+MRA | 8 | 0.0211 | OK |
| SOLVD-Treatment | ACEI vs Placebo | 10 | 0.0181 | OK |
| VICTOR | +Vericiguat vs ACEI+BB+MRA | 11 | 0.0179 | OK |
| US-Carvedilol | ACEI+BB vs ACEI | 12 | 0.0011 | OK |
| COPERNICUS | ACEI+BB vs ACEI | 30 | 0.00014 | OK |
| MERIT-HF | ACEI+BB vs ACEI | 34 | 0.00009 | OK |
| CIBIS-II | ACEI+BB vs ACEI | 37 | 0.00006 | OK |
| PARADIGM-HF | ARNI+BB vs ACEI+BB | 49 | 0.0008 | OK |
| RALES | ACEI+MRA vs ACEI | 54 | <1e-5 | OK |

Median FI among significant contrasts = **12**. Only QUEST is fragile, and it is fragile
in exactly the way F5 describes.

### 5b. Network level — FI is UNDEFINED for 11 of the 12 significant contrasts

The league table has **12 contrasts whose 95% CI excludes 1**. Critically:

**11 of those 12 are purely INDIRECT (`direct_k = 0`)** — no trial ever randomised those
two treatments against each other. The Walsh fragility index is defined on an *observed
2×2 table*; an indirect estimate has **no 2×2 table**. Computing an "FI" for these would
require inventing patients who do not exist. **I have not done so, and no FI should ever
be quoted for them.**

| Contrast (CI excludes 1) | RR | direct_k | FI |
|---|---:|---:|---|
| +QLQX vs Placebo | 0.501 | 0 | **undefined (indirect)** |
| +Vericiguat vs Placebo | 0.508 | 0 | **undefined (indirect)** |
| +SGLT2i vs Placebo | 0.526 | 0 | **undefined (indirect)** |
| +QLQX vs ACEI | 0.560 | 0 | **undefined (indirect)** |
| +Vericiguat vs ACEI | 0.569 | 0 | **undefined (indirect)** |
| ARNI+BB vs Placebo | 0.579 | 0 | **undefined (indirect)** |
| +SGLT2i vs ACEI | 0.588 | 0 | **undefined (indirect)** |
| ACEI+BB vs Placebo | 0.645 | 0 | **undefined (indirect)** |
| ACEI vs ACEI+BB+MRA | 1.506 | 0 | **undefined (indirect)** |
| ACEI vs ACEI+BB+ARB | 1.520 | 0 | **undefined (indirect)** |
| ACEI vs ARNI+BB | 1.543 | 0 | **undefined (indirect)** |
| **ACEI vs ACEI+BB** | **1.386** | **8** | **direct — see below** |

**Only one** CI-excludes-1 contrast rests on direct evidence: **ACEI vs ACEI+BB**, from 8
trials. Walsh FI is per-trial, so the honest reporting is the contributing trials'
individual FIs:

CIBIS-II **37**, MERIT-HF **34**, COPERNICUS **30**, US-Carvedilol **12** (significant);
CIBIS-I, BEST, RESOLVD, CARMEN not individually significant.

That contrast is **robust** — its four significant contributors need 12–37 events to
overturn. It is also the only one of the twelve for which fragility can be assessed at all.

> **Headline for the reader:** the network's most eye-catching results — every "×2 mortality
> benefit vs placebo" — are **purely indirect**, and their fragility is not merely
> unfavourable, it is **unmeasurable by this method**.

---

## 6. Proposed badge / verdict update

The current live badge (correctly) says the gates were **not run**. That is now stale in
the other direction. Proposed replacement text, reflecting only what was actually tested
and found:

> **VERDICT: UNCERTAIN — GATES NOW RUN, 5 FINDINGS OPEN**
> Trials in network: **28** · Arithmetic gates: **0 findings** · Source-verified: **15 full,
> 8 denominator-only** · Provenance findings: **5**
>
> Per-trial data-integrity gates have now been executed (2026-07-30). Arithmetic is clean:
> all 57 arm rows pass count plausibility and all 30 contrasts recompute exactly. GRIM is
> **not applicable** (binary outcome, no means). Registry concordance covers **9 of 28**
> trials — the other 19 predate ClinicalTrials.gov or are registered elsewhere, so
> concordance is **N/A, not passed**.
>
> **Open findings:** CARMEN's 14/14/14 deaths have no located source and are contradicted
> by this project's own code annotation; RESOLVD cites the wrong paper (fix proposed);
> SPICE has no primary source; He 2015's per-arm denominators are unverified; QUEST is
> significance-discordant with its published all-cause-mortality analysis (FI = 1).
>
> **11 of the 12 network contrasts whose CI excludes 1 are purely indirect — fragility
> index is undefined for them, not favourable.** AMSTAR-2 confidence: **CRITICALLY LOW.**

**Verdict stays UNCERTAIN.** Running the gates did not earn a PASS: it converted "untested"
into "tested, arithmetic clean, five provenance findings open". Those findings must be
dispositioned by a human before any upgrade.

---

## 7. What was NOT tested — explicit

1. **Full-text verification.** All source checks are against **abstracts** and registry
   records. The 8 DENOM_ONLY trials need full text to confirm their all-cause death counts.
2. **AACT posted-results (R10) event-count checks.** Not run: 17 trials have no registry
   record, and this audit used the live ClinicalTrials.gov API rather than the AACT
   2026-04-12 snapshot the methodology names.
3. **Inconsistency testing.** Still not fitted or quoted — unchanged from the app's
   standing position.
4. **The residual RESOLVD metoprolol count discrepancy** (3.7% extracted vs 3.4% published)
   is open.
5. **Whether CARMEN and SPICE should remain in the network at all** — a human decision.

---

## Attribution

Source verification used **PubMed** (NCBI E-utilities) and **ClinicalTrials.gov API v2**.
Per-trial DOIs are recorded in `outputs/hfref_source_verification.json`. Fragility index
per Walsh M et al., *J Clin Epidemiol* 2014;67:622-628, as implemented in
`scripts/fragility_index_check.py`.
