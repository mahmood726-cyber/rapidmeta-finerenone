#!/usr/bin/env python
"""Read-only audit: detect shared-control multi-arm extraction errors in RapidMeta apps.

A parent trial with >=2 intervention arms vs ONE shared control is sometimes extracted
as >=2 rows that each REPEAT the same control (cE,cN). Naive pairwise pooling then
double-counts the control patients/events. Flag those apps.

Signals (per app, among included binary trials):
  A) same pmid in >=2 rows                         -> definite multi-arm
  B) identical (cE,cN) in >=2 rows, cN>0           -> shared-control duplication
  C) normalized name collision (dose/arm suffix)   -> multi-arm split
"""
import re, io, os, glob, json, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

def extract(src):
    rows=[]
    for c in src.split('{name:"')[1:]:
        name=c.split('"',1)[0]
        win=c[:900]
        def g(k):
            m=re.search(k+r':(-?\d+(?:\.\d+)?)',win); return m.group(1) if m else None
        tE,tN,cE,cN=g('tE'),g('tN'),g('cE'),g('cN')
        pm=re.search(r'pmid:"([^"]*)"',win)
        inc = not re.search(r'included:\s*false', win[:200])
        if tE and tN and cE and cN:
            rows.append(dict(name=name,pmid=(pm.group(1) if pm else ""),
                             tE=int(float(tE)),tN=int(float(tN)),
                             cE=int(float(cE)),cN=int(float(cN)),inc=inc))
    return rows

def norm(n):
    n=n.lower()
    n=re.sub(r'\s*\(.*?\)','',n)              # drop parenthetical (dose/arm)
    n=re.sub(r'\b(high|low|mid|medium|\d+\s*mg|once|twice|daily|bid|qd|arm|dose)\b','',n)
    return re.sub(r'[^a-z0-9]','',n)

def audit(path):
    src=io.open(path,encoding="utf-8",errors="replace").read()
    rows=[r for r in extract(src) if r['inc']]
    if len(rows)<2: return None
    flags=[]
    # A: pmid repeats
    pm=collections.Counter(r['pmid'] for r in rows if r['pmid'])
    pdup={k:v for k,v in pm.items() if v>=2}
    # B: identical control (cE,cN) across rows
    ctl=collections.defaultdict(list)
    for i,r in enumerate(rows):
        ctl[(r['cE'],r['cN'])].append(i)
    cdup={k:v for k,v in ctl.items() if len(v)>=2 and k[1]>0}
    # C: normalized-name collision
    nm=collections.defaultdict(list)
    for i,r in enumerate(rows): nm[norm(r['name'])].append(i)
    ndup={k:v for k,v in nm.items() if len(v)>=2}
    if not (pdup or cdup or ndup): return None
    return dict(path=os.path.basename(path),k=len(rows),
                pmid_dups=pdup, ctrl_dups={f"{k[0]}/{k[1]}":[rows[i]['name'] for i in v] for k,v in cdup.items()},
                name_dups={k:[rows[i]['name'] for i in v] for k,v in ndup.items()})

files=[f for f in glob.glob("*REVIEW.html") if os.path.getsize(f)>100_000]
hits=[]
for f in sorted(files):
    try:
        r=audit(f)
        if r: hits.append(r)
    except Exception as e:
        print("ERR",f,e)
print(f"Scanned {len(files)} apps (>100KB). Flagged {len(hits)}.\n")
for h in hits:
    print(f"== {h['path']}  (k={h['k']})")
    if h['pmid_dups']: print("   PMID repeat:",h['pmid_dups'])
    if h['ctrl_dups']: print("   SHARED CONTROL:",h['ctrl_dups'])
    if h['name_dups']: print("   NAME collision:",h['name_dups'])
json.dump(hits,open("findings/multiarm_audit.json","w"),indent=1)
print(f"\nWrote findings/multiarm_audit.json")
