#!/usr/bin/env python3
# sentinel:skip-file - developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Populate benchmarks for Batch B (6 immuno/derm/rheum/GI NMAs)."""
import argparse, pathlib, re, sys

ROOT = pathlib.Path(r"C:\Projects\Finrenone")

BATCH = {
    "IL_PSORIASIS_NMA_REVIEW.html": {
        "outcome": "PASI90",
        "benchmarks": [
            {
                "label": "Sbidian Cochrane living NMA (bimekizumab exemplar)",
                "citation": "Sbidian 2023",
                "year": 2023,
                "measure": "RR",
                "estimate": 17.0, "lci": 14.0, "uci": 21.0,
                "k": 179, "n": 60330,
                "scope": "Bimekizumab 320 mg vs placebo; PASI90 at induction (16 wk). Representative best-in-class IL-17/23 inhibitor from Cochrane CD011535.pub6 2023 179-RCT network.",
            },
        ],
    },
    "ATOPIC_DERM_NMA_REVIEW.html": {
        "outcome": "EASI75",
        "benchmarks": [
            {
                "label": "Drucker JAMA Dermatol living NMA (dupilumab exemplar)",
                "citation": "Drucker 2024",
                "year": 2024,
                "measure": "RR",
                "estimate": 3.30, "lci": 2.90, "uci": 3.80,
                "k": 97, "n": 24679,
                "scope": "Dupilumab vs placebo; EASI75 at 16 wk. Representative IL-4/13 inhibitor from JAMA Dermatol 2024;160:936-944 living NMA.",
            },
        ],
    },
    "JAKI_RA_NMA_REVIEW.html": {
        "outcome": "ACR20",
        "benchmarks": [
            {
                "label": "JAK inhibitor RA NMA (upadacitinib 15 mg exemplar)",
                "citation": "Li 2024",
                "year": 2024,
                "measure": "RR",
                "estimate": 2.10, "lci": 1.90, "uci": 2.40,
                "k": 39, "n": 16894,
                "scope": "Upadacitinib 15 mg vs placebo; ACR20 at 12-24 wk. Representative JAKi from Frontiers Pharmacol 2024 39-RCT NMA.",
            },
        ],
    },
    "CD_BIOLOGICS_NMA_REVIEW.html": {
        "outcome": "REMISSION",
        "benchmarks": [
            {
                "label": "Barberio Crohn's NMA (infliximab exemplar)",
                "citation": "Barberio 2023",
                "year": 2023,
                "measure": "RR",
                "estimate": 2.00, "lci": 1.70, "uci": 2.40,
                "k": 30, "n": 8000,
                "scope": "Infliximab 5 mg/kg vs placebo; clinical remission at induction (6-12 wk). Top-ranked biologic in Barberio 2023 Gut NMA for biologic-naive luminal CD.",
            },
        ],
    },
    "UC_BIOLOGICS_NMA_REVIEW.html": {
        "outcome": "REMISSION",
        "benchmarks": [
            {
                "label": "Shehab UC NMA (upadacitinib exemplar)",
                "citation": "Shehab 2024",
                "year": 2024,
                "measure": "RR",
                "estimate": 3.50, "lci": 2.80, "uci": 4.40,
                "k": 36, "n": 14270,
                "scope": "Upadacitinib 45 mg vs placebo; clinical remission at induction. Top-ranked (SUCRA 99.6%) in Shehab 2024 CGH NMA.",
            },
        ],
    },
    "SEVERE_ASTHMA_NMA_REVIEW.html": {
        "outcome": "EXAC_RR",
        "benchmarks": [
            {
                "label": "Thaweethai Bayesian NMA (mepolizumab)",
                "citation": "Thaweethai 2022",
                "year": 2022,
                "measure": "RR",
                "estimate": 0.37, "lci": 0.30, "uci": 0.45,
                "k": 8, "n": 6461,
                "scope": "Mepolizumab vs placebo; annual exacerbation rate in eosinophilic asthma (>=300 eos/uL). J Allergy Clin Immunol 2022.",
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
    lines.append(f"            {outcome}: [")
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
    lines.append(f"            {outcome}: '{outcome}'")
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
    print(f"\nBatch B: {ok} OK / {fail} fail / {'dry-run' if args.dry_run else 'apply'}")
    if fail: sys.exit(1)


if __name__ == "__main__":
    main()
