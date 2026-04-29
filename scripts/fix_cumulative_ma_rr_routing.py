"""
Fix cumulative-MA log-OR-only routing (idempotent, exact-string).

The cumulative meta-analysis render() has:
  const useHR = (emMode === 'HR');
  // ...
  const logEff = Math.log((a / b) / (c / dd));
  const vi = 1 / a + 1 / b + 1 / c + 1 / dd;

When emMode is RR (default for binary in AUTO), this still pools log-OR.
Fix: add useRR declaration and an if/else at the formula site.

Uses exact-string replacement matching the actual file formatting
(double-newlines between statements). Idempotent.

Usage: python scripts/fix_cumulative_ma_rr_routing.py [--dry-run]
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

# Exact strings from the actual file (verified by raw inspection)
OLD_USEHR = "                const useHR = (emMode === 'HR');"
NEW_USEHR = (
    "                const useHR = (emMode === 'HR');\n"
    "\n"
    "\n"
    "                const useRR = (emMode === 'RR');"
)

# The formula block has a triple-newline separator (\n\n\n) between statements
OLD_FORMULA = (
    "                        const logEff = Math.log((a / b) / (c / dd));\n"
    "\n"
    "\n"
    "                        const vi = 1 / a + 1 / b + 1 / c + 1 / dd;"
)
NEW_FORMULA = (
    "                        let logEff, vi;\n"
    "                        if (useRR) {\n"
    "                            logEff = Math.log((a / (a + b)) / (c / (c + dd)));\n"
    "                            vi = b / (a * (a + b)) + dd / (c * (c + dd));\n"
    "                        } else {\n"
    "                            logEff = Math.log((a / b) / (c / dd));\n"
    "                            vi = 1 / a + 1 / b + 1 / c + 1 / dd;\n"
    "                        }"
)

# Idempotency marker — present after fix, absent before
FIXED_MARKER = "                        let logEff, vi;\n                        if (useRR) {"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    print(f'Mode: {"DRY-RUN" if args.dry_run else "APPLY"}')
    files = sorted(
        f for f in os.listdir(ROOT)
        if f.endswith('_REVIEW.html') and not f.endswith('.bak.html')
    )
    summary = {'changed': 0, 'unchanged': 0, 'partial_no_formula': 0, 'partial_no_usehr': 0}
    for fname in files:
        path = os.path.join(ROOT, fname)
        src = open(path, 'r', encoding='utf-8').read()
        if FIXED_MARKER in src:
            summary['unchanged'] += 1
            continue
        if 'cumulative-container' not in src:
            summary['unchanged'] += 1
            continue
        if OLD_FORMULA not in src:
            summary['unchanged'] += 1
            continue
        if OLD_USEHR not in src:
            summary['partial_no_usehr'] += 1
            continue
        out = src.replace(OLD_USEHR, NEW_USEHR, 1)
        out = out.replace(OLD_FORMULA, NEW_FORMULA, 1)
        if not args.dry_run:
            open(path, 'w', encoding='utf-8').write(out)
        summary['changed'] += 1
    print(f'Summary: {summary}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
