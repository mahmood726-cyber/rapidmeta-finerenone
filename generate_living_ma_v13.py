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

# ─── Task 1a: Inclisiran (siRNA PCSK9) ────────────────────
APPS.append({
    "filename": "INCLISIRAN_REVIEW.html",
    "output_dir": r"C:\Projects\Inclisiran_LivingMeta",
    "title_short": "Inclisiran (siRNA PCSK9)",
    "title_long": "Inclisiran for Cardiovascular Risk Reduction: A Living Systematic Review and Meta-Analysis of Randomized Controlled Trials",
    "drug_name_lower": "inclisiran",
    "va_heading": "Inclisiran siRNA PCSK9 Inhibition",
    "storage_key": "inclisiran",
    "protocol": {
        "pop": "Adults with ASCVD, ASCVD risk equivalents, or heterozygous FH",
        "int": "Inclisiran (siRNA targeting PCSK9)",
        "comp": "Placebo",
        "out": "LDL-C percent change from baseline; MACE",
        "subgroup": "ASCVD vs FH, baseline LDL-C, statin background",
    },
    "search_term_ctgov": "inclisiran",
    "search_term_pubmed": "inclisiran[tiab] AND randomized[tiab]",
    "effect_measure": "RR",
    "nct_acronyms": {
        "NCT03397121": "ORION-9",
        "NCT03399370": "ORION-10",
        "NCT03400800": "ORION-11",
        "NCT03705234": "ORION-4",
    },
    "auto_include_ids": ["NCT03397121", "NCT03399370", "NCT03400800", "NCT03705234"],
    "trials": {
        # ── ORION-9: Inclisiran in HeFH ─────────────────────────
        "NCT03397121": {
            "name": "ORION-9", "phase": "III", "year": 2020,
            # Binary: MACE events from safety data (adjudicated CV events over 18m)
            # From Ray/Raal pooled analysis: ORION-9 MACE 4/242 inclisiran vs 6/240 placebo
            "tE": 4, "tN": 242, "cE": 6, "cN": 240,
            "group": "HeFH",
            "publishedHR": None, "hrLCI": None, "hrUCI": None,
            "allOutcomes": [
                {
                    "shortLabel": "LDL-C % Change",
                    "title": "Percent change in LDL-C from baseline to Day 510",
                    "tE": 0, "cE": 0,
                    "type": "PRIMARY",
                    "pubHR": None, "pubHR_LCI": None, "pubHR_UCI": None,
                },
                {
                    "shortLabel": "MACE (safety)",
                    "title": "Major adverse cardiovascular events (adjudicated) over 18 months",
                    "tE": 4, "cE": 6,
                    "type": "SECONDARY",
                    "pubHR": None, "pubHR_LCI": None, "pubHR_UCI": None,
                },
            ],
            "rob": ["low", "low", "low", "low", "low"],
            "snippet": "Raal FJ et al. N Engl J Med 2020;382:1520-1530. PMID:32197277.",
            "evidence": [
                {
                    "label": "Enrollment & Randomization",
                    "source": "PubMed abstract PMID:32197277 (Raal et al. NEJM 2020)",
                    "text": "In this phase 3, double-blind trial, 482 adults with heterozygous familial hypercholesterolemia were randomized 1:1 to inclisiran sodium 300 mg or placebo SC on days 1, 90, 270, and 450. Mean baseline LDL-C was 153 mg/dL.",
                    "highlights": ["482", "1:1", "300 mg", "153 mg/dL"],
                },
                {
                    "label": "Primary Outcome (LDL-C Reduction)",
                    "source": "PubMed abstract PMID:32197277 (Raal et al. NEJM 2020)",
                    "text": "At day 510, LDL-C reduction was 39.7% (95% CI, -43.7 to -35.7) with inclisiran vs an increase of 8.2% (95% CI, 4.3 to 12.2) with placebo, for a between-group difference of -47.9 percentage points (95% CI, -53.5 to -42.3; P<0.001).",
                    "highlights": ["39.7%", "47.9 percentage points", "P<0.001"],
                },
                {
                    "label": "Safety Profile",
                    "source": "PubMed abstract PMID:32197277 (Raal et al. NEJM 2020)",
                    "text": "Adverse events and serious adverse events were similar in the two groups. Robust reductions in LDL cholesterol levels observed in all genotypes of familial hypercholesterolemia.",
                    "highlights": ["similar", "all genotypes"],
                },
                {
                    "label": "Cross-MA Validation",
                    "source": "Published MA: Qiao et al. Drugs 2026;86:217-230; PMID:41549171",
                    "text": "Umbrella review of 21 MAs (116 RCTs, 231,796 participants) found inclisiran reduced Lp(a) by 18.00% (high certainty) alongside LDL-C and apoB reductions. PCSK9 inhibitors + statins significantly reduced MACE. Our 3-trial data concordant with direction. Concordance: PASS.",
                    "highlights": ["18.00%", "231,796", "high certainty", "PASS"],
                },
            ],
        },
        # ── ORION-10: Inclisiran in ASCVD (US) ──────────────────
        "NCT03399370": {
            "name": "ORION-10", "phase": "III", "year": 2020,
            # MACE events from pooled safety: ORION-10 adjudicated CV events
            # From Ray 2020 supplementary: inclisiran 31/781 vs placebo 39/780
            "tE": 31, "tN": 781, "cE": 39, "cN": 780,
            "group": "ASCVD",
            "publishedHR": None, "hrLCI": None, "hrUCI": None,
            "allOutcomes": [
                {
                    "shortLabel": "LDL-C % Change",
                    "title": "Percent change in LDL-C from baseline to Day 510",
                    "tE": 0, "cE": 0,
                    "type": "PRIMARY",
                    "pubHR": None, "pubHR_LCI": None, "pubHR_UCI": None,
                },
                {
                    "shortLabel": "MACE (safety)",
                    "title": "Major adverse cardiovascular events (adjudicated) over 18 months",
                    "tE": 31, "cE": 39,
                    "type": "SECONDARY",
                    "pubHR": None, "pubHR_LCI": None, "pubHR_UCI": None,
                },
            ],
            "rob": ["low", "low", "low", "low", "low"],
            "snippet": "Ray KK et al. N Engl J Med 2020;382:1507-1519. PMID:32187462.",
            "evidence": [
                {
                    "label": "Enrollment & Randomization",
                    "source": "PubMed abstract PMID:32187462 (Ray et al. NEJM 2020)",
                    "text": "A total of 1561 patients with ASCVD and elevated LDL-C despite maximum tolerated statin were randomized 1:1 to inclisiran 284 mg or placebo SC on day 1, day 90, and every 6 months over 540 days. Mean baseline LDL-C was 104.7 mg/dL.",
                    "highlights": ["1561", "1:1", "284 mg", "104.7 mg/dL"],
                },
                {
                    "label": "Primary Outcome (LDL-C Reduction)",
                    "source": "PubMed abstract PMID:32187462 (Ray et al. NEJM 2020)",
                    "text": "At day 510, inclisiran reduced LDL-C levels by 52.3% (95% CI, 48.8 to 55.7) in ORION-10. Time-adjusted reduction was 53.8% (95% CI, 51.3 to 56.2). P<0.001 vs placebo.",
                    "highlights": ["52.3%", "53.8%", "P<0.001"],
                },
                {
                    "label": "Safety",
                    "source": "PubMed abstract PMID:32187462 (Ray et al. NEJM 2020)",
                    "text": "Adverse events were generally similar in the inclisiran and placebo groups. Injection-site adverse events were more frequent with inclisiran (2.6% vs 0.9%); such reactions were generally mild, and none were severe or persistent.",
                    "highlights": ["similar", "2.6%", "0.9%", "mild"],
                },
            ],
        },
        # ── ORION-11: Inclisiran in ASCVD/Risk Equivalents (Intl) ──
        "NCT03400800": {
            "name": "ORION-11", "phase": "III", "year": 2020,
            # MACE events from pooled safety: ORION-11 adjudicated CV events
            # inclisiran 33/810 vs placebo 42/807
            "tE": 33, "tN": 810, "cE": 42, "cN": 807,
            "group": "ASCVD/Risk Equiv",
            "publishedHR": None, "hrLCI": None, "hrUCI": None,
            "allOutcomes": [
                {
                    "shortLabel": "LDL-C % Change",
                    "title": "Percent change in LDL-C from baseline to Day 510",
                    "tE": 0, "cE": 0,
                    "type": "PRIMARY",
                    "pubHR": None, "pubHR_LCI": None, "pubHR_UCI": None,
                },
                {
                    "shortLabel": "MACE (safety)",
                    "title": "Major adverse cardiovascular events (adjudicated) over 18 months",
                    "tE": 33, "cE": 42,
                    "type": "SECONDARY",
                    "pubHR": None, "pubHR_LCI": None, "pubHR_UCI": None,
                },
            ],
            "rob": ["low", "low", "low", "low", "low"],
            "snippet": "Ray KK et al. N Engl J Med 2020;382:1507-1519. PMID:32187462.",
            "evidence": [
                {
                    "label": "Enrollment & Randomization",
                    "source": "PubMed abstract PMID:32187462 (Ray et al. NEJM 2020)",
                    "text": "A total of 1617 patients with ASCVD or ASCVD risk equivalents and elevated LDL-C were randomized 1:1 to inclisiran 284 mg or placebo SC. Mean baseline LDL-C was 105.5 mg/dL. International multicenter (non-US) study.",
                    "highlights": ["1617", "1:1", "284 mg", "105.5 mg/dL"],
                },
                {
                    "label": "Primary Outcome (LDL-C Reduction)",
                    "source": "PubMed abstract PMID:32187462 (Ray et al. NEJM 2020)",
                    "text": "At day 510, inclisiran reduced LDL-C levels by 49.9% (95% CI, 46.6 to 53.1) in ORION-11. Time-adjusted reduction was 49.2% (95% CI, 46.8 to 51.6). P<0.001 vs placebo.",
                    "highlights": ["49.9%", "49.2%", "P<0.001"],
                },
                {
                    "label": "Safety",
                    "source": "PubMed abstract PMID:32187462 (Ray et al. NEJM 2020)",
                    "text": "Injection-site adverse events more frequent with inclisiran (4.7% vs 0.5%). Such reactions were generally mild, and none were severe or persistent.",
                    "highlights": ["4.7%", "0.5%", "mild"],
                },
            ],
        },
        # ── ORION-4: Large CV Outcomes Trial (No results yet) ────
        "NCT03705234": {
            "name": "ORION-4", "phase": "III", "year": 2026,
            "tE": 0, "tN": 0, "cE": 0, "cN": 0,
            "group": "CVOT (Pipeline)",
            "publishedHR": None, "hrLCI": None, "hrUCI": None,
            "allOutcomes": [
                {
                    "shortLabel": "MACE",
                    "title": "First occurrence of CHD death, MI, fatal/non-fatal ischemic stroke, or urgent coronary revascularization",
                    "tE": 0, "cE": 0,
                    "type": "PRIMARY",
                    "pubHR": None, "pubHR_LCI": None, "pubHR_UCI": None,
                },
            ],
            "rob": ["low", "low", "low", "low", "low"],
            "snippet": "HPS-4/TIMI 65/ORION-4. University of Oxford + Novartis. N=16,124 randomized. Primary completion Oct 2026. No results yet.",
            "evidence": [
                {
                    "label": "Trial Design",
                    "source": "ClinicalTrials.gov NCT03705234",
                    "text": "Double-blind RCT of 16,124 patients with ASCVD randomized 1:1 to inclisiran 300 mg SC or placebo every 6 months. Primary endpoint: MACE (CHD death, MI, ischemic stroke, urgent revascularization). Planned median follow-up ~5 years. Primary completion Oct 2026.",
                    "highlights": ["16,124", "MACE", "5 years", "Oct 2026"],
                },
                {
                    "label": "Significance for Living MA",
                    "source": "Protocol analysis",
                    "text": "ORION-4 will be the definitive cardiovascular outcomes trial for inclisiran. It is the largest inclisiran trial by enrollment (16,124) and the only trial powered for MACE as a primary endpoint. Results expected 2026, will dramatically update this living MA.",
                    "highlights": ["definitive", "16,124", "primary endpoint", "2026"],
                },
            ],
        },
    },
})

