"""
Bulk-fix two more cardio template-leaks in non-cardio dashboards:

1. Hardcoded "Secondary Outcomes" eligibility row:
     <td>Secondary Outcomes</td><td>All-cause mortality; CV death; HF
     hospitalization; renal composite; quality of life</td>
   - Replace with a generic placeholder pointing users to the Outcome Selector
   for the dashboard's actual endpoints.

2. Static dropdown default option:
     <option value="default">CV Death or HF Hospitalization (default)</option>
   - Replace with neutral 'Primary outcome (default)'.

Cardio dashboards (where the HF labels are legitimate) are left alone.

Usage:
    python scripts/patch_secondary_outcomes_and_dropdown.py --dry-run
    python scripts/patch_secondary_outcomes_and_dropdown.py
"""
import argparse, os, re, sys

ROOT = os.environ.get('RAPIDMETA_REPO_ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CARDIO_KEYWORDS = (
    'arni_hf', 'mavacamten_hcm', 'aficamten', 'attr_cm', 'iv_iron_hf',
    'incretin_hfpef', 'mitral_funcmr', 'sglt2_hf', 'sotagliflozin_hf',
    'finerenone', 'rivaroxaban_vasc', 'tnk_vs', 'colchicine_cvd',
    'sglt2_mace_cvot', 'tavr', 'lipid_hub', 'pcsk9', 'glp1_cvot',
    'cangrelor', 'doac_af', 'ablation_af', 'sotatercept_pah',
)

def is_cardio(fname):
    fl = fname.lower()
    return any(s in fl for s in CARDIO_KEYWORDS)

# Edit 1: Secondary Outcomes row — match the entire <tr>...</tr> with the
# leaked HF text and replace with a generic placeholder.
SECONDARY_OLD = '<tr><td class="p-4 font-bold text-purple-400 bg-purple-400/5">Secondary Outcomes</td><td class="p-4 text-slate-300">All-cause mortality; CV death; HF hospitalization; renal composite; quality of life</td></tr>'
SECONDARY_NEW = '<tr><td class="p-4 font-bold text-purple-400 bg-purple-400/5">Secondary Outcomes</td><td class="p-4 text-slate-300">Trial-registered secondary outcomes — open the Outcome Selector above the forest plot to switch between endpoints captured for this review.</td></tr>'

# Edit 2: cardio dropdown default option
DROPDOWN_OLD = '<option value="default">CV Death or HF Hospitalization (default)</option>'
DROPDOWN_NEW = '<option value="default">Primary outcome (default)</option>'


def patch_file(path, dry=False):
    src = open(path, 'r', encoding='utf-8').read()
    changed = []
    new_src = src
    if SECONDARY_OLD in new_src:
        new_src = new_src.replace(SECONDARY_OLD, SECONDARY_NEW, 1)
        changed.append('secondary-outcomes-row')
    if DROPDOWN_OLD in new_src:
        new_src = new_src.replace(DROPDOWN_OLD, DROPDOWN_NEW, 1)
        changed.append('dropdown-default')
    if not changed:
        return False, 'no_anchors'
    if not dry:
        open(path, 'w', encoding='utf-8').write(new_src)
    return True, ', '.join(changed)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    print(f'Mode: {"DRY-RUN" if args.dry_run else "APPLY"}')

    files = sorted([f for f in os.listdir(ROOT)
                    if f.endswith('_REVIEW.html')
                    and not f.endswith('.bak.html')
                    and not is_cardio(f)])

    summary = {'changed': 0, 'unchanged': 0}
    for fname in files:
        path = os.path.join(ROOT, fname)
        try:
            changed, info = patch_file(path, dry=args.dry_run)
            if changed:
                summary['changed'] += 1
                print(f'  [CHANGED] {fname}: {info}')
            else:
                summary['unchanged'] += 1
        except Exception as e:
            print(f'  [ERROR] {fname}: {e}')
    print(f'\nTotal non-cardio scanned: {len(files)}\nSummary: {summary}')


if __name__ == '__main__':
    sys.exit(main())
