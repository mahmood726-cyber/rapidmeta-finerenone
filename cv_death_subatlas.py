#!/usr/bin/env python
"""
CV-Death Sub-Atlas — k>=3 pooled per drug class.

Pools cardiovascular death HRs from ctgov_mining_results.json (combining
analyses-supplied and Peto-derived sources) per drug class. Only classes
with k>=3 trials reporting CV death are included.

Methodology (per advanced-stats.md):
  - Paule-Mandel tau2 (NOT DL — DL is biased for k<10)
  - HKSJ standard error with Q/(k-1) floor
  - t-distribution CI: t_{k-1}
  - Log scale pooling, back-transform after
  - 95% prediction interval: t_{k-2} formula (k>=3)

Output:
  cv_death_subatlas.json
  cv_death_subatlas.md  (human-readable report)
"""
import sys, io, os, json, math
from collections import defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

MIN_K_PER_CLASS = 3


# ────────────────────────────────────────────────────────────
# Statistics
# ────────────────────────────────────────────────────────────

def log_se_from_ci(est, lo, hi):
    """Convert HR + 95% CI to (logHR, SE) on log scale."""
    return math.log(est), (math.log(hi) - math.log(lo)) / (2 * 1.96)


def paule_mandel_tau2(estimates, max_iter=200, tol=1e-8):
    """Paule-Mandel iterative tau2.

    Solves sum(w_i(tau2) * (y_i - mean)^2) = k - 1
    where w_i(tau2) = 1 / (v_i + tau2). Bisection over [0, 10].
    """
    k = len(estimates)
    if k < 2:
        return 0.0
    ys = [y for y, _ in estimates]
    vs = [se ** 2 for _, se in estimates]

    def Q_at(tau2):
        ws = [1.0 / (v + tau2) for v in vs]
        sw = sum(ws)
        mean = sum(w * y for w, y in zip(ws, ys)) / sw
        return sum(w * (y - mean) ** 2 for w, y in zip(ws, ys))

    # Q at tau2=0
    q0 = Q_at(0.0)
    if q0 <= k - 1:
        return 0.0
    # Bisection on [0, hi]
    lo, hi = 0.0, 10.0
    while Q_at(hi) > k - 1 and hi < 1e6:
        hi *= 2
    for _ in range(max_iter):
        mid = (lo + hi) / 2
        q = Q_at(mid)
        if abs(q - (k - 1)) < tol:
            return mid
        if q > k - 1:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# Approximation of t-distribution quantile (Student's t inverse CDF)
def qt(p, df):
    """Approximate t-distribution quantile using Hill's approximation.
    Sufficient accuracy for meta-analytic CIs (df 2-30, p 0.025/0.975).
    """
    if df <= 0:
        return float('nan')
    # Use Cornish-Fisher expansion for moderate df
    # For df>=2 and p in [0.001, 0.999] this is accurate to ~3 decimals
    # which is plenty for forest-plot CIs
    z = qnorm(p)
    g1 = (z ** 3 + z) / 4
    g2 = (5 * z ** 5 + 16 * z ** 3 + 3 * z) / 96
    g3 = (3 * z ** 7 + 19 * z ** 5 + 17 * z ** 3 - 15 * z) / 384
    g4 = (79 * z ** 9 + 776 * z ** 7 + 1482 * z ** 5 - 1920 * z ** 3 - 945 * z) / 92160
    return z + g1 / df + g2 / df ** 2 + g3 / df ** 3 + g4 / df ** 4


def qnorm(p):
    """Inverse normal CDF (Beasley-Springer-Moro)."""
    a = [-3.969683028665376e1, 2.209460984245205e2, -2.759285104469687e2,
         1.383577518672690e2, -3.066479806614716e1, 2.506628277459239e0]
    b = [-5.447609879822406e1, 1.615858368580409e2, -1.556989798598866e2,
         6.680131188771972e1, -1.328068155288572e1]
    c = [-7.784894002430293e-3, -3.223964580411365e-1, -2.400758277161838,
         -2.549732539343734, 4.374664141464968, 2.938163982698783]
    d = [7.784695709041462e-3, 3.224671290700398e-1, 2.445134137142996,
         3.754408661907416]
    p_low = 0.02425
    p_high = 1 - p_low
    if p < p_low:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p <= p_high:
        q = p - 0.5
        r = q * q
        return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
               (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
    q = math.sqrt(-2 * math.log(1 - p))
    return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)


