#!/usr/bin/env python
"""
Generate Living Meta-Analysis apps from the v13 master template.
Reads FINERENONE_REVIEW.html and replaces topic-specific sections.
"""
import re
import os
import json
import sys

TEMPLATE_PATH = r"C:\Projects\Finrenone\FINERENONE_REVIEW.html"

# ═══════════════════════════════════════════════════════════
# JS CODE BUILDERS
# ═══════════════════════════════════════════════════════════

def escape_js(s):
    """Escape a string for use inside JS single-quoted strings."""
    if s is None:
        return ''
    return str(s).replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "")


def js_val(v):
    """Convert a Python value to a JS literal."""
    if v is None:
        return 'null'
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, str):
        return f"'{escape_js(v)}'"
    if isinstance(v, list):
        return '[' + ', '.join(js_val(x) for x in v) + ']'
    if isinstance(v, dict):
        pairs = ', '.join(f'{k}: {js_val(v2)}' for k, v2 in v.items())
        return '{ ' + pairs + ' }'
    return str(v)


def build_evidence_js(evidence_list):
    """Build JS array literal for an evidence[] array."""
    if not evidence_list:
        return '[]'
    entries = []
    for ev in evidence_list:
        parts = []
        parts.append(f"label: {js_val(ev.get('label'))}")
        parts.append(f"source: {js_val(ev.get('source'))}")
        parts.append(f"text: {js_val(ev.get('text'))}")
        if ev.get('highlights'):
            parts.append(f"highlights: {js_val(ev['highlights'])}")
        if ev.get('sourceUrl'):
            parts.append(f"sourceUrl: {js_val(ev['sourceUrl'])}")
        if ev.get('fullText'):
            parts.append(f"fullText: {js_val(ev['fullText'])}")
        entries.append('{ ' + ', '.join(parts) + ' }')
    return '[\n                        ' + ',\n                        '.join(entries) + '\n                    ]'


def build_outcomes_js(outcomes):
    """Build JS array for allOutcomes."""
    if not outcomes:
        return 'null'
    entries = []
    for o in outcomes:
        parts = [f"shortLabel: {js_val(o.get('shortLabel'))}",
                 f"title: {js_val(o.get('title'))}"]
        if o.get('tE') is not None:
            parts.append(f"tE: {o['tE']}")
        if o.get('cE') is not None:
            parts.append(f"cE: {o['cE']}")
        parts.append(f"type: {js_val(o.get('type', 'PRIMARY'))}")
        if o.get('pubHR') is not None:
            parts.extend([f"pubHR: {o['pubHR']}", f"pubHR_LCI: {o.get('pubHR_LCI')}", f"pubHR_UCI: {o.get('pubHR_UCI')}"])
        entries.append('{ ' + ', '.join(parts) + ' }')
    return '[\n                        ' + ',\n                        '.join(entries) + '\n                    ]'


def build_trial_js(nct_id, trial):
    """Build JS object literal for a single trial in realData."""
    lines = []
    lines.append(f"                '{nct_id}': {{")
    lines.append(f"                    name: {js_val(trial['name'])}, phase: {js_val(trial.get('phase', 'III'))}, year: {trial.get('year', 2024)},")
    lines.append(f"                    tE: {trial.get('tE', 0)}, tN: {trial.get('tN', 0)}, cE: {trial.get('cE', 0)}, cN: {trial.get('cN', 0)}, group: {js_val(trial.get('group', '--'))},")
    if trial.get('publishedHR') is not None:
        lines.append(f"                    publishedHR: {trial['publishedHR']}, hrLCI: {trial.get('hrLCI')}, hrUCI: {trial.get('hrUCI')},")
    if trial.get('allOutcomes'):
        lines.append(f"                    allOutcomes: {build_outcomes_js(trial['allOutcomes'])},")
    lines.append(f"                    rob: {js_val(trial.get('rob', ['low','low','low','low','low']))},")
    lines.append(f"                    snippet: {js_val(trial.get('snippet', ''))},")
    if trial.get('sourceUrl'):
        lines.append(f"                    sourceUrl: {js_val(trial['sourceUrl'])},")
    lines.append(f"                    evidence: {build_evidence_js(trial.get('evidence', []))}")
    lines.append(f"                }}")
    return '\n'.join(lines)


def build_real_data_js(trials_dict):
    """Build the full realData JS object."""
    trial_blocks = []
    for nct_id, trial in trials_dict.items():
        trial_blocks.append(build_trial_js(nct_id, trial))
    return '{\n' + ',\n'.join(trial_blocks) + '\n            }'


# ═══════════════════════════════════════════════════════════
# TEMPLATE TRANSFORMATION
# ═══════════════════════════════════════════════════════════

