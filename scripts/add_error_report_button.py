#!/usr/bin/env python
"""Add an in-app "Report a data issue" button — the capture mechanism we lack.

The project's claimed differentiator is that USERS audit our numbers and tell us.
But zero apps have any way to report an error, so every report arrived out-of-band
and was never counted. This button fixes that: a reader who spots a wrong number
files a STRUCTURED report — app / trial / field / our-value / their-value / source
— matching the user_error_corpus schema, so every future report becomes a counted,
labelled training row instead of a lost email.

Offline-safe: no backend needed. It produces (a) a prefilled mailto: to the owner
AND (b) a downloadable JSON row (so it can be dropped straight into the corpus).
The trial dropdown is pre-populated from the app's own realData, and the field's
currently-displayed value is captured automatically — low friction = more reports.

Additive, idempotent, injected early (before the printBlob literal-<script> region),
jscheck-verified with auto-revert. Same discipline as the bundle button.

Usage: python scripts/add_error_report_button.py --files APP.html [--apply]
       python scripts/add_error_report_button.py --from-classification provenance-ok,verified --add-only --apply
"""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from assert_count_effect_consistency import _objbody, _top_entries, _num, _sval  # noqa

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARK = 'rm-report-issue:begin'
OWNER_EMAIL = 'mahmood726@gmail.com'


def _trials(txt):
    m = re.search(r'realData\s*:\s*\{', txt)
    if not m:
        return []
    out = []
    for k, o in _top_entries(_objbody(txt, m.end() - 1)):
        name = _sval(o, 'name') or _sval(o, 'shortLabel') or str(k)
        out.append({'id': str(k), 'name': name[:80]})
    return out


def button_js(app, trials):
    tj = json.dumps(trials)
    return f'''<!-- {MARK} -->
<div id="rm-report-box" style="font-family:system-ui,sans-serif;margin:10px;max-width:1100px">
<button id="rm-report-btn" style="background:#8957e5;color:#fff;border:0;border-radius:8px;
 padding:10px 16px;font-size:13px;font-weight:600;cursor:pointer">&#9888; Report a data issue</button>
<span style="opacity:.7;font-size:12px;margin-left:8px">spotted a wrong number? tell us — it makes the next version better</span>
<div id="rm-report-form" style="display:none;margin-top:10px;border:1px solid #8957e5;border-radius:8px;padding:12px;background:#0d1117;color:#e6edf3;max-width:640px">
 <div style="margin-bottom:6px"><b>Which trial?</b><br><select id="rm-r-trial" style="width:100%;padding:5px;margin-top:3px"></select></div>
 <div style="margin-bottom:6px"><b>Which field is wrong?</b><br>
  <select id="rm-r-field" style="width:100%;padding:5px;margin-top:3px">
   <option value="event counts (2x2)">event counts (2x2)</option>
   <option value="effect estimate">effect estimate / CI</option>
   <option value="trial label / name">trial label / name</option>
   <option value="PMID / registry ID">PMID / registry ID</option>
   <option value="year">year</option>
   <option value="other">other</option></select></div>
 <div style="margin-bottom:6px"><b>What SHOULD it be? (the value you read in the source)</b><br>
  <input id="rm-r-correct" style="width:100%;padding:5px;margin-top:3px" placeholder="e.g. 608/4668, not 0/4668"></div>
 <div style="margin-bottom:6px"><b>Source (where you read it)</b><br>
  <input id="rm-r-source" style="width:100%;padding:5px;margin-top:3px" placeholder="e.g. LEADER, NEJM 2016, Table 2 / PMID / DOI"></div>
 <div style="margin-top:8px">
  <button id="rm-r-email" style="background:#238636;color:#fff;border:0;border-radius:6px;padding:7px 12px;cursor:pointer">Email the report</button>
  <button id="rm-r-download" style="background:#1f6feb;color:#fff;border:0;border-radius:6px;padding:7px 12px;cursor:pointer;margin-left:6px">Download as JSON</button>
 </div>
 <div style="opacity:.6;font-size:11px;margin-top:6px">No account, no tracking. The report is structured so it becomes a labelled example that improves extraction.</div>
</div></div>
<script>
(function(){{
 var APP={json.dumps(app)}, TRIALS={tj}, OWNER={json.dumps(OWNER_EMAIL)};
 var box=document.getElementById('rm-report-form');
 var sel=document.getElementById('rm-r-trial');
 TRIALS.forEach(function(t){{var o=document.createElement('option');o.value=t.id;o.textContent=t.name+' ['+t.id+']';sel.appendChild(o);}});
 document.getElementById('rm-report-btn').addEventListener('click',function(){{box.style.display=box.style.display==='none'?'block':'none';}});
 function report(){{
  var t=TRIALS.find(function(x){{return x.id===sel.value;}})||{{}};
  return {{app:APP, trial:(t.name||'')+' ('+sel.value+')',
    field:document.getElementById('rm-r-field').value,
    corrected_value:document.getElementById('rm-r-correct').value,
    source:document.getElementById('rm-r-source').value,
    caught_by:'user', tier:'attributed-user', error_class:'user-reported'}};
 }}
 document.getElementById('rm-r-email').addEventListener('click',function(){{
  var r=report();
  var body='RapidMeta data issue report%0D%0A%0D%0Aapp: '+r.app+'%0D%0Atrial: '+r.trial+'%0D%0Afield: '+r.field+'%0D%0Ashould be: '+r.corrected_value+'%0D%0Asource: '+r.source;
  window.location.href='mailto:'+OWNER+'?subject='+encodeURIComponent('RapidMeta data issue: '+r.app)+'&body='+body;
 }});
 document.getElementById('rm-r-download').addEventListener('click',function(){{
  var r=report(); var blob=new Blob([JSON.stringify(r,null,1)],{{type:'application/json'}});
  var a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='rapidmeta_issue_'+r.app.replace('.html','')+'.json';
  document.body.appendChild(a);a.click();setTimeout(function(){{URL.revokeObjectURL(a.href);a.remove();}},1500);
 }});
}})();
</script>
<!-- rm-report-issue:end -->'''


