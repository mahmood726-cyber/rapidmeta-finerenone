#!/usr/bin/env python
"""Audit: apps whose default selectedOutcome is NOT an outcome any trial actually has
(clone bug -> 0 included studies -> blank extraction/forest). Propose the correct primary."""
import re,io,os,glob,json,sys,collections
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8",errors="replace")

def analyze(path):
    s=io.open(path,encoding="utf-8",errors="replace").read()
    m=re.search(r'selectedOutcome:"([^"]+)"',s)
    if not m: return None
    default=m.group(1)
    # gather (shortLabel,type) across all trial chunks
    pri=collections.Counter(); allc=collections.Counter()
    labels=set()
    for c in s.split('{name:"')[1:]:
        win=c[:1600]
        for sl,ty in re.findall(r'shortLabel:"([^"]+)"[^}]*?type:"([^"]+)"',win):
            labels.add(sl); allc[sl]+=1
            if ty.upper()=="PRIMARY": pri[sl]+=1
    if not labels:  # no outcome metadata -> different render path; skip
        return None
    ok = default in labels
    # proposed = most common PRIMARY label, else most common label
    proposed=None
    if pri: proposed=pri.most_common(1)[0][0]
    elif allc: proposed=allc.most_common(1)[0][0]
    return dict(path=os.path.basename(path),default=default,ok=ok,proposed=proposed,
                n_with_proposed=allc.get(proposed,0),n_primary=sum(pri.values()),labels=sorted(labels)[:6])

files=[f for f in glob.glob("*REVIEW.html") if os.path.getsize(f)>100_000]
broken=[];okc=0;skip=0
for f in sorted(files):
    r=analyze(f)
    if r is None: skip+=1; continue
    if r["ok"]: okc+=1
    else: broken.append(r)
print(f"scanned {len(files)} | ok {okc} | broken {len(broken)} | skipped(no-outcome-meta) {skip}\n")
bydefault=collections.Counter(b["default"] for b in broken)
print("broken default values:",dict(bydefault),"\n")
for b in broken[:60]:
    print(f"  {b['path'][:46]:46s} default={b['default']:14s} -> {b['proposed']} (on {b['n_with_proposed']} trials)")
json.dump(broken,open("findings/default_outcome_broken.json","w"),indent=1)
print(f"\n... {len(broken)} total. Written findings/default_outcome_broken.json")
