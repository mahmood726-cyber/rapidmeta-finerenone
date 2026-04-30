"""
Fix the residual valsartan/sacubitril filename leak across cloned dashboards.

The previous fix (commit aea1768) replaced the `app:` field in
exportReviewPack(). But filenames inside the export/download paths still
carry the original sacubitril/valsartan slug -- meaning user-clicked
downloads land as `sacubitril-valsartan_v12_capsule.zip`,
`sacubitril/valsartan_meta_analysis_v11.json`, etc., regardless of the
actual disease.

This script derives a per-file slug from the filename
(`IL23_PSORIASIS_REVIEW.html` -> `il23_psoriasis`) and replaces every
hardcoded sacubitril-valsartan filename with that slug.

Replacements:
  'sacubitril-valsartan_v12_capsule.zip'              -> '<slug>_v12_capsule.zip'
  'sacubitril/valsartan_meta_analysis_v11.json'       -> '<slug>_meta_analysis_v11.json'
  'sacubitril\\/valsartan_meta_analysis_data.csv'      -> '<slug>_meta_analysis_data.csv'
  'sacubitril/valsartan_validation_v11.py'            -> '<slug>_validation_v11.py'
  'sacubitril\\/valsartan_validation_v11.py'           -> '<slug>_validation_v11.py'
  'sacubitril\\/valsartan_run_artifact_*'              -> '<slug>_run_artifact_*'
  'sacubitril\\/valsartan_forest.png'                  -> '<slug>_forest.png'

Skipped: ARNI_HF_REVIEW.html (the legitimate sacubitril/valsartan dashboard)
+ frozen submission snapshots.

Idempotent: skipped if no `sacubitril-valsartan` or `sacubitril/valsartan`
download / filename remains.

Usage: python scripts/fix_valsartan_filename_leak.py [--dry-run]
"""
import argparse
import io
import os
import re
import sys

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.environ.get(
    'RAPIDMETA_REPO_ROOT',
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)

SKIP = {'ARNI_HF_REVIEW.html'}

# Regex catches both `sacubitril-valsartan` and `sacubitril/valsartan` (with
# optional JS-escaped backslash) as a "drug slug" in filename / artifact
# string contexts. We match the slug only; the surrounding suffix remains.
SLUG_RE = re.compile(r"sacubitril(?:-|\\/|/)valsartan")


def derive_slug(fname: str) -> str:
    base = fname.replace('_REVIEW.html', '').lower()
    return base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    print(f'Mode: {"DRY-RUN" if args.dry_run else "APPLY"}')
    files = sorted(
        f for f in os.listdir(ROOT)
        if f.endswith('_REVIEW.html')
        and not f.endswith('.bak.html')
        and f not in SKIP
    )
    summary = {'changed': 0, 'unchanged': 0}
    for fname in files:
        path = os.path.join(ROOT, fname)
        src = open(path, 'r', encoding='utf-8').read()
        if not SLUG_RE.search(src):
            summary['unchanged'] += 1
            continue
        slug = derive_slug(fname)
        new = SLUG_RE.sub(slug, src)
        if new != src:
            if not args.dry_run:
                open(path, 'w', encoding='utf-8').write(new)
            summary['changed'] += 1
        else:
            summary['unchanged'] += 1
    print(f'Summary: {summary}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
