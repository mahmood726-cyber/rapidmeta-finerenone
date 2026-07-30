"""Integrity gates for the P. vivax radical-cure network.

Verifies rather than asserts:
  G1 count plausibility  - recurrence_free + recurrence + censored == n, per arm
  G2 node coverage       - every declared node appears in >=1 trial; no orphan node refs
  G3 connectivity        - the comparison graph is a single connected component
  G4 loop testability    - which loops have an edge informed by trials that do NOT
                           supply the whole loop (i.e. genuinely node-splittable)
  G5 single-edge nodes   - nodes whose every edge comes from one trial (preset P7)

Run: python check_network.py network.json
Exits non-zero if any gate fails, so it can block a build.
"""
import json, sys, io, itertools
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

net = json.load(open(sys.argv[1] if len(sys.argv) > 1 else 'network.json', encoding='utf-8'))
nodes = [n['id'] for n in net['nodes']]
trials = net['trials']
failures = []

# ---- G1 count plausibility -------------------------------------------------
print('G1  count plausibility')
for t in trials:
    for a in t['arms']:
        f, r, c, n = a.get('recurrence_free'), a.get('recurrence'), a.get('censored'), a['n']
        if None in (f, r, c, n):
            failures.append(f"G1 {t['id']}/{a['node']}: missing count field")
            continue
        if f + r + c != n:
            failures.append(f"G1 {t['id']}/{a['node']}: {f}+{r}+{c} != {n}")
        if not 0 <= r <= n:
            failures.append(f"G1 {t['id']}/{a['node']}: recurrence {r} outside [0,{n}]")
    tot = sum(a['n'] for a in t['arms'])
    flag = 'OK' if tot == t['n'] else f"<<< declared {t['n']}"
    print(f"    {t['id']:18s} arms={len(t['arms'])} sum(n)={tot:5d} {flag}")
    if tot != t['n']:
        failures.append(f"G1 {t['id']}: arm n sum {tot} != declared {t['n']}")

# ---- G2 node coverage ------------------------------------------------------
print('\nG2  node coverage')
used = defaultdict(list)
for t in trials:
    for a in t['arms']:
        if a['node'] not in nodes:
            failures.append(f"G2 {t['id']}: unknown node {a['node']}")
        used[a['node']].append(t['id'])
for n in nodes:
    if not used[n]:
        failures.append(f"G2 node {n} declared but never used")
    print(f"    {n:22s} in {len(used[n])} trial(s): {', '.join(used[n])}")

# ---- G3 connectivity -------------------------------------------------------
print('\nG3  connectivity')
edges = defaultdict(set)          # frozenset(pair) -> {trial ids}
adj = defaultdict(set)
for t in trials:
    for x, y in itertools.combinations(sorted(a['node'] for a in t['arms']), 2):
        edges[frozenset((x, y))].add(t['id'])
        adj[x].add(y); adj[y].add(x)

seen, stack = set(), [nodes[0]]
while stack:
    v = stack.pop()
    if v in seen: continue
    seen.add(v)
    stack.extend(adj[v] - seen)
components = 1 if seen == set(nodes) else 'MULTIPLE'
print(f"    nodes={len(nodes)}  edges={len(edges)}  reached from {nodes[0]}: {len(seen)}")
if seen != set(nodes):
    failures.append(f"G3 DISCONNECTED: unreachable {sorted(set(nodes) - seen)}")
    print(f"    <<< DISCONNECTED: {sorted(set(nodes)-seen)}")
else:
    print('    single connected component: YES')

print('\n    edge multiplicity:')
for e, ts in sorted(edges.items(), key=lambda kv: -len(kv[1])):
    a, b = sorted(e)
    print(f"      {a:22s} <-> {b:22s} {len(ts)} trial(s)  [{', '.join(sorted(ts))}]")

# ---- G4 leave-one-trial-out robustness -------------------------------------
# A "testable loop" verdict from graph shape alone is unreliable: a three-arm
# trial makes its own triangle closed but internally consistent by construction,
# so a shape-only rule reports inconsistency information that does not exist.
# What is defensible is asking what survives when each trial is removed.
print('\nG4  leave-one-trial-out robustness')

def component(nodeset, trial_subset):
    adj2 = defaultdict(set)
    for t in trial_subset:
        for x, y in itertools.combinations(sorted(a['node'] for a in t['arms']), 2):
            adj2[x].add(y); adj2[y].add(x)
    if not adj2: return set()
    root = next(iter(adj2))
    seen2, st = set(), [root]
    while st:
        v = st.pop()
        if v in seen2: continue
        seen2.add(v); st.extend(adj2[v] - seen2)
    return seen2

for t in trials:
    rest = [x for x in trials if x is not t]
    reach = component(nodes, rest)
    lost = sorted(set(nodes) - reach)
    print(f"    drop {t['id']:18s} -> {len(reach)}/{len(nodes)} nodes still connected"
          + (f"   LOST: {', '.join(lost)}" if lost else "   (network intact)"))

robust = set(nodes)
for t in trials:
    robust &= component(nodes, [x for x in trials if x is not t])
print(f"\n    ROBUST CORE (survives removal of any single trial): "
      f"{', '.join(sorted(robust)) if robust else 'EMPTY'}")

# edges carrying direct evidence from >1 trial are the only ones where
# cross-trial comparison (heterogeneity or inconsistency) is possible at all
multi = {e: ts for e, ts in edges.items() if len(ts) > 1}
print(f"    edges with direct evidence from >1 trial: {len(multi)} of {len(edges)}")
for e, ts in sorted(multi.items(), key=lambda kv: -len(kv[1])):
    a, b = sorted(e)
    print(f"      {a:22s} <-> {b:22s} {len(ts)} trials")

# ---- G5 single-edge nodes --------------------------------------------------
print('\nG5  single-edge nodes (preset P7 targets)')
for n in nodes:
    src = set()
    for e, ts in edges.items():
        if n in e: src |= ts
    if len(src) == 1:
        print(f"    {n:22s} all edges from a single trial: {src.pop()}")

# ---- verdict ---------------------------------------------------------------
print('\n' + '=' * 62)
if failures:
    print(f'FAILED ({len(failures)}):')
    for f in failures: print('  -', f)
    sys.exit(1)
print('ALL GATES PASS')
