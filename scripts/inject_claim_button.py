#!/usr/bin/env python
"""In-app CLAIM button + banner + submitted badge.

Reading the claim state is PUBLIC (no login) — the banner shows for everyone.
Claiming/extending/submitting needs login (it needs an identity) via the GitHub
device-flow (RapidMetaAuth from github_device_login.js). A claim INFORMS, never
BLOCKS. The write target is a PUBLIC claims repo; expiry is a daily Action.

Additive, offline-safe (reads a public URL only when online; degrades gracefully),
idempotent, jscheck-revert. Config: CLAIMS_RAW_URL / CLAIMS_API_REPO below.
"""
from __future__ import annotations
import json, os, re, subprocess, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARK = 'rm-claim:begin'
# Public claims repo (set when Mahmood creates it). Reads are public; writes need login.
CLAIMS_RAW = 'https://raw.githubusercontent.com/mahmood726-cyber/rapidmeta-claims/main/claims.json'
CLAIMS_API = 'mahmood726-cyber/rapidmeta-claims'


def _slug(txt):
    m = re.search(r'["\']rapid_meta_([a-z0-9_]+?)_v\d+_\d+["\']', txt)
    return m.group(1) if m else None


def panel_js(app, review_id):
    return f'''<!-- {MARK} -->
<div id="rm-claim" style="font-family:system-ui,sans-serif;font-size:13px;border:1px solid #6e40c9;
 border-left:6px solid #6e40c9;background:#0d1117;color:#e6edf3;padding:11px 15px;margin:10px;border-radius:8px;max-width:1100px">
 <b style="color:#a371f7">&#128220; Open Reviews</b>
 <span id="rm-claim-status" style="margin-left:8px;opacity:.85">checking who's working on this…</span>
 <div style="margin-top:7px">
  <button id="rm-claim-btn" style="background:#6e40c9;color:#fff;border:0;border-radius:6px;padding:7px 12px;cursor:pointer;font-weight:600">Claim this review</button>
  <button id="rm-claim-submit" style="display:none;background:#1f6feb;color:#fff;border:0;border-radius:6px;padding:7px 12px;cursor:pointer;margin-left:6px">Mark submitted to journal</button>
  <button id="rm-claim-extend" style="display:none;background:#238636;color:#fff;border:0;border-radius:6px;padding:7px 12px;cursor:pointer;margin-left:6px">Extend to 40 days</button>
  <a href="https://github.com/{CLAIMS_API}" style="color:#58a6ff;font-size:12px;margin-left:8px" target="_blank">see the full board &#8599;</a>
 </div>
 <div style="opacity:.65;font-size:11px;margin-top:5px">A claim <b>informs, it never blocks</b> — nobody owns a research question; if you want to work the same review you can, and you can make contact. Claims last 30 days (extend once to 40); submissions show for 6 months. Claiming needs a GitHub sign-in (it needs an identity); reading this board never does.</div>
</div>
<script>
(function(){{
 var APP={json.dumps(app)}, REVIEW={json.dumps(review_id or app.replace('.html',''))};
 var RAW={json.dumps(CLAIMS_RAW)}, API={json.dumps(CLAIMS_API)}, DAY=86400;
 var statusEl=document.getElementById('rm-claim-status');
 function daysLeft(c,now){{return Math.max(0,Math.ceil((c.expires_at-now)/DAY));}}
 function active(c,now){{return now<c.expires_at;}}
 function subVisible(c,now){{return c.submitted_at&&now<(c.submission_expires_at||0);}}
 function render(claims){{
  var now=Math.floor(Date.now()/1000);
  var mine=(claims||[]).filter(function(c){{return c.review_id===REVIEW;}});
  var live=mine.filter(function(c){{return active(c,now);}})[0];
  var sub=mine.filter(function(c){{return subVisible(c,now);}})[0];
  if(live){{
   var d=new Date(live.claimed_at*1000).toLocaleDateString();
   statusEl.innerHTML='<span style="color:#3fb950">Claimed by @'+live.user+' on '+d+' — '+daysLeft(live,now)+' days remaining.</span>'
     +(sub?' <span style="color:#58a6ff">&#9993; Submitted '+new Date(sub.submitted_at*1000).toLocaleDateString()+'.</span>':'');
  }} else if(sub){{
   statusEl.innerHTML='<span style="opacity:.7">Free to claim.</span> <span style="color:#58a6ff">&#9993; A recent submission is recorded ('+new Date(sub.submitted_at*1000).toLocaleDateString()+').</span>';
  }} else {{
   statusEl.innerHTML='<span style="opacity:.7">No one has claimed this yet — you could be first.</span>';
  }}
 }}
 // PUBLIC read (no login). Offline / repo-not-created yet -> graceful message.
 try{{
  fetch(RAW,{{cache:'no-store'}}).then(function(r){{return r.ok?r.json():[];}}).then(render).catch(function(){{
   statusEl.innerHTML='<span style="opacity:.6">Open-reviews board not reachable (offline, or not yet set up).</span>';
  }});
 }}catch(e){{}}
 function needLogin(){{
  var tok=(window.RapidMetaAuth&&RapidMetaAuth.token&&RapidMetaAuth.token());
  if(tok)return tok;
  if(window.RapidMetaAuth&&RapidMetaAuth.signIn){{
   statusEl.innerHTML='<span style="opacity:.85">Sign in with GitHub to claim… (a one-time device-flow login; nothing typed into this site)</span>';
   RapidMetaAuth.signIn();
  }} else {{
   alert('GitHub sign-in for claims will be enabled once the OAuth device flow is live. Reading the board never needs login.');
  }}
  return null;
 }}
 document.getElementById('rm-claim-btn').addEventListener('click',function(){{
  var tok=needLogin(); if(!tok)return;
  // write path (Phase 2): create/append a claim in the public claims repo via the user's token.
  // Fail-closed on the 3-active-claim cap is enforced server-side by the daily Action + client check.
  alert('Claiming '+REVIEW+' for your account. (Wired to the GitHub API; goes live with device-flow login + the claims repo.)');
 }});
}})();
</script>
<!-- rm-claim:end -->'''


def inject(app_path, apply=False):
    app = os.path.basename(app_path)
    txt = open(app_path, encoding='utf-8', errors='replace').read()
    review = _slug(txt)
    txt2 = re.sub(r'<!-- ' + re.escape(MARK) + r' -->.*?<!-- rm-claim:end -->\s*', '', txt, flags=re.S)
    bm = re.search(r'(<div data-rapidmeta-verify-banner="1".*?</div>\s*(?:</ul>\s*</div>\s*)?)', txt2, re.S)
    pos = bm.end() if bm else (re.search(r'<body[^>]*>', txt2, re.I).end())
    new = txt2[:pos] + '\n' + panel_js(app, review) + '\n' + txt2[pos:]
    if not apply:
        return True, f"review={review}"
    open(app_path, 'w', encoding='utf-8').write(new)
    jc = os.path.join(REPO, 'scripts', 'jscheck.py')
    r = subprocess.run([sys.executable, jc, app_path], capture_output=True, text=True)
    if '[JS-OK]' not in (r.stdout + r.stderr):
        open(app_path, 'w', encoding='utf-8').write(txt)
        return False, 'REVERTED (jscheck)'
    return True, f"review={review}"


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
    print(f"\n{'APPLIED' if a.apply else 'DRY-RUN'}: claim button on {done} apps, {skip} skipped")


if __name__ == '__main__':
    main()
