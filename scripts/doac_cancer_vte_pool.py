"""Recompute the DOAC-vs-LMWH cancer-associated-VTE pooled estimates from source-verified data.

Every input figure is sourced in outputs/doac_cancer_vte_correction_ledger.json.
Cross-validated against R metafor by scripts/doac_cancer_vte_pool.R.

Run:  python scripts/doac_cancer_vte_pool.py
"""
import io
import json
import math
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

Z = 1.959963984540054


def t_quantile(p, df):
    """Two-sided upper t quantile via bisection on the regularized incomplete beta CDF."""
    lo, hi = 0.0, 200.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if student_t_cdf(mid, df) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def betacf(a, b, x):
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < 3e-16:
            break
    return h


def betainc(a, b, x):
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(lbeta + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * betacf(a, b, x) / a
    return 1.0 - math.exp(lbeta + b * math.log(1.0 - x) + a * math.log(x)) * betacf(b, a, 1.0 - x) / b


def student_t_cdf(t, df):
    x = df / (df + t * t)
    p = 0.5 * betainc(df / 2.0, 0.5, x)
    return 1.0 - p if t > 0 else p


def chi2_sf(q, df):
    """Upper tail of the chi-square distribution via the regularized upper incomplete gamma."""
    if q <= 0:
        return 1.0
    a = df / 2.0
    x = q / 2.0
    if x < a + 1.0:
        # series
        term = 1.0 / a
        total = term
        n = a
        for _ in range(1000):
            n += 1.0
            term *= x / n
            total += term
            if abs(term) < abs(total) * 1e-16:
                break
        return 1.0 - total * math.exp(-x + a * math.log(x) - math.lgamma(a))
    # continued fraction
    tiny = 1e-300
    b = x + 1.0 - a
    c = 1.0 / tiny
    d = 1.0 / b
    h = d
    for i in range(1, 1000):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < 1e-16:
            break
    return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h


def from_ci(eff, lo, hi):
    """log effect and its standard error from a published point estimate and 95% CI."""
    return math.log(eff), (math.log(hi) - math.log(lo)) / (2.0 * Z)


def pool(rows, label):
    y = [r['y'] for r in rows]
    se = [r['se'] for r in rows]
    v = [s * s for s in se]
    k = len(rows)
    w = [1.0 / vi for vi in v]
    sw = sum(w)
    fe = sum(wi * yi for wi, yi in zip(w, y)) / sw
    fe_se = math.sqrt(1.0 / sw)

    q = sum(wi * (yi - fe) ** 2 for wi, yi in zip(w, y))
    df = k - 1
    q_p = chi2_sf(q, df)
    i2 = max(0.0, (q - df) / q) * 100.0 if q > 0 else 0.0

    c = sw - sum(wi * wi for wi in w) / sw
    tau2 = max(0.0, (q - df) / c)

    ws = [1.0 / (vi + tau2) for vi in v]
    sws = sum(ws)
    re = sum(wi * yi for wi, yi in zip(ws, y)) / sws
    re_se = math.sqrt(1.0 / sws)

    # Hartung-Knapp-Sidik-Jonkman, with the ad-hoc floor at 1 (never narrower than DL)
    q_hk = sum(wi * (yi - re) ** 2 for wi, yi in zip(ws, y)) / df
    q_hk_floored = max(1.0, q_hk)
    hk_se = math.sqrt(q_hk_floored / sws)
    tcrit = t_quantile(0.975, df)

    # prediction interval, t_{k-1} per Cochrane Handbook v6.5
    pi_se = math.sqrt(tau2 + re_se * re_se)

    out = {
        'label': label,
        'k': k,
        'studies': [r['id'] for r in rows],
        'fe': {'est': math.exp(fe), 'lci': math.exp(fe - Z * fe_se), 'uci': math.exp(fe + Z * fe_se)},
        'tau2': tau2,
        'Q': q,
        'Q_df': df,
        'Q_p': q_p,
        'I2': i2,
        'dl': {
            'logEffect': re, 'se': re_se, 'est': math.exp(re),
            'lci': math.exp(re - Z * re_se), 'uci': math.exp(re + Z * re_se),
            'p': 2 * (1 - student_t_cdf(abs(re / re_se) * 1e6, 1e6)) if False else None,
        },
        'hksj': {
            'q_hk_raw': q_hk, 'q_hk_used': q_hk_floored, 'se': hk_se, 't_crit': tcrit,
            'lci': math.exp(re - tcrit * hk_se), 'uci': math.exp(re + tcrit * hk_se),
            'p': 2 * (1 - student_t_cdf(abs(re / hk_se), df)),
        },
        'pi': {'lci': math.exp(re - tcrit * pi_se), 'uci': math.exp(re + tcrit * pi_se)},
        'weights_pct': [100.0 * wi / sws for wi in ws],
    }
    # two-sided normal p for the DL estimate
    zst = re / re_se
    out['dl']['p'] = math.erfc(abs(zst) / math.sqrt(2.0))
    return out


# --- source-verified inputs -------------------------------------------------
# Recurrent VTE, relative time-to-event effect as published / as posted on the registry.
HR_ROWS_PRIMARY = [
    dict(id='HOKUSAI VTE-Cancer', eff=0.71, lo=0.476, hi=1.059,
         src='ClinicalTrials.gov NCT02073682 posted results, secondary outcome '
             '"Recurrent VTE During the Overall Study Period", Cox PH; NEJM 2018;378:615-624'),
    dict(id='SELECT-D', eff=0.43, lo=0.19, hi=0.99,
         src='J Clin Oncol 2018;36:2017-2023 (ISRCTN86712308)'),
    dict(id='ADAM VTE', eff=0.099, lo=0.013, hi=0.780,
         src='J Thromb Haemost 2020;18:411-421 (NCT02585713)'),
    dict(id='CARAVAGGIO', eff=0.63, lo=0.37, hi=1.07,
         src='NEJM 2020;382:1599-1607; ClinicalTrials.gov NCT03045406 posted results'),
]

CASTA_DIVA = dict(id='CASTA-DIVA', eff=0.75, lo=0.21, hi=2.66,
                  src='Chest 2021;161:781-790 (NCT02746185); SUBDISTRIBUTION hazard ratio, '
                      'composite outcome also counts worsening of pulmonary vascular or venous obstruction')


def prep(rows):
    out = []
    for r in rows:
        y, se = from_ci(r['eff'], r['lo'], r['hi'])
        out.append(dict(id=r['id'], y=y, se=se, **{k: r[k] for k in ('eff', 'lo', 'hi', 'src')}))
    return out


def main():
    primary = pool(prep(HR_ROWS_PRIMARY), 'Recurrent VTE - primary (cause-specific/Cox HR, k=4)')
    sens = pool(prep(HR_ROWS_PRIMARY + [CASTA_DIVA]),
                'Recurrent VTE - sensitivity adding CASTA-DIVA subdistribution HR (k=5)')

    res = {'primary': primary, 'sensitivity_with_casta_diva': sens,
           'inputs': {'primary': HR_ROWS_PRIMARY, 'casta_diva': CASTA_DIVA}}

    for r in (primary, sens):
        print('=' * 78)
        print(r['label'])
        print('  k = %d   studies: %s' % (r['k'], ', '.join(r['studies'])))
        print('  FE      HR %.4f (%.4f - %.4f)' % (r['fe']['est'], r['fe']['lci'], r['fe']['uci']))
        print('  DL RE   HR %.4f (%.4f - %.4f)   p = %.4f' %
              (r['dl']['est'], r['dl']['lci'], r['dl']['uci'], r['dl']['p']))
        print('  HKSJ    HR %.4f (%.4f - %.4f)   p = %.4f   (q_hk = %.4f, t_%d = %.4f)' %
              (r['dl']['est'], r['hksj']['lci'], r['hksj']['uci'], r['hksj']['p'],
               r['hksj']['q_hk_raw'], r['Q_df'], r['hksj']['t_crit']))
        print('  PI      %.4f - %.4f' % (r['pi']['lci'], r['pi']['uci']))
        print('  tau2 = %.6f   Q = %.4f (df %d, p = %.4f)   I2 = %.1f%%' %
              (r['tau2'], r['Q'], r['Q_df'], r['Q_p'], r['I2']))
        print('  weights: ' + ', '.join('%s %.1f%%' % (s, w)
                                        for s, w in zip(r['studies'], r['weights_pct'])))

    here = os.path.dirname(os.path.abspath(__file__))
    dest = os.path.join(here, '..', 'outputs', 'doac_cancer_vte_pooled.json')
    with open(dest, 'w', encoding='utf-8') as fh:
        json.dump(res, fh, indent=2)
    print('\nwrote', os.path.normpath(dest))


if __name__ == '__main__':
    main()
