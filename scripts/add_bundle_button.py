#!/usr/bin/env python
"""P1 — the "Download this review + toolkit" button (the headline feature).

Additive, offline, idempotent. For a count-traceable app it:
  1. extracts each trial's log-effect + variance (the same 2x2 basis the app
     plots), on the app's measure (OR for counts, else HR from CI, else MD/SE),
  2. computes the DerSimonian-Laird random-effects pool in Python (build time),
  3. embeds a self-contained bundle (data + deterministic Python toolkit + tests
     + manifest) and a pure-JS stored-ZIP writer with a real CRC32,
  4. injects a button before </body> that downloads `<APP>_bundle.zip`.

The bundle reproduces the pooled number bit-for-bit in a clean room (no model, no
network) and FAILS LOUDLY if any count, number, or the protocol is tampered with.

Usage:
  python scripts/add_bundle_button.py --files MALARIA_VACCINE_REVIEW.html [--apply]
  python scripts/add_bundle_button.py --from-classification provenance-ok,verified [--apply]
"""
from __future__ import annotations
import argparse, base64, glob, io, json, math, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from assert_count_effect_consistency import _objbody, _top_entries, _num, _sval  # noqa
import count_consistency as cc  # noqa

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HARNESS = os.path.join(REPO, 'scripts', 'bundle_harness')
MARKER = 'rm-bundle-button:begin'
Z = 1.959963984540054


# ---- per-trial effect extraction (matches the app's plotData basis) --------

def _woolf_or(tE, tN, cE, cN):
    a, b, c, d = tE, tN - tE, cE, cN - cE
    if min(a, b, c, d) == 0:                     # Haldane-Anscombe
        a, b, c, d = a + .5, b + .5, c + .5, d + .5
    y = math.log((a * d) / (b * c))
    v = 1/a + 1/b + 1/c + 1/d
    return y, v


def _trial_for(measure, k, o):
    """Extract one trial's (y, v) for a given measure, or None if unsupported.
    Kept separate so we can try EVERY measure and pick the best — never assume
    'any counts -> OR' (that greedily drops HR/MD pools with a stray count row)."""
    tE, tN, cE, cN = _num(o,'tE'), _num(o,'tN'), _num(o,'cE'), _num(o,'cN')
    rec = {'id': str(k)}
    if measure == 'OR':
        if None not in (tE, tN, cE, cN) and tN > 0 and cN > 0 and 0 <= tE <= tN and 0 <= cE <= cN:
            y, v = _woolf_or(tE, tN, cE, cN)
            rec.update({'y': y, 'v': v, 'tE': tE, 'tN': tN, 'cE': cE, 'cN': cN})
            return rec
    elif measure == 'HR':
        hr, lo, hi = _num(o,'publishedHR'), _num(o,'hrLCI'), _num(o,'hrUCI')
        if hr and lo and hi and hr > 0 and lo > 0 and hi > 0:
            se = (math.log(hi) - math.log(lo)) / (2 * Z)
            if se > 0:
                rec.update({'y': math.log(hr), 'v': se * se,
                            'tE': tE, 'tN': tN, 'cE': cE, 'cN': cN})
                return rec
    elif measure == 'MD':
        md, se = _num(o, 'md'), _num(o, 'se')
        if md is not None and se and se > 0:
            rec.update({'y': md, 'v': se * se, 'tE': None, 'tN': None, 'cE': None, 'cN': None})
            return rec
    return None


def _extract(entries):
    """Return (measure, trials[]). Try EVERY measure (OR / HR / MD) and pick the
    one that yields the MOST poolable trials (>=2). Assume the parser is wrong
    before assuming the data is un-poolable — an app with 2 HR+CI trials plus one
    stray count row must NOT be forced to OR (k=1) and skipped."""
    entries = list(entries)
    cands = {}
    for measure in ('OR', 'HR', 'MD'):
        trials = [r for r in (_trial_for(measure, k, o) for k, o in entries) if r]
        if len(trials) >= 2:
            cands[measure] = trials
    if not cands:
        return None, []
    pref = {'OR': 3, 'HR': 2, 'MD': 1}   # tie-break: prefer OR > HR > MD
    best = max(cands, key=lambda m: (len(cands[m]), pref[m]))
    return best, cands[best]


