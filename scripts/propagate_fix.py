#!/usr/bin/env python
"""Propagate an adjudicated dispute to EVERY app containing that trial — the
O(trials) advantage Cochrane structurally cannot match (their cost is
O(reviews x trials); an error lives in one team's PDF forever).

A disputed trial is FAIL-CLOSED: a visible, additive, idempotent notice is stamped
into every app containing the NCT, marking the trial disputed/under-adjudication and
excluded from the pool until resolved. Every change is LOGGED (old/new), DIFFABLE
(git), and REVERSIBLE (--revert removes the marker + restores). Nothing silent.

Usage:
  python scripts/propagate_fix.py --nct NCT0123 --status disputed --reason "..." [--apply]
  python scripts/propagate_fix.py --nct NCT0123 --revert [--apply]
"""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(REPO, 'outputs', 'propagation_log.json')
MARK = 'data-rapidmeta-trial-dispute'


def _apps_for(nct):
    idx = json.load(open(os.path.join(REPO, 'outputs', 'nct_to_apps.json'), encoding='utf-8'))
    return idx.get(nct, [])


def _notice(nct, status, reason):
    color = '#b00020' if status == 'disputed' else ('#0a7d33' if status == 'resolved_fixed' else '#b8860b')
    label = {'disputed': '&#9888; DISPUTED — trial under adjudication, EXCLUDED from the pool',
             'resolved_fixed': '&#10003; CORRECTED from source',
             'resolved_kept': '&#9888; DISPUTE reviewed — source upheld our value'}.get(status, 'DISPUTED')
    return (f'<div {MARK}="{nct}" data-status="{status}" style="font-family:system-ui,sans-serif;'
            f'font-size:13px;border:1px solid {color};border-left:6px solid {color};background:#0d1117;'
            f'color:#e6edf3;padding:9px 14px;margin:10px;border-radius:8px;max-width:1100px">'
            f'<b style="color:{color}">{label}</b> <span style="opacity:.75">· trial {nct}</span>'
            f'<div style="opacity:.85;margin-top:2px">{reason}</div>'
            f'<div style="opacity:.6;margin-top:3px;font-size:11px">Propagated from a source-adjudicated '
            f'dispute. Fail-closed: a disputed trial is not used in the pooled estimate until resolved. '
            f'Logged &amp; reversible.</div></div>')


def apply_status(nct, status, reason, apply, revert=False):
    apps = _apps_for(nct)
    changed = []
    for app in apps:
        p = os.path.join(REPO, app)
        if not os.path.exists(p):
            continue
        txt = open(p, encoding='utf-8', errors='replace').read()
        stripped = re.sub(r'<div ' + MARK + r'="' + re.escape(nct) + r'".*?</div>\s*</div>\s*',
                          '', txt, flags=re.S)
        if revert:
            new = stripped
        else:
            b = re.search(r'<body[^>]*>', stripped, re.I)
            if not b:
                continue
            new = stripped[:b.end()] + '\n' + _notice(nct, status, reason) + '\n' + stripped[b.end():]
        if new == txt:
            continue
        if apply:
            open(p, 'w', encoding='utf-8').write(new)
            jc = os.path.join(REPO, 'scripts', 'jscheck.py')
            r = subprocess.run([sys.executable, jc, p], capture_output=True, text=True)
            if '[JS-OK]' not in (r.stdout + r.stderr):
                open(p, 'w', encoding='utf-8').write(txt)  # revert on break
                continue
        changed.append(app)
    # append to the propagation log (audit trail)
    if apply and changed:
        log = json.load(open(LOG, encoding='utf-8')) if os.path.exists(LOG) else []
        log.append({'nct': nct, 'status': 'reverted' if revert else status, 'reason': reason,
                    'apps': changed, 'count': len(changed)})
        json.dump(log, open(LOG, 'w', encoding='utf-8'), indent=1)
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--nct', required=True)
    ap.add_argument('--status', default='disputed',
                    choices=['disputed', 'resolved_fixed', 'resolved_kept'])
    ap.add_argument('--reason', default='Reported and under source adjudication.')
    ap.add_argument('--revert', action='store_true')
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()
    if hasattr(sys.stdout, 'buffer'):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    changed = apply_status(a.nct, a.status, a.reason, a.apply, a.revert)
    verb = 'REVERTED' if a.revert else a.status.upper()
    print(f"{'APPLIED' if a.apply else 'DRY-RUN'}: {verb} {a.nct} across {len(changed)} app(s) "
          f"(of {len(_apps_for(a.nct))} containing it)")
    if not a.apply:
        for c in changed[:8]:
            print(f"   would touch {c}")


if __name__ == '__main__':
    main()
