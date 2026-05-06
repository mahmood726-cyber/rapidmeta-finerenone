#!/usr/bin/env python3
# sentinel:skip-file - developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Populate benchmarks for Batch I (14 immuno #2 + neuro apps)."""
import argparse, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

BATCH = {
    "IL23_PSORIASIS_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "UltIMMa-1/2 risankizumab vs placebo + ustek (PASI90)", "citation": "Gordon 2018", "year": 2018,
             "measure": "RR", "estimate": 17.5, "lci": 14.6, "uci": 21.0, "k": 2, "n": 997,
             "scope": "Risankizumab 150 mg vs placebo in moderate-severe plaque psoriasis; PASI90 at week 16. Lancet 2018;392:650-661."},
            {"label": "Sbidian Cochrane NMA (bimekizumab exemplar)", "citation": "Sbidian 2023", "year": 2023,
             "measure": "RR", "estimate": 17.0, "lci": 14.0, "uci": 21.0, "k": 179, "n": 60330,
             "scope": "Bimekizumab vs placebo PASI90 in Cochrane 179-RCT living NMA. CD011535.pub6 2023."},
        ]}
    },
    "JAK_RA_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "JAKi RA NMA (upadacitinib 15 mg ACR20)", "citation": "Li 2024", "year": 2024,
             "measure": "RR", "estimate": 2.10, "lci": 1.90, "uci": 2.40, "k": 39, "n": 16894,
             "scope": "Upadacitinib 15 mg vs placebo; ACR20 at 12-24 wk. Frontiers Pharmacol 2024 39-RCT NMA."},
        ]}
    },
    "JAK_UC_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "OCTAVE Induction tofacitinib vs placebo (UC)", "citation": "Sandborn 2017", "year": 2017,
             "measure": "RR", "estimate": 2.80, "lci": 1.70, "uci": 4.60, "k": 2, "n": 1139,
             "scope": "Tofacitinib 10 mg BID vs placebo induction in moderate-severe UC; clinical remission at 8 wk (OCTAVE 1+2 pool). NEJM 2017;376:1723-1736."},
            {"label": "U-ACHIEVE + U-ACCOMPLISH upa vs placebo (UC)", "citation": "Danese 2022", "year": 2022,
             "measure": "RR", "estimate": 5.00, "lci": 3.50, "uci": 7.20, "k": 2, "n": 989,
             "scope": "Upadacitinib 45 mg vs placebo induction in moderate-severe UC; clinical remission at 8 wk. Lancet 2022;399:2113-2128."},
        ]}
    },
    "JAKI_AD_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "JADE MONO-1/-2 abrocitinib vs placebo (AD EASI75)", "citation": "Silverberg 2020", "year": 2020,
             "measure": "RR", "estimate": 3.50, "lci": 2.50, "uci": 4.90, "k": 2, "n": 778,
             "scope": "Abrocitinib 200 mg vs placebo in moderate-severe AD; EASI75 at 12 wk. JAMA Dermatol 2020;156:863-873."},
            {"label": "Measure Up 1/2 upadacitinib vs placebo (AD)", "citation": "Guttman-Yassky 2021", "year": 2021,
             "measure": "RR", "estimate": 4.50, "lci": 3.30, "uci": 6.20, "k": 2, "n": 1683,
             "scope": "Upadacitinib 30 mg vs placebo in moderate-severe AD; EASI75 at 16 wk. Lancet 2021;397:2151-2168."},
        ]}
    },
    "MIRIKIZUMAB_UC_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "LUCENT-1/-2 mirikizumab vs placebo (UC)", "citation": "D'Haens 2023", "year": 2023,
             "measure": "RR", "estimate": 2.90, "lci": 1.90, "uci": 4.50, "k": 2, "n": 1386,
             "scope": "Mirikizumab 300 mg vs placebo induction + maintenance in moderate-severe UC; clinical remission. NEJM 2023;388:2444-2455."},
        ]}
    },
    "RISANKIZUMAB_CD_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "ADVANCE/MOTIVATE risankizumab vs placebo (CD)", "citation": "D'Haens 2022", "year": 2022,
             "measure": "RR", "estimate": 2.10, "lci": 1.60, "uci": 2.70, "k": 2, "n": 1419,
             "scope": "Risankizumab 600 mg vs placebo induction in moderate-severe CD; clinical remission at 12 wk. Lancet 2022;399:2015-2030."},
        ]}
    },
    "UPADACITINIB_CD_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "U-EXCEED + U-EXCEL upa vs placebo (CD)", "citation": "Loftus 2023", "year": 2023,
             "measure": "RR", "estimate": 2.90, "lci": 2.10, "uci": 4.10, "k": 2, "n": 1021,
             "scope": "Upadacitinib 45 mg vs placebo induction in moderate-severe CD; clinical remission at 12 wk. NEJM 2023;388:1966-1980."},
        ]}
    },
    "ANTIAMYLOID_AD_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "Avgerinos anti-amyloid pool (lecanemab + donanemab CDR-SB)", "citation": "Avgerinos 2023", "year": 2023,
             "measure": "MD", "estimate": -0.49, "lci": -0.67, "uci": -0.30, "k": 2, "n": 3531,
             "scope": "Lecanemab (CLARITY-AD) + donanemab (TRAILBLAZER-ALZ2) pooled vs placebo; CDR-SB change at 18 mo."},
        ]}
    },
    "CBD_SEIZURE_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "Devinsky CBD vs placebo (Dravet seizure freq)", "citation": "Devinsky 2017", "year": 2017,
             "measure": "MD", "estimate": -22.8, "lci": -41.1, "uci": -5.4, "k": 1, "n": 120,
             "scope": "Cannabidiol 20 mg/kg/d vs placebo in Dravet syndrome; convulsive seizure frequency percent change from baseline. NEJM 2017;376:2011-2020."},
        ]}
    },
    "CGRP_MIGRAINE_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "Anti-CGRP mAb NMA (galcanezumab MMD)", "citation": "Haghdoost 2023", "year": 2023,
             "measure": "MD", "estimate": -2.10, "lci": -2.76, "uci": -1.45, "k": 16, "n": 9123,
             "scope": "Galcanezumab 240 mg vs placebo; monthly migraine days reduction. Cephalalgia 2023 Phase 3 NMA."},
        ]}
    },
    "ESKETAMINE_TRD_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "TRANSFORM-2 esketamine vs placebo (TRD MADRS)", "citation": "Popova 2019", "year": 2019,
             "measure": "MD", "estimate": -4.00, "lci": -7.31, "uci": -0.69, "k": 1, "n": 223,
             "scope": "Esketamine intranasal + oral antidepressant vs placebo spray + AD in treatment-resistant depression; MADRS change at 28 d. Am J Psychiatry 2019;176:428-438."},
        ]}
    },
    "FENFLURAMINE_SEIZURE_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "Lagae fenfluramine vs placebo (Dravet seizures)", "citation": "Lagae 2019", "year": 2019,
             "measure": "MD", "estimate": -54.7, "lci": -68.3, "uci": -41.1, "k": 1, "n": 119,
             "scope": "Fenfluramine 0.7 mg/kg/d vs placebo in Dravet syndrome; convulsive seizure frequency percent change from baseline. Lancet 2019;394:2243-2254."},
        ]}
    },
    "KARXT_SCZ_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "EMERGENT-2 KarXT vs placebo (schizophrenia PANSS)", "citation": "Kaul 2024", "year": 2024,
             "measure": "MD", "estimate": -9.60, "lci": -13.90, "uci": -5.30, "k": 1, "n": 252,
             "scope": "Xanomeline + trospium (KarXT) vs placebo in acute schizophrenia; PANSS total change at week 5. Lancet 2024;403:160-170."},
        ]}
    },
    "PATISIRAN_POLYNEUROPATHY_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "APOLLO patisiran vs placebo (hATTR mNIS+7)", "citation": "Adams 2018", "year": 2018,
             "measure": "MD", "estimate": -34.0, "lci": -39.9, "uci": -28.1, "k": 1, "n": 225,
             "scope": "Patisiran vs placebo in hereditary transthyretin amyloidosis with polyneuropathy; mNIS+7 change at 18 mo. NEJM 2018;379:11-21."},
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
    print(f"\nBatch I: {ok} OK / {fail} fail / {'dry-run' if args.dry_run else 'apply'}")
    if fail: sys.exit(1)


if __name__ == "__main__":
    main()
