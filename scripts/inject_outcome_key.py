#!/usr/bin/env python
"""THE KEYSTONE: add a per-trial outcome/timepoint/arm/NCT/source-tier KEY.

The single data-model gap that has blocked, all night: bulk registry-integer
re-routing, the timepoint rule, mixed-timepoint detection, and outcome-matched
adjudication all failed because the apps store no per-trial outcome/timepoint key.

This adds it — ADDITIVELY and backward-compatibly — as a sidecar map keyed by NCT
(not by surgically editing each realData trial object, which is fragile):

  window.RapidMeta.outcomeKeys = {
    "NCT01179048": { outcome: "...", timepoint_weeks: 245, arms: ["...","..."],
                     nct: "NCT01179048", source_tier: "registry-backed" }, ... }

Derived deterministically from the registry (AACT primary outcome title + time_frame
+ design_group arm labels) and our own grades (source tier). Apps and tools that
know the key can now match a pooled number to the registry's specific posted
analysis; apps that don't simply ignore the extra object. Reversible (marker-bounded).
"""
from __future__ import annotations
import json, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from assert_count_effect_consistency import _objbody, _top_entries  # noqa

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARK = 'rm-outcome-key'


def _load(n, d):
    p = os.path.join(REPO, 'outputs', n)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else d


OA = _load('aact_outcome_arms.json', {'outcomes': {}, 'arms': {}})
TP = _load('timepoint_cache.json', {})
CONF = _load('registry_confirmed_trials.json', [])
_CONF_SET = {(x['app'], x['nct']) for x in CONF}


def _key_for(app, nct):
    tp = TP.get(nct, {})
    return {
        'nct': nct,
        'outcome': OA['outcomes'].get(nct),
        'timepoint_weeks': tp.get('weeks'),
        'timepoint_text': tp.get('time_frame'),
        'arms': OA['arms'].get(nct, []),
        'source_tier': 'registry-backed' if (app, nct) in _CONF_SET else 'extracted',
    }


def inject(app_path, apply=False):
    app = os.path.basename(app_path)
    txt = open(app_path, encoding='utf-8', errors='replace').read()
    m = re.search(r'realData\s*:\s*\{', txt)
    if not m:
        return False, 'no realData'
    ncts = []
    for k, _o in _top_entries(_objbody(txt, m.end() - 1)):
        mm = re.search(r'NCT\d{8}', str(k))
        if mm:
            ncts.append((str(k), mm.group(0)))
    keys = {}
    for k, nct in ncts:
        keys[k] = _key_for(app, nct)   # keyed by the app's realData key (usually the NCT)
    payload = json.dumps(keys, ensure_ascii=True)
    block = (f'<script data-{MARK}="1">window.RapidMeta=window.RapidMeta||{{}};'
             f'window.RapidMeta.outcomeKeys=Object.assign(window.RapidMeta.outcomeKeys||{{}},{payload});'
             f'</script>')
    txt2 = re.sub(r'<script data-' + MARK + r'="1">.*?</script>\s*', '', txt, flags=re.S)
    b = re.search(r'<body[^>]*>', txt2, re.I)
    if not b:
        return False, 'no body'
    new = txt2[:b.end()] + '\n' + block + '\n' + txt2[b.end():]
    if not apply:
        return True, f"{len(keys)} trials keyed"
    open(app_path, 'w', encoding='utf-8').write(new)
    jc = os.path.join(REPO, 'scripts', 'jscheck.py')
    r = subprocess.run([sys.executable, jc, app_path], capture_output=True, text=True)
    if '[JS-OK]' not in (r.stdout + r.stderr):
        open(app_path, 'w', encoding='utf-8').write(txt)
        return False, 'REVERTED (jscheck)'
    return True, f"{len(keys)} trials keyed"


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--files', nargs='*', default=[])
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--add-only', action='store_true')
    a = ap.parse_args()
    import glob
    targets = list(a.files) or (sorted(glob.glob(os.path.join(REPO, '*_REVIEW.html'))) if a.all else [])
    if hasattr(sys.stdout, 'buffer'):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    done = skip = keyed = 0
    for t in targets:
        p = t if os.path.isabs(t) else os.path.join(REPO, t)
        if not os.path.exists(p):
            continue
        if a.add_only and f'data-{MARK}' in open(p, encoding='utf-8', errors='replace').read():
            continue
        ok, msg = inject(p, a.apply)
        done += ok
        skip += (not ok)
        if ok:
            mm = re.match(r'(\d+)', msg)
            keyed += int(mm.group(1)) if mm else 0
        if a.files:
            print(f"  {'APPLIED' if (ok and a.apply) else ('DRY' if ok else 'SKIP')} {os.path.basename(t)}: {msg}")
    print(f"\n{'APPLIED' if a.apply else 'DRY-RUN'}: outcome-key on {done} apps ({keyed} trial keys), {skip} skipped")


if __name__ == '__main__':
    main()
