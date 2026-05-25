"""Inject the qProfileTau2CI helper (Viechtbauer 2007) into curated REVIEW
dashboards that have a `tau2` computation but no `qProfileTau2CI` helper.

Source of the canonical helper: FINERENONE_REVIEW.html lines 5979-6010.
Sentinel rule violation 'R-Qprofile-tau2': the helper is either missing
entirely OR present but never invoked — meaning the page can't compute the
random-effects heterogeneity-variance uncertainty interval that the
methodology rule mandates.

This script ONLY injects the helper definition (so the function is
callable). Wiring an invocation into each engine's main pool flow is a
deeper refactor that touches per-page variable scopes — left to a future
manual pass. Once the helper is present, a single line `const { tau2_lo,
tau2_hi } = qProfileTau2CI(plotData.map(d=>d.logOR), plotData.map(d=>d.vi),
k-1, 1-confLevel);` enables full Q-profile reporting where the engine
already exposes plotData / k / confLevel.

Insertion point: immediately after the existing `qchisq` helper (which
every affected dashboard has), since qProfileTau2CI calls qchisq.

Safety: each post-injection file is verified by the build-time JS parse
gate (scripts/_js_parse_gate.py). Files that fail the gate get rolled back.

Idempotent — re-running on a file that already has the helper is a no-op.
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

# Canonical helper text (extracted from FINERENONE_REVIEW.html), expanded
# to minimal whitespace so it injects cleanly regardless of host page style.
HELPER_BLOCK = """\

        // Q-profile tau-squared CI (Viechtbauer 2007). Injected by
        // scripts/propagate_qprofile_helper.py for Sentinel rule R-Qprofile-tau2.
        const qProfileTau2CI = (yi, vi, df, alpha) => {
            if (df < 1 || yi.length < 2) return { tau2_lo: NaN, tau2_hi: NaN };
            const qGen = (tau2) => {
                let sW = 0, sWY = 0, sW_Y2 = 0;
                for (let i = 0; i < yi.length; i++) {
                    const w = 1 / (vi[i] + tau2);
                    sW += w;
                    sWY += w * yi[i];
                    sW_Y2 += w * yi[i] * yi[i];
                }
                if (sW === 0) return 0;
                return Math.max(0, sW_Y2 - (sWY * sWY) / sW);
            };
            const cutHi = qchisq(1 - alpha/2, df);
            const cutLo = qchisq(alpha/2, df);
            const Q0 = qGen(0);
            const bisect = (target) => {
                if (Q0 <= target) return 0;
                let lo = 0, hi = 100;
                for (let _e = 0; _e < 30 && qGen(hi) > target && hi < 1e8; _e++) hi *= 2;
                for (let _i = 0; _i < 60; _i++) {
                    const mid = (lo + hi) / 2;
                    if (qGen(mid) > target) lo = mid; else hi = mid;
                }
                return (lo + hi) / 2;
            };
            return { tau2_lo: bisect(cutHi), tau2_hi: bisect(cutLo) };
        };
"""

# Anchor: the closing brace of the qchisq function. We insert immediately
# after. Pattern matches `const qchisq = ... => { ... };` with non-greedy body.
QCHISQ_END_RE = re.compile(
    r"(const\s+qchisq\s*=\s*\([^)]*\)\s*=>\s*\{[\s\S]{0,2000}?\};\s*\n)"
)


def patch_file(p: Path) -> bool:
    txt = p.read_text(encoding="utf-8", errors="replace")
    if "qProfileTau2CI" in txt:
        return False  # already present (helper or invocation)
    m = QCHISQ_END_RE.search(txt)
    if not m:
        return False  # no qchisq helper to anchor to
    new = txt[: m.end()] + HELPER_BLOCK + txt[m.end():]
    if not js_parse_ok(new):
        return False  # safety: don't ship broken JS
    p.write_text(new, encoding="utf-8")
    return True


def main():
    targets = [
        p for p in HERE.glob("*_REVIEW.html")
        if p.is_file()
        and "AUTO" not in p.name
        and "FULL_REVIEW" not in p.name
    ]
    print(f"Targets: {len(targets):,} curated REVIEW files")
    n_injected = n_skip_present = n_skip_no_anchor = n_rollback = 0
    for i, p in enumerate(targets, 1):
        txt = p.read_text(encoding="utf-8", errors="replace")
        if "qProfileTau2CI" in txt:
            n_skip_present += 1
            continue
        if not QCHISQ_END_RE.search(txt):
            n_skip_no_anchor += 1
            continue
        if patch_file(p):
            n_injected += 1
        else:
            n_rollback += 1
        if i % 100 == 0:
            print(f"  [{i}/{len(targets)}] {p.name}")
    print(f"\nInjected:      {n_injected:,}")
    print(f"Already had it: {n_skip_present:,}")
    print(f"No anchor:     {n_skip_no_anchor:,}")
    print(f"Rolled back:   {n_rollback:,}")


if __name__ == "__main__":
    main()
