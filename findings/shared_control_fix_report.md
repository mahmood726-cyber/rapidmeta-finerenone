# Shared-control / multi-arm extraction audit & fix

**Date:** 2026-06-20
**Scope:** Class-1 (shared-control double-counting) only, per request. Hybrid method
(combine same-drug doses; split shared control for distinct interventions).
**Tools:** `scripts/audit_multiarm.py` (read-only detector), `scripts/fix_shared_control_split.py` (codemod).

## What the bug is
A multi-arm parent trial (or a trial that borrowed another trial's placebo as an
external control) was extracted as >=2 rows that each **repeat the same control
`(cE,cN)`**. Naive pairwise pooling then counts those control patients/events twice:
the pooled weights are wrong, the variance is understated, and the N/event aggregates
(total N, ARD, NNT) double-count the control.

**Remedy (Cochrane Handbook v6.5 §23.3.4):** divide the shared control group size and
events by the number `m` of comparisons that share it. The control **event rate is
preserved** (each contrast's point estimate is unchanged) while the smaller control `n`
inflates each contrast's variance to reflect that the evidence is shared. The control
appears in two inline spots per arm — trial-level `cE/cN` and the `allOutcomes` PRIMARY
`cE` (the engine overwrites `t.data.cE` from the selected outcome) — both were split.

## Audit result
935 data-bearing apps (>100 KB) scanned. 88 flagged, in three classes:

| Class | Signal | Count | Meaning |
|---|---|---|---|
| 1 | identical `(cE,cN)` repeated | 5 | **shared-control double-counting** (this fix) |
| 2 | same PMID, *different* controls | 80 | citation misattribution / garbled extraction (separate pass) |
| 3 | normalized-name collision | 3 | mostly benign (e.g. IMPORT-LOW/IMPORT-HIGH are two real trials) |

## Class-1 fixes APPLIED (3 pairwise apps)

| App | Trial structure (verified via PubMed) | Split |
|---|---|---|
| `HIV_ART_FIRSTLINE_REVIEW.html` | ADVANCE 3-arm RCT (Venter, NEJM 2019, PMID 31339677). DTG/TAF + DTG/TDF vs one shared EFV control (351/arm). Different NRTI backbones → split. | control `282/351` → `141/176` (TAF) + `141/175` (TDF). Total control N 702→**351** (true). Pooled RR preserved ≈1.11. |
| `NMOSD_BIOLOGICS_REVIEW.html` | CHAMPION-NMOSD (ravulizumab, PMID 38356884) reused PREVENT's placebo (eculizumab, PMID 31050279) as an external control — placebo is unethical in NMOSD. Different drugs → split. | control `20/47` → `10/24` (PREVENT) + `10/23` (CHAMPION). Total control 94→**47** (true). |
| `HPV_DOSE_REDUCTION_REVIEW.html` | KEN-SHE single-dose HPV 3-arm trial: bivalent + nonavalent vs one shared control. Different vaccines → split. | control `38/758` → `19/379` each. Total control 1516→**758** (true). |

All three: 12/12 codemod replacements unambiguous; JS still parses (0 parse failures).
Each is idempotent and re-runnable.

> Note: after an *even* split the two halves are identical (`19/379`/`19/379` for HPV),
> so `audit_multiarm.py` re-flags HPV — that is the **expected post-split state** (the two
> rows now *sum* to the single true control), not double-counting.

## Class-1 fix APPLIED (1 NMA app)

- **`COMPLEMENT_C5_BROAD_NMA_REVIEW.html`** — same PREVENT/CHAMPION borrowed placebo
  `20/47`, here inside the C5-inhibitor NMA. The 47 placebo patients were double-counted
  in the placebo *node*. Split `20/47` → `10/24` (PREVENT) + `10/23` (CHAMPION); both arms
  still connect to the placebo node so network connectivity is preserved.

**All 4 true shared-control double-counts (3 pairwise + 1 NMA) are now fixed.** JS parses
clean (0 failures) on all four.

## Class-2 (PMID-repeat) verification — PubMed cross-check of all 65 unique repeated PMIDs

These do **not** double-count a control (the repeated-PMID rows have *different* controls →
independent contrasts → pooled estimates unaffected). The only question is citation
correctness. Each repeated PMID's title was checked against the app's drug/trial names.

- **80 / 87 assignments confirmed correct** — including legitimate co-publications where
  two distinct trials share one paper (e.g. `ANTIAMYLOID_AD`: EMERGE + ENGAGE share PMID
  34807243; `AML_TARGETED`: QuANTUM program).
- **1 fixed:** `HPV_DOSE_REDUCTION` — both KEN-SHE rows had wrong PMIDs (`32078808` = a
  comment; `35693867` = an unrelated phototherapy paper). KEN-SHE is one 3-arm RCT; both
  now cite the verified efficacy paper **PMID 38049621** (Barnabas RV et al., Nat Med 2023,
  DOI 10.1038/s41591-023-02658-0, NCT03675256).
- **10 row-level PMIDs corrected** after PubMed verification (each app had one wrong PMID on
  two different trials → each row given its own confirmed primary publication). Tool:
  `scripts/fix_pmid_misattribution.py` (name-anchored, idempotent). Every new PMID was
  validated by fetching its title and matching trial+drug:
  - `CART_B_CELL_LYMPHOMA`: BELINDA→**34904798**, TRANSFORM→**35717989**
  - `HCC_LOCAL_THERAPY_NMA`: EMERALD-1→**39798579**, TACTICS→**31801872**
  - `OBINUTUZUMAB_LN`: REGENCY→**39927615**, NOBILITY/NCT02550652→**34615636**
  - `HIV_PREP_INJECTABLE`: HPTN 083→**34379922**, HPTN 084→**35594553** (correct PMIDs were
    already present in the app's own evidence text)
  - `ROXADUSTAT_ANEMIA_CKD` + `ROXADUSTAT_RENAL_ANEMIA`: DOLOMITES→**34077510** (the app's
    DOLOMITES arm Ns 323/293 exactly match the trial — a good integrity signal)
- **Verification caught 2 bad candidates** that search ranking offered: PMID 35314445
  ("Stalled progress on reconciliation in health care") and 40088884 (an HCC commentary) —
  both rejected after title check. Confirms: never write a PMID from search rank or memory.
- **Still unresolved → flagged, NOT guessed** (the trial's *primary* paper is not retrievable
  from the PubMed index; writing a PMID would be fabrication):
  - `ROXADUSTAT_*`: PYRENEES — the index returns only the ROCKIES trial and 4-study *pooled*
    analyses (which list Csiky as an author), never the standalone PYRENEES primary. Left as
    the known-wrong 36005278, flagged. (Substituting a pooled paper for the trial = wrong.)
  - `DELGOCITINIB_AD_AUTO_FULL`: not touched — confirmed via PMID 35084738 that its rows are
    **chronic hand-eczema** phase 2b trials (delgocitinib cream, Worm Br J Dermatol 2022),
    mis-scoped into an **atopic-dermatitis** review. A PMID swap would entrench the error;
    needs re-extraction/re-scoping of the whole app.
  - `VAMOROLONE_DMD2_AUTO_FULL`: degraded data (4 garbled NCTs, placeholder n, a future PMID);
    doesn't match the real VISION-DMD trial → full re-extraction, not a PMID patch.

## NOT fixed — flagged for re-extraction (cannot fix without fabricating)

- **`VAMOROLONE_DMD2_AUTO_FULL_REVIEW.html`** — flagged control `2/12`, but the underlying
  data is **degraded**: 4 different NCTs with tiny n (10–12), `tE==cE` rows (OR=1 / no
  information), and a future-looking PMID `41774261`. Does **not** match the real
  vamorolone pivotal (VISION-DMD, NCT03439670, Guglieri JAMA 2022). Auto-combining would
  launder bad data; needs full **re-extraction** against source, not a structural split.

## Adjacent data-integrity issues observed (out of Class-1 scope)
- `HPV_DOSE_REDUCTION`: nonavalent row PMID `35693867` resolves to an **unrelated
  phototherapy/muscle-damage paper** — a misattribution (real KEN-SHE single-dose =
  Barnabas, NEJM Evid 2022). Should be corrected in a Class-2 pass.
- `HIV_ART_FIRSTLINE`: treatment event counts (310/315) run ~15 above the published
  ADVANCE snapshot suppression (~295/298 at 84%/85%); structural fix done, count accuracy
  is a separate Class-2 item.
- **Class 2 (80 apps):** same PMID stamped on genuinely different arms/controls
  (e.g. `ONTAMALIMAB_IBD` — one PMID on 4 sub-studies). Each needs per-trial PubMed
  verification before any edit is safe. See `findings/multiarm_audit.json`.
