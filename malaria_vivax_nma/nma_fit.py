"""Arm-based binary network meta-analysis for P. vivax radical cure.

Outcome: P. vivax RECURRENCE by 180 days (event = recurrence; lower is better).
Effect measure: log odds ratio, reference node = no hypnozoiticidal therapy.

Model: contrast-based random-effects NMA (Lu & Ades / netmeta parameterisation).
Each trial contributes contrasts against its own baseline arm; the within-trial
covariance of those contrasts is
    Var(y_k)      = v_base + v_k
    Cov(y_j, y_k) = v_base                     (shared baseline arm)
and the random-effects structure adds
    Var  += tau^2 ,  Cov += tau^2 / 2          (shared baseline, per Higgins & Whitehead)

tau^2 is estimated by REML.  DerSimonian-Laird is deliberately NOT used: with
5 trials it is materially downward-biased (house rule: REML or Paule-Mandel for k<10).

Validated against R netmeta 1e-6 by validate_netmeta.R.
"""
import json, sys, io, itertools
from collections import OrderedDict
import numpy as np
from scipy.optimize import minimize_scalar
from scipy import stats

if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

REF = 'no_hypnozoiticidal'
CC = 0.5  # continuity correction, applied ONLY when a trial has a zero cell


# --------------------------------------------------------------------------
# event / denominator conventions -- preset P8
# --------------------------------------------------------------------------
def arm_counts(arm, rule):
    """Return (events, n) for a recurrence outcome under the chosen P8 rule."""
    rec = arm['recurrence']
    free = arm['recurrence_free']
    cens = arm.get('censored', 0) or 0
    if rule == 'observed':          # P8a: evaluable only, censored excluded
        return rec, rec + free
    if rule == 'missing_failure':   # P8b: censored counted as recurrences
        if arm.get('recurrence_missing_eq_failure') is not None:
            return arm['recurrence_missing_eq_failure'], arm['n']
        return rec + cens, arm['n']
    if rule == 'censored_success':  # P8c: censored counted as non-recurrences
        return rec, arm['n']
    raise ValueError(f'unknown P8 rule {rule!r}')


def build_contrasts(trials, rule):
    """Per trial: log-ORs vs that trial's first arm, plus within-trial covariance."""
    rows = []
    for t in trials:
        arms = t['arms']
        if len(arms) < 2:
            continue
        ec = [arm_counts(a, rule) for a in arms]
        zero = any(e == 0 or e == n for e, n in ec)
        adj = CC if zero else 0.0
        logit, var = [], []
        for (e, n) in ec:
            a_, b_ = e + adj, n - e + adj
            logit.append(np.log(a_ / b_))
            var.append(1.0 / a_ + 1.0 / b_)
        base = 0
        idx = [i for i in range(len(arms)) if i != base]
        y = np.array([logit[i] - logit[base] for i in idx])
        S = np.full((len(idx), len(idx)), var[base])
        for r, i in enumerate(idx):
            S[r, r] = var[base] + var[i]
        rows.append({
            'trial': t['id'],
            'base_node': arms[base]['node'],
            'nodes': [arms[i]['node'] for i in idx],
            'y': y, 'S': S, 'zero_corrected': zero,
            'counts': {arms[i]['node']: ec[i] for i in range(len(arms))},
        })
    return rows


def design(rows, nodes):
    """Design matrix mapping basic parameters (node vs REF) to observed contrasts."""
    pos = {n: i for i, n in enumerate(n_ for n_ in nodes if n_ != REF)}
    X = []
    for r in rows:
        for nd in r['nodes']:
            row = np.zeros(len(pos))
            if nd != REF:
                row[pos[nd]] += 1.0
            if r['base_node'] != REF:
                row[pos[r['base_node']]] -= 1.0
            X.append(row)
    return np.vstack(X), pos


def _blocks(rows, tau2):
    out = []
    for r in rows:
        m = r['S'].shape[0]
        T = np.full((m, m), tau2 / 2.0)
        np.fill_diagonal(T, tau2)
        out.append(r['S'] + T)
    return out


def gls(rows, nodes, tau2):
    X, pos = design(rows, nodes)
    y = np.concatenate([r['y'] for r in rows])
    Vs = _blocks(rows, tau2)
    XtWX = np.zeros((X.shape[1], X.shape[1]))
    XtWy = np.zeros(X.shape[1])
    k = 0
    for V, r in zip(Vs, rows):
        m = V.shape[0]
        Xi = X[k:k + m]; yi = y[k:k + m]; k += m
        Wi = np.linalg.inv(V)
        XtWX += Xi.T @ Wi @ Xi
        XtWy += Xi.T @ Wi @ yi
    cov = np.linalg.pinv(XtWX)
    return cov @ XtWy, cov, pos


def _neg_reml(tau2, rows, nodes):
    if tau2 < 0:
        return 1e12
    X, _ = design(rows, nodes)
    y = np.concatenate([r['y'] for r in rows])
    Vs = _blocks(rows, tau2)
    ll = 0.0
    XtWX = np.zeros((X.shape[1], X.shape[1]))
    k = 0
    for V, r in zip(Vs, rows):
        m = V.shape[0]
        Xi = X[k:k + m]; k += m
        sign, ld = np.linalg.slogdet(V)
        ll += -0.5 * ld
        XtWX += Xi.T @ np.linalg.inv(V) @ Xi
    beta, cov, _ = gls(rows, nodes, tau2)
    k = 0
    for V, r in zip(Vs, rows):
        m = V.shape[0]
        Xi = X[k:k + m]; yi = y[k:k + m]; k += m
        res = yi - Xi @ beta
        ll += -0.5 * res @ np.linalg.inv(V) @ res
    s, ld2 = np.linalg.slogdet(XtWX)
    ll += -0.5 * ld2
    return -ll


