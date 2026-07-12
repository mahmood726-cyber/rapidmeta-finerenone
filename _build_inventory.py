#!/usr/bin/env python
"""Ground-truth inventory of living-meta apps actually present on disk.

Real app = *_AUTO_FULL_REVIEW.html OR plain *_REVIEW.html (NOT *_AUTO_REVIEW.html,
which are <5KB redirect stubs pointing at their _AUTO_FULL twin).
"""
import os, re, glob, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.abspath(__file__))
TITLE_RE = re.compile(r'<title>(.*?)</title>', re.I | re.S)
REDIRECT_RE = re.compile(r'rm-orphan-redirect|http-equiv="refresh"', re.I)

def is_app(fn):
    if fn.endswith('_AUTO_REVIEW.html'):
        return False
    return fn.endswith('_REVIEW.html')  # incl _AUTO_FULL_REVIEW.html and plain _REVIEW.html

apps = []
redirect_like = []
for path in sorted(glob.glob(os.path.join(ROOT, '*_REVIEW.html'))):
    fn = os.path.basename(path)
    if not is_app(fn):
        continue
    size = os.path.getsize(path)
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        head = f.read(8000)
    if REDIRECT_RE.search(head):
        redirect_like.append((fn, size))
        continue
    m = TITLE_RE.search(head)
    title = re.sub(r'\s+', ' ', m.group(1)).strip() if m else ''
    nma = bool(re.search(r'\bNMA\b|network meta', title, re.I) or '_NMA_' in fn or fn.endswith('_NMA_REVIEW.html'))
    apps.append({'file': fn, 'title': title, 'size': size, 'nma': nma})

# counts
n = len(apps)
n_nma = sum(1 for a in apps if a['nma'])
n_pw = n - n_nma
n_notitle = sum(1 for a in apps if not a['title'])
n_small = sum(1 for a in apps if a['size'] < 50000)

print(f"TRUE APP COUNT: {n}")
print(f"  pairwise: {n_pw}")
print(f"  network (NMA): {n_nma}")
print(f"  missing <title>: {n_notitle}")
print(f"  small (<50KB): {n_small}")
print(f"  app files that look like redirects (excluded): {len(redirect_like)}")
for fn, sz in redirect_like[:20]:
    print(f"    REDIRECT-LIKE APP FILE: {fn} ({sz}B)")

json.dump(apps, open(os.path.join(ROOT, '_inventory.json'), 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
print(f"\nWrote _inventory.json ({n} apps)")

# PI3K check
for a in apps:
    if 'PI3K' in a['file'] or 'PI3K' in a['title'].upper():
        print(f"PI3K APP: {a['file']} -> {a['title']!r} (nma={a['nma']})")
