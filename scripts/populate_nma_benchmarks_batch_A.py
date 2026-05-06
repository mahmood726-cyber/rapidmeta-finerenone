#!/usr/bin/env python3
# sentinel:skip-file - developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Populate PUBLISHED_META_BENCHMARKS + BENCHMARK_OUTCOME_MAP for Batch A (5 cardio-metabolic NMAs).

Each NMA:
  1. Rewrites BENCHMARK_OUTCOME_MAP (still Finerenone clone-template) to map
     all known keys to the app-specific outcomeKey so 'default' resolves.
  2. Populates PUBLISHED_META_BENCHMARKS = {} with one or more topic-appropriate
     published meta-analysis entries (label, citation, year, measure, estimate,
     lci, uci, k, n, scope).

Verified via WebSearch of primary sources 2026-04-23. All numbers traced to
published abstracts/full texts.
"""
import argparse, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# outcomeKey -> list of benchmark entries. Each entry is a dict.
# measure/estimate/lci/uci all numeric. Scope is human-readable.
BATCH_A = {
    "SGLT2I_HF_NMA_REVIEW.html": {
        "outcome": "CVDEATH_HHF",
        "benchmarks": [
            {
                "label": "Vaduganathan 5-trial pooled analysis",
                "citation": "Vaduganathan 2022",
                "year": 2022,
                "measure": "HR",
                "estimate": 0.77, "lci": 0.72, "uci": 0.82,
                "k": 5, "n": 21947,
                "scope": "SGLT2i across EF spectrum; CV death or first HHF (DAPA-HF + EMPEROR-Reduced + DELIVER + EMPEROR-Preserved + SOLOIST-WHF). Lancet 2022;400:757-767.",
            },
        ],
    },
    "DOAC_AF_NMA_REVIEW.html": {
        "outcome": "STROKE_SE",
        "benchmarks": [
            {
                "label": "Ruff pooled DOAC vs warfarin MA",
                "citation": "Ruff 2014",
                "year": 2014,
                "measure": "RR",
                "estimate": 0.81, "lci": 0.73, "uci": 0.91,
                "k": 4, "n": 71683,
                "scope": "DOACs pooled vs warfarin; stroke or systemic embolism. RE-LY+ROCKET-AF+ARISTOTLE+ENGAGE-AF. Lancet 2014;383:955-962.",
            },
        ],
    },
    "GLP1_CVOT_NMA_REVIEW.html": {
        "outcome": "MACE",
        "benchmarks": [
            {
                "label": "Sattar GLP-1 CVOT meta-analysis",
                "citation": "Sattar 2021",
                "year": 2021,
                "measure": "HR",
                "estimate": 0.86, "lci": 0.80, "uci": 0.93,
                "k": 8, "n": 60080,
                "scope": "GLP-1 RAs vs placebo; 3-point MACE (CV death + nonfatal MI + nonfatal stroke). Lancet Diabetes Endocrinol 2021;9:653-662.",
            },
        ],
    },
    "PCSK9_LIPID_NMA_REVIEW.html": {
        "outcome": "MACE",
        "benchmarks": [
            {
                "label": "Schmidt Cochrane review",
                "citation": "Schmidt 2017",
                "year": 2017,
                "measure": "OR",
                "estimate": 0.86, "lci": 0.80, "uci": 0.92,
                "k": 20, "n": 67237,
                "scope": "PCSK9 inhibitors (alirocumab + evolocumab) vs placebo; composite cardiovascular events. Cochrane 2017.",
            },
        ],
    },
    "INCRETINS_T2D_NMA_REVIEW.html": {
        "outcome": "HBA1C",
        "benchmarks": [
            {
                "label": "Htike GLP-1 RA NMA (liraglutide 1.8 mg exemplar)",
                "citation": "Htike 2017",
                "year": 2017,
                "measure": "MD",
                "estimate": -1.14, "lci": -1.23, "uci": -1.05,
                "k": 34, "n": 14464,
                "scope": "Liraglutide 1.8 mg vs placebo; HbA1c (%) change at 24-32 wk. Class reductions span -0.55 (lixisenatide) to -1.21 (dulaglutide).",
            },
        ],
    },
}


# ---- brace-balanced utilities ------------------------------------------------
def find_balanced_close(text: str, open_pos: int) -> int:
    depth = 0
    i = open_pos
    while i < len(text):
        c = text[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def render_benchmark_block(outcome: str, benchmarks: list) -> str:
    """Render `const PUBLISHED_META_BENCHMARKS = {...};` block."""
    lines = ["{"]
    lines.append(f"            {outcome}: [")
    for b in benchmarks:
        lines.append(
            "                { "
            f"label: '{b['label']}', "
            f"citation: '{b['citation']}', "
            f"year: {b['year']}, "
            f"measure: '{b['measure']}', "
            f"estimate: {b['estimate']}, "
            f"lci: {b['lci']}, "
            f"uci: {b['uci']}, "
            f"k: {b['k']}, "
            f"n: {b['n']}, "
            f"scope: '{b['scope'].replace(chr(39), chr(92) + chr(39))}' "
            "},"
        )
    lines.append("            ]")
    lines.append("        }")
    return "\n".join(lines)


def render_outcome_map(outcome: str) -> str:
    """Rewrite BENCHMARK_OUTCOME_MAP so every legacy key points to the app's actual outcome."""
    legacy_keys = ["default", "MACE", "ACH", "ACM", "Renal40", "Hyperkalemia",
                   "HF_CV_First", "KidneyComp", "Renal57"]
    lines = ["{"]
    for k in legacy_keys:
        lines.append(f"            {k}: '{outcome}',")
    lines.append(f"            {outcome}: '{outcome}'")
    lines.append("        }")
    return "\n".join(lines)


