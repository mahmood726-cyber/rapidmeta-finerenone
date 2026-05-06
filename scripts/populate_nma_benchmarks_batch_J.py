#!/usr/bin/env python3
# sentinel:skip-file - developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Populate benchmarks for Batch J (15 mixed pairwise apps; 3 legacy MISSING deferred)."""
import argparse, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

BATCH = {
    "HIGH_EFFICACY_MS_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "OPERA I+II ocrelizumab vs IFN beta-1a (RRMS ARR)", "citation": "Hauser 2017", "year": 2017,
             "measure": "RR", "estimate": 0.53, "lci": 0.40, "uci": 0.71, "k": 2, "n": 1656,
             "scope": "Ocrelizumab 600 mg Q6mo vs interferon beta-1a SC in relapsing MS; annualized relapse rate at 96 wk. NEJM 2017;376:221-234."},
        ]}
    },
    "CAB_PREP_HIV_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "HPTN 083 cabotegravir-LA vs daily TDF/FTC (PrEP MSM/TGW)", "citation": "Landovitz 2021", "year": 2021,
             "measure": "HR", "estimate": 0.34, "lci": 0.18, "uci": 0.62, "k": 1, "n": 4566,
             "scope": "Long-acting cabotegravir IM Q8W vs daily oral TDF/FTC in at-risk MSM/transgender women; HIV incidence. NEJM 2021;385:595-608."},
            {"label": "HPTN 084 CAB-LA vs TDF/FTC (cis women)", "citation": "Delany-Moretlwe 2022", "year": 2022,
             "measure": "HR", "estimate": 0.11, "lci": 0.04, "uci": 0.31, "k": 1, "n": 3224,
             "scope": "CAB-LA vs daily TDF/FTC in sub-Saharan African cisgender women; HIV incidence. Lancet 2022;399:1779-1789."},
        ]}
    },
    "COVID_ORAL_ANTIVIRALS_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "EPIC-HR nirmatrelvir/ritonavir vs placebo (hosp/death)", "citation": "Hammond 2022", "year": 2022,
             "measure": "RR", "estimate": 0.11, "lci": 0.05, "uci": 0.23, "k": 1, "n": 2246,
             "scope": "Nirmatrelvir/ritonavir 5-day vs placebo in unvaccinated high-risk COVID-19 outpatients; hospitalization or death by day 28. NEJM 2022;386:1397-1408."},
            {"label": "MOVe-OUT molnupiravir vs placebo", "citation": "Jayk Bernal 2022", "year": 2022,
             "measure": "RR", "estimate": 0.70, "lci": 0.49, "uci": 0.99, "k": 1, "n": 1433,
             "scope": "Molnupiravir 800 mg BID x 5 d vs placebo in at-risk unvaccinated COVID-19 outpatients; hosp/death at 29 d. NEJM 2022;386:509-520."},
        ]}
    },
    "LENACAPAVIR_PREP_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "PURPOSE 1 lenacapavir 2x/yr vs TDF/FTC (cis women)", "citation": "Bekker 2024", "year": 2024,
             "measure": "HR", "estimate": 0.0, "lci": 0.0, "uci": 0.10, "k": 1, "n": 2134,
             "scope": "Lenacapavir SC Q26W vs daily TDF/FTC or F-TAF in sub-Saharan African cisgender women/adolescents; HIV incidence (100% efficacy, 0 infections in lenacapavir arm). NEJM 2024;391:1179-1192."},
            {"label": "PURPOSE 2 lenacapavir (MSM/TGW/GD)", "citation": "Kelley 2024", "year": 2024,
             "measure": "HR", "estimate": 0.04, "lci": 0.00, "uci": 0.18, "k": 1, "n": 3265,
             "scope": "Lenacapavir SC Q26W vs daily TDF/FTC in cisgender MSM, transgender and gender-diverse individuals; HIV incidence. NEJM 2024."},
        ]}
    },
    "NIRSEVIMAB_INFANT_RSV_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "MELODY nirsevimab vs placebo (infant RSV LRTI)", "citation": "Hammitt 2022", "year": 2022,
             "measure": "RR", "estimate": 0.25, "lci": 0.13, "uci": 0.46, "k": 1, "n": 1490,
             "scope": "Nirsevimab 50/100 mg IM one-time vs placebo in healthy term/late-preterm infants; medically-attended RSV LRTI through 150 d. NEJM 2022;386:837-846."},
        ]}
    },
    "RSV_VACCINE_OLDER_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "RENOIR RSVpreF (Pfizer) vs placebo in >=60y", "citation": "Papi 2023", "year": 2023,
             "measure": "RR", "estimate": 0.33, "lci": 0.14, "uci": 0.71, "k": 1, "n": 34284,
             "scope": "Bivalent RSV prefusion F vaccine (Pfizer) vs placebo in adults >=60y; RSV-associated LRTI >=2 signs. NEJM 2023;388:1465-1477."},
            {"label": "AReSVi-006 RSVPreF3-AS01 (GSK) vs placebo", "citation": "Papi 2023b", "year": 2023,
             "measure": "RR", "estimate": 0.18, "lci": 0.07, "uci": 0.44, "k": 1, "n": 24966,
             "scope": "Adjuvanted RSVPreF3 OA vaccine (GSK) vs placebo in >=60y; RSV-LRTD season 1. NEJM 2023;388:595-608."},
        ]}
    },
    "CFTR_CF_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "Middleton ELX/TEZ/IVA vs placebo (ppFEV1)", "citation": "Middleton 2019", "year": 2019,
             "measure": "MD", "estimate": 13.80, "lci": 12.10, "uci": 15.40, "k": 1, "n": 403,
             "scope": "Elexacaftor/tezacaftor/ivacaftor vs placebo; absolute ppFEV1 change at 4 wk in F508del-heterozygous CF. NEJM 2019;381:1809-1819."},
        ]}
    },
    "EVT_BASILAR_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "ATTENTION EVT vs best medical (basilar occlusion)", "citation": "Tao 2022", "year": 2022,
             "measure": "RR", "estimate": 2.06, "lci": 1.46, "uci": 2.91, "k": 1, "n": 340,
             "scope": "Endovascular thrombectomy vs best medical management within 12 h of basilar artery occlusion; mRS 0-3 at 90 d. NEJM 2022;387:1361-1372."},
            {"label": "BAOCHE EVT vs medical (basilar stroke)", "citation": "Jovin 2022", "year": 2022,
             "measure": "RR", "estimate": 1.81, "lci": 1.26, "uci": 2.60, "k": 1, "n": 217,
             "scope": "Endovascular thrombectomy 6-24 h after basilar occlusion; mRS 0-3 at 90 d. NEJM 2022;387:1373-1384."},
        ]}
    },
    "EVT_EXTENDED_WINDOW_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "HERMES extended-window pool (DAWN + DEFUSE 3)", "citation": "Jovin 2022b", "year": 2022,
             "measure": "OR", "estimate": 2.54, "lci": 1.83, "uci": 3.54, "k": 2, "n": 388,
             "scope": "EVT vs medical therapy 6-24 h after anterior-circulation stroke with favorable imaging; functional independence (mRS 0-2) at 90 d. Lancet 2022."},
        ]}
    },
    "EVT_LARGECORE_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "SELECT2 EVT vs medical (large core)", "citation": "Sarraj 2023", "year": 2023,
             "measure": "OR", "estimate": 2.43, "lci": 1.59, "uci": 3.71, "k": 1, "n": 352,
             "scope": "Endovascular thrombectomy vs medical management in large ischemic core (ASPECTS 3-5 or core >=50 mL); mRS 0-3 at 90 d. NEJM 2023;388:1259-1271."},
            {"label": "RESCUE-Japan LIMIT EVT vs medical (low ASPECTS)", "citation": "Yoshimura 2022", "year": 2022,
             "measure": "RR", "estimate": 2.43, "lci": 1.35, "uci": 4.37, "k": 1, "n": 203,
             "scope": "EVT vs medical care in acute stroke with large ischemic core (ASPECTS 3-5); mRS 0-3 at 90 d. NEJM 2022;386:1303-1313."},
        ]}
    },
    "FARICIMAB_NAMD_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "TENAYA/LUCERNE faricimab vs aflibercept (nAMD BCVA)", "citation": "Heier 2022", "year": 2022,
             "measure": "MD", "estimate": 0.04, "lci": -0.65, "uci": 0.73, "k": 2, "n": 1329,
             "scope": "Faricimab 6 mg Q16W vs aflibercept Q8W in nAMD; BCVA change at 48 wk. Non-inferior, Lancet 2022;399:729-740."},
        ]}
    },
    "PEGCETACOPLAN_GA_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "OAKS + DERBY pegcetacoplan vs sham (GA lesion growth)", "citation": "Heier 2023", "year": 2023,
             "measure": "MD", "estimate": -0.34, "lci": -0.52, "uci": -0.16, "k": 2, "n": 1258,
             "scope": "Pegcetacoplan IVT monthly/every-other-month vs sham; GA lesion-area change at 24 mo (mm^2). Lancet 2023;402:1434-1448."},
        ]}
    },
    "FEZOLINETANT_VMS_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "SKYLIGHT 1+2 fezolinetant vs placebo (VMS frequency)", "citation": "Lederman 2023", "year": 2023,
             "measure": "MD", "estimate": -2.07, "lci": -2.57, "uci": -1.57, "k": 2, "n": 1022,
             "scope": "Fezolinetant 45 mg QD vs placebo in postmenopausal women with VMS; moderate-severe VMS frequency change (per day) at week 12. Lancet 2023;401:1091-1102."},
        ]}
    },
    "MAVACAMTEN_HCM_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "EXPLORER-HCM mavacamten vs placebo (composite response)", "citation": "Olivotto 2020", "year": 2020,
             "measure": "RR", "estimate": 2.08, "lci": 1.45, "uci": 3.00, "k": 1, "n": 251,
             "scope": "Mavacamten vs placebo in symptomatic obstructive HCM; composite of >=1.5 mL/kg/min pVO2 + >=1 NYHA class improvement OR >=3.0 mL/kg/min pVO2 at 30 wk. Lancet 2020;396:759-769."},
        ]}
    },
    "ROMOSOZUMAB_OP_REVIEW.html": {
        "outcomes": ["MACE"],
        "benchmarks": {"MACE": [
            {"label": "ARCH romo then alendronate vs alendronate (vertebral fx)", "citation": "Saag 2017", "year": 2017,
             "measure": "RR", "estimate": 0.52, "lci": 0.40, "uci": 0.66, "k": 1, "n": 4093,
             "scope": "Romosozumab 210 mg Q1M x 12 mo then alendronate vs alendronate alone; new vertebral fracture at 24 mo. NEJM 2017;377:1417-1427."},
            {"label": "FRAME romosozumab vs placebo (vertebral fx)", "citation": "Cosman 2016", "year": 2016,
             "measure": "RR", "estimate": 0.27, "lci": 0.16, "uci": 0.47, "k": 1, "n": 7180,
             "scope": "Romosozumab 210 mg Q1M vs placebo in postmenopausal osteoporosis; new vertebral fracture at 12 mo. NEJM 2016;375:1532-1543."},
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


def _escape(s):
    # escape apostrophes for JS single-quoted strings
    return s.replace(chr(39), chr(92)+chr(39))


def render_benchmark_block(benchmarks_by_key):
    lines = ["{"]
    for key, benchmarks in benchmarks_by_key.items():
        lines.append(f"            '{key}': [")
        for b in benchmarks:
            lines.append(
                "                { "
                f"label: '{_escape(b['label'])}', "
                f"citation: '{_escape(b['citation'])}', "
                f"year: {b['year']}, "
                f"measure: '{b['measure']}', "
                f"estimate: {b['estimate']}, "
                f"lci: {b['lci']}, "
                f"uci: {b['uci']}, "
                f"k: {b['k']}, "
                f"n: {b['n']}, "
                f"scope: '{_escape(b['scope'])}' "
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
    print(f"\nBatch J: {ok} OK / {fail} fail / {'dry-run' if args.dry_run else 'apply'}")
    if fail: sys.exit(1)


if __name__ == "__main__":
    main()
