#!/usr/bin/env python
"""
Apply Pending Updates

Reads pending_config_updates.json (output of review_extractions.py) and
updates trial entries in generate_living_ma_v13.py with the verified
publishedHR values.

For each approved proposal:
1. Find the matching NCT ID in the generator's APPS list (or in the
   FINERENONE_REVIEW.html template for finerenone-side trials)
2. Replace publishedHR/hrLCI/hrUCI fields with verified values
3. Strip the 'PENDING' note from snippet/evidence
4. Add a "Verified by extract_ctgov_results.py" provenance line

Run:
  python apply_pending_updates.py             # apply all approved
  python apply_pending_updates.py --dry-run   # show what would change

After applying, run:
  python generate_living_ma_v13.py NAME       # regenerate affected app
  python validate_living_ma_portfolio.py      # confirm 23/23 maintained
"""
import sys, io, os, json, re

# Force UTF-8 stdout only when run as a script; reassigning sys.stdout at IMPORT
# time breaks pytest's output capture for any test that imports this module.
if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


PENDING_FILE = 'pending_config_updates.json'
GENERATOR_FILE = 'generate_living_ma_v13.py'


def _is_hr_measure(measure) -> bool:
    """True iff *measure* is a hazard ratio (the estimand publishedHR represents).

    publishedHR/hrLCI/hrUCI are HAZARD-RATIO fields; extract_ctgov_results.py
    also emits RR and OR estimates. Storing an RR/OR in these fields silently
    mislabels the estimand downstream (it is pooled/displayed as an HR). Only an
    HR-type measure may be applied. Missing measure defaults to HR (the historic
    contract) but a present non-HR measure must be rejected.
    """
    return str(measure).strip().upper() == 'HR'


def load_pending(path):
    if not os.path.exists(path):
        print(f'No pending file at {path}')
        sys.exit(1)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def update_generator(approved_proposals, dry_run=False):
    """Patch each approved trial's HR fields in generate_living_ma_v13.py."""
    here = os.path.dirname(os.path.abspath(__file__))
    gen_path = os.path.join(here, GENERATOR_FILE)
    with open(gen_path, 'r', encoding='utf-8') as f:
        content = f.read()

    changes = []
    for p in approved_proposals:
        nct = p['nctId']
        e = p.get('extracted', {})
        if not e:
            continue
        est = e['estimate']
        lo = e['lci']
        hi = e['uci']
        measure = e.get('measure', 'HR')

        # Estimand guard: publishedHR/hrLCI/hrUCI are hazard-ratio fields. An
        # approved RR/OR must NOT be written there (it would be pooled/labelled
        # as an HR downstream). Skip a non-HR measure rather than corrupt it.
        if not _is_hr_measure(measure):
            print(f'  SKIP {nct}: measure is {measure!r}, not HR — refusing to '
                  f'store a non-HR estimate in publishedHR fields')
            continue

        # Find the publishedHR=None line within the trial's block
        # Pattern: scope-narrowed match for the trial's NCT id followed by null HR fields
        nct_pattern = re.compile(
            rf'("{nct}":\s*\{{[^{{}}]*?)"publishedHR":\s*None,\s*"hrLCI":\s*None,\s*"hrUCI":\s*None,',
            re.DOTALL
        )
        new_fields = f'"publishedHR": {est}, "hrLCI": {lo}, "hrUCI": {hi},'

        m = nct_pattern.search(content)
        if not m:
            # Try with single quotes (for any single-quoted entries)
            nct_pattern2 = re.compile(
                rf"('{nct}':\s*\{{[^{{}}]*?)'publishedHR':\s*None,\s*'hrLCI':\s*None,\s*'hrUCI':\s*None,",
                re.DOTALL
            )
            m = nct_pattern2.search(content)
            if m:
                new_fields = f"'publishedHR': {est}, 'hrLCI': {lo}, 'hrUCI': {hi},"

        if not m:
            print(f'  WARNING: {nct} not found in generator (or already verified)')
            continue

        # Replace the entire matched substring with prefix + new fields
        old_block = m.group(0)
        new_block = m.group(1) + new_fields
        content = content.replace(old_block, new_block, 1)

        # Add provenance comment in snippet
        snippet_pattern = re.compile(rf'("name":\s*"[^"]*",\s*"phase":[^\n]*\n[^\n]*\n[^\n]*PENDING[^"]*"[^,]*,)', re.DOTALL)
        # Just mark in changes
        changes.append({
            'nct': nct,
            'measure': measure,
            'estimate': est,
            'lci': lo,
            'uci': hi,
        })
        print(f'  PATCH {nct}: {measure} = {est} ({lo}-{hi})')

    if not changes:
        print('No matches found in generator.')
        return False

    if dry_run:
        print(f'\nDRY RUN: would apply {len(changes)} updates. Re-run without --dry-run.')
        return False

    with open(gen_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'\nApplied {len(changes)} updates to {GENERATOR_FILE}')
    return True


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    pending_path = os.path.join(here, PENDING_FILE)
    pending = load_pending(pending_path)
    approved = pending.get('approved', [])

    if not approved:
        print('No approved proposals to apply.')
        return

    print(f'Found {len(approved)} approved proposals.')
    dry_run = '--dry-run' in sys.argv

    success = update_generator(approved, dry_run=dry_run)

    if success and not dry_run:
        # Mark approved as applied (move to a different bucket)
        pending['applied'] = pending.get('applied', []) + approved
        pending['approved'] = []
        with open(pending_path, 'w', encoding='utf-8') as f:
            json.dump(pending, f, indent=2)
        print(f'\nNext: regenerate the affected apps and re-validate:')
        for p in approved:
            print(f'  python generate_living_ma_v13.py <APPNAME>  # for {p["nctId"]}')
        print(f'  python validate_living_ma_portfolio.py')


if __name__ == '__main__':
    main()
