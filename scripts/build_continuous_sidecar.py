r"""Generate continuous-outcome R-validation sidecars.

Matches the schema of existing outputs/r_validation/continuous/*.json
(scale, pool, se, lci, uci, tau2, I2, Q, Qp, PI_lci, PI_uci ...).

Trial input: each NCT block must carry `publishedHR` + `hrLCI` + `hrUCI`
plus an `estimandType` of 'MD', 'HR', 'OR', 'RR', or 'RD'. The engine
populates these from AACT outcome_analyses + per-arm Mean+SD.

Pooling rules (advanced-stats.md):
  * For ratio scales (HR, OR, RR): pool on log scale, back-transform.
  * For difference scales (MD, RD): pool natively (no transform).
  * REML tau-squared (iterative).
  * HKSJ correction with floor at 1 (Wiksten 2016).
  * Prediction interval via t_(k-1) per Cochrane v6.5; undefined for k<3.

Re-uses the math from build_binary_sidecar (reml_tau2, t_quantile_975).

The sidecar is written to outputs/r_validation/continuous/<PAGE_STEM>.json
where PAGE_STEM is the page name minus .html (the engine's fetch path
for continuous sidecars per puppeteer-observed log).
"""
from __future__ import annotations
import sys, io, re, json, math
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SIDECAR_DIR = HERE / "outputs" / "r_validation" / "continuous"
SIDECAR_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_binary_sidecar import reml_tau2, t_quantile_975, normal_quantile, TRIAL_RE, get_num, get_str


RATIO_SCALES = {"HR", "OR", "RR"}
DIFF_SCALES = {"MD", "RD", "SMD"}


def _gammaincc(s, x):
    if x < 0 or s <= 0: return 1.0
    if x == 0: return 1.0
    from math import exp, lgamma, log
    if x < s + 1:
        ap = s
        summ = 1 / s
        term = summ
        for _ in range(200):
            ap += 1
            term *= x / ap
            summ += term
            if abs(term) < abs(summ) * 1e-12:
                break
        return 1 - summ * exp(-x + s * log(x) - lgamma(s))
    else:
        b = x + 1 - s
        c = 1e300
        d = 1.0 / b
        h = d
        for i in range(1, 200):
            an = -i * (i - s)
            b += 2
            d = an * d + b
            if abs(d) < 1e-30: d = 1e-30
            c = b + an / c
            if abs(c) < 1e-30: c = 1e-30
            d = 1.0 / d
            delt = d * c
            h *= delt
            if abs(delt - 1.0) < 1e-12:
                break
        return h * exp(-x + s * log(x) - lgamma(s))


def extract_continuous_trials(page_path: Path) -> tuple[list[dict], str | None]:
    """Return (trials, scale) for the first usable continuous outcome.

    A trial is "usable" if it has publishedHR (the effect), hrLCI, hrUCI
    all non-null. The scale is determined from the majority of trials'
    estimandType. If trials disagree on scale, we restrict to the
    majority scale (the rest are skipped).
    """
    txt = page_path.read_text(encoding="utf-8", errors="replace")
    candidates = []
    for m in TRIAL_RE.finditer(txt):
        nct = m.group(1) or m.group(2) or m.group(3)
        body = m.group("body")
        ph = get_num(body, "publishedHR")
        lo = get_num(body, "hrLCI")
        hi = get_num(body, "hrUCI")
        scale = get_str(body, "estimandType")
        if ph is None or lo is None or hi is None or scale is None:
            continue
        if scale not in RATIO_SCALES and scale not in DIFF_SCALES:
            continue
        candidates.append({
            "nct": nct,
            "name": get_str(body, "name") or nct,
            "pmid": get_str(body, "pmid"),
            "publishedHR": ph,
            "hrLCI": lo,
            "hrUCI": hi,
            "scale": scale,
        })
    if not candidates:
        return [], None

    # Pick the majority scale
    from collections import Counter
    scale_counter = Counter(t["scale"] for t in candidates)
    chosen_scale, _ = scale_counter.most_common(1)[0]
    trials = [t for t in candidates if t["scale"] == chosen_scale]

    # Compute yi/vi per trial
    z975 = 1.959964
    enriched = []
    for t in trials:
        ph, lo, hi = t["publishedHR"], t["hrLCI"], t["hrUCI"]
        if chosen_scale in RATIO_SCALES:
            # Log-transform; require all positive
            if ph <= 0 or lo <= 0 or hi <= 0:
                continue
            yi = math.log(ph)
            log_lo = math.log(lo)
            log_hi = math.log(hi)
            se = (log_hi - log_lo) / (2 * z975)
        else:
            yi = ph
            se = (hi - lo) / (2 * z975)
        if not math.isfinite(yi) or not math.isfinite(se) or se <= 0:
            continue
        vi = se * se
        enriched.append({**t, "yi": yi, "vi": vi})
    return enriched, chosen_scale


