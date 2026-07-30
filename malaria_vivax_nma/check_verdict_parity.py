"""Gate: the human-visible verdict must match window.__verdict.

A badge that says one thing while window.__verdict says another is the exact
failure this checks for. The badge is rendered at runtime FROM window.__verdict,
so the risk is not the badge element itself -- it is prose elsewhere in the page
asserting a different tier, or reason text that contradicts the payload.

Checks:
  V1  window.__verdict parses and carries a known tier
  V2  every tier word appearing as standalone prose in the HTML equals that tier
  V3  window.__tierDesc has an entry for the declared tier
  V4  p0_total is consistent with the P0_* counts
  V5  the reasons list is non-empty whenever the tier is not STABLE
  V6  no hardcoded tier string sits inside the rendered badge container

Exits non-zero on failure so it can block a publish.
"""
import json, re, sys, io, os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
TIERS = {'STABLE', 'MODERATE', 'EXPOSED', 'UNCERTAIN'}

path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..',
    'VIVAX_RADICAL_CURE_NMA_REVIEW.html')
h = open(path, encoding='utf-8').read()
fails = []

# V1 -------------------------------------------------------------------------
m = re.search(r'window\.__verdict\s*=\s*(\{.*?\});', h, re.S)
if not m:
    print('V1 FAIL: window.__verdict not found'); sys.exit(1)
V = json.loads(m.group(1))
tier = V.get('verdict')
print(f'V1  window.__verdict.verdict = {tier!r}')
if tier not in TIERS:
    fails.append(f'V1 unknown tier {tier!r}')

# V2 -------------------------------------------------------------------------
# Only rendered markup counts as an assertion a reader can see. Script contents
# are never displayed, so the payload, the tier-description table and the
# renderer's own fallback (col.UNCERTAIN) are excluded by stripping every
# <script> block -- not by pattern-matching individual declarations, which
# silently misses whichever one you forget.
body = re.sub(r'<script\b[^>]*>.*?</script\s*>', '', h, flags=re.S | re.I)
if 'window.__verdict' in body:
    fails.append('V2 window.__verdict leaked outside a <script> block')
found = set()
for t in TIERS:
    if re.search(r'(?<![A-Za-z])' + t + r'(?![A-Za-z])', body):
        found.add(t)
print(f'V2  tier words in prose: {sorted(found) or "none"}')
for t in found:
    if t != tier:
        fails.append(f'V2 prose asserts {t!r} but window.__verdict says {tier!r}')

# V3 -------------------------------------------------------------------------
md = re.search(r'window\.__tierDesc\s*=\s*(\{.*?\});', h, re.S)
if not md:
    fails.append('V3 window.__tierDesc missing')
else:
    TD = json.loads(md.group(1))
    if tier not in TD:
        fails.append(f'V3 no tier description for {tier!r}')
    else:
        print(f'V3  tierDesc[{tier}] = {TD[tier][:64]}...')

# V4 -------------------------------------------------------------------------
counts = V.get('counts', {})
p0 = sum(v for k, v in counts.items() if k.startswith('P0_'))
print(f'V4  sum(P0_*) = {p0}   p0_total = {V.get("p0_total")}')
if p0 != V.get('p0_total'):
    fails.append(f'V4 p0_total {V.get("p0_total")} != sum of P0_* {p0}')

# V5 -------------------------------------------------------------------------
reasons = V.get('reasons') or []
print(f'V5  reasons: {len(reasons)}')
if tier != 'STABLE' and not reasons:
    fails.append('V5 non-STABLE tier with no reasons')

# V6 -------------------------------------------------------------------------
host = re.search(r'<div id="verdict">(.*?)</div>', h, re.S)
if host and host.group(1).strip():
    fails.append('V6 #verdict container is not empty in source; '
                 'the tier must be rendered from window.__verdict at runtime')
else:
    print('V6  #verdict container is empty in source (rendered at runtime): OK')

print('\n' + '=' * 58)
if fails:
    print(f'VERDICT PARITY FAILED ({len(fails)}):')
    for f in fails:
        print('  -', f)
    sys.exit(1)
print(f'VERDICT PARITY PASS  -- single source of truth: {tier}')
