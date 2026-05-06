#!/usr/bin/env python3
# sentinel:skip-file - developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Rename the benchmark outcome key from 'MACE' (clone-template artifact)
to the drug-appropriate primary endpoint key in pairwise apps where the
drug's clinical primary is NOT a CV composite.

Changes per file:
  1. PUBLISHED_META_BENCHMARKS = { MACE: [...] }  ->  { '<NEW>': [...] }
  2. BENCHMARK_OUTCOME_MAP target 'MACE' -> '<NEW>' (legacy MACE/ACH/ACM/etc.
     still present as aliases that now route to the new semantic key)

Apps where MACE IS the correct primary (CV composite) are omitted. Apps
already using drug-appropriate keys (NMAs, FINERENONE, etc.) are omitted.

Does NOT modify trial-level data.allOutcomes shortLabels - that would
require per-trial outcome curation and risks breaking downstream filters.
"""
import argparse, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

RENAMES = {
    'ACALABRUTINIB_CLL_REVIEW.html':       'PFS',
    'ANIFROLUMAB_SLE_REVIEW.html':         'BICLA',
    'ANTIAMYLOID_AD_REVIEW.html':          'CDR_SB',
    'BELIMUMAB_SLE_REVIEW.html':           'SRI4',
    'BIOLOGIC_ASTHMA_REVIEW.html':         'EXAC_RR',
    'CART_DLBCL_REVIEW.html':              'EFS',
    'CART_MM_REVIEW.html':                 'PFS',
    'CBD_SEIZURE_REVIEW.html':             'SeizureFreq',
    'CDK46_MBC_REVIEW.html':               'PFS',
    'CFTR_CF_REVIEW.html':                 'ppFEV1',
    'CGRP_MIGRAINE_REVIEW.html':           'MMD',
    'COPD_TRIPLE_REVIEW.html':             'EXAC_RR',
    'COVID_ORAL_ANTIVIRALS_REVIEW.html':   'HospDeath',
    'DOAC_CANCER_VTE_REVIEW.html':         'VTE',
    'DUPILUMAB_AD_REVIEW.html':            'EASI75',
    'DUPILUMAB_COPD_REVIEW.html':          'EXAC_RR',
    'ESKETAMINE_TRD_REVIEW.html':          'MADRS',
    'EVT_BASILAR_REVIEW.html':             'mRS_0_3',
    'EVT_EXTENDED_WINDOW_REVIEW.html':     'mRS_0_2',
    'EVT_LARGECORE_REVIEW.html':           'mRS_0_3',
    'FARICIMAB_NAMD_REVIEW.html':          'BCVA',
    'FENFLURAMINE_SEIZURE_REVIEW.html':    'SeizureFreq',
    'FEZOLINETANT_VMS_REVIEW.html':        'VMSfreq',
    'HIGH_EFFICACY_MS_REVIEW.html':        'ARR',
    'IL23_PSORIASIS_REVIEW.html':          'PASI90',
    'INSULIN_ICODEC_REVIEW.html':          'HbA1c',
    'IO_CHEMO_NSCLC_1L_REVIEW.html':       'OS',
    'JAK_RA_REVIEW.html':                  'ACR20',
    'JAK_UC_REVIEW.html':                  'Remission',
    'JAKI_AD_REVIEW.html':                 'EASI75',
    'KARXT_SCZ_REVIEW.html':               'PANSS',
    'LENACAPAVIR_PREP_REVIEW.html':        'HIV_incidence',
    'LU_PSMA_MCRPC_REVIEW.html':           'OS',
    'MAVACAMTEN_HCM_REVIEW.html':          'CompResp',
    'MIRIKIZUMAB_UC_REVIEW.html':          'Remission',
    'NIRSEVIMAB_INFANT_RSV_REVIEW.html':   'RSV_LRTI',
    'PARP_ARPI_MCRPC_REVIEW.html':         'rPFS',
    'PARP_OVARIAN_REVIEW.html':            'PFS',
    'PATISIRAN_POLYNEUROPATHY_REVIEW.html':'mNIS',
    'PBC_PPAR_REVIEW.html':                'BiochResp',
    'PEGCETACOPLAN_GA_REVIEW.html':        'GA_Growth',
    'RENAL_DENERV_REVIEW.html':            'SBP24h',
    'RISANKIZUMAB_CD_REVIEW.html':         'Remission',
    'ROMOSOZUMAB_OP_REVIEW.html':          'VertFracture',
    'RSV_VACCINE_OLDER_REVIEW.html':       'RSV_LRTD',
    'TDXD_HER2LOW_BC_REVIEW.html':         'PFS',
    'TIRZEPATIDE_OBESITY_REVIEW.html':     'BW',
    'TIRZEPATIDE_T2D_REVIEW.html':         'HbA1c',
    'TNK_VS_TPA_STROKE_REVIEW.html':       'mRS_0_1',
    'UPADACITINIB_CD_REVIEW.html':         'Remission',
    'VENETOCLAX_AML_REVIEW.html':          'OS',
}


def _find_balanced_close(text: str, open_pos: int) -> int:
    depth = 0
    i = open_pos
    while i < len(text):
        c = text[i]
        if c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0: return i
        i += 1
    return -1


def apply_to_file(path: pathlib.Path, new_key: str, dry_run: bool) -> str:
    raw = path.read_bytes()
    crlf = b"\r\n" in raw
    text = raw.decode("utf-8").replace("\r\n", "\n")

    # Sentinel: if benchmark block already has the new key, skip.
    if re.search(rf"const PUBLISHED_META_BENCHMARKS\s*=\s*\{{\s*'?{re.escape(new_key)}'?:", text):
        return f"SKIP {path.name}: already '{new_key}'"

    # --- Rename benchmark block's first key: 'MACE': [...] -> '<NEW>': [...]
    pat_bench = re.compile(r"(const PUBLISHED_META_BENCHMARKS\s*=\s*\{\s*)'?MACE'?:")
    new_text, bench_n = pat_bench.subn(rf"\g<1>'{new_key}':", text, count=1)
    if bench_n == 0:
        return f"FAIL {path.name}: PUBLISHED_META_BENCHMARKS 'MACE' key not found"

    # --- Rename BENCHMARK_OUTCOME_MAP values from 'MACE' to '<NEW>' ONLY
    # within the balanced-brace scope of that single const declaration.
    # This avoids corrupting unrelated MACE references (trial shortLabels,
    # realData outcome names, etc.) elsewhere in the file.
    map_decl = re.search(r"const BENCHMARK_OUTCOME_MAP\s*=\s*\{", new_text)
    if not map_decl:
        return f"FAIL {path.name}: BENCHMARK_OUTCOME_MAP not found"
    open_pos = map_decl.end() - 1
    close_pos = _find_balanced_close(new_text, open_pos)
    if close_pos < 0:
        return f"FAIL {path.name}: BENCHMARK_OUTCOME_MAP unbalanced braces"

    block = new_text[open_pos : close_pos + 1]
    block_new, map_n = re.subn(
        r"(:\s*)'MACE'(\s*[,\n}])",
        rf"\1'{new_key}'\2",
        block,
    )

    # Ensure a self-map entry exists so lookups of the new key succeed.
    if f"'{new_key}': '{new_key}'" not in block_new and f"{new_key}: '{new_key}'" not in block_new:
        # Insert before the closing brace of the block (block_new ends with '}').
        body = block_new.rstrip()
        if body.endswith("}"):
            body_inside = body[:-1].rstrip()
            # Ensure trailing comma on previous entry.
            if not body_inside.endswith(","):
                body_inside += ","
            block_new = body_inside + f"\n            '{new_key}': '{new_key}'\n        }}"

    new_text = new_text[:open_pos] + block_new + new_text[close_pos + 1:]

    out = new_text.replace("\n", "\r\n") if crlf else new_text
    if not dry_run:
        path.write_bytes(out.encode("utf-8"))
    return f"OK   {path.name}: MACE -> {new_key} (bench={bench_n}, map={map_n})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run or args.apply):
        ap.error("pass --dry-run or --apply")

    ok = skip = fail = 0
    for name, new_key in RENAMES.items():
        p = ROOT / name
        if not p.exists():
            print(f"MISS {name}: not found"); fail += 1; continue
        r = apply_to_file(p, new_key, args.dry_run)
        if r.startswith("OK"):
            ok += 1
        elif r.startswith("SKIP"):
            skip += 1
        else:
            fail += 1
        print(r)
    print(f"\n{'dry-run' if args.dry_run else 'apply'}: {ok} ok / {skip} skip / {fail} fail")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
