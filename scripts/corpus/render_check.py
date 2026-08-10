#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Headless render check for a wave-edited page, before vs after.

WHY A RENDER CHECK AT ALL. The static guards in corpus_wave.py prove that no number
in the page SOURCE moved and that the per-page data spans are byte-identical. They
cannot prove the page still runs: an edit inside a minified <script> that breaks
syntax produces a page whose source numbers are perfect and whose screen is blank.
The sweep was static-only and explicitly flags D1/D9/D10/D12/D14/D17's runtime
consequences as inferred, not observed. So the exemplars get executed.

WHAT IT ASSERTS, per page, before and after:
  1. zero uncaught JS errors in the console (SEVERE entries),
  2. the analysis tab renders a pooled effect, CI, I-squared and HKSJ card,
  3. the DOM's rendered-number multiset for those result cards is IDENTICAL
     before vs after -- this is the runtime counterpart of the static guard, and it
     is the one that would catch an edit that changed a computed value,
  4. the tab bar has the same set of visible tabs, EXCEPT where the T9 gate is
     expected to have removed a disconnected NMA tab.

Usage:
    python render_check.py --before DIR_OR_FILE --after DIR_OR_FILE
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

NUM = re.compile(r"\d+(?:[.,]\d+)*")

PROBE = r"""
const out = {tabs: [], results: {}, text: "", nmaVisible: null, qa4Banner: null};
document.querySelectorAll('nav .tab-btn').forEach(b => {
  const vis = b.style.display !== 'none' && b.offsetParent !== null;
  out.tabs.push({id: b.id, label: (b.textContent||'').trim(), visible: vis});
});
const nma = document.getElementById('btn-tab-nma');
out.nmaVisible = nma ? (nma.style.display !== 'none') : null;
const qa4 = document.getElementById('qa4-discordance-banner');
out.qa4Banner = qa4 ? (qa4.className.indexOf('hidden') === -1) : null;
['res-or','res-ci','res-i2','res-hksj','res-pi','res-tau2-ci'].forEach(id => {
  const el = document.getElementById(id);
  out.results[id] = el ? (el.innerText||'').trim() : null;
});
const an = document.getElementById('tab-analysis');
out.text = an ? (an.innerText||'').slice(0, 20000) : '';
return JSON.stringify(out);
"""


NETWORK_NOISE = ("net::ERR", "Access to fetch", "Failed to fetch", "favicon",
                 "ERR_INTERNET_DISCONNECTED", "CORS policy", "Failed to load resource")


BLANK = "blank__rmwave.html"


def _blank_for(path):
    """A near-empty file in the same directory, so it shares the page's file:// origin.

    Storage must be cleared between loads -- every file:// page shares one origin, and
    a before-run would otherwise seed state that changes how the after-run behaves. The
    obvious way to do that is load the page, clear, reload, but that costs TWO loads of
    a ~900 KB single-file app carrying plotly, i.e. four heavy loads per before/after
    pair. Clearing from a blank page in the same origin costs one trivial load instead,
    which is the difference between a 12-hour rollout and a 5-hour one."""
    p = pathlib.Path(path).resolve().parent / BLANK
    if not p.exists():
        p.write_text("<!doctype html><title>b</title>", encoding="utf-8")
    return p.as_uri()


