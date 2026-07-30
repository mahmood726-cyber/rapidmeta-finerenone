# RAPIDMETA ERROR SWEEP

**Generated:** 2026-07-30 · **Registry:** `RAPIDMETA_ERROR_REGISTRY.md` v1.0 · **Mode:** READ-ONLY DETECTION — no file was modified.

**Command:** `python scripts/rapidmeta_error_sweep.py`

Every STATIC detector in the registry applied to every `*_REVIEW.html` in the repo. SOURCE- and RENDER-class detectors are **not** in these counts — they need a registry lookup or a browser, and their absence is a limit of this sweep, not a clean result.

## 1. Corpus

| | count |
|---|---:|
| `*_REVIEW.html` files matched | 1659 |
| Apps scanned (>= 20 KB) | 1088 |
| Redirect stubs skipped (< 20 KB) | 571 |
| Apps with **zero** static findings | 0 (0.0%) |
| Apps with >= 1 finding | 1088 (100.0%) |
| Detectors run | 52 |
| Files where a detector raised | 0 |
| **Apps whose `realData` ledger did not parse** (ledger detectors blind there) | **19** |

> A ledger that does not parse is a **finding about the app**, not a clean result. Every `RM-A*`, `RM-C*`, `RM-D*` and `RM-G02` count below is measured on 1069 apps, not 1088. Full list in the JSON (`unparsable_ledgers`).

## 2. Prevalence — apps affected per error type

| id | error type | sev | apps | % of apps | evidence items |
|---|---|---|---:|---:|---:|
| `RM-F05` | Missing rendered as zero | P1 | 1059 | 97.3% | 2233 |
| `RM-I01` | Direction inversion risk (no explicit polarity) | P1 | 1053 | 96.8% | 2059 |
| `RM-H01` | k-inappropriate machinery | P1 | 1049 | 96.4% | 7045 |
| `RM-E01` | Cross-topic template contamination | P0 | 1035 | 95.1% | 4158 |
| `RM-J07` | Integrity gate passes over a fail-closed condition | P0 | 1030 | 94.7% | 1030 |
| `RM-B03` | Silent endpoint fallback | P0 | 1024 | 94.1% | 1024 |
| `RM-B02` | Stale outcome-state leakage | P0 | 1010 | 92.8% | 1754 |
| `RM-G01` | safeRob unknown -> low | P0 | 1006 | 92.5% | 2012 |
| `RM-J01` | False ICMJE / PROSPERO equivalence attribution | P0 | 1006 | 92.5% | 1799 |
| `RM-H04` | N/A gate reported as a pass | P1 | 999 | 91.8% | 1775 |
| `RM-F04` | Interface state desync | P2 | 991 | 91.1% | 991 |
| `RM-H02` | Inadmissible estimator / uninterpretable tau2 at small k | P1 | 976 | 89.7% | 976 |
| `RM-B01` | Scope-lock failure | P0 | 939 | 86.3% | 939 |
| `RM-A02` | Estimand mixing in one pool | P0 | 810 | 74.4% | 819 |
| `RM-J02` | Retrospective protocol framed as prospective | P1 | 808 | 74.3% | 862 |
| `RM-H05` | External-validation claim vs a different-scope benchmark | P1 | 807 | 74.2% | 807 |
| `RM-F01` | False-green verdict badge | P0 | 802 | 73.7% | 1668 |
| `RM-F03` | Badge self-contradiction | P0 | 802 | 73.7% | 802 |
| `RM-D08` | False registry-status claim | P1 | 767 | 70.5% | 767 |
| `RM-A05` | Continuous outcome in a ratio model | P0 | 748 | 68.8% | 748 |
| `RM-A14` | escalc(measure=RR) over rows the ledger tags as different endpoints | P0 | 744 | 68.4% | 784 |
| `RM-E02` | Foreign trial-alias registry | P1 | 716 | 65.8% | 716 |
| `RM-G03` | RoB chip contradicts the trial's own extraction evidence | P1 | 701 | 64.4% | 1023 |
| `RM-F02` | Verdict-surface disagreement | P0 | 596 | 54.8% | 1146 |
| `RM-D10` | Duplicate, NULLED or ghost trial rows | P0 | 512 | 47.1% | 813 |
| `RM-D05` | Fabricated / imported analysis row | P1 | 351 | 32.3% | 1909 |
| `RM-A07` | Non-ratio quantity in a ratio field | P0 | 315 | 29.0% | 2449 |
| `RM-J05` | COMPLETED-only registry filter | P2 | 216 | 19.9% | 216 |
| `RM-H03` | Fragility index where undefined | P1 | 207 | 19.0% | 207 |
| `RM-D07` | False claim that no external benchmark exists | P2 | 171 | 15.7% | 171 |
| `RM-G02` | RoB asserted from design fields alone | P2 | 169 | 15.5% | 169 |
| `RM-A03` | Wrong effect-measure label | P1 | 168 | 15.4% | 736 |
| `RM-A08` | Component counts paired with a composite effect | P1 | 165 | 15.2% | 198 |
| `RM-A12` | Effect estimate contradicts its own 2x2 | P0 | 134 | 12.3% | 166 |
| `RM-D02` | Wrong or cross-topic citation | P1 | 132 | 12.1% | 156 |
| `RM-E03` | Registry/monitoring watchlist tracks the wrong drug class | P0 | 56 | 5.1% | 56 |
| `RM-B08` | Search under-inclusion vs a known external synthesis | P1 | 33 | 3.0% | 33 |
| `RM-C01` | Randomised vs analysed denominator unlabelled | P2 | 30 | 2.8% | 42 |
| `RM-D09` | Phase label inapplicable to a device or behavioural trial | P1 | 23 | 2.1% | 59 |
| `RM-D06` | App identity mismatch | P1 | 21 | 1.9% | 21 |
| `RM-D11` | Published pooled estimate presented as a trial-level effect | P1 | 21 | 1.9% | 29 |
| `RM-F07` | Unearned confidence on unsourced fields | P1 | 17 | 1.6% | 17 |
| `RM-D01` | Wrong NCT / registry-concordance failure | P1 | 10 | 0.9% | 17 |
| `RM-A13` | Estimand-granularity mismatch: composite component sets differ | P0 | 9 | 0.8% | 9 |
| `RM-A01` | Recurrent-event coercion | P0 | 8 | 0.7% | 19 |
| `RM-A10` | Kaplan-Meier risk rendered as a crude event count | P0 | 5 | 0.5% | 9 |
| `RM-C04` | Arm reversal: intervention and control denominators swapped | P0 | 4 | 0.4% | 4 |
| `RM-A04` | Peto output labelled HR | P1 | 3 | 0.3% | 5 |
| `RM-A09` | Win-ratio estimate paired with an HR | P1 | 3 | 0.3% | 3 |
| `RM-V01` | Displayed value contradicts the source-verified fixture | P0 | 3 | 0.3% | 5 |
| `RM-D12` | Citation volume/issue/page metadata mismatch | P1 | 0 | 0.0% | 0 |
| `RM-F06` | Impossible PRISMA zeros | P1 | 0 | 0.0% | 0 |

### 2a. P0 types, by prevalence

| id | error type | apps | % |
|---|---|---:|---:|
| `RM-E01` | Cross-topic template contamination | 1035 | 95.1% |
| `RM-J07` | Integrity gate passes over a fail-closed condition | 1030 | 94.7% |
| `RM-B03` | Silent endpoint fallback | 1024 | 94.1% |
| `RM-B02` | Stale outcome-state leakage | 1010 | 92.8% |
| `RM-G01` | safeRob unknown -> low | 1006 | 92.5% |
| `RM-J01` | False ICMJE / PROSPERO equivalence attribution | 1006 | 92.5% |
| `RM-B01` | Scope-lock failure | 939 | 86.3% |
| `RM-A02` | Estimand mixing in one pool | 810 | 74.4% |
| `RM-F01` | False-green verdict badge | 802 | 73.7% |
| `RM-F03` | Badge self-contradiction | 802 | 73.7% |
| `RM-A05` | Continuous outcome in a ratio model | 748 | 68.8% |
| `RM-A14` | escalc(measure=RR) over rows the ledger tags as different endpoints | 744 | 68.4% |
| `RM-F02` | Verdict-surface disagreement | 596 | 54.8% |
| `RM-D10` | Duplicate, NULLED or ghost trial rows | 512 | 47.1% |
| `RM-A07` | Non-ratio quantity in a ratio field | 315 | 29.0% |
| `RM-A12` | Effect estimate contradicts its own 2x2 | 134 | 12.3% |
| `RM-E03` | Registry/monitoring watchlist tracks the wrong drug class | 56 | 5.1% |
| `RM-A13` | Estimand-granularity mismatch: composite component sets differ | 9 | 0.8% |
| `RM-A01` | Recurrent-event coercion | 8 | 0.7% |
| `RM-A10` | Kaplan-Meier risk rendered as a crude event count | 5 | 0.5% |
| `RM-C04` | Arm reversal: intervention and control denominators swapped | 4 | 0.4% |
| `RM-V01` | Displayed value contradicts the source-verified fixture | 3 | 0.3% |

## 3. Worst offenders per type

### `RM-F05` — Missing rendered as zero (1059 apps, P1)

- **ABEMACICLIB_BREAST_AUTO_FULL_REVIEW.html** (3 items)
  - `Number.isFinite(Number(x))` presence check — Number(null)===0 passes it
  - presence guard tests the DENOMINATOR only; a null numerator coerces to 0
- **ACALABRUTINIB_CLL_REVIEW.html** (3 items)
  - `Number.isFinite(Number(x))` presence check — Number(null)===0 passes it
  - presence guard tests the DENOMINATOR only; a null numerator coerces to 0
- **ACLIDINIUM_COPD_AUTO_FULL_REVIEW.html** (3 items)
  - `Number.isFinite(Number(x))` presence check — Number(null)===0 passes it
  - presence guard tests the DENOMINATOR only; a null numerator coerces to 0
- **ACORAMIDIS_ATTR_CM_REVIEW.html** (3 items)
  - `Number.isFinite(Number(x))` presence check — Number(null)===0 passes it
  - presence guard tests the DENOMINATOR only; a null numerator coerces to 0
- **ADC_HER2_ADJUVANT_REVIEW.html** (3 items)
  - `Number.isFinite(Number(x))` presence check — Number(null)===0 passes it
  - presence guard tests the DENOMINATOR only; a null numerator coerces to 0

### `RM-I01` — Direction inversion risk (no explicit polarity) (1053 apps, P1)

- **ABALOPARATIDE_OSTEO_AUTO_FULL_REVIEW.html** (2 items)
  - no outcome row carries an explicit polarity across 1 trial(s) — an OR<1 on a GOOD outcome cannot be distinguished from an OR<1 on a bad one
  - an NNH is rendered with no polarity field to justify the direction
- **ABATACEPT_PSA_AUTO_FULL_REVIEW.html** (2 items)
  - no outcome row carries an explicit polarity across 2 trial(s) — an OR<1 on a GOOD outcome cannot be distinguished from an OR<1 on a bad one
  - an NNH is rendered with no polarity field to justify the direction
- **ABATACEPT_RA_AUTO_FULL_REVIEW.html** (2 items)
  - no outcome row carries an explicit polarity across 2 trial(s) — an OR<1 on a GOOD outcome cannot be distinguished from an OR<1 on a bad one
  - an NNH is rendered with no polarity field to justify the direction
- **ABEMACICLIB_BREAST_AUTO_FULL_REVIEW.html** (2 items)
  - no outcome row carries an explicit polarity across 2 trial(s) — an OR<1 on a GOOD outcome cannot be distinguished from an OR<1 on a bad one
  - an NNH is rendered with no polarity field to justify the direction
- **ABLATION_AF_REVIEW.html** (2 items)
  - no outcome row carries an explicit polarity across 4 trial(s) — an OR<1 on a GOOD outcome cannot be distinguished from an OR<1 on a bad one
  - an NNH is rendered with no polarity field to justify the direction

### `RM-H01` — k-inappropriate machinery (1049 apps, P1)

- **ABALOPARATIDE_OSTEO_AUTO_FULL_REVIEW.html** (8 items)
  - funnel rendered at k=1 (requires k>=10)
  - egger rendered at k=1 (requires k>=10)
- **ABATACEPT_PSA_AUTO_FULL_REVIEW.html** (8 items)
  - funnel rendered at k=2 (requires k>=10)
  - egger rendered at k=2 (requires k>=10)