def _dl(trials):
    ys = [t['y'] for t in trials]; vs = [t['v'] for t in trials]; k = len(ys)
    wf = [1/v for v in vs]; sw = sum(wf)
    mu_fe = sum(w*y for w, y in zip(wf, ys)) / sw
    Q = sum(w*(y-mu_fe)**2 for w, y in zip(wf, ys)); df = k - 1
    c = sw - sum(w*w for w in wf)/sw
    tau2 = max(0.0, (Q-df)/c) if (k > 1 and c > 0) else 0.0
    wr = [1/(v+tau2) for v in vs]; swr = sum(wr)
    mu = sum(w*y for w, y in zip(wr, ys))/swr; se = math.sqrt(1/swr)
    i2 = max(0.0, (Q-df)/Q)*100 if Q > 0 else 0.0
    return {'k': k, 'logEffect': mu, 'se': se, 'lci': mu-Z*se, 'uci': mu+Z*se,
            'tau2': tau2, 'Q': Q, 'I2': i2, 'estimator': 'DL'}


# ---- bundle assembly -------------------------------------------------------

def _harness_files():
    out = {}
    for fn in ('pool.py', 'consistency.py', 'reproduce.py', 'test_reproduce.py'):
        out[fn] = open(os.path.join(HARNESS, fn), encoding='utf-8').read()
    return out


def _protocol_hash(app_name):
    p = os.path.join(REPO, 'protocol', app_name.replace('.html', '.txt'))
    if os.path.exists(p):
        import hashlib
        return hashlib.sha256(open(p, encoding='utf-8').read().encode()).hexdigest(), \
            open(p, encoding='utf-8').read()
    return None, None


def build_bundle(app_path):
    app = os.path.basename(app_path)
    txt = open(app_path, encoding='utf-8', errors='replace').read()
    m = re.search(r'realData\s*:\s*\{', txt)
    if not m:
        return None, 'no realData'
    entries = list(_top_entries(_objbody(txt, m.end()-1)))
    measure, trials = _extract(entries)
    if measure is None or len(trials) < 2:
        return None, f'not count-traceable (measure={measure}, k={len(trials)})'
    pool = _dl(trials)

    import hashlib
    realdata = {t['id']: {k: t.get(k) for k in ('tE', 'tN', 'cE', 'cN', 'y', 'v')}
                for t in trials}
    result = {'app': app, 'measure': measure, 'trials': trials,
              'pooled_DL': {k: pool[k] for k in ('k', 'logEffect', 'se', 'lci',
                                                 'uci', 'tau2', 'Q', 'I2')}}
    files = {}
    files['data/realData.json'] = json.dumps(realdata, indent=1, sort_keys=True)
    files['data/result.json'] = json.dumps(result, indent=1, sort_keys=True)
    for fn, body in _harness_files().items():
        files[f'harness/{fn}' if fn in ('pool.py', 'consistency.py') else fn] = body
    prot_hash, prot_body = _protocol_hash(app)
    if prot_body:
        files['protocol.txt'] = prot_body
    man = {'sha256': {'realData.json': hashlib.sha256(files['data/realData.json'].encode()).hexdigest(),
                      'result.json': hashlib.sha256(files['data/result.json'].encode()).hexdigest()}}
    if prot_hash:
        man['protocol_sha256'] = prot_hash
    files['MANIFEST.json'] = json.dumps(man, indent=1)
    eff = math.exp(pool['logEffect']) if measure in ('OR','RR','HR','IRR') else pool['logEffect']
    lci = math.exp(pool['lci']) if measure in ('OR','RR','HR','IRR') else pool['lci']
    uci = math.exp(pool['uci']) if measure in ('OR','RR','HR','IRR') else pool['uci']
    files['README.md'] = (
        f"# RapidMeta clean-room bundle — {app}\n\n"
        f"Reproduce this meta-analysis **offline**, with no model and no network, in one command:\n\n"
        f"    python reproduce.py\n\n"
        f"Or run the full test suite:\n\n"
        f"    python -m pytest test_reproduce.py -q\n\n"
        f"## What it checks\n"
        f"- The pooled **{measure} = {eff:.4f} (95% CI {lci:.4f}-{uci:.4f})**, k={pool['k']}, "
        f"DerSimonian-Laird random effects, is **recomputed from the per-trial data** and must "
        f"match to machine precision (bit-for-bit).\n"
        f"- Every trial's displayed 2x2 counts imply the same direction as its effect.\n"
        f"- The data has not been tampered with (SHA-256 manifest).\n"
        + ("- The analysis still matches the **pre-registered protocol** hash.\n" if prot_hash else "")
        + f"\n## What this proves (and what it doesn't)\n"
        f"It proves the review is **internally consistent** and **reproduces from its own raw data**, "
        f"offline. Changing any trial's counts changes the recomputed pool, so a tampered number cannot "
        f"silently survive. The SHA-256 manifest is *inside* the bundle, so it detects casual edits but not "
        f"an attacker who rewrites both data and manifest — for **authenticity** (that this is the unmodified "
        f"RapidMeta review), compare the pooled value above / the manifest hash against the published "
        f"RapidMeta corpus.\n\n"
        f"`reproduce.py` is short, auditable, non-mutating (it only reads local JSON) and uses only the "
        f"Python 3.8+ standard library. Nothing here calls out to the network.\n")
    return files, None