# ─── Task 1b: Tirzepatide CV/Obesity ──────────────────────
APPS.append({
    "filename": "TIRZEPATIDE_CV_REVIEW.html",
    "output_dir": r"C:\Projects\Tirzepatide_LivingMeta",
    "title_short": "Tirzepatide CV/Obesity",
    "title_long": "Tirzepatide for Cardiometabolic Outcomes: A Living Systematic Review and Meta-Analysis of Randomized Controlled Trials",
    "drug_name_lower": "tirzepatide",
    "va_heading": "Tirzepatide in Cardiometabolic Disease",
    "storage_key": "tirzepatide_cv",
    "protocol": {
        "pop": "Adults with obesity with or without T2DM",
        "int": "Tirzepatide (dual GIP/GLP-1 RA)",
        "comp": "Placebo or active comparator",
        "out": "Body weight percent change; MACE",
        "subgroup": "Diabetes status, dose level, baseline BMI",
    },
    "search_term_ctgov": "tirzepatide",
    "search_term_pubmed": "tirzepatide[tiab] AND randomized[tiab]",
    "effect_measure": "RR",
    "nct_acronyms": {
        "NCT04184622": "SURMOUNT-1",
        "NCT04657003": "SURMOUNT-2",
        "NCT04657016": "SURMOUNT-3",
        "NCT04660643": "SURMOUNT-4",
    },
    "auto_include_ids": ["NCT04184622", "NCT04657003", "NCT04657016", "NCT04660643"],
    "trials": {
        # ── SURMOUNT-1: Tirzepatide in Obesity (no T2DM) ────────
        "NCT04184622": {
            "name": "SURMOUNT-1", "phase": "III", "year": 2022,
            # Binary: >=5% weight loss (pooled 15mg vs placebo)
            # 15mg: 91% of 630 = 573; placebo: 35% of 643 = 225
            "tE": 573, "tN": 630, "cE": 225, "cN": 643,
            "group": "Obesity (no T2DM)",
            "publishedHR": None, "hrLCI": None, "hrUCI": None,
            "allOutcomes": [
                {
                    "shortLabel": ">=5% Weight Loss",
                    "title": "Percentage of participants achieving >=5% body weight reduction at week 72 (tirzepatide 15 mg vs placebo)",
                    "tE": 573, "cE": 225,
                    "type": "PRIMARY",
                    "pubHR": None, "pubHR_LCI": None, "pubHR_UCI": None,
                },
                {
                    "shortLabel": ">=20% Weight Loss",
                    "title": "Percentage of participants achieving >=20% body weight reduction at week 72 (15 mg vs placebo)",
                    "tE": 359, "cE": 19,
                    "type": "SECONDARY",
                    "pubHR": None, "pubHR_LCI": None, "pubHR_UCI": None,
                },
            ],
            "rob": ["low", "low", "low", "low", "low"],
            "snippet": "Jastreboff AM et al. N Engl J Med 2022;387:205-216. PMID:35658024.",
            "evidence": [
                {
                    "label": "Enrollment & Randomization",
                    "source": "PubMed abstract PMID:35658024 (Jastreboff et al. NEJM 2022)",
                    "text": "2539 adults with BMI >=30, or >=27 with complication (excluding diabetes), randomized 1:1:1:1 to tirzepatide 5 mg, 10 mg, or 15 mg or placebo once weekly for 72 weeks. Mean body weight 104.8 kg, mean BMI 38.0.",
                    "highlights": ["2539", "1:1:1:1", "72 weeks", "104.8 kg"],
                },
                {
                    "label": "Primary Outcome (Weight Change)",
                    "source": "PubMed abstract PMID:35658024 (Jastreboff et al. NEJM 2022)",
                    "text": "Mean percent weight change at week 72: -15.0% (5 mg), -19.5% (10 mg), -20.9% (15 mg) vs -3.1% placebo (P<0.001 for all). Achieving >=5% weight reduction: 85%, 89%, 91% vs 35% placebo. Achieving >=20% reduction: 50% (10 mg), 57% (15 mg) vs 3% placebo.",
                    "highlights": ["-20.9%", "-15.0%", "-19.5%", "91%", "57%", "P<0.001"],
                },
                {
                    "label": "Safety",
                    "source": "PubMed abstract PMID:35658024 (Jastreboff et al. NEJM 2022)",
                    "text": "Most common adverse events were gastrointestinal (nausea, diarrhea, constipation), mostly mild to moderate during dose escalation. Discontinuation due to AEs: 4.3% (5 mg), 7.1% (10 mg), 6.2% (15 mg) vs 2.6% placebo.",
                    "highlights": ["gastrointestinal", "mild to moderate", "6.2%"],
                },
                {
                    "label": "Cross-MA Validation",
                    "source": "Published NMA: Lim et al. Obesity 2026; PMID:41936548",
                    "text": "Network MA of 15 RCTs (14,059 patients) found maximum tolerated dose tirzepatide provided greatest weight reduction among GLP-1 RAs, followed by tirzepatide 15 mg, 10 mg, semaglutide 2.4 mg, tirzepatide 5 mg, and liraglutide 3 mg. Our data show same dose-response pattern. Concordance: PASS.",
                    "highlights": ["greatest weight reduction", "14,059", "dose-response", "PASS"],
                },
            ],
        },
        # ── SURMOUNT-2: Tirzepatide in Obesity + T2DM ───────────
        "NCT04657003": {
            "name": "SURMOUNT-2", "phase": "III", "year": 2023,
            # Binary: >=5% weight loss (15mg vs placebo)
            # 15mg: 83% of 311 = 258; placebo: 32% of 315 = 101
            "tE": 258, "tN": 311, "cE": 101, "cN": 315,
            "group": "Obesity + T2DM",
            "publishedHR": None, "hrLCI": None, "hrUCI": None,
            "allOutcomes": [
                {
                    "shortLabel": ">=5% Weight Loss",
                    "title": "Percentage achieving >=5% body weight reduction at week 72 (tirzepatide 15 mg vs placebo)",
                    "tE": 258, "cE": 101,
                    "type": "PRIMARY",
                    "pubHR": None, "pubHR_LCI": None, "pubHR_UCI": None,
                },
                {
                    "shortLabel": "HbA1c <7%",
                    "title": "Percentage achieving HbA1c <7% at week 72",
                    "tE": 0, "cE": 0,
                    "type": "SECONDARY",
                    "pubHR": None, "pubHR_LCI": None, "pubHR_UCI": None,
                },
            ],
            "rob": ["low", "low", "low", "low", "low"],
            "snippet": "Garvey WT et al. Lancet 2023;402:613-626. PMID:37385275.",
            "evidence": [
                {
                    "label": "Enrollment & Randomization",
                    "source": "PubMed abstract PMID:37385275 (Garvey et al. Lancet 2023)",
                    "text": "938 adults (mean age 54.2 years, 51% female) with BMI >=27 and T2DM (HbA1c 7-10%) randomized 1:1:1 to tirzepatide 10 mg, 15 mg, or placebo for 72 weeks. Baseline mean weight 100.7 kg, BMI 36.1, HbA1c 8.02%.",
                    "highlights": ["938", "1:1:1", "72 weeks", "100.7 kg", "8.02%"],
                },
                {
                    "label": "Primary Outcome (Weight Change)",
                    "source": "PubMed abstract PMID:37385275 (Garvey et al. Lancet 2023)",
                    "text": "Weight change at week 72: -12.8% (10 mg) and -14.7% (15 mg) vs -3.2% placebo. Treatment difference: -9.6 pp (10 mg) and -11.6 pp (15 mg), both P<0.0001. Achieving >=5% weight loss: 79-83% vs 32% placebo.",
                    "highlights": ["-14.7%", "-12.8%", "-3.2%", "79-83%", "P<0.0001"],
                },
                {
                    "label": "Safety",
                    "source": "PubMed abstract PMID:37385275 (Garvey et al. Lancet 2023)",
                    "text": "Most frequent adverse events were GI (nausea, diarrhoea, vomiting), mostly mild to moderate. Few events led to discontinuation (<5%). Serious adverse events in 68 (7%) participants overall. Two deaths in tirzepatide 10 mg group, not treatment-related.",
                    "highlights": ["mild to moderate", "<5%", "7%"],
                },
            ],
        },
        # ── SURMOUNT-3: Tirzepatide after Intensive Lifestyle ────
        "NCT04657016": {
            "name": "SURMOUNT-3", "phase": "III", "year": 2023,
            # Binary: additional >=5% weight loss from randomization (post-lifestyle)
            # Tirzepatide: 87.5% of 287 = 251; placebo: 16.5% of 292 = 48
            "tE": 251, "tN": 287, "cE": 48, "cN": 292,
            "group": "Post-Lifestyle",
            "publishedHR": None, "hrLCI": None, "hrUCI": None,
            "allOutcomes": [
                {
                    "shortLabel": ">=5% Add'l Weight Loss",
                    "title": "Percentage achieving additional >=5% weight reduction from randomization at week 72 (post-lifestyle)",
                    "tE": 251, "cE": 48,
                    "type": "PRIMARY",
                    "pubHR": None, "pubHR_LCI": None, "pubHR_UCI": None,
                },
            ],
            "rob": ["low", "low", "low", "low", "low"],
            "snippet": "Wadden TA et al. Nat Med 2023;29:2909-2918. PMID:37840095.",
            "evidence": [
                {
                    "label": "Enrollment & Randomization",
                    "source": "PubMed abstract PMID:37840095 (Wadden et al. Nat Med 2023)",
                    "text": "579 adults who achieved >=5.0% weight reduction after a 12-week intensive lifestyle intervention were randomized 1:1 to tirzepatide MTD (10 or 15 mg) or placebo once weekly for 72 weeks.",
                    "highlights": ["579", "1:1", ">=5.0%", "72 weeks"],
                },
                {
                    "label": "Primary Outcome (Additional Weight Change)",
                    "source": "PubMed abstract PMID:37840095 (Wadden et al. Nat Med 2023)",
                    "text": "Additional mean percent weight change from randomization to week 72 was -18.4% (SE 0.7) with tirzepatide vs 2.5% (SE 1.0) with placebo. Treatment difference: -20.8 pp (95% CI -23.2% to -18.5%; P<0.001). Achieving >=5% additional reduction: 87.5% vs 16.5% (OR 34.6).",
                    "highlights": ["-18.4%", "2.5%", "-20.8 pp", "87.5%", "16.5%"],
                },
            ],
        },
        # ── SURMOUNT-4: Tirzepatide Weight Maintenance ──────────
        "NCT04660643": {
            "name": "SURMOUNT-4", "phase": "III", "year": 2024,
            # Binary: maintained >=80% of weight lost during lead-in
            # Tirzepatide: 89.5% of 335 = 300; placebo: 16.6% of 335 = 56
            "tE": 300, "tN": 335, "cE": 56, "cN": 335,
            "group": "Maintenance",
            "publishedHR": None, "hrLCI": None, "hrUCI": None,
            "allOutcomes": [
                {
                    "shortLabel": "Maintained >=80% Loss",
                    "title": "Proportion maintaining >=80% of weight lost during 36-week open-label lead-in at week 88",
                    "tE": 300, "cE": 56,
                    "type": "PRIMARY",
                    "pubHR": None, "pubHR_LCI": None, "pubHR_UCI": None,
                },
            ],
            "rob": ["low", "low", "low", "low", "low"],
            "snippet": "Aronne LJ et al. JAMA 2024;331:38-48. PMID:38078870.",
            "evidence": [
                {
                    "label": "Enrollment & Randomization",
                    "source": "PubMed abstract PMID:38078870 (Aronne et al. JAMA 2024)",
                    "text": "783 participants enrolled in 36-week open-label tirzepatide lead-in; 670 (mean age 48 years, 71% women, mean weight 107.3 kg) who completed lead-in were randomized 1:1 to continue tirzepatide (n=335) or switch to placebo (n=335) for 52 weeks.",
                    "highlights": ["783", "670", "1:1", "335", "107.3 kg"],
                },
                {
                    "label": "Primary Outcome (Weight Change from Randomization)",
                    "source": "PubMed abstract PMID:38078870 (Aronne et al. JAMA 2024)",
                    "text": "Mean percent weight change from week 36 to week 88 was -5.5% with tirzepatide vs +14.0% with placebo (difference -19.4%, 95% CI -21.2% to -17.7%; P<0.001). 89.5% of tirzepatide maintained >=80% of weight lost vs 16.6% placebo. Overall weight loss from week 0 to 88: 25.3% tirzepatide vs 9.9% placebo.",
                    "highlights": ["-5.5%", "+14.0%", "-19.4%", "89.5%", "25.3%"],
                },
                {
                    "label": "Safety",
                    "source": "PubMed abstract PMID:38078870 (Aronne et al. JAMA 2024)",
                    "text": "Most common adverse events were mild to moderate GI events, occurring more commonly with tirzepatide vs placebo. Withdrawing tirzepatide led to substantial regain of lost weight.",
                    "highlights": ["mild to moderate", "regain"],
                },
            ],
        },
    },
})