- **ABATACEPT_RA_AUTO_FULL_REVIEW.html** (8 items)
  - funnel rendered at k=2 (requires k>=10)
  - egger rendered at k=2 (requires k>=10)
- **ABEMACICLIB_BREAST_AUTO_FULL_REVIEW.html** (8 items)
  - funnel rendered at k=2 (requires k>=10)
  - egger rendered at k=2 (requires k>=10)
- **ACALABRUTINIB_CLL_REVIEW.html** (8 items)
  - funnel rendered at k=2 (requires k>=10)
  - egger rendered at k=2 (requires k>=10)

### `RM-E01` — Cross-topic template contamination (1035 apps, P0)

- **ACS_ANTIPLATELET_REVIEW.html** (6 items)
  - sglt2/dapagliflozin [residue]: ...e(/<[^>]+>/g,""):"";try{const ctgovUrl="https://clinicaltrials.gov/api/v2/studies?query.intr=empagliflozin+OR+dapagliflozin+OR+sacubitril+AND+heart+failure+reduced&pageSize=100&filter.overallStatus=CO...
  - sglt2/empagliflozin [residue]: ...tml=s=>s?s.replace(/<[^>]+>/g,""):"";try{const ctgovUrl="https://clinicaltrials.gov/api/v2/studies?query.intr=empagliflozin+OR+dapagliflozin+OR+sacubitril+AND+heart+failure+reduced&pageSize=100&filter...
- **AD_PEDIATRIC_BIOLOGIC_NMA_REVIEW.html** (6 items)
  - sglt2/sglt2 [residue]: ...t-amber-400">OpenAlex</td><td class="p-3"><code class="text-[10px] text-slate-400 font-mono break-all">search=sglt2%20heart%20failure&amp;per_page=50</code></td><td class="p-3 text-slate-400">Bibliogr...
  - sglt2/sglt-2 [CLAIM-BEARING]: ...year??0,10)||0,score=parseInt(trial?.screenScore??0,10)||0,hasNct=/^NCT\d{8}$/i.test(id),hasDrug=/\bsglt2\b|\bsglt-2\b|\bdapagliflozin\b|\bempagliflozin\b|\bsotagliflozin\b|\bcanagliflozin\b|\bertugli...
- **ADC_HER2_ADJUVANT_REVIEW.html** (6 items)
  - sglt2/dapagliflozin [residue]: ...px] text-slate-400 font-mono break-all">https://clinicaltrials.gov/api/v2/studies?query.intr=empagliflozin+OR+dapagliflozin+OR+sacubitril+AND+heart+failure+reduced&amp;pageSize=100&amp;filter.overallS...
  - sglt2/empagliflozin [residue]: ...e class="text-[10px] text-slate-400 font-mono break-all">https://clinicaltrials.gov/api/v2/studies?query.intr=empagliflozin+OR+dapagliflozin+OR+sacubitril+AND+heart+failure+reduced&amp;pageSize=100&am...
- **ADC_HER2_LOW_REVIEW.html** (6 items)
  - sglt2/dapagliflozin [residue]: ...px] text-slate-400 font-mono break-all">https://clinicaltrials.gov/api/v2/studies?query.intr=empagliflozin+OR+dapagliflozin+OR+sacubitril+AND+heart+failure+reduced&amp;pageSize=100&amp;filter.overallS...
  - sglt2/empagliflozin [residue]: ...e class="text-[10px] text-slate-400 font-mono break-all">https://clinicaltrials.gov/api/v2/studies?query.intr=empagliflozin+OR+dapagliflozin+OR+sacubitril+AND+heart+failure+reduced&amp;pageSize=100&am...
- **ADC_HER2_NMA_REVIEW.html** (6 items)
  - sglt2/dapagliflozin [residue]: ...px] text-slate-400 font-mono break-all">https://clinicaltrials.gov/api/v2/studies?query.intr=empagliflozin+OR+dapagliflozin+OR+sacubitril+AND+heart+failure+reduced&amp;pageSize=100&amp;filter.overallS...
  - sglt2/empagliflozin [residue]: ...e class="text-[10px] text-slate-400 font-mono break-all">https://clinicaltrials.gov/api/v2/studies?query.intr=empagliflozin+OR+dapagliflozin+OR+sacubitril+AND+heart+failure+reduced&amp;pageSize=100&am...

### `RM-J07` — Integrity gate passes over a fail-closed condition (1030 apps, P0)

- **ABALOPARATIDE_OSTEO_AUTO_FULL_REVIEW.html** (1 item)
  - the visible gate asserts a pass while these fail-closed conditions hold: a rendered NaN; trial counts disagreeing across surfaces [1, 2]
- **ABATACEPT_PSA_AUTO_FULL_REVIEW.html** (1 item)
  - the visible gate asserts a pass while these fail-closed conditions hold: a rendered NaN
- **ABATACEPT_RA_AUTO_FULL_REVIEW.html** (1 item)
  - the visible gate asserts a pass while these fail-closed conditions hold: a rendered NaN
- **ABEMACICLIB_BREAST_AUTO_FULL_REVIEW.html** (1 item)
  - the visible gate asserts a pass while these fail-closed conditions hold: a rendered NaN
- **ABLATION_AF_REVIEW.html** (1 item)
  - the visible gate asserts a pass while these fail-closed conditions hold: a rendered NaN; trial counts disagreeing across surfaces [0, 4]

### `RM-B03` — Silent endpoint fallback (1024 apps, P0)

- **ABALOPARATIDE_OSTEO_AUTO_FULL_REVIEW.html** (1 item)
  - 3 `outcomes[0]` fallback site(s) — a missing scope substitutes another endpoint
- **ABATACEPT_PSA_AUTO_FULL_REVIEW.html** (1 item)
  - 3 `outcomes[0]` fallback site(s) — a missing scope substitutes another endpoint
- **ABATACEPT_RA_AUTO_FULL_REVIEW.html** (1 item)
  - 3 `outcomes[0]` fallback site(s) — a missing scope substitutes another endpoint
- **ABEMACICLIB_BREAST_AUTO_FULL_REVIEW.html** (1 item)
  - 3 `outcomes[0]` fallback site(s) — a missing scope substitutes another endpoint
- **ABLATION_AF_REVIEW.html** (1 item)
  - 3 `outcomes[0]` fallback site(s) — a missing scope substitutes another endpoint

### `RM-B02` — Stale outcome-state leakage (1010 apps, P0)

- **ABALOPARATIDE_OSTEO_AUTO_FULL_REVIEW.html** (2 items)
  - the `pooling-repair` block is present and not disabled — it copies realData tE/cE into t.data and force-sets effectMeasure='HR', bypassing the scope lock
  - `?? t.data.<count>` fallback leaks the previously bound endpoint's counts
- **ABATACEPT_PSA_AUTO_FULL_REVIEW.html** (2 items)
  - the `pooling-repair` block is present and not disabled — it copies realData tE/cE into t.data and force-sets effectMeasure='HR', bypassing the scope lock
  - `?? t.data.<count>` fallback leaks the previously bound endpoint's counts
- **ABATACEPT_RA_AUTO_FULL_REVIEW.html** (2 items)
  - the `pooling-repair` block is present and not disabled — it copies realData tE/cE into t.data and force-sets effectMeasure='HR', bypassing the scope lock
  - `?? t.data.<count>` fallback leaks the previously bound endpoint's counts
- **ABEMACICLIB_BREAST_AUTO_FULL_REVIEW.html** (2 items)
  - the `pooling-repair` block is present and not disabled — it copies realData tE/cE into t.data and force-sets effectMeasure='HR', bypassing the scope lock
  - `?? t.data.<count>` fallback leaks the previously bound endpoint's counts
- **ABLATION_AF_REVIEW.html** (2 items)
  - the `pooling-repair` block is present and not disabled — it copies realData tE/cE into t.data and force-sets effectMeasure='HR', bypassing the scope lock
  - `?? t.data.<count>` fallback leaks the previously bound endpoint's counts

### `RM-G01` — safeRob unknown -> low (1006 apps, P0)

- **ABALOPARATIDE_OSTEO_AUTO_FULL_REVIEW.html** (2 items)
  - safeRob resolves every unrecognised rating to "low" — "some-concerns" is not in the valid list, so every Some-Concerns renders as Low Risk
  - a non-array RoB resolves to all-"low"
- **ABATACEPT_PSA_AUTO_FULL_REVIEW.html** (2 items)
  - safeRob resolves every unrecognised rating to "low" — "some-concerns" is not in the valid list, so every Some-Concerns renders as Low Risk
  - a non-array RoB resolves to all-"low"
- **ABATACEPT_RA_AUTO_FULL_REVIEW.html** (2 items)
  - safeRob resolves every unrecognised rating to "low" — "some-concerns" is not in the valid list, so every Some-Concerns renders as Low Risk
  - a non-array RoB resolves to all-"low"
- **ABEMACICLIB_BREAST_AUTO_FULL_REVIEW.html** (2 items)
  - safeRob resolves every unrecognised rating to "low" — "some-concerns" is not in the valid list, so every Some-Concerns renders as Low Risk
  - a non-array RoB resolves to all-"low"
- **ABLATION_AF_REVIEW.html** (2 items)
  - safeRob resolves every unrecognised rating to "low" — "some-concerns" is not in the valid list, so every Some-Concerns renders as Low Risk
  - a non-array RoB resolves to all-"low"

### `RM-J01` — False ICMJE / PROSPERO equivalence attribution (1006 apps, P0)

- **ABALOPARATIDE_OSTEO_AUTO_FULL_REVIEW.html** (2 items)
  - ICMJE attribution: on (PROSPERO / OSF) on submission-bound topics, see the per-topic Submission Cockpit. Per ICMJE 2023, GitHub commit hash + timestamp constitutes a verifiable pre-registration record equivalent to PROS
  - a literal PROSPERO-equivalence label is asserted
- **ABATACEPT_PSA_AUTO_FULL_REVIEW.html** (2 items)
  - ICMJE attribution: on (PROSPERO / OSF) on submission-bound topics, see the per-topic Submission Cockpit. Per ICMJE 2023, GitHub commit hash + timestamp constitutes a verifiable pre-registration record equivalent to PROS
  - a literal PROSPERO-equivalence label is asserted
- **ABATACEPT_RA_AUTO_FULL_REVIEW.html** (2 items)
  - ICMJE attribution: on (PROSPERO / OSF) on submission-bound topics, see the per-topic Submission Cockpit. Per ICMJE 2023, GitHub commit hash + timestamp constitutes a verifiable pre-registration record equivalent to PROS
  - a literal PROSPERO-equivalence label is asserted
- **ABEMACICLIB_BREAST_AUTO_FULL_REVIEW.html** (2 items)
  - ICMJE attribution: on (PROSPERO / OSF) on submission-bound topics, see the per-topic Submission Cockpit. Per ICMJE 2023, GitHub commit hash + timestamp constitutes a verifiable pre-registration record equivalent to PROS
  - a literal PROSPERO-equivalence label is asserted
- **ABLATION_AF_REVIEW.html** (2 items)
  - ICMJE attribution: on (PROSPERO / OSF) on submission-bound topics, see the per-topic Submission Cockpit. Per ICMJE 2023, GitHub commit hash + timestamp constitutes a verifiable pre-registration record equivalent to PROS
  - a literal PROSPERO-equivalence label is asserted

### `RM-H04` — N/A gate reported as a pass (999 apps, P1)

- **ABALOPARATIDE_OSTEO_AUTO_FULL_REVIEW.html** (2 items)
  - P0_grim=0 on an all-binary ledger — GRIM is N/A (no mean of a bounded integer scale to reconstruct); a 0 reads as a pass
  - a Benford verdict on 4 values (needs >=30) with no UNDERPOWERED label
- **ABATACEPT_PSA_AUTO_FULL_REVIEW.html** (2 items)
  - P0_grim=0 on an all-binary ledger — GRIM is N/A (no mean of a bounded integer scale to reconstruct); a 0 reads as a pass
  - a Benford verdict on 8 values (needs >=30) with no UNDERPOWERED label
- **ABATACEPT_RA_AUTO_FULL_REVIEW.html** (2 items)
  - P0_grim=0 on an all-binary ledger — GRIM is N/A (no mean of a bounded integer scale to reconstruct); a 0 reads as a pass
  - a Benford verdict on 8 values (needs >=30) with no UNDERPOWERED label
