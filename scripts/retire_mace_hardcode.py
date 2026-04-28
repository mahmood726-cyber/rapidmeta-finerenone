"""
Retire the `shortLabel === 'MACE'` hardcoded debt across all RapidMeta dashboards.

Three patterns leak from the cardiology template into all 123 dashboards:

  1. `outcomes.find(o => o.shortLabel === 'MACE')` (~246 sites)
     - Used in applyOutcomeScope('default') and the trial-level outcome
       selector resolution to find the canonical primary outcome.
     - Replaced with `outcomes[0]` (the array is ordered with primary first
       by convention; this works for both cardio and non-cardio dashboards
       and unblocks renaming the primary's shortLabel away from 'MACE').

  2. `if (shortLabel === 'MACE') score += 20;` (~123 sites)
     - Auto-screening scoring boost for MACE-labeled outcomes. Dead in
       non-cardio dashboards and redundant in cardio (the immediately-
       preceding `if (isPrimary) score += 22;` already handles primary
       outcomes generally).
     - Deleted entirely. The isPrimary boost takes over.

Idempotent. Run before/after to compare:
    python scripts/retire_mace_hardcode.py --dry-run

Triggering incident: PEGCETACOPLAN_GA OAKS/DERBY swap fix renamed primary
shortLabels (GA12_Q4W, GA12_Q8W, etc.) and broke the hardcoded MACE
lookups silently.
"""
import argparse, os, re, sys

ROOT = r'C:\Projects\Finrenone'

# Pattern 1: outcomes.find(o => o.shortLabel === 'MACE') -> outcomes[0]
# Match common variations:
#   outcomes.find(o => o.shortLabel === 'MACE')
#   outcomes.find(x => x.shortLabel === 'MACE')
#   outcomes?.find(o => o?.shortLabel === 'MACE')
PATTERN_1_RE = re.compile(
    r"outcomes\??\.find\(\s*(\w+)\s*=>\s*\1\??\.shortLabel\s*===\s*'MACE'\s*\)"
)
PATTERN_1_REPLACE = "(outcomes && outcomes[0])"

# Pattern 2: standalone score-boost line. Match the entire line including
# trailing whitespace so deletion leaves clean indentation.
PATTERN_2_RE = re.compile(
    r"^\s*if\s*\(\s*shortLabel\s*===\s*'MACE'\s*\)\s*score\s*\+=\s*20\s*;\s*\n",
    re.M,
)


def patch_file(path, dry=False):
    src = open(path, 'r', encoding='utf-8').read()
    original = src

    n1 = 0
    src, n1 = PATTERN_1_RE.subn(PATTERN_1_REPLACE, src)

    n2 = 0
    src, n2 = PATTERN_2_RE.subn('', src)

    if src == original:
        return False, 'no_changes'
    if not dry:
        open(path, 'w', encoding='utf-8').write(src)
    return True, f'pattern1: {n1} replaced; pattern2: {n2} deleted'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    print(f'Mode: {"DRY-RUN" if args.dry_run else "APPLY"}')

    files = sorted([f for f in os.listdir(ROOT)
                    if f.endswith('_REVIEW.html')
                    and not f.endswith('.bak.html')])
    summary = {'changed': 0, 'unchanged': 0, 'errors': 0,
               'p1_total': 0, 'p2_total': 0}

    for fname in files:
        path = os.path.join(ROOT, fname)
        try:
            changed, info = patch_file(path, dry=args.dry_run)
            if changed:
                summary['changed'] += 1
                # Crude parse of info for summary
                p1 = int(info.split('pattern1: ')[1].split(' ')[0])
                p2 = int(info.split('pattern2: ')[1].split(' ')[0])
                summary['p1_total'] += p1
                summary['p2_total'] += p2
            else:
                summary['unchanged'] += 1
        except Exception as e:
            print(f'  [ERROR] {fname}: {e}')
            summary['errors'] += 1

    print(f'\nFiles touched: {summary["changed"]} of {len(files)}')
    print(f'  Pattern 1 (outcomes.find -> outcomes[0]): {summary["p1_total"]} total')
    print(f'  Pattern 2 (MACE score boost deleted):    {summary["p2_total"]} total')
    return 0 if summary['errors'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
