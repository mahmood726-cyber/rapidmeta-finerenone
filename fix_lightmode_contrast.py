"""
Fix light-mode WCAG contrast for .chart-dl-btn and .extract-view-btn.
Dark mode: #94a3b8 on #020617 = 7.87:1 (passes)
Light mode: #94a3b8 on #f8fafc = 2.45:1 (FAILS)
Fix: add .light-mode overrides with #475569 (7.18:1 on #f8fafc)

Also add .light-mode .evidence-source and .light-mode .extract-action-btn overrides.
"""
import sys as _sys
if __name__ != "__main__":
    _sys.exit(0)

import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DIR = os.path.dirname(os.path.abspath(__file__))

FILES = [f for f in os.listdir(DIR)
         if f.endswith('.html') and '_REVIEW' in f
         and '.bak.' not in f and 'backup' not in f.lower()]

# The insertion anchor: .light-mode .chart-desc already exists
ANCHOR = '.light-mode .chart-desc { color: #374151; }'
ADDITIONS = """.light-mode .chart-desc { color: #374151; }
        .light-mode .chart-dl-btn { color: #475569; }
        .light-mode .chart-dl-btn:hover { color: #2563eb; }
        .light-mode .extract-view-btn { color: #475569; }
        .light-mode .extract-view-btn.active { color: #2563eb; }
        .light-mode .evidence-source { color: #475569; }
        .light-mode .extract-action-btn { color: #475569; }
        .light-mode .evidence-action-btn { color: #475569; }"""

count = 0
for fname in sorted(FILES):
    path = os.path.join(DIR, fname)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    if '.light-mode .chart-dl-btn' in content:
        print(f'  SKIP (already has): {fname}')
        continue

    if ANCHOR not in content:
        print(f'  SKIP (no anchor): {fname}')
        continue

    content = content.replace(ANCHOR, ADDITIONS)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    count += 1
    print(f'  FIXED: {fname}')

print(f'\n{count} files fixed')
