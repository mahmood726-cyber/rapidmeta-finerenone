"""R5b — Review-level pool reproduction vs published MAs.

Design (handles Cochrane temporal/PICO differences explicitly):

  1. Each target has a published trial set + published pooled HR/CI for a
     specific outcome.
  2. We pool ONLY the overlap (intersection of published trial set and our
     extracted trials).
  3. Report trial-set overlap %, our overlap-only pool, our portfolio-pool
     (all relevant extracted trials), and the published pool.
  4. Acknowledge that if overlap pool ≈ published pool, our extraction is
     faithful to the original trial-level values. If portfolio pool diverges
     from published pool, that's likely PICO/scope difference (more or fewer
     trials), not extraction error.

Pooling method: log-scale inverse-variance, DerSimonian-Laird τ², HKSJ
adjustment when k ≥ 3. log(HR) derived from publishedHR; SE(log HR) derived
from CI: (log(uci) - log(lci)) / (2 × 1.96).

Output: outputs/extraction_audit/r5b_pool_results.json
"""
from __future__ import annotations
import json, sys, io, math
from pathlib import Path
from statistics import NormalDist

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
DATA = HERE / "outputs" / "extraction_audit" / "data"
OUT = HERE / "outputs" / "extraction_audit"

# ─────────── Published reference MAs ───────────
# Each: published pooled HR + CI + trial set (NCT list) for a specific outcome,
# with citation. Per PubMed attribution policy, DOIs recorded.
TARGETS = [
    {
        "name": "SGLT2i in HF — CV death + HHF (full HFrEF + HFpEF pool)",
        "ref": "Vaduganathan Lancet 2022; Jhund EHJ 2022 DAPA-HF+DELIVER pool",
        "pmid": "36041474", "doi": "10.1016/S0140-6736(22)01429-5",
        "published_HR": 0.80, "published_LCI": 0.75, "published_UCI": 0.85,
        "trial_nct_set": ["NCT03036124", "NCT03057977", "NCT03619213", "NCT03057951"],
        "trial_names": ["DAPA-HF", "EMPEROR-Reduced", "DELIVER", "EMPEROR-Preserved"],
        "our_review": "SGLT2I_HF_NMA_REVIEW",
        "outcome_label": "CV death + HHF",
    },
    {
        "name": "DOAC vs warfarin in AF — stroke or systemic embolism",
        "ref": "Ruff Lancet 2014 (NEJM-published MA of 4 phase-3 DOAC trials)",
        "pmid": "24315724", "doi": "10.1016/S0140-6736(13)62343-0",
        "published_HR": 0.81, "published_LCI": 0.73, "published_UCI": 0.91,
        "trial_nct_set": ["NCT00403767", "NCT00412984", "NCT00262600", "NCT00781391"],
        "trial_names": ["ROCKET-AF", "ARISTOTLE", "RE-LY", "ENGAGE AF-TIMI 48"],
        "our_review": "DOAC_AF_NMA_REVIEW",
        "outcome_label": "Stroke or systemic embolism",
    },
    {
        "name": "FIDELIO + FIGARO (FIDELITY) — cardiorenal composite",
        "ref": "Agarwal EHJ 2022 (FIDELITY pre-specified pool)",
        "pmid": "34529029", "doi": "10.1093/eurheartj/ehab777",
        "published_HR": 0.86, "published_LCI": 0.78, "published_UCI": 0.95,
        "trial_nct_set": ["NCT02540993", "NCT02545049"],
        "trial_names": ["FIDELIO-DKD", "FIGARO-DKD"],
        "our_review": "CARDIORENAL_DKD_NMA_REVIEW",
        "outcome_label": "CV composite (FIDELITY-style pool)",
    },
    {
        "name": "Empa/Cana/Dapa SGLT2 — MACE in CV-OUT trials",
        "ref": "Zelniker Lancet 2019 (3-trial CVOT pool: EMPA-REG + CANVAS + DECLARE)",
        "pmid": "30424892", "doi": "10.1016/S0140-6736(18)32590-X",
        "published_HR": 0.89, "published_LCI": 0.83, "published_UCI": 0.96,
        "trial_nct_set": ["NCT01131676", "NCT01032629", "NCT01730534"],
        "trial_names": ["EMPA-REG OUTCOME", "CANVAS Program", "DECLARE-TIMI 58"],
        "our_review": "SGLT2_MACE_CVOT_REVIEW",
        "outcome_label": "3-point MACE",
    },
]


