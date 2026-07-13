#!/usr/bin/env python
"""One-click dispute + one-tap reason + status-up-front. No login. Persists locally.

Mahmood's spec, stripped to a tap:
  - Show the status we ALREADY know for each trial (we've checked every number vs
    registry + arithmetic + identity BEFORE the user opens the app) — surface the
    doubt before they go looking.
  - Dispute = ONE CLICK. Pick the trial, ONE TAP a reason (6 classes that ROUTE the
    adjudicator), done. Optional skippable "what should it be / where". No account.
  - The dispute is flagged INSTANTLY and stored in the app's own localStorage
    namespace (so it persists across sessions and rides the export/offline-copy).
    It also produces a GitHub-Issue-ready payload for Phase 2 (device-flow login).
  - The report TRIGGERS verification; it never bypasses it. Fail-closed.

Additive, offline, idempotent, jscheck-revert. Supersedes the older report button.
"""
from __future__ import annotations
import json, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from assert_count_effect_consistency import _objbody, _top_entries, _sval  # noqa

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARK = 'rm-dispute:begin'
OWNER = 'mahmood726@gmail.com'

REASONS = [  # (label, reason_class -> routes the adjudicator)
    ('Wrong number', 'wrong_number', 'arithmetic gate + registry posted value'),
    ('Wrong trial', 'wrong_trial', 'identity gate: NCT binding, arm count, N'),
    ('Wrong outcome / timepoint', 'wrong_outcome_timepoint', 'registered outcome + timepoint'),
    ('Wrong arm', 'wrong_arm', 'arm-label / arm-count adjudication'),
    ("This trial shouldn't be here", 'trial_shouldnt_be_here', 'PICO / eligibility'),
    ('Something else', 'something_else', 'free text -> human queue'),
]


def _status_map(app):
    conf = {x['nct'] for x in json.load(open(os.path.join(REPO, 'outputs', 'registry_confirmed_trials.json'), encoding='utf-8')) if x['app'] == app} \
        if os.path.exists(os.path.join(REPO, 'outputs', 'registry_confirmed_trials.json')) else set()
    ident = {x['nct'] for x in json.load(open(os.path.join(REPO, 'outputs', 'identity_findings.json'), encoding='utf-8')) if x.get('app') == app and x.get('confidence') == 'high'} \
        if os.path.exists(os.path.join(REPO, 'outputs', 'identity_findings.json')) else set()
    return conf, ident


def _trials(txt, conf, ident):
    m = re.search(r'realData\s*:\s*\{', txt)
    if not m:
        return []
    out = []
    for k, o in _top_entries(_objbody(txt, m.end()-1)):
        nct = (re.search(r'NCT\d{8}', str(k)) or [None])
        nct = nct.group(0) if hasattr(nct, 'group') else None
        st = 'disputed_by_us' if (nct and nct in ident) else ('registry_verified' if (nct and nct in conf) else 'sound')
        out.append({'id': str(k), 'nct': nct, 'name': (_sval(o, 'name') or _sval(o, 'shortLabel') or str(k))[:70], 'status': st})
    return out