def replace_const_decl(text: str, const_name: str, new_rhs_block: str) -> tuple:
    """Replace `const NAME = {...};` with `const NAME = <new_rhs_block>;`.

    new_rhs_block is the full `{...}` body. Preserves trailing semicolon.
    Returns (new_text, changed_bool).
    """
    pat = re.compile(rf"const\s+{re.escape(const_name)}\s*=\s*\{{")
    m = pat.search(text)
    if not m:
        return text, False
    open_pos = m.end() - 1
    close_pos = find_balanced_close(text, open_pos)
    if close_pos < 0:
        return text, False
    # Skip past optional `;` after `}`
    after = close_pos + 1
    while after < len(text) and text[after] in " \t":
        after += 1
    if after < len(text) and text[after] == ';':
        after += 1
    replacement = f"const {const_name} = {new_rhs_block};"
    new_text = text[:m.start()] + replacement + text[after:]
    return new_text, True


def apply_to_file(path: pathlib.Path, outcome: str, benchmarks: list, dry_run: bool) -> str:
    text = path.read_text(encoding="utf-8", newline="")
    crlf = "\r\n" in text
    work = text.replace("\r\n", "\n") if crlf else text

    new_bench = render_benchmark_block(outcome, benchmarks)
    new_map = render_outcome_map(outcome)

    work2, changed1 = replace_const_decl(work, "PUBLISHED_META_BENCHMARKS", new_bench)
    work3, changed2 = replace_const_decl(work2, "BENCHMARK_OUTCOME_MAP", new_map)

    if not (changed1 and changed2):
        return f"FAIL {path.name}: bench={changed1} map={changed2}"

    if work3 == work:
        return f"NOOP {path.name}: no change"

    if not dry_run:
        out = work3.replace("\n", "\r\n") if crlf else work3
        path.write_text(out, encoding="utf-8", newline="")
    return f"OK   {path.name}: bench+{len(benchmarks)} map=fixed"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run or args.apply):
        ap.error("pass --dry-run or --apply")

    ok = fail = 0
    for name, spec in BATCH_A.items():
        path = ROOT / name
        if not path.exists():
            print(f"SKIP {name}: not found")
            continue
        r = apply_to_file(path, spec["outcome"], spec["benchmarks"], dry_run=args.dry_run)
        print(r)
        if r.startswith("OK"):
            ok += 1
        else:
            fail += 1
    print(f"\nBatch A: {ok} OK / {fail} fail / {'dry-run' if args.dry_run else 'apply'}")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
