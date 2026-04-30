"""
Append missing-dashboard rows to the portfolio index.html table.

The portfolio index lists ~77 dashboards but the repo has ~155 *_REVIEW.html
files. This script identifies dashboards that aren't yet linked from the
index and appends them as new <tr> rows in the comprehensive table at the
bottom (just before </tbody>).

Each new row carries:
  - link to the file
  - display name derived from <title> if available, else from filename
  - category (best-guess from filename pattern + heuristic)
  - k = '—' (placeholder; user can curate later)
  - outcome = '—' (placeholder)
  - protocol cell = 'v1.0' (placeholder)

Idempotent: skipped if the link is already in the index.

Usage: python scripts/update_portfolio_index.py [--dry-run]
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

INDEX_PATH = os.path.join(ROOT, 'index.html')

TITLE_RE = re.compile(r'<title>(.*?)</title>', re.IGNORECASE | re.DOTALL)


def derive_display_name(html: str, fname: str) -> str:
    m = TITLE_RE.search(html)
    if m:
        title = m.group(1).strip()
        # Format: "RapidMeta {Specialty} | {Drug/Topic} v1.0" -> Drug/Topic
        if '|' in title:
            after = title.split('|', 1)[1].strip()
            after = re.sub(r'\s*v\d+(?:\.\d+)*\s*$', '', after).strip()
            if after:
                return after
    return fname.replace('_REVIEW.html', '').replace('_', ' ').title()


def derive_category(fname: str) -> str:
    f = fname.upper()
    if '_DTA_' in f:
        return 'DTA'
    if '_NMA_' in f:
        return 'Network MA'
    cat_map = {
        'BIMEKIZUMAB': 'Dermatology',
        'LEBRIKIZUMAB': 'Dermatology',
        'JAKI_AD_NMA': 'Dermatology (NMA)',
        'BPAL_MDRTB': 'Infectious Disease (TB)',
        'HIV_LA_PREP_NMA': 'Infectious Disease (HIV)',
        'MALARIA_VACCINES': 'Infectious Disease (Malaria)',
        'DOLUTEGRAVIR': 'Infectious Disease (HIV)',
        'AZITHROMYCIN_CHILD': 'Infectious Disease (Paediatric MDA)',
        'TYVAC_TYPHOID': 'Infectious Disease (Vaccine)',
        'ACORAMIDIS': 'Cardiology (HF/CM)',
        'AFICAMTEN': 'Cardiology (HCM)',
        'CARDIORENAL': 'Renal & CKD',
        'IPTACOPAN': 'Renal',
        'SPARSENTAN': 'Renal',
        'VOCLOSPORIN': 'Renal',
        'RESMETIROM': 'Hepatology',
        'CFTR_MODULATORS': 'Respiratory',
        'DELANDISTROGENE': 'Neurology (DMD)',
        'EFGARTIGIMOD': 'Neurology (MG)',
        'AVACINCAPTAD': 'Ophthalmology',
        'TARLATAMAB': 'Oncology (Lung)',
        'CAPIVASERTIB': 'Oncology (Breast)',
        'INAVOLISIB': 'Oncology (Breast)',
        'ELACESTRANT': 'Oncology (Breast)',
        'ZOLBETUXIMAB': 'Oncology (Gastric)',
        'MIRVETUXIMAB': 'Oncology (Ovarian)',
        'VORASIDENIB': 'Oncology (Glioma)',
        'TEPLIZUMAB': 'Endocrinology (T1D)',
        'MITAPIVAT': 'Haematology',
        'RUSFERTIDE': 'Haematology',
        'ZURANOLONE': 'Psychiatry',
        'ENSIFENTRINE': 'Respiratory',
        'ETRASIMOD': 'Gastroenterology',
        'DONANEMAB': 'Neurology (AD)',
        'ARPI_MHSPC': 'Oncology (Prostate)',
        'ATOPIC_DERM': 'Dermatology (NMA)',
        'ALOPECIA': 'Dermatology (NMA)',
        'SOTATERCEPT': 'Cardiology (PAH)',
        'VUTRISIRAN': 'Neurology (hATTR)',
    }
    for key, cat in cat_map.items():
        if key in f:
            return cat
    if '_NMA_' in f:
        return 'Network MA'
    return 'Other'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    print(f'Mode: {"DRY-RUN" if args.dry_run else "APPLY"}')

    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        index_html = f.read()

    # Collect linked filenames already in the index
    linked = set(re.findall(r'([A-Z][A-Z_0-9]+_REVIEW\.html)', index_html))

    # All review files in repo
    all_files = sorted(
        f for f in os.listdir(ROOT)
        if f.endswith('_REVIEW.html') and not f.endswith('.bak.html')
    )

    missing = [f for f in all_files if f not in linked]
    print(f'Linked: {len(linked)}; Total files: {len(all_files)}; Missing: {len(missing)}')

    if not missing:
        print('Nothing to add.')
        return 0

    # Build new <tr> rows
    rows = []
    for f in missing:
        with open(os.path.join(ROOT, f), 'r', encoding='utf-8') as fh:
            html = fh.read()
        name = derive_display_name(html, f)
        cat = derive_category(f)
        row = (
            f'        <tr><td style="padding:.4rem .8rem">'
            f'<a href="{f}" style="color:#2E6B8A">{name}</a></td>'
            f'<td>{cat}</td>'
            f'<td style="text-align:right">&mdash;</td>'
            f'<td style="text-align:right;font-family:ui-monospace,monospace">v13.0 Cochrane v6.5</td>'
            f'<td style="text-align:center"><span style="color:#7A5A10">v1.0</span></td></tr>'
        )
        rows.append(row)

    insertion = '\n'.join(rows) + '\n'

    # Insert before the table's </tbody>
    tbody_close = '      </tbody>'
    if tbody_close not in index_html:
        print('FAIL: </tbody> close tag not found in index.html')
        return 2

    new_html = index_html.replace(tbody_close, insertion + tbody_close, 1)

    if not args.dry_run:
        with open(INDEX_PATH, 'w', encoding='utf-8') as f:
            f.write(new_html)
        print(f'Inserted {len(rows)} rows; updated {INDEX_PATH}')
    else:
        print(f'[dry-run] would insert {len(rows)} rows')

    return 0


if __name__ == '__main__':
    sys.exit(main())