def pm_hksj_pool(estimates):
    """Paule-Mandel tau2 + HKSJ SE with floor + t-distribution CI.

    Returns dict with k, tau2, I2, Q, pooled_est/lci/uci, pi_lo/pi_hi (k>=3).
    """
    k = len(estimates)
    if k == 0:
        return None
    if k == 1:
        y, se = estimates[0]
        return {
            'k': 1,
            'pooled_est': math.exp(y), 'pooled_lci': math.exp(y - 1.96 * se),
            'pooled_uci': math.exp(y + 1.96 * se),
            'tau2': 0.0, 'I2': 0.0, 'Q': 0.0, 'df': 0,
            'pi_lo': None, 'pi_hi': None,
            'method': 'single-study (no pooling)',
        }

    ys = [y for y, _ in estimates]
    vs = [se ** 2 for _, se in estimates]

    tau2 = paule_mandel_tau2(estimates)

    # FE-weighted Q for I2 (Higgins-Thompson — must use fixed-effect weights)
    fe_weights = [1.0 / v for v in vs]
    sum_fw = sum(fe_weights)
    fe_mean = sum(w * y for w, y in zip(fe_weights, ys)) / sum_fw
    Q_fe = sum(w * (y - fe_mean) ** 2 for w, y in zip(fe_weights, ys))
    df = k - 1
    I2 = max(0.0, (Q_fe - df) / Q_fe * 100) if Q_fe > 0 else 0.0

    # RE-weighted pooled estimate (PM tau2 weights)
    weights = [1.0 / (v + tau2) for v in vs]
    sum_w = sum(weights)
    pooled = sum(w * y for w, y in zip(weights, ys)) / sum_w

    # Q on RE weights — drives HKSJ scaling
    Q_re = sum(w * (y - pooled) ** 2 for w, y in zip(weights, ys))

    # HKSJ SE: sqrt(q / sum_w) with Q/(k-1) floor (advanced-stats.md rule)
    raw_q_over_df = Q_re / df
    q_floor = max(1.0, raw_q_over_df)
    floor_applied = raw_q_over_df < 1.0
    hksj_se = math.sqrt(q_floor / sum_w)

    # t-distribution CI: t_{k-1}
    t_crit = qt(0.975, df)

    pooled_lci = math.exp(pooled - t_crit * hksj_se)
    pooled_uci = math.exp(pooled + t_crit * hksj_se)

    # Prediction interval (Higgins 2009): t_{k-2}, undefined for k<3
    pi_lo = pi_hi = None
    if k >= 3:
        t_pi = qt(0.975, k - 2)
        pi_se = math.sqrt(tau2 + hksj_se ** 2)
        pi_lo = math.exp(pooled - t_pi * pi_se)
        pi_hi = math.exp(pooled + t_pi * pi_se)

    return {
        'k': k,
        'pooled_est': math.exp(pooled),
        'pooled_lci': pooled_lci,
        'pooled_uci': pooled_uci,
        'tau2': tau2,
        'I2': I2,
        'Q_fe': Q_fe,
        'Q_re': Q_re,
        'df': df,
        'q_floor_applied': floor_applied,
        'hksj_se': hksj_se,
        't_crit': t_crit,
        'pi_lo': pi_lo,
        'pi_hi': pi_hi,
        'method': 'PM tau2 + HKSJ SE (Q/(k-1) floor) + t_{k-1} CI',
    }


# ────────────────────────────────────────────────────────────
# Build sub-atlas
# ────────────────────────────────────────────────────────────

def build_subatlas():
    if not os.path.exists('ctgov_mining_results.json'):
        sys.exit('ERROR: ctgov_mining_results.json missing — run ctgov_deep_mining.py first')
    if not os.path.exists('cardiology_mortality_atlas.json'):
        sys.exit('ERROR: cardiology_mortality_atlas.json missing — run cardiology_mortality_atlas.py --json')

    with open('ctgov_mining_results.json', 'r', encoding='utf-8') as f:
        mined = json.load(f)
    with open('cardiology_mortality_atlas.json', 'r', encoding='utf-8') as f:
        atlas = json.load(f)

    # Build NCT -> drug_class
    nct_to_class = {}
    nct_to_trial_name = {}
    for cls in atlas['classes']:
        for t in cls.get('trials', []):
            nct = t.get('nct') or t.get('id')
            if nct:
                nct_to_class[nct] = cls['drug_class']
                nct_to_trial_name[nct] = t.get('name', nct)

    # Collect CV-death estimates per class
    by_class = defaultdict(list)  # class -> list of dicts
    unmapped_cvd = []  # NCTs with CV death but no atlas class

    for nct, info in mined.items():
        cvd = info.get('outcomes', {}).get('CV_death')
        if not cvd:
            continue
        cls = nct_to_class.get(nct)
        record = {
            'nct': nct,
            'name': nct_to_trial_name.get(nct, info.get('title', '')[:40]),
            'hr': cvd['est'], 'lci': cvd['lci'], 'uci': cvd['uci'],
            'source': cvd.get('source', 'analyses'),
            'outcome_title': cvd.get('outcome_title', '')[:60],
        }
        if cls:
            by_class[cls].append(record)
        else:
            unmapped_cvd.append(record)

    # Build per-class pools (k>=3 only)
    pools = []
    excluded = []
    for cls, trials in sorted(by_class.items()):
        k = len(trials)
        if k < MIN_K_PER_CLASS:
            excluded.append({'class': cls, 'k': k, 'trials': trials})
            continue
        estimates = []
        for t in trials:
            try:
                y, se = log_se_from_ci(t['hr'], t['lci'], t['uci'])
                if math.isfinite(y) and math.isfinite(se) and se > 0:
                    estimates.append((y, se))
            except (ValueError, ZeroDivisionError):
                continue
        if len(estimates) < MIN_K_PER_CLASS:
            excluded.append({'class': cls, 'k': len(estimates), 'reason': 'invalid CIs', 'trials': trials})
            continue
        pool = pm_hksj_pool(estimates)
        pools.append({
            'drug_class': cls,
            'pool': pool,
            'trials': trials,
        })

    return {
        'method': 'Paule-Mandel tau2 + HKSJ SE (Q/(k-1) floor) + t_{k-1} CI',
        'min_k_per_class': MIN_K_PER_CLASS,
        'pools': pools,
        'excluded_classes': excluded,
        'unmapped_trials': unmapped_cvd,
    }


