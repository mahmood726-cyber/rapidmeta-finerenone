#!/usr/bin/env python3
# sentinel:skip-file - developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Populate benchmarks for Batch H (14 onco #2 + immuno #1 apps)."""
import argparse, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

BATCH = {
    "CART_DLBCL_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "ZUMA-7 axi-cel vs SOC (2L LBCL)", "citation": "Locke 2022", "year": 2022,
             "measure": "HR", "estimate": 0.40, "lci": 0.31, "uci": 0.51, "k": 1, "n": 359,
             "scope": "Axicabtagene ciloleucel vs standard-of-care 2nd-line therapy in relapsed/refractory large B-cell lymphoma; event-free survival. NEJM 2022;386:640-654."},
            {"label": "TRANSFORM liso-cel vs SOC (2L LBCL)", "citation": "Kamdar 2022", "year": 2022,
             "measure": "HR", "estimate": 0.35, "lci": 0.23, "uci": 0.53, "k": 1, "n": 184,
             "scope": "Lisocabtagene maraleucel vs SOC in 2L R/R LBCL; EFS. Lancet 2022;399:2294-2308."},
        ]}
    },
    "CART_MM_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "CARTITUDE-4 cilta-cel vs SOC (multiple myeloma)", "citation": "San-Miguel 2023", "year": 2023,
             "measure": "HR", "estimate": 0.26, "lci": 0.18, "uci": 0.38, "k": 1, "n": 419,
             "scope": "Ciltacabtagene autoleucel vs physician's-choice regimen in 1-3 prior lines R/R MM; PFS. NEJM 2023;389:335-347."},
            {"label": "KarMMa-3 ide-cel vs SOC (MM)", "citation": "Rodriguez-Otero 2023", "year": 2023,
             "measure": "HR", "estimate": 0.49, "lci": 0.38, "uci": 0.65, "k": 1, "n": 386,
             "scope": "Idecabtagene vicleucel vs SOC regimen in triple-class-exposed R/R MM; PFS. NEJM 2023;388:1002-1014."},
        ]}
    },
    "CDK46_MBC_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "PALOMA-2 palbociclib + letrozole vs letrozole", "citation": "Rugo 2019", "year": 2019,
             "measure": "HR", "estimate": 0.58, "lci": 0.46, "uci": 0.72, "k": 1, "n": 666,
             "scope": "Palbociclib + letrozole vs placebo + letrozole in HR+/HER2- MBC 1L; PFS. NEJM 2016;375:1925-1936."},
            {"label": "MONARCH 3 abemaciclib + AI vs AI", "citation": "Goetz 2017", "year": 2017,
             "measure": "HR", "estimate": 0.54, "lci": 0.41, "uci": 0.72, "k": 1, "n": 493,
             "scope": "Abemaciclib + nonsteroidal AI vs AI in HR+/HER2- MBC 1L; PFS. JCO 2017;35:3638-3646."},
        ]}
    },
    "IO_CHEMO_NSCLC_1L_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "KEYNOTE-189 pembro + chemo vs chemo (NSCLC 1L)", "citation": "Gandhi 2018", "year": 2018,
             "measure": "HR", "estimate": 0.49, "lci": 0.38, "uci": 0.64, "k": 1, "n": 616,
             "scope": "Pembrolizumab + pemetrexed/platinum vs chemo alone in 1L non-squamous NSCLC; overall survival. NEJM 2018;378:2078-2092."},
            {"label": "KEYNOTE-407 pembro + chemo (squamous)", "citation": "Paz-Ares 2018", "year": 2018,
             "measure": "HR", "estimate": 0.64, "lci": 0.49, "uci": 0.85, "k": 1, "n": 559,
             "scope": "Pembrolizumab + carboplatin/taxane vs chemo in 1L squamous NSCLC; OS. NEJM 2018;379:2040-2051."},
        ]}
    },
    "LU_PSMA_MCRPC_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "VISION 177Lu-PSMA-617 vs SOC (mCRPC OS)", "citation": "Sartor 2021", "year": 2021,
             "measure": "HR", "estimate": 0.62, "lci": 0.52, "uci": 0.74, "k": 1, "n": 831,
             "scope": "177Lu-PSMA-617 + SOC vs SOC alone in PSMA+ mCRPC post-ARPI and taxane; overall survival. NEJM 2021;385:1091-1103."},
        ]}
    },
    "PARP_ARPI_MCRPC_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "PROpel olaparib + abiraterone (mCRPC 1L)", "citation": "Clarke 2022", "year": 2022,
             "measure": "HR", "estimate": 0.66, "lci": 0.54, "uci": 0.81, "k": 1, "n": 796,
             "scope": "Olaparib + abiraterone vs placebo + abiraterone in 1L mCRPC regardless of HRR status; radiographic PFS. NEJM Evidence 2022."},
            {"label": "TALAPRO-2 talazoparib + enzalutamide", "citation": "Agarwal 2023", "year": 2023,
             "measure": "HR", "estimate": 0.63, "lci": 0.51, "uci": 0.78, "k": 1, "n": 805,
             "scope": "Talazoparib + enzalutamide vs placebo + enzalutamide in 1L mCRPC; rPFS. Lancet 2023;402:291-303."},
        ]}
    },
    "PARP_OVARIAN_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "SOLO-1 olaparib maintenance (BRCA+ ovarian)", "citation": "Moore 2018", "year": 2018,
             "measure": "HR", "estimate": 0.30, "lci": 0.23, "uci": 0.41, "k": 1, "n": 391,
             "scope": "Olaparib vs placebo maintenance after platinum response in BRCA1/2-mutated newly diagnosed advanced ovarian; PFS. NEJM 2018;379:2495-2505."},
            {"label": "PAOLA-1 olaparib + bevacizumab maintenance", "citation": "Ray-Coquard 2019", "year": 2019,
             "measure": "HR", "estimate": 0.59, "lci": 0.49, "uci": 0.72, "k": 1, "n": 806,
             "scope": "Olaparib + bev vs placebo + bev maintenance in advanced ovarian (HRD+); PFS. NEJM 2019;381:2416-2428."},
        ]}
    },
    "TDXD_HER2LOW_BC_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "DESTINY-Breast04 T-DXd vs TPC (HER2-low)", "citation": "Modi 2022", "year": 2022,
             "measure": "HR", "estimate": 0.51, "lci": 0.40, "uci": 0.64, "k": 1, "n": 557,
             "scope": "Trastuzumab deruxtecan vs physician's-choice chemotherapy in HER2-low metastatic BC; PFS. NEJM 2022;387:9-20."},
        ]}
    },
    "VENETOCLAX_AML_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "VIALE-A venetoclax + azacitidine (unfit AML)", "citation": "DiNardo 2020", "year": 2020,
             "measure": "HR", "estimate": 0.66, "lci": 0.52, "uci": 0.85, "k": 1, "n": 431,
             "scope": "Venetoclax + azacitidine vs placebo + azacitidine in newly-diagnosed AML ineligible for intensive chemo; overall survival. NEJM 2020;383:617-629."},
        ]}
    },
    "ANIFROLUMAB_SLE_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "TULIP-2 anifrolumab vs placebo (SLE)", "citation": "Morand 2020", "year": 2020,
             "measure": "OR", "estimate": 2.20, "lci": 1.40, "uci": 3.60, "k": 1, "n": 362,
             "scope": "Anifrolumab vs placebo + SOC in moderate-to-severe SLE; BICLA response at week 52. NEJM 2020;382:211-221."},
        ]}
    },
    "BELIMUMAB_SLE_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "BLISS-52/-76 belimumab vs placebo meta (SLE)", "citation": "Furie 2011", "year": 2011,
             "measure": "OR", "estimate": 1.55, "lci": 1.22, "uci": 1.98, "k": 2, "n": 1684,
             "scope": "Belimumab 10 mg/kg vs placebo pooled (BLISS-52 + BLISS-76) in seropositive SLE; SRI4 response at week 52. Arthritis Rheum 2011;63:3918-3930."},
        ]}
    },
    "BIOLOGIC_ASTHMA_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "Biologic asthma meta (mepolizumab exemplar, exac)", "citation": "Thaweethai 2022", "year": 2022,
             "measure": "RR", "estimate": 0.37, "lci": 0.30, "uci": 0.45, "k": 8, "n": 6461,
             "scope": "Mepolizumab vs placebo in eosinophilic asthma (>=300 eos/uL); annual exacerbation rate. Bayesian NMA J Allergy Clin Immunol 2022."},
        ]}
    },
    "DUPILUMAB_AD_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "SOLO 1/2 dupilumab vs placebo (AD)", "citation": "Simpson 2016", "year": 2016,
             "measure": "RR", "estimate": 3.80, "lci": 2.90, "uci": 4.90, "k": 2, "n": 1379,
             "scope": "Dupilumab 300 mg Q2W vs placebo pooled (SOLO 1 + SOLO 2) in moderate-severe AD; EASI75 at week 16. NEJM 2016;375:2335-2348."},
        ]}
    },
    "DUPILUMAB_COPD_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "BOREAS dupilumab vs placebo (COPD + type 2 inflam)", "citation": "Bhatt 2023", "year": 2023,
             "measure": "RR", "estimate": 0.70, "lci": 0.58, "uci": 0.86, "k": 1, "n": 939,
             "scope": "Dupilumab vs placebo in COPD with type-2 inflammation (eos >=300); annual moderate-severe exacerbation rate. NEJM 2023;389:205-214."},
            {"label": "NOTUS dupilumab vs placebo (COPD confirmation)", "citation": "Bhatt 2024", "year": 2024,
             "measure": "RR", "estimate": 0.66, "lci": 0.54, "uci": 0.82, "k": 1, "n": 935,
             "scope": "Dupilumab vs placebo in COPD + type-2 inflam; annual exac rate (confirmatory trial). NEJM 2024;390:2274-2283."},
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
    print(f"\nBatch H: {ok} OK / {fail} fail / {'dry-run' if args.dry_run else 'apply'}")
    if fail: sys.exit(1)


if __name__ == "__main__":
    main()
