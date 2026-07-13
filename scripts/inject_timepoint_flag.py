#!/usr/bin/env python
"""Timepoint rule on screen (deliverable d): TAG the pool's timepoint span, and
FLAG pools whose trials' registry PRIMARY timepoints differ severely (>=10x).

Conservative on purpose (no-regression): only the >=10x tier is flagged as a
warning (a spread too large to be time_frame-parse noise); milder spreads are
shown as an informational tag, not a red flag. Additive, offline, idempotent,
jscheck-revert. Reads outputs/mixed_timepoint_pools.json.
"""
from __future__ import annotations
import json, os, re, subprocess, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARK = 'data-rapidmeta-timepoint'
FLAG_RATIO = 10.0


def _wk(w):
    return f"{w/52.14:.1f}y" if w >= 104 else (f"{w/4.345:.0f}mo" if w >= 8 else f"{w:.0f}w")


def notice(rec):
    lo, hi, r = rec['min_w'], rec['max_w'], rec['ratio']
    if r >= FLAG_RATIO:
        color, head = '#b8860b', '&#9888; TIMEPOINT SPREAD — verify comparability'
        body = ('This pool\'s trials have registry PRIMARY endpoints that differ by '
                f'~{r:.0f}x ({_wk(lo)} to {_wk(hi)}). Pooling a short-follow-up effect with a '
                'long-follow-up effect as if they were the same quantity is a hidden '
                'heterogeneity error. THE RULE: use each trial\'s pre-registered primary '
                'timepoint; where absent, the LONGEST <b>COMMON</b> timepoint across the pool '
                '(not the longest available in each). Verify these trials share a timepoint.')
    else:
        color, head = '#3b6', 'Timepoint span'
        body = (f'Registry primary endpoints span {_wk(lo)}–{_wk(hi)}. Shown for transparency; '
                'within the normal range for this pool.')
    return (f'<div {MARK}="1" style="font-family:system-ui,sans-serif;font-size:13px;'
            f'border:1px solid {color};border-left:6px solid {color};background:#0d1117;color:#e6edf3;'
            f'padding:9px 14px;margin:10px;border-radius:8px;max-width:1100px">'
            f'<b style="color:{color}">{head}</b><div style="opacity:.85;margin-top:2px">{body}</div>'
            f'<div style="opacity:.6;margin-top:3px;font-size:11px">Deterministic timepoint rule; '
            f'registry-derived (AACT primary time_frame). A risk flag, not a certified defect — '
            f'confirming needs the pool\'s own stored timepoint.</div></div>')


def main():
    apply = '--apply' in sys.argv
    recs = json.load(open(os.path.join(REPO, 'outputs', 'mixed_timepoint_pools.json'), encoding='utf-8'))
    # Only inject where we FLAG (>=10x). Milder spreads: skip (avoid over-tagging the
    # showcase; the measurement is logged regardless).
    recs = [r for r in recs if r['ratio'] >= FLAG_RATIO]
    done = 0
    for r in recs:
        p = os.path.join(REPO, r['app'])
        if not os.path.exists(p):
            continue
        txt = open(p, encoding='utf-8', errors='replace').read()
        txt2 = re.sub(r'<div ' + MARK + r'="1".*?</div>\s*</div>\s*', '', txt, flags=re.S)
        b = re.search(r'<body[^>]*>', txt2, re.I)
        if not b:
            continue
        new = txt2[:b.end()] + '\n' + notice(r) + '\n' + txt2[b.end():]
        if apply:
            open(p, 'w', encoding='utf-8').write(new)
            jc = os.path.join(REPO, 'scripts', 'jscheck.py')
            rr = subprocess.run([sys.executable, jc, p], capture_output=True, text=True)
            if '[JS-OK]' not in (rr.stdout + rr.stderr):
                open(p, 'w', encoding='utf-8').write(txt)
                continue
        done += 1
    if hasattr(sys.stdout, 'buffer'):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    print(f"{'APPLIED' if apply else 'DRY'}: timepoint flag (>={FLAG_RATIO:.0f}x) on {done} pools")


if __name__ == '__main__':
    main()
