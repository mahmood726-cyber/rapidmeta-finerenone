# Cardiology RapidMeta apps — inventory, triage, and program plan

**Date:** 2026-07-30 · **Branch:** `audit/cardio-program-2026-07-30` · **Status:** STAGED, NOT PUSHED
**Scope:** every `*_REVIEW.html` in the repo classified for cardiology content
**Scanner:** `scripts/cardio_inventory.py` (13 self-tests) → `outputs/cardio_inventory.json`
**Triage:** `scripts/cardio_triage.py` → `outputs/cardio_triage.json`
**Recipe:** `outputs/CARDIO_UPGRADE_RECIPE.md` · **Pilot:** `outputs/APIXABAN_ACS_PILOT_2026-07-30.md`

Read-only inventory. No app file was modified in producing this document.

---

## 1. What was scanned, and what the scanner does *not* see

1216 `*_REVIEW.html` files were read. **139 files / 107 unique apps** classify as
cardiology or cardiology-adjacent; 1077 files were excluded as non-cardiac.

Classification is keyed on drug and condition names in the filename **and** the app's own
`<title>`, because filenames lie (§2.4). Every exclusion below was confirmed by reading the
app's title, not inferred:

- **Substring false positives**, enumerated because a naive token list produces them:
  `elAFIBranor` → AFIB, `volunTEER` → TEER, `CRT` = chemoradiotherapy in `HEAD_NECK_CRT`,
  anti-amyloid Alzheimer's → cardiac amyloidosis, **ocular** hypertension.
- **Right drug class, non-cardiac indication:** ATTR *polyneuropathy* (vs ATTR-CM),
  tolvaptan in *ADPKD* (vs HF decongestion), sotagliflozin in *T1D* (vs HF),
  fenofibrate in *diabetic retinopathy*, elamipretide in primary mitochondrial disease.

**Two scanner defects were found and fixed during this pass, and they matter for the
numbers below.** The first version counted trials with a regex for `NCT\d{8}:` keys. Real
ledgers also use quoted keys (`"NCT01507831":`) and suffixed keys
(`NCT01206062_SENIOR:`), and the regex silently returned **0** for both — reporting
ALIROCUMAB_LIPID (6 trials), ROSUVASTATIN (2), INTENSIVE_BP and EMPAGLIFLOZIN_HF as
"empty templates". A real depth-1 JS key parser replaced it, with 13 regression tests
including those two exact cases. A second bug — an over-broad `_PE(D|DIATRIC)` exclusion
meant to stop `_PE_` matching "PEDIATRIC" — silently dropped `PEDIATRIC_HF_DAPA_NMA`, a
genuine heart-failure app. **Both were silent-zero failures, the class this whole program
exists to remove; the inventory was measuring itself wrong before it measured anything else.**

Still not seen, and stated rather than glossed:
- **6 apps store data outside `realData`** and read as `k=0` here: `HFREF_NMA`,
  `HSCTN_NSTEMI_DTA`, `SGLT2I_DOSE_RESP`, `DDIMER_PE_DTA`, `FINERENONE_ARTS_DN_DOSE_RESP`,
  `PROGNOSTIC_HSTN_PAD`. Each needs a bespoke reader. `k=0` for these means *unread*, not *empty*.
- **3 app classes are mixed in** and the intervention-MA recipe only partly applies:
  2 DTA apps, 1 prognostic-marker app, 2 dose-response apps.
- No app was rendered in a browser for this inventory. Badge state is read from source.

---

## 2. Headline findings

### 2.1 Badge dishonesty is the norm, not the exception — 75 of 107 apps

| Class | n | What it means |
|---|---:|---|
| **Badge says "INTERNAL CHECKS PASSED" while `window.__verdict` says `UNCERTAIN`** | **13** | A flat contradiction between the two surfaces. The machine verdict withholds confidence; the page asserts it. |
| **False green** — green "PASSED" badge over non-zero `P1_*`/`P2_*` counts or a non-empty `reasons[]` | **64** | The verdict object lists unresolved findings; the badge renders green over them. |
| **Either badge problem** | **75 / 107 (70%)** | |
| No badge and no `__verdict` at all | 11 | Mostly the 6 redirect-stub-only apps |
| Honest headline (`MANUAL REVIEW REQUIRED`, `LOW CONCERN`, or the HFrEF honest-limits badge) | 21 | |

75 of 107 apps carry the identical string **"INTERNAL CHECKS PASSED"**. Only **one** app in
the whole cardiology set carries a badge that names its own limits —
`HFREF_NMA` ("INTERNAL CHECKS -- READ WITH THE HONEST LIMITS"), the app we just fixed.

**The `reasons[]` array often already names the bug.** On the pilot it read
`"2 AACT outcome-direction divergence(s)"` — the exact defect the gates later confirmed as
CRITICAL — while the badge rendered green. The machinery is not blind. The badge is.

### 2.2 Trial counts disagree across surfaces in 55 of 107 apps

The three surfaces — visible badge `Trials: N`, `__verdict.n_trials_seen`, and the
`realData` ledger — disagree in **55 apps (51%)**. The usual pattern is a badge and verdict
asserting **2** over a ledger carrying **4**: the audit covered half the pooled evidence and
neither surface says so.

### 2.3 The evidence base is thin nearly everywhere

387 trial rows across 107 apps — a **mean k of 3.6**. **64 apps (60%) have k ≤ 4**;
**25 apps (23%) have k ≤ 2**. Two apps ship a **green "CHECKS PASSED · Trials: 2"** badge
over `realData:{}` — an **empty ledger, zero trials** (`EZETIMIBE_LIPID`, `LISINOPRIL_HTN`).
Both were verified by direct grep. 3 apps carry a ledger with **no PMIDs at all**, so no
row in them can be source-verified.