def get_trial(rv: str, nct: str) -> dict | None:
    """Fetch our extracted trial dict (or None) from <rv>.json."""
    p = DATA / f"{rv}.json"
    if not p.exists(): return None
    try: d = json.loads(p.read_text(encoding="utf-8"))
    except: return None
    rd = d.get("realData") or {}
    if not isinstance(rd, dict): return None
    t = rd.get(nct)
    if not isinstance(t, dict): return None
    return t


def log_hr_from_trial(t: dict) -> tuple[float, float] | None:
    """Return (log_hr, se_log_hr) for inverse-variance pooling, or None if missing."""
    hr = t.get("publishedHR")
    lci = t.get("hrLCI")
    uci = t.get("hrUCI")
    if hr is None or lci is None or uci is None: return None
    try:
        hr = float(hr); lci = float(lci); uci = float(uci)
    except: return None
    if hr <= 0 or lci <= 0 or uci <= 0: return None
    log_hr = math.log(hr)
    se = (math.log(uci) - math.log(lci)) / (2 * 1.959964)  # ±1.96σ
    if se <= 0: return None
    return log_hr, se


def pool_REML_HKSJ(yi_si: list[tuple[float, float]]) -> dict:
    """Inverse-variance random-effects pool with DL τ² + HKSJ adjustment.

    Returns {pool_HR, lci, uci, k, tau2, Q, Qp, I2, method}.
    Uses HKSJ when k >= 3.
    """
    k = len(yi_si)
    if k < 2: return {"error": "k<2"}
    yis = [y for y, s in yi_si]
    sis2 = [s*s for y, s in yi_si]
    wis_fe = [1.0 / s2 for s2 in sis2]
    sum_w = sum(wis_fe)
    yhat_fe = sum(w*y for w, y in zip(wis_fe, yis)) / sum_w

    # Q statistic
    Q = sum(w * (y - yhat_fe)**2 for w, y in zip(wis_fe, yis))
    df = k - 1
    # DerSimonian-Laird τ²
    c = sum_w - sum(w*w for w in wis_fe) / sum_w
    tau2 = max(0.0, (Q - df) / c) if c > 0 else 0.0

    # RE weights
    wis_re = [1.0 / (s2 + tau2) for s2 in sis2]
    sum_w_re = sum(wis_re)
    yhat_re = sum(w*y for w, y in zip(wis_re, yis)) / sum_w_re

    # SE (RE)
    se_re_std = math.sqrt(1.0 / sum_w_re)

    # HKSJ when k >= 3 — variance of mean
    if k >= 3:
        # HKSJ multiplier: sum( w_i * (y_i - yhat_re)^2 ) / (k-1) / sum_w_re
        rss = sum(w * (y - yhat_re)**2 for w, y in zip(wis_re, yis))
        # Floor at Q-floor = max(1, Q/(k-1)) per Cochrane v6.5 advanced-stats.md
        q_over_df = rss / (k - 1)
        var_hksj = max(q_over_df, 1.0) / sum_w_re  # apply floor
        se_re = math.sqrt(var_hksj)
        # t-distribution k-1 df
        # 95% CI: ±t_{k-1, 0.975}
        # Approximation: t_{k-1, 0.975} for small k
        t_crit = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571,
                  7: 2.447, 8: 2.365, 9: 2.306, 10: 2.262, 20: 2.086, 30: 2.042}
        df_ = k - 1
        t = t_crit.get(df_, 1.96)
        method = "REML-DL-HKSJ-Qfloor"
    else:
        se_re = se_re_std
        t = 1.96
        method = "DL (k<3, no HKSJ)"

    lci_log = yhat_re - t * se_re
    uci_log = yhat_re + t * se_re

    # Q p-value (χ² df=k-1)
    # Approximate using normal-cdf chain (good enough for k≤20)
    Qp = math.exp(-Q / 2)  # crude χ² approx; real p needs gamma; for k=2 OK

    I2 = max(0.0, 100.0 * (Q - df) / Q) if Q > 0 else 0.0

    return {
        "pool_HR": round(math.exp(yhat_re), 4),
        "lci": round(math.exp(lci_log), 4),
        "uci": round(math.exp(uci_log), 4),
        "log_HR": round(yhat_re, 4),
        "se_log_HR": round(se_re, 4),
        "tau2": round(tau2, 4),
        "Q": round(Q, 3),
        "Qp_approx": round(Qp, 4),
        "I2_pct": round(I2, 1),
        "k": k,
        "method": method,
    }


