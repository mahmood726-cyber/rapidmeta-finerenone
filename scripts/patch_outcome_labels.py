"""
Refactor outcomeLabel(key) and the inline `const outcomeNames = {...}` literal
across all pairwise reviews so both derive from realData[*].allOutcomes (the
per-dashboard outcome metadata) instead of a hardcoded cardiology map.

Replaces:
- `outcomeLabel(key) { const map = {...}; return map[key] ?? String(key ?? 'default'); }`
  -> three new methods: _derivedOutcomeMap, outcomeLabel (data-driven), _outcomeNamesMap
- `const outcomeNames = { default: [...], MACE: [...], ... };`
  -> `const outcomeNames = RapidMeta._outcomeNamesMap();`

Idempotent: skips files that already contain _derivedOutcomeMap.

Usage:
    python scripts/patch_outcome_labels.py --dry-run
    python scripts/patch_outcome_labels.py
"""
import argparse, os, re, sys

ROOT = os.environ.get('RAPIDMETA_REPO_ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

NEW_BLOCK = """// Walk realData[*].allOutcomes once; dedupe by shortLabel; centralise the
            // per-trial outcome metadata so outcomeLabel + _outcomeNamesMap produce
            // dashboard-correct labels from the same source of truth that drives the
            // analysis pipeline. Replaces the prior hardcoded cardiology map.
            _derivedOutcomeMap() {
                const map = new Map();
                const real = this.realData ?? {};
                for (const id of Object.keys(real)) {
                    const outcomes = real[id]?.allOutcomes ?? [];
                    for (const o of outcomes) {
                        const key = o.shortLabel;
                        if (!key) continue;
                        if (!map.has(key)) {
                            map.set(key, { shortLabel: key, title: o.title ?? key, type: o.type ?? '', count: 0 });
                        }
                        map.get(key).count += 1;
                    }
                }
                return map;
            },


            outcomeLabel(key) {
                const m = this._derivedOutcomeMap();
                if (key === 'default' || key == null || key === '') {
                    const entries = [...m.values()].sort((a, b) => b.count - a.count);
                    if (entries.length > 0) return entries[0].title;
                    return 'Primary outcome';
                }
                const e = m.get(String(key));
                if (e) return e.title;
                return String(key);
            },


            // Replaces the previous inline cardiology-flavoured `outcomeNames` literal
            // at the SoF render site. Shape: { [shortLabel]: [shortLabel, title], default: [...] }
            _outcomeNamesMap() {
                const map = this._derivedOutcomeMap();
                const out = {};
                for (const e of map.values()) {
                    out[e.shortLabel] = [e.shortLabel, e.title];
                }
                const entries = [...map.values()].sort((a, b) => b.count - a.count);
                if (entries.length > 0) {
                    out.default = [entries[0].shortLabel, entries[0].title];
                } else {
                    out.default = ['Primary outcome', 'Trial-registered primary outcome'];
                }
                return out;
            }"""

OUTCOME_NAMES_REPLACEMENT = """// Data-driven from realData[*].allOutcomes (per-dashboard outcome metadata).
                // Replaces a hardcoded cardiology-flavoured map that leaked HF/MI/stroke
                // descriptors into non-cardio dashboards' SoF table.
                const outcomeNames = RapidMeta._outcomeNamesMap();"""


def find_block_end(src, start):
    """Given an offset of an opening { (or anywhere inside a function header),
    walk forward and return the offset of the matching closing }."""
    depth = 0
    started = False
    for j in range(start, len(src)):
        c = src[j]
        if c == '{':
            depth += 1
            started = True
        elif c == '}':
            depth -= 1
            if started and depth == 0:
                return j
    return -1


def patch_outcome_label(src):
    """Replace the existing outcomeLabel(key) block with the new 3-method block.
    Returns (new_src, status)."""
    if '_derivedOutcomeMap()' in src:
        return src, 'SKIP_already_refactored'
    i = src.find('outcomeLabel(key) {')
    if i < 0:
        return src, 'SKIP_no_outcomeLabel'
    brace_open = src.find('{', i)
    end = find_block_end(src, brace_open)
    if end < 0:
        return src, 'SKIP_unbalanced_braces'
    # The block is: from `outcomeLabel(key) {` ... `}`
    # Replace with NEW_BLOCK which starts with a comment then defines the 3 methods.
    # We do NOT include the trailing comma — that's already in src right after `}`.
    new_src = src[:i] + NEW_BLOCK + src[end+1:]
    return new_src, 'APPLIED'


def patch_outcome_names(src):
    """Replace `const outcomeNames = {...};` literal with a call to _outcomeNamesMap."""
    if 'const outcomeNames = RapidMeta._outcomeNamesMap()' in src:
        return src, 'SKIP_already_refactored'
    i = src.find('const outcomeNames = {')
    if i < 0:
        return src, 'SKIP_no_outcomeNames_literal'
    brace_open = src.find('{', i)
    end = find_block_end(src, brace_open)
    if end < 0:
        return src, 'SKIP_unbalanced_braces'
    semi = src.find(';', end)
    if semi < 0 or semi - end > 5:
        return src, 'SKIP_no_trailing_semicolon'
    new_src = src[:i] + OUTCOME_NAMES_REPLACEMENT + src[semi+1:]
    return new_src, 'APPLIED'


def patch_file(path, dry=False):
    src = open(path, 'r', encoding='utf-8').read()
    original = src
    log = []
    src, s1 = patch_outcome_label(src)
    log.append(f'  outcomeLabel: {s1}')
    src, s2 = patch_outcome_names(src)
    log.append(f'  outcomeNames: {s2}')
    changed = src != original
    if changed and not dry:
        open(path, 'w', encoding='utf-8').write(src)
    return changed, log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--include-nma', action='store_true', help='include _NMA_REVIEW.html files')
    args = ap.parse_args()
    print(f'Mode: {"DRY-RUN" if args.dry_run else "APPLY"}')

    files = sorted([f for f in os.listdir(ROOT)
                    if f.endswith('_REVIEW.html')
                    and 'DTA' not in f
                    and not f.endswith('.bak.html')
                    and (args.include_nma or 'NMA' not in f)])

    summary = {'changed': 0, 'unchanged': 0, 'errors': 0}
    for fname in files:
        path = os.path.join(ROOT, fname)
        try:
            changed, log = patch_file(path, dry=args.dry_run)
            tag = 'CHANGED' if changed else 'no-op'
            print(f'\n[{tag}] {fname}')
            for line in log:
                print(line)
            summary['changed' if changed else 'unchanged'] += 1
        except Exception as e:
            print(f'\n[ERROR] {fname}: {e}')
            summary['errors'] += 1
    print(f'\nSummary: {summary}')
    return 0 if summary['errors'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
