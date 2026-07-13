#!/usr/bin/env python
"""Phase-1 adoption fix: session persistence + portable Save/Import state file.

A meta-analysis takes weeks. If closing the tab loses the work, the tool is a toy.
RapidMeta already writes its working state to localStorage under a per-app prefix
(so it survives a tab close), but there is no visible proof, no backup, and no way
to move machines. This panel adds, ADDITIVELY (it only reads/writes the app's own
localStorage namespace — it never touches the app's save logic):

  1. A visible "Saved locally" indicator (autosave status) so users TRUST it.
  2. "Save my work" -> one portable JSON state file (versioned + SHA-256 hashed,
     app-agnostic: every localStorage key under the app's prefix). Email it, back
     it up, move machines.
  3. "Import" -> verify checksum + app match, back up current first, then REPLACE
     and reload. (Codex-A: replace not merge; reject cross-app; checksum.)

Offline: SHA-256 via crypto.subtle (a browser primitive, no network). Idempotent,
jscheck-verified with auto-revert.
"""
from __future__ import annotations
import json, os, re, subprocess, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARK = 'rm-session-persist:begin'


def _prefix(txt):
    m = re.search(r'["\'](rapid_meta_[a-z0-9_]+?_)v\d+_\d+["\']', txt)
    return m.group(1) if m else None


def panel_js(app, prefix):
    slug = (prefix or 'rapid_meta_').replace('rapid_meta_', '').rstrip('_') or 'review'
    return f'''<!-- {MARK} -->
<div id="rm-persist" style="font-family:system-ui,sans-serif;font-size:13px;border:1px solid #2ea043;
 border-left:6px solid #2ea043;background:#0d1117;color:#e6edf3;padding:10px 15px;margin:10px;border-radius:8px;max-width:1100px">
 <b style="color:#3fb950">&#128190; Your work is saved</b>
 <span id="rm-saved-ind" style="opacity:.8;margin-left:8px">checking…</span>
 <div style="margin-top:7px">
  <button id="rm-save-work" style="background:#238636;color:#fff;border:0;border-radius:6px;padding:7px 12px;cursor:pointer;font-weight:600">Save my work (download)</button>
  <button id="rm-import-work" style="background:#1f6feb;color:#fff;border:0;border-radius:6px;padding:7px 12px;cursor:pointer;margin-left:6px">Import a saved file</button>
  <button id="rm-offline-copy" style="background:#8957e5;color:#fff;border:0;border-radius:6px;padding:7px 12px;cursor:pointer;margin-left:6px">&#11015; Download my review (runs offline)</button>
  <input id="rm-import-file" type="file" accept="application/json,.json" style="display:none">
 </div>
 <div style="opacity:.65;font-size:11px;margin-top:5px">Your work autosaves in THIS browser. It is not sent anywhere. To move machines, back up, or email a colleague — use <b>Save my work</b>. (Clearing your browser data still deletes local-only work — keep a saved file.)</div>
</div>
<script>
(function(){{
 var APP={json.dumps(app)}, PREFIX={json.dumps(prefix or '')}, SLUG={json.dumps(slug)}, FMT=1;
 function detectPrefix(){{
  if(PREFIX){{for(var i=0;i<localStorage.length;i++){{if(localStorage.key(i).indexOf(PREFIX)===0)return PREFIX;}}}}
  // fallback: any rapid_meta_*_v key namespace present
  for(var j=0;j<localStorage.length;j++){{var k=localStorage.key(j);var m=k.match(/^(rapid_meta_[a-z0-9_]+?_)v\\d+_\\d+/);if(m)return m[1];}}
  return PREFIX||'rapid_meta_';
 }}
 function entries(){{var p=detectPrefix(),e={{}};for(var i=0;i<localStorage.length;i++){{var k=localStorage.key(i);if(k.indexOf(p)===0)e[k]=localStorage.getItem(k);}}return e;}}
 function canon(e){{return JSON.stringify(e,Object.keys(e).sort());}}
 async function sha256(str){{try{{var b=new TextEncoder().encode(str);var h=await crypto.subtle.digest('SHA-256',b);return Array.from(new Uint8Array(h)).map(function(x){{return x.toString(16).padStart(2,'0');}}).join('');}}catch(e){{return '';}}}}
 function dl(obj,name){{var blob=new Blob([JSON.stringify(obj,null,1)],{{type:'application/json'}});var a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;document.body.appendChild(a);a.click();setTimeout(function(){{URL.revokeObjectURL(a.href);a.remove();}},1500);}}
 // autosave indicator
 var lastHash=null,lastSaved=null;
 function fmtTime(d){{return d?d.toLocaleString():'';}}
 function tick(){{var s=canon(entries());if(s!==lastHash){{lastHash=s;lastSaved=new Date();}}var el=document.getElementById('rm-saved-ind');if(el)el.textContent=lastSaved?('· last change '+fmtTime(lastSaved)+' · '+(Object.keys(entries()).length)+' items in this browser'):'no saved work yet — start working and it saves automatically';}}
 setInterval(tick,3000);tick();
 document.getElementById('rm-save-work').addEventListener('click',async function(){{
  var e=entries();if(!Object.keys(e).length){{alert('No saved work yet in this browser to export.');return;}}
  var file={{rapidmeta_state_file:FMT,schema_min:1,app:APP,slug:SLUG,prefix:detectPrefix(),saved_at:Date.now(),app_version:(Object.keys(e).find(function(k){{return /_v\\d+_\\d+$/.test(k);}})||'').replace(detectPrefix(),''),sha256:await sha256(canon(e)),entries:e}};
  dl(file, SLUG+'_myreview_'+new Date().toISOString().slice(0,10)+'.json');
 }});
 // Download a self-contained offline copy of THIS review, seeded with the user's
 // own work. Opening the file (no network) restores their exact session.
 document.getElementById('rm-offline-copy').addEventListener('click',function(){{
  var e=entries();
  var seed='<'+'script data-rm-seed="1">(function(){{try{{var O='+JSON.stringify(JSON.stringify(e))+';var d=JSON.parse(O);var p=Object.keys(d).find(function(k){{return /_v\\d+_\\d+$/.test(k);}});if(p&&!localStorage.getItem(p)){{Object.keys(d).forEach(function(k){{try{{localStorage.setItem(k,d[k]);}}catch(_){{}}}});}}}}catch(_){{}}}})();<'+'/script>';
  var html=document.documentElement.outerHTML;
  html=html.replace(/<script data-rm-seed="1">[\\s\\S]*?<\\/script>/,'');   // idempotent
  var bm=html.match(/<body[^>]*>/i);
  html=bm?html.replace(bm[0],bm[0]+'\\n'+seed):seed+html;
  var blob=new Blob(['<!doctype html>\\n'+html],{{type:'text/html'}});
  var a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=SLUG+'_my_review_offline.html';
  document.body.appendChild(a);a.click();setTimeout(function(){{URL.revokeObjectURL(a.href);a.remove();}},1500);
  alert('Downloaded a self-contained copy of your review with your work in it. Open it on any laptop — no internet needed — and your session is restored.');
 }});
 document.getElementById('rm-import-work').addEventListener('click',function(){{document.getElementById('rm-import-file').click();}});
 document.getElementById('rm-import-file').addEventListener('change',async function(ev){{
  var f=ev.target.files[0];if(!f)return;var obj;try{{obj=JSON.parse(await f.text());}}catch(e){{alert('Not a valid file.');return;}}
  if(!obj||obj.rapidmeta_state_file!==FMT||!obj.entries){{alert('This is not a RapidMeta "Save my work" file.');return;}}
  var p=detectPrefix();
  if(obj.prefix && obj.prefix!==p){{if(!confirm('This saved file is for a different review ("'+obj.app+'"). Importing it here may not work. Continue anyway?'))return;}}
  var h=await sha256(canon(obj.entries));
  if(obj.sha256 && h && h!==obj.sha256){{if(!confirm('Checksum does not match — the file may be corrupted or edited. Import anyway?'))return;}}
  if(!confirm('This will REPLACE the current work in this browser with the saved file. Your current work will be downloaded as a backup first. Continue?'))return;
  // backup current, then REPLACE
  var cur=entries();if(Object.keys(cur).length)dl({{rapidmeta_state_file:FMT,app:APP,slug:SLUG,prefix:p,saved_at:Date.now(),note:'auto-backup before import',entries:cur}}, SLUG+'_backup_before_import.json');
  Object.keys(cur).forEach(function(k){{localStorage.removeItem(k);}});
  Object.keys(obj.entries).forEach(function(k){{try{{localStorage.setItem(k,obj.entries[k]);}}catch(e){{}}}});
  alert('Your saved work has been restored. Reloading.');location.reload();
 }});
}})();
</script>
<!-- rm-session-persist:end -->'''


