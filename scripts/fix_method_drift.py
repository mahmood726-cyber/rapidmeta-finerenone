"""Align release-facing methods TEXT with the validated statistical contract.

Contract (test_reml_pooling.py + validate_living_ma_portfolio.py + R metafor
sidecars + the app's own HKSJ-CI which uses the REML estimate `_pLog_reml`):
  REML tau^2 + Hartung-Knapp-Sidik-Jonkman + t_{k-1} prediction interval.

The deployed copy carries hardcoded manuscript-export sentences, a methods-
table row, and PI-df text that claim DerSimonian-Laird + PI t_{k-2}. Those are
the drift. We replace ONLY those exact statement strings.

NOT touched (intentionally):
  - meta-regression k-2 df in JS code (correct for 1-predictor regression)
  - "DerSimonian-Laird+REML+HKSJ" implementation lists / DL-as-sensitivity
    option mentions / exported R-Python code that genuinely computes res_dl
"""
from __future__ import annotations
import argparse, glob, io, os, sys

# (old, new) — exact substrings only. Order matters (longest/most-specific first).
PAIRS = [
    # --- Pooling-model methods-table row + manuscript-statement sentences ---
    ("DerSimonian-Laird random-effects (inverse-variance weighting)",
     "REML random-effects, HKSJ-adjusted (inverse-variance weighting)"),
    ("Analysis performed using DerSimonian-Laird random-effects model with",
     "Analysis performed using a REML random-effects model (HKSJ-adjusted) with"),
    ("meta-analysis using the DerSimonian-Laird τ² estimator, with the Hartung-Knapp-Sidik-Jonkman",
     "meta-analysis using the REML τ² estimator, with the Hartung-Knapp-Sidik-Jonkman"),
    ("was performed using the DerSimonian-Laird estimator with Hartung-Knapp-Sidik-Jonkman adjustment",
     "was performed using the REML τ² estimator with Hartung-Knapp-Sidik-Jonkman adjustment"),
    ("Under DerSimonian-Laird random-effects pooling, ",
     "Under REML random-effects (HKSJ-adjusted) pooling, "),
    ("DerSimonian-Laird random-effects model with ${ciPct}%",
     "REML random-effects model (HKSJ-adjusted) with ${ciPct}%"),
    ("DerSimonian-Laird random-effects model. '+confLevel",
     "REML random-effects model (HKSJ-adjusted). '+confLevel"),
    # --- Prediction-interval df text (computation is t_{k-1}; contract = Cochrane v6.5) ---
    ("t-distribution, df = k&minus;2 (Higgins 2009)",
     "t-distribution, df = k&minus;1 (Cochrane Handbook v6.5)"),
    ("Prediction intervals computed with k−2 degrees of freedom per Higgins et al. (2009)",
     "Prediction intervals computed with k−1 degrees of freedom per the Cochrane Handbook (v6.5)"),
    ("prediction interval was computed using a t-distribution with k−2 degrees of freedom",
     "prediction interval was computed using a t-distribution with k−1 degrees of freedom"),
    ("prediction interval (Higgins 2009 t-distribution with df = k−2)",
     "prediction interval (Cochrane Handbook v6.5 t-distribution with df = k−1)"),
]


def fix_text(s):
    n = 0
    for old, new in PAIRS:
        c = s.count(old)
        if c:
            s = s.replace(old, new)
            n += c
    return s, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--glob", default="*.html")
    args = ap.parse_args()
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    files = files = sorted(glob.glob(os.path.join(here, args.glob)))
    repl = changed = 0
    for f in files:
        s = io.open(f, encoding="utf-8", errors="replace").read()
        new, n = fix_text(s)
        if n == 0:
            continue
        changed += 1
        repl += n
        if not args.dry_run:
            io.open(f, "w", encoding="utf-8", newline="").write(new)
    print(f"{'DRY-RUN' if args.dry_run else 'APPLIED'}  files changed={changed}  replacements={repl}")


if __name__ == "__main__":
    main()
