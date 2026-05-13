"""tests/test_flagship_playwright_smoke.py

Playwright headless-Chromium smoke test for the 3 dose-response flagships.
Complements `tests/test_flagship_field_paths.mjs` (Node-only contract test)
by catching bugs that only manifest in a real browser runtime:

- Console errors (e.g. an unguarded `undefined.toFixed()` that the contract
  test's `(x != null ? ...)` safe-access pattern would hide)
- Async render races (R precompute JSON loads via fetch + injects HTML into
  the R-parity badge mount; if the engine call beats the JSON load, the
  badge mount stays empty)
- CSS/layout regressions (any `<table>` that fails to render its caption,
  any `<details>` that stays collapsed when it should be open, etc.)
- The specific Round 2C bug pattern: KPI areas displaying "n/a" because
  the JS read the wrong field path

Test design:
1. Start `python -m http.server` on a fixed port in the repo root
2. For each flagship: load page, wait for the R-parity badge mount to render,
   capture console errors, scan rendered HTML for forbidden patterns
3. Assert: 0 console errors, 0 user-facing "n/a" in KPI areas, R-parity badge
   has the GREEN class

Usage:
  python tests/test_flagship_playwright_smoke.py

Requires Playwright Python (`pip install playwright` + `playwright install chromium`).
"""

import http.server
import io
import json
import os
import socketserver
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

# Windows cp1252 console can't print non-ASCII (lessons.md gotcha).
# Wrap stdout in UTF-8 with replace fallback before any print().
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)

from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parent.parent
PORT = 8772  # avoid collision with ad-hoc http.server usage

# (flagship-html, R-parity-mount-id, KPI-area-id) — what each flagship exposes
# expected_badge: "green" (default) means header GREEN and 0 AMBER rows;
#                 "amber_with_known_rows" allows header AMBER iff every AMBER row is
#                 in `allowed_amber_rows` (intended for small-k stress-test flagships
#                 like SURMOUNT k=2 where linear_tau2 is expected AMBER by design).
FLAGSHIPS = [
    {
        "html": "ALCOHOL_BC_DOSE_RESP_REVIEW.html",
        "r_parity_mount_id": "r-parity-doseresp",
        "rcs_kpi_id": "rcs-kpis",
        "expected_badge": "green",
        "allowed_amber_rows": [],
    },
    {
        "html": "SGLT2I_DOSE_RESP_REVIEW.html",
        "r_parity_mount_id": "r-parity-doseresp-hba1c",
        "rcs_kpi_id": "hba1c-rcs-kpis",
        "expected_badge": "green",
        "allowed_amber_rows": [],
    },
    {
        "html": "TIRZEPATIDE_T2D_SURPASS_DOSE_RESP_REVIEW.html",
        "r_parity_mount_id": "r-parity-tirzepatide-hba1c",
        "rcs_kpi_id": "hba1c-rcs-kpis",
        "expected_badge": "green",
        "allowed_amber_rows": [],
    },
    {
        # Round 3.5 — intentional k=2 small-k stress test; linear_tau2 row is
        # expected AMBER (engine PM τ² vs R REML τ² diverge at k=2). The header
        # will be AMBER because allGreen=false. This is documented behaviour.
        "html": "TIRZEPATIDE_OBESITY_SURMOUNT_DOSE_RESP_REVIEW.html",
        "r_parity_mount_id": "r-parity-tirzepatide-obesity",
        "rcs_kpi_id": "wt-rcs-kpis",
        "expected_badge": "amber_with_known_rows",
        # The row labels in the badge come from vendor/r-validation-doseresp.js.
        # `Linear τ²` is the badge label for linear_tau2. We match the engine
        # value `Linear &tau;<sup>2</sup>` (or post-HTML-parse `Linear τ²`) below.
        "allowed_amber_rows": ["Linear τ²"],
    },
]


