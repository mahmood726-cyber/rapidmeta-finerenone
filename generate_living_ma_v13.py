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

    # 11. Visual abstract heading
    html = re.sub(
        r'Finerenone in (?:CKD|Heart Failure|Cardiorenal Disease)',
        cfg.get("va_heading", cfg["title_short"]),
        html,
        count=2
    )

    # 12. Drug name references in protocol tables
    html = re.sub(r'\bfinerenone\b(?!_)', cfg.get("drug_name_lower", cfg["title_short"].lower()), html, flags=re.IGNORECASE, count=0)
    # But restore finerenone in localStorage keys (they use underscore)
    html = html.replace(f"rapid_meta_{cfg.get('drug_name_lower', '').replace(' ', '_')}_{storage}", f"rapid_meta_{storage}")

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

    # Div balance
    opens = len(re.findall(r'<div[\s>]', html))
    closes = html.count('</div>')
    if opens != closes:
        errors.append(f"Div imbalance: {opens} opens vs {closes} closes")

    # Script integrity
    if '</script>' in html.split('<script')[1] if '<script' in html else '':
        # Check for literal </script> inside script blocks
        in_script = False
        for line_num, line in enumerate(html.split('\n'), 1):
            if '<script' in line:
                in_script = True
            if in_script and '</script>' in line and '<script' not in line:
                in_script = False
            elif in_script and '</script>' in line:
                errors.append(f"Line {line_num}: literal </script> inside script block")

    # Dangling finerenone references (but allow in code comments)
    finerenone_refs = [(i+1, line.strip()) for i, line in enumerate(html.split('\n'))
                       if 'finerenone' in line.lower()
                       and not line.strip().startswith('//')
                       and not line.strip().startswith('*')
                       and 'v12.0:' not in line
                       and 'v13.0:' not in line
                       and 'localStorage' not in line
                       and '_migrated' not in line]
    if finerenone_refs and cfg["storage_key"] != "finerenone":
        # Only flag if there are many — some may be in evidence text
        code_refs = [r for r in finerenone_refs if 'evidence' not in r[1].lower() and 'source' not in r[1].lower()]
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

APPS = []  # Will be populated by subsequent tasks


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
