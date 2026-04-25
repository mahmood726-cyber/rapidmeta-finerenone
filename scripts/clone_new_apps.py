#!/usr/bin/env python3
# sentinel:skip-file - developer tool; hardcoded ROOT is intentional
"""Clone a source RapidMeta app and substitute drug-specific data to create
new portfolio apps. Used for Tier-1 expansion (post-2015 pivotal-trial drugs).

Approach: byte-exact source-file copy + brace-balanced replacement of:
  1. <title>...</title>
  2. AUTO_INCLUDE_TRIAL_IDS Set declaration
  3. nctAcronyms object (inside RapidMeta literal)
  4. realData object (inside RapidMeta literal)
  5. PUBLISHED_META_BENCHMARKS const
  6. BENCHMARK_OUTCOME_MAP const

After cloning, re-run the existing fix scripts (fix_pico_boilerplate,
fix_boilerplate_full) plus propagate_*.py retrofits (peer-review,
qa-enhancer, reml, pro-detector) - they will pick up the new HTML files.

Source app should be semantically similar to target so structure +
benchmark-engine wiring transfer cleanly.
"""
import argparse, pathlib, re, shutil, sys

ROOT = pathlib.Path(r"C:\Projects\Finrenone")


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


def replace_object_literal(text: str, key_pattern: str, new_body: str) -> tuple:
    """Find `<key>: {...}` and replace the {...} portion with new_body.
    new_body should be the full new object including braces.
    Returns (new_text, success).
    """
    m = re.search(key_pattern, text)
    if not m:
        return text, False
    open_pos = text.find('{', m.end() - 1)
    if open_pos < 0:
        return text, False
    close_pos = find_balanced_close(text, open_pos)
    if close_pos < 0:
        return text, False
    new_text = text[:open_pos] + new_body + text[close_pos + 1:]
    return new_text, True


def replace_const_decl(text: str, const_name: str, new_body: str) -> tuple:
    pat = re.compile(rf"const\s+{re.escape(const_name)}\s*=\s*\{{")
    m = pat.search(text)
    if not m:
        return text, False
    open_pos = m.end() - 1
    close_pos = find_balanced_close(text, open_pos)
    if close_pos < 0:
        return text, False
    after = close_pos + 1
    while after < len(text) and text[after] in " \t":
        after += 1
    if after < len(text) and text[after] == ';':
        after += 1
    new_text = text[:m.start()] + f"const {const_name} = {new_body};" + text[after:]
    return new_text, True


def clone_app(source_path: pathlib.Path, target_path: pathlib.Path, spec: dict) -> str:
    if target_path.exists():
        return f"SKIP {target_path.name}: already exists"
    shutil.copy2(source_path, target_path)

    raw = target_path.read_bytes()
    crlf = b"\r\n" in raw
    text = raw.decode("utf-8")
    if crlf:
        text = text.replace("\r\n", "\n")

    # 1. Title
    text = re.sub(r"<title>[^<]*</title>", f"<title>{spec['title']}</title>", text, count=1)

    # 2. AUTO_INCLUDE_TRIAL_IDS
    auto = ", ".join(f"'{n}'" for n in spec["nct_ids"])
    text = re.sub(
        r"const AUTO_INCLUDE_TRIAL_IDS\s*=\s*new Set\(\[[^\]]*\]\);",
        f"const AUTO_INCLUDE_TRIAL_IDS = new Set([{auto}]);",
        text,
        count=1,
    )

    # 3. nctAcronyms object: replace inline
    acro = ", ".join(f"'{nct}': '{name}'" for nct, name in spec["acronyms"].items())
    text = re.sub(
        r"nctAcronyms:\s*\{[^}]*\}",
        f"nctAcronyms: {{ {acro} }}",
        text,
        count=1,
    )

    # 4. realData object - balanced replacement
    text, ok_data = replace_object_literal(
        text, r"realData:\s*\{", "{\n" + spec["realData_body"] + "\n            }"
    )
    if not ok_data:
        return f"FAIL {target_path.name}: realData not replaced"

    # 5. PUBLISHED_META_BENCHMARKS
    text, ok_b = replace_const_decl(text, "PUBLISHED_META_BENCHMARKS", spec["benchmarks_body"])
    if not ok_b:
        return f"FAIL {target_path.name}: PUBLISHED_META_BENCHMARKS not replaced"

    # 6. BENCHMARK_OUTCOME_MAP
    text, ok_m = replace_const_decl(text, "BENCHMARK_OUTCOME_MAP", spec["outcome_map_body"])
    if not ok_m:
        return f"FAIL {target_path.name}: BENCHMARK_OUTCOME_MAP not replaced"

    out = text.replace("\n", "\r\n") if crlf else text
    target_path.write_bytes(out.encode("utf-8"))
    return f"OK   {target_path.name}"


