r"""Generate an R-validation sidecar JSON for binary-outcome meta-analyses
using REML + HKSJ + HKSJ-floor + Cochrane-v6.5 t_(k-1) prediction interval.

Same JSON schema as the existing outputs/r_validation/*.json so the page
engine renders the sidecar's "R-validation" panel.

Inputs: a FULL_REVIEW HTML containing trial blocks with tE/tN/cE/cN.
Output: outputs/r_validation/<TOPIC>.json

Methodology rationale (advanced-stats.md gotchas):
  * Yates 0.5 correction: applied ONLY when at least one cell is zero,
    not unconditionally (unconditional biases OR -> 1).
  * tau-squared via REML (Viechtbauer 2005): iterative, robust for k<10.
  * HKSJ floor at 1: when Q/(k-1) < 1, the HKSJ variance scaling would
    narrow CIs below DL; floor it (Wiksten et al. 2016).
  * Prediction interval via t_(k-1) per Cochrane Handbook v6.5
    (resolved 2026-05-25; supersedes IntHout 2016 t_(k-2)).
  * Fisher z / log scale -> back-transform after pooling.

Limitations:
  * Binary outcomes only. Pages with continuous outcomes (publishedHR/MD)
    are handled by a separate path or left to the existing R generator.
  * Requires k >= 2 trials (k=1 is a single-study summary, not a pool).
"""
from __future__ import annotations
import sys, io, re, json, math, argparse, datetime, hashlib, subprocess
from pathlib import Path

# sys.stdout reassignment lives in main() to avoid breaking importers
# (see lessons.md: module-level sys.stdout reassignment kills pytest /
# downstream callers' stdout when they import this module).

HERE = Path(__file__).resolve().parent.parent
SIDECAR_DIR = HERE / "outputs" / "r_validation"
SIDECAR_DIR.mkdir(parents=True, exist_ok=True)


