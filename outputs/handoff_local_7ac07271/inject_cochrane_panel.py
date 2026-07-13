#!/usr/bin/env python
"""Inject an in-app "Published MA comparison" panel (offline-safe, additive).

This is the slide that wins the room: for an app whose question a published
meta-analysis has answered, show OUR pooled estimate next to THEIRS, with the
trial-inclusion difference BOTH ways and an honest verdict. Same answer as
Cochrane + full provenance = the pitch in one panel.

Config is a dict per app:
  { 'app': '<FILE>.html',
    'question': '...',
    'published': [ {'ref':'Cochrane Steingart 2014', 'doi':'10.1002/14651858.CD009593.pub3',
                    'measure':'Se/Sp', 'their':'89% / 99%', 'their_ci':'(85-92) / (98-99)',
                    'k_theirs':22} , ... ],
    'ours':'85.8% / 97.8%', 'ours_ci':'(83.6-87.7) / (97.2-98.2)', 'k_ours':17,
    'they_have_we_dont':'...', 'we_have_they_dont':'...',
    'verdict':'MATCH — small explicable difference',
    'verdict_color':'#0a7d33', 'note':'...' }

Idempotent (replaces a prior panel). Inserted right after the verification banner
if present, else after <body>.
"""
from __future__ import annotations
import sys, io, os, re, json
_MARK = 'data-rapidmeta-cochrane-panel'


def panel_html(cfg):
    color = cfg.get('verdict_color', '#1f6feb')
    rows = ''
    for p in cfg.get('published', []):
        doi = p.get('doi', '')
        link = f'https://doi.org/{doi}' if doi else '#'
        rows += (f'<tr><td style="padding:3px 10px;border-top:1px solid #30363d">'
                 f'<a href="{link}" style="color:#58a6ff">{p["ref"]}</a></td>'
                 f'<td style="padding:3px 10px;border-top:1px solid #30363d">{p.get("their","")} '
                 f'<span style="opacity:.6">{p.get("their_ci","")}</span></td>'
                 f'<td style="padding:3px 10px;border-top:1px solid #30363d;text-align:center">'
                 f'{p.get("k_theirs","")}</td></tr>')
    ours = (f'<tr style="background:#0d2818"><td style="padding:3px 10px;border-top:2px solid {color}">'
            f'<b style="color:{color}">RapidMeta (ours)</b></td>'
            f'<td style="padding:3px 10px;border-top:2px solid {color}"><b>{cfg.get("ours","")}</b> '
            f'<span style="opacity:.6">{cfg.get("ours_ci","")}</span></td>'
            f'<td style="padding:3px 10px;border-top:2px solid {color};text-align:center">{cfg.get("k_ours","")}</td></tr>')
    diff = ''
    if cfg.get('they_have_we_dont') or cfg.get('we_have_they_dont'):
        diff = ('<div style="margin-top:6px;font-size:12px;opacity:.85">'
                f'<b>Trial-inclusion diff:</b> they include but we don\'t — <i>{cfg.get("they_have_we_dont","—")}</i>; '
                f'we include but they don\'t — <i>{cfg.get("we_have_they_dont","—")}</i></div>')
    return (
        f'<div {_MARK}="1" style="font-family:system-ui,sans-serif;font-size:13px;'
        f'border:1px solid {color};border-left:6px solid {color};background:#0d1117;color:#e6edf3;'
        f'padding:12px 16px;margin:10px;border-radius:8px;max-width:1100px">'
        f'<b style="color:{color}">◆ Published meta-analysis comparison</b> '
        f'<span style="opacity:.75">— {cfg.get("question","")}</span>'
        f'<table style="border-collapse:collapse;margin-top:8px;width:100%;font-size:13px">'
        f'<tr style="opacity:.7"><th style="text-align:left;padding:2px 10px">Source</th>'
        f'<th style="text-align:left;padding:2px 10px">Pooled estimate ({cfg.get("measure_label","measure")})</th>'
        f'<th style="padding:2px 10px">k</th></tr>'
        f'{rows}{ours}</table>'
        f'{diff}'
        f'<div style="margin-top:8px"><b style="color:{color}">Verdict:</b> {cfg.get("verdict","")}</div>'
        f'<div style="opacity:.8;margin-top:3px;font-size:12px">{cfg.get("note","")}</div>'
        f'</div>'
    )


def inject_one(path, cfg, apply=False):
    txt = open(path, encoding='utf-8', errors='replace').read()
    txt = re.sub(r'<div ' + _MARK + r'="1".*?</div>\s*</div>\s*', '', txt, flags=re.S, count=1)
    html = panel_html(cfg)
    # place after the verification banner if present, else after <body>
    bm = re.search(r'(<div data-rapidmeta-verify-banner="1".*?</div>\s*(?:</ul>\s*</div>\s*)?)', txt, re.S)
    if bm:
        pos = bm.end()
    else:
        m = re.search(r'<body[^>]*>', txt, re.I)
        if not m:
            return False
        pos = m.end()
    new = txt[:pos] + '\n' + html + '\n' + txt[pos:]
    if apply:
        open(path, 'w', encoding='utf-8').write(new)
    return True


def main(argv):
    cfg_path = argv[1]
    apply = '--apply' in argv
    cfgs = json.load(open(cfg_path, encoding='utf-8'))
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    done = 0
    for cfg in cfgs:
        p = os.path.join(root, cfg['app'])
        if os.path.exists(p) and inject_one(p, cfg, apply):
            done += 1
    print(f"{'APPLIED' if apply else 'DRY-RUN'}: cochrane panel on {done}/{len(cfgs)} apps")
    return 0


if __name__ == '__main__':
    if hasattr(sys.stdout, 'buffer') and getattr(sys.stdout, 'encoding', '').lower() != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main(sys.argv))