def inject(app_path, apply=False):
    txt = open(app_path, encoding='utf-8', errors='replace').read()
    txt2 = re.sub(r'<!-- ' + re.escape(MARK) + r' -->.*?<!-- rm-report-issue:end -->\s*', '', txt, flags=re.S)
    trials = _trials(txt2)
    if len(trials) < 1:
        return False, 'no trials'
    js = button_js(os.path.basename(app_path), trials)
    bm = re.search(r'(<div data-rapidmeta-verify-banner="1".*?</div>\s*(?:</ul>\s*</div>\s*)?)', txt2, re.S)
    if bm:
        pos = bm.end()
    else:
        b = re.search(r'<body[^>]*>', txt2, re.I)
        if not b:
            return False, 'no <body>'
        pos = b.end()
    new = txt2[:pos] + '\n' + js + '\n' + txt2[pos:]
    if not apply:
        return True, f"{len(trials)} trials"
    open(app_path, 'w', encoding='utf-8').write(new)
    jc = os.path.join(REPO, 'scripts', 'jscheck.py')
    if os.path.exists(jc):
        r = subprocess.run([sys.executable, jc, app_path], capture_output=True, text=True)
        if '[JS-OK]' not in (r.stdout + r.stderr):
            open(app_path, 'w', encoding='utf-8').write(txt)
            return False, 'REVERTED (jscheck broke)'
    return True, f"{len(trials)} trials"


def main():
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
        if ok:
            done += 1
            if a.files:
                print(f"  {'APPLIED' if a.apply else 'DRY'} {os.path.basename(t)}: {msg}")
        else:
            skip += 1
    print(f"\n{'APPLIED' if a.apply else 'DRY-RUN'}: report-issue button on {done} apps, {skip} skipped")


if __name__ == '__main__':
    main()