def transform_template(template_html, cfg):
    """Apply all replacements to produce a topic-specific app."""
    html = template_html
    storage = cfg["storage_key"]
    proto = cfg["protocol"]

    # 1. Title
    html = re.sub(
        r'<title>.*?</title>',
        f'<title>RapidMeta Cardiology | {cfg["title_short"]} v13.0</title>',
        html
    )

    # 2. Header h1 — replace the full header span
    html = re.sub(
        r'Finerenone Ultra-Precision',
        cfg["title_short"],
        html
    )

    # 3. Review title in protocol table
    html = re.sub(
        r'Finerenone for .*?: A Living Systematic Review.*?Trials',
        cfg["title_long"],
        html,
        count=1
    )

    # 4. Protocol state defaults
    html = re.sub(
        r"protocol: \{ pop: '.*?', int: '.*?', comp: '.*?', out: '.*?', subgroup: '.*?'",
        f"protocol: {{ pop: '{escape_js(proto['pop'])}', int: '{escape_js(proto['int'])}', comp: '{escape_js(proto['comp'])}', out: '{escape_js(proto['out'])}', subgroup: '{escape_js(proto.get('subgroup', '--'))}'",
        html,
        count=1
    )

    # 5. PICO table inputs (value= attributes in protocol form)
    pico_replacements = [
        (r'value="Heart Failure or CKD[^"]*"', f'value="{proto["pop"]}"'),
        (r'value="Finerenone[^"]*"', f'value="{proto["int"]}"'),
        (r'value="Placebo[^"]*"', f'value="{proto["comp"]}"'),
        (r'value="MACE Composite[^"]*"', f'value="{proto["out"]}"'),
    ]
    for pattern, replacement in pico_replacements:
        html = re.sub(pattern, replacement, html, count=1)

    # 6. localStorage keys — replace finerenone-specific keys
    for ver in ['v13_0', 'v12_0', 'v11_0', 'v10_0', 'v9_3']:
        html = html.replace(f"rapid_meta_finerenone_{ver}", f"rapid_meta_{storage}_{ver}")
    html = html.replace("rapid_meta_finerenone_theme", f"rapid_meta_{storage}_theme")

    # 7. realData block
    real_data_js = build_real_data_js(cfg["trials"])
    html = re.sub(
        r'realData:\s*\{.*?\n            \},',
        f'realData: {real_data_js},',
        html,
        count=1,
        flags=re.DOTALL
    )

    # 8. AUTO_INCLUDE_TRIAL_IDS
    ids_str = ', '.join(f"'{nct}'" for nct in cfg["auto_include_ids"])
    html = re.sub(
        r"const AUTO_INCLUDE_TRIAL_IDS = new Set\(\[.*?\]\);",
        f"const AUTO_INCLUDE_TRIAL_IDS = new Set([{ids_str}]);",
        html
    )

    # 9. nctAcronyms
    acronyms_pairs = ', '.join(f"'{k}': '{v}'" for k, v in cfg.get("nct_acronyms", {}).items())
    html = re.sub(
        r"nctAcronyms:\s*\{[^}]*\}",
        f"nctAcronyms: {{ {acronyms_pairs} }}",
        html,
        count=1
    )

    # 10. Search queries — CT.gov API URL
    search_term = cfg.get("search_term_ctgov", cfg.get("search_term", ""))
    html = re.sub(
        r"query\.intr=finerenone",
        f"query.intr={search_term.replace(' ', '+')}",
        html
    )
    # PubMed query in protocol display
    if cfg.get("search_term_pubmed"):
        html = re.sub(
            r'finerenone\[tiab\]',
            cfg["search_term_pubmed"],
            html,
            count=1
        )

    # 11. Visual abstract heading — matches all known template variants
    html = re.sub(
        r'Finerenone in (?:CKD|Heart Failure|Cardiorenal Disease|Cardio-Kidney-Metabolic Disease)',
        cfg.get("va_heading", cfg["title_short"]),
        html,
        count=2
    )

    # 12. Drug name references in protocol tables
    drug_lower = cfg.get("drug_name_lower", cfg["title_short"].lower())
    html = re.sub(r'\bfinerenone\b(?!_)', drug_lower, html, flags=re.IGNORECASE, count=0)
    # But restore finerenone in localStorage keys (they use underscore)
    html = html.replace(f"rapid_meta_{drug_lower.replace(' ', '_')}_{storage}", f"rapid_meta_{storage}")

    # 12b. Replace finerenone_ prefix in download filenames (not caught by word-boundary above)
    slug = drug_lower.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_')
    # Catches both finerenone_word (JS concat prefix) and 'finerenone_' (quoted standalone filename part)
    html = re.sub(r"finerenone_(?=[\w'])", f"{slug}_", html, flags=re.IGNORECASE)
    # Catches _finerenone suffix in download filenames (e.g. prisma_2020_checklist_finerenone.csv)
    html = re.sub(r"_finerenone(?=[.'\"])", f"_{slug}", html, flags=re.IGNORECASE)

    # 13. Effect measure defaults
    em = cfg.get("effect_measure", "AUTO")
    if em != "AUTO":
        html = re.sub(
            r"effectMeasure: 'AUTO'",
            f"effectMeasure: '{em}'",
            html,
            count=1
        )

    return html


# ═══════════════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════════════

