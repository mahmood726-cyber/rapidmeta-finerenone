import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

worklist = json.load(open('F:/rapidmeta-finerenone/outputs/reclass_continuous_worklist.json'))

def is_meanish(pt):
    if not pt: return False
    p = pt.upper()
    return 'MEAN' in p  # MEAN, LEAST_SQUARES_MEAN, LS Mean, GEOMETRIC MEAN

target = sys.argv[1] if len(sys.argv) > 1 else None

for w in worklist:
    nct = w['nct']
    if target and nct != target:
        continue
    d = json.load(open(f'F:/rapidmeta-finerenone/outputs/ctgov_cache/{nct}.json'))
    try:
        oms = d['resultsSection']['outcomeMeasuresModule']['outcomeMeasures']
    except KeyError:
        print(f'### {nct} {w["drug"]} ({w["condition"]}): NO RESULTS SECTION')
        continue
    print(f'### {nct}  {w["drug"]}  ({w["condition"]})  -- {len(oms)} outcomes')
    for i, om in enumerate(oms):
        typ = om.get('type','')
        pt = om.get('paramType','')
        if typ not in ('PRIMARY','SECONDARY'):
            continue
        meanish = is_meanish(pt)
        has_an = bool(om.get('analyses'))
        # only show primary + meanish, or anything with a mean-diff analysis
        an_md = False
        if has_an:
            for a in om['analyses']:
                if 'MEAN' in (a.get('paramType','') or '').upper() and 'DIFF' in (a.get('paramType','') or '').upper():
                    an_md = True
        if not meanish and not an_md:
            continue
        print(f'  [{i}] {typ} pt={pt} disp={om.get("dispersionType")} unit={om.get("unitOfMeasure")}')
        print(f'      title: {om.get("title","")[:110]}')
        groups = om.get('groups', [])
        print(f'      groups: ' + ' | '.join(f'{g["id"]}={g.get("title","")[:35]}' for g in groups))
        # denom counts
        denoms = om.get('denoms', [])
        nmap = {}
        for dn in denoms:
            for c in dn.get('counts', []):
                nmap[c['groupId']] = c.get('value')
        # per-arm measurements (first class/category)
        classes = om.get('classes', [])
        if classes:
            for ci, cl in enumerate(classes):
                cats = cl.get('categories', [])
                clab = cl.get('title','')
                for cat in cats:
                    catlab = cat.get('title','')
                    ms = cat.get('measurements', [])
                    mtxt = ' | '.join(f'{m["groupId"]}:v={m.get("value")},sp={m.get("spread")},n={nmap.get(m["groupId"])}' for m in ms)
                    lab = (clab+'/'+catlab).strip('/')
                    print(f'      meas[{ci}] {lab[:30]}: {mtxt}')
        if has_an:
            for a in om['analyses']:
                print(f'      ANALYSIS pt={a.get("paramType")} val={a.get("paramValue")} ci=[{a.get("ciLowerLimit")},{a.get("ciUpperLimit")}] p={a.get("pValue")} disp={a.get("dispersionType")}={a.get("dispersionValue")} grp={a.get("groupIds")}')
    print()