### 2.4 Two apps' filenames describe a different drug from their contents

Confirmed from each app's own `<title>`:

| File stem | What it actually contains |
|---|---|
| `TIRZEPATIDE_ARDS` | **Andexanet alfa** for FXa-inhibitor reversal |
| `ICAGEN` | **Edoxaban** TIMI-48 cancer-VTE |

(Two further codename stubs, `PYROXAMINE` and `BURADIRAGAB`, hold non-cardiac apps —
sotagliflozin T1D and rituximab in AAV/IgG4-RD — and are excluded from this inventory.)

### 2.5 Variant consistency is the one thing that is fine

Each app ships up to 4 file variants. Across the 32 apps with more than one non-stub
variant, **zero** disagree on trial count and **zero** disagree on verdict. Whatever
produced these apps applied itself consistently across variants. That is good news for
batch work: a fix designed once should apply cleanly to all variants of an app.

---

## 3. Triage — top 20 by upgrade value

Upgrade value = **clinical importance (1–5, by domain)** × **gap (0–10, additive from
evidence in the inventory)**. Every gap component is printed so the ranking can be argued
with; full detail for all 107 apps in `outputs/cardio_triage.json`.

Gap components: badge-says-PASSED-over-UNCERTAIN **+4** · false-green **+3** ·
empty ledger **+3** · green-badge-over-empty-ledger **+3** · counts disagree **+2** ·
no `__verdict` **+2** · filename≠content **+2** · ledger has no PMIDs **+2** ·
k≤2 **+2** · k=3–4 **+1** · orphan stub **+1** · non-`realData` architecture **+1**.

| # | App | Domain | Imp | Gap | UV | Why the gap is that size |
|---:|---|---|---:|---:|---:|---|
| 1 | `ALDO_SYNTHASE` | Hypertension | 4 | 10 | 40 | badge says PASSED while __verdict says UNCERTAIN; false-green badge over non-zero P1/P2 findings; trial counts disagree across surfaces; k=2 — too few to pool credibly |
| 2 | `EZETIMIBE_LIPID` | Lipids | 4 | 10 | 40 | false-green badge over non-zero P1/P2 findings; trial counts disagree across surfaces; realData:{} — template with NO trials; green badge over an EMPTY ledger |
| 3 | `INCLISIRAN` | Lipids | 4 | 10 | 40 | badge says PASSED while __verdict says UNCERTAIN; false-green badge over non-zero P1/P2 findings; trial counts disagree across surfaces; k=3 — thin evidence base |
| 4 | `LISINOPRIL_HTN` | Hypertension | 4 | 10 | 40 | false-green badge over non-zero P1/P2 findings; trial counts disagree across surfaces; realData:{} — template with NO trials; green badge over an EMPTY ledger |
| 5 | `ARNI_HF` | Heart failure | 5 | 7 | 35 | badge says PASSED while __verdict says UNCERTAIN; trial counts disagree across surfaces; k=4 — thin evidence base |
| 6 | `ATTR_CM` | Heart failure | 5 | 7 | 35 | badge says PASSED while __verdict says UNCERTAIN; trial counts disagree across surfaces; k=4 — thin evidence base |
| 7 | `EMPAGLIFLOZIN_HF` | Heart failure | 5 | 7 | 35 | false-green badge over non-zero P1/P2 findings; k=2 — too few to pool credibly; ledger carries no PMIDs |
| 8 | `INCRETIN_HFpEF` | Heart failure | 5 | 7 | 35 | badge says PASSED while __verdict says UNCERTAIN; trial counts disagree across surfaces; k=3 — thin evidence base |
| 9 | `IV_IRON_HF` | Heart failure | 5 | 7 | 35 | badge says PASSED while __verdict says UNCERTAIN; trial counts disagree across surfaces; k=4 — thin evidence base |
| 10 | `MAVACAMTEN_HCM` | Heart failure | 5 | 7 | 35 | badge says PASSED while __verdict says UNCERTAIN; trial counts disagree across surfaces; k=4 — thin evidence base |
| 11 | `ICAGEN` | Anticoagulation | 4 | 8 | 32 | false-green badge over non-zero P1/P2 findings; trial counts disagree across surfaces; filename does not describe content; k=3 — thin evidence base |
| 12 | `PCSK9` | Lipids | 4 | 8 | 32 | badge says PASSED while __verdict says UNCERTAIN; trial counts disagree across surfaces; k=2 — too few to pool credibly |
| 13 | `TIRZEPATIDE_ARDS` | Anticoagulation | 4 | 8 | 32 | false-green badge over non-zero P1/P2 findings; trial counts disagree across surfaces; filename does not describe content; k=3 — thin evidence base |
| 14 | `APIXABAN_ACS` | MI | 5 | 6 | 30 | false-green badge over non-zero P1/P2 findings; trial counts disagree across surfaces; k=4 — thin evidence base |
| 15 | `ABLATION_AF` | Atrial fibrillation | 4 | 7 | 28 | badge says PASSED while __verdict says UNCERTAIN; trial counts disagree across surfaces; k=4 — thin evidence base |
| 16 | `BEMPEDOIC_ACID` | Lipids | 4 | 7 | 28 | badge says PASSED while __verdict says UNCERTAIN; trial counts disagree across surfaces; k=4 — thin evidence base |
| 17 | `DOAC_CANCER_VTE` | Anticoagulation | 4 | 7 | 28 | badge says PASSED while __verdict says UNCERTAIN; trial counts disagree across surfaces; k=4 — thin evidence base |
| 18 | `RIVAROXABAN_VASC` | Anticoagulation | 4 | 7 | 28 | badge says PASSED while __verdict says UNCERTAIN; trial counts disagree across surfaces; k=4 — thin evidence base |
| 19 | `RIVAROXABAN_ACS` | MI | 5 | 5 | 25 | false-green badge over non-zero P1/P2 findings; k=2 — too few to pool credibly |
| 20 | `SOTAGLIFLOZIN_HF` | Heart failure | 5 | 5 | 25 | false-green badge over non-zero P1/P2 findings; k=2 — too few to pool credibly |

