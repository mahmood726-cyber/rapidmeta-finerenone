#!/usr/bin/env python
"""Enrich Class-2 (same-PMID) audit: dump each repeated-PMID row group with names+2x2."""
import re,io,os,glob,json,sys,collections
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8",errors="replace")

def extract(src):
    rows=[]
    for c in src.split('{name:"')[1:]:
        name=c.split('"',1)[0]; win=c[:1100]
        def g(k):
            m=re.search(k+r':(-?\.?\d+(?:\.\d+)?)',win); return m.group(1) if m else None
        pm=re.search(r'pmid:"([^"]*)"',win)
        grp=re.search(r'group:"([^"]{0,60})',win)
        if g('tE') and g('cN') and not re.search(r'included:\s*false',win[:200]):
            rows.append(dict(name=name,pmid=(pm.group(1) if pm else ""),
                grp=(grp.group(1) if grp else ""),
                tE=g('tE'),tN=g('tN'),cE=g('cE'),cN=g('cN')))
    return rows

out={}
allpmids=set()
for f in sorted(glob.glob("*REVIEW.html")):
    if os.path.getsize(f)<100_000: continue
    rows=extract(io.open(f,encoding="utf-8",errors="replace").read())
    pm=collections.Counter(r['pmid'] for r in rows if r['pmid'])
    dups={k:v for k,v in pm.items() if v>=2}
    if not dups: continue
    grp={}
    for k in dups:
        grp[k]=[r for r in rows if r['pmid']==k]
        allpmids.add(k)
    out[f]={'k':len(rows),'is_nma':'_NMA_' in f,'dups':grp}
json.dump(out,open("findings/pmid_groups.json","w"),indent=1)
print(f"apps with PMID repeats: {len(out)}  | unique repeated PMIDs: {len(allpmids)}")
json.dump(sorted(allpmids),open("findings/pmid_list.json","w"))
# preview a few non-NMA
shown=0
for f,d in out.items():
    if d['is_nma']: continue
    print(f"\n== {f} (k={d['k']})")
    for pmid,rows in d['dups'].items():
        print(f"   PMID {pmid}:")
        for r in rows:
            print(f"      {r['name'][:26]:26s} {r['grp'][:34]:34s} t={r['tE']}/{r['tN']} c={r['cE']}/{r['cN']}")
    shown+=1
    if shown>=6: break
