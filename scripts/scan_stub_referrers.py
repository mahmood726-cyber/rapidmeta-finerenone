#!/usr/bin/env python
"""Enumerate every surface referring to the 47 orphan stubs, by SEARCHING.

Reads bytes and decodes with errors='replace': a NUL byte would flip grep to
binary mode and make it report nothing, which is the failure mode that looks
like good news. Reports the denominator (files opened, files skipped and why).
"""
import os, json, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT_EXT = {'.html', '.json', '.md', '.xml', '.txt', '.js', '.csv', '.yml', '.yaml'}
SKIP_DIRS = {'.git', 'node_modules', 'pytest_tmp', 'build-artefacts'}

stubs = [l.strip() for l in open(os.path.join(ROOT, '_stubs47.txt'),
                                encoding='utf-8', errors='replace') if l.strip()]
bare = {s[:-len('.html')]: s for s in stubs}
per = {s: [] for s in stubs}
scanned = 0
skipped = []

for rt, dirs, fs in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for f in fs:
        p = os.path.join(rt, f)
        rel = os.path.relpath(p, ROOT).replace(os.sep, '/')
        if os.path.splitext(f)[1].lower() in TEXT_EXT:
            try:
                data = open(p, 'rb').read()
            except OSError as e:
                skipped.append({'file': rel, 'why': str(e)}); continue
            scanned += 1
            t = data.decode('utf-8', 'replace')
            if '_AUTO_REVIEW' not in t:       # cheap prefilter
                continue
            for b, s in bare.items():
                if b in t:
                    per[s].append(rel)
        else:
            skipped.append({'file': rel, 'why': 'non-text extension'})

refs = sorted({x for v in per.values() for x in v})
non_sitemap = {s: [x for x in v if x != 'sitemap.xml' and x not in stubs]
               for s, v in per.items()}
out = {
    'files_scanned': scanned,
    'files_skipped_count': len(skipped),
    'skipped_sample': skipped[:5],
    'per_stub': per,
    'referring_files': refs,
    'total_referring_files': len(refs),
    'stubs_with_zero_referrers_outside_sitemap_and_self':
        sorted(s for s, v in non_sitemap.items() if not v),
    'referrers_outside_sitemap_and_self':
        sorted({x for v in non_sitemap.values() for x in v}),
}
os.makedirs(os.path.join(ROOT, 'outputs'), exist_ok=True)
with open(os.path.join(ROOT, 'outputs', 'stub47_referrers.json'), 'w',
          encoding='utf-8', newline='') as fh:
    json.dump(out, fh, indent=1)
print('files scanned            :', scanned)
print('files skipped (non-text) :', len(skipped))
print('distinct referring files :', len(refs))
print('referrers OUTSIDE sitemap/self:', out['referrers_outside_sitemap_and_self'])
print('stubs with no such referrer   :',
      len(out['stubs_with_zero_referrers_outside_sitemap_and_self']), 'of', len(stubs))