def generator_provenance():
    """WHEN this ran and WHICH CODE ran, both measured at run time.

    The previous version wrote a hardcoded `"generated_on": "2026-05-26"` on
    every file it produced. Regenerating with that in place would stamp 692
    rebuilt artefacts with a date that was not true, and a reader could not
    then tell a corrected artefact from the original by its provenance --
    which would leave the corrected corpus indistinguishable from the broken
    one, the exact property the regeneration exists to remove.

    A DATE ALONE IS NOT ENOUGH. It says when, not which code. Two artefacts
    built the same day either side of an estimator fix carry the same date
    and different numbers. So this also records:

      generator_sha256  the hash of THIS FILE as it ran. This is the field
                        that actually separates a pre-fix artefact from a
                        post-fix one, and it works even when the generator
                        is uncommitted -- which it is during a fix.
      generator_commit  the repository HEAD, for humans. Recorded as
                        "unavailable" rather than omitted if git cannot be
                        reached, because a missing field reads as an
                        oversight while a named absence reads as a fact.
      generator_tree_dirty  whether the working tree had uncommitted changes,
                        so `generator_commit` is never mistaken for a
                        complete description of what ran.
    """
    src = Path(__file__).resolve()
    try:
        digest = hashlib.sha256(src.read_bytes()).hexdigest()
    except Exception:
        digest = "unavailable"
    commit, dirty = "unavailable", None
    try:
        p = subprocess.run(["git", "-C", str(HERE), "rev-parse", "HEAD"],
                           capture_output=True)
        if p.returncode == 0:
            commit = p.stdout.decode("utf-8", "replace").strip()
        p2 = subprocess.run(["git", "-C", str(HERE), "status", "--porcelain",
                             "--", str(src)], capture_output=True)
        if p2.returncode == 0:
            dirty = bool(p2.stdout.decode("utf-8", "replace").strip())
    except Exception:
        pass
    return {
        "generated_by": "scripts/build_binary_sidecar.py",
        "generated_on": datetime.datetime.now(
            datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator_sha256": digest,
        "generator_commit": commit,
        "generator_file_uncommitted": dirty,
        "estimator": "REML tau2 via the Viechtbauer (2005) direct update, "
                     "including the 1/sum(w) term. Artefacts stamped with a "
                     "generator_sha256 other than this one may have been "
                     "built by the earlier increment form, which could not "
                     "return a non-zero tau2 once a step went negative.",
    }

# Trial-block regex handles all three NCT-key quote forms (post-terser).
TRIAL_RE = re.compile(
    r"(?:'(NCT\d{7,8})'|\"(NCT\d{7,8})\"|\b(NCT\d{7,8}))\s*:\s*\{"
    r"(?P<body>(?:[^{}]|\{[^{}]*\}){0,4000})\}",
    re.DOTALL,
)


def get_num(body, name):
    """Get a numeric field. None on null/missing."""
    m = re.search(
        rf"['\"]?{name}['\"]?\s*:\s*(-?[\d.eE+-]+|null|None)",
        body,
    )
    if not m: return None
    v = m.group(1)
    if v in ("null", "None"): return None
    try:
        return float(v) if "." in v or "e" in v.lower() else int(v)
    except ValueError:
        return None


def get_str(body, name):
    """Get a string field (handles JSON-quoted and JS unquoted keys)."""
    m = re.search(rf"['\"]?{name}['\"]?\s*:\s*['\"]([^'\"]*)['\"]", body)
    return m.group(1) if m else None


def normal_quantile(p):
    """Inverse normal CDF, no scipy dependency. Acklam approximation."""
    # See Peter J. Acklam's algorithm. Accurate to ~1e-9 in central region.
    a = [-39.69683028665376, 220.9460984245205, -275.9285104469687,
         138.3577518672690, -30.66479806614716, 2.506628277459239]
    b = [-54.47609879822406, 161.5858368580409, -155.6989798598866,
         66.80131188771972, -13.28068155288572]
    c = [-0.007784894002430293, -0.3223964580411365, -2.400758277161838,
         -2.549732539343734, 4.374664141464968, 2.938163982698783]
    d = [0.007784695709041462, 0.3224671290700398, 2.445134137142996,
         3.754408661907416]
    plow = 0.02425
    phigh = 1 - plow
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return ((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5] / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5] / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q*q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
           (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def t_quantile_975(df):
    """Two-sided 97.5% t-quantile (alpha=0.025 upper tail), with df>=1.
    Hill (1970) approximation; good to ~1e-4 for df>=2."""
    if df <= 0:
        return float('nan')
    if df == 1:
        return 12.7062
    if df == 2:
        return 4.30265
    if df == 3:
        return 3.18245
    if df == 4:
        return 2.77645
    if df == 5:
        return 2.57058
    if df == 6:
        return 2.44691
    if df == 7:
        return 2.36462
    if df == 8:
        return 2.306
    if df == 9:
        return 2.26216
    if df == 10:
        return 2.22814
    if df == 12:
        return 2.1788
    if df == 15:
        return 2.13145
    if df == 20:
        return 2.08596
    if df == 30:
        return 2.04227
    if df == 60:
        return 2.0003
    # Hill's algorithm for general df
    z = 1.959964   # qnorm(0.975)
    g1 = (z**3 + z) / 4
    g2 = (5*z**5 + 16*z**3 + 3*z) / 96
    g3 = (3*z**7 + 19*z**5 + 17*z**3 - 15*z) / 384
    g4 = (79*z**9 + 776*z**7 + 1482*z**5 - 1920*z**3 - 945*z) / 92160
    return z + g1/df + g2/df**2 + g3/df**3 + g4/df**4


def log_or_per_trial(tE, tN, cE, cN):
    """Compute logOR + variance for one trial. Returns (yi, vi) or None
    if the trial is unanalyzable (e.g., 100% in both arms)."""
    # Yates 0.5 only if any cell is 0
    tNE = tN - tE
    cNE = cN - cE
    cells = [tE, tNE, cE, cNE]
    if any(c < 0 for c in cells):
        return None
    if min(cells) == 0:
        a = tE + 0.5
        b = tNE + 0.5
        c = cE + 0.5
        d = cNE + 0.5
    else:
        a, b, c, d = tE, tNE, cE, cNE
    try:
        yi = math.log((a * d) / (b * c))
        vi = 1/a + 1/b + 1/c + 1/d
    except (ValueError, ZeroDivisionError):
        return None
    if not math.isfinite(yi) or not math.isfinite(vi) or vi <= 0:
        return None
    return yi, vi


def reml_tau2(yis, vis, max_iter=1000, tol=1e-16):
    """REML estimator of tau-squared, Viechtbauer (2005).

        w = 1/(v + tau2);  sw = sum(w);  mu = sum(w*y)/sw
        tau2 <- sum(w^2 * ((y - mu)^2 - v)) / sum(w^2)  +  1/sw

    CORRECTED 2026-08-31. The previous implementation was

        tau2 <- tau2 + sum(w^2 * ((y - mu)^2 - v)) / sum(w^2)

    which differs in two ways, and both matter. It was an INCREMENT on the
    previous value rather than a direct assignment, and it OMITTED the
    `1/sum(w)` term -- which is the entire difference between REML and ML.
    Without that term the estimator is biased downward, and because the
    result is clamped at zero it had a fixed point AT zero: once a step went
    negative the loop returned exactly 0.0 and stopped.

    WHY THIS SURVIVED SO LONG, AND THE GENERAL LESSON. tau2 = 0 means "no
    heterogeneity detected", which is a legitimate and common finding. The
    FAILURE VALUE of this estimator was also a MEANINGFUL VALUE, so its
    output was indistinguishable from a real result. No range check, no
    assertion and no plausibility test on the number itself could separate
    the two. Only an EXTERNAL ORACLE -- the same quantity computed by an
    independent program -- can. Here that oracle is metafor 5.0.1 under
    R 4.6.0, run by scripts/metafor_oracle.R, whose output is the fixture
    tests/fixtures/metafor_oracle.json. When a computation's failure value is
    also a meaningful value, an external oracle is not a nicety; it is the
    only detector.

    MEASURED EFFECT of the defect, before this fix: of 351 sidecars whose
    stored tau2 was exactly 0.0, 250 were legitimately zero (the correct
    estimator agrees), 86 had heterogeneity erased, and 3 of those carried a
    published interval that excluded the null and no longer does.

    Do NOT "simplify" this back toward the old form. Both the direct
    assignment and the `1/sw` term are load-bearing, and
    tests/test_metafor_oracle.py fails against metafor-computed values if
    either is removed.

    ROBUST FALLBACK ADDED 2026-09-01, and it was found the same way as the
    original defect -- by an external oracle, not by inspection. The
    fixed-point iteration below converges on most inputs but not all: on the
    OMECAMTIV rows it settled at 0.0030576 where metafor returns 0.4893, a
    factor of 160, and it settled LOW. Settling low is the same direction as
    the bug this function was written to fix, and therefore just as
    invisible.

    A fixed point of f is a root of g(t) = f(t) - t. As t grows, w -> 1/t,
    so f(t) -> mean((y-mu)^2 - v) + t/k and g(t) -> C - t*(1 - 1/k), which
    goes to minus infinity for k >= 2. So g is bracketed and bisection is
    guaranteed to find the root. An earlier attempt at bisection bracketed
    sum(w^2*(...)) instead of g, which never crosses zero -- that failure was
    a statement about the bracket, not about the method.

    Iterate first (fast, and exact where it converges); bisect only where it
    does not. Validated against 46 metafor values: 0 disagreements, worst
    relative 3.6e-05.
    """
    k = len(yis)
    if k < 2:
        return 0.0

    def _f(t):
        ws = [1.0 / (v + t) for v in vis]
        sw = sum(ws)
        mu = sum(w * y for w, y in zip(ws, yis)) / sw
        den = sum(w ** 2 for w in ws)
        num = sum((w ** 2) * ((y - mu) ** 2 - v)
                  for w, y, v in zip(ws, yis, vis))
        return num / den + 1.0 / sw

    tau2 = 0.0
    for _ in range(max_iter):
        try:
            nxt = _f(tau2)
        except ZeroDivisionError:
            return 0.0
        if not math.isfinite(nxt):
            break
        nxt = max(0.0, nxt)
        if abs(nxt - tau2) < tol:
            return nxt
        tau2 = nxt

    # the iteration did not settle: solve g(t) = f(t) - t = 0 by bisection
    def _g(x):
        return _f(x) - x

    if _g(0.0) <= 0.0:
        return 0.0
    hi = max(1e-6, max(vis)) * 10.0 + 1.0
    for _ in range(200):
        if _g(hi) < 0.0:
            break
        hi *= 2.0
    lo = 0.0
    for _ in range(300):
        mid = 0.5 * (lo + hi)
        if _g(mid) > 0.0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def pool_binary(trials_xy):
    """Pool a list of (yi, vi) tuples via REML+HKSJ+floor and compute the
    Cochrane v6.5 prediction interval. Returns a dict ready for JSON output."""
    yis = [t[0] for t in trials_xy]
    vis = [t[1] for t in trials_xy]
    k = len(yis)

    tau2 = reml_tau2(yis, vis)
    ws = [1.0 / (v + tau2) for v in vis]
    sw = sum(ws)
    mu = sum(w * y for w, y in zip(ws, yis)) / sw
    var_mu_re = 1.0 / sw
    se_re = math.sqrt(var_mu_re)

    # Q statistic (random-effects: still computed at fixed-effect weights)
    ws_fe = [1.0 / v for v in vis]
    mu_fe = sum(w * y for w, y in zip(ws_fe, yis)) / sum(ws_fe)
    Q = sum(w * (y - mu_fe)**2 for w, y in zip(ws_fe, yis))
    Qdf = k - 1
    # Chi-square upper-tail p via Wilson-Hilferty approximation
    # X^2(df) ~ df * (1 - 2/(9df) + z * sqrt(2/(9df)))^3  =>  invert
    if Qdf > 0:
        # Use Pearson chi-square approximation
        from math import exp, sqrt as _sqrt, lgamma
        # Use complementary CDF via incomplete gamma series
        # Simplification: use the regularized incomplete gamma function Q(s, x)
        # via series. Acceptable for our display purposes.
        def _gammaincc(s, x):
            # Complementary regularized incomplete gamma function.
            if x < 0 or s <= 0: return 1.0
            if x == 0: return 1.0
            # Continued fraction for x > s+1, series otherwise
            if x < s + 1:
                # series
                ap = s
                summ = 1 / s
                term = summ
                for _ in range(200):
                    ap += 1
                    term *= x / ap
                    summ += term
                    if abs(term) < abs(summ) * 1e-12:
                        break
                return 1 - summ * exp(-x + s * math.log(x) - lgamma(s))
            else:
                # continued fraction
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
                return h * exp(-x + s * math.log(x) - lgamma(s))
        Qp = _gammaincc(Qdf / 2.0, Q / 2.0)
    else:
        Qp = float('nan')

    # I^2
    I2 = max(0.0, (Q - Qdf) / Q) * 100 if Q > 0 else 0.0
    H2 = max(1.0, Q / Qdf) if Qdf > 0 else 1.0

    # HKSJ correction with floor at 1 (Wiksten 2016)
    hksj_scale_raw = sum(w * (y - mu)**2 for w, y in zip(ws, yis)) / (k - 1) if k > 1 else 1.0
    hksj_scale = max(1.0, hksj_scale_raw)
    se_hksj = math.sqrt(hksj_scale * var_mu_re)
    floor_applied = hksj_scale_raw < 1.0

    # CI on log scale using t_(k-1)
    t_crit = t_quantile_975(k - 1)
    ci_lo = mu - t_crit * se_hksj
    ci_hi = mu + t_crit * se_hksj

    # Prediction interval via t_(k-1) (Cochrane v6.5)
    if k >= 3:
        pi_se = math.sqrt(tau2 + se_hksj**2)
        pi_lo = mu - t_crit * pi_se
        pi_hi = mu + t_crit * pi_se
    else:
        pi_lo = pi_hi = float('nan')

    return {
        "k": k,
        "pooled_logOR": mu,
        "pooled_se": se_hksj,
        "pooled_OR": math.exp(mu),
        "ci_low_OR": math.exp(ci_lo),
        "ci_high_OR": math.exp(ci_hi),
        "tau2": tau2,
        "I2": I2,
        "H2": H2,
        "Q": Q,
        "Qdf": Qdf,
        "Qp": Qp,
        "PI_low_OR": math.exp(pi_lo) if not math.isnan(pi_lo) else None,
        "PI_high_OR": math.exp(pi_hi) if not math.isnan(pi_hi) else None,
        "pi_df_convention": "t_{k-1}_Cochrane_v6.5",
        "hksj_floor_applied": floor_applied,
        "hksj_scale_raw": hksj_scale_raw,
        "method": "REML+HKSJ+floor",
    }


def extract_binary_trials(page_path):
    """Return list of dicts with name/nct/pmid/tE/tN/cE/cN/yi/vi.
    Skips trials without 4 binary counts."""
    txt = page_path.read_text(encoding="utf-8", errors="replace")
    out = []
    for m in TRIAL_RE.finditer(txt):
        nct = m.group(1) or m.group(2) or m.group(3)
        body = m.group("body")
        tE = get_num(body, "tE")
        tN = get_num(body, "tN")
        cE = get_num(body, "cE")
        cN = get_num(body, "cN")
        if None in (tE, tN, cE, cN):
            continue
        if tN <= 0 or cN <= 0:
            continue
        if tE > tN or cE > cN:
            continue  # impossible; skip
        r = log_or_per_trial(int(tE), int(tN), int(cE), int(cN))
        if r is None:
            continue
        yi, vi = r
        out.append({
            "name": get_str(body, "name") or nct,
            "nct": nct,
            "pmid": get_str(body, "pmid"),
            "tE": tE,
            "tN": tN,
            "cE": cE,
            "cN": cN,
            "yi": yi,
            "vi": vi,
        })
    return out


def sidecar_stem(page_name: str) -> str:
    """The engine fetches outputs/r_validation/<STEM>.json where <STEM> is
    the page name with only the final _REVIEW.html removed. Verified via
    puppeteer log: ABALOPARATIDE_OSTEO_AUTO_FULL_REVIEW.html fetches
    `ABALOPARATIDE_OSTEO_AUTO_FULL.json`, not the topic-only stem.
    Existing sidecars (FINERENONE.json for FINERENONE_REVIEW.html) match
    this rule once you account for `_REVIEW` being the only suffix on
    those flagship pages.
    """
    n = page_name.replace(".html", "")
    if n.endswith("_REVIEW"):
        n = n[: -len("_REVIEW")]
    return n


def emit_sidecar(page_path: Path, force=False, out_dir=None) -> dict:
    """Generate (or refuse) a sidecar for the given page. Returns status dict.

    out_dir lets a regeneration write to a PARALLEL location, so a rebuilt
    corpus can be compared against the served one before anything is
    replaced. Nothing is swapped in place by this function.
    """
    stem = sidecar_stem(page_path.name)
    out_path = Path(out_dir or SIDECAR_DIR) / f"{stem}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists() and not force:
        return {"status": "exists", "page": page_path.name, "stem": stem}

    trials = extract_binary_trials(page_path)
    if len(trials) < 2:
        return {"status": "insufficient_k", "page": page_path.name, "k": len(trials)}

    pool = pool_binary([(t["yi"], t["vi"]) for t in trials])
    # Trim trial detail to publishable fields
    trial_records = [{
        "name": t["name"],
        "nct": t["nct"],
        "tE": t["tE"], "tN": t["tN"], "cE": t["cE"], "cN": t["cN"],
        "yi": round(t["yi"], 6),
        "vi": round(t["vi"], 6),
    } for t in trials]

    # Match the existing field ordering (FINERENONE.json layout)
    sidecar = {
        "k": pool["k"],
        "pooled_logOR": round(pool["pooled_logOR"], 6),
        "pooled_se": round(pool["pooled_se"], 6),
        "pooled_OR": round(pool["pooled_OR"], 6),
        "ci_low_OR": round(pool["ci_low_OR"], 6),
        "ci_high_OR": round(pool["ci_high_OR"], 6),
        "tau2": round(pool["tau2"], 10),
        "I2": round(pool["I2"], 6),
        "H2": round(pool["H2"], 6),
        "Q": round(pool["Q"], 6),
        "Qdf": pool["Qdf"],
        "Qp": float(f"{pool['Qp']:.6e}") if pool["Qp"] == pool["Qp"] else None,
        "PI_low_OR": round(pool["PI_low_OR"], 6) if pool["PI_low_OR"] is not None else None,
        "PI_high_OR": round(pool["PI_high_OR"], 6) if pool["PI_high_OR"] is not None else None,
        "pi_df_convention": pool["pi_df_convention"],
        "hksj_floor_applied": pool["hksj_floor_applied"],
        "method": pool["method"],
        "trials": trial_records,
    }
    # Provenance measured at run time, never asserted. See
    # generator_provenance(): a date says WHEN, the generator hash says
    # WHICH CODE, and only the second distinguishes an artefact built before
    # the reml_tau2 correction from one built after it.
    sidecar.update(generator_provenance())
    out_path.write_text(json.dumps(sidecar, indent=2), encoding="utf-8")
    return {"status": "generated", "page": page_path.name, "stem": stem,
            "k": pool["k"], "pooled_OR": pool["pooled_OR"]}


def main():
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="build binary-outcome sidecars")
    ap.add_argument("--out-dir", default=None,
                    help="write to a PARALLEL directory instead of the served "
                         "one. Nothing is replaced in place.")
    ap.add_argument("--force", action="store_true",
                    help="rebuild sidecars that already exist at the target")
    args = ap.parse_args()
    out_dir = Path(args.out_dir) if args.out_dir else SIDECAR_DIR

    targets = sorted(p for p in HERE.glob("*_FULL_REVIEW.html") if p.is_file())
    print(f"Candidate FULL_REVIEW pages: {len(targets):,}")
    print(f"Writing to: {out_dir}")
    if out_dir == SIDECAR_DIR:
        print("  NOTE: this is the SERVED directory.")
    prov = generator_provenance()
    print(f"  generator sha256 {prov['generator_sha256'][:16]}  "
          f"commit {prov['generator_commit'][:12]}  "
          f"uncommitted={prov['generator_file_uncommitted']}")

    stats = {"generated": 0, "exists": 0, "insufficient_k": 0}
    for i, p in enumerate(targets, 1):
        r = emit_sidecar(p, force=args.force, out_dir=out_dir)
        stats[r["status"]] = stats.get(r["status"], 0) + 1
        if i % 200 == 0:
            print(f"  [{i}/{len(targets)}]  {stats}")
    print(f"\nDone. {stats}")
    print(f"Sidecars now in {out_dir}: {len(list(Path(out_dir).rglob('*.json'))):,}")


if __name__ == "__main__":
    main()
