"""
Replace the hardcoded `<select id="mf-indication">` dropdown with a free-text
input across all non-cardio pairwise reviews. The default options
(CKD/Heart Failure/Other) were Finrenone-template leftovers and surfaced as
wrong choices on every non-cardio dashboard.

Consumer code reads `.value`; an `<input>` works identically.

Usage:
    python scripts/patch_indication_dropdown.py --dry-run
    python scripts/patch_indication_dropdown.py
"""
import argparse, os, re, sys

ROOT = os.environ.get('RAPIDMETA_REPO_ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Cardio-correct files where the HF dropdown legitimately applies.
CARDIO_KEYWORDS = (
    'arni_hf', 'mavacamten_hcm', 'aficamten', 'attr_cm', 'iv_iron_hf',
    'incretin_hfpef', 'mitral_funcmr', 'sglt2_hf', 'sotagliflozin_hf',
    'finerenone', 'rivaroxaban_vasc', 'tnk_vs', 'colchicine_cvd',
    'sglt2_mace_cvot', 'tavr', 'lipid_hub', 'pcsk9', 'glp1_cvot',
    'cangrelor', 'doac_af', 'ablation_af', 'sotatercept_pah',
)

OLD = '<select id="mf-indication"><option value="CKD">CKD</option><option value="Heart Failure">Heart Failure</option><option value="Other">Other</option></select>'

NEW = '<input id="mf-indication" type="text" placeholder="e.g. asthma, melanoma, glioma..." class="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs">'


def patch_file(path, dry=False):
    src = open(path, 'r', encoding='utf-8').read()
    if OLD not in src:
        return False, 'no_anchor'
    new_src = src.replace(OLD, NEW)
    if not dry:
        open(path, 'w', encoding='utf-8').write(new_src)
    return True, f'replaced ({src.count(OLD)} match)'


def is_cardio(fname):
    fl = fname.lower()
    return any(s in fl for s in CARDIO_KEYWORDS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    print(f'Mode: {"DRY-RUN" if args.dry_run else "APPLY"}')

    files = sorted([f for f in os.listdir(ROOT)
                    if f.endswith('_REVIEW.html')
                    and 'NMA' not in f
                    and 'DTA' not in f
                    and not f.endswith('.bak.html')
                    and not is_cardio(f)])

    summary = {'changed': 0, 'unchanged': 0}
    for fname in files:
        path = os.path.join(ROOT, fname)
        try:
            changed, info = patch_file(path, dry=args.dry_run)
            if changed:
                summary['changed'] += 1
            else:
                summary['unchanged'] += 1
            if changed or info != 'no_anchor':
                tag = 'CHANGED' if changed else 'no-op'
                print(f'  [{tag}] {fname}: {info}')
        except Exception as e:
            print(f'  [ERROR] {fname}: {e}')
    print(f'\nTotal non-cardio scanned: {len(files)}')
    print(f'Summary: {summary}')


if __name__ == '__main__':
    sys.exit(main())