def write_report(subatlas):
    out = subatlas
    lines = []
    lines.append('# CV-Death Sub-Atlas\n')
    lines.append(f'**Method:** {out["method"]}\n')
    lines.append(f'**Inclusion:** drug classes with k>={out["min_k_per_class"]} trials reporting CV death\n')
    lines.append(f'**Pools generated:** {len(out["pools"])}\n')
    lines.append(f'**Excluded (k<3):** {len(out["excluded_classes"])} classes\n')
    lines.append(f'**Unmapped CV-death trials:** {len(out["unmapped_trials"])}\n')
    lines.append('\n## Pooled estimates\n')
    if not out['pools']:
        lines.append('_No drug class met k>=3 inclusion threshold._\n')
    for p in out['pools']:
        cls = p['drug_class']
        pool = p['pool']
        lines.append(f'\n### {cls}  (k={pool["k"]})\n')
        lines.append(f'- **Pooled HR:** {pool["pooled_est"]:.3f} (95% CI {pool["pooled_lci"]:.3f}-{pool["pooled_uci"]:.3f})\n')
        lines.append(f'- **tau²:** {pool["tau2"]:.4f} | **I²:** {pool["I2"]:.1f}% | **Q (FE):** {pool["Q_fe"]:.2f} on {pool["df"]} df\n')
        if pool.get('q_floor_applied'):
            lines.append(f'- _HKSJ Q/(k-1) floor applied (Q < df, prevents narrow-CI artifact)_\n')
        if pool.get('pi_lo'):
            lines.append(f'- **95% prediction interval:** {pool["pi_lo"]:.3f}-{pool["pi_hi"]:.3f}\n')
        lines.append('\n| NCT | Trial | HR | 95% CI | Source |\n')
        lines.append('|---|---|---|---|---|\n')
        for t in p['trials']:
            lines.append(f'| {t["nct"]} | {t["name"][:30]} | {t["hr"]:.3f} | {t["lci"]:.2f}-{t["uci"]:.2f} | {t["source"]} |\n')
    if out['excluded_classes']:
        lines.append('\n## Excluded (k<3)\n\n')
        for ex in out['excluded_classes']:
            lines.append(f'- **{ex["class"]}** — k={ex["k"]}\n')
    if out['unmapped_trials']:
        lines.append('\n## CV-death trials unmapped to atlas classes\n\n')
        for t in out['unmapped_trials']:
            lines.append(f'- {t["nct"]} ({t["name"][:35]}) — HR {t["hr"]:.3f} ({t["lci"]:.2f}-{t["uci"]:.2f}) [{t["source"]}]\n')
    return ''.join(lines)


if __name__ == '__main__':
    subatlas = build_subatlas()
    with open('cv_death_subatlas.json', 'w', encoding='utf-8') as f:
        json.dump(subatlas, f, indent=2, default=str)
    report = write_report(subatlas)
    with open('cv_death_subatlas.md', 'w', encoding='utf-8') as f:
        f.write(report)
    print(f'Wrote cv_death_subatlas.json + cv_death_subatlas.md')
    print(f'Pools generated: {len(subatlas["pools"])}')
    print(f'Excluded classes: {len(subatlas["excluded_classes"])}')
    print(f'Unmapped CV-death trials: {len(subatlas["unmapped_trials"])}')