- **ABEMACICLIB_BREAST_AUTO_FULL_REVIEW.html** (2 items)
  - P0_grim=0 on an all-binary ledger — GRIM is N/A (no mean of a bounded integer scale to reconstruct); a 0 reads as a pass
  - a Benford verdict on 4 values (needs >=30) with no UNDERPOWERED label
- **ABLATION_AF_REVIEW.html** (2 items)
  - P0_grim=0 on an all-binary ledger — GRIM is N/A (no mean of a bounded integer scale to reconstruct); a 0 reads as a pass
  - a Benford verdict on 16 values (needs >=30) with no UNDERPOWERED label

### `RM-F04` — Interface state desync (991 apps, P2)

- **ABALOPARATIDE_OSTEO_AUTO_FULL_REVIEW.html** (1 item)
  - 2 distinct APP version tokens on RapidMeta-labelled surfaces: ['11.0', '12.0']
- **ABATACEPT_PSA_AUTO_FULL_REVIEW.html** (1 item)
  - 2 distinct APP version tokens on RapidMeta-labelled surfaces: ['11.0', '12.0']
- **ABATACEPT_RA_AUTO_FULL_REVIEW.html** (1 item)
  - 2 distinct APP version tokens on RapidMeta-labelled surfaces: ['11.0', '12.0']
- **ABEMACICLIB_BREAST_AUTO_FULL_REVIEW.html** (1 item)
  - 3 distinct APP version tokens on RapidMeta-labelled surfaces: ['1.1', '11.0', '12.0']
- **ABLATION_AF_REVIEW.html** (1 item)
  - 3 distinct APP version tokens on RapidMeta-labelled surfaces: ['11.0', '12.0', '12.5']

### `RM-H02` — Inadmissible estimator / uninterpretable tau2 at small k (976 apps, P1)

- **ABALOPARATIDE_OSTEO_AUTO_FULL_REVIEW.html** (1 item)
  - DerSimonian-Laird at k=1 (inadmissible below k=10)
- **ABATACEPT_PSA_AUTO_FULL_REVIEW.html** (1 item)
  - DerSimonian-Laird at k=2 (inadmissible below k=10)
- **ABATACEPT_RA_AUTO_FULL_REVIEW.html** (1 item)
  - DerSimonian-Laird at k=2 (inadmissible below k=10)
- **ABEMACICLIB_BREAST_AUTO_FULL_REVIEW.html** (1 item)
  - DerSimonian-Laird at k=2 (inadmissible below k=10)
- **ABLATION_AF_REVIEW.html** (1 item)
  - DerSimonian-Laird at k=4 (inadmissible below k=10)

### `RM-B01` — Scope-lock failure (939 apps, P0)

- **ABALOPARATIDE_OSTEO_AUTO_FULL_REVIEW.html** (1 item)
  - outcomeLabel derives from a MODAL-TITLE frequency sort while the binding indexes outcomes[0] — label and binding are decoupled
- **ABATACEPT_PSA_AUTO_FULL_REVIEW.html** (1 item)
  - outcomeLabel derives from a MODAL-TITLE frequency sort while the binding indexes outcomes[0] — label and binding are decoupled
- **ABATACEPT_RA_AUTO_FULL_REVIEW.html** (1 item)
  - outcomeLabel derives from a MODAL-TITLE frequency sort while the binding indexes outcomes[0] — label and binding are decoupled
- **ABEMACICLIB_BREAST_AUTO_FULL_REVIEW.html** (1 item)
  - outcomeLabel derives from a MODAL-TITLE frequency sort while the binding indexes outcomes[0] — label and binding are decoupled
- **ABLATION_AF_REVIEW.html** (1 item)
  - outcomeLabel derives from a MODAL-TITLE frequency sort while the binding indexes outcomes[0] — label and binding are decoupled

### `RM-A02` — Estimand mixing in one pool (810 apps, P0)

- **CGRP_MIGRAINE_NMA_REVIEW.html** (2 items)
  - the DENYLIST guard `"RR" !== String(d?.estimandType ?? "HR")` is present — anything not literally RR is treated as a hazard ratio
  - mixed estimands across pooled trials: MDx3, RRx1
- **DIABETIC_RETINOPATHY_REVIEW.html** (2 items)
  - the DENYLIST guard `"RR" !== String(d?.estimandType ?? "HR")` is present — anything not literally RR is treated as a hazard ratio
  - mixed estimands across pooled trials: MDx1, RRx2
- **HEMOPHILIA_GENE_THERAPY_REVIEW.html** (2 items)
  - the DENYLIST guard `"RR" !== String(d?.estimandType ?? "HR")` is present — anything not literally RR is treated as a hazard ratio
  - mixed estimands across pooled trials: MDx1, RRx2
- **HEPATITIS_HCV_DAA_REVIEW.html** (2 items)
  - the DENYLIST guard `"RR" !== String(d?.estimandType ?? "HR")` is present — anything not literally RR is treated as a hazard ratio
  - mixed estimands across pooled trials: ORx1, PROPORTIONx1, RRx1
- **HIV_PREP_INJECTABLE_REVIEW.html** (2 items)
  - the DENYLIST guard `"RR" !== String(d?.estimandType ?? "HR")` is present — anything not literally RR is treated as a hazard ratio
  - mixed estimands across pooled trials: HRx2, IRRx1

### `RM-J02` — Retrospective protocol framed as prospective (808 apps, P1)

- **ACS_ANTIPLATELET_REVIEW.html** (2 items)
  - a prospective-registration claim co-occurs with an admission that the protocol is retrospective
  - 'Retrospective Public Protocol Pack (OSF-ready)' is presented as a registration artefact
- **ADC_HER2_ADJUVANT_REVIEW.html** (2 items)
  - a prospective-registration claim co-occurs with an admission that the protocol is retrospective
  - 'Retrospective Public Protocol Pack (OSF-ready)' is presented as a registration artefact
- **ADC_HER2_LOW_REVIEW.html** (2 items)
  - a prospective-registration claim co-occurs with an admission that the protocol is retrospective
  - 'Retrospective Public Protocol Pack (OSF-ready)' is presented as a registration artefact
- **ADC_HER2_NMA_REVIEW.html** (2 items)
  - a prospective-registration claim co-occurs with an admission that the protocol is retrospective
  - 'Retrospective Public Protocol Pack (OSF-ready)' is presented as a registration artefact
- **ANTI_CD20_MS_REVIEW.html** (2 items)
  - a prospective-registration claim co-occurs with an admission that the protocol is retrospective
  - 'Retrospective Public Protocol Pack (OSF-ready)' is presented as a registration artefact

### `RM-H05` — External-validation claim vs a different-scope benchmark (807 apps, P1)

- **ABALOPARATIDE_OSTEO_AUTO_FULL_REVIEW.html** (1 item)
  - BENCHMARK_OUTCOME_MAP routes an all-cause-mortality scope onto a MACE (composite) benchmark
- **ABATACEPT_PSA_AUTO_FULL_REVIEW.html** (1 item)
  - BENCHMARK_OUTCOME_MAP routes an all-cause-mortality scope onto a MACE (composite) benchmark
- **ABATACEPT_RA_AUTO_FULL_REVIEW.html** (1 item)
  - BENCHMARK_OUTCOME_MAP routes an all-cause-mortality scope onto a MACE (composite) benchmark
- **ABEMACICLIB_BREAST_AUTO_FULL_REVIEW.html** (1 item)
  - BENCHMARK_OUTCOME_MAP routes an all-cause-mortality scope onto a MACE (composite) benchmark
- **ABLATION_AF_REVIEW.html** (1 item)
  - BENCHMARK_OUTCOME_MAP routes an all-cause-mortality scope onto a MACE (composite) benchmark

### `RM-F01` — False-green verdict badge (802 apps, P0)

