#!/usr/bin/env python
"""Corpus-wide sweep for RENDER-LAYER defect CLASSES found on one page by an
external reviewer. Each instance came from one page out of hundreds; these are
classes, so the corpus is the right denominator.

LAYER NOTE, per class, stated explicitly:
  All six classes live at the RENDER layer (what the page shows a reader), not
  in the stored object. This script reads the SERVED HTML BYTES. That catches
  statically-rendered instances only. Anything injected at runtime by JS is
  INVISIBLE here and must be confirmed in a rendered page -- see
  scripts/confirm_render_defects_browser.py. A zero from this script is
  therefore "no STATIC instance", never "no instance".
"""
import os, re, json, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = re.compile(r'<script\b.*?</script>', re.S | re.I)

# 1. a certainty rating displayed while the page says GRADE is pending
CERT = re.compile(r'GRADE\s+certainty\s*:\s*(very\s+low|low|moderate|high)', re.I)
PENDING = re.compile(r'(?:GRADE|[Cc]ertainty)[^.]{0,80}(pending|not\s+yet\s+rated|to\s+be\s+(?:rated|assessed))', re.I)
# 2. a null identity printed beside a real percentage
NULLPCT = re.compile(r'(?<![A-Za-z])(None|null|undefined|NaN)\s+\d{1,3}(?:\.\d+)?\s*%')
# 3. a block promised in prose
PROMISE = re.compile(r'reported\s+in\s+the\s+(sensitivity|leave-one-out|subgroup)\s+block', re.I)
# 5. an NCT label whose href is not clinicaltrials.gov
NCTLINK = re.compile(r'<a[^>]+href="([^"]+)"[^>]*>\s*(NCT\d{8})\s*</a>', re.I)
# 6. RoB 2 domain judged with a signalling-question answer
ROBNOINFO = re.compile(r'(domain[^.<]{0,80}|judg[e]?ment[^.<]{0,80})(No information)', re.I)

STYLE = re.compile(r'<style\b.*?</style>', re.S | re.I)
TAG = re.compile(r'<[^>]+>')
import html as _html

def rendered_text(t):
    """Approximate what a READER sees.

    A sentence a reader sees as one string is often several strings in the file,
    split by an inline tag. Matching against SOURCE therefore silently misses
    every markup-spanning phrase -- which is how this sweep first reported 0
    pages for a defect an external reviewer had confirmed by eye. Strip tags,
    unescape entities, collapse whitespace, THEN match.
    """
    t = STYLE.sub(' ', SCRIPT.sub(' ', t))
    t = TAG.sub(' ', t)
    return re.sub(r'\s+', ' ', _html.unescape(t))

def strip_scripts(t):
    return rendered_text(t)

def scan(path):
    raw = open(path, 'rb').read().decode('utf-8', 'replace')
    vis = strip_scripts(raw)
    out = {}
    certs = CERT.findall(vis)
    if certs and PENDING.search(vis):
        out['c1_certainty_shown_while_pending'] = sorted(set(c.lower() for c in certs))
    n = NULLPCT.findall(vis)
    if n:
        out['c2_null_identity_with_percent'] = collections.Counter(n).most_common()
    p = PROMISE.findall(vis)
    if p:
        out['c3_promised_block'] = sorted(set(x.lower() for x in p))
    bad = [(h, n2) for h, n2 in NCTLINK.findall(SCRIPT.sub(' ', raw))
           if 'clinicaltrials.gov' not in h.lower()]
    if bad:
        out['c5_nct_label_not_linking_registry'] = bad[:6]
    r = ROBNOINFO.findall(vis)
    if r:
        out['c6_rob_domain_no_information'] = len(r)
    return out

if __name__ == '__main__':
    findings = {}
    scanned = 0
    for rt, dirs, fs in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', 'pytest_tmp',
                                                'build-artefacts', 'vendor'}]
        for f in (x for x in fs if x.endswith('.html')):
            p = os.path.join(rt, f)
            rel = os.path.relpath(p, ROOT).replace(os.sep, '/')
            scanned += 1
            r = scan(p)
            if r:
                findings[rel] = r
    tally = collections.Counter()
    for v in findings.values():
        for k in v:
            tally[k] += 1
    print(f'pages scanned (STATIC bytes only) : {scanned}')
    print(f'pages with >=1 static instance    : {len(findings)}')
    for k, c in sorted(tally.items()):
        print(f'   {k:44s} {c:5d} pages')
    os.makedirs(os.path.join(ROOT, 'outputs'), exist_ok=True)
    with open(os.path.join(ROOT, 'outputs', 'render_defect_sweep.json'), 'w',
              encoding='utf-8', newline='') as fh:
        json.dump({'pages_scanned': scanned, 'findings': findings}, fh, indent=1)
    print('\nNOTE: static-only. Runtime-injected instances are not visible here.')