### Flagged classes, called out explicitly

**False-green over an EMPTY ledger (worst class, 2 apps).** `EZETIMIBE_LIPID` and
`LISINOPRIL_HTN` both carry a green `#15803d` "INTERNAL CHECKS PASSED · Trials: 2" badge and
a `__verdict` of `STABLE` with `n_trials_seen: 2`, over `realData:{}`. The page asserts that
checks passed on two trials it does not contain. Fix is a badge rewrite, not an extraction.

**Badge asserts PASSED over `__verdict: UNCERTAIN` (13 apps).** `ALDO_SYNTHASE`,
`INCLISIRAN`, `PCSK9`, `ARNI_HF`, `ATTR_CM`, `INCRETIN_HFpEF`, `IV_IRON_HF`,
`MAVACAMTEN_HCM`, `ABLATION_AF`, `BEMPEDOIC_ACID`, `DOAC_CANCER_VTE`, `RIVAROXABAN_VASC`,
`RENAL_DENERV`. Five of these are heart failure, the highest-importance domain.

**Filename does not match content (2 apps).** `TIRZEPATIDE_ARDS`, `ICAGEN` — see §2.4. Any
citation, share link, or index entry pointing at these by name misdescribes them.

**Orphan redirect stubs (6 apps).** `DAPAGLIFLOZIN_HFPEF`, `APIXABAN_CANCER_VTE`,
`EVOLOCUMAB_LIPID`, `INCLISIRAN_LIPID`, `RIVAROXABAN_PERIPHERAL`, `SILDENAFIL_PAH` exist
only as ~1.5 KB "opening the full RapidMeta…" redirects with no full app on this branch.
They need a target or removal — not an audit.

**Contaminated / borrowed data.** No cardio app in this pass showed the SGLT2i-lineage
residue that commit `d11d9f167` neutralised in 148 clones. But the pilot found a
**different** contamination class: `APIXABAN_ACS` pools **AUGUSTUS**, an atrial-fibrillation
trial comparing apixaban against a vitamin K antagonist, into an app asking about apixaban
versus placebo in ACS. That is borrowed evidence from a neighbouring PICO, and it is not
detectable by grepping for donor-app strings — only by checking each row's comparator and
population against the app's own question. **Every app in the batch needs the Phase-2.8
PICO check; a clean cross-contamination scan does not substitute for it.**

**Over-claims.** All 75 "INTERNAL CHECKS PASSED" badges claim `Multi-source audit completed
(AACT 2026-04-12 + PubMed + 10 internal-consistency rounds)`. On the pilot the very next
sentence of the same badge says **14** rounds — the badge contradicts itself inside its own
body, the same defect class as the HFrEF 28-vs-27 leftover. The claim also names an AACT
snapshot whose concordance is unverified. And `P0_grim: 0` reads as a GRIM pass when GRIM is
**not applicable** to binary per-arm counts.

---

## 4. Pilot result (summary; full report in `outputs/APIXABAN_ACS_PILOT_2026-07-30.md`)

`APIXABAN_ACS` (rank 14, importance 5, k=4) was taken end-to-end. All four trials have
posted ClinicalTrials.gov results, so every number was checkable. **Not one of the eight arm
rows survived verification.**

- **9 CRITICAL, 9 HIGH, 1 MEDIUM, 4 ADVISORY findings.** Gate exits non-zero.
- **The counts in two of four trials are arithmetically manufactured.** APPRAISE-2's 515 and
  489 are exactly `3687 × 13.96/100` and `3705 × 13.20/100` from a posted outcome whose unit
  is **events per 100 patient-years** — a rate, not a proportion. The real counts are 279 and
  293. AUGUSTUS's 284 and 413 are `1153 × 24.66/100` and `1153 × 35.79/100` from
  `"Percentage per year"`, on a denominator (1153) that corresponds to **no arm of the trial**.
- **Three of four trials have their arms swapped**, because ClinicalTrials.gov lists placebo
  first and the extractor bound arms by group *index*.
- **APPRAISE-J's 17 and 19 reconcile with nothing.** The paper says 2, 2 and 1 events; the
  registry's recoverable counts are 1 and 2.
