#!/usr/bin/env python
"""Inject a visible verification/provenance banner into every STANDING app.

RapidMeta's value is not that every app is right — it is that a researcher can SEE
which ones are right and how we know. So every standing app carries, on its face,
an honest status: verified / provenance-backed / FLAGGED (with the specific gap).
An app that shows a number must show whether that number has been checked. Never
silently display a number we know contradicts its source.

Additive, offline-safe (inline styles, no external calls), idempotent (re-running
replaces the prior banner). Reads outputs/corpus_classification.json.

Usage: python scripts/inject_verification_banner.py [--apply]
"""
from __future__ import annotations
import sys, io, os, re, json

ROOT = os.environ.get('RAPIDMETA_REPO_ROOT',
                      os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_MARK = 'data-rapidmeta-verify-banner'

# Apps carrying HAND-AUTHORED banners (specific source wording + Cochrane panels)
# that the generic auto-banner must not overwrite. Demo-critical.
_SKIP_HANDCRAFTED = {'MALARIA_ACT_REVIEW.html', 'MALARIA_VACCINE_REVIEW.html'}

_STYLE = {
    'verified':      ('#0a7d33', '✓ VERIFIED',
                      'Pooled estimate matches a published meta-analysis (within CI) and every displayed number was checked against its source.'),
    'provenance-ok': ('#1f6feb', '✓ PROVENANCE-BACKED',
                      'Every contributing trial is sourced (PubMed ID + registry) and the displayed counts agree with the displayed effect. Not externally benchmarked against a published meta-analysis.'),
    'flagged':       ('#b8860b', '⚠ UNVERIFIED — see notes',
                      'This app stays up so you can check it. Some displayed data has NOT been fully verified:'),
}


def banner_html(rec):
    color, label, blurb = _STYLE.get(rec['status'], ('#b00020', '⚠ UNVERIFIED', 'Status unknown.'))
    reasons = ''.join(f'<li>{r}</li>' for r in rec.get('reasons', []))
    reasons_block = f'<ul style="margin:6px 0 0 18px;padding:0">{reasons}</ul>' if reasons else ''
    warn = rec.get('warn') or []
    warn_block = (f'<div style="opacity:.7;margin-top:4px">advisory: {", ".join(warn)}</div>'
                  if warn else '')
    kline = (f'k = {rec["k"]} contributing trial(s)' if rec.get('k') is not None else '')
    val = 'externally validated' if rec.get('externally_validated') else 'not externally benchmarked'
    return (
        f'<div {_MARK}="1" style="font-family:system-ui,sans-serif;font-size:13px;'
        f'border:1px solid {color};border-left:6px solid {color};background:#0d1117;'
        f'color:#e6edf3;padding:11px 15px;margin:10px;border-radius:8px;max-width:1100px">'
        f'<b style="color:{color}">{label}</b> '
        f'<span style="opacity:.75">· {kline} · {val}</span>'
        f'<div style="opacity:.85;margin-top:3px">{blurb}</div>'
        f'{reasons_block}{warn_block}'
        f'</div>'
    )


def inject_one(path, rec, apply=False):
    txt = open(path, encoding='utf-8', errors='replace').read()
    txt = re.sub(r'<div ' + _MARK + r'="1".*?</div>\s*(?:</ul>\s*</div>\s*)?', '', txt,
                 flags=re.S, count=1)
    m = re.search(r'<body[^>]*>', txt, re.I)
    if not m:
        return False
    new = txt[:m.end()] + '\n' + banner_html(rec) + '\n' + txt[m.end():]
    if apply:
        open(path, 'w', encoding='utf-8').write(new)
    return True


def main(argv):
    apply = '--apply' in argv
    recs = json.load(open(os.path.join(ROOT, 'outputs', 'corpus_classification.json'), encoding='utf-8'))
    done = miss = 0
    for r in recs:
        if r['status'].startswith('delist') or r['status'] == 'redirect':
            continue                      # de-listed apps get their own notice; redirects just forward to their full app (which gets a banner)
        if r['app'] in _SKIP_HANDCRAFTED:
            continue                      # hand-authored banner + Cochrane panel — do not clobber
        p = os.path.join(ROOT, r['app'])
        if not os.path.exists(p):
            miss += 1; continue
        if inject_one(p, r, apply):
            done += 1
        else:
            miss += 1
    if hasattr(sys.stdout, 'buffer') and getattr(sys.stdout, 'encoding', '').lower() != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    from collections import Counter
    c = Counter(r['status'] for r in recs if not r['status'].startswith('delist'))
    print(f"{'APPLIED' if apply else 'DRY-RUN'}: banners on {done} standing apps ({miss} missing/no-body)")
    for s, n in c.most_common():
        print(f"  {s}: {n}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
