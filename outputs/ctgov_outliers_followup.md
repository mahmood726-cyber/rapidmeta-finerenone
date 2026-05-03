# CT.gov outliers — remaining triage notes (2026-05-03)

Following the 8 confirmed wrong-NCT fixes (commits `7d9b61f3`, `c096b815`, `ebeaae21` swap-fixes + this commit's HARMONIE fix), 36 outliers remain in `outputs/ctgov_cross_check.csv`. Categorized for follow-up:

## Group A — Wrong NCT, source publication needed (10 entries)

These have ratios > 5× or have CT.gov titles that clearly don't match the file's trial label. Need source-paper lookup to find the correct NCT.

| File | Trial | Current NCT | CT.gov title | Action |
|---|---|---|---|---|
| TYVAC_TYPHOID | TyVAC Nepal | NCT03158961 | "TOETVA thyroidectomy" | Trial likely ISRCTN-only; remove NCT or find ISRCTN ID |
| TYVAC_TYPHOID | TyVAC Bangladesh | NCT03527355 | "Safety/reactogenicity" generic | Same — likely ISRCTN |
| ANTIVEGF_NAMD_NMA | IVAN | NCT00784290 | "TSU-68 cancer" | IVAN was UK ISRCTN; remove NCT |
| HIFPH_CKD_ANEMIA | INNO2VATE | NCT02865850 | vadadustat (right drug, wrong N) | Find INNO2VATE-DD (dialysis-dependent) NCT |
| FRAGILITY_FRACTURE_NMA | VERT | NCT00077428 | bortezomib | VERT 1996 pre-CT.gov; mark legacy/no-NCT |
| ALDO_SYNTHASE_NMA | Target-HTN | NCT05186870 | "Reliability functional outcomes NF1" | Find correct Target-HTN NCT (likely NCT05137002 BrigHTN) |
| ANTIPSYCHOTICS_SCHIZO_NMA | Olanzapine-Pivotal | NCT01414205 | obinutuzumab oncology | Olanzapine pivotals are 1990s pre-CT.gov; remove or mark legacy |
| ANTIPSYCHOTICS_SCHIZO_NMA | Aripiprazole-Pivotal | NCT01414725 | (similar mismatch) | Same |
| CFTR_CF | VX17-445-103 | NCT03525548 | (need check) | Verify |
| SEVERE_ASTHMA_NMA | SIROCCO | NCT02075255 | (n=220 wrong) | Real SIROCCO is NCT01928771 (n=2681); needs source review for n=805 mITT |

## Group B — Multi-arm subset, by design (~12 entries)

File row uses 2 arms of a 3-4 arm trial; CT.gov enrollment is the full trial. Ratios 0.20–0.30 are legitimate and not bugs. Examples:
- BIOLOGIC_ASTHMA CALIMA: row 487 / ctg 2508 (CT.gov includes long-term-extension cohort)
- RISANKIZUMAB_CD FORTIFY: row 305 (responders re-randomised) / ctg 1336 (full pre-randomised cohort)
- JAK_UC SELECTION: row 343 (induction A subset) / ctg 1351 (full induction + maintenance)
- CD_BIOLOGICS CLASSIC-1: row 148 / ctg 854 (different analysis populations)

These are documented per-protocol or subset-by-design choices and don't represent extraction errors.

## Group C — Antiamyloid AD (4 swap-candidate entries)

`ANTIAMYLOID_AD_NMA` shows GRADUATE I/II at ratio ~2× (file claim 1961 / 1958 vs CT.gov 975 / 1053). This is NOT a swap (different drugs from EMERGE/ENGAGE — gantenerumab vs aducanumab). The 2× pattern suggests the file double-counts patients (perhaps summing both GRADUATE I + II totals into each row's denominator). Needs source review of Bateman 2023 NEJM gantenerumab data.

## Group D — Resolved this commit

- **NIRSEVIMAB_INFANT_RSV HARMONIE**: NCT05110261 → **NCT05437510** (CT.gov acronym 'HARMONIE' confirmed; n=8057 matches file claim 8058 — fix applied)

## Recommended next-pass agent

A separate agent task with:
- The `outputs/ctgov_cross_check.csv` outlier list as input
- Access to PubMed and CT.gov MCP for each trial's source publication
- Authority to apply 3-way replace_all NCT swaps after verification
- Output: PR per file with correction + verification log

The remaining 36 outliers split roughly 10 wrong-NCT (need source-paper triage) + 12 multi-arm-by-design (no fix needed) + remaining mixed cases.
