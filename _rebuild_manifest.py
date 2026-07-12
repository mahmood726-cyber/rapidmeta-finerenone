#!/usr/bin/env python
"""Rebuild outputs/portfolio_index.json so the dashboard lists EVERY real app.

- Canonical app = *_AUTO_FULL_REVIEW.html OR plain *_REVIEW.html, excluding
  *_AUTO_REVIEW.html redirect stubs AND short twins that have a
  *_REVIEW_FULL_REVIEW.html full version.
- Preserve all stats on the 794 rows already in the manifest (join on file).
- Add a real `title` + `display_topic` to every row (from each app's <title>).
- New rows (apps not yet in manifest) get real title + type, but NULL numeric
  stats -- we never fabricate pooled estimates.
"""
import os, re, glob, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.abspath(__file__))
MAN = os.path.join(ROOT, 'outputs', 'portfolio_index.json')
TITLE_RE = re.compile(r'<title>(.*?)</title>', re.I | re.S)
REDIRECT_RE = re.compile(r'rm-orphan-redirect|http-equiv="refresh"', re.I)

def html_unescape(s):
    for a, b in (('&amp;', '&'), ('&mdash;', '—'), ('&ndash;', '–'), ('&minus;', '−'),
                 ('&rarr;', '→'), ('&beta;', 'β'), ('&alpha;', 'α'), ('&gt;', '>'),
                 ('&lt;', '<'), ('&plusmn;', '±'), ('&deg;', '°'), ('&times;', '×'),
                 ('&#39;', "'"), ('&quot;', '"'), ('&nbsp;', ' ')):
        s = s.replace(a, b)
    return s

def clean_topic(title):
    """Human-friendly topic from the raw <title>."""
    t = html_unescape(title).strip()
    # strip leading "RapidMeta <specialty> | " or "RapidMeta | "
    t = re.sub(r'^RapidMeta\b[^|]*\|\s*', '', t)
    # strip trailing version token  v1.0 / v12.5 / v0.1
    t = re.sub(r'\s*v\d+(\.\d+)?\s*$', '', t)
    # strip trailing "— RapidMeta (audit-first)" / "(audit-first, full-functionality)"
    t = re.sub(r'\s*[—-]\s*RapidMeta.*$', '', t)
    t = re.sub(r'\s*\(audit-first[^)]*\)\s*$', '', t)
    t = re.sub(r'\s*[—-]\s*Living Meta-Analysis.*$', '', t)
    return re.sub(r'\s+', ' ', t).strip() or t

def is_nma(title, fn):
    return bool(re.search(r'\bNMA\b|network meta', title, re.I) or '_NMA_' in fn
                or fn.endswith('_NMA_REVIEW.html') or 'network meta' in title.lower())

# --- gather canonical app files from disk ---
all_files = {os.path.basename(p) for p in glob.glob(os.path.join(ROOT, '*_REVIEW.html'))}
def is_app(fn):
    return fn.endswith('_REVIEW.html') and not fn.endswith('_AUTO_REVIEW.html')

canonical = {}
dropped_twins = []
for fn in sorted(all_files):
    if not is_app(fn):
        continue
    # short twin? (a *_REVIEW.html whose *_REVIEW_FULL_REVIEW.html exists)
    full_twin = fn[:-5] + '_FULL_REVIEW.html'
    if not fn.endswith('_FULL_REVIEW.html') and full_twin in all_files:
        dropped_twins.append(fn)
        continue
    path = os.path.join(ROOT, fn)
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        head = f.read(8000)
    if REDIRECT_RE.search(head):
        continue
    m = TITLE_RE.search(head)
    raw = re.sub(r'\s+', ' ', m.group(1)).strip() if m else fn.replace('_REVIEW.html', '')
    canonical[fn] = {
        'title': html_unescape(raw),
        'topic_name': clean_topic(raw),
        'nma': is_nma(raw, fn),
    }

# --- load existing manifest, preserve stats ---
man = json.load(open(MAN, encoding='utf-8'))
existing = {r['file']: r for r in man['rows']}

rows = []
added, enriched = 0, 0
for fn in sorted(canonical):
    info = canonical[fn]
    if fn in existing:
        r = dict(existing[fn])
        enriched += 1
    else:
        r = {
            'file': fn, 'topic': fn.replace('_REVIEW.html', ''),
            'type': 'NMA' if info['nma'] else 'Pairwise',
            'n_trials': 0, 'n_treatments': None, 'ncts': [], 'k': None,
            'pooled_OR': None, 'ci_low': None, 'ci_high': None, 'I2': None,
            'tau2': None, 'PI_low': None, 'PI_high': None, 'integrity_flags': 0,
            'retro_count': 0, 'overdue_count': 0, 'n_with_baseline': 0,
            'last_modified': None, 'bucket': 'Other', 'stats_pending': True,
        }
        added += 1
    # real title for display + search (this is the fix for the HER2 search miss)
    r['title'] = info['title']
    r['display_name'] = info['topic_name']
    if info['nma']:
        r['type'] = 'NMA'
    rows.append(r)

rows.sort(key=lambda r: r['display_name'].lower())
n_total = len(rows)
n_nma = sum(1 for r in rows if r['type'] == 'NMA')
n_pw = n_total - n_nma
n_rval = sum(1 for r in rows if r.get('pooled_OR') is not None and not r.get('stats_pending'))

out = dict(man)
out['n_total'] = n_total
out['n_pairwise'] = n_pw
out['n_nma'] = n_nma
out['rows'] = rows
json.dump(out, open(MAN, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)

print(f"canonical apps on disk : {len(canonical)}")
print(f"short twins dropped     : {len(dropped_twins)} -> {dropped_twins}")
print(f"rows written            : {n_total}  ({n_pw} pairwise + {n_nma} NMA)")
print(f"  preserved-with-stats  : {enriched}")
print(f"  newly added (no stats): {added}")
pi = [r for r in rows if 'PI3K' in r['file']]
print(f"PI3K row                : {pi[0]['display_name']!r} | title={pi[0]['title']!r}" if pi else "PI3K MISSING")
