# RIFAPENTINE / latent TB — HFrEF-procedure pilot, executed

**Date:** 2026-07-30
**App:** `RIFAPENTINE_TB_AUTO_FULL_REVIEW.html` (905 KB, 2 fitted trials)
**Branch:** `upgrade/tb-prevention-rifapentine-2026-07-30`
**Recipe:** `GLOBAL_HEALTH_UPGRADE_RECIPE.md`
**Status:** STAGED, committed, **NOT PUSHED**. Pending cross-family gate.
**Ledger:** `outputs/rifapentine_tb_source_verification.json`

This is the pilot that validates the generalised HFrEF upgrade procedure on the
communicable-disease / Africa-relevant app set. It was chosen as a TB-prevention
app: WHO-recommended regimen, mission-central for the target audience, real
injected data, both badge surfaces present.

---

## Headline

**Both fitted trials fail source verification. Neither 2×2 table exists in its
cited source.** The app displayed a green `INTERNAL CHECKS PASSED` badge with
`Fabrication-risk score: 0.275 · Trials: 2` above a pooled **OR 0.389 (95% CI
0.134–1.124)** that has no evidentiary basis.

The arithmetic layer is **perfectly clean** — every cell is a valid integer with
`e ≤ N`, and the log-odds-ratio and variance recompute from the stored 2×2 to
**Δ = 0.00e+00, exactly**. That is precisely why the badge said checks passed.
**The pipeline is faithful; its input is not.**

---

## 1. What the two surfaces said, before

| Surface | Content |
|---|---|
| Visible `#rapidmeta-integrity-badge` | `#15803d` **green** · "INTERNAL CHECKS PASSED" · Fabrication-risk score **0.275** · Trials: **2** · "Multi-source audit completed (AACT 2026-04-12 + PubMed + 10 internal-consistency rounds)" |
| Machine `window.__verdict` | `"verdict":"STABLE"`, `P1_aact_concord: 2`, `P2_evidence_incomplete: 2`, `n_trials_seen: 2`, reasons: **"2 AACT title/registry advisory", "2 AACT outcome-direction divergence(s)", "2 trial(s) missing evidence rows"** |

Every trial in the app was missing evidence rows, both had registry
outcome-direction divergence — and the visible surface was green. This is the
false-green pattern the programme exists to kill, and here it sat on top of
fabricated data.

---

## 2. Source verification — every identifier by lookup

Lanes run: **ClinicalTrials.gov API v2 (live, 2026-07-30)** and **PubMed
(NCBI E-utilities)**. Nothing below is from recall.

### 2.1 NCT00814671 — wrong population **and** fabricated cells

Registry record: *"A Phase 2 Randomized, Open-label Trial of Daily Rifapentine
450mg or 600mg in Place of Rifampicin 600mg for **Intensive Phase Treatment of
Smear-positive Pulmonary Tuberculosis**"* — Johns Hopkins / University of Cape
Town Lung Institute, South Africa, enrolment **153**, PHASE2, condition
**Tuberculosis (active)**. Inclusion requires *"acid-fast bacilli in a stained
smear of expectorated sputum"*.

**This is an active-TB treatment trial sitting in a latent-TB review.** The
population mismatch is total, not marginal.

Now the cells. The app fits **tE=46, tN=54, cE=45, cN=48**. The posted results:

| | RPT450 | RIF 600 | RPT 600 |
|---|---:|---:|---:|
| Participant flow — started | **54** | **48** | 51 |
| Participant flow — completed | 47 | 44 | 49 |
| Primary: % negative LJ culture wk 8 (denominator) | 85% (41) | 94% (36) | 96% (**45**) |
| Secondary: time to conversion, liquid MGIT — **denominator** | 31 | **46** | **45** |

- **tE = 46** is not an event count. It is the **denominator of the RIF600 arm
  in a secondary *median-days* outcome**.
- **cE = 45** is not an event count. It is the **denominator of the RPT600 arm**
  in that same outcome.
- **tN = 54** is the participant-flow *started* count for **RPT450**.
- **cN = 48** is the participant-flow *started* count for **RIF600**.

So two analysis-set sizes from a median-days secondary outcome were used as
**event counts**, paired with randomisation counts from **two different arms**
as denominators. **No arm pairing in this trial yields 46/54 or 45/48 for any
outcome.** All four cells are wrong.

