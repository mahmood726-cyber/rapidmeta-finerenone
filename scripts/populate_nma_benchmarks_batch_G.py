#!/usr/bin/env python3
# sentinel:skip-file - developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Populate benchmarks for Batch G (12 cardio #2 + onco #1 apps)."""
import argparse, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

BATCH = {
    "SOTAGLIFLOZIN_HF_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "SOLOIST-WHF sotagliflozin vs placebo", "citation": "Bhatt 2021", "year": 2021,
             "measure": "HR", "estimate": 0.67, "lci": 0.52, "uci": 0.85, "k": 1, "n": 1222,
             "scope": "Sotagliflozin vs placebo in T2D recently hospitalized for worsening HF; CV death, HHF, or urgent HF visit. NEJM 2021;384:117-128."},
        ]}
    },
    "TAVR_LOWRISK_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "PARTNER 3 TAVR vs SAVR (low-risk)", "citation": "Mack 2019", "year": 2019,
             "measure": "HR", "estimate": 0.54, "lci": 0.37, "uci": 0.79, "k": 1, "n": 1000,
             "scope": "Balloon-expandable TAVR (SAPIEN 3) vs SAVR in low surgical-risk severe AS; death, stroke, or rehospitalization at 1 yr. NEJM 2019;380:1695-1705."},
            {"label": "Evolut Low Risk TAVR vs SAVR", "citation": "Popma 2019", "year": 2019,
             "measure": "HR", "estimate": 0.74, "lci": 0.56, "uci": 0.98, "k": 1, "n": 1468,
             "scope": "Self-expanding TAVR (Evolut) vs SAVR in low-risk severe AS; death or disabling stroke at 24 mo. NEJM 2019;380:1706-1715."},
        ]}
    },
    "TIRZEPATIDE_OBESITY_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "SURMOUNT-1 tirzepatide vs placebo (weight)", "citation": "Jastreboff 2022", "year": 2022,
             "measure": "MD", "estimate": -17.80, "lci": -19.30, "uci": -16.30, "k": 1, "n": 2539,
             "scope": "Tirzepatide 15 mg weekly vs placebo in overweight/obesity without diabetes; body-weight percent change at 72 wk. NEJM 2022;387:205-216."},
        ]}
    },
    "TIRZEPATIDE_T2D_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "SURPASS-2 tirzepatide vs semaglutide (HbA1c)", "citation": "Frias 2021", "year": 2021,
             "measure": "MD", "estimate": -0.45, "lci": -0.57, "uci": -0.32, "k": 1, "n": 1879,
             "scope": "Tirzepatide 15 mg vs semaglutide 1 mg weekly in T2D on metformin; HbA1c change at 40 wk. NEJM 2021;385:503-515."},
        ]}
    },
    "TNK_VS_TPA_STROKE_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "AcT tenecteplase vs alteplase (stroke)", "citation": "Menon 2022", "year": 2022,
             "measure": "RR", "estimate": 1.06, "lci": 0.94, "uci": 1.19, "k": 1, "n": 1577,
             "scope": "Tenecteplase 0.25 mg/kg vs alteplase 0.9 mg/kg in acute ischemic stroke <4.5 h; mRS 0-1 at 90 d (non-inferior). Lancet 2022;400:161-169."},
        ]}
    },
    "DOAC_CANCER_VTE_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "Caravaggio apixaban vs dalteparin (cancer VTE)", "citation": "Agnelli 2020", "year": 2020,
             "measure": "HR", "estimate": 0.63, "lci": 0.37, "uci": 1.07, "k": 1, "n": 1155,
             "scope": "Apixaban vs dalteparin in cancer-associated VTE; recurrent VTE at 6 mo. NEJM 2020;382:1599-1607."},
            {"label": "Hokusai-VTE Cancer edoxaban vs dalteparin", "citation": "Raskob 2018", "year": 2018,
             "measure": "HR", "estimate": 0.71, "lci": 0.48, "uci": 1.06, "k": 1, "n": 1046,
             "scope": "Edoxaban vs dalteparin in cancer-associated VTE; recurrent VTE or major bleeding at 12 mo. NEJM 2018;378:615-624."},
        ]}
    },
    "AFLIBERCEPT_HD_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "PULSAR aflibercept 8 mg vs 2 mg (nAMD BCVA)", "citation": "Lanzetta 2024", "year": 2024,
             "measure": "MD", "estimate": -0.3, "lci": -1.7, "uci": 1.1, "k": 1, "n": 1009,
             "scope": "Aflibercept 8 mg Q12W/Q16W vs 2 mg Q8W in nAMD; BCVA change at 48 wk (non-inferior). Lancet 2024 / Eye 2024."},
        ]}
    },
    "PBC_PPAR_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "ELATIVE elafibranor vs placebo (PBC composite)", "citation": "Kowdley 2024", "year": 2024,
             "measure": "RR", "estimate": 5.40, "lci": 2.60, "uci": 11.30, "k": 1, "n": 161,
             "scope": "Elafibranor vs placebo in PBC with inadequate UDCA response; biochemical response at 52 wk (ALP <1.67x ULN + ALP reduction >=15% + normal bilirubin). NEJM 2024;390:795-805."},
            {"label": "RESPONSE seladelpar vs placebo (PBC composite)", "citation": "Hirschfield 2024", "year": 2024,
             "measure": "RR", "estimate": 4.20, "lci": 2.50, "uci": 7.10, "k": 1, "n": 193,
             "scope": "Seladelpar vs placebo in PBC; composite biochemical response at 12 mo. NEJM 2024."},
        ]}
    },
    "RENAL_DENERV_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "SPYRAL HTN-ON MED renal denervation vs sham", "citation": "Kandzari 2023", "year": 2023,
             "measure": "MD", "estimate": -4.0, "lci": -6.9, "uci": -1.1, "k": 1, "n": 337,
             "scope": "Renal denervation vs sham procedure in uncontrolled HTN on meds; 24-h ambulatory SBP change at 6 mo (mm Hg). Lancet 2022;400:1405-1416."},
        ]}
    },
    "COPD_TRIPLE_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "IMPACT triple vs dual ICS/LABA (COPD exac)", "citation": "Lipson 2018", "year": 2018,
             "measure": "RR", "estimate": 0.85, "lci": 0.80, "uci": 0.90, "k": 1, "n": 10355,
             "scope": "FF/UMEC/VI triple therapy vs FF/VI in COPD; annual rate of moderate/severe exacerbations. NEJM 2018;378:1671-1680."},
        ]}
    },
    "ACALABRUTINIB_CLL_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "ELEVATE-TN acalabrutinib+obinutuzumab vs chlor+obin", "citation": "Sharman 2020", "year": 2020,
             "measure": "HR", "estimate": 0.10, "lci": 0.07, "uci": 0.17, "k": 1, "n": 535,
             "scope": "Acalabrutinib +/- obinutuzumab vs chlorambucil + obinutuzumab in treatment-naive CLL; PFS. Lancet 2020;395:1278-1291."},
        ]}
    },
    "ARPI_mHSPC_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "ARPI + ADT vs ADT in mHSPC meta-analysis", "citation": "Riaz 2023", "year": 2023,
             "measure": "HR", "estimate": 0.67, "lci": 0.61, "uci": 0.74, "k": 6, "n": 7785,
             "scope": "Androgen receptor pathway inhibitors (abiraterone, enzalutamide, apalutamide, darolutamide) + ADT vs ADT in metastatic hormone-sensitive prostate cancer; overall survival. JAMA Oncol 2023 MA."},
        ]}
    },
}


