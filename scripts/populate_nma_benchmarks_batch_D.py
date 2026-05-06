#!/usr/bin/env python3
# sentinel:skip-file - developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Populate benchmarks for Batch D (4 onco NMAs)."""
import argparse, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

BATCH = {
    "BTKI_CLL_NMA_REVIEW.html": {
        "outcome": "PFS",
        "benchmarks": [
            {
                "label": "Zanubrutinib vs ibrutinib R/R CLL NMA",
                "citation": "Molica 2023",
                "year": 2023,
                "measure": "HR",
                "estimate": 0.67, "lci": 0.52, "uci": 0.87,
                "k": 5, "n": 2400,
                "scope": "Zanubrutinib vs ibrutinib head-to-head within BTKi NMA; PFS in relapsed/refractory CLL. Blood Adv 2025 multilevel network meta-regression.",
            },
            {
                "label": "RESONATE ibrutinib vs ofatumumab",
                "citation": "Byrd 2014",
                "year": 2014,
                "measure": "HR",
                "estimate": 0.22, "lci": 0.15, "uci": 0.32,
                "k": 1, "n": 391,
                "scope": "Ibrutinib vs ofatumumab; PFS in R/R CLL. Landmark pivotal trial, NEJM 2014;371:213-223. Single-trial anchor.",
            },
        ],
    },
    "ADC_HER2_NMA_REVIEW.html": {
        "outcome": "PFS",
        "benchmarks": [
            {
                "label": "DESTINY-Breast03 T-DXd vs T-DM1",
                "citation": "Hurvitz 2022",
                "year": 2022,
                "measure": "HR",
                "estimate": 0.28, "lci": 0.22, "uci": 0.37,
                "k": 1, "n": 524,
                "scope": "Trastuzumab deruxtecan vs trastuzumab emtansine; PFS in HER2+ metastatic BC (2L). Landmark ADC head-to-head, Lancet 2023;401:105-117.",
            },
            {
                "label": "EMILIA T-DM1 vs capecitabine+lapatinib",
                "citation": "Verma 2012",
                "year": 2012,
                "measure": "HR",
                "estimate": 0.65, "lci": 0.55, "uci": 0.77,
                "k": 1, "n": 991,
                "scope": "T-DM1 vs capecitabine+lapatinib; PFS in HER2+ metastatic BC. Pivotal first-in-class ADC trial, NEJM 2012;367:1783-1791.",
            },
        ],
    },
    "ADC_HER2_ADJUVANT_NMA_REVIEW.html": {
        "outcome": "iDFS",
        "benchmarks": [
            {
                "label": "KATHERINE T-DM1 vs trastuzumab (adjuvant residual disease)",
                "citation": "von Minckwitz 2019",
                "year": 2019,
                "measure": "HR",
                "estimate": 0.50, "lci": 0.39, "uci": 0.64,
                "k": 1, "n": 1486,
                "scope": "T-DM1 vs trastuzumab in HER2+ early BC with residual invasive disease after neoadjuvant therapy; 3-yr iDFS. NEJM 2019;380:617-628.",
            },
        ],
    },
    "ADC_HER2_LOW_NMA_REVIEW.html": {
        "outcome": "PFS",
        "benchmarks": [
            {
                "label": "DESTINY-Breast04 T-DXd vs TPC (HER2-low)",
                "citation": "Modi 2022",
                "year": 2022,
                "measure": "HR",
                "estimate": 0.51, "lci": 0.40, "uci": 0.64,
                "k": 1, "n": 557,
                "scope": "Trastuzumab deruxtecan vs physician's choice chemotherapy; PFS in HER2-low metastatic BC. First-in-class ADC in HER2-low, NEJM 2022;387:9-20.",
            },
            {
                "label": "DESTINY-Breast06 T-DXd vs TPC (HER2-low/ultralow, HR+)",
                "citation": "Curigliano 2024",
                "year": 2024,
                "measure": "HR",
                "estimate": 0.62, "lci": 0.51, "uci": 0.74,
                "k": 1, "n": 866,
                "scope": "T-DXd vs TPC in HR+ HER2-low/ultralow metastatic BC after endocrine therapy; PFS. NEJM 2024.",
            },
        ],
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


def render_benchmark_block(outcome, benchmarks):
    lines = ["{"]
    lines.append(f"            '{outcome}': [")
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
    lines.append("            ]")
    lines.append("        }")
    return "\n".join(lines)


def render_outcome_map(outcome):
    legacy = ["default", "MACE", "ACH", "ACM", "Renal40", "Hyperkalemia",
              "HF_CV_First", "KidneyComp", "Renal57"]
    lines = ["{"]
    for k in legacy:
        lines.append(f"            {k}: '{outcome}',")
    lines.append(f"            '{outcome}': '{outcome}'")
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


def apply_to_file(path, outcome, benchmarks, dry_run):
    text = path.read_text(encoding="utf-8", newline="")
    crlf = "\r\n" in text
    work = text.replace("\r\n", "\n") if crlf else text
    work, c1 = replace_const_decl(work, "PUBLISHED_META_BENCHMARKS",
                                   render_benchmark_block(outcome, benchmarks))
    work, c2 = replace_const_decl(work, "BENCHMARK_OUTCOME_MAP",
                                   render_outcome_map(outcome))
    if not (c1 and c2): return f"FAIL {path.name}: bench={c1} map={c2}"
    if not dry_run:
        out = work.replace("\n", "\r\n") if crlf else work
        path.write_text(out, encoding="utf-8", newline="")
    return f"OK   {path.name}: bench+{len(benchmarks)} map=fixed"


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
        r = apply_to_file(p, spec["outcome"], spec["benchmarks"], args.dry_run)
        print(r)
        if r.startswith("OK"): ok += 1
        else: fail += 1
    print(f"\nBatch D: {ok} OK / {fail} fail / {'dry-run' if args.dry_run else 'apply'}")
    if fail: sys.exit(1)


if __name__ == "__main__":
    main()