Two further findings: the trial randomised **three** arms and the app fits two,
silently dropping **RPT600 — the best-performing arm (96%)**, when rifapentine
dose is the trial's own experimental variable. And the primary outcome is a
**good** outcome (negative culture), so an OR < 1 would mean rifapentine
**worse** — the opposite of how the app presents it.

### 2.2 NCT01582711 (iAdhere, TBTC Study 33) — wrong outcome

Registry + publication both located. **PMID 29114781**, DOI
`10.7326/M17-1150`, PMC5766341 — Belknap R, Holland D, Feng PJ, et al.
*Ann Intern Med* 2017;167(10):689-697. Enrolment **1002**, PHASE3, condition
**Latent Tuberculosis Infection**. Population is correct.

The app fits **tE=2, tN=337, cE=5, cN=337**. The posted results:

| Outcome | DOT | SAT | SAT+SMS |
|---|---:|---:|---:|
| Participant flow — started | **337** | **337** | 328 |
| **PRIMARY — treatment completion** | **294 / 337** | **248 / 335** | 250 / 326 |
| Secondary — *"Not advisable to continue study drugs"* | **2** | **5** | 2 |
| Secondary — drug toxicity causing permanent discontinuation | 12 | 18 | 14 |
| Secondary — grade 3/4 drug-related AE or death | 23 | 23 | 29 |

The denominators **337/337 are verified exactly**. The numerators **2 and 5 are
a real number from the source — from the wrong outcome**: the class *"Not
advisable to continue study drugs"*, **one of eight** reasons-for-failure-to-
complete categories, and a clinician-judgement administrative reason. It is not
TB disease, not treatment completion, and not a safety endpoint.

The trial's primary outcome — published as **87.2% (95% CI 83.1–90.5) DOT vs
74.0% (68.9–78.6) SAT** — is nowhere in the app.

Two further findings: iAdhere is a **non-inferiority** trial with a **15%
margin**, pooled here into a superiority odds ratio with the margin discarded;
and the **SAT+SMS arm is silently dropped**.

### 2.3 The sign conflict

The withdrawn pooled estimate combined a **good** outcome (negative culture,
OR<1 = worse) with a **bad** outcome (failure-to-complete reason, OR<1 = better)
on one odds-ratio scale, with no sign reconciliation. The app's own machine
verdict had already recorded *"2 AACT outcome-direction divergence(s)"*.

### 2.4 The evidence base is absent