# ---------------------------------------------------------------------
# Tier 1 specs (4 apps in this batch - post-2015 pivotal drugs)
# ---------------------------------------------------------------------

def trial_entry(nct, name, pmid, year, tE, tN, cE, cN, hr, hr_lo, hr_hi,
                group, outcome_label, source_url, ctgov_url, snippet):
    return f"""                '{nct}': {{
                    name: '{name}', pmid: '{pmid}', phase: 'III', year: {year}, tE: {tE}, tN: {tN}, cE: {cE}, cN: {cN}, group: '{group}', publishedHR: {hr}, hrLCI: {hr_lo}, hrUCI: {hr_hi},
                    allOutcomes: [
                        {{ shortLabel: 'MACE', title: '{outcome_label}', tE: {tE}, cE: {cE}, type: 'PRIMARY', matchScore: 95, effect: {hr}, lci: {hr_lo}, uci: {hr_hi}, estimandType: 'RR' }}
                    ],
                    rob: ['low', 'low', 'low', 'low', 'low'],
                    snippet: '{snippet}',
                    sourceUrl: '{source_url}',
                    ctgovUrl: '{ctgov_url}',
                    evidence: []
                }}"""


def make_outcome_map(outcome_key):
    """Map all legacy outcome keys to the new app's primary outcome key."""
    legacy = ["default", "MACE", "ACH", "ACM", "Renal40", "Hyperkalemia", "HF_CV_First", "KidneyComp", "Renal57"]
    body = "{\n"
    for k in legacy:
        body += f"            {k}: '{outcome_key}',\n"
    body += f"            '{outcome_key}': '{outcome_key}'\n        }}"
    return body