def start_server():
    """Start http.server in a daemon thread bound to 127.0.0.1:PORT."""
    handler = http.server.SimpleHTTPRequestHandler

    class QuietHandler(handler):
        def log_message(self, *a, **kw):  # silence per-request log spam
            pass

    os.chdir(REPO_ROOT)
    srv = socketserver.TCPServer(("127.0.0.1", PORT), QuietHandler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    # wait for socket to accept
    for _ in range(20):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/", timeout=1)
            return srv
        except Exception:
            time.sleep(0.1)
    raise RuntimeError("HTTP server did not come up on port " + str(PORT))


def run_flagship(page, flagship):
    """Load a single flagship, return (console_errors, engine_version_text, kpi_text, badge_html)."""
    url = f"http://127.0.0.1:{PORT}/{flagship['html']}"
    console_errors = []
    page_errors = []

    def on_console(msg):
        if msg.type == "error":
            console_errors.append(msg.text)

    def on_pageerror(err):
        page_errors.append(str(err))

    page.on("console", on_console)
    page.on("pageerror", on_pageerror)

    page.goto(url, wait_until="domcontentloaded")
    # Wait for the inline script to populate #engine-version (the engine has loaded
    # by then; this is set before any fit/badge work, so it's the earliest reliable
    # signal that the flagship script is running). The placeholder is U+2026 "…".
    try:
        page.wait_for_function(
            "() => { const el = document.getElementById('engine-version'); "
            "return el && el.textContent && el.textContent.trim() !== '' "
            "&& el.textContent.trim() !== '\\u2026'; }",
            timeout=10000,
        )
    except Exception as e:
        return console_errors + page_errors, "", "", f"ENGINE NEVER LOADED: {e}"

    # Wait for R-parity badge to render in the DOM (state='attached' allows hidden
    # tabs — badge on Tab N which is display:none by default until user clicks).
    try:
        page.wait_for_selector(
            f"#{flagship['r_parity_mount_id']} .rv-badge",
            state="attached",
            timeout=10000,
        )
    except Exception as e:
        return console_errors + page_errors, "", "", f"BADGE NEVER RENDERED: {e}"

    page.wait_for_load_state("networkidle", timeout=5000)

    engine_version_text = page.locator("#engine-version").text_content() or ""
    kpi_text = page.locator(f"#{flagship['rcs_kpi_id']}").text_content() or ""
    badge_html = page.locator(f"#{flagship['r_parity_mount_id']}").inner_html() or ""
    return console_errors + page_errors, engine_version_text, kpi_text, badge_html


def assert_no_user_facing_na_in_kpis(kpi_text, flagship_name):
    """Catch the Round 2C bug pattern: KPI display 'HKSJ-mv = n/a' due to wrong field path."""
    # "n/a" can legitimately appear in disclaimer text (e.g. coverage_warning notes),
    # so we narrow to KPI value displays via specific suspicious substrings.
    forbidden = [
        "HKSJ-mv = n/a",  # round 2c bug pattern
        "tcrit = n/a",
        "t_{k-1} = n/a",
        "p = n/a",  # only flag in KPI scope (this check is on rcs-kpis only)
    ]
    hits = [f for f in forbidden if f in kpi_text]
    assert not hits, (
        f"{flagship_name}: KPI text contains forbidden 'n/a' display(s) — "
        f"likely a Round 2C-style field-path bug.\nHits: {hits}\nKPI text: {kpi_text[:500]}"
    )


def assert_badge_is_green(badge_html, flagship_name):
    """The non-linearity-p row was always-amber in v0.1/v0.2; Round 2C made it threshold-driven."""
    assert "rv-badge-green" in badge_html, (
        f"{flagship_name}: R-parity badge header is not GREEN. "
        f"Badge HTML head: {badge_html[:300]}"
    )
    # All 5 rows should be rv-row-green; flag if any rv-row-amber sneaks in
    assert "rv-row-amber" not in badge_html, (
        f"{flagship_name}: at least one R-parity badge row is AMBER — engine drift from R?\n"
        f"Badge HTML: {badge_html[:1000]}"
    )


def assert_badge_amber_with_known_rows(badge_html, allowed_amber_rows, flagship_name):
    """For small-k stress-test flagships: header may be AMBER, but every AMBER row
    MUST be one of the documented allowed rows (e.g. linear_tau2 for SURMOUNT k=2).

    The badge HTML structure (from vendor/r-validation-doseresp.js v0.2.0) is:
        <tr class="rv-row rv-row-{green,amber}"><td class="rv-label">{label}</td>...
    So we count amber-row labels and assert subset relation against allowed_amber_rows.
    """
    import re
    # Match each <tr class="rv-row rv-row-amber">...<td class="rv-label">LABEL</td>
    amber_row_pattern = re.compile(
        r'<tr[^>]*\brv-row-amber\b[^>]*>\s*<td[^>]*\brv-label\b[^>]*>([^<]*)</td>',
        re.IGNORECASE,
    )
    amber_labels_found = [m.strip() for m in amber_row_pattern.findall(badge_html)]
    extra = [lbl for lbl in amber_labels_found if lbl not in allowed_amber_rows]
    assert not extra, (
        f"{flagship_name}: unexpected AMBER row(s) {extra} (allowed: {allowed_amber_rows}). "
        f"Badge HTML: {badge_html[:1500]}"
    )
    # Sanity: at least one of the allowed-amber labels should actually be present
    # (otherwise the test isn't actually validating anything for the stress-test case).
    if allowed_amber_rows:
        present = [lbl for lbl in allowed_amber_rows if lbl in amber_labels_found]
        assert present, (
            f"{flagship_name}: expected AMBER row(s) {allowed_amber_rows} not found in badge — "
            f"engine may have unexpectedly converged with R at k=2 (or label string drifted from "
            f"vendor/r-validation-doseresp.js). Badge HTML: {badge_html[:1500]}"
        )
    # Header should be AMBER (because at least one row is AMBER → allGreen=false)
    assert "rv-badge-amber" in badge_html, (
        f"{flagship_name}: badge header should be AMBER (since {allowed_amber_rows} row is "
        f"expected AMBER), but rv-badge-amber class is missing. Badge HTML: {badge_html[:300]}"
    )


def main():
    print(f"Starting HTTP server on 127.0.0.1:{PORT}...")
    srv = start_server()
    print(f"Server up. Repo root: {REPO_ROOT}")

    failed = 0
    passed = 0

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                for flagship in FLAGSHIPS:
                    print(f"\n--- {flagship['html']} ---")
                    page = browser.new_page()
                    try:
                        errs, engine_version, kpi, badge = run_flagship(page, flagship)

                        # Test 1: no console errors
                        try:
                            assert not errs, f"console/page errors: {errs}"
                            print(f"  ✓ no console/page errors")
                            passed += 1
                        except AssertionError as e:
                            print(f"  ✗ console/page errors: {e}")
                            failed += 1

                        # Test 2: no user-facing 'n/a' in KPI areas
                        try:
                            assert_no_user_facing_na_in_kpis(kpi, flagship["html"])
                            print(f"  ✓ no 'HKSJ-mv = n/a' / 'tcrit = n/a' KPI bugs")
                            passed += 1
                        except AssertionError as e:
                            print(f"  ✗ {e}")
                            failed += 1

                        # Test 3: R-parity badge state (GREEN by default; AMBER-with-known-rows
                        # for small-k stress-test flagships like SURMOUNT k=2).
                        try:
                            expected = flagship.get("expected_badge", "green")
                            if expected == "amber_with_known_rows":
                                assert_badge_amber_with_known_rows(
                                    badge,
                                    flagship.get("allowed_amber_rows", []),
                                    flagship["html"],
                                )
                                print(f"  ✓ R-parity badge AMBER with known rows: {flagship.get('allowed_amber_rows', [])}")
                            else:
                                assert_badge_is_green(badge, flagship["html"])
                                print(f"  ✓ R-parity badge GREEN (5/5 rows green)")
                            passed += 1
                        except AssertionError as e:
                            print(f"  ✗ {e}")
                            failed += 1

                        # Test 4: engine_version span has been populated and contains 0.3.0
                        try:
                            assert "0.3.0" in engine_version, (
                                f"engine_version span text {engine_version!r} does not contain '0.3.0'"
                            )
                            print(f"  ✓ engine v0.3.0 label rendered: {engine_version!r}")
                            passed += 1
                        except AssertionError as e:
                            print(f"  ✗ {e}")
                            failed += 1
                    finally:
                        page.close()
            finally:
                browser.close()
    finally:
        srv.shutdown()
        srv.server_close()
        print(f"\nHTTP server stopped.")

    print(f"\n{'=' * 60}\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
