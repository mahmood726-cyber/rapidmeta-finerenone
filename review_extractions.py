#!/usr/bin/env python
"""
Review Auto-Extracted Trial Values

Loads extraction_proposals.json (output of extract_ctgov_results.py),
displays each trial's auto-extracted primary outcome, and lets the user:
  [a] Approve  -- adds to pending_config_updates.json
  [e] Edit     -- modify any field then approve
  [r] Reject   -- skip this trial
  [s] Skip     -- decide later
  [q] Quit

After approval, run apply_pending_updates.py to merge into the generator config.

This is the human-in-the-loop verification step that protects against
silent fabrication of HR values.

Run: python review_extractions.py [--auto-approve-extracted]
"""
import sys, io, os, json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


PROPOSAL_FILE = 'extraction_proposals.json'
PENDING_FILE = 'pending_config_updates.json'


def load_proposals(path):
    if not os.path.exists(path):
        print(f'No proposals file at {path}')
        print(f'Run: python extract_ctgov_results.py first')
        sys.exit(1)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_pending(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'approved': [], 'rejected': []}


def save_pending(path, pending):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(pending, f, indent=2)


def print_header(p, idx, total):
    print()
    print('═' * 72)
    print(f' [{idx+1}/{total}]  {p["nctId"]}  {p.get("acronym", "")}')
    print('═' * 72)
    print(f'  Title:        {p.get("title", "")[:65]}')
    print(f'  Sponsor:      {p.get("sponsor", "")[:55]}')
    print(f'  Phase:        {p.get("phase", "")}')
    print(f'  Enrollment:   {p.get("enrollment", "?")}')
    print(f'  Completed:    {p.get("primaryCompletionDate", "?")}')
    print(f'  Status:       {p.get("extraction_status", "?")}')


def print_extraction(p):
    if not p.get('extracted'):
        print(f'  ** No HR/RR/OR extractable from CT.gov results **')
        if p.get('primary_outcome_title'):
            print(f'  Primary outcome on CT.gov: {p["primary_outcome_title"][:60]}')
        return False
    e = p['extracted']
    print()
    print(f'  PRIMARY OUTCOME (CT.gov):  {p.get("primary_outcome_title", "")[:60]}')
    print()
    print(f'  Measure:  {e["measure"]}')
    print(f'  Estimate: {e["estimate"]}  (95% CI {e["lci"]}-{e["uci"]})')
    if e.get('pValue'):
        print(f'  p-value:  {e["pValue"]}')
    if e.get('method'):
        print(f'  Method:   {e["method"]}')
    if p.get('n_per_group'):
        print(f'  N per group:')
        for gid, n in p['n_per_group'].items():
            grp_title = next((g['title'][:30] for g in p.get('groups', []) if g['id'] == gid), gid)
            print(f'    {gid} ({grp_title}): n={n}')
    return True


def edit_proposal(p):
    """Allow user to edit fields before approval."""
    print()
    print('  EDIT MODE — press Enter to keep current value')
    e = p.get('extracted', {})
    new_e = dict(e)

    def ask(label, current, key):
        ans = input(f'  {label} [{current}]: ').strip()
        if ans:
            try:
                new_e[key] = float(ans)
            except ValueError:
                new_e[key] = ans

    ask('Measure (HR/RR/OR)', e.get('measure', ''), 'measure')
    ask('Estimate', e.get('estimate', ''), 'estimate')
    ask('Lower CI', e.get('lci', ''), 'lci')
    ask('Upper CI', e.get('uci', ''), 'uci')

    p['extracted'] = new_e
    p['edited'] = True
    return p


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    proposal_path = os.path.join(here, PROPOSAL_FILE)
    pending_path = os.path.join(here, PENDING_FILE)

    proposals = load_proposals(proposal_path)
    pending = load_pending(pending_path)
    auto_approve = '--auto-approve-extracted' in sys.argv

    already_decided = {p['nctId'] for p in pending['approved'] + pending['rejected']}
    todo = [p for p in proposals if p.get('nctId') not in already_decided]

    print(f'Loaded {len(proposals)} proposals, {len(todo)} pending review.')
    print(f'Already decided: {len(already_decided)} (in {PENDING_FILE})')

    if not todo:
        print('Nothing to review.')
        return

    if auto_approve:
        print(f'\nAUTO-APPROVE MODE: approving all extracted, skipping non-extractable.')
        approved = 0
        for p in todo:
            if p.get('extraction_status') == 'extracted':
                pending['approved'].append(p)
                approved += 1
        save_pending(pending_path, pending)
        print(f'Auto-approved {approved} trials. Run apply_pending_updates.py next.')
        return

    quit_now = False
    for idx, p in enumerate(todo):
        if quit_now:
            break
        print_header(p, idx, len(todo))
        has_extraction = print_extraction(p)
        print()

        if has_extraction:
            print('  [a] Approve   [e] Edit   [r] Reject   [s] Skip   [q] Quit')
        else:
            print('  [r] Reject   [s] Skip   [q] Quit  (no values to approve)')

        while True:
            choice = input('  > ').strip().lower()
            if choice == 'q':
                quit_now = True
                break
            elif choice == 's':
                print('  Skipped.')
                break
            elif choice == 'r':
                pending['rejected'].append(p)
                save_pending(pending_path, pending)
                print('  Rejected and saved.')
                break
            elif choice == 'a' and has_extraction:
                pending['approved'].append(p)
                save_pending(pending_path, pending)
                print('  Approved and saved.')
                break
            elif choice == 'e' and has_extraction:
                edited = edit_proposal(p)
                pending['approved'].append(edited)
                save_pending(pending_path, pending)
                print('  Edited and approved.')
                break
            else:
                print('  Invalid choice. Use a/e/r/s/q.')

    print()
    print('═' * 72)
    print(f' DONE.  Approved: {len(pending["approved"])}  Rejected: {len(pending["rejected"])}')
    print('═' * 72)
    print(f'\nNext step: python apply_pending_updates.py')


if __name__ == '__main__':
    main()