def fit(trials, nodes, rule='observed'):
    rows = build_contrasts(trials, rule)
    opt = minimize_scalar(_neg_reml, bounds=(0.0, 4.0), args=(rows, nodes),
                          method='bounded', options={'xatol': 1e-10})
    tau2 = max(0.0, float(opt.x))
    if _neg_reml(0.0, rows, nodes) <= _neg_reml(tau2, rows, nodes):
        tau2 = 0.0
    beta, cov, pos = gls(rows, nodes, tau2)
    # Q for heterogeneity/inconsistency, from the fixed-effect fit
    b0, _, _ = gls(rows, nodes, 0.0)
    X, _ = design(rows, nodes)
    y = np.concatenate([r['y'] for r in rows])
    Q, k = 0.0, 0
    for r in rows:
        m = r['S'].shape[0]
        Xi = X[k:k + m]; yi = y[k:k + m]; k += m
        res = yi - Xi @ b0
        Q += float(res @ np.linalg.inv(r['S']) @ res)
    dfQ = max(0, len(y) - (len(nodes) - 1))
    return {'tau2': tau2, 'tau': tau2 ** 0.5, 'beta': beta, 'cov': cov, 'pos': pos,
            'rows': rows, 'Q': Q, 'df': dfQ,
            'pQ': float(1 - stats.chi2.cdf(Q, dfQ)) if dfQ > 0 else None,
            'I2': max(0.0, (Q - dfQ) / Q * 100) if Q > 0 and dfQ > 0 else 0.0,
            'n_contrasts': len(y), 'rule': rule}


def contrast(f, a, b):
    """log-OR of node a vs node b, with SE, from the fitted basic parameters."""
    pos, beta, cov = f['pos'], f['beta'], f['cov']
    v = np.zeros(len(pos))
    if a != REF: v[pos[a]] += 1
    if b != REF: v[pos[b]] -= 1
    est = float(v @ beta)
    se = float(np.sqrt(v @ cov @ v))
    return est, se


def report(f, nodes, label, out):
    z = stats.norm.ppf(0.975)
    out.append(f'\n### {label}')
    out.append(f'  rule={f["rule"]}  contrasts={f["n_contrasts"]}  '
               f'tau2={f["tau2"]:.4f} (tau={f["tau"]:.3f})  '
               f'Q={f["Q"]:.2f} df={f["df"]} p={f["pQ"]:.3f} I2={f["I2"]:.1f}%'
               if f['pQ'] is not None else
               f'  rule={f["rule"]}  tau2={f["tau2"]:.4f}')
    out.append(f'  {"node":24s} {"OR vs no-therapy":>18s}  {"95% CI":>20s}')
    for n in nodes:
        if n == REF: continue
        e, se = contrast(f, n, REF)
        out.append(f'  {n:24s} {np.exp(e):18.3f}  '
                   f'[{np.exp(e - z * se):7.3f}, {np.exp(e + z * se):7.3f}]')
    return out


def main():
    net = json.load(open(sys.argv[1] if len(sys.argv) > 1 else
                         'preflight/network.json', encoding='utf-8'))
    nodes = [n['id'] for n in net['nodes']]
    trials = net['trials']
    out = ['P. vivax radical cure -- arm-based binary NMA',
           'outcome: RECURRENCE by 180 days (event = recurrence; OR < 1 favours the node)',
           f'reference node: {REF}']

    full = fit(trials, nodes, 'observed')
    report(full, nodes, f'FULL NETWORK -- 7 nodes, {len(trials)} trials, '
                        f'N={sum(t["n"] for t in trials)}', out)

    core_nodes = [REF, 'PQ_14d_low_3.5', 'TQ_300']
    core_trials = []
    for t in trials:
        arms = [a for a in t['arms'] if a['node'] in core_nodes]
        if len(arms) >= 2:
            core_trials.append({**t, 'arms': arms})
    core = fit(core_trials, core_nodes, 'observed')
    report(core, core_nodes, f'ROBUST CORE -- 3 nodes, {len(core_trials)} trials, '
                             f'N={sum(sum(a["n"] for a in t["arms"]) for t in core_trials)}', out)

    out.append('\n### FULL vs CORE on the shared contrasts')
    out.append(f'  {"contrast":34s} {"full OR":>10s} {"core OR":>10s} {"ratio":>8s}')
    for a, b in [('TQ_300', REF), ('PQ_14d_low_3.5', REF), ('TQ_300', 'PQ_14d_low_3.5')]:
        ef, _ = contrast(full, a, b)
        ec, _ = contrast(core, a, b)
        out.append(f'  {a + " vs " + b:34s} {np.exp(ef):10.3f} {np.exp(ec):10.3f} '
                   f'{np.exp(ef - ec):8.3f}')

    out.append('\n### P8 sensitivity (censoring rule) -- full network')
    for rule in ['observed', 'missing_failure', 'censored_success']:
        fr = fit(trials, nodes, rule)
        e, se = contrast(fr, 'TQ_300', 'PQ_14d_low_3.5')
        z = stats.norm.ppf(0.975)
        out.append(f'  {rule:18s} tau2={fr["tau2"]:.4f}  TQ300 vs PQ3.5 OR='
                   f'{np.exp(e):.3f} [{np.exp(e - z * se):.3f}, {np.exp(e + z * se):.3f}]')

    txt = '\n'.join(out)
    print(txt)
    return full, core, nodes, trials


if __name__ == '__main__':
    main()
