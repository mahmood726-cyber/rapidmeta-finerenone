"""
Audit dermatology dashboards (and any specified file) for OR-mislabeled-as-RR
or RR-mislabeled-as-OR in trial allOutcomes entries.

For each PRIMARY outcome with binary event counts (tE, cE, tN, cN):
- Compute RR = (tE/tN) / (cE/cN) — handles zero-cell with 0.5 correction
- Compute OR = (tE*(cN-cE)) / (cE*(tN-tE)) — same correction
- Compare to declared `effect` and `estimandType`
- Flag if effect matches the OTHER estimand (sign of mislabeling)

Pure read; emits a CSV-style report. Use --apply later to autocorrect labels.

Usage: python scripts/audit_or_vs_rr.py [FILES...]
"""
import argparse
import io
import os
import re
import sys

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.environ.get(
    'RAPIDMETA_REPO_ROOT',
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)


def compute(tE, tN, cE, cN):
    if None in (tE, tN, cE, cN):
        return None, None
    if tN <= 0 or cN <= 0:
        return None, None
    a, b, c, d = tE, tN - tE, cE, cN - cE
    if a == 0 or b == 0 or c == 0 or d == 0:
        a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
        tE_, tN_ = a, a + b
        cE_, cN_ = c, c + d
    else:
        tE_, tN_, cE_, cN_ = tE, tN, cE, cN
    rr = (tE_ / tN_) / (cE_ / cN_)
    or_ = (tE_ * (cN_ - cE_)) / (cE_ * (tN_ - tE_)) if (cE_ * (tN_ - tE_)) > 0 else None
    return rr, or_


TRIAL_RE = re.compile(
    r"name:\s*['\"]([^'\"]+)['\"][^}]*?"
    r"tE:\s*(\d+),\s*tN:\s*(\d+),\s*cE:\s*(\d+),\s*cN:\s*(\d+)[^}]*?"
    r"allOutcomes:\s*\[(.*?)\]\s*,\s*rob:",
    re.DOTALL,
)

OUTCOME_RE = re.compile(
    r"\{[^{}]*?type:\s*'(PRIMARY)'[^{}]*?effect:\s*([\d.]+)[^{}]*?"
    r"estimandType:\s*'([A-Z]+)'[^{}]*?\}",
)


def audit_file(path):
    src = open(path, 'r', encoding='utf-8').read()
    rows = []
    for m in TRIAL_RE.finditer(src):
        name, tE, tN, cE, cN, outcomes_text = m.groups()
        tE, tN, cE, cN = int(tE), int(tN), int(cE), int(cN)
        rr, or_ = compute(tE, tN, cE, cN)
        for om in OUTCOME_RE.finditer(outcomes_text):
            otype, effect, etype = om.groups()
            effect = float(effect)
            if rr is None:
                continue
            tol = 0.05 * max(abs(rr), abs(or_ or 0), 1)
            matches_rr = abs(effect - rr) <= tol
            matches_or = or_ is not None and abs(effect - or_) <= tol
            mismatch = None
            if etype == 'OR' and matches_rr and not matches_or:
                mismatch = 'OR-labeled but value is RR'
            elif etype == 'RR' and matches_or and not matches_rr:
                mismatch = 'RR-labeled but value is OR'
            elif not matches_rr and not matches_or:
                or_str = f'{or_:.2f}' if or_ else 'None'
                mismatch = f'value matches neither (RR={rr:.2f}, OR={or_str})'
            if mismatch:
                rows.append({
                    'file': os.path.basename(path),
                    'trial': name,
                    'tE': tE, 'tN': tN, 'cE': cE, 'cN': cN,
                    'effect': effect,
                    'declared': etype,
                    'computed_RR': round(rr, 3),
                    'computed_OR': round(or_, 3) if or_ else None,
                    'flag': mismatch,
                })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='*', help='Specific *_REVIEW.html files (default: all)')
    args = ap.parse_args()
    if args.files:
        paths = [os.path.join(ROOT, f) if not os.path.isabs(f) else f for f in args.files]
    else:
        paths = sorted(
            os.path.join(ROOT, f)
            for f in os.listdir(ROOT)
            if f.endswith('_REVIEW.html') and not f.endswith('.bak.html')
        )
    all_rows = []
    for p in paths:
        all_rows.extend(audit_file(p))
    if not all_rows:
        print('No mismatches detected.')
        return 0
    print(f'Found {len(all_rows)} mismatches:')
    print(f'{"File":<35} {"Trial":<25} {"effect":<8} {"declared":<8} {"RR":<8} {"OR":<8} flag')
    print('-' * 120)
    for r in all_rows:
        print(f'{r["file"]:<35} {r["trial"]:<25} {r["effect"]:<8.2f} {r["declared"]:<8} {r["computed_RR"]:<8.2f} {str(r["computed_OR"] or "-"):<8} {r["flag"]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