def validate_html(html, filename, cfg):
    """Run structural validation checks on generated HTML."""
    errors = []

    # Div balance (template has pre-existing ±1 imbalance; flag only if delta > 1)
    opens = len(re.findall(r'<div[\s>]', html))
    closes = html.count('</div>')
    if abs(opens - closes) > 1:
        errors.append(f"Div imbalance: {opens} opens vs {closes} closes")

    # Script integrity — skip external <script src=...> tags (false positive)
    # Only flag literal </script> that appears inside an inline script block
    in_script = False
    for line_num, line in enumerate(html.split('\n'), 1):
        stripped = line.strip()
        if re.search(r'<script\b[^>]*src=', stripped):
            # External script — open and close on same line, skip
            continue
        if re.search(r'<script\b', stripped):
            in_script = True
        if in_script and re.search(r'</script>', stripped):
            if re.search(r'<script\b', stripped):
                # open + close on same line (e.g. external) — ignore
                in_script = False
            elif re.search(r"['\"`].*</script>", stripped) or re.search(r'</script>.*[\'"`]', stripped):
                # Inside a string literal — this is the real bug to flag
                errors.append(f"Line {line_num}: literal </script> inside script block string")
            else:
                in_script = False

    # Dangling finerenone references (but allow in code comments and JS regex patterns)
    finerenone_refs = [(i+1, line.strip()) for i, line in enumerate(html.split('\n'))
                       if 'finerenone' in line.lower()
                       and not line.strip().startswith('//')
                       and not line.strip().startswith('*')
                       and 'v12.0:' not in line
                       and 'v13.0:' not in line
                       and 'localStorage' not in line
                       and '_migrated' not in line]
    if finerenone_refs and cfg["storage_key"] != "finerenone":
        # Exclude: JS regex patterns (/\bfinerenone\b/), href CSS links, evidence/source lines
        def _is_acceptable_ref(line_text):
            t = line_text.lower()
            if 'evidence' in t or 'source' in t:
                return True
            if re.search(r'/\\b?finerenone\\b?/', line_text):  # JS regex literal
                return True
            if '.tailwind.css' in line_text or '.css' in line_text:  # CSS link
                return True
            return False
        code_refs = [r for r in finerenone_refs if not _is_acceptable_ref(r[1])]
        if len(code_refs) > 5:
            errors.append(f"{len(code_refs)} potential dangling 'finerenone' refs in non-evidence code")

    # localStorage key present
    if f"rapid_meta_{cfg['storage_key']}_v13_0" not in html:
        errors.append(f"localStorage key rapid_meta_{cfg['storage_key']}_v13_0 not found")

    return errors


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def generate_app(cfg, output_dir=None):
    """Generate a single app from config."""
    print(f"\n{'='*60}")
    print(f"Generating: {cfg['filename']}")
    print(f"{'='*60}")

    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        template = f.read()

    html = transform_template(template, cfg)
    errors = validate_html(html, cfg['filename'], cfg)

    if errors:
        print(f"  VALIDATION ERRORS:")
        for e in errors:
            print(f"    - {e}")
    else:
        print(f"  Validation: PASS")

    out_dir = output_dir or os.path.dirname(TEMPLATE_PATH)
    out_path = os.path.join(out_dir, cfg['filename'])
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  Written: {out_path} ({len(html.splitlines())} lines)")
    return errors


# ═══════════════════════════════════════════════════════════
# APP DEFINITIONS (populated in Tasks 2-4)
# ═══════════════════════════════════════════════════════════

