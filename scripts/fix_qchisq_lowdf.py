"""
Fix qchisq accuracy for small df (df=1, df=2).

Wilson-Hilferty cube-root inverse is inaccurate at the tails for low df.
Specifically qchisq(0.025, 1) returns 0 via W-H which makes the Q-profile
bisection saturate at the search cap (1e8) for k=2 dashboards.

Replace with closed-form for df=1 (chi^2_1 -> z^2) and df=2 (chi^2_2 ->
-2*ln(1-p)), keep W-H for df>=3.

Idempotent: skipped if `df === 1` already in qchisq body.

Usage: python scripts/fix_qchisq_lowdf.py [--dry-run]
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

OLD = (
    "        // Chi-square quantile via Wilson-Hilferty inverse (sufficient for df >= 1).\n"
    "        const qchisq = (p, df) => {\n"
    "            if (df <= 0) return NaN;\n"
    "            const z = normalQuantile(p);\n"
    "            const v = 1 - 2/(9*df) + z * Math.sqrt(2/(9*df));\n"
    "            return Math.max(0, df * v * v * v);\n"
    "        };"
)

NEW = (
    "        // Chi-square quantile.\n"
    "        // df=1: chi^2_1 -> qnorm((1+p)/2)^2 (exact).\n"
    "        // df=2: chi^2_2 -> -2*ln(1-p) (exact).\n"
    "        // df>=3: Wilson-Hilferty cube-root inverse (sufficient).\n"
    "        const qchisq = (p, df) => {\n"
    "            if (df <= 0 || p <= 0) return 0;\n"
    "            if (p >= 1) return Infinity;\n"
    "            if (df === 1) { const z = normalQuantile((1 + p) / 2); return z * z; }\n"
    "            if (df === 2) return -2 * Math.log(1 - p);\n"
    "            const z = normalQuantile(p);\n"
    "            const v = 1 - 2/(9*df) + z * Math.sqrt(2/(9*df));\n"
    "            return Math.max(0, df * v * v * v);\n"
    "        };"
)


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
        if NEW in src:
            summary['unchanged'] += 1
            continue
        if OLD not in src:
            summary['unchanged'] += 1
            continue
        out = src.replace(OLD, NEW, 1)
        if not args.dry_run:
            open(path, 'w', encoding='utf-8').write(out)
        summary['changed'] += 1
    print(f'Summary: {summary}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
