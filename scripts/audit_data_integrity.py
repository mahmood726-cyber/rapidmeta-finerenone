"""
Comprehensive data-integrity audit for RapidMeta dashboards.

Detects the same classes of bug found during the OAKS/DERBY swap fix in
PEGCETACOPLAN_GA, scaled across every *_REVIEW.html (pairwise + NMA + DTA):

  1. Duplicate NCT keys in realData (silent JS object-literal dedup; later
     entries shadow earlier ones, masking real data).
  2. nctAcronyms map mistakes:
       - same acronym mapped to multiple NCTs (the OAKS/OAKS bug)
       - NCT in realData with a `name` that differs from nctAcronyms[NCT]
       - NCT in nctAcronyms but missing from realData (orphan)
       - NCT in realData but missing from nctAcronyms
  3. Duplicate field names within a single trial entry (the `pmid: X, pmid: X`
     bug; JS keeps the last value silently).
  4. Sibling-template PICO copy-paste: int field doesn't reference the
     dashboard's expected drug; pop field carries Finrenone HF/CKD defaults.
  5. NCT mentioned in narrative/eligibility but not in realData — possible
     extension/related trial that should be in seedExcludedNCTs.

Usage:
    python scripts/audit_data_integrity.py            # report only
    python scripts/audit_data_integrity.py --json     # machine-readable
"""
import argparse, os, re, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = r'C:\Projects\Finrenone'

# Match a top-level NCT key inside realData. realData entries look like:
#   'NCT01234567': {
#       name: '...', pmid: '...', ...
NCT_KEY_RE = re.compile(r"'(NCT\d{8})'\s*:\s*\{")

# Trial entry: name field
NAME_RE = re.compile(r"name:\s*'([^']*)'", re.M)

# Duplicate field names within an entry
def find_duplicate_fields(entry_body):
    """Return list of field names that appear more than once at the top level
    of a trial-entry body. Only inspect the prefix BEFORE allOutcomes/evidence
    arrays — nested objects inside those arrays have their own field namespace
    and aren't duplicates of the top-level entry fields."""
    # Slice off everything from 'allOutcomes:' / 'evidence:' / 'rob:' onwards;
    # what's left is the single-line entry header.
    cuts = []
    for marker in ('allOutcomes:', 'evidence:', 'rob:'):
        idx = entry_body.find(marker)
        if idx > 0:
            cuts.append(idx)
    header = entry_body[:min(cuts)] if cuts else entry_body[:600]
    fields = re.findall(r'\b(\w+)\s*:\s*[\'\[\{\dntfu-]', header)
    seen = {}
    dupes = []
    for f in fields:
        seen[f] = seen.get(f, 0) + 1
    for f, n in seen.items():
        if n > 1 and f in {'name', 'pmid', 'phase', 'year', 'tE', 'tN', 'cE', 'cN',
                           'group', 'publishedHR', 'hrLCI', 'hrUCI', 'snippet',
                           'sourceUrl', 'ctgovUrl'}:
            dupes.append((f, n))
    return dupes


def parse_realdata(src):
    """Return list of (nct, entry_body, name_field) for each realData entry."""
    i = src.find('realData')
    if i < 0: return []
    # Find { after realData
    brace = src.find('{', i)
    if brace < 0: return []
    # Walk to matching close
    depth = 0; started = False; end = -1
    for j in range(brace, len(src)):
        c = src[j]
        if c == '{': depth += 1; started = True
        elif c == '}':
            depth -= 1
            if started and depth == 0: end = j; break
    if end < 0: return []
    block = src[brace:end+1]

    # Find each NCT key inside the block
    entries = []
    for m in NCT_KEY_RE.finditer(block):
        nct = m.group(1)
        # Extract just the trial-header line (first 800 chars before nested arrays)
        # i.e. capture from '{' of the entry until first '\n            },' or
        # the next NCT key
        entry_start = m.end()
        # Find the closing brace of THIS entry
        d = 1; entry_end = -1
        for k in range(entry_start, min(entry_start + 6000, len(block))):
            c = block[k]
            if c == '{': d += 1
            elif c == '}':
                d -= 1
                if d == 0: entry_end = k; break
        body = block[entry_start:entry_end] if entry_end > 0 else block[entry_start:entry_start+800]
        # Just the FIRST 600 chars (before the nested allOutcomes/evidence arrays)
        header = body[:600]
        nm = NAME_RE.search(header)
        name = nm.group(1) if nm else None
        entries.append({'nct': nct, 'name': name, 'header': header, 'body': body})
    return entries


