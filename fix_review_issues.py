"""
Fix 3 real issues found in multi-persona review across all Finrenone apps:

1. WCAG AA contrast failures in dark mode:
   - .badge-search: #94a3b8 on #334155 = 4.02:1 → bump to #cbd5e1 (6.71:1)
   - .chart-dl-btn: #64748b on dark = 3.89:1 → bump to #94a3b8 (7.19:1)
   - .evidence-source: #64748b on dark = 3.89:1 → bump to #94a3b8 (7.19:1)
   - .extract-view-btn: #64748b on dark = 3.89:1 → bump to #94a3b8 (7.19:1)

2. controlEventRate || 0.15 drops valid zero → use ?? 0.15
   (3 active files: COLCHICINE, GLP1, SGLT2_HF)

3. _highlightScreening no-op regex replace (cosmetic cleanup)

Run: python fix_review_issues.py
"""
import os, re, sys

DIR = os.path.dirname(os.path.abspath(__file__))

# Only fix active HTML files (skip .bak and backup files)
REVIEW_FILES = [f for f in os.listdir(DIR)
                if f.endswith('.html')
                and '_REVIEW' in f
                and '.bak.' not in f
                and 'backup' not in f.lower()]

ALL_HTML = [f for f in os.listdir(DIR)
            if f.endswith('.html')
            and '.bak.' not in f
            and 'backup' not in f.lower()]

print(f"Review files: {len(REVIEW_FILES)}")
print(f"All HTML files: {len(ALL_HTML)}")

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
fixes = {1: 0, 2: 0, 3: 0}
files_fixed = set()

for fname in ALL_HTML:
    path = os.path.join(DIR, fname)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # === FIX 1: WCAG contrast ===
    # .badge-search text: #94a3b8 → #cbd5e1 (on #334155 bg)
    content = re.sub(
        r'(\.badge-search\s*\{[^}]*color:\s*)#94a3b8',
        r'\g<1>#cbd5e1',
        content
    )

    # .chart-dl-btn text: #64748b → #94a3b8 (on dark bg)
    content = re.sub(
        r'(\.chart-dl-btn\s*\{[^}]*color:\s*)#64748b',
        r'\g<1>#94a3b8',
        content
    )

    # .evidence-source text: #64748b → #94a3b8 (on dark panel)
    content = re.sub(
        r'(\.evidence-source\s*\{[^}]*color:\s*)#64748b',
        r'\g<1>#94a3b8',
        content
    )

    # .extract-view-btn text: #64748b → #94a3b8 (on dark bg)
    content = re.sub(
        r'(\.extract-view-btn\s*\{[^}]*color:\s*)#64748b',
        r'\g<1>#94a3b8',
        content
    )

    if content != original:
        fixes[1] += 1

    # === FIX 2: controlEventRate || 0.15 → ?? 0.15 ===
    prev = content
    content = content.replace(
        'pooledControlEventRate(included) || 0.15',
        'pooledControlEventRate(included) ?? 0.15'
    )
    if content != prev:
        fixes[2] += 1

    # === FIX 3: No-op regex replace in _highlightScreening ===
    prev = content
    # h.pattern.replace(/\\/g, '\\') is a no-op — just use h.pattern directly
    content = content.replace(
        "h.pattern.replace(/\\\\/g, '\\\\')",
        "h.pattern"
    )
    if content != prev:
        fixes[3] += 1

    if content != original:
        files_fixed.add(fname)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  FIXED: {fname}")

print(f"\n{'='*60}")
print(f"SUMMARY: {len(files_fixed)} files fixed")
print(f"  Fix 1 (WCAG contrast):        {fixes[1]} files")
print(f"  Fix 2 (|| 0.15 → ?? 0.15):    {fixes[2]} files")
print(f"  Fix 3 (no-op regex cleanup):   {fixes[3]} files")
print(f"{'='*60}")

# Verify fixes applied correctly
print("\nVerification:")
for fname in sorted(files_fixed):
    path = os.path.join(DIR, fname)
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Check no remaining #64748b in the 3 fixed selectors
    bad_contrast = len(re.findall(r'\.(?:chart-dl-btn|evidence-source|extract-view-btn)\s*\{[^}]*#64748b', text))
    bad_badge = len(re.findall(r'\.badge-search\s*\{[^}]*#94a3b8', text))
    bad_or = text.count('pooledControlEventRate(included) || 0.15')
    bad_noop = text.count("h.pattern.replace(/\\\\/g, '\\\\')")

    status = "OK" if (bad_contrast + bad_badge + bad_or + bad_noop) == 0 else "ISSUES REMAIN"
    print(f"  {fname}: {status}")