- **AFLIBERCEPT_HD_REVIEW.html** (4 items)
  - green badge (#15803d) over __verdict='UNCERTAIN'
  - green badge (#15803d) over 2 open P1/P2 finding(s)
- **ALDO_SYNTHASE_REVIEW.html** (4 items)
  - green badge (#15803d) over __verdict='UNCERTAIN'
  - green badge (#15803d) over 2 open P1/P2 finding(s)
- **CFTR_CF_REVIEW.html** (4 items)
  - green badge (#15803d) over __verdict='UNCERTAIN'
  - green badge (#15803d) over 3 open P1/P2 finding(s)
- **CGRP_MIGRAINE_REVIEW.html** (4 items)
  - green badge (#15803d) over __verdict='UNCERTAIN'
  - green badge (#15803d) over 3 open P1/P2 finding(s)
- **DELANDISTROGENE_DMD_REVIEW.html** (4 items)
  - green badge (#15803d) over __verdict='UNCERTAIN'
  - green badge (#15803d) over 1 open P1/P2 finding(s)

### `RM-F03` — Badge self-contradiction (802 apps, P0)

- **ABALOPARATIDE_OSTEO_AUTO_FULL_REVIEW.html** (1 item)
  - two internal-consistency rounds values in one badge: 10 vs 14
- **ABATACEPT_PSA_AUTO_FULL_REVIEW.html** (1 item)
  - two internal-consistency rounds values in one badge: 10 vs 14
- **ABATACEPT_RA_AUTO_FULL_REVIEW.html** (1 item)
  - two internal-consistency rounds values in one badge: 10 vs 14
- **ABEMACICLIB_BREAST_AUTO_FULL_REVIEW.html** (1 item)
  - two internal-consistency rounds values in one badge: 10 vs 14
- **ABLATION_AF_REVIEW.html** (1 item)
  - two internal-consistency rounds values in one badge: 10 vs 14

### `RM-D08` — False registry-status claim (767 apps, P1)

- **ABALOPARATIDE_OSTEO_AUTO_FULL_REVIEW.html** (1 item)
  - asserts 'no linked publications' while the ledger itself carries 1 PMID(s)
- **ABATACEPT_PSA_AUTO_FULL_REVIEW.html** (1 item)
  - asserts 'no linked publications' while the ledger itself carries 2 PMID(s)
- **ABATACEPT_RA_AUTO_FULL_REVIEW.html** (1 item)
  - asserts 'no linked publications' while the ledger itself carries 2 PMID(s)
- **ABEMACICLIB_BREAST_AUTO_FULL_REVIEW.html** (1 item)
  - asserts 'no linked publications' while the ledger itself carries 2 PMID(s)
- **ABLATION_AF_REVIEW.html** (1 item)
  - asserts 'no linked publications' while the ledger itself carries 4 PMID(s)

### `RM-A05` — Continuous outcome in a ratio model (748 apps, P0)

- **ABALOPARATIDE_OSTEO_AUTO_FULL_REVIEW.html** (1 item)
  - `|| {md: t.data.md, se: t.data.se}` fallback substitutes a different estimand for trials lacking the selected continuous outcome
- **ABATACEPT_PSA_AUTO_FULL_REVIEW.html** (1 item)
  - `|| {md: t.data.md, se: t.data.se}` fallback substitutes a different estimand for trials lacking the selected continuous outcome
- **ABATACEPT_RA_AUTO_FULL_REVIEW.html** (1 item)
  - `|| {md: t.data.md, se: t.data.se}` fallback substitutes a different estimand for trials lacking the selected continuous outcome
- **ABEMACICLIB_BREAST_AUTO_FULL_REVIEW.html** (1 item)
  - `|| {md: t.data.md, se: t.data.se}` fallback substitutes a different estimand for trials lacking the selected continuous outcome
- **ABLATION_AF_REVIEW.html** (1 item)
  - `|| {md: t.data.md, se: t.data.se}` fallback substitutes a different estimand for trials lacking the selected continuous outcome

### `RM-A14` — escalc(measure=RR) over rows the ledger tags as different endpoints (744 apps, P0)

- **ANCA_VASCULITIS_NMA_REVIEW.html** (2 items)
  - the generated R builds `ai = c(${trials.map(t=>t.data.tE)})` and pools it with escalc(measure=RR) across primaries that are NOT the same construct: ADVOCATE: "Sustained remission at week 52 (avacopan)" (tE=120, cE=115) | RAVE: "Remission at 6 months (RAVE)" (tE=64, cE=53) | RITUXVAS: "Sustained remi
  - timepoints mixed in one binary pool: at 28 month, at 6 month, unstated
- **ANTIAMYLOID_AD_NMA_REVIEW.html** (2 items)
  - the generated R builds `ai = c(${trials.map(t=>t.data.tE)})` and pools it with escalc(measure=RR) across primaries that are NOT the same construct: Clarity AD: "CDR-SB change at 18 months lecanemab vs placebo (MD, points)" (tE=None, cE=None) | TRAILBLAZER-ALZ 2: "CDR-SB change at 76 weeks donanemab 
  - timepoints mixed in one binary pool: at 18 month, at 76 week, at 78 week, unstated
- **AZITHROMYCIN_CHILD_MORTALITY_REVIEW.html** (2 items)
  - the generated R builds `ai = c(${trials.map(t=>t.data.tE)})` and pools it with escalc(measure=RR) across primaries that are NOT the same construct: MORDOR-I: "All-cause under-5 mortality at 2 years (primary, IRR pooled across cou" (tE=None, cE=None) | MORDOR-II: "All-cause under-5 mortality at year 
  - timepoints mixed in one binary pool: at 2 year, unstated
- **BARIATRIC_RYGB_VS_SG_REVIEW.html** (2 items)
  - the generated R builds `ai = c(${trials.map(t=>t.data.tE)})` and pools it with escalc(measure=RR) across primaries that are NOT the same construct: SM-BOSS: "Excess BMI loss ≥50% at 5 years" (tE=45, cE=39) | SLEEVEPASS: "%EWL at 5 years (RYGB superior at 10y)" (tE=56, cE=53) | STAMPEDE: "Diabetes re
  - timepoints mixed in one binary pool: at 1 year, at 12 month, at 2 year, at 3 year, at 5 year, unstated
- **BOSUTINIB_LEUKEMIA_AUTO_FULL_REVIEW.html** (2 items)
  - the generated R builds `ai = c(${trials.map(t=>t.data.tE)})` and pools it with escalc(measure=RR) across primaries that are NOT the same construct: NCT01903733: "Number of Participants With Treatment-Emergent Adverse Events (AEs) an" (tE=241, cE=283) | NCT02130557: "Percentage of Participants With M
  - timepoints mixed in one binary pool: at 24 week, unstated

### `RM-E02` — Foreign trial-alias registry (716 apps, P1)

- **ABALOPARATIDE_OSTEO_AUTO_FULL_REVIEW.html** (1 item)
  - sacubitril/valsartan alias table baked into a non-ARNI app: ['NCT01035255', 'NCT01920711', 'NCT02924727']
- **ABATACEPT_PSA_AUTO_FULL_REVIEW.html** (1 item)
  - sacubitril/valsartan alias table baked into a non-ARNI app: ['NCT01035255', 'NCT01920711', 'NCT02924727']
- **ABATACEPT_RA_AUTO_FULL_REVIEW.html** (1 item)
  - sacubitril/valsartan alias table baked into a non-ARNI app: ['NCT01035255', 'NCT01920711', 'NCT02924727']
- **ABEMACICLIB_BREAST_AUTO_FULL_REVIEW.html** (1 item)
  - sacubitril/valsartan alias table baked into a non-ARNI app: ['NCT01035255', 'NCT01920711', 'NCT02924727']
- **ACALABRUTINIB_CLL_REVIEW.html** (1 item)
  - sacubitril/valsartan alias table baked into a non-ARNI app: ['NCT01035255', 'NCT01920711', 'NCT02924727']

### `RM-G03` — RoB chip contradicts the trial's own extraction evidence (701 apps, P1)

- **MALARIA_ACT_REVIEW.html** (19 items)
  - Bandim AL-vs-DP: evidence says D2 = 'SOME concerns' but the chart chip shows 'high'
  - Bandim AL-vs-DP: evidence says D3 = 'LOW' but the chart chip shows 'some-concerns'
- **IO_CHEMO_NSCLC_1L_REVIEW.html** (13 items)
  - KEYNOTE-189: evidence says D3 = 'LOW' but the chart chip shows 'some-concerns'
  - KEYNOTE-189: evidence says D5 = 'LOW' but the chart chip shows 'some-concerns'
- **TNK_VS_TPA_STROKE_REVIEW.html** (12 items)
  - NOR-TEST: evidence says D2 = 'SOME CONCERNS' but the chart chip shows 'low'
  - NOR-TEST: evidence says D3 = 'LOW' but the chart chip shows 'some-concerns'
- **EVT_BASILAR_REVIEW.html** (11 items)
  - ATTENTION: evidence says D3 = 'LOW' but the chart chip shows 'some-concerns'
  - ATTENTION: evidence says D4 = 'LOW' but the chart chip shows 'some-concerns'
- **INSULIN_ICODEC_REVIEW.html** (11 items)
  - ONWARDS-1: evidence says D2 = 'SOME CONCERNS' but the chart chip shows 'high'
  - ONWARDS-1: evidence says D3 = 'LOW' but the chart chip shows 'some-concerns'

### `RM-F02` — Verdict-surface disagreement (596 apps, P0)

- **PCSK9_INHIBITORS_CV_REVIEW.html** (3 items)
  - __verdict.n_trials_seen=5 vs realData k=2
  - badge 'Trials: 10' vs __verdict.n_trials_seen=5
- **ABALOPARATIDE_OSTEO_AUTO_FULL_REVIEW.html** (2 items)
  - __verdict.n_trials_seen=2 vs realData k=1
  - badge 'Trials: 2' vs realData k=1
- **ABLATION_AF_REVIEW.html** (2 items)
  - __verdict.n_trials_seen=0 vs realData k=4
  - badge 'Trials: 4' vs __verdict.n_trials_seen=0
- **ACLIDINIUM_COPD_AUTO_FULL_REVIEW.html** (2 items)
  - __verdict.n_trials_seen=2 vs realData k=3
  - badge 'Trials: 2' vs realData k=3
- **ACUTE_HF_DIURESIS_NEW_REVIEW.html** (2 items)
  - __verdict.n_trials_seen=5 vs realData k=10
  - badge 'Trials: 10' vs __verdict.n_trials_seen=5

### `RM-D10` — Duplicate, NULLED or ghost trial rows (512 apps, P0)

- **COVID19_VACCINES_REVIEW.html** (9 items)
  - row key 'NULLED:NCT04368728' is a NULLED placeholder
  - row key 'NULLED:NCT04470427' is a NULLED placeholder
- **MIS_GASTRECTOMY_NMA_REVIEW.html** (8 items)
  - row key 'NULLED:NCT01102452' is a NULLED placeholder
  - row key 'NULLED:NCT01692457' is a NULLED placeholder
- **ARDS_PRONE_POSITIONING_REVIEW.html** (7 items)
  - row key 'NULLED:NCT04356508' is a NULLED placeholder
  - row key 'NULLED:NCT04376255' is a NULLED placeholder
- **BARIATRIC_RYGB_VS_SG_REVIEW.html** (7 items)
  - row key 'NULLED:NCT02788513' is a NULLED placeholder
  - row key 'NULLED:NCT01435902' is a NULLED placeholder
- **PERIPHERAL_DCB_PAD_NMA_REVIEW.html** (7 items)
  - row key 'NULLED:NCT01858363' is a NULLED placeholder
  - row key 'NULLED:NCT01858350' is a NULLED placeholder

### `RM-D05` — Fabricated / imported analysis row (351 apps, P1)

- **CGRP_MIGRAINE_PREVENT_REVIEW.html** (15 items)
  - STRIVE: outcome '≥50% reduction in monthly migraine days at month 4' carries effect=2.04 with no source field
  - ARISE: outcome '≥50% reduction in MMD at month 3' carries effect=1.34 with no source field
- **CDK46_BREAST_CANCER_REVIEW.html** (12 items)
  - PALOMA-1: outcome 'Investigator-assessed PFS' carries effect=0.488 with no source field
  - PALOMA-2: outcome 'Investigator-assessed PFS' carries effect=0.58 with no source field
- **COVID19_HOSPITALIZED_TX_REVIEW.html** (12 items)
  - RECOVERY-DEXA: outcome '28-day mortality in hospitalized patients' carries effect=0.83 with no source field
  - RECOVERY-BARI: outcome '28-day mortality in hospitalized' carries effect=0.87 with no source field
- **COVID19_VACCINES_REVIEW.html** (12 items)
  - C4591001 (BNT162b2): outcome 'Symptomatic confirmed COVID-19 ≥7d after dose 2' carries effect=0.05 with no source field
  - COVE (mRNA-1273): outcome 'Symptomatic confirmed COVID-19 ≥14d after dose 2' carries effect=0.06 with no source field
- **HEMOPHILIA_FACTOR_PROPHYLAXIS_REVIEW.html** (12 items)
  - HAVEN-1: outcome 'ABR vs no prophylaxis (HemA inhibitor)' carries effect=0.1 with no source field
  - HAVEN-2: outcome 'ABR in pediatric inhibitor (single-arm)' carries effect=0.15 with no source field

### `RM-A07` — Non-ratio quantity in a ratio field (315 apps, P0)

- **BOCOCIZUMAB_LIPID_AUTO_FULL_REVIEW.html** (35 items)
  - SPIRE-LDL.publishedHR = -56.2 — a ratio of positive rates cannot be <= 0
  - SPIRE-LDL.pubHR = -56.2 — a ratio of positive rates cannot be <= 0
- **IL_PSORIASIS_NMA_REVIEW.html** (32 items)
  - VOYAGE 1.publishedHR = 86.76 — outside any reported ratio range
  - VOYAGE 1.hrLCI = 34.66 — outside any reported ratio range
- **AZILSARTAN_HTN_AUTO_FULL_REVIEW.html** (28 items)
  - NCT00846365.publishedHR = -6.1 — a ratio of positive rates cannot be <= 0
  - NCT00846365.pubHR = -6.1 — a ratio of positive rates cannot be <= 0
- **retired/CARIPRAZINE_BIPOLAR_AUTO_FULL_REVIEW.html** (28 items)
  - NCT01058096.publishedHR = -4.3 — a ratio of positive rates cannot be <= 0
  - NCT01058096.pubHR = -4.3 — a ratio of positive rates cannot be <= 0
- **retired/VRAYLAR_BIPOLAR_DEPRESSION_AUTO_FULL_REVIEW.html** (28 items)
  - NCT01058096.publishedHR = -4.3 — a ratio of positive rates cannot be <= 0
  - NCT01058096.pubHR = -4.3 — a ratio of positive rates cannot be <= 0

### `RM-J05` — COMPLETED-only registry filter (216 apps, P2)

- **ACUTE_HF_DIURESIS_NEW_REVIEW.html** (1 item)
  - the stored registry query filters to COMPLETED with no TERMINATED/WITHDRAWN — a trial stopped early for harm would be excluded
- **AD_PEDIATRIC_BIOLOGIC_NMA_REVIEW.html** (1 item)
  - the stored registry query filters to COMPLETED with no TERMINATED/WITHDRAWN — a trial stopped early for harm would be excluded
- **ADJUVANT_IO_PAN_TUMOR_REVIEW.html** (1 item)
  - the stored registry query filters to COMPLETED with no TERMINATED/WITHDRAWN — a trial stopped early for harm would be excluded
- **ALS_NEW_AGENTS_NMA_REVIEW.html** (1 item)
  - the stored registry query filters to COMPLETED with no TERMINATED/WITHDRAWN — a trial stopped early for harm would be excluded
- **AML_TARGETED_NEW_REVIEW.html** (1 item)
  - the stored registry query filters to COMPLETED with no TERMINATED/WITHDRAWN — a trial stopped early for harm would be excluded

### `RM-H03` — Fragility index where undefined (207 apps, P1)

- **ABEMACICLIB_BREAST_AUTO_FULL_REVIEW.html** (1 item)
  - a fragility index is rendered where no trial carries an observed 2x2
- **ACALABRUTINIB_CLL_REVIEW.html** (1 item)
  - a fragility index is rendered where no trial carries an observed 2x2
- **ACORAMIDIS_ATTR_CM_REVIEW.html** (1 item)
  - a fragility index is rendered where no trial carries an observed 2x2
- **ADC_HER2_ADJUVANT_REVIEW.html** (1 item)
  - a fragility index is rendered where no trial carries an observed 2x2
- **ADC_HER2_LOW_REVIEW.html** (1 item)
  - a fragility index is rendered where no trial carries an observed 2x2

### `RM-D07` — False claim that no external benchmark exists (171 apps, P2)

- **ABLATION_AF_REVIEW.html** (1 item)
  - a 'No published benchmark available' fallback ships while PUBLISHED_META_BENCHMARKS is populated — RENDER-confirm which scopes hit the fallback
- **ACALABRUTINIB_CLL_REVIEW.html** (1 item)
  - a 'No published benchmark available' fallback ships while PUBLISHED_META_BENCHMARKS is populated — RENDER-confirm which scopes hit the fallback
- **ACORAMIDIS_ATTR_CM_REVIEW.html** (1 item)
  - a 'No published benchmark available' fallback ships while PUBLISHED_META_BENCHMARKS is populated — RENDER-confirm which scopes hit the fallback
- **ACS_ANTIPLATELET_REVIEW.html** (1 item)
  - a 'No published benchmark available' fallback ships while PUBLISHED_META_BENCHMARKS is populated — RENDER-confirm which scopes hit the fallback; scopes absent from BENCHMARK_OUTCOME_MAP: ['CompositeOfDeathMiOrStro', 'CompositeOfDeathMiOrStro2']
- **ADC_HER2_ADJUVANT_REVIEW.html** (1 item)
  - a 'No published benchmark available' fallback ships while PUBLISHED_META_BENCHMARKS is populated — RENDER-confirm which scopes hit the fallback

### `RM-G02` — RoB asserted from design fields alone (169 apps, P2)

- **ABALOPARATIDE_OSTEO_AUTO_FULL_REVIEW.html** (1 item)
  - all 1 trial(s) carry an all-'low' RoB array with no stored RoB 2 domain answers
- **ABATACEPT_RA_AUTO_FULL_REVIEW.html** (1 item)
  - all 2 trial(s) carry an all-'low' RoB array with no stored RoB 2 domain answers
- **ABEMACICLIB_BREAST_AUTO_FULL_REVIEW.html** (1 item)
  - all 2 trial(s) carry an all-'low' RoB array with no stored RoB 2 domain answers
- **ADALIMUMAB_PSO_AUTO_FULL_REVIEW.html** (1 item)
  - all 2 trial(s) carry an all-'low' RoB array with no stored RoB 2 domain answers
- **ADUCANUMAB_AD_AUTO_FULL_REVIEW.html** (1 item)
  - all 2 trial(s) carry an all-'low' RoB array with no stored RoB 2 domain answers

### `RM-A03` — Wrong effect-measure label (168 apps, P1)

- **CGRP_MIGRAINE_PREVENT_REVIEW.html** (15 items)
  - STRIVE: estimandType=RR beside a publishedHR field (2.04)
  - ARISE: estimandType=RR beside a publishedHR field (1.34)
- **COVID19_VACCINES_REVIEW.html** (12 items)
  - C4591001 (BNT162b2): estimandType=RR beside a publishedHR field (0.05)
  - COVE (mRNA-1273): estimandType=RR beside a publishedHR field (0.06)
- **IBD_BIOLOGICS_REVIEW.html** (12 items)
  - UNITI-1: estimandType=RR beside a publishedHR field (1.69)
  - UNITI-2: estimandType=RR beside a publishedHR field (1.91)
- **JAK_RA_REVIEW.html** (12 items)
  - RA-BEAM: estimandType=RR beside a publishedHR field (1.99)
  - RA-BUILD: estimandType=RR beside a publishedHR field (1.71)
- **SEVERE_ASTHMA_BIOLOGICS_REVIEW.html** (12 items)
  - MUSCA: estimandType=RR beside a publishedHR field (0.42)
  - MENSA: estimandType=RR beside a publishedHR field (0.47)

### `RM-A08` — Component counts paired with a composite effect (165 apps, P1)

- **BIMEKIZUMAB_PSORIATIC_AUTO_FULL_REVIEW.html** (3 items)
  - BE OPTIMAL: crude RR 0.227 vs published effect 7.082 — opposite directions
  - BE COMPLETE: crude RR 0.156 vs published effect 11.139 — opposite directions
- **BOCOCIZUMAB_LIPID_AUTO_FULL_REVIEW.html** (3 items)
  - SPIRE-LL: crude RR 0.139 vs published effect 50.0 — opposite directions
  - SPIRE-HR: crude RR 0.506 vs published effect 56.6 — opposite directions
- **IXEKIZUMAB_AXIAL_AUTO_FULL_REVIEW.html** (3 items)
  - COAST-X: crude RR 0.440 vs published effect 2.36 — opposite directions
  - NCT04285229: crude RR 0.203 vs published effect 7.64 — opposite directions
- **MIS_COLECTOMY_VS_OPEN_NMA_REVIEW.html** (3 items)
  - COLOR-II: crude RR 0.790 vs published effect 1.06 — opposite directions
  - ALaCaRT: crude RR 1.078 vs published effect 0.82 — opposite directions
- **AML_TARGETED_NEW_REVIEW.html** (2 items)
  - QuANTUM-R: crude RR 1.052 vs published effect 0.776 — opposite directions
  - IDHENTIFY: crude RR 1.091 vs published effect 0.92 — opposite directions

### `RM-A12` — Effect estimate contradicts its own 2x2 (134 apps, P0)

- **IXEKIZUMAB_AXIAL_AUTO_FULL_REVIEW.html** (4 items)
  - COAST-W: displayed effect 2.41 vs crude ratio 0.000 from ledger counts — opposite sides of 1
  - COAST-X: displayed effect 2.36 vs crude ratio 0.440 from ledger counts — opposite sides of 1
- **BIMEKIZUMAB_PSORIATIC_AUTO_FULL_REVIEW.html** (3 items)
  - BE OPTIMAL: displayed effect 7.082 vs crude ratio 0.227 from ledger counts — opposite sides of 1
  - BE COMPLETE: displayed effect 11.139 vs crude ratio 0.156 from ledger counts — opposite sides of 1
- **BOCOCIZUMAB_LIPID_AUTO_FULL_REVIEW.html** (3 items)
  - SPIRE-LL: displayed effect 50.0 vs crude ratio 0.139 from ledger counts — opposite sides of 1
  - SPIRE-HR: displayed effect 56.6 vs crude ratio 0.506 from ledger counts — opposite sides of 1
- **MIS_COLECTOMY_VS_OPEN_NMA_REVIEW.html** (3 items)
  - COLOR-II: displayed effect 1.06 vs crude ratio 0.790 from ledger counts — opposite sides of 1
  - ALaCaRT: displayed effect 0.82 vs crude ratio 1.078 from ledger counts — opposite sides of 1
- **AML_TARGETED_NEW_REVIEW.html** (2 items)
  - QuANTUM-R: displayed effect 0.776 vs crude ratio 1.052 from ledger counts — opposite sides of 1
  - IDHENTIFY: displayed effect 0.92 vs crude ratio 1.091 from ledger counts — opposite sides of 1

### `RM-D02` — Wrong or cross-topic citation (132 apps, P1)

- **ANTI_CD20_MS_REVIEW.html** (3 items)
  - PMID 28002679 cited for 2 different trials: ['OPERA I', 'OPERA II']
  - PMID 32757523 cited for 2 different trials: ['ASCLEPIOS I', 'ASCLEPIOS II']
- **ANTIVEGF_NAMD_NMA_REVIEW.html** (3 items)
  - PMID 23084240 cited for 2 different trials: ['VIEW-1', 'VIEW-2']
  - PMID 35085502 cited for 2 different trials: ['LUCERNE', 'TENAYA']
- **HCV_DAA_NEW_NMA_REVIEW.html** (3 items)
  - PMID 26575258 cited for 2 different trials: ['ASTRAL-1', 'ASTRAL-2']
  - PMID 28564569 cited for 2 different trials: ['POLARIS-2', 'POLARIS-3']
- **IBD_BIOLOGICS_REVIEW.html** (3 items)
  - PMID 27959607 cited for 3 different trials: ['IM-UNITI', 'UNITI-1', 'UNITI-2']
  - PMID 35644154 cited for 2 different trials: ['ADVANCE', 'MOTIVATE']
- **IL_PSORIASIS_NMA_REVIEW.html** (3 items)
  - PMID 26072109 cited for 2 different trials: ['UNCOVER-2', 'UNCOVER-3']
  - PMID 25007392 cited for 2 different trials: ['ERASURE', 'FIXTURE']

### `RM-E03` — Registry/monitoring watchlist tracks the wrong drug class (56 apps, P0)

- **ACS_ANTIPLATELET_REVIEW.html** (1 item)
  - the monitored registry watchlist tracks FINERENONE trials ['FIDELIO-DKD', 'FIGARO-DKD', 'FINEARTS-HF', 'ARTS-DN', 'FINE-ONE', 'CONFIDENCE'] in an app about 'RapidMeta Cardio | ACS Antiplatelet NMA (Clopidogrel / Ticag' — full watchlist: ['FIDELIO-DKD', 'FIGARO-DKD', 'FINEARTS-HF', 'ARTS-DN', 'CONFID
- **ADC_HER2_ADJUVANT_REVIEW.html** (1 item)
  - the monitored registry watchlist tracks FINERENONE trials ['FIDELIO-DKD', 'FIGARO-DKD', 'FINEARTS-HF', 'ARTS-DN', 'FINE-ONE', 'CONFIDENCE'] in an app about 'RapidMeta Oncology | ADC NMA in HER2+ Early Breast Cancer Ad' — full watchlist: ['FIDELIO-DKD', 'FIGARO-DKD', 'FINEARTS-HF', 'ARTS-DN', 'CONFID
- **ADC_HER2_LOW_REVIEW.html** (1 item)
  - the monitored registry watchlist tracks FINERENONE trials ['FIDELIO-DKD', 'FIGARO-DKD', 'FINEARTS-HF', 'ARTS-DN', 'FINE-ONE', 'CONFIDENCE'] in an app about 'RapidMeta Oncology | ADC NMA in HER2-Low Metastatic Breast C' — full watchlist: ['FIDELIO-DKD', 'FIGARO-DKD', 'FINEARTS-HF', 'ARTS-DN', 'CONFID
- **ADC_HER2_NMA_REVIEW.html** (1 item)
  - the monitored registry watchlist tracks FINERENONE trials ['FIDELIO-DKD', 'FIGARO-DKD', 'FINEARTS-HF', 'ARTS-DN', 'FINE-ONE', 'CONFIDENCE'] in an app about 'RapidMeta Oncology | ADC NMA in HER2+ MBC 2L+ PFS v1.2 (spli' — full watchlist: ['FIDELIO-DKD', 'FIGARO-DKD', 'FINEARTS-HF', 'ARTS-DN', 'CONFID
- **ANTI_CD20_MS_REVIEW.html** (1 item)
  - the monitored registry watchlist tracks FINERENONE trials ['FIDELIO-DKD', 'FIGARO-DKD', 'FINEARTS-HF', 'ARTS-DN', 'FINE-ONE', 'CONFIDENCE'] in an app about 'RapidMeta Neurology | Anti-CD20 Therapies in Relapsing MS — ' — full watchlist: ['FIDELIO-DKD', 'FIGARO-DKD', 'FINEARTS-HF', 'ARTS-DN', 'CONFID

### `RM-B08` — Search under-inclusion vs a known external synthesis (33 apps, P1)

- **ARPI_NMCRPC_REVIEW.html** (1 item)
  - the app pools k=3 while a benchmark record in the same file declares k=6 — verify the search, and record an explicit include/exclude decision for every eligible trial (omitting one silently is selection bias)
- **ATOPIC_DERM_NMA_REVIEW.html** (1 item)
  - the app pools k=7 while a benchmark record in the same file declares k=97 — verify the search, and record an explicit include/exclude decision for every eligible trial (omitting one silently is selection bias)
- **BIMEKIZUMAB_PSORIASIS_REVIEW.html** (1 item)
  - the app pools k=3 while a benchmark record in the same file declares k=179 — verify the search, and record an explicit include/exclude decision for every eligible trial (omitting one silently is selection bias)
- **BIOLOGIC_ASTHMA_REVIEW.html** (1 item)
  - the app pools k=4 while a benchmark record in the same file declares k=8 — verify the search, and record an explicit include/exclude decision for every eligible trial (omitting one silently is selection bias)
- **CARDIORENAL_DKD_NMA_REVIEW.html** (1 item)
  - the app pools k=6 while a benchmark record in the same file declares k=13 — verify the search, and record an explicit include/exclude decision for every eligible trial (omitting one silently is selection bias)

### `RM-C01` — Randomised vs analysed denominator unlabelled (30 apps, P2)

- **MIGRAINE_ACUTE_REVIEW.html** (4 items)
  - Rimegepant Study 303 (75 mg ODT): baseline n=854 vs arms 669+682=1351 (58.2% gap) with no randomised/analysed label
  - Rimegepant Study 301 (75 mg): baseline n=920 vs arms 543+541=1084 (17.8% gap) with no randomised/analysed label
- **SPONDYLOARTHRITIS_REVIEW.html** (3 items)
  - COAST-V (ixekizumab): baseline n=233 vs arms 81+87=168 (27.9% gap) with no randomised/analysed label
  - BE MOBILE 1: baseline n=386 vs arms 128+126=254 (34.2% gap) with no randomised/analysed label
- **COVID19_HOSPITALIZED_TX_REVIEW.html** (2 items)
  - REMAP-CAP-IL6: baseline n=803 vs arms 366+412=778 (3.1% gap) with no randomised/analysed label
  - EPIC-HR: baseline n=2246 vs arms 1039+1046=2085 (7.2% gap) with no randomised/analysed label
- **COVID19_VACCINES_REVIEW.html** (2 items)
  - COVE (mRNA-1273): baseline n=30420 vs arms 14134+14073=28207 (7.3% gap) with no randomised/analysed label
  - Sputnik V: baseline n=21977 vs arms 14964+4902=19866 (9.6% gap) with no randomised/analysed label
- **HIV_ART_FIRSTLINE_REVIEW.html** (2 items)
  - ADVANCE DTG/TAF: baseline n=702 vs arms 351+176=527 (24.9% gap) with no randomised/analysed label
  - ADVANCE DTG/TDF: baseline n=702 vs arms 351+175=526 (25.1% gap) with no randomised/analysed label

### `RM-D09` — Phase label inapplicable to a device or behavioural trial (23 apps, P1)

- **CRYO_AF_ABLATION_NMA_REVIEW.html** (7 items)
  - CRYO-FIRST: ledger phase 'III' on a device trial — ClinicalTrials.gov records these as phase Not Applicable; a phase-III/IV eligibility rule would wrongly exclude it
  - STOP-AF-First: ledger phase 'III' on a device trial — ClinicalTrials.gov records these as phase Not Applicable; a phase-III/IV eligibility rule would wrongly exclude it
- **MITRACLIP_TEER_REVIEW.html** (6 items)
  - COAPT: ledger phase 'III' on a device trial — ClinicalTrials.gov records these as phase Not Applicable; a phase-III/IV eligibility rule would wrongly exclude it
  - MITRA-FR: ledger phase 'III' on a device trial — ClinicalTrials.gov records these as phase Not Applicable; a phase-III/IV eligibility rule would wrongly exclude it
- **TRICUSPID_TEER_TMVR_NMA_REVIEW.html** (6 items)
  - TRILUMINATE-Pivotal: ledger phase 'III' on a device trial — ClinicalTrials.gov records these as phase Not Applicable; a phase-III/IV eligibility rule would wrongly exclude it
  - TRISCEND-II: ledger phase 'III' on a device trial — ClinicalTrials.gov records these as phase Not Applicable; a phase-III/IV eligibility rule would wrongly exclude it
- **ABLATION_AF_REVIEW.html** (4 items)
  - CASTLE-AF: ledger phase 'III' on a device trial — ClinicalTrials.gov records these as phase Not Applicable; a phase-III/IV eligibility rule would wrongly exclude it
  - CABANA: ledger phase 'III' on a device trial — ClinicalTrials.gov records these as phase Not Applicable; a phase-III/IV eligibility rule would wrongly exclude it
- **PFA_AF_PULSED_FIELD_REVIEW.html** (4 items)
  - PULSED-AF: ledger phase 'III' on a device trial — ClinicalTrials.gov records these as phase Not Applicable; a phase-III/IV eligibility rule would wrongly exclude it
  - ADVENT: ledger phase 'III' on a device trial — ClinicalTrials.gov records these as phase Not Applicable; a phase-III/IV eligibility rule would wrongly exclude it

### `RM-D06` — App identity mismatch (21 apps, P1)

- **AGRYLIN_ET_AUTO_FULL_REVIEW.html** (1 item)
  - filename tokens ['agrylin'] appear in neither the title ('RapidMeta | Anagrelide in essential thrombocythemia (audit-first, full-functiona') nor any ledger group
- **BURADIRAGAB_AUTO_FULL_REVIEW.html** (1 item)
  - filename tokens ['buradiragab'] appear in neither the title ('RapidMeta | Rituximab in AAV / IgG4-RD (audit-first, full-functionality)') nor any ledger group
- **CAB_PREP_HIV_REVIEW.html** (1 item)
  - filename tokens ['prep'] appear in neither the title ('RapidMeta Infectious Disease | Cabotegravir LA for HIV Pre-Exposure Prophylaxis ') nor any ledger group
- **DOAC_AF_REVIEW.html** (1 item)
  - filename tokens ['doac'] appear in neither the title ('RapidMeta Cardiology | Direct Oral Anticoagulants vs Warfarin in Non-Valvular At') nor any ledger group
- **HEPATITIS_HCV_DAA_REVIEW.html** (1 item)
  - filename tokens ['hepatitis'] appear in neither the title ('RapidMeta Hepatology | Pan-Genotypic HCV DAA Therapy NMA v0.1 (post-2014)') nor any ledger group

### `RM-D11` — Published pooled estimate presented as a trial-level effect (21 apps, P1)

- **HIGH_EFFICACY_MS_REVIEW.html** (4 items)
  - OPERA-I: its own evidence prose describes a pooled/meta analysis while 0.54 is displayed as this trial's effect
  - OPERA-II: trial-level effect 0.53 equals a stored benchmark POOLED estimate 0.53 (0.4-0.71)
- **GLP1_CVOT_REVIEW.html** (3 items)
  - ELIXA: its own evidence prose describes a pooled/meta analysis while 1.02 is displayed as this trial's effect
  - SUSTAIN-6: its own evidence prose describes a pooled/meta analysis while 0.74 is displayed as this trial's effect
- **e156-submission/assets/GLP1_CVOT_REVIEW.html** (3 items)
  - ELIXA: its own evidence prose describes a pooled/meta analysis while 1.02 is displayed as this trial's effect
  - SUSTAIN-6: its own evidence prose describes a pooled/meta analysis while 0.74 is displayed as this trial's effect
- **e156-submission/assets/PCSK9_REVIEW.html** (2 items)
  - FOURIER: trial-level effect 0.85 equals a stored benchmark POOLED estimate 0.85 (0.78-0.93)
  - ODYSSEY OUTCOMES: trial-level effect 0.85 equals a stored benchmark POOLED estimate 0.85 (0.78-0.93)
- **ANTI_CD20_MS_REVIEW.html** (1 item)
  - OPERA II: trial-level effect 0.53 equals a stored benchmark POOLED estimate 0.53 (0.4-0.71)

### `RM-F07` — Unearned confidence on unsourced fields (17 apps, P1)

- **ADC_HER2_ADJUVANT_REVIEW.html** (1 item)
  - fabrication-risk 0.000 while __verdict records P2_evidence_incomplete=1
- **ADC_HER2_LOW_REVIEW.html** (1 item)
  - fabrication-risk 0.000 while __verdict records P2_evidence_incomplete=2
- **ADC_HER2_NMA_REVIEW.html** (1 item)
  - fabrication-risk 0.000 while __verdict records P2_evidence_incomplete=4
- **AFICAMTEN_HCM_REVIEW.html** (1 item)
  - fabrication-risk 0.000 while __verdict records P2_evidence_incomplete=1
- **COLCHICINE_CVD_REVIEW.html** (1 item)
  - fabrication-risk 0.000 while __verdict records P2_evidence_incomplete=3

### `RM-D01` — Wrong NCT / registry-concordance failure (10 apps, P1)

- **COVID19_HOSPITALIZED_TX_REVIEW.html** (3 items)
  - malformed registry identifier: NCT04381936c
  - malformed registry identifier: NCT04381936d
- **INTENSIVE_BP_REVIEW.html** (2 items)
  - malformed registry identifier: NCT01206062_SENIOR
  - malformed registry identifier: NCT01206062_CKD
- **PEGCETACOPLAN_GA_REVIEW.html** (2 items)
  - malformed registry identifier: NCT03525613_PEOM
  - malformed registry identifier: NCT03525600_PEOM
- **RENAL_DENERV_REVIEW.html** (2 items)
  - malformed registry identifier: NCT02439749_ON
  - malformed registry identifier: NCT02439749_OFF
- **e156-submission/assets/INTENSIVE_BP_REVIEW.html** (2 items)
  - malformed registry identifier: NCT01206062_SENIOR
  - malformed registry identifier: NCT01206062_CKD

### `RM-A13` — Estimand-granularity mismatch: composite component sets differ (9 apps, P0)

- **COLCHICINE_CVD_REVIEW.html** (1 item)
  - primary composites with DIFFERENT component sets are pooled under one scope: [core-3] COLCOT: "Composite (CV Death, Cardiac Arrest, MI, Stroke, Urgent Revasc)"; LoDoCo2: "Composite (CV Death, Spontaneous MI, Ischaemic Stroke, Ischaemia-Driven Revasc)" || [unstable-angina] CONVINCE: "Composite (Recur
- **EVOLOCUMAB_DYSLIPIDEMIA_AUTO_FULL_REVIEW.html** (1 item)
  - primary composites with DIFFERENT component sets are pooled under one scope: [revasc+unstable-angina] FOURIER: "Time to Cardiovascular Death, Myocardial Infarction, Hospitalization for Unstable Angina, " || [core-3] OSLER-2: "Number of Participants With Adverse Events (primary)"
- **OMEGA3_HIGHDOSE_CV_REVIEW.html** (1 item)
  - primary composites with DIFFERENT component sets are pooled under one scope: [revasc+unstable-angina] REDUCE-IT: "Composite CV death, MI, stroke, revascularization, unstable angina (5-component MACE)"; STRENGTH: "Composite CV death, MI, stroke, revascularization, unstable angina" || [core-3] VITAL: 
- **PCSK9_INHIBITORS_CV_REVIEW.html** (1 item)
  - primary composites with DIFFERENT component sets are pooled under one scope: [unstable-angina] FOURIER: "Composite CV death/MI/stroke/unstable angina/revasc (5-pt MACE)" || [unstable-angina+CHD-death] ODYSSEY OUTCOMES: "Composite CHD death/MI/stroke/unstable angina (4-pt MACE)"
- **PCSK9_LIPID_NMA_REVIEW.html** (1 item)
  - primary composites with DIFFERENT component sets are pooled under one scope: [core-3] IMPROVE-IT: "Primary composite (CV death/MI/UA hosp/coronary revasc/stroke) ezetimibe+simva vs simva (I"; FOURIER: "CV death/MI/stroke/UA hosp/coronary revasc evolocumab vs placebo (FOURIER primary; median " || [CH

### `RM-A01` — Recurrent-event coercion (8 apps, P0)

- **FCM_HF_REVIEW.html** (4 items)
  - AFFIRM-AHF (NCT02937454) carries tE=293 cE=372 with estimandType=HR — 293 vs 372 TOTAL recurrent events; rate ratio 0.79
  - AFFIRM-AHF primary row 'Total HF hospitalizations and CV death at 52 weeks' has per-arm counts under estimandType=HR
- **IV_IRON_HF_REVIEW.html** (4 items)
  - AFFIRM-AHF (NCT02937454) carries tE=293 cE=372 with estimandType=ABSENT — 293 vs 372 TOTAL recurrent events; rate ratio 0.79
  - AFFIRM-AHF primary row 'Total HF hospitalizations and CV death' has per-arm counts under estimandType=ABSENT
- **e156-submission/assets/IV_IRON_HF_REVIEW.html** (4 items)
  - AFFIRM-AHF (NCT02937454) carries tE=293 cE=372 with estimandType=ABSENT — 293 vs 372 TOTAL recurrent events; rate ratio 0.79
  - AFFIRM-AHF primary row 'Total HF hospitalizations and CV death' has per-arm counts under estimandType=ABSENT
- **SOTAGLIFLOZIN_HF_AUTO_FULL_REVIEW.html** (2 items)
  - SCORED (NCT03315143) carries tE=6 cE=8 with estimandType=ABSENT — recurrent-event primary (co-primaries)
  - SCORED primary row 'Number of Total Occurrences of Cardiovascular (CV) Death, Hospitalizations for Heart Failure (HHF) and Urgent Visits for (primary)' has per-arm counts under estimandType=HR
- **e156-submission/assets/ARNI_HF_REVIEW.html** (2 items)
  - PARAGON-HF (NCT01920711) carries tE=526 cE=557 with estimandType=ABSENT — 894 vs 1009 TOTAL events; rate ratio 0.87, not a hazard ratio
  - PARAGON-HF primary row 'CV death or total HF hospitalizations' has per-arm counts under estimandType=ABSENT

### `RM-A10` — Kaplan-Meier risk rendered as a crude event count (5 apps, P0)

- **GLP1_CVOT_REVIEW.html** (3 items)
  - LEADER: treatment 608/4668 = 13.0% reproduces the 13.0% figure, and the source states it as a per-patient-year rate — "ts (5.7%) in the liraglutide group (1.5 per 100 patient-years) vs 337 patients (7.2%) in the placebo group (1.9 per 100 patient-ye"
  - AMPLITUDE-O: treatment 189/2717 = 7.0% reproduces the 7.0% figure, and the source states it as a per-patient-year rate — "in the pooled efpeglenatide group (3.9 per 100 person-years) and 125 of 1,359 patients (9.2%) in the placebo group (5.3 per 100 p"
- **e156-submission/assets/GLP1_CVOT_REVIEW.html** (3 items)
  - LEADER: treatment 608/4668 = 13.0% reproduces the 13.0% figure, and the source states it as a per-patient-year rate — "ts (5.7%) in the liraglutide group (1.5 per 100 patient-years) vs 337 patients (7.2%) in the placebo group (1.9 per 100 patient-ye"
  - AMPLITUDE-O: treatment 189/2717 = 7.0% reproduces the 7.0% figure, and the source states it as a per-patient-year rate — "in the pooled efpeglenatide group (3.9 per 100 person-years) and 125 of 1,359 patients (9.2%) in the placebo group (5.3 per 100 p"
- **MITRAL_FUNCMR_REVIEW.html** (1 item)
  - COAPT: control 212/312 = 67.9% reproduces the 67.9% figure, and the source states it as a per-patient-year rate — "one (n=312). Enrollment & Randomization Annualized rate of HF hospitalizations at 24 months: 35.8% per patient-year with MitraClip"
- **OSTEOPOROSIS_BROAD_NMA_REVIEW.html** (1 item)
  - FREEDOM: treatment 86/3886 = 2.2% reproduces the 2.3% figure, and the source states it as a Kaplan-Meier estimate — "radiographic vertebral fracture, with a cumulative incidence of 2.3% in the denosumab group, versus 7.2% in the placebo group (ris"
- **removed/TAVR_LOWRISK_REVIEW.html** (1 item)
  - PARTNER 3: treatment 42/496 = 8.5% reproduces the 8.5% figure, and the source states it as a Kaplan-Meier estimate — "CI 0.37-0.79; P<0.001 for superiority). Kaplan-Meier curves separate at 30 days and remain divergent through 12 months. Primary —"

### `RM-C04` — Arm reversal: intervention and control denominators swapped (4 apps, P0)

- **COVID19_HOSPITALIZED_TX_REVIEW.html** (1 item)
  - ACTT-2: evidence names the intervention arm as n=518, which is the ledger's CONTROL denominator (tN=515, cN=518) — "treatment and 518"
- **VITAMIN_C_THIAMINE_SEPSIS_REVIEW.html** (1 item)
  - VITAMINS: evidence names the intervention arm as n=109, which is the ledger's CONTROL denominator (tN=107, cN=109) — "INTERVENTIONS: Patients were randomized to the intervention group (n = 109"
- **removed/STROKE_THROMBECTOMY_LATE_NMA_REVIEW.html** (1 item)
  - MR-CLEAN: evidence names the intervention arm as n=267, which is the ledger's CONTROL denominator (tN=233, cN=267) — "treatment and 267"
- **retired/MENTAL_HEALTH_FRIENDSHIP_BENCH_REVIEW.html** (1 item)
  - Friendship Bench Zimbabwe: evidence names the intervention arm as n=287, which is the ledger's CONTROL denominator (tN=286, cN=287) — "intervention, 287"

### `RM-A04` — Peto output labelled HR (3 apps, P1)

- **INCRETIN_HFpEF_REVIEW.html** (3 items)
  - Peto near an HR label: PetoHrF",title:"Worsening HF events (Peto HR from counts)",tE:null,cE:null,type:"PRIMARY",
  - Peto near an HR label: Peto HR from counts)",tE:null,cE:null,type:"PRIMARY",pubHR:.18,pubHR_LCI:.06,pubHR_UCI:.54
- **COLCHICINE_CVD_REVIEW.html** (1 item)
  - Peto near an HR label: petoResult.uci})}}else document.getElementById("res-mh").innerText=isHRMode?"N/A (HR mode)
- **GLP1_CVOT_REVIEW.html** (1 item)
  - Peto near an HR label: petoResult.uci})}}else document.getElementById("res-mh").innerText=isHRMode?"N/A (HR mode)

### `RM-A09` — Win-ratio estimate paired with an HR (3 apps, P1)

- **IV_IRON_HF_REVIEW.html** (1 item)
  - HEART-FID: a win-ratio trial carries publishedHR=0.93
- **TRICUSPID_TEER_TMVR_NMA_REVIEW.html** (1 item)
  - TRILUMINATE-Pivotal: a win-ratio trial carries publishedHR=2.08
- **e156-submission/assets/IV_IRON_HF_REVIEW.html** (1 item)
  - HEART-FID: a win-ratio trial carries publishedHR=0.93

### `RM-V01` — Displayed value contradicts the source-verified fixture (3 apps, P0)

- **BEMPEDOIC_ACID_REVIEW.html** (2 items)
  - CLEAR Wisdom: ledger carries NCT02973841, the verified identifier is NCT02991118 — NCT02973841 = 'Sono-ease Device for Internal Jaguar Vein Cannulation', Mansoura University, n=40, ages 18-45, INTERVENTIONAL, phase NA, has_results false. Its e
  - CLEAR Wisdom: displays "JAMA. 2019;322(14):1380-1388"; verified citation is "JAMA 2019;322(18):1780-1788, PMID 31714986"
- **e156-submission/assets/BEMPEDOIC_ACID_REVIEW.html** (2 items)
  - fixture trial 'NULLED:NCT02666664' (CLEAR Harmony) is absent from the ledger
  - fixture trial 'NULLED:NCT02973841' (CLEAR Wisdom) is absent from the ledger
- **MITRAL_FUNCMR_REVIEW.html** (1 item)
  - RESHAPE-HF2: ARM REVERSAL — tN=255 is the CONTROL n (255); the device arm is 250 [verified: Textbook multi-error instance: scope-lock, arm reversal, recurrent-event coercion, KM-as-crude-count, cross-endpoint escalc pooling, RoB self-contradiction, false registry-status, device phase mislabel.]

## 4. Worst offenders overall — apps by distinct error types

| app | distinct error types | k | ids |
|---|---:|---:|---|
| `BIMEKIZUMAB_AXIAL_AUTO_FULL_REVIEW.html` | 29 | 4 | `RM-A02`, `RM-A05`, `RM-A07`, `RM-A08`, `RM-A12`, `RM-A14`, `RM-B01`, `RM-B02`, `RM-B03`, `RM-D02`, `RM-D08`, `RM-D10`, `RM-E01`, `RM-E02`, `RM-F01`, `RM-F02`, `RM-F03`, `RM-F04`, `RM-F05`, `RM-G01`, `RM-G03`, `RM-H01`, `RM-H02`, `RM-H04`, `RM-H05`, `RM-I01`, `RM-J01`, `RM-J02`, `RM-J07` |
| `BOCOCIZUMAB_LIPID_AUTO_FULL_REVIEW.html` | 29 | 5 | `RM-A02`, `RM-A05`, `RM-A07`, `RM-A08`, `RM-A12`, `RM-A14`, `RM-B01`, `RM-B02`, `RM-B03`, `RM-D02`, `RM-D08`, `RM-D10`, `RM-E01`, `RM-E02`, `RM-F01`, `RM-F02`, `RM-F03`, `RM-F04`, `RM-F05`, `RM-G01`, `RM-G03`, `RM-H01`, `RM-H02`, `RM-H04`, `RM-H05`, `RM-I01`, `RM-J01`, `RM-J02`, `RM-J07` |
| `ELAGOLIX_HMB_AUTO_FULL_REVIEW.html` | 29 | 3 | `RM-A02`, `RM-A05`, `RM-A07`, `RM-A08`, `RM-A12`, `RM-A14`, `RM-B01`, `RM-B02`, `RM-B03`, `RM-D02`, `RM-D08`, `RM-D10`, `RM-E01`, `RM-E02`, `RM-F01`, `RM-F02`, `RM-F03`, `RM-F04`, `RM-F05`, `RM-G01`, `RM-G03`, `RM-H01`, `RM-H02`, `RM-H04`, `RM-H05`, `RM-I01`, `RM-J01`, `RM-J02`, `RM-J07` |
| `HPV_DOSE_REDUCTION_REVIEW.html` | 29 | 3 | `RM-A02`, `RM-A03`, `RM-A05`, `RM-A14`, `RM-B02`, `RM-B03`, `RM-C01`, `RM-D01`, `RM-D02`, `RM-D05`, `RM-D07`, `RM-D08`, `RM-D10`, `RM-E01`, `RM-E02`, `RM-F01`, `RM-F03`, `RM-F04`, `RM-F05`, `RM-G01`, `RM-G03`, `RM-H01`, `RM-H02`, `RM-H04`, `RM-H05`, `RM-I01`, `RM-J01`, `RM-J02`, `RM-J07` |
| `JAKI_AD_REVIEW.html` | 29 | 6 | `RM-A02`, `RM-A05`, `RM-A14`, `RM-B01`, `RM-B02`, `RM-B03`, `RM-D02`, `RM-D05`, `RM-D07`, `RM-D08`, `RM-D10`, `RM-D11`, `RM-E01`, `RM-E02`, `RM-F01`, `RM-F02`, `RM-F03`, `RM-F04`, `RM-F05`, `RM-G01`, `RM-G03`, `RM-H01`, `RM-H02`, `RM-H04`, `RM-H05`, `RM-I01`, `RM-J01`, `RM-J02`, `RM-J07` |
| `LIGELIZUMAB_URTICARIA_AUTO_2_FULL_REVIEW.html` | 29 | 3 | `RM-A02`, `RM-A05`, `RM-A07`, `RM-A08`, `RM-A12`, `RM-A14`, `RM-B01`, `RM-B02`, `RM-B03`, `RM-D02`, `RM-D08`, `RM-D10`, `RM-E01`, `RM-E02`, `RM-F01`, `RM-F02`, `RM-F03`, `RM-F04`, `RM-F05`, `RM-G01`, `RM-G03`, `RM-H01`, `RM-H02`, `RM-H04`, `RM-H05`, `RM-I01`, `RM-J01`, `RM-J02`, `RM-J07` |
| `LIGELIZUMAB_URTICARIA_AUTO_FULL_REVIEW.html` | 29 | 3 | `RM-A02`, `RM-A05`, `RM-A07`, `RM-A08`, `RM-A12`, `RM-A14`, `RM-B01`, `RM-B02`, `RM-B03`, `RM-D02`, `RM-D08`, `RM-D10`, `RM-E01`, `RM-E02`, `RM-F01`, `RM-F02`, `RM-F03`, `RM-F04`, `RM-F05`, `RM-G01`, `RM-G03`, `RM-H01`, `RM-H02`, `RM-H04`, `RM-H05`, `RM-I01`, `RM-J01`, `RM-J02`, `RM-J07` |
| `MAGROLIMAB_AML_AUTO_FULL_REVIEW.html` | 29 | 3 | `RM-A02`, `RM-A05`, `RM-A07`, `RM-A08`, `RM-A12`, `RM-A14`, `RM-B01`, `RM-B02`, `RM-B03`, `RM-D02`, `RM-D08`, `RM-D10`, `RM-E01`, `RM-E02`, `RM-F01`, `RM-F02`, `RM-F03`, `RM-F04`, `RM-F05`, `RM-G01`, `RM-G03`, `RM-H01`, `RM-H02`, `RM-H04`, `RM-H05`, `RM-I01`, `RM-J01`, `RM-J02`, `RM-J07` |
| `MIPOMERSEN_HOFH_AUTO_FULL_REVIEW.html` | 29 | 4 | `RM-A02`, `RM-A05`, `RM-A07`, `RM-A08`, `RM-A12`, `RM-A14`, `RM-B01`, `RM-B02`, `RM-B03`, `RM-D02`, `RM-D08`, `RM-D10`, `RM-E01`, `RM-E02`, `RM-F01`, `RM-F02`, `RM-F03`, `RM-F04`, `RM-F05`, `RM-G01`, `RM-G03`, `RM-H01`, `RM-H02`, `RM-H04`, `RM-H05`, `RM-I01`, `RM-J01`, `RM-J02`, `RM-J07` |
| `MITRAL_FUNCMR_REVIEW.html` | 29 | 3 | `RM-A02`, `RM-A05`, `RM-A10`, `RM-A14`, `RM-B01`, `RM-B02`, `RM-B03`, `RM-D05`, `RM-D07`, `RM-D08`, `RM-D09`, `RM-D10`, `RM-E01`, `RM-E02`, `RM-F01`, `RM-F03`, `RM-F04`, `RM-F05`, `RM-G01`, `RM-G03`, `RM-H01`, `RM-H02`, `RM-H04`, `RM-H05`, `RM-I01`, `RM-J01`, `RM-J02`, `RM-J07`, `RM-V01` |
| `OMALIZUMAB_URTICARIA_AUTO_FULL_REVIEW.html` | 29 | 3 | `RM-A02`, `RM-A05`, `RM-A07`, `RM-A08`, `RM-A12`, `RM-A14`, `RM-B01`, `RM-B02`, `RM-B03`, `RM-D02`, `RM-D08`, `RM-D10`, `RM-E01`, `RM-E02`, `RM-F01`, `RM-F02`, `RM-F03`, `RM-F04`, `RM-F05`, `RM-G01`, `RM-G03`, `RM-H01`, `RM-H02`, `RM-H04`, `RM-H05`, `RM-I01`, `RM-J01`, `RM-J02`, `RM-J07` |
| `TIRZEPATIDE_ARDS_AUTO_FULL_REVIEW.html` | 29 | 3 | `RM-A02`, `RM-A05`, `RM-A07`, `RM-A08`, `RM-A12`, `RM-A14`, `RM-B01`, `RM-B02`, `RM-B03`, `RM-D02`, `RM-D06`, `RM-D08`, `RM-D10`, `RM-E01`, `RM-E02`, `RM-F01`, `RM-F02`, `RM-F03`, `RM-F04`, `RM-F05`, `RM-G01`, `RM-H01`, `RM-H02`, `RM-H04`, `RM-H05`, `RM-I01`, `RM-J01`, `RM-J02`, `RM-J07` |
| `ALIROCUMAB_LIPID_AUTO_FULL_REVIEW.html` | 28 | 6 | `RM-A02`, `RM-A05`, `RM-A07`, `RM-B01`, `RM-B02`, `RM-B03`, `RM-D02`, `RM-D08`, `RM-D10`, `RM-E01`, `RM-E02`, `RM-F01`, `RM-F02`, `RM-F03`, `RM-F04`, `RM-F05`, `RM-G01`, `RM-G02`, `RM-G03`, `RM-H01`, `RM-H02`, `RM-H03`, `RM-H04`, `RM-H05`, `RM-I01`, `RM-J01`, `RM-J02`, `RM-J07` |
| `ANDEXANET_BLEEDING_AUTO_FULL_REVIEW.html` | 28 | 3 | `RM-A02`, `RM-A05`, `RM-A07`, `RM-A08`, `RM-A12`, `RM-A14`, `RM-B01`, `RM-B02`, `RM-B03`, `RM-D02`, `RM-D08`, `RM-D10`, `RM-E01`, `RM-E02`, `RM-F01`, `RM-F02`, `RM-F03`, `RM-F04`, `RM-F05`, `RM-G01`, `RM-H01`, `RM-H02`, `RM-H04`, `RM-H05`, `RM-I01`, `RM-J01`, `RM-J02`, `RM-J07` |
| `ANIDULAFUNGIN_CANDIDA_AUTO_FULL_REVIEW.html` | 28 | 3 | `RM-A02`, `RM-A05`, `RM-A07`, `RM-A08`, `RM-A12`, `RM-A14`, `RM-B01`, `RM-B02`, `RM-B03`, `RM-D02`, `RM-D08`, `RM-D10`, `RM-E01`, `RM-E02`, `RM-F01`, `RM-F02`, `RM-F03`, `RM-F04`, `RM-F05`, `RM-G01`, `RM-H01`, `RM-H02`, `RM-H04`, `RM-H05`, `RM-I01`, `RM-J01`, `RM-J02`, `RM-J07` |
| `BARICITINIB_AD_AUTO_FULL_REVIEW.html` | 28 | 4 | `RM-A02`, `RM-A05`, `RM-A08`, `RM-A12`, `RM-A14`, `RM-B01`, `RM-B02`, `RM-B03`, `RM-D02`, `RM-D08`, `RM-D10`, `RM-E01`, `RM-E02`, `RM-F01`, `RM-F02`, `RM-F03`, `RM-F04`, `RM-F05`, `RM-G01`, `RM-G03`, `RM-H01`, `RM-H02`, `RM-H04`, `RM-H05`, `RM-I01`, `RM-J01`, `RM-J02`, `RM-J07` |
| `BARICITINIB_SLE_AUTO_FULL_REVIEW.html` | 28 | 3 | `RM-A02`, `RM-A05`, `RM-A08`, `RM-A12`, `RM-A14`, `RM-B01`, `RM-B02`, `RM-B03`, `RM-D02`, `RM-D08`, `RM-D10`, `RM-E01`, `RM-E02`, `RM-F01`, `RM-F02`, `RM-F03`, `RM-F04`, `RM-F05`, `RM-G01`, `RM-G03`, `RM-H01`, `RM-H02`, `RM-H04`, `RM-H05`, `RM-I01`, `RM-J01`, `RM-J02`, `RM-J07` |
| `BIMEKIZUMAB_PSORIATIC_AUTO_FULL_REVIEW.html` | 28 | 3 | `RM-A02`, `RM-A05`, `RM-A07`, `RM-A08`, `RM-A12`, `RM-A14`, `RM-B01`, `RM-B02`, `RM-B03`, `RM-D08`, `RM-D10`, `RM-E01`, `RM-E02`, `RM-F01`, `RM-F02`, `RM-F03`, `RM-F04`, `RM-F05`, `RM-G01`, `RM-G03`, `RM-H01`, `RM-H02`, `RM-H04`, `RM-H05`, `RM-I01`, `RM-J01`, `RM-J02`, `RM-J07` |
| `CART_DLBCL_REVIEW.html` | 28 | 3 | `RM-A02`, `RM-A05`, `RM-A08`, `RM-A12`, `RM-A14`, `RM-B01`, `RM-B02`, `RM-B03`, `RM-D05`, `RM-D07`, `RM-D08`, `RM-D10`, `RM-E01`, `RM-E02`, `RM-F01`, `RM-F03`, `RM-F04`, `RM-F05`, `RM-G01`, `RM-G03`, `RM-H01`, `RM-H02`, `RM-H04`, `RM-H05`, `RM-I01`, `RM-J01`, `RM-J02`, `RM-J07` |
| `CEFTOLOZANE_INFECTION_AUTO_FULL_REVIEW.html` | 28 | 3 | `RM-A02`, `RM-A05`, `RM-A08`, `RM-A12`, `RM-A14`, `RM-B01`, `RM-B02`, `RM-B03`, `RM-D08`, `RM-D10`, `RM-E01`, `RM-E02`, `RM-F01`, `RM-F02`, `RM-F03`, `RM-F04`, `RM-F05`, `RM-G01`, `RM-G02`, `RM-G03`, `RM-H01`, `RM-H02`, `RM-H04`, `RM-H05`, `RM-I01`, `RM-J01`, `RM-J02`, `RM-J07` |
| `CEFTOLOZANE_TAZ_AUTO_FULL_REVIEW.html` | 28 | 3 | `RM-A02`, `RM-A05`, `RM-A08`, `RM-A12`, `RM-A14`, `RM-B01`, `RM-B02`, `RM-B03`, `RM-D08`, `RM-D10`, `RM-E01`, `RM-E02`, `RM-F01`, `RM-F02`, `RM-F03`, `RM-F04`, `RM-F05`, `RM-G01`, `RM-G02`, `RM-G03`, `RM-H01`, `RM-H02`, `RM-H04`, `RM-H05`, `RM-I01`, `RM-J01`, `RM-J02`, `RM-J07` |
| `DERISOMALTOSE_IRON_DEFICIENCY_AUTO_FULL_REVIEW.html` | 28 | 4 | `RM-A02`, `RM-A05`, `RM-A07`, `RM-A08`, `RM-A14`, `RM-B01`, `RM-B02`, `RM-B03`, `RM-D02`, `RM-D08`, `RM-D10`, `RM-E01`, `RM-E02`, `RM-F01`, `RM-F02`, `RM-F03`, `RM-F04`, `RM-F05`, `RM-G01`, `RM-G03`, `RM-H01`, `RM-H02`, `RM-H04`, `RM-H05`, `RM-I01`, `RM-J01`, `RM-J02`, `RM-J07` |
| `DONANEMAB_AD_AUTO_FULL_REVIEW.html` | 28 | 4 | `RM-A02`, `RM-A05`, `RM-A07`, `RM-A08`, `RM-A12`, `RM-A14`, `RM-B01`, `RM-B02`, `RM-B03`, `RM-D08`, `RM-D10`, `RM-E01`, `RM-E02`, `RM-F01`, `RM-F02`, `RM-F03`, `RM-F04`, `RM-F05`, `RM-G01`, `RM-G03`, `RM-H01`, `RM-H02`, `RM-H04`, `RM-H05`, `RM-I01`, `RM-J01`, `RM-J02`, `RM-J07` |
| `EVOBRUTINIB_MS_AUTO_FULL_REVIEW.html` | 28 | 3 | `RM-A02`, `RM-A05`, `RM-A07`, `RM-A08`, `RM-A14`, `RM-B01`, `RM-B02`, `RM-B03`, `RM-D02`, `RM-D08`, `RM-D10`, `RM-E01`, `RM-E02`, `RM-F01`, `RM-F02`, `RM-F03`, `RM-F04`, `RM-F05`, `RM-G01`, `RM-G03`, `RM-H01`, `RM-H02`, `RM-H04`, `RM-H05`, `RM-I01`, `RM-J01`, `RM-J02`, `RM-J07` |
| `FARICIMAB_DME_AUTO_FULL_REVIEW.html` | 28 | 3 | `RM-A02`, `RM-A05`, `RM-A07`, `RM-A08`, `RM-A12`, `RM-A14`, `RM-B01`, `RM-B02`, `RM-B03`, `RM-D02`, `RM-D08`, `RM-D10`, `RM-E01`, `RM-E02`, `RM-F01`, `RM-F02`, `RM-F03`, `RM-F04`, `RM-F05`, `RM-G01`, `RM-H01`, `RM-H02`, `RM-H04`, `RM-H05`, `RM-I01`, `RM-J01`, `RM-J02`, `RM-J07` |

## 6. What this sweep cannot see

- **SOURCE-class detectors** (RM-A06 rate-as-proportion, RM-B04 outcome substitution, RM-B05 omitted trial, RM-B06 PICO mismatch, RM-B07 arm dropping, RM-C02 arm-as-overall, RM-C03 arm orientation, RM-D03 protocol-paper citation, RM-D04 fabricated counts, RM-H06 NI margin, RM-J03 eligibility contradiction) need a registry/PubMed lookup per trial. A zero here is **not** a clean result for those types.
- **RENDER-class detectors** (RM-B02 Defect 4, RM-F08 hidden sensitivity interval) need the app served and driven in-browser. The HFrEF badge contradiction was found by rendering, after a file-level gate had passed it.
- **Redirect stubs** are excluded from the denominator. A fix applied to one variant is not applied to the app (RECIPE-C 0.2) — variant consistency is a separate check.
- A detector that fires is a **hypothesis**, not a proven defect. The HFrEF pass withdrew three of its five findings on verification.

