"""
Fix the cloned-dashboard leak: every clone of ARNI_HF carries
`app: 'RapidMeta Sacubitril/Valsartan v12.0'` inside exportReviewPack().
That string ends up embedded in user-exported JSON — leaking the wrong
disease across 87 unrelated topic dashboards (psoriasis, oncology, etc.).

Fix: replace the string with a per-file app name derived from the file's
own <title> element. Idempotent — only runs replace if the leaked string
is still present.

Skip ARNI_HF_REVIEW.html (the legitimate sacubitril/valsartan dashboard)
and any nested copies under e156-submission/.

Usage: python scripts/fix_app_metadata_leak.py [--dry-run]
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

LEAK = "app: 'RapidMeta Sacubitril/Valsartan v12.0'"
SKIP = {'ARNI_HF_REVIEW.html'}
TITLE_RE = re.compile(r'<title>\s*(.*?)\s*</title>', re.IGNORECASE | re.DOTALL)


def derive_app_name(html: str, fallback: str) -> str:
    m = TITLE_RE.search(html)
    if not m:
        return fallback
    title = m.group(1).strip()
    title = title.replace("'", "’")
    return title


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
    summary = {'changed': 0, 'unchanged': 0, 'no_title': 0}
    for fname in files:
        path = os.path.join(ROOT, fname)
        src = open(path, 'r', encoding='utf-8').read()
        if LEAK not in src:
            summary['unchanged'] += 1
            continue
        fallback = f"RapidMeta {fname.replace('_REVIEW.html', '')}"
        app_name = derive_app_name(src, fallback)
        if app_name == fallback:
            summary['no_title'] += 1
        new = f"app: '{app_name}'"
        out = src.replace(LEAK, new)
        if not args.dry_run:
            open(path, 'w', encoding='utf-8').write(out)
        summary['changed'] += 1
        print(f'  {fname}: -> {app_name}')
    print(f'Summary: {summary}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
