"""PI gap check — for each topic with k>=3 trials, re-pool the trials' raw 2x2
counts using DerSimonian-Laird random-effects (with HKSJ floor) and compute
both the pooled CI and the prediction interval. Flag the topic if pooled CI
excludes the null but PI includes the null — the headline conclusion is then
fragile to between-trial heterogeneity (a single new trial could overturn it).

Adapted from Mahmood's MetaAudit `pi_gap` detector. Threshold: PI gap = FAIL
if (pooled CI excludes null) AND (PI contains null) AND (k>=3).

Per advanced-stats.md, this implementation:
  - Uses log-RR pooling (back-transform after) for binary outcomes
  - Cochrane Handbook v6.5 PI: t_{k-1} convention
  - HKSJ floor: max(1, Q/(k-1))
  - Skips trials with zero events on both sides (no log-RR estimate)

Output: outputs/pi_gap_check.csv with one row per topic (REVIEW HTML file).
"""
from __future__ import annotations
import sys, io, csv, re, math
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO_DIR = Path(__file__).resolve().parent.parent
OUT_CSV = REPO_DIR / "outputs" / "pi_gap_check.csv"

TRIAL_RE = re.compile(
    r"'(NCT\d+(?:_[A-Za-z0-9]+)?|LEGACY-[A-Za-z0-9-]+)'\s*:\s*\{[^}]*?"
    r"name:\s*'([^']+?)'[^}]*?"
    r"tE:\s*([\d.eE+\-]+|null|None|NaN)\s*,\s*"
    r"tN:\s*([\d.eE+\-]+|null|None|NaN)\s*,\s*"
    r"cE:\s*([\d.eE+\-]+|null|None|NaN)\s*,\s*"
    r"cN:\s*([\d.eE+\-]+|null|None|NaN)",
    re.DOTALL,
)