def find_balanced_close(text, open_pos):
    depth = 0
    i = open_pos
    while i < len(text):
        if text[i] == '{': depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0: return i
        i += 1
    return -1


def render_benchmark_block(benchmarks_by_key):
    lines = ["{"]
    for key, benchmarks in benchmarks_by_key.items():
        lines.append(f"            '{key}': [")
        for b in benchmarks:
            lines.append(
                "                { "
                f"label: '{b['label'].replace(chr(39), chr(92)+chr(39))}', "
                f"citation: '{b['citation']}', "
                f"year: {b['year']}, "
                f"measure: '{b['measure']}', "
                f"estimate: {b['estimate']}, "
                f"lci: {b['lci']}, "
                f"uci: {b['uci']}, "
                f"k: {b['k']}, "
                f"n: {b['n']}, "
                f"scope: '{b['scope'].replace(chr(39), chr(92)+chr(39))}' "
                "},"
            )
        lines.append("            ],")
    lines.append("        }")
    return "\n".join(lines)


def render_outcome_map(outcomes):
    primary = outcomes[0]
    legacy = ["default", "MACE", "ACH", "ACM", "Renal40", "Hyperkalemia",
              "HF_CV_First", "KidneyComp", "Renal57"]
    lines = ["{"]
    for k in legacy:
        lines.append(f"            {k}: '{primary}',")
    seen = set(legacy)
    for o in outcomes:
        if o not in seen:
            lines.append(f"            '{o}': '{o}',")
    lines[-1] = lines[-1].rstrip(",")
    lines.append("        }")
    return "\n".join(lines)


def replace_const_decl(text, const_name, new_rhs):
    pat = re.compile(rf"const\s+{re.escape(const_name)}\s*=\s*\{{")
    m = pat.search(text)
    if not m: return text, False
    open_pos = m.end() - 1
    close_pos = find_balanced_close(text, open_pos)
    if close_pos < 0: return text, False
    after = close_pos + 1
    while after < len(text) and text[after] in " \t": after += 1
    if after < len(text) and text[after] == ';': after += 1
    return text[:m.start()] + f"const {const_name} = {new_rhs};" + text[after:], True


def apply_to_file(path, spec, dry_run):
    text = path.read_text(encoding="utf-8", newline="")
    crlf = "\r\n" in text
    work = text.replace("\r\n", "\n") if crlf else text
    work, c1 = replace_const_decl(work, "PUBLISHED_META_BENCHMARKS",
                                   render_benchmark_block(spec["benchmarks"]))
    work, c2 = replace_const_decl(work, "BENCHMARK_OUTCOME_MAP",
                                   render_outcome_map(spec["outcomes"]))
    if not (c1 and c2): return f"FAIL {path.name}: bench={c1} map={c2}"
    if not dry_run:
        out = work.replace("\n", "\r\n") if crlf else work
        path.write_text(out, encoding="utf-8", newline="")
    n_entries = sum(len(v) for v in spec["benchmarks"].values())
    return f"OK   {path.name}: bench+{n_entries} map=fixed"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run or args.apply): ap.error("pass --dry-run or --apply")
    ok = fail = 0
    for name, spec in BATCH.items():
        p = ROOT / name
        if not p.exists():
            print(f"SKIP {name}"); continue
        r = apply_to_file(p, spec, args.dry_run)
        print(r)
        if r.startswith("OK"): ok += 1
        else: fail += 1
    print(f"\nBatch G: {ok} OK / {fail} fail / {'dry-run' if args.dry_run else 'apply'}")
    if fail: sys.exit(1)


if __name__ == "__main__":
    main()
