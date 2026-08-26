#!/usr/bin/env python
"""HTTP-verify the served site: sitemap resolution + redirect-stub targets.

Deliberately includes CONTROLS that must return 200 and a NEGATIVE control that
must return 404. If the controls do not come out right, the run ABORTS -- a
check that cannot fail is not a check.

Usage: python scripts/check_served_links.py [base_url]
"""
import os, re, sys, json, urllib.request, urllib.error
from urllib.parse import urlsplit, unquote

BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8931'
SITE = '/rapidmeta-finerenone/'

def status(path):
    try:
        req = urllib.request.Request(f'{BASE}/{path}', method='HEAD')
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        return f'ERR:{type(e).__name__}'

def sitemap_paths():
    sm = open('sitemap.xml', encoding='utf-8', errors='replace').read()
    out = []
    for u in re.findall(r'<loc>\s*([^<]+?)\s*</loc>', sm):
        p = unquote(urlsplit(u).path)
        if p.startswith(SITE):
            p = p[len(SITE):]
        out.append(p.lstrip('/'))
    return out

STUB_RE = re.compile(r'rm-orphan-redirect"\s+content="([^"]+)"')
def orphan_stubs():
    """(stub, target) pairs where the redirect target is not on disk."""
    out = []
    # Positive property: iterate the HTML pages, rather than excluding
    # everything that lacks the extension. (pre-commit exclusion-by-absence gate)
    for f in sorted(p for p in os.listdir('.') if p.endswith('.html')):
        t = open(f, 'rb').read().decode('utf-8', 'replace')
        m = STUB_RE.search(t)
        if m and not os.path.isfile(m.group(1)):
            out.append((f, m.group(1)))
    return out

if __name__ == '__main__':
    # ---- controls first. If these are wrong, nothing below means anything ----
    pos = status('index.html')
    neg = status('__control_definitely_absent_page__.html')
    print(f'CONTROL positive index.html      -> {pos} (expect 200)')
    print(f'CONTROL negative absent page     -> {neg} (expect 404)')
    if pos != 200 or neg != 404:
        sys.exit('ABORT: controls failed; the probe is not measuring anything.')

    paths = sitemap_paths()
    missing = [p for p in paths if p and not os.path.isfile(p)]
    print(f'\nsitemap entries                  : {len(paths)}')
    print(f'  not resolving on disk          : {len(missing)}')
    bad = [p for p in missing if status(p) != 200]
    print(f'  CONFIRMED non-200 over HTTP    : {len(bad)}')

    stubs = orphan_stubs()
    print(f'\nredirect stubs with dead target  : {len(stubs)}')
    confirmed = [(s, t) for s, t in stubs if status(s) == 200 and status(t) == 404]
    print(f'  CONFIRMED 200->404 over HTTP   : {len(confirmed)}')

    json.dump({'sitemap_broken': bad,
               'orphan_stubs': [s for s, _ in confirmed]},
              open('outputs/served_link_check.json', 'w'), indent=1)
    print(f'\nTOTAL broken reader paths        : {len(bad) + len(confirmed)}')
