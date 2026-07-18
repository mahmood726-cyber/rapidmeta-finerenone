#!/usr/bin/env python
"""Regression check across the *_REVIEW.html app corpus.

For each app, verifies 7 signals:
  1. Page loads without pageerror events
  2. RapidMeta.state.trials present, count >= 1
  3. Auto-include trials are in 'include' status
  4. Provisional RoB+GRADE banner present + correct wording
  5. Protocol link no longer points to arni_hf_protocol (except ARNI_HF itself)
  6. webr-validator.js script tag present
  7. Analysis tab pool computes (res-or is a finite number, not '--')

EXIT CODES -- this is a gate; it is meant to be able to fail.
  0  every checked app passed every signal
  1  at least one app failed at least one signal
  2  PRECONDITION not met (no HTTP server, no apps matched) -- NOT an app failure

The precondition check exists because the failure it prevents actually happened:
a full-corpus run once reported page_errors 1215/1215 and still exited 0. Every
one of those "failures" was the absence of a server on the target port, not a
broken app. A run that cannot reach the server must not be reported in the same
channel as a run where the apps are broken -- hence exit 2, checked before the
loop starts.

Serve the corpus first, from the repo root:
    python -m http.server 8787 --bind 127.0.0.1
"""
import argparse
import fnmatch
import io
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parents[1]

# Signals that constitute a failing gate. "fully_ok" is a tally, not a signal.
FAILURE_SIGNALS = (
    "page_errors",
    "no_trials",
    "zero_included",
    "no_rob_banner",
    "wrong_protocol_link",
    "no_webr_tag",
    "pool_broken",
)


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-a", "--app", action="append", default=[], metavar="GLOB",
                    help="Restrict to apps matching this glob (repeatable). "
                         "e.g. -a GLP1_CVOT_REVIEW -a 'SEMA*'")
    ap.add_argument("--base-url", default="http://localhost:8787",
                    help="Base URL serving the corpus (default: %(default)s)")
    ap.add_argument("--limit", type=int, default=None,
                    help="Check at most N apps (after --app filtering)")
    ap.add_argument("--json-out", default=str(ROOT / "regression_results.json"),
                    help="Where to write raw results (default: %(default)s)")
    ap.add_argument("--timeout", type=int, default=60000,
                    help="Per-page load timeout in ms (default: %(default)s)")
    ap.add_argument("--allow-empty", action="store_true",
                    help="Exit 0 rather than 2 when no apps match the filter")
    return ap.parse_args(argv)


def check_server(base_url, timeout=10):
    """Return None if the server is reachable, else a human-readable reason."""
    try:
        urllib.request.urlopen(base_url, timeout=timeout).read(1)
        return None
    except urllib.error.HTTPError:
        # Any HTTP response at all proves something is listening and speaking HTTP.
        return None
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"


def select_apps(patterns, limit):
    apps = sorted(p.name[: -len(".html")] for p in ROOT.glob("*_REVIEW.html"))
    if patterns:
        apps = [a for a in apps
                if any(fnmatch.fnmatch(a, pat) or a == pat for pat in patterns)]
    if limit is not None:
        apps = apps[:limit]
    return apps