# ---- pure-JS stored-ZIP writer + button (injected) -------------------------

def button_js(app, files):
    payload = {name: base64.b64encode(body.encode('utf-8')).decode('ascii')
               for name, body in files.items()}
    data_js = json.dumps(payload)
    zipname = app.replace('.html', '') + '_bundle.zip'
    # a minimal, correct stored-ZIP (no compression) writer with CRC-32
    return f'''<!-- {MARKER} -->
<div id="rm-bundle-box" style="font-family:system-ui,sans-serif;margin:10px;max-width:1100px">
<button id="rm-bundle-btn" style="background:#1f6feb;color:#fff;border:0;border-radius:8px;
 padding:11px 18px;font-size:14px;font-weight:600;cursor:pointer">&#128230; Download this review + reproducibility toolkit</button>
<span style="opacity:.7;font-size:12px;margin-left:10px">offline &middot; no model &middot; no network &middot; reproduces the pooled number bit-for-bit</span>
</div>
<script>
(function(){{
 var FILES={data_js};
 var T=[];for(var n=0;n<256;n++){{var c=n;for(var q=0;q<8;q++)c=(c&1)?(0xEDB88320^(c>>>1)):(c>>>1);T[n]=c>>>0;}}
 function crc32(b){{var c=0xFFFFFFFF;for(var i=0;i<b.length;i++)c=T[(c^b[i])&0xFF]^(c>>>8);return (c^0xFFFFFFFF)>>>0;}}
 function b64(s){{var bin=atob(s),a=new Uint8Array(bin.length);for(var i=0;i<bin.length;i++)a[i]=bin.charCodeAt(i);return a;}}
 function u16(v){{return [v&0xFF,(v>>>8)&0xFF];}}
 function u32(v){{return [v&0xFF,(v>>>8)&0xFF,(v>>>16)&0xFF,(v>>>24)&0xFF];}}
 function strb(s){{var a=[];for(var i=0;i<s.length;i++)a.push(s.charCodeAt(i)&0xFF);return a;}}
 function buildZip(files){{
  var chunks=[],central=[],offset=0;
  Object.keys(files).sort().forEach(function(name){{
   var data=b64(files[name]),crc=crc32(data),nb=strb(name);
   var lh=[].concat(u32(0x04034b50),u16(20),u16(0),u16(0),u16(0),u16(0x21),u32(crc),u32(data.length),u32(data.length),u16(nb.length),u16(0),nb);
   var lhb=new Uint8Array(lh.length+data.length);lhb.set(lh,0);lhb.set(data,lh.length);
   chunks.push(lhb);
   central.push([].concat(u32(0x02014b50),u16(20),u16(20),u16(0),u16(0),u16(0),u16(0x21),u32(crc),u32(data.length),u32(data.length),u16(nb.length),u16(0),u16(0),u16(0),u16(0),u32(0),u32(offset),nb));
   offset+=lhb.length;
  }});
  var cd=[],cdlen=0;central.forEach(function(c){{cd.push(new Uint8Array(c));cdlen+=c.length;}});
  var eocd=new Uint8Array([].concat(u32(0x06054b50),u16(0),u16(0),u16(central.length),u16(central.length),u32(cdlen),u32(offset),u16(0)));
  var total=offset+cdlen+eocd.length,out=new Uint8Array(total),p=0;
  chunks.forEach(function(c){{out.set(c,p);p+=c.length;}});
  cd.forEach(function(c){{out.set(c,p);p+=c.length;}});
  out.set(eocd,p);return out;
 }}
 document.getElementById('rm-bundle-btn').addEventListener('click',function(){{
  try{{
   var zip=buildZip(FILES);
   var blob=new Blob([zip],{{type:'application/zip'}});
   var a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download={json.dumps(zipname)};
   document.body.appendChild(a);a.click();setTimeout(function(){{URL.revokeObjectURL(a.href);a.remove();}},1500);
  }}catch(e){{alert('Bundle build failed: '+e);}}
 }});
}})();
</script>
<!-- rm-bundle-button:end -->'''


