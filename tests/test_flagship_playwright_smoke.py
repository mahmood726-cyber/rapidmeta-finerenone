"""tests/test_flagship_playwright_smoke.py

Playwright headless-Chromium smoke test for the 5 dose-response flagships.
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
#                 like SURMOUNT k=2 where linear_tau2 is expected AMBER by design);
#                 "deferred" allows header `rv-badge-deferred` (k=1 single-trial flagships
#                 where the standard 5-row badge cannot run because the engine has no
#                 `linear` or `one_stage` output at k=1; FINERENONE_ARTS_DN is the case).
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
    {
        # Round 3.6 — intentional k=1 single-trial flagship (ARTS-DN finerenone
        # Phase 2b dose-finder, NCT01874431). The standard 5-row R-parity badge
        # cannot run at k=1 because:
        #   - engine fitLinear requires k >= 2 (no engine linear output)
        #   - R lme4::lmer requires >= 2 sampled grouping levels (no R one-stage output)
        # The flagship renders a custom 2-row RCS-only badge with class
        # `rv-badge-deferred`. The deferral note must be visible.
        "html": "FINERENONE_ARTS_DN_DOSE_RESP_REVIEW.html",
        "r_parity_mount_id": "r-parity-finerenone-arts-dn",
        "rcs_kpi_id": "uacr-rcs-kpis",
        "expected_badge": "deferred",
        "allowed_amber_rows": [],
        # Phrase in the deferral note that must be present in the badge HTML.
        "deferral_must_contain": "deferred to engine v0.5",
    },
    {
        # Round 3.7 — 6-trial semaglutide SUSTAIN HbA1c dose-response flagship.
        # R dosresmeta refuses RCS entirely on the sparse-arm requirement (4 of 6
        # trials have only 1 non-reference arm after Option A active-comparator
        # dropping vs K_p=2 spline coefs required). The engine handles this by
        # silently dropping singular per-trial designs and pooling k_RCS=2.
        # The flagship renders a custom hybrid panel:
        #   - header class `rv-badge-deferred` (overall RCS deferred)
        #   - linear-slope row GREEN (engine -0.94 vs R -0.93, |Δ| < 0.01)
        #   - linear-τ² row AMBER (engine PM 0.41 vs R REML 0.40, |Δ| 0.011 —
        #     expected estimator divergence at I² = 97.4 %; PM and REML both valid)
        #   - 3 RCS rows DEFERRED (rv-row-deferred)
        #   - one-stage row PASS-THROUGH (engine fitOneStage just reads R JSON)
        # Use "deferred" check + the deferral note must be present.
        "html": "SEMAGLUTIDE_T2D_SUSTAIN_DOSE_RESP_REVIEW.html",
        "r_parity_mount_id": "r-parity-sustain-hba1c",
        "rcs_kpi_id": "hba1c-rcs-kpis",
        "expected_badge": "deferred",
        "allowed_amber_rows": [],
        "deferral_must_contain": "deferred to engine v0.5",
    },
    {
        # Round 3.8 — 4-trial SELECT upadacitinib DAS28-CRP dose-response flagship.
        # First flagship to exercise the engine's documented RCS-fallback in
        # production. The 4 trials use a {0, 15, 30} mg dose grid that cannot
        # support a 3-knot Harrell-default RCS under two-stage pooling (only 3
        # distinct doses; engine needs ≥ K = 3 distinct knot locations across
        # the pool with sufficient per-trial non-reference observations).
        # Engine `fitRCS` short-circuits to `fitLinear` and decorates the
        # result with `layer='linear'`, `fallback='degenerate_to_linear'`,
        # `rcs=null`. R `dosresmeta` refuses RCS with the parallel sparse-arm
        # error in the R precompute JSON. The flagship's RCS tab is REPLACED
        # with a methodological note (Tab 2) rather than a KPI grid; the
        # R-parity tab (Tab 3) renders the linear-only audit panel.
        # Badge characteristics:
        #   - header class `rv-badge-deferred` (overall RCS deferred)
        #   - linear-slope row GREEN (engine -0.0296 vs R -0.0296, |Δ| ≈ 0)
        #   - linear-τ² row GREEN (engine PM 0.000254 vs R REML 0.000258, |Δ| ≈ 4e-6
        #     well within the 0.0001 threshold)
        #   - 3 RCS rows DEFERRED (rv-row-deferred)
        #   - one-stage row PASS-THROUGH
        # The KPI scope here is Tab 2's `rcs-note-body` (which contains the
        # verbatim engine-output code block); we re-use the standard 'no n/a
        # in KPI' check but point it at the RCS-note body rather than a KPI
        # grid (the standard 'hba1c-rcs-kpis' mount does not exist on this
        # flagship — Tab 2 is the methodological note).
        "html": "UPADACITINIB_RA_SELECT_DOSE_RESP_REVIEW.html",
        "r_parity_mount_id": "r-parity-select-das28",
        "rcs_kpi_id": "rcs-note-body",
        "expected_badge": "deferred",
        "allowed_amber_rows": [],
        "deferral_must_contain": "deferred to engine v0.5",
    },
    {
        # Round 3.9 — 3-trial AMAGINE brodalumab PASI 75 binary dose-response flagship.
        # FIRST flagship where engine declines RCS but R FITS RCS (the prior
        # degeneracy flagships SUSTAIN and SELECT had both engines refusing via
        # different paths). The 3 trials use a {0, 140, 210} mg dose grid that
        # has only 2 distinct positive doses; the engine's `rcsKnots` returns
        # fewer than K=3 distinct knot locations and `fitRCS` short-circuits to
        # `fitLinear` with `fallback='degenerate_to_linear'`, `rcs=null`. R
        # `dosresmeta` does NOT short-circuit — each trial has 2 non-reference
        # arms after Option A active-comparator dropping (>= K_p=2 required),
        # so R's sparse-per-trial-arm guard does not fire. R proceeds and fits
        # a 3-knot RCS with all 3 percentile knots inside the 140–210 mg
        # interval (knots [157.5, 175, 192.5], spline_coefs [0.01763, -0.01875],
        # nonlinearity_wald_p 1.64e-13). The R fit is technically valid arithmetic
        # but uses degenerate (uninformative) knots.
        # Badge characteristics (custom panel, NOT the standard 5-row badge):
        #   - header class `rv-badge-deferred` (purple) — overall flag for the
        #     engine-vs-R disagreement
        #   - linear-slope row GREEN (engine 0.00523 vs R 0.00735, |Δ| ≈ 0.0021
        #     well within the 0.01 threshold)
        #   - linear-τ² row GREEN (both essentially zero; engine PM 8.6e-7 vs
        #     R REML 4.6e-19, |Δ| ≈ 8.6e-7 well within the 0.0001 threshold)
        #   - 3 RCS rows custom "ENGINE-DECLINED / R-FIT" status (rv-row-deferred
        #     styling; status cell explicitly contains "ENGINE-DECLINED / R-FIT")
        #   - one-stage row PASS-THROUGH (R glmer converged=false)
        # KPI scope here is Tab 2's `rcs-note-body` (containing the side-by-side
        # engine-output / R-output code blocks); we re-use the standard 'no n/a
        # in KPI' check (the standard 'pasi-rcs-kpis' mount does not exist on
        # this flagship — Tab 2 is the methodological note).
        "html": "BRODALUMAB_PSORIASIS_AMAGINE_DOSE_RESP_REVIEW.html",
        "r_parity_mount_id": "r-parity-brodalumab-pasi",
        "rcs_kpi_id": "rcs-note-body",
        "expected_badge": "deferred",
        "allowed_amber_rows": [],
        "deferral_must_contain": "deferred to engine v0.5",
        # AMAGINE-specific check: the badge must explicitly surface the
        # "engine-declined / R-fit" disagreement in the RCS rows. Without this,
        # readers cannot tell whether the deferral is the SUSTAIN/SELECT
        # case (both refused) or the AMAGINE case (engine refused, R fit).
        "must_contain_phrases": [
            "ENGINE-DECLINED / R-FIT",
            "knots inside 140",  # part of "knots inside 140–210 mg gap"
        ],
    },
    {
        # Round 3.10 — 3-trial erenumab Phase 3 Δ MMD dose-response flagship.
        # SAME methodological pattern as Round 3.8 SELECT (both engine and R
        # refuse RCS). The 3 trials use a {0, 70, 140} mg dose grid with sparse
        # per-trial coverage: STRIVE has all 3 arms (placebo + 70 + 140), but
        # ARISE has only placebo + 70 mg and LIBERTY has only placebo + 140 mg.
        # Engine fitRCS sees only 2 distinct POSITIVE doses (70, 140) → rcsKnots
        # returns < K=3 distinct knot locations → engine short-circuits to
        # fitLinear with layer='linear', fallback='degenerate_to_linear',
        # rcs=null. R dosresmeta refuses with the parallel sparse-arm error
        # because ARISE and LIBERTY each have only 1 non-reference arm vs
        # K_p=2 spline coefficients required.
        # Distinctive feature: LIBERTY's population is treatment-refractory
        # (prior failure of 2-4 oral preventives) vs STRIVE/ARISE which are
        # treatment-naive. The placebo arm in LIBERTY reduces MMD by only
        # -0.16 days vs -1.83/-1.84 in STRIVE/ARISE — a 10x smaller placebo
        # response by population. Tab 1 includes a population-heterogeneity
        # panel documenting this.
        # Badge characteristics (SAME as SELECT, Round 3.8):
        #   - header class `rv-badge-deferred` (overall RCS deferred)
        #   - linear-slope row GREEN (engine -0.01313 vs R -0.01312, |Δ| ≈ 1e-5
        #     well within the 0.01 threshold)
        #   - linear-τ² row GREEN (both essentially zero; engine PM 0 vs
        #     R REML 1.3e-20, |Δ| ≈ 1.3e-20 well within the 0.0001 threshold)
        #   - 3 RCS rows DEFERRED (rv-row-deferred)
        #   - one-stage row PASS-THROUGH (R lme4::lmer converged=true)
        # KPI scope here is Tab 2's `rcs-note-body` (same as SELECT — the
        # standard 'rcs-kpis' mount does not exist on this flagship).
        # PubMed citation erratum (3rd in this autonomous block): LIBERTY's
        # correct PMID is 30360965 (not 30360966 which is an unrelated Lancet
        # kinase-inhibition comment article in the same issue). Round 3.7
        # caught SUSTAIN-FORTE journal name; Round 3.9 caught AMAGINE-1
        # journal name; Round 3.10 caught LIBERTY PMID off-by-one.
        "html": "ERENUMAB_MIGRAINE_PHASE3_DOSE_RESP_REVIEW.html",
        "r_parity_mount_id": "r-parity-erenumab-mmd",
        "rcs_kpi_id": "rcs-note-body",
        "expected_badge": "deferred",
        "allowed_amber_rows": [],
        "deferral_must_contain": "deferred to engine v0.5",
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


def assert_badge_is_deferred(badge_html, deferral_must_contain, flagship_name):
    """For k=1 single-trial flagships: the standard 5-row badge can't run; the
    flagship renders a custom panel with class `rv-badge-deferred` and a
    deferral note that must contain the documented phrase (default:
    "deferred to engine v0.5").
    """
    assert "rv-badge-deferred" in badge_html, (
        f"{flagship_name}: expected `rv-badge-deferred` class on the R-parity badge "
        f"(k=1 single-trial flagship; standard 5-row badge can't run). "
        f"Badge HTML head: {badge_html[:300]}"
    )
    assert deferral_must_contain in badge_html, (
        f"{flagship_name}: deferral note must contain {deferral_must_contain!r} but "
        f"badge HTML did not include it. Badge HTML: {badge_html[:800]}"
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
                        # for small-k stress-test flagships like SURMOUNT k=2; DEFERRED for
                        # k=1 single-trial flagships like FINERENONE_ARTS_DN).
                        try:
                            expected = flagship.get("expected_badge", "green")
                            if expected == "amber_with_known_rows":
                                assert_badge_amber_with_known_rows(
                                    badge,
                                    flagship.get("allowed_amber_rows", []),
                                    flagship["html"],
                                )
                                print(f"  ✓ R-parity badge AMBER with known rows: {flagship.get('allowed_amber_rows', [])}")
                            elif expected == "deferred":
                                assert_badge_is_deferred(
                                    badge,
                                    flagship.get("deferral_must_contain", "deferred to engine v0.5"),
                                    flagship["html"],
                                )
                                print(f"  ✓ R-parity badge DEFERRED (k=1; deferral note present)")
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

                        # Test 5 (Round 3.9, AMAGINE-specific): if the flagship
                        # specifies must_contain_phrases, each phrase must appear
                        # in the rendered badge HTML. Round 3.9 uses this to
                        # assert that the badge surfaces the "ENGINE-DECLINED /
                        # R-FIT" disagreement explicitly (distinguishing it from
                        # the SUSTAIN/SELECT case where both engines refused).
                        # Flagships without this key skip the test silently
                        # (back-compat with the 7 prior flagships).
                        must_contain = flagship.get("must_contain_phrases")
                        if must_contain:
                            try:
                                missing = [phrase for phrase in must_contain if phrase not in badge]
                                assert not missing, (
                                    f"{flagship['html']}: badge HTML missing required phrases "
                                    f"{missing}. Badge HTML (first 2000 chars): {badge[:2000]}"
                                )
                                print(f"  ✓ badge contains required phrases: {must_contain}")
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