According to PubMed, the landmark rifapentine-LTBI efficacy trial — **PREVENT TB
/ TBTC Study 26**, NCT00023452, Sterling TR et al, *N Engl J Med*
2011;365(23):2155-66, [PMID 22150035](https://doi.org/10.1056/NEJMoa1104875) —
reports **tuberculosis in 7 of 3986 (0.19%) with 3HP vs 15 of 3745 (0.43%) with
9H**, completion 82.1% vs 69.0% (P<0.001). It is the trial that underpins the
WHO recommendation for this regimen, and **it does not appear anywhere in the
app**.

Also absent, all confirmed by lookup:
[PMID 25904367](https://doi.org/10.1093/cid/civ323) (PREVENT TB systemic drug
reactions: 138/3893 with 3HP vs 15/3659 with 9H),
[PMID 30029896](https://doi.org/10.1016/j.tube.2018.05.013) (Taiwan 3HP vs 9H,
NCT02208427, n=263), and
[PMID 38996972](https://doi.org/10.1016/j.cmi.2024.06.024) (1HP vs 3HP,
NCT04094012, n=490).

> That list is what a lookup-based search surfaced on 2026-07-30. It is a
> starting set for a rebuild, **not a completed systematic search** — BRIEF-TB /
> A5279, WHIP3TB, V-QUIN and ASTERoiD were not verified in this pass.

*Bibliographic data in this section retrieved from **PubMed**.*

---

## 3. Gate results — and what each gate could not see

| Gate | Result | What it means here |
|---|---|---|
| **G1** per-arm count plausibility | **0 findings** | All cells non-negative integers with `e ≤ N`. **This gate is structurally blind to the defect** — fabricated cells are still valid integers |
| **G1b** contrast recompute | **0 findings** | logOR and variance recompute to **Δ = 0.00e+00**, exact. The pipeline is faithful to a corrupt input |
| **G2** GRIM / GRIMMER | **N/A** | Binary counts only; no mean of a bounded integer scale exists to test. Replaced by G1 |
| **G3** Benford | **N/A** | 8 digits total (2 trials × 4 cells) — far below a meaningful χ². A verdict here would be noise presented as evidence |
| **G4** arm balance | 2 advisories, **both benign as ratios** | 1.125:1 and 1.000:1. Both **mask a silent 3-arm→2-arm collapse**, which a ratio test cannot detect |
| **G5** identifiers | **2 findings** | **Zero PMIDs and zero DOIs anywhere in the app.** Both NCT IDs are well-formed and resolve |
| **G6** registry concordance | **2 of 2 covered — 2 of 2 FAIL** | Full coverage, and **the only gate that catches this** |
| **G7** fragility index | **N/A for both** | Fisher p = 0.2098 and p = 0.4507 — neither significant, so FI undefined. It would be meaningless anyway: **FI on a fabricated 2×2 measures nothing** |
| **G8** clone contamination | **BLOCKING** | see §4 |
| **G9** self-contradiction | **FAIL (pre-fix)** | green badge over a verdict recording 2 concordance failures and 2 of 2 trials missing evidence |
| **G10** anchor | **N/A** | No re-fit. The disposition is quarantine of the whole fit, not correction |

### Statistical findings

- **S1 (P1).** `pooled_DL` at **k = 2**. DerSimonian–Laird is biased for k<10;
  REML or Paule–Mandel is required. `tau2 = 0.0` from `Q = 0.00093` on df=1 is
  uninformative, and the reported **I² = 0.0% is an artefact of k=2**, not
  evidence of homogeneity.
- **S2 (P0).** The sign conflict in §2.3. Independently recomputed
  fixed-effect logOR **−0.944898**, matching the app's stored
  **−0.944897553936862** — the app computes correctly what it should not be
  computing at all.

---

## 4. Residual contamination

`scripts/clone_contamination_gate.py RIFAPENTINE_TB_AUTO_FULL_REVIEW.html`
→ **exit 1, BLOCKING**, finding `foreign_trial_registry_rendered`.

The app embeds:

```
KNOWN_TRIAL_ALIASES = { NCT01035255:["paradigm-hf","paradigm"],
                        NCT01920711:["paragon-hf","paragon"],
                        NCT02924727:["paradise-mi","paradise"],
                        NCT03988634:["paraglide-hf","paraglide"] }
```

Four **sacubitril/valsartan heart-failure** trials baked into a tuberculosis
app. This is the same base-engine survivor family as the SGLT2i adverse-event
contamination fixed in `d11d9f167`, but in a **different slot** (trial-alias
resolution) that the drug-class blocklist does not cover.

**Corpus scope: 526 apps carry this alias table; 56 of them are in the
global-health scope set.** Reported here, **not fixed** — corpus-wide
remediation is a separate batch.

The **SGLT2i adverse-event profile is clean** in this app: no `SGLT2`,
`Fournier`, `genital mycotic`, `diabetic ketoacidosis`, `DAPA-HF`, `EMPEROR`,
`DELIVER` or `EMPA-REG` strings survive.

---

## 5. Disposition

**Quarantine the entire fit.** Under *quarantine, never silent deletion*, both
trial rows are **retained in the ledger and flagged**, not deleted. The app
verifier **blocks if either NCT is removed** rather than flagged.

**No count was altered. Counts changed: 0.** There is no sourced value to
correct them to, because neither extraction corresponds to any outcome its
source reports.

| | Before | After |
|---|---:|---:|
| Trials in fit | 2 | **0** |
| Trials quarantined | 0 | **2** |
| Pooled OR | 0.389 (0.134–1.124) | **withdrawn** |
| Verdict | `STABLE` | **`FABRICATED`** |
| Badge | `#15803d` green, "INTERNAL CHECKS PASSED" | `#991b1b` red, "FABRICATED EXTRACTION — DO NOT CITE" |

**Reinstatement conditions.** NCT00814671: **not reinstatable at any count** in
an LTBI review — wrong population; it belongs in an active-TB-treatment review
if anywhere. NCT01582711: reinstatable if re-extracted against its **primary**
outcome (294/337 vs 248/335, PMID 29114781), with the non-inferiority margin
carried and the SMS arm handled explicitly.

> This is a provenance correction, **not** a result that got better or worse.
> Withdrawing an estimate is not evidence of anything about rifapentine. The
> actual evidence for 3HP — PREVENT TB — is strong and is simply not in this app.

---

## 6. Verification performed

| Check | Tool | Result |
|---|---|---|
| Badge replaced **wholesale** by balanced-`<div>` matching | `scripts/gh_apply_honest_badge.py` | span [83596:84565], 969 → 4624 bytes; div-balance delta preserved |
| Both surfaces agree | `scripts/gh_inventory.py` re-scan | `badge_disagreement: []`, `badge_green: False`, verdict `FABRICATED` |
| Structure / agreement / self-contradiction / quarantine / stale-value | `scripts/gh_verify_upgraded_app.py` | **PASS** |
| **Verifier negative-tested** | `--selftest` | **6 of 6 seeded defects BLOCK** (green badge restored; verdict → STABLE; p0_total zeroed; badge trial count contradicting spec; quarantined trial deleted; withdrawn pooled estimate reinstated) |
| JS parse | `scripts/jscheck.py` | `[JS-OK]` |
| Clone contamination | `scripts/clone_contamination_gate.py` | exit 1 — **blocking, reported not fixed** (§4) |

> The verifier earned its keep during this pass: its stale-value check fired on
> `INTERNAL CHECKS PASSED` surviving in the file. Investigation showed the only
> surviving instance was inside the new badge's own correction narrative. Check F
> was then scoped to claim-bearing surfaces **outside** the correction notice —
> the HFrEF precedent that a superseded value is *"gone except where the
> correction itself is documented."*

### Pre-existing condition, noted not fixed

The file carries a **div-balance delta of −1** (888 `<div` vs 889 `</div>`) that
predates this work. The badge edit **preserved** the delta exactly; the verifier
pins it via `--div-delta -1` so any future drift fails. Root-causing the −1 is
out of scope for this pilot.

---

## 7. Not done — explicit

1. **No rebuild.** Locating and extracting PREVENT TB, BRIEF-TB/A5279, WHIP3TB,
   V-QUIN, ASTERoiD and the Taiwan/1HP trials is a **build** task, not an audit
   task.
2. **No full-text verification** — all checks are against ClinicalTrials.gov
   posted results and PubMed abstracts.
3. **WHO lane not run** — Prequalification and the consolidated TB
   preventive-treatment guideline evidence tables were not consulted.
4. **Cochrane / prior-synthesis lane (L3) not run.**
5. **No live browser render** — the app was not served and driven in-browser
   this pass (recipe §7.8). Static structure and JS parse only.
6. **The 526-app `KNOWN_TRIAL_ALIASES` contamination is reported, not fixed.**
7. **Cross-family gate not run** — required before any push.

---

## Attribution

Registry data: **ClinicalTrials.gov API v2** (live, 2026-07-30).
Bibliographic data: **PubMed** (NCBI E-utilities). Fragility index per Walsh M
et al., *J Clin Epidemiol* 2014;67:622-628. Methodology adapted from
`outputs/HFREF_INTEGRITY_GATES_2026-07-30.md` and
`outputs/HFREF_FINDINGS_RESOLVED_2026-07-30.md`.

---

## 8. Defect found and fixed during the pilot (recorded for the batch)

**Line-ending drift on badge write.** The first application of the badge produced
a **6341-line / 6341-line diff** — a whole-file rewrite — because the corpus is
**CRLF** and `gh_apply_honest_badge.py` read with Python's default
universal-newline translation (CRLF → `\n`) while writing with `newline=""`
(passes `\n` through). Every line changed; the real 2-line edit was invisible.

Fixed at the source: `newline=""` on **both** read and write, preserving
endings verbatim. After the fix the same edit is a **2-line diff** with
`CRLF 6341 / bare LF 0` — byte-identical endings to `HEAD`.

**This must be checked on every app in the batch.** A whole-file rewrite defeats
review, and would have made the 56-app contamination remediation unreviewable.
Recipe §7 gains a check: *after any app edit, `git diff --numstat` must show a
line count proportional to the edit, not to the file.*
