"""
Switch PI df convention: t_{k-2} (IntHout 2016) -> t_{k-1} (Cochrane v6.5).

Per advanced-stats.md:
  PI df conflict: Cochrane Handbook v6.5 (Nov 2024, §10.10.4.3) uses
  `t_{k-1}` × √(τ²+SE²); IntHout/Higgins/Tudur Smith 2016 derived `t_{k-2}`.
  Default to `t_{k-1}` for Cochrane / RevMan-2025 bit-reproducibility.

This change makes PI CI matchable with Cochrane reviews. The PI is now
defined for k >= 2 (where t_1 is heavy-tailed but defined) instead of
k >= 3 (which the k-2 formula required).

Touches:
- ContinuousMDEngine PI computation
- Binary main pool PI computation
- PI display gate (k>=3 -> k>=2)

Idempotent: skipped if no `k - 2)` occurrences in PI context.

Usage: python scripts/fix_pi_df_cochrane.py [--dry-run]
"""
import argparse
import io
import os
import sys

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.environ.get(
    'RAPIDMETA_REPO_ROOT',
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)

# PI df + gate for both engines
REPLACEMENTS = [
    # Continuous engine (added in prior commit)
    (
        "        const tCritPI = (k >= 3) ? tQuantile(1 - (1 - confLevel) / 2, k - 2) : NaN;\n"
        "        const piLCI = (k >= 3) ? (pMD - tCritPI * piSE) : NaN;\n"
        "        const piUCI = (k >= 3) ? (pMD + tCritPI * piSE) : NaN;",
        "        // PI df = k-1 per Cochrane Handbook v6.5 §10.10.4.3 (RevMan default).\n"
        "        const tCritPI = (k >= 2) ? tQuantile(1 - (1 - confLevel) / 2, k - 1) : NaN;\n"
        "        const piLCI = (k >= 2) ? (pMD - tCritPI * piSE) : NaN;\n"
        "        const piUCI = (k >= 2) ? (pMD + tCritPI * piSE) : NaN;",
    ),
    # Binary main pool
    (
        "                const tCritPI = (k >= 3) ? tQuantile(1 - (1 - confLevel) / 2, k - 2) : NaN;\n"
        "\n"
        "\n"
        "                const piLCI = (k >= 3) ? Math.exp(pLogOR - tCritPI * piSE) : NaN;\n"
        "\n"
        "\n"
        "                const piUCI = (k >= 3) ? Math.exp(pLogOR + tCritPI * piSE) : NaN;",
        "                // PI df = k-1 per Cochrane Handbook v6.5 §10.10.4.3 (RevMan default).\n"
        "                const tCritPI = (k >= 2) ? tQuantile(1 - (1 - confLevel) / 2, k - 1) : NaN;\n"
        "\n"
        "\n"
        "                const piLCI = (k >= 2) ? Math.exp(pLogOR - tCritPI * piSE) : NaN;\n"
        "\n"
        "\n"
        "                const piUCI = (k >= 2) ? Math.exp(pLogOR + tCritPI * piSE) : NaN;",
    ),
    # Display gate
    (
        "                document.getElementById('res-pi').innerText = (c.k >= 3) ? `${c.piLCI.toFixed(2)} \\u2014 ${c.piUCI.toFixed(2)}` : 'N/A (k < 3)';",
        "                document.getElementById('res-pi').innerText = (c.k >= 2 && Number.isFinite(c.piLCI)) ? `${c.piLCI.toFixed(2)} \\u2014 ${c.piUCI.toFixed(2)}` : 'N/A (k < 2)';",
    ),
    # QA7 check label
    (
        "                checks.push({ id: 'QA7', name: 'Prediction Interval', status: r && r.piLCI !== '--' ? 'pass' : 'warn', detail: r && r.piLCI !== '--' ? 'PI: ' + r.piLCI + '\\u2014' + r.piUCI : 'Not available (k < 3)' });",
        "                checks.push({ id: 'QA7', name: 'Prediction Interval', status: r && r.piLCI !== '--' ? 'pass' : 'warn', detail: r && r.piLCI !== '--' ? 'PI: ' + r.piLCI + '\\u2014' + r.piUCI : 'Not available (k < 2)' });",
    ),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    print(f'Mode: {"DRY-RUN" if args.dry_run else "APPLY"}')
    files = sorted(
        f for f in os.listdir(ROOT)
        if f.endswith('_REVIEW.html') and not f.endswith('.bak.html')
    )
    summary = {'changed': 0, 'unchanged': 0}
    for fname in files:
        path = os.path.join(ROOT, fname)
        src = open(path, 'r', encoding='utf-8').read()
        out = src
        for old, new in REPLACEMENTS:
            if old in out and new not in out:
                out = out.replace(old, new, 1)
        if out != src:
            if not args.dry_run:
                open(path, 'w', encoding='utf-8').write(out)
            summary['changed'] += 1
        else:
            summary['unchanged'] += 1
    print(f'Summary: {summary}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
