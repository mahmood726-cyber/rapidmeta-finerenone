#!/usr/bin/env python
"""Put each app's evidence GRADE on screen, with the published criteria (Bukhari's move).

Additive, offline, idempotent, jscheck-revert. Reads outputs/corpus_grades.json.
"""
from __future__ import annotations
import json, os, re, subprocess, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARK = 'data-rapidmeta-grade-badge'
STYLE = {
    'VERIFIED': ('#0a7d33', 'VERIFIED', 'externally validated vs a published meta-analysis; passes all gates'),
    'AACT_CONCORDANT': ('#1a7f8c', 'REGISTRY-CONCORDANT', 'the pooled effect matches the value the sponsor posted to the trial registry (numeric match; outcome identity not machine-verified)'),
    'REGISTRY-BACKED': ('#0f6e57', 'REGISTRY-BACKED', 'at least one contributing trial\'s event counts were CONFIRMED against the sponsor-posted registry results (both arms match a single posted outcome) — the number came from, or matches, the registry, not extraction alone'),
    'SOUND': ('#1f6feb', 'SOUND', 'every trial sourced (PMID+registry); passes the arithmetic + identity gates; numbers extracted, not registry-posted'),
    'WEAK': ('#b8860b', 'WEAK', 'a gap remains (missing PMID/registry, blank cells) resting on a single unverified source'),
    'REJECTED': ('#b00020', 'REJECTED', 'fails a HARD arithmetic gate (count<->effect) or a high-confidence identity gate (fabricated control / wrong-NCT) — flagged, logged, never silently dropped'),
}
CRITERIA = ('Grades are deterministic, from the published gate outputs. '
            'VERIFIED &gt; REGISTRY-CONCORDANT &gt; SOUND &gt; WEAK &gt; REJECTED. '
            'The standard is published and applied uniformly.')


def badge(grade):
    color, label, desc = STYLE.get(grade, STYLE['WEAK'])
    return (f'<div {MARK}="1" style="font-family:system-ui,sans-serif;font-size:13px;'
            f'border:1px solid {color};border-left:6px solid {color};background:#0d1117;color:#e6edf3;'
            f'padding:9px 14px;margin:10px;border-radius:8px;max-width:1100px">'
            f'<b style="color:{color}">EVIDENCE GRADE: {label}</b>'
            f'<div style="opacity:.85;margin-top:2px">{desc}</div>'
            f'<div style="opacity:.6;margin-top:3px;font-size:11px">{CRITERIA}</div></div>')


def main():
    apply = '--apply' in sys.argv
    only = [a for a in sys.argv[1:] if a.endswith('.html')]
    grades = json.load(open(os.path.join(REPO, 'outputs', 'corpus_grades.json'), encoding='utf-8'))
    done = 0
    items = [(a, g) for a, g in grades.items() if not only or a in only]
    for app, grade in items:
        p = os.path.join(REPO, app)
        if not os.path.exists(p):
            continue
        txt = open(p, encoding='utf-8', errors='replace').read()
        txt2 = re.sub(r'<div ' + MARK + r'="1".*?</div>\s*</div>\s*', '', txt, flags=re.S)
        b = re.search(r'<body[^>]*>', txt2, re.I)
        if not b:
            continue
        new = txt2[:b.end()] + '\n' + badge(grade) + '\n' + txt2[b.end():]
        if apply:
            open(p, 'w', encoding='utf-8').write(new)
            jc = os.path.join(REPO, 'scripts', 'jscheck.py')
            r = subprocess.run([sys.executable, jc, p], capture_output=True, text=True)
            if '[JS-OK]' not in (r.stdout + r.stderr):
                open(p, 'w', encoding='utf-8').write(txt)
                continue
        done += 1
    if hasattr(sys.stdout, 'buffer'):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    print(f"{'APPLIED' if apply else 'DRY'}: grade badge on {done} apps")


if __name__ == '__main__':
    main()
