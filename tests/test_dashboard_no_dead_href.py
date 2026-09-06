#!/usr/bin/env python
"""dashboard.html must not link a review whose page does not exist.

dashboard.html renders rows from outputs/portfolio_index.json -- a deliberately kept, and
therefore stale, record of what was once built. 52 of its 71 rows (2026-09-06) point to pages
that no longer exist. The dashboard must DISCLOSE those as "not built", never emit an <a href>
to a 404. It does this by rendering the name as a <span data-review-file> and upgrading to a
link only after a HEAD confirms the file exists (verifyReviewLinks).

This test fails if the renderer can emit a raw href to r.file (the pre-fix anti-pattern), so a
future stale JSON cannot silently reintroduce dead links. It also reports how many index rows
point to missing files, so the size of the disclosed gap is measured rather than assumed.

Run: python tests/test_dashboard_no_dead_href.py   (or via pytest)
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASH = os.path.join(ROOT, "dashboard.html")
INDEX = os.path.join(ROOT, "outputs", "portfolio_index.json")


def main():
    html = io.open(DASH, encoding="utf-8").read()
    fails = []

    # (1) ANTI-PATTERN: a raw href built directly from r.file. This is exactly what emitted the
    # dead links; if it comes back, so do they.
    if re.search(r'href="[\'"]?\s*\+\s*r\.file', html) or re.search(r'href=[\'"]\s*\+\s*r\.file', html):
        fails.append("renderer emits a raw href from r.file (unguarded) -- a missing file becomes a 404 link")

    # (2) The existence gate must be present: the name is a data-review-file span, upgraded to a
    # link only after a HEAD check.
    if "data-review-file" not in html:
        fails.append("no data-review-file span -- names are not gated behind an existence check")
    if "verifyReviewLinks" not in html or "method: 'HEAD'" not in html.replace('"', "'"):
        fails.append("no HEAD-gated link upgrade (verifyReviewLinks) -- existence is not verified before linking")

    # (3) Measure the disclosed gap: how many index rows point to a file that is not there.
    missing = existing = 0
    try:
        rows = json.load(io.open(INDEX, encoding="utf-8")).get("rows", [])
        for r in rows:
            f = r.get("file")
            if not f:
                continue
            if os.path.exists(os.path.join(ROOT, f)):
                existing += 1
            else:
                missing += 1
    except Exception as e:
        fails.append("could not read %s (%s)" % (INDEX, e))

    print("test_dashboard_no_dead_href")
    print("  portfolio_index.json rows: %d exist, %d MISSING (disclosed as 'not built', not linked)"
          % (existing, missing))
    if fails:
        print("  FAIL:")
        for f in fails:
            print("    - " + f)
        return 1
    print("  OK -- the dashboard gates every review href behind a HEAD existence check")
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    raise SystemExit(main())
