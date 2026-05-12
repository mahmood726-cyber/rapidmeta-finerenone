"""Audit existing pairwise R-validation files vs engine-recomputed pool.

For each outputs/r_validation/<REVIEW>.json (271 files), recompute the
DerSimonian-Laird random-effects log-OR pool from the realData in
outputs/extraction_audit/data/<REVIEW>_REVIEW.json and compare to the
R metafor pool. Flag any |Δ log-OR| ≥ 0.10 (≈10% relative on OR scale)
or any sign-flip.

This is the same internal-consistency check the audit agents did, but
now applied portfolio-wide to the pre-existing R-validation outputs.
"""
from __future__ import annotations
import io, json, math, sys
from pathlib import Path

if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

REPO = Path(__file__).resolve().parent.parent
R_DIR = REPO / "outputs" / "r_validation"
DATA_DIR = REPO / "outputs" / "extraction_audit" / "data"


def _finite(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def trial_log_or(tE, tN, cE, cN):
    a, b, c, d = tE, tN - tE, cE, cN - cE
    if min(a, b, c, d) == 0:
        a += 0.5; b += 0.5; c += 0.5; d += 0.5
    return math.log((a * d) / (b * c)), 1/a + 1/b + 1/c + 1/d


def pool_dl(trials):
    pts = []
    for t in trials:
        tE, tN, cE, cN = t.get("tE"), t.get("tN"), t.get("cE"), t.get("cN")
        if not all(_finite(v) for v in (tE, tN, cE, cN)): continue
        if not (tN > 0 and cN > 0 and tE >= 0 and cE >= 0 and tE <= tN and cE <= cN): continue
        try:
            yi, vi = trial_log_or(int(tE), int(tN), int(cE), int(cN))
        except Exception:
            continue
        pts.append((yi, vi))
    if len(pts) < 2: return None
    W = sum(1/v for _, v in pts)
    yFE = sum(y/v for y, v in pts) / W
    Q = sum((y - yFE)**2 / v for y, v in pts)
    df = len(pts) - 1
    sumW2 = sum((1/v)**2 for _, v in pts)
    c = W - sumW2/W
    tau2 = max(0.0, (Q - df)/c) if c > 0 else 0.0
    W2 = sum(1/(v + tau2) for _, v in pts)
    yRE = sum(y/(v + tau2) for y, v in pts) / W2
    return {"yRE": yRE, "OR": math.exp(yRE), "k": len(pts), "tau2": tau2, "Q": Q}


def main():
    n_files = 0; matches = 0; mismatches = []; missing_data = []
    for r_path in sorted(R_DIR.glob("*.json")):
        if r_path.stem in ("index", "_index"): continue
        if r_path.stem == "dta_index": continue
        stem = r_path.stem  # e.g. ABLATION_AF
        review_stem = stem + "_REVIEW"
        data_path = DATA_DIR / f"{review_stem}.json"
        if not data_path.exists():
            missing_data.append(stem); continue
        try:
            r_out = json.loads(r_path.read_text(encoding="utf-8"))
            doc = json.loads(data_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not r_out.get("pooled_logOR") and r_out.get("pooled_logOR") != 0:
            continue
        rd = doc.get("realData") or {}
        engine_pool = pool_dl(list(rd.values()))
        if engine_pool is None: continue
        n_files += 1
        r_logOR = float(r_out["pooled_logOR"])
        e_logOR = engine_pool["yRE"]
        delta = abs(r_logOR - e_logOR)
        sign_flip = (r_logOR < 0) != (e_logOR < 0) and abs(r_logOR) > 0.01 and abs(e_logOR) > 0.01
        if delta < 0.10 and not sign_flip:
            matches += 1
        else:
            mismatches.append({
                "stem": stem,
                "r_OR": math.exp(r_logOR), "engine_OR": math.exp(e_logOR),
                "delta_log": delta, "sign_flip": sign_flip,
                "k_r": r_out.get("k"), "k_e": engine_pool["k"]
            })
    print(f"Files audited: {n_files}")
    print(f"Match (|Δlog| < 0.10): {matches} ({matches*100//max(1,n_files)}%)")
    print(f"Mismatches: {len(mismatches)}")
    print(f"Missing data files: {len(missing_data)}")
    if mismatches:
        mismatches.sort(key=lambda x: -x["delta_log"])
        print("\nTop 15 worst mismatches:")
        for m in mismatches[:15]:
            flip = " SIGN-FLIP" if m["sign_flip"] else ""
            print(f"  {m['stem']:38s} R={m['r_OR']:.3f} engine={m['engine_OR']:.3f} "
                  f"Δlog={m['delta_log']:.2f} k_r={m['k_r']} k_e={m['k_e']}{flip}")
        # Save full report
        out = REPO / "outputs" / "r_validation" / "_audit_vs_engine.json"
        out.write_text(json.dumps({
            "audited": n_files, "matches": matches, "mismatches": mismatches,
            "missing_data": missing_data,
        }, indent=2), encoding="utf-8")
        print(f"\nFull report: {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
