"""Pre-declared 8-axis specification multiverse + results payload for the app.

The axes were fixed in STAGE0_PREFLIGHT.md before any model was fitted; nothing
here is chosen after seeing an estimate. Every cell reports the focal contrast
TQ 300 mg vs PQ 14 d low dose (3.5 mg/kg) -- the only edge with more than one
trial's direct evidence -- plus the node set that survives the cell.

Writes ../outputs/vivax_nma_results.json, consumed by the app.
"""
import json, sys, io, os
import numpy as np
from scipy import stats
import nma_fit as M

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
Z = stats.norm.ppf(0.975)
HERE = os.path.dirname(os.path.abspath(__file__))

net = json.load(open(os.path.join(HERE, 'preflight', 'network.json'), encoding='utf-8'))
ALL_NODES = [n['id'] for n in net['nodes']]
TRIALS = net['trials']
NODE_LABEL = {n['id']: n['label'] for n in net['nodes']}
FOCAL = ('TQ_300', 'PQ_14d_low_3.5')

# trial-level attributes used by the axes (all recorded at Stage 0/1a)
ATTR = {
    'DETECTIVE_PART1': dict(partner='chloroquine', blind=True, supervised=True,
                            g6pd='screened', region='mixed'),
    'DETECTIVE_PART2': dict(partner='chloroquine', blind=True, supervised=True,
                            g6pd='screened', region='mixed'),
    'GATHER':          dict(partner='chloroquine', blind=True, supervised=True,
                            g6pd='screened_plus_moderate_female', region='mixed'),
    'INSPECTOR':       dict(partner='DHA-piperaquine', blind=True, supervised=True,
                            g6pd='screened', region='tropical'),
    'EFFORT':          dict(partner='mixed', blind=False, supervised=False,
                            g6pd='screened', region='tropical'),
}
SINGLE_EDGE = ['TQ_50', 'TQ_100', 'TQ_600', 'PQ_7d_high_7']


def subset(trial_filter=None, node_filter=None):
    nodes = [n for n in ALL_NODES if node_filter is None or node_filter(n)]
    out = []
    for t in TRIALS:
        if trial_filter and not trial_filter(t):
            continue
        arms = [a for a in t['arms'] if a['node'] in nodes]
        if len(arms) >= 2:
            out.append({**t, 'arms': arms})
    present = {a['node'] for t in out for a in t['arms']}
    return out, [n for n in nodes if n in present]


def cell(name, axis, level, trial_filter=None, node_filter=None, rule='observed',
         note=''):
    trials, nodes = subset(trial_filter, node_filter)
    rec = dict(cell=name, axis=axis, level=level, note=note, rule=rule,
               n_trials=len(trials), nodes=nodes,
               N=sum(sum(a['n'] for a in t['arms']) for t in trials),
               trial_ids=[t['id'] for t in trials])
    if not trials or not all(f in nodes for f in FOCAL):
        rec.update(estimable=False,
                   reason='focal contrast not in this cell' if trials else 'no trials')
        return rec
    # focal contrast must remain connected within this cell
    f = M.fit(trials, nodes, rule)
    e, se = M.contrast(f, *FOCAL)
    rec.update(estimable=True, tau2=round(f['tau2'], 4), I2=round(f['I2'], 1),
               tau2_estimable=f['tau2_estimable'],
               Q=round(f['Q'], 3), df=f['df'],
               OR=round(float(np.exp(e)), 3),
               lo=round(float(np.exp(e - Z * se)), 3),
               hi=round(float(np.exp(e + Z * se)), 3))
    return rec


CELLS = []
# --- P1 horizon --------------------------------------------------------------
CELLS.append(cell('P1a', 'P1 follow-up horizon', '180 d only (PRIMARY)',
                  note='the pre-declared primary cell'))