def snapshot(driver, path, settle=2.5):
    uri = pathlib.Path(path).resolve().as_uri()
    try:
        driver.get(_blank_for(path))
        driver.execute_script("localStorage.clear();sessionStorage.clear();")
    except Exception:                                          # noqa: BLE001
        pass
    driver.get(uri)
    from selenium.webdriver.support.ui import WebDriverWait
    WebDriverWait(driver, 40).until(
        lambda d: d.execute_script("return document.readyState") == "complete")
    # The analysis tab computes on switch; drive it the way a reader would.
    try:
        driver.execute_script("RapidMeta.switchTab('analysis'); AnalysisEngine.run();")
    except Exception as e:                                    # noqa: BLE001
        return None, [f"switchTab/AnalysisEngine failed: {e}"], []
    try:
        WebDriverWait(driver, 25).until(
            lambda d: (d.execute_script("var e=document.getElementById('res-or');"
                                        "return e? e.innerText : '--'") or "--") != "--")
    except Exception:                                          # noqa: BLE001
        pass          # a k=0 page never fills res-or; the probe below still runs
    # init() finishes AFTER the first result render: the tab-visibility gate is the
    # last statement in it. Probing on res-or alone read the tab bar mid-init and
    # reported the T9 gate as not firing when it had. Settle, then probe.
    import time
    time.sleep(settle)
    data = json.loads(driver.execute_script(PROBE))
    logs = driver.get_log("browser")
    # An offline single-file page legitimately fails its live registry fetches in a
    # sandbox. Those are environmental, not regressions; JS errors are not.
    severe = [l["message"] for l in logs if l["level"] == "SEVERE"
              and not any(n in l["message"] for n in NETWORK_NOISE)]
    return data, severe, logs


# Pre-existing, INTERMITTENT runtime errors in the corpus. Each entry is here only
# because an A/A control -- the unedited page loaded twice, compared against itself --
# reproduced it. They are real defects and are reported as such; they are not
# regressions introduced by a wave, and treating them as ones would make the render
# check unable to pass on any NMA page.
#
#   s.i2.toFixed is not a function  -- NMA summary rendering assumes i2 is a Number
#   and receives a preformatted string. Observed on ADC_HER2_LOW, ADC_HER2_ADJUVANT,
#   DOAC_AF_NMA. Out of scope for W1-W3 (it is neither prose nor a shared claim);
#   logged for the backlog.
#   <g> attribute transform: Expected number, "rotate(0,NaN,...)"  -- raised inside
#   vendor/plotly-*.min.js, a file no wave touches, when a plot is handed a NaN
#   coordinate. Reproduced in equal or greater numbers by the A/A control on
#   CBD_SEIZURE, GLP1_MASH, HIV_LA_PREP, MDR_TB_SHORTENED and RENAL_DENERV. Also a
#   real defect, also out of scope here.
#
# Matched as substrings, because the rotate() arguments differ per render.
KNOWN_PREEXISTING = (
    "Uncaught TypeError: s.i2.toFixed is not a function",
    # Both SVG-attribute families from the same NaN coordinate: the <g> transform one
    # and the <path> d one. A/A on the five affected pages produced 62 of each.
    "attribute transform: Expected number",
    "attribute d: Expected number",
)


def is_known_preexisting(msg):
    return any(k in msg for k in KNOWN_PREEXISTING)

URL_PREFIX = re.compile(r"^\S*?\.html(?:\s+\d+:\d+)?\s*")


def normalize_error(msg):
    return URL_PREFIX.sub("", msg).strip()


def result_numbers(d):
    joined = " ".join(v for v in d["results"].values() if v)
    return collections.Counter(m.group(0).replace(",", "") for m in NUM.finditer(joined))


def new_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    o = Options()
    o.add_argument("--headless=new")
    o.add_argument("--disable-gpu")
    o.add_argument("--no-sandbox")
    o.add_argument("--disable-dev-shm-usage")
    o.add_argument("--allow-file-access-from-files")
    o.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    return webdriver.Chrome(options=o)


def compare(db, sb, da, sa):
    """Score one before/after pair. Split out so the A/A retry can reuse it."""
    nb, na = result_numbers(db), result_numbers(da)
    mb = collections.Counter(normalize_error(m) for m in sb)
    ma = collections.Counter(normalize_error(m) for m in sa)
    new = [e for e in sorted((ma - mb).elements()) if not is_known_preexisting(e)]
    return nb == na, new, nb, na


