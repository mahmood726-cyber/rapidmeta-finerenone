import json, io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
nct = sys.argv[1]
d = json.load(open(nct + '.json', encoding='utf-8'))
rs = d.get('resultsSection')
if not rs:
    print(nct, 'NO RESULTS SECTION'); sys.exit()
pf = rs.get('participantFlowModule', {})
print('=== PARTICIPANT FLOW GROUPS')
for g in pf.get('groups', []):
    print(' ', g['id'], '|', g['title'], '|', (g.get('description') or '')[:150])
for per in pf.get('periods', []):
    print('  PERIOD:', per.get('title'))
    for m in per.get('milestones', []):
        print('    ', m.get('type'), {a['groupId']: a.get('numSubjects') for a in m.get('achievements', [])})
om = rs.get('outcomeMeasuresModule', {}).get('outcomeMeasures', [])
print('=== OUTCOME MEASURES (%d)' % len(om))
want = re.compile(r'recurren|relapse|efficac', re.I)
for i, o in enumerate(om):
    ttl = o.get('title', '')
    if not want.search(ttl): continue
    print(f'--- [{i}] {o.get("type")}: {ttl}')
    print('    timeFrame:', o.get('timeFrame'))
    print('    desc:', (o.get('description') or '')[:220])
    print('    popDesc:', (o.get('populationDescription') or '')[:160])
    print('    unit:', o.get('unitOfMeasure'), '| paramType:', o.get('paramType'))
    gmap = {g['id']: g['title'] for g in o.get('groups', [])}
    for cls in o.get('classes', []):
        if cls.get('title'): print('    CLASS:', cls.get('title'))
        for cat in cls.get('categories', []):
            if cat.get('title'): print('      CAT:', cat.get('title'))
            for m in cat.get('measurements', []):
                print('       ', gmap.get(m['groupId'], m['groupId']), '=', m.get('value'),
                      (('[' + str(m.get('lowerLimit')) + ',' + str(m.get('upperLimit')) + ']')
                       if m.get('lowerLimit') else ''))
    for g in o.get('groups', []):
        print('    GROUP', g['id'], g['title'], '| N=', (g.get('description') or '')[:80])
    for dn in o.get('denoms', []):
        print('    DENOM', dn.get('units'), {c['groupId']: c['value'] for c in dn.get('counts', [])})
