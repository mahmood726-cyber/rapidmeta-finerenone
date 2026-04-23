#!/usr/bin/env python
"""Regression check across all 53 apps after the recent changes:
  - living-MA fix (b929e52)
  - 4+4+4 new-topic clones (4f59c67, 306b52c, 35a72ab)
  - WebR validator injection (138b90e)
  - P1/P2 batch v1.1 protocols (f305b52)
  - P0 editor-review banner + taxonomy (8befc5f)

For each app, verifies 7 signals:
  1. Page loads without pageerror events
  2. RapidMeta.state.trials present, count >= 1
  3. Auto-include trials are in 'include' status
  4. Provisional RoB+GRADE banner present + correct wording
  5. Protocol link no longer points to arni_hf_protocol (except ARNI_HF itself)
  6. webr-validator.js script tag present
  7. Analysis tab pool computes (res-or is a finite number, not '--')
Outputs: 53/53 PASS or list of failures per signal.
"""
import io
import json
import subprocess
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SKIP = {"LivingMeta.html", "META_DASHBOARD.html", "AutoGRADE.html", "AutoManuscript.html"}

apps = sorted([p.name.replace('.html', '') for p in ROOT.glob("*_REVIEW.html")])
print(f"Regression checking {len(apps)} apps")

signals = {
    "page_errors": [],
    "no_trials": [],
    "zero_included": [],
    "no_rob_banner": [],
    "wrong_protocol_link": [],
    "no_webr_tag": [],
    "pool_broken": [],
    "fully_ok": [],
}

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=['--disable-gpu'])
    ctx = b.new_context(viewport={'width': 1400, 'height': 900})
    pg = ctx.new_page()
    for i, a in enumerate(apps, 1):
        pg_errors = []
        pg.on('pageerror', lambda e: pg_errors.append(str(e)[:100]))
        try:
            pg.goto(f'http://localhost:8787/{a}.html', wait_until='load', timeout=60000)
            pg.wait_for_timeout(1500)
            pg.evaluate('localStorage.clear()')
            pg.goto(f'http://localhost:8787/{a}.html', wait_until='load', timeout=60000)
            pg.wait_for_timeout(2200)
        except Exception as e:
            signals["page_errors"].append((a, f"load: {e}"))
            continue

        if pg_errors:
            signals["page_errors"].append((a, pg_errors[:2]))

        try:
            trials = pg.evaluate('RapidMeta?.state?.trials?.length ?? -1')
            incl = pg.evaluate('(RapidMeta?.state?.trials||[]).filter(t => (t.screenReview?.status || t.status) === "include").length')
            banner_txt = pg.evaluate('document.getElementById("rob-status-banner")?.innerText || ""') or ""
            proto_href = pg.evaluate('document.querySelector(\'a[href*="protocols/"][href*="_protocol_v1"]\')?.getAttribute("href") || ""') or ""
            webr_tag = pg.evaluate('!!document.querySelector("script[src=\\"webr-validator.js\\"]")')
            # Switch to analysis tab and read pool
            pg.evaluate('try { RapidMeta.switchTab("analysis") } catch(e){}')
            pg.wait_for_timeout(800)
            pool = pg.evaluate('document.getElementById("res-or")?.innerText || ""') or ""
        except Exception as e:
            signals["page_errors"].append((a, f"eval: {e}"))
            continue

        if trials < 1:
            signals["no_trials"].append((a, trials))
        if incl < 1:
            signals["zero_included"].append((a, incl))
        if "Provisional RoB-2 and GRADE" not in banner_txt:
            signals["no_rob_banner"].append((a, banner_txt[:60]))
        if a != "ARNI_HF_REVIEW" and "arni_hf_protocol" in proto_href:
            signals["wrong_protocol_link"].append((a, proto_href))
        if not webr_tag:
            signals["no_webr_tag"].append((a,))
        pool_clean = pool.strip()
        try:
            pool_f = float(pool_clean)
            if pool_f in (0.0,):
                signals["pool_broken"].append((a, pool_clean))
        except (TypeError, ValueError):
            # "--" or blank means pool failed
            if pool_clean in ("", "--", "NaN"):
                signals["pool_broken"].append((a, pool_clean or "empty"))

        # If the app hit NO signal-failure so far, mark fully ok
        broken_here = any(
            any(x[0] == a for x in signals[k])
            for k in ("page_errors", "no_trials", "zero_included", "no_rob_banner", "wrong_protocol_link", "no_webr_tag", "pool_broken")
        )
        if not broken_here:
            signals["fully_ok"].append(a)

        if i % 10 == 0:
            print(f"  [{i}/{len(apps)}]")
    b.close()

print()
print("=" * 60)
for k, v in signals.items():
    if k == "fully_ok":
        print(f"{k}:    {len(v)}/{len(apps)}")
        continue
    print(f"{k}:    {len(v)}/{len(apps)}")
    for item in v[:6]:
        print(f"   {item}")
    if len(v) > 6:
        print(f"   ... +{len(v)-6} more")

# Save raw
Path("/tmp/regression_results.json").write_text(json.dumps({k: v for k, v in signals.items()}, default=str), encoding='utf-8')
print()
print("Raw JSON saved to /tmp/regression_results.json")