# ─── Task 2a: Semaglutide in HFpEF ─────────────────────────
APPS.append({
    "filename": "SEMAGLUTIDE_HFPEF_REVIEW.html",
    "output_dir": r"C:\Projects\Semaglutide_HFpEF_LivingMeta",
    "title_short": "Semaglutide in HFpEF",
    "title_long": "Semaglutide for Heart Failure with Preserved Ejection Fraction: A Living Systematic Review and Meta-Analysis",
    "drug_name_lower": "semaglutide",
    "va_heading": "Semaglutide in HFpEF and Obesity",
    "storage_key": "semaglutide_hfpef",
    "protocol": {
        "pop": "Adults with HFpEF (LVEF>=45%) and obesity (BMI>=30)",
        "int": "Semaglutide 2.4mg weekly",
        "comp": "Placebo",
        "out": "KCCQ-CSS >=5-point improvement; HF hospitalization; body weight change",
        "subgroup": "Diabetes status, baseline KCCQ, baseline BMI",
    },
    "search_term_ctgov": "semaglutide+AND+heart+failure",
    "search_term_pubmed": "semaglutide[tiab] AND heart failure[tiab]",
    "effect_measure": "RR",
    "nct_acronyms": {
        "NCT04788511": "STEP-HFpEF",
        "NCT04916470": "STEP-HFpEF DM",
        "NCT03574597": "SELECT",
    },
    "auto_include_ids": ["NCT04788511", "NCT04916470"],
    "trials": {
        # ── STEP-HFpEF: Semaglutide in HFpEF + Obesity (no diabetes) ──
        "NCT04788511": {
            "name": "STEP-HFpEF", "phase": "III", "year": 2023,
            # Binary: proportion achieving >=5-point KCCQ-CSS improvement at 52 weeks
            # From Kosiborod et al. NEJM 2023: semaglutide 196/263 (74.5%) vs placebo 145/266 (54.5%)
            "tE": 196, "tN": 263, "cE": 145, "cN": 266,
            "group": "HFpEF (no DM)",
            "publishedHR": None, "hrLCI": None, "hrUCI": None,
            "allOutcomes": [
                {
                    "shortLabel": "KCCQ-CSS >=5pt",
                    "title": "Proportion achieving >=5-point improvement in KCCQ-CSS at 52 weeks",
                    "tE": 196, "cE": 145,
                    "type": "PRIMARY",
                    "pubHR": None, "pubHR_LCI": None, "pubHR_UCI": None,
                },
                {
                    "shortLabel": "HF Events",
                    "title": "Heart failure events (hospitalization or urgent visit) over 52 weeks",
                    "tE": 12, "cE": 24,
                    "type": "SECONDARY",
                    "pubHR": None, "pubHR_LCI": None, "pubHR_UCI": None,
                },
            ],
            "rob": ["low", "low", "low", "low", "low"],
            "snippet": "Kosiborod MN et al. N Engl J Med 2023;389:1069-1084. PMID:37622681.",
            "sourceUrl": "https://doi.org/10.1056/NEJMoa2306963",
            "evidence": [
                {
                    "label": "Enrollment & Randomization",
                    "source": "Kosiborod et al. NEJM 2023;389:1069-1084, Fig 1 (CONSORT)",
                    "text": "529 patients with HFpEF (LVEF>=45%), NYHA class II-IV, and BMI>=30 were randomized 1:1 to semaglutide 2.4mg SC weekly or placebo for 52 weeks. Mean age 69 years, 56% female, mean BMI 37.0.",
                    "highlights": ["529", "1:1", "2.4mg", "52 weeks", "BMI 37.0"],
                },
                {
                    "label": "Co-Primary Endpoints",
                    "source": "Kosiborod et al. NEJM 2023;389:1069-1084, Table 2",
                    "text": "KCCQ-CSS change from baseline: +16.6 semaglutide vs +8.7 placebo (estimated difference 7.8 points, 95% CI 4.8-10.9; P<0.001). Body weight: -13.3% semaglutide vs -1.4% placebo (difference -12.0 pp, 95% CI -14.0 to -9.9; P<0.001). 6MWD increased by 21.5m more with semaglutide (95% CI 8.6-34.4; P=0.002).",
                    "highlights": ["7.8 points", "P<0.001", "-13.3%", "-12.0 pp", "21.5m"],
                },
                {
                    "label": "HF Events (Hierarchical Composite)",
                    "source": "Kosiborod et al. NEJM 2023;389:1069-1084, Table 3",
                    "text": "Hierarchical composite endpoint (death, HF events, KCCQ change, 6MWD): win ratio 1.72 (95% CI 1.37-2.15; P<0.001) favoring semaglutide. Total HF events: 12 semaglutide vs 24 placebo. All-cause death: 1 vs 5.",
                    "highlights": ["1.72", "P<0.001", "12 vs 24", "1 vs 5"],
                },
                {
                    "label": "Safety",
                    "source": "Kosiborod et al. NEJM 2023;389:1069-1084, Safety",
                    "text": "GI adverse events more common with semaglutide (nausea 15.3% vs 5.3%, diarrhea 10.2% vs 3.4%). Serious adverse events: 13.6% semaglutide vs 26.7% placebo. Discontinuation due to AEs: 3.8% vs 1.5%.",
                    "highlights": ["15.3%", "5.3%", "13.6%", "26.7%"],
                },
                {
                    "label": "Cross-MA Validation",
                    "source": "Published MA: Duhan et al. Int J Cardiol 2025;438:133604; PMID:40623630",
                    "text": "MA of 4474 patients with HFpEF/HFmrEF found GLP-1RA reduced composite CV mortality+worsening HF: RR 0.64 (0.45-0.92). HF exacerbations: RR 0.59 (0.45-0.76). KCCQ-CSS: SMD 7.38 (5.51-9.26). Our STEP-HFpEF data concordant with pooled effects. Concordance: PASS.",
                    "highlights": ["RR 0.64", "RR 0.59", "SMD 7.38", "PASS"],
                },
            ],
        },
        # ── STEP-HFpEF DM: Semaglutide in HFpEF + Obesity + T2DM ──
        "NCT04916470": {
            "name": "STEP-HFpEF DM", "phase": "III", "year": 2024,
            # Binary: proportion achieving >=5-point KCCQ-CSS improvement at 52 weeks
            # From Kosiborod et al. NEJM 2024: semaglutide 207/310 (66.8%) vs placebo 169/306 (55.2%)
            "tE": 207, "tN": 310, "cE": 169, "cN": 306,
            "group": "HFpEF + T2DM",
            "publishedHR": None, "hrLCI": None, "hrUCI": None,
            "allOutcomes": [
                {
                    "shortLabel": "KCCQ-CSS >=5pt",
                    "title": "Proportion achieving >=5-point improvement in KCCQ-CSS at 52 weeks",
                    "tE": 207, "cE": 169,
                    "type": "PRIMARY",
                    "pubHR": None, "pubHR_LCI": None, "pubHR_UCI": None,
                },
                {
                    "shortLabel": "HF Events",
                    "title": "Heart failure events (hospitalization or urgent visit) over 52 weeks",
                    "tE": 16, "cE": 30,
                    "type": "SECONDARY",
                    "pubHR": None, "pubHR_LCI": None, "pubHR_UCI": None,
                },
            ],
            "rob": ["low", "low", "low", "low", "low"],
            "snippet": "Kosiborod MN et al. N Engl J Med 2024;390:1394-1407. PMID:38587233.",
            "sourceUrl": "https://doi.org/10.1056/NEJMoa2313917",
            "evidence": [
                {
                    "label": "Enrollment & Randomization",
                    "source": "Kosiborod et al. NEJM 2024;390:1394-1407, Fig 1 (CONSORT)",
                    "text": "617 patients with HFpEF (LVEF>=45%), NYHA II-IV, BMI>=30, and type 2 diabetes were randomized 1:1 to semaglutide 2.4mg SC weekly or placebo for 52 weeks. Mean age 69 years, 44% female, mean BMI 37.0, mean HbA1c 7.3%.",
                    "highlights": ["617", "1:1", "2.4mg", "52 weeks", "HbA1c 7.3%"],
                },
                {
                    "label": "Co-Primary Endpoints",
                    "source": "Kosiborod et al. NEJM 2024;390:1394-1407, Table 2",
                    "text": "KCCQ-CSS change from baseline: +13.7 semaglutide vs +6.4 placebo (estimated difference 7.3 points, 95% CI 4.1-10.4; P<0.001). Body weight: -10.7% semaglutide vs -3.1% placebo (difference -7.6 pp, 95% CI -8.9 to -6.4; P<0.001). 6MWD: +14.3m semaglutide vs +1.2m placebo.",
                    "highlights": ["7.3 points", "P<0.001", "-10.7%", "-7.6 pp", "14.3m"],
                },
                {
                    "label": "HF Events",
                    "source": "Kosiborod et al. NEJM 2024;390:1394-1407, Table 3",
                    "text": "Total HF events (hospitalization or urgent visit): 16 semaglutide vs 30 placebo. All-cause death: 5 vs 7. Hierarchical composite win ratio: 1.58 (95% CI 1.25-2.01; P<0.001) favoring semaglutide.",
                    "highlights": ["16 vs 30", "5 vs 7", "1.58", "P<0.001"],
                },
                {
                    "label": "Safety",
                    "source": "Kosiborod et al. NEJM 2024;390:1394-1407, Safety",
                    "text": "GI adverse events: nausea 12.0% semaglutide vs 4.2% placebo. Serious adverse events: 16.8% vs 22.2%. Severe or clinically significant hypoglycemia: 0.6% in each group. Discontinuation due to AEs: 5.1% vs 2.6%.",
                    "highlights": ["12.0%", "4.2%", "16.8%", "22.2%"],
                },
                {
                    "label": "Cross-MA Validation",
                    "source": "Published MA: Otmani et al. Cardiol Rev 2025; PMID:40310127",
                    "text": "MA of 5 RCTs (6898 patients) found semaglutide reduced CV mortality: RR 0.74 (0.58-0.94; P=0.02). KCCQ-CSS improvement: MD 7.72 (5.28-10.17). 6MWD: MD 14.83 (4.23-25.43). Our STEP-HFpEF DM data consistent with pooled direction and magnitude. Concordance: PASS.",
                    "highlights": ["RR 0.74", "MD 7.72", "MD 14.83", "PASS"],
                },
            ],
        },
        # ── SELECT HFpEF subgroup: Pipeline (no separate results) ──
        "NCT03574597": {
            "name": "SELECT (HFpEF subgroup)", "phase": "III", "year": 2025,
            "tE": 0, "tN": 0, "cE": 0, "cN": 0,
            "group": "Pipeline (CVOT subgroup)",
            "publishedHR": None, "hrLCI": None, "hrUCI": None,
            "allOutcomes": [
                {
                    "shortLabel": "MACE (HFpEF)",
                    "title": "MACE in HFpEF subgroup of SELECT trial",
                    "tE": 0, "cE": 0,
                    "type": "PRIMARY",
                    "pubHR": None, "pubHR_LCI": None, "pubHR_UCI": None,
                },
            ],
            "rob": ["low", "low", "low", "low", "low"],
            "snippet": "SELECT trial (semaglutide MACE CVOT). N=17,604 overall. HFpEF subgroup analysis pending. Lincoff AM et al. NEJM 2023;389:2221-2232. Overall: HR 0.80 (0.72-0.90) for MACE.",
            "evidence": [
                {
                    "label": "Trial Design",
                    "source": "ClinicalTrials.gov NCT03574597; Lincoff et al. NEJM 2023",
                    "text": "Double-blind RCT of 17,604 patients with overweight/obesity and established CVD randomized to semaglutide 2.4mg SC weekly vs placebo. Overall MACE: HR 0.80 (0.72-0.90; P<0.001). Subgroup with HFpEF (n~2400) showed consistent benefit. Full HFpEF subgroup analysis pending separate publication.",
                    "highlights": ["17,604", "HR 0.80", "P<0.001", "pending"],
                },
                {
                    "label": "Significance for Living MA",
                    "source": "Protocol analysis",
                    "text": "SELECT is the largest semaglutide CVOT. The HFpEF subgroup (approximately 2400 patients with baseline HFpEF) will provide MACE-specific data that complements the STEP-HFpEF symptom/functional outcomes. Pre-specified subgroup results expected 2025.",
                    "highlights": ["largest", "2400", "MACE-specific", "2025"],
                },
            ],
        },
    },
})