CELLS.append(cell('P1b', 'P1 follow-up horizon', 'nearby horizons admitted',
                  note='NCT03610399 (168 d) and NCT04706130 (3 mo) have no 180-d row; '
                       'they cannot be added without changing the estimand, so this '
                       'cell is declared NOT ESTIMABLE rather than approximated'))
CELLS[-1].update(estimable=False, reason='off-horizon trials lack a 180-day count')
# --- P2 relapse periodicity --------------------------------------------------
CELLS.append(cell('P2a', 'P2 relapse periodicity', 'tropical-only sites',
                  trial_filter=lambda t: ATTR[t['id']]['region'] == 'tropical'))
CELLS.append(cell('P2b', 'P2 relapse periodicity', 'all regions pooled'))
# --- P3 partner drug ---------------------------------------------------------
CELLS.append(cell('P3a', 'P3 partner blood-stage drug', 'chloroquine partner only',
                  trial_filter=lambda t: ATTR[t['id']]['partner'] == 'chloroquine'))
CELLS.append(cell('P3b', 'P3 partner blood-stage drug', 'DHA-piperaquine partner only',
                  trial_filter=lambda t: ATTR[t['id']]['partner'] == 'DHA-piperaquine'))
CELLS.append(cell('P3c', 'P3 partner blood-stage drug', 'any partner pooled'))
# --- P4 G6PD -----------------------------------------------------------------
CELLS.append(cell('P4a', 'P4 G6PD eligibility', 'strictly screened only',
                  trial_filter=lambda t: ATTR[t['id']]['g6pd'] == 'screened'))
CELLS.append(cell('P4b', 'P4 G6PD eligibility', 'incl. moderate-deficient females'))
# --- P5 node scheme ----------------------------------------------------------
CELLS.append(cell('P5a', 'P5 node scheme', 'total mg/kg (PRIMARY)',
                  note='PQ 7 d @1.0 and PQ 14 d @0.5 would merge at 7 mg/kg -- but no '
                       '14 d high-dose arm exists at 180 d, so the merge is untested'))
CELLS.append(cell('P5b', 'P5 node scheme', 'daily dose x duration kept distinct',
                  note='identical to P5a in this evidence base: the only 7 mg/kg node '
                       'present is the 7-day regimen'))
# --- P6 supervision ----------------------------------------------------------
CELLS.append(cell('P6a', 'P6 administration', 'supervised (efficacy) only',
                  trial_filter=lambda t: ATTR[t['id']]['supervised']))
CELLS.append(cell('P6b', 'P6 administration', 'unsupervised (effectiveness) only',
                  trial_filter=lambda t: not ATTR[t['id']]['supervised']))
# --- P7 single-edge nodes ----------------------------------------------------
CELLS.append(cell('P7a', 'P7 single-edge nodes', 'retained (full 7-node network)'))
CELLS.append(cell('P7b', 'P7 single-edge nodes', 'dropped -> 3-node robust core',
                  node_filter=lambda n: n not in SINGLE_EDGE))
# --- P8 censoring rule -------------------------------------------------------
CELLS.append(cell('P8a', 'P8 censoring rule', 'observed recurrence (PRIMARY)',
                  rule='observed'))
CELLS.append(cell('P8b', 'P8 censoring rule', 'missing = failure',
                  rule='missing_failure'))
CELLS.append(cell('P8c', 'P8 censoring rule', 'censored = success',
                  rule='censored_success'))
# --- risk of bias (EFFORT is the only open-label trial) ----------------------
CELLS.append(cell('RoB', 'risk of bias', 'double-blind trials only',
                  trial_filter=lambda t: ATTR[t['id']]['blind'],
                  note='drops EFFORT, the only open-label trial'))

# ---------------------------------------------------------------------------
full = M.fit(TRIALS, ALL_NODES, 'observed')
core_trials, core_nodes = subset(node_filter=lambda n: n not in SINGLE_EDGE)
core = M.fit(core_trials, core_nodes, 'observed')


