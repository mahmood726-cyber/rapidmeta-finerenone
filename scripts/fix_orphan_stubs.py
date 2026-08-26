#!/usr/bin/env python
"""Repair live breakage on the served site. NO DELETIONS.

Two defects, both confirmed over HTTP by scripts/check_served_links.py:
  A) 47 redirect stubs serve 200 then redirect to a target that 404s.
     Their targets were hard-deleted by 2a011cdfe (2026-06-07) because the
     underlying analysis had exactly one trial (k=1, not a meta-analysis).
     That commit removed the index cards and most sitemap entries but left
     these stubs pointing at nothing.
     FIX: rewrite each stub as an honest, noindex withdrawal notice (200).
  B) 163 sitemap entries point at files that do not exist -> hard 404.
     FIX: drop non-resolving entries, and drop the withdrawn pages too
     (a withdrawn analysis should not be advertised).

Idempotent. Byte-safe (newline='' on every write). Run --apply to act.
"""
import os, re, sys, html
from urllib.parse import urlsplit, unquote

SITE = '/rapidmeta-finerenone/'
WITHDRAWN_MARK = 'rm-withdrawn-analysis'
STUB_RE = re.compile(r'rm-orphan-redirect"\s+content="([^"]+)"')
TITLE_RE = re.compile(r'<title>(.*?)\s*-\s*opening the full RapidMeta', re.S | re.I)

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<meta name="{mark}" content="k=1; withdrawn 2026-06-07 in commit 2a011cdfe">
<title>{topic} - analysis withdrawn | RapidMeta</title>
<style>body{{font:16px/1.6 system-ui,Segoe UI,Arial,sans-serif;margin:3rem auto;max-width:42rem;padding:0 1rem;color:#1f2937}}
a{{color:#b45309;font-weight:600}}h1{{font-size:1.25rem}}
.note{{background:#fef3c7;border-left:4px solid #f0b429;padding:.75rem 1rem;margin:1.25rem 0}}</style>
</head>
<body>
<h1>{topic} &mdash; this analysis was withdrawn</h1>
<div class="note">
<p>This page previously presented <strong>{topic}</strong> as a meta-analysis. It was withdrawn on
<strong>7 June 2026</strong> because a poolability audit found it contained <strong>exactly one trial</strong>.</p>
<p>A meta-analysis requires at least two trials measuring a shared outcome. A single-trial page does not
meet that definition, so it was removed rather than corrected.</p>
</div>
<p>The URL is kept so existing links do not break. There is no replacement analysis for this topic.</p>
<p><a href="index.html">Return to the RapidMeta index</a></p>
</body>
</html>
"""

def orphan_stubs():
    out = []
    # Positive property: iterate the HTML pages, rather than excluding
    # everything that lacks the extension. (pre-commit exclusion-by-absence gate)
    for f in sorted(p for p in os.listdir('.') if p.endswith('.html')):
        t = open(f, 'rb').read().decode('utf-8', 'replace')
        if WITHDRAWN_MARK in t:
            continue  # already fixed -- idempotent
        m = STUB_RE.search(t)
        if m and not os.path.isfile(m.group(1)):
            tm = TITLE_RE.search(t)
            topic = html.escape(tm.group(1).strip()) if tm else f.replace('_AUTO_REVIEW.html', '').replace('_', ' ').title()
            out.append((f, topic))
    return out

def sitemap_prune(drop):
    src = open('sitemap.xml', encoding='utf-8', errors='replace').read()
    blocks = re.findall(r'<url>.*?</url>\s*', src, re.S)
    kept, removed = [], []
    for b in blocks:
        m = re.search(r'<loc>\s*([^<]+?)\s*</loc>', b)
        if not m:
            kept.append(b); continue
        p = unquote(urlsplit(m.group(1)).path)
        if p.startswith(SITE):
            p = p[len(SITE):]
        p = p.lstrip('/')
        # The site ROOT has an empty path and is served by index.html.
        # os.path.isfile('') is False, so without this guard the homepage
        # entry would be dropped. Caught by an off-by-one, 2026-08-26.
        if p == '':
            kept.append(b); continue
        if p in drop or not os.path.isfile(p):
            removed.append(p)
        else:
            kept.append(b)
    head = src[:src.index(blocks[0])] if blocks else src
    tail = '</urlset>\n'
    return head + ''.join(kept) + tail, removed

if __name__ == '__main__':
    apply = '--apply' in sys.argv
    stubs = orphan_stubs()
    print(f'orphan stubs to rewrite : {len(stubs)}')
    new_sm, removed = sitemap_prune({s for s, _ in stubs})
    print(f'sitemap entries to drop : {len(removed)}')
    if not apply:
        print('\nDRY RUN. Re-run with --apply.')
        sys.exit(0)
    for f, topic in stubs:
        open(f, 'w', encoding='utf-8', newline='').write(
            TEMPLATE.format(topic=topic, mark=WITHDRAWN_MARK))
    open('sitemap.xml', 'w', encoding='utf-8', newline='').write(new_sm)
    print(f'\nAPPLIED: {len(stubs)} stubs rewritten, {len(removed)} sitemap entries dropped.')
