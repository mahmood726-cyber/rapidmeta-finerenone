"""
Migrate localStorage keys to be filename-unique. Fixes the clone-heritage
collision bug where child dashboards inherited their template's localStorage
keys (e.g. VOCLOSPORIN_LN used `rapid_meta_anifrolumab_sle_*` from its
ANIFROLUMAB clone heritage; opening both dashboards on github.io would
have them stomp each other's persisted state).

Strategy:
  1. For each *_REVIEW.html, derive the canonical key prefix from the
     filename: rapid_meta_{file_stem.lower()}
  2. Find every localStorage key in the file that doesn't already match
     that prefix (with optional _vX_Y or _theme suffix).
  3. Replace the OFFENDING prefix with the canonical one. Files that already
     use abbreviated-but-unique prefixes (e.g. AFLIBERCEPT_HD's `aflib_hd`)
     are left alone if their prefix isn't shared with any other file.

Idempotent.

Triggering incident: VOCLOSPORIN_LN -> SPARSENTAN_IGAN clone uncovered the
pattern; full audit found 18 prefix collisions across 38 file-pairings.
"""
import argparse, os, re, sys
from collections import defaultdict

ROOT = os.environ.get('RAPIDMETA_REPO_ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LS_RE = re.compile(r"rapid_meta_\w+")


def file_to_canonical_prefix(fname):
    stem = fname.replace('_REVIEW.html', '').lower()
    return f'rapid_meta_{stem}'


def collect_keys():
    """{prefix: set(files)} for all rapid_meta_* keys in any review file."""
    result = defaultdict(set)
    files = sorted(f for f in os.listdir(ROOT) if f.endswith('_REVIEW.html') and not f.endswith('.bak.html'))
    for fname in files:
        src = open(os.path.join(ROOT, fname), 'r', encoding='utf-8').read()
        for m in LS_RE.finditer(src):
            full = m.group(0)
            prefix = re.sub(r'_(theme|v\d+_\d+)$', '', full)
            result[prefix].add(fname)
    return result, files


def patch_file(path, fname, key_to_files, dry=False):
    """For this file, find any rapid_meta_ prefix that isn't its canonical
    prefix AND is shared with at least one other file (= collision). Migrate
    those keys to the canonical prefix."""
    canonical = file_to_canonical_prefix(fname)
    src = open(path, 'r', encoding='utf-8').read()
    original = src

    # Identify offending prefixes in this file
    file_prefixes = set()
    for m in LS_RE.finditer(src):
        prefix = re.sub(r'_(theme|v\d+_\d+)$', '', m.group(0))
        file_prefixes.add(prefix)

    migrations = []
    for prefix in file_prefixes:
        if prefix == canonical:
            continue
        # Only migrate if this prefix is shared with at least one other file
        # (i.e. it's a real collision, not a unique abbreviation)
        if prefix not in key_to_files or len(key_to_files[prefix]) <= 1:
            continue
        # Migrate this prefix -> canonical in the file's source
        src = src.replace(prefix, canonical)
        migrations.append(prefix)

    if src == original:
        return False, []
    if not dry:
        open(path, 'w', encoding='utf-8').write(src)
    return True, migrations


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    print(f'Mode: {"DRY-RUN" if args.dry_run else "APPLY"}')

    key_to_files, files = collect_keys()
    summary = {'changed': 0, 'unchanged': 0}
    for fname in files:
        path = os.path.join(ROOT, fname)
        try:
            changed, migrations = patch_file(path, fname, key_to_files, dry=args.dry_run)
            if changed:
                print(f'  [CHANGED] {fname}')
                for m in migrations:
                    print(f'    {m} -> rapid_meta_{fname.replace("_REVIEW.html","").lower()}')
                summary['changed'] += 1
            else:
                summary['unchanged'] += 1
        except Exception as e:
            print(f'  [ERROR] {fname}: {e}')
    print(f'\nSummary: {summary}')


if __name__ == '__main__':
    sys.exit(main())