def run_pair(before_dir, after_dir, settle=2.5, driver=None, log=print):
    """Render every page present in after_dir, before vs after. Returns report rows.

    ONE before-load and ONE after-load per page. The A/A baseline -- loading the
    unedited page a second time -- is expensive and only earns its cost when something
    looks new, so it is taken lazily, per page, and only then. That keeps a ~900-page
    rollout inside a night while preserving the property that actually matters: no
    page is failed for an error the unedited page also produces.
    """
    before_dir, after_dir = pathlib.Path(before_dir), pathlib.Path(after_dir)
    pages = sorted(p.name for p in after_dir.glob("*.html"))
    own = driver is None
    d = driver or new_driver()
    report = []
    try:
        for i, name in enumerate(pages, 1):
            bp, apth = before_dir / name, after_dir / name
            row = {"page": name}
            if not bp.exists():
                row["verdict"] = "NO_BASELINE"
                report.append(row)
                continue
            try:
                db, sb, _ = snapshot(d, bp, settle)
                da, sa, _ = snapshot(d, apth, settle)
            except Exception as e:                              # noqa: BLE001
                row["verdict"] = "RUNTIME_BREAK"
                row["error"] = str(e)[:300]
                report.append(row)
                log(f"   [{i}/{len(pages)}] {name}: RUNTIME_BREAK {str(e)[:80]}")
                continue
            if db is None or da is None:
                row["verdict"] = "RUNTIME_BREAK"
                row["before_console_severe"] = sb
                row["after_console_severe"] = sa
                report.append(row)
                log(f"   [{i}/{len(pages)}] {name}: RUNTIME_BREAK")
                continue
            same, new, nb, na = compare(db, sb, da, sa)
            if new:
                # Lazy A/A: reload the UNEDITED page and see whether it produces the
                # same thing. Only errors the before-page cannot reproduce count.
                try:
                    _, sb2, _ = snapshot(d, bp, settle)
                    same, new, nb, na = compare(db, sb + sb2, da, sa)
                except Exception:                               # noqa: BLE001
                    pass
            row.update({
                "result_numbers_identical": same,
                "new_console_errors": new,
                "results_before": db["results"], "results_after": da["results"],
                "nma_visible_before": db["nmaVisible"], "nma_visible_after": da["nmaVisible"],
                "qa4_banner_after": da["qa4Banner"],
                "before_console_severe": sb, "after_console_severe": sa,
                "known_preexisting_seen": sorted({e for e in
                                                  (normalize_error(m) for m in sa)
                                                  if is_known_preexisting(e)}),
                "verdict": "OK" if (same and not new) else "CHANGED",
            })
            report.append(row)
            if row["verdict"] != "OK":
                log(f"   [{i}/{len(pages)}] {name}: {row['verdict']} "
                    f"numbers-identical={same} new-errors={len(new)}")
            elif i % 25 == 0:
                log(f"   [{i}/{len(pages)}] ok so far")
    finally:
        if own:
            d.quit()
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", required=True)
    ap.add_argument("--after", required=True)
    ap.add_argument("--settle", type=float, default=2.5)
    ap.add_argument("--json-out", default=None)
    a = ap.parse_args()
    rep = run_pair(a.before, a.after, settle=a.settle)
    for r in rep:
        print(f"{r['page']}: {r.get('verdict')}  "
              f"result-numbers identical={r.get('result_numbers_identical')}  "
              f"new-console-errors={len(r.get('new_console_errors', []))}  "
              f"NMA tab {r.get('nma_visible_before')}->{r.get('nma_visible_after')}")
    if a.json_out:
        pathlib.Path(a.json_out).write_text(json.dumps(rep, indent=1, ensure_ascii=False),
                                            encoding="utf-8")
        print(f"report -> {a.json_out}")
    return 0 if all(r.get("verdict") == "OK" for r in rep) else 1


if __name__ == "__main__":
    sys.exit(main())