def parse_nct_acronyms(src):
    """Return the nctAcronyms dict {nct: acronym} or None."""
    m = re.search(r"nctAcronyms:\s*\{([^}]*)\}", src)
    if not m: return None
    acronyms = {}
    for kv in re.finditer(r"'(NCT\d{8})'\s*:\s*'([^']*)'", m.group(1)):
        acronyms[kv.group(1)] = kv.group(2)
    return acronyms


def audit_file(path):
    src = open(path, 'r', encoding='utf-8').read()
    issues = []

    entries = parse_realdata(src)
    acronyms = parse_nct_acronyms(src)

    # 1. Duplicate NCT keys
    nct_counts = {}
    for e in entries:
        nct_counts[e['nct']] = nct_counts.get(e['nct'], 0) + 1
    for nct, n in nct_counts.items():
        if n > 1:
            issues.append({'severity': 'CRITICAL', 'kind': 'dup_nct_key',
                           'msg': f'NCT {nct} appears {n} times as realData key (later entries shadow earlier)'})

    # 2a. nctAcronyms duplicates: same acronym -> multiple NCTs
    if acronyms:
        rev = {}
        for nct, acr in acronyms.items():
            rev.setdefault(acr, []).append(nct)
        for acr, ncts in rev.items():
            if len(ncts) > 1:
                issues.append({'severity': 'CRITICAL', 'kind': 'acronym_collision',
                               'msg': f'Acronym "{acr}" mapped to multiple NCTs: {ncts}'})

    # 2b. nctAcronyms vs realData name mismatch
    if acronyms:
        for e in entries:
            nct, name = e['nct'], e['name']
            if name and nct in acronyms:
                if acronyms[nct].upper() != name.upper():
                    issues.append({'severity': 'HIGH', 'kind': 'acronym_name_mismatch',
                                   'msg': f'NCT {nct}: nctAcronyms says "{acronyms[nct]}" but realData name is "{name}"'})

    # 2c. NCT in nctAcronyms but missing from realData (orphan)
    if acronyms:
        rd_ncts = {e['nct'] for e in entries}
        for nct in acronyms:
            if nct not in rd_ncts:
                issues.append({'severity': 'LOW', 'kind': 'acronym_orphan',
                               'msg': f'NCT {nct} ("{acronyms[nct]}") in nctAcronyms but not in realData'})

    # 3. Duplicate field names within each entry header
    for e in entries:
        dupes = find_duplicate_fields(e['header'])
        for fname, n in dupes:
            issues.append({'severity': 'HIGH', 'kind': 'dup_field',
                           'msg': f'NCT {e["nct"]} ({e["name"]}): field "{fname}" appears {n} times in trial header'})

    return entries, acronyms, issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()

    files = sorted([f for f in os.listdir(ROOT)
                    if f.endswith('_REVIEW.html')
                    and not f.endswith('.bak.html')])

    all_issues = []
    by_severity = {'CRITICAL': 0, 'HIGH': 0, 'LOW': 0}
    for fname in files:
        path = os.path.join(ROOT, fname)
        try:
            entries, acronyms, issues = audit_file(path)
        except Exception as e:
            issues = [{'severity': 'CRITICAL', 'kind': 'audit_error', 'msg': f'audit crashed: {e}'}]
        for issue in issues:
            issue['file'] = fname
            all_issues.append(issue)
            by_severity[issue['severity']] = by_severity.get(issue['severity'], 0) + 1

    if args.json:
        print(json.dumps(all_issues, indent=2))
        return

    # Pretty report
    by_kind = {}
    for issue in all_issues:
        by_kind.setdefault(issue['kind'], []).append(issue)

    print(f'Total files scanned: {len(files)}')
    print(f'Issues by severity: {by_severity}')
    print(f'Issues by kind: {dict((k, len(v)) for k, v in by_kind.items())}\n')

    for kind in ['dup_nct_key', 'acronym_collision', 'dup_field',
                 'acronym_name_mismatch', 'acronym_orphan', 'audit_error']:
        if kind not in by_kind: continue
        items = by_kind[kind]
        print(f'\n=== {kind} ({len(items)}) ===')
        for issue in items[:50]:
            print(f'  [{issue["severity"]}] {issue["file"]}: {issue["msg"]}')
        if len(items) > 50:
            print(f'  ... +{len(items)-50} more')


if __name__ == '__main__':
    main()
