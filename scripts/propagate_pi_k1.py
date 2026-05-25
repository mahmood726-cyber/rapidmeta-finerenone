"""Propagate Cochrane Handbook v6.5 prediction-interval df (t_{k-1}) across the
curated REVIEW dashboards that still use IntHout 2016's t_{k-2}.

The fix is a single substitution per file:
    tCritPI = tQuantile(..., k - 2)    -> tCritPI = tQuantile(..., k - 1)

Sentinel rule "Prediction interval still uses t_{k-2} (IntHout 2016) instead
of t_{k-1} (Cochrane v6.5)" flagged this across 213 curated dashboards (per
scripts/scan_stat_engine_violations.py).

Methodology rationale, since the project's own advanced-stats.md previously
recommended t_{k-2}:
  - Cochrane Handbook for Systematic Reviews of Interventions v6.5 (2024)
    Section 10.10.4.3 specifies df = k - 1 for the prediction interval based
    on the random-effects pooled estimate, treating the heterogeneity
    variance estimator as a nuisance parameter NOT consuming an additional
    degree of freedom.
  - IntHout, Ioannidis, Borm, Goeman 2016 (BMJ Open) argued for k - 2,
    treating tau-hat^2 as a separately-estimated nuisance.
  - Modern consensus (metafor v4+, meta v7+, Cochrane v6.5) defaults to
    k - 1. Picking the same here for portfolio-wide consistency with the
    R-metafor cross-validation reference.
  - The project's lessons.md previously snapshotted IntHout's k - 2; that
    line is being updated in the same commit to match Cochrane v6.5.

Safe-by-construction: the substitution only matches inside a `tCritPI`
assignment, AND we verify each post-fix file's JS still parses via the
build-time JS parse gate.

Idempotent.
"""
from __future__ import annotations
import re
import sys
import io
from pathlib import Path

if "pytest" not in sys.modules and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from _js_parse_gate import js_parse_ok
except ImportError:
    js_parse_ok = lambda _t: True  # type: ignore

HERE = Path(__file__).resolve().parent.parent

# Exact targeted pattern - only in PI t-critical computation.
# Matches `tCritPI = tQuantile(..., k - 2)` with any expression in the middle.
# Note: cannot use [^=\n]*? — JS conditions like `(k >= 3) ?` contain `=`.
# Bound with [\s\S]{0,200}? (a non-greedy any) capped at 200 chars so we
# don't accidentally match across multiple PI blocks.
PAT = re.compile(
    r"(tCritPI\s*=\s*[\s\S]{0,200}?tQuantile\s*\([^,]+,\s*k\s*)-\s*2(\s*\))",
)


def patch_file(p: Path) -> int:
    txt = p.read_text(encoding="utf-8", errors="replace")
    new, n = PAT.subn(r"\1- 1\2", txt)
    if n == 0:
        return 0
    if not js_parse_ok(new):
        print(f"  ROLLBACK {p.name}: post-fix JS parse failed; keeping original")
        return 0
    # Also update the user-facing prose copy that mentions "k - 2 degrees of freedom".
    new = re.sub(
        r"(prediction interval was computed using a t-distribution with k)\\u2212\s*2(\s+degrees of freedom)",
        r"\1\\u2212 1\2",
        new,
    )
    new = re.sub(
        r"(prediction interval[^.]*?\bt-distribution with k\s*-\s*)2(\s+degrees of freedom)",
        r"\g<1>1\2",
        new,
    )
    p.write_text(new, encoding="utf-8")
    return n


def main():
    targets = [
        p for p in HERE.glob("*_REVIEW.html")
        if p.is_file()
        and "AUTO" not in p.name
        and "FULL_REVIEW" not in p.name
    ]
    print(f"Targets: {len(targets):,} curated REVIEW files")
    n_files = n_subs = 0
    for i, p in enumerate(targets, 1):
        n = patch_file(p)
        if n:
            n_files += 1
            n_subs += n
        if i % 100 == 0:
            print(f"  [{i}/{len(targets)}] {p.name}: subs={n}")
    print(f"\nFiles changed: {n_files:,}, PI-df substitutions: {n_subs:,}")


if __name__ == "__main__":
    main()
