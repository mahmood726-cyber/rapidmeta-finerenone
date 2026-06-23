"""
Inject the shared Supabase auth + save-progress widget into every living-meta
app by adding a single <script src="rapidmeta-auth.js"> tag before the final
</body>. Idempotent (skips files that already have it). Additive only — touches
nothing else in the file.

Run: python inject_auth.py [--dry-run]
"""
import os, sys, glob

DRY = '--dry-run' in sys.argv
DIR = os.path.dirname(os.path.abspath(__file__))
TAG = '<script src="rapidmeta-auth.js?v=1" defer></script>'
MARKER = 'rapidmeta-auth.js'

injected = skipped = nobody = 0
for path in sorted(glob.glob(os.path.join(DIR, '*.html'))):
    name = os.path.basename(path)
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()
    if MARKER in html:
        skipped += 1
        continue
    idx = html.rfind('</body>')          # final body close = real document end
    if idx == -1:
        nobody += 1
        print('  NO </body>:', name)
        continue
    new = html[:idx] + TAG + '\n' + html[idx:]
    if not DRY:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new)
    injected += 1

print('\n%s: injected=%d  already-present=%d  no-body=%d' % (
    'DRY RUN' if DRY else 'DONE', injected, skipped, nobody))