def node_table(f, nodes):
    rows = []
    for n in nodes:
        if n == M.REF:
            rows.append(dict(node=n, label=NODE_LABEL[n], OR=1.0, lo=None, hi=None,
                             reference=True))
            continue
        e, se = M.contrast(f, n, M.REF)
        rows.append(dict(node=n, label=NODE_LABEL[n],
                         OR=round(float(np.exp(e)), 3),
                         lo=round(float(np.exp(e - Z * se)), 3),
                         hi=round(float(np.exp(e + Z * se)), 3), reference=False))
    return rows


direct = []
for t in TRIALS:
    nd = {a['node'] for a in t['arms']}
    if set(FOCAL) <= nd:
        a = next(x for x in t['arms'] if x['node'] == FOCAL[0])
        b = next(x for x in t['arms'] if x['node'] == FOCAL[1])
        ea, na = M.arm_counts(a, 'observed')
        eb, nb = M.arm_counts(b, 'observed')
        orr = (ea / (na - ea)) / (eb / (nb - eb))
        direct.append(dict(trial=t['id'], partner=ATTR[t['id']]['partner'],
                           blind=ATTR[t['id']]['blind'],
                           tq_events=ea, tq_n=na, pq_events=eb, pq_n=nb,
                           OR=round(float(orr), 4)))

payload = dict(
    generated='2026-07-30',
    estimand='P. vivax recurrence by 180 days (recurrence, NOT relapse)',
    measure='odds ratio of recurrence; OR < 1 favours the listed node',
    reference=M.REF,
    full=dict(n_trials=len(TRIALS), N=sum(t['n'] for t in TRIALS),
              nodes=node_table(full, ALL_NODES),
              tau2=round(full['tau2'], 4), I2=round(full['I2'], 1),
              Q=round(full['Q'], 3), df=full['df'], pQ=round(full['pQ'], 4)),
    core=dict(n_trials=len(core_trials),
              N=sum(sum(a['n'] for a in t['arms']) for t in core_trials),
              nodes=node_table(core, core_nodes),
              tau2=round(core['tau2'], 4), I2=round(core['I2'], 1),
              Q=round(core['Q'], 3), df=core['df'], pQ=round(core['pQ'], 4)),
    focal=dict(contrast='TQ 300 mg vs PQ 14 d low dose (3.5 mg/kg)',
               per_trial=direct),
    multiverse=CELLS,
    q_decomposition=dict(total=17.041286, total_df=6, total_p=0.009133,
                         within_design=4.995111, within_df=2, within_p=0.082286,
                         between_design=12.046175, between_df=4, between_p=0.017011,
                         source='R netmeta decomp.design()'),
    validation=dict(tool='R netmeta', max_abs_diff_fixed_effect=4.83e-08,
                    tolerance=1e-6, passed=True),
)

os.makedirs(os.path.join(HERE, '..', 'outputs'), exist_ok=True)
p = os.path.join(HERE, '..', 'outputs', 'vivax_nma_results.json')
json.dump(payload, open(p, 'w', encoding='utf-8'), indent=2)

print(f'{"cell":6s} {"axis":30s} {"level":38s} {"k":>2s} {"OR":>7s} {"95% CI":>18s} {"I2":>6s}')
for c in CELLS:
    if c.get('estimable'):
        print(f'{c["cell"]:6s} {c["axis"][:30]:30s} {c["level"][:38]:38s} '
              f'{c["n_trials"]:2d} {c["OR"]:7.3f} [{c["lo"]:7.3f},{c["hi"]:7.3f}] '
              f'{c["I2"]:5.1f}%'
              + ('' if c['tau2_estimable'] else '  <tau2 not estimable>'))
    else:
        print(f'{c["cell"]:6s} {c["axis"][:30]:30s} {c["level"][:38]:38s} '
              f'{c.get("n_trials",0):2d}  NOT ESTIMABLE -- {c["reason"]}')
print(f'\nwrote {os.path.normpath(p)}')
