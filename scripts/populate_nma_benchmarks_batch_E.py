#!/usr/bin/env python3
# sentinel:skip-file - developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Populate benchmarks for Batch E (3 specialty NMAs)."""
import argparse, pathlib, re, sys

ROOT = pathlib.Path(r"C:\Projects\Finrenone")

# CFTR has TWO outcomes (ppFEV1 + PulmExacRR) — needs dict of outcome arrays.
BATCH = {
    "ANTIVEGF_NAMD_NMA_REVIEW.html": {
        "outcomes": ["BCVA"],
        "benchmarks": {
            "BCVA": [
                {
                    "label": "MARINA ranibizumab vs sham (BCVA 12 mo)",
                    "citation": "Rosenfeld 2006",
                    "year": 2006,
                    "measure": "MD",
                    "estimate": 17.5, "lci": 13.0, "uci": 22.0,
                    "k": 1, "n": 716,
                    "scope": "Ranibizumab 0.5 mg monthly vs sham; BCVA change (ETDRS letters) at 12 mo. Pivotal anti-VEGF efficacy anchor, NEJM 2006;355:1419-1431.",
                },
                {
                    "label": "TENAYA/LUCERNE faricimab vs aflibercept (BCVA 1 yr)",
                    "citation": "Heier 2022",
                    "year": 2022,
                    "measure": "MD",
                    "estimate": 0.04, "lci": -0.65, "uci": 0.73,
                    "k": 2, "n": 1329,
                    "scope": "Faricimab 6 mg Q16W vs aflibercept Q8W; BCVA change. Non-inferior, Lancet 2022;399:729-740. Representative modern head-to-head.",
                },
            ],
        },
    },
    "CFTR_MODULATORS_NMA_REVIEW.html": {
        "outcomes": ["ppFEV1", "PulmExacRR"],
        "benchmarks": {
            "ppFEV1": [
                {
                    "label": "Middleton ELX/TEZ/IVA vs placebo (ppFEV1)",
                    "citation": "Middleton 2019",
                    "year": 2019,
                    "measure": "MD",
                    "estimate": 13.8, "lci": 12.1, "uci": 15.4,
                    "k": 1, "n": 403,
                    "scope": "Elexacaftor/tezacaftor/ivacaftor vs placebo; absolute ppFEV1 change at 4 wk in F508del heterozygous CF. Pivotal triple-modulator trial, NEJM 2019;381:1809-1819.",
                },
            ],
            "PulmExacRR": [
                {
                    "label": "Triple CFTR modulator pool (pulmonary exacerbation)",
                    "citation": "Huang 2023",
                    "year": 2023,
                    "measure": "OR",
                    "estimate": 0.29, "lci": 0.19, "uci": 0.43,
                    "k": 3, "n": 800,
                    "scope": "ELX/TEZ/IVA vs placebo 3-study pool; pulmonary exacerbation odds. Frontiers Pharmacol 2023 SR-MA.",
                },
            ],
        },
    },
    "DOAC_VTE_NMA_REVIEW.html": {
        "outcomes": ["VTE"],
        "benchmarks": {
            "VTE": [
                {
                    "label": "DOAC pooled vs VKA MA (VTE recurrence)",
                    "citation": "van der Hulle 2014",
                    "year": 2014,
                    "measure": "RR",
                    "estimate": 0.90, "lci": 0.77, "uci": 1.06,
                    "k": 6, "n": 27000,
                    "scope": "DOACs (rivaroxaban + apixaban + dabigatran + edoxaban) pooled vs VKA; VTE recurrence in acute VTE. Blood 2014;124:1968-1975.",
                },
            ],
        },
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
    """If one outcome, map all legacy keys + 'default' to it.
    If multiple, default to first; each outcome key maps to itself."""
    primary = outcomes[0]
    legacy = ["default", "MACE", "ACH", "ACM", "Renal40", "Hyperkalemia",
              "HF_CV_First", "KidneyComp", "Renal57"]
    lines = ["{"]
    for k in legacy:
        lines.append(f"            {k}: '{primary}',")
    for o in outcomes:
        lines.append(f"            '{o}': '{o}',")
    # strip trailing comma from last line
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
    print(f"\nBatch E: {ok} OK / {fail} fail / {'dry-run' if args.dry_run else 'apply'}")
    if fail: sys.exit(1)


if __name__ == "__main__":
    main()
