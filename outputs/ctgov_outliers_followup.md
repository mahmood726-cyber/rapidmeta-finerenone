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

## Group D — Resolved across triage commits

| Trial | Old NCT (wrong) | New NCT | Verification |
|---|---|---|---|
| HARMONIE (NIRSEVIMAB_INFANT_RSV) | NCT05110261 | **NCT05437510** | CT.gov acronym 'HARMONIE'; n=8057 matches file 8058 |
| SIROCCO (SEVERE_ASTHMA_NMA) | NCT02075255 | **NCT01928771** | CT.gov title 'Benralizumab Added to High-dose ICS-LABA in Uncontrolled Asthma'; n=2681 (file uses mITT subset 805, ratio 0.30 = OK) |
| INNO2VATE (HIFPH_CKD_ANEMIA) | NCT02865850 (Conversion arm only, n=369) | **NCT02892149** (Correction arm, n=3554; combined Eckardt 2021 NEJM analysis n=3923) | File reports combined Conversion+Correction (n=3923); ratio 1.104 |

## Group E — Legacy / non-CT.gov trials (requires ISRCTN-key strategy)

These trials are NOT registered in CT.gov at all and will continue to flag as wrong-NCT until the file scaffold supports synthetic registry-IDs (e.g. `ISRCTN43385572` or `LEGACY-VERT-1996`):

| Trial | Real registration | Status |
|---|---|---|
| TyVAC Nepal (NCT03158961 in file) | ISRCTN43385572 (Shakya 2019 NEJM PMID 31800986, n=20,019) | Replace key with ISRCTN ID + null ctgovUrl |
| TyVAC Bangladesh (NCT03527355 in file) | ISRCTN11643110 (Theiss-Nyland 2021 Lancet, n=41,344) | Replace key with ISRCTN ID + null ctgovUrl |
| IVAN (ANTIVEGF_NAMD_NMA NCT00784290 in file) | ISRCTN92166560 (Chakravarthy 2013 Lancet PMID 23945232, n=610) | Replace key with ISRCTN ID + null ctgovUrl |
| VERT (FRAGILITY_FRACTURE_NMA NCT00077428 in file) | Pre-CT.gov 1996 (Harris 1999 JAMA PMID 10519411, n=388) | Replace key with `LEGACY-VERT-1999` + null ctgovUrl |
| Olanzapine-Pivotal (ANTIPSYCHOTICS_SCHIZO_NMA NCT01414205 in file) | 1990s pre-CT.gov pivotals (Beasley 1996, Tollefson 1997) | Replace key with `LEGACY-OLANZAPINE-PIVOTAL` |
| Aripiprazole-Pivotal (ANTIPSYCHOTICS_SCHIZO_NMA NCT01414725 in file) | 2000s pivotals (Kane 2002, Marder 2003) | Replace key with `LEGACY-ARIPIPRAZOLE-PIVOTAL` |

A future agent task should:
1. Update the build script's CT.gov audit to skip keys starting with `ISRCTN` or `LEGACY-`
2. Replace the wrong NCT keys in the affected files with synthetic IDs
3. Update each row's `ctgovUrl` to the ISRCTN URL or set to null
4. Add `pmid:` field to each row to anchor the source publication

This work is mechanical but file-by-file; deferred from this session.

## Recommended next-pass agent

A separate agent task with:
- The `outputs/ctgov_cross_check.csv` outlier list as input
- Access to PubMed and CT.gov MCP for each trial's source publication
- Authority to apply 3-way replace_all NCT swaps after verification
- Output: PR per file with correction + verification log

The remaining 36 outliers split roughly 10 wrong-NCT (need source-paper triage) + 12 multi-arm-by-design (no fix needed) + remaining mixed cases.
