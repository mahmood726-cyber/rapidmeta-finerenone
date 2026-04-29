"""
Self-test for scripts/clone_dashboard.py.

Validates that a synthetic clone produces a structurally-valid dashboard:
all anchors retemplated, JS braces balanced, no leftover source-template
identifiers in the canonical fields, output file size within reasonable
bounds.

Run:
    python scripts/test_clone_dashboard.py
Exit 0 = pass, 1 = fail.

Uses VOCLOSPORIN_LN_REVIEW.html as the base template (small, clean,
single-trial). Writes to a temp output that's deleted after.
"""
from __future__ import annotations
import json, os, re, subprocess, sys, tempfile

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get('RAPIDMETA_REPO_ROOT', os.path.dirname(SCRIPTS_DIR))


def make_synthetic_config(out_path):
    return {
        "base": os.path.join(ROOT, "VOCLOSPORIN_LN_REVIEW.html"),
        "out":  out_path,
        "title": "RapidMeta TestSuite | Synthetic Clone Self-Test v0.1",
        "hero_h2": "Synthetic Drug X in Synthetic Disease Y",
        "nyt_headline": "The Synthetic Drug X Evidence",
        "auto_include_ncts": ["NCT99999999"],
        "nct_acronyms": {"NCT99999999": "TEST-1"},
        "localstorage_old": "rapid_meta_voclosporin_ln_v1_0",
        "localstorage_new": "rapid_meta_synthetic_test_v1_0",
        "pico": {
            "pop": "Synthetic test population",
            "int": "Synthetic Drug X 100 mg PO QD",
            "comp": "Placebo",
            "out": "Synthetic primary outcome",
            "subgroup": "Test stratum"
        },
        "real_data_entries": [{
            "nct": "NCT99999999",
            "name": "TEST-1",
            "pmid": "00000000",
            "phase": "III",
            "year": 2099,
            "tE": 0, "tN": 100, "cE": 0, "cN": 100,
            "group": "Synthetic test trial",
            "publishedHR": 0.5, "hrLCI": 0.3, "hrUCI": 0.8,
            "allOutcomes": [
                {"shortLabel": "MACE", "title": "Synthetic primary outcome (HR)",
                 "tE": 0, "cE": 0, "type": "PRIMARY", "matchScore": 95,
                 "effect": 0.5, "lci": 0.3, "uci": 0.8, "estimandType": "HR"}
            ],
            "rob": ["low", "low", "low", "low", "low"],
            "snippet": "Source: synthetic test data.",
            "sourceUrl": "https://example.com/test",
            "evidence": []
        }],
        "extra_replaces": []
    }


def find_block_end(text, start_brace):
    depth = 0
    started = False
    for j in range(start_brace, len(text)):
        c = text[j]
        if c == '{': depth += 1; started = True
        elif c == '}':
            depth -= 1
            if started and depth == 0: return j
    return -1


def run_tests():
    failures = []

    # Stage 1: write synthetic config + run cloner
    with tempfile.TemporaryDirectory() as tmp:
        out_path = os.path.join(tmp, 'TEST_SYNTHETIC_REVIEW.html')
        config_path = os.path.join(tmp, 'test_config.json')
        config = make_synthetic_config(out_path)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f)

        cloner = os.path.join(SCRIPTS_DIR, 'clone_dashboard.py')
        result = subprocess.run(
            [sys.executable, cloner, '--config', config_path],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            failures.append(f'Cloner exited {result.returncode}: {result.stderr[:400]}')
            return failures

        # Stage 2: read output and run structural checks
        if not os.path.exists(out_path):
            failures.append(f'Output file not created at {out_path}')
            return failures
        try:
            src = open(out_path, 'r', encoding='utf-8').read()
        except OSError as e:
            failures.append(f'Could not read output: {e}')
            return failures

        # File-size sanity
        size = len(src)
        if size < 500_000 or size > 5_000_000:
            failures.append(f'Output file size {size} bytes outside reasonable range')

        # Structural: required anchors
        required = [
            ('Title retemplated',     '<title>RapidMeta TestSuite | Synthetic'),
            ('Hero retemplated',      'Synthetic Drug X in Synthetic Disease Y'),
            ('NYT headline',          'The Synthetic Drug X Evidence'),
            ('AUTO_INCLUDE applied',  "AUTO_INCLUDE_TRIAL_IDS = new Set(['NCT99999999'])"),
            ('nctAcronyms applied',   "'NCT99999999': 'TEST-1'"),
            ('localStorage migrated', 'rapid_meta_synthetic_test_v1_0'),
            ('PICO pop',              'Synthetic test population'),
            ('PICO int',              "'Synthetic Drug X 100 mg PO QD'"),
            ('realData NCT key',      "'NCT99999999':"),
            ('realData name field',   "name: 'TEST-1'"),
        ]
        for label, needle in required:
            if needle not in src:
                failures.append(f'Missing anchor: {label} ({needle[:60]!r})')

        # Anti-leak: source-template identifiers should NOT remain in the
        # canonical fields (these would mean the cloner missed a replacement)
        anti_leaks = [
            ('Original VOCLOSPORIN_LN title',       'Voclosporin (Calcineurin Inhibitor)'),
            ('Original AURORA NCT in nctAcronyms',  "'NCT03021499': 'AURORA"),
            ('Original protocol drug',              "int: 'Voclosporin"),
            ('Original localStorage key',           'rapid_meta_voclosporin_ln_v1_0'),
        ]
        for label, needle in anti_leaks:
            if needle in src:
                failures.append(f'Source-template leak: {label} ({needle!r})')

        # Brace balance: walk the entire file's <script> blocks and confirm
        # each top-level object literal balances. Cheap proxy: find each
        # `realData: {` and confirm it closes properly.
        i = src.find('realData: {')
        if i < 0:
            failures.append('realData: { block not found in output')
        else:
            end = find_block_end(src, src.find('{', i))
            if end < 0:
                failures.append('realData block braces unbalanced')

        # Plotly script reference still present (sanity for any rendering)
        if 'plotly' not in src.lower():
            failures.append('Plotly reference missing — base template was wrong?')

    return failures


def main():
    print('=== clone_dashboard self-test ===')
    failures = run_tests()
    if failures:
        print(f'FAILED ({len(failures)} issue(s)):')
        for f in failures:
            print(f'  - {f}')
        return 1
    print('PASSED — clone produces structurally-valid dashboard')
    return 0


if __name__ == '__main__':
    sys.exit(main())