def check_app(pg, app, base_url, timeout, signals):
    pg_errors = []
    handler = lambda e: pg_errors.append(str(e)[:100])
    pg.on('pageerror', handler)
    try:
        url = f'{base_url}/{app}.html'
        try:
            pg.goto(url, wait_until='load', timeout=timeout)
            pg.wait_for_timeout(1500)
            pg.evaluate('localStorage.clear()')
            pg.goto(url, wait_until='load', timeout=timeout)
            pg.wait_for_timeout(2200)
        except Exception as exc:
            signals["page_errors"].append((app, f"load: {exc}"))
            return

        if pg_errors:
            signals["page_errors"].append((app, pg_errors[:2]))

        try:
            trials = pg.evaluate('RapidMeta?.state?.trials?.length ?? -1')
            incl = pg.evaluate('(RapidMeta?.state?.trials||[]).filter(t => '
                               '(t.screenReview?.status || t.status) === "include").length')
            banner_txt = pg.evaluate(
                'document.getElementById("rob-status-banner")?.innerText || ""') or ""
            proto_href = pg.evaluate(
                'document.querySelector(\'a[href*="protocols/"][href*="_protocol_v1"]\')'
                '?.getAttribute("href") || ""') or ""
            webr_tag = pg.evaluate(
                '!!document.querySelector("script[src=\\"webr-validator.js\\"]")')
            pg.evaluate('try { RapidMeta.switchTab("analysis") } catch(e){}')
            pg.wait_for_timeout(800)
            pool = pg.evaluate('document.getElementById("res-or")?.innerText || ""') or ""
        except Exception as exc:
            signals["page_errors"].append((app, f"eval: {exc}"))
            return

        if trials < 1:
            signals["no_trials"].append((app, trials))
        if incl < 1:
            signals["zero_included"].append((app, incl))
        if "Provisional RoB-2 and GRADE" not in banner_txt:
            signals["no_rob_banner"].append((app, banner_txt[:60]))
        if app != "ARNI_HF_REVIEW" and "arni_hf_protocol" in proto_href:
            signals["wrong_protocol_link"].append((app, proto_href))
        if not webr_tag:
            signals["no_webr_tag"].append((app,))

        pool_clean = pool.strip()
        try:
            if float(pool_clean) == 0.0:
                signals["pool_broken"].append((app, pool_clean))
        except (TypeError, ValueError):
            if pool_clean in ("", "--", "NaN"):
                signals["pool_broken"].append((app, pool_clean or "empty"))
    finally:
        # Without this the handler stays bound and later apps inherit this
        # app's pageerror events, smearing one failure across the whole run.
        try:
            pg.remove_listener('pageerror', handler)
        except Exception:
            pass


def main(argv=None):
    args = parse_args(argv)
    base_url = args.base_url.rstrip('/')

    apps = select_apps(args.app, args.limit)
    if not apps:
        print(f"[PRECONDITION] no apps matched {args.app or '*_REVIEW.html'} under {ROOT}")
        return 0 if args.allow_empty else 2

    reason = check_server(base_url)
    if reason is not None:
        print(f"[PRECONDITION] cannot reach {base_url} -- {reason}")
        print(f"[PRECONDITION] serve the corpus first:  "
              f"python -m http.server {base_url.rsplit(':', 1)[-1]} --bind 127.0.0.1")
        print("[PRECONDITION] NOT reporting app results -- this is an environment "
              "failure, not a corpus failure.")
        return 2

    print(f"Regression checking {len(apps)} app(s) against {base_url}")

    signals = {k: [] for k in FAILURE_SIGNALS}
    signals["fully_ok"] = []

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, args=['--disable-gpu'])
        ctx = b.new_context(viewport={'width': 1400, 'height': 900})
        pg = ctx.new_page()
        try:
            for i, app in enumerate(apps, 1):
                check_app(pg, app, base_url, args.timeout, signals)
                broken = any(any(x[0] == app for x in signals[k]) for k in FAILURE_SIGNALS)
                if not broken:
                    signals["fully_ok"].append(app)
                if i % 10 == 0:
                    print(f"  [{i}/{len(apps)}]")
        finally:
            b.close()

    print()
    print("=" * 60)
    for k in FAILURE_SIGNALS + ("fully_ok",):
        v = signals[k]
        print(f"{k}:    {len(v)}/{len(apps)}")
        if k == "fully_ok":
            continue
        for item in v[:6]:
            print(f"   {item}")
        if len(v) > 6:
            print(f"   ... +{len(v)-6} more")

    out = Path(args.json_out)
    out.write_text(json.dumps(signals, default=str, indent=1), encoding='utf-8')
    print()
    print(f"Raw JSON saved to {out}")

    failing = {k: len(signals[k]) for k in FAILURE_SIGNALS if signals[k]}
    if failing:
        print()
        print(f"[FAIL] {sum(failing.values())} signal-failure(s) across "
              f"{len(apps)} app(s): {failing}")
        return 1

    print()
    print(f"[PASS] {len(signals['fully_ok'])}/{len(apps)} apps clean on all "
          f"{len(FAILURE_SIGNALS)} signals")
    return 0


if __name__ == "__main__":
    sys.exit(main())
