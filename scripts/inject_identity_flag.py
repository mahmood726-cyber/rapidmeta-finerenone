#!/usr/bin/env python
"""Additive in-app notice for HIGH-confidence identity-gate defects.

Discipline: a number that fails is FLAGGED, never silently dropped. Every app with
a high-confidence arm-count/Nix-TB finding gets a visible, offline, idempotent
notice naming the specific trial + the registry contradiction, so a reader sees it.
"""
from __future__ import annotations
import json, os, re, subprocess, sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARK = 'data-rapidmeta-identity-flag'


def notice_html(rows):
    items = ''.join(
        f'<li><b>{r["nct"]}</b>: {r["shown"]} — registry says {r["registry"]}</li>' for r in rows[:8])
    return (
        f'<div {MARK}="1" style="font-family:system-ui,sans-serif;font-size:13px;'
        f'border:1px solid #b00020;border-left:6px solid #b00020;background:#0d1117;color:#e6edf3;'
        f'padding:11px 15px;margin:10px;border-radius:8px;max-width:1100px">'
        f'<b style="color:#f85149">⚠ IDENTITY CHECK — registry contradicts a displayed arm</b>'
        f'<div style="opacity:.85;margin-top:3px">One or more trials show a comparator arm the trial '
        f'registry did not register (single-arm study), or bind an NCT to a different trial. A pooled '
        f'estimate that includes a fabricated or mis-bound arm can be wrong. Verify against the source '
        f'before using these numbers:</div>'
        f'<ul style="margin:6px 0 0 18px;padding:0">{items}</ul>'
        f'<div style="opacity:.7;margin-top:4px;font-size:12px">Checked offline against AACT 2026-04-12 '
        f'(design_groups). Flagged, not removed — see outputs/identity_findings.json.</div></div>')


def main():
    apply = '--apply' in sys.argv
    idf = json.load(open(os.path.join(REPO, 'outputs', 'identity_findings.json'), encoding='utf-8'))
    byapp = defaultdict(list)
    for x in idf:
        if x.get('confidence') == 'high':
            byapp[x['app']].append(x)
    done = 0
    for app, rows in byapp.items():
        p = os.path.join(REPO, app)
        if not os.path.exists(p):
            continue
        txt = open(p, encoding='utf-8', errors='replace').read()
        txt2 = re.sub(r'<div ' + MARK + r'="1".*?</div>\s*</div>\s*', '', txt, flags=re.S)
        bm = re.search(r'(<div data-rapidmeta-verify-banner="1".*?</div>\s*(?:</ul>\s*</div>\s*)?)', txt2, re.S)
        pos = bm.end() if bm else (re.search(r'<body[^>]*>', txt2, re.I).end())
        new = txt2[:pos] + '\n' + notice_html(rows) + '\n' + txt2[pos:]
        if apply:
            open(p, 'w', encoding='utf-8').write(new)
            jc = os.path.join(REPO, 'scripts', 'jscheck.py')
            r = subprocess.run([sys.executable, jc, p], capture_output=True, text=True)
            if '[JS-OK]' not in (r.stdout + r.stderr):
                open(p, 'w', encoding='utf-8').write(txt)  # revert
                continue
        done += 1
    if hasattr(sys.stdout, 'buffer'):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    print(f"{'APPLIED' if apply else 'DRY'}: identity-defect notice on {done}/{len(byapp)} apps")


if __name__ == '__main__':
    main()