def parse_num(s):
    if s is None:
        return None
    s = s.strip()
    if s.lower() in ("null", "none", "nan"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def t_inv(p, df):
    """Approximate inverse t-CDF via Hill 1970. Used only for k<=30."""
    if df < 1:
        return float("nan")
    if df > 30:
        # z-approximation safe
        return 1.96 if abs(p - 0.025) < 0.01 else 2.576 if abs(p - 0.005) < 0.01 else 1.96
    table = {
        1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
        6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
        11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131,
        16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086,
        21: 2.080, 22: 2.074, 23: 2.069, 24: 2.064, 25: 2.060,
        26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045, 30: 2.042,
    }
    return table.get(int(df), 1.96)


def dl_pool_logrr(trials):
    """DerSimonian-Laird random-effects pooling on log-RR scale.
    Returns (mu_logRR, se_mu, tau2, k_used, Q, pi_lower_RR, pi_upper_RR,
             ci_lower_RR, ci_upper_RR).
    Skips trials with zero events on BOTH sides (uninformative).
    Uses Haldane 0.5 correction when one side is zero.
    """
    valid = []
    for t in trials:
        tE, tN, cE, cN = t
        if None in (tE, tN, cE, cN):
            continue
        if tN <= 0 or cN <= 0:
            continue
        # Skip if both arms zero events (no signal)
        if tE == 0 and cE == 0:
            continue
        # Haldane correction
        if tE == 0 or cE == 0:
            tE_a, cE_a = tE + 0.5, cE + 0.5
            tN_a, cN_a = tN + 0.5, cN + 0.5
        else:
            tE_a, cE_a = tE, cE
            tN_a, cN_a = tN, cN
        try:
            log_rr = math.log((tE_a / tN_a) / (cE_a / cN_a))
        except (ValueError, ZeroDivisionError):
            continue
        # Variance of log-RR (Greenland-Robins)
        try:
            var = 1.0 / tE_a - 1.0 / tN_a + 1.0 / cE_a - 1.0 / cN_a
        except ZeroDivisionError:
            continue
        if var <= 0 or not math.isfinite(var):
            continue
        valid.append((log_rr, var))

    k = len(valid)
    if k < 2:
        return None

    # Fixed-effect mean for Q
    weights_fe = [1.0 / v for _, v in valid]
    sum_w = sum(weights_fe)
    mu_fe = sum(w * lr for (lr, _), w in zip(valid, weights_fe)) / sum_w
    Q = sum(w * (lr - mu_fe) ** 2 for (lr, _), w in zip(valid, weights_fe))
    df = k - 1

    # DL tau^2
    if Q > df:
        c = sum_w - sum(w * w for w in weights_fe) / sum_w
        tau2 = max(0.0, (Q - df) / c)
    else:
        tau2 = 0.0

    # RE weights
    weights_re = [1.0 / (v + tau2) for _, v in valid]
    sum_w_re = sum(weights_re)
    mu_re = sum(w * lr for (lr, _), w in zip(valid, weights_re)) / sum_w_re
    se_mu = math.sqrt(1.0 / sum_w_re)

    # HKSJ floor: scale variance up
    hksj_factor = max(1.0, Q / df) if df > 0 else 1.0
    se_mu_hksj = se_mu * math.sqrt(hksj_factor)

    # 95% CI (use t_{k-1} for HKSJ)
    t_crit = t_inv(0.025, df)
    ci_lower = mu_re - t_crit * se_mu_hksj
    ci_upper = mu_re + t_crit * se_mu_hksj

    # 95% PI (Cochrane Handbook v6.5: t_{k-1} × sqrt(tau^2 + se_mu^2))
    if k >= 3:
        pi_t_crit = t_inv(0.025, df)
        pi_se = math.sqrt(tau2 + se_mu ** 2)
        pi_lower = mu_re - pi_t_crit * pi_se
        pi_upper = mu_re + pi_t_crit * pi_se
    else:
        pi_lower = float("nan")
        pi_upper = float("nan")

    return {
        "k_used": k,
        "mu_logRR": mu_re,
        "tau2": tau2,
        "Q": Q,
        "ci_lower_RR": math.exp(ci_lower),
        "ci_upper_RR": math.exp(ci_upper),
        "pi_lower_RR": math.exp(pi_lower) if not math.isnan(pi_lower) else float("nan"),
        "pi_upper_RR": math.exp(pi_upper) if not math.isnan(pi_upper) else float("nan"),
    }


def main():
    review_files = sorted(REPO_DIR.glob("*_REVIEW.html"))
    print(f"Scanning {len(review_files)} review HTMLs ...")

    findings = []
    for hp in review_files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        trials = []
        for m in TRIAL_RE.finditer(text):
            tE = parse_num(m.group(3))
            tN = parse_num(m.group(4))
            cE = parse_num(m.group(5))
            cN = parse_num(m.group(6))
            trials.append((tE, tN, cE, cN))

        if len(trials) < 3:
            continue

        result = dl_pool_logrr(trials)
        if not result:
            continue

        k = result["k_used"]
        ci_l = result["ci_lower_RR"]
        ci_u = result["ci_upper_RR"]
        pi_l = result["pi_lower_RR"]
        pi_u = result["pi_upper_RR"]

        ci_excludes_null = (ci_u < 1.0) or (ci_l > 1.0)
        pi_includes_null = False
        if not math.isnan(pi_l) and not math.isnan(pi_u):
            pi_includes_null = (pi_l <= 1.0 <= pi_u)

        verdict = "OK"
        if ci_excludes_null and pi_includes_null and k >= 3:
            verdict = "PI_GAP_FAIL"
        elif ci_excludes_null and pi_includes_null:
            verdict = "PI_GAP_LOWPOWER"

        findings.append({
            "file": hp.name,
            "k_used": k,
            "tau2": f"{result['tau2']:.4f}",
            "pooled_RR": f"{math.exp(result['mu_logRR']):.3f}",
            "ci_lower": f"{ci_l:.3f}",
            "ci_upper": f"{ci_u:.3f}",
            "pi_lower": f"{pi_l:.3f}" if not math.isnan(pi_l) else "",
            "pi_upper": f"{pi_u:.3f}" if not math.isnan(pi_u) else "",
            "ci_excludes_null": ci_excludes_null,
            "pi_includes_null": pi_includes_null,
            "verdict": verdict,
        })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        if findings:
            w = csv.DictWriter(f, fieldnames=list(findings[0].keys()))
            w.writeheader()
            w.writerows(findings)

    by_v: dict[str, int] = {}
    for r in findings:
        by_v[r["verdict"]] = by_v.get(r["verdict"], 0) + 1
    print(f"\n=== PI gap results ===")
    print(f"  Topics analysed (k>=3): {len(findings)}")
    for k_, v in sorted(by_v.items()):
        print(f"  {k_:25s} {v}")

    print(f"\n=== Topics with PI_GAP_FAIL (CI sig, PI not) ===")
    for r in findings:
        if r["verdict"] == "PI_GAP_FAIL":
            print(f"  {r['file'][:48]:48s} k={r['k_used']:2d} pooled_RR={r['pooled_RR']:6s} CI=[{r['ci_lower']},{r['ci_upper']}] PI=[{r['pi_lower']},{r['pi_upper']}]")

    print(f"\nWritten: {OUT_CSV}")


if __name__ == "__main__":
    main()