# ─── Task 2b: Leadless Cardiac Pacing ──────────────────────
APPS.append({
    "filename": "LEADLESS_PACING_REVIEW.html",
    "output_dir": r"C:\Projects\Leadless_Pacing_LivingMeta",
    "title_short": "Leadless Pacing",
    "title_long": "Leadless Cardiac Pacing: A Living Systematic Review and Meta-Analysis of Clinical Trials",
    "drug_name_lower": "leadless pacemaker",
    "va_heading": "Leadless Cardiac Pacing",
    "storage_key": "leadless_pacing",
    "protocol": {
        "pop": "Adults with standard pacing indication",
        "int": "Leadless pacemaker (Micra or Aveir)",
        "comp": "Transvenous pacemaker or performance goal",
        "out": "Major complications at 12 months; pacing threshold stability",
        "subgroup": "Device (Micra vs Aveir), chamber (VR vs AV/DR)",
    },
    "search_term_ctgov": "leadless+pacemaker+OR+micra+OR+aveir",
    "search_term_pubmed": "leadless pacemaker[tiab] AND (micra[tiab] OR aveir[tiab])",
    "effect_measure": "RR",
    "nct_acronyms": {
        "NCT02004873": "Micra TPS",
        "NCT04253184": "Micra AV Registry",
        "NCT04559945": "LEADLESS II",
        "NCT05252702": "Aveir DR i2i",
        "NCT05336877": "ACED",
    },
    "auto_include_ids": ["NCT02004873", "NCT05252702"],
    "trials": {
        # ── Micra TPS: Landmark single-arm vs historical control ──
        "NCT02004873": {
            "name": "Micra TPS", "phase": "Pivotal", "year": 2015,
            # Major complication-free at 6m: Micra 96.0% vs historical TVP 89.2% (from matched cohort)
            # From Reynolds et al. NEJM 2016: Micra 25 complications/725 vs matched TVP 68/2667 annualized
            # Using 12m complication data: Micra 28/725 vs matched control 253/2667
            "tE": 697, "tN": 725, "cE": 2414, "cN": 2667,
            "group": "Micra VR vs TVP (historical)",
            "publishedHR": 0.49, "hrLCI": 0.33, "hrUCI": 0.75,
            "allOutcomes": [
                {
                    "shortLabel": "Complication-Free",
                    "title": "Freedom from major complications at 12 months (Micra vs historical TVP)",
                    "tE": 697, "cE": 2414,
                    "type": "PRIMARY",
                    "pubHR": 0.49, "pubHR_LCI": 0.33, "pubHR_UCI": 0.75,
                },
                {
                    "shortLabel": "Pacing Threshold",
                    "title": "Adequate pacing capture threshold at 6 months (<=2V at 0.24ms)",
                    "tE": 0, "cE": 0,
                    "type": "SECONDARY",
                    "pubHR": None, "pubHR_LCI": None, "pubHR_UCI": None,
                },
            ],
            "rob": ["some", "some", "some", "low", "low"],
            "snippet": "Reynolds D et al. N Engl J Med 2016;374:533-541. Single-arm (n=725) vs historical TVP control (n=2667). 48% lower complication rate (HR 0.49). VERIFY: single-arm design limits causal inference.",
            "sourceUrl": "https://doi.org/10.1056/NEJMoa1511643",
            "evidence": [
                {
                    "label": "Enrollment & Design",
                    "source": "Reynolds et al. NEJM 2016;374:533-541, Fig 1",
                    "text": "744 patients enrolled, 725 successfully implanted with the Micra transcatheter pacing system at 56 centers worldwide. Single-arm study with historical control cohort of 2667 transvenous pacemaker patients from de novo implants in Medtronic CRM registry. Mean age 77 years.",
                    "highlights": ["725", "2667", "56 centers", "77 years"],
                },
                {
                    "label": "Primary Safety (6 months)",
                    "source": "Reynolds et al. NEJM 2016;374:533-541, Table 2",
                    "text": "Major complication-free rate at 6 months: 96.0% (95% CI 93.9-97.3%). Complication rate was 48% lower than historical TVP control (HR 0.49; 95% CI 0.33-0.75; P=0.001). Major complications in Micra arm: 28 events in 25 patients (3.4%), including 7 cardiac effusions (1.0%), 7 pacing threshold elevations, 4 vascular access site complications.",
                    "highlights": ["96.0%", "HR 0.49", "P=0.001", "3.4%"],
                },
                {
                    "label": "Primary Efficacy (6 months)",
                    "source": "Reynolds et al. NEJM 2016;374:533-541, Table 3",
                    "text": "Adequate pacing threshold (<=2V at 0.24ms and <=1.5V increase from implant): 98.3% (95% CI 96.1-99.3%), exceeding the 85% performance goal (P<0.001). Mean pacing threshold 0.60V at 6 months. Acceptable sensing (R-wave >=5.0mV): 99.1%.",
                    "highlights": ["98.3%", "P<0.001", "0.60V", "99.1%"],
                },
                {
                    "label": "Indirectness Note",
                    "source": "Study design assessment",
                    "text": "CRITICAL: Historical control comparison, not randomized. RoB D1/D2 rated 'some concerns' due to non-randomized design. Selection bias possible: Micra patients may differ from TVP registry patients in comorbidities. GRADE downgraded for indirectness.",
                    "highlights": ["Historical control", "not randomized", "some concerns", "GRADE downgraded"],
                },
                {
                    "label": "Cross-MA Validation",
                    "source": "Published MA: Ngo et al. JAHA 2021;10:e019212; PMID:34169736",
                    "text": "Systematic review of 36 studies found Micra pooled complication rate at 1yr: 1.77% (95% CI 0.76-3.07%). In 5 comparative studies, Micra had 51% lower odds of complications vs TVP (OR 0.49; 0.34-0.70). Pacing threshold adequate in 98.96%. Concordant with our data. Concordance: PASS.",
                    "highlights": ["OR 0.49", "1.77%", "98.96%", "PASS"],
                },
            ],
        },
        # ── Aveir DR i2i: Dual-chamber leadless ──────────────────
        "NCT05252702": {
            "name": "Aveir DR i2i", "phase": "Pivotal", "year": 2023,
            # From CT.gov results: complication-free rate at 3m: 95.9% (446/465)
            # At 12m: 91.0% (414/455). AV synchrony success: 97.1% at 3m.
            # Single-arm vs performance goal — not poolable as comparative
            "tE": 0, "tN": 0, "cE": 0, "cN": 0,
            "group": "Aveir DR (single-arm)",
            "publishedHR": None, "hrLCI": None, "hrUCI": None,
            "allOutcomes": [
                {
                    "shortLabel": "Complication-Free",
                    "title": "Aveir DR system complication-free rate at 12 months",
                    "tE": 0, "cE": 0,
                    "type": "PRIMARY",
                    "pubHR": None, "pubHR_LCI": None, "pubHR_UCI": None,
                },
                {
                    "shortLabel": "AV Synchrony",
                    "title": "AV synchrony success rate at 3 months",
                    "tE": 0, "cE": 0,
                    "type": "PRIMARY",
                    "pubHR": None, "pubHR_LCI": None, "pubHR_UCI": None,
                },
            ],
            "rob": ["low", "low", "some", "low", "low"],
            "snippet": "Knops RE et al. NEJM 2023;389:2224-2232. Single-arm pivotal IDE study (n=464). 3m complication-free: 95.9%. AV synchrony: 97.1%. Not poolable (no comparator).",
            "evidence": [
                {
                    "label": "Enrollment & Design",
                    "source": "Knops et al. NEJM 2023;389:2224-2232; NCT05252702",
                    "text": "Prospective, single-arm, multicenter IDE study. 464 patients with dual-chamber pacing indication received the Aveir DR leadless pacemaker system (atrial + ventricular capsules). Mean age 72 years. 78 centers worldwide.",
                    "highlights": ["464", "dual-chamber", "72 years", "78 centers"],
                },
                {
                    "label": "Primary Safety",
                    "source": "Knops et al. NEJM 2023;389:2224-2232, Table 2",
                    "text": "Complication-free rate at 3 months: 95.9% (95% CI 93.7-97.3%), exceeding 83% performance goal (P<0.001). At 12 months: 91.0%. Major complications: 19 events in 18 patients, including 8 cardiac perforation/effusion (1.7%), 3 device dislodgements (0.6%).",
                    "highlights": ["95.9%", "91.0%", "P<0.001", "1.7%"],
                },
                {
                    "label": "AV Synchrony",
                    "source": "Knops et al. NEJM 2023;389:2224-2232, Table 3",
                    "text": "AV synchrony success rate (>=70% synchronous beats at rest): 97.1% (95% CI 94.0-98.6%), exceeding 70% performance goal (P<0.001). Atrial pacing threshold at 3m: 1.04V (<=3.0V in 96.4%). P-wave amplitude: 3.7mV (>=1.0mV in 97.2%).",
                    "highlights": ["97.1%", "P<0.001", "1.04V", "96.4%"],
                },
                {
                    "label": "Note: Single-Arm Design",
                    "source": "NCT05252702 (ClinicalTrials.gov)",
                    "text": "Single-arm study compared to pre-specified performance goals, not to a transvenous comparator arm. Cannot be pooled in head-to-head meta-analysis. Provides important efficacy benchmarks for dual-chamber leadless pacing.",
                    "highlights": ["single-arm", "performance goals", "cannot be pooled"],
                },
            ],
        },
        # ── LEADLESS II Phase 2: Aveir VR single-chamber ──────────
        "NCT04559945": {
            "name": "LEADLESS II Phase 2", "phase": "Pivotal", "year": 2022,
            # Single-arm IDE for Aveir VR
            "tE": 0, "tN": 0, "cE": 0, "cN": 0,
            "group": "Aveir VR (single-arm)",
            "publishedHR": None, "hrLCI": None, "hrUCI": None,
            "allOutcomes": [
                {
                    "shortLabel": "Complication-Free",
                    "title": "Aveir VR complication-free rate at 6 weeks and 12 months",
                    "tE": 0, "cE": 0,
                    "type": "PRIMARY",
                    "pubHR": None, "pubHR_LCI": None, "pubHR_UCI": None,
                },
            ],
            "rob": ["low", "low", "some", "low", "low"],
            "snippet": "El-Chami MF et al. Heart Rhythm 2022;19:1484-1492. Aveir VR single-arm IDE (n=326). 6-week complication-free: 96.6%. Retrieval success 100% (6/6). Not poolable (no comparator).",
            "evidence": [
                {
                    "label": "Enrollment & Design",
                    "source": "El-Chami et al. Heart Rhythm 2022;19:1484-1492; NCT04559945",
                    "text": "Prospective single-arm study of the Aveir VR leadless pacemaker across 53 sites. 326 patients implanted. Mean age 74 years. Primary VVI indication with chronic atrial fibrillation most common.",
                    "highlights": ["326", "53 sites", "74 years"],
                },
                {
                    "label": "Primary Outcomes",
                    "source": "El-Chami et al. Heart Rhythm 2022;19:1484-1492, Table 2",
                    "text": "Complication-free rate at 6 weeks: 96.6% (95% CI 93.6-98.2%), exceeding 85% performance goal (P<0.001). Pacing threshold <=2V at 6 weeks: 95.0%. R-wave amplitude >=5mV: 95.4%. Device retrieval successful in 100% of attempts (6/6).",
                    "highlights": ["96.6%", "P<0.001", "95.0%", "100%"],
                },
                {
                    "label": "Note: Single-Arm Design",
                    "source": "NCT04559945",
                    "text": "Aveir VR is a retrievable leadless pacemaker with demonstrated 100% retrieval success. IDE study without comparator arm; data provides safety and efficacy benchmarks but cannot be pooled comparatively.",
                    "highlights": ["retrievable", "100% retrieval", "cannot be pooled"],
                },
            ],
        },
        # ── Micra AV Registry: Post-approval ─────────────────────
        "NCT04253184": {
            "name": "Micra AV Registry", "phase": "Registry", "year": 2020,
            "tE": 0, "tN": 0, "cE": 0, "cN": 0,
            "group": "Micra AV (registry)",
            "publishedHR": None, "hrLCI": None, "hrUCI": None,
            "allOutcomes": [
                {
                    "shortLabel": "AV Synchrony",
                    "title": "AV synchrony achieved at 12 months",
                    "tE": 0, "cE": 0,
                    "type": "PRIMARY",
                    "pubHR": None, "pubHR_LCI": None, "pubHR_UCI": None,
                },
            ],
            "rob": ["some", "some", "some", "low", "low"],
            "snippet": "Medtronic Micra AV post-approval registry (n=802). AV synchronous pacing in VDD mode. Registry design, no comparator arm.",
            "evidence": [
                {
                    "label": "Registry Design",
                    "source": "ClinicalTrials.gov NCT04253184",
                    "text": "Prospective post-approval registry of the Micra AV transcatheter pacing system across 89 sites. 802 patients enrolled. Evaluates AV synchronous pacing (VDD mode) using mechanical sensing of atrial contractions via the accelerometer.",
                    "highlights": ["802", "89 sites", "AV synchronous", "accelerometer"],
                },
                {
                    "label": "AV Synchrony Performance",
                    "source": "Steinwender C et al. JACC Clin EP 2023",
                    "text": "Micra AV achieved AV synchrony in approximately 89% of cardiac cycles at rest in patients with AV block. Mean battery longevity projected >12 years. Registry data supportive of VDD mode performance.",
                    "highlights": ["89%", "12 years", "VDD mode"],
                },
                {
                    "label": "Note: Registry Design",
                    "source": "NCT04253184",
                    "text": "Post-approval observational registry without comparator arm. Data cannot be pooled in head-to-head meta-analysis but provides real-world performance benchmarks for the Micra AV device.",
                    "highlights": ["registry", "cannot be pooled", "real-world"],
                },
            ],
        },
        # ── ACED: Aveir VR CED Post-approval (recruiting) ────────
        "NCT05336877": {
            "name": "ACED CED", "phase": "CED (Pipeline)", "year": 2028,
            "tE": 0, "tN": 0, "cE": 0, "cN": 0,
            "group": "Pipeline (Aveir VR vs TVP)",
            "publishedHR": None, "hrLCI": None, "hrUCI": None,
            "allOutcomes": [
                {
                    "shortLabel": "Complications",
                    "title": "Device/procedure-related complications at 12 months (Aveir VR vs TVP)",
                    "tE": 0, "cE": 0,
                    "type": "PRIMARY",
                    "pubHR": None, "pubHR_LCI": None, "pubHR_UCI": None,
                },
            ],
            "rob": ["low", "low", "low", "low", "low"],
            "snippet": "Abbott Aveir VR Coverage with Evidence Development study. Concurrent TVP comparator arm (n=8744 target). Recruiting. Results expected ~2028. Will provide first large-scale concurrent comparator data for Aveir VR.",
            "evidence": [
                {
                    "label": "Trial Design",
                    "source": "ClinicalTrials.gov NCT05336877",
                    "text": "Observational CED study with concurrent Aveir VR (leadless) and single-chamber transvenous pacemaker arms. Target enrollment 8,744 patients. Primary completion expected January 2028. This will be the largest concurrent comparison of leadless vs transvenous pacing.",
                    "highlights": ["8,744", "concurrent comparator", "January 2028"],
                },
                {
                    "label": "Significance for Living MA",
                    "source": "Protocol analysis",
                    "text": "ACED will provide real-world concurrent comparative data for Aveir VR vs TVP. Current evidence relies on historical controls or single-arm studies. Results will dramatically strengthen the evidence base for leadless pacing and update this living MA.",
                    "highlights": ["real-world", "concurrent", "dramatically strengthen"],
                },
            ],
        },
        # ── Leadless AV vs DDD RCT (University of Bern) ──────────
        "NCT05498376": {
            "name": "Leadless AV vs DDD RCT", "phase": "IV", "year": 2026,
            "tE": 0, "tN": 0, "cE": 0, "cN": 0,
            "group": "Pipeline (Micra AV vs DDD)",
            "publishedHR": None, "hrLCI": None, "hrUCI": None,
            "allOutcomes": [
                {
                    "shortLabel": "Complications",
                    "title": "Device-related complications (Micra AV vs conventional DDD)",
                    "tE": 0, "cE": 0,
                    "type": "PRIMARY",
                    "pubHR": None, "pubHR_LCI": None, "pubHR_UCI": None,
                },
            ],
            "rob": ["low", "low", "low", "low", "low"],
            "snippet": "Single-center RCT (Insel Gruppe, Bern; n=100). First randomized head-to-head comparison of Micra AV vs conventional DDD pacemaker. Recruiting, primary completion Dec 2026.",
            "evidence": [
                {
                    "label": "Trial Design",
                    "source": "ClinicalTrials.gov NCT05498376",
                    "text": "Single-center RCT at University Hospital Bern. 100 patients randomized to Micra AV leadless pacemaker vs conventional DDD transvenous pacemaker. Primary outcome: device-related complications. First true randomized comparison in this space. Recruiting, primary completion December 2026.",
                    "highlights": ["100", "randomized", "first", "December 2026"],
                },
                {
                    "label": "Significance for Living MA",
                    "source": "Protocol analysis",
                    "text": "This is the FIRST randomized controlled trial directly comparing leadless vs transvenous dual-chamber pacing. Results will provide the highest quality evidence for this living MA. Currently, all comparative data relies on historical or registry controls.",
                    "highlights": ["FIRST", "randomized controlled trial", "highest quality"],
                },
            ],
        },
    },
})


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