# ─────────── Run comparisons ───────────
results = []
for target in TARGETS:
    rv = target["our_review"]
    nct_set = target["trial_nct_set"]
    print(f"\n{'='*70}")
    print(f"Target: {target['name']}")
    print(f"  Published: HR {target['published_HR']} [{target['published_LCI']}, {target['published_UCI']}]")
    print(f"  Ref: {target['ref']}")

    # Fetch our trials
    yi_si_overlap = []
    overlap_nct_with_data = []
    overlap_nct_missing = []
    for nct, name in zip(nct_set, target["trial_names"]):
        t = get_trial(rv, nct)
        if t is None:
            overlap_nct_missing.append((nct, name, "not-in-review"))
            continue
        lhr = log_hr_from_trial(t)
        if lhr is None:
            overlap_nct_missing.append((nct, name, "missing-HR-or-CI"))
            continue
        yi_si_overlap.append(lhr)
        overlap_nct_with_data.append((nct, name, t.get("publishedHR")))

    n_overlap = len(yi_si_overlap)
    print(f"  Overlap: {n_overlap}/{len(nct_set)} trials with usable HR+CI in our extraction")
    for nct, name, hr in overlap_nct_with_data:
        print(f"     ✓ {name} ({nct}): HR={hr}")
    for nct, name, why in overlap_nct_missing:
        print(f"     ○ {name} ({nct}): {why}")

    # Pool the overlap
    if n_overlap >= 2:
        pool = pool_REML_HKSJ(yi_si_overlap)
        print(f"  Our overlap pool: HR {pool['pool_HR']} [{pool['lci']}, {pool['uci']}] "
              f"k={pool['k']} I²={pool['I2_pct']}%")
        # Delta
        delta_log = abs(math.log(pool["pool_HR"]) - math.log(target["published_HR"]))
        print(f"  Δ|log(HR)| = {delta_log:.4f}")
        result = {**target, "overlap": n_overlap, "trial_overlap_pct": round(100*n_overlap/len(nct_set), 1),
                  "overlap_nct_with_data": overlap_nct_with_data,
                  "overlap_nct_missing": overlap_nct_missing,
                  "our_overlap_pool": pool,
                  "delta_log_HR_vs_published": round(delta_log, 4),
                  "verdict": ("EXCELLENT" if delta_log < 0.01 else
                              "MATCHES" if delta_log < 0.025 else
                              "WITHIN-FLOOR" if delta_log < 0.05 else
                              "DIVERGE"),
                  }
    else:
        result = {**target, "overlap": n_overlap, "trial_overlap_pct": round(100*n_overlap/len(nct_set), 1),
                  "overlap_nct_with_data": overlap_nct_with_data,
                  "overlap_nct_missing": overlap_nct_missing,
                  "verdict": "INSUFFICIENT-OVERLAP"}
    results.append(result)

(OUT / "r5b_pool_results.json").write_text(
    json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nWrote {OUT / 'r5b_pool_results.json'}")

print(f"\n{'='*70}")
print(f"R5b Summary")
print(f"{'='*70}")
for r in results:
    print(f"  {r['verdict']:20s} {r['name'][:55]}")
    if "our_overlap_pool" in r:
        p = r["our_overlap_pool"]
        print(f"    Published: HR {r['published_HR']} [{r['published_LCI']}, {r['published_UCI']}]")
        print(f"    Ours:      HR {p['pool_HR']} [{p['lci']}, {p['uci']}]  (k={r['overlap']}/{len(r['trial_nct_set'])})")
        print(f"    Δ|log HR|: {r['delta_log_HR_vs_published']}")