SPECS = {

    # ============ RESMETIROM_MASH ============
    "RESMETIROM_MASH_REVIEW.html": {
        "source": "PBC_PPAR_REVIEW.html",
        "title": "RapidMeta Hepatology | Resmetirom (THR-β Agonist) in MASH/NASH v1.0",
        "nct_ids": ["NCT03900429"],
        "acronyms": {"NCT03900429": "MAESTRO-NASH"},
        "realData_body": trial_entry(
            "NCT03900429", "MAESTRO-NASH", "38231248", 2024, 84, 322, 31, 322, 2.71, 1.85, 3.96,
            "MASH F1B-F3, resmetirom 100 mg PO daily vs placebo (wk 52, NASH resolution + >=1-stage fibrosis improvement RR)",
            "NASH resolution at week 52 (primary, biopsy-confirmed, resmetirom 100 mg vs placebo, RR)",
            "https://www.nejm.org/doi/full/10.1056/NEJMoa2309000",
            "https://clinicaltrials.gov/study/NCT03900429",
            "Source: Harrison SA et al. NEJM 2024;390:497-509 (MAESTRO-NASH)."
        ),
        "benchmarks_body": """{
            'MASH_RESOLUTION': [
                { label: 'MAESTRO-NASH (resmetirom 100 mg pivotal)', citation: 'Harrison 2024', year: 2024, measure: 'RR', estimate: 2.71, lci: 1.85, uci: 3.96, k: 1, n: 644, scope: 'Resmetirom 100 mg vs placebo in MASH F1B-F3; NASH resolution + >=1-stage fibrosis improvement at wk 52. NEJM 2024;390:497-509.' }
            ]
        }""",
        "outcome_map_body": make_outcome_map("MASH_RESOLUTION"),
    },

    # ============ AFICAMTEN_HCM ============
    "AFICAMTEN_HCM_REVIEW.html": {
        "source": "MAVACAMTEN_HCM_REVIEW.html",
        "title": "RapidMeta Cardiology | Aficamten (Cardiac Myosin Inhibitor) in Obstructive HCM v1.0",
        "nct_ids": ["NCT05186818"],
        "acronyms": {"NCT05186818": "SEQUOIA-HCM"},
        "realData_body": trial_entry(
            "NCT05186818", "SEQUOIA-HCM", "38754167", 2024, 95, 139, 32, 143, 2.06, 1.45, 2.93,
            "Symptomatic obstructive HCM, aficamten 5-20 mg PO daily vs placebo (wk 24, composite functional response RR)",
            "Composite functional response at week 24 (primary; >=1.5 mL/kg/min pVO2 + NYHA class improvement OR >=3.0 mL/kg/min pVO2)",
            "https://www.nejm.org/doi/full/10.1056/NEJMoa2401231",
            "https://clinicaltrials.gov/study/NCT05186818",
            "Source: Maron MS et al. NEJM 2024;390:1849-1861 (SEQUOIA-HCM)."
        ),
        "benchmarks_body": """{
            'COMP_RESPONSE': [
                { label: 'SEQUOIA-HCM aficamten vs placebo', citation: 'Maron 2024', year: 2024, measure: 'RR', estimate: 2.06, lci: 1.45, uci: 2.93, k: 1, n: 282, scope: 'Aficamten vs placebo in obstructive HCM; composite functional response at wk 24. NEJM 2024;390:1849-1861.' },
                { label: 'EXPLORER-HCM mavacamten vs placebo', citation: 'Olivotto 2020', year: 2020, measure: 'RR', estimate: 2.08, lci: 1.45, uci: 3.00, k: 1, n: 251, scope: 'Mavacamten vs placebo in obstructive HCM; composite functional response at wk 30. Lancet 2020;396:759-769. (Class comparator)' }
            ]
        }""",
        "outcome_map_body": make_outcome_map("COMP_RESPONSE"),
    },

    # ============ ETRASIMOD_UC ============
    "ETRASIMOD_UC_REVIEW.html": {
        "source": "MIRIKIZUMAB_UC_REVIEW.html",
        "title": "RapidMeta GI | Etrasimod (S1P Modulator) in Moderate-Severe Ulcerative Colitis v1.0",
        "nct_ids": ["NCT03945188", "NCT03996369"],
        "acronyms": {"NCT03945188": "ELEVATE UC 52", "NCT03996369": "ELEVATE UC 12"},
        "realData_body": (
            trial_entry(
                "NCT03945188", "ELEVATE UC 52", "36871574", 2023, 78, 289, 10, 144, 3.89, 2.10, 7.20,
                "Moderate-severe UC, etrasimod 2 mg PO daily vs placebo (wk 12, clinical remission RR; ELEVATE UC 52)",
                "Clinical remission at week 12 (primary; ELEVATE UC 52 induction)",
                "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(23)00061-2/fulltext",
                "https://clinicaltrials.gov/study/NCT03945188",
                "Source: Sandborn WJ et al. Lancet 2023;401:1159-1171 (ELEVATE UC 52)."
            ) + ",\n" +
            trial_entry(
                "NCT03996369", "ELEVATE UC 12", "36871574", 2023, 60, 238, 17, 116, 1.72, 1.05, 2.83,
                "Moderate-severe UC, etrasimod 2 mg PO daily vs placebo (wk 12, clinical remission RR; ELEVATE UC 12)",
                "Clinical remission at week 12 (primary; ELEVATE UC 12 induction)",
                "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(23)00061-2/fulltext",
                "https://clinicaltrials.gov/study/NCT03996369",
                "Source: Sandborn WJ et al. Lancet 2023;401:1159-1171 (ELEVATE UC 12)."
            )
        ),
        "benchmarks_body": """{
            'REMISSION': [
                { label: 'Etrasimod ELEVATE UC pooled', citation: 'Sandborn 2023', year: 2023, measure: 'RR', estimate: 2.50, lci: 1.70, uci: 3.70, k: 2, n: 787, scope: 'Etrasimod 2 mg vs placebo induction in moderate-severe UC; clinical remission at wk 12. Lancet 2023;401:1159-1171.' },
                { label: 'JAKi UC NMA (upadacitinib)', citation: 'Danese 2022', year: 2022, measure: 'RR', estimate: 5.00, lci: 3.50, uci: 7.20, k: 2, n: 989, scope: 'Upadacitinib 45 mg vs placebo induction in moderate-severe UC; clinical remission at wk 8. Class comparator.' }
            ]
        }""",
        "outcome_map_body": make_outcome_map("REMISSION"),
    },

    # ============ VUTRISIRAN_ATTR ============
    "VUTRISIRAN_ATTR_REVIEW.html": {
        "source": "ATTR_CM_REVIEW.html",
        "title": "RapidMeta Cardiology | Vutrisiran (siRNA) in Transthyretin Amyloid Cardiomyopathy v1.0",
        "nct_ids": ["NCT04153149"],
        "acronyms": {"NCT04153149": "HELIOS-B"},
        "realData_body": trial_entry(
            "NCT04153149", "HELIOS-B", "39213189", 2024, 84, 326, 113, 329, 0.72, 0.56, 0.93,
            "ATTR-CM (wild-type or hereditary), vutrisiran 25 mg SC Q3M vs placebo (composite ACM + recurrent CV events HR)",
            "All-cause mortality and recurrent CV events through 36 months (primary, hierarchical composite, HR)",
            "https://www.nejm.org/doi/full/10.1056/NEJMoa2409134",
            "https://clinicaltrials.gov/study/NCT04153149",
            "Source: Fontana M et al. NEJM 2024;391:2349-2360 (HELIOS-B)."
        ),
        "benchmarks_body": """{
            'COMPOSITE_CV': [
                { label: 'HELIOS-B vutrisiran vs placebo', citation: 'Fontana 2024', year: 2024, measure: 'HR', estimate: 0.72, lci: 0.56, uci: 0.93, k: 1, n: 655, scope: 'Vutrisiran 25 mg SC Q3M vs placebo in ATTR-CM; composite ACM + recurrent CV events at 36 mo. NEJM 2024;391:2349-2360.' },
                { label: 'ATTR-ACT tafamidis vs placebo', citation: 'Maurer 2018', year: 2018, measure: 'HR', estimate: 0.70, lci: 0.51, uci: 0.96, k: 1, n: 441, scope: 'Tafamidis vs placebo in ATTR-CM; ACM at 30 mo. NEJM 2018;379:1007-1016. (Class comparator)' }
            ]
        }""",
        "outcome_map_body": make_outcome_map("COMPOSITE_CV"),
    },

}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run or args.apply):
        ap.error("pass --dry-run or --apply")

    ok = fail = skip = 0
    for target_name, spec in SPECS.items():
        source = ROOT / spec["source"]
        target = ROOT / target_name
        if not source.exists():
            print(f"FAIL {target_name}: source {spec['source']} missing")
            fail += 1
            continue
        if args.dry_run:
            print(f"WOULD CLONE {source.name} -> {target.name}")
            continue
        r = clone_app(source, target, spec)
        print(r)
        if r.startswith("OK"):
            ok += 1
        elif r.startswith("SKIP"):
            skip += 1
        else:
            fail += 1

    print(f"\n{'dry-run' if args.dry_run else 'apply'}: {ok} ok / {skip} skip / {fail} fail")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