- **The cited AUGUSTUS paper is the protocol paper** (PMID 29898844, PubMed type "Clinical
  Trial Protocol"), which reports no results. The results paper is PMID 30883055.
- **The consequence: the correction flips the sign.** As pooled now, Mantel-Haenszel
  OR **0.850 (0.780–0.926)**, favouring apixaban. The verified synthesis of the coherent
  PICO gives OR **1.975 (1.223–3.189)** — apixaban roughly **doubles** major/CRNM bleeding.
  Both nominally significant, on opposite sides of 1.0. The live app is wrong about the one
  finding that terminated APPRAISE-2 and ended apixaban's development in ACS.

**The pilot changed the recipe.** Three gates now exist that did not before: **G6b**
rate-vs-proportion units, **G6c** arm orientation, **G6d** posted-results reconcilability.
G6b and G6d are the two that found the manufactured and unsourced counts.

---

## 5. Per-app effort estimate

Measured on the pilot, split by phase (see the recipe for phase numbering):

| Phase | Work | Pilot actual |
|---|---|---|
| 0 | Preflight: variants, identity, ledger read | ~5 min |
| 1 | Grep both verdict surfaces | ~10 min |
| 2 | **Source-verify every number** — PubMed + registry + posted results per trial | **~20 min per trial** |
| 3 | Run the gate battery (automated) | ~2 min |
| 4 | Disposition each finding | ~5 min per finding |
| 5 | Measure the consequence (re-fit, anchor table) | ~20 min |
| 6 | Rewrite the badge honestly, both surfaces | ~20 min |
| 7 | Transparency ledger | ~15 min |
| 8 | Verify artefact + render + commit | ~20 min |

**Per-app: roughly `95 min + 20·k + 5·findings`.**

At the corpus mean of k=3.6 and the pilot's finding rate, that is **~4 hours per app** for a
first pass with a real fix. The pilot itself took about that, and it was the *first* run —
but it also **built** the gate battery, which the next app inherits for free. Steady-state,
with the gates in place and no new gate development:

- **k ≤ 2 app: ~2 h** · **k = 3–4: ~3 h** · **k = 5–10: ~4–6 h**
- **107 apps ≈ 320–400 hours** of lane time for the full cardiology set.

Two cheap accelerants, both grounded in what this pass measured:
- **Badge-only fixes are ~30 min** and need no source verification: the 2 empty-ledger apps
  and the 6 orphan stubs are pure honesty fixes (Phase 1 + 6 + 8 only). 8 apps, ~4 hours total.
- **Variants are consistent** (§2.5), so a fix designed once applies to all variants of an
  app without redesign.

---

## 6. Proposed batch order

Batches of 5–8 with a checkpoint after each, per `rules/rules.md` scope discipline.
**Nothing pushes** until a cross-family gate clears it.

| Batch | Apps | Rationale | Est. |
|---|---|---|---|
| **B0 — honesty-only, no extraction** | `EZETIMIBE_LIPID`, `LISINOPRIL_HTN` + the 6 orphan stubs | Highest dishonesty per unit effort. A green "CHECKS PASSED · Trials: 2" over an empty ledger is indefensible and takes 30 min to fix. Ships the badge-rewrite + self-contradiction verifier the rest of the program reuses. | ~4 h |
| **B1 — heart failure, PASSED-over-UNCERTAIN** | `ARNI_HF`, `ATTR_CM`, `INCRETIN_HFpEF`, `IV_IRON_HF`, `MAVACAMTEN_HCM`, `EMPAGLIFLOZIN_HF` | Importance 5, flat badge contradiction, and adjacent to the HFrEF work so the domain knowledge and quarantine machinery carry over. `EMPAGLIFLOZIN_HF` additionally has **no PMIDs**. | ~20 h |
| **B2 — ACS / antiplatelet** | `APIXABAN_ACS` (finish the pilot), `RIVAROXABAN_ACS`, `ACS_ANTIPLATELET`, `CANGRELOR_PCI`, `DAPT_DE_ESCALATION_PCI`, `CABG_VS_PCI_LEFT_MAIN_NMA` | Importance 5. The pilot proves the unit-error and arm-swap defects are here; `ACS_ANTIPLATELET` and `DAPT_DE_ESCALATION_PCI` already return 8 and 10 CRITICAL findings on a gate run. | ~25 h |
| **B3 — anticoagulation / VTE** | `ICAGEN`, `TIRZEPATIDE_ARDS` (both also need renaming), `DOAC_CANCER_VTE`, `RIVAROXABAN_VASC`, `ANDEXANET_BLEEDING`, `DABIGATRAN_VTE`, `EDOXABAN_VTE`, `EDOXABAN_CANCER_VTE` | The largest domain (28 files). Two filename-content fixes belong here. AUGUSTUS-style comparator mixing is most likely in this domain. | ~30 h |
| **B4 — lipids** | `INCLISIRAN`, `PCSK9`, `BEMPEDOIC_ACID`, `ALIROCUMAB_LIPID`, `BOCOCIZUMAB_LIPID`, `MIPOMERSEN_HOFH`, `PCSK9_LIPID_NMA` | 25 files, mostly surrogate (LDL) endpoints — the co-primary/surrogate-marking lesson applies hardest here. | ~25 h |
| **B5 — hypertension + AF** | `ALDO_SYNTHASE`, `RENAL_DENERV`, `AZILSARTAN_HTN`, `OLMESARTAN_HTN`, `INTENSIVE_BP`, `ABLATION_AF`, `APIXABAN_AF`, `DOAC_AF` | `ALDO_SYNTHASE` is rank 1 overall but k=2; batching it with the domain is more efficient than a solo run. | ~28 h |
| **B6 — structural, PH, devices, stroke, adjacent** | remaining ~60 apps | Lower importance; several are NMAs needing the indirect-estimate / fragility-undefined treatment in full. | ~200 h |
| **B7 — the 6 non-`realData` apps** | `HFREF_NMA`, `HSCTN_NSTEMI_DTA`, `SGLT2I_DOSE_RESP`, `DDIMER_PE_DTA`, `FINERENONE_ARTS_DN_DOSE_RESP`, `PROGNOSTIC_HSTN_PAD` | Each needs a bespoke reader first, and 3 are DTA / prognostic / dose-response classes the intervention recipe only partly covers. Do last, deliberately. | ~20 h |

**Why B0 first rather than the highest-UV app.** `ALDO_SYNTHASE` scores 40 and B0's apps
score 40 and 16. But B0 needs no source verification at all, ships the badge-rewrite tooling
and the self-contradiction verifier that every later batch depends on, and removes the two
most flatly indefensible pages in the set in an afternoon. Build the tool on the easy case,
then use it 99 times.

---

## 7. What this program should NOT claim

- **The gates are not a pass.** Running them converts "untested" into "tested, with N
  findings". Only 5 of the 13 gates apply to every app; GRIM is N/A on binary counts and
  registry concordance is N/A for unregistered trials. **N/A is not a pass.**
- **Verification here is 2-source**, not the 4-source triangulation the recipe targets. The
  pilot reached the primary publication and ClinicalTrials.gov posted results. **FDA/EMA
  review documents and prior published/Cochrane meta-analyses were not consulted for any
  app.** No badge should say "multi-source" on the strength of two.
- **No app has been rendered** for this inventory. On HFrEF, serving the page and reading
  the DOM caught a badge contradiction that a passing file-level gate had missed. Phase 8.2
  is not optional.
- **Nothing is pushed, and push is not deploy.** Every artefact here is staged on
  `audit/cardio-program-2026-07-30`. `main` is the deploy ref; a push to this branch would
  create a remote branch and deploy nothing.
- **This inventory measured its own scanner wrong twice** before it was right (§1). The
  scanner now has 15 self-tests, including a proof that the gate exits non-zero on a
  known-bad ledger and zero on a known-good one. Re-run
  `python scripts/test_cardio_inventory.py` before trusting any number above.

---

## Appendix - full inventory by domain

Legend: **EMPTY** = `realData:{}` (template, zero trials); stub-only = redirect stub with no full app on this branch; other-arch = data stored outside `realData` and therefore unread by this scanner. Badge k = the `Trials: N` figure printed on the visible badge. UV = upgrade value.

### Heart failure — 16 apps / 18 files (importance 5/5)

| App | k | Data | `__verdict` | Visible badge | Badge k | Surfaces agree? | Badge state | UV |
|---|---:|---|---|---|---:|:-:|---|---:|
| `ARNI_HF` | 4 | real | UNCERTAIN | INTERNAL CHECKS PASSED | 4 | **NO** | **PASSED-over-UNCERTAIN** | 35 |
| `ATTR_CM` | 4 | real | UNCERTAIN | INTERNAL CHECKS PASSED | 4 | **NO** | **PASSED-over-UNCERTAIN** | 35 |
| `EMPAGLIFLOZIN_HF` | 2 | real | STABLE | INTERNAL CHECKS PASSED | 2 | yes | false-green | 35 |
| `INCRETIN_HFpEF` | 3 | real | UNCERTAIN | INTERNAL CHECKS PASSED | 3 | **NO** | **PASSED-over-UNCERTAIN** | 35 |
| `IV_IRON_HF` | 4 | real | UNCERTAIN | INTERNAL CHECKS PASSED | 4 | **NO** | **PASSED-over-UNCERTAIN** | 35 |
| `MAVACAMTEN_HCM` | 4 | real | UNCERTAIN | INTERNAL CHECKS PASSED | 4 | **NO** | **PASSED-over-UNCERTAIN** | 35 |
| `SOTAGLIFLOZIN_HF` | 2 | real | STABLE | INTERNAL CHECKS PASSED | 2 | yes | false-green | 25 |
| `PEDIATRIC_HF_DAPA_NMA` | 2 | real | STABLE | MANUAL REVIEW REQUIRED | 2 | **NO** | ok | 20 |
| `DAPAGLIFLOZIN_HFPEF` | 0 | stub-only | ABSENT | — | — | yes | no badge | 15 |
| `HFREF_NMA` | 0 | other-arch | STABLE | INTERNAL CHECKS -- READ WITH | — | **NO** | ok | 15 |
| `HF_QUADRUPLE_NMA` | 6 | real | STABLE | INTERNAL CHECKS PASSED | 6 | yes | false-green | 15 |
| `SGLT2I_DOSE_RESP` | 0 | other-arch | ABSENT | — | — | yes | no badge | 15 |
| `SGLT2I_HF_NMA` | 6 | real | STABLE | INTERNAL CHECKS PASSED | 6 | yes | false-green | 15 |
| `SGLT2_HF` | 5 | real | STABLE | INTERNAL CHECKS PASSED | 5 | yes | false-green | 15 |
| `ACUTE_HF_DIURESIS_NEW` | 10 | real | STABLE | LOW CONCERN | 10 | **NO** | ok | 10 |
| `FCM_HF` | 5 | real | STABLE | LOW CONCERN | 5 | yes | ok | 0 |

### MI / ACS / IHD — 8 apps / 10 files (importance 5/5)

| App | k | Data | `__verdict` | Visible badge | Badge k | Surfaces agree? | Badge state | UV |
|---|---:|---|---|---|---:|:-:|---|---:|
| `APIXABAN_ACS` | 4 | real | STABLE | INTERNAL CHECKS PASSED | 2 | **NO** | false-green | 30 |
| `RIVAROXABAN_ACS` | 2 | real | STABLE | INTERNAL CHECKS PASSED | 2 | yes | false-green | 25 |
| `ACS_ANTIPLATELET` | 4 | real | STABLE | INTERNAL CHECKS PASSED | 4 | yes | false-green | 20 |
| `CANGRELOR_PCI` | 3 | real | STABLE | INTERNAL CHECKS PASSED | 3 | yes | false-green | 20 |
| `EVT_LARGECORE` | 6 | real | STABLE | INTERNAL CHECKS PASSED | 6 | yes | false-green | 15 |
| `HSCTN_NSTEMI_DTA` | 0 | other-arch | ABSENT | — | — | yes | no badge | 15 |
| `CABG_VS_PCI_LEFT_MAIN_NMA` | 8 | real | STABLE | MANUAL REVIEW REQUIRED | 8 | **NO** | ok | 10 |
| `DAPT_DE_ESCALATION_PCI` | 10 | real | STABLE | LOW CONCERN | 10 | **NO** | ok | 10 |

### Anticoagulation / VTE — 18 apps / 28 files (importance 4/5)

| App | k | Data | `__verdict` | Visible badge | Badge k | Surfaces agree? | Badge state | UV |
|---|---:|---|---|---|---:|:-:|---|---:|
| `ICAGEN` | 3 | real | STABLE | INTERNAL CHECKS PASSED | 2 | **NO** | false-green | 32 |
| `TIRZEPATIDE_ARDS` | 3 | real | STABLE | INTERNAL CHECKS PASSED | 2 | **NO** | false-green | 32 |
| `DOAC_CANCER_VTE` | 4 | real | UNCERTAIN | INTERNAL CHECKS PASSED | 4 | **NO** | **PASSED-over-UNCERTAIN** | 28 |
| `RIVAROXABAN_VASC` | 4 | real | UNCERTAIN | INTERNAL CHECKS PASSED | 4 | **NO** | **PASSED-over-UNCERTAIN** | 28 |
| `ANDEXANET_BLEEDING` | 3 | real | STABLE | INTERNAL CHECKS PASSED | 2 | **NO** | false-green | 24 |
| `DABIGATRAN_VTE` | 4 | real | STABLE | INTERNAL CHECKS PASSED | 2 | **NO** | false-green | 24 |
| `EDOXABAN_CANCER_VTE` | 3 | real | STABLE | INTERNAL CHECKS PASSED | 2 | **NO** | false-green | 24 |
| `EDOXABAN_VTE` | 3 | real | STABLE | INTERNAL CHECKS PASSED | 2 | **NO** | false-green | 24 |
| `ENOXAPARIN_VTE` | 3 | real | STABLE | INTERNAL CHECKS PASSED | 2 | **NO** | false-green | 24 |
| `FONDAPARINUX` | 4 | real | STABLE | INTERNAL CHECKS PASSED | 2 | **NO** | false-green | 24 |
| `APIXABAN_VTE` | 2 | real | STABLE | INTERNAL CHECKS PASSED | 2 | yes | false-green | 20 |
| `ARGATROBAN_HIT` | 2 | real | STABLE | INTERNAL CHECKS PASSED | 2 | yes | false-green | 20 |
| `DABIGATRAN_STROKE` | 2 | real | STABLE | INTERNAL CHECKS PASSED | 2 | yes | false-green | 20 |
| `FONDAPARINUX_VTE` | 2 | real | STABLE | INTERNAL CHECKS PASSED | 2 | yes | false-green | 20 |
| `DOAC_VTE_NMA` | 4 | real | STABLE | INTERNAL CHECKS PASSED | 4 | yes | false-green | 16 |
| `APIXABAN_CANCER_VTE` | 0 | stub-only | ABSENT | — | — | yes | no badge | 12 |
| `DDIMER_PE_DTA` | 0 | other-arch | ABSENT | — | — | yes | no badge | 12 |
| `RIVAROXABAN_PERIPHERAL` | 0 | stub-only | ABSENT | — | — | yes | no badge | 12 |

### Atrial fibrillation / arrhythmia — 10 apps / 14 files (importance 4/5)

| App | k | Data | `__verdict` | Visible badge | Badge k | Surfaces agree? | Badge state | UV |
|---|---:|---|---|---|---:|:-:|---|---:|
| `ABLATION_AF` | 4 | real | UNCERTAIN | INTERNAL CHECKS PASSED | 4 | **NO** | **PASSED-over-UNCERTAIN** | 28 |
| `APIXABAN_AF` | 4 | real | STABLE | INTERNAL CHECKS PASSED | 2 | **NO** | false-green | 24 |
| `DABIGATRAN_AF` | 2 | real | STABLE | INTERNAL CHECKS PASSED | 2 | yes | false-green | 20 |
| `ETRIPAMIL_PAROXYSMAL_SUPRAVENTRICU` | 2 | real | STABLE | INTERNAL CHECKS PASSED | 2 | yes | false-green | 20 |
| `VT_ABLATION_NEW_NMA` | 4 | real | STABLE | LOW CONCERN | 4 | **NO** | ok | 20 |
| `WARFARIN_AF` | 2 | real | STABLE | INTERNAL CHECKS PASSED | 2 | yes | false-green | 20 |
| `DOAC_AF` | 4 | real | STABLE | INTERNAL CHECKS PASSED | 4 | yes | false-green | 16 |
| `DOAC_AF_NMA` | 4 | real | STABLE | INTERNAL CHECKS PASSED | 4 | yes | false-green | 16 |
| `PFA_AF_PULSED_FIELD` | 4 | real | STABLE | MANUAL REVIEW REQUIRED | 4 | **NO** | ok | 12 |
| `CRYO_AF_ABLATION_NMA` | 7 | real | STABLE | LOW CONCERN | 7 | **NO** | ok | 8 |

### Hypertension (systemic) — 6 apps / 9 files (importance 4/5)

| App | k | Data | `__verdict` | Visible badge | Badge k | Surfaces agree? | Badge state | UV |
|---|---:|---|---|---|---:|:-:|---|---:|
| `ALDO_SYNTHASE` | 2 | real | UNCERTAIN | INTERNAL CHECKS PASSED | 2 | **NO** | **PASSED-over-UNCERTAIN** | 40 |
| `LISINOPRIL_HTN` | 0 | **EMPTY** | STABLE | INTERNAL CHECKS PASSED | 2 | **NO** | false-green | 40 |
| `AZILSARTAN_HTN` | 4 | real | STABLE | INTERNAL CHECKS PASSED | 2 | **NO** | false-green | 24 |
| `OLMESARTAN_HTN` | 3 | real | STABLE | INTERNAL CHECKS PASSED | 2 | **NO** | false-green | 24 |
| `RENAL_DENERV` | 6 | real | UNCERTAIN | INTERNAL CHECKS PASSED | 6 | **NO** | **PASSED-over-UNCERTAIN** | 24 |
| `INTENSIVE_BP` | 5 | real | STABLE | INTERNAL CHECKS PASSED | 5 | yes | false-green | 12 |

### Lipids — 17 apps / 25 files (importance 4/5)

| App | k | Data | `__verdict` | Visible badge | Badge k | Surfaces agree? | Badge state | UV |
|---|---:|---|---|---|---:|:-:|---|---:|
| `EZETIMIBE_LIPID` | 0 | **EMPTY** | STABLE | INTERNAL CHECKS PASSED | 2 | **NO** | false-green | 40 |
| `INCLISIRAN` | 3 | real | UNCERTAIN | INTERNAL CHECKS PASSED | 3 | **NO** | **PASSED-over-UNCERTAIN** | 40 |
| `PCSK9` | 2 | real | UNCERTAIN | INTERNAL CHECKS PASSED | 2 | **NO** | **PASSED-over-UNCERTAIN** | 32 |
| `BEMPEDOIC_ACID` | 4 | real | UNCERTAIN | INTERNAL CHECKS PASSED | 4 | **NO** | **PASSED-over-UNCERTAIN** | 28 |
| `INCLISIRAN_LIPID_KIDNEY` | 3 | real | STABLE | INTERNAL CHECKS PASSED | 2 | **NO** | false-green | 24 |
| `MIPOMERSEN_HOFH` | 4 | real | STABLE | INTERNAL CHECKS PASSED | 2 | **NO** | false-green | 24 |
| `ALIROCUMAB_LIPID` | 6 | real | STABLE | INTERNAL CHECKS PASSED | 2 | **NO** | false-green | 20 |
| `BOCOCIZUMAB_LIPID` | 5 | real | STABLE | INTERNAL CHECKS PASSED | 2 | **NO** | false-green | 20 |
| `EVOLOCUMAB_DYSLIPIDEMIA` | 2 | real | STABLE | INTERNAL CHECKS PASSED | 2 | yes | false-green | 20 |
| `EVOLOCUMAB_MIXED_DYSLIPIDEMIA` | 2 | real | STABLE | INTERNAL CHECKS PASSED | 2 | yes | false-green | 20 |
| `ICOSAPENT_LIPID` | 2 | real | STABLE | INTERNAL CHECKS PASSED | 2 | yes | false-green | 20 |
| `PITAVASTATIN` | 2 | real | STABLE | INTERNAL CHECKS PASSED | 2 | yes | false-green | 20 |
| `ROSUVASTATIN` | 2 | real | STABLE | INTERNAL CHECKS PASSED | 2 | yes | false-green | 20 |
| `PCSK9_INHIBITORS_CV` | 2 | real | STABLE | LOW CONCERN | 10 | **NO** | ok | 16 |
| `PCSK9_LIPID_NMA` | 4 | real | STABLE | INTERNAL CHECKS PASSED | 4 | yes | false-green | 16 |
| `EVOLOCUMAB_LIPID` | 0 | stub-only | ABSENT | — | — | yes | no badge | 12 |
| `INCLISIRAN_LIPID` | 0 | stub-only | ABSENT | — | — | yes | no badge | 12 |

### CV prevention / cardiorenal CV outcomes (adjacent) — 9 apps / 9 files (importance 3/5)

| App | k | Data | `__verdict` | Visible badge | Badge k | Surfaces agree? | Badge state | UV |
|---|---:|---|---|---|---:|:-:|---|---:|
| `MEDITERRANEAN_DIET_CV` | 2 | real | STABLE | INTERNAL CHECKS PASSED | 3 | **NO** | false-green | 21 |
| `FINERENONE` | 4 | real | STABLE | INTERNAL CHECKS PASSED | 4 | **NO** | false-green | 18 |
| `SGLT2_MACE_CVOT` | 4 | real | STABLE | INTERNAL CHECKS PASSED | 4 | yes | false-green | 12 |
| `CARDIORENAL_DKD_NMA` | 6 | real | STABLE | INTERNAL CHECKS PASSED | 6 | yes | false-green | 9 |
| `FINERENONE_ARTS_DN_DOSE_RESP` | 0 | other-arch | ABSENT | — | — | yes | no badge | 9 |
| `GLP1_CVOT` | 10 | real | STABLE | INTERNAL CHECKS PASSED | 10 | yes | false-green | 9 |
| `GLP1_CVOT_NMA` | 8 | real | MODERATE | INTERNAL CHECKS PASSED | 8 | yes | false-green | 9 |
| `HYPERKALEMIA_K_BINDER_NMA` | 8 | real | STABLE | MANUAL REVIEW REQUIRED | 8 | **NO** | ok | 6 |
| `OMEGA3_HIGHDOSE_CV` | 5 | real | STABLE | LOW CONCERN | 5 | yes | ok | 0 |

### Cardiac devices / procedures — 2 apps / 2 files (importance 3/5)

| App | k | Data | `__verdict` | Visible badge | Badge k | Surfaces agree? | Badge state | UV |
|---|---:|---|---|---|---:|:-:|---|---:|
| `CARDIAC_CONTRACTILITY_MOD_NMA` | 2 | real | STABLE | LOW CONCERN | 2 | **NO** | ok | 12 |
| `INTRAVASCULAR_LITHOTRIPSY_NMA` | 5 | real | STABLE | MANUAL REVIEW REQUIRED | 5 | yes | ok | 6 |

### Pulmonary hypertension / pulmonary vascular — 8 apps / 11 files (importance 3/5)

| App | k | Data | `__verdict` | Visible badge | Badge k | Surfaces agree? | Badge state | UV |
|---|---:|---|---|---|---:|:-:|---|---:|
| `PAH_THERAPY` | 4 | real | STABLE | INTERNAL CHECKS PASSED | 4 | **NO** | false-green | 18 |
| `RIOCIGUAT_PAH` | 4 | real | STABLE | INTERNAL CHECKS PASSED | 2 | **NO** | false-green | 18 |
| `BOSENTAN_PAH` | 2 | real | STABLE | INTERNAL CHECKS PASSED | 2 | yes | false-green | 15 |
| `SOTATERCEPT_PAH` | 2 | real | STABLE | INTERNAL CHECKS PASSED | 2 | yes | false-green | 15 |
| `SOTATERCEPT_PAH_AUTO_2` | 2 | real | STABLE | INTERNAL CHECKS PASSED | 2 | yes | false-green | 15 |
| `SILDENAFIL_PAH` | 0 | stub-only | ABSENT | — | — | yes | no badge | 9 |
| `CTEPH_NMA` | 7 | real | STABLE | LOW CONCERN | 7 | **NO** | ok | 6 |
| `PAH_SOTATERCEPT_BROAD` | 10 | real | STABLE | LOW CONCERN | 10 | **NO** | ok | 6 |

### Stroke (cardioembolic/cerebrovascular) — 3 apps / 3 files (importance 3/5)

| App | k | Data | `__verdict` | Visible badge | Badge k | Surfaces agree? | Badge state | UV |
|---|---:|---|---|---|---:|:-:|---|---:|
| `EVT_BASILAR` | 3 | real | STABLE | INTERNAL CHECKS PASSED | 3 | yes | false-green | 12 |
| `EVT_EXTENDED_WINDOW` | 3 | real | STABLE | INTERNAL CHECKS PASSED | 3 | yes | false-green | 12 |
| `TNK_VS_TPA_STROKE` | 6 | real | MODERATE | INTERNAL CHECKS PASSED | 6 | yes | false-green | 9 |

### Valvular / structural — 6 apps / 6 files (importance 3/5)

| App | k | Data | `__verdict` | Visible badge | Badge k | Surfaces agree? | Badge state | UV |
|---|---:|---|---|---|---:|:-:|---|---:|
| `PFO_STROKE_CLOSURE_NMA` | 7 | real | STABLE | INTERNAL CHECKS PASSED | 7 | **NO** | false-green | 15 |
| `MITRAL_FUNCMR` | 3 | real | STABLE | INTERNAL CHECKS PASSED | 3 | yes | false-green | 12 |
| `TAVR_LOW_RISK` | 5 | real | STABLE | INTERNAL CHECKS PASSED | 5 | yes | false-green | 9 |
| `MITRACLIP_TEER` | 6 | real | STABLE | LOW CONCERN | 6 | **NO** | ok | 6 |
| `TRICUSPID_TEER_TMVR_NMA` | 6 | real | STABLE | MANUAL REVIEW REQUIRED | 6 | **NO** | ok | 6 |
| `WATCHMAN_LAAO_NMA` | 6 | real | STABLE | MANUAL REVIEW REQUIRED | 6 | **NO** | ok | 6 |

### Pericardial / myocarditis — 2 apps / 2 files (importance 2/5)

| App | k | Data | `__verdict` | Visible badge | Badge k | Surfaces agree? | Badge state | UV |
|---|---:|---|---|---|---:|:-:|---|---:|
| `COLCHICINE_CVD` | 5 | real | STABLE | INTERNAL CHECKS PASSED | 5 | **NO** | false-green | 10 |
| `RECURRENT_PERICARDITIS_NMA` | 2 | real | STABLE | LOW CONCERN | 2 | **NO** | ok | 8 |

### Peripheral arterial — 2 apps / 2 files (importance 2/5)

| App | k | Data | `__verdict` | Visible badge | Badge k | Surfaces agree? | Badge state | UV |
|---|---:|---|---|---|---:|:-:|---|---:|
| `PROGNOSTIC_HSTN_PAD` | 0 | other-arch | ABSENT | — | — | yes | no badge | 6 |
| `PERIPHERAL_DCB_PAD_NMA` | 10 | real | STABLE | MANUAL REVIEW REQUIRED | 10 | **NO** | ok | 4 |