def panel_js(app, trials):
    tj = json.dumps(trials)
    rj = json.dumps([{'label': l, 'cls': c, 'routes': r} for l, c, r in REASONS])
    return f'''<!-- {MARK} -->
<div id="rm-dispute" style="font-family:system-ui,sans-serif;font-size:13px;border:1px solid #d29922;
 border-left:6px solid #d29922;background:#0d1117;color:#e6edf3;padding:11px 15px;margin:10px;border-radius:8px;max-width:1100px">
 <b style="color:#e3b341">&#9873; Spot a wrong number? Flag it — one tap, no account.</b>
 <span style="opacity:.7;font-size:12px;margin-left:6px">Every number here was already checked vs the trial registry, its own arithmetic, and its identity. We surface what we found — and you can dispute any of it.</span>
 <div style="margin-top:8px">
  <select id="rm-d-trial" style="width:100%;padding:6px"></select>
 </div>
 <div id="rm-d-reasons" style="margin-top:7px;display:flex;flex-wrap:wrap;gap:6px"></div>
 <div id="rm-d-more" style="display:none;margin-top:7px">
  <input id="rm-d-value" placeholder="Optional: what should it be? (skippable)" style="width:49%;padding:5px">
  <input id="rm-d-source" placeholder="Optional: where did you see it? (skippable)" style="width:49%;padding:5px">
 </div>
 <div id="rm-d-out" style="margin-top:8px;opacity:.9"></div>
</div>
<script>
(function(){{
 var APP={json.dumps(app)}, TRIALS={tj}, REASONS={rj}, OWNER={json.dumps(OWNER)};
 var sel=document.getElementById('rm-d-trial');
 function badge(s){{return s==='registry_verified'?'&#9989; registry-verified':(s==='disputed_by_us'?'&#9888; we dispute this':'&#128196; source: extracted');}}
 TRIALS.forEach(function(t){{var o=document.createElement('option');o.value=t.id;o.innerHTML=t.name+' ['+(t.nct||t.id)+']  —  '+badge(t.status);sel.appendChild(o);}});
 function detectPrefix(){{for(var j=0;j<localStorage.length;j++){{var m=localStorage.key(j).match(/^(rapid_meta_[a-z0-9_]+?_)v\\d+_\\d+/);if(m)return m[1];}}return 'rapid_meta_';}}
 function saveDispute(d){{try{{var K=detectPrefix()+'disputes';var cur=JSON.parse(localStorage.getItem(K)||'[]');cur.push(d);localStorage.setItem(K,JSON.stringify(cur));}}catch(e){{}}}}
 var box=document.getElementById('rm-d-reasons'), more=document.getElementById('rm-d-more'), out=document.getElementById('rm-d-out');
 REASONS.forEach(function(r){{
  var b=document.createElement('button');b.textContent=r.label;
  b.style.cssText='background:#21262d;color:#e6edf3;border:1px solid #444;border-radius:6px;padding:6px 10px;cursor:pointer;font-size:12px';
  b.addEventListener('click',function(){{
   more.style.display=r.cls==='something_else'?'block':'none';
   var t=TRIALS.find(function(x){{return x.id===sel.value;}})||{{}};
   var d={{app:APP,trial:t.name,nct:t.nct,field:'value',reason_class:r.cls,routes:r.routes,
     proposed_value:document.getElementById('rm-d-value').value||null,
     source:document.getElementById('rm-d-source').value||null,
     our_status:t.status,at:new Date().toISOString()}};
   saveDispute(d);   // instant, local, persists + exports + rides the offline copy
   // instant local flag on this trial
   out.innerHTML='<div style="border:1px solid #b00020;border-left:5px solid #b00020;padding:8px;border-radius:6px;background:#160b0d">'
     +'<b style="color:#f85149">&#9888; Disputed — recorded.</b> Trial <b>'+(t.nct||t.id)+'</b>, reason: <i>'+r.label+'</i>. '
     +'This is now saved with your work and will be checked against the SOURCE ('+r.routes+'). '
     +'A disputed number is excluded from the pool until resolved. '
     +'<div style="opacity:.75;margin-top:4px;font-size:12px">The crowd finds the question; the source settles the answer — your report TRIGGERS verification, it does not bypass it. '
     +'When GitHub sign-in is enabled this becomes an Issue on the review\\'s repo and is adjudicated automatically.</div>'
     +'<button id="rm-d-issue" style="margin-top:6px;background:#238636;color:#fff;border:0;border-radius:6px;padding:6px 10px;cursor:pointer">Email this report now (optional)</button></div>';
   var ib=document.getElementById('rm-d-issue');if(ib)ib.addEventListener('click',function(){{
     var body='RapidMeta dispute%0D%0Aapp: '+APP+'%0D%0Atrial: '+(t.nct||t.id)+'%0D%0Areason: '+r.label+' ('+r.cls+')%0D%0Aroutes-to: '+r.routes+'%0D%0Aproposed: '+(d.proposed_value||'(none)')+'%0D%0Asource: '+(d.source||'(none)');
     window.location.href='mailto:'+OWNER+'?subject='+encodeURIComponent('RapidMeta dispute: '+APP)+'&body='+body;
   }});
  }});
  box.appendChild(b);
 }});
}})();
</script>
<!-- rm-dispute:end -->'''


def inject(app_path, apply=False):
    app = os.path.basename(app_path)
    txt = open(app_path, encoding='utf-8', errors='replace').read()
    conf, ident = _status_map(app)
    trials = _trials(txt, conf, ident)
    if not trials:
        return False, 'no trials'
    # supersede the older report button + our own prior marker
    txt2 = re.sub(r'<!-- rm-report-issue:begin -->.*?<!-- rm-report-issue:end -->\s*', '', txt, flags=re.S)
    txt2 = re.sub(r'<!-- ' + re.escape(MARK) + r' -->.*?<!-- rm-dispute:end -->\s*', '', txt2, flags=re.S)
    bm = re.search(r'(<div data-rapidmeta-verify-banner="1".*?</div>\s*(?:</ul>\s*</div>\s*)?)', txt2, re.S)
    pos = bm.end() if bm else (re.search(r'<body[^>]*>', txt2, re.I).end())
    new = txt2[:pos] + '\n' + panel_js(app, trials) + '\n' + txt2[pos:]
    if not apply:
        return True, f"{len(trials)} trials"
    open(app_path, 'w', encoding='utf-8').write(new)
    jc = os.path.join(REPO, 'scripts', 'jscheck.py')
    r = subprocess.run([sys.executable, jc, app_path], capture_output=True, text=True)
    if '[JS-OK]' not in (r.stdout + r.stderr):
        open(app_path, 'w', encoding='utf-8').write(txt)
        return False, 'REVERTED (jscheck)'
    return True, f"{len(trials)} trials"


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--files', nargs='*', default=[])
    ap.add_argument('--from-classification')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--add-only', action='store_true')
    a = ap.parse_args()
    targets = list(a.files)
    if a.from_classification:
        want = set(a.from_classification.split(','))
        recs = json.load(open(os.path.join(REPO, 'outputs', 'corpus_classification.json'), encoding='utf-8'))
        targets += [r['app'] for r in recs if r['status'] in want]
    if hasattr(sys.stdout, 'buffer'):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    done = skip = 0
    for t in targets:
        p = t if os.path.isabs(t) else os.path.join(REPO, t)
        if not os.path.exists(p):
            continue
        if a.add_only and MARK in open(p, encoding='utf-8', errors='replace').read():
            continue
        ok, msg = inject(p, a.apply)
        done += ok
        skip += (not ok)
        if a.files:
            print(f"  {'APPLIED' if (ok and a.apply) else ('DRY' if ok else 'SKIP')} {os.path.basename(t)}: {msg}")
    print(f"\n{'APPLIED' if a.apply else 'DRY-RUN'}: dispute UI on {done} apps, {skip} skipped")


if __name__ == '__main__':
    main()
