"""Deterministic DerSimonian-Laird random-effects pooling — pure stdlib.

Closed-form (no iteration), so it reproduces bit-for-bit across machines. This is
the clean-room anchor: given the per-trial (y=log-effect, v=variance) the review
exported, this recomputes the pooled log-effect and must match to 1e-12.

No model. No network. No third-party packages.
"""
import math


def dl_pool(trials):
    """trials: list of {'y': logeffect, 'v': variance}. Returns the DL RE pool."""
    ys = [t['y'] for t in trials]
    vs = [t['v'] for t in trials]
    k = len(ys)
    if k == 0:
        raise ValueError('no trials')
    # fixed-effect weights
    wf = [1.0 / v for v in vs]
    sw = sum(wf)
    mu_fe = sum(w * y for w, y in zip(wf, ys)) / sw
    Q = sum(w * (y - mu_fe) ** 2 for w, y in zip(wf, ys))
    df = k - 1
    # DL tau^2
    if k > 1:
        c = sw - sum(w * w for w in wf) / sw
        tau2 = max(0.0, (Q - df) / c) if c > 0 else 0.0
    else:
        tau2 = 0.0
    # random-effects pool
    wr = [1.0 / (v + tau2) for v in vs]
    swr = sum(wr)
    mu = sum(w * y for w, y in zip(wr, ys)) / swr
    se = math.sqrt(1.0 / swr)
    z = 1.959963984540054  # 97.5th percentile of N(0,1)
    lci, uci = mu - z * se, mu + z * se
    i2 = max(0.0, (Q - df) / Q) * 100.0 if Q > 0 else 0.0
    return {
        'k': k, 'logEffect': mu, 'se': se, 'lci': lci, 'uci': uci,
        'tau2': tau2, 'Q': Q, 'I2': i2, 'estimator': 'DL',
    }


def back_transform(mu, lci, uci, measure):
    """Ratio measures live on the log scale; MD/SMD are already natural."""
    if measure in ('OR', 'RR', 'HR', 'IRR'):
        return math.exp(mu), math.exp(lci), math.exp(uci)
    return mu, lci, uci
