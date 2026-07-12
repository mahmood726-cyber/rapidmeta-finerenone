#!/usr/bin/env python
"""Inject a pre-registration provenance badge into a built app (STAGED, additive).

Surfaces, INSIDE the app the researcher reads: the registered protocol hash, the
git commit + UTC timestamp of registration, and the machine-computed
protocol-as-registered vs analysis-as-run verdict (CONCORDANT / MINOR-DRIFT /
DRIFT). Self-contained inline styles — no external calls (offline-safe). Additive:
inserts one <div> after <body>; re-running replaces the prior badge in place.

Usage:
  python scripts/inject_protocol_badge.py protocol/<REVIEW>.json <APP>_REVIEW.html [--apply]
"""
from __future__ import annotations
import sys, io, os, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import protocol_diff as pdiff

_COLORS = {'CONCORDANT': '#0a7d33', 'MINOR-DRIFT': '#b8860b', 'DRIFT': '#b00020'}
_MARK = 'data-rapidmeta-prereg-badge'


def badge_html(d):
    color = _COLORS.get(d['verdict'], '#555')
    sha = (d.get('protocol_sha256') or '')[:12]
    commit = (d.get('git_commit_at_lock') or '')[:12]
    findings = ''.join(
        f'<li>{f["code"].replace("_"," ")} — {f.get("detail","")}</li>' for f in d['findings'])
    findings_block = f'<ul style="margin:6px 0 0 16px;padding:0">{findings}</ul>' if findings else ''
    return (
        f'<div {_MARK}="1" style="font-family:system-ui,sans-serif;font-size:13px;'
        f'border:1px solid {color};border-left:5px solid {color};background:#0d1117;'
        f'color:#e6edf3;padding:10px 14px;margin:10px;border-radius:8px;max-width:1100px">'
        f'<b style="color:{color}">◆ Pre-registered protocol — {d["verdict"]}</b> '
        f'<span style="opacity:.8">(protocol-as-registered vs analysis-as-run)</span><br>'
        f'<span style="opacity:.85">review <code>{d.get("review_id","")}</code> · '
        f'protocol sha256 <code>{sha}…</code> · registered at git commit '
        f'<code>{commit}</code> · locked <code>{d.get("locked_utc","")}</code></span>'
        f'<div style="opacity:.75;margin-top:4px">Registered primary: '
        f'<i>{(d.get("registered_primary_outcome") or "")[:90]}</i></div>'
        f'{findings_block}'
        f'</div>'
    )


def inject(protocol_path, app_path, apply=False):
    d = pdiff.diff(protocol_path, app_path)
    html = badge_html(d)
    txt = open(app_path, encoding='utf-8', errors='replace').read()
    # remove a prior badge if present (idempotent)
    txt = re.sub(r'<div ' + _MARK + r'="1".*?</div>\s*(?:</div>\s*)?', '', txt, flags=re.S, count=1)
    m = re.search(r'<body[^>]*>', txt, re.I)
    if not m:
        return {'ok': False, 'reason': 'no <body> anchor', 'verdict': d['verdict']}
    newtxt = txt[:m.end()] + '\n' + html + '\n' + txt[m.end():]
    if apply:
        open(app_path, 'w', encoding='utf-8').write(newtxt)
    return {'ok': True, 'verdict': d['verdict'], 'applied': apply,
            'badge_bytes': len(html), 'findings': [f['code'] for f in d['findings']]}


def main(argv):
    if len(argv) < 3:
        print(__doc__); return 2
    r = inject(argv[1], argv[2], apply='--apply' in argv)
    print(json.dumps(r, indent=2, ensure_ascii=False))
    return 0 if r.get('ok') else 1


if __name__ == '__main__':
    if hasattr(sys.stdout, 'buffer') and getattr(sys.stdout, 'encoding', '').lower() != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main(sys.argv))