def pool_continuous(trials_xy, scale):
    """REML+HKSJ+floor pool of yi/vi pairs."""
    yis = [t["yi"] for t in trials_xy]
    vis = [t["vi"] for t in trials_xy]
    k = len(yis)
    if k < 2:
        return None
    tau2 = reml_tau2(yis, vis)
    ws = [1.0 / (v + tau2) for v in vis]
    sw = sum(ws)
    mu = sum(w * y for w, y in zip(ws, yis)) / sw
    var_mu_re = 1.0 / sw
    se_re = math.sqrt(var_mu_re)
    # Q at fixed-effect weights
    ws_fe = [1.0 / v for v in vis]
    mu_fe = sum(w * y for w, y in zip(ws_fe, yis)) / sum(ws_fe)
    Q = sum(w * (y - mu_fe)**2 for w, y in zip(ws_fe, yis))
    Qdf = k - 1
    Qp = _gammaincc(Qdf / 2.0, Q / 2.0) if Qdf > 0 else float('nan')
    I2 = max(0.0, (Q - Qdf) / Q) * 100 if Q > 0 else 0.0
    H2 = max(1.0, Q / Qdf) if Qdf > 0 else 1.0
    # HKSJ with floor at 1
    hksj_scale_raw = sum(w * (y - mu)**2 for w, y in zip(ws, yis)) / (k - 1)
    hksj_scale = max(1.0, hksj_scale_raw)
    se_hksj = math.sqrt(hksj_scale * var_mu_re)
    floor_applied = hksj_scale_raw < 1.0
    t_crit = t_quantile_975(k - 1)
    ci_lo_t = mu - t_crit * se_hksj
    ci_hi_t = mu + t_crit * se_hksj
    # PI via t_(k-1)
    pi_skip_reason = {}
    if k >= 3:
        pi_se = math.sqrt(tau2 + se_hksj**2)
        pi_lo_t = mu - t_crit * pi_se
        pi_hi_t = mu + t_crit * pi_se
    else:
        pi_lo_t = pi_hi_t = None
        pi_skip_reason = {"reason": "k<3"}

    # For ratio scales, back-transform pool + CI + PI
    if scale in RATIO_SCALES:
        pool_disp = math.exp(mu)
        lci_disp = math.exp(ci_lo_t)
        uci_disp = math.exp(ci_hi_t)
        pi_lci_disp = math.exp(pi_lo_t) if pi_lo_t is not None else None
        pi_uci_disp = math.exp(pi_hi_t) if pi_hi_t is not None else None
    else:
        pool_disp = mu
        lci_disp = ci_lo_t
        uci_disp = ci_hi_t
        pi_lci_disp = pi_lo_t
        pi_uci_disp = pi_hi_t

    # z and p (Wald)
    zval = mu / se_hksj if se_hksj > 0 else float('nan')
    # Two-sided p via 1 - Phi(|z|) * 2.
    # Use erfc approx for portability.
    pval = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(zval) / math.sqrt(2.0))))

    return {
        "scale": scale,
        "k": k,
        "fit_ok": True,
        "pool": round(pool_disp, 4),
        "se": round(se_hksj, 4),
        "lci": round(lci_disp, 4),
        "uci": round(uci_disp, 4),
        "zval": round(zval, 4),
        "pval": round(pval, 4),
        "tau2": round(tau2, 4),
        "tau": round(math.sqrt(tau2), 4),
        "I2": round(I2, 4),
        "H2": round(H2, 4),
        "Q": round(Q, 4),
        "Qp": float(f"{Qp:.4e}") if Qp == Qp else None,
        "PI_lci": round(pi_lci_disp, 4) if pi_lci_disp is not None else None,
        "PI_uci": round(pi_uci_disp, 4) if pi_uci_disp is not None else None,
        "PI_skip_reason": pi_skip_reason,
        "PI_convention": "t_{k-1} (Cochrane v6.5 §10.10.4.3)",
        "hksj_floor_applied": floor_applied,
    }


def emit_sidecar(page_path: Path, force=False) -> dict:
    stem = page_path.name.replace(".html", "")
    out_path = SIDECAR_DIR / f"{stem}.json"
    if out_path.exists() and not force:
        return {"status": "exists", "page": page_path.name}

    trials, scale = extract_continuous_trials(page_path)
    if not trials or len(trials) < 2:
        return {"status": "insufficient_k", "page": page_path.name, "k": len(trials)}

    pool = pool_continuous(trials, scale)
    if pool is None:
        return {"status": "pool_failed", "page": page_path.name}

    sidecar = {
        "review": stem,
        "engine": "python-rapidmeta-meta",
        "version": "1.0",
        **pool,
        "trials": [{
            "nct": t["nct"],
            "name": t["name"],
            "pmid": t["pmid"],
            "publishedHR": t["publishedHR"],
            "hrLCI": t["hrLCI"],
            "hrUCI": t["hrUCI"],
            "yi": round(t["yi"], 6),
            "vi": round(t["vi"], 6),
        } for t in trials],
        "generated_by": "scripts/build_continuous_sidecar.py",
        "generated_on": "2026-05-27",
    }
    out_path.write_text(json.dumps(sidecar, indent=2), encoding="utf-8")
    return {"status": "generated", "page": page_path.name, "k": pool["k"], "scale": scale,
            "pool": pool["pool"]}


def main():
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    targets = sorted(p for p in HERE.glob("*_REVIEW.html") if p.is_file())
    print(f"Candidate pages: {len(targets):,}")
    stats = {"generated": 0, "exists": 0, "insufficient_k": 0, "pool_failed": 0}
    for i, p in enumerate(targets, 1):
        r = emit_sidecar(p)
        stats[r["status"]] = stats.get(r["status"], 0) + 1
        if i % 200 == 0:
            print(f"  [{i}/{len(targets)}]  {stats}")
    print(f"\nDone. {stats}")
    print(f"Total continuous sidecars: {len(list(SIDECAR_DIR.glob('*.json'))):,}")


if __name__ == "__main__":
    main()