def inject(app_path, apply=False):
    app = os.path.basename(app_path)
    txt = open(app_path, encoding='utf-8', errors='replace').read()
    prefix = _prefix(txt)
    txt2 = re.sub(r'<!-- ' + re.escape(MARK) + r' -->.*?<!-- rm-session-persist:end -->\s*', '', txt, flags=re.S)
    bm = re.search(r'(<div data-rapidmeta-verify-banner="1".*?</div>\s*(?:</ul>\s*</div>\s*)?)', txt2, re.S)
    pos = bm.end() if bm else (re.search(r'<body[^>]*>', txt2, re.I).end())
    new = txt2[:pos] + '\n' + panel_js(app, prefix) + '\n' + txt2[pos:]
    if not apply:
        return True, f"prefix={prefix}"
    open(app_path, 'w', encoding='utf-8').write(new)
    jc = os.path.join(REPO, 'scripts', 'jscheck.py')
    r = subprocess.run([sys.executable, jc, app_path], capture_output=True, text=True)
    if '[JS-OK]' not in (r.stdout + r.stderr):
        open(app_path, 'w', encoding='utf-8').write(txt)
        return False, 'REVERTED (jscheck)'
    return True, f"prefix={prefix}"


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
    print(f"\n{'APPLIED' if a.apply else 'DRY-RUN'}: session-persistence panel on {done} apps, {skip} skipped")


if __name__ == '__main__':
    main()