def inject(app_path, apply=False):
    app = os.path.basename(app_path)
    files, err = build_bundle(app_path)
    if err:
        return False, err
    txt = open(app_path, encoding='utf-8', errors='replace').read()
    txt = re.sub(r'<!-- ' + re.escape(MARKER) + r' -->.*?<!-- rm-bundle-button:end -->\s*',
                 '', txt, flags=re.S)
    js = button_js(app, files)
    # Place the button EARLY — after the verification banner if present, else right
    # after <body>. RapidMeta apps build an export-HTML string (printBlob) that
    # contains LITERAL <script>/</script> tokens, leaving unpaired <script> opens.
    # A new <script> pair added before </body> gets its </script> "stolen" by an
    # earlier unpaired literal open (jscheck block-swallow). Injecting our pair
    # before that fragile region keeps the app's tag pairing byte-identical.
    bm = re.search(r'(<div data-rapidmeta-verify-banner="1".*?</div>\s*(?:</ul>\s*</div>\s*)?)', txt, re.S)
    if bm:
        pos = bm.end()
    else:
        b = re.search(r'<body[^>]*>', txt, re.I)
        if not b:
            return False, 'no <body>'
        pos = b.end()
    new = txt[:pos] + '\n' + js + '\n' + txt[pos:]
    k = files['data/result.json'].count('"id"')
    if not apply:
        return True, f"k={k}"
    open(app_path, 'w', encoding='utf-8').write(new)
    # SAFETY: jscheck after writing; if the injection broke the app's JS, REVERT
    # (the app's printBlob literal-<script> region can make placement fragile).
    jc = os.path.join(REPO, 'scripts', 'jscheck.py')
    if os.path.exists(jc):
        r = subprocess.run([sys.executable, jc, app_path], capture_output=True, text=True)
        if '[JS-OK]' not in (r.stdout + r.stderr):
            open(app_path, 'w', encoding='utf-8').write(txt)   # revert to original
            return False, 'REVERTED (jscheck broke) — left unchanged'
    return True, f"k={k}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--files', nargs='*', default=[])
    ap.add_argument('--from-classification')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--limit', type=int)
    ap.add_argument('--add-only', action='store_true',
                    help='skip apps that already carry a bundle button (purely additive)')
    a = ap.parse_args()
    targets = list(a.files)
    if a.from_classification:
        want = set(a.from_classification.split(','))
        recs = json.load(open(os.path.join(REPO, 'outputs', 'corpus_classification.json'), encoding='utf-8'))
        targets += [r['app'] for r in recs if r['status'] in want]
    if a.limit:
        targets = targets[:a.limit]
    if hasattr(sys.stdout, 'buffer') and getattr(sys.stdout, 'encoding', '').lower() != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    done = skip = 0
    for t in targets:
        p = t if os.path.isabs(t) else os.path.join(REPO, t)
        if not os.path.exists(p):
            print(f"  MISS {t}"); continue
        if a.add_only and MARKER in open(p, encoding='utf-8', errors='replace').read():
            continue                      # already seeded — leave untouched
        ok, msg = inject(p, a.apply)
        if ok:
            done += 1
            if a.files or done <= 5:
                print(f"  {'APPLIED' if a.apply else 'DRY'} {os.path.basename(t)}: {msg}")
        else:
            skip += 1
            if a.files:
                print(f"  SKIP {os.path.basename(t)}: {msg}")
    print(f"\n{'APPLIED' if a.apply else 'DRY-RUN'}: bundle button on {done} apps, {skip} skipped")
    return 0


if __name__ == '__main__':
    sys.exit(main())
