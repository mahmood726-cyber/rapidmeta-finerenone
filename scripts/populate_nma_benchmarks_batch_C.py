#!/usr/bin/env python3
# sentinel:skip-file - developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Populate benchmarks for Batch C (4 neuro/psych/renal NMAs)."""
import argparse, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

BATCH = {
    "ANTIPSYCHOTICS_SCHIZO_NMA_REVIEW.html": {
        "outcome": "PANSS_SMD",
        "benchmarks": [
            {
                "label": "Huhn 32-antipsychotic NMA (clozapine exemplar)",
                "citation": "Huhn 2019",
                "year": 2019,
                "measure": "SMD",
                "estimate": -0.89, "lci": -1.08, "uci": -0.71,
                "k": 402, "n": 53463,
                "scope": "Clozapine vs placebo; overall symptoms SMD on standardized rating scales (PANSS/BPRS). Top-ranked in landmark Lancet 2019;394:939-951 NMA of 32 oral antipsychotics, 40815 pts in efficacy analysis.",
            },
        ],
    },
    "ANTIAMYLOID_AD_NMA_REVIEW.html": {
        "outcome": "CDR-SB",
        "benchmarks": [
            {
                "label": "Avgerinos pooled anti-amyloid MA (lecanemab + donanemab)",
                "citation": "Avgerinos 2023",
                "year": 2023,
                "measure": "MD",
                "estimate": -0.49, "lci": -0.67, "uci": -0.30,
                "k": 2, "n": 3531,
                "scope": "Lecanemab (CLARITY-AD) + donanemab (TRAILBLAZER-ALZ2) pooled vs placebo; CDR-SB change at 18 mo. Phase III RCTs through Nov 2023.",
            },
        ],
    },
    "CGRP_MIGRAINE_NMA_REVIEW.html": {
        "outcome": "MMD",
        "benchmarks": [
            {
                "label": "Anti-CGRP mAb migraine NMA (galcanezumab exemplar)",
                "citation": "Haghdoost 2023",
                "year": 2023,
                "measure": "MD",
                "estimate": -2.10, "lci": -2.76, "uci": -1.45,
                "k": 16, "n": 9123,
                "scope": "Galcanezumab 240 mg vs placebo; monthly migraine days reduction. Phase 3 RCT NMA of CGRP mAbs + gepants for migraine prevention. Cephalalgia 2023.",
            },
        ],
    },
    "CARDIORENAL_DKD_NMA_REVIEW.html": {
        "outcome": "RENAL_COMP",
        "benchmarks": [
            {
                "label": "FIDELITY finerenone pooled (kidney composite)",
                "citation": "Agarwal 2022",
                "year": 2022,
                "measure": "HR",
                "estimate": 0.77, "lci": 0.67, "uci": 0.88,
                "k": 2, "n": 13026,
                "scope": "Finerenone vs placebo; kidney composite (sustained eGFR decline >=57%, kidney failure, or renal death) in FIDELIO-DKD + FIGARO-DKD pool. Eur Heart J 2022.",
            },
            {
                "label": "SGLT2i DKD composite (Nuffield Dept Collaborative)",
                "citation": "Nuffield 2022",
                "year": 2022,
                "measure": "HR",
                "estimate": 0.62, "lci": 0.56, "uci": 0.70,
                "k": 13, "n": 90409,
                "scope": "SGLT2i class vs placebo; renal composite in CKD + CV + DM trials. Lancet Diabetes Endocrinol 2022 SMART-C meta-analysis.",
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
    print(f"\nBatch C: {ok} OK / {fail} fail / {'dry-run' if args.dry_run else 'apply'}")
    if fail: sys.exit(1)


if __name__ == "__main__":
    main()