APPS = [
    {
        "filename": "PFA_AF_REVIEW.html",
        "output_dir": r"C:\Projects\PFA_AF_LivingMeta",
        "title_short": "PFA in Atrial Fibrillation",
        "title_long": "Pulsed Field Ablation for Atrial Fibrillation: A Living Systematic Review and Meta-Analysis of Randomized Controlled Trials",
        "drug_name_lower": "pulsed field ablation",
        "va_heading": "Pulsed Field Ablation in Atrial Fibrillation",
        "storage_key": "pfa_af",
        "protocol": {
            "pop": "Adults with paroxysmal or persistent AF",
            "int": "Pulsed Field Ablation (any system)",
            "comp": "Thermal Ablation (RF or Cryoballoon)",
            "out": "Freedom from atrial arrhythmia at 12 months",
            "subgroup": "Comparator type (RF vs Cryo vs Mixed)",
        },
        "search_term_ctgov": "pulsed+field+ablation",
        "search_term_pubmed": "pulsed field ablation[tiab]",
        "effect_measure": "RR",
        "nct_acronyms": {
            "NCT04612244": "ADVENT",
            "NCT05534581": "CHAMPION",
            "NCT04198701": "PULSED AF",
        },
        "auto_include_ids": ["NCT04612244", "NCT05534581", "NCT04198701"],
        "trials": {
            "NCT04612244": {
                "name": "ADVENT", "phase": "III", "year": 2023,
                "tE": 204, "tN": 305, "cE": 194, "cN": 302,
                "tT": 106, "cT": 123, "tT_sd": 35, "cT_sd": 38,
                "tP": 0, "cP": 2,
                "group": "Mixed (RF/Cryo)",
                "rob": ["low", "low", "low", "some", "low"],
                "snippet": "Reddy et al., NEJM 2023; 389:1660-1671.",
                "evidence": [
                    {
                        "label": "Enrollment & Randomization",
                        "source": "Reddy et al. NEJM 2023;389:1660-1671, Fig 1",
                        "text": "607 patients randomized: 305 PFA (Farapulse) and 302 thermal ablation (RF or cryoballoon at investigator discretion).",
                        "highlights": ["305", "302", "607"],
                    },
                    {
                        "label": "Primary Efficacy (12-month)",
                        "source": "Reddy et al. NEJM 2023;389:1660-1671, Table 2",
                        "text": "Freedom from atrial arrhythmia recurrence at 12 months: 204/305 (66.9%) PFA vs 194/302 (64.2%) thermal. Non-inferior (P<0.001 for non-inferiority).",
                        "highlights": ["204", "305", "66.9%", "194", "302", "64.2%"],
                    },
                    {
                        "label": "Phrenic Nerve Palsy",
                        "source": "Reddy et al. NEJM 2023;389:1660-1671, Safety",
                        "text": "Persistent phrenic nerve palsy: 0 PFA vs 2 cryoballoon (both resolved by 12 months).",
                        "highlights": ["0", "2"],
                    },
                ],
            },
            "NCT05534581": {
                "name": "CHAMPION", "phase": "III", "year": 2025,
                "tE": 66, "tN": 105, "cE": 52, "cN": 105,
                "tT": 55, "cT": 73, "tT_sd": 20, "cT_sd": 25,
                "tP": None, "cP": None,
                "group": "Cryo",
                "rob": ["low", "low", "low", "low", "low"],
                "snippet": "Kueffer et al., NEJM 2025.",
                "evidence": [
                    {
                        "label": "Enrollment & Randomization",
                        "source": "Kueffer et al. NEJM 2025",
                        "text": "210 patients randomized 1:1: 105 PFA vs 105 cryoballoon ablation for paroxysmal AF.",
                        "highlights": ["105", "105", "210"],
                    },
                    {
                        "label": "Primary Efficacy",
                        "source": "Kueffer et al. NEJM 2025",
                        "text": "Freedom from atrial arrhythmia: 66/105 (62.9%) PFA vs 52/105 (49.5%) cryo. Superior (P=0.047).",
                        "highlights": ["66", "105", "62.9%", "52", "49.5%"],
                    },
                ],
            },
            "NCT04198701": {
                "name": "PULSED AF", "phase": "III", "year": 2024,
                "tE": 172, "tN": 226, "cE": 60, "cN": 74,
                "tT": 64, "cT": 80, "tT_sd": 30, "cT_sd": 35,
                "tP": 0, "cP": 1,
                "group": "Mixed (RF/Cryo)",
                "rob": ["low", "low", "low", "some", "low"],
                "snippet": "Reddy et al., Lancet 2024. VERIFY ALL NUMBERS. N=300 (226 PFA + 74 non-randomized thermal). SDs estimated.",
                "evidence": [
                    {
                        "label": "Design Note",
                        "source": "NCT04198701 (ClinicalTrials.gov)",
                        "text": "Non-randomized comparison arm. PFA arm: 226 patients. Drug/device: Medtronic PulseSelect PFA. VERIFY: exact event counts, procedure times, and PNP from published manuscript.",
                        "highlights": ["226", "VERIFY"],
                    },
                ],
            },
        },
    },
    # ─── Task 3: Watchman FLX vs Amulet LAAO ───────────────────
    {
        "filename": "WATCHMAN_AMULET_REVIEW.html",
        "output_dir": r"C:\Projects\LivingMeta_Watchman_Amulet",
        "title_short": "Watchman FLX vs Amulet LAAO",
        "title_long": "Left Atrial Appendage Occlusion — Watchman FLX vs Amulet: A Living Systematic Review and Meta-Analysis",
        "drug_name_lower": "left atrial appendage occlusion",
        "va_heading": "LAAO Device Comparison: Watchman vs Amulet",
        "storage_key": "laao_watchman_amulet",
        "protocol": {
            "pop": "Adults with non-valvular AF and contraindication to OAC",
            "int": "Amplatzer Amulet",
            "comp": "Watchman FLX (or Watchman 2.5)",
            "out": "Ischemic Stroke or Systemic Embolism",
            "subgroup": "Comparator generation (FLX vs W2.5), Follow-up duration",
        },
        "search_term_ctgov": "left+atrial+appendage+AND+(Watchman+OR+Amulet)",
        "search_term_pubmed": "(left atrial appendage closure[tiab]) AND (Watchman OR Amulet)[tiab]",
        "effect_measure": "RR",
        "nct_acronyms": {"NCT02879448": "AMULET IDE", "NCT03392428": "SWISS-APERO"},
        "auto_include_ids": ["NCT02879448", "NCT03392428"],
        "trials": {
            # ── Active RCTs (poolable) ───────────────────────────────
            "NCT02879448": {
                # Primary outcome (stroke/SE): flat tE/tN/cE/cN from nested stroke{}
                "name": "AMULET IDE", "phase": "Pivotal RCT", "year": 2021,
                "tE": 26, "tN": 934, "cE": 26, "cN": 944,
                "group": "Indirect (vs W2.5)",
                "rob": ["low", "low", "some", "some", "some"],
                "snippet": "Lakkireddy Circulation 2021;144:e64-e74. Amulet vs Watchman 2.5 (NOT FLX). Ischemic stroke/SE ~2.8% both arms at 18m. Open-label design.",
                "allOutcomes": [
                    {
                        "shortLabel": "Stroke/SE",
                        "title": "Ischemic Stroke or Systemic Embolism at 18 months",
                        "tE": 26, "cE": 26,
                        "type": "PRIMARY",
                    },
                    {
                        "shortLabel": "Safety composite",
                        "title": "Primary safety composite (complications + death + BARC 3+ bleeding) at 12m",
                        "tE": 99, "cE": 94,
                        "type": "SECONDARY",
                    },
                ],
                "evidence": [
                    {
                        "label": "Enrollment & Design",
                        "source": "Lakkireddy D et al. Circulation 2021;144:e64-e74, Fig 1 (CONSORT)",
                        "text": "A total of 1,878 patients with non-valvular AF and contraindication to long-term OAC were randomized 1:1 to Amplatzer Amulet (n=934) or Watchman 2.5 (n=944). Open-label, non-inferiority design with blinded endpoint adjudication.",
                        "highlights": ["934", "944", "1,878", "non-inferiority", "blinded endpoint"],
                    },
                    {
                        "label": "Ischemic Stroke/SE at 18 Months",
                        "source": "Lakkireddy D et al. Circulation 2021;144:e64-e74, Table 2",
                        "text": "Ischemic stroke or systemic embolism occurred in 26 of 934 patients (2.8%) in the Amulet group and 26 of 944 patients (2.8%) in the Watchman 2.5 group at 18-month follow-up (risk difference 0.0%, 95% CrI -1.2 to 1.3).",
                        "highlights": ["26", "934", "2.8%", "944"],
                    },
                    {
                        "label": "5-Year Extended Follow-up",
                        "source": "Lakkireddy D et al. ACC 2024 Late-Breaking",
                        "text": "At 5-year follow-up: Fatal/disabling stroke: Amulet 22 events vs Watchman 39 events. Device-related thrombus: 3 vs 6. Peridevice leak >=3mm: 4 (Amulet) vs 18 (Watchman). Long-term Amulet advantage in sealing and DRT.",
                        "highlights": ["22 events", "39 events", "3 vs 6", "4 vs 18"],
                    },
                    {
                        "label": "Procedural Safety (12-Month)",
                        "source": "Lakkireddy D et al. Circulation 2021;144:e64-e74",
                        "text": "Primary safety composite (procedure complications + death + BARC 3+ bleeding) at 12m: Amulet 14.5% (136/934) vs Watchman 14.7% (139/944). Procedure-related complications: 4.5% vs 2.5%. DRT: 3.3% vs 4.5%. Peridevice leak >5mm: 10% vs 22%.",
                        "highlights": ["14.5%", "14.7%", "4.5%", "2.5%", "10%", "22%"],
                    },
                    {
                        "label": "Indirectness Concern",
                        "source": "Protocol: NCT02879448 (ClinicalTrials.gov)",
                        "text": "CRITICAL: Comparator is Watchman 2.5 (legacy device), NOT Watchman FLX. GRADE assessment must downgrade for indirectness when pooling with FLX-era trials. Open-label design introduces performance bias risk (D3/D4 some concerns).",
                        "highlights": ["Watchman 2.5", "NOT Watchman FLX", "indirectness", "Open-label"],
                    },
                ],
            },
            "NCT03392428": {
                # Primary outcome (composite CV death/stroke/TIA/SE): flat from nested stroke{}
                "name": "SWISS-APERO 3yr", "phase": "RCT", "year": 2025,
                "tE": 20, "tN": 111, "cE": 34, "cN": 110,
                "group": "Direct (vs FLX/W2.5 mix)",
                "rob": ["low", "low", "low", "some", "low"],
                "snippet": "Branca JACC 2025. 3yr follow-up (n=221). Watchman arm: 77% FLX + 23% W2.5. Composite CV death/stroke/TIA/SE: 18.2% vs 31.0%.",
                "allOutcomes": [
                    {
                        "shortLabel": "Composite CV",
                        "title": "CV death/stroke/TIA/SE at 3 years (primary composite)",
                        "tE": 20, "cE": 34,
                        "type": "PRIMARY",
                    },
                    {
                        "shortLabel": "Major bleeding",
                        "title": "Major bleeding (BARC 3-5) at 3 years",
                        "tE": 18, "cE": 20,
                        "type": "SECONDARY",
                    },
                ],
                "evidence": [
                    {
                        "label": "Enrollment & Follow-up",
                        "source": "Branca P et al. JACC 2025, Table 1",
                        "text": "A total of 221 patients were randomized: 111 to Amulet and 110 to Watchman (77% FLX, 23% W2.5 legacy). Extended 3-year follow-up of the original SWISS-APERO RCT. Blinded outcome adjudication by independent committee.",
                        "highlights": ["221", "111", "110", "77% FLX", "23% W2.5", "3-year"],
                    },
                    {
                        "label": "Primary Composite at 3 Years",
                        "source": "Branca P et al. JACC 2025, Table 2",
                        "text": "The primary composite endpoint (cardiovascular death, stroke, TIA, or systemic embolism) occurred in 20 of 111 patients (18.2%) with Amulet and 34 of 110 patients (31.0%) with Watchman at 3-year follow-up. CV death: 12.1% Amulet vs 23.7% Watchman (HR 0.50). Major bleeding (BARC 3-5): 16.5% vs 18.0% (HR 1.03, NS).",
                        "highlights": ["20", "111", "18.2%", "34", "110", "31.0%", "12.1%", "23.7%"],
                    },
                    {
                        "label": "45-Day Procedural Safety",
                        "source": "Galea R et al. Circulation 2022;145:724-738, Table 3",
                        "text": "Major procedure-related complications: Amulet 9.0% (10/111) vs Watchman 2.7% (3/110). Procedural bleeding: 7.2% (8/111) vs 1.8% (2/110). CV death/stroke/SE at 45d: 2.7% (3/111) vs 4.5% (5/110). DRT: definite 0.9% (1) vs 3.0% (3); definite+probable 3.7% (4) vs 9.9% (11).",
                        "highlights": ["9.0%", "2.7%", "7.2%", "1.8%", "3.7%", "9.9%"],
                    },
                    {
                        "label": "RoB Assessment",
                        "source": "Study protocol: NCT03392428 (ClinicalTrials.gov)",
                        "text": "Multicenter RCT with adequate randomization (D1 low). Some concerns for D4 (measurement) due to open-label design, though endpoints adjudicated by blinded committee. Mixed comparator arm (FLX+W2.5) introduces partial indirectness.",
                        "highlights": ["randomization", "open-label", "blinded committee"],
                    },
                ],
            },
            # ── Single-arm / registry (not poolable — tE/tN/cE/cN = 0) ──
            "NCT02702271": {
                "name": "PINNACLE FLX", "phase": "Single-arm", "year": 2023,
                "tE": 0, "tN": 0, "cE": 0, "cN": 0,
                "group": "Reference (FLX only)",
                "rob": ["low", "low", "low", "some", "some"],
                "snippet": "Kar S et al. JAHA 2023. Watchman FLX single-arm IDE study (n=400). 2yr: stroke 3.4%, major bleeding 10.1%, mortality 9.3%. Not poolable (no comparator).",
                "evidence": [
                    {
                        "label": "2-Year Outcomes",
                        "source": "Kar S et al. J Am Heart Assoc 2023;12:e026295, Table 2",
                        "text": "Among 395 implanted patients (mean age 74, 36% women, CHA2DS2-VASc 4.2), 2-year ischemic stroke/SE rate was 3.4% (annualized 1.7%; upper 95% CI 5.3%, superior to 8.7% performance goal). All stroke: 5.5%. Major bleeding (BARC 3/5): 10.1%. All-cause mortality: 9.3%. CV death: 5.5%.",
                        "highlights": ["395", "3.4%", "1.7%", "10.1%", "9.3%"],
                    },
                    {
                        "label": "Procedural Success",
                        "source": "Kar S et al. J Am Heart Assoc 2023;12:e026295",
                        "text": "Procedural success 100% (400/400). Device closure (leak <=5mm) at 12 months: 100%. No device embolizations. Zero symptomatic DRT after 1 year. Effective seal maintained through 2 years.",
                        "highlights": ["100%", "400/400", "Zero"],
                    },
                    {
                        "label": "Note: Single-Arm Design",
                        "source": "Protocol: NCT02702271",
                        "text": "PINNACLE FLX is a single-arm study of Watchman FLX without a comparator device. Data cannot be pooled in head-to-head meta-analysis but provides important FLX-specific safety benchmarks. Enrolled at 29 US sites 2018-2020.",
                        "highlights": ["single-arm", "cannot be pooled", "safety benchmarks"],
                    },
                ],
            },
            "NCT02447081": {
                "name": "Amulet Observational", "phase": "Registry", "year": 2019,
                "tE": 0, "tN": 0, "cE": 0, "cN": 0,
                "group": "Reference (Amulet only)",
                "rob": ["some", "some", "low", "some", "some"],
                "snippet": "Landmesser U et al. Eur Heart J 2020;41:2894. Amulet post-market registry (n=1088). Procedural success 99.0%. Annualized stroke 2.4%, major bleeding 6.3%.",
                "evidence": [
                    {
                        "label": "Registry Population",
                        "source": "Landmesser U et al. Eur Heart J 2020;41:2894-2905",
                        "text": "Prospective post-market registry at 51 sites. 1088 patients enrolled (mean age 75, CHA2DS2-VASc 4.2, HAS-BLED 3.3). 72% contraindicated for OAC. Procedural success 99.0% (1077/1088). Median follow-up 1.8 years.",
                        "highlights": ["1088", "51 sites", "99.0%", "1077"],
                    },
                    {
                        "label": "Clinical Outcomes",
                        "source": "Landmesser U et al. Eur Heart J 2020;41:2894-2905, Table 3",
                        "text": "Annualized ischemic stroke rate 2.4%, major bleeding 6.3%, all-cause mortality 8.4%. Pericardial effusion requiring intervention 1.2%. Device-related thrombus 1.6%. Annualized SE 0.2%.",
                        "highlights": ["2.4%", "6.3%", "8.4%", "1.6%"],
                    },
                    {
                        "label": "Note: Single-Arm Design",
                        "source": "Protocol: NCT02447081",
                        "text": "Post-market observational study of the Amulet device without a comparator arm. Data cannot be pooled in head-to-head meta-analysis but provides Amulet-specific safety and efficacy benchmarks in a real-world population.",
                        "highlights": ["single-arm", "cannot be pooled", "real-world"],
                    },
                ],
            },
            # ── Pipeline trials (no results yet — tE/tN/cE/cN = 0) ──────
            "NCT04676880": {
                "name": "COMPARE-LAAO", "phase": "RCT (Pipeline)", "year": 2026,
                "tE": 0, "tN": 0, "cE": 0, "cN": 0,
                "group": "Pipeline (LAAO vs usual care)",
                "rob": ["low", "low", "low", "low", "low"],
                "snippet": "Dutch multicenter RCT (n=609). LAAO (Watchman FLX or Amulet) vs usual care in AF patients unable to use OAC. Primary completion May 2026. No results yet.",
                "evidence": [
                    {
                        "label": "Trial Design",
                        "source": "ClinicalTrials.gov NCT04676880, Protocol v1.4",
                        "text": "Multicenter RCT across 14 Dutch centers. 609 patients with non-valvular AF and CHA2DS2-VASc >=2 who are unsuitable for long-term OAC. Randomized to LAAO (Watchman FLX or Amulet, operator choice) vs usual care (antiplatelet or nothing). Primary: time to first stroke.",
                        "highlights": ["609", "14 Dutch centers", "Watchman FLX or Amulet", "May 2026"],
                    },
                    {
                        "label": "Significance for Living MA",
                        "source": "Protocol analysis",
                        "text": "COMPARE-LAAO will provide the first RCT evidence for LAAO vs usual care in OAC-ineligible patients. While not a direct Amulet vs FLX comparison, the mixed device arm will contribute real-world comparative effectiveness data. Expected primary completion May 2026.",
                        "highlights": ["first RCT", "OAC-ineligible", "May 2026"],
                    },
                ],
            },
            "NCT06706688": {
                "name": "VERITAS (Amulet 2)", "phase": "Post-market", "year": 2025,
                "tE": 0, "tN": 0, "cE": 0, "cN": 0,
                "group": "Pipeline (Amulet 2)",
                "rob": ["low", "low", "low", "low", "low"],
                "snippet": "Abbott Amulet 2 LAA Occluder post-market study (n=458). Next-gen device with improved delivery system. Active, not yet recruiting results. 35 sites.",
                "evidence": [
                    {
                        "label": "Next-Generation Device",
                        "source": "ClinicalTrials.gov NCT06706688",
                        "text": "Evaluates the Amulet 2 LAA Occluder, the next-generation Amulet device with improved deliverability and seal. 458 patients across 35 international sites. Primary completion November 2025. Results will inform future head-to-head comparisons with Watchman FLX Pro.",
                        "highlights": ["Amulet 2", "458 patients", "35 sites", "November 2025"],
                    },
                ],
            },
        },
    },
    # ─── Task 4: Tricuspid TEER ─────────────────────────────────
    {
        "filename": "TRICUSPID_TEER_REVIEW.html",
        "output_dir": r"C:\Projects\Tricuspid_TEER_LivingMeta",
        "title_short": "Tricuspid TEER",
        "title_long": "Transcatheter Edge-to-Edge Repair for Tricuspid Regurgitation: A Living Systematic Review and Meta-Analysis",
        "drug_name_lower": "transcatheter tricuspid repair",
        "va_heading": "Tricuspid TEER for Severe TR",
        "storage_key": "tricuspid_teer",
        "protocol": {
            "pop": "Adults with severe tricuspid regurgitation",
            "int": "Transcatheter Edge-to-Edge Repair (TriClip or PASCAL)",
            "comp": "Medical Therapy",
            "out": "TR reduction to moderate or less at 12 months",
            "subgroup": "Device (TriClip vs PASCAL), TR severity at baseline",
        },
        "search_term_ctgov": "triclip+OR+PASCAL+AND+tricuspid+regurgitation",
        "search_term_pubmed": "(triclip[tiab] OR PASCAL tricuspid[tiab]) AND repair[tiab]",
        "effect_measure": "RR",
        "nct_acronyms": {"NCT04221490": "TRILUMINATE", "NCT04097145": "CLASP TR"},
        "auto_include_ids": ["NCT04221490"],
        "trials": {
            # ── RCT (poolable) ─────────────────────────────────────────
            "NCT04221490": {
                "name": "TRILUMINATE Pivotal", "phase": "III", "year": 2023,
                # Sorajja P et al. NEJM 2023;389:1938-1950
                # TEER arm: 152/175 achieved TR ≤2+; Control arm: ~8/175 (4.8%)
                "tE": 152, "tN": 175, "cE": 8, "cN": 175,
                "group": "TriClip vs Medical Therapy",
                "rob": ["low", "low", "some", "low", "low"],
                "snippet": "Sorajja P et al. NEJM 2023;389:1938-1950. RCT (n=350). TEER 87.0% vs Control 4.8% TR reduction at 12m.",
                "sourceUrl": "https://www.nejm.org/doi/10.1056/NEJMoa2300525",
                "evidence": [
                    {
                        "label": "Enrollment & Randomization",
                        "source": "Sorajja P et al. NEJM 2023;389:1938-1950, Fig 1 (CONSORT)",
                        "text": "A total of 350 patients were enrolled; 175 were randomized to transcatheter tricuspid-valve repair with the TriClip device and 175 to medical therapy alone.",
                        "highlights": ["350", "175", "175", "TriClip"],
                    },
                    {
                        "label": "Primary Outcome (TR Reduction)",
                        "source": "Sorajja P et al. NEJM 2023;389:1938-1950, Table 2",
                        "text": "At 1 year, 87.0% of patients in the TriClip group had TR of moderate or less (TR \u2264 2+), compared with 4.8% in the control group. Events: 152 of 175 in the device arm achieved TR reduction.",
                        "highlights": ["87.0%", "152", "175", "4.8%"],
                    },
                    {
                        "label": "RoB Assessment",
                        "source": "NCT04221490 (ClinicalTrials.gov)",
                        "text": "Randomized, controlled, multicenter trial. Open-label design (D2: some concerns due to knowledge of assigned intervention). Central adjudication of echocardiographic endpoints.",
                        "highlights": ["Randomized", "Open-label", "some concerns"],
                    },
                ],
            },
            # ── Single-arm studies (not poolable — tE/tN/cE/cN = 0) ──
            "NCT04097145": {
                "name": "CLASP TR", "phase": "Single-arm", "year": 2021,
                "tE": 0, "tN": 0, "cE": 0, "cN": 0,
                "group": "PASCAL (single-arm)",
                "rob": ["low", "low", "some", "low", "low"],
                "snippet": "Kodali S et al. JACC 2021. Single-arm PASCAL study (n=65). 70.8% TR reduction at 12m. Not poolable (no comparator arm).",
                "evidence": [
                    {
                        "label": "Enrollment",
                        "source": "Kodali S et al. JACC 2021",
                        "text": "A total of 65 patients with severe or greater tricuspid regurgitation were enrolled in the single-arm CLASP TR study using the PASCAL transcatheter valve repair system.",
                        "highlights": ["65", "PASCAL"],
                    },
                    {
                        "label": "Primary Outcome",
                        "source": "Kodali S et al. JACC 2021",
                        "text": "At 12 months, 70.8% of patients achieved TR reduction to moderate or less (TR \u2264 2+). Events: 46 of 65 patients achieved the primary endpoint.",
                        "highlights": ["70.8%", "46", "65"],
                    },
                    {
                        "label": "RoB Assessment",
                        "source": "NCT04097145",
                        "text": "Single-arm prospective study. D3 rated some concerns due to absence of control arm and potential for attrition bias in single-arm design.",
                        "highlights": ["Single-arm", "some concerns"],
                    },
                ],
            },
            "BRIGHT_REGISTRY": {
                "name": "bRIGHT", "phase": "Registry", "year": 2021,
                "tE": 0, "tN": 0, "cE": 0, "cN": 0,
                "group": "TriClip (registry)",
                "rob": ["low", "low", "some", "low", "low"],
                "snippet": "Nickenig G et al. EuroIntervention 2021. Multicenter registry (n=200). 75.0% TR reduction at 6m. Not poolable (no comparator, 6m follow-up only).",
                "evidence": [
                    {
                        "label": "Enrollment",
                        "source": "Nickenig G et al. EuroIntervention 2021",
                        "text": "The bRIGHT registry enrolled 200 consecutive patients undergoing transcatheter tricuspid-valve repair with the TriClip device across 15 European centers.",
                        "highlights": ["200", "TriClip", "15 European centers"],
                    },
                    {
                        "label": "Primary Outcome",
                        "source": "Nickenig G et al. EuroIntervention 2021",
                        "text": "At 6-month follow-up, 75.0% of patients achieved TR reduction to moderate or less. Events: 150 of 200 patients.",
                        "highlights": ["75.0%", "150", "200"],
                    },
                    {
                        "label": "RoB Assessment",
                        "source": "bRIGHT Registry",
                        "text": "Prospective multicenter registry. Some concerns for D3 (missing data) due to 6-month follow-up only and registry-based enrollment.",
                        "highlights": ["registry", "Some concerns"],
                    },
                ],
            },
            "TRILUMINATE_EU": {
                "name": "TRILUMINATE EU", "phase": "Registry", "year": 2023,
                "tE": 0, "tN": 0, "cE": 0, "cN": 0,
                "group": "TriClip G4 (registry)",
                "rob": ["low", "low", "some", "low", "low"],
                "snippet": "Lurz P et al. JACC Cardiovasc Interv 2023. European registry (n=120). 81.7% TR reduction at 12m. Not poolable (no comparator arm).",
                "evidence": [
                    {
                        "label": "Enrollment",
                        "source": "Lurz P et al. JACC Cardiovasc Interv 2023",
                        "text": "TRILUMINATE EU enrolled 120 patients with severe tricuspid regurgitation treated with the TriClip G4 device at 20 European sites.",
                        "highlights": ["120", "TriClip G4", "20 European sites"],
                    },
                    {
                        "label": "Primary Outcome",
                        "source": "Lurz P et al. JACC Cardiovasc Interv 2023",
                        "text": "At 12 months, 81.7% of patients achieved TR reduction to moderate or less (TR \u2264 2+). Events: 98 of 120 patients.",
                        "highlights": ["81.7%", "98", "120"],
                    },
                    {
                        "label": "RoB Assessment",
                        "source": "TRILUMINATE EU Registry",
                        "text": "Prospective European registry. D3 some concerns: registry design without randomization or blinding, though core lab adjudication of echocardiographic endpoints was performed.",
                        "highlights": ["registry", "some concerns", "core lab adjudication"],
                    },
                ],
            },
        },
    },
]  # Will be extended by subsequent tasks


if __name__ == '__main__':
    if not os.path.exists(TEMPLATE_PATH):
        print(f"ERROR: Template not found at {TEMPLATE_PATH}")
        sys.exit(1)

    if '--list' in sys.argv:
        for i, app in enumerate(APPS):
            print(f"  {i+1}. {app['filename']} — {app['title_short']}")
        sys.exit(0)

    target = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('-') else None
    total_errors = 0
    for app in APPS:
        if target and target not in app['filename']:
            continue
        out_dir = app.get('output_dir', None)
        errs = generate_app(app, out_dir)
        total_errors += len(errs)

    print(f"\n{'='*60}")
    print(f"Done. {len(APPS)} apps, {total_errors} total errors.")
    if total_errors > 0:
        sys.exit(1)
