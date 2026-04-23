#!/usr/bin/env python3
# sentinel:skip-file - developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Populate benchmarks for Batch F (14 cardio pairwise apps).

Each uses the drug's pivotal RCT as the anchor (with 'MACE' outcome key).
BENCHMARK_OUTCOME_MAP routes all legacy keys (incl. MACE) to MACE so the
benchmark shows regardless of selected outcome.
"""
import argparse, pathlib, re, sys

ROOT = pathlib.Path(r"C:\Projects\Finrenone")

BATCH = {
    "ABLATION_AF_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {
            "MACE": [
                {"label": "CASTLE-AF ablation vs drug (AF + HF)", "citation": "Marrouche 2018", "year": 2018,
                 "measure": "HR", "estimate": 0.62, "lci": 0.43, "uci": 0.87, "k": 1, "n": 363,
                 "scope": "Catheter ablation vs medical therapy in AF + HFrEF; ACM or HF hospitalization. NEJM 2018;378:417-427."},
            ]
        }
    },
    "ARNI_HF_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {
            "MACE": [
                {"label": "PARADIGM-HF sacubitril/valsartan vs enalapril", "citation": "McMurray 2014", "year": 2014,
                 "measure": "HR", "estimate": 0.80, "lci": 0.73, "uci": 0.87, "k": 1, "n": 8442,
                 "scope": "Sacubitril/valsartan vs enalapril in HFrEF; CV death or first HHF. NEJM 2014;371:993-1004."},
            ]
        }
    },
    "BEMPEDOIC_ACID_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {
            "MACE": [
                {"label": "CLEAR Outcomes bempedoic acid vs placebo", "citation": "Nissen 2023", "year": 2023,
                 "measure": "HR", "estimate": 0.87, "lci": 0.79, "uci": 0.96, "k": 1, "n": 13970,
                 "scope": "Bempedoic acid vs placebo in statin-intolerant primary/secondary prevention; MACE-4 (CV death, MI, stroke, coronary revascularization). NEJM 2023;388:1353-1364."},
            ]
        }
    },
    "CANGRELOR_PCI_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {
            "MACE": [
                {"label": "CHAMPION PHOENIX cangrelor vs clopidogrel", "citation": "Bhatt 2013", "year": 2013,
                 "measure": "OR", "estimate": 0.78, "lci": 0.66, "uci": 0.93, "k": 1, "n": 11145,
                 "scope": "Cangrelor vs clopidogrel at PCI; death, MI, ischemia-driven revascularization, or stent thrombosis at 48 h. NEJM 2013;368:1303-1313."},
            ]
        }
    },
    "DOAC_AF_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {
            "MACE": [
                {"label": "Ruff pooled DOAC vs warfarin MA (stroke/SE)", "citation": "Ruff 2014", "year": 2014,
                 "measure": "RR", "estimate": 0.81, "lci": 0.73, "uci": 0.91, "k": 4, "n": 71683,
                 "scope": "DOACs pooled vs warfarin in AF; stroke or systemic embolism. Lancet 2014;383:955-962."},
            ]
        }
    },
    "INCLISIRAN_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {
            "MACE": [
                {"label": "ORION-10/-11 inclisiran vs placebo (LDL-C)", "citation": "Ray 2020", "year": 2020,
                 "measure": "MD", "estimate": -52.0, "lci": -56.2, "uci": -47.8, "k": 2, "n": 3178,
                 "scope": "Inclisiran vs placebo in ASCVD/FH; LDL-C percent change at day 510. MACE outcomes await ORION-4. NEJM 2020;382:1507-1519."},
            ]
        }
    },
    "INCRETIN_HFpEF_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {
            "MACE": [
                {"label": "STEP-HFpEF semaglutide 2.4 mg (KCCQ)", "citation": "Kosiborod 2023", "year": 2023,
                 "measure": "MD", "estimate": 7.80, "lci": 4.80, "uci": 10.90, "k": 1, "n": 529,
                 "scope": "Semaglutide 2.4 mg vs placebo in HFpEF + obesity; KCCQ-CSS change. NEJM 2023;389:1069-1084."},
            ]
        }
    },
    "IV_IRON_HF_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {
            "MACE": [
                {"label": "IV iron HF pooled MA (Graham 2023)", "citation": "Graham 2023", "year": 2023,
                 "measure": "RR", "estimate": 0.84, "lci": 0.76, "uci": 0.93, "k": 3, "n": 4501,
                 "scope": "IV ferric carboxymaltose vs placebo in iron-deficient HFrEF (AFFIRM-AHF + CONFIRM-HF + HEART-FID + IRONMAN); CV death + HHF. Eur Heart J 2023."},
            ]
        }
    },
    "INSULIN_ICODEC_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {
            "MACE": [
                {"label": "ONWARDS program icodec vs daily basal (HbA1c)", "citation": "Mathieu 2023", "year": 2023,
                 "measure": "MD", "estimate": -0.05, "lci": -0.14, "uci": 0.04, "k": 6, "n": 4157,
                 "scope": "Insulin icodec weekly vs daily basal insulin in T2D; HbA1c change (non-inferior). ONWARDS 1-6 pool."},
            ]
        }
    },
    "MITRAL_FUNCMR_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {
            "MACE": [
                {"label": "COAPT MitraClip vs GDMT (functional MR)", "citation": "Stone 2018", "year": 2018,
                 "measure": "HR", "estimate": 0.53, "lci": 0.40, "uci": 0.70, "k": 1, "n": 614,
                 "scope": "Transcatheter mitral leaflet edge-to-edge repair (MitraClip) + GDMT vs GDMT in severe secondary MR; HHF at 24 mo. NEJM 2018;379:2307-2318."},
            ]
        }
    },
    "PCSK9_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {
            "MACE": [
                {"label": "FOURIER evolocumab vs placebo", "citation": "Sabatine 2017", "year": 2017,
                 "measure": "HR", "estimate": 0.85, "lci": 0.79, "uci": 0.92, "k": 1, "n": 27564,
                 "scope": "Evolocumab + statin vs placebo + statin in ASCVD; CV death, MI, stroke, hospitalization for UA or coronary revascularization. NEJM 2017;376:1713-1722."},
                {"label": "ODYSSEY OUTCOMES alirocumab vs placebo", "citation": "Schwartz 2018", "year": 2018,
                 "measure": "HR", "estimate": 0.85, "lci": 0.78, "uci": 0.93, "k": 1, "n": 18924,
                 "scope": "Alirocumab vs placebo post-ACS; CHD death, MI, ischemic stroke, or UA requiring hospitalization. NEJM 2018;379:2097-2107."},
            ]
        }
    },
    "RIVAROXABAN_VASC_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {
            "MACE": [
                {"label": "COMPASS rivaroxaban 2.5 mg + ASA vs ASA", "citation": "Eikelboom 2017", "year": 2017,
                 "measure": "HR", "estimate": 0.76, "lci": 0.66, "uci": 0.86, "k": 1, "n": 27395,
                 "scope": "Rivaroxaban 2.5 mg BID + aspirin 100 mg QD vs aspirin alone in stable ASCVD/PAD; CV death, stroke, or MI. NEJM 2017;377:1319-1330."},
            ]
        }
    },
    "SEMAGLUTIDE_OBESITY_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {
            "MACE": [
                {"label": "SELECT semaglutide 2.4 mg vs placebo", "citation": "Lincoff 2023", "year": 2023,
                 "measure": "HR", "estimate": 0.80, "lci": 0.72, "uci": 0.90, "k": 1, "n": 17604,
                 "scope": "Semaglutide 2.4 mg weekly vs placebo in overweight/obese CVD without diabetes; CV death, nonfatal MI, nonfatal stroke. NEJM 2023;389:2221-2232."},
            ]
        }
    },
    "SGLT2_MACE_CVOT_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {
            "MACE": [
                {"label": "Zelniker SGLT2i CVOT MA", "citation": "Zelniker 2019", "year": 2019,
                 "measure": "HR", "estimate": 0.89, "lci": 0.83, "uci": 0.96, "k": 3, "n": 34322,
                 "scope": "SGLT2i pooled (EMPA-REG OUTCOME + CANVAS + DECLARE-TIMI 58) vs placebo; 3-point MACE. Lancet 2019;393:31-39."},
            ]
        }
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
    print(f"\nBatch F: {ok} OK / {fail} fail / {'dry-run' if args.dry_run else 'apply'}")
    if fail: sys.exit(1)


if __name__ == "__main__":
    main()
